"""Marks, flags and the catch-up through ``app.run`` with the fake host, a temporary ``HOME`` and ``XDG_STATE_HOME`` (AC-7.2).

``add`` and a redo mark the followed topics a source matters to (P >= 0.3); a redo or re-read that changes a claim an
agreed version cites flags that topic by quote; ``ask`` with ``whats_new`` (or ``topic``) searches every followed topic,
lets marks only add and order, skips an unchanged no-change set's answer call and stores a verdict in
``topics.last_catchup``. Each absence (no mark, no call, no flag, no answer) is paired with the case where it happens.
"""

from __future__ import annotations

import json
import re
import unittest
from contextlib import closing
from typing import Any

from tests.fakes.fake_host import FakeHost, support, text_reply, tool_reply
from tests.test_add import SECOND, SECOND_PAGE, SECOND_RECORD
from tests.test_redo import FULL, NEW_ROLES, PRICES, haiku, sonnet
from tests.test_reread import BASE, NEW_C3, REREAD, WINDOWS_LINE, page
from tests.test_summarize import C1, C2, C3, LINK, PAGE, PipelineTest, record

from atlas import ports  # noqa: E402
from atlas.core import app  # noqa: E402
from atlas.store import ClaimRecord, PageText, SourceRecord, VersionClaim, VersionRecord, sqlite  # noqa: E402
from tools.quality import marks as marks_report  # noqa: E402

OLD = "2026-10-01T10:00:00+00:00"
SAVED = "2026-11-01T10:00:00+00:00"
NEW = "2026-11-05T10:00:00+00:00"


def topic_judge(by_topic: dict[str, float]) -> Any:
    """A judge that answers the topic question by the topic's name, claim support as supported and every other question as no."""

    def answer(state: str, question: ports.Question) -> ports.Answer:
        if question.id == "topic":
            return ports.Answer(p=by_topic[state.split("\n", 1)[0].removeprefix("Topic: ")])
        if question.id == "support":
            return support(0.95)
        return ports.Answer(p=0.1)

    return answer


def version(text: str = "Agreed.", saved: str = SAVED) -> VersionRecord:
    return VersionRecord(text, "fake/opus", None, "complete", ("fake/reviewer",), "reconcile-1", "none", None, saved)


class StoreTest(PipelineTest):
    def put_topic(self, name: str, brief: str, versions: list[list[VersionClaim]] | None = None, **state: Any) -> int:
        """A topic with one saved version per list of claim copies, and ``followed``, ``archived`` and ``reviewed`` when given."""
        with closing(sqlite.open_store(self.store)) as store:
            topic_id = store.add_topic(name, brief)
            for n, copies in enumerate(versions or [], 1):
                store.add_version(topic_id, version(f"Agreed {n}."), copies)
            if "followed" in state:
                store.set_topic_followed(topic_id, state["followed"])
            if "archived" in state:
                store.set_topic_archived(topic_id, state["archived"])
            if "reviewed" in state:
                store.set_topic_reviewed(topic_id, state["reviewed"])
        return topic_id

    def copies(self, link: str, *positions: int) -> list[VersionClaim]:
        """Copies, as a saved version takes them, of the stored claims at ``positions`` (from 1) of the source ``link`` holds."""
        with closing(sqlite.open_store(self.store)) as store:
            [(source_id,)] = self.rows("SELECT id FROM sources WHERE key_link = ?", link)
            stored = store.claims(source_id)
            return [VersionClaim(c.id, c.claim.text, tuple(q.text for q in c.claim.quotes)) for c in stored if c.ord in positions]

    def topic_questions(self, fake: FakeHost) -> list[str]:
        return [call[1].split("\n", 1)[0] for call in self.calls(fake, "judge") if call[2][0].id == "topic"]


