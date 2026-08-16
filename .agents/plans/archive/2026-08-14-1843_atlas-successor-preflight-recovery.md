# Atlas successor preflight recovery

**Datetime**: 2026-08-14-1843
**Authority kind**: local-authority
**Scope**: One narrow production guard and regression test for the exhausted explicit-reroute recovery
**Summary**: Record the parent plan's expansion, guard legacy route successors before writes, and repeat the required high-consequence assurance with the complete project-rule manifest.
**Status**: DONE

## Objective

- Outcome: OUT-ATLAS-SUCCESSOR-PREFLIGHT-RECOVERY
- Context: The parent recovery completed its fixture correction and fresh independent verification, but its sole review rerun returned `CHANGES REQUIRED`. The remaining production blocker is exact: `transaction.successor` can replay an eligible legacy `route-upsert` journal without `_route_guard`; the review Context Pack also omitted two applicable rules.
- Observable end state: The parent plan points to this child while remaining permanently exhausted and `IN_PROGRESS`; every eligible route successor preflights the stored predecessor target projection before creating an attempt-one event or writing targets; this child's fresh verification, review, and Standard curation are terminal only for this child.
- Progress signal: One newly satisfied `AC-...` criterion or one exact blocker-resolution result. Activity, another audit, or repeated evidence is not progress.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-USER | explicit human scope | this plan, `DEC-USER-SCOPE` | User directive dated 2026-08-14: create the necessary narrow child plan, attempt the blocker fix, and update the parent plan to point to it | Authorizes this plan's scope; native execution approval of exact bytes remains required. |
| AUTH-PARENT | exhausted direct-repository plan | `.agents/plans/2026-08-14-1528_atlas-explicit-reroute-destaged-recovery.md` | SHA-256 `89f99e8c4c00c2275d0058d5b0e69f34ff4e5a4fcc2b26c2f53044bc13abab8b`, `IN_PROGRESS` | T1 and T2 are complete; parent attempts 3/3, repair 1/1, and review rerun are consumed. This child does not reset them. |
| AUTH-REVIEW | exact terminal review Handoff | `/Users/kim/.omp/agent/sessions/-dev-atlas-app/2026-08-14T09-18-36-860Z_019fff90-f13c-7000-82fe-fe0a4c9199ec/RerouteRecoveryBackend/RerouteRecoveryBackend.RerouteFinalReviewer.md` | SHA-256 `1e954048af7df664d03e3fc307b05cacf6cbd094c65705cfcf80fa31a934cddc` | Authoritative blocker evidence: `RR-ROUTE-COMPLETE-DECISION-PREFLIGHT` and `RR-PROJECT-RULE-MANIFEST-INCOMPLETE`. |
| AUTH-PRODUCT | canonical Atlas framework contract | `.agents/ARCHITECTURE.md` and `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` | SHA-256 `5b5ad98edd3c1fdaa89cd78da1eb8f3b936b56275ef27dd0852969d70a6d14a6` and `dd37340921a790dcad21b76306f33be05c0e9cf2700130294cd71931187e92d1` | Intended behavior already requires route projection preflight before any transaction event or target write; no architecture decision changes. |
| AUTH-PLAN-REVIEW | native OMP plan review | `local://atlas-successor-preflight-recovery-plan.md` | Exact complete-byte revision selected by native approval | Not approved at publication. Every start requires fresh native approval and backend preflight for the exact bytes and a pending or resumable in-progress status. |

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-USER-SCOPE | AUTH-USER | Keep the recovery to the two review blockers: one parent expansion pointer, one production guard, one focused regression test, complete rule binding, and the locked assurance suffix. |
| DEC-SUCCESSOR-GUARD | AUTH-REVIEW plus AUTH-PRODUCT | In `_tx_successor`, preserve existing terminal-eligibility error precedence, then call `_route_guard(connector, record, predecessor.targets)` after confirming an `aborted` or `rolled-back` terminal and before `build_successor_plan`, `store_event`, or `execute_transaction`. No new helper or contract is needed. |
| DEC-LEGACY-JOURNAL-TEST | current `tests/test_atlas_tool.py` | Add one test covering both tampered bytes and an incomplete target set by constructing a complete source-policy-loadable attempt-zero `rolled-back` legacy route journal without either public façade operation. Store the malformed plan's event, then call low-level `atlas_transaction.execute_transaction` through the existing `InterruptingConnector` with `after_write=False`, source target allowlist, and source target rank; require `rolled-back`, then prove public `transaction.successor` returns `ROUTE_PREFLIGHT_PROJECTION_MISMATCH` without changing the post-rollback vault digest. Do not change source transaction policy. |
| DEC-PARENT-EXPANSION | AUTH-PARENT | Append one row to each existing AUTH-PARENT table: `Governing decisions`, `Blockers and recovery`, and `Critical anchors and assumptions`. Rewrite no other parent byte. The rows permanently leave parent T3/T4 non-ready, forbid parent reapproval/resumption and `DONE`, state that parent OUTP-T4 will never exist, and bind child terminals only to this child. |
| DEC-RULE-MANIFEST | AUTH-REVIEW | Every child Task Contract and Context Pack binds the complete applicable manifest listed under Execution policy, including `atlas-skill-surface` and `canonical-project-contracts`; no reviewer may repair an omitted manifest. |
| DEC-ASSURANCE | AUTH-REVIEW | High-consequence, one shared sequential lineage, fresh independent verification, one new child-outcome review, then required Standard curation. Parent review accounting remains consumed and is not reused. |
| DEC-CONVERGENCE | AUTH-USER | T1 gets one semantic implementation attempt. No retry, consolidated repair, review rerun, or diagnosis loop is authorized; any remaining blocker stops this child. |
| DEC-NO-DELIVERY | AUTH-USER | No Atlas living-state write, framework sync, architecture/contract/owner edit, credentials, destructive action, dotfiles-plan edit, commit, push, delivery, or shipping. |

