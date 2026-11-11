"""``note``, ``archive``, ``restore``, notes in ``ask`` answers and note proposals through ``app.run`` (AC-6.1).

Every test uses the fake host and its own temporary ``HOME`` and ``XDG_STATE_HOME``. Each absence
(a note hidden, a proposal not made, a stop not asked) is paired with the presence it differs from.
"""

from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from datetime import datetime, timezone
from typing import Any
from unittest import mock

from tests.fakes.fake_host import FakeHost, tool_reply
from tests.test_answer import NOISE, SOUND_2, SOURCES, AskTest, answered
from tests.test_search import link, seed

from atlas.core import app, spend  # noqa: E402
from atlas.store import VersionRecord, sqlite  # noqa: E402

WORDS = "Lean towards Simon Willison on agent skills."
GOOD = {"who": "Simon Willison", "subject": "agent skills", "lean": "towards", "reason": "Careful, hands-on write-ups."}


def requested(body: dict[str, Any], words: str = WORDS) -> dict[str, Any]:
    return {**body, "approval": {"by": "request", "words": words}}


def local_date(stamp: str) -> str:
    return datetime.fromisoformat(stamp).astimezone().date().isoformat()


def line(who: str, subject: str, n: int, direction: str) -> dict[str, str]:
    return {"who": who, "subject": subject, "link": link(n), "direction": direction}


class NotesTest(AskTest):
    def run_cmd(self, command: str, body: dict[str, Any]) -> tuple[dict[str, Any], int]:
        return app.run(command, None, body, FakeHost().host())

    def save(self, **fields: Any) -> tuple[dict[str, Any], int]:
        who = fields.get("who", GOOD["who"])
        return self.run_cmd("note", requested({**GOOD, **fields}, f"Note about {who}."))

    def note_rows(self) -> list[tuple]:
        return self.rows("SELECT id, who, subject, lean, reason, at, archived_at FROM notes ORDER BY id")

    def counts(self) -> dict[str, int]:
        tables = ("sources", "claims", "links", "page_text", "notes", "tally")
        return {table: self.rows(f"SELECT count(*) FROM {table}")[0][0] for table in tables}

    def approvals(self) -> list[tuple]:
        return self.rows("SELECT command, change_kind, by, words FROM approvals ORDER BY id")

    def sent(self, fake: FakeHost, n: int = 0) -> str:
        """The text of the ``n``th ``atlas_answer`` call's last message."""
        return self.calls(fake, "call", "atlas_answer")[n][2][-1]["content"]


