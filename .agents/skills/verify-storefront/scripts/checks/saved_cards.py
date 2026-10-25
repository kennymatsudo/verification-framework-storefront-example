#!/usr/bin/env python3
"""Check saved cards (REQUIREMENTS.md SC-1 to SC-4) on the running storefront in a real, recorded browser.

One journey through Chromium. With one product in the cart each time, the customer pays with "Save this card"
ticked on a declining card (not saved), pays without ticking it (not saved), pays with it ticked on a card
expiring this month and on one that expired last month (both saved), then sees the saved cards on the
checkout page, pays with the card expiring this month, has the expired one refused, and removes both cards,
one from the checkout page and one from the Saved cards page. Page claims are read from the browser's screen;
stored claims from the shop and payments databases, read-only and without app code.

Expiry months come from today's UTC date when the check runs. The expired card is saved by typing it at
checkout, which works because the stand-in payments service charges a typed card whatever its expiry.

Side effects: empties the signed-in customer's cart, and leaves paid and declined orders and their charges in
the local databases. It removes the saved cards it created; saved cards that existed before it ran are left
alone. Nothing leaves this machine.

Needs Playwright for Python and Chromium in this python3. Run through the framework:
`python3 .agents/skills/verify-storefront/scripts/framework/vf.py run --
python3 .agents/skills/verify-storefront/scripts/checks/saved_cards.py` from the project root.
Set VERIFY_KEEP_RECORDING=1 to keep a passing run's video. Exit 0 every step passed, 1 a step failed,
2 the run stopped before a verdict.
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import reads  # noqa: E402
from report import Report  # noqa: E402
from screen import Screen  # noqa: E402
from shop_http import cents  # noqa: E402

SUB_FEATURES = ["saved-cards.save", "saved-cards.pay", "saved-cards.expired", "saved-cards.remove"]
DECLINING_CARD = "4000 0000 0000 0002"  # README.md: a card ending 0002 is always declined
UNSAVED_CARD = "4242 4242 4242 4242"
CURRENT_CARD = "5555 5555 5555 4444"  # saved, expiring this month: usable through its last day
EXPIRED_CARD = "4111 1111 1111 1111"  # saved, expired at the end of last month
MAX_LINES = 20  # more Remove clicks than the six-product catalog can need; a cart that won't empty stops the run


def expiry_months():
    """(this month, last month) as MM/YY from today's UTC date."""
    today = datetime.now(timezone.utc).date()
    last_year, last_month = (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)
    return f"{today.month:02d}/{today.year % 100:02d}", f"{last_month:02d}/{last_year % 100:02d}"


def path_of(page_or_response):
    return re.sub(r"^https?://[^/]+", "", page_or_response.url).split("?")[0]


def digits(card_number):
    return card_number.replace(" ", "")


def run_cards(before):
    """Saved cards the shop stores that this run created: IDs above the highest one before it started."""
    return [card for card in reads.saved_cards() if card["id"] > before]


def empty_cart(screen):
    page = screen.page
    screen.goto("/cart", "Opens the cart")
    for _ in range(MAX_LINES):
        if not page.get_by_role("button", name="Remove").count():
            return
        screen.act("Clicks Remove", lambda: page.get_by_role("button", name="Remove").first.click())


def fill_cart_and_open_checkout(screen, product):
    """Empty the cart, add one product through the shop page, and open the checkout page."""
    empty_cart(screen)
    screen.goto("/", "Opens the shop")
    card = screen.page.locator(f'li.product[data-product-id="{product["id"]}"]')
    screen.act(f"Adds {product['name']}", lambda: card.get_by_role("button", name="Add to cart").click())
    screen.goto("/checkout", "Opens the checkout page")


def pay_new_card(screen, card_number, expiry, save):
    """Fill the new-card form, tick or leave "Save this card for later", and press its Pay button."""
    form = screen.page.locator("form.card-form")
    form.get_by_label("Card number").fill(card_number)
    form.get_by_label("Expiry").fill(expiry)
    form.get_by_label("Save this card for later").set_checked(save)
    label = f"Pays with card ending {card_number[-4:]}" + (", saving it" if save else "")
    screen.act(label, lambda: form.get_by_role("button", name=re.compile(r"^Pay\b")).click())


