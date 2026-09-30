#!/usr/bin/env python3
"""Slide 07 - The How 1/2: the desk. Left, the dashboard's Today view, kept minimal:
an Ask box (src/ask.py is live, and every suggested question below is one it answers),
four stat cards and one row of what came in. Every figure is counted from one offline
run of the desk (src/workflow.run(use_llm=False)) on its synthetic inbox. Right, the
16 agents, step by step, with how many agents work each step.

Colours are the dashboard's own tokens only (static/index.html), one job each: blue is
an agent (every count chip, the Ask box), amber is the Playbook's check, black is the
one thing a person does - approve. Green only for "done", greys for the rest. The risk layer is a very light grey row; slide 08 is its job.
Tags follow src/roster.py: Planner scripted, TMS link demo. Nothing is sent or written."""
from kit import *

BLUE, BLUE_BG = "#006BFF", "#E8F1FF"
GREEN, GREEN_BG = "#0F7B3F", "#E7F5EC"
AMBR, AMBR_BG = "#96580A", "#FDF3E3"
GREY, GREY_BG, LINE = "#9A9A9A", "#F3F3F3", "#E6E6E6"

s = Slide()
s.header("06 · THE HOW, 1 OF 2", "SQRlane does the desk work itself.",
         "Every mail read once. Sixteen agents do the work. Nothing leaves without you.")
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
    body = re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + "o7-" + g.group(2), m["body"])
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
for name, count, on in (("Today", None, True), ("Inbox", "13", False), ("Approvals", "24", False),
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
s.T(MX, TOP + 82, "Today", 26, 600, ls=-0.6)
s.T(MX, TOP + 105, "The desk worked the morning inbox.", 13, 400, MUT)
s.end()

# ---- the toast the bell raised: IN-111 lands, the Customs agent already has it
TW_, TX_ = 372, MX + MW - 372
s.g("mail-toast")
soft_card(TX_, TOP + 54, TW_, 60, 14)
s.R(TX_ + 12, TOP + 64, 40, 40, GREY_BG, 10)
mark("Outlook", TX_ + 18, TOP + 70, 28)
s.T(TX_ + 64, TOP + 78, "New mail · Maison Cardelle SAS", 11, 500, GREY)
s.T(TX_ + 64, TOP + 98, "Arrival notice: MEDU-2209471", 13, 600)
agent_mark(TX_ + TW_ - 88, TOP + 84, 5)
s.T(TX_ + TW_ - 78, TOP + 88, "Customs", 11.5, 600, BLUE)
s.end()

# ---- the morning in one line: every figure counted from workflow.run()
OY, OH = TOP + 126, 112
STEPS = [("13", "mails in", "8 end to end · 5 held"),
         ("100", "agent messages", "every handoff on record"),
         ("8", "Playbook fixes", "sent back, then fixed"),
         ("24", "waiting for you", "10 drafts · 14 TMS changes"),
         ("0", "sent or written", "until you approve")]
s.g("the-morning")
s.card(MX, OY, MW, OH, 12)
s.T(MX + 18, OY + 26, "This morning", 13, 600)
s.T(MX + MW - 18, OY + 26, "13 mails, start to finish", 12, 400, GREY, anchor="end")
sw_ = (MW - 36) / 5
for k, (n, lab, sub) in enumerate(STEPS):
    x = MX + 18 + k * sw_
    s.T(x, OY + 64, n, 30, 600, GREEN if n == "0" else INK, ls=-1)
    s.T(x, OY + 83, lab, 12, 600, "#3A3A3A")
    s.T(x, OY + 99, sub, 10.5, 400, GREY)
    if k < 4:
        s.T(x + sw_ - 16, OY + 62, "›", 20, 400, "#C8C8C8")
s.end()

# ---- the chat window: its own header, its own tint, bubbles
CY0 = OY + OH + 14; CHh = BOT - 20 - CY0
CHAT_BG = "#F6F8FB"
s.g("chat-window")
s.R(MX, CY0, MW, CHh, CHAT_BG, 14, f' stroke="{INK}" stroke-opacity="0.12"')
s.R(MX, CY0, MW, 40, CARD, 14); s.R(MX, CY0 + 26, MW, 14, CARD)
s.rule(CY0 + 40, 0.10, MX, MW)
agent_mark(MX + 22, CY0 + 20)
s.T(MX + 38, CY0 + 25, "Ask SQRlane", 13.5, 600)
s.T(MX + 126, CY0 + 25, "the agent who owns it answers", 12, 400, GREY)
s.raw(f'<circle cx="{MX + MW - 76}" cy="{CY0 + 20}" r="3.5" fill="{GREEN}"/>')
s.T(MX + MW - 68, CY0 + 24.5, "LIVE", 10.5, 700, GREEN, ls=0.8)
cy = CY0 + 50
q = "Where is MEDU-1774390?"
qw = round(len(q) * 7.6 + 32)
s.R(MX + MW - 16 - qw, cy, qw, 34, INK, 17)
s.T(MX + MW - 16 - qw / 2, cy + 22, q, 13.5, 500, CARD, anchor="middle")
cy += 42
BWb = 470
s.R(MX + 16, cy, BWb, 42, CARD, 14, f' stroke="{INK}" stroke-opacity="0.10"')
s.T(MX + 30, cy + 26, "Milestones agent", 12, 600, BLUE)
s.T(MX + 138, cy + 26, "SHP-004, Shenzhen to Antwerp, is on plan.", 13, 400, INK)
cy += 48
DHh = 72
s.R(MX + 16, cy, BWb, DHh, CARD, 14, f' stroke="{INK}" stroke-opacity="0.10"')
mark("Outlook", MX + 30, cy + 12, 16)
s.T(MX + 54, cy + 25, "Reply to Pieter Claes: RE: Where is MEDU-1774390?", 12.5, 600)
s.T(MX + 30, cy + 44, "Dear Pieter Claes, MEDU-1774390 (electronics) is on the water …", 12, 400, MUT)
s.T(MX + 30, cy + 62, "Draft, not sent", 11, 600, AMBR)
s.R(MX + 16 + BWb - 92, cy + DHh - 34, 78, 26, INK, 8)
s.T(MX + 16 + BWb - 53, cy + DHh - 16, "Approve", 12, 600, CARD, anchor="middle")
# the input, with suggestions above it
IY = CY0 + CHh - 52
sx = MX + 16
for sq in ("What is waiting for my approval?", "Price 2 x 40HC Shanghai to Rotterdam", "Which invoices are disputed?"):
    w = round(len(sq) * 6.1 + 22)
    s.R(sx, IY - 34, w, 26, CARD, 13, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(sx + w / 2, IY - 17, sq, 11.5, 500, "#4A4A4A", anchor="middle")
    sx += w + 8
s.R(MX + 12, IY, MW - 24, 42, CARD, 21, f' stroke="{INK}" stroke-opacity="0.14"')
s.T(MX + 32, IY + 26, "Ask the desk anything", 13, 400, GREY)
s.raw(f'<circle cx="{MX + MW - 33}" cy="{IY + 21}" r="14" fill="{INK}"/>')
s.raw(f'<path d="M{MX+MW-33} {IY+27} v-12 M{MX+MW-38} {IY+20} l5 -5 l5 5" stroke="{CARD}" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
s.end()
s.end()

# ================================================================ how the work is structured
HX = FX + FW + 24; HW = W - M - HX
hx, hw = HX + 24, HW - 48
s.g("how-the-work-is-structured")
s.card(HX, TOP, HW, BOT - TOP)
s.T(hx, TOP + 36, "HOW THE WORK IS STRUCTURED", 13, 600, AMB, ls=1.4)
s.T(HX + HW - 24, TOP + 36, "14 live · Planner scripted · TMS link demo", 12, 500, GREY, anchor="end")

def arrow(y1, y2, x=None):
    x = x or hx + hw / 2
    s.line(x, y1, x, y2 - 5, INK, 0.3, 1.5)
    s.raw(f'<path d="M{x-4.5} {y2-6} L{x} {y2} L{x+4.5} {y2-6}" stroke="{INK}" stroke-opacity="0.3" stroke-width="1.5" fill="none"/>')

def count_chip(x, y, text, fill=BLUE_BG, ink=BLUE, anchor="start"):
    """The agent count on every step: '1 agent', '2 agents'."""
    w = round(len(text) * 6 + 16)
    x0 = x - w if anchor == "end" else x
    s.R(x0, y, w, 19, fill, 9.5)
    s.T(x0 + w / 2, y + 13.5, text, 10.5, 600, ink, anchor="middle")
    return w

def agents(n): return f"{n} agent" + ("s" if n > 1 else "")

y = TOP + 56
# the risk layer: light grey, detailed on slide 08
s.g("risk-layer")
s.R(hx, y, hw, 40, GREY_BG, 10, f' stroke="{INK}" stroke-opacity="0.10" stroke-dasharray="4 3"')
s.T(hx + 14, y + 25, "Risk layer", 13.5, 600, "#7A7A7A")
cw = count_chip(hx + 96, y + 10, agents(4), CARD, "#7A7A7A")
s.T(hx + 96 + cw + 12, y + 25, "watches 60 sources, decides reroute or hold", 11.5, 400, "#8A8A8A")
s.T(hx + hw - 14, y + 25, "slide 08", 11.5, 600, "#8A8A8A", anchor="end")
s.raw('<defs><linearGradient id="risk-fade" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0.35" stop-color="{CARD}" stop-opacity="0"/><stop offset="0.95" stop-color="{CARD}" stop-opacity="1"/>'
      '</linearGradient></defs>')
s.R(hx - 2, y - 2, hw + 4, 44, "url(#risk-fade)")
s.end()
y += 40; arrow(y, y + 12); y += 14

# the two front doors
s.g("front-doors")
IW = hw - 248
s.R(hx, y, IW, 40, CARD, 10, f' stroke="{INK}" stroke-opacity="0.16"')
s.T(hx + 14, y + 25, "Inbox", 13.5, 600, INK)
cw = count_chip(hx + 62, y + 10, agents(1))
s.T(hx + 62 + cw + 12, y + 25, "reads every mail, routes it to its owner", 11.5, 400, MUT)
ax0 = hx + IW + 8
s.R(ax0, y, 240, 40, CARD, 10, f' stroke="{INK}" stroke-opacity="0.16"')
s.T(ax0 + 14, y + 25, "Assistant", 13.5, 600, INK)
cw = count_chip(ax0 + 88, y + 10, agents(1))
s.T(ax0 + 88 + cw + 10, y + 25, "your questions", 11.5, 400, MUT)
s.end()
y += 40; arrow(y, y + 12); y += 14

# the desk: six stages, in the order a shipment lives, each with its agent count
STAGES = [("01", "Quote", ["Rate", "RFQ"], "Prices it, drafts the quote"),
          ("02", "Book", ["Booking"], "Opens the booking from the mail"),
          ("03", "Documents", ["Docs"], "Checks each field on the B/L"),
          ("04", "In transit", ["Milestones", "Exception"], "Updates the ETA, flags rollovers"),
          ("05", "Arrival", ["Customs"], "Prepares the entry, never files"),
          ("06", "Billing", ["Invoice"], "Checks the bill against the rate")]
s.g("the-desk")
DH = 234
s.R(hx, y, hw, DH, BG, 12, f' stroke="{INK}" stroke-opacity="0.10"')
s.T(hx + 14, y + 22, "THE DESK", 10.5, 700, MUT, ls=1.2)
s.T(hx + 84, y + 22, "8 agents, in the order a shipment lives", 11.5, 400, MUT)
cw3 = (hw - 28 - 16) / 3; chh = 92
for k, (num, name, who, job) in enumerate(STAGES):
    r, c = divmod(k, 3)
    x = hx + 14 + c * (cw3 + 8); yy = y + 36 + r * (chh + 8)
    s.g("stage-" + name.lower().replace(" ", "-"))
    s.R(x, yy, cw3, chh, CARD, 10, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(x + 14, yy + 26, num, 11, 700, GREY, ls=0.6)
    s.T(x + 38, yy + 26, name, 14.5, 600, ls=-0.2)
    count_chip(x + cw3 - 12, yy + 11, agents(len(who)), anchor="end")
    s.T(x + 14, yy + 47, job, 11.5, 400, MUT)
    bx = x + 14
    for a in who:
        w = round(len(a) * 6.4 + 16)
        s.R(bx, yy + 60, w, 20, GREY_BG, 5)
        s.T(bx + w / 2, yy + 74, a, 11, 500, "#3A3A3A", anchor="middle")
        bx += w + 5
    s.end()
s.end()
y += DH
for c in range(3):                       # every stage hands its output to the Playbook
    x = hx + 14 + c * (cw3 + 8) + cw3 / 2
    s.line(x, y, x, y + 8, AMB, 0.6, 1.5)
y += 8
s.g("playbook")
s.R(hx, y, hw, 36, AMBR_BG, 10)
s.T(hx + 14, y + 23, "Playbook", 13.5, 600, AMB)
cw = count_chip(hx + 86, y + 9, agents(1), CARD, AMB)
s.T(hx + 86 + cw + 12, y + 23, "checks every output against the customer's rules", 11.5, 400, AMB)
s.end()
y += 36; arrow(y, y + 12); y += 14

# the gate, then the record
s.g("gate-and-record")
GW = (hw - 28) / 2
s.R(hx, y, GW, 40, INK, 10)
s.T(hx + 14, y + 25, "You approve", 13.5, 700, CARD)
s.T(hx + 108, y + 25, "every draft, every change", 11.5, 400, "#D6D6D6")
ax1 = hx + GW + 4
s.line(ax1, y + 20, ax1 + 15, y + 20, INK, 0.3, 1.5)
s.raw(f'<path d="M{ax1+14} {y+15.5} L{ax1+20} {y+20} L{ax1+14} {y+24.5}" stroke="{INK}" stroke-opacity="0.3" stroke-width="1.5" fill="none"/>')
tx = hx + GW + 28
s.R(tx, y, GW, 40, CARD, 10, f' stroke="{INK}" stroke-opacity="0.16"')
s.T(tx + 14, y + 25, "TMS link", 13.5, 600, INK)
cw = count_chip(tx + 84, y + 10, agents(1))
s.T(tx + 84 + cw + 10, y + 25, "writes it onto the booking", 11.5, 400, MUT)
s.end()
y += 40

# one mail, worked together - the run's own path for IN-108
s.g("worked-together")
y += 28
s.T(hx, y, "ONE MAIL, TOGETHER", 10.5, 700, MUT, ls=1.2)
s.T(hx + 150, y, "IN-108, a vaccine booking", 11.5, 400, MUT)
y += 12
cx = hx
steps = [("Inbox", None), ("Booking", None), ("Docs", None), ("Rate", None),
         ("Playbook sends it back", "amb"), ("Booking rebooks", None), ("You approve", "ink")]
for k, (name, kind) in enumerate(steps):
    w = round(len(name) * 6.2 + 16)
    fill, ink = {"amb": (AMB, CARD), "ink": (INK, CARD)}.get(kind, (GREY_BG, "#3A3A3A"))
    s.R(cx, y, w, 22, fill, 5)
    s.T(cx + w / 2, y + 15, name, 11, 600 if kind else 500, ink, anchor="middle")
    cx += w
    if k < len(steps) - 1:
        s.T(cx + 4, y + 15, "›", 12, 500, MUT); cx += 14
s.end()
s.end()

s.T(M, 946, "Ask the desk anything. Every step recorded, and approved by you.", 28, 600, ls=-0.6)
s.footer(7)
s.write("slide-07-the-how-1.svg")
