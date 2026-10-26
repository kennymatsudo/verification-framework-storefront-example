#!/usr/bin/env python3
"""Screenshot the verification comments on the public PRs, collapsed and expanded, for the framed stills scene.

    demo/stills.py            # writes demo/out/stills/pr<N>-<state>.png for PRs 2 and 4
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_URL = "https://github.com/kennymatsudo/verification-framework-storefront-example"
OUT = Path(__file__).resolve().parent / "out" / "stills"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=2)
        for number in (2, 4):
            page.goto(f"{REPO_URL}/pull/{number}")
            page.wait_for_selector("div.timeline-comment")
            comment = page.locator("div.timeline-comment", has_text="Tested with Verification Framework").last
            # The sticky PR header would otherwise land across the middle of a tall element screenshot.
            page.add_style_tag(content="[class*=stickyHeader], .AppHeader { display: none !important; }")
            comment.scroll_into_view_if_needed()
            # Let the embedded clip load its first frame so the still doesn't show a spinner.
            page.wait_for_function("[...document.querySelectorAll('video')].every(v => v.readyState >= 2)", timeout=15000)
            comment.screenshot(path=OUT / f"pr{number}-collapsed.png")
            # Only the "How it was checked" folds; the edit-history dropdown in the header is a details element too.
            comment.evaluate("el => el.querySelectorAll('.comment-body details').forEach(d => { d.open = true })")
            page.wait_for_timeout(300)
            comment.screenshot(path=OUT / f"pr{number}-expanded.png")
            print(f"PR #{number}: {OUT / f'pr{number}-collapsed.png'}, {OUT / f'pr{number}-expanded.png'}")
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
