#!/usr/bin/env python3
"""Check discount codes at checkout (REQUIREMENTS.md DC-1, DC-2) on the running storefront in a real, recorded browser.

One journey through Chromium: empty the cart with the cart page's Remove buttons, fill it with the shop page's
Add to cart buttons, type WELCOME10 into the checkout page's Discount code field and press Apply, read the
subtotal, discount, and total the page shows, then pay with a good card. The stored order must record the code,
discount, and total the page showed, and the payments service's charge must be for that reduced total. Page
claims are read from the browser's screen; stored claims from the shop and payments databases, read-only and
without app code. The cart is priced from the shop database's catalog.

Side effects: empties the signed-in customer's cart, and leaves one discounted order and its charge in the local
databases. Nothing leaves this machine.

Needs Playwright for Python and Chromium in this python3. Run through the framework:
`python3 .agents/skills/verify-storefront/scripts/framework/vf.py run --
python3 .agents/skills/verify-storefront/scripts/checks/discount.py` from the project root.
Set VERIFY_KEEP_RECORDING=1 to keep a passing run's video. Exit 0 every step passed, 1 a step failed,
2 the run stopped before a verdict.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import reads  # noqa: E402
from report import Report  # noqa: E402
from screen import Screen  # noqa: E402
from shop_http import cents  # noqa: E402

SUB_FEATURES = ["discount.applied", "discount.charged"]
CODE, PERCENT = "WELCOME10", 10  # REQUIREMENTS.md DC-1 and issue #1: WELCOME10 takes 10% off the subtotal
GOOD_CARD = "4242 4242 4242 4242"
EXPIRY = "12/30"
MAX_LINES = 20  # more Remove clicks than the six-product catalog can need; a cart that won't empty stops the run


def stored_cart():
    return {line["product_id"]: line["quantity"] for line in reads.cart()}


def path_of(page):
    return re.sub(r"^https?://[^/]+", "", page.url).split("?")[0]


def empty_cart(screen):
    """Press Remove on every cart line until the cart page shows none."""
    page = screen.page
    screen.goto("/cart", "Opens the cart")
    for _ in range(MAX_LINES):
        if not page.get_by_role("button", name="Remove").count():
            return
        screen.act("Clicks Remove", lambda: page.get_by_role("button", name="Remove").first.click())


def add(screen, product):
    card = screen.page.locator(f'li.product[data-product-id="{product["id"]}"]')
    screen.act(f"Adds {product['name']}", lambda: card.get_by_role("button", name="Add to cart").click())


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    report = Report("discount", SUB_FEATURES, "what the user sees and stored state")
    try:
        with Screen(report) as screen:
            run(report, screen)
    except Exception as error:  # noqa: BLE001 - an action that can't be done means no verdict, not a pass
        report.stop(f"unexpected error: {error!r}")
    report.finish()


def run(report, screen):
    page = screen.page
    snap = screen.snapshot

    report.mark("step", "Step 1: Customer empties the cart and fills it")
    empty_cart(screen)
    if not report.judge("cart starts empty", [], lambda: ((c := stored_cart()) == {}, f"stored cart {c}", None), snap):
        report.stop("could not empty the cart through the Remove buttons, so no later step can be judged")
    catalog = reads.catalog()
    first, second = catalog[:2]
    screen.goto("/", "Opens the shop")
    add(screen, first)
    screen.goto("/", "Back to the shop")
    add(screen, first)
    screen.goto("/", "Back to the shop")
    add(screen, second)
    wanted = {first["id"]: 2, second["id"]: 1}
    if not report.judge("cart holds the test products", [], lambda: (
            (c := stored_cart()) == wanted, f"stored cart {c}, wanted {wanted}", None), snap):
        report.stop("the Add to cart buttons didn't build the test cart, so the discount can't be judged")
    prices = {product["id"]: product["price_cents"] for product in catalog}
    subtotal = sum(prices[product_id] * quantity for product_id, quantity in wanted.items())
    discount = subtotal * PERCENT // 100
    if discount * 100 != subtotal * PERCENT:
        report.stop(f"10% of the test cart's subtotal {subtotal} is not a whole number of cents; pick another cart")

    report.mark("step", f"Step 2: Customer applies {CODE} on the checkout page")
    screen.act("Clicks Check out", lambda: page.get_by_role("link", name="Check out").click())
    screen.act(f"Types {CODE}", lambda: page.get_by_label("Discount code").fill(CODE))
    screen.act("Clicks Apply", lambda: page.get_by_role("button", name="Apply").click())
    seen = {}

    def page_shows_discount():
        page.locator("[data-discount]").wait_for(state="visible", timeout=5_000)
        seen["subtotal"] = cents(page.locator("[data-subtotal]").inner_text())
        seen["discount"] = cents(page.locator("[data-discount]").inner_text().replace("−", "").replace("-", ""))
        seen["total"] = cents(page.locator("[data-order-total]").inner_text())
        label = page.locator("tr", has=page.locator("[data-discount]")).inner_text()
        pay_label = page.get_by_role("button", name=re.compile(r"^Pay\b")).inner_text()
        seen["pay"] = cents(pay_label.split("Pay", 1)[1])
        ok = (path_of(page) == "/checkout" and CODE in label and seen["subtotal"] == subtotal
              and seen["discount"] == discount and seen["total"] == subtotal - discount and seen["pay"] == seen["total"])
        return ok, (f"shown subtotal {seen['subtotal']}, discount {seen['discount']} ({label.strip()!r}), total {seen['total']}, "
                    f"Pay button {seen['pay']}; wanted subtotal {subtotal}, discount {discount}, total {subtotal - discount}"), None

    shown = report.judge("checkout page shows the subtotal, discount, and reduced total", ["discount.applied"], page_shows_discount, snap)

    report.mark("step", "Step 3: Customer pays with a good card")
    last_order = reads.latest_order_id()
    if path_of(page) == "/checkout":
        screen.act("Types the card details", lambda: (page.get_by_label("Card number").fill(GOOD_CARD), page.get_by_label("Expiry").fill(EXPIRY)))
        screen.act("Pays with card ending 4242", lambda: page.get_by_role("button", name=re.compile(r"^Pay\b")).click())
        try:
            page.wait_for_url(re.compile(r"/orders/\d+$"), timeout=10_000)
        except Exception:  # noqa: BLE001 - the steps below judge what happened instead
            pass
    placed = reads.orders_after(last_order)
    report.created(orders=[o["id"] for o in placed])
    order = reads.order(placed[-1]["id"]) if len(placed) == 1 else None

    def order_records_discount():
        if not shown:
            return False, "the checkout page didn't show the discount, so there is nothing to compare the order with", None
        if order is None:
            return False, f"expected one new order, found {[o['id'] for o in placed]}", None
        ok = (order["discount_code"] == CODE and order["discount_cents"] == seen["discount"]
              and order["total_cents"] == seen["total"])
        return ok, (f"order {order['id']} code {order['discount_code']!r} discount {order['discount_cents']} total {order['total_cents']}; "
                    f"shown code {CODE!r} discount {seen['discount']} total {seen['total']}"), {"order_id": order["id"]}

    def charged_reduced_total():
        if order is None:
            return False, f"expected one new order, found {[o['id'] for o in placed]}", None
        charge = reads.charge(order["charge_id"]) if order["charge_id"] else None
        if charge:
            report.created(charges=[charge["id"]])
        reduced = subtotal - discount
        ok = (order["status"] == "paid" and charge is not None and charge["status"] == "succeeded"
              and charge["amount_cents"] == order["total_cents"] == reduced)
        found = f"charge {charge['id']} {charge['status']} for {charge['amount_cents']}" if charge else f"no charge record for charge_id {order['charge_id']!r}"
        return ok, f"order {order['id']} {order['status']} total {order['total_cents']}, reduced total {reduced}; {found}", {
            "order_id": order["id"], "charge_id": order["charge_id"]}

    report.judge("order records the code, discount, and total shown", ["discount.applied"], order_records_discount, snap)
    report.judge("card is charged the reduced total", ["discount.charged"], charged_reduced_total, snap)


if __name__ == "__main__":
    main()
