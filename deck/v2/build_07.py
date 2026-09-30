#!/usr/bin/env python3
"""Slide 07 - The How 1/2: the desk. Left, the dashboard's overview, kept clean: four
stat cards and two small infographics, every figure counted from one offline run of
the desk (src/workflow.run(use_llm=False)) on its synthetic inbox. Right, how the work
is structured and who does it: the 16 agents, in the order a shipment lives.

The risk layer is only a band here; slide 08 is its whole job. Tags follow
src/roster.py: Planner scripted, TMS link demo. Nothing is sent or written.

Chart colours are the deck's validated pair (dataviz validator, light surface):
handled #3D72A8, held #96580A. The job bars are one series, so they stay neutral."""
from kit import *

BLUE, BLUE_BG = "#3D72A8", "#EAF1F8"
AMB_BG = "#F6EEE3"
HANDLED, HELD, BAR = "#3D72A8", AMB, "#3A3A3A"

s = Slide()
s.header("06 · THE HOW, 1 OF 2", "SQRlane does the desk work itself.",
         "Every mail read once. Sixteen agents do the work. Nothing leaves without you.")
TOP, BOT = 306, 890

def pill(x_right, y, text, fill, ink):
    w = round(len(text) * 6.2 + 18)
    s.R(x_right - w, y, w, 20, fill, 10)
    s.T(x_right - w / 2, y + 14, text, 10.5, 600, ink, anchor="middle")

# ================================================================ the dashboard
FX, FW = M, 940
s.g("dashboard")
s.R(FX, TOP, FW, BOT - TOP, CARD, 14, f' stroke="{INK}" stroke-opacity="0.14"')
s.g("window-bar")
s.R(FX, TOP, FW, 36, "#F4F4F4", 14); s.R(FX, TOP + 22, FW, 14, "#F4F4F4")
s.rule(TOP + 36, 0.09, FX, FW)
for i in range(3):
    s.raw(f'<circle cx="{FX + 20 + i * 16}" cy="{TOP + 18}" r="5" fill="#DEDEDE"/>')
pill(FX + FW - 14, TOP + 8, "Demo run · synthetic inbox", AMB_BG, AMB)
s.end()

SBW, SY0 = 164, TOP + 37
s.g("sidebar")
s.R(FX + 1, SY0, SBW, BOT - SY0 - 1, "#FBFBFB")
s.R(FX + SBW, SY0, 1, BOT - SY0 - 1, INK, extra=' fill-opacity="0.08"')
s.R(FX + 18, SY0 + 22, 22, 22, INK, 6)
s.raw(f'<path d="M{FX+23.5} {SY0+38}h11 M{FX+23.5} {SY0+33}h7.5 M{FX+23.5} {SY0+28}h4" stroke="{BG}" stroke-width="1.8" stroke-linecap="round" fill="none"/>')
s.T(FX + 50, SY0 + 39, "SQRlane", 15, 600)
ny = SY0 + 76
for name, count, on in (("Overview", None, True), ("Inbox", "13", False), ("Approvals", "24", False),
                        ("Shipments", "7", False), ("Agents", "16", False), ("TMS link", None, False)):
    if on: s.R(FX + 10, ny, SBW - 20, 30, TRACK, 7)
    s.T(FX + 22, ny + 20, name, 13, 600 if on else 500, INK if on else "#4A4A4A")
    if count: s.T(FX + SBW - 22, ny + 20, count, 12, 500, MUT, anchor="end")
    ny += 34
s.end()

MX = FX + SBW + 28; MW = FX + FW - 28 - MX
s.T(MX, TOP + 80, "Overview", 22, 600, ls=-0.4)
s.T(MX, TOP + 101, "The desk worked the morning inbox.", 13, 400, MUT)

# ---- four stat cards: label and pill, a big number, one line under it
SCY, SCH, gap = TOP + 122, 104, 12
scw = (MW - 3 * gap) / 4
STATS = [("Mails worked", "13 routed", BLUE_BG, BLUE, "13", "", "every mail to its owner"),
         ("Handled end to end", "no person", BLUE_BG, BLUE, "8", "of 13", "worked through to approval"),
         ("Held for a person", "not guessed", AMB_BG, AMB, "5", "", "a person decides"),
         ("Awaiting your approval", "gated", TRACK, "#4A4A4A", "24", "", "10 drafts · 14 TMS changes")]
s.g("stat-cards")
for i, (lab, pl, pf, pi, val, suf, cap) in enumerate(STATS):
    x = MX + i * (scw + gap)
    s.card(x, SCY, scw, SCH, 12)
    s.T(x + 16, SCY + 28, lab, 12.5, 500, MUT)
    pill(x + scw - 12, SCY + 56, pl, pf, pi)
    s.T(x + 16, SCY + 72, val, 36, 600, ls=-1.2)
    if suf: s.T(x + 16 + len(val) * 22 + 8, SCY + 72, suf, 18, 500, MUT)
    s.T(x + 16, SCY + 92, cap, 11, 400, MUT)
