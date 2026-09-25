"""ask.py - ask SQRlane a question, and the Worker who owns it answers.

The desk already talks: every Worker hands work to another as a message on one
bus (src/workflow.py). This puts a person on that bus. A question comes in, the
Assistant decides which Worker owns it, that Worker checks with the others it
needs - the TMS Link for the record, the Routing Worker for the decision, the
Risk Worker for what the lane is exposed to - and answers. Every one of those
exchanges is returned, so the answer can be audited and not just read.

Three rules, the same ones the rest of the product keeps:

  * **Answers come from the run, never from the model.** Each answer is
    assembled from a fresh run of the board the person is looking at - the
    bookings read through the TMS link, the decisions the Route Advisor made,
    the drafts, the queued write-backs, the desk's inbox. A model, when one is
    configured, only helps decide *who* owns the question; dates, prices and
    decisions never go through it.
  * **A question nobody owns is said to be nobody's.** If no Worker can answer,
    the Assistant says so, says why, and suggests what can be done - who to ask,
    what to connect, how to rephrase. It never produces a plausible answer from
    nowhere.
  * **Asking changes nothing.** Nothing here drafts, queues or writes. A person
    asking "tell the customer" gets the draft the Comms Worker already has
    waiting at the gate, not a new mail sent.
"""

import re
from datetime import datetime, timezone
from types import SimpleNamespace

from src import config, llm, orchestrator, roster, route_advisor, tms, uploads, workflow

NAMES = dict(workflow.NAMES, assistant="Assistant", tms="TMS Link", you="You")
MODE = {w["id"]: w["mode"] for w in roster.ROSTER}
MODE.update(risk="live", routing="live", comms="live", assistant="live")

# What each Worker owns, as the cue phrases a question uses. Scored, not first-
# match: "why was SHP-001 rerouted" carries a status cue (SHP-001) and a
# decision cue (why, rerouted), and the decision is what was asked.
TOPICS = [
    ("routing", 3, ["why", "reroute", "rerouted", "divert", "hold", "held", "decision",
                    "decide", "decided", "alternative", "option", "instead", "switch"]),
    ("milestones", 2, ["where is", "where's", "status", "eta", "arrive", "arrival",
                       "when will", "when does", "track", "on time", "late", "delayed"]),
    ("risk", 2, ["risk", "disruption", "strike", "storm", "weather", "closure", "closed",
                 "congestion", "news", "event", "canal", "water level", "low water",
                 "alert", "threat", "sources", "what is happening", "what's happening"]),
    ("comms", 3, ["email", "e-mail", "draft", "tell the customer", "tell the carrier",
                  "notify", "write to", "inform", "message to", "what did we send"]),
    ("tms", 3, ["approve", "approval", "pending", "queue", "queued", "write-back",
                "writeback", "write back", "tms", "system of record", "waiting for me",
                "connected", "connection"]),
    ("rate", 3, ["rate", "price", "quote", "how much", "pricing", "cost to ship",
                 "cheapest", "per container"]),
    ("inbox", 2, ["inbox", "mails today", "emails today", "incoming", "which mail",
                  "this morning"]),
    ("playbook", 4, ["playbook", "rules", "standing instruction", "sop", "instructions",
                     "approved carrier", "allowed carrier", "customer rule"]),
    ("docs", 3, ["document", "b/l", "bill of lading", "packing list", "paperwork",
                 "gross weight", "hs code"]),
    ("booking", 2, ["booking request", "new booking", "amend", "amendment", "book "]),
    ("exception", 3, ["exception", "rolled", "rollover", "escalat", "mismatch",
                      "what needs a person", "problem"]),
    ("invoice", 3, ["invoice", "surcharge", "billing", "billed", "overcharge", "dispute"]),
    ("customs", 3, ["customs", "entry", "eori", "clearance", "duty", "declaration",
                    "country of entry"]),
    ("planner", 3, ["forward book", "pre-departure", "before departure", "not yet shipped",
                    "unshipped", "upcoming bookings"]),
]

EXAMPLES = ["Where is SHP-002?", "Why was SHP-001 rerouted?", "What is happening in Hamburg?",
            "What is waiting for my approval?", "Price 2 x 40HC Shanghai to Rotterdam",
            "Which invoices are disputed?", "What are Nordmed Pharma's rules?"]

ROUTER_SYSTEM = """You route a freight forwarder's question to the one Worker who owns it.
Workers: {workers}
Reply with JSON only: {{"worker": "<id>", "reason": "one short sentence"}}.
Use "none" when no Worker's job covers the question."""


class Conversation:
    """The exchanges behind one answer, in order - the same shape as the desk's bus."""

    def __init__(self):
        self.messages: list[dict] = []

    def post(self, frm, to, kind, text, why=None):
        msg = {"seq": len(self.messages) + 1, "from": NAMES.get(frm, frm), "from_id": frm,
               "to": NAMES.get(to, to), "to_id": to, "kind": kind, "text": text}
        if why:
            msg["why"] = why
        self.messages.append(msg)
        return msg

    def ask(self, frm, to, question, answer, why=None):
        self.post(frm, to, "query", question)
        self.post(to, frm, "reply", answer, why=why)
        return answer


