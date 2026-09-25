"""SQRlane works through the TMS. This file holds that claim up.

The product statement is that the agents do not run beside the forwarder's
system of record - they run on it: bookings are read out of the TMS, every
decision is written back into it, and a person approves the write. That is said
on the landing page, in the dashboard, in the whitepaper and out loud in the
demo, so it needs something better than good intentions behind it.

Two kinds of check, the same split the sending test uses:

  * Structural - there is exactly one door to the book. Every .py under src/ is
    parsed, and if anything except the connector reads the shipments file
    directly, this fails and names the file and line. A second door is how "the
    board is the TMS's book" quietly stops being true.
  * Behavioural - a full offline cycle is run, and every action the three live
    Workers took is checked for a matching TMS write-back, named by the Worker
    that produced it and queued behind a person.

What this deliberately does NOT assert: that a TMS was contacted. It was not.
The connector is a demo one and every check below expects it to say so.

Run it:

    python -m unittest discover -s tests
"""

import ast
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"

# The connector owns the read. config names the path; nothing else may touch it.
MAY_READ_THE_BOOK = {"tms.py", "config.py"}


def python_files():
    return sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


class OneDoorToTheBook(unittest.TestCase):
    """Structural: the bookings can only come in one way."""

    def test_only_the_connector_reads_the_shipments_file(self):
        """Passing the path to a call is reading it. Naming it is not.

        app.py names the file in /api/health to report whether the deploy
        bundled data/ at all, which is a question about files rather than about
        bookings. Opening it anywhere outside the connector is the thing that
        matters, so that is what this looks for.
        """
        offences = []
        for path in python_files():
            if path.name in MAY_READ_THE_BOOK:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                passed = list(node.args) + [kw.value for kw in node.keywords]
                for arg in passed:
                    if isinstance(arg, ast.Attribute) and arg.attr == "SHIPMENTS_FILE":
                        offences.append(f"{path.name}:{node.lineno} opens SHIPMENTS_FILE")

        self.assertEqual(offences, [], "\n".join([
            "",
            "Something other than the connector is reading the book directly:",
            *(f"    {o}" for o in offences),
            "",
            "Bookings come out of the TMS through tms.read_bookings(), and that is the",
            "whole point - one door in means the day the connector talks to a real TMS,",
            "every component follows. A second door is how that quietly stops being true.",
        ]))

    def test_the_advisor_gets_its_shipments_from_the_connector(self):
        from src import route_advisor
        bookings = route_advisor.load_shipments()
        self.assertGreater(len(bookings), 0, "No bookings means this tests nothing.")
        for booking in bookings:
            with self.subTest(booking=booking["id"]):
                self.assertIn("demo", booking["source_system"].lower(),
                              "Every record must carry the system it came from - and in "
                              "this build that system is the demo connector.")
                self.assertEqual(booking["record_status"], "synced")


