"""The store's numbered migrations on a temporary file: the baseline, later migrations and a newer store."""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "atlas-ask"))
from atlas.store import StoreFailed, StoreNewer, sqlite  # noqa: E402

SHIPPED = ROOT / "skills" / "atlas-ask" / "atlas" / "store" / "migrations"
# The number of the last shipped migration, read from the file names.
LATEST = max(int(path.name[:4]) for path in SHIPPED.glob("[0-9][0-9][0-9][0-9]_*.sql"))


class MigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.path = self.folder / "main.db"

    def query(self, sql: str) -> list[tuple]:
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute(sql).fetchall()

    def tables(self) -> set[str]:
        return {name for (name,) in self.query("SELECT name FROM sqlite_master WHERE type = 'table'")}

    def version(self) -> int:
        return self.query("PRAGMA user_version")[0][0]

    def own_migrations(self, *scripts: str) -> None:
        """Replace the shipped migrations with ``scripts``, numbered from 0001."""
        folder = self.folder / "migrations"
        folder.mkdir(exist_ok=True)
        for old in folder.iterdir():
            old.unlink()
        for number, script in enumerate(scripts, 1):
            (folder / f"{number:04d}_step.sql").write_text(script)
        self.enterContext(mock.patch.object(sqlite, "MIGRATIONS", folder))

    def test_fresh_store_gets_the_baseline_once(self) -> None:
        sqlite.open_store(self.path).close()
        self.assertEqual(self.version(), LATEST)
        self.assertLessEqual({"sources", "links", "related_links", "expansions", "queries", "tally"}, self.tables())
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO inbox (link, added_at, origin) VALUES ('https://example.com/a', 'now', 'user')")
            db.commit()
        sqlite.open_store(self.path).close()
        self.assertEqual(self.query("SELECT link FROM inbox"), [("https://example.com/a",)])
        self.assertEqual(self.version(), LATEST)

    def test_a_version_1_store_gains_notes_on_open_and_keeps_its_rows(self) -> None:
        baseline = self.folder / "baseline"
        baseline.mkdir()
        shutil.copy(SHIPPED / "0001_baseline.sql", baseline)
        with mock.patch.object(sqlite, "MIGRATIONS", baseline):
            sqlite.open_store(self.path).close()
        self.assertEqual((self.version(), "notes" in self.tables()), (1, False))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO inbox (link, added_at, origin) VALUES ('https://example.com/a', 'now', 'user')")
            db.commit()
        sqlite.open_store(self.path).close()
        self.assertEqual(self.version(), LATEST)
        self.assertEqual(self.query("SELECT link FROM inbox"), [("https://example.com/a",)])
        columns = [row[1] for row in self.query("PRAGMA table_info(notes)")]
        self.assertEqual(columns, ["id", "who", "subject", "lean", "reason", "at", "archived_at"])
        with closing(sqlite3.connect(self.path)) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO notes (who, subject, lean, reason, at) VALUES ('a', 'b', 'sideways', 'c', 'now')")

    def test_a_version_2_store_gains_the_topic_tables_on_open_and_keeps_its_rows(self) -> None:
        older = self.folder / "older"
        older.mkdir()
        for name in ("0001_baseline.sql", "0002_notes.sql"):
            shutil.copy(SHIPPED / name, older)
        with mock.patch.object(sqlite, "MIGRATIONS", older):
            sqlite.open_store(self.path).close()
        self.assertEqual((self.version(), "topics" in self.tables()), (2, False))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO notes (who, subject, lean, reason, at) VALUES ('a', 'b', 'towards', 'c', 'now')")
            db.commit()
        sqlite.open_store(self.path).close()
        self.assertEqual(self.version(), LATEST)
        self.assertLessEqual({"topics", "versions", "version_claims", "marks", "plans", "plan_items"}, self.tables())
        self.assertEqual(self.query("SELECT who FROM notes"), [("a",)])
        topics = [row[1] for row in self.query("PRAGMA table_info(topics)")]
        self.assertEqual(topics, ["id", "name", "brief", "followed", "reviewed_up_to", "last_catchup", "archived_at"])
        versions = [row[1] for row in self.query("PRAGMA table_info(versions)")]
        self.assertEqual(versions, ["topic_id", "n", "text", "writer_model", "thinking", "cross_check", "reviewers", "run", "changes", "diff", "saved_at"])
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO topics (name, brief) VALUES ('t', 'b')")
            insert = "INSERT INTO versions (topic_id, n, text, cross_check, saved_at) VALUES (1, ?, 'x', ?, 'now')"
            db.execute(insert, (1, "not cross-checked: Reconcile is not ready"))
            for n, status in ((2, "maybe"), (3, "")):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(insert, (n, status))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO topics (name, brief) VALUES ('t', 'again')")

    def test_a_version_3_store_gains_citations_on_open_and_a_row_cites_a_source_or_a_version_never_both(self) -> None:
        older = self.folder / "older"
        older.mkdir()
        for name in ("0001_baseline.sql", "0002_notes.sql", "0003_topics.sql"):
            shutil.copy(SHIPPED / name, older)
        with mock.patch.object(sqlite, "MIGRATIONS", older):
            sqlite.open_store(self.path).close()
        self.assertEqual((self.version(), "citations" in self.tables()), (3, False))
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("INSERT INTO topics (name, brief) VALUES ('t', 'b')")
            db.commit()
        sqlite.open_store(self.path).close()
        self.assertEqual(self.version(), LATEST)
        self.assertEqual(self.query("SELECT name FROM topics"), [("t",)])
        columns = [row[1] for row in self.query("PRAGMA table_info(citations)")]
        self.assertEqual(columns, ["id", "source_id", "topic_id", "n", "repo", "file", "at", "archived_at"])
        insert = "INSERT INTO citations (source_id, topic_id, n, repo, file, at) VALUES (?, ?, ?, 'o/r', 'f.md', 'now')"
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(insert, (1, None, None))
            db.execute(insert, (None, 1, 1))
            for cited in ((1, 1, 1), (1, None, 1), (None, None, None), (None, 1, None)):
                with self.assertRaises(sqlite3.IntegrityError, msg=str(cited)):
                    db.execute(insert, cited)

    def test_newer_store_stops_and_is_left_as_it_is(self) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            db.execute(f"PRAGMA user_version = {LATEST + 1}")
        with self.assertRaises(StoreNewer):
            sqlite.open_store(self.path)
        self.assertEqual((self.version(), self.tables()), (LATEST + 1, set()))

    def test_later_migrations_apply_in_order_above_the_store_version(self) -> None:
        self.own_migrations("CREATE TABLE a (x);")
        sqlite.open_store(self.path).close()
        self.own_migrations("CREATE TABLE a (x);", "ALTER TABLE a ADD COLUMN y;", "INSERT INTO a VALUES (1, 2);")
        sqlite.open_store(self.path).close()
        self.assertEqual((self.version(), self.query("SELECT x, y FROM a")), (3, [(1, 2)]))

    def test_failed_migration_leaves_the_store_as_it_was(self) -> None:
        self.own_migrations("CREATE TABLE a (x);")
        sqlite.open_store(self.path).close()
        self.own_migrations("CREATE TABLE a (x);", "CREATE TABLE b (y);", "INSERT INTO missing VALUES (1);")
        with self.assertRaises(StoreFailed):
            sqlite.open_store(self.path)
        self.assertEqual((self.version(), self.tables()), (1, {"a"}))

    def test_store_with_tables_but_no_migration_fails_and_keeps_its_rows(self) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TABLE sources (id INTEGER PRIMARY KEY, key_link TEXT)")
            db.execute("INSERT INTO sources (key_link) VALUES ('https://example.com/kept')")
            db.commit()
        with self.assertRaises(StoreFailed):
            sqlite.open_store(self.path)
        self.assertEqual((self.version(), self.tables()), (0, {"sources"}))
        self.assertEqual(self.query("SELECT key_link FROM sources"), [("https://example.com/kept",)])


if __name__ == "__main__":
    unittest.main()
