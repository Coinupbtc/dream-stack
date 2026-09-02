#!/usr/bin/env bash
# Two-token chat against 0731, Qwen, and baton. Fail loud.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
[[ -f "$ROOT/.env" ]] && set -a && source "$ROOT/.env" && set +a
# RFC 5737 TEST-NET-1 fallback — override via N2_IP in .env
N2_IP="${N2_IP:-192.0.2.10}"
QWEN_PORT="${QWEN_PORT:-8100}"

chat() {
  local name="$1" url="$2" model="$3"
  local body out content
  body="$(python3 -c 'import json,sys; print(json.dumps({"model":sys.argv[1],"max_tokens":16,"temperature":0,"messages":[{"role":"user","content":"Reply with the single word: pong"}]}))' "$model")"
  out="$(curl -sf --max-time 60 "$url/chat/completions" -H 'Content-Type: application/json' -d "$body")"
  content="$(python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print((d.get("choices") or [{}])[0].get("message",{}).get("content") or "")' <<<"$out")"
  if [[ -z "${content// }" ]]; then
    echo "FAIL $name  empty content"
    echo "$out" | head -c 400
    echo
    return 1
  fi
  echo "OK   $name  ${content//$'\n'/ } "
}

chat "0731 " "http://127.0.0.1:8888/v1" "deepseek-v4-flash-0731"
chat "Qwen " "http://${N2_IP}:${QWEN_PORT}/v1" "Qwen3.8-27B"
chat "baton" "http://127.0.0.1:${BATON_PORT:-8877}/v1" "dream-baton"
echo "smoke ok"
