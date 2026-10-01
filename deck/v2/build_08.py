#!/usr/bin/env python3
"""Slide 08 - The How 2/2: the risk layer. The same frame as slide 07. Left, the product
on the day the Hamburg strike hits: a regional headline lands, the Risk agent picks it
up, one line of the run, and the decisions as a thread - SHP-001 rerouted via
Rotterdam with its customer mail drafted, SHP-002 held. Right, how the four risk agents
work, the 60 sources by family, and the detection trail.

Every decision, reason, recipient and trail entry is from
orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg"). Dates follow
slide 02's frame (ETA 10 Oct, due 14 Oct, +2 days = 12 Oct), because the run's own
dates age forward weekly. The strike is the authored demo scenario, so the 23-hour lead
is labelled "demo scenario"; the 60 sources are the live watch list
(risk_monitor.expected_sources()). Approvals 18 = the risk run's 6 drafts + 12 TMS
changes. Nothing is sent or written."""
from kit import *

BLUE, BLUE_BG = "#006BFF", "#E8F1FF"
GREEN, GREEN_BG = "#0F7B3F", "#E7F5EC"
AMBR, AMBR_BG = "#96580A", "#FDF3E3"
GREY, GREY_BG, LINE = "#9A9A9A", "#F3F3F3", "#E6E6E6"

s = Slide()
s.header("06 · THE HOW, 2 OF 2", "Know early, while you still have options.",
         "60 live sources, read against every booking. The call comes before the route breaks.")
TOP, BOT = 306, 890

def pill(x, y, text, fill, ink, anchor="end", size=10.5, h=20):
    w = round(len(text) * size * 0.6 + 18)
    x0 = x - w if anchor == "end" else x
    s.R(x0, y, w, h, fill, h / 2)
    s.T(x0 + w / 2, y + h / 2 + size * 0.36, text, size, 600, ink, anchor="middle")
    return w

# ================================================================ the dashboard
import json, math, pathlib, re
CH = json.loads((pathlib.Path(__file__).with_name("channel_marks.json")).read_text())   # Iconify, CC0/MIT
RED = "#EA001D"

def mark(name, x, y, size):
    """An official mark, byte-for-byte, scaled into a size x size box. Never redrawn."""
    m = CH[name]; sc = size / max(m["w"], m["h"])
    body = re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + "o8-" + g.group(2), m["body"])
    dx = x + (size - m["w"] * sc) / 2; dy = y + (size - m["h"] * sc) / 2
    s.raw(f'<g id="mark-{name.lower()}" transform="translate({dx:.1f} {dy:.1f}) scale({sc:.4f})">{body}</g>')

def agent_mark(cx, cy, r=6, col=BLUE):
    for i in range(8):                                   # the agent: a ring of dots
        a = i * math.pi / 4
        s.raw(f'<circle cx="{cx + r * math.cos(a):.1f}" cy="{cy + r * math.sin(a):.1f}" r="{r * 0.27:.1f}" fill="{col}" fill-opacity="{0.35 + 0.08 * i:.2f}"/>')

FX, FW = M, 1000
s.g("dashboard")
s.R(FX, TOP, FW, BOT - TOP, CARD, 14, f' stroke="{INK}" stroke-opacity="0.14"')
s.g("window-bar")
s.R(FX, TOP, FW, 40, "#F4F4F4", 14); s.R(FX, TOP + 26, FW, 14, "#F4F4F4")
s.rule(TOP + 40, 0.09, FX, FW)
for i in range(3):
    s.raw(f'<circle cx="{FX + 22 + i * 18}" cy="{TOP + 20}" r="5.5" fill="#DEDEDE"/>')
s.R(FX + FW / 2 - 150, TOP + 9, 300, 22, CARD, 6, f' stroke="{INK}" stroke-opacity="0.08"')
s.T(FX + FW / 2, TOP + 25, "SQRlane · Desk", 12, 500, MUT, anchor="middle")
s.end()

