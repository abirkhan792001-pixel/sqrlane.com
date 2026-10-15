"""quote_request.py - a shipper's quote request, from their own AI chat.

One job: take what a shipper typed into Claude (or any MCP client) - a few lines,
and any text documents they dropped in - and put it through the desk exactly as
an inbound mail is worked: the Inbox Worker reads it, the RFQ Worker parses the
lane and asks the Rate Worker for options, the Playbook Worker checks the draft.

What comes back is what the forwarder would receive, and nothing more:

    the request, structured   origin, destination, equipment, count, as read
    what is missing           a question for each field the desk could not read,
                              never a value filled in
    the draft quote           DRAFT - not sent, awaiting the forwarder's approval.
                              It is not an offer, and it says so

Who may call it is decided before it is reached: on /mcp only a customer holding
a key the forwarder issued (src/customer_access.py), and `customer` is then the
key's customer, so their playbook applies. One thing this build does not do, and
the result says so every time: nothing is stored, so the request does not reach
a forwarder's queue. A price from the synthetic rate sheet is not a market rate.

Nothing here sends, writes or keeps anything: `workflow.work_mail` returns its
outputs as dicts at the gate, and this module only reads them.
"""

from itertools import count as _counter

from src import uploads, workflow

DOCUMENT_CHARS = 4000      # of each document, added to the text the lane is read from
_ids = _counter(1)

QUESTIONS = {
    "origin": ("Where does the cargo load? The desk prices from Shanghai, Ningbo, Shenzhen "
               "and Busan."),
    "destination": ("Where is it going? Hamburg, Rotterdam, Antwerp or Fos, or on to Munich, "
                    "Basel or Lyon."),
    "equipment": ("How many containers, and which kind? For example 2 x 40HC - the desk "
                  "prices 20ft, 40ft, 40HC, 40RH (reefer) and flatracks."),
}
# Not needed for a price, needed before anything is booked. Asked after the quote.
LATER = {
    "commodity": "What is the cargo? Needed before booking, not for the price.",
    "ready": "When is the cargo ready? Needed before booking, not for the price.",
}

NOT_STORED = ("In this build nothing is stored: this request does not reach a forwarder's "
              "queue, and nothing is sent or written.")
NOT_AN_OFFER = ("This is the draft the forwarder would be asked to approve - not an offer. "
                "Prices come from the desk's synthetic rate sheet, not market rates.")


def _documents(documents) -> tuple[list[dict], list[str], list[dict]]:
    """(attachments, extra text to read the lane from, files not read)."""
    attachments, extra, unread = [], [], []
    for index, doc in enumerate(documents or [], 1):
        seen = uploads.read(str(doc.get("name") or f"document-{index}"), doc.get("content"), index)
        if seen["kind"] == "unreadable":
            unread.append({"name": seen["name"], "reason": seen["reason"]})
        elif seen["kind"] == "export":
            unread.append({"name": seen["name"],
                           "reason": "This is a bookings export, not a quote request - the "
                                     "forwarder's TMS link reads those, not this tool."})
        else:
            mail = seen["message"]
            parts = [mail.get("body") or ""] + [a.get("text") or "" for a in mail["attachments"]]
            extra.append(f"--- {seen['name']} ---\n" + "\n".join(parts)[:DOCUMENT_CHARS])
            attachments += mail["attachments"] or [{"name": seen["name"], "text": mail["body"]}]
    return attachments, extra, unread


