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
4. `skill://atlas-core/assets/source-summary-quality-guide.md` for `--source-quality`
5. `skill://atlas-core/assets/source-summary-template.md` for `--source-quality`
6. `skill://atlas-core/assets/evals/source-summary-quality.json` for `--source-quality-calibration`
7. `vault://atlas/summaries/sources/MANIFEST.md`
8. `vault://atlas/summaries/registry/VOCAB.md`
9. `vault://atlas/summaries/registry/TOPICS.md`
10. `vault://atlas/summaries/registry/RELATIONS.md`
11. only the Atlas source and research paths required by the requested audit scope

## Workflow

- Stay read-only. Never repair or rewrite findings from this entrypoint.
- Run `scripts/atlas_state.py validate` over the complete manifest/topic/relation bundle first. Report stable diagnostic codes, paths, lines, and row IDs from the reference validator.
- Treat only the one contiguous canonical table region in each registry as state. A schema-shaped row outside it is `RELATION_ROW_OUTSIDE_TABLE` (or the matching registry diagnostic), never a relation to count or a cache input.
- Check manifest source-seq continuity, duplicate canonical URLs, duplicate source IDs, and missing source artifact paths.
- Check source frontmatter shape, invalid `canonical_tags`, and accidental promotion of `candidate_terms` into canonical routing fields.
- Check canonical relation references, deterministic and duplicate `Edge ID` values, valid `Relation`/`Impact`/`Confidence`/`Status` enums, hash/path consistency, and pending/applied pass provenance.
- Report `TOPICS.md` cache findings from reducer derivation; never recompute against orphan rows or accept a cache merely because it counted invalid text.
- Check that applied relations point at existing pass files and that topic paths exist.
- Check managed-section marker pairing and raw URL citations in managed answer/evidence sections.
- Check for unexpected SQLite or `.db` files under Atlas, unexpected `UNCLAIMED-SOURCES.md`, and leftover smoke fixture artifacts or fixture vocabulary rows.
- Report findings grouped by severity and recommend `atlas-index` or `atlas-migrate` only when a separate repair workflow is actually needed.

## `--source-quality-calibration` mode

This optional diagnostic stays product-fixture-only and read-only. Run every assessment, summary, routing, context-perturbation, checklist, and negative-audit case in the versioned eval asset for the active harness/model/template version; exact-validate structured outcomes with `scripts/atlas_quality.py validate-calibration`.

Use the same fixtures, evidence, validator, and expected JSON in every host. Record provider/harness/model plus resolved repo-local paths/hashes only as execution metadata. Report a missing or failed pair; never let a diagnostic grant or revoke source-write authority, add a provider-specific prompt, or weaken an expectation.

## Bounded `--source-quality` mode

Accept only these cohort selectors:

- `--source-seq <N|N-M>` — select one manifest sequence or one inclusive, non-reversed sequence range.
- `--source-id <id>` — select one manifest source ID; the option is repeatable.

Require at least one selector. When both forms are present, audit their deduplicated union. Resolve selectors through `MANIFEST.md`, report unknown or malformed selectors, and never widen the cohort to unrelated source rows or artifacts. Apply the registry checks above only to rows, relations, and topic-cache fields reachable from the selected cohort.

For each selected artifact:

- Build the declared source-only evidence bundle from its canonical payload, inspected media ledger, bounds, and immutable identity fields. The checklist is not part of that bundle.
- Produce the same seven-item checklist once as the bounded semantic audit: source-only boundary, primary contribution, source support, limits/uncertainty, context neutrality, assessment coherence, and proportionality.
- Run `scripts/atlas_quality.py validate-summary` with the artifact, evidence envelope, and separate checklist. Report failed IDs; do not add a score, threshold, prose match, length/citation limit, or second model pass.
- Flag generated/request/plan/repository/provider context in semantic sections, while allowing source-attributed text that is actually inside the evidence envelope.
- Flag `coverage: complete` when any canonical range or meaning-critical asset was truncated, omitted, unavailable, or unread.
- Flag full-commit-pinned GitHub payloads scored `moving`; `adopt` without high evidence, high practicality, stable payload, and no unresolved validation caveat; and thin authoritative primary mechanisms scored `low`.
- Compare Assessment Notes by signal after trimming and collapsing whitespace. Flag an identical nonempty note repeated in at least two artifacts and in more than half of the requested cohort.
- Require source-local locators for consequential concrete claims when available. Flag missing high-evidence locators, malformed/nonmatching relation verifier reasons, candidate-list-only Notes, and media links that are not the exact successfully fetched assets.
- Check header/frontmatter agreement, required sections, canonical/source/media URLs, semantic/post-draft boundaries, context perturbation, proportional concision, route/manifest/relation consistency, and all seven checklist invariants.

Report every finding with the artifact or registry path plus a section, row, or line anchor. Do not auto-repair, even when the correction appears mechanical.

## Output

Return a read-only audit report with the requested cohort, clean/issue status, finding counts by check, and concrete failing paths, anchors, or row identifiers.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