# ---------------------------------------------------------------------------
# Reading the question
# ---------------------------------------------------------------------------


def _norm(text):
    return " " + re.sub(r"\s+", " ", (text or "").lower()) + " "


def _board_matches(question, cards) -> list[dict]:
    """Bookings the question names - by id, carrier reference, container or customer."""
    q = _norm(question)
    found = []
    for card in cards:
        keys = [card["id"], card.get("booking_ref")]
        customer = (card.get("customer") or "").lower()
        hit = any(k and re.search(rf"(?<![\w-]){re.escape(k.lower())}(?![\w-])", q) for k in keys)
        if not hit and customer:
            words = [w for w in re.findall(r"[a-zäöüé]+", customer)
                     if len(w) >= 5 and w not in ("gmbh", "logistik", "direct", "group")]
            hit = bool(words) and words[0] in q
        if hit:
            found.append(card)
    return found


def _chokepoints(question) -> list[dict]:
    q = _norm(question)
    out = []
    for cp in route_advisor._load_json(config.CHOKEPOINTS_FILE)["chokepoints"]:
        names = [cp["name"], cp.get("short_name", "")] + cp.get("keywords", [])
        names = [n.lower().removeprefix("the ") for n in names if n and len(n) > 3]
        if any(f" {n}" in q or f"{n} " in q for n in names) or re.search(rf"\b{cp['id']}\b", question):
            out.append(cp)
    return out


def _unwatched_places(question, cards, chokepoints) -> list[str]:
    """A place the question asks about that no source on the board watches.

    "What is the weather in Paris?" must not be answered with Hamburg's strike:
    the Risk Worker says what it watches instead.
    """
    if chokepoints:
        return []
    known = {w.lower() for c in cards for w in re.findall(r"[A-Za-z]+",
             f"{c['origin']} {c['final_destination']} {c.get('customer') or ''}")}
    places = re.findall(r"\b(?:in|at|near|around|over|for)\s+([A-Z][a-zA-Z-]{2,})", question)
    return [p for p in places if p.lower() not in known and not re.match(r"[A-Z]{2,5}-\d", p)]


def _unknown_refs(question, cards) -> list[str]:
    """Things shaped like a booking reference that are not in the book."""
    known = {c["id"].lower() for c in cards} | {(c.get("booking_ref") or "").lower() for c in cards}
    refs = re.findall(r"\b[A-Za-z]{2,5}-\d{3,}\b", question)
    return [r for r in refs if r.lower() not in known and not re.match(r"(?i)in-\d+", r)]


def _rules_route(question) -> tuple[str | None, str]:
    q = _norm(question)
    scores = {}
    freight = bool(workflow._equipment(question)[0]) or bool(
        re.search(r"\b[A-Za-z]{2,5}-\d{3,}\b", question))
    for worker, weight, cues in TOPICS:
        # "book" alone is ordinary English ("book me a table"); it is a booking
        # only with freight in the question - a container count or a reference.
        hits = [c for c in cues if c in q and (c != "book " or freight)]
        if hits:
            scores[worker] = (len(hits) * weight, hits)
    if not scores:
        return None, "no Worker's cue phrases appear in the question"
    worker = max(scores, key=lambda w: scores[w][0])
    return worker, f"strongest cues: {', '.join(scores[worker][1][:3])}"


def _model_route(question) -> tuple[str | None, str] | None:
    workers = "; ".join(f"{w['id']}: {w['role']}" for w in orchestrator.WORKERS + roster.ROSTER
                        if w["id"] != "assistant")
    try:
        reply = llm.complete_json(question, system=ROUTER_SYSTEM.format(workers=workers),
                                  max_tokens=120)
    except llm.LLMError:
        return None
    worker = (reply or {}).get("worker") if isinstance(reply, dict) else None
    if worker == "none":
        return None, str(reply.get("reason") or "no Worker owns it")[:160]
    if worker in NAMES and worker not in ("you", "assistant", "person"):
        return worker, str(reply.get("reason") or "")[:160]
    return None


# ---------------------------------------------------------------------------
# The Workers' answers
# ---------------------------------------------------------------------------


def _days(n):
    return f"{n} day" if abs(n) == 1 else f"{n} days"


def _outlet(event):
    return (event.get("source") or "a source").split(" (")[0]


def _record_line(card):
    return (f"{card['id']}: {card['cargo']}, {card['origin']} to {card['final_destination']}, "
            f"{card.get('carrier') or 'carrier not stated'} {card.get('booking_ref') or ''}".strip()
            + f". Booked ETA {card['eta']}"
            + (f", required by {card['required_by']} ({_days(card['slack_days'])} slack)"
               if card.get("required_by") else "")
            + f". Read from {card.get('source_system') or tms.connector_name()}.")


