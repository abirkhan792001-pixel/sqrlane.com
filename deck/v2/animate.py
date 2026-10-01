#!/usr/bin/env python3
"""Animate a deck slide into an MP4 for Figma Slides.

Figma drops SVG animation on import, so the motion is rendered to video instead: the
slide's own SVG is opened in headless Chromium, its named layers (the <g id> groups the
builders write) are hidden and then revealed on a timeline, and every frame is captured
and encoded as H.264. The last frame is the finished slide, held, so the video can loop.

    python3 animate.py 07        # -> slide-07-the-how-1.mp4, the whole slide
    python3 animate.py 07-desk   # -> slide-07-the-desk.mp4, the dashboard alone
    python3 animate.py 08

A video whose last frame should be the static slide (all of them, today) is checked: the
finished slide is rendered on its own and compared with the last frame, pixel for pixel.

Needs: pip install playwright imageio-ffmpeg; Geist in ~/.fonts (see HANDOFF.md)."""
import glob, json, pathlib, re, subprocess, sys, tempfile
import imageio_ffmpeg
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
FONTS = HERE.parent.parent / "static" / "fonts"
FPS, W, H = 30, 1920, 1080
SCALE = 2          # capture at 2x: the video is 3840x2160 (4K), so 11px text stays sharp
                   # when Figma or a projector scales it

# (layer id, start in seconds, effect). Layers not listed are on screen from the start.
# Effects: up (rise and fade in), down (drop in from above), left (a short slide from the
# right), right (a long slide in from the right edge), pop (scale up), fade. A slide may
# add a scene script (scene_NN.js) for motion a reveal cannot do: counters, spinners,
# a chat playing out.
STEPS_07 = [
    ("risk-layer", 0.3, "up"), ("the-morning", 0.4, "up"),
    ("front-doors", 0.8, "up"),
    ("notifications", 0.9, "pop"), ("popup-mail", 1.0, "right"),
    ("the-desk", 1.3, "fade"),
    ("stage-quote", 1.4, "up"), ("stage-book", 1.6, "up"), ("stage-documents", 1.8, "up"),
    ("popup-agent", 1.8, "right"),
    ("stage-in-transit", 2.0, "up"), ("stage-arrival", 2.2, "up"), ("stage-billing", 2.4, "up"),
    ("playbook", 3.0, "up"), ("gate-and-record", 3.8, "up"),
]
# The dashboard on slides 07 and 08 (the same frame), with a 12px margin of slide
# background: x 84, y 294, 1024 x 608 on the 1920 x 1080 slide. Placed there in Figma, it
# sits exactly over the static mock. Captured at 3.5x: 3584 x 2128, the largest size at this
# aspect inside 4K UHD with both sides a multiple of 16, which every decoder handles cleanly.
DESK_07 = (84, 294, 1024, 608)

# slide 08: the dashboard's reveals are the alert; the right panel follows the story the
# scene plays (scene_08.js): the trail as the headline lands, each agent as it works
STEPS_08 = [
    ("notifications", 0.5, "pop"), ("popup-news", 0.5, "down"),
    ("detection-trail", 0.9, "up"), ("watch", 1.0, "up"),
    ("popup-agent", 1.3, "left"), ("this-run", 1.6, "up"),
    ("risk-agent", 2.2, "up"), ("routing-agent", 3.9, "up"), ("comms-agent", 5.3, "up"),
    ("cost-impact", 7.4, "up"), ("planner-agent", 7.9, "up"), ("the-desk", 8.3, "up"),
    ("gate-and-record", 8.7, "up"),
]

