"""app.py - the web layer. Serves the dashboard and exposes the trigger.

A handful of routes and two static pages. That is the whole backend:

    GET  /              the landing page - what this is, before you press anything
    GET  /app           the dashboard (the demo itself)
    GET  /fonts/{file}  the self-hosted Geist faces the pages are set in
    GET  /api/initial   the calm 'before' board, so the page renders instantly
    GET  /api/gauges    live Rhine water levels for the landing page
    POST /run           the trigger button - runs the orchestrator, returns JSON

Start it:

    uvicorn src.app:app --reload
    then open http://127.0.0.1:8000
"""

import hashlib
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from src import config, llm, orchestrator, simulation

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
INDEX = STATIC_DIR / "index.html"        # the dashboard, served at /app
LANDING = STATIC_DIR / "landing.html"    # the front door, served at /
PAPER = STATIC_DIR / "whitepaper.html"   # the technical whitepaper, served at /whitepaper

# The four pages the front door hands off to. Each answers one question and
# says which on itself, so none of them has to carry the whole pitch:
#   product      - what you get
#   how-it-works - how a decision is made
#   use-cases    - when it fires, and what changes
#   about        - what is real here, and what is not
PAGES = {name: STATIC_DIR / f"{name}.html"
         for name in ("product", "how-it-works", "use-cases", "about")}

# The deck, which is a different kind of page: it argues the pitch to a room
# rather than answering a visitor's question, so it sits outside the four above
# and is routed on its own.
DECK = STATIC_DIR / "deck.html"          # the pitch deck, served at /deck
WHAT = STATIC_DIR / "what.html"          # the What section on its own, served at /what
PITCH = STATIC_DIR / "pitch.html"        # the rebuilt deck, served at /pitch
FONTS_DIR = STATIC_DIR / "fonts"         # Geist, self-hosted: no CDN, ever
VIDEO_DIR = STATIC_DIR / "video"         # the hero reel; absent in a fresh checkout

app = FastAPI(title="SQRlane",
              description="Demo prototype. Drafts emails; sends nothing.")


class RunRequest(BaseModel):
    """Options the button can send. The defaults are what the demo uses."""
    live: bool = True             # pull real news alongside the scripted event
    inject: bool = True           # load the selected scripted scenario
    use_llm: bool = True          # fall back to deterministic logic if this is false
    scenario: str | None = None   # hamburg, redsea, rhine, france. None = the default


def _page(path: Path, what: str):
    """Serve a static page, or say which file is missing and why.

    Only the missing branch is interesting: it is reachable when a deploy fails
    to bundle static/, and a named file beats a 500 at whoever opened the page.
    """
    if not path.exists():
        return HTMLResponse(status_code=500, content=(
            f"<h1>{what} file missing</h1><p>Expected <code>{path}</code>. If this "
            "is a deployed build, check that <code>vercel.json</code> still lists "
            "<code>static/**</code> under <code>includeFiles</code>.</p>"))
    return FileResponse(path)


@app.get("/")
def landing():
    """The front door: what SQRlane is, and what is real about it."""
    return _page(LANDING, "Landing page")


@app.get("/product")
def product():
    """What the desk gets: the roster, the write-back map, the approval gate."""
    return _page(PAGES["product"], "Product page")


@app.get("/how-it-works")
def how_it_works():
    """The mechanism: sixty sources in, one decision per booking out."""
    return _page(PAGES["how-it-works"], "How it works page")


@app.get("/use-cases")
def use_cases():
    """Four disruptions over one board, and the four different calls they force."""
    return _page(PAGES["use-cases"], "Use cases page")


@app.get("/about")
def about():
    """What is real here and what is not, and the desk it is modelled on."""
    return _page(PAGES["about"], "About page")


@app.get("/whitepaper")
def whitepaper():
    """The technical whitepaper: how the loop works, and where it breaks."""
    return _page(PAPER, "Whitepaper")


@app.get("/signals")
def signals():
    """The public live-feed page: headlines from the feeds SQRlane reads."""
    return _page(STATIC_DIR / "signals.html", "Signals page")


