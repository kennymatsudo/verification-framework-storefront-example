from shop.db import DEMO_CUSTOMER

CARD = {"card_number": "4242 4242 4242 4242", "expiry": "12/30", "name_on_card": "Mira Okafor"}


def fill_cart(client):
    client.post("/cart/add", data={"product_id": 1})  # 18.00
    client.post("/cart/add", data={"product_id": 3})  # 89.00


def test_a_successful_charge_marks_the_order_paid(client, repository, payments):
    fill_cart(client)
    response = client.post("/checkout", data=CARD)
    assert response.status_code == 303
    order = repository.order(1)
    assert order["status"] == "paid"
    assert order["charge_id"] == "ch_fake1"


def test_the_charge_is_for_the_order_total(client, payments):
    fill_cart(client)
    client.post("/checkout", data=CARD)
    assert payments.charges == [10700]


def test_the_order_keeps_the_lines_the_customer_saw(client, repository):
    fill_cart(client)
    client.post("/checkout", data=CARD)
    lines = repository.order_lines(1)
    assert [(line["name"], line["quantity"], line["unit_price_cents"]) for line in lines] == [
        ("Field Notebook", 1, 1800),
        ("Desk Lamp", 1, 8900),
    ]
    assert repository.order(1)["total_cents"] == 10700


def test_the_cart_is_empty_after_paying(client, repository):
    fill_cart(client)
    client.post("/checkout", data=CARD)
    assert repository.cart(DEMO_CUSTOMER) == []


def test_a_declined_card_leaves_the_order_unpaid_and_the_cart_full(client, repository, payments):
    payments.status = "declined"
    fill_cart(client)
    response = client.post("/checkout", data=CARD)
    assert response.status_code == 200
    assert "declined" in response.text
    assert repository.order(1)["status"] == "declined"
    assert len(repository.cart(DEMO_CUSTOMER)) == 2


def test_an_empty_cart_cannot_check_out(client, repository):
    response = client.post("/checkout", data=CARD)
    assert response.status_code == 303
    assert response.headers["location"] == "/cart"
    assert repository.orders(DEMO_CUSTOMER) == []
