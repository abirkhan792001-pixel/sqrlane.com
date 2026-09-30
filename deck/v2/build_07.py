#!/usr/bin/env python3
"""Slide 07 - The How 1/2: the desk. Left, the product: the dashboard's Today view,
drawn from one offline run of the desk (src/workflow.run, rules only) - 13 mails,
5 held for a person, 24 drafts and TMS changes at the gate. Every row, path, reason
and subject below is that run's own output; nothing is illustrative. Right, how the
16 agents share the work, with the systems at both ends tagged Today or Next.

The risk layer (feed, board, reroute/hold) is deliberately NOT on this slide: it is
slide 08's whole job. Tags follow src/roster.py: Planner scripted, TMS link demo.
Nothing is sent or written: the caption in the browser bar says the run is a demo."""
import json, pathlib, re
from kit import *

HERE = pathlib.Path(__file__).parent
CH = json.loads((HERE / "channel_marks.json").read_text())   # Iconify, CC0/MIT
TM = json.loads((HERE / "tms_marks.json").read_text())       # from static/landing.html #stack
GREEN, BLUE, BLUE_BG = "#0F7B3F", "#1F5FA8", "#E8F0FA"
_n = [0]

def mark(name, x, y, size):
    """An official mark, byte-for-byte, scaled into a size x size box. Never redrawn."""
    _n[0] += 1
    if name in CH:
        m = CH[name]; sc = size / max(m["w"], m["h"])
        body = re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + f"c{_n[0]}-" + g.group(2), m["body"])
        dx = x + (size - m["w"] * sc) / 2; dy = y + (size - m["h"] * sc) / 2
        s.raw(f'<g id="mark-{name.lower()}" transform="translate({dx:.1f} {dy:.1f}) scale({sc:.4f})">{body}</g>')

def wordmark(name, x, y, h):
    """A TMS vendor's own wordmark, fitted to height h. Returns the width drawn."""
    m = TM[name]; w = m["w"] * h / m["h"]
    if m["kind"] == "png":
        s.raw(f'<image id="mark-{name.lower()}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" href="{m["href"]}"/>')
    else:
        _n[0] += 1
        body = re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + f"t{_n[0]}-" + g.group(2), m["body"])
        s.raw(f'<g id="mark-{name.lower()}" transform="translate({x:.1f} {y:.1f}) scale({h / m["h"]:.5f})">{body}</g>')
    return w

def chip(x, y, text, fill, ink, size=10, w=None):
    w = w or round(len(text) * size * 0.66 + 14)
    s.R(x, y, w, size + 8, fill, 4)
    s.T(x + w / 2, y + size + 2.5, text, size, 600, ink, anchor="middle", ls=0.6)
    return w

def tag(x, y, text):   # TODAY / NEXT, right-aligned at x
    today = text == "TODAY"
    w = 46 if today else 38
    chip(x - w, y, text, GREEN if today else TRACK, BG if today else MUT, 9, w)

s = Slide()
s.header("06 · THE HOW, 1 OF 2", "SQRlane does the desk work itself.",
         "Every mail read once. Sixteen agents do the work. Nothing leaves without you.")

TOP, BOT = 306, 890

# =============================================================== the product
FX, FW = M, 1052
s.g("dashboard")
s.R(FX, TOP, FW, BOT - TOP, CARD, 14, f' stroke="{INK}" stroke-opacity="0.14"')
# browser bar
s.g("browser-bar")
s.R(FX, TOP, FW, 40, "#F2F2F2", 14)
s.R(FX, TOP + 26, FW, 14, "#F2F2F2")
s.rule(TOP + 40, 0.10, FX, FW)
for i, c in enumerate(("#E0E0E0", "#E0E0E0", "#E0E0E0")):
    s.raw(f'<circle cx="{FX + 22 + i * 18}" cy="{TOP + 20}" r="5.5" fill="{c}"/>')
s.R(FX + 380, TOP + 9, 292, 22, CARD, 6, f' stroke="{INK}" stroke-opacity="0.08"')
s.T(FX + 526, TOP + 25, "SQRlane · Desk", 12, 500, MUT, anchor="middle")
s.R(FX + FW - 212, TOP + 9, 196, 22, AMB, 6, ' fill-opacity="0.10"')
s.T(FX + FW - 114, TOP + 25, "Demo run · synthetic inbox", 11.5, 600, AMB, anchor="middle")
s.end()

