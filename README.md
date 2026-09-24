# SQRlane

**AI Agents for freight forwarders.**

**SQRlane runs on the bookings in a forwarder's TMS.** It is not another book to keep:
the shipments are read out of the system of record, the Workers decide against those
records, and every action they take is written back onto them.

SQRlane has **two layers on one TMS**, and the join between them is the point:

- **The workflow layer — the everyday desk.** Eleven Workers work every mail that lands:
  rate requests, bookings, bills of lading, rollovers, invoices, arrival notices. The
  Inbox Worker reads each one and hands it to the Worker that owns it; that Worker asks
  the others what it needs (the fields off the documents, the rate on the lane); the
  Playbook Worker checks every output against the customer's standing instructions and
  sends it back until it complies; the Exception Worker escalates what the desk cannot
  absorb. Every handoff is a **message** on one bus you can read. And when a person
  corrects a Worker, the correction becomes a **lesson** every later run applies — kept
  only if replaying the whole inbox shows it fixes that mail and breaks no earlier lesson.
- **The risk layer — when a lane moves.** Three Workers watch **everything that moves a
  trade lane** — 60 free, keyless sources across six families: news and trade press in
  several languages, river gauges, port weather and sea state, seismic and natural-hazard
  feeds, government filings, and the reference rate a reroute is billed at. When something
  hits, they work out which bookings are affected, decide whether to **reroute** or
  **hold** each one, explain *why*, draft the carrier and customer emails — and hand the
  consequences to the desk: the amendment to Booking, a changed country of entry to
  Customs, the new ETA to Milestones.

Both layers queue every change they make back into the TMS — the exception on the booking,
the new discharge port, routing code and ETA, a new booking, a filed document, a disputed
invoice, each drafted mail on the communication log — and every message and every write is
held for human approval.

> In this build the TMS is a **demo connector** (`src/tms.py`). Both directions are modelled
> and the read is the only door to the book — nothing else in `src/` opens it — but no TMS is
> contacted: there is no client, no credential and no endpoint, and a write-back is a
> described change that stays queued. The inbox the desk works is a synthetic morning of
> mail (`data/inbox.json`), like the bookings: no mailbox is connected.

**The workflow layer**, in the order work flows through it (`src/workflow.py`):

| Group | Worker | Does | |
|---|---|---|---|
| 01 Inbox & rules | **Inbox Worker** | Reads every inbound mail, works out what it is (the model when configured, rules otherwise, lessons always), links it to the booking, and hands it on | `LIVE` |
| | **Playbook Worker** | Checks every output against the customer's standing instructions, and sends it back to the Worker that made it until it complies | `LIVE` |
| 02 Quotes & rates | **Rate Worker** | Prices a lane across the carriers that serve it, for any Worker that asks | `LIVE` |
| | **RFQ Worker** | Reads an inbound rate request into fields and drafts the quote back | `LIVE` |
| 03 Bookings & documents | **Booking Worker** | Opens the booking on the TMS record from the mail and its documents, flags what it cannot verify, drafts the carrier request | `LIVE` |
| | **Docs Worker** | Pulls the fields out of bills of lading, packing lists and invoices, and checks them against the booking | `LIVE` |
| 04 Shipments & exceptions | **Milestones Worker** | Writes carrier notices onto the booking as milestones and ETAs, and answers where-is-my-box | `LIVE` |
| | **Exception Worker** | Catches the rolled box and the mismatched document, and escalates what the desk cannot absorb — a breached booking goes to the Routing Worker | `LIVE` |
| | **Assistant** | Answers questions about what is on the board | `SCRIPTED` |
| 05 Billing & customs | **Invoice Worker** | Reconciles the carrier invoice against what was agreed, and drafts the dispute | `LIVE` |
| | **Customs Worker** | Prepares the entry for the discharge country, and escalates what needs a person | `LIVE` |

**The risk layer**, and the record they share:

