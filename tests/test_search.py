"""``find`` through ``app.run`` with the fake host and a temporary ``HOME`` (AC-4.1).

Covers the ranker chain of spec 4.5 (Jev; ``atlas_rerank`` when Jev fails or the
profile chose Opus; fusion order when ``atlas_rerank`` fails), the rewrite and
its fallback, the ``judge_setup`` decision before searching, the cap yield and
one query record per search (spec 4.10).
"""

from __future__ import annotations

import json
import unittest
from contextlib import closing
from typing import Any

from tests.fakes.fake_host import FakeHost, text_reply, tool_reply
from tests.test_summarize import PipelineTest

from atlas import ports  # noqa: E402
from atlas.core import app, spend  # noqa: E402
from atlas.store import CallRecord, ClaimRecord, PageText, SourceRecord, sqlite  # noqa: E402

AT = "2026-11-01T10:00:00+00:00"
QUESTION = "How do build caches speed up large repos?"
ORIGINAL = "how do caches speed up builds?"


def link(n: int) -> str:
    return f"https://example.com/s{n}"


def seed(path: Any, sources: list[dict[str, Any]]) -> list[str]:
    """Store each source (title, abstract, claims, and optional author, publisher, related, archived) and index it."""
    with closing(sqlite.open_store(path)) as store:
        for n, item in enumerate(sources, 1):
            key = item.get("link", link(n))
            record = SourceRecord(
                key_link=key,
                kind="article",
                unchangeable=False,
                first_seen=AT,
                last_read=AT,
                content_hash=f"hash{n}",
                text_origin="read",
                title=item["title"],
                author=item.get("author"),
                publisher=item.get("publisher"),
                published=item.get("published"),
                abstract=item.get("abstract", ""),
                archived_at=item.get("archived"),
            )
            source_id = store.add_source(record, PageText("page", (), (0,) * 64))
            store.add_link(key, source_id, "key", AT)
            for ord, text in enumerate(item.get("claims", ()), 1):
                store.add_claim(source_id, ord, ClaimRecord("claim", text, "asserted", ()), AT)
            store.add_related_links(source_id, item.get("related", ()), "page")
            store.index_source(source_id)
        return [item.get("link", link(n)) for n, item in enumerate(sources, 1)]


def by_title(ps: dict[str, float]) -> Any:
    """A Jev answer per candidate, looked up by the title line of the candidate in the judge's state."""

    def answer(state: str, question: ports.Question) -> ports.Answer:
        title = state.split("Source:\n", 1)[1].split("\n", 1)[0]
        return ports.Answer(p=ps[title])

    return answer


CACHE_SOURCES = [
    {"title": "Cache basics", "abstract": "What a build cache is.", "claims": ["A build cache stores outputs."], "author": "Ann", "published": "2026-01-02"},
    {"title": "Large repos", "abstract": "Speeding up builds in large repos.", "claims": ["Large repos rebuild too much."], "author": "Bob"},
    {"title": "Gardening", "abstract": "Tomatoes and soil.", "claims": ["Tomatoes like sun."]},
    {"title": "Old cache note", "abstract": "A build cache note.", "claims": ["Caches speed up builds."], "archived": AT},
]


class FindTest(PipelineTest):
    def find(self, fake: FakeHost, body: dict[str, Any] | None = None, mode: str | None = None) -> tuple[dict[str, Any], int]:
        return app.run("find", mode, self.body() if body is None else body, fake.host())

    def body(self) -> dict[str, Any]:
        return {"question": QUESTION, "original": ORIGINAL, "phrasings": ["build cache", "large repos"]}

    def queries(self) -> list[tuple]:
        return self.rows("SELECT op, original, question, phrasings, context, ranker, judge_records, note FROM queries")

    def links(self, answer: dict[str, Any]) -> list[str]:
        return [item["link"] for item in answer["result"]["sources"]]


