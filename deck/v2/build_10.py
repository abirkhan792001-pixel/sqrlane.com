#!/usr/bin/env python3
"""Slide 10 - Who am I. Option A, "the proof stack", on the owner's pick (2026-10-01).

Left, the founder: photo, name, role, the two approved experience lines and a LinkedIn
link. Right, three one-line proofs, one per part of the headline (the owner asked for them
brief), and under them the logo band in the owner's three groups.

Logos are the owner's own files (deck/v2/logos/), cropped to the mark and, where they came
on white, made transparent - nothing redrawn. A logo whose file has not arrived is a dashed
box in its own named layer (logo-*), sized for the owner to drop the file in.

Name and photo stay dashed slots: a placeholder that reads like real copy is how an
invented founder reaches a room.

SVG text does not wrap, so every string is measured against Geist and the build stops if
one overruns its box."""
from kit import *
import base64, math, pathlib
from PIL import Image, ImageFont

GREEN, GREEN_BG = "#0F7B3F", "#E9F3EC"
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

def tick(cx, cy):
    s.raw(f'<circle cx="{cx}" cy="{cy}" r="11" fill="{GREEN_BG}"/>')
    s.raw(f'<path d="M{cx - 4.5} {cy + 0.3}l3 3 6-6.4" stroke="{GREEN}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')

s = Slide()
HEAD = "Seen the gap. Built the product. Mapped the buyers."
fit(HEAD, 66, 600, W - 2 * M, ls=-2)
s.header("08 · WHO AM I", HEAD, "One founder. Every proof below is already done.")

TOP, BOTTOM = 318, 880

# ---------------------------------------------------------------- the founder
FX, FW, PAD = M, 520, 32
IN_W = FW - 2 * PAD
s.g("founder")
s.card(FX, TOP, FW, BOTTOM - TOP)
PH = 200
slot(FX + PAD, TOP + PAD, PH, PH, ["[ Photo ]"], 17, "photo")
NX = FX + PAD + PH + 20
slot(NX, TOP + PAD + 6, IN_W - PH - 20, 48, ["[ Full name ]"], 24, "name")
s.T(NX, TOP + PAD + 88, "Founder, SQRlane", 19, 400, MUT)

HR = TOP + PAD + PH + 28
s.rule(HR, 0.1, FX + PAD, IN_W)
s.T(FX + PAD, HR + 36, "EXPERIENCE", 13, 500, MUT, ls=2.4, mono=True)
EXPERIENCE = ["Shaped the investment thesis of a $170M VC fund.",
              "Advised Fortune 500 CEOs on restructuring liabilities above $100M."]
y = HR + 74
for item in EXPERIENCE:
    for ln in wrap(item, 19, 400, IN_W):
        s.T(FX + PAD, y, ln, 19, 400)
        y += 27
    y += 14
EXP_END = y - 14 - 27 + 8

# the link sits on the card's foot, under a hairline, like a contact line
FOOT = BOTTOM - PAD - 46
assert EXP_END + 20 <= FOOT, f"experience runs into the link ({EXP_END})"
s.rule(FOOT, 0.1, FX + PAD, IN_W)
s.g("linkedin")
s.raw(f'<a href="{LINKEDIN}" target="_blank">')
LBASE = BOTTOM - PAD - 6
# LinkedIn's official mark, byte-for-byte from @iconify-json/logos (linkedin-icon, CC0)
s.raw(f'<g transform="translate({FX + PAD} {LBASE - 17}) scale({20 / 256:.5f})">'
      '<path fill="#0a66c2" d="M218.123 218.127h-37.931v-59.403c0-14.165-.253-32.4-19.728-32.4c-19.756 0-22.779 15.434-22.779 31.369v60.43h-37.93V95.967h36.413v16.694h.51a39.91 39.91 0 0 1 35.928-19.733c38.445 0 45.533 25.288 45.533 58.186zM56.955 79.27c-12.157.002-22.014-9.852-22.016-22.009s9.851-22.014 22.008-22.016c12.157-.003 22.014 9.851 22.016 22.008A22.013 22.013 0 0 1 56.955 79.27m18.966 138.858H37.95V95.967h37.97zM237.033.018H18.89C8.58-.098.125 8.161-.001 18.471v219.053c.122 10.315 8.576 18.582 18.89 18.474h218.144c10.336.128 18.823-8.139 18.966-18.474V18.454c-.147-10.33-8.635-18.588-18.966-18.453"/></g>')
LTXT = "linkedin.com/in/khan-abir"
lw = fit(LTXT, 18, 500, IN_W - 32)
s.T(FX + PAD + 32, LBASE, LTXT, 18, 500)
s.R(FX + PAD + 32, LBASE + 4, round(lw), 1, INK, extra=' fill-opacity="0.35"')   # reads as a link
s.raw('</a>')
s.end()
s.end()

