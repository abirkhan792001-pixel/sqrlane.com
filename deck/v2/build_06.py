#!/usr/bin/env python3
"""Slide 06 - The Job 2/2. One picture: where the lane breaks, who pays, and how
fast the margin goes. Map geometry is the product's own (data/geo.json + the
dashboard's COAST); the cost split is the one slide 05's original deck made."""
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

# ---- how often: a compact badge beside the headline
s.g("how-often")
BXR, BY0, C, G = W - M, 118, 9, 2
gx = BXR - 10 * (C + G) + G
for i in range(100):
    r, c = divmod(i, 10)
    s.R(gx + c * (C + G), BY0 + r * (C + G), C, C, AMB if i < 47 else MID, 1.5)
s.T(gx - 20, BY0 + 30, "47 late", 26, 600, AMB, anchor="end", ls=-0.5)
s.T(gx - 20, BY0 + 56, "53 on time, mid-2025", 14, 400, MUT, anchor="end")
s.T(gx - 20, BY0 + 78, "75 to 80% on time before 2020", 14, 400, MUT, anchor="end")
s.end()

YOU, CUST = "YOU", "CUSTOMER"
def tag(x, y, who):
    w = 42 if who == YOU else 82
    you = who == YOU
    s.R(x - w, y, w, 20, AMB if you else TRACK, 4, ' fill-opacity="0.16"' if you else "")
    s.T(x - w / 2, y + 14, who, 11, 700, AMB if you else MUT, anchor="middle", ls=0.8)

# ---- the lane, and who pays where it breaks
Y1, H1 = 306, 492
MX, MW = M, 1044
s.g("the-lane")
s.card(MX, Y1, MW, H1)
s.T(MX + 28, Y1 + 38, "ONE LANE, SIX PLACES IT BREAKS, AND WHO PAYS", 13, 600, AMB, ls=1.4)
AX, AY, AW, AH = MX + 1, Y1 + 54, MW - 2, H1 - 55
LON0, LON1, LAT0, LAT1 = -16.0, 126.0, 0.0, 58.5
x0, y0 = proj(LAT1, LON0); x1, y1 = proj(LAT0, LON1)
SC = min(AW / (x1 - x0), AH / (y1 - y0))
OX = AX + AW - (x1 - x0) * SC - 8; OY = AY
def mp(lat, lon):
    x, y = proj(lat, lon); return OX + (x - x0) * SC, OY + (y - y0) * SC
s.raw(f'<defs><clipPath id="map-clip"><rect x="{AX}" y="{AY}" width="{AW}" height="{AH}" rx="12"/></clipPath></defs>')
s.raw('<g clip-path="url(#map-clip)">')
s.R(AX, AY, AW, AH, "#F2F4F5")
s.raw(f'<g id="coast" transform="translate({OX - x0*SC:.1f} {OY - y0*SC:.1f}) scale({SC:.4f})">'
      f'<path d="{COAST}" fill="#E4E4E1" stroke="#D2D2CE" stroke-width="{0.8/SC:.3f}"/></g>')
s.g("lane")
for name in ("asia_to_malacca", "malacca_to_babelmandeb", "redsea_to_suez", "suez_to_gibraltar", "suez_to_fos", "gibraltar_to_northsea"):
    pts = [mp(la, lo) for la, lo in GEO["corridors"][name]]
    d = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(pts))
    s.raw(f'<path d="{d}" fill="none" stroke="{INK}" stroke-opacity="0.45" stroke-width="1.6" stroke-dasharray="1 4" stroke-linecap="round"/>')
