# Verification status

## Latest results

Written by `vf.py status` from the evidence on this machine; every accepted run refreshes it, and `vf.py not-verified` records a check that could not run. Edits here are overwritten; notes belong in notes.md.

- cart.add: Verified. cart, reads state and served HTML, storefront 9883b1a. Break-tested 2026-10-25: a second add leaves the quantity at 1 (ON CONFLICT DO NOTHING). Evidence: evidence/cart/2026-10-25T23-23-26Z.json
- cart.remove: Verified. cart, reads state and served HTML, storefront 9883b1a. Break-tested 2026-10-25: removing takes off one unit at a time instead of all. Evidence: evidence/cart/2026-10-25T23-23-26Z.json
- cart.total: Verified. cart, reads state and served HTML, storefront 9883b1a. Break-tested 2026-10-25: the cart total adds prices and ignores quantities. Evidence: evidence/cart/2026-10-25T23-23-26Z.json
- cart.badge: Verified. cart, reads state and served HTML, storefront 9883b1a. Break-tested 2026-10-25: the badge counts lines instead of units. Evidence: evidence/cart/2026-10-25T23-23-26Z.json
- checkout.order-lines: Verified. checkout, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: order lines are stored with quantity 1. Evidence: evidence/checkout/2026-10-25T23-23-27Z.json
- checkout.pay: Verified. checkout, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: the paid order does not record the charge ID. Evidence: evidence/checkout/2026-10-25T23-23-27Z.json
- checkout.decline: Verified. checkout, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: a declined card empties the cart. Evidence: evidence/checkout/2026-10-25T23-23-27Z.json
- checkout.clears-cart: Verified. checkout, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: the cart is not emptied after paying. Evidence: evidence/checkout/2026-10-25T23-23-27Z.json
- checkout.empty-cart: Verified. checkout, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: the empty-cart guard on POST /checkout is removed. Evidence: evidence/checkout/2026-10-25T23-23-27Z.json
- saved-cards.save: Verified. saved-cards, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: the shop stores the full card number in place of the last four. Evidence: evidence/saved-cards/2026-10-25T23-23-24Z.json
- saved-cards.pay: Verified. saved-cards, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: paying with a saved card charges the most recently saved card, not the chosen one. Evidence: evidence/saved-cards/2026-10-25T23-23-24Z.json
- saved-cards.expired: Verified. saved-cards, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: POST /checkout no longer refuses an expired saved card. Evidence: evidence/saved-cards/2026-10-25T23-23-24Z.json
- saved-cards.remove: Verified. saved-cards, reads what the user sees and stored state, storefront 9883b1a. Break-tested 2026-10-25: removing a card deletes the shop's row but leaves the card at the payments service. Evidence: evidence/saved-cards/2026-10-25T23-23-24Z.json
