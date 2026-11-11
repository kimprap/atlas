"""``topic`` and ``plan`` through ``app.run`` with the fake host and a temporary ``HOME`` and ``XDG_STATE_HOME`` (AC-7.1).

Versions copy the claims they cite; a save always stops; nothing to save stores the date and clears marks; a
save that is not cross-checked carries its reason; a plan is stored with its review. Marks are inserted with SQL,
because the code that makes them is a later task. Each absence (no version, no mark cleared, no stop skipped) is
paired with the presence it differs from.
"""

from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from datetime import datetime, timezone
from typing import Any

from tests.fakes.fake_host import FakeHost, text_reply, tool_reply
from tests.test_search import by_title
from tests.test_summarize import PipelineTest

from atlas import ports  # noqa: E402
from atlas.core import app  # noqa: E402
from atlas.core.config import CHANGE_KINDS  # noqa: E402
from atlas.store import ClaimRecord, PageText, QuoteRecord, SourceRecord, sqlite  # noqa: E402

AT = "2026-11-01T10:00:00+00:00"
NAME = "Build caches"
BRIEF = "Do build caches help large repositories?"
CREATE = {"name": NAME, "brief": BRIEF}
SOURCES = [
    ("Cache basics", [("A build cache stores outputs.", "Outputs are stored by input hash."), ("Caches cut rebuilds.", "Rebuilds drop by half.")]),
    ("Large repos", [("Large repos rebuild too much.", "Large repos rebuild everything."), ("Remote caches share outputs.", "A remote cache is shared.")]),
]
DRAFT = {
    "writer_model": "fake/opus",
    "thinking": "medium",
    "claims": [
        {"claim": "Caches cut rebuilds.", "cites": [{"link": "https://example.com/s1", "claim": 2}, {"link": "https://example.com/s2", "claim": 1}]},
        {"claim": "Hashing makes outputs reusable.", "cites": [{"link": "https://example.com/s1", "claim": 1}, {"link": "https://example.com/s1", "claim": 2}]},
        {"claim": "A view of the author, citing nothing."},
    ],
}
REVIEW = {
    "status": "complete",
    "text": "Reviewed draft.",
    "run": "reconcile-20261111-abc",
    "reviewers": ["fake/reviewer-a", "fake/reviewer-b"],
    "changes": "Dropped one unsupported line.",
    "diff": "- a\n+ b",
}
PLAN = {
    "topic": NAME,
    "text": "Plan as the agent wrote it.",
    "items": [{"kind": "question", "text": "What do caches cost?"}, {"kind": "search", "text": "remote build cache"}, {"kind": "page", "text": "https://example.com/bench"}],
    "review": {**REVIEW, "text": "Reviewed plan."},
}


def link(n: int) -> str:
    return f"https://example.com/s{n}"


def written(**extra: Any) -> dict[str, Any]:
    return {
        "answer": "Build caches help large repos.",
        "claims": [
            {"claim": "Caches cut rebuilds.", "sources": [link(1)], "label": "Sound", "reason": "Two sources agree.", "cites": ["S1.2", "S2.1", "S9.9"]},
            {"claim": "Caches are magic.", "sources": [link(1)], "label": "Noise", "reason": "Hype."},
        ],
        "disagreements": [],
        "gaps": ["No source covers Windows."],
        "model_view": "My view: invalidation is the hard part.",
        **extra,
    }


