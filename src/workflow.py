"""workflow.py - the workflow layer. The everyday desk, run by Workers that talk.

SQRlane has two layers on one TMS:

    the risk layer      something happens in the world -> which bookings does it
                        threaten -> reroute, hold or leave on plan, and why
                        (risk_monitor, route_advisor, comms_agent, orchestrator)
    the workflow layer  something arrives in the inbox -> what is it -> do the
                        work it asks for, on the record it belongs to
                        (this file)

The risk layer runs a few times a month. This one runs on every mail, all day:
rate requests, booking requests, documents, carrier notices, invoices, arrival
notices. It is the part of a forwarder's day that is mostly re-keying.

How it works, in one pass over the inbox:

    Inbox Worker     reads each mail, decides what it is (the model when one is
                     configured, rules otherwise, lessons always), links it to
                     a booking or a customer, and hands it to the Worker that
                     owns it
    the owner        does the work - RFQ prices and quotes, Booking opens the
                     record, Docs extracts and checks, Milestones writes the
                     notice onto the booking, Invoice reconciles, Customs
                     prepares the entry - asking other Workers what it needs
                     to know on the way
    Playbook Worker  checks every output against the customer's standing
                     instructions and sends it back to the Worker that made it
                     until it complies, or flags it for a person
    Exception Worker catches what is off plan and escalates what the desk cannot
                     absorb - including handing a breached booking to the risk
                     layer's Routing Worker

The Workers do not call each other's internals: every handoff, question, answer,
check and revision is a **message** on one bus, recorded in order. The bus is
what the dashboard shows as the conversation behind each mail, so "the agents
talk to each other" is something a person can read rather than take on trust.

Everything they produce is gated exactly like the risk layer's output: a mail is
`DRAFT - not sent`, a record change is `QUEUED - not written` through tms.gate(),
and both wait in the same approval queue. Nothing here can send or write.

**The learning loop** is correct() at the bottom of this file. A person corrects a
Worker; the correction becomes a lesson (src/learning.py); the whole inbox is
replayed with it; the lesson is kept only if it fixes the item it came from and
every earlier lesson still holds. The report says what else it changed - one
correction usually fixes every mail like it.

The mail is synthetic (data/inbox.json), like the bookings. What is done with it
is computed on the run: nothing here is replayed.

Run it on its own:

    python -m src.workflow              # work the inbox, rules only
    python -m src.workflow --llm        # let the Inbox Worker use the model
    python -m src.workflow --reset      # forget every lesson first
"""

import argparse
import json
import re
from datetime import date, datetime, timedelta, timezone

from src import config, learning, llm, roster, route_advisor, tms

NAMES = {w["id"]: w["name"] for w in roster.ROSTER}
NAMES.update({"routing": "Routing Worker", "risk": "Risk Worker", "comms": "Comms Worker",
              "person": "A person"})
MODE = "workflow"

HONESTY = ("The inbox is synthetic - a morning of authored mail, like the bookings. "
           "Everything done with it is computed on this run. Nothing is sent and "
           "nothing is written: every mail is a draft and every record change is "
           "queued, both waiting for a person.")

LEARNING_NOTE = ("Learning means a correction becomes a rule and a line of context the "
                 "Workers read on every later run. No model is retrained. A lesson is "
                 "kept only if it fixes the mail it came from and every earlier lesson "
                 "still holds.")

# ---------------------------------------------------------------------------
# What a mail can be, and who owns each kind
# ---------------------------------------------------------------------------

INTENTS = {
    "rate_request":    {"label": "Rate request",      "owner": "rfq"},
    "booking_request": {"label": "Booking request",   "owner": "booking"},
    "document":        {"label": "Documents",         "owner": "docs"},
    "carrier_notice":  {"label": "Carrier notice",    "owner": "milestones"},
    "status_request":  {"label": "Status request",    "owner": "milestones"},
    "milestone":       {"label": "Milestone",         "owner": "milestones"},
    "invoice":         {"label": "Carrier invoice",   "owner": "invoice"},
    "customs_notice":  {"label": "Arrival notice",    "owner": "customs"},
}

# The rules classifier: phrases counted in the subject (twice) and the body.
# Deliberately simple - it is the fallback when no model is configured, and the
# thing lessons are layered on top of. It gets two mails in the synthetic inbox
# wrong on purpose (they say "booking" more than "quote"), which is what gives
# the learning loop something honest to learn from.
CUES = {
    "rate_request":    ["pricing", "quote", "quotation", "rate", "rates", "price"],
    "booking_request": ["please book", "booking request", "book", "booking"],
    "document":        ["bill of lading", "b/l", "documents", "commercial invoice", "draft"],
    "carrier_notice":  ["rollover", "rolled", "omit", "schedule change", "delay"],
    "status_request":  ["where is", "when it arrives", "status"],
    "milestone":       ["milestone", "departed", "gate-in", "loaded", "discharged"],
    "invoice":         ["invoice"],
    "customs_notice":  ["arrival notice", "customs"],
}

# Phrases a person is likely to mean when they correct a mail to this intent,
# most specific first. Used to suggest the cue a lesson will key on.
HINTS = {
    "rate_request":    ["re-quote", "requote", "quotation", "pricing", "quote", "price", "rates"],
    "booking_request": ["please book", "booking request", "book"],
    "document":        ["bill of lading", "b/l", "packing list", "commercial invoice", "documents"],
    "carrier_notice":  ["rollover", "rolled", "omit", "schedule change", "delay"],
    "status_request":  ["where is", "when it arrives", "status", "eta"],
    "milestone":       ["milestone", "departed", "gate-in", "discharged"],
    "invoice":         ["invoice"],
    "customs_notice":  ["arrival notice", "customs"],
}

# ---------------------------------------------------------------------------
# What the Docs Worker reads
# ---------------------------------------------------------------------------

FIELDS = {
    "shipper":   ("Shipper",      ["shipper"]),
    "consignee": ("Consignee",    ["consignee"]),
    "commodity": ("Commodity",    ["commodity", "goods", "description of goods"]),
    "hs_code":   ("HS code",      ["hs code", "hs", "commodity code"]),
    "incoterm":  ("Incoterm",     ["incoterm", "incoterms", "terms of delivery"]),
    "packages":  ("Packages",     ["packages", "no. of packages"]),
    "gross_kg":  ("Gross weight", ["gross weight", "gross wt", "g.w."]),
    "net_kg":    ("Net weight",   ["net weight", "net wt", "n.w."]),
}
WEIGHT_FIELDS = {"gross_kg", "net_kg"}
REQUIRED_FOR_BOOKING = ["commodity", "hs_code", "incoterm", "packages", "gross_kg"]
# The booking record keys the Docs Worker compares a document against.
BOOKED_KEYS = {"hs_code": "hs", "incoterm": "incoterm", "gross_kg": "gross_kg",
               "packages": "packages"}

# ---------------------------------------------------------------------------
# Lanes
# ---------------------------------------------------------------------------

ORIGINS = ["shanghai", "ningbo", "shenzhen", "busan"]
DEST_PORT = {"hamburg": "HAM", "rotterdam": "RTM", "antwerp": "ANR", "fos-sur-mer": "FOS",
             "fos": "FOS", "munich": "HAM", "basel": "RTM", "lyon": "FOS", "duisburg": "RTM"}
PORT_NAMES = {"HAM": "Hamburg", "RTM": "Rotterdam", "ANR": "Antwerp", "FOS": "Fos-sur-Mer"}
# Final destinations outside the EU customs union. Arriving at an EU port for one
# of these is a transit, not an import - which is exactly the call a Customs
# Worker should not make on its own.
NON_EU = {"basel": "Switzerland"}
EQUIPMENT = re.compile(r"(\d+)\s*x\s*(40\s?hc|40\s?rh|40\s?ft|40'|20\s?ft|flatracks?)\b", re.I)
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}


def _load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_inbox() -> dict:
    return _load(config.INBOX_FILE)


def load_playbooks() -> dict:
    return _load(config.PLAYBOOKS_FILE).get("customers", {})


def _norm(text):
    return learning.normalise(text)


def _count(cue, text):
    return len(learning.cue_pattern(cue).findall(text))


def parse_weight(raw) -> int | None:
    """'14.200 kg', '18,900 kg' and '2480' all read as whole kilograms. A comma or
    a dot followed by exactly three digits is a thousands separator, whichever
    side of the Rhine the document was typed on."""
    match = re.search(r"\d[\d.,]*", str(raw or ""))
    if not match:
        return None
    number = match.group(0).rstrip(".,")
    if re.fullmatch(r"\d{1,3}([.,]\d{3})+", number):
        return int(re.sub(r"[.,]", "", number))
    try:
        return round(float(number.replace(",", ".")))
    except ValueError:
        return None


def _money(raw) -> int | None:
    return parse_weight(raw)   # same separators, same rule


def _eur(amount) -> str:
    return f"EUR {amount:,.0f}"


