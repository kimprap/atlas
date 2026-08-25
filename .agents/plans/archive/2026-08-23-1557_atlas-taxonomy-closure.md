# Atlas taxonomy closure migration

**Datetime**: 2026-08-23-1557
**Authority kind**: local-authority
**Scope**: Atlas canonical taxonomy closure, legacy-state migration, vocabulary-aware topic creation, actionable candidate findings, owner-result semantics, and deterministic fault handling
**Summary**: Close safe legacy vocabulary gaps, preserve complete blockers when closure is unsafe, and make future topic creation maintain the same invariant without widening Atlas ownership or touching a bound instance during implementation.
**Status**: DONE
**Completed At**: 2026-08-24-1131

## Objective

- Outcome: OUT-ATLAS-TAXONOMY-CLOSURE
- Observable end state: the product treats exact vocabulary bindings as a canonical invariant; exposes a deterministic read-only preview and separately approved one-target migration for legacy state; makes new topic creation insert or resolve its approved domain/subdomain atomically; and returns complete, actionable taxonomy blockers before candidate discovery. Repository implementation does not claim that a bound instance is already migrated.
- Progress signal: only a satisfied acceptance criterion or exact named blocker advances the outcome; file count, elapsed time, scaffolding, and partial test passes do not.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-USER-FIX | Direct user product authority | `conversation://2026-08-23/atlas-taxonomy-closure` | `recommended-fix-r1-2026-08-23` | The recommended root correction is selected; native review must still approve these exact plan bytes before execution. |
| AUTH-DIAGNOSIS | Read-only defect evidence | `conversation://2026-08-23/atlas-taxonomy-closure-diagnosis` | `diagnosis-r1-2026-08-23` | One unrelated active legacy source with an invalid domain binding deterministically blocks `source.candidates_for_topic`; adding the missing domain removes the failure; current transport drops the invalid row ID. |
| AUTH-ARCH-BASE | Current canonical Atlas framework baseline | `repo://.agents/ARCHITECTURE.md` | `sha256:e807877825e968966ff680cfa682da0f73109d39f37452b4086ecfde6c3ac5df` | Architecture changes are permitted only within AUTH-USER-FIX; no bound-instance synchronization, migration invocation, deployment, or shipping is authorized. |
| AUTH-REVISION | Direct user revision authority | `conversation://2026-08-23/atlas-taxonomy-closure-revision` | `revision-handoff-r1-2026-08-23` | Extend existing Atlas machinery only; correct migration/result/snapshot/parent/topic-role details; rerun preflight and obtain a new approval identity before T1. |
| AUTH-REVISION-2 | Direct user revision authority | `conversation://2026-08-23/atlas-taxonomy-closure-revision-2` | `revision-handoff-r2-2026-08-23` | Split nested, façade, and owner terminals; preserve rejected blocker previews; rerun preflight and obtain a new approval identity before T1. |

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-CLOSURE | `AUTH-USER-FIX@recommended-fix-r1-2026-08-23` | Require exact `VOCAB.md` ID/type/parent bindings for every `TOPICS.md` row and every active MANIFEST-selected source artifact; `candidate_terms` remain explicitly noncanonical. |
| DEC-EXTEND-ONLY | `AUTH-REVISION@revision-handoff-r1-2026-08-23` | Extend the existing matcher, candidate lock, one-target migration CAS/rollback, generic topic transaction, three-field finding envelope, front door, and three owners. Add no journal, recovery operation, owner, or second taxonomy workflow. |
| DEC-SAFE-BACKFILL | `AUTH-REVISION@revision-handoff-r1-2026-08-23` | Backfill appends only provably missing domain/subdomain/tag rows. It never invents source kinds, edits an existing row, rewrites a source/topic artifact, guesses a parent, splits an existing ID/label/alias token space, or rejects an exact binding because its status is reserved or deprecated. |
| DEC-TWO-PHASE | `AUTH-USER-FIX@recommended-fix-r1-2026-08-23` | Migration preview is read-only. Apply requires a second fresh candidate-bound approval, regenerates the candidate, and writes only `VOCAB.md`. |
| DEC-MIGRATION-FAULTS | `AUTH-REVISION-2@revision-handoff-r2-2026-08-23` | Retain at most one forward CAS and one exact output-to-preimage rollback CAS, with no journal or recovery operation. Nested `applied` maps to façade completed/null recovery and owner completed/committed/null next. Nested `rolled-back` with proven preimage, including sibling-drift rollback, maps to façade no-write/null recovery but owner blocked/none/null next. Nested `manual-conflict` maps to façade manual-intervention/null recovery and owner blocked/unknown/null next with recovery required; drop lineage. |
| DEC-MIGRATION-CUTOVER | `AUTH-USER-FIX@recommended-fix-r1-2026-08-23` | Replace the one-time `migration.prepare_topics_lists` and `migration.apply_topics_lists` product surfaces with `migration.prepare_taxonomy_backfill` and `migration.apply_taxonomy_backfill`; archived plans remain historical, and no alias or dual current migration is retained. |
| DEC-TOPIC-REQUEST | `AUTH-REVISION@revision-handoff-r1-2026-08-23` | Public create uses one exact request-local version-2 shape; immutable embedded version-1 requests remain private to journal load/recovery and retain their original base identity formula. |
| DEC-TOPIC-STRICTNESS | `AUTH-USER-FIX@recommended-fix-r1-2026-08-23` | Source preparation retains candidate-term degradation; topic creation blocks on ambiguity, source-kind contact, wrong type, parent conflict, or resolved identity differing from its asserted canonical identity. |
| DEC-TOPIC-TRANSACTION | `AUTH-REVISION@revision-handoff-r1-2026-08-23` | Reuse the existing generic topic transaction. Unchanged VOCAB retains topic, subdomain, TOPICS order; changed VOCAB prepends one VOCAB role. All topic-create preparation, result, validation, and recovery code resolves roles instead of numeric indexes; research publication indexing is untouched. |
| DEC-FINDING | `AUTH-DIAGNOSIS@diagnosis-r1-2026-08-23` | Candidate discovery validates every locked active source before matching, carries the complete field-qualified taxonomy finding set through existing `Failure.findings`, keeps JSON in the string `detail`, and exposes only the read-only migration preview. |
| DEC-HIGH-CONSEQUENCE | `skill://dev-implementation@current` | Use one cohesive sequential implementation lineage followed once by independent verification, final review, and curation because canonical state, migration, public write effects, and recovery semantics change together. |

## Scope, non-goals, and prohibited effects

