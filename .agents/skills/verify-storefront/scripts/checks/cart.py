#!/usr/bin/env python3
"""Check the cart (REQUIREMENTS.md CT-1 to CT-4) on the running storefront.

Submits the shop's own "Add to cart" and "Remove" forms over HTTP, the same requests the buttons send, then
reads the stored cart from the shop's database and the served cart and shop pages' HTML. Prices come from
the stored catalog. It reads served HTML, not a browser render.

Side effects: empties the signed-in customer's cart first, then leaves two test products in it. Local only.

Run through the framework: `python3 .agents/skills/verify-storefront/scripts/framework/vf.py run --
python3 .agents/skills/verify-storefront/scripts/checks/cart.py` from the project root.
Exit 0 every step passed, 1 a step failed, 2 the run stopped before a verdict.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import reads  # noqa: E402
import shop_http  # noqa: E402
from report import Report  # noqa: E402

SUB_FEATURES = ["cart.add", "cart.remove", "cart.total", "cart.badge"]
MAX_REMOVES = 10  # rounds of Remove presses before setup gives up


def stored_quantities():
    return {line["product_id"]: line["quantity"] for line in reads.cart()}


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    report = Report("cart", SUB_FEATURES, "state and served HTML")
    try:
        run(report)
    except Exception as error:  # noqa: BLE001 - an action that can't be done means no verdict, not a pass
        report.stop(f"unexpected error: {error!r}")
    report.finish()


def run(report):

    report.mark("step", "Step 1: Start from an empty cart")
    try:
        # Press Remove until the cart is empty, as a customer would; bounded so a cart that won't empty stops the run.
        for _ in range(MAX_REMOVES):
            remaining = stored_quantities()
            if not remaining:
                break
            for product_id in remaining:
                report.mark("action", f"Removes product {product_id}")
                shop_http.remove_from_cart(product_id)
        catalog = reads.catalog()
    except Exception as error:  # noqa: BLE001
        report.stop(f"could not reach the shop or its database: {error!r}")
    if not report.step("cart starts empty", stored_quantities() == {}, detail=f"stored cart {stored_quantities()}"):
        report.stop("could not empty the cart through the Remove form, so no later step can be judged")
    if len(catalog) < 3:
        report.stop(f"the catalog has {len(catalog)} products; the check needs 3")
    first, second, third = catalog[:3]
    prices = {product["id"]: product["price_cents"] for product in catalog}

    report.mark("step", "Step 2: Add the same product twice")
    report.mark("action", f"Adds {first['name']}")
    shop_http.add_to_cart(first["id"])
    report.judge("first add puts one in the cart", ["cart.add"], lambda: (
        (q := stored_quantities()) == {first["id"]: 1}, f"stored cart {q}", None))
    report.mark("action", f"Adds {first['name']} again")
    shop_http.add_to_cart(first["id"])
    report.judge("second add raises the quantity by one", ["cart.add"], lambda: (
        (q := stored_quantities()).get(first["id"]) == 2, f"stored cart {q}", None))

    report.mark("step", "Step 3: Fill the cart with several products")
    for product, times in ((second, 3), (third, 2)):
        for _ in range(times):
            report.mark("action", f"Adds {product['name']}")
            shop_http.add_to_cart(product["id"])
    # Build the expected cart from the stored rows rather than from the adds, so a broken add can't fail
    # the total and badge steps too.
    expected = stored_quantities()
    report.step("cart holds several products", len(expected) == 3 and all(q > 1 for q in expected.values()),
                detail=f"stored cart {expected}")

    report.mark("step", "Step 4: Read the cart page")

    def lines_match():
        cart_page = shop_http.page("/cart")
        shown = {}
        for row in cart_page.find_all("data-product-id"):
            shown[int(row.attrs["data-product-id"])] = (
                int(row.find("data-quantity").text()), shop_http.cents(row.find("data-line-total").text()))
        want = {pid: (qty, prices[pid] * qty) for pid, qty in expected.items()}
        return shown == want, f"page lines {shown}, expected {want}", None

    def total_matches():
        cart_page = shop_http.page("/cart")
        shown = shop_http.cents(cart_page.find("data-cart-total").text())
        want = sum(prices[pid] * qty for pid, qty in expected.items())
        return shown == want, f"page total {shown}, expected {want}", None

    report.judge("cart page lines are price times quantity", ["cart.total"], lines_match)
    report.judge("cart page total is the sum of its lines", ["cart.total"], total_matches)

    def badges_show_units():
        units = sum(expected.values())
        shown = {path: shop_http.page(path).find("data-cart-count").text() for path in ("/cart", "/")}
        return all(value == str(units) for value in shown.values()), f"badges {shown}, units in cart {units}", None

    report.judge("header badge shows the units in the cart", ["cart.badge"], badges_show_units)

    report.mark("step", "Step 5: Remove a product with several units")
    before = stored_quantities()
    others = {pid: qty for pid, qty in before.items() if pid != first["id"]}
    report.mark("action", f"Removes {first['name']}")
    shop_http.remove_from_cart(first["id"])
    def removed_every_unit():
        after = stored_quantities()
        return (before.get(first["id"], 0) > 1 and after == others,
                f"before {before}, after {after}, expected {others}", None)

    report.judge("remove takes every unit out and leaves the rest", ["cart.remove"], removed_every_unit)


if __name__ == "__main__":
    main()
