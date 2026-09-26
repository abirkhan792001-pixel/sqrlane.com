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


class AFileGoesToTheWorkerItBelongsTo(unittest.TestCase):
    """The Ask box's upload: an export to the TMS Link, a mail or document to the
    desk, and a file nothing here can read is said to be unreadable."""

    BL = ("BILL OF LADING (DRAFT) HLCU-2261188\nShipper: Shanghai Ruida Auto Components\n"
          "Gross weight: 18,900 kg")

    def upload(self, name, content, question=""):
        return ask.ask(question, scenario="hamburg", use_llm=False,
                       attachments=[{"name": name, "content": content}])

    def test_an_export_is_previewed_not_connected(self):
        from src import config, tms
        result = self.upload("tms.csv", config.SAMPLE_TMS_EXPORT.read_text(encoding="utf-8"))
        self.assertEqual(len(result["connection_preview"]["bookings"]), 7)
        self.assertIsNone(tms.active())
        self.assertIn("Nothing changes until you choose", result["text"])

    def test_a_document_is_worked_by_the_desk_and_gated(self):
        result = self.upload("BL.txt", self.BL)
        item = result["desk_item"]["item"]
        self.assertEqual(item["owner"], "docs")
        self.assertEqual(item["linked_booking"], "SHP-001")
        for out in result["desk_item"]["outputs"]:
            self.assertEqual(out["approval_status"], "awaiting_approval")

    def test_an_unreadable_file_is_said_to_be_unreadable(self):
        for name in ("scan.pdf", "photo.jpg", "export.xlsx"):
            with self.subTest(name=name):
                result = self.upload(name, None)
                self.assertFalse(result["answered"])
                self.assertNotIn("desk_item", result)

    def test_a_vague_question_beside_a_file_keeps_the_files_answer(self):
        result = self.upload("BL.txt", self.BL, question="check this please")
        self.assertTrue(result["answered"])
        self.assertIn("desk_item", result)


class TheDashboardCountsNotTrends(unittest.TestCase):
    """The insights page's cards and charts, held to the run they came from."""

    @classmethod
    def setUpClass(cls):
        from src import insights, workflow
        cls.data = insights.build(scenario="hamburg")
        cls.desk = workflow.run(use_llm=False)
        cls.board = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")

    def test_the_cards_are_the_runs_counts(self):
        cards = {c["label"]: c["value"] for c in self.data["cards"]}
        self.assertEqual(cards["Mails worked"], str(len(self.desk["items"])))
        self.assertEqual(cards["Escalated to a person"],
                         str(len({e["item"] for e in self.desk["escalations"]})))
        waiting = (sum(1 for o in self.desk["outputs"]
                       if o["approval_status"] == "awaiting_approval")
                   + self.board["tms"]["queued"])
        self.assertEqual(cards["Waiting for you"], str(waiting))
        self.assertEqual(sum(r["count"] for r in self.data["approvals"]["rows"]), waiting)

    def test_every_share_adds_to_a_hundred(self):
        for chart in ("mix", "approvals"):
            with self.subTest(chart=chart):
                self.assertEqual(sum(r["share"] for r in self.data[chart]["rows"]), 100)

    def test_nothing_is_a_trend(self):
        import json
        text = json.dumps(self.data).lower()
        for phrase in ("last period", "previous", "vs.", "win rate", "response time"):
            self.assertNotIn(phrase, text)


class TheWordingMayChangeButNotTheFacts(unittest.TestCase):
    """A small model rewords the answer; the guard throws the rewording away if a
    number, date, reference or status word changed, vanished or appeared."""

    ORIGINAL = ("SHP-002 is held: No better option - hold and notify. Revised ETA "
                "2026-10-19, 5 days later than booked, past the required-by date.")
    GOOD = ("SHP-002 is being held - there's no better option, so hold it and let the "
            "customer know. The revised ETA is 2026-10-19, 5 days later than booked, "
            "which is past the required-by date.")

    def test_a_faithful_rewording_passes(self):
        self.assertIsNone(ask.check_wording(self.ORIGINAL, self.GOOD))

    def test_a_changed_dropped_or_invented_fact_is_refused(self):
        for bad in (self.GOOD.replace("2026-10-19", "2026-10-20"),
                    self.GOOD.replace("SHP-002 ", "The booking "),
                    self.GOOD + " Expect about 3 more days.",
                    self.GOOD.replace("is being held", "was moved")):
            with self.subTest(bad=bad[:60]):
                self.assertIsNotNone(ask.check_wording(self.ORIGINAL, bad))

    def test_a_refused_rewording_shows_the_desks_own_words(self):
        from unittest import mock
        from src import llm
        with mock.patch.object(llm, "is_configured", return_value=True), \
             mock.patch.object(llm, "complete_json", side_effect=llm.LLMError("off")), \
             mock.patch.object(llm, "complete", return_value="SHP-002 arrives on 2026-10-01."):
            result = ask.ask("Where is SHP-002?", scenario="hamburg", use_llm=True)
        self.assertEqual(result["worded_by"], "code")
        self.assertEqual(result["text"], result["plain_text"])
        self.assertIn("kept the desk's wording", result["wording_note"])

    def test_an_accepted_rewording_keeps_the_original_beside_it(self):
        from unittest import mock
        from src import llm
        plain = put("Where is SHP-002?")["text"]
        with mock.patch.object(llm, "is_configured", return_value=True), \
             mock.patch.object(llm, "complete_json", side_effect=llm.LLMError("off")), \
             mock.patch.object(llm, "complete", return_value=plain + " "):
            result = ask.ask("Where is SHP-002?", scenario="hamburg", use_llm=True)
        self.assertEqual(result["worded_by"], "model")
        self.assertEqual(result["plain_text"], plain)


