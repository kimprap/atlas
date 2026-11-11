"""``add --redo`` through ``app.run`` with the fake host and a temporary ``HOME`` and ``XDG_STATE_HOME`` (AC-5.1)."""

from __future__ import annotations

import hashlib
import json
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import Any

from tests.fakes.fake_host import ALL_ROLES, FakeHost, support, text_reply, tool_reply
from tests.test_add import CHART, IMAGE, IMAGE_PAGE, IMAGE_RECORD, PIXEL, SECOND, SECOND_PAGE, SECOND_RECORD, VIDEO, VIDEO_PAGE, VIDEO_RECORD, VIDEO_TRANSCRIPT, WINDOW
from tests.test_summarize import C1, C2, C3, LINK, PAGE, TEXT, PipelineTest, record

from atlas import ports  # noqa: E402
from atlas.core import app, summarize  # noqa: E402
from atlas.store import VersionClaim, VersionRecord, sqlite  # noqa: E402

# The summary role moves to another model, so every stored (sonnet, not escalated) record is older.
NEW_ROLES = {**ALL_ROLES, "atlas_summarize": "fake/haiku:high"}
HAIKU = "fake/haiku"
# One price token costs one dollar, so the confirm's estimate is the pages' token count in dollars.
PRICES = '[prices."fake/haiku"]\ninput = 1000000.0\noutput = 0.0\ncache_read = 0.0\ncache_write = 0.0\n'
FULL = ports.Window("fake", "fake:5h", 18000, 0.95, "2099-01-01T14:30:00+00:00")

NEW_TEXT = "# Faster builds\nThe revised cache cuts build time by 55% on large repos.\nUse the cache only when your builds are deterministic."
NEW_PAGE = replace(PAGE, text=NEW_TEXT)
NEW_CLAIM = {"section": "claim", "text": "The revised cache cuts build time by 55%.", "basis": "measured", "quotes": ["The revised cache cuts build time by 55% on large repos."]}
NEW_RECORD = {"abstract": "A revised note on the build cache.", "claims": [NEW_CLAIM]}
PINNED = f"https://github.com/o/r/blob/{'a' * 40}/NOTES.md"
PINNED_TEXT = "Pinned notes. Caching helps a lot."
PINNED_PAGE = ports.Page(PINNED, "Notes", None, None, None, "article", PINNED_TEXT, counts=ports.Counts(5, 0, 0))
PINNED_RECORD = {"abstract": "Pinned notes on caching.", "claims": [{"text": "Caching helps a lot.", "basis": "asserted", "quotes": ["Caching helps a lot."]}]}


def sonnet(payload: dict[str, Any]) -> ports.Reply:
    return tool_reply(payload)


def haiku(payload: dict[str, Any]) -> ports.Reply:
    return tool_reply(payload, model=HAIKU)


