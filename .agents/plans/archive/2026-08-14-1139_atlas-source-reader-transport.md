# Fix Atlas Source Reader Transport

**Datetime**: 2026-08-14-1139
**Authority kind**: local-authority
**Mode**: standard
**Scope**: Atlas source-ingestion acquisition-to-semantic-worker boundary
**Summary**: Repair the source workflow so the selected same-agent owner captures and extracts exact reader results before optional semantic-worker transport. Preserve the existing extractor, worker-result schema, preparation, transaction, and routing seams.
**Status**: DONE

## Objective

- Outcome: OUT-1
- Observable end state: A routine `/atlas-ask` URL ingestion can use an optional tool-limited semantic worker without requiring that worker to call `functions.read`, `functions.eval`, shell, or the Atlas façade.
- Progress signal: AC-1 through AC-9 complete with their sole VR-1 through VR-9 proofs; activity, elapsed time, and worker count are not progress.

Current product bytes still assign canonical-page fetch and `source.extract_reader_result` to the source worker in TGT-1 and TGT-4. The intended end state is a lean ownership correction: the selected owner freezes exact extracted evidence before optional semantic transport, while the existing worker output, `source.prepare`, transaction, and route contracts remain distinct and unchanged.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-1 | Current explicit user intent | `conversation://current/debug-and-resolve` | `sha256:2519bd68e6596e4923e833acd9511b1e5017d7f1cf8c1d1ba0787438b33eab44` over `debug and resolve. lean and non-brittle.` | Planning authorized; execution requires native approval of this repaired local plan and a fresh later-session review accepting its exact locally presented SHA-256 |
| AUTH-2 | Canonical architecture | `.agents/ARCHITECTURE.md` | `sha256:5b5ad98edd3c1fdaa89cd78da1eb8f3b936b56275ef27dd0852969d70a6d14a6` | Normative current worktree authority; preserve unrelated dirty bytes |
| AUTH-3 | Accepted orchestration rationale | `docs/adr/0001-single-entry-atlas-orchestration.md` | `sha256:c1c97aa6f2d30e82e6b3cf6c1159fd02c39aaec39f87cacec60c1df65391f776` | Accepted current worktree rationale |
| AUTH-4 | Product/instance rationale | `docs/adr/0002-separate-product-and-instance-state.md` | `sha256:db18072d0f470204fffc6aaf6c6f7ebc02f7765a2f439471a51aae5362c29bdb` | Accepted |
| AUTH-5 | Terminal successor preflight recovery and exhausted-parent pointer | Child archive `.agents/plans/archive/2026-08-14-1843_atlas-successor-preflight-recovery.md`; terminal Handoff `agent://SuccessorNeutralCurator`; read-only parent `.agents/plans/2026-08-14-1528_atlas-explicit-reroute-destaged-recovery.md` | Terminal OUTP-T4 Handoff `sha256:53956ed4c3ae70114d527b84d340c0171d5339751564c95d57a5d5f21805f8c5`, `NO DURABLE LEARNING`, binds its T4-time child snapshot `sha256:b71c81b80c54a3e22615a5f5a98a95ae87cb64b7dbc04f773aff8c5b9e77a1a2`, `IN_PROGRESS`; the later `DONE` child archive is `sha256:c983cbc4710be3284d7d9d40ce2347a919d6e80b21dde86841d332864de3d66b`; parent pointer `sha256:8884816cd2f46ab98bb5de6f185ff5f016249a2c289a861c428bd011d34754b9` | The child terminal replaces the impossible destaged OUTP-T4 gate and satisfies lineage sequencing only. The parent remains exhausted `IN_PROGRESS`, must not be re-approved or resumed, cannot reach `DONE`, and never emits parent OUTP-T4. Source-plan execution still requires BLK-0 and native approval. |

