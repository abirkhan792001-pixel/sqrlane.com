#!/usr/bin/env python3
"""Animate a deck slide into an MP4 for Figma Slides.

Figma drops SVG animation on import, so the motion is rendered to video instead: the
slide's own SVG is opened in headless Chromium, its named layers (the <g id> groups the
builders write) are hidden and then revealed on a timeline, and every frame is captured
and encoded as H.264. The last frame is the finished slide, held, so the video can loop.

    python3 animate.py 07      # -> slide-07-the-how-1.mp4
    python3 animate.py 08
    python3 animate.py 01      # -> slide-01-cover.mp4 and slide-01-cover.gif (a loop)
    python3 animate.py 01 --at 2 6 9   # check single frames as PNGs, no video

Needs: pip install playwright imageio-ffmpeg; Geist in ~/.fonts (see HANDOFF.md)."""
import glob, pathlib, subprocess, sys, tempfile
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
FPS, W, H = 30, 1920, 1080
SCALE = 2          # capture at 2x: the video is 3840x2160 (4K), so 11px text stays sharp
                   # when Figma or a projector scales it

# (layer id, start in seconds, effect). Layers not listed are on screen from the start.
# Effects: up (rise and fade in), down (drop in from above), left (a short slide from the
# right), right (a long slide in from the right edge), pop (scale up), fade. A slide may
# add a scene script (scene_NN.js) for motion a reveal cannot do: counters, spinners,
# a chat playing out.
TIMELINES = {
    # The cover is a loop, not a build: everything moves in scene_01.js, and the
    # last frame meets the first, so it also ships as a GIF.
    "01": {"file": "slide-01-cover.svg", "length": 14.0, "scene": "scene_01.js", "steps": [], "gif": True},
    "07": {"file": "slide-07-the-how-1.svg", "length": 15.0, "scene": "scene_07.js", "steps": [
        ("risk-layer", 0.3, "up"), ("the-morning", 0.4, "up"),
        ("front-doors", 0.8, "up"),
        ("notifications", 0.9, "pop"), ("popup-mail", 1.0, "right"),
        ("the-desk", 1.3, "fade"),
        ("stage-quote", 1.4, "up"), ("stage-book", 1.6, "up"), ("stage-documents", 1.8, "up"),
        ("popup-agent", 1.8, "right"),
        ("stage-in-transit", 2.0, "up"), ("stage-arrival", 2.2, "up"), ("stage-billing", 2.4, "up"),
        ("playbook", 3.0, "up"), ("gate-and-record", 3.8, "up"),
    ]},
    "08": {"file": "slide-08-the-how-2.svg", "length": 8.0, "steps": [
        ("watch", 0.3, "up"),
        ("notifications", 0.7, "pop"), ("popup-news", 0.8, "down"),
        ("risk-agent", 1.1, "up"),
        ("popup-agent", 1.6, "left"), ("routing-agent", 1.7, "up"),
        ("this-run", 2.3, "up"), ("cost-impact", 2.4, "up"),
        ("decision-reroute", 3.0, "up"), ("comms-agent", 3.1, "up"),
        ("planner-agent", 3.5, "up"),
        ("decision-mail", 3.8, "up"), ("the-desk", 4.0, "up"),
        ("decision-hold", 4.6, "up"), ("gate-and-record", 4.7, "up"),
        ("detection-trail", 5.3, "up"),
    ]},
}
DUR = 0.6   # each reveal

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;padding:0;background:#FAFAFA}
body > svg{display:block;width:1920px;height:1080px}
.anim{transform-box:fill-box;transform-origin:center}
</style></head><body>%SVG%<script>
const STEPS = %STEPS%, DUR = %DUR%;
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


def chrome():
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    return hits[-1] if hits else None


def page_html(spec):
    import json
    svg = (HERE / spec["file"]).read_text(encoding="utf-8")
    svg = svg[svg.index("<svg"):]
    missing = [i for i, _, _ in spec["steps"] if f'id="{i}"' not in svg]
    assert not missing, f"layers not in the slide: {missing}"
    return (PAGE.replace("%SVG%", svg).replace("%STEPS%", json.dumps(spec["steps"]))
                .replace("%DUR%", str(DUR))
                .replace("%SCENE%", (HERE / spec["scene"]).read_text(encoding="utf-8") if "scene" in spec else ""))


def stills(key, times):
    """Single frames as PNGs beside the slide, to check a moment without a video."""
    spec = TIMELINES[key]
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        page_file = pathlib.Path(tmp) / "slide.html"
        page_file.write_text(page_html(spec), encoding="utf-8")
        b = pw.chromium.launch(executable_path=chrome(), args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(page_file.as_uri())
        pg.wait_for_timeout(300)
        for t in times:
            pg.evaluate(f"setTime({t})")
            out = HERE / f"{spec['file'].replace('.svg', '')}-t{t:05.2f}.png"
            pg.screenshot(path=str(out))
            print("wrote", out)
        b.close()


def render(key):
    spec = TIMELINES[key]
    html = page_html(spec)
    out = HERE / spec["file"].replace(".svg", ".mp4")
    frames = round(spec["length"] * FPS)
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        page_file = pathlib.Path(tmp) / "slide.html"
        page_file.write_text(html, encoding="utf-8")
        b = pw.chromium.launch(executable_path=chrome(), args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=SCALE)
        pg.goto(page_file.as_uri())
        pg.wait_for_timeout(300)                     # fonts settle
        for f in range(frames):
            pg.evaluate(f"setTime({f / FPS})")
            pg.screenshot(path=f"{tmp}/f{f:04d}.png")
        b.close()
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                        "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "12",
                        "-preset", "slow", "-tune", "animation", "-profile:v", "high", "-movflags", "+faststart", str(out)], check=True)
        if spec.get("gif"):
            # 1920 wide at 25 fps (a GIF frame lasts whole hundredths of a second, so
            # 30 fps is not representable), one palette for the whole loop so colours
            # do not flicker between frames, and only the changed rectangle re-dithered.
            gif = out.with_suffix(".gif")
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                            "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png", "-vf",
                            "fps=25,scale=1920:-1:flags=lanczos,split[a][b];"
                            "[a]palettegen=max_colors=192:stats_mode=full[p];"
                            "[b][p]paletteuse=dither=sierra2_4a:diff_mode=rectangle",
                            "-loop", "0", str(gif)], check=True)
            print("wrote", gif, f"({gif.stat().st_size / 1e6:.1f} MB)")
    print("wrote", out, f"({frames} frames, {spec['length']}s)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--at" in args:
        i = args.index("--at")
        stills(args[0], [float(x) for x in args[i + 1:]])
    else:
        for k in (args or TIMELINES):
            render(k)