class RoutingAndWordingUseTheSmallModel(unittest.TestCase):

    def test_the_small_tier_picks_a_small_model_the_key_offers(self):
        from unittest import mock
        from src import config, llm
        lineup = [{"id": m} for m in ("openai/gpt-oss-120b", "llama-3.3-70b-versatile",
                                      "llama-3.1-8b-instant", "whisper-large-v3")]
        with mock.patch.object(config, "LLM_PROVIDER", "groq"), \
             mock.patch.object(config, "LLM_SMALL_MODEL", ""), \
             mock.patch.object(llm, "_list_model_entries", return_value=lineup), \
             mock.patch.dict(llm._resolved_small, clear=True):
            self.assertEqual(llm.resolve_small_model("groq"), "llama-3.1-8b-instant")

    def test_no_small_model_on_the_key_falls_back_to_the_main_one(self):
        from unittest import mock
        from src import config, llm
        lineup = [{"id": "openai/gpt-oss-120b"}]
        with mock.patch.object(config, "LLM_PROVIDER", "groq"), \
             mock.patch.object(config, "LLM_SMALL_MODEL", ""), \
             mock.patch.object(config, "LLM_MODEL", ""), \
             mock.patch.object(llm, "_list_model_entries", return_value=lineup), \
             mock.patch.dict(llm._resolved_small, clear=True), \
             mock.patch.dict(llm._resolved, clear=True):
            self.assertEqual(llm.resolve_small_model("groq"), "openai/gpt-oss-120b")

    def test_ask_calls_the_model_only_on_the_small_tier(self):
        import ast as _ast
        tree = _ast.parse((SRC / "ask.py").read_text(encoding="utf-8"))
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Call) and getattr(node.func, "attr", "") in (
                    "complete", "complete_json"):
                tiers = [k.value.value for k in node.keywords if k.arg == "tier"]
                self.assertEqual(tiers, ["small"], "every model call in ask.py is small-tier")


class TheMapIsEveryBookingReadThroughTheTms(unittest.TestCase):

    def test_every_booking_is_placed_and_the_estimate_says_so(self):
        from fastapi.testclient import TestClient
        from src.app import app
        data = TestClient(app).get("/api/map?scenario=hamburg").json()
        self.assertEqual(data["mapped"], data["bookings"])
        for lane in data["map"]["lanes"]:
            with self.subTest(lane=lane["id"]):
                self.assertIn("not vessel tracking", lane["position"]["basis"])
                self.assertTrue(0 <= lane["position"]["progress"] <= 1)

    def test_a_connected_book_is_what_the_map_shows(self):
        from fastapi.testclient import TestClient
        from src import config
        from src.app import app
        client = TestClient(app)
        conn = client.post("/api/tms/connect", json={
            "kind": "file", "filename": "s.csv",
            "content": config.SAMPLE_TMS_EXPORT.read_text(encoding="utf-8")}).json()
        data = client.post("/api/map", json={"scenario": "hamburg", "connection": conn}).json()
        self.assertEqual({l["id"] for l in data["map"]["lanes"]},
                         {b["id"] for b in conn["bookings"]})
        self.assertEqual(data["connector"], conn["name"])


