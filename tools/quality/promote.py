"""``promote`` and ``promote-page``: the only two reads of a real profile (spec 4.15, ticket 13 section 1 item 4).

Both open the real store read only, copy what a case needs into the ``eval`` store as a ``cases`` row with
origin ``promoted``, and write nothing to the real profile.

- ``promote --from <profile> --query <id>``: one query record (its question, its phrasings) and the page text of the
  sources its Jev ranking listed, best first, at most 10.
- ``promote-page --from <profile> --link <link> --old-ref <date> --old-text <file>``: a changed page's old text, new text
  and old record (the claims with their quotes alive on ``<date>``). The store keeps one text per source, the new one, so
  the old text comes from the file the user names.
"""

from __future__ import annotations

import json
import sqlite3
import zlib
from pathlib import Path
from typing import Any

from tools.quality import _path, evaldb  # noqa: F401

from atlas.core import config, identity  # noqa: E402

PROMOTED_SOURCES = 10


class PromoteError(Exception):
    pass


def _real_store(name: str) -> Path:
    try:
        profile = config.resolve(name, None)
    except config.NotSetUp as err:
        raise PromoteError(f"profile {name} cannot be used: {err.what}") from None
    if not profile.store.exists():
        raise PromoteError(f"the store of profile {name} does not exist: {profile.store}")
    return profile.store


def _source(conn: sqlite3.Connection, key_link: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT s.id, s.key_link, s.title, s.author, s.publisher, s.published, s.kind, p.text FROM sources s"
        " JOIN page_text p ON p.source_id = s.id WHERE s.key_link = ? AND s.archived_at IS NULL",
        (key_link,),
    ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "link": row[1],
        "title": row[2],
        "author": row[3],
        "publisher": row[4],
        "published": row[5],
        "kind": row[6],
        "text": zlib.decompress(row[7]).decode("utf-8"),
    }


def promote(db: sqlite3.Connection, profile: str, query_id: int) -> str:
    """Copy one real query and its sources' page text into ``eval``; returns the new case's id."""
    path = _real_store(profile)
    with evaldb.readonly(path) as conn:
        row = conn.execute("SELECT original, question, phrasings, judge_records FROM queries WHERE id = ?", (query_id,)).fetchone()
        if row is None:
            raise PromoteError(f"profile {profile} has no query record {query_id}")
        original, question, phrasings, judged = row
        ranked = sorted(json.loads(judged) if judged else [], key=lambda entry: -entry["p"])[:PROMOTED_SOURCES]
        sources = []
        for entry in ranked:
            found = _source(conn, entry["link"])
            if found is not None:
                sources.append({key: found[key] for key in ("link", "title", "author", "publisher", "published", "kind", "text")})
    case_id = f"q:promoted:{profile}:{query_id}"
    payload = {
        "qid": f"promoted-{profile}-{query_id}",
        "origin": "promoted",
        "text": question,
        "original": original,
        "rewrites": json.loads(phrasings),
        "sources": sources,
    }
    with evaldb.transaction(db):
        if not evaldb.add_case(db, case_id, "search", "query", payload, None, "promoted"):
            raise PromoteError(f"{case_id} is already in eval")
    return case_id


def promote_page(db: sqlite3.Connection, profile: str, link: str, old_ref: str, old_text: Path) -> str:
    """Copy one changed page into ``eval``: old text, new text and the old record as of ``old_ref``."""
    try:
        old = old_text.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        raise PromoteError(f"the old text {old_text} cannot be read: {err}") from None
    path = _real_store(profile)
    cleaned = identity.clean(link)
    if cleaned is None:
        raise PromoteError(f"{link} is not a full http(s) link")
    with evaldb.readonly(path) as conn:
        found = conn.execute("SELECT s.key_link FROM links l JOIN sources s ON s.id = l.source_id WHERE l.link = ?", (cleaned,)).fetchone()
        source = _source(conn, found[0]) if found else None
        if source is None:
            raise PromoteError(f"profile {profile} holds no source for {link}")
        claims = conn.execute(
            "SELECT id, ord, section, text, basis FROM claims WHERE source_id = ? AND created_at <= ? AND (replaced_at IS NULL OR replaced_at > ?) ORDER BY ord",
            (source["id"], old_ref, old_ref),
        ).fetchall()
        if not claims:
            raise PromoteError(f"{link} had no claims on {old_ref}")
        old_record = [
            {
                "section": section,
                "text": text,
                "basis": basis,
                "quotes": [q[0] for q in conn.execute("SELECT text FROM quotes WHERE claim_id = ? ORDER BY ord", (claim_id,))],
            }
            for claim_id, _, section, text, basis in claims
        ]
    payload = {
        "kind": source["kind"],
        "title": source["title"],
        "old_ref": old_ref,
        "old_text": old,
        "new_text": source["text"],
        "old_record": old_record,
    }
    case_id = f"c:{profile}:{source['link']}:{old_ref}"
    with evaldb.transaction(db):
        if not evaldb.add_case(db, case_id, "summary", "changed", payload, source["link"], "promoted"):
            raise PromoteError(f"{case_id} is already in eval")
    return case_id
