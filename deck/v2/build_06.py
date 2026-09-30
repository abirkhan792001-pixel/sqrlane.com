#!/usr/bin/env python3
"""Slide 06 - The Job 2/2. Lanes break often, and the forwarder pays for it.
Map geometry is the product's own: data/geo.json and static/index.html's COAST."""
from kit import *
import json, re
ROOT = pathlib.Path(__file__).resolve().parents[2]
COAST = re.search(r'const COAST\s*=\s*"([^"]+)"', (ROOT / "static" / "index.html").read_text(encoding="utf-8")).group(1)
GEO = json.loads((ROOT / "data" / "geo.json").read_text(encoding="utf-8"))
FR = GEO["_frame"]
def proj(lat, lon):
    return ((lon - FR["lon0"]) / (FR["lon1"] - FR["lon0"]) * FR["width"],
            (FR["lat1"] - lat) / (FR["lat1"] - FR["lat0"]) * FR["height"])

s = Slide()
s.header("05 · THE JOB, 2 OF 2", "47 of 100 sailings arrive late.",
         "So the question is not whether a lane breaks. It is who pays, and how often.")
Y1, H1 = 306, 364
GREEN = "#0F7B3F"

# ---- the map
MX, MW = M, 820
s.g("one-lane-six-breaks")
s.card(MX, Y1, MW, H1)
s.T(MX + 28, Y1 + 40, "ONE LANE, SIX PLACES IT CAN BREAK", 13, 600, AMB, ls=1.4)
AX, AY, AW, AH = MX + 1, Y1 + 56, MW - 2, H1 - 100
# Fit the latitudes the lane needs to the card's height, then widen the
# longitude window to fill its width - no empty bands either side.
LAT0, LAT1, LONC = 28.6, 56.2, 12.0
_, ya = proj(LAT1, 0); _, yb = proj(LAT0, 0)
SC = AH / (yb - ya)
xc, _ = proj(0, LONC)
x0, y0 = max(0.0, xc - AW / 2 / SC), ya   # the coast data starts at the frame edge
OX, OY = AX, AY
def mp(lat, lon):
    x, y = proj(lat, lon); return OX + (x - x0) * SC, OY + (y - y0) * SC
s.raw(f'<defs><clipPath id="map-clip"><rect x="{AX}" y="{AY}" width="{AW}" height="{AH}"/></clipPath></defs>')
s.R(AX, AY, AW, AH, "#F2F4F5")
s.raw(f'<g clip-path="url(#map-clip)"><g id="coast" transform="translate({OX - x0*SC:.1f} {OY - y0*SC:.1f}) scale({SC:.4f})">'
      f'<path d="{COAST}" fill="#E4E4E1" stroke="#D2D2CE" stroke-width="{0.8/SC:.3f}"/></g>')