def _decision_line(card):
    d = card.get("decision") or {}
    if not d or d.get("decision") == "no-action":
        return f"{card['id']} is on plan: {d.get('headline') or 'nothing active touches its route'}."
    verb = {"reroute": "rerouted", "hold": "held"}[d["decision"]]
    line = f"{card['id']} is {verb}: {d['headline']}."
    if d.get("revised_eta"):
        line += f" Revised ETA {d['revised_eta']}, {_days(d.get('delay_days') or 0)} later than booked"
        line += ", past the required-by date." if d.get("deadline_breached") else "."
    return line


def _events_on(card, run):
    ids = set((card.get("decision") or {}).get("triggering_events") or [])
    return [e for e in run["risk"]["events"] if e["event_id"] in ids]


def _answer(text, *, facts=None, links=None, suggestions=None, answered=True):
    return {"text": text, "facts": facts or [], "links": links or [],
            "suggestions": suggestions or [], "answered": answered}


def _milestones(conv, ctx):
    cards = ctx["found"]
    if not cards:
        run = ctx["run"]
        moved = [c for c in run["shipments"] if c["state"] != "green"]
        conv.ask("milestones", "tms", "How many bookings are on the board?",
                 f"{len(run['shipments'])} bookings read from {tms.connector_name()}.")
        text = (f"{len(run['shipments'])} bookings on the board. "
                + (f"{len(moved)} off plan: " + "; ".join(_decision_line(c) for c in moved)
                   if moved else "All of them are on plan."))
        return _answer(text, links=[{"label": c["id"], "view": "shipments", "id": c["id"]}
                                    for c in moved])
    parts, facts = [], []
    for card in cards:
        conv.ask("milestones", "tms", f"Read {card['id']} from the book.", _record_line(card),
                 why="The booking's own record is the starting point: ETA and required-by "
                     "are read, never assumed.")
        said = conv.ask("milestones", "routing", f"Is {card['id']} on plan?", _decision_line(card))
        events = _events_on(card, ctx["run"])
        if events:
            conv.ask("milestones", "risk", f"What is {card['id']}'s route exposed to?",
                     "; ".join(f"{e['title']} ({e['severity']}, first seen via {_outlet(e)})"
                               for e in events))
        parts.append(f"{card['id']} ({card['cargo']}, {card['origin']} to "
                     f"{card['final_destination']}) is booked to arrive {card['eta']}"
                     f" on {card.get('route_description') or card.get('route_id')}. {said}")
        facts += [{"label": f"{card['id']} ETA", "value": card["eta"]},
                  {"label": "Required by", "value": card.get("required_by") or "not on the record"},
                  {"label": "State", "value": card["state"]}]
    return _answer(" ".join(parts), facts=facts,
                   links=[{"label": c["id"], "view": "shipments", "id": c["id"]} for c in cards])


def _routing(conv, ctx):
    run, cards = ctx["run"], ctx["found"]
    if not cards:
        tally = run["summary"]
        by = {k: [c["id"] for c in run["shipments"] if (c.get("decision") or {}).get("decision") == k]
              for k in ("reroute", "hold")}
        if not by["reroute"] and not by["hold"]:
            return _answer("Nothing is rerouted or held: no active disruption touches a route "
                           "on the board, so every booking stays on plan.")
        text = (f"{tally['reroute']} rerouted ({', '.join(by['reroute']) or 'none'}), "
                f"{tally['hold']} held ({', '.join(by['hold']) or 'none'}), "
                f"{tally['no-action']} on plan. A reroute wins when an alternate lands sooner "
                f"than waiting and its extra cost is worth it; a hold wins when every alternate "
                f"is worse than the disruption itself.")
        return _answer(text, links=[{"label": i, "view": "shipments", "id": i}
                                    for i in by["reroute"] + by["hold"]])
    parts = []
    for card in cards:
        d = card.get("decision") or {}
        events = _events_on(card, run)
        if events:
            conv.ask("routing", "risk", f"What made you flag {card['id']}'s route?",
                     "; ".join(f"{e['title']} - expected delay "
                               f"{'-'.join(str(x) for x in (e.get('expected_delay_days') or []))} days"
                               for e in events))
        drafts = card.get("drafts") or []
        if drafts:
            conv.ask("routing", "comms", f"Has {card['id']} been drafted to anyone?",
                     f"{len(drafts)} drafts, all waiting at the gate: "
                     + ", ".join(f"{x['audience']} to {x['to']}" for x in drafts) + ".")
        reasoning = d.get("reasoning") or "Nothing active touches its route, so there was nothing to weigh."
        parts.append(f"{_decision_line(card)} {reasoning}")
    return _answer(" ".join(parts), facts=[
        {"label": f"{c['id']} decided by", "value": (c.get("decision") or {}).get("decided_by", "-")}
        for c in cards], links=[{"label": c["id"], "view": "shipments", "id": c["id"]} for c in cards])


