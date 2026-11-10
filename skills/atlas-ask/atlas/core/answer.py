"""``ask`` with a ``question``: search, then answer from the top 10 (spec 4.10; ticket 09 items 6-10; ticket 02).

The search is ``find``'s (``search``), with its stops, fallbacks and query
record. The top 10 sources go to ``atlas_answer`` with the question and the
caller's ``context``, through the tool ``answer`` on tool choice auto with
"Answer only by calling `answer`"; a reply with no tool call gets one
same-conversation turn repeating that line. The tool gives the answer, the
claims shown (each with its source links, a label and one reason),
disagreements, gaps, the Model view and tally lines.

Code then checks the label format fail-closed: every claim must carry exactly
Sound, Doubtful or Noise and a one-line reason, or every claim is shown
unlabelled and ``labels`` says why; nothing is withheld. Labelled claims are
listed Sound, Doubtful, Noise. Backing is counted in code over the sources
searched: the claim's sources that are among them, grouped so that sources
sharing an author or a publisher, or where one links the other, count once.
Valid tally lines (who, subject, a searched source's link, towards or against)
are stored without a stop. The answer itself is kept nowhere.

``source``, ``topic`` and ``whats_new`` forms come with later stages.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from atlas import ports
from atlas.core import identity, reply, search, spend, summarize
from atlas.core.config import Profile
from atlas.store import SourceRecord, Store, TallyRecord

COMMAND = "ask"
ANSWER = "atlas_answer"
FORMS = ("question", "source", "topic", "whats_new")
FIELDS = search.FIELDS
ANSWERED = 10
MAX_OUTPUT = 16_000
LABELS = ("Sound", "Doubtful", "Noise")
DIRECTIONS = ("towards", "against")

ANSWER_TOOL = {
    "name": "answer",
    "description": "Give the answer to the question from the sources.",
    "input_schema": {
        "type": "object",
        "required": ["answer", "claims", "disagreements", "gaps", "model_view", "tally_lines"],
        "properties": {
            "answer": {"type": "string"},
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["claim", "sources", "label", "reason"],
                    "properties": {
                        "claim": {"type": "string"},
                        "sources": {"type": "array", "items": {"type": "string"}},
                        "label": {"type": "string", "enum": list(LABELS)},
                        "reason": {"type": "string"},
                    },
                },
            },
            "disagreements": {"type": "array", "items": {"type": "string"}},
            "gaps": {"type": "array", "items": {"type": "string"}},
            "model_view": {"type": "string"},
            "tally_lines": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["who", "subject", "link", "direction"],
                    "properties": {
                        "who": {"type": "string"},
                        "subject": {"type": "string"},
                        "link": {"type": "string"},
                        "direction": {"type": "string", "enum": list(DIRECTIONS)},
                    },
                },
            },
        },
    },
}


class _Unusable(Exception):
    """The answer call gave nothing Atlas can show; the message says why."""


def _source_block(n: int, record: SourceRecord, store: Store, source_id: int) -> str:
    meta = [f"[S{n}] {record.key_link}", f"Title: {record.title or 'unknown'}"]
    where = f"Publisher: {record.publisher or 'unknown'}" + (f" | Platform: {record.platform}" if record.platform else "")
    meta.append(f"Author: {record.author or 'unknown'} | {where} | Date: {record.published or 'unknown'}")
    meta.append(f"Abstract: {record.abstract or 'none'}")
    meta.append("Claims:")
    for stored in store.claims(source_id):
        claim = stored.claim
        flag = " [flagged: its quotes may not support it]" if claim.flag is not None and claim.flag.flagged else ""
        meta.append(f"- ({claim.section}, {claim.basis}) {claim.text}{flag}")
    return "\n".join(meta)


def _message(request: search.Request, blocks: Sequence[str]) -> str:
    head = [f"Question: {request.question}"]
    if request.context:
        head.append(f"Context: {request.context}")
    return "\n".join(head) + "\n\nSources:\n\n" + "\n\n".join(blocks) + f"\n\n{summarize.answer_line(ANSWER_TOOL['name'])}"


def _call(deps: summarize.Deps, messages: list[dict[str, Any]]) -> ports.Reply:
    try:
        answer = deps.host.call.call(ANSWER, messages, [ANSWER_TOOL], None, MAX_OUTPUT)
    except ports.CallFailed as err:
        raise _Unusable(f"the {ANSWER} call failed: {err.detail}") from None
    spend.record_call(deps.store, deps.profile, deps.command, ANSWER, answer, deps.clock())
    if answer.stop == "cut_off":
        raise _Unusable("the reply was cut off")
    if answer.stop == "refused":
        raise _Unusable("the model refused")
    return answer


def _write(deps: summarize.Deps, text: str) -> ports.Reply:
    """The answer reply with its tool call, after at most one reminder; ``ports.RoleMissing`` passes through."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": summarize.prompt("answer.md")},
        {"role": "user", "content": text},
    ]
    answer = _call(deps, messages)
    if answer.tool_input is None:
        messages.append({"role": "assistant", "content": answer.content.strip() or "(no answer)"})
        messages.append({"role": "user", "content": summarize.answer_line(ANSWER_TOOL["name"])})
        answer = _call(deps, messages)
        if answer.tool_input is None:
            raise _Unusable(f"the model did not call {ANSWER_TOOL['name']}")
    return answer


