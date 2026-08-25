# Atlas source-topic routing architecture

**Datetime**: 2026-08-24-0841
**Authority kind**: local-authority
**Scope**: Atlas sourced-artifact taxonomy metadata, topic routing, empty-topic freshness, refresh provenance, and the migration-safe framework changes needed to improve them
**Summary**: Refine the source-to-topic routing contract so newly created topics remain useful without existing evidence, future sources deterministically create explainable pending work, and richer source metadata improves recall without weakening canonical taxonomy or write safety.
**Status**: PENDING

## Context

The request is to review and improve how Atlas source artifacts support creation and refresh of research topics, including topics whose domain, subdomain, tags, or aliases do not yet exist. The current framework already creates an evidence-empty topic shell, records `last_synthesized` as null, derives dirty state from canonical pending relation edges, exposes dirty count and stable pending edge IDs, and requires refresh to consume the complete pending set. The implementation gap is routing recall and explainability: source worker schema version 1 permits one domain, one subdomain, at most three unscored tags, and unscored aliases/candidate terms; public topic-create version 2 accepts aliases/include/exclude terms but always writes empty canonical tags; candidate matching ignores candidate terms and uses only exact domain/subdomain/tag overlap plus topic phrase rules.

The completed archived taxonomy-closure plan is historical evidence, not authority for this new outcome. The active OMP session `01a03264-33d2-7753-b897-0277dfdc00f0` has implemented a repository-only source-taxonomy remediation target and is still in high-consequence independent verification. Let that session finish; do not halt it. This plan may perform read-only decision work concurrently, but no repository, framework-sync, bound-vault, migration, or research write may start until that session reaches a terminal verdict and this plan is rebound to its final immutable target.

## Grounded design baseline

- Keep each topic single-homed under exactly one canonical domain/subdomain pair. That pair is topic identity and path authority, not the complete retrieval taxonomy. Use canonical tags plus topic-local routing terms for overlap; allow a source to record one primary domain and multiple secondary-domain/subdomain observations through the plural fields already present in source artifacts.
- Do not put source-specific confidence on global `VOCAB.md` aliases. A vocabulary alias means exact canonical identity and is shared by every source/topic; making it exhaustive increases ambiguity and fail-closed resolution conflicts. Put open-world, source-local discovery phrases in a new scored routing-term surface and keep unresolved identity collisions in non-routing `candidate_terms`.
- Reuse Atlas's existing ordinal `high|medium|low` scale instead of model-generated percentages. Percentages imply calibration the framework does not have. The candidate design to test is `support_count: 3 -> high`, `2 -> medium`, `1 -> low` from three independent source-only classifications; only high/medium terms participate in cheap candidate matching, while low terms remain inspectable metadata for later curation/resummarization and never create a pending edge by themselves.
- Preserve the current two-stage route: deterministic cheap matching creates only a bounded candidate packet, then the source-topic verifier decides inclusion and records relation, impact, confidence, and evidence-shaped reason. Classification confidence controls candidate recall; relation confidence continues to describe verified source-topic relevance. Never conflate them.
- Preserve the relation-free empty topic shell as `current`, `insufficient`, and `last_synthesized: null`. Creation must also persist approved topic aliases, canonical tags, include terms, and exclude terms so both historical-source backfill and future source-centric routing can find it. Do not create an empty dated pass; passes remain research/refresh provenance.
- Preserve `RELATIONS.md` as pending-evidence authority and `TOPICS.md` as its derived cache. Add explicit refresh provenance only if it binds one disposition for every pending edge (`incorporated` or `reviewed-no-change`) and requires exact set equality before commit; do not invent another dirty flag, queue, index, or background matcher.
- Treat richer metadata as a versioned schema change. Repository contracts/runtime, a separately approved living-state migration, and any network-backed resummarization/enrichment of existing sources are distinct effects. The migration may preserve existing semantics but must not invent new tags, aliases, or confidence; existing sources gain richer semantic metadata only through separately approved resummarization.

The three-worker candidate is not assumed correct merely because it has three votes. The documented grilling stage must compare it against a single richer classifier on portability, cost, semantic diversity, and deterministic aggregation. If the panel is retained, it remains three owner-local non-authoritative semantic workers feeding one deterministic aggregate packet into `source.prepare`; it does not add owners, helper-owner chains, vault access, or write authority.

## Required correctness repairs