def _risk(conv, ctx):
    run = ctx["run"]
    events = run["risk"]["events"]
    cps = ctx["chokepoints"]
    if ctx["unwatched"]:
        watched = ", ".join(cp["short_name"].removeprefix("the ") for cp in
                            route_advisor._load_json(config.CHOKEPOINTS_FILE)["chokepoints"])
        conv.post("risk", "assistant", "reply",
                  f"I do not watch {', '.join(ctx['unwatched'])}. I watch the board's lanes: "
                  f"{watched}.", why="A place off every lane on the board moves no booking, "
                  "so no source is pointed at it.")
        return _answer(f"No Worker watches {', '.join(ctx['unwatched'])}: it is not on any lane "
                       f"the board's bookings travel. The Risk Worker watches {watched}.",
                       answered=False,
                       suggestions=["Ask about a port or chokepoint on the board, e.g. "
                                    "\"What is happening in Rotterdam?\"",
                                    "If that place matters to your lanes, it is a new source to "
                                    "add - one function in src/signals.py or a feed in config."])
    if cps:
        ids = {c["id"] for c in cps}
        events = [e for e in events if e.get("chokepoint") in ids]
    if not events:
        where = " or ".join(c["name"] for c in cps) if cps else "the board's lanes"
        if run.get("scenario"):
            return _answer(f"No active disruption on {where} in this run - the "
                           f"{run['scenario']['name']} scenario does not touch it.")
        return _answer(f"No active disruption on {where}: no scenario is running. Pressing "
                       f"Run reads the live sources and loads one.",
                       suggestions=["Run a scenario from the top bar, then ask again."])
    parts, links = [], []
    for e in events:
        exposed = [c for c in run["shipments"]
                   if e["event_id"] in ((c.get("decision") or {}).get("triggering_events") or [])]
        conv.ask("risk", "routing", f"Which bookings did {e['event_id']} move?",
                 ("; ".join(_decision_line(c) for c in exposed)) or "None - no booking on the "
                 "board passes it.")
        lead = e.get("english_wire_lag_hours")
        parts.append(f"{e['title']} ({e['severity']}, {e.get('type')}), first seen via "
                     f"{_outlet(e)}" + (f", {lead}h before the international wires" if lead else "")
                     + f". It moved {len(exposed)} booking{'' if len(exposed) == 1 else 's'}"
                     + (f": {', '.join(c['id'] for c in exposed)}." if exposed else "."))
        links += [{"label": c["id"], "view": "shipments", "id": c["id"]} for c in exposed]
    return _answer(" ".join(parts), links=links + [{"label": "Risk feed", "view": "risk"}])


def _comms(conv, ctx):
    cards = ctx["found"] or [c for c in ctx["run"]["shipments"] if c.get("drafts")]
    drafts = [(c, d) for c in cards for d in (c.get("drafts") or [])]
    if not drafts:
        who = ", ".join(c["id"] for c in ctx["found"]) or "the board"
        return _answer(f"Nothing is drafted for {who}: it is on plan, so there is nothing a "
                       f"carrier or customer needs to hear.",
                       suggestions=["If you want to send an update anyway, it is a person's "
                                    "mail - SQRlane drafts only when a decision changes a booking."])
    for card in {c["id"]: c for c, _ in drafts}.values():
        conv.ask("comms", "playbook", f"Do the drafts for {card['id']} meet "
                 f"{card.get('customer') or 'the customer'}'s rules?",
                 "Checked against the playbook before filing; any fix is already on the draft.")
    text = "; ".join(f"{c['id']} {d['audience']} mail to {d['to']}: \"{d['subject']}\" "
                     f"- {d['status']}" for c, d in drafts)
    return _answer(f"{len(drafts)} draft{'' if len(drafts) == 1 else 's'}, none sent: {text}. "
                   f"Each one waits for your approval.",
                   links=[{"label": "Approvals", "view": "approvals"}])


def _tms(conv, ctx):
    run, desk = ctx["run"], ctx["desk"]
    link = run["tms"]
    desk_waiting = [o for o in desk["outputs"] if o.get("approval_status") == "awaiting_approval"]
    drafts = sum(len(c.get("drafts") or []) for c in run["shipments"])
    conv.ask("tms", "comms", "How many of your drafts are waiting?",
             f"{drafts} drafts from the disruption run, none sent.")
    conv.ask("tms", "inbox", "What did the desk queue from the inbox?",
             f"{len(desk_waiting)} outputs - replies, quotes and TMS changes - each gated.",
             why=link["honesty"])
    by_booking = {}
    for op in link["writebacks"]:
        by_booking.setdefault(op["booking_ref"], []).append(op["agent"])
    text = (f"{link['connector']} is {link['status']}. {link['queued'] + len(desk_waiting)} items "
            f"wait for your approval: {link['queued']} write-backs from the disruption run"
            + (" (" + "; ".join(f"{b}: {len(a)}" for b, a in by_booking.items()) + ")"
               if by_booking else "")
            + f" and {len(desk_waiting)} from the desk's inbox. {link['honesty']}")
    return _answer(text, facts=[{"label": "Connector", "value": link["connector"]},
                                {"label": "Bookings read", "value": str(link["bookings_read"])},
                                {"label": "Queued", "value": str(link["queued"])}],
                   links=[{"label": "Approvals", "view": "approvals"},
                          {"label": "TMS link", "view": "tms"}])


