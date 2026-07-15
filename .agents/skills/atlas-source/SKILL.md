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
4. `skill://atlas-core/assets/source-summary-quality-guide.md`
5. `skill://atlas-core/assets/source-summary-template.md`
6. `vault://atlas/summaries/sources/MANIFEST.md` when it exists
7. `vault://atlas/summaries/registry/VOCAB.md`, `TOPICS.md`, and `RELATIONS.md` when routing is required

## Workflow

### Resolve mode and immutable identity

- Accept explicit source inputs only. Normalize one canonical URL before fetch, dedupe, or identity generation.
- Without `--resummarize`, use normal ingestion/refresh behavior below.
- With `--resummarize`, require an existing canonical URL or exact artifact path and resolve it to exactly one manifest row. A missing identity or URL/path conflict halts before any write; never allocate a source in this branch.
- The identity resolver may read that exact manifest row, but the semantic-draft envelope receives only preserved `source_id`, `source_seq`, `canonical_url`, artifact path, first-seen/acquisition provenance, and required retrieval fields. Never pass old artifact prose or relation/topic context into drafting.

### Calibrate write support

- Before the first write-capable invocation for an active harness/model/template/fixture version, run every case in `skill://atlas-core/assets/evals/source-summary-quality.json` and exact-validate the structured results with `scripts/atlas_quality.py validate-calibration`.
- A batch calibrates once before its first write. Any unavailable or wrong result mutation-disables that pair and produces zero invocation writes. Never add a provider-specific prompt, relax an expected result, or borrow another pair's qualification.
- Verify live app-directory discovery of repo-local `.agents/AGENTS.md`, this skill, `atlas-core`, and both Python reference scripts. Record host/model metadata only in the execution report.

### Fetch and build the source-only envelope

- Prefer official Markdown, docs, README, or reader-mode extraction before browser fallback. Fetch the complete readable canonical payload before hashing or scoring coverage; page every omitted range.
- Inspect each linked image, diagram, code asset, audio segment, or video segment essential to meaning. Record exact successfully fetched pinned URLs and page/range/timestamp bounds; never reconstruct a media path.
- If complete retrieval fails, hash and summarize only the materialized payload, set `coverage: partial`, and name the exact missing range or meaning-critical asset.
- Build the typed evidence envelope from only the new canonical payload/URL, inspected pinned media, retrieval bounds, immutable identity/acquisition fields needed to render the artifact, and product-owned template/rubric versions. Exclude old artifacts, sibling sources, taxonomy/topics/relations, campaign/request/plan/task/session text, repository context, and provider/model identity.

### Assess, draft, and gate each source independently

- Derive a source-specific assessment tuple and context-neutral semantic draft independently for each source. Never inherit another batch item's tuple, phrasing, candidates, or posture.
- Draft identity/retrieval metadata, Assessment, TL;DR, Key points, Approaches / mechanics, Evidence, Caveats, Reuse cues, and source/media Links with `skill://atlas-core/assets/source-summary-template.md`; keep schema version 1 and all keys/enums.
- Preserve minimum-sufficient distinct information. Reject duplicates, paraphrased filler, stock advice, empty boilerplate, and campaign rationale without imposing a fixed output length.
- Run `scripts/atlas_quality.py validate-summary`. Then run the guide's exact seven-item acceptance checklist once as the existing bounded semantic audit over only the same envelope and draft. One structural finding or failed item rejects the draft; revise that dimension and rerun both gates.

### Classify, route, and write

- Only after the semantic draft passes, read bounded `VOCAB.md`, `TOPICS.md`, and `RELATIONS.md` rows. Normalize classification, propose bounded routes with exact verifier reasons, and attach post-draft Classification/Routing annotations without rewriting source claims.
- Validate taxonomy enums, assessment/adoption coupling, source/media URL ledger, route-reason shape, and the complete candidate cohort.
- Route through `atlas-route` and `scripts/atlas_state.py`; persist source, manifest, relation, and topic replacements only after every gate passes and current input hashes match.

### Normal ingestion or refresh

- If the source exists and refresh is not due, skip summarization and report the existing artifact path.
- If refresh is due, fetch first and compare `content_hash`. When unchanged, update only `last_checked`; do not rewrite the artifact or relations.
- If the source is absent, allocate the next monotonically increasing `Source seq` and append one manifest row.
- Write one source artifact for a new or materially changed source, update its manifest row, and run route-source. Do not run route-source for an unchanged duplicate skip.

### Explicit `--resummarize`

- Re-fetch and redraft even when refresh is not due. Preserve `source_id`, `source_seq`, `canonical_url`, `first_seen`, `acquired_by`, `acquisition_run`, and the artifact path; update `last_checked` and `last_summarized`.
- **Same hash:** replace generated summary frontmatter values and body in place; preserve the manifest identity/hash, acquisition provenance, and existing `applied`, `rejected`, and `superseded` relation history. Re-run bounded routing against every existing current-hash pending edge plus newly generated candidates. Route-source may update an existing `pending` edge, reject one no longer supported, or add a deterministic pending edge for a newly included topic. Never reopen an `applied` edge solely because prose changed.
- **Changed hash:** follow normal material-change routing. Update the artifact and manifest hash in place, mark every old-hash `pending` row for the source `superseded`, preserve old `applied` rows as provenance, and rerun candidate generation plus the bounded verifier. Create a deterministic current-hash pending edge only for `include: true`; create no replacement for an excluded candidate.
- Recompute affected topic dirty fields from `RELATIONS.md`. Set source and manifest route status from current-hash relations: `routed` when any is `pending` or `applied`, `no-topic-match` when none is included, and `routing-blocked` only for a vocabulary/schema blocker. Historical old-hash edges do not determine the current status.

## Output

Report artifact path, `source_id`, `source_seq`, route status, evidence bounds/coverage, and whether the source was created, materially refreshed, resummarized with the same hash, resummarized with a changed hash, or skipped as an unchanged routine duplicate.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
