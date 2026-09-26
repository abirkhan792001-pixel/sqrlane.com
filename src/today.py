"""today.py - what a run means for the person running the desk, from that run alone.

The dashboard's Today page answers four questions, most urgent first: is my book
at risk and how badly (`at_stake`), what is about to go wrong (`runway`,
`watchlist`), who must I tell (`customers_to_notify`), and where is every
shipment - in its voyage and in the agents' loop (`journey`).

Every function here takes the run dict and nothing else, and `build()` is called
by the orchestrator on every run, so these numbers always describe the exact run
the rest of the screen shows. They used to be recomputed from a separate
rules-only run of the selected scenario, which put Hamburg figures beside a
board that had not been run - and after a live run, where the model decides,
the two could disagree. Arithmetic only, never a forecast, never a trend.
"""

from datetime import date

WATCH_MARGIN_DAYS = 2   # on plan, but a known delay would leave this little slack or less
THIN_SLACK_DAYS = 1     # on plan, with so little slack any disruption breaks the date


def watchlist(run: dict) -> list[dict]:
    """Bookings still on plan that are close to their limit - before anything moves.

    Two reasons, both arithmetic on the booking's own record and the active
    events, never a forecast: a disruption on the route whose worst expected
    delay leaves WATCH_MARGIN_DAYS of slack or less, or slack so thin
    (THIN_SLACK_DAYS or less) that any disruption on the route breaks the date.
    """
    events = {e["event_id"]: e for e in run["risk"]["events"]}
    rows = []
    for card in run["shipments"]:
        if card["state"] != "green":
            continue
        slack = card["slack_days"]
        exposed = [events[e] for e in (card.get("decision") or {}).get("triggering_events") or []
                   if e in events]
        if exposed:
            worst = max((max(e.get("expected_delay_days") or [0]) for e in exposed), default=0)
            margin = slack - worst
            if margin > WATCH_MARGIN_DAYS:
                continue
            reason = (f"{exposed[0]['title']} could delay it up to {worst} days; its {slack} "
                      f"days of slack would leave {margin}.")
        elif slack <= THIN_SLACK_DAYS:
            worst, margin = 0, slack
            reason = (f"Only {slack} day{'' if slack == 1 else 's'} of slack before its "
                      f"required-by date - any disruption on its route would break it.")
        else:
            continue
        rows.append({"id": card["id"], "cargo": card["cargo"], "eta": card["eta"],
                     "required_by": card.get("required_by"), "slack_days": slack,
                     "worst_delay_days": worst, "margin_days": margin, "reason": reason,
                     "events": [e["event_id"] for e in exposed]})
    return sorted(rows, key=lambda r: r["margin_days"])


def at_stake(run: dict) -> dict:
    """Money at stake per booking the disruption moved: doing nothing, against
    the recommended action. The advisor's own arithmetic on the booking's terms
    (route_advisor.cost_of) - a hold keeps the cost of staying, because nothing
    better exists."""
    rows = []
    for card in run["shipments"]:
        d = card.get("decision") or {}
        if d.get("decision") not in ("reroute", "hold"):
            continue
        stay, action = d.get("stay_exposure_eur", 0), d.get("action_exposure_eur", 0)
        rows.append({"id": card["id"], "customer": card.get("customer"), "cargo": card["cargo"],
                     "decision": d["decision"], "headline": d.get("headline"),
                     "stay_exposure_eur": stay, "action_exposure_eur": action,
                     "avoided_eur": max(0, stay - action),
                     "breaks_date": bool(d.get("deadline_breached")),
                     "costs_basis": d.get("costs_basis")})
    rows.sort(key=lambda r: -r["stay_exposure_eur"])
    return {"title": "At stake",
            "subtitle": "If nothing is done, against the recommended action",
            "rows": rows,
            "total_stay_eur": sum(r["stay_exposure_eur"] for r in rows),
            "total_action_eur": sum(r["action_exposure_eur"] for r in rows),
            "total_avoided_eur": sum(r["avoided_eur"] for r in rows),
            "basis": ("Computed from each booking's commercial terms - freight, the cost of "
                      "a day late, the cost of missing the date - by the Routing agent. "
                      "Not a forecast, and not a market figure.")}


def customers_to_notify(run: dict) -> dict:
    """Every customer a decision affects, with what is already drafted for them."""
    by_customer: dict[str, dict] = {}
    for card in run["shipments"]:
        d = card.get("decision") or {}
        if d.get("decision") not in ("reroute", "hold") or not d.get("notify_customer", True):
            continue
        entry = by_customer.setdefault(card.get("customer") or "Unknown customer",
                                       {"customer": card.get("customer") or "Unknown customer",
                                        "bookings": [], "breaks_date": False, "drafts": 0})
        entry["bookings"].append(card["id"])
        entry["breaks_date"] = entry["breaks_date"] or bool(d.get("deadline_breached"))
        entry["drafts"] += sum(1 for x in card.get("drafts") or [] if x.get("audience") == "customer")
    rows = sorted(by_customer.values(), key=lambda r: (not r["breaks_date"], r["customer"]))
    return {"title": "Customers to notify",
            "subtitle": "Each customer a decision affects; the mail is drafted, not sent",
            "rows": rows}


