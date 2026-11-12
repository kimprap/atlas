"""Repo citations (spec 4.14, stage 8): the ``cited_in`` body of ``add``, the writes to ``citations``, and the lists
of citing repos and files a reply names.

``cited_in`` is ``{"repo", "file", "topics"?, "join"?}``: the repo (``owner/name``) and the repo-root-relative file
whose research relied on the items' sources and on the topic versions in ``topics`` (``{"topic", "version"}``).
``Writer`` does the writes of one ``add``: the first citing transaction replaces the file's earlier citations
(unless ``join``) and stores the topic versions; each source is one row. A replaced row gets ``archived_at``; no
row is deleted.

A reply that changes a claim names who cites it with ``of_source``, ``of_topic`` and ``attach``: each citation is
``{repo, file, date}`` plus ``link`` (a source's key link) or ``topic`` and ``version``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from atlas.core import identity, reply, spend
from atlas.store import CitationRecord, Store

_FIELDS = ("repo", "file", "topics", "join")


@dataclass(frozen=True)
class Cite:
    """A checked ``cited_in``: ``topics`` are (topic id, version number) pairs, without repeats."""

    repo: str
    file: str
    topics: tuple[tuple[int, int], ...]
    join: bool


def _text(value: Any) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _topics(value: Any, store: Store) -> tuple[tuple[int, int], ...] | dict[str, Any]:
    """The (topic id, version) pairs ``value`` names, without repeats, or the problem."""
    if not isinstance(value, list):
        return reply.problem("cited_in.topics", "topics must be a list of {topic, version} objects")
    found: dict[tuple[int, int], None] = {}
    for index, entry in enumerate(value):
        field = f"cited_in.topics[{index}]"
        if not isinstance(entry, Mapping) or set(entry) != {"topic", "version"}:
            return reply.problem(field, "each topic is an object with exactly topic and version")
        name = _text(entry["topic"])
        topic = None if name is None else store.topic(name)
        if topic is None:
            return reply.problem(f"{field}.topic", "topic must be the name of a stored topic")
        version = entry["version"]
        if isinstance(version, bool) or not isinstance(version, int) or version not in {saved.n for saved in store.versions(topic.id)}:
            return reply.problem(f"{field}.version", f"version must be a saved version number of {topic.name}")
        found[(topic.id, version)] = None
    return tuple(found)


def parse(value: Any, store: Store) -> Cite | dict[str, Any]:
    """The checked ``cited_in``, or the problem that makes it bad input."""
    if not isinstance(value, Mapping):
        return reply.problem("cited_in", "cited_in must be an object with repo and file, and optionally topics and join")
    extra = sorted(set(value) - set(_FIELDS))
    if extra:
        return reply.problem(f"cited_in.{extra[0]}", f'"{extra[0]}" is not a field of cited_in; it takes {", ".join(_FIELDS)}')
    repo = _text(value.get("repo"))
    if repo is None:
        return reply.problem("cited_in.repo", "repo must be non-empty text, the citing repo as owner/name")
    file = _text(value.get("file"))
    if file is None or file.startswith("/"):
        return reply.problem("cited_in.file", "file must be non-empty text: a path from the repo root, not starting with /")
    join = value.get("join", False)
    if not isinstance(join, bool):
        return reply.problem("cited_in.join", "join must be true or false")
    topics: tuple[tuple[int, int], ...] = ()
    if "topics" in value:
        found = _topics(value["topics"], store)
        if isinstance(found, dict):
            return found
        topics = found
    return Cite(repo, file, topics, join)


class Writer:
    """The citation writes of one ``add``; every method runs inside the transaction of the item it belongs to."""

    def __init__(self, store: Store, cite: Cite) -> None:
        self.store = store
        self.cite = cite
        self.opened = False
        self.sources = 0
        self.topics = 0
        self.replaced = 0

    def _held(self) -> list[CitationRecord]:
        """The file's current (unarchived) citations."""
        return [row for row in self.store.file_citations(self.cite.repo, self.cite.file) if row.archived_at is None]

    def open(self) -> None:
        """The first citing transaction's work: archive the file's earlier citations (unless joining) and store the topic
        versions the file does not already cite."""
        if self.opened:
            return
        self.opened = True
        cite, at = self.cite, spend.stamp(spend.local_now())
        if not cite.join:
            self.replaced = self.store.archive_citations(cite.repo, cite.file, at)
        held = {(row.topic_id, row.n) for row in self._held()}
        for topic_id, n in cite.topics:
            if (topic_id, n) not in held:
                self.store.add_citation(CitationRecord(cite.repo, cite.file, at, topic_id=topic_id, n=n))
                self.topics += 1

    def source(self, source_id: int) -> None:
        """Cite source ``source_id`` for the file, unless the file already cites it unarchived."""
        self.open()
        cite = self.cite
        if any(row.source_id == source_id for row in self._held()):
            return
        self.store.add_citation(CitationRecord(cite.repo, cite.file, spend.stamp(spend.local_now()), source_id=source_id))
        self.sources += 1

    def counts(self) -> dict[str, Any]:
        """The reply's ``result.cited_in``."""
        return {
            "repo": self.cite.repo,
            "file": self.cite.file,
            "sources": self.sources,
            "topics": self.topics,
            "replaced": self.replaced,
        }


def _named(row: CitationRecord, **what: Any) -> dict[str, Any]:
    return {"repo": row.repo, "file": row.file, "date": identity.date(row.at), **what}


def of_source(store: Store, source_id: int) -> list[dict[str, Any]]:
    """The named citations of source ``source_id``: unarchived rows of an unarchived source, by repo and file."""
    rows = store.source_citations(source_id)
    link = store.source(source_id).key_link if rows else ""
    return [_named(row, link=link) for row in rows]


def of_version(store: Store, topic_id: int, name: str, n: int) -> list[dict[str, Any]]:
    """The named citations of version ``n`` of an unarchived topic, by repo and file."""
    return [_named(row, topic=name, version=n) for row in store.version_citations(topic_id, n)]


def of_topic(store: Store, name: str) -> list[dict[str, Any]]:
    """The named citations of a topic's agreed (latest saved) version."""
    topic = store.topic(name)
    versions = [] if topic is None else store.versions(topic.id)
    return of_version(store, topic.id, topic.name, versions[-1].n) if topic is not None and versions else []


def attach(entry: dict[str, Any], *groups: Sequence[dict[str, Any]]) -> None:
    """Add ``cited_in``, the groups one after the other, to ``entry`` when they name any citation."""
    found = [named for group in groups for named in group]
    if found:
        entry["cited_in"] = found
