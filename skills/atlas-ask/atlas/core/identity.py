"""Source identity: which stored source, if any, a given link or page already is.

``add`` and ``add --reread`` call these steps:

1. ``Batch(store, near_copy, items)`` cleans every given link and matches it
   against the stored links before any read. A stored link is never read again:
   it settles as "already stored, last read <date>" or "archived <date>". An
   item with no scope whose link is a page added as each item or each link
   settles as "already added as <n> items" (``expansions``), also unread. A link
   given twice settles once; a link that cannot be cleaned settles as a bad link.
   ``Batch.to_read()`` lists the items left to read, in the given order.
2. ``Batch.examine(item, read)`` takes the read port's answer for one of them.
   A page whose key link (the cleaned link the reader reports) is stored, or
   whose content hash is stored, joins that source ("already stored as <link>").
   A page whose text shares at least ``near_copy`` with a stored source's text
   joins it too ("joined near copy (<share>%)"), with a Next that stores it
   separately instead. A page the batch already handled settles once. Anything
   else is ``new``: the caller summarizes it and calls ``Batch.keep``.
3. ``refresh`` stores a re-read page's text, hash and read time.

Content hash: SHA-256 of the normalized page text (NFC, line endings, each
line's whitespace runs, no blank lines), plus each image's SHA-256 in page order
for an image source. Near copies: word 5-gram shingles of the normalized text;
stored sources whose 64-value MinHash estimate is at least 0.7 are candidates;
the share is the smaller of the two containments, computed exactly on the
stored text.
"""

from __future__ import annotations

import hashlib
import struct
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from atlas import ports
from atlas.core import links, reply, sites, spend
from atlas.store import ExpansionRecord, LinkedSource, PageText, SourceRecord, Store, StoredSource

SHINGLE_WORDS = 5
MINHASH_SIZE = 64
CANDIDATE_ESTIMATE = 0.7
SEPARATE = "separate"  # the scope that stores a near copy as its own source
# The expanding choices whose page a plain re-add matches in ``expansions``; after "both" the page's
# own source holds its link, so ``links`` matches it first.
ITEMS_ONLY = ("each_item", "each_link")

# Outcome kinds.
STORED = "stored"
ARCHIVED = "archived"
JOINED = "joined"
NEAR_COPY = "near_copy"
REPEAT = "repeat"
BAD_LINK = "bad_link"
UNREADABLE = "unreadable"
NEW = "new"
EXPANDED = "expanded"

_MINHASH_VALUES = struct.Struct(f"<{MINHASH_SIZE}I")


def normalize(text: str) -> str:
    """Page text as identity compares it: NFC, ``\\n`` line ends, one space per whitespace run, no blank lines."""
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = (" ".join(line.split()) for line in text.split("\n"))
    return "\n".join(line for line in lines if line)


def image_hash(data: bytes) -> str:
    """One image's SHA-256 hex, as the content hash covers it."""
    return hashlib.sha256(data).hexdigest()


def content_hash(text: str, image_hashes: Sequence[str] = ()) -> str:
    """SHA-256 hex of normalized ``text`` and, for an image source, each image's SHA-256 in page order."""
    digest = hashlib.sha256(text.encode("utf-8"))
    for value in image_hashes:
        digest.update(b"\0" + value.encode("ascii"))
    return digest.hexdigest()


def shingles(text: str) -> frozenset[str]:
    """The word 5-grams of normalized ``text``; a text under 5 words is one shingle, an empty one none."""
    words = text.split()
    if len(words) < SHINGLE_WORDS:
        return frozenset({" ".join(words)}) if words else frozenset()
    return frozenset(" ".join(words[at : at + SHINGLE_WORDS]) for at in range(len(words) - SHINGLE_WORDS + 1))


def minhash(found: Iterable[str]) -> tuple[int, ...]:
    """The 64-value MinHash of a shingle set: per position, the least 32-bit hash over the shingles."""
    rows = [_MINHASH_VALUES.unpack(hashlib.shake_128(item.encode("utf-8")).digest(_MINHASH_VALUES.size)) for item in found]
    if not rows:
        return (0xFFFFFFFF,) * MINHASH_SIZE
    return tuple(min(column) for column in zip(*rows))


def estimate(first: Sequence[int], second: Sequence[int]) -> float:
    """The MinHash estimate of two shingle sets' overlap: the share of equal positions."""
    return sum(a == b for a, b in zip(first, second)) / MINHASH_SIZE


def share(first: frozenset[str], second: frozenset[str]) -> float:
    """The smaller of the two containments: shared shingles over the larger set's size."""
    larger = max(len(first), len(second))
    return len(first & second) / larger if larger else 0.0


def new_text_share(stored: str, new: str) -> float:
    """The share of the new text's shingles the stored text lacks (a re-read's "new text")."""
    found = shingles(new)
    return len(found - shingles(stored)) / len(found) if found else 0.0


def date(stamp: str) -> str:
    """A store time as the local calendar date replies show."""
    return datetime.fromisoformat(stamp).astimezone().date().isoformat()


