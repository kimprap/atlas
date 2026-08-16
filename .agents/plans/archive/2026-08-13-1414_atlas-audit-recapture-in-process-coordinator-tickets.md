# Atlas audit recapture in-process coordinator executor plan

**Datetime**: 2026-08-13-1414
**Authority kind**: local-authority
**Scope**: Contract-first implementation of the Atlas hosted audit-recapture coordinator as one clean-cutover repository lineage
**Summary**: One dependency-ready vertical ticket keeps every shared contract and mutable surface under one semantic implementation owner, exercises the real hosted seam early, completes the clean cutover, and proves AC-01 through AC-12 without Atlas or shipping effects.
**Status**: CLOSED

## Objective

- Outcome: OUT-ATLAS-AUDIT-RECAPTURE-IN-PROCESS-COORDINATOR-TICKETS
- Observable end state: One final repository lineage implements the exact hosted `source.audit_recapture` specification, contains none of the retired prompt/filesystem/successor transport, preserves all named ordinary Atlas behavior, and carries complete worker smoke evidence ready for high-consequence independent assurance.
- Progress signal: AC-01 through AC-12 each have one implementation owner and one proof recipe; the real `execute_hosted` to coordinator to qualified-host to quality-validation seam runs before the remaining cutover work, and the final focused/full/disposable proof closes without a specification or route blocker.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-PLAN | Approved engineering plan | `local://atlas-audit-recapture-in-process-coordinator-plan.md` | `sha256:3c393bd33559550e11d64cd6d6849a7001d5ebe39fb985e366838da7afbbbccd` | Exact bytes are human-approved and current. |
| AUTH-SPEC | Approved Engineering Specification | `local://atlas-audit-recapture-in-process-coordinator-specification.md` | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Status is Ready for dev-ticketing; the current assignment approves this exact revision for projection. |

The immutable planner assignment is backend-delivered context rather than a separately exposed artifact revision. It adds no authority beyond AUTH-PLAN and AUTH-SPEC.

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-HOSTED-COORDINATOR | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Replace prompt, JSON, worker, and filesystem reconstruction with one repository-owned in-process hosted coordinator and non-serializable callback host. |
| DEC-CAPABILITY-BOUNDARY | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | A qualified host is globally required before connector access; lack of one required native variant for an otherwise qualified host is source-local, and neither case permits fallback. |
| DEC-CLOSED-NATIVE-V1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Accept only the proved `functions.read-v1` and `github.file_read-v1` native shapes, route repository-file GitHub URLs only to native GitHub file read, and fail closed on any unapproved shape. |
| DEC-SEQUENTIAL-EXACT-SEVEN | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Freeze exactly seven unique caller-order identities before callbacks, process sequentially with one raw source payload live at most, and recheck canonical revisions before a clean result. |
| DEC-READ-ONLY-NONRETENTION | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Permit no Atlas mutation or filesystem evidence write, expose no raw payload/checklist/exception data, and close coordinator-owned references without claiming RAM erasure. |
| DEC-CLEAN-CUTOVER | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Remove every named old operation, mode, schema, descriptor, root, cleanup, successor, worker, caller, test, eval, and prose reference with no alias, shim, dual mode, or runtime fallback. |
| DEC-COHESIVE-OWNER | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Keep the cross-cutting contracts, owners, runtime, deletions, compatibility, regressions, and smoke on one shared lineage under one semantic implementation owner; internal phases are not independent tickets. |
| ADR-0001 | `sha256:f80492a4e4d2e0231ce350e70d0cf82a43ccf12fafbaf9b8faa29dfcacd742cb` | Preserve one `/atlas-ask` entry, one selected owner, and one outer result. |
| ADR-0002 | `sha256:db18072d0f470204fffc6aaf6c6f7ebc02f7765a2f439471a51aae5362c29bdb` | Keep product-package changes separate from bound-instance state. |
| ADR-0003 | `sha256:691406dec27eda2fdd358b2e9d7d6181c9ff908a9055e5d8575d9562989fcc55` | Keep manifest and artifact Markdown canonical; callback output is transient evidence, never state. |
| ADR-0004 | `sha256:5a65bf9ec6aaa216d65e82a6ff212ceb7d0206f3f8d0a8c0c04eb26b5ff50d5c` | Preserve the acquisition boundary; recapture observes frozen sources and does not crawl or ingest. |
| ADR-0005 | `sha256:0599c128aa6cbd24b8745bcb1a099e4f8d8596dcb375feba9ffa20f2a0c142a5` | This engineering route neither retries T13 nor mutates the instance. |

## Scope, non-goals, and prohibited effects

