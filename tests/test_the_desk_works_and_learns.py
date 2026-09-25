"""The workflow layer's claims, held.

The desk says four things out loud, and each is checked here:

  1. IT WORKS THE WHOLE INBOX. Every mail is read, linked and handed to the
     Worker that owns it - or escalated to a person, never guessed at.
  2. THE WORKERS TALK. Handoffs, questions, checks and revisions are messages on
     one bus, and the Playbook Worker's fixes are made by the Worker it asked,
     where anyone can read them.
  3. NOTHING LEAVES. Every mail is a draft and every record change is queued,
     through the same gate as the risk layer's.
  4. IT LEARNS, SAFELY. A correction becomes a lesson that fixes every mail like
     it - and a lesson that would undo an earlier one is refused, not saved.
     Learning is rules and context, never retraining, and a correction a person
     made cannot be quietly undone by the model disagreeing later.

Standard library only; no network, no model.
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src import config, learning, llm, orchestrator, workflow

ROOT = Path(__file__).resolve().parent.parent


class _TempLessons(unittest.TestCase):
    """Every test gets its own empty lessons file."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(config, "LESSONS_FILE",
                                        Path(self._tmp.name) / "lessons.json")
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._tmp.cleanup()

    def run_desk(self, **kw):
        return workflow.run(use_llm=False, **kw)


class TheDeskWorksTheWholeInbox(_TempLessons):

    def setUp(self):
        super().setUp()
        self.result = self.run_desk()
        self.items = {i["id"]: i for i in self.result["items"]}

    def test_every_mail_is_routed_or_escalated(self):
        inbox = workflow.load_inbox()["messages"]
        self.assertEqual(len(self.result["items"]), len(inbox))
        for item in self.result["items"]:
            with self.subTest(item=item["id"]):
                self.assertTrue(item["owner"] or item["escalations"],
                                f"{item['id']} was neither routed nor escalated")
                if item["intent"]:
                    self.assertIn(item["intent"], workflow.INTENTS)

    def test_mail_is_linked_by_the_reference_it_quotes(self):
        self.assertEqual(self.items["IN-105"]["linked_booking"], "SHP-003")
        self.assertEqual(self.items["IN-110"]["linked_booking"], "SHP-005")
        self.assertIsNone(self.items["IN-102"]["linked_booking"])   # a new customer

    def test_a_missing_field_is_held_not_guessed(self):
        """IN-102's gross weight is under a label the extractor does not know.
        The booking must be held and the customer asked - never a number made up."""
        booking = next(o for o in self.result["outputs"]
                       if o["item"] == "IN-102" and o.get("operation") == "create_booking")
        status = next(c["to"] for c in booking["changes"] if c["field"] == "booking_status")
        self.assertTrue(status.startswith("INCOMPLETE"), status)
        self.assertFalse(any(c["field"] == "gross_kg" for c in booking["changes"]))
        self.assertTrue(self.items["IN-102"]["escalations"])

    def test_a_document_that_does_not_match_the_booking_is_caught(self):
        exc = [o for o in self.result["outputs"]
               if o["item"] == "IN-103" and o.get("record") == "exception"]
        self.assertEqual(len(exc), 1)
        self.assertIn("mismatch", exc[0]["changes"][0]["to"].lower())

    def test_a_slip_the_desk_cannot_absorb_goes_to_the_risk_layer(self):
        """Rolled seven days against three of slack: that is a routing question,
        and routing is the Routing Worker's call, not the desk's."""
        esc = self.items["IN-105"]["escalations"]
        self.assertTrue(any(e["to"] == "Routing Worker" for e in esc), esc)
        self.assertIn("routing", self.items["IN-105"]["path"])

    def test_an_invoice_line_nobody_agreed_is_disputed(self):
        status = next(o for o in self.result["outputs"]
                      if o["item"] == "IN-110" and o["kind"] == "tms")
        self.assertIn("DISPUTED", status["changes"][0]["to"])
        self.assertTrue(any(o["item"] == "IN-110" and o["kind"] == "mail"
                            and o["audience"] == "carrier" for o in self.result["outputs"]))

    def test_customs_escalates_a_transit_rather_than_filing_it(self):
        self.assertTrue(self.items["IN-112"]["escalations"])      # Basel: out of the EU
        self.assertFalse(self.items["IN-111"]["escalations"])     # Lyon via Fos: an import

    def test_a_routine_milestone_owes_no_reply(self):
        outs = [o for o in self.result["outputs"] if o["item"] == "IN-113"]
        self.assertTrue(outs)
        self.assertFalse(any(o["kind"] == "mail" for o in outs))