## Scope, non-goals, and prohibited effects

- Read surfaces: AUTH-PARENT, AUTH-REVIEW, AUTH-PRODUCT, the current explicit-reroute target set, `_route_guard`, `_tx_successor`, transaction journal helpers, successor and route-preflight tests, and the complete rule manifest below.
- Change surfaces: the three-row expansion in AUTH-PARENT; one `_route_guard` call in `scripts/atlas_tool.py`; one regression test in `tests/test_atlas_tool.py`; local-plan lifecycle/projection updates; and zero or one directly impacted project-owned guidance delta only if T4 receives a complete frozen candidate.
- Non-goals: Do not change architecture, core contracts, Atlas skills/owners, transaction library semantics, public APIs, error strings, source behavior, OptMem state, or the sibling dotfiles plan. Do not revise, approve, or start `.agents/plans/2026-08-14-1139_atlas-source-reader-transport.md`; it remains blocked until a later source-reader revision rebinds `AUTH-5` and `BLK-7` to this child's terminal OUTP-T4 and post-repair hashes.
- Prohibited effects: Do not reset parent accounting, reuse the consumed parent review rerun, run `sync-framework`, write a bound Atlas instance, synthesize a compatibility bypass, broaden recovery semantics, or create another plan.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-PARENT-EXPANSION | direct-repository plan update | AUTH-USER, AUTH-PARENT | Exactly the three additive rows in DEC-PARENT-EXPANSION, written through the shared generation protocol. Reversible as unshipped bytes; never alter parent lifecycle/task state. |
| EFF-SUCCESSOR-GUARD | production code and test repair | AUTH-USER, AUTH-PRODUCT | One guard call and one focused test. Temporary-profile journal/vault writes are test fixtures only and are cleaned by existing fixture teardown. |
| EFF-CURATION | conditional project-guidance curation | AUTH-USER | Zero or one smallest backend-frozen directly impacted project-owned guidance delta. No user-level guidance, new rule, new skill, or unrelated cleanup. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-PARENT-PRESERVATION | Parent expansion pointer and consumed-accounting preservation | T1 | AUTH-PARENT plus DEC-PARENT-EXPANSION | T2, T3 |
| CONTRACT-SUCCESSOR-PREFLIGHT | Eligible legacy route successor must run exact reducer/renderer projection guard before attempt-one event or target writes | T1 | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md:214` plus DEC-SUCCESSOR-GUARD | T2, T3 |
| CONTRACT-RULE-MANIFEST | Complete immutable project-rule manifest | T1 | DEC-RULE-MANIFEST and exact revisions under Execution policy | T2, T3, T4 |
| CONTRACT-VERIFIED-TARGET | Fresh exact-target aggregate verification | T2 | Runtime-bound OUTP-T2 | T3 |
| CONTRACT-REVIEWED-TARGET | Fresh child-outcome Standards and Specification review | T3 | Runtime-bound OUTP-T3 | T4 |
| CONTRACT-CURATION-RESULT | Terminal Standard assessment | T4 | Runtime-bound OUTP-T4 | none |

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-PARENT-PLAN | `.agents/plans/2026-08-14-1528_atlas-explicit-reroute-destaged-recovery.md` | T1 | SHA-256 `89f99e8c4c00c2275d0058d5b0e69f34ff4e5a4fcc2b26c2f53044bc13abab8b` | Future parent recovery readers | AC-PARENT-EXPANSION, AC-WORKER-PROOF |
| TGT-ATLAS-TOOL | `scripts/atlas_tool.py`, `_tx_successor` and `_route_guard` | T1 | SHA-256 `99bfbf3512efa61c1450624b21a66cd407830030dd84df0b1d1e0209c56fe150` | `transaction.successor` dispatch at line 5741; route successors from direct and effect recovery | AC-SUCCESSOR-GUARD, AC-WORKER-PROOF |
| TGT-TOOL-TEST | `tests/test_atlas_tool.py`, successor and route-preflight fixtures | T1 | SHA-256 `8789b211f6890fbd4ba5eadad93ac1c322b042c3ce75cfe064637a2db04b8157` | Existing successor tests and four repaired route cases | AC-SUCCESSOR-GUARD, AC-WORKER-PROOF |
| TGT-PRESERVATION-SET | `.agents/ARCHITECTURE.md`; core contract; atlas-ask; atlas-source owner; atlas-route owner; `tests/test_atlas_harness_surface.py` | T1 | Exact hashes in AUTH-PRODUCT and Execution policy | Public classification, explicit reroute, effect preclaim, ordinary Atlas behavior | AC-WORKER-PROOF |
| TGT-VERIFICATION | Fresh dev-verification Handoff for the exact post-T1 target | T2 | Exact OUTP-T1 identity | T3 intake | AC-INDEPENDENT-VERIFIED |
| TGT-REVIEW | Fresh dev-code-review Handoff for exact VERIFIED target | T3 | Exact OUTP-T2 identity | T4 intake | AC-REVIEW-APPROVED |
| TGT-CURATION | Standard dev-continual-learning Handoff | T4 | Exact OUTP-T3 identity | Completion | AC-CURATION-TERMINAL |

## Execution policy

- Assurance: high-consequence
- Topology: one-owner-sequential
- Max concurrency: 1
- Isolation: one shared implementation lineage; fresh verifier; decorrelated fresh reviewer; neutral curator
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: one task at a time; target drift or generation-lock contention stops without adoption, overwrite, or retry.
- Decomposition: none; workers may not delegate or redesign the fix.
- Effect limit: EFF-PARENT-EXPANSION, EFF-SUCCESSOR-GUARD, EFF-CURATION
- Orchestrator profile: the one-owner sequential projection is pre-approved; full orchestration is not required.
- Convergence: exactly one T1 semantic attempt; child post-assurance repair is not authorized; one initial child review only.
- Applicable project-rule manifest, all mandatory in every Task Contract/Context Pack:
  - `.agents/AGENTS.md` SHA-256 `be5e676e6e20296e0bfe383a3e8ec0044bb8d1760b163af095494200bcdb0674`
  - `/Users/kim/.agents/AGENTS.md` SHA-256 `1ab60d54c0ba71feae07fe64361a0f2acd749ebf368290998a83a11cbd4998e9`
  - `rule://atlas-boundaries` SHA-256 `6b5cf49a7f45a98762b40ed43a827ac3669383f09cb2983b9fca9fbc22b444de`
  - `rule://atlas-reducer-discipline` SHA-256 `3f0e895218ad83696d99452af7aa08dce3ea6168648d52d93c44e00531e8b1c6`
  - `rule://atlas-skill-surface` SHA-256 `a5fdc3405f2b22864f32487c74fd123877759e0cb575b064330a79797ae4975c`
  - `rule://canonical-project-contracts` SHA-256 `4c7e6e788cdc03ff6dc4d5e24286f9a3616a9986f92f05bbe57c3dcbcd2a520c`
  - `rule://plan` SHA-256 `e57cde63de93714f4e30c67a3eda3e4f416987b22ee2412ec3cb7f4c98119448`
  - `rule://plan-impl-spec` SHA-256 `58d6fabcf02fcaf890849dc3b6451719463275731c26e9ca5b5175ab48c006cb`
  - `rule://plan-repo-storage` SHA-256 `cd537adc74d2908dc08e2c2e380568b9ca78cdaf292915bca28d620e0f898dbd`
  - `rule://plan-omp-transport` SHA-256 `df3a4c75c548770513dd738d4bb1fd95577b30d3eaf1c6d3b37c460bce2fb925`