class TopicTest(PipelineTest):
    def setUp(self) -> None:
        super().setUp()
        with closing(sqlite.open_store(self.store)) as store:
            for n, (title, claims) in enumerate(SOURCES, 1):
                record = SourceRecord(link(n), "article", False, AT, AT, f"hash{n}", "read", title=title, abstract=f"{title}: build cache notes.")
                source_id = store.add_source(record, PageText("page", (), (0,) * 64))
                store.add_link(link(n), source_id, "key", AT)
                for ord, (text, quote) in enumerate(claims, 1):
                    store.add_claim(source_id, ord, ClaimRecord("claim", text, "asserted", (QuoteRecord(quote, 0, len(quote)),)), AT)
                store.index_source(source_id)

    def cmd(self, command: str, body: dict[str, Any], fake: FakeHost | None = None) -> tuple[dict[str, Any], int]:
        return app.run(command, None, body, (fake or FakeHost()).host())

    def go(self, command: str, body: dict[str, Any], **extra: Any) -> tuple[dict[str, Any], int]:
        """Call without approval, expect the one decision, answer its go option with yes and resend with ``extra``."""
        first, code = self.cmd(command, body)
        self.assertEqual(code, 4, first)
        [decision] = first["decisions"]
        [go] = [option for option in decision["options"] if option["id"] == "go"]
        approval = {**go["then"]["resend"]["approval"], "words": "yes"}
        return self.cmd(command, {**body, **extra, "approval": approval})

    def create(self) -> None:
        answer, code = self.go("topic create", CREATE)
        self.assertEqual(code, 0, answer)

    def save(self, draft: dict[str, Any] = DRAFT, **extra: Any) -> tuple[dict[str, Any], int]:
        return self.go("topic save", {"name": NAME, "draft": draft}, review=extra.pop("review", REVIEW), **extra)

    def count(self, table: str) -> int:
        return self.rows(f"SELECT count(*) FROM {table}")[0][0]

    def sql(self, statement: str, *args: Any) -> None:
        with closing(sqlite3.connect(self.store)) as db:
            db.execute(statement, args)
            db.commit()

    def mark(self, topic_id: int, source_id: int) -> None:
        self.sql("INSERT INTO marks (topic_id, source_id, p, judge_model, at) VALUES (?, ?, 0.6, 'fake-judge-1', ?)", topic_id, source_id, AT)

    def versions(self) -> list[tuple]:
        return self.rows("SELECT topic_id, n, text, writer_model, thinking, cross_check, reviewers, run, changes, diff FROM versions ORDER BY topic_id, n")


