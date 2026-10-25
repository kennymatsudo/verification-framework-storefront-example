# Add discount codes at checkout

Closes the discount-codes ticket.

Marketing wants to run two launch promotions, so checkout now takes a discount code. `WELCOME10` and `FRIENDS20` take 10% and 20% off the subtotal.

## What changed

- A discount code field on the checkout page with an Apply button. The page reloads showing the subtotal, the discount line, and the reduced total.
- The order records the code and the discount amount, and its page shows the discount line.
- An unknown code shows "That code isn't valid" and applies nothing.
- Codes live in a dict in `shop/db.py` for now; a table can come when marketing needs to add codes without a deploy.

## Test plan

- [x] Valid code reduces the stored order total (unit test)
- [x] Checkout page shows subtotal, discount, and reduced total (unit test)
- [x] The discounted order is charged (unit test)
- [x] Unknown code is rejected with no discount (unit test)
- [x] Tried WELCOME10 locally end to end: order #7 shows the discount and the total matched the Pay button
