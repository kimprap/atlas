"""``add --reread``: read stored sources again and update only what changed.

Body: ``{"items": [{"link"}]}``, each a link a stored source holds. The sources
to re-read are one change of kind ``add_reread`` under the approval rules;
re-reading 2 or more is paid at scale, and its confirm states the estimate from
the stored pages' sizes. The cap and window guard run as for ``add``. The one
``approvals`` row is written inside the first source the command updates.

For each source the page is read again the way it was added: its kept
``scope_choice`` picks the transcript, the sections or the first part. An image source's images are fetched
again; while their bytes are unchanged, the stored transcriptions are kept
(a new transcription is not a change). Then:

- every cited quote still found and less than ``reread_new_text`` of the new
  text's shingles new: the new hash, read time and text are stored, and the
  summary is kept ("re-read, no meaningful change");
- otherwise the stored and new text are compared by line. Affected claims are
  those with a quote gone or inside a changed region. One update call gets the
  unaffected claims as fixed, the affected ones to keep, revise or remove, and
  the changed regions to add from; the rethink turn, checks and claim support
  run on the changed claims only. Unchanged claims keep their ids and get their
  quotes' new places ("updated (<n> claims changed)").

An unreadable page keeps the stored source ("unreadable, kept"), and so does a
page that grew past the page limit when no part was chosen at its add (a cut
now would count the rest as gone; a ``scope`` problem says so). An update that
fails after its escalation stores nothing and returns a ``summary_failed``
decision.
"""

from __future__ import annotations

import difflib
from collections.abc import Mapping, Sequence
from typing import Any

from atlas import ports
from atlas.core import add, approvals, identity, reply, spend, summarize
from atlas.core.config import Profile
from atlas.store import HistoryRecord, QuoteRecord, Store, StoredClaim, StoredSource

COMMAND = "add"
MODE = "reread"
CALLED = "add --reread"
FIELDS = {"profile", "approval", "items"}
ITEM_FIELDS = {"link"}
_IMAGE_BLOCK = "[image 1, transcribed by "


def _bad(problem: dict[str, Any]) -> tuple[dict[str, Any], int]:
    return reply.build(COMMAND, reply.BAD_INPUT, problems=[problem]), reply.BAD_INPUT


def transcriptions(text: str) -> str:
    """The stored ``[image <n>, transcribed by <model>]`` blocks at the end of a page text, or ``""``."""
    at = text.find(_IMAGE_BLOCK)
    while at > 0 and text[at - 1] != "\n":
        at = text.find(_IMAGE_BLOCK, at + 1)
    return text[at:] if at >= 0 else ""


def changed_regions(old: str, new: str) -> tuple[list[tuple[int, int]], list[str]]:
    """The old text's changed character ranges, and the new text's changed regions, by a line diff."""
    old_lines, new_lines = old.split("\n"), new.split("\n")
    offsets = [0]
    for line in old_lines:
        offsets.append(offsets[-1] + len(line) + 1)
    ranges: list[tuple[int, int]] = []
    regions: list[str] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if i2 > i1:
            ranges.append((offsets[i1], offsets[i2]))
        if j2 > j1:
            regions.append("\n".join(new_lines[j1:j2]))
    return ranges, regions


def affected(claims: Sequence[StoredClaim], index: summarize.PageIndex, ranges: Sequence[tuple[int, int]]) -> list[StoredClaim]:
    """The claims with a quote gone from the new text or inside a changed range of the old text."""
    found = []
    for stored in claims:
        quotes = stored.claim.quotes
        gone = any(index.find(quote.text) is None for quote in quotes)
        touched = any(quote.start < high and quote.end > low for quote in quotes for low, high in ranges)
        if gone or touched:
            found.append(stored)
    return found


