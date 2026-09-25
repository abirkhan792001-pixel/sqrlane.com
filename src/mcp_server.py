"""mcp_server.py - the desk, as an MCP server.

The dashboard's Ask box is one way in. This is the other: any MCP client - Claude,
an IDE, another agent - can add https://sqrlane.com/mcp as a connector and put
questions to the same Assistant, which hands each one to the Worker who owns it.

It speaks the Model Context Protocol's Streamable HTTP transport in its simplest
form: one JSON-RPC request per POST, one JSON answer back, no session and no
server-sent stream. Three tools, all read-only - the same rule as the Ask box:
asking changes nothing.

    ask_sqrlane      a question, answered by the Worker who owns it
    list_bookings    the book the agents are working on, with each one's state
    list_scenarios   the disruptions that can be put on the board
"""

import json

from src import ask, orchestrator, risk_monitor

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "sqrlane", "title": "SQRlane - AI agents for freight forwarders",
               "version": "0.1"}
INSTRUCTIONS = ("SQRlane's desk of freight-forwarding agents. Ask about a booking, a port, a "
                "rate, an invoice, customs or what is waiting for approval; the Worker who owns "
                "it answers from a run of the board. The bookings are synthetic and the TMS "
                "link is a demo connector: nothing is sent and nothing is written.")

_SCENARIO = {"type": "string", "enum": ["hamburg", "redsea", "rhine", "france"],
             "description": "Which disruption is on the board. Omit for a calm board."}

TOOLS = [
    {"name": "ask_sqrlane",
     "title": "Ask the SQRlane desk",
     "description": ("Ask a freight-operations question. The Assistant routes it to the agent "
                     "who owns it (Milestones, Routing, Risk, Comms, Rate, Customs, Invoice, "
                     "TMS Link ...), that agent checks with the others, and answers from the "
                     "run. Says so when no agent owns the question."),
     "inputSchema": {"type": "object", "properties": {
         "question": {"type": "string", "description": "e.g. 'Where is SHP-002?'"},
         "scenario": _SCENARIO}, "required": ["question"]},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "list_bookings",
     "title": "List the bookings on the board",
     "description": "Every booking read through the TMS link, with its state after the run.",
     "inputSchema": {"type": "object", "properties": {"scenario": _SCENARIO}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "list_scenarios",
     "title": "List the disruption scenarios",
     "description": "The authored disruptions that can be put on the board.",
     "inputSchema": {"type": "object", "properties": {}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
]


def _text(payload) -> dict:
    return {"content": [{"type": "text", "text": payload if isinstance(payload, str)
                         else json.dumps(payload, ensure_ascii=False, indent=1)}]}


def _call(name: str, args: dict) -> dict:
    scenario = args.get("scenario") or None
    if name == "ask_sqrlane":
        result = ask.ask(str(args.get("question") or ""), scenario=scenario, use_llm=False)
        lines = [result["text"]]
        if result.get("routed_to"):
            lines.append(f"(Answered by the {result['routed_to']['name']}.)")
        lines += [f"- {s}" for s in result.get("suggestions") or []]
        lines.append("")
        lines += [f"{m['seq']}. {m['from']} -> {m['to']}: {m['text']}"
                  for m in result["conversation"]]
        return _text("\n".join(lines))
    if name == "list_bookings":
        run = orchestrator.run_cycle(live=False, inject=bool(scenario), use_llm=False,
                                     scenario=scenario)
        return _text({"connector": run["tms"]["connector"], "bookings": [
            {"id": c["id"], "cargo": c["cargo"], "from": c["origin"],
             "to": c["final_destination"], "eta": c["eta"], "state": c["state"],
             "decision": (c.get("decision") or {}).get("headline")}
            for c in run["shipments"]]})
    if name == "list_scenarios":
        return _text([{k: sc[k] for k in ("id", "name", "summary")}
                      for sc in risk_monitor.load_scenarios()])
    raise KeyError(name)


def handle(message: dict) -> dict | None:
    """One JSON-RPC message in, one response out (None for a notification)."""
    method, mid = message.get("method"), message.get("id")
    if mid is None:
        return None                      # notifications/initialized and friends
    try:
        if method == "initialize":
            result = {"protocolVersion": PROTOCOL_VERSION,
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": SERVER_INFO, "instructions": INSTRUCTIONS}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = message.get("params") or {}
            try:
                result = _call(params.get("name"), params.get("arguments") or {})
            except KeyError:
                return {"jsonrpc": "2.0", "id": mid,
                        "error": {"code": -32602, "message": f"Unknown tool: {params.get('name')}"}}
            except Exception as exc:  # noqa: BLE001 - a tool failure is a result, not a crash
                result = dict(_text(f"The desk could not answer: {type(exc).__name__}: {exc}"),
                              isError=True)
        else:
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}}
    except Exception as exc:  # noqa: BLE001
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(exc)}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}
