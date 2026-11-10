"""The replay read adapter: a read port that answers from stored page records and never reads the network.

The quality tool gives both versions it compares the same page text through this
adapter (spec 4.15). It is built with ``PageRecord`` values. A link a record
holds, or one joined to it, returns the record's key link as ``final_link``,
its kind, its items and its kept text for the asked scope; an image link
returns the recorded bytes; a link no record holds returns ``Unreadable``.

The Atlas store keeps cleaned page text and image SHA-256s only, no image bytes
and no repo items, so records built from the ``eval`` store (``store_records``)
have no items and no image bytes: ``image`` is ``Unreadable`` for them. Records
loaded from a recorded fixture (``load_records``) carry both.
"""

from __future__ import annotations

import base64
import json
import zlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.quality import _path, evaldb  # noqa: F401  (_path puts the atlas package on sys.path)

from atlas import ports  # noqa: E402

NOT_HELD = "the replay library holds no page for this link"


@dataclass(frozen=True)
class PageRecord:
    """One stored page: its key link, the other links that reach it and what a read returns.

    ``transcript`` is the page text a ``transcript`` read returns, ``None`` when
    the page has none; ``image_bytes`` maps an image link to its recorded bytes.
    """

    link: str
    kind: str
    text: str
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    published: str | None = None
    joined: tuple[str, ...] = ()
    links: tuple[str, ...] = ()
    images: tuple[str, ...] = ()
    items: tuple[ports.RepoItem, ...] = ()
    transcript: str | None = None
    image_bytes: Mapping[str, bytes] = field(default_factory=dict)

    @classmethod
    def from_json(cls, value: Mapping[str, Any]) -> PageRecord:
        return cls(
            link=value["link"],
            kind=value["kind"],
            text=value["text"],
            title=value.get("title"),
            author=value.get("author"),
            publisher=value.get("publisher"),
            published=value.get("published"),
            joined=tuple(value.get("joined", ())),
            links=tuple(value.get("links", ())),
            images=tuple(value.get("images", ())),
            items=tuple(ports.RepoItem(i["path"], i["link"], i["kind"]) for i in value.get("items", ())),
            transcript=value.get("transcript"),
            image_bytes={link: base64.b64decode(data) for link, data in value.get("image_bytes", {}).items()},
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "link": self.link,
            "kind": self.kind,
            "text": self.text,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "published": self.published,
            "joined": list(self.joined),
            "links": list(self.links),
            "images": list(self.images),
            "items": [{"path": i.path, "link": i.link, "kind": i.kind} for i in self.items],
            "transcript": self.transcript,
            "image_bytes": {link: base64.b64encode(data).decode("ascii") for link, data in self.image_bytes.items()},
        }

    def page(self, text: str, kind: str) -> ports.Page:
        return ports.Page(
            final_link=self.link,
            title=self.title,
            author=self.author,
            publisher=self.publisher,
            published=self.published,
            kind_hint=kind,
            text=text,
            images=self.images,
            links=self.links,
            counts=ports.Counts(len(text.split()), len(self.links), len(self.images)),
            items=self.items,
        )


class ReplayRead:
    """``ports.ReadPort`` over page records; it opens no socket and starts no process."""

    def __init__(self, records: Iterable[PageRecord]) -> None:
        self._by_link: dict[str, PageRecord] = {}
        for record in records:
            for link in (record.link, *record.joined):
                self._by_link.setdefault(link, record)
        self._images = {link: data for record in self._by_link.values() for link, data in record.image_bytes.items()}

    def read(self, link: str, scope: ports.Scope = None) -> ports.Page | ports.Unreadable:
        record = self._by_link.get(link)
        if record is None:
            return ports.Unreadable("gone", NOT_HELD)
        if scope == "transcript":
            if record.transcript is None:
                return ports.Unreadable("no_transcript", "the stored page has no transcript")
            return record.page(record.transcript, "video")
        return record.page(record.text, record.kind)

    def image(self, link: str) -> bytes | ports.Unreadable:
        data = self._images.get(link)
        return data if data is not None else ports.Unreadable("gone", NOT_HELD)


def load_records(path: Path) -> list[PageRecord]:
    """The records of a recorded fixture: a JSON file with a ``records`` list."""
    return [PageRecord.from_json(item) for item in json.loads(path.read_text(encoding="utf-8"))["records"]]


def store_records(db: Path) -> list[PageRecord]:
    """One record per stored source of the ``eval`` store at ``db``: its kept page text and every link that reaches it.

    The store holds no image bytes and no repo items, so these records have none; a video
    source's kept text is its transcript.
    """
    with evaldb.readonly(db) as conn:
        joined: dict[int, list[str]] = {}
        for source_id, link in conn.execute("SELECT source_id, link FROM links WHERE kind = 'other' ORDER BY link"):
            joined.setdefault(source_id, []).append(link)
        rows = conn.execute(
            "SELECT s.id, s.key_link, s.kind, s.title, s.author, s.publisher, s.published, p.text"
            " FROM sources s JOIN page_text p ON p.source_id = s.id ORDER BY s.id"
        ).fetchall()
    records = []
    for source_id, link, kind, title, author, publisher, published, blob in rows:
        text = zlib.decompress(blob).decode("utf-8")
        records.append(
            PageRecord(
                link=link,
                kind=kind,
                text=text,
                title=title,
                author=author,
                publisher=publisher,
                published=published,
                joined=tuple(joined.get(source_id, ())),
                transcript=text if kind == "video" else None,
            )
        )
    return records
