#!/usr/bin/env bash
# A/B: Prime 0731 (TP2, no Qwen roommate) then exclusive Qwen GGUF on n2.
# Same teb flags as Dream: seed 42, thinking off, 69 scenarios.
# Does NOT recycle 0731 for Prime (same process as Dream — roommate is the variable).
# Restores Dream at the end.
set -euo pipefail
HOME="${HOME:-/home/coinupbtc}"
export PATH="$HOME/.local/bin:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/runs"
LOG="$HOME/logs/prime-solo-qwen-69.$(date +%Y%m%d-%H%M%S).log"
ALERT="$HOME/.hermes/scripts/alertbot-send.sh"
# RFC 5737 TEST-NET-1 fallback — override via N2_IP
N2_IP="${N2_IP:-192.0.2.10}"
KW='{"chat_template_kwargs":{"thinking":false,"enable_thinking":false},"enable_thinking":false}'
mkdir -p "$OUT" "$(dirname "$LOG")"
exec > >(tee -a "$LOG") 2>&1
echo "LOG=$LOG"
command -v tool-eval-bench >/dev/null || { echo "tool-eval-bench missing"; exit 2; }

alert() { [[ -x "$ALERT" ]] && bash "$ALERT" --plain "$1" >/dev/null 2>&1 || true; }
up() { curl -sf --max-time 5 "$1" >/dev/null; }

