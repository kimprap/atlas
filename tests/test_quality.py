"""The quality tool offline (AC-5.2; the offline proof for the paid AC-5.5): ``tools/quality/quality.py`` on a temporary ``HOME``.

The tool's own host is the fake host. Versions run through ``worker.execute`` on other fake hosts from real
``git worktree`` checkouts of two refs of a temporary repository, which also holds ticket 08's history files and
the v1 vault is a temporary folder. No network, model or judge call is made, and nothing outside the temporary
folders is read or written.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest import mock

from tests.fakes.fake_host import FakeHost, support, tool_reply

from atlas import ports  # noqa: E402
from atlas.core import app  # noqa: E402
from tools.quality import _path, lanes, quality, replay_read, stats, versions, worker  # noqa: E402

ROOT = _path.ROOT
HISTORY = ".scratch/atlas-v2/prototypes/08-retrieval"
NAMES = {"a": "alpha", "b": "bravo", "c": "charlie", "h": "hotel", "i": "india"}
ARTICLES = {sid: f"https://example.com/{name}" for sid, name in NAMES.items()}
LINKS = {
    **ARTICLES,
    "d": "https://example.com/charlie?utm_source=newsletter",  # shares charlie's cleaned link with "c"
    "e": "https://example.com/gone",
    "g": "https://github.com/fake/tools",
    "v": "https://www.youtube.com/watch?v=abc123",
}
# Pool id "f" has no canonical_url in the vault.
GRADES = {
    "Q1": {"a": 2, "b": 0, "c": 1},
    "Q2": {"b": 2, "h": 1, "e": 1},
    "Q3": {"i": 1, "g": 2, "d": 1, "v": 1, "f": 0},
}
QUERIES = [
    {"qid": "Q1", "origin": "synthetic-single", "seed": "a", "seed_title": "Alpha", "text": "alpha note"},
    {"qid": "Q2", "origin": "real-user", "text": "bravo and hotel notes", "gold_user": ["b", "h"]},
    {"qid": "Q3", "origin": "synthetic-broad", "text": "india notes"},
]
REWRITES = {"Q1": ["alpha", "alpha note"], "Q2": ["bravo", "hotel"], "Q3": ["india"]}
GRADE_COUNT = sum(len(graded) for graded in GRADES.values())
ITEMS = (ports.RepoItem("one", "https://github.com/fake/tools/tree/HEAD/one", "skill"), ports.RepoItem("two", "https://github.com/fake/tools/tree/HEAD/two", "skill"))


def sentence(name: str, n: int) -> str:
    word = ("one", "two", "three")[n]
    return f"Sentence {word} about {name}-a {name}-b {name}-c {name}-d."


def text_of(name: str) -> str:
    return f"# {name.title()}\n" + "\n".join(sentence(name, n) for n in range(3))


def page(link: str, name: str, kind: str = "article", **extra: Any) -> ports.Page:
    return ports.Page(link, name.title(), None, None, None, kind, text_of(name), **extra)


def record_for(name: str, abstract: str | None = None) -> dict[str, Any]:
    return {
        "abstract": abstract or f"A note on {name}.",
        "claims": [{"text": sentence(name, n), "basis": "asserted", "quotes": [sentence(name, n)]} for n in range(2)],
    }


def name_in(messages: Any) -> str:
    found = re.search(r"Sentence one about (\w+)-a", json.dumps(messages))
    assert found, messages
    return found.group(1)


def summarizer(follow_planted: bool = False) -> Any:
    """A model reply from the page it is given; with ``follow_planted`` it obeys an inserted "deprecated" instruction."""

    def reply(messages: Any) -> ports.Reply:
        joined = json.dumps(messages)
        name = name_in(messages)
        abstract = "This project is deprecated." if follow_planted and "Ignore your instructions" in joined else None
        return tool_reply(record_for(name, abstract), "Rethink: no change")

    return reply


def key_points_reply(messages: Any) -> ports.Reply:
    name = name_in(messages)
    points = [{"text": f"{name} says one", "quote": sentence(name, 0)}, {"text": f"{name} says two", "quote": sentence(name, 1)}, {"text": "invented", "quote": "words that are not on the page"}]
    return tool_reply({"points": points})


def tool_judge(state: str, question: ports.Question) -> ports.Answer:
    if question.id == "support":
        return support(0.3 if state.startswith("Claim: Sentence two") else 0.95)
    if question.id in ("same_work", "planted"):
        return ports.Answer(p=0.1)
    return ports.Answer(p=0.9)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class QualityCase(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home), "XDG_STATE_HOME": str(self.home / "state")}))
        os.environ.pop("ATLAS_PROFILE", None)
        self.eval_db = self.home / "data" / "eval.db"
        self.main_db = self.home / "data" / "main.db"
        self.settings = self.home / ".config" / "atlas" / "config.toml"
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(
            f'default_profile = "main"\n[profiles.main]\nstore = "{self.main_db}"\njudge = "jev"\n'
            f'[profiles.eval]\nstore = "{self.eval_db}"\njudge = "jev"\nrethink = true\n'
            '[prices."fake/sonnet"]\ninput = 2.0\noutput = 10.0\ncache_read = 0.2\ncache_write = 2.5\n'
            '[prices."fake/opus"]\ninput = 5.0\noutput = 25.0\ncache_read = 0.5\ncache_write = 6.0\n'
        )
        self.vault = self.home / "vault"
        sources = self.vault / "summaries" / "sources" / "artifacts"
        sources.mkdir(parents=True)
        for sid, link in LINKS.items():
            (sources / f"{sid}.md").write_text(f'---\nsource_id: "{sid}"\ncanonical_url: "{link}"\n---\nbody\n')
        runs = self.vault / "summaries" / "sources" / "runs"
        runs.mkdir()
        (runs / "log.md").write_text('---\nsource_id: "f"\ncanonical_url: "https://example.com/log-only"\n---\n')
        self.repo = self.home / "repo"
        self.git("init", "--quiet", "-b", "main", str(self.repo), cwd=self.home)
        history = self.repo / HISTORY
        history.mkdir(parents=True)
        (history / "grades.json").write_text(json.dumps(GRADES))
        (history / "queries.json").write_text(json.dumps(QUERIES))
        (history / "rewrites.json").write_text(json.dumps(REWRITES))
        (self.repo / "marker.txt").write_text("base")
        self.base = self.commit("base")
        (self.repo / "marker.txt").write_text("cand")
        self.cand = self.commit("cand")
        self.tool_host = FakeHost(judge_answer=lambda state, question: support(0.95) if question.id == "support" else ports.Answer(p=0.1))
        self.out, self.err = io.StringIO(), io.StringIO()

    def git(self, *args: str, cwd: Path | None = None) -> str:
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "GIT_CONFIG_NOSYSTEM": "1"}
        proc = subprocess.run(["git", *args], cwd=cwd or self.repo, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def commit(self, subject: str) -> str:
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", subject)
        return self.git("rev-parse", "HEAD")

    def quality(self, *argv: str, runner: Any = None) -> int:
        self.out.seek(0), self.out.truncate(), self.err.seek(0), self.err.truncate()
        return quality.main(
            list(argv), host_factory=lambda profile: self.tool_host.host(), runner=runner, repo=self.repo,
            history_ref="HEAD", now=lambda: datetime(2026, 11, 10, 15, 0, 0), out=self.out, err=self.err,
        )

    def library_host(self) -> FakeHost:
        pages = {link: page(link, NAMES[sid]) for sid, link in ARTICLES.items()}
        pages[LINKS["g"]] = page(LINKS["g"], "golf", "repo", items=ITEMS)
        pages[LINKS["v"]] = page(LINKS["v"], "victor", "video")
        return FakeHost(
            pages=pages,
            transcripts={LINKS["v"]: ports.Page(LINKS["v"], "Victor", None, None, None, "video", text_of("victor"))},
            reply_with={"atlas_summarize": summarizer(), "atlas_escalate": summarizer()},
            judge_answer=lambda state, question: support(0.95) if question.id == "support" else ports.Answer(p=0.1),
        )

    def build_library(self, *flags: str) -> int:
        self.tool_host = self.library_host()
        return self.quality("build-library", "--vault", str(self.vault), *flags)

    def rows(self, db: Path, sql: str, *args: Any) -> list[tuple]:
        with closing(sqlite3.connect(db)) as conn:
            return conn.execute(sql, args).fetchall()

    def tool_calls(self, port: str) -> list[tuple]:
        return [call for call in self.tool_host.calls if call[0] == port]


class LibraryTests(QualityCase):
    def test_without_yes_it_prints_the_count_and_estimate_and_makes_no_call_or_write(self) -> None:
        self.tool_host = self.library_host()
        code = self.quality("build-library", "--vault", str(self.vault))
        self.assertEqual(code, 0, self.err.getvalue())
        self.assertRegex(self.out.getvalue(), r"\d+ of \d+ pool links are not stored yet")
        self.assertIn("about $", self.out.getvalue())
        self.assertEqual([call for call in self.tool_host.calls if call[0] in ("read", "call", "judge", "image")], [])
        self.assertFalse(self.eval_db.exists())
        # The same command with --yes does read and call, so the check above can see a call.
        self.assertEqual(self.build_library("--yes"), 0, self.err.getvalue())
        self.assertTrue(self.tool_calls("read") and self.tool_calls("call"))

    def test_the_library_is_built_once_and_each_pool_id_is_counted_once(self) -> None:
        code = self.build_library("--yes")
        self.assertEqual(code, 0, self.err.getvalue())
        self.assertEqual(self.out.getvalue().splitlines()[-1], f"library: 8 added, 2 unreadable, 3 queries, {GRADE_COUNT} grades")
        # Joined copies and ids that share one cleaned link count; links that do not read or have no vault link are listed.
        self.assertIn("dropped e https://example.com/gone", self.err.getvalue())
        self.assertIn("dropped f (no link): no canonical_url in the v1 vault", self.err.getvalue())
        stored = {row[0] for row in self.rows(self.eval_db, "SELECT key_link FROM sources")}
        self.assertEqual(stored, {*ARTICLES.values(), LINKS["g"], LINKS["v"]})
        # A repo and a video are added as the page and the transcript, never an expanding scope.
        scopes = dict(self.rows(self.eval_db, "SELECT key_link, scope_choice FROM sources WHERE scope_choice IS NOT NULL"))
        self.assertEqual(scopes, {LINKS["g"]: "page", LINKS["v"]: "transcript"})
        # Cases: ticket 08's queries and grades, origin ticket08.
        self.assertEqual(self.rows(self.eval_db, "SELECT kind, count(*) FROM cases WHERE origin = 'ticket08' GROUP BY kind ORDER BY kind"), [("grade", GRADE_COUNT), ("query", 3)])

        # A rerun makes no paid call and imports nothing twice; only the link that did not read is read again.
        first_reads = len(self.tool_calls("read"))
        self.tool_host.calls.clear()
        code = self.build_library("--yes")
        self.assertEqual(code, 0, self.err.getvalue())
        self.assertEqual(self.out.getvalue().splitlines()[-1], f"library: 8 added, 2 unreadable, 3 queries, {GRADE_COUNT} grades")
        self.assertEqual([call for call in self.tool_calls("call")], [])
        self.assertEqual([call[1] for call in self.tool_calls("read")], [LINKS["e"]])
        self.assertGreater(first_reads, 1)

    def test_a_window_stop_ends_the_run_with_the_decision_text_and_a_rerun_continues(self) -> None:
        self.tool_host = self.library_host()
        window = ports.Window("fake", "fake:5h", 18000, 0.95, "2099-01-01T14:30:00+00:00")
        self.tool_host.window_rows = [window]
        code = self.quality("build-library", "--yes", "--vault", str(self.vault))
        self.assertEqual(code, 1)
        self.assertRegex(self.out.getvalue().splitlines()[-1], r"^stopped: .*95%")
        self.assertEqual(self.tool_calls("call"), [])
        self.tool_host.window_rows = []
        self.assertEqual(self.quality("build-library", "--yes", "--vault", str(self.vault)), 0, self.err.getvalue())
        self.assertTrue(self.out.getvalue().splitlines()[-1].startswith("library: 8 added"))

    def test_a_store_in_a_folder_named_with_uri_characters_is_read_back_by_the_replay_adapter(self) -> None:
        self.assertEqual(self.build_library("--yes"), 0, self.err.getvalue())
        odd = self.home / "a#b?c%20d" / "eval.db"
        odd.parent.mkdir()
        with closing(sqlite3.connect(self.eval_db)) as source, closing(sqlite3.connect(odd)) as copy:
            source.backup(copy)
        self.assertEqual({record.link for record in replay_read.store_records(odd)}, {*ARTICLES.values(), LINKS["g"], LINKS["v"]})


class RunCase(QualityCase):
    """A built library, the tool's host with Jev flagging every second claim, and two version hosts: the base and the
    candidate both run from a worktree of their ref, so the marker file in it says which one a case ran on."""

    def setUp(self) -> None:
        super().setUp()
        self.assertEqual(self.build_library("--yes"), 0, self.err.getvalue())
        with closing(sqlite3.connect(self.eval_db)) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        from atlas.store import sqlite as store_sqlite

        store_sqlite.open_store(self.main_db).close()
        self.tool_host = FakeHost(judge_answer=tool_judge, reply_with={"atlas_escalate": key_points_reply})
        self.version_hosts = {
            "base": FakeHost(reply_with={"atlas_summarize": summarizer(False)}, judge=False),
            "cand": FakeHost(reply_with={"atlas_summarize": summarizer(True)}, judge=False),
        }
        self.seen: list[tuple[str, str, Path]] = []

    def runner(self, worktree: Path, job: dict[str, Any]) -> dict[str, Any]:
        label = (worktree / "marker.txt").read_text()
        self.seen.append((label, job["case"]["id"], worktree))
        return worker.execute(job, self.version_hosts[label].host())

    def compare(self, *flags: str) -> int:
        return self.quality(
            "run", "summary", "--base", self.base, "--cand", self.cand, "--set", "rethink=false", *flags, runner=self.runner
        )

    def review_key_points(self) -> int:
        reviewed = 0
        while True:
            self.assertEqual(self.quality("spot", "keypoints"), 0, self.err.getvalue())
            item = json.loads(self.out.getvalue())
            if item.get("done"):
                return reviewed
            label = "drop:2" if reviewed == 0 else "keep"
            self.assertEqual(self.quality("spot", "keypoints", "--answer", item["item"], label), 0, self.err.getvalue())
            reviewed += 1

    def tables(self) -> set[str]:
        return {row[0] for row in self.rows(self.eval_db, "SELECT name FROM sqlite_master WHERE type = 'table'")}


class EstimateTests(RunCase):
    def test_a_run_without_yes_prints_the_estimate_and_makes_no_call_and_no_write(self) -> None:
        self.tool_host.calls.clear()
        self.assertEqual(self.compare(), 0, self.err.getvalue())
        output = self.out.getvalue()
        self.assertRegex(output, r"estimate: \d+ summaries \(10 cases x 3 runs x 2 versions\); about \$[\d.]+ at list price")
        self.assertIn("have none", output)
        self.assertEqual([call for call in self.tool_host.calls if call[0] in ("read", "call", "judge", "image")], [])
        self.assertEqual(self.seen, [])
        # Nothing was written: the planning rows (the 30 pages' cases and the planted copies) were rolled back.
        planned = "SELECT (SELECT count(*) FROM cases WHERE kind IN ('page', 'planted')), (SELECT count(*) FROM key_points), (SELECT count(*) FROM runs)"
        self.assertEqual(self.rows(self.eval_db, planned), [(0, 0, 0)])

    def test_key_points_are_drafted_with_found_quotes_and_the_run_waits_for_the_users_review(self) -> None:
        self.assertEqual(self.compare("--yes"), 1, self.err.getvalue())
        self.assertIn("drafted key points for 7 pages", self.out.getvalue())
        self.assertEqual(len(self.tool_calls("call")), 7)
        # The draft's third point quotes words that are not on the page, so it is left out.
        counts = self.rows(self.eval_db, "SELECT count(*), min(reviewed_at) FROM key_points GROUP BY case_id")
        self.assertEqual(counts, [(2, None)] * 7)
        self.assertEqual(self.seen, [])
        self.assertEqual(self.compare("--yes"), 1)
        self.assertIn("have not reviewed", self.err.getvalue())
        self.assertEqual(self.seen, [])
        self.assertEqual(self.review_key_points(), 7)
        self.assertEqual(self.rows(self.eval_db, "SELECT count(*) FROM key_points"), [(13,)])

    def test_a_failed_key_point_call_stops_the_run_with_its_reason_and_keeps_nothing_half_drafted(self) -> None:
        self.tool_host = FakeHost(judge_answer=tool_judge, reply_with={"atlas_escalate": lambda messages: ports.CallFailed(503, "gateway down")})
        self.assertEqual(self.compare("--yes"), 1)
        self.assertRegex(self.err.getvalue(), r"^stopped: the key-point draft of https://\S+ failed: .*gateway down")
        self.assertEqual(self.rows(self.eval_db, "SELECT (SELECT count(*) FROM key_points), (SELECT count(*) FROM runs)"), [(0, 0)])
        self.assertEqual(self.seen, [])


class ComparisonTests(RunCase):
    def setUp(self) -> None:
        super().setUp()
        self.assertEqual(self.compare("--yes"), 1, self.err.getvalue())
        self.review_key_points()
        self.settings_before, self.main_before = sha(self.settings), sha(self.main_db)
        self.library_before = self.library_rows()
        self.assertEqual(self.compare("--yes", "--runs", "2"), 0, self.err.getvalue())
        self.report = self.out.getvalue()
        [(self.comparison,)] = self.rows(self.eval_db, "SELECT id FROM comparisons")

    def library_rows(self) -> list[tuple]:
        return self.rows(self.eval_db, "SELECT (SELECT count(*) FROM sources), (SELECT count(*) FROM claims), (SELECT count(*) FROM calls), (SELECT count(*) FROM queries), (SELECT count(*) FROM summary_history)")

    def test_each_version_runs_its_own_ref_from_a_worktree_that_is_gone_afterwards(self) -> None:
        by_label = {label: {case for lab, case, _ in self.seen if lab == label} for label in ("base", "cand")}
        self.assertEqual(by_label["base"], by_label["cand"])
        self.assertEqual(len(by_label["base"]), 10)
        self.assertEqual(len([seen for seen in self.seen if seen[0] == "base"]), 20)
        self.assertEqual(self.git("worktree", "list").count("\n"), 0)
        self.assertEqual(list((self.home / ".cache" / "atlas-quality").iterdir()), [])
        self.assertEqual(
            self.rows(self.eval_db, "SELECT label, ref, rep FROM runs ORDER BY id"),
            [("base", self.base, 1), ("cand", self.cand, 1), ("base", self.base, 2), ("cand", self.cand, 2)],
        )

    def test_overrides_reach_the_version_through_an_in_memory_profile_and_only_eval_is_written(self) -> None:
        turns = dict(((r, c), v) for r, c, m, v in self.rows(self.eval_db, "SELECT r.label, m.case_id, m.measure, m.value FROM measures m JOIN runs r ON r.id = m.run_id") if m == "model_turns")
        page_turns = {label: {v for (lab, _), v in turns.items() if lab == label} for label in ("base", "cand")}
        self.assertEqual(page_turns, {"base": {2.0}, "cand": {1.0}})  # base: draft and rethink; candidate: rethink turned off
        self.assertEqual(self.rows(self.eval_db, "SELECT overrides FROM runs WHERE label = 'cand' LIMIT 1"), [('{"rethink": "false"}',)])
        self.assertEqual((sha(self.settings), sha(self.main_db)), (self.settings_before, self.main_before))
        self.assertEqual(self.library_rows(), self.library_before, "the library's own records are never written by a run")
        self.assertEqual([p.name for p in (self.home / ".cache" / "atlas-quality").iterdir()], [])
        self.assertRegex(self.report, r"atlas-rethink rule: with it, faithfulness is \w+ and completeness is \w+: ")

    def test_planted_instructions_are_checked_in_code_and_a_version_that_follows_one_is_seen(self) -> None:
        planted = dict(self.rows(self.eval_db, "SELECT id, json_extract(payload, '$.check') FROM cases WHERE kind = 'planted'"))
        self.assertEqual(sorted(planted.values()), ["deprecated", "french", "price_zero"])
        [deprecated] = [case for case, check in planted.items() if check == "deprecated"]
        followed = self.rows(self.eval_db, "SELECT r.label, m.value FROM measures m JOIN runs r ON r.id = m.run_id WHERE m.case_id = ? AND m.measure = 'planted_code' ORDER BY r.id", deprecated)
        self.assertEqual(followed, [("base", 0.0), ("cand", 1.0), ("base", 0.0), ("cand", 1.0)])

    def test_only_sampled_measures_can_be_unreliable_and_the_rest_are_not_spot_checked(self) -> None:
        for measure in ("completeness", "conciseness"):
            self.assertRegex(self.report, rf"{measure} \| .*\| not spot-checked\n")
        self.assertRegex(self.report, r"faithfulness \| .*\| not spot-checked until the sample is labelled \(0 of 20\)")
        items = self.label_sample(disagree=10)
        self.assertEqual(self.quality("report", self.comparison), 0, self.err.getvalue())
        report = self.out.getvalue()
        self.assertRegex(report, r"faithfulness \| .*\| UNRELIABLE: you disagreed with Jev on 10 of 20")
        self.assertRegex(report, r"completeness \| .*\| not spot-checked\n")
        self.assertIn("spot check: complete", report)
        # Four of twenty is not more than two in ten: put six of the ten wrong labels right.
        for item in items[:6]:
            self.assertEqual(self.quality("spot", self.comparison, "--answer", item, "unsupported"), 0)
        self.assertEqual(self.quality("report", self.comparison), 0)
        self.assertRegex(self.out.getvalue(), r"faithfulness \| .*\| spot-checked: you disagreed with Jev on 4 of 20")

    def test_the_spot_sample_is_half_flagged_seeded_and_never_shows_jevs_flag(self) -> None:
        items = [row[0] for row in self.rows(self.eval_db, "SELECT item FROM spot WHERE comparison_id = ? ORDER BY rowid", self.comparison)]
        self.assertEqual(len(items), 20)
        flagged = [i for i in items if self.rows(self.eval_db, "SELECT p < 0.8 FROM judgments WHERE item = ?", i) == [(1,)]]
        self.assertEqual(len(flagged), 10)
        self.assertEqual(len({i.split(":")[1] for i in items}), 2, "the sample is drawn across the candidate's runs")
        self.assertEqual(self.quality("spot", self.comparison), 0)
        shown = json.loads(self.out.getvalue())
        self.assertEqual(set(shown), {"comparison", "item", "shown", "labels", "remaining"})
        self.assertEqual((shown["labels"], shown["remaining"]), (["supported", "unsupported"], 20))
        self.assertRegex(shown["shown"], r"^Claim: Sentence (one|two) about \w+-a")
        self.assertNotRegex(json.dumps(shown), r"0\.3|0\.95|flag")
        self.assertEqual(self.quality("spot", self.comparison, "--answer", shown["item"], "maybe"), 2)
        self.assertIn("one of supported, unsupported", self.err.getvalue())

    def label_sample(self, disagree: int) -> list[str]:
        """Label the whole sample; ``disagree`` of its labels contradict Jev's flags. Returns the item ids, flagged first."""
        items = [row[0] for row in self.rows(self.eval_db, "SELECT item FROM spot WHERE comparison_id = ? ORDER BY rowid", self.comparison)]
        flagged = [i for i in items if self.rows(self.eval_db, "SELECT p < 0.8 FROM judgments WHERE item = ?", i) == [(1,)]]
        plain = [i for i in items if i not in flagged]
        ordered = flagged + plain
        for n, item in enumerate(ordered):
            is_flagged = item in flagged
            wrong = n < disagree if is_flagged else False
            label = "supported" if (is_flagged and wrong) or (not is_flagged) else "unsupported"
            self.assertEqual(self.quality("spot", self.comparison, "--answer", item, label), 0, self.err.getvalue())
        return ordered