def request_quote(request: str, *, customer: str | None = None, contact: str | None = None,
                  documents: list[dict] | None = None, use_llm: bool = False) -> dict:
    """Work one quote request through the desk. Returns the structured result."""
    request = (request or "").strip()
    attachments, extra, unread = _documents(documents)
    if not request and not extra:
        return {"status": "nothing to read",
                "text": "Nothing to quote: send the request as text, or a text document.",
                "questions": list(QUESTIONS.values()), "unread_documents": unread,
                "notes": [NOT_STORED]}
    item_id = f"RQ-{next(_ids):03d}"
    org = (customer or "").strip() or "Unnamed shipper (AI chat)"
    message = {"id": item_id, "from": (contact or "").strip() or org, "sender_org": org,
               # "Quote request" in the subject: the person chose the quote tool, so the
               # Inbox Worker is told as much in the words it reads.
               "subject": "Quote request via AI chat",
               "body": "\n\n".join([request] + extra), "attachments": attachments}
    worked = workflow.work_mail(message, use_llm=use_llm)
    item = worked["item"]
    parsed = item.get("parsed") or {}
    outputs = worked["outputs"]
    quote = next((o for o in outputs if o.get("template") == "quote"), None)
    quotation = next((o for o in outputs if o.get("operation") == "create_quotation"), None)

    if item.get("owner") != "rfq":
        missing = []
        status = "not read as a quote request"
        owner = workflow.NAMES.get(item.get("owner"), "a person")
        text = (f"The desk read this as {(item.get('intent_label') or 'something else').lower()}, "
                f"not a quote request, and handed it to the {owner}. Say what you want to "
                f"ship, from where to where, and how many containers.")
    else:
        missing = [k for k in QUESTIONS if not parsed.get(k)]
        if missing:
            status = "details missing"
            text = "The desk needs a little more before it can price this - nothing is guessed."
        elif not quote:
            status = "needs a person"
            text = "Nothing on the desk's rate sheet for this lane: a person at the forwarder prices it."
        else:
            status = "draft quote - awaiting the forwarder's approval"
            text = NOT_AN_OFFER

    return {
        "id": item_id, "status": status, "text": text,
        "request": {"customer": org, "contact": message["from"],
                    **{k: parsed.get(k) for k in ("origin", "destination", "discharge_port",
                                                  "equipment", "count", "commodity", "ready")}},
        "questions": [QUESTIONS[k] for k in missing],
        "before_booking": ([LATER[k] for k in LATER if not parsed.get(k)] if quote else []),
        "draft_quote": ({k: quote.get(k) for k in ("subject", "body", "status",
                                                    "approval_status", "reason", "worker")}
                        | {"checks": quote.get("checks") or []}) if quote else None,
        "queued_quotation": ({k: quotation.get(k) for k in ("changes", "status",
                                                            "approval_status", "worker")}
                             if quotation else None),
        "escalations": [e["text"] for e in worked["escalations"]],
        "unread_documents": unread,
        "conversation": [f"{m['seq']}. {m['from']} -> {m['to']}: {m['text']}"
                         for m in worked["messages"]],
        "classifier": worked["classifier"],
        "notes": [NOT_STORED],
    }


def as_text(result: dict) -> str:
    """The result as a chat client shows it."""
    lines = [f"Status: {result['status']}.", result["text"]]
    req = result.get("request")
    if req:
        lane = f"{req.get('origin') or '?'} to {req.get('destination') or '?'}"
        kit = (f"{req.get('count') or '?'} x {req['equipment']}" if req.get("equipment")
               else "equipment ?")
        lines.append(f"Request from {req['customer']}, as read: {lane}, {kit}.")
    if result.get("questions"):
        lines += ["", "Questions for the shipper:"] + [f"- {q}" for q in result["questions"]]
    quote = result.get("draft_quote")
    if quote:
        lines += ["", f"{quote['status']} ({quote['approval_status']}) - {quote['worker']}",
                  f"Subject: {quote['subject']}", "", quote["body"]]
    if result.get("before_booking"):
        lines += ["", "Before anything is booked:"] + [f"- {q}" for q in result["before_booking"]]
    if result.get("escalations"):
        lines += ["", "Escalated to a person:"] + [f"- {e}" for e in result["escalations"]]
    for doc in result.get("unread_documents") or []:
        lines.append(f"Not read: {doc['name']} - {doc['reason']}")
    if result.get("conversation"):
        lines += ["", "How the desk worked it:"] + result["conversation"]
    lines += [""] + result["notes"]
    return "\n".join(lines)
