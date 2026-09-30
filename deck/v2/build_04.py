#!/usr/bin/env python3
"""Slide 04 - The Why. Where the EUR 4bn sits, and the seam neither category crosses."""
from kit import *
s = Slide()
s.header("03 · THE WHY", "€4bn a year of desk work. Nobody does all of it.",
         "Risk platforms watch and stop. Execution AI starts after the decision. Both are funded.")

Y, HGT = 318, 520

# ---- the market, counted
LX, LW = M, 540
s.g("where-the-4bn-sits")
s.card(LX, Y, LW, HGT)
x = LX + 32
s.label(x, Y + 48, "WHERE THE €4BN SITS", INK, 13)
def step(y, big, lab):
    s.T(x, y, big, 44, 600, ls=-1.2); s.T(x, y + 28, lab, 15, 400, MUT)
def op(y, sym, lab, chip=None):
    s.T(x, y, sym, 17, 600, AMB); s.T(x + 110, y, lab, 15, 400, MUT)
    if chip:
        s.R(x + 330, y - 16, 72, 22, AMB, 6, ' fill-opacity="0.12"')
        s.T(x + 366, y - 1, chip, 12, 600, AMB, anchor="middle")
step(Y + 114, "1.6M", "people in European freight forwarding")
op(Y + 184, "÷ 5", "1 in 5 on an operating desk", "assumed")
step(Y + 250, "320,000", "operating desks")
op(Y + 320, "× €13,600", "admin cost per desk, per year")
s.rule(Y + 350, 0.1, x, LW - 64)
s.T(x, Y + 428, "€4.36bn", 64, 600, ls=-2)
s.T(x, Y + 460, "a year in wages, spent on re-typing", 16, 500)
s.T(x, Y + 490, "UK: 66,187 staff across 6,737 firms, scaled to 163,000 EU firms", 12, 400, MUT)
s.T(x, Y + 508, "IBISWorld · SalaryExpert · €34k salary × 40% admin", 12, 400, MUT)
s.end()

# ---- three columns: risk platforms, the seam, execution AI
CW3 = 372
cols = [
    ("risk-platforms", "RISK PLATFORMS", "Watch, then stop.", "Never touch the booking.", [0],
     ["Everstream", "Interos", "Resilinc"], "$1bn", "Interos valuation, 2024", None),
    ("the-seam", "THE SEAM", "Decide.", "Empty on both sides.", [0, 1, 2, 3],
     None, None, None, None),
    ("execution-ai", "EXECUTION AI", "Act, once you decide.", "Never touch risk.", [2, 3],
     ["5U AI", "Augment", "Nexcade", "Zauber"], "$96.7M", "raised since Sept 2025",
     "Augment $85M · Nexcade $8.5M · 5U AI $3.2M"),
]
STEPS = ["WATCH", "DECIDE", "ACT", "RECORD"]
for i, (idn, lab, title, sub, on, vendors, big, cap, src) in enumerate(cols):
    cx = LX + LW + 24 + i * (CW3 + 24)
    seam = idn == "the-seam"
    hi = AMB if seam else INK
    s.g(idn)
    if seam:
        s.R(cx, Y, CW3, HGT, AMB, 14, f' fill-opacity="0.06" stroke="{AMB}" stroke-opacity="0.45"')
    else:
        s.card(cx, Y, CW3, HGT)
    ix = cx + 28
    s.T(ix, Y + 48, lab, 13, 600, AMB if seam else MUT, ls=1.4)
    s.T(ix, Y + 94, title, 40 if seam else 26, 600, ls=-1 if seam else -0.5)
    s.T(ix, Y + 124, sub, 15, 400, AMB if seam else MUT)
    sw = (CW3 - 56 - 3 * 8) / 4
    for k, nm in enumerate(STEPS):
        bx = ix + k * (sw + 8)
        active = k in on
        s.R(bx, Y + 150, sw, 6, hi if active else TRACK, 3)
        s.T(bx, Y + 176, nm, 11, 600 if active else 500, hi if active else MUT, ls=0.8)
    if vendors:
        for k, v in enumerate(vendors):
            s.R(ix, Y + 204 + k * 42, CW3 - 56, 34, TRACK, 8, ' fill-opacity="0.7"')
            s.T(ix + (CW3 - 56) / 2, Y + 226 + k * 42, v, 14, 500, anchor="middle")
        s.rule(Y + 404, 0.1, ix, CW3 - 56)
        s.T(ix, Y + 456, big, 38, 600, ls=-1)
        s.T(ix, Y + 482, cap, 14, 400, MUT)
        if src:
            s.T(ix, Y + 504, src, 11.5, 400, MUT)
    else:
        s.T(ix, Y + 236, "One loop, one record.", 21, 600)
        s.T(ix, Y + 266, "Watch and act are sold.", 15, 400, MUT)
        s.T(ix, Y + 288, "The step between is not.", 15, 400, MUT)
        s.rule(Y + 404, 0.12, ix, CW3 - 56)
        s.R(ix, Y + 440, 28, 28, INK, 7)
        s.raw(f'<path d="M{ix+7} {Y+461}h14 M{ix+7} {Y+454}h9.5 M{ix+7} {Y+447}h5" stroke="{BG}" stroke-width="2.2" stroke-linecap="round" fill="none"/>')
        s.T(ix + 40, Y + 461, "sqrlane", 20, 600)
        s.T(ix, Y + 500, "Owns the decision, end to end.", 14, 500, AMB)
    s.end()

s.g("closing")
s.T(M, 900, "Anyone can send an alert. SQRlane makes the call, records why,", 30, 600, ls=-0.6)
s.T(M, 938, "and puts it on the booking.", 30, 600, ls=-0.6)
s.T(W - M, 900, "163,000 forwarding businesses in Europe. 24 of the top 25 run CargoWise.", 12.5, 400, MUT, anchor="end")
s.T(W - M, 920, "IBISWorld 2025 · WiseTech Global FY25 · TAM derived, not measured.", 12.5, 400, MUT, anchor="end")
s.end()
s.footer(4)
s.write("slide-04-the-why.svg")
