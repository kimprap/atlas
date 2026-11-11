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
are stored without a stop; the answer itself is kept nowhere. Each who-and-subject
pair with 3 or more lines no note proposal has used yet then gets one proposal
(``result.note_proposals``) and one ``next`` item, and its lines are marked
proposed in the same transaction that stores the new lines.

Notes (``notes``): the unarchived notes whose who equals, case-insensitively, the
author, an author alias or the publisher of a top-10 source go to the model as
``N1``, ``N2``, ...; a claim lists the keys of the notes the model applied, and
code shows each beside the claim's label. A note never changes a label.

``topic draft`` shares this writer (``draft``): the topic's brief is searched as a question is, and ``atlas_answer``
writes the draft revision through the same tool ``answer`` with prompt ``draft.md``, given each stored claim's key
(``S<n>.<position>``); each claim of the draft lists the stored claims it relies on (``cites``). A draft stores no
tally line. The catch-up (``ask`` with ``whats_new`` or ``topic``, ``catchup``) writes through ``catch_up``: the same tool
``answer`` with prompt ``catchup.md``, a required ``changes_conclusion`` and no tally lines, over a topic's new and
marked sources; the ``source`` form of ``ask`` comes with no stage yet.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from atlas import ports
from atlas.core import identity, notes, reply, search, spend, summarize
from atlas.core.config import Profile
from atlas.store import NoteRecord, SourceRecord, Store, StoredTally, TallyRecord

COMMAND = "ask"
ANSWER = "atlas_answer"
FORMS = ("question", "source", "topic", "whats_new")
FIELDS = search.FIELDS
ANSWERED = 10
MAX_OUTPUT = 16_000
LABELS = ("Sound", "Doubtful", "Noise")
DIRECTIONS = ("towards", "against")
PROPOSE_AT = 3

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
                        "notes": {"type": "array", "items": {"type": "string"}},
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


def _draft_tool() -> dict[str, Any]:
    """The ``answer`` tool of a topic draft: no tally lines, and each claim lists the keys of the stored claims it cites."""
    tool = copy.deepcopy(ANSWER_TOOL)
    tool["description"] = "Give the draft revision of the topic from the sources."
    schema = tool["input_schema"]
    schema["required"].remove("tally_lines")
    del schema["properties"]["tally_lines"]
    schema["properties"]["claims"]["items"]["properties"]["cites"] = {"type": "array", "items": {"type": "string"}}
    return tool


DRAFT_TOOL = _draft_tool()


def _catchup_tool() -> dict[str, Any]:
    """The ``answer`` tool of a catch-up: no tally lines, and it must say whether a conclusion of the topic changes."""
    tool = copy.deepcopy(ANSWER_TOOL)
    tool["description"] = "Say whether the new sources change a conclusion of the topic, and what they change."
    schema = tool["input_schema"]
    schema["required"].remove("tally_lines")
    del schema["properties"]["tally_lines"]
    schema["required"].append("changes_conclusion")
    schema["properties"]["changes_conclusion"] = {"type": "boolean"}
    return tool


CATCHUP_TOOL = _catchup_tool()


class _Unusable(Exception):
    """The answer call gave nothing Atlas can show; the message says why."""


def _source_block(n: int, record: SourceRecord, store: Store, source_id: int, keys: dict[str, tuple[str, int]] | None = None) -> str:
    """A source as the writer is given it; with ``keys``, each claim also carries its key ``S<n>.<position>``, which
    is added to ``keys`` with the source's link and the claim's position."""
    meta = [f"[S{n}] {record.key_link}", f"Title: {record.title or 'unknown'}"]
    where = f"Publisher: {record.publisher or 'unknown'}" + (f" | Platform: {record.platform}" if record.platform else "")
    meta.append(f"Author: {record.author or 'unknown'} | {where} | Date: {record.published or 'unknown'}")
    meta.append(f"Abstract: {record.abstract or 'none'}")
    meta.append("Claims:")
    for stored in store.claims(source_id):
        claim = stored.claim
        flag = " [flagged: its quotes may not support it]" if claim.flag is not None and claim.flag.flagged else ""
        key = ""
        if keys is not None:
            keys[f"S{n}.{stored.ord}"] = (record.key_link, stored.ord)
            key = f"[S{n}.{stored.ord}] "
        meta.append(f"- {key}({claim.section}, {claim.basis}) {claim.text}{flag}")
    return "\n".join(meta)


def _aliases(text: str | None) -> list[str]:
    """An author's aliases: ``sources.author_aliases`` holds a JSON list of names; other text counts as one name."""
    if not text:
        return []
    try:
        value = json.loads(text)
    except ValueError:
        value = None
    return value if isinstance(value, list) and all(isinstance(item, str) for item in value) else [text]