s.end()
sh = GEO["places"]["Shanghai"]; sx, sy = mp(sh["lat"], sh["lon"])
s.raw(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="5" fill="{INK}"/>')
s.T(round(sx - 10, 1), round(sy - 12, 1), "Shanghai", 13, 600, anchor="end")

# callouts: place, what breaks, what it costs, who pays (the original deck's split)
CW, CH = 250, 58
calls = [
    ("HAM", "Hamburg", "labour", "€185 a day while it sits", YOU, (AX + 370, AY + 18)),
    ("RTM", "Rotterdam", "congestion", "rolled: +7 to 10 days, re-booked", YOU, (AX + 370, AY + 94)),
    ("ANR", "Antwerp", "congestion", "rerouted: customs in a new country", YOU, (AX + 370, AY + 170)),
    ("RHINE", "Rhine", "low water", "low-water surcharge per box", CUST, (AX + 640, AY + 18)),
    ("FOS", "Fos", "labour", "every hour spent chasing it", YOU, (AX + 640, AY + 94)),
    ("SUEZ", "Suez", "conflict routing", "6 to 9% capacity pulled, rates 2.4×", CUST, (AX + 640, AY + 250)),
]
pts = {pid: mp(GEO["places"][pid]["lat"], GEO["places"][pid]["lon"]) for pid, *_ in calls}
s.g("leaders")                       # all leaders first, so every card sits on top
for pid, name, what, cost, who, (cx, cy) in calls:
    px, py = pts[pid]
    s.raw(f'<path d="M{px:.1f} {py:.1f} L{cx:.1f} {cy + CH/2:.1f}" stroke="{AMB if who == YOU else MUT}" stroke-width="1.2" stroke-opacity="0.7" fill="none"/>')
s.end()
for pid, name, what, cost, who, (cx, cy) in calls:
    px, py = pts[pid]
    s.g("break-" + name.lower())
    s.R(cx, cy, CW, CH, CARD, 8, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(cx + 12, cy + 23, name, 14, 600)
    s.T(cx + 20 + len(name) * 8.4, cy + 23, what, 12.5, 400, MUT)
    s.T(cx + 12, cy + 44, cost, 13, 500, AMB if who == YOU else INK)
    tag(cx + CW - 10, cy + 8, who)
    s.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5.5" fill="{AMB if who == YOU else MUT}" stroke="{CARD}" stroke-width="1.5"/>')
    s.end()
s.raw('</g>')
s.end()

# ---- the margin falls, one box, day by day
FX, FW = MX + MW + 24, W - M - (MX + MW + 24)
s.g("the-margin-falls")
s.card(FX, Y1, FW, H1)
s.T(FX + 28, Y1 + 38, "THE MARGIN FALLS", 13, 600, AMB, ls=1.4)
s.T(FX + 28, Y1 + 64, "One clean box, then €185 a day at the port.", 15, 400, MUT)
days = [127 - 185 * d for d in range(6)]
# Polarity chart (dataviz skill): two validated hues, POS #3D72A8 / NEG amber,
# both pass lightness, chroma, CVD and contrast on the card surface. Values wear
# text tokens, not the bar colour, and only the story's three bars are labelled.
POS = "#3D72A8"
CX0, CX1, ZERO = FX + 44, FX + FW - 36, Y1 + 150
K = 0.33                                   # px per euro
step = (CX1 - CX0) / 6
BWID = 32
s.line(FX + 28, ZERO, FX + FW - 28, ZERO, INK, 0.35, 1.2)
s.T(FX + FW - 28, ZERO - 8, "break-even", 12, 400, MUT, anchor="end")
def col(x, v):
    """Column from the baseline: square at zero, 4px rounded at the data end."""
    h = abs(v) * K; r = 4; w = BWID
    if v > 0:
        d = f"M{x} {ZERO} V{ZERO-h+r} Q{x} {ZERO-h} {x+r} {ZERO-h} H{x+w-r} Q{x+w} {ZERO-h} {x+w} {ZERO-h+r} V{ZERO} Z"
    else:
        d = f"M{x} {ZERO} V{ZERO+h-r} Q{x} {ZERO+h} {x+r} {ZERO+h} H{x+w-r} Q{x+w} {ZERO+h} {x+w} {ZERO+h-r} V{ZERO} Z"
    s.raw(f'<path d="{d}" fill="{POS if v > 0 else AMB}"/>')
    return h
for d, v in enumerate(days):
    bx = round(CX0 + d * step + (step - BWID) / 2, 1)
    h = col(bx, v)
    if d in (0, 1, 5):
        lab = f"+€{v}" if v > 0 else f"−€{abs(v)}"
        ly = ZERO - h - 10 if v > 0 else ZERO + h + 20
        s.T(round(bx + BWID / 2, 1), round(ly, 1), lab, 15, 600, INK, anchor="middle")
    s.T(round(bx + BWID / 2, 1), Y1 + H1 - 20, "clean" if d == 0 else f"day {d}", 12.5, 600 if d == 0 else 500, MUT, anchor="middle")
s.T(FX + FW - 28, ZERO - 34, "under water from day one", 15, 600, INK, anchor="end")

s.end()

# ---- who pays, and the close
s.g("who-pays")
LY = Y1 + H1 + 42
tag(M + 42, LY - 15, YOU)
s.T(M + 54, LY, "storage, re-booking, clearing, chasing: 4 of the 6", 15, 500)
tag(M + 640, LY - 15, CUST)
s.T(M + 652, LY, "surcharges, the higher rate, the later date", 15, 400, MUT)
s.T(W - M, LY, "Published figures, 2025 · margin: K+N FY25", 12.5, 400, MUT, anchor="end")
s.end()
s.T(M, 942, "It is not an edge case. It is the whole job.", 34, 600, ls=-0.8)
s.footer(6)
s.write("slide-06-the-job-2.svg")
