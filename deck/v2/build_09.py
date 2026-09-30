#!/usr/bin/env python3
"""Slide 09 - Integrations: how SQRlane plugs into the tools a desk already runs. The
same frame as slides 07 and 08. Left, the product's TMS link view, reading a bookings
export: what it read, how every column was mapped, what it could not cover (said, not
guessed), and one change queued back onto a booking. Right, every place SQRlane
connects: the TMS, mail and chat, the 60 sources, and an AI assistant over MCP, each
with what works today and what is coming.

Every figure on the left is from connect.read_export() on data/sample_tms_export.csv
(renamed bookings.csv on screen) and orchestrator.run_cycle(live=False, use_llm=False,
scenario="hamburg") with that export as the book: 10 rows, 16 columns mapped, 0
unmapped, 7 covered, 3 not covered with the connector's own reasons, 8 changes queued
on 2 bookings. JOB-24126's reroute is the Routing agent's write-back; its ETA is shown
as "+2 days", because the run's dates age forward. The vendor marks are official
files; none of those systems is connected, and the slide says so beside them."""
from kit import *
import json, math, pathlib, re

BLUE, BLUE_BG = "#006BFF", "#E8F1FF"
GREEN, GREEN_BG = "#0F7B3F", "#E7F5EC"
AMBR, AMBR_BG = "#96580A", "#FDF3E3"
GREY, GREY_BG = "#9A9A9A", "#F3F3F3"
RED = "#EA001D"

s = Slide()
s.header("07 · INTEGRATIONS", "Works inside the tools you already run.",
         "Your TMS stays the system of record. SQRlane reads from it, and writes back only what you approve.")
TOP, BOT = 306, 890

HERE = pathlib.Path(__file__).parent
CH = json.loads((HERE / "channel_marks.json").read_text())   # Iconify, CC0/MIT
TM = json.loads((HERE / "tms_marks.json").read_text())       # official marks, see HANDOFF

def pill(x, y, text, fill, ink, anchor="end", size=10.5, h=20):
    w = round(len(text) * size * 0.6 + 18)
    x0 = x - w if anchor == "end" else x
    s.R(x0, y, w, h, fill, h / 2)
    s.T(x0 + w / 2, y + h / 2 + size * 0.36, text, size, 600, ink, anchor="middle")
    return w

def mark(name, x, y, size, fill=None):
    """An official mark, byte-for-byte, scaled into a size x size box. Never redrawn."""
    m = CH[name]; sc = size / max(m["w"], m["h"])
    body = re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + "o9-" + g.group(2), m["body"])
    dx = x + (size - m["w"] * sc) / 2; dy = y + (size - m["h"] * sc) / 2
    col = f' color="{fill}"' if fill else ""
    s.raw(f'<g id="mark-{name.lower()}"{col} transform="translate({dx:.1f} {dy:.1f}) scale({sc:.4f})">{body}</g>')

def tms_mark(name, x, cy, h):
    """A TMS vendor's mark at height h, left-aligned at x. Returns its width."""
    m = TM[name]; sc = h / m["h"]; w = m["w"] * sc
    if m["kind"] == "png":
        s.raw(f'<image id="mark-{name.lower()}" x="{x:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h:.1f}" href="{m["href"]}"/>')
    else:
        body = re.sub(r'(id="|url\(#|href="#)([^")]+)', lambda g: g.group(1) + "t9-" + g.group(2), m["body"])
        s.raw(f'<g id="mark-{name.lower()}" transform="translate({x:.1f} {cy - h / 2:.1f}) scale({sc:.4f})">{body}</g>')
    return w

def agent_mark(cx, cy, r=6, col=BLUE):
    for i in range(8):                                   # the agent: a ring of dots
        a = i * math.pi / 4
        s.raw(f'<circle cx="{cx + r * math.cos(a):.1f}" cy="{cy + r * math.sin(a):.1f}" r="{r * 0.27:.1f}" fill="{col}" fill-opacity="{0.35 + 0.08 * i:.2f}"/>')

def soft_card(x, y, w, h, r=14, fill=CARD, op=0.12):
    s.R(x, y + 3, w, h, INK, r, ' fill-opacity="0.04"')
    s.R(x, y, w, h, fill, r, f' stroke="{INK}" stroke-opacity="{op}"')

def h_arrow(x, y, op=0.3):
    s.line(x, y, x + 12, y, INK, op, 1.5)
    s.raw(f'<path d="M{x+11} {y-4} L{x+16} {y} L{x+11} {y+4}" stroke="{INK}" stroke-opacity="{op}" stroke-width="1.5" fill="none"/>')

