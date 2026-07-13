---
name: atlas-acquire
description: >
  Atlas bounded-acquisition entrypoint. Use when the user invokes
  /atlas-acquire or wants Atlas to discover sources from a watchlist, feed,
  inbox, repo list, author list, or explicitly scoped query.
disableModelInvocation: true
---

# atlas-acquire

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `skill://atlas-source`
5. `skill://atlas-core/assets/research-library-templates.md`
6. `vault://atlas/summaries/sources/MANIFEST.md` when it exists

## Workflow

- Accept only bounded acquisition scope: watchlists, feeds, inboxes, repo lists, author lists, or explicitly scoped queries.
- Enumerate candidate sources and dedupe them through `MANIFEST.md` before summarization.
- Materialize each new or changed source through the `atlas-source` workflow, not by writing ad hoc source summaries.
- Write one acquisition run log under `vault://atlas/summaries/sources/runs/<YYYY>/<YYYY-MM>/`.
- Record created, refreshed, skipped, blocked, and no-topic-match outcomes in the run log with exact source identifiers when available.
- Never update topic answers directly from acquisition.
- Never create vocabulary rows, topic rows, or topic folders as an acquisition side effect.

## Output

Report the run-log path plus grouped source outcomes: created, refreshed, skipped duplicate, blocked, and no-topic-match.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
