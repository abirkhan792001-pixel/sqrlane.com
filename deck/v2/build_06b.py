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
def ref(n):
    """A source marker: small grey superscript, keyed to the list at the foot."""
    return ""   # sources live in the appendix (build_06.py SOURCES)
s.header("05 · THE JOB, 2 OF 2", "Half of all sailings arrive late.",
         "And when a box is late, most of the cost lands on the forwarder.")

# ---- how often: a compact badge beside the headline
s.g("how-often")
BXR, BY0, C, G = W - M, 118, 9, 2
gx = BXR - 10 * (C + G) + G
for i in range(100):
    r, c = divmod(i, 10)
    s.R(gx + c * (C + G), BY0 + r * (C + G), C, C, AMB if i < 50 else MID, 1.5)
s.T(gx - 20, BY0 + 30, "50 of 100 late" + ref(1), 26, 600, AMB, anchor="end", ls=-0.5)
s.T(gx - 20, BY0 + 56, "49.9% on time in August 2026", 14, 400, MUT, anchor="end")
s.T(gx - 20, BY0 + 78, "74% on time before the pandemic", 14, 400, MUT, anchor="end")
s.end()

YOU, CUST = "FORWARDER PAYS", "CUSTOMER PAYS"
def tag(x, y, who, short=False):
    label = who.split()[0] if short else who
    w = (84 if who == YOU else 76) if short else (112 if who == YOU else 106)
    you = who == YOU
    s.R(x - w, y, w, 20, AMB if you else TRACK, 4, ' fill-opacity="0.16"' if you else "")
    s.T(x - w / 2, y + 14, label, 11, 700, AMB if you else MUT, anchor="middle", ls=0.8)

# ---- the lane, and who pays where it breaks
Y1, H1 = 306, 446
MX, MW = M, 1044
s.g("the-lane")
s.card(MX, Y1, MW, H1)
s.T(MX + 28, Y1 + 38, "ONE TRIP, SIX PLACES IT GOES WRONG, AND WHO PAYS", 13, 600, AMB, ls=1.4)
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
CW, CH = 262, 58
calls = [
    ("HAM", "Hamburg", "strike", "box waits: €115 a day" + ref(5), YOU, (AX + 404, AY + 18)),
    ("RTM", "Rotterdam", "too busy", "bumped to a later ship: +7 days" + ref(4), YOU, (AX + 404, AY + 94)),
    ("ANR", "Antwerp", "rerouted", "customs paperwork starts again", YOU, (AX + 404, AY + 170)),
    ("RHINE", "Rhine", "river too low", "extra charge on every box" + ref(7), CUST, (AX + 684, AY + 18)),
    ("FOS", "Fos", "strike", "hours spent chasing updates", YOU, (AX + 684, AY + 94)),
    ("SUEZ", "Suez", "conflict nearby", "fewer ships, prices up to 2.4×" + ref("2,3"), CUST, (AX + 684, AY + 250)),
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
    tag(cx + CW - 10, cy + 8, who, short=True)
    s.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5.5" fill="{AMB if who == YOU else MUT}" stroke="{CARD}" stroke-width="1.5"/>')
    s.end()
s.raw('</g>')
s.end()

# ---- the margin falls, one box, day by day
FX, FW = MX + MW + 24, W - M - (MX + MW + 24)
s.g("the-margin-falls")
s.card(FX, Y1, FW, H1)
s.T(FX + 28, Y1 + 38, "WHAT THE FORWARDER KEEPS ON ONE BOX", 13, 600, AMB, ls=1.4)
s.T(FX + 28, Y1 + 64, "€127 when all goes well, then €115 for every day it waits." + ref("6,5"), 15, 400, MUT)
days = [127 - 115 * d for d in range(6)]
# Polarity chart (dataviz skill): two validated hues, POS #3D72A8 / NEG amber,
# both pass lightness, chroma, CVD and contrast on the card surface. Values wear
# text tokens, not the bar colour, and only the story's three bars are labelled.
POS = "#3D72A8"
CX0, CX1, ZERO = FX + 44, FX + FW - 36, Y1 + 176
K = 0.46                                   # px per euro
step = (CX1 - CX0) / 6
BWID = 32
s.line(FX + 28, ZERO, FX + FW - 28, ZERO, INK, 0.35, 1.2)
s.T(FX + FW - 28, ZERO - 8, "€0", 12, 600, MUT, anchor="end")
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
    if d in (0, 1, 2, 5):
        lab = f"+€{v}" if v > 0 else f"−€{abs(v)}"
        ly = ZERO - h - 10 if v > 0 else ZERO + h + 20
        s.T(round(bx + BWID / 2, 1), round(ly, 1), lab, 15, 600, INK, anchor="middle")
    s.T(round(bx + BWID / 2, 1), Y1 + H1 - 20, "on time" if d == 0 else f"{d} day" + ("" if d == 1 else "s") + " late", 12.5, 600 if d == 0 else 500, MUT, anchor="middle")
s.T(FX + FW - 28, ZERO - 34, "a loss from day two", 15, 600, INK, anchor="end")

s.end()

# ---- who pays, and the close
s.g("who-pays")
LY = Y1 + H1 + 34
tag(M + 112, LY - 15, YOU)
s.T(M + 124, LY, "storage, re-booking, customs paperwork, chasing: 4 of the 6", 15, 500)
tag(M + 820, LY - 15, CUST)
s.T(M + 832, LY, "surcharges and higher prices", 15, 400, MUT)
s.T(W - M, LY, "Typical contract split. Contracts vary.", 13, 400, MUT, anchor="end")
s.end()
# What a late box costs: the four takeaways, as one slim strip
s.g("what-a-late-box-costs")
TY0, TH0 = LY + 22, 62
tiles = [("€115", "a day while the box waits", "against €127 earned on the box"),
         ("+7 days", "when it is bumped to the next ship", "the next weekly sailing"),
         ("2.4×", "swing in the price of one container", "$1,913 to $4,526 per 40ft"),
         ("6 to 9%", "of the world’s ship capacity lost", "to the Red Sea detour")]
TW = (W - 2 * M - 3 * 16) / 4
for k, (v, lab, sub) in enumerate(tiles):
    tx = M + k * (TW + 16)
    s.R(round(tx, 1), TY0, round(TW, 1), TH0, CARD, 10, f' stroke="{INK}" stroke-opacity="0.1"')
    s.T(round(tx + 20, 1), TY0 + 40, v, 26, 600, AMB, ls=-0.6)
    vx = tx + 20 + max(78, len(v) * 15.5)
    s.T(round(vx, 1), TY0 + 27, lab, 14.5, 500)
    s.T(round(vx, 1), TY0 + 46, sub, 12.5, 400, MUT)
s.end()
# The close: the claim, then what one bottleneck costs. 3.5x is derived from the
# chart above (EUR 448 lost after five days / EUR 127 earned), so it shows its sum.
s.g("close")
s.T(M, 920, "It is not an edge case. It is the whole job.", 30, 600, ls=-0.7)
s.T(M, 956, 'One bottleneck, five days of waiting, and the forwarder loses '
    f'<tspan fill="{AMB}" font-weight="600">3.5×</tspan> what the box earns.', 21, 500, MUT, ls=-0.2)
s.T(W - M, 956, "€448 lost against €127 earned, from the chart above", 13, 400, MUT, anchor="end")
s.end()
s.footer(6)
s.write("slide-06-the-job-2-b.svg")
