"""The store interface core uses; ``atlas.store.sqlite`` implements it.

One store per profile. Core opens it through ``Host.open_store(path)`` and never
imports the SQLite adapter. Every method raises ``StoreFailed`` when the store
cannot do it. Times are UTC ISO-8601 text, so text order is time order.
"""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

NEWER_THAN_CODE = "store is newer than this Atlas; check out a newer tag"


class StoreNewer(Exception):
    """The store's schema version is newer than this code can read."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"{path}: {NEWER_THAN_CODE}")
        self.path = path


class StoreFailed(Exception):
    """The store could not be opened or used; ``detail`` says why in plain text."""

    def __init__(self, path: Path, detail: str) -> None:
        super().__init__(f"{path}: {detail}")
        self.path = path
        self.detail = detail


@dataclass(frozen=True)
class CallRecord:
    """One paid call: ``cost_usd`` is None exactly when ``cost_kind`` is ``unknown``."""

    at: str
    command: str
    role: str
    model: str
    thinking: str | None
    tokens_in: int
    tokens_out: int
    cache_read: int
    cache_write: int
    cost_usd: float | None
    cost_kind: str


@dataclass(frozen=True)
class ApprovalRecord:
    """One applied change and what let it run: ``by`` is ``request``, ``confirm`` or ``never``."""

    at: str
    command: str
    change_kind: str
    by: str
    words: str | None
    decision_id: str | None


@dataclass(frozen=True)
class SourceRecord:
    """One ``sources`` row as stored: identity columns first, then the summary's (``None`` until set)."""

    key_link: str
    kind: str
    unchangeable: bool
    first_seen: str
    last_read: str
    content_hash: str
    text_origin: str
    title: str | None = None
    author: str | None = None
    author_aliases: str | None = None
    publisher: str | None = None
    platform: str | None = None
    published: str | None = None
    scope_choice: str | None = None
    read_share: float | None = None
    abstract: str | None = None
    rubric_version: str | None = None
    model: str | None = None
    thinking: str | None = None
    escalated: bool | None = None
    rethink_line: str | None = None
    dropped_claims: int | None = None
    support_status: str | None = None
    copies_status: str | None = None
    topics_status: str | None = None
    archived_at: str | None = None


@dataclass(frozen=True)
class StoredSource:
    """What identity needs of a stored source."""

    id: int
    key_link: str
    last_read: str
    archived_at: str | None


@dataclass(frozen=True)
class LinkedSource:
    """The source a link belongs to and the link's kind there (``key`` or ``other``)."""

    source: StoredSource
    kind: str


@dataclass(frozen=True)
class ExpansionRecord:
    """An expanding choice for a page link: ``each_item``, ``each_link`` or ``both``, and when it was made."""

    link: str
    choice: str
    at: str


@dataclass(frozen=True)
class PageText:
    """A source's cleaned page text, its images' SHA-256 hex in page order, and its 64-value MinHash."""

    text: str
    image_hashes: tuple[str, ...]
    minhash: tuple[int, ...]


@dataclass(frozen=True)
class InboxRecord:
    link: str
    added_at: str
    origin: str


@dataclass(frozen=True)
class QuoteRecord:
    """One quote of a claim and the span ``[start, end)`` where it stands in the stored page text."""

    text: str
    start: int
    end: int


@dataclass(frozen=True)
class FlagRecord:
    """The judge's claim-support answer: ``p`` is the probability of "supports"; under 0.8 it is ``flagged``."""

    verdict: str
    p: float
    flagged: bool
    judge_model: str
    at: str


@dataclass(frozen=True)
class ClaimRecord:
    """One claim, recommendation or caveat with its quotes, and its support answer when the judge gave one."""

    section: str
    text: str
    basis: str
    quotes: tuple[QuoteRecord, ...]
    flag: FlagRecord | None = None


@dataclass(frozen=True)
class StoredClaim:
    id: int
    ord: int
    claim: ClaimRecord


@dataclass(frozen=True)
class CopyFlagRecord:
    """The judge's answer whether ``other_source_id`` is the same work; at 0.5 or more it is ``flagged``."""

    other_source_id: int
    p: float
    flagged: bool
    judge_model: str
    at: str