class Reread:
    """One ``add --reread`` command on an opened store."""

    def __init__(self, body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> None:
        self.body = body
        self.profile = profile
        self.store = store
        self.host = host
        self.deps = summarize.Deps(host, profile, store, CALLED)
        self.items: list[dict[str, Any]] = []
        self.problems: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.approved: tuple[approvals.Change, approvals.Go] | None = None

    def _applied(self) -> None:
        """Write the command's one ``approvals`` row, inside the transaction of the first source it updates."""
        if self.approved is not None:
            approvals.record(self.store, *self.approved)
            self.approved = None

    def _question(self, sources: Sequence[StoredSource], at_scale: bool, guard: spend.Guard) -> str:
        if not at_scale:
            return f"Re-read {sources[0].key_link} and update its summary where the page changed?"
        selector = None
        if self.host.facts is not None:
            try:
                selector = self.host.facts.roles().get(summarize.SUMMARIZE)
            except ports.CallFailed:
                selector = None
        if selector is None:
            estimate = "cost unknown: the summary model is not known"
        else:
            costs = [
                spend.estimate_item(self.store, self.profile, selector, summarize.page_tokens(self.store.page_text(source.id).text))
                for source in sources
            ]
            total = None if any(cost is None for cost in costs) else sum(costs)  # type: ignore[arg-type]
            estimate = spend.estimate_text(total, selector) + " if every page changed"
        named = ", ".join(source.key_link for source in sources)
        return f"Re-read {len(sources)} sources ({named}) and update their summaries where the pages changed? Estimated cost: {estimate}. Window use: {guard.window_use()}."

    def run(self) -> tuple[dict[str, Any], int]:
        problem = add.items_problem(self.body, FIELDS, ITEM_FIELDS)
        if problem is not None:
            return _bad(problem)
        sources: list[StoredSource] = []
        for item in self.body["items"]:
            source = identity.lookup(self.store, item["link"])
            if source is None:
                self.problems.append(reply.problem("items", "not stored; add it first", item["link"]))
            elif source.archived_at is not None:
                self.items.append({"link": source.key_link, "result": f"archived {identity.date(source.archived_at)}"})
            elif all(source.id != seen.id for seen in sources):
                sources.append(source)
        if sources:
            stopped = self._run(sources)
            if stopped is not None:
                return stopped
        steps = [reply.next_step("ask about these sources with `ask`", {"stop": True})]
        result = {"items": self.items}
        if self.decisions:
            answer = reply.build(COMMAND, reply.NEEDS_DECISION, result=result, problems=self.problems, next=steps, decisions=self.decisions)
            return answer, reply.NEEDS_DECISION
        return reply.build(COMMAND, reply.DONE, result=result, problems=self.problems, next=steps), reply.DONE

    def _stop(self, decisions: list[dict[str, Any]]) -> tuple[dict[str, Any], int]:
        answer = reply.build(COMMAND, reply.NEEDS_DECISION, result={"items": self.items}, problems=self.problems, decisions=decisions)
        return answer, reply.NEEDS_DECISION

    def _run(self, sources: list[StoredSource]) -> tuple[dict[str, Any], int] | None:
        missing = add.role_items(self.host, add.ROLES)
        if missing:
            return add.not_set_up(COMMAND, missing, {"items": self.items})
        at_scale = len(sources) >= 2
        guard = spend.Guard(self.store, self.profile, self.host, add.ROLES, paid=True, batch=at_scale)
        change = approvals.Change(
            command=COMMAND,
            mode=MODE,
            body=self.body,
            kind="add_reread",
            question=self._question(sources, at_scale, guard),
            links=[source.key_link for source in sources],
            paid_at_scale=at_scale,
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
                return add.not_set_up(COMMAND, add.role_items(self.host, (err.role,)), {"items": self.items})
        return None

    def _one(self, source: StoredSource) -> None:
        link = source.key_link
        record = self.store.source_record(source.id)
        scope = add.stored_scope(record.scope_choice)
        read = self.host.read.read(link, add.read_scope(scope))
        if isinstance(read, ports.Unreadable):
            self.items.append({"link": link, "result": "unreadable, kept"})
            return
        limit = add.page_limit(self.host, self.profile)
        bounded = scope == add.FIRST_PART or isinstance(scope, Mapping) or record.read_share is not None
        tokens = summarize.page_tokens(identity.normalize(read.text))
        if not bounded and tokens > limit:
            # No part was chosen when it was added: a cut now would count the rest of the page as gone.
            problem = f"the page grew to about {tokens:,} tokens, over the {limit:,}-token limit; the stored summary is kept"
            self.problems.append(reply.problem("scope", problem, link))
            self.items.append({"link": link, "result": "unreadable, kept"})
            return
        scoped = add.scoped_text(read, scope, limit)
        if isinstance(scoped, str):
            self.problems.append(reply.problem("scope", scoped, link))
            self.items.append({"link": link, "result": "unreadable, kept"})
            return
        stored = self.store.page_text(source.id)
        images: list[bytes] = []
        if stored.image_hashes:
            for image_link in read.images:
                got = self.host.read.image(image_link)
                if isinstance(got, ports.Unreadable):
                    self.items.append({"link": link, "result": "unreadable, kept"})
                    return
                images.append(got)
        same_images = tuple(identity.image_hash(data) for data in images) == stored.image_hashes
        new_text = scoped[0]
        kept_blocks = transcriptions(stored.text) if stored.image_hashes and same_images else ""
        full = "\n".join(part for part in (new_text, kept_blocks) if part)
        claims = self.store.claims(source.id)
        index = summarize.PageIndex(full)
        ranges, regions = changed_regions(stored.text, full)
        hit = affected(claims, index, ranges)
        gone = [stored_claim for stored_claim in hit if any(index.find(q.text) is None for q in stored_claim.claim.quotes)]
        if not gone and same_images and identity.new_text_share(stored.text, full) < self.profile.reread_new_text:
            self._keep_as_is(source, read, full, images, claims, index)
            return
        kind = add.kind_of(read, link)
        page_input = summarize.PageInput(
            page=read,
            text=new_text if not same_images else full,
            kind=add.TRANSCRIPT if kind == "video" else kind,
            link=link,
            images=() if same_images else tuple(images),
        )
        fixed = [stored_claim for stored_claim in claims if stored_claim not in hit]
        revision = summarize.revise(self.deps, page_input, fixed, hit, regions)
        if isinstance(revision, summarize.Failed):
            self.items.append({"link": link, "result": "summary failed, old summary kept"})
            self.decisions.append(add.summary_failed(COMMAND, MODE, {"link": link}, link, revision.reason))
            return
        self._store_revision(source, read, images, claims, record.dropped_claims or 0, revision)

    def _keep_as_is(
        self,
        source: StoredSource,
        read: ports.Page,
        full: str,
        images: Sequence[bytes],
        claims: Sequence[StoredClaim],
        index: summarize.PageIndex,
    ) -> None:
        with self.store.transaction():
            self._applied()
            identity.refresh(self.store, source, read, text=full, images=images)
            self.store.update_summary(source.id, text_origin="read")
            for stored_claim in claims:
                spans = [QuoteRecord(quote.text, *index.find(quote.text)) for quote in stored_claim.claim.quotes]  # type: ignore[misc]
                self.store.move_claim(stored_claim.id, stored_claim.ord, spans)
        self.items.append({"link": source.key_link, "result": "re-read, no meaningful change"})

    def _store_revision(
        self,
        source: StoredSource,
        read: ports.Page,
        images: Sequence[bytes],
        claims: Sequence[StoredClaim],
        dropped_before: int,
        revision: summarize.Revision,
    ) -> None:
        at = spend.stamp(spend.local_now())
        order = {stored_claim.id: stored_claim.ord for stored_claim in claims}
        with self.store.transaction():
            self._applied()
            identity.refresh(self.store, source, read, text=revision.text, images=images)
            for claim_id, quotes in revision.kept:
                self.store.move_claim(claim_id, order[claim_id], quotes)
            for claim_id in revision.removed:
                self.store.replace_claim(claim_id, at)
            last = max(order.values(), default=0)
            for ord, claim in enumerate(revision.added, last + 1):
                self.store.add_claim(source.id, ord, claim, at)
            self.store.update_summary(
                source.id,
                text_origin="read",
                rubric_version=summarize.RUBRIC_VERSION,
                model=revision.model,
                thinking=revision.thinking,
                escalated=revision.escalated,
                rethink_line=revision.rethink_line,
                dropped_claims=dropped_before + revision.dropped,
                support_status=revision.support_status,
            )
            self.store.add_history(HistoryRecord(source.id, at, "reread", summarize.RUBRIC_VERSION, revision.model, revision.escalated))
            self.store.index_source(source.id)
        self.items.append({"link": source.key_link, "result": f"updated ({revision.changed} claims changed)"})


def run(body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``add --reread`` on the opened store."""
    return Reread(body, profile, store, host).run()