def _rate(conv, ctx):
    question = ctx["question"]
    origin, city, port = workflow._lane(question)
    count, equipment = workflow._equipment(question)
    equipment, count = equipment or "40HC", count or 1
    if not (origin and port):
        conv.post("rate", "assistant", "reply",
                  "Which lane? The rate sheet prices Shanghai, Ningbo, Shenzhen and Busan into "
                  "Hamburg, Rotterdam, Antwerp and Fos, and on to Munich, Basel and Lyon.")
        return _answer("The Rate Worker needs a lane it prices: an origin (Shanghai, Ningbo, "
                       "Shenzhen, Busan) and a destination (Hamburg, Rotterdam, Antwerp, Fos, "
                       "Munich, Basel, Lyon).", answered=False,
                       suggestions=["Try: Price 2 x 40HC Shanghai to Rotterdam",
                                    "For a lane that is not on the sheet, the RFQ Worker drafts "
                                    "a quote request to the carriers when the mail arrives."])
    sheet = workflow.load_inbox()["rate_sheet"]
    desk = SimpleNamespace(rate_sheet=sheet, routes=route_advisor.load_routes())
    options = workflow._rate_options(desk, port, city, equipment, count)
    lane = f"{origin} to {city or workflow.PORT_NAMES.get(port, port)}"
    if not options:
        conv.post("rate", "assistant", "reply",
                  f"No carrier on the rate sheet serves {lane} for {equipment}.")
        return _answer(f"No carrier on the rate sheet serves {lane} for {equipment}.",
                       answered=False, suggestions=["Ask the carriers for a spot rate - that is "
                                                    "a person's call, the sheet has nothing."])
    best = options[0]
    conv.post("rate", "assistant", "reply",
             f"{len(options)} options; best {best['carrier']} on {best['route_id']}, "
             f"EUR {best['per_container_eur']:,} per {equipment}, {best['transit_days']} days.",
             why="Every carrier on a route into the lane, priced from the rate sheet: Cape "
                 "routings last, then cheapest, then fastest.")
    rows = "; ".join(f"{o['carrier']} via {o['route_id']}: EUR {o['total_eur']:,} "
                     f"({o['transit_days']} days)" for o in options[:4])
    return _answer(f"{count} x {equipment} {lane}: {rows}. Reference rates from the desk's "
                   f"synthetic rate sheet, not market rates - a quote goes out only as a draft "
                   f"you approve.",
                   facts=[{"label": "Best", "value": f"{best['carrier']}, EUR {best['total_eur']:,}"}])


def _desk_items(ctx, owner=None, intent=None):
    items = ctx["desk"]["items"]
    if ctx["mail_ids"]:
        return [i for i in items if i["id"] in ctx["mail_ids"]]
    return [i for i in items if (owner is None or i["owner"] == owner or owner in i["path"])
            and (intent is None or i["intent"] == intent)]


def _item_line(item, desk):
    outs = [o for o in desk["outputs"] if o["item"] == item["id"]]
    esc = item.get("escalations") or []
    line = (f"{item['id']} from {item.get('sender_org')}: {item['intent_label'].lower()}, "
            f"worked by {' -> '.join(NAMES.get(w, w) for w in item['path'])}.")
    if outs:
        line += " " + "; ".join(f"{o['worker']} {o.get('subject') or o.get('action')}"
                                f" ({o.get('status')})" for o in outs[:3]) + "."
    if esc:
        line += " Escalated: " + "; ".join(e["text"].rstrip(".") for e in esc) + "."
    return line


def _desk_worker(worker):
    def handler(conv, ctx):
        desk = ctx["desk"]
        items = _desk_items(ctx, owner=worker)
        if ctx["found"]:
            ids = {c["id"] for c in ctx["found"]} | {c.get("booking_ref") for c in ctx["found"]}
            items = [i for i in items if i.get("linked_booking") in ids]
        # The risk layer hands this Worker work too, on the same booking.
        handed = [m for m in ctx["run"]["workflow_handoffs"]["messages"] if m["to_id"] == worker
                  and (not ctx["found"] or m["item"] in {c["id"] for c in ctx["found"]})]
        for m in handed[:3]:
            conv.post(m["from_id"], worker, "handoff", m["text"], why=m.get("why"))
        if ctx["found"] and not handed and not items:
            ids = ", ".join(c["id"] for c in ctx["found"])
            text = (f"Nothing for the {NAMES[worker]} on {ids} in this run - "
                    f"{_decision_line(ctx['found'][0])}")
            return _answer(text, links=[{"label": c["id"], "view": "shipments", "id": c["id"]}
                                        for c in ctx["found"]])
        if not items and not handed:
            return _answer(f"The {NAMES[worker]} has nothing on the desk right now.",
                           links=[{"label": "Desk", "view": "desk"}])
        parts = [_item_line(i, desk) for i in items[:3]]
        if len(items) > 3:
            parts.append(f"And {len(items) - 3} more on the desk.")
        parts += [f"From the risk layer: {m['text']}" for m in handed[:3]]
        return _answer(" ".join(parts), links=[{"label": i["id"], "view": "desk", "id": i["id"]}
                                               for i in items[:4]])
    return handler


