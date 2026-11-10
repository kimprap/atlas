"""The store's numbered migrations on a temporary file: the baseline, later migrations and a newer store."""

from __future__ import annotations

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