# ---------------------------------------------------------------------------
# The bus - every handoff, question, answer, check and revision, in order
# ---------------------------------------------------------------------------


class Desk:
    """One run of the desk: the bus, the outputs, and what each Worker touched."""

    def __init__(self, *, bookings, routes, playbooks, rate_sheet, lessons, today):
        self.bookings = bookings
        self.by_ref = {b["booking_ref"]: b for b in bookings}
        self.by_id = {b["id"]: b for b in bookings}
        self.routes = routes
        self.playbooks = playbooks
        self.rate_sheet = rate_sheet
        self.lessons = lessons
        self.today = today
        self.messages: list[dict] = []
        self.queue: list[dict] = []
        self.outputs: list[dict] = []
        self.escalations: list[dict] = []
        self.items: dict[str, dict] = {}
        self.applied: dict[str, set] = {}

    # --- messages ---------------------------------------------------------

    def post(self, frm, to, kind, item, text, *, deliver=False, why=None, **data) -> dict:
        """`why` is the short reason behind the message - the logic the Worker
        applied, in one line - so the conversation can be audited, not just read."""
        msg = {"seq": len(self.messages) + 1, "from": NAMES.get(frm, frm), "from_id": frm,
               "to": NAMES.get(to, to), "to_id": to, "kind": kind, "item": item,
               "text": text}
        if why:
            msg["why"] = why
        if data:
            msg["data"] = data
        self.messages.append(msg)
        for wid in (frm, to):
            path = self.items.get(item, {}).get("path")
            if path is not None and wid in NAMES and wid != "person" and wid not in path:
                path.append(wid)
        if deliver:
            self.queue.append(msg)
        return msg

    def ask(self, frm, to, item, question, answer_fn):
        """A question one Worker puts to another, and the answer, both on the bus."""
        self.post(frm, to, "query", item, question)
        answer, said, *why = answer_fn()
        self.post(to, frm, "reply", item, said, why=why[0] if why else None)
        return answer

    def escalate(self, frm, item, text, *, to="person", why=None, **data):
        self.post(frm, to, "escalate", item, text, why=why, **data)
        entry = {"item": item, "from": NAMES[frm], "to": NAMES.get(to, to), "text": text}
        if why:
            entry["why"] = why
        self.escalations.append(entry)
        self.items[item]["escalations"].append(entry)

    def look(self, item, reason):
        """Mark a mail for a person to look at - the desk is unsure, not wrong."""
        record = self.items[item]
        record["needs_look"] = True
        if reason not in record["look_reasons"]:
            record["look_reasons"].append(reason)

    def lesson_used(self, lesson_id, item):
        self.applied.setdefault(lesson_id, set()).add(item)
        if lesson_id not in self.items[item]["lessons_applied"]:
            self.items[item]["lessons_applied"].append(lesson_id)

    # --- outputs ------------------------------------------------------------

    def emit(self, producer, output) -> dict:
        """File an output: numbered, gated, and checked by the Playbook Worker."""
        item = output["item"]
        n = sum(1 for o in self.outputs if o["item"] == item) + 1
        output = dict(output, id=f"{item}-{n}", worker=NAMES[producer], worker_id=producer)
        if output["kind"] == "mail":
            output.update(status="DRAFT - not sent", approval_status="awaiting_approval",
                          cc=list(output.get("cc") or []))
        else:
            output = tms.gate(dict(output, agent=NAMES[producer]))
        self.outputs.append(output)
        self.items[item]["outputs"].append(output["id"])
        output["checks"] = _playbook_review(self, producer, output)
        return output


# ---------------------------------------------------------------------------
# Inbox Worker - what is this, whose is it, who does it go to
# ---------------------------------------------------------------------------

INBOX_SYSTEM = """You are the Inbox Worker on a freight forwarder's operations desk.
For each inbound mail decide what it is. Choose exactly one intent:
  rate_request     a customer asks for a price, a rate or a re-quote
  booking_request  a customer asks you to book cargo now
  document         shipping documents sent to be checked
  carrier_notice   a carrier reports a rollover, delay or schedule change
  status_request   someone asks where cargo is or when it arrives
  milestone        a routine event notice with no exception
  invoice          a carrier's invoice
  customs_notice   an arrival notice that needs customs clearance
Follow every line under CORRECTIONS exactly - a person made them after checking.
Return {"items": [{"id": "...", "intent": "...", "reason": "one short sentence"}]}."""


def _rules_intent(message) -> tuple[str | None, int, dict]:
    subject = _norm(message["subject"])
    body = _norm(message["body"])
    scores = {intent: sum(2 * _count(c, subject) + _count(c, body) for c in cues)
              for intent, cues in CUES.items()}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top, best = ranked[0]
    margin = best - ranked[1][1]
    return (top if best else None), margin, scores


def _model_intents(messages, lessons) -> tuple[dict, str | None]:
    """One call for the whole inbox. Returns ({id: (intent, reason)}, failure)."""
    corrections = learning.context_for("Inbox Worker", lessons)
    prompt = ("CORRECTIONS:\n" + ("\n".join(f"- {c}" for c in corrections) or "- none yet")
              + "\n\nMAIL:\n" + "\n\n".join(
                  f"[{m['id']}] from {m['sender_org']}\nSubject: {m['subject']}\n"
                  f"{m['body'][:600]}" for m in messages))
    try:
        reply = llm.complete_json(prompt, system=INBOX_SYSTEM, max_tokens=1600)
    except llm.LLMError as exc:
        return {}, f"{type(exc).__name__}: {exc}"[:200]
    rows = reply.get("items") if isinstance(reply, dict) else reply
    out = {}
    for row in rows or []:
        if isinstance(row, dict) and row.get("intent") in INTENTS and row.get("id"):
            out[row["id"]] = (row["intent"], str(row.get("reason") or "")[:200])
    return out, None


def _link(desk, message) -> tuple[dict | None, str | None]:
    text = f"{message['subject']} {message['body']}"
    for ref in re.findall(r"\b[A-Z]{4}-\d{6,8}\b", text):
        if ref in desk.by_ref:
            booking = desk.by_ref[ref]
            return booking, booking["customer"]
    for sid in re.findall(r"\bSHP-\d{3}\b", text):
        if sid in desk.by_id:
            return desk.by_id[sid], desk.by_id[sid]["customer"]
    org = message.get("sender_org")
    known = any(b["customer"] == org for b in desk.bookings) or org in desk.playbooks
    return None, (org if known else None)


def _triage(desk, messages, use_llm) -> dict:
    """Classify, link and route every mail. Returns the mode actually used."""
    modelled, failure = ({}, None)
    if use_llm and llm.is_configured():
        modelled, failure = _model_intents(messages, desk.lessons)
    elif use_llm:
        failure = "no AI provider configured"

    for message in messages:
        item = desk.items[message["id"]]
        rules_intent, margin, scores = _rules_intent(message)
        if message["id"] in modelled:
            intent, reason = modelled[message["id"]]
            decided_by = "model"
            if rules_intent and rules_intent != intent:
                item["second_opinion"] = (f"rules read it as "
                                          f"{INTENTS[rules_intent]['label'].lower()}")
        else:
            intent, decided_by = rules_intent, "rules"
            reason = (f"strongest cues: {INTENTS[intent]['label'].lower()} "
                      f"({scores[intent]} vs next {scores[intent] - margin})"
                      if intent else "no known cue in the subject or body")
            if intent and margin <= 1:
                desk.look(message["id"], "close call between two intents")

        # Lessons last, and they win. A correction a person made is applied after
        # the model or the rules have answered, so it cannot be quietly undone by
        # either of them disagreeing on a later run.
        text = _norm(message["subject"] + " " + message["body"])
        for lesson in learning.intent_overrides(desk.lessons):
            if learning.cue_pattern(lesson["cue"]).search(text):
                desk.lesson_used(lesson["id"], message["id"])
                if intent != lesson["right"]:
                    intent, decided_by = lesson["right"], "lesson"
                    reason = f"{lesson['id']}: {lesson['learned']}"
                break

        booking, customer = _link(desk, message)
        item.update(intent=intent, decided_by=decided_by, reason=reason,
                    intent_label=INTENTS[intent]["label"] if intent else "Unclear",
                    linked_booking=booking["id"] if booking else None,
                    customer=customer or message.get("sender_org"),
                    known_customer=bool(customer))
        if decided_by == "model" and item.get("second_opinion"):
            desk.look(message["id"], f"model and rules disagree - {item['second_opinion']}")

        if not intent:
            desk.escalate("inbox", message["id"], "Could not tell what this mail is - "
                          "left for a person rather than guessed.")
            continue
        owner = INTENTS[intent]["owner"]
        item["owner"] = owner
        link = (f" Linked to {booking['id']} ({booking['booking_ref']})." if booking
                else f" Customer: {customer}." if customer else " New sender - no booking linked.")
        by = {"rules": "By rules", "model": "By the model", "lesson": "By a lesson"}[decided_by]
        desk.post("inbox", owner, "handoff", message["id"],
                  f"{INTENTS[intent]['label']} from {message['sender_org']}.{link}",
                  deliver=True, why=f"{by} - {reason.rstrip('.')}. Routed to the "
                                    f"{NAMES[owner]}.")
    return {"classifier": "model" if modelled else "rules", "failure": failure}