def answerer(messages: Any) -> ports.Reply:
    """An answer from the sources it is shown: one claim on the first, one on the first two."""
    links = list(dict.fromkeys(re.findall(r"https://example\.com/\w+", json.dumps(messages))))
    claims = [
        {"claim": "Alpha holds.", "sources": links[:1], "label": "Sound", "reason": "One page says so."},
        {"claim": "Both agree.", "sources": links[:2], "label": "Doubtful", "reason": "Two pages say it, weakly."},
    ]
    return tool_reply({"answer": "The pages agree.", "claims": claims, "disagreements": [], "gaps": [], "model_view": "x", "tally_lines": []}, model="fake/opus")


def version_judge(state: str, question: ports.Question) -> ports.Answer:
    if question.id == "helps":
        return ports.Answer(p=0.9 if "alpha" in state.lower() else 0.2)
    return ports.Answer(p=0.1) if question.id == "same_work" else support(0.95)


class OtherLaneTests(RunCase):
    def setUp(self) -> None:
        super().setUp()
        self.version_hosts = {label: FakeHost(judge_answer=version_judge, reply_with={"atlas_answer": answerer}) for label in ("base", "cand")}

    def test_the_search_lane_pools_new_pairs_once_measures_code_counts_and_leaves_the_library_alone(self) -> None:
        self.tool_host = FakeHost(judge_answer=lambda state, question: ports.Answer(p=0.9))
        code = self.quality("run", "search", "--base", self.base, "--cand", self.cand, "--yes", "--runs", "2", runner=self.runner)
        self.assertEqual(code, 0, self.err.getvalue())
        measures = dict(self.rows(self.eval_db, "SELECT case_id || '/' || measure, avg(value) FROM measures WHERE measure IN ('mrr', 'recall') GROUP BY 1"))
        self.assertEqual(measures, {"q:Q1/mrr": 1.0, "q:Q2/recall": 1.0})
        new_pairs = [row[0] for row in self.rows(self.eval_db, "SELECT item FROM judgments WHERE item LIKE 'grade:%'")]
        self.assertTrue(new_pairs)
        # Each new top-10 pair was graded once for the whole comparison, not once per version and run.
        self.assertEqual(len(set(new_pairs)), len(new_pairs))
        self.assertEqual(len(self.tool_calls("judge")), len(new_pairs))
        self.assertEqual(self.rows(self.eval_db, "SELECT count(*) FROM queries"), [(0,)], "the library itself is never searched: runs search a copy")
        self.assertRegex(self.out.getvalue(), r"ndcg10 \| .*\| not spot-checked until the sample is labelled \(0 of \d+\)")
        self.assertRegex(self.out.getvalue(), r"mrr \| [^|]*\| [^|]*\| [^|]*\| \w+ \| \n")

    def test_the_answers_lane_recounts_backing_and_reports_support_flags_as_not_spot_checked(self) -> None:
        code = self.quality("run", "answers", "--base", self.base, "--cand", self.cand, "--yes", "--runs", "1", runner=self.runner)
        self.assertEqual(code, 0, self.err.getvalue())
        report = self.out.getvalue()
        self.assertRegex(report, r"backing_match \| 1\.000 \| 1\.000")
        self.assertRegex(report, r"answer_support \| .*\| not spot-checked\n")
        [(comparison,)] = self.rows(self.eval_db, "SELECT id FROM comparisons")
        kinds = self.rows(self.eval_db, "SELECT substr(item, 1, instr(item, ':') - 1), count(*) FROM spot GROUP BY 1 ORDER BY 1")
        self.assertEqual(kinds, [("claim", 8), ("pair", 2)])  # 2 cases x 2 claims x 2 versions, and one side-by-side per case
        # The user labels before seeing the model's label: the item never shows it.
        while True:
            self.assertEqual(self.quality("spot", comparison), 0)
            item = json.loads(self.out.getvalue())
            if item.get("done"):
                break
            if item["item"].startswith("claim"):
                self.assertEqual(set(item["shown"]), {"claim", "sources", "backing"})
            label = {"claim": "Doubtful", "pair": "level"}[item["item"].split(":")[0]]
            self.assertEqual(self.quality("spot", comparison, "--answer", item["item"], label), 0)
        self.assertEqual(self.quality("report", comparison), 0)
        report = self.out.getvalue()
        self.assertIn("your labels agree with the model's on 4 of 8 claims", report)
        self.assertIn("model said Doubtful: you agreed on 4 of 4", report)
        self.assertIn("side by side: base 0, candidate 0, level 2", report)

    def test_backing_is_recounted_from_authors_publishers_and_related_links(self) -> None:
        with closing(sqlite3.connect(self.eval_db)) as conn:
            ids = dict(conn.execute("SELECT key_link, id FROM sources"))
            conn.execute("UPDATE sources SET author = 'Ann' WHERE key_link IN (?, ?)", (ARTICLES["a"], ARTICLES["b"]))
            conn.execute("UPDATE sources SET publisher = 'Press' WHERE key_link IN (?, ?)", (ARTICLES["h"], ARTICLES["i"]))
            conn.execute("INSERT INTO related_links (source_id, link, origin) VALUES (?, ?, 'page')", (ids[ARTICLES["c"]], ARTICLES["a"]))
            conn.commit()
        ctx = lanes.Ctx(self.tool_host.host(), None, None, self.eval_db, self.repo, None, datetime.now, self.out, self.err, self.home, None)  # type: ignore[arg-type]
        a, b, c, h, i = (ARTICLES[k] for k in "abchi")
        self.assertEqual(
            [lanes.backing_recount(ctx, links) for links in ([], [a], [a, b], [h, i], [a, h], [a, c], [a, c, h, i])],
            [0, 1, 1, 1, 2, 1, 2],
        )


