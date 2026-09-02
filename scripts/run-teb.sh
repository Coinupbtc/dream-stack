#!/usr/bin/env bash
# tool-eval-bench wrapper matching the published RESULTS.md numbers.
#   bash scripts/run-teb.sh --short baton
#   bash scripts/run-teb.sh 69 baton|0731|qwen
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
[[ -f "$ROOT/.env" ]] && set -a && source "$ROOT/.env" && set +a
export PATH="${HOME}/.local/bin:${PATH}"
# RFC 5737 TEST-NET-1 fallback — override via N2_IP in .env
N2_IP="${N2_IP:-192.0.2.10}"
QWEN_PORT="${QWEN_PORT:-8100}"
BATON_PORT="${BATON_PORT:-8877}"
OUT="${ROOT}/runs"
KW='{"chat_template_kwargs":{"thinking":false,"enable_thinking":false},"enable_thinking":false}'

SHORT=()
if [[ "${1:-}" == "--short" ]]; then
  SHORT=(--short)
  shift
fi
WHICH="${1:-baton}"
SUITE=69
if [[ "$WHICH" == "69" || "$WHICH" == "15" ]]; then
  [[ "$WHICH" == "15" ]] && SHORT=(--short)
  shift
  WHICH="${1:-baton}"
fi
if [[ "$WHICH" == "baton" || "$WHICH" == "0731" || "$WHICH" == "ds4f" || "$WHICH" == "qwen" ]]; then
  shift || true
fi
SCENARIOS=("$@")

case "$WHICH" in
  baton) BASE="http://127.0.0.1:${BATON_PORT}" MODEL="dream-baton" LABEL="dream-baton" ;;
  0731|ds4f) BASE="http://127.0.0.1:8888" MODEL="deepseek-v4-flash-0731" LABEL="dream-0731-348k" ;;
  qwen) BASE="http://${N2_IP}:${QWEN_PORT}" MODEL="Qwen3.8-27B" LABEL="dream-qwen38-gguf-88k" ;;
  *) echo "usage: $0 [--short] [69] baton|0731|qwen [TC-03 TC-61 ...]" >&2; exit 2 ;;
esac
if ((${#SCENARIOS[@]})); then
  LABEL="${LABEL}-subset"
fi

if ! command -v tool-eval-bench >/dev/null 2>&1; then
  echo "installing tool-eval-bench"
  uv tool install 'git+https://github.com/SeraphimSerapis/tool-eval-bench.git'
fi

mkdir -p "$OUT"
echo "teb $WHICH  $BASE  $MODEL  seed=42  thinking=off  ${SCENARIOS[*]:-all}"
EXTRA=()
if ((${#SCENARIOS[@]})); then
  EXTRA=(--scenarios "${SCENARIOS[@]}")
fi
TOOL_EVAL_BASE_URL="$BASE" TOOL_EVAL_MODEL="$MODEL" \
  tool-eval-bench run --seed 42 --label "$LABEL" \
    --base-url "$BASE" --model "$MODEL" \
    --backend-kwargs "$KW" \
    --output-dir "$OUT" \
    "${SHORT[@]}" \
    "${EXTRA[@]}"