@dataclass(frozen=True)
class HistoryRecord:
    """One summary event: ``added``, ``reread``, ``redone`` or ``redo_failed``."""

    source_id: int
    at: str
    event: str
    rubric_version: str
    model: str
    escalated: bool


@dataclass(frozen=True)
class Neighbour:
    """A stored source found by search, with what a copy check compares."""

    id: int
    key_link: str
    title: str | None
    abstract: str | None


@dataclass(frozen=True)
class StoreCounts:
    """Sources and their current claims (archived sources left out), inbox links, archived sources and unarchived topics."""

    sources: int
    claims: int
    inbox: int
    archived: int
    topics: int


@dataclass(frozen=True)
class JudgeRecord:
    """One Jev answer of a search: the candidate's key link, the probability it helps, and the Jev model version."""

    link: str
    p: float
    model: str


@dataclass(frozen=True)
class QueryRecord:
    """One ``find`` or ``ask``: what was asked, the phrasings searched, the ranker and its records, any fallback note."""

    at: str
    op: str
    original: str
    question: str
    phrasings: tuple[str, ...]
    context: str | None
    ranker: str  # jev, atlas_rerank or bm25
    judge_records: tuple[JudgeRecord, ...] | None  # None when Jev did not rank
    note: str | None


@dataclass(frozen=True)
class TallyRecord:
    """One trust-evidence line: who, the subject, the source link, ``towards`` or ``against``, and when."""

    who: str
    subject: str
    link: str
    direction: str
    at: str



@dataclass(frozen=True)
class StoredTally:
    """A tally line no note proposal has used yet, with its id."""

    id: int
    line: TallyRecord


@dataclass(frozen=True)
class NoteRecord:
    """One trust note: who, the subject, ``towards`` or ``against``, the reason, when it was saved or last changed, and when archived."""

    id: int
    who: str
    subject: str
    lean: str
    reason: str
    at: str
    archived_at: str | None = None


@dataclass(frozen=True)
class CitationRecord:
    """One citation: ``repo`` and ``file`` relied on a source (``source_id``) or on one saved version of a topic
    (``topic_id`` and ``n``) at time ``at``; ``archived_at`` is set once a later add or an archive hides it."""

    repo: str
    file: str
    at: str
    source_id: int | None = None
    topic_id: int | None = None
    n: int | None = None
    archived_at: str | None = None


@dataclass(frozen=True)
class TopicRecord:
    """One topic: its name and brief, whether the catch-up follows it, the time the user last reviewed it with nothing
    to save, the last catch-up's verdict as stored (JSON text), and when it was archived."""

    id: int
    name: str
    brief: str
    followed: bool
    reviewed_up_to: str | None
    last_catchup: str | None
    archived_at: str | None = None


@dataclass(frozen=True)
class VersionClaim:
    """A claim a version cites, copied as it was when the version was saved: the id it was copied from, its text and
    its quote texts."""

    claim_id: int
    text: str
    quotes: tuple[str, ...]


@dataclass(frozen=True)
class MarkRecord:
    """An open mark: the source the judge said matters to a topic, its probability and judge model, and when it was made."""

    source_id: int
    p: float
    judge_model: str
    at: str


@dataclass(frozen=True)
class VersionRecord:
    """One saved version's own fields: the reviewed text, the model and thinking that wrote the draft, the cross-check
    status (``complete`` or ``not cross-checked: <reason>``), the review's reviewers, run, changes and diff, and when it was saved."""

    text: str
    writer_model: str | None
    thinking: str | None
    cross_check: str
    reviewers: tuple[str, ...]
    run: str | None
    changes: str | None
    diff: str | None
    saved_at: str


@dataclass(frozen=True)
class StoredVersion:
    """A saved version with its number in its topic and the claims it copied."""

    n: int
    version: VersionRecord
    claims: tuple[VersionClaim, ...]


