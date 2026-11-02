Type: prototype
Parent: [Atlas v2](../map.md)
Blocked by: 08
Status: claimed

## Question

The map's standing decision on the Jev decision model (2026-10-29) makes Jev Atlas's default reranker only after test runs that compare it with Opus on quality, speed and cost. On the same 47 queries, the same BM25-with-rewriting top 30 and the same graded pool as [Prototype retrieval on real summaries](08-prototype-retrieval-on-real-summaries.md), how do these rerankers compare?

- Jev: one yes/no per query–candidate pair, sorted by probability; once on the same title plus 700 characters the Opus reranker saw, once on the whole v2 record.
- Opus listwise at `:medium` (the map's default effort, untested so far).
- Opus listwise at `:high` and Nemotron, from ticket 08's saved runs.

Quality: nDCG@10 on the pool, with new top-10 pairs graded by Jev as in ticket 08 and spot-checked by the user (the gate); plus two checks that do not use Jev as the grader, because Jev would otherwise grade its own reranking: the rank of each S query's source (Seed@10, MRR) and the user's six trading sources for R1. Speed: wall time per query. Cost: cost per query.

Also: does one Jev yes/no over the whole library ("is this source about the same area as the brief?") find the user's six trading sources that a top-10 search misses? This is evidence for ticket 06's "How topic creation gathers candidate sources wider than a top-10 search".

Disposable decision evidence for [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md); it decides nothing. The frozen v1 vault is read only.