TIMELINES = {
    "07": {"file": "slide-07-the-how-1.svg", "length": 16.0, "scene": "scene_07.js", "steps": STEPS_07},
    "07-desk": {"file": "slide-07-the-how-1.svg", "out": "slide-07-the-desk.mp4", "length": 16.0,
                "scene": "scene_07.js", "steps": STEPS_07, "clip": DESK_07, "scale": 3.5},
    "08": {"file": "slide-08-the-how-2.svg", "length": 18.0, "scene": "scene_08.js", "steps": STEPS_08},
    "08-desk": {"file": "slide-08-the-how-2.svg", "out": "slide-08-the-desk.mp4", "length": 18.0,
                "scene": "scene_08.js", "steps": STEPS_08, "clip": DESK_07, "scale": 3.5},
}
DUR = 0.6   # each reveal

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:"Geist";src:url("%FONT%") format("woff2");font-weight:100 900;font-style:normal}
html,body{margin:0;padding:0;background:#FAFAFA}
body > svg{display:block;width:1920px;height:1080px}
.anim{transform-box:fill-box;transform-origin:center}
</style></head><body>%SVG%<script>
const STEPS = %STEPS%, DUR = %DUR%;
window.LAST_T = %LAST%;          // the last frame's time: a scene can land exactly on the still
window.MARKS = %MARKS%;          // channel_marks.json, for a scene that needs an official mark
const ease = x => 1 - Math.pow(1 - x, 3);
const els = [];
for (const [id, t0, fx] of STEPS) {
  const el = document.getElementById(id);
  if (!el) continue;
  el.classList.add("anim");
  els.push([el, t0, fx]);
  // the connector drawn just before a layer (an arrow is a few loose <path>s) arrives with it
  let sib = el.previousElementSibling;
  while (sib && sib.tagName === "path") { els.push([sib, t0, "fade"]); sib = sib.previousElementSibling; }
}
window.setTime = t => {
  for (const [el, t0, fx] of els) {
    if (!el) continue;
    const p = ease(Math.min(1, Math.max(0, (t - t0) / DUR)));
    el.style.opacity = p;
    const k = 1 - p;
    el.style.transform =
      fx === "up"   ? `translateY(${14 * k}px)` :
      fx === "down" ? `translateY(${-22 * k}px)` :
      fx === "left" ? `translateX(${24 * k}px)` :
      fx === "right" ? `translateX(${180 * k}px)` :
      fx === "pop"  ? `scale(${0.6 + 0.4 * p})` : "none";
  }
  if (window.scene) window.scene(t);
};
</script><script>%SCENE%</script></body></html>"""


FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def h264_level(path):
    """The level the encoder wrote into the stream's first SPS."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path), "-c", "copy", "-bsf:v", "trace_headers",
                        "-frames:v", "1", "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"level_idc\s+\d+ = (\d+)", r.stderr)
    assert m, "could not read the H.264 level"
    return int(m.group(1))


def chrome():
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    return hits[-1] if hits else None


def render(key):
    spec = TIMELINES[key]
    svg = (HERE / spec["file"]).read_text(encoding="utf-8")
    svg = svg[svg.index("<svg"):]
    missing = [i for i, _, _ in spec["steps"] if f'id="{i}"' not in svg]
    assert not missing, f"layers not in the slide: {missing}"
    html = (PAGE.replace("%SVG%", svg).replace("%STEPS%", json.dumps(spec["steps"]))
                .replace("%DUR%", str(DUR))
                .replace("%FONT%", (FONTS / "Geist-Variable.woff2").as_uri())
                .replace("%LAST%", repr((round(spec["length"] * FPS) - 1) / FPS))
                .replace("%MARKS%", (HERE / "channel_marks.json").read_text(encoding="utf-8"))
                .replace("%SCENE%", (HERE / spec["scene"]).read_text(encoding="utf-8") if "scene" in spec else ""))
    out = HERE / spec.get("out", spec["file"].replace(".svg", ".mp4"))
    frames = round(spec["length"] * FPS)
    scale = spec.get("scale", SCALE)
    shot = {}
    if "clip" in spec:
        x, y, w, h = spec["clip"]
        shot["clip"] = {"x": x, "y": y, "width": w, "height": h}
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        page_file = pathlib.Path(tmp) / "slide.html"
        page_file.write_text(html, encoding="utf-8")
        b = pw.chromium.launch(executable_path=chrome(), args=["--no-sandbox"])

        def open_page():
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=scale)
            pg.goto(page_file.as_uri())
            pg.evaluate("document.fonts.load('500 13px Geist').then(() => document.fonts.ready)")
            assert pg.evaluate("document.fonts.check('600 13px Geist')"), "Geist did not load"
            pg.wait_for_timeout(300)
            return pg

        # the finished slide on its own, before anything animates
        pg = open_page()
        pg.screenshot(path=f"{tmp}/static.png", **shot)
        pg.close()
        pg = open_page()
        for f in range(frames):
            pg.evaluate(f"setTime({f / FPS})")
            pg.screenshot(path=f"{tmp}/f{f:04d}.png", **shot)
        b.close()
        last = Image.open(f"{tmp}/f{frames - 1:04d}.png").convert("RGB")
        diff = ImageChops.difference(last, Image.open(f"{tmp}/static.png").convert("RGB")).getbbox()
        assert diff is None, f"the last frame is not the static slide: they differ in {diff}"
        w_px, h_px = last.size
        assert w_px % 16 == 0 and h_px % 16 == 0, f"{w_px}x{h_px}: both sides must be a multiple of 16"
        assert w_px <= 3840 and h_px <= 2160, f"{w_px}x{h_px} is larger than 4K UHD"
        # H.264 High at level 5.1, the level browsers, QuickTime and Figma decode. Left to
        # itself, -tune animation doubles the reference frames, which pushes a 4K frame past
        # 5.1's buffer and x264 silently writes level 6.0 - a file many players will not play.
        # Colour is converted and tagged as BT.709, what players assume for HD and up.
        subprocess.run([FFMPEG, "-y", "-loglevel", "error",
                        "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                        "-c:v", "libx264", "-profile:v", "high", "-level:v", "5.1", "-refs", "4",
                        "-crf", "12", "-preset", "slow", "-tune", "animation",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-color_range", "tv", "-movflags", "+faststart", str(out)], check=True)
    level = h264_level(out)
    assert level <= 51, f"{out.name} is H.264 level {level / 10}, above 5.1"
    print("wrote", out, f"({frames} frames, {spec['length']}s, {w_px}x{h_px}, H.264 level {level / 10}, last frame = static slide)")


if __name__ == "__main__":
    for k in (sys.argv[1:] or TIMELINES):
        render(k)
