"""A real Chromium browser on the shop, driven through Playwright, that records what it does.

Needs Playwright for Python and its Chromium in the interpreter running the check (`python3 -m pip install
playwright && python3 -m playwright install chromium`). Every run records video; the video is kept in the run
folder only when the run failed or VERIFY_KEEP_RECORDING=1. Console output and failed requests are always
saved as console.json and requests.json. Each user action adds an `action` mark to the report.
"""

import json
import os

import connection

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # reported by Screen.__enter__ as a stopped run
    sync_playwright = None


class Screen:
    def __init__(self, report):
        self.report = report
        self.console, self.requests = [], []

    def __enter__(self):
        if sync_playwright is None:
            self.report.stop("Playwright for Python is not installed for this python3; see screen.py")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch()
        self._video_dir = self.report.run_dir / "video-parts"
        self.video_starts_at = self.report.at()
        self._context = self._browser.new_context(
            base_url=connection.base_url("shop"),
            viewport={"width": 1100, "height": 760},
            record_video_dir=str(self._video_dir),
            record_video_size={"width": 1100, "height": 760},
        )
        self._context.set_default_timeout(10_000)
        self.page = self._context.new_page()
        self.page.on("console", lambda msg: self.console.append({"at": self.report.at(), "text": f"{msg.type}: {msg.text}"}))
        self.page.on("requestfailed", lambda req: self.requests.append({"at": self.report.at(), "text": f"{req.method} {req.url} failed: {req.failure}"}))
        self.page.on("response", lambda res: res.status >= 400 and self.requests.append({"at": self.report.at(), "text": f"{res.request.method} {res.url} -> {res.status}"}))
        return self

    def act(self, label, do):
        """Do one user action and mark it on the timeline."""
        self.report.mark("action", label)
        do()
        self.page.wait_for_load_state()

    def goto(self, path, label=None):
        self.act(label or f"Opens {path}", lambda: self.page.goto(path))

    def snapshot(self, name):
        """A screenshot and the page's visible text, saved in the run folder; returns their file names."""
        stem = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
        shot, text = f"{stem}.png", f"{stem}.txt"
        try:
            self.page.screenshot(path=str(self.report.run_dir / shot), full_page=True)
            (self.report.run_dir / text).write_text(f"URL: {self.page.url}\n\n" + self.page.locator("body").inner_text())
        except Exception as error:  # noqa: BLE001 - a snapshot failure must not hide the step's own verdict
            (self.report.run_dir / text).write_text(f"snapshot failed: {error!r}\n")
            return {"text": text}
        return {"screenshot": shot, "text": text}

    def __exit__(self, *exc):
        video = self.page.video
        self._context.close()  # writes the video
        recorded = video.path() if video else None  # needs Playwright still running
        self._browser.close()
        self._playwright.stop()
        (self.report.run_dir / "console.json").write_text(json.dumps(self.console, indent=1))
        (self.report.run_dir / "requests.json").write_text(json.dumps(self.requests, indent=1))
        keep = bool(self.report.failed) or exc[0] is not None or os.environ.get("VERIFY_KEEP_RECORDING") == "1"
        if recorded and keep:
            target = self.report.run_dir / "video.webm"
            os.replace(recorded, target)
            self.report.recording(target.name, self.video_starts_at)
        for leftover in self._video_dir.glob("*"):
            leftover.unlink()
        if self._video_dir.exists():
            self._video_dir.rmdir()
        return False