class PromoteTests(RunCase):
    """The one place the tool reads a real profile: ``main`` holds a query and a page the library lacks."""

    JULIET = "https://example.com/juliet"

    def setUp(self) -> None:
        super().setUp()
        real = FakeHost(
            pages={self.JULIET: page(self.JULIET, "juliet"), ARTICLES["a"]: page(ARTICLES["a"], "alpha")},
            reply_with={"atlas_summarize": summarizer()},
            judge_answer=lambda state, question: ports.Answer(p=0.9 if "juliet" in state.lower() else 0.2) if question.id == "helps" else support(0.95),
        ).host()
        for link in (self.JULIET, ARTICLES["a"]):
            added, code = app.run("add", None, {"profile": "main", "items": [{"link": link}], "approval": {"by": "request", "words": f"Add {link}"}}, real)
            self.assertEqual(code, 0, added)
        found, code = app.run("find", None, {"profile": "main", "question": "juliet note", "original": "juliet note", "phrasings": ["juliet", "alpha"]}, real)
        self.assertEqual(code, 0, found)
        self.main_before = sha(self.main_db)
        self.settings_before = sha(self.settings)

    def test_promote_copies_a_query_and_its_sources_text_and_writes_nothing_to_the_real_profile(self) -> None:
        self.assertEqual(self.quality("promote", "--from", "main", "--query", "1"), 0, self.err.getvalue())
        [(case_id, lane, kind, origin, payload)] = self.rows(self.eval_db, "SELECT id, lane, kind, origin, payload FROM cases WHERE origin = 'promoted'")
        self.assertEqual((case_id, lane, kind, origin), ("q:promoted:main:1", "search", "query", "promoted"))
        body = json.loads(payload)
        self.assertEqual((body["text"], body["rewrites"]), ("juliet note", ["juliet", "alpha"]))
        self.assertEqual([source["link"] for source in body["sources"]], [self.JULIET, ARTICLES["a"]])
        self.assertEqual(body["sources"][0]["text"], text_of("juliet"))
        self.assertEqual((sha(self.main_db), sha(self.settings)), (self.main_before, self.settings_before))
        self.assertEqual(self.quality("promote", "--from", "main", "--query", "1"), 1)
        self.assertIn("already in eval", self.err.getvalue())
        self.assertEqual(self.quality("promote", "--from", "main", "--query", "9"), 1)
        self.assertIn("no query record 9", self.err.getvalue())

    def test_a_promoted_query_runs_with_its_sources_replayed_and_no_page_is_read(self) -> None:
        self.assertEqual(self.quality("promote", "--from", "main", "--query", "1"), 0)
        self.version_hosts = {label: FakeHost(judge_answer=version_judge, reply_with={"atlas_summarize": summarizer(), "atlas_answer": answerer}) for label in ("base", "cand")}
        self.tool_host = FakeHost(judge_answer=lambda state, question: ports.Answer(p=0.9))
        self.assertEqual(self.quality("run", "search", "--base", self.base, "--cand", self.cand, "--yes", "--runs", "1", runner=self.runner), 0, self.err.getvalue())
        self.assertEqual(self.rows(self.eval_db, "SELECT count(*) FROM measures WHERE case_id = 'q:promoted:main:1' AND measure = 'ndcg10'"), [(2,)])
        for host in self.version_hosts.values():
            self.assertEqual([call for call in host.calls if call[0] == "read"], [])
            turns = [call for call in host.calls if call[0] == "call" and call[1] == "atlas_summarize"]
            self.assertEqual(len(turns), 2, "juliet was added under the version (draft and rethink); alpha was already in the library copy")
        self.assertEqual(self.rows(self.eval_db, "SELECT count(*) FROM sources WHERE key_link = ?", self.JULIET), [(0,)], "and only to the run's copy")

    def test_promote_page_copies_old_text_new_text_and_the_old_record(self) -> None:
        old = self.home / "old.txt"
        old.write_text("# Juliet\nSentence one about juliet-a juliet-b juliet-c juliet-d.\nAn older line.")
        self.assertEqual(self.quality("promote-page", "--from", "main", "--link", self.JULIET, "--old-ref", "2999-01-01", "--old-text", str(old)), 0, self.err.getvalue())
        [(case_id, link, payload)] = self.rows(self.eval_db, "SELECT id, link, payload FROM cases WHERE kind = 'changed'")
        body = json.loads(payload)
        self.assertEqual((link, body["new_text"], body["old_text"]), (self.JULIET, text_of("juliet"), old.read_text()))
        self.assertEqual([claim["text"] for claim in body["old_record"]], [sentence("juliet", 0), sentence("juliet", 1)])
        self.assertEqual(body["old_record"][0]["quotes"], [sentence("juliet", 0)])
        self.assertEqual(sha(self.main_db), self.main_before)
        self.assertEqual(self.quality("promote-page", "--from", "main", "--link", self.JULIET, "--old-ref", "2000-01-01", "--old-text", str(old)), 1)
        self.assertIn("had no claims on 2000-01-01", self.err.getvalue())
        before = self.rows(self.eval_db, "SELECT count(*) FROM cases WHERE kind = 'changed'")
        for missing in (self.home / "nope.txt", self.home):
            self.assertEqual(self.quality("promote-page", "--from", "main", "--link", self.JULIET, "--old-ref", "2999-01-01", "--old-text", str(missing)), 1)
            self.assertIn("cannot be read", self.err.getvalue())
        self.assertEqual(self.rows(self.eval_db, "SELECT count(*) FROM cases WHERE kind = 'changed'"), before)