class TopicTests(TopicTest):
    def test_create_asks_the_plan_start_confirm_and_a_request_naming_the_topic_runs_it(self) -> None:
        answer, code = self.cmd("topic create", CREATE)
        self.assertEqual((code, [d["kind"] for d in answer["decisions"]]), (4, ["confirm"]), answer)
        self.assertEqual((self.count("topics"), self.count("approvals")), (0, 0), "a stop stores nothing")

        answer, code = self.cmd("topic create", {**CREATE, "approval": {"by": "request", "words": "Let us look at something else."}})
        self.assertEqual((code, self.count("topics")), (4, 0), "words that do not name the topic are not its confirm")

        answer, code = self.go("topic create", {"name": f"  {NAME}  ", "brief": f"  {BRIEF}  "})
        self.assertEqual((code, answer["result"]["result"]), (0, "created"), answer)
        self.assertEqual(
            answer["result"]["topic"],
            {"name": NAME, "brief": BRIEF, "followed": True, "archived": None, "reviewed_up_to": None, "version": None, "version_saved": None},
        )
        self.assertEqual(self.rows("SELECT name, brief, followed, archived_at FROM topics"), [(NAME, BRIEF, 1, None)])
        self.assertEqual(self.rows("SELECT command, change_kind, by, words FROM approvals"), [("topic create", "plan_start", "confirm", "yes")])

        # The name is unique whatever its case: the second create changes nothing and asks nothing.
        answer, code = self.cmd("topic create", {"name": NAME.upper(), "brief": "Another brief."})
        self.assertEqual((code, answer["result"]["result"], answer["decisions"]), (0, "already stored", []), answer)
        self.assertEqual((self.count("topics"), self.count("approvals")), (1, 1))

        # A request whose words name the topic is its confirm (the default setting is "always").
        answer, code = self.cmd("topic create", {"name": "Remote caches", "brief": "Shared caches.", "approval": {"by": "request", "words": "start a topic on REMOTE CACHES"}})
        self.assertEqual((code, answer["result"]["result"]), (0, "created"), answer)

    def test_topic_actions_and_fields_are_checked_and_a_topic_not_stored_is_exit_1(self) -> None:
        for command, body in (("topic", {}), ("topic create", {"name": NAME}), ("topic create", {"name": " ", "brief": BRIEF}), ("topic list", {"name": NAME})):
            with self.subTest(command=command, body=body):
                self.assertEqual(self.cmd(command, body)[1], 2)
        needs = {
            "topic draft": {"name": "Nope"},
            "topic save": {"name": "Nope", "draft": DRAFT},
            "topic follow": {"name": "Nope"},
            "topic unfollow": {"name": "Nope"},
            "topic nothing_to_save": {"name": "Nope"},
            "plan show": {"topic": "Nope"},
        }
        for command, body in needs.items():
            with self.subTest(command=command):
                answer, code = self.cmd(command, body)
                self.assertEqual((code, answer["problems"][0]["problem"]), (1, "not stored; create it first"), answer)
        self.assertEqual((self.count("topics"), self.count("approvals"), self.count("versions")), (0, 0, 0))

    def test_follow_and_unfollow_are_their_own_confirms_and_a_topic_already_there_asks_nothing(self) -> None:
        self.create()
        answer, code = self.cmd("topic follow", {"name": NAME})
        self.assertEqual((code, answer["result"]["result"], answer["decisions"]), (0, "already followed", []), answer)
        answer, code = self.go("topic unfollow", {"name": NAME})
        self.assertEqual((code, answer["result"]["result"], answer["result"]["topic"]["followed"]), (0, "unfollowed", False), answer)
        answer, code = self.cmd("topic unfollow", {"name": NAME.lower()})
        self.assertEqual((code, answer["result"]["result"]), (0, "not followed"), answer)
        answer, code = self.go("topic follow", {"name": NAME})
        self.assertEqual((code, answer["result"]["topic"]["followed"]), (0, True), answer)
        self.assertEqual(
            self.rows("SELECT command, change_kind, by FROM approvals ORDER BY id"),
            [("topic create", "plan_start", "confirm"), ("topic unfollow", "unfollow", "confirm"), ("topic follow", "follow", "confirm")],
        )
        listed, code = self.cmd("topic list", {})
        self.assertEqual((code, [topic["name"] for topic in listed["result"]["topics"]]), (0, [NAME]))

    def test_nothing_to_save_stores_the_date_and_clears_only_that_topics_marks(self) -> None:
        self.create()
        self.sql("INSERT INTO topics (name, brief) VALUES ('Other topic', 'Something else.')")
        for topic_id in (1, 2):
            self.mark(topic_id, 1)
            self.mark(topic_id, 2)
        fake = FakeHost()
        before = datetime.now(timezone.utc)
        answer, code = self.cmd("topic nothing_to_save", {"name": NAME}, fake)
        self.assertEqual((code, answer["result"]["result"], answer["result"]["marks_cleared"], answer["decisions"]), (0, "nothing to save", 2, []), answer)
        [(reviewed,)] = self.rows("SELECT reviewed_up_to FROM topics WHERE id = 1")
        self.assertLessEqual(before.replace(microsecond=0), datetime.fromisoformat(reviewed))
        self.assertEqual(self.rows("SELECT topic_id, cleared_at IS NOT NULL FROM marks ORDER BY id"), [(1, 1), (1, 1), (2, 0), (2, 0)])
        self.assertEqual(self.rows("SELECT reviewed_up_to FROM topics WHERE id = 2"), [(None,)])
        self.assertEqual((self.count("versions"), self.count("version_claims")), (0, 0), "no version")
        self.assertEqual(self.count("approvals"), 1, "the topic's own create is the only row: nothing to save writes none")
        self.assertEqual([call[0] for call in fake.calls], ["open_store"], "it asks no Reconcile and makes no model or judge call")


