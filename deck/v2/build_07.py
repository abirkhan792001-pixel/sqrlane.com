#!/usr/bin/env python3
"""Slide 07 - The How 1/2. Answers slide 03's first problem: the same carrier mail,
read once, written into every system by the agent that owns it, checked, and
queued for a person. Roster and tags follow src/roster.py (14 live, 1 scripted,
1 demo). Nothing here is sent or written: the TMS link is a demo connector."""
from kit import *
s = Slide()
s.header("06 · THE HOW, 1 OF 2", "SQRlane does the desk work itself.",
         "The mail is read once. Agents fill every system, check each other, and wait for you.")
GREEN = "#0F7B3F"

# ---- one mail, read once (the mirror of slide 03)
AY, AH, AW = 306, 400, 1110
s.g("one-mail-read-once")
s.card(M, AY, AW, AH)
x0 = M + 28
s.T(x0, AY + 38, "ONE MAIL, READ ONCE", 13, 600, AMB, ls=1.4)
s.T(M + AW - 28, AY + 38, "same booking as slide 03", 13, 400, MUT, anchor="end")
SX, SY, SW, SH = x0, AY + 124, 212, 170
s.g("source-mail")
s.R(SX, SY, SW, SH, BG, 12, f' stroke="{INK}" stroke-opacity="0.18"')
s.T(SX + 18, SY + 30, "CARRIER MAIL", 12, 600, MUT, ls=1.4)
s.T(SX + 18, SY + 58, "Booking confirmed", 16, 600)
s.T(SX + 18, SY + 92, "Booking", 12.5, 400, MUT); s.T(SX + SW - 18, SY + 92, "HLCU-2261188", 13, 600, anchor="end")
s.T(SX + 18, SY + 118, "ETA", 12.5, 400, MUT); s.T(SX + SW - 18, SY + 118, "10 Oct", 13, 600, anchor="end")
s.rule(SY + 134, 0.08, SX + 18, SW - 36)
s.T(SX + 18, SY + 156, "read once", 12.5, 600, AMB)
s.end()
# the agents node
NX, NY = SX + SW + 36, SY + SH / 2
s.line(SX + SW, NY, NX, NY, INK, 0.4, 1.5)
s.R(NX, NY - 22, 44, 44, INK, 11)
s.raw(f'<path d="M{NX+11} {NY+9}h22 M{NX+11} {NY}h14 M{NX+11} {NY-9}h8" stroke="{BG}" stroke-width="2.8" stroke-linecap="round" fill="none"/>')
s.T(NX + 22, NY + 44, "AGENTS", 11, 600, MUT, anchor="middle", ls=1.2)
# six systems, written by their owner, all consistent, all waiting for approval
rows = [("TMS", "Booking agent", "fields filled from the mail"),
        ("Carrier portal", "Booking agent", "amendment drafted"),
        ("Customer mail", "Milestones agent", "update drafted"),
        ("Customs", "Customs agent", "entry prepared, not filed"),
        ("Invoice", "Invoice agent", "checked against the agreed rate"),
        ("Tracking sheet", "Milestones agent", "ETA set to 10 Oct")]