class RankerChainTests(FindTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, CACHE_SOURCES)

    def test_jev_ranks_the_fused_phrasings_by_probability_and_one_query_record_keeps_it(self) -> None:
        fake = FakeHost(judge_answer=by_title({"Cache basics": 0.2, "Large repos": 0.9}))
        answer, code = self.find(fake, {**self.body(), "context": "choosing a CI cache"})
        self.assertEqual(code, 0, answer)
        # Gardening matches no phrasing; the archived note is left out.
        self.assertEqual(self.links(answer), [link(2), link(1)])
        self.assertEqual(answer["result"]["ranker"], {"name": "jev", "model": "fake-judge-1"})
        self.assertEqual(answer["result"]["question_as_searched"], QUESTION)
        self.assertEqual(
            answer["result"]["sources"][1],
            {"link": link(1), "title": "Cache basics", "author": "Ann", "date": "2026-01-02", "last_read": answer["result"]["sources"][1]["last_read"]},
        )
        [judged] = {call[2][0].text for call in self.calls(fake, "judge")}
        self.assertEqual(judged, "Does this source help answer the question?")
        self.assertEqual([call[1] for call in fake.calls if call[0] == "call"], [], "agent phrasings need no rewrite")
        [row] = self.queries()
        self.assertEqual(row[:6], ("find", ORIGINAL, QUESTION, '["build cache", "large repos"]', "choosing a CI cache", "jev"))
        records = sorted(json.loads(row[6]), key=lambda item: item["link"])
        self.assertEqual(records, [{"link": link(1), "p": 0.2, "model": "fake-judge-1"}, {"link": link(2), "p": 0.9, "model": "fake-judge-1"}])
        self.assertIsNone(row[7])
        self.assertEqual(self.rows("SELECT count(*) FROM calls WHERE role = 'judge' AND command = 'find'"), [(2,)])

    def test_the_question_as_searched_is_left_out_when_it_is_the_original(self) -> None:
        fake = FakeHost(judge_answer=by_title({"Cache basics": 0.5, "Large repos": 0.5}))
        answer, code = self.find(fake, {**self.body(), "original": QUESTION})
        self.assertEqual(code, 0, answer)
        self.assertNotIn("question_as_searched", answer["result"])

    def test_jev_failing_after_its_backoff_hands_the_search_to_atlas_rerank_and_says_so(self) -> None:
        fake = FakeHost(
            judge_error=ports.JudgeFailed(529, "overloaded after 1, 2, 4 and 8 s"),
            replies={"atlas_rerank": [tool_reply({"order": [2, 1]}, model="fake/opus")]},
        )
        answer, code = self.find(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["ranker"], {"name": "atlas_rerank", "model": "fake/opus"})
        [problem] = answer["problems"]
        self.assertEqual(problem["field"], "ranker")
        self.assertIn("Jev failed after its backoff", problem["problem"])
        # Fusion order puts Cache basics first (a tie, first seen); atlas_rerank's order wins.
        self.assertEqual(self.links(answer), [link(2), link(1)])
        [call] = self.calls(fake, "call", "atlas_rerank")
        self.assertIn("Cache basics", call[2][-1]["content"])
        [row] = self.queries()
        self.assertEqual((row[5], row[6]), ("atlas_rerank", None))
        self.assertIn("Jev failed", row[7])
        self.assertEqual(self.rows("SELECT role FROM calls"), [("atlas_rerank",)])

    def test_a_profile_that_chose_opus_ranks_with_atlas_rerank_and_asks_no_judge(self) -> None:
        self.configure(judge="opus")
        fake = FakeHost(replies={"atlas_rerank": [tool_reply({"order": [1]}, model="fake/opus")]})
        answer, code = self.find(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["ranker"]["name"], "atlas_rerank")
        self.assertEqual(answer["problems"], [])
        # Sources the ranking leaves out follow in fusion order.
        self.assertEqual(self.links(answer), [link(1), link(2)])
        self.assertEqual(self.calls(fake, "judge"), [])

    def test_atlas_rerank_failing_keeps_fusion_order_and_says_so(self) -> None:
        self.configure(judge="opus")
        fake = FakeHost(replies={"atlas_rerank": [text_reply("I would rather not rank these.", model="fake/opus")]})
        # Large repos leads the first list, but Cache basics is found by two phrasings, so fusion puts it first.
        answer, code = self.find(fake, {"question": QUESTION, "original": ORIGINAL, "phrasings": ["large repos", "build cache", "cache basics"]})
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["ranker"], {"name": "bm25", "model": None})
        self.assertEqual(self.links(answer), [link(1), link(2)])
        [problem] = answer["problems"]
        self.assertIn("atlas_rerank failed", problem["problem"])
        self.assertEqual(self.queries()[0][5], "bm25")