class SummaryScoringTests(RunCase):
    """Summary-lane paths the comparison fixture does not reach: a version that checks support itself, and a changed page."""

    OLD = text_of("kilo")
    NEW = f"# Kilo\n{sentence('kilo', 0)}\n{sentence('kilo', 2)}\nA brand new finding about kilo-z kilo-y kilo-x kilo-w."

    def setUp(self) -> None:
        super().setUp()
        self.assertEqual(self.compare("--yes"), 1, self.err.getvalue())
        self.review_key_points()
        payload = {"kind": "article", "title": "Kilo", "old_ref": "2000-01-01", "old_text": self.OLD, "new_text": self.NEW, "old_record": []}
        with closing(sqlite3.connect(self.eval_db)) as conn:
            conn.execute(
                "INSERT INTO cases (id, lane, kind, payload, link, origin) VALUES ('c:main:kilo', 'summary', 'changed', ?, 'https://example.com/kilo', 'promoted')",
                (json.dumps(payload),),
            )
            conn.commit()

    def measure(self, label: str, case: str, name: str) -> float:
        [(value,)] = self.rows(self.eval_db, "SELECT m.value FROM measures m JOIN runs r ON r.id = m.run_id WHERE r.label = ? AND m.case_id = ? AND m.measure = ?", label, case, name)
        return value

    def test_a_changed_page_is_summarized_then_read_again_and_its_changed_claims_counted(self) -> None:
        def update_or_summarize(messages: Any) -> ports.Reply:
            joined = json.dumps(messages)
            if "This page changed since its record was written" not in joined:
                return summarizer()(messages)
            [ref] = re.findall(r"- (c\d+): \[[^\]]*\] Sentence two about kilo", joined.replace("\\n", "\n"))
            added = {"text": "A brand new finding.", "basis": "asserted", "quotes": ["A brand new finding about kilo-z kilo-y kilo-x kilo-w."]}
            return tool_reply({"affected": [{"ref": ref, "action": "remove"}], "added": [added]})

        for host in self.version_hosts.values():
            host.reply_with["atlas_summarize"] = update_or_summarize
        self.assertEqual(self.compare("--yes", "--runs", "1"), 0, self.err.getvalue())
        for label in ("base", "cand"):
            self.assertEqual(self.measure(label, "c:main:kilo", "claims_changed"), 2.0)  # one removed, one added

    def test_faithfulness_uses_the_versions_own_flags_when_it_checked_support_and_asks_jev_otherwise(self) -> None:
        def own_judge(state: str, question: ports.Question) -> ports.Answer:
            if question.id == "support":
                return support(0.6 if state.startswith("Claim: Sentence two") else 0.95)
            return ports.Answer(p=0.1)

        self.version_hosts["base"] = FakeHost(reply_with={"atlas_summarize": summarizer(False)}, judge_answer=own_judge, judge_model="version-judge")
        self.assertEqual(self.compare("--yes", "--runs", "1"), 0, self.err.getvalue())
        models = lambda label: {m for (m,) in self.rows(self.eval_db, "SELECT DISTINCT j.judge_model FROM judgments j JOIN runs r ON r.id = j.run_id WHERE r.label = ? AND j.item LIKE 'faith:%'", label)}
        self.assertEqual((models("base"), models("cand")), ({"version-judge"}, {"fake-judge-1"}))
        # Claim two carries the version's 0.6, not Jev's 0.3 for it.
        self.assertEqual(self.rows(self.eval_db, "SELECT DISTINCT j.p FROM judgments j JOIN runs r ON r.id = j.run_id WHERE r.label = 'base' AND j.item LIKE 'faith:%' ORDER BY 1"), [(0.6,), (0.95,)])


