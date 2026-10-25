# Storefront verification settings

The values `rules.md` refers to for this app. Change a rule in the framework that provides `rules.md`, not here.

## Setup

- Status: ready

## Workflow

- Requirements source: REQUIREMENTS.md

## Repos

- storefront: .

## Commands

- Start: python3 .agents/skills/verify-storefront/scripts/framework/vf.py start --until "python3 .agents/skills/verify-storefront/scripts/doctor.py" -- .agents/skills/verify-storefront/scripts/serve.sh
- Stop: python3 .agents/skills/verify-storefront/scripts/framework/vf.py stop
- Doctor: python3 .agents/skills/verify-storefront/scripts/doctor.py
- Ready line: verify-storefront: ready
- Probe: none yet
- Run scratch code: .agents/skills/verify-storefront/scripts/relaunch.sh {repo} {checkout}
- After an edit: .agents/skills/verify-storefront/scripts/relaunch.sh {repo} {checkout}

All commands run from the project root. Start runs the repo's own `scripts/dev.sh start` through `serve.sh`, which stays in the foreground so the launcher can record and stop both services as one process group. The agent may start and stop the app: it needs no login, secret, or human step, only `uv`, `curl`, and `lsof` on this machine, and it touches nothing outside this machine. The services listen on 127.0.0.1:8800 (shop) and 127.0.0.1:8801 (payments) and write their SQLite databases, logs, and PID files under the checkout's `data/`. Neither service reloads on edit, so After an edit restarts them.
