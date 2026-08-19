#!/usr/bin/env bash
# Orient a clone. Does not start two Sparks unless you pass --up.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> Dream stack — occupancy for 2× NVIDIA DGX Spark"
echo "    0731 TP2 @ 348k + Qwen GGUF roommate + baton :8877"
echo

ok=0
for f in setup.sh scripts/*.sh; do
  bash -n "$f"
done
python3 -m py_compile dream-baton.py
echo "syntax: setup.sh, scripts/*.sh, dream-baton.py OK"

if [[ ! -f .env ]]; then
  cp env.example .env
  echo "wrote .env from env.example"
  echo "edit at least: N2_IP  SPARK2  GGUF  LLAMA_SERVER"
  ok=1
else
  echo ".env already present (not overwritten)"
fi

if [[ "${1:-}" == "--up" ]]; then
  echo
  echo "starting roommate + baton (needs 0731 on :8888)…"
  exec bash "$ROOT/scripts/up.sh"
fi

echo
echo "Laptop / no cluster — you are done. Read README.md."
echo "Two Sparks already running 0731 @ 348k / 0.74:"
echo "  1. edit .env"
echo "  2. ./setup.sh --up"
echo "  3. curl -s http://127.0.0.1:8877/v1/models"
echo
echo "0731 recipe (not this repo):"
echo "  https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark"
exit 0
