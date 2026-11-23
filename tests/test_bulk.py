"""The bulk runner offline (AC-B1 to AC-B6): ``tools/bulk/bulk.py`` through its ``main`` on the fake host.

Every case runs on a temporary ``HOME`` and ``XDG_STATE_HOME``, so the real settings, stores and state folders are
never read or written. The fake host holds the pages and scripts the model replies; no network, model or judge call
is made. The expected values come from the route's contract (``ARCHITECTURE.md`` "Bulk runner"), not from a run.
"""

from __future__ import annotations

import dataclasses
import io
import itertools
import json
import os
import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from typing import Any
from unittest import mock

from tests.fakes.fake_host import FakeHost, text_reply, tool_reply

from atlas import ports  # noqa: E402
from atlas.core import add, app, reply  # noqa: E402
from tools.bulk import bulk  # noqa: E402

TOKEN = "ghp_test_secret_value_123"
ITEMS = (ports.RepoItem("one", "https://github.com/fake/tools/tree/HEAD/one", "skill"), ports.RepoItem("two", "https://github.com/fake/tools/tree/HEAD/two", "skill"))
PAGES = [f"p{n}" for n in range(1, 10)] + ["g1", "b1", "u1", "stored", "seed", "x1", "x2", "L1", "L2", "later", "pic"]


def url(name: str) -> str:
    return f"https://example.com/{name}"


def sentence(name: str, n: int) -> str:
    return f"Sentence {('one', 'two', 'three')[n]} about {name}-a {name}-b {name}-c {name}-d."


def page(link: str, name: str, kind: str = "article", **extra: Any) -> ports.Page:
    text = f"# {name.title()}\n" + "\n".join(sentence(name, n) for n in range(3))
    return ports.Page(link, name.title(), None, None, None, kind, text, **extra)


def summary(messages: Any) -> ports.Reply:
    """A model reply built from the page it is given; the page named ``broken`` gets a reply with no tool call."""
    name = re.search(r"Sentence one about (\w+)-a", json.dumps(messages)).group(1)  # type: ignore[union-attr]
    if name == "broken":
        return text_reply("I would rather not.")
    record = {"abstract": f"A note on {name}.", "claims": [{"text": sentence(name, n), "basis": "asserted", "quotes": [sentence(name, n)]} for n in range(2)]}
    return tool_reply(record, "Rethink: no change")


def billed(messages: Any) -> ports.Reply:
    return dataclasses.replace(summary(messages), cost=ports.Cost(1.0, "billed"))


