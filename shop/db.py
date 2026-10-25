"""SQLite storage for the shop. Every read and write the app does goes through Repository."""

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(os.environ.get("STOREFRONT_DB", "data/shop.sqlite"))
DEMO_CUSTOMER = 1

# Discount codes and the percentage they take off the order. A table in the database would let staff add codes
# without a deploy; for now the marketing team has two.
DISCOUNT_CODES = {"WELCOME10": 10, "FRIENDS20": 20}


@dataclass
class Discount:
    code: str
    percent: int
    cents: int


def discount_for(code: str | None, subtotal_cents: int) -> Discount | None:
    """The discount a code earns on a subtotal, or None when the code is blank or unknown."""
    code = (code or "").strip().upper()
    if code not in DISCOUNT_CODES:
        return None
    percent = DISCOUNT_CODES[code]
    return Discount(code=code, percent=percent, cents=subtotal_cents * percent // 100)

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    tint TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cart_items (
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (customer_id, product_id)
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    total_cents INTEGER NOT NULL,
    discount_code TEXT,
    discount_cents INTEGER NOT NULL DEFAULT 0,
    charge_id TEXT,
    placed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS order_lines (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL
);
"""

PRODUCTS = [
    ("Field Notebook", "Dot grid, 192 pages, lies flat.", 1800, "#d9b99b"),
    ("Brass Pen", "Machined brass body, refillable.", 4200, "#c9a227"),
    ("Desk Lamp", "Warm LED, three brightness levels.", 8900, "#8aa6b1"),
    ("Linen Tote", "Heavy linen, reinforced handles.", 3400, "#b7b19d"),
    ("Pour-over Kettle", "Gooseneck spout, one litre.", 6500, "#6f7d8c"),
    ("Wool Throw", "Merino wool, 130 by 180 cm.", 12000, "#a2535a"),
]


def connect(path: Path = DEFAULT_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def seed(connection: sqlite3.Connection) -> None:
    """Create the schema and the catalog if the database is empty."""
    connection.executescript(SCHEMA)
    if connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        connection.executemany(
            "INSERT INTO products (name, description, price_cents, tint) VALUES (?, ?, ?, ?)", PRODUCTS
        )
    if connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        connection.execute(
            "INSERT INTO customers (id, name, email) VALUES (?, ?, ?)",
            (DEMO_CUSTOMER, "Mira Okafor", "mira@example.com"),
        )
    connection.commit()


class Repository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def products(self) -> list[sqlite3.Row]:
        return self.connection.execute("SELECT * FROM products ORDER BY id").fetchall()

    def product(self, product_id: int) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    def customer(self, customer_id: int) -> sqlite3.Row:
        return self.connection.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()

    def cart(self, customer_id: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            """SELECT p.id, p.name, p.price_cents, p.tint, c.quantity,
                      p.price_cents * c.quantity AS line_cents
               FROM cart_items c JOIN products p ON p.id = c.product_id
               WHERE c.customer_id = ? ORDER BY p.id""",
            (customer_id,),
        ).fetchall()

    def add_to_cart(self, customer_id: int, product_id: int) -> None:
        self.connection.execute(
            """INSERT INTO cart_items (customer_id, product_id, quantity) VALUES (?, ?, 1)
               ON CONFLICT (customer_id, product_id) DO UPDATE SET quantity = quantity + 1""",
            (customer_id, product_id),
        )
        self.connection.commit()

    def remove_from_cart(self, customer_id: int, product_id: int) -> None:
        self.connection.execute(
            "DELETE FROM cart_items WHERE customer_id = ? AND product_id = ?", (customer_id, product_id)
        )
        self.connection.commit()

    def clear_cart(self, customer_id: int) -> None:
        self.connection.execute("DELETE FROM cart_items WHERE customer_id = ?", (customer_id,))
        self.connection.commit()

    def create_order(
        self, customer_id: int, lines: list[sqlite3.Row], total_cents: int, discount: "Discount | None" = None
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO orders (customer_id, status, total_cents, discount_code, discount_cents, placed_at)
               VALUES (?, 'pending', ?, ?, ?, ?)""",
            (
                customer_id,
                total_cents,
                discount.code if discount else None,
                discount.cents if discount else 0,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        order_id = cursor.lastrowid
        self.connection.executemany(
            "INSERT INTO order_lines (order_id, product_id, name, quantity, unit_price_cents) VALUES (?, ?, ?, ?, ?)",
            [(order_id, line["id"], line["name"], line["quantity"], line["price_cents"]) for line in lines],
        )
        self.connection.commit()
        return order_id

    def set_order_status(self, order_id: int, status: str, charge_id: str | None = None) -> None:
        self.connection.execute(
            "UPDATE orders SET status = ?, charge_id = ? WHERE id = ?", (status, charge_id, order_id)
        )
        self.connection.commit()

    def order(self, order_id: int) -> sqlite3.Row | None:
        return self.connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()

    def order_lines(self, order_id: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT *, unit_price_cents * quantity AS line_cents FROM order_lines WHERE order_id = ? ORDER BY rowid",
            (order_id,),
        ).fetchall()

    def orders(self, customer_id: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (customer_id,)
        ).fetchall()