def runway(run: dict) -> dict:
    """Every booking's time left: slack against the worst delay if nothing is done,
    sorted so the one that runs out first is on top."""
    severity = {e["event_id"]: e.get("severity") for e in run["risk"]["events"]}
    rank = {"low": 1, "medium": 2, "high": 3}
    rows = []
    for card in run["shipments"]:
        d = card.get("decision") or {}
        slack = card["slack_days"]
        worst = d.get("stay_delay_days", 0) or 0
        margin = slack - worst
        sev = max((severity.get(e) for e in d.get("triggering_events") or []
                   if severity.get(e)), key=lambda x: rank.get(x, 0), default=None)
        after = ((d.get("delay_days") or 0) if d.get("decision") in ("reroute", "hold")
                 else worst)
        margin_after = slack - after
        if margin_after < 0:
            status = "breaks"          # even after the decision, the date is missed
        elif margin < 0:
            status = "resolved"        # would have broken; the decision keeps the date
        elif margin <= WATCH_MARGIN_DAYS and (worst or slack <= THIN_SLACK_DAYS):
            status = "close"
        else:
            status = "clear"
        rows.append({"id": card["id"], "cargo": card["cargo"], "customer": card.get("customer"),
                     "state": card["state"], "decision": d.get("decision"),
                     "slack_days": slack, "worst_delay_days": worst, "margin_days": margin,
                     "delay_after_decision_days": after, "margin_after_decision_days": margin_after,
                     "severity": sev, "status": status})
    order = {"breaks": 0, "resolved": 1, "close": 2, "clear": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["margin_after_decision_days"], r["id"]))
    return {"title": "Time runway",
            "subtitle": ("Slack against the worst delay if nothing is done, and where the "
                         "decision leaves it - what still breaks its date on top"),
            "statuses": {"breaks": "misses the required-by date even after the decision",
                         "resolved": "would have missed it; the decision keeps the date",
                         "close": "on plan, but close to the limit",
                         "clear": "time to spare"},
            "rows": rows}



def journey(run: dict) -> dict:
    """Where every shipment is: in its voyage, and in the agents' loop.

    The voyage stage is estimated from the booking's ETD and ETA - the same
    estimate the map draws, and labelled the same way. The loop stages are what
    this run actually did for the booking: detected, decided, drafted, queued.
    Approval is the person's step and is recorded by the dashboard, not here.
    """
    lanes = {l["id"]: l for l in (run.get("map") or {}).get("lanes", [])}
    events = {e["event_id"]: e for e in run["risk"]["events"]}
    queued: dict[str, int] = {}
    for op in run["tms"]["writebacks"]:
        queued[op["booking_ref"]] = queued.get(op["booking_ref"], 0) + 1
    today = date.today()
    rows = []
    for card in run["shipments"]:
        d = card.get("decision") or {}
        pos = (lanes.get(card["id"]) or {}).get("position") or {}
        try:
            days_to_eta = (date.fromisoformat(d.get("revised_eta") or card["eta"]) - today).days
        except (TypeError, ValueError):
            days_to_eta = None
        exposed = [events[e] for e in d.get("triggering_events") or [] if e in events]
        acted = d.get("decision") in ("reroute", "hold")
        drafts = len(card.get("drafts") or [])
        n_queued = queued.get(card["id"], 0)
        rows.append({
            "id": card["id"], "cargo": card["cargo"], "customer": card.get("customer"),
            "origin": card["origin"], "destination": card["final_destination"],
            "carrier": card.get("carrier"), "state": card["state"],
            "voyage": {
                "status": pos.get("status") or "unknown",
                "progress": pos.get("progress"),
                "etd": card.get("etd"), "eta": card["eta"],
                "revised_eta": d.get("revised_eta") if acted else None,
                "required_by": card.get("required_by"),
                "days_to_eta": days_to_eta,
                "basis": pos.get("basis") or "estimated from ETD and ETA - not vessel tracking",
            },
            "loop": [
                {"key": "detected", "label": "Disruption detected", "done": bool(exposed),
                 "detail": exposed[0]["title"] if exposed else "Nothing active on its route"},
                {"key": "decided", "label": "Decision", "done": acted,
                 "detail": d.get("headline") or "On plan"},
                {"key": "drafted", "label": "Mails drafted", "done": drafts > 0,
                 "detail": f"{drafts} draft{'' if drafts == 1 else 's'}, not sent" if drafts
                           else "Nothing to tell anyone"},
                {"key": "queued", "label": "Queued to the TMS", "done": n_queued > 0,
                 "detail": f"{n_queued} change{'' if n_queued == 1 else 's'}, not written"
                           if n_queued else "No change needed"},
                {"key": "approved", "label": "Your approval", "done": None,
                 "detail": "recorded by the dashboard when you approve"},
            ],
        })
    return {"title": "Where every shipment is",
            "subtitle": "In its voyage, and in the agents' loop",
            "rows": rows}


def build(run: dict) -> dict:
    """Everything Today shows about the board, from this run."""
    return {"at_stake": at_stake(run), "customers": customers_to_notify(run),
            "runway": runway(run), "watchlist": watchlist(run), "journey": journey(run),
            "scenario": (run.get("scenario") or {}).get("name"),
            "ran_at": run.get("ran_at")}