class MarksAfterAddTests(StoreTest):
    def setUp(self) -> None:
        super().setUp()
        self.configure("rethink = false\n")

    def added(self, judge: Any, **options: Any) -> tuple[FakeHost, dict[str, Any], int]:
        fake = FakeHost(pages={LINK: PAGE}, replies={"atlas_summarize": [tool_reply(record(C1, C2, C3))]}, judge_answer=judge, **options)
        answer, code = self.add(fake)
        return fake, answer, code

    def test_a_stored_source_is_marked_for_each_followed_topic_it_reaches_and_only_those(self) -> None:
        self.put_topic("Build caches", "Do build caches help?", [[]])
        self.put_topic("Windows ports", "Does it run on Windows?")
        self.put_topic("Gardening", "How do tomatoes grow?")
        self.put_topic("Unfollowed", "Do build caches help?", followed=False)
        self.put_topic("Archived", "Do build caches help?", archived=SAVED)
        fake, answer, code = self.added(topic_judge({"Build caches": 0.7, "Windows ports": 0.3, "Gardening": 0.29}))
        self.assertEqual(code, 0, answer)
        [item] = answer["result"]["items"]
        self.assertEqual(item["result"], "added")
        # P of exactly 0.3 marks; 0.29 does not.
        self.assertEqual(item["topics_marked"], ["Build caches", "Windows ports"])
        self.assertEqual(
            self.rows("SELECT t.name, m.p, m.judge_model, m.cleared_at FROM marks m JOIN topics t ON t.id = m.topic_id ORDER BY t.id"),
            [("Build caches", 0.7, "fake-judge-1", None), ("Windows ports", 0.3, "fake-judge-1", None)],
        )
        self.assertEqual(sorted(self.topic_questions(fake)), ["Topic: Build caches", "Topic: Gardening", "Topic: Windows ports"], "one noul per followed, unarchived topic")
        self.assertEqual(self.rows("SELECT topics_status FROM sources"), [("checked",)])
        states = {call[1].split("\n", 1)[0]: call[1] for call in self.calls(fake, "judge") if call[2][0].id == "topic"}
        self.assertIn("Agreed version, the understanding the user last saved:\nAgreed 1.", states["Topic: Build caches"])
        self.assertNotIn("Agreed version", states["Topic: Gardening"], "a topic with no agreed version is matched on its brief alone")
        for part in ("Brief: Do build caches help?", "Faster builds", C1["text"], "A note on a new build cache."):
            self.assertIn(part, states["Topic: Build caches"])

    def test_a_failed_topic_match_says_so_and_stores_the_source_all_the_same(self) -> None:
        self.put_topic("Build caches", "Do build caches help?")

        def judge(state: str, question: ports.Question) -> ports.Answer:
            if question.id == "topic":
                raise ports.JudgeFailed(529, "overloaded after 1, 2, 4 and 8 s")
            return support(0.95) if question.id == "support" else ports.Answer(p=0.1)

        _, answer, code = self.added(judge)
        self.assertEqual(code, 0, answer)
        [item] = answer["result"]["items"]
        self.assertEqual((item["result"], item["topics"]), ("added", "topics not matched"))
        self.assertNotIn("topics_marked", item)
        self.assertEqual(self.rows("SELECT topics_status FROM sources"), [("topics not matched",)])
        self.assertEqual(self.rows("SELECT count(*) FROM marks"), [(0,)])

    def test_no_topic_call_and_no_mark_when_no_topic_is_followed(self) -> None:
        # The unfollowed topic is not asked about.
        self.put_topic("Unfollowed", "Do build caches help?", followed=False)
        fake, answer, code = self.added(topic_judge({}))
        self.assertEqual(code, 0, answer)
        self.assertEqual(self.topic_questions(fake), [])
        self.assertEqual(self.rows("SELECT count(*), (SELECT topics_status FROM sources) FROM marks"), [(0, None)])
        self.assertNotIn("topics_marked", answer["result"]["items"][0])

    def test_jev_not_set_up_makes_no_topic_call_and_no_mark_and_the_add_does_not_stop(self) -> None:
        self.put_topic("Build caches", "Do build caches help?")
        missing = ports.SetupProblem("The Jev key file is missing", ("Put the key in the file.",), "/fake/key.env")
        fake, answer, code = self.added(topic_judge({"Build caches": 0.9}), setup_problem=missing)
        self.assertEqual(code, 0, answer)
        self.assertEqual((answer["result"]["items"][0]["result"], self.topic_questions(fake)), ("added", []))
        self.assertEqual(self.rows("SELECT count(*), (SELECT topics_status FROM sources) FROM marks"), [(0, None)])

    def test_a_profile_on_opus_makes_no_topic_call_and_no_mark(self) -> None:
        self.configure("rethink = false\n", judge="opus")
        self.put_topic("Build caches", "Do build caches help?")
        fake, answer, code = self.added(topic_judge({"Build caches": 0.9}))
        self.assertEqual(code, 0, answer)
        self.assertEqual(self.calls(fake, "judge"), [])
        self.assertEqual(self.rows("SELECT count(*), (SELECT topics_status FROM sources) FROM marks"), [(0, None)])


