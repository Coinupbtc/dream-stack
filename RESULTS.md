# Measured scores (2026-08-16)

tool-eval-bench v2.5.1.dev29+g573a3ec70 · 69 scenarios · seed 42 · thinking off · 69/69 · error 0

| Occupancy | Score | Pass / partial / fail | Wall |
|-----------|------:|----------------------:|-----:|
| Dream 0731 TP2 | 87 | 56 / 8 / 5 | 8.1 min |
| Prime 0731 (Qwen parked) | 85 | 55 / 7 / 7 | 8.6 min |
| Dream Qwen GGUF | 90 | 58 / 8 / 3 | 18.0 min |
| Solo Qwen n2 | 90 | 58 / 8 / 3 | 16.3 min |
| **Baton :8877** | **91** | **59 / 8 / 2** | **15.0 min** |

91 is the **suite** score, not 100% of every prompt. Baton still fails TC-03 and TC-61.

Point any OpenAI client at `http://127.0.0.1:8877/v1` model `dream-baton`. No orch/Kanban tags required.
