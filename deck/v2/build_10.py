#!/usr/bin/env python3
"""Slide 10 - Who am I. Option A, "the proof stack", on the owner's pick (2026-10-01).

Top left, the founder: photo, name, role, LinkedIn QR and the two experience lines the
owner approved. Top right, three rows that prove the headline one part each. Under both,
the logo band: education, work and institutions, as the owner listed them.

No official file for any of the eight logos could be had from this sandbox (only npm is
reachable, and no open icon set carries them), so each sits in its own named layer
(logo-*) as a grey name badge, the deck's fallback for a missing mark. Drop the official
file into that layer in Figma, or send it and it is inlined byte-for-byte. Never redrawn.

Name, photo and QR are dashed slots: a placeholder that reads like real copy is how an
invented founder reaches a room.

SVG text does not wrap, so every string is measured against Geist and the build stops if
one overruns its box."""
from kit import *
import pathlib
from PIL import ImageFont

GREEN, GREEN_BG = "#0F7B3F", "#E9F3EC"
AMB_BG, CHIP_BG = "#F6EEE3", "#F0F0F0"
SLOT_BG, SLOT_INK = "#F2F2F2", "#8F8F8F"

FONT = pathlib.Path.home() / ".fonts" / "Geist-Variable.ttf"
if not FONT.exists():
    FONT = pathlib.Path(__file__).resolve().parents[2] / "static" / "fonts" / "Geist-Variable.ttf"
_cache = {}
def width(text, size, weight=400, ls=0):
    """Rendered width of a string in Geist, letter-spacing included."""
    key = (size, weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONT), size)
        f.set_variation_by_axes([weight])
        _cache[key] = f
    t = text.replace("&amp;", "&")
    return _cache[key].getlength(t) + ls * max(len(t) - 1, 0)

def fit(text, size, weight, box, ls=0):
    w = width(text, size, weight, ls)
    assert w <= box, f"overruns by {w - box:.1f}px: {text!r}"
    return w

def wrap(text, size, weight, box):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if width(trial, size, weight) <= box: cur = trial
        else: lines.append(cur); cur = word
    lines.append(cur)
    return lines

s = Slide()
HEAD = "Seen the gap. Built the product. Mapped the buyers."
fit(HEAD, 66, 600, W - 2 * M, ls=-2)
s.header("08 · WHO AM I", HEAD, "One founder. Every line on the right is already done.")

def slot(x, y, w, h, lines, size, idn):
    """A dashed placeholder the founder fills in. Visibly unfinished on purpose."""
    s.g(idn)
    s.R(x, y, w, h, SLOT_BG, 10, f' stroke="{INK}" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="6 5"')
    lh = size * 1.25
    y0 = y + h / 2 - lh * (len(lines) - 1) / 2 + size * 0.36
    for i, ln in enumerate(lines):
        fit(ln, size, 500, w - 12)
        s.T(x + w / 2, round(y0 + i * lh, 1), ln, size, 500, SLOT_INK, anchor="middle")
    s.end()

def chip(x, y, text, kind):
    """A status tag, left edge at x, top at y, 30 tall. Returns its width."""
    fg, bg = {"live": (GREEN, GREEN_BG), "grey": (MUT, CHIP_BG), "amber": (AMB, AMB_BG)}[kind]
    dot = 16 if kind == "live" else 0
    w = round(width(text, 14, 500) + 22 + dot)
    s.R(x, y, w, 30, bg, 7)
    if dot: s.raw(f'<circle cx="{x + 15}" cy="{y + 15}" r="4" fill="{GREEN}"/>')
    s.T(x + 11 + dot, y + 20, text, 14, 500, fg)
    return w