class BulkCase(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.state = self.home / "state"
        env = {"HOME": str(self.home), "XDG_STATE_HOME": str(self.state)}
        self.enterContext(mock.patch.dict(os.environ, env))
        for variable in ("ATLAS_PROFILE", "GITHUB_TOKEN", "GH_TOKEN"):
            os.environ.pop(variable, None)
        self.store = self.home / "data" / "bulk.db"
        self.write_settings()
        self.fake = self.host()
        self.out, self.err = io.StringIO(), io.StringIO()
        self.sent: list[dict[str, Any]] = []
        self.intercept: Any = None
        real = app.run

        def spy(command: str, mode: Any, body: dict[str, Any], host: ports.Host) -> tuple[dict[str, Any], int]:
            self.sent.append(body)
            made = self.intercept(body) if self.intercept is not None else None
            return made if made is not None else real(command, mode, body, host)

        self.enterContext(mock.patch.object(app, "run", spy))

    def write_settings(self, extra: str = "") -> None:
        settings = self.home / ".config" / "atlas" / "config.toml"
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(
            f'default_profile = "main"\n[profiles.main]\nstore = "{self.home / "data" / "main.db"}"\njudge = "jev"\n'
            f'[profiles.bulk]\nstore = "{self.store}"\njudge = "jev"\n{extra}'
            '[prices."fake/sonnet"]\ninput = 2.0\noutput = 10.0\ncache_read = 0.2\ncache_write = 2.5\n'
        )

    def host(self, reply: Any = summary, **kwargs: Any) -> FakeHost:
        pages = {url(name): page(url(name), name) for name in PAGES}
        pages[url("broken")] = page(url("broken"), "broken")
        pages["https://x.com/user/status/1"] = page("https://x.com/user/status/1", "tweet")
        pages["https://github.com/fake/issues/1"] = page("https://github.com/fake/issues/1", "issue")
        pages["https://github.com/fake/tools"] = page("https://github.com/fake/tools", "golf", "repo", items=ITEMS)
        pages["https://www.youtube.com/watch?v=abc123"] = page("https://www.youtube.com/watch?v=abc123", "victor", "video")
        del pages[url("u1")]  # the page that does not read
        transcripts = {"https://www.youtube.com/watch?v=abc123": page("https://www.youtube.com/watch?v=abc123", "victor", "video")}
        return FakeHost(pages=pages, transcripts=transcripts, reply_with={"atlas_summarize": reply, "atlas_escalate": reply}, **kwargs)

    def bulk(self, *argv: str, now: Any = None) -> int:
        self.out.seek(0), self.out.truncate(), self.err.seek(0), self.err.truncate()
        kwargs = {} if now is None else {"now": now}
        return bulk.main(list(argv), host_factory=lambda profile: self.fake.host(), out=self.out, err=self.err, **kwargs)

    def run_cmd(self, name: str, *flags: str, now: Any = None) -> int:
        return self.bulk("run", "--profile", "bulk", "--name", name, *flags, now=now)

    def command(self, command: str, name: str, *rest: str) -> int:
        return self.bulk(command, "--profile", "bulk", "--name", name, *rest)

    def links_file(self, *lines: str) -> str:
        path = self.home / "links.txt"
        path.write_text("\n".join(lines) + "\n")
        return str(path)

    def ledger_file(self, name: str) -> Path:
        return self.state / "atlas" / "bulk" / "bulk" / f"{name}.json"

    def ledger(self, name: str) -> dict[str, Any]:
        return json.loads(self.ledger_file(name).read_text())

    def last(self) -> str:
        return self.out.getvalue().splitlines()[-1]

    def reads(self) -> list[str]:
        return [call[1] for call in self.fake.calls if call[0] == "read"]

    def batches(self) -> list[list[str]]:
        """The links of each ``add`` the runner started (resends of a decision and approved repeats left out)."""
        return [[item["link"] for item in body["items"]] for body in self.sent if "approval" not in body and all("scope" not in item for item in body["items"])]

    def rows(self, sql: str) -> list[tuple]:
        with closing(sqlite3.connect(self.store)) as conn:
            return conn.execute(sql).fetchall()


class QueueAndLaneTests(BulkCase):
    def test_links_are_cleaned_and_deduplicated_and_sent_by_lane_in_batches_of_at_most_8(self) -> None:
        # A store that already holds a link: it is never sent again.
        app.run("add", None, {"profile": "bulk", "items": [{"link": url("stored")}], "approval": {"by": "request", "words": f"add {url('stored')}"}}, self.fake.host())
        self.sent.clear()
        self.fake.calls.clear()
        video, image = "https://www.youtube.com/watch?v=abc123", url("pic") + ".png"
        self.fake.pages[image] = page(image, "pic")
        gh_page, repo, tweet = "https://github.com/fake/issues/1", "https://github.com/fake/tools", "https://x.com/user/status/1"
        pages = [url(f"p{n}") for n in range(1, 10)]
        path = self.links_file("# the queue", video, image, repo, "", gh_page, tweet, *pages, url("p1") + "?utm_source=feed", url("stored"), "not a link")
        code = self.run_cmd("lanes", "--links", path, "--yes", "--no-token")
        self.assertEqual(code, 0, self.err.getvalue())
        # Lanes run page, X post, GitHub page, repo root, video, image; a batch is at most 8 links of one lane.
        self.assertEqual(self.batches(), [pages[:8], pages[8:], [tweet], [gh_page], [repo], [video], [image]])
        self.assertEqual(list(dict.fromkeys(self.reads())), [*pages, tweet, gh_page, repo, video, image])
        stored = {row[0] for row in self.rows("SELECT key_link FROM sources")}
        self.assertEqual(stored, {*pages, url("stored"), tweet, gh_page, repo, video, image})
        # The repo is added as its page and the video as its transcript, never an expanding scope; each batch's confirm carried the approval words.
        self.assertEqual(dict(self.rows("SELECT key_link, scope_choice FROM sources WHERE scope_choice IS NOT NULL")), {repo: "page", video: "transcript"})
        self.assertNotIn(ITEMS[0].link, self.reads())
        self.assertEqual({row[0] for row in self.rows("SELECT words FROM approvals")} - {f"add {url('stored')}"}, {"bulk.py run --yes"})
        # Everything stored left the ledger; only the text that is not a link stays, dropped, with no lane.
        self.assertEqual(self.ledger("lanes")["links"], {"not a link": {"lane": None, "state": "dropped", "reason": "not a full http(s) link", "attempts": 0, "last_run": 0}})
        self.assertEqual(self.last(), "nothing left to send: 0 parked, 1 dropped")

    def test_a_slice_ends_after_the_batch_in_flight_and_a_rerun_continues_from_store_and_ledger(self) -> None:
        pages = [url(f"p{n}") for n in range(1, 10)]
        ticks = itertools.count()
        # The clock moves 30 minutes at every look: the first batch starts, the second would start past the 40-minute slice.
        code = self.run_cmd("sliced", "--links", self.links_file(*pages), "--yes", "--slice", "40", now=lambda: next(ticks) * 1800.0)
        self.assertEqual(code, 0, self.err.getvalue())
        self.assertEqual(self.batches(), [pages[:8]])
        self.assertEqual(self.last(), "run again to continue")
        self.assertIn("page done 8", self.out.getvalue())
        self.assertIn("page queued 1", self.out.getvalue())
        path = self.ledger_file("sliced")
        self.assertEqual(self.ledger("sliced")["run"], 1)
        self.assertEqual(list(self.ledger("sliced")["links"]), [pages[8]])
        self.assertEqual(self.ledger("sliced")["links"][pages[8]]["state"], "queued")
        self.assertEqual((path.stat().st_mode & 0o777, path.parent.stat().st_mode & 0o777), (0o600, 0o700))
        self.assertEqual([p.name for p in path.parent.iterdir()], ["sliced.json"])
        # The rerun needs no link list: it sends the one link left and none the store holds.
        self.sent.clear()
        self.assertEqual(self.run_cmd("sliced", "--yes"), 0, self.err.getvalue())
        self.assertEqual(self.batches(), [[pages[8]]])
        self.assertEqual(self.last(), "nothing left to send: 0 parked, 0 dropped")
        self.assertEqual(self.ledger("sliced"), {"run": 2, "links": {}})


class OutcomeTests(BulkCase):
    def test_an_unreadable_link_is_sent_in_each_of_the_next_two_runs_and_then_dropped(self) -> None:
        bad = url("u1")
        self.assertEqual(self.run_cmd("retry3", "--links", self.links_file(url("g1"), bad), "--yes"), 0, self.err.getvalue())
        self.assertEqual(self.reads().count(bad), 1)  # never twice in one run
        self.assertEqual((self.ledger("retry3")["links"][bad]["state"], self.ledger("retry3")["links"][bad]["attempts"]), ("retry", 1))
        self.assertEqual(self.last(), "run again to continue")
        for run, state in ((2, "retry"), (3, "dropped")):
            self.assertEqual(self.run_cmd("retry3", "--yes"), 0, self.err.getvalue())
            self.assertEqual(self.reads().count(bad), run)
            entry = self.ledger("retry3")["links"][bad]
            self.assertEqual((entry["state"], entry["attempts"]), (state, run))
        self.assertTrue(entry["reason"].startswith("unreadable: "))
        self.assertEqual(self.last(), "nothing left to send: 0 parked, 1 dropped")
        self.assertEqual(self.run_cmd("retry3", "--yes"), 0)
        self.assertEqual(self.reads().count(bad), 3)  # a dropped link is not sent again on its own

    def test_a_failed_summary_is_dropped_with_its_log_and_retry_puts_it_back(self) -> None:
        broken = url("broken")
        self.assertEqual(self.run_cmd("failed", "--links", self.links_file(url("g1"), broken, "not a link"), "--yes"), 0, self.err.getvalue())
        entry = self.ledger("failed")["links"][broken]
        self.assertEqual((entry["state"], entry["reason"]), ("dropped", "summary failed"))
        self.assertTrue(Path(entry["log"]).is_file() and Path(entry["log"]).is_relative_to(self.state))
        self.assertEqual(self.last(), "nothing left to send: 0 parked, 2 dropped")
        self.assertEqual(self.command("status", "failed"), 0)
        self.assertIn(f"dropped {broken}: summary failed [log {entry['log']}]", self.out.getvalue())
        self.assertIn("dropped not a link: not a full http(s) link", self.out.getvalue())
        self.assertIn("page: dropped 1", self.out.getvalue())
        # Never retried on its own; `retry <link>` and `retry --dropped` queue it again, with attempts at 0.
        reads = self.reads().count(broken)
        self.assertEqual(self.run_cmd("failed", "--yes"), 0)
        self.assertEqual(self.reads().count(broken), reads)
        self.assertEqual(self.command("retry", "failed", broken), 0)
        self.assertEqual(self.ledger("failed")["links"][broken], {"lane": "page", "state": "queued", "reason": None, "attempts": 0, "last_run": 0})
        self.assertEqual(self.run_cmd("failed", "--yes"), 0)
        self.assertEqual(self.ledger("failed")["links"][broken]["state"], "dropped")
        self.assertEqual(self.command("retry", "failed", "--dropped"), 0)
        links = self.ledger("failed")["links"]
        self.assertEqual((links[broken]["state"], links["not a link"]["state"]), ("queued", "dropped"))
        # A link that is not dropped, or not in the run, is refused and changes nothing.
        before = self.ledger_file("failed").read_bytes()
        for argv in (("retry", "failed", broken), ("retry", "failed", url("nowhere")), ("status", "nobody"), ("retry", "nobody", "--dropped")):
            self.assertEqual(self.command(*argv), 2, argv)
        self.assertEqual(self.ledger_file("failed").read_bytes(), before)

    def test_a_scope_question_with_no_fixed_answer_is_parked_and_the_answer_is_sent_on_the_next_run(self) -> None:
        odd, skipped, later = url("L1"), url("L2"), "https://x.com/user/status/1"

        def odd_decision(body: dict[str, Any]) -> tuple[dict[str, Any], int] | None:
            # The core never offers a scope question without a fixed answer today; the decision is built with its own constructors so its shape is the real one.
            asked = [item["link"] for item in body["items"] if item["link"] in (odd, skipped) and "scope" not in item]
            if "approval" in body or not asked:
                return None
            decisions = [add.pick_scope({"link": link}, f"{link} is odd: which part?", [("whole", "the whole page", "page"), ("skip", "skip it", None)]) for link in asked]
            made = reply.build("add", reply.NEEDS_DECISION, {"items": [{"link": link, "result": "pick scope"} for link in asked]}, decisions=decisions)
            return made, reply.NEEDS_DECISION

        self.intercept = odd_decision
        self.assertEqual(self.run_cmd("parked", "--links", self.links_file(odd, skipped, later), "--yes"), 0, self.err.getvalue())
        # The run went on past the parked links: the X post after them was stored.
        self.assertEqual([row[0] for row in self.rows("SELECT key_link FROM sources")], [later])
        links = self.ledger("parked")["links"]
        self.assertEqual({link: links[link]["state"] for link in links}, {odd: "parked", skipped: "parked"})
        self.assertEqual([option["id"] for option in links[odd]["options"]], ["whole", "skip"])
        self.assertEqual(self.last(), "nothing left to send: 2 parked, 0 dropped")  # a parked link without an answer is not sent
        self.assertEqual(self.command("status", "parked"), 0)
        self.assertIn(f"parked {odd}: {odd} is odd: which part? [options: whole, skip]", self.out.getvalue())
        # Unknown links and options are refused and change nothing.
        before = self.ledger_file("parked").read_bytes()
        for argv in (("answer", "parked", odd, "everything"), ("answer", "parked", url("nowhere"), "whole"), ("answer", "nobody", odd, "whole")):
            self.assertEqual(self.command(*argv), 2, argv)
        self.assertEqual(self.ledger_file("parked").read_bytes(), before)
        # An answer with a resend is sent as its own add on the next run; a skip has nothing to send and is dropped.
        self.assertEqual(self.command("answer", "parked", odd, "whole"), 0)
        self.assertEqual(self.command("answer", "parked", skipped, "skip"), 0)
        self.assertEqual(self.ledger("parked")["links"][odd]["answer"], "whole")
        self.assertEqual((self.ledger("parked")["links"][skipped]["state"], self.ledger("parked")["links"][skipped]["reason"]), ("dropped", "skipped (skip)"))
        self.assertEqual(self.last(), "recorded skip for " + skipped + "; nothing to send, so it is dropped")
        self.sent.clear()
        self.assertEqual(self.run_cmd("parked", "--yes"), 0, self.err.getvalue())
        self.assertEqual([body["items"] for body in self.sent if "approval" not in body], [[{"link": odd, "scope": "page"}]])
        self.assertEqual({row[0] for row in self.rows("SELECT key_link FROM sources")}, {later, odd})
        self.assertEqual(list(self.ledger("parked")["links"]), [skipped])
        self.assertEqual(self.last(), "nothing left to send: 0 parked, 1 dropped")


class StopTests(BulkCase):
    def queue(self) -> str:
        return self.links_file(url("p1"), url("p2"), "https://x.com/user/status/1", "https://github.com/fake/issues/1")

    def assert_stopped_at_once(self, name: str, code: int) -> None:
        """One add was started, nothing was read, and the whole queue is still in the ledger."""
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.reads(), [])
        self.assertEqual({entry["state"] for entry in self.ledger(name)["links"].values()}, {"queued"})
        self.assertEqual(len(self.ledger(name)["links"]), 4)
        self.assertTrue(self.last().startswith("stopped: "), self.last())

    def test_a_window_decision_merged_with_a_confirm_ends_the_slice_with_its_reset_time_and_a_rerun_continues(self) -> None:
        self.fake.window_rows = [ports.Window("fake", "fake:5h", 18000, 0.95, "2099-01-01T14:30:00+00:00")]
        self.assertEqual(self.run_cmd("window", "--links", self.queue(), "--yes", "--no-token"), 1)
        self.assert_stopped_at_once("window", 1)
        self.assertRegex(self.last(), r"^stopped: .*95%.*resets 2099-01-0[12] \d\d:\d\d")
        # The same queue goes on once the window has reset, so the empty read log above was the stop's doing.
        self.fake.window_rows = []
        self.assertEqual(self.run_cmd("window", "--yes", "--no-token"), 0, self.err.getvalue())
        self.assertEqual(len(self.rows("SELECT key_link FROM sources")), 4)

    def test_a_cap_decision_merged_with_a_confirm_ends_the_slice(self) -> None:
        self.write_settings("cap_usd = 1.0\n")
        self.fake = self.host(billed)
        # One billed summary puts this month's spend at the cap before the queue's first batch.
        seed = url("seed")
        app.run("add", None, {"profile": "bulk", "items": [{"link": seed}], "approval": {"by": "request", "words": f"add {seed}"}}, self.fake.host())
        self.sent.clear()
        self.fake.calls.clear()
        self.assertEqual(self.run_cmd("cap", "--links", self.queue(), "--yes", "--no-token"), 1)
        self.assert_stopped_at_once("cap", 1)
        self.assertRegex(self.last(), r"^stopped: .*monthly cap")

    def test_judge_setup_and_not_set_up_end_the_run_with_exit_3_and_any_other_decision_with_exit_1(self) -> None:
        def decision(kind: str) -> Any:
            def made(body: dict[str, Any]) -> tuple[dict[str, Any], int]:
                question = reply.decision("add", None, body, kind, f"{kind} needs you", [reply.option("stop", "stop", {"stop": True})])
                return reply.build("add", reply.NEEDS_DECISION, decisions=[question]), reply.NEEDS_DECISION

            return made

        for kind, code in (("judge_setup", 3), ("version_save", 1)):
            with self.subTest(kind):
                self.intercept = decision(kind)
                self.sent.clear()
                self.assertEqual(self.run_cmd(kind, "--links", self.queue(), "--yes", "--no-token"), code)
                self.assertEqual(self.last(), f"stopped: {kind} needs you")
                self.assertEqual(len(self.sent), 1)
        # A role the host lacks is the core's exit 3 (not set up): the run ends with its text.
        self.intercept = None
        self.fake.role_map = {}
        self.assertEqual(self.run_cmd("roles", "--links", self.queue(), "--yes", "--no-token"), 3)
        self.assertIn("atlas_summarize", self.last())
        self.assertEqual(len(self.ledger("roles")["links"]), 4)
        # A profile that is not in the settings is exit 3 before anything is sent or written.
        self.sent.clear()
        self.assertEqual(self.bulk("run", "--profile", "nowhere", "--name", "n", "--links", self.queue(), "--yes"), 3)
        self.assertIn("is not set up", self.err.getvalue())
        self.assertEqual(self.sent, [])
        self.assertFalse((self.state / "atlas" / "nowhere").exists())


