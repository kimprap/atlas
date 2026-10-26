# Ticket 08 results: retrieval on real v1 summaries

Run on 2026-10-19. Disposable decision evidence for [Decide Atlas v2 architecture](../../issues/06-decide-atlas-v2-architecture.md); it decides nothing.

## Setup

- **Corpus:** all 673 frozen v1 summaries in `~/dev/atlas/vault/instances/atlas` (read-only).
- **Text versions indexed:**
  - `v1`: the whole note as stored, including TL;DR, ratings, labels, routing notes and reuse cues.
  - `v2`: the claims-first record from ticket 02: title, author, publisher, kind, key points, approaches, evidence and caveats.
  - `v2c`: v2 plus the v1 reuse cues.
  - `v2t`: v2 plus the v1 TL;DR.
- **Queries:** 47 in [queries.md](queries.md), reviewed by the user before the run.
  - R1–R7 are real: the user's trading, SEO and agent-evals prompts word for word, the three v1 topic scopes, and the agent-skills "24 skills" question.
  - S01–S34 are agent-style questions written by an LLM, one per randomly picked source, with names and titles kept out.
  - B1–B6 are broad questions that several sources should answer.
- **Engines:**
  - BM25: SQLite 3.53.2 FTS5 with porter stemming; the query becomes stopword-filtered terms joined with OR.
  - Embeddings: `nvidia/nemotron-3-embed-1b:free` on OpenRouter (2048 dimensions, `query:`/`passage:` prefixes), searched exactly by cosine similarity.
  - Hybrid: RRF (k=60), or a 0.5/0.5 convex combination (`cc`) of min-max-normalised scores.
  - `rw`: the agent first rewrites the request into 1–3 short searches; their results are merged with RRF.
  - Rerankers re-order the top 30: `nvidia/llama-nemotron-rerank-vl-1b-v2:free` on OpenRouter (`nemo`), or a listwise LLM reranker using omp's default model on the title plus the first 700 characters of v2 (`llm`).
- **Grading:**
  - Each query's top 10 from every method, plus known answers, were pooled: 1,535 pairs.
  - An LLM grader graded each pair 0/1/2 (not / partly / highly relevant). The grader was omp's judge model (`typesafe/jev-1.14`), which is not the model behind the LLM reranker.
  - The user spot-checked 20 grades and agreed with all of them.
  - The user's own list of six relevant trading sources for R1 overrides the grader.
- **Metrics:**
  - nDCG@10 on the graded pool.
  - Recall@10 of "highly relevant" sources.
  - Seed@10 and MRR: whether, and how high, each S query's source came back.
  - Differences between methods are tested by a paired bootstrap over queries (95% CI).

## Results

| Method | nDCG@10 all | Recall@10 all | nDCG@10 real (R) | Seed@10 | Seed MRR |
| - | - | - | - | - | - |
| bm25_v2_rw+llm | 0.903 | 0.765 | 0.848 | 1.000 | 0.919 |
| hyb_v2_rw+llm | 0.902 | 0.745 | 0.838 | 1.000 | 0.904 |
| hyb_v2+nemo | 0.870 | 0.726 | 0.837 | 1.000 | 0.869 |
| hyb_v2_rw+nemo | 0.869 | 0.723 | 0.816 | 1.000 | 0.873 |
| bm25_v2_rw+nemo | 0.861 | 0.727 | 0.812 | 1.000 | 0.873 |
| hyb_rrf_v2t | 0.843 | 0.719 | 0.834 | 0.971 | 0.863 |
| hyb_rrf_v2c | 0.831 | 0.701 | 0.807 | 0.971 | 0.821 |
| hyb_cc_v2 | 0.830 | 0.687 | 0.815 | 0.971 | 0.846 |
| dense_v1 | 0.825 | 0.682 | 0.826 | 0.941 | 0.815 |
| hyb_rrf_v2 | 0.824 | 0.694 | 0.802 | 0.971 | 0.833 |
| dense_v2c | 0.818 | 0.664 | 0.792 | 0.912 | 0.821 |
| dense_v2t | 0.812 | 0.669 | 0.792 | 0.971 | 0.823 |
| hyb_rrf_v2_rw | 0.807 | 0.673 | 0.798 | 1.000 | 0.806 |
| dense_v2 | 0.801 | 0.644 | 0.786 | 0.971 | 0.812 |
| bm25_v2t | 0.766 | 0.642 | 0.677 | 0.971 | 0.862 |
| bm25_v2c | 0.754 | 0.648 | 0.667 | 0.971 | 0.812 |
| bm25_v1 | 0.752 | 0.636 | 0.634 | 0.971 | 0.839 |
| bm25_v2 | 0.752 | 0.629 | 0.675 | 0.941 | 0.791 |
| bm25_v2_rw | 0.740 | 0.647 | 0.692 | 1.000 | 0.727 |

Paired differences in nDCG@10 (mean, 95% CI, queries better/worse):