- Preserved target hashes: atlas-ask `01f2e4b8e799dcfaf3892764c4a795540e69d3d0041739ed854cfb0f04e3dcca`; atlas-source owner `857db57c74a1b7ce6d320850b74db96484fc2e007a731212d87cbaf8ff0d553c`; atlas-route owner `ca403494e1e8464994c416abf4ef84d0ea21120933c86151df498623e6499b20`; harness test `8219d962c81cf4bfcaf040c0790f07ccb1ff50c66954d315a34de1f28c4793a8`.

## Tasks

- [x] T1. Record the child expansion and close successor route preflight with one focused attempt.
  completed 2026-08-14-2330
  - Owner: dev-implementation
  - Wave: W0
  - Depends on: none
  - Targets: TGT-PARENT-PLAN, TGT-ATLAS-TOOL, TGT-TOOL-TEST, TGT-PRESERVATION-SET
  - Contracts: CONTRACT-PARENT-PRESERVATION, CONTRACT-SUCCESSOR-PREFLIGHT, CONTRACT-RULE-MANIFEST
  - Criteria: AC-PARENT-EXPANSION, AC-SUCCESSOR-GUARD, AC-WORKER-PROOF
  - Effects: EFF-PARENT-EXPANSION, EFF-SUCCESSOR-GUARD
  - Output: OUTP-T1
  - Receiver: dev-implementation
  - Verification: VR-PARENT-EXPANSION, VR-SUCCESSOR-GUARD, VR-WORKER-PROOF
  - Lineage: shared
  1. Recheck AUTH-PARENT, AUTH-REVIEW, all three mutable targets, the preservation set, and every rule-manifest revision. Stop on semantic drift; do not rebind a changed contract inside this plan.
  2. Confirm the valid local authority and its managed projection `.agents/plans/2026-08-14-1843_atlas-successor-preflight-recovery.md` exist for the same identity. Through the direct-repository generation protocol, append one row to each named existing AUTH-PARENT table without rewriting any other existing byte:
     - In `Governing decisions`, append `DEC-EXPANDED-SUCCESSOR-RECOVERY`; revision is AUTH-REVIEW SHA-256 `1e954048af7df664d03e3fc307b05cacf6cbd094c65705cfcf80fa31a934cddc` plus child identity `2026-08-14-1843_atlas-successor-preflight-recovery`; execution effect states parent T1/T2 remain historical, parent attempts 3/3, repair 1/1, and sole review rerun remain consumed, parent T3/T4 remain permanently non-ready, parent cannot reach `DONE` and must not be re-approved or resumed, parent OUTP-T4 will never exist, and this child's terminals close only this child.
     - In `Blockers and recovery`, append `BLK-EXPANDED-SUCCESSOR-RECOVERY`; owner is `dev-ask`; recovery evidence is AUTH-REVIEW plus this child identity; affected tasks are T3 and T4; revision/approval boundary states no child authority resets or satisfies parent work; ready condition is permanently none under the parent identity, with explicit text that the parent must not be re-approved or resumed, cannot reach `DONE`, and will never emit OUTP-T4.
     - In `Critical anchors and assumptions`, append `ANC-EXPANDED-SUCCESSOR-RECOVERY`; kind is child recovery plan; exact reference is `local://atlas-successor-preflight-recovery-plan.md` and `.agents/plans/2026-08-14-1843_atlas-successor-preflight-recovery.md`; execution role states this is the sole narrow production-repair authority, its terminal Handoffs close only this child, and the parent remains permanently exhausted and `IN_PROGRESS`.
  3. In `_tx_successor`, after the existing `journal.status in {"aborted", "rolled-back"}` eligibility check and before computing `successor_id` or building/storing an attempt-one plan, insert exactly `_route_guard(connector, record, predecessor.targets)`. Reuse `_route_guard`; do not alter its signature, findings, or other callers.
  4. Add `AtlasToolTests.test_transaction_successor_rejects_legacy_tampered_and_incomplete_route_projections_without_writes`. For each mutation `tampered-bytes` and `incomplete-target-set`, use `transaction_args`; mutate the first target text by appending one LF or remove the final target; construct the malformed attempt-zero plan with existing `_event`, `_targets`, `_bind`, `_plan`, `_Port`, and `atlas_transaction.store_event`. Build a second `_Port` over `InterruptingConnector(fixture.connector(), path=args["targets"][0]["path"], after_write=False)`, call low-level `atlas_transaction.execute_transaction` with `plan.transaction_root`, the malformed plan, `target_allowlist=atlas_tool._target_allowed`, and `target_rank=atlas_tool._rank`, and require status `rolled-back`. Do not invoke the public `transaction.execute` or `transaction.recover` operations. Capture `vault.digest_tree`; invoke public `transaction.successor`; require first finding `ROUTE_PREFLIGHT_PROJECTION_MISMATCH`; recapture the digest and require exact equality. Use a fresh `temporary_profile` per subtest.
  5. Run the new test alone, then one command containing it plus the four existing repaired cases: `test_route_empty_complete_decision_rejects_current_pending_projection`, `test_route_empty_complete_decision_preserves_applied_history_and_routed_status`, `test_route_preflight_rejects_tampered_and_incomplete_exact_projections`, and `test_effect_preclaim_rejects_tampered_route_renderer_projection_without_writes`.
  6. Run `python3 -m unittest tests.test_atlas_tool`, `python3 -m unittest tests.test_atlas_harness_surface`, read-only `python3 scripts/atlas-instance.py check --name atlas`, and one provider-neutral classify-only public `/atlas-ask` request with tools and Atlas I/O unavailable. Require `{"first_owner":"atlas-source","ask_required":false,"router_write_set":[]}`. The historical OMP no-tools invocation is one attested recipe, not a required provider; record the exact invocation used. If no verified native or contract-equivalent classify-only capability exists, stop `transport-unavailable` rather than enabling Atlas I/O.
  7. Rehash before and after proof. Only AUTH-PARENT, `scripts/atlas_tool.py`, and `tests/test_atlas_tool.py` may change. Record no Atlas living effect, no framework sync, one semantic attempt used, and the exact parent accounting preserved.