def percent(value: float) -> int:
    """A share as whole percent, rounded down, so a share under the limit never shows as the limit."""
    return round(value * 10_000) // 100


@dataclass(frozen=True)
class Item:
    """One given link: as given, cleaned (``None`` when it cannot be), and its scope."""

    given: str
    link: str | None
    scope: Any = None


@dataclass(frozen=True)
class NewSource:
    """A read page no stored source holds: what ``Batch.keep`` stores once its summary passes."""

    item: Item
    key_link: str
    page: ports.Page
    text: str
    content_hash: str
    image_hashes: tuple[str, ...]
    unchangeable: bool
    origin: str

    @property
    def links(self) -> tuple[str, ...]:
        """Every cleaned link that led here: the key link first."""
        given = self.item.link
        return (self.key_link,) if given in (None, self.key_link) else (self.key_link, given)


@dataclass(frozen=True)
class Outcome:
    """How one item settled. ``result`` is the reply's per-item text; ``new`` is set for kind ``new``;
    ``items`` and ``expansion`` for kind ``expanded`` (the item sources' key links and the kept choice)."""

    item: Item
    kind: str
    result: str
    source_link: str | None = None
    share: float | None = None
    next: Mapping[str, Any] | None = None
    new: NewSource | None = None
    items: tuple[str, ...] = ()
    expansion: ExpansionRecord | None = None


def separate_step(link: str) -> dict[str, Any]:
    """The Next that stores a joined near copy as its own source instead."""
    return reply.next_step(
        "store it separately instead", {"resend": {"items": [{"link": link, "scope": SEPARATE}]}}
    )


