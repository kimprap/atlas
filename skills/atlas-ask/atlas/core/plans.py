"""``plan``: reviewed research plans and their items (spec 4.8 and 4.12; ticket 06 section 6 item 4).

- ``save`` (``topic``, ``text``, ``items``, ``review``): one change of kind ``plan_start`` whose one name target is the
  topic's name and whose question is ``topics.plan_question``, the question ``topic create`` asks, so the plan's one
  confirm covers both: each returns its own decision and writes its own ``approvals`` row. A call with no approval
  returns its decision before the topic is looked up, so the caller can collect both decisions before the topic
  exists; when the confirmed call applies, a topic that is not stored is exit 1 "not stored; create it first". The
  ``review`` is required, and its reviewed text is what is stored (``text`` is the plan as the agent wrote it).
  ``items`` are ``{kind, text}`` with ``kind`` one of ``ITEM_KINDS``; each starts open.
- ``mark`` (``plan``, ``item``, ``state``): sets one item ``done`` or ``skipped``. No stop and no ``approvals`` row.
- ``show`` (``topic?``): plans, newest first, each with its cross-check status, run, reviewed text and open items.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from atlas.core import approvals, identity, reply, spend
from atlas.core.config import Profile
from atlas.core.topics import bad, not_stored, parse_review, plan_question, stop, text, unknown_field
from atlas.store import PlanItem, PlanRecord, Store, StoredPlan

ITEM_KINDS = ("question", "search", "source", "page")
MARK_STATES = ("done", "skipped")
_FIELDS = {
    "save": {"topic", "text", "items", "review", "approval"},
    "mark": {"plan", "item", "state"},
    "show": {"topic"},
}


def _count(value: Any) -> bool:
    return type(value) is int and value >= 1


def shown(plan: StoredPlan, topic: str) -> dict[str, Any]:
    """A plan as replies show it, with its open items and how many are done and skipped."""
    items = plan.items
    return {
        "plan": plan.id,
        "topic": topic,
        "saved": identity.date(plan.plan.saved_at),
        "cross_check": plan.plan.cross_check,
        "run": plan.plan.run,
        "reviewers": list(plan.plan.reviewers),
        "changes": plan.plan.changes,
        "text": plan.plan.text,
        "open_items": [{"item": item.ord, "kind": item.item.kind, "text": item.item.text} for item in items if item.state == "open"],
        "done": sum(1 for item in items if item.state == "done"),
        "skipped": sum(1 for item in items if item.state == "skipped"),
    }


def run(action: str, body: Mapping[str, Any], profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    """Answer ``plan <action>`` on the opened store."""
    if action not in _FIELDS:
        return bad("plan", reply.problem("action", f'plan takes one of the actions {", ".join(_FIELDS)}'))
    command = f"plan {action}"
    problem = unknown_field(body, _FIELDS[action])
    if problem is not None:
        return bad(command, problem)
    if action == "save":
        return _save(command, body, profile, store)
    if action == "mark":
        return _mark(command, body, store)
    return _show(command, body, store)


def _items(value: Any) -> list[PlanItem] | dict[str, Any]:
    kinds = ", ".join(ITEM_KINDS)
    if not isinstance(value, list) or not value:
        return reply.problem("items", f"items must be a non-empty list of {{kind, text}}, kind one of {kinds}")
    found = []
    for n, item in enumerate(value, 1):
        kind, words = (item.get("kind"), text(item.get("text"))) if isinstance(item, Mapping) and set(item) == {"kind", "text"} else (None, None)
        if kind not in ITEM_KINDS or words is None:
            return reply.problem("items", f"item {n} must be {{kind, text}} with kind one of {kinds} and non-empty text")
        found.append(PlanItem(kind, words))
    return found


def _save(command: str, body: Mapping[str, Any], profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    name = text(body.get("topic"))
    if name is None:
        return bad(command, reply.problem("topic", "topic must be a topic name"))
    if text(body.get("text")) is None:
        return bad(command, reply.problem("text", "text must be the plan as the agent wrote it, non-empty"))
    items = _items(body.get("items"))
    if isinstance(items, dict):
        return bad(command, items)
    if "review" not in body:
        return bad(command, reply.problem("review", "a plan is saved with its review: send the review of the plan"))
    review = parse_review(body["review"])
    if isinstance(review, dict):
        return bad(command, review)
    change = approvals.Change(command=command, mode=None, body=body, kind="plan_start", question=plan_question(name), names=[name])
    verdict = approvals.check(change, profile, None)
    if isinstance(verdict, approvals.Refused):
        return bad(command, verdict.problem)
    if isinstance(verdict, approvals.Stop):
        return stop(command, verdict)
    topic = store.topic(name)
    if topic is None:
        return not_stored(command, "topic", name)
    now = spend.local_now()
    record = PlanRecord(review.text, review.cross_check, review.reviewers, review.run, review.changes, spend.stamp(now))
    with store.transaction():
        plan_id = store.add_plan(topic.id, record, items)
        approvals.record(store, change, verdict, now)
    saved = store.plan(plan_id)
    assert saved is not None
    steps = [reply.next_step("research the open items, marking each with `plan mark`, then draft with `topic draft`", {"stop": True})]
    return reply.build(command, reply.DONE, result={"plan": shown(saved, topic.name), "result": "saved"}, next=steps), reply.DONE


def _mark(command: str, body: Mapping[str, Any], store: Store) -> tuple[dict[str, Any], int]:
    plan_id, number, state = body.get("plan"), body.get("item"), body.get("state")
    if not _count(plan_id):
        return bad(command, reply.problem("plan", "plan must be the plan number `plan show` gives"))
    if not _count(number):
        return bad(command, reply.problem("item", "item must be the item number `plan show` gives"))
    if state not in MARK_STATES:
        return bad(command, reply.problem("state", f'state must be "{MARK_STATES[0]}" or "{MARK_STATES[1]}"'))
    plan = store.plan(plan_id)
    if plan is None:
        problems = [reply.problem("plan", f"no plan {plan_id} is stored")]
        return reply.build(command, reply.FAILED, result={"plan": plan_id, "result": "not stored"}, problems=problems), reply.FAILED
    item = next((item for item in plan.items if item.ord == number), None)
    if item is None:
        problems = [reply.problem("item", f"plan {plan_id} has no item {number}")]
        return reply.build(command, reply.FAILED, result={"plan": plan_id, "result": "no such item"}, problems=problems), reply.FAILED
    store.set_plan_item_state(plan_id, number, state, spend.stamp(spend.local_now()))
    marked = store.plan(plan_id)
    assert marked is not None
    still_open = sum(1 for other in marked.items if other.state == "open")
    result = {"plan": plan_id, "item": {"item": number, "kind": item.item.kind, "text": item.item.text, "state": state}, "open": still_open}
    label = "do the next open item, then mark it with `plan mark`" if result["open"] else "every item is marked; draft the topic with `topic draft`"
    return reply.build(command, reply.DONE, result=result, next=[reply.next_step(label, {"stop": True})]), reply.DONE


def _show(command: str, body: Mapping[str, Any], store: Store) -> tuple[dict[str, Any], int]:
    names = {topic.id: topic.name for topic in store.topics()}
    if "topic" in body:
        name = text(body["topic"])
        if name is None:
            return bad(command, reply.problem("topic", "topic must be a topic name"))
        topic = store.topic(name)
        if topic is None:
            return not_stored(command, "topic", name)
        found = store.plans(topic.id)
    else:
        found = store.plans()
    plans = [shown(plan, names[plan.topic_id]) for plan in found]
    label = "do a plan's open items, marking each with `plan mark`" if any(plan["open_items"] for plan in plans) else "save a plan with `plan save` once Reconcile has reviewed it"
    return reply.build(command, reply.DONE, result={"plans": plans}, next=[reply.next_step(label, {"stop": True})]), reply.DONE
