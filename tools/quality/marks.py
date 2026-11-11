"""``marks-report``: each mark of one profile's store with its P, topic, source and whether the topic's last catch-up
answer named the source (spec 4.15, 4.12; ticket 17 section 3). The user reads the rows to keep or change the 0.3 mark
threshold.

The store file is opened read-only through an SQLite read-only URI, never through the migrating core open, and nothing is
written: a store that is not migrated to stage 7 yet has no ``marks`` table and is reported as such, not migrated.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tools.quality import _path  # noqa: F401
from tools.quality.evaldb import readonly

NAMED = "named in the catch-up answer"
NOT_NAMED = "not named in the catch-up answer"
UNANSWERED = "not yet answered"
HEADER = "P | topic | source | catch-up answer"


class MarksError(Exception):
    """The store cannot be reported; the message says why."""


def _answer(mark_at: str, source_id: int, last_catchup: str | None) -> str:
    """Whether the topic's last catch-up answer named the source; a mark made after that answer, or with no answer yet, is not yet answered."""
    try:
        verdict = None if last_catchup is None else json.loads(last_catchup)
    except ValueError:
        verdict = None
    if not isinstance(verdict, dict) or not isinstance(verdict.get("at"), str) or not isinstance(verdict.get("named"), list):
        return UNANSWERED
    if mark_at > verdict["at"]:
        return UNANSWERED
    return NAMED if source_id in verdict["named"] else NOT_NAMED


def rows(path: Path) -> list[str]:
    """One text row per mark, by topic and then time: P, topic name, the source's key link and the catch-up answer's state."""
    try:
        with readonly(path) as conn:
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'marks'").fetchone() is None:
                [(version,)] = conn.execute("PRAGMA user_version").fetchall()
                raise MarksError(f"the store {path} has no marks table (user_version {version}); it is not migrated to stage 7 yet, and marks-report never migrates it")
            found = conn.execute(
                "SELECT m.p, t.name, s.key_link, m.at, m.source_id, t.last_catchup FROM marks m"
                " JOIN topics t ON t.id = m.topic_id JOIN sources s ON s.id = m.source_id ORDER BY t.id, m.at, m.id"
            ).fetchall()
    except sqlite3.Error as err:
        raise MarksError(f"the store {path} cannot be read: {err}") from None
    return [f"{p:.2f} | {topic} | {link} | {_answer(at, source_id, last_catchup)}" for p, topic, link, at, source_id, last_catchup in found]
