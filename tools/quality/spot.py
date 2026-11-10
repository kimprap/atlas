"""Spot checks: the user's blind samples of a comparison (spec 4.15, ticket 13 section 7).

Samples are drawn when a comparison finishes, seeded by its id, and stored as ``spot`` rows
with no label. ``spot <comparison>`` prints the next unlabelled item as JSON (what is shown never
includes Jev's flag or the model's label) and ``--answer <item> <label>`` records the user's label.

- Summary lane: 20 claims per comparison drawn across the candidate's runs, half flagged by
  Jev and half not (all the flagged ones when there are fewer); label ``supported`` or ``unsupported``.
- Search lane: 10 new Jev grades per run; label ``helps`` or ``not_helps``.
- Answers lane: 30 claims per run, labelled ``Sound``, ``Doubtful`` or ``Noise`` before the user sees the
  model's label; and for each question both versions' answers side by side, unlabelled, as ``first``,
  ``second`` or ``level``.
- ``spot keypoints`` is the one review of the 30 pages' key points: ``--answer <case> keep`` or
  ``--answer <case> drop:<ord>[,<ord>]``.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from typing import Any

from tools.quality import evaldb, stats
from tools.quality.lanes import SEPARATOR, SUPPORT_LIMIT

SAMPLES = {"summary": 20, "search": 10, "answers": 30}
LABELS = {
    "faith": ("supported", "unsupported"),
    "grade": ("helps", "not_helps"),
    "claim": ("Sound", "Doubtful", "Noise"),
    "pair": ("first", "second", "level"),
}
KEY_POINTS = "keypoints"


def _items(db: sqlite3.Connection, runs: Sequence[int], prefix: str) -> list[tuple[str, float | None, str]]:
    return [(item, p, question) for _, item, question, p, _ in evaldb.judgments(db, runs) if item.startswith(prefix + ":")]


def materialize(db: sqlite3.Connection, comparison: str, lane: str, base_runs: Sequence[int], cand_runs: Sequence[int]) -> int:
    """Draw the comparison's samples and store them unlabelled; returns how many items there are."""
    shown: dict[str, str] = {}
    if lane == "summary":
        rows = _items(db, cand_runs, "faith")
        flagged = [item for item, p, _ in rows if p is not None and p < SUPPORT_LIMIT]
        plain = [item for item, p, _ in rows if p is not None and p >= SUPPORT_LIMIT]
        chosen = stats.half_flagged(flagged, plain, SAMPLES[lane], comparison)
        shown = {item: question.split(SEPARATOR)[0] for item, _, question in rows if item in chosen}
    elif lane == "search":
        for run in [*base_runs, *cand_runs]:
            rows = _items(db, [run], "grade")
            chosen = stats.sample([item for item, _, _ in rows], SAMPLES[lane], f"{comparison}:{run}")
            shown.update({item: question.split(SEPARATOR)[0] for item, _, question in rows if item in chosen})
    else:
        for run in [*base_runs, *cand_runs]:
            rows = _items(db, [run], "claim")
            chosen = stats.sample([item for item, _, _ in rows], SAMPLES[lane], f"{comparison}:{run}")
            for item, _, question in rows:
                if item in chosen:
                    claim = json.loads(question)
                    shown[item] = json.dumps({key: claim[key] for key in ("claim", "sources", "backing")}, ensure_ascii=False)
        answers = {item.split(":", 2)[2]: question for item, _, question in _items(db, [base_runs[0]], "answer")} if base_runs else {}
        theirs = {item.split(":", 2)[2]: question for item, _, question in _items(db, [cand_runs[0]], "answer")} if cand_runs else {}
        for case in sorted(set(answers) & set(theirs)):
            flip = stats.rng(f"{comparison}:{case}").random() < 0.5
            first, second = (theirs[case], answers[case]) if flip else (answers[case], theirs[case])
            shown[f"pair:{case}:{int(flip)}"] = json.dumps({"first": json.loads(first), "second": json.loads(second)}, ensure_ascii=False)
    with evaldb.transaction(db):
        for item, text in sorted(shown.items()):
            db.execute("INSERT OR IGNORE INTO spot (comparison_id, item, shown, user_label, at) VALUES (?, ?, ?, NULL, NULL)", (comparison, item, text))
        _status(db, comparison)
    return len(shown)