@app.get("/deck")
def deck():
    """The pitch deck: what, why, how, who.

    Deliberately not linked from the landing nav. It is the deck you hand to a
    room, not a page for whoever wanders onto the site.
    """
    return _page(DECK, "Pitch deck")


@app.get("/what")
def what():
    """The What section on its own: the problem, and what it costs.

    Split out from /deck because the problem is the half that gets rebuilt most
    often, and because it is the section that goes into Figma on its own.
    """
    return _page(WHAT, "What deck")


@app.get("/pitch")
def pitch():
    """The deck being rebuilt from scratch, slide by slide.

    Generated by tools/build_slides.py from the same objects that write the
    editable SVGs in static/assets/, so the page a room sees and the files that
    go into Figma cannot drift apart.
    """
    return _page(PITCH, "Pitch")


@app.get("/app")
def dashboard():
    """The demo itself. This is the page with the button."""
    return _page(INDEX, "Dashboard")


# A clip is identified by what it contains, not by when it was asked for. The
# filenames are deliberately stable - static/video/README.md's whole contract is
# "drop a file in under that name and it plays" - so the bytes behind a name do
# change, and a cache that cannot tell is a cache that serves the wrong film.
def _clip_etag(target: Path) -> str:
    st = target.stat()
    return '"%s"' % hashlib.md5(
        f"{st.st_mtime_ns}-{st.st_size}".encode()).hexdigest()


@app.get("/video/{filename}")
def video(filename: str, request: Request):
    """The hero reel's clips, served from static/video/.

    Same-origin like everything else the pages load: the promise is that no
    page fetches anything from another host, and a CDN-hosted background video
    would break it for the sake of decoration.

    404 is a supported answer, not a fault. The clips are licensed footage that
    is not in the repository, so a fresh checkout has none - and the hero is
    built to render exactly as it does today when they are missing. That is the
    same rule the rest of the page follows: nothing on screen may depend on a
    fetch that can fail.

    **These revalidate, and that is not a detail.** This route used to answer
    `max-age=86400` with nothing to check it against, which cost twice in one
    afternoon: a truncated response from a cold function got pinned in a
    browser for a day and failed the element on every load afterwards, and a
    replaced clip went on showing the old footage to anyone with a warm cache.
    Both are the same bug - a stable URL whose content changes, cached
    unconditionally.

    So the browser is told to revalidate every time (`max-age=0`) and this
    route answers `If-None-Match` itself. Starlette's FileResponse sends an
    ETag but does not honour one, so without the check below "revalidate"
    would mean re-sending the whole clip on every page view rather than a
    bodiless 304.

    `s-maxage` keeps Vercel's edge cache doing its job in front of that - each
    deployment gets its own cache, so a deploy is already the purge.
    """
    # Resolve and confine to VIDEO_DIR so a crafted name cannot walk upward.
    target = (VIDEO_DIR / filename).resolve()
    if not target.is_file() or VIDEO_DIR.resolve() not in target.parents:
        return JSONResponse(status_code=404, content={"error": "No such clip."})
    cache = "public, max-age=0, s-maxage=86400, must-revalidate"
    etag = _clip_etag(target)
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304,
                        headers={"Cache-Control": cache, "ETag": etag})
    return FileResponse(target, media_type="video/mp4", headers={
        "Cache-Control": cache, "ETag": etag})


@app.get("/fonts/{filename}")
def font(filename: str):
    """Geist Sans and Geist Mono, served from static/fonts/.

    Self-hosted on purpose: the pages must load no external asset, so flaky wifi
    in front of an audience cannot strip the typography or blank the page.
    """
    # Resolve and confine to FONTS_DIR so a crafted name cannot walk upward.
    target = (FONTS_DIR / filename).resolve()
    if not target.is_file() or FONTS_DIR.resolve() not in target.parents:
        return JSONResponse(status_code=404, content={"error": "No such font."})
    return FileResponse(target, media_type="font/woff2", headers={
        "Cache-Control": "public, max-age=31536000, immutable"})


