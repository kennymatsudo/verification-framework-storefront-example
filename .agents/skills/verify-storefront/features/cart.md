# Cart

The signed-in customer collects products in a cart, sees each line and the total on the cart page, and sees the number of units in the header badge on every page.

## Sub-features

- cart.add: adding a product puts one of it in the cart, and adding it again raises its quantity by one.
- cart.remove: removing a product takes every unit of it out of the cart.
- cart.total: the cart page's total equals the sum of its lines, each line being the product's price times its quantity.
- cart.badge: the cart badge in the header shows the number of units in the cart.

## How a user reaches it

- Shop page (`/`), "Add to cart" button: a form `POST /cart/add` with `product_id`.
- Cart page (`/cart`), "Remove" button on a line: a form `POST /cart/remove` with `product_id`.
- Header "Cart" link with its badge, on every page.

## Verification plan

Source: [REQUIREMENTS.md](../../../../REQUIREMENTS.md) CT-1 to CT-4; the developer agreed this plan on 2026-10-25.

The check submits the shop's own forms over HTTP, exactly as the browser posts them (the pages use no JavaScript), and first empties the cart through the real Remove form so it starts from a known state. Product prices come from the shop database's catalog, not from the app.

- cart.add: add a product to an empty cart; its stored cart row has quantity 1. Add it again; the row has quantity 2. Reads stored state.
- cart.remove: with a product at quantity 2 and another product in the cart, remove the first; no stored row remains for it and the other product's row is unchanged. Reads stored state.
- cart.total: with several products at quantities above one, read the served cart page: each line's quantity and line amount equal the stored quantity times the catalog price, and the page's total equals the sum of those. Reads the served HTML, not a browser render.
- cart.badge: with several products at quantities above one, the header badge on the served cart and shop pages equals the stored sum of quantities, not the number of lines. Reads the served HTML, not a browser render.

## How to prove it

- cart.add: `python3 .agents/skills/verify-storefront/scripts/checks/cart.py`. Reads the stored cart rows (state).
- cart.remove: `python3 .agents/skills/verify-storefront/scripts/checks/cart.py`. Reads the stored cart rows (state).
- cart.total: `python3 .agents/skills/verify-storefront/scripts/checks/cart.py`. Reads the served cart page's lines and total against catalog prices.
- cart.badge: `python3 .agents/skills/verify-storefront/scripts/checks/cart.py`. Reads the served header badge against the stored quantities.

## Gotchas

- The cart is shared: one customer is always signed in, so the check clears whatever is in the local dev cart.
