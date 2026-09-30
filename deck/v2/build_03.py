#!/usr/bin/env python3
"""Slide 03 - The What. Two problems, side by side, each with its two figures."""
from kit import *
s = Slide()
s.header("02 · THE WHAT", "Two problems. Each makes the other worse.",
         "Every hour spent re-typing is an hour nobody watches the lane.")

PW, PY, PH = 848, 318, 540
def panel(x, n, title, sub, idn):
    s.g(idn)
    s.card(x, PY, PW, PH)
    s.R(x + 32, PY + 32, 30, 30, INK, 7)
    s.T(x + 47, PY + 52, n, 14, 600, BG, anchor="middle", mono=True)
    s.T(x + 78, PY + 57, title, 30, 600, ls=-0.6)
    s.T(x + 32, PY + 96, sub, 17, 400, MUT)

def stat(x, big, lab, qual, src):
    s.T(x, PY + 436, big, 50, 600, ls=-1.4)
    s.T(x, PY + 468, lab, 16, 500)
    s.T(x, PY + 492, qual, 14, 400, MUT)
    s.T(x, PY + 518, src, 11.5, 500, MUT, mono=True, ls=0.3)

# ---- 01 the desk re-types
X1 = M
panel(X1, "01", "The desk re-types the same facts.", "One booking, typed out by hand into every system it touches.", "problem-retyping")
# One source, typed out by hand six times: a new field name, a new date format,
# and one transposed digit nobody catches. Illustrative.
REF = "HLCU-2261188"
SRC_X, SRC_Y, SRC_W, SRC_H = X1 + 32, PY + 144, 212, 170
s.g("source-mail")
s.R(SRC_X, SRC_Y, SRC_W, SRC_H, BG, 12, f' stroke="{INK}" stroke-opacity="0.18"')
s.T(SRC_X + 18, SRC_Y + 30, "CARRIER MAIL", 12, 600, MUT, ls=1.4)
s.T(SRC_X + 18, SRC_Y + 58, "Booking confirmed", 16, 600)
s.T(SRC_X + 18, SRC_Y + 92, "Booking", 12.5, 400, MUT)
s.T(SRC_X + SRC_W - 18, SRC_Y + 92, REF, 13, 600, anchor="end")
s.T(SRC_X + 18, SRC_Y + 118, "ETA", 12.5, 400, MUT)
s.T(SRC_X + SRC_W - 18, SRC_Y + 118, "10 Oct", 13, 600, anchor="end")
s.rule(SRC_Y + 134, 0.08, SRC_X + 18, SRC_W - 36)
s.T(SRC_X + 18, SRC_Y + 156, "the one true copy", 12.5, 400, MUT)
s.end()

rows = [  # system, its field name, the ref as typed, the date as typed, typo?
    ("TMS", "Job ref", REF, "10/10/2026", False),
    ("Carrier portal", "Booking no.", REF, "2026-10-10", False),
    ("Customer mail", "Your ref", REF, "10 October", False),
    ("Customs", "Declarant ref", "HLCU-2216188", "10.10.26", True),
    ("Invoice", "Our ref", REF, "Oct 10", False),
    ("Tracking sheet", "Ref", REF, "10-OCT-26", False),
]
RX, RW, RH, RS = X1 + 304, 512, 32, 36
R0 = PY + 122
srcy = SRC_Y + SRC_H / 2
TRUNK = (SRC_X + SRC_W + RX) / 2
s.g("typed-six-times")
s.line(SRC_X + SRC_W, srcy, TRUNK, srcy, INK, 0.3, 1.5)
s.line(TRUNK, R0 + RH / 2, TRUNK, R0 + 5 * RS + RH / 2, INK, 0.3, 1.5)
for i, (sysn, lab, ref, dt, typo) in enumerate(rows):
    ry = R0 + i * RS
    cy = ry + RH / 2
    col = AMB if typo else INK
    s.line(TRUNK, cy, RX, cy, col, 0.9 if typo else 0.3, 1.5)
    s.raw(f'<circle cx="{RX}" cy="{cy}" r="3" fill="{col}" fill-opacity="{1 if typo else 0.45}"/>')
    s.g("row-" + sysn.lower().replace(" ", "-"))
    s.R(RX, ry, RW, RH, AMB if typo else BG, 8,
        f' fill-opacity="{0.07 if typo else 1}" stroke="{col}" stroke-opacity="{0.5 if typo else 0.12}"')
    s.T(RX + 14, cy + 5, sysn, 13.5, 600)
    s.T(RX + 136, cy + 5, lab, 12.5, 400, MUT)
    s.T(RX + 356, cy + 5, ref, 13, 600 if typo else 500, col, anchor="end")
    s.T(RX + RW - 14, cy + 5, dt, 13, 500, INK, anchor="end")
    s.end()
