# Measured scores (2026-08-16)

Instrument: [tool-eval-bench](https://github.com/SeraphimSerapis/tool-eval-bench) `v2.5.1.dev29+g573a3ec70`
Suite: **69** scenarios · seed **42** · thinking **off** · completion **69/69** · error **0**

Live occupancy while scoring Dream rows: 0731 TP2 `:8888` `max_model_len=347392` + Qwen GGUF n2 `:8100` `n_ctx=88064` + 4B vision n1.

**Live roommate after those runs (2026-08-16 night):** Qwen `n_ctx=104192` (requested 104000). Same GGUF + MTP3. teb numbers above are the 88k occupancy.

| Occupancy | Score | Pass / partial / fail | Wall | Unique tok/s |
|-----------|------:|----------------------:|-----:|-------------:|
| Dream 0731 TP2 | 87 | 56 / 8 / 5 | 8.1 min | 39.6 |
| Prime 0731 (same 0731 process, Qwen parked) | 85 | 55 / 7 / 7 | 8.6 min | 42.7 |
| Dream Qwen GGUF 88k | 90 | 58 / 8 / 3 | 18.0 min | 18.4 |
| Solo Qwen n2 131k (0731 parked) | 90 | 58 / 8 / 3 | 16.3 min | 22.0 |
| **Baton :8877** | **91** | **59 / 8 / 2** | **15.0 min** | 19.2 (Qwen default) |

91 is the **suite** score, not 100% of every prompt. Baton still fails **TC-03** and **TC-61**. It flipped TC-45 (`tool_choice=required` → 0731).

0731 Dream fails (do not overlap Qwen): TC-34, 42, 51, 57, 68.
Qwen Dream fails: TC-03, 45, 61.

Roommate tax on 0731 unique decode is ~**8%** (39.6 vs 42.7). Quality did not go up when the roommate was parked.

Point any OpenAI client at `http://127.0.0.1:8877/v1` model `dream-baton`.

Reproduce: `bash scripts/run-teb.sh 69 baton` (and `0731` / `qwen`). Same seed + thinking-off or do not compare.
