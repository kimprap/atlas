# atlas-acquire

## Qualified invocation

This ordinary Workflow Owner resource may execute only when one of these qualified conditions holds:

1. The selected Workflow Owner receives a live `/atlas-ask` Task whose dispatch binding names `atlas-acquire`.
2. An allowlisted current Workflow Owner loads this resource as a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
3. Any other load performs no further read, model work, façade call, profile/vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

Only the selected Workflow Owner emits one outer `atlas-workflow-result.schema.json` result. A Successor Owner preserves its native current output and never creates another Task or outer result.



## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core`
3. `skill://atlas-core/assets/markdown-registry-contracts.md`
4. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
5. `skill://atlas-ask/owners/atlas-source/OWNER.md`

## Workflow

- Accept only one bounded watchlist, feed, inbox, repository list, author list, or explicitly scoped query. State its kind, identifier, and positive limit before discovery; no open-ended crawl, taxonomy promotion, or topic creation is allowed.
- Use the harness to fetch/search that declared scope. It returns candidate `url`, `discovered_from`, and `label` values only; discovery output is untrusted input, not write authority.
- Read the bounded manifest through `vault.read`, then call `discovery.normalize` with the exact scope, harness candidates, and manifest rows. Use only its selected candidates; retain its rejected and overflow outcomes in the run report. Do not recalculate canonical URLs, dedupe, ordering, classifications, or limits.
- Pass the complete selected candidate list once to the allowlisted Successor Owner resource `skill://atlas-ask/owners/atlas-source/OWNER.md`. `atlas-source` owns its one inventory, worker wave, just-in-time source preparation, serial source transactions, and route delegation. Acquisition adds no second inventory, reducer, renderer, transaction path, or per-URL child workflow.
- Write one acquisition run log under `vault://atlas/summaries/sources/runs/<YYYY>/<YYYY-MM>/` only through `vault.conditional_replace`. Acquisition never writes topic answers, vocabulary rows, topic rows, or topic folders.

## Output

Report the run-log path and grouped created, refreshed, skipped duplicate, blocked, no-topic-match, rejected, and overflow outcomes.

