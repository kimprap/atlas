"""The fake host: every port and the host facts capability from in-memory scripts.

Pages and image bytes are scripted by link, replies (each with its usage, cost
and any raw tool text) by role and turn, judgments by question id or by a
function of the state and question, with one cost per judge call, windows by
provider; roles, the host version, the role-fix target, a facts failure and the
judge's setup problem are plain values. The store is the real SQLite store on
whatever path the profile names, so tests point ``HOME`` at a temporary folder.
Every port call is appended to ``FakeHost.calls`` as ``(port, *arguments)``.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "skills" / "atlas-ask") not in sys.path:
    sys.path.insert(0, str(ROOT / "skills" / "atlas-ask"))

from atlas import ports  # noqa: E402
from atlas.store import Store, sqlite  # noqa: E402

ALL_ROLES = {
    "atlas_summarize": "fake/sonnet:high",
    "atlas_query": "fake/opus:medium",
    "atlas_rerank": "fake/opus:medium",
    "atlas_answer": "fake/opus:medium",
    "atlas_escalate": "fake/opus:medium",
}
FAKE_COST = ports.Cost(0.0, "billed")
PIPELINE_USAGE = ports.Usage(input=1200, output=300, cache_read=0, cache_write=0)


def tool_reply(tool_input: Mapping[str, Any], content: str = "", model: str = "fake/sonnet", thinking: str | None = "high") -> ports.Reply:
    """A model reply that called its tool with ``tool_input``; its cost is left to the price table."""
    return ports.Reply(model, thinking, content, dict(tool_input), "tool", PIPELINE_USAGE, ports.Cost(None, "unknown"))


def text_reply(content: str, stop: str = "end", model: str = "fake/sonnet", tool_raw: str | None = None) -> ports.Reply:
    """A model reply with no usable tool call: plain text, a cut-off or a refusal, or with ``tool_raw``
    the host's raw text of tool arguments that did not parse (stop ``tool``)."""
    return ports.Reply(model, "high", content, None, stop, PIPELINE_USAGE, ports.Cost(None, "unknown"), tool_raw)


def support(p: float) -> ports.Answer:
    """A claim-support answer whose "supports" probability is ``p``, the rest on "says nothing"."""
    return ports.Answer(probabilities={"supports": p, "contradicts": 0.0, "says nothing": round(1 - p, 6)}, confidence=0.9)