class NoteTests(NotesTest):
    def test_a_note_is_saved_then_changed_in_place_and_another_subject_is_kept_apart(self) -> None:
        first = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
        with mock.patch.object(spend, "local_now", return_value=first):
            answer, code = self.run_cmd("note", requested(GOOD))
        self.assertEqual(code, 0, answer)
        [saved] = self.note_rows()
        note_id = saved[0]
        self.assertEqual(saved[1:], ("Simon Willison", "agent skills", "towards", GOOD["reason"], "2026-11-01T12:00:00+00:00", None))
        self.assertEqual(
            answer["result"],
            {"note": {**GOOD, "date": local_date(saved[5])}, "result": "saved new"},
        )
        self.assertEqual(self.approvals(), [("note", "note", "request", WORDS)])

        # The same pair, spelled with other case and spaces, changes the one row in place.
        later = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
        body = requested({"who": " SIMON willison ", "subject": "Agent Skills", "lean": "against", "reason": "Changed my mind."}, "note simon willison")
        with mock.patch.object(spend, "local_now", return_value=later):
            answer, code = self.run_cmd("note", body)
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["result"], "changed (earlier lean: towards)")
        self.assertEqual(
            self.note_rows(),
            [(note_id, "Simon Willison", "agent skills", "against", "Changed my mind.", "2026-11-02T12:00:00+00:00", None)],
        )
        self.assertEqual(len(self.approvals()), 2, "each applied change writes one approvals row")

        # Another subject for the same who is its own note.
        answer, code = self.save(subject="evals", lean="against")
        self.assertEqual((code, answer["result"]["result"]), (0, "saved new"))
        self.assertEqual([(row[0] == note_id, row[2], row[3]) for row in self.note_rows()], [(True, "agent skills", "against"), (False, "evals", "against")])

    def test_a_field_that_is_missing_blank_or_not_allowed_is_exit_2_naming_it_and_stores_nothing(self) -> None:
        cases = {
            "who": {"who": "   "},
            "subject": {"subject": ""},
            "reason": {"reason": 7},
            "lean": {"lean": "sideways"},
            "extra": {"stars": 5},
        }
        for field, change in cases.items():
            with self.subTest(field):
                answer, code = self.run_cmd("note", requested({**GOOD, **change}))
                self.assertEqual((code, answer["problems"][0]["field"]), (2, "stars" if field == "extra" else field), answer)
        missing = {key: value for key, value in GOOD.items() if key != "reason"}
        answer, code = self.run_cmd("note", requested(missing))
        self.assertEqual((code, answer["problems"][0]["field"]), (2, "reason"))
        self.assertEqual((self.note_rows(), self.approvals()), ([], []))
        answer, code = self.run_cmd("note", requested(GOOD))
        self.assertEqual(code, 0, "the same call with valid fields saves")

    def test_request_words_with_the_who_run_at_once_and_words_without_it_get_one_confirm(self) -> None:
        answer, code = self.run_cmd("note", requested(GOOD, "yes, save that note"))
        self.assertEqual(code, 4, answer)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "confirm")
        self.assertEqual((self.note_rows(), self.approvals()), ([], []), "a stop changes nothing")

        resend = {**GOOD, "approval": {"by": "confirm", "decision": decision["id"], "choice": "go", "words": "yes"}}
        answer, code = self.run_cmd("note", resend)
        self.assertEqual((code, answer["result"]["result"]), (0, "saved new"))
        self.assertEqual(self.approvals(), [("note", "note", "confirm", "yes")])

        # With the who in the words (any case) the request approval runs it under the default "always".
        answer, code = self.run_cmd("note", requested({**GOOD, "subject": "evals"}, "note SIMON WILLISON on evals"))
        self.assertEqual(code, 0, answer)
        self.assertEqual(self.approvals()[1], ("note", "note", "request", "note SIMON WILLISON on evals"))


