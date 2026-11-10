"""``add``: store one checked summary per source the user names.

Body: ``{"items": [{"link", "text"?, "scope"?}]}``. Every link is matched against
the stored links before any read (``identity.Batch``); only links no stored
source holds are read. An item with ``text`` is not read: that text is the page,
stored with text origin ``agent``. The links left to read are one change of
kind ``add`` under the approval rules; reading 2 or more of them, or choosing
"each item" or "each link", is paid at scale, so its confirm states the batch
estimate and the window use. The cap and window guard run before the first
paid call and before each later item.

Each page read is then, in order:

- given a ``pick_scope`` decision when its scope is unclear: a repo with 2 or
  more items (this page, each item, both), a video (transcript or skip), an
  image or mostly-images page (read images or skip), a link list (this page,
  each link), or a page over ``max_page_tokens`` (first part, or sections by
  top-level heading). The item is resent with the chosen ``scope``, which the
  source keeps as ``scope_choice``. A ``transcript`` item is read with read
  scope ``transcript``, so a video without one is ``unreadable: no_transcript``;
- matched by identity (same text, near copy, a key link already stored);
- summarized (``summarize.summarize``), checked for copies of stored sources,
  and stored with its claims in one transaction; a summary that fails after its
  escalation stores nothing and returns a ``summary_failed`` decision.

``next`` offers storing a joined near copy separately, and one combined re-read
of stored sources the reply relies on that were last read over ``reread_days``
ago (unchangeable sources left out).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit

from atlas import ports
from atlas.core import approvals, identity, reply, sites, spend, summarize
from atlas.core.config import SETUP_SKILL, Profile
from atlas.core.status import ROLES as SUGGESTED  # the model each role is suggested to use
from atlas.store import HistoryRecord, Store

COMMAND = "add"
FIELDS = {"profile", "approval", "items"}
ITEM_FIELDS = {"link", "text", "scope"}
ROLES = (summarize.SUMMARIZE, summarize.ESCALATE)

# Scopes an item may carry. "page" keeps a repo or link list to its own page.
PAGE = "page"
EACH_ITEM = "each_item"
BOTH = "both"
EACH_LINK = "each_link"
TRANSCRIPT = "transcript"
IMAGES = "images"
SKIP = "skip"
FIRST_PART = "first_part"
# Tuples, not sets: a ``{"sections": [...]}`` scope is a dict and must compare, not hash.
SCOPES = (identity.SEPARATE, PAGE, EACH_ITEM, BOTH, EACH_LINK, TRANSCRIPT, IMAGES, SKIP, FIRST_PART)
EXPANDING = (EACH_ITEM, BOTH, EACH_LINK)

# A page is mostly images when it has fewer words than this per image.
WORDS_PER_IMAGE = 50
# Of the context a summary call may fill with page text, after the output room.
CONTEXT_SHARE = 0.8
# Section options a pick-scope decision lists at most.
SECTION_OPTIONS = 10
_HEADING = re.compile(r"^(#{1,6}) +(.+?)\s*#*$")


def _bad(problem: dict[str, Any]) -> tuple[dict[str, Any], int]:
    return reply.build(COMMAND, reply.BAD_INPUT, problems=[problem]), reply.BAD_INPUT


def _scope_ok(scope: Any) -> bool:
    if scope is None or scope in SCOPES:
        return True
    return (
        isinstance(scope, Mapping)
        and set(scope) == {"sections"}
        and isinstance(scope["sections"], list)
        and bool(scope["sections"])
        and all(isinstance(name, str) and name for name in scope["sections"])
    )


def items_problem(body: Mapping[str, Any], allowed: set[str], item_fields: set[str]) -> dict[str, Any] | None:
    """Why ``body`` is not a valid ``add`` body, or ``None``."""
    extra = sorted(set(body) - allowed)
    if extra:
        return reply.problem(extra[0], f'"{extra[0]}" is not a field of this command; it takes {", ".join(sorted(allowed))}')
    items = body.get("items")
    if not isinstance(items, list) or not items:
        return reply.problem("items", "items must be a non-empty list of {link} objects")
    for item in items:
        if not isinstance(item, Mapping) or not isinstance(item.get("link"), str) or set(item) - item_fields:
            return reply.problem("items", f'each item is an object with a link and only {", ".join(sorted(item_fields))}')
        if "text" in item and not (isinstance(item["text"], str) and item["text"].strip()):
            return reply.problem("items", "an item's text must be the page text")
        if not _scope_ok(item.get("scope")):
            choices = ", ".join(sorted(SCOPES))
            return reply.problem("items", f'an item\'s scope is one of {choices}, or {{"sections": [headings]}}')
    return None


def role_items(host: ports.Host, roles: Sequence[str]) -> list[dict[str, Any]]:
    """One ``needs_action`` item per role the host lacks, with its fix; none when the host cannot say."""
    if host.facts is None:
        return []
    try:
        present = host.facts.roles()
    except ports.CallFailed:
        return []

    items = []
    for role in roles:
        if role not in present:
            fix = host.facts.role_fix({role: SUGGESTED[role]})
            lines = list(fix.lines) or [f"Add the model role {role} with the model {SUGGESTED[role]}."]
            items.append({"what": f"Role {role} is missing", "fix": lines, "where": fix.where})
    return items


def not_set_up(command: str, items: list[dict[str, Any]], result: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
    steps = [reply.next_step(f"run `{SETUP_SKILL}`", {"skill": SETUP_SKILL})]
    body = {**result, "needs_action": items}
    return reply.build(command, reply.NOT_SET_UP, result=body, next=steps), reply.NOT_SET_UP


def page_limit(host: ports.Host, profile: Profile) -> int:
    """``max_page_tokens``, capped to 80% of the summary role's context minus the output room when the host says."""
    limit = profile.max_page_tokens
    if host.facts is not None:
        try:
            context = host.facts.role_context(summarize.SUMMARIZE)
        except ports.CallFailed:
            context = None
        if context:
            limit = min(limit, int(context * CONTEXT_SHARE) - summarize.MAX_OUTPUT)
    return limit


