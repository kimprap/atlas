"""Repo citations through ``app.run`` with the fake host, a temporary ``HOME`` and ``XDG_STATE_HOME`` and a fixed clock (AC-8.1).

``add`` with ``cited_in`` stores one row per cited source and topic version, replaces a file's citations when it is cited
again, and asks its confirm before anything else; ``archive`` and ``restore`` of a ``citation`` hide and bring back a
file's rows; a re-read, a redo and the catch-up name who cites a claim that changed. Each absence (no row, no ``cited_in``,
no replacement, no stop) is paired with the case where it happens.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest import mock

from tests.fakes.fake_host import FakeHost, support, text_reply, tool_reply
from tests.test_add import (
    ITEMS,
    NEVER,
    PRICES,
    RAW,
    REPO,
    REPO_PAGE,
    SECOND,
    SECOND_PAGE,
    SECOND_RECORD,
    VIDEO,
    VIDEO_PAGE,
    VIDEO_RECORD,
    VIDEO_TRANSCRIPT,
    WINDOW,
    follow,
    item_page,
    item_record,
    request,
)
from tests.test_catchup import CatchupTest, StoreTest, caught, s
from tests.test_redo import NEW_ROLES, haiku, sonnet
from tests.test_redo import PRICES as REDO_PRICES
from tests.test_reread import BASE, NEW_C3, REREAD, WINDOWS_LINE, page
from tests.test_summarize import C1, C2, C3, LINK, PAGE, record

from atlas import ports  # noqa: E402
from atlas.core import app, spend  # noqa: E402

REPO_NAME = "owner/app"
FILE = "docs/research/findings.md"
ALIAS = "https://example.com/builds-alias"
RECORDS = {LINK: record(C1, C2, C3), SECOND: SECOND_RECORD, VIDEO: VIDEO_RECORD, **{item.link: item_record(item.path) for item in ITEMS}}
CACHING = {"topic": "Caching", "version": 1}
WINDOWS = {"topic": "Windows", "version": 1}


def fake(*summarized: str, **extra: Any) -> FakeHost:
    """A host that serves the test pages and answers one summary per link in ``summarized``, in that order."""
    pages: dict[str, Any] = {LINK: PAGE, ALIAS: PAGE, SECOND: SECOND_PAGE, VIDEO: VIDEO_PAGE, REPO: REPO_PAGE}
    pages.update({item.link: item_page(item.link, item.path) for item in ITEMS})
    pages.update(extra.pop("pages", {}))
    settings: dict[str, Any] = {
        "pages": pages,
        "transcripts": {VIDEO: VIDEO_TRANSCRIPT},
        "replies": {"atlas_summarize": [tool_reply(RECORDS[link]) for link in summarized]},
        "judge_answer": lambda state, question: ports.Answer(p=0.1) if question.id == "same_work" else support(0.95),
    }
    settings.update(extra)
    return FakeHost(**settings)


def items(*links: str) -> list[dict[str, str]]:
    return [{"link": link} for link in links]


def cited_in(file: str = FILE, repo: str = REPO_NAME, **more: Any) -> dict[str, Any]:
    return {"repo": repo, "file": file, **more}


def named(day: datetime, file: str, repo: str = REPO_NAME, **what: Any) -> dict[str, Any]:
    """A citation as a reply names it, written on ``day``."""
    return {"repo": repo, "file": file, "date": day.astimezone().date().isoformat(), **what}


class CitationBase(StoreTest):
    """A profile whose ``add`` runs without a confirm, a topic ``Caching`` with one saved version and a clock the test moves."""

    CONFIG = NEVER

    def setUp(self) -> None:
        super().setUp()
        self.configure(self.CONFIG)
        self.now = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
        self.enterContext(mock.patch.object(spend, "local_now", lambda: self.now))
        self.put_topic("Caching", "Do build caches help?", [[]])

    def day(self) -> datetime:
        """Move the clock to the next day; returns the time it showed before."""
        before, self.now = self.now, self.now + timedelta(days=1)
        return before

    def run_add(self, host: FakeHost, **body: Any) -> tuple[dict[str, Any], int]:
        return app.run("add", None, body, host.host())

    def stored(self, *links: str) -> None:
        answer, code = self.run_add(fake(*links), items=items(*links))
        self.assertEqual((code, answer["result"]["added"]), (0, len(links)), answer)

    def cite(self, *links: str, **cited: Any) -> tuple[dict[str, Any], int]:
        """A cited add of stored ``links``: every item is already stored, so nothing is read."""
        return self.run_add(fake(), items=items(*links), cited_in=cited_in(**cited))

    def citations(self) -> list[tuple]:
        """Every citation row in id order: repo, file, the source's link or ``<topic> v<n>``, archived."""
        return self.rows(
            "SELECT c.repo, c.file, COALESCE(s.key_link, t.name || ' v' || c.n), c.archived_at IS NOT NULL FROM citations c"
            " LEFT JOIN sources s ON s.id = c.source_id LEFT JOIN topics t ON t.id = c.topic_id ORDER BY c.id"
        )

    def approvals(self) -> list[tuple]:
        return self.rows("SELECT command, change_kind, by FROM approvals ORDER BY id")


