# Storyboard

Each scene is produced by a script under `demo/`, from a real run. Nothing is staged or typed by hand. `demo/render.sh` renders everything: the VHS tapes, the hero session replay (`demo/replay.py hero`), the PR comment stills (`demo/stills.py`), and the Remotion cuts under `demo/video/`. Rendered files go under `demo/out/`, which Git ignores.

| # | Scene | Length | Source | Script |
| --- | --- | --- | --- | --- |
| 1 | "Done, tests pass": the discount PR's description and its green unit tests | 14 s | VHS tape running `uv run pytest` on the PR branch, then the PR page | `demo/tapes/tests-pass.tape` |
| 2 | The harness catches it: the PR comment with "1 problem found", expanded to the charge read from the payments ledger | 15 s | Screenshot sequence of the real PR comment, framed in Remotion | `demo/stills.py` |
| 3 | The planned break: the same check failing on a copy with the behavior broken on purpose, then `vf.py status` flipping the behavior to Verified | 56 s | VHS tape running `vf.py break run` and `vf.py status` | `demo/tapes/calibration.tape` |
| 4 | The clip: PR #4's green comment with the 15 s saved-cards clip the framework cut (PR #3 got no clip: the harness had nothing to add there, which is the rule working) | 15 s | `vf.py clip --demo` output, attached to the comment | the harness |
| 5 | The instruments: a probe and an action by hand, with `--help` | 28 s | VHS tape | `demo/tapes/instruments.tape` |
| 6 | The hero run: one prompt builds saved cards and verifies before saying done, with the preview, the three open questions, the unusable first clip, and the PR | 130 s full, 42 s in the cut | `demo/replay.py hero`: a cast built from the saved session (words unedited, tool calls summarised, timing synthetic), rendered with agg | `demo/replay.py` |

The README opens with a 14 s GIF of scenes 1 and 2 (`demo/readme-hero.gif`, from the `ReadmeHero` composition). Each PR carries its own comment and clip. The full six-scene cut, `demo/out/demo.mp4` (3 min 30 s), is published as a GitHub release.

## Rules for every scene

- One terminal theme and font size across tapes. Checked at phone width before it ships.
- A frame is inspected for secrets, real addresses, and local paths before it is published.
- A scene that shows the agent's words shows them unedited. Waits are cut; nothing is reordered.