s.end()

# ---- infographic A: how the 13 mails ended, one square per mail
CY = SCY + SCH + 14; CH = BOT - 20 - CY
AWd = 352
s.g("chart-how-mails-ended")
s.card(MX, CY, AWd, CH, 12)
s.T(MX + 20, CY + 32, "How the 13 mails ended", 15, 600)
s.T(MX + 20, CY + 52, "One square per mail", 12, 400, MUT)
done = ["101", "103", "106", "107", "108", "110", "111", "113"]
held = ["102", "104", "105", "109", "112"]
SQ, SG = 38, 6
for k, (num, col) in enumerate([(n, HANDLED) for n in done] + [(n, HELD) for n in held]):
    r, c = divmod(k, 7)
    x = MX + 20 + c * (SQ + SG); y = CY + 72 + r * (SQ + SG)
    s.R(x, y, SQ, SQ, col, 6)
    s.T(x + SQ / 2, y + SQ / 2 + 4, num, 10.5, 600, CARD, anchor="middle")
ly = CY + 178
for col, name, n, note in ((HANDLED, "End to end", "8", "worked through to your approval"),
                           (HELD, "Held for a person", "5", "a detail no agent could verify")):
    s.raw(f'<circle cx="{MX + 26}" cy="{ly - 5}" r="5" fill="{col}"/>')
    s.T(MX + 40, ly, name, 13, 600)
    s.T(MX + AWd - 20, ly, n, 13, 600, anchor="end")
    s.T(MX + 40, ly + 18, note, 11.5, 400, MUT)
    ly += 46
s.rule(CY + CH - 50, 0.08, MX + 20, AWd - 40)
s.T(MX + 20, CY + CH - 28, "Held: 3 bookings missing a detail, 1 rolled box,", 11.5, 400, MUT)
s.T(MX + 20, CY + CH - 12, "1 transit leaving the EU.", 11.5, 400, MUT)
s.end()

# ---- infographic B: what came in, by job (the six stages on the right)
BX = MX + AWd + gap; BWd = MX + MW - BX
JOBS = [("Quote", 1), ("Book", 4), ("Documents", 2), ("In transit", 3), ("Arrival", 2), ("Billing", 1)]
s.g("chart-what-came-in")
s.card(BX, CY, BWd, CH, 12)
s.T(BX + 20, CY + 32, "What came in", 15, 600)
s.T(BX + 20, CY + 52, "13 mails, by the job they start", 12, 400, MUT)
TX = BX + 108; TW = BWd - 108 - 44
row = (CH - 92) / len(JOBS)
for k, (job, n) in enumerate(JOBS):
    y = CY + 80 + k * row
    s.T(BX + 20, y + 13, job, 12.5, 500, "#3A3A3A")
    s.R(TX, y + 2, TW, 14, TRACK, 4)
    s.R(TX, y + 2, TW * n / 4, 14, BAR, 4)
    s.T(BX + BWd - 20, y + 13, str(n), 12.5, 600, anchor="end")
s.end()
s.end()

# ================================================================ how the work is structured
HX = FX + FW + 24; HW = W - M - HX
hx, hw = HX + 24, HW - 48
s.g("how-the-work-is-structured")
s.card(HX, TOP, HW, BOT - TOP)
s.T(hx, TOP + 36, "HOW THE WORK IS STRUCTURED", 13, 600, AMB, ls=1.4)
s.T(HX + HW - 24, TOP + 36, "14 live · Planner scripted · TMS link demo", 12.5, 500, MUT, anchor="end")

def arrow(y1, y2, x=None):
    x = x or hx + hw / 2
    s.line(x, y1, x, y2 - 5, INK, 0.35, 1.5)
    s.raw(f'<path d="M{x-4.5} {y2-6} L{x} {y2} L{x+4.5} {y2-6}" stroke="{INK}" stroke-opacity="0.35" stroke-width="1.5" fill="none"/>')

def count_chip(x, y, text, fill, ink):
    w = round(len(text) * 6 + 14)
    s.R(x, y, w, 18, fill, 9)
    s.T(x + w / 2, y + 13, text, 10, 600, ink, anchor="middle")
    return w