class ArchiveSourceTests(NotesTest):
    joined = "https://alias.example.com/skills"

    def setUp(self) -> None:
        super().setUp()
        seed(self.store, [{**source, "claims": [f"{source['title']} states a claim."]} for source in SOURCES])
        with closing(sqlite.open_store(self.store)) as store:
            store.add_link(self.joined, store.source_for_link(link(1)).source.id, "other", "2026-11-01T10:00:00+00:00")

    def test_archiving_a_source_hides_it_from_find_ask_and_add_and_restore_returns_it(self) -> None:
        fake = self.host(*[tool_reply(answered([SOUND_2]), model="fake/opus")] * 2)
        before = self.counts()
        self.assertEqual((before["sources"], before["claims"], before["links"]), (4, 4, 5), "the counts compared below are not empty")
        self.assertIn(link(1), self.links(self.find(fake)[0]))
        self.ask(fake)
        self.assertIn(link(1), self.sent(fake, 0))

        # A source is reached through any of its links: archive by a joined link, not the key link.
        joined = self.joined
        answer, code = self.run_cmd("archive", requested({"link": joined}, f"Archive {joined}"))
        self.assertEqual((code, answer["result"]), (0, {"link": link(1), "result": "archived"}), answer)
        self.assertEqual(self.rows("SELECT archived_at IS NOT NULL FROM sources WHERE key_link = ?", link(1)), [(1,)])
        found = self.links(self.find(fake)[0])
        self.assertEqual((link(1) in found, link(2) in found), (False, True))
        self.ask(fake)
        self.assertNotIn(link(1), self.sent(fake, 1))
        added, _ = self.add(fake, {"items": [{"link": link(1)}]})
        self.assertTrue(added["result"]["items"][0]["result"].startswith("archived "), added)
        self.assertEqual(self.calls(fake, "read"), [], "an archived link is matched before any read")
        self.assertEqual(self.counts(), before, "archive deletes no row and keeps claims, links and page text")

        answer, code = self.run_cmd("restore", requested({"link": link(1)}, f"Restore {link(1)}"))
        self.assertEqual((code, answer["result"]["result"]), (0, "restored"), answer)
        self.assertEqual(self.rows("SELECT archived_at FROM sources WHERE key_link = ?", link(1)), [(None,)])
        self.assertIn(link(1), self.links(self.find(fake)[0]))
        added, _ = self.add(fake, {"items": [{"link": link(1)}]})
        self.assertTrue(added["result"]["items"][0]["result"].startswith("already stored"), added)
        self.assertEqual(self.counts(), before)
        self.assertEqual([row[:3] for row in self.approvals()], [("archive", "archive", "request"), ("restore", "restore", "request")])

    def test_a_target_already_in_the_asked_state_changes_nothing_and_asks_nothing(self) -> None:
        answer, code = self.run_cmd("archive", {"link": link(1)})
        self.assertEqual((code, len(answer["decisions"])), (4, 1), "a change that would run asks first")
        self.assertEqual(self.rows("SELECT count(*) FROM sources WHERE archived_at IS NOT NULL"), [(0,)])

        request = requested({"link": link(1)}, f"Archive {link(1)}")
        self.assertEqual(self.run_cmd("archive", request)[1], 0)
        answer, code = self.run_cmd("archive", {"link": link(1)})
        self.assertEqual(code, 0, answer)
        self.assertTrue(answer["result"]["result"].startswith("already archived "), answer)
        self.assertEqual(len(self.approvals()), 1)
        self.run_cmd("restore", requested({"link": link(1)}, f"Restore {link(1)}"))
        answer, code = self.run_cmd("restore", {"link": link(1)})
        self.assertEqual((code, answer["result"]["result"]), (0, "not archived"))
        self.assertEqual(len(self.approvals()), 2)

    def test_a_link_that_is_not_stored_or_a_citation_not_built_yet_is_reported_and_changes_nothing(self) -> None:
        answer, code = self.run_cmd("archive", {"link": "https://example.com/never-added"})
        self.assertEqual((code, answer["result"]["result"]), (0, "not stored"))
        self.assertEqual(answer["problems"][0]["problem"], "not stored; add it first")
        for command in ("archive", "restore"):
            with self.subTest(command=command):
                answer, code = self.run_cmd(command, {"citation": {"repo": "r", "file": "f"}})
                self.assertEqual(code, 1, answer)
                self.assertIn("is not available in this Atlas build yet", answer["problems"][0]["problem"])
        for body in ({}, {"link": link(1), "note": {"who": "a", "subject": "b"}}, {"link": "not a link"}):
            with self.subTest(body=body):
                self.assertEqual(self.run_cmd("archive", body)[1], 2)
        self.assertEqual(self.approvals(), [])


class ArchiveNoteTests(NotesTest):
    def test_restoring_a_note_while_another_note_holds_its_pair_changes_nothing(self) -> None:
        self.assertEqual(self.save()[1], 0)
        target = {"note": {"who": "simon willison", "subject": "AGENT skills"}}
        answer, code = self.run_cmd("archive", requested(target, "Archive my note on Simon Willison"))
        self.assertEqual((code, answer["result"]["result"]), (0, "archived"), answer)
        answer, code = self.save(lean="against", reason="Second thoughts.")
        self.assertEqual(answer["result"]["result"], "saved new", "an archived note does not hold the pair")
        self.assertEqual([row[0] for row in self.note_rows() if row[6] is None], [2])
        before = (self.note_rows(), self.approvals())

        answer, code = self.run_cmd("restore", requested(target, "Restore my note on Simon Willison"))
        self.assertEqual((code, answer["result"]["result"]), (0, "not restored"), answer)
        self.assertIn("Simon Willison on agent skills", answer["problems"][0]["problem"])
        self.assertEqual((self.note_rows(), self.approvals()), before)

        # Once the pair is free again, restore brings back the newest archived note.
        self.assertEqual(self.run_cmd("archive", requested(target, "Archive my note on Simon Willison"))[1], 0)
        answer, code = self.run_cmd("restore", requested(target, "Restore my note on Simon Willison"))
        self.assertEqual((code, answer["result"]["result"]), (0, "restored"), answer)
        self.assertEqual([(row[0], row[6] is None) for row in self.note_rows()], [(1, False), (2, True)])
        self.assertEqual(self.run_cmd("restore", {"note": {"who": "Nobody", "subject": "x"}})[0]["result"]["result"], "not stored")

    def test_a_note_archive_needs_the_who_in_the_words(self) -> None:
        self.save()
        target = {"note": {"who": "Simon Willison", "subject": "agent skills"}}
        answer, code = self.run_cmd("archive", requested(target, "archive that note"))
        self.assertEqual((code, answer["decisions"][0]["kind"]), (4, "confirm"))
        self.assertEqual(self.note_rows()[0][6], None)
        self.assertEqual(self.run_cmd("archive", requested(target, "archive the SIMON WILLISON note"))[1], 0)
        self.assertIsNotNone(self.note_rows()[0][6])


