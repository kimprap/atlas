"""release.py publish on temporary git repositories with a bare origin.

Each test has its own HOME (so the run's clone, lock and cache live there) and
stubs `omp`, `gh` and `notify` on PATH; nothing reaches the real HOME, GitHub
or this checkout's origin.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "tools" / "release" / "release.py"
OMP_STUB = """#!/bin/sh
case "$1" in
  --version) echo omp/18.18.2 ;;
  plugin) cat "$STUB_PLUGINS" ;;
  *) exit 1 ;;
esac
"""
LOGGING_STUB = f"""#!{sys.executable}
import json, os, sys
with open(os.environ["STUB_LOG"], "a") as log:
    log.write(json.dumps([os.path.basename(sys.argv[0]), *sys.argv[1:]]) + "\\n")
"""
PASSING_TEST = "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n"
FAILING_TEST = PASSING_TEST.replace("assertTrue(True)", "assertTrue(False)")


def executable(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class ReleaseRunTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        home, stubs = tmp / "home", tmp / "bin"
        self.stubs = stubs
        home.mkdir()
        stubs.mkdir()
        self.log = tmp / "stub.log"
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(
            HOME=str(home),
            PATH=f"{stubs}{os.pathsep}{os.environ['PATH']}",
            GIT_CONFIG_NOSYSTEM="1",
            GIT_AUTHOR_NAME="Test",
            GIT_AUTHOR_EMAIL="test@example.com",
            GIT_COMMITTER_NAME="Test",
            GIT_COMMITTER_EMAIL="test@example.com",
            STUB_LOG=str(self.log),
            STUB_PLUGINS=str(tmp / "plugins.json"),
        )
        executable(stubs / "omp", OMP_STUB)
        executable(stubs / "gh", LOGGING_STUB)
        executable(stubs / "notify", LOGGING_STUB)

        # dotagents linked from a dotfiles checkout, as on g10.
        dotfiles = self.dotfiles = tmp / "dotfiles"
        script = dotfiles / ".config/agents/skills/craft-skill/scripts/check_skills.py"
        script.parent.mkdir(parents=True)
        script.write_text("import sys\nsys.exit(0)\n")
        self.git(tmp, "init", "--quiet", "-b", "main", str(dotfiles))
        self.git(dotfiles, "add", "-A")
        self.git(dotfiles, "commit", "--quiet", "-m", "dotfiles")
        self.dotfiles_head = self.git(dotfiles, "rev-parse", "HEAD")
        link = tmp / "plugins/node_modules/dotagents"
        link.parent.mkdir(parents=True)
        link.symlink_to(dotfiles / ".config/agents")
        plugins = {"npm": [{"name": "dotagents", "version": "0.0.0", "path": str(link)}]}
        (tmp / "plugins.json").write_text(json.dumps(plugins))

        self.origin, self.work = tmp / "origin.git", tmp / "work"
        self.git(tmp, "init", "--quiet", "--bare", "-b", "main", str(self.origin))
        self.git(tmp, "clone", "--quiet", str(self.origin), str(self.work))

    def git(self, cwd: Path, *args: str) -> str:
        proc = subprocess.run(["git", *args], cwd=cwd, env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.strip()

    def commit(self, subject: str, files: dict[str, str], push: bool = True) -> str:
        for name, text in files.items():
            path = self.work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.git(self.work, "add", "-A")
        self.git(self.work, "commit", "--quiet", "-m", subject)
        if push:
            self.git(self.work, "push", "--quiet", "origin", "main")
        return self.git(self.work, "rev-parse", "HEAD")

    def first_commit(self) -> str:
        return self.commit(
            "add plugin",
            {
                "package.json": '{"name": "atlas", "version": "2.0.0", "omp": {}}\n',
                "skills/atlas-ask/SKILL.md": "skill\n",
                "README.md": "readme\n",
                "tests/__init__.py": "",
                "tests/test_ok.py": PASSING_TEST,
            },
        )

    def publish(self, sha: str) -> subprocess.CompletedProcess[str]:
        gone = subprocess.Popen(["true"])
        gone.wait()
        return subprocess.run(
            [sys.executable, str(RELEASE), "publish", "--after-push", str(gone.pid), sha],
            cwd=self.work,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=300,
        )

    def tags(self) -> dict[str, str]:
        """Origin's tags and the commits they point at."""
        out = self.git(self.origin, "for-each-ref", "--format=%(refname:short)", "refs/tags")
        return {name: self.git(self.origin, "rev-parse", f"{name}^{{commit}}") for name in out.splitlines()}

    def message(self, tag: str) -> str:
        return self.git(self.origin, "for-each-ref", "--format=%(contents)", f"refs/tags/{tag}")

    def stub_calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_first_release_ignores_v1_and_writes_both_trailers(self) -> None:
        first = self.first_commit()
        self.git(self.work, "tag", "v1", first)
        self.git(self.work, "push", "--quiet", "origin", "v1")
        docs = self.commit("update readme", {"README.md": "new readme\n"})

        run = self.publish(docs)

        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.tags(), {"v1": first, "v2.0.0": docs})
        message = self.message("v2.0.0")
        self.assertEqual(message.splitlines()[0], "atlas v2.0.0")
        self.assertIn("- add plugin\n- update readme\n", message)
        trailers = subprocess.run(
            ["git", "interpret-trailers", "--parse"], input=message, capture_output=True, text=True, env=self.env
        ).stdout
        self.assertEqual(trailers, f"Omp-Version: 18.18.2\nDotagents: {self.dotfiles_head}\n")
        calls = self.stub_calls()
        self.assertIn(["gh", "release", "create", "v2.0.0"], [call[:4] for call in calls])
        self.assertIn(["notify", "send"], [call[:2] for call in calls])

    def test_tags_only_shipped_changes_and_bumps_minor_for_a_migration(self) -> None:
        self.publish(self.first_commit())
        self.assertEqual(set(self.tags()), {"v2.0.0"})

        docs = self.commit("docs only", {"README.md": "more\n", "tools/x.py": "x = 1\n"})
        run = self.publish(docs)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(set(self.tags()), {"v2.0.0"})

        skill = self.commit("change skill", {"skills/atlas-ask/SKILL.md": "skill 2\n"})
        self.publish(skill)
        self.assertEqual(self.tags().get("v2.0.1"), skill)

        migration = self.commit(
            "add migration", {"skills/atlas-ask/atlas/store/migrations/0001_baseline.sql": "create table t (id);\n"}
        )
        self.publish(migration)
        self.assertEqual(self.tags().get("v2.1.0"), migration)
        self.assertEqual(set(self.tags()), {"v2.0.0", "v2.0.1", "v2.1.0"})

    def test_change_left_untagged_by_failed_checks_is_tagged_by_the_next_push(self) -> None:
        self.publish(self.first_commit())
        broken = self.commit(
            "change skill, break test", {"skills/atlas-ask/SKILL.md": "skill 2\n", "tests/test_ok.py": FAILING_TEST}
        )

        run = self.publish(broken)
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertIn("check tests: fail", run.stdout)
        self.assertEqual(set(self.tags()), {"v2.0.0"})

        fixed = self.commit("fix test", {"tests/test_ok.py": PASSING_TEST})
        run = self.publish(fixed)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.tags().get("v2.0.1"), fixed)
        self.assertIn("- change skill, break test\n- fix test\n", self.message("v2.0.1"))

    def test_commit_not_on_origin_main_is_not_tagged(self) -> None:
        self.first_commit()
        local = self.commit("not pushed", {"skills/atlas-ask/SKILL.md": "local\n"}, push=False)

        run = self.publish(local)

        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("skipped", run.stdout)
        self.assertEqual(self.tags(), {})

    def test_notify_falls_back_to_the_dotfiles_checkout(self) -> None:
        (self.stubs / "notify").unlink()
        self.assertIsNone(shutil.which("notify", path=self.env["PATH"]))
        fallback = self.dotfiles / ".config/scripts/notify"
        fallback.parent.mkdir(parents=True)
        executable(fallback, LOGGING_STUB)

        run = self.publish(self.first_commit())

        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        sends = [call for call in self.stub_calls() if call[:2] == ["notify", "send"]]
        self.assertEqual(len(sends), 1)
        self.assertIn("atlas v2.0.0 released", sends[0])


if __name__ == "__main__":
    unittest.main()
