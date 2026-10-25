# Checkout

The signed-in customer reviews the cart on the checkout page, pays by card, and lands on the order's page; a declined card keeps them on the checkout page with their cart intact.

## Sub-features

- checkout.order-lines: placing an order stores the lines and the total exactly as the customer saw them on the checkout page.
- checkout.pay: when the card is charged successfully, the order is marked paid and records the payment's ID, and the amount charged equals the order's total.
- checkout.decline: when the card is declined, the order is not marked paid, the customer is told on the checkout page, and the cart is left as it was.
- checkout.clears-cart: after a paid order, the cart is empty.
- checkout.empty-cart: an empty cart cannot be checked out.

## How a user reaches it

- Cart page, "Check out" link to `GET /checkout`.
- Checkout page, card form with a "Pay" button: a form `POST /checkout` with `name_on_card`, `card_number`, and `expiry`.
- The shop charges the card through the payments service's `POST /charges`; a card number ending `0002` is always declined.

## Request flow

`POST /checkout` reads the cart, stores an order with its lines as `pending`, asks the payments service to charge the total, then marks the order `paid` with the charge ID and empties the cart, or marks it `declined` and renders the checkout page again with an error.

## Verification plan

Source: [REQUIREMENTS.md](../../../../REQUIREMENTS.md) CO-1 to CO-5, [README.md](../../../../README.md) for the declining card; the developer agreed this plan on 2026-10-25, including that a cart changed in another tab between opening checkout and paying is out of scope.

The check drives a real Chromium browser through Playwright and records the run. It fills a cart through the shop page's "Add to cart" buttons, empties it first through the cart page's "Remove" buttons, then walks one journey: a declined card, then a good card, then an empty cart. Page claims are read from the browser's screen; stored claims are read from the shop and payments databases directly, without app code.

- checkout.order-lines: read the lines (name, quantity, line amount) and total shown on the checkout page before paying; the new order's stored lines and total equal them. Reads the screen, then stored state.
- checkout.pay: pay with a good card; the new order is stored as `paid` with a charge ID, and the payments service's record for that charge succeeded for an amount equal to the order's stored total. Reads stored state in both databases.
- checkout.decline: pay with a card ending `0002`; no order created by that attempt is stored as `paid`, the browser is still on the checkout page showing an alert that says the card was declined, and the stored cart equals the cart before the attempt. Reads the screen and stored state.
- checkout.clears-cart: after the paid order, the stored cart has no rows and the header badge on screen shows 0. Reads stored state and the screen.
- checkout.empty-cart: with an empty cart, opening the checkout page shows no payment form; and submitting the checkout form with an empty cart, as a stale tab would, stores no new order and makes no new charge. Reads the screen and stored state in both databases.

## How to prove it

- checkout.order-lines: `python3 .agents/skills/verify-storefront/scripts/checks/checkout.py`. Reads the checkout page on screen, then the stored order and lines.
- checkout.pay: `python3 .agents/skills/verify-storefront/scripts/checks/checkout.py`. Reads the stored order and the payments service's charge record (state).
- checkout.decline: `python3 .agents/skills/verify-storefront/scripts/checks/checkout.py`. Reads the alert on screen and the stored orders and cart.
- checkout.clears-cart: `python3 .agents/skills/verify-storefront/scripts/checks/checkout.py`. Reads the stored cart and the header badge on screen.
- checkout.empty-cart: `python3 .agents/skills/verify-storefront/scripts/checks/checkout.py`. Reads the screen and the stored orders and charges.

## Gotchas

- Needs Playwright for Python and its Chromium in the system `python3`, not the project's uv environment.
- The cart is shared: one customer is always signed in, so the check clears whatever is in the local dev cart.
