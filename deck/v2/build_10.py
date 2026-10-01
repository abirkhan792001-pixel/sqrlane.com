#!/usr/bin/env python3
"""Slide 10 - Who am I. Option A, "the proof stack", third pass (2026-10-01).

Top left, the founder: photo, name, role, the two experience lines and a LinkedIn link.
Top right, the headline proved in three linked tiles, each with its own picture: the gap
(alert, decide, act, with nobody owning decide), the product (14 live agents, 60 live
sources), the buyers (ICP list, Apollo, events). Under both, one horizontal logo band in
the owner's three groups.

Logos and the photo are the owner's own files (deck/v2/logos/, deck/v2/people/), cropped
and, where they came on white, made transparent - nothing redrawn. A logo whose file has
not arrived is a dashed box in its own named layer (logo-*), for the owner to drop it in.

SVG text does not wrap, so every string is measured against Geist and the build stops if
one overruns its box."""
from kit import *
import base64, pathlib
from PIL import Image, ImageFont

SLOT_BG, SLOT_INK = "#F2F2F2", "#8F8F8F"
HERE = pathlib.Path(__file__).parent
LINKEDIN = "https://www.linkedin.com/in/khan-abir/"

FONT = pathlib.Path.home() / ".fonts" / "Geist-Variable.ttf"
if not FONT.exists():
    FONT = HERE.parents[1] / "static" / "fonts" / "Geist-Variable.ttf"
_cache = {}
def width(text, size, weight=400, ls=0):
    """Rendered width of a string in Geist, letter-spacing included."""
    if (size, weight) not in _cache:
        f = ImageFont.truetype(str(FONT), size)
        f.set_variation_by_axes([weight])
        _cache[size, weight] = f
    t = text.replace("&amp;", "&")
    return _cache[size, weight].getlength(t) + ls * max(len(t) - 1, 0)

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

def slot(x, y, w, h, lines, size, idn):
    """A dashed placeholder. Visibly unfinished on purpose."""
    s.g(idn)
    s.R(x, y, w, h, SLOT_BG, 10, f' stroke="{INK}" stroke-opacity="0.3" stroke-width="1.5" stroke-dasharray="6 5"')
    lh = size * 1.25
    y0 = y + h / 2 - lh * (len(lines) - 1) / 2 + size * 0.36
    for i, ln in enumerate(lines):
        fit(ln, size, 500, w - 12)
        s.T(x + w / 2, round(y0 + i * lh, 1), ln, size, 500, SLOT_INK, anchor="middle")
    s.end()

def embed(path, mime):
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()

s = Slide()
HEAD = "Seen the gap. Built the product. Mapped the buyers."
fit(HEAD, 66, 600, W - 2 * M, ls=-2)
s.header("08 · WHO AM I", HEAD, "One founder. Every proof here is already done.")

TOP, BOTTOM = 318, 880
BAND_H = 150
ROW_B = BOTTOM - BAND_H - 24          # foot of the top row

# ---------------------------------------------------------------- the founder
FX, FW, PAD = M, 760, 32
s.g("founder")
s.card(FX, TOP, FW, ROW_B - TOP)
PW_, PH_ = 260, 324                   # 4:5 portrait, the owner's photo
assert PH_ <= ROW_B - TOP - 2 * PAD, "photo taller than the card"
px, py = FX + PAD, TOP + PAD
s.raw(f'<clipPath id="photo-clip"><rect x="{px}" y="{py}" width="{PW_}" height="{PH_}" rx="12"/></clipPath>')
s.raw(f'<image id="photo" clip-path="url(#photo-clip)" x="{px}" y="{py}" width="{PW_}" height="{PH_}" '
      f'preserveAspectRatio="xMidYMid slice" href="{embed(HERE / "people" / "abir-khan.jpg", "image/jpeg")}"/>')

DX = px + PW_ + 32                    # the details column
DW = FX + FW - PAD - DX
s.T(DX, py + 40, "Abir Khan", 44, 600, ls=-1.2)
s.T(DX, py + 76, "Founder, SQRlane", 20, 400, MUT)
s.rule(py + 104, 0.1, DX, DW)
s.T(DX, py + 138, "EXPERIENCE", 13, 500, MUT, ls=2.4, mono=True)
EXPERIENCE = ["Shaped the investment thesis of a VC fund.",
              "Advised Fortune 500 CEOs on restructuring liabilities above $100M."]
y = py + 174
for item in EXPERIENCE:
    for ln in wrap(item, 19, 400, DW):
        s.T(DX, y, ln, 19, 400)
        y += 27
    y += 12
EXP_END = y - 12 - 27 + 8