# ---------------------------------------------------------------------------
# Docs Worker - fields out of paper, checked against the booking
# ---------------------------------------------------------------------------


def extract(text, lessons) -> dict:
    """Read 'Label: value' lines into fields. Labels a lesson taught are read
    exactly like the built-in ones; labels nobody taught are reported, never
    guessed at."""
    learned = learning.field_aliases(lessons)
    fields, sources, unread = {}, {}, []
    for line in (text or "").splitlines():
        if ":" not in line:
            continue
        label, value = (part.strip() for part in line.split(":", 1))
        key, lesson_id = None, None
        norm = _norm(label)
        for field, (_, aliases) in FIELDS.items():
            if norm in aliases:
                key = field
                break
        if key is None and norm in learned:
            key, lesson_id = learned[norm]
        if key is None:
            if value and not norm.startswith(("bill of lading", "packliste", "invoice")):
                unread.append({"label": label, "value": value})
            continue
        if key in fields:
            continue
        fields[key] = parse_weight(value) if key in WEIGHT_FIELDS else value
        sources[key] = {"label": label, "line": line.strip(), "lesson": lesson_id}
    return {"fields": fields, "sources": sources, "unread": unread}


def _extract_all(desk, requester, item_id, message) -> dict:
    """The Docs Worker, asked by another Worker to read the attachments."""
    merged = {"fields": {}, "sources": {}, "unread": [], "documents": []}
    item = desk.items[item_id]

    def answer():
        for attachment in message.get("attachments") or []:
            got = extract(attachment.get("text"), desk.lessons)
            for field, source in got["sources"].items():
                if source["lesson"]:
                    desk.lesson_used(source["lesson"], item_id)
            for key in ("fields", "sources"):
                for field, value in got[key].items():
                    merged[key].setdefault(field, value)
            merged["unread"] += got["unread"]
            merged["documents"].append({"name": attachment["name"],
                                        "kind": attachment.get("kind"),
                                        "fields": got["fields"], "unread": got["unread"]})
        item["extracted"] = merged
        if merged["unread"]:
            desk.look(item_id, "document labels not recognised: " + ", ".join(
                u["label"] for u in merged["unread"]))
        n = len(merged["fields"])
        said = (f"Read {n} field{'' if n == 1 else 's'} from "
                f"{len(merged['documents'])} document(s)")
        if merged["unread"]:
            said += " - labels not recognised: " + ", ".join(
                f"“{u['label']}”" for u in merged["unread"])
        return merged, said + ".", ("Fields read from “Label: value” lines the extractor "
                                    "knows; a label it does not know is reported, never "
                                    "guessed.")

    if requester == "docs":
        return answer()[0]
    return desk.ask(requester, "docs", item_id,
                    f"Read the {len(message.get('attachments') or [])} attachment(s) on "
                    f"{item_id}.", answer)


def _docs(desk, item_id, message, msg):
    item = desk.items[item_id]
    got = _extract_all(desk, "docs", item_id, message)
    booking = desk.by_id.get(item.get("linked_booking"))
    if not booking:
        desk.escalate("docs", item_id, "Documents with no booking to check them against "
                      "- filed for a person to match.")
        return
    booked = roster.booked_docs(booking["id"])
    diffs, unchecked = [], []
    for field, booked_key in BOOKED_KEYS.items():
        expected = booked.get(booked_key)
        if expected is None:
            continue
        if field not in got["fields"]:
            unchecked.append(FIELDS[field][0])
            continue
        found = got["fields"][field]
        same = (parse_weight(expected) == found if field in WEIGHT_FIELDS
                else _norm(str(expected)) == _norm(str(found)))
        if not same:
            diffs.append({"field": field, "label": FIELDS[field][0],
                          "document": found, "booking": expected})
    for label in unchecked:
        desk.look(item_id, f"{label} not read from the document - not checked")

    summary = ("matches the booking" if not diffs and not unchecked else
               f"{len(diffs)} mismatch{'' if len(diffs) == 1 else 'es'}" if diffs else
               f"{', '.join(unchecked).lower()} not read")
    doc_names = ", ".join(d["name"] for d in got["documents"])
    desk.emit("docs", {
        "item": item_id, "kind": "tms", "record": "documents", "operation": "file_document",
        "action": "document", "booking_ref": booking["id"], "customer": booking["customer"],
        "changes": [{"field": "documents", "to": f"{doc_names} - {summary}"}],
        "reason": f"Checked against {booking['id']}'s booking: {summary}.",
    })
    if diffs:
        desk.post("docs", "exception", "handoff", item_id,
                  "Document does not match the booking: " + "; ".join(
                      f"{d['label']} {d['document']:,} vs {d['booking']} booked"
                      if isinstance(d["document"], int) else
                      f"{d['label']} {d['document']} vs {d['booking']} booked" for d in diffs),
                  deliver=True, reason="doc_mismatch", diffs=diffs, booking=booking["id"],
                  why=f"Each field read is compared with {booking['id']}'s booking; a "
                      f"difference is handed on to Exception, never corrected.")


# ---------------------------------------------------------------------------
# Rate and RFQ Workers - a lane priced, a quote drafted
# ---------------------------------------------------------------------------


def _lane(text) -> tuple[str | None, str | None, str | None]:
    """(origin, destination city, destination port) as written in the mail."""
    low = _norm(text)
    origin = next((o for o in ORIGINS if o in low), None)
    after = low.split(origin, 1)[1] if origin else low
    hits = [(after.find(city), city) for city in DEST_PORT if city in after]
    city = min(hits)[1] if hits else None
    return (origin.title() if origin else None, city.title() if city else None,
            DEST_PORT.get(city) if city else None)


def _equipment(text) -> tuple[int | None, str | None]:
    match = EQUIPMENT.search(text or "")
    if not match:
        return None, None
    kind = re.sub(r"\s", "", match.group(2).lower())
    kind = {"40hc": "40HC", "40rh": "40RH", "40ft": "40ft", "40'": "40ft",
            "20ft": "20ft"}.get(kind, "flatrack")
    return int(match.group(1)), kind


def _commodity(text) -> str | None:
    match = re.search(r"\d+\s*x\s*\S+\s+(.*?)\s+from\s", text or "", re.I)
    return match.group(1).strip() if match else None


def _ready(text, today) -> str | None:
    match = re.search(r"(\d+|one|two|three|four|five|six)\s+weeks?", _norm(text))
    if not match:
        return None
    weeks = NUMBER_WORDS.get(match.group(1)) or int(match.group(1))
    return (today + timedelta(weeks=weeks)).isoformat()


def _rate_options(desk, port, city, equipment, count) -> list[dict]:
    sheet = desk.rate_sheet
    base = sheet["base_eur_per_container"] * sheet["equipment_multiplier"].get(equipment, 1.0)
    inland_basel = (city or "").lower() == "basel"
    options = []
    for route_id, route in desk.routes.items():
        if route.get("discharge_port") != port:
            continue
        via_basel = "basel" in (route.get("inland_leg") or "").lower()
        if via_basel != inland_basel:
            continue
        for carrier, index in roster.carriers_for(route_id):
            options.append({
                "route_id": route_id, "carrier": carrier,
                "discharge_port": port, "transit_days": route["transit_days"],
                "via_cape": "COGH" in route_id,
                "cost_index": index,
                "per_container_eur": int(round(base * index / 100, -1)),
                "total_eur": int(round(base * index / 100, -1)) * (count or 1),
            })
    options.sort(key=lambda o: (o["via_cape"], o["total_eur"], o["transit_days"]))
    return options


def _ask_rates(desk, frm, item_id, port, city, equipment, count, carrier_filter=None):
    lane = f"{PORT_NAMES.get(port, port)}{' for ' + city if city and city != PORT_NAMES.get(port) else ''}"

    def answer():
        options = _rate_options(desk, port, city, equipment, count)
        if carrier_filter:
            options = [o for o in options if o["carrier"] in carrier_filter]
        if not options:
            return options, f"No carrier on the rate sheet serves {lane} for {equipment}."
        best = options[0]
        why = (f"Every carrier on a route into {lane}, priced from the rate sheet and "
               f"ranked: Cape routings last, then cheapest, then fastest.")
        if carrier_filter:
            why += f" Only {' or '.join(carrier_filter)}, as the playbook allows."
        return options, (f"{len(options)} option{'' if len(options) == 1 else 's'} into {lane}; "
                         f"best {best['carrier']} on {best['route_id']}, "
                         f"{_eur(best['per_container_eur'])} per {equipment}, "
                         f"{best['transit_days']} days."), why

    ask = f"Price {count or 1} x {equipment} into {lane}"
    if carrier_filter:
        ask += f", only {' or '.join(carrier_filter)}"
    return desk.ask(frm, "rate", item_id, ask + ".", answer)


