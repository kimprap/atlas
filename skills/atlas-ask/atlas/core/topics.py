"""``topic``: topics, their drafts and their saved versions (spec 4.8 and 4.12; ticket 06 section 6; ticket 17 section 2).

A topic is a name (unique, trimmed and compared case-insensitively, archived topics included) with a brief. Every
action that needs a stored topic and finds none is exit 1 "not stored; create it first".

- ``create`` (``name``, ``brief``): a new followed topic. One change of kind ``plan_start`` whose one name target is
  the topic's name; ``plans.save`` asks the same question, so the plan's one confirm covers both. A name already
  stored changes nothing and asks nothing.
- ``draft`` (``name``, ``context?``): stores nothing and asks no approval; ``answer.draft`` searches the topic's
  brief and writes the draft revision.
- ``save`` (``name``, ``draft``, ``review``): always returns a ``version_save`` decision first, whatever the
  ``confirm`` settings say and whatever approval comes with it, because the stop is fixed. A ``confirm`` approval of
  that decision with a ``review`` stores the next numbered version: the review's reviewed text, the draft's writer
  model and thinking, the review's cross-check status, reviewers, run, changes and diff, a copy of each claim the
  draft cites as it is then (text and quote texts), the clearing of the topic's marks and one ``approvals`` row.
  A confirmed call with no ``review`` is bad input. ``review`` is produced after the decision is returned, so the
  decision id leaves it out (``reply.decision_id``).
- ``follow`` and ``unfollow`` (``name``): their own change kinds; a topic already in the asked state changes nothing
  and asks nothing.
- ``nothing_to_save`` (``name``): stores ``reviewed_up_to`` (the time of the call) and clears the topic's marks. It
  creates no version, asks nothing and writes no ``approvals`` row: the user's pick of its Next line is its confirm.
- ``list``: every topic, archived ones included.

``Review`` is the parsed ``review`` of ``topic save`` and ``plan save``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from atlas import ports
from atlas.core import answer, approvals, identity, reply, search, spend
from atlas.core.config import Profile
from atlas.store import ApprovalRecord, Store, TopicRecord, VersionClaim, VersionRecord

NOT_STORED = "not stored; create it first"
COMPLETE = "complete"
NOT_CROSS_CHECKED = "not_cross_checked"
_REVIEW_FIELDS = {"status", "reason", "run", "reviewers", "changes", "diff", "text"}
_FIELDS = {
    "create": {"name", "brief", "approval"},
    "draft": {"name", "context", "approval"},
    "save": {"name", "draft", "review", "approval"},
    "follow": {"name", "approval"},
    "unfollow": {"name", "approval"},
    "nothing_to_save": {"name"},
    "list": set(),
}


@dataclass(frozen=True)
class Review:
    """A valid ``review``: the reviewed text, the cross-check status it stores, and the review's own fields as given."""

    text: str
    cross_check: str
    reviewers: tuple[str, ...]
    run: str | None
    changes: str | None
    diff: str | None


def bad(command: str, *problems: dict[str, Any]) -> tuple[dict[str, Any], int]:
    return reply.build(command, reply.BAD_INPUT, problems=list(problems)), reply.BAD_INPUT


def unknown_field(body: Mapping[str, Any], allowed: set[str]) -> dict[str, Any] | None:
    """The problem when ``body`` holds a field outside ``allowed`` and ``profile``, else ``None``."""
    extra = sorted(set(body) - allowed - {"profile"})
    if not extra:
        return None
    names = ", ".join(sorted(allowed))
    return reply.problem(extra[0], f'"{extra[0]}" is not a field of this command; it takes {names}')


def text(value: Any) -> str | None:
    """``value`` trimmed, or ``None`` when it is not non-empty text."""
    if not isinstance(value, str):
        return None
    return value.strip() or None


def not_stored(command: str, field: str, name: str) -> tuple[dict[str, Any], int]:
    problems = [reply.problem(field, NOT_STORED)]
    return reply.build(command, reply.FAILED, result={"topic": name, "result": "not stored"}, problems=problems), reply.FAILED


