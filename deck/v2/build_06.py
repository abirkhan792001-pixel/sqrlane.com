#!/usr/bin/env python3
"""Slide 06 - The Job 2/2. Lanes break often, and most of the cost lands on the
forwarder. Map geometry is the product's own (data/geo.json + the dashboard's
COAST). Sources are kept below for the appendix; they are not drawn here."""
from kit import *
import json, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
COAST = re.search(r'const COAST\s*=\s*"([^"]+)"', (ROOT / "static" / "index.html").read_text(encoding="utf-8")).group(1)
GEO = json.loads((ROOT / "data" / "geo.json").read_text(encoding="utf-8"))
FR = GEO["_frame"]
def proj(lat, lon):
    return ((lon - FR["lon0"]) / (FR["lon1"] - FR["lon0"]) * FR["width"],
            (FR["lat1"] - lat) / (FR["lat1"] - FR["lat0"]) * FR["height"])

# For the appendix slide - every figure on this slide, traced.
SOURCES = [
    "Sea-Intelligence, Global Liner Performance, Aug 2026: 49.9% on time; 2018 to 2019 average 74%",
    "ING Think and Freightos: the Red Sea detour absorbs 6 to 9% of global fleet capacity",
    "Drewry World Container Index: $1,913 to $4,526 per 40ft",
    "Rolled cargo moves to the next sailing, usually a week later (Shapiro, Vizion)",
    "Hapag-Lloyd Germany import tariff, 40ft: EUR 115 a day after 3 free days, EUR 180 later",
    "Kuehne+Nagel Sea Logistics FY25: EUR 127 margin per clean box (slide 05)",
    "ING and gCaptain, Aug 2026: low-water surcharges on the Rhine",
]

s = Slide()
s.header("05 · THE JOB, 2 OF 2", "Half of all sailings arrive late.",
         "And when a box is late, most of the cost lands on the forwarder.")
SLATE = "#8A8A84"          # customer-pays pins: quiet, so the forwarder's amber leads

# ---- how often
s.g("how-often")
BXR, BY0, C, G = W - M, 118, 9, 2
gx = BXR - 10 * (C + G) + G
for i in range(100):
    r, c = divmod(i, 10)
    s.R(gx + c * (C + G), BY0 + r * (C + G), C, C, AMB if i < 50 else MID, 1.5)
s.T(gx - 20, BY0 + 30, "50 of 100 late", 26, 600, AMB, anchor="end", ls=-0.5)
s.T(gx - 20, BY0 + 56, "49.9% on time in August 2026", 14, 400, MUT, anchor="end")
s.T(gx - 20, BY0 + 78, "74% on time before the pandemic", 14, 400, MUT, anchor="end")
s.end()

Y1, H1 = 306, 300
Y2, H2 = Y1 + H1 + 20, 262
LW = 1000
RX, RW = M + LW + 24, W - M - (M + LW + 24)

# ---- the lane, lean: a pin and two words per problem
s.g("the-lane")
s.card(M, Y1, LW, H1)
s.T(M + 28, Y1 + 38, "ONE TRIP, SIX PLACES IT GOES WRONG", 13, 600, AMB, ls=1.4)
lx = M + LW - 28
s.raw(f'<circle cx="{lx - 238}" cy="{Y1 + 33}" r="5" fill="{AMB}"/>'); s.T(lx - 228, Y1 + 38, "forwarder pays", 13, 500, INK)
s.raw(f'<circle cx="{lx - 104}" cy="{Y1 + 33}" r="5" fill="{SLATE}"/>'); s.T(lx - 94, Y1 + 38, "customer pays", 13, 500, MUT)
AX, AY, AW, AH = M + 1, Y1 + 54, LW - 2, H1 - 55
LAT0, LAT1, LONC = 26.8, 56.6, 17.0
_, ya = proj(LAT1, 0); _, yb = proj(LAT0, 0)
SC = AH / (yb - ya)
xc, _ = proj(0, LONC)
x0, y0 = xc - AW / 2 / SC, ya
def mp(lat, lon):
    x, y = proj(lat, lon); return AX + (x - x0) * SC, AY + (y - y0) * SC
