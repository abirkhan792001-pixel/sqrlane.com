#!/usr/bin/env python3
"""Slide 05 - The Job 1/2. One file end to end: the clock, the 26 handoffs, what the
TMS holds and does not, and what a clean file earns."""
from kit import *
GREEN = "#0F7B3F"
import json, pathlib, re
# Official marks, byte-for-byte from Iconify's npm sets (logos + simple-icons: CC0,
# vscode-icons: MIT). Vendors with no published mark stay as name badges: never redraw one.
MARKS = json.loads((pathlib.Path(__file__).with_name("channel_marks.json")).read_text())
_n = [0]
def mark(name, x, y, size=18):
    m = MARKS[name]; sc = size / max(m["w"], m["h"])
    _n[0] += 1; body = re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + f"m{_n[0]}-" + g.group(2), m["body"])
    dx = x + (size - m["w"] * sc) / 2; dy = y + (size - m["h"] * sc) / 2
    s.raw(f'<g id="mark-{name.lower()}" transform="translate({dx:.1f} {dy:.1f}) scale({sc:.4f})">{body}</g>')
    return size
def glyph(kind, x, y, size=18):
    c = MUT; k = size / 18
    p = {"phone": f'<path d="M{x+5*k} {y+2*k} h{8*k} a{1.5*k} {1.5*k} 0 0 1 {1.5*k} {1.5*k} v{11*k} a{1.5*k} {1.5*k} 0 0 1 -{1.5*k} {1.5*k} h-{8*k} a{1.5*k} {1.5*k} 0 0 1 -{1.5*k} -{1.5*k} v-{11*k} a{1.5*k} {1.5*k} 0 0 1 {1.5*k} -{1.5*k} Z M{x+8*k} {y+14*k} h{2*k}" stroke="{c}" stroke-width="1.5" fill="none" stroke-linecap="round"/>',
         "sms": f'<path d="M{x+2*k} {y+4*k} h{14*k} v{9*k} h-{8*k} l-{3.5*k} {3*k} v-{3*k} h-{2.5*k} Z" stroke="{c}" stroke-width="1.5" fill="none" stroke-linejoin="round"/>',
         "portal": f'<rect x="{x+1.5*k}" y="{y+3*k}" width="{15*k}" height="{12*k}" rx="{1.5*k}" stroke="{c}" stroke-width="1.5" fill="none"/><path d="M{x+1.5*k} {y+6.5*k} h{15*k}" stroke="{c}" stroke-width="1.5"/>',
         "EDI": f'<path d="M{x+3*k} {y+6*k} h{11*k} m-{3*k} -{3*k} l{3*k} {3*k} l-{3*k} {3*k} M{x+15*k} {y+12*k} h-{11*k} m{3*k} -{3*k} l-{3*k} {3*k} l{3*k} {3*k}" stroke="{c}" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'}[kind]
    s.raw(f'<g id="glyph-{kind.lower()}">{p}</g>')
    return size
def badge(name, x, y):
    w = round(len(name) * 7 + 14)
    s.R(x, y, w, 20, TRACK, 3)
    s.T(x + w / 2, y + 14, name, 11.5, 600, INK, anchor="middle")
    return w
def channel(name, x, y):
    if name in MARKS: return mark(name, x, y)
    if name in ("phone", "sms", "portal", "EDI"): return glyph(name, x, y)
    return badge(name, x, y - 1)

s = Slide()
s.header("04 · THE JOB, 1 OF 2", "45 days, 7 parties, €127 of margin.",
         "The TMS stores the booking. It does not decide or move anything.")