# ---------------------------------------------------------------- the proofs, one line each
PX = FX + FW + 24
PW = W - M - PX
ROW, PPAD = 58, 12
LAB_W = 250
CX0, CX1 = PX + 36 + LAB_W, PX + PW - 36
PROOFS = [("proof-gap", "SEEN THE GAP", "Nobody owns the step between. That is my bet."),
          ("proof-built", "BUILT THE PRODUCT", "Runs today: 14 live agents, 60 live sources."),
          ("proof-buyers", "MAPPED THE BUYERS", "Forwarder ICP list in Apollo. Events lined up for outreach.")]
PH_CARD = len(PROOFS) * ROW + 2 * PPAD
s.g("proofs")
s.card(PX, TOP, PW, PH_CARD)
for i, (idn, lab, line) in enumerate(PROOFS):
    top = TOP + PPAD + i * ROW
    s.g(idn)
    if i: s.rule(top, 0.1, PX + 36, PW - 72)
    tick(PX + 36 + 11, top + 29)
    fit(lab, 13, 500, LAB_W - 40, ls=1.44)
    s.T(PX + 36 + 34, top + 34, lab, 13, 500, INK, ls=2.4, mono=True)
    fit(line, 24, 600, CX1 - CX0, ls=-0.4)
    s.T(CX0, top + 37, line, 24, 600, ls=-0.4)
    s.end()
s.end()

# ---------------------------------------------------------------- the logos
BY = TOP + PH_CARD + 24
BH = BOTTOM - BY
GROUPS = [("EDUCATION", ["nova-sbe", "cems-mim"]),
          ("WORK", ["alvarez-and-marsal", "scaile", "biome-vc"]),
          ("INSTITUTIONS", ["un-foundation", "manage-and-more", "hack-nation"])]
NAMES = {"nova-sbe": "Nova SBE", "cems-mim": "CEMS MIM", "alvarez-and-marsal": "Alvarez &amp; Marsal",
         "scaile": "SCAILE", "biome-vc": "Biome VC", "un-foundation": "UN Foundation",
         "manage-and-more": "TUM Manage and More", "hack-nation": "Hack-Nation"}
SIDE, BPAD = 28, 32
COL_W = math.floor((PW - 2 * BPAD - 2 * (2 * SIDE + 1)) / 3)
SLOT_H, SLOT_GAP = 76, 12
LOGO_MAX_W = COL_W - 20
# Optical height per mark, set by eye on the render: a lockup with small type under it
# needs more height than a one-line wordmark to carry the same weight.
LOGO_H = {"nova-sbe": 62, "cems-mim": 44, "alvarez-and-marsal": 70, "scaile": 34}
SY0 = BY + 64
assert SY0 + 3 * SLOT_H + 2 * SLOT_GAP <= BOTTOM - 20, "logo slots run past the band"

def logo(key, x, y):
    """The owner's file at its optical height (LOGO_H), left-aligned in its slot."""
    p = HERE / "logos" / f"{key}.png"
    s.g(f"logo-{key}")
    if p.exists():
        im = Image.open(p)
        a = im.width / im.height
        h = min(LOGO_H.get(key, 56), LOGO_MAX_W / a)
        w = h * a
        href = "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
        s.raw(f'<image x="{x}" y="{y + (SLOT_H - h) / 2:.1f}" width="{w:.1f}" height="{h:.1f}" href="{href}"/>')
    else:
        slot(x, y + 8, 220, SLOT_H - 16, [f"[ {NAMES[key]} ]"], 15, f"logo-{key}-slot")
    s.end()

s.g("logos")
s.card(PX, BY, PW, BH)
x = PX + BPAD
for gi, (lab, keys) in enumerate(GROUPS):
    if gi:
        s.R(x + SIDE, BY + 28, 1, BH - 56, INK, extra=' fill-opacity="0.1"')
        x += 2 * SIDE + 1
    s.T(x, BY + 42, lab, 13, 500, MUT, ls=2.4, mono=True)
    for j, key in enumerate(keys):
        logo(key, x, SY0 + j * (SLOT_H + SLOT_GAP))
    x += COL_W
assert x <= PX + PW - BPAD, f"logo columns overrun by {x - (PX + PW - BPAD)}px"
s.end()

# ---------------------------------------------------------------- the line they repeat
CLOSE = "I’ve helped shape a fund’s thesis. This is the company I’d back."
fit(CLOSE, 34, 600, W - 2 * M, ls=-0.8)
s.g("closing")
s.T(M, 936, CLOSE, 34, 600, ls=-0.8)
s.end()

s.footer(10)
s.write("slide-10-who-am-i.svg")