def _quote_body(p) -> str:
    lines = [f"Dear {p['greeting']},", "",
             f"Thank you for the request. For {p['count']} x {p['equipment']} "
             f"{p['commodity']} from {p['origin']} to {p['destination']}:",
             "",
             f"  {p['carrier']} via {p['port_name']} ({p['route_id']}), about "
             f"{p['transit_days']} days port to port",
             f"  {_eur(p['per_container_eur'])} per container, {_eur(p['total_eur'])} in total",
             "",
             f"This quote is valid for {p['validity_days']} days."]
    if p.get("ready"):
        lines.append(f"We have planned against cargo ready around {p['ready']}.")
    lines += ["", "Happy to firm this up as soon as you confirm.", "", "Kind regards,",
              config.FORWARDER["company"]]
    return "\n".join(lines)


def _sender(message):
    name, _, addr = message["from"].partition("<")
    return name.strip(), addr.rstrip(">").strip() or message["from"]


def _rfq(desk, item_id, message, msg):
    item = desk.items[item_id]
    text = f"{message['subject']}\n{message['body']}"
    origin, city, port = _lane(text)
    count, equipment = _equipment(text)
    customer = item.get("customer")
    current = next((b for b in desk.bookings if b["customer"] == customer), None)
    commodity = _commodity(message["body"]) or (current["cargo"].lower() if current else None)
    parsed = {"origin": origin, "destination": city, "discharge_port": port,
              "equipment": equipment, "count": count, "commodity": commodity,
              "ready": _ready(text, desk.today)}
    item["parsed"] = parsed
    missing = [k for k in ("origin", "destination", "equipment") if not parsed[k]]
    if missing:
        desk.escalate("rfq", item_id, "Could not read the lane or equipment ("
                      + ", ".join(missing) + ") - not guessed.")
        return
    options = _ask_rates(desk, "rfq", item_id, port, city, equipment, count)
    if not options:
        desk.escalate("rfq", item_id, "Nothing on the rate sheet for this lane - a person prices it.")
        return
    best = options[0]
    name, addr = _sender(message)
    params = {"greeting": name, "count": count or 1, "equipment": equipment,
              "commodity": commodity or "cargo", "origin": origin, "destination": city,
              "port_name": PORT_NAMES.get(port, port), "ready": parsed["ready"],
              "validity_days": desk.rate_sheet["quote_validity_days_default"],
              **{k: best[k] for k in ("carrier", "route_id", "transit_days",
                                      "per_container_eur", "total_eur")}}
    quote = desk.emit("rfq", {
        "item": item_id, "kind": "mail", "audience": "customer", "template": "quote",
        "customer": customer, "to": addr, "params": params,
        "validity_days": params["validity_days"],
        "subject": f"Quote: {origin} to {city}, {count or 1} x {equipment}",
        "body": _quote_body(params), "booking_ref": current["id"] if current else None,
        "reason": f"The top-ranked option on the rate sheet: {best['carrier']} on "
                  f"{best['route_id']}, {best['transit_days']} days.",
    })
    desk.emit("rfq", {
        "item": item_id, "kind": "tms", "record": "quotation", "operation": "create_quotation",
        "action": "quotation", "booking_ref": f"Q-{item_id[3:]}", "customer": customer,
        "changes": [{"field": "quotation", "to": f"{origin} - {city}, {count or 1} x {equipment}, "
                     f"{best['carrier']}, {_eur(best['total_eur'])}, "
                     f"valid {quote['validity_days']} days"}],
        "reason": f"Quote drafted for {customer}.",
    })


# ---------------------------------------------------------------------------
# Booking Worker - the record opened from the mail and its documents
# ---------------------------------------------------------------------------


def _booking(desk, item_id, message, msg):
    item = desk.items[item_id]
    text = f"{message['subject']}\n{message['body']}"
    origin, city, port = _lane(text)
    count, equipment = _equipment(text)
    requested = next((c for c in ("MSC", "Maersk", "Hapag-Lloyd", "CMA CGM", "ONE")
                      if re.search(rf"\bwith {re.escape(c)}\b", text)), None)
    got = _extract_all(desk, "booking", item_id, message)
    fields = got["fields"]
    missing = [FIELDS[f][0] for f in REQUIRED_FOR_BOOKING if f not in fields]
    if not (origin and port and equipment):
        desk.escalate("booking", item_id, "Could not read the lane or equipment - not guessed.")
        return
    options = _ask_rates(desk, "booking", item_id, port, city, equipment, count)
    if not options:
        desk.escalate("booking", item_id, "No carrier on the rate sheet for this lane.")
        return
    chosen = next((o for o in options if o["carrier"] == requested), None)
    note = ""
    if requested and not chosen:
        note = f"{requested} was asked for but does not price this lane on the rate sheet. "
        desk.look(item_id, f"{requested} requested, not on the lane - carrier chosen instead")
    chosen = chosen or options[0]
    ref = f"NEW-{item_id[3:]}"
    etd = _ready(text, desk.today)
    customer = item.get("customer")
    status = (f"INCOMPLETE - held: {', '.join(missing).lower()} not found" if missing
              else "NEW - awaiting carrier confirmation")
    record = desk.emit("booking", {
        "item": item_id, "kind": "tms", "record": "booking", "operation": "create_booking",
        "action": "new booking", "booking_ref": ref, "customer": customer,
        "carrier": chosen["carrier"], "options": options,
        "changes": _booking_changes(customer, origin, city, port, chosen, count, equipment,
                                    fields, etd, status),
        "reason": note + (f"Held, not guessed: {', '.join(missing).lower()} could not be read "
                          f"from the documents." if missing else
                          f"Opened from the mail and {len(got['documents'])} document(s)."),
    })
    name, addr = _sender(message)
    if missing:
        desk.escalate("booking", item_id, f"{ref} held: {', '.join(missing).lower()} not "
                      f"found in the documents. Not guessed - asking the customer.",
                      why="A booking goes to the carrier only when every required field "
                          "was read from the documents.")
        desk.emit("booking", {
            "item": item_id, "kind": "mail", "audience": "customer", "customer": customer,
            "to": addr, "booking_ref": ref,
            "subject": f"Your booking request {origin} to {city} - one detail missing",
            "body": (f"Dear {name},\n\nThank you - we have opened booking {ref}. Before we "
                     f"can place it with the carrier we need the "
                     f"{', '.join(missing).lower()}, which we could not find in the "
                     f"documents you sent. Could you confirm it?\n\nKind regards,\n"
                     f"{config.FORWARDER['company']}"),
        })
    else:
        carrier = record["carrier"]
        desk.emit("booking", {
            "item": item_id, "kind": "mail", "audience": "carrier", "customer": customer,
            "to": f"Booking desk, {carrier}", "booking_ref": ref,
            "subject": f"Booking request {ref}: {origin} - {PORT_NAMES.get(port, port)}, "
                       f"{count or 1} x {equipment}",
            "body": (f"Please book {count or 1} x {equipment} {fields.get('commodity', '')} "
                     f"from {origin} to {PORT_NAMES.get(port, port)} on "
                     f"{next(c['to'] for c in record['changes'] if c['field'] == 'routing_code')}, "
                     f"sailing around {etd}.\n"
                     f"HS {fields.get('hs_code')}, gross {fields.get('gross_kg'):,} kg, "
                     f"{fields.get('packages')}, {fields.get('incoterm')}.\n"
                     f"Shipper {fields.get('shipper', 'per documents')}, consignee "
                     f"{fields.get('consignee', customer)}.\n\nPlease confirm with your "
                     f"booking number.\n\n{config.FORWARDER['company']}"),
        })
        desk.emit("booking", {
            "item": item_id, "kind": "mail", "audience": "customer", "customer": customer,
            "to": addr, "booking_ref": ref,
            "subject": f"Booking {ref} received - {origin} to {city}",
            "body": (f"Dear {name},\n\nWe have your booking as {ref}: {count or 1} x "
                     f"{equipment} from {origin} to {city} with {carrier}, sailing around "
                     f"{etd}. We will send the carrier's confirmation as soon as we have "
                     f"it.\n\nKind regards,\n{config.FORWARDER['company']}"),
        })
    # Across the layers: every new booking is one the risk layer should look at
    # before it sails. The Planner is scripted today, so this is recorded as a
    # handoff and not acted on here.
    desk.post("booking", "planner", "handoff", item_id,
              f"{ref} is new on the forward book - for the pre-departure sweep.")