@app.get("/api/scenarios")
def scenarios():
    """The switchable disruptions. All scripted, and labelled so on screen."""
    from src import risk_monitor
    return {"default": risk_monitor.default_scenario(),
            "scenarios": [{k: s[k] for k in ("id", "name", "kind", "summary",
                                             "decision_type", "expected")}
                          for s in risk_monitor.load_scenarios()]}


@app.get("/api/health")
def health(request: Request):
    """What the app can actually see. First stop when a deploy misbehaves.

    Reports the path FastAPI received, so a routing problem shows up here as a
    path that is not /api/health.
    """
    return {
        "ok": True,
        "path_seen_by_app": request.url.path,
        "serverless": config.SERVERLESS,
        "dashboard_present": INDEX.exists(),
        "landing_present": LANDING.exists(),
        "whitepaper_present": PAPER.exists(),
        "deck_present": DECK.exists(),
        "what_present": WHAT.exists(),
        "fonts_present": sorted(f.name for f in FONTS_DIR.glob("*.woff2")),
        "data_files_present": {
            f.name: f.exists() for f in (
                config.CHOKEPOINTS_FILE, config.ROUTES_FILE,
                config.SHIPMENTS_FILE, config.INJECTED_EVENTS_FILE)
        },
        "risk_state_path": str(config.RISK_STATE_FILE),
        "risk_state_dir_writable": os.access(config.RISK_STATE_FILE.parent, os.W_OK),
        "ai_provider": llm.describe() if llm.is_configured() else None,
        # Groq's model is resolved at runtime, so name the one really in use.
        "ai_model": llm.active_model() if llm.is_configured() else None,
        "ai_model_source": llm.resolution_note() or "not resolved yet",
        "live_pull_budget_seconds": config.LIVE_PULL_BUDGET_SECONDS,
        "gauge_budget_seconds": config.GAUGE_BUDGET_SECONDS,
        "gauge_cache_seconds": config.GAUGE_CACHE_SECONDS,
    }


# The landing page's live gauge strip, cached in the process. The page is
# public and PEGELONLINE only refreshes about every fifteen minutes, so reading
# it again on every visit would be both rude to the source and slower than the
# page for no new information. On Vercel each warm instance keeps its own copy,
# which is fine - the point is not to hit the gauge once per visitor.
_gauge_cache = {"at": 0.0, "payload": None}


def _gauge_response(payload: dict, *, age: float, stale: bool):
    """Attach the age to the body and the caching rules to the headers."""
    body = dict(payload, stale=stale, age_seconds=round(age))
    # A good reading may be cached; a failure must not be, or one bad minute
    # would be served for the next five.
    cache = ("no-store" if stale or not payload.get("ok") else
             f"public, max-age=60, s-maxage={config.GAUGE_CACHE_SECONDS}")
    return JSONResponse(body, headers={"Cache-Control": cache})


@app.get("/api/gauges")
def gauges():
    """Rhine water levels, read live from PEGELONLINE.

    This never fails the caller. If the source is unreachable it serves the last
    good reading marked stale, or an empty payload marked not-ok. The landing
    page is allowed to say the gauges are unavailable; it is not allowed to
    break because a river gauge is down.
    """
    from src import risk_monitor

    now = time.monotonic()
    cached = _gauge_cache["payload"]
    age = now - _gauge_cache["at"]
    if cached and age < config.GAUGE_CACHE_SECONDS:
        return _gauge_response(cached, age=age, stale=False)

    try:
        fresh = risk_monitor.read_rhine_gauges()
    except Exception as exc:                      # noqa: BLE001
        fresh = {"source": "PEGELONLINE", "gauges": [], "ok": False,
                 "error": f"{type(exc).__name__}: {exc}"}

    if fresh.get("ok"):
        _gauge_cache.update(at=now, payload=fresh)
        return _gauge_response(fresh, age=0, stale=False)

    # Nothing fresh. A stale reading still tells the truth about the river as of
    # a stated time, which beats an empty panel.
    if cached:
        return _gauge_response(cached, age=age, stale=True)
    return _gauge_response(fresh, age=0, stale=False)


