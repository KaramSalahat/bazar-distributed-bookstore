
import os
import sqlite3

import requests
from flask import Flask, jsonify, request

from database import (
    initialize_database,
    create_order,
    get_order,
    claim_order,
    update_order_status,
)

app = Flask(__name__)

CATALOG_SERVICE_URL = os.getenv(
    "CATALOG_SERVICE_URL",
    "http://127.0.0.1:5001"
)

initialize_database()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "order",
        "status": "ok"
    }), 200


@app.route("/purchase", methods=["POST"])
def purchase_book():
    data = request.get_json(silent=True)

    # Validate request body
    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON body is required"
        }), 400

    request_id = data.get("request_id")
    item_number = data.get("item_number")
    quantity = data.get("quantity", 1)

    if (
        not isinstance(request_id, str)
        or not request_id.strip()
        or len(request_id) > 128
    ):
        return jsonify({
            "error": "request_id must be a non-empty string (max 128 characters)"
        }), 400

    if type(item_number) is not int or item_number <= 0:
        return jsonify({
            "error": "item_number must be a positive integer"
        }), 400

    if type(quantity) is not int or quantity <= 0:
        return jsonify({
            "error": "quantity must be a positive integer"
        }), 400

    # Create order with unique request_id
    try:
        created = create_order(
            request_id,
            item_number,
            quantity
        )
    except sqlite3.Error:
        return jsonify({
            "error": "Order database unavailable"
        }), 503

    # Handle duplicate requests
    if not created:
        try:
            existing = get_order(request_id)
        except sqlite3.Error:
            return jsonify({
                "error": "Order database unavailable"
            }), 503

        if existing is None:
            return jsonify({
                "error": "Order lookup failed"
            }), 503

        if (
            existing["item_number"] != item_number
            or existing["quantity"] != quantity
        ):
            return jsonify({
                "error": "request_id already used for different purchase data"
            }), 409

        if existing["status"] == "completed":
            return jsonify({
                "message": "Order already completed",
                "order": existing
            }), 200

        return jsonify({
            "message": "Order already exists; no new stock deduction attempted",
            "order": existing
        }), 202

    # Claim order for processing
    try:
        claimed = claim_order(request_id)
    except sqlite3.Error:
        return jsonify({
            "error": "Order database unavailable"
        }), 503

    if not claimed:
        return jsonify({
            "error": "Order could not be claimed"
        }), 503

    # Get book information from Catalog Service
    try:
        response = requests.get(
            f"{CATALOG_SERVICE_URL}/info/{item_number}",
            timeout=5
        )

        if response.status_code == 404:
            update_order_status(request_id, "failed")
            return jsonify({
                "error": "Book not found"
            }), 404

        if response.status_code != 200:
            update_order_status(request_id, "failed")
            return jsonify({
                "error": "Catalog service error",
                "request_id": request_id
            }), 502

        book = response.json()

        if not isinstance(book, dict) or not all(
            key in book
            for key in ("id", "title", "price", "stock")
        ):
            update_order_status(request_id, "failed")
            return jsonify({
                "error": "Invalid book data from catalog"
            }), 502

        if (
            type(book["id"]) is not int
            or book["id"] != item_number
            or type(book["price"]) not in (int, float)
            or type(book["stock"]) is not int
            or not (0 <= book["price"] < float("inf"))
            or book["stock"] < 0
        ):
            update_order_status(request_id, "failed")
            return jsonify({
                "error": "Invalid book values from catalog"
            }), 502

        if book["stock"] < quantity:
            update_order_status(request_id, "failed")
            return jsonify({
                "error": "Insufficient stock",
                "available_stock": book["stock"]
            }), 409

    except (requests.RequestException, ValueError):
        # No stock deduction was attempted yet
        update_order_status(request_id, "failed")
        return jsonify({
            "error": "Could not verify book information",
            "request_id": request_id
        }), 503

    unit_price = float(book["price"])
    total_price = round(unit_price * quantity, 2)

    # Request atomic stock deduction from Catalog Service
    try:
        decrement_response = requests.patch(
            f"{CATALOG_SERVICE_URL}/books/{item_number}/decrement",
            json={"quantity": quantity},
            timeout=5
        )

    except requests.RequestException:
        # Stock might have been deducted before connection failed
        update_order_status(
            request_id,
            "uncertain",
            unit_price,
            total_price
        )

        return jsonify({
            "error": "Stock deduction result is uncertain; do not retry with a new request_id",
            "request_id": request_id
        }), 503

    if decrement_response.status_code == 409:
        update_order_status(request_id, "failed")
        return jsonify({
            "error": "Insufficient stock"
        }), 409

    if decrement_response.status_code == 404:
        update_order_status(request_id, "failed")
        return jsonify({
            "error": "Book not found"
        }), 404

    if decrement_response.status_code != 200:
        update_order_status(
            request_id,
            "uncertain",
            unit_price,
            total_price
        )

        return jsonify({
            "error": "Stock deduction result is uncertain",
            "request_id": request_id
        }), 502

    # Finalize successful order
    try:
        completed = update_order_status(
            request_id,
            "completed",
            unit_price,
            total_price
        )
    except sqlite3.Error:
        return jsonify({
            "error": "Stock may have been deducted but order could not be finalized",
            "request_id": request_id
        }), 503

    if not completed:
        return jsonify({
            "error": "Order finalization failed; manual review required",
            "request_id": request_id
        }), 503

    # Print the successful purchase message required by the lab
    print(f"bought book {book['title']}", flush=True)

    return jsonify({
        "message": "Purchase completed successfully",
        "order": get_order(request_id)
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