- [x] T2. Independently verify the exact repaired child target.
  completed 2026-08-14-2347
  - Owner: dev-verification
  - Wave: W1
  - Depends on: T1
  - Targets: TGT-VERIFICATION
  - Contracts: CONTRACT-PARENT-PRESERVATION, CONTRACT-SUCCESSOR-PREFLIGHT, CONTRACT-RULE-MANIFEST, CONTRACT-VERIFIED-TARGET
  - Criteria: AC-INDEPENDENT-VERIFIED
  - Effects: none
  - Output: OUTP-T2
  - Receiver: dev-implementation
  - Verification: VR-INDEPENDENT-VERIFIED
  - Lineage: shared
  1. Consume only the exact post-T1 target, complete rule manifest, authority, and worker evidence; never repair.
  2. Rehash the mutable and preservation targets; rerun the new successor test, the five-case anchored command, both full impacted modules, read-only instance check, and the provider-neutral classify-only smoke with the exact required object.
  3. Inspect the guard placement and the complete source-policy-loadable rolled-back predecessor built with `store_event` plus low-level `atlas_transaction.execute_transaction` through `InterruptingConnector(after_write=False)`. Prove both malformed projections fail before attempt-one event/target writes, normal one-successor behavior remains, no source transaction policy changes, the parent expansion is additive and permanently non-resumable, and original explicit-reroute AC-1 through AC-6 remain preserved.
  4. Return aggregate VERIFIED, NOT VERIFIED, or INCONCLUSIVE with exact pre/post identities and deduplicated blocking criteria.

