"""``inbox add`` and ``inbox list`` through ``app.run`` with the fake host and a temporary ``HOME``."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from typing import Any
from unittest import mock

from tests.fakes.fake_host import FakeHost

from atlas import ports  # noqa: E402  (fake_host puts the package on sys.path)
from atlas.core import app, identity  # noqa: E402

A = "https://example.com/a"
B = "https://example.com/b"


class InboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        os.environ.pop("ATLAS_PROFILE", None)
        self.store = self.home / "data" / "smoke.db"
        self.configure()

    def configure(self, extra: str = "") -> None:
        settings = self.home / ".config" / "atlas" / "config.toml"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(
            f'default_profile = "smoke"\n[profiles.smoke]\nstore = "{self.store}"\njudge = "jev"\n{extra}'
        )

    def run_app(self, command: str, body: dict[str, Any]) -> tuple[dict[str, Any], int]:
        return app.run(command, None, body, FakeHost().host())

    def listed(self) -> list[str]:
        answer, code = self.run_app("inbox list", {})
        self.assertEqual(code, 0)
        self.assertEqual(answer["result"]["count"], len(answer["result"]["links"]))
        return [row["link"] for row in answer["result"]["links"]]

    def approvals(self) -> list[tuple]:
        with closing(sqlite3.connect(self.store)) as db:
            return db.execute("SELECT command, change_kind, by, words FROM approvals").fetchall()

    def test_links_the_user_names_are_kept_and_listed(self) -> None:
        words = f"save {A}?utm_source=x and {B} for later"
        answer, code = self.run_app(
            "inbox add", {"add": [f"{A}?utm_source=x", B], "approval": {"by": "request", "words": words}}
        )
        self.assertEqual(code, 0)
        self.assertEqual(answer["result"]["added"], 2)
        self.assertEqual(self.listed(), [A, B])
        self.assertEqual(self.approvals(), [("inbox add", "inbox_add", "request", words)])

    def test_without_the_users_words_a_confirm_comes_first(self) -> None:
        body: dict[str, Any] = {"add": [A]}
        answer, code = self.run_app("inbox add", body)
        self.assertEqual(code, 4)
        [decision] = answer["decisions"]
        self.assertEqual((decision["kind"], decision["question"]), ("confirm", f"Keep {A} in the inbox?"))
        self.assertEqual(self.listed(), [])

        [go] = [option for option in decision["options"] if option["id"] == "go"]
        approval = {**go["then"]["resend"]["approval"], "words": "yes"}
        answer, code = self.run_app("inbox add", {**body, "approval": approval})
        self.assertEqual((code, answer["result"]["added"]), (0, 1))
        self.assertEqual(self.listed(), [A])
        self.assertEqual(self.approvals(), [("inbox add", "inbox_add", "confirm", "yes")])

    def test_never_adds_without_approval(self) -> None:
        self.configure('[profiles.smoke.confirm]\ninbox_add = "never"\n')
        answer, code = self.run_app("inbox add", {"add": [A]})
        self.assertEqual((code, answer["result"]["added"]), (0, 1))
        self.assertEqual(self.approvals(), [("inbox add", "inbox_add", "never", None)])

    def test_kept_stored_and_bad_links_are_reported_and_not_added(self) -> None:
        self.configure('[profiles.smoke.confirm]\ninbox_add = "never"\n')
        self.run_app("inbox add", {"add": [A]})
        stored = "https://example.com/stored"
        with closing(FakeHost().open_store(self.store)) as store:
            batch = identity.Batch(store, 0.9, [(stored, None)])
            [item] = batch.to_read()
            outcome = batch.examine(item, ports.Page(stored, None, None, None, None, "article", "Some text."))
            assert outcome.new is not None
            batch.keep(outcome.new)

        answer, code = self.run_app("inbox add", {"add": [f"{A}#x", stored, "not a link", B]})
        self.assertEqual(code, 0)
        self.assertEqual(
            answer["result"],
            {
                "added": 1,
                "items": [
                    {"link": A, "result": "already in the inbox"},
                    {"link": stored, "result": f"already stored as {stored}"},
                    {"link": B, "result": "added to the inbox"},
                ],
            },
        )
        self.assertEqual([(p["link"], p["field"]) for p in answer["problems"]], [("not a link", "add")])
        self.assertEqual(self.listed(), [A, B])

    def test_a_link_leaves_the_inbox_when_a_source_holds_it(self) -> None:
        self.configure('[profiles.smoke.confirm]\ninbox_add = "never"\n')
        self.run_app("inbox add", {"add": [A, B]})
        with closing(FakeHost().open_store(self.store)) as store:
            batch = identity.Batch(store, 0.9, [(A, None)])
            [item] = batch.to_read()
            outcome = batch.examine(item, ports.Page(A, None, None, None, None, "article", "Some text."))
            assert outcome.new is not None
            batch.keep(outcome.new)
        self.assertEqual(self.listed(), [B])

    def test_bad_bodies_are_bad_input(self) -> None:
        for command, body in (
            ("inbox add", {}),
            ("inbox add", {"add": []}),
            ("inbox add", {"add": [A], "links": [B]}),
            ("inbox list", {"add": [A]}),
            ("inbox", {}),
        ):
            with self.subTest(command=command, body=body):
                answer, code = self.run_app(command, body)
                self.assertEqual((code, answer["ok"]), (2, False))
        self.assertEqual(self.listed(), [])


if __name__ == "__main__":
    unittest.main()