class VersionTests(TopicTest):
    def test_a_save_always_stops_and_the_users_confirm_with_a_review_stores_the_next_version_with_copied_claims(self) -> None:
        # Every setting says "never"; the version_save stop does not read them.
        self.configure("[profiles.smoke.confirm]\n" + "".join(f'{kind} = "never"\n' for kind in CHANGE_KINDS))
        answer, code = self.cmd("topic create", CREATE)
        self.assertEqual((code, answer["decisions"]), (0, []), "a never setting runs the plan start without a stop")
        self.mark(1, 1)
        self.mark(1, 2)
        body = {"name": NAME, "draft": DRAFT}

        first, code = self.cmd("topic save", body)
        self.assertEqual(code, 4, first)
        [decision] = first["decisions"]
        self.assertEqual(decision["kind"], "version_save")
        self.assertIn("version 1", decision["question"])
        self.assertIn("3 stored claims", decision["question"], "four cites name three claims: the repeat counts once")
        [go] = [option for option in decision["options"] if option["id"] == "go"]
        approval = {**go["then"]["resend"]["approval"], "words": "yes, save it"}
        self.assertEqual(self.count("versions"), 0)

        # No approval that is not the user's confirm of this decision saves: not a request, not another change's confirm.
        request = {"by": "request", "words": f"Save the {NAME} draft as a version."}
        answer, code = self.cmd("topic save", {**body, "review": REVIEW, "approval": request})
        self.assertEqual((code, [d["kind"] for d in answer["decisions"]]), (4, ["version_save"]), answer)
        answer, code = self.cmd("topic save", {**body, "review": REVIEW, "approval": {**approval, "decision": "0" * 16}})
        self.assertEqual((code, answer["problems"][0]["problem"]), (2, "this approval is for a different change"), answer)
        answer, code = self.cmd("topic save", {**body, "approval": approval})
        self.assertEqual((code, answer["problems"][0]["field"]), (2, "review"), "a confirmed save with no review is bad input")
        self.assertEqual((self.count("versions"), self.count("approvals")), (0, 1))

        # The resend carries the review Reconcile made after the decision was returned; it is the same decision.
        answer, code = self.cmd("topic save", {**body, "review": REVIEW, "approval": approval})
        self.assertEqual((code, answer["result"]["result"]), (0, "saved version 1"), answer)
        self.assertEqual(
            answer["result"]["version"],
            {
                "n": 1,
                "cross_check": "complete",
                "reviewers": REVIEW["reviewers"],
                "run": REVIEW["run"],
                "changes": REVIEW["changes"],
                "diff": REVIEW["diff"],
                "text": "Reviewed draft.",
                "saved": answer["result"]["version"]["saved"],
                "claims": 3,
            },
        )
        self.assertEqual((answer["result"]["topic"]["version"], answer["result"]["marks_cleared"]), (1, 2))
        self.assertEqual(
            self.versions(),
            [(1, 1, "Reviewed draft.", "fake/opus", "medium", "complete", json.dumps(REVIEW["reviewers"]), REVIEW["run"], REVIEW["changes"], REVIEW["diff"])],
            "the reviewed text is stored, not the draft's",
        )
        copies = self.rows("SELECT v.text, v.quotes, s.key_link FROM version_claims v JOIN claims c ON c.id = v.claim_id JOIN sources s ON s.id = c.source_id ORDER BY v.rowid")
        self.assertEqual(
            copies,
            [
                ("Caches cut rebuilds.", json.dumps(["Rebuilds drop by half."]), link(1)),
                ("Large repos rebuild too much.", json.dumps(["Large repos rebuild everything."]), link(2)),
                ("A build cache stores outputs.", json.dumps(["Outputs are stored by input hash."]), link(1)),
            ],
        )
        self.assertEqual(self.rows("SELECT topic_id, cleared_at IS NOT NULL FROM marks"), [(1, 1), (1, 1)])
        self.assertEqual(
            self.rows("SELECT command, change_kind, by, words, decision_id FROM approvals WHERE change_kind = 'version_save'"),
            [("topic save", "version_save", "confirm", "yes, save it", decision["id"])],
        )

        # A copy is the claim as it was: a redo that replaces the claim leaves the version's text and quotes alone.
        self.sql("UPDATE claims SET text = 'Rewritten after a redo.', replaced_at = ? WHERE text = 'Caches cut rebuilds.'", AT)
        self.sql("UPDATE quotes SET text = 'A rewritten quote.' WHERE text = 'Rebuilds drop by half.'")
        answer, code = self.go("topic save", {"name": NAME, "draft": {"writer_model": "fake/opus", "thinking": None, "claims": []}}, review={**REVIEW, "text": "Second."})
        self.assertEqual((code, answer["result"]["result"]), (0, "saved version 2"), answer)
        self.assertEqual([row[:2] for row in self.versions()], [(1, 1), (1, 2)], "a new version is numbered next and the first stays")
        self.assertEqual(self.rows("SELECT text, quotes FROM version_claims WHERE n = 1 ORDER BY rowid")[0], ("Caches cut rebuilds.", json.dumps(["Rebuilds drop by half."])))

    def test_a_save_that_is_not_cross_checked_carries_its_reason_and_a_bad_review_is_bad_input(self) -> None:
        self.create()
        review = {"status": "not_cross_checked", "reason": "Reconcile is not ready: no reviewer models", "text": "Unreviewed draft."}
        answer, code = self.save(review=review)
        self.assertEqual((code, answer["result"]["version"]["cross_check"]), (0, "not cross-checked: Reconcile is not ready: no reviewer models"), answer)
        self.assertEqual(
            self.rows("SELECT text, cross_check, reviewers, run, changes, diff FROM versions"),
            [("Unreviewed draft.", "not cross-checked: Reconcile is not ready: no reviewer models", None, None, None, None)],
        )
        bad = {
            "no text": {**REVIEW, "text": " "},
            "an unknown status": {**REVIEW, "status": "maybe"},
            "complete without its run": {k: v for k, v in REVIEW.items() if k != "run"},
            "complete without reviewers": {**REVIEW, "reviewers": []},
            "complete without changes": {**REVIEW, "changes": None},
            "not cross-checked without a reason": {"status": "not_cross_checked", "text": "Draft."},
            "a field of its own": {**REVIEW, "verdict": "fine"},
            "not an object": "reviewed",
        }
        for named, value in bad.items():
            with self.subTest(named):
                answer, code = self.save(review=value)
                self.assertEqual(code, 2, answer)
        self.assertEqual(self.count("versions"), 1, "only the valid review stored a version")

    def test_a_draft_that_cites_a_claim_that_is_not_stored_is_bad_input_before_any_decision(self) -> None:
        self.create()
        cases = {
            "a source not stored": {"link": "https://example.com/nowhere", "claim": 1},
            "a claim the source does not hold": {"link": link(1), "claim": 9},
            "a cite that is not {link, claim}": {"link": link(1)},
        }
        for named, cite in cases.items():
            with self.subTest(named):
                draft = {**DRAFT, "claims": [{"claim": "x", "cites": [cite]}]}
                answer, code = self.cmd("topic save", {"name": NAME, "draft": draft})
                self.assertEqual((code, answer["decisions"]), (2, []), answer)
        answer, code = self.cmd("topic save", {"name": NAME, "draft": {**DRAFT, "writer_model": ""}})
        self.assertEqual(code, 2, answer)


