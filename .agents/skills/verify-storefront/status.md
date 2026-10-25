# Verification status

## Latest results

Written by `vf.py status` from the evidence on this machine; every accepted run refreshes it, and `vf.py not-verified` records a check that could not run. Edits here are overwritten; notes belong in notes.md.

- cart.add: Verified. cart, reads state and served HTML, storefront e4df978. Break-tested 2026-10-25: a second add leaves the quantity at 1 (ON CONFLICT DO NOTHING). Evidence: evidence/cart/2026-10-25T22-25-02Z.json
- cart.remove: Verified. cart, reads state and served HTML, storefront e4df978. Break-tested 2026-10-25: removing takes off one unit at a time instead of all. Evidence: evidence/cart/2026-10-25T22-25-02Z.json
- cart.total: Verified. cart, reads state and served HTML, storefront e4df978. Break-tested 2026-10-25: the cart total adds prices and ignores quantities. Evidence: evidence/cart/2026-10-25T22-25-02Z.json
- cart.badge: Verified. cart, reads state and served HTML, storefront e4df978. Break-tested 2026-10-25: the badge counts lines instead of units. Evidence: evidence/cart/2026-10-25T22-25-02Z.json
- checkout.order-lines: Verified. checkout, reads what the user sees and stored state, storefront f1dd5de. Break-tested 2026-10-25: order lines are stored with quantity 1. Evidence: evidence/checkout/2026-10-25T23-03-37Z.json
- checkout.pay: Verified. checkout, reads what the user sees and stored state, storefront f1dd5de. Break-tested 2026-10-25: the paid order does not record the charge ID. Evidence: evidence/checkout/2026-10-25T23-03-37Z.json
- checkout.decline: Verified. checkout, reads what the user sees and stored state, storefront f1dd5de. Break-tested 2026-10-25: a declined card empties the cart. Evidence: evidence/checkout/2026-10-25T23-03-37Z.json
- checkout.clears-cart: Verified. checkout, reads what the user sees and stored state, storefront f1dd5de. Break-tested 2026-10-25: the cart is not emptied after paying. Evidence: evidence/checkout/2026-10-25T23-03-37Z.json
- checkout.empty-cart: Verified. checkout, reads what the user sees and stored state, storefront f1dd5de. Break-tested 2026-10-25: the empty-cart guard on POST /checkout is removed. Evidence: evidence/checkout/2026-10-25T23-03-37Z.json
- discount.applied: Failed. Step 'card is charged the reduced total': order 1 paid total 7020, reduced total 7020; charge ch_d70cd318ea84 succeeded for 7800. storefront f1dd5de. Evidence: evidence/discount/2026-10-25T23-03-28Z.json. Replay: evidence/discount/2026-10-25T23-03-28Z/replay.html
- discount.charged: Failed. Step 'card is charged the reduced total': order 1 paid total 7020, reduced total 7020; charge ch_d70cd318ea84 succeeded for 7800. storefront f1dd5de. Evidence: evidence/discount/2026-10-25T23-03-28Z.json. Replay: evidence/discount/2026-10-25T23-03-28Z/replay.html