def kind_of(page: ports.Page, link: str) -> str:
    """The page's kind: the reader's hint, else the site table's (X post, GitHub repo, YouTube video)."""
    if page.kind_hint != "unknown":
        return page.kind_hint
    site = sites.site_for(urlsplit(link).hostname or "")
    if site is None:
        return "unknown"
    if site.name == "x":
        return "x_post" if "/status/" in link else "unknown"
    return {"github": "repo", "youtube": "video"}.get(site.name, "unknown")


def platform_of(link: str) -> str | None:
    site = sites.site_for(urlsplit(link).hostname or "")
    return None if site is None else site.name


def mostly_images(page: ports.Page) -> bool:
    images = len(page.images)
    return images > 0 and page.counts.words < WORDS_PER_IMAGE * images


def sections(text: str) -> list[tuple[str, str]]:
    """The page's top-level sections as (heading, text), by its shallowest heading level."""
    lines = text.split("\n")
    levels = [len(match.group(1)) for line in lines if (match := _HEADING.match(line))]
    if not levels:
        return []
    top = min(levels)
    found: list[tuple[str, list[str]]] = []
    for line in lines:
        match = _HEADING.match(line)
        if match and len(match.group(1)) == top:
            found.append((match.group(2).strip(), [line]))
        elif found:
            found[-1][1].append(line)
    return [(name, "\n".join(body)) for name, body in found]


def first_part(text: str, limit: int) -> str:
    """The page's opening lines up to ``limit`` tokens."""
    room = max(limit, 1) * 4
    if len(text) <= room:
        return text
    cut = text.rfind("\n", 0, room)
    return text[: cut if cut > 0 else room]


def read_scope(scope: Any) -> ports.Scope:
    """The read port scope for a chosen ``scope``: only a transcript is read differently."""
    return TRANSCRIPT if scope == TRANSCRIPT else None


_SECTIONS_CHOICE = "sections: "


def scope_choice(scope: Any) -> str | None:
    """The ``scope_choice`` a source keeps for a chosen ``scope``."""
    if isinstance(scope, Mapping):
        return _SECTIONS_CHOICE + "; ".join(scope["sections"])
    return scope


