"""``note``, ``archive`` and ``restore`` (spec 4.8; ticket 09 items 3, 4 and 14).

``note`` takes ``{"who", "subject", "lean", "reason"}``, each non-empty text after
trimming, ``lean`` being ``towards`` or ``against``. One unarchived note is held
per who-and-subject pair (trimmed, compared case-insensitively): a new pair gets
a row, a held pair has that row's lean, reason and time updated in place. The
change is kind ``note`` with the note's ``who`` as its one name target; it makes
no model call.

``archive`` and ``restore`` take exactly one of ``link`` (cleaned, then resolved
through ``links`` to its source), ``note`` (``{"who", "subject"}``), ``topic`` (its
name, trimmed and compared case-insensitively) or ``citation`` (``{"repo", "file"}``,
each trimmed and matched exactly; it applies to every citation of that file). The
change is kind ``archive`` or ``restore`` and names the cleaned link, the note's
``who``, the topic's name or the citation's repo and file. It sets or clears
``archived_at`` and deletes nothing; an archived topic keeps its versions, plans
and marks. ``archive`` of a citation stamps every unarchived row of the file;
``restore`` clears the rows that share the file's newest ``archived_at``, so rows
a replacing ``add`` archived stay archived. A target that is already in the asked
state changes nothing and asks nothing. Restoring a note while another unarchived
note holds its pair is a problem and changes nothing.

An archived note is never given to the answering model and never shown
(``answer``); an archived source is left out of ``find`` and ``ask``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from functools import partial
from typing import Any

from atlas.core import approvals, identity, reply, spend
from atlas.core.config import Profile
from atlas.store import NoteRecord, Store

LEANS = ("towards", "against")
TARGETS = ("link", "note", "topic", "citation")
_NOTE_FIELDS = {"profile", "approval", "who", "subject", "lean", "reason"}
_ARCHIVE_FIELDS = {"profile", "approval", *TARGETS}


def pair_key(who: str, subject: str) -> tuple[str, str]:
    """A who-and-subject pair as notes and tally lines compare it: trimmed and case-folded."""
    return who.strip().casefold(), subject.strip().casefold()


def shown(note: NoteRecord) -> dict[str, str]:
    """A note as replies show it."""
    return {"who": note.who, "subject": note.subject, "lean": note.lean, "reason": note.reason, "date": identity.date(note.at)}


def held(store: Store, who: str, subject: str) -> NoteRecord | None:
    """The unarchived note that holds the pair, else ``None``."""
    key = pair_key(who, subject)
    return next((note for note in store.notes() if note.archived_at is None and pair_key(note.who, note.subject) == key), None)


def _bad(command: str, problem: dict[str, Any]) -> tuple[dict[str, Any], int]:
    return reply.build(command, reply.BAD_INPUT, problems=[problem]), reply.BAD_INPUT


def _unknown_field(body: Mapping[str, Any], allowed: set[str]) -> dict[str, Any] | None:
    extra = sorted(set(body) - allowed)
    if not extra:
        return None
    return reply.problem(extra[0], f'"{extra[0]}" is not a field of this command; it takes {", ".join(sorted(allowed))}')


def _text(value: Any) -> str | None:
    """``value`` trimmed, or ``None`` when it is not non-empty text."""
    if not isinstance(value, str):
        return None
    return value.strip() or None


def _stop(command: str, verdict: approvals.Stop) -> tuple[dict[str, Any], int]:
    return reply.build(command, reply.NEEDS_DECISION, decisions=[verdict.decision]), reply.NEEDS_DECISION


# note -------------------------------------------------------------------------
def run_note(body: Mapping[str, Any], profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    """Answer ``note`` on the opened store."""
    command = "note"
    problem = _unknown_field(body, _NOTE_FIELDS)
    if problem is not None:
        return _bad(command, problem)
    fields: dict[str, str] = {}
    for name in ("who", "subject", "lean", "reason"):
        value = _text(body.get(name))
        if value is None:
            return _bad(command, reply.problem(name, f"{name} must be non-empty text"))
        fields[name] = value
    who, subject, lean, reason = fields["who"], fields["subject"], fields["lean"], fields["reason"]
    if lean not in LEANS:
        return _bad(command, reply.problem("lean", f"lean must be {' or '.join(LEANS)}"))

    earlier = held(store, who, subject)
    if earlier is None:
        question = f"Save a note: lean {lean} {who} on {subject}? Reason: {reason}"
    else:
        question = f"Change the note on {who} for {subject} (now lean {earlier.lean}) to lean {lean}? Reason: {reason}"
    change = approvals.Change(command=command, mode=None, body=body, kind="note", question=question, names=[who])
    verdict = approvals.check(change, profile, None)
    if isinstance(verdict, approvals.Refused):
        return _bad(command, verdict.problem)
    if isinstance(verdict, approvals.Stop):
        return _stop(command, verdict)

    now = spend.local_now()
    with store.transaction():
        if earlier is None:
            note_id = store.add_note(who, subject, lean, reason, spend.stamp(now))
        else:
            note_id = earlier.id
            store.change_note(note_id, lean, reason, spend.stamp(now))
        approvals.record(store, change, verdict, now)
    saved = next(note for note in store.notes() if note.id == note_id)
    outcome = "saved new" if earlier is None else f"changed (earlier lean: {earlier.lean})"
    steps = [reply.next_step("ask a question; the note shows beside the labels of answers it applies to", {"stop": True})]
    return reply.build(command, reply.DONE, result={"note": shown(saved), "result": outcome}, next=steps), reply.DONE


# archive and restore ----------------------------------------------------------
def run_archive(command: str, body: Mapping[str, Any], profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    """Answer ``archive`` or ``restore`` on the opened store."""
    problem = _unknown_field(body, _ARCHIVE_FIELDS)
    if problem is not None:
        return _bad(command, problem)
    named = [target for target in TARGETS if target in body]
    if len(named) != 1:
        return _bad(command, reply.problem("body", f"{command} takes exactly one of {', '.join(TARGETS)}"))
    [target] = named
    value = body[target]
    if target == "link":
        return _link(command, body, value, profile, store)
    if target == "note":
        return _note(command, body, value, profile, store)
    if target == "topic":
        return _topic(command, body, value, profile, store)
    return _citation(command, body, value, profile, store)


def _already(restoring: bool, archived_at: str | None) -> str | None:
    """What an archive or restore reports when the target is already in the asked state, else ``None``."""
    if restoring and archived_at is None:
        return "not archived"
    if not restoring and archived_at is not None:
        return f"already archived {identity.date(archived_at)}"
    return None


def _done(command: str, result: dict[str, Any]) -> tuple[dict[str, Any], int]:
    label = "bring it back with `restore`" if result["result"] == "archived" else "ask about your sources with `find` or `ask`"
    return reply.build(command, reply.DONE, result=result, next=[reply.next_step(label, {"stop": True})]), reply.DONE


def _change(
    command: str,
    body: Mapping[str, Any],
    profile: Profile,
    store: Store,
    question: str,
    write: Callable[[str | None], None],
    result: dict[str, Any],
    *,
    links: Sequence[str] = (),
    names: Sequence[str] = (),
) -> tuple[dict[str, Any], int]:
    """Decide an archive or restore; when it may run, ``write`` sets ``archived_at`` (a time, or ``None`` to clear it)
    in one transaction with the change's one ``approvals`` row, and the reply is done with ``result``."""
    restoring = command == "restore"
    change = approvals.Change(command=command, mode=None, body=body, kind=command, question=question, links=links, names=names)
    verdict = approvals.check(change, profile, None)
    if isinstance(verdict, approvals.Refused):
        return _bad(command, verdict.problem)
    if isinstance(verdict, approvals.Stop):
        return _stop(command, verdict)
    now = spend.local_now()
    with store.transaction():
        write(None if restoring else spend.stamp(now))
        approvals.record(store, change, verdict, now)
    return _done(command, {**result, "result": "restored" if restoring else "archived"})


