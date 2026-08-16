# Ready to post

Quote: https://x.com/MiaAI_lab/status/2088307594142052486
Instrument: tool-eval-bench @SeraAndroid v2.5.1.dev29+g573a3ec70 · 69 · seed 42 · thinking off · 69/69 · error 0

---

## Tweet 1

Dream stack on 2× DGX Spark — occupancy recipe, not a new engine.

Keep @MiaAI_lab 0731 TP2 as the long brain (348k).
Roommate Qwen 3.8 27B GGUF on node2 leftover + 4B vision on node1.

NVFP4 Qwen will not sit next to 0731. GGUF will.
0731 unique ~36–40 tok/s (roommate tax ~4–8% vs Prime).
Qwen unique 19 tok/s, file copy 64 (MTP3+ngram).

Not a split. 0731 still owns both boxes.

---

## Tweet 2

Same eval Mia used for Qwen 3.8: tool-eval-bench @SeraAndroid · 69 · seed 42 · thinking off.

Dream occupancy (both brains live):

0731 :8888 348k — **87**/100 ★★★★ · 56 pass / 8 partial / 5 fail · **8.1 min** · median turn 2.1s
Qwen GGUF :8100 88k — **90**/100 ★★★★★ · 58 / 8 / 3 · **18.0 min** · median turn 4.8s

Completion 69/69. Infra fails: 0.

Qwen wins the tool pack. 0731 is ~2× wall and much snappier.
Telegram stays on 0731. Kanban talks to Qwen.

0731 dropped 3 safety-critical injection cases (K=73%). Qwen K=88%.

---

## Tweet 3 — A/B (optional, honest)

We parked the roommate (Prime, same 0731 TP2 process): 0731 **87 → 85**. Not smarter. Unique 39.6 → 42.7 tok/s.

We gave Qwen the whole node2 (0731 down): Qwen **90 → 90**, same 58/8/3. Unique 18.4 → 22.

The 90 vs 87 gap is the model, not the squeeze.
Fails don’t overlap — a baton (Qwen default, 0731 on tool_choice=required / async) is the score path, not a third engine.

---

Tags: @MiaAI_lab @SeraAndroid @Alibaba_Qwen