def _booking(conv, ctx):
    """A booking asked for in chat is priced, not opened.

    The Booking Worker opens a booking from the customer's request and its
    documents, because that is where the fields it has to verify come from. A
    line typed here has none of them, so it is answered with the price and the
    way in - never with a booking nobody can stand behind.
    """
    origin, city, port = workflow._lane(ctx["question"])
    if not (origin and port) or ctx["found"] or ctx["mail_ids"]:
        return _desk_worker("booking")(conv, ctx)
    priced = _rate(conv, ctx)
    conv.post("booking", "you", "reply",
              "Nothing booked: a booking is opened from the customer's request and its "
              "documents, where every field I verify comes from.",
              why="A booking goes to the carrier only when every required field was read "
                  "from the documents.")
    return _answer(f"Nothing is booked from a chat line. {priced['text']}",
                   facts=priced["facts"],
                   suggestions=["Forward the customer's booking request, with its documents, "
                                "to the desk: the Booking Worker opens it on the TMS record, "
                                "holds anything it cannot verify, and queues it for your "
                                "approval."])


def _inbox(conv, ctx):
    desk = ctx["desk"]
    if ctx["mail_ids"]:
        items = _desk_items(ctx)
        for item in items:
            conv.ask("inbox", item["owner"] or "inbox", f"Where is {item['id']}?",
                     _item_line(item, desk), why=item.get("reason"))
        return _answer(" ".join(_item_line(i, desk) for i in items),
                       links=[{"label": i["id"], "view": "desk", "id": i["id"]} for i in items])
    stats = desk["stats"]
    return _answer(f"{stats['items']} mails this morning: {stats['routed']} routed to their "
                   f"Worker, {stats['escalations']} escalated to a person, {stats['mails']} "
                   f"replies drafted and {stats['writes']} TMS changes queued - all waiting "
                   f"for approval. The inbox is a synthetic morning; no mailbox is connected.",
                   links=[{"label": "Desk", "view": "desk"}])


def _playbook(conv, ctx):
    books = workflow.load_playbooks()
    books = books.get("customers", books)
    q = _norm(ctx["question"])
    names = [n for n in books if any(w.lower() in q for w in n.split() if len(w) >= 5)]
    names += [c["customer"] for c in ctx["found"] if c.get("customer") in books]
    names = list(dict.fromkeys(names))
    if not names:
        return _answer(f"{len(books)} customers have standing instructions: "
                       + ", ".join(books) + ". Ask for one by name.")
    parts = []
    for name in names:
        rules = "; ".join(f"{r['type'].replace('_', ' ')}: "
                          f"{', '.join(r['value']) if isinstance(r['value'], list) else r['value']}"
                          f" ({r['why']})" for r in books[name])
        parts.append(f"{name}: {rules}.")
    return _answer(" ".join(parts) + " Every output for them is checked against these before "
                   "it reaches the gate.")


def _planner(conv, ctx):
    cards = ctx["run"]["shipments"]
    panel = (cards[0].get("roster") or {}).get("planner") if cards else None
    if not panel:
        return _answer("The Planner has no sweep for this board.")
    return _answer(f"{panel['headline']}. The Planner is scripted - it replays an authored "
                   f"forward book rather than sweeping one live.",
                   facts=[{"label": "Mode", "value": "scripted"}])


HANDLERS = {"milestones": _milestones, "routing": _routing, "risk": _risk, "comms": _comms,
            "tms": _tms, "rate": _rate, "rfq": _rate, "inbox": _inbox, "playbook": _playbook,
            "planner": _planner, "assistant": _inbox,
            "booking": _booking,
            **{w: _desk_worker(w) for w in ("docs", "exception", "invoice", "customs")}}