def _applicable(store: Store, top: Sequence[SourceRecord]) -> dict[str, NoteRecord]:
    """The unarchived notes whose who equals, case-insensitively, the author, an author alias or the publisher of a
    source in ``top``, by their keys ``N1``, ``N2``, ... in note order."""
    names = {
        name.strip().casefold()
        for record in top
        for name in (record.author, record.publisher, *_aliases(record.author_aliases))
        if name and name.strip()
    }
    found = [note for note in store.notes() if note.archived_at is None and note.who.strip().casefold() in names]
    return {f"N{n}": note for n, note in enumerate(found, 1)}


def _applied(value: Any, n: int, given: Mapping[str, NoteRecord], problems: list[dict[str, Any]]) -> list[dict[str, str]]:
    """The notes claim ``n`` lists as applied, shown; a key that names no given note is a problem and is left out."""
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(key, str) for key in value):
        problems.append(reply.problem("claims", f"claim {n}'s notes are not a list of note keys; they are left out"))
        return []
    keys = list(dict.fromkeys(key.strip() for key in value))
    for key in keys:
        if key not in given:
            problems.append(reply.problem("claims", f'claim {n} names note "{key}", which was not given; it is left out'))
    return [notes.shown(given[key]) for key in keys if key in given]


def _question_head(request: search.Request) -> list[str]:
    head = [f"Question: {request.question}"]
    if request.context:
        head.append(f"Context: {request.context}")
    return head


def _message(head: Sequence[str], blocks: Sequence[str], given: Mapping[str, NoteRecord]) -> str:
    text = "\n".join(head) + "\n\nSources:\n\n" + "\n\n".join(blocks)
    if given:
        lines = [
            f"[{key}] {note.who} | subject: {note.subject} | lean: {note.lean} | reason: {' '.join(note.reason.split())} | saved: {identity.date(note.at)}"
            for key, note in given.items()
        ]
        text += "\n\nTrust notes (the user's own):\n\n" + "\n".join(lines)
    return text + f"\n\n{summarize.answer_line(ANSWER_TOOL['name'])}"


def _call(deps: summarize.Deps, messages: list[dict[str, Any]], tool: Mapping[str, Any]) -> ports.Reply:
    try:
        answer = deps.host.call.call(ANSWER, messages, [tool], None, MAX_OUTPUT)
    except ports.CallFailed as err:
        raise _Unusable(f"the {ANSWER} call failed: {err.detail}") from None
    spend.record_call(deps.store, deps.profile, deps.command, ANSWER, answer, deps.clock())
    if answer.stop == "cut_off":
        raise _Unusable("the reply was cut off")
    if answer.stop == "refused":
        raise _Unusable("the model refused")
    return answer