def tick(cx, cy):
    s.raw(f'<circle cx="{cx}" cy="{cy}" r="11" fill="{GREEN_BG}"/>')
    s.raw(f'<path d="M{cx - 4.5} {cy + 0.3}l3 3 6-6.4" stroke="{GREEN}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

TOP, CARD_H = 318, 358

# ---------------------------------------------------------------- the founder
FX, FW, PAD = M, 520, 32
s.g("founder")
s.card(FX, TOP, FW, CARD_H)
slot(FX + PAD, TOP + PAD, 120, 120, ["[ Photo ]"], 16, "photo")
NX = FX + PAD + 120 + 20
slot(NX, TOP + PAD + 14, 210, 48, ["[ Full name ]"], 24, "name")
s.T(NX, TOP + PAD + 96, "Founder, SQRlane", 19, 400, MUT)
slot(FX + FW - PAD - 84, TOP + PAD, 84, 84, ["[ LinkedIn", "QR ]"], 12, "linkedin-qr")
assert NX + 210 + 12 <= FX + FW - PAD - 84, "name slot runs into the QR"

HR = TOP + PAD + 120 + 26
s.rule(HR, 0.1, FX + PAD, FW - 2 * PAD)
s.T(FX + PAD, HR + 36, "EXPERIENCE", 13, 500, MUT, ls=2.4, mono=True)
EXPERIENCE = ["Shaped the investment thesis of a $170M VC fund.",
              "Advised Fortune 500 CEOs on restructuring liabilities above $100M."]
y = HR + 72
for item in EXPERIENCE:
    for ln in wrap(item, 19, 400, FW - 2 * PAD):
        s.T(FX + PAD, y, ln, 19, 400)
        y += 26
    y += 10
assert y - 10 - 26 + 8 <= TOP + CARD_H - 20, f"experience runs past the card foot ({y})"
s.end()

# ---------------------------------------------------------------- the proofs
PX = FX + FW + 24
PW = W - M - PX
ROW = CARD_H / 3
LAB_W = 260
CX0, CX1 = PX + 36 + LAB_W, PX + PW - 36            # content column
PROOFS = [
    ("proof-gap", "SEEN THE GAP", "Nobody owns the step between. That is my bet.",
     "Risk tools stop at the alert. Execution tools start after the decision.", []),
    ("proof-built", "BUILT THE PRODUCT", "SQRlane runs today, end to end.",
     "16 agents, 60 live sources, any TMS by export or API. You approve every change.",
     [("14 live", "live"), ("Planner scripted", "grey"), ("TMS link demo", "grey")]),
    ("proof-buyers", "MAPPED THE BUYERS", "Mid-size forwarders in DACH and Benelux.",
     "An ICP list of forwarders, enriched in Apollo. Events lined up for outreach.",
     [("To confirm", "amber")]),
]
s.g("proofs")
s.card(PX, TOP, PW, CARD_H)
for i, (idn, lab, claim, ev, chips) in enumerate(PROOFS):
    top = TOP + i * ROW
    s.g(idn)
    if i: s.rule(round(top), 0.1, PX + 36, PW - 72)
    tick(PX + 36 + 11, round(top + 42))
    fit(lab, 13, 500, LAB_W - 40, ls=1.44)
    s.T(PX + 36 + 34, round(top + 47), lab, 13, 500, INK, ls=2.4, mono=True)
    base = round(top + 52)
    cw = fit(claim, 28, 600, CX1 - CX0, ls=-0.5)
    s.T(CX0, base, claim, 28, 600, ls=-0.5)
    fit(ev, 19, 400, CX1 - CX0)
    s.T(CX0, base + 34, ev, 19, 400, MUT)
    # status chips sit right-aligned on the claim's line
    widths = [round(width(t, 14, 500) + 22 + (16 if k == "live" else 0)) for t, k in chips]
    x = CX1 - sum(widths) - 8 * max(len(widths) - 1, 0)
    assert not chips or x >= CX0 + cw + 24, f"{idn}: chips run into the claim"
    for (t, k), w in zip(chips, widths):
        chip(x, base - 23, t, k)
        x += w + 8
    s.end()
s.end()

# ---------------------------------------------------------------- the logo band
BAND_Y, BAND_H = TOP + CARD_H + 24, 156
GROUPS = [("EDUCATION", ["Nova SBE", "CEMS MIM"]),
          ("WORK", ["Alvarez &amp; Marsal", "SCAILE", "Biome VC"]),
          ("INSTITUTIONS", ["UN Foundation", "TUM|Manage and More", "Hack-Nation"])]
CELL_W, CELL_H, GAP, SIDE = 184, 64, 12, 32
s.g("logos")
s.card(M, BAND_Y, W - 2 * M, BAND_H)
x = M + 32
for gi, (lab, names) in enumerate(GROUPS):
    if gi:
        s.R(x + SIDE, BAND_Y + 24, 1, BAND_H - 48, INK, extra=' fill-opacity="0.1"')
        x += 2 * SIDE + 1
    s.T(x, BAND_Y + 40, lab, 13, 500, MUT, ls=2.4, mono=True)
    for name in names:
        slug = "logo-" + name.lower().replace("&amp;", "and").replace("|", " ").replace(" ", "-")
        s.g(slug)
        s.R(x, BAND_Y + 60, CELL_W, CELL_H, "#F5F5F5", 10, f' stroke="{INK}" stroke-opacity="0.08"')
        # "|" is a chosen line break, so a name splits where it reads, not where it runs out
        lines = name.split("|") if "|" in name else [name] if width(name, 16, 600) <= CELL_W - 24 else wrap(name, 16, 600, CELL_W - 24)
        lh = 20
        y0 = BAND_Y + 60 + CELL_H / 2 - lh * (len(lines) - 1) / 2 + 6
        for j, ln in enumerate(lines):
            fit(ln, 16, 600, CELL_W - 24)
            s.T(x + CELL_W / 2, round(y0 + j * lh, 1), ln, 16, 600, "#3A3A3A", anchor="middle")
        s.end()
        x += CELL_W + GAP
    x -= GAP
assert x <= W - M - 32, f"logo band overruns by {x - (W - M - 32)}px"
s.end()

# ---------------------------------------------------------------- the line they repeat
CLOSE = "I’ve helped shape a fund’s thesis. This is the company I’d back."
fit(CLOSE, 34, 600, W - 2 * M, ls=-0.8)
s.g("closing")
s.T(M, 936, CLOSE, 34, 600, ls=-0.8)
s.end()

s.footer(10)
s.write("slide-10-who-am-i.svg")
