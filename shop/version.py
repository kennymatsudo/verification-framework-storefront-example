"""The commit this process was started from, so the health endpoint can name the code it runs."""

import subprocess
from pathlib import Path


def current_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"
