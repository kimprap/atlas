Type: research
Parent: [Atlas v2 and portable skill plugins](../map.md)
Status: resolved

## Question

How can agents find relevant sources without fixed labels? Compare full-text search, embedding search, and hybrid retrieval for a corpus of short Markdown source summaries that runs locally on this Mac now and can move to hosted infrastructure later with little change.

## Answer

# Research Evidence: label-free retrieval for a small local-first Markdown summary corpus

## Authority and scope

- Requesting owner and receiver: Wayfinder controller acting as `dev-ask`. Governing artifact: `../map.md` as of 2026-10-19 (omp-only; one local vault reached only through a service; agent-only storage; public-ready with a personal-settings layer). The choice of engine, model, and fusion method belongs to ticket 06; this answer decides nothing.
- Bounded question: for a corpus of a few hundred to about 10k Markdown source summaries (about 0.5–3k tokens each, with a canonical link and metadata), queried only by coding agents in natural language, with no fixed labels, served locally on Apple Silicon and later hosted: (1) what retrieval-quality evidence exists for BM25 vs dense vs hybrid vs reranking; (2) which local engines fit, and how they move to hosting; (3) which embedding models fit, and what re-embedding costs; (4) what survives a move to the cloud unchanged.
- Stop condition: every item answered from primary sources with a version or date; contradictions named; no recommendation.
- Context only: Atlas v1 kept Markdown as canonical state and deferred SQLite to an "optional Phase 4 derived registry cache… rebuilt from Markdown". "Lexical/vector retrieval" was deferred to Phase 6 ("may use SQLite FTS or a separate vector adapter") (`~/dev/atlas/.agents/plans/archive/2026-07-01-2313_atlas-routing-refresh.md`, lines 85, 360–362). v1 was not evaluated.

## Sources

All sources were accessed on 2026-10-19 unless a date is given.