s.g("lane")
for name in ("redsea_to_suez", "suez_to_gibraltar", "suez_to_fos", "gibraltar_to_northsea"):
    pts = [mp(la, lo) for la, lo in GEO["corridors"][name]]
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    s.raw(f'<path d="{d}" fill="none" stroke="{AMB}" stroke-opacity="0.55" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
s.end()
BREAKS = [("RTM", "Rotterdam", "congestion", -12, -24, "end"), ("HAM", "Hamburg", "labour", 12, -8, "start"),
          ("ANR", "Antwerp", "congestion", -12, 16, "end"), ("RHINE", "Rhine", "low water", 12, 16, "start"),
          ("FOS", "Fos", "labour", 12, 14, "start"), ("SUEZ", "Suez", "conflict routing", -12, -8, "end")]
for pid, lab, why, dx, dy, anc in BREAKS:
    p = GEO["places"][pid]; x, y = mp(p["lat"], p["lon"])
    s.g("break-" + lab.lower())
    s.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{AMB}"/>')
    s.T(round(x + dx, 1), round(y + dy, 1), lab, 13, 600, INK, anchor=anc)
    s.T(round(x + dx, 1), round(y + dy + 16, 1), why, 12, 400, AMB, anchor=anc)
    s.end()
s.raw('</g>')
s.T(MX + 28, Y1 + H1 - 20, "None of these is unusual. All of them are on this one route.", 15, 400, MUT)
s.end()

# ---- a hundred sailings
PX, PW = MX + MW + 24, 400
s.g("a-hundred-sailings")
s.card(PX, Y1, PW, H1)
s.T(PX + 28, Y1 + 40, "A HUNDRED SAILINGS", 13, 600, MUT, ls=1.4)
CELL, GAP, GX, GY = 20, 4, PX + 28, Y1 + 62
for i in range(100):
    r, c = divmod(i, 10)
    s.R(GX + c * (CELL + GAP), GY + r * (CELL + GAP), CELL, CELL, AMB if i < 47 else TRACK, 4)
LX = GX + 10 * (CELL + GAP) + 14
s.R(LX, GY + 2, 12, 12, AMB, 3); s.T(LX + 20, GY + 13, "47 late", 14, 600)
s.R(LX, GY + 30, 12, 12, TRACK, 3); s.T(LX + 20, GY + 41, "53 on time", 14, 500, MUT)
s.T(PX + 28, Y1 + H1 - 42, "Schedule reliability, mid-2025.", 14, 500)
s.T(PX + 28, Y1 + H1 - 20, "It was 75 to 80% before 2020.", 14, 400, MUT)
s.end()

# ---- what eats it
EX, EW = PX + PW + 24, W - M - (PX + PW + 24)
s.g("what-eats-it")
s.card(EX, Y1, EW, H1)
s.T(EX + 28, Y1 + 40, "WHAT EATS IT", 13, 600, MUT, ls=1.4)
items = [("6 to 9%", "of global capacity pulled", "blank sailings and reroutes"),
         ("7 to 10 days", "added when a box is rolled", "to the next vessel with space"),
         ("2.4×", "swing in the spot rate", "$1,913 to $4,526 per 40ft"),
         ("€185", "a day once it sits at the port", "against €127 of margin")]
for k, (v, lab, sub) in enumerate(items):
    iy = Y1 + 84 + k * 62
    if k: s.rule(iy - 32, 0.07, EX + 28, EW - 56)
    s.T(EX + 28, iy, v, 24, 600, AMB, ls=-0.5)
    s.T(EX + 190, iy - 6, lab, 14, 500)
    s.T(EX + 190, iy + 12, sub, 12.5, 400, MUT)
s.T(EX + 28, Y1 + H1 - 20, "Every figure published, all 2025.", 12.5, 400, MUT)
s.end()

# ---- row 2: who pays, and should a forwarder care
Y2, H2 = Y1 + H1 + 20, 206
WX, WW = M, 820
s.g("who-owns-which-cost")
s.card(WX, Y2, WW, H2)
s.T(WX + 28, Y2 + 40, "WHO OWNS WHICH COST", 13, 600, MUT, ls=1.4)
cols = [("THE CUSTOMER", ["The carrier’s surcharge", "The higher freight rate", "The later arrival date"], False),
        ("THE FORWARDER", ["Storage while the box waits", "Re-booking and paperwork", "Clearing into a new country", "Every hour spent chasing it"], True)]
for i, (head, its, us) in enumerate(cols):
    cx = WX + 28 + i * 256
    s.T(cx, Y2 + 76, head, 12, 600, AMB if us else INK, ls=1.2)
    for k, it in enumerate(its):
        iy = Y2 + 104 + k * 24
        if us: s.raw(f'<circle cx="{cx + 4}" cy="{iy - 5}" r="3.5" fill="{AMB}"/>')
        else: s.raw(f'<circle cx="{cx + 4}" cy="{iy - 5}" r="3.2" fill="none" stroke="{MUT}" stroke-width="1.2"/>')
        s.T(cx + 16, iy, it, 14.5, 400)
s.line(WX + 540, Y2 + 62, WX + 540, Y2 + 182, INK, 0.1, 1)
s.T(WX + 564, Y2 + 104, "The contract decides", 18, 600)
s.T(WX + 564, Y2 + 128, "who pays.", 18, 600)
s.T(WX + 564, Y2 + 160, "The forwarder argues it", 14, 400, MUT)
s.T(WX + 564, Y2 + 180, "later, unpaid.", 14, 400, MUT)
s.end()

DX, DW = WX + WW + 24, W - M - (WX + WW + 24)
LIGHT, AMB_L = "#F5F5F0", "#F2B866"
s.g("should-a-forwarder-care")
s.R(DX, Y2, DW, H2, INK, 14)
s.T(DX + 28, Y2 + 40, "SO SHOULD A FORWARDER CARE", 13, 600, "#A3A39B", ls=1.4)
rows = [("Margin on a clean box", "+€127", 127, LIGHT), ("One day at the port", "−€185", 185, AMB_L), ("Five days sitting", "−€926", 926, AMB_L)]
for k, (lab, val, v, col) in enumerate(rows):
    ry = Y2 + 76 + k * 30
    s.T(DX + 28, ry, lab, 15, 400, LIGHT)
    s.R(DX + 260, ry - 11, round(420 * v / 926), 12, col, 3, ' fill-opacity="0.9"')
    s.T(DX + DW - 28, ry, val, 18, 600, col, anchor="end")
s.R(DX + 28, Y2 + 150, DW - 56, 1, LIGHT, 0, ' fill-opacity="0.15"')
s.T(DX + 28, Y2 + 184, "One day at the port costs more than a clean box earns. Five days undo seven.", 17, 600, LIGHT)
s.end()

s.T(M, 948, "It is not an edge case. It is the whole job.", 32, 600, ls=-0.7)
s.footer(6)
s.write("slide-06-the-job-2.svg")
