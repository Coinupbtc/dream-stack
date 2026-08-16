# Dream stack — 0731 + Qwen 3.8 + vision on 2× DGX Spark

**What it is:** a measured **occupancy recipe**, not a new engine.

You already run [MiaAI DeepSeek-V4-Flash-0731 DSpark TP=2](https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark). Dream keeps that chat brain and **roommates** two more services on the leftover UMA:

| Piece | Where | Endpoint | Window |
|-------|--------|----------|--------|
| **DeepSeek-V4-Flash-0731** TP=2 (Mia / Anemll) | both Sparks | `:8888` | **348k** (`max_model_len=347392`) |
| **Qwen3.8-27B** Unsloth UD-Q4_K_XL + MTP3 + ngram | node2 only | `192.168.100.11:8100` | **88k** |
| **Qwen3-VL-4B** house vision | **node1** only | `:8891` (proxy `:8890`) | 8k |

NVFP4 Qwen **does not** fit next to 0731 TP2. The roommate has to be the **GGUF**. Pictures stay on node1. Do not idle-park them.

This is **not** “split one model per Spark.” 0731 still owns both boxes. Qwen sits in node2 leftover. 0731 decode tax from the roommate is **~4%**.

## Numbers we already measured (2026-08-14 … 2026-08-16)

Thinking **off** unless noted.

### Speed

| Engine | Unique prose | Copy / edit | TTFT |
|--------|-------------:|------------:|------|
| **0731** Dream TP2 348k MTP=5 | **35.6–39.6 tok/s** | 87 tok/s (short repeat) | warm **0.3 s**; idle-cold **16.1 s** |
| **0731** same prompt, no Qwen roommate | 36.9 tok/s | — | — |
| **Qwen GGUF** baseline | 11.1 | 11.3 | ~0.4 s |
| **Qwen + MTP3 + ngram** (live) | **19.0** | **63.6** | 0.63 / 0.99 s |

Keep-warm: 3rd identical 0731 hit **0.38 s** (timer every 10m).

Prime (0731 TP2, no Qwen) short forced-decode c=1 is **62–83 tok/s**. Dream unique-prose is the same class as Prime unique-prose. Do not compare 39 tok/s essays to 83 tok/s `ignore_eos` cells.

### tool-eval-bench (69, seed 42, thinking off) — 2026-08-16