class TheWorkersTalk(_TempLessons):

    def setUp(self):
        super().setUp()
        self.result = self.run_desk()
        self.bus = self.result["messages"]

    def test_every_routed_mail_starts_with_an_inbox_handoff(self):
        for item in self.result["items"]:
            if not item["owner"]:
                continue
            first = next(m for m in self.bus if m["item"] == item["id"])
            self.assertEqual((first["from_id"], first["kind"], first["to_id"]),
                             ("inbox", "handoff", item["owner"]))

    def test_workers_ask_each_other_and_answer(self):
        queries = [m for m in self.bus if m["kind"] == "query"]
        self.assertTrue(queries)
        for q in queries:
            reply = next((m for m in self.bus if m["seq"] > q["seq"] and m["kind"] == "reply"
                          and m["from_id"] == q["to_id"] and m["to_id"] == q["from_id"]), None)
            self.assertIsNotNone(reply, f"query {q['seq']} was never answered")

    def test_the_playbook_worker_sends_a_wrong_carrier_back(self):
        """Nordmed books GDP-audited carriers only. The Booking Worker's first pick
        is not one; the Playbook Worker asks for a fix; the Booking Worker asks the
        Rate Worker for an approved carrier and rebooks. All of it on the bus."""
        booking = next(o for o in self.result["outputs"]
                       if o["item"] == "IN-108" and o.get("operation") == "create_booking")
        self.assertIn(booking["carrier"], ("Maersk", "Hapag-Lloyd"))
        check = next(c for c in booking["checks"] if c["rule"] == "approved_carriers")
        self.assertEqual(check["result"], "fixed")
        kinds = [(m["from_id"], m["to_id"], m["kind"]) for m in self.bus if m["item"] == "IN-108"]
        self.assertIn(("playbook", "booking", "revise"), kinds)
        self.assertIn(("booking", "rate", "query"), kinds)
        self.assertIn(("booking", "playbook", "revised"), kinds)

    def test_every_customer_mail_meets_the_customers_copy_rule(self):
        rules = workflow.load_playbooks()
        for out in self.result["outputs"]:
            if out["kind"] != "mail" or out.get("audience") != "customer":
                continue
            for rule in rules.get(out.get("customer"), []):
                if rule["type"] == "cc_on_customer_mail":
                    self.assertIn(rule["value"], out["cc"], out["id"])

    def test_a_slip_over_the_customers_threshold_gets_a_notice(self):
        notices = [o for o in self.result["outputs"] if o["item"] == "IN-105"
                   and o["kind"] == "mail" and o["audience"] == "customer"]
        self.assertEqual(len(notices), 1)


    def test_the_product_page_transcript_is_what_the_workers_really_say(self):
        """/product shows the conversation behind IN-108. It is copied from a run,
        so it has to stay one: every line on the page must be on the bus, in the
        same order, or the page is drawing a diagram of something the code does
        not do."""
        import html
        import re
        page = (ROOT / "static" / "product.html").read_text()
        block = re.search(r'data-bus-item="(IN-\d+)">(.*?)</ol>', page, re.S)
        self.assertIsNotNone(block, "the transcript block is gone from /product")
        item, body = block.group(1), block.group(2)
        said = [html.unescape(t).strip()
                for t in re.findall(r'<span class="say">(.*?)</span>', body, re.S)]
        self.assertGreaterEqual(len(said), 5)
        spoken = [m["text"] for m in self.bus if m["item"] == item]
        at = 0
        for line in said:
            self.assertIn(line, spoken[at:], f"not said on the bus (in order): {line}")
            at = spoken.index(line, at) + 1


    def _scenes(self):
        import json
        import re
        page = (ROOT / "static" / "use-cases.html").read_text()
        block = re.search(r'<script type="application/json" id="uc-scenes">(.*?)</script>',
                          page, re.S)
        self.assertIsNotNone(block, "the scene data is gone from /use-cases")
        return json.loads(block.group(1))

    def test_the_use_cases_stage_says_only_what_the_desk_did(self):
        """/use-cases draws its cards from #uc-scenes. Every line a card puts in an
        agent's mouth - a step's result, a chat message, a field it read, a rule
        it checked, a queued record, a draft's subject, recipient and body, an
        escalation - must be what this run produced for that mail, said by that
        Worker. Titles, one-line descriptions and "working" labels are the page's
        own and are not checked; they describe, they do not quote. The learning
        card is checked on its own, below.

        The hover reasons ("why") are held the same way: each must be the reason
        the desk recorded on this run for that exact line - the bus message's
        `why`, the queued record's `reason`, the draft's `reason`, the
        escalation's `why` - so the logic a visitor reads is the logic that ran."""
        from src import roster
        scenes = self._scenes()
        self.assertEqual(len(scenes), 7)
        inbox = {m["id"]: m for m in workflow.load_inbox()["messages"]}
        items = {i["id"]: i for i in self.result["items"]}
        playbooks = workflow.load_playbooks()
        for sc in scenes:
            if sc["id"] == "learn":
                continue
            item = sc["item"]
            with self.subTest(scene=sc["id"]):
                self.assertEqual(sc["trigger"]["subject"], inbox[item]["subject"])
                self.assertEqual(sc["trigger"]["from"], inbox[item]["sender_org"])
                outs = [o for o in self.result["outputs"] if o["item"] == item]
                said = {(m["from"], m["text"]) for m in self.bus if m["item"] == item}
                said |= {(o["worker"], c["to"]) for o in outs if o["kind"] == "tms"
                         for c in o["changes"]}
                why = {}
                for o in outs:
                    if o["kind"] == "tms":
                        for c in o["changes"]:
                            why.setdefault((o["worker"], c["to"]), set()).add(o.get("reason"))
                for m in self.bus:
                    if m["item"] == item:
                        why.setdefault((m["from"], m["text"]), set()).add(m.get("why"))
                refs = {o["booking_ref"] for o in outs}
                for st in sc.get("steps", []):
                    self.assertIn(st["done"], {t for _, t in said}, st["done"])
                    self.assertIn(st["why"], why.get((st["who"], st["done"]), set()),
                                  f"not the recorded reason for: {st['done']}")
                    if st.get("record"):
                        self.assertIn(st["record"], refs)
                for m in sc.get("messages", []):
                    kind = m.get("kind")
                    if kind is None:
                        self.assertIn((m["who"], m["text"]), said, m["text"])
                        self.assertIn(m["why"], why.get((m["who"], m["text"]), set()),
                                      f"not the recorded reason for: {m['text']}")
                    elif kind == "file":
                        self.assertIn(m["name"], [a["name"] for a in inbox[item]["attachments"]])
                    elif kind == "fields":
                        read = items[item]["extracted"]["fields"]
                        booked = roster.booked_docs(items[item]["linked_booking"])
                        self.assertEqual(m["against"], items[item]["linked_booking"])
                        docs = next(o for o in outs if o["worker"] == "Docs Worker"
                                    and o["kind"] == "tms")
                        self.assertEqual(m["why"], docs["reason"])
                        for row in m["rows"]:
                            self.assertEqual(row["value"], read[row["field"]], row["field"])
                            self.assertEqual(row["label"], workflow.FIELDS[row["field"]][0])
                            if "booked" in row:
                                key = workflow.BOOKED_KEYS[row["field"]]
                                self.assertEqual(row["booked"], booked[key])
                    elif kind == "rules":
                        rules = {r["type"]: r for r in playbooks[m["customer"]]}
                        self.assertEqual(m["customer"], items[item]["customer"])
                        self.assertIn(m["why"], {b.get("why") for b in self.bus
                                                 if b["item"] == item and b["kind"] == "check"})
                        for r in m["rules"]:
                            self.assertIn(r["type"], rules)
                            self.assertEqual(r["why"], rules[r["type"]]["why"])
                            value = rules[r["type"]]["value"]
                            for v in (value if isinstance(value, list) else [value]):
                                if isinstance(v, str):
                                    self.assertIn(v, r["text"])
                    if m.get("record"):
                        self.assertIn(m["record"], refs)
                end = sc.get("end")
                if end and end["kind"] == "draft":
                    mail = next((o for o in outs if o["kind"] == "mail"
                                 and o["subject"] == end["subject"]), None)
                    self.assertIsNotNone(mail, end["subject"])
                    self.assertEqual(end["to"], mail["to"])
                    if end.get("cc"):
                        self.assertIn(end["cc"], mail["cc"])
                    for line in end["lines"]:
                        self.assertIn(line, mail["body"])
                    self.assertEqual(end["why"], mail.get("reason"))
                elif end:
                    esc = [(e["to"], e["text"], e.get("why")) for e in items[item]["escalations"]]
                    self.assertIn((end["to"], end["text"], end["why"]), esc)

    def test_the_use_cases_learning_card_is_what_a_correction_really_does(self):
        """The learning card shows a person correcting IN-104 and the desk's
        answer. Replay that exact correction on a clean slate: the misreading,
        the lesson's words and id, the mails it fixed and the mail count must all
        be what the loop reports - and the lesson must actually be kept."""
        scene = next(sc for sc in self._scenes() if sc["id"] == "learn")
        msgs = {m.get("kind"): m for m in scene["messages"]}
        item = scene["item"]
        before = next(i for i in self.result["items"] if i["id"] == item)
        self.assertEqual(msgs["intent"]["intent"], before["intent"])
        self.assertEqual(msgs["intent"]["label"], workflow.INTENTS[before["intent"]]["label"])
        self.assertIn(("Inbox Worker", msgs["intent"]["text"], msgs["intent"]["why"]),
                      {(m["from"], m["text"], m.get("why")) for m in self.bus if m["item"] == item})
        fix = msgs["human"]["correct"]
        self.assertIn(fix["cue"], msgs["human"]["text"])
        self.assertIn(workflow.INTENTS[fix["right"]]["label"].lower(), msgs["human"]["text"])
        report = workflow.correct(item, kind=fix["kind"], right=fix["right"], cue=fix["cue"])
        self.assertTrue(report["accepted"], report.get("reason"))
        self.assertEqual(msgs["lesson"]["id"], report["lesson"]["id"])
        self.assertEqual(msgs["lesson"]["text"], report["lesson"]["learned"])
        self.assertEqual(msgs["replay"]["fixed"], report["fixed_item"])
        self.assertEqual(msgs["replay"]["also"], [c["item"] for c in report["propagated"]])
        self.assertEqual(msgs["replay"]["mails"], len(report["run"]["items"]))
        self.assertFalse([r for r in report["regression"] if not r["holds"]])
        # The hover reasons: the lesson's is the Inbox Worker's own reason on the
        # replayed run; the replay's and the keep's name what the report says.
        after = {m.get("why") for m in report["run"]["messages"]
                 if m["item"] == item and m["from"] == "Inbox Worker"}
        self.assertIn(msgs["lesson"]["why"], after)
        self.assertIn(report["lesson"]["id"], msgs["replay"]["why"])
        self.assertIn(f"{len(report['changed'])} changed", msgs["replay"]["why"])
        self.assertIn(item, msgs["kept"]["why"])
        self.assertIn("No earlier lesson" if not report["regression"] else
                      f"All {len(report['regression'])} earlier lessons", msgs["kept"]["why"])