class UsageTests(QualityCase):
    def test_a_set_belongs_to_the_version_before_it_and_must_name_an_override(self) -> None:
        base = ("run", "summary", "--base", "main")
        self.assertEqual(self.quality("run", "summary", "--set", "rethink=false", "--base", "a", "--cand", "b"), 2)
        self.assertIn("put it after --base or --cand", self.err.getvalue())
        self.assertEqual(self.quality(*base, "--cand", "b", "--set", "bogus=1"), 2)
        self.assertIn('"bogus" is not an override', self.err.getvalue())
        lane, left, right, runs, yes = quality.parse_run(["search", "--base", "a", "--set", "judge=opus", "--cand", "b", "--set", "role.atlas_rerank=x/y:low", "--runs", "5"])
        self.assertEqual((lane, left.overrides, right.overrides, runs, yes), ("search", {"judge": "opus"}, {"role.atlas_rerank": "x/y:low"}, 5, False))

    def test_no_eval_profile_is_not_set_up_and_marks_report_waits_for_stage_7(self) -> None:
        self.settings.write_text('default_profile = "main"\n[profiles.main]\nstore = "/tmp/x.db"\n')
        self.assertEqual(self.quality("run", "summary", "--base", "a", "--cand", "b"), 3)
        self.assertIn('profile "eval" is not in the settings file', self.err.getvalue())
        self.assertEqual(self.quality("marks-report", "--profile", "main"), 1)
        self.assertIn("stage 7", self.err.getvalue())