# In-memory cache for the live feed panel. 15 min is plenty - the panel
# rotates through 4-6 items every few seconds, and hammering three RSS
# hosts on every visit would be rude and slow the page. A cold serverless
# instance will re-fetch on its first request and cache from there.
_feed_cache = {"at": 0.0, "payload": None}
_FEED_CACHE_SECONDS = 900

# A curated pool of regional broadcasters, all keyless. Kept small because
# this endpoint runs on every /signals load and cannot afford the full
# RSS_FEEDS budget - risk_monitor is where breadth belongs, not here. This
# is still a subset of config.RSS_FEEDS; adding a feed there is what wires
# it into the risk monitor, adding a feed here only surfaces it on the
# panel. If the two need to reference the same URL, take it from
# config.RSS_FEEDS by name rather than re-typing.
_LIVE_FEEDS = [
    ("NDR Hamburg", "de", "https://www.ndr.de/nachrichten/hamburg/index-rss.xml"),
    ("tagesschau",  "de", "https://www.tagesschau.de/index~rss2.xml"),
    ("DW Deutsch",  "de", "https://rss.dw.com/rdf/rss-de-all"),
    ("Rijnmond",    "nl", "https://www.rijnmond.nl/rss/index.xml"),
    ("NOS Nieuws",  "nl", "https://feeds.nos.nl/nosnieuwsalgemeen"),
    ("France Info", "fr", "https://www.francetvinfo.fr/titres.rss"),
    ("Le Monde",    "fr", "https://www.lemonde.fr/rss/une.xml"),
    ("NHK",         "ja", "https://www3.nhk.or.jp/rss/news/cat0.xml"),
    ("BBC Arabic",  "ar", "https://feeds.bbci.co.uk/arabic/rss.xml"),
]

# Cap how many items per feed and in total, so a chatty feed cannot crowd
# out the rest and one translation batch is not too long for the model to
# parse cleanly. 3 * 9 = 27 max; the total cap trims to 18 after
# de-duplication and ordering.
_ITEMS_PER_FEED = 3
_MAX_ITEMS = 18


def _translate_items_to_english(items):
    """Batch-translate non-English titles + summaries to English.

    Adds `title_en` and `summary_en` to each item in place. Called once
    per cache refresh (every 15 min), so it never blocks a warm request.
    Returns a small dict describing what happened so a failure shows up
    in the response payload instead of being swallowed - broad try/except
    used to eat the actual error and left us guessing in production.
    """
    if not llm.is_configured():
        return {"status": "off", "reason": "llm not configured"}
    todo = [(i, it) for i, it in enumerate(items)
            if (it.get("iso") or "").lower() != "en"
            and (it.get("title") or it.get("summary"))]
    if not todo:
        return {"status": "skipped", "reason": "no non-english items"}

    # Small batches keep each round-trip fast (Groq's free tier can be
    # slow to first token) so one bad call only loses a handful of items,
    # and the whole translation stays inside the function's time budget.
    BATCH = 6
    translated = 0
    errors = []
    for start in range(0, len(todo), BATCH):
        chunk = todo[start:start + BATCH]
        payload = [
            {"i": idx, "lang": (items[idx].get("iso") or "").lower(),
             "title": items[idx].get("title", "")[:200],
             "summary": items[idx].get("summary", "")[:220]}
            for (idx, _) in chunk
        ]
        prompt = (
            "Translate each item's title and summary into natural, concise "
            "English. Keep proper nouns (people, places, organisations, "
            "publication names) as they are. Do not paraphrase or add "
            "commentary. If the source is already in English return the "
            "original text.\n\n"
            "Return a JSON array in the SAME order and length as the input, "
            "with objects of exactly this shape:\n"
            '  {"i": <same index>, "title_en": "<translated title>", '
            '"summary_en": "<translated summary or empty string>"}\n\n'
            "Input:\n" + json.dumps(payload, ensure_ascii=False)
        )
        try:
            out = llm.complete_json(prompt, temperature=0.2, max_tokens=900)
        except Exception as exc:                       # noqa: BLE001
            # Record the reason so it surfaces in the response payload -
            # a silent failure took an afternoon to diagnose on production.
            errors.append(f"{type(exc).__name__}: {exc}"[:200])
            continue
        if not isinstance(out, list):
            errors.append(f"non-list JSON: {type(out).__name__}")
            continue
        for row in out:
            if not isinstance(row, dict):
                continue
            idx = row.get("i")
            if not isinstance(idx, int) or idx < 0 or idx >= len(items):
                continue
            te = (row.get("title_en") or "").strip()
            se = (row.get("summary_en") or "").strip()
            wrote = False
            if te and te.lower() != (items[idx].get("title") or "").lower():
                items[idx]["title_en"] = te[:200]
                wrote = True
            if se and se.lower() != (items[idx].get("summary") or "").lower():
                items[idx]["summary_en"] = se[:220]
                wrote = True
            if wrote:
                translated += 1

    diag = {"status": "ok" if translated else "failed",
            "translated": translated, "todo": len(todo),
            "model": llm.active_model() if llm.is_configured() else None}
    if errors:
        diag["errors"] = errors[:3]
    return diag


