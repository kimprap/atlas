"""``add --reread`` through ``app.run`` with the fake host and a temporary ``HOME`` (AC-3.6)."""

from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any

from tests.fakes.fake_host import FakeHost, support, tool_reply
from tests.test_summarize import C1, C2, C3, LINK, PAGE, PipelineTest, claim_of, record

from atlas import ports  # noqa: E402

# 300 distinct words after the claims' lines, so one short added line stays under 5% new text.
FILLER = " ".join(f"word{n}" for n in range(300))
BASE = ports.Page(LINK, PAGE.title, PAGE.author, None, None, "article", f"{PAGE.text}\n{FILLER}")
REREAD = {"items": [{"link": LINK}], "approval": {"by": "request", "words": f"re-read {LINK}"}}
WINDOWS_LINE = "The cache does not work on Windows yet."
NEW_C3 = {"section": "caveat", "text": "The cache now works on Windows.", "basis": "asserted", "quotes": ["now works on Windows too"]}
NEW_CLAIM = {"section": "claim", "text": "The cache also speeds up tests by 20%.", "basis": "measured", "quotes": ["also speeds up tests by 20%"]}


def page(text: str) -> ports.Page:
    return replace(BASE, text=text)


class RereadTests(PipelineTest):
    def setUp(self) -> None:
        super().setUp()
        self.configure("rethink = false\n")
        stored = FakeHost(
            pages={LINK: BASE},
            replies={"atlas_summarize": [tool_reply(record(C1, C2, C3))]},
            judge_answer=lambda state, question: support(0.95),
        )
        _, code = self.add(stored)
        self.assertEqual(code, 0)
        self.before = self.rows("SELECT id, text FROM claims ORDER BY ord")
        [(self.hash, self.read_at)] = self.rows("SELECT content_hash, last_read FROM sources")

    def reread(self, text: str, replies: list[ports.Reply] | None = None) -> tuple[FakeHost, dict[str, Any], int]:
        fake = FakeHost(
            pages={LINK: page(text)},
            replies={"atlas_summarize": replies or []},
            judge_answer=lambda state, question: support(0.95),
        )
        answer, code = self.add(fake, REREAD, mode="reread")
        return fake, answer, code

    def current(self) -> list[tuple]:
        return self.rows("SELECT id, text FROM claims WHERE replaced_at IS NULL ORDER BY ord")

    def test_no_quote_gone_and_under_5_percent_new_text_changes_no_claim(self) -> None:
        text = f"{BASE.text}\nOne short line added."
        fake, answer, code = self.reread(text)
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["items"], [{"link": LINK, "result": "re-read, no meaningful change"}])
        self.assertEqual(self.calls(fake, "call"), [])
        self.assertEqual(self.current(), self.before)
        [(content_hash, read_at)] = self.rows("SELECT content_hash, last_read FROM sources")
        self.assertNotEqual(content_hash, self.hash)
        self.assertGreaterEqual(read_at, self.read_at)
        self.assertEqual(self.rows("SELECT count(*) FROM summary_history"), [(1,)])
        self.assertEqual(self.rows("SELECT by FROM approvals WHERE change_kind = 'add_reread'"), [("request",)])

    def test_a_gone_quote_revises_only_its_claim_and_the_others_keep_their_ids_and_move(self) -> None:
        text = "Updated in November.\n" + BASE.text.replace(WINDOWS_LINE, "The cache now works on Windows too.")
        id3 = self.before[2][0]
        update = {"affected": [{"ref": f"c{id3}", "action": "revise", **NEW_C3}], "added": []}
        fake, answer, code = self.reread(text, [tool_reply(update)])
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["items"], [{"link": LINK, "result": "updated (1 claims changed)"}])
        [call] = self.calls(fake, "call", "atlas_summarize")
        message = call[2][1]["content"]
        self.assertIn(f"- c{id3}: [caveat, asserted] {C3['text']}", message)
        self.assertIn(f"- [claim, measured] {C1['text']}", message)
        self.assertEqual([claim_of(judged[1]) for judged in self.calls(fake, "judge")], [NEW_C3["text"]])
        current = self.current()
        self.assertEqual(current[:2], self.before[:2], "unaffected claims keep their ids")
        self.assertEqual(current[2][1], NEW_C3["text"])
        self.assertEqual(self.rows("SELECT replaced_at IS NOT NULL FROM claims WHERE id = ?", id3), [(1,)])
        [(start,)] = self.rows("SELECT start FROM quotes WHERE claim_id = ?", self.before[1][0])
        self.assertEqual(start, text.index(C2["quotes"][0]), "a kept claim's quote has its place in the new text")
        self.assertEqual(self.rows("SELECT event FROM summary_history ORDER BY id"), [("added",), ("reread",)])

    def test_new_text_over_5_percent_adds_claims_from_the_changed_part_only(self) -> None:
        extra = "The cache also speeds up tests by 20%. " + " ".join(f"more{n}" for n in range(40))
        text = f"{BASE.text}\n{extra}"
        fake, answer, code = self.reread(text, [tool_reply({"affected": [], "added": [NEW_CLAIM]})])
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["items"], [{"link": LINK, "result": "updated (1 claims changed)"}])
        [call] = self.calls(fake, "call", "atlas_summarize")
        self.assertIn(f"Changed parts of the new page, to add new claims from (in added):\n<<<\n{extra}\n>>>", call[2][1]["content"])
        self.assertEqual(self.current(), [*self.before, (self.current()[3][0], NEW_CLAIM["text"])])

    def test_a_source_added_from_its_transcript_is_read_again_from_its_transcript(self) -> None:
        video = "https://www.youtube.com/watch?v=abc123"
        spoken = "Ann: Caches cut our build time in half."
        whole = ports.Page(video, "Talk", None, None, None, "video", f"# Talk\n\n## Description\nSlides and links.\n\n## Transcript\n{spoken}")
        transcript = ports.Page(video, "Talk", None, None, None, "video", f"# Talk\n\n{spoken}")
        claim = {"text": "Ann says caches halved build time.", "basis": "asserted", "quotes": [spoken.removeprefix("Ann: ")]}
        adding = FakeHost(
            pages={video: whole},
            transcripts={video: transcript},
            replies={"atlas_summarize": [tool_reply({"abstract": "A talk on caches.", "claims": [claim]})]},
            judge_answer=lambda state, question: support(0.95),
        )
        _, code = self.add(adding, {"items": [{"link": video, "scope": "transcript"}], "approval": {"by": "request", "words": f"add {video}"}})
        self.assertEqual(code, 0)
        fake = FakeHost(pages={video: whole}, transcripts={video: transcript})
        answer, code = self.add(fake, {"items": [{"link": video}], "approval": {"by": "request", "words": f"re-read {video}"}}, mode="reread")
        self.assertEqual(answer["result"]["items"], [{"link": video, "result": "re-read, no meaningful change"}])
        self.assertEqual([call[1:] for call in fake.calls if call[0] == "read"], [(video, "transcript")])

    def test_a_source_added_from_one_section_ignores_changes_in_the_others(self) -> None:
        link = "https://example.com/sections"
        intro = "# Intro\nCaches save time on every build."
        before = ports.Page(link, "Sections", None, None, None, "article", f"{intro}\n# Results\nOld results.")
        after = replace(before, text=f"{intro}\n# Results\n" + " ".join(f"new{n}" for n in range(50)))
        claim = {"text": "Caches save build time.", "basis": "asserted", "quotes": ["Caches save time on every build."]}
        adding = FakeHost(
            pages={link: before},
            replies={"atlas_summarize": [tool_reply({"abstract": "Notes on caches.", "claims": [claim]})]},
            judge_answer=lambda state, question: support(0.95),
        )
        body = {"items": [{"link": link, "scope": {"sections": ["Intro"]}}], "approval": {"by": "request", "words": f"add {link}"}}
        self.assertEqual(self.add(adding, body)[1], 0)
        reread = {"items": [{"link": link}], "approval": {"by": "request", "words": f"re-read {link}"}}
        answer, code = self.add(FakeHost(pages={link: after}), reread, mode="reread")
        self.assertEqual(answer["result"]["items"], [{"link": link, "result": "re-read, no meaningful change"}])

    def test_an_unreadable_page_keeps_the_stored_source(self) -> None:
        fake = FakeHost(pages={LINK: ports.Unreadable("gone", "HTTP 404")})
        answer, code = self.add(fake, REREAD, mode="reread")
        self.assertEqual((code, answer["result"]["items"]), (0, [{"link": LINK, "result": "unreadable, kept"}]))
        self.assertEqual(self.rows("SELECT content_hash, last_read FROM sources"), [(self.hash, self.read_at)])
        self.assertEqual(self.rows("SELECT count(*) FROM approvals WHERE change_kind = 'add_reread'"), [(0,)], "nothing was applied")

    def test_a_page_that_grew_past_the_limit_is_kept_and_no_claim_is_replaced(self) -> None:
        self.configure("rethink = false\nmax_page_tokens = 2000\n")
        grown = "Prepended long intro. " * 400 + "\n" + BASE.text
        fake = FakeHost(pages={LINK: page(grown)}, judge_answer=lambda state, question: support(0.95))
        answer, code = self.add(fake, REREAD, mode="reread")
        self.assertEqual((code, answer["result"]["items"]), (0, [{"link": LINK, "result": "unreadable, kept"}]))
        [problem] = answer["problems"]
        self.assertIn("over the 2,000-token limit", problem["problem"])
        self.assertEqual(self.calls(fake, "call"), [])
        self.assertEqual(self.current(), self.before)
        self.assertEqual(self.rows("SELECT count(*) FROM claims WHERE replaced_at IS NOT NULL"), [(0,)])

    def test_a_link_no_source_holds_is_a_problem(self) -> None:
        other = "https://example.com/never-added"
        answer, code = self.add(FakeHost(), {"items": [{"link": other}]}, mode="reread")
        self.assertEqual(code, 0)
        self.assertEqual([(p["link"], p["problem"]) for p in answer["problems"]], [(other, "not stored; add it first")])


if __name__ == "__main__":
    unittest.main()
