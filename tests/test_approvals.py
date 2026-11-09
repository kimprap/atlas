"""Approvals (spec 4.2) on the core module: request words, paid at scale, ``never``,
fixed stops, merged stops and a wrong decision id, with the ``approvals`` row.

No change command exists before ``add`` lands, so these run ``approvals.check``
on a profile resolved from a temporary ``HOME``, the real SQLite store and the
fake host.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest import mock

from tests.fakes.fake_host import FakeHost

from atlas import ports  # noqa: E402  (fake_host puts the package on sys.path)
from atlas.core import approvals, config, reply, spend  # noqa: E402

NOW = datetime(2026, 11, 15, 12, 0).astimezone()
LINK = "https://example.com/report"
OTHER = "https://example.com/other"
BODY: dict[str, Any] = {"items": [{"link": LINK}]}
PAIR: dict[str, Any] = {"items": [{"link": LINK}, {"link": OTHER}]}


class ApprovalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        self.store_path = self.home / "data" / "smoke.db"
        self.configure()

    def configure(self, extra: str = "") -> None:
        settings = config.config_path()
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(
            f'default_profile = "smoke"\n[profiles.smoke]\nstore = "{self.store_path}"\njudge = "jev"\n{extra}'
        )
        self.profile = config.resolve(None, None)

    def change(self, body: dict[str, Any] = BODY, approval: Any = None, **fields: Any) -> approvals.Change:
        if approval is not None:
            body = {**body, "approval": approval}
        values = {"command": "add", "mode": None, "body": body, "kind": "add", "question": f"Add {LINK}?", "links": [LINK]}
        return approvals.Change(**{**values, **fields})

    def guard(self, fake: FakeHost | None = None, batch: bool = False) -> spend.Guard:
        fake = fake or FakeHost()
        store = fake.open_store(self.store_path)
        self.addCleanup(store.close)
        return spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], batch=batch, clock=lambda: NOW)

    def bill(self, usd: float) -> None:
        """Record one billed judge call this month, so the cap counts ``usd``."""
        with closing(FakeHost().open_store(self.store_path)) as store:
            spend.record_judgments(store, "add", ports.Judgments("jev-1", {}, ports.Cost(usd, "billed")), now=NOW)

    @staticmethod
    def go(decision: dict[str, Any], words: str = "yes") -> dict[str, Any]:
        """The approval a front door resends for the go option, with the user's reply."""
        [option] = [item for item in decision["options"] if item["id"] == approvals.GO]
        return {**option["then"]["resend"]["approval"], "words": words}

    def test_request_words_naming_every_target_run_without_a_confirm(self) -> None:
        words = "Please add HTTPS://EXAMPLE.COM/report?utm_source=feed to Atlas."
        verdict = approvals.check(self.change(approval={"by": "request", "words": words}), self.profile, None)
        self.assertEqual(verdict, approvals.Go("request", words, None))

        with closing(FakeHost().open_store(self.store_path)) as store:
            approvals.record(store, self.change(mode="reread", kind="add_reread"), verdict, now=NOW)
        with closing(sqlite3.connect(self.store_path)) as db:
            rows = db.execute("SELECT at, command, change_kind, by, words, decision_id FROM approvals").fetchall()
        self.assertEqual(rows, [(spend.stamp(NOW), "add --reread", "add_reread", "request", words, None)])

    def test_request_words_missing_a_target_get_one_confirm(self) -> None:
        note = self.change(kind="note", links=[], names=["Simon Willison"], question="Save the note?")
        cases = {
            "a link not in the words": (self.change(PAIR, links=[LINK, OTHER]), f"add {LINK}"),
            "vague words": (self.change(), "yes, add it"),
            "a name not in the words": (note, "note what Simon says"),
        }
        for label, (change, words) in cases.items():
            with self.subTest(label):
                asked = replace(change, body={**change.body, "approval": {"by": "request", "words": words}})
                verdict = approvals.check(asked, self.profile, None)
                self.assertIsInstance(verdict, approvals.Stop)
                decision = verdict.decision
                self.assertEqual(decision["kind"], "confirm")
                self.assertEqual(decision["question"], change.question)
                self.assertEqual(decision["id"], reply.decision_id("add", None, change.body, "confirm"))
                self.assertEqual([option["id"] for option in decision["options"]], ["go", "stop"])
        named = replace(note, body={**BODY, "approval": {"by": "request", "words": "note what SIMON WILLISON says"}})
        self.assertIsInstance(approvals.check(named, self.profile, None), approvals.Go)

    def test_paid_at_scale_needs_a_confirm_even_on_request(self) -> None:
        asked = {"by": "request", "words": f"add {LINK} and {OTHER}"}
        at_scale = approvals.check(self.change(PAIR, asked, links=[LINK, OTHER], paid_at_scale=True), self.profile, None)
        self.assertEqual(at_scale.decision["kind"], "confirm")
        not_at_scale = approvals.check(self.change(PAIR, asked, links=[LINK, OTHER]), self.profile, None)
        self.assertEqual(not_at_scale, approvals.Go("request", asked["words"], None))

    def test_a_confirm_on_the_returned_decision_runs_the_change(self) -> None:
        first = approvals.check(self.change(), self.profile, None)
        verdict = approvals.check(self.change(approval=self.go(first.decision, "yes, add it")), self.profile, None)
        self.assertEqual(verdict, approvals.Go("confirm", "yes, add it", first.decision["id"]))

    def test_never_runs_without_approval(self) -> None:
        self.configure('[profiles.smoke.confirm]\nadd = "never"\n')
        self.assertEqual(approvals.check(self.change(), self.profile, None), approvals.Go("never", None, None))
        self.assertIsInstance(approvals.check(self.change(kind="inbox_add"), self.profile, None), approvals.Stop)

    def test_a_bad_confirm_setting_is_not_set_up(self) -> None:
        with self.assertRaises(config.NotSetUp) as caught:
            self.configure('[profiles.smoke.confirm]\nadd = "sometimes"\n')
        self.assertIn("confirm.add", caught.exception.what)

    def test_an_approval_for_another_change_or_choice_is_bad_input(self) -> None:
        first = approvals.check(self.change(), self.profile, None)
        moved = approvals.check(self.change({"items": [{"link": OTHER}]}, self.go(first.decision)), self.profile, None)
        self.assertEqual(moved, approvals.Refused(reply.problem("approval", reply.OTHER_CHANGE)))

        bad = {
            "a stop choice": {**self.go(first.decision), "choice": "stop"},
            "an unknown by": {"by": "maybe", "words": "yes"},
            "no words": {"by": "request"},
            "not an object": "yes",
        }
        for label, approval in bad.items():
            with self.subTest(label):
                verdict = approvals.check(self.change(approval=approval), self.profile, None)
                self.assertIsInstance(verdict, approvals.Refused)
                self.assertEqual(verdict.problem["field"], "approval")

    def test_cap_yields_stop_whatever_the_setting_with_one_decision(self) -> None:
        self.configure('cap_usd = 10.0\n[profiles.smoke.confirm]\nadd = "never"\n')
        self.bill(8.5)
        never = approvals.check(self.change(), self.profile, self.guard())
        self.assertEqual(never.decision["kind"], "cap")
        self.assertEqual([option["id"] for option in never.decision["options"]], ["go", "raise_cap", "stop"])
        self.assertIn("85% of the $10.00 monthly cap", never.decision["question"])

        self.configure("cap_usd = 10.0\n")
        request = approvals.check(self.change(approval={"by": "request", "words": f"add {LINK}"}), self.profile, self.guard())
        self.assertEqual(request.decision["kind"], "cap")
        self.assertNotIn(f"Add {LINK}?", request.decision["question"])

        guard = self.guard()
        verdict = approvals.check(self.change(approval=self.go(request.decision)), self.profile, guard)
        self.assertEqual(verdict, approvals.Go("confirm", "yes", request.decision["id"]))
        self.assertEqual(guard.continued, {"cap"})

    def test_a_confirm_and_a_limit_merge_into_one_decision(self) -> None:
        self.configure("cap_usd = 10.0\n")
        self.bill(9.0)
        decision = approvals.check(self.change(), self.profile, self.guard()).decision
        self.assertEqual(decision["kind"], "cap")
        self.assertTrue(decision["question"].startswith(f"Add {LINK}? This month's billed spend is $9.00, 90%"))
        verdict = approvals.check(self.change(approval=self.go(decision)), self.profile, self.guard())
        self.assertEqual(verdict, approvals.Go("confirm", "yes", decision["id"]))

        self.configure()
        full = FakeHost(windows=[ports.Window("fake", "5h", 18_000, 0.95, "2026-11-15T13:30:00+00:00")])
        batch = self.change(PAIR, links=[LINK, OTHER], paid_at_scale=True)
        decision = approvals.check(batch, self.profile, self.guard(full, batch=True)).decision
        self.assertEqual(decision["kind"], "window")
        self.assertIn("Fake 5-hour window at 95%", decision["question"])
        self.assertEqual([option["id"] for option in decision["options"]], ["go", "after_reset", "stop"])
        resent = replace(batch, body={**PAIR, "approval": self.go(decision)})
        guard = self.guard(full, batch=True)
        self.assertEqual(approvals.check(resent, self.profile, guard), approvals.Go("confirm", "yes", decision["id"]))
        self.assertEqual(guard.continued, {"window"})


if __name__ == "__main__":
    unittest.main()
