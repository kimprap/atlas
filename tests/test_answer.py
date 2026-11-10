"""``ask`` with a ``question`` through ``app.run`` with the fake host and a temporary ``HOME`` (AC-4.2).

Labels are checked fail-closed (ticket 09 item 7), backing is counted in code
over the sources searched (item 6), tally lines are stored without a stop
(item 10), and the answer comes from the top 10 through ``atlas_answer``
(spec 4.10).
"""

from __future__ import annotations

import unittest
from typing import Any

from tests.fakes.fake_host import FakeHost, text_reply, tool_reply
from tests.test_search import FindTest, link, seed

from atlas import ports  # noqa: E402
from atlas.core import app  # noqa: E402

QUESTION = "Does a build cache help large repos?"
SOURCES = [
    {"title": "Cache basics", "abstract": "What a build cache is.", "author": "Ann", "publisher": "Acme"},
    {"title": "Large repos", "abstract": "A build cache in large repos.", "author": "Bob", "publisher": "Acme"},
    {"title": "Cache bench", "abstract": "A build cache benchmark.", "author": "Cy", "publisher": "Bench Co"},
    # Dee's repost names Cy's benchmark with a tracking parameter; link cleanup still finds it.
    {"title": "Cache repost", "abstract": "A build cache benchmark, reposted.", "author": "Dee", "related": [link(3) + "?utm_source=feed"]},
]
SOUND_2 = {"claim": "Caches cut rebuilds in large repos.", "sources": [link(1), link(2)], "label": "Sound", "reason": "Two write-ups agree."}
NOISE = {"claim": "Caches are magic.", "sources": [link(1)], "label": "Noise", "reason": "Hype."}
# A link not searched and a link that is not text are both left out with a problem.
DOUBTFUL = {"claim": "The cache halves build time.", "sources": [link(1), {"link": link(2)}, link(3), "https://elsewhere.example/x"], "label": "Doubtful", "reason": "One benchmark only."}
SOUND_4 = {"claim": "The benchmark ran on 3 repos.", "sources": [link(3), link(4)], "label": "Sound", "reason": "Measured."}


