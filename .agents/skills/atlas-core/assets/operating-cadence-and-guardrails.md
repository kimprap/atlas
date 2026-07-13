# Atlas operating cadence and guardrails

Read this when choosing how to operate Atlas or when deciding whether a workflow should stay manual, become scheduled, or gain cheap automation.

## Immediate operating cadence

- Manual `/atlas-source` ingestion is allowed anytime for explicit sources.
- `/atlas-acquire` is the bounded discovery path. Use feeds, inboxes, watchlists, repo lists, author lists, or explicitly scoped queries; do not turn acquisition into open-ended crawling.
- `/atlas-answer` may answer only when `TOPICS.md` says the target topic is `current`.
- Dirty topics require `/atlas-refresh` before answer; do not answer from stale topic content plus pending deltas.
- Run `/atlas-audit` periodically and before or after nontrivial Atlas changes; audit is the first operational guardrail.

## Cheap guardrails only

- Hooks or extensions may warn, block, or trigger cheap deterministic checks.
- Hooks or extensions must not run LLM synthesis.
- Reducer workflows stay in slash-command entrypoints, not in background hooks.
- Optional split files remain threshold-driven only; do not pre-create `SOURCES.md`, `DECISIONS.md`, or `HISTORY.md` before the topic size thresholds in `vault://atlas/ARCHITECTURE.md` are crossed.
- Framework text is authored at `.agents/ARCHITECTURE.md`; bound instances hold product-owned snapshots at `vault://atlas/ARCHITECTURE.md`. Sync only intended instances after any required approval, then run `python3 scripts/atlas-instance.py check`; never hand-copy framework trees.
- Smoke fixtures are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.

## Deferred capabilities

- Schedule refresh only after manual `/atlas-refresh` runs persist correct delta passes consistently.
- Add priority or impact-based routing only after refresh quality is stable and observed workload requires it.
- SQLite, FTS, vector retrieval, and self-healing mutation require an explicit architecture decision and migration; no skill may introduce them ad hoc.
- Any later storage or retrieval layer must keep Markdown artifacts browsable and define deterministic rebuild or rollback.
