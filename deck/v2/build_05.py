#!/usr/bin/env python3
"""Slide 05 - The Job 1/2. One file end to end: the clock, the 26 handoffs, what the
TMS holds and does not, and what a clean file earns."""
from kit import *
GREEN = "#0F7B3F"
s = Slide()
s.header("04 · THE JOB, 1 OF 2", "45 days, 7 parties, €127 of margin.",
         "The TMS stores the booking. It does not decide or move anything.")

# ---- one file, end to end
TY, TH = 306, 416
s.g("one-file")
s.card(M, TY, W - 2 * M, TH)
x0 = M + 32
STAGES = ["Enquiry", "Quote", "Book", "Docs", "In transit", "Customs", "Delivery", "Invoice"]
CX = [400 + i * 124 for i in range(8)]
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
RX = 1392
s.T(RX, HY, "REACHED ON", 13, 600, AMB, ls=1.4)
s.T(W - M - 32, HY, "not every one", 12, 400, MUT, anchor="end")
parties = [
    ("Customer", [1, 1, 1, 1, 1, 0, 1, 1], ["Outlook", "Gmail", "Slack", "WhatsApp"]),
    ("Shipping line", [0, 1, 1, 1, 1, 0, 0, 1], ["portal", "EDI", "INTTRA", "Outlook"]),
    ("Origin agent", [0, 0, 1, 1, 0, 0, 0, 0], ["Outlook", "WeChat", "WhatsApp"]),
    ("Port terminal", [0, 0, 0, 1, 1, 1, 0, 0], ["Portbase", "DAKOSY", "portal"]),
    ("Haulier", [0, 1, 0, 0, 0, 0, 1, 1], ["phone", "WhatsApp", "SMS", "TIMOCOM"]),
    ("Customs broker", [0, 0, 0, 1, 0, 1, 1, 0], ["Outlook", "ATLAS", "portal"]),
    ("Consignee", [0, 0, 0, 0, 1, 0, 1, 1], ["Outlook", "Teams", "phone"]),
]
assert sum(sum(p[1]) for p in parties) == 26
s.g("handoffs")
for r, (name, marks, chans) in enumerate(parties):
    ry = HY + 32 + r * 25
    s.T(x0, ry, name, 14, 500)
    for c, m in zip(CX, marks):
        if m:
            s.raw(f'<circle cx="{c}" cy="{ry - 5}" r="6.5" fill="{AMB}"/>')
        else:
            s.raw(f'<circle cx="{c}" cy="{ry - 5}" r="2" fill="{INK}" fill-opacity="0.2"/>')
    s.T(RX, ry, str(len(chans)), 14, 600, AMB)
    s.T(RX + 24, ry, "  ·  ".join(chans), 14, 400, INK)
s.end()
s.rule(TY + TH - 48, 0.08, x0, W - 2 * M - 64)
s.T(x0, TY + TH - 18, "26 handoffs, 7 parties, 15 channels. Every dot is a mail, a portal login or a call.", 15, 400, MUT)
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
