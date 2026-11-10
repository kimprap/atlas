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

    def close(self) -> None: ...
