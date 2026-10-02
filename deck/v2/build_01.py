#!/usr/bin/env python3
"""Slide 01 - the cover. The desk and the lane, landing on one TMS record, with
the lane drawn on the map it actually runs over.

The map is real geography: Natural Earth 50m countries and 10m river
centrelines (public domain), projected here and inlined as paths, so the SVG
stays self-contained and Figma-editable. The files are cached in
tools/.ne-cache/ (gitignored), the same cache tools/build_rhine_map.py uses;
the first run fetches them.

Every place on it is where data/geo.json says it is, and the four signals are
the four authored scenarios' own places: the Hamburg strike, Rotterdam's gusts
(read for HAM/RTM/ANR/FOS), the Kaub gauge and the Rhone wildfire. The record
on the right is SHP-001 under the Hamburg strike: rerouted to Rotterdam, +2
days, the carrier mail drafted, queued for a person.

    cd deck/v2 && python3 build_01.py && cd .. && python3 render.py v2/slide-01-cover.svg
"""
import json, math, pathlib, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / "tools" / ".ne-cache"
NE = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/")
LAYERS = {"ne_countries.geojson": "ne_50m_admin_0_countries.geojson",
          "ne_rivers_world.geojson": "ne_10m_rivers_lake_centerlines.geojson"}
GEO = json.loads((ROOT / "data" / "geo.json").read_text(encoding="utf-8"))["places"]

W, H, M = 1920, 1080, 96
BG, INK, MUT, AMB = "#F2EAE0", "#0A0A0A", "#6E6E66", "#96580A"
CARD, LAND, BORDER, RIVER = "#FBF8F3", "#E6DCCF", "#D6C9B8", "#C9D1D0"
TOP_RULE, BOTTOM_RULE = 144, 928

# The record's two field groups set the height of the two tracks, so the arrows
# land on the middle field of each group.
DESK_Y, LANE_Y = 296, 524
NODE_X = 1362                      # both agent nodes stand on one vertical
CARD_X, CARD_Y, CARD_W, CARD_H = 1564, 176, 260, 524


def fetch():
    CACHE.mkdir(parents=True, exist_ok=True)
    for local, remote in LAYERS.items():
        p = CACHE / local
        if not p.exists():
            print("fetching", remote)
            urllib.request.urlretrieve(NE + remote, p)
    return {k: json.loads((CACHE / k).read_text(encoding="utf-8")) for k in LAYERS}


# ---- projection: equirectangular with a cos(latitude) correction, as the
# Rhine corridor map does. Plain equirectangular at this scale stretches
# Europe east-west and the Netherlands comes out visibly too wide.
K = 23.0                                       # px per degree of longitude
KY = K / math.cos(math.radians(50.5))          # px per degree of latitude
RTM = GEO["RTM"]
AX, AY = 1176, 500                             # where Rotterdam sits on the slide


def P(lon, lat):
    return AX + (lon - RTM["lon"]) * K, AY - (lat - RTM["lat"]) * KY


def place(pid):
    p = GEO[pid]
    return P(p["lon"], p["lat"])


# The map's window: between the two rules, from behind the hero to the bleed.
MX0, MY0, MX1, MY1 = 700, TOP_RULE + 1, W, BOTTOM_RULE


