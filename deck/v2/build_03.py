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
panel(X1, "01", "The desk re-types the same facts.", "One booking number, one ETA. Six systems, six field names.", "problem-retyping")
BW, BH, GAP = 232, 96, 44
# The same two facts in every system, under a different field name each time.
REF, ETA = "HLCU-2261188", "10 Oct"
fields = {"Inbox": ("Subject ref", "Arrival"), "TMS": ("Job ref", "ETA"),
          "Carrier portal": ("Booking no.", "ETA POD"), "Customer": ("Your ref", "Arrival"),
          "Invoice": ("Our ref", "Arrival date"), "Customs": ("Declarant ref", "Arrival")}
rows = [["Inbox", "TMS", "Carrier portal"], ["Customer", "Invoice", "Customs"]]
pos = {}
for r, names in enumerate(rows):
    for c, nm in enumerate(names):
        bx, by = X1 + 32 + c * (BW + GAP), PY + 124 + r * 124
        pos[nm] = (bx, by)
        s.g("system-" + nm.lower().replace(" ", "-"))
        s.R(bx, by, BW, BH, BG, 10, f' stroke="{INK}" stroke-opacity="0.14"')
        s.T(bx + 14, by + 27, nm, 15, 600)
        for k, (lab, val, vw) in enumerate([(fields[nm][0], REF, 104), (fields[nm][1], ETA, 60)]):
            ry = by + 42 + k * 26
            s.T(bx + 14, ry + 15, lab, 12.5, 400, MUT)
            s.R(bx + BW - 12 - vw, ry, vw, 22, TRACK, 5)
            s.T(bx + BW - 12 - vw / 2, ry + 15, val, 12.5, 500, INK, anchor="middle")
        s.end()
s.g("handoffs")
for a, b in [("Inbox", "TMS"), ("TMS", "Carrier portal"), ("Customer", "Invoice"), ("Invoice", "Customs")]:
    (ax, ay), (bx, by) = pos[a], pos[b]
    s.line(ax + BW, ay + BH / 2, bx, by + BH / 2, AMB, 0.8, 1.5)
cx, cy = pos["Carrier portal"]
s.line(cx + BW / 2, cy + BH, cx + BW / 2, cy + 124, AMB, 0.8, 1.5)
s.end()
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