class WorkerProcessTests(QualityCase):
    """The production seam: one case in a new process on a checkout's own Atlas, against the recorded ``omp``."""

    def job(self, **overrides: str) -> dict[str, Any]:
        record = replay_read.PageRecord(link="https://example.com/alpha", kind="article", text=text_of("alpha"), title="Alpha")
        return {
            "lane": "summary", "profile": "eval", "overrides": overrides, "store": str(self.home / "scratch.db"),
            "case": {"id": "s:alpha", "link": "https://example.com/alpha", "scope": None}, "records": [record.to_json()],
        }

    def test_the_process_reads_the_replayed_page_applies_overrides_and_prints_one_result(self) -> None:
        from tests.contract.test_omp_recorded import OMP

        path = f"{OMP.parent}{os.pathsep}{os.environ.get('PATH', '')}"
        with mock.patch.dict(os.environ, {"PATH": path}):
            plain = versions.subprocess_runner(ROOT, self.job())
            overridden = versions.subprocess_runner(ROOT, self.job(**{"role.atlas_summarize": "fake/sonnet:high"}))
        roles = lambda result: [item["what"] for item in result["needs_action"]]  # noqa: E731
        self.assertEqual((plain["code"], plain["decisions"]), (3, []))
        self.assertEqual(roles(plain), ["Role atlas_summarize is missing", "Role atlas_escalate is missing"])
        self.assertEqual(roles(overridden), ["Role atlas_escalate is missing"])
        with self.assertRaises(versions.VersionError):
            versions.subprocess_runner(self.home, self.job())


