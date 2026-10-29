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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
