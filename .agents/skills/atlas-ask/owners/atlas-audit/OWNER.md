# atlas-audit

## Qualified invocation

This ordinary Workflow Owner resource may execute only when one of these qualified conditions holds:

1. The selected Workflow Owner receives a live `/atlas-ask` Task whose dispatch binding names `atlas-audit`.
2. An allowlisted current Workflow Owner loads this resource as a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
3. Any other load performs no further read, model work, façade call, profile/vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

Only the selected Workflow Owner emits one outer `atlas-workflow-result.schema.json` result. A Successor Owner preserves its native current output and never creates another Task or outer result.



## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/SKILL.md`
3. `skill://atlas-core/assets/markdown-registry-contracts.md`
4. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
5. `skill://atlas-core/assets/source-summary-quality-guide.md` and `skill://atlas-core/assets/source-summary-template.md` for `--source-quality`
6. `skill://atlas-core/assets/evals/source-summary-quality.json` for `--source-quality-calibration` and semantic calibration packets
7. `skill://atlas-core/assets/evals/agent-tooling.json` for `--agent-tools-calibration` and deterministic-tool packets
8. only the Atlas source and research paths required by the requested audit scope

## Façade-first boundary

- Begin with `scripts/atlas_tool.py capabilities`. Require the advertised operations needed for the selected read-only mode before proceeding.
- Send every Atlas request through `scripts/atlas_tool.py call --input <path|->` in the version-1 envelope. Use `vault.read`, `vault.list`, `vault.hash`, and `vault.digest_tree` for bounded logical-vault inspection; use their returned revisions, paths, ordering, and findings rather than resolving a profile, root, host path, or digest locally.
- Use `state.validate` for registry state, `quality.validate_summary` for source-quality checks, and `quality.prepare_calibration` / `quality.validate_calibration` for calibration. The core operation contracts own request shape, deterministic validation, hashing, and output normalization.
- This entrypoint never calls `vault.write_json`, `vault.conditional_replace`, `vault.delete_tree`, `transaction.execute`, `transaction.recover`, or `transaction.successor` against the bound profile. It never invokes an underlying Python owner directly. A finding is not mutation approval; direct repairs belong to the separately authorized `atlas-index` or `atlas-migrate` workflow.

## Workflow

- Read the requested logical documents through `vault.read`. Validate the complete manifest/topic/relation bundle with `state.validate` before reporting derived state.
- Treat only the one contiguous canonical table region in each registry as state. A schema-shaped row outside it is `RELATION_ROW_OUTSIDE_TABLE` (or the matching registry diagnostic), never a relation to count or a cache input.
- Check that every manifest `Source seq` is a positive integer and unique, that historical allocations are not reused, and that the next allocation is `max(existing Source seq) + 1`. Gaps are legal and produce no finding; never repair or renumber them.
- Check canonical relation references, deterministic and duplicate `Edge ID` values, valid `Relation`/`Impact`/`Confidence`/`Status` enums, hash/path consistency, and pending/applied pass provenance. Report `TOPICS.md` cache findings from reducer derivation; never recompute against orphan rows or accept a cache merely because it counted invalid text.
- Check that applied relations point at existing pass files, topic paths exist, managed-section markers pair, and managed answer/evidence sections contain no raw URL citations.
- Compare every bounded subdomain index topic-map row, coverage bucket, and stale/weak entry with the topic path and freshness in `TOPICS.md` plus the referenced topic frontmatter's `coverage_state` and `last_researched`. Emit stable read-only finding IDs `SUBDOMAIN_TOPIC_MAP_DRIFT` and `SUBDOMAIN_COVERAGE_MAP_DRIFT`; recommend `atlas-research` for synthesis/projection correction and never auto-repair.
- Use bounded `vault.list` inspection to identify unexpected SQLite or `.db` files, `UNCLAIMED-SOURCES.md`, leftover smoke-fixture artifacts, and fixture vocabulary rows. Do not inspect a host filesystem or infer unlisted paths.
- Group findings by severity. Recommend `atlas-research` for subdomain synthesis/projection drift, or `atlas-index` / `atlas-migrate` only when a distinct authorized registry or schema repair workflow is needed.

## `--source-quality-calibration` mode

This optional diagnostic remains product-fixture-only and read-only. Prepare fixture-order blinded cases through `quality.prepare_calibration`, then exact-validate each structured response through `quality.validate_calibration`. Run every assessment, summary, routing, context-perturbation, checklist, and negative-audit case in the versioned fixture; report missing or failed pairs. It never grants or revokes source-write authority, adds provider-specific prompts, or weakens an expectation.

## `--agent-tools-calibration` mode

This is isolated qualification orchestration, not an audit exception: it can exercise only an OS-temporary Atlas instance and can never mutate the bound instance or confer bound-vault write authority.