class NotesInAnswerTests(NotesTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, SOURCES)
        # Ann's alias is stored as a JSON list; Acme is the publisher of the first two sources.
        self.rows_write("UPDATE sources SET author_aliases = ? WHERE key_link = ?", '["Annie L."]', link(1))

    def rows_write(self, sql: str, *args: Any) -> None:
        with closing(sqlite3.connect(self.store)) as db:
            db.execute(sql, args)
            db.commit()

    def test_notes_that_may_apply_go_to_the_model_and_an_applied_key_shows_beside_its_label(self) -> None:
        self.save(who="Annie L.", subject="build caches", lean="towards", reason="Measures before claiming.")
        self.save(who="acme", subject="vendor claims", lean="against", reason="Sells the caches.")
        self.save(who="Zed", subject="build caches", lean="towards", reason="Nobody searched.")
        applied = {**SOUND_2, "notes": ["N1", "N9"]}
        twice = {**NOISE, "notes": ["N2", "N2"]}
        fake = self.host(tool_reply(answered([twice, applied]), model="fake/opus"))
        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)

        sent = self.sent(fake)
        [n1] = [row for row in sent.splitlines() if row.startswith("[N1]")]
        [n2] = [row for row in sent.splitlines() if row.startswith("[N2]")]
        for part in ("Annie L.", "build caches", "towards", "Measures before claiming."):
            self.assertIn(part, n1)
        for part in ("acme", "vendor claims", "against", "Sells the caches."):
            self.assertIn(part, n2)
        self.assertNotIn("Zed", sent)
        [call] = self.calls(fake, "call", "atlas_answer")
        item = call[3][0]["input_schema"]["properties"]["claims"]["items"]["properties"]["notes"]
        self.assertEqual(item, {"type": "array", "items": {"type": "string"}})

        first, second = answer["result"]["claims"]
        self.assertEqual((first["label"], second["label"]), ("Sound", "Noise"))
        [at] = [row[5] for row in self.note_rows() if row[1] == "Annie L."]
        self.assertEqual(first["notes"], [{"who": "Annie L.", "subject": "build caches", "lean": "towards", "reason": "Measures before claiming.", "date": local_date(at)}])
        self.assertEqual([note["who"] for note in second["notes"]], ["acme"], "a repeated key shows its note once")
        problems = [problem["problem"] for problem in answer["problems"]]
        self.assertEqual(len([text for text in problems if '"N9"' in text]), 1, problems)

    def test_a_failed_label_check_still_shows_each_applied_note_with_its_claim(self) -> None:
        self.save(who="acme", subject="vendor claims", lean="against", reason="Sells the caches.")
        unlabelled = {**SOUND_2, "label": "Strong", "notes": ["N1"]}
        answer, code = self.ask(self.host(tool_reply(answered([unlabelled]), model="fake/opus")))
        self.assertEqual(code, 0, answer)
        self.assertTrue(answer["result"]["labels"].startswith("unlabelled"))
        [claim] = answer["result"]["claims"]
        self.assertNotIn("label", claim)
        self.assertEqual(claim["notes"][0]["reason"], "Sells the caches.")

    def test_an_archived_note_is_never_given_to_the_model_or_shown_and_restore_brings_it_back(self) -> None:
        self.save(who="Ann", subject="build caches", reason="Hands-on and honest.")
        key = {"note": {"who": "Ann", "subject": "build caches"}}
        applied = {**SOUND_2, "notes": ["N1"]}
        fake = self.host(*[tool_reply(answered([applied]), model="fake/opus")] * 3)
        before = self.counts()

        answer, _ = self.ask(fake)
        self.assertIn("Trust notes", self.sent(fake, 0))
        self.assertIn("Hands-on and honest.", json.dumps(answer["result"]))

        self.assertEqual(self.run_cmd("archive", requested(key, "archive my note on Ann"))[1], 0)
        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)
        self.assertNotIn("Trust notes", self.sent(fake, 1))
        self.assertNotIn("Hands-on and honest.", self.sent(fake, 1))
        self.assertNotIn("Hands-on and honest.", json.dumps(answer))
        self.assertNotIn("notes", answer["result"]["claims"][0], "even a key the model sends shows nothing")
        self.assertEqual(self.counts()["notes"], before["notes"], "archive deletes no note")

        self.assertEqual(self.run_cmd("restore", requested(key, "restore my note on Ann"))[1], 0)
        answer, _ = self.ask(fake)
        self.assertIn("Hands-on and honest.", self.sent(fake, 2))
        self.assertIn("Hands-on and honest.", json.dumps(answer["result"]))