class RedoTest(PipelineTest):
    """Two sources stored on the old setup (sonnet), then redone under a host whose summary role is haiku."""

    def setUp(self) -> None:
        super().setUp()
        self.config()
        stored = FakeHost(
            pages={LINK: PAGE, SECOND: SECOND_PAGE},
            replies={"atlas_summarize": [sonnet(record(C1, C2, C3)), sonnet(SECOND_RECORD)]},
            judge_answer=lambda state, question: support(0.95),
        )
        answer, code = app.run("add", None, {"items": [{"link": LINK}, {"link": SECOND}]}, stored.host())
        self.assertEqual(code, 0, answer)
        self.before = self.rows("SELECT id, content_hash, last_read, model FROM sources ORDER BY id")
        self.old_claims = self.rows("SELECT id, text FROM claims ORDER BY id")

    def config(self, confirm: str = "", limits: str = "") -> None:
        # The stored sources are added without a confirm; the redo's own confirm setting is the caller's.
        self.configure(f'rethink = false\n{limits}[profiles.smoke.confirm]\nadd = "never"\n{confirm}{PRICES}')

    def host(self, pages: dict[str, Any] | None = None, replies: list[ports.Reply] | None = None, **options: Any) -> FakeHost:
        return FakeHost(
            pages=pages if pages is not None else {LINK: NEW_PAGE, SECOND: SECOND_PAGE},
            roles=NEW_ROLES,
            replies={"atlas_summarize": replies or []},
            judge_answer=lambda state, question: support(0.95),
            **options,
        )

    def redo(self, fake: FakeHost, body: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
        return app.run("add", "redo", body if body is not None else {}, fake.host())

    def confirmed(self, fake: FakeHost, body: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
        """Run the redo, answer its confirm with yes, and return the second reply."""
        body = body if body is not None else {}
        first, code = self.redo(fake, body)
        self.assertEqual((code, [d["kind"] for d in first["decisions"]]), (4, ["confirm"]), first)
        [go] = [option for option in first["decisions"][0]["options"] if option["id"] == "go"]
        return self.redo(fake, {**body, "approval": {**go["then"]["resend"]["approval"], "words": "yes"}})

    def used(self, fake: FakeHost) -> list[tuple]:
        return [call for call in fake.calls if call[0] in ("read", "image", "call", "judge")]

    def current(self, source_id: int) -> list[tuple]:
        return self.rows("SELECT id, text FROM claims WHERE source_id = ? AND replaced_at IS NULL ORDER BY ord", source_id)

    def history(self, source_id: int) -> list[tuple]:
        return self.rows("SELECT event, rubric_version, model, escalated FROM summary_history WHERE source_id = ? ORDER BY id", source_id)

    def page_text(self, source_id: int) -> str:
        with closing(sqlite.open_store(self.store)) as store:
            return store.page_text(source_id).text


class RedoScopeAndConfirmTests(RedoTest):
    def test_the_one_confirm_states_count_estimate_and_window_use_before_any_read_or_call(self) -> None:
        fake = self.host(windows=[WINDOW])
        answer, code = self.redo(fake)
        self.assertEqual(code, 4, answer)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "confirm")
        tokens = len(TEXT) // 4 + len(SECOND_PAGE.text) // 4
        self.assertIn("Redo 2 summaries", decision["question"])
        self.assertIn(f"Estimated cost: about ${tokens:.2f} at list price.", decision["question"])
        self.assertIn("Window use: fake 5-hour window at 42%, resets 2099-01-01", decision["question"])
        self.assertEqual(self.used(fake), [])
        self.assertEqual(self.rows("SELECT count(*) FROM approvals WHERE change_kind = 'add_redo'"), [(0,)])
        self.assertEqual(self.rows("SELECT id, content_hash, last_read, model FROM sources ORDER BY id"), self.before)

    def test_a_request_approval_never_skips_the_confirm_and_a_never_setting_runs_without_one(self) -> None:
        body = {"links": [LINK], "approval": {"by": "request", "words": f"Redo the summary of {LINK}"}}
        answer, code = self.redo(self.host(), body)
        self.assertEqual((code, [d["kind"] for d in answer["decisions"]]), (4, ["confirm"]), "a redo is always paid at scale")

        self.config(confirm='add_redo = "never"\n')
        fake = self.host(replies=[haiku(NEW_RECORD)])
        answer, code = self.redo(fake, {"links": [LINK]})
        self.assertEqual((code, answer["decisions"], answer["result"]["redone"]), (0, [], 1))
        self.assertEqual(self.rows("SELECT command, by, words FROM approvals WHERE change_kind = 'add_redo'"), [("add --redo", "never", None)])

    def test_bad_or_unavailable_bodies_and_unstored_links(self) -> None:
        cases = {
            "a topic that is not stored": ({"topic": "caching"}, 1, "not stored; create it first"),
            "force never goes with a topic": ({"topic": "caching", "force": True}, 2, "force needs links"),
            "force needs links": ({"force": True}, 2, "force needs links"),
            "links or a topic, not both": ({"links": [LINK], "topic": "caching"}, 2, "not both"),
            "an empty link list": ({"links": []}, 2, "non-empty list"),
            "an unknown field": ({"items": []}, 2, "is not a field"),
        }
        for named, (body, expected, text) in cases.items():
            with self.subTest(named):
                fake = self.host()
                answer, code = self.redo(fake, body)
                self.assertEqual(code, expected, answer)
                self.assertIn(text, answer["problems"][0]["problem"])
                self.assertEqual(self.used(fake), [])
        other = "https://example.com/never-added"
        answer, code = self.redo(self.host(), {"links": [other]})
        self.assertEqual((code, answer["decisions"], answer["result"]["redone"]), (0, [], 0))
        self.assertEqual([(p["link"], p["problem"]) for p in answer["problems"]], [(other, "not stored; add it first")])


class RedoReplaceTests(RedoTest):
    def test_each_page_is_read_again_and_a_passing_summary_replaces_the_old_one_with_one_history_line(self) -> None:
        fake = self.host(replies=[haiku(NEW_RECORD), haiku(SECOND_RECORD)])
        answer, code = self.confirmed(fake)
        self.assertEqual(code, 0, answer)
        first, second = answer["result"]["items"]
        self.assertEqual((first["link"], first["result"], first["page"], first["claims"]), (LINK, "redone", "read again", 1))
        self.assertEqual((second["link"], second["result"]), (SECOND, "redone"))
        self.assertEqual(answer["result"]["redone"], 2)
        self.assertEqual([call[1:] for call in fake.calls if call[0] == "read"], [(LINK, None), (SECOND, None)])

        [(_, old_hash, old_read, _), _] = self.before
        [(hash1, read1, model1, abstract1, rubric1), _] = self.rows("SELECT content_hash, last_read, model, abstract, rubric_version FROM sources ORDER BY id")
        self.assertNotEqual(hash1, old_hash)
        self.assertGreaterEqual(read1, old_read)
        self.assertEqual((model1, abstract1, rubric1), (HAIKU, NEW_RECORD["abstract"], summarize.RUBRIC_VERSION))
        self.assertEqual(self.page_text(1), NEW_TEXT)
        [(claim_id, claim_text)] = self.current(1)
        self.assertEqual(claim_text, NEW_CLAIM["text"])
        self.assertNotIn(claim_id, [row[0] for row in self.old_claims])
        self.assertEqual(
            self.rows("SELECT count(*) FROM claims WHERE source_id = 1 AND replaced_at IS NOT NULL"), [(3,)], "the old summary's claims are dropped"
        )
        [(start,)] = self.rows("SELECT start FROM quotes WHERE claim_id = ?", claim_id)
        self.assertEqual(start, NEW_TEXT.index(NEW_CLAIM["quotes"][0]), "a new quote has its place in the new page text")
        # One line for the redo, carrying the replaced summary's rubric, model and escalation.
        self.assertEqual(self.history(1), [("added", summarize.RUBRIC_VERSION, "fake/sonnet", 0), ("redone", summarize.RUBRIC_VERSION, "fake/sonnet", 0)])
        self.assertEqual(self.rows("SELECT rowid FROM source_fts WHERE source_fts MATCH 'revised'"), [(1,)], "the search index holds the new summary")
        self.assertEqual(self.rows("SELECT rowid FROM source_fts WHERE source_fts MATCH 'Windows'"), [], "and no longer the old claims")
        self.assertEqual(
            self.rows("SELECT command, by, words FROM approvals WHERE change_kind = 'add_redo'"), [("add --redo", "confirm", "yes")]
        )

        # Both records are on the current setup now: a rerun has nothing to redo, asks nothing and reads nothing.
        again = self.host()
        answer, code = self.redo(again)
        self.assertEqual((code, answer["decisions"], answer["result"]), (0, [], {"redone": 0, "items": []}))
        self.assertEqual(answer["next"][0]["label"], "nothing to redo: every record is on the current rubric and summary model")
        self.assertEqual(self.used(again), [])

    def test_an_unreadable_page_and_an_unchangeable_source_use_the_stored_text_and_the_item_says_so(self) -> None:
        stored = FakeHost(
            pages={PINNED: PINNED_PAGE},
            replies={"atlas_summarize": [sonnet(PINNED_RECORD)]},
            judge_answer=lambda state, question: support(0.95),
        )
        _, code = app.run("add", None, {"items": [{"link": PINNED}]}, stored.host())
        self.assertEqual(code, 0)
        self.assertEqual(self.rows("SELECT unchangeable FROM sources WHERE key_link = ?", PINNED), [(1,)])
        pages = {LINK: ports.Unreadable("gone", "HTTP 404"), SECOND: SECOND_PAGE, PINNED: replace(PINNED_PAGE, text="Changed text.")}
        fake = self.host(pages=pages, replies=[haiku(record(C1, C2, C3)), haiku(SECOND_RECORD), haiku(PINNED_RECORD)])
        answer, code = self.confirmed(fake)
        self.assertEqual(code, 0, answer)
        by_link = {item["link"]: item for item in answer["result"]["items"]}
        self.assertEqual((by_link[LINK]["result"], by_link[LINK]["page"]), ("redone", "stored text used: page unreadable (gone)"))
        self.assertEqual((by_link[PINNED]["result"], by_link[PINNED]["page"]), ("redone", "stored text used: unchangeable source"))
        self.assertEqual(by_link[SECOND]["page"], "read again", "a readable page next to them is read as usual")
        self.assertNotIn(PINNED, [call[1] for call in fake.calls if call[0] == "read"], "an unchangeable source is not read again")
        [(_, old_hash, old_read, _), *_] = self.before
        self.assertEqual(self.rows("SELECT content_hash, last_read, model FROM sources WHERE id = 1"), [(old_hash, old_read, HAIKU)], "the stored hash and read date stay")
        self.assertEqual(self.page_text(1), TEXT)
        self.assertEqual(self.page_text(3), PINNED_TEXT)
        [call] = [call for call in self.used(fake) if call[0] == "call" and TEXT in call[2][1]["content"]]
        self.assertEqual(call[1], "atlas_summarize", "the summary was built from the stored text")

    def test_the_stored_scope_drives_the_read_a_transcript_and_an_images_source_and_an_unreadable_image_uses_the_stored_text(self) -> None:
        stored = FakeHost(
            pages={VIDEO: VIDEO_PAGE, IMAGE: IMAGE_PAGE},
            transcripts={VIDEO: VIDEO_TRANSCRIPT},
            images={IMAGE: PIXEL},
            replies={"atlas_summarize": [sonnet(VIDEO_RECORD), sonnet({"transcriptions": [CHART]}), sonnet(IMAGE_RECORD)]},
            judge_answer=lambda state, question: support(0.95),
        )
        added = {"items": [{"link": VIDEO, "scope": "transcript"}, {"link": IMAGE, "scope": "images"}]}
        _, code = app.run("add", None, added, stored.host())
        self.assertEqual(code, 0)
        fake = self.host(
            pages={VIDEO: VIDEO_PAGE, IMAGE: IMAGE_PAGE},
            replies=[haiku(VIDEO_RECORD), haiku({"transcriptions": [CHART]}), haiku(IMAGE_RECORD)],
            transcripts={VIDEO: VIDEO_TRANSCRIPT},
            images={IMAGE: PIXEL},
        )
        answer, code = self.confirmed(fake, {"links": [VIDEO, IMAGE]})
        self.assertEqual(code, 0, answer)
        self.assertEqual([(item["link"], item["result"], item["page"]) for item in answer["result"]["items"]], [(VIDEO, "redone", "read again"), (IMAGE, "redone", "read again")])
        self.assertEqual([call[1:] for call in fake.calls if call[0] == "read"], [(VIDEO, "transcript"), (IMAGE, None)])
        transcribe = [call for call in self.used(fake) if call[0] == "call" and call[3][0]["name"] == "transcribe"]
        self.assertEqual([call[6] for call in transcribe], [(PIXEL,)], "the images are fetched and transcribed again")
        [(image_hashes,)] = self.rows("SELECT image_hashes FROM page_text WHERE source_id = 4")
        self.assertEqual(image_hashes, hashlib.sha256(PIXEL).hexdigest())

        # An image that cannot be fetched now: the stored text, with its transcription, is summarized and the item says so.
        fake = self.host(replies=[haiku(IMAGE_RECORD)], pages={IMAGE: IMAGE_PAGE}, images={IMAGE: ports.Unreadable("gone", "HTTP 404")})
        answer, code = self.confirmed(fake, {"links": [IMAGE], "force": True})
        self.assertEqual(code, 0, answer)
        [item] = answer["result"]["items"]
        self.assertEqual((item["result"], item["page"]), ("redone", "stored text used: an image is unreadable (gone)"))
        self.assertEqual([call[3][0]["name"] for call in self.used(fake) if call[0] == "call"], ["record"], "nothing is transcribed again")
        self.assertIn(CHART, self.page_text(4))


class RedoFailureAndLimitTests(RedoTest):
    def test_a_failed_redo_keeps_the_old_summary_logs_it_and_never_blocks_the_next_source(self) -> None:
        failing = [text_reply("No.", model=HAIKU), text_reply("No.", model=HAIKU)]
        fake = self.host(replies=[*failing, haiku(SECOND_RECORD)])
        fake.replies["atlas_escalate"] = [text_reply("No.", model="fake/opus"), text_reply("Still no.", model="fake/opus")]
        answer, code = self.confirmed(fake)
        self.assertEqual(code, 4, answer)
        failed, redone = answer["result"]["items"]
        self.assertEqual((failed["link"], failed["result"]), (LINK, "redo failed, old summary kept"))
        self.assertEqual((redone["link"], redone["result"]), (SECOND, "redone"))
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "summary_failed")
        [retry] = [option for option in decision["options"] if option["id"] == "retry"]
        self.assertEqual(retry["then"], {"resend": {"links": [LINK]}})
        # The old summary, page text, hash and read date are untouched; the only write is one failure line.
        self.assertEqual(self.current(1), [row for row in self.old_claims if row[0] in (1, 2, 3)])
        self.assertEqual(self.rows("SELECT id, content_hash, last_read, model FROM sources WHERE id = 1"), self.before[:1])
        self.assertEqual(self.page_text(1), TEXT)
        self.assertEqual(self.history(1), [("added", summarize.RUBRIC_VERSION, "fake/sonnet", 0), ("redo_failed", summarize.RUBRIC_VERSION, "fake/sonnet", 0)])
        self.assertEqual(self.history(2)[-1][0], "redone")
        log = json.loads(Path(failed["replies_log"]).read_text(encoding="utf-8"))
        self.assertEqual((log["command"], log["key_link"]), ("add --redo", LINK))
        self.assertEqual(self.rows("SELECT count(*) FROM approvals WHERE change_kind = 'add_redo'"), [(1,)])

    def test_a_page_that_now_needs_a_scope_choice_keeps_its_old_summary(self) -> None:
        self.config(limits="max_page_tokens = 100\n")
        grown = replace(PAGE, text=TEXT + "\n" + "Long addition. " * 40)
        fake = self.host(pages={LINK: grown, SECOND: SECOND_PAGE}, replies=[haiku(SECOND_RECORD)])
        answer, code = self.confirmed(fake)
        self.assertEqual((code, answer["decisions"]), (0, []), answer)
        kept, redone = answer["result"]["items"]
        self.assertEqual((kept["link"], kept["result"]), (LINK, "kept: needs scope"))
        self.assertEqual((redone["link"], redone["result"]), (SECOND, "redone"))
        [problem] = answer["problems"]
        self.assertEqual((problem["link"], problem["field"]), (LINK, "scope"))
        self.assertIn("over the 100-token limit", problem["problem"])
        self.assertEqual([call[1] for call in self.used(fake) if call[0] == "call"], ["atlas_summarize"], "only the readable-scope source made a summary call")
        self.assertEqual(self.rows("SELECT id, content_hash, last_read, model FROM sources WHERE id = 1"), self.before[:1])
        self.assertEqual(self.history(1), [("added", summarize.RUBRIC_VERSION, "fake/sonnet", 0)])
        self.assertEqual(self.current(1), [row for row in self.old_claims if row[0] in (1, 2, 3)])

    def test_the_window_guard_stops_the_batch_before_the_next_item(self) -> None:
        fake = self.host(windows=[WINDOW], replies=[haiku(NEW_RECORD), haiku(SECOND_RECORD)])

        def judged(state: str, question: ports.Question) -> ports.Answer:
            fake.window_rows = [FULL]  # the window fills while the first source is being redone
            return support(0.95)

        fake.judge_answer = judged
        answer, code = self.confirmed(fake)
        self.assertEqual(code, 4, answer)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "window")
        self.assertIn("1 of 2 done, 1 not started", decision["question"])
        self.assertEqual([(item["link"], item["result"]) for item in answer["result"]["items"]], [(LINK, "redone")])
        self.assertEqual(self.rows("SELECT model FROM sources ORDER BY id"), [(HAIKU,), ("fake/sonnet",)], "the second source is not started")