def answered(claims: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return {
        "answer": "Yes, for large repos.",
        "claims": claims,
        "disagreements": ["Ann says caches always help; Cy measured gains on large repos only."],
        "gaps": ["No source covers Windows."],
        "model_view": "My view: cache invalidation is the hard part.",
        "tally_lines": [],
        **extra,
    }


class AskTest(FindTest):
    def ask(self, fake: FakeHost, body: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
        if body is None:
            body = {"question": QUESTION, "original": "does caching help?", "phrasings": ["build cache"], "context": "picking a CI setup"}
        return app.run("ask", None, body, fake.host())

    def host(self, *replies: ports.Reply) -> FakeHost:
        return FakeHost(replies={"atlas_answer": list(replies)}, judge_answer=lambda state, question: ports.Answer(p=0.5))


class AnswerTests(AskTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, SOURCES)

    def test_labelled_claims_sort_sound_doubtful_noise_with_backing_counted_and_tally_lines_stored(self) -> None:
        tally = [
            {"who": "Cy", "subject": "build caches", "link": link(3), "direction": "towards"},
            {"who": "Dee", "subject": "build caches", "link": link(4), "direction": "sideways"},
        ]
        fake = self.host(tool_reply(answered([NOISE, SOUND_2, DOUBTFUL, SOUND_4], tally_lines=tally), model="fake/opus"))
        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)
        result = answer["result"]
        self.assertEqual(result["labels"], "checked")
        shown = [(claim["claim"], claim["label"], claim["backing"]) for claim in result["claims"]]
        self.assertEqual(
            shown,
            [
                # Ann and Bob share a publisher, so they count once.
                (SOUND_2["claim"], "Sound", "backed by 1 independent source"),
                # Dee's repost links Cy's benchmark, so they count once.
                (SOUND_4["claim"], "Sound", "backed by 1 independent source"),
                (DOUBTFUL["claim"], "Doubtful", "backed by 2 independent sources"),
                (NOISE["claim"], "Noise", "backed by 1 independent source"),
            ],
        )
        self.assertEqual(result["claims"][2]["sources"], [link(1), link(3)], "a link not searched is left out")
        self.assertEqual(result["claims"][0]["reason"], "Two write-ups agree.")
        self.assertEqual(result["writing_model"], "fake/opus:high")
        self.assertEqual(result["ranker"], {"name": "jev", "model": "fake-judge-1"})
        self.assertEqual(result["question_as_searched"], QUESTION)
        self.assertEqual((result["answer"], result["gaps"], result["model_view"]), ("Yes, for large repos.", ["No source covers Windows."], "My view: cache invalidation is the hard part."))
        self.assertEqual(result["tally_lines"], [tally[0]])
        self.assertEqual(self.rows("SELECT who, subject, link, direction, proposed_at FROM tally"), [("Cy", "build caches", link(3), "towards", None)])
        self.assertEqual(sorted(problem["field"] for problem in answer["problems"]), ["claims", "claims", "tally_lines"])
        self.assertEqual(self.rows("SELECT count(*) FROM approvals"), [(0,)], "tally lines need no stop")
        [call] = self.calls(fake, "call", "atlas_answer")
        self.assertIn("Context: picking a CI setup", call[2][-1]["content"])
        self.assertEqual(self.rows("SELECT role, command FROM calls WHERE role = 'atlas_answer'"), [("atlas_answer", "ask")])
        self.assertEqual([row[0] for row in self.queries()], ["ask"])

    def test_a_label_outside_the_three_shows_every_claim_unlabelled_and_says_so(self) -> None:
        strong = {**SOUND_4, "label": "Strong"}
        fake = self.host(tool_reply(answered([NOISE, SOUND_2, strong]), model="fake/opus"))
        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)
        result = answer["result"]
        self.assertTrue(result["labels"].startswith("unlabelled: the label check failed"), result["labels"])
        self.assertIn('"Strong"', result["labels"])
        # Nothing is withheld: every claim stays, in the model's order, with its backing.
        self.assertEqual([claim["claim"] for claim in result["claims"]], [NOISE["claim"], SOUND_2["claim"], SOUND_4["claim"]])
        for claim in result["claims"]:
            self.assertEqual(set(claim), {"claim", "sources", "backing"})

    def test_a_reply_without_the_tool_gets_one_reminder(self) -> None:
        fake = self.host(text_reply("Here is my answer in prose.", model="fake/opus"), tool_reply(answered([SOUND_2]), model="fake/opus"))
        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)
        first, second = self.calls(fake, "call", "atlas_answer")
        self.assertIsNone(first[4], "tool choice auto")
        self.assertTrue(first[2][-1]["content"].endswith("Answer only by calling `answer`."))
        self.assertEqual(second[2][-1]["content"], "Answer only by calling `answer`.")

    def test_no_answer_after_the_reminder_fails_with_the_sources_kept(self) -> None:
        fake = self.host(text_reply("prose", model="fake/opus"), text_reply("more prose", model="fake/opus"))
        answer, code = self.ask(fake)
        self.assertEqual(code, 1, answer)
        self.assertEqual(answer["problems"][-1]["field"], "answer")
        self.assertEqual(len(answer["result"]["sources"]), 4)
        self.assertEqual(self.rows("SELECT count(*) FROM tally"), [(0,)])

    def test_other_forms_of_ask_are_not_built_yet(self) -> None:
        answer, code = self.ask(self.host(), {"source": link(1)})
        self.assertEqual(code, 1)
        self.assertIn("not available", answer["problems"][0]["problem"])


class TopTenTests(AskTest):
    def test_the_answer_reads_the_top_10(self) -> None:
        seed(self.store, [{"title": f"Cache note {n}", "abstract": "build cache"} for n in range(1, 13)])
        fake = self.host(tool_reply(answered([]), model="fake/opus"))
        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(len(answer["result"]["sources"]), 10)
        [call] = self.calls(fake, "call", "atlas_answer")
        self.assertIn("[S10] ", call[2][-1]["content"])
        self.assertNotIn("[S11] ", call[2][-1]["content"])

    def test_nothing_found_makes_no_answer_call(self) -> None:
        fake = self.host()
        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)
        self.assertIsNone(answer["result"]["answer"])
        self.assertEqual(self.calls(fake, "call"), [])
        self.assertEqual(len(self.queries()), 1)


if __name__ == "__main__":
    unittest.main()
