"""``ask`` with ``whats_new: true`` or ``topic``: what is new for the topics the user follows (spec 4.12; ticket 17 section 2).

``whats_new`` takes every followed, unarchived topic; ``topic`` (a name) takes that one stored, unarchived topic, followed
or not. Each topic is searched, one after the other, for the sources first seen after its agreed version's ``saved_at``
or its ``reviewed_up_to``, whichever is later (a topic with neither has no lower bound): BM25 over the brief as given
(no rewrite call), ranked by Jev, else by ``atlas_rerank``, through ``search.search``; each search writes one query
record (op ``ask``). The topic's set is the sources found plus its open marks: marks add sources and order the
topics (marked first) and never remove one.

An ``atlas_answer`` call (``answer.catch_up``) runs for a topic whose set is not empty, over its marked sources first and
then the found ones, at most 10 (every marked one when there are more). A topic whose set equals the set its last
catch-up answered with no conclusion change skips the call and counts as no change. Two or more answer calls make the
catch-up a batch for the window guard, checked before each call; the cap is checked as for every paid command, so a limit
stops it with a ``cap`` or ``window`` decision that states how many topics are done and not started. One failed answer
leaves that topic unanswered (a problem, ``unanswered``) and does not stop the others.

Each answered topic stores one JSON value in ``topics.last_catchup``: ``{"changed", "sources", "named", "at"}``, its
verdict, the ids of its set and the ids of the sources its answer's claims name; never the answer text. The reply lists
the conclusion-changing topics first (``changed``), then the count and names of the topics whose evidence changes no
conclusion (``no_change``), then the quiet ones (``quiet``), and its ``next`` offers "save as version N+1" and
"nothing to save" for the topics shown.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from atlas import ports
from atlas.core import answer, marks, reply, search, spend, summarize, topics
from atlas.core.config import Profile
from atlas.store import MarkRecord, SourceRecord, Store, TopicRecord

COMMAND = "ask"
GATE_KINDS = (spend.CAP, spend.WINDOW)


@dataclass
class Work:
    """One topic's catch-up: what it is, what was found for it and what its marks add."""

    topic: TopicRecord
    agreed: tuple[int, str] | None
    found: search.Searched
    marked: list[MarkRecord]

    def ids(self) -> list[int]:
        """The topic's set: the sources found and the sources its marks name, by id."""
        return sorted({*self.found.ids, *(mark.source_id for mark in self.marked)})


@dataclass
class Caught:
    """What a catch-up has so far: the topics in each part of the reply."""

    changed: list[dict[str, Any]] = field(default_factory=list)
    no_change: list[str] = field(default_factory=list)
    quiet: list[str] = field(default_factory=list)
    unanswered: list[dict[str, str]] = field(default_factory=list)
    problems: list[dict[str, Any]] = field(default_factory=list)

    def result(self, not_started: int | None = None) -> dict[str, Any]:
        found: dict[str, Any] = {
            "changed": self.changed,
            "no_change": {"count": len(self.no_change), "topics": self.no_change},
            "quiet": {"count": len(self.quiet), "topics": self.quiet},
            "unanswered": self.unanswered,
            "summary": self.summary(),
        }
        if not_started is not None:
            found["not_started"] = not_started
        return found

    def summary(self) -> str:
        def topics_of(count: int) -> str:
            return f"{count} topic" + ("" if count == 1 else "s")

        return (
            f"{topics_of(len(self.changed))} with evidence that changes a conclusion; "
            f"{topics_of(len(self.no_change))} whose evidence changes no conclusion; "
            f"{topics_of(len(self.quiet))} quiet"
        )


def _about(topic: TopicRecord, problem: Mapping[str, Any]) -> dict[str, Any]:
    """A problem raised while working on ``topic``, with its name in front so a catch-up over many topics stays readable."""
    return reply.problem(problem["field"], f'{topic.name}: {problem["problem"]}', problem["link"])


