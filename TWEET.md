# Draft tweets — supporting occupancy, not the public hero (miaai35-tune)

0731 TP=2 serving is [MiaAI-Lab / Anemll DSpark](https://github.com/MiaAI-Lab/DeepSeek-v4-Flash-DSpark-2x-DGX-Spark). This repo is leftover Qwen + n1 vision + baton on a live pair.

Images: tweet-cards/01-teb69-scoreboard.png + 02-speed-tax-fails.png

---

## Tweet 1 (card 01)

I run two DGX Sparks as leftover occupancy I call Dream. Public hero is miaai35-tune.

0731 TP=2 serving is MiaAI/Anemll DSpark.
0731 TP2 @ 348k across the pair.
Qwen 3.8 27B GGUF on node2 leftover (88k, MTP3).
4B vision stay-up on node1.
One URL in front: baton :8877. No tags. It picks the brain.

tool-eval-bench 69 · seed 42 · thinking off · 69 completed · 0 infra errors (not a 69/69 pass)

0731 Dream  87  56/8/5  8.1 min  39.6 tok/s
Qwen Dream  90  58/8/3  18.0 min 18.4 tok/s
BATON       91  59/8/2  15.0 min 19.2 tok/s default

NVFP4 Qwen does not fit next to 0731. GGUF does. This is not a 1-model-per-Spark split.

---

## Tweet 2 (card 02)

Same seed, same day, same 0731 process:

Park the roommate: 0731 87→85. Unique 39.6→42.7 (+8%). Speed tax, not quality.
Give Qwen the whole node: 90→90, same 58/8/3. Unique 18.4→22.0 (+20%).

Fails do not overlap.
0731 dies on injection/schema. Qwen dies on implicit chain / tool_choice=required / async.
Baton flipped required (TC-45). Live 91. Still miss 03 and 61.

Keep-warm: idle TTFT 16.1s → 0.38s.

0731 TP=2 serving is MiaAI/Anemll DSpark. This tweet is leftover occupancy (roommate + baton), not the lab hero.

---

Credit line for tweet 1: MiaAI-Lab / Anemll DSpark TP=2. Optional @MiaAI_lab.
