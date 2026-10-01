#!/usr/bin/env python3
"""Slide 09 - Integrations, rebuilt from scratch on the owner's brief: less text, logos in
an orbit around each agent, and the agents joined as one network.

Eight agent nodes on an ellipse around SQRlane. Each carries an outward-facing arc of the
tools its job lives in (official marks only, inlined byte-for-byte; a mark that cannot be
had is left out, never redrawn). Blue links are real handoffs on that bus (workflow.py / orchestrator):
Inbox passes mail to Docs, Rate and the Playbook; Docs feeds the booking in the TMS; Rate's
quote goes to the Playbook; the Playbook checks Comms' mail; Risk hands its decision to
the TMS record and to Comms; the Assistant asks the TMS link and Risk.

One line under the network says what is connected in this build, because a real logo
reads as a live integration."""
from kit import *
import json, math, pathlib, re

BLUE = "#006BFF"
GREY = "#9A9A9A"

s = Slide()
s.header("07 · INTEGRATIONS", "Works inside the tools you already run.",
         "Each agent works where its job already lives. They all talk on one bus.")

HERE = pathlib.Path(__file__).parent
CH = json.loads((HERE / "channel_marks.json").read_text())   # Iconify, CC0/MIT
TM = json.loads((HERE / "tms_marks.json").read_text())

CX, CY, RX, RY = 960, 606, 650, 186
N_R = 54          # agent node radius
B_R = 31          # logo bubble radius

def uid():
    uid.n += 1
    return f"m{uid.n}-"
uid.n = 0

def scoped(body):
    p = uid()
    return re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + p + g.group(2), body)

def mark(name, cx, cy, size):
    """An official mark, byte-for-byte, centred in a size x size box. Never redrawn."""
    m = CH[name]; sc = size / max(m["w"], m["h"])
    dx = cx - m["w"] * sc / 2; dy = cy - m["h"] * sc / 2
    s.raw(f'<g id="mark-{name.lower()}" transform="translate({dx:.1f} {dy:.1f}) scale({sc:.4f})">{scoped(m["body"])}</g>')

def tms_word(name, cx, cy, width):
    """A TMS vendor's wordmark, fitted to width, centred."""
    m = TM[name]; sc = width / m["w"]; h = m["h"] * sc
    x, y = cx - width / 2, cy - h / 2
    if m["kind"] == "png":
        s.raw(f'<image id="mark-{name.lower()}" x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{h:.1f}" href="{m["href"]}"/>')
    else:
        s.raw(f'<g id="mark-{name.lower()}" transform="translate({x:.1f} {y:.1f}) scale({sc:.4f})">{scoped(m["body"])}</g>')

def cargowise_icon(cx, cy, h=24):
    """CargoWise's own icon: the left square of its official wordmark, clipped. Not redrawn."""
    m = TM["CargoWise"]; sc = h / m["h"]; w = m["w"] * sc
    x, y = cx - h * 0.5, cy - h / 2
    cid = uid() + "cw"
    s.raw(f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{h:.1f}" height="{h:.1f}"/></clipPath>'
          f'<image id="mark-cargowise" clip-path="url(#{cid})" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" href="{m["href"]}"/>')

def agent_mark(cx, cy, r=6, col=BLUE):
    for i in range(8):
        a = i * math.pi / 4
        s.raw(f'<circle cx="{cx + r * math.cos(a):.1f}" cy="{cy + r * math.sin(a):.1f}" r="{r * 0.27:.1f}" fill="{col}" fill-opacity="{0.35 + 0.08 * i:.2f}"/>')

# (name, angle in degrees on the ellipse, orbit radius, tools). A tool is a channel mark
# name, ("tms", vendor) for a TMS wordmark, ("cw",) for the CargoWise icon, or ("more", text).
# Work order, clockwise from the left: a mail comes in, is booked, its documents read, the
# lane priced, the result checked, written to the TMS; then the risk side.
NODES = [
    ("Inbox",     180, 108, ["Outlook", "Gmail"]),
    ("Booking",   220,  96, []),
    ("Docs",      260, 96, ["PDF", "Word", "Excel", "Image"]),
    ("Rate",      300, 100, ["Excel", "GoogleSheets"]),
    ("Playbook",  340, 104, ["Word", "OneDrive", "GoogleDrive"]),
    ("TMS link",   20, 140, [("cw",), ("tms", "SAP"), ("tms", "Oracle"), ("tms", "Descartes")]),
    ("Comms",      60, 108, ["Teams", "Slack", "WhatsApp", "WeChat"]),
    ("Assistant", 100, 96, ["Claude", "ChatGPT", "Cursor"]),
    ("Risk",      140, 108, ["NDR", "DW", "NASA", ("more", "+57")]),
]
# The open-weight model each agent is built to run, EU-hosted - the strong end of the
# options static/whitepaper.html already gives per job. Where the answer must be exact
# (a price, a rule check, a write to the record) it is computed, never generated.
MODEL = {"Inbox": "Gemma-3-27B", "Booking": "code only", "Docs": "Qwen2.5-VL-72B",
         "Rate": "code only", "Playbook": "Qwen3-235B", "TMS link": "code only",
         "Comms": "Llama-3.3-70B", "Assistant": "Gemma-3-27B", "Risk": "Qwen3-235B"}
