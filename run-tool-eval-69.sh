#!/usr/bin/env bash
# Full 69-scenario tool-eval-bench on the live Dream occupancy.
# Sequential: 0731 first, then Qwen. Thinking OFF so it matches our speed notes
# and does not sit in 0731 DEFAULT_THINKING=max for an hour.
#
#   bash ~/Documents/projects/dream-stack/run-tool-eval-69.sh
set -euo pipefail
HOME="${HOME:-/home/coinupbtc}"
export PATH="$HOME/.local/bin:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/runs"
LOG="$HOME/logs/dream-tool-eval-69.$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$OUT" "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
echo "LOG=$LOG"

if ! command -v tool-eval-bench >/dev/null 2>&1; then
  echo "installing tool-eval-bench (once)"
  uv tool install 'git+https://github.com/SeraphimSerapis/tool-eval-bench.git'
fi
tool-eval-bench --help >/dev/null
echo "teb=$(command -v tool-eval-bench)"

KW='{"chat_template_kwargs":{"thinking":false,"enable_thinking":false},"enable_thinking":false}'

run_one() {
  local label="$1" base="$2" model="$3"
  echo "======== $label $base $model ========"
  date -Iseconds
  TOOL_EVAL_BASE_URL="$base" TOOL_EVAL_MODEL="$model" \
    tool-eval-bench run --seed 42 --label "$label" \
      --base-url "$base" --model "$model" \
      --backend-kwargs "$KW" \
      --output-dir "$OUT"
  date -Iseconds
}

# RFC 5737 TEST-NET-1 fallback — override via N2_IP
N2_IP="${N2_IP:-192.0.2.10}"

# keep the trio alive — fail loud if someone parked an engine
curl -sf --max-time 5 http://127.0.0.1:8888/v1/models | grep -q deepseek
curl -sf --max-time 5 "http://${N2_IP}:8100/v1/models" | grep -qi qwen

run_one "dream-0731-348k" "http://127.0.0.1:8888" "deepseek-v4-flash-0731"
run_one "dream-qwen38-gguf-88k" "http://${N2_IP}:8100" "Qwen3.8-27B"

echo "DONE both 69s"
ls -lt "$OUT" | head
