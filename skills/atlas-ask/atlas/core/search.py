"""``find``: search the stored sources and rank them (spec 4.5 rerank row, 4.10).

The body holds the agent's self-contained ``question``, the user's ``original``
words, optional ``phrasings`` and optional ``context``. Before searching, the
ranker is chosen: Jev when the profile chose it and it is set up, ``atlas_rerank``
when the profile chose Opus, otherwise a ``judge_setup`` decision (exit 4) that
``atlas-init`` answers, so the choice is saved and asked once. Then the cap
yields before the first paid call, as for every paid command; a ``confirm``
approval of that ``cap`` decision continues past it for this command.

The phrasings searched are the agent's, else three ``atlas_query`` rewrites of
``question``; a failed rewrite searches ``question`` as given and the reply says
so. Each phrasing is one BM25 search over ``source_fts`` (archived sources left
out); the lists merge by reciprocal rank fusion (k = 60) and the top 30 go to
the ranker, each as its title plus the first 700 characters of its abstract and
claims. Jev asks one noul question per candidate and orders by its probability;
when Jev fails after its backoff, ``atlas_rerank`` ranks that search and the
reply says so. When ``atlas_rerank`` fails, the sources stay in fusion (BM25)
order and the reply says so. Every paid call writes its ``calls`` row, and each
search writes one query record. ``ask`` searches the same way (``answer``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from atlas import ports
from atlas.core import add, approvals, identity, reply, spend, summarize
from atlas.core.config import SETUP_SKILL, Profile
from atlas.store import JudgeRecord, QueryRecord, SourceRecord, Store

COMMAND = "find"
QUERY = "atlas_query"
RERANK = "atlas_rerank"
JEV = "jev"
BM25 = "bm25"
FIELDS = {"profile", "approval", "question", "original", "phrasings", "context"}

REWRITES = 3
PER_PHRASING = 100
RRF_K = 60
RANKED = 30
RERANK_CHARS = 700
REWRITE_OUTPUT = 2_000
RERANK_OUTPUT = 4_000
JEV_QUESTION = "Does this source help answer the question?"

REWRITE_TOOL = {
    "name": "phrasings",
    "description": "Give the search phrasings for the question.",
    "input_schema": {
        "type": "object",
        "required": ["phrasings"],
        "properties": {"phrasings": {"type": "array", "items": {"type": "string"}}},
    },
}
RANK_TOOL = {
    "name": "rank",
    "description": "Give every source's number, the most helpful first.",
    "input_schema": {
        "type": "object",
        "required": ["order"],
        "properties": {"order": {"type": "array", "items": {"type": "integer"}}},
    },
}


@dataclass(frozen=True)
class Request:
    """A valid ``find`` or ``ask`` question body."""

    question: str
    original: str
    phrasings: tuple[str, ...] | None
    context: str | None


@dataclass
class Searched:
    """The ranked sources of one search (ids and rows, best first), the ranker that ordered them, and what the
    reply and query record keep."""

    ids: list[int]
    sources: list[SourceRecord]
    ranker: str
    model: str | None
    phrasings: tuple[str, ...]
    judge_records: tuple[JudgeRecord, ...] | None = None
    problems: list[dict[str, Any]] = field(default_factory=list)

    def ranker_item(self) -> dict[str, Any]:
        return {"name": self.ranker, "model": self.model}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def parse(body: Mapping[str, Any], allowed: set[str]) -> Request | dict[str, Any]:
    """The question body, or the problem that makes it bad input."""
    extra = sorted(set(body) - allowed)
    if extra:
        return reply.problem(extra[0], f'"{extra[0]}" is not a field of this command; it takes {", ".join(sorted(allowed))}')
    for name in ("question", "original"):
        if not _text(body.get(name)):
            return reply.problem(name, f"{name} must be non-empty text")
    phrasings = body.get("phrasings")
    if phrasings is not None and not (isinstance(phrasings, list) and phrasings and all(_text(item) for item in phrasings)):
        return reply.problem("phrasings", "phrasings must be a non-empty list of non-empty text")
    context = body.get("context")
    if context is not None and not isinstance(context, str):
        return reply.problem("context", "context must be text")
    return Request(
        question=body["question"].strip(),
        original=body["original"].strip(),
        phrasings=None if phrasings is None else tuple(item.strip() for item in phrasings),
        context=context.strip() or None if context is not None else None,
    )


def bad(command: str, problem: dict[str, Any]) -> tuple[dict[str, Any], int]:
    return reply.build(command, reply.BAD_INPUT, problems=[problem]), reply.BAD_INPUT


def _cap_approval(command: str, body: Mapping[str, Any]) -> dict[str, Any] | None:
    """The problem with the body's ``approval``, or ``None``; only a ``confirm`` of this command's cap decision is taken."""
    if "approval" not in body:
        return None
    value = body["approval"]
    fields_ = {"by", "decision", "choice", "words"}
    if not (isinstance(value, Mapping) and set(value) == fields_ and value.get("by") == approvals.CONFIRM):
        return reply.problem("approval", f"{command} takes only a confirm approval of its cap decision, with exactly the fields {', '.join(sorted(fields_))}")
    if not all(_text(value[key]) for key in fields_):
        return reply.problem("approval", "every approval field is non-empty text")
    if value["choice"] != approvals.GO:
        return reply.problem("approval", f'approval.choice "{value["choice"]}" does not go ahead; only "{approvals.GO}" is resent')
    if reply.approved_kind(command, None, body, (spend.CAP,)) is None:
        return reply.problem("approval", reply.OTHER_CHANGE)
    return None


def _cap_decision(command: str, body: Mapping[str, Any], limit: spend.Limit) -> dict[str, Any]:
    decision_id = reply.decision_id(command, None, body, spend.CAP)
    go = {"resend": {"approval": {"by": approvals.CONFIRM, "decision": decision_id, "choice": approvals.GO}}}
    options = [
        reply.option(approvals.GO, "continue anyway (this command only)", go),
        reply.option(approvals.RAISE_CAP, "raise the cap yourself in config.toml", {"stop": True}),
        reply.option(approvals.STOP, "stop here", {"stop": True}),
    ]
    text = limit.text()
    return reply.decision(command, None, body, spend.CAP, text[:1].upper() + text[1:] + ".", options)


def _judge_setup(command: str, body: Mapping[str, Any], profile: Profile, host: ports.Host) -> dict[str, Any]:
    trouble = host.judge.setup_problem() if profile.judge == JEV and host.judge is not None else None
    why = f" ({trouble.what})" if trouble is not None else ""
    question = (
        f"Jev is not set up for profile {profile.name}{why}, so Atlas cannot rank this search. "
        "Set up Jev, or use Opus for this profile? The choice is saved, so this is asked once."
    )
    options = [
        reply.option("set_up_jev", f"set up Jev (run `{SETUP_SKILL}`)", {"skill": SETUP_SKILL}),
        reply.option("use_opus", f"use Opus for this profile (run `{SETUP_SKILL}`)", {"skill": SETUP_SKILL}),
        reply.option(approvals.STOP, "stop here", {"stop": True}),
    ]
    return reply.decision(command, None, body, "judge_setup", question, options)


def missing_roles(command: str, host: ports.Host, roles: Sequence[str]) -> tuple[dict[str, Any], int] | None:
    """The exit 3 reply when the host reports any of ``roles`` missing, else ``None``."""
    items = add.role_items(host, roles)
    return add.not_set_up(command, items, {}) if items else None


def role_missing(command: str, host: ports.Host, role: str) -> tuple[dict[str, Any], int]:
    """The exit 3 reply for a role the host refused at call time."""
    items = add.role_items(host, (role,)) or [{"what": f"Role {role} is missing", "fix": [f"Add the model role {role}."], "where": None}]
    return add.not_set_up(command, items, {})


def gate(
    command: str, body: Mapping[str, Any], request: Request, profile: Profile, store: Store, host: ports.Host, roles: Sequence[str]
) -> tuple[dict[str, Any], int] | None:
    """The stop before any paid call: a bad approval, ``judge_setup``, a missing role or the cap; ``None`` to go on.

    ``roles`` are the model roles the command calls besides search's own.
    """
    problem = _cap_approval(command, body)
    if problem is not None:
        return bad(command, problem)
    deps = summarize.Deps(host, profile, store, command)
    if profile.judge != "opus" and not summarize.judge_ready(deps):
        decision = _judge_setup(command, body, profile, host)
        return reply.build(command, reply.NEEDS_DECISION, decisions=[decision]), reply.NEEDS_DECISION
    needed = [*([] if request.phrasings else [QUERY]), *([RERANK] if profile.judge == "opus" else []), *roles]
    stopped = missing_roles(command, host, needed)
    if stopped is not None:
        return stopped
    guard = spend.Guard(store, profile, host, needed, paid=True, batch=False)
    if "approval" in body:
        guard.continue_past({spend.CAP})
    limit = guard.check()
    if limit is not None:
        decision = _cap_decision(command, body, limit)
        return reply.build(command, reply.NEEDS_DECISION, decisions=[decision]), reply.NEEDS_DECISION
    return None


def _model_call(deps: summarize.Deps, role: str, system: str, text: str, tool: Mapping[str, Any], max_output: int) -> ports.Reply:
    """One call with ``tool`` on tool choice auto and the answer-only line; it writes its ``calls`` row.

    ``ports.CallFailed`` and ``ports.RoleMissing`` pass through.
    """
    messages = [{"role": "system", "content": system}, {"role": "user", "content": f"{text}\n\n{summarize.answer_line(tool['name'])}"}]
    answer = deps.host.call.call(role, messages, [tool], None, max_output)
    spend.record_call(deps.store, deps.profile, deps.command, role, answer, deps.clock())
    return answer


def _no_tool_reason(answer: ports.Reply, tool: str) -> str:
    if answer.stop == "cut_off":
        return "the reply was cut off"
    if answer.stop == "refused":
        return "the model refused"
    return f"the model did not call {tool}"


def _rewrite(deps: summarize.Deps, question: str) -> tuple[tuple[str, ...], dict[str, Any] | None]:
    """Three ``atlas_query`` phrasings of ``question``; on failure ``question`` itself and the problem that says so."""
    try:
        answer = _model_call(deps, QUERY, summarize.prompt("rewrite.md"), f"Question: {question}", REWRITE_TOOL, REWRITE_OUTPUT)
    except ports.CallFailed as err:
        why = f"the {QUERY} call failed: {err.detail}"
    else:
        value = answer.tool_input
        if value is None or answer.stop in ("cut_off", "refused"):
            why = _no_tool_reason(answer, REWRITE_TOOL["name"])
        else:
            items = value.get("phrasings")
            found = [item.strip() for item in items if _text(item)] if isinstance(items, list) else []
            found = list(dict.fromkeys(found))[:REWRITES]
            if found:
                return tuple(found), None
            why = "the rewrite gave no phrasing"
    return (question,), reply.problem("phrasings", f"the rewrite failed ({why}), so Atlas searched the question as given")


def fuse(lists: Sequence[Sequence[int]], limit: int = RANKED) -> list[int]:
    """Reciprocal rank fusion (k = 60) of ranked id lists; ties keep first-seen order."""
    scores: dict[int, float] = {}
    for ranked in lists:
        for rank, source_id in enumerate(ranked, 1):
            scores[source_id] = scores.get(source_id, 0.0) + 1.0 / (RRF_K + rank)
    order = sorted(scores, key=lambda source_id: -scores[source_id])
    return order[:limit]


def rerank_text(store: Store, source_id: int, record: SourceRecord) -> str:
    """The ranker's view of a source: its title, then the first 700 characters of its abstract and claims."""
    body = "\n".join([record.abstract or "", *(stored.claim.text for stored in store.claims(source_id))]).strip()
    return f"{record.title or record.key_link}\n{body[:RERANK_CHARS]}"


