"""The summary pipeline through ``add`` with the fake host and a temporary ``HOME`` (AC-3.3)."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from typing import Any
from unittest import mock

from tests.fakes.fake_host import FakeHost, support, text_reply, tool_reply

from atlas import ports  # noqa: E402  (fake_host puts the package on sys.path)
from atlas.core import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LINK = "https://example.com/builds"
TEXT = (
    "# Faster builds\n"
    "The new cache cuts build time by 40% on large repos, according to the team\u2019s benchmark.\n"
    "Use the cache only when your builds are deterministic.\n"
    "The cache does not work on Windows yet."
)
PAGE = ports.Page(LINK, "Faster builds", "Ann Lee", None, None, "article", TEXT, counts=ports.Counts(40, 0, 0))
WORDS = f"Summarize this link {LINK}"

# The page quote has a curly apostrophe; the model's quote a straight one.
QUOTE_1 = "cuts build time by 40% on large repos, according to the team's benchmark"
C1 = {"section": "claim", "text": "The new cache cuts build time by 40% on large repos, per the team's benchmark.", "basis": "measured", "quotes": [QUOTE_1]}
C2 = {"section": "recommendation", "text": "Use the cache only with deterministic builds.", "basis": "asserted", "quotes": ["Use the cache only when your builds are deterministic."]}
C3 = {"section": "caveat", "text": "The cache does not work on Windows yet.", "basis": "asserted", "quotes": ["does not work on Windows yet"]}
BAD_QUOTE = "cuts build times by forty percent"
C1_BAD = {**C1, "quotes": [BAD_QUOTE]}
ABSTRACT = "A note on a new build cache. It reports the speed-up and its limits."


def record(*claims: dict[str, Any]) -> dict[str, Any]:
    return {"abstract": ABSTRACT, "claims": list(claims)}


def claim_of(state: str) -> str:
    return state.split("\n", 1)[0].removeprefix("Claim: ")


class PipelineTest(unittest.TestCase):
    """A temporary ``HOME`` with profile ``smoke`` and helpers to run ``add`` and read the store back."""

    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        os.environ.pop("ATLAS_PROFILE", None)
        self.store = self.home / "data" / "smoke.db"
        self.configure()

    def configure(self, extra: str = "", judge: str | None = "jev") -> None:
        settings = self.home / ".config" / "atlas" / "config.toml"
        settings.parent.mkdir(parents=True, exist_ok=True)
        line = f'judge = "{judge}"\n' if judge else ""
        settings.write_text(f'default_profile = "smoke"\n[profiles.smoke]\nstore = "{self.store}"\n{line}{extra}')

    def add(self, fake: FakeHost, body: dict[str, Any] | None = None, mode: str | None = None) -> tuple[dict[str, Any], int]:
        if body is None:
            body = {"items": [{"link": LINK}], "approval": {"by": "request", "words": WORDS}}
        return app.run("add", mode, body, fake.host())

    def rows(self, sql: str, *args: Any) -> list[tuple]:
        with closing(sqlite3.connect(self.store)) as db:
            return db.execute(sql, args).fetchall()

    def calls(self, fake: FakeHost, port: str, role: str | None = None) -> list[tuple]:
        return [call for call in fake.calls if call[0] == port and (role is None or call[1] == role)]


def judge_by_claim(values: dict[str, float]) -> Any:
    return lambda state, question: support(values.get(claim_of(state), 0.95))


class SummaryPipelineTests(PipelineTest):
    def test_a_clean_draft_runs_rethink_and_support_then_stores_quotes_flags_and_records(self) -> None:
        fake = FakeHost(
            pages={LINK: PAGE},
            replies={"atlas_summarize": [tool_reply(record(C1, C2, C3)), tool_reply(record(C1, C2, C3), "Looks right.\nRethink: no change")]},
            judge_answer=judge_by_claim({}),
        )
        answer, code = self.add(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(
            answer["result"]["items"],
            [{"link": LINK, "result": "added", "title": "Faster builds", "claims": 3, "dropped_claims": 0, "flagged_claims": 0, "copies": []}],
        )
        draft, rethink = self.calls(fake, "call", "atlas_summarize")
        _, _, messages, tools, tool_choice, max_output, _ = draft
        rubric = (ROOT / "skills" / "atlas-ask" / "prompts" / "summarize.md").read_text(encoding="utf-8").rstrip("\n")
        self.assertEqual((messages[0]["role"], messages[0]["content"]), ("system", rubric))
        self.assertTrue(messages[1]["content"].endswith("Answer only by calling `record`."))
        self.assertIn(TEXT, messages[1]["content"])
        self.assertEqual(([tool["name"] for tool in tools], tool_choice, max_output), (["record"], None, 64_000))
        lens = rethink[2][-1]["content"]
        self.assertTrue(lens.startswith("Re-examine your record against the page once"))
        self.assertIn("Code-check failures:\n- none", lens)
        self.assertEqual(rethink[2][:2], messages, "the rethink turn continues the draft's conversation")
        self.assertEqual(rethink[2][2]["role"], "assistant")

        [source] = self.rows(
            "SELECT id, rubric_version, model, thinking, escalated, rethink_line, dropped_claims, support_status, copies_status, text_origin FROM sources"
        )
        self.assertEqual(source[1:], ("r1", "fake/sonnet", "high", 0, "Rethink: no change", 0, "checked", "checked", "read"))
        claims = self.rows("SELECT id, section, text, basis FROM claims WHERE source_id = ? ORDER BY ord", source[0])
        self.assertEqual([row[1:] for row in claims], [(c["section"], c["text"], c["basis"]) for c in (C1, C2, C3)])
        [(start, end)] = self.rows('SELECT start, "end" FROM quotes WHERE claim_id = ?', claims[0][0])
        page_quote = "cuts build time by 40% on large repos, according to the team\u2019s benchmark"
        self.assertEqual((start, end), (TEXT.index(page_quote), TEXT.index(page_quote) + len(page_quote)))
        self.assertEqual(
            self.rows("SELECT verdict, p, flagged, judge_model FROM claim_flags ORDER BY claim_id"),
            [("supports", 0.95, 0, "fake-judge-1")] * 3,
        )
        self.assertEqual(self.rows("SELECT role, count(*) FROM calls GROUP BY role ORDER BY role"), [("atlas_summarize", 2), ("judge", 3)])
        self.assertEqual(self.rows("SELECT event, rubric_version, model, escalated FROM summary_history"), [("added", "r1", "fake/sonnet", 0)])

    def test_with_rethink_off_there_is_no_rethink_turn(self) -> None:
        self.configure("rethink = false\n")
        fake = FakeHost(pages={LINK: PAGE}, replies={"atlas_summarize": [tool_reply(record(C1, C2, C3))]}, judge_answer=judge_by_claim({}))
        answer, code = self.add(fake)
        self.assertEqual((code, answer["result"]["added"]), (0, 1))
        self.assertEqual(len(self.calls(fake, "call", "atlas_summarize")), 1)
        self.assertEqual(self.rows("SELECT rethink_line FROM sources"), [(None,)])

    def test_failures_and_flags_get_one_repair_turn_and_only_changed_claims_are_judged_again(self) -> None:
        fake = FakeHost(
            pages={LINK: PAGE},
            replies={
                "atlas_summarize": [
                    tool_reply(record(C1_BAD, C2, C3)),
                    tool_reply(record(C1_BAD, C2, C3), "Rethink: no change"),
                    tool_reply(record(C1, C2, C3)),
                ]
            },
            judge_answer=judge_by_claim({C2["text"]: 0.3}),
        )
        answer, code = self.add(fake)
        self.assertEqual(code, 0, answer)
        draft, rethink, repair = self.calls(fake, "call", "atlas_summarize")
        self.assertIn(f'- quote 1 of claim 1 is not on the page word for word: "{BAD_QUOTE}"', rethink[2][-1]["content"])
        self.assertEqual(
            repair[2][-1]["content"],
            "Fix exactly these problems, then call the tool again with the whole answer:\n"
            f'- quote 1 of claim 1 is not on the page word for word: "{BAD_QUOTE}"\n'
            "- claim 2 may not be supported by its quote: fix it, pick a better quote, or keep it\n\n"
            "Answer only by calling `record`.",
        )
        judged = [claim_of(call[1]) for call in self.calls(fake, "judge")]
        self.assertCountEqual(judged[:3], [C1["text"], C2["text"], C3["text"]])
        self.assertEqual(judged[3:], [C1["text"]], "after the repair only the changed claim is judged again")
        self.assertEqual(answer["result"]["items"][0]["flagged_claims"], 1)
        self.assertEqual(
            self.rows("SELECT c.text, f.p, f.flagged FROM claims c JOIN claim_flags f ON f.claim_id = c.id ORDER BY c.ord"),
            [(C1["text"], 0.95, 0), (C2["text"], 0.3, 1), (C3["text"], 0.95, 0)],
        )

    def test_a_claim_whose_quote_is_still_missing_after_repair_is_dropped_and_counted(self) -> None:
        self.configure("rethink = false\n")
        fake = FakeHost(
            pages={LINK: PAGE},
            replies={"atlas_summarize": [tool_reply(record(C1_BAD, C2, C3)), tool_reply(record(C1_BAD, C2, C3))]},
            judge_answer=judge_by_claim({}),
        )
        answer, code = self.add(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual((answer["result"]["dropped_claims"], answer["result"]["items"][0]["claims"]), (1, 2))
        self.assertEqual(self.rows("SELECT text FROM claims ORDER BY ord"), [(C2["text"],), (C3["text"],)])
        self.assertEqual(self.rows("SELECT dropped_claims FROM sources"), [(1,)])

    def test_a_basis_still_outside_its_list_after_repair_is_a_bad_shape_not_a_drop(self) -> None:
        self.configure("rethink = false\n")
        odd = {**C1, "basis": "rumoured"}
        fake = FakeHost(
            pages={LINK: PAGE},
            replies={
                "atlas_summarize": [tool_reply(record(odd, C2, C3)), tool_reply(record(odd, C2, C3))],
                "atlas_escalate": [tool_reply(record(C1, C2, C3), model="fake/opus")],
            },
            judge_answer=judge_by_claim({}),
        )
        answer, code = self.add(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(len(self.calls(fake, "call", "atlas_escalate")), 1)
        self.assertEqual(self.rows("SELECT escalated, dropped_claims FROM sources"), [(1, 0)])
        self.assertEqual(self.rows("SELECT basis FROM claims ORDER BY ord"), [("measured",), ("asserted",), ("asserted",)])

    def test_no_tool_call_gets_one_reminder_then_one_escalation(self) -> None:
        fake = FakeHost(
            pages={LINK: PAGE},
            replies={
                "atlas_summarize": [text_reply("Here is a summary."), text_reply("Still prose.")],
                "atlas_escalate": [
                    tool_reply(record(C1, C2, C3), model="fake/opus", thinking="medium"),
                    tool_reply(record(C1, C2, C3), "Rethink: no change", model="fake/opus", thinking="medium"),
                ],
            },
            judge_answer=judge_by_claim({}),
        )
        answer, code = self.add(fake)
        self.assertEqual(code, 0, answer)
        first, reminder = self.calls(fake, "call", "atlas_summarize")
        self.assertEqual(
            reminder[2][-2:],
            [{"role": "assistant", "content": "Here is a summary."}, {"role": "user", "content": "Answer only by calling `record`."}],
        )
        self.assertEqual(len(self.calls(fake, "call", "atlas_escalate")), 2)
        self.assertEqual(self.rows("SELECT model, thinking, escalated FROM sources"), [("fake/opus", "medium", 1)])
        self.assertEqual(self.rows("SELECT model, escalated FROM summary_history"), [("fake/opus", 1)])

    def test_when_the_escalation_fails_too_nothing_is_stored_and_a_summary_failed_decision_returns(self) -> None:
        self.configure("rethink = false\n")
        bad = record(C1_BAD, {**C2, "quotes": ["not on the page at all"]})
        fake = FakeHost(
            pages={LINK: PAGE},
            replies={
                "atlas_summarize": [text_reply("The page says", stop="cut_off")],
                "atlas_escalate": [tool_reply(bad, model="fake/opus"), tool_reply(bad, model="fake/opus")],
            },
            judge_answer=judge_by_claim({}),
        )
        answer, code = self.add(fake)
        self.assertEqual(code, 4)
        self.assertEqual(answer["result"]["items"], [{"link": LINK, "result": "summary failed"}])
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "summary_failed")
        self.assertIn("no claim is left after the checks", decision["question"])
        self.assertEqual(
            [(option["id"], option["then"]) for option in decision["options"]],
            [("retry", {"resend": {"items": [{"link": LINK}]}}), ("skip", {"stop": True})],
        )
        for table in ("sources", "links", "page_text", "claims", "quotes", "claim_flags", "summary_history"):
            self.assertEqual(self.rows(f"SELECT count(*) FROM {table}"), [(0,)], table)
        self.assertEqual(
            self.rows("SELECT role, count(*) FROM calls GROUP BY role ORDER BY role"),
            [("atlas_escalate", 2), ("atlas_summarize", 1), ("judge", 2)],
        )

    def test_a_support_answer_near_the_limit_is_asked_again_with_the_options_reversed(self) -> None:
        self.configure("rethink = false\n")
        asked: list[tuple[str, tuple[str, ...]]] = []

        def answer(state: str, question: ports.Question) -> ports.Answer:
            asked.append((claim_of(state), question.options))
            if claim_of(state) != C2["text"]:
                return support(0.95)
            return support(0.75 if question.options[0] == "supports" else 0.95)

        fake = FakeHost(pages={LINK: PAGE}, replies={"atlas_summarize": [tool_reply(record(C1, C2, C3))]}, judge_answer=answer)
        reply, code = self.add(fake)
        self.assertEqual(code, 0, reply)
        options = ("supports", "contradicts", "says nothing")
        # Claims are judged concurrently, so only the rerun's place after its first answer is ordered.
        self.assertCountEqual(
            asked,
            [(C1["text"], options), (C2["text"], options), (C3["text"], options), (C2["text"], tuple(reversed(options)))],
        )
        self.assertLess(asked.index((C2["text"], options)), asked.index((C2["text"], tuple(reversed(options)))))
        self.assertEqual(
            self.rows("SELECT c.text, f.p, f.flagged FROM claims c JOIN claim_flags f ON f.claim_id = c.id WHERE c.ord = 2"),
            [(C2["text"], 0.85, 0)],
        )
        self.assertEqual(len(self.calls(fake, "call", "atlas_summarize")), 1, "no flag left, so no repair turn")


if __name__ == "__main__":
    unittest.main()
