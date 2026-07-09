---
name: atlas-source
description: >
  Atlas source-ingestion entrypoint. Use when the user invokes /atlas-source
  or wants to ingest explicit URLs, repos, or files into Atlas source
  artifacts and manifest rows without broader research synthesis.
disableModelInvocation: true
---

# atlas-source

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `skill://digest/assets/source-summary-template.md`
5. `vault://atlas/summaries/sources/MANIFEST.md` when it exists
6. `vault://atlas/summaries/registry/VOCAB.md`, `TOPICS.md`, and `RELATIONS.md` when routing is required

## Workflow

- Accept explicit source inputs only.
- Normalize each input into one canonical URL before fetch or dedupe.
- Derive `source_id` from the canonical URL and look up both `Source ID` and `Canonical URL` in `MANIFEST.md`.
- If the source exists and refresh is not due, skip summarization and report the existing artifact path.
- If refresh is due, fetch readable content first, compute `content_hash`, and update only `last_checked` when unchanged.
- Prefer official Markdown/docs/README or reader-mode extraction before browser fallback.
- Extract title, canonical URL, author or org, publisher, source kind, published date when visible, and only canonical vocabulary IDs for `canonical_tags`.
- Write one source artifact from `skill://digest/assets/source-summary-template.md`.
- Append or update one manifest row with `Source seq`, `Source ID`, `Canonical URL`, artifact path, dates, `content_hash`, `Refresh after`, `Route status`, and `Status`.
- Run route-source after any new or changed artifact unless the result was an unchanged duplicate skip.

## Output

Report artifact path, `source_id`, `source_seq`, route status, and whether the source was created, refreshed, or skipped as an unchanged duplicate.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
