"""The SQLite store: one file per profile, WAL mode, foreign keys on.

Until the baseline migration exists the schema is ``schema_dev.sql``: a store
whose recorded schema differs from that file's text is rebuilt from it. The
recorded schema is the CRC-32 of the text, kept in the file header's
``application_id``, so the store needs no table of its own. ``user_version``
counts migrations; a store whose ``user_version`` is newer than ``SCHEMA_VERSION``
raises ``StoreNewer``;
any SQLite or file error on open raises ``StoreFailed``.
"""

from __future__ import annotations

import sqlite3
import struct
import zlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import astuple, fields
from pathlib import Path

from atlas.store import (
    ApprovalRecord,
    CallRecord,
    InboxRecord,
    LinkedSource,
    PageText,
    SourceRecord,
    StoredSource,
    StoreFailed,
    StoreNewer,
)

SCHEMA_FILE = Path(__file__).resolve().parent / "schema_dev.sql"
SCHEMA_VERSION = 0

_CALL_COLUMNS = (
    "at, command, role, model, thinking, tokens_in, tokens_out, cache_read, cache_write, cost_usd, cost_kind"
)
_APPROVAL_COLUMNS = "at, command, change_kind, by, words, decision_id"
_SOURCE_COLUMNS = ", ".join(field.name for field in fields(SourceRecord))
_STORED_COLUMNS = "s.id, s.key_link, s.last_read, s.archived_at"
_MINHASH = struct.Struct("<64I")


def _image_hashes(text: str) -> tuple[str, ...]:
    return tuple(text.split())


def _schema_id(text: str) -> int:
    """The schema text's CRC-32 as the signed 32-bit integer ``application_id`` holds."""
    crc = zlib.crc32(text.encode("utf-8"))
    return crc - (1 << 32) if crc >= 1 << 31 else crc


