# Measured scores (2026-08-16)

Instrument: [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench) `v2.5.1.dev29+g573a3ec70`
Suite: **69** scenarios · seed **42** · thinking **off** · completion **69/69** · error **0**

Live occupancy while scoring Dream rows: 0731 TP2 `:8888` `max_model_len=347392` + Qwen GGUF n2 `:8100` `n_ctx=88064` + 4B vision n1.

**Live roommate (2026-08-17 night):** Qwen `n_ctx=116224`, **MTP4** (unique-256 **20.1** tok/s vs MTP3 **18.4**). 124k OOM-killed n2. First baton teb (91) was 88k occupancy.

**2026-08-17 rematch** (same seed 42, thinking off, 69/69): live 116k + n2 traffic cop. MTP5 unique-256 **20.2** (wash vs MTP4 **20.1**). 0731 `MAX_NUM_SEQS=4` / `MAX_NUM_BATCHED_TOKENS=16384` **did not boot** while Qwen held n2 (free 89.71G < 90.05G; later KV 3.91G < 8.14G). Reverted to **6 / 8192**. Do not retry those 0731 knobs without parking Qwen first.

| Occupancy | Score | Pass / partial / fail | Wall | Unique tok/s |
|-----------|------:|----------------------:|-----:|-------------:|
| Dream 0731 TP2 | 87 | 56 / 8 / 5 | 8.1 min | 39.6 |
| Prime 0731 (same 0731 process, Qwen parked) | 85 | 55 / 7 / 7 | 8.6 min | 42.7 |
| Dream Qwen GGUF 88k | 90 | 58 / 8 / 3 | 18.0 min | 18.4 |
| Solo Qwen n2 131k (0731 parked) | 90 | 58 / 8 / 3 | 16.3 min | 22.0 |
| Baton :8877 (first, 88k) | 91 | 59 / 8 / 2 | 15.0 min | 19.2 (Qwen default) |
| Baton rematch (116k + cop) | 88 | 57 / 7 / 5 | 16.4 min | — |
| **Baton live** (notify/script/research) | **94** | **61 / 8 / 0** | **13.9 min** | — |
| Baton + draft/CC handoff | 91 | 59 / 8 / 2 | 16.1 min | — |

**Best full 69: 94** (run `2026-08-18T01-09-23.332449Z_72cf1a03`). **0 fails.** 130/138. Median **3.8s**.

**This rematch: 91** (run `2026-08-18T02-34-54.165263Z_5502bb24`). Draft/CC/role-email handoff: **TC-48 and TC-50 pass**. **TC-03, 45, 61** still pass. Lost **TC-35** (Kelvin) and **TC-68** (extra tools); **TC-60** and **TC-53** back to partial. Same 126/138 as the first 88k baton, different mix.

**Offered / live router is the 94 stack** (notify / script / research). Draft/CC regex was reverted so Telegram, Console, and `origin/main` match the 94 run.

0731 Dream fails (do not overlap Qwen): TC-34, 42, 51, 57, 68.
Qwen Dream fails: TC-03, 45, 61.

Roommate tax on 0731 unique decode is ~**8%** (39.6 vs 42.7). Quality did not go up when the roommate was parked.

**Subset 2026-08-17 (live baton, not a full 69):** general handoffs — implicit notify (`let NAME know`), run-this-script, research/report chains.

| Item | Before (rematch) | After | Wall |
|------|------------------|-------|-----:|
| TC-03 implicit notify | fail | **pass** | 9.2s |
| TC-61 run script / poll | fail | **pass** | 10.3s |
| TC-60 sleeper email | fail | **pass** | 12.6s |
| TC-46 research (5-turn) | partial 44.8s | partial | **33.3s** |
| TC-62 research (6-turn) | partial 70.7s | partial | **32.0s** |

Full 69 on the notify/script/research baton: **94**. Draft/CC rematch: **91** (48+50 pass; 35+68 fail).

Point any OpenAI client at `http://127.0.0.1:8877/v1` model `dream-baton`.

Reproduce: `bash scripts/run-teb.sh 69 baton` (and `0731` / `qwen`). Same seed + thinking-off or do not compare.
