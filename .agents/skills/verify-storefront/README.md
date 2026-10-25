# Verify storefront

This folder proves changes to the Northwind Goods storefront work by driving the running shop and payments services and reading back the result. An AI agent uses it through the `verify-storefront` skill; you can use it directly too.

- **Verify a change:** ask your agent to "verify my change to the storefront".
- **See what passed and failed:** [status.md](status.md). Known limits and untested cases are in [notes.md](notes.md).
- **See how each check last ran, and watch recordings:** open [recordings.html](recordings.html) in a browser.
- **See what's covered:** [the feature map](features/README.md).
- **Debug by hand:** [tools.md](tools.md) lists every command. Check the app is up with the readiness check listed there.

Keep a passing run's video by running a check with `VERIFY_KEEP_RECORDING=1`. A failed run keeps its video on its own.

Files in `scripts/framework/` and `rules.md`, and the `vf`, `vf-verify`, and `vf-explain` folders beside this one, are copied from verification-framework and are never edited here; vf's update mode replaces them all. Nothing to install: your agent finds the skills in this repo.
