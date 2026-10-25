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
