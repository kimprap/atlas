"""No key value reaches a reply, problem, row, log or argv (AC-2.5).

The key file holds a made-up ``OPENROUTER_API_KEY`` beside another made-up
secret line, as a shared env file would. ``cli.py status`` runs as a subprocess
on the real composition root with the recorded ``omp`` first on ``PATH``, so
every ``omp`` run's argv and stdin are logged; the Jev adapter runs in process
against a loopback server that echoes the key back in its errors.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.contract import suite
from tests.contract.replay import FIXTURES, Replay

from atlas import ports  # noqa: E402
from atlas.adapters.jev import JevJudge  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills" / "atlas-ask" / "cli.py"
KEY = "sk-or-v1-atlas-secret-test-7f3a9c"
OTHER = "other-service-secret-51be04"
KEY_FILE_TEXT = f"OTHER_SERVICE_TOKEN={OTHER}\nexport OPENROUTER_API_KEY='{KEY}'\n"
OK_REPLY = (FIXTURES / "jev" / "decisions_ok.json").read_bytes()


def _echo(status: int):
    """A server answer that puts the request's Authorization header into its error text."""

    def answer(method: str, path: str, body: bytes) -> tuple[int, bytes]:
        header = replay.requests[-1]["headers"].get("Authorization", "")
        return status, json.dumps({"error": {"message": f"bad credentials: {header}"}}).encode()

    replay = Replay(answer)
    return replay


class SecretsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        self.key_file = self.home / ".config" / "atlas" / "openrouter.env"
        self.key_file.parent.mkdir(parents=True)
        self.key_file.write_text(KEY_FILE_TEXT, encoding="utf-8")
        os.chmod(self.key_file, 0o600)

    def assertNoSecret(self, text: str, where: str) -> None:
        self.assertNotIn(KEY, text, f"the key reached {where}")
        self.assertNotIn(OTHER, text, f"another key file value reached {where}")

    def _status(self) -> tuple[subprocess.CompletedProcess[str], str]:
        (self.home / ".config" / "atlas" / "config.toml").write_text(
            'default_profile = "smoke"\n[profiles.smoke]\nstore = "~/atlas/smoke.db"\njudge = "jev"\n',
            encoding="utf-8",
        )
        log = self.home / "omp.log"
        env = {
            **os.environ,
            "HOME": str(self.home),
            "PATH": f"{FIXTURES / 'omp'}{os.pathsep}{os.environ.get('PATH', '')}",
            "ATLAS_FAKE_OMP_LOG": str(log),
        }
        env.pop("ATLAS_PROFILE", None)
        env.pop("ATLAS_HOST", None)
        proc = subprocess.run(
            [sys.executable, str(CLI), "status", "--detail"],
            input="{}",
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        return proc, log.read_text(encoding="utf-8")

    def test_status_shows_no_key_in_its_reply_log_argv_or_store(self) -> None:
        proc, omp_runs = self._status()
        reply = json.loads(proc.stdout)
        self.assertEqual(reply["result"]["detail"]["judge"], "jev")
        self.assertNotIn("Jev key", json.dumps(reply), "the key file was usable, so no key item is expected")
        self.assertIn('"argv": ["config", "get", "modelRoles", "--json"]', omp_runs)
        self.assertNoSecret(proc.stdout, "the reply")
        self.assertNoSecret(proc.stderr, "stderr")
        self.assertNoSecret(omp_runs, "an omp argv or stdin")
        store_files = list((self.home / "atlas").glob("smoke.db*"))
        self.assertTrue(store_files)
        for path in store_files:
            self.assertNoSecret(path.read_bytes().decode("latin-1"), path.name)

    def test_a_loose_key_file_is_a_status_item_without_the_key(self) -> None:
        os.chmod(self.key_file, 0o644)
        proc, _ = self._status()
        items = json.loads(proc.stdout)["result"]["needs_action"]
        self.assertIn("The Jev key file has mode 644, not 600", [item["what"] for item in items])
        self.assertNoSecret(proc.stdout, "the reply")

    def test_judge_errors_and_judgments_carry_no_key(self) -> None:
        for status in (401, 429):
            with self.subTest(status=status), _echo(status) as server:
                judge = JevJudge(endpoint=server.url, sleep=lambda s: None)
                with self.assertRaises(ports.JudgeFailed) as caught:
                    judge.judge(suite.JUDGE_STATE, [suite.CAUSE])
                self.assertEqual(server.requests[0]["headers"]["Authorization"], f"Bearer {KEY}")
                failure = caught.exception
                self.assertIn("bad credentials", failure.detail)
                for text in (str(failure), failure.detail, repr(failure.args)):
                    self.assertNoSecret(text, "a judge error")
        with Replay(lambda m, p, b: (200, OK_REPLY)) as server, mock.patch("subprocess.Popen") as spawn:
            got = JevJudge(endpoint=server.url).judge(suite.JUDGE_STATE, [suite.CAUSE])
        self.assertNoSecret(repr(got), "the judgments")
        self.assertNotIn(OTHER, json.dumps(server.requests[0]["headers"]))
        spawn.assert_not_called()

    def test_a_loose_key_file_is_never_sent(self) -> None:
        os.chmod(self.key_file, 0o640)
        with Replay(lambda m, p, b: (200, OK_REPLY)) as server:
            judge = JevJudge(endpoint=server.url)
            with self.assertRaises(ports.JudgeNotSetUp) as caught:
                judge.judge(suite.JUDGE_STATE, [suite.CAUSE])
        self.assertEqual(server.requests, [])
        self.assertNoSecret(str(caught.exception), "the setup error")
        self.assertNoSecret(repr(judge.setup_problem()), "the setup problem")


if __name__ == "__main__":
    unittest.main()
