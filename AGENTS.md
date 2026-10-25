# Working in this repo

Northwind Goods is a small storefront: a FastAPI shop (`shop/`) and a separate payments service (`payments/`), each with its own SQLite database under `data/`.

- Start both with `scripts/dev.sh start`, stop with `scripts/dev.sh stop`, and see what's running with `scripts/dev.sh status`. The shop is on port 8800 and payments on 8801; each answers `/health` with the commit it runs.
- Expected behavior comes from `REQUIREMENTS.md`, never from the code. When a requirement leaves something open, ask before building.
- Unit tests: `uv run pytest`. They mock the repository and the payments client, so they prove the shop's logic and nothing about the running stack.
- Before reporting a change done, verify it on the running app with the verification harness (the `verify-storefront` skill once it exists). A unit test pass is not done.