s.raw(f'<defs><clipPath id="map-clip"><rect x="{AX}" y="{AY}" width="{AW}" height="{AH}" rx="12"/></clipPath></defs>')
s.raw('<g clip-path="url(#map-clip)">')
s.R(AX, AY, AW, AH, "#F2F4F5")
s.raw(f'<g id="coast" transform="translate({AX - x0*SC:.1f} {AY - y0*SC:.1f}) scale({SC:.4f})">'
      f'<path d="{COAST}" fill="#E4E4E1" stroke="#D2D2CE" stroke-width="{0.8/SC:.3f}"/></g>')
s.g("lane")
for name in ("redsea_to_suez", "suez_to_gibraltar", "suez_to_fos", "gibraltar_to_northsea"):
    pts = [mp(la, lo) for la, lo in GEO["corridors"][name]]
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    s.raw(f'<path d="{d}" fill="none" stroke="{INK}" stroke-opacity="0.4" stroke-width="1.6" stroke-dasharray="1 4" stroke-linecap="round"/>')
s.end()
sx, sy = mp(GEO["places"]["SUEZ"]["lat"], GEO["places"]["SUEZ"]["lon"])
PINS = [("RTM", "Rotterdam", "too busy", True, -14, -20, "end"),
        ("ANR", "Antwerp", "rerouted", True, -14, 24, "end"),
        ("HAM", "Hamburg", "strike", True, 12, -6, "start"),
        ("RHINE", "Rhine", "river too low", False, 12, 18, "start"),
        ("FOS", "Fos", "strike", True, 12, 16, "start"),
        ("SUEZ", "Suez", "conflict nearby", False, -12, -6, "end")]
for pid, name, what, fwd, dx, dy, anc in PINS:
    p = GEO["places"][pid]; x, y = mp(p["lat"], p["lon"])
    s.g("pin-" + name.lower())
    s.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6.5" fill="{AMB if fwd else SLATE}" stroke="#F2F4F5" stroke-width="2"/>')
    s.T(round(x + dx, 1), round(y + dy, 1), name, 14, 600, anchor=anc)
    s.T(round(x + dx, 1), round(y + dy + 17, 1), what, 13, 500, AMB if fwd else MUT, anchor=anc)
    s.end()
s.raw('</g>')
s.end()

# ---- what eats it: the four numbers that matter, in plain words
s.g("what-eats-it")
s.card(RX, Y1, RW, H1)
s.T(RX + 28, Y1 + 38, "WHAT A LATE BOX COSTS", 13, 600, MUT, ls=1.4)
eats = [("€115", "a day while the box waits at the port", "against €127 earned on the whole box"),
        ("+7 days", "when a box is bumped to the next ship", "the next weekly sailing"),
        ("2.4×", "swing in the price of one container", "$1,913 to $4,526 per 40ft"),
        ("6 to 9%", "of the world’s ship capacity lost", "to the Red Sea detour")]
for k, (v, lab, sub) in enumerate(eats):
    iy = Y1 + 88 + k * 56
    if k: s.rule(iy - 32, 0.07, RX + 28, RW - 56)
    s.T(RX + 28, iy, v, 26, 600, AMB, ls=-0.6)
    s.T(RX + 176, iy - 6, lab, 15, 500)
    s.T(RX + 176, iy + 13, sub, 13, 400, MUT)
s.end()

# ---- who owns which cost
s.g("who-owns-which-cost")
s.card(M, Y2, LW, H2)
s.T(M + 28, Y2 + 38, "WHO PAYS FOR IT", 13, 600, MUT, ls=1.4)
cols = [("THE FORWARDER", ["Storage while the box waits", "Re-booking and paperwork", "Customs in a new country", "Every hour spent chasing it"], True),
        ("THE CUSTOMER", ["The carrier’s surcharge", "The higher freight price", "The later arrival date"], False)]
