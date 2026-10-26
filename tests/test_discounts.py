from tests.test_checkout import CARD, fill_cart


def test_a_valid_code_reduces_the_stored_total(client, repository):
    fill_cart(client)  # 107.00
    client.post("/checkout", data={**CARD, "code": "WELCOME10"})
    order = repository.order(1)
    assert order["discount_code"] == "WELCOME10"
    assert order["discount_cents"] == 1070
    assert order["total_cents"] == 9630


def test_the_checkout_page_shows_the_discount(client):
    fill_cart(client)
    page = client.get("/checkout?code=WELCOME10").text
    assert "$107.00" in page and "$10.70" in page and "$96.30" in page


def test_a_discounted_order_is_still_charged(client, payments):
    fill_cart(client)
    client.post("/checkout", data={**CARD, "code": "FRIENDS20"})
    assert len(payments.charges) == 1


def test_an_unknown_code_is_rejected_without_a_discount(client, repository):
    fill_cart(client)
    page = client.get("/checkout?code=NOPE").text
    assert "isn't valid" in page
    client.post("/checkout", data={**CARD, "code": "NOPE"})
    assert repository.order(1)["total_cents"] == 10700
    assert repository.order(1)["discount_code"] is None
