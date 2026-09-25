"""A forwarder can put their own TMS behind the connector - and it stays honest.

The demo connector reads a synthetic book. src/connect.py lets a real one in: an
uploaded export or a live HTTPS endpoint, mapped onto SQRlane's fields and put
behind the same one door (tms.read_bookings), so every Worker follows. Four
claims are made about that on screen, and each is held here:

  * The mapping is shown, not guessed: every column used is named, and a row the
    agents cannot judge is listed with its reason rather than forced onto a lane.
  * The connected book really is the book: a run under a connection decides on
    those records and no demo booking leaks in - and the demo comes back after.
  * The gate does not move: every write-back to a real TMS is still queued.
  * The link cannot be pointed inward: plain http, loopback and private
    addresses are refused before any request is made.

Run it:  python -m unittest discover -s tests
"""

import ast
import unittest
from pathlib import Path

from src import config, connect, orchestrator, tms

SRC = Path(__file__).resolve().parent.parent / "src"


def sample():
    return connect.read_export(config.SAMPLE_TMS_EXPORT.read_text(encoding="utf-8"),
                               "sample_tms_export.csv")


class TheExportIsMappedNotGuessed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = sample()

    def test_every_column_of_the_sample_is_mapped(self):
        self.assertEqual(self.conn["unmapped_columns"], [])
        fields = {m["field"] for m in self.conn["mapping"]}
        for needed in ("id", "origin", "port_of_discharge", "eta", "required_by"):
            self.assertIn(needed, fields)

    def test_rows_off_the_catalogue_are_listed_with_their_reason(self):
        self.assertEqual(self.conn["rows_read"], 10)
        self.assertEqual(len(self.conn["bookings"]), 7)
        reasons = {n["ref"]: n["reason"] for n in self.conn["not_covered"]}
        self.assertIn("Los Angeles", reasons["JOB-24166"])
        self.assertIn("Gdansk", reasons["JOB-24171"])
        self.assertIn("ETA", reasons["JOB-24175"])

    def test_both_date_formats_read_and_slack_is_computed(self):
        by_id = {b["id"]: b for b in self.conn["bookings"]}
        self.assertEqual(by_id["JOB-24126"]["eta"][5:], "10-08")
        self.assertEqual(by_id["JOB-24126"]["deadline_slack_days"], 3)
        self.assertTrue(by_id["JOB-24121"]["cold_chain"])
        self.assertEqual(by_id["JOB-24117"]["commercial"]["freight_eur"], 14200)

    def test_an_unreadable_value_is_not_filled_in(self):
        self.assertIsNone(connect.parse_date("next Tuesday"))
        text = "Shipment No,POL,POD,ETA\nJ-1,Shanghai,Hamburg,soon\n"
        conn = connect.read_export(text, "x.csv")
        self.assertEqual(conn["bookings"], [])
        self.assertIn("ETA", conn["not_covered"][0]["reason"])

    def test_a_missing_required_by_date_is_said_not_hidden(self):
        conn = connect.read_export("Shipment No,POL,POD,ETA\nJ-1,Shanghai,Hamburg,2026-10-01\n",
                                   "x.csv")
        self.assertEqual(conn["bookings"][0]["deadline_slack_days"], 0)
        self.assertTrue(any("required-by" in w for w in conn["warnings"]))


class TheConnectedBookIsTheBook(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        conn = sample()
        cls.spec = {k: conn[k] for k in ("kind", "name", "source", "read_at", "bookings")}
        with tms.using(cls.spec):
            cls.cycle = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")

    def test_every_card_comes_from_the_connected_tms(self):
        ids = {c["id"] for c in self.cycle["shipments"]}
        self.assertEqual(ids, {b["id"] for b in self.spec["bookings"]})
        for card in self.cycle["shipments"]:
            self.assertEqual(card["source_system"], self.spec["name"])
        self.assertEqual(self.cycle["tms"]["connector"], self.spec["name"])
        self.assertEqual(self.cycle["tms"]["kind"], "file")

    def test_the_agents_really_decide_on_it(self):
        states = {c["id"]: c["state"] for c in self.cycle["shipments"]}
        self.assertEqual(states["JOB-24126"], "rerouted")
        self.assertEqual(states["JOB-24121"], "hold")
        self.assertEqual(states["JOB-24117"], "green")

    def test_the_gate_does_not_move(self):
        self.assertGreater(self.cycle["tms"]["queued"], 0)
        for op in self.cycle["tms"]["writebacks"]:
            self.assertEqual(op["status"], "QUEUED - not written")
            self.assertEqual(op["approval_status"], "awaiting_approval")
        self.assertIn("nothing is written to it from here", self.cycle["tms"]["honesty"])

    def test_a_tampered_booking_costs_one_card_not_the_run(self):
        spec = dict(self.spec, bookings=[dict(self.spec["bookings"][0], primary_route="R-NOWHERE"),
                                         dict(self.spec["bookings"][1], eta="garbage"),
                                         "not a booking"] + self.spec["bookings"][2:])
        with tms.using(spec):
            run = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")
        self.assertEqual(len(run["shipments"]), len(self.spec["bookings"]) - 2)

    def test_the_demo_book_comes_back_after(self):
        self.assertIsNone(tms.active())
        self.assertIn("demo", tms.read_bookings()[0]["source_system"].lower())


class TheLinkCannotBePointedInward(unittest.TestCase):

    def test_only_public_https_is_accepted(self):
        for url in ("http://example.com/bookings", "https://127.0.0.1/x",
                    "https://10.0.0.8/x", "https://169.254.169.254/latest", "ftp://x/y", ""):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    connect.check_url(url)

    def test_redirects_are_never_followed_by_the_connector(self):
        tree = ast.parse((SRC / "connect.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "get_capped":
                kw = {k.arg: k.value for k in node.keywords}
                self.assertIn("allow_redirects", kw)
                self.assertFalse(kw["allow_redirects"].value)

    def test_nothing_is_stored_server_side(self):
        tree = ast.parse((SRC / "connect.py").read_text(encoding="utf-8"))
        opens = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "open"]
        self.assertEqual(opens, [], "connect.py must not write a connection or token to disk")


class TheApiAnswersInSentences(unittest.TestCase):

    def test_connect_and_run_over_http(self):
        from fastapi.testclient import TestClient
        from src.app import app
        client = TestClient(app)
        text = client.get("/api/tms/sample.csv").text
        conn = client.post("/api/tms/connect", json={"kind": "file", "content": text,
                                                     "filename": "s.csv"}).json()
        self.assertTrue(conn["ok"])
        bad = client.post("/api/tms/connect", json={"kind": "api",
                                                    "url": "https://127.0.0.1/"}).json()
        self.assertFalse(bad["ok"])
        self.assertIn("private", bad["error"])
        run = client.post("/run", json={"live": False, "use_llm": False, "scenario": "hamburg",
                                        "connection": conn}).json()
        self.assertEqual(run["state"], "complete")
        self.assertEqual(run["tms"]["connector"], conn["name"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