for i, (head, its, fwd) in enumerate(cols):
    cx = M + 28 + i * 300
    s.T(cx, Y2 + 74, head, 12, 700, AMB if fwd else MUT, ls=1.2)
    for k, it in enumerate(its):
        iy = Y2 + 104 + k * 28
        if fwd: s.raw(f'<circle cx="{cx + 4}" cy="{iy - 5}" r="4" fill="{AMB}"/>')
        else: s.raw(f'<circle cx="{cx + 4}" cy="{iy - 5}" r="3.5" fill="none" stroke="{SLATE}" stroke-width="1.4"/>')
        s.T(cx + 18, iy, it, 16, 500 if fwd else 400, INK if fwd else MUT)
s.line(M + 640, Y2 + 60, M + 640, Y2 + H2 - 28, INK, 0.1, 1)
s.T(M + 668, Y2 + 104, "The contract decides", 21, 600, ls=-0.3)
s.T(M + 668, Y2 + 132, "who pays.", 21, 600, ls=-0.3)
s.T(M + 668, Y2 + 168, "The forwarder argues it", 15, 400, MUT)
s.T(M + 668, Y2 + 190, "later, unpaid.", 15, 400, MUT)
s.end()

# ---- what the forwarder keeps on one box
s.g("what-the-forwarder-keeps")
s.card(RX, Y2, RW, H2)
s.T(RX + 28, Y2 + 38, "WHAT THE FORWARDER KEEPS ON ONE BOX", 13, 600, AMB, ls=1.4)
POS = "#3D72A8"      # polarity pair validated with the dataviz skill (all checks pass)
days = [127 - 115 * d for d in range(6)]
ZERO, K, BW_ = Y2 + 104, 0.20, 30
c0, c1 = RX + 36, RX + RW - 28
step = (c1 - c0) / 6
s.line(RX + 28, ZERO, RX + RW - 28, ZERO, INK, 0.3, 1.2)
s.T(RX + RW - 28, ZERO - 8, "€0", 12, 600, MUT, anchor="end")
s.T(RX + RW - 28, ZERO - 30, "a loss from day two", 15, 600, anchor="end")
for d, v in enumerate(days):
    bx = round(c0 + d * step + (step - BW_) / 2, 1); h = abs(v) * K; r = 4
    if v > 0:
        dpath = f"M{bx} {ZERO} V{ZERO-h+r} Q{bx} {ZERO-h} {bx+r} {ZERO-h} H{bx+BW_-r} Q{bx+BW_} {ZERO-h} {bx+BW_} {ZERO-h+r} V{ZERO} Z"
    else:
        dpath = f"M{bx} {ZERO} V{ZERO+h-r} Q{bx} {ZERO+h} {bx+r} {ZERO+h} H{bx+BW_-r} Q{bx+BW_} {ZERO+h} {bx+BW_} {ZERO+h-r} V{ZERO} Z"
    s.raw(f'<path d="{dpath}" fill="{POS if v > 0 else AMB}"/>')
    if d in (0, 2, 5):
        lab = f"+€{v}" if v > 0 else f"−€{abs(v)}"
        ly = ZERO - h - 8 if v > 0 else ZERO + h + 18
        s.T(round(bx + BW_ / 2, 1), round(ly, 1), lab, 14, 600, anchor="middle")
    s.T(round(bx + BW_ / 2, 1), Y2 + H2 - 14, "on time" if d == 0 else f"day {d}", 12.5, 600 if d == 0 else 500, MUT, anchor="middle")
s.end()

s.T(M, 944, "It is not an edge case. It is the whole job.", 32, 600, ls=-0.7)
s.footer(6)
s.write("slide-06-the-job-2.svg")
