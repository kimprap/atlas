"""Each judge fallback cell for claim support and copy flags, through ``add`` (AC-3.7).

Cells: the judge set up and answering; failing after its backoff; a profile
that chose Opus; no judge set up and no choice saved. Claim support flags under
0.8 and copy flags at 0.5 or more only in the first cell; every other cell
marks "support not checked" and "copies not checked", makes no Opus call, and
``add`` still stores the source.
"""

from __future__ import annotations

import unittest
from typing import Any

from tests.fakes.fake_host import FakeHost, support, tool_reply
from tests.test_summarize import C1, C2, C3, LINK, PAGE, WORDS, PipelineTest, claim_of, record

from atlas import ports  # noqa: E402

OTHER = "https://example.org/build-cache-repost"
OTHER_TEXT = "# Build cache\nA team measured a faster build cache on large repos.\nIt is not ready for Windows."
OTHER_PAGE = ports.Page(OTHER, "Faster builds, reposted", None, None, None, "article", OTHER_TEXT)
OTHER_CLAIM = {"section": "claim", "text": "A team measured a faster build cache.", "basis": "measured", "quotes": ["measured a faster build cache on large repos"]}
OTHER_RECORD = {"abstract": "A repost of a note on a new build cache and its speed-up.", "claims": [OTHER_CLAIM]}


class JudgeFallbackTests(PipelineTest):
    def setUp(self) -> None:
        super().setUp()
        self.configure("rethink = false\n")
        # A stored source the new one may be a copy of.
        stored = FakeHost(
            pages={OTHER: OTHER_PAGE},
            replies={"atlas_summarize": [tool_reply(OTHER_RECORD)]},
            judge_answer=lambda state, question: support(0.95),
        )
        _, code = self.add(stored, {"items": [{"link": OTHER}], "approval": {"by": "request", "words": f"add {OTHER}"}})
        self.assertEqual(code, 0)

    def add_new(self, **host: Any) -> tuple[FakeHost, dict[str, Any]]:
        # The second reply answers the repair turn a flag brings; without flags it is never asked for.
        replies = {"atlas_summarize": [tool_reply(record(C1, C2, C3)), tool_reply(record(C1, C2, C3))]}
        fake = FakeHost(pages={LINK: PAGE}, replies=replies, **host)
        answer, code = self.add(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["added"], 1)
        return fake, answer["result"]["items"][0]

    def new_source(self) -> tuple:
        [row] = self.rows("SELECT support_status, copies_status FROM sources WHERE key_link = ?", LINK)
        return row

    def assert_not_checked(self, fake: FakeHost, item: dict[str, Any]) -> None:
        self.assertEqual((item["support"], item["copies"]), ("support not checked", "copies not checked"))
        self.assertEqual(self.new_source(), ("not checked", "not checked"))
        self.assertEqual(self.rows("SELECT count(*) FROM claim_flags f JOIN claims c ON c.id = f.claim_id JOIN sources s ON s.id = c.source_id WHERE s.key_link = ?", LINK), [(0,)])
        self.assertEqual(self.rows("SELECT count(*) FROM copy_flags"), [(0,)])
        self.assertEqual([call[1] for call in self.calls(fake, "call")], ["atlas_summarize"], "no Opus call stands in")

    def test_judge_set_up_and_answering_flags_support_under_0_8_and_copies_at_0_5(self) -> None:
        def answer(state: str, question: ports.Question) -> ports.Answer:
            if question.id == "same_work":
                return ports.Answer(p=0.5)
            return support(0.5 if claim_of(state) == C3["text"] else 0.95)

        fake, item = self.add_new(judge_answer=answer)
        self.assertEqual((item["flagged_claims"], item["copies"]), (1, [f"may be a copy of {OTHER}"]))
        self.assertNotIn("support", item)
        self.assertEqual(self.new_source(), ("checked", "checked"))
        self.assertEqual(
            self.rows("SELECT c.text, f.flagged FROM claims c JOIN claim_flags f ON f.claim_id = c.id JOIN sources s ON s.id = c.source_id WHERE s.key_link = ? ORDER BY c.ord", LINK),
            [(C1["text"], 0), (C2["text"], 0), (C3["text"], 1)],
        )
        self.assertEqual(
            self.rows("SELECT o.key_link, f.p, f.flagged, f.judge_model FROM copy_flags f JOIN sources o ON o.id = f.other_source_id"),
            [(OTHER, 0.5, 1, "fake-judge-1")],
        )

    def test_a_copy_answer_under_0_5_is_kept_but_not_flagged(self) -> None:
        answer = lambda state, question: ports.Answer(p=0.49) if question.id == "same_work" else support(0.95)  # noqa: E731
        _, item = self.add_new(judge_answer=answer)
        self.assertEqual(item["copies"], [])
        self.assertEqual(self.rows("SELECT p, flagged FROM copy_flags"), [(0.49, 0)])

    def test_judge_failing_after_its_backoff_marks_both_not_checked(self) -> None:
        fake, item = self.add_new(judge_error=ports.JudgeFailed(429, "busy after 1, 2, 4 and 8 s"))
        self.assertTrue(self.calls(fake, "judge"), "the judge was asked")
        self.assert_not_checked(fake, item)

    def test_copies_failing_alone_keep_the_support_flags(self) -> None:
        def answer(state: str, question: ports.Question) -> ports.Answer:
            if question.id == "same_work":
                raise ports.JudgeFailed(529, "busy")
            return support(0.95)

        _, item = self.add_new(judge_answer=answer)
        self.assertEqual(item["copies"], "copies not checked")
        self.assertEqual(self.new_source(), ("checked", "not checked"))

    def test_a_profile_that_chose_opus_checks_neither(self) -> None:
        self.configure("rethink = false\n", judge="opus")
        fake, item = self.add_new(judge=False)
        self.assert_not_checked(fake, item)

    def test_no_judge_choice_saved_checks_neither_and_add_does_not_stop(self) -> None:
        self.configure("rethink = false\n", judge=None)
        fake, item = self.add_new(judge_answer=lambda state, question: support(0.95))
        self.assertEqual(self.calls(fake, "judge"), [])
        self.assert_not_checked(fake, item)

    def test_a_judge_key_file_problem_checks_neither_and_add_does_not_stop(self) -> None:
        missing = ports.SetupProblem("The Jev key file is missing", ("Put the key in the file.",), "/fake/key.env")
        fake, item = self.add_new(setup_problem=missing)
        self.assertEqual(self.calls(fake, "judge"), [])
        self.assert_not_checked(fake, item)


if __name__ == "__main__":
    unittest.main()