class RedoMarksAndFlagsTests(StoreTest):
    """Two sources stored on the old setup and three topics whose agreed versions cite them, then both redone on a new model."""

    C2_NEW = {**C2, "text": "Use the cache only with deterministic builds and a clean tree."}

    def setUp(self) -> None:
        super().setUp()
        self.configure(f'rethink = false\n[profiles.smoke.confirm]\nadd = "never"\nadd_redo = "never"\n{PRICES}')
        stored = FakeHost(
            pages={LINK: PAGE, SECOND: SECOND_PAGE},
            replies={"atlas_summarize": [sonnet(record(C1, C2, C3)), sonnet(SECOND_RECORD)]},
            judge_answer=lambda state, question: support(0.95),
        )
        answer, code = app.run("add", None, {"items": [{"link": LINK}, {"link": SECOND}]}, stored.host())
        self.assertEqual(code, 0, answer)
        self.put_topic("Caching", "Do build caches help?", [[*self.copies(LINK, 1, 2), *self.copies(SECOND, 1)]])
        self.put_topic("Windows", "Does the cache work on Windows?", [self.copies(LINK, 3)])
        # Its agreed version is the latest one, which cites only the second source.
        self.put_topic("Superseded", "An older topic.", [self.copies(LINK, 3), self.copies(SECOND, 1)])

    def redo(self, link_record: dict[str, Any]) -> tuple[FakeHost, dict[str, Any], int]:
        fake = FakeHost(
            pages={LINK: PAGE, SECOND: SECOND_PAGE},
            roles=NEW_ROLES,
            replies={"atlas_summarize": [haiku(link_record), haiku(SECOND_RECORD)]},
            judge_answer=topic_judge({"Caching": 0.7, "Windows": 0.1, "Superseded": 0.1}),
        )
        answer, code = app.run("add", "redo", {}, fake.host())
        return fake, answer, code

    def test_a_redo_that_changed_claims_marks_and_flags_by_quote_and_an_unchanged_one_does_neither(self) -> None:
        # The first claim is the same, the second says something else under the same quote, the third is gone.
        fake, answer, code = self.redo(record(C1, self.C2_NEW))
        self.assertEqual(code, 0, answer)
        items = {item["link"]: item for item in answer["result"]["items"]}
        changed, unchanged = items[LINK], items[SECOND]
        self.assertEqual((changed["result"], unchanged["result"]), ("redone", "redone"))
        # Caching cites the changed second claim; Windows cites the removed third; Superseded's agreed version cites neither.
        self.assertEqual(changed["topics_flagged"], ["Caching", "Windows"])
        self.assertEqual(changed["topics_marked"], ["Caching"])
        self.assertNotIn("topics_flagged", unchanged)
        self.assertNotIn("topics_marked", unchanged)
        self.assertEqual(sorted(self.topic_questions(fake)), ["Topic: Caching", "Topic: Superseded", "Topic: Windows"], "only the changed source is matched again")
        self.assertEqual(self.rows("SELECT t.name, s.key_link FROM marks m JOIN topics t ON t.id = m.topic_id JOIN sources s ON s.id = m.source_id"), [("Caching", LINK)])

    def test_identical_claims_flag_nothing_even_though_their_rows_are_new(self) -> None:
        fake, answer, code = self.redo(record(C1, C2, C3))
        self.assertEqual(code, 0, answer)
        [changed, unchanged] = answer["result"]["items"]
        self.assertEqual((changed["result"], unchanged["result"]), ("redone", "redone"))
        self.assertTrue(all("topics_flagged" not in item and "topics_marked" not in item for item in (changed, unchanged)))
        self.assertEqual(self.topic_questions(fake), [])
        self.assertEqual(self.rows("SELECT count(*) FROM marks"), [(0,)])
        # The rows are new: the redo replaced every claim, so flags compare by text and quote and not by claim id.
        self.assertEqual(self.rows("SELECT count(*) FROM claims WHERE replaced_at IS NOT NULL"), [(4,)])


