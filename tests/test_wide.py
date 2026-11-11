"""``find --wide`` through ``app.run`` with the fake host and a temporary ``HOME`` and ``XDG_STATE_HOME`` (AC-7.2).

The wide gather adds Jev's P >= 0.3 set over every unarchived source to the BM25 candidates and puts the rest, by P, one
Next away; when Jev fails or the profile chose Opus the Opus path runs over BM25 top 100 for each phrasing. Each absence
(a source not asked, no judge call, nothing searched) is paired with the case where the thing happens.
"""

from __future__ import annotations

import json
import unittest
from typing import Any

from tests.fakes.fake_host import FakeHost, tool_reply
from tests.test_search import AT, FindTest, by_title, link, seed

from atlas import ports  # noqa: E402
from atlas.core import app  # noqa: E402

BRIEF = "How do build caches speed up large repos?"
LIBRARY = [
    {"title": "Cache basics", "abstract": "What a build cache is.", "claims": ["A build cache stores outputs."]},
    {"title": "Large repos", "abstract": "Speeding up builds in large repos.", "claims": ["Large repos rebuild too much."]},
    {"title": "Remote execution", "abstract": "Distributed compilation farms.", "claims": ["Farms compile remotely."]},
    {"title": "Bazel notes", "abstract": "A build cache for bazel users.", "claims": ["Bazel keeps a cache."]},
    {"title": "Gardening", "abstract": "Tomatoes and soil.", "claims": ["Tomatoes like sun."]},
    {"title": "Old cache note", "abstract": "A build cache note.", "claims": ["Caches speed up builds."], "archived": AT},
]
NOTES = [{"title": f"Cache note {n}", "abstract": "build cache", "claims": [], "link": f"https://example.com/note{n}"} for n in range(1, 33)]
# Jev's P by title: three sources reach 0.3, one of them (Remote execution) matches no phrasing; Bazel notes matches a
# phrasing but is not near the brief; Gardening is neither.
JEV = {"Cache basics": 0.6, "Large repos": 0.4, "Remote execution": 0.8, "Bazel notes": 0.1, "Gardening": 0.05, "Old cache note": 0.9}


class WideTest(FindTest):
    def wide(self, fake: FakeHost, body: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
        return app.run("find", "wide", {"brief": BRIEF, "phrasings": ["build cache", "large repos"], **(body or {})}, fake.host())

    def links(self, answer: dict[str, Any]) -> list[str]:
        return [item["link"] for item in answer["result"]["sources"]]


class JevGatherTests(WideTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, LIBRARY)

    def test_jevs_set_joins_the_bm25_candidates_ordered_by_p_and_one_noul_is_asked_per_unarchived_source(self) -> None:
        fake = FakeHost(judge_answer=by_title(JEV))
        answer, code = self.wide(fake, {"context": "choosing a CI cache"})
        self.assertEqual(code, 0, answer)
        result = answer["result"]
        # Remote execution matches no phrasing and comes in on Jev's P; Bazel notes comes in on BM25 alone.
        shown = [(item["link"], item["p"], item["found_by"]) for item in result["sources"]]
        self.assertEqual(shown, [(link(3), 0.8, "jev"), (link(1), 0.6, "both"), (link(2), 0.4, "both"), (link(4), 0.1, "bm25")])
        self.assertEqual(result["counts"], {"shown": 4, "jev_set": 3, "bm25": 3, "rest": 1})
        self.assertEqual(result["ranker"], {"name": "jev", "model": "fake-judge-1"})
        self.assertEqual(result["page"], "first")
        asked = self.calls(fake, "judge")
        self.assertEqual(len(asked), 5, "every unarchived source and no archived one")
        self.assertEqual({call[2][0].text for call in asked}, {"Is this source about the same area as the brief?"})
        self.assertTrue(all(call[1].startswith(f"Brief: {BRIEF}\nContext: choosing a CI cache\n\nSource:\n") for call in asked))
        self.assertEqual([call for call in fake.calls if call[0] == "call"], [], "phrasings were given, so no rewrite")
        [row] = self.queries()
        self.assertEqual((row[0], row[1], row[2], row[4], row[5]), ("find", BRIEF, BRIEF, "choosing a CI cache", "jev"))
        self.assertEqual({item["link"]: item["p"] for item in json.loads(row[6])}, {link(n): JEV[title] for n, title in enumerate(JEV, 1) if n != 6})
        self.assertEqual(self.rows("SELECT count(*) FROM calls WHERE role = 'judge' AND command = 'find --wide'"), [(5,)])

    def test_the_rest_is_one_next_away_and_that_resend_returns_only_what_was_not_shown(self) -> None:
        fake = FakeHost(judge_answer=by_title(JEV))
        first, code = self.wide(fake)
        self.assertEqual(code, 0, first)
        [more] = [step for step in first["next"] if "resend" in step["then"]]
        self.assertIn("1 other stored source", more["label"])
        self.assertEqual(more["then"], {"resend": {"rest": True}})
        answer, code = self.wide(fake, more["then"]["resend"])
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["page"], "rest")
        self.assertEqual([(item["link"], item["p"]) for item in answer["result"]["sources"]], [(link(5), 0.05)])
        self.assertEqual(set(self.links(first)) & set(self.links(answer)), set(), "nothing is shown twice and nothing is dropped")
        self.assertEqual(len(self.links(first)) + len(self.links(answer)), 5)
        # Paired: with everything shown there is nothing more to resend.
        everything = FakeHost(judge_answer=by_title({**JEV, "Gardening": 0.5}))
        answer, code = self.wide(everything)
        self.assertEqual([step for step in answer["next"] if "resend" in step["then"]], [])
        self.assertEqual(len(self.links(answer)), 5)

    def test_only_the_fused_top_30_are_the_bm25_candidates_beside_jevs_set(self) -> None:
        seed(self.store, NOTES)
        fake = FakeHost(judge_answer=lambda state, question: ports.Answer(p=0.1))
        answer, code = self.wide(fake, {"phrasings": ["build cache"]})
        self.assertEqual(code, 0, answer)
        counts = answer["result"]["counts"]
        # 34 sources match "build cache" (32 notes and two of LIBRARY); none reaches 0.3.
        self.assertEqual((counts["jev_set"], counts["bm25"], counts["shown"]), (0, 30, 30))
        self.assertEqual(counts["rest"], len(self.rows("SELECT id FROM sources WHERE archived_at IS NULL")) - 30)