def stored_scope(choice: str | None) -> Any:
    """The scope a kept ``scope_choice`` stands for, to read the page the same way again."""
    if choice is not None and choice.startswith(_SECTIONS_CHOICE):
        return {"sections": choice.removeprefix(_SECTIONS_CHOICE).split("; ")}
    return choice


def scoped_text(page: ports.Page, scope: Any, limit: int) -> tuple[str, float | None] | str:
    """The text to summarize and the share of the page it is, or a problem text."""
    text = identity.normalize(page.text)
    if isinstance(scope, Mapping):
        wanted = {name.casefold() for name in scope["sections"]}
        chosen = [body for name, body in sections(text) if name.casefold() in wanted]
        if not chosen:
            return f'no top-level section is named {", ".join(scope["sections"])}'
        kept = "\n".join(chosen)
    else:
        kept = text
    if summarize.page_tokens(kept) > limit:
        kept = first_part(kept, limit)
    share = None if kept == text else round(len(kept) / len(text), 4)
    return kept, share


@dataclass
class Work:
    """One item to handle: the batch it belongs to, its body item and the repo link it came from."""

    batch: identity.Batch
    item: identity.Item
    given: Mapping[str, Any]
    related: tuple[str, ...] = ()


@dataclass
class Run:
    """What one ``add`` builds up: per-item results, problems, decisions, Next and sources relied on."""

    items: list[dict[str, Any]] = field(default_factory=list)
    problems: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    relied_on: list[str] = field(default_factory=list)

    def result(self, extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
        added = [item for item in self.items if item["result"] == "added"]
        return {
            "added": len(added),
            "dropped_claims": sum(item.get("dropped_claims", 0) for item in added),
            "items": self.items,
            **(extra or {}),
        }


def _decision_body(given: Mapping[str, Any]) -> dict[str, Any]:
    return {"items": [dict(given)]}


def _resend(given: Mapping[str, Any], scope: Any) -> dict[str, Any]:
    return {"resend": {"items": [{**given, "scope": scope}]}}


def pick_scope(given: Mapping[str, Any], question: str, choices: Sequence[tuple[str, str, Any]]) -> dict[str, Any]:
    """A ``pick_scope`` decision for one item; ``choices`` are (option id, label, scope or ``None`` to skip)."""
    options = [
        reply.option(option, label, {"stop": True} if scope is None else _resend(given, scope))
        for option, label, scope in choices
    ]
    return reply.decision(COMMAND, None, _decision_body(given), "pick_scope", question, options)


def summary_failed(command: str, mode: str | None, given: Mapping[str, Any], link: str, reason: str) -> dict[str, Any]:
    options = [
        reply.option("retry", "retry the summary", {"resend": {"items": [dict(given)]}}),
        reply.option("skip", "skip this link", {"stop": True}),
    ]
    question = f"The summary of {link} failed, also after one escalation ({reason}). Nothing was stored. Retry or skip?"
    return reply.decision(command, mode, _decision_body(given), "summary_failed", question, options)


class Add:
    """One ``add`` command on an opened store."""

    def __init__(self, body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> None:
        self.body = body
        self.profile = profile
        self.store = store
        self.host = host
        self.run_state = Run()
        self.deps = summarize.Deps(host, profile, store, COMMAND)
        self.limit = page_limit(host, profile)

    # Scope decisions -----------------------------------------------------------
    def _scope_question(self, work: Work, page: ports.Page, kind: str) -> dict[str, Any] | None:
        """The pick-scope decision a page needs before it is summarized, else ``None``."""
        scope = work.item.scope
        link = work.item.link
        if scope in (None, identity.SEPARATE):
            if kind == "repo" and len(page.items) >= 2:
                listed = ", ".join(item.path for item in page.items)
                return pick_scope(
                    work.given,
                    f"{link} is a repo with {len(page.items)} items ({listed}). Summarize the repo, each item, or both?",
                    [(PAGE, "the repo page", PAGE), (EACH_ITEM, f"each of the {len(page.items)} items", EACH_ITEM), (BOTH, "both", BOTH)],
                )
            if kind == "video":
                return pick_scope(
                    work.given, f"{link} is a video. Summarize its transcript, or skip it?",
                    [(TRANSCRIPT, "summarize the transcript", TRANSCRIPT), (SKIP, "skip it", None)],
                )
            if kind == "image" or mostly_images(page):
                return pick_scope(
                    work.given, f"{link} is mostly images ({len(page.images)}). Read the images, or skip it?",
                    [(IMAGES, "read the images", IMAGES), (SKIP, "skip it", None)],
                )
            if kind == "link_list":
                return pick_scope(
                    work.given,
                    f"{link} is a list of {len(page.links)} links. Summarize this page, or each link?",
                    [(PAGE, "this page", PAGE), (EACH_LINK, f"each of the {len(page.links)} links", EACH_LINK)],
                )
        if summarize.page_tokens(page.text) > self.limit and scope != FIRST_PART and not isinstance(scope, Mapping):
            found = sections(page.text)
            names = [name for name, _ in found]
            listed = "; ".join(names) if names else "none"
            question = (
                f"{link} is about {summarize.page_tokens(page.text):,} tokens, over the {self.limit:,}-token limit. "
                f"Summarize its first part, or pick sections by heading (resend scope {{\"sections\": [...]}} with several "
                f"to read more than one). Top-level headings: {listed}."
            )
            choices: list[tuple[str, str, Any]] = [(FIRST_PART, "the first part", FIRST_PART)]
            choices += [(f"section_{n}", f"section: {name}", {"sections": [name]}) for n, name in enumerate(names[:SECTION_OPTIONS], 1)]
            return pick_scope(work.given, question, choices)
        return None

    # One item -----------------------------------------------------------------
    def _read(self, work: Work) -> tuple[ports.Page | ports.Unreadable, str]:
        text = work.given.get("text")
        if isinstance(text, str):
            link = work.item.link
            assert link is not None
            page = ports.Page(link, None, None, None, None, "unknown", text, counts=ports.Counts(len(text.split()), 0, 0))
            return page, "agent"
        return self.host.read.read(work.item.link, read_scope(work.item.scope)), "read"

    def _settled(self, outcome: identity.Outcome) -> None:
        state = self.run_state
        state.items.append({"link": outcome.item.link, "result": outcome.result})
        if outcome.kind in (identity.STORED, identity.JOINED, identity.NEAR_COPY) and outcome.source_link:
            state.relied_on.append(outcome.source_link)
        if outcome.next is not None:
            state.steps.append(dict(outcome.next))

    def handle(self, work: Work, queue: list[Work]) -> None:
        """Read, scope, match, summarize and store one item; expansions go onto ``queue``."""
        state = self.run_state
        item = work.item
        assert item.link is not None
        read, origin = self._read(work)
        if isinstance(read, ports.Unreadable):
            self._settled(work.batch.examine(item, read))
            return
        kind = kind_of(read, item.link)
        decision = self._scope_question(work, read, kind)
        if decision is not None:
            state.items.append({"link": item.link, "result": "pick scope"})
            state.decisions.append(decision)
            return
        scope = item.scope
        if scope == SKIP:
            state.items.append({"link": item.link, "result": "skipped"})
            return
        if scope in EXPANDING:
            children = [entry.link for entry in read.items] if scope in (EACH_ITEM, BOTH) else list(read.links)
            related = (item.link,) if scope in (EACH_ITEM, BOTH) else ()
            child_batch = identity.Batch(self.store, self.profile.near_copy, [(link, None) for link in children])
            for child in child_batch.items:
                outcome = child_batch.outcome(child)
                if outcome is not None:
                    self._settled_or_problem(outcome)
                else:
                    queue.append(Work(child_batch, child, {"link": child.given}, related))
            if scope != BOTH:
                state.items.append({"link": item.link, "result": f"read as its {len(children)} links"})
                return
        images: list[bytes] = []
        if scope == IMAGES:
            for n, link in enumerate(read.images, 1):
                got = self.host.read.image(link)
                if isinstance(got, ports.Unreadable):
                    state.items.append({"link": item.link, "result": f"unreadable: {got.reason} (image {n})"})
                    return
                images.append(got)
        outcome = work.batch.examine(item, read, images=images, origin=origin)
        if outcome.kind != identity.NEW:
            self._settled(outcome)
            return
        new = outcome.new
        assert new is not None
        scoped = scoped_text(read, scope, self.limit)
        if isinstance(scoped, str):
            state.problems.append(reply.problem("scope", scoped, item.link))
            state.items.append({"link": item.link, "result": "not added: " + scoped})
            return
        text, share = scoped
        source = summarize.PageInput(
            page=read,
            text=text,
            kind=TRANSCRIPT if kind == "video" else kind,
            link=new.key_link,
            images=tuple(images),
        )
        summary = summarize.summarize(self.deps, source)
        if isinstance(summary, summarize.Failed):
            state.items.append({"link": new.key_link, "result": "summary failed"})
            state.decisions.append(summary_failed(COMMAND, None, work.given, new.key_link, summary.reason))
            return
        flags, copies = summarize.copy_flags(self.deps, summary.title, summary.abstract, new.key_link)
        self._keep(work, new, summary, flags, copies, scope, share)

    def _settled_or_problem(self, outcome: identity.Outcome) -> None:
        if outcome.kind == identity.BAD_LINK:
            self.run_state.problems.append(reply.problem("items", outcome.result, outcome.item.given))
        else:
            self._settled(outcome)

    def _keep(
        self,
        work: Work,
        new: identity.NewSource,
        summary: summarize.Summary,
        flags: Sequence[tuple[Any, str]],
        copies: str,
        scope: Any,
        share: float | None,
    ) -> None:
        at = spend.stamp(spend.local_now())
        choice = scope_choice(scope)
        with self.store.transaction():
            source_id = work.batch.keep(
                new,
                text=summary.text,
                title=summary.title,
                author=summary.author,
                publisher=summary.publisher,
                platform=platform_of(new.key_link),
                published=summary.published,
                scope_choice=choice,
                read_share=share,
                abstract=summary.abstract,
                rubric_version=summarize.RUBRIC_VERSION,
                model=summary.model,
                thinking=summary.thinking,
                escalated=summary.escalated,
                rethink_line=summary.rethink_line,
                dropped_claims=summary.dropped,
                support_status=summary.support_status,
                copies_status=copies,
            )
            for ord, claim in enumerate(summary.claims, 1):
                self.store.add_claim(source_id, ord, claim, at)
            self.store.add_related_links(source_id, [*summary.related_links, *work.related])
            self.store.add_copy_flags(source_id, [flag for flag, _ in flags])
            self.store.add_history(HistoryRecord(source_id, at, "added", summarize.RUBRIC_VERSION, summary.model, summary.escalated))
            self.store.index_source(source_id)
        entry: dict[str, Any] = {
            "link": new.key_link,
            "result": "added",
            "title": summary.title,
            "claims": len(summary.claims),
            "dropped_claims": summary.dropped,
            "flagged_claims": sum(1 for claim in summary.claims if claim.flag is not None and claim.flag.flagged),
        }
        if summary.support_status != summarize.CHECKED:
            entry["support"] = "support not checked"
        if copies != summarize.CHECKED:
            entry["copies"] = "copies not checked"
        else:
            entry["copies"] = [f"may be a copy of {link}" for flag, link in flags if flag.flagged]
        self.run_state.items.append(entry)

    # The command --------------------------------------------------------------
    def _question(self, links: Sequence[str], at_scale: bool, guard: spend.Guard) -> str:
        if not at_scale:
            return f"Read and summarize {links[0]}?"
        selector = None
        if self.host.facts is not None:
            try:
                selector = self.host.facts.roles().get(summarize.SUMMARIZE)
            except ports.CallFailed:
                selector = None
        count = len(links)
        if selector is None:
            estimate = "cost unknown: the summary model is not known"
        else:
            each = spend.estimate_item(self.store, self.profile, selector)
            estimate = spend.estimate_text(None if each is None else each * count, selector)
            if each is not None:
                estimate += f" ({spend.estimate_text(each, selector)} per link)"
        named = ", ".join(links)
        return (
            f"Read and summarize {count} links ({named}), or each item or link they list? "
            f"Estimated cost: {estimate}. Window use: {guard.window_use()}."
        )

    def _reread_offer(self) -> dict[str, Any] | None:
        now = spend.local_now()
        due = []
        for link in dict.fromkeys(self.run_state.relied_on):
            found = self.store.source_for_link(link)
            if found is None or found.source.archived_at is not None:
                continue
            record = self.store.source_record(found.source.id)
            age = now - datetime.fromisoformat(record.last_read)
            if not record.unchangeable and age.total_seconds() > self.profile.reread_days * 86_400:
                due.append(record.key_link)
        if not due:
            return None
        label = f"Re-read {len(due)} source{'s' if len(due) != 1 else ''} last read over {self.profile.reread_days} days ago"
        return reply.next_step(label, {"resend": {"mode": "reread", "items": [{"link": link} for link in due]}})

    def run(self) -> tuple[dict[str, Any], int]:
        problem = items_problem(self.body, FIELDS, ITEM_FIELDS)
        if problem is not None:
            return _bad(problem)
        given = list(self.body["items"])
        batch = identity.Batch(self.store, self.profile.near_copy, [(item["link"], item.get("scope")) for item in given])
        state = self.run_state
        queue: list[Work] = []
        for item, entry in zip(batch.items, given):
            outcome = batch.outcome(item)
            if outcome is None:
                queue.append(Work(batch, item, entry))
            else:
                self._settled_or_problem(outcome)
        if queue:
            stopped = self._run_queue(queue)
            if stopped is not None:
                return stopped
        offer = self._reread_offer()
        steps = state.steps + ([offer] if offer else [])
        if not steps:
            steps = [reply.next_step("ask about these sources with `ask`, or add more links", {"stop": True})]
        steps = steps[: reply.MAX_NEXT]
        if state.decisions:
            answer = reply.build(COMMAND, reply.NEEDS_DECISION, result=state.result(), problems=state.problems, next=steps, decisions=state.decisions)
            return answer, reply.NEEDS_DECISION
        return reply.build(COMMAND, reply.DONE, result=state.result(), problems=state.problems, next=steps), reply.DONE

    def _run_queue(self, queue: list[Work]) -> tuple[dict[str, Any], int] | None:
        state = self.run_state
        missing = role_items(self.host, ROLES)
        if missing:
            return not_set_up(COMMAND, missing, state.result())
        links = [work.item.link for work in queue if work.item.link is not None]
        at_scale = len(queue) >= 2 or any(work.item.scope in EXPANDING for work in queue)
        guard = spend.Guard(self.store, self.profile, self.host, ROLES, paid=True, batch=at_scale)
        change = approvals.Change(
            command=COMMAND,
            mode=None,
            body=self.body,
            kind="add",
            question=self._question(links, at_scale, guard),
            links=links,
            paid_at_scale=at_scale,
        )
        verdict = approvals.check(change, self.profile, guard)
        if isinstance(verdict, approvals.Refused):
            return _bad(verdict.problem)
        if isinstance(verdict, approvals.Stop):
            answer = reply.build(COMMAND, reply.NEEDS_DECISION, result=state.result(), problems=state.problems, decisions=[verdict.decision])
            return answer, reply.NEEDS_DECISION
        approvals.record(self.store, change, verdict)
        done = 0
        while queue:
            work = queue.pop(0)
            if done:
                guard.batch = True  # a second item makes this a batch, also after an expansion
                limit = guard.check(done, len(queue) + 1)
                if limit is not None:
                    decisions = [*state.decisions, approvals.limit_decision(change, limit)]
                    answer = reply.build(COMMAND, reply.NEEDS_DECISION, result=state.result(), problems=state.problems, decisions=decisions)
                    return answer, reply.NEEDS_DECISION
            try:
                self.handle(work, queue)
            except ports.RoleMissing as err:
                return not_set_up(COMMAND, role_items(self.host, (err.role,)) or [_role_item(err.role)], state.result())
            done += 1
        return None


def _role_item(role: str) -> dict[str, Any]:
    return {"what": f"Role {role} is missing", "fix": [f"Add the model role {role}."], "where": None}


def run(body: Mapping[str, Any], profile: Profile, store: Store, host: ports.Host) -> tuple[dict[str, Any], int]:
    """Answer ``add`` on the opened store."""
    return Add(body, profile, store, host).run()
