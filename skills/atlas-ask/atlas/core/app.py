"""The one entry every caller uses: ``run(command, mode, body, host)``.

``cli.py`` calls it after the strict body decode; tests pass their own host.
Every command first resolves its profile from the settings file; one that
cannot be resolved replies exit 3 with the fix, before any store is opened.
Only ``status`` then asks the host facts for the missing roles; every other
command uses no host before setup resolves. Then the command opens its profile's store. ``status``,
``add``, ``add --redo``, ``add --reread``, ``inbox``, ``find`` (also ``find --wide``), ``ask`` with a ``question``, a
``topic`` or ``whats_new`` (the catch-up), ``topic``, ``plan``, ``note``,
``archive`` and ``restore`` (of a link, a note, a topic or a citation) are answered in full;
the ``source`` form of ``ask`` and the other commands arrive with the stages that build them.
"""

from __future__ import annotations

import os
from typing import Any

from atlas import ports
from atlas.core import add, answer, catchup, config, inbox, notes, plans, reply, redo, reread, search, status, topics
from atlas.store import NEWER_THAN_CODE, StoreFailed, StoreNewer

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


def run(
    command: str, mode: str | None, body: dict[str, Any], host: ports.Host
) -> tuple[dict[str, Any], int]:
    """Answer one call and return ``(reply, exit code)``.

    ``command`` is the command word, followed by its action word for ``inbox``,
    ``topic`` and ``plan`` (``"plan show"``); ``mode`` is the flag without its
    dashes (``"detail"``) or ``None``; ``body`` is the decoded JSON object.
    """
    usage = _usage_problem(command, mode)
    if usage is None and "profile" in body and not (isinstance(body["profile"], str) and body["profile"]):
        usage = reply.problem("profile", "profile must be a profile name")
    if usage is not None:
        return reply.build(command, reply.BAD_INPUT, problems=[usage]), reply.BAD_INPUT
    try:
        profile = config.resolve(body.get("profile"), os.environ.get("ATLAS_PROFILE"))
    except config.NotSetUp as err:
        if command == "status":
            return status.not_set_up(err.item(), host)
        result = {"needs_action": [err.item()]}
        steps = [reply.next_step(f"run `{config.SETUP_SKILL}`", {"skill": config.SETUP_SKILL})]
        return reply.build(command, reply.NOT_SET_UP, result=result, next=steps), reply.NOT_SET_UP
    word = command.partition(" ")[0]
    if word == "status":
        return status.run(profile, mode == "detail", host)
    try:
        store = host.open_store(profile.store)
    except StoreNewer:
        problems = [reply.problem("store", NEWER_THAN_CODE)]
        return reply.build(command, reply.FAILED, problems=problems), reply.FAILED
    except StoreFailed as err:
        problems = [reply.problem("store", f"the store cannot be opened: {err.detail}")]
        return reply.build(command, reply.FAILED, problems=problems), reply.FAILED
    try:
        if word == "inbox":
            return inbox.run(command.partition(" ")[2], body, profile, store)
        if word == "add" and mode is None:
            return add.run(body, profile, store, host)
        if word == "add" and mode == "reread":
            return reread.run(body, profile, store, host)
        if word == "add" and mode == "redo":
            return redo.run(body, profile, store, host)
        if word == "find":
            return search.run(command, mode, body, profile, store, host)
        if word == "ask":
            if "topic" in body or "whats_new" in body:
                return catchup.run(body, profile, store, host)
            return answer.run(body, profile, store, host)
        if word == "note":
            return notes.run_note(body, profile, store)
        if word in ("archive", "restore"):
            return notes.run_archive(word, body, profile, store)
        if word == "topic":
            return topics.run(command.partition(" ")[2], body, profile, store, host)
        if word == "plan":
            return plans.run(command.partition(" ")[2], body, profile, store)
    except StoreFailed as err:
        problems = [reply.problem("store", f"the store failed: {err.detail}")]
        return reply.build(command, reply.FAILED, problems=problems), reply.FAILED
    finally:
        store.close()
    problems = [reply.problem("command", f'"{word}" is not available in this Atlas build yet')]
    return reply.build(command, reply.FAILED, problems=problems), reply.FAILED
