"""``add`` through ``app.run`` with the fake host and a temporary ``HOME``: approvals, agent text,
pick-scope decisions, images, the re-read offer and missing roles."""

from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace
from datetime import timedelta
from typing import Any
from unittest import mock

from tests.fakes.fake_host import ALL_ROLES, FakeHost, support, tool_reply
from tests.test_summarize import C1, C2, C3, LINK, PAGE, WORDS, PipelineTest, record

from atlas import ports  # noqa: E402
from atlas.core import app, spend  # noqa: E402

SECOND = "https://example.com/second"
SECOND_PAGE = ports.Page(SECOND, "Second", None, None, None, "article", "Second page. Caching helps a lot.")
SECOND_RECORD = {"abstract": "A second page.", "claims": [{"text": "Caching helps a lot.", "basis": "asserted", "quotes": ["Caching helps a lot."]}]}
PRICES = '[prices."fake/sonnet"]\ninput = 2.0\noutput = 10.0\ncache_read = 0.2\ncache_write = 2.5\n'
WINDOW = ports.Window("fake", "fake:5h", 18000, 0.42, "2099-01-01T14:30:00+00:00")
VIDEO = "https://www.youtube.com/watch?v=abc123"
DESCRIPTION = "Slides and links for the build talk."
VIDEO_PAGE = ports.Page(VIDEO, "Build talk", None, None, None, "video", f"# Build talk\n\n## Description\n{DESCRIPTION}\n\n## Transcript\nAnn: Caches cut our build time in half.")
VIDEO_TRANSCRIPT = ports.Page(VIDEO, "Build talk", None, None, None, "video", "# Build talk\n\nAnn: Caches cut our build time in half.")
VIDEO_RECORD = {"abstract": "A talk on build caches.", "claims": [{"text": "Ann says caches halved build time.", "basis": "asserted", "quotes": ["Caches cut our build time in half."]}]}
IMAGE = "https://example.com/chart.png"
PIXEL = b"\x89PNG\r\n\x1a\nchart bytes"
IMAGE_PAGE = ports.Page(IMAGE, None, None, None, None, "image", "Fetched image content (image/png).", images=(IMAGE,))
CHART = "Build time: 10 min before, 6 min after the cache."
IMAGE_RECORD = {"abstract": "A chart of build times.", "claims": [{"text": "Build time fell from 10 to 6 minutes.", "basis": "measured", "quotes": [CHART]}]}
REPO = "https://github.com/fake/tools"
ITEMS = (ports.RepoItem("one", f"{REPO}/tree/HEAD/one", "skill"), ports.RepoItem("two", f"{REPO}/tree/HEAD/two", "skill"))
REPO_PAGE = ports.Page(REPO, "fake/tools", "fake", "GitHub", None, "repo", "# fake/tools\nTwo skills.", items=ITEMS)


def item_page(link: str, name: str) -> ports.Page:
    return ports.Page(link, name, None, None, None, "docs", f"# {name}\nThe {name} skill formats files.")


def item_record(name: str) -> dict[str, Any]:
    return {"abstract": f"The {name} skill.", "claims": [{"text": f"{name} formats files.", "basis": "asserted", "quotes": [f"The {name} skill formats files."]}]}


def request(*links: str) -> dict[str, Any]:
    return {"by": "request", "words": "Summarize " + " and ".join(links)}


def follow(body: dict[str, Any], option: dict[str, Any], words: str) -> dict[str, Any]:
    """The next body for a decision option, built as SKILL.md's "Follow a choice" says."""
    resend = option["then"]["resend"]
    following = {**body, **{field: value for field, value in resend.items() if field != "mode"}}
    if "approval" in resend:
        following["approval"] = {**resend["approval"], "words": words}
    elif body.get("approval", {}).get("by") == "confirm":
        del following["approval"]
    return following