| Comparison | Δ | CI | Better / worse |
| - | - | - | - |
| hybrid (RRF) vs BM25, v2 | +0.072 | +0.040 to +0.107 | 30 / 15 |
| embeddings vs BM25, v2 | +0.049 | +0.003 to +0.099 | 29 / 15 |
| convex vs RRF fusion | +0.006 | −0.003 to +0.015 | 21 / 18 |
| query rewrite vs none, BM25 | −0.012 | −0.037 to +0.015 | 21 / 25 |
| Nemotron rerank on rewritten BM25 | +0.120 | +0.083 to +0.160 | 38 / 6 |
| Nemotron rerank on hybrid | +0.046 | +0.022 to +0.071 | 27 / 18 |
| LLM rerank vs Nemotron rerank (rewritten BM25) | +0.042 | +0.021 to +0.063 | 33 / 8 |
| hybrid vs BM25 under the LLM reranker | −0.001 | −0.017 to +0.014 | 19 / 21 |
| hybrid vs BM25 under the Nemotron reranker | +0.010 | −0.006 to +0.026 | 23 / 15 |
| reuse cues added, BM25 | +0.001 | −0.011 to +0.015 | 14 / 19 |
| reuse cues added, embeddings | +0.017 | +0.003 to +0.031 | 24 / 13 |
| reuse cues added, hybrid | +0.007 | −0.006 to +0.020 | 16 / 19 |
| TL;DR added, hybrid | +0.018 | +0.007 to +0.030 | 28 / 15 |
| TL;DR added, BM25 | +0.014 | +0.002 to +0.027 | 23 / 14 |
| v1 full note vs v2, BM25 | 0.000 | −0.022 to +0.022 | 24 / 20 |

Time added per query, measured on this Mac:

| Step | Time |
| - | - |
| BM25 (FTS5) | about 1 ms |
| Exact vector search over 673 notes | about 31 ms in pure Python |
| Query embedding (OpenRouter call) | about 0.8 s |
| Agent query rewrite (LLM call) | 1.8–3.9 s |
| Nemotron rerank of 30 (OpenRouter call) | about 1.45 s |
| LLM rerank of 30 (one sequential call) | 2.3–4.3 s |
| Embedding the whole corpus (free tier) | 65–87 s per text version |

The embedding and reranker calls cost $0 on the free tier. Grading cost $0.10.

## Findings

1. **A reranker gives the largest gain.** It adds +0.05 to +0.12 nDCG. The LLM reranker beats the Nemotron reranker by +0.04.
2. **Once results are reranked, embeddings add almost nothing.**
   - With the LLM reranker, BM25 with rewriting and hybrid with rewriting score the same: 0.903 and 0.902.
   - With the Nemotron reranker, hybrid leads BM25 by +0.01, which is not significant.
   - Without a reranker, hybrid beats BM25 by +0.07.
3. **Query rewriting does not improve BM25's ranking on its own,** but it brings every S query's source into the top 10 (seed@10 1.00 vs 0.94). It raises recall, and the reranker turns that into better ranking.
4. **Reuse cues hardly help.** BM25 and hybrid show no significant gain. Embeddings gain +0.017, which is less than adding the TL;DR (+0.018 for hybrid). This is the condition ticket 02 set for keeping reuse cues.
5. **A short TL;DR in the stored record helps search a little,** for both BM25 and hybrid. Ticket 02 dropped the TL;DR from the record; the gain is small but significant.
6. **Plain RRF is good enough.** The tuned-weight method (convex fusion) is not significantly better.
7. **No method found the user's whole idea of relevance on a broad topic (R1, trading).**
   - Of the six trading sources the user named, at most four reached any method's top 10.
   - AI-Trader ranked 48th at best. NOFX and the Bell Labs thread ranked 10th to 38th.
   - The LLM grader also rated four of the six as not relevant to the TradingView TA brief.
   - The user's relevance is "everything I have on this area"; the brief's literal content is narrower. A top-10 search under-collects for topic creation.

## Caveats

- **Pool bias:** sources that no method returned were never graded, so recall is relative to the pool. Absolute scores are optimistic; differences between methods are more reliable.
- **Lexical leakage:** the S queries were written from each source's key points, so wording may still overlap even with names removed. This flatters BM25.
- **Shared model family:** an LLM grades and an LLM reranks. They are different models, but they may share preferences. The user's spot-check (20 of 20 agreed) only partly offsets this.
- **Corpus scope:** 673 notes mostly about agents and design. Results may not hold for other domains, or at 10k notes.
- **Single configuration:** only one embedding model, one cross-encoder and one LLM reranker were tested. RRF k and the convex weight were not tuned.
- **Free tier:** OpenRouter free models have rate limits and no service guarantee. Latency includes network time.

## Files

- [proto.py](proto.py): loader, BM25, embeddings, fusion, rerank and metrics. The notebook-cell glue that ran it is not saved.
- [queries.json](queries.json) and [queries.md](queries.md), [rewrites.json](rewrites.json), [runs-top10.json](runs-top10.json), [grades.json](grades.json).
- `cache/` (126 MB): cached embeddings and reranker responses, so a rerun costs nothing.

Disposal: keep this folder until [Decide Atlas v2 architecture](../../issues/06-decide-atlas-v2-architecture.md) is resolved, then delete it. Nothing was installed. The API key was read from `~/.config/mise/.env` and is not stored here.
