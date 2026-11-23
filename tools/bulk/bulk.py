#!/usr/bin/env python3
"""The Atlas bulk runner's command line (repo-only; never shipped, never reached through ``atlas-ask``).

  bulk.py status --profile <profile> --name <run name>
  bulk.py run --profile <profile> --name <run name> [--links <file>] [--yes] [--slice <minutes>] [--no-token]
  bulk.py answer <link> <option> --profile <profile> --name <run name>
  bulk.py retry <link> | --dropped --profile <profile> --name <run name>

``run`` works through the run's links in lanes for one slice (default 55 minutes); ``--links`` is a file with one
link per line (blank and ``#`` lines ignored) and is optional once the run has a ledger. Without ``--yes`` it prints
each lane's count and the estimated cost and makes no read, model or judge call and writes nothing. Before a run whose
queue holds a GitHub link it checks that ``GITHUB_TOKEN`` or ``GH_TOKEN`` holds a value, unless given ``--no-token``.
``--profile`` is always required, so the runner never falls back to the default profile. The ledger is
``$XDG_STATE_HOME/atlas/<profile>/bulk/<name>.json`` (else under ``~/.local/state``); the behavior is
``ARCHITECTURE.md`` "Bulk runner".
Exit codes: 0 the slice ended, 1 a cap, a window or an unexpected stop, 2 bad input, 3 not set up.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TextIO

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.bulk import runner  # noqa: E402

from atlas import ports  # noqa: E402

COMMANDS = ("status", "run", "answer", "retry")
# Each command's flags: ``True`` when the flag takes a value.
FLAGS = {
    "status": {"profile": True, "name": True},
    "run": {"profile": True, "name": True, "links": True, "yes": False, "slice": True, "no-token": False},
    "answer": {"profile": True, "name": True},
    "retry": {"profile": True, "name": True, "dropped": False},
}


class Usage(Exception):
    pass


def parse(command: str, argv: Sequence[str]) -> tuple[dict[str, Any], list[str]]:
    """The flags and the bare words of ``argv``; anything else is a usage error."""
    spec = FLAGS[command]
    found: dict[str, Any] = {}
    words: list[str] = []
    items = list(argv)
    while items:
        item = items.pop(0)
        if not item.startswith("--"):
            words.append(item)
            continue
        name = item[2:]
        if name not in spec:
            raise Usage(f'unexpected "{item}"')
        if spec[name]:
            if not items:
                raise Usage(f"{item} needs a value")
            found[name] = items.pop(0)
        else:
            found[name] = True
    for required in ("profile", "name"):
        if required not in found:
            raise Usage(f"--{required} is required")
    return found, words


def read_links(path: str) -> list[str]:
    try:
        lines = Path(path).expanduser().read_text(encoding="utf-8").splitlines()
    except (OSError, ValueError) as err:
        raise Usage(f"--links {path} cannot be read: {err}") from None
    stripped = [line.strip() for line in lines]
    return [line for line in stripped if line and not line.startswith("#")]


def main(
    argv: Sequence[str] | None = None,
    *,
    host_factory: Callable[[str], ports.Host] | None = None,
    now: Callable[[], float] = time.monotonic,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    out, err = out or sys.stdout, err or sys.stderr
    if not args or args[0] not in COMMANDS:
        print(f"usage: bulk.py <{'|'.join(COMMANDS)}> --profile <profile> --name <run name> ...", file=err)
        return 2
    command = args[0]
    try:
        flags, words = parse(command, args[1:])
        profile, name = flags["profile"], flags["name"]
        if command == "status" and not words:
            return runner.status(profile, name, out, err)
        if command == "answer" and len(words) == 2:
            return runner.answer(profile, name, words[0], words[1], out, err)
        if command == "retry" and len(words) == (0 if flags.get("dropped") else 1):
            return runner.retry(profile, name, None if flags.get("dropped") else words[0], out, err)
        if command != "run" or words:
            raise Usage("status takes no word, answer takes <link> <option>, retry takes <link> or --dropped, run takes no word")
        try:
            slice_minutes = runner.minutes(flags["slice"]) if "slice" in flags else float(runner.DEFAULT_SLICE)
        except ValueError:
            raise Usage("--slice needs a number of minutes above 0") from None
        links = read_links(flags["links"]) if "links" in flags else None
    except Usage as usage:
        print(f"{command}: {usage}", file=err)
        return 2
    if host_factory is None:
        from atlas import host as atlas_host

        host_factory = atlas_host.build
    yes = bool(flags.get("yes"))
    result = runner.run(
        host_factory(profile), profile, name, links, yes=yes, slice_minutes=slice_minutes, check_token=not flags.get("no-token"),
        words="bulk.py run --yes", now=now, out=out, err=err,
    )
    if result.end == "dry":
        print("no read, model or judge call was made and nothing was written; run again with --yes to run it", file=out)
    elif result.end == "stopped":
        print(f"stopped: {result.text}", file=out)
    elif result.end in ("sliced", "finished"):
        if result.more:
            print("run again to continue", file=out)
        else:
            held = [entry["state"] for entry in result.left.values()]
            print(f"nothing left to send: {held.count(runner.PARKED)} parked, {held.count(runner.DROPPED)} dropped", file=out)
    return result.code


if __name__ == "__main__":
    raise SystemExit(main())