def _by_jev(deps: summarize.Deps, question: str, texts: Sequence[str], links: Sequence[str]) -> tuple[list[int], str, tuple[JudgeRecord, ...]]:
    """Candidate indexes by Jev's probability, highest first; ``ports.JudgeFailed`` passes through."""
    asked = ports.Question("helps", "noul", JEV_QUESTION)
    requests = [(f"Question: {question}\n\nSource:\n{text}", asked) for text in texts]
    answers = summarize.judge_all(deps, requests)
    ps = [float(next(iter(got.answers.values())).p or 0.0) for got in answers]
    records = tuple(JudgeRecord(link, p, got.model) for link, p, got in zip(links, ps, answers))
    order = sorted(range(len(texts)), key=lambda n: -ps[n])
    return order, answers[0].model, records


def _by_opus(deps: summarize.Deps, question: str, texts: Sequence[str]) -> tuple[list[int], str]:
    """Candidate indexes in ``atlas_rerank``'s order; sources it leaves out follow in fusion order.

    Raises ``ValueError`` with the reason when the ranking cannot be used.
    """
    listed = "\n\n".join(f"[{n}] {text}" for n, text in enumerate(texts, 1))
    try:
        answer = _model_call(deps, RERANK, summarize.prompt("rerank.md"), f"Question: {question}\n\nSources:\n{listed}", RANK_TOOL, RERANK_OUTPUT)
    except ports.CallFailed as err:
        raise ValueError(f"the {RERANK} call failed: {err.detail}") from None
    if answer.tool_input is None or answer.stop in ("cut_off", "refused"):
        raise ValueError(_no_tool_reason(answer, RANK_TOOL["name"]))
    order = answer.tool_input.get("order")
    valid = isinstance(order, list) and all(
        isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= len(texts) for n in order
    )
    if not valid or len(set(order)) != len(order):
        raise ValueError("the ranking is not a list of distinct source numbers")
    picked = [n - 1 for n in order]
    return picked + [n for n in range(len(texts)) if n not in picked], answer.model