def _status(db: sqlite3.Connection, comparison: str) -> str:
    total, labelled = db.execute("SELECT count(*), count(user_label) FROM spot WHERE comparison_id = ?", (comparison,)).fetchone()
    status = "no sample" if total == 0 else "complete" if labelled == total else f"{labelled} of {total} labelled"
    db.execute("UPDATE comparisons SET spot_status = ? WHERE id = ?", (status, comparison))
    return status


def kind_of(item: str) -> str:
    return item.split(":", 1)[0]


def next_item(db: sqlite3.Connection, comparison: str) -> dict[str, Any]:
    """The next unlabelled item of the comparison as the user is shown it, or ``{"done": true}``."""
    row = db.execute(
        "SELECT item, shown FROM spot WHERE comparison_id = ? AND user_label IS NULL ORDER BY rowid LIMIT 1", (comparison,)
    ).fetchone()
    if row is None:
        return {"comparison": comparison, "done": True}
    remaining = db.execute("SELECT count(*) FROM spot WHERE comparison_id = ? AND user_label IS NULL", (comparison,)).fetchone()[0]
    kind = kind_of(row[0])
    try:
        shown: Any = json.loads(row[1])
    except json.JSONDecodeError:
        shown = row[1]
    return {"comparison": comparison, "item": row[0], "shown": shown, "labels": list(LABELS[kind]), "remaining": remaining}


def answer(db: sqlite3.Connection, comparison: str, item: str, label: str, at: str) -> str:
    """Record the user's label for ``item``; returns the comparison's spot status."""
    row = db.execute("SELECT item FROM spot WHERE comparison_id = ? AND item = ?", (comparison, item)).fetchone()
    if row is None:
        raise ValueError(f"{comparison} has no spot item {item}")
    allowed = LABELS[kind_of(item)]
    if label not in allowed:
        raise ValueError(f"the label of {item} is one of {', '.join(allowed)}, not {label}")
    with evaldb.transaction(db):
        db.execute("UPDATE spot SET user_label = ?, at = ? WHERE comparison_id = ? AND item = ?", (label, at, comparison, item))
        return _status(db, comparison)


def next_key_points(db: sqlite3.Connection) -> dict[str, Any]:
    """The next page whose key points the user has not reviewed, or ``{"done": true}``."""
    row = db.execute(
        "SELECT c.id, c.link FROM cases c WHERE EXISTS (SELECT 1 FROM key_points k WHERE k.case_id = c.id AND k.reviewed_at IS NULL) ORDER BY c.id LIMIT 1"
    ).fetchone()
    if row is None:
        return {"comparison": KEY_POINTS, "done": True}
    points = db.execute("SELECT ord, text, quote FROM key_points WHERE case_id = ? ORDER BY ord", (row[0],)).fetchall()
    shown = {"page": row[1], "points": [{"ord": o, "text": t, "quote": q} for o, t, q in points]}
    left = db.execute("SELECT count(DISTINCT case_id) FROM key_points WHERE reviewed_at IS NULL").fetchone()[0]
    return {"comparison": KEY_POINTS, "item": row[0], "shown": shown, "labels": ["keep", "drop:<ord>[,<ord>]"], "remaining": left}


def answer_key_points(db: sqlite3.Connection, case_id: str, label: str, at: str) -> None:
    """``keep`` marks the page's key points reviewed; ``drop:<ord>,...`` removes those points first."""
    count = db.execute("SELECT count(*) FROM key_points WHERE case_id = ? AND reviewed_at IS NULL", (case_id,)).fetchone()[0]
    if count == 0:
        raise ValueError(f"{case_id} has no key points waiting for review")
    drops: list[int] = []
    if label != "keep":
        head, _, rest = label.partition(":")
        if head != "drop" or not rest or not all(part.strip().isdigit() for part in rest.split(",")):
            raise ValueError("the label of a page's key points is keep or drop:<ord>[,<ord>]")
        drops = [int(part) for part in rest.split(",")]
    with evaldb.transaction(db):
        for ord in drops:
            db.execute("DELETE FROM key_points WHERE case_id = ? AND ord = ?", (case_id, ord))
        remaining = db.execute("SELECT count(*) FROM key_points WHERE case_id = ?", (case_id,)).fetchone()[0]
        if remaining == 0:
            raise ValueError(f"dropping those points would leave {case_id} with none")
        db.execute("UPDATE key_points SET reviewed_at = ? WHERE case_id = ?", (at, case_id))
