#!/usr/bin/env bash
# Probe the live Dream occupancy (head node).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
[[ -f "$ROOT/.env" ]] && set -a && source "$ROOT/.env" && set +a
# RFC 5737 TEST-NET-1 fallback — override via N2_IP in .env
N2_IP="${N2_IP:-192.0.2.10}"

probe() {
  local name="$1" url="$2"
  if out="$(curl -sf --max-time 4 "$url" 2>/dev/null)"; then
    echo "UP   $name  $(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print([ (m.get("id"), m.get("max_model_len") or (m.get("meta") or {}).get("n_ctx")) for m in d.get("data") or []])' "$out")"
  else
    echo "DOWN $name  $url"
  fi
}

echo "=== dream-stack status $(date -Iseconds) ==="
probe "0731  :8888" "http://127.0.0.1:8888/v1/models"
probe "Qwen  ${N2_IP}:8100" "http://${N2_IP}:8100/v1/models"
probe "vision :8890" "http://127.0.0.1:8890/v1/models"
probe "vision :8891" "http://127.0.0.1:8891/v1/models"
probe "baton  :8877" "http://127.0.0.1:8877/v1/models"
free -g | head -2