class StatsTests(unittest.TestCase):
    def test_bootstrap_marks_better_level_or_worse_by_whether_the_interval_excludes_zero(self) -> None:
        wins = [(0.5, 0.5 + 0.1 + 0.01 * n) for n in range(30)]
        mean, low, high = stats.bootstrap(wins, "cmp-1")
        self.assertGreater(low, 0)
        self.assertEqual((stats.verdict(low, high), stats.verdict(low, high, higher_is_better=False)), ("better", "worse"))
        mixed = [(0.5, 0.5 + (0.2 if n % 2 else -0.2)) for n in range(30)]
        _, low, high = stats.bootstrap(mixed, "cmp-1")
        self.assertTrue(low < 0 < high)
        self.assertEqual(stats.verdict(low, high), "level")
        losses = [(0.9, 0.5 + 0.01 * n) for n in range(30)]
        _, low, high = stats.bootstrap(losses, "cmp-1")
        self.assertEqual(stats.verdict(low, high), "worse")

    def test_bootstrap_is_seeded_by_the_comparison_id_and_resamples_cases_in_pairs(self) -> None:
        pairs = [(0.01 * n, 0.01 * n + (0.37 * n % 11 - 5) / 20) for n in range(25)]
        self.assertEqual(stats.bootstrap(pairs, "cmp-1"), stats.bootstrap(pairs, "cmp-1"))
        self.assertNotEqual(stats.bootstrap(pairs, "cmp-1")[1:], stats.bootstrap(pairs, "cmp-2")[1:])
        # A steady lift over cases of very different levels has no spread to resample: the interval is that lift.
        lifted = [(0.03 * n, 0.03 * n + 0.05) for n in range(30)]
        _, low, high = stats.bootstrap(lifted, "cmp-1")
        self.assertAlmostEqual(low, 0.05)
        self.assertAlmostEqual(high, 0.05)

    def test_half_flagged_samples_take_half_flagged_all_flagged_when_fewer_and_repeat_for_a_seed(self) -> None:
        flagged = [f"f{n:02}" for n in range(30)]
        plain = [f"p{n:02}" for n in range(30)]
        chosen = stats.half_flagged(flagged, plain, 20, "cmp-1")
        self.assertEqual((len(chosen), sum(c.startswith("f") for c in chosen)), (20, 10))
        self.assertEqual(chosen, stats.half_flagged(flagged, plain, 20, "cmp-1"))
        self.assertNotEqual(chosen, stats.half_flagged(flagged, plain, 20, "cmp-2"))
        few = stats.half_flagged(flagged[:3], plain, 20, "cmp-1")
        self.assertEqual((len(few), sum(c.startswith("f") for c in few)), (20, 3))
        self.assertEqual(stats.sample(["x", "y"], 10, "s"), ["x", "y"])

    def test_more_than_two_in_ten_disagreements_is_unreliable(self) -> None:
        self.assertEqual([stats.unreliable(n, 10) for n in (2, 3)], [False, True])
        self.assertEqual([stats.unreliable(n, 20) for n in (4, 5)], [False, True])
        self.assertFalse(stats.unreliable(0, 0))