BLUE_BG2, GREY_BG2 = "#E8F1FF", "#F3F3F3"
AMB_L = "#96580A"
POS, OUT = {}, {}
_ts = [math.pi + 2 * math.pi * i / 3600 for i in range(3601)]
_pts = [(CX + RX * math.cos(u), CY + RY * math.sin(u)) for u in _ts]
_cum = [0.0]
for i in range(1, len(_pts)):
    _cum.append(_cum[-1] + math.dist(_pts[i - 1], _pts[i]))
for k, (name, _, _, _) in enumerate(NODES):
    target = _cum[-1] * k / len(NODES)
    i = next(j for j, c in enumerate(_cum) if c >= target)
    u = _ts[i]
    POS[name] = _pts[i]
    OUT[name] = math.atan2(RX * math.sin(u), RY * math.cos(u))   # the outward normal

s.g("bus")
s.raw(f'<ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}" fill="none" stroke="{INK}" stroke-opacity="0.06" stroke-width="1"/>')
s.end()

def curve(a, b, k_near=0.30, k_far=0.50):
    (x1, y1), (x2, y2) = POS[a], POS[b]
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    k = k_near if math.dist((x1, y1), (x2, y2)) < 520 else k_far
    return x1, y1, mx + (CX - mx) * k, my + (CY - my) * k, x2, y2

def at(c, t):
    x1, y1, qx, qy, x2, y2 = c
    return ((1 - t) ** 2 * x1 + 2 * (1 - t) * t * qx + t ** 2 * x2,
            (1 - t) ** 2 * y1 + 2 * (1 - t) * t * qy + t ** 2 * y2)

# ---- every other real handoff, faint
OTHER = [("Inbox", "Rate"), ("Docs", "TMS link"), ("Playbook", "Comms"), ("Risk", "TMS link"),
         ("Risk", "Comms"), ("Assistant", "TMS link"), ("Assistant", "Risk")]
s.g("network")
for a, b in OTHER:
    x1, y1, qx, qy, x2, y2 = curve(a, b)
    s.raw(f'<path d="M{x1:.1f} {y1:.1f} Q{qx:.1f} {qy:.1f} {x2:.1f} {y2:.1f}" stroke="{INK}" stroke-opacity="0.10" stroke-width="1.2" fill="none"/>')
s.end()

# ---- one real thread, IN-108, the vaccine booking: the bus's own messages, in order
THREAD = [("Inbox", "Booking", "1", "Booking request · Nordmed Pharma", BLUE),
          ("Docs", "Booking", "2", "7 fields read", BLUE),
          ("Rate", "Booking", "3", "Best: ONE · €3,880", BLUE),
          ("Playbook", "Booking", "4", "ONE not approved · use Maersk or Hapag-Lloyd", AMB_L),
          ("Playbook", "TMS link", "5", "Rebooked Hapag-Lloyd · queued for you", BLUE)]
LABEL_T = {"1": 0.5, "2": 0.5, "3": 0.55, "4": 0.5, "5": 0.5}
LABEL_DY = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
s.g("thread-in-108")
labels = []
for a, b, n, msg, col in THREAD:
    c = curve(a, b)
    x1, y1, qx, qy, x2, y2 = c
    s.raw(f'<path d="M{x1:.1f} {y1:.1f} Q{qx:.1f} {qy:.1f} {x2:.1f} {y2:.1f}" stroke="{col}" stroke-opacity="0.75" stroke-width="2" fill="none"/>')
    ex, ey = at(c, 0.9); fx, fy = at(c, 0.86)               # arrowhead, pointing at b
    ang = math.atan2(ey - fy, ex - fx)
    s.raw(f'<path d="M{ex + 7*math.cos(ang):.1f} {ey + 7*math.sin(ang):.1f} L{ex + 6*math.cos(ang+2.5):.1f} {ey + 6*math.sin(ang+2.5):.1f} L{ex + 6*math.cos(ang-2.5):.1f} {ey + 6*math.sin(ang-2.5):.1f} Z" fill="{col}"/>')
    labels.append((at(c, LABEL_T[n]), n, msg, col))
s.end()


