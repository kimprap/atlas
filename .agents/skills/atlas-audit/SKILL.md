---
name: atlas-audit
description: >
  Atlas read-only audit entrypoint. Use when the user invokes /atlas-audit or
  wants Atlas registry, artifact, freshness, and schema state validated without
  mutating vault data.
disableModelInvocation: true
---

# atlas-audit

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `vault://atlas/summaries/sources/MANIFEST.md`
5. `vault://atlas/summaries/registry/VOCAB.md`
6. `vault://atlas/summaries/registry/TOPICS.md`
7. `vault://atlas/summaries/registry/RELATIONS.md`
8. the Atlas source and research roots needed by the requested audit scope

## Workflow

- Stay read-only. Do not repair anything from this entrypoint.
- Check manifest source-seq continuity, duplicate canonical URLs, duplicate source IDs, and missing source artifact paths.
- Check source frontmatter shape, invalid `canonical_tags`, and accidental promotion of `candidate_terms` into canonical routing fields.
- Check relation references, duplicate `Edge ID` values, valid `Relation`/`Impact`/`Confidence`/`Status` enums, and pending/applied consistency.
- Check `TOPICS.md` dirty counts, pending edge IDs, newest pending source seq, and source watermarks against `RELATIONS.md`.
- Check that applied relations point at existing pass files and that topic paths exist.
- Check managed-section marker pairing and raw URL citations in managed answer/evidence sections.
- Check for unexpected SQLite or `.db` files under Atlas, unexpected `UNCLAIMED-SOURCES.md`, and leftover smoke fixture artifacts or fixture vocabulary rows.
- Report findings grouped by severity and recommend `atlas-index` or `atlas-migrate` only when a separate repair workflow is actually needed.

## Output

Return a read-only audit report with clean/issue status, finding counts, and concrete failing paths or row identifiers.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