# sidebar
SBW = 172; SY0 = TOP + 41
s.g("sidebar")
s.R(FX + 1, SY0, SBW, BOT - SY0 - 1, "#FBFBFB")
s.R(FX + SBW, SY0, 1, BOT - SY0 - 1, INK, extra=' fill-opacity="0.08"')
s.R(FX + 18, SY0 + 20, 22, 22, INK, 6)
s.raw(f'<path d="M{FX+23.5} {SY0+36}h11 M{FX+23.5} {SY0+31}h7.5 M{FX+23.5} {SY0+26}h4" stroke="{BG}" stroke-width="1.8" stroke-linecap="round" fill="none"/>')
s.T(FX + 50, SY0 + 37, "sqrlane", 15, 600)
navy = SY0 + 78
def nav_group(title, items, y):
    s.T(FX + 20, y, title, 10, 600, MUT, ls=1.2)
    y += 12
    for name, count, on in items:
        if on: s.R(FX + 10, y, SBW - 20, 28, TRACK, 6)
        s.T(FX + 20, y + 19, name, 13, 600 if on else 500, INK if on else "#3A3A3A")
        if count:
            cw = len(count) * 7 + 12
            s.R(FX + SBW - 16 - cw, y + 6, cw, 17, BLUE_BG, 8.5)
            s.T(FX + SBW - 16 - cw / 2, y + 18.5, count, 10.5, 600, BLUE, anchor="middle")
        y += 32
    return y + 14
navy = nav_group("DESK", [("Today", None, True), ("Inbox", "13", False),
                          ("Approvals", "24", False), ("Lessons", None, False)], navy)
navy = nav_group("BOOK", [("Shipments", "7", False), ("TMS link", None, False)], navy)
navy = nav_group("RISK", [("Risk feed", None, False), ("Board", None, False)], navy)
s.end()

# main column
MX = FX + SBW + 24; MW = FX + FW - 24 - MX
s.g("page-header")
s.T(MX, TOP + 78, "Today", 24, 600, ls=-0.5)
s.T(MX, TOP + 99, "The desk worked the morning inbox. Nothing is sent or written until you approve.", 13, 400, MUT)
bw = 132
s.R(MX + MW - bw, TOP + 60, bw, 30, CARD, 6, f' stroke="{INK}" stroke-opacity="0.14"')
s.T(MX + MW - bw / 2, TOP + 80, "Work the inbox", 12.5, 600, anchor="middle")
s.end()

# four stat cards - counted from the run
SC = [("Mails worked", "13", "every mail routed to its owner"),
      ("Handled end to end", "8 of 13", "no person needed before approval"),
      ("Held for a person", "5", "held rather than guessed"),
      ("Waiting for you", "24", "drafts and TMS changes")]
SCY, SCH, gap = TOP + 116, 80, 12
scw = (MW - 3 * gap) / 4
s.g("stat-cards")
for i, (lab, val, cap) in enumerate(SC):
    x = MX + i * (scw + gap)
    s.card(x, SCY, scw, SCH, 12)
    s.T(x + 16, SCY + 24, lab, 12, 500, MUT)
    s.T(x + 16, SCY + 54, val, 28, 600, AMB if i == 3 else INK, ls=-0.8)
    s.T(x + 16, SCY + 70, cap, 11, 400, MUT)
s.end()

# ---- inbox panel: each mail, and the agents it passed through (the run's own path)
PY = SCY + SCH + 12; PH = BOT - 16 - PY
IW = 470
s.g("inbox-panel")
s.card(MX, PY, IW, PH, 12)
s.T(MX + 16, PY + 28, "Inbox", 15, 600)
s.T(MX + 62, PY + 28, "13 mails · who worked each one", 12, 400, MUT)
AG = {"inbox": "Inbox", "rfq": "RFQ", "rate": "Rate", "playbook": "Playbook", "docs": "Docs",
      "booking": "Booking", "exception": "Exception", "milestones": "Milestones",
      "routing": "Routing", "invoice": "Invoice", "customs": "Customs", "planner": "Planner"}
ROWS = [("IN-101", "Pricing request: Shenzhen to Antwerp, 3 x 40HC", ["inbox", "rfq", "rate", "playbook"], None),
        ("IN-103", "Final documents for HLCU-2261188", ["inbox", "docs", "playbook", "exception"], "flag"),
        ("IN-105", "Rollover notice: CMDU-4410765", ["inbox", "milestones", "playbook", "exception", "routing"], "held"),
        ("IN-108", "Please book 1 x 40RH vaccines Ningbo to Hamburg", ["inbox", "booking", "docs", "rate", "playbook", "planner"], "fix"),
        ("IN-110", "Freight invoice HL-88213407", ["inbox", "invoice", "playbook"], None)]
