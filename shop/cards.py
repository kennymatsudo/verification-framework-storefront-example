"""Card expiry rules: a card is usable through the last day of its expiry month and expired from the day after."""

import re
from datetime import date

EXPIRY = re.compile(r"^\s*(\d{1,2})\s*/\s*(\d{2}|\d{4})\s*$")


def parse_expiry(expiry: str) -> tuple[int, int] | None:
    """Return (year, month) for an expiry written MM/YY or MM/YYYY, or None when it isn't one."""
    match = EXPIRY.match(expiry)
    if not match:
        return None
    month, year = int(match[1]), int(match[2])
    if not 1 <= month <= 12:
        return None
    return (2000 + year if year < 100 else year), month


def card_expired(expiry: str, today: date) -> bool:
    year, month = parse_expiry(expiry)
    first_day_after = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return today >= first_day_after
