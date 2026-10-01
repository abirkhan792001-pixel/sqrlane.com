"""Shared kit for the v2 deck (slides after the cover). Figma-editable SVG:
inline attributes, no <style>, named groups, fonts by name only."""
import pathlib, re
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
        fam = "Geist"                       # one typeface across the deck
        if mono: ls = round(ls * 0.6, 2)    # former mono labels: tighter tracking in Geist
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
    def export(self, group, name, box, pad=2):
        """One named layer as its own SVG, cropped to the box it was built in, so a
        panel can go into Figma on its own and never drift from the slide it came from.
        The layer is moved to the origin on its own <g>, so it stays one named layer."""
        doc = "\n".join(self.o)
        i = doc.index(f'<g id="{group}">')
        depth = 0
        for m in re.finditer(r'<g[\s>]|</g>', doc[i:]):
            depth += 1 if m.group().startswith("<g") else -1
            if depth == 0:
                frag = doc[i:i + m.end()]
                break
        ids = set(re.findall(r' id="([^"]+)"', frag))
        refs = set(re.findall(r'url\(#([^)]+)\)', frag))
        assert refs <= ids, f"{group} uses defs from outside it: {refs - ids}"
        x, y, w, h = box
        frag = frag.replace(f'<g id="{group}">',
                            f'<g id="{group}" transform="translate({pad - x} {pad - y})">', 1)
        out = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w + 2 * pad}" height="{h + 2 * pad}" '
               f'viewBox="0 0 {w + 2 * pad} {h + 2 * pad}">\n{frag}\n</svg>')
        assert "\u2014" not in out, "em dash in slide copy"
        p = pathlib.Path(__file__).with_name(name)
        p.write_text(out, encoding="utf-8")
        print("wrote", p)

    def write(self, name):
        self.o.append('</svg>')
        p = pathlib.Path(__file__).with_name(name)
        p.write_text("\n".join(self.o), encoding="utf-8")
        assert "—" not in p.read_text(), "em dash in slide copy"
        print("wrote", p)
