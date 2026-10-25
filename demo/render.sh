#!/usr/bin/env bash
# Render every terminal scene from its tape. Needs vhs, and the app's ports free.
set -euo pipefail
cd "$(dirname "$0")/.."
for tape in demo/tapes/*.tape; do
  echo "== $tape"
  vhs "$tape"
done
ls -la demo/out
