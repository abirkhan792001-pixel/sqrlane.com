#!/usr/bin/env python3
"""Slide 02 - Introduction. Writes slide-02-introduction.svg (Figma-editable:
inline attributes, no <style>, named groups, fonts by name only)."""
import pathlib
INK, MUT, AMB, BG, CARD = "#0A0A0A", "#6B6B6B", "#96580A", "#FAFAFA", "#FFFFFF"
SAGE = "#DBDBCD"
M, W = 96, 1920
out = []
def T(x, y, s, size, weight=400, fill=INK, anchor="start", ls=0, mono=False, idn=None):
    fam = "Geist Mono" if mono else "Geist"
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    i = f' id="{idn}"' if idn else ""
    out.append(f'<text{i} x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}"{a}{l}>{s}</text>')
def R(x, y, w, h, fill, rx=0, extra=""):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{extra}/>')
def rule(y, op=0.12, x=M, w=W-2*M):
    R(x, y, w, 1, INK, extra=f' fill-opacity="{op}"')
G = lambda n: out.append(f'<g id="{n}">'); E = lambda: out.append('</g>')

out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">')
R(0, 0, 1920, 1080, BG); out[-1] = out[-1].replace('<rect', '<rect id="background"')

G("header")
R(M, 104, 10, 10, AMB, 2)
T(M+24, 114, "01 · INTRODUCTION", 15, 500, MUT, ls=3, mono=True)
T(M-3, 196, "A freight forwarder’s product is a date.", 66, 600, ls=-2)
T(M, 246, "No ships. No trucks. One promise: this box, there, by then.", 24, 400, MUT)
rule(282, 0.12)
E()

# the promise: one booking across the lane
CX = [300, 740, 1180, 1620]
LY = 420
G("the-promise")
T(M, 354, "SHP-001", 16, 600, mono=True, ls=0.6)
T(M+92, 354, "Automotive parts · Shanghai → Munich", 17, 400, MUT)
T(W-M-196, 354, "4 days to spare", 17, 500, AMB, anchor="end")
T(W-M, 356, "14 Oct", 40, 600, anchor="end", ls=-1)
out.append(f'<path id="lane" d="M{M} {LY} H{W-M}" stroke="{INK}" stroke-width="2.5" stroke-linecap="round" fill="none"/>')
for i, (x, name) in enumerate(zip(CX, ["SHANGHAI", "SUEZ", "HAMBURG", "MUNICH"])):
    G(f"stop-{name.lower()}")
    fill = INK if i == 0 else BG
    out.append(f'<circle cx="{x}" cy="{LY}" r="8" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>')
    T(x+16, LY-14, name, 13, 500, INK, ls=1.6, mono=True)
    out.append(f'<path d="M{x} {LY+10} V{LY+70}" stroke="{AMB}" stroke-width="1.5" stroke-dasharray="3 4" fill="none"/>')
    E()
E()

