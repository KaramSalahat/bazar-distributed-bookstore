import json
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

BOOKS_FILE = Path(__file__).resolve().parent / "books.json"


def load_books():
    db_file = Path(__file__).resolve().parent / "books.db"

    with sqlite3.connect(db_file) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            "SELECT id, title, topic, price, stock FROM books ORDER BY id"
        ).fetchall()

        return [dict(row) for row in rows]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "service": "catalog",
        "status": "ok"
    })


@app.route("/search", methods=["GET"])
def search_books():
    topic = request.args.get("topic", "").strip()

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    books = load_books()

    matching_books = [
        book for book in books
        if topic.lower() in book["topic"].lower()
    ]

    return jsonify({
        "topic": topic,
        "count": len(matching_books),
        "books": matching_books
    })


@app.route("/info/<int:item_number>", methods=["GET"])
def get_book_info(item_number):
    books = load_books()

    for book in books:
        if book["id"] == item_number:
            return jsonify(book)

    return jsonify({
        "error": "Book not found"
    }), 404


@app.route("/books/<int:item_number>/price", methods=["PATCH"])
def update_book_price(item_number):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body is required"}), 400

    price = data.get("price")

    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not (0 <= price < float("inf"))
    ):
        return jsonify({"error": "Price must be a non-negative finite number"}), 400

    db_file = Path(__file__).resolve().parent / "books.db"

    with sqlite3.connect(db_file, timeout=10) as connection:
        cursor = connection.execute(
            "UPDATE books SET price = ? WHERE id = ?",
            (price, item_number)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Book not found"}), 404

    return jsonify({
        "message": "Price updated successfully",
        "id": item_number,
        "price": price
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