# the link sits on the column's foot, under a hairline, like a contact line
LBASE = ROW_B - PAD - 4
assert EXP_END + 34 <= LBASE - 30, f"experience runs into the link ({EXP_END})"
s.rule(LBASE - 34, 0.1, DX, DW)
s.g("linkedin")
s.raw(f'<a href="{LINKEDIN}" target="_blank">')
# LinkedIn's official mark, byte-for-byte from @iconify-json/logos (linkedin-icon, CC0)
s.raw(f'<g transform="translate({DX} {LBASE - 17}) scale({20 / 256:.5f})">'
      '<path fill="#0a66c2" d="M218.123 218.127h-37.931v-59.403c0-14.165-.253-32.4-19.728-32.4c-19.756 0-22.779 15.434-22.779 31.369v60.43h-37.93V95.967h36.413v16.694h.51a39.91 39.91 0 0 1 35.928-19.733c38.445 0 45.533 25.288 45.533 58.186zM56.955 79.27c-12.157.002-22.014-9.852-22.016-22.009s9.851-22.014 22.008-22.016c12.157-.003 22.014 9.851 22.016 22.008A22.013 22.013 0 0 1 56.955 79.27m18.966 138.858H37.95V95.967h37.97zM237.033.018H18.89C8.58-.098.125 8.161-.001 18.471v219.053c.122 10.315 8.576 18.582 18.89 18.474h218.144c10.336.128 18.823-8.139 18.966-18.474V18.454c-.147-10.33-8.635-18.588-18.966-18.453"/></g>')
LTXT = "linkedin.com/in/khan-abir"
lw = fit(LTXT, 18, 500, DW - 32)
s.T(DX + 32, LBASE, LTXT, 18, 500)
s.R(DX + 32, LBASE + 4, round(lw), 1, INK, extra=' fill-opacity="0.35"')   # reads as a link
s.raw('</a>')
s.end()
s.end()

# ---------------------------------------------------------------- the proofs, as three linked tiles
TX0 = FX + FW + 24
TGAP = 24
TW = (W - M - TX0 - 2 * TGAP) / 3
TH = ROW_B - TOP
TP = 28
HERO_Y = TOP + 110                    # top of each tile's picture
CAP_Y = ROW_B - TP - 36               # first baseline of each tile's punchline

def tile_head(x, text):
    s.card(round(x, 1), TOP, round(TW, 1), TH)
    fit(text, 13, 500, TW - 2 * TP - 24, ls=1.44)
    s.label(round(x + TP, 1), TOP + TP + 18, text, INK, 13)

def punch(x, text):
    lines = wrap(text, 21, 600, TW - 2 * TP)
    assert len(lines) <= 2, f"punchline longer than two lines: {text!r}"
    for i, ln in enumerate(lines):
        s.T(round(x + TP, 1), CAP_Y + i * 28, ln, 21, 600, ls=-0.3)

# 1 - the gap: who owns each step between an alert and an action
x = TX0
s.g("proof-gap")
tile_head(x, "SEEN THE GAP")
STEPS = [("ALERT", "Risk tools", INK), ("DECIDE", "Nobody", AMB), ("ACT", "Execution", INK)]
sw = (TW - 2 * TP - 2 * 8) / 3
for i, (step, owner, col) in enumerate(STEPS):
    sx_ = round(x + TP + i * (sw + 8), 1)
    s.R(sx_, HERO_Y + 40, round(sw, 1), 10, col, 5)
    fit(step, 13, 600, sw, ls=2 * 0.6)
    fit(owner, 15, 600 if col == AMB else 400, sw - 4)
    s.T(sx_, HERO_Y + 78, step, 13, 600, col, ls=2, mono=True)
    s.T(sx_, HERO_Y + 102, owner, 15, 600 if col == AMB else 400, col if col == AMB else MUT)
punch(x, "Nobody owns the step between. That is my bet.")
s.end()

# 2 - the product: two counts from the build, not from a market
x = TX0 + TW + TGAP
s.g("proof-built")
tile_head(x, "BUILT THE PRODUCT")
for i, (n, what) in enumerate([("14", "live agents"), ("60", "live sources")]):
    nx = round(x + TP + i * (TW - 2 * TP) / 2, 1)
    s.T(nx, HERO_Y + 74, n, 76, 600, ls=-3)
    s.T(nx, HERO_Y + 102, what, 16, 400, MUT)
punch(x, "Runs today, end to end.")
s.end()