class RewriteTests(FindTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, CACHE_SOURCES)
        self.jev = by_title({"Cache basics": 0.9, "Large repos": 0.8})

    def test_without_phrasings_atlas_query_rewrites_the_question_into_three(self) -> None:
        rewrites = ["gardening tomatoes", "large repos", "soil"]
        fake = FakeHost(replies={"atlas_query": [tool_reply({"phrasings": rewrites}, model="fake/opus")]}, judge_answer=by_title({"Gardening": 0.1, "Large repos": 0.8}))
        answer, code = self.find(fake, {"question": QUESTION, "original": ORIGINAL})
        self.assertEqual(code, 0, answer)
        self.assertEqual(self.links(answer), [link(2), link(3)])
        [call] = self.calls(fake, "call", "atlas_query")
        self.assertIn(QUESTION, call[2][-1]["content"])
        self.assertEqual(json.loads(self.queries()[0][3]), rewrites)
        self.assertEqual(self.rows("SELECT role, command FROM calls WHERE role = 'atlas_query'"), [("atlas_query", "find")])

    def test_a_failed_rewrite_searches_the_question_as_given_and_says_so(self) -> None:
        fake = FakeHost(replies={"atlas_query": [ports.CallFailed(500, "gateway error")]}, judge_answer=self.jev)
        question = "build cache in large repos"
        answer, code = self.find(fake, {"question": question, "original": question})
        self.assertEqual(code, 0, answer)
        self.assertEqual(self.links(answer), [link(1), link(2)])
        [problem] = answer["problems"]
        self.assertEqual(problem["field"], "phrasings")
        self.assertIn("searched the question as given", problem["problem"])
        self.assertEqual(json.loads(self.queries()[0][3]), [question])


class StopTests(FindTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, CACHE_SOURCES)

    def assert_no_search(self, fake: FakeHost) -> None:
        self.assertEqual([call for call in fake.calls if call[0] in ("call", "judge")], [])
        self.assertEqual(self.queries(), [])

    def test_no_judge_choice_saved_is_a_judge_setup_decision_before_searching(self) -> None:
        self.configure(judge=None)
        fake = FakeHost()
        answer, code = self.find(fake)
        self.assertEqual(code, 4, answer)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "judge_setup")
        self.assertEqual({option["then"].get("skill") for option in decision["options"]}, {"atlas-init", None})
        self.assert_no_search(fake)

    def test_a_jev_key_problem_is_a_judge_setup_decision_naming_it(self) -> None:
        missing = ports.SetupProblem("The Jev key file is missing", ("Put the key in the file.",), "/fake/key.env")
        fake = FakeHost(setup_problem=missing)
        answer, code = self.find(fake)
        self.assertEqual(code, 4, answer)
        self.assertIn("The Jev key file is missing", answer["decisions"][0]["question"])
        self.assert_no_search(fake)

    def test_the_cap_yields_before_the_first_paid_call_and_a_confirm_continues(self) -> None:
        self.configure("cap_usd = 1.0\n")
        with closing(sqlite.open_store(self.store)) as store:
            store.add_call(CallRecord(spend.stamp(spend.local_now()), "add", "judge", "fake-judge-1", None, 0, 0, 0, 0, 0.9, "billed"))
        fake = FakeHost(judge_answer=by_title({"Cache basics": 0.5, "Large repos": 0.5}))
        answer, code = self.find(fake)
        self.assertEqual(code, 4, answer)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "cap")
        self.assert_no_search(fake)
        go = next(option for option in decision["options"] if option["id"] == "go")
        resent = {**self.body(), **go["then"]["resend"]}
        resent["approval"] = {**resent["approval"], "words": "continue anyway"}
        answer, code = self.find(fake, resent)
        self.assertEqual(code, 0, answer)
        self.assertEqual(len(self.queries()), 1)

    def test_a_missing_role_stops_with_exit_3_before_any_paid_call(self) -> None:
        roles = {"atlas_summarize": "fake/sonnet:high"}
        fake = FakeHost(roles=roles)
        answer, code = self.find(fake, {"question": QUESTION, "original": ORIGINAL})
        self.assertEqual(code, 3, answer)
        self.assertEqual([item["what"] for item in answer["result"]["needs_action"]], ["Role atlas_query is missing"])
        self.assert_no_search(fake)


class TopThirtyTests(FindTest):
    def test_only_the_fused_top_30_go_to_the_ranker(self) -> None:
        seed(self.store, [{"title": f"Cache note {n}", "abstract": "build cache", "claims": []} for n in range(1, 33)])
        fake = FakeHost(judge_answer=lambda state, question: ports.Answer(p=0.5))
        answer, code = self.find(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(len(self.calls(fake, "judge")), 30)
        self.assertEqual(len(answer["result"]["sources"]), 30)


if __name__ == "__main__":
    unittest.main()
