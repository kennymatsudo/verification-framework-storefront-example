"""A stand-in payment processor: charges a card and keeps its own ledger of charges.

It behaves like a real processor from the shop's point of view: the shop never sees the full card number again,
only the last four digits, and a card ending in 0002 is always declined so declines can be exercised.
"""

import os
import secrets
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
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
"""


class ChargeRequest(BaseModel):
    amount_cents: int
    card_number: str
    expiry: str
    name: str


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
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
    digits = request.card_number.replace(" ", "")
    status = "declined" if digits.endswith(DECLINED_SUFFIX) else "succeeded"
    charge_id = "ch_" + secrets.token_hex(6)
    app.state.connection.execute(
        "INSERT INTO charges (id, amount_cents, card_last4, status, created_at) VALUES (?, ?, ?, ?, ?)",
        (charge_id, request.amount_cents, digits[-4:], status, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    app.state.connection.commit()
    return {"id": charge_id, "status": status, "amount_cents": request.amount_cents, "card_last4": digits[-4:]}


@app.get("/charges/{charge_id}")
def get_charge(charge_id: str):
    row = app.state.connection.execute("SELECT * FROM charges WHERE id = ?", (charge_id,)).fetchone()
    return dict(row) if row else {"error": "no such charge"}
