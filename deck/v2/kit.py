"""Shared kit for the v2 deck (slides after the cover). Figma-editable SVG:
inline attributes, no <style>, named groups, fonts by name only."""
import pathlib
INK, MUT, AMB = "#0A0A0A", "#6B6B6B", "#96580A"
BG, CARD, TRACK, MID = "#FAFAFA", "#FFFFFF", "#EBEBEB", "#D4D4D4"
M, W, H = 96, 1920, 1080
HEADER_RULE = 282   # hairline under the header, mirrors the footer rule at 978
TAGLINE = "Automates the desk. Acts before the route breaks."

class Slide:
    def __init__(self):
        self.o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                  f'<rect id="background" x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>']
    def raw(self, s): self.o.append(s)
    def T(self, x, y, s, size, weight=400, fill=INK, anchor="start", ls=0, mono=False):
        fam = "Geist Mono" if mono else "Geist"
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        self.o.append(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{weight}" fill="{fill}"{a}{l}>{s}</text>')
    def R(self, x, y, w, h, fill, rx=0, extra=""):
        r = f' rx="{rx}"' if rx else ""
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"{r} fill="{fill}"{extra}/>')
    def line(self, x1, y1, x2, y2, stroke=INK, op=0.25, w=1.5, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.o.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{stroke}" stroke-opacity="{op}" stroke-width="{w}" fill="none"{d}/>')
    def rule(self, y, op=0.12, x=M, w=W - 2 * M): self.R(x, y, w, 1, INK, extra=f' fill-opacity="{op}"')
    def card(self, x, y, w, h, rx=14): self.R(x, y, w, h, CARD, rx, f' stroke="{INK}" stroke-opacity="0.12"')
    def g(self, name): self.o.append(f'<g id="{name}">')
    def end(self): self.o.append('</g>')
    def label(self, x, y, s, square=INK, size=13):
        self.R(x, y - 10, 10, 10, square, 2)
        self.T(x + 24, y, s, size, 500, MUT, ls=2.4, mono=True)
    def header(self, eyebrow, headline, sub):
        self.g("header")
        self.label(M, 114, eyebrow, AMB, 15)
        self.T(M - 3, 196, headline, 66, 600, ls=-2)
        self.T(M, 246, sub, 24, 400, MUT)
        self.rule(HEADER_RULE)
        self.end()
    def footer(self, n):
        self.g("footer")
        self.rule(978)
        self.R(M, 1004, 22, 22, INK, 6)
        self.raw(f'<path d="M{M+5.5} 1020h11 M{M+5.5} 1015h7.5 M{M+5.5} 1010h4" stroke="{BG}" stroke-width="1.8" stroke-linecap="round" fill="none"/>')
        self.T(M + 34, 1021, "sqrlane", 16, 600)
        self.T(M + 104, 1021, TAGLINE, 14, 400, MUT)
        self.T(W - M, 1021, f"SLIDE {n:02d}", 12.5, 500, MUT, anchor="end", ls=2, mono=True)
        self.end()
    def write(self, name):
        self.o.append('</svg>')
        p = pathlib.Path(__file__).with_name(name)
        p.write_text("\n".join(self.o), encoding="utf-8")
        assert "—" not in p.read_text(), "em dash in slide copy"
        print("wrote", p)