def date(stamp: str | None) -> str | None:
    return None if stamp is None else identity.date(stamp)


def plan_question(name: str) -> str:
    """The one question of the plan's confirm, asked by ``topic create`` and ``plan save`` alike."""
    return f'Start the research plan for the topic "{name}": create the topic and save its reviewed plan?'


def shown(store: Store, topic: TopicRecord) -> dict[str, Any]:
    """A topic as replies show it: its agreed version is the latest one saved."""
    versions = store.versions(topic.id)
    latest = versions[-1] if versions else None
    return {
        "name": topic.name,
        "brief": topic.brief,
        "followed": topic.followed,
        "archived": date(topic.archived_at),
        "reviewed_up_to": date(topic.reviewed_up_to),
        "version": None if latest is None else latest.n,
        "version_saved": None if latest is None else date(latest.version.saved_at),
    }


def _optional_text(value: Any, name: str) -> str | None | dict[str, Any]:
    """``value`` as stored text (``None`` when absent), or the problem when it is not text."""
    if value is None:
        return None
    if not isinstance(value, str):
        return reply.problem(f"review.{name}", f"review.{name} must be text")
    return value


def parse_review(value: Any) -> Review | dict[str, Any]:
    """The ``review`` Reconcile's run gave, or the problem that makes it bad input.

    ``status`` is ``complete`` (it needs ``run``, ``reviewers`` and ``changes``) or ``not_cross_checked`` (it needs
    ``reason``); the reviewed ``text`` is always required and is stored as given.
    """
    if not isinstance(value, Mapping):
        return reply.problem("review", "review must be an object with status, text and the review's fields")
    extra = sorted(set(value) - _REVIEW_FIELDS)
    if extra:
        return reply.problem("review", f'"{extra[0]}" is not a field of review; it takes {", ".join(sorted(_REVIEW_FIELDS))}')
    status = value.get("status")
    if status not in (COMPLETE, NOT_CROSS_CHECKED):
        return reply.problem("review.status", f'review.status must be "{COMPLETE}" or "{NOT_CROSS_CHECKED}"')
    reviewed = value.get("text")
    if not isinstance(reviewed, str) or not reviewed.strip():
        return reply.problem("review.text", "review.text must be the reviewed text, non-empty")
    given: dict[str, str | None] = {}
    for name in ("run", "changes", "diff"):
        found = _optional_text(value.get(name), name)
        if isinstance(found, dict):
            return found
        given[name] = found
    reviewers = value.get("reviewers")
    if reviewers is not None and not (isinstance(reviewers, list) and all(text(item) for item in reviewers)):
        return reply.problem("review.reviewers", "review.reviewers must be a list of reviewer names")
    names = tuple(item.strip() for item in reviewers or ())
    if status == COMPLETE:
        if not text(given["run"]):
            return reply.problem("review.run", "a complete review needs its run")
        if not names:
            return reply.problem("review.reviewers", "a complete review needs its reviewers")
        if given["changes"] is None:
            return reply.problem("review.changes", "a complete review needs its changes (empty text when it made none)")
        cross_check = COMPLETE
    else:
        reason = text(value.get("reason"))
        if reason is None:
            return reply.problem("review.reason", "a review that is not cross-checked needs its reason")
        cross_check = f"not cross-checked: {reason}"
    return Review(reviewed, cross_check, names, given["run"], given["changes"], given["diff"])


def shown_review(review: Review) -> dict[str, Any]:
    """A review's stored fields as replies show them."""
    return {
        "cross_check": review.cross_check,
        "reviewers": list(review.reviewers),
        "run": review.run,
        "changes": review.changes,
        "diff": review.diff,
    }


def stop(command: str, verdict: approvals.Stop) -> tuple[dict[str, Any], int]:
    return reply.build(command, reply.NEEDS_DECISION, decisions=[verdict.decision]), reply.NEEDS_DECISION