@app.get("/api/live-feed")
def live_feed():
    """A handful of live headlines from three regional broadcasters.

    Powers the small floating card on the landing page. Fails soft in
    exactly the same shape as /api/gauges: a bad read serves the last
    good payload if there is one, otherwise returns ok:false items:[]
    so the client can hide the card rather than break the page.
    """
    import calendar
    import re
    from datetime import datetime, timezone

    import feedparser
    from src import httpget

    now = time.monotonic()
    cached = _feed_cache["payload"]
    age = now - _feed_cache["at"]
    if cached and age < _FEED_CACHE_SECONDS:
        return JSONResponse(dict(cached, age_seconds=round(age)))

    # RSS summaries often ship as HTML. Strip tags, collapse whitespace and
    # decode the handful of entities feedparser leaves behind - the panel
    # renders one line as plain text, so a stray <p> or &nbsp; would show.
    _tag_re = re.compile(r"<[^>]+>")
    _ws_re = re.compile(r"\s+")
    _entities = {"&amp;": "&", "&nbsp;": " ", "&#160;": " ",
                 "&quot;": '"', "&#39;": "'", "&apos;": "'",
                 "&lt;": "<", "&gt;": ">"}

    def _clean_summary(raw: str) -> str:
        if not raw:
            return ""
        s = _tag_re.sub(" ", raw)
        for k, v in _entities.items():
            s = s.replace(k, v)
        s = _ws_re.sub(" ", s).strip()
        # A one-liner is 180 chars at the outside; the CSS clamps visually
        # to one line, this caps the payload so a wall of copy is never sent.
        if len(s) > 180:
            s = s[:177].rstrip() + "…"
        return s

    def _published_iso(entry) -> str:
        # feedparser normalises to a UTC time.struct_time on published_parsed
        # or updated_parsed. Prefer published; fall back to updated.
        for key in ("published_parsed", "updated_parsed"):
            ts = entry.get(key)
            if ts:
                try:
                    return datetime.fromtimestamp(
                        calendar.timegm(ts), tz=timezone.utc
                    ).isoformat().replace("+00:00", "Z")
                except (TypeError, ValueError, OverflowError):
                    continue
        return ""

    # Fetch the feeds in parallel. Serial fetches (9 * up to 3.5s each) can
    # eat most of the 60s function budget on a cold start, which is what
    # left production without translations even though the code shipped.
    from concurrent.futures import ThreadPoolExecutor

    def _read_one(spec):
        name, iso, url = spec
        rows = []
        try:
            resp = httpget.get_capped(url, timeout=3.0)
            parsed = feedparser.parse(resp.content)
        except Exception:                             # noqa: BLE001
            return rows
        for entry in list(parsed.entries)[:_ITEMS_PER_FEED]:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            summary = _clean_summary(
                entry.get("summary") or entry.get("description") or ""
            )
            # A summary that just echoes the title adds noise, not
            # information - drop it so the row stays a headline.
            if summary and summary.lower().startswith(title.lower()[:60]):
                summary = ""
            rows.append({
                "source": name,
                "iso": iso,
                "title": title[:160],
                "summary": summary,
                "published": _published_iso(entry),
                "link": entry.get("link", ""),
            })
        return rows

    items = []
    with ThreadPoolExecutor(max_workers=len(_LIVE_FEEDS)) as pool:
        for rows in pool.map(_read_one, _LIVE_FEEDS):
            items.extend(rows)

    # Round-robin merge so each source's first item comes before any
    # source's second item, then cap. Otherwise a run of German feeds at
    # the top of _LIVE_FEEDS pushes every other language off the panel.
    by_feed = {}
    for it in items:
        by_feed.setdefault(it["source"], []).append(it)
    sources_order = [n for (n, _, _) in _LIVE_FEEDS if n in by_feed]
    interleaved = []
    for row in range(_ITEMS_PER_FEED):
        for src in sources_order:
            bucket = by_feed[src]
            if row < len(bucket):
                interleaved.append(bucket[row])
    items = interleaved[:_MAX_ITEMS]

    # Translate non-English titles/summaries in place. Returns a small
    # diagnostic dict so a failure is visible in the payload instead of
    # being silently swallowed.
    translation_diag = _translate_items_to_english(items)

    payload = {"ok": bool(items), "items": items,
               "sources": [{"name": n, "iso": i} for (n, i, _) in _LIVE_FEEDS],
               "translation": translation_diag}
    if items:
        _feed_cache.update(at=now, payload=payload)
        return JSONResponse(dict(payload, age_seconds=0),
                            headers={"Cache-Control":
                                     f"public, max-age=60, s-maxage={_FEED_CACHE_SECONDS}"})
    if cached:
        return JSONResponse(dict(cached, age_seconds=round(age)))
    return JSONResponse(dict(payload, age_seconds=0),
                        headers={"Cache-Control": "no-store"})


