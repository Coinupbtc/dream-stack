#!/usr/bin/env python3
"""Two tweet cards with exact measured numbers (Pillow)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Write next to this file so a clone can regenerate cards (no house path).
OUT = Path(__file__).resolve().parent / "tweet-cards"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = (11, 18, 32)
INK = (232, 238, 247)
MUTED = (154, 168, 188)
GOLD = (240, 180, 41)
TEAL = (61, 204, 199)
CARD = (20, 28, 43)
LINE = (42, 53, 72)
OK = (127, 217, 154)
RED = (240, 113, 120)

W, H = 1600, 900


def font(size, bold=False):
    for p in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ):
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded(draw, xy, r, fill, outline=None):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=2 if outline else 0)


def card1() -> Path:
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.text((40, 28), "DREAM STACK  ·  2× DGX Spark GB10", font=font(28, True), fill=TEAL)
    d.text((40, 72), "tool-eval-bench 69   seed 42   thinking OFF   69 completed   infra error 0", font=font(20), fill=MUTED)
    d.text((40, 104), "v2.5.1.dev29+g573a3ec70   occupancy + baton by coinupbtc", font=font(18), fill=MUTED)

    headers = ["Occupancy", "Score", "P / part / F", "Points", "Wall", "Unique t/s", "Med turn"]
    rows = [
        ["0731 Dream (TP2+roommate)", "87", "56 / 8 / 5", "120/138", "8.1 min", "39.6", "2.1 s"],
        ["0731 Prime (Qwen parked)", "85", "55 / 7 / 7", "117/138", "8.6 min", "42.7", "2.2 s"],
        ["Qwen Dream leftover 88k", "90", "58 / 8 / 3", "124/138", "18.0 min", "18.4", "4.8 s"],
        ["Qwen solo n2 131k", "90", "58 / 8 / 3", "124/138", "16.3 min", "22.0", "4.2 s"],
        ["BATON :8877 (fusion)", "91", "59 / 8 / 2", "126/138", "15.0 min", "19.2*", "4.2 s"],
    ]
    xs = [44, 520, 660, 880, 1050, 1230, 1420]
    y = 160
    for i, h in enumerate(headers):
        d.text((xs[i], y), h, font=font(16, True), fill=GOLD)
    d.line((40, 190, 1560, 190), fill=LINE, width=2)
    for r, row in enumerate(rows):
        yy = 210 + r * 58
        if r == 4:
            rounded(d, (36, yy - 10, 1564, yy + 44), 8, (26, 40, 48), TEAL)
        for i, cell in enumerate(row):
            col = GOLD if r == 4 and i == 1 else INK
            d.text((xs[i], yy), cell, font=font(20 if i else 18, i in (0, 1)), fill=col)

    d.text((40, 520), "Suite score  (points / 138 × 100)", font=font(18), fill=MUTED)
    bars = [
        ("0731 Dream", 87, (107, 140, 206)),
        ("0731 Prime", 85, (74, 106, 163)),
        ("Qwen Dream", 90, TEAL),
        ("Qwen solo", 90, (42, 163, 156)),
        ("BATON", 91, GOLD),
    ]
    for i, (name, sc, c) in enumerate(bars):
        yy = 560 + i * 48
        d.text((40, yy), name, font=font(16), fill=MUTED)
        bw = int(1040 * (sc / 100))
        rounded(d, (280, yy + 2, 280 + bw, yy + 26), 6, c)
        d.text((290 + bw, yy), str(sc), font=font(18, True), fill=INK)

    d.text((40, 860), "*Baton default unique 19.2 tok/s (Qwen path). Long prompts flip to 0731 ~40. 91 is the suite, not every prompt.",
           font=font(15), fill=MUTED)
    p = OUT / "01-teb69-scoreboard.png"
    im.save(p, "PNG")
    return p


def card2() -> Path:
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.text((40, 28), "SPEED  ·  TAX  ·  COMPLEMENTARY FAILS", font=font(28, True), fill=TEAL)
    d.text((40, 72), "2026-08-16   thinking off   unique 256-tok prose   teb-69 walls are separate", font=font(18), fill=MUTED)

    rounded(d, (36, 120, 780, 500), 12, CARD, LINE)
    d.text((56, 136), "Unique decode (tok/s)", font=font(20, True), fill=GOLD)
    speeds = [
        ("0731 Dream", 39.6, (107, 140, 206)),
        ("0731 Prime no roommate", 42.7, GOLD),
        ("Qwen Dream leftover", 18.4, TEAL),
        ("Qwen solo n2", 22.0, (42, 163, 156)),
        ("Qwen file-copy MTP3 (house)", 63.6, OK),
        ("Baton default (this box)", 19.2, GOLD),
        ("Qwen SGLang exclusive (not this box)", 34.0, MUTED),
    ]
    for i, (name, v, c) in enumerate(speeds):
        yy = 176 + i * 44
        d.text((56, yy), name, font=font(15), fill=MUTED)
        bw = int(360 * (v / 64))
        rounded(d, (400, yy + 2, 400 + bw, yy + 24), 5, c)
        d.text((410 + bw, yy), f"{v}", font=font(16, True), fill=INK)

    rounded(d, (820, 120, 1564, 500), 12, CARD, LINE)
    d.text((840, 136), "teb-69 wall  ·  median turn  ·  tokens", font=font(20, True), fill=GOLD)
    walls = [
        "0731 Dream     8.1 min   2.1 s    488.1 s    312,522 tok",
        "0731 Prime     8.6 min   2.2 s    515.5 s    297,644 tok",
        "Qwen Dream    18.0 min   4.8 s   1079.4 s    244,856 tok",
        "Qwen solo     16.3 min   4.2 s    980.6 s    score still 90",
        "BATON         15.0 min   4.2 s    902.8 s    374,851 tok",
    ]
    for i, line in enumerate(walls):
        col = GOLD if line.startswith("BATON") else INK
        d.text((840, 190 + i * 52), line, font=font(17), fill=col)

    rounded(d, (36, 520, 780, 868), 12, CARD, LINE)
    d.text((56, 536), "Roommate tax (same 0731 TP2 process)", font=font(20, True), fill=GOLD)
    tax = [
        "0731 unique  39.6 → 42.7 tok/s when Qwen leaves  (+8%)",
        "0731 teb     87 → 85  (not smarter; +2 safety fails)",
        "Qwen unique  18.4 → 22.0 tok/s on a whole node   (+20%)",
        "Qwen teb     90 → 90  identical 58 / 8 / 3",
        "Keep-warm TTFT  idle 16.1s → 3rd hit 0.38s",
        "Baton default 19.2 (Qwen); long/required → 0731 ~40",
    ]
    for i, t in enumerate(tax):
        d.text((56, 578 + i * 40), t, font=font(15), fill=INK)

    rounded(d, (820, 520, 1564, 868), 12, CARD, LINE)
    d.text((840, 536), "Fails do not overlap  →  baton", font=font(20, True), fill=GOLD)
    d.text((840, 580), "0731 0/2   Qwen better", font=font(16, True), fill=RED)
    d.text((840, 610), "TC-34 inject · 42 extra-params · 51 plan", font=font(15), fill=INK)
    d.text((840, 638), "TC-57 search-inject · 68 schema tools", font=font(15), fill=INK)
    d.text((840, 682), "Qwen 0/2   0731 better", font=font(16, True), fill=OK)
    d.text((840, 712), "TC-03 lookup→email · 45 tool_choice=required", font=font(15), fill=INK)
    d.text((840, 740), "TC-61 async poll / run_code", font=font(15), fill=INK)
    d.text((840, 786), "Oracle item-max ~95.7     live baton 91", font=font(17, True), fill=TEAL)
    d.text((840, 822), "Still miss TC-03 and TC-61 on the live baton.", font=font(14), fill=MUTED)

    p = OUT / "02-speed-tax-fails.png"
    im.save(p, "PNG")
    return p


if __name__ == "__main__":
    print(card1())
    print(card2())
