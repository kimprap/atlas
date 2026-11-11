"""``status``: what needs action, one summary line, and Next.

Action items come first, in this order: not set up, store newer than the code,
missing model roles (one item per role), the judge's setup problem, judge choice
not saved, a price row missing for a recorded model, this month's billed spend
at or past ``cap_warn`` of the cap, a usage window at or past ``window_stop``,
and the host version warning. When no profile resolves, ``status``
lists the not-set-up item and the missing roles only, so ``atlas-init`` takes the
role fix lines from it on a fresh machine; it opens no store and uses no judge.
Not set up and a missing role exit 3, a store newer than the code or host facts
that cannot be read exit 1; the exit code is the first blocking item's. The
price, cap and window items are warnings and never change the exit code.
``detail`` is filled only on ``--detail``. The summary line and ``detail``
count sources, current claims, unarchived topics, inbox links and
archived sources. ``detail.redo`` and Next's redo offer count the unarchived
summaries older than the current rubric version and ``atlas_summarize`` model
(``Store.older_count``); the offer is a Next line only, never an action item.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from atlas import ports
from atlas.core import reply, spend, summarize
from atlas.core.config import SETUP_SKILL, Profile, config_path
from atlas.store import NEWER_THAN_CODE, StoreCounts, StoreFailed, StoreNewer

# The model roles Atlas calls and the model each is suggested to use.
ROLES = {
    "atlas_summarize": "anthropic/claude-sonnet-5-5:high",
    "atlas_query": "anthropic/claude-opus-5-5:medium",
    "atlas_rerank": "anthropic/claude-opus-5-5:medium",
    "atlas_answer": "anthropic/claude-opus-5-5:medium",
    "atlas_escalate": "anthropic/claude-opus-5-5:medium",
}
JUDGE_LABELS = {"jev": "Jev", "opus": "Opus", None: "not chosen"}
# ``detail.windows`` when the host has no quota port or host facts, or the windows cannot be read.
WINDOWS_UNKNOWN = "windows unknown"

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


def summary_model(host: ports.Host) -> str | None:
    """The model the ``atlas_summarize`` role is set to, without its thinking suffix; ``None`` when the host cannot say."""
    if host.facts is None:
        return None
    try:
        selector = host.facts.roles().get(summarize.SUMMARIZE)
    except ports.CallFailed:
        return None
    return None if selector is None else selector.partition(":")[0]


def _facts_problem(err: ports.CallFailed) -> dict[str, Any]:
    return reply.problem("roles", f"the host's model roles cannot be read: {err.detail}")


def _price_item(model: str) -> dict[str, Any]:
    return _item(
        f"Model {model} has no price row, so the cost of its calls is unknown",
        [
            f'[prices."{model}"]',
            "input = <USD per million input tokens>",
            "output = <USD per million output tokens>",
            "cache_read = <USD per million cache-read tokens>",
            "cache_write = <USD per million cache-write tokens>",
        ],
        str(config_path()),
    )


def _limit_items(
    profile: Profile, billed: float | None, windows: list[ports.Window] | None, now: datetime
) -> list[dict[str, Any]]:
    """The cap item, then one item per window at or past ``window_stop``."""
    items = []
    cap = spend.cap_limit(profile, billed) if billed is not None else None
    if cap is not None:
        items.append(
            _item(
                cap.what[:1].upper() + cap.what[1:],
                ["Each paid command asks before its first paid call until next month; raise cap_usd to ask later."],
                str(config_path()),
            )
        )
    for window in spend.windows_at_stop(profile, windows or []):
        items.append(
            _item(
                f"{spend.window_label(window)} at {round(window.used_fraction * 100)}%;"
                f" resets {spend.reset_label(window.resets_at, now)}",
                ["Batches stop before each item until this window resets; single commands still run."],
                None,
            )
        )
    return items


def _window_detail(windows: list[ports.Window] | None, now: datetime) -> list[dict[str, Any]] | str:
    """Each window's use and reset time, or ``windows unknown`` when the host cannot report them."""
    if windows is None:
        return WINDOWS_UNKNOWN
    return [
        {
            "provider": window.provider,
            "window": spend.duration_label(window.duration_s),
            "used_percent": round(window.used_fraction * 100),
            "resets": spend.reset_label(window.resets_at, now),
        }
        for window in windows
    ]


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

    now = spend.local_now()
    size: int | None = None
    month: dict[str, Any] | None = None
    counts: StoreCounts | None = None
    unpriced: list[str] = []
    older: int | None = None
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
        try:
            month = spend.month(store, now)
            counts = store.counts()
            unpriced = [
                model
                for model in store.models_not_billed(spend.JUDGE_ROLE)
                if spend.price_for(profile.prices, model) is None
            ]
            older = store.older_count(summarize.RUBRIC_VERSION, summary_model(host))
        except StoreFailed as err:
            problems.append(reply.problem("store", f"the store cannot be read: {err.detail}"))
            code = reply.FAILED
        finally:
            store.close()
        # After close, so the write-ahead log is folded into the file the size measures.
        size = store.size()

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

    items += [_price_item(model) for model in unpriced]
    windows = spend.windows(host, list(ROLES))
    items += _limit_items(profile, month["total"]["billed"] if month is not None else None, windows, now)

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
    if older:
        plural = "summary" if older == 1 else "summaries"
        label = f'{older} {plural} on an older rubric or summary model; to rebuild them, ask "Redo old summaries"'
        steps.append(reply.next_step(label, {"stop": True}))

    summary = f"Profile {profile.name}: "
    if counts is not None:
        plural = "" if counts.sources == 1 else "s"
        summary += f"{counts.sources} source{plural}, inbox {counts.inbox}, "
    result = {
        "needs_action": items,
        "summary": f"{summary}judge {JUDGE_LABELS[profile.judge]}, Atlas {version}",
        "detail": None,
    }
    if detail:
        result["detail"] = {
            "profile": profile.name,
            "store": {"path": str(profile.store), "size": size},
            "roles": None if roles is None else {role: roles.get(role) for role in ROLES},
            "judge": profile.judge,
            "counts": None
            if counts is None
            else {
                "sources": counts.sources,
                "claims": counts.claims,
                "topics": counts.topics,
                "inbox": counts.inbox,
                "archived": counts.archived,
            },
            "atlas_version": version,
            "host_version": host_version,
            "spend": month,
            "windows": _window_detail(windows, now),
            "redo": older,
            "confirm": dict(profile.confirm),
            "limits": profile.limits(),
        }
    return reply.build("status", code, result=result, problems=problems, next=steps), code