# ================================================================ the dashboard: TMS link
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
for name, count, on in (("Today", None, False), ("Risk", "1", False), ("Approvals", "8", False),
                        ("Shipments", "7", False), ("Agents", "16", False), ("TMS link", None, True)):
    if on: s.R(FX + 12, ny, SBW - 24, 32, GREY_BG, 8)
    s.T(FX + 26, ny + 21, name, 13.5, 600 if on else 500, INK if on else "#4A4A4A")
    if count:
        cw = len(count) * 7 + 14
        s.R(FX + SBW - 22 - cw, ny + 7, cw, 18, BLUE_BG if name == "Approvals" else GREY_BG, 9)
        s.T(FX + SBW - 22 - cw / 2, ny + 20, count, 11, 600, BLUE if name == "Approvals" else "#6B6B6B", anchor="middle")
    ny += 36
s.end()

MX = FX + SBW + 32; MW = FX + FW - 32 - MX

s.g("page-header")
s.T(MX, TOP + 90, "TMS link", 26, 600, ls=-0.6)
s.end()

# ---- two pop-ups: an export lands, the TMS Link agent maps it
PT, PH_ = TOP + 54, 56
P2W = 290; P2X = MX + MW - P2W
P1W = 280; P1X = P2X - 26 - P1W
s.g("popup-file")
soft_card(P1X, PT, P1W, PH_, 14)
s.R(P1X + 10, PT + 9, 38, 38, GREEN_BG, 10)
fx0, fy0 = P1X + 20, PT + 16                              # a plain file pictogram
s.raw(f'<path d="M{fx0} {fy0} h12 l6 6 v18 h-18 z M{fx0+12} {fy0} v6 h6" stroke="{GREEN}" stroke-width="1.5" fill="{CARD}" stroke-linejoin="round"/>')
s.T(fx0 + 9, fy0 + 20, "CSV", 6.5, 700, GREEN, anchor="middle")
s.T(P1X + 60, PT + 23, "Your TMS · bookings export", 11, 500, GREY)
s.T(P1X + 60, PT + 42, "bookings.csv · 10 rows", 12.5, 600)
s.end()
h_arrow(P1X + P1W + 5, PT + PH_ / 2)
s.g("popup-agent")
soft_card(P2X, PT, P2W, PH_, 14)
s.R(P2X, PT, P2W, PH_, "none", 14, f' stroke="{BLUE}" stroke-width="0.8" stroke-opacity="0.45"')
agent_mark(P2X + 22, PT + 19, 6)
s.T(P2X + 38, PT + 23, "TMS Link agent", 12.5, 600, BLUE)
s.T(P2X + P2W - 14, PT + 23, "working…", 11, 500, GREY, anchor="end")
s.T(P2X + 14, PT + 44, "Mapping 16 columns onto the booking.", 12, 400, INK)
s.end()

# ---- the read in one line, each figure with its tag
OY, OH = TOP + 124, 114
STEPS = [("10", "rows read", "from your export", GREY_BG, "#4A4A4A"),
         ("16", "columns mapped", "0 unmapped", GREEN_BG, GREEN),
         ("7", "bookings covered", "on modelled lanes", BLUE_BG, BLUE),
         ("3", "not covered", "said, not guessed", AMBR_BG, AMBR),
         ("0", "written", "until you approve", GREEN_BG, GREEN)]
s.g("this-read")
s.card(MX, OY, MW, OH, 12)
s.T(MX + 18, OY + 25, "This read", 13, 600)
s.T(MX + MW - 18, OY + 25, "synthetic export · Hamburg strike scenario", 12, 400, GREY, anchor="end")
sw_ = (MW - 36) / 5
for k, (n, lab, tag, tf, ti) in enumerate(STEPS):
    x = MX + 18 + k * sw_
    s.T(x, OY + 60, n, 30, 600, ls=-1)
    s.T(x, OY + 79, lab, 12, 500, "#4A4A4A")
    pill(x, OY + 87, tag, tf, ti, anchor="start", size=10, h=18)
    if k < 4:
        s.T(x + sw_ - 14, OY + 60, "›", 18, 400, "#C8C8C8")
s.end()

