#!/usr/bin/env python3
"""Slide 09 - Integrations, third version: three layers, on the owner's pick.

Top, the tools a forwarder already runs, grouped by type. Middle, the agents in work order,
all on one bus. Bottom, the TMS link and the TMS systems it is built to point at. Each tool group
sits directly above the agents that use it, so every connection is a short vertical drop.

Official marks only, inlined byte-for-byte; a mark that cannot be had is left out, never
redrawn. Two footnotes say what is connected in this build, because a real logo reads as
a live integration, and that the prototype calls a US-hosted provider today."""
from kit import *
import json, math, pathlib, re

BLUE, BLUE_BG = "#006BFF", "#E8F1FF"   # only the agent icon
AMB_BG = "#F6EEE3"
GREY, GREY_BG = "#9A9A9A", "#F3F3F3"

s = Slide()
s.header("07 · INTEGRATIONS", "Works inside the tools you already run.",
         "Each agent works where its job already lives. They all talk on one bus.")

HERE = pathlib.Path(__file__).parent
CH = json.loads((HERE / "channel_marks.json").read_text())   # Iconify, CC0/MIT
TM = json.loads((HERE / "tms_marks.json").read_text())

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


# ---- the agents, in work order
AGENTS = ["Inbox", "Booking", "Docs", "Rate", "Playbook", "Comms", "Assistant", "Risk"]
# ---- the tools, grouped by type, each over the agents that use it (first slot, span, more)
GROUPS = [("Mail", ["Outlook", "Gmail"], 0, 1, "+ more"),
          ("Documents", ["PDF", "Word", "Excel", "Image"], 1, 2, "+ more"),
          ("Sheets &amp; files", ["GoogleSheets", "OneDrive", "GoogleDrive"], 3, 2, "+ more"),
          ("Chat", ["Teams", "Slack", "WhatsApp", "WeChat"], 5, 1, "+ more"),
          ("AI assistants", ["Claude", "ChatGPT", "Cursor"], 6, 1, "+ any MCP client"),
          ("Sources", ["NDR", "DW", "NASA"], 7, 1, "+ 57 more")]
SLOT = (W - 2 * M) / len(AGENTS)
def sx(i): return M + i * SLOT + SLOT / 2          # centre of agent slot i

def layer_label(x, y, lines):
    for k, ln in enumerate(lines):
        s.T(x, y + k * 15, ln, 11, 700, AMB, ls=1.4)

def arrow_down(x, y, col=INK, op=0.35):
    s.raw(f'<path d="M{x-5} {y-7} L{x} {y} L{x+5} {y-7} Z" fill="{col}" fill-opacity="{op}"/>')

