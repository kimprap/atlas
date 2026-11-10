"""The fake host passes the contract suite, so core tests that run on it hold on a real host."""

from __future__ import annotations

import unittest
from collections.abc import Sequence
from typing import Any

from tests.contract import suite
from tests.fakes.fake_host import ALL_ROLES, FakeHost

from atlas import ports  # noqa: E402

REDIRECT = "http://fake.example/old"
REPO = "https://github.com/fake/repo"
GONE = "https://fake.example/gone"
IMAGE = "https://fake.example/pixel.png"
PIXEL = b"\x89PNG\r\n\x1a\n fake image bytes"
VIDEO = "https://www.youtube.com/watch?v=fake"
TRANSCRIPTS: dict[str, ports.Page | ports.Unreadable] = {
    VIDEO: ports.Page(VIDEO, "Fake talk", None, None, None, "video", "# Fake talk\n\nHello and welcome.", counts=ports.Counts(6, 0, 0)),
}
USAGE = ports.Usage(input=12, output=8, cache_read=0, cache_write=0)
COST = ports.Cost(None, "unknown")
PAGES: dict[str, ports.Page | ports.Unreadable] = {
    REDIRECT: ports.Page(
        final_link="https://fake.example/new",
        title="New",
        author=None,
        publisher=None,
        published=None,
        kind_hint="article",
        text="The page moved here.",
        counts=ports.Counts(4, 0, 0),
    ),
    REPO: ports.Page(
        final_link=REPO,
        title="fake/repo",
        author="fake",
        publisher="GitHub",
        published=None,
        kind_hint="repo",
        text="# fake/repo\n\nA repo.",
        counts=ports.Counts(4, 0, 0),
        items=(ports.RepoItem("skills/one", f"{REPO}/tree/HEAD/skills/one", "skill"),),
    ),
    GONE: ports.Unreadable("gone", "HTTP 404"),
}
REPLIES = {
    "atlas_answer": [
        ports.Reply("fake/opus", None, "", {"fact": "The sky is blue.", "confidence": 0.9}, "tool", USAGE, COST)
    ],
    "atlas_query": [ports.Reply("fake/opus", None, "The sky is", None, "cut_off", USAGE, COST)],
    "atlas_rerank": [ports.Reply("fake/opus", None, "", None, "refused", USAGE, COST)],
}
JUDGMENTS = {
    "q_cause": ports.Answer(p=0.97),
    "q_kind": ports.Answer(probabilities={"disk": 0.9, "network": 0.1, "none": 0.0}, confidence=0.8),
}
PROBLEMS = {
    "ok": None,
    "missing": ports.SetupProblem("The key file is missing", ("Put the key in /fake/key.env.",), "/fake/key.env"),
    "loose": ports.SetupProblem("The key file has mode 644", ("chmod 600 /fake/key.env",), "/fake/key.env"),
}


class FakeRead(suite.ReadContract, unittest.TestCase):
    REDIRECT_LINK = REDIRECT
    REDIRECTED_TO = "https://fake.example/new"
    REPO_LINK = REPO
    GONE_LINK = GONE
    GONE_REASON = "gone"
    PAGE_LINKS = (REDIRECT, REPO)
    IMAGE_LINK = IMAGE
    VIDEO_LINK = VIDEO
    TRANSCRIPT_PHRASE = "Hello and welcome."
    NO_TRANSCRIPT_LINK = REDIRECT

    def make_read(self) -> ports.ReadPort:
        return FakeHost(pages=PAGES, images={IMAGE: PIXEL}, transcripts=TRANSCRIPTS).host().read


class FakeCall(suite.CallContract, suite.CallStopContract, unittest.TestCase):
    TOOL_ROLE = "atlas_answer"
    CUT_OFF_ROLE = "atlas_query"
    REFUSED_ROLE = "atlas_rerank"

    def make_call(self) -> ports.CallPort:
        return FakeHost(replies=REPLIES, roles=ALL_ROLES).host().call


class FakeJudge(suite.JudgeContract, suite.JudgeWireContract, unittest.TestCase):
    JUDGE_MODEL = r"^fake-judge-1$"

    def make_judge(self, key: str) -> ports.JudgePort:
        return FakeHost(judgments=JUDGMENTS, setup_problem=PROBLEMS[key]).host().judge

    def make_busy_judge(self, statuses: Sequence[int]) -> tuple[ports.JudgePort, Any]:
        error = None if statuses[-1] == 200 else ports.JudgeFailed(statuses[-1], "busy")
        self.fake = FakeHost(judgments=JUDGMENTS, judge_error=error)
        return self.fake.host().judge, lambda: None

    def requests(self) -> list[tuple[str, dict[str, str]]]:
        return [
            (call[1], {question.id: question.type for question in call[2]})
            for call in self.fake.calls
            if call[0] == "judge"
        ]


class FakeQuota(suite.QuotaContract, unittest.TestCase):
    PROVIDER = "fake"

    def make_quota(self) -> ports.QuotaPort:
        rows = [ports.Window("fake", "fake:5h", 18000, 0.25, "2026-11-09T19:00:00+00:00")]
        return FakeHost(windows=rows).host().quota


class FakeFacts(suite.FactsContract, unittest.TestCase):
    KNOWN_ROLE = "atlas_summarize"

    def make_facts(self) -> ports.HostFacts:
        return FakeHost(version="1.2.3", contexts={"atlas_summarize": 200000}).host().facts


if __name__ == "__main__":
    unittest.main()
