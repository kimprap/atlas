"""Runs one case of one version of Atlas and reports what happened (repo-only).

A version is a git worktree of a ref plus overrides. ``execute(job, host)`` runs one
case through ``atlas.core.app.run`` on the ``Host`` it is given, against an in-memory
copy of the ``eval`` profile: the settings file is read as it is, then the copy's
store path is replaced by the job's scratch store, every confirm is set to ``never``
(the tool is the user and the run was started with ``--yes``) and the overrides are
applied. Nothing is written back to the settings file.

``main`` is the subprocess entry the tool starts once per case with the worktree's
``skills/atlas-ask`` first on ``sys.path``, so the version under test is the
code that runs: it reads the job as JSON on stdin, builds the version's own host,
applies role overrides and prints the
result as one JSON line.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    # As a script: the root makes ``tools.quality`` importable, and the version's own Atlas (the
    # first argument, a worktree's ``skills/atlas-ask``) goes first, before any import of ``atlas``.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    if len(sys.argv) > 1:
        sys.path.insert(0, sys.argv[1])

from tools.quality import _path  # noqa: F401  (puts the atlas package on sys.path)

from tools.quality import replay_read

from atlas import ports  # noqa: E402
from atlas.core import app, config, identity  # noqa: E402

# Settings of the profile an override may set, and the prefix that sets a role's model.
PROFILE_SETTINGS = (
    "judge",
    "max_page_tokens",
    "judge_concurrency",
    "rethink",
    "near_copy",
    "reread_days",
    "reread_new_text",
    "cap_usd",
    "cap_warn",
    "window_stop",
)
ROLE_PREFIX = "role."
# Settings of the tool itself, never of the profile: ``phrasings=own`` makes the search
# lane run without the fixed phrasings, so ``atlas_query`` is tested.
TOOL_SETTINGS = ("phrasings",)
PHRASINGS = ("fixed", "own")


def parse_override(text: str) -> tuple[str, str]:
    """``key=value`` of one ``--set``; the key must name a profile setting, ``role.<role>`` or a tool setting."""
    key, equals, value = text.partition("=")
    if not equals or not key or not value:
        raise ValueError(f'--set takes key=value, got "{text}"')
    known = key in PROFILE_SETTINGS or key in TOOL_SETTINGS or (key.startswith(ROLE_PREFIX) and len(key) > len(ROLE_PREFIX))
    if not known:
        raise ValueError(
            f'--set "{key}" is not an override; use a profile setting ({", ".join(PROFILE_SETTINGS)}), '
            f'role.<role>=<model selector> or {", ".join(TOOL_SETTINGS)}'
        )
    if key == "phrasings" and value not in PHRASINGS:
        raise ValueError(f"--set phrasings is one of {', '.join(PHRASINGS)}")
    return key, value


def _typed(value: str) -> Any:
    if value in ("true", "false"):
        return value == "true"
    for kind in (int, float):
        try:
            return kind(value)
        except ValueError:
            pass
    return value


@contextmanager
def in_memory_profile(name: str, store: Path, overrides: Mapping[str, str]) -> Iterator[None]:
    """Make ``config`` read the profile ``name`` with its store at ``store``, no confirms and ``overrides`` applied."""
    original = config._read  # noqa: SLF001  (the settings file is read once, then copied in memory)

    def read() -> dict[str, Any]:
        settings = original()
        profiles = settings.get("profiles")
        if not isinstance(profiles, dict) or not isinstance(profiles.get(name), dict):
            raise config.NotSetUp(f'profile "{name}" is not in the settings file')
        entry = dict(profiles[name])
        entry["store"] = str(store)
        entry["confirm"] = dict.fromkeys(config.CHANGE_KINDS, config.NEVER)
        entry.update({key: _typed(value) for key, value in overrides.items() if key in PROFILE_SETTINGS})
        return {**settings, "default_profile": name, "profiles": {**profiles, name: entry}}

    config._read = read  # noqa: SLF001
    try:
        yield
    finally:
        config._read = original  # noqa: SLF001


def role_overrides(overrides: Mapping[str, str]) -> dict[str, str]:
    return {key[len(ROLE_PREFIX) :]: value for key, value in overrides.items() if key.startswith(ROLE_PREFIX)}


def with_role_overrides(host: ports.Host, roles: Mapping[str, str]) -> ports.Host:
    """``host`` with each role in ``roles`` served by the given model selector.

    The OMP adapter sends ``@<role>`` as the gateway's model, so an overridden role's request
    carries the selector instead; the adapter's role table also names it, so core's checks and
    the records name the model that ran. [INFERENCE] the gateway takes a model selector as a
    request's ``model``; the model each call ran on is recorded in the ``calls`` rows and shown by
    the report, so a gateway that ignored it shows up there.
    """
    if not roles:
        return host
    omp = host.call
    omp._roles = {**omp.roles(), **roles}  # type: ignore[attr-defined]  # noqa: SLF001
    gateway = omp._gateway  # type: ignore[attr-defined]  # noqa: SLF001

    def patched(path: str, body: Mapping[str, Any] | None, timeout: int) -> tuple[int, Any]:
        model = None if body is None else body.get("model")
        if isinstance(model, str) and model.startswith("@") and model[1:] in roles:
            body = {**body, "model": roles[model[1:]]}  # type: ignore[dict-item]
        return gateway(path, body, timeout)

    omp._gateway = patched  # type: ignore[attr-defined]  # noqa: SLF001
    return host


def _calls(store: Any, before: int) -> tuple[list[dict[str, Any]], float, bool]:
    rows = store.calls_since("")[before:]
    calls = [
        {"role": row.role, "model": row.model, "thinking": row.thinking, "cost_usd": row.cost_usd, "cost_kind": row.cost_kind}
        for row in rows
    ]
    return calls, sum(row.cost_usd or 0.0 for row in rows), any(row.cost_kind == "unknown" for row in rows)


def _claims(store: Any, source_id: int) -> list[dict[str, Any]]:
    found = []
    for stored in store.claims(source_id):
        claim = stored.claim
        flag = claim.flag
        found.append(
            {
                "section": claim.section,
                "text": claim.text,
                "basis": claim.basis,
                "quotes": [{"text": q.text, "start": q.start, "end": q.end} for q in claim.quotes],
                "flag": None if flag is None else {"verdict": flag.verdict, "p": flag.p, "flagged": flag.flagged, "judge_model": flag.judge_model},
            }
        )
    return found


def _records(items: Sequence[Mapping[str, Any]]) -> list[replay_read.PageRecord]:
    return [replay_read.PageRecord.from_json(item) for item in items]


def _summary(job: Mapping[str, Any], host: ports.Host, store_path: Path) -> dict[str, Any]:
    case = job["case"]
    item: dict[str, Any] = {"link": case["link"]}
    if case.get("scope"):
        item["scope"] = case["scope"]
    started = time.monotonic()
    answer, code = app.run("add", None, {"profile": job["profile"], "items": [item]}, host)
    seconds = time.monotonic() - started
    entries = answer.get("result", {}).get("items", [])
    changed = None
    if job.get("records_new") and code == 0:
        # A promoted changed page: the old text was added above; now the new text is read again (claim-level update).
        newer = replace(host, read=replay_read.ReplayRead(_records(job["records_new"])))
        again, _ = app.run("add", "reread", {"profile": job["profile"], "items": [{"link": case["link"]}]}, newer)
        got = (again.get("result", {}).get("items") or [{}])[0].get("result", "")
        found = re.search(r"updated \((\d+) claims? changed\)", got)
        changed = int(found.group(1)) if found else 0
        entries = [{"result": got}]
    out: dict[str, Any] = {
        "case": case["id"],
        "code": code,
        "result": entries[0]["result"] if entries else None,
        "decisions": [d["kind"] for d in answer.get("decisions", ())],
        "decision_text": [d["question"] for d in answer.get("decisions", ())],
        "needs_action": answer.get("result", {}).get("needs_action"),
        "seconds": seconds,
        "claims_changed": changed,
        "source": None,
    }
    store = host.open_store(store_path)
    try:
        calls, cost, unknown = _calls(store, 0)
        out.update(calls=calls, cost_usd=cost, cost_unknown=unknown)
        link = identity.clean(case["link"])
        found = None if link is None else store.source_for_link(link)
        if found is not None:
            record = store.source_record(found.source.id)
            out["source"] = {
                "abstract": record.abstract,
                "model": record.model,
                "thinking": record.thinking,
                "escalated": bool(record.escalated),
                "rethink_line": record.rethink_line,
                "dropped_claims": record.dropped_claims or 0,
                "support_status": record.support_status,
            }
            out["claims"] = _claims(store, found.source.id)
            out["text"] = store.page_text(found.source.id).text
    finally:
        store.close()
    return out


def _find(job: Mapping[str, Any], host: ports.Host, store_path: Path, command: str) -> dict[str, Any]:
    case = job["case"]
    body: dict[str, Any] = {"profile": job["profile"], "question": case["text"], "original": case["text"]}
    if job["overrides"].get("phrasings", "fixed") == "fixed" and case.get("rewrites"):
        body["phrasings"] = list(case["rewrites"])
    store = host.open_store(store_path)
    before = len(store.calls_since(""))
    started = time.monotonic()
    try:
        # A promoted query brings its sources' page text: each is added under this version first (replayed, never read).
        for record in _records(job.get("records", ())):
            app.run("add", None, {"profile": job["profile"], "items": [{"link": record.link}]}, host)
        answer, code = app.run(command, None, body, host)
        seconds = time.monotonic() - started
        calls, cost, unknown = _calls(store, before)
    finally:
        store.close()
    return {
        "case": case["id"],
        "code": code,
        "result": answer.get("result", {}),
        "problems": [p["problem"] for p in answer.get("problems", ())],
        "decisions": [d["kind"] for d in answer.get("decisions", ())],
        "decision_text": [d["question"] for d in answer.get("decisions", ())],
        "needs_action": answer.get("result", {}).get("needs_action"),
        "seconds": seconds,
        "calls": calls,
        "cost_usd": cost,
        "cost_unknown": unknown,
    }


def execute(job: Mapping[str, Any], host: ports.Host) -> dict[str, Any]:
    """Run ``job`` (one case of one lane) on ``host`` and return what it did as plain data."""
    store_path = Path(job["store"])
    host = replace(host, read=replay_read.ReplayRead(_records(job.get("records", ()))))
    with in_memory_profile(job["profile"], store_path, job["overrides"]):
        if job["lane"] == "summary":
            return _summary(job, host, store_path)
        if job["lane"] == "search":
            return _find(job, host, store_path, "find")
        if job["lane"] == "answers":
            return _find(job, host, store_path, "ask")
    raise ValueError(f"unknown lane {job['lane']!r}")


def main(argv: Sequence[str] | None = None) -> int:
    """The subprocess entry: ``worker.py`` reads one job on stdin; the version's ``atlas`` is first on ``sys.path``."""
    job = json.load(sys.stdin)
    from atlas import host as atlas_host

    built = with_role_overrides(atlas_host.build(job["profile"]), role_overrides(job["overrides"]))
    print(json.dumps(execute(job, built)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