def shown_card_row(page, last4):
    """The saved-card rows the page shows for a card ending last4."""
    return page.locator("ul.saved-cards li").filter(has_text=re.compile(rf"\bending {last4}\b"))


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    report = Report("saved-cards", SUB_FEATURES, "what the user sees and stored state")
    try:
        with Screen(report) as screen:
            run(report, screen)
    except Exception as error:  # noqa: BLE001 - an action that can't be done means no verdict, not a pass
        report.stop(f"unexpected error: {error!r}")
    report.finish()


def run(report, screen):
    page = screen.page
    snap = screen.snapshot
    this_month, last_month = expiry_months()
    product = reads.catalog()[0]
    cards_before = reads.latest_saved_card_id()
    leftovers = [c["id"] for c in reads.saved_cards() if c["last4"] in (CURRENT_CARD[-4:], EXPIRED_CARD[-4:])]
    if leftovers:
        report.stop(f"saved cards {leftovers} already end in {CURRENT_CARD[-4:]} or {EXPIRED_CARD[-4:]}, likely left by "
                    "an earlier failed run; remove them on the Saved cards page and rerun")

    report.mark("step", "Step 1: Customer ticks Save on a card that is declined")
    fill_cart_and_open_checkout(screen, product)
    if path_of(page) != "/checkout":
        report.stop(f"the checkout page didn't open with a product in the cart; at {path_of(page)}")
    last_order, held_before = reads.latest_order_id(), reads.payments_card_count()
    pay_new_card(screen, DECLINING_CARD, this_month, save=True)

    def declined_attempt():
        attempts = reads.orders_after(last_order)
        report.created(orders=[o["id"] for o in attempts])
        return bool(attempts) and all(o["status"] == "declined" for o in attempts), (
            f"orders from this attempt {[(o['id'], o['status']) for o in attempts]}"), None

    report.judge("the declining card was declined", [], declined_attempt, snap)
    def nothing_saved(held_before, attempted):
        new, held = run_cards(cards_before), reads.payments_card_count() - held_before
        return attempted and new == [] and held == 0, (
            f"payment attempted {attempted}; shop saved cards from this run {[(c['id'], c['last4']) for c in new]}, "
            f"new payments cards {held}"), None

    declined = bool(reads.orders_after(last_order))
    report.judge("a declined card is not saved", ["saved-cards.save"], lambda: nothing_saved(held_before, declined), snap)

    report.mark("step", "Step 2: Customer pays without ticking Save")
    fill_cart_and_open_checkout(screen, product)
    last_order, held_before = reads.latest_order_id(), reads.payments_card_count()
    pay_new_card(screen, UNSAVED_CARD, this_month, save=False)
    paid = [o for o in reads.orders_after(last_order) if o["status"] == "paid"]
    report.created(orders=[o["id"] for o in reads.orders_after(last_order)])
    report.judge("the unticked payment went through", [], lambda: (
        len(paid) == 1, f"paid orders from this attempt {[o['id'] for o in paid]}", None), snap)
    report.judge("a card is not saved unless the customer asks", ["saved-cards.save"],
                 lambda: nothing_saved(held_before, bool(paid)), snap)

    report.mark("step", "Step 3: Customer saves a card expiring this month and one that has expired")
    saved = {}
    for name, number, expiry in (("current", CURRENT_CARD, this_month), ("expired", EXPIRED_CARD, last_month)):
        fill_cart_and_open_checkout(screen, product)
        last_order = reads.latest_order_id()
        known = {c["id"] for c in run_cards(cards_before)}
        pay_new_card(screen, number, expiry, save=True)
        report.created(orders=[o["id"] for o in reads.orders_after(last_order)])
        new = [c for c in run_cards(cards_before) if c["id"] not in known]
        saved[name] = new[0] if len(new) == 1 else None
        if saved[name]:
            report.created(saved_cards=[saved[name]["id"]])

        def stored_as_shown(name=name, number=number, expiry=expiry, new=new, last_order=last_order):
            orders = reads.orders_after(last_order)
            if not (len(orders) == 1 and orders[0]["status"] == "paid"):
                return False, f"expected one paid order, found {[(o['id'], o['status']) for o in orders]}", None
            if len(new) != 1:
                return False, f"expected one new saved card, found {[(c['id'], c['last4']) for c in new]}", None
            card = new[0]
            held = reads.payments_card(card["payments_card_id"])
            ok = (card["last4"] == number[-4:] and card["expiry"] == expiry and held is not None
                  and held["last4"] == number[-4:])
            return ok, (f"shop stores card {card['id']} ending {card['last4']} expiring {card['expiry']}, wanted "
                        f"{number[-4:]} {expiry}; payments holds {held}"), {"saved_card_id": card["id"]}

        report.judge(f"saving the {name} card stores its last four and expiry", ["saved-cards.save"], stored_as_shown, snap)

    def full_numbers_not_stored():
        found = {number[-4:]: reads.shop_columns_containing(digits(number))
                 for number in (CURRENT_CARD, EXPIRED_CARD, UNSAVED_CARD, DECLINING_CARD)}
        return not any(found.values()), f"shop columns holding a full card number: {found}", None

    report.judge("the shop stores no full card number", ["saved-cards.save"], full_numbers_not_stored, snap)

    report.mark("step", "Step 4: Checkout shows the saved cards; the expired one can't be picked")
    fill_cart_and_open_checkout(screen, product)

    def card_shown(number, expiry):
        row = shown_card_row(page, number[-4:])
        try:
            row.first.wait_for(timeout=3_000)
        except Exception:  # noqa: BLE001 - the count below decides
            pass
        if row.count() != 1:
            return False, f"rows showing a card ending {number[-4:]}: {row.count()}", None
        text = " ".join(row.inner_text().split())
        return expiry in text, f"row shows {text!r}, wanted expiry {expiry}", None

    report.judge("checkout shows the current card by last four and expiry", ["saved-cards.save"],
                 lambda: card_shown(CURRENT_CARD, this_month), snap)
    report.judge("checkout shows the expired card by last four and expiry", ["saved-cards.save"],
                 lambda: card_shown(EXPIRED_CARD, last_month), snap)

    def offered(number, wanted):
        row = shown_card_row(page, number[-4:])
        if row.count() != 1:
            return False, f"rows showing a card ending {number[-4:]}: {row.count()}", None
        pay_buttons = row.get_by_role("button", name=re.compile(r"^Pay\b")).count()
        labelled = bool(re.search(r"\bExpired\b", row.inner_text()))
        ok = (pay_buttons == 1 and not labelled) if wanted else (pay_buttons == 0 and labelled)
        return ok, f"card ending {number[-4:]}: Pay buttons {pay_buttons}, labelled Expired {labelled}", None

    report.judge("a card expiring this month is offered for payment", ["saved-cards.expired"],
                 lambda: offered(CURRENT_CARD, True), snap)
    report.judge("an expired card is labelled Expired with no way to pay", ["saved-cards.expired"],
                 lambda: offered(EXPIRED_CARD, False), snap)

    report.mark("step", "Step 5: A stale checkout form submits the expired card")
    # The page offers no Pay button for an expired card, so this posts the form a checkout tab opened before
    # the card expired would still hold, to the same /checkout route the button uses.
    last_order, charges_before = reads.latest_order_id(), reads.charge_count()
    cart_at_post = reads.cart()
    refused = {}
    if saved.get("expired"):
        report.mark("action", "Submits the expired card's Pay form from a stale tab")
        response = page.request.post("/checkout", form={"saved_card_id": str(saved["expired"]["id"])})
        refused = {"status": response.status, "text": response.text()}

    def expired_refused():
        if not refused:
            return False, "no expired card was saved, so nothing could be submitted", None
        new_orders = reads.orders_after(last_order)
        report.created(orders=[o["id"] for o in new_orders])
        new_charges = reads.charge_count() - charges_before
        # The page always lists the card with an Expired label, so only the alert says why it was refused.
        alert = re.search(r'role="alert"[^>]*>([^<]*)<', refused["text"])
        told = alert.group(1).strip() if alert else None
        ok = (bool(cart_at_post) and refused["status"] < 500 and not new_orders and new_charges == 0
              and told is not None and "has expired" in told.lower())
        return ok, (f"cart when posted {cart_at_post}, status {refused['status']}, alert {told!r}, "
                    f"new orders {[o['id'] for o in new_orders]}, new charges {new_charges}"), None

    report.judge("an expired card is refused with no order or charge", ["saved-cards.expired"], expired_refused, snap)

    report.mark("step", "Step 6: Customer pays with the saved card expiring this month")
    screen.goto("/checkout", "Opens the checkout page")
    last_order = reads.latest_order_id()
    try:
        shown_total = cents(page.locator("[data-order-total]").inner_text())
    except Exception:  # noqa: BLE001 - a missing total fails the pay step below rather than stopping the run
        shown_total = None
    row = shown_card_row(page, CURRENT_CARD[-4:])
    if row.count() == 1 and row.get_by_role("button", name=re.compile(r"^Pay\b")).count() == 1:
        screen.act("Pays with the saved card ending 4444",
                   lambda: row.get_by_role("button", name=re.compile(r"^Pay\b")).click())
        try:
            page.wait_for_url(re.compile(r"/orders/\d+$"), timeout=10_000)
        except Exception:  # noqa: BLE001 - the step below judges what happened instead
            pass

    def charged_to_saved_card():
        card = saved.get("current")
        if card is None:
            return False, "the card expiring this month was not saved", None
        placed = reads.orders_after(last_order)
        report.created(orders=[o["id"] for o in placed])
        if len(placed) != 1:
            return False, f"expected one new order, found {[(o['id'], o['status']) for o in placed]}", None
        order = placed[0]
        charge = reads.charge(order["charge_id"]) if order["charge_id"] else None
        if charge:
            report.created(charges=[charge["id"]])
        ok = (order["status"] == "paid" and charge is not None and charge["status"] == "succeeded"
              and charge["card_id"] == card["payments_card_id"] and charge["card_last4"] == CURRENT_CARD[-4:]
              and charge["amount_cents"] == order["total_cents"] == shown_total)
        found = (f"charge {charge['id']} {charge['status']} to card {charge['card_id']} ending {charge['card_last4']} "
                 f"for {charge['amount_cents']}") if charge else f"no charge record for {order['charge_id']!r}"
        return ok, (f"order {order['id']} {order['status']} total {order['total_cents']} (shown {shown_total}); {found}; "
                    f"saved card's payments ID {card['payments_card_id']}"), {"order_id": order["id"], "charge_id": order["charge_id"]}

    report.judge("paying with a saved card charges that card", ["saved-cards.pay"], charged_to_saved_card, snap)

    report.mark("step", "Step 7: Customer removes the expired card at checkout and the other on the Saved cards page")

    def remove(where, path, number, card_key):
        card = saved.get(card_key)
        if card is None:
            return False, f"the {card_key} card was not saved, so it can't be removed", None
        row = shown_card_row(page, number[-4:])
        if row.count() != 1:
            return False, f"on {where}, rows showing a card ending {number[-4:]}: {row.count()}", None
        screen.act(f"Removes the card ending {number[-4:]}", lambda: row.get_by_role("button", name="Remove").click())
        still_shown = shown_card_row(page, number[-4:]).count()
        still_stored = [c["id"] for c in reads.saved_cards() if c["id"] == card["id"]]
        held = reads.payments_card(card["payments_card_id"])
        ok = path_of(page) == path and not still_shown and not still_stored and held is None
        return ok, (f"after Remove on {where}, now at {path_of(page)}: rows shown {still_shown}, shop rows "
                    f"{still_stored}, payments holds {held}"), {"saved_card_id": card["id"]}

    fill_cart_and_open_checkout(screen, product)
    report.judge("removing a card at checkout forgets it", ["saved-cards.remove"],
                 lambda: remove("the checkout page", "/checkout", EXPIRED_CARD, "expired"), snap)
    screen.goto("/cards", "Opens the Saved cards page")
    report.judge("removing a card on the Saved cards page forgets it", ["saved-cards.remove"],
                 lambda: remove("the Saved cards page", "/cards", CURRENT_CARD, "current"), snap)
    empty_cart(screen)


if __name__ == "__main__":
    main()
