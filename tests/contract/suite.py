"""The adapter contract suite: one case class per port, bound once per adapter.

A binding module mixes a case class into ``unittest.TestCase`` and supplies the
factory and the scenario values the class names. Every adapter of a port passes
the same cases: the fake host offline, the OMP and Jev adapters against recorded
output offline and against the real host with ``ATLAS_LIVE=1``. Cases that need
a host to misbehave on cue (a cut-off or refused reply, a busy judge) and cases
that read the judge's wire request sit in their own classes, which only the
offline bindings take, because a live host cannot be made to answer that way.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from tests.fakes import fake_host  # noqa: F401  (puts the atlas package on sys.path)

from atlas import ports  # noqa: E402

FORCED_TOOL_MESSAGE = "Record that the sky is blue, with confidence 0.9."
CUT_OFF_MESSAGE = "Describe the sky at length."
REFUSED_MESSAGE = "Decline this request."
RECORD_TOOL = {
    "name": "record",
    "description": "Record one fact.",
    "input_schema": {
        "type": "object",
        "properties": {"fact": {"type": "string"}, "confidence": {"type": "number"}},
        "required": ["fact", "confidence"],
    },
}
MISSING_ROLE = "atlas_no_such_role"

JUDGE_STATE = "The note says: the build failed because the disk was full."
CAUSE = ports.Question("q_cause", "noul", "Does the note name a cause of the failure?")
KIND = ports.Question("q_kind", "choice", "What kind of cause does the note name?", ("disk", "network", "none"))
MISSING_PROVIDER = "atlas-no-such-provider"

# What must never reach ``Page.text``: the read header and GitHub or X counter lines.
HEADER_LINE = re.compile(r"^(URL|Content-Type|Method|Notes): ", re.M)
COUNTER_LINE = re.compile(r"^\s*(Stars|Forks|Issues|Watchers|Likes|Reposts|Replies|Quotes|Views|Bookmarks): \d", re.M)
VERSION = re.compile(r"^\d+(\.\d+)+$")


class ReadContract:
    """Binding supplies ``make_read()`` and the links below."""

    REDIRECT_LINK: str
    REDIRECTED_TO: str
    REPO_LINK: str
    GONE_LINK: str
    GONE_REASON: str
    PAGE_LINKS: Sequence[str]

    def make_read(self) -> ports.ReadPort:
        raise NotImplementedError

    def _page(self, link: str) -> ports.Page:
        page = self.make_read().read(link)
        self.assertIsInstance(page, ports.Page, f"{link} was not read: {page}")
        return page

    def test_final_link_is_where_a_redirect_lands(self) -> None:
        page = self._page(self.REDIRECT_LINK)
        self.assertEqual(page.final_link, self.REDIRECTED_TO)
        self.assertNotEqual(page.final_link, self.REDIRECT_LINK)

    def test_header_and_counter_lines_never_reach_the_text(self) -> None:
        for link in self.PAGE_LINKS:
            with self.subTest(link=link):
                page = self._page(link)
                self.assertTrue(page.text.strip())
                self.assertIsNone(HEADER_LINE.search(page.text))
                self.assertIsNone(COUNTER_LINE.search(page.text))
                self.assertEqual(page.counts.words, len(page.text.split()))

    def test_an_unreadable_page_is_unreadable(self) -> None:
        got = self.make_read().read(self.GONE_LINK)
        self.assertIsInstance(got, ports.Unreadable)
        self.assertEqual(got.reason, self.GONE_REASON)
        self.assertTrue(got.detail)

    def test_a_repo_page_has_its_kind_and_items(self) -> None:
        page = self._page(self.REPO_LINK)
        self.assertEqual(page.kind_hint, "repo")
        self.assertTrue(page.items)
        for item in page.items:
            self.assertIn(item.kind, {"skill", "plugin", "package"})
            self.assertTrue(item.link.startswith(self.REPO_LINK.rstrip("/") + "/"), item.link)


class CallContract:
    """Binding supplies ``make_call()`` and ``TOOL_ROLE``, a role the host has."""

    TOOL_ROLE: str

    def make_call(self) -> ports.CallPort:
        raise NotImplementedError

    def test_a_forced_tool_reply_fills_tool_input(self) -> None:
        reply = self.make_call().call(
            self.TOOL_ROLE, [{"role": "user", "content": FORCED_TOOL_MESSAGE}], [RECORD_TOOL], "record", 200
        )
        self.assertEqual(reply.stop, "tool")
        self.assertIsInstance(reply.tool_input, dict)
        self.assertIsInstance(reply.tool_input.get("fact"), str)
        self.assertIsInstance(reply.tool_input.get("confidence"), (int, float))
        self.assertTrue(reply.model)
        self.assertGreater(reply.usage.input + reply.usage.cache_read + reply.usage.cache_write, 0)
        self.assertGreater(reply.usage.output, 0)
        self.assertIn(reply.cost.kind, ports.COST_KINDS)

    def test_an_unknown_role_raises_role_missing(self) -> None:
        with self.assertRaises(ports.RoleMissing) as caught:
            self.make_call().call(MISSING_ROLE, [{"role": "user", "content": FORCED_TOOL_MESSAGE}], [], None, 50)
        self.assertEqual(caught.exception.role, MISSING_ROLE)


class CallStopContract:
    """Binding supplies ``make_call()`` and the roles that answer cut off and refused."""

    CUT_OFF_ROLE: str
    REFUSED_ROLE: str

    def make_call(self) -> ports.CallPort:
        raise NotImplementedError

    def test_a_reply_cut_at_max_output_is_cut_off(self) -> None:
        reply = self.make_call().call(self.CUT_OFF_ROLE, [{"role": "user", "content": CUT_OFF_MESSAGE}], [], None, 16)
        self.assertEqual(reply.stop, "cut_off")
        self.assertIsNone(reply.tool_input)

    def test_a_refusal_is_refused(self) -> None:
        reply = self.make_call().call(self.REFUSED_ROLE, [{"role": "user", "content": REFUSED_MESSAGE}], [], None, 200)
        self.assertEqual(reply.stop, "refused")
        self.assertIsNone(reply.tool_input)


class JudgeContract:
    """Binding supplies ``make_judge(key)`` for ``key`` in ``ok``, ``missing``, ``loose``,
    and ``JUDGE_MODEL``, a pattern the answering model version matches."""

    JUDGE_MODEL: str

    def make_judge(self, key: str) -> ports.JudgePort:
        raise NotImplementedError

    def judged(self) -> ports.Judgments:
        return self.make_judge("ok").judge(JUDGE_STATE, [CAUSE, KIND])

    def test_answers_are_parsed_into_p_and_probabilities(self) -> None:
        got = self.judged()
        self.assertEqual(set(got.answers), {CAUSE.id, KIND.id})
        cause, kind = got.answers[CAUSE.id], got.answers[KIND.id]
        self.assertIsNotNone(cause.p)
        self.assertTrue(0.0 <= cause.p <= 1.0)
        self.assertIsNone(cause.probabilities)
        self.assertEqual(set(kind.probabilities), set(KIND.options))
        self.assertTrue(math.isclose(sum(kind.probabilities.values()), 1.0, abs_tol=0.02))
        self.assertTrue(0.0 <= kind.confidence <= 1.0)

    def test_the_model_version_and_billed_cost_are_kept(self) -> None:
        got = self.judged()
        self.assertRegex(got.model, self.JUDGE_MODEL)
        self.assertEqual(got.cost.kind, "billed")
        self.assertIsNotNone(got.cost.usd)
        self.assertGreaterEqual(got.cost.usd, 0.0)

    def test_a_usable_key_file_is_no_setup_problem(self) -> None:
        self.assertIsNone(self.make_judge("ok").setup_problem())

    def test_a_missing_key_file_is_a_setup_problem(self) -> None:
        judge = self.make_judge("missing")
        problem = judge.setup_problem()
        self.assertIsNotNone(problem)
        self.assertTrue(problem.fix)
        self.assertTrue(problem.where)
        with self.assertRaises(ports.JudgeNotSetUp):
            judge.judge(JUDGE_STATE, [CAUSE])

    def test_a_loose_key_file_is_a_setup_problem_fixed_by_chmod_600(self) -> None:
        judge = self.make_judge("loose")
        problem = judge.setup_problem()
        self.assertIsNotNone(problem)
        self.assertTrue(any("chmod 600" in line for line in problem.fix), problem.fix)
        self.assertTrue(problem.where)
        with self.assertRaises(ports.JudgeNotSetUp):
            judge.judge(JUDGE_STATE, [CAUSE])


class JudgeWireContract:
    """Binding supplies ``make_busy_judge(statuses)`` returning ``(judge, sleeps)``,
    where ``sleeps()`` lists the backoff waits taken, or ``None`` for a judge
    with no transport; and ``requests()``, each judge request seen as
    ``(state, {question id: type})``."""

    def make_busy_judge(self, statuses: Sequence[int]) -> tuple[ports.JudgePort, Any]:
        raise NotImplementedError

    def requests(self) -> list[tuple[str, dict[str, str]]]:
        raise NotImplementedError

    def test_one_request_holds_one_state_and_typed_questions(self) -> None:
        judge, _ = self.make_busy_judge([200])
        judge.judge(JUDGE_STATE, [CAUSE, KIND])
        self.assertEqual(self.requests(), [(JUDGE_STATE, {CAUSE.id: "noul", KIND.id: "choice"})])

    def test_busy_429_and_529_are_retried_with_backoff_then_fail(self) -> None:
        judge, sleeps = self.make_busy_judge([429, 529, 429, 529, 429])
        with self.assertRaises(ports.JudgeFailed) as caught:
            judge.judge(JUDGE_STATE, [CAUSE])
        self.assertEqual(caught.exception.status, 429)
        if sleeps() is not None:
            self.assertEqual(sleeps(), [1, 2, 4, 8])
            self.assertEqual(len(self.requests()), 5)

    def test_a_busy_judge_that_recovers_answers(self) -> None:
        judge, sleeps = self.make_busy_judge([529, 200])
        got = judge.judge(JUDGE_STATE, [CAUSE, KIND])
        self.assertEqual(set(got.answers), {CAUSE.id, KIND.id})
        if sleeps() is not None:
            self.assertEqual(sleeps(), [1])


class QuotaContract:
    """Binding supplies ``make_quota()`` and ``PROVIDER``, a provider with windows."""

    PROVIDER: str

    def make_quota(self) -> ports.QuotaPort:
        raise NotImplementedError

    def test_windows_are_parsed_for_the_asked_providers_only(self) -> None:
        rows = self.make_quota().windows([self.PROVIDER, MISSING_PROVIDER])
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row.provider, self.PROVIDER)
            self.assertTrue(row.window_id)
            self.assertGreater(row.duration_s, 0)
            self.assertTrue(0.0 <= row.used_fraction <= 1.0)
            self.assertIsNotNone(datetime.fromisoformat(row.resets_at).tzinfo)

    def test_a_missing_provider_gives_no_row(self) -> None:
        self.assertEqual(self.make_quota().windows([MISSING_PROVIDER]), [])


class FactsContract:
    """Binding supplies ``make_facts()`` and ``KNOWN_ROLE``, a role the host has."""

    KNOWN_ROLE: str

    def make_facts(self) -> ports.HostFacts:
        raise NotImplementedError

    def test_the_version_is_bare(self) -> None:
        self.assertRegex(self.make_facts().version() or "", VERSION)

    def test_roles_and_their_provider_and_context(self) -> None:
        facts = self.make_facts()
        roles = facts.roles()
        self.assertIn(self.KNOWN_ROLE, roles)
        self.assertEqual(facts.role_provider(self.KNOWN_ROLE), roles[self.KNOWN_ROLE].partition("/")[0])
        self.assertIsNone(facts.role_provider(MISSING_ROLE))
        context = facts.role_context(self.KNOWN_ROLE)
        self.assertIsInstance(context, int)
        self.assertGreater(context, 0)

    def test_role_fix_names_every_missing_role_and_its_file(self) -> None:
        missing = {"atlas_summarize": "a/b:high", "atlas_answer": "a/c:medium"}
        fix = self.make_facts().role_fix(missing)
        for role, selector in missing.items():
            self.assertTrue(any(role in line and selector in line for line in fix.lines), fix.lines)
        self.assertTrue(fix.where)