# ---- the mapping, and what it could not cover
CY0 = OY + OH + 14; CHh = BOT - 20 - CY0
s.g("mapping-and-writeback")
s.R(MX, CY0, MW, CHh, "#F6F8FB", 16, f' stroke="{INK}" stroke-opacity="0.10"')
cy = CY0 + 12
BWb = MW - 32
LW = 380; RX = MX + 16 + LW + 10; RW = BWb - LW - 10

# left: mapped, not guessed
soft_card(MX + 16, cy, LW, 178, 14, op=0.10)
s.T(MX + 32, cy + 25, "Mapped, not guessed", 12.5, 600)
s.T(MX + 16 + LW - 14, cy + 25, "6 of 16", 11, 500, GREY, anchor="end")
s.T(MX + 32, cy + 48, "YOUR COLUMN", 9.5, 700, GREY, ls=1)
s.T(MX + 158, cy + 48, "SQRLANE READS IT AS", 9.5, 700, GREY, ls=1)
my = cy + 56
for col, field in (("Shipment No", "the booking"), ("POD", "discharge port"), ("ETA", "arrival, delay measured from it"),
                   ("RDD", "customer's date, slack to it"), ("Reefer", "cold chain"), ("Late Penalty per Day", "what a day late costs")):
    s.rule(my, 0.07, MX + 32, LW - 32)
    s.T(MX + 32, my + 16, col, 11.5, 600, "#3A3A3A")
    s.T(MX + 158, my + 16, field, 11.5, 400, MUT)
    my += 19

# right: not covered, out loud
soft_card(RX, cy, RW, 178, 14, op=0.10)
s.T(RX + 16, cy + 25, "Not covered, said out loud", 12.5, 600)
pill(RX + RW - 14, cy + 12, "3 rows", AMBR_BG, AMBR)
ny2 = cy + 50
for ref, why in (("JOB-24166", "Los Angeles: not a modelled port"),
                 ("JOB-24171", "Gdansk: not a modelled port"),
                 ("JOB-24175", "no readable ETA to measure from")):
    s.R(RX + 16, ny2, RW - 32, 36, BG, 8, f' stroke="{INK}" stroke-opacity="0.07"')
    s.T(RX + 28, ny2 + 23, ref, 11.5, 600)
    s.T(RX + 110, ny2 + 23, why, 11.5, 400, MUT)
    ny2 += 42
cy += 186

# the write-back: one change, queued onto the booking it came from
WH = CY0 + CHh - 12 - cy
soft_card(MX + 16, cy, BWb, WH, 14, op=0.10)
agent_mark(MX + 36, cy + 20)
s.T(MX + 52, cy + 25, "Routing agent", 12.5, 600, BLUE)
s.T(MX + 150, cy + 25, "JOB-24126 · Bicycle frames, Kaohsiung → Berlin", 12, 400, GREY)
pill(MX + 16 + BWb - 14, cy + 12, "reroute", BLUE_BG, BLUE)
fx = MX + 32
for off, lab, old, new in ((0, "Port of discharge", "HAM", "RTM"), (172, "Routing code", "R-HAM-STD", "R-RTM-ALT"), (390, "ETA", "booked", "+2 days")):
    fx = MX + 32 + off
    s.T(fx, cy + 50, lab.upper(), 9.5, 700, GREY, ls=1)
    s.T(fx, cy + 70, old, 12.5, 400, GREY)
    ow = sum(6.6 if c.islower() else 8.2 for c in old)
    s.line(fx, cy + 66, fx + ow, cy + 66, GREY, 0.8, 1)
    s.T(fx + ow + 10, cy + 70, "→", 12.5, 400, GREY)
    s.T(fx + ow + 30, cy + 70, new, 12.5, 600, INK)
by = cy + WH - 38
s.R(MX + 16 + BWb - 92, by, 78, 26, INK, 8)
s.T(MX + 16 + BWb - 53, by + 18, "Approve", 12, 600, CARD, anchor="middle")
s.T(MX + 16 + BWb - 104, by + 17.5, "Queued, not written", 11, 600, AMBR, anchor="end")
s.end()
s.end()

# ================================================================ where SQRlane connects
HX = FX + FW + 24; HW = W - M - HX
hx, hw = HX + 24, HW - 48
s.g("where-sqrlane-connects")
s.card(HX, TOP, HW, BOT - TOP)
s.T(hx, TOP + 36, "WHERE SQRLANE CONNECTS", 13, 600, AMB, ls=1.4)
s.T(HX + HW - 24, TOP + 36, "reads in · writes back after you approve", 12, 500, GREY, anchor="end")

