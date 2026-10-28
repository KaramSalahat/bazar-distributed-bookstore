import json
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

BOOKS_FILE = Path(__file__).resolve().parent / "books.json"


def load_books():
    with open(BOOKS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


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
