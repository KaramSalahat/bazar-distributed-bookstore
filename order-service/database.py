
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent / "orders.db"


def get_connection():
    connection = sqlite3.connect(DB_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL UNIQUE,
                item_number INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL,
                total_price REAL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN (
                        'pending',
                        'processing',
                        'completed',
                        'failed',
                        'uncertain'
                    )),
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)

    print("Orders database initialized successfully!")


def create_order(request_id, item_number, quantity):
    """
    Create a pending order.
    Return True if created, False if request_id exists.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO orders
                (request_id, item_number, quantity, status)
            VALUES (?, ?, ?, 'pending')
            """,
            (request_id, item_number, quantity)
        )
        return cursor.rowcount == 1


def get_order(request_id):
    """Retrieve an order using its unique request ID."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM orders WHERE request_id = ?",
            (request_id,)
        ).fetchone()

    return dict(row) if row is not None else None


def claim_order(request_id):
    """
    Atomically claim a pending order for processing.
    Only one caller can change pending to processing.
    """
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET status = 'processing'
            WHERE request_id = ? AND status = 'pending'
            """,
            (request_id,)
        )
        return cursor.rowcount == 1


def update_order_status(
    request_id,
    status,
    unit_price=None,
    total_price=None
):
    """
    Update an order that is currently being processed.
    """
    if status not in ("completed", "failed", "uncertain"):
        raise ValueError("Invalid final order status")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE orders
            SET status = ?,
                unit_price = COALESCE(?, unit_price),
                total_price = COALESCE(?, total_price)
            WHERE request_id = ? AND status = 'processing'
            """,
            (status, unit_price, total_price, request_id)
        )
        return cursor.rowcount == 1


if __name__ == "__main__":
    initialize_database()