def _booking_changes(customer, origin, city, port, option, count, equipment, fields, etd,
                     status):
    changes = [
        {"field": "customer", "to": customer},
        {"field": "port_of_loading", "to": origin},
        {"field": "port_of_discharge", "to": PORT_NAMES.get(port, port)},
        {"field": "final_destination", "to": city},
        {"field": "routing_code", "to": option["route_id"]},
        {"field": "carrier", "to": option["carrier"]},
        {"field": "equipment", "to": f"{count or 1} x {equipment}"},
        {"field": "etd", "to": etd},
    ]
    for field in ("commodity", "hs_code", "incoterm", "gross_kg"):
        if field in fields:
            value = fields[field]
            changes.append({"field": field, "to": f"{value:,} kg" if field == "gross_kg" else value})
    changes.append({"field": "booking_status", "to": status})
    return changes


# ---------------------------------------------------------------------------
# Milestones Worker - notices onto the booking, and where-is-my-box
# ---------------------------------------------------------------------------


def _milestones(desk, item_id, message, msg):
    item = desk.items[item_id]
    booking = desk.by_id.get(item.get("linked_booking"))
    if not booking:
        desk.escalate("milestones", item_id, "No booking matches the reference in this "
                      "mail - left for a person to link.")
        return
    route = desk.routes.get(booking["primary_route"], {})
    text = _norm(message["subject"] + " " + message["body"])

    if item["intent"] == "carrier_notice":
        match = re.search(r"(\d+)\s*days?", text)
        delay = int(match.group(1)) if match else None
        if delay is None:
            desk.escalate("milestones", item_id, "Carrier notice with no delay stated - "
                          "ETA left unchanged until someone confirms it.")
            return
        new_eta = (date.fromisoformat(booking["eta"]) + timedelta(days=delay)).isoformat()
        what = "Rolled to next sailing" if "roll" in text else "Schedule change"
        desk.emit("milestones", {
            "item": item_id, "kind": "tms", "record": "booking", "operation": "update_milestone",
            "action": "milestone", "booking_ref": booking["id"], "customer": booking["customer"],
            "changes": [{"field": "milestone", "to": what},
                        {"field": "eta", "from": booking["eta"], "to": new_eta}],
            "reason": f"{message['sender_org']}: {what.lower()}, {delay} days.",
        })
        desk.post("milestones", "exception", "handoff", item_id,
                  f"{booking['id']} slips {delay} days to {new_eta}. Slack on the booking "
                  f"is {booking['deadline_slack_days']} days.", deliver=True,
                  reason="slip", delay=delay, new_eta=new_eta, booking=booking["id"],
                  why=f"The notice says {delay} days; the ETA moves by exactly that and the "
                      f"slip goes to Exception to weigh against the slack.")
        return

    if item["intent"] == "milestone":
        what = ("Departed transhipment port" if "depart" in text else
                "Discharged" if "discharg" in text else "Gate-in" if "gate-in" in text
                else "Milestone")
        desk.emit("milestones", {
            "item": item_id, "kind": "tms", "record": "booking", "operation": "log_milestone",
            "action": "milestone", "booking_ref": booking["id"], "customer": booking["customer"],
            "changes": [{"field": "milestone", "to": what}],
            "reason": "Routine milestone, no exception. No reply owed.",
        })
        return

    # status_request - answered from the record, not from memory
    name, addr = _sender(message)
    port = PORT_NAMES.get(route.get("discharge_port"), route.get("discharge_port"))
    desk.emit("milestones", {
        "item": item_id, "kind": "mail", "audience": "customer",
        "customer": booking["customer"], "to": addr, "booking_ref": booking["id"],
        "subject": f"RE: {message['subject']}",
        "body": (f"Dear {name},\n\n{booking['booking_ref']} ({booking['cargo'].lower()}) is on "
                 f"the water on {route.get('description', 'its booked routing')}, discharging "
                 f"at {port}. Current ETA is {booking['eta']}, with delivery to "
                 f"{booking['final_destination']} after that. We will tell you straight away "
                 f"if it moves.\n\nKind regards,\n{config.FORWARDER['company']}"),
    })


# ---------------------------------------------------------------------------
# Exception Worker - what is off plan, and who has to know
# ---------------------------------------------------------------------------


def _exception(desk, item_id, message, msg):
    data = msg.get("data") or {}
    booking = desk.by_id.get(data.get("booking"))
    if not booking:
        return
    if data.get("reason") == "slip":
        delay, slack = data["delay"], booking["deadline_slack_days"]
        breach = delay > slack
        flag = (f"Rolled +{delay}d - breaches required-by {booking['required_by']} by "
                f"{delay - slack}d" if breach else
                f"Slip +{delay}d - absorbed by {slack}d slack")
        desk.emit("exception", {
            "item": item_id, "kind": "tms", "record": "exception", "operation": "flag_exception",
            "action": "exception", "booking_ref": booking["id"], "customer": booking["customer"],
            "delay_days": delay, "new_eta": data["new_eta"],
            "changes": [{"field": "exception_flag", "from": "none", "to": flag}],
            "reason": (f"{delay} days late against {slack} days of slack." +
                       (" No routing change the desk can make absorbs that alone." if breach
                        else "")),
        })
        if breach:
            # Across the layers, the other way: a slip the desk cannot absorb is a
            # routing question, and routing is the risk layer's call.
            desk.escalate("exception", item_id,
                          f"{booking['id']} now misses its required-by date by "
                          f"{delay - slack} days. Re-plan: the next routing decision is "
                          f"the Routing Worker's, and a person approves it.",
                          to="routing", why=f"{delay} days late against {slack} days of "
                                            f"slack - more than the desk can absorb.")
        return

    if data.get("reason") == "doc_mismatch":
        diffs = data.get("diffs") or []
        name, addr = _sender(message)
        desk.emit("exception", {
            "item": item_id, "kind": "tms", "record": "exception", "operation": "flag_exception",
            "action": "exception", "booking_ref": booking["id"], "customer": booking["customer"],
            "changes": [{"field": "exception_flag", "from": "none",
                         "to": "Document mismatch - release held"}],
            "reason": "; ".join(f"{d['label']}: "
                                + (f"{d['document']:,}" if isinstance(d["document"], int)
                                   else f"{d['document']}")
                                + f" on the document, {d['booking']} on the booking"
                                for d in diffs) + " - release held until it is resolved.",
        })
        desk.emit("exception", {
            "item": item_id, "kind": "mail", "audience": "customer",
            "customer": booking["customer"], "to": addr, "booking_ref": booking["id"],
            "subject": f"{booking['booking_ref']}: please check the documents before release",
            "body": (f"Dear {name},\n\nThank you for the documents. Before we release them, one "
                     f"thing does not match the booking: " + "; ".join(
                         f"the {d['label'].lower()} reads {d['document']:,} kg on the "
                         f"document and {d['booking']} kg on the booking"
                         if d["field"] in WEIGHT_FIELDS else
                         f"the {d['label'].lower()} reads {d['document']} on the document and "
                         f"{d['booking']} on the booking" for d in diffs)
                     + ". Could you ask the shipper to confirm which is right, and correct "
                     f"the draft if needed?\n\nKind regards,\n{config.FORWARDER['company']}"),
            "reason": "The document is not corrected to match the booking or the other way "
                      "round - the customer confirms which figure is right.",
        })


def _delay_notice(desk, item_id, output) -> dict:
    booking = desk.by_id[output["booking_ref"]]
    contact = (booking.get("customer_contact") or "").split(",")[0] or "team"
    return desk.emit("exception", {
        "item": item_id, "kind": "mail", "audience": "customer",
        "customer": booking["customer"],
        "to": f"{booking.get('customer_contact', booking['customer'])}",
        "booking_ref": booking["id"],
        "subject": f"{booking['booking_ref']}: revised arrival {output['new_eta']}",
        "body": (f"Dear {contact},\n\nThe carrier has rolled your {booking['cargo'].lower()} "
                 f"to the next sailing. The new ETA is {output['new_eta']}, "
                 f"{output['delay_days']} days later than booked. We are looking at how to "
                 f"win that time back and will come back to you today with the options.\n\n"
                 f"Kind regards,\n{config.FORWARDER['company']}"),
    })


# ---------------------------------------------------------------------------
# Invoice Worker - what was billed against what was agreed
# ---------------------------------------------------------------------------


