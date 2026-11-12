"""Whether a change runs: the approval rules every change command obeys.

A change body may carry one ``approval``:

- ``{"by": "request", "words": <the user's message, verbatim>}``;
- ``{"by": "confirm", "decision": <decisions[].id>, "choice": "go", "words": <the user's reply, verbatim>}``.

``check`` decides each change in this order. Fixed stops always stop, whatever
the setting: the caller returns ``pick_scope``, ``summary_failed``,
``judge_setup`` and ``version_save`` decisions itself, and the cap and window
yields come from the command's ``spend.Guard``. A change whose
``confirm.<kind>`` is ``never`` runs without approval. Under ``always`` it runs
on a ``confirm`` approval, or on a ``request`` approval when the change is not
paid at scale and every target it names appears in the words (each link after
link cleanup of the links found in the words, each name; case-insensitive); a
proposal (an ``add`` carrying ``cited_in``) never runs on a ``request`` approval;
otherwise it returns a ``confirm`` decision. A confirm and a cap or window yield
on the same command merge into one decision, of the limit's kind, whose
question states the limit; going ahead on it counts as continuing past the
limit. A ``never`` change with a yield gets that yield only, so no command
stops twice. A ``confirm`` approval may name any decision this change could
return (confirm, cap or window); one naming none of them is bad input.

The caller writes one ``approvals`` row per applied change with ``record``.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from atlas.core import links, reply, spend
from atlas.core.config import CHANGE_KINDS, NEVER, Profile
from atlas.store import ApprovalRecord, Store

REQUEST = "request"
CONFIRM = "confirm"
# The ``by`` of a change that ran on its ``never`` setting with no approval.
BY_SETTING = NEVER

# Option ids: going ahead, and the stops.
GO = "go"
STOP = "stop"
RAISE_CAP = "raise_cap"
AFTER_RESET = "after_reset"

# The decision kinds a ``confirm`` approval may answer.
APPROVED_KINDS = (CONFIRM, spend.CAP, spend.WINDOW)

_LINK_RE = re.compile(r"https?://[^\s<>\"'`]+", re.IGNORECASE)
_TRAILING = ".,;:!?'\""
_CLOSERS = {")": "(", "]": "[", "}": "{"}


@dataclass(frozen=True)
class Change:
    """One change a command would make.

    ``command`` is the command word with its action (``inbox add``), ``mode`` the
    flag without dashes; ``kind`` is its confirm setting's name. ``question`` asks
    the user about this change in plain words ("Add https://example.com/a?"),
    with any batch estimate and window use. ``links`` and ``names`` are the
    targets the change names (topic names, a note's ``who``); ``paid_at_scale``
    is true for ``add --redo``, an ``add`` or ``add --reread`` reading 2 or more
    links after stored links are matched, and an "each link" or "each item"
    scope with 2 or more links. ``proposal`` is true for a change the agent proposes (an ``add`` carrying
    ``cited_in``): no ``request`` approval runs it.
    """

    command: str
    mode: str | None
    body: Mapping[str, Any]
    kind: str
    question: str
    links: Sequence[str] = ()
    names: Sequence[str] = ()
    paid_at_scale: bool = False
    proposal: bool = False

    def __post_init__(self) -> None:
        if self.kind not in CHANGE_KINDS:
            raise ValueError(f"change kind {self.kind!r} is not one of {', '.join(CHANGE_KINDS)}")

    def called(self) -> str:
        """The command as called: ``add --reread``."""
        return f"{self.command} --{self.mode}" if self.mode else self.command


@dataclass(frozen=True)
class Go:
    """The change runs; ``by``, ``words`` and ``decision_id`` go into its ``approvals`` row."""

    by: str
    words: str | None
    decision_id: str | None


@dataclass(frozen=True)
class Stop:
    """The change waits for the user: return ``decision`` with exit 4."""

    decision: dict[str, Any]


@dataclass(frozen=True)
class Refused:
    """The approval is bad input: return ``problem`` with exit 2."""

    problem: dict[str, Any]


@dataclass(frozen=True)
class _Approval:
    by: str
    words: str
    decision: str | None


def _parse(change: Change) -> _Approval | Refused | None:
    """The body's approval, ``None`` without one, or why it is bad input."""
    if "approval" not in change.body:
        return None
    value = change.body["approval"]
    if not isinstance(value, Mapping):
        return Refused(reply.problem("approval", "approval must be an object"))
    by = value.get("by")
    expected = {REQUEST: {"by", "words"}, CONFIRM: {"by", "decision", "choice", "words"}}.get(by)
    if expected is None:
        return Refused(reply.problem("approval", f'approval.by must be "{REQUEST}" or "{CONFIRM}"'))
    if set(value) != expected:
        fields = ", ".join(sorted(expected))
        return Refused(reply.problem("approval", f"a {by} approval has exactly the fields {fields}"))
    if not all(isinstance(value[key], str) and value[key] for key in expected):
        return Refused(reply.problem("approval", "every approval field is non-empty text"))
    if by == REQUEST:
        return _Approval(REQUEST, value["words"], None)
    if value["choice"] != GO:
        return Refused(reply.problem("approval", f'approval.choice "{value["choice"]}" does not go ahead; only "{GO}" is resent'))
    return _Approval(CONFIRM, value["words"], value["decision"])


def _trim(found: str) -> str:
    """Drop sentence punctuation after a link, and a closing bracket the link does not open."""
    while found:
        last = found[-1]
        if last in _TRAILING or (last in _CLOSERS and found.count(last) > found.count(_CLOSERS[last])):
            found = found[:-1]
        else:
            break
    return found


def _clean(link: str) -> str:
    try:
        return links.normalize_canonical_url(link).casefold()
    except (TypeError, ValueError):
        return link.casefold()


def links_in(words: str) -> set[str]:
    """Every link found in ``words``, after link cleanup, case-folded."""
    return {_clean(_trim(found)) for found in _LINK_RE.findall(words)}


def asked_for(change: Change, words: str) -> bool:
    """Whether ``words`` ask for ``change`` in so many words: not a proposal, not paid at scale, and every target named."""
    if change.paid_at_scale or change.proposal:
        return False
    found = links_in(words)
    folded = words.casefold()
    return all(_clean(link) in found for link in change.links) and all(
        name.casefold() in folded for name in change.names
    )


def _go_then(decision_id: str) -> dict[str, Any]:
    return {"resend": {"approval": {"by": CONFIRM, "decision": decision_id, "choice": GO}}}


def _stop_then() -> dict[str, Any]:
    return {"stop": True}


def _limit_option(limit: spend.Limit) -> dict[str, Any]:
    if limit.kind == spend.CAP:
        return reply.option(RAISE_CAP, "raise the cap yourself in config.toml", _stop_then())
    return reply.option(AFTER_RESET, f"rerun after the reset ({limit.resets})", _stop_then())


def _sentence(text: str) -> str:
    return text[:1].upper() + text[1:] + "."


def limit_decision(change: Change, limit: spend.Limit) -> dict[str, Any]:
    """The cap or window decision that stops ``change`` alone, before its first paid call or next item."""
    decision_id = reply.decision_id(change.command, change.mode, change.body, limit.kind)
    go_label = "continue anyway (this command only)" if limit.kind == spend.CAP else "continue now anyway (this batch only)"
    options = [
        reply.option(GO, go_label, _go_then(decision_id)),
        _limit_option(limit),
        reply.option(STOP, "stop here", _stop_then()),
    ]
    return reply.decision(change.command, change.mode, change.body, limit.kind, _sentence(limit.text()), options)


def confirm_decision(change: Change, limit: spend.Limit | None) -> dict[str, Any]:
    """The one decision for a change that needs a confirm, merged with ``limit`` when one applies."""
    if limit is None:
        decision_id = reply.decision_id(change.command, change.mode, change.body, CONFIRM)
        options = [
            reply.option(GO, "yes, go ahead", _go_then(decision_id)),
            reply.option(STOP, "no, stop here", _stop_then()),
        ]
        return reply.decision(change.command, change.mode, change.body, CONFIRM, change.question, options)
    decision_id = reply.decision_id(change.command, change.mode, change.body, limit.kind)
    scope = "this command" if limit.kind == spend.CAP else "this batch"
    question = f"{change.question} {_sentence(limit.text())} Going ahead continues past this limit for {scope}."
    options = [
        reply.option(GO, "yes, go ahead anyway", _go_then(decision_id)),
        _limit_option(limit),
        reply.option(STOP, "no, stop here", _stop_then()),
    ]
    return reply.decision(change.command, change.mode, change.body, limit.kind, question, options)


def check(change: Change, profile: Profile, guard: spend.Guard | None) -> Go | Stop | Refused:
    """Decide ``change`` before its first paid call; ``guard`` is ``None`` for a change that makes no paid call.

    A ``confirm`` approval of a cap or window decision marks that limit continued
    on ``guard`` for the rest of the command.
    """
    approval = _parse(change)
    if isinstance(approval, Refused):
        return approval
    confirmed = False
    if approval is not None and approval.by == CONFIRM:
        kind = reply.approved_kind(change.command, change.mode, change.body, APPROVED_KINDS)
        if kind is None:
            return Refused(reply.problem("approval", reply.OTHER_CHANGE))
        confirmed = True
        if guard is not None and kind != CONFIRM:
            guard.continue_past({kind})
    limit = guard.check() if guard is not None else None

    if profile.confirm[change.kind] == NEVER:
        if limit is not None:
            return Stop(limit_decision(change, limit))
        if approval is None:
            return Go(BY_SETTING, None, None)
        return Go(approval.by, approval.words, approval.decision)
    if confirmed or (approval is not None and asked_for(change, approval.words)):
        if limit is not None:
            return Stop(limit_decision(change, limit))
        return Go(approval.by, approval.words, approval.decision)
    return Stop(confirm_decision(change, limit))


def record(store: Store, change: Change, go: Go, now: datetime | None = None) -> None:
    """Write the one ``approvals`` row of an applied change."""
    store.add_approval(
        ApprovalRecord(
            at=spend.stamp(now or spend.local_now()),
            command=change.called(),
            change_kind=change.kind,
            by=go.by,
            words=go.words,
            decision_id=go.decision_id,
        )
    )
