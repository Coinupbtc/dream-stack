#!/usr/bin/env bash
# One command after `cp env.example .env`: require 0731, start roommate + baton, smoke.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
if [[ ! -f "$ROOT/.env" ]]; then
  echo "copy env.example to .env and edit N2_IP / SPARK2 / GGUF / LLAMA_SERVER"
  echo "  cp $ROOT/env.example $ROOT/.env"
  exit 2
fi
set -a && source "$ROOT/.env" && set +a

if ! curl -sf --max-time 5 http://127.0.0.1:8888/v1/models | grep -q deepseek; then
  cat <<'EOF'
0731 is not answering on http://127.0.0.1:8888/v1

Start Mia DSpark TP2 first, with Dream knobs:
  export MAX_MODEL_LEN=347392
  export GPU_MEMORY_UTILIZATION_TEXT=0.74
  export ENABLE_VL_SIDECAR=0
  ./start-deepseek-v4-flash-dspark.sh

https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark
EOF
  exit 2
fi

bash "$ROOT/scripts/start-roommate.sh"
BATON_DAEMON=1 bash "$ROOT/scripts/start-baton.sh"
bash "$ROOT/scripts/status.sh"
bash "$ROOT/scripts/smoke.sh"
echo "ready  http://127.0.0.1:${BATON_PORT:-8877}/v1  model=dream-baton"
