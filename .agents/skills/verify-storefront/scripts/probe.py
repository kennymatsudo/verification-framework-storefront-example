#!/usr/bin/env python3
"""Answer a question about the running storefront's stored state, read straight from its databases.

  probe.py cart                 the signed-in customer's cart: each product and quantity, and the unit count
  probe.py order <order-id>     an order: status, total, charge ID, and its lines
  probe.py charge <charge-id>   the payments service's record of a charge: amount, status, card's last four
  probe.py saved-cards          the customer's saved cards as the shop stores them, and whether payments holds each

Read-only: it opens the shop and payments SQLite files in read-only mode, finding each through the service's
GET /health, so the services must be running. It never imports the shop's code.

Prints one JSON object. Add --full for every stored column. Values under keys that look like a secret,
token, or password are redacted.
Exit 0: answered. Exit 1: not found, with {"not_found": ..., "hint": ...}.
Exit 2: could not answer, with `STOPPED: <reason>` on stderr, such as a bad argument or a service that
doesn't answer.
"""

import argparse
import json
import re
import sys

PROBE = "python3 .agents/skills/verify-storefront/scripts/probe.py"
SECRET = re.compile(r"secret|token|password", re.I)


class Stopped(Exception):
    pass


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Stopped(message)


def redact(value):
    if isinstance(value, dict):
        return {k: "[redacted]" if SECRET.search(k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def answer(reads, question, ident, full):
    """(result, None) when answered, (None, not_found) when the record isn't stored."""
    if question == "cart":
        lines = reads.cart()
        return {"lines": lines, "units": sum(line["quantity"] for line in lines),
                "next": [f"{PROBE} order <order-id>"]}, None
    if question == "order":
        if not re.fullmatch(r"[0-9]+", ident or ""):
            raise Stopped("order needs a numeric order ID")
        found = reads.order(int(ident))
        if found is None:
            return None, {"not_found": f"order {ident}", "hint": "order IDs are the numbers in /orders/<id> on the Orders page"}
        if not full:
            found = {k: found[k] for k in ("id", "status", "total_cents", "charge_id", "placed_at", "lines")}
        found["next"] = [f"{PROBE} charge {found['charge_id']}"] if found.get("charge_id") else []
        return found, None
    if question == "saved-cards":
        cards = []
        for card in reads.saved_cards():
            held = reads.payments_card(card["payments_card_id"])
            shown = card if full else {k: card[k] for k in ("id", "payments_card_id", "last4", "expiry")}
            cards.append({**shown, "payments_holds_card": held is not None})
        return {"saved_cards": cards}, None
    if not ident:
        raise Stopped("charge needs a charge ID")
    found = reads.charge(ident)
    if found is None:
        return None, {"not_found": f"charge {ident}", "hint": f"charge IDs look like ch_ and 12 hex digits; {PROBE} order <id> shows an order's"}
    if not full:
        found = {k: found[k] for k in ("id", "status", "amount_cents", "card_last4", "card_id")}
    return found, None


def main():
    parser = Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", choices=["cart", "order", "charge", "saved-cards"])
    parser.add_argument("id", nargs="?", help="the order ID or charge ID")
    parser.add_argument("--full", action="store_true", help="print every stored column")
    try:
        args = parser.parse_args()
        import reads  # after parsing, so --help works without reading the environment or the services

        result, missing = answer(reads, args.question, args.id, args.full)
    except Stopped as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001 - any failure to read is "could not answer", never "not found"
        print(f"STOPPED: could not read the storefront's databases: {error!r}", file=sys.stderr)
        return 2
    if missing:
        print(json.dumps(missing))
        return 1
    print(json.dumps(redact(result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
