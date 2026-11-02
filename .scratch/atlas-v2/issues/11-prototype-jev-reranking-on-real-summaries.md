Type: prototype
Parent: [Atlas v2](../map.md)
Blocked by: 08
Status: resolved

## Question

The map's standing decision on the Jev decision model (2026-10-29) makes Jev Atlas's default reranker only after test runs that compare it with Opus on quality, speed and cost. On the same 47 queries, the same BM25-with-rewriting top 30 and the same graded pool as [Prototype retrieval on real summaries](08-prototype-retrieval-on-real-summaries.md), how do these rerankers compare?

- Jev: one yes/no per query–candidate pair, sorted by probability; once on the same title plus 700 characters the Opus reranker saw, once on the whole v2 record.
- Opus listwise at `:medium` (the map's default effort, untested so far).
- Opus listwise at `:high` and Nemotron, from ticket 08's saved runs.

Quality: nDCG@10 on the pool, with new top-10 pairs graded by Jev as in ticket 08 and spot-checked by the user (the gate); plus two checks that do not use Jev as the grader, because Jev would otherwise grade its own reranking: the rank of each S query's source (Seed@10, MRR) and the user's six trading sources for R1. Speed: wall time per query. Cost: cost per query.

Also: does one Jev yes/no over the whole library ("is this source about the same area as the brief?") find the user's six trading sources that a top-10 search misses? This is evidence for ticket 06's "How topic creation gathers candidate sources wider than a top-10 search".

Disposable decision evidence for [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md); it decides nothing. The frozen v1 vault is read only.

## Answer

Prototype run on 2026-11-02 on g10, under the route the user approved ("approve - note as well, on the new secrets rule i have just added into all repos. Atlas should also follow that"). Shown the results and 10 Jev grades on new top-10 pairs to spot-check, the user replied: "continue with redesign. no disagreements." Full method, tables and caveats: [results](../prototypes/11-jev-rerank/results.md); `score.py` recomputes every number from the saved files.

- No clear quality winner. Graded by Jev, Jev reranks best: nDCG@10 0.925 (short text) and 0.936 (whole record) vs 0.901 for Opus `:medium` (+0.024 and +0.034, both significant). Without Jev as the grader, Opus is level or ahead: the S query's own source ranks higher (Seed MRR 0.934 vs 0.903 and 0.869; intervals touch zero), while Jev puts one more of the user's six trading sources in the top 10 (4 vs 3).
- Opus `:medium` matches `:high` (nDCG difference 0.000, −0.008 to +0.007), so the map's default effort is tested.
- Jev is about 2× faster and 35–90× cheaper per search: 2.2–2.7 s and about $0.001, vs 4.7 s and about $0.04–0.07 [INFERENCE: Opus cost estimated from tokens].
- Reading the whole record does not help Jev rerank (+0.010 nDCG, not significant; lower Seed MRR).
- One Jev yes/no over the whole library finds a broad topic's sources that top-10 search misses: all six trading sources rank in the top 17 of 673, for $0.03 in 11 s.

This answer is evidence for [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md), which decides the default reranker and fallback, and how topic creation gathers candidates; it decides nothing.

The prototype folder was deleted on 2026-11-02 after ticket 06 was resolved; the results link points into git history.
