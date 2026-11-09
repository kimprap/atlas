"""Atlas CLI: one call in, one JSON reply line out.

    python3 cli.py <command> [<action>] [--redo|--reread|--wide|--detail] < body.json

stdin holds one JSON object (``{}`` when the command takes no fields). The body
is decoded strictly before anything else, so a bad body is exit 2 whatever the
command or setup. Then ``atlas.host`` builds the host the command runs on and
``atlas.core.app.run`` answers it. Exit codes: 0 done, 1 failed, 2 bad input,
3 not set up, 4 needs a decision.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from atlas import host  # noqa: E402
from atlas.core import app, reply  # noqa: E402


def _parse(args: list[str]) -> tuple[str, str | None]:
    """Return (command with its action word, mode); raise ``BadInput`` for a malformed call."""
    words = [arg for arg in args if not arg.startswith("--")]
    flags = [arg[2:] for arg in args if arg.startswith("--")]
    if not words:
        raise reply.BadInput("no command given; call cli.py <command> [<action>] [--mode]")
    if len(words) > 2:
        raise reply.BadInput(f"too many words: {' '.join(words)}; give a command and at most one action")
    if len(flags) > 1:
        raise reply.BadInput(f"give at most one flag, got {' '.join('--' + f for f in flags)}")
    return " ".join(words), (flags[0] if flags else None)


def main(args: list[str]) -> int:
    op = " ".join(arg for arg in args if not arg.startswith("--"))
    try:
        body = reply.decode_body(sys.stdin.buffer.read())
    except reply.BadInput as err:
        bad = reply.build(op, reply.BAD_INPUT, problems=[reply.problem("body", err.problem)])
        return reply.write(bad, reply.BAD_INPUT)
    try:
        command, mode = _parse(args)
    except reply.BadInput as err:
        bad = reply.build(op, reply.BAD_INPUT, problems=[reply.problem("arguments", err.problem)])
        return reply.write(bad, reply.BAD_INPUT)
    chosen = body.get("profile")
    try:
        on = host.build(chosen if isinstance(chosen, str) and chosen else None)
    except host.UnknownHost as err:
        failed = reply.build(command, reply.FAILED, problems=[reply.problem("host", str(err))])
        return reply.write(failed, reply.FAILED)
    answer, code = app.run(command, mode, body, on)
    return reply.write(answer, code)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
