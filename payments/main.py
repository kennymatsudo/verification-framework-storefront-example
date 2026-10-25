"""A stand-in payment processor: charges a card and keeps its own ledger of charges.

It behaves like a real processor from the shop's point of view: the shop never sees the full card number again,
only the last four digits, and a card ending in 0002 is always declined so declines can be exercised. A card the
customer asks to save is kept here, and the shop charges it later by the card ID it was given.
"""

import os
import secrets
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = Path(os.environ.get("PAYMENTS_DB", "data/payments.sqlite"))
DECLINED_SUFFIX = "0002"

SCHEMA = """
CREATE TABLE IF NOT EXISTS charges (
    id TEXT PRIMARY KEY,
    amount_cents INTEGER NOT NULL,
    card_last4 TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cards (
    id TEXT PRIMARY KEY,
    card_number TEXT NOT NULL,
    expiry TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class ChargeRequest(BaseModel):
    """Either a typed card (card_number, expiry, name) or a saved one (card_id)."""

    amount_cents: int
    card_number: str | None = None
    expiry: str | None = None
    name: str | None = None
    card_id: str | None = None
    save_card: bool = False


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    # Databases created before saved cards existed lack this column, and CREATE TABLE IF NOT EXISTS won't add it.
    if "card_id" not in {row["name"] for row in connection.execute("PRAGMA table_info(charges)")}:
        connection.execute("ALTER TABLE charges ADD COLUMN card_id TEXT")
    return connection


def current_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


app = FastAPI(title="Payments")
app.state.connection = connect()
app.state.commit = current_commit()


@app.get("/health")
def health():
    return {"status": "ok", "commit": app.state.commit, "database": str(DB_PATH)}


@app.post("/charges")
def create_charge(request: ChargeRequest):
    connection = app.state.connection
    if request.card_id:
        card = connection.execute("SELECT * FROM cards WHERE id = ?", (request.card_id,)).fetchone()
        if card is None:
            raise HTTPException(status_code=404, detail="no such card")
        card_number, expiry, name = card["card_number"], card["expiry"], card["name"]
    elif request.card_number and request.expiry and request.name:
        card_number, expiry, name = request.card_number, request.expiry, request.name
    else:
        raise HTTPException(status_code=422, detail="give a card_id, or a card_number, expiry, and name")
    digits = card_number.replace(" ", "")
    status = "declined" if digits.endswith(DECLINED_SUFFIX) else "succeeded"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    card_id = request.card_id
    if request.save_card and not card_id and status == "succeeded":
        card_id = "card_" + secrets.token_hex(6)
        connection.execute(
            "INSERT INTO cards (id, card_number, expiry, name, created_at) VALUES (?, ?, ?, ?, ?)",
            (card_id, digits, expiry, name, now),
        )
    charge_id = "ch_" + secrets.token_hex(6)
    connection.execute(
        "INSERT INTO charges (id, amount_cents, card_last4, status, created_at, card_id) VALUES (?, ?, ?, ?, ?, ?)",
        (charge_id, request.amount_cents, digits[-4:], status, now, card_id),
    )
    connection.commit()
    return {
        "id": charge_id, "status": status, "amount_cents": request.amount_cents,
        "card_last4": digits[-4:], "card_id": card_id,
    }


@app.get("/charges/{charge_id}")
def get_charge(charge_id: str):
    row = app.state.connection.execute("SELECT * FROM charges WHERE id = ?", (charge_id,)).fetchone()
    return dict(row) if row else {"error": "no such charge"}


@app.delete("/cards/{card_id}")
def forget_card(card_id: str):
    app.state.connection.execute("DELETE FROM cards WHERE id = ?", (card_id,))
    app.state.connection.commit()
    return {"id": card_id, "deleted": True}
