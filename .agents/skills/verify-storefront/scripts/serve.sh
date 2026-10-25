#!/usr/bin/env bash
# Run the storefront the way developers do, through scripts/dev.sh start, and stay in the foreground while
# both services run, so vf.py start records one process group and vf.py stop ends all of it.
# dev.sh backgrounds the services and exits at once, so the launcher can't track it directly.
# Usage: serve.sh [CHECKOUT]   CHECKOUT defaults to the repo this harness sits in.
set -euo pipefail

case "${1:-}" in -h|--help) sed -n '2,5p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac

here="$(cd "$(dirname "$0")" && pwd)"
checkout="$(cd "${1:-$here/../../../..}" && pwd)"

# dev.sh would report an instance it finds through its PID files as "already running" and return, which would
# hand the launcher a group that doesn't own the services.
for name in payments shop; do
  pidfile="$checkout/data/$name.pid"
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "serve: $name is already running as process $(cat "$pidfile"), started outside this harness; stop it with scripts/dev.sh stop first" >&2
    exit 1
  fi
done

trap '"$checkout/scripts/dev.sh" stop' EXIT
"$checkout/scripts/dev.sh" start

while :; do
  for name in payments shop; do
    if ! kill -0 "$(cat "$checkout/data/$name.pid" 2>/dev/null)" 2>/dev/null; then
      echo "serve: $name exited; see $checkout/data/$name.log" >&2
      exit 1
    fi
  done
  sleep 1
done