class DraftTests(TopicTest):
    def host(self, *replies: ports.Reply) -> FakeHost:
        phrasing = tool_reply({"phrasings": ["build cache", "large repos"]}, model="fake/opus")
        return FakeHost(
            replies={"atlas_query": [phrasing] * len(replies), "atlas_answer": list(replies)},
            judge_answer=by_title({"Cache basics": 0.9, "Large repos": 0.4}),
        )

    def test_a_draft_stores_nothing_but_the_query_and_its_claims_cite_the_keys_the_writer_was_given(self) -> None:
        self.create()
        # The writer sends a valid tally line anyway (as `ask` would store it); a draft keeps none.
        tally = [{"who": "Ann", "subject": "build caches", "link": link(1), "direction": "towards"}]
        fake = self.host(tool_reply(written(tally_lines=tally), model="fake/opus", thinking="medium"), tool_reply(written(), model="fake/opus"))
        tables = ("topics", "versions", "version_claims", "plans", "marks", "tally", "approvals")
        before = [self.count(table) for table in tables]
        answer, code = self.cmd("topic draft", {"name": NAME.lower(), "context": "picking a CI setup"}, fake)
        self.assertEqual(code, 0, answer)
        self.assertEqual([self.count(table) for table in tables], before, "a draft stores no topic, version, mark, tally line or approval")
        self.assertEqual(self.rows("SELECT op, original, question FROM queries"), [("ask", BRIEF, BRIEF)])
        result = answer["result"]
        self.assertEqual([item["link"] for item in result["sources"]], [link(1), link(2)])
        draft = result["draft"]
        self.assertEqual((draft["text"], draft["labels"], draft["writer_model"], draft["thinking"]), ("Build caches help large repos.", "checked", "fake/opus", "medium"))
        self.assertEqual(draft["claims"][0]["cites"], [{"link": link(1), "claim": 2}, {"link": link(2), "claim": 1}], "keys map to source link and position")
        self.assertEqual(draft["claims"][1]["cites"], [])
        self.assertEqual([problem["field"] for problem in answer["problems"]], ["claims"], "a key never given (S9.9) is a problem")
        self.assertNotIn("tally_lines", draft)
        self.assertIn("save it as version 1", answer["next"][0]["label"])
        call = self.calls(fake, "call", "atlas_answer")[0]
        message = call[2][-1]["content"]
        self.assertIn("[S1.2] (claim, asserted) Caches cut rebuilds.", message)
        self.assertIn(f"Brief: {BRIEF}", message)
        self.assertIn("Context: picking a CI setup", message)
        self.assertNotIn("Agreed version", message, "a topic with no saved version has none to revise")
        self.assertEqual([tool["name"] for tool in call[3]], ["answer"])
        self.assertNotIn("tally_lines", json.dumps(call[3]))

        # Once a version is saved the next draft revises it, and its Next says which version it would be.
        saved, code = self.save()
        self.assertEqual(code, 0, saved)
        answer, code = self.cmd("topic draft", {"name": NAME}, fake)
        self.assertEqual(code, 0, answer)
        self.assertIn("save it as version 2", answer["next"][0]["label"])
        message = self.calls(fake, "call", "atlas_answer")[1][2][-1]["content"]
        self.assertIn("Agreed version 1", message)
        self.assertIn("Reviewed draft.", message)

    def test_a_draft_is_stopped_before_searching_when_the_judge_is_not_set_up_and_a_failed_writer_stores_nothing(self) -> None:
        self.create()
        fake = FakeHost(setup_problem=ports.SetupProblem("The Jev key file is missing", ("Put the key in the file.",), "/fake/key.env"))
        answer, code = self.cmd("topic draft", {"name": NAME}, fake)
        self.assertEqual((code, [d["kind"] for d in answer["decisions"]]), (4, ["judge_setup"]), answer)
        self.assertEqual([call for call in fake.calls if call[0] in ("call", "judge")], [])
        self.assertEqual(self.count("queries"), 0)

        fake = self.host(text_reply("prose", model="fake/opus"), text_reply("more prose", model="fake/opus"))
        answer, code = self.cmd("topic draft", {"name": NAME}, fake)
        self.assertEqual((code, answer["problems"][-1]["field"]), (1, "draft"), answer)
        self.assertEqual(len(answer["result"]["sources"]), 2, "the sources found stay in the reply")


