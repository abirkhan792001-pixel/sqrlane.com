#!/usr/bin/env python3
"""Slide 09 - Integrations, rebuilt from scratch on the owner's brief: less text, logos in
an orbit around each agent, and the agents joined as one network.

Eight agent nodes on an ellipse around SQRlane. Each carries an outward-facing arc of the
tools its job lives in (official marks only, inlined byte-for-byte; a mark that cannot be
had is left out, never redrawn). Faint spokes run from every agent to the centre: the one
message bus. Blue links are real handoffs on that bus (workflow.py / orchestrator):
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

CX, CY, RX, RY = 960, 622, 650, 204
N_R = 42          # agent node radius
B_R = 22          # logo bubble radius

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
# name, ("tms", vendor, pill width), ("cw",) for the CargoWise icon, or ("more", text).
NODES = [
    ("Inbox",     180, 80, ["Outlook", "Gmail"]),
    ("Docs",      225, 84, ["PDF", "Word", "Excel", "Image", "XML"]),
    ("Playbook",  270, 80, ["Word", "OneDrive", "GoogleDrive"]),
    ("Rate",      315, 80, ["Excel", "GoogleSheets"]),
    ("TMS link",    0, 96, [("cw",), ("tms", "SAP", 40), ("tms", "Oracle", 70), ("tms", "Descartes", 84)]),
    ("Comms",      45, 84, ["Teams", "Slack", "WhatsApp", "WeChat"]),
    ("Assistant",  90, 80, ["Claude", "Cursor", "VSCode"]),
    ("Risk",      135, 84, ["NDR", "DW", "NASA", ("more", "+57")]),
]
POS = {}
for name, ang, _, _ in NODES:
    a = math.radians(ang)
    POS[name] = (CX + RX * math.cos(a), CY + RY * math.sin(a))

# ---- the bus: a faint spoke from every agent to the centre
s.g("bus")
s.raw(f'<ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}" fill="none" stroke="{INK}" stroke-opacity="0.06" stroke-width="1"/>')
for name, (x, y) in POS.items():
    s.line(CX, CY, x, y, INK, 0.10, 1, dash="3 5")
s.end()

# ---- the network: real handoffs between agents, curved through the middle
LINKS = [("Inbox", "Docs"), ("Inbox", "Rate"), ("Inbox", "Playbook"), ("Docs", "TMS link"),
         ("Rate", "Playbook"), ("Playbook", "Comms"), ("Risk", "TMS link"), ("Risk", "Comms"),
         ("Assistant", "TMS link"), ("Assistant", "Risk")]
s.g("network")
for a, b in LINKS:
    (x1, y1), (x2, y2) = POS[a], POS[b]
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    near = math.dist((x1, y1), (x2, y2)) < 600                 # neighbours: a gentle bend
    k = 0.18 if near else 0.55
    qx, qy = mx + (CX - mx) * k, my + (CY - my) * k           # bend toward the bus
    s.raw(f'<path d="M{x1:.1f} {y1:.1f} Q{qx:.1f} {qy:.1f} {x2:.1f} {y2:.1f}" stroke="{BLUE}" stroke-opacity="0.28" stroke-width="1.4" fill="none"/>')
    for t, op in ((0.32, 0.9), (0.62, 0.45)):                  # messages in flight
        px = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * qx + t ** 2 * x2
        py = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * qy + t ** 2 * y2
        s.raw(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{BLUE}" fill-opacity="{op}"/>')
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
        return tool[2] + 26
    return B_R * 2

def draw_tool(tool, bx, by):
    w = bubble_w(tool); h = B_R * 2
    s.R(bx - w / 2, by - h / 2 + 2, w, h, INK, h / 2, ' fill-opacity="0.05"')
    s.R(bx - w / 2, by - h / 2, w, h, CARD, h / 2, f' stroke="{INK}" stroke-opacity="0.10"')
    if isinstance(tool, str):
        mark(tool, bx, by, 22)
    elif tool[0] == "cw":
        cargowise_icon(bx, by, 24)
    elif tool[0] == "tms":
        tms_word(tool[1], bx, by, tool[2])
    else:
        s.T(bx, by + 4.5, tool[1], 12.5, 600, MUT, anchor="middle")

for name, ang, orb, tools in NODES:
    x, y = POS[name]
    s.g(f"agent-{name.lower().replace(' ', '-')}")
    out = math.radians(ang)
    # spread the tools along the arc: each takes the room it needs across the arc's direction
    tx, ty = -math.sin(out), math.cos(out)
    ang_sizes = [(abs(bubble_w(tl) * tx) + abs(2 * B_R * ty) + 10) / orb for tl in tools]
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
    agent_mark(x, y - 10, 6)
    s.T(x, y + 15, name, 13, 600, anchor="middle")
    # the tools
    a = a0
    for tl, sz in zip(tools, ang_sizes):
        c = a + sz / 2
        draw_tool(tl, x + orb * math.cos(c), y + orb * math.sin(c))
        a += sz
    s.end()

s.g("disclosure")
s.T(M, 954, "Logos show where each agent works. Live today: the 60 public sources and MCP. "
    "TMS and mail are read from exports and files; native links come next.",
    12.5, 400, GREY)
s.end()

s.footer(9)
s.write("slide-09-integrations.svg")
