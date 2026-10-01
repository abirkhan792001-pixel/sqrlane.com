#!/usr/bin/env python3
"""Slide 09 - Integrations, third version: three layers, on the owner's pick.

Top, the tools a forwarder already runs, grouped by type. Middle, the agents in work order,
each with the open-weight model it is built to run (the whitepaper's agent table), all on
one bus. Bottom, the TMS link and the TMS systems it is built to point at. Each tool group
sits directly above the agents that use it, so every connection is a short vertical drop.

Official marks only, inlined byte-for-byte; a mark that cannot be had is left out, never
redrawn. Two footnotes say what is connected in this build, because a real logo reads as
a live integration, and that the prototype calls a US-hosted provider today."""
from kit import *
import json, math, pathlib, re

BLUE, BLUE_BG = "#006BFF", "#E8F1FF"
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


# ---- the agents, in work order, with the model each is built to run
AGENTS = [("Inbox", "Gemma-3-27B"), ("Booking", "code only"), ("Docs", "Qwen2.5-VL-72B"),
          ("Rate", "code only"), ("Playbook", "Qwen3-235B"), ("Comms", "Llama-3.3-70B"),
          ("Assistant", "Gemma-3-27B"), ("Risk", "Qwen3-235B")]
# ---- the tools, grouped by type, each over the agents that use it (first slot, span)
GROUPS = [("Mail", ["Outlook", "Gmail"], 0, 1),
          ("Documents", ["PDF", "Word", "Excel", "Image"], 1, 2),
          ("Sheets &amp; files", ["GoogleSheets", "OneDrive", "GoogleDrive"], 3, 2),
          ("Chat", ["Teams", "Slack", "WhatsApp", "WeChat"], 5, 1),
          ("AI assistants", ["Claude", "ChatGPT", "Cursor"], 6, 1),
          ("Sources", ["NDR", "DW", "NASA", ("more", "+57")], 7, 1)]
SLOT = (W - 2 * M) / len(AGENTS)
def sx(i): return M + i * SLOT + SLOT / 2          # centre of agent slot i

def layer_label(y, text):
    s.T(M, y, text, 11, 700, GREY, ls=1.4)

# ============================================================ top: your tools
GY, GH = 334, 128
layer_label(GY - 10, "YOUR TOOLS")
s.g("your-tools")
for name, tools, first, span in GROUPS:
    x0 = M + first * SLOT + 6; w = span * SLOT - 12
    s.R(x0, GY, w, GH, CARD, 14, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(x0 + w / 2, GY + 30, name, 13.5, 600, "#4A4A4A", anchor="middle")
    n = len(tools); BR = 22; gap = 6          # one size for every logo; fits four in a card
    tot = n * BR * 2 + (n - 1) * gap
    bx = x0 + w / 2 - tot / 2 + BR
    for tl in tools:
        s.raw(f'<circle cx="{bx:.1f}" cy="{GY + 80}" r="{BR}" fill="{BG}" stroke="{INK}" stroke-opacity="0.08"/>')
        if isinstance(tl, str):
            mark(tl, bx, GY + 80, 28)
        else:
            s.T(bx, GY + 85, tl[1], 14, 600, MUT, anchor="middle")
        bx += BR * 2 + gap
s.end()

# ============================================================ middle: the agents
AY, AH = 532, 120
s.g("drops")                                    # each group to the agents under it
for name, tools, first, span in GROUPS:
    for i in range(first, first + span):
        s.line(sx(i), GY + GH, sx(i), AY, BLUE, 0.35, 1.4)
        s.raw(f'<circle cx="{sx(i):.1f}" cy="{AY - 1}" r="3" fill="{BLUE}" fill-opacity="0.6"/>')
s.end()
s.g("agents")
for i, (name, mdl) in enumerate(AGENTS):
    w = SLOT - 20; x0 = sx(i) - w / 2
    s.R(x0, AY + 3, w, AH, INK, 14, ' fill-opacity="0.04"')
    s.R(x0, AY, w, AH, CARD, 14, f' stroke="{BLUE}" stroke-opacity="0.35" stroke-width="1.2"')
    agent_mark(sx(i), AY + 30, 8)
    s.T(sx(i), AY + 66, name, 17, 600, anchor="middle")
    code = mdl == "code only"
    mw = round(len(mdl) * 6.2 + 20)
    s.R(sx(i) - mw / 2, AY + 82, mw, 22, GREY_BG if code else BLUE_BG, 11)
    s.T(sx(i), AY + 97, mdl, 11, 600, GREY if code else BLUE, anchor="middle")
s.end()

# the bus: every agent on one line
BUS = AY + AH + 44
s.g("bus")
for i in range(len(AGENTS)):
    s.line(sx(i), AY + AH, sx(i), BUS, BLUE, 0.35, 1.4)
s.line(sx(0), BUS, sx(len(AGENTS) - 1), BUS, BLUE, 0.6, 2)
for i in range(len(AGENTS)):
    s.raw(f'<circle cx="{sx(i):.1f}" cy="{BUS}" r="4" fill="{BLUE}"/>')
s.T(sx(0) - 6, BUS + 26, "SQRlane · 16 agents on one bus · every handoff between them recorded", 12, 600, BLUE)
s.T(sx(len(AGENTS) - 1) + 6, BUS + 26, "also on the bus: Routing, Planner, RFQ, Milestones, Exception, Invoice, Customs",
    11.5, 400, GREY, anchor="end")
s.end()

# ============================================================ bottom: your TMS
TY = BUS + 60
layer_label(TY + 43, "YOUR TMS")
s.g("your-tms")
s.line(W / 2, BUS, W / 2, TY, BLUE, 0.6, 2)
TW_, TH_ = 300, 76
PW_, PH_ = 196, 56
pills = [("cw", W / 2 - 560), ("SAP", W / 2 - 340), ("Oracle", W / 2 + 340), ("Descartes", W / 2 + 560)]
y = TY + TH_ / 2
s.line(pills[0][1], y, pills[-1][1], y, BLUE, 0.35, 1.4)      # one line through all, drawn first
for name, cx in pills:
    s.R(cx - PW_ / 2, y - PH_ / 2, PW_, PH_, CARD, PH_ / 2, f' stroke="{INK}" stroke-opacity="0.12"')
    if name == "cw":
        tms_word("CargoWise", cx, y, 120)
    else:
        tms_word(name, cx, y, {"SAP": 60, "Oracle": 112, "Descartes": 132}[name])
s.R(W / 2 - TW_ / 2, TY + 3, TW_, TH_, INK, 14, ' fill-opacity="0.04"')
s.R(W / 2 - TW_ / 2, TY, TW_, TH_, CARD, 14, f' stroke="{BLUE}" stroke-opacity="0.35" stroke-width="1.2"')
agent_mark(W / 2 - 92, TY + 35, 7)
s.T(W / 2 - 74, TY + 31, "TMS link", 16, 600)
s.R(W / 2 - 74, TY + 41, 82, 20, GREY_BG, 10)
s.T(W / 2 - 33, TY + 55, "code only", 11, 600, GREY, anchor="middle")
s.end()

s.g("disclosure")
s.T(M, 946, "Logos show where each agent works. Live today: the 60 public sources and MCP. "
    "TMS and mail are read from exports and files; native links come next.", 12.5, 400, GREY)
s.T(M, 966, "Model chips: the open-weight model each agent is built to run, hosted in the EU. Code-only agents compute "
    "exact answers (prices, records) and run no model. The prototype calls a US-hosted provider today.", 12.5, 400, GREY)
s.end()

s.footer(9)
s.write("slide-09-integrations.svg")