def search(deps: summarize.Deps, request: Request) -> Searched:
    """Search and rank for ``request`` after ``gate`` let it go on; ``ports.RoleMissing`` passes through."""
    problems: list[dict[str, Any]] = []
    phrasings = request.phrasings
    if phrasings is None:
        phrasings, problem = _rewrite(deps, request.question)
        if problem is not None:
            problems.append(problem)
    store = deps.store
    ids = fuse([store.search(phrasing, PER_PHRASING) for phrasing in phrasings])
    records = [store.source_record(source_id) for source_id in ids]
    ranker = RERANK if deps.profile.judge == "opus" else JEV

    def ranked(order: Sequence[int], name: str, model: str | None, judged: tuple[JudgeRecord, ...] | None) -> Searched:
        return Searched([ids[n] for n in order], [records[n] for n in order], name, model, phrasings, judged, problems)

    if not ids:
        return ranked([], ranker, None, None if ranker == RERANK else ())
    texts = [rerank_text(store, source_id, record) for source_id, record in zip(ids, records)]
    if ranker == JEV:
        try:
            order, model, judged = _by_jev(deps, request.question, texts, [record.key_link for record in records])
            return ranked(order, JEV, model, judged)
        except ports.JudgeFailed as err:
            problems.append(reply.problem("ranker", f"Jev failed after its backoff ({err.detail}), so {RERANK} ranked this search"))
        except ports.JudgeNotSetUp as err:
            # The key file changed after the gate found Jev ready; this search still gets a ranker.
            problems.append(reply.problem("ranker", f"Jev could not run ({err}), so {RERANK} ranked this search"))
    try:
        order, model = _by_opus(deps, request.question, texts)
    except ValueError as err:
        problems.append(reply.problem("ranker", f"{RERANK} failed ({err}), so the sources are in BM25 order"))
        return ranked(range(len(ids)), BM25, None, None)
    return ranked(order, RERANK, model, None)