Repository base: `d8290d085f32483a9e7dc7cf9710803875e5383a`. Current explicit intent takes precedence; this plan does not expand it beyond the Atlas source transport defect.

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-1 | ADR-0001 `sha256:c1c97aa6f2d30e82e6b3cf6c1159fd02c39aaec39f87cacec60c1df65391f776` | Keep end-to-end workflow and façade ownership in the selected same agent; nested Task/JSON-schema transport stays optional and can never be a capability stop. |
| DEC-2 | ARCH source lifecycle `sha256:5b5ad98edd3c1fdaa89cd78da1eb8f3b936b56275ef27dd0852969d70a6d14a6` | Preserve exact `functions.read-v1` extraction through `source.extract_reader_result`; never parse spilled text, hash rendered framing, or create a second extractor. |
| DEC-3 | ADR-0002 `sha256:db18072d0f470204fffc6aaf6c6f7ebc02f7765a2f439471a51aae5362c29bdb` | Author the correction in the product package, then update only the product-owned architecture snapshot through `sync-framework --name atlas`. |
| DEC-4 | User constraint AUTH-1 | Prefer the smallest ownership correction: move acquisition/extraction before semantic dispatch; do not change source identity, state schemas, worker-result schema, reducer, transaction, route, or command surfaces. |
| DEC-5 | Review of plan `sha256:817cd95e771935055f6babae2d41f0762bd62c3ea91f59f1c712b15345439c61` | Rebind current worktree bases; distinguish owner-held worker input from `source.prepare`; replace live-worker smoke with deterministic tests; make new red/green assertions and the quality-guide frozen-input cutover explicit; disclose whole-snapshot synchronization. |
| DEC-6 | Review of source plan `sha256:3dc848ebf53e2880c0ce76c3643529b1b5819cca6df7cc4aab68311d0a1d4301` plus AUTH-5 terminal OUTP-T4 | The terminal Handoff binds the T4-time child snapshot `sha256:b71c81b80c54a3e22615a5f5a98a95ae87cb64b7dbc04f773aff8c5b9e77a1a2`, `IN_PROGRESS`; the later `DONE` archive is `sha256:c983cbc4710be3284d7d9d40ce2347a919d6e80b21dde86841d332864de3d66b`. This terminal `NO DURABLE LEARNING` result replaces the impossible parent OUTP-T4 gate; the parent pointer at `sha256:8884816cd2f46ab98bb5de6f185ff5f016249a2c289a861c428bd011d34754b9` remains read-only and non-resumable. Fresh reread confirms TGT-1, TGT-2, TGT-4, and TGT-5 still match their rebound bases, so lineage sequencing is satisfied. A fresh exact-plan semantic review and native approval still gate T1; later drift stops for another rebound revision. |
| DEC-7 | Current `### Explicit reroute` branch and `test_explicit_reroute_uses_lookup_then_fresh_bounded_route` | Preserve explicit reroute as a fetch-free, extraction-free, inventory-free, worker-free, prepare-free early branch. This plan's ingestion correction must not weaken that branch. |

## Scope, non-goals, and prohibited effects

- Read surfaces: AUTH-2 through AUTH-5, the successor child terminal OUTP-T4, and the read-only exhausted-parent pointer; `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`; `.agents/skills/atlas-core/assets/source-summary-quality-guide.md`; `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md`; `tests/test_atlas_harness_surface.py`; and the development instance classification reported by `python3 scripts/atlas-instance.py check --name atlas`.
- Change surfaces: TGT-1 through TGT-9 only.
- Non-goals: Do not modify `scripts/atlas_source.py`, `scripts/atlas_tool.py`, `source-worker-result.schema.json`, `source-summary-proposal.schema.json`, reducers, transactions, routing, `/atlas-ask`, or the thin command wrapper. Do not add a CONTRACT-2 schema file, acquisition service, scratch packet store, compatibility alias, worker-specific parser, or OMP-only `eval` requirement. Do not retry or ingest `https://github.com/unclebob/swarm-forge`; that is a separate Atlas request and approval. Do not start any task before AUTH-5 OUTP-T4 is terminal.
- Prohibited effects: No living source, manifest, relation, topic, pass, or registry writes; no credentials; no non-development profile writes; no deploy, commit, push, release, or shipping action; no destructive command; no direct edit of `vault://atlas/ARCHITECTURE.md`; no ordinary write to the repository plan projection.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-1 | Repository working-tree mutation | AUTH-1 | Edit only TGT-1 through TGT-5 against their exact current worktree bases; ordinary reversible changes; preserve every unrelated dirty byte. |
| EFF-2 | Development framework snapshot synchronization | AUTH-1, AUTH-4 | After T1, run only `python3 scripts/atlas-instance.py sync-framework --name atlas`. This replaces the instance snapshot with the complete current TGT-1 postimage, including unrelated uncommitted architecture bytes already present in AUTH-2 plus T1's surgical source-lifecycle edit. Any additional TGT-1 drift after plan approval stops on BLK-4 before sync. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-1 | Reader extraction | T1 | Existing `functions.read-v1` to `source.extract_reader_result` contract at `markdown-registry-contracts.md` `sha256:dd37340921a790dcad21b76306f33be05c0e9cf2700130294cd71931187e92d1` | T1, T3, T4 |
| CONTRACT-2 | Semantic worker input | T1 | Exact owner-held shape `{identity:{canonical_url,source_id},mode,extracted}` where `extracted` is the unchanged `source.extract_reader_result` result; native Task input remains ordinary bound data and gains no schema file | T1, T3, T4 |
| CONTRACT-3 | Semantic worker output | T1 | One complete existing `source-worker-result.schema.json` object; no schema change | T1, T3, T4 |
| CONTRACT-4 | Optional transport and preparation boundary | T1 | A native strict Task or same-owner semantic role consumes CONTRACT-2 and emits CONTRACT-3. The owner then calls `source.prepare` only with `{identity:{canonical_url,checked_on},mode,worker}`, where `worker` is the complete CONTRACT-3 object; CONTRACT-2 is never passed to `source.prepare`. | T1, T3, T4, T5 |
| CONTRACT-5 | Frozen evidence across worker resumes | T1 | The initial `extracted` value in CONTRACT-2 is immutable for aggregate choice and the one same-worker correction; neither path refetches or reconstructs it | T1, T3, T4 |
| CONTRACT-6 | Product snapshot sync | T2 | ADR-0002 and `atlas-instance.py sync-framework --name atlas` over the complete approved TGT-1 postimage | T2, T3 |
| CONTRACT-7 | Explicit-reroute compatibility | T1 | Exactly one canonical URL; initial `source.lookup`; helper-only `atlas-route`; no fetch, inventory, extraction, semantic worker, `source.prepare`, or source transaction; preserve `test_explicit_reroute_uses_lookup_then_fresh_bounded_route` | T1, T3, T4 |