class CommandTests(BulkCase):
    def test_a_link_an_add_ends_with_no_outcome_the_runner_knows_is_dropped_and_not_sent_again(self) -> None:
        odd = url("L1")
        # `add` ends a link it skipped with the result "skipped" and no decision; nothing stores it.
        self.intercept = lambda body: (reply.build("add", reply.DONE, {"items": [{"link": item["link"], "result": "skipped"} for item in body["items"]]}), reply.DONE)
        self.assertEqual(self.run_cmd("noend", "--links", self.links_file(odd), "--yes"), 0, self.err.getvalue())
        self.assertEqual(self.ledger("noend")["links"][odd]["state"], "dropped")
        self.assertEqual(self.ledger("noend")["links"][odd]["reason"], "not stored after the add: skipped")
        self.assertEqual(self.last(), "nothing left to send: 0 parked, 1 dropped")
        self.sent.clear()
        self.assertEqual(self.run_cmd("noend", "--yes"), 0)
        self.assertEqual(self.sent, [])

    def test_run_without_yes_prints_the_lanes_and_estimate_and_makes_no_call_and_writes_nothing(self) -> None:
        path = self.links_file(url("p1"), url("p2"), "https://x.com/user/status/1")
        self.assertEqual(self.run_cmd("dry", "--links", path), 0, self.err.getvalue())
        text = self.out.getvalue()
        self.assertIn("page: 2 not yet done, 2 to send", text)
        self.assertIn("x_post: 1 not yet done, 1 to send", text)
        self.assertIn("about $", text)
        self.assertEqual(self.last(), "no read, model or judge call was made and nothing was written; run again with --yes to run it")
        self.assertEqual([call for call in self.fake.calls if call[0] in ("read", "call", "judge", "image", "open_store")], [])
        self.assertEqual(self.sent, [])
        self.assertFalse(self.store.exists())
        self.assertFalse((self.state / "atlas").exists())
        # The same call with --yes does read, write the store and keep a ledger, so the checks above can see them.
        self.assertEqual(self.run_cmd("dry", "--links", path, "--yes"), 0, self.err.getvalue())
        self.assertTrue(self.reads() and self.store.exists() and self.ledger_file("dry").exists())

    def test_a_queue_with_a_github_link_needs_a_token_value_that_is_never_shown_or_stored(self) -> None:
        path = self.links_file("https://github.com/fake/tools", url("p1"))
        for variable, value in (("GITHUB_TOKEN", ""), ("GH_TOKEN", "  ")):
            os.environ[variable] = value
        self.assertEqual(self.run_cmd("tok", "--links", path, "--yes"), 2)
        self.assertIn("GITHUB_TOKEN", self.err.getvalue())
        self.assertIn("GH_TOKEN", self.err.getvalue())
        self.assertEqual((self.sent, self.reads(), self.ledger_file("tok").exists()), ([], [], False))
        # A queue with no GitHub link needs none; --no-token starts the run without one.
        self.assertEqual(self.run_cmd("page", "--links", self.links_file(url("p1")), "--yes"), 0, self.err.getvalue())
        self.assertEqual(self.run_cmd("tok", "--links", path, "--yes", "--no-token"), 0, self.err.getvalue())
        # A non-blank value in either variable starts it; the value is in no output and no ledger.
        os.environ["GH_TOKEN"] = TOKEN
        self.assertEqual(self.run_cmd("tok2", "--links", self.links_file("https://github.com/fake/issues/1"), "--yes"), 0, self.err.getvalue())
        self.assertEqual(self.command("status", "tok2"), 0)
        shown = self.out.getvalue() + self.err.getvalue() + "".join(p.read_text() for p in (self.state / "atlas").rglob("*.json"))
        self.assertTrue(self.reads().count("https://github.com/fake/issues/1"))
        self.assertNotIn(TOKEN, shown)

    def test_bad_calls_are_exit_2(self) -> None:
        for argv in (
            (), ("nothing",), ("run", "--name", "n"), ("run", "--profile", "bulk"), ("run", "--profile", "bulk", "--name", "n", "--slice", "0"),
            ("run", "--profile", "bulk", "--name", "n", "--slice", "soon"), ("run", "--profile", "bulk", "--name", "n", "--links", str(self.home / "none.txt")),
            ("run", "--profile", "bulk", "--name", "../n", "--links", self.links_file(url("p1"))), ("run", "--profile", "bulk", "--name", "n"),
            ("run", "--profile", "bulk", "--name", "n", "--bogus"), ("answer", "--profile", "bulk", "--name", "n", "only-a-link"), ("retry", "--profile", "bulk", "--name", "n"),
        ):
            with self.subTest(argv):
                self.assertEqual(self.bulk(*argv), 2)
        self.assertEqual(self.reads(), [])
        self.assertFalse((self.state / "atlas").exists())
        # A ledger this runner did not write is refused, not trusted.
        self.ledger_file("hand").parent.mkdir(parents=True)
        for text in ("not json", '{"run": 1, "links": {"https://example.com/p1": {"state": "queued"}}}'):
            self.ledger_file("hand").write_text(text)
            self.assertEqual(self.command("status", "hand"), 2, text)
            self.assertEqual(self.run_cmd("hand", "--yes"), 2, text)
        self.assertEqual(self.reads(), [])


if __name__ == "__main__":
    unittest.main()