SBW, SY0 = 180, TOP + 41
s.g("sidebar")
s.R(FX + SBW, SY0, 1, BOT - SY0 - 1, INK, extra=' fill-opacity="0.08"')
s.R(FX + 22, SY0 + 22, 24, 24, INK, 6)
s.raw(f'<path d="M{FX+28} {SY0+39}h12 M{FX+28} {SY0+34}h8 M{FX+28} {SY0+29}h4.5" stroke="{BG}" stroke-width="1.9" stroke-linecap="round" fill="none"/>')
s.T(FX + 56, SY0 + 40, "sqrlane", 16, 600)
ny = SY0 + 80
for name, count, on in (("Today", None, False), ("Risk", "1", True), ("Approvals", "18", False),
                        ("Shipments", "7", False), ("Agents", "16", False)):
    if on: s.R(FX + 12, ny, SBW - 24, 32, GREY_BG, 8)
    s.T(FX + 26, ny + 21, name, 13.5, 600 if on else 500, INK if on else "#4A4A4A")
    if count:
        cw = len(count) * 7 + 14
        s.R(FX + SBW - 22 - cw, ny + 7, cw, 18, BLUE_BG if name == "Approvals" else GREY_BG, 9)
        s.T(FX + SBW - 22 - cw / 2, ny + 20, count, 11, 600, BLUE if name == "Approvals" else "#6B6B6B", anchor="middle")
    ny += 36
s.end()

MX = FX + SBW + 32; MW = FX + FW - 32 - MX

def soft_card(x, y, w, h, r=14, fill=CARD, op=0.12):
    s.R(x, y + 3, w, h, INK, r, ' fill-opacity="0.04"')
    s.R(x, y, w, h, fill, r, f' stroke="{INK}" stroke-opacity="{op}"')