def status(x, y, text, live):
    """A status line: green dot for what works today, grey dashed for what comes next."""
    if live:
        s.raw(f'<circle cx="{x + 4}" cy="{y - 4}" r="4" fill="{GREEN}"/>')
        s.T(x + 14, y, text, 11, 600, GREEN)
    else:
        s.raw(f'<circle cx="{x + 4}" cy="{y - 4}" r="3.5" fill="none" stroke="#B4B4B4" stroke-width="1.2" stroke-dasharray="2 1.5"/>')
        s.T(x + 14, y, text, 11, 600, GREY)

def block(y, h, title, direction, grp):
    s.g(grp)
    s.R(hx, y, hw, h, CARD, 12, f' stroke="{INK}" stroke-opacity="0.16"')
    s.T(hx + 16, y + 26, title, 13.5, 600)
    pill(hx + hw - 14, y + 11, direction, BLUE_BG, BLUE)

y = TOP + 56
# 1. the TMS: the system of record, both directions
block(y, 162, "Your TMS", "reads in · writes back", "tms")
mx = hx + 16
for name, hgt in (("CargoWise", 20), ("SAP", 20), ("Oracle", 11), ("Descartes", 14)):
    s.R(mx, y + 42, 140, 36, BG, 8, f' stroke="{INK}" stroke-opacity="0.07"')
    w = TM[name]["w"] * hgt / TM[name]["h"]
    tms_mark(name, mx + (140 - w) / 2, y + 60, hgt)
    mx += 150
s.T(hx + 16, y + 102, "In: a bookings export (CSV or JSON), or a live HTTPS endpoint, mapped by column name.", 11.5, 400, MUT)
s.T(hx + 16, y + 120, "Out: each approved change, one at a time, to a write-back URL you name.", 11.5, 400, MUT)
status(hx + 16, y + 146, "Works today", True)
status(hx + 124, y + 146, "Native connectors, next", False)
s.end()
y += 172

# 2. mail and chat: where the work arrives
block(y, 120, "Mail and chat", "reads in", "mail-and-chat")
mx = hx + 16
for name in ("Outlook", "Gmail", "Teams", "Slack", "WhatsApp", "WeChat"):
    s.R(mx, y + 40, 36, 36, BG, 8, f' stroke="{INK}" stroke-opacity="0.07"')
    mark(name, mx + 8, y + 48, 20)
    mx += 44
s.T(mx + 8, y + 56, "The desk works every mail: routed,", 11.5, 400, MUT)
s.T(mx + 8, y + 72, "checked against the playbook, drafted.", 11.5, 400, MUT)
status(hx + 16, y + 104, "Works today: drop a mail file into Ask", True)
status(hx + 290, y + 104, "Mailbox and chat links, next", False)
s.end()
y += 130

# 3. the sources: the world, read live
block(y, 78, "60 public sources", "reads in", "sources")
s.T(hx + 16, y + 48, "News, rivers, weather and sea, hazards, government filings, rates.", 11.5, 400, MUT)
s.T(hx + 16, y + 65, "Free and keyless, so there is no account to set up.", 11.5, 400, MUT)
status(hx + hw - 104, y + 60, "Live today", True)
s.end()
y += 88

# 4. an AI assistant over MCP
block(y, 78, "Your AI assistant", "asks the desk", "assistant")
s.R(hx + 16, y + 36, 32, 32, BG, 8, f' stroke="{INK}" stroke-opacity="0.07"')
mark("Claude", hx + 22, y + 42, 20)
s.R(hx + 54, y + 36, 32, 32, BG, 8, f' stroke="{INK}" stroke-opacity="0.07"')
mark("MCP", hx + 61, y + 43, 18, INK)
s.T(hx + 98, y + 50, "Ask the desk from Claude or any MCP client.", 11.5, 400, MUT)
s.T(hx + 98, y + 67, "sqrlane.com/mcp · read-only", 11.5, 600, "#3A3A3A")
status(hx + hw - 104, y + 60, "Live today", True)
s.end()
y += 88

s.g("disclosure")
s.T(hx, y + 14, "None of the named systems is connected in this build: no vendor credential, no native client.", 10.5, 400, GREY)
s.T(hx, y + 30, "SQRlane reads what they export or an endpoint you give it, and writes nothing until you approve.", 10.5, 400, GREY)
s.end()
s.end()

s.T(M, 946, "No new system to keep. The work lands where your desk already looks.", 28, 600, ls=-0.6)
s.footer(9)
s.write("slide-09-integrations.svg")
