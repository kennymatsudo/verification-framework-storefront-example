"""The events a check reports to `vf.py run`, one JSON object per line in the file VERIFY_REPORT names.

Each event is appended the moment it happens, so a crash later in the run can't hide an earlier step.
`vf.py run` builds the evidence file from these; a check never writes evidence itself.
"""

import json
import os
import sys
import time
import traceback
from pathlib import Path


class Report:
    def __init__(self, name, sub_features, reads):
        path = os.environ.get("VERIFY_REPORT")
        if not path:
            print("STOPPED: run this check through `vf.py run --`, which sets VERIFY_REPORT", file=sys.stderr)
            sys.exit(2)
        self.path = Path(path)
        self.run_dir = Path(os.environ.get("VERIFY_RUN_DIR") or self.path.parent)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.started = time.monotonic()
        self.failed = []
        self._emit({"event": "check", "name": name, "sub_features": sub_features, "reads": reads})

    def at(self):
        """Seconds since the check started."""
        return round(time.monotonic() - self.started, 2)

    def _emit(self, event):
        with self.path.open("a") as out:
            out.write(json.dumps(event) + "\n")

    def mark(self, kind, label):
        self._emit({"event": "mark", "kind": kind, "label": label, "at": self.at()})

    def step(self, name, passed, sub_features=(), detail=None, evidence=None, snapshot=None):
        event = {"event": "step", "name": name, "passed": bool(passed), "at": self.at(), "sub_features": list(sub_features)}
        for key, value in (("detail", detail), ("evidence", evidence), ("snapshot", snapshot)):
            if value is not None:
                event[key] = value
        self._emit(event)
        print(f"{'PASS' if passed else 'FAIL'} {name}" + (f": {detail}" if detail else ""))
        if not passed:
            self.failed.append(name)
        return bool(passed)

    def judge(self, name, sub_features, decide, on_fail=None):
        """Run decide(), which returns (passed, detail, evidence), and report it as a step. An error in decide
        is a failed step, so independent steps after it still run. on_fail() may return a snapshot to attach."""
        try:
            passed, detail, evidence = decide()
        except Exception as error:  # noqa: BLE001 - any error is this step's failure, not the run's
            passed, detail, evidence = False, f"error: {error!r}", {"traceback": traceback.format_exc(limit=3)}
        snapshot = on_fail(name) if (not passed and on_fail) else None
        return self.step(name, passed, sub_features, detail, evidence, snapshot)

    def created(self, **ids):
        self._emit({"event": "created", **{kind: [str(i) for i in values] for kind, values in ids.items()}})

    def recording(self, video, starts_at):
        self._emit({"event": "recording", "video": video, "starts_at": starts_at})

    def stop(self, reason):
        """Report that the run can't reach a verdict, and exit 2."""
        self._emit({"event": "stopped", "reason": reason})
        print(f"STOPPED: {reason}", file=sys.stderr)
        sys.exit(2)

    def finish(self):
        """Exit 0 when every step passed, 1 when any failed."""
        sys.exit(1 if self.failed else 0)
