"""``inbox add`` and ``inbox list``: links kept for later, unsummarized.

``inbox add`` takes ``{"add": [links]}``. Each link is cleaned; one that cannot
be is a problem and the others go on. A link already in the inbox, or already
held by a stored source, is reported and not added. The links left are one
change of kind ``inbox_add`` under the approval rules; it makes no paid call.
A link leaves the inbox when a source comes to hold it (``identity``).

``inbox list`` takes no field and lists every inbox link, oldest first.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from atlas.core import approvals, identity, reply, spend
from atlas.core.config import Profile
from atlas.store import InboxRecord, Store

ORIGIN = "inbox add"
_ADD_FIELDS = {"profile", "approval", "add"}
_LIST_FIELDS = {"profile"}


def _unknown(body: Mapping[str, Any], allowed: set[str]) -> dict[str, Any] | None:
    extra = sorted(set(body) - allowed)
    if not extra:
        return None
    return reply.problem(extra[0], f'"{extra[0]}" is not a field of this command; it takes {", ".join(sorted(allowed))}')


def _bad(command: str, problem: dict[str, Any]) -> tuple[dict[str, Any], int]:
    return reply.build(command, reply.BAD_INPUT, problems=[problem]), reply.BAD_INPUT


def run(action: str, body: Mapping[str, Any], profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    """Answer ``inbox <action>`` on the opened store."""
    if action == "list":
        return _list(body, store)
    if action == "add":
        return _add(body, profile, store)
    return _bad("inbox", reply.problem("action", 'inbox takes the action "add" or "list"'))


def _list(body: Mapping[str, Any], store: Store) -> tuple[dict[str, Any], int]:
    command = "inbox list"
    unknown = _unknown(body, _LIST_FIELDS)
    if unknown is not None:
        return _bad(command, unknown)
    rows = store.inbox()
    result = {
        "count": len(rows),
        "links": [{"link": row.link, "added": identity.date(row.added_at), "origin": row.origin} for row in rows],
    }
    label = "add any of these links to summarize it" if rows else "the inbox is empty"
    steps = [reply.next_step(label, {"stop": True})]
    return reply.build(command, reply.DONE, result=result, next=steps), reply.DONE


def _add(body: Mapping[str, Any], profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    command = "inbox add"
    unknown = _unknown(body, _ADD_FIELDS)
    if unknown is not None:
        return _bad(command, unknown)
    given = body.get("add")
    if not isinstance(given, list) or not given or not all(isinstance(link, str) for link in given):
        return _bad(command, reply.problem("add", "add must be a non-empty list of links"))

    items: list[dict[str, str]] = []
    problems: list[dict[str, Any]] = []
    to_add: list[str] = []
    for link in given:
        cleaned = identity.clean(link)
        if cleaned is None:
            problems.append(reply.problem("add", "not a link Atlas can read: give a full http or https link", link))
            continue
        if cleaned in to_add or store.in_inbox(cleaned):
            items.append({"link": cleaned, "result": "already in the inbox"})
            continue
        stored = store.source_for_link(cleaned)
        if stored is not None:
            items.append({"link": cleaned, "result": f"already stored as {stored.source.key_link}"})
            continue
        to_add.append(cleaned)
        items.append({"link": cleaned, "result": "added to the inbox"})

    if to_add:
        count = len(to_add)
        question = f"Keep {to_add[0]} in the inbox?" if count == 1 else f"Keep these {count} links in the inbox: {', '.join(to_add)}?"
        change = approvals.Change(command="inbox add", mode=None, body=body, kind="inbox_add", question=question, links=to_add)
        verdict = approvals.check(change, profile, None)
        if isinstance(verdict, approvals.Refused):
            return _bad(command, verdict.problem)
        if isinstance(verdict, approvals.Stop):
            return reply.build(command, reply.NEEDS_DECISION, decisions=[verdict.decision]), reply.NEEDS_DECISION
        now = spend.local_now()
        with store.transaction():
            for link in to_add:
                store.add_inbox(InboxRecord(link, spend.stamp(now), ORIGIN))
            approvals.record(store, change, verdict, now)

    result = {"added": len(to_add), "items": items}
    steps = [reply.next_step("review the inbox with `inbox list`", {"stop": True})]
    return reply.build(command, reply.DONE, result=result, problems=problems, next=steps), reply.DONE