def _write(deps: summarize.Deps, text: str, tool: Mapping[str, Any] = ANSWER_TOOL, system: str = "answer.md") -> ports.Reply:
    """The reply with its tool call, after at most one reminder; ``ports.RoleMissing`` passes through."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": summarize.prompt(system)},
        {"role": "user", "content": text},
    ]
    answer = _call(deps, messages, tool)
    if answer.tool_input is None:
        messages.append({"role": "assistant", "content": answer.content.strip() or "(no answer)"})
        messages.append({"role": "user", "content": summarize.answer_line(tool["name"])})
        answer = _call(deps, messages, tool)
        if answer.tool_input is None:
            raise _Unusable(f"the model did not call {tool['name']}")
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
        given = _applicable(store, top)
        try:
            answer = _write(deps, _message(_question_head(request), blocks, given))
            shown = _shown(deps, answer, top, ids, given, problems)
        except _Unusable as err:
            problems.append(reply.problem("answer", f"no answer: {err}"))
            return reply.build(COMMAND, reply.FAILED, result=result, problems=problems), reply.FAILED
    except ports.RoleMissing as err:
        return search.role_missing(COMMAND, host, err.role)
    result.update(shown)
    steps = []
    if shown["gaps"]:
        steps.append(reply.next_step("research the gaps, then add the sources you find", {"stop": True}))
    proposal = _proposal_step(store, shown["note_proposals"])
    if proposal is not None:
        steps.append(proposal)
    steps.append(reply.next_step("ask a follow-up question", {"stop": True}))
    return reply.build(COMMAND, reply.DONE, result=result, problems=problems, next=steps), reply.DONE


def _shown(
    deps: summarize.Deps,
    answer: ports.Reply,
    top: Sequence[SourceRecord],
    ids: Sequence[int],
    given: Mapping[str, NoteRecord],
    problems: list[dict[str, Any]],
    cites: Mapping[str, tuple[str, int]] | None = None,
    store_tally: bool = True,
) -> dict[str, Any]:
    """The checked answer: claims with backing and checked labels, the other sections, and the stored tally lines.

    With ``cites`` (a topic draft), each claim also shows the stored claims it relies on; with ``cites`` or without
    ``store_tally`` (a draft, a catch-up) no tally line is stored."""
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
        applied = _applied(claim.get("notes"), n, given, problems)
        if applied:
            item["notes"] = applied
        if cites is not None:
            item["cites"] = _cited(claim.get("cites"), n, cites, problems)
        shown.append(item)
    if failure is None:
        shown.sort(key=lambda item: LABELS.index(item["label"]))
    tally, proposals = ([], []) if cites is not None or not store_tally else _tally(deps, value.get("tally_lines"), by_link, problems)
    return {
        "answer": text.strip(),
        "claims": shown,
        "labels": "checked" if failure is None else f"unlabelled: the label check failed ({failure})",
        "disagreements": disagreements,
        "gaps": gaps,
        "model_view": (model_view or "").strip() or None,
        "writing_model": _writing_model(answer),
        "tally_lines": tally,
        "note_proposals": proposals,
    }


def _tally(
    deps: summarize.Deps, lines: Any, by_link: Mapping[str, int], problems: list[dict[str, Any]]
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """Store the valid tally lines without a stop; each other line is a problem and is left out.

    Returns the kept lines and the note proposals their storing made due (``_proposals``)."""
    if lines is None:
        return [], []
    if not isinstance(lines, list):
        problems.append(reply.problem("tally_lines", "the tally lines are not a list; none is stored"))
        return [], []
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
    proposals: list[dict[str, Any]] = []
    if kept:
        with deps.store.transaction():
            deps.store.add_tally(kept)
            proposals = _proposals(deps.store, at)
    return [{"who": row.who, "subject": row.subject, "link": row.link, "direction": row.direction} for row in kept], proposals


def _proposals(store: Store, at: str) -> list[dict[str, Any]]:
    """One proposal per who-and-subject pair with ``PROPOSE_AT`` or more lines no proposal has used yet; those lines are
    marked proposed (in the caller's transaction), so the pair's count starts again whether the user takes it or not."""
    pairs: dict[tuple[str, str], list[StoredTally]] = {}
    for stored in store.unproposed_tally():
        pairs.setdefault(notes.pair_key(stored.line.who, stored.line.subject), []).append(stored)
    found = []
    for lines in pairs.values():
        if len(lines) < PROPOSE_AT:
            continue
        who, subject = lines[0].line.who, lines[0].line.subject
        towards = sum(1 for stored in lines if stored.line.direction == "towards")
        against = len(lines) - towards
        lean = None if towards == against else "towards" if towards > against else "against"
        reason = f"{len(lines)} tally lines for {who} on {subject}: {towards} towards, {against} against"
        if lean is None:
            reason += "; a tie, so no lean is proposed"
        links = list(dict.fromkeys(stored.line.link for stored in lines))
        found.append({"who": who, "subject": subject, "lean": lean, "reason": reason, "links": links})
        store.mark_proposed([stored.id for stored in lines], at)
    return found


def _proposal_step(store: Store, proposals: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """The one ``next`` item for all of an answer's note proposals, or ``None`` without any."""
    if not proposals:
        return None
    if len(proposals) > 1:
        label = f"{len(proposals)} note proposals: save or change notes from `note_proposals`"
        return reply.next_step(label, {"stop": True})
    [proposal] = proposals
    who, subject, lean = proposal["who"], proposal["subject"], proposal["lean"]
    changing = notes.held(store, who, subject) is not None
    if lean is None:
        head = f"change the note on {who} for {subject}" if changing else f"save a note on {who} for {subject}"
        label = f"{head}: the evidence is tied, so choose its lean"
    elif changing:
        label = f"change the note on {who} for {subject} to lean {lean}"
    else:
        label = f"save a note: lean {lean} {who} on {subject}"
    return reply.next_step(label, {"stop": True})


def _cited(value: Any, n: int, given: Mapping[str, tuple[str, int]], problems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The stored claims claim ``n`` of a draft cites, shown as the source's link and the claim's position; a key the
    writer was not given is a problem and is left out."""
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(key, str) for key in value):
        problems.append(reply.problem("claims", f"claim {n}'s cites are not a list of claim keys; they are left out"))
        return []
    keys = list(dict.fromkeys(key.strip() for key in value))
    for key in keys:
        if key not in given:
            problems.append(reply.problem("claims", f'claim {n} cites "{key}", which was not given; it is left out'))
    return [{"link": given[key][0], "claim": given[key][1]} for key in keys if key in given]


def draft(
    command: str,
    body: Mapping[str, Any],
    request: search.Request,
    topic: str,
    agreed: tuple[int, str] | None,
    save_label: str,
    profile: Profile,
    store: Store,
    host: ports.Host,
) -> tuple[dict[str, Any], int]:
    """Answer ``topic draft``: search the topic's brief (``request.question``) as ``ask`` searches a question, then
    write the draft revision from the top 10 sources, given the topic's ``agreed`` version (its number and reviewed
    text) when there is one. Nothing but the query record and the call records is stored. ``save_label`` is the
    first ``next`` item."""
    stopped = search.gate(command, body, request, profile, store, host, (ANSWER,))
    if stopped is not None:
        return stopped
    deps = summarize.Deps(host, profile, store, command)
    try:
        searched = search.search(deps, request)
        search.record_query(deps, COMMAND, request, searched)
        top, ids = searched.sources[:ANSWERED], searched.ids[:ANSWERED]
        result = {"topic": topic, **search.searched_result(request, searched, top)}
        problems = list(searched.problems)
        if not top:
            result["draft"] = None
            steps = [reply.next_step("no stored source matches the brief; research it, add the sources you find, then draft again", {"stop": True})]
            return reply.build(command, reply.DONE, result=result, problems=problems, next=steps), reply.DONE
        keys: dict[str, tuple[str, int]] = {}
        blocks = [_source_block(n, record, store, source_id, keys) for n, (record, source_id) in enumerate(zip(top, ids), 1)]
        given = _applicable(store, top)
        head = [f"Topic: {topic}", f"Brief: {request.question}"]
        if request.context:
            head.append(f"Context: {request.context}")
        if agreed is not None:
            head.append(f"Agreed version {agreed[0]}, the understanding the user last saved:\n{agreed[1]}")
        try:
            written = _write(deps, _message(head, blocks, given), DRAFT_TOOL, "draft.md")
            shown = _shown(deps, written, top, ids, given, problems, keys)
        except _Unusable as err:
            problems.append(reply.problem("draft", f"no draft: {err}"))
            return reply.build(command, reply.FAILED, result=result, problems=problems), reply.FAILED
    except ports.RoleMissing as err:
        return search.role_missing(command, host, err.role)
    result["draft"] = {
        "text": shown["answer"],
        "claims": shown["claims"],
        "labels": shown["labels"],
        "disagreements": shown["disagreements"],
        "gaps": shown["gaps"],
        "model_view": shown["model_view"],
        "writing_model": shown["writing_model"],
        "writer_model": written.model,
        "thinking": written.thinking,
    }
    steps = [reply.next_step(save_label, {"stop": True})]
    if shown["gaps"]:
        steps.append(reply.next_step("research the gaps, add the sources you find, then draft again", {"stop": True}))
    return reply.build(command, reply.DONE, result=result, problems=problems, next=steps), reply.DONE


@dataclass(frozen=True)
class CaughtUp:
    """A topic's catch-up answer: whether a conclusion changes, the checked answer, and the ids of the sources its claims name."""

    changes: bool
    shown: dict[str, Any]
    named: tuple[int, ...]


def catch_up(
    deps: summarize.Deps,
    topic: str,
    brief: str,
    agreed: tuple[int, str] | None,
    top: Sequence[SourceRecord],
    ids: Sequence[int],
    marked: set[int],
    problems: list[dict[str, Any]],
) -> CaughtUp | str:
    """Write one topic's catch-up answer from its sources (``top``, with their ``ids``; the ``marked`` ones are labelled as
    such to the writer), given the topic's ``agreed`` version (its number and reviewed text) when there is one.

    Returns the reason as text when the call gave nothing Atlas can show; ``ports.RoleMissing`` passes through."""
    blocks = []
    for n, (record, source_id) in enumerate(zip(top, ids), 1):
        block = _source_block(n, record, deps.store, source_id)
        blocks.append(block + ("\nMarked: the judge thought this source may matter to this topic when it was added." if source_id in marked else ""))
    given = _applicable(deps.store, top)
    head = [f"Topic: {topic}", f"Brief: {brief}"]
    if agreed is None:
        head.append("No version of this topic is saved yet.")
    else:
        head.append(f"Agreed version {agreed[0]}, the understanding the user last saved:\n{agreed[1]}")
    try:
        written = _write(deps, _message(head, blocks, given), CATCHUP_TOOL, "catchup.md")
        value = written.tool_input
        assert value is not None
        changes = value.get("changes_conclusion")
        if not isinstance(changes, bool):
            raise _Unusable("the answer does not say whether a conclusion changes")
        shown = _shown(deps, written, top, ids, given, problems, store_tally=False)
    except _Unusable as err:
        return f"no answer: {err}"
    by_link = {record.key_link: source_id for record, source_id in zip(top, ids)}
    named = sorted({by_link[link] for claim in shown["claims"] for link in claim["sources"]})
    return CaughtUp(changes, shown, tuple(named))