def _since(topic: TopicRecord, agreed_saved: str | None) -> str | None:
    stamps = [stamp for stamp in (agreed_saved, topic.reviewed_up_to) if stamp]
    return max(stamps) if stamps else None


def _verdict(text: str | None) -> dict[str, Any] | None:
    """A topic's last catch-up verdict as stored, or ``None`` when there is none or it is not of the stored shape."""
    if text is None:
        return None
    try:
        value = json.loads(text)
    except ValueError:
        return None
    if isinstance(value, dict) and isinstance(value.get("changed"), bool) and isinstance(value.get("sources"), list):
        return value
    return None


def _links(store: Store, ids: list[int]) -> list[str]:
    return [store.source_record(source_id).key_link for source_id in ids]


def _chosen(work: Work) -> tuple[list[int], list[int]]:
    """The sources an answer reads: the marked ones (highest P first) and then the found ones, at most
    ``answer.ANSWERED`` (every marked one when there are more). Returns them and the marked ones' ids."""
    marked = [mark.source_id for mark in sorted(work.marked, key=lambda mark: (-mark.p, mark.source_id))]
    room = max(0, answer.ANSWERED - len(marked))
    return marked + [source_id for source_id in work.found.ids if source_id not in marked][:room], marked


def _next(caught: Caught) -> list[dict[str, Any]]:
    steps = []
    if caught.changed:
        saves = ", ".join(f'"{item["topic"]}" as version {item["next_version"]}' for item in caught.changed)
        names = ", ".join(f'"{item["topic"]}"' for item in caught.changed)
        steps.append(reply.next_step(f"save as the next version: {saves} (Atlas drafts it with `topic draft`, then asks before `topic save`)", {"stop": True}))
        steps.append(reply.next_step(f"nothing to save for {names}: `topic nothing_to_save` stores today's date and clears their marks", {"stop": True}))
    if caught.unanswered:
        names = ", ".join(f'"{item["topic"]}"' for item in caught.unanswered)
        steps.append(reply.next_step(f"ask again for the topics that could not be answered: {names}", {"stop": True}))
    if not steps:
        steps.append(reply.next_step("add sources, or check again later with `ask`", {"stop": True}))
    return steps


def _answer_one(deps: summarize.Deps, work: Work, caught: Caught) -> None:
    """Answer one topic, record its verdict and file it under the part of the reply it belongs to."""
    store, topic = deps.store, work.topic
    ids, marked = _chosen(work)
    top: list[SourceRecord] = [store.source_record(source_id) for source_id in ids]
    problems: list[dict[str, Any]] = []
    got = answer.catch_up(deps, topic.name, topic.brief, work.agreed, top, ids, set(marked), problems)
    caught.problems += [_about(topic, problem) for problem in problems]
    if isinstance(got, str):
        caught.unanswered.append({"topic": topic.name, "why": got})
        caught.problems.append(reply.problem("answer", f"{topic.name}: {got}"))
        return
    verdict = {"changed": got.changes, "sources": work.ids(), "named": list(got.named), "at": spend.stamp(deps.clock())}
    store.set_topic_catchup(topic.id, json.dumps(verdict))
    if not got.changes:
        caught.no_change.append(topic.name)
        return
    shown = got.shown
    version = work.agreed[0] if work.agreed else None
    caught.changed.append(
        {
            "topic": topic.name,
            "version": version,
            "next_version": (version or 0) + 1,
            "marked": _links(store, marked),
            "new": _links(store, [source_id for source_id in work.found.ids if source_id not in marked]),
            "answer": shown["answer"],
            "claims": shown["claims"],
            "labels": shown["labels"],
            "disagreements": shown["disagreements"],
            "gaps": shown["gaps"],
            "model_view": shown["model_view"],
            "writing_model": shown["writing_model"],
        }
    )


