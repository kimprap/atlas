"""``status`` through ``app.run`` with the fake host and a temporary ``HOME``."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from tests.fakes.fake_host import ALL_ROLES, FakeHost

from atlas import ports  # noqa: E402  (fake_host puts the package on sys.path)
from atlas.core import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
READY_NEXT = [{"label": "nothing to fix; Atlas is ready", "then": {"stop": True}}]
SETUP_NEXT = {"label": "run `atlas-init`", "then": {"skill": "atlas-init"}}


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
            },
        )

    def test_action_items_in_order_with_fixes_from_host_facts(self) -> None:
        self.configure()
        roles = {role: model for role, model in ALL_ROLES.items() if role not in ("atlas_answer", "atlas_escalate")}
        trouble = ports.SetupProblem("The judge key file is missing", ("Put the key in place.",), "/fake/key")
        answer, code = self.status(FakeHost(roles=roles, setup_problem=trouble, version="0.0.1-other"))
        self.assertEqual(code, 3)
        missing, judge, version = answer["result"]["needs_action"]
        self.assertEqual(
            missing,
            {
                "what": "Roles atlas_answer and atlas_escalate are missing",
                "fix": [
                    "[roles]",
                    "atlas_answer = anthropic/claude-opus-5-5:medium",
                    "atlas_escalate = anthropic/claude-opus-5-5:medium",
                ],
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

    def test_without_host_facts_roles_and_host_version_are_unknown(self) -> None:
        self.configure()
        answer, code = self.status(FakeHost(roles={}, version="0.0.1-other", facts=False), mode="detail")
        self.assertEqual((code, answer["result"]["needs_action"]), (0, []))
        self.assertIsNone(answer["result"]["detail"]["roles"])
        self.assertIsNone(answer["result"]["detail"]["host_version"])

    def test_not_set_up_ends_the_reply_before_any_port(self) -> None:
        cases = {"no settings file": None, 'profile "other" is not in the settings file': "other"}
        for named, profile in cases.items():
            with self.subTest(named):
                if profile is not None:
                    self.configure()
                    os.environ["ATLAS_PROFILE"] = profile
                fake = FakeHost()
                answer, code = app.run("status", None, {}, fake.host())
                self.assertEqual(code, 3)
                [item] = answer["result"]["needs_action"]
                self.assertIn(named, item["what"])
                self.assertEqual(fake.calls, [])
                self.assertFalse((self.home / "data").exists())

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