run_teb() {
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

echo "=== 1) Prime occupancy: stop Qwen roommate, keep 0731 TP2, vision → n2 ==="
alert "🔬 Prime A/B: parking Qwen roommate, 0731 stays. Then teb 69."
QWEN38_PORT=8100 bash "$HOME/scripts/dgx/qwen38-27b.sh" stop-replica || true
bash "$HOME/scripts/dgx/qwen38-27b.sh" stop || true
VISION="$HOME/Documents/projects/ds4f-qwen-vision-sidecar"
if [[ -x "$VISION/stop-qwen-vision-tp1.sh" ]]; then
  QWEN_VISION_STOP_SCOPE=local bash "$VISION/stop-qwen-vision-tp1.sh" || true
fi
python3 "$HOME/.hermes/scripts/wire-spark-chat.py" prime
systemctl --user restart hermes-gateway-orchestrator hermes-gateway-dobby \
  hermes-gateway-light hermes-gateway-smeagle || true
if [[ -x "$HOME/.hermes/scripts/ensure-qwen-vision.sh" ]]; then
  QWEN_VISION_WAIT_SECS=300 QWEN_VISION_FORCE=1 \
    QWEN_VISION_BACKEND_HOST="${N2_IP}" \
    bash "$HOME/.hermes/scripts/ensure-qwen-vision.sh" || echo "WARN vision n2"
fi
python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
p = Path.home() / ".local/state/hermes/spark-stack.json"
p.write_text(json.dumps({
    "desired": "prime",
    "detected": "prime",
    "phase": "idle",
    "message": "Prime A/B — 0731 kept, Qwen parked, vision n2",
    "updated_at": datetime.now(timezone.utc).isoformat(),
}, indent=2) + "\n")
PY

up http://127.0.0.1:8888/v1/models || { echo "0731 died after roommate stop"; exit 3; }
echo "0731 still up after Qwen park"
# unique-prose smoke speed (same prompt as Dream live bench)
python3 - <<'PY'
import json, time, urllib.request
url = "http://127.0.0.1:8888/v1/chat/completions"
prompt = (
    "Write a 500-word technical explanation of why unified memory on NVIDIA GB10 "
    "changes KV-cache planning versus discrete VRAM. Use concrete numbers, no lists of "
    "questions, no code fences. Start with the sentence: UNIFIED_MEM_BEGIN"
)
body = json.dumps({
    "model": "deepseek-v4-flash-0731",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 256, "temperature": 0, "stream": True,
    "stream_options": {"include_usage": True},
    "chat_template_kwargs": {"thinking": False, "enable_thinking": False},
    "enable_thinking": False,
}).encode()
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
t0 = time.perf_counter(); first = None; usage = {}
with urllib.request.urlopen(req, timeout=180) as resp:
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
        except Exception:
            continue
        if first is None and chunk.get("choices"):
            d = chunk["choices"][0].get("delta") or {}
            if d.get("content"):
                first = time.perf_counter()
        if chunk.get("usage"):
            usage = chunk["usage"]
out = int(usage.get("completion_tokens") or 0)
ttft = (first - t0) if first else 0
gen = time.perf_counter() - (first or t0)
print(f"prime-0731 unique: {out/gen if gen else 0:.1f} tok/s  ttft={ttft:.3f}s  out={out}")
PY

run_teb "prime-0731-tp2" "http://127.0.0.1:8888" "deepseek-v4-flash-0731"

echo "=== 2) Exclusive Qwen GGUF on n2 (park 0731 TP2) ==="
alert "🔬 Parking 0731 for solo Qwen n2 teb 69. Dream restore after."
STOP="$HOME/Documents/projects/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark/stop-deepseek-v4-flash-dspark.sh"
bash "$STOP" || true
docker ps -aq --filter name=deepseek 2>/dev/null | xargs -r docker rm -f || true
# same spec as Dream roommate; more ctx because the node is empty
QWEN38_PORT=8100 QWEN38_CTX=131072 QWEN38_PARALLEL=1 QWEN38_CACHE=q4_0 \
  QWEN38_BATCH=4096 QWEN38_UBATCH=1024 \
  QWEN38_SPEC='--spec-type draft-mtp,ngram-mod,ngram-simple --spec-draft-n-max 3 --spec-draft-p-min 0.4' \
  bash "$HOME/scripts/dgx/qwen38-27b.sh" start-n2
for i in $(seq 1 60); do
  if up "http://${N2_IP}:8100/v1/models"; then break; fi
  sleep 5
done
up "http://${N2_IP}:8100/v1/models" || { echo "solo Qwen n2 did not come up"; exit 4; }
curl -sf --max-time 5 "http://${N2_IP}:8100/v1/models" || true
python3 - <<PY
import json, time, urllib.request
url = "http://${N2_IP}:8100/v1/chat/completions"
prompt = (
    "Write a 500-word technical explanation of why unified memory on NVIDIA GB10 "
    "changes KV-cache planning versus discrete VRAM. Use concrete numbers, no lists of "
    "questions, no code fences. Start with the sentence: UNIFIED_MEM_BEGIN"
)
body = json.dumps({
    "model": "Qwen3.8-27B",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 256, "temperature": 0, "stream": True,
    "stream_options": {"include_usage": True},
    "enable_thinking": False,
    "chat_template_kwargs": {"thinking": False, "enable_thinking": False},
}).encode()
req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
t0 = time.perf_counter(); first = None; usage = {}
with urllib.request.urlopen(req, timeout=180) as resp:
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
        except Exception:
            continue
        if first is None and chunk.get("choices"):
            d = chunk["choices"][0].get("delta") or {}
            if d.get("content"):
                first = time.perf_counter()
        if chunk.get("usage"):
            usage = chunk["usage"]
out = int(usage.get("completion_tokens") or 0)
ttft = (first - t0) if first else 0
gen = time.perf_counter() - (first or t0)
print(f"solo-qwen unique: {out/gen if gen else 0:.1f} tok/s  ttft={ttft:.3f}s  out={out}")
PY

run_teb "solo-qwen38-gguf-n2" "http://${N2_IP}:8100" "Qwen3.8-27B"

echo "=== 3) Restore Dream ==="
alert "🔬 A/B done — restoring Dream (0731 + n1 vision + n2 Qwen)."
bash "$HOME/scripts/dgx/spark-stack.sh" dream

echo "ALL_DONE"
ls -lt "$OUT/2026/08" | head