class RedoNamedLinkTests(RedoTest):
    def make_second_current(self) -> None:
        fake = self.host(replies=[haiku(SECOND_RECORD)])
        answer, code = self.confirmed(fake, {"links": [SECOND]})
        self.assertEqual((code, answer["result"]["redone"]), (0, 1), answer)

    def test_named_links_on_the_current_setup_are_skipped_and_said_so(self) -> None:
        self.make_second_current()
        fake = self.host(replies=[haiku(NEW_RECORD)])
        answer, code = self.confirmed(fake, {"links": [LINK, SECOND]})
        self.assertEqual(code, 0, answer)
        by_link = {item["link"]: item for item in answer["result"]["items"]}
        self.assertEqual((by_link[LINK]["result"], answer["result"]["redone"]), ("redone", 1))
        self.assertEqual(by_link[SECOND], {"link": SECOND, "result": "skipped: already on the current rubric and summary model"})
        self.assertEqual([call[1] for call in fake.calls if call[0] == "read"], [LINK], "the current source is not read")
        self.assertEqual([row[0] for row in self.history(2)], ["added", "redone"], "and gets no history line")

    def test_links_that_are_all_current_offer_redo_anyway_and_force_redoes_them(self) -> None:
        self.make_second_current()
        fake = self.host(replies=[haiku(SECOND_RECORD)])
        answer, code = self.redo(fake, {"links": [SECOND]})
        self.assertEqual(code, 4, answer)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "already_current")
        self.assertIn(f"{SECOND} is already on the current rubric and summary model", decision["question"])
        [anyway] = [option for option in decision["options"] if option["id"] == "redo_anyway"]
        self.assertEqual(anyway["then"], {"resend": {"force": True}})
        self.assertEqual(self.used(fake), [], "no read, call or confirm yet")

        answer, code = self.confirmed(fake, {"links": [SECOND], "force": True})
        self.assertEqual(code, 0, answer)
        self.assertEqual([(item["link"], item["result"]) for item in answer["result"]["items"]], [(SECOND, "redone")])
        self.assertEqual([row[0] for row in self.history(2)], ["added", "redone", "redone"])
        self.assertEqual(self.history(2)[-1][2], HAIKU, "the forced redo replaces a current summary and records its model")