EXP = 46                                   # the opened row's extra height
ry = PY + 42; RH = (PH - 48 - EXP) / len(ROWS)
for rid, subj, path, st in ROWS:
    h = RH + (EXP if st == "fix" else 0)
    s.g("mail-" + rid.lower())
    if st == "fix":                        # the opened row: selected, with the bus's own words
        s.R(MX + 8, ry + 3, IW - 16, h - 6, BG, 8, f' stroke="{INK}" stroke-opacity="0.12"')
    else:
        s.rule(ry, 0.07, MX + 16, IW - 32)
    s.T(MX + 16, ry + 21, rid, 11.5, 600, MUT)
    s.T(MX + 70, ry + 21, subj, 12.5, 500)
    cx = MX + 70
    for a in path:
        name = AG[a]
        other = a in ("routing", "planner")          # the risk layer's agents, in blue
        w = round(len(name) * 6.3 + 14)
        fill, ink = (BLUE_BG, BLUE) if other else (TRACK, "#3A3A3A")
        if a == "playbook" and st == "fix":
            fill, ink = (AMB, BG); pb = cx + w / 2
        s.R(cx, ry + 29, w, 18, fill, 4)
        s.T(cx + w / 2, ry + 42, name, 10.5, 500, ink, anchor="middle")
        cx += w + 4
        if a != path[-1]:
            s.T(cx + 1, ry + 42, "›", 11, 500, MUT); cx += 10
    if st == "fix":
        ny = ry + 56
        s.raw(f'<path d="M{pb-5} {ny} L{pb} {ny-6} L{pb+5} {ny} Z" fill="{AMB}" fill-opacity="0.14"/>')
        s.R(MX + 70, ny, IW - 70 - 20, 38, AMB, 6, ' fill-opacity="0.10"')
        s.T(MX + 80, ny + 15, "PLAYBOOK SENT IT BACK · RULE: GDP-AUDITED REEFER CARRIERS ONLY", 9, 700, AMB, ls=0.7)
        s.T(MX + 80, ny + 31, "ONE is not an approved carrier - use Maersk or Hapag-Lloyd.", 11.5, 500, INK)
    if st == "held":
        chip(MX + IW - 16 - 96, ry + 10, "HELD FOR YOU", AMB, BG, 9, 96)
    elif st == "flag":
        chip(MX + IW - 16 - 96, ry + 10, "1 MISMATCH", "#FBEFE0", AMB, 9, 96)
    s.end()
    ry += h
s.end()

# ---- approvals panel: grouped by booking, the run's own outputs
AX = MX + IW + 14; AW = MX + MW - AX
s.g("approvals-panel")
s.card(AX, PY, AW, PH, 12)
s.T(AX + 16, PY + 28, "Approvals", 15, 600)
s.T(AX + AW - 16, PY + 28, "24 waiting", 12, 500, MUT, anchor="end")
seg = [("Awaiting", True), ("Approved", False), ("All", False)]
sx = AX + 16; sgy = PY + 42
s.R(sx, sgy, AW - 32, 26, TRACK, 6)
sw = (AW - 36) / 3
for i, (lab, on) in enumerate(seg):
    if on: s.R(sx + 2 + i * sw, sgy + 2, sw, 22, CARD, 5, f' stroke="{INK}" stroke-opacity="0.08"')
    s.T(sx + 2 + i * sw + sw / 2, sgy + 17, lab, 11.5, 600 if on else 500, INK if on else MUT, anchor="middle")
GROUPS = [("NEW-108", "new booking, from IN-108", [
              ("TMS", "New booking, Hapag-Lloyd", "QUEUED - not written"),
              ("Mail", "Booking request to carrier", "DRAFT - not sent"),
              ("Mail", "Confirmation to customer", "DRAFT - not sent")]),
          ("SHP-005", "from IN-110", [
              ("Mail", "Invoice query to carrier", "DRAFT - not sent")])]