class CitedAddTests(CitationBase):
    def test_stored_joined_and_new_items_and_a_topic_version_each_get_a_row_and_the_reply_counts_them(self) -> None:
        # A plain add leaves no citation and its reply has no cited_in; the same add with cited_in leaves rows.
        plain, code = self.run_add(fake(LINK), items=items(LINK))
        self.assertEqual((code, "cited_in" in plain["result"], self.citations()), (0, False, []), plain)

        topic = {"topic": "  caching ", "version": 1}
        answer, code = self.run_add(fake(SECOND), items=items(LINK, ALIAS, SECOND), cited_in=cited_in(topics=[topic]))
        self.assertEqual(code, 0, answer)
        self.assertEqual(
            [(item["link"], item["result"].split(",")[0]) for item in answer["result"]["items"]],
            [(LINK, "already stored"), (ALIAS, f"already stored as {LINK}"), (SECOND, "added")],
        )
        self.assertEqual(answer["result"]["cited_in"], {"repo": REPO_NAME, "file": FILE, "sources": 2, "topics": 1, "replaced": 0})
        # The first citing transaction stores the topic version; the joined alias leaves the source the file already cites.
        self.assertEqual(
            self.citations(),
            [(REPO_NAME, FILE, "Caching v1", 0), (REPO_NAME, FILE, LINK, 0), (REPO_NAME, FILE, SECOND, 0)],
        )
        self.assertEqual(self.approvals(), [("add", "add", "never")] * 2, "one approvals row per applied change")

    def test_each_child_of_an_expanding_choice_and_each_item_source_of_an_added_page_get_a_row(self) -> None:
        children = [item.link for item in ITEMS]
        first, code = self.run_add(fake(*children), items=[{"link": REPO, "scope": "each_item"}], cited_in=cited_in())
        self.assertEqual((code, first["result"]["cited_in"]["sources"]), (0, 2), first)
        self.assertEqual([row[2] for row in self.citations()], children, "the children are cited, not the repo page")
        self.assertEqual(self.rows("SELECT count(*) FROM sources WHERE key_link = ?", REPO), [(0,)])

        again, code = self.run_add(fake(), items=items(REPO), cited_in=cited_in(file="docs/other.md"))
        self.assertEqual((code, again["result"]["items"][0]["result"]), (0, "already added as 2 items"), again)
        self.assertEqual([row[1:3] for row in self.citations()[2:]], [("docs/other.md", child) for child in children])

    def test_citing_a_file_again_replaces_its_citations_and_a_join_adds_without_replacing(self) -> None:
        self.stored(LINK, SECOND)
        self.cite(LINK, file="docs/other.md")
        first, _ = self.cite(LINK)
        self.assertEqual(first["result"]["cited_in"]["replaced"], 0)
        self.day()
        second, code = self.cite(SECOND)
        self.assertEqual((code, second["result"]["cited_in"]), (0, {"repo": REPO_NAME, "file": FILE, "sources": 1, "topics": 0, "replaced": 1}))
        self.assertEqual(
            self.citations(),
            [(REPO_NAME, "docs/other.md", LINK, 0), (REPO_NAME, FILE, LINK, 1), (REPO_NAME, FILE, SECOND, 0)],
            "the file's earlier row is archived, not deleted, and another file's row is left alone",
        )
        self.day()
        joined, code = self.cite(LINK, join=True)
        self.assertEqual((code, joined["result"]["cited_in"]["replaced"]), (0, 0))
        self.assertEqual(
            self.citations()[2:],
            [(REPO_NAME, FILE, SECOND, 0), (REPO_NAME, FILE, LINK, 0)],
            "the join adds its source and leaves the file's current citations",
        )

    def test_replaying_a_cited_add_leaves_the_same_current_citations_and_a_join_repeats_no_row(self) -> None:
        self.stored(LINK, SECOND)
        current = [(REPO_NAME, FILE, "Caching v1"), (REPO_NAME, FILE, LINK), (REPO_NAME, FILE, SECOND)]
        for replay in range(2):
            answer, code = self.cite(LINK, SECOND, topics=[CACHING])
            self.assertEqual((code, answer["result"]["cited_in"]["replaced"]), (0, 3 * replay), answer)
            self.assertEqual([row[:3] for row in self.citations() if not row[3]], current)
        self.assertEqual(sum(row[3] for row in self.citations()), 3, "the replay archived the first set and lost nothing")
        answer, code = self.cite(LINK, SECOND, topics=[CACHING], join=True)
        self.assertEqual((code, answer["result"]["cited_in"]), (0, {"repo": REPO_NAME, "file": FILE, "sources": 0, "topics": 0, "replaced": 0}))
        self.assertEqual(len(self.citations()), 6, "a join repeats no current row")

    def test_a_pick_scope_decision_still_replaces_and_stores_the_topics_and_its_join_resend_adds(self) -> None:
        self.stored(LINK)
        self.cite(LINK)
        self.day()
        approvals = len(self.approvals())
        body: dict[str, Any] = {"items": items(VIDEO), "cited_in": cited_in(topics=[CACHING])}
        answer, code = self.run_add(fake(VIDEO), **body)
        [decision] = answer["decisions"]
        self.assertEqual((code, decision["kind"]), (4, "pick_scope"), answer)
        self.assertEqual(answer["result"]["cited_in"], {"repo": REPO_NAME, "file": FILE, "sources": 0, "topics": 1, "replaced": 1})
        # Before the resend: the earlier row is replaced and the topic version stored, with the change's approvals row.
        self.assertEqual(self.citations(), [(REPO_NAME, FILE, LINK, 1), (REPO_NAME, FILE, "Caching v1", 0)])
        self.assertEqual(len(self.approvals()), approvals + 1)

        [option] = [option for option in decision["options"] if option["id"] == "transcript"]
        join = {"repo": REPO_NAME, "file": FILE, "join": True}
        self.assertEqual(option["then"], {"resend": {"items": [{"link": VIDEO, "scope": "transcript"}], "cited_in": join}})
        answer, code = self.run_add(fake(VIDEO), **follow(body, option, "the transcript"))
        self.assertEqual((code, answer["result"]["cited_in"]["replaced"]), (0, 0), answer)
        self.assertEqual(
            self.citations(),
            [(REPO_NAME, FILE, LINK, 1), (REPO_NAME, FILE, "Caching v1", 0), (REPO_NAME, FILE, VIDEO, 0)],
            "the resend adds its source to the new citations and replaces nothing",
        )

    def test_a_summary_failed_decision_also_replaces_and_its_retry_resend_joins(self) -> None:
        self.stored(SECOND)
        self.cite(SECOND)
        self.day()
        replies = {
            "atlas_summarize": [text_reply("", stop="tool", tool_raw=RAW), text_reply("Still prose.")],
            "atlas_escalate": [text_reply("The page says", stop="cut_off", model="fake/opus")],
        }
        body: dict[str, Any] = {"items": items(LINK), "cited_in": cited_in()}
        answer, code = self.run_add(fake(replies=replies), **body)
        [decision] = answer["decisions"]
        self.assertEqual((code, decision["kind"]), (4, "summary_failed"), answer)
        self.assertEqual(self.citations(), [(REPO_NAME, FILE, SECOND, 1)], "nothing is stored, yet the file's earlier citation is replaced")
        [retry] = [option for option in decision["options"] if option["id"] == "retry"]
        join = {"repo": REPO_NAME, "file": FILE, "join": True}
        self.assertEqual(retry["then"], {"resend": {"items": [{"link": LINK}], "cited_in": join}})
        answer, code = self.run_add(fake(LINK), **follow(body, retry, "retry"))
        self.assertEqual((code, answer["result"]["items"][0]["result"]), (0, "added"), answer)
        self.assertEqual(self.citations(), [(REPO_NAME, FILE, SECOND, 1), (REPO_NAME, FILE, LINK, 0)])

    def test_an_add_that_leaves_no_source_and_returns_no_decision_replaces_and_writes_nothing(self) -> None:
        self.stored(LINK)
        self.cite(LINK)
        self.day()
        before = (self.citations(), self.approvals())
        gone = fake(pages={SECOND: ports.Unreadable("gone", "HTTP 404")})
        answer, code = self.run_add(gone, items=items(SECOND), cited_in=cited_in(topics=[CACHING]))
        self.assertEqual((code, answer["result"]["items"][0]["result"]), (0, "unreadable: gone"), answer)
        self.assertEqual(answer["result"]["cited_in"], {"repo": REPO_NAME, "file": FILE, "sources": 0, "topics": 0, "replaced": 0})
        self.assertEqual((self.citations(), self.approvals()), before)

    def test_bad_cited_in_fields_are_exit_2_naming_the_field_and_reread_and_redo_reject_cited_in(self) -> None:
        good = {"repo": REPO_NAME, "file": FILE}
        cases = [
            ("cited_in", "docs/a.md"),
            ("cited_in.repo", {"file": FILE}),
            ("cited_in.repo", {"repo": "  ", "file": FILE}),
            ("cited_in.file", {"repo": REPO_NAME}),
            ("cited_in.file", {**good, "file": "/etc/passwd"}),
            ("cited_in.extra", {**good, "extra": 1}),
            ("cited_in.join", {**good, "join": "yes"}),
            ("cited_in.topics", {**good, "topics": CACHING}),
            ("cited_in.topics[1]", {**good, "topics": [CACHING, {"topic": "Caching"}]}),
            ("cited_in.topics[0].topic", {**good, "topics": [{"topic": "Nobody", "version": 1}]}),
            ("cited_in.topics[0].version", {**good, "topics": [{"topic": "Caching", "version": 2}]}),
            ("cited_in.topics[0].version", {**good, "topics": [{"topic": "Caching", "version": True}]}),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                host = fake(LINK)
                answer, code = self.run_add(host, items=items(LINK), cited_in=value)
                self.assertEqual((code, answer["problems"][0]["field"]), (2, field), answer)
                self.assertEqual((self.calls(host, "read"), self.rows("SELECT count(*) FROM sources")), ([], [(0,)]))
        for mode, body in (("reread", {"items": items(LINK)}), ("redo", {"links": [LINK]})):
            with self.subTest(mode=mode):
                answer, code = app.run("add", mode, {**body, "cited_in": good}, fake().host())
                self.assertEqual((code, answer["problems"][0]["field"]), (2, "cited_in"), answer)
        # The same body with a good cited_in is accepted.
        answer, code = self.run_add(fake(LINK), items=items(LINK), cited_in=good)
        self.assertEqual((code, answer["result"]["cited_in"]["sources"]), (0, 1), answer)


class CitedAddApprovalTests(CitationBase):
    CONFIG = "rethink = false\n"  # confirm.add stays "always"

    def test_a_request_approval_never_runs_a_cited_add_while_a_confirm_does_also_for_stored_items(self) -> None:
        # Presence: the user's words run a plain add of the link, which stores it.
        plain, code = self.run_add(fake(LINK), items=items(LINK), approval=request(LINK))
        self.assertEqual((code, plain["decisions"]), (0, []), plain)
        stored = self.approvals()

        body: dict[str, Any] = {"items": items(LINK), "cited_in": cited_in(topics=[CACHING])}
        for approval in (None, request(LINK)):
            with self.subTest(approval=approval):
                host = fake()
                answer, code = self.run_add(host, **body, **({} if approval is None else {"approval": approval}))
                [decision] = answer["decisions"]
                self.assertEqual((code, decision["kind"]), (4, "confirm"), answer)
                self.assertIn(f"Cite 1 link and 1 topic version for {FILE} in {REPO_NAME}", decision["question"])
                self.assertEqual((self.citations(), self.approvals(), self.calls(host, "read")), ([], stored, []))
        [go] = [option for option in decision["options"] if option["id"] == "go"]
        answer, code = self.run_add(fake(), **follow(body, go, "yes, cite them"))
        self.assertEqual((code, answer["decisions"]), (0, []), answer)
        self.assertEqual(self.citations(), [(REPO_NAME, FILE, "Caching v1", 0), (REPO_NAME, FILE, LINK, 0)])
        self.assertEqual(self.approvals()[len(stored):], [("add", "add", "confirm")])

    def test_reading_two_links_is_one_confirm_with_the_estimate_and_window_use_and_no_second_one(self) -> None:
        self.configure(f"rethink = false\n{PRICES}")
        body: dict[str, Any] = {"items": items(LINK, SECOND), "cited_in": cited_in()}
        host = fake(LINK, SECOND, windows=[WINDOW])
        answer, code = self.run_add(host, **body)
        [decision] = answer["decisions"]
        self.assertEqual((code, decision["kind"]), (4, "confirm"), answer)
        self.assertIn(f"Cite 2 links and 0 topic versions for {FILE} in {REPO_NAME}", decision["question"])
        self.assertIn("Read and summarize 2 links", decision["question"])
        self.assertIn("Estimated cost: about $0.28 at list price (about $0.14 at list price per link)", decision["question"])
        self.assertIn("Window use: fake 5-hour window at 42%, resets 2099-01-01", decision["question"])
        self.assertEqual((self.calls(host, "read"), self.citations()), ([], []))
        [go] = [option for option in decision["options"] if option["id"] == "go"]
        answer, code = self.run_add(host, **follow(body, go, "yes"))
        self.assertEqual((code, answer["decisions"], answer["result"]["cited_in"]["sources"]), (0, [], 2), answer)
        self.assertEqual([row[2] for row in self.citations()], [LINK, SECOND])
        self.assertEqual(self.approvals(), [("add", "add", "confirm")])


class ArchiveCitationTests(CitationBase):
    CONFIG = NEVER  # confirm.archive and confirm.restore stay "always"

    def archive(self, command: str, repo: str = REPO_NAME, file: str = FILE, words: str | None = None) -> tuple[dict[str, Any], int]:
        body: dict[str, Any] = {"citation": {"repo": repo, "file": file}}
        if words is not None:
            body["approval"] = {"by": "request", "words": words}
        return app.run(command, None, body, FakeHost().host())

    def test_archive_and_restore_report_the_files_state_and_ask_only_when_the_words_do_not_name_both(self) -> None:
        self.stored(LINK)
        for command in ("archive", "restore"):
            answer, code = self.archive(command)
            self.assertEqual((code, answer["result"]["result"], answer["decisions"]), (0, "not stored", []), answer)
            self.assertEqual(answer["problems"][0]["problem"], "not stored; cite it with `add` first")
        self.cite(LINK)
        approvals = len(self.approvals())
        answer, code = self.archive("archive", repo="other/app")
        self.assertEqual((code, answer["result"]["result"], answer["decisions"]), (0, "not stored", []), "the repo is part of the file's identity")

        answer, code = self.archive("restore")
        self.assertEqual((code, answer["result"]["result"], answer["decisions"]), (0, "not archived", []), answer)
        for words in (None, f"Archive the citations of {FILE}", f"Archive the citations in {REPO_NAME}"):
            answer, code = self.archive("archive", words=words)
            self.assertEqual((code, [d["kind"] for d in answer["decisions"]]), (4, ["confirm"]), (words, answer))
        self.assertEqual((self.citations(), len(self.approvals())), ([(REPO_NAME, FILE, LINK, 0)], approvals))

        words = f"Archive the citations of {FILE} in {REPO_NAME.upper()}"
        answer, code = self.archive("archive", words=words)
        self.assertEqual((code, answer["result"]), (0, {"citation": {"repo": REPO_NAME, "file": FILE}, "result": "archived"}), answer)
        self.assertEqual(self.citations(), [(REPO_NAME, FILE, LINK, 1)])
        self.assertEqual(self.approvals()[approvals:], [("archive", "archive", "request")])
        answer, code = self.archive("archive")
        self.assertEqual((code, answer["result"]["result"], answer["decisions"]), (0, f"already archived {self.now.astimezone().date()}", []), answer)
        answer, code = self.archive("restore", words=f"Restore {REPO_NAME} {FILE}")
        self.assertEqual((code, answer["result"]["result"]), (0, "restored"), answer)
        self.assertEqual(self.citations(), [(REPO_NAME, FILE, LINK, 0)])
        for body in ({"citation": {"repo": "r"}}, {"citation": {"repo": " ", "file": "f"}}, {"citation": "f"}):
            self.assertEqual(app.run("archive", None, body, FakeHost().host())[1], 2, body)


class CatchupCitationTests(CatchupTest):
    def setUp(self) -> None:
        super().setUp()
        self.configure(NEVER)
        self.now = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)
        self.enterContext(mock.patch.object(spend, "local_now", lambda: self.now))
        self.topics()

    def day(self) -> datetime:
        before, self.now = self.now, self.now + timedelta(days=1)
        return before

    def cite(self, repo: str, file: str, **more: Any) -> None:
        body = {"items": items(s(1)), "cited_in": cited_in(file=file, repo=repo, **more)}
        answer, code = app.run("add", None, body, FakeHost().host())
        self.assertEqual(code, 0, answer)

    def changed(self) -> dict[str, dict[str, Any]]:
        fake = self.host({"Caching": caught(True, s(1)), "Latency": caught(True, s(3))})
        answer, code = self.catch(fake)
        self.assertEqual(code, 0, answer)
        return {entry["topic"]: entry for entry in answer["result"]["changed"]}

    def rows_of(self, file: str) -> list[tuple]:
        return self.rows("SELECT archived_at IS NOT NULL, source_id IS NULL FROM citations WHERE file = ? ORDER BY id", file)

    def test_the_catch_up_names_who_cites_a_changed_topic_and_archive_and_restore_hide_and_return_only_the_newest_set(self) -> None:
        # docs/a.md is cited, then cited again a day later (replacing its first set); z.md is another repo's.
        first, topics = self.now, [CACHING]
        self.cite("owner/app", "docs/a.md", topics=topics)
        self.cite("alpha/zed", "z.md")
        self.day()
        second = self.now
        self.cite("owner/app", "docs/a.md", topics=topics)
        self.assertEqual(self.rows_of("docs/a.md"), [(1, 1), (1, 0), (0, 1), (0, 0)], "the replaced set is archived, not deleted")

        # The agreed version's citations come first, then those of the topic's sources, each by repo and file.
        whole = [
            named(second, "docs/a.md", topic="Caching", version=1),
            named(first, "z.md", repo="alpha/zed", link=s(1)),
            named(second, "docs/a.md", link=s(1)),
        ]
        changed = self.changed()
        self.assertEqual(changed["Caching"]["cited_in"], whole)
        self.assertNotIn("cited_in", changed["Latency"], "a changed topic nobody cites has no cited_in")

        self.day()
        target = {"repo": "owner/app", "file": "docs/a.md"}
        words = "Archive the citations of docs/a.md in owner/app"
        answer, code = app.run("archive", None, {"citation": target, "approval": {"by": "request", "words": words}}, FakeHost().host())
        self.assertEqual((code, answer["result"]["result"]), (0, "archived"), answer)
        self.assertEqual(self.rows_of("docs/a.md"), [(1, 1), (1, 0)] * 2)
        self.assertEqual(self.changed()["Caching"]["cited_in"], whole[1:2], "an archived file is no longer named")

        self.day()
        words = "Restore the citations of docs/a.md in owner/app"
        answer, code = app.run("restore", None, {"citation": target, "approval": {"by": "request", "words": words}}, FakeHost().host())
        self.assertEqual((code, answer["result"]["result"]), (0, "restored"), answer)
        self.assertEqual(self.rows_of("docs/a.md"), [(1, 1), (1, 0), (0, 1), (0, 0)], "only the newest archived set came back")
        self.assertEqual(self.changed()["Caching"]["cited_in"], whole, "the replaced set stays hidden and the restored one is named again")


