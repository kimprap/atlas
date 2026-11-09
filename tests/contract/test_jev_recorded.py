"""The Jev adapter against recorded Decisions replies on a loopback server, offline.

The replies in ``tests/fixtures/jev`` were captured from OpenRouter on 2026-11-09
(``index.json`` names each one's source; the busy reply is derived). ``HOME`` is
a temporary folder whose key file holds a made-up key; no network and no real
key are used.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from unittest import mock

from tests.contract import suite
from tests.contract.replay import FIXTURES, Replay, in_order

from atlas import ports  # noqa: E402
from atlas.adapters.jev import MODEL, JevJudge  # noqa: E402

TEST_KEY = "sk-or-v1-recorded-test-key"
OK = (200, (FIXTURES / "jev" / "decisions_ok.json").read_bytes())
BAD_REQUEST = (400, (FIXTURES / "jev" / "decisions_bad_request.json").read_bytes())
BUSY = (FIXTURES / "jev" / "decisions_busy.json").read_bytes()


def write_key_file(home: Path, text: str, mode: int) -> Path:
    path = home / ".config" / "atlas" / "openrouter.env"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.chmod(path, mode)
    return path


class RecordedJudge(suite.JudgeContract, suite.JudgeWireContract, unittest.TestCase):
    JUDGE_MODEL = r"^typesafe/jev-1\.14-20261014$"

    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        self.waits: list[float] = []

    def _judge(self, replies: Sequence[tuple[int, bytes]], key: str = "ok") -> JevJudge:
        self.server = self.enterContext(Replay(in_order(*replies)))
        if key != "missing":
            write_key_file(self.home, f"OTHER=1\nOPENROUTER_API_KEY={TEST_KEY}\n", 0o600 if key == "ok" else 0o644)
        return JevJudge(endpoint=self.server.url + "/api/alpha/decisions", sleep=self.waits.append)

    def test_the_key_file_is_atlas_own(self) -> None:
        problem = self.make_judge("missing").setup_problem()
        self.assertEqual(problem.where, str(self.home / ".config" / "atlas" / "openrouter.env"))

    def test_a_linked_key_file_is_checked_and_read_through_the_link(self) -> None:
        target = write_key_file(self.home / "dotfiles", f"OPENROUTER_API_KEY={TEST_KEY}\n", 0o600)
        link = self.home / ".config" / "atlas" / "openrouter.env"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        judge = self._judge([OK], key="missing")
        self.assertIsNone(judge.setup_problem())
        judge.judge(suite.JUDGE_STATE, [suite.CAUSE, suite.KIND])
        self.assertEqual(self.server.requests[0]["headers"]["Authorization"], f"Bearer {TEST_KEY}")
        os.chmod(target, 0o644)
        self.assertIn("mode 644", self._judge([OK], key="missing").setup_problem().what)

    def make_judge(self, key: str) -> ports.JudgePort:
        return self._judge([OK], key)

    def make_busy_judge(self, statuses: Sequence[int]) -> tuple[ports.JudgePort, Any]:
        replies = [OK if status == 200 else (status, BUSY) for status in statuses]
        return self._judge(replies), lambda: self.waits

    def requests(self) -> list[tuple[str, dict[str, str]]]:
        seen = []
        for request in self.server.requests:
            body = json.loads(request["body"])
            seen.append((body["state"], {qid: q["type"] for qid, q in body["questions"].items()}))
        return seen

    def test_the_wire_request_is_pinned(self) -> None:
        self.make_judge("ok").judge(suite.JUDGE_STATE, [suite.CAUSE, suite.KIND])
        (request,) = self.server.requests
        self.assertEqual((request["method"], request["path"]), ("POST", "/api/alpha/decisions"))
        self.assertEqual(request["headers"]["Authorization"], f"Bearer {TEST_KEY}")
        self.assertEqual(
            json.loads(request["body"]),
            {
                "model": MODEL,
                "state": suite.JUDGE_STATE,
                "questions": {
                    "q_cause": {"type": "noul", "instructions": suite.CAUSE.text},
                    "q_kind": {
                        "type": "choice",
                        "instructions": suite.KIND.text,
                        "criteria": {"disk": "disk", "network": "network", "none": "none"},
                    },
                },
            },
        )
        self.assertEqual(MODEL, "~typesafe/jev-latest")

    def test_the_recorded_answers_and_cost_are_kept(self) -> None:
        got = self.make_judge("ok").judge(suite.JUDGE_STATE, [suite.CAUSE, suite.KIND])
        self.assertEqual(got.answers["q_cause"], ports.Answer(p=0.99))
        self.assertEqual(
            got.answers["q_kind"],
            ports.Answer(probabilities={"disk": 1.0, "network": 0.0, "none": 0.0}, confidence=1.0),
        )
        self.assertEqual(got.cost, ports.Cost(0.000014742, "billed"))

    def test_a_refused_request_fails_without_retry(self) -> None:
        judge = self._judge([BAD_REQUEST])
        with self.assertRaises(ports.JudgeFailed) as caught:
            judge.judge(suite.JUDGE_STATE, [suite.CAUSE])
        self.assertEqual(caught.exception.status, 400)
        self.assertIn("invalid_union", caught.exception.detail)
        self.assertEqual((len(self.server.requests), self.waits), (1, []))

    def test_the_key_is_read_once_per_command(self) -> None:
        judge = self._judge([OK, OK])
        judge.judge(suite.JUDGE_STATE, [suite.CAUSE, suite.KIND])
        write_key_file(self.home, "OPENROUTER_API_KEY=sk-or-v1-a-later-key\n", 0o600)
        judge.judge(suite.JUDGE_STATE, [suite.CAUSE, suite.KIND])
        keys = [request["headers"]["Authorization"] for request in self.server.requests]
        self.assertEqual(keys, [f"Bearer {TEST_KEY}"] * 2)


if __name__ == "__main__":
    unittest.main()