If the selected owner itself cannot preserve the exact structured reader result into `source.extract_reader_result`, return a terminal blocked/capability-unavailable result with effect `none`; never misclassify transport failure as source evidence `no-write` and never reconstruct reader framing.

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-1 | `.agents/ARCHITECTURE.md`, `## Source lifecycle` | T1 | `sha256:5b5ad98edd3c1fdaa89cd78da1eb8f3b936b56275ef27dd0852969d70a6d14a6` | `/atlas-ask`, all source owners, framework snapshot | AC-1, AC-2 |
| TGT-2 | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`, reader extraction and source worker preparation | T1 | `sha256:dd37340921a790dcad21b76306f33be05c0e9cf2700130294cd71931187e92d1` | `atlas-source`, `source.prepare`, harness tests | AC-1, AC-2, AC-3, AC-4 |
| TGT-3 | `.agents/skills/atlas-core/assets/source-summary-quality-guide.md`, semantic draft evidence envelope and entry-accessibility step 1 | T1 | `sha256:83af25108067368094a523ad349d53107e3d1423881a53009912d4208942ee08` | source semantic drafting and validation | AC-1, AC-2, AC-3 |
| TGT-4 | `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md`, façade boundary, explicit-reroute branch, and inventory/worker wave | T1 | `sha256:857db57c74a1b7ce6d320850b74db96484fc2e007a731212d87cbaf8ff0d553c` | selected same-agent source workflow and CONTRACT-7 | AC-1, AC-2, AC-3, AC-4, AC-5 |
| TGT-5 | `tests/test_atlas_harness_surface.py`, source workflow contract tests | T1 | `sha256:8219d962c81cf4bfcaf040c0790f07ccb1ff50c66954d315a34de1f28c4793a8` | `AtlasHarnessSurfaceTests`, including `test_explicit_reroute_uses_lookup_then_fresh_bounded_route` | AC-5 |
| TGT-6 | `vault://atlas/ARCHITECTURE.md`, product-owned development snapshot | T2 | `sha256:5b5ad98edd3c1fdaa89cd78da1eb8f3b936b56275ef27dd0852969d70a6d14a6`, equal to current TGT-1 as proven by `check --name atlas` returning `check OK` during this revision | `atlas` development instance | AC-6 |
| TGT-7 | Independent verification result bound to the implementation postimage hashes | T3 | missing before T3 | T4 review intake | AC-7 |
| TGT-8 | Final Standards and Specification review result | T4 | missing before T4 | T5 curation intake | AC-8 |
| TGT-9 | Terminal curation assessment and Common Handoff | T5 | missing before T5 | `dev-ask completion presentation` | AC-9 |

## Execution policy

- Assurance: standard
- Topology: shared
- Max concurrency: 1
- Isolation: Shared working tree with pre/post SHA-256 target bundles; no commit is authorized.
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: Reread each TGT immediately before edit and preserve unrelated user changes. Any semantic target drift that changes authority, scope, or the fix boundary returns to `dev-ask` for material reapproval.
- Decomposition: T1 and T2 form one cohesive implementation sequence because architecture, contracts, owner behavior, regression proof, and framework snapshot must agree. T3 and T4 are read-only assurance boundaries. T5 performs only the required terminal curation screen.
- Effect limit: EFF-1, EFF-2
- Orchestrator profile: One-qualified-owner sequential projection; full orchestration is unnecessary and no capability fallback may weaken CONTRACT-1 through CONTRACT-5 or CONTRACT-7.

Prospective route:

1. `dev-implementation`
2. `dev-verification`
3. `dev-code-review`
4. `dev-continual-learning`
5. `dev-ask completion presentation`

Execution precondition: T1 may start only after the exact AUTH-5 successor child OUTP-T4 terminal Handoff and read-only exhausted-parent pointer are reread, and a fresh planner session reviews the exact locally presented plan SHA-256 and returns an accepted executable verdict. Native plan approval, structural validity, and backend eligibility do not satisfy this semantic review gate. Immediately before T1 mutation, reread AUTH-5 preservation hashes. Drift from the rebound TGT-1, TGT-2, TGT-4, and TGT-5 bases stops on BLK-1.

## Tasks