| Worker | Does | |
|---|---|---|
| **Risk Worker** | Reads the wires, the press next to the port, the instruments and the government notices, tags what threatens a lane, and flags the exception on the booking | `LIVE` |
| **Routing Worker** | Weighs schedule slack against added transit and expected delay, then writes the booking change | `LIVE` |
| **Comms Worker** | Drafts the carrier and customer emails and files them against the booking. Sends nothing | `LIVE` |
| **Planner Worker** | Sweeps the forward book before departure — exposure, the last cheap moment, and the rebooking or hedge it implies, each ending act-now / tripwire / stand-down | `SCRIPTED` |
| **TMS Link** | The system of record: bookings in, and every Worker's action back out | `DEMO CONNECTOR` |

`LIVE` means the Worker genuinely runs on every run's input, and every output says whether
the model, a rule or a learned lesson decided it. The two `SCRIPTED` Workers replay
authored data and say so on screen. The desk's Workers also show a per-booking panel on the
disruption board; that panel is authored content, and the dashboard labels it so. The TMS
Link is neither: its write-backs are derived from the decisions that run actually made, and
what makes it a demo is the far end, so it carries its own tag.

**Nothing leaves the app, and that includes the workflow layer.** A drafted reply, a drafted
quote, a new booking and a change queued into the TMS all sit behind the same approval gate
as the carrier and customer emails, because they are all outbound actions.
`tests/test_comms_agent_sends_nothing.py` and `tests/test_the_desk_works_and_learns.py`
check every one of them, and the first separately parses every file in `src/` to prove no
transport library exists to send them with.
**The tag is the honesty.**

## Four disruptions, one shipment pool

The seven shipments never change; the active risk event does. That is the point — the
same board reacting differently is what shows the system generalises rather than
performing one trick.

| Scenario | What breaks | The decision it forces |
|---|---|---|
| **Hamburg strike** | A port | Reroute the ones with slack, hold the tight cold-chain one |
| **Red Sea closure** | A chokepoint | The whole board weighs the Cape against waiting |
| **Rhine low water** | An inland waterway | A **mode switch** — barge to rail — not a port change |
| **France wildfire** | A land corridor | Ready and switchable-on; off by default |

![The dashboard after a run](docs/dashboard.png)

*Captured offline — no network and no provider key — so the risk feed falls back to the scripted scenario and every decision is badged `rule`. On the deployed instance the sources are live and the model decides; the layout and the numbers are otherwise exactly what a run produces.*

> **The honest line:** the risk detection is real — it runs against live news right now.
> The shipments are synthetic, so a disruption can be shown on demand instead of waiting
> for one. **Emails are drafted and never sent.**

That distinction is on screen, not buried in a footnote: the risk feed is marked *live*,
the shipment board is marked *synthetic*, and every event says whether it came from a
real source or the scripted scenario.

---

## Run it