def _invoice(desk, item_id, message, msg):
    item = desk.items[item_id]
    booking = desk.by_id.get(item.get("linked_booking"))
    if not booking:
        desk.escalate("invoice", item_id, "Invoice for a booking this desk cannot find.")
        return
    agreed_extra = desk.rate_sheet.get("agreed_charges_eur", {})
    freight = (booking.get("commercial") or {}).get("freight_eur")
    lines = []
    for attachment in message.get("attachments") or []:
        for raw in (attachment.get("text") or "").splitlines():
            if ":" not in raw or "eur" not in raw.lower():
                continue
            label, value = (p.strip() for p in raw.split(":", 1))
            amount = _money(value)
            norm = _norm(label)
            agreed = (freight if norm.startswith("ocean freight")
                      else agreed_extra.get(norm, 0))
            lines.append({"description": label, "invoiced": amount, "agreed": agreed})
    item["invoice_lines"] = lines
    disputed = [l for l in lines if l["invoiced"] != l["agreed"]]
    gap = sum(l["invoiced"] - l["agreed"] for l in disputed)
    desk.emit("invoice", {
        "item": item_id, "kind": "tms", "record": "invoice", "operation": "reconcile_invoice",
        "action": "invoice", "booking_ref": booking["id"], "customer": booking["customer"],
        "changes": [{"field": "invoice_status",
                     "to": (f"DISPUTED - {_eur(gap)} not agreed" if disputed
                            else "MATCHED - pass for payment")}],
        "reason": (f"{len(disputed)} of {len(lines)} lines differ from the agreed rate."
                   if disputed else f"All {len(lines)} lines match the agreed rate."),
    })
    if disputed:
        _, addr = _sender(message)
        desk.emit("invoice", {
            "item": item_id, "kind": "mail", "audience": "carrier",
            "customer": booking["customer"], "to": addr, "booking_ref": booking["id"],
            "subject": f"Query on {message['subject'].split(' - ')[0]}",
            "body": ("Hello,\n\nWe have checked this invoice against the rate agreed for "
                     f"{booking['booking_ref']}. " + " ".join(
                         f"{l['description']} ({_eur(l['invoiced'])}) is not part of the "
                         f"agreed rate." if not l["agreed"] else
                         f"{l['description']} is billed at {_eur(l['invoiced'])} against "
                         f"{_eur(l['agreed'])} agreed." for l in disputed)
                     + " Please send a corrected invoice, or the basis for the charge.\n\n"
                     f"Kind regards,\n{config.FORWARDER['company']}"),
            "reason": (f"{len(disputed)} line{'' if len(disputed) == 1 else 's'} not on the "
                       f"agreed rate - queried with the carrier, not passed for payment."),
        })


# ---------------------------------------------------------------------------
# Customs Worker - the entry prepared, or escalated
# ---------------------------------------------------------------------------


def _customs(desk, item_id, message, msg):
    item = desk.items[item_id]
    booking = desk.by_id.get(item.get("linked_booking"))
    if not booking:
        desk.escalate("customs", item_id, "Arrival notice for a booking this desk cannot find.")
        return
    route = desk.routes.get(booking["primary_route"], {})
    port = route.get("discharge_port")
    entry = roster.entry_for(port)
    docs = roster.booked_docs(booking["id"])
    onward = NON_EU.get(booking["final_destination"].lower())
    if onward:
        desk.emit("customs", {
            "item": item_id, "kind": "tms", "record": "customs", "operation": "flag_customs",
            "action": "customs", "booking_ref": booking["id"], "customer": booking["customer"],
            "changes": [{"field": "customs_status",
                         "to": f"ESCALATED - transit to {onward}, not an import at {port}"}],
            "reason": "Onward to a destination outside the EU customs union.",
        })
        desk.escalate("customs", item_id,
                      f"{booking['id']} lands at {PORT_NAMES.get(port, port)} but is going "
                      f"to {booking['final_destination']} ({onward}): a transit out of the EU, "
                      f"not an import entry. Who declares it and under which guarantee is a "
                      f"person's call - nothing filed.",
                      why=f"{booking['final_destination']} is outside the EU customs union, "
                          f"so an import entry at {PORT_NAMES.get(port, port)} would be the "
                          f"wrong filing.")
        return
    if not docs.get("hs") or not entry:
        desk.escalate("customs", item_id, "Missing HS code or entry office - nothing filed.")
        return
    desk.emit("customs", {
        "item": item_id, "kind": "tms", "record": "customs", "operation": "prepare_entry",
        "action": "customs entry", "booking_ref": booking["id"], "customer": booking["customer"],
        "changes": [{"field": "customs_entry",
                     "to": f"Import entry prepared - {entry['office']}, HS {docs['hs']}, "
                           f"{docs.get('incoterm')}, importer EORI {entry['eori']}..."}],
        "reason": f"Arrival at {PORT_NAMES.get(port, port)} ({entry['country']}). "
                  f"Prepared, not filed.",
    })


HANDLERS = {"rfq": _rfq, "booking": _booking, "docs": _docs, "milestones": _milestones,
            "exception": _exception, "invoice": _invoice, "customs": _customs}


# ---------------------------------------------------------------------------
# Playbook Worker - every output against the customer's standing rules
# ---------------------------------------------------------------------------


def _rule_verdict(desk, rule, output) -> tuple[str, str] | None:
    """(result, note) for one rule on one output, or None if it does not apply."""
    kind, value = rule["type"], rule["value"]
    if kind == "cc_on_customer_mail":
        if output["kind"] != "mail" or output.get("audience") != "customer":
            return None
        return (("pass", f"{value} copied") if value in output["cc"]
                else ("fix", f"copy {value} on every mail to this customer"))
    if kind == "quote_validity_days":
        if output.get("template") != "quote":
            return None
        return (("pass", f"validity {value} days") if output.get("validity_days") == value
                else ("fix", f"quotes to this customer are valid {value} days, not "
                             f"{output.get('validity_days')}"))
    if kind == "approved_carriers":
        if output.get("operation") != "create_booking":
            return None
        return (("pass", f"{output['carrier']} is approved") if output["carrier"] in value
                else ("fix", f"{output['carrier']} is not an approved carrier - use "
                             f"{' or '.join(value)}"))
    if kind == "notify_delay_over_days":
        if output.get("delay_days") is None:
            return None
        if output["delay_days"] <= value:
            return "pass", f"slip within {value} day(s) - no notice required"
        notified = any(o["kind"] == "mail" and o.get("audience") == "customer"
                       and o["item"] == output["item"] for o in desk.outputs)
        return (("pass", "customer notice drafted") if notified
                else ("fix", f"a slip over {value} day(s) needs a customer notice today"))
    return None


def _fix(desk, rule, output) -> tuple[bool, str]:
    """The producing Worker applies the fix the Playbook Worker asked for."""
    kind, value = rule["type"], rule["value"]
    if kind == "cc_on_customer_mail":
        output["cc"].append(value)
        return True, f"added {value} in copy"
    if kind == "quote_validity_days":
        output["validity_days"] = value
        output["params"]["validity_days"] = value
        output["body"] = _quote_body(output["params"])
        return True, f"validity set to {value} days"
    if kind == "approved_carriers":
        route = next((c["to"] for c in output["changes"] if c["field"] == "routing_code"), None)
        port = next((c["to"] for c in output["changes"] if c["field"] == "port_of_discharge"), None)
        city = next((c["to"] for c in output["changes"] if c["field"] == "final_destination"), None)
        equip = next((c["to"] for c in output["changes"] if c["field"] == "equipment"), "1 x 40ft")
        count, _, equipment = equip.partition(" x ")
        port_code = next((k for k, v in PORT_NAMES.items() if v == port), port)
        allowed = _ask_rates(desk, output["worker_id"], output["item"], port_code, city,
                             equipment, int(count), carrier_filter=value)
        if not allowed:
            return False, "no approved carrier prices this lane"
        pick = allowed[0]
        output["carrier"] = pick["carrier"]
        for change in output["changes"]:
            if change["field"] == "carrier":
                change["to"] = pick["carrier"]
            if change["field"] == "routing_code":
                change["to"] = pick["route_id"]
        output["reason"] = (output["reason"] + f" Carrier changed to {pick['carrier']} "
                            f"under the customer's playbook.").strip()
        return True, f"rebooked with {pick['carrier']} ({_eur(pick['per_container_eur'])} per container)"
    if kind == "notify_delay_over_days":
        notice = _delay_notice(desk, output["item"], output)
        return True, f"drafted customer notice {notice['id']}"
    return False, "no fix known"