@dataclass(frozen=True)
class PlanRecord:
    """One reviewed research plan's own fields: the reviewed text, the cross-check status, the review's reviewers, run
    and changes, and when it was saved."""

    text: str
    cross_check: str
    reviewers: tuple[str, ...]
    run: str | None
    changes: str | None
    saved_at: str


@dataclass(frozen=True)
class PlanItem:
    """One item of a plan as the agent wrote it: its kind (``question``, ``search``, ``source`` or ``page``) and text."""

    kind: str
    text: str


@dataclass(frozen=True)
class StoredPlanItem:
    """A plan item with its place (from 1), its state (``open``, ``done`` or ``skipped``) and when that state was set."""

    ord: int
    item: PlanItem
    state: str
    at: str


@dataclass(frozen=True)
class StoredPlan:
    """A stored plan with its id, its topic's id and its items in order."""

    id: int
    topic_id: int
    plan: PlanRecord
    items: tuple[StoredPlanItem, ...]


class Store(Protocol):
    path: Path

    def size(self) -> int:
        """Bytes on disk of the store file."""
        ...

    def add_call(self, call: CallRecord) -> None:
        """Keep one paid call."""
        ...

    def calls_since(self, at: str) -> list[CallRecord]:
        """Every paid call at or after ``at``, oldest first."""
        ...

    def recent_calls(self, role: str, limit: int) -> list[CallRecord]:
        """The last ``limit`` calls of ``role``, newest first."""
        ...

    def models_not_billed(self, except_role: str) -> list[str]:
        """Each model with a call outside ``except_role`` whose cost is not billed, in name order."""
        ...

    def add_approval(self, approval: ApprovalRecord) -> None:
        """Keep one applied change's approval."""
        ...

    def transaction(self) -> AbstractContextManager[None]:
        """Run the block's writes as one unit: all kept when it ends, none when it raises. Nests."""
        ...

    def source(self, source_id: int) -> StoredSource:
        """The stored source with id ``source_id``."""
        ...

    def source_for_link(self, link: str) -> LinkedSource | None:
        """The source holding the cleaned ``link``, else ``None``."""
        ...

    def source_by_hash(self, content_hash: str) -> StoredSource | None:
        """The first stored source whose content hash is ``content_hash``, else ``None``."""
        ...

    def signatures(self) -> list[tuple[int, tuple[int, ...]]]:
        """Every stored source's id with its page text's MinHash, by id."""
        ...

    def page_text(self, source_id: int) -> PageText:
        """The stored page text of source ``source_id``."""
        ...

    def add_source(self, source: SourceRecord, page: PageText) -> int:
        """Keep one new source and its page text; returns the source's id."""
        ...

    def update_page(self, source_id: int, content_hash: str, last_read: str, page: PageText) -> None:
        """Replace a source's page text, content hash and read time after a re-read."""
        ...

    def add_link(self, link: str, source_id: int, kind: str, at: str) -> None:
        """Keep one more cleaned link of a source."""
        ...

    def move_link(self, link: str, source_id: int, kind: str) -> None:
        """Give a stored link to another source (a near copy the user stores separately)."""
        ...

    def add_inbox(self, item: InboxRecord) -> None:
        """Keep one link for later."""
        ...

    def inbox(self) -> list[InboxRecord]:
        """Every inbox link, oldest first."""
        ...

    def in_inbox(self, link: str) -> bool:
        """Whether the inbox holds ``link``."""
        ...

    def remove_inbox(self, links: Sequence[str]) -> None:
        """Take ``links`` out of the inbox; links it does not hold are skipped."""
        ...

    def source_record(self, source_id: int) -> SourceRecord:
        """The whole ``sources`` row of source ``source_id``."""
        ...

    def update_summary(self, source_id: int, **columns: object) -> None:
        """Set summary columns of a source; each key is a ``SourceRecord`` field."""
        ...

    def add_claim(self, source_id: int, ord: int, claim: ClaimRecord, at: str) -> int:
        """Keep one claim with its quotes and its support answer, if any; returns the claim's id."""
        ...

    def claims(self, source_id: int) -> list[StoredClaim]:
        """The current (not replaced) claims of a source, in summary order."""
        ...

    def replace_claim(self, claim_id: int, at: str) -> None:
        """Mark a claim replaced: revised or removed by a re-read."""
        ...

    def move_claim(self, claim_id: int, ord: int, quotes: Sequence[QuoteRecord]) -> None:
        """Give a kept claim its new place in the summary and its quotes' spans in the new page text."""
        ...

    def add_related_links(self, source_id: int, links: Sequence[str], origin: str) -> None:
        """Keep links related to a source with their ``origin``.

        ``page``: links the source presents as its sources or next reading; known ones are skipped.
        ``expansion``: the page links whose expanding choice produced the source; each replaces
        a ``page`` row for the same link.
        """
        ...

    def add_expansion(self, expansion: ExpansionRecord) -> None:
        """Keep the expanding choice for a page link; a link that has one keeps its first."""
        ...

    def expansion(self, link: str) -> ExpansionRecord | None:
        """The expanding choice kept for the cleaned page ``link``, else ``None``."""
        ...

    def expansion_sources(self, link: str) -> list[str]:
        """The key links of the unarchived sources the expanding choice for ``link`` produced, by id."""
        ...

    def add_copy_flags(self, source_id: int, flags: Sequence[CopyFlagRecord]) -> None:
        """Keep the judge's same-work answers for a source."""
        ...

    def add_history(self, event: HistoryRecord) -> None:
        """Keep one summary event."""
        ...

    def index_source(self, source_id: int) -> None:
        """Put a source's title, abstract and current claims into the search index, replacing any earlier entry."""
        ...

    def similar(self, text: str, limit: int) -> list[Neighbour]:
        """Up to ``limit`` unarchived sources whose title and abstract best match ``text`` by BM25, best first."""
        ...

    def search(self, text: str, limit: int, since: str | None = None) -> list[int]:
        """Up to ``limit`` unarchived source ids whose title, abstract and claims best match ``text`` by BM25, best first;
        with ``since``, only sources first seen after that time."""
        ...

    def unarchived_source_ids(self) -> list[int]:
        """The ids of every unarchived source, by id."""
        ...

    def claim_sources(self, claim_ids: Sequence[int]) -> dict[int, int]:
        """The id of the source each claim (replaced ones included) belongs to."""
        ...

    def related_links(self, source_ids: Sequence[int]) -> list[tuple[int, str]]:
        """Each related link of the sources ``source_ids`` as stored, with its source's id."""
        ...

    def add_query(self, query: QueryRecord) -> None:
        """Keep one query record."""
        ...

    def add_tally(self, lines: Sequence[TallyRecord]) -> None:
        """Keep trust-evidence lines."""
        ...

    def counts(self) -> StoreCounts:
        """How many sources, current claims, inbox links, archived sources and unarchived topics the store holds."""
        ...

    def older_sources(self, rubric_version: str, model: str | None) -> list[StoredSource]:
        """The unarchived sources whose summary is older than the current setup, by id.

        A summary is older when its rubric version is not ``rubric_version``, or, when ``model`` is
        given, when it was written without escalation by a model other than ``model``. An escalated
        summary is older on a rubric change only.
        """
        ...

    def older_count(self, rubric_version: str, model: str | None) -> int:
        """How many sources ``older_sources`` lists."""
        ...

    def unproposed_tally(self) -> list[StoredTally]:
        """Every tally line no note proposal has used yet, oldest first."""
        ...

    def mark_proposed(self, tally_ids: Sequence[int], at: str) -> None:
        """Set ``proposed_at`` of the tally lines ``tally_ids``; no line is deleted."""
        ...

    def notes(self) -> list[NoteRecord]:
        """Every note, archived ones included, by id."""
        ...

    def add_note(self, who: str, subject: str, lean: str, reason: str, at: str) -> int:
        """Keep one new unarchived note; returns its id."""
        ...

    def change_note(self, note_id: int, lean: str, reason: str, at: str) -> None:
        """Update a note's lean, reason and time in place."""
        ...

    def set_note_archived(self, note_id: int, archived_at: str | None) -> None:
        """Archive a note (a time) or restore it (``None``)."""
        ...

    def set_source_archived(self, source_id: int, archived_at: str | None) -> None:
        """Archive a source (a time) or restore it (``None``); its claims, links and page text stay."""
        ...

    def topic(self, name: str) -> TopicRecord | None:
        """The topic whose name equals ``name``, trimmed and compared case-insensitively (archived topics included), else ``None``."""
        ...

    def topics(self) -> list[TopicRecord]:
        """Every topic, archived ones included, by id."""
        ...

    def add_topic(self, name: str, brief: str) -> int:
        """Keep one new followed, unarchived topic; returns its id."""
        ...

    def set_topic_followed(self, topic_id: int, followed: bool) -> None:
        """Follow or unfollow a topic."""
        ...

    def set_topic_archived(self, topic_id: int, archived_at: str | None) -> None:
        """Archive a topic (a time) or restore it (``None``); its versions, plans and marks stay."""
        ...

    def set_topic_reviewed(self, topic_id: int, reviewed_up_to: str) -> None:
        """Store the time the user last reviewed a topic with nothing to save."""
        ...

    def clear_marks(self, topic_id: int, at: str) -> int:
        """Set ``cleared_at`` of every uncleared mark of a topic; returns how many were cleared."""
        ...

    def add_mark(self, topic_id: int, source_id: int, p: float, judge_model: str, at: str) -> None:
        """Keep a mark of a source for a topic; a source already marked open for the topic keeps one mark, which takes the new
        probability, judge model and time."""
        ...

    def open_marks(self, topic_id: int) -> list[MarkRecord]:
        """A topic's marks that are not cleared, of unarchived sources, by id."""
        ...

    def set_topic_catchup(self, topic_id: int, last_catchup: str) -> None:
        """Store a topic's last catch-up verdict (JSON text)."""
        ...

    def versions(self, topic_id: int) -> list[StoredVersion]:
        """A topic's saved versions with the claims each copied, oldest first (numbered from 1)."""
        ...

    def add_version(self, topic_id: int, version: VersionRecord, claims: Sequence[VersionClaim]) -> int:
        """Keep a topic's next numbered version with the claims it copied; returns its number."""
        ...

    def version_sources(self, topic_id: int) -> list[int]:
        """The ids of the sources that the claims copied into any saved version of a topic came from, by id."""
        ...

    def add_plan(self, topic_id: int, plan: PlanRecord, items: Sequence[PlanItem]) -> int:
        """Keep a topic's plan with its items, all open as of ``plan.saved_at``; returns the plan's id."""
        ...

    def plans(self, topic_id: int | None = None) -> list[StoredPlan]:
        """The stored plans of a topic, or of every topic, newest first."""
        ...

    def plan(self, plan_id: int) -> StoredPlan | None:
        """The stored plan with id ``plan_id``, else ``None``."""
        ...

    def set_plan_item_state(self, plan_id: int, ord: int, state: str, at: str) -> None:
        """Set one plan item's state (``open``, ``done`` or ``skipped``) and the time it was set."""
        ...

    def add_citation(self, citation: CitationRecord) -> None:
        """Keep one citation row (unarchived); it names a source, or a topic and one of its versions, never both."""
        ...

    def file_citations(self, repo: str, file: str) -> list[CitationRecord]:
        """Every citation of ``repo`` and ``file``, archived ones included, by id."""
        ...

    def archive_citations(self, repo: str, file: str, at: str) -> int:
        """Set ``archived_at`` of every unarchived citation of ``repo`` and ``file``; returns how many were archived."""
        ...

    def restore_citations(self, repo: str, file: str) -> int:
        """Clear ``archived_at`` of the citations of ``repo`` and ``file`` that share the file's newest ``archived_at``;
        returns how many were restored."""
        ...

    def source_citations(self, source_id: int) -> list[CitationRecord]:
        """The unarchived citations of an unarchived source, by repo, file and id."""
        ...

    def version_citations(self, topic_id: int, n: int) -> list[CitationRecord]:
        """The unarchived citations of version ``n`` of an unarchived topic, by repo, file and id."""
        ...

    def close(self) -> None: ...