- [x] T1. Move source acquisition and exact extraction into the selected owner before semantic dispatch
  completed 2026-08-15-0202
  - Owner: dev-implementation
  - Wave: W0
  - Depends on: none
  - Targets: TGT-1, TGT-2, TGT-3, TGT-4, TGT-5
  - Contracts: CONTRACT-1, CONTRACT-2, CONTRACT-3, CONTRACT-4, CONTRACT-5, CONTRACT-7
  - Criteria: AC-1, AC-2, AC-3, AC-4, AC-5
  - Effects: EFF-1
  - Output: OUTP-1
  - Receiver: T2
  - Verification: VR-1, VR-2, VR-3, VR-4, VR-5
  - Lineage: shared
  - Before any mutation, require terminal AUTH-5 successor child OUTP-T4 and the fresh accepted review receipt for the exact locally presented plan SHA-256, then run the exact VR-5 one-liner and record its expected nonzero verdict on current TGT-4. Without the successor child terminal result, stop on BLK-7. Without the review receipt, stop on BLK-0. After both pass, edit in canonical order: architecture, registry contract, quality guide, `atlas-source`, and harness-surface regression. Preserve `### Explicit reroute` and CONTRACT-7.
  - In TGT-1, replace “Source workers own fetch” with the selected owner owning bounded harness fetch, complete-reader extraction, and frozen CONTRACT-2 construction; retain aggregate recognition and source-local semantic drafting as worker work.
  - In TGT-2, define CONTRACT-2 and CONTRACT-4 exactly. Preserve the existing `source.prepare` signature `{identity:{canonical_url,checked_on},mode,worker}` and its complete CONTRACT-3 worker object. Never pass CONTRACT-2 to prepare and never add a schema or runtime-code surface.
  - In TGT-3 `## Entry accessibility and aggregate-page scope`, replace step 1 `Open the supplied canonical link.` with `Consume the selected owner's frozen CONTRACT-2 extracted payload_text, canonical URL, and retrieval metadata; do not open or refetch the link.` Make only the minimum referent edits needed for the remaining existing steps to describe the frozen payload; add no new quality policy.
  - In TGT-4, preserve inventory-before-fetch and bounded per-host acquisition, but make the selected owner fetch each actionable canonical page and immediately call `source.extract_reader_result` before dispatch. Dispatch only successfully extracted CONTRACT-2 packets. Unavailable/invalid extraction remains effect-none; source-content insufficiency remains the existing `needs-input|no-write` semantic outcome.
  - The native Task remains optional and binds only the existing strict output schema. A Task or same-owner semantic role consumes CONTRACT-2 and emits one complete CONTRACT-3 object; the owner then calls `source.prepare` with inventory-derived `{canonical_url,checked_on}`, mode, and that worker object. Do not loosen strict native output, parse prose, or treat CONTRACT-2 as preparation input.
  - Preserve the exact CONTRACT-2 `extracted` value across aggregate choice and the one correction. Expansion inventories selected children through the existing bounded depth-1 path; each new actionable child receives its own owner acquisition/extraction before semantic work.
  - In TGT-5, extend the current tests with these exact required phrases: “The selected owner fetches each actionable canonical page” and “The worker receives only its assigned identity, mode, and the unchanged extracted result. It performs no I/O or tool calls.” Assert `source.inventory` precedes the owner `source.extract_reader_result` call, which precedes `Dispatch at most one source worker`. Slice the worker bullet that starts `- The worker receives` and reject `functions.read`, `source.extract_reader_result`, `scripts/atlas_tool.py`, and `eval` from that bullet without requiring those names to appear in it. Also read TGT-3, require `Consume the selected owner's frozen`, and reject `Open the supplied canonical link`. Keep `test_explicit_reroute_uses_lookup_then_fresh_bounded_route` green.

- [x] T2. Synchronize the complete approved product architecture postimage to the development snapshot
  completed 2026-08-15-0204
  - Owner: dev-implementation
  - Wave: W1
  - Depends on: T1
  - Targets: TGT-6
  - Contracts: CONTRACT-6
  - Criteria: AC-6
  - Effects: EFF-2
  - Output: OUTP-2
  - Receiver: dev-verification
  - Verification: VR-6
  - Lineage: shared
  - Immediately after T1, run `python3 scripts/atlas-instance.py check --name atlas` before sync. Accept only the expected product-owned architecture drift caused by T1; any other finding, an unchanged `check OK`, or any additional TGT-1 byte drift triggers BLK-4.
  - Recompute TGT-1 and prove its diff from the approved `sha256:5b5ad98edd3c1fdaa89cd78da1eb8f3b936b56275ef27dd0852969d70a6d14a6` is limited to T1 while every unrelated pre-existing dirty byte remains. The approved sync candidate is the entire current TGT-1 postimage, not a source-lifecycle patch.
  - Run `python3 scripts/atlas-instance.py sync-framework --name atlas`, then `python3 scripts/atlas-instance.py check --name atlas`. Do not use `--all` and do not touch living research state. If execution approval does not include this disclosed whole-snapshot EFF-2, stop on BLK-4 instead of syncing to make the check green.
  - Emit a postimage SHA-256 bundle for TGT-1 through TGT-5 plus the successful focused/full commands and exact snapshot effect; the receiver rechecks that bundle before and after verification.

- [x] T3. Independently verify the immutable postimage and deterministic transport proof
  completed 2026-08-15-0218
  - Owner: dev-verification
  - Wave: W2
  - Depends on: T2
  - Targets: TGT-1, TGT-2, TGT-3, TGT-4, TGT-5, TGT-6, TGT-7
  - Contracts: CONTRACT-1, CONTRACT-2, CONTRACT-3, CONTRACT-4, CONTRACT-5, CONTRACT-6, CONTRACT-7
  - Criteria: AC-7
  - Effects: none
  - Output: OUTP-3
  - Receiver: dev-code-review
  - Verification: VR-7
  - Lineage: shared
  - Use fresh read-only evidence. Reject any hash drift, worker-owned fetch/extract/tool dependency, CONTRACT-2-to-prepare collapse, quality-guide refetch instruction, schema weakening, unapproved instance write, or failed deterministic check; do not repair.