- Close the changed-content freshness hole in `scripts/atlas_state.py::reduce_event`. A changed-hash `source-upsert` currently supersedes old pending edges and recomputes the affected topic to `current` before the separate route transaction runs; an already-applied relation can therefore point at an overwritten source artifact while the topic appears current. The specification must create deterministic invalidation work for every affected applied topic at source commit, keep those topics non-current through route failure/no-match, and define how refresh records evidence removal or no-longer-relevant review. Do not solve this with an owner-only check or by hiding the status interval.
- Make refresh eligibility a state-owned invariant. `refresh-start` currently accepts a `current` topic with an empty edge list because it checks only equality with the pending set. Add one pure preparation/eligibility seam that derives a nonempty complete ordered pending set from `topic.inspect`, and reject current/empty refresh both before transaction preparation and inside the reducer.
- Make canonical topic tags one synchronized value across the public create request, `VOCAB.md`, `TOPICS.md`, topic `INDEX.md`, research identity/post-validation, and candidate-scope hashing. Current create writes empty topic tags and current research identity omits canonical tags, so frontmatter tags can diverge without improving future matching.
- Add an end-to-end zero-match proof: create an absent topic and missing parent taxonomy, return no historical candidates, keep the shell `current`/`insufficient` with null synthesis and no relation/pass, then ingest a matching source and observe one stable pending edge, exact dirty count, and status output. Existing tests prove the pieces but not this sequence.
- Decide explicitly how existing same-hash sources gain richer metadata. Current explicit resummarization preserves living taxonomy when the content hash is unchanged. The recommended cutover permits an explicitly approved resummarize to replace classification/routing metadata from fresh capture while routine same-hash checks remain metadata-preserving; a migration alone may only project existing values and cannot invent semantic enrichment.
- Include one bounded topic-scope revision path only if the confirmed requirements include post-create alias/tag/include/exclude updates. That path must preserve topic ID/domain/subdomain/path, bind a new routing-scope hash, rescan historical active sources through `source.candidates_for_topic`, and use the existing route transaction. Moving a topic between domain/subdomain paths remains a separately designed migration, not an alias/tag update.

## Route and assurance

1. `grill-with-docs`
2. `dev-requirements`
3. `dev-specification`
4. `dev-ticketing`
5. `dev-implementation`
6. `dev-verification`
7. `dev-code-review`
8. `dev-continual-learning`
9. `completion-presentation`

Use high-consequence assurance: this outcome changes canonical Markdown state, source/topic schemas, public topic-create semantics, freshness transitions, migration behavior, and recovery-sensitive write sets. Use one serialized implementation lineage because the contracts, reducers, façade, owners, and tests overlap; do not fan out repository edits or add `dev-integration`.

## Approach

