"""Where the running storefront lives: the harness paths, the services' ports, and their health reads."""

import json
import os
import sqlite3
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


def running_checkout():
    """The checkout the running instance serves: the launch record's while its process is alive, else this one."""
    if not LAUNCH_RECORD.exists():
        return PROJECT_ROOT
    record = json.loads(LAUNCH_RECORD.read_text())
    try:
        os.kill(record["pid"], 0)
    except ProcessLookupError:
        return PROJECT_ROOT  # a record left by a crashed launch names nothing that runs
    except PermissionError:
        pass  # alive, owned by another user
    return launched_checkout(record)


def database_path(service):
    """The SQLite file the running service writes. /health names it relative to the service's working
    directory, which scripts/dev.sh sets to the checkout. Raises OSError when the service doesn't answer,
    and FileNotFoundError when the file is missing."""
    path = Path(health(service)["database"])
    if not path.is_absolute():
        path = running_checkout() / path
    if not path.exists():
        raise FileNotFoundError(f"the {service} database {path} does not exist")
    return path


def read_only(service):
    """A read-only connection to the service's database; it cannot write even by mistake."""
    connection = sqlite3.connect(f"file:{database_path(service)}?mode=ro", uri=True, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection
