"""The composition root: the only module that picks adapters.

``build`` makes the ``Host`` one command runs on. ``ATLAS_HOST`` names the host;
``omp`` is the default and only value: the OMP adapter supplies read, call,
quota and the host facts, the Jev adapter the judge (none when the profile chose
Opus), and the SQLite store opens the profile's store. Building starts no
process and reads no key; each adapter does its work when core first asks.
"""

from __future__ import annotations

import os

from atlas import ports
from atlas.adapters.jev import JevJudge
from atlas.adapters.omp import OmpHost
from atlas.core import config
from atlas.store import sqlite

HOSTS = ("omp",)


class UnknownHost(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f'ATLAS_HOST is "{name}"; the hosts Atlas knows are {", ".join(HOSTS)}')
        self.name = name


def _judge_choice(profile: str | None) -> str | None:
    """The resolved profile's judge, or ``None`` when no profile resolves (core then stops first)."""
    try:
        return config.resolve(profile, os.environ.get("ATLAS_PROFILE")).judge
    except config.NotSetUp:
        return None


def build(profile: str | None) -> ports.Host:
    """The ``Host`` for one command; ``profile`` is the body's profile name, if any."""
    name = os.environ.get("ATLAS_HOST") or "omp"
    if name not in HOSTS:
        raise UnknownHost(name)
    omp = OmpHost()
    judge = None if _judge_choice(profile) == "opus" else JevJudge()
    return ports.Host(
        read=omp, call=omp, open_store=sqlite.open_store, judge=judge, quota=omp, facts=omp
    )
