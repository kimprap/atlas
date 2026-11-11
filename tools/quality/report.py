"""The report of a comparison (spec 4.15, ticket 13 section 3).

Each measure is a difference (candidate minus base) with a 95% paired-bootstrap interval, marked
better, level or worse; nothing is decided in code, and cost and time per item are shown beside it. Only a measure
with a user sample can be marked unreliable (more than 2 in 10 of the user's labels disagree with
Jev): the summary lane's faithfulness flags and the search lane's Jev grades. Completeness,
conciseness, the planted-instruction Jev check and the answers lane's support flags have no sample
and are always reported "not spot-checked". The answers lane's user labels are reported as
agreement with the model's labels, not as a Jev measure.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from tools.quality import evaldb, stats
from tools.quality.lanes import STATED, SUPPORT_LIMIT, mean_by_case
from tools.quality.spot import kind_of

NOT_SPOT_CHECKED = "not spot-checked"
# measure -> (label, direction: +1 higher is better, -1 lower is better, 0 informs only, kind)
# kind: sampled (a Jev measure with a user sample), unsampled (a Jev measure with none), code
MEASURES: dict[str, tuple[tuple[str, int, str], ...]] = {
    "summary": (
        ("completeness", 1, "unsampled"),
        ("faithfulness", 1, "sampled"),
        ("conciseness", 1, "unsampled"),
        ("planted_code", -1, "code"),
        ("planted_jev", -1, "unsampled"),
        ("summary_failed", -1, "code"),
        ("dropped_claims", -1, "code"),
        ("escalated", -1, "code"),
        ("rethink_corrections", 0, "code"),
        ("model_turns", 0, "code"),
        ("claims_changed", 0, "code"),
        ("seconds", -1, "code"),
        ("cost_usd", -1, "code"),
    ),
    "search": (
        ("ndcg10", 1, "sampled"),
        ("mrr", 1, "code"),
        ("recall", 1, "code"),
        ("recall_wide", 1, "code"),
        ("seconds", -1, "code"),
        ("cost_usd", -1, "code"),
    ),
    "answers": (
        ("backing_match", 1, "code"),
        ("labels_checked", 1, "code"),
        ("answer_support", 1, "unsampled"),
        ("answer_failed", -1, "code"),
        ("seconds", -1, "code"),
        ("cost_usd", -1, "code"),
    ),
}
SAMPLED_FOR = {"summary": "faith", "search": "grade"}


def _load(db: sqlite3.Connection, comparison: str) -> dict[str, Any]:
    row = db.execute("SELECT lane, base_runs, cand_runs, spot_status FROM comparisons WHERE id = ?", (comparison,)).fetchone()
    if row is None:
        raise ValueError(f"no comparison {comparison}")
    base, cand = json.loads(row[1]), json.loads(row[2])
    runs = {r[0]: r for r in db.execute(f"SELECT id, label, ref, overrides, cost_usd FROM runs WHERE id IN ({','.join('?' * len(base + cand))})", base + cand)}
    return {"lane": row[0], "base": base, "cand": cand, "status": row[3], "runs": runs}


def disagreements(db: sqlite3.Connection, comparison: str, lane: str, runs: Sequence[int]) -> tuple[int, int]:
    """``(disagreeing, labelled)``: the user's labels against Jev's answer for the lane's sampled measure."""
    prefix = SAMPLED_FOR.get(lane)
    if prefix is None:
        return 0, 0
    p_of = {item: p for _, item, _, p, _ in evaldb.judgments(db, runs) if item.startswith(prefix + ":")}
    rows = db.execute("SELECT item, user_label FROM spot WHERE comparison_id = ? AND user_label IS NOT NULL", (comparison,)).fetchall()
    bad = labelled = 0
    for item, label in rows:
        if kind_of(item) != prefix or item not in p_of or p_of[item] is None:
            continue
        labelled += 1
        p = p_of[item]
        if prefix == "faith":
            bad += (p < SUPPORT_LIMIT) == (label == "supported")
        else:
            bad += (p >= STATED) != (label == "helps")
    return bad, labelled


def _sample_note(db: sqlite3.Connection, comparison: str, lane: str, runs: Sequence[int]) -> str:
    prefix = SAMPLED_FOR.get(lane)
    total = db.execute("SELECT count(*) FROM spot WHERE comparison_id = ? AND item LIKE ?", (comparison, f"{prefix}:%")).fetchone()[0] if prefix else 0
    bad, labelled = disagreements(db, comparison, lane, runs)
    if total == 0:
        return NOT_SPOT_CHECKED
    if labelled < total:
        return f"{NOT_SPOT_CHECKED} until the sample is labelled ({labelled} of {total})"
    if stats.unreliable(bad, labelled):
        return f"UNRELIABLE: you disagreed with Jev on {bad} of {labelled}"
    return f"spot-checked: you disagreed with Jev on {bad} of {labelled}"


def _spot_agreement(db: sqlite3.Connection, comparison: str, lane: str, runs: Sequence[int]) -> None:
    """Keep each run's agreement with Jev beside its measures, so drift in Jev's grading shows across runs."""
    prefix = SAMPLED_FOR.get(lane)
    if prefix is None:
        return
    for run in runs:
        bad, labelled = disagreements(db, comparison, lane, [run])
        if labelled:
            evaldb.set_measure(db, run, "*", "spot_agreement", (labelled - bad) / labelled)


