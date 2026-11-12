"""``add --redo``: rebuild old summaries from a fresh read of each page.

Body: ``{"links"?: [link], "topic"?: name, "force"?: true}``. Without ``links`` the
scope is every unarchived record that is older: its rubric version differs from
the current one, or it was written without escalation by a model other than the
model of the ``atlas_summarize`` role (without its thinking suffix); an
escalated record counts only on a rubric change (``Store.older_sources``). With
``links`` the scope is those sources, and a ``topic`` (a name) scopes the redo to the
sources its saved versions cite (``Store.version_sources``), a topic that is not stored
being exit 1. In either scope the sources already on the current setup are skipped and
the reply says so, and when all of them are current an ``already_current`` decision
offers "redo anyway" (a resend with ``force``). ``force`` redoes current sources too and
needs ``links`` or ``topic``. With nothing older and no scope named the reply is done
with nothing to redo.

The sources to redo are one change of kind ``add_redo``, always paid at scale:
its confirm states the count, the list-price estimate from the stored pages'
sizes and the window use, and the cap and window guard run before each item.
The one ``approvals`` row is written inside the first source the command
changes (a redone source or a ``redo_failed`` line).

Each source is handled alone, so one bad source never blocks the batch. The page
is read again the way it was added (its kept ``scope_choice``). An unreadable
page, an unreadable image of an image source and a source the site table marks
unchangeable use the stored page text, and the item's ``page`` says so. A page
that now needs a scope choice the record does not hold (``add.scope_question``),
or whose chosen sections are gone, keeps its old summary: ``kept: needs scope``.
Otherwise the full pipeline (``summarize.summarize``) rebuilds the summary from
scratch. Only a summary that passes replaces the old one, in one transaction:
the new text, hash and read date (when the page was read again), the old claims
marked replaced, the new claims, the summary columns, the search index entry and
one ``summary_history`` line ``redone`` that carries the replaced summary's
rubric version, model and escalation. A summary that fails after its escalation
changes nothing but one ``redo_failed`` line, writes the failed-summary log
(``failure_log``) and returns a ``summary_failed`` decision.

A redone source whose claims changed (the replaced and the new claims differ in text or quotes) is matched to the
followed topics (``marks.match``: ``topics_marked``, or ``topics`` is ``topics not matched``), and flags each topic
whose agreed version cites a claim of it that is now changed or removed (``topics_flagged``); it also names who cites it and
each flagged topic's agreed version (``cited_in``, ``citations``).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from atlas import ports
from atlas.core import add, approvals, citations, failure_log, identity, marks, reply, spend, status, summarize, topics
from atlas.core.config import Profile
from atlas.store import HistoryRecord, SourceRecord, Store, StoredSource, TopicRecord

COMMAND = "add"
MODE = "redo"
CALLED = "add --redo"
FIELDS = {"profile", "approval", "links", "topic", "force"}
# Links a confirm names before "and <n> more".
NAMED = 5
CURRENT = "skipped: already on the current rubric and summary model"
NEEDS_SCOPE = "kept: needs scope"


def _bad(problem: dict[str, Any]) -> tuple[dict[str, Any], int]:
    return reply.build(COMMAND, reply.BAD_INPUT, problems=[problem]), reply.BAD_INPUT


def body_problem(body: Mapping[str, Any]) -> dict[str, Any] | None:
    """Why ``body`` is not a valid ``add --redo`` body, or ``None``."""
    extra = sorted(set(body) - FIELDS)
    if extra:
        return reply.problem(extra[0], f'"{extra[0]}" is not a field of this command; it takes {", ".join(sorted(FIELDS))}')
    links = body.get("links")
    if "links" in body and not (isinstance(links, list) and links and all(isinstance(link, str) for link in links)):
        return reply.problem("links", "links must be a non-empty list of links")
    topic = body.get("topic")
    if "topic" in body and not (isinstance(topic, str) and topic.strip()):
        return reply.problem("topic", "topic must be a topic name")
    if "links" in body and "topic" in body:
        return reply.problem("topic", "name links or a topic, not both")
    if "force" in body and not isinstance(body["force"], bool):
        return reply.problem("force", "force must be true or false")
    if body.get("force") and "links" not in body and "topic" not in body:
        return reply.problem("force", "force needs links or a topic: it redoes the named sources although they are on the current setup")
    return None


@dataclass(frozen=True)
class Prepared:
    """What the pipeline reads for one source, and how the page was got: ``read`` is the page read
    again (``None`` when the stored text is used), ``share`` the part of it kept, ``note`` the item's ``page``."""

    page_input: summarize.PageInput
    read: ports.Page | None
    images: tuple[bytes, ...]
    share: float | None
    note: str