class Batch:
    """One ``add`` batch: every given link matched before any read, each source handled once.

    ``given`` holds each item's link as given and its scope (``None`` for none).
    """

    def __init__(
        self, store: Store, near_copy: float, given: Sequence[tuple[Any, Any]], now: datetime | None = None
    ) -> None:
        self.store = store
        self.near_copy = near_copy
        self.now = now
        self.items: list[Item] = []
        self.settled: dict[int, Outcome] = {}
        self._keys: dict[str, Item] = {}
        self._hashes: dict[str, Item] = {}
        first: dict[str, Item] = {}
        for link, scope in given:
            item = Item(link, clean(link), scope)
            self.items.append(item)
            if item.link is None:
                self._settle(item, BAD_LINK, "not a link Atlas can read: give a full http or https link")
            elif item.link in first:
                self._settle(item, REPEAT, f"same source as {first[item.link].given} in this batch")
            else:
                first[item.link] = item
                self._match(item)
                if id(item) not in self.settled:
                    self._keys[item.link] = item

    def _settle(self, item: Item, kind: str, result: str, **fields: Any) -> Outcome:
        outcome = Outcome(item, kind, result, **fields)
        self.settled[id(item)] = outcome
        return outcome

    def _stamp(self) -> str:
        return spend.stamp(self.now or spend.local_now())

    def _match(self, item: Item) -> None:
        assert item.link is not None
        found = self.store.source_for_link(item.link)
        if found is None:
            kept = self.store.expansion(item.link) if item.scope is None else None
            if kept is not None and kept.choice in ITEMS_ONLY:
                sources = tuple(self.store.expansion_sources(item.link))
                self._settle(item, EXPANDED, f"already added as {len(sources)} items", items=sources, expansion=kept)
            return
        source = found.source
        if source.archived_at is not None:
            self._settle(item, ARCHIVED, f"archived {date(source.archived_at)}", source_link=source.key_link)
        elif not (item.scope == SEPARATE and found.kind == "other"):
            self._settle(item, STORED, f"already stored, last read {date(source.last_read)}", source_link=source.key_link)

    def _separating(self, item: Item, found: LinkedSource) -> bool:
        """Whether ``item`` asks to store separately a near copy whose joined links include ``found``."""
        if item.scope != SEPARATE or found.kind != "other":
            return False
        given = self.store.source_for_link(item.link) if item.link is not None else None
        return given is not None and given.source.id == found.source.id

    def outcome(self, item: Item) -> Outcome | None:
        """How ``item`` settled, or ``None`` while it waits for its read or summary."""
        return self.settled.get(id(item))

    def to_read(self) -> list[Item]:
        """The items no stored link settled, in the given order: the only links to read."""
        return [item for item in self.items if id(item) not in self.settled]

    def examine(
        self,
        item: Item,
        read: ports.Page | ports.Unreadable,
        images: Sequence[bytes] = (),
        origin: str = "read",
    ) -> Outcome:
        """Settle ``item`` from its read; ``images`` are an image source's bytes in page order."""
        if id(item) in self.settled:
            raise ValueError(f"{item.given} is already settled; only to_read() items are read")
        assert item.link is not None
        if isinstance(read, ports.Unreadable):
            return self._settle(item, UNREADABLE, f"unreadable: {read.reason}")
        key = clean(read.final_link) or item.link
        joins = [item.link] if key == item.link else [item.link, key]

        if key != item.link:
            earlier = self._keys.get(key)
            if earlier is not None:
                return self._settle(item, REPEAT, f"same source as {earlier.given} in this batch")
            found = self.store.source_for_link(key)
            if found is not None and not self._separating(item, found):
                return self._join(item, found.source, [item.link], JOINED)
            self._keys[key] = item

        text = normalize(read.text)
        hashes = tuple(image_hash(data) for data in images)
        digest = content_hash(text, hashes)
        earlier = self._hashes.get(digest)
        if earlier is not None:
            return self._settle(item, REPEAT, f"same source as {earlier.given} in this batch")
        self._hashes[digest] = item
        same = self.store.source_by_hash(digest)
        if same is not None:
            return self._join(item, same, joins, JOINED)

        if item.scope != SEPARATE:
            near = self._near_copy(text)
            if near is not None:
                return self._join(item, near[0], joins, NEAR_COPY, near[1])

        new = NewSource(item, key, read, text, digest, hashes, sites.unchangeable(key), origin)
        return Outcome(item, NEW, "new", new=new)

    def _near_copy(self, text: str) -> tuple[StoredSource, float] | None:
        found = shingles(text)
        signature = minhash(found)
        best: tuple[int, float] | None = None
        for source_id, stored in self.store.signatures():
            if estimate(signature, stored) < CANDIDATE_ESTIMATE:
                continue
            value = share(found, shingles(self.store.page_text(source_id).text))
            if value >= self.near_copy and (best is None or value > best[1]):
                best = (source_id, value)
        if best is None:
            return None
        return self.store.source(best[0]), best[1]

    def _join(
        self, item: Item, source: StoredSource, joins: Sequence[str], kind: str, value: float | None = None
    ) -> Outcome:
        at = self._stamp()
        with self.store.transaction():
            for link in joins:
                if self.store.source_for_link(link) is None:
                    self.store.add_link(link, source.id, "other", at)
            self.store.remove_inbox(joins)
        if source.archived_at is not None:
            return self._settle(item, ARCHIVED, f"archived {date(source.archived_at)}", source_link=source.key_link)
        if kind == NEAR_COPY:
            assert value is not None and item.link is not None
            return self._settle(
                item,
                NEAR_COPY,
                f"joined near copy ({percent(value)}%)",
                source_link=source.key_link,
                share=value,
                next=separate_step(item.link),
            )
        return self._settle(item, JOINED, f"already stored as {source.key_link}", source_link=source.key_link)

    def keep(self, new: NewSource, text: str | None = None, **summary: Any) -> int:
        """Store ``new`` once its summary passed: the source row, its links and its page text.

        ``text`` is the page text to keep when it differs from the read text (an
        image source's transcriptions appended); the hash stays the read one.
        ``summary`` holds the summary's ``SourceRecord`` columns. Returns the id.
        """
        at = self._stamp()
        kept = new.text if text is None else text
        record = SourceRecord(
            key_link=new.key_link,
            kind=new.page.kind_hint,
            unchangeable=new.unchangeable,
            first_seen=at,
            last_read=at,
            content_hash=new.content_hash,
            text_origin=new.origin,
            **summary,
        )
        page = PageText(kept, new.image_hashes, minhash(shingles(kept)))
        with self.store.transaction():
            source_id = self.store.add_source(record, page)
            for link in new.links:
                kind = "key" if link == new.key_link else "other"
                if self.store.source_for_link(link) is None:
                    self.store.add_link(link, source_id, kind, at)
                else:
                    self.store.move_link(link, source_id, kind)
            self.store.remove_inbox(new.links)
        self._settle(new.item, NEW, "added", source_link=new.key_link)
        return source_id


def clean(link: Any) -> str | None:
    """``link`` after link cleanup, or ``None`` when it is not a full http or https link."""
    try:
        return links.normalize_canonical_url(link)
    except (TypeError, ValueError):
        return None


def lookup(store: Store, link: Any) -> StoredSource | None:
    """The stored source holding ``link`` after cleanup (``add --reread``'s match), else ``None``."""
    cleaned = clean(link)
    found = None if cleaned is None else store.source_for_link(cleaned)
    return None if found is None else found.source


def refresh(
    store: Store,
    source: StoredSource,
    read: ports.Page,
    text: str | None = None,
    images: Sequence[bytes] = (),
    now: datetime | None = None,
) -> None:
    """Keep a re-read page: its text, hash and read time, and its newly reported link.

    ``text`` is the page text to keep when it differs from the normalized read
    text (image transcriptions appended); the hash covers the read text and the
    image bytes.
    """
    at = spend.stamp(now or spend.local_now())
    read_text = normalize(read.text)
    kept = read_text if text is None else text
    hashes = tuple(image_hash(data) for data in images)
    with store.transaction():
        store.update_page(source.id, content_hash(read_text, hashes), at, PageText(kept, hashes, minhash(shingles(kept))))
        reported = clean(read.final_link)
        if reported is not None and store.source_for_link(reported) is None:
            store.add_link(reported, source.id, "other", at)