- [x] T3. Review the freshly verified child outcome once.
  completed 2026-08-15-0002
  - Owner: dev-code-review
  - Wave: W2
  - Depends on: T2
  - Targets: TGT-REVIEW
  - Contracts: CONTRACT-PARENT-PRESERVATION, CONTRACT-SUCCESSOR-PREFLIGHT, CONTRACT-RULE-MANIFEST, CONTRACT-VERIFIED-TARGET, CONTRACT-REVIEWED-TARGET
  - Criteria: AC-REVIEW-APPROVED
  - Effects: none
  - Output: OUTP-T3
  - Receiver: dev-implementation
  - Verification: VR-REVIEW-APPROVED
  - Lineage: shared
  1. Require exact OUTP-T2 VERIFIED, the complete immutable rule manifest, and a fresh decorrelated reviewer. This is the child outcome's sole initial review, not a parent rerun.
  2. Review Standards and Specification across the exact target. Require closure of `RR-ROUTE-COMPLETE-DECISION-PREFLIGHT` and `RR-PROJECT-RULE-MANIFEST-INCOMPLETE`; confirm `RR-FRESH-ROW-GUARD-UNEXECUTABLE` and the effect-preclaim fixture seam remain closed.
  3. Return APPROVED, CHANGES REQUIRED, or INCONCLUSIVE with one deduplicated blocker set. Any non-APPROVED result stops; no repair or review rerun is authorized.