def _answers_extras(db: sqlite3.Connection, comparison: str, base: Sequence[int], cand: Sequence[int]) -> list[str]:
    lines = []
    asked = {item: json.loads(q)["label"] for _, item, q, _, _ in evaldb.judgments(db, [*base, *cand]) if item.startswith("claim:")}
    rows = db.execute("SELECT item, user_label FROM spot WHERE comparison_id = ? AND user_label IS NOT NULL AND item LIKE 'claim:%'", (comparison,)).fetchall()
    scored = [(asked[item], label) for item, label in rows if asked.get(item)]
    if scored:
        lines.append(f"your labels agree with the model's on {sum(a == b for a, b in scored)} of {len(scored)} claims")
        for name in ("Doubtful", "Noise"):
            mine = [b for a, b in scored if a == name]
            lines.append(f"  model said {name}: you agreed on {sum(b == name for b in mine)} of {len(mine)}")
    tally = {"base": 0, "cand": 0, "level": 0}
    for item, label in db.execute("SELECT item, user_label FROM spot WHERE comparison_id = ? AND user_label IS NOT NULL AND item LIKE 'pair:%'", (comparison,)):
        flip = item.rsplit(":", 1)[1] == "1"
        tally["level" if label == "level" else ("cand" if (label == "first") == flip else "base")] += 1
    if sum(tally.values()):
        lines.append(f"side by side: base {tally['base']}, candidate {tally['cand']}, level {tally['level']}")
    return lines


def _rethink_rule(rows: Mapping[str, tuple[float, float, float, str]], base_on: bool) -> str:
    """The ``atlas-rethink`` rule fixed before the first run: it stays only if faithfulness or completeness is better
    and neither is worse, across the runs; level, mixed or worse removes it. ``rows`` hold candidate minus base."""
    verdicts = []
    for name in ("faithfulness", "completeness"):
        if name not in rows:
            return f"atlas-rethink rule: cannot be applied, {name} was not measured"
        verdicts.append(rows[name][3] if not base_on else {"better": "worse", "worse": "better"}.get(rows[name][3], "level"))
    if "worse" in verdicts:
        result = "removed (a measure is worse with it)"
    elif "better" in verdicts:
        result = "stays (faithfulness or completeness is better, neither is worse)"
    else:
        result = "removed (level)"
    return f"atlas-rethink rule: with it, faithfulness is {verdicts[0]} and completeness is {verdicts[1]}: {result}"


def build(db: sqlite3.Connection, comparison: str) -> str:
    found = _load(db, comparison)
    lane, base, cand, runs = found["lane"], found["base"], found["cand"], found["runs"]
    values = evaldb.measures(db, [*base, *cand])
    _spot_agreement(db, comparison, lane, [*base, *cand])
    lines = []
    for side, ids in (("base", base), ("cand", cand)):
        run = runs[ids[0]]
        overrides = json.loads(run[3])
        seen = [json.loads(q) for _, item, q, _, _ in evaldb.judgments(db, ids) if item.startswith("models:")]
        models = {}
        for entry in seen:
            for role, names in entry.items():
                models.setdefault(role, set()).update(names)
        shown = ", ".join(f"{role}={'/'.join(sorted(names))}" for role, names in sorted(models.items())) or "none recorded"
        lines.append(f"{side}: {run[2][:12]} {' '.join(f'{k}={v}' for k, v in overrides.items()) or '(no overrides)'}; {len(ids)} run(s); models seen: {shown}")
    lines.insert(0, f"comparison {comparison}: {lane} lane, spot check: {found['status']}")
    lines.append("measure | base | candidate | difference [95% interval] | verdict | spot check")
    results: dict[str, tuple[float, float, float, str]] = {}
    for measure, direction, kind in MEASURES[lane]:
        base_mean, cand_mean = mean_by_case(values, base, measure), mean_by_case(values, cand, measure)
        shared = sorted(set(base_mean) & set(cand_mean))
        if not shared:
            continue
        pairs = [(base_mean[case], cand_mean[case]) for case in shared]
        diff, low, high = stats.bootstrap(pairs, comparison)
        mark = stats.verdict(low, high, direction >= 0) if direction else "informs only"
        results[measure] = (diff, low, high, mark)
        note = {"code": "", "unsampled": NOT_SPOT_CHECKED, "sampled": _sample_note(db, comparison, lane, [*base, *cand])}[kind]
        lines.append(
            f"{measure} | {sum(b for b, _ in pairs) / len(pairs):.3f} | {sum(c for _, c in pairs) / len(pairs):.3f} | "
            f"{diff:+.3f} [{low:+.3f}, {high:+.3f}] over {len(pairs)} cases | {mark} | {note}"
        )
    if lane == "summary":
        base_overrides, cand_overrides = json.loads(runs[base[0]][3]), json.loads(runs[cand[0]][3])
        on = lambda o: o.get("rethink", "true") != "false"  # noqa: E731
        if on(base_overrides) != on(cand_overrides):
            lines.append(_rethink_rule(results, on(base_overrides)))
        else:
            lines.append("atlas-rethink rule: not applied, this comparison does not turn rethink on or off")
    if lane == "answers":
        lines += _answers_extras(db, comparison, base, cand)
    lines.append("tie-break: level quality, the cheaper version wins; the user decides")
    return "\n".join(lines)