1. Create a new OS-temporary instance and a temporary profile that selects only that instance. Do not copy, resolve, or reuse the bound profile/root. Record a pre-run product write-set snapshot and a pre-run temporary-instance write-set snapshot; for the temporary logical tree, use `vault.digest_tree` through the temporary profile rather than an ad hoc walker or hash implementation.
2. Use `quality.prepare_calibration` to create exactly two blinded packet families: all deterministic behavior cases from `agent-tooling.json`, and a fixture-order semantic matrix from `source-summary-quality.json` covering assessment blinding, evidence-backed claims, forbidden-context absence, proposal/checklist/render/summary validation, and scope gates. Record the selected semantic case IDs and rationale. Keep each serialized family below 50 KiB; do not add ad hoc cases, live vault text, profile/root data, hidden expected values, or prior-lane output.
3. Run one pilot in a fresh task context. Inspect and record only its resolved provider, harness, and model metadata, then exact-validate the pilot response with `quality.validate_calibration`. After that gate, run fresh isolated task contexts across the two families, with at most four contexts concurrent. Contexts do not share prompts, responses, temporary state, or authority.
4. Exact-validate every structured calibration result with `quality.validate_calibration`. For temporary-instance exercises, compare the façade-observed canonical outputs, declared write set, identities, transitions, rendered structure, and scope gates with the fixture contract. Prose may vary only where the fixture permits it; evidence-backed claims, forbidden-context absence, proposal/checklist/render/summary validation, and allowed actions must pass.
5. Record provider/harness/model solely as execution metadata. Do not branch packet content, expectations, authority, or conclusions on provider/model metadata, and claim cross-context reproducibility only—not cross-provider equivalence unless a second provider actually ran.
6. Send only failed or ambiguous rows to one blind second review. That reviewer receives neither the first verdict nor the hidden expected value; clean rows receive no second review.
7. Record post-run product and temporary-instance write-set snapshots. The product snapshot must be unchanged; the temporary snapshot may contain only declared calibration effects. On every exit path, remove the complete temporary instance, profile, packets, responses, and snapshot artifacts with the temporary-run cleanup owner, then prove that the temporary root is absent. Cleanup failure is a calibration failure, never permission to retain or move temporary data into `vault://atlas/`.

## Bounded `--source-quality` mode

Accept only these cohort selectors:

- `--source-seq <N|N-M>` — select one manifest sequence or one inclusive, non-reversed sequence range.
- `--source-id <id>` — select one manifest source ID; the option is repeatable.

Require at least one selector. When both forms are present, audit their deduplicated union. Resolve selectors through `MANIFEST.md`, report unknown or malformed selectors, and never widen the cohort to unrelated source rows or artifacts. Apply the registry checks above only to rows, relations, and topic-cache fields reachable from the selected cohort.

For each selected artifact:

- Build the declared source-only evidence bundle from its canonical payload, inspected media ledger, bounds, and immutable identity fields. The checklist is not part of that bundle.
- Produce the same seven-item checklist once as the bounded semantic audit: source-only boundary, primary contribution, source support, limits/uncertainty, context neutrality, assessment coherence, and proportionality.
- Use `quality.validate_summary` with the artifact, evidence envelope, and separate checklist. Report failed IDs; do not add a score, threshold, prose match, length/citation limit, or second model pass.
- Flag generated/request/plan/repository/provider context in semantic sections, while allowing source-attributed text that is actually inside the evidence envelope.
- Flag `coverage: complete` when any canonical range or meaning-critical asset was truncated, omitted, unavailable, or unread.
- Flag full-commit-pinned GitHub payloads scored `moving`; `adopt` without high evidence, high practicality, stable payload, and no unresolved validation caveat; and thin authoritative primary mechanisms scored `low`.
- Compare Assessment Notes by signal after trimming and collapsing whitespace. Flag an identical nonempty note repeated in at least two artifacts and in more than half of the requested cohort.
- Require source-local locators for consequential concrete claims when available. Flag missing high-evidence locators, malformed/nonmatching relation verifier reasons, candidate-list-only Notes, and media links that are not the exact successfully fetched assets.
- Check header/frontmatter agreement, required sections, canonical/source/media URLs, semantic/post-draft boundaries, context perturbation, proportional concision, route/manifest/relation consistency, and all seven checklist invariants.

Report every finding with the artifact or registry path plus a section, row, or line anchor. Do not auto-repair, even when the correction appears mechanical.

## Output

Return a read-only audit report with the requested cohort, clean/issue status, finding counts by check, and concrete failing paths, anchors, or row identifiers. Calibration output additionally names the two packet families, pilot/concurrency outcome, exact-validation findings, metadata-only execution record, product/temp write-set comparison, and cleanup result.