class RereadCitationTests(CitationBase):
    def setUp(self) -> None:
        super().setUp()
        stored = FakeHost(pages={LINK: BASE}, replies={"atlas_summarize": [tool_reply(record(C1, C2, C3))]}, judge_answer=lambda state, question: support(0.95))
        _, code = self.add(stored)
        self.assertEqual(code, 0)
        self.put_topic("Windows", "Does the cache work on Windows?", [self.copies(LINK, 3)])
        self.written = self.now
        self.cite(LINK, file="docs/a.md", topics=[WINDOWS])
        self.cite(LINK, file="docs/b.md")

    def reread(self, text: str, replies: list[ports.Reply] | None = None) -> tuple[dict[str, Any], int]:
        host = FakeHost(pages={LINK: page(text)}, replies={"atlas_summarize": replies or []}, judge_answer=lambda state, question: support(0.95))
        return self.add(host, REREAD, mode="reread")

    def test_a_reread_names_the_citations_of_a_changed_claim_and_names_none_when_no_claim_changed(self) -> None:
        answer, code = self.reread(f"{BASE.text}\nOne short line added.")
        self.assertEqual((code, answer["result"]["items"]), (0, [{"link": LINK, "result": "re-read, no meaningful change"}]), answer)

        text = "Updated in November.\n" + BASE.text.replace(WINDOWS_LINE, "The cache now works on Windows too.")
        [(id3,)] = self.rows("SELECT id FROM claims WHERE ord = 3")
        update = {"affected": [{"ref": f"c{id3}", "action": "revise", **NEW_C3}], "added": []}
        answer, code = self.reread(text, [tool_reply(update)])
        self.assertEqual(code, 0, answer)
        [item] = answer["result"]["items"]
        self.assertEqual((item["result"], item["topics_flagged"]), ("updated (1 claims changed)", ["Windows"]))
        # The source's citations by repo and file, then the flagged topic's agreed version.
        self.assertEqual(
            item["cited_in"],
            [
                named(self.written, "docs/a.md", link=LINK),
                named(self.written, "docs/b.md", link=LINK),
                named(self.written, "docs/a.md", topic="Windows", version=1),
            ],
        )


