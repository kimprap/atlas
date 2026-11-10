#!/usr/bin/env python3
"""Near-copy calibration on v1's known duplicate pairs (repo-only; never shipped).

  near_copy.py --vault <v1 instance folder>

Reads the frozen v1 vault (read only): every source artifact's front matter
under summaries/sources/ (run logs left out). Its known duplicates are the
content-hash pairs (two artifacts with the same ``content_hash:`` line) and the
title pairs (artifacts with the same ``title:`` line). Both links of each pair
are read through the read port (the OMP adapter, up to 4 reads at once; each
link once) and the share between their texts comes from core's identity code,
the same normalization and shingles ``add`` uses.

Prints one line per pair: ``hash`` or ``title "<title>"``, then the share or
``unreadable``, then the links. A title shared by more than two links prints one
line with the link count and the highest share among its pairs that are not
already a content-hash pair. It makes no model call and writes no store or file.
Spec 4.9 turns the table into keep-or-change for the 90% ``near_copy`` default.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills" / "atlas-ask"))

from atlas import ports  # noqa: E402
from atlas.adapters.omp import OmpHost  # noqa: E402
from atlas.core import identity  # noqa: E402

READERS = 4


def front_matter(path: Path) -> dict[str, str]:
    """The ``key: value`` lines of one artifact's front matter, values as written."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    fields: dict[str, str] = {}
    for line in text[4:].split("\n---", 1)[0].splitlines():
        key, colon, value = line.partition(":")
        if colon and key and not key.startswith(" "):
            fields[key] = value.strip()
    return fields


def groups(artifacts: Sequence[Mapping[str, str]], key: str) -> list[tuple[str, list[str]]]:
    """Each value of ``key`` held by 2 or more artifacts, with their links, in value order."""
    found: dict[str, list[str]] = {}
    for fields in artifacts:
        value = fields.get(key)
        link = fields.get("canonical_url", "").strip('"')
        if value and link:
            found.setdefault(value, []).append(link)
    return sorted((value, links) for value, links in found.items() if len(links) > 1)


def read_all(links: Sequence[str]) -> dict[str, frozenset[str] | str]:
    """Each link's shingles, or why it is unreadable."""
    host = OmpHost()

    def read(link: str) -> frozenset[str] | str:
        answer = host.read(link)
        if isinstance(answer, ports.Unreadable):
            return f"{answer.reason}: {answer.detail}"
        return identity.shingles(identity.normalize(answer.text))

    with ThreadPoolExecutor(READERS) as pool:
        return dict(zip(links, pool.map(read, links)))


def share_of(texts: Mapping[str, frozenset[str] | str], first: str, second: str) -> float | None:
    a, b = texts[first], texts[second]
    if isinstance(a, str) or isinstance(b, str):
        return None
    return identity.share(a, b)


def shown(value: float | None) -> str:
    return "unreadable" if value is None else f"{value:.3f}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print each v1 duplicate pair's near-copy share.")
    parser.add_argument("--vault", required=True, type=Path, help="the v1 instance folder (read only)")
    args = parser.parse_args(argv)
    sources = args.vault.expanduser() / "summaries" / "sources"
    if not sources.is_dir():
        print(f"no summaries/sources folder under {args.vault}", file=sys.stderr)
        return 2
    artifacts = [front_matter(path) for path in sorted(sources.rglob("*.md")) if "runs" not in path.relative_to(sources).parts]
    hash_pairs = groups(artifacts, "content_hash")
    title_groups = groups(artifacts, "title")
    links = sorted({link for _, members in hash_pairs + title_groups for link in members})
    texts = read_all(links)

    unreadable = {link: why for link, why in texts.items() if isinstance(why, str)}
    known = {frozenset(pair) for _, members in hash_pairs for pair in combinations(members, 2)}
    for _, members in hash_pairs:
        print(f"hash  {shown(share_of(texts, *members[:2]))}  {'  '.join(members)}")
    for title, members in title_groups:
        if len(members) == 2:
            print(f"title {title}  {shown(share_of(texts, *members))}  {'  '.join(members)}")
            continue
        scored = [
            (value, pair)
            for pair in combinations(members, 2)
            if frozenset(pair) not in known and (value := share_of(texts, *pair)) is not None
        ]
        if scored:
            value, pair = max(scored)
            print(f"title {title}  {len(members)} links, highest share {shown(value)}  {'  '.join(pair)}")
        else:
            print(f"title {title}  {len(members)} links, unreadable")
    for link, why in sorted(unreadable.items()):
        print(f"  unreadable {link}: {why}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