def _playbook_review(desk, producer, output) -> list[dict]:
    """Check, ask for a fix, re-check - up to three rounds. The Playbook Worker
    never edits another Worker's output itself: it says what is wrong, and the
    Worker that made it does the fixing, on the bus where anyone can read it."""
    rules = desk.playbooks.get(output.get("customer"), [])
    item = output["item"]
    if not rules:
        return [{"rule": "none", "result": "pass",
                 "note": "no standing instructions for this customer"}]
    desk.post(producer, "playbook", "check", item, f"Check {output['id']} for "
              f"{output.get('customer')}.",
              why=f"Every output is checked against {output.get('customer')}'s "
                  f"{len(rules)} standing rule(s) before a person sees it.")
    outcome: dict[str, dict] = {}
    for _round in range(3):
        broken = []
        for rule in rules:
            verdict = _rule_verdict(desk, rule, output)
            if verdict is None:
                continue
            result, note = verdict
            if result == "pass":
                outcome.setdefault(rule["type"], {"rule": rule["type"], "result": "pass",
                                                  "note": note, "why": rule.get("why")})
            else:
                broken.append((rule, note))
        if not broken:
            break
        for rule, note in broken:
            desk.post("playbook", producer, "revise", item, f"{output['id']}: {note}.",
                      why=f"Customer rule: {(rule.get('why') or rule['type']).rstrip('.')}.")
            ok, did = _fix(desk, rule, output)
            if ok:
                desk.post(producer, "playbook", "revised", item, f"{output['id']}: {did}.",
                          why="The Worker that made it fixes it - the Playbook Worker "
                              "never edits another Worker's output.")
                outcome[rule["type"]] = {"rule": rule["type"], "result": "fixed",
                                         "note": did, "why": rule.get("why")}
            else:
                outcome[rule["type"]] = {"rule": rule["type"], "result": "flag",
                                         "note": f"{note} - {did}", "why": rule.get("why")}
                desk.escalate("playbook", item, f"{output['id']} breaks the customer's "
                              f"playbook and cannot be fixed automatically: {note}.")
                rules = [r for r in rules if r is not rule]
    checks = list(outcome.values()) or [{"rule": "none", "result": "pass",
                                         "note": "no rule applies to this output"}]
    passed = sum(1 for c in checks if c["result"] in ("pass", "fixed"))
    desk.post("playbook", producer, "verdict", item,
              f"{output['id']}: {passed} of {len(checks)} rule(s) satisfied"
              + (f", {sum(1 for c in checks if c['result'] == 'fixed')} after a fix"
                 if any(c["result"] == "fixed" for c in checks) else "") + ".",
              why="Re-checked after every fix, up to three rounds; anything still "
                  "broken would have gone to a person.")
    return checks


# ---------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------


def _item_record(message) -> dict:
    return {"id": message["id"], "from": message["from"], "sender_org": message["sender_org"],
            "subject": message["subject"], "body": message["body"],
            "attachments": message.get("attachments") or [],
            "received": f"{message['received_minutes_ago']}m ago",
            "intent": None, "intent_label": None, "decided_by": None, "reason": None,
            "linked_booking": None, "customer": None, "owner": None, "path": ["inbox"],
            "outputs": [], "escalations": [], "needs_look": False, "look_reasons": [],
            "lessons_applied": [], "extracted": None}


def run(*, use_llm=True, lessons=None, today=None) -> dict:
    """Work the whole inbox once. Returns everything the dashboard needs."""
    lessons = learning.load() if lessons is None else lessons
    inbox = load_inbox()
    messages = inbox["messages"]
    desk = Desk(bookings=tms.read_bookings(), routes=route_advisor.load_routes(),
                playbooks=load_playbooks(), rate_sheet=inbox["rate_sheet"],
                lessons=lessons, today=today or date.today())
    by_id = {m["id"]: m for m in messages}
    for message in messages:
        desk.items[message["id"]] = _item_record(message)

    mode = _triage(desk, messages, use_llm)

    # Deliver handoffs until nothing is left. A Worker that hands on (Docs to
    # Exception, Milestones to Exception) adds to the queue; the guard is only
    # there so a bug can never become an infinite loop in front of a room.
    steps = 0
    while desk.queue and steps < 500:
        msg = desk.queue.pop(0)
        steps += 1
        handler = HANDLERS.get(msg["to_id"])
        if handler:
            handler(desk, msg["item"], by_id[msg["item"]], msg)

    items = list(desk.items.values())
    mails = [o for o in desk.outputs if o["kind"] == "mail"]
    writes = [o for o in desk.outputs if o["kind"] == "tms"]
    fixed = sum(1 for o in desk.outputs for c in o.get("checks", []) if c["result"] == "fixed")
    active = learning.active(lessons)
    return {
        "ran_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "state": "complete",
        "layer": MODE,
        "classifier": mode["classifier"],
        "classifier_note": mode["failure"],
        "model": llm.active_model() if mode["classifier"] == "model" else None,
        "items": items,
        "messages": desk.messages,
        "outputs": desk.outputs,
        "escalations": desk.escalations,
        "workers": _worker_summaries(desk, items),
        "groups": [dict(g, workers=[w["id"] for w in roster.ROSTER
                                    if w.get("group") == g["id"]])
                   for g in roster.GROUPS],
        "lessons": [dict(l, applied_to=sorted(desk.applied.get(l["id"], set())))
                    for l in lessons],
        "context": {name: learning.context_for(name, lessons)
                    for name in ("Inbox Worker", "Docs Worker")},
        "intents": {k: v["label"] for k, v in INTENTS.items()},
        "fields": {k: v[0] for k, v in FIELDS.items()},
        "stats": {
            "items": len(items),
            "routed": sum(1 for i in items if i["owner"]),
            "mails": len(mails), "writes": len(writes),
            "escalations": len(desk.escalations),
            "needs_look": sum(1 for i in items if i["needs_look"]),
            "messages": len(desk.messages),
            "playbook_fixes": fixed,
            "lessons_active": len(active),
            "lessons_applied": sum(1 for l in active if desk.applied.get(l["id"])),
            "by_model": sum(1 for i in items if i["decided_by"] == "model"),
            "by_rules": sum(1 for i in items if i["decided_by"] == "rules"),
            "by_lesson": sum(1 for i in items if i["decided_by"] == "lesson"),
        },
        "note": HONESTY,
        "learning_note": LEARNING_NOTE,
        "lessons_persist": not config.SERVERLESS,
    }


def _worker_summaries(desk, items) -> list[dict]:
    out = []
    for worker in roster.ROSTER:
        if worker.get("layer") != "workflow":
            continue
        wid = worker["id"]
        touched = [i["id"] for i in items if wid in i["path"]]
        made = [o for o in desk.outputs if o["worker_id"] == wid]
        sent = sum(1 for m in desk.messages if m["from_id"] == wid)
        if wid == "inbox":
            summary = f"{len(items)} mails read · {sum(1 for i in items if i['owner'])} routed"
        elif wid == "playbook":
            checked = sum(1 for m in desk.messages if m["to_id"] == "playbook" and m["kind"] == "check")
            fixes = sum(1 for m in desk.messages if m["from_id"] == "playbook" and m["kind"] == "revise")
            summary = f"{checked} outputs checked · {fixes} sent back to be fixed"
        elif worker["mode"] == "scripted":
            summary = "scripted - replays authored data"
        else:
            summary = (f"{len(touched)} mail{'' if len(touched) == 1 else 's'} · "
                       f"{len(made)} output{'' if len(made) == 1 else 's'}")
        out.append(dict(worker, items=touched, outputs=len(made), messages_sent=sent,
                        summary=summary))
    return out


# ---------------------------------------------------------------------------
# The learning loop - correct, learn, replay, verify, keep or refuse
# ---------------------------------------------------------------------------


def suggest_cue(message, right) -> str | None:
    text = _norm(message["subject"] + " " + message["body"])
    for hint in HINTS.get(right, []):
        if learning.cue_pattern(hint).search(text):
            return hint
    return None


def _label_for_value(message, value) -> str | None:
    """The label of the document line a corrected value came from."""
    for attachment in message.get("attachments") or []:
        for line in (attachment.get("text") or "").splitlines():
            if ":" not in line:
                continue
            label, raw = (p.strip() for p in line.split(":", 1))
            if parse_weight(raw) == parse_weight(value) or _norm(raw) == _norm(str(value)):
                return label
    return None


def _holds(lesson, result) -> bool:
    item = next((i for i in result["items"] if i["id"] == lesson["from_item"]), None)
    if not item:
        return False
    if lesson["kind"] == "intent":
        return item["intent"] == lesson["right"]
    got = ((item.get("extracted") or {}).get("fields") or {}).get(lesson["field"])
    if lesson["field"] in WEIGHT_FIELDS:
        return got is not None and got == parse_weight(lesson["right"])
    return got is not None and _norm(str(got)) == _norm(str(lesson["right"]))


def _signature(item, outputs) -> dict:
    mine = [o for o in outputs if o["item"] == item["id"]]
    return {"intent": item["intent"], "owner": item["owner"],
            "fields": (item.get("extracted") or {}).get("fields") or {},
            "outputs": [(o["kind"], o.get("operation") or o.get("subject")) for o in mine],
            "status": [c["to"] for o in mine if o["kind"] == "tms"
                       for c in o["changes"] if c["field"] in
                       ("booking_status", "documents", "exception_flag")],
            "escalations": len(item["escalations"]), "needs_look": item["needs_look"]}


