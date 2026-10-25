# Discount codes

The signed-in customer enters a discount code on the checkout page, sees the discount taken off the subtotal, and pays the reduced total.

## Sub-features

- discount.applied: a valid code entered at checkout takes its percentage off the subtotal; the checkout page shows the subtotal, the discount, and the reduced total, and the stored order records the code, the discount, and the reduced total.
- discount.charged: the amount charged to the card equals the reduced total.

## How a user reaches it

- Checkout page, "Discount code" field with an "Apply" button: a form `GET /checkout?code=<code>` that reloads the page with the discount shown.
- Checkout page, "Pay" button: the card form `POST /checkout` carries the code in a hidden `code` field.

## Request flow

`GET /checkout?code=` prices the cart and looks the code up in `DISCOUNT_CODES` (shop/db.py). `POST /checkout` repeats that from the hidden field, stores the order with `discount_code`, `discount_cents`, and the reduced `total_cents`, then asks the payments service's `POST /charges` to charge the card.

## Verification plan

Source: [REQUIREMENTS.md](../../../../REQUIREMENTS.md) DC-1 and DC-2 at f1dd5de; issue #1 acceptance criteria 1 to 3 (read 2026-10-25); the developer approved this plan on 2026-10-25 while verifying PR #2. DC-3 (an unknown code is rejected) is left to the shop's unit tests: only the shop's own code decides it.

The check drives a real Chromium browser through Playwright and records the run. It empties the cart through the cart page's "Remove" buttons, fills it through the shop page's "Add to cart" buttons (two of the first product, one of the second), types WELCOME10 into the Discount code field, presses Apply, and pays with a good card. The expected subtotal comes from the shop database's catalog; WELCOME10's 10% comes from DC-1's source, issue #1. Page claims are read from the browser's screen; stored claims from the shop and payments databases directly, without app code.

- discount.applied: after Apply, the checkout page shows a subtotal equal to the cart priced from the catalog, a discount line naming WELCOME10 for 10% of it, a total and a Pay button for the subtotal less the discount; after paying, the new order's stored code, discount, and total equal what the page showed. Reads the screen, then stored state.
- discount.charged: the new order is stored as `paid`, and the payments service's record of its charge succeeded for an amount equal to the order's stored reduced total. Reads stored state in both databases.

## How to prove it

- discount.applied: `python3 .agents/skills/verify-storefront/scripts/checks/discount.py`. Reads the checkout page on screen, then the stored order.
- discount.charged: `python3 .agents/skills/verify-storefront/scripts/checks/discount.py`. Reads the stored order and the payments service's charge record (state). Not break-tested: broken on current code; passes on a planned fix (the shop charges the reduced total instead of the subtotal).

## Gotchas

- Needs Playwright for Python and its Chromium in the system `python3`, not the project's uv environment.
- The cart is shared: one customer is always signed in, so the check clears whatever is in the local dev cart.
- A `data/shop.sqlite` created before discount codes lacks the `discount_code` and `discount_cents` columns; the schema is only created when missing, so start from a fresh `data/`.
