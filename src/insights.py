"""insights.py - the dashboard's numbers, counted from one run.

The dashboard's insights page draws four stat cards and two bar charts. Every
number on it comes from here, and every one is a count of what the desk and the
board just did - never a trend. There is no history to compare a run against,
so there is no "from last period", no win rate and no response time: those would
be invented, and an invented metric is the one thing this project refuses to
produce. A test holds each figure to the run it came from.
"""

from datetime import datetime, timezone

from src import orchestrator, tms, workflow

SHORT = {"Inbox Worker": "Inbox", "Playbook Worker": "Playbook", "Rate Worker": "Rate",
         "RFQ Worker": "RFQ", "Booking Worker": "Booking", "Docs Worker": "Docs",
         "Milestones Worker": "Milestones", "Exception Worker": "Exception",
         "Invoice Worker": "Invoice", "Customs Worker": "Customs", "Routing Worker": "Routing",
         "Risk Worker": "Risk", "Comms Worker": "Comms", "Planner Worker": "Planner"}


def _shares(counts: dict) -> list[dict]:
    """Rows with a count and a whole-number share that adds up to exactly 100."""
    total = sum(counts.values())
    if not total:
        return []
    rows = sorted(counts.items(), key=lambda kv: -kv[1])
    raw = [(k, v, v * 100 / total) for k, v in rows]
    floors = [int(p) for _, _, p in raw]
    # Largest remainder, so the bars' labels add to 100 rather than 99 or 101.
    for i in sorted(range(len(raw)), key=lambda i: -(raw[i][2] - floors[i]))[:100 - sum(floors)]:
        floors[i] += 1
    return [{"label": k, "count": v, "share": s} for (k, v, _), s in zip(raw, floors)]


def build(*, scenario: str | None = None) -> dict:
    run = orchestrator.run_cycle(live=False, inject=bool(scenario), use_llm=False,
                                 scenario=scenario)
    with tms.using(None):
        desk = workflow.run(use_llm=False)
    items, outputs = desk["items"], desk["outputs"]

    escalated = {e["item"] for e in desk["escalations"]}
    end_to_end = [i for i in items if i["owner"] and i["id"] not in escalated]
    waiting = (sum(1 for o in outputs if o.get("approval_status") == "awaiting_approval")
               + run["tms"]["queued"])

    by_worker: dict[str, int] = {}
    for msg in desk["messages"] + run["workflow_handoffs"]["messages"]:
        name = SHORT.get(msg["from"])
        if name:
            by_worker[name] = by_worker.get(name, 0) + 1

    intents: dict[str, int] = {}
    for item in items:
        label = item.get("intent_label") or "Unclear"
        intents[label] = intents.get(label, 0) + 1

    approvals: dict[str, int] = {}
    for o in outputs:
        approvals[o["worker"]] = approvals.get(o["worker"], 0) + 1
    for op in run["tms"]["writebacks"]:
        approvals[op["agent"]] = approvals.get(op["agent"], 0) + 1

    n = len(items)
    return {
        "built_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "title": "Desk insights",
        "subtitle": (f"This morning's inbox and the {run['scenario']['name']} board"
                     if run.get("scenario") else "This morning's inbox and a calm board"),
        "cards": [
            {"label": "Mails worked", "value": str(n),
             "caption": "every inbound mail, triaged and routed"},
            {"label": "Handled end to end", "value": f"{round(len(end_to_end) * 100 / n)}%" if n else "0%",
             "caption": f"{len(end_to_end)} of {n} needed no person before approval"},
            {"label": "Escalated to a person", "value": str(len(escalated)),
             "caption": "held rather than guessed"},
            {"label": "Waiting for you", "value": str(waiting),
             "caption": "drafts and TMS changes at the gate"},
        ],
        "workload": {"title": "Work by agent",
                     "subtitle": "Messages each agent posted on the desk's bus in this run",
                     "bars": [{"label": k, "value": v} for k, v in
                              sorted(by_worker.items(), key=lambda kv: -kv[1])]},
        "mix": {"title": "What the inbox asked for",
                "subtitle": "Share of this morning's mails, by what the Inbox Worker read them as",
                "rows": _shares(intents)},
        "approvals": {"title": "Where your approvals come from",
                      "subtitle": "Items waiting at the gate, by the agent that produced them",
                      "rows": _shares(approvals)},
        "note": ("Counted from one run - the desk's synthetic inbox and the board as it "
                 "stands. There is no history yet, so nothing here is a trend."),
    }
