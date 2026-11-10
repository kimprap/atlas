"""The quality tool's own tables in the ``eval`` store (spec 4.15, ticket 13 section 1 item 3).

The tool creates them when missing; they are not a numbered migration, because
migrations ship in the plugin and apply to every profile's store, and the tool is
repo-only. They live in the same SQLite file as the store's tables, which the
tool opens through the SQLite adapter first, so the file is a valid store.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any

LANES = ("summary", "search", "answers")

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    lane TEXT NOT NULL CHECK (lane IN ('summary', 'search', 'answers')),
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    link TEXT,
    origin TEXT NOT NULL CHECK (origin IN ('ticket08', 'promoted', 'planted'))
);
CREATE TABLE IF NOT EXISTS key_points (
    case_id TEXT NOT NULL REFERENCES cases (id),
    ord INTEGER NOT NULL,
    text TEXT NOT NULL,
    quote TEXT NOT NULL,
    reviewed_at TEXT,
    PRIMARY KEY (case_id, ord)
);
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    lane TEXT NOT NULL,
    label TEXT NOT NULL,
    ref TEXT NOT NULL,
    overrides TEXT NOT NULL,
    rep INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    cost_usd REAL
);
CREATE TABLE IF NOT EXISTS measures (
    run_id INTEGER NOT NULL REFERENCES runs (id),
    case_id TEXT NOT NULL,
    measure TEXT NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY (run_id, case_id, measure)
);
CREATE TABLE IF NOT EXISTS judgments (
    run_id INTEGER NOT NULL REFERENCES runs (id),
    item TEXT NOT NULL,
    question TEXT NOT NULL,
    p REAL,
    judge_model TEXT NOT NULL,
    PRIMARY KEY (run_id, item)
);
CREATE TABLE IF NOT EXISTS comparisons (
    id TEXT PRIMARY KEY,
    lane TEXT NOT NULL,
    base_runs TEXT NOT NULL,
    cand_runs TEXT NOT NULL,
    report TEXT,
    spot_status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS spot (
    comparison_id TEXT NOT NULL REFERENCES comparisons (id),
    item TEXT NOT NULL,
    shown TEXT NOT NULL,
    user_label TEXT,
    at TEXT,
    PRIMARY KEY (comparison_id, item)
);
"""


def readonly(path: Path) -> Any:
    """A read-only connection to a store file, closed when the block ends; the path is escaped, so a folder named with ``#``, ``?`` or ``%`` still opens."""
    return closing(sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True))


def connect(path: Path) -> sqlite3.Connection:
    """The tool's connection to the ``eval`` store file, its tables created when missing."""
    db = sqlite3.connect(path, isolation_level=None)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SCHEMA)
    return db


@contextmanager
def transaction(db: sqlite3.Connection) -> Iterator[None]:
    """All the block's writes or none; inside an open transaction (an estimate's) it is a savepoint."""
    nested = db.in_transaction
    db.execute("SAVEPOINT block" if nested else "BEGIN")
    try:
        yield
    except BaseException:
        db.execute("ROLLBACK TO block" if nested else "ROLLBACK")
        if nested:
            db.execute("RELEASE block")
        raise
    db.execute("RELEASE block" if nested else "COMMIT")


@contextmanager
def session(path: Path, dry: bool) -> Iterator[sqlite3.Connection]:
    """The tool's connection to the ``eval`` store file. A dry session (an estimate) runs in one transaction that is rolled back,
    so planning code can write rows and nothing is kept."""
    if not dry:
        db = connect(path)
        try:
            yield db
        finally:
            db.close()
        return
    db = sqlite3.connect(path, isolation_level=None)
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("BEGIN")
    try:
        for statement in SCHEMA.split(";\n"):
            if statement.strip():
                db.execute(statement)
        yield db
    finally:
        db.execute("ROLLBACK")
        db.close()


def add_case(db: sqlite3.Connection, id: str, lane: str, kind: str, payload: Mapping[str, Any], link: str | None, origin: str) -> bool:
    """Keep one case; a case that already exists is left as it is. Returns whether it was new."""
    cursor = db.execute(
        "INSERT OR IGNORE INTO cases (id, lane, kind, payload, link, origin) VALUES (?, ?, ?, ?, ?, ?)",
        (id, lane, kind, json.dumps(payload, sort_keys=True, ensure_ascii=False), link, origin),
    )
    return cursor.rowcount == 1


def cases(db: sqlite3.Connection, lane: str, kind: str | None = None) -> list[dict[str, Any]]:
    """The cases of ``lane`` (of one ``kind`` when given) with their payloads decoded, by id."""
    sql = "SELECT id, lane, kind, payload, link, origin FROM cases WHERE lane = ?"
    args: list[Any] = [lane]
    if kind is not None:
        sql += " AND kind = ?"
        args.append(kind)
    rows = db.execute(sql + " ORDER BY id", args).fetchall()
    return [
        {"id": id, "lane": lane, "kind": kind, "payload": json.loads(payload), "link": link, "origin": origin}
        for id, lane, kind, payload, link, origin in rows
    ]


def add_run(db: sqlite3.Connection, lane: str, label: str, ref: str, overrides: Mapping[str, str], rep: int, at: str) -> int:
    cursor = db.execute(
        "INSERT INTO runs (lane, label, ref, overrides, rep, started_at) VALUES (?, ?, ?, ?, ?, ?)",
        (lane, label, ref, json.dumps(dict(overrides), sort_keys=True), rep, at),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def finish_run(db: sqlite3.Connection, run_id: int, at: str, cost_usd: float) -> None:
    db.execute("UPDATE runs SET finished_at = ?, cost_usd = ? WHERE id = ?", (at, cost_usd, run_id))


def set_measure(db: sqlite3.Connection, run_id: int, case_id: str, measure: str, value: float) -> None:
    db.execute(
        "INSERT INTO measures (run_id, case_id, measure, value) VALUES (?, ?, ?, ?)"
        " ON CONFLICT (run_id, case_id, measure) DO UPDATE SET value = excluded.value",
        (run_id, case_id, measure, float(value)),
    )


def add_judgment(db: sqlite3.Connection, run_id: int, item: str, question: str, p: float | None, model: str) -> None:
    db.execute(
        "INSERT OR REPLACE INTO judgments (run_id, item, question, p, judge_model) VALUES (?, ?, ?, ?, ?)",
        (run_id, item, question, p, model),
    )


def measures(db: sqlite3.Connection, run_ids: Sequence[int]) -> dict[tuple[int, str, str], float]:
    """``(run, case, measure) -> value`` for the runs."""
    marks = ",".join("?" * len(run_ids))
    rows = db.execute(f"SELECT run_id, case_id, measure, value FROM measures WHERE run_id IN ({marks})", list(run_ids))
    return {(run, case, measure): value for run, case, measure, value in rows}


def judgments(db: sqlite3.Connection, run_ids: Sequence[int]) -> list[tuple[int, str, str, float | None, str]]:
    marks = ",".join("?" * len(run_ids))
    sql = f"SELECT run_id, item, question, p, judge_model FROM judgments WHERE run_id IN ({marks}) ORDER BY run_id, item"
    return db.execute(sql, list(run_ids)).fetchall()
