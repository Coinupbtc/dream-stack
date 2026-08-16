#!/usr/bin/env bash
# Download the exact Unsloth GGUF Dream uses, then rsync to node2.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
[[ -f "$ROOT/.env" ]] && set -a && source "$ROOT/.env" && set +a

DEST_DIR="$(dirname "${GGUF:-$HOME/models/hf/Qwen3.8-27B/Qwen3.8-27B-UD-Q4_K_XL.gguf}")"
FILE="Qwen3.8-27B-UD-Q4_K_XL.gguf"
SPARK2="${SPARK2:-spark2}"

mkdir -p "$DEST_DIR"
if [[ -f "$DEST_DIR/$FILE" ]] && [[ "$(stat -c%s "$DEST_DIR/$FILE")" -ge 16000000000 ]]; then
  echo "already have $DEST_DIR/$FILE ($(du -h "$DEST_DIR/$FILE" | awk '{print $1}'))"
else
  if command -v huggingface-cli >/dev/null 2>&1; then
    huggingface-cli download unsloth/Qwen3.8-27B-GGUF "$FILE" --local-dir "$DEST_DIR"
  else
    python3 - <<PY
from huggingface_hub import hf_hub_download
print(hf_hub_download("unsloth/Qwen3.8-27B-GGUF", "$FILE", local_dir="$DEST_DIR"))
PY
  fi
fi

if ssh -o BatchMode=yes -o ConnectTimeout=8 "$SPARK2" true 2>/dev/null; then
  ssh "$SPARK2" "mkdir -p '$DEST_DIR'"
  rsync -aP "$DEST_DIR/$FILE" "$SPARK2:$DEST_DIR/$FILE"
  echo "synced to $SPARK2:$DEST_DIR/$FILE"
else
  echo "node2 ssh ($SPARK2) not reachable — copy $DEST_DIR/$FILE yourself"
fi