# ---- the centre: SQRlane
s.g("sqrlane")
s.raw(f'<circle cx="{CX}" cy="{CY}" r="86" fill="none" stroke="{BLUE}" stroke-opacity="0.12" stroke-width="1"/>')
s.raw(f'<circle cx="{CX}" cy="{CY + 3}" r="58" fill="{INK}" fill-opacity="0.06"/>')
s.raw(f'<circle cx="{CX}" cy="{CY}" r="58" fill="{INK}"/>')
mx0, my0 = CX - 11, CY - 22
s.raw(f'<path d="M{mx0} {my0+18}h22 M{mx0} {my0+9}h15 M{mx0} {my0}h8" stroke="{BG}" stroke-width="3.4" stroke-linecap="round" fill="none"/>')
s.T(CX, CY + 24, "sqrlane", 15, 600, BG, anchor="middle")
s.R(CX - 70, CY + 90, 140, 24, BG, 12)
s.T(CX, CY + 106.5, "16 agents · one bus", 12.5, 500, MUT, anchor="middle")
s.end()

# ---- each agent, with its tools in orbit
def bubble_w(tool):
    if isinstance(tool, tuple) and tool[0] == "tms":
        return 128
    return B_R * 2

def draw_tool(tool, bx, by):
    w = bubble_w(tool); h = B_R * 2
    s.R(bx - w / 2, by - h / 2 + 2, w, h, INK, h / 2, ' fill-opacity="0.05"')
    s.R(bx - w / 2, by - h / 2, w, h, CARD, h / 2, f' stroke="{INK}" stroke-opacity="0.10"')
    if isinstance(tool, str):
        mark(tool, bx, by, 34)
    elif tool[0] == "cw":
        cargowise_icon(bx, by, 36)
    elif tool[0] == "tms":
        tms_word(tool[1], bx, by, {'SAP': 52, 'Oracle': 92, 'Descartes': 100}[tool[1]])
    else:
        s.T(bx, by + 5, tool[1], 14, 600, MUT, anchor="middle")

for name, ang, orb, tools in NODES:
    x, y = POS[name]
    s.g(f"agent-{name.lower().replace(' ', '-')}")
    out = OUT[name]
    # spread the tools along the arc: each takes the room it needs across the arc's direction
    tx, ty = -math.sin(out), math.cos(out)
    ang_sizes = [(abs(bubble_w(tl) * tx) + abs(2 * B_R * ty) + 16) / orb for tl in tools]
    total = sum(ang_sizes)
    a0 = out - total / 2
    # the orbit line, a little longer than the tools
    a_s, a_e = a0 - 0.22, a0 + total + 0.22
    p1 = (x + orb * math.cos(a_s), y + orb * math.sin(a_s))
    p2 = (x + orb * math.cos(a_e), y + orb * math.sin(a_e))
    large = 1 if (a_e - a_s) > math.pi else 0
    s.raw(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} A{orb} {orb} 0 {large} 1 {p2[0]:.1f} {p2[1]:.1f}" stroke="{INK}" stroke-opacity="0.12" stroke-width="1" fill="none"/>')
    # the node
    s.raw(f'<circle cx="{x:.1f}" cy="{y + 3:.1f}" r="{N_R}" fill="{INK}" fill-opacity="0.05"/>')
    s.raw(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{N_R}" fill="{CARD}" stroke="{BLUE}" stroke-opacity="0.35" stroke-width="1.2"/>')
    agent_mark(x, y - 20, 6)
    s.T(x, y + 7, name, 13, 600, anchor="middle")
    # the open-weight model this agent would run, EU-hosted (whitepaper's per-agent table)
    mdl = MODEL[name]
    px_, py_ = x, y + 29                        # inside the node, under the name
    mw = round(len(mdl) * 5.6 + 14)
    fill, ink = (GREY_BG2, GREY) if mdl == "code only" else (BLUE_BG2, BLUE)
    s.R(px_ - mw / 2, py_ - 9, mw, 18, fill, 9)
    s.T(px_, py_ + 3.5, mdl, 9.5, 600, ink, anchor="middle")
    # the tools
    a = a0
    for tl, sz in zip(tools, ang_sizes):
        c = a + sz / 2
        draw_tool(tl, x + orb * math.cos(c), y + orb * math.sin(c))
        a += sz
    s.end()

s.g("disclosure")
s.T(M, 946, "Logos show where each agent works. Live today: the 60 public sources and MCP. "
    "TMS and mail are read from exports and files; native links come next.",
    12.5, 400, GREY)
s.T(M, 966, "Model chips: the open-weight model each agent is built to run, hosted in the EU. Code-only agents compute "
    "exact answers (prices, records) and run no model. The prototype calls a US-hosted provider today.", 12.5, 400, GREY)
s.end()

s.footer(9)
s.write("slide-09-integrations.svg")
