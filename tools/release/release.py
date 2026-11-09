#!/usr/bin/env python3
"""Atlas release tool (repo-only; never shipped).

Commands, run inside an Atlas checkout:

  setup                 set this repository's core.hooksPath to .githooks
                        (idempotent; run once after cloning)
  shipped-paths <ref>   print the shipped files at <ref>: package.json,
                        skills/ and rules/
  publish --after-push <pid> [--background] <sha>
                        once the git push in <pid> has exited, tag <sha> as
                        the next v2 release when origin main is <sha>; with
                        --background, run detached (the pre-push hook's form)

A release run works in its own clone, ~/.cache/atlas-release/clone, so it
never writes to the checkout; one run at a time holds release.lock there,
passing checks are remembered in check-cache, and a background run appends to
release.log. It runs at nice 19. Every run on a landed push first runs both
gates on <sha>: `python3 -m unittest discover -s tests -t .` and dotagents'
`check_skills.py skills`, found through `omp plugin list --json`; a failed gate
ends the run untagged. Tags counted are v2.<minor>.<patch> only (v1 is
ignored). The first run tags v2.0.0; later runs tag only when the shipped
paths changed since the last v2 tag, with a minor bump when that change adds a
store migration, else a patch bump. A change left untagged by a failed gate is
tagged by the next passing run, because each tag compares against the last
tag, not the last run. The annotated tag message is
`atlas v2.x.y`, the commit subjects since the last tag, and the trailers
`Omp-Version` and `Dotagents`; a GitHub Release is created from it with `gh`
(a gh failure only logs), and `notify` on PATH, when present, reports the
outcome.

Exit codes: 0 done (tagged, nothing to tag or skipped), 1 a gate or the tag
push failed, 2 tool error.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

SHIPPED = ("package.json", "skills", "rules")
MIGRATIONS = "skills/atlas-ask/atlas/store/migrations/"
TAG_RE = re.compile(r"v2\.(\d+)\.(\d+)")
OMP_VERSION_RE = re.compile(r"(?:omp/)?(\d+\.\d+\.\d+\S*)")
CHECK_SKILLS = "skills/craft-skill/scripts/check_skills.py"
PUSH_WAIT = 3600  # seconds the run waits for the `git push` process to exit
TEST_TIMEOUT = 1800
CHECK_TIMEOUT = 600
TOOL_TIMEOUT = 120  # omp, gh and notify calls
LOG_MAX = 1 << 20  # bytes; a larger log moves to release.log.1 before the next run
CACHE_KEEP = 50  # passing check keys kept in check-cache
DETAIL_LINES = 20  # output lines shown for a failed gate


class ToolError(Exception):
    pass


def cache_dir() -> Path:
    return Path.home() / ".cache" / "atlas-release"


def git(repo: Path | str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace").strip().split("\n")[-1]
        raise ToolError(f"git {args[0]}: {detail or f'exit {proc.returncode}'}")
    return proc.stdout.decode()


def git_ok(repo: Path | str, *args: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True).returncode == 0


def repo_root() -> Path:
    return Path(git(".", "rev-parse", "--show-toplevel").strip())


def resolve_commit(repo: Path, rev: str) -> str:
    return git(repo, "rev-parse", "--verify", "--end-of-options", f"{rev}^{{commit}}").strip()


def say(line: str) -> str:
    print(line)
    return line


# --- setup and shipped-paths ---------------------------------------------------


def cmd_setup(args: argparse.Namespace) -> int:
    repo = repo_root()
    git(repo, "config", "--local", "core.hooksPath", ".githooks")
    print(f"setup: core.hooksPath is .githooks in {repo}")
    return 0


def shipped_paths(repo: Path, ref: str) -> list[str]:
    return git(repo, "ls-tree", "-r", "--name-only", ref, "--", *SHIPPED).splitlines()


def cmd_shipped_paths(args: argparse.Namespace) -> int:
    for path in shipped_paths(repo_root(), args.ref):
        print(path)
    return 0


# --- release decisions ----------------------------------------------------------


def last_tag(clone: Path) -> tuple[tuple[int, int], str] | None:
    """The highest v2.<minor>.<patch> tag, or None."""
    tags = []
    for name in git(clone, "tag", "--list", "v2.*").split():
        match = TAG_RE.fullmatch(name)
        if match:
            tags.append(((int(match.group(1)), int(match.group(2))), name))
    return max(tags) if tags else None


def next_tag(clone: Path, sha: str) -> tuple[str | None, str | None, str]:
    """(tag to make or None, last tag or None, reason)."""
    last = last_tag(clone)
    if last is None:
        return "v2.0.0", None, "first v2 release"
    (minor, patch), name = last
    changed = git(clone, "diff", "--name-only", name, sha, "--", *SHIPPED).split()
    if not changed:
        return None, name, f"no shipped change since {name}"
    added = git(clone, "diff", "--name-only", "--diff-filter=A", name, sha, "--", MIGRATIONS).split()
    if added:
        return f"v2.{minor + 1}.0", name, f"adds migration {added[0]}"
    return f"v2.{minor}.{patch + 1}", name, f"{len(changed)} shipped file(s) changed since {name}"


def subjects(clone: Path, sha: str, since: str | None) -> list[str]:
    span = f"{since}..{sha}" if since else sha
    return git(clone, "log", "--reverse", "--format=%s", span, "--").splitlines()


def tag_message(tag: str, lines: list[str], omp: str, dotagents: str) -> str:
    body = "".join(f"- {line}\n" for line in lines)
    return f"atlas {tag}\n\n" + (f"{body}\n" if body else "") + f"Omp-Version: {omp}\nDotagents: {dotagents}\n"


# --- host facts -------------------------------------------------------------------


def run_tool(cmd: list[str], cwd: Path | None = None) -> str:
    label = " ".join(cmd[:3])
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=TOOL_TIMEOUT)
    except OSError as err:
        raise ToolError(f"{label}: {err.strerror or err}") from err
    except subprocess.TimeoutExpired as err:
        raise ToolError(f"{label}: timed out after {TOOL_TIMEOUT} s") from err
    if proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace").strip().split("\n")[-1]
        raise ToolError(f"{label}: {detail or f'exit {proc.returncode}'}")
    return proc.stdout.decode()


def omp_version() -> str:
    """The bare version `omp --version` reports, such as 18.18.2."""
    out = run_tool(["omp", "--version"]).strip()
    match = OMP_VERSION_RE.fullmatch(out)
    if not match:
        raise ToolError(f"omp --version: unexpected output {out!r}")
    return match.group(1)


def dotagents_facts() -> tuple[Path, str]:
    """(check_skills.py path, Dotagents trailer value) from the `dotagents` plugin entry.

    The trailer is the commit of the checkout the plugin is linked from, or the
    installed version when the plugin is not a git checkout."""
    try:
        listing = json.loads(run_tool(["omp", "plugin", "list", "--json"]))
        entry = next(e for e in listing.get("npm", []) if e.get("name") == "dotagents")
    except (ToolError, ValueError, AttributeError, StopIteration) as err:
        reason = err if isinstance(err, ToolError) else "no dotagents entry in omp plugin list --json"
        raise ToolError(f"check_skills.py not found: {reason}") from err
    root = Path(str(entry.get("path", "")))
    script = root / CHECK_SKILLS
    if not script.is_file():
        raise ToolError(f"check_skills.py not found: {script}")
    if git_ok(root.resolve(), "rev-parse", "--show-toplevel"):
        return script, git(root.resolve(), "rev-parse", "HEAD").strip()
    version = entry.get("version")
    if not version:
        raise ToolError("dotagents plugin entry has no version")
    return script, str(version)


# --- clone, gates and cache ---------------------------------------------------------


def clean_env() -> dict[str, str]:
    """The environment without variables git sets for hooks, which would point
    git calls in the clone back at the checkout."""
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def sync_clone(url: str) -> Path:
    clone = cache_dir() / "clone"
    if not clone.exists():
        git(cache_dir(), "clone", "--quiet", url, str(clone))
    top = subprocess.run(["git", "-C", str(clone), "rev-parse", "--show-toplevel"], capture_output=True)
    if top.returncode != 0 or Path(top.stdout.decode().strip()).resolve() != clone.resolve():
        raise ToolError(f"{clone}: not a clone of {url}")
    git(clone, "remote", "set-url", "origin", url)
    git(clone, "fetch", "--quiet", "--force", "--prune", "--prune-tags", "--tags", "origin")
    return clone


def gate(name: str, cmd: list[str], cwd: Path, timeout: int) -> bool:
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=clean_env(), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"check {name}: fail (timed out after {timeout} s)")
        return False
    if proc.returncode == 0:
        print(f"check {name}: pass")
        return True
    print(f"check {name}: fail (exit {proc.returncode})")
    lines = (proc.stdout + proc.stderr).decode(errors="replace").rstrip().split("\n")
    for line in lines[-DETAIL_LINES:]:
        print(f"  {line}")
    return False


def check_key(clone: Path, sha: str, script: Path) -> str:
    tree = git(clone, "rev-parse", f"{sha}^{{tree}}").strip()
    digest = hashlib.sha256(f"python {sys.version}\ntree {tree}\n".encode())
    digest.update(hashlib.sha256(script.read_bytes()).hexdigest().encode())
    return digest.hexdigest()


def cached_passes() -> list[str]:
    try:
        return [k for k in (cache_dir() / "check-cache").read_text().split("\n") if k]
    except OSError:
        return []


def record_pass(key: str) -> None:
    keys = [k for k in cached_passes() if k != key][-(CACHE_KEEP - 1) :] + [key]
    fd, tmp = tempfile.mkstemp(dir=cache_dir(), prefix="check-cache.")
    with os.fdopen(fd, "w") as out:
        out.write("".join(f"{k}\n" for k in keys))
    os.replace(tmp, cache_dir() / "check-cache")


def gates_pass(clone: Path, sha: str, script: Path) -> bool:
    key = check_key(clone, sha, script)
    if key in cached_passes():
        print("check tests, skills: pass (cached)")
        return True
    tests = gate("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], clone, TEST_TIMEOUT)
    skills = gate("skills", [sys.executable, str(script), "skills"], clone, CHECK_TIMEOUT)
    if tests and skills:
        record_pass(key)
    return tests and skills


# --- the run ------------------------------------------------------------------------


def release(repo: Path, sha: str) -> tuple[str, int]:
    """Check `sha` and tag it when due; return (outcome line, exit code)."""
    url = git(repo, "remote", "get-url", "origin").strip()
    clone = sync_clone(url)
    if not git_ok(clone, "rev-parse", "--verify", "--quiet", "origin/main"):
        return say("release: skipped (origin has no main branch)"), 0
    tip = git(clone, "rev-parse", "origin/main").strip()
    if tip != sha:
        if git_ok(clone, "merge-base", "--is-ancestor", sha, tip):
            return say(f"release: skipped (superseded by {tip})"), 0
        return say(f"release: skipped (origin main is {tip}, not {sha}: the push did not land)"), 0
    git(clone, "checkout", "--quiet", "--force", "--detach", sha)
    git(clone, "clean", "-ffdxq")

    script, dotagents = dotagents_facts()
    if not gates_pass(clone, sha, script):
        return say(f"release: failed (checks did not pass on {sha}; the next push retries)"), 1
    tag, since, reason = next_tag(clone, sha)
    if tag is None:
        return say(f"release: nothing to tag ({reason})"), 0
    omp = omp_version()

    with tempfile.TemporaryDirectory() as tmp:
        message = Path(tmp) / "message"
        message.write_text(tag_message(tag, subjects(clone, sha, since), omp, dotagents))
        git(clone, "tag", "--annotate", "--cleanup=verbatim", "--file", str(message), tag, sha)
    push = subprocess.run(["git", "-C", str(clone), "push", "--quiet", "origin", f"refs/tags/{tag}"], capture_output=True)
    if push.returncode != 0:
        git(clone, "tag", "--delete", tag)
        detail = push.stderr.decode(errors="replace").strip().split("\n")[-1]
        return say(f"release: failed (tag push: {detail or f'exit {push.returncode}'})"), 1
    outcome = say(f"release: {tag} from {sha}")
    create_github_release(clone, tag)
    return outcome, 0


def create_github_release(clone: Path, tag: str) -> None:
    notes = git(clone, "for-each-ref", "--format=%(contents)", f"refs/tags/{tag}").rstrip("\n")
    env = {**clean_env(), "GH_PROMPT_DISABLED": "1"}
    cmd = ["gh", "release", "create", tag, "--verify-tag", "--title", f"atlas {tag}", "--notes", notes]
    try:
        proc = subprocess.run(cmd, cwd=clone, env=env, capture_output=True, timeout=TOOL_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as err:
        print(f"github release: not created ({err})")
        return
    if proc.returncode != 0:
        detail = proc.stderr.decode(errors="replace").strip().split("\n")[-1]
        print(f"github release: not created ({detail or f'exit {proc.returncode}'})")
        return
    print(f"github release: {tag} created")


def notify(outcome: str, code: int) -> None:
    """Report a tag or a failure through `notify` on PATH; quiet outcomes are only logged."""
    tagged = re.match(r"release: (v2\.\d+\.\d+) from ", outcome)
    if not tagged and code == 0:
        return
    script = shutil.which("notify")
    if script is None:
        return
    level = "info" if tagged else "urgent"
    title = f"atlas {tagged.group(1)} released" if tagged else "atlas release failed"
    message = "" if tagged else f"{outcome} (log: {cache_dir() / 'release.log'})"
    with contextlib.suppress(OSError, subprocess.TimeoutExpired):
        subprocess.run(
            [script, "send", "--project", "atlas", "--about", "release", "--level", level, title, message],
            capture_output=True,
            timeout=TOOL_TIMEOUT,
        )


def wait_for_exit(pid: int, limit: float) -> bool:
    """Whether process `pid` is gone within `limit` seconds (a missing process is gone)."""
    deadline = time.monotonic() + limit
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass  # alive, owned by another user
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.5)


def publish_after_push(repo: Path, sha: str, push_pid: int) -> int:
    """One release run: one log block `--- release <sha> <time>` .. `--- exit <code>` under the lock."""
    with contextlib.suppress(OSError):
        os.nice(19)
    sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    exited = wait_for_exit(push_pid, PUSH_WAIT)
    cache_dir().mkdir(parents=True, exist_ok=True)
    with open(cache_dir() / "release.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        print(f"--- release {sha} {datetime.now().astimezone().isoformat(timespec='seconds')}")
        try:
            if exited:
                outcome, code = release(repo, sha)
            else:
                outcome, code = say(f"release: skipped (git push {push_pid} still running after {PUSH_WAIT} s)"), 0
        except ToolError as err:
            outcome, code = say(f"release: error: {err}"), 2
        print(f"--- exit {code}")
    notify(outcome, code)
    return code


def start_background(repo: Path, sha: str, push_pid: int) -> int:
    cache_dir().mkdir(parents=True, exist_ok=True)
    log_path = cache_dir() / "release.log"
    with contextlib.suppress(OSError):
        if log_path.stat().st_size > LOG_MAX:
            log_path.replace(log_path.with_name("release.log.1"))
    with open(log_path, "ab") as log:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "publish", "--after-push", str(push_pid), sha],
            cwd=repo,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print(f"started in the background after the push; result in {log_path}")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    repo = repo_root()
    sha = resolve_commit(repo, args.sha)
    if args.background:
        return start_background(repo, sha, args.after_push)
    return publish_after_push(repo, sha, args.after_push)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="release.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("setup", help="set core.hooksPath to .githooks")
    p.set_defaults(run=cmd_setup)
    p = sub.add_parser("shipped-paths", help="print the shipped files at a ref")
    p.add_argument("ref")
    p.set_defaults(run=cmd_shipped_paths)
    p = sub.add_parser("publish", help="tag a pushed commit as the next v2 release when due")
    p.add_argument("sha")
    p.add_argument("--after-push", type=int, required=True, metavar="PID", help="wait for this git push to exit")
    p.add_argument("--background", action="store_true", help="run detached, appending to release.log")
    p.set_defaults(run=cmd_publish)
    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except ToolError as err:
        print(f"release.py: error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