1. **Settle the architecture decision frontier with repository evidence.** `grill-with-docs` starts from this plan's grounded baseline and obtains one user-confirmed immutable decision artifact. It must resolve: single classifier versus exactly three independent source-only classifiers; aggregation/quorum/failure behavior; confidence semantics and routing threshold; bounded canonical tags versus open-world routing terms; singular topic placement versus plural source observations; topic tag/alias generation; same-hash resummarization enrichment; post-create topic-scope revision; empty shell versus empty pass; changed-hash invalidation; and refresh disposition provenance. Recommend the three-worker `support_count` design, ordinal confidence, medium threshold, singular topic placement, plural source observations, shell-without-pass, and no global alias confidence. No model worker receives vocabulary, topic, relation, path, identity, transaction, or write authority.
2. **Convert the confirmed decisions into observable requirements.** `dev-requirements` names acceptance for new-topic creation with missing taxonomy and zero sources; historical-source backfill; future source ingestion; low-confidence non-routing metadata; exact dirty/status evidence; complete refresh consideration; canonical topic-tag synchronization; changed-source invalidation; routine versus explicit resummarization; and any confirmed topic-scope revision. It separates repository behavior, migration-capability behavior, living migration, framework sync, and network resummarization into distinct effects.
3. **Specify one versioned clean cutover.** `dev-specification` re-reads the predecessor session's terminal target and defines the exact source-worker packet, deterministic aggregation packet, source-artifact metadata, topic-create request, topic routing-scope identity, relation invalidation/disposition data, reducer events, façade operations, owner procedures, transaction targets/order, historical journal decoders, migrations, recovery, and test seams. Reuse `resolve_vocabulary_proposals`, `source.prepare`, `source.candidates_for_topic`, `topic.inspect`, the relation/TOPICS reducers, `index.create_topic`, and generic transactions. Do not add a second vocabulary store, embedding index, queue, helper owner, public command, direct vault patch, or compatibility alias. If the public nested topic request or persisted source schema changes, give the new current shape a new version and keep older shapes only inside immutable historical recovery.
4. **Derive an acyclic vertical ticket graph.** `dev-ticketing` separates the correctness slice (changed-hash invalidation and refresh eligibility), enriched source classification/aggregation, synchronized topic routing metadata and zero-match behavior, owner/façade cutover, and versioned migration capability. Preserve one shared-lineage implementation order for overlapping files. Living migration apply, instance sync, and network resummarization are follow-on effect tickets with their own approvals, not dependencies that block repository completion.
5. **Implement contracts before mechanics.** `dev-implementation` first updates `.agents/ARCHITECTURE.md`, then `atlas-core` contracts/schemas/templates/recipes, then deterministic runtime modules and generated operation catalog, then `/atlas-ask` and owner resources, then focused changed-contract tests/evals. Migrate every active caller in the same lineage; remove obsolete current request/schema paths; retain only version-selected historical decoders required by immutable journals. Use a state-owned refresh-preparation seam and reducer defense in depth. Persist one aggregate classification packet, never worker transcripts.
6. **Prove behavior at the immutable repository target.** The implementation owner runs focused behavior checks and the full Atlas suite once, removes every temporary profile artifact, and emits an acceptance-to-smoke map. Independent verification reruns impacted proof at the exact target, final review checks Standards and Specification once, and continual learning records only a qualifying durable rule/contract gap. `completion-presentation` is a terminal marker, not a dispatched owner.

## Tasks

- [ ] T1. Settle source-topic architecture decisions
  - Owner: `grill-with-docs`
  - Receiver: `dev-ask`
  - Intent: Confirm the smallest useful routing model and every human-owned semantic boundary.
  - Methods: `none`
- [ ] T2. Establish observable routing requirements
  - Owner: `dev-requirements`
  - Receiver: `dev-ask`
  - Intent: Bind complete behavior, acceptance, scope, constraints, and separately gated effects.
  - Methods: `none`
- [ ] T3. Specify versioned metadata and freshness contracts
  - Owner: `dev-specification`
  - Receiver: `dev-ask`
  - Intent: Define exact interfaces, state transitions, migration seams, recovery, and proof boundaries.
  - Methods: `none`
- [ ] T4. Derive the vertical implementation graph
  - Owner: `dev-ticketing`
  - Receiver: `dev-ask`
  - Intent: Produce dependency-complete tickets without splitting the shared mutation lineage.
  - Methods: `none`
- [ ] T5. Implement the repository cutover
  - Owner: `dev-implementation`
  - Receiver: `dev-verification`
  - Intent: Deliver every approved contract and behavior without living-instance or shipping effects.
  - Methods: `none`
- [ ] T6. Independently verify the immutable target
  - Owner: `dev-verification`
  - Receiver: `dev-code-review`
  - Intent: Produce a fresh aggregate verdict for every acceptance criterion and prohibited effect.
  - Methods: `none`
- [ ] T7. Review standards and specification
  - Owner: `dev-code-review`
  - Receiver: `dev-continual-learning`
  - Intent: Assess the exact verified target without repair or scope expansion.
  - Methods: `none`
- [ ] T8. Curate eligible engineering learning
  - Owner: `dev-continual-learning`
  - Receiver: `dev-ask`
  - Intent: Retain only a severe, recurring, or otherwise qualifying durable lesson.
  - Methods: `none`

## Critical files & anchors

- `.agents/ARCHITECTURE.md` — canonical source/topic write sets, worker ownership, freshness transitions, migration authority, and the direct overlap with the active remediation lineage.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — exact vocabulary resolution, source/topic schemas, candidate matching, relation transitions, topic inspection, refresh, and transaction contracts.
- `.agents/skills/atlas-core/assets/source-worker-result.schema.json` — current single unscored classification packet and the version boundary for any panel aggregate.
- `scripts/atlas_state.py` — `normalize_source_classification`, `resolve_vocabulary_proposals`, `build_source_candidates`, topic inspection, pending-set derivation, and `source-upsert|route-upsert|refresh-*` reducers.
- `scripts/atlas_index.py` — public topic-create request validation, vocabulary resolution, canonical topic tags, empty-shell rendering, transaction roles, and historical recovery.