- Read surfaces: the exact Target map, named direct callers, generated operation catalog, connector capability declarations, repository scaffold bytes, and temporary local profiles created by existing tests.
- Change surfaces: architecture/core/front-door/maintain contracts; the one owner-result schema branch; strict vocabulary resolution and closure; active-source projection; taxonomy preview/apply response mapping; topic request/preparation/post-validation/recovery; candidate finding transport; research-owner procedure; focused tests and packaged evals.
- Non-goals: rewriting source artifacts or topic/index projections during migration; editing/deleting/relabeling/deprecating/reserving existing VOCAB rows; inserting `source-kind`; changing source proposal degradation; adding a fourth owner, helper-owner chain, public command, alternate root/store, background audit, automatic repair, hidden retry/rebase/force-write, migration successor, migration journal, migration recovery operation, or second taxonomy workflow.
- Clean cutover: remove active product code, catalog entries, owner/recipe references, eval expectations, and tests for `prepare_topics_list_candidate`, `TopicsListCandidateResult`, `migration.prepare_topics_lists`, `migration.apply_topics_lists`, the old approval literal, and migration `lineage`; replace the old three-document/no-fourth-document topic-create clauses. Do not edit archived plans or ADR history.
- Prohibited effects: no `vault://atlas/` write, real migration preview/apply, bound framework sync, non-development profile write, credential use, network acquisition, deployment, release, or Git shipping action during implementation or verification. A real instance starts later through a fresh `/atlas-ask` preview and separately approved apply.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-CONTRACT | Repository contract edit | AUTH-USER-FIX, AUTH-ARCH-BASE, AUTH-REVISION | Only TGT-ARCH, TGT-CORE, TGT-RESULT, TGT-FRONTDOOR, and TGT-MAINTAIN; reversible before shipping. |
| EFF-RUNTIME | Repository runtime and packaged-owner edit | AUTH-USER-FIX, AUTH-ARCH-BASE, AUTH-REVISION | Only TGT-STATE, TGT-SOURCE, TGT-INDEX, TGT-TOOL, and TGT-RESEARCH-OWNER; no living I/O. |
| EFF-TEST | Repository fixture/eval edit and temporary local mutation | AUTH-USER-FIX, AUTH-REVISION | Only TGT-EVAL, TGT-TEST-PURE, and TGT-TEST; temporary profiles remove every artifact, registry, transaction record, and directory. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-CLOSURE | Canonical source/topic references, status, token, and parent semantics | T1 | `atlas-taxonomy-closure-r4` | T1, T2 |
| CONTRACT-RESOLVER | One proposal matcher with source-degrade and topic-block policies | T1 | `atlas-vocabulary-resolution-r4` | T1, T2 |
| CONTRACT-MIGRATION | Candidate-locked preview, rejected blockers, one-target apply, bounded inline rollback, layered terminals | T1 | `atlas-taxonomy-backfill-r5` | T1, T2 |
| CONTRACT-RESULT | Blocked owner results without invented recovery for known-none and unknown effects | T1 | `atlas-migration-result-r5` | T1, T2 |
| CONTRACT-FINDING | Complete three-field façade findings plus preview-only guidance | T1 | `atlas-taxonomy-finding-r4` | T1, T2 |
| CONTRACT-TOPIC | Public version-2 create, optional VOCAB-first target, role-based recovery, private v1 decode | T1 | `atlas-topic-vocab-create-r4` | T1, T2 |
| CONTRACT-COMPAT | Singular public surface, unchanged source behavior, transaction reuse, historical journal identity | T1 | `atlas-taxonomy-compat-r4` | T1, T2 |

### Canonical closure

- Active sources are every MANIFEST row whose `Status` is exactly `active`, including stale-hash rows, ordered by numeric `Source seq`. Archived rows and artifacts are not observations and are never read.
- Each active artifact's nonblank `source_kind` must name an exact `source-kind` ID; nonblank `primary_domain` and every `secondary_domains[i]` must name exact `domain` IDs; every `subdomains[i]` must name exact `subdomain` IDs; every `canonical_tags[i]` must name exact `tag` IDs. `candidate_terms` never participates.
- An exact ID/type/parent binding remains valid when the VOCAB row status is `active`, `deprecated`, or `reserved`; status is not a closure predicate. Every inserted row has status `active`.
- A topic subdomain observation has allowed-parent set `{Domain}`. A source subdomain observation has the nonblank IDs in `{primary_domain} ∪ secondary_domains` as its allowed-parent set.
- For an existing subdomain row, inspect every topic/source observation containing that ID independently. The row conflicts if its `Parent` is absent from any one observation's allowed-parent set; topic observations therefore still require exact `Parent == Domain`. Never weaken this to membership in the union of some observations.
- For a missing subdomain row, intersect every observation's allowed-parent set. Insert only when the intersection is exactly one domain ID and that domain already exists with the right type or is an earlier domain insert in the same candidate.
- A missing observed ID whose ASCII-lowercased ID token overlaps any existing row's ID, label, or allowed alias is not safely insertable, regardless of row status. Return a conflict rather than create a second live token identity.

### Shared resolver

Extend the state-owned matcher rather than adding another:

```python
resolve_vocabulary_proposals(
    vocab_text: str,
    classification: Any,
    *,
    conflict_policy: Literal["candidate-term", "block"],
) -> tuple[str, dict[str, Any] | None, list[Finding]]
```

- Reuse `normalize_source_classification`, `_classification_token`, `_proposal_tokens`, `_record_tokens`, `_new_vocab_row`, the canonical table codec, and current row rendering. Matching continues across every status.
- `resolve_source_classification` remains the wrapper with `conflict_policy="candidate-term"` and retains current candidate-term degradation byte-for-byte.
- `atlas_index` calls the same seam with `conflict_policy="block"` for domain/subdomain only. Zero match inserts; one compatible match reuses its ID; multi-match, source-kind contact, wrong type, parent mismatch, or a result differing from the request's asserted outer ID returns `TOPIC_VOCABULARY_CONFLICT`, original VOCAB bytes, and no plan.
- Migration needs exact persisted IDs because it does not rewrite source/topic artifacts. It reuses the same token functions for collision detection but never remaps an observed missing ID to another row; any overlap returns `TAXONOMY_BACKFILL_TOKEN_CONFLICT`.

### Taxonomy migration

Replace `TopicsListCandidateResult` and `prepare_topics_list_candidate` with:

```python
prepare_taxonomy_backfill_candidate(
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    vocab_text: str,
    source_projections: Mapping[str, Mapping[str, Any]],
) -> TaxonomyBackfillCandidateResult
```

- `source_projections` is keyed by the exact relative MANIFEST `Artifact` value and uses `atlas_source.candidate_artifact_projection` extended with `source_kind`. The reducer requires exactly the locked active MANIFEST artifact set and proves source ID, canonical URL, content hash, artifact revision shape, and field shapes before taxonomy observation.
- Observe every registered TOPICS row and every locked active source under Canonical closure. `RELATIONS.md` participates only in complete-registry validation, candidate inventory binding, sibling-staleness checks, and post-validation; relation rows never produce taxonomy observations.
- Invalid IDs return `TAXONOMY_BACKFILL_ID_INVALID`; multi-type or wrong-type IDs return `TAXONOMY_BACKFILL_TYPE_CONFLICT`; missing source-kind returns `TAXONOMY_BACKFILL_INSERT_UNSUPPORTED`; token overlap returns `TAXONOMY_BACKFILL_TOKEN_CONFLICT`; missing subdomain intersection size other than one returns `TAXONOMY_BACKFILL_PARENT_AMBIGUOUS`; an existing subdomain parent that fails any observation returns `TAXONOMY_BACKFILL_PARENT_CONFLICT`.
- Any blocker returns every normalized observation finding and no candidate. Each detail is canonical compact sorted-key JSON retaining `field`, `row_id`, `expected_type`, `observed_state`, `observed_type`, `expected_parent_ids`, and `observed_parent`.
- Missing safe rows append once in fixed type order `domain`, `subdomain`, `tag`, then UTF-8 byte order by ID. Each change is exactly `{"id","type","label","parent","allowed_aliases","status","notes"}` with label equal to the observed ID, aliases `[]`, status `active`, notes empty, blank domain/tag parent, and the single proven subdomain parent.
- Preserve every existing VOCAB row and unmanaged byte, newline convention, and final-newline state. Candidate output fully validates; replay returns byte-identical `state:"no-op"`.
- `migration.prepare_taxonomy_backfill` accepts exactly `{}` and reuses the candidate-lock pattern in `_source_candidates_for_topic`: read only MANIFEST preliminarily, parse it with `validated_manifest_rows`, derive every active artifact URI as `vault://atlas/` plus its relative `Artifact`, then perform one connector `consistent_read` across MANIFEST, TOPICS, RELATIONS, VOCAB, and that exact artifact superset. Reject unless the locked active set equals the preliminary set; build projections in numeric source-sequence order.
- Both migration operations declare and call the connector `consistent_read` capability; apply additionally requires the existing mutation-session and conditional-replace capabilities. Update operation catalog metadata and every migration test double to expose the same methods instead of falling back to `_read_documents_stable`.
- Inventory is exactly:

```json
{
  "manifest_revision": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "topics_revision": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "relations_revision": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "vocab_revision": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
  "artifact_revisions": [
    {
      "path": "vault://atlas/summaries/sources/artifacts/2026/2026-07/2026-07-28--000001-example--synthetic.md",
      "revision": "sha256:4444444444444444444444444444444444444444444444444444444444444444"
    }
  ]
}
```

- A successful preview returns exactly `{state,binding,inventory,candidate}` with either `state:"no-op"` and `candidate:null`, or `state:"candidate"` and candidate fields exactly `candidate_sha256,path,preimage_text,text,preimage_revision,output_revision,changes,approval_literal`. Any taxonomy blocker follows the existing `_reject` path with complete findings and returns façade `ok:false`, disposition `rejected`, and `recovery:null`; it returns no successful preview object, approval, or write. Hash canonical compact sorted-key UTF-8 JSON without trailing LF for `{version:1,binding,inventory,path:VOCAB,output_revision,changes}`. Approval is `APPLY ATLAS TAXONOMY BACKFILL {instance_id} {candidate_sha256}`.
- `migration.apply_taxonomy_backfill` accepts exactly `{instance_id,candidate_sha256,approval}`, regenerates the same stable snapshot/candidate, and rejects approval, binding, path, inventory, change, or output drift before mutation with zero CAS.
- Apply performs at most one forward VOCAB CAS. Post-validation rereads the complete inventory; proves unchanged MANIFEST/TOPICS/RELATIONS/artifact revisions, exact VOCAB output, complete document and closure validity, and a second reducer pass of no-op.
- The nested result is exactly `{version,state,binding,candidate_sha256,inventory,forward,post_validation,rollback,findings}` with no `lineage`. State is `applied`, `rolled-back`, or `manual-conflict`; `forward` is `{attempted,status,revision,acknowledged_revision,classification}`; `post_validation` is `{attempted,inventory,ok,findings}`; optional rollback is `{attempted,status,revision,acknowledged_revision,preimage_confirmed}`.
- Any acknowledgement, reread, or post-validation failure classifies current VOCAB as exact input, exact output, or other. Exact output permits one output-to-preimage rollback CAS; exact input is already rolled back; other bytes or unproved rollback are manual conflict. Proven preimage remains `rolled-back` even when the triggering finding was sibling drift; do not port the old lineage overlay that relabeled such a rollback as unknown.
- Add `_migration_result_response(op, result)` and make `_result_response` delegate to it only for `migration.apply_taxonomy_backfill` before reading generic `status`; never pass migration `state` through transaction-status mapping. The dedicated adapter emits façade `completed` for `applied`, `no-write` for `rolled-back`, and `manual-intervention` with nested findings for `manual-conflict`. Every branch has `recovery:null`; manual conflict is never a successful envelope.
- Owner mapping is frozen by layer: applied → `outcome:"completed"`/`effect:"committed"`/`next:null`; rolled-back with proven preimage, including sibling-drift rollback → `outcome:"blocked"`/`effect:"none"`/`next:null`; manual-conflict → `outcome:"blocked"`/`effect:"unknown"`/`next:null`, at least one blocked item with `recovery_required:true`, and no invented operation or identity.
- Replace the two old migration literals in active code, catalog, recipes, owners, evals, and tests. Discovery remains exactly 30 lifecycle, 13 internal, and 43 total operations. Archived plans and ADR history remain unchanged.

### Owner result and front-door consumption

- In architecture, cadence, CLI recipes, `/atlas-ask`, and `atlas-maintain`, replace every migration promise of “commit or exact recovery.” This one-target apply has inline rollback only and never returns a recovery operation.
- Add exactly one owner-result schema alternative: `outcome:"blocked"`, `effect:"unknown"`, blocked items whose `recovery_required` is `true`, and `next:null`. Keep the existing recoverable branch requiring nonnull `{operation,identity}` for `partial` or `unknown`; do not permit `partial` with null `next`.
- `recovery_required:true` is a human/manual-intervention flag, not executable authority. Front-door blocked-result consumption invokes recovery only when `next` is a nonnull schema-valid recovery object; with `next:null`, it stops even when an item says recovery is required.
- `atlas-maintain` consumes migration states exactly as frozen above. Repair and every nonmigration journal-backed workflow retain their existing exact recovery contracts.
- Front-door and research-owner Goal/Effect text for create/research names the possible insert-only domain/subdomain VOCAB rows in the same approved topic-create transaction.

### Candidate finding transport

- Extend `validate_source_taxonomy` and every caller with `source_kind`; preserve scalar/list field names and indices; distinguish `missing`, `wrong-type`, `parent-conflict`, and `invalid-id`; and apply the per-observation parent rules.
- Each public finding remains exactly `{code,path,detail}`. `path` is the logical artifact URI. `detail` remains a string containing canonical compact sorted-key JSON with exact keys `expected_parent_ids`, `expected_type`, `field`, `observed_parent`, `observed_state`, `observed_type`, and `row_id`; `atlas_cli.normalize_findings` is unchanged.
- Extend `SourceCandidateError` with an optional complete normalized `Finding` tuple while preserving code/path/detail for non-taxonomy snapshot errors. `build_source_candidates` validates and accumulates taxonomy findings for every locked active source before any eligibility match, then raises once. `_source_candidates_for_topic` passes `_owner_findings(exc.findings)` into the already-existing `Failure.findings`.
- A taxonomy-only failure has `ok:false`, disposition `rejected`, no candidates, top-level `recovery:null`, and exact result `{"migration_preview":{"operation":"migration.prepare_taxonomy_backfill","args":{}}}`. It exposes no apply arguments, approval literal, transaction identity, owner chain, or automatic maintain dispatch.

### Topic create and recovery

Public `index.create_topic` accepts only this closed request-local version-2 shape:

```json
{
  "version": 2,
  "topic_id": "new-topic",
  "topic_path": "vault://atlas/summaries/research/test/test-subdomain/topics/new-topic/INDEX.md",
  "domain": "test",
  "subdomain": "test-subdomain",
  "vocabulary": {
    "domain": {"id": "test", "label": "Test", "aliases": []},
    "subdomain": {"id": "test-subdomain", "label": "Test subdomain", "aliases": [], "parent": "test"}
  },
  "canonical_title": "New topic",
  "aliases": [],
  "include_terms": ["test"],
  "exclude_terms": [],
  "related_topic_ids": [],
  "status": "active",
  "coverage_state": "insufficient",
  "confidence": "low",
  "refresh_model": "same-as-topic-creation",
  "created_on": "2026-08-02"
}
```