- [x] T4. Complete the required neutral Standard assessment.
  completed 2026-08-15-0009
  - Owner: dev-continual-learning
  - Wave: W3
  - Depends on: T3
  - Targets: TGT-CURATION
  - Contracts: CONTRACT-RULE-MANIFEST, CONTRACT-REVIEWED-TARGET, CONTRACT-CURATION-RESULT
  - Criteria: AC-CURATION-TERMINAL
  - Effects: EFF-CURATION
  - Output: OUTP-T4
  - Receiver: dev-implementation
  - Verification: VR-CURATION-TERMINAL
  - Lineage: shared
  1. Inspect only the exact reviewed affected-artifact manifest and directly impacted project-owned guidance.
  2. Mutate guidance only with a complete backend-frozen candidate and exact EFF-CURATION authority; otherwise return NO DURABLE LEARNING.
  3. Return exactly CURATED or NO DURABLE LEARNING with the required seven-field payload. Do not start Atlas work or touch either dotfiles plan.

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-PARENT-EXPANSION | Exact AUTH-PARENT base and valid child identity | Parent gains only one appended row in each of the three named tables, names both child URIs, preserves `IN_PROGRESS` and T1/T2 history, and states T3/T4 are permanently non-ready, parent reapproval/resumption and `DONE` are forbidden, parent OUTP-T4 will never exist, and child terminals close only this child | TGT-PARENT-PLAN | T1 |
| AC-SUCCESSOR-GUARD | Eligible attempt-zero route journal with an `aborted` or `rolled-back` terminal and tampered bytes or incomplete targets | `transaction.successor` returns first finding `ROUTE_PREFLIGHT_PROJECTION_MISMATCH`; no attempt-one event or target write occurs; valid identical successor behavior remains applied once | TGT-ATLAS-TOOL, TGT-TOOL-TEST | T1 |
| AC-WORKER-PROOF | Exact post-T1 target | New test, five anchored cases, both full modules, read-only instance check, and classify-only smoke pass; only three authorized paths change; no living Atlas effect | TGT-PARENT-PLAN, TGT-ATLAS-TOOL, TGT-TOOL-TEST, TGT-PRESERVATION-SET | T1 |
| AC-INDEPENDENT-VERIFIED | Exact OUTP-T1 target in a fresh non-implementer context | Aggregate VERIFIED with identical pre/post hashes, complete rule manifest, both malformed successor cases, preserved normal successor and explicit-reroute behavior | TGT-VERIFICATION | T2 |
| AC-REVIEW-APPROVED | Exact OUTP-T2 VERIFIED target | Standards PASS, Specification PASS, Overall APPROVED; both named blockers closed; no blocking finding | TGT-REVIEW | T3 |
| AC-CURATION-TERMINAL | Exact reviewed target and affected-artifact manifest | CURATED with complete bound validation or NO DURABLE LEARNING; no unbound or user-level guidance write | TGT-CURATION | T4 |

## Verification / Done criteria

- [x] VR-PARENT-EXPANSION. Prove the parent points to this child without lifecycle reset.
  - Criterion: AC-PARENT-EXPANSION
  - Proof class: worker smoke
  - Scenario / environment / fixture: Rehash and structurally reread AUTH-PARENT immediately after the direct-generation update.
  - Evidence form: Exact before/after hash, the three appended rows, no other changed parent byte, and explicit preservation of `IN_PROGRESS`, T1/T2 history, permanently non-ready T3/T4, prohibited parent reapproval/resumption and `DONE`, nonexistent parent OUTP-T4, child-only terminal ownership, and consumed accounting.
  - Target recheck: TGT-PARENT-PLAN
  - Receiver: dev-implementation