gy = sgy + 44
approve_at = None
for bk, src, items in GROUPS:
    s.T(AX + 16, gy, bk, 11.5, 700, INK, ls=0.4)
    s.T(AX + 16 + len(bk) * 8 + 8, gy, src, 11, 400, MUT)
    gy += 10
    for k, (kind, what, status) in enumerate(items):
        s.g("approval-" + bk.lower() + "-" + str(k + 1))
        s.R(AX + 12, gy, AW - 24, 46, BG if not (bk == "NEW-108" and k == 0) else "#F3F3F3", 8,
            f' stroke="{INK}" stroke-opacity="0.08"')
        s.R(AX + 22, gy + 15, 14, 14, CARD, 3, f' stroke="{INK}" stroke-opacity="0.3"')
        s.T(AX + 44, gy + 20, what, 12.5, 500)
        s.T(AX + 44, gy + 37, kind.upper(), 9.5, 700, MUT, ls=0.8)
        s.T(AX + 44 + (30 if kind == "TMS" else 36), gy + 37, status, 10.5, 600, AMB)
        bx = AX + AW - 24 - 66
        s.R(bx, gy + 12, 60, 22, INK if (bk == "NEW-108" and k == 0) else CARD, 5,
            "" if (bk == "NEW-108" and k == 0) else f' stroke="{INK}" stroke-opacity="0.18"')
        s.T(bx + 30, gy + 27, "Approve", 11, 600, BG if (bk == "NEW-108" and k == 0) else INK, anchor="middle")
        if bk == "NEW-108" and k == 0: approve_at = (bx + 50, gy + 28)
        s.end()
        gy += 50
    gy += 10
s.T(AX + 16, PY + PH - 16, "+ 20 more, grouped by booking", 11.5, 500, MUT)
s.end()

# frozen interaction state: a cursor on Approve, the row under it hovered.
if approve_at:
    cx, cy = approve_at
    s.raw(f'<path id="cursor" d="M{cx} {cy} l0 17 l4.5 -4.3 l3.2 7 l2.8 -1.3 l-3.1 -6.8 l6 -0.3 Z" fill="{INK}" stroke="{CARD}" stroke-width="1.4" stroke-linejoin="round"/>')
s.end()

# =============================================================== under the hood
HX = FX + FW + 24; HW = W - M - HX
hx = HX + 24; hw = HW - 48
s.g("under-the-hood")
s.card(HX, TOP, HW, BOT - TOP)
s.T(hx, TOP + 36, "16 AGENTS, ONE DESK", 13, 600, AMB, ls=1.4)
s.T(HX + HW - 24, TOP + 36, "how a mail moves", 13, 400, MUT, anchor="end")

def step_label(y, text):
    s.T(hx, y, text, 10.5, 700, MUT, ls=1.2)

def arrow(y1, y2, x=None):
    x = x or HX + HW / 2
    s.line(x, y1, x, y2 - 5, INK, 0.35, 1.5)
    s.raw(f'<path d="M{x-4.5} {y2-6} L{x} {y2} L{x+4.5} {y2-6}" stroke="{INK}" stroke-opacity="0.35" stroke-width="1.5" fill="none"/>')

# IN: where work arrives. Brackets say what works today and what is next.
y = TOP + 68
step_label(y, "IN · WHERE WORK ARRIVES")
y += 12
TT = 150                                   # the TMS tile
tw = (hw - TT - 4 * 8) / 4
def bracket(x, w, yb, t):
    s.line(x, yb + 12, x, yb + 6, INK, 0.25, 1.2); s.line(x + w, yb + 12, x + w, yb + 6, INK, 0.25, 1.2)
    s.line(x, yb + 6, x + w, yb + 6, INK, 0.25, 1.2)
    cw = 46 if t == "TODAY" else 38
    s.R(x + w / 2 - cw / 2 - 4, yb - 2, cw + 8, 18, CARD)
    tag(x + w / 2 + cw / 2, yb - 1, t)
s.g("in-row")
bracket(hx, 4 * tw + 3 * 8, y, "NEXT")
bracket(hx + 4 * (tw + 8), TT, y, "TODAY")
y += 22
for i, name in enumerate(("Outlook", "Teams", "Slack", "WhatsApp")):
    x = hx + i * (tw + 8)
    s.R(x, y, tw, 36, BG, 8, f' stroke="{INK}" stroke-opacity="0.10"')
    mark(name, x + 10, y + 9, 18)
    s.T(x + 36, y + 23, name, 12, 500)
x = hx + 4 * (tw + 8)
s.R(x, y, TT, 36, BG, 8, f' stroke="{INK}" stroke-opacity="0.10"')
s.T(x + 12, y + 23, "Your TMS export / API", 11.5, 600)
s.end()
y += 36
arrow(y, y + 14); y += 18