y = TOP + 56
# the risk layer: one band, detailed on slide 08
s.g("risk-layer")
s.R(hx, y, hw, 40, BLUE_BG, 10, f' stroke="{BLUE}" stroke-opacity="0.35" stroke-dasharray="4 3"')
s.T(hx + 14, y + 25, "Risk layer", 13.5, 600, BLUE)
cw = count_chip(hx + 96, y + 11, "4 agents", CARD, BLUE)
s.T(hx + 96 + cw + 12, y + 25, "watches 60 sources, decides reroute or hold, hands it to the desk", 11.5, 400, BLUE)
s.T(hx + hw - 14, y + 25, "slide 08", 11.5, 600, BLUE, anchor="end")
s.end()
y += 40; arrow(y, y + 12); y += 14

# the two front doors
s.g("front-doors")
IW = hw - 196
s.R(hx, y, IW, 40, INK, 10)
s.T(hx + 14, y + 25, "Inbox", 13.5, 600, BG)
cw = count_chip(hx + 62, y + 11, "1 agent", "#2A2A2A", "#D6D6D6")
s.T(hx + 62 + cw + 12, y + 25, "reads every mail, links it to the booking, hands it on", 11.5, 400, "#D6D6D6")
s.R(hx + IW + 8, y, 188, 40, INK, 10)
s.T(hx + IW + 22, y + 25, "Assistant", 13.5, 600, BG)
s.T(hx + IW + 96, y + 25, "your questions", 11.5, 400, "#D6D6D6")
s.end()
y += 40; arrow(y, y + 12); y += 14

# the desk: six stages, in the order a shipment lives
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
for k, (num, name, agents, job) in enumerate(STAGES):
    r, c = divmod(k, 3)
    x = hx + 14 + c * (cw3 + 8); yy = y + 36 + r * (chh + 8)
    s.g("stage-" + name.lower().replace(" ", "-"))
    s.R(x, yy, cw3, chh, CARD, 10, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(x + 14, yy + 26, num, 11, 700, AMB, ls=0.6)
    s.T(x + 38, yy + 26, name, 14.5, 600, ls=-0.2)
    s.T(x + 14, yy + 47, job, 11.5, 400, MUT)
    ax = x + 14
    for a in agents:
        w = round(len(a) * 6.4 + 16)
        s.R(ax, yy + 60, w, 20, TRACK, 5)
        s.T(ax + w / 2, yy + 74, a, 11, 500, "#3A3A3A", anchor="middle")
        ax += w + 5
    s.end()
s.end()
y += DH
for c in range(3):                       # every stage hands its output to the Playbook
    x = hx + 14 + c * (cw3 + 8) + cw3 / 2
    s.line(x, y, x, y + 8, AMB, 0.6, 1.5)
y += 8
s.g("playbook")
s.R(hx, y, hw, 36, AMB_BG, 10)
s.T(hx + 14, y + 23, "Playbook", 13.5, 600, AMB)
cw = count_chip(hx + 86, y + 9, "1 agent", CARD, AMB)
s.T(hx + 86 + cw + 12, y + 23, "checks every output against the customer's rules, sends back what breaks them", 11.5, 400, AMB)
s.end()
y += 36; arrow(y, y + 12); y += 14

# the gate, then the record
s.g("gate-and-record")
GW = (hw - 28) / 2
s.R(hx, y, GW, 40, CARD, 10, f' stroke="{INK}" stroke-opacity="0.55" stroke-width="1.5"')
s.T(hx + 14, y + 25, "You approve", 13.5, 700)
s.T(hx + 108, y + 25, "every draft, every change", 11.5, 400, MUT)
ax1 = hx + GW + 4
s.line(ax1, y + 20, ax1 + 15, y + 20, INK, 0.35, 1.5)
s.raw(f'<path d="M{ax1+14} {y+15.5} L{ax1+20} {y+20} L{ax1+14} {y+24.5}" stroke="{INK}" stroke-opacity="0.35" stroke-width="1.5" fill="none"/>')
tx = hx + GW + 28
s.R(tx, y, GW, 40, INK, 10)
s.T(tx + 14, y + 25, "TMS link", 13.5, 600, BG)
s.T(tx + 86, y + 25, "writes it onto the booking", 11.5, 400, "#D6D6D6")
count_chip(tx + GW - 60, y + 11, "demo", "#2A2A2A", "#D6D6D6")
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
    w = round(len(name) * 6.3 + 18)
    fill, ink = {"amb": (AMB, CARD), "ink": (INK, CARD)}.get(kind, (TRACK, "#3A3A3A"))
    s.R(cx, y, w, 22, fill, 5)
    s.T(cx + w / 2, y + 15, name, 11, 600 if kind else 500, ink, anchor="middle")
    cx += w
    if k < len(steps) - 1:
        s.T(cx + 5, y + 15, "›", 12, 500, MUT); cx += 16
s.end()
s.end()

s.T(M, 946, "Every step recorded, checked against the customer's rules, and approved by you.", 28, 600, ls=-0.6)
s.footer(7)
s.write("slide-07-the-how-1.svg")
