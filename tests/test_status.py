"""``status`` through ``app.run`` with the fake host and a temporary ``HOME``."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path
from unittest import mock

from tests.fakes.fake_host import ALL_ROLES, FakeHost

from atlas import ports  # noqa: E402  (fake_host puts the package on sys.path)
from atlas.core import app, spend  # noqa: E402
from atlas.store import CallRecord  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
READY_NEXT = [{"label": "nothing to fix; Atlas is ready", "then": {"stop": True}}]
SETUP_NEXT = {"label": "run `atlas-init`", "then": {"skill": "atlas-init"}}
NOW = datetime(2026, 11, 15, 12, 0).astimezone()
CHANGE_KINDS = ("add", "add_redo", "add_reread", "inbox_add", "note", "archive", "restore", "follow", "unfollow", "plan_start")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()


# The version a checkout reports, and the host version its nearest v2 tag was released with.
DESCRIBED = _git("describe", "--tags", "--match", "v2.*")
TAG = _git("describe", "--tags", "--abbrev=0", "--match", "v2.*")
RELEASED_WITH = _git("tag", "-l", TAG, f"--format=%(contents:trailers:key={ports.HOST_VERSION_TRAILER},valueonly)")


class StatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        os.environ.pop("ATLAS_PROFILE", None)
        self.enterContext(mock.patch.object(spend, "local_now", return_value=NOW))
        self.settings = self.home / ".config" / "atlas" / "config.toml"

    def configure(self, text: str = '[profiles.smoke]\nstore = "~/data/smoke.db"\njudge = "jev"\n') -> None:
        self.settings.parent.mkdir(parents=True, exist_ok=True)
        self.settings.write_text('default_profile = "smoke"\n' + text)

    def status(self, fake: FakeHost, mode: str | None = None, body: dict | None = None) -> tuple[dict, int]:
        answer, code = app.run("status", mode, body or {}, fake.host())
        self.assertEqual(answer["ok"], code == 0)
        self.assertTrue(1 <= len(answer["next"]) <= 3)
        return answer, code

    def test_ready_profile_has_no_action_items_and_ends_with_next(self) -> None:
        self.configure()
        fake = FakeHost(version=RELEASED_WITH)
        answer, code = self.status(fake)
        self.assertEqual(code, 0)
        self.assertEqual(
            answer["result"],
            {"needs_action": [], "summary": f"Profile smoke: judge Jev, Atlas {DESCRIBED}", "detail": None},
        )
        self.assertEqual(answer["next"], READY_NEXT)
        self.assertTrue((self.home / "data" / "smoke.db").is_file())
        self.assertIn(("open_store", self.home / "data" / "smoke.db"), fake.calls)
        self.assertIn(("roles",), fake.calls)

    def test_detail_only_on_request(self) -> None:
        self.configure()
        answer, code = self.status(FakeHost(version=RELEASED_WITH), mode="detail")
        self.assertEqual(code, 0)
        store = self.home / "data" / "smoke.db"
        self.assertEqual(
            answer["result"]["detail"],
            {
                "profile": "smoke",
                "store": {"path": str(store), "size": store.stat().st_size},
                "roles": ALL_ROLES,
                "judge": "jev",
                "atlas_version": DESCRIBED,
                "host_version": RELEASED_WITH,
                "spend": {
                    "month": "2026-11",
                    "calls": 0,
                    "by_role": {},
                    "total": {"billed": 0.0, "estimated": 0.0, "unknown_calls": 0},
                },
                "windows": [],
                "confirm": dict.fromkeys(CHANGE_KINDS, "always"),
                "limits": {
                    "max_page_tokens": 150000,
                    "judge_concurrency": 8,
                    "rethink": True,
                    "near_copy": 0.9,
                    "reread_days": 30,
                    "reread_new_text": 0.05,
                    "cap_usd": None,
                    "cap_warn": 0.8,
                    "window_stop": 0.9,
                },
            },
        )

    def test_price_cap_and_window_items_follow_the_judge_items_and_detail_shows_spend(self) -> None:
        self.configure(
            '[profiles.smoke]\nstore = "~/data/smoke.db"\ncap_usd = 10.0\nwindow_stop = 0.9\n'
            '[profiles.smoke.confirm]\ninbox_add = "never"\n'
            '[prices."fake/opus"]\ninput = 4.0\noutput = 20.0\ncache_read = 0.2\ncache_write = 5.0\n'
        )
        fake = FakeHost(
            version="0.0.1-other",
            windows=[
                ports.Window("fake", "5h", 18_000, 0.93, datetime(2026, 11, 15, 14, 30).astimezone().isoformat()),
                ports.Window("fake", "7d", 604_800, 0.20, datetime(2026, 11, 20, 9, 0).astimezone().isoformat()),
            ],
        )
        with closing(fake.open_store(self.home / "data" / "smoke.db")) as store:
            for role, model, cost, kind in (
                ("judge", "fake-judge-1", 8.5, "billed"),
                ("judge", "fake-judge-2", None, "unknown"),
                ("atlas_summarize", "fake/sonnet", None, "unknown"),
                ("atlas_escalate", "fake/opus:medium", 0.25, "estimated"),
            ):
                store.add_call(CallRecord(spend.stamp(NOW), "add", role, model, None, 100, 10, 0, 0, cost, kind))
            store.add_call(CallRecord(spend.stamp(datetime(2026, 10, 1).astimezone()), "add", "judge", "j", None, 0, 0, 0, 0, 5.0, "billed"))
        answer, code = self.status(fake, mode="detail")
        self.assertEqual(code, 0)
        judge, price, cap, window, version = answer["result"]["needs_action"]
        self.assertEqual(judge["what"], "No judge is chosen for profile smoke")
        self.assertEqual(price["what"], "Model fake/sonnet has no price row, so the cost of its calls is unknown")
        self.assertEqual(price["fix"][0], '[prices."fake/sonnet"]')
        self.assertEqual(cap["what"], "This month's billed spend is $8.50, 85% of the $10.00 monthly cap")
        self.assertEqual(window["what"], "fake 5-hour window at 93%; resets 14:30")
        self.assertIn("0.0.1-other", version["what"])

        detail = answer["result"]["detail"]
        self.assertEqual(
            detail["spend"],
            {
                "month": "2026-11",
                "calls": 4,
                "by_role": {
                    "judge": {"calls": 2, "billed": 8.5, "estimated": 0.0, "unknown_calls": 1},
                    "atlas_summarize": {"calls": 1, "billed": 0.0, "estimated": 0.0, "unknown_calls": 1},
                    "atlas_escalate": {"calls": 1, "billed": 0.0, "estimated": 0.25, "unknown_calls": 0},
                },
                "total": {"billed": 8.5, "estimated": 0.25, "unknown_calls": 2},
            },
        )
        self.assertEqual([(w["window"], w["used_percent"]) for w in detail["windows"]], [("5-hour", 93), ("weekly", 20)])
        self.assertEqual(detail["confirm"]["inbox_add"], "never")
        self.assertEqual((detail["limits"]["cap_usd"], detail["limits"]["window_stop"]), (10.0, 0.9))

    def test_action_items_in_order_with_fixes_from_host_facts(self) -> None:
        self.configure()
        roles = {role: model for role, model in ALL_ROLES.items() if role not in ("atlas_answer", "atlas_escalate")}
        trouble = ports.SetupProblem("The judge key file is missing", ("Put the key in place.",), "/fake/key")
        answer, code = self.status(FakeHost(roles=roles, setup_problem=trouble, version="0.0.1-other"))
        self.assertEqual(code, 3)
        answer_role, escalate_role, judge, version = answer["result"]["needs_action"]
        for item, role in ((answer_role, "atlas_answer"), (escalate_role, "atlas_escalate")):
            self.assertEqual(
                item,
                {
                    "what": f"Role {role} is missing",
                    "fix": ["[roles]", f"{role} = anthropic/claude-opus-5-5:medium"],
                    "where": "/fake/host/settings.conf",
                },
            )
        self.assertEqual(judge, {"what": "The judge key file is missing", "fix": ["Put the key in place."], "where": "/fake/key"})
        self.assertIn("0.0.1-other", version["what"])
        self.assertIn(RELEASED_WITH, version["what"])
        self.assertEqual(answer["result"]["summary"], f"Profile smoke: judge Jev, Atlas {DESCRIBED}")
        self.assertIn(SETUP_NEXT, answer["next"])

    def test_store_newer_than_code_comes_first_and_fails(self) -> None:
        self.configure()
        store = self.home / "data" / "smoke.db"
        store.parent.mkdir()
        with closing(sqlite3.connect(store)) as db:
            db.execute("PRAGMA user_version = 1")
        roles = {role: model for role, model in ALL_ROLES.items() if role != "atlas_query"}
        answer, code = self.status(FakeHost(roles=roles, version=RELEASED_WITH))
        self.assertEqual(code, 1)
        newer, missing = answer["result"]["needs_action"]
        self.assertIn("newer than this Atlas", newer["what"])
        self.assertEqual(missing["what"], "Role atlas_query is missing")
        self.assertEqual(answer["problems"][0]["problem"], "store is newer than this Atlas; check out a newer tag")

    def test_role_fix_without_host_syntax_names_roles_and_models(self) -> None:
        self.configure()
        roles = {role: model for role, model in ALL_ROLES.items() if role != "atlas_summarize"}
        answer, code = self.status(FakeHost(roles=roles, role_fix_lines=False, version=RELEASED_WITH))
        self.assertEqual(code, 3)
        [item] = answer["result"]["needs_action"]
        self.assertEqual(item["fix"], ["Add the model role atlas_summarize with the model anthropic/claude-sonnet-5-5:high."])
        self.assertIsNone(item["where"])

    def test_judge_items_follow_the_profile_choice(self) -> None:
        trouble = ports.SetupProblem("The judge key file is missing", ("Put the key in place.",), "/fake/key")
        self.configure('[profiles.smoke]\nstore = "~/data/smoke.db"\njudge = "opus"\n')
        answer, code = self.status(FakeHost(setup_problem=trouble, version=RELEASED_WITH))
        self.assertEqual((code, answer["result"]["needs_action"]), (0, []))
        self.assertIn("judge Opus", answer["result"]["summary"])

        self.configure('[profiles.smoke]\nstore = "~/data/smoke.db"\n')
        answer, code = self.status(FakeHost(setup_problem=trouble, version=RELEASED_WITH))
        self.assertEqual(code, 0)
        [item] = answer["result"]["needs_action"]
        self.assertEqual(item["what"], "No judge is chosen for profile smoke")
        self.assertIn("judge not chosen", answer["result"]["summary"])
        self.assertIn(SETUP_NEXT, answer["next"])

    def test_without_host_facts_roles_host_version_and_windows_are_unknown(self) -> None:
        self.configure()
        answer, code = self.status(FakeHost(roles={}, version="0.0.1-other", facts=False), mode="detail")
        self.assertEqual((code, answer["result"]["needs_action"]), (0, []))
        self.assertIsNone(answer["result"]["detail"]["roles"])
        self.assertIsNone(answer["result"]["detail"]["host_version"])
        self.assertIsNone(answer["result"]["detail"]["windows"])

    def test_not_set_up_status_lists_the_missing_roles_without_store_or_judge(self) -> None:
        cases = {"no settings file": None, 'profile "other" is not in the settings file': "other"}
        roles = {role: model for role, model in ALL_ROLES.items() if role not in ("atlas_query", "atlas_answer")}
        for named, profile in cases.items():
            with self.subTest(named):
                if profile is not None:
                    self.configure()
                    os.environ["ATLAS_PROFILE"] = profile
                fake = FakeHost(roles=roles)
                answer, code = self.status(fake)
                self.assertEqual(code, 3)
                setup, *missing = answer["result"]["needs_action"]
                self.assertIn(named, setup["what"])
                self.assertEqual(
                    missing,
                    [
                        {
                            "what": f"Role {role} is missing",
                            "fix": ["[roles]", f"{role} = anthropic/claude-opus-5-5:medium"],
                            "where": "/fake/host/settings.conf",
                        }
                        for role in ("atlas_query", "atlas_answer")
                    ],
                )
                self.assertEqual(answer["next"], [SETUP_NEXT])
                self.assertEqual({call[0] for call in fake.calls}, {"roles", "role_fix"})
                self.assertFalse((self.home / "data").exists())

    def test_not_set_up_without_host_facts_lists_every_role_in_plain_words(self) -> None:
        answer, code = self.status(FakeHost(facts=False))
        self.assertEqual(code, 3)
        missing = answer["result"]["needs_action"][1:]
        self.assertEqual([item["what"] for item in missing], [f"Role {role} is missing" for role in ALL_ROLES])
        self.assertEqual(
            missing[0]["fix"], ["Add the model role atlas_summarize with the model anthropic/claude-sonnet-5-5:high."]
        )

    def test_other_commands_not_set_up_use_no_host(self) -> None:
        fake = FakeHost(roles={})
        answer, code = app.run("find", None, {}, fake.host())
        self.assertEqual(code, 3)
        [item] = answer["result"]["needs_action"]
        self.assertIn("not set up", item["what"])
        self.assertEqual(fake.calls, [])

    def test_host_facts_that_cannot_be_read_are_a_problem_not_a_crash(self) -> None:
        broken = ports.CallFailed(None, "omp config could not be read: boom")
        answer, code = self.status(FakeHost(facts_error=broken))
        self.assertEqual(code, 3)
        self.assertEqual(len(answer["result"]["needs_action"]), 1)
        [problem] = answer["problems"]
        self.assertEqual(problem["field"], "roles")
        self.assertIn("boom", problem["problem"])

        self.configure()
        answer, code = self.status(FakeHost(facts_error=broken), mode="detail")
        self.assertEqual(code, 1)
        self.assertEqual(answer["result"]["needs_action"], [])
        self.assertIn("boom", answer["problems"][0]["problem"])
        self.assertIsNone(answer["result"]["detail"]["roles"])
        self.assertEqual(
            answer["next"], [{"label": "fix the problems shown, then ask for status again", "then": {"stop": True}}]
        )

    def test_profile_from_body_else_environment_else_default(self) -> None:
        self.settings.parent.mkdir(parents=True)
        self.settings.write_text(
            'default_profile = "a"\n'
            + "".join(f'[profiles.{name}]\nstore = "~/data/{name}.db"\njudge = "opus"\n' for name in "abc")
        )
        os.environ["ATLAS_PROFILE"] = "b"
        steps = (({"profile": "c"}, "c"), ({}, "b"))
        for body, chosen in steps:
            with self.subTest(chosen=chosen):
                answer, _ = self.status(FakeHost(), body=body)
                self.assertTrue(answer["result"]["summary"].startswith(f"Profile {chosen}:"))
                self.assertTrue((self.home / "data" / f"{chosen}.db").is_file())
        del os.environ["ATLAS_PROFILE"]
        answer, _ = self.status(FakeHost())
        self.assertTrue(answer["result"]["summary"].startswith("Profile a:"))


if __name__ == "__main__":
    unittest.main()