s.end()
s.T(RX + 14, R0 + 6 * RS + 16, "Same booking. Six field names, six date formats, one typo.", 13, 500, MUT)
s.rule(PY + 372, 0.08, X1 + 32, PW - 64)
stat(X1 + 32, "40%", "of the day on admin", "upper estimate", "logistics industry surveys")
stat(X1 + 440, "€13,600", "per desk, per year", "€34k average salary × 40%", "SalaryExpert 2025 · DE and NL")
s.end()

# ---- 02 nobody watches the lane
X2 = M + PW + 32
panel(X2, "02", "Nobody watches the lane.", "The world moves every lane. Nothing reads it against your bookings.", "problem-unwatched")
risks = [["Tariffs", "Sanctions", "War", "Strikes", "Congestion"], ["Low water", "Storms", "Floods", "Earthquakes", "Closures"]]
ghost = ["Piracy", "Fuel", "Inspections", "Capacity", "Blank sailings"]
CWd, CHt, CG = 144, 38, 16
R0 = PY + 170                      # first solid row
s.raw('<defs><linearGradient id="fade-up" x1="0" y1="0" x2="0" y2="1">'
      f'<stop offset="0" stop-color="{CARD}" stop-opacity="1"/>'
      f'<stop offset="1" stop-color="{CARD}" stop-opacity="0"/></linearGradient></defs>')
s.g("more-beyond")
for c, nm in enumerate(ghost):
    bx = X2 + 32 + c * (CWd + CG)
    s.R(bx, R0 - 48, CWd, CHt, TRACK, 8, ' fill-opacity="0.7"')
    s.T(bx + CWd / 2, R0 - 24, nm, 14, 500, MUT, anchor="middle")
s.R(X2 + 24, R0 - 52, PW - 48, 46, "url(#fade-up)")
s.end()
s.g("what-moves-a-lane")
for r, names in enumerate(risks):
    for c, nm in enumerate(names):
        bx, by = X2 + 32 + c * (CWd + CG), R0 + r * 48
        s.R(bx, by, CWd, CHt, TRACK, 8)
        s.T(bx + CWd / 2, by + 24, nm, 14, 500, INK, anchor="middle")
        if r == 1:
            s.line(bx + CWd / 2, by + CHt, bx + CWd / 2, R0 + 104, INK, 0.22, 1.2)
s.end()
s.g("no-system-here")
s.R(X2 + 32, R0 + 104, PW - 64, 64, AMB, 12, f' fill-opacity="0.06" stroke="{AMB}" stroke-opacity="0.7" stroke-dasharray="6 6"')
s.T(X2 + PW / 2, R0 + 131, "NO SYSTEM HERE", 13, 600, AMB, anchor="middle", ls=2, mono=True)
s.T(X2 + PW / 2, R0 + 155, "Nothing reads these per booking.", 16, 400, MUT, anchor="middle")
s.end()
s.rule(PY + 372, 0.08, X2 + 32, PW - 64)
stat(X2 + 32, "26,225", "disruption alerts in 2025", "up from 22,522 in 2024", "Resilinc EventWatchAI")
stat(X2 + 440, "€120M", "a month on the Rhine", "if every box pays a €1,000 low-water surcharge", "2.3M TEU a year ÷ 12 ÷ 1.6 ≈ 120k boxes")
s.end()

s.g("closing")
s.T(M, 928, "Both jobs land on one desk. Neither has a system.", 34, 600, ls=-0.8)
s.T(W - M, 926, "Money figures are derived from the cited sources.", 12.5, 400, MUT, anchor="end")
s.end()
s.footer(3)
s.write("slide-03-the-what.svg")
