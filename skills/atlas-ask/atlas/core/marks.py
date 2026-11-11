"""Topic marks and claim-change flags (spec 4.5 marks row, 4.12; ticket 17 sections 1 item 5 and 3).

``match`` runs after ``add`` stores a source and after a redo whose claims changed (``claims_changed``): one Jev noul
per followed, unarchived topic over the source's title, abstract and claims against the topic's brief and its agreed
version's reviewed text (the brief alone when the topic has no agreed version). P of 0.3 or more adds a mark with the P
and the Jev model version (``Store.add_mark``); a source already marked open for the topic keeps one mark. The source's
``topics_status`` becomes ``checked``. With the profile on Opus, or Jev not set up, no judge call is made and nothing is
marked or recorded; when Jev fails after its backoff the source's ``topics_status`` is ``topics not matched`` and the
reply says so. With no followed topic no judge call is made at all. Marks only add sources to a catch-up and order it.

``flagged_topics`` is derived, never stored: after a redo or re-read changed a source's claims, each unarchived topic
whose agreed version (its latest saved one) holds a copy of one of that source's claims is compared with the source's
claims now, by quote. A copy that no current claim shares a quote with is removed; one whose sharing claim differs in
text or in its set of quotes is changed; either flags the topic.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from atlas import ports
from atlas.core import spend, summarize
from atlas.store import SourceRecord, Store, StoredClaim, TopicRecord, VersionClaim

MATCH_QUESTION = "Could this source change or add to a conclusion of this topic?"
MARK_AT = 0.3
MATCHED = "checked"
NOT_MATCHED = "topics not matched"


@dataclass(frozen=True)
class Matched:
    """What one source's matching did: the names of the topics it was marked for, and the ``topics_status`` it left
    (``None`` when no judge call was made)."""

    marked: tuple[str, ...] = ()
    status: str | None = None

    def apply(self, entry: dict[str, Any]) -> None:
        """Show the matching on a reply item: the topics marked, or that they were not matched."""
        if self.marked:
            entry["topics_marked"] = list(self.marked)
        if self.status == NOT_MATCHED:
            entry["topics"] = NOT_MATCHED


def followed(store: Store) -> list[TopicRecord]:
    """The topics the catch-up follows: followed and not archived."""
    return [topic for topic in store.topics() if topic.followed and topic.archived_at is None]


def _view(record: SourceRecord, claims: Sequence[StoredClaim]) -> str:
    lines = [record.title or record.key_link, f"Abstract: {record.abstract or 'none'}", "Claims:", *(f"- {stored.claim.text}" for stored in claims)]
    return "\n".join(lines)


def _state(topic: TopicRecord, agreed: str | None, view: str) -> str:
    head = f"Topic: {topic.name}\nBrief: {topic.brief}"
    if agreed is not None:
        head += f"\nAgreed version, the understanding the user last saved:\n{agreed}"
    return f"{head}\n\nSource:\n{view}"


def match(deps: summarize.Deps, source_id: int) -> Matched:
    """Mark the followed topics a newly stored or redone source matters to; see the module docstring."""
    store = deps.store
    topics = followed(store)
    if not topics or not summarize.judge_ready(deps):
        return Matched()
    view = _view(store.source_record(source_id), store.claims(source_id))
    asked = ports.Question("topic", "noul", MATCH_QUESTION)
    requests = []
    for topic in topics:
        versions = store.versions(topic.id)
        requests.append((_state(topic, versions[-1].version.text if versions else None, view), asked))
    try:
        answers = summarize.judge_all(deps, requests)
    except (ports.JudgeFailed, ports.JudgeNotSetUp):
        store.update_summary(source_id, topics_status=NOT_MATCHED)
        return Matched((), NOT_MATCHED)
    at = spend.stamp(deps.clock())
    marked = []
    with store.transaction():
        store.update_summary(source_id, topics_status=MATCHED)
        for topic, got in zip(topics, answers):
            p = float(next(iter(got.answers.values())).p or 0.0)
            if p >= MARK_AT:
                store.add_mark(topic.id, source_id, round(p, 6), got.model, at)
                marked.append(topic.name)
    return Matched(tuple(marked), MATCHED)


def _identity(text: str, quotes: Sequence[str]) -> tuple[str, frozenset[str]]:
    return " ".join(text.split()), frozenset(" ".join(quote.split()) for quote in quotes)


def claims_changed(old: Sequence[StoredClaim], new: Sequence[StoredClaim]) -> bool:
    """Whether the claims a redo left differ from the ones it replaced: some claim has no counterpart of the same text and quotes."""
    before = {_identity(stored.claim.text, [quote.text for quote in stored.claim.quotes]) for stored in old}
    after = {_identity(stored.claim.text, [quote.text for quote in stored.claim.quotes]) for stored in new}
    return before != after


def _altered(copy: VersionClaim, current: Sequence[StoredClaim]) -> bool:
    """Whether a version's copy of a claim was changed or removed, by quote (by text for a copy with no quote)."""
    kept = _identity(copy.text, copy.quotes)
    sharing = []
    for stored in current:
        found = _identity(stored.claim.text, [quote.text for quote in stored.claim.quotes])
        if (kept[1] & found[1]) or (not kept[1] and not found[1] and kept[0] == found[0]):
            sharing.append(found)
    return kept not in sharing


def flagged_topics(store: Store, source_id: int) -> list[str]:
    """The names of the unarchived topics whose agreed version cites a claim of the source that is now changed or removed."""
    current = store.claims(source_id)
    names = []
    for topic in store.topics():
        versions = store.versions(topic.id) if topic.archived_at is None else []
        if not versions:
            continue
        copies = versions[-1].claims
        owners = store.claim_sources([copy.claim_id for copy in copies])
        if any(_altered(copy, current) for copy in copies if owners.get(copy.claim_id) == source_id):
            names.append(topic.name)
    return names