@app.get("/api/initial")
def initial():
    """The board before the button is pressed: five shipments, all green."""
    try:
        state = orchestrator.initial_state()
    except OSError as exc:
        return JSONResponse(status_code=200, content={
            "state": "error",
            "error": f"Could not read the shipment data: {exc}",
            "notes": ["The data/ files did not ship with this build. Check "
                      "includeFiles in vercel.json."],
            "shipments": [], "risk": {"events": [], "sources": []},
            "summary": {"reroute": 0, "hold": 0, "no-action": 0, "drafts": 0},
        })
    state["provider"] = llm.describe() if llm.is_configured() else None
    state["forwarder"] = config.FORWARDER["company"]
    state["ai"] = {
        "provider": config.LLM_PROVIDER if llm.is_configured() else None,
        "model": llm.active_model() if llm.is_configured() else None,
        "model_source": llm.resolution_note(),
    }
    return state


@app.get("/api/simulation")
def api_simulation(days: int | None = None, use_llm: bool = False):
    """Replay the authored week over the board.

    Deterministic by default: a full week is seven shipments times eight days of
    decisions, which is far more model calls than a free tier will take. The
    timeline is authored either way and the payload says so.
    """
    try:
        return simulation.run(use_llm=use_llm, until_day=days, verbose=False)
    except Exception as exc:  # noqa: BLE001 - same reason as /run
        return JSONResponse(status_code=200, content={
            "state": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "days": [], "totals": {},
        })


@app.post("/run")
def run(request: RunRequest | None = None):
    """One press of the button: refresh risk, decide, draft, return everything.

    Any failure is returned as a readable payload rather than a 500, because a
    stack trace on screen in front of an audience is its own kind of failure.
    """
    options = request or RunRequest()
    try:
        return orchestrator.run_cycle(live=options.live, inject=options.inject,
                                      use_llm=options.use_llm, scenario=options.scenario)
    except Exception as exc:  # noqa: BLE001 - never let the demo show a stack trace
        return JSONResponse(status_code=200, content={
            "state": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "notes": ["The run failed. The scripted scenario can still be shown with "
                      "the live pull turned off."],
            "shipments": [], "risk": {"events": [], "sources": []},
            "summary": {"reroute": 0, "hold": 0, "no-action": 0, "drafts": 0},
        })
