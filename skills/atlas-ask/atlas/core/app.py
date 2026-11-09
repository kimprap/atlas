"""The one entry every caller uses: ``run(command, mode, body, host)``.

``cli.py`` calls it after the strict body decode; tests pass their own host.
This build answers only whether Atlas is set up: with no settings file every
command replies exit 3 with the fix, and command work arrives with the stages
that build it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.core import reply

# Commands with the action words and mode flags each accepts. An empty action
# set means the command takes no action word.
COMMANDS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "status": (frozenset(), frozenset({"detail"})),
    "add": (frozenset(), frozenset({"redo", "reread"})),
    "inbox": (frozenset({"add", "list"}), frozenset()),
    "find": (frozenset(), frozenset({"wide"})),
    "ask": (frozenset(), frozenset()),
    "topic": (
        frozenset({"create", "draft", "save", "follow", "unfollow", "nothing_to_save", "list"}),
        frozenset(),
    ),
    "plan": (frozenset({"save", "mark", "show"}), frozenset()),
    "note": (frozenset(), frozenset()),
    "archive": (frozenset(), frozenset()),
    "restore": (frozenset(), frozenset()),
}

SETUP_SKILL = "atlas-init"


def config_path() -> Path:
    """The settings file ``atlas-init`` writes, under the caller's ``HOME``."""
    return Path.home() / ".config" / "atlas" / "config.toml"


def _usage_problem(command: str, mode: str | None) -> dict[str, Any] | None:
    word, _, action = command.partition(" ")
    if word not in COMMANDS:
        known = ", ".join(COMMANDS)
        return reply.problem("command", f'unknown command "{word}"; the commands are {known}')
    actions, modes = COMMANDS[word]
    if action and action not in actions:
        if not actions:
            return reply.problem("action", f'"{word}" takes no action word, got "{action}"')
        return reply.problem(
            "action", f'"{word}" has no action "{action}"; its actions are {", ".join(sorted(actions))}'
        )
    if mode is not None and mode not in modes:
        if not modes:
            return reply.problem("mode", f'"{word}" takes no --{mode}')
        return reply.problem(
            "mode", f'"{word}" has no --{mode}; it takes {", ".join("--" + m for m in sorted(modes))}'
        )
    return None


def run(command: str, mode: str | None, body: dict[str, Any], host: Any) -> tuple[dict[str, Any], int]:
    """Answer one call and return ``(reply, exit code)``.

    ``command`` is the command word, followed by its action word for ``inbox``,
    ``topic`` and ``plan`` (``"plan show"``); ``mode`` is the flag without its
    dashes (``"detail"``) or ``None``; ``body`` is the decoded JSON object.
    """
    usage = _usage_problem(command, mode)
    if usage is not None:
        return reply.build(command, reply.BAD_INPUT, problems=[usage]), reply.BAD_INPUT
    path = config_path()
    if not path.is_file():
        result = {
            "needs_action": [
                {
                    "what": "Atlas is not set up: there is no settings file",
                    "fix": [f"Run `{SETUP_SKILL}` to set up Atlas."],
                    "where": str(path),
                }
            ]
        }
        steps = [reply.next_step(f"run `{SETUP_SKILL}`", {"skill": SETUP_SKILL})]
        return reply.build(command, reply.NOT_SET_UP, result=result, next=steps), reply.NOT_SET_UP
    word = command.partition(" ")[0]
    problems = [reply.problem("command", f'"{word}" is not available in this Atlas build yet')]
    return reply.build(command, reply.FAILED, problems=problems), reply.FAILED
