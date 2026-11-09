"""The OMP adapter against the real ``omp``, run only with ``ATLAS_LIVE=1``.

Live effects: three ``omp read`` fetches of public pages (each read once and
reused), GitHub's tree API for one repo, ``/v1/models`` and ``/v1/usage``
reads, and one small forced-tool call on a role the host already has (``tiny``
when set, else ``smol``, else ``default``).
"""

from __future__ import annotations

import os
import unittest
from functools import cache

from tests.contract import suite

from atlas import ports  # noqa: E402
from atlas.adapters.omp import OmpHost  # noqa: E402

LIVE = os.environ.get("ATLAS_LIVE") == "1"
SKIP = "live: set ATLAS_LIVE=1 to call the real omp"


@cache
def _omp() -> OmpHost:
    return OmpHost()


@cache
def _read(link: str) -> ports.Page | ports.Unreadable:
    return _omp().read(link)


@cache
def _role() -> str:
    roles = _omp().roles()
    return next(role for role in ("tiny", "smol", "default") if role in roles)


class _OnceRead:
    def read(self, link: str, scope: ports.Scope = None) -> ports.Page | ports.Unreadable:
        return _read(link)


@unittest.skipUnless(LIVE, SKIP)
class LiveRead(suite.ReadContract, unittest.TestCase):
    REDIRECT_LINK = "https://python.org/"
    REDIRECTED_TO = "https://www.python.org/"
    REPO_LINK = "https://github.com/anthropics/skills"
    GONE_LINK = "https://example.com/atlas-no-such-page-404"
    GONE_REASON = "gone"
    PAGE_LINKS = (REDIRECT_LINK, REPO_LINK)

    def make_read(self) -> ports.ReadPort:
        return _OnceRead()


@unittest.skipUnless(LIVE, SKIP)
class LiveCall(suite.CallContract, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.TOOL_ROLE = _role()

    def make_call(self) -> ports.CallPort:
        return _omp()


@unittest.skipUnless(LIVE, SKIP)
class LiveQuota(suite.QuotaContract, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.PROVIDER = _omp().role_provider(_role())

    def make_quota(self) -> ports.QuotaPort:
        return _omp()


@unittest.skipUnless(LIVE, SKIP)
class LiveFacts(suite.FactsContract, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.KNOWN_ROLE = _role()

    def make_facts(self) -> ports.HostFacts:
        return _omp()


if __name__ == "__main__":
    unittest.main()