def _diff(before, after) -> list[dict]:
    changed = []
    after_items = {i["id"]: i for i in after["items"]}
    for old in before["items"]:
        new = after_items[old["id"]]
        a, b = _signature(old, before["outputs"]), _signature(new, after["outputs"])
        if a == b:
            continue
        what = []
        if a["intent"] != b["intent"]:
            what.append(f"now read as {INTENTS[b['intent']]['label'].lower()} "
                        f"(was {INTENTS[a['intent']]['label'].lower() if a['intent'] else 'unclear'})")
        if a["owner"] != b["owner"] and b["owner"]:
            what.append(f"handled by the {NAMES[b['owner']]}")
        for field, value in b["fields"].items():
            if a["fields"].get(field) != value:
                what.append(f"{FIELDS[field][0].lower()} read as "
                            f"{value:,}" if isinstance(value, int) else
                            f"{FIELDS[field][0].lower()} read as {value}")
        if a["status"] != b["status"]:
            what += [s for s in b["status"] if s not in a["status"]]
        if a["outputs"] != b["outputs"]:
            gone = [o for o in a["outputs"] if o not in b["outputs"]]
            came = [o for o in b["outputs"] if o not in a["outputs"]]
            what += [f"now: {o[1]}" for o in came] + [f"no longer: {o[1]}" for o in gone]
        if a["escalations"] > b["escalations"]:
            what.append("no longer escalated to a person")
        if a["needs_look"] and not b["needs_look"]:
            what.append("no longer needs a look")
        changed.append({"item": old["id"], "subject": old["subject"], "changes": what})
    return changed


def correct(item_id, *, kind, right=None, cue=None, field=None, value=None, label=None,
            use_llm=False) -> dict:
    """A person corrects a Worker. The loop:

        1. make a lesson out of the correction
        2. replay the whole inbox with it
        3. keep it only if it fixes the mail it came from
        4. ...and every earlier lesson still holds (it may not undo one)
        5. report everything else it changed

    Returns {"accepted": bool, ...}. A refused lesson changes nothing.
    """
    lessons = learning.load()
    before = run(use_llm=use_llm, lessons=lessons)
    item = next((i for i in before["items"] if i["id"] == item_id), None)
    message = next((m for m in load_inbox()["messages"] if m["id"] == item_id), None)
    if not item or not message:
        return {"accepted": False, "reason": f"No mail {item_id} in the inbox."}

    if kind == "intent":
        if right not in INTENTS:
            return {"accepted": False, "reason": f"Unknown intent {right!r}."}
        if item["intent"] == right:
            return {"accepted": False, "reason": f"{item_id} is already read as "
                    f"{INTENTS[right]['label'].lower()} - nothing to learn."}
        cue = (cue or "").strip() or suggest_cue(message, right)
        text = _norm(message["subject"] + " " + message["body"])
        if not cue or not learning.cue_pattern(cue).search(text):
            return {"accepted": False, "reason": "A lesson needs a phrase that actually "
                    "appears in the mail, so it knows when to apply."}
        lesson = learning.intent_lesson(lessons, item_id=item_id, wrong=item["intent"],
                                        right=right, cue=cue,
                                        right_label=INTENTS[right]["label"])
    elif kind == "field":
        if field not in FIELDS:
            return {"accepted": False, "reason": f"Unknown field {field!r}."}
        if value in (None, ""):
            return {"accepted": False, "reason": "A field correction needs the right value."}
        label = (label or "").strip() or _label_for_value(message, value)
        if not label:
            return {"accepted": False, "reason": "That value is not on any line of the "
                    "attached documents, so there is no label to learn."}
        current = ((item.get("extracted") or {}).get("fields") or {}).get(field)
        lesson = learning.field_lesson(lessons, item_id=item_id, field=field,
                                       field_label=FIELDS[field][0], label=label,
                                       wrong=current, right=str(value))
    else:
        return {"accepted": False, "reason": f"Unknown correction kind {kind!r}."}

    candidate = learning.with_lesson(lessons, lesson)
    after = run(use_llm=use_llm, lessons=candidate)

    if not _holds(lesson, after):
        return {"accepted": False, "lesson": lesson,
                "reason": f"The lesson did not fix {item_id} when replayed, so it was not kept."}
    regression = [{"lesson": l["id"], "from_item": l["from_item"], "learned": l["learned"],
                   "holds": _holds(l, after)}
                  for l in learning.active(candidate) if l["id"] != lesson["id"]]
    broken = [r for r in regression if not r["holds"]]
    if broken:
        return {"accepted": False, "lesson": lesson, "regression": regression,
                "reason": f"Refused: it would undo {', '.join(r['lesson'] for r in broken)}. "
                          f"An earlier correction wins until a person removes it."}

    learning.save(candidate)
    changed = _diff(before, after)
    return {
        "accepted": True, "lesson": lesson,
        "superseded": [l["id"] for l in learning.conflicts(lessons, lesson)],
        "fixed_item": item_id,
        "changed": changed,
        "propagated": [c for c in changed if c["item"] != item_id],
        "regression": regression,
        "run": after,
    }


# ---------------------------------------------------------------------------
# Across the layers: the risk layer's decisions, carried out by the desk
# ---------------------------------------------------------------------------


def from_risk(cards) -> dict:
    """What the workflow layer does with a risk run's decisions.

    A reroute is not finished when it is decided. The booking has to be amended,
    a changed port can move the country of entry, the ETA moves on the record,
    and whatever is said to the customer has to meet their standing
    instructions. This is that handoff, as messages from the Routing Worker to
    the desk's Workers, and the Playbook Worker's check on every customer mail
    the Comms Worker drafted - fixing what it can (a missing copy address) on
    the draft itself, so the fix is in what a person approves.
    """
    playbooks = load_playbooks()
    messages, checks = [], []

    def post(frm, to, kind, sid, text):
        messages.append({"seq": len(messages) + 1, "from": NAMES.get(frm, frm), "from_id": frm,
                         "to": NAMES.get(to, to), "to_id": to, "kind": kind,
                         "item": sid, "text": text})

    for card in cards:
        decision = card.get("decision") or {}
        action = decision.get("decision")
        if action not in ("reroute", "hold"):
            continue
        sid = card["id"]
        if action == "reroute":
            old, new = card.get("discharge_port"), decision.get("recommended_discharge_port")
            post("routing", "booking", "handoff", sid,
                 f"Amend {sid}: discharge {old} to {new}, routing "
                 f"{card.get('route_id')} to {decision.get('recommended_route')}.")
            before, after = roster.entry_for(old), roster.entry_for(new)
            if before and after and before.get("country") != after.get("country"):
                post("routing", "customs", "handoff", sid,
                     f"Entry moves from {before['country']} to {after['country']}: a "
                     f"different office and EORI apply, and the B/L has to be reissued.")
        else:
            post("routing", "booking", "handoff", sid,
                 f"Hold {sid} at the load port - no equipment release until the hold lifts.")
        if decision.get("revised_eta"):
            post("routing", "milestones", "handoff", sid,
                 f"ETA on {sid} moves to {decision['revised_eta']}.")

        rules = playbooks.get(card.get("customer"), [])
        for draft in card.get("drafts") or []:
            if draft.get("audience") != "customer":
                continue
            for rule in rules:
                if rule["type"] == "cc_on_customer_mail":
                    cc = draft.setdefault("cc", [])
                    if rule["value"] in cc:
                        result, note = "pass", f"{rule['value']} copied"
                    else:
                        post("playbook", "comms", "revise", sid,
                             f"Customer mail on {sid}: copy {rule['value']}.")
                        cc.append(rule["value"])
                        result, note = "fixed", f"added {rule['value']} in copy"
                elif rule["type"] == "notify_delay_over_days":
                    result, note = "pass", "the customer is told in this draft"
                else:
                    continue
                checks.append({"booking": sid, "draft": draft.get("subject"),
                               "rule": rule["type"], "result": result, "note": note,
                               "why": rule.get("why")})
    return {"messages": messages, "checks": checks}


def main():
    parser = argparse.ArgumentParser(description="The workflow layer: work the inbox.")
    parser.add_argument("--llm", action="store_true", help="let the Inbox Worker use the model")
    parser.add_argument("--reset", action="store_true", help="forget every lesson first")
    parser.add_argument("--json", action="store_true", help="print the whole result")
    args = parser.parse_args()
    if args.reset:
        print(f"Forgot {learning.reset()} lesson(s).")
    result = run(use_llm=args.llm)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        return 0
    print(f"\nInbox worked: {result['stats']['items']} mails, classifier: {result['classifier']}")
    for item in result["items"]:
        flag = "  <- needs a look" if item["needs_look"] else ""
        print(f"  {item['id']} {item['intent_label'] or '?':<16} [{item['decided_by']}] "
              f"{' > '.join(NAMES[w].replace(' Worker', '') for w in item['path'])}{flag}")
    s = result["stats"]
    print(f"\n  {s['mails']} drafts (none sent) · {s['writes']} TMS changes queued (none written)"
          f" · {s['escalations']} escalations · {s['messages']} messages between Workers"
          f" · {s['playbook_fixes']} playbook fixes · {s['lessons_active']} lessons\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
