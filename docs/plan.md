# Demo plan

This repo is the public demo of the verification framework. It exists to show one story: a coding agent says "done" and, because the repo has a verification harness, "done" comes with proof that anyone can inspect and rerun.

## The story, in three cuts

1. **The hero run.** One prompt asks an agent to build "pay with a saved card." Before it reports done, it previews what it will prove, asks about the one open requirement, builds the checks and the probe they need, shows each check failing on a planned break, runs them on the real app, and opens a pull request with the result and a clip.
2. **The teammate's pull request.** A PR with green unit tests and a confident description carries a regression: the screen shows a discounted total, but the payments service charged full price. The harness catches it, and the PR comment says what it did, what it read, and which break the check was shown to fail on. A second, clean PR gets a green comment and the demo clip.
3. **The instruments.** The harness folder holds command-line probes and actions any teammate can run by hand. None of them asks the app whether it is fine; they read the database, the raw response, or the screen.

## What the repo contains

- A small storefront: browse, cart, checkout with a new card, order history. FastAPI, Jinja templates, SQLite.
- A separate payments service, also FastAPI and SQLite, so an order's outcome depends on two processes agreeing.
- Unit tests that mock the repository and the payments client. They are honest tests of the kind real teams write, and they stay green on the planted regression.
- `REQUIREMENTS.md`, the only source of expected behavior. One item is deliberately open so the agent has to ask.
- `AGENTS.md`, which tells an agent to verify with the harness before reporting done.
- The verification harness, built by the framework's own setup, not by hand, and committed with its evidence and recordings.
- `demo/`, the scripts that run and capture every scene so the demo re-renders when the app or the skills change.

Hidden breaks and the answer sheet for the agent's questions live in a private companion repo until the demo is filmed and graded. They are published afterward with the grading result.

## Build order

Each slice is checkable on its own.

1. The app, unit tests, requirements, seed data, agent instructions. Done when both processes start with one command and the tests pass.
2. The harness, through the framework's setup. Done when `vf.py validate` passes and the harness is committed.
3. Baseline checks for checkout, through the framework. Done when checkout's behaviors are Verified with their break records committed.
4. The two teammate PRs, verified through the framework. Done when both comments are on GitHub.
5. The hero run, as a real agent session captured by the demo scripts. Done when the agent verifies before reporting done and opens the PR with its comment and clip.
6. The public surface: recordings on GitHub Pages, a README that tells the story, the hidden breaks published with their grading.

## Finish condition

Someone who has never heard of the framework opens the repo, reads a PR comment, watches the clip, clones, and runs a probe by hand.

## Decisions

- Python and FastAPI over Node. The framework's practice repos already prove recorded screen checks in Node; doing it in Python exercises a path nothing has yet.
- Payments as a second process, so the planted regression is two components disagreeing, which is what the harness exists to catch.
- Hidden breaks private until graded, then public, so "caught every break it never saw" is a claim a skeptic can rerun.
- Test-first (checks written before the feature exists) stays parked in the framework. The hero run builds first and proves within the agreed scope.
- No ORM, no frontend build, no Docker: each adds a layer between the check and the stored state and nothing a viewer would notice.

## Capture

- Terminal scenes: VHS tapes, one theme and font size throughout.
- The hero session: run for real through the agent's command line with a scripted developer answering, captured with asciinema, rendered with agg, framed and captioned with Remotion. Labeled as a replay of a real session.
- Screen clips: the harness's own `vf.py clip --demo` output, never a hand recording.
- README: a GIF under 15 seconds made with gifski. PR comments: the MP4 attached directly.
- Every frame is checked at phone width before it ships.