class FakeHost:
    def __init__(
        self,
        *,
        pages: Mapping[str, ports.Page | ports.Unreadable] | None = None,
        images: Mapping[str, bytes | ports.Unreadable] | None = None,
        transcripts: Mapping[str, ports.Page | ports.Unreadable] | None = None,
        replies: Mapping[str, Sequence[ports.Reply | Exception]] | None = None,
        judgments: Mapping[str, ports.Answer] | None = None,
        judge_answer: Callable[[str, ports.Question], ports.Answer] | None = None,
        judge_model: str = "fake-judge-1",
        judge_error: Exception | None = None,
        judge_cost: ports.Cost = FAKE_COST,
        setup_problem: ports.SetupProblem | None = None,
        windows: Sequence[ports.Window] = (),
        roles: Mapping[str, str] | None = None,
        role_fix_lines: bool = True,
        role_fix_where: str | None = "/fake/host/settings.conf",
        version: str | None = None,
        facts_error: ports.CallFailed | None = None,
        contexts: Mapping[str, int] | None = None,
        judge: bool = True,
        quota: bool = True,
        facts: bool = True,
    ) -> None:
        self.pages = dict(pages or {})
        self.image_bytes = dict(images or {})
        self.transcripts = dict(transcripts or {})
        self.replies = {role: list(items) for role, items in (replies or {}).items()}
        self.judgments = dict(judgments or {})
        self.judge_answer = judge_answer
        self.judge_model = judge_model
        self.judge_error = judge_error
        self.judge_cost = judge_cost
        self.problem = setup_problem
        self.window_rows = list(windows)
        self.role_map = dict(ALL_ROLES if roles is None else roles)
        self.role_fix_lines = role_fix_lines
        self.role_fix_where = role_fix_where
        self.host_version = version
        self.facts_error = facts_error
        self.contexts = dict(contexts or {})
        self.name = "fake"
        self.calls: list[tuple[Any, ...]] = []
        self._turns: dict[str, int] = {}
        self._ports = {"judge": judge, "quota": quota, "facts": facts}

    def host(self) -> ports.Host:
        """The ``Host`` value core receives, with the ports this fake was built to offer."""
        return ports.Host(
            read=self,
            call=self,
            open_store=self.open_store,
            judge=self if self._ports["judge"] else None,
            quota=self if self._ports["quota"] else None,
            facts=self if self._ports["facts"] else None,
        )

    def open_store(self, path: Path) -> Store:
        self.calls.append(("open_store", path))
        return sqlite.open_store(path)

    # read port
    def read(self, link: str, scope: ports.Scope = None) -> ports.Page | ports.Unreadable:
        self.calls.append(("read", link, scope))
        if scope == "transcript":
            return self.transcripts.get(link, ports.Unreadable("no_transcript", f"no transcript is scripted for {link}"))
        return self.pages.get(link, ports.Unreadable("error", f"no page is scripted for {link}"))

    def image(self, link: str) -> bytes | ports.Unreadable:
        self.calls.append(("image", link))
        return self.image_bytes.get(link, ports.Unreadable("gone", f"no image is scripted for {link}"))

    # call port
    def call(
        self,
        role: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
        tool_choice: str | None,
        max_output: int,
        images: Sequence[bytes] = (),
    ) -> ports.Reply:
        self.calls.append(("call", role, [dict(message) for message in messages], tools, tool_choice, max_output, images))
        if role not in self.role_map:
            raise ports.RoleMissing(role)
        turn = self._turns.get(role, 0)
        self._turns[role] = turn + 1
        scripted = self.replies.get(role, [])
        if turn >= len(scripted):
            raise ports.CallFailed(None, f"no reply is scripted for turn {turn + 1} of {role}")
        item = scripted[turn]
        if isinstance(item, Exception):
            raise item
        return item

    # judge port
    def judge(self, state: str, questions: Sequence[ports.Question]) -> ports.Judgments:
        self.calls.append(("judge", state, tuple(questions)))
        if not isinstance(state, str) or not questions:
            raise ValueError("a judge request holds one state and at least one question")
        if any(not isinstance(question, ports.Question) for question in questions):
            raise ValueError("judge questions are ports.Question values")
        if self.problem is not None:
            raise ports.JudgeNotSetUp(self.problem.what)
        if self.judge_error is not None:
            raise self.judge_error
        if self.judge_answer is not None:
            answers = {question.id: self.judge_answer(state, question) for question in questions}
            return ports.Judgments(self.judge_model, answers, self.judge_cost)
        missing = [question.id for question in questions if question.id not in self.judgments]
        if missing:
            raise ports.JudgeFailed(None, f"no judgment is scripted for {', '.join(missing)}")
        answers = {question.id: self.judgments[question.id] for question in questions}
        return ports.Judgments(self.judge_model, answers, self.judge_cost)

    def setup_problem(self) -> ports.SetupProblem | None:
        self.calls.append(("setup_problem",))
        return self.problem

    # quota port
    def windows(self, providers: Sequence[str]) -> list[ports.Window]:
        self.calls.append(("windows", tuple(providers)))
        return [row for row in self.window_rows if row.provider in providers]

    # host facts capability
    def version(self) -> str | None:
        self.calls.append(("version",))
        if self.facts_error is not None:
            raise self.facts_error
        return self.host_version

    def roles(self) -> dict[str, str]:
        self.calls.append(("roles",))
        if self.facts_error is not None:
            raise self.facts_error
        return dict(self.role_map)

    def role_fix(self, missing: Mapping[str, str]) -> ports.RoleFix:
        self.calls.append(("role_fix", dict(missing)))
        if not self.role_fix_lines:
            return ports.RoleFix((), None)
        lines = ("[roles]", *(f"{role} = {selector}" for role, selector in missing.items()))
        return ports.RoleFix(lines, self.role_fix_where)

    def role_provider(self, role: str) -> str | None:
        self.calls.append(("role_provider", role))
        selector = self.role_map.get(role)
        return selector.partition("/")[0] if selector and "/" in selector else None

    def role_context(self, role: str) -> int | None:
        self.calls.append(("role_context", role))
        return self.contexts.get(role)
