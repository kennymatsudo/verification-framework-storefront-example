from shop.db import DEMO_CUSTOMER


def test_adding_an_item_puts_it_in_the_cart(client, repository):
    client.post("/cart/add", data={"product_id": 1})
    assert [(line["id"], line["quantity"]) for line in repository.cart(DEMO_CUSTOMER)] == [(1, 1)]


def test_adding_the_same_item_again_raises_its_quantity(client, repository):
    client.post("/cart/add", data={"product_id": 2})
    client.post("/cart/add", data={"product_id": 2})
    assert repository.cart(DEMO_CUSTOMER)[0]["quantity"] == 2


def test_removing_an_item_takes_it_out(client, repository):
    client.post("/cart/add", data={"product_id": 1})
    client.post("/cart/remove", data={"product_id": 1})
    assert repository.cart(DEMO_CUSTOMER) == []


def test_cart_page_shows_the_sum_of_the_lines(client):
    client.post("/cart/add", data={"product_id": 1})  # 18.00
    client.post("/cart/add", data={"product_id": 2})  # 42.00
    page = client.get("/cart").text
    assert "$60.00" in page
