# Northwind Goods

A small storefront used to demo the [verification framework](https://github.com/kennymatsudo/verification-framework): a coding agent that says "done" with a verified result behind it.

Two services, each with its own SQLite database: the shop (catalog, cart, checkout, orders) and a stand-in payment processor.

```sh
uv sync
scripts/dev.sh start      # shop on http://127.0.0.1:8800, payments on :8801
uv run pytest             # unit tests
scripts/dev.sh stop
```

A card ending in `0002` is always declined; any other number succeeds.

What the shop must do is in [REQUIREMENTS.md](REQUIREMENTS.md). The demo's plan is in [docs/plan.md](docs/plan.md).
