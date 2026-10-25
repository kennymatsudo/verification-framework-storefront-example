import sqlite3
from datetime import date

import pytest
from fastapi.testclient import TestClient

from shop import db
from shop.main import create_app
from shop.payments_client import Charge


class FakePayments:
    """Stands in for the payments service. Records every charge it was asked for."""

    def __init__(self, status="succeeded"):
        self.status = status
        self.charges = []
        self.saved_card_charges = []
        self.forgotten_cards = []

    def charge(self, amount_cents, card_number, expiry, name, save_card=False):
        self.charges.append(amount_cents)
        card_id = f"card_fake{len(self.charges)}" if save_card and self.status == "succeeded" else None
        return Charge(id=f"ch_fake{len(self.charges)}", status=self.status, amount_cents=amount_cents, card_id=card_id)

    def charge_saved(self, amount_cents, card_id):
        self.charges.append(amount_cents)
        self.saved_card_charges.append(card_id)
        return Charge(id=f"ch_fake{len(self.charges)}", status=self.status, amount_cents=amount_cents, card_id=card_id)

    def forget_card(self, card_id):
        self.forgotten_cards.append(card_id)


TODAY = date(2026, 10, 25)


@pytest.fixture
def repository():
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row
    db.seed(connection)
    return db.Repository(connection)


@pytest.fixture
def payments():
    return FakePayments()


@pytest.fixture
def client(repository, payments):
    return TestClient(create_app(repository=repository, payments=payments, today=lambda: TODAY), follow_redirects=False)
