#!/usr/bin/env python3
"""Slide 07 - The How 1/2: the desk. Left, the dashboard's Today view, kept minimal:
an Ask box (src/ask.py is live, and every suggested question below is one it answers),
four stat cards and one row of what came in. Every figure is counted from one offline
run of the desk (src/workflow.run(use_llm=False)) on its synthetic inbox. Right, the
16 agents, step by step, with how many agents work each step.

Colours are the dashboard's own tokens only (static/index.html): blue, green, amber,
plus ink and greys. The risk layer is a very light grey row; slide 08 is its job.
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
pill(FX + FW - 14, TOP + 9, "Demo run · synthetic inbox", AMBR_BG, AMBR, size=11.5, h=22)
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
    if count: s.T(FX + SBW - 26, ny + 21, count, 12.5, 500, GREY, anchor="end")
    ny += 36
s.end()

MX = FX + SBW + 32; MW = FX + FW - 32 - MX
s.g("page-header")
s.T(MX, TOP + 84, "Today", 26, 600, ls=-0.6)
s.T(MX, TOP + 107, "The desk worked the morning inbox. Nothing is sent or written until you approve.", 13, 400, MUT)
s.R(MX + MW - 138, TOP + 64, 138, 34, CARD, 8, f' stroke="{INK}" stroke-opacity="0.16"')
s.T(MX + MW - 69, TOP + 86, "Work the inbox", 13, 600, anchor="middle")
s.end()

# ---- the Ask box: a question, to the agent who owns it
AY, AH = TOP + 134, 116
s.g("ask-box")
s.R(MX, AY + 3, MW, AH, INK, 20, ' fill-opacity="0.04"')          # soft shadow
s.R(MX, AY, MW, AH, CARD, 20, f' stroke="{INK}" stroke-opacity="0.12"')
s.T(MX + 24, AY + 38, "Where is MEDU-1774390?", 17, 400, "#8A8A8A")
s.R(MX + 24 + 214, AY + 22, 1.6, 22, INK)                              # cursor
by = AY + AH - 46
s.R(MX + 18, by, 32, 32, GREY_BG, 10)
s.raw(f'<path d="M{MX+39} {by+11} l-7.5 7.5 a3 3 0 0 0 4.2 4.2 l8 -8 a5 5 0 0 0 -7 -7 l-8 8 a7 7 0 0 0 9.9 9.9 l6 -6" '
      f'transform="translate(-2 -2) scale(0.78) translate({(MX+34)*0.282:.1f} {(by+16)*0.282:.1f})" stroke="#4A4A4A" stroke-width="2" fill="none" stroke-linecap="round"/>')
s.R(MX + 58, by, 134, 32, BLUE_BG, 10)
for i in range(8):                                                     # the agent mark: a ring of dots
    import math
    a = i * math.pi / 4
    s.raw(f'<circle cx="{MX + 76 + 6 * math.cos(a):.1f}" cy="{by + 16 + 6 * math.sin(a):.1f}" r="1.6" fill="{BLUE}" fill-opacity="{0.35 + 0.08 * i:.2f}"/>')
s.T(MX + 92, by + 21, "Ask SQRlane", 13, 600, BLUE)
s.raw(f'<circle cx="{MX + MW - 34}" cy="{by + 16}" r="18" fill="{GREY_BG}"/>')
s.raw(f'<path d="M{MX+MW-34} {by+24} v-15 M{MX+MW-40} {by+15} l6 -6 l6 6" stroke="#6B6B6B" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
s.end()

# suggested questions - each one answered by src/ask.py today
s.g("suggestions")
sy = AY + AH + 16
sx = MX
for q in ("What is waiting for my approval?", "Price 2 x 40HC Shanghai to Rotterdam", "Which invoices are disputed?"):
    w = round(len(q) * 6.4 + 26)
    s.R(sx, sy, w, 30, CARD, 15, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(sx + w / 2, sy + 20, q, 12, 500, "#4A4A4A", anchor="middle")
    sx += w + 8
s.end()

# ---- four stat cards: label, pill, one number
SCY, SCH, gap = sy + 52, 92, 12
scw = (MW - 3 * gap) / 4
STATS = [("Mails worked", "all routed", BLUE_BG, BLUE, "13"),
         ("Handled end to end", "no person", GREEN_BG, GREEN, "8"),
         ("Held for a person", "held", AMBR_BG, AMBR, "5"),
         ("Awaiting approval", "you decide", BLUE_BG, BLUE, "24")]
s.g("stat-cards")
for i, (lab, pl, pf, pi, val) in enumerate(STATS):
    x = MX + i * (scw + gap)
    s.card(x, SCY, scw, SCH, 12)
    s.T(x + 16, SCY + 27, lab, 12.5, 500, MUT)
    s.T(x + 16, SCY + 74, val, 38, 600, ls=-1.2)
    pill(x + scw - 14, SCY + 56, pl, pf, pi)
s.end()

# ---- one row: what came in, by job
RY = SCY + SCH + 12; RH = BOT - 22 - RY; RM = RY + RH / 2 - 60
JOBS = [("Quote", 1), ("Book", 4), ("Documents", 2), ("In transit", 3), ("Arrival", 2), ("Billing", 1)]
s.g("what-came-in")
s.card(MX, RY, MW, RH, 12)
s.T(MX + 18, RY + 28, "What came in", 14, 600)
s.T(MX + MW - 18, RY + 28, "13 mails", 12.5, 500, GREY, anchor="end")
jw = (MW - 36) / 6
for k, (job, n) in enumerate(JOBS):
    x = MX + 18 + k * jw
    s.T(x, RM + 62, job, 12, 500, MUT)
    s.T(x, RM + 94, str(n), 24, 600)
    s.R(x, RM + 108, jw - 24, 8, GREY_BG, 4)
    s.R(x, RM + 108, (jw - 24) * n / 4, 8, BLUE, 4)
s.end()
s.end()

# ================================================================ the agents, step by step
HX = FX + FW + 24; HW = W - M - HX
hx, hw = HX + 24, HW - 48
s.g("agents-step-by-step")
s.card(HX, TOP, HW, BOT - TOP)
s.T(hx, TOP + 38, "16 AGENTS, STEP BY STEP", 13, 600, AMB, ls=1.4)
s.T(HX + HW - 24, TOP + 38, "agents per step", 12.5, 500, GREY, anchor="end")

ROWS = [("", "Risk layer", [("Risk", 0), ("Routing", 0), ("Comms", 0), ("Planner", "scripted")], 4, "risk"),
        ("", "Front door", [("Inbox", 0), ("Assistant", 0)], 2, "desk"),
        ("01", "Quote", [("Rate", 0), ("RFQ", 0)], 2, "desk"),
        ("02", "Book", [("Booking", 0)], 1, "desk"),
        ("03", "Documents", [("Docs", 0)], 1, "desk"),
        ("04", "In transit", [("Milestones", 0), ("Exception", 0)], 2, "desk"),
        ("05", "Arrival", [("Customs", 0)], 1, "desk"),
        ("06", "Billing", [("Invoice", 0)], 1, "desk"),
        ("", "Every step", [("Playbook", 0)], 1, "check"),
        ("", "You approve", [], 0, "you"),
        ("", "Into the TMS", [("TMS link", "demo")], 1, "desk")]
RY0, RHt, RG = TOP + 58, 38, 4
DOT = {"risk": GREY, "desk": BLUE, "check": AMBR}
for k, (num, step, agents, n, kind) in enumerate(ROWS):
    y = RY0 + k * (RHt + RG)
    s.g("step-" + step.lower().replace(" ", "-"))
    if kind == "risk":
        s.R(hx, y, hw, RHt, GREY_BG, 8)
    elif kind == "check":
        s.R(hx, y, hw, RHt, AMBR_BG, 8)
    elif kind == "you":
        s.R(hx, y, hw, RHt, CARD, 8, f' stroke="{INK}" stroke-opacity="0.5" stroke-width="1.4"')
    else:
        s.R(hx, y, hw, RHt, CARD, 8, f' stroke="{INK}" stroke-opacity="0.10"')
    ink = GREY if kind == "risk" else INK
    if num: s.T(hx + 14, y + 24, num, 11, 700, AMB, ls=0.6)
    s.T(hx + 42, y + 24, step, 14, 600 if kind != "risk" else 500, ink)
    cx = hx + 170
    for a, tag in agents:
        label = a + (" · " + tag if tag else "")
        w = round(len(label) * 6.5 + 18)
        s.R(cx, y + 8, w, 22, GREY_BG if kind != "risk" else CARD, 6)
        s.T(cx + w / 2, y + 23, label, 11.5, 500, GREY if kind == "risk" else "#3A3A3A", anchor="middle")
        cx += w + 6
    if kind == "you":
        s.T(hx + 170, y + 24, "every draft, every change. Nothing leaves before that.", 12, 400, MUT)
    else:
        s.T(hx + hw - 14, y + 25, str(n), 17, 600, ink, anchor="end")
        for d in range(n):
            s.raw(f'<circle cx="{hx + hw - 40 - d * 13}" cy="{y + RHt / 2}" r="4.5" fill="{DOT[kind]}"/>')
    s.end()
ty = RY0 + len(ROWS) * (RHt + RG) + 6
s.rule(ty, 0.12, hx, hw)
s.T(hx, ty + 28, "14 live · Planner scripted · TMS link demo", 12, 400, GREY)
s.T(hx + hw - 14, ty + 29, "16 agents", 17, 600, anchor="end")
s.end()

s.T(M, 946, "Ask the desk anything. Every step recorded, and approved by you.", 28, 600, ls=-0.6)
s.footer(7)
s.write("slide-07-the-how-1.svg")
