#!/usr/bin/env bash
# Restart the harness's storefront instance from a checkout: stop what vf.py start launched, then start
# CHECKOUT's own scripts/dev.sh through serve.sh, recording CHECKOUT's code for repo REPO, and wait until the
# readiness check passes. vf.py break runs this to point the app at a scratch worktree and back. Neither
# service reloads on edit, so this is also how an edit takes effect.
# Usage, from the project root: relaunch.sh REPO CHECKOUT
set -euo pipefail

usage() { sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; }
case "${1:-}" in -h|--help) usage; exit 0 ;; esac
if [ $# -ne 2 ]; then usage >&2; exit 2; fi

harness=".agents/skills/verify-storefront"
python3 "$harness/scripts/framework/vf.py" stop
exec python3 "$harness/scripts/framework/vf.py" start --checkout "$1=$2" \
  --until "python3 $harness/scripts/doctor.py" -- "$harness/scripts/serve.sh" "$2"
