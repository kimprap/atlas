# Atlas operating cadence and guardrails

Read this when choosing how to operate Atlas or when deciding whether a workflow should stay manual, become scheduled, or gain cheap automation.

## Immediate operating cadence

- Manual `/atlas-source` ingestion is allowed anytime for explicit sources.
- `/atlas-acquire` is the bounded discovery path. Use feeds, inboxes, watchlists, repo lists, author lists, or explicitly scoped queries; do not turn acquisition into open-ended crawling.
- `/atlas-answer` may answer only when `TOPICS.md` says the target topic is `current`.
- Dirty topics require `/atlas-refresh` before answer; do not answer from stale topic content plus pending deltas.
- Run `/atlas-audit` periodically and before or after nontrivial Atlas changes. In Phase 1 and early Phase 2, audit is the first operational guardrail.

## Cheap guardrails only

- Hooks or extensions may warn, block, or trigger cheap deterministic checks.
- Hooks or extensions must not run LLM synthesis.
- Reducer workflows stay in slash-command entrypoints, not in background hooks.
- Optional split files remain threshold-driven only; do not pre-create `SOURCES.md`, `DECISIONS.md`, or `HISTORY.md` before the topic size thresholds in `vault://atlas/ARCHITECTURE.md` are crossed.
- Framework text is authored in the app repo; bound instances only hold a product_owned snapshot. After app-root architecture edits, run `python3 scripts/atlas-instance.py sync-framework` (then `check`) instead of hand-copying trees.
- Smoke fixtures are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.

## Deferred phases

- Cron refresh is deferred until `/atlas-refresh` is stable on manual runs and persisted delta passes are consistently correct.
- Priority or impact-based routing is deferred until refresh quality is stable.
- SQLite, FTS, vector retrieval, and self-healing migration workflows are deferred to later explicit plans.
- If a later plan introduces those capabilities, keep Markdown artifacts browsable in Obsidian and keep deterministic rebuild or rollback paths explicit.