def _nobody(conv, ctx, reason):
    """No Worker owns it. Say so, and say what can be done."""
    suggestions = []
    missing = ctx["unknown_refs"]
    if missing:
        conv.ask("assistant", "tms", f"Is {', '.join(missing)} in the book?",
                 f"No - {', '.join(missing)} is not among the {len(ctx['run']['shipments'])} "
                 f"bookings read from {tms.connector_name()}.")
        text = (f"{', '.join(missing)} is not in the book the agents are working on "
                f"({tms.connector_name()}). No Worker can answer for a booking it cannot read.")
        suggestions += ["Check the reference - the board's ids are "
                        + ", ".join(c["id"] for c in ctx["run"]["shipments"][:7]) + ".",
                        "If it lives in your own TMS, connect it on the TMS link page and ask again."]
    else:
        conv.post("assistant", "you", "reply",
                  "I asked who owns this and no Worker does.", why=reason)
        text = ("None of the Workers on this desk owns that question, so none of them can "
                "answer it honestly. They cover the bookings on the board, the disruptions on "
                "their lanes, the inbox, rates, documents, invoices, customs and the approvals "
                "queue.")
        suggestions += ["Rephrase it around a booking, a port or a mail - for example: "
                        + "; ".join(EXAMPLES[:3]) + ".",
                        "If it needs someone outside the desk - a carrier, a customer, "
                        "a colleague - it is a person's call. SQRlane can draft the mail once a "
                        "decision exists, but it will not guess an answer."]
    return _answer(text, suggestions=suggestions, answered=False)


# ---------------------------------------------------------------------------
# One question
# ---------------------------------------------------------------------------


def _uploaded(conv, upload, use_llm) -> dict:
    """One dropped-in file, handed to the Worker it belongs to."""
    conv.post("you", "assistant", "ask", f"Uploaded {upload['name']}.")
    if upload["kind"] == "unreadable":
        conv.post("assistant", "docs", "handoff", f"Read {upload['name']}.")
        conv.post("docs", "you", "answer", upload["reason"])
        return _answer(f"{upload['name']}: {upload['reason']}", answered=False,
                       suggestions=["Upload the mail as .eml, or paste the document's text.",
                                    "A bookings export works as CSV or JSON."])
    if upload["kind"] == "export":
        conn = upload["connection"]
        conv.post("assistant", "tms", "handoff", f"{upload['name']} looks like a bookings export.")
        conv.post("tms", "you", "answer",
                  f"Read {conn['rows_read']} rows: {len(conn['bookings'])} on lanes the agents "
                  f"judge, {len(conn['not_covered'])} not covered.",
                  why=f"{len(conn['mapping'])} columns mapped by the names TMS exports use.")
        text = (f"{upload['name']} is a bookings export: {conn['rows_read']} rows read, "
                f"{len(conn['bookings'])} on lanes the agents can judge, "
                f"{len(conn['not_covered'])} not covered"
                + (" (" + "; ".join(f"{n['ref'] or 'row ' + str(n['row'])}: {n['reason']}"
                                    for n in conn["not_covered"][:3]) + ")"
                   if conn["not_covered"] else "")
                + ". Nothing changes until you choose to use it as your TMS.")
        return dict(_answer(text, facts=[{"label": m["column"], "value": m["field"]}
                                         for m in conn["mapping"][:8]],
                            links=[{"label": "TMS link", "view": "tms"}]),
                    connection_preview=conn)
    message = upload["message"]
    worked = workflow.work_mail(message, use_llm=use_llm)
    item = worked["item"]
    for msg in worked["messages"]:
        conv.post(msg["from_id"], msg["to_id"], msg["kind"], msg["text"], why=msg.get("why"))
    outs = worked["outputs"]
    parts = [f"{upload['name']}: the Inbox Worker read it as "
             f"\"{(item.get('intent_label') or 'unclear').lower()}\""
             + (f" from {item['sender_org']}" if item.get("sender_org") else "")
             + (f", linked to {item['linked_booking']}" if item.get("linked_booking") else "")
             + f", and it went {' -> '.join(NAMES.get(w, w) for w in item['path'])}."]
    if item.get("extracted") and item["extracted"].get("fields"):
        fields = item["extracted"]["fields"]
        parts.append("Read from the document: " + ", ".join(
            f"{workflow.FIELDS.get(k, (k,))[0]} {v:,}" if isinstance(v, int)
            else f"{workflow.FIELDS.get(k, (k,))[0]} {v}" for k, v in list(fields.items())[:6]) + ".")
    if outs:
        parts.append("Waiting for your approval: " + "; ".join(
            f"{o['worker']} - {o.get('subject') or o.get('action')} ({o['status']})"
            for o in outs[:4]) + ".")
    if worked["escalations"]:
        parts.append("For a person: " + "; ".join(e["text"].rstrip(".")
                                                   for e in worked["escalations"][:3]) + ".")
    answered = bool(item.get("owner"))
    return dict(_answer(" ".join(parts), answered=answered,
                        suggestions=[] if answered else [
                            "Add what the mail is about to the subject, or correct it on the "
                            "Desk page - one correction teaches the desk every mail like it."]),
                desk_item={"item": item, "outputs": outs})


