"""The shop's view of the payments service: charge a typed or saved card, and forget a saved one."""

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
    card_id: str | None = None  # set when the charge was to a saved card, or saved the card it charged


class PaymentsClient:
    def __init__(self, base_url: str = DEFAULT_URL):
        self.base_url = base_url

    def charge(self, amount_cents: int, card_number: str, expiry: str, name: str, save_card: bool = False) -> Charge:
        """Charge a typed card. With save_card, a successful charge also saves the card and returns its card_id."""
        return self._charge(
            {"amount_cents": amount_cents, "card_number": card_number, "expiry": expiry, "name": name,
             "save_card": save_card}
        )

    def charge_saved(self, amount_cents: int, card_id: str) -> Charge:
        return self._charge({"amount_cents": amount_cents, "card_id": card_id})

    def forget_card(self, card_id: str) -> None:
        try:
            httpx.delete(f"{self.base_url}/cards/{card_id}", timeout=5).raise_for_status()
        except httpx.HTTPError as error:
            raise PaymentsUnavailable(str(error)) from error

    def _charge(self, payload: dict) -> Charge:
        try:
            response = httpx.post(f"{self.base_url}/charges", json=payload, timeout=5)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise PaymentsUnavailable(str(error)) from error
        body = response.json()
        return Charge(id=body["id"], status=body["status"], amount_cents=body["amount_cents"], card_id=body["card_id"])