# three front doors
doors = [("Inbox", "reads every mail, routes it", "1 agent", False),
         ("Assistant", "takes your questions", "1 agent", False),
         ("Risk layer", "sends decisions · slide 08", "4 agents", True)]
dw = (hw - 16) / 3
s.g("front-doors")
for i, (name, what, n, other) in enumerate(doors):
    x = hx + i * (dw + 8)
    if other:
        s.R(x, y, dw, 58, BLUE_BG, 10, f' stroke="{BLUE}" stroke-opacity="0.35" stroke-dasharray="4 3"')
    else:
        s.R(x, y, dw, 58, INK, 10)
    s.T(x + 12, y + 22, name, 14, 600, BLUE if other else BG)
    s.T(x + dw - 12, y + 22, n, 10.5, 500, BLUE if other else "#BDBDBD", anchor="end")
    s.T(x + 12, y + 44, what, 11.5, 400, BLUE if other else "#D6D6D6")
s.end()
y += 58
arrow(y, y + 14); y += 18

# four stations, in work order, and the Playbook rail under them
st = [("01", "Quotes", "Rate · RFQ"),
      ("02", "Bookings &amp; docs", "Booking · Docs"),
      ("03", "Shipments", "Milestones · Exception"),
      ("04", "Billing &amp; customs", "Invoice · Customs")]
sw4 = (hw - 24) / 4
s.g("stations")
for i, (num, name, who) in enumerate(st):
    x = hx + i * (sw4 + 8)
    s.R(x, y, sw4, 80, CARD, 10, f' stroke="{INK}" stroke-opacity="0.16"')
    s.T(x + 12, y + 22, num, 10.5, 700, AMB, ls=0.8)
    s.T(x + sw4 - 12, y + 22, "2 agents", 10.5, 500, MUT, anchor="end")
    s.T(x + 12, y + 46, name, 13.5, 600, ls=-0.2)
    s.T(x + 12, y + 66, who, 10.5, 400, MUT)
    s.line(x + sw4 / 2, y + 80, x + sw4 / 2, y + 92, AMB, 0.6, 1.5)
s.end()
y += 92
s.g("playbook-rail")
s.R(hx, y, hw, 36, AMB, 8, ' fill-opacity="0.10"')
s.T(hx + 12, y + 23, "Playbook", 13, 700, AMB)
s.T(hx + 84, y + 23, "checks every output against the customer's rules, sends back what breaks them", 11, 500, AMB)
s.end()
y += 36
arrow(y, y + 14); y += 18

# the gate
s.g("the-gate")
s.R(hx, y, hw, 40, CARD, 8, f' stroke="{INK}" stroke-opacity="0.5" stroke-width="1.5"')
s.T(hx + 14, y + 26, "You approve", 14, 700)
s.T(hx + 112, y + 26, "each draft and each change. Nothing is sent or written before that.", 11.5, 400, MUT)
s.end()
y += 40
arrow(y, y + 14); y += 18

# OUT: through the TMS link, into the TMS
s.g("out-row")
step_label(y + 10, "OUT · THROUGH THE TMS LINK")
y += 20
TT2 = 150
bracket(hx, TT2, y, "TODAY")
bracket(hx + TT2 + 8, hw - TT2 - 8, y, "NEXT")
y += 22
s.R(hx, y, TT2, 40, BG, 8, f' stroke="{INK}" stroke-opacity="0.10"')
s.T(hx + 12, y + 25, "Export or your URL", 11.5, 600)
ox = hx + TT2 + 8; ow = hw - TT2 - 8
s.R(ox, y, ow, 40, BG, 8, f' stroke="{INK}" stroke-opacity="0.10"')
marks = (("CargoWise", 26), ("SAP", 18), ("Oracle", 9.5), ("Descartes", 13))
tot = sum(TM[n]["w"] * h / TM[n]["h"] for n, h in marks)
gap = (ow - 28 - tot) / 3
lx = ox + 14
for name, h in marks:
    lx += wordmark(name, lx, y + 20 - h / 2, h) + gap
s.end()
s.T(hx, BOT - 36, "Native TMS connectors are next. None of these vendors is connected.", 11, 400, MUT)
s.T(hx, BOT - 20, "Planner is scripted. The TMS link is a demo connector.", 11, 400, MUT)
s.end()

s.T(M, 946, "Every system on one screen. Every step recorded. You approve each change.", 28, 600, ls=-0.6)
s.T(W - M, 944, "Built for the 40%.", 20, 600, AMB, anchor="end")
s.footer(7)
s.write("slide-07-the-how-1.svg")
