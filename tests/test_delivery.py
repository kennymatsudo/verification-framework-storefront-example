from tests.test_checkout import CARD, fill_cart


def test_a_paid_order_shows_delivery_five_days_after_placing(client, repository):
    fill_cart(client)
    client.post("/checkout", data=CARD)
    repository.connection.execute("UPDATE orders SET placed_at = '2026-03-02T10:00:00+00:00' WHERE id = 1")
    page = client.get("/orders/1").text
    assert "Estimated delivery" in page
    assert "Saturday, Mar 7" in page


def test_a_declined_order_shows_no_delivery_estimate(client, repository, payments):
    payments.status = "declined"
    fill_cart(client)
    client.post("/checkout", data=CARD)
    assert "Estimated delivery" not in client.get("/orders/1").text