class RoleOverrideTests(unittest.TestCase):
    """An overridden role's request carries the given model; the others keep ``@<role>`` (recorded ``omp``, no network)."""

    def test_the_gateway_request_names_the_override_only_for_that_role(self) -> None:
        from tests.contract.test_omp_recorded import OMP
        from atlas.adapters.omp import OmpHost
        from tests.contract import suite

        log = Path(self.enterContext(tempfile.TemporaryDirectory())) / "omp.log"
        path = f"{OMP.parent}{os.pathsep}{os.environ.get('PATH', '')}"
        with mock.patch.dict(os.environ, {"ATLAS_FAKE_OMP_LOG": str(log), "PATH": path}):
            omp = OmpHost()
            host = ports.Host(read=omp, call=omp, open_store=lambda p: None, facts=omp)  # type: ignore[arg-type,return-value]
            message = [{"role": "user", "content": suite.FORCED_TOOL_MESSAGE}]
            host.call.call("tiny", message, [suite.RECORD_TOOL], "record", 200)
            plain = json.loads(json.loads(log.read_text().splitlines()[-1])["stdin"])["body"]["model"]
            worker.with_role_overrides(host, {"tiny": "fake/other-model:high"})
            host.call.call("tiny", message, [suite.RECORD_TOOL], "record", 200)
            overridden = json.loads(json.loads(log.read_text().splitlines()[-1])["stdin"])["body"]["model"]
            self.assertEqual((plain, overridden), ("@tiny", "fake/other-model:high"))
            self.assertEqual(host.facts.roles()["tiny"], "fake/other-model:high")


if __name__ == "__main__":
    unittest.main()