class RedoTopicTests(RedoTest):
    """``topic``: the older sources the topic's saved versions cite, and no others."""

    def setUp(self) -> None:
        super().setUp()
        saved = VersionRecord("Agreed.", "fake/opus", None, "complete", ("fake/reviewer",), "reconcile-1", "none", None, "2026-11-01T10:00:00+00:00")
        with closing(sqlite.open_store(self.store)) as store:
            topic_id = store.add_topic("caching", "Do build caches help?")
            store.add_version(topic_id, saved, [VersionClaim(self.old_claims[0][0], "Copied claim.", ("Copied quote.",))])

    def test_a_topic_redoes_the_older_sources_its_versions_cite_and_a_current_one_is_left_out(self) -> None:
        fake = self.host(replies=[haiku(NEW_RECORD)])
        answer, code = self.confirmed(fake, {"topic": "  Caching "})
        self.assertEqual(code, 0, answer)
        self.assertEqual([(item["link"], item["result"]) for item in answer["result"]["items"]], [(LINK, "redone")])
        self.assertEqual([call[1] for call in fake.calls if call[0] == "read"], [LINK], "the second source is older too, but the topic does not cite it")
        self.assertEqual(([row[0] for row in self.history(1)], [row[0] for row in self.history(2)]), (["added", "redone"], ["added"]))
        self.assertEqual(self.rows("SELECT model FROM sources ORDER BY id"), [(HAIKU,), ("fake/sonnet",)])

        # Every source it cites is now on the current setup: nothing to redo, no decision, no read or call.
        fake = self.host()
        answer, code = self.redo(fake, {"topic": "caching"})
        self.assertEqual((code, answer["decisions"], answer["result"]["redone"]), (0, [], 0), answer)
        self.assertEqual(self.used(fake), [])


if __name__ == "__main__":
    unittest.main()
