"""cli.py as a subprocess: reply keys, exit codes and strict JSON input."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "atlas-ask" / "cli.py"
COMMANDS = ("status", "add", "inbox", "find", "ask", "topic", "plan", "note", "archive", "restore")
REPLY_KEYS = {"ok", "op", "result", "problems", "next", "decisions"}


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def call(self, *args: str, body: bytes = b"{}") -> tuple[dict, int]:
        env = {**os.environ, "HOME": str(self.home)}
        proc = subprocess.run(
            [sys.executable, str(CLI), *args], input=body, capture_output=True, env=env, timeout=30
        )
        lines = proc.stdout.decode().splitlines()
        self.assertEqual(len(lines), 1, proc.stdout + proc.stderr)
        reply = json.loads(lines[0])
        self.assertEqual(set(reply), REPLY_KEYS)
        return reply, proc.returncode

    def test_every_command_is_not_set_up_without_settings(self) -> None:
        for command in COMMANDS:
            with self.subTest(command=command):
                reply, code = self.call(command)
                self.assertEqual(code, 3)
                self.assertIs(reply["ok"], False)
                self.assertEqual(reply["op"], command)
                [item] = reply["result"]["needs_action"]
                self.assertIn("not set up", item["what"])
                self.assertIn("atlas-init", " ".join(item["fix"]))
                self.assertEqual(reply["next"], [{"label": "run `atlas-init`", "then": {"skill": "atlas-init"}}])

    def test_settings_file_under_home_ends_the_not_set_up_reply(self) -> None:
        settings = self.home / ".config" / "atlas" / "config.toml"
        settings.parent.mkdir(parents=True)
        settings.write_text("")
        reply, code = self.call("status")
        self.assertNotEqual(code, 3)
        self.assertNotIn("needs_action", reply["result"])

    def test_bad_body_is_bad_input_before_setup(self) -> None:
        cases = {
            "duplicate key": (b'{"a":1,"a":2}', 'duplicate key "a"'),
            "NaN": (b'{"a":NaN}', "NaN"),
            "Infinity": (b'{"a":Infinity}', "Infinity"),
            "not an object": (b"[1]", "object"),
            "invalid UTF-8": (b'{"a":"\xff"}', "UTF-8"),
            "empty": (b"", "JSON"),
        }
        for name, (body, named) in cases.items():
            with self.subTest(name):
                reply, code = self.call("status", body=body)
                self.assertEqual(code, 2)
                self.assertIs(reply["ok"], False)
                [problem] = reply["problems"]
                self.assertEqual(problem["field"], "body")
                self.assertIn(named, problem["problem"])

    def test_unknown_command_or_flag_is_bad_input(self) -> None:
        for args in (("statuz",), ("status", "--wide"), ("status", "extra")):
            with self.subTest(args=args):
                reply, code = self.call(*args)
                self.assertEqual(code, 2)
                self.assertEqual(len(reply["problems"]), 1)


if __name__ == "__main__":
    unittest.main()