Retrieval quality:
- **[BEIR]** Thakur et al., arXiv [2104.08663](https://arxiv.org/abs/2104.08663) (v4 PDF; first posted 2021-04-17). It covers 18 datasets and 10 systems. Claims:
  - "BM25 is a robust baseline", and re-ranking and late-interaction models score best on average, "however, at high computational costs".
  - Dense models "often underperform".
  - BM25 plus a cross-encoder (BM25+CE) beats BM25 on 16 of 18 datasets.
  - Document lengths in BEIR are 11–635 words.
  - Relevance labels show a lexical annotation bias (the "Hole@10" analysis).
- **[E5]** Wang et al., arXiv [2212.03533](https://arxiv.org/abs/2212.03533) (2022-12-07): "the first model that outperforms the strong BM25 baseline on the BEIR retrieval benchmark without using any labeled data."
- **[BRIGHT]** Su et al., arXiv [2407.12883](https://arxiv.org/abs/2407.12883) (v4 PDF; first posted 2024-07-16). It is a reasoning-intensive retrieval benchmark that includes coding queries (LeetCode, Pony, StackExchange). Claims:
  - The best model reaches only 24.3 nDCG@10.
  - "BM25 matches the <1B models" but trails larger ones.
  - With LLM-written reasoning as the query, "BM25 improves the most" and is "best on the leaderboard" with GPT-4 reasoning queries.
  - An MS MARCO cross-encoder reranker "negatively impacts retrieval quality", while LLM reranking helps (+3.1 for GPT-4 over BM25).
- **[Bruch]** Bruch, Gai, Ingber, arXiv [2210.11934](https://arxiv.org/abs/2210.11934) (2022-10-21). A convex combination (CC) of normalized scores "outperforms RRF in in-domain and out-of-domain settings". RRF is "sensitive to its parameters". CC needs "only a small set of training examples".
- **[RRF]** Cormack, Clarke, Büttcher, SIGIR 2009, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods", doi:[10.1145/1571941.1572114](https://doi.org/10.1145/1571941.1572114). This is the original RRF claim, cited from its title and the LanceDB RRF doc; the paper was not re-read.
- **[Anthropic-CR]** "Introducing Contextual Retrieval", [anthropic.com/engineering/contextual-retrieval](https://www.anthropic.com/engineering/contextual-retrieval) (published 2024-09-19; modified 2026-01-07). It is a vendor eval across codebases, fiction, ArXiv, and science papers, using 1−recall@20. Claims:
  - "Embeddings+BM25 is better than embeddings on their own".
  - Contextual embeddings plus contextual BM25 cut the failure rate from 5.7% to 2.9%; adding a Cohere reranker cuts it to 1.9%.
  - For a knowledge base under 200k tokens, "just include the entire knowledge base in the prompt".
  - "summary-based indexing… low performance"; "adding generic document summaries to chunks… very limited gains".
- **[MMTEB]** Enevoldsen et al., arXiv [2502.13595](https://arxiv.org/abs/2502.13595) (2025-02-19): a 500+ task MTEB expansion, including code and long-document retrieval.
- **[RTEB]** "Introducing RTEB", [huggingface.co/blog/rteb](https://huggingface.co/blog/rteb) (2025-10-01, beta). It is a retrieval-only benchmark with private held-out datasets, because "existing benchmarks struggle to measure true generalization".

Engines (latest tag or release with its date, as read from the GitHub API):
- **[FTS5]** [sqlite.org/fts5.html](https://sqlite.org/fts5.html); SQLite 3.54.1 (2026-10-16, [changes](https://www.sqlite.org/changes.html)); public domain.
  - Ranking is a built-in `bm25()` function (k1=1.2, b=0.75).
  - Each commit writes a new segment b-tree, which incremental "automerge" merges.
  - For external-content tables, "it is the responsibility of the user" to keep the index consistent, for example with triggers.
  - Tokenizers include porter and trigram.
- **[sqlite-vec]** [asg017/sqlite-vec](https://github.com/asg017/sqlite-vec). Apache-2.0 per the GitHub API (the README does not state the licence).
  - Stable v0.1.9 (2026-03-31); v0.1.10-alpha.4 (2026-05-18) adds experimental ANN indexes (rescore, DiskANN, IVF).
  - The alpha notes say DiskANN DELETEs are "quite expensive".
  - README: "pre-v1, so expect breaking changes!"
  - Last push 2026-05-18. Mozilla Builders sponsored.
- **[libSQL]** [tursodatabase/libsql](https://github.com/tursodatabase/libsql), MIT. Docs: [AI & Embeddings](https://docs.turso.tech/features/ai-and-embeddings) and [libSQL](https://docs.turso.tech/libsql.md).
  - Native `F32_BLOB` vectors, a DiskANN index via `libsql_vector_idx`, and the query function `vector_top_k`.
  - Docs call libSQL "production-ready", but say Turso's "focus is Turso Database".
  - The last libsql-server release is v0.24.32 (2025-02-14); the repo was still pushed 2026-10-17.
- **[Turso DB]** [tursodatabase/turso](https://github.com/tursodatabase/turso), MIT, v0.8.3 (2026-10-12). This is the Rust rewrite of SQLite.
  - The README lists FTS (Tantivy) and vector indexing as experimental, and says "we have not yet reached 1.0".
  - [FTS docs](https://docs.turso.tech/sql-reference/functions/fts.md): Tantivy-powered and "not SQLite's FTS3/FTS4/FTS5"; BM25 `fts_score`; index updated automatically on DML; "No automatic segment merging" (run `OPTIMIZE INDEX` instead).
  - [Vector guide](https://docs.turso.tech/guides/vector-search.md): dense, sparse, int8, and 1-bit vectors, with exact distance functions.
  - [Extensions](https://docs.turso.tech/sql-reference/extensions.md): "SQLite `.so`/`.dll` loadable extensions are not supported".
- **[Turso Cloud extensions]** [docs.turso.tech/features/sqlite-extensions](https://docs.turso.tech/features/sqlite-extensions.md): FTS5 is built in. sqlite-vec is an optional extension pinned at **0.1.3**, available only on the Fly provider for Pro and Enterprise plans.
- **[LanceDB]** [lancedb/lancedb](https://github.com/lancedb/lancedb), Apache-2.0, v0.40.0 (2026-10-07). Docs: [hybrid search](https://docs.lancedb.com/search/hybrid-search.md), [reindexing](https://docs.lancedb.com/indexing/reindexing.md), [storage](https://docs.lancedb.com/storage/index.md).
  - BM25 FTS plus vector search, with RRF as the default hybrid reranker (linear combination is "deprecated").
  - In OSS, new rows stay unindexed until `table.optimize()`. Until then, queries "combine results from the existing index with exhaustive/flat search on the new data".
  - The same Lance format runs on local disk or S3/GCS/Azure, plus Enterprise `db://`.
- **[DuckDB FTS]** [duckdb FTS docs](https://duckdb.org/docs/current/core_extensions/full_text_search) on DuckDB v1.5.6 (2026-09-28), MIT. It provides `match_bm25`, but "The FTS index will not update automatically when the input table changes"; the documented workaround is to recreate the index.
- **[DuckDB VSS]** [vss docs](https://duckdb.org/docs/current/core_extensions/vss): "experimental".
  - HNSW persistence sits behind `hnsw_enable_experimental_persistence`, with a warning of possible "data loss or corruption of the index", and the docs "recommend that you do not use this feature in production".
  - The index must fit in RAM. Deletes are only marked, and need `hnsw_compact_index`.
- **[pgvector]** [pgvector/pgvector](https://github.com/pgvector/pgvector) v0.8.7 (2026-10-01, CHANGELOG); PostgreSQL licence (SPDX shows NOASSERTION on GitHub).
  - HNSW "can be created without any data" and has "slower build times".
  - Iterative index scans exist since 0.8.0.
  - README section "Hybrid Search": "Use together with Postgres full-text search", combined with RRF or a cross-encoder.
  - "Hosted Postgres": available on the [listed providers](https://github.com/pgvector/pgvector/issues/54).
- **[PG FTS]** [PostgreSQL 18 docs §12.3](https://www.postgresql.org/docs/current/textsearch-controls.html); current release 18.6 (2026-08-13). `ts_rank` "ranking functions do not use any global information", so it is not BM25 (it has no corpus IDF).
- **[ParadeDB]** [paradedb/paradedb](https://github.com/paradedb/paradedb), AGPL-3.0 (Community), v0.26.2 (2026-10-16). Adds Tantivy-based BM25 to Postgres; managed ParadeDB Cloud; Enterprise has a commercial licence.
- **[Meilisearch]** [meilisearch/meilisearch](https://github.com/meilisearch/meilisearch) v1.55.0 (2026-10-12); licence `MIT AND BUSL-1.1` (Enterprise Edition parts are BUSL).
  - Hybrid search via `semanticRatio` (default 0.5).
  - Local HuggingFace embedders or REST APIs ([hybrid ranking](https://www.meilisearch.com/docs/capabilities/hybrid_search/advanced/custom_hybrid_ranking.md), [choose an embedder](https://www.meilisearch.com/docs/capabilities/hybrid_search/how_to/choose_an_embedder.md)).
- **[Typesense]** [typesense/typesense](https://github.com/typesense/typesense) v30.2 (2026-04-19), GPL-3.0.
  - Hybrid uses weighted rank fusion with `alpha` ([vector search 30.1](https://typesense.org/docs/30.1/api/vector-search.html)).
  - "stores the entire search index in-memory" ([system requirements](https://typesense.org/docs/guide/system-requirements.html)).
- **[Tantivy]** [quickwit-oss/tantivy](https://github.com/quickwit-oss/tantivy) 0.26.1 (2026-05-10), MIT. A Rust BM25 library; it powers Turso FTS and ParadeDB.

Embedding models (Hugging Face API: licence tag, parameter count from safetensors, commit sha; numbers are **self-reported on each model card**):

| Model (sha) | Params | Dims | Max tokens | Licence | Card-reported retrieval |
| - | - | - | - | - | - |
| [bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5) (5c38ec7c40) | 33M | 384 | 512 | MIT | MTEB v1 Retrieval(15) 51.68 |
| [bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5) (a5beb1e3e6) | 109M | 768 | 512 | MIT | 53.25 |
| [nomic-embed-text-v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) (e9b6763023) | 137M | 768 (Matryoshka truncation to 64) | 8192 | Apache-2.0 | MTEB v1 Retrieval 53.01 (per the gte card) |
| [gte-modernbert-base](https://huggingface.co/Alibaba-NLP/gte-modernbert-base) (e7f32e3c00) | 149M | 768 | 8192 | Apache-2.0 | BEIR(15) 55.33; CoIR(20) 79.31 |
| [granite-embedding-english-r2](https://huggingface.co/ibm-granite/granite-embedding-english-r2) (47ea694b25) | 149M | 768 | 8192 | Apache-2.0 | BEIR(15) 53.1; CoIR(10) 55.3; no MS MARCO in training |
| [embeddinggemma-300m](https://ai.google.dev/gemma/docs/embeddinggemma/model_card) (57c266a740) | 303M | 768 (Matryoshka 512/256/128) | 2048 | Gemma licence | MTEB Eng v2 mean 69.67; Code v1 68.76 |
| [snowflake-arctic-embed-m-v2.0](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0) (95c2741480) | 305M | 768 (Matryoshka) | 8192 | Apache-2.0 | per granite card: MTEB-v2 Retrieval 58.4 |
| [mxbai-embed-large-v1](https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1) (b33106f585) | 335M | 1024 (Matryoshka, binary) | 512 | Apache-2.0 | MTEB v1 Retrieval 54.39 |
| [voyage-4-nano](https://huggingface.co/voyageai/voyage-4-nano) (433ece5e27) | 346M | 2048 default (Matryoshka 1024/512/256) | 32000 | Apache-2.0 | shares an embedding space with hosted voyage-4/-lite/-large |
| [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) (97b0c614be) | 596M | 1024 (32–1024 selectable) | 32k | Apache-2.0 | MTEB Eng v2 Retrieval 61.83; MMTEB Retrieval 64.64 |

- Rerankers (Hugging Face API): [bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3), 568M, Apache-2.0; [Qwen3-Reranker-0.6B](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B), 596M, Apache-2.0; [mxbai-rerank-base-v2](https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v2), 494M, Apache-2.0. [jina-embeddings-v3](https://huggingface.co/jinaai/jina-embeddings-v3) is CC-BY-NC-4.0, so it is not usable for a public-ready build without a licence.
- Local runtime: [Ollama library](https://ollama.com/library) serves `embeddinggemma`, `qwen3-embedding`, `nomic-embed-text`, `bge-m3`, `snowflake-arctic-embed2`, and `granite-embedding` (all pages returned HTTP 200).
- Hosted pricing, per million tokens:
  - OpenAI ([embeddings guide](https://platform.openai.com/docs/guides/embeddings), [model page](https://platform.openai.com/docs/models/text-embedding-3-small)): text-embedding-3-small $0.02 at 1536 dims; -3-large $0.13 at 3072 dims. Both have a `dimensions` parameter and accept up to 8192 input tokens.
  - Voyage ([pricing](https://docs.voyageai.com/docs/pricing)): voyage-4-lite $0.02, voyage-4 $0.06, voyage-context-4 $0.12, rerank-2.5 $0.05. The first 200M tokens are free per account.
  - Gemini ([pricing](https://ai.google.dev/gemini-api/docs/pricing)): gemini-embedding-2 text $0.20.
  - Voyage's shared embedding space is stated on the voyage-4-nano card. The [MongoDB blog](https://www.mongodb.com/company/blog/technical/moe-shared-embedding-spaces-how-voyage-4-scales-smarter) corroborates it (a vendor source).

## Findings

### 1. Retrieval quality

- **BM25 is a strong zero-shot floor, not a ceiling.** In 2021, BEIR found that dense retrievers out of domain often lost to BM25, and that BM25 plus a cross-encoder won 16 of 18 datasets. From 2022 on (E5), dense models beat BM25 on average on BEIR. Today's small models report BEIR/MTEB-retrieval figures of about 51–62, against BM25's BEIR scores as cited in BRIGHT's appendix.
- **Coding and reasoning queries narrow the gap.** On BRIGHT, BM25 equals the dense models under 1B parameters, and every system scores at most 24.3 nDCG@10. When an LLM rewrites the query as reasoning steps, BM25 gains the most and tops the board. This is the closest published proxy for "a coding agent writes a natural-language query".
- **Hybrid beats either method alone in the one vendor eval that matches this setup** (Anthropic-CR, which includes a codebase domain). Bruch shows that *how* results are fused matters: a tuned convex combination beats RRF, and RRF's constant matters.
- **Reranking helps when the reranker transfers.** It helped in BEIR (cross-encoder) and in Anthropic-CR (Cohere). On BRIGHT, an MS MARCO MiniLM cross-encoder *hurt*, while LLM rerankers helped.
- **Applicability limits:**
  - BEIR and MTEB documents are mostly passages under 635 words. This corpus is roughly 375–2,250 words per document, and models capped at 512 tokens (bge-*-v1.5, mxbai-large) would truncate most summaries `[INFERENCE from the stated token limits]`.
  - No benchmark found uses LLM-written *summaries* as the documents. Anthropic reports that "summary-based indexing" and "generic document summaries" did poorly, but as *augmentations* of chunks, not as a whole-document corpus, so it neither supports nor refutes this design.
  - All model scores are self-reported on model cards. RTEB exists because public MTEB scores may reflect overfitting.
  - Anthropic's under-200k-token note applies only to the low end: about 300 summaries × 0.5k tokens is about 150k tokens; 10k × 3k is about 30M tokens `[INFERENCE: arithmetic]`.

### 2. Local engines (all run in-process or as one local process on macOS arm64)

| Engine | Hybrid | Insert/update cost | Maturity (version, date) | Licence | Hosted path |
| - | - | - | - | - | - |
| SQLite FTS5 + sqlite-vec | No built-in fusion; FTS5 `bm25()` + `vec0` KNN, fused in SQL or the app | FTS5: a segment per commit, auto-merged; external content needs triggers. vec0 0.1.9 is a flat (exact) scan; ANN only in an alpha with expensive deletes | SQLite 3.54.1 (2026-10-16) stable; sqlite-vec v0.1.9 (2026-03-31), pre-v1, last push 2026-05-18 | Public domain / Apache-2.0 | The file copies as-is to any host. Turso Cloud supports FTS5, but sqlite-vec only at 0.1.3 on Fly Pro/Enterprise |
| libSQL vector | FTS5 + `vector_top_k`, fused in the app | DiskANN index maintained on write | Server v0.24.32 (2025-02-14); docs say "production-ready", vendor focus has moved | MIT | Turso Cloud runs libSQL natively |
| Turso DB (rewrite) | Tantivy FTS + vectors in one SQL engine, fused in the app | FTS updates automatically on DML; manual `OPTIMIZE INDEX`; vector indexing experimental | v0.8.3 (2026-10-12), pre-1.0, FTS experimental | MIT | Turso Cloud; FTS syntax differs from FTS5 |
| LanceDB | Built in (RRF default; cross-encoder, Cohere, and other rerankers) | New rows searched flat until `optimize()` (OSS manual; Enterprise automatic) | v0.40.0 (2026-10-07) | Apache-2.0 | The same Lance tables on S3/GCS/Azure, or Enterprise |
| DuckDB FTS/VSS | Manual | FTS index **does not update**, so every change means a rebuild; VSS persistence experimental, RAM-bound | v1.5.6 (2026-09-28); VSS "experimental" | MIT | The file is portable; MotherDuck not assessed |
| Postgres + pgvector (+FTS or ParadeDB) | Documented recipe: FTS + vector, fused by RRF or a cross-encoder | HNSW inserts are incremental; builds are slower | pgvector 0.8.7 (2026-10-01); PG 18.6 | PostgreSQL licence; ParadeDB AGPL-3.0 | Many managed hosts (issue #54); a dump/restore move. ParadeDB needs its own cloud or self-hosting |
| Meilisearch | Built in (`semanticRatio`, local or REST embedders) | Async indexing tasks | v1.55.0 (2026-10-12) | MIT + BUSL-1.1 (Enterprise Edition) | Meilisearch Cloud; dump/snapshot |
| Typesense | Built in (rank fusion with `alpha`) | Whole index in RAM | v30.2 (2026-04-19) | GPL-3.0 | Typesense Cloud |

- Postgres's built-in `ts_rank` is not BM25: it uses no global statistics. True BM25 inside Postgres needs ParadeDB, which is AGPL.
- Scale: 10k × 1024-dim float32 is about 41 MB, so exact brute-force KNN is feasible without ANN at this size `[INFERENCE: arithmetic; no latency benchmark was run]`.

### 3. Embedding models and re-embedding cost

- **Local options** that fit the 0.5–3k token documents without truncation: nomic-v1.5, gte-modernbert, granite-r2, arctic-m-v2 (8k context); EmbeddingGemma (2k context, so 3k-token documents would be cut); Qwen3-0.6B and voyage-4-nano (32k context). All are 0.1–0.6B parameters.
- **Licences:** all are Apache-2.0 except EmbeddingGemma (Gemma licence) and the bge models (MIT).
- **Hosted options:** OpenAI, Voyage, and Gemini (prices in Sources).
- **Re-embedding the whole corpus** at the 30M-token upper bound costs about $0.60 (3-small or voyage-4-lite), $1.80 (voyage-4), $3.90 (3-large), or $6.00 (gemini-embedding-2). It costs $0 inside Voyage's 200M free tokens. At the 150k-token low end, every price is under $0.05 `[INFERENCE: arithmetic on listed prices]`.
- **The real switching cost is not money.** Any model change invalidates every stored vector and any ANN index, and the query side must switch at the same moment. The one documented exception is the Voyage 4 family's shared embedding space: local voyage-4-nano vectors are declared compatible with the hosted voyage-4 models (a vendor claim, not independently verified).
- **Gap:** no primary benchmark of embedding throughput on Apple Silicon was found, so local re-embed wall-time is unquantified.

### 4. What survives a cloud move

- **Unchanged (formats):**
  - A SQLite file with FTS5 tables (any host; Turso Cloud also has FTS5 built in).
  - Lance tables, whose format is the same on local disk and object storage.
  - A Postgres dump (pgvector is on many managed hosts).
  - Raw stored vectors, which are portable across engines, provided the embedding model is unchanged.
- **Must be rebuilt or changed:**
  - Moving from local sqlite-vec to Turso Cloud: an old sqlite-vec (0.1.3) and plan limits, or a switch to native libSQL vectors.
  - Moving to Turso DB: FTS5 → Tantivy FTS (different syntax), and no loadable extensions.
  - DuckDB: the FTS index (every change) and the VSS index (not production-persistent).
  - Typesense and Meilisearch: a re-import into the hosted instance.
  - Any switch of embedding model: everything vector-related, except within the Voyage 4 family.
- **Unaffected by the engine:** the Markdown summaries themselves, if they stay canonical, can rebuild any of these indexes (cf. Atlas v1's rebuildable-cache rule) `[INFERENCE]`.

### Contradictions

1. **BM25 vs dense over time.** BEIR (2021) says dense often underperforms BM25; E5 (2022) and later model cards say dense beats it; BRIGHT (2024) says BM25 ≈ small dense models on reasoning and coding queries, and wins with LLM-expanded queries.
2. **RRF.** Cormack 2009 says RRF beats the methods it fuses; Bruch 2022 says CC beats RRF and RRF is parameter-sensitive. Engines default to RRF anyway (LanceDB, the pgvector example) or to weighted fusion (Typesense `alpha`, Meilisearch `semanticRatio`).
3. **Cross-encoder reranking.** It is best in BEIR and helps in Anthropic-CR, but hurts in BRIGHT (MS MARCO MiniLM).
4. **Self-reported scores disagree across cards.** Examples: the gte-modernbert card reports BEIR 55.33 and CoIR(20) 79.31, while the granite card reports CoIR(10) 71.5 for the same model. The Qwen card reports text-embedding-3-large below Qwen3-0.6B, a competitor's numbers. MTEB v1 Retrieval(15), MTEB Eng v2 Retrieval, and BEIR(15) are different task sets and are not comparable.
5. **Turso's own messages.** libSQL docs say "production-ready" and point new projects to Turso DB, while the Turso DB README marks FTS and vector indexing experimental and pre-1.0.

### Gaps

- No benchmark on agent-issued queries against LLM-written source summaries.
- No Apple Silicon throughput or latency figures.
- RTEB results per model were not extracted.
- MotherDuck and other hosting for DuckDB extensions was not assessed.
- The licence of the hosted Meilisearch hybrid feature was not checked.

## Decision coverage

- **Supported:**
  - Lexical BM25 alone is a defensible floor for agent queries, especially when the agent can rewrite its query.
  - Hybrid plus reranking is the best-evidenced quality stack, but its gain is domain-dependent and the fusion method is contested.
  - At ≤10k documents, exact vector search is feasible without ANN `[INFERENCE]`.
  - Embedding cost is negligible; the switching burden is a full vector rebuild.
  - SQLite (FTS5), Lance, and Postgres formats can move to hosting largely unchanged. DuckDB's indexes and the Turso rewrite's FTS cannot.
- **Not decided (ticket 06):**
  - Which engine, embedding model, fusion method, or reranker to use.
  - Whether vectors are needed at all, or BM25 plus agent query rewriting is enough.
  - Whether each summary is chunked or embedded whole.
  - The hosting target.
  - The smallest remaining question: a local eval of BM25 vs hybrid vs hybrid+rerank on a sample of real summaries with real agent queries, since no published benchmark matches this corpus.

## Freshness and capture

- Stored-evidence freshness: not applicable.
- Durable capture: this ticket file.

## Next owner

- Wayfinder controller acting as `dev-ask`.
