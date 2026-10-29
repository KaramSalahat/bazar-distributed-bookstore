import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JSON_FILE = BASE_DIR / "books.json"
DB_FILE = BASE_DIR / "books.db"


def initialize_database():
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        books = json.load(file)

    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                topic TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                stock INTEGER NOT NULL CHECK (stock >= 0)
            )
        """)

        for book in books:
            connection.execute("""
                INSERT OR IGNORE INTO books
                (id, title, topic, price, stock)
                VALUES (?, ?, ?, ?, ?)
            """, (
                book["id"],
                book["title"],
                book["topic"],
                book["price"],
                book["stock"]
            ))

    print("Database initialized successfully!")


if __name__ == "__main__":
    initialize_database()
