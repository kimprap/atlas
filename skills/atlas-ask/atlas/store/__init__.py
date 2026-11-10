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
    """The source a link belongs to and the link's kind there (``key``, ``other`` or ``related_repo``)."""

    source: StoredSource
    kind: str


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
    """Sources and their current claims (archived sources left out), inbox links and archived sources."""

    sources: int
    claims: int
    inbox: int
    archived: int


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

    def add_related_links(self, source_id: int, links: Sequence[str]) -> None:
        """Keep the links a source presents as its sources or next reading; known ones are skipped."""
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

    def counts(self) -> StoreCounts:
        """How many sources, current claims, inbox links and archived sources the store holds."""
        ...

    def close(self) -> None: ...
