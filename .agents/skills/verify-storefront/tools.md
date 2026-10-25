# Storefront developer tools

Use these commands for debugging, investigation, or verification. A read reports current state; it does not by itself prove a feature works.

## Is the storefront instance worth driving?

Use when: before driving the shop or payments service, or when a check stops because the app isn't ready. It checks readiness only; use a feature's check to prove behavior.

Run from the project root:

`python3 .agents/skills/verify-storefront/scripts/doctor.py`

- Inputs: none. Ports come from `STOREFRONT_PORT` and `PAYMENTS_PORT`, defaulting to 8800 and 8801, as in `scripts/dev.sh`.
- Environment: an instance started with the Start command in `settings.md`, which records its process group and code state in `evidence/launch/record.json`; `lsof` installed.
- Permissions: read-only. It sends `GET /health` to each service and reads process information; it starts and stops nothing.
- Result: exit 0 prints one line per service (process, launched group, port, commit, database path), an auth line, the code line (commit, branch, uncommitted-changes fingerprint, whether the commit is on the default branch), and last `verify-storefront: ready`. Ready means the launched process group is alive, the checkout's code still matches what was on disk at launch, and each port is held by a process in that group, answers `/health` ok with the launch commit, and runs from the launched checkout.
- Failure: exit 1 prints one `not ready:` reason per line, such as no instance started, a changed checkout (restart with Stop then Start), nothing on a port, or a port held by a process the harness did not launch. Exit 2 prints `STOPPED:` when it can't tell, such as `lsof` missing or an unreadable launch record.
- Limits: it does not prove any page or payment works, and a service that answers `/health` can still fail every request. The commit match relies on the services not reloading on edit, which holds because `scripts/dev.sh` starts uvicorn without `--reload`.

Help: `python3 .agents/skills/verify-storefront/scripts/doctor.py --help`.

## Start the storefront for verification

Use when: starting the app so checks can drive it. Use `scripts/dev.sh start` directly only for hand testing; the readiness check rejects an instance it didn't launch.

Run from the project root:

`python3 .agents/skills/verify-storefront/scripts/framework/vf.py start --until "python3 .agents/skills/verify-storefront/scripts/doctor.py" -- .agents/skills/verify-storefront/scripts/serve.sh`

- Inputs: optionally a checkout path after `serve.sh`, which defaults to this repo.
- Environment: `uv` and `curl` installed; ports 8800 and 8801 free.
- Permissions: local side effects only. It runs the checkout's `scripts/dev.sh start`, which creates and seeds `data/*.sqlite` when absent and writes PID and log files under `data/`. Nothing leaves this machine. `serve.sh` refuses to start when `data/*.pid` names a running service it didn't start.
- Result: prints the process ID, the recorded code, and `started` once the readiness check passes; exit 0.
- Failure: exit 1 with the last lines of `evidence/launch/output.log` when the app exits or doesn't become ready within 60 seconds, after stopping what it started. `scripts/dev.sh` reports a service ready when anything answers its port's `/health`, so a port conflict shows up as `serve: shop exited` rather than a bind error; see `data/shop.log`.
- Limits: one instance per checkout at the default ports.

Help: `.agents/skills/verify-storefront/scripts/serve.sh --help` and `python3 .agents/skills/verify-storefront/scripts/framework/vf.py start --help`.

## Stop the storefront the harness started

Use when: done driving the app, or before restarting it on new code.

Run from the project root:

`python3 .agents/skills/verify-storefront/scripts/framework/vf.py stop`

- Inputs: none.
- Environment: none.
- Permissions: stops only the process group the launch record names, then removes the record; it never touches an instance started another way.
- Result: `process <pid> stopped; record removed`, or `nothing to stop`; exit 0.
- Failure: exit 1 when the process survives SIGKILL.
- Limits: it leaves the databases and logs in `data/` in place.

Help: `python3 .agents/skills/verify-storefront/scripts/framework/vf.py stop --help`.

## Restart the storefront from another checkout

Use when: pointing the app at a scratch worktree for a planned break and back, or making an edit take effect, since neither service reloads on edit. `vf.py break` runs it for you.

Run from the project root:

`.agents/skills/verify-storefront/scripts/relaunch.sh storefront /path/to/checkout`

- Inputs: the repo name from `settings.md` (`storefront`) and the checkout to run.
- Environment: as for Start; the checkout needs `uv` to build its own environment on first run.
- Permissions: stops the harness's instance, then starts the given checkout's `scripts/dev.sh`, which uses that checkout's own `data/`.
- Result: as for Start, then the readiness check has passed against the given checkout.
- Failure: as for Start; exit 2 with usage when the arguments are missing.
- Limits: restarting does not undo data a check wrote.

Help: `.agents/skills/verify-storefront/scripts/relaunch.sh --help`.

## What is in the cart, an order, a charge, or the saved cards right now?

Use when: debugging the cart or checkout, or re-checking what a check judged. It reports stored state; it does not by itself prove a feature works.

Run from the project root:

`python3 .agents/skills/verify-storefront/scripts/probe.py cart`, `... probe.py order <order-id>`, `... probe.py charge <charge-id>`, or `... probe.py saved-cards`

