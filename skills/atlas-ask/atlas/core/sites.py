"""The site table: one row per site whose links need more than the generic rules.

Each row names its hosts, cleans a link on them after ``links`` has applied the
generic rules, and says whether a cleaned link names a source that cannot
change. Rows: X (the ``twitter.com`` aliases, a numeric ``s``, handle case,
``/photo/N`` and ``/video/N``; a post cannot change), GitHub (owner and repo
case, ``ref``; a file or tree pinned to a commit cannot change) and YouTube
(``si``, ``feature``, the ``youtu.be`` short link). There is no ``www.`` or
http→https rule: redirects and the text joins catch those.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Query:
    """One query component: as written, and its name and value decoded."""

    raw: str
    name: str
    value: str


@dataclass(frozen=True)
class Parts:
    """A link after the generic rules; ``port`` is ``":<n>"`` for a non-default port, else empty."""

    scheme: str
    host: str
    port: str
    path: str
    query: tuple[Query, ...]

    def render(self) -> str:
        link = f"{self.scheme}://{self.host}{self.port}{self.path}"
        if self.query:
            link += "?" + "&".join(item.raw for item in self.query)
        return link


@dataclass(frozen=True)
class Site:
    name: str
    hosts: frozenset[str]
    clean: Callable[[Parts], Parts]
    unchangeable: Callable[[Parts], bool]


_DIGITS = re.compile(r"[0-9]+", re.ASCII)
_COMMIT = re.compile(r"[0-9a-fA-F]{40}", re.ASCII)


def _segments(path: str) -> list[str]:
    return path.split("/")[1:] if path.startswith("/") else []


def _drop(query: tuple[Query, ...], names: frozenset[str]) -> tuple[Query, ...]:
    return tuple(item for item in query if item.name not in names)


# X: x.com is the one host; s=<digits> is a share tracker; handles are case-blind;
# /photo/N and /video/N open one medium of the same post.
_X_STATUS = re.compile(r"/[^/]+/status/[0-9]+", re.ASCII)
_X_MEDIUM = re.compile(r"(/[^/]+/status/[0-9]+)/(?:photo|video)/[0-9]+", re.ASCII)


def _clean_x(parts: Parts) -> Parts:
    path = parts.path
    medium = _X_MEDIUM.fullmatch(path)
    if medium is not None:
        path = medium.group(1)
    segments = _segments(path)
    if segments and segments[0]:
        path = "/" + "/".join([segments[0].lower(), *segments[1:]])
    query = tuple(item for item in parts.query if not (item.name == "s" and _DIGITS.fullmatch(item.value)))
    return replace(parts, host="x.com", path=path, query=query)


def _x_post(parts: Parts) -> bool:
    return _X_STATUS.fullmatch(parts.path) is not None


# GitHub: owner and repo names are case-blind; ref= is a referral tracker.
def _clean_github(parts: Parts) -> Parts:
    segments = _segments(parts.path)
    path = parts.path
    if len(segments) >= 2 and segments[0] and segments[1]:
        path = "/" + "/".join([segments[0].lower(), segments[1].lower(), *segments[2:]])
    return replace(parts, path=path, query=_drop(parts.query, frozenset({"ref"})))


def _github_pinned(parts: Parts) -> bool:
    segments = _segments(parts.path)
    return (
        len(segments) >= 4
        and segments[2] in {"blob", "tree", "commit"}
        and _COMMIT.fullmatch(segments[3]) is not None
    )


# YouTube: si= and feature= are share trackers; youtu.be/<id> is watch?v=<id>,
# the link that short link redirects to.
_YOUTUBE_TRACKERS = frozenset({"si", "feature"})
_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]+", re.ASCII)


def _clean_youtube(parts: Parts) -> Parts:
    query = _drop(parts.query, _YOUTUBE_TRACKERS)
    segments = _segments(parts.path)
    if parts.host == "youtu.be" and len(segments) == 1 and _VIDEO_ID.fullmatch(segments[0]):
        video = Query(f"v={segments[0]}", "v", segments[0])
        return replace(parts, host="www.youtube.com", path="/watch", query=(video, *query))
    return replace(parts, query=query)


def _never(parts: Parts) -> bool:
    return False


SITES: tuple[Site, ...] = (
    Site("x", frozenset({"x.com", "www.x.com", "twitter.com", "www.twitter.com"}), _clean_x, _x_post),
    Site("github", frozenset({"github.com"}), _clean_github, _github_pinned),
    Site(
        "youtube",
        frozenset({"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}),
        _clean_youtube,
        _never,
    ),
)


def site_for(host: str) -> Site | None:
    """The row whose hosts include ``host``, else ``None``."""
    for site in SITES:
        if host in site.hosts:
            return site
    return None


def clean(parts: Parts) -> Parts:
    """``parts`` after its site's row, unchanged on a host no row names."""
    site = site_for(parts.host)
    return parts if site is None else site.clean(parts)


def unchangeable(link: str) -> bool:
    """Whether the cleaned ``link`` names a source that cannot change (an X post, a pinned GitHub file)."""
    split = urlsplit(link)
    site = site_for(split.hostname or "")
    if site is None:
        return False
    return site.unchangeable(Parts(split.scheme, split.hostname or "", "", split.path, ()))
