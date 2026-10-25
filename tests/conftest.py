import sqlite3

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

    def charge(self, amount_cents, card_number, expiry, name):
        self.charges.append(amount_cents)
        return Charge(id=f"ch_fake{len(self.charges)}", status=self.status, amount_cents=amount_cents)


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
    return TestClient(create_app(repository=repository, payments=payments), follow_redirects=False)