class EveryActionLandsOnTheRecord(unittest.TestCase):
    """Behavioural: what the Workers did, expressed as changes to TMS records."""

    @classmethod
    def setUpClass(cls):
        from src import orchestrator, tms
        cls.tms = tms
        cls.result = orchestrator.run_cycle(live=False, inject=True, use_llm=False)
        cls.link = cls.result["tms"]
        cls.operations = cls.link["writebacks"]

    def test_the_cycle_queued_something_to_check(self):
        self.assertGreater(len(self.operations), 0,
                           "The injected strike actions bookings, so write-backs should be "
                           "queued. None means this file is testing nothing.")

    def test_the_board_is_the_book(self):
        self.assertEqual(self.link["bookings_read"], len(self.result["shipments"]),
                         "Every card on the board is one booking read out of the TMS.")
        for card in self.result["shipments"]:
            with self.subTest(booking=card["id"]):
                self.assertEqual(card["source_system"], self.tms.CONNECTOR_NAME)

    def test_all_three_live_workers_write_to_the_tms(self):
        """The claim is that the agents work *in* the system of record.

        A run where only the Routing Worker wrote anything would still look fine
        on screen while the claim quietly narrowed to one agent.
        """
        wrote = {op["agent"] for op in self.operations}
        for agent in ("Risk Worker", "Routing Worker", "Comms Worker"):
            with self.subTest(agent=agent):
                self.assertIn(agent, wrote,
                              f"{agent} produced no TMS write-back on a run that actioned "
                              f"{self.link['bookings_affected']} bookings.")

    def test_every_actioned_booking_has_a_write_back(self):
        actioned = [c["id"] for c in self.result["shipments"]
                    if (c.get("decision") or {}).get("decision") in ("reroute", "hold")]
        self.assertGreater(len(actioned), 0, "Nothing was actioned - this tests nothing.")
        written = {op["booking_ref"] for op in self.operations}
        for booking in actioned:
            with self.subTest(booking=booking):
                self.assertIn(booking, written,
                              "A decision that never reaches the TMS is a decision nobody "
                              "acts on.")

    def test_a_booking_on_plan_writes_nothing(self):
        """Silence is a real answer. A write-back for an unchanged booking is noise."""
        on_plan = [c["id"] for c in self.result["shipments"]
                   if (c.get("decision") or {}).get("decision") == "no-action"]
        self.assertGreater(len(on_plan), 0,
                           "The strike leaves some bookings alone - that is the point of "
                           "the screenplay. None means this tests nothing.")
        written = {op["booking_ref"] for op in self.operations}
        for booking in on_plan:
            with self.subTest(booking=booking):
                self.assertNotIn(booking, written)

    def test_every_write_back_names_the_worker_that_made_it(self):
        known = {a["agent"] for a in self.tms.AGENT_RECORDS}
        records = {a["record"] for a in self.tms.AGENT_RECORDS}
        for op in self.operations:
            with self.subTest(booking=op["booking_ref"], operation=op["operation"]):
                self.assertIn(op["agent"], known)
                self.assertIn(op["record"], records)
                self.assertTrue(op["changes"], "A write-back that changes nothing is not one.")

    def test_nothing_is_ever_written(self):
        """The gate, on the write side. Same rule as a drafted email."""
        for op in self.operations:
            with self.subTest(booking=op["booking_ref"], operation=op["operation"]):
                self.assertEqual(op["status"], "QUEUED - not written")
                self.assertEqual(op["approval_status"], "awaiting_approval")

    def test_the_link_says_what_it_is_everywhere_it_is_surfaced(self):
        self.assertIn("demo", (self.link["connector"] + self.link["status"]).lower())
        self.assertIn("tms", self.link["positioning"].lower(),
                      "The one-line positioning is where the product claim is written "
                      "down. It has to name the system of record.")
        self.assertIn("nothing is written", self.link["honesty"].lower())

    def test_the_board_reports_the_link_before_the_button_is_pressed(self):
        """The connection is not something a run creates. It is where the board came from."""
        from src import orchestrator
        idle = orchestrator.initial_state()
        self.assertEqual(idle["tms"]["bookings_read"], len(idle["shipments"]))
        self.assertEqual(idle["tms"]["queued"], 0,
                         "Nothing has been decided yet, so nothing can be queued.")