- [x] T4. Perform the final Standards and Specification review
  completed 2026-08-15-0258
  - Owner: dev-code-review
  - Wave: W3
  - Depends on: T3
  - Targets: TGT-1, TGT-2, TGT-3, TGT-4, TGT-5, TGT-8
  - Contracts: CONTRACT-1, CONTRACT-2, CONTRACT-3, CONTRACT-4, CONTRACT-5, CONTRACT-7
  - Criteria: AC-8
  - Effects: none
  - Output: OUTP-4
  - Receiver: dev-continual-learning
  - Verification: VR-8
  - Lineage: shared
  - Review only the independently verified postimage against AUTH-1 through AUTH-5, DEC-5 through DEC-7, ADR-0001, Atlas skill-surface rules, clean-cutover policy, CONTRACT-7, and the literal lean/non-brittle constraint, exactly as VR-8 requires. Any blocker returns to bounded implementation repair; advisories do not reopen accepted work.

- [x] T5. Run the terminal continual-learning screen and hand off completion
  completed 2026-08-15-0303
  - Owner: dev-continual-learning
  - Wave: W4
  - Depends on: T4
  - Targets: TGT-1, TGT-4, TGT-9
  - Contracts: CONTRACT-4
  - Criteria: AC-9
  - Effects: none
  - Output: OUTP-5
  - Receiver: dev-ask completion presentation
  - Verification: VR-9
  - Lineage: shared
  - Assess only directly impacted project-owned guidance. The expected terminal result is no additional mutation because the canonical architecture and source owner carry the durable correction; any proposed new rule/skill target is a material scope change and returns to `dev-ask` rather than being written.

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-1 | One actionable routine URL after inventory | The selected owner fetches once, passes the complete structured reader result unchanged to `source.extract_reader_result`, freezes CONTRACT-2, then starts semantic work | TGT-1, TGT-2, TGT-3, TGT-4 | T1 |
| AC-2 | Optional worker lacks `eval`, shell, façade, or fetch tools | Contract text and deterministic tests prove semantic drafting receives CONTRACT-2 without owning those tools; worker limitations do not become source `no-write` | TGT-1, TGT-2, TGT-3, TGT-4 | T1 |
| AC-3 | Exact reader, worker-output, and preparation contracts | No second extractor, spill parsing, framing hash, caller-authored retrieval metadata, schema relaxation, persistent packet state, or CONTRACT-2 call to `source.prepare` exists | TGT-2, TGT-3, TGT-4 | T1 |
| AC-4 | Aggregate choice or one correction | The owner reuses frozen CONTRACT-2 evidence; it does not refetch, reconstruct, merge deltas, or reread a stale worker artifact | TGT-2, TGT-4 | T1 |
| AC-5 | Regression harness tests | New assertions deterministically fail on the current worker-fetch ordering and pass only when owner acquisition precedes a tool-free worker and TGT-3 consumes frozen evidence | TGT-4, TGT-5 | T1 |
| AC-6 | Approved complete product architecture postimage | Pre-sync check reports only T1 product-owned drift; the disclosed whole-snapshot `sync-framework --name atlas` succeeds; post-sync check reports `check OK`; no instance-owned research path changes | TGT-6 | T2 |
| AC-7 | Fresh independent verification | VR-1 through VR-6 pass against one unchanged postimage SHA-256 bundle and the verifier emits a bound verdict | TGT-7 | T3 |
| AC-8 | Final read-only review | No blocking Standards or Specification finding remains and the reviewer emits a bound result | TGT-8 | T4 |
| AC-9 | Terminal curation screen | A grounded no-change result or material changed-route Handoff is emitted without silently expanding this plan | TGT-9 | T5 |

## Verification / Done criteria

- [x] VR-1. New owner-acquisition assertions and frozen-input guide pass
  - Criterion: AC-1
  - Proof class: worker smoke
  - Scenario / environment / fixture: From `/Users/kim/dev/atlas/app`, run `python3 -m unittest tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_source_skill_uses_inventory_before_fetch tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_reader_result_extraction_is_one_shared_source_contract tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_explicit_reroute_uses_lookup_then_fresh_bounded_route` after adding assertions for the exact phrases “The selected owner fetches each actionable canonical page”, “The worker receives only its assigned identity, mode, and the unchanged extracted result. It performs no I/O or tool calls.”, and “Consume the selected owner's frozen”, plus absence of “Open the supplied canonical link”.
  - Evidence form: Exit 0 and named tests `OK`; assertions also prove the order `source.inventory` then owner `source.extract_reader_result` then `Dispatch at most one source worker`.
  - Target recheck: TGT-1, TGT-2, TGT-3, TGT-4
  - Receiver: T2

