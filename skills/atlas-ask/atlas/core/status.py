"""``status``: what needs action, one summary line, and Next.

Action items come first, in this order: not set up, store newer than the code,
missing model roles (one item per role), the judge's setup problem, judge choice
not saved, and the host version warning. When no profile resolves, ``status``
lists the not-set-up item and the missing roles only, so ``atlas-init`` takes the
role fix lines from it on a fresh machine; it opens no store and uses no judge.
Not set up and a missing role exit 3, a store newer than the code or host facts
that cannot be read exit 1; the exit code is the first blocking item's.
``detail`` is filled only on ``--detail``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from atlas import ports
from atlas.core import reply
from atlas.core.config import SETUP_SKILL, Profile, config_path
from atlas.store import NEWER_THAN_CODE, StoreFailed, StoreNewer

# The model roles Atlas calls and the model each is suggested to use.
ROLES = {
    "atlas_summarize": "anthropic/claude-sonnet-5-5:high",
    "atlas_query": "anthropic/claude-opus-5-5:medium",
    "atlas_rerank": "anthropic/claude-opus-5-5:medium",
    "atlas_answer": "anthropic/claude-opus-5-5:medium",
    "atlas_escalate": "anthropic/claude-opus-5-5:medium",
}
JUDGE_LABELS = {"jev": "Jev", "opus": "Opus", None: "not chosen"}

# The plugin root: skills/atlas-ask/atlas/core/status.py is four levels below it.
ROOT = Path(__file__).resolve().parents[4]
GIT_TIMEOUT_S = 10


def _git(*args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT_S
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else None


def atlas_version() -> tuple[str, str | None]:
    """``(version, nearest v2 tag)``: ``git describe`` in a checkout, else ``package.json`` and no tag."""
    top = _git("rev-parse", "--show-toplevel")
    if top is not None and Path(top).resolve() == ROOT:
        described = _git("describe", "--tags", "--match", "v2.*")
        if described is not None:
            return described, _git("describe", "--tags", "--abbrev=0", "--match", "v2.*")
    version = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    return f"v{version}", None


def _released_host_version(tag: str) -> str | None:
    """The host version trailer of annotated tag ``tag``."""
    return _git(
        "for-each-ref",
        f"refs/tags/{tag}",
        f"--format=%(contents:trailers:key={ports.HOST_VERSION_TRAILER},valueonly)",
    )


def _item(what: str, fix: list[str], where: str | None) -> dict[str, Any]:
    return {"what": what, "fix": fix, "where": where}


def _role_items(facts: ports.HostFacts | None, missing: dict[str, str]) -> list[dict[str, Any]]:
    """One item per missing role, with the host's fix lines, else the role and its model in plain words."""
    items = []
    for role, model in missing.items():
        fix = facts.role_fix({role: model}) if facts is not None else ports.RoleFix((), None)
        lines = list(fix.lines) or [f"Add the model role {role} with the model {model}."]
        items.append(_item(f"Role {role} is missing", lines, fix.where))
    return items


def _facts_problem(err: ports.CallFailed) -> dict[str, Any]:
    return reply.problem("roles", f"the host's model roles cannot be read: {err.detail}")


def not_set_up(item: dict[str, Any], host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``status`` when no profile resolves: ``item``, then every missing role.

    Without host facts every role is listed, since none can be checked.
    """
    problems: list[dict[str, Any]] = []
    items = [item]
    facts = host.facts
    try:
        roles = facts.roles() if facts is not None else {}
        items += _role_items(facts, {role: model for role, model in ROLES.items() if role not in roles})
    except ports.CallFailed as err:
        problems.append(_facts_problem(err))
    steps = [reply.next_step(f"run `{SETUP_SKILL}`", {"skill": SETUP_SKILL})]
    answer = reply.build("status", reply.NOT_SET_UP, result={"needs_action": items}, problems=problems, next=steps)
    return answer, reply.NOT_SET_UP


def run(profile: Profile, detail: bool, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``status`` for the resolved ``profile``."""
    items: list[dict[str, Any]] = []
    problems: list[dict[str, Any]] = []
    steps: list[dict[str, Any]] = []
    code = reply.DONE

    size: int | None = None
    try:
        store = host.open_store(profile.store)
    except StoreNewer:
        items.append(
            _item(
                f"The store of profile {profile.name} is newer than this Atlas",
                ["Check out a newer Atlas tag."],
                str(profile.store),
            )
        )
        problems.append(reply.problem("store", NEWER_THAN_CODE))
        steps.append(reply.next_step("check out a newer Atlas tag", {"stop": True}))
        code = reply.FAILED
    except StoreFailed as err:
        problems.append(reply.problem("store", f"the store cannot be opened: {err.detail}"))
        code = reply.FAILED
    else:
        size = store.size()
        store.close()

    facts = host.facts
    roles: dict[str, str] | None = None
    setup_needed = False
    try:
        if facts is not None:
            roles = facts.roles()
            missing = _role_items(facts, {role: model for role, model in ROLES.items() if role not in roles})
            if missing:
                items += missing
                setup_needed = True
                if code == reply.DONE:
                    code = reply.NOT_SET_UP
    except ports.CallFailed as err:
        roles = None
        problems.append(_facts_problem(err))
        if code == reply.DONE:
            code = reply.FAILED

    if profile.judge == "jev" and host.judge is not None:
        trouble = host.judge.setup_problem()
        if trouble is not None:
            items.append(_item(trouble.what, list(trouble.fix), trouble.where))
            setup_needed = True
    if profile.judge is None:
        items.append(
            _item(
                f"No judge is chosen for profile {profile.name}",
                [f"Run `{SETUP_SKILL}` to choose the judge: jev or opus."],
                str(config_path()),
            )
        )
        setup_needed = True

    version, tag = atlas_version()
    try:
        host_version = facts.version() if facts is not None else None
    except ports.CallFailed:
        host_version = None
    released = _released_host_version(tag) if tag is not None and host_version is not None else None
    if released is not None and host_version != released:
        items.append(
            _item(
                f"Host {facts.name} is version {host_version}, but Atlas {tag} was released with {released}",
                ["This is a warning; Atlas keeps working. If a command fails, check out an Atlas tag released with this host version."],
                None,
            )
        )

    if setup_needed:
        steps.append(reply.next_step(f"run `{SETUP_SKILL}`", {"skill": SETUP_SKILL}))
    if not steps and code == reply.DONE:
        steps.append(reply.next_step("nothing to fix; Atlas is ready", {"stop": True}))
    elif not steps:
        steps.append(reply.next_step("fix the problems shown, then ask for status again", {"stop": True}))

    result = {
        "needs_action": items,
        "summary": f"Profile {profile.name}: judge {JUDGE_LABELS[profile.judge]}, Atlas {version}",
        "detail": None,
    }
    if detail:
        result["detail"] = {
            "profile": profile.name,
            "store": {"path": str(profile.store), "size": size},
            "roles": None if roles is None else {role: roles.get(role) for role in ROLES},
            "judge": profile.judge,
            "atlas_version": version,
            "host_version": host_version,
        }
    return reply.build("status", code, result=result, problems=problems, next=steps), code
