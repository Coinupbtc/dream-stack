#!/usr/bin/env bash
# Qwen 3.8 27B GGUF on node2 leftover — exact live Dream flags.
# Requires 0731 TP2 already up. Does not start or stop 0731.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
[[ -f "$ROOT/.env" ]] && set -a && source "$ROOT/.env" && set +a

N2_IP="${N2_IP:-192.168.100.11}"
SPARK2="${SPARK2:-spark2}"
PORT="${QWEN_PORT:-8100}"
CTX="${QWEN_CTX:-88000}"
PAR="${QWEN_PARALLEL:-1}"
CACHE="${QWEN_CACHE:-q4_0}"
BATCH="${QWEN_BATCH:-4096}"
UBATCH="${QWEN_UBATCH:-1024}"
GGUF="${GGUF:-$HOME/models/hf/Qwen3.8-27B/Qwen3.8-27B-UD-Q4_K_XL.gguf}"
BIN="${LLAMA_SERVER:-$HOME/llama.cpp-v9/build/bin/llama-server}"
SPEC="${QWEN_SPEC:---spec-type draft-mtp,ngram-mod,ngram-simple --spec-draft-n-max 3 --spec-draft-p-min 0.4}"

ssh2() { ssh -o BatchMode=yes -o ConnectTimeout=12 "$SPARK2" "$@"; }

if curl -sf --max-time 3 "http://${N2_IP}:${PORT}/v1/models" >/dev/null; then
  echo "already up http://${N2_IP}:${PORT}/v1"
  exit 0
fi

ssh2 "test -x '$BIN'" || { echo "node2 missing $BIN"; exit 2; }
ssh2 "test -f '$GGUF'" || { echo "node2 missing $GGUF — rsync the UD-Q4_K_XL file first"; exit 2; }

ssh2 "pkill -f '[l]lama-server .*Qwen3.8-27B-UD-Q4_K_XL' || true; mkdir -p '\$HOME/logs'; nohup '$BIN' \
  --model '$GGUF' \
  --ctx-size '$CTX' \
  --parallel '$PAR' \
  --flash-attn on \
  --cache-type-k '$CACHE' \
  --cache-type-v '$CACHE' \
  --batch-size '$BATCH' \
  --ubatch-size '$UBATCH' \
  --host 0.0.0.0 \
  --port '$PORT' \
  --alias Qwen3.8-27B \
  --chat-template-kwargs '{\"enable_thinking\":false,\"preserve_thinking\":true}' \
  $SPEC \
  >'\$HOME/logs/qwen38-27b-n2-server.log' 2>&1 & echo \$! >'\$HOME/logs/qwen38-27b-n2.pid'"

echo "waiting for http://${N2_IP}:${PORT}/v1/models"
for i in $(seq 1 90); do
  if curl -sf --max-time 3 "http://${N2_IP}:${PORT}/v1/models" >/dev/null; then
    echo "Qwen roommate UP (:${PORT} ctx=${CTX})"
    exit 0
  fi
  sleep 2
done
echo "Qwen did not come up — check spark2:~/logs/qwen38-27b-n2-server.log"
exit 1