def _link(command: str, body: Mapping[str, Any], value: Any, profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    restoring = command == "restore"
    if _text(value) is None:
        return _bad(command, reply.problem("link", "link must be a link"))
    cleaned = identity.clean(value)
    if cleaned is None:
        return _bad(command, reply.problem("link", "not a link Atlas can read: give a full http or https link", value))
    found = store.source_for_link(cleaned)
    if found is None:
        problems = [reply.problem("link", "not stored; add it first", cleaned)]
        return reply.build(command, reply.DONE, result={"link": cleaned, "result": "not stored"}, problems=problems), reply.DONE
    source = found.source
    unchanged = _already(restoring, source.archived_at)
    if unchanged is not None:
        return _done(command, {"link": source.key_link, "result": unchanged})
    if restoring:
        question = f"Restore {source.key_link}? Find and ask include it again."
    else:
        question = f"Archive {source.key_link}? Find and ask leave it out until it is restored; nothing is deleted."
    write = partial(store.set_source_archived, source.id)
    return _change(command, body, profile, store, question, write, {"link": source.key_link}, links=[cleaned])


def _note(command: str, body: Mapping[str, Any], value: Any, profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    restoring = command == "restore"
    if not isinstance(value, Mapping) or set(value) != {"who", "subject"}:
        return _bad(command, reply.problem("note", "note must be an object with exactly who and subject"))
    who, subject = _text(value["who"]), _text(value["subject"])
    if who is None or subject is None:
        return _bad(command, reply.problem("note", "the note's who and subject must be non-empty text"))
    key = pair_key(who, subject)
    rows = [note for note in store.notes() if pair_key(note.who, note.subject) == key]
    if not rows:
        problems = [reply.problem("note", "not stored; save it with `note` first")]
        result = {"note": {"who": who, "subject": subject}, "result": "not stored"}
        return reply.build(command, reply.DONE, result=result, problems=problems), reply.DONE
    live = [note for note in rows if note.archived_at is None]
    archived = [note for note in rows if note.archived_at is not None]
    # Archive takes the note held, else reports the newest archived one; restore brings back the newest archived one.
    if restoring:
        target = archived[-1] if archived else live[0]
    else:
        target = live[0] if live else archived[-1]
    unchanged = _already(restoring, target.archived_at)
    if unchanged is not None:
        return _done(command, {"note": shown(target), "result": unchanged})
    if restoring and live:
        text = f"an unarchived note already holds {live[0].who} on {live[0].subject}; archive it first, or change it with `note`"
        result = {"note": shown(target), "result": "not restored"}
        return reply.build(command, reply.DONE, result=result, problems=[reply.problem("note", text)]), reply.DONE
    if restoring:
        question = f"Restore the note on {target.who} for {target.subject} (lean {target.lean})? Answers use it again."
    else:
        question = f"Archive the note on {target.who} for {target.subject} (lean {target.lean})? Answers stop using it; nothing is deleted."
    write = partial(store.set_note_archived, target.id)
    return _change(command, body, profile, store, question, write, {"note": shown(target)}, names=[who])


def _topic(command: str, body: Mapping[str, Any], value: Any, profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    restoring = command == "restore"
    name = _text(value)
    if name is None:
        return _bad(command, reply.problem("topic", "topic must be a topic name"))
    topic = store.topic(name)
    if topic is None:
        problems = [reply.problem("topic", "not stored; create it first")]
        return reply.build(command, reply.DONE, result={"topic": name, "result": "not stored"}, problems=problems), reply.DONE
    unchanged = _already(restoring, topic.archived_at)
    if unchanged is not None:
        return _done(command, {"topic": topic.name, "result": unchanged})
    if restoring:
        question = f'Restore the topic "{topic.name}"? The catch-up and topic matching include it again.'
    else:
        question = f'Archive the topic "{topic.name}"? The catch-up and topic matching leave it out until it is restored; its versions, plans and marks stay and nothing is deleted.'
    write = partial(store.set_topic_archived, topic.id)
    return _change(command, body, profile, store, question, write, {"topic": topic.name}, names=[topic.name])


def _citation(command: str, body: Mapping[str, Any], value: Any, profile: Profile, store: Store) -> tuple[dict[str, Any], int]:
    restoring = command == "restore"
    if not isinstance(value, Mapping) or set(value) != {"repo", "file"}:
        return _bad(command, reply.problem("citation", "citation must be an object with exactly repo and file"))
    repo, file = _text(value["repo"]), _text(value["file"])
    if repo is None or file is None:
        return _bad(command, reply.problem("citation", "the citation's repo and file must be non-empty text"))
    shown_file = {"repo": repo, "file": file}
    rows = store.file_citations(repo, file)
    if not rows:
        problems = [reply.problem("citation", "not stored; cite it with `add` first")]
        return reply.build(command, reply.DONE, result={"citation": shown_file, "result": "not stored"}, problems=problems), reply.DONE
    # The file is archived when no row is unarchived, as of its newest archive time.
    archived = [row.archived_at for row in rows if row.archived_at is not None]
    unchanged = _already(restoring, None if len(archived) < len(rows) else max(archived))
    if unchanged is not None:
        return _done(command, {"citation": shown_file, "result": unchanged})

    def write(at: str | None) -> None:
        if at is None:
            store.restore_citations(repo, file)
        else:
            store.archive_citations(repo, file, at)

    if restoring:
        question = f"Restore the citations of {file} in {repo} that were last archived? Replies name them again."
    else:
        question = f"Archive the citations of {file} in {repo}? Replies stop naming them until they are restored; nothing is deleted."
    return _change(command, body, profile, store, question, write, {"citation": shown_file}, names=[repo, file])
