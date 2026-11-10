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

import json
import re
import sqlite3
import struct
import zlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict, astuple, fields, replace
from pathlib import Path

from atlas.store import (
    ApprovalRecord,
    CallRecord,
    ClaimRecord,
    CopyFlagRecord,
    ExpansionRecord,
    FlagRecord,
    HistoryRecord,
    InboxRecord,
    LinkedSource,
    Neighbour,
    PageText,
    QueryRecord,
    QuoteRecord,
    SourceRecord,
    StoreCounts,
    StoredClaim,
    StoredSource,
    StoreFailed,
    StoreNewer,
    TallyRecord,
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
_SOURCE_FIELDS = frozenset(field.name for field in fields(SourceRecord))
_BOOL_FIELDS = ("unchangeable", "escalated")
# The words of a copy-check query: at most this many distinct ones.
_QUERY_WORDS = 64
_WORD = re.compile(r"\w+")


def _source_record(row: tuple) -> SourceRecord:
    record = SourceRecord(*row)
    flags = {name: None if getattr(record, name) is None else bool(getattr(record, name)) for name in _BOOL_FIELDS}
    return replace(record, **flags)


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

    def source_record(self, source_id: int) -> SourceRecord:
        rows = self._run(f"SELECT {_SOURCE_COLUMNS} FROM sources WHERE id = ?", (source_id,))
        if not rows:
            raise StoreFailed(self.path, f"no source has id {source_id}")
        return _source_record(rows[0])

    def update_summary(self, source_id: int, **columns: object) -> None:
        unknown = sorted(set(columns) - _SOURCE_FIELDS)
        if unknown:
            raise ValueError(f"not source columns: {', '.join(unknown)}")
        if columns:
            assignments = ", ".join(f"{name} = ?" for name in columns)
            self._run(f"UPDATE sources SET {assignments} WHERE id = ?", (*columns.values(), source_id))

    def _set_flag(self, claim_id: int, flag: FlagRecord) -> None:
        self._run(
            "INSERT OR REPLACE INTO claim_flags (claim_id, verdict, p, flagged, judge_model, at) VALUES (?, ?, ?, ?, ?, ?)",
            (claim_id, flag.verdict, flag.p, int(flag.flagged), flag.judge_model, flag.at),
        )

    def _set_quotes(self, claim_id: int, quotes: Sequence[QuoteRecord]) -> None:
        self._run("DELETE FROM quotes WHERE claim_id = ?", (claim_id,))
        for ord, quote in enumerate(quotes, 1):
            self._run(
                'INSERT INTO quotes (claim_id, ord, text, start, "end") VALUES (?, ?, ?, ?, ?)',
                (claim_id, ord, quote.text, quote.start, quote.end),
            )

    def add_claim(self, source_id: int, ord: int, claim: ClaimRecord, at: str) -> int:
        with self.transaction():
            [(claim_id,)] = self._run(
                "INSERT INTO claims (source_id, ord, section, text, basis, created_at) VALUES (?, ?, ?, ?, ?, ?) RETURNING id",
                (source_id, ord, claim.section, claim.text, claim.basis, at),
            )
            self._set_quotes(claim_id, claim.quotes)
            if claim.flag is not None:
                self._set_flag(claim_id, claim.flag)
        return claim_id

    def claims(self, source_id: int) -> list[StoredClaim]:
        rows = self._run(
            "SELECT c.id, c.ord, c.section, c.text, c.basis, f.verdict, f.p, f.flagged, f.judge_model, f.at"
            " FROM claims c LEFT JOIN claim_flags f ON f.claim_id = c.id"
            " WHERE c.source_id = ? AND c.replaced_at IS NULL ORDER BY c.ord, c.id",
            (source_id,),
        )
        found = []
        for claim_id, ord, section, text, basis, verdict, p, flagged, judge_model, at in rows:
            quotes = tuple(
                QuoteRecord(*row)
                for row in self._run('SELECT text, start, "end" FROM quotes WHERE claim_id = ? ORDER BY ord', (claim_id,))
            )
            flag = None if verdict is None else FlagRecord(verdict, p, bool(flagged), judge_model, at)
            found.append(StoredClaim(claim_id, ord, ClaimRecord(section, text, basis, quotes, flag)))
        return found

    def replace_claim(self, claim_id: int, at: str) -> None:
        self._run("UPDATE claims SET replaced_at = ? WHERE id = ?", (at, claim_id))

    def move_claim(self, claim_id: int, ord: int, quotes: Sequence[QuoteRecord]) -> None:
        with self.transaction():
            self._run("UPDATE claims SET ord = ? WHERE id = ?", (ord, claim_id))
            self._set_quotes(claim_id, quotes)

    def add_related_links(self, source_id: int, links: Sequence[str], origin: str) -> None:
        if origin == "page":
            sql = "INSERT OR IGNORE INTO related_links (source_id, link, origin) VALUES (?, ?, ?)"
        else:
            sql = (
                "INSERT INTO related_links (source_id, link, origin) VALUES (?, ?, ?)"
                " ON CONFLICT (source_id, link) DO UPDATE SET origin = excluded.origin"
            )
        for link in links:
            self._run(sql, (source_id, link, origin))

    def add_expansion(self, expansion: ExpansionRecord) -> None:
        self._run("INSERT OR IGNORE INTO expansions (link, choice, at) VALUES (?, ?, ?)", astuple(expansion))

    def expansion(self, link: str) -> ExpansionRecord | None:
        rows = self._run("SELECT link, choice, at FROM expansions WHERE link = ?", (link,))
        return ExpansionRecord(*rows[0]) if rows else None

    def expansion_sources(self, link: str) -> list[str]:
        rows = self._run(
            "SELECT s.key_link FROM related_links r JOIN sources s ON s.id = r.source_id"
            " WHERE r.link = ? AND r.origin = 'expansion' AND s.archived_at IS NULL ORDER BY s.id",
            (link,),
        )
        return [key_link for (key_link,) in rows]

    def add_copy_flags(self, source_id: int, flags: Sequence[CopyFlagRecord]) -> None:
        for flag in flags:
            self._run(
                "INSERT OR REPLACE INTO copy_flags (source_id, other_source_id, p, flagged, judge_model, at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (source_id, flag.other_source_id, flag.p, int(flag.flagged), flag.judge_model, flag.at),
            )

    def add_history(self, event: HistoryRecord) -> None:
        self._run(
            "INSERT INTO summary_history (source_id, at, event, rubric_version, model, escalated) VALUES (?, ?, ?, ?, ?, ?)",
            (event.source_id, event.at, event.event, event.rubric_version, event.model, int(event.escalated)),
        )

    def index_source(self, source_id: int) -> None:
        [(title, abstract)] = self._run("SELECT title, abstract FROM sources WHERE id = ?", (source_id,)) or [(None, None)]
        claims = "\n".join(
            text
            for (text,) in self._run(
                "SELECT text FROM claims WHERE source_id = ? AND replaced_at IS NULL ORDER BY ord", (source_id,)
            )
        )
        with self.transaction():
            self._run("DELETE FROM source_fts WHERE rowid = ?", (source_id,))
            self._run(
                "INSERT INTO source_fts (rowid, title, abstract, claims) VALUES (?, ?, ?, ?)",
                (source_id, title or "", abstract or "", claims),
            )

    def _match(self, text: str, columns: str) -> str | None:
        """An FTS5 query matching any of ``text``'s first distinct words in ``columns``, or ``None`` without words."""
        words = list(dict.fromkeys(word.casefold() for word in _WORD.findall(text)))[:_QUERY_WORDS]
        if not words:
            return None
        return columns + " : (" + " OR ".join('"' + word.replace('"', '""') + '"' for word in words) + ")"

    def similar(self, text: str, limit: int) -> list[Neighbour]:
        query = self._match(text, "{title abstract}")
        if query is None:
            return []
        rows = self._run(
            "SELECT s.id, s.key_link, s.title, s.abstract FROM source_fts JOIN sources s ON s.id = source_fts.rowid"
            " WHERE source_fts MATCH ? AND s.archived_at IS NULL ORDER BY bm25(source_fts) LIMIT ?",
            (query, limit),
        )
        return [Neighbour(*row) for row in rows]

    def search(self, text: str, limit: int) -> list[int]:
        query = self._match(text, "{title abstract claims}")
        if query is None:
            return []
        rows = self._run(
            "SELECT s.id FROM source_fts JOIN sources s ON s.id = source_fts.rowid"
            " WHERE source_fts MATCH ? AND s.archived_at IS NULL ORDER BY bm25(source_fts), s.id LIMIT ?",
            (query, limit),
        )
        return [source_id for (source_id,) in rows]

    def related_links(self, source_ids: Sequence[int]) -> list[tuple[int, str]]:
        if not source_ids:
            return []
        marks = ", ".join("?" * len(source_ids))
        rows = self._run(
            f"SELECT source_id, link FROM related_links WHERE source_id IN ({marks}) ORDER BY source_id, link",
            tuple(source_ids),
        )
        return [(source_id, link) for source_id, link in rows]

    def add_query(self, query: QueryRecord) -> None:
        records = None if query.judge_records is None else json.dumps([asdict(row) for row in query.judge_records])
        self._run(
            "INSERT INTO queries (at, op, original, question, phrasings, context, ranker, judge_records, note)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                query.at,
                query.op,
                query.original,
                query.question,
                json.dumps(list(query.phrasings), ensure_ascii=False),
                query.context,
                query.ranker,
                records,
                query.note,
            ),
        )

    def add_tally(self, lines: Sequence[TallyRecord]) -> None:
        with self.transaction():
            for line in lines:
                self._run(
                    "INSERT INTO tally (who, subject, link, direction, at) VALUES (?, ?, ?, ?, ?)", astuple(line)
                )

    def counts(self) -> StoreCounts:
        [(sources, archived)] = self._run(
            "SELECT count(*) FILTER (WHERE archived_at IS NULL), count(*) FILTER (WHERE archived_at IS NOT NULL) FROM sources"
        )
        [(claims,)] = self._run(
            "SELECT count(*) FROM claims c JOIN sources s ON s.id = c.source_id"
            " WHERE c.replaced_at IS NULL AND s.archived_at IS NULL"
        )
        [(inbox,)] = self._run("SELECT count(*) FROM inbox")
        return StoreCounts(sources, claims, inbox, archived)

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
