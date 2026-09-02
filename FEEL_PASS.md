## Feel-pass (Dream stack · 2026-08-19)

1. Cold open: occupancy table and **measured** teb-69 scores before any flag diary. This repo is **supporting** occupancy, not the public hero ([miaai35-tune](https://github.com/Coinupbtc/miaai35-tune)). Screenshot is the scoreboard (Baton vs 0731 vs Qwen).
2. Primary path: `./setup.sh` copies `env.example`, syntax-checks, prints laptop-vs-cluster next steps. `./setup.sh --up` is the two-Spark path and refuses if `:8888` is not 0731.
3. Break / empty: no `.env` → copy + “edit N2_IP / SPARK2 / GGUF”. 0731 down → `up.sh` exits 2 with Mia start knobs. Never pretends a laptop can load 0731.
4. Loading: roommate + baton take minutes; `scripts/status.sh` / `smoke.sh` are the success surface (`UP 0731 / Qwen / baton`).
5. Would a stranger keep this? **yes if they already run MiaAI 0731 TP=2 on two Sparks.** Everyone else still sees proof (scores + flags) and a one-command no-GPU setup. MiaAI/Anemll credit for TP=2 dual-node serving is above the fold.

Evidence: `docs/screenshots/hero.png` · `RESULTS.md` · `./setup.sh` (no `--up`).