def clip_poly(pts, x0, y0, x1, y1):
    """Sutherland-Hodgman against a rectangle. The clip path hides everything
    outside anyway; this only keeps the inlined path data small."""
    def clip(pts, inside, cut):
        out = []
        for i, cur in enumerate(pts):
            prev = pts[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cut(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cut(prev, cur))
        return out
    def at_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def at_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    for inside, cut in ((lambda p: p[0] >= x0, at_x(x0)), (lambda p: p[0] <= x1, at_x(x1)),
                        (lambda p: p[1] >= y0, at_y(y0)), (lambda p: p[1] <= y1, at_y(y1))):
        if not pts:
            break
        pts = clip(pts, inside, cut)
    return pts


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    worst, wi = -1.0, 0
    for i in range(1, len(pts) - 1):
        p = pts[i]
        d = (abs(dy * p[0] - dx * p[1] + b[0] * a[1] - b[1] * a[0]) / n if n
             else math.hypot(p[0] - a[0], p[1] - a[1]))
        if d > worst:
            worst, wi = d, i
    if worst <= eps:
        return [a, b]
    return rdp(pts[:wi + 1], eps)[:-1] + rdp(pts[wi:], eps)


def d_of(pts, close):
    s = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return s + ("Z" if close else "")


def land_paths(countries):
    pad = 6
    out = []
    for f in countries["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly:
                pts = [P(lon, lat) for lon, lat in ring]
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                if max(xs) < MX0 or min(xs) > MX1 or max(ys) < MY0 or min(ys) > MY1:
                    continue
                pts = clip_poly(pts, MX0 - pad, MY0 - pad, MX1 + pad, MY1 + pad)
                pts = rdp(pts + [pts[0]], 0.45)[:-1] if len(pts) > 2 else pts
                if len(pts) > 2:
                    out.append(d_of(pts, True))
    return out


RIVERS = {"Rhine": ("Rhine", "Rhein", "Rhin"), "Elbe": ("Elbe",), "Rhone": ("Rhône", "Rhne")}


def river_paths(rivers):
    out = []
    for f in rivers["features"]:
        name = f["properties"].get("name") or ""
        if not any(name in alts for alts in RIVERS.values()):
            continue
        g = f["geometry"]
        lines = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in lines:
            run = []
            for lon, lat in line:
                x, y = P(lon, lat)
                if MX0 - 20 <= x <= MX1 + 20 and MY0 - 20 <= y <= MY1 + 20:
                    run.append((x, y))
                elif run:
                    if len(run) > 1:
                        out.append(d_of(rdp(run, 0.4), False))
                    run = []
            if len(run) > 1:
                out.append(d_of(rdp(run, 0.4), False))
    return out


def smooth(pts, t=0.5):
    """Catmull-Rom through the waypoints, as cubic Beziers: a sea lane is a
    curve, and straight segments between waypoints read as a drawn polygon."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 3, p1[1] + (p2[1] - p0[1]) * t / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 3, p2[1] - (p3[1] - p1[1]) * t / 3)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


# ---- text measuring, so pills fit their words. Geist's own advance widths.
try:
    from fontTools.ttLib import TTFont
    _FONT = TTFont(ROOT / "static" / "fonts" / "Geist-Variable.woff2")
    _CMAP, _HMTX, _UPM = _FONT.getBestCmap(), _FONT["hmtx"], _FONT["head"].unitsPerEm
except Exception:                      # no fontTools: a fair average instead
    _FONT = None


def width(s, size, weight=400):
    if _FONT is None:
        return len(s) * size * 0.52
    adv = sum(_HMTX[_CMAP.get(ord(c), _CMAP[ord("n")])][0] for c in s)
    return adv / _UPM * size * (1 + (weight - 400) / 4000)


# ---- the SVG
o = []
def raw(s): o.append(s)
def T(x, y, s, size, weight=400, fill=INK, anchor="start", ls=0, mono=False, extra=""):
    fam = "Geist Mono" if mono else "Geist"
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    raw(f'<text x="{x:g}" y="{y:g}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}"{a}{l}{extra}>{s}</text>')
def g(name): raw(f'<g id="{name}">')
def end(): raw("</g>")


def pill(x, y, w, label, tone="desk", h=28):
    """One chip. desk: a filled mail chip. signal: quieter. active: amber."""
    fill, fo, stroke, so, dot, ink = {
        "desk":   ("#D9CFC2", 1, INK, 0.10, MUT, INK),
        "signal": (CARD, 1, INK, 0.12, MUT, MUT),
        "active": ("#EBDCC6", 1, AMB, 0.45, AMB, AMB),
    }[tone]
    raw(f'<rect x="{x:g}" y="{y - h / 2:g}" width="{w:g}" height="{h}" rx="{h / 2:g}" fill="{fill}" '
        f'stroke="{stroke}" stroke-opacity="{so}" filter="url(#chip-shadow)"/>')
    raw(f'<circle cx="{x + 16:g}" cy="{y:g}" r="3" fill="{dot}"/>')
    T(x + 28, y + 4.5, label, 13.5, 500, ink)


def node(cx, cy, caption, caption_dy=40):
    raw(f'<rect x="{cx - 20}" y="{cy - 20}" width="40" height="40" rx="10" fill="{INK}" filter="url(#node-shadow)"/>')
    raw(f'<path d="M{cx - 10} {cy + 8}h20 M{cx - 10} {cy}h13 M{cx - 10} {cy - 8}h7" stroke="{BG}" '
        f'stroke-width="2.6" stroke-linecap="round" fill="none"/>')
    T(cx, cy + caption_dy, caption, 11, 500, MUT, "middle", 1.4, True)


def arrow(x0, x1, y, caption):
    raw(f'<path d="M{x0} {y} H{x1 - 10}" stroke="{INK}" stroke-width="2" fill="none"/>')
    raw(f'<path d="M{x1 - 10} {y - 6} L{x1} {y} L{x1 - 10} {y + 6} Z" fill="{INK}"/>')
    T((x0 + x1 - 10) / 2, y - 12, caption, 11, 500, MUT, "middle", 1.2, True)


def shadow(fid, dy, blur, alpha):
    return (f'<filter id="{fid}" x="-30%" y="-40%" width="160%" height="200%" color-interpolation-filters="sRGB">'
            f'<feFlood flood-opacity="0" result="BackgroundImageFix"/>'
            f'<feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha"/>'
            f'<feOffset dy="{dy}"/><feGaussianBlur stdDeviation="{blur}"/>'
            f'<feComposite in2="hardAlpha" operator="out"/>'
            f'<feColorMatrix type="matrix" values="0 0 0 0 0.24 0 0 0 0 0.18 0 0 0 0 0.11 0 0 0 {alpha} 0"/>'
            f'<feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow"/>'
            f'<feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow" result="shape"/></filter>')


ne = fetch()
raw(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
raw("<defs>")
raw(f'<clipPath id="map-clip"><rect x="{MX0}" y="{MY0}" width="{MX1 - MX0}" height="{MY1 - MY0}"/></clipPath>')
raw(f'<linearGradient id="fade-left" x1="{MX0}" y1="0" x2="{MX0 + 300}" y2="0" gradientUnits="userSpaceOnUse">'
    f'<stop offset="0" stop-color="{BG}"/><stop offset="0.45" stop-color="{BG}" stop-opacity="0.7"/>'
    f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>')
raw(f'<linearGradient id="fade-top" x1="0" y1="{MY0}" x2="0" y2="{MY0 + 250}" gradientUnits="userSpaceOnUse">'
    f'<stop offset="0" stop-color="{BG}"/><stop offset="0.55" stop-color="{BG}" stop-opacity="0.6"/>'
    f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>')
raw(f'<linearGradient id="fade-bottom" x1="0" y1="{MY1 - 90}" x2="0" y2="{MY1}" gradientUnits="userSpaceOnUse">'
    f'<stop offset="0" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}"/></linearGradient>')
raw(shadow("chip-shadow", 1, 1.5, 0.10))
raw(shadow("node-shadow", 4, 6, 0.22))
raw(shadow("card-shadow", 14, 22, 0.14))
raw("</defs>")
raw(f'<rect id="background" width="{W}" height="{H}" fill="{BG}"/>')

# ---- the map, under everything on the right
g("map")
raw('<g clip-path="url(#map-clip)">')
raw(f'<path id="land" d="{" ".join(land_paths(ne["ne_countries.geojson"]))}" fill="{LAND}" '
    f'stroke="{BORDER}" stroke-width="0.9" stroke-linejoin="round" fill-rule="nonzero"/>')
raw(f'<path id="rivers" d="{" ".join(river_paths(ne["ne_rivers_world.geojson"]))}" fill="none" '
    f'stroke="{RIVER}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')

# The lane: SHP-001's sea leg, Shanghai to Hamburg, as the corridor waypoints in
# data/geo.json carry it up the Atlantic and through the Channel. The planned
# last leg into Hamburg is the one the strike breaks; the reroute ends in
# Rotterdam, which is what the record says: the solid leg ends there, and the
# leg it would have sailed on to Hamburg is drawn dashed, in the strike's amber.
SEA = [(-11.2, 40.0), (-9.8, 43.6), (-6.4, 48.3), (-3.5, 49.6), (-1.0, 50.15), (1.4, 50.95), (3.0, 51.6)]
TO_RTM = [(3.0, 51.6), (3.6, 51.85), (GEO["RTM"]["lon"], GEO["RTM"]["lat"])]
TO_HAM = [(GEO["RTM"]["lon"], GEO["RTM"]["lat"]), (4.3, 52.5), (5.2, 53.4), (7.0, 54.0), (8.7, 53.9),
          (GEO["HAM"]["lon"], GEO["HAM"]["lat"])]
g("lane")
raw(f'<path id="lane-sea" d="{smooth([P(*p) for p in SEA])}" fill="none" stroke="{INK}" stroke-opacity="0.55" '
    f'stroke-width="1.8" stroke-dasharray="1 5" stroke-linecap="round"/>')
raw(f'<path id="lane-planned-hamburg" d="{smooth([P(*p) for p in TO_HAM])}" fill="none" stroke="{AMB}" '
    f'stroke-opacity="0.75" stroke-width="1.8" stroke-dasharray="6 5" stroke-linecap="round"/>')
raw(f'<path id="lane-reroute-rotterdam" d="{smooth([P(*p) for p in TO_RTM])}" fill="none" stroke="{INK}" '
    f'stroke-width="2.4" stroke-linecap="round"/>')
end()
raw("</g>")
raw(f'<rect id="map-fade-left" x="{MX0}" y="{MY0}" width="300" height="{MY1 - MY0}" fill="url(#fade-left)"/>')
raw(f'<rect id="map-fade-top" x="{MX0}" y="{MY0}" width="{MX1 - MX0}" height="250" fill="url(#fade-top)"/>')
raw(f'<rect id="map-fade-bottom" x="{MX0}" y="{MY1 - 90}" width="{MX1 - MX0}" height="90" fill="url(#fade-bottom)"/>')
end()

# ---- top bar
g("top-bar")
raw(f'<g id="mark"><rect x="{M}" y="80" width="32" height="32" rx="8" fill="{INK}"/>'
    f'<path d="M104 104h16 M104 97h11 M104 90h6" stroke="{BG}" stroke-width="2.4" stroke-linecap="round" fill="none"/></g>')
T(144, 103, "sqrlane.com", 20, 500)
T(W - M, 102, "CONFIDENTIAL · FOR REVIEW PURPOSES ONLY · NOT FOR PRESENTATION", 14.5, 400, MUT, "end", 0.4)
raw(f'<rect id="top-rule" x="{M}" y="{TOP_RULE}" width="{W - 2 * M}" height="1" fill="{INK}" fill-opacity="0.14"/>')
end()

# ---- hero, left column
g("hero")
raw(f'<rect id="eyebrow-square" x="{M}" y="309" width="10" height="10" rx="2" fill="{AMB}"/>')
T(M + 24, 320, "AI WORKFORCE FOR FREIGHT FORWARDERS", 21, 400, MUT, ls=1, mono=True)
T(M - 8, 512, "SQRlane", 172, 600, ls=-5, extra=' id="wordmark"')
T(M, 612, "Automates the desk.", 46, 400, ls=-1)
T(M, 668, "Acts before the route breaks.", 46, 400, ls=-1)
for i, line in enumerate(("An AI workforce that does the desk work end to end,",
                          "from quote to invoice, and moves bookings before a",
                          "disruption reaches the trade lane. You approve every change.")):
    T(M, 730 + i * 36, line, 24, 400, MUT)
end()

# ---- the desk: every mail, filled onto the record
g("desk-track")
T(1000, 210, "THE DESK · EVERY MAIL", 12.5, 500, MUT, ls=2.4, mono=True)
MAIL = ["Rate request", "Booking request", "Bill of lading", "Carrier invoice"]
for i, label in enumerate(MAIL):
    y = DESK_Y - 54 + i * 36
    raw(f'<g id="mail-{label.lower().replace(" ", "-")}">')
    pill(1000, y, 196, label, "desk")
    raw("</g>")
    raw(f'<path d="M1196 {y} C{NODE_X - 110} {y} {NODE_X - 110} {DESK_Y} {NODE_X - 20} {DESK_Y}" '
        f'stroke="{INK}" stroke-opacity="0.38" stroke-width="1.5" fill="none"/>')
node(NODE_X, DESK_Y, "DESK AGENTS")
arrow(NODE_X + 20, CARD_X, DESK_Y, "FILLS THE RECORD")
end()

# ---- the lane: every signal, where it happens
g("lane-track")
T(1000, 412, "THE LANE · EVERY SIGNAL", 12.5, 500, MUT, ls=2.4, mono=True)
# (place id, label, pill anchor relative to the pin, tone). The pin is the
# place; the pill names what is read there.
SIGNALS = [
    ("HAM", "Strike · Hamburg", "right", "active"),
    ("RTM", "Gusts · Rotterdam", "above-left", "signal"),
    ("RHINE", "River gauge · Kaub", "left", "signal"),
    ("FRINL", "Wildfire · Rhône", "left", "signal"),
]
for pid, label, side, tone in SIGNALS:
    px, py = place(pid)
    w = round(width(label, 13.5, 500) + 44)
    lit = tone == "active"
    raw(f'<g id="signal-{pid.lower()}">')
    # the line every signal takes to the risk agents
    raw(f'<path d="M{px:.1f} {py:.1f} C{(px + NODE_X) / 2:.1f} {py:.1f} {NODE_X - 70} {LANE_Y} {NODE_X - 20} {LANE_Y}" '
        f'stroke="{AMB if lit else INK}" stroke-opacity="{1 if lit else 0.22}" stroke-width="{2 if lit else 1.5}" fill="none"/>')
    if lit:
        for r, op in ((18, 0.10), (11, 0.18)):
            raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{AMB}" fill-opacity="{op}"/>')
    raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{AMB if lit else INK}" stroke="{BG}" stroke-width="2"/>')
    if side == "above-left":          # clear of the lane, which comes in from below-left
        ex, ey = px - 18, py - 30
        raw(f'<path d="M{ex:.1f} {ey + 6:.1f} L{px - 4:.1f} {py - 4:.1f}" stroke="{INK}" stroke-opacity="0.35" stroke-width="1"/>')
        pill(ex - w, ey, w, label, tone)
    else:
        pill(px + 14 if side == "right" else px - 14 - w, py, w, label, tone)
    raw("</g>")
sx, sy = P(-8.0, 45.6)            # beside the lane, over the Bay of Biscay
T(sx + 16, sy, "SHP-001", 11, 600, INK, ls=1.2, mono=True)
T(sx + 16, sy + 16, "FROM SHANGHAI", 11, 500, MUT, ls=1.2, mono=True)
node(NODE_X, LANE_Y, "RISK AGENTS")
arrow(NODE_X + 20, CARD_X, LANE_Y, "AMENDS THE BOOKING")
T(1000, 868, "60 SOURCES WATCHED · NEWS, RIVERS, WEATHER, HAZARDS, FILINGS, RATES", 11, 500, MUT, ls=1.2, mono=True)
end()

# ---- the record both tracks land on
g("tms-record")
raw(f'<rect x="{CARD_X}" y="{CARD_Y}" width="{CARD_W}" height="{CARD_H}" rx="14" fill="{CARD}" '
    f'stroke="{INK}" stroke-opacity="0.10" filter="url(#card-shadow)"/>')
fx0, fx1 = CARD_X + 24, CARD_X + CARD_W - 24
T(fx0, CARD_Y + 34, "SHP-001", 15, 600, ls=0.6, mono=True)
T(fx1, CARD_Y + 34, "TMS RECORD", 11.5, 500, MUT, "end", 1.8, True)
raw(f'<rect x="{fx0}" y="{CARD_Y + 52}" width="{fx1 - fx0}" height="1" fill="{INK}" fill-opacity="0.12"/>')
def fields(gid, cy, rows):
    raw(f'<g id="{gid}">')
    raw(f'<rect x="{fx0}" y="{cy - 64}" width="2" height="128" rx="1" fill="{INK}"/>')
    for i, (k, v) in enumerate(rows):
        y = cy - 47 + i * 47 + 5
        T(fx0 + 16, y, k, 14, 400, MUT)
        T(fx1, y, v, 14, 500, anchor="end")
    raw("</g>")
fields("fields-from-desk", DESK_Y, [("Quote", "on file"), ("B/L fields", "read"), ("Invoice", "reconciled")])
raw(f'<rect x="{fx0}" y="{(DESK_Y + LANE_Y) // 2}" width="{fx1 - fx0}" height="1" fill="{INK}" fill-opacity="0.08"/>')
fields("fields-from-lane", LANE_Y, [("Discharge", f'<tspan fill="{MUT}" text-decoration="line-through">HAM</tspan> → RTM'),
                                    ("ETA", "+2 days"), ("Carrier mail", "drafted")])
raw(f'<rect x="{fx0}" y="{LANE_Y + 84}" width="{fx1 - fx0}" height="1" fill="{INK}" fill-opacity="0.12"/>')
gy = LANE_Y + 124
raw(f'<g id="approval-gate"><rect x="{fx0}" y="{gy - 16}" width="{fx1 - fx0}" height="32" rx="16" fill="{AMB}" fill-opacity="0.12"/>'
    f'<circle cx="{fx0 + 18}" cy="{gy}" r="4" fill="{AMB}"/></g>')
T(fx0 + 32, gy + 4, "QUEUED · AWAITING YOU", 11.5, 600, AMB, ls=0.6, mono=True)
end()

# ---- bottom bar
g("bottom-bar")
raw(f'<rect id="bottom-rule" x="{M}" y="{BOTTOM_RULE}" width="{W - 2 * M}" height="1" fill="{INK}" fill-opacity="0.14"/>')
T(M, 982, "Abir Khan", 22, 600)
T(M, 1012, "Founder", 16, 400, MUT)
T(1040, 982, "ONE WORKFORCE", 13, 500, MUT, ls=2.4, mono=True)
T(1040, 1012, "The desk  +  the lane  →  one TMS record", 18, 500)
T(W - M, 982, "khan.abirhilal@gmail.com", 18, 500, anchor="end")
T(W - M, 1012, "+91 7596947806", 16, 400, MUT, "end")
end()
raw("</svg>")

out = HERE / "slide-01-cover.svg"
text = "\n".join(o)
assert "—" not in text, "em dash in slide copy"
assert " & " not in text, "escape & as &amp; - a bare one blanks the slide in Figma"
out.write_text(text, encoding="utf-8")
print("wrote", out, f"{len(text) / 1024:.0f} KB")
