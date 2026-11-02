# Ticket 11 results: Jev reranking on real v1 summaries

Run on 2026-11-02 on g10. Disposable decision evidence for [Decide Atlas v2 architecture](../../issues/06-decide-atlas-v2-architecture.md); it decides nothing. Every score below is recomputed from the saved files by `python3 score.py` (no API calls).

## Setup

- **Same as ticket 08:** all 673 frozen v1 summaries (`~/dev/atlas-v1-vault`, read only), the 47 queries, the graded pool, and the candidate list for every reranker: the BM25 top 30 over the v2 record after agent query rewriting (`bm25_v2_rw`). Rebuilt candidates match ticket 08's saved top 10 on 47 of 47 queries, and ticket 08's scores reproduce exactly (0.903, 0.861, 0.740).
- **Rerankers:**
  - `jev_short`: Jev (`typesafe/jev-1.14-20261014` via `~typesafe/jev-latest`), one yes/no per query–candidate pair on the same text the Opus reranker saw (title plus the first 700 characters of v2), sorted by P(yes).
  - `jev_full`: the same on the whole v2 record.
  - `opus_medium`: one listwise call to `claude-opus-5-5:medium` (omp role `smol`) on the title plus 700 characters. New prompt, in `prompts.json`.
  - `opus_high` and `nemotron`: ticket 08's saved runs. Ticket 08's `:high` prompt was not saved, so `opus_medium` vs `opus_high` mixes effort and prompt.
- **Grading:** the ticket 08 pool, plus 49 new top-10 pairs (30 from `jev_short`, 27 from `jev_full`, 13 from `opus_medium`, overlapping) graded 0/1/2 by Jev with a new prompt. Ticket 08's grading prompt was not saved; the new prompt re-graded 80 random pool pairs and agreed exactly on 73 and within one level on 80 (the 7 differences are one level higher). The user's six R1 trading sources count as 2.
- **Checks that do not use Jev as the grader:** the rank of each S query's own source (Seed MRR, rank 1), and how many of the user's six R1 sources reach the top 10.

## Results

| Method | nDCG@10 all | Recall@10 all | nDCG@10 real (R) | Seed MRR | Seed at rank 1 | R1 six in top 10 |
| - | - | - | - | - | - | - |
| bm25_v2_rw (no rerank) | 0.740 | 0.640 | 0.689 | 0.727 | 20/34 | 3/6 |
| opus_high (ticket 08) | 0.902 | 0.755 | 0.843 | 0.919 | 29/34 | 3/6 |
| opus_medium | 0.901 | 0.750 | 0.852 | 0.934 | 30/34 | 3/6 |
| jev_short | 0.925 | 0.776 | 0.892 | 0.903 | 29/34 | 4/6 |
| jev_full | 0.936 | 0.793 | 0.879 | 0.869 | 27/34 | 4/6 |
| nemotron (ticket 08) | 0.860 | 0.719 | 0.808 | 0.873 | 27/34 | 4/6 |

`opus_high` reads 0.902 here, not 0.903, because the 49 new grades widen the ideal ranking for some queries.

Paired bootstrap over queries (10,000 resamples):

| Comparison | Metric | Difference | 95% CI |
| - | - | - | - |
| jev_full vs opus_medium | nDCG@10 | +0.034 | +0.019 to +0.050 |
| jev_full vs opus_medium | Seed MRR | -0.065 | -0.143 to +0.006 |
| jev_short vs opus_medium | nDCG@10 | +0.024 | +0.012 to +0.037 |
| jev_short vs opus_medium | Seed MRR | -0.031 | -0.095 to +0.025 |
| opus_medium vs opus_high (ticket 08) | nDCG@10 | -0.000 | -0.008 to +0.007 |
| opus_medium vs opus_high (ticket 08) | Seed MRR | +0.015 | +0.000 to +0.044 |
| jev_full vs jev_short | nDCG@10 | +0.010 | -0.002 to +0.023 |
| jev_full vs nemotron (ticket 08) | nDCG@10 | +0.076 | +0.056 to +0.097 |

`score.py` prints the full set, including both Jev variants against `opus_high`.

Speed and cost per query, measured on 10 queries one at a time (Jev with a per-run nonce so no cached answer counts):

| Reranker | Wall time, median (min–max) | Cost per query |
| - | - | - |
| jev_short (30 parallel calls) | 2.15 s (0.59–2.75) | $0.0007, measured |
| jev_full (30 parallel calls) | 2.68 s (1.47–2.83) | $0.0012, measured |
| opus_medium (one call) | 4.69 s (4.45–5.67) | about $0.04–0.07 [INFERENCE: about 5.7k input tokens at assumed list prices of $5/M input and $25/M output; not metered separately] |

Repeat stability: an identical second `jev_short` run moved P(yes) by 0.011 on average (max 0.16).

## Library-wide screen for topic creation (R1, trading)

One Jev yes/no per source over all 673 summaries ("is this source about the same area as the brief?", whole v2 record): $0.027, 10.6 s.

- The user's six trading sources rank 1, 2, 7, 11, 14 and 17 of 673.
- 20 sources reach P(yes) ≥ 0.5, and all six are among them; at ≥ 0.3, 35 sources; at ≥ 0.2, 61 sources.
- For comparison, at most four of the six reach any reranker's top 10, and one (`6fb00c7ac55e`) is not even in the BM25 top 30.

## Findings

1. **Judged by Jev, Jev reranks best:** +0.024 to +0.034 nDCG@10 over Opus, and +0.076 over Nemotron. This is the shared-family case the map's standing decision warns about: Jev grades its own choices, and 49 of its top-10 picks were graded only by Jev.
2. **Judged without Jev, Opus is level or ahead:** Opus `:medium` puts the S query's own source higher (Seed MRR 0.934 vs 0.903 short and 0.869 full; the intervals touch zero). Jev gets one more of the six trading sources into the top 10 (4 vs 3).
3. **Opus `:medium` matches `:high`:** nDCG difference 0.000 (−0.008 to +0.007); Seed MRR +0.015. The map's default effort is now tested.
4. **Jev reads the whole record no better than the short text.** Full v2 gains +0.010 nDCG (not significant) and loses Seed MRR.
5. **Jev is about 2× faster and 35–90× cheaper per search than Opus `:medium`** (2.2–2.7 s vs 4.7 s; about $0.001 vs about $0.04–0.07).
6. **A whole-library Jev screen finds a broad topic's sources that top-10 search misses:** all six trading sources in its top 17 of 673 for $0.03.

## Caveats

- **Self-grading:** see finding 1. The user's spot-check of the new grades is the gate.
- **Opus prompt:** `opus_medium` used a new prompt; ticket 08's `:high` prompt is lost.
- **One library, one domain:** 673 notes mostly about agents and design.
- **Latency** includes network time from g10 and omp's judge batching; Opus cost is estimated, not metered.

## Files

- [score.py](score.py): recomputes every table from the saved files.
- `candidates.json` (BM25-rw top 30 per query), `runs.json` (full orders for the three new rerankers), `jev-probs.json` (P(yes) per pair, including the repeat run), `grades-new.json` (49 new grades and the 80-pair calibration), `screen-r1.json`, `timing.json`, `prompts.json`, `spot-check.json`.

Disposal: keep this folder with ticket 08's until [Decide Atlas v2 architecture](../../issues/06-decide-atlas-v2-architecture.md) is resolved, then delete both. Nothing was installed. The OpenRouter key came from the session environment and is not stored here.
