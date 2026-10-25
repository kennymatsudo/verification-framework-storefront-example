# Saved cards

The signed-in customer can save a card when paying, pay with it on a later checkout instead of typing it, cannot pay with one that has expired, and can remove a saved card.

## Sub-features

- saved-cards.save: at checkout the customer can choose to save the card; only a card whose charge succeeded is saved, it is shown by its last four digits and expiry, and the shop never stores the full number.
- saved-cards.pay: on a later checkout the customer can pay with a saved card instead of typing one, and the order is charged to that card.
- saved-cards.expired: a saved card is usable through the last day of its expiry month; once expired it stays listed at checkout, labelled Expired, cannot be picked, and is refused if submitted anyway.
- saved-cards.remove: the customer can remove a saved card, from the checkout page or the Saved cards page.

## How a user reaches it

- Checkout page, new-card form: a "Save this card for later" checkbox, sent as `save_card` with the `POST /checkout` form.
- Checkout page, "Saved cards" list: each usable card has a "Pay ... with this card" button, a form `POST /checkout` with `saved_card_id`; every card has a "Remove" button, a form `POST /cards/remove` with `saved_card_id` and `back=/checkout`.
- Header "Saved cards" link to `GET /cards`, which lists the cards with a "Remove" button each.

## Request flow

The payments service keeps the full card. `POST /checkout` with `save_card` asks payments to charge and, only when the charge succeeds, save the card; payments returns a card ID, and the shop stores that ID with the last four digits and expiry in `saved_cards`. Paying with a saved card sends payments only the card ID. The shop refuses an expired saved card before storing an order. Removing a card asks payments to delete it, then deletes the shop's row.

## Verification plan

Source: [REQUIREMENTS.md](../../../../REQUIREMENTS.md) SC-1 to SC-4 at 7537b6c, and the developer's answers on 2026-10-25: a card is usable through the last day of its expiry month and expired from the first day after; an expired card stays visible at checkout, labelled Expired, not selectable, and still removable; a declined card is not saved, only a card whose charge succeeded.

The check drives a real Chromium browser through Playwright and records the run. Each payment starts from a cart holding one product, filled through the shop page's "Add to cart" button. Expiry months come from today's UTC date. Page claims are read from the browser's screen; stored claims are read from the shop and payments databases directly, without app code.

- saved-cards.save: with "Save this card" ticked, a declined card leaves no new saved card in the shop or the payments service; unticked, a successful payment leaves none; ticked, a successful payment leaves exactly one, stored with the typed card's last four and expiry, and the payments service holds a card with that ID and last four; no column anywhere in the shop database contains any typed card's full number; the checkout page shows each saved card with its last four and expiry. Reads stored state and the screen.
- saved-cards.pay: pay with a saved card through its own Pay button; the one new order is paid, and the payments service's charge for it succeeded, names that saved card's payments ID and last four, and is for the order's total, which equals the total the checkout page showed. Reads the screen and stored state in both databases.
- saved-cards.expired: a saved card expiring this month shows a Pay button and no Expired label; one that expired last month shows the Expired label and no Pay button; posting that card's ID to `POST /checkout`, as a tab opened before it expired would, while the cart holds a product stores no order, makes no charge, and answers with an alert saying the card has expired. Reads the screen, the response, and stored state.
- saved-cards.remove: Remove on the checkout page, and Remove on the Saved cards page, each return to that page with the card no longer shown, and take it out of the shop's saved cards and out of the payments service's cards. Reads the screen and stored state in both databases.

## How to prove it

- saved-cards.save: `python3 .agents/skills/verify-storefront/scripts/checks/saved_cards.py`. Reads the stored saved cards, the payments service's cards, every shop column, and the checkout page on screen.
- saved-cards.pay: `python3 .agents/skills/verify-storefront/scripts/checks/saved_cards.py`. Reads the checkout total on screen, the stored order, and the payments service's charge record.
- saved-cards.expired: `python3 .agents/skills/verify-storefront/scripts/checks/saved_cards.py`. Reads the saved-card rows on screen, the response to the stale form, and the stored orders and charges.
- saved-cards.remove: `python3 .agents/skills/verify-storefront/scripts/checks/saved_cards.py`. Reads both pages on screen, the stored saved cards, and the payments service's cards.

## Gotchas

- Needs Playwright for Python and its Chromium in the system `python3`, not the project's uv environment.
- The expired card is saved by typing a past expiry at checkout, which works only because the stand-in payments service charges a typed card whatever its expiry.
- The check stops when a saved card ending 4444 or 1111 already exists, such as one left by a failed run; remove it on the Saved cards page.