class RereadFlagsTests(StoreTest):
    def setUp(self) -> None:
        super().setUp()
        self.configure("rethink = false\n")
        stored = FakeHost(pages={LINK: BASE}, replies={"atlas_summarize": [tool_reply(record(C1, C2, C3))]}, judge_answer=lambda state, question: support(0.95))
        _, code = self.add(stored)
        self.assertEqual(code, 0)
        self.put_topic("Speed", "How much faster are builds?", [self.copies(LINK, 1)])
        self.put_topic("Windows", "Does the cache work on Windows?", [self.copies(LINK, 3)])

    def test_a_reread_that_changed_a_cited_claim_flags_that_topic_and_not_the_others(self) -> None:
        text = "Updated in November.\n" + BASE.text.replace(WINDOWS_LINE, "The cache now works on Windows too.")
        [(id3,)] = self.rows("SELECT id FROM claims WHERE ord = 3")
        update = {"affected": [{"ref": f"c{id3}", "action": "revise", **NEW_C3}], "added": []}
        fake = FakeHost(pages={LINK: page(text)}, replies={"atlas_summarize": [tool_reply(update)]}, judge_answer=lambda state, question: support(0.95))
        answer, code = self.add(fake, REREAD, mode="reread")
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["items"], [{"link": LINK, "result": "updated (1 claims changed)", "topics_flagged": ["Windows"]}])
        self.assertEqual(self.rows("SELECT count(*) FROM marks"), [(0,)], "a re-read makes no marks")


# Catch-up --------------------------------------------------------------------------------------------------------
def caught(changes: bool, *links: str) -> dict[str, Any]:
    """An ``atlas_answer`` tool call of a catch-up: one Sound claim naming ``links`` when a conclusion changes."""
    claims = [{"claim": "Newer evidence moves the conclusion.", "sources": list(links), "label": "Sound", "reason": "Two sources agree."}] if changes else []
    answer = "A newer source moves a conclusion." if changes else "The new sources only repeat what is held."
    return {"answer": answer, "claims": claims, "disagreements": [], "gaps": [], "model_view": "My view.", "changes_conclusion": changes}


def answers(by_topic: dict[str, Any]) -> Any:
    """``atlas_answer`` replies by the topic named in the message; a ``ports.Reply`` is returned as it is."""

    def reply(messages: Any) -> ports.Reply:
        name = re.search(r"^Topic: (.+)$", messages[1]["content"], re.M).group(1)  # type: ignore[union-attr]
        made = by_topic[name]
        return made if isinstance(made, ports.Reply) else tool_reply(made, model="fake/opus")

    return reply


def s(n: int) -> str:
    return f"https://example.com/s{n}"