class PlanTests(TopicTest):
    def test_one_plan_confirm_covers_both_commands_and_the_plan_is_stored_with_its_review(self) -> None:
        # The front door sends both bodies with no approval before the topic exists; each decides alone.
        first, code = self.cmd("topic create", CREATE)
        second, code2 = self.cmd("plan save", PLAN)
        self.assertEqual((code, code2), (4, 4), second)
        self.assertEqual(first["decisions"][0]["question"], second["decisions"][0]["question"], "one question for both")
        self.assertNotEqual(first["decisions"][0]["id"], second["decisions"][0]["id"])
        self.assertEqual((self.count("topics"), self.count("plans")), (0, 0))

        # Its confirm with no topic stored is a problem, not a plan.
        approval = {"by": "confirm", "decision": second["decisions"][0]["id"], "choice": "go", "words": "yes"}
        answer, code = self.cmd("plan save", {**PLAN, "approval": approval})
        self.assertEqual((code, answer["problems"][0]["problem"], self.count("plans")), (1, "not stored; create it first", 0), answer)

        created, code = self.cmd("topic create", {**CREATE, "approval": {**approval, "decision": first["decisions"][0]["id"]}})
        self.assertEqual(code, 0, created)
        answer, code = self.cmd("plan save", {**PLAN, "approval": approval})
        self.assertEqual(code, 0, answer)
        plan = answer["result"]["plan"]
        self.assertEqual((plan["cross_check"], plan["run"], plan["reviewers"], plan["text"]), ("complete", REVIEW["run"], REVIEW["reviewers"], "Reviewed plan."))
        self.assertEqual([(item["item"], item["kind"]) for item in plan["open_items"]], [(1, "question"), (2, "search"), (3, "page")])
        self.assertEqual(self.rows("SELECT text, cross_check, run, changes FROM plans"), [("Reviewed plan.", "complete", REVIEW["run"], REVIEW["changes"])], "the reviewed text is stored")
        self.assertEqual(
            self.rows("SELECT command, change_kind, by FROM approvals ORDER BY id"),
            [("topic create", "plan_start", "confirm"), ("plan save", "plan_start", "confirm")],
        )

        # A plan needs its review and well-formed items.
        for named, body in {"no review": {k: v for k, v in PLAN.items() if k != "review"}, "no items": {**PLAN, "items": []}, "a kind outside the four": {**PLAN, "items": [{"kind": "idea", "text": "x"}]}}.items():
            with self.subTest(named):
                self.assertEqual(self.cmd("plan save", body)[1], 2)
        self.assertEqual(self.count("plans"), 1)

    def test_marked_items_leave_the_open_list_and_show_lists_the_newest_plan_first_with_its_run(self) -> None:
        self.create()
        answer, code = self.go("plan save", PLAN)
        self.assertEqual(code, 0, answer)
        plan_id = answer["result"]["plan"]["plan"]
        answer, code = self.cmd("plan mark", {"plan": plan_id, "item": 2, "state": "done"})
        self.assertEqual((code, answer["result"]["item"]["state"], answer["result"]["open"], answer["decisions"]), (0, "done", 2, []), answer)
        answer, code = self.cmd("plan mark", {"plan": plan_id, "item": 1, "state": "skipped"})
        self.assertEqual((code, answer["result"]["open"]), (0, 1), answer)
        self.assertEqual(self.count("approvals"), 2, "marking asks nothing and writes no approval row: only create and save did")

        newer = {**PLAN, "text": "Second plan.", "items": [{"kind": "source", "text": "https://example.com/s1"}], "review": {"status": "not_cross_checked", "reason": "not ready", "text": "Second reviewed."}}
        answer, code = self.go("plan save", newer)
        self.assertEqual(code, 0, answer)
        shown, code = self.cmd("plan show", {})
        self.assertEqual(code, 0, shown)
        [latest, earlier] = shown["result"]["plans"]
        self.assertEqual((latest["cross_check"], latest["run"], latest["text"]), ("not cross-checked: not ready", None, "Second reviewed."))
        self.assertEqual((earlier["cross_check"], earlier["run"], earlier["done"], earlier["skipped"]), ("complete", REVIEW["run"], 1, 1))
        self.assertEqual([item["item"] for item in earlier["open_items"]], [3])
        other, code = self.cmd("plan show", {"topic": NAME.upper()})
        self.assertEqual((code, len(other["result"]["plans"])), (0, 2))

        for named, body in {"a plan not stored": {"plan": 99, "item": 1, "state": "done"}, "an item the plan lacks": {"plan": plan_id, "item": 9, "state": "done"}}.items():
            with self.subTest(named):
                self.assertEqual(self.cmd("plan mark", body)[1], 1)
        for named, body in {"open is not a mark": {"plan": plan_id, "item": 1, "state": "open"}, "a plan that is text": {"plan": "1", "item": 1, "state": "done"}}.items():
            with self.subTest(named):
                self.assertEqual(self.cmd("plan mark", body)[1], 2)


if __name__ == "__main__":
    unittest.main()