- [x] VR-2. Deterministic extractor and worker-boundary smoke
  - Criterion: AC-2
  - Proof class: worker smoke
  - Scenario / environment / fixture: From `/Users/kim/dev/atlas/app`, run `python3 -m unittest tests.test_atlas_source.AtlasSourceTests.test_extract_reader_result_preserves_exact_synthetic_body_and_metadata tests.test_atlas_tool.AtlasToolTests.test_extract_reader_result_facade_is_pure_and_fails_closed tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_source_skill_uses_inventory_before_fetch tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_reader_result_extraction_is_one_shared_source_contract`. No live semantic worker is spawned.
  - Evidence form: Exit 0 and final `OK`; existing unit/façade fixtures prove exact extraction, while harness assertions prove the worker subsection contains no `functions.read`, `source.extract_reader_result`, `scripts/atlas_tool.py`, or `eval` ownership.
  - Target recheck: TGT-1, TGT-2, TGT-3, TGT-4
  - Receiver: T2

- [x] VR-3. Worker output and prepare contracts remain distinct and closed
  - Criterion: AC-3
  - Proof class: worker smoke
  - Scenario / environment / fixture: Run `python3 -m unittest tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_source_skill_uses_strict_schema_and_direct_correction_reply tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_reader_result_extraction_is_one_shared_source_contract` from `/Users/kim/dev/atlas/app`, then inspect TGT-2 and TGT-4 for the exact `source.prepare` input `{identity:{canonical_url,checked_on},mode,worker}` and the statement that CONTRACT-2 is never passed to prepare.
  - Evidence form: Exit 0, final `OK`, no source schema diff, no second extraction/storage surface, and a complete CONTRACT-3 worker object at the preparation boundary.
  - Target recheck: TGT-2, TGT-3, TGT-4
  - Receiver: T2

- [x] VR-4. Aggregate and correction paths reuse frozen evidence
  - Criterion: AC-4
  - Proof class: worker smoke
  - Scenario / environment / fixture: Inspect the updated `### Inventory and worker wave` and `### Choices, preparation, and persistence` sections and run `python3 -m unittest tests.test_atlas_harness_surface`.
  - Evidence form: Exit 0 and contract text that binds aggregate choice and one correction to CONTRACT-2 `extracted` with no refetch or result reconstruction.
  - Target recheck: TGT-2, TGT-4
  - Receiver: T2

- [x] VR-5. Red-before-green worker ownership check
  - Criterion: AC-5
  - Proof class: worker smoke
  - Scenario / environment / fixture: Before T1 edits and again after T1, run from `/Users/kim/dev/atlas/app`: `python3 -c 'from pathlib import Path; s=Path(\".agents/skills/atlas-ask/owners/atlas-source/OWNER.md\").read_text(); o=s[s.index(\"### Inventory and worker wave\"):s.index(\"### Choices, preparation, and persistence\")]; assert o.index(\"source.inventory\") < o.index(\"source.extract_reader_result\") < o.index(\"Dispatch at most one source worker\"); assert \"The selected owner fetches each actionable canonical page\" in o; w=o[o.index(\"- The worker receives\"):o.index(\"- For unavailable\")]; assert \"unchanged extracted result\" in w; assert all(x not in w for x in (\"functions.read\",\"source.extract_reader_result\",\"scripts/atlas_tool.py\",\"eval\"))'`.
  - Evidence form: Pre-edit command exits nonzero against current TGT-4 `sha256:857db57c74a1b7ce6d320850b74db96484fc2e007a731212d87cbaf8ff0d553c` on all four intended ownership checks: extraction order, owner-fetch phrase, frozen-worker phrase, and tool-free worker boundary. Post-edit command exits 0, followed by green VR-1.
  - Target recheck: TGT-4, TGT-5
  - Receiver: T2

- [x] VR-6. Full suite and disclosed development snapshot effect pass
  - Criterion: AC-6
  - Proof class: worker smoke
  - Scenario / environment / fixture: From `/Users/kim/dev/atlas/app`, run `python3 -m unittest discover -s tests -p 'test_*.py'`; run pre-sync `python3 scripts/atlas-instance.py check --name atlas` and require only T1-caused product-owned architecture drift; verify no post-approval TGT-1 drift beyond T1; run `python3 scripts/atlas-instance.py sync-framework --name atlas`; then rerun `python3 scripts/atlas-instance.py check --name atlas`.
  - Evidence form: Test exit 0 with final `OK`; pre-sync check has only the expected product-owned drift; sync acknowledges the complete TGT-1 postimage; post-sync check exits 0 with `check OK`, `instances: atlas`, and `product_owned entries: 1`; no instance-owned target is selected.
  - Target recheck: TGT-6
  - Receiver: dev-verification

- [x] VR-7. Independent postimage verification
  - Criterion: AC-7
  - Proof class: independent verification
  - Scenario / environment / fixture: Recompute the TGT-1 through TGT-5 SHA-256 bundle; rerun the deterministic commands from VR-1 through VR-5, the full suite, and read-only `python3 scripts/atlas-instance.py check --name atlas`; then recompute the bundle. Confirm architecture, contracts, guide, and owner order agree; CONTRACT-2 never reaches prepare; CONTRACT-7 explicit-reroute branch remains fetch-free; `/atlas-ask` command and source schemas are unchanged.
  - Evidence form: TGT-7 verification verdict with identical pre/post hashes, exact command outputs, snapshot check, and no repair.
  - Target recheck: TGT-7
  - Receiver: dev-code-review

