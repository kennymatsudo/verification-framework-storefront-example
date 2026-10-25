# Storyboard

Each scene is produced by a script under `demo/`, from a real run. Nothing is staged or typed by hand. Re-render everything with `demo/render.sh` once the scripts exist.

| # | Scene | Length | Source | Script |
| --- | --- | --- | --- | --- |
| 1 | "Done, tests pass": the discount PR's description and its green unit tests | 8 s | VHS tape running `uv run pytest` on the PR branch, then the PR page | `demo/tapes/tests-pass.tape` |
| 2 | The harness catches it: the PR comment with "1 problem found", expanded to the charge read from the payments ledger | 15 s | Screenshot sequence of the real PR comment, framed in Remotion | `demo/render/` |
| 3 | The planned break: the same check failing on a copy with the behavior broken on purpose, then `vf.py status` flipping the behavior to Verified | 12 s | VHS tape running `vf.py break run` and `vf.py status` | `demo/tapes/calibration.tape` |
| 4 | The clip: the clean PR's green comment with the delivery-date clip the framework cut | 10 s | `vf.py clip --demo` output | the harness |
| 5 | The instruments: a probe and an action by hand, with `--help` | 15 s | VHS tape | `demo/tapes/instruments.tape` |
| 6 | The hero run: one prompt builds saved cards and verifies before saying done, with the preview, the question about expired cards, the break, and the PR | 60 s | asciinema recording of the real headless session, rendered with agg, cut in Remotion | `demo/hero.sh` |

The README gets scene 2 as a GIF. Each PR carries its own comment and clip. The landing page, if there is one, gets scene 6.

## Rules for every scene

- One terminal theme and font size across tapes. Checked at phone width before it ships.
- A frame is inspected for secrets, real addresses, and local paths before it is published.
- A scene that shows the agent's words shows them unedited. Waits are cut; nothing is reordered.
