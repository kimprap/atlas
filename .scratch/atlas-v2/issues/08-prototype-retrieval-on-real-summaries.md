Type: prototype
Parent: [Atlas v2 and portable skill plugins](../map.md)
Blocked by: 02
Status: resolved

## Question

On a sample of the frozen v1 summaries (`~/dev/atlas-v1-vault/instances/atlas`, read-only) and real agent-style queries, how well do keyword search (BM25), keyword plus embeddings, and keyword plus embeddings plus a reranker find the right sources? The prototype is disposable decision evidence for ticket 06; it fills the gap named in [Research label-free source retrieval](03-research-label-free-source-retrieval.md).

## Answer

Prototype run on 2026-10-19 with the user. The user approved the setup and picked the models (OpenRouter free tier: `nvidia/nemotron-3-embed-1b:free` for embeddings, `nvidia/llama-nemotron-rerank-vl-1b-v2:free` for reranking), reviewed the 47 queries before the run, and agreed with all 20 spot-checked grades. Full method, tables and caveats: [results](../prototypes/08-retrieval/results.md). This answer is evidence for [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md); it decides nothing.

**Setup:** all 673 v1 summaries; 47 queries (7 real, 34 agent-style with one target source each, 6 broad); 19 methods; 1,535 pooled pairs graded 0–2 by an LLM; nDCG@10 with a paired bootstrap.

**What the data shows:**

- **A reranker matters most:** +0.05 to +0.12 nDCG@10. The LLM reranker (0.903) beats Nemotron (0.861–0.870) by +0.04 (CI +0.02 to +0.06).
- **Once results are reranked, embeddings add almost nothing.**
  - With the LLM reranker, BM25 with query rewriting scores the same as hybrid (0.903 vs 0.902).
  - With Nemotron, hybrid leads by +0.01, which is not significant.
  - Without any reranker, hybrid beats BM25 by +0.07 (0.824 vs 0.752).
- **Query rewriting alone does not improve BM25's ranking (−0.01, n.s.),** but every target source reaches the top 10 (1.00 vs 0.94). The rewrite is useful as the feed for a reranker.
- **Plain RRF fusion is enough.** The 0.5/0.5 convex combination is +0.006, not significant.
- **Reuse cues (ticket 02's condition):** no significant gain for BM25 (+0.001) or hybrid (+0.007). Embeddings gain +0.017.
- **TL;DR (dropped from the v2 record):** small significant gains, +0.018 for hybrid and +0.014 for BM25.
- **v1 full note vs v2 claims-first record:** the same for BM25 (0.752 both). The extra v1 sections bring no search benefit beyond the TL;DR and cues effects above.
- **Broad topic creation under-collects (R1, trading).**
  - Of the six trading sources the user named, at most four reach any method's top 10. AI-Trader ranks 48th at best.
  - The LLM grader also rated four of the six as not relevant to the brief.
  - The user's sense of a topic's sources is wider than what is similar to the brief.
- **Time added per query:** BM25 about 1 ms; exact vector search about 31 ms (pure Python, 673 notes); query embedding about 0.8 s; rewrite 1.8–3.9 s; Nemotron rerank about 1.45 s; LLM rerank 2.3–4.3 s. Embedding the whole corpus takes about 65 s per text version on the free tier. All model calls cost $0, and grading cost $0.10.

**Caveats:**

- Recall is relative to the graded pool.
- The agent-style queries may share wording with their sources, which flatters BM25.
- The grader and the LLM reranker are different LLMs but may share preferences.
- Only one corpus in mostly two domains, and only one model per role.
- The free tier has rate limits and no service guarantee.

**Owned by [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md):**

- The retrieval stack.
- Whether vectors are stored at all.
- Which reranker to use, and its fallback.
- Whether the record keeps a TL;DR-style abstract or reuse cues.
- How topic creation gathers candidate sources beyond a top-10 search.

**Artifact:** `.scratch/atlas-v2/prototypes/08-retrieval/` (script, queries, rewrites, grades, top-10 lists, and a 126 MB response cache). Keep it until ticket 06 is resolved, then delete it. Nothing was installed.

Deleted on 2026-11-02 after ticket 06 was resolved; the results link points into git history.