def _name(command: str, body: Mapping[str, Any], field: str = "name") -> str | tuple[dict[str, Any], int]:
    name = text(body.get(field))
    if name is None:
        return bad(command, reply.problem(field, f"{field} must be a topic name"))
    return name


def run(action: str, body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``topic <action>`` on the opened store."""
    if action not in _FIELDS:
        return bad("topic", reply.problem("action", f'topic takes one of the actions {", ".join(_FIELDS)}'))
    command = f"topic {action}"
    problem = unknown_field(body, _FIELDS[action])
    if problem is not None:
        return bad(command, problem)
    if action == "list":
        return _list(store)
    name = _name(command, body)
    if not isinstance(name, str):
        return name
    if action == "create":
        return _create(command, body, name, profile, store)
    topic = store.topic(name)
    if topic is None:
        return not_stored(command, "name", name)
    if action == "draft":
        return _draft(command, body, topic, profile, store, host)
    if action == "save":
        return _save(command, body, topic, store)
    if action == "nothing_to_save":
        return _nothing_to_save(command, topic, store)
    return _follow(command, body, action == "follow", topic, profile, store)


def _list(store: Store) -> tuple[dict[str, Any], int]:
    found = [shown(store, topic) for topic in store.topics()]
    label = "draft one with `topic draft`, or check what is new with `ask`" if found else "create a topic with `topic create`"
    return reply.build("topic list", reply.DONE, result={"topics": found}, next=[reply.next_step(label, {"stop": True})]), reply.DONE


def _create(command: str, body: Mapping[str, Any], name: str, profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    brief = text(body.get("brief"))
    if brief is None:
        return bad(command, reply.problem("brief", "brief must say what the topic is about"))
    held = store.topic(name)
    if held is not None:
        problems = [reply.problem("name", "already stored; work on that topic, or name another")]
        result = {"topic": shown(store, held), "result": "already stored"}
        return reply.build(command, reply.DONE, result=result, problems=problems), reply.DONE
    change = approvals.Change(command=command, mode=None, body=body, kind="plan_start", question=plan_question(name), names=[name])
    verdict = approvals.check(change, profile, None)
    if isinstance(verdict, approvals.Refused):
        return bad(command, verdict.problem)
    if isinstance(verdict, approvals.Stop):
        return stop(command, verdict)
    now = spend.local_now()
    with store.transaction():
        topic_id = store.add_topic(name, brief)
        approvals.record(store, change, verdict, now)
    topic = next(topic for topic in store.topics() if topic.id == topic_id)
    steps = [reply.next_step("save its reviewed research plan with `plan save`, then add the sources you find and draft with `topic draft`", {"stop": True})]
    return reply.build(command, reply.DONE, result={"topic": shown(store, topic), "result": "created"}, next=steps), reply.DONE


def _follow(command: str, body: Mapping[str, Any], following: bool, topic: TopicRecord, profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    if topic.followed == following:
        label = "check what is new with `ask`" if following else "follow it again with `topic follow`"
        result = {"topic": shown(store, topic), "result": "already followed" if following else "not followed"}
        return reply.build(command, reply.DONE, result=result, next=[reply.next_step(label, {"stop": True})]), reply.DONE
    if following:
        question = f'Follow the topic "{topic.name}"? The catch-up searches it for new sources.'
    else:
        question = f'Unfollow the topic "{topic.name}"? The catch-up leaves it out until you follow it again; its versions stay.'
    kind = "follow" if following else "unfollow"
    change = approvals.Change(command=command, mode=None, body=body, kind=kind, question=question, names=[topic.name])
    verdict = approvals.check(change, profile, None)
    if isinstance(verdict, approvals.Refused):
        return bad(command, verdict.problem)
    if isinstance(verdict, approvals.Stop):
        return stop(command, verdict)
    now = spend.local_now()
    with store.transaction():
        store.set_topic_followed(topic.id, following)
        approvals.record(store, change, verdict, now)
    changed = next(found for found in store.topics() if found.id == topic.id)
    label = "check what is new with `ask`" if following else "follow it again with `topic follow`"
    result = {"topic": shown(store, changed), "result": "followed" if following else "unfollowed"}
    return reply.build(command, reply.DONE, result=result, next=[reply.next_step(label, {"stop": True})]), reply.DONE


def _nothing_to_save(command: str, topic: TopicRecord, store: Store) -> tuple[dict[str, Any], int]:
    at = spend.stamp(spend.local_now())
    with store.transaction():
        store.set_topic_reviewed(topic.id, at)
        cleared = store.clear_marks(topic.id, at)
    changed = next(found for found in store.topics() if found.id == topic.id)
    result = {"topic": shown(store, changed), "result": "nothing to save", "marks_cleared": cleared}
    steps = [reply.next_step("check what is new later with `ask`", {"stop": True})]
    return reply.build(command, reply.DONE, result=result, next=steps), reply.DONE


def _draft(command: str, body: Mapping[str, Any], topic: TopicRecord, profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    context = body.get("context")
    if context is not None and not isinstance(context, str):
        return bad(command, reply.problem("context", "context must be text"))
    request = search.Request(question=topic.brief, original=topic.brief, phrasings=None, context=(context or "").strip() or None)
    versions = store.versions(topic.id)
    agreed = (versions[-1].n, versions[-1].version.text) if versions else None
    save_label = f'save it as version {len(versions) + 1} of "{topic.name}": Atlas asks, and the draft is reviewed first'
    return answer.draft(command, body, request, topic.name, agreed, save_label, profile, store, host)


# save ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _Draft:
    """What a save reads of the draft: its writer and the stored claims it cites, by the source's link and position."""

    writer_model: str
    thinking: str | None
    cites: tuple[tuple[str, int], ...]


def _parse_draft(value: Any) -> _Draft | dict[str, Any]:
    if not isinstance(value, Mapping):
        return reply.problem("draft", "draft must be the draft object `topic draft` replied with")
    model, thinking, claims = value.get("writer_model"), value.get("thinking"), value.get("claims")
    if not (isinstance(model, str) and model.strip()):
        return reply.problem("draft", "draft.writer_model must name the model that wrote the draft")
    if thinking is not None and not isinstance(thinking, str):
        return reply.problem("draft", "draft.thinking must be text")
    if not isinstance(claims, list) or not all(isinstance(claim, Mapping) for claim in claims):
        return reply.problem("draft", "draft.claims must be the draft's list of claims")
    cites: list[tuple[str, int]] = []
    for claim in claims:
        listed = claim.get("cites")
        if listed is None:
            continue
        if not isinstance(listed, list):
            return reply.problem("draft", "a draft claim's cites must be a list of {link, claim}")
        for cite in listed:
            if not (isinstance(cite, Mapping) and isinstance(cite.get("link"), str) and type(cite.get("claim")) is int):
                return reply.problem("draft", "each cite of a draft claim must be {link, claim}: a source's link and a claim position")
            cites.append((cite["link"], cite["claim"]))
    return _Draft(model.strip(), thinking, tuple(dict.fromkeys(cites)))


def _copies(store: Store, cites: tuple[tuple[str, int], ...]) -> tuple[list[VersionClaim], list[dict[str, Any]]]:
    """The claims ``cites`` name as they are stored now, copied for a version, and a problem for each that is not stored."""
    copies: dict[int, VersionClaim] = {}
    problems: list[dict[str, Any]] = []
    for link, position in cites:
        source = identity.lookup(store, link)
        if source is None:
            problems.append(reply.problem("draft", "cites a source that is not stored", link))
            continue
        found = next((stored for stored in store.claims(source.id) if stored.ord == position), None)
        if found is None:
            problems.append(reply.problem("draft", f"cites claim {position}, which the source does not hold", source.key_link))
            continue
        copies.setdefault(found.id, VersionClaim(found.id, found.claim.text, tuple(quote.text for quote in found.claim.quotes)))
    return list(copies.values()), problems


def _confirmed(command: str, body: Mapping[str, Any]) -> bool | dict[str, Any]:
    """Whether the body's approval is a ``confirm`` of this save's ``version_save`` decision, or the problem with it.

    Without an approval, and with a ``request`` one, the answer is ``False``: the stop is fixed, so only the user's
    answer to the decision itself lets a version be saved."""
    if "approval" not in body:
        return False
    value = body["approval"]
    if not isinstance(value, Mapping):
        return reply.problem("approval", "approval must be an object")
    by = value.get("by")
    expected = {approvals.REQUEST: {"by", "words"}, approvals.CONFIRM: {"by", "decision", "choice", "words"}}.get(by)
    if expected is None:
        return reply.problem("approval", f'approval.by must be "{approvals.REQUEST}" or "{approvals.CONFIRM}"')
    if set(value) != expected:
        return reply.problem("approval", f"a {by} approval has exactly the fields {', '.join(sorted(expected))}")
    if not all(isinstance(value[key], str) and value[key] for key in expected):
        return reply.problem("approval", "every approval field is non-empty text")
    if by == approvals.REQUEST:
        return False
    if value["choice"] != approvals.GO:
        return reply.problem("approval", f'approval.choice "{value["choice"]}" does not go ahead; only "{approvals.GO}" is resent')
    if reply.approved_kind(command, None, body, (reply.VERSION_SAVE,)) is None:
        return reply.problem("approval", reply.OTHER_CHANGE)
    return True


def _version_decision(command: str, body: Mapping[str, Any], topic: TopicRecord, number: int, cited: int) -> dict[str, Any]:
    decision_id = reply.decision_id(command, None, body, reply.VERSION_SAVE)
    go = {"resend": {"approval": {"by": approvals.CONFIRM, "decision": decision_id, "choice": approvals.GO}}}
    claims = "no stored claim" if cited == 0 else f"copies of {cited} stored claim{'' if cited == 1 else 's'}"
    question = f'Save this draft as version {number} of the topic "{topic.name}"? The version keeps {claims}.'
    options = [
        reply.option(approvals.GO, f"yes, save it as version {number}", go),
        reply.option(approvals.STOP, "no, stop here", {"stop": True}),
    ]
    return reply.decision(command, None, body, reply.VERSION_SAVE, question, options)


def _save(command: str, body: Mapping[str, Any], topic: TopicRecord, store: Store) -> tuple[dict[str, Any], int]:
    parsed = _parse_draft(body.get("draft"))
    if isinstance(parsed, dict):
        return bad(command, parsed)
    copies, problems = _copies(store, parsed.cites)
    if problems:
        return bad(command, *problems)
    confirmed = _confirmed(command, body)
    if isinstance(confirmed, dict):
        return bad(command, confirmed)
    number = len(store.versions(topic.id)) + 1
    if not confirmed:
        decision = _version_decision(command, body, topic, number, len(copies))
        return reply.build(command, reply.NEEDS_DECISION, decisions=[decision]), reply.NEEDS_DECISION
    if "review" not in body:
        return bad(command, reply.problem("review", "a version is saved with its review: send the review of the draft with the confirm"))
    review = parse_review(body["review"])
    if isinstance(review, dict):
        return bad(command, review)
    approval = body["approval"]
    now = spend.local_now()
    at = spend.stamp(now)
    with store.transaction():
        version = VersionRecord(review.text, parsed.writer_model, parsed.thinking, review.cross_check, review.reviewers, review.run, review.changes, review.diff, at)
        number = store.add_version(topic.id, version, copies)
        cleared = store.clear_marks(topic.id, at)
        store.add_approval(ApprovalRecord(at, command, reply.VERSION_SAVE, approvals.CONFIRM, approval["words"], approval["decision"]))
    saved = {"n": number, **shown_review(review), "text": review.text, "saved": identity.date(at), "claims": len(copies)}
    result = {"topic": shown(store, topic), "version": saved, "marks_cleared": cleared, "result": f"saved version {number}"}
    steps = [reply.next_step("ask what is new on the topic later, or research what it is missing", {"stop": True})]
    return reply.build(command, reply.DONE, result=result, next=steps), reply.DONE
