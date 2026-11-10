"""Source identity (spec 4.9) on the core module, the step ``add`` calls before and after each read.

``add`` arrives with the summary pipeline, so these drive ``identity.Batch`` the
way ``add`` does: read only ``to_read()`` items through the fake host's read
port, examine each read, and keep each new page. The store is the real SQLite
store in a temporary folder.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any

from tests.fakes.fake_host import FakeHost

from atlas import ports  # noqa: E402  (fake_host puts the package on sys.path)
from atlas.core import identity  # noqa: E402

NOW = datetime(2026, 11, 15, 12, 0).astimezone()
LATER = datetime(2026, 11, 20, 12, 0).astimezone()
NEAR_COPY = 0.90
A = "https://example.com/report"
B = "https://mirror.example.org/copy"


def words(count: int, changed: tuple[int, ...] = ()) -> str:
    """``count`` distinct words, with the words at ``changed`` replaced by new ones.

    Every changed word well inside the text removes the 5 shingles that cover it
    and adds 5 new ones, so with 204 words (200 shingles) and k changed words the
    share with the unchanged text is (200 - 5k) / 200.
    """
    return " ".join(f"new{at}" if at in changed else f"word{at}" for at in range(count))


def page(link: str, text: str, final_link: str | None = None, kind: str = "article") -> ports.Page:
    return ports.Page(final_link or link, "Title", None, None, None, kind, text)


class IdentityTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.path = folder / "smoke.db"
        self.fake = FakeHost()
        self.store = self.fake.open_store(self.path)
        self.addCleanup(self.store.close)

    def batch(self, *given: str | tuple[str, Any], now: datetime = NOW) -> identity.Batch:
        items = [item if isinstance(item, tuple) else (item, None) for item in given]
        return identity.Batch(self.store, NEAR_COPY, items, now=now)

    def add(self, *given: str | tuple[str, Any], now: datetime = NOW, keep: bool = True) -> list[identity.Outcome]:
        """One batch as ``add`` runs it: read only what ``to_read()`` lists, keep each new page."""
        batch = self.batch(*given, now=now)
        for item in batch.to_read():
            outcome = batch.examine(item, self.fake.read(item.link))
            if outcome.kind == identity.NEW and keep:
                assert outcome.new is not None
                batch.keep(outcome.new, abstract="An abstract.")
        return [batch.outcome(item) or identity.Outcome(item, identity.NEW, "not kept") for item in batch.items]

    def reads(self) -> list[str]:
        return [call[1] for call in self.fake.calls if call[0] == "read"]

    def rows(self, sql: str) -> list[tuple]:
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute(sql).fetchall()

    def test_a_stored_link_is_matched_before_any_read_and_never_read_again(self) -> None:
        self.fake.pages[A] = page(A, words(50))
        [first] = self.add(f"{A}?utm_source=feed")
        self.assertEqual((first.kind, first.result), (identity.NEW, "added"))
        self.assertEqual(self.reads(), [A])

        self.fake.calls.clear()
        outcomes = self.add(A, f"{A}/#top", now=LATER)
        self.assertEqual(
            [(o.kind, o.result) for o in outcomes],
            [(identity.STORED, "already stored, last read 2026-11-15"), (identity.REPEAT, f"same source as {A} in this batch")],
        )
        self.assertEqual(self.reads(), [])
        self.assertEqual(
            self.rows("SELECT key_link, kind, unchangeable, text_origin, abstract FROM sources"),
            [(A, "article", 0, "read", "An abstract.")],
        )

    def test_same_text_under_a_new_link_joins_without_a_new_source(self) -> None:
        self.fake.pages[A] = page(A, "Line one\r\nline  two\n\n")
        self.fake.pages[B] = page(B, "Line one\nline two")
        self.add(A)
        [joined] = self.add(B)
        self.assertEqual((joined.kind, joined.result), (identity.JOINED, f"already stored as {A}"))
        self.assertEqual(self.rows("SELECT link, source_id, kind FROM links ORDER BY link"), [(A, 1, "key"), (B, 1, "other")])

        self.fake.calls.clear()
        [again] = self.add(B)
        self.assertEqual(again.kind, identity.STORED)
        self.assertEqual(self.reads(), [])

    def test_a_redirect_to_a_stored_key_link_joins_the_given_link(self) -> None:
        self.fake.pages[A] = page(A, words(50))
        self.fake.pages[B] = page(B, words(50, (10,)), final_link=f"{A}?utm_medium=x")
        self.add(A)
        stored, joined = self.add(A, B)
        self.assertEqual(stored.kind, identity.STORED)
        self.assertEqual((joined.kind, joined.result), (identity.JOINED, f"already stored as {A}"))
        self.assertEqual(self.rows("SELECT link, source_id FROM links ORDER BY link"), [(A, 1), (B, 1)])

    def test_a_near_copy_at_the_limit_joins_with_its_share_and_one_below_is_new(self) -> None:
        self.fake.pages[A] = page(A, words(204))
        self.fake.pages[B] = page(B, words(204, (20, 60, 100, 140)))  # (200 - 20) / 200 = 90%
        other = "https://elsewhere.example.net/draft"
        self.fake.pages[other] = page(other, words(204, (20, 50, 80, 110, 140)))  # (200 - 25) / 200 = 87.5%
        self.add(A)
        near, below = self.add(B, other)
        self.assertEqual((near.kind, near.result, near.source_link), (identity.NEAR_COPY, "joined near copy (90%)", A))
        self.assertAlmostEqual(near.share, 0.90)
        self.assertEqual(
            near.next, {"label": "store it separately instead", "then": {"resend": {"items": [{"link": B, "scope": "separate"}]}}}
        )
        self.assertEqual((below.kind, below.result), (identity.NEW, "added"))
        self.assertEqual(self.rows("SELECT link, source_id FROM links ORDER BY source_id, link"), [(A, 1), (B, 1), (other, 2)])

    def test_store_it_separately_reads_the_joined_link_and_gives_it_its_own_source(self) -> None:
        self.fake.pages[A] = page(A, words(204))
        self.fake.pages[B] = page(B, words(204, (30,)))
        self.add(A)
        self.add(B)
        self.fake.calls.clear()
        [separate] = self.add((B, identity.SEPARATE))
        self.assertEqual((separate.kind, separate.result), (identity.NEW, "added"))
        self.assertEqual(self.reads(), [B])
        self.assertEqual(self.rows("SELECT link, source_id, kind FROM links ORDER BY link"), [(A, 1, "key"), (B, 2, "key")])

    def test_store_it_separately_holds_for_a_near_copy_read_under_another_link(self) -> None:
        final = "https://example.com/builds"
        self.fake.pages[A] = page(A, words(204))
        self.fake.pages[B] = page(B, words(204, (30,)), final_link=final)
        self.add(A)
        [near] = self.add(B)
        self.assertEqual(near.kind, identity.NEAR_COPY)
        [separate] = self.add((B, identity.SEPARATE))
        self.assertEqual((separate.kind, separate.result, separate.source_link), (identity.NEW, "added", final))
        self.assertEqual(
            self.rows("SELECT link, source_id, kind FROM links ORDER BY link"),
            [(final, 2, "key"), (A, 1, "key"), (B, 2, "other")],
        )

    def test_an_archived_link_reports_archived_and_is_not_read(self) -> None:
        self.fake.pages[A] = page(A, words(50))
        self.add(A)
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE sources SET archived_at = ?", (LATER.isoformat(),))
        self.fake.calls.clear()
        [archived] = self.add(A)
        self.assertEqual((archived.kind, archived.result), (identity.ARCHIVED, "archived 2026-11-20"))
        self.assertEqual(self.reads(), [])

    def test_one_batch_handles_one_source_once(self) -> None:
        moved = "https://old.example.com/report"
        twin = "https://twin.example.com/report"
        self.fake.pages[A] = page(A, words(50))
        self.fake.pages[moved] = page(moved, words(50, (5,)), final_link=A)
        self.fake.pages[twin] = page(twin, words(50))
        outcomes = self.add(A, f"{A}?fbclid=1", moved, twin, keep=False)
        self.assertEqual(
            [(o.kind, o.result) for o in outcomes],
            [
                (identity.NEW, "not kept"),
                (identity.REPEAT, f"same source as {A} in this batch"),
                (identity.REPEAT, f"same source as {A} in this batch"),
                (identity.REPEAT, f"same source as {A} in this batch"),
            ],
        )
        self.assertEqual(self.reads(), [A, moved, twin])
        self.assertEqual(self.rows("SELECT count(*) FROM sources"), [(0,)])

    def test_the_hash_covers_image_bytes_and_unreadable_pages_store_nothing(self) -> None:
        def examine(link: str, image: bytes) -> identity.Outcome:
            batch = self.batch(link)
            [item] = batch.to_read()
            outcome = batch.examine(item, page(link, "Chart", kind="image"), images=[image])
            if outcome.new is not None:
                batch.keep(outcome.new)
            return outcome

        chart = "https://example.com/chart"
        self.assertEqual(examine(chart, b"\x89PNG one").kind, identity.NEW)
        same = examine("https://example.com/chart-copy", b"\x89PNG one")
        self.assertEqual((same.kind, same.result), (identity.JOINED, f"already stored as {chart}"))
        self.assertNotEqual(examine("https://example.com/chart-new", b"\x89PNG two").kind, identity.JOINED)

        [unreadable] = self.add("https://example.com/gone")
        self.assertEqual((unreadable.kind, unreadable.result), (identity.UNREADABLE, "unreadable: error"))
        self.assertEqual(self.rows("SELECT count(*) FROM sources"), [(1,)])
