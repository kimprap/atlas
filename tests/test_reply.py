"""The reply seam: six keys, exit codes 0-4, strict JSON input and decision ids.

Replies that end before a host process is needed (bad input, not set up) run
through ``cli.py`` as a subprocess with the recorded stand-in ``omp`` first on
``PATH``; the rest run through ``app.run`` with the fake host,
and the decision shape and id binding on ``reply`` directly.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from tests.fakes.fake_host import FakeHost

from atlas.core import app, reply  # noqa: E402  (fake_host puts the package on sys.path)

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "atlas-ask" / "cli.py"
FAKE_OMP = ROOT / "tests" / "fixtures" / "omp"
COMMANDS = ("status", "add", "inbox", "find", "ask", "topic", "plan", "note", "archive", "restore")
REPLY_KEYS = {"ok", "op", "result", "problems", "next", "decisions"}
SETUP_NEXT = [{"label": "run `atlas-init`", "then": {"skill": "atlas-init"}}]


class CliReplyTests(unittest.TestCase):
    """``cli.py`` as a subprocess, for replies that end before any store is opened."""

    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def call(self, *args: str, body: bytes = b"{}") -> tuple[dict, int]:
        env = {key: value for key, value in os.environ.items() if key != "ATLAS_PROFILE"}
        env["HOME"] = str(self.home)
        env["PATH"] = f"{FAKE_OMP}{os.pathsep}{env.get('PATH', '')}"
        proc = subprocess.run(
            [sys.executable, str(CLI), *args], input=body, capture_output=True, env=env, timeout=30
        )
        lines = proc.stdout.decode().splitlines()
        self.assertEqual(len(lines), 1, proc.stdout + proc.stderr)
        answer = json.loads(lines[0])
        self.assertEqual(set(answer), REPLY_KEYS)
        return answer, proc.returncode

    def assert_not_set_up(self, answer: dict, code: int, op: str, named: str) -> None:
        self.assertEqual(code, 3)
        self.assertIs(answer["ok"], False)
        self.assertEqual(answer["op"], op)
        item = answer["result"]["needs_action"][0]
        self.assertIn("not set up", item["what"])
        self.assertIn(named, item["what"])
        self.assertIn("atlas-init", " ".join(item["fix"]))
        self.assertEqual(item["where"], str(self.home / ".config" / "atlas" / "config.toml"))
        self.assertEqual(answer["next"], SETUP_NEXT)

    def test_every_command_is_not_set_up_without_settings(self) -> None:
        for command in COMMANDS:
            with self.subTest(command=command):
                answer, code = self.call(command)
                self.assert_not_set_up(answer, code, command, "no settings file")
                roles = [item["what"] for item in answer["result"]["needs_action"][1:]]
                if command == "status":
                    self.assertEqual(len(roles), 5)
                    self.assertTrue(all(what.startswith("Role atlas_") for what in roles))
                else:
                    self.assertEqual(roles, [])

    def test_settings_without_a_usable_profile_are_not_set_up(self) -> None:
        settings = self.home / ".config" / "atlas" / "config.toml"
        settings.parent.mkdir(parents=True)
        cases = {
            "": "no profile is chosen",
            'default_profile = "smoke"\n': 'profile "smoke" is not in the settings file',
            'default_profile = "smoke"\n[profiles.smoke]\njudge = "jev"\n': 'profile "smoke" has no store path',
            "default_profile = \n": "not valid TOML",
        }
        for text, named in cases.items():
            with self.subTest(settings=text):
                settings.write_text(text)
                answer, code = self.call("find")
                self.assert_not_set_up(answer, code, "find", named)

    def test_bad_body_is_bad_input_before_setup(self) -> None:
        cases = {
            "duplicate key": (b'{"a":1,"a":2}', 'duplicate key "a"'),
            "NaN": (b'{"a":NaN}', "NaN"),
            "Infinity": (b'{"a":Infinity}', "Infinity"),
            "not an object": (b"[1]", "object"),
            "invalid UTF-8": (b'{"a":"\xff"}', "UTF-8"),
            "empty": (b"", "JSON"),
            "integer over 4300 digits": (b'{"a":' + b"1" * 5000 + b"}", "body"),
            "float overflowing to infinity": (b'{"a":1e999}', "body"),
        }
        for name, (body, named) in cases.items():
            with self.subTest(name):
                answer, code = self.call("status", body=body)
                self.assertEqual(code, 2)
                self.assertIs(answer["ok"], False)
                [problem] = answer["problems"]
                self.assertEqual(problem["field"], "body")
                self.assertIn(named, problem["problem"])

    def test_malformed_call_is_bad_input(self) -> None:
        cases = {
            ("statuz",): (b"{}", "command"),
            ("status", "--wide"): (b"{}", "mode"),
            ("status", "extra"): (b"{}", "action"),
            ("status",): (b'{"profile": 3}', "profile"),
            ("status", "--detail"): (b'{"profile": ""}', "profile"),
        }
        for args, (body, field) in cases.items():
            with self.subTest(args=args, body=body):
                answer, code = self.call(*args, body=body)
                self.assertEqual(code, 2)
                [problem] = answer["problems"]
                self.assertEqual(problem["field"], field)


class AppReplyTests(unittest.TestCase):
    """``app.run`` with the fake host, for replies past setup."""

    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        os.environ.pop("ATLAS_PROFILE", None)
        self.store = self.home / "data" / "smoke.db"
        settings = self.home / ".config" / "atlas" / "config.toml"
        settings.parent.mkdir(parents=True)
        settings.write_text(f'default_profile = "smoke"\n[profiles.smoke]\nstore = "{self.store}"\njudge = "opus"\n')

    def run_app(self, command: str, body: dict | None = None) -> tuple[dict, int]:
        answer, code = app.run(command, None, body or {}, FakeHost(judge=False).host())
        self.assertEqual(set(answer), REPLY_KEYS)
        self.assertEqual(json.loads(json.dumps(answer)), answer)
        return answer, code

    def test_done_is_exit_0_and_the_only_ok_reply(self) -> None:
        answer, code = self.run_app("status")
        self.assertEqual(code, 0)
        self.assertIs(answer["ok"], True)
        self.assertEqual(answer["decisions"], [])

    def test_failed_is_exit_1(self) -> None:
        answer, code = self.run_app("ask", {"source": "https://example.com/a"})
        self.assertEqual((code, answer["ok"]), (1, False))
        self.assertIn("not available", answer["problems"][0]["problem"])

        self.store.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.store)) as db:
            db.execute("PRAGMA user_version = 9999")
        answer, code = self.run_app("find")
        self.assertEqual((code, answer["ok"]), (1, False))
        self.assertEqual(
            answer["problems"],
            [{"link": None, "field": "store", "problem": "store is newer than this Atlas; check out a newer tag"}],
        )

        self.store.write_bytes(b"not a store, " * 100)
        answer, code = self.run_app("find")
        self.assertEqual((code, answer["ok"]), (1, False))
        [problem] = answer["problems"]
        self.assertEqual(problem["field"], "store")
        self.assertIn("cannot be opened", problem["problem"])


class DecisionTests(unittest.TestCase):
    """The ``decisions[]`` shape, exit 4 and the id that binds a decision to its change."""

    BODY = {"items": [{"link": "https://example.com/a"}], "profile": "smoke"}

    def make(self, kind: str = "confirm", **then: object) -> dict:
        return reply.decision(
            "add",
            None,
            self.BODY,
            kind,
            "Add https://example.com/a?",
            [
                reply.option("yes", "add it", then or {"resend": {"approval": {"by": "confirm"}}}),
                reply.option("no", "leave it", {"stop": True}),
            ],
        )

    def test_exit_4_carries_typed_decisions(self) -> None:
        item = self.make()
        answer = reply.build("add", reply.NEEDS_DECISION, decisions=[item])
        self.assertIs(answer["ok"], False)
        [shown] = answer["decisions"]
        self.assertEqual(set(shown), {"id", "kind", "question", "options"})
        self.assertEqual(shown["kind"], "confirm")
        self.assertEqual(
            [(option["id"], option["then"]) for option in shown["options"]],
            [("yes", {"resend": {"approval": {"by": "confirm"}}}), ("no", {"stop": True})],
        )
        skill = reply.option("setup", "set up the judge", {"skill": "atlas-init"})
        self.assertEqual(skill["then"], {"skill": "atlas-init"})

    def test_decisions_belong_to_exit_4_only(self) -> None:
        with self.assertRaises(ValueError):
            reply.build("add", reply.NEEDS_DECISION)
        with self.assertRaises(ValueError):
            reply.build("add", reply.DONE, decisions=[self.make()])
        with self.assertRaises(ValueError):
            reply.build("add", 5)

    def test_unknown_kinds_and_untyped_actions_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            self.make(kind="maybe")
        for then in ({"resend": "approval"}, {"skill": ""}, {"stop": False}, {"goto": "x"}, {}):
            with self.subTest(then=then), self.assertRaises(ValueError):
                reply.option("x", "x", then)

    def test_id_binds_the_change_and_ignores_the_approval(self) -> None:
        item = self.make()
        self.assertRegex(item["id"], r"^[0-9a-f]{16}$")
        same = {"profile": "smoke", "items": [{"link": "https://example.com/a"}], "approval": {"by": "request"}}
        self.assertEqual(reply.decision_id("add", None, same, "confirm"), item["id"])
        others = {
            "command": reply.decision_id("inbox add", None, self.BODY, "confirm"),
            "mode": reply.decision_id("add", "reread", self.BODY, "confirm"),
            "body": reply.decision_id("add", None, {**self.BODY, "profile": "main"}, "confirm"),
            "kind": reply.decision_id("add", None, self.BODY, "cap"),
        }
        for changed, other in others.items():
            with self.subTest(changed=changed):
                self.assertNotEqual(other, item["id"])

    def test_a_version_save_id_also_ignores_the_review_the_resend_adds(self) -> None:
        body = {"name": "caching", "draft": {"claims": []}}
        review = {"status": "complete", "text": "Reviewed."}
        resent = {**body, "review": review, "approval": {"by": "confirm", "decision": "x", "choice": "go", "words": "yes"}}
        saved = reply.decision_id("topic save", None, body, "version_save")
        self.assertEqual(reply.decision_id("topic save", None, resent, "version_save"), saved)
        self.assertEqual(reply.approved_kind("topic save", None, {**resent, "approval": {"decision": saved}}, ("version_save",)), "version_save")
        # Every other kind still binds the whole body, so a resend that adds or changes a review field is another change.
        self.assertNotEqual(reply.decision_id("plan save", None, {**body, "review": review}, "confirm"), reply.decision_id("plan save", None, body, "confirm"))
        self.assertNotEqual(reply.decision_id("topic save", None, {**body, "draft": {"claims": [1]}}, "version_save"), saved)

    def test_an_approval_names_one_of_the_kinds_its_change_could_stop_with(self) -> None:
        item = self.make(kind="cap")
        kinds = ("confirm", "cap", "window")
        resent = {**self.BODY, "approval": {"by": "confirm", "decision": item["id"], "choice": "yes", "words": "yes"}}
        self.assertEqual(reply.approved_kind("add", None, resent, kinds), "cap")
        self.assertIsNone(reply.approved_kind("add", None, resent, ("confirm", "window")))
        moved = {**resent, "items": [{"link": "https://example.com/b"}]}
        self.assertIsNone(reply.approved_kind("add", None, moved, kinds))
        self.assertIsNone(reply.approved_kind("add", None, self.BODY, kinds))


if __name__ == "__main__":
    unittest.main()
