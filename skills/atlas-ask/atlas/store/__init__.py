"""The store interface core uses; ``atlas.store.sqlite`` implements it.

One store per profile. Core opens it through ``Host.open_store(path)`` and never
imports the SQLite adapter.
"""

from __future__ import annotations

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


class Store(Protocol):
    path: Path

    def size(self) -> int:
        """Bytes on disk of the store file."""
        ...

    def close(self) -> None: ...
