"""The store interface core uses; ``atlas.store.sqlite`` implements it.

One store per profile. Core opens it through ``Host.open_store(path)`` and never
imports the SQLite adapter. Every method raises ``StoreFailed`` when the store
cannot do it. Times are UTC ISO-8601 text, so text order is time order.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

NEWER_THAN_CODE = "store is newer than this Atlas; check out a newer tag"


class StoreNewer(Exception):
    """The store's schema version is newer than this code can read."""

    def __init__(self, path: Path) -> None:
        super().__init__(f"{path}: {NEWER_THAN_CODE}")
        self.path = path


class StoreFailed(Exception):
    """The store could not be opened or used; ``detail`` says why in plain text."""

    def __init__(self, path: Path, detail: str) -> None:
        super().__init__(f"{path}: {detail}")
        self.path = path
        self.detail = detail


@dataclass(frozen=True)
class CallRecord:
    """One paid call: ``cost_usd`` is None exactly when ``cost_kind`` is ``unknown``."""

    at: str
    command: str
    role: str
    model: str
    thinking: str | None
    tokens_in: int
    tokens_out: int
    cache_read: int
    cache_write: int
    cost_usd: float | None
    cost_kind: str


@dataclass(frozen=True)
class ApprovalRecord:
    """One applied change and what let it run: ``by`` is ``request``, ``confirm`` or ``never``."""

    at: str
    command: str
    change_kind: str
    by: str
    words: str | None
    decision_id: str | None


class Store(Protocol):
    path: Path

    def size(self) -> int:
        """Bytes on disk of the store file."""
        ...

    def add_call(self, call: CallRecord) -> None:
        """Keep one paid call."""
        ...

    def calls_since(self, at: str) -> list[CallRecord]:
        """Every paid call at or after ``at``, oldest first."""
        ...

    def recent_calls(self, role: str, limit: int) -> list[CallRecord]:
        """The last ``limit`` calls of ``role``, newest first."""
        ...

    def models_not_billed(self, except_role: str) -> list[str]:
        """Each model with a call outside ``except_role`` whose cost is not billed, in name order."""
        ...

    def add_approval(self, approval: ApprovalRecord) -> None:
        """Keep one applied change's approval."""
        ...

    def close(self) -> None: ...
