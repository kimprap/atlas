"""The failed-summary log: every model turn of a summary that failed after its escalation.

``add`` and ``add --reread`` call ``keep`` when ``summarize`` returns ``Failed``.
It writes one JSON file
``<state>/atlas/<profile>/failed-summaries/<UTC time>-<first 8 hex of SHA-256 of the key link>.json``,
``<state>`` being ``$XDG_STATE_HOME`` (when set to an absolute path), else
``~/.local/state``. The file holds the time, profile, command, key link, rubric
version and failure reason, and per model turn its role, model, thinking, stop,
usage, ``content``, ``tool_input`` and ``tool_raw`` as received, with the
code-check failures it produced. It holds no request messages, settings, keys
or headers. Only the newest ``KEEP`` files per profile stay: older ones are
deleted after each write. Folders are mode 700 and files mode 600; the file
sits outside the store because it holds page text the replies quote.

The failed item carries ``replies_log: <path>``; a write that fails adds the
problem ``replies not logged: <reason>`` and changes nothing else.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.core import reply, summarize

KEEP = 20
FOLDER = "failed-summaries"
_TIME = "%Y%m%dT%H%M%S.%fZ"


def state_home() -> Path:
    """``$XDG_STATE_HOME`` when it is an absolute path, else ``~/.local/state``."""
    given = os.environ.get("XDG_STATE_HOME")
    if given and Path(given).is_absolute():
        return Path(given)
    return Path.home() / ".local" / "state"


def folder(profile: str) -> Path:
    """The profile's failed-summary folder."""
    if not profile or profile in (".", "..") or "/" in profile or os.sep in profile:
        raise ValueError(f'the profile name "{profile}" is not a folder name')
    return state_home() / "atlas" / profile / FOLDER


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"{type(value).__name__} is not JSON")


def _turn(turn: summarize.Turn) -> dict[str, Any]:
    got = turn.reply
    usage = got.usage
    return {
        "role": turn.role,
        "model": got.model,
        "thinking": got.thinking,
        "stop": got.stop,
        "usage": {"input": usage.input, "output": usage.output, "cache_read": usage.cache_read, "cache_write": usage.cache_write},
        "content": got.content,
        "tool_input": got.tool_input,
        "tool_raw": got.tool_raw,
        "failures": list(turn.failures),
    }


def _private_folder(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)


def write(profile: str, command: str, key_link: str, failed: summarize.Failed) -> Path:
    """Write one failed-summary log and return its path; ``OSError``, ``ValueError`` or ``TypeError`` when it cannot."""
    when = datetime.now(timezone.utc)
    target = folder(profile)
    for part in (target.parent.parent, target.parent, target):
        _private_folder(part)
    record = {
        "time": when.isoformat(timespec="seconds"),
        "profile": profile,
        "command": command,
        "key_link": key_link,
        "rubric_version": summarize.RUBRIC_VERSION,
        "reason": failed.reason,
        "turns": [_turn(turn) for turn in failed.turns],
    }
    text = json.dumps(record, ensure_ascii=False, indent=1, default=_plain) + "\n"
    digest = hashlib.sha256(key_link.encode("utf-8")).hexdigest()[:8]
    path = target / f"{when.strftime(_TIME)}-{digest}.json"
    handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.fchmod(handle, 0o600)
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            handle = -1
            out.write(text)
    except BaseException:
        if handle >= 0:
            os.close(handle)
        path.unlink(missing_ok=True)  # a failed write leaves no part of a log behind
        raise
    kept = sorted(found for found in target.glob("*.json") if found.is_file())
    for older in kept[: max(len(kept) - KEEP, 0)]:
        older.unlink(missing_ok=True)  # another failed summary may have pruned it first
    return path


def keep(
    entry: dict[str, Any],
    problems: list[dict[str, Any]],
    profile: str,
    command: str,
    key_link: str,
    failed: summarize.Failed,
) -> None:
    """Log ``failed`` and put ``replies_log`` on its reply item, or the problem when the write fails."""
    try:
        path = write(profile, command, key_link, failed)
    except (OSError, ValueError, TypeError) as err:
        reason = getattr(err, "strerror", None) or str(err)
        problems.append(reply.problem("replies_log", f"replies not logged: {reason}", key_link))
        return
    entry["replies_log"] = str(path)