- [x] VR-8. Final Standards and Specification pass
  - Criterion: AC-8
  - Proof class: review
  - Scenario / environment / fixture: Review the exact verified hash bundle against AUTH-1 through AUTH-5, DEC-5 through DEC-7, ADR-0001, Atlas skill-surface rules, clean-cutover policy, CONTRACT-7, and the literal lean/non-brittle constraint.
  - Evidence form: TGT-8 final review verdict with blockers separated from advisories; zero blockers required.
  - Target recheck: TGT-8
  - Receiver: dev-continual-learning

- [x] VR-9. Continual-learning terminal screen
  - Criterion: AC-9
  - Proof class: other authorized class
  - Scenario / environment / fixture: Assess only whether the same correction revealed a durable gap outside the already-updated architecture and owner contracts.
  - Evidence form: TGT-9 explicit no-change result, or changed-route Common Handoff before any new target mutation.
  - Target recheck: TGT-9
  - Receiver: dev-ask completion presentation

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-1 | T1 | TGT-1 through TGT-5 postimage SHA-256 bundle plus VR-1 through VR-5 evidence | completed, blocked | T2 | Common Handoff; route-impact unchanged unless CONTRACT-1 through CONTRACT-5, CONTRACT-7, or target set changes |
| OUTP-2 | T2 | Implementation postimage, VR-6 output, and TGT-6 sync receipt | completed, blocked | dev-verification | Common Handoff with exact effect state and no inferred snapshot success |
| OUTP-3 | T3 | TGT-7 independent verification verdict bound to OUTP-2 hashes | completed, failed, blocked | dev-code-review | Common Handoff; no repair authority |
| OUTP-4 | T4 | TGT-8 final Standards and Specification review | completed, blocked | dev-continual-learning | Common Handoff; advisories cannot reopen work |
| OUTP-5 | T5 | TGT-9 terminal curation assessment and complete route evidence | completed, authority-change-required, blocked | dev-ask completion presentation | Common Handoff; completion only on unchanged route with all AC and VR items complete |

## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-0 | T1 | Fresh later-session planner review receipt accepting the exact locally presented plan SHA-256 | T1, T2, T3, T4, T5 | Native approval or preflight without the exact semantic review receipt authorizes no task or effect | Exact current plan SHA-256 has an accepted executable review verdict from a later session |
| BLK-7 | T1 | AUTH-5 terminal OUTP-T4 Handoff `sha256:53956ed4c3ae70114d527b84d340c0171d5339751564c95d57a5d5f21805f8c5` with `NO DURABLE LEARNING`, binding T4-time child snapshot `sha256:b71c81b80c54a3e22615a5f5a98a95ae87cb64b7dbc04f773aff8c5b9e77a1a2`, `IN_PROGRESS`; later `DONE` child archive `sha256:c983cbc4710be3284d7d9d40ce2347a919d6e80b21dde86841d332864de3d66b`; parent pointer `sha256:8884816cd2f46ab98bb5de6f185ff5f016249a2c289a861c428bd011d34754b9`; and a fresh reread of the shared bases | T1, T2, T3, T4, T5 | The child terminal replaces the impossible parent terminal without approving source work; the parent remains read-only, exhausted, and non-resumable. Source-plan mutation before this rebind would have been contention. | Sequencing is satisfied at this revision: child OUTP-T4 is terminal and TGT-1, TGT-2, TGT-4, and TGT-5 match their rebound bases. Unavailable terminal evidence or later drift stops on BLK-7 or BLK-1; BLK-0 and native approval still block execution. |
| BLK-1 | T1 | Fresh reread and semantic comparison of any drifted TGT | T1, T2, T3, T4, T5 | Material authority/scope/contract drift requires `dev-ask` reapproval; unrelated drift is preserved | All target bases are current or non-material drift is documented |
| BLK-2 | T1 | VR-2 or VR-5 still shows worker fetch/façade/`eval` dependency | T1, T2, T3, T4, T5 | Repair only within CONTRACT-2 through CONTRACT-5, CONTRACT-7, and TGT-1 through TGT-5; no harness bypass | Deterministic assertions prove the worker consumes frozen evidence only |
| BLK-3 | T1 | Evidence that `source-worker-result.schema.json` cannot represent the semantic role's complete output | T1, T2, T3, T4, T5 | Schema or runtime-code change is material scope expansion and requires `dev-ask` reapproval | Existing CONTRACT-3 is proven sufficient, or a separately approved revised plan exists |
| BLK-4 | T2 | Pre-sync check is not exactly T1-caused product-owned drift, TGT-1 changed after approval beyond T1, EFF-2 is excluded, or sync/check reports ambiguity, unsafe state, or possible effect | T2, T3, T4, T5 | Preserve every observed object; no retry, `--all`, direct vault edit, sync-to-green shortcut, or inferred success | The complete TGT-1 postimage effect is still exactly authorized and safely resumable, or user grants revised authority |
| BLK-5 | T3 | Postimage hash drift or any failed VR | T3, T4, T5 | Verification performs no repair; return exact failure to bounded T1/T2 owner under unchanged route only when scope/contracts remain fixed | One unchanged postimage passes all required checks |
| BLK-6 | T4 | Blocking Standards or Specification finding | T4, T5 | Return to bounded implementation repair; route reapproval only for a material trigger | Repair is independently reverified and review has zero blockers |

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-1 | Architecture | `.agents/ARCHITECTURE.md` `## Source lifecycle`, base `sha256:5b5ad98edd3c1fdaa89cd78da1eb8f3b936b56275ef27dd0852969d70a6d14a6` | Canonical ownership order; edit first and preserve unrelated dirty bytes |
| ANC-2 | Accepted rationale | `docs/adr/0001-single-entry-atlas-orchestration.md` line 13, `sha256:c1c97aa6f2d30e82e6b3cf6c1159fd02c39aaec39f87cacec60c1df65391f776` | Nested Task optionality and same-agent owner authority |
| ANC-3 | Core contract | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` `## Reader-result source-body extraction` and `## Source inventory and preparation`, base `sha256:dd37340921a790dcad21b76306f33be05c0e9cf2700130294cd71931187e92d1` | Exact extractor, worker-output, and preparation seams |
| ANC-4 | Workflow | `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md` `### Inventory and worker wave` and `### Explicit reroute`, base `sha256:857db57c74a1b7ce6d320850b74db96484fc2e007a731212d87cbaf8ff0d553c` | Current worker-owned fetch defect, implementation target, and preserved reroute branch |
| ANC-6 | Successor recovery terminal | Terminal Handoff `/Users/kim/.omp/agent/sessions/-dev-atlas-app/2026-08-14T16-20-48-202Z_01a00113-77ca-7000-b588-8d91a39057d5/SuccessorNeutralCurator.md` `sha256:53956ed4c3ae70114d527b84d340c0171d5339751564c95d57a5d5f21805f8c5` binds its T4-time child snapshot `sha256:b71c81b80c54a3e22615a5f5a98a95ae87cb64b7dbc04f773aff8c5b9e77a1a2`, `IN_PROGRESS`; later `DONE` child archive `.agents/plans/archive/2026-08-14-1843_atlas-successor-preflight-recovery.md` `sha256:c983cbc4710be3284d7d9d40ce2347a919d6e80b21dde86841d332864de3d66b`; read-only parent `.agents/plans/2026-08-14-1528_atlas-explicit-reroute-destaged-recovery.md` `sha256:8884816cd2f46ab98bb5de6f185ff5f016249a2c289a861c428bd011d34754b9` | Child OUTP-T4 `NO DURABLE LEARNING` is the replacement lineage readiness evidence. The parent pointer is preservation-only and remains permanently exhausted `IN_PROGRESS`, non-resumable, unable to reach `DONE`, and unable to emit parent OUTP-T4. |
| ANC-5 | Quality boundary | `.agents/skills/atlas-core/assets/source-summary-quality-guide.md` `## Entry accessibility and aggregate-page scope`, base `sha256:83af25108067368094a523ad349d53107e3d1423881a53009912d4208942ee08` | Remove the semantic worker's reopen/refetch instruction |