class TheProductPageIsOneRealRun(unittest.TestCase):
    """/product follows SHP-001 through the Hamburg strike and shows every field
    each Worker writes on the record, the handoffs to the desk and the roster.
    It is drawn from #product-run, a copy of one offline run - so it has to stay
    one. Rebuild each fact from a fresh run here and compare: a page that shows
    a change the connector would not queue is drawing a diagram of something the
    code does not do. (It replaced the IN-108 transcript check on 2026-09-25,
    when that exchange moved to /use-cases, where it is held the same way.)"""

    @classmethod
    def setUpClass(cls):
        import json
        import re
        from src import orchestrator, tms
        page = (Path(__file__).resolve().parent.parent / "static" / "product.html").read_text()
        block = re.search(r'<script type="application/json" id="product-run">(.*?)</script>',
                          page, re.S)
        assert block, "the run data is gone from /product"
        cls.page = json.loads(block.group(1))
        cls.cycle = orchestrator.run_cycle(live=False, inject=True, use_llm=False,
                                         scenario=cls.page["scenario"])
        cls.card = next(c for c in cls.cycle["shipments"] if c["id"] == cls.page["booking"]["id"])
        cls.ops = tms.writebacks_for(cls.card)

    def _writes(self, agent):
        from datetime import date
        out = []
        for op in self.ops:
            if op["agent"] != agent:
                continue
            for c in op["changes"]:
                if c["field"] == "eta":
                    out.append({"field": "eta", "shift_days": (date.fromisoformat(c["to"]) -
                                                              date.fromisoformat(c["from"])).days})
                else:
                    out.append({k: c[k] for k in ("field", "from", "to") if c.get(k) is not None})
        return out

    def test_the_booking_is_the_one_the_connector_reads(self):
        for key, value in self.page["booking"].items():
            self.assertEqual(value, self.card[key], key)

    def test_every_field_on_the_record_is_what_that_worker_queues(self):
        steps = {s["who"]: s for s in self.page["steps"]}
        for agent in ("Risk Worker", "Routing Worker", "Comms Worker"):
            self.assertEqual(steps[agent]["writes"], self._writes(agent), agent)
        self.assertEqual(self.page["gate"]["operations"], len(self.ops))
        self.assertEqual(self.page["gate"]["changes"], sum(len(op["changes"]) for op in self.ops))

    def test_every_agent_line_and_reason_is_the_runs_own(self):
        d = self.card["decision"]
        ev = next(e for e in self.cycle["risk"]["events"] if e["event_id"] in d["triggering_events"])
        for key in ("event_id", "title", "type", "severity", "chokepoint"):
            self.assertEqual(self.page["event"][key], ev[key], key)
        self.assertTrue(ev["source"].startswith(self.page["event"]["outlet"]))
        risk, routing, comms = self.page["steps"]
        exc = next(op for op in self.ops if op["agent"] == "Risk Worker")
        self.assertEqual(risk["says"], f"Flags {ev['event_id']} on {self.card['id']}.")
        self.assertEqual(risk["why"], exc["reason"].split(" Revised ETA")[0] +
                         f" Severity {ev['severity']}.")
        self.assertEqual(routing["says"], d["headline"])
        self.assertEqual(routing["why"], d["reasoning"])
        self.assertEqual(self.page["join"]["decision"], d["headline"])
        logs = [op for op in self.ops if op["agent"] == "Comms Worker"]
        self.assertEqual([x["to"] for x in comms["drafts"]], [op["changes"][0]["to"] for op in logs])
        for x, op in zip(comms["drafts"], logs):
            if "subject" in x:
                self.assertEqual(x["subject"], op["reason"])
        check = next(c for c in self.cycle["workflow_handoffs"]["checks"]
                     if c["booking"] == self.card["id"] and c["rule"] == "notify_delay_over_days")
        self.assertEqual(comms["why"], f"Playbook check on the customer mail: {check['note']} "
                                       f"({check['why']}).")
        self.assertEqual(self.page["join"]["check"], {"note": check["note"], "why": check["why"]})

    def test_the_handoffs_are_what_the_routing_worker_sent_the_desk(self):
        sent = {(m["to"], m["text"], m.get("why")) for m in self.cycle["workflow_handoffs"]["messages"]
                if m["item"] == self.card["id"]}
        self.assertGreaterEqual(len(self.page["join"]["handoffs"]), 2)
        for h in self.page["join"]["handoffs"]:
            self.assertIn((h["to"], h["text"], h["why"]), sent)

    def test_the_roster_is_the_code_s_roster(self):
        from src import orchestrator, roster
        risk = [{"name": w["name"], "mode": "live", "role": w["role"]} for w in orchestrator.WORKERS]
        risk += [{"name": w["name"], "mode": w["mode"], "role": w["role"]}
                 for w in roster.ROSTER if w["layer"] in ("risk", "record")]
        self.assertEqual(self.page["roster"]["risk"], risk)
        desk = self.page["roster"]["desk"]
        self.assertEqual([(g["num"], g["title"]) for g in desk],
                         [(g["num"], g["title"]) for g in roster.GROUPS])
        on_page = [w for g in desk for w in g["workers"]]
        in_code = {w["name"]: w for w in roster.ROSTER if w["layer"] == "workflow"}
        self.assertEqual(sorted(w["name"] for w in on_page), sorted(in_code))
        for w in on_page:
            self.assertEqual((w["mode"], w["role"]), (in_code[w["name"]]["mode"],
                                                      in_code[w["name"]]["role"]), w["name"])
        self.assertEqual(len(self.page["roster"]["risk"]) + len(on_page), 16)

    def test_no_date_is_printed_on_the_page(self):
        """The bookings age forward weekly, so a date copied onto the page would be
        wrong within a week. The ETA is carried as a shift in days instead."""
        import json
        import re
        text = json.dumps(self.page)
        self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}", text), "a date leaked onto /product")


if __name__ == "__main__":
    unittest.main(verbosity=2)
