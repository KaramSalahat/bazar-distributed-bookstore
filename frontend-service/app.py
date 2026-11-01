
import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

CATALOG_URL = os.getenv("CATALOG_SERVICE_URL", "http://127.0.0.1:5001")
ORDER_URL = os.getenv("ORDER_SERVICE_URL", "http://127.0.0.1:5002")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "frontend", "status": "ok"}), 200


@app.route("/search/<path:topic>", methods=["GET"])
def search_books(topic):
    try:
        response = requests.get(
            f"{CATALOG_URL}/search",
            params={"topic": topic},
            timeout=5
        )
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "Catalog service unavailable"}), 503

    except ValueError:
        return jsonify({"error": "Invalid catalog response"}), 502


@app.route("/info/<int:item_number>", methods=["GET"])
def book_info(item_number):
    try:
        response = requests.get(
            f"{CATALOG_URL}/info/{item_number}",
            timeout=5
        )
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "Catalog service unavailable"}), 503

    except ValueError:
        return jsonify({"error": "Invalid catalog response"}), 502


@app.route("/purchase", methods=["POST"])
def purchase_book():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body is required"}), 400

    try:
        response = requests.post(
            f"{ORDER_URL}/purchase",
            json=data,
            timeout=15
        )
        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "Order service unavailable or timed out"}), 503

    except ValueError:
        return jsonify({"error": "Invalid order service response"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