class Redo:
    """One ``add --redo`` command on an opened store."""

    def __init__(self, body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> None:
        self.body = body
        self.profile = profile
        self.store = store
        self.host = host
        self.force = body.get("force") is True
        self.model: str | None = None  # the current summary model, set once the command starts
        self.deps = summarize.Deps(host, profile, store, CALLED)
        self.limit = add.page_limit(host, profile)
        self.items: list[dict[str, Any]] = []
        self.problems: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.redone = 0
        self.approved: tuple[approvals.Change, approvals.Go] | None = None

    # Replies ------------------------------------------------------------------
    def _result(self) -> dict[str, Any]:
        return {"redone": self.redone, "items": self.items}

    def _stop(self, decisions: list[dict[str, Any]]) -> tuple[dict[str, Any], int]:
        answer = reply.build(COMMAND, reply.NEEDS_DECISION, result=self._result(), problems=self.problems, decisions=decisions)
        return answer, reply.NEEDS_DECISION

    def _done(self, label: str) -> tuple[dict[str, Any], int]:
        steps = [reply.next_step(label, {"stop": True})]
        return reply.build(COMMAND, reply.DONE, result=self._result(), problems=self.problems, next=steps), reply.DONE

    def _applied(self) -> None:
        """Write the command's one ``approvals`` row, inside the transaction of the first source it changes."""
        if self.approved is not None:
            approvals.record(self.store, *self.approved)
            self.approved = None

    # Scope --------------------------------------------------------------------
    def _named(self, older: Sequence[StoredSource]) -> list[StoredSource]:
        """The named links' sources to redo; the rest are noted on the items."""
        found: list[StoredSource] = []
        for link in self.body["links"]:
            source = identity.lookup(self.store, link)
            if source is None:
                self.problems.append(reply.problem("links", "not stored; add it first", link))
            else:
                found.append(source)
        return self._scoped(found, older)

    def _cited(self, topic: TopicRecord, older: Sequence[StoredSource]) -> list[StoredSource]:
        """The sources a topic's saved versions cite that are to be redone; the rest are noted on the items."""
        return self._scoped([self.store.source(source_id) for source_id in self.store.version_sources(topic.id)], older)

    def _scoped(self, found: Sequence[StoredSource], older: Sequence[StoredSource]) -> list[StoredSource]:
        older_ids = {source.id for source in older}
        redo: list[StoredSource] = []
        current: list[StoredSource] = []
        for source in found:
            if source.archived_at is not None:
                self.items.append({"link": source.key_link, "result": f"archived {identity.date(source.archived_at)}"})
            elif any(source.id == seen.id for seen in (*redo, *current)):
                continue
            elif self.force or source.id in older_ids:
                redo.append(source)
            else:
                current.append(source)
        if redo:
            self.items += [{"link": source.key_link, "result": CURRENT} for source in current]
        elif current:
            self.decisions.append(self._already_current(current))
        return redo

    def _already_current(self, current: Sequence[StoredSource]) -> dict[str, Any]:
        names = ", ".join(source.key_link for source in current)
        this = "it" if len(current) == 1 else "them"
        verb = "is" if len(current) == 1 else "are"
        question = f"{names} {verb} already on the current rubric and summary model. Redo {this} anyway?"
        options = [
            reply.option("redo_anyway", "redo anyway", {"resend": {"force": True}}),
            reply.option("stop", "no, stop here", {"stop": True}),
        ]
        return reply.decision(COMMAND, MODE, self.body, "already_current", question, options)

    # The command --------------------------------------------------------------
    def run(self) -> tuple[dict[str, Any], int]:
        problem = body_problem(self.body)
        if problem is not None:
            return _bad(problem)
        topic = None
        if "topic" in self.body:
            topic = self.store.topic(self.body["topic"])
            if topic is None:
                problems = [reply.problem("topic", topics.NOT_STORED)]
                return reply.build(COMMAND, reply.FAILED, result=self._result(), problems=problems), reply.FAILED
        missing = add.role_items(self.host, add.ROLES)
        if missing:
            return add.not_set_up(COMMAND, missing, self._result())
        self.model = status.summary_model(self.host)
        older = self.store.older_sources(summarize.RUBRIC_VERSION, self.model)
        if topic is not None:
            sources = self._cited(topic, older)
        else:
            sources = self._named(older) if "links" in self.body else older
        if self.decisions:
            return self._stop(self.decisions)
        if not sources:
            if topic is not None:
                return self._done(f'nothing to redo: "{topic.name}" cites no source that is not archived')
            if "links" in self.body:
                return self._done("nothing was redone; add the links first, or ask about these sources with `ask`")
            return self._done("nothing to redo: every record is on the current rubric and summary model")
        stopped = self._run(sources)
        if stopped is not None:
            return stopped
        steps = [reply.next_step("ask about these sources with `ask`", {"stop": True})]
        if self.decisions:
            answer = reply.build(
                COMMAND, reply.NEEDS_DECISION, result=self._result(), problems=self.problems, next=steps, decisions=self.decisions
            )
            return answer, reply.NEEDS_DECISION
        return reply.build(COMMAND, reply.DONE, result=self._result(), problems=self.problems, next=steps), reply.DONE

    def _question(self, sources: Sequence[StoredSource], guard: spend.Guard) -> str:
        model = self.model
        if model is None:
            estimate = "cost unknown: the summary model is not known"
        else:
            costs = [
                spend.estimate_item(self.store, self.profile, model, summarize.page_tokens(self.store.page_text(source.id).text))
                for source in sources
            ]
            total = None if any(cost is None for cost in costs) else sum(costs)  # type: ignore[arg-type]
            estimate = spend.estimate_text(total, model)
        named = ", ".join(source.key_link for source in sources[:NAMED])
        if len(sources) > NAMED:
            named += f" and {len(sources) - NAMED} more"
        count = f"{len(sources)} summary" if len(sources) == 1 else f"{len(sources)} summaries"
        return (
            f"Redo {count} ({named}) from a fresh read of each page? "
            f"Estimated cost: {estimate}. Window use: {guard.window_use()}."
        )

    def _run(self, sources: list[StoredSource]) -> tuple[dict[str, Any], int] | None:
        guard = spend.Guard(self.store, self.profile, self.host, add.ROLES, paid=True, batch=True)
        change = approvals.Change(
            command=COMMAND,
            mode=MODE,
            body=self.body,
            kind="add_redo",
            question=self._question(sources, guard),
            links=[source.key_link for source in sources],
            paid_at_scale=True,
        )
        verdict = approvals.check(change, self.profile, guard)
        if isinstance(verdict, approvals.Refused):
            return _bad(verdict.problem)
        if isinstance(verdict, approvals.Stop):
            return self._stop([verdict.decision])
        self.approved = (change, verdict)
        for done, source in enumerate(sources):
            if done:
                limit = guard.check(done, len(sources) - done)
                if limit is not None:
                    return self._stop([*self.decisions, approvals.limit_decision(change, limit)])
            try:
                self._one(source)
            except ports.RoleMissing as err:
                return add.not_set_up(COMMAND, add.role_items(self.host, (err.role,)), self._result())
        return None

    # One source ---------------------------------------------------------------
    def _from_stored(self, record: SourceRecord, source: StoredSource, note: str) -> Prepared:
        """The pipeline input made of the stored page text."""
        text = self.store.page_text(source.id).text
        page = ports.Page(source.key_link, record.title, record.author, record.publisher, record.published, record.kind, text, counts=ports.Counts(len(text.split()), 0, 0))
        kind = add.kind_of(page, source.key_link)
        page_input = summarize.PageInput(page, text, add.TRANSCRIPT if kind == "video" else kind, source.key_link)
        return Prepared(page_input, None, (), None, f"stored text used: {note}")

    def _prepare(self, source: StoredSource, record: SourceRecord) -> Prepared | str:
        """The pipeline input, or the problem that keeps the old summary because a scope choice is needed."""
        link = source.key_link
        if record.unchangeable:
            return self._from_stored(record, source, "unchangeable source")
        scope = add.stored_scope(record.scope_choice)
        read = self.host.read.read(link, add.read_scope(scope))
        if isinstance(read, ports.Unreadable):
            return self._from_stored(record, source, f"page unreadable ({read.reason})")
        kind = add.kind_of(read, link)
        needed = add.scope_question({}, link, scope, read, kind, self.limit)
        if needed is not None:
            return needed["question"]
        scoped = add.scoped_text(read, scope, self.limit)
        if isinstance(scoped, str):
            return scoped
        images: list[bytes] = []
        if scope == add.IMAGES:
            for image_link in read.images:
                got = self.host.read.image(image_link)
                if isinstance(got, ports.Unreadable):
                    return self._from_stored(record, source, f"an image is unreadable ({got.reason})")
                images.append(got)
        text, share = scoped
        page_input = summarize.PageInput(read, text, add.TRANSCRIPT if kind == "video" else kind, link, tuple(images))
        return Prepared(page_input, read, tuple(images), share, "read again")

    def _one(self, source: StoredSource) -> None:
        link = source.key_link
        record = self.store.source_record(source.id)
        prepared = self._prepare(source, record)
        if isinstance(prepared, str):
            self.problems.append(reply.problem("scope", prepared, link))
            self.items.append({"link": link, "result": NEEDS_SCOPE})
            return
        summary = summarize.summarize(self.deps, prepared.page_input)
        if isinstance(summary, summarize.Failed):
            self._failed(source, record, prepared, summary)
        else:
            self._replace(source, record, prepared, summary)

    def _history(self, source: StoredSource, record: SourceRecord, event: str, at: str) -> None:
        """One history line carrying the summary the event leaves behind or replaces."""
        self.store.add_history(HistoryRecord(source.id, at, event, record.rubric_version or "", record.model or "", bool(record.escalated)))

    def _failed(self, source: StoredSource, record: SourceRecord, prepared: Prepared, failed: summarize.Failed) -> None:
        link = source.key_link
        with self.store.transaction():
            self._applied()
            self._history(source, record, "redo_failed", spend.stamp(spend.local_now()))
        entry = {"link": link, "result": "redo failed, old summary kept", "page": prepared.note}
        failure_log.keep(entry, self.problems, self.profile.name, CALLED, link, failed)
        self.items.append(entry)
        retry = {"links": [link], **({"force": True} if self.force else {})}
        options = [
            reply.option("retry", "retry the redo", {"resend": retry}),
            reply.option("skip", "skip this link", {"stop": True}),
        ]
        question = f"The redo of {link} failed, also after one escalation ({failed.reason}). The old summary was kept. Retry or skip?"
        self.decisions.append(reply.decision(COMMAND, MODE, retry, "summary_failed", question, options))

    def _replace(self, source: StoredSource, record: SourceRecord, prepared: Prepared, summary: summarize.Summary) -> None:
        at = spend.stamp(spend.local_now())
        old = self.store.claims(source.id)
        with self.store.transaction():
            self._applied()
            if prepared.read is not None:
                identity.refresh(self.store, source, prepared.read, text=summary.text, images=prepared.images)
                self.store.update_summary(source.id, text_origin="read", read_share=prepared.share)
            for stored_claim in old:
                self.store.replace_claim(stored_claim.id, at)
            for ord, claim in enumerate(summary.claims, 1):
                self.store.add_claim(source.id, ord, claim, at)
            self.store.update_summary(
                source.id,
                title=summary.title,
                author=summary.author,
                publisher=summary.publisher,
                published=summary.published,
                abstract=summary.abstract,
                rubric_version=summarize.RUBRIC_VERSION,
                model=summary.model,
                thinking=summary.thinking,
                escalated=summary.escalated,
                rethink_line=summary.rethink_line,
                dropped_claims=summary.dropped,
                support_status=summary.support_status,
            )
            self._history(source, record, "redone", at)
            self.store.index_source(source.id)
        entry: dict[str, Any] = {
            "link": source.key_link,
            "result": "redone",
            "title": summary.title,
            "abstract": summary.abstract,
            "claims": len(summary.claims),
            "dropped_claims": summary.dropped,
            "flagged_claims": sum(1 for claim in summary.claims if claim.flag is not None and claim.flag.flagged),
            "page": prepared.note,
        }
        if summary.support_status != summarize.CHECKED:
            entry["support"] = "support not checked"
        if prepared.share is not None:
            entry["read_share"] = prepared.share
        if marks.claims_changed(old, self.store.claims(source.id)):
            marks.match(self.deps, source.id).apply(entry)
            flagged = marks.flagged_topics(self.store, source.id)
            if flagged:
                entry["topics_flagged"] = flagged
            citations.attach(entry, citations.of_source(self.store, source.id), *(citations.of_topic(self.store, name) for name in flagged))
        self.items.append(entry)
        self.redone += 1


def run(body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``add --redo`` on the opened store."""
    return Redo(body, profile, store, host).run()