# ---- one file, end to end
TY, TH = 306, 416
s.g("one-file")
s.card(M, TY, W - 2 * M, TH)
x0 = M + 32
STAGES = ["Enquiry", "Quote", "Book", "Docs", "In transit", "Customs", "Delivery", "Invoice"]
CX = [380 + i * 108 for i in range(8)]
s.T(x0, TY + 42, "ONE FILE, END TO END", 13, 600, MUT, ls=1.4)
s.T(CX[0] - 64, TY + 43, "Shanghai to Munich · 45 days", 15, 500, MUT)
# The clock, in three phases. Handoffs per phase are summed from the grid below;
# widths follow the days (45 in all, 32 at sea).
s.T(x0, TY + 112, "The clock", 15, 500)
phases = [("Before sailing", 9, 12, True), ("At sea · 32 days", 32, 4, False), ("After arrival", 4, 10, True)]
assert sum(p[2] for p in phases) == 26 and sum(p[1] for p in phases) == 45
BX0, BX1, GAPB = CX[0] - 64, W - M - 32, 6
unit = (BX1 - BX0 - GAPB * 2) / 45
bx = BX0
s.g("clock")
for name, d, n, busy in phases:
    w = d * unit
    s.T(round(bx, 1), TY + 80, name, 13, 500, MUT)
    s.R(round(bx, 1), TY + 90, round(w, 1), 36, AMB if busy else TRACK, 8, ' fill-opacity="0.14"' if busy else "")
    s.T(round(bx + 14, 1), TY + 113, f"{n} handoffs", 15, 600, AMB if busy else INK)
    if not busy:
        s.T(round(bx + w - 14, 1), TY + 113, "the lane goes unwatched", 13, 400, MUT, anchor="end")
    bx += w + GAPB
s.end()
s.rule(TY + 146, 0.08, x0, W - 2 * M - 64)

HY = TY + 176
s.T(x0, HY, "WHO THEY TALK TO", 13, 600, AMB, ls=1.4)
for c, st in zip(CX, STAGES):
    s.T(c, HY, st, 13, 600, INK, anchor="middle")
RX = 1216
RX2 = RX + 262
s.T(RX, HY, "WHAT THEY EXCHANGE", 13, 600, AMB, ls=1.4)
s.T(RX2, HY, "REACHED ON", 13, 600, AMB, ls=1.4)
parties = [
    ("Customer", [1, 1, 1, 1, 1, 0, 1, 1], ["Outlook", "Gmail", "Slack", "WhatsApp"], "enquiry, PO, delivery date"),
    ("Shipping line", [0, 1, 1, 1, 1, 0, 0, 1], ["portal", "EDI", "INTTRA", "Outlook"], "rate, booking, B/L draft"),
    ("Origin agent", [0, 0, 1, 1, 0, 0, 0, 0], ["Outlook", "WeChat", "WhatsApp"], "pickup, packing list"),
    ("Port terminal", [0, 0, 0, 1, 1, 1, 0, 0], ["Portbase", "DAKOSY", "portal"], "gate-in, VGM, release"),
    ("Haulier", [0, 1, 0, 0, 0, 0, 1, 1], ["phone", "WhatsApp", "sms", "TIMOCOM"], "pickup slot, proof of delivery"),
    ("Customs broker", [0, 0, 0, 1, 0, 1, 1, 0], ["Outlook", "ATLAS", "portal"], "entry, duties"),
    ("Consignee", [0, 0, 0, 0, 1, 0, 1, 1], ["Outlook", "Teams", "phone"], "arrival notice, delivery slot"),
]
assert sum(sum(p[1]) for p in parties) == 26
s.g("handoffs")
for r, (name, marks, chans, what) in enumerate(parties):
    ry = HY + 32 + r * 25
    s.T(x0, ry, name, 14, 500)
    for c, m in zip(CX, marks):
        if m:
            s.raw(f'<circle cx="{c}" cy="{ry - 5}" r="6.5" fill="{AMB}"/>')
        else:
            s.raw(f'<circle cx="{c}" cy="{ry - 5}" r="2" fill="{INK}" fill-opacity="0.2"/>')
    s.T(RX, ry, what, 14, 400, INK)
    cxp = RX2
    for ch in chans:
        cxp += channel(ch, cxp, ry - 14) + 12
OPEN_R, OPEN_C = 1, 3
s.raw(f'<circle cx="{CX[OPEN_C]}" cy="{HY + 32 + OPEN_R * 25 - 5}" r="12" fill="none" stroke="{AMB}" stroke-width="1.5"/>')
s.end()
s.rule(TY + TH - 48, 0.08, x0, W - 2 * M - 64)
# one dot, opened up: the B/L draft from the shipping line
SY = TY + TH - 18
s.g("one-dot-opened")
s.T(x0, SY, "ONE DOT, OPENED", 12, 600, AMB, ls=1.2)
steps = ["B/L draft arrives by mail", "checked against the booking", "corrected with the carrier",
         "re-typed into the TMS", "forwarded to the customer"]
