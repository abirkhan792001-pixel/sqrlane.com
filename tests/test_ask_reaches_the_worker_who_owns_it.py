"""Ask SQRlane: the Worker who owns a question answers it, from the run.

src/ask.py puts a person on the desk's bus. The claims made about it:

  * A question reaches the Worker whose job it is, and the exchanges behind the
    answer are returned in order - the answer can be audited, not just read.
  * The answer is the run's own: the decision, the ETA and the event it quotes
    are the ones the run produced.
  * A question nobody owns is said to be nobody's, with suggestions - never a
    plausible answer from nowhere. That includes a booking not in the book and a
    place no source watches.
  * Asking changes nothing: nothing is drafted, queued or sent.

Run it:  python -m unittest discover -s tests
"""

import ast
import unittest
from pathlib import Path

from src import ask, orchestrator

SRC = Path(__file__).resolve().parent.parent / "src"

ROUTES = {
    "Where is SHP-002?": "milestones",
    "Why was SHP-001 rerouted?": "routing",
    "What is happening in Hamburg?": "risk",
    "What is waiting for my approval?": "tms",
    "Price 2 x 40HC Shanghai to Rotterdam": "rate",
    "Which invoices are disputed?": "invoice",
    "What are Nordmed Pharma's rules?": "playbook",
    "Which documents do not match?": "docs",
    "Is the customs entry ready for SHP-001?": "customs",
    "IN-108": "inbox",
}


def put(question):
    return ask.ask(question, scenario="hamburg", use_llm=False)


class EveryQuestionReachesItsOwner(unittest.TestCase):

    def test_each_example_is_routed_and_answered(self):
        for question, worker in ROUTES.items():
            with self.subTest(question=question):
                result = put(question)
                self.assertEqual(result["routed_to"]["id"], worker)
                self.assertTrue(result["answered"])
                self.assertTrue(result["text"].strip())
                convo = result["conversation"]
                self.assertEqual((convo[0]["from_id"], convo[0]["to_id"]), ("you", "assistant"))
                self.assertEqual([m["seq"] for m in convo], list(range(1, len(convo) + 1)))

    def test_the_owner_checks_with_the_others(self):
        convo = put("Where is SHP-002?")["conversation"]
        asked = {m["to_id"] for m in convo if m["kind"] == "query"}
        self.assertTrue({"tms", "routing", "risk"} <= asked)


class TheAnswerIsTheRunsOwn(unittest.TestCase):

    def test_the_decision_and_eta_are_the_runs(self):
        run = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")
        card = next(c for c in run["shipments"] if c["id"] == "SHP-002")
        text = put("Where is SHP-002?")["text"]
        self.assertIn(card["decision"]["headline"], text)
        self.assertIn(card["decision"]["revised_eta"], text)
        self.assertIn(card["eta"], text)

    def test_the_event_is_the_runs(self):
        run = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")
        text = put("What is happening in Hamburg?")["text"]
        self.assertIn(run["risk"]["events"][0]["title"], text)


class NobodysQuestionIsSaidToBeNobodys(unittest.TestCase):

    def test_a_booking_not_in_the_book(self):
        result = put("Where is SHP-099?")
        self.assertFalse(result["answered"])
        self.assertIsNone(result["routed_to"])
        self.assertIn("not in the book", result["text"])
        self.assertTrue(result["suggestions"])

    def test_a_place_no_source_watches(self):
        result = put("What's the weather in Paris tomorrow?")
        self.assertFalse(result["answered"])
        self.assertIn("Paris", result["text"])
        self.assertNotIn("Hamburg - union", result["text"])
        self.assertTrue(result["suggestions"])

    def test_a_question_off_the_desk(self):
        result = put("Can you book me a table for dinner?")
        self.assertFalse(result["answered"])
        self.assertTrue(result["suggestions"])


class AskingChangesNothing(unittest.TestCase):

    def test_ask_never_gates_emits_or_sends(self):
        tree = ast.parse((SRC / "ask.py").read_text(encoding="utf-8"))
        called = {getattr(n.func, "attr", getattr(n.func, "id", "")) for n in ast.walk(tree)
                  if isinstance(n, ast.Call)}
        for forbidden in ("gate", "emit", "push", "post_capped", "correct"):
            self.assertNotIn(forbidden, called)

    def test_a_request_to_draft_returns_what_is_already_at_the_gate(self):
        result = put("Draft a mail to the customer for SHP-001")
        self.assertEqual(result["routed_to"]["id"], "comms")
        self.assertIn("none sent", result["text"])
        self.assertIn("DRAFT - not sent", result["text"])


class TheDeskIsAnMcpServer(unittest.TestCase):
    """Any MCP client can ask the same Assistant - read-only, like the Ask box."""

    def test_handshake_tools_and_a_question(self):
        from fastapi.testclient import TestClient
        from src.app import app
        client = TestClient(app)
        init = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                         "params": {}}).json()["result"]
        self.assertIn("tools", init["capabilities"])
        self.assertEqual(client.post("/mcp", json={"jsonrpc": "2.0",
                                                   "method": "notifications/initialized"}
                                     ).status_code, 202)
        tools = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2,
                                          "method": "tools/list"}).json()["result"]["tools"]
        for tool in tools:
            self.assertTrue(tool["annotations"]["readOnlyHint"], tool["name"])
        reply = client.post("/mcp", json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "ask_sqrlane", "arguments": {"question": "Where is SHP-002?",
                                                            "scenario": "hamburg"}}}).json()
        self.assertIn("SHP-002 is held", reply["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
