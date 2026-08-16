#!/usr/bin/env bash
# One-URL baton on :8877. Does not start 0731 or Qwen.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
[[ -f "$ROOT/.env" ]] && set -a && source "$ROOT/.env" && set +a
export BATON_HOST="${BATON_HOST:-127.0.0.1}"
export BATON_PORT="${BATON_PORT:-8877}"
export BATON_0731="${BATON_0731:-http://127.0.0.1:8888/v1}"
export BATON_QWEN="${BATON_QWEN:-http://192.168.100.11:8100/v1}"
export BATON_MAX_LEN="${BATON_MAX_LEN:-347392}"
export BATON_QWEN_SAFE="${BATON_QWEN_SAFE:-75000}"

if curl -sf --max-time 2 "http://${BATON_HOST}:${BATON_PORT}/health" >/dev/null; then
  echo "baton already up :${BATON_PORT}"
  exit 0
fi

mkdir -p "${HOME}/logs"
if [[ "${BATON_DAEMON:-0}" == "1" ]]; then
  nohup python3 "$ROOT/dream-baton.py" >>"${HOME}/logs/dream-baton.log" 2>&1 &
  echo $! >"${HOME}/logs/dream-baton.pid"
  for _ in $(seq 1 20); do
    if curl -sf --max-time 1 "http://${BATON_HOST}:${BATON_PORT}/health" >/dev/null; then
      echo "baton UP :${BATON_PORT} pid=$(cat "${HOME}/logs/dream-baton.pid")"
      exit 0
    fi
    sleep 0.25
  done
  echo "baton did not bind :${BATON_PORT} — see ${HOME}/logs/dream-baton.log"
  exit 1
fi

exec python3 "$ROOT/dream-baton.py"
