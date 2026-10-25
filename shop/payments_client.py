"""The shop's view of the payments service: one call to charge a card."""

import os
from dataclasses import dataclass

import httpx

DEFAULT_URL = os.environ.get("PAYMENTS_URL", "http://127.0.0.1:8801")


class PaymentsUnavailable(Exception):
    pass


@dataclass
class Charge:
    id: str
    status: str  # "succeeded" or "declined"
    amount_cents: int


class PaymentsClient:
    def __init__(self, base_url: str = DEFAULT_URL):
        self.base_url = base_url

    def charge(self, amount_cents: int, card_number: str, expiry: str, name: str) -> Charge:
        try:
            response = httpx.post(
                f"{self.base_url}/charges",
                json={"amount_cents": amount_cents, "card_number": card_number, "expiry": expiry, "name": name},
                timeout=5,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise PaymentsUnavailable(str(error)) from error
        body = response.json()
        return Charge(id=body["id"], status=body["status"], amount_cents=body["amount_cents"])