class SqliteStore:
    def __init__(self, path: Path, connection: sqlite3.Connection) -> None:
        self.path = path
        self._db = connection
        self._depth = 0

    def _run(self, sql: str, args: tuple[object, ...] = ()) -> list[tuple]:
        try:
            return self._db.execute(sql, args).fetchall()
        except sqlite3.Error as err:
            raise StoreFailed(self.path, str(err)) from None

    def size(self) -> int:
        return self.path.stat().st_size

    def add_call(self, call: CallRecord) -> None:
        self._run(f"INSERT INTO calls ({_CALL_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", astuple(call))

    def calls_since(self, at: str) -> list[CallRecord]:
        rows = self._run(f"SELECT {_CALL_COLUMNS} FROM calls WHERE at >= ? ORDER BY at, id", (at,))
        return [CallRecord(*row) for row in rows]

    def recent_calls(self, role: str, limit: int) -> list[CallRecord]:
        rows = self._run(
            f"SELECT {_CALL_COLUMNS} FROM calls WHERE role = ? ORDER BY at DESC, id DESC LIMIT ?", (role, limit)
        )
        return [CallRecord(*row) for row in rows]

    def models_not_billed(self, except_role: str) -> list[str]:
        rows = self._run(
            "SELECT DISTINCT model FROM calls WHERE cost_kind != 'billed' AND role != ? ORDER BY model", (except_role,)
        )
        return [model for (model,) in rows]

    def add_approval(self, approval: ApprovalRecord) -> None:
        self._run(f"INSERT INTO approvals ({_APPROVAL_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?)", astuple(approval))

    @contextmanager
    def transaction(self) -> Iterator[None]:
        name = f"atlas_{self._depth}"
        self._depth += 1
        try:
            self._run(f"SAVEPOINT {name}")
            try:
                yield
            except BaseException:
                self._run(f"ROLLBACK TO {name}")
                self._run(f"RELEASE {name}")
                raise
            self._run(f"RELEASE {name}")
        finally:
            self._depth -= 1

    def source(self, source_id: int) -> StoredSource:
        rows = self._run(f"SELECT {_STORED_COLUMNS} FROM sources s WHERE s.id = ?", (source_id,))
        if not rows:
            raise StoreFailed(self.path, f"no source has id {source_id}")
        return StoredSource(*rows[0])

    def source_for_link(self, link: str) -> LinkedSource | None:
        rows = self._run(
            f"SELECT {_STORED_COLUMNS}, l.kind FROM links l JOIN sources s ON s.id = l.source_id WHERE l.link = ?",
            (link,),
        )
        return LinkedSource(StoredSource(*rows[0][:4]), rows[0][4]) if rows else None

    def source_by_hash(self, content_hash: str) -> StoredSource | None:
        rows = self._run(
            f"SELECT {_STORED_COLUMNS} FROM sources s WHERE s.content_hash = ? ORDER BY s.id LIMIT 1", (content_hash,)
        )
        return StoredSource(*rows[0]) if rows else None

    def signatures(self) -> list[tuple[int, tuple[int, ...]]]:
        rows = self._run("SELECT source_id, minhash FROM page_text ORDER BY source_id")
        return [(source_id, _MINHASH.unpack(minhash)) for source_id, minhash in rows]

    def page_text(self, source_id: int) -> PageText:
        rows = self._run("SELECT text, image_hashes, minhash FROM page_text WHERE source_id = ?", (source_id,))
        if not rows:
            raise StoreFailed(self.path, f"source {source_id} has no page text")
        text, image_hashes, minhash = rows[0]
        return PageText(zlib.decompress(text).decode("utf-8"), _image_hashes(image_hashes), _MINHASH.unpack(minhash))

    def _page_values(self, page: PageText) -> tuple[bytes, str, bytes]:
        return zlib.compress(page.text.encode("utf-8")), " ".join(page.image_hashes), _MINHASH.pack(*page.minhash)

    def add_source(self, source: SourceRecord, page: PageText) -> int:
        marks = ", ".join("?" * len(fields(SourceRecord)))
        with self.transaction():
            [(source_id,)] = self._run(
                f"INSERT INTO sources ({_SOURCE_COLUMNS}) VALUES ({marks}) RETURNING id", astuple(source)
            )
            self._run(
                "INSERT INTO page_text (source_id, text, image_hashes, minhash) VALUES (?, ?, ?, ?)",
                (source_id, *self._page_values(page)),
            )
        return source_id

    def update_page(self, source_id: int, content_hash: str, last_read: str, page: PageText) -> None:
        with self.transaction():
            self._run(
                "UPDATE sources SET content_hash = ?, last_read = ? WHERE id = ?", (content_hash, last_read, source_id)
            )
            self._run(
                "UPDATE page_text SET text = ?, image_hashes = ?, minhash = ? WHERE source_id = ?",
                (*self._page_values(page), source_id),
            )

    def add_link(self, link: str, source_id: int, kind: str, at: str) -> None:
        self._run("INSERT INTO links (link, source_id, kind, added_at) VALUES (?, ?, ?, ?)", (link, source_id, kind, at))

    def move_link(self, link: str, source_id: int, kind: str) -> None:
        self._run("UPDATE links SET source_id = ?, kind = ? WHERE link = ?", (source_id, kind, link))

    def add_inbox(self, item: InboxRecord) -> None:
        self._run("INSERT INTO inbox (link, added_at, origin) VALUES (?, ?, ?)", astuple(item))

    def inbox(self) -> list[InboxRecord]:
        return [InboxRecord(*row) for row in self._run("SELECT link, added_at, origin FROM inbox ORDER BY added_at, link")]

    def in_inbox(self, link: str) -> bool:
        return bool(self._run("SELECT 1 FROM inbox WHERE link = ?", (link,)))

    def remove_inbox(self, links: Sequence[str]) -> None:
        for link in links:
            self._run("DELETE FROM inbox WHERE link = ?", (link,))

    def close(self) -> None:
        self._db.close()


def _rebuild(db: sqlite3.Connection, schema: str, schema_id: int) -> None:
    """Drop every table and view, then apply ``schema``, in one transaction."""
    objects = db.execute(
        "SELECT type, name FROM sqlite_master WHERE type IN ('view', 'table') AND name NOT LIKE 'sqlite_%'"
        " ORDER BY type = 'table'"
    ).fetchall()
    drops = "".join(f'DROP {kind.upper()} IF EXISTS "{name.replace(chr(34), chr(34) * 2)}";\n' for kind, name in objects)
    db.execute("PRAGMA foreign_keys = OFF")
    try:
        db.executescript(f"BEGIN;\n{drops}{schema}\nPRAGMA application_id = {schema_id};\nCOMMIT;")
    except sqlite3.Error:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise
    db.execute("PRAGMA foreign_keys = ON")


def open_store(path: Path) -> SqliteStore:
    """Open the store at ``path``, creating it and its folder on first open."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path, isolation_level=None)
    except (OSError, sqlite3.Error) as err:
        raise StoreFailed(path, str(err)) from None
    try:
        if db.execute("PRAGMA user_version").fetchone()[0] > SCHEMA_VERSION:
            raise StoreNewer(path)
        db.execute("PRAGMA journal_mode = WAL")
        db.execute("PRAGMA foreign_keys = ON")
        schema = SCHEMA_FILE.read_text(encoding="utf-8")
        schema_id = _schema_id(schema)
        if db.execute("PRAGMA application_id").fetchone()[0] != schema_id:
            _rebuild(db, schema, schema_id)
    except sqlite3.Error as err:
        db.close()
        raise StoreFailed(path, str(err)) from None
    except BaseException:
        db.close()
        raise
    return SqliteStore(path, db)