# four things that take the date, hung where they strike
CW4, CY, CH = 408, 490, 290
cards = [
    ("AT BOOKING · PRICE", "2.4×", "swing in the price of one 40ft box", "Drewry · $1,913 to $4,526 per 40ft"),
    ("ON THE WATER · CHOKEPOINTS", "3 of 14", "trade lanes with no way around", "BCG · 2026"),
    ("AT THE BORDER · POLICY", "+128%", "more rule changes to track", "Resilinc EventWatchAI · 2024 vs 2023"),
    ("INLAND · CLIMATE", "146 years", "since the Rhine ran this low", "gCaptain · ING · Aug 2026"),
]
ids = ["price", "chokepoints", "policy", "climate"]
for k, ((eb, big, desc, src), idn) in enumerate(zip(cards, ids)):
    x = M + k*(CW4+32)
    G(f"threat-{idn}")
    R(x, CY, CW4, CH, CARD, 14, f' stroke="{INK}" stroke-opacity="0.12"')
    T(x+28, CY+42, eb, 12, 500, MUT, ls=2, mono=True)
    T(x+26, CY+114, big, 60, 600, ls=-1.8)
    T(x+28, CY+150, desc, 17, 400, INK)
    vy = CY+180
    if idn == "price":
        for j, (lab, v, col) in enumerate([("$1,913", 1913, "#D4D4D4"), ("$4,526", 4526, AMB)]):
            w = round(260*v/4526)
            R(x+28, vy+j*30, w, 18, col, 4)
            T(x+28+w+12, vy+j*30+14, lab, 14, 600 if j else 500, AMB if j else MUT, mono=True)
    if idn == "chokepoints":
        for j in range(14):
            cx = x+36+j*25
            if j < 3:
                out.append(f'<circle cx="{cx}" cy="{vy+22}" r="8" fill="{AMB}"/>')
            else:
                out.append(f'<circle cx="{cx}" cy="{vy+22}" r="7.25" fill="none" stroke="{INK}" stroke-opacity="0.28" stroke-width="1.5"/>')
        T(x+28, vy+60, "If one closes, there is no other route.", 14, 400, MUT)
    if idn == "policy":
        for j, (lab, v, col, tc) in enumerate([("regulatory", 128, AMB, AMB), ("geopolitical", 123, "#D4D4D4", MUT)]):
            T(x+28, vy+j*30+14, lab, 13, 400, MUT)
            w = round(200*v/128)
            R(x+128, vy+j*30, w, 18, col, 4)
            T(x+128+w+10, vy+j*30+14, f"+{v}%", 14, 600, tc, mono=True)
    if idn == "climate":
        R(x+28, vy+10, 352, 10, "#EBEBEB", 5)
        R(x+220, vy+10, 160, 10, "#D4D4D4", 5)
        R(x+44, vy+2, 3, 26, AMB, 1.5)
        T(x+52, vy+48, "now · record low", 13, 500, AMB)
        T(x+380, vy+48, "normal", 13, 400, MUT, anchor="end")
    rule(CY+CH-44, 0.08, x+28, CW4-56)
    T(x+28, CY+CH-18, src, 11.5, 500, MUT, mono=True, ls=0.3)
    E()

# the person who owns the date
BY = 840
G("the-desk")
R(M, BY-18, 10, 10, INK, 2)
T(M+24, BY-8, "AND THE PERSON WHO OWNS IT", 13, 500, MUT, ls=2.4, mono=True)
BW = 1000
R(M, BY+8, BW, 52, "#EBEBEB", 10)
R(M, BY+8, round(BW*0.40), 52, INK, 10)
T(M+20, BY+41, "40% admin", 17, 600, BG)
T(M+round(BW*0.40)+20, BY+41, "everything else", 17, 400, MUT)
T(M, BY+92, "Quotes, data entry, documents, invoices, customs. No time left to watch the lane.", 15, 400, MUT)
T(M+BW, BY+92, "logistics industry surveys · upper estimate", 11.5, 500, MUT, anchor="end", mono=True)
T(1180, BY+26, "The person who could protect the date", 34, 600, ls=-0.8)
T(1180, BY+70, "is stuck doing data entry.", 34, 600, ls=-0.8)
E()

G("footer")
rule(978, 0.12)
R(M, 1004, 22, 22, INK, 6)
out.append(f'<path d="M{M+5.5} {1020}h11 M{M+5.5} {1015}h7.5 M{M+5.5} {1010}h4" stroke="{BG}" stroke-width="1.8" stroke-linecap="round" fill="none"/>')
T(M+34, 1021, "sqrlane", 16, 600)
T(M+104, 1021, "Automates the desk. Acts before the route breaks.", 14, 400, MUT)
T(W-M, 1021, "SLIDE 02", 12.5, 500, MUT, anchor="end", ls=2, mono=True)
E()
out.append('</svg>')
p = pathlib.Path(__file__).with_name("slide-02-introduction.svg")
p.write_text("\n".join(out), encoding="utf-8"); print("wrote", p)
