# Research Evidence: where the Jev decision model could help Atlas v2

## Authority and scope
- Requesting owner: the dotfiles route `route-20261029-jev-top-picks`, which mapped TypeSafe's Jev cookbook onto the dotagents harness and Atlas v2. Receiver: the user, who continues this work from the Atlas repository. The user's direction and the decision it led to are in the map's standing decision on the Jev decision model, 2026-10-29 ([Atlas v2](../map.md)).
- Governing revisions: the map's standing decisions (Atlas models, 2026-10-19), tickets 02, 08 and 09, and the dotagents rule `rule://decision-model` (a decision model only ranks or flags; it never drops an item, makes a script check probabilistic, or decides whether a step runs).
- Bounded question: which Atlas v2 seams could use a decision model (Jev, omp's `judge` role), which uses the rule allows, and what each needs.
- Stop condition: every open v2 seam checked against the TypeSafe cookbook pages. Research only. This file makes no design decision.
- Access date for all sources: 2026-10-29. Copied from the route's reconciled research record and its Atlas scout report, which lived in a temporary folder.

## Sources
**S1. TypeSafe cookbook, Re-ranking.** https://docs.typesafe.ai/cookbooks/rerank_typesafe.md
- One yes/no per query–candidate pair over a BM25 top 30, sorted by probability: "top-1 accuracy from 5% to 18% and top-10 accuracy from 38% to 62%".

**S2. TypeSafe cookbook, Parallel questions.** https://docs.typesafe.ai/cookbooks/parallel_questions.md
- Batching questions into one request: "12.2x cheaper and 10.0x faster".

**S3. TypeSafe cookbook, Self-consistency: yes/no.** https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md
- Rerun items near the threshold.

**S4. TypeSafe cookbook, Double-checking citations.** https://docs.typesafe.ai/cookbooks/citation_check.md
- A string match marks a missing quote fabricated. One choice (supports / contradicts / says nothing) per surviving claim, with confidence ≥ 0.8 to auto-accept. All 4 planted failures were caught; accurate citations scored "0.93 or higher".

**S5. TypeSafe cookbook, Entity alignment.** https://docs.typesafe.ai/cookbooks/entity_alignment.md
- A 3-level score plus per-field yes/no questions. Of 450 pairs, 40 merged, 50 went to the curator and 360 stayed unlinked.

**S6. TypeSafe cookbook, Classifying RAG passages.** https://docs.typesafe.ai/cookbooks/classifying_rag_passages.md
- Four yes/no questions per passage with thresholds in code, including relevance and injection (0.99 on the planted page; "Nothing here is a security boundary").

**S7. TypeSafe cookbook, Line-by-line search.** https://docs.typesafe.ai/cookbooks/semantic_find.md
- A choice over IDs plus an `exists` yes/no.

**S8. TypeSafe cookbook, Intelliprompter.** https://docs.typesafe.ai/cookbooks/intelliprompter.md
- A score per (new claim, agreed conclusion) pair.

**S9. TypeSafe cookbook, Hierarchical classification.** https://docs.typesafe.ai/cookbooks/hierarchical_classification.md
- Beam search matched 4 of 4, greedy 2 of 4.

**S10. Local: [Prototype retrieval on real summaries](../issues/08-prototype-retrieval-on-real-summaries.md) and its [results](../prototypes/08-retrieval/results.md).**
- omp's judge model (`typesafe/jev-1.14`) graded the pooled 1,535 (query, summary) pairs 0/1/2 for $0.10; the user agreed with 20 of 20 spot checks.
- The grader rated 4 of the user's 6 trading sources as not relevant to the TradingView brief; the user's list overrides the grader.
- The listwise LLM reranker on the top 30 was the biggest gain and costs a paid call of about 2.3–4.3 s per search.

**S11. Local: the dotagents OMP decision-model adapter (`harnesses/omp/decision-model.md`, "Out-of-process gap").**
- Only in-process callers reach the judge. Extensions have no judge call, and `omp auth-gateway stdio` lists no judge models, so a script or plugin outside the session needs a new direct provider credential, which needs explicit human approval.

**S12. Local: the [map](../map.md)'s standing decision on Atlas models (user, 2026-10-19).**
- `atlas_query`, `atlas_rerank` and `atlas_summarize` run on Opus omp roles; omp roles can only be chat models.

## Findings
- **How Atlas would call Jev.** Most likely out of process: Atlas is an MCP/tool/extension plugin (ticket 06), and extensions have no judge call (S11). Live Jev calls from Atlas therefore need a direct provider credential and the user's approval. Only offline work an agent runs in an eval session, as in ticket 08, stays in session. Atlas also ships public-ready, so every use needs a fallback that works without Jev.
- **Reranking (high value).** Seam: ticket 06 "the fallback when a role is missing or fails". Uses: (a) Jev as the `atlas_rerank` fallback, one yes/no per candidate ("does this summary answer the query?") over the BM25 top 30, sorted by probability (S1, S2); (b) a Jev-vs-Opus run on the ticket-08 queries and graded pool before choosing. Allowed, because it ranks and drops nothing. Making Jev the default reranker would change the 2026-10-19 decision (S12), and a Jev reranker cannot be an omp role (chat models only), so it would run out of process. Jev's reranking quality on this corpus is unmeasured [INFERENCE].
- **Quality judging (high value).** Map item "How summaries and search results are judged for quality". Pooled 0/1/2 grading as in ticket 08 (S10), with reruns near the threshold (S3). The user's spot check stays the gate. Caveats: Jev rated 4 of the 6 trading sources as not relevant (S10), and a Jev reranker graded by Jev is scored by its own model family (ticket 08's shared-family risk). Runs in session.
- **Claim locator and citation support (medium value).** Seam: ticket 02's stored record ("claims… each with a locator") and the answer's "claims behind it with their sources". After `atlas_summarize`, a script checks each locator exists; Jev then flags claims whose section says nothing or contradicts, and the agent rereads only those (S4). Allowed as flag-only. Making the fail-closed check of the Sound/Doubtful/Noise labels probabilistic is forbidden, and Jev assigning those labels is ruled out by ticket 09. Out of process.
- **Source identity and near-duplicates (medium value).** Map item "How a source's identity is decided". Canonical URL plus content hash stay deterministic (v1 note 6). Jev judges only near-duplicate candidates such as reposts, mirrors and a thread versus its article; "same" and the middle level both become a proposal the user confirms (S5). Per-field questions on author, publisher and claim can help the backing-count independence rule. Auto-merging on "same" and replacing the URL/hash check are forbidden. Out of process.
- **Topic creation beyond the top 10 (medium).** Seam: ticket 06 "How topic creation gathers candidate sources". A yes/no "is this source about the same area as the brief?" over the library or a BM25 top 100 adds candidates for the research plan (S6, S7). The question must be broader than the brief, since Jev graded the brief narrowly [INFERENCE].
- **Inbox triage and injection screen (low now).** A relevance score orders the inbox; an injection yes/no flags a page for attention (S6). Excluding a page on the score is forbidden. Low value until discovery and `last30days` arrive.
- **"What's new" (medium).** A score per (new claim, agreed conclusion) adds likely conclusion-changing claims to what the answering agent reads (S8). Using Jev as a filter that hides sources needs a rule change.
- **Ruled out.** Topic assignment (S9): v2 drops fixed labels and finds membership by search. Probabilistic freshness or dirty detection: the content hash decides, and Jev skipping a re-summary would make a script check probabilistic. Weighting by source credibility: ticket 09 decided no automatic credibility score.

## Decision coverage
- Supports: a measured Jev-vs-Opus rerank trial in session, pooled Jev grading as the quality-judging method, and flag-only claim-support and near-duplicate checks.
- Does not decide: the default reranker, the fallback, the out-of-process credential, or any architecture choice. Those stay with [Decide Atlas v2 architecture](../issues/06-decide-atlas-v2-architecture.md).

## Freshness and capture
- Stored-evidence freshness state: not applicable.
- Durable capture location: this file.

## Next owner
- The user, through [Decide Atlas v2 architecture](../issues/06-decide-atlas-v2-architecture.md).