class TheWatchlistIsArithmeticNotAForecast(unittest.TestCase):
    """On plan, but close to the limit - computed from the record and the events."""

    def test_a_connected_booking_near_its_limit_is_on_watch(self):
        from fastapi.testclient import TestClient
        from src import config
        from src.app import app
        client = TestClient(app)
        conn = client.post("/api/tms/connect", json={
            "kind": "file", "filename": "s.csv",
            "content": config.SAMPLE_TMS_EXPORT.read_text(encoding="utf-8")}).json()
        data = client.post("/api/insights", json={"scenario": "hamburg",
                                                  "connection": conn}).json()
        rows = {r["id"]: r for r in data["watchlist"]["rows"]}
        # 6 days of slack against a strike of up to 5: on plan, 1 day to spare.
        self.assertEqual(rows["JOB-24117"]["margin_days"], 1)
        self.assertEqual(rows["JOB-24117"]["worst_delay_days"], 5)
        for row in data["watchlist"]["rows"]:
            self.assertLessEqual(row["margin_days"], 2)

    def test_nothing_already_actioned_is_on_watch(self):
        from src import insights
        run = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")
        actioned = {c["id"] for c in run["shipments"] if c["state"] != "green"}
        self.assertFalse(actioned & {r["id"] for r in insights.watchlist(run)})

    def test_thin_slack_is_flagged_with_the_reason(self):
        from src import insights
        run = orchestrator.run_cycle(live=False, inject=False, use_llm=False)
        rows = {r["id"]: r for r in insights.watchlist(run)}
        self.assertIn("SHP-002", rows)
        self.assertIn("1 day of slack", rows["SHP-002"]["reason"])


class TheQueueCanBeSortedByFacts(unittest.TestCase):

    def test_every_write_back_carries_its_age_and_severity(self):
        run = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")
        for op in run["tms"]["writebacks"]:
            self.assertTrue(op["queued_at"])
            self.assertEqual(op["severity"], "high")

    def test_a_connection_test_refuses_a_private_address(self):
        from fastapi.testclient import TestClient
        from src.app import app
        result = TestClient(app).post("/api/tms/test", json={
            "kind": "writeback", "url": "https://192.168.1.4/hook"}).json()
        self.assertFalse(result["ok"])
        self.assertIsNone(result["verified_at"])


class TodayShowsWhatIsAtStakeInItsOwnUnits(unittest.TestCase):
    """The rebuilt Today page: money at stake, customers, the runway and the
    decision count are all the run's own arithmetic, in bookings and days."""

    @classmethod
    def setUpClass(cls):
        from src import insights
        cls.data = insights.build(scenario="hamburg")
        cls.board = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")

    def test_at_stake_is_the_advisors_own_arithmetic(self):
        stake = self.data["at_stake"]
        cards = {c["id"]: c for c in self.board["shipments"]}
        for row in stake["rows"]:
            d = cards[row["id"]]["decision"]
            self.assertEqual(row["stay_exposure_eur"], d["stay_exposure_eur"])
            self.assertEqual(row["action_exposure_eur"], d["action_exposure_eur"])
            self.assertGreaterEqual(row["avoided_eur"], 0)
            # The trail states the same number in prose.
            self.assertTrue(any(f"{d['stay_exposure_eur']:,}" in t["finding"]
                                for t in d["reasoning_trail"]))
        self.assertEqual(stake["total_stay_eur"], sum(r["stay_exposure_eur"] for r in stake["rows"]))
        hold = next(r for r in stake["rows"] if r["decision"] == "hold")
        self.assertEqual(hold["avoided_eur"], 0, "a hold keeps the cost of staying")

    def test_every_customer_to_notify_has_a_drafted_mail(self):
        rows = self.data["customers"]["rows"]
        self.assertEqual({b for r in rows for b in r["bookings"]},
                         {c["id"] for c in self.board["shipments"] if c["state"] != "green"})
        for row in rows:
            self.assertGreaterEqual(row["drafts"], 1)

    def test_the_runway_puts_what_still_breaks_on_top(self):
        rows = self.data["runway"]["rows"]
        self.assertEqual(len(rows), len(self.board["shipments"]))
        self.assertEqual((rows[0]["id"], rows[0]["status"]), ("SHP-002", "breaks"))
        statuses = {r["id"]: r["status"] for r in rows}
        self.assertEqual(statuses["SHP-001"], "resolved")
        for row in rows:
            self.assertEqual(row["margin_days"], row["slack_days"] - row["worst_delay_days"])

    def test_decisions_are_counted_in_bookings(self):
        dec = self.data["decisions"]
        self.assertLess(dec["bookings"], dec["items"])
        self.assertEqual(self.data["mix"]["total"], sum(r["count"] for r in self.data["mix"]["rows"]))

    def test_where_a_person_was_needed_matches_the_escalations(self):
        from src import workflow
        desk = workflow.run(use_llm=False)
        self.assertEqual(sum(r["count"] for r in self.data["people_needed"]["rows"]),
                         len(desk["escalations"]))

    def test_a_booking_without_terms_says_its_costs_are_not_priced(self):
        from src import connect, tms
        conn = connect.read_export("Shipment No,POL,POD,ETA,RDD\nJ-1,Shanghai,Hamburg,"
                                   "2026-10-06,2026-10-07\n", "x.csv")
        with tms.using(dict(conn, kind="file")):
            run = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")
        self.assertIn("not priced", run["shipments"][0]["decision"]["costs_basis"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
