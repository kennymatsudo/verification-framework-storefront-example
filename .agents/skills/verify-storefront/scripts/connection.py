"""Where the running storefront lives: the harness paths, the services' ports, and their health reads."""

import json
import os
import urllib.request
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
PROJECT_ROOT = HARNESS.parents[2]
LAUNCH_RECORD = HARNESS / "evidence" / "launch" / "record.json"

# The same variables and defaults scripts/dev.sh uses.
PORTS = {
    "payments": int(os.environ.get("PAYMENTS_PORT", "8801")),
    "shop": int(os.environ.get("STOREFRONT_PORT", "8800")),
}


def base_url(service):
    return f"http://127.0.0.1:{PORTS[service]}"


def launched_checkout(record):
    """The checkout the launched instance runs: its --checkout override, such as a scratch worktree, else this one."""
    override = (record.get("checkouts") or {}).get("storefront")
    return Path(override).resolve() if override else PROJECT_ROOT


def health(service, timeout=3):
    """The service's /health body. Raises OSError when it doesn't answer 200, ValueError when the body isn't JSON."""
    with urllib.request.urlopen(base_url(service) + "/health", timeout=timeout) as response:
        return json.loads(response.read())