class AddTests(PipelineTest):
    def setUp(self) -> None:
        super().setUp()
        self.configure("rethink = false\n")

    def fake(self, **extra: Any) -> FakeHost:
        pages = {LINK: PAGE, SECOND: SECOND_PAGE, VIDEO: VIDEO_PAGE, IMAGE: IMAGE_PAGE, REPO: REPO_PAGE}
        pages.update({item.link: item_page(item.link, item.path) for item in ITEMS})
        settings = {
            "pages": pages,
            "transcripts": {VIDEO: VIDEO_TRANSCRIPT},
            "replies": {"atlas_summarize": [tool_reply(record(C1, C2, C3))]},
            "judge_answer": lambda state, question: ports.Answer(p=0.1) if question.id == "same_work" else support(0.95),
        }
        settings.update(extra)
        return FakeHost(**settings)

    def reads(self, fake: FakeHost) -> list[str]:
        return [call[1] for call in fake.calls if call[0] == "read"]

    def test_the_users_own_words_run_one_link_with_no_confirm_and_record_calls(self) -> None:
        fake = self.fake()
        answer, code = self.add(fake)
        self.assertEqual((code, answer["decisions"], answer["result"]["added"]), (0, [], 1))
        self.assertEqual(self.rows("SELECT command, change_kind, by, words FROM approvals"), [("add", "add", "request", WORDS)])
        status, code = app.run("status", "detail", {}, FakeHost().host())
        detail = status["result"]["detail"]
        self.assertEqual((detail["counts"]["sources"], detail["spend"]["calls"]), (1, 4))

    def test_without_the_users_words_a_confirm_comes_before_any_read(self) -> None:
        fake = self.fake()
        body: dict[str, Any] = {"items": [{"link": LINK}]}
        answer, code = self.add(fake, body)
        self.assertEqual(code, 4)
        [decision] = answer["decisions"]
        self.assertEqual((decision["kind"], decision["question"]), ("confirm", f"Read and summarize {LINK}?"))
        self.assertEqual(self.reads(fake), [])
        [go] = [option for option in decision["options"] if option["id"] == "go"]
        answer, code = self.add(fake, {**body, "approval": {**go["then"]["resend"]["approval"], "words": "yes"}})
        self.assertEqual((code, answer["result"]["added"]), (0, 1))
        self.assertEqual(self.rows("SELECT by, words FROM approvals"), [("confirm", "yes")])

    def test_two_links_need_a_confirm_that_states_the_estimate_and_window_use(self) -> None:
        self.configure(f"rethink = false\n{PRICES}")
        fake = self.fake(windows=[WINDOW])
        answer, code = self.add(fake, {"items": [{"link": LINK}, {"link": SECOND}], "approval": request(LINK, SECOND)})
        self.assertEqual(code, 4)
        [decision] = answer["decisions"]
        # 30K in and 8K out per link before any call is recorded: (30000 * 2 + 8000 * 10) / 1e6 = $0.14.
        self.assertIn("Estimated cost: about $0.28 at list price (about $0.14 at list price per link)", decision["question"])
        self.assertIn("Window use: fake 5-hour window at 42%, resets 2099-01-01", decision["question"])
        self.assertEqual(self.reads(fake), [])

    def test_agent_text_is_stored_unread_and_a_host_without_a_reader_reports_no_reader(self) -> None:
        self.configure("rethink = false\n[profiles.smoke.confirm]\nadd = \"never\"\n")
        fake = self.fake(pages={SECOND: ports.Unreadable("no_reader", "no reader on this host")})
        answer, code = self.add(fake, {"items": [{"link": LINK, "text": TEXT_GIVEN}, {"link": SECOND}]})
        self.assertEqual(code, 0, answer)
        self.assertEqual(
            [(item["link"], item["result"]) for item in answer["result"]["items"]],
            [(LINK, "added"), (SECOND, "unreadable: no_reader")],
        )
        self.assertEqual(self.reads(fake), [SECOND])
        self.assertEqual(self.rows("SELECT key_link, text_origin FROM sources"), [(LINK, "agent")])

    def test_a_video_asks_for_its_scope_and_the_choice_is_kept(self) -> None:
        fake = self.fake(replies={"atlas_summarize": [tool_reply(VIDEO_RECORD)]})
        body = {"items": [{"link": VIDEO}], "approval": request(VIDEO)}
        answer, code = self.add(fake, body)
        self.assertEqual(code, 4)
        [decision] = answer["decisions"]
        self.assertEqual(decision["kind"], "pick_scope")
        self.assertEqual(
            [(option["id"], option["then"]) for option in decision["options"]],
            [("transcript", {"resend": {"items": [{"link": VIDEO, "scope": "transcript"}]}}), ("skip", {"stop": True})],
        )
        self.assertEqual(self.rows("SELECT count(*) FROM sources"), [(0,)])
        self.assertEqual(self.rows("SELECT count(*) FROM approvals"), [(0,)], "a pick_scope reply applies nothing")
        answer, code = self.add(fake, {**body, **decision["options"][0]["then"]["resend"]})
        self.assertEqual(self.rows("SELECT by FROM approvals"), [("request",)], "the stored resend applies once")
        self.assertEqual((code, answer["result"]["added"]), (0, 1), answer)
        self.assertEqual([call[1:] for call in fake.calls if call[0] == "read"], [(VIDEO, None), (VIDEO, "transcript")])
        [call] = self.calls(fake, "call", "atlas_summarize")
        self.assertTrue(call[2][0]["content"].endswith("\nName who is speaking."))
        self.assertIn("Ann: Caches cut our build time in half.", call[2][1]["content"])
        self.assertNotIn(DESCRIPTION, call[2][1]["content"])
        self.assertEqual(self.rows("SELECT scope_choice, read_share FROM sources"), [("transcript", None)])

    def test_a_long_transcript_keeps_its_transcript_read_and_reads_its_first_part(self) -> None:
        self.configure("rethink = false\nmax_page_tokens = 15\n")
        spoken = "Ann: Caches cut our build time in half."
        long_talk = replace(VIDEO_TRANSCRIPT, text=f"# Build talk\n{spoken}\n" + "\n".join(f"More talk {n}." for n in range(30)))
        fake = self.fake(transcripts={VIDEO: long_talk}, replies={"atlas_summarize": [tool_reply(VIDEO_RECORD)]})
        answer, code = self.add(fake, {"items": [{"link": VIDEO, "scope": "transcript"}], "approval": request(VIDEO)})
        self.assertEqual((code, answer["decisions"]), (0, []), answer)
        self.assertEqual([call[1:] for call in fake.calls if call[0] == "read"], [(VIDEO, "transcript")])
        [(choice, share)] = self.rows("SELECT scope_choice, read_share FROM sources")
        self.assertEqual(choice, "transcript")
        self.assertLess(share, 0.5)
        self.assertEqual(answer["result"]["items"][0]["read_share"], share)

    def test_following_a_pick_scope_after_a_confirmed_batch_never_resends_the_old_confirm(self) -> None:
        fake = self.fake()
        body: dict[str, Any] = {"items": [{"link": LINK}, {"link": REPO}], "approval": request(LINK, REPO)}
        answer, code = self.add(fake, body)
        [confirm] = answer["decisions"]
        [go] = [option for option in confirm["options"] if option["id"] == "go"]
        body = follow(body, go, "yes")
        answer, code = self.add(fake, body)
        [scope] = answer["decisions"]
        self.assertEqual((code, scope["kind"], answer["result"]["added"]), (4, "pick_scope", 1))
        [page] = [option for option in scope["options"] if option["id"] == "page"]
        answer, code = self.add(fake, follow(body, page, "the repo page"))
        self.assertNotEqual(code, 2, answer)
        [again] = answer["decisions"]
        self.assertEqual((code, again["kind"]), (4, "confirm"), "the narrowed change is asked about once")

    def test_a_video_stored_separately_is_read_from_its_transcript_with_no_question(self) -> None:
        fake = self.fake(replies={"atlas_summarize": [tool_reply(VIDEO_RECORD)]})
        answer, code = self.add(fake, {"items": [{"link": VIDEO, "scope": "separate"}], "approval": request(VIDEO)})
        self.assertEqual((code, answer["decisions"], answer["result"]["added"]), (0, [], 1), answer)
        self.assertEqual([call[1:] for call in fake.calls if call[0] == "read"], [(VIDEO, None), (VIDEO, "transcript")])
        [call] = self.calls(fake, "call", "atlas_summarize")
        self.assertNotIn(DESCRIPTION, call[2][1]["content"])
        self.assertEqual(self.rows("SELECT scope_choice FROM sources"), [("transcript",)])

    def test_a_video_without_a_transcript_is_unreadable_no_transcript(self) -> None:
        fake = self.fake(transcripts={})
        body = {"items": [{"link": VIDEO, "scope": "transcript"}], "approval": request(VIDEO)}
        answer, code = self.add(fake, body)
        self.assertEqual(code, 0, answer)
        self.assertEqual(answer["result"]["items"], [{"link": VIDEO, "result": "unreadable: no_transcript"}])
        self.assertEqual(self.calls(fake, "call"), [])
        self.assertEqual(self.rows("SELECT count(*) FROM sources"), [(0,)])

    def test_a_page_over_the_length_limit_asks_and_its_first_part_is_read(self) -> None:
        self.configure("rethink = false\nmax_page_tokens = 20\n")
        long_text = "# Intro\nCaches save time on every build.\n# Results\n" + "More detail here. " * 20
        fake = self.fake(
            pages={LINK: ports.Page(LINK, "Long", None, None, None, "article", long_text)},
            replies={"atlas_summarize": [tool_reply({"abstract": "A long page.", "claims": [{"text": "Caches save build time.", "basis": "asserted", "quotes": ["Caches save time on every build."]}]})]},
        )
        body = {"items": [{"link": LINK}], "approval": request(LINK)}
        answer, code = self.add(fake, body)
        [decision] = answer["decisions"]
        self.assertEqual((code, decision["kind"]), (4, "pick_scope"))
        self.assertEqual(
            [option["then"]["resend"]["items"][0]["scope"] for option in decision["options"]],
            ["first_part", {"sections": ["Intro"]}, {"sections": ["Results"]}],
        )
        answer, code = self.add(fake, {**body, **decision["options"][0]["then"]["resend"]})
        self.assertEqual(code, 0, answer)
        [(choice, share)] = self.rows("SELECT scope_choice, read_share FROM sources")
        self.assertEqual(choice, "first_part")
        self.assertLess(share, 0.5)
        [call] = self.calls(fake, "call", "atlas_summarize")
        self.assertNotIn("More detail here. " * 5, call[2][1]["content"])

    def test_an_image_page_asks_then_its_images_are_fetched_transcribed_and_hashed(self) -> None:
        fake = self.fake(
            images={IMAGE: PIXEL},
            replies={"atlas_summarize": [tool_reply({"transcriptions": [CHART]}), tool_reply(IMAGE_RECORD)]},
        )
        body = {"items": [{"link": IMAGE}], "approval": request(IMAGE)}
        answer, code = self.add(fake, body)
        [decision] = answer["decisions"]
        self.assertEqual([option["id"] for option in decision["options"]], ["images", "skip"])
        self.assertNotIn(("image", IMAGE), fake.calls, "no image is fetched before the choice")
        answer, code = self.add(fake, {**body, **decision["options"][0]["then"]["resend"]})
        self.assertEqual(code, 0, answer)
        transcribe, summary = self.calls(fake, "call", "atlas_summarize")
        self.assertEqual((transcribe[3][0]["name"], transcribe[6]), ("transcribe", (PIXEL,)))
        self.assertIn(f"[image 1, transcribed by fake/sonnet]\n{CHART}", summary[2][1]["content"])
        [(image_hashes,)] = self.rows("SELECT image_hashes FROM page_text")
        self.assertEqual(image_hashes, hashlib.sha256(PIXEL).hexdigest())
        self.assertEqual(self.rows("SELECT q.text FROM quotes q"), [(CHART,)])

    def test_each_item_of_a_repo_is_its_own_source_after_a_confirm_that_counts_the_items(self) -> None:
        self.configure(f"rethink = false\n{PRICES}")
        replies = [tool_reply(item_record("one")), tool_reply(item_record("two"))]
        fake = self.fake(replies={"atlas_summarize": replies})
        body = {"items": [{"link": REPO}], "approval": request(REPO)}
        answer, code = self.add(fake, body)
        [decision] = answer["decisions"]
        self.assertEqual([option["id"] for option in decision["options"]], ["page", "each_item", "both"])
        body = {**body, **decision["options"][1]["then"]["resend"]}
        answer, code = self.add(fake, body)
        [confirm] = answer["decisions"]
        self.assertEqual((code, confirm["kind"]), (4, "confirm"), "each item is paid at scale, so the request is not enough")
        # Two items at 30K in and 8K out each before any call is recorded: 2 * $0.14.
        self.assertIn(f"Read and summarize 2 links (each of the 2 items of {REPO})?", confirm["question"])
        self.assertIn("Estimated cost: about $0.28 at list price", confirm["question"])
        [go] = [option for option in confirm["options"] if option["id"] == "go"]
        answer, code = self.add(fake, {**body, "approval": {**go["then"]["resend"]["approval"], "words": "yes"}})
        self.assertEqual(code, 0, answer)
        self.assertEqual(
            self.rows("SELECT s.key_link, r.link FROM sources s JOIN related_links r ON r.source_id = s.id ORDER BY s.id"),
            [(ITEMS[0].link, REPO), (ITEMS[1].link, REPO)],
        )

    def test_a_stored_source_read_long_ago_brings_one_re_read_offer(self) -> None:
        old = spend.local_now() - timedelta(days=40)
        with mock.patch.object(spend, "local_now", return_value=old):
            self.add(self.fake())
        fake = self.fake()
        answer, code = self.add(fake)
        self.assertEqual(code, 0)
        self.assertEqual(answer["result"]["items"], [{"link": LINK, "result": f"already stored, last read {old.date().isoformat()}"}])
        self.assertEqual(self.reads(fake), [])
        self.assertEqual(
            answer["next"],
            [{"label": "Re-read 1 source last read over 30 days ago", "then": {"resend": {"mode": "reread", "items": [{"link": LINK}]}}}],
        )

    def test_a_missing_summary_role_is_not_set_up_before_any_read(self) -> None:
        roles = {role: model for role, model in ALL_ROLES.items() if role != "atlas_escalate"}
        fake = self.fake(roles=roles)
        answer, code = self.add(fake)
        self.assertEqual(code, 3)
        self.assertEqual([item["what"] for item in answer["result"]["needs_action"]], ["Role atlas_escalate is missing"])
        self.assertEqual(self.reads(fake), [])


TEXT_GIVEN = PAGE.text


if __name__ == "__main__":
    unittest.main()