- Read surfaces: AUTH-PLAN, AUTH-SPEC, the exact target-map baselines, their direct callers and fixtures, the accepted ADRs, and the repository commands required by the fixed proof recipes.
- Change surfaces: Only TGT-CANONICAL-CONTRACTS, TGT-OWNER-TOPOLOGY, TGT-COORDINATOR-RUNTIME, TGT-HOSTED-FACADE, TGT-RETIRED-SCHEMA, TGT-REGRESSION-PROOF, and TGT-NATIVE-CASSETTES; TGT-PRESERVATION-ANCHORS is rechecked but remains unchanged.
- Non-goals: A public T13 audit; T14 through T19; connector/profile/vault/bound-instance work; acquisition, ingestion, resummarization, routing, transaction, refresh, migration, index, registry, or source-state behavior; provider/model product branches; concurrency; nonempty native projections; a public command or second outer result; implementation outside the target map.
- Prohibited effects: No plan/projection, active profile, vault, bound instance, source artifact, registry, credential, external service, memory-bank, shipping, deployment, release, commit, push, rollback, compatibility/fallback transport, persistent evidence, temporary recapture root, or raw-data retention effect. The ticketing attempt itself authorizes only creation of this session-local ticket set; the effects below are limits for later dev-implementation execution.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-REPOSITORY-LINEAGE | Reversible repository working-tree change | AUTH-PLAN AUTH-SPEC | Only target-map product files may change, one obsolete schema may be deleted, and the new ADR/cassettes may be created; no commit, push, release, or bound-state effect. The final lineage must be internally consistent and whole-lineage reversible. |
| EFF-DISPOSABLE-PROOF | Disposable local verification process and files | AUTH-SPEC | Only synthetic fixtures, test-runner temporaries, and the specified disposable hosted smoke may be used; no bound instance, live T13 audit, external source call, credential, persistent raw evidence, or shipping effect. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-HOSTED-FACADE-V1 | Exact `capabilities(connector=None, host keyword)`, ordinary `execute`, hosted-only `execute_hosted`, operation discovery, `CAPABILITY_UNAVAILABLE`, and removed-operation `OP_UNKNOWN` behavior | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-HOST-V1 | Non-serializable repository-owned `AuditRecaptureHostV1`, qualification, `observe` and `assess` callback reachability, global capability stop, source-local unavailable variant, and no retry/substitution | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-REQUEST-FREEZE-V1 | Closed request containing only seven unique source IDs; complete pre-callback manifest/artifact freeze, request-order identities, cohort binding, attributable freeze inability, and final revision recheck | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-NATIVE-OBSERVATION-V1 | Closed `functions.read-v1` and `github.file_read-v1` objects, exact GitHub URL grammar, variant selection, URL/origin/adapter/UTF-8 validation, exact bytes/hash, empty current projection ranges, and closed code-only inability | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-ASSESSMENT-QUALITY-V1 | Source-local assessment packet, exact ordered seven-item checklist, one assessment and one `quality.validate_summary` call per accepted observation, audit identity, and lossless ordered findings | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-ITEM-AGGREGATE-V1 | Closed item/receipt/inability shapes, exactly seven ordered slots, deterministic `blocked` then `cancelled` then `issues` then `clean` precedence, callback/cancellation/drift accounting, and stable coordinator findings | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-ISOLATION-CLOSURE-V1 | Minimal callback arguments, sequential source-local lifetime, no sibling/connector/effect reachability, no writes or returned raw data, `aggregate_effect:none`, `persistent_evidence_created:false`, and logical transient closure without a RAM-erasure claim | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-OUTER-TOPOLOGY-V1 | Sole `/atlas-ask` entry, one selected `atlas-audit` owner, one hosted coordinator call, unchanged outer-result schema/mapping, no recapture successor/depth-2 worker, and fail-closed capability presentation | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |
| CONTRACT-CUTOVER-COMPATIBILITY-V1 | Exact removal inventory with no aliases plus preservation of ordinary source ingestion, resummarization, extractor, non-audit quality callers, routing, transactions, legal successors, command forwarding, connector semantics, and historical T1 through T12 state | T1 | `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | none |

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-CANONICAL-CONTRACTS | `.agents/ARCHITECTURE.md`; `docs/adr/INDEX.md`; new `docs/adr/0006-hosted-audit-recapture-coordinator.md`; `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`; `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md`; `.agents/skills/atlas-core/assets/source-summary-quality-guide.md`; `.agents/skills/atlas-core/SKILL.md`; `.agents/AGENTS.md` | T1 | Existing digests respectively `85758a598c7bc79da8fb6bb3c435fdc390c8918e72a56197a8c6c040f488c921`, `87173a6bbc5f09b08dfeac25d710b4800d4a39ee88d8f0cdd10b3a888da5a1fa`, absent, `8670987c3dc99f28b2ecfeca8121bcc3bd8c65757840b5c2a7df367daa600642`, `6dd928067b5a9991d451b60fab88a65f8a665899eaf9a4958ec1653b785785f2`, `a4e6fea9b312b4a9d260b65e37552b424b75ab3acbf90b0ec5b910253559117d`, `5c4940b7913d048b759fc39dac72bef6e2ed72929b499a54a8ebffd90e2446f7`, `6a8119ec36f7ac4a44160ae085c53582b4b1c1ade4cc5bdc479632c1e4abb06e` | Architecture readers, owner skills, operation inventories, eval contracts, runtime implementer | AC-01 AC-02 AC-03 AC-07 AC-08 AC-09 AC-10 AC-11 AC-12 |
| TGT-OWNER-TOPOLOGY | `.agents/skills/atlas-ask/SKILL.md`; `.agents/skills/atlas-ask/owners/atlas-audit/OWNER.md`; `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md` | T1 | Digests `e37099c09dfee2b10cadcc39e65beb9bbbdf417681704947cf25810fa90ad20f`, `39ac925eeb0e1adb79cf3c714ff96ea53ab94ce3d8d5a894aa50240100aa5730`, `8d974ea87f753face43a435ff7553ceed6e26acf4f63844444a30822b49e20c5` | `/atlas-ask`, selected audit owner, ordinary source owner, workflow-result mapping, harness-surface assertions | AC-01 AC-02 AC-03 AC-07 AC-08 AC-09 AC-10 AC-11 AC-12 |
| TGT-COORDINATOR-RUNTIME | `scripts/atlas_source.py`, including retained `extract_reader_result`, removal of `project_recapture_schema`, and new request/host/native/freeze/assessment/item/aggregate/closure logic | T1 | `579e634eff094a496f10f2ca512c379d73d463aead2203c602c6b7c5083523f5` | `scripts/atlas_tool.py`, `scripts/atlas_quality.py`, source tests, native cassettes, frozen connector fixtures | AC-01 AC-03 AC-04 AC-05 AC-06 AC-07 AC-08 AC-09 AC-10 AC-11 AC-12 |
| TGT-HOSTED-FACADE | `scripts/atlas_tool.py`, including hosted capability binding, `execute_hosted`, hosted-only dispatch, folded freeze entry, and removal of old operation/schema dispatch | T1 | `5c4fa9d9c24d7b5d28dd17cc6bb913a75de1da360d9be8c85ac7c3f9d7a7357b` | Existing façade callers, CLI, coordinator, connector fixtures, tool tests, operation discovery | AC-01 AC-03 AC-04 AC-05 AC-07 AC-08 AC-09 AC-10 AC-11 AC-12 |
| TGT-RETIRED-SCHEMA | Delete `.agents/skills/atlas-core/assets/source-recapture-result.schema.json` and every loader/projection/caller/export/reference | T1 | `c43b7bc909d2beca33158f5011577d2465cff64c7b039fbbc09f4ba0726f624e` | Old `source.recapture_schema` dispatch, source projection code, tests, evals, prose, inventories | AC-10 AC-12 |
| TGT-REGRESSION-PROOF | `.agents/skills/atlas-core/assets/evals/agent-tooling.json`; `tests/test_atlas_source.py`; `tests/test_atlas_tool.py`; `tests/test_atlas_quality.py`; `tests/test_atlas_harness_surface.py`; focused/full command evidence and disposable hosted smoke | T1 | Digests `2f9d7042fa0c3b6e195e7ca5366c9a099e9a7e674f1b2d296c065e5720f241db`, `a045121f5da6a49219299d12ea49eea3bc1bf685447178bd110aae57e59d59e1`, `9828b6dfd9767deb1e3c66a09d2cf4572d2f4cbac0fe731024d190b663a1cae3`, `2866e395c69ca06929823ec740fa7a4e222065d2e40b585e87b7a47223718231`, `30fc230e6b7495e75dfa9cd0d8dfe9b16dfed3bba2a9eddfdc0c16cc74f96fb2`; proof evidence not yet produced | Coordinator/façade/quality fixtures, owner topology assertions, forbidden-surface inventory, disposable connector/tree | AC-01 AC-02 AC-03 AC-04 AC-05 AC-06 AC-07 AC-08 AC-09 AC-10 AC-11 AC-12 |
| TGT-NATIVE-CASSETTES | New `tests/cassettes/native_reader/v1/functions-read.json` and `tests/cassettes/native_reader/v1/github-file-read.json` | T1 | Both absent at the verified specification baseline | Exact closed native validators and hosted adapter integration; inert credential-free synthetic bodies only | AC-01 AC-03 AC-05 AC-12 |
| TGT-PRESERVATION-ANCHORS | Unchanged `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json`; `scripts/atlas_quality.py`; `scripts/atlas_connector.py`; `.agents/commands/atlas-ask.md` | T1 | Digests `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`, `b09f7ff570fcce4732b6e44b5d00c234b4967125b723d7ac1eeac3ef271742b3`, `5650a5ac58a36bda1322efc8dbe74a268dc8df438538ab69600038359e2fd5d0`, `ad86431e28edb7c3d8c125a062f2567d07728e57846fda58dbcf49f5ee2c8292` | Outer result validation, existing quality helpers and callers, connector read/revision API, argument-preserving command wrapper | AC-02 AC-05 AC-06 AC-08 AC-11 AC-12 |

## Execution policy

- Assurance: high-consequence
- Topology: one-owner-sequential
- Max concurrency: 1
- Isolation: One qualified implementation worker owns the complete shared lineage; callbacks remain sequential and source-local at application runtime, and independent assurance receives only the final immutable target.
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: No parallel repository mutation, no sibling semantic authority, and no second ticket may edit or reinterpret any target or shared contract.
- Decomposition: Prohibited. Contract updates, the early real-seam tracer, complete runtime behavior, deletion, compatibility regression, and proof are ordered phases of T1 rather than independent tickets because they share mutable contracts/runtime and no intermediate state is releasable.
- Effect limit: EFF-REPOSITORY-LINEAGE EFF-DISPOSABLE-PROOF
- Orchestrator profile: High-consequence one-owner sequential execution under a fresh backend-bound Role Profile; dev-implementation retains lifecycle, independent-verification, review, and recovery ownership.
- Graph validation: One stable ticket name, one task, no dependency edges, one shared lineage, one implementation owner, no mutable ownership overlap, no fan-in, and no current blocker. The one-node graph is acyclic and is the minimum faithful graph; splitting would create a horizontal contract/test scaffold or overlapping authority rather than an independent vertical objective.
- Criterion accounting: AC-01 through AC-12 each have exactly one Acceptance row owned by T1 and exactly one corresponding VR recipe. No criterion is shared with another implementation task.

## Tasks

- [ ] T1. Implement `ATLAS-AUDIT-RECAPTURE-HOSTED-CLEAN-CUTOVER-V1` as one contract-first vertical repository lineage.
  - Owner: atlas-audit-recapture-implementation-owner
  - Wave: W0
  - Depends on: none
  - Targets: TGT-CANONICAL-CONTRACTS, TGT-OWNER-TOPOLOGY, TGT-COORDINATOR-RUNTIME, TGT-HOSTED-FACADE, TGT-RETIRED-SCHEMA, TGT-REGRESSION-PROOF, TGT-NATIVE-CASSETTES, TGT-PRESERVATION-ANCHORS
  - Contracts: CONTRACT-HOSTED-FACADE-V1, CONTRACT-HOST-V1, CONTRACT-REQUEST-FREEZE-V1, CONTRACT-NATIVE-OBSERVATION-V1, CONTRACT-ASSESSMENT-QUALITY-V1, CONTRACT-ITEM-AGGREGATE-V1, CONTRACT-ISOLATION-CLOSURE-V1, CONTRACT-OUTER-TOPOLOGY-V1, CONTRACT-CUTOVER-COMPATIBILITY-V1
  - Criteria: AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-12
  - Effects: EFF-REPOSITORY-LINEAGE, EFF-DISPOSABLE-PROOF
  - Output: OUTP-ATLAS-AUDIT-RECAPTURE-CLEAN-CUTOVER
  - Receiver: dev-implementation
  - Verification: VR-01, VR-02, VR-03, VR-04, VR-05, VR-06, VR-07, VR-08, VR-09, VR-10, VR-11, VR-12
  - Lineage: shared

### Ticket: ATLAS-AUDIT-RECAPTURE-HOSTED-CLEAN-CUTOVER-V1

#### Authority

- Governing specification: AUTH-SPEC, exact revision `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba`.
- Governing approved plan: AUTH-PLAN, exact revision `sha256:3c393bd33559550e11d64cd6d6849a7001d5ebe39fb985e366838da7afbbbccd`.
- Required human approvals: Current approval of those exact bytes is sufficient. Any change named by BLK-AUTHORITY-DRIFT, BLK-NATIVE-SHAPE-DRIFT, or BLK-ROUTE-CHANGE stops before affected mutation and requires the named owner; the ticket cannot approve its own revision.

#### Objective

- Produce one observable, raw-free, exact-seven hosted recapture path through the real façade/coordinator/host/quality seam, retire every old recapture transport surface in the same final lineage, preserve the named ordinary Atlas behavior, and return exact-revision smoke evidence for AC-01 through AC-12.

#### Ownership

- May read: The exact authority, target-map baselines, direct callers/fixtures, and commands named by VR-01 through VR-12.
- May change or produce: Only the mutable/created/deleted surfaces in TGT-CANONICAL-CONTRACTS, TGT-OWNER-TOPOLOGY, TGT-COORDINATOR-RUNTIME, TGT-HOSTED-FACADE, TGT-RETIRED-SCHEMA, TGT-REGRESSION-PROOF, and TGT-NATIVE-CASSETTES.
- Must not change: TGT-PRESERVATION-ANCHORS; `.agents/commands/atlas-ask.md`; `scripts/atlas_connector.py`; the outer result schema; ordinary source, route, transaction, recovery, acquisition, profile, vault, bound-instance, plan, shipping, and public-command behavior; any repository path outside the target map.
- Fixed shared interfaces or state: CONTRACT-HOSTED-FACADE-V1, CONTRACT-HOST-V1, CONTRACT-REQUEST-FREEZE-V1, CONTRACT-NATIVE-OBSERVATION-V1, CONTRACT-ASSESSMENT-QUALITY-V1, CONTRACT-ITEM-AGGREGATE-V1, CONTRACT-ISOLATION-CLOSURE-V1, CONTRACT-OUTER-TOPOLOGY-V1, and CONTRACT-CUTOVER-COMPATIBILITY-V1. The worker implements them exactly and cannot reinterpret, split, or reassign them.

#### Dependencies

- Blocking ticket names: none. This is the sole node in the implementation DAG.
- Exact upstream artifacts: AUTH-PLAN and AUTH-SPEC. No ambient sibling state or separately exposed upstream Handoff is required.
- Baseline readiness: Every existing digest in the Target map must still match or receive a backend-confirmed nonmaterial rebind before T1 becomes ready; a material mismatch invokes BLK-AUTHORITY-DRIFT.

#### Acceptance

- The single authoritative ownership rows are AC-01 through AC-12 in the Acceptance table below. T1 owns every row exactly once; no other ticket shares, verifies on behalf of, or changes that ownership.
- Compatibility and degraded behavior are part of those owned criteria, not optional follow-up work. A source-local inability, malformed callback, exception, cancellation, known source drift, or global revision uncertainty must produce the exact specified non-clean behavior without retry or fallback, while ordinary non-recapture behavior remains unchanged.

#### Verification

- VR-01 through VR-11 require exact-revision worker smoke over the named real interfaces, boundaries, fixtures, and preserved behavior. Source-text assertions alone are insufficient where the specification requires runtime behavior.
- VR-12 is the cohesive terminal proof: focused suites, the complete applicable suite once, and the real disposable hosted seven-source smoke with deterministic genuine-shape native/semantic adapters, zero mutation/write calls, raw-canary absence, unchanged disposable tree digest, and exact final target identity.
- dev-implementation must then send the one immutable final lineage through decorrelated dev-verification and the one eligible final dev-code-review pass before completion; this ticket does not perform or pre-claim either verdict.

#### Execution policy

1. Rebind AUTH-PLAN, AUTH-SPEC, target baselines, capability-proof shapes, and the high-consequence one-owner profile. Stop on a material mismatch; do not preserve old behavior as fallback.
2. Update `.agents/ARCHITECTURE.md` first. Only after that normative change exists in the same lineage, add ADR 0006 and update every shared registry, guardrail, quality guide, core inventory, front-door, audit-owner, source-owner, and operation contract to the exact fixed interfaces. Architecture remains normative; the ADR records rationale only.
3. Early real-seam tracer bullet: after the contract update and before broad cleanup, implement and exercise the production `atlas_tool.execute_hosted` to `atlas_source.audit_recapture` to qualified `AuditRecaptureHostV1.observe` and `assess` to one `atlas_quality.validate_summary` per accepted source to raw-free ordered aggregate path using exactly seven mixed versioned cassette results. Also exercise global host absence before connector access and ordinary JSON/CLI capability-unavailable behavior. This is real production code and closed runtime validation, not a scaffold, mock transport, prompt/JSON/file reconstruction, compatibility branch, or separate lineage. It is an early checkpoint only; it does not make the ticket or an intermediate target complete.
4. Complete every exact freeze, native validation, packet, checklist, finding, source-local failure, exception, cancellation, revision recheck, precedence, outer mapping, isolation, read-only, and transient-closure behavior. Process sources sequentially and retain at most one source-local raw payload/packet; add no concurrency, retry, substitute evidence, or nonempty native projection.
5. Complete the clean cutover in that same lineage: delete the recapture schema asset and remove `audit-recapture-v1`, the audit-to-source successor, recapture depth-2 workers/preflight, `source.audit_cohort`, `source.recapture_schema`, schema loading/projection, temporary roots/files/descriptors/cleanup, every caller/allowlist/export/fixture/eval/prose reference, and any alias or fallback acceptance path.
6. Finish the behavior-level regression and forbidden-surface suite, exact native cassettes, ordinary-compatibility coverage, and the cohesive VR-12 proof. Do not run a public T13 audit or use a bound instance. Freeze the exact final single-lineage target only after every worker-smoke recipe passes.
7. Return OUTP-ATLAS-AUDIT-RECAPTURE-CLEAN-CUTOVER in one Common Handoff to dev-implementation. Any implementation defect is repaired only through dev-implementation's inherited high-consequence recovery budget; no worker, ticket, or assurance role invents a second lineage or restores consumed lifecycle state.

- Decomposition permission: none.
- Isolation and integration needs: One owner, one working lineage, sequential mutation, no neutral integration task, final immutable-target verification only.
- Material decision gates: Open decisions are none. Any unsupported native shape, nonempty projection need, concurrency request, connector change, persistent evidence, fallback, changed public behavior, changed outer schema, or expanded target/effect returns to the specification or route owner through the matching blocker.

#### Completion output

- Required artifacts: One exact final repository target identity, complete changed/deleted/created path inventory, implementer smoke evidence for VR-01 through VR-12, preserved-anchor rehashes, forbidden-surface result, command/scenario evidence, and one Common Handoff. No implementation artifact is produced by ticketing itself.
- Next receiver: dev-implementation, which consumes the worker result, owns independent assurance and recovery, and may not treat the worker Handoff alone as completion.

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-01 | Qualified host with both native variants; host absent; strict assessment absent; one required source-native callback absent; ordinary execute and CLI request | Hosted discovery only for a qualified host; genuine native dict/list objects cross in process; global absence causes zero connector/callback work; per-source absence yields one inability with six siblings; no reconstruction or fallback | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES | T1 |
| AC-02 | Exact-seven source-quality route and representative legal non-recapture successor | `/atlas-ask` selects one `atlas-audit` owner and yields one outer result; recapture depth-2 gate and audit-to-source successor are absent; other legal topology and unchanged outer schema remain valid | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS | T1 |
| AC-03 | Seven clean mixed URL-kind captures through hosted façade and coordinator | One hosted `source.audit_recapture` call owns freeze, native validation, evidence construction, assessment, quality validation, ordered aggregation, and transient closure; old operations are unknown | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES | T1 |
| AC-04 | Six, eight, duplicate, malformed, reverse-order seven, malformed callback wrappers, and cancellation after a settled prefix | Invalid requests invoke no callbacks; every trustworthy freeze yields exactly seven unique request-order slots with exact identity/call accounting and no missing/duplicate/late collector | TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF | T1 |
| AC-05 | LF, CRLF, multibyte UTF-8, both cassettes, malformed/truncated/non-text/empty observations, wrong adapter or identity, hash mismatch, projection fixtures, and revision drift | Exact byte count/SHA/reconstruction and manifest/artifact/binding identity either match or fail closed at the specified source-local/global boundary before unsafe assessment; no changed evidence is accepted | TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES TGT-PRESERVATION-ANCHORS | T1 |
| AC-06 | Clean, structurally malformed, failing, exceptional, and multiple-finding checklist/validator scenarios | Exactly one strict checklist and one summary-validation call occur per accepted observation; malformed assessment yields one call then zero validation; every normalized finding including routing and audit identity survives unchanged and ordered | TGT-COORDINATOR-RUNTIME TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS | T1 |
| AC-07 | Recording/sentinel callbacks, malicious untrusted payload text, one source inability, and mutation/effect sentinels | Observe and assess receive only their exact source-local closed packets; no sibling, connector, route, effect, credential, or path authority is reachable; each required callback is called at most once with no substitute/retry | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF | T1 |
| AC-08 | Raw canary under clean, issue, exception, and cancellation; connector/filesystem mutation spies; disposable tree digest | Zero Atlas mutation and filesystem evidence-write calls; raw/checklist/exception content absent from result/log/cache/artifact surfaces; effect is none, persistent evidence is false, transient closure is closed, and tree digest is unchanged | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS | T1 |
| AC-09 | Source inability, malformed observation/checklist, observe/assess exception, cancellation at each stage, source drift, manifest/binding uncertainty, and combined precedence cases | No case yields clean; seven slots remain safely attributed where frozen; settled siblings survive; no retry/substitution occurs; precedence is blocked before cancelled before issues before clean | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF | T1 |
| AC-10 | Exhaustive old-symbol/path/mode/operation/schema/owner/test/eval/prose inventory and direct removed-operation calls | Every named old surface is absent, schema asset is deleted, old calls return `OP_UNKNOWN`, ordinary use of the hosted op returns `CAPABILITY_UNAVAILABLE`, and no alias, shim, dual mode, or fallback exists | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-RETIRED-SCHEMA TGT-REGRESSION-PROOF | T1 |
| AC-11 | Existing ordinary source ingestion, resummarization, extractor, non-audit quality, routing, transaction, recovery, successor, command-wrapper, and connector scenarios | Fixed ordinary inputs remain byte/shape equivalent; existing focused behavior remains passing; connector, outer schema, command wrapper, and valid three-argument quality callers remain unchanged | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS | T1 |
| AC-12 | Final exact single lineage, focused suites, complete applicable suite once, disposable mixed-seven hosted smoke, independent verification, and final review | Ordered raw-free seven-item aggregate, zero mutation/write calls, unchanged tree digest, passing focused/full evidence, one immutable target accepted by decorrelated dev-verification and final dev-code-review | TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-RETIRED-SCHEMA TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES TGT-PRESERVATION-ANCHORS | T1 |

## Verification / Done criteria

- [ ] VR-01. Prove global and source-local capability boundaries across the real hosted façade.
  - Criterion: AC-01
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Qualified recording host with both versioned native cassettes; absent/unqualified host; absent strict assessment; missing GitHub callback for one GitHub slot; ordinary `execute` and CLI request; disposable connector spies.
  - Evidence form: Operation discovery envelopes, exact callback/connector call counts, seven-slot result for source-local absence, standard failure envelope for global absence, and explicit no-fallback observation.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES
  - Receiver: dev-implementation
- [ ] VR-02. Prove the singular public owner topology and unchanged outer result boundary.
  - Criterion: AC-02
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Harness-surface interface/discovery assertions for exact-seven source quality plus one representative ordinary successor chain; unchanged outer schema validation.
  - Evidence form: One selected audit owner/outer result observation, absent recapture successor/depth-2 terms and calls, passing legal-successor case, and unchanged schema digest.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS
  - Receiver: dev-implementation
- [ ] VR-03. Exercise the complete hosted coordinator seam with seven clean mixed native results.
  - Criterion: AC-03
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: In-process `execute_hosted` call with one qualified host, disposable connector, both exact cassette variants, and instrumented coordinator/quality entrypoints.
  - Evidence form: One hosted/coordinator call, seven sequential ordered cycles, seven clean items, closed raw-free aggregate, exact quality call counts, and `OP_UNKNOWN` for both retired operations.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES
  - Receiver: dev-implementation
- [ ] VR-04. Prove exact-seven cardinality, uniqueness, ordering, identity, and total slot accounting.
  - Criterion: AC-04
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Six, eight, duplicate, malformed, reverse-order seven, `None`, string, batch/list/duplicate wrapper, and cancellation-after-prefix cases in coordinator and hosted façade tests.
  - Evidence form: Zero callbacks for invalid requests; exact request-order identities for valid input; seven slots after trustworthy freeze; actual checklist/validation counts; no late/duplicate collector path.
  - Target recheck: TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF
  - Receiver: dev-implementation
- [ ] VR-05. Prove exact native bytes, URL/origin/adapter/source identity, hashes, projections, freeze binding, and recheck behavior.
  - Criterion: AC-05
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: LF, CRLF, multibyte text, both cassettes, empty/non-text/truncated/wrong-field/wrong-variant/wrong GitHub identity/final-URL cases, persisted-hash mismatch, artifact/manifest/binding drift, and existing valid/invalid multibyte projection fixtures.
  - Evidence form: Exact byte counts and SHA-256 values, exact reconstruction, stable source-local findings/inabilities, correct global drift envelope/aggregate, and zero assessment of mismatched evidence.
  - Target recheck: TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES TGT-PRESERVATION-ANCHORS
  - Receiver: dev-implementation
- [ ] VR-06. Prove strict checklist and one-call semantic validation with lossless findings.
  - Criterion: AC-06
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Clean exact checklist; every structural defect; one failed item; assessment exception; deterministic validator exception; simultaneous routing-reason, audit-identity, and other findings.
  - Evidence form: Exact assess/validate call counts, accepted ID/order snapshot, malformed 1-to-0 boundary, item findings equal validator output values/order, and no returned checklist evidence.
  - Target recheck: TGT-COORDINATOR-RUNTIME TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS
  - Receiver: dev-implementation
- [ ] VR-07. Prove callback source-local isolation and no substitute evidence path.
  - Criterion: AC-07
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Recording callbacks inspect exact keys/object reachability; malicious artifact/payload text; one source inability; connector/effect/write sentinels; sequential mixed-adapter host.
  - Evidence form: Exact observe and assess argument-key snapshots, no sibling identity/reachable authority, one-call counts, no alternate adapter/retry, and zero sentinel calls.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF
  - Receiver: dev-implementation
- [ ] VR-08. Prove read-only behavior, raw-data omission, non-persistence, and logical transient closure.
  - Criterion: AC-08
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Unique raw canary through clean, issue, callback-error, and cancellation runs; connector mutation and filesystem/temp/open-for-write spies; captured logs; disposable pre/post tree digest.
  - Evidence form: Zero mutation/write/temp calls, canary absent from serialized outputs/logs/caches/artifacts, exact effect/persistence constants, closed transient record, and identical tree digest.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS
  - Receiver: dev-implementation
- [ ] VR-09. Prove every degraded path and aggregate precedence while retaining safely attributable siblings.
  - Criterion: AC-09
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: One inability plus six clean; malformed native/checklist; observe/assess/validator exception; cancellation at each stage; known artifact drift; manifest/binding/global uncertainty; issue plus cancellation plus global blocker.
  - Evidence form: Seven items where freeze is trustworthy, exact stage/code/call counts, settled sibling preservation, no retry/substitute, and pairwise precedence results ending in the specified aggregate outcome.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF
  - Receiver: dev-implementation
- [ ] VR-10. Prove exhaustive clean-cutover deletion and hard removal behavior.
  - Criterion: AC-10
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Exhaustive forbidden-surface inventory across operations, symbols, imports, schema assets, modes, owners, contracts, tests, evals, and prose; direct calls to retired and hosted-only operations.
  - Evidence form: Empty forbidden set, absent schema path, no loader/projection/export/caller, `OP_UNKNOWN` for retired operations, `CAPABILITY_UNAVAILABLE` for ordinary hosted invocation, and no alias/fallback branch.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-RETIRED-SCHEMA TGT-REGRESSION-PROOF
  - Receiver: dev-implementation
- [ ] VR-11. Prove named ordinary Atlas behavior and preservation anchors remain unchanged.
  - Criterion: AC-11
  - Proof class: worker smoke plus independent verification
  - Scenario / environment / fixture: Existing focused source/tool/quality/state/index/route/transaction/connector suites and representative fixed ordinary reader/source fixtures; legal successor coverage; direct anchor rehash.
  - Evidence form: Passing ordinary cases, byte/shape equivalence for fixed fixtures, unchanged outer schema/quality/connector/command digests, and no changed non-recapture caller contract.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-REGRESSION-PROOF TGT-PRESERVATION-ANCHORS
  - Receiver: dev-implementation
- [ ] VR-12. Close the final cohesive regression, full-suite, disposable hosted smoke, and independent-assurance boundary.
  - Criterion: AC-12
  - Proof class: worker smoke followed by independent verification and final review
  - Scenario / environment / fixture: Focused source/tool/quality/harness/architecture/instance-contract commands; complete applicable repository suite once; disposable seven-source profile with deterministic genuine-shape native/semantic adapters; immutable target sent to decorrelated verifier then final reviewer.
  - Evidence form: Exact command evidence, one ordered raw-free aggregate, seven independently attributable items, zero connector mutation/filesystem evidence writes, raw canary absence, unchanged disposable tree digest, final target digest, verifier `VERIFIED`, and reviewer `APPROVED`.
  - Target recheck: TGT-CANONICAL-CONTRACTS TGT-OWNER-TOPOLOGY TGT-COORDINATOR-RUNTIME TGT-HOSTED-FACADE TGT-RETIRED-SCHEMA TGT-REGRESSION-PROOF TGT-NATIVE-CASSETTES TGT-PRESERVATION-ANCHORS
  - Receiver: dev-implementation

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-ATLAS-AUDIT-RECAPTURE-CLEAN-CUTOVER | T1 | Exact final single-lineage repository target digest plus changed-path inventory and VR-01 through VR-12 worker-smoke evidence index | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation | One Common Handoff binding AUTH-PLAN, AUTH-SPEC, this ticket-set digest, owned criteria, expected/observed delta, exact target/evidence, effects, convergence state, next unmet criterion, and one receiver; it grants no shipping or Atlas authority. |

A completed worker output returns to dev-implementation for the already-approved `dev-verification → dev-code-review → dev-continual-learning → dev-ask completion presentation` route. It does not skip assurance or authorize a public T13 audit.

## Blockers and recovery

Current blockers: none. The following fail-closed conditions are complete recovery rules, not unresolved implementation choices.

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-AUTHORITY-DRIFT | dev-specification | Rebased approved specification and ticket-set revision, or an exact backend-confirmed nonmaterial baseline rebind | T1 | Any material change to AUTH-PLAN, AUTH-SPEC, architecture baseline, owner boundary, outer schema, fixed behavior, target/effect scope, or acceptance | Exact current authority and ticket projection are revalidated with no changed unresolved decision. |
| BLK-NATIVE-SHAPE-DRIFT | dev-specification | New capability proof, versioned cassette, approved closed interface, and revised specification/tickets | T1 | Unsupported native result shape, ambiguous GitHub mapping, need for nonempty native projection, connector involvement, or altered callback capability | The new exact shape/ownership/failure behavior is approved and all dependent contracts and criteria are rebound. |
| BLK-ROUTE-CHANGE | dev-ask | Exact material change plus revised human-approved Route Overview and downstream authority | T1 | Concurrency, fallback, persistence, changed public behavior, external/destructive effect, multiple lineages, changed assurance, or shipping/deployment request | One approved route names the new topology/effects/owners and a fresh specification/ticket revision is current. |

Implementation failures that do not alter authority remain dev-implementation recovery work under the inherited high-consequence attempt and one post-assurance repair policy. They do not revise this graph, add a lineage, or restore lifecycle budget.

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-SPEC | Governing specification | `local://atlas-audit-recapture-in-process-coordinator-specification.md` at `sha256:39cf2ffced04a6b735705d13032224df459efb60ce1df8dcf1c8809353315aba` | Sole technical interface, behavior, target, deletion, compatibility, degraded-path, and proof authority. |
| ANC-PLAN | Approved plan | `local://atlas-audit-recapture-in-process-coordinator-plan.md` at `sha256:3c393bd33559550e11d64cd6d6849a7001d5ebe39fb985e366838da7afbbbccd` | Outcome, clean-cutover, assurance, route, and prohibited-effect authority. |
| ANC-ARCHITECTURE-FIRST | Canonical contract order | `.agents/ARCHITECTURE.md` baseline `85758a598c7bc79da8fb6bb3c435fdc390c8918e72a56197a8c6c040f488c921` | Must change before dependent contracts or runtime semantics; remains normative over ADR rationale. |
| ANC-SOURCE-SEAM | Runtime symbol boundary | `scripts/atlas_source.py::extract_reader_result`, `scripts/atlas_source.py::project_recapture_schema`, and new `audit_recapture` coordinator surface | Reuse the ordinary extractor, replace old projection, and own closed coordination without a second convention. |
| ANC-FACADE-SEAM | Runtime entry boundary | `scripts/atlas_tool.py::capabilities`, `scripts/atlas_tool.py::execute`, current `_source_audit_cohort`, and new `execute_hosted` | Qualify/expose the hosted operation, fail ordinary invocation, fold freeze, and remove old dispatch. |
| ANC-QUALITY-SEAM | Preserved validator boundary | `scripts/atlas_quality.py::validate_checklist`, `resolve_effective_content_hash`, and `validate_summary` baseline `b09f7ff570fcce4732b6e44b5d00c234b4967125b723d7ac1eeac3ef271742b3` | Reuse strict checklist, projection, summary, and audit-identity authority unchanged. |
| ANC-CONNECTOR-SEAM | Preserved instance boundary | `scripts/atlas_connector.py` baseline `5650a5ac58a36bda1322efc8dbe74a268dc8df438538ab69600038359e2fd5d0` | Read/revision/binding owner only; no external observation or code change. |
| ANC-OWNER-SEAM | Workflow owner boundary | `.agents/skills/atlas-ask/SKILL.md`, `owners/atlas-audit/OWNER.md`, and `owners/atlas-source/OWNER.md` at the Target-map digests | Preserve one selected audit owner and one outer result while deleting only the recapture successor/depth-2 topology. |
| ANC-CASSETTES | Native proof fixtures | `tests/cassettes/native_reader/v1/functions-read.json` and `tests/cassettes/native_reader/v1/github-file-read.json` | Credential-free exact-shape adapter authority for tests and smoke; never live audit evidence. |
| ANC-PLAN-VALIDATOR | Planner structural validator | `skill://dev-implementation/scripts/executor_plan.py` with `context=omp` and `consumer=planner` | Validate these exact ticket-set bytes before publication; the result proves structure only. |

- Assumptions: none

Close note: Terminal-closed 2026-08-13-2144 by approved plan `2026-08-13-1718_atlas-lean-heart-and-memory-t4` at sha256:a735fa42f75e76063772ea07303c8b83c6c238c1794d1ee145a3d8505140bab6. Hosted recapture is not a required Atlas seam. CLOSED is terminal; a later resume needs a new plan identity.
