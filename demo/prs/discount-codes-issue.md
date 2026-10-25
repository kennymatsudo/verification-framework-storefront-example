# Discount codes at checkout

Marketing is running two launch promotions and needs checkout to accept a code.

## Acceptance criteria

1. A valid code entered at checkout takes its percentage off the subtotal. The checkout page shows the subtotal, the discount, and the reduced total.
2. The stored order records the code, the discount amount, and the reduced total.
3. The card is charged the reduced total, not the subtotal.
4. An unknown code is rejected with a message, and no discount is applied.

Codes for launch: WELCOME10 (10%), FRIENDS20 (20%).
