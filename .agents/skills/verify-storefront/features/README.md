# Storefront feature map

Open the file for the feature you changed. Follow `../rules.md` for every proof.
Read [the latest results](../status.md) and [the notes](../notes.md) for known failures, misleading passes, and untested cases.
See each check's latest run, and watch recorded ones, in [the recordings page](../recordings.html).

## Baseline

- Start: `python3 .agents/skills/verify-storefront/scripts/framework/vf.py start --until "python3 .agents/skills/verify-storefront/scripts/doctor.py" -- .agents/skills/verify-storefront/scripts/serve.sh`. Ready when `python3 .agents/skills/verify-storefront/scripts/doctor.py` exits 0. Stop: `python3 .agents/skills/verify-storefront/scripts/framework/vf.py stop`.
- Data: the shop seeds six products and one customer, Mira Okafor, into an empty `data/shop.sqlite` at startup (shop/db.py). There is no login; that customer is always signed in. A card number ending in `0002` is always declined; any other succeeds (README.md). Both databases persist across runs in the checkout's `data/`.
- Isolation: one instance per checkout at the default ports 8800 and 8801; a scratch worktree gets its own `data/`. Never drive an instance you did not start: the readiness check fails when a port is held by a process the harness did not launch.

## Features

- [Cart](cart.md): add, remove, cart total, header badge.
- [Checkout](checkout.md): order matches the checkout page, paid order, declined card, cart emptied after paying, empty cart refused.
- [Saved cards](saved-cards.md): save a card at checkout, pay with a saved card, expired cards refused, remove a card.