def run(body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``ask`` with ``whats_new`` or ``topic`` on the opened store."""
    forms = [name for name in answer.FORMS if name in body]
    if len(forms) != 1:
        return search.bad(COMMAND, reply.problem("body", "ask takes exactly one of question, source, topic or whats_new"))
    form = forms[0]
    extra = sorted(set(body) - {"profile", "approval", form})
    if extra:
        return search.bad(COMMAND, reply.problem(extra[0], f'"{extra[0]}" is not a field of ask with {form}; it takes {form}'))
    if form == "whats_new":
        if body["whats_new"] is not True:
            return search.bad(COMMAND, reply.problem("whats_new", "whats_new must be true"))
        chosen = marks.followed(store)
    else:
        name = topics.text(body["topic"])
        if name is None:
            return search.bad(COMMAND, reply.problem("topic", "topic must be a topic name"))
        topic = store.topic(name)
        if topic is None:
            return topics.not_stored(COMMAND, "topic", name)
        if topic.archived_at is not None:
            problem = reply.problem("topic", f"archived {topics.date(topic.archived_at)}; restore it first")
            return reply.build(COMMAND, reply.FAILED, result={"topic": topic.name, "result": "archived"}, problems=[problem]), reply.FAILED
        chosen = [topic]
    caught = Caught()
    if not chosen:
        steps = [reply.next_step("create a topic with `topic create`, or follow one with `topic follow`", {"stop": True})]
        return reply.build(COMMAND, reply.DONE, result=caught.result(), next=steps), reply.DONE
    request = search.Request(chosen[0].brief, chosen[0].brief, (chosen[0].brief,), None)
    stopped = search.gate(COMMAND, body, request, profile, store, host, (answer.ANSWER,), GATE_KINDS)
    if stopped is not None:
        return stopped
    deps = summarize.Deps(host, profile, store, COMMAND)
    try:
        queue = _search(deps, chosen, caught)
        guard = spend.Guard(store, profile, host, (answer.ANSWER,), paid=True, batch=len(queue) >= 2)
        if "approval" in body:
            guard.continue_past({reply.approved_kind(COMMAND, None, body, GATE_KINDS) or spend.CAP})
        for done, work in enumerate(queue):
            limit = guard.check(done, len(queue) - done)
            if limit is not None:
                decision = search.limit_decision(COMMAND, body, limit)
                answered = reply.build(COMMAND, reply.NEEDS_DECISION, result=caught.result(len(queue) - done), problems=caught.problems, decisions=[decision])
                return answered, reply.NEEDS_DECISION
            _answer_one(deps, work, caught)
    except ports.RoleMissing as err:
        return search.role_missing(COMMAND, host, err.role)
    code = reply.FAILED if queue and len(caught.unanswered) == len(queue) else reply.DONE
    return reply.build(COMMAND, code, result=caught.result(), problems=caught.problems, next=_next(caught)), code


def _search(deps: summarize.Deps, chosen: list[TopicRecord], caught: Caught) -> list[Work]:
    """Search each topic and sort it into ``caught`` (quiet, or no change by its last verdict) or the queue of topics to
    answer, marked ones first. ``ports.RoleMissing`` passes through."""
    store = deps.store
    queue: list[Work] = []
    for topic in chosen:
        versions = store.versions(topic.id)
        agreed = (versions[-1].n, versions[-1].version.text) if versions else None
        since = _since(topic, versions[-1].version.saved_at if versions else None)
        request = search.Request(topic.brief, topic.brief, (topic.brief,), None)
        searched = search.search(deps, request, since)
        search.record_query(deps, COMMAND, request, searched)
        caught.problems += [_about(topic, problem) for problem in searched.problems]
        work = Work(topic, agreed, searched, store.open_marks(topic.id))
        ids = work.ids()
        prior = _verdict(topic.last_catchup)
        if not ids:
            caught.quiet.append(topic.name)
        elif prior is not None and not prior["changed"] and prior["sources"] == ids:
            caught.no_change.append(topic.name)
        else:
            queue.append(work)
    queue.sort(key=lambda work: (not work.marked, work.topic.id))
    return queue
