"""The quality tool's counting: paired bootstrap, seeded spot samples, nDCG and the disagreement rule.

All of it is deterministic for a given seed, and the seed is always the comparison
id (spec 4.15), so a report can be recomputed.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Mapping, Sequence

RESAMPLES = 10_000
INTERVAL = 0.95
# More than 2 in 10 of the user's labels disagreeing with Jev marks its measures unreliable (ticket 13 item 7.3).
UNRELIABLE_SHARE = 0.2

BETTER, LEVEL, WORSE = "better", "level", "worse"


def rng(seed: str) -> random.Random:
    """A random generator seeded by ``seed`` (a comparison id), whatever the Python hash seed."""
    return random.Random(int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big"))


def bootstrap(pairs: Sequence[tuple[float, float]], seed: str, resamples: int = RESAMPLES) -> tuple[float, float, float]:
    """The mean ``candidate - base`` over ``pairs`` and its percentile interval from ``resamples`` paired resamples of the cases."""
    if not pairs:
        raise ValueError("a bootstrap needs at least one case")
    diffs = [cand - base for base, cand in pairs]
    generator = rng(seed)
    count = len(diffs)
    means = sorted(sum(generator.choices(diffs, k=count)) / count for _ in range(resamples))
    tail = (1 - INTERVAL) / 2
    low = means[int(tail * resamples)]
    high = means[min(resamples - 1, int((1 - tail) * resamples))]
    return sum(diffs) / count, low, high


def verdict(low: float, high: float, higher_is_better: bool = True) -> str:
    """``better`` or ``worse`` when the interval excludes 0, else ``level``."""
    if low > 0:
        return BETTER if higher_is_better else WORSE
    if high < 0:
        return WORSE if higher_is_better else BETTER
    return LEVEL


def sample(items: Sequence[str], count: int, seed: str) -> list[str]:
    """``count`` of ``items`` (all when fewer), drawn by the seed and listed in item order."""
    ordered = sorted(items)
    if len(ordered) <= count:
        return ordered
    return sorted(rng(seed).sample(ordered, count))


def half_flagged(flagged: Sequence[str], unflagged: Sequence[str], count: int, seed: str) -> list[str]:
    """``count`` claims, half flagged and half not; all the flagged ones when there are fewer than half.

    The flagged draw is ``count // 2`` of the flagged claims (all of them when fewer); the
    unflagged claims fill the rest.
    """
    chosen = sample(flagged, count // 2, seed + ":flagged")
    chosen += sample(unflagged, count - len(chosen), seed + ":unflagged")
    return sorted(chosen)


def unreliable(disagreements: int, labelled: int) -> bool:
    """Whether more than 2 in 10 of the labels disagree with Jev."""
    return labelled > 0 and disagreements / labelled > UNRELIABLE_SHARE


def ndcg_at(ranked: Sequence[str], grades: Mapping[str, int], k: int = 10) -> float:
    """nDCG@k of the ranked links against the graded pool ``grades`` (a link not in it counts 0); 0 when nothing is gradable."""

    def dcg(gains: Sequence[int]) -> float:
        return sum((2**gain - 1) / math.log2(rank + 2) for rank, gain in enumerate(gains))

    ideal = dcg(sorted(grades.values(), reverse=True)[:k])
    if ideal == 0:
        return 0.0
    return dcg([grades.get(link, 0) for link in ranked[:k]]) / ideal


def reciprocal_rank(ranked: Sequence[str], target: str, k: int = 10) -> float:
    for rank, link in enumerate(ranked[:k], 1):
        if link == target:
            return 1 / rank
    return 0.0


def recall(ranked: Sequence[str], wanted: Sequence[str], k: int = 10) -> float:
    """The share of the named source set found in the top ``k``."""
    return len(set(ranked[:k]) & set(wanted)) / len(set(wanted)) if wanted else 0.0