def record_query(deps: summarize.Deps, op: str, request: Request, searched: Searched) -> None:
    """Write the one query record of this ``find`` or ``ask``."""
    note = "; ".join(problem["problem"] for problem in searched.problems) or None
    deps.store.add_query(
        QueryRecord(
            at=spend.stamp(deps.clock()),
            op=op,
            original=request.original,
            question=request.question,
            phrasings=searched.phrasings,
            context=request.context,
            ranker=searched.ranker,
            judge_records=searched.judge_records,
            note=note,
        )
    )


def source_item(record: SourceRecord) -> dict[str, Any]:
    """A ranked source as replies show it."""
    return {
        "link": record.key_link,
        "title": record.title,
        "author": record.author,
        "date": record.published,
        "last_read": identity.date(record.last_read),
    }


def searched_result(request: Request, searched: Searched, sources: Sequence[SourceRecord]) -> dict[str, Any]:
    """The result fields ``find`` and ``ask`` share: the sources, the ranker and the question as searched."""
    result: dict[str, Any] = {"sources": [source_item(record) for record in sources], "ranker": searched.ranker_item()}
    if request.question != request.original:
        result["question_as_searched"] = request.question
    return result


def run(command: str, mode: str | None, body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``find`` on the opened store."""
    if mode is not None:
        problem = reply.problem("command", f'"{command} --{mode}" is not available in this Atlas build yet')
        return reply.build(command, reply.FAILED, problems=[problem]), reply.FAILED
    request = parse(body, FIELDS)
    if not isinstance(request, Request):
        return bad(command, request)
    stopped = gate(command, body, request, profile, store, host, ())
    if stopped is not None:
        return stopped
    deps = summarize.Deps(host, profile, store, command)
    try:
        searched = search(deps, request)
    except ports.RoleMissing as err:
        return role_missing(command, host, err.role)
    record_query(deps, COMMAND, request, searched)
    result = searched_result(request, searched, searched.sources)
    if searched.sources:
        steps = [reply.next_step("ask Atlas to answer this question from these sources", {"stop": True})]
    else:
        steps = [reply.next_step("no stored source matches; research the question, then add the sources you find", {"stop": True})]
    return reply.build(command, reply.DONE, result=result, problems=searched.problems, next=steps), reply.DONE