Same instrument Mia used for Qwen 3.8 ([@SeraAndroid](https://github.com/SeraphimSerapis/tool-eval-bench) `v2.5.1.dev29+g573a3ec70`). Sequential on the **live Dream occupancy**. Error rate **0**. Completion **69/69**.

| Brain | Score | Rating | Pass / partial / fail | Points | Wall | Median turn |
|-------|------:|--------|----------------------:|-------:|-----:|------------:|
| **0731 Dream** `:8888` 348k | **87** | ★★★★ Good | **56 / 8 / 5** | 120/138 | **8.1 min** | **2.1 s** |
| **0731 Prime** (Qwen parked) | **85** | ★★★★ Good | **55 / 7 / 7** | 117/138 | 8.6 min | 2.2 s |
| **Qwen Dream** `:8100` 88k | **90** | ★★★★★ Excellent | **58 / 8 / 3** | 124/138 | **18.0 min** | 4.8 s |
| **Qwen solo n2** (0731 down) | **90** | ★★★★★ Excellent | **58 / 8 / 3** | 124/138 | 16.3 min | 4.2 s |

0731 weakest: Safety 73% (3 safety-critical: TC-34, TC-42, TC-57) and Planning 50%.  
Qwen weakest: Tool Selection 67% (TC-03, TC-45, TC-61). Structured Output **12/12**.

Reports: `runs/2026/08/*--dream-0731-348k.md` and `*--dream-qwen38-gguf-88k.md`.

### Occupancy A/B (same seed 42, thinking off, 2026-08-16)

0731 stayed the **same TP2 process** for Prime (roommate parked, vision moved to n2). Solo Qwen = 0731 parked, GGUF MTP3 on n2 with **131k** ctx (Dream was 88k leftover).

| Occupancy | Score | Pass/part/fail | Wall | Unique tok/s | Median turn |
|-----------|------:|----------------|-----:|-------------:|------------:|
| 0731 **Dream** (TP2 + Qwen leftover) | **87** | 56 / 8 / 5 | 8.1 min | 39.6 | 2.1 s |
| 0731 **Prime** (TP2, no Qwen) | **85** | 55 / 7 / 7 | 8.6 min | **42.7** | 2.2 s |
| Qwen **Dream** roommate 88k | **90** | 58 / 8 / 3 | 18.0 min | 18.4 | 4.8 s |
| Qwen **solo n2** 131k | **90** | 58 / 8 / 3 | **16.3 min** | **22.0** | 4.2 s |

Roommate does **not** buy 0731 a better tool score (87 vs 85 is noise / safety jitter). It costs ~**8%** unique decode. Solo Qwen is the **same 90**, ~**20%** faster unique, ~10% less wall. Still GGUF — not SGLang 34–38.

Exclusive SGLang Qwen **34–38 tok/s** still needs a **whole Spark**. It evicts 0731 TP2. Dream stays on GGUF **19**.

## How to stand it up

Needs the Mia 0731 TP2 recipe already healthy on CX7.

```bash
# one occupant of both UMAs
bash ~/scripts/dgx/spark-stack.sh dream

# repair after a fabric flicker (does not bounce 0731 if :8888 is up)
bash ~/scripts/dgx/spark-stack.sh heal
```

Wire (same five Hermes profiles; no sixth gateway). Chat is **one URL**:

```text
orch / light / dobby / smeagle / desktop  →  baton :8877
vision                                     →  4B on node1
```

No orch/Kanban tags. Baton picks Qwen or 0731.

```text
http://127.0.0.1:8877/v1   model: dream-baton
```

Default Qwen; 0731 only when `tool_choice=required` or the prompt looks like async/run-script. Suite score **91** (not 100% of every prompt).

```bash
python3 ~/.hermes/scripts/wire-spark-chat.py dream
systemctl --user enable --now dream-baton.service
```

Laws:

1. Pin vision **down** until `:8888` answers, then start n1 4B and **leave it up**.
2. Qwen is **`192.168.100.11:8100`**, never `127.0.0.1:8100` on node1.
3. Do not start NVFP4 Qwen beside 0731.

## Public bench (same instrument as Mia’s Qwen 3.8 post)

```bash
uv tool install git+https://github.com/SeraphimSerapis/tool-eval-bench.git

# 0731
TOOL_EVAL_BASE_URL=http://127.0.0.1:8888 TOOL_EVAL_MODEL=deepseek-v4-flash-0731 \
  tool-eval-bench run --seed 42 --label "dream-0731-348k"

# Qwen roommate (CX7)
TOOL_EVAL_BASE_URL=http://192.168.100.11:8100 TOOL_EVAL_MODEL=Qwen3.8-27B \
  tool-eval-bench run --seed 42 --label "dream-qwen38-gguf-88k"
```

`--short` is 15 scenarios (smoke). Full suite is **69**. Publish score, rating, pass/partial/fail, wall time, completion rate. Compare only same seed + same commit of tool-eval-bench.

Optional speed add-on (do not mix into the quality score):

```bash
tool-eval-bench bench --perf-legacy-only --pp 2048 --tg 128 \
  --base-url http://127.0.0.1:8888 --model deepseek-v4-flash-0731
```

## Credit

- 0731 TP2 engine: [MiaAI-Lab / Anemll DSpark](https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark)
- Qwen 3.8: [Qwen](https://huggingface.co/Qwen) / Unsloth GGUF
- Public tool-call eval: [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench)
- Hardware: 2× NVIDIA DGX Spark (GB10), CX7 ~0.4 ms