class NoteProposalTests(NotesTest):
    def setUp(self) -> None:
        super().setUp()
        seed(self.store, SOURCES)

    def reply(self, *lines: dict[str, str]) -> Any:
        return tool_reply(answered([SOUND_2], tally_lines=list(lines)), model="fake/opus")

    def labels(self, answer: dict[str, Any]) -> list[str]:
        return [step["label"] for step in answer["next"]]

    def proposed(self) -> list[bool]:
        return [bool(row[0]) for row in self.rows("SELECT proposed_at IS NOT NULL FROM tally ORDER BY id")]

    def test_the_third_unproposed_line_proposes_a_note_and_the_fourth_does_not_but_the_count_starts_again(self) -> None:
        fake = self.host(
            self.reply(line("Cy", "build caches", 3, "towards"), line("Cy", "build caches", 4, "towards")),
            self.reply(line("cy", " Build Caches ", 3, "against")),
            self.reply(line("Cy", "build caches", 3, "towards")),
            self.reply(line("Cy", "build caches", 3, "towards"), line("Cy", "build caches", 3, "towards")),
        )
        answer, _ = self.ask(fake)
        self.assertEqual((answer["result"]["note_proposals"], self.proposed()), ([], [False, False]))
        self.assertFalse([label for label in self.labels(answer) if "note" in label])

        answer, code = self.ask(fake)
        self.assertEqual(code, 0, answer)
        [proposal] = answer["result"]["note_proposals"]
        self.assertEqual((proposal["who"], proposal["subject"], proposal["lean"]), ("Cy", "build caches", "towards"))
        self.assertRegex(proposal["reason"], r"2 towards.*1 against")
        self.assertEqual(proposal["links"], [link(3), link(4)])
        [step] = [step for step in answer["next"] if step["label"].startswith("save a note")]
        self.assertEqual(step["then"], {"stop": True})
        self.assertEqual(self.proposed(), [True, True, True], "its lines are marked proposed whether or not the user takes it")

        answer, _ = self.ask(fake)
        self.assertEqual((answer["result"]["note_proposals"], self.proposed()), ([], [True, True, True, False]))
        answer, _ = self.ask(fake)
        [again] = answer["result"]["note_proposals"]
        self.assertEqual((again["lean"], self.proposed()), ("towards", [True] * 6))
        self.assertTrue(any(label.startswith("save a note") for label in self.labels(answer)))

    def test_a_tie_proposes_no_lean_and_only_an_unarchived_note_makes_it_a_change(self) -> None:
        self.save(who="Cy", subject="build caches")
        tie = [line("Cy", "build caches", 3, "towards"), line("Cy", "build caches", 3, "against")] * 2
        fake = self.host(self.reply(*tie), self.reply(*[line("Cy", "build caches", 3, "towards")] * 3))
        answer, _ = self.ask(fake)
        [proposal] = answer["result"]["note_proposals"]
        self.assertIsNone(proposal["lean"])
        self.assertIn("tie", proposal["reason"])
        self.assertRegex(proposal["reason"], r"2 towards.*2 against")
        self.assertIn("change the note on Cy for build caches", " ".join(self.labels(answer)))

        key = {"note": {"who": "Cy", "subject": "build caches"}}
        self.assertEqual(self.run_cmd("archive", requested(key, "archive the Cy note"))[1], 0)
        answer, _ = self.ask(fake)
        self.assertEqual(answer["result"]["note_proposals"][0]["lean"], "towards")
        labels = self.labels(answer)
        self.assertTrue(any(label.startswith("save a note: lean towards Cy") for label in labels), labels)
        self.assertFalse(any(label.startswith("change the note") for label in labels), labels)

    def test_two_pairs_reaching_their_third_line_in_one_answer_give_one_next_item(self) -> None:
        lines = [line("Cy", "build caches", 3, "towards")] * 3 + [line("Dee", "build caches", 4, "against")] * 3
        answer, code = self.ask(self.host(self.reply(*lines)))
        self.assertEqual(code, 0, answer)
        self.assertEqual([(item["who"], item["lean"]) for item in answer["result"]["note_proposals"]], [("Cy", "towards"), ("Dee", "against")])
        labels = self.labels(answer)
        self.assertEqual(len(labels), 3, labels)
        [many] = [label for label in labels if "note proposals" in label]
        self.assertIn("2 note proposals", many)
        self.assertIn("note_proposals", many)


