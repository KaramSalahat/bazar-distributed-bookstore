
import os

import requests
from flask import Flask, jsonify, request

from database import initialize_database

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

    if not isinstance(data, dict):
        return jsonify({
            "error": "JSON body is required"
        }), 400

    item_number = data.get("item_number")
    quantity = data.get("quantity", 1)

    if type(item_number) is not int or item_number <= 0:
        return jsonify({
            "error": "item_number must be a positive integer"
        }), 400

    if type(quantity) is not int or quantity <= 0:
        return jsonify({
            "error": "quantity must be a positive integer"
        }), 400

    try:
        response = requests.get(
            f"{CATALOG_SERVICE_URL}/info/{item_number}",
            timeout=5
        )
    except requests.RequestException:
        return jsonify({
            "error": "Catalog service unavailable"
        }), 503

    if response.status_code == 404:
        return jsonify({
            "error": "Book not found"
        }), 404

    if response.status_code != 200:
        return jsonify({
            "error": "Catalog service error"
        }), 502

    try:
        book = response.json()
    except ValueError:
        return jsonify({
            "error": "Invalid response from catalog service"
        }), 502

    if not isinstance(book, dict) or not all(
        key in book for key in ("id", "title", "price", "stock")
    ):
        return jsonify({
            "error": "Invalid book data from catalog service"
        }), 502

    return jsonify({
        "message": "Purchase request validated",
        "item_number": item_number,
        "quantity": quantity,
        "book": book
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
