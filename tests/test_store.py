"""The SQLite store on a temporary file: first open and the dev schema rebuild."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "atlas-ask"))
from atlas.store import sqlite  # noqa: E402


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.path = self.folder / "share" / "atlas" / "smoke.db"

    def tables(self) -> set[str]:
        with sqlite3.connect(self.path) as db:
            return {name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}

    def test_first_open_creates_the_file_and_folder_in_wal_mode(self) -> None:
        sqlite.open_store(self.path).close()
        self.assertTrue(self.path.is_file())
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_schema_is_rebuilt_only_when_its_text_changes(self) -> None:
        schema = self.folder / "schema_dev.sql"
        self.enterContext(mock.patch.object(sqlite, "SCHEMA_FILE", schema))
        schema.write_text("CREATE TABLE kept (x);\n")
        sqlite.open_store(self.path).close()
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO kept VALUES (1)")
        sqlite.open_store(self.path).close()
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT x FROM kept").fetchall(), [(1,)])

        schema.write_text("CREATE TABLE fresh (y);\n")
        sqlite.open_store(self.path).close()
        self.assertEqual(self.tables(), {"fresh"})


if __name__ == "__main__":
    unittest.main()
