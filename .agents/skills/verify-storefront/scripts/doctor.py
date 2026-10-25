#!/usr/bin/env python3
"""Readiness check for the storefront: is the instance vf.py start launched up, running the code under test,
and the one answering on the shop and payments ports?

It first runs the framework's `vf.py doctor`, which confirms the launched process group is alive and that the
checkout's commit and uncommitted changes still match what was on disk at launch; neither service reloads on
edit, so that is the code they loaded. Then, for each service, it confirms that a process in the launched group
is listening on the port, that /health answers ok, that the commit /health reports (read once at the service's
startup) is the launch record's commit, and that the service runs from the launched checkout. A port held by
any other process, such as an instance started by hand with scripts/dev.sh, is not ready.

Read-only: it sends GET /health and reads process information; it starts and stops nothing.
Ports come from STOREFRONT_PORT and PAYMENTS_PORT, defaulting to 8800 and 8801, as in scripts/dev.sh.

Exit 0: ready. Prints one line per service, an auth line, a code line, and last `verify-storefront: ready`.
Exit 1: not ready. One `not ready:` reason per line.
Exit 2: could not tell, such as lsof missing or an unreadable launch record. A `STOPPED:` line.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import connection

READY_LINE = "verify-storefront: ready"


def listening_pids(port):
    """PIDs listening on the local TCP port. Raises FileNotFoundError when lsof is missing."""
    result = subprocess.run(["lsof", "-nP", "-t", f"-iTCP:{port}", "-sTCP:LISTEN"], capture_output=True, text=True)
    return sorted({int(line) for line in result.stdout.split()})


def working_directory(pid):
    """The process's current directory, or None when lsof can't read it."""
    result = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], capture_output=True, text=True)
    names = [line[1:] for line in result.stdout.splitlines() if line.startswith("n")]
    return Path(names[0]).resolve() if names else None


def process_group(pid):
    try:
        return os.getpgid(pid)
    except ProcessLookupError:
        return None


def check_service(service, group, checkout, commit):
    """One line describing the service when it is ready, and the reasons it is not."""
    port = connection.PORTS[service]
    pids = listening_pids(port)
    if not pids:
        return None, [f"not ready: nothing listens on the {service} port {port}"]
    reasons = [
        f"not ready: the {service} port {port} is held by process {pid}, which vf.py start did not launch; stop it or use other ports"
        for pid in pids
        if process_group(pid) != group
    ]
    try:
        body = connection.health(service)
    except (OSError, ValueError) as error:
        return None, reasons + [f"not ready: {service} /health did not answer: {error}"]
    if body.get("status") != "ok":
        reasons.append(f"not ready: {service} /health reports status {body.get('status')!r}")
    if body.get("commit") != commit:
        reasons.append(f"not ready: {service} reports commit {body.get('commit')}, but the launch recorded {commit}; restart it")
    cwd = working_directory(pids[0])
    if cwd != checkout:
        reasons.append(f"not ready: {service} runs from {cwd}, not the launched checkout {checkout}")
    database = Path(body.get("database", ""))
    database = database if database.is_absolute() or cwd is None else cwd / database
    line = f"{service}: up, process {pids[0]} in launched group {group}, port {port}, commit {str(body.get('commit'))[:7]}, database {database}"
    return line, reasons


def main():
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()

    framework = subprocess.run(
        [sys.executable, str(connection.HARNESS / "scripts" / "framework" / "vf.py"), "doctor"],
        cwd=connection.PROJECT_ROOT, capture_output=True, text=True,
    )
    if framework.returncode != 0:
        sys.stdout.write(framework.stdout)
        sys.stderr.write(framework.stderr)
        return framework.returncode

    try:
        record = json.loads(connection.LAUNCH_RECORD.read_text())
        code = json.loads(framework.stdout.split("\n", 1)[1])["storefront"]
    except (OSError, ValueError, IndexError, KeyError) as error:
        print(f"STOPPED: could not read the launch record or code state: {error}")
        return 2

    lines, reasons = [], []
    try:
        for service in connection.PORTS:
            line, service_reasons = check_service(service, record["pid"], connection.launched_checkout(record), code["commit"])
            reasons += service_reasons
            if line:
                lines.append(line)
    except FileNotFoundError:
        print("STOPPED: lsof is not installed, so the ports' owners can't be checked")
        return 2

    if reasons:
        print("\n".join(reasons))
        return 1
    dirty = f"uncommitted changes {code['dirty_hash'][:12]}" if code["dirty"] else "clean"
    lines.append("auth: none; the shop has one always signed-in customer")
    lines.append(f"code: storefront {code['commit'][:7]} on {code['branch']}, {dirty}, on default branch: {code['on_main']}")
    lines.append(READY_LINE)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
