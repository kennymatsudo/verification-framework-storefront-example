# Verification notes

## Setup: verify-storefront

- Target: Northwind Goods storefront, the FastAPI shop (`shop/`, port 8800) and the payments service (`payments/`, port 8801) in this repo, each with its own SQLite database under `data/`. Requested setup: a verification harness for local development.
- Findings: `scripts/dev.sh start` runs payments then the shop with `uv run uvicorn`, backgrounded with `nohup`, on 127.0.0.1 ports from `PAYMENTS_PORT` (8801) and `STOREFRONT_PORT` (8800), writing PID and log files under `data/` (scripts/dev.sh:7-9,16-17,35). It waits for each `/health` and then exits, so `serve.sh` keeps it in the foreground for the launcher. Neither uvicorn runs with `--reload` (scripts/dev.sh:16). Each `/health` returns `status`, `commit`, and `database`; the commit is `git rev-parse HEAD` read once at startup, without dirty state (shop/version.py:7-13, shop/main.py:30,42-44, payments/main.py:46-62), so the launch record's code state and dirty fingerprint are the evidence of loaded code and the `/health` commit is a cross-check. Databases default to `data/shop.sqlite` and `data/payments.sqlite` (shop/db.py:8, payments/main.py:17). The shop seeds six products and one always-signed-in customer (shop/db.py:47-77, REQUIREMENTS.md:3). There is no login, secret, or external service; payments is a local stand-in, and a card ending `0002` is declined (README.md:14, payments/main.py:68). There is no Git remote, so `main` is the only branch to compare with. Requirements live in REQUIREMENTS.md (AGENTS.md:6).
- Looked in: AGENTS.md, README.md, REQUIREMENTS.md, docs/plan.md, pyproject.toml, scripts/dev.sh, shop/version.py, shop/main.py, shop/db.py, shop/payments_client.py, payments/main.py, Git branches and remotes. No Makefile, compose file, or CI config exists.
- Blocker: none
- Next action: none
- Doctor proof: evidence/doctor/2026-10-25T22-08-04Z.txt, 2026-10-25, storefront bcd33ce with uncommitted changes c905818e (an unrelated `.gitignore` edit and untracked `demo/`), plus a clean scratch worktree at bcd33ce. Ready (exit 0) on the real start; not ready (exit 1) before any start, on a wrong port, after an untracked file changed the checkout, after Stop, after a crash left the launch record behind (the next Start replaced it), and when the shop's port was held by a lookalike process the harness didn't launch. Start refused a lookalike already holding port 8800: `scripts/dev.sh` reported "shop ready" against it, and `serve.sh` exited when the real shop failed to bind. Run scratch code was exercised from a scratch worktree and back, each time reaching ready with the services running from that checkout and its own `data/`.

## Known failing checks

None yet.

## Where a pass can mislead

None yet.

## Untested cases

None yet.