- Inputs: `cart` and `saved-cards` take nothing; `order` takes the number from `/orders/<id>`; `charge` takes a payments ID such as `ch_1a2b3c4d5e6f`, which `order` shows. `--full` prints every stored column.
- Environment: the shop and payments services running, since it finds each database through the service's `GET /health`. A relative path there resolves against the checkout the launch record names while its process is alive, or this repo otherwise.
- Permissions: read-only. It opens the SQLite files each service's `/health` names (by default `data/shop.sqlite` and `data/payments.sqlite`; `STOREFRONT_DB` and `PAYMENTS_DB` change them) in read-only mode, in one read transaction per answer, and sends `GET /health`.
- Result: exit 0 with one JSON object: the cart's lines (product ID and quantity) and unit count; an order's status, total, charge ID, placement time, and lines; a charge's status, amount, card's last four digits, and the saved card it was charged to, if any; the saved cards' shop ID, payments card ID, last four, expiry, and whether the payments service still holds each card (its full number is never printed). `next` lists follow-up probe commands. Values under keys that look like a secret, token, or password are redacted.
- Failure: exit 1 with `{"not_found": ..., "hint": ...}` for an order or charge that isn't stored. Exit 2 with `STOPPED:` on stderr for a bad argument or when it can't read, such as a service that doesn't answer or a missing database file.
- Limits: it reads storage, not what a page shows; a correct cart row can still render wrongly. The cart is the one always-signed-in customer's. Where each database lives comes from the app's own `/health` response; the rows themselves are read directly.

Help: `python3 .agents/skills/verify-storefront/scripts/probe.py --help`.

## Watch or share a recorded check run

Use when: a check failed and you want to see it, or you want a clip of a run for a PR. The Checkout and Saved cards checks record their browser; they keep the video when the run fails or when `VERIFY_KEEP_RECORDING=1` is set for the run. A full-speed local run is over in seconds, so set `VERIFY_SLOW_MO_MS=400` too when the video is for people to watch. `recordings.html` in this harness lists every check's latest run, with a Watch button where a video was kept.

Run from the project root:

`python3 .agents/skills/verify-storefront/scripts/framework/vf.py replay <evidence file>` builds a run's replay page; `python3 .agents/skills/verify-storefront/scripts/framework/vf.py clip --steps 2-3 <evidence file>` cuts those steps into an MP4, and `--frames failed` writes stills around each failed step.

- Inputs: an evidence file such as `.agents/skills/verify-storefront/evidence/checkout/<time>.json`.
- Environment: replay pages need nothing extra. Clips and stills need `ffmpeg`; `vf.py clip --check` says what this machine can make.
- Permissions: local files only. Writes the replay page and `recordings.html`, or the clip and stills beside the evidence.
- Result: the path of the page, clip, or stills.
- Failure: exit nonzero with the reason, such as a run that kept no video.
- Limits: a video shows what happened; the check's steps decide the verdict.

Help: `python3 .agents/skills/verify-storefront/scripts/framework/vf.py replay --help` and `python3 .agents/skills/verify-storefront/scripts/framework/vf.py clip --help`.

## Prove the cart, checkout, or saved cards work

Use when: a change touches the cart, checkout, or saved cards. Each check proves the behaviors its feature file maps to it (`features/cart.md`, `features/checkout.md`, `features/saved-cards.md`).

Run from the project root:

`python3 .agents/skills/verify-storefront/scripts/framework/vf.py run -- python3 .agents/skills/verify-storefront/scripts/checks/cart.py`, or `checks/checkout.py` or `checks/saved_cards.py` in its place.

- Inputs: none. Set `VERIFY_KEEP_RECORDING=1` to keep a passing Checkout or Saved cards run's video, and `VERIFY_SLOW_MO_MS=<ms>`, such as 400, to pause before every browser step so the video can be followed; it is off by default and changes pacing only.
- Environment: an instance started with the Start command; the readiness check runs first. The Checkout and Saved cards checks need Playwright for Python and its Chromium in the system `python3`.
- Permissions: local side effects only. All empty the signed-in customer's cart; Cart leaves two products in it, and Checkout and Saved cards leave paid and declined orders and their charges in the local databases. Saved cards removes the saved cards it created and leaves earlier ones alone.
- Result: one PASS or FAIL line per step, and `vf.py run` writes the evidence under `evidence/cart/` or `evidence/checkout/` and refreshes `status.md`.
- Failure: exit 1 when a step failed, with what it found; exit 2 when the run stopped before a verdict, with the reason.
- Limits: Cart reads served HTML, not a browser render. None covers the payments service being down, nor a cart changed in another tab before paying. Saved cards makes its expired card by typing a past expiry, which only the stand-in payments service accepts, and stops when a card ending 4444 or 1111 is already saved.

Help: `python3 .agents/skills/verify-storefront/scripts/checks/cart.py --help`, `python3 .agents/skills/verify-storefront/scripts/checks/checkout.py --help`, and `python3 .agents/skills/verify-storefront/scripts/checks/saved_cards.py --help`.