- Keep every current scalar/list/date/path constraint. `vocabulary` is required and closed. Proposal IDs may differ from outer IDs only when one compatible existing row resolves to those exact asserted outer IDs; zero-match proposal IDs equal outer IDs. The subdomain proposal parent may equal the proposal-domain ID or resolved outer domain ID.
- Owner construction preserves explicitly retained labels and aliases. Otherwise label equals the approved ID and aliases are `[]`; the reducer invents no presentation semantics.
- Change the pure signature to `prepare_topic(request, manifest_text, topics_text, relations_text, vocab_text, subdomain_text, topic_text_or_missing)`. `_index_paths` and `_index_prepare` always snapshot VOCAB and pass it to the reducer.
- Add one pure `topic_target_roles(request, target_paths)` validator in `atlas_index`; no equivalent exists because current callers use indexes. It returns exact present role/path pairs for either topic/subdomain/registry or vocab/topic/subdomain/registry and rejects any missing, duplicate, extra, reordered, or request-inconsistent path.
- For an absent topic, unchanged VOCAB yields topic → subdomain → TOPICS targets; changed VOCAB yields VOCAB → topic → subdomain → TOPICS. Strict vocabulary conflict returns `TOPIC_VOCABULARY_CONFLICT` and no targets. Compatible existing-topic confirmation requires unchanged valid closure; if insertion would be needed, return preview-only migration guidance with no plan.
- `TopicPlan` properties, output maps, event creation, `load_topic_binding`, `_index_bind`, `_index_post_validator`, `_index_transaction_result`, receipt/revision maps, terminal validation, successor checks, and `index.recover_topic` use the role map rather than target indexes. Fix the current decoder's rejection of a missing subdomain input: topic input is missing, subdomain input may be missing or present, TOPICS input is present, and VOCAB input is present only in the four-target form.
- `_index_rank` orders VOCAB `0`, topic `1`, subdomain `2`, TOPICS `3` for generic apply and reverse rollback. Do not use rank values to identify result or post-validation roles. Do not edit `atlas_research.py`: its `plan.targets[0]` pass, `[1]` topic, `[2]` subdomain publication contract is a different four-target research plan.
- `TopicPostValidation` stores frozen expected VOCAB bytes: appended output for four-target plans, unchanged snapshot bytes for three-target plans. `_index_post_validator` always reads VOCAB, proves those bytes and closure, then reads topic/subdomain/TOPICS by role. VOCAB is a write target only when bytes changed.
- Split public request validation from immutable-record decoding. `_validate_request` accepts exact version 2 only. Add private `_decode_journal_request`, called only by `load_topic_binding`/recovery, which validates canonical embedded version-2 records or the exact historical version-1 15-key shape without calling the public validator. Public create never accepts or advertises v1.
- Keep event-record version 1, outer recovery version 1, `TOPIC_OWNER_ID`, namespace formula, and `topic-post-v1` unchanged. `topic_base_transaction_id` requires exact three/four role sets for v2 using the existing canonical `{owner,request_sha256,target_paths,input_identities,output_sha256s}` payload. Its v1 branch requires three historical targets and produces byte-identical old base IDs from the old target-path/input-identity formula. Emit no new v1 request.

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-ARCH | `.agents/ARCHITECTURE.md` mode/write ownership, canonical state, source/topic/migration lifecycle | T1 | `sha256:e807877825e968966ff680cfa682da0f73109d39f37452b4086ecfde6c3ac5df` | all product contracts and owners | AC-ARCH |
| TGT-CORE | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`; `operating-cadence-and-guardrails.md`; `agent-cli-recipes.md`; `research-library-templates.md` | T1 | `sha256:3509f26fbc9031fa64fc27915e3e8b0e70a801860ac7a6ceb23c17720229189c`; `sha256:78770c2c7719f7f3aa6fab26e37e0b2a55ed527e483d2eb9785db1708b1a3396`; `sha256:a5c64c0dc3df500cf105bf8d20bdb49ab0eed8ad145a30441695ce558355e40b`; `sha256:e98fb5831d0d5c4fc2ed0114ff2d83d91f63493a5e3cf44d50422707413148f3` | reducers, façade, owners, packaged recipes | AC-ARCH |
| TGT-RESULT | `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json` blocked unknown branch | T1 | `sha256:c0aea38041b146de5adad5e16096c1ea7295d09727d8e2c444ecc1685e766214` | front-door validation and harness schema tests | AC-ARCH |
| TGT-FRONTDOOR | `.agents/skills/atlas-ask/SKILL.md` migration classification, result consumption, and Goal/Effect wording | T1 | `sha256:343b79a7d19eae4a6606ddc3a2bc8d46d37416748df14fa48f392f1b9087c05c` | `/atlas-ask` classification and packaged evals | AC-ARCH |
| TGT-MAINTAIN | `.agents/skills/atlas-ask/owners/atlas-maintain/OWNER.md` two-phase migration and state mapping | T1 | `sha256:14743aea728bf8f52ca396014fa5ade52690affb7cc214aac749b05a5f2d259a` | same-agent migrate procedure and packaged evals | AC-ARCH |
| TGT-STATE | `scripts/atlas_state.py` resolver, closure observations, candidate result, taxonomy findings | T2 | `sha256:71c805fe4a64a92b67aad96cd8adf2cffda4a2870d8dffdff1b8e482db9d0e0c` | source/index/tool and pure tests | AC-CLOSURE, AC-MIGRATION-PREVIEW, AC-MIGRATION-CONFLICT, AC-CANDIDATE-FINDING, AC-TOPIC-CREATE, AC-COMPAT |
| TGT-SOURCE | `scripts/atlas_source.py::candidate_artifact_projection` | T2 | `sha256:1189728f2f1682c2decd9e07c40473fe9167d663eccab5d5837b7156aa142d70` | candidate and migration snapshots | AC-CLOSURE, AC-MIGRATION-PREVIEW, AC-CANDIDATE-FINDING, AC-COMPAT |
| TGT-INDEX | `scripts/atlas_index.py` request validation, preparation, plan/binding/post-validation | T2 | `sha256:e1aea992d5e733fc1297692d79c08dd50e254004a3cbcf057f9af4b398bc4c26` | index façade and research fixtures | AC-TOPIC-REQUEST, AC-TOPIC-CREATE, AC-TOPIC-RECOVERY, AC-COMPAT |
| TGT-TOOL | `scripts/atlas_tool.py` consistent snapshots, catalog, migration apply response, finding context, topic adapter | T2 | `sha256:a1b24e44ab749919911e0db1b7b488dc0c8a0d9f251bea392e574240d8bb0468` | generated commands and temporary connectors | AC-MIGRATION-PREVIEW, AC-MIGRATION-CONFLICT, AC-MIGRATION-APPLY, AC-MIGRATION-FAULT, AC-CANDIDATE-FINDING, AC-TOPIC-CREATE, AC-TOPIC-RECOVERY, AC-COMPAT |
| TGT-RESEARCH-OWNER | `.agents/skills/atlas-ask/owners/atlas-research/OWNER.md` create/research Goal/Effect and taxonomy stop | T2 | `sha256:b6092c3e7c5050126b6d165ebad45e98db7baaef0fb473f1bad14491a7f932e3` | same-agent create/research procedures | AC-OWNERS, AC-COMPAT |
| TGT-EVAL | `.agents/skills/atlas-core/assets/evals/agent-tooling.json` operation, approval, create, finding, and manual-conflict cases | T2 | `sha256:3955af259518cd8e3e6bf0888dcb2943357e500d135b03338580a750286b6fe6` | packaged harness test | AC-OWNERS, AC-COMPAT |
| TGT-TEST-PURE | `tests/test_atlas_state.py`; `tests/test_atlas_source.py`; `tests/test_atlas_index.py`; `tests/test_atlas_research.py` | T2 | `sha256:4762946714a61aa2f5653c7571a831c3ff9124f89227533a8ec9f73cd72d9340`; `sha256:6267eb8482869bd474df2a087f17095607a349dddf15965dc134aa39baa8a140`; `sha256:d1ccdc3cab1becb87a79593e23e33d9e73b2ceba738e4ad46b056234bdf3687e`; `sha256:c53b512a750d6dc350cf07244b53ed51a40cdb4ffd94f4e44de1da02491b46ce` | pure snapshots and imported fixtures | AC-CLOSURE, AC-MIGRATION-PREVIEW, AC-MIGRATION-CONFLICT, AC-TOPIC-REQUEST, AC-TOPIC-CREATE, AC-TOPIC-RECOVERY, AC-COMPAT |
| TGT-TEST | `tests/test_atlas_tool.py`; `tests/test_atlas_harness_surface.py`; `tests/test_atlas_instance.py` | T2 | `sha256:5f4f0e4d1d121acf41d9c488e3e4065d726c4e4ef7c3105f0ae2632c55aedf28`; `sha256:4df0fc4740a054719ace47ec139371ef9b20c11a2bc3dcd39f82cbe84936f599`; `sha256:a41fa6de8d8404705b0af857f575e3807e63b0781b8ed73a9808efa1e1a20053` | temporary profile, catalog, schema, and fault matrices | AC-MIGRATION-PREVIEW, AC-MIGRATION-CONFLICT, AC-MIGRATION-APPLY, AC-MIGRATION-FAULT, AC-CANDIDATE-FINDING, AC-TOPIC-REQUEST, AC-TOPIC-CREATE, AC-TOPIC-RECOVERY, AC-OWNERS, AC-COMPAT |

## Execution policy

- Assurance: high-consequence
- Topology: one-owner-sequential
- Max concurrency: 1
- Isolation: none
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: one implementation worker owns every listed target in T1 then T2; unexpected semantic drift stops for exact authority rebind rather than overwrite.
- Decomposition: T1 establishes architecture and contracts; T2 performs the cohesive runtime/owner/test cutover. No helper worker or same-file parallel edit is permitted. The backend schedules `dev-verification` → `dev-code-review` → `dev-continual-learning` once after T2.
- Effect limit: EFF-CONTRACT, EFF-RUNTIME, EFF-TEST
- Orchestrator profile: one-owner-sequential

## Tasks

- [x] T1. Bind canonical closure contracts
  completed 2026-08-24-0118
  - Owner: dev-implementation worker
  - Intent: Establish one durable closure, migration, result, finding, topic-create, and topic-recovery contract; remove active migration-recovery promises before implementation.
  - Methods: none
  - Wave: W0
  - Depends on: none
  - Targets: TGT-ARCH, TGT-CORE, TGT-RESULT, TGT-FRONTDOOR, TGT-MAINTAIN
  - Contracts: CONTRACT-CLOSURE, CONTRACT-RESOLVER, CONTRACT-MIGRATION, CONTRACT-RESULT, CONTRACT-FINDING, CONTRACT-TOPIC, CONTRACT-COMPAT
  - Criteria: AC-ARCH
  - Effects: EFF-CONTRACT
  - Output: OUTP-T1
  - Receiver: dev-implementation worker
  - Verification: VR-1
  - Lineage: shared

- [x] T2. Implement taxonomy closure end to end
  completed 2026-08-24-0215
  - Owner: dev-implementation worker
  - Intent: Cut over the reducer, façade, topic transaction, research owner, evals, and tests to the approved closure contract.
  - Methods: none
  - Wave: W1
  - Depends on: T1
  - Targets: TGT-STATE, TGT-SOURCE, TGT-INDEX, TGT-TOOL, TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST-PURE, TGT-TEST
  - Contracts: CONTRACT-CLOSURE, CONTRACT-RESOLVER, CONTRACT-MIGRATION, CONTRACT-RESULT, CONTRACT-FINDING, CONTRACT-TOPIC, CONTRACT-COMPAT
  - Criteria: AC-CLOSURE, AC-MIGRATION-PREVIEW, AC-MIGRATION-CONFLICT, AC-MIGRATION-APPLY, AC-MIGRATION-FAULT, AC-CANDIDATE-FINDING, AC-TOPIC-REQUEST, AC-TOPIC-CREATE, AC-TOPIC-RECOVERY, AC-OWNERS, AC-COMPAT
  - Effects: EFF-RUNTIME, EFF-TEST
  - Output: OUTP-T2
  - Receiver: dev-verification
  - Verification: VR-2, VR-3, VR-4, VR-5, VR-6, VR-7, VR-8, VR-9, VR-10, VR-11, VR-12
  - Lineage: shared

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-ARCH | Inspect every changed architecture, core, result-schema, front-door, and maintain-owner clause; validate owner packets for applied completed/committed/null, rolled-back blocked/none/null, manual-conflict blocked/unknown/null with recovery-required items, and blocked partial/null. | One closure/resolver/migration/topic convention exists and every active “migrate then exact recovery” promise is removed. Nested applied maps to façade completed/null recovery and owner completed/committed/null next; proven preimage, including sibling-drift rollback, maps to façade no-write/null recovery but owner blocked/none/null next; manual conflict maps to façade manual-intervention/null recovery and owner blocked/unknown/null next with recovery-required items. The schema accepts the two blocked null-next owner packets and rejects blocked partial/null; journal-backed nonmigration recovery remains unchanged. | TGT-ARCH, TGT-CORE, TGT-RESULT, TGT-FRONTDOOR, TGT-MAINTAIN | T1 |
| AC-CLOSURE | Analyze multiple source projections and every topic row with exact and invalid domain, subdomain, tag, and source-kind bindings across active, deprecated, and reserved VOCAB rows. | Required IDs and types are exact; row status does not invalidate an exact binding; topic and source subdomains apply their own per-observation allowed-parent sets; candidate terms are ignored; complete field-qualified observations are deterministic. | TGT-STATE, TGT-SOURCE, TGT-TEST-PURE | T2 |
| AC-MIGRATION-PREVIEW | Preview a MANIFEST containing active, active stale-hash, and archived rows; repeat with a locked active-set mismatch, repeated missing domain/tag observations, and a missing subdomain whose allowed-parent intersection is one domain. | A preliminary MANIFEST read derives the exact active artifact superset; one connector `consistent_read` locks all four registries plus those artifacts in numeric source-sequence order; archived artifacts are never read; mismatch rejects; RELATIONS contributes validity/staleness but no observation. The successful candidate state appends each safe ID once in domain/subdomain/tag then byte-ID order, uses real MANIFEST artifact URIs, preserves unmanaged bytes/newlines, and binds the complete inventory; replay returns only successful `state:"no-op"` with `candidate:null`. Catalog requirements and migration doubles expose `consistent_read`. | TGT-STATE, TGT-SOURCE, TGT-TOOL, TGT-TEST-PURE, TGT-TEST | T2 |
| AC-MIGRATION-CONFLICT | Preview invalid IDs, one ID under multiple types, wrong-type and source-kind contacts, missing source-kind, ambiguous parent intersections, an existing subdomain parent that fails one observation's allowed set, and a missing ID overlapping an active, deprecated, or reserved row ID/label/alias token. | Every observation survives in exact findings; per-observation mismatch and every token overlap return façade `ok:false`, disposition `rejected`, and `recovery:null`; no successful preview object, candidate, approval, target, or write exists; no source, topic, registry, or transaction byte changes. | TGT-STATE, TGT-TOOL, TGT-TEST-PURE, TGT-TEST | T2 |
| AC-MIGRATION-APPLY | Apply the unchanged exact preview triple; repeat with wrong approval and drift in every inventory member. | Fresh candidate-locked regeneration precedes mutation; exactly one forward CAS targets VOCAB; acknowledgement/reread and complete closure post-validation prove output; a second reducer pass is no-op; the façade returns completed with `recovery:null`. Wrong approval or inventory drift performs zero CAS. | TGT-TOOL, TGT-TEST | T2 |
| AC-MIGRATION-FAULT | Inject forward acknowledgement, reread, sibling-drift, post-validation, rollback acknowledgement, and other-byte failures. | Exact output permits at most one output-to-preimage rollback CAS. Exact input or proven rollback stays nested `rolled-back` and façade `no-write`; unproved rollback or other bytes stays nested `manual-conflict` and façade `manual-intervention`; every envelope has `recovery:null`. No journal, recovery operation, retry, rebase, force-write, lineage, or more than two VOCAB CAS calls exists. | TGT-TOOL, TGT-TEST | T2 |
| AC-CANDIDATE-FINDING | Run candidate discovery with an unrelated active poison source under missing ID, source-kind collision, parent conflict, and two-invalid-field variants. | Discovery fails before eligibility matching or glance, returns every exact artifact/field/ID/expected/observed detail, result names only `migration.prepare_taxonomy_backfill {}`, recovery is null, and the fixture tree digest is unchanged. | TGT-STATE, TGT-SOURCE, TGT-TOOL, TGT-TEST | T2 |
| AC-TOPIC-REQUEST | Submit valid version-2 vocabulary proposals plus missing, unknown, malformed, resolved-ID-mismatch, and public version-1 create requests. | Only the exact closed v2 shape passes public validation; malformed/proposal conflicts and public v1 fail before mutation; proposal labels and aliases are preserved and the reducer invents no presentation semantics. | TGT-INDEX, TGT-TEST-PURE, TGT-TEST | T2 |
| AC-TOPIC-CREATE | Create under zero-match vocabulary; repeat with compatible exact rows in every status and a unique alias proposal resolving to asserted outer IDs; try ambiguity, type, parent, and existing-topic closure conflicts. | Changed VOCAB yields role order VOCAB/topic/subdomain/TOPICS; unchanged VOCAB yields topic/subdomain/TOPICS with no VOCAB byte change. Result, receipt, post-validation, recovery, and terminal checks resolve roles rather than rank; every unsafe case yields no plan/journal/write and preview-only guidance. | TGT-STATE, TGT-INDEX, TGT-TOOL, TGT-TEST-PURE, TGT-TEST | T2 |
| AC-TOPIC-RECOVERY | Fault three- and four-target creates after each target, include a missing subdomain input, recover a current v2 journal, and load/recover a historical v1 three-target journal. | Exact role alternatives bind and reverse rollback restores each applicable target; the missing-subdomain decoder path works; v2 recovery passes; historical v1 recovery uses the private immutable decoder and old base formula without invoking public v2 validation; event-record v1, recovery v1, owner ID, namespace, and topic-post-v1 remain unchanged; no new v1 request is emitted. | TGT-INDEX, TGT-TOOL, TGT-TEST-PURE, TGT-TEST | T2 |
| AC-OWNERS | Exercise research-owner create/research paths and packaged create, taxonomy-stop, preview/apply, and manual-conflict eval cases. | Create/research Goal/Effect names possible insert-only domain/subdomain VOCAB rows; the owner applies retained labels/defaults, stops on taxonomy findings without loading maintain, and emits no owner chain. Packaged evals preserve fresh migration approvals and manual conflict without fabricated recovery. | TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST | T2 |
| AC-COMPAT | Run existing-vocabulary confirmation/create, source ingest/resummarize/promote/reroute, candidate backfill, research publication, generic transaction recovery, catalog, instance checks, and the full Atlas suite. | Source conflict degradation and research publication indices are unchanged; existing-vocabulary topic bytes/targets stay exact; operation counts are 30 lifecycle, 13 internal, 43 total; old active migration literals and lineage are absent. `atlas_cli.py`, `atlas_research.py`, `atlas_transaction.py`, the command, source owner/schemas, scaffold, and bound-instance state remain untouched; temporary fixtures leave no residue. | TGT-STATE, TGT-SOURCE, TGT-INDEX, TGT-TOOL, TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST-PURE, TGT-TEST | T2 |

## Verification / Done criteria

- [x] VR-1. Validate contracts, result schema, and owner consumption.
  - Criterion: AC-ARCH
  - Proof class: independent verification
  - Scenario / environment / fixture: Inspect every changed architecture/core/front-door/maintain clause; validate applied completed/committed/null, rolled-back blocked/none/null, manual-conflict blocked/unknown/null with recovery-required items, and blocked-partial/null owner packets; run `python3 -m unittest tests.test_atlas_harness_surface tests.test_atlas_instance`.
  - Evidence form: Contract diff and passing suites proving one convention, removed migration-recovery promises, exact nested/façade/owner terminal mapping, accepted blocked/none/null and blocked/unknown/null, rejected blocked/partial/null, retained nonmigration recovery, and unchanged prohibited effects.
  - Target recheck: TGT-ARCH, TGT-CORE, TGT-RESULT, TGT-FRONTDOOR, TGT-MAINTAIN
  - Receiver: dev-verification

- [x] VR-2. Validate canonical closure observations.
  - Criterion: AC-CLOSURE
  - Proof class: independent verification
  - Scenario / environment / fixture: Run `python3 -m unittest tests.test_atlas_state tests.test_atlas_source` over multi-source/topic, all-VOCAB-status, wrong-type, per-observation-parent, and candidate-term fixtures.
  - Evidence form: Exact complete observation/finding tuples proving status-independent exact bindings and separate topic/source parent sets.
  - Target recheck: TGT-STATE, TGT-SOURCE, TGT-TEST-PURE
  - Receiver: dev-verification

- [x] VR-3. Validate candidate-locked taxonomy preview.
  - Criterion: AC-MIGRATION-PREVIEW
  - Proof class: independent verification
  - Scenario / environment / fixture: Run preview cases in `python3 -m unittest tests.test_atlas_state tests.test_atlas_source tests.test_atlas_tool` with active, stale-hash-active, archived, locked-set-mismatch, repeated-ID, one-parent-intersection, LF/CRLF, unmanaged-suffix, and final-newline fixtures.
  - Evidence form: Preliminary MANIFEST trace; exactly one `consistent_read` of four registries and the exact active artifact URIs in numeric sequence; no archived read; no RELATIONS observation; updated catalog/doubles; exact successful candidate and no-op preview shapes, inventory, and approval; preserved bytes; replay no-op.
  - Target recheck: TGT-STATE, TGT-SOURCE, TGT-TOOL, TGT-TEST-PURE, TGT-TEST
  - Receiver: dev-verification

- [x] VR-4. Validate unsafe taxonomy conflict handling.
  - Criterion: AC-MIGRATION-CONFLICT
  - Proof class: independent verification
  - Scenario / environment / fixture: Run `python3 -m unittest tests.test_atlas_state tests.test_atlas_tool` for invalid and multi-type IDs, wrong-type/source-kind contacts, missing source-kind, ambiguous intersections, a parent failing only one observation, and token overlaps against each VOCAB status through ID, label, and alias.
  - Evidence form: Façade `ok:false` with disposition `rejected`, null recovery, complete canonical findings, no successful preview/candidate/approval/target, zero CAS and transaction writes, and equal before/after fixture digests.
  - Target recheck: TGT-STATE, TGT-TOOL, TGT-TEST-PURE, TGT-TEST
  - Receiver: dev-verification

- [x] VR-5. Validate candidate-bound taxonomy apply.
  - Criterion: AC-MIGRATION-APPLY
  - Proof class: independent verification
  - Scenario / environment / fixture: Run taxonomy apply, wrong-approval, every-inventory-drift, and repeat-preview cases in `python3 -m unittest tests.test_atlas_tool` using temporary local profiles.
  - Evidence form: Zero-CAS stale traces, one acknowledged VOCAB CAS, exact post-validation inventory and closure proof, second-pass no-op, completed façade disposition, and null recovery.
  - Target recheck: TGT-TOOL, TGT-TEST
  - Receiver: dev-verification

- [x] VR-6. Validate bounded migration fault handling.
  - Criterion: AC-MIGRATION-FAULT
  - Proof class: independent verification
  - Scenario / environment / fixture: Run injected forward-acknowledgement, reread, sibling-drift, post-validation, rollback-acknowledgement, and other-byte cases in `python3 -m unittest tests.test_atlas_tool`.
  - Evidence form: Nested applied/rolled-back/manual-conflict states; completed/no-write/manual-intervention façade mapping; at most two VOCAB CAS calls; null recovery; unchanged siblings; absence of journal, recovery op, lineage, retry, rebase, and force-write.
  - Target recheck: TGT-TOOL, TGT-TEST
  - Receiver: dev-verification

- [x] VR-7. Validate complete candidate taxonomy findings.
  - Criterion: AC-CANDIDATE-FINDING
  - Proof class: independent verification
  - Scenario / environment / fixture: Run unrelated-poison candidate cases in `python3 -m unittest tests.test_atlas_state tests.test_atlas_source tests.test_atlas_tool` for missing, wrong-type, parent, and multiple-binding variants.
  - Evidence form: Failed version-2 envelopes with every canonical JSON detail, preview-only result, null recovery, no glance/candidate payload, and equal before/after tree digest.
  - Target recheck: TGT-STATE, TGT-SOURCE, TGT-TOOL, TGT-TEST
  - Receiver: dev-verification

- [x] VR-8. Validate the public topic-create request cutover.
  - Criterion: AC-TOPIC-REQUEST
  - Proof class: independent verification
  - Scenario / environment / fixture: Run `python3 -m unittest tests.test_atlas_index tests.test_atlas_research tests.test_atlas_tool` with valid version-2 proposals, every missing/unknown/malformed field, resolved-ID mismatch, and public version-1 input.
  - Evidence form: Exact accepted normalized v2 request, deterministic pre-effect failures, public v1 rejection, and preserved proposal labels/aliases without reducer defaults.
  - Target recheck: TGT-INDEX, TGT-TEST-PURE, TGT-TEST
  - Receiver: dev-verification

- [x] VR-9. Validate vocabulary-aware topic creation.
  - Criterion: AC-TOPIC-CREATE
  - Proof class: independent verification
  - Scenario / environment / fixture: Run `python3 -m unittest tests.test_atlas_state tests.test_atlas_index tests.test_atlas_research tests.test_atlas_tool` for exact rows in every status, zero match, unique alias reuse, strict conflicts, and existing-topic missing closure.
  - Evidence form: Exact three/four-target bytes, semantic roles and order, approved labels/aliases, role-based result/post-validation evidence, no-target conflict findings, preview-only guidance, and unchanged compatible output.
  - Target recheck: TGT-STATE, TGT-INDEX, TGT-TOOL, TGT-TEST-PURE, TGT-TEST
  - Receiver: dev-verification

- [x] VR-10. Validate current and historical topic recovery.
  - Criterion: AC-TOPIC-RECOVERY
  - Proof class: independent verification
  - Scenario / environment / fixture: Run topic execution/fault cases in `python3 -m unittest tests.test_atlas_index tests.test_atlas_tool` with each acknowledged three/four-target prefix, missing subdomain input, current v2 recovery, and an immutable historical v1 three-target journal while public v2 validation is instrumented to reject calls.
  - Evidence form: Exact role-based event/intent targets, reverse byte restoration, fixed missing-subdomain decode, current v2 recovery, byte-identical historical v1 recovery/base identity without public-validator use, unchanged v1 outer contracts, and no new v1 create.
  - Target recheck: TGT-INDEX, TGT-TOOL, TGT-TEST-PURE, TGT-TEST
  - Receiver: dev-verification

- [x] VR-11. Validate research-owner and packaged behavior.
  - Criterion: AC-OWNERS
  - Proof class: independent verification
  - Scenario / environment / fixture: Run `python3 -m unittest tests.test_atlas_harness_surface` across packaged create/research Goal/Effect, label/alias defaults, taxonomy-stop, migration approval, and manual-conflict evals.
  - Evidence form: Insert-only vocabulary authority, retained owner presentation semantics, research stop without maintain load, one owner with no chain, fresh approvals, and no fabricated migration recovery.
  - Target recheck: TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST
  - Receiver: dev-verification

- [x] VR-12. Validate compatibility and complete product behavior.
  - Criterion: AC-COMPAT
  - Proof class: independent verification
  - Scenario / environment / fixture: Record no-touch digests; run `python3 scripts/atlas_tool.py capabilities`, `python3 scripts/atlas_tool.py capabilities --all`, and `python3 -m unittest discover -s tests -p 'test_atlas_*.py'` using repository bytes and temporary local profiles; compare digests and inspect active literals afterward.
  - Evidence form: Passing actual CLI output and full suite; operation counts 30/13/43; old active migration literals and lineage absent; source degradation, research indices, and generic transaction recovery preserved; exact no-touch digests; no bound-instance access or temporary residue.
  - Target recheck: TGT-STATE, TGT-SOURCE, TGT-INDEX, TGT-TOOL, TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST-PURE, TGT-TEST
  - Receiver: dev-verification

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-T1 | T1 | Exact revisions of TGT-ARCH, TGT-CORE, TGT-RESULT, TGT-FRONTDOOR, and TGT-MAINTAIN | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation worker | Common Handoff binds AC-ARCH, every fixed contract, changed digests, schema proof, and any authority conflict. |
| OUTP-T2 | T2 | Exact final shared-lineage repository target for all eight T2 targets | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-verification | Common Handoff binds AC-CLOSURE through AC-COMPAT, operation/request/event identities, bounded migration fault evidence, topic recovery evidence, smoke output, no-touch digests, final target digest, and residual risk. |

## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-APPROVAL | dev-ask / human authority | Fresh native preflight names this exact local plan identity, complete-byte SHA-256, `PENDING` status, and explicit execution approval. | T1-T2 | Any plan byte change invalidates approval. | Exact published bytes are structurally valid and explicitly approved for execution. |
| BLK-CONTRACT-DRIFT | T1 | Exact changed upstream digest plus semantic diff against AUTH-USER-FIX and AUTH-ARCH-BASE. | T1-T2 | Material scope/write-set/interface drift requires revised exact plan approval. | User authority and base identities are current or rebound without semantic change. |
| BLK-BACKFILL-UNSAFE | T2 | Complete path/field/ID/type/parent observations and proof of no candidate or target write. | T2 | Implementation must return fixed conflict behavior; it may not infer a remap, add source-kind, or widen targets. | Only safe missing domain/subdomain/tag rows remain, or separately approved taxonomy design resolves the conflict. |
| BLK-MIGRATION-MANUAL | T2 | Exact candidate, binding, inventory, forward/rollback acknowledgements, current VOCAB classification/revision, and complete findings. | T2 | `manual-conflict` has unknown effect and no safe automatic recovery; do not fabricate `next`, retry, rebase, or overwrite other bytes. | A separately authorized maintain audit establishes current state and a new approved repair/migration contract; the failed apply itself is never resumed. |
| BLK-HISTORICAL-JOURNAL | T2 | Exact immutable v1 journal/request/target bytes that the private decoder cannot validate without weakening current authority. | T2 | Do not rewrite, delete, reinterpret, or expose a new v1 create path. | Existing v1 three-target bytes validate under their original contract, or a separately approved journal migration is required. |
| BLK-OLD-MIGRATION-CONSUMER | T2 | Active nonhistorical product caller or contract that still requires TOPICS-list normalization, with exact path and rationale. | T2 | Archived plans/ADRs are history and do not block removal; a real active need is a product-scope change. | No active consumer exists, or revised authority explicitly retains a second current migration. |
| BLK-FORBIDDEN-LIVE-EFFECT | T1 | Evidence that implementation/verification would require a bound profile, instance sync, credential, deployment, or real migration effect. | T1-T2 | Outside EFF-CONTRACT, EFF-RUNTIME, and EFF-TEST. | Work uses repository bytes and temporary local fixtures only; living preview/apply remains separate authority. |

- exhausted token at 2026-08-24-0306
  - trying: Complete immutable historical v1 topic recovery while keeping public v2 closure exact.
  - found: REV-AC-TOPIC-RECOVERY-HISTORICAL-V1-CLOSURE-01 — historical three-target post-validation incorrectly requires current VOCAB closure.
  - tried: Removed public-validator coupling and added exact historical façade proof; did not change version-selected post-validation semantics.
  - target: sha256:8b4b5b65b1ab63ddb2664abf06997a60fa94dbe826af36b9daf2b8d8f0955cce
  - remaining: AC-TOPIC-RECOVERY / human outcome authority
  - grant: continue 2026-08-24-1046
  - opinion: absent

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-ARCH | Canonical contract | `.agents/ARCHITECTURE.md` `Mode and write ownership`, `Canonical instance state`, `Source lifecycle`, `Topic lifecycle`, `Instance administration and migration` | Change first; bind closure, write sets, owner authority, and migration fault semantics. |
| ANC-PRIOR-LIMIT | Historical scope evidence | `.agents/plans/archive/2026-08-19-2019_atlas-ingest-vocab-topic-backfill.md` `CONTRACT-VOCAB` and completed result, `sha256:32a26974f8c9691e210cfa136ce4f3978a904d4095532891c4cf6187cc8c4662` | Preserve source proposal behavior; close the legacy/topic-create exclusions as a new outcome rather than reopening the completed one. |
| ANC-STATE | Runtime | `scripts/atlas_state.py::resolve_source_classification`, `validate_source_taxonomy`, `build_source_candidates`, `_validated_vocab`, `_append_rows` | Reuse one parser/matcher/renderer; keep source degradation and make persisted closure strict. |
| ANC-MIGRATION | Runtime | `scripts/atlas_state.py::prepare_topics_list_candidate`; `scripts/atlas_tool.py::_migration_prepare_topics_lists`, `_migration_apply_topics_lists` | Reuse deterministic candidate binding and bounded one-target CAS/rollback shape for VOCAB, add the complete active-source inventory, then remove the old active migration implementation. |
| ANC-RESULT | Envelope | `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json`; `operating-cadence-and-guardrails.md` owner results, exact recovery, and two-phase migration | Preserve exact recovery for recoverable effects while representing migration manual conflict as unknown with no invented operation. |
| ANC-INDEX | Runtime | `scripts/atlas_index.py::REQUEST_FIELDS`, `_validate_request`, `prepare_topic`, `load_topic_binding`, `TopicPostValidation`; `scripts/atlas_tool.py::_index_prepare`, `_index_rank`, `_index_post_validator`, `_index_transaction_result`, `_index_recover` | Keep canonical scalar identity, add proposal authority, replace fixed indexes with exact roles, and preserve private historical recovery without changing research publication indices or the generic transaction engine. |
| ANC-FINDING | Envelope | `scripts/atlas_tool.py::Failure`, `_owner_findings`, `_exception`; `scripts/atlas_cli.py::normalize_findings` | Keep the public three-field finding contract; carry structure in canonical JSON detail and preview guidance in failure result. |
| ANC-OWNERS | Workflow | `.agents/skills/atlas-ask/owners/atlas-maintain/OWNER.md` `Two-phase migration`; `atlas-research/OWNER.md` `Research` and `Create` | Keep fresh migration approvals, one selected owner, in-process topic create, and no owner chaining. |
| ANC-UNCHANGED | Negative guard | `.agents/commands/atlas-ask.md` `sha256:c5bc3503f780926af8195bde3bd97a0b383f24afb05b8c1cf5989581403a016f`; `scripts/atlas_cli.py` `sha256:f7de23c759123c07d3c13db285e149acf3471eeba59a0780fa0a6fd6c800f686`; `scripts/atlas_research.py`; `scripts/atlas_transaction.py`; `source-worker-result.schema.json`; `source-summary-proposal.schema.json`; `source-capture.schema.json`; `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md`; `scaffold/`; bound-instance state | No edits or bound-state effects unless execution proves an acceptance criterion impossible and a revised plan receives new approval. |

- ASM-BOUND-UNOBSERVED: No bound-instance state was inspected, so repository execution makes no claim that a real instance is already taxonomy-closed.
- ASM-RETIRED-MIGRATION: Repository execution makes no claim that a bound instance lacks bytes once targeted by the retired TOPICS-list migration; deployment and the first real taxonomy preview/apply remain separately authorized.

## Completion Summary

- Delivered behavior: Atlas now enforces canonical taxonomy closure in source and topic workflows, provides candidate-locked one-target taxonomy preview/apply semantics, preserves complete actionable findings, and performs vocabulary-aware topic creation without widening owner or transaction surfaces.
- Historical compatibility: under the human `continue 2026-08-24-1046` grant, lineage `REV-AC-TOPIC-RECOVERY-HISTORICAL-V1-CLOSURE-01` was closed by selecting immutable three-target post-validation for decoded v1 journals without a VOCAB snapshot, read, or closure dependency. Public v1 create remains rejected and current v2 remains vocabulary-aware and closure-strict.
- Final target: `local://atlas-taxonomy-closure-continued-target.json`, artifact `sha256:09997d703c7852fbb977639444f4d3e48686591caac5e6fcfe2ae20c24cd580b`, semantic target `sha256:195ebd34bfd6d7aad17cb6e4dce7d3cdea7bb2aaaac1995af6909eaf8a0629c5`.
- Verification: `local://atlas-taxonomy-closure-continued-verification.txt` at `sha256:6260a4ce8cf7807947d298868c2dfbd4f243cb31fa26f56fb0a1ae3d1f3386bf` independently verified all twelve acceptance criteria. Fresh continued proof included 181 index/tool tests, zero VOCAB reads and zero public-validator calls for exact historical v1 recovery, one VOCAB read plus strict closure for current v2, stable 30/13/43 capability counts, and no prohibited effect or residue. Worker smoke additionally ran the full 374-test Atlas suite successfully.
- Review: `local://atlas-taxonomy-closure-continued-review.txt` at `sha256:bdc87890f14843dd28d8c2ae57c38070468f91d2ab86ba6524c57860ea1b7404` returned Standards `PASS`, Specification `PASS`, Overall `APPROVED`, with no blocker or terminal advisory.
- Learning: `local://atlas-taxonomy-closure-learning.txt` at `sha256:bf3ff60ced0a4d08af3d6f304ff31e95f51c2d4ae382142379a8f410e59b4cdb` returned `NO DURABLE LEARNING`; the compatibility invariant is already encoded in product contracts, code, and regression proof, and no bound guidance candidate existed.
- Decisions and residual risk: the compatibility fork is selected by the immutable decoded request version; version-specific registry gates remain separate while exact-byte and baseline checks stay shared. No bound instance was read or changed, and completion does not claim any living instance is migrated or taxonomy-closed. Bound-instance preview/apply, framework sync, deployment, release, and Git shipping remain separately authorized effects.