RX, RW, RH, RS = NX + 104, M + AW - 28 - (NX + 104), 36, 44
R0 = AY + 70
TRUNK = NX + 44 + 30
s.line(NX + 44, NY, TRUNK, NY, INK, 0.4, 1.5)
s.line(TRUNK, R0 + RH / 2, TRUNK, R0 + 5 * RS + RH / 2, INK, 0.4, 1.5)
s.g("written-once")
for i, (sysn, agent, what) in enumerate(rows):
    ry = R0 + i * RS; cy = ry + RH / 2
    s.line(TRUNK, cy, RX, cy, INK, 0.4, 1.5)
    s.g("row-" + sysn.lower().replace(" ", "-"))
    s.R(RX, ry, RW, RH, BG, 8, f' stroke="{INK}" stroke-opacity="0.12"')
    s.T(RX + 14, cy + 5, sysn, 14, 600)
    s.T(RX + 150, cy + 5, agent, 13, 400, MUT)
    s.raw(f'<path d="M{RX + 290} {cy} l4 4 l8 -9" stroke="{GREEN}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    s.T(RX + 310, cy + 5, what, 13.5, 500)
    s.R(RX + RW - 126, ry + 8, 114, 20, AMB, 4, ' fill-opacity="0.12"')
    s.T(RX + RW - 69, ry + 22, "waits for you", 11.5, 600, AMB, anchor="middle")
    s.end()
s.end()
s.T(RX, AY + AH - 22, "Same booking. Read once, no re-typing, no typo.", 14, 500, MUT)
s.end()

# ---- sixteen agents, one desk
BX, BW = M + AW + 24, W - M - (M + AW + 24)
s.g("sixteen-agents")
s.card(BX, AY, BW, AH)
bx = BX + 28
s.T(bx, AY + 38, "16 AGENTS, ONE DESK", 13, 600, AMB, ls=1.4)
s.T(BX + BW - 28, AY + 38, "14 live · 1 scripted · 1 demo", 13, 500, MUT, anchor="end")
groups = [("Inbox &amp; rules", ["Inbox", "Playbook"]),
          ("Quotes", ["Rate", "RFQ"]),
          ("Bookings", ["Booking", "Docs"]),
          ("Shipments", ["Milestones", "Exception", "Assistant"]),
          ("Billing &amp; customs", ["Invoice", "Customs"]),
          ("Risk", ["Risk", "Routing", "Comms", ("Planner", "SCRIPTED")]),
          ("Record", [("TMS link", "DEMO")])]
for g, (gname, agents) in enumerate(groups):
    gy = AY + 84 + g * 40
    s.T(bx, gy, gname, 13, 500, MUT)
    px = bx + 146
    for a in agents:
        name, tagt = (a if isinstance(a, tuple) else (a, None))
        w = round(len(name) * 7.8 + 24 + (len(tagt) * 7 + 12 if tagt else 0))
        s.R(px, gy - 19, w, 28, TRACK, 6)
        s.T(px + 12, gy, name, 13.5, 500)
        if tagt:
            s.T(px + 12 + len(name) * 7.8 + 8, gy - 1, tagt, 10.5, 700, MUT, ls=0.8)
        px += w + 8
s.T(bx, AY + AH - 44, "Live: reasons on every run. Scripted: replays set data.", 12.5, 400, MUT)
s.T(bx, AY + AH - 24, "Demo: the TMS link, with no TMS on the far end yet.", 12.5, 400, MUT)
s.end()

# ---- three things the desk does that typing never did
TY, TH = AY + AH + 24, 136
tiles = [("Checked before it goes out", ["The Playbook agent checks every output against", "the customer’s own rules, and sends back what breaks them."]),
         ("Correct it once. The desk learns.", ["One correction becomes a rule, replays the inbox", "and fixes every mail like it. Nothing earlier is undone."]),
         ("Nothing leaves without you", ["Every draft and every TMS change waits for your", "approval. Nothing is sent or written on its own."])]
TW = (W - 2 * M - 2 * 24) / 3
for k, (title, lines) in enumerate(tiles):
    tx = round(M + k * (TW + 24), 1)
    s.g("tile-" + str(k + 1))
    s.card(tx, TY, round(TW, 1), TH)
    s.T(tx + 28, TY + 44, title, 21, 600, ls=-0.3)
    for j, ln in enumerate(lines):
        s.T(tx + 28, TY + 78 + j * 22, ln, 14.5, 400, MUT)
    s.end()

s.T(M, 946, "Every system on one screen. Every step recorded. You approve each change.", 28, 600, ls=-0.6)
s.T(W - M, 944, "Built for the 40%.", 20, 600, AMB, anchor="end")
s.footer(7)
s.write("slide-07-the-how-1.svg")
