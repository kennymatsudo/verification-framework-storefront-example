from datetime import date

from shop.cards import card_expired
from shop.db import DEMO_CUSTOMER

CARD = {"card_number": "4242 4242 4242 4242", "expiry": "12/30", "name_on_card": "Mira Okafor"}


def fill_cart(client):
    client.post("/cart/add", data={"product_id": 1})  # 18.00


def save_card(client, expiry="12/30"):
    fill_cart(client)
    client.post("/checkout", data={**CARD, "expiry": expiry, "save_card": "true"})


def test_a_card_is_usable_through_the_last_day_of_its_expiry_month():
    assert not card_expired("10/26", date(2026, 10, 31))
    assert card_expired("10/26", date(2026, 11, 1))
    assert card_expired("12/26", date(2027, 1, 1))
    assert not card_expired("12/26", date(2026, 12, 31))


def test_saving_a_card_keeps_only_its_last_four_and_expiry(client, repository):
    save_card(client)
    [card] = repository.saved_cards(DEMO_CUSTOMER)
    assert (card["payments_card_id"], card["last4"], card["expiry"]) == ("card_fake1", "4242", "12/30")
    assert "4242 4242" not in str(dict(card)) and "42424242" not in str(dict(card))


def test_a_card_is_not_saved_unless_asked(client, repository):
    fill_cart(client)
    client.post("/checkout", data=CARD)
    assert repository.saved_cards(DEMO_CUSTOMER) == []


def test_a_declined_card_is_not_saved(client, repository, payments):
    payments.status = "declined"
    save_card(client)
    assert repository.saved_cards(DEMO_CUSTOMER) == []


def test_paying_with_a_saved_card_charges_that_card(client, repository, payments):
    save_card(client)
    [card] = repository.saved_cards(DEMO_CUSTOMER)
    fill_cart(client)
    response = client.post("/checkout", data={"saved_card_id": card["id"]})
    assert response.status_code == 303
    assert payments.saved_card_charges == ["card_fake1"]
    assert repository.order(2)["status"] == "paid"


def test_an_expired_saved_card_cannot_pay(client, repository, payments):
    save_card(client, expiry="09/26")
    [card] = repository.saved_cards(DEMO_CUSTOMER)
    fill_cart(client)
    page = client.get("/checkout").text
    assert "Expired" in page and "with this card" not in page
    response = client.post("/checkout", data={"saved_card_id": card["id"]})
    assert response.status_code == 200
    assert "expired" in response.text
    assert payments.saved_card_charges == []
    assert len(repository.orders(DEMO_CUSTOMER)) == 1


def test_removing_a_saved_card_forgets_it(client, repository, payments):
    save_card(client)
    [card] = repository.saved_cards(DEMO_CUSTOMER)
    response = client.post("/cards/remove", data={"saved_card_id": card["id"], "back": "/checkout"})
    assert response.headers["location"] == "/checkout"
    assert repository.saved_cards(DEMO_CUSTOMER) == []
    assert payments.forgotten_cards == ["card_fake1"]
