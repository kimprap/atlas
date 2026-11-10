"""The SQLite store on a temporary file: first open and the call and approval records."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "atlas-ask"))
from atlas.store import ApprovalRecord, CallRecord, StoreFailed, sqlite  # noqa: E402


def call(at: str, role: str, model: str, cost: float | None, kind: str, tokens_in: int = 10) -> CallRecord:
    return CallRecord(at, "add", role, model, "high", tokens_in, 5, 2, 1, cost, kind)


class StoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.path = self.folder / "share" / "atlas" / "smoke.db"

    def test_first_open_creates_the_file_and_folder_in_wal_mode(self) -> None:
        sqlite.open_store(self.path).close()
        self.assertTrue(self.path.is_file())
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_call_and_approval_records_read_back(self) -> None:
        store = sqlite.open_store(self.path)
        self.addCleanup(store.close)
        old = call("2026-10-31T23:00:00+00:00", "atlas_summarize", "m/a", 0.5, "estimated", tokens_in=1)
        new = call("2026-11-01T00:00:00+00:00", "atlas_summarize", "m/a", 0.2, "estimated", tokens_in=2)
        judged = call("2026-11-02T00:00:00+00:00", "judge", "jev-1", None, "unknown")
        billed = call("2026-11-03T00:00:00+00:00", "atlas_escalate", "m/b", 1.25, "billed")
        for record in (new, old, judged, billed):
            store.add_call(record)
        self.assertEqual(store.calls_since("2026-11-01T00:00:00+00:00"), [new, judged, billed])
        self.assertEqual(store.recent_calls("atlas_summarize", 1), [new])
        self.assertEqual(store.models_not_billed("judge"), ["m/a"])
        with self.assertRaises(StoreFailed):
            store.add_call(call("2026-11-04T00:00:00+00:00", "x", "m/c", 1.0, "unknown"))

        store.add_approval(ApprovalRecord("2026-11-03T00:00:00+00:00", "add", "add", "request", "add it", None))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT at, command, change_kind, by, words, decision_id FROM approvals").fetchall(),
                [("2026-11-03T00:00:00+00:00", "add", "add", "request", "add it", None)],
            )


if __name__ == "__main__":
    unittest.main()
