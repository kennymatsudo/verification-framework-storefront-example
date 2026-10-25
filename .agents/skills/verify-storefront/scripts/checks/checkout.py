#!/usr/bin/env python3
"""Check checkout (REQUIREMENTS.md CO-1 to CO-5) on the running storefront in a real, recorded browser.

One journey through Chromium: empty the cart with the cart page's Remove buttons, fill it with the shop
page's Add to cart buttons, pay with a declining card (number ending 0002), then a good card, then try to
check out an empty cart, both by opening the checkout page and by pressing Pay in a checkout tab whose cart
was emptied in another tab. Page claims are read from the browser's screen; stored claims from the shop and
payments databases, read-only and without app code.

Side effects: empties the signed-in customer's cart, and leaves one paid order, one or more declined orders,
and their charges in the local databases. Nothing leaves this machine.

Needs Playwright for Python and Chromium in this python3. Run through the framework:
`python3 .agents/skills/verify-storefront/scripts/framework/vf.py run --
python3 .agents/skills/verify-storefront/scripts/checks/checkout.py` from the project root.
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

SUB_FEATURES = ["checkout.order-lines", "checkout.pay", "checkout.decline", "checkout.clears-cart", "checkout.empty-cart"]
GOOD_CARD = "4242 4242 4242 4242"
DECLINING_CARD = "4000 0000 0000 0002"  # README.md: a card ending 0002 is always declined
EXPIRY = "12/30"
MAX_LINES = 20  # more Remove clicks than the six-product catalog can need; a cart that won't empty stops the run


def stored_cart():
    return {line["product_id"]: line["quantity"] for line in reads.cart()}


def path_of(page_or_response):
    return re.sub(r"^https?://[^/]+", "", page_or_response.url).split("?")[0]


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


def pay(screen, card_number):
    """Pay with a typed card through the new-card form, which stays unique when saved cards add their own Pay buttons."""
    form = screen.page.locator("form.card-form")
    form.get_by_label("Card number").fill(card_number)
    form.get_by_label("Expiry").fill(EXPIRY)
    screen.act(f"Pays with card ending {card_number[-4:]}", lambda: form.get_by_role("button", name=re.compile(r"^Pay\b")).click())


def seen_summary(page):
    """The lines and total the checkout page shows: [(name, quantity, line cents)], total cents."""
    lines = []
    for row in page.locator("section.summary tbody tr").all():
        label, amount = [cell.inner_text().strip() for cell in row.locator("td").all()]
        name, quantity = label.rsplit(" × ", 1)
        lines.append((name, int(quantity), cents(amount)))
    return lines, cents(page.locator("[data-order-total]").inner_text())


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    report = Report("checkout", SUB_FEATURES, "what the user sees and stored state")
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
    first, second = reads.catalog()[:2]
    screen.goto("/", "Opens the shop")
    add(screen, first)
    screen.goto("/", "Back to the shop")
    add(screen, first)
    screen.goto("/", "Back to the shop")
    add(screen, second)
    wanted = {first["id"]: 2, second["id"]: 1}
    if not report.judge("cart holds the test products", [], lambda: (
            (c := stored_cart()) == wanted, f"stored cart {c}, wanted {wanted}", None), snap):
        report.stop("the Add to cart buttons didn't build the test cart, so checkout can't be judged")

    report.mark("step", "Step 2: Customer pays with a card that is declined")
    screen.act("Clicks Check out", lambda: page.get_by_role("link", name="Check out").click())
    cart_before = stored_cart()
    last_order, charges_before = reads.latest_order_id(), reads.charge_count()
    pay(screen, DECLINING_CARD)
    report.judge("the payment service saw the declined card", [], lambda: (
        (n := reads.charge_count() - charges_before) >= 1, f"new charges {n}", None), snap)

    def no_paid_order():
        attempts = reads.orders_after(last_order)
        report.created(orders=[o["id"] for o in attempts])
        statuses = {o["id"]: o["status"] for o in attempts}
        return all(s != "paid" for s in statuses.values()), f"orders from this attempt {statuses}", None

    def told_on_checkout_page():
        alert = page.get_by_role("alert")
        alert.wait_for(state="visible", timeout=5_000)
        text = alert.inner_text().strip()
        on_checkout = path_of(page) == "/checkout"
        return on_checkout and "declined" in text.lower(), f"page {path_of(page)}, alert {text!r}", None

    report.judge("declined attempt leaves no paid order", ["checkout.decline"], no_paid_order, snap)
    report.judge("declined card is reported on the checkout page", ["checkout.decline"], told_on_checkout_page, snap)
    report.judge("declined attempt leaves the cart as it was", ["checkout.decline"], lambda: (
        (now := stored_cart()) == cart_before, f"stored cart {now}, before {cart_before}", None), snap)

    report.mark("step", "Step 3: Customer pays with a good card")
    screen.goto("/checkout", "Opens the checkout page")
    last_order = reads.latest_order_id()
    seen = {}

    def read_checkout_page():
        if path_of(page) != "/checkout":
            return False, f"checkout page not shown; at {path_of(page)}", None
        seen["lines"], seen["total"] = seen_summary(page)
        return bool(seen["lines"]), f"shown lines {seen['lines']}, total {seen['total']}", None

    report.judge("checkout page shows the cart", [], read_checkout_page, snap)
    if path_of(page) == "/checkout":
        pay(screen, GOOD_CARD)
        try:
            page.wait_for_url(re.compile(r"/orders/\d+$"), timeout=10_000)
        except Exception:  # noqa: BLE001 - the steps below judge what happened instead
            pass
    placed = reads.orders_after(last_order)
    report.created(orders=[o["id"] for o in placed])
    order = reads.order(placed[-1]["id"]) if len(placed) == 1 else None

    def order_matches_page():
        if order is None:
            return False, f"expected one new order, found {[o['id'] for o in placed]}", None
        stored = [(line["name"], line["quantity"], line["unit_price_cents"] * line["quantity"]) for line in order["lines"]]
        matches = stored == seen.get("lines") and order["total_cents"] == seen.get("total")
        return matches, f"order {order['id']} lines {stored} total {order['total_cents']}; shown {seen.get('lines')} total {seen.get('total')}", {"order_id": order["id"]}

    def paid_with_matching_charge():
        if order is None:
            return False, f"expected one new order, found {[o['id'] for o in placed]}", None
        charge = reads.charge(order["charge_id"]) if order["charge_id"] else None
        if charge:
            report.created(charges=[charge["id"]])
        ok = (order["status"] == "paid" and charge is not None and charge["status"] == "succeeded"
              and charge["amount_cents"] == order["total_cents"])
        found = f"charge {charge['id']} {charge['status']} for {charge['amount_cents']}" if charge else f"no charge record for charge_id {order['charge_id']!r}"
        return ok, f"order {order['id']} {order['status']} total {order['total_cents']}; {found}", {"order_id": order["id"], "charge_id": order["charge_id"]}

    def cart_empty_after_paying():
        if order is None or order["status"] != "paid":
            return False, f"no paid order to follow; new orders {[(o['id'], o['status']) for o in placed]}", None
        stored = stored_cart()
        badge = page.locator("[data-cart-count]")
        try:
            badge.filter(has_text=re.compile(r"^\s*0\s*$")).wait_for(timeout=3_000)
        except Exception:  # noqa: BLE001 - the badge's text below decides
            pass
        shown = badge.inner_text().strip()
        return stored == {} and shown == "0", f"stored cart {stored}, badge on {path_of(page)} shows {shown!r}", None

    report.judge("order stores the lines and total shown at checkout", ["checkout.order-lines"], order_matches_page, snap)
    report.judge("paid order records a charge for its total", ["checkout.pay"], paid_with_matching_charge, snap)
    report.judge("cart is empty after paying", ["checkout.clears-cart"], cart_empty_after_paying, snap)

    report.mark("step", "Step 4: Customer tries to check out an empty cart")
    if stored_cart():
        empty_cart(screen)  # keeps this step independent of whether paying emptied the cart

    def no_payment_form():
        screen.goto("/checkout", "Opens the checkout page with an empty cart")
        pay_button = page.get_by_role("button", name=re.compile(r"^Pay\b")).count()
        card_field = page.get_by_label("Card number").count()
        empty = stored_cart() == {}
        return empty and not pay_button and not card_field, (
            f"at {path_of(page)}, Pay buttons {pay_button}, card number fields {card_field}, cart empty {empty}"), None

    report.judge("empty cart shows no payment form", ["checkout.empty-cart"], no_payment_form, snap)

    # A checkout tab opened while the cart had items, then the cart emptied in another tab: Pay still submits.
    screen.goto("/", "Opens the shop")
    add(screen, first)
    screen.goto("/checkout", "Opens the checkout page")
    other = page.context.new_page()
    report.mark("action", "Opens the cart in another tab")
    other.goto("/cart")
    for _ in range(MAX_LINES):
        if not other.get_by_role("button", name="Remove").count():
            break
        report.mark("action", "Clicks Remove in another tab")
        other.get_by_role("button", name="Remove").first.click()
        other.wait_for_load_state()
    other.close()
    last_order, charges_before = reads.latest_order_id(), reads.charge_count()
    submitted = None
    if path_of(page) == "/checkout":
        page.get_by_label("Card number").fill(GOOD_CARD)
        page.get_by_label("Expiry").fill(EXPIRY)
        report.mark("action", "Pays in the first tab")
        with page.expect_response(lambda res: res.request.method == "POST" and path_of(res) == "/checkout") as posted:
            page.locator("form.card-form").get_by_role("button", name=re.compile(r"^Pay\b")).click()
        submitted = posted.value.status
        page.wait_for_load_state()

    def stale_pay_refused():
        new_orders = reads.orders_after(last_order)
        report.created(orders=[o["id"] for o in new_orders])
        new_charges = reads.charge_count() - charges_before
        # A server error that stored nothing is a crash, not the shop refusing the checkout.
        ok = submitted is not None and submitted < 500 and not new_orders and new_charges == 0 and stored_cart() == {}
        return ok, (f"Pay submitted: {submitted is not None} (status {submitted}); new orders {[o['id'] for o in new_orders]}, "
                    f"new charges {new_charges}, now at {path_of(page)}"), None

    report.judge("paying for an emptied cart stores no order and no charge", ["checkout.empty-cart"], stale_pay_refused, snap)


if __name__ == "__main__":
    main()