# ---- the bell, top right of the app bar: one new mail
s.g("notifications")
bx, byy = FX + FW - 34, TOP + 20
s.raw(f'<path d="M{bx-6} {byy+4} h12 l-1.5 -2 v-4.5 a4.5 4.5 0 0 0 -9 0 v4.5 z M{bx-1.8} {byy+6.5} a1.9 1.9 0 0 0 3.6 0" '
      f'stroke="#4A4A4A" stroke-width="1.5" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
s.raw(f'<circle cx="{bx + 6}" cy="{byy - 7}" r="6.5" fill="{RED}" stroke="#F4F4F4" stroke-width="1.5"/>')
s.T(bx + 6, byy - 3.8, "1", 8.5, 700, CARD, anchor="middle")
s.end()


s.g("page-header")
s.T(MX, TOP + 90, "Risk", 26, 600, ls=-0.6)
s.end()

def news_mark(x, y, sz):
    """A plain news pictogram - no outlet's logo."""
    s.R(x, y, sz, sz, INK, 7)
    for k, w in enumerate((0.62, 0.62, 0.40)):
        s.R(x + sz * 0.2, y + sz * (0.3 + k * 0.17), sz * w, sz * 0.08, CARD, 1)

# ---- two pop-ups: a regional headline lands, the Risk agent picks it up
PT, PH_ = TOP + 54, 56
P2W = 290; P2X = MX + MW - P2W
P1W = 318; P1X = P2X - 26 - P1W
s.g("popup-news")
soft_card(P1X, PT, P1W, PH_, 14)
s.R(P1X + 10, PT + 9, 38, 38, GREY_BG, 10)
mark("NDR", P1X + 15, PT + 14, 28)
s.raw(f'<circle cx="{P1X + 46}" cy="{PT + 10}" r="8" fill="{RED}" stroke="{CARD}" stroke-width="2"/>')
s.T(P1X + 46, PT + 14, "1", 10, 700, CARD, anchor="middle")
s.T(P1X + 60, PT + 23, "Regional source · NDR Hamburg", 11, 500, GREY)
s.T(P1X + 60, PT + 42, "Warnstreik im Hamburger Hafen", 12.5, 600)
s.end()
ax = P1X + P1W + 5
s.line(ax, PT + PH_ / 2, ax + 12, PT + PH_ / 2, INK, 0.3, 1.5)
s.raw(f'<path d="M{ax+11} {PT+PH_/2-4} L{ax+16} {PT+PH_/2} L{ax+11} {PT+PH_/2+4}" stroke="{INK}" stroke-opacity="0.3" stroke-width="1.5" fill="none"/>')
s.g("popup-agent")
soft_card(P2X, PT, P2W, PH_, 14)
s.R(P2X, PT, P2W, PH_, "none", 14, f' stroke="{BLUE}" stroke-width="0.8" stroke-opacity="0.45"')
agent_mark(P2X + 22, PT + 19, 6)
s.T(P2X + 38, PT + 23, "Risk agent", 12.5, 600, BLUE)
s.T(P2X + P2W - 14, PT + 23, "working…", 11, 500, GREY, anchor="end")
s.T(P2X + 14, PT + 44, "Checking 7 bookings against it.", 12, 400, INK)
s.end()

# ---- the run in one line, each figure with its tag
RED_BG = "#FEECEC"
OY, OH = TOP + 124, 114
STEPS = [("60", "sources watched", "live", GREEN_BG, GREEN),
         ("1", "event", "strike · high", RED_BG, RED),
         ("3", "decisions", None, None, None),
         ("€46,500", "cost avoided", "vs doing nothing", GREEN_BG, GREEN),
         ("0", "sent or written", "until you approve", GREEN_BG, GREEN)]
s.g("this-run")
s.card(MX, OY, MW, OH, 12)
s.T(MX + 18, OY + 25, "This run", 13, 600)
s.T(MX + MW - 18, OY + 25, "Hamburg strike · demo scenario", 12, 400, GREY, anchor="end")
sw_ = (MW - 36) / 5
for k, (n, lab, tag, tf, ti) in enumerate(STEPS):
    x = MX + 18 + k * sw_
    s.T(x, OY + 60, n, 26 if len(n) > 3 else 30, 600, ls=-1)
    s.T(x, OY + 79, lab, 12, 500, "#4A4A4A")
    if tag:
        pill(x, OY + 87, tag, tf, ti, anchor="start", size=10, h=18)
    else:                                              # the three decisions, split
        w1 = pill(x, OY + 87, "2 reroute", BLUE_BG, BLUE, anchor="start", size=10, h=18)
        pill(x + w1 + 5, OY + 87, "1 hold", AMBR_BG, AMBR, anchor="start", size=10, h=18)
    if k < 4:
        s.T(x + sw_ - 14, OY + 60, "›", 18, 400, "#C8C8C8")
s.end()

# ---- the decisions, as a thread
CY0 = OY + OH + 14; CHh = BOT - 20 - CY0
s.g("decisions")
s.R(MX, CY0, MW, CHh, "#F6F8FB", 16, f' stroke="{INK}" stroke-opacity="0.10"')
cy = CY0 + 12
BWb = MW - 32
# SHP-001: the reroute (the booking from slides 02 and 03)
s.g("decision-reroute")
soft_card(MX + 16, cy, BWb, 76, 14, op=0.10)
agent_mark(MX + 36, cy + 20)
s.T(MX + 52, cy + 25, "Routing agent", 12.5, 600, BLUE)
s.T(MX + 150, cy + 25, "SHP-001 · Automotive parts, Shanghai → Munich", 12, 400, GREY)
pill(MX + 16 + BWb - 14, cy + 12, "reroute", BLUE_BG, BLUE)
s.T(MX + 32, cy + 48, "Reroute via Rotterdam. Arrives 12 Oct, due 14 Oct.", 13.5, 600)
s.T(MX + 32, cy + 66, "Hamburg: up to 5 days late against 4 days of slack. Rotterdam adds 2 days, with no active risk.", 11.5, 400, MUT)
s.end()
cy += 84
# the customer mail the Comms agent drafted for it
DHh = 84
s.g("decision-mail")
soft_card(MX + 16, cy, BWb, DHh, 14, op=0.10)
agent_mark(MX + 36, cy + 20)
s.T(MX + 52, cy + 25, "Comms agent", 12.5, 600, BLUE)
s.T(MX + 148, cy + 25, "Drafted a mail to Katrin Vogel, Bavaria Drivetrain.", 12, 400, GREY)
mark("Outlook", MX + 32, cy + 38, 15)
s.T(MX + 54, cy + 50, "HLCU-2261188 Automotive parts: revised ETA", 12.5, 600)
s.T(MX + 32, cy + 70, "We are bringing it in through Rotterdam instead of Hamburg, 2 days later than planned.", 11.5, 400, MUT)
def draft_gate(top, h):
    by = top + h - 38
    s.R(MX + 16 + BWb - 92, by, 78, 26, INK, 8)
    s.T(MX + 16 + BWb - 53, by + 18, "Approve", 12, 600, CARD, anchor="middle")
    s.T(MX + 16 + BWb - 104, by + 17.5, "Draft ready", 11, 600, AMBR, anchor="end")
draft_gate(cy, DHh)
s.end()
cy += DHh + 8
# SHP-002: the hold - the call with no good option
s.g("decision-hold")
soft_card(MX + 16, cy, BWb, 82, 14, op=0.10)
agent_mark(MX + 36, cy + 20)
s.T(MX + 52, cy + 25, "Routing agent", 12.5, 600, BLUE)
s.T(MX + 150, cy + 25, "SHP-002 · Reefer pharma, Ningbo → Hamburg", 12, 400, GREY)
pill(MX + 16 + BWb - 14, cy + 12, "hold", AMBR_BG, AMBR)
s.T(MX + 32, cy + 48, "Hold the boxes instead of discharging into the strike. No other route lands any better.", 12.5, 500, INK)
mark("Outlook", MX + 32, cy + 58, 14)
s.T(MX + 52, cy + 70, "Comms drafted the hold instruction to Maersk and the notice to Nordmed Pharma.", 11.5, 400, MUT)
draft_gate(cy, 82)
s.end()
cy += 90
s.T(MX + 18, cy + 10, "Cost avoided = €141,100 if nothing is done, minus €94,600 with these calls. From each synthetic booking's own terms.", 10.5, 400, GREY)
s.end()
s.end()

# ================================================================ how the risk layer works
HX = FX + FW + 24; HW = W - M - HX
hx, hw = HX + 24, HW - 48
s.g("how-the-risk-layer-works")
s.card(HX, TOP, HW, BOT - TOP)
s.T(hx, TOP + 36, "HOW THE RISK LAYER WORKS", 13, 600, AMB, ls=1.4)
s.T(HX + HW - 24, TOP + 36, "4 agents · 3 live, Planner scripted", 12, 500, GREY, anchor="end")

def arrow(y1, y2, x=None):
    x = x or hx + hw / 2
    s.line(x, y1, x, y2 - 5, INK, 0.3, 1.5)
    s.raw(f'<path d="M{x-4.5} {y2-6} L{x} {y2} L{x+4.5} {y2-6}" stroke="{INK}" stroke-opacity="0.3" stroke-width="1.5" fill="none"/>')

def count_chip(x, y, text, fill=BLUE_BG, ink=BLUE, anchor="start"):
    w = round(len(text) * 6 + 16)
    x0 = x - w if anchor == "end" else x
    s.R(x0, y, w, 19, fill, 9.5)
    s.T(x0 + w / 2, y + 13.5, text, 10.5, 600, ink, anchor="middle")
    return w

def step(y, name, n, what, h=44, fill=CARD, ink=INK, sub=MUT, stroke=0.16, nx=None):
    s.R(hx, y, hw, h, fill, 10, f' stroke="{INK}" stroke-opacity="{stroke}"' if stroke else "")
    s.T(hx + 14, y + h / 2 + 5, name, 13.5, 600, ink)
    cw = count_chip(nx or hx + 118, y + h / 2 - 9.5, n)
    s.T((nx or hx + 118) + cw + 12, y + h / 2 + 4.5, what, 11.5, 400, sub)

y = TOP + 56
# WATCH: the 60 live sources by family, then what comes next, fading out
s.g("watch")
s.R(hx, y, hw, 94, BG, 12, f' stroke="{INK}" stroke-opacity="0.10"')
s.T(hx + 14, y + 22, "WATCH", 10.5, 700, MUT, ls=1.2)
s.raw(f'<circle cx="{hx + 76}" cy="{y + 18}" r="4" fill="{GREEN}"/>')
s.T(hx + 86, y + 22, "60 sources, live, read together on every run", 11.5, 400, MUT)
fx = hx + 14
for fam, n in (("News", 41), ("Rivers", 7), ("Weather & sea", 4), ("Hazards", 5), ("Government", 2), ("Markets", 1)):
    lab = fam.replace("&", "&amp;")
    w = round(len(fam) * 6.3 + len(str(n)) * 7 + 30)
    s.R(fx, y + 34, w, 22, CARD, 6, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(fx + 10, y + 49, lab, 11, 500, "#3A3A3A")
    s.T(fx + w - 9, y + 49, str(n), 11, 700, BLUE, anchor="end")
    fx += w + 6
s.raw(f'<circle cx="{hx + 18}" cy="{y + 75}" r="4" fill="#C4C4C4"/>')
s.T(hx + 28, y + 79, "Coming soon", 11, 600, GREY)
fx = hx + 122
for k, nxt in enumerate(("AIS vessel positions", "Freight indices", "Prediction markets", "Port calls", "")):
    op = (0.85, 0.6, 0.38, 0.2, 0.08)[k]
    w = round(len(nxt) * 6.3 + 22) if nxt else 70
    s.R(fx, y + 64, w, 22, CARD, 6, f' stroke="{INK}" stroke-opacity="{0.22 * op:.2f}" stroke-dasharray="3 3" fill-opacity="{op:.2f}"')
    if nxt: s.T(fx + 11, y + 79, nxt, 11, 500, "#6B6B6B")
    fx += w + 6
s.raw('<defs><linearGradient id="soon-fade" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0.55" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity="1"/>'
      '</linearGradient></defs>')
s.R(hx + 122, y + 62, hw - 136, 26, "url(#soon-fade)")
s.end()
y += 94; arrow(y, y + 11); y += 13

# every agent step on the same grid: name, count, what it does
NX = hx + 108
ROWH = 38
def row(name, n, what, grp, chip=None, right=None, h=None):
    global y
    s.g(grp)
    s.R(hx, y, hw, h or ROWH, CARD, 10, f' stroke="{INK}" stroke-opacity="0.16"')
    s.T(hx + 14, y + 24, name, 13.5, 600)
    cw = count_chip(NX, y + 9.5, n, *(chip or ()))
    s.T(NX + 92, y + 23.5, what, 11.5, 400, MUT)
    if right: right(y)
    s.end()
    y += h or ROWH
def outcomes(yy):
    ox = hx + hw - 14
    for lab, f, i in (("no change", GREY_BG, "#4A4A4A"), ("hold", AMBR_BG, AMBR), ("reroute", BLUE_BG, BLUE)):
        ox -= pill(ox, yy + 9, lab, f, i) + 6

row("Risk", "1 agent", "reads every source, flags what touches a booking", "risk-agent")
arrow(y, y + 11); y += 13
row("Routing", "1 agent", "weighs slack against delay, prices every option", "routing-agent", right=outcomes)
arrow(y, y + 11); y += 13
s.g("cost-impact")
s.raw('<defs><linearGradient id="cost-fade" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0" stop-color="{GREEN_BG}"/><stop offset="1" stop-color="{CARD}"/></linearGradient></defs>')
s.R(hx, y, hw, ROWH, "url(#cost-fade)", 10, f' stroke="{GREEN}" stroke-opacity="0.18"')
s.T(hx + 14, y + 24, "Cost impact", 13.5, 600, GREEN)
count_chip(NX, y + 9.5, "−€46,500", CARD, GREEN)
s.T(NX + 92, y + 23.5, "€141,100 if nothing is done, €94,600 with these calls", 11.5, 400, GREEN)
s.end()
y += ROWH
arrow(y, y + 11); y += 13
row("Comms", "1 agent", "drafts the carrier and customer mail", "comms-agent")
arrow(y, y + 11); y += 13
row("Planner", "1 agent", "checks bookings before departure · scripted", "planner-agent", chip=(GREY_BG, "#6B6B6B"))
arrow(y, y + 11); y += 13

# the desk: slide 07, faded here as the risk layer was there
s.g("the-desk")
s.R(hx, y, hw, ROWH, GREY_BG, 10, f' stroke="{INK}" stroke-opacity="0.10" stroke-dasharray="4 3"')
s.T(hx + 14, y + 26, "The desk", 13.5, 600, "#7A7A7A")
count_chip(NX, y + 11.5, "12 agents", CARD, "#7A7A7A")
s.T(NX + 92, y + 25.5, "amends the booking, moves the entry, sets the new ETA", 11.5, 400, "#8A8A8A")
s.raw('<defs><linearGradient id="desk-fade" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0.35" stop-color="{CARD}" stop-opacity="0"/><stop offset="0.95" stop-color="{CARD}" stop-opacity="1"/>'
      '</linearGradient></defs>')
s.R(hx - 2, y - 2, hw + 4, ROWH + 4, "url(#desk-fade)")
s.end()
y += ROWH; arrow(y, y + 11); y += 13

s.g("gate-and-record")
GW2 = (hw - 28) / 2
s.R(hx, y, GW2, ROWH, INK, 10)
s.T(hx + 14, y + 26, "You approve", 13.5, 700, CARD)
s.T(hx + 108, y + 25.5, "every reroute, every mail", 11.5, 400, "#D6D6D6")
ax1 = hx + GW2 + 4
s.line(ax1, y + 21, ax1 + 15, y + 21, INK, 0.3, 1.5)
s.raw(f'<path d="M{ax1+14} {y+16.5} L{ax1+20} {y+21} L{ax1+14} {y+25.5}" stroke="{INK}" stroke-opacity="0.3" stroke-width="1.5" fill="none"/>')
tx = hx + GW2 + 28
s.R(tx, y, GW2, ROWH, CARD, 10, f' stroke="{INK}" stroke-opacity="0.16"')
s.T(tx + 14, y + 26, "TMS link", 13.5, 600)
cw = count_chip(tx + 84, y + 11.5, "1 agent")
s.T(tx + 84 + cw + 10, y + 25.5, "writes it onto the booking", 11.5, 400, MUT)
s.end()
y += ROWH

# one event, earlier: the detection trail of the authored strike
s.g("detection-trail")
y += 24
s.T(hx, y, "ONE EVENT, EARLIER", 10.5, 700, MUT, ls=1.2)
s.T(hx + 146, y, "the Hamburg strike · demo scenario", 11.5, 400, MUT)
y += 12
cx = hx
TRAIL = [("NDR Hamburg", "first", "first"), ("ver.di", "+22 min", None), ("NOS Nieuws", "+4 h", None),
         ("International wires", "+23 h", "wire")]
for k, (src, when, kind) in enumerate(TRAIL):
    lab = f"{src} · {when}"
    w = round(len(lab) * 6.2 + 18)
    fill, ink = {"first": (BLUE, CARD), "wire": (CARD, INK)}.get(kind, (GREY_BG, "#3A3A3A"))
    s.R(cx, y, w, 24, fill, 6, f' stroke="{INK}" stroke-opacity="0.3"' if kind == "wire" else "")
    s.T(cx + w / 2, y + 16, lab, 11, 600 if kind else 500, ink, anchor="middle")
    cx += w
    if k < len(TRAIL) - 1:
        s.T(cx + 5, y + 16, "›", 12, 500, MUT); cx += 16
s.end()
s.end()

s.T(M, 946, "The earlier the call, the more options you have and the less it costs.", 28, 600, ls=-0.6)
s.footer(8)
s.write("slide-08-the-how-2.svg")
