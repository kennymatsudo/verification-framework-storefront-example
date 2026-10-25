# Northwind Goods: what the shop must do

Expected behavior lives here, not in the code. Each item has an ID so checks and reviews can name it. One customer is signed in at all times for this demo.

## Catalog

- **CA-1** The shop page lists every product with its name and price.

## Cart

- **CT-1** Adding a product puts one of it in the cart. Adding the same product again raises its quantity by one.
- **CT-2** Removing a product takes every unit of it out of the cart.
- **CT-3** The cart page's total equals the sum of its lines, each line being the product's price times its quantity.
- **CT-4** The cart badge in the header shows the number of units in the cart.

## Checkout

- **CO-1** Placing an order stores the lines and the total exactly as the customer saw them on the checkout page.
- **CO-2** When the card is charged successfully, the order is marked paid and records the payment's ID, and the amount charged equals the order's total.
- **CO-3** When the card is declined, the order is not marked paid, the customer is told on the checkout page, and the cart is left as it was.
- **CO-4** After a paid order, the cart is empty.
- **CO-5** An empty cart cannot be checked out.

## Orders

- **OR-1** The orders page lists the customer's orders, newest first, each with its status and total.
- **OR-2** An order's page shows its lines, its total, and its status.
- **OR-3** A paid order's page shows an estimated delivery date, five days after the order was placed. An order that is not paid shows none.

## Saved cards

Not built yet. Expected behavior once it is:

- **SC-1** At checkout the customer can choose to save the card for later. A saved card is shown by its last four digits and expiry; the full number is never stored by the shop.
- **SC-2** On a later checkout the customer can pay with a saved card instead of typing one, and the order is charged to that card.
- **SC-3** A saved card that has expired cannot be used to pay.
- **SC-4** The customer can remove a saved card.