class ArchiveTopicTests(NotesTest):
    NAME = "Build caches"

    def setUp(self) -> None:
        super().setUp()
        saved = VersionRecord("Agreed.", "fake/opus", None, "complete", ("fake/reviewer",), "reconcile-1", "none", None, "2026-11-01T10:00:00+00:00")
        with closing(sqlite.open_store(self.store)) as store:
            topic_id = store.add_topic(self.NAME, "Do build caches help?")
            store.add_version(topic_id, saved, [])

    def topic_rows(self) -> list[tuple]:
        return self.rows("SELECT name, archived_at IS NOT NULL, followed, (SELECT count(*) FROM versions) FROM topics")

    def test_archiving_a_topic_asks_first_keeps_its_versions_and_restore_brings_it_back(self) -> None:
        answer, code = self.run_cmd("archive", {"topic": "build CACHES"})
        self.assertEqual((code, [d["kind"] for d in answer["decisions"]]), (4, ["confirm"]), answer)
        self.assertEqual((self.topic_rows(), self.approvals()), ([(self.NAME, 0, 1, 1)], []), "a stop changes nothing")

        # Words that name the topic, in any case, are its confirm under the default setting.
        answer, code = self.run_cmd("archive", requested({"topic": "build caches"}, "Archive my build CACHES topic"))
        self.assertEqual((code, answer["result"]), (0, {"topic": self.NAME, "result": "archived"}), answer)
        self.assertEqual(self.topic_rows(), [(self.NAME, 1, 1, 1)], "archived, still followed and with its version")
        listed, _ = app.run("topic list", None, {}, FakeHost().host())
        self.assertIsNotNone(listed["result"]["topics"][0]["archived"])
        answer, code = self.run_cmd("archive", {"topic": self.NAME})
        self.assertEqual((code, answer["decisions"]), (0, []), "already archived asks nothing")
        self.assertTrue(answer["result"]["result"].startswith("already archived "), answer)

        answer, code = self.run_cmd("restore", requested({"topic": self.NAME}, f"Restore {self.NAME}"))
        self.assertEqual((code, answer["result"]["result"]), (0, "restored"), answer)
        self.assertEqual(self.topic_rows(), [(self.NAME, 0, 1, 1)])
        answer, code = self.run_cmd("restore", {"topic": self.NAME})
        self.assertEqual((code, answer["result"]["result"], answer["decisions"]), (0, "not archived", []), answer)
        self.assertEqual([row[:3] for row in self.approvals()], [("archive", "archive", "request"), ("restore", "restore", "request")])

    def test_a_topic_not_stored_is_reported_and_a_bad_name_is_bad_input(self) -> None:
        answer, code = self.run_cmd("archive", {"topic": "Nope"})
        self.assertEqual((code, answer["result"]["result"], answer["problems"][0]["problem"]), (0, "not stored", "not stored; create it first"), answer)
        self.assertEqual(self.run_cmd("restore", {"topic": " "})[1], 2)
        self.assertEqual((self.topic_rows(), self.approvals()), ([(self.NAME, 0, 1, 1)], []))



if __name__ == "__main__":
    unittest.main()