- [x] VR-SUCCESSOR-GUARD. Prove legacy malformed route successors fail before writes.
  - Criterion: AC-SUCCESSOR-GUARD
  - Proof class: worker smoke
  - Scenario / environment / fixture: For each malformed plan, call `atlas_transaction.store_event`, then low-level `atlas_transaction.execute_transaction` through `InterruptingConnector(after_write=False)` with the source allowlist/rank and require a complete `rolled-back` journal; run the new two-subtest temporary-profile test and the existing valid one-successor test; never seed the malformed journal through public `transaction.execute` or `transaction.recover`.
  - Evidence form: Expected/observed first finding, equal pre/post vault digests, valid successor receipt attempt `1` and status `applied`.
  - Target recheck: TGT-ATLAS-TOOL, TGT-TOOL-TEST
  - Receiver: dev-implementation

- [x] VR-WORKER-PROOF. Exercise the complete impacted worker boundary.
  - Criterion: AC-WORKER-PROOF
  - Proof class: worker smoke
  - Scenario / environment / fixture: Run the exact T1 commands from `/Users/kim/dev/atlas/app`; no credentials or non-development profile writes.
  - Evidence form: Commands, exit codes, test counts, exact classification object, instance-check result, target hashes, and effect `none` for living Atlas state.
  - Target recheck: TGT-PARENT-PLAN, TGT-ATLAS-TOOL, TGT-TOOL-TEST, TGT-PRESERVATION-SET
  - Receiver: dev-implementation

- [x] VR-INDEPENDENT-VERIFIED. Freshly prove the exact child target.
  - Criterion: AC-INDEPENDENT-VERIFIED
  - Proof class: independent verification
  - Scenario / environment / fixture: A fresh verifier repeats every T2 check and independently inspects normal and malformed successor paths plus complete rule binding.
  - Evidence form: Criterion map, fixtures, pre/post identities, aggregate verdict, and deduplicated blockers.
  - Target recheck: TGT-VERIFICATION
  - Receiver: dev-implementation

- [x] VR-REVIEW-APPROVED. Perform one final Standards and Specification review.
  - Criterion: AC-REVIEW-APPROVED
  - Proof class: review
  - Scenario / environment / fixture: Fresh decorrelated reviewer receives exact VERIFIED target, both historical blocker IDs, and complete immutable rule manifest.
  - Evidence form: Standards, Specification, Overall verdicts; blocker closures; blockers/advisories; exact target identity.
  - Target recheck: TGT-REVIEW
  - Receiver: dev-implementation

- [x] VR-CURATION-TERMINAL. Complete one narrow Standard assessment.
  - Criterion: AC-CURATION-TERMINAL
  - Proof class: other authorized class
  - Scenario / environment / fixture: Inspect only reviewed affected artifacts; require a frozen evaluation binding before any guidance mutation.
  - Evidence form: Exactly Updated, Added, Removed, Skipped, Validation, Deep candidate, and Papercut outcome plus terminal result.
  - Target recheck: TGT-CURATION
  - Receiver: dev-implementation

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-T1 | T1 | Exact parent/code/test target plus worker evidence | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with criteria, exact hashes, one-attempt accounting, parent preservation, checks, effects, blockers, and one receiver. |
| OUTP-T2 | T2 | Exact verifier Handoff | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with verifier target, criterion evidence, fixtures, pre/post identities, aggregate verdict, blockers, and one receiver. |
| OUTP-T3 | T3 | Exact child final-review Handoff | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with reviewer separation, both axes, overall verdict, blocker closures/set, advisories, target, and one receiver. |
| OUTP-T4 | T4 | Exact Standard curation Handoff | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with curator target, terminal result, seven-field payload, effects, blockers, and one receiver. |

## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-PLAN-APPROVAL | native-plan-reviewer | Exact local authority path, complete bytes/SHA, PENDING or resumable IN_PROGRESS status, structural validation, native approval, backend preflight | all | Plan presence or projection never approves execution | Exact current local revision is approved and fresh preflight is eligible. |
| BLK-SOURCE-DRIFT | dev-implementation | Rehash every authority, mutable target, preservation target, and rule | all | Any semantic drift changes the one-line fix or proof contract | All bound revisions match before T1; otherwise stop for revised authority. |
| BLK-PARENT-GENERATION | dev-implementation | Direct-repository generation ownership, safe target, exact base, postcondition | T1-T4 | Parent overwrite, contention, or ambiguous state is prohibited | Exact three-row addition succeeds once with verified postcondition. |
| BLK-T1-FAILURE | dev-implementation | OUTP-T1 with reproduction, target/effect state, and exact blocker | T2-T4 | One semantic attempt only; no repair/retry | T1 completes every owned criterion. Any remaining blocker stops the child. |
| BLK-VERIFICATION | dev-verification | OUTP-T2 aggregate VERIFIED on exact target | T3-T4 | Verifier never repairs | Fresh exact-target verdict is VERIFIED. |
| BLK-REVIEW | dev-code-review | OUTP-T3 Standards PASS, Specification PASS, Overall APPROVED | T4 | One child review; no rerun or repair | Exact VERIFIED target is APPROVED with both named blockers closed. |
| BLK-CURATION | dev-continual-learning | OUTP-T4 CURATED or NO DURABLE LEARNING | T4 | Deep work or unbound candidates require another route | One narrow terminal Standard result. |
| BLK-AUTHORITY-CHANGE | dev-ask | Revised human authority for changed scope, contract, effects, topology, or delivery | all | Current plan cannot absorb expansion | A new exact approved revision exists; otherwise preserve and stop. |

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-PARENT | parent authority | `.agents/plans/2026-08-14-1528_atlas-explicit-reroute-destaged-recovery.md` SHA-256 `89f99e8c4c00c2275d0058d5b0e69f34ff4e5a4fcc2b26c2f53044bc13abab8b` | Receives only one appended row in each of the three named tables; remains permanently exhausted and `IN_PROGRESS`, is never re-approved or resumed, cannot reach `DONE`, and never emits OUTP-T4. |
| ANC-CHILD | local plan identity | `local://atlas-successor-preflight-recovery-plan.md`; projection `.agents/plans/2026-08-14-1843_atlas-successor-preflight-recovery.md` | Sole new recovery authority after native approval. |
| ANC-REVIEW | blocker authority | Reviewer Handoff SHA-256 `1e954048af7df664d03e3fc307b05cacf6cbd094c65705cfcf80fa31a934cddc` | Exact two-blocker frontier; no broad audit. |
| ANC-SUCCESSOR | code seam | `scripts/atlas_tool.py` `_tx_successor` lines 2155-2227 and `_route_guard` lines 1797-1870 at base SHA-256 `99bfbf3512efa61c1450624b21a66cd407830030dd84df0b1d1e0209c56fe150` | Insert one guard after eligibility and before any attempt-one construction/write. |
| ANC-TEST | proof seam | `tests/test_atlas_tool.py` `InterruptingConnector` lines 578-601, route-preflight lines 3565-3586, and successor lines 3847-3906 at base SHA-256 `8789b211f6890fbd4ba5eadad93ac1c322b042c3ce75cfe064637a2db04b8157` | Reuse existing low-level journal, interruption, and temporary-profile patterns; preserve valid successor behavior. |

- Assumptions: none

## Completion Summary

- Delivered: the exhausted parent gained only its three child-expansion rows; `_tx_successor` now reuses `_route_guard(connector, record, predecessor.targets)` after terminal eligibility and before every attempt-one construction or write; the focused legacy-journal regression covers tampered bytes and an incomplete target set while preserving the valid one-successor path.
- Proof: worker smoke passed the new test, five anchored cases, 86 Atlas tool tests, 21 harness tests, the read-only instance check, and the no-tools public classification smoke. `agent://SuccessorFreshVerifier` returned aggregate `VERIFIED`; `agent://SuccessorFinalReviewer` returned Standards `PASS`, Specification `PASS`, Overall `APPROVED`; `agent://SuccessorNeutralCurator` returned `NO DURABLE LEARNING` with no guidance or papercut effect.
- Effects: product changes are limited to the parent plan, `scripts/atlas_tool.py`, and `tests/test_atlas_tool.py`; local-authority/projection lifecycle bytes record this completed child. No Atlas living-state write, framework sync, architecture/contract/owner change, guidance mutation, credential use, destructive action, commit, push, delivery, or shipping occurred.
- Decisions: reused the existing guard and source transaction policy; constructed only the synthetic malformed predecessor journals at the low-level fixture seam; made no architecture or guidance update because the canonical contract already stated the invariant and no frozen curation candidate existed.
- Residual risk: no blocking child criterion or review advisory remains. Model-family decorrelation was unavailable but was not a Task Contract stop condition. The parent remains permanently exhausted and `IN_PROGRESS`, must never be re-approved or resumed, cannot reach `DONE`, and will never emit parent OUTP-T4; this completion closes only the child.