class OpusPathTests(WideTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, LIBRARY)

    def test_a_failing_jev_hands_the_gather_to_atlas_rerank_over_every_bm25_candidate_and_says_so(self) -> None:
        seed(self.store, NOTES)
        fake = FakeHost(
            judge_error=ports.JudgeFailed(529, "overloaded after 1, 2, 4 and 8 s"),
            replies={"atlas_rerank": [tool_reply({"order": [2, 1]}, model="fake/opus")]},
        )
        answer, code = self.wide(fake, {"phrasings": ["build cache"]})
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["ranker"], {"name": "atlas_rerank", "model": "fake/opus"})
        [problem] = answer["problems"]
        self.assertEqual(problem["field"], "ranker")
        self.assertIn("Jev failed after its backoff", problem["problem"])
        self.assertIn("wide gather", problem["problem"])
        # Every candidate of the phrasing (here 34 > 30), not Jev's set and not a top 30, goes to the ranker.
        [call] = self.calls(fake, "call", "atlas_rerank")
        listed = call[2][-1]["content"]
        self.assertIn("[34] ", listed)
        self.assertNotIn("[35] ", listed)
        self.assertEqual(len(self.links(answer)), 34)
        self.assertEqual(answer["result"]["counts"], {"shown": 34, "rest": 0})
        self.assertNotIn("p", answer["result"]["sources"][0])
        [row] = self.queries()
        self.assertEqual((row[0], row[5], row[6]), ("find", "atlas_rerank", None))
        self.assertIn("Jev failed", row[7])

    def test_a_profile_that_chose_opus_asks_no_judge_and_the_rest_call_has_nothing_more(self) -> None:
        self.configure(judge="opus")
        fake = FakeHost(replies={"atlas_rerank": [tool_reply({"order": [1]}, model="fake/opus"), tool_reply({"order": [1]}, model="fake/opus")]})
        answer, code = self.wide(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["ranker"]["name"], "atlas_rerank")
        self.assertEqual(self.calls(fake, "judge"), [])
        self.assertEqual(self.links(answer)[0], link(1), "atlas_rerank's first pick leads; the others follow in fusion order")
        self.assertEqual([step for step in answer["next"] if "resend" in step["then"]], [])
        answer, code = self.wide(fake, {"rest": True})
        self.assertEqual((code, self.links(answer), answer["result"]["page"]), (0, [], "rest"))


class StopAndBodyTests(WideTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, LIBRARY)

    def test_jev_not_set_up_is_a_judge_setup_decision_before_any_judge_call_or_query(self) -> None:
        missing = ports.SetupProblem("The Jev key file is missing", ("Put the key in the file.",), "/fake/key.env")
        fake = FakeHost(setup_problem=missing)
        answer, code = self.wide(fake)
        self.assertEqual((code, answer["decisions"][0]["kind"]), (4, "judge_setup"), answer)
        self.assertEqual([call for call in fake.calls if call[0] in ("call", "judge")], [])
        self.assertEqual(self.queries(), [])
        # Paired: with the key in place the same body searches.
        answer, code = self.wide(FakeHost(judge_answer=by_title(JEV)))
        self.assertEqual((code, len(self.queries())), (0, 1))

    def test_the_body_takes_a_brief_and_nothing_else_beside_its_options(self) -> None:
        fake = FakeHost(judge_answer=by_title(JEV))
        cases = [
            ({"question": BRIEF}, "question"),
            ({"brief": "  "}, "brief"),
            ({"brief": BRIEF, "rest": "yes"}, "rest"),
            ({"brief": BRIEF, "phrasings": []}, "phrasings"),
        ]
        for body, field in cases:
            answer, code = app.run("find", "wide", body, fake.host())
            self.assertEqual((code, answer["problems"][0]["field"]), (2, field), body)
        self.assertEqual([call for call in fake.calls if call[0] != "open_store"], [], "a bad body costs no call")
        answer, code = app.run("find", "wide", {"brief": BRIEF, "phrasings": ["build cache"], "rest": False}, fake.host())
        self.assertEqual(code, 0, answer)


if __name__ == "__main__":
    unittest.main()