def ask(question: str, *, scenario: str | None = None, use_llm: bool = True,
        attachments: list[dict] | None = None) -> dict:
    """Answer one question from a fresh run of the board the person is looking at.

    The run is offline and rules-only on purpose: it is the same board, decided
    the same way, in a fraction of a second - fast enough to answer while you
    wait. Pressing Run is what reads the live sources and lets the model decide.
    """
    question = (question or "").strip()[:500]
    run = orchestrator.run_cycle(live=False, inject=bool(scenario), use_llm=False,
                                 scenario=scenario)
    # The inbox is the demo's synthetic morning whichever TMS is connected - no
    # mailbox is - so the desk works it against the demo book it was written for.
    with tms.using(None):
        desk = workflow.run(use_llm=False)
    ctx = {"question": question, "run": run, "desk": desk,
           "found": _board_matches(question, run["shipments"]),
           "chokepoints": _chokepoints(question),
           "mail_ids": [m.upper() for m in re.findall(r"(?i)\bin-\d{3}\b", question)],
           "unknown_refs": _unknown_refs(question, run["shipments"])}
    ctx["unwatched"] = _unwatched_places(question, run["shipments"], ctx["chokepoints"])

    conv = Conversation()
    if attachments:
        results = [_uploaded(conv, uploads.read(a.get("name"), a.get("content"), i), use_llm)
                   for i, a in enumerate(attachments[:3], start=1)]
        answer = {"text": " ".join(r["text"] for r in results),
                  "facts": [f for r in results for f in r["facts"]],
                  "links": [l for r in results for l in r["links"]],
                  "suggestions": [x for r in results for x in r["suggestions"]],
                  "answered": all(r["answered"] for r in results)}
        for extra in ("connection_preview", "desk_item"):
            found = [r[extra] for r in results if extra in r]
            if found:
                answer[extra] = found[0]
        uploaded = answer
        # A question beside a file is answered only if a Worker owns it; "check
        # this please" is about the file, and the file's answer stands.
        if not question or not (_rules_route(question)[0] or _board_matches(
                question, run["shipments"])):
            return dict(answer, question=question, conversation=conv.messages, routed_to=None,
                        routed_by="upload", route_reason="each file goes to the Worker it "
                        "belongs to", asked_at=datetime.now(timezone.utc).replace(
                            microsecond=0).isoformat(), examples=EXAMPLES,
                        checked_against={"connector": run["tms"]["connector"],
                                         "bookings": len(run["shipments"]),
                                         "note": "Uploaded files are worked by the desk; "
                                                 "nothing is sent and nothing is written."})
    else:
        uploaded = None
    conv.post("you", "assistant", "ask", question)

    routed = _model_route(question) if use_llm and llm.is_configured() else None
    routed_by = "model" if routed and routed[0] else "rules"
    worker, reason = routed if routed and routed[0] else _rules_route(question)
    if not worker:
        # Nothing asked for, but something named: a booking means "tell me about
        # it", a mail means "where is it", a port means "what is happening there".
        if ctx["found"]:
            worker, reason = "milestones", "a booking on the board is named"
        elif ctx["mail_ids"]:
            worker, reason = "inbox", "a mail on the desk is named"
        elif ctx["chokepoints"]:
            worker, reason = "risk", "a port or chokepoint the board watches is named"
    if worker and ctx["unknown_refs"] and not ctx["found"] and worker in (
            "milestones", "routing", "comms"):
        worker, reason = None, "the booking named is not in the book"

    if worker:
        conv.post("assistant", worker, "handoff", question, why=f"Routed by {routed_by}: {reason}.")
        answer = HANDLERS[worker](conv, ctx)
        conv.post(worker, "you", "answer", answer["text"])
    else:
        answer = _nobody(conv, ctx, reason)
    if uploaded:
        answer = dict(uploaded, text=f"{uploaded['text']} {answer['text']}",
                      facts=uploaded["facts"] + answer["facts"],
                      links=uploaded["links"] + answer["links"],
                      suggestions=uploaded["suggestions"] + answer["suggestions"])

    return {
        "question": question,
        "asked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "routed_to": ({"id": worker, "name": NAMES[worker], "mode": MODE.get(worker, "live")}
                      if worker else None),
        "routed_by": routed_by,
        "route_reason": reason,
        "conversation": conv.messages,
        **answer,
        "checked_against": {
            "scenario": (run.get("scenario") or {}).get("name"),
            "connector": run["tms"]["connector"],
            "bookings": len(run["shipments"]),
            "note": ("Answered from a fresh rules-only run of this board. Pressing Run reads "
                     "the live sources and lets the model decide."),
        },
        "examples": EXAMPLES,
    }


def main():
    import sys
    question = " ".join(sys.argv[1:]) or "Where is SHP-002?"
    result = ask(question, scenario="hamburg", use_llm=False)
    for msg in result["conversation"]:
        print(f"  {msg['seq']:>2} {msg['from']} -> {msg['to']} [{msg['kind']}]: {msg['text'][:160]}")
    print("\n" + result["text"])
    for s in result["suggestions"]:
        print("  - " + s)


if __name__ == "__main__":
    main()