class NothingLeaves(_TempLessons):

    def test_every_output_is_gated(self):
        result = self.run_desk()
        self.assertTrue(result["outputs"])
        for out in result["outputs"]:
            with self.subTest(output=out["id"]):
                self.assertEqual(out["approval_status"], "awaiting_approval")
                self.assertEqual(out["status"], "DRAFT - not sent" if out["kind"] == "mail"
                                 else "QUEUED - not written")


    def test_every_record_change_names_a_worker_the_connector_knows(self):
        from src import tms
        known = {(a["agent"], a["record"]) for a in tms.AGENT_RECORDS}
        for out in self.run_desk()["outputs"]:
            if out["kind"] == "tms":
                with self.subTest(output=out["id"]):
                    self.assertIn((out["agent"], out["record"]), known)
                    self.assertTrue(out["changes"])


class ItLearnsSafely(_TempLessons):

    def test_the_planted_mistakes_are_really_there(self):
        items = {i["id"]: i for i in self.run_desk()["items"]}
        self.assertEqual(items["IN-104"]["intent"], "booking_request")
        self.assertEqual(items["IN-109"]["intent"], "booking_request")
        self.assertNotIn("gross_kg", items["IN-107"]["extracted"]["fields"])

    def test_one_intent_correction_fixes_every_mail_like_it(self):
        report = workflow.correct("IN-104", kind="intent", right="rate_request")
        self.assertTrue(report["accepted"], report.get("reason"))
        self.assertEqual(report["lesson"]["cue"], "re-quote")
        self.assertEqual([c["item"] for c in report["propagated"]], ["IN-109"])
        items = {i["id"]: i for i in self.run_desk()["items"]}
        for iid in ("IN-104", "IN-109"):
            self.assertEqual(items[iid]["intent"], "rate_request")
            self.assertEqual(items[iid]["decided_by"], "lesson")
        # ...and nothing else moved.
        self.assertEqual(items["IN-102"]["intent"], "booking_request")

    def test_one_field_correction_fixes_every_document_like_it(self):
        report = workflow.correct("IN-102", kind="field", field="gross_kg", value="14200")
        self.assertTrue(report["accepted"], report.get("reason"))
        self.assertEqual(report["lesson"]["label"], "bruttogewicht")
        self.assertIn("IN-107", [c["item"] for c in report["propagated"]])
        items = {i["id"]: i for i in self.run_desk()["items"]}
        self.assertEqual(items["IN-102"]["extracted"]["fields"]["gross_kg"], 14200)
        self.assertEqual(items["IN-107"]["extracted"]["fields"]["gross_kg"], 26300)

    def test_a_lesson_that_would_undo_an_earlier_one_is_refused_and_not_saved(self):
        self.assertTrue(workflow.correct("IN-104", kind="intent", right="rate_request")["accepted"])
        saved = json.loads(config.LESSONS_FILE.read_text())
        # "booking" also appears in IN-104, so this lesson would flip it back.
        report = workflow.correct("IN-109", kind="intent", right="booking_request", cue="booking")
        self.assertFalse(report["accepted"])
        self.assertIn("L-001", report["reason"])
        self.assertEqual(json.loads(config.LESSONS_FILE.read_text()), saved)

    def test_re_teaching_the_same_phrase_supersedes_and_keeps_the_history(self):
        """A person deliberately re-teaching a phrase is not a regression - it is
        the newer instruction. The old lesson stays on record, marked superseded."""
        workflow.correct("IN-104", kind="intent", right="rate_request")
        report = workflow.correct("IN-109", kind="intent", right="booking_request", cue="re-quote")
        self.assertTrue(report["accepted"], report.get("reason"))
        self.assertEqual(report["superseded"], ["L-001"])
        old = next(l for l in learning.load() if l["id"] == "L-001")
        self.assertEqual((old["status"], old["superseded_by"]), ("superseded", "L-002"))

    def test_a_cue_that_is_not_in_the_mail_is_refused(self):
        report = workflow.correct("IN-104", kind="intent", right="rate_request",
                                  cue="tariff schedule")
        self.assertFalse(report["accepted"])
        self.assertEqual(learning.load(), [])

    def test_the_model_cannot_undo_a_correction(self):
        """With a model configured and disagreeing, the lesson still decides."""
        workflow.correct("IN-104", kind="intent", right="rate_request")
        disagree = {m["id"]: ("booking_request", "model says so")
                    for m in workflow.load_inbox()["messages"]}
        with mock.patch.object(llm, "is_configured", return_value=True), \
             mock.patch.object(llm, "active_model", return_value="stub"), \
             mock.patch.object(workflow, "_model_intents", return_value=(disagree, None)):
            items = {i["id"]: i for i in workflow.run(use_llm=True)["items"]}
        self.assertEqual(items["IN-104"]["intent"], "rate_request")
        self.assertEqual(items["IN-104"]["decided_by"], "lesson")

    def test_learning_is_rules_and_context_not_retraining(self):
        """learning.py may import nothing that could train or call a model."""
        tree = ast.parse((ROOT / "src" / "learning.py").read_text())
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)
                    for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree)
                     if isinstance(n, ast.ImportFrom) and n.module}
        self.assertLessEqual(imported, {"json", "re", "datetime", "src"})
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "src":
                self.assertEqual([a.name for a in node.names], ["config"])


class TheRiskLayerHandsItsDecisionsToTheDesk(_TempLessons):

    @classmethod
    def setUpClass(cls):
        cls.result = orchestrator.run_cycle(live=False, use_llm=False, scenario="hamburg")

    def test_every_reroute_is_handed_to_booking_customs_and_milestones(self):
        msgs = self.result["workflow_handoffs"]["messages"]
        for sid in ("SHP-001", "SHP-005"):
            got = {m["to_id"] for m in msgs if m["item"] == sid}
            self.assertEqual(got, {"booking", "customs", "milestones"}, sid)
        self.assertNotIn("customs", {m["to_id"] for m in msgs if m["item"] == "SHP-002"})

    def test_the_playbook_fix_lands_on_the_draft_a_person_approves(self):
        card = next(c for c in self.result["shipments"] if c["id"] == "SHP-002")
        customer = next(d for d in card["drafts"] if d["audience"] == "customer")
        self.assertIn("qa-logistics@nordmed-pharma.example", customer.get("cc", []))


if __name__ == "__main__":
    unittest.main()
