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
import zlib
from pathlib import Path

from atlas.store import StoreFailed, StoreNewer

SCHEMA_FILE = Path(__file__).resolve().parent / "schema_dev.sql"
SCHEMA_VERSION = 0


def _schema_id(text: str) -> int:
    """The schema text's CRC-32 as the signed 32-bit integer ``application_id`` holds."""
    crc = zlib.crc32(text.encode("utf-8"))
    return crc - (1 << 32) if crc >= 1 << 31 else crc


class SqliteStore:
    def __init__(self, path: Path, connection: sqlite3.Connection) -> None:
        self.path = path
        self._db = connection

    def size(self) -> int:
        return self.path.stat().st_size

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