def _strings(value: Any, name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise _Unusable(f"{name} is not a list of text")
    return [item.strip() for item in value if item.strip()]


def _labels_failure(claims: Sequence[Mapping[str, Any]]) -> str | None:
    """Why the label format check fails, or ``None`` when every claim carries a label and a one-line reason."""
    for n, claim in enumerate(claims, 1):
        label, reason = claim.get("label"), claim.get("reason")
        if label not in LABELS:
            given = f'"{label}"' if isinstance(label, str) else "missing" if label is None else repr(label)
            return f"claim {n}'s label {given} is not Sound, Doubtful or Noise"
        if not isinstance(reason, str) or not reason.strip() or "\n" in reason.strip():
            return f"claim {n} has no one-line reason"
    return None


def _linked(store: Store, ids: Sequence[int]) -> set[tuple[int, int]]:
    """Each ``(a, b)`` among ``ids`` where source ``a`` keeps a related link that source ``b`` holds after link cleanup."""
    found = set()
    for source_id, link in store.related_links(ids):
        other = identity.lookup(store, link)
        if other is not None and other.id in ids and other.id != source_id:
            found.add((source_id, other.id))
    return found


def independent(ids: Sequence[int], records: Mapping[int, SourceRecord], linked: set[tuple[int, int]]) -> int:
    """How many independent sources ``ids`` are: sharing an author or a publisher, or one linking the other, counts once."""
    parent = {source_id: source_id for source_id in ids}

    def root(source_id: int) -> int:
        while parent[source_id] != source_id:
            source_id = parent[source_id]
        return source_id

    def same(value_a: str | None, value_b: str | None) -> bool:
        return bool(value_a and value_b and value_a.strip().casefold() == value_b.strip().casefold())

    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            ra, rb = records[a], records[b]
            if same(ra.author, rb.author) or same(ra.publisher, rb.publisher) or (a, b) in linked or (b, a) in linked:
                parent[root(b)] = root(a)
    return len({root(source_id) for source_id in ids})


def backing_text(count: int) -> str:
    if count == 0:
        return "backed by no source searched"
    return f"backed by {count} independent source{'' if count == 1 else 's'}"


def _writing_model(answer: ports.Reply) -> str:
    return f"{answer.model}:{answer.thinking}" if answer.thinking and ":" not in answer.model else answer.model


def run(body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``ask`` on the opened store."""
    forms = [name for name in FORMS if name in body]
    if len(forms) != 1:
        return search.bad(COMMAND, reply.problem("body", "ask takes exactly one of question, source, topic or whats_new"))
    if forms[0] != "question":
        problem = reply.problem("command", f'"ask" with {forms[0]} is not available in this Atlas build yet')
        return reply.build(COMMAND, reply.FAILED, problems=[problem]), reply.FAILED
    request = search.parse(body, FIELDS)
    if not isinstance(request, search.Request):
        return search.bad(COMMAND, request)
    stopped = search.gate(COMMAND, body, request, profile, store, host, (ANSWER,))
    if stopped is not None:
        return stopped
    deps = summarize.Deps(host, profile, store, COMMAND)
    try:
        searched = search.search(deps, request)
        search.record_query(deps, COMMAND, request, searched)
        top, ids = searched.sources[:ANSWERED], searched.ids[:ANSWERED]
        result = search.searched_result(request, searched, top)
        problems = list(searched.problems)
        if not top:
            result["answer"] = None
            steps = [reply.next_step("no stored source matches; research the question, then add the sources you find", {"stop": True})]
            return reply.build(COMMAND, reply.DONE, result=result, problems=problems, next=steps), reply.DONE
        blocks = [_source_block(n, record, store, source_id) for n, (record, source_id) in enumerate(zip(top, ids), 1)]
        try:
            answer = _write(deps, _message(request, blocks))
            shown = _shown(deps, answer, top, ids, problems)
        except _Unusable as err:
            problems.append(reply.problem("answer", f"no answer: {err}"))
            return reply.build(COMMAND, reply.FAILED, result=result, problems=problems), reply.FAILED
    except ports.RoleMissing as err:
        return search.role_missing(COMMAND, host, err.role)
    result.update(shown)
    steps = []
    if shown["gaps"]:
        steps.append(reply.next_step("research the gaps, then add the sources you find", {"stop": True}))
    steps.append(reply.next_step("ask a follow-up question", {"stop": True}))
    return reply.build(COMMAND, reply.DONE, result=result, problems=problems, next=steps), reply.DONE


def _shown(
    deps: summarize.Deps, answer: ports.Reply, top: Sequence[SourceRecord], ids: Sequence[int], problems: list[dict[str, Any]]
) -> dict[str, Any]:
    """The checked answer: claims with backing and checked labels, the other sections, and the stored tally lines."""
    value = answer.tool_input
    assert value is not None
    text = value.get("answer")
    if not isinstance(text, str) or not text.strip():
        raise _Unusable("the answer has no answer text")
    claims = value.get("claims")
    if not isinstance(claims, list) or not all(
        isinstance(claim, Mapping) and isinstance(claim.get("claim"), str) and claim["claim"].strip() and isinstance(claim.get("sources"), list)
        for claim in claims
    ):
        raise _Unusable("the claims are not a list of objects with claim text and source links")
    model_view = value.get("model_view")
    if model_view is not None and not isinstance(model_view, str):
        raise _Unusable("the Model view is not text")
    disagreements = _strings(value.get("disagreements"), "disagreements")
    gaps = _strings(value.get("gaps"), "gaps")

    by_link = {record.key_link: source_id for record, source_id in zip(top, ids)}
    records = {source_id: record for record, source_id in zip(top, ids)}
    linked = _linked(deps.store, ids)
    failure = _labels_failure(claims)
    shown = []
    for n, claim in enumerate(claims, 1):
        links = []
        for link in claim["sources"]:
            if not isinstance(link, str) or link not in by_link:
                left_out = f"claim {n} names a link that is not among the sources searched; it is left out"
                problems.append(reply.problem("claims", left_out, link if isinstance(link, str) else None))
            elif link not in links:
                links.append(link)
        item = {"claim": claim["claim"].strip(), "sources": links, "backing": backing_text(independent([by_link[link] for link in links], records, linked))}
        if failure is None:
            item["label"] = claim["label"]
            item["reason"] = claim["reason"].strip()
        shown.append(item)
    if failure is None:
        shown.sort(key=lambda item: LABELS.index(item["label"]))
    tally = _tally(deps, value.get("tally_lines"), by_link, problems)
    return {
        "answer": text.strip(),
        "claims": shown,
        "labels": "checked" if failure is None else f"unlabelled: the label check failed ({failure})",
        "disagreements": disagreements,
        "gaps": gaps,
        "model_view": (model_view or "").strip() or None,
        "writing_model": _writing_model(answer),
        "tally_lines": tally,
    }


def _tally(deps: summarize.Deps, lines: Any, by_link: Mapping[str, int], problems: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Store the valid tally lines without a stop; each other line is a problem and is left out."""
    if lines is None:
        return []
    if not isinstance(lines, list):
        problems.append(reply.problem("tally_lines", "the tally lines are not a list; none is stored"))
        return []
    at = spend.stamp(deps.clock())
    kept: list[TallyRecord] = []
    for n, line in enumerate(lines, 1):
        ok = (
            isinstance(line, Mapping)
            and all(isinstance(line.get(key), str) and line[key].strip() for key in ("who", "subject", "link", "direction"))
            and line["link"] in by_link
            and line["direction"] in DIRECTIONS
        )
        if not ok:
            problems.append(reply.problem("tally_lines", f"tally line {n} is not who, subject, a searched source's link and towards or against; it is not stored"))
            continue
        kept.append(TallyRecord(line["who"].strip(), line["subject"].strip(), line["link"], line["direction"], at))
    if kept:
        deps.store.add_tally(kept)
    return [{"who": row.who, "subject": row.subject, "link": row.link, "direction": row.direction} for row in kept]
