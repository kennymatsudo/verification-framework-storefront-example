#!/usr/bin/env bash
# Start, stop, or report the two local processes: the shop on port 8800 and the payments service on port 8801.
# Process IDs and logs live under data/, which Git ignores.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data
SHOP_PORT="${STOREFRONT_PORT:-8800}"
PAY_PORT="${PAYMENTS_PORT:-8801}"
export PAYMENTS_URL="${PAYMENTS_URL:-http://127.0.0.1:$PAY_PORT}"

start_one() { # name module port
  local name=$1 module=$2 port=$3
  if [ -f "data/$name.pid" ] && kill -0 "$(cat "data/$name.pid")" 2>/dev/null; then
    echo "$name already running (pid $(cat "data/$name.pid"))"; return
  fi
  nohup uv run uvicorn $module --host 127.0.0.1 --port "$port" > "data/$name.log" 2>&1 &
  echo $! > "data/$name.pid"
  for _ in $(seq 1 50); do
    if curl -fsS "http://127.0.0.1:$port/health" > /dev/null 2>&1; then echo "$name ready on :$port"; return; fi
    sleep 0.2
  done
  echo "$name did not become ready; see data/$name.log" >&2; exit 2
}

stop_one() {
  local name=$1
  if [ -f "data/$name.pid" ]; then
    kill "$(cat "data/$name.pid")" 2>/dev/null || true
    rm -f "data/$name.pid"
    echo "$name stopped"
  fi
}

case "${1:-}" in
  start) start_one payments payments.main:app "$PAY_PORT"; start_one shop "--factory shop.main:create_app" "$SHOP_PORT" ;;
  stop) stop_one shop; stop_one payments ;;
  status)
    for pair in "payments:$PAY_PORT" "shop:$SHOP_PORT"; do
      name=${pair%%:*}; port=${pair##*:}
      curl -fsS "http://127.0.0.1:$port/health" 2>/dev/null || echo "{\"service\": \"$name\", \"status\": \"down\"}"
      echo
    done ;;
  reset) "$0" stop; rm -f data/shop.sqlite data/payments.sqlite; echo "databases removed" ;;
  *) echo "usage: scripts/dev.sh start|stop|status|reset" >&2; exit 2 ;;
esac