- ASM-1: The selected main agent can preserve a complete reader result for the façade; the tool-limited semantic worker need not. If the selected owner cannot compose the exact reader result, stop as blocked/capability-unavailable with effect none; do not return source `no-write` or add a parser.
- ASM-2: `source-worker-result.schema.json` already represents CONTRACT-3 and `source.prepare` already validates that complete worker object. If deterministic tests disprove sufficiency, trigger BLK-3; do not alter schemas under this plan.
- ASM-3: `python3 scripts/atlas-instance.py check --name atlas` returned `check OK` while repairing this plan, binding current TGT-6 to current AUTH-2. T1 will intentionally create product-owned drift. Plan approval authorizes syncing the complete approved TGT-1 postimage, including unrelated pre-existing dirty bytes; any additional post-approval drift triggers BLK-4 before EFF-2.

## Completion Summary

- Delivered: ordinary Atlas source ingestion now keeps inventory, bounded acquisition, exact reader-result extraction, and input freezing in the selected owner before optional tool-free semantic dispatch. Incomplete or truncated reader results stop effect-none before `CONTRACT-2`, artifact, registry, preparation, or semantic work; explicit reroute remains fetch-free.
- Decisions: preserved the existing extractor, worker-result and proposal schemas, `source.prepare`, transaction, and routing seams. Native Task transport remains optional. No compatibility path, secondary parser, façade operation, or direct worker I/O was added.
- Effects: synchronized the complete approved product-owned `.agents/ARCHITECTURE.md` postimage to the bound development instance `atlas`; living research state and seed-once templates were unchanged.
- Verification: the repaired final bundle passed 304 tests and `python3 scripts/atlas-instance.py check --name atlas`; independent verification marked AC-1 through AC-7 `VERIFIED`; final Standards and Specification review approved AC-8 with no blockers or advisories; terminal curation returned `NO DURABLE LEARNING` for AC-9.
- Repair accounting: the sole post-assurance repair removed the stale partial-reader fallback, added deterministic regression coverage, and passed fresh impacted verification plus the sole authorized review rerun.
- Residual risk: none within the approved target and proof seams. Shipping was not requested or performed.