sx = x0 + 160
for k, st in enumerate(steps):
    w = round(len(st) * 6.9 + 24)
    s.R(sx, SY - 17, w, 24, AMB if k == 3 else TRACK, 4, ' fill-opacity="0.14"' if k == 3 else "")
    s.T(sx + w / 2, SY - 1, st, 13, 500, AMB if k == 3 else INK, anchor="middle")
    sx += w
    if k < len(steps) - 1:
        s.T(sx + 11, SY - 1, "→", 13, 400, MUT, anchor="middle"); sx += 22
s.T(W - M - 32, SY, "26 handoffs · 7 parties · 15 channels", 13, 500, MUT, anchor="end")
s.end()
s.end()

# ---- bottom: what the TMS does, what a clean file earns
BY, BH = 742, 212
LW = 700
s.g("where-the-tms-sits")
s.card(M, BY, LW, BH)
s.T(x0, BY + 40, "WHERE THE TMS SITS", 13, 600, MUT, ls=1.4)
cols = [("IT HOLDS", ["The booking and its dates", "The rate that was agreed", "The documents on file"], True),
        ("IT DOES NOT", ["Watch anything", "Decide anything", "Type itself"], False)]
for i, (head, items, ok) in enumerate(cols):
    cx = x0 + i * 330
    s.T(cx, BY + 70, head, 12, 600, INK if ok else AMB, ls=1.2)
    for k, it in enumerate(items):
        iy = BY + 98 + k * 24
        if ok:
            s.raw(f'<path d="M{cx} {iy - 5} l4 4 l8 -9" stroke="{GREEN}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            s.raw(f'<path d="M{cx + 1} {iy - 12} l9 9 M{cx + 10} {iy - 12} l-9 9" stroke="{AMB}" stroke-width="2" fill="none" stroke-linecap="round"/>')
        s.T(cx + 22, iy, it, 15, 400)
s.line(x0 + 306, BY + 56, x0 + 306, BY + 154, INK, 0.1, 1)
s.rule(BY + 168, 0.08, x0, LW - 64)
s.T(x0, BY + 194, "The TMS is the record. The desk types into it.", 16, 600)
s.end()

RX0, RW = M + LW + 28, W - 2 * M - LW - 28
s.g("what-a-clean-file-earns")
s.card(RX0, BY, RW, BH)
ex = RX0 + 32
s.T(ex, BY + 38, "WHAT A CLEAN FILE EARNS", 13, 600, AMB, ls=1.4)
s.T(RX0 + RW - 32, BY + 40, "per container", 13, 400, MUT, anchor="end")
rows = [("Billed to the customer", "€1,913", "100.0%", 1913, False, False),
        ("Paid to the carrier", "−€1,475", "−77.1%", 1475, False, False),
        ("Gross profit", "€438", "22.9%", 438, False, False),
        ("Running the desk", "−€311", "−16.3%", 311, False, False),
        ("Left over", "€127", "6.6%", 127, True, True)]
BAR0, BARW = ex + 210, 380
for k, (lab, val, pct, v, bold, hi) in enumerate(rows):
    ry = BY + 66 + k * 22
    s.T(ex, ry, lab, 14, 600 if bold else 400)
    s.R(BAR0, ry - 11, max(4, round(BARW * v / 1913)), 12, AMB if hi else MID, 3)
    s.T(RX0 + RW - 130, ry, val, 14, 600, AMB if hi else INK, anchor="end")
    s.T(RX0 + RW - 32, ry, pct, 14, 600 if hi else 400, AMB if hi else MUT, anchor="end")
s.rule(BY + 168, 0.08, ex, RW - 64)
s.T(ex, BY + 194, "€6.60 kept on every €100 billed. That is the good day.", 16, 600)
s.T(RX0 + RW - 32, BY + 194, "K+N Sea Logistics FY25 · CHF at 1.07", 11.5, 400, MUT, anchor="end")
s.end()

s.footer(5)
s.write("slide-05-the-job-1.svg")
