"""One read per fact the storefront's probes and checks rely on, straight from the shop and payments databases.

Every read opens a read-only connection, reads inside one transaction so related rows come from the same
moment, and imports no app code, so a bug in the shop's own queries can't hide itself. A read returns None or
an empty list only when the record is truly absent, and raises on any other failure (a service that doesn't
answer, a missing database file), so an outage never looks like "none".
"""

from contextlib import closing

import connection

CUSTOMER = 1  # REQUIREMENTS.md: one customer is always signed in. shop/db.py seeds that customer as ID 1.


def _read(service, *queries):
    """Run each (sql, args) in one read-only transaction; returns a list of row-dict lists, one per query."""
    with closing(connection.read_only(service)) as db:
        db.execute("BEGIN")
        try:
            return [[dict(row) for row in db.execute(sql, args).fetchall()] for sql, args in queries]
        finally:
            db.execute("ROLLBACK")


def _rows(service, sql, args=()):
    return _read(service, (sql, args))[0]


def catalog():
    """Every product with its stored price, in ID order."""
    return _rows("shop", "SELECT id, name, price_cents FROM products ORDER BY id")


def cart():
    """The signed-in customer's stored cart: one {product_id, quantity} per line, in product order."""
    return _rows(
        "shop",
        "SELECT product_id, quantity FROM cart_items WHERE customer_id = ? ORDER BY product_id",
        (CUSTOMER,),
    )


def latest_order_id():
    """The highest stored order ID, or 0 when there are no orders."""
    return _rows("shop", "SELECT COALESCE(MAX(id), 0) AS id FROM orders")[0]["id"]


def orders_after(order_id):
    """Orders stored with an ID above order_id, oldest first."""
    return _rows("shop", "SELECT * FROM orders WHERE id > ? ORDER BY id", (order_id,))


def order(order_id):
    """The stored order with its lines, or None when no such order exists."""
    found, lines = _read(
        "shop",
        ("SELECT * FROM orders WHERE id = ?", (order_id,)),
        ("SELECT product_id, name, quantity, unit_price_cents FROM order_lines WHERE order_id = ? ORDER BY rowid", (order_id,)),
    )
    return {**found[0], "lines": lines} if found else None


def charge(charge_id):
    """The payments service's stored record of a charge, or None when it has none."""
    found = _rows("payments", "SELECT * FROM charges WHERE id = ?", (charge_id,))
    return found[0] if found else None


def charge_count():
    """How many charges the payments service has stored."""
    return _rows("payments", "SELECT COUNT(*) AS n FROM charges")[0]["n"]