Needs Python 3.11+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # then paste a free API key into .env
uvicorn src.app:app --reload
```

Open **http://127.0.0.1:8000** for the landing page, then **Open the demo** —
or go straight to **http://127.0.0.1:8000/app** and press **Inject Hamburg strike**.


| Route | What |
|---|---|
| `/` | Home — the gap, the cost of acting late, the systems it works through, the FAQ |
| `/product` | The sixteen Workers, how they talk and learn, the write-back map, the approval gate |
| `/use-cases` | Six everyday jobs played as the agents handle them, then four disruptions over one board |
| `/about` | What is real here and what is not, and the desk it is modelled on |
| `/whitepaper` | The technical paper |
| `/app` | The dashboard. This is the demo, and the button lives here |
| `/video/<clip>` | The hero reel's clips, same-origin. 404 is fine — the hero renders without them |
| `/api/health` | What a running instance can actually see. First stop when a deploy misbehaves |
| `/api/gauges` | Live Rhine water levels from PEGELONLINE. No page shows them since `/how-it-works` was removed; the endpoint and its tests stay |
| `POST /run` | One cycle: refresh risk, decide, draft, hand the consequences to the desk |
| `GET /api/workflow` | The desk works the inbox once: triage, the work, the playbook checks, the queue |
| `POST /api/workflow/correct` | A person corrects a Worker; the learning loop runs and reports what it fixed |
| `POST /api/workflow/reset` | Forget every lesson — to rehearse the learning loop from scratch |

Each page answers **one** question and says so on itself, in a chip under its
headline. That is deliberate: pages that all try to sell the whole product
are pages nobody finishes.

For the AI key, pick one free provider and put it in `.env`:

| Provider | Where | `.env` |
|---|---|---|
| **Groq** (recommended) | https://console.groq.com | `GROQ_API_KEY=…` (provider defaults to groq) |
| Hugging Face | https://huggingface.co/settings/tokens | `LLM_PROVIDER=hf`, `HF_TOKEN=…` |
| Google Gemini | https://aistudio.google.com/apikey | `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=…` |
| Ollama (local, no key) | https://ollama.com | `LLM_PROVIDER=ollama` |

Hugging Face is worth knowing about for one reason: its router puts several upstream
backends behind a single token, so the rate limit that makes the last drafts of a cycle
fall back to a template becomes a routing choice instead of a wall. It is a sibling to
Groq, not a replacement — and it is a US company too, so it does not change where the
inference happens.

You do **not** set a model name. On Groq and Hugging Face the app asks your key which
models it can actually run and picks the best available one, because providers retire and rename
models and a hard-coded name that has been retired fails with a 404 that looks
exactly like a broken key. To see what your key offers:

```bash
python -m src.llm --models
```

Pin one with `LLM_MODEL` in `.env` only if you want a specific model — and even then,
if it turns out to be unavailable the app falls back to discovery rather than failing.

Without a key it still runs — decisions and emails come from deterministic fallbacks,
and every card that used one is badged `rule` so you can see it.

---

## What happens when you press the button

1. **Seven bookings in transit**, read out of the TMS, all green.
2. **A strike hits the Port of Hamburg.** One click.
3. **It was caught from a German-language source first** — the feed shows the original
   headline (*"Warnstreik im Hamburger Hafen…"*) next to the English one, roughly a day
   before the English wires carried it. Beside it, the family strip shows what else was
   read on the same run: gauges, weather, hazards, filings and rates.
4. **The whole board is triaged in seconds** — two reroute, one holds, four stay green.
   It doesn't cry wolf.
5. **Each decision opens up** into plain-English reasoning, the routes it rejected and
   why, and the full recorded trail of checks behind the call.
6. **The emails are drafted** — one to the carrier, one to the customer. Nothing is sent.
7. **The changes are queued back into the TMS** — the exception on the booking, the new
   discharge port, routing code and ETA, and each draft on the communication log. Nothing is
   written. The bookings left on plan queue nothing at all.

The whole thing runs in well under two minutes.

---

## Working the inbox

Open **Workflow** in the dashboard sidebar (or `g` then `i`). The desk works a synthetic
morning of thirteen mails the moment the view opens:

1. **Every mail is read, linked and routed.** Each row shows which Workers it passed
   through, in order — Inbox → RFQ → Rate → Playbook, say.
2. **Open one to see the conversation.** Every handoff, question, answer, playbook check
   and revision is a numbered message. Open IN-108: the customer asks for a carrier their
   own playbook does not allow, the Playbook Worker sends the booking back, and the Booking
   Worker asks the Rate Worker for an approved one.
3. **What cannot be verified is held, not guessed.** A missing weight holds the booking and
   drafts a question to the customer; a transit out of the EU is escalated, not filed; a
   rollover that breaks the customer's date goes across to the Routing Worker.
4. **Correct a mistake, and watch it learn.** Two are left in on purpose. IN-104 is a
   re-quote the rules read as a booking — pick *Rate request* and press **It is this**. The
   report shows the lesson, that the whole inbox was replayed with it, that IN-109 was
   fixed too, and that every earlier lesson still holds. IN-102's packing list has a weight
   label the Docs Worker has never seen — teach it, and IN-107's bill of lading is checked
   properly as well.
5. **Everything waits in Approvals**, grouped by booking, beside the risk layer's drafts.

Learning here is deliberately modest and checkable: a lesson is a rule plus a line of
context the Worker reads before it works. **No model is retrained.** A lesson that would
undo an earlier correction is refused, and a correction a person made cannot be quietly
undone by the model disagreeing on a later run. Lessons live in one JSON file (gitignored);
**Forget lessons** clears it.

---

## The human-approval gate

Drafts land in **Awaiting approval**, and so does every change queued into the TMS. A person
clicks **Approve** and it moves to **Approved — ready to send** (or **ready to write**).

That is the whole interaction, and it is deliberately the whole interaction. Approval is
a state change: there is no SMTP, no email library and no transport of any kind anywhere
in `src/`, no TMS client and no endpoint, and tests assert it stays that way. Say this out loud in the demo — human
oversight is the responsible design, not a missing feature.

---

## The components

| | | |
|---|---|---|
| **TMS link** | `src/tms.py` | The system of record. Reads the book in, and turns each Worker's action into the booking change it implies — queued, never written. Imports nothing but `json`, `datetime` and the config. |
| **Risk Monitor** | `src/risk_monitor.py` | The news half: 11 GDELT queries and 30 multilingual feeds, plus the six Rhine gauges. An LLM classifies each item for logistics relevance → chokepoint, type, severity. |
| **Signal layer** | `src/signals.py` | The structured half: port weather and sea state (Open-Meteo, Open-Meteo Marine), official weather warnings (DWD), river discharge (GloFAS via Open-Meteo Flood), seismic (USGS and EMSC), natural events and disaster alerts (NASA EONET, GDACS), trade filings (Federal Register), and the ECB's rates (Frankfurter) — with the US NWS, NOAA NHC and the Hong Kong Observatory read as context. Numbers are classified by threshold — no model call, and nothing to hallucinate. |
| **Route Advisor** | `src/route_advisor.py` | Weighs schedule slack against added transit against expected disruption delay. Decides reroute / hold / no-action, and records the trail. |
| **Comms Agent** | `src/comms_agent.py` | Drafts a carrier email and a customer email, in two deliberately different voices. Sends nothing. |
| **Workflow layer** | `src/workflow.py` | The everyday desk: the Inbox, Playbook, Rate, RFQ, Booking, Docs, Milestones, Exception, Invoice and Customs Workers, the message bus they talk over, and the learning loop. Also takes each risk run's decisions and hands them to the desk. |
| **Lessons** | `src/learning.py` | Corrections in, lessons out: a cue phrase and the intent it means, or a document label and the field it fills. Imports nothing but `json`, `re`, `datetime` and the config — no model, no training. |
| **Orchestrator** | `src/orchestrator.py` | The loop, plus `src/app.py` (FastAPI), `static/index.html` (the dashboard) and the five marketing pages under `static/`. |

Each Worker reports what it handled on every run — sources read, shipments triaged,
drafts written, and how many came from the model rather than the deterministic
fallback. Those numbers are counted from the run that just happened. **Nothing on the
dashboard is illustrative**, and there are no traction, accuracy or percentage claims
anywhere: real reasoning on synthetic shipments is the honest pitch.

Each runs on its own, which is how you debug one without the others:

```bash
python -m src.risk_monitor  --inject          # add --no-llm to skip the AI call
python -m src.route_advisor --inject --shipment SHP-002
python -m src.comms_agent   --inject
python -m src.orchestrator  --no-live         # the whole loop, no network
python -m src.workflow                        # the desk works the inbox (--llm, --reset)
```

---

## Deploying to Vercel

The repo is configured for it: `api/index.py` re-exports the same FastAPI app,
and `vercel.json` routes every path to it (`routes`, not `rewrites`, so nothing else in
the checkout is ever served as a file), so `/` and `POST /run` both land on
one function.

1. In Vercel, **Add New → Project** and import this GitHub repo.
2. Framework preset **Other**. Leave build and output settings empty — `vercel.json`
   handles it.
3. Add your AI key under **Settings → Environment Variables**
   (`LLM_PROVIDER` and `GROQ_API_KEY`), then redeploy so it takes effect.

**Check `/api/health` first.** It reports what the running app can actually see —
the path it received, whether the dashboard and data files shipped, and whether a
provider is configured. If something is wrong, it will say so there before you go
hunting.

Serverless changes two things, both handled automatically:

- **The filesystem is read-only.** `risk_state.json` is written to the temp
  directory instead. Nothing is kept between requests, which is fine — this app
  has no database and never did.
- **Functions have a hard timeout.** `maxDuration` is 60s, and on a deployed host
  the live pull is trimmed to 10s and the classifier to 16 items to leave room for
  the LLM calls. Tune with `LIVE_PULL_BUDGET_SECONDS` and `MAX_ITEMS_TO_CLASSIFY`
  if a run gets cut off.

> **A demo you are presenting should run locally.** A full cycle makes up to a
> dozen sequential model calls, and on a cold serverless function that can bump the
> 60-second ceiling. Locally there is no ceiling and no cold start. Deploy for
> sharing a link; run `uvicorn` for the room.

---

## Built to survive a live audience

- **A dead source is skipped, not fatal.** Each one is read in its own function and its
  failure is recorded and shown.
- **A slow source cannot stall the demo.** The whole live pull has a hard 25-second
  budget shared across every family, and the families are read concurrently — 60 sources
  cost about what the slowest one costs. Whatever isn't read by then is skipped and the
  cycle moves on.
- **No source is load-bearing.** That is what makes breadth safe: any one of the 60 can
  be down, slow or reshaped without the cycle failing, and a test holds it.
- **No provider, no problem.** Decisions and drafts fall back to deterministic logic,
  clearly badged.
- **The page is self-contained.** No CDN, no external font, no request beyond its own
  API — flaky wifi can't blank it.
- **A failed run shows a sentence, not a stack trace.**

---

## Before you present it

The demo runs itself; these are the things only a person can check.

1. **Open the risk feed and read the source line** — "N of 60 sources read", and the
   family strip under it. If the news family is at 0, the live news pull is not working
   and the `LIVE` chip is overclaiming. `python -m src.risk_monitor` says which sources
   failed and why, family by family; `python -m src.signals` does the structured half
   on its own.
2. **Open all three actioned cards**, not just one. SHP-001 and SHP-005 reroute;
   SHP-002 holds. They take different branches and read differently.
3. **Check the decision-engine strip** at the top of the board — it names the model
   actually running and how many decisions and drafts came from it rather than the
   rules. A `rule` or `template` badge on a card means the model did not do that one,
   and the reason prints underneath.
4. **Read SHP-002's customer email aloud.** It is the centrepiece: no good option,
   here is the least-bad one. If you would not send it as written, the prompts in
   `comms_agent.py` are what to change.
5. **Run it from `uvicorn` locally**, not the deployed link. A cold serverless
   function plus about fourteen model calls sits close to the 60-second ceiling.

---

## What this is not

No real route optimisation (routes are pre-authored candidates the agent *chooses among*
and justifies). No sending. **No live TMS connection** — working through the TMS is the
design and both directions are modelled, but the far end is absent: no vendor, no
credential, no endpoint, and nothing is ever written. **No mailbox connected** — the desk
works a synthetic inbox. **No retraining** — learning is lessons you can read and delete. No scheduler. No database. No paid
data. The "AI Worker" framing on the header is cosmetic.

It is a learning artifact and a demo — not a live product. The gap between this and a
business is the integration, trust and liability wall, which is real work for later.

---

## Tests

```bash
python -m unittest discover -s tests
```

No test framework to install — `unittest` from the standard library, plus the
`requests` the app already depends on. Twelve files, each holding up a claim the demo makes
out loud. Seven of them are described below; the rest cover the Rhine gauges, the Planner,
the ML layer, pricing a reroute, and the provider staying swappable. A claim nobody checks is a claim that has already stopped being true.

`tests/test_comms_agent_sends_nothing.py` — **the Comms Agent drafts emails and never
sends them.** It parses every file in `src/` and fails, naming the file and line, if a
transport library is ever imported — including through `__import__` or `importlib`. Then
it runs a full offline cycle and checks that every draft it produced carries
`DRAFT - not sent` and starts behind the approval gate.

`tests/test_tms_is_the_system_of_record.py` — **the Workers work through the TMS.** It
fails if anything except the connector opens the shipments file, so there stays exactly
one door to the book. Then it runs a cycle and checks that all three live Workers wrote
something back, that every actioned booking has a write-back and every on-plan booking has
none, and that every one of them is `QUEUED - not written` behind the approval gate.

`tests/test_signals_read_wide_and_fail_soft.py` — **breadth without fragility.** It checks
that a structured event matches the scripted schema key for key, that a reading far from
every corridor is dropped rather than attached to a lane, that a `context` source never
emits an event, and that a source which is down or has reshaped its response fails alone
while the rest still read.

`tests/test_the_pages_keep_their_promises.py` — **the pages say what they should and
nothing they should not.** No language is named on any marketing page or the dashboard (the
edge is source proximity, and the whitepaper is the stated exception because it names
where models come from); no period-over-period delta appears anywhere, because there is no
history to compute one from; no reference product's Worker name appears, in copy or in a
comment; and nothing loads or fetches from another host.

`tests/test_the_desk_works_and_learns.py` — **the everyday desk works, talks and learns
safely.** Every mail is routed or escalated, never guessed; every question one Worker asks
another is answered on the bus; the Playbook Worker's carrier fix happens where anyone can
read it; every output is gated. Then the loop: one correction fixes every mail like it, a
lesson that would undo an earlier one is refused and not saved, the model cannot undo a
correction, and `learning.py` imports nothing that could train a model. The transcript on
`/product` and the handoff counts on `/use-cases` are held to what a run really produces.

`tests/test_the_simulation_holds_together.py` — **the authored week makes sense as a
week.** No booking is ever offered the route it just left, yesterday's reroute is still in
place this morning, and a held booking pays a day for every day it waits.

`tests/test_a_slow_source_cannot_stall_the_demo.py` — **a slow feed cannot hang a
demo.** Against real sockets: a source that hangs and a source that trickles one byte at a
time are both cut off, and a run whose every source trickles still ends inside its budget
with the scenario intact.

None of these is a "no networking" rule. The app makes real HTTP calls on purpose — all 60
sources and the LLM provider — and the live pull is the credibility anchor. What must not
exist is a way to send a *message*. So `requests` is fine and `smtplib` is not.

## Where things are

```
data/     the screenplay - chokepoints, routes, 7 bookings, four scenarios,
          a synthetic morning of inbound mail, and each customer's playbook
src/      the components + llm.py (the only door to the AI provider) + config.py
          risk_monitor.py reads the prose, signals.py reads the instruments,
          httpget.py is the capped GET both of them share,
          tms.py is the only door to the book of bookings,
          workflow.py is the everyday desk, learning.py what it was taught
static/   landing.html - home  ·  product.html
          use-cases.html  ·  about.html  ·  whitepaper.html
          index.html - the dashboard
          fonts/ - Geist Sans + Mono, self-hosted (no CDN, ever)
          video/ - the hero reel's clips; the .mp4s are gitignored,
                   and the page renders fine without them
tests/    the guards: nothing is ever sent, and every action goes through the TMS
*.md      the planning docs; CLAUDE.md is the working summary
```

`.env`, `risk_state.json` and `lessons.json` are gitignored. **Never commit `.env`.**