class RedoCitationTests(CitationBase):
    CONFIG = f'rethink = false\n[profiles.smoke.confirm]\nadd = "never"\nadd_redo = "never"\n{REDO_PRICES}'
    C2_NEW = {**C2, "text": "Use the cache only with deterministic builds and a clean tree."}

    def setUp(self) -> None:
        super().setUp()
        stored = FakeHost(
            pages={LINK: PAGE, SECOND: SECOND_PAGE},
            replies={"atlas_summarize": [sonnet(record(C1, C2, C3)), sonnet(SECOND_RECORD)]},
            judge_answer=lambda state, question: support(0.95),
        )
        answer, code = app.run("add", None, {"items": items(LINK, SECOND)}, stored.host())
        self.assertEqual(code, 0, answer)
        self.put_topic("Windows", "Does the cache work on Windows?", [self.copies(LINK, 3)])
        self.written = self.now
        self.cite(LINK, SECOND, topics=[CACHING, WINDOWS])

    def test_a_redo_names_the_citations_only_of_a_source_whose_claims_changed(self) -> None:
        host = FakeHost(
            pages={LINK: PAGE, SECOND: SECOND_PAGE},
            roles=NEW_ROLES,
            replies={"atlas_summarize": [haiku(record(C1, self.C2_NEW)), haiku(SECOND_RECORD)]},
            judge_answer=lambda state, question: support(0.95),
        )
        answer, code = app.run("add", "redo", {}, host.host())
        self.assertEqual(code, 0, answer)
        changed, unchanged = {item["link"]: item for item in answer["result"]["items"]}.values()
        self.assertEqual((changed["result"], unchanged["result"]), ("redone", "redone"))
        self.assertEqual(changed["topics_flagged"], ["Windows"])
        # Both sources are cited by the same file, so the only difference is whether their claims changed.
        self.assertEqual(
            changed["cited_in"],
            [named(self.written, FILE, link=LINK), named(self.written, FILE, topic="Windows", version=1)],
        )
        self.assertNotIn("cited_in", unchanged)


if __name__ == "__main__":
    unittest.main()