# ============================================================ top: your tools
GY, GH = 334, 132
layer_label(M, GY - 10, ["YOUR TOOLS"])
s.g("your-tools")
for name, tools, first, span, more in GROUPS:
    x0 = M + first * SLOT + 6; w = span * SLOT - 12
    s.R(x0, GY, w, GH, CARD, 14, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(x0 + w / 2, GY + 30, name, 13.5, 600, "#4A4A4A", anchor="middle")
    n = len(tools); BR = 22; gap = 6          # one size for every logo
    tot = n * BR * 2 + (n - 1) * gap
    bx = x0 + w / 2 - tot / 2 + BR
    for tl in tools:
        s.raw(f'<circle cx="{bx:.1f}" cy="{GY + 74}" r="{BR}" fill="{BG}" stroke="{INK}" stroke-opacity="0.08"/>')
        mark(tl, bx, GY + 74, 28)
        bx += BR * 2 + gap
    s.T(x0 + w / 2, GY + 118, more, 11.5, 500, GREY, anchor="middle")
s.end()

# ============================================================ middle: the agents
AY, AH = 524, 92
s.g("drops")                                    # work flows down from each group to its agents
for name, tools, first, span, more in GROUPS:
    for i in range(first, first + span):
        s.line(sx(i), GY + GH, sx(i), AY - 2, INK, 0.25, 1.4)
        arrow_down(sx(i), AY - 1)
s.end()
s.g("agents")
for i, name in enumerate(AGENTS):
    w = SLOT - 20; x0 = sx(i) - w / 2
    s.R(x0, AY + 3, w, AH, INK, 14, ' fill-opacity="0.04"')
    s.R(x0, AY, w, AH, CARD, 14, f' stroke="{INK}" stroke-opacity="0.12"')
    agent_mark(sx(i), AY + 32, 8)
    s.T(sx(i), AY + 68, name, 17, 600, anchor="middle")
s.end()

# the bus: every agent on one line
BUS = AY + AH + 36
s.g("bus")
for i in range(len(AGENTS)):
    s.line(sx(i), AY + AH, sx(i), BUS, INK, 0.25, 1.4)
s.line(sx(0), BUS, sx(len(AGENTS) - 1), BUS, INK, 0.45, 2)
for i in range(len(AGENTS)):
    s.raw(f'<circle cx="{sx(i):.1f}" cy="{BUS}" r="4" fill="{INK}" fill-opacity="0.55"/>')
s.T(sx(0) - 6, BUS + 26, "SQRlane · 16 agents on one bus · every handoff between them recorded", 12, 600, INK)
s.T(sx(len(AGENTS) - 1) + 6, BUS + 26, "also on the bus: Routing, Planner, RFQ, Milestones, Exception, Invoice, Customs",
    11.5, 400, GREY, anchor="end")
s.end()

# ============================================================ bottom: any TMS, behind your approval
TY = BUS + 92
s.g("your-approval")
s.line(W / 2, BUS, W / 2, TY - 2, AMB, 0.9, 2.2)
arrow_down(W / 2, TY - 1, AMB, 1)
aw = 132; ay = BUS + 26
s.R(W / 2 - aw / 2, ay, aw, 28, INK, 14)
s.T(W / 2, ay + 18.5, "You approve", 12.5, 700, CARD, anchor="middle")
s.end()

layer_label(M, TY + 32, ["ANY TMS,", "BY EXPORT OR API"])
s.g("any-tms")
TW_, TH_ = 280, 64
PW_, PH_ = 184, 52
pills = [("cw", W / 2 - 520), ("SAP", W / 2 - 316), ("Oracle", W / 2 + 316), ("Descartes", W / 2 + 520)]
y = TY + TH_ / 2
s.line(pills[0][1], y, pills[-1][1], y, AMB, 0.45, 1.6)
for name, cx in pills:
    s.R(cx - PW_ / 2, y - PH_ / 2, PW_, PH_, CARD, PH_ / 2, f' stroke="{INK}" stroke-opacity="0.12"')
    if name == "cw":
        tms_word("CargoWise", cx, y, 116)
    else:
        tms_word(name, cx, y, {"SAP": 56, "Oracle": 108, "Descartes": 128}[name])
s.R(W / 2 - TW_ / 2, TY + 3, TW_, TH_, INK, 14, ' fill-opacity="0.04"')
s.R(W / 2 - TW_ / 2, TY, TW_, TH_, CARD, 14, f' stroke="{AMB}" stroke-opacity="0.6" stroke-width="1.4"')
agent_mark(W / 2 - 46, TY + TH_ / 2, 8)
s.T(W / 2 - 28, TY + TH_ / 2 + 6, "TMS link", 17, 600)
# second row: systems without an official mark, as plain names, and the open door
ry = TY + TH_ + 22
items = [("Riege Scope", "n"), ("AEB", "n"), ("DAKOSY", "n"), ("Portbase", "n"),
         ("Freight exchanges", "l"), ("TIMOCOM", "n"), ("Transporeon", "n"),
         ("+ any TMS with an export or API", "o")]
def iw(txt, kind): return round(len(txt) * 6.6 + (0 if kind == "l" else 26))
tot = sum(iw(a, k) for a, k in items) + 8 * (len(items) - 1) + 24
x = W / 2 - tot / 2
for txt, kind in items:
    w = iw(txt, kind)
    if kind == "l":
        x += 16
        s.T(x, ry + 19, txt, 11.5, 600, GREY)
    elif kind == "o":
        x += 8
        s.R(x, ry, w, 28, AMB_BG, 14, f' stroke="{AMB}" stroke-opacity="0.5" stroke-dasharray="4 3"')
        s.T(x + w / 2, ry + 18.5, txt, 12, 600, AMB, anchor="middle")
    else:
        s.R(x, ry, w, 28, GREY_BG, 14)
        s.T(x + w / 2, ry + 18.5, txt, 12, 600, "#4A4A4A", anchor="middle")
    x += w + 8
s.end()

s.g("disclosure")
s.T(M, 956, "Logos are examples, not the full list. Live today: the 60 public sources and MCP. Your TMS is read from an "
    "export or its API; approved changes go back the same way. Native connectors come next.", 12.5, 400, GREY)
s.end()

s.footer(9)
s.write("slide-09-integrations.svg")