## Verification / Done criteria

- [ ] VR1. The confirmed grilling artifact has no open frontier and explicitly accepts or rejects the three-worker panel, ordinal confidence/threshold, topic-scope revision, and empty-pass behavior.
- [ ] VR2. The requirements contract maps every requested outcome and each correctness repair in this plan to an observable criterion, while keeping repository, living migration, sync, resummarization, and shipping effects separate.
- [ ] VR3. The specification fixes every schema version, field, enum, cap, normalization/order rule, quorum/failure rule, event, state transition, transaction target/order, migration, recovery path, historical decoder, and caller; a fresh implementer has no design choice.
- [ ] VR4. The ticket graph is acyclic, retains one shared repository lineage, names exact acceptance ownership, and leaves all bound-instance effects separately gated.
- [ ] VR5. From the repository root with no bound profile or credentials, run `python3 -m unittest tests.test_atlas_state tests.test_atlas_source tests.test_atlas_index tests.test_atlas_research tests.test_atlas_tool tests.test_atlas_harness_surface`; all focused contract tests pass and temporary local profiles leave no residue.
- [ ] VR6. Run `python3 scripts/atlas_tool.py capabilities` and `python3 scripts/atlas_tool.py capabilities --all`; both emit valid version-2 JSON envelopes and the exact generated lifecycle/internal operation inventory specified by T3.
- [ ] VR7. Run `python3 -m unittest discover -s tests -p 'test_atlas_*.py'`; the complete Atlas suite passes at the immutable implementation target.
- [ ] VR8. New behavior proof creates a topic with missing compatible domain/subdomain/tag vocabulary and zero candidates, observes `current`/`insufficient`, null synthesis, zero relations and no pass, then ingests a medium-or-high matching source and observes exactly one stable pending edge, dirty count one, and status evidence. A low-only match creates no edge but remains inspectable metadata.
- [ ] VR9. Freshness proof starts with an applied source-topic relation, changes the source hash, and shows the topic never becomes answerable as current before deterministic invalidation/reroute/refresh completes; a route no-match or failure cannot silently restore a stale answer.
- [ ] VR10. Refresh proof rejects current-plus-empty input without writes, binds an exact nonempty pending set and one disposition per edge, rejects set/revision drift, and on success applies exactly that set to one pass and derives zero pending edges/current state.
- [ ] VR11. Metadata proof shows canonical topic tags remain byte-consistent across request, vocabulary, TOPICS, topic index, inspection/research identity, and candidate hashing; permutation of valid classifier outputs yields byte-identical aggregate metadata and candidate facts.
- [ ] VR12. Independent verification returns `PASS` for every criterion and prohibited effect at one immutable target; final Standards and Specification review returns approved with no blocker; learning settles; no framework sync, living migration/apply, network resummarization, deployment, release, or shipping occurs.

## Assumptions & contingencies

- The active remediation session may continue through its read-only verification/review/curation tail. Before T3 binds technical authority—and always before T5 writes—read its terminal handoff and final digest map. If its target differs from provisional `sha256:b61b506d9af0301f6f3435cb6c262ddc20c1072698fa83e91363de530d4432fc`, re-read every changed overlapping contract/runtime file; a material semantic conflict returns to `dev-ask` for reapproval, while unrelated byte drift is rebound without replaying T1.
- Existing legal `VOCAB.md` alias overlap remains accepted unless the confirmed decision artifact explicitly changes global identity semantics. If it changes, T3 must add a separate candidate-bound vocabulary migration; implementation must not silently tighten validation against existing instances.
- If exactly three independent schema-bound semantic completions are not available through a contract-equivalent runtime capability, stop for material reapproval. Do not silently substitute one classifier, self-clone one output, weaken quorum, or let the parent agent invent missing votes.
- Repository implementation may add read-only preview and separately approved apply/recovery capabilities for the new schema, but this plan authorizes no `vault://atlas/` mutation, instance framework sync, live preview/apply, credential use, source fetch, resummarization wave, deployment, release, commit, push, or other shipping effect.
- If T1 confirms routing-metadata updates after topic creation, use a fixed-identity topic-scope revision as described above. A request to change topic ID/domain/subdomain/path is a different migration outcome and returns to `dev-ask`; it is never folded into retargeting.
