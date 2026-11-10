"""Versions of Atlas to compare: a git ref plus setting overrides, each run from its own worktree (spec 4.15).

``checkout`` makes a ``git worktree`` of a ref under ``~/.cache/atlas-quality/`` and removes it
afterwards. ``subprocess_runner`` runs one case of the worktree's Atlas in a fresh process
(``worker.py`` with the worktree's ``skills/atlas-ask`` first on ``sys.path``), so two versions never
share a module namespace.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.quality import _path  # noqa: F401

WORKER = Path(__file__).resolve().with_name("worker.py")
# One case may run a summary with its rethink, repair and escalation turns.
CASE_TIMEOUT_S = 1800


class VersionError(Exception):
    """A ref that cannot be checked out, or a case process that failed; the message says why."""


@dataclass(frozen=True)
class Version:
    label: str  # base or cand
    ref: str
    overrides: Mapping[str, str] = field(default_factory=dict)


def cache_root() -> Path:
    return Path.home() / ".cache" / "atlas-quality"


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise VersionError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.returncode}")
    return proc.stdout.strip()


def resolve(repo: Path, ref: str) -> str:
    """The commit ``ref`` names, as the run records it."""
    return _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")


@contextmanager
def checkout(repo: Path, ref: str, name: str) -> Iterator[Path]:
    """A detached worktree of ``ref`` named ``name`` under the cache folder, removed when the block ends."""
    path = cache_root() / name
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", "--detach", "--force", str(path), ref)
    try:
        yield path
    finally:
        _git(repo, "worktree", "remove", "--force", str(path))


def subprocess_runner(worktree: Path, job: Mapping[str, Any]) -> dict[str, Any]:
    """Run ``job`` on the Atlas of ``worktree`` in a new process and return its result."""
    atlas = worktree / "skills" / "atlas-ask"
    if not atlas.is_dir():
        raise VersionError(f"{worktree} holds no skills/atlas-ask: the ref has no Atlas v2")
    proc = subprocess.run(
        [sys.executable, str(WORKER), str(atlas)],
        input=json.dumps(job),
        capture_output=True,
        text=True,
        timeout=CASE_TIMEOUT_S,
    )
    last = proc.stdout.strip().splitlines()[-1:] or [""]
    if proc.returncode != 0 or not last[0].startswith("{"):
        tail = proc.stderr.strip().splitlines()[-3:]
        raise VersionError(f"the case process failed (exit {proc.returncode}): {' | '.join(tail)}")
    return json.loads(last[0])