# 3 - the buyers: the groundwork, in the order it was done
x = TX0 + 2 * (TW + TGAP)
s.g("proof-buyers")
tile_head(x, "MAPPED THE BUYERS")
CHAIN = ["Forwarder ICP list", "Enriched in Apollo", "Events lined up"]
cy = HERO_Y - 4
bx = round(x + TP, 1)
for i, step in enumerate(CHAIN):
    last = i == len(CHAIN) - 1
    cw = round(width(step, 15, 500) + 28)
    assert cw <= TW - 2 * TP, f"chain step too wide: {step}"
    s.R(bx, cy, cw, 32, INK if last else CARD, 8, "" if last else f' stroke="{INK}" stroke-opacity="0.18"')
    s.T(bx + 14, cy + 21, step, 15, 500, BG if last else INK)
    if not last:
        s.line(bx + 16, cy + 34, bx + 16, cy + 44, INK, 0.35, 1.5)
        s.raw(f'<path d="M{bx + 12} {cy + 40} l4 4 l4 -4" stroke="{INK}" stroke-opacity="0.35" stroke-width="1.5" fill="none"/>')
    cy += 46
assert cy - 14 <= CAP_Y - 30, "chain runs into the punchline"
punch(x, "Next: outreach.")
s.end()

# the joins between tiles: seen, then built, then mapped
s.g("proof-joins")
for i in (1, 2):
    gx = TX0 + i * TW + (i - 0.5) * TGAP
    gy = TOP + TH / 2
    s.raw(f'<circle cx="{gx:.1f}" cy="{gy}" r="15" fill="{CARD}" stroke="{INK}" stroke-opacity="0.18"/>')
    s.raw(f'<path d="M{gx - 2.5:.1f} {gy - 5} l5 5 l-5 5" stroke="{INK}" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
s.end()

# ---------------------------------------------------------------- the logos, one horizontal band
BY = BOTTOM - BAND_H
GROUPS = [("EDUCATION", ["nova-sbe", "cems-mim"]),
          ("WORK", ["alvarez-and-marsal", "scaile", "biome-vc"]),
          ("INSTITUTIONS", ["un-foundation", "manage-and-more", "hack-nation"])]
NAMES = {"nova-sbe": "Nova SBE", "cems-mim": "CEMS MIM", "alvarez-and-marsal": "Alvarez &amp; Marsal",
         "scaile": "SCAILE", "biome-vc": "Biome VC", "un-foundation": "UN Foundation",
         "manage-and-more": "Manage and More", "hack-nation": "Hack-Nation"}
# Optical height per mark, set by eye on the render: a lockup with small type under it
# needs more height than a one-line wordmark to carry the same weight.
LOGO_H = {"nova-sbe": 60, "cems-mim": 42, "alvarez-and-marsal": 68, "scaile": 34}
SLOT_W, SLOT_H, IN_GAP = 168, 52, 36
ROW_CY = BY + 98                       # centre line of the logos

def size_of(key):
    p = HERE / "logos" / f"{key}.png"
    if not p.exists(): return None, SLOT_W, SLOT_H
    im = Image.open(p)
    h = LOGO_H.get(key, 52)
    return p, h * im.width / im.height, h

def draw_logo(key, x):
    p, w, h = size_of(key)
    s.g(f"logo-{key}")
    if p:
        s.raw(f'<image x="{x:.1f}" y="{ROW_CY - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" href="{embed(p, "image/png")}"/>')
    else:
        slot(round(x), round(ROW_CY - SLOT_H / 2), SLOT_W, SLOT_H, [f"[ {NAMES[key]} ]"], 14, f"logo-{key}-slot")
    s.end()
    return w

gw = [sum(size_of(k)[1] for k in keys) + IN_GAP * (len(keys) - 1) for _, keys in GROUPS]
INNER0, INNER1 = M + 32, W - M - 32
free = (INNER1 - INNER0) - sum(gw) - 2
assert free >= 4 * 32, f"logo band too full ({free:.0f}px free)"
gap = free / 4
s.g("logos")
s.card(M, BY, W - 2 * M, BAND_H)
x = INNER0
for gi, (lab, keys) in enumerate(GROUPS):
    if gi:
        x += gap
        s.R(round(x), BY + 24, 1, BAND_H - 48, INK, extra=' fill-opacity="0.1"')
        x += 1 + gap
    s.T(round(x), BY + 40, lab, 13, 500, MUT, ls=2.4, mono=True)
    lx = x
    for key in keys:
        lx += draw_logo(key, lx) + IN_GAP
    x += gw[gi]
s.end()

# ---------------------------------------------------------------- the line they repeat
CLOSE = "I’ve helped shape a fund’s thesis. This is the company I’d back."
fit(CLOSE, 34, 600, W - 2 * M, ls=-0.8)
s.g("closing")
s.T(M, 936, CLOSE, 34, 600, ls=-0.8)
s.end()

s.footer(10)
s.write("slide-10-who-am-i.svg")