class CatchupTest(StoreTest):
    def setUp(self) -> None:
        super().setUp()
        with closing(sqlite.open_store(self.store)) as store:
            for n, title, abstract, seen in (
                (1, "Cache news", "new build cache speed results", NEW),
                (2, "Cache old", "build cache speed", OLD),
                (3, "Latency report", "network latency budgets for services", NEW),
                (4, "Delta unrelated", "delta epsilon", OLD),
            ):
                self.put_source(store, n, title, abstract, seen)

    def put_source(self, store: Any, n: int, title: str, abstract: str, seen: str) -> int:
        record = SourceRecord(s(n), "article", False, seen, seen, f"hash{n}", "read", title=title, abstract=abstract)
        source_id = store.add_source(record, PageText("page", (), (0,) * 64))
        store.add_link(s(n), source_id, "key", seen)
        store.add_claim(source_id, 1, ClaimRecord("claim", f"{title} claim.", "asserted", ()), seen)
        store.index_source(source_id)
        return source_id

    def topics(self) -> dict[str, int]:
        self.caching = self.put_topic("Caching", "build cache speed", [[]])
        self.latency = self.put_topic("Latency", "network latency budgets", [[]])
        self.gardening = self.put_topic("Gardening", "tomatoes soil", [[]])
        return {"Caching": self.caching, "Latency": self.latency, "Gardening": self.gardening}

    def mark(self, topic_id: int, source_n: int, at: str = NEW) -> None:
        with closing(sqlite.open_store(self.store)) as store:
            [(source_id,)] = self.rows("SELECT id FROM sources WHERE key_link = ?", s(source_n))
            store.add_mark(topic_id, source_id, 0.6, "fake-judge-1", at)

    def host(self, scripted: dict[str, Any], **options: Any) -> FakeHost:
        return FakeHost(reply_with={"atlas_answer": answers(scripted)}, judge_answer=lambda state, question: ports.Answer(p=0.9), **options)

    def catch(self, fake: FakeHost, body: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
        return app.run("ask", None, {"whats_new": True} if body is None else body, fake.host())

    def asked(self, fake: FakeHost) -> list[str]:
        """The topics an answer call was made for, in order."""
        return [re.search(r"^Topic: (.+)$", call[2][1]["content"], re.M).group(1) for call in self.calls(fake, "call", "atlas_answer")]  # type: ignore[union-attr]

    def verdict(self, name: str) -> dict[str, Any] | None:
        [(stored,)] = self.rows("SELECT last_catchup FROM topics WHERE name = ?", name)
        return None if stored is None else json.loads(stored)

    def source_id(self, n: int) -> int:
        [(source_id,)] = self.rows("SELECT id FROM sources WHERE key_link = ?", s(n))
        return source_id


class WhatsNewTests(CatchupTest):
    def test_each_followed_topic_is_searched_for_sources_since_its_version_and_only_topics_with_news_get_an_answer_call(self) -> None:
        self.topics()
        marked = self.put_topic("Marked only", "alpha beta gamma", [[]])
        self.mark(marked, 4, at=SAVED)  # the source matches no word of its brief: the search misses it
        fake = self.host({"Caching": caught(True, s(1)), "Latency": caught(False), "Marked only": caught(True, s(4))})
        answer, code = self.catch(fake)
        self.assertEqual(code, 0, answer)
        result = answer["result"]
        # Conclusion-changing topics first, the marked one before the other; then the no-change count; then the quiet count.
        self.assertEqual([item["topic"] for item in result["changed"]], ["Marked only", "Caching"])
        self.assertEqual(result["no_change"], {"count": 1, "topics": ["Latency"]})
        self.assertEqual(result["quiet"], {"count": 1, "topics": ["Gardening"]})
        self.assertEqual(self.asked(fake), ["Marked only", "Caching", "Latency"], "no answer call for the quiet topic")
        first, second = result["changed"]
        self.assertEqual((first["marked"], first["new"], first["version"], first["next_version"]), ([s(4)], [], 1, 2))
        self.assertEqual((second["marked"], second["new"]), ([], [s(1)]), "the older cache source is not new since the version was saved")
        self.assertEqual((second["claims"][0]["label"], second["claims"][0]["sources"]), ("Sound", [s(1)]))
        self.assertEqual(re.findall(r"\d+", result["summary"]), ["2", "1", "1"], "changed, no-change and quiet counts")
        # The marked source reached its answer call although the search missed it; the older source did not reach Caching's.
        calls = {re.search(r"^Topic: (.+)$", call[2][1]["content"], re.M).group(1): call[2][1]["content"] for call in self.calls(fake, "call", "atlas_answer")}  # type: ignore[union-attr]
        self.assertIn("Delta unrelated", calls["Marked only"])
        self.assertIn("Cache news", calls["Caching"])
        self.assertNotIn("Cache old", calls["Caching"])
        self.assertIn('"Marked only" as version 2, "Caching" as version 2', answer["next"][0]["label"])
        self.assertIn('"Marked only", "Caching"', answer["next"][1]["label"])
        self.assertEqual(self.rows("SELECT count(*) FROM queries WHERE op = 'ask'"), [(4,)], "one query record per topic search")
        self.assertEqual(self.rows("SELECT count(*) FROM calls WHERE role = 'atlas_answer'"), [(3,)])
        # What the catch-up keeps: a verdict, the set and the sources the answer named; nothing for the quiet topic.
        changed = self.verdict("Caching")
        self.assertEqual((changed["changed"], changed["sources"], changed["named"]), (True, [self.source_id(1)], [self.source_id(1)]))
        self.assertRegex(changed["at"], r"^\d{4}-\d\d-\d\dT")
        self.assertEqual(self.verdict("Latency")["named"], [])
        self.assertEqual((self.verdict("Latency")["changed"], self.verdict("Latency")["sources"]), (False, [self.source_id(3)]))
        self.assertIsNone(self.verdict("Gardening"))

    def test_a_set_that_equals_the_last_no_change_one_skips_its_answer_call_and_a_new_source_reopens_it(self) -> None:
        self.topics()
        fake = self.host({"Caching": caught(True, s(1)), "Latency": caught(False)})
        self.catch(fake)
        self.assertEqual(self.asked(fake), ["Caching", "Latency"])
        fake = self.host({"Caching": caught(True, s(1)), "Latency": caught(False)})
        answer, code = self.catch(fake)
        self.assertEqual(code, 0, answer)
        # Latency's set is the one its last answer found changed nothing: no call, and it still counts as no change.
        # Caching's last verdict was a change, so it is answered again.
        self.assertEqual(self.asked(fake), ["Caching"])
        self.assertEqual(answer["result"]["no_change"], {"count": 1, "topics": ["Latency"]})
        with closing(sqlite.open_store(self.store)) as store:
            self.put_source(store, 5, "Latency news", "more network latency budgets", "2026-11-09T10:00:00+00:00")
        fake = self.host({"Caching": caught(True, s(1)), "Latency": caught(False)})
        answer, code = self.catch(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(self.asked(fake), ["Caching", "Latency"], "any new source reopens a no-change topic")
        self.assertEqual(self.verdict("Latency")["sources"], [self.source_id(3), self.source_id(5)])

    def test_new_means_after_the_later_of_the_agreed_version_and_the_reviewed_up_to_date(self) -> None:
        self.put_topic("Caching", "build cache speed", [[]])
        fake = self.host({"Caching": caught(False)})
        answer, code = self.catch(fake)
        self.assertEqual((code, self.asked(fake)), (0, ["Caching"]), answer)
        # Nothing to save, later than the cache source: it is no longer new.
        with closing(sqlite.open_store(self.store)) as store:
            store.set_topic_reviewed(self.rows("SELECT id FROM topics")[0][0], "2026-11-10T10:00:00+00:00")
            self.put_source(store, 5, "Cache later", "build cache speed again", "2026-11-12T10:00:00+00:00")
        fake = self.host({"Caching": caught(False)})
        answer, code = self.catch(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual(self.verdict("Caching")["sources"], [self.source_id(5)], "the source seen after the review is new; the one seen before it is not")

    def test_an_unfollowed_and_an_archived_topic_are_left_out_and_ask_topic_takes_one_stored_unarchived_topic(self) -> None:
        self.put_topic("Caching", "build cache speed", [[]])
        self.put_topic("Unfollowed", "build cache speed", [[]], followed=False)
        self.put_topic("Archived", "build cache speed", [[]], archived=SAVED)
        fake = self.host({"Caching": caught(False), "Unfollowed": caught(False), "Archived": caught(False)})
        answer, code = self.catch(fake)
        self.assertEqual((code, self.asked(fake)), (0, ["Caching"]), answer)
        self.assertEqual(self.rows("SELECT count(*) FROM queries"), [(1,)])
        # ask with topic takes the one named topic, followed or not.
        fake = self.host({"Caching": caught(False), "Unfollowed": caught(True, s(1)), "Archived": caught(False)})
        answer, code = self.catch(fake, {"topic": "  unfollowed "})
        self.assertEqual((code, self.asked(fake)), (0, ["Unfollowed"]), answer)
        self.assertEqual([item["topic"] for item in answer["result"]["changed"]], ["Unfollowed"])
        for name, why in (("Archived", "restore it first"), ("Nobody", "create it first")):
            answer, code = self.catch(self.host({}), {"topic": name})
            self.assertEqual((code, answer["problems"][0]["field"]), (1, "topic"), answer)
            self.assertIn(why, answer["problems"][0]["problem"])

    def test_no_followed_topic_is_a_done_reply_with_no_call(self) -> None:
        fake = self.host({})
        answer, code = self.catch(fake)
        self.assertEqual((code, answer["result"]["changed"], answer["result"]["quiet"]["count"]), (0, [], 0), answer)
        self.assertEqual([call for call in fake.calls if call[0] in ("call", "judge")], [])
        self.assertIn("topic create", answer["next"][0]["label"])


class StopsTests(CatchupTest):
    def setUp(self) -> None:
        super().setUp()
        self.topics()
        self.scripted = {"Caching": caught(True, s(1)), "Latency": caught(True, s(3))}

    def test_two_answer_calls_are_a_batch_for_the_window_guard_and_one_is_not(self) -> None:
        fake = self.host(self.scripted, windows=[FULL])
        answer, code = self.catch(fake)
        self.assertEqual(code, 4, answer)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "window")
        self.assertIn("0 of 2 done, 2 not started", decision["question"])
        self.assertEqual(self.asked(fake), [], "stopped before the first answer call")
        self.assertEqual(answer["result"]["not_started"], 2)
        go = next(option for option in decision["options"] if option["id"] == "go")
        resent = {"whats_new": True, **go["then"]["resend"]}
        resent["approval"] = {**resent["approval"], "words": "go on"}
        answer, code = self.catch(fake, resent)
        self.assertEqual((code, self.asked(fake)), (0, ["Caching", "Latency"]), answer)
        # One answer call is not a batch: the same full window stops nothing.
        with closing(sqlite.open_store(self.store)) as store:
            store.set_topic_followed(self.latency, False)
        fake = self.host(self.scripted, windows=[FULL])
        answer, code = self.catch(fake)
        self.assertEqual((code, self.asked(fake)), (0, ["Caching"]), answer)

    def test_a_failed_answer_leaves_its_topic_unanswered_without_stopping_the_others(self) -> None:
        scripted = {"Caching": text_reply("I would rather not.", model="fake/opus"), "Latency": caught(True, s(3))}
        fake = self.host(scripted)
        answer, code = self.catch(fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual([item["topic"] for item in answer["result"]["changed"]], ["Latency"])
        [unanswered] = answer["result"]["unanswered"]
        self.assertEqual(unanswered["topic"], "Caching")
        self.assertIn("did not call answer", unanswered["why"])
        self.assertTrue(any(problem["problem"].startswith("Caching: ") for problem in answer["problems"]))
        self.assertIsNone(self.verdict("Caching"))
        self.assertIsNotNone(self.verdict("Latency"))
        self.assertIn("Caching", answer["next"][-1]["label"])
        # With every answer failing the catch-up fails.
        answer, code = self.catch(self.host(scripted), {"topic": "Caching"})
        self.assertEqual(code, 1, answer)
        self.assertEqual(answer["result"]["unanswered"][0]["topic"], "Caching")

    def test_jev_not_set_up_is_a_judge_setup_decision_before_any_search_and_a_failing_jev_hands_a_topic_to_atlas_rerank(self) -> None:
        missing = ports.SetupProblem("The Jev key file is missing", ("Put the key in the file.",), "/fake/key.env")
        fake = self.host(self.scripted, setup_problem=missing)
        answer, code = self.catch(fake)
        self.assertEqual((code, answer["decisions"][0]["kind"]), (4, "judge_setup"), answer)
        self.assertEqual((self.rows("SELECT count(*) FROM queries"), self.asked(fake)), ([(0,)], []))
        # Jev fails after its backoff for this search: atlas_rerank ranks it, the problem names the topic, and it goes on.
        fake = self.host(self.scripted, judge_error=ports.JudgeFailed(529, "overloaded"), replies={"atlas_rerank": [tool_reply({"order": [1]}, model="fake/opus")] * 3})
        answer, code = self.catch(fake, {"topic": "Caching"})
        self.assertEqual(code, 0, answer)
        [problem] = answer["problems"]
        self.assertTrue(problem["problem"].startswith("Caching: Jev failed after its backoff"), problem)
        self.assertEqual(self.rows("SELECT ranker FROM queries"), [("atlas_rerank",)])

    def test_the_body_takes_exactly_one_form(self) -> None:
        for body, field in (
            ({"whats_new": True, "topic": "Caching"}, "body"),
            ({"whats_new": False}, "whats_new"),
            ({"whats_new": True, "context": "x"}, "context"),
            ({"topic": " "}, "topic"),
        ):
            answer, code = self.catch(self.host({}), body)
            self.assertEqual((code, answer["problems"][0]["field"]), (2, field), body)


class MarksReportAfterCatchupTests(CatchupTest):
    def test_what_a_catch_up_stores_is_what_marks_report_reads(self) -> None:
        self.topics()
        self.mark(self.caching, 1, at=OLD)
        self.mark(self.latency, 3, at=OLD)
        fake = self.host({"Caching": caught(True, s(1)), "Latency": caught(False)})
        answer, code = self.catch(fake)
        self.assertEqual(code, 0, answer)
        # A mark made after the answer is not yet answered.
        self.mark(self.caching, 3, at="2999-01-01T00:00:00+00:00")
        self.assertEqual(
            marks_report.rows(self.store),
            [
                "0.60 | Caching | https://example.com/s1 | named in the catch-up answer",
                "0.60 | Caching | https://example.com/s3 | not yet answered",
                "0.60 | Latency | https://example.com/s3 | not named in the catch-up answer",
            ],
        )


if __name__ == "__main__":
    unittest.main()
