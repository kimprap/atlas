# Prove the remaining Atlas 1842 cutover criteria

**Datetime**: 2026-08-16-1824
**Authority kind**: direct-repository
**Scope**: Read-only proof of AC-CONTRACTS, AC-RESEARCH, and AC-INTEGRATED on the repaired Atlas cutover target
**Summary**: Prove the three remaining 1842 criteria on the immutable repaired target, freeze one proof target, and obtain fresh independent verification without changing product bytes or reopening either predecessor plan.
**Status**: DONE
**Completed At**: 2026-08-16-2302

## Objective

- Outcome: OUT-ATLAS-1842-CUTOVER-PROOF
- Observable end state: AC-CONTRACTS, AC-RESEARCH, and AC-INTEGRATED are freshly proven with their 1842 recipes on one immutable target derived from `atlas-review-repair-target/v1@sha256:7b153de300a294b808bd93596cf81f4634962f9d382ac03d22771f57255919d3`; a separate verifier returns aggregate `VERIFIED`; the active 1842 plan and archived 1519 plan remain byte-identical.
- Progress signal: One of AC-CONTRACTS, AC-RESEARCH, or AC-INTEGRATED gains its exact recipe evidence on the unchanged target, or a named blocker gains current recovery evidence.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-USER | direct user intent | conversation://2026-08-16/atlas-1842-cutover-proof | sha256:1edb8acb95466235bb27ae320cd5bff6b71cbd559f9095fb1520a8da1cf94fae | Authorizes creation of this proof-only plan. Execution requires native approval of this exact repository path and complete bytes. |
| AUTH-PARENT | terminal historical parent | `.agents/plans/2026-08-15-1842_IMPROVE_deep.md` | sha256:f76cecffcb0d639224a75e82ef6f92b9045c466d4458a0b7cb672754cff4fecf | Supplies only AC-CONTRACTS, AC-RESEARCH, AC-INTEGRATED and VR-CONTRACTS, VR-RESEARCH, VR-INTEGRATED. It must not be revised, resumed, completed, archived, or treated as executable authority. |
| AUTH-REPAIR | completed successor repair | `.agents/plans/archive/2026-08-16-1519_atlas-review-004-005-repair.md` | sha256:ba69fc86b60d833df368dbfcd8a38cef14304782536a7ee900de6f049fcd73bb | Supplies the repaired target and closed repair findings only. Its tasks, criteria, review, curation, and lifecycle remain immutable historical evidence. |
| AUTH-TARGET | immutable repaired repository target | `atlas-review-repair-target/v1` | sha256:7b153de300a294b808bd93596cf81f4634962f9d382ac03d22771f57255919d3 | Current proof baseline. Reconstruct the exact canonical manifest before and after every proof stage; no task may change a member. |
| AUTH-ARCH | canonical architecture | `.agents/ARCHITECTURE.md` | sha256:39c6a56efe2f8a238cbb8ba439f6dd2ecf48318b547425dbd1b831b16a5f344f | Current owner, operation-audience, write-set, and research-eligibility authority; read-only in this outcome. |
| AUTH-REGISTRY | registry and runtime contract | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` | sha256:3b886371e8036ff1b3c31c2c63799bf0b0f247c98fa6a62ae334534d16dd3cb0 | Current reducer, inspection, publication, and recovery authority; read-only in this outcome. |

- AUTH-USER revision is SHA-256 over this exact UTF-8 statement plus one LF: `Create and natively approve a new direct-repository Executor Plan whose only Build proves AC-CONTRACTS/VR-CONTRACTS, AC-RESEARCH/VR-RESEARCH, and AC-INTEGRATED/T7/VR-INTEGRATED on atlas-review-repair-target/v1@sha256:7b153de300a294b808bd93596cf81f4634962f9d382ac03d22771f57255919d3; do not revise, resume, complete, or unarchive the 2026-08-15-1842 and 2026-08-16-1519 plan identities.`
- AUTH-TARGET is canonical JSON `{"base_target":"sha256:6c8eb80425a35e71935c175445b16c90faaf66981530f8151e4781d7cdce83d9","files":{"scripts/atlas_research.py":"73ab85ec4491ab76cbf0f19a2102dd619670e0620e0fdc5aa1b5f63d172be5c6","scripts/atlas_state.py":"90d6b972d9704cef03c9bd1daacd56b9c6b85855165f7c3353d23d782a89389f","scripts/atlas_tool.py":"778a82749de882e6ac0a1f57b56551c9b36f60d8dc114b57660703721263a98d","tests/test_atlas_research.py":"75eccfb051f35985ee7c10bc349c987ff91602b693d4fc72ecc81d751a399be9","tests/test_atlas_state.py":"1bf7f6c9ed1019831f0b023bd7b11d8635c467d3241422ba8e7ed67cb98bcf53","tests/test_atlas_tool.py":"da40fbb80da7f6a25e2e0120fb06a6830060eac3744e06cfcbf66b4218f6d1a8"},"schema":"atlas-review-repair-target/v1"}` plus one LF, SHA-256 hashed. File keys are sorted by canonical JSON serialization.

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-PROOF-ONLY | AUTH-USER@sha256:1edb8acb95466235bb27ae320cd5bff6b71cbd559f9095fb1520a8da1cf94fae | Run proof and produce evidence only. No product, contract, test, runtime, owner, command, scaffold, profile, vault, or predecessor-plan byte may change. A failed criterion is a stop, not repair authority. |
| DEC-PREDECESSOR-FROZEN | AUTH-PARENT@sha256:f76cecffcb0d639224a75e82ef6f92b9045c466d4458a0b7cb672754cff4fecf; AUTH-REPAIR@sha256:ba69fc86b60d833df368dbfcd8a38cef14304782536a7ee900de6f049fcd73bb | Leave both predecessor identities byte-identical. Do not restore the 1842 repair token or review rerun and do not reopen any 1519 task, criterion, review, or curation state. |
| DEC-USE-1842-IDS | AUTH-PARENT:AC-CONTRACTS,AC-RESEARCH,AC-INTEGRATED,VR-CONTRACTS,VR-RESEARCH,VR-INTEGRATED | Prove the three original IDs with their original recipes. The seven 1519 criteria are baseline assurance and do not substitute for these IDs. |
| DEC-TARGET-BINDING | AUTH-TARGET@sha256:7b153de300a294b808bd93596cf81f4634962f9d382ac03d22771f57255919d3 | Reconstruct the six-file manifest before T1, between tasks, before verifier dispatch, and after verification. Any mismatch invalidates all proof evidence. |
| DEC-ASSURANCE-INHERITANCE | AUTH-REPAIR:396-402 | AUTH-TARGET already received independent `VERIFIED`, final `APPROVED`, and `NO DURABLE LEARNING` for the repaired product criteria. This proof-only outcome adds one fresh independent verification pass for its three IDs; it authorizes no new review, review rerun, repair, or curation pass. |
| DEC-INSTANCE-DEFER | AUTH-ARCH:214-220; AUTH-PARENT#DEC-DEFER-INSTANCE-DURABILITY | Use only OS-temporary instances and profiles. Bound-instance sync, non-development profile effects, and instance-sync durability remain deferred. |

## Scope, non-goals, and prohibited effects

- Read surfaces: AUTH-PARENT remaining criteria and recipes; AUTH-REPAIR target and terminal evidence; AUTH-ARCH; AUTH-REGISTRY; ADR 0007 and its index row; the workflow-result and source-capture schemas; source-capture mapping; agent CLI recipes; lean tooling eval matrix; the generated façade and instance CLI; scaffold manifest; and Atlas tests required by the three recipes.
- Change surfaces: This plan's lifecycle metadata; session-local worker target/evidence and verification Handoffs; OS-temporary instances, profiles, journals, and receipts created by the declared proof recipes.
- Non-goals: Product repair or refactoring; another 1842 or 1519 lifecycle transition; another review or curation pass; framework synchronization; instance durability work; changing an operation, owner, schema, contract, test, fixture, command, or target member; delivery or shipping.
- Prohibited effects: No reset, checkout, stash, overwrite, auto-merge, code or contract edit, bound `vault://atlas/` I/O, real profile mutation, `sync-framework`, credential use, commit, stage, push, deploy, release, force Git operation, stale-plan-gate edit, execution of `2026-07-29-2056_atlas-evaluation-loop` or `2026-08-02-1332_atlas-topic-creation`, or mutation of AUTH-PARENT or AUTH-REPAIR.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-PLAN | direct-repository plan lifecycle | AUTH-USER plus native approval of this exact plan | Only this plan may move PENDING to IN_PROGRESS and later DONE or a recorded terminal stop. Never touch another plan identity. |
| EFF-EVIDENCE | session-local evidence write | AUTH-USER plus native approval of this exact plan | Only the worker evidence index, canonical proof-target manifest, verifier Handoff, and required Common Handoffs. No repository projection or product artifact. |
| EFF-TEMP | temporary-filesystem proof fixture | AUTH-USER plus native approval of this exact plan | OS-temporary instances, profiles, journals, requests, and receipts only; remove every root before T3 hands off. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-CUTOVER | Architecture, ADR 0007, owner result, source capture, recipes, lifecycle audience, and lean eval agreement | T1 | TGT-CONTRACTS@sha256:3695effbe1b04b5086e9b0ce9a4fd2e29a9754fd0f6a62c4b389c16faa7cdcc5 | T1, T3 |
| CONTRACT-RESEARCH | Purpose-specific inspection, body-excluded identity, current zero-pending eligibility, four-target publication, post-validation, rollback, exact recovery, and sole successor | T2 | AUTH-ARCH@sha256:39c6a56efe2f8a238cbb8ba439f6dd2ecf48318b547425dbd1b831b16a5f344f; AUTH-REGISTRY@sha256:3b886371e8036ff1b3c31c2c63799bf0b0f247c98fa6a62ae334534d16dd3cb0 | T2, T3 |
| CONTRACT-TARGET | Exact repaired six-file manifest, read-only proof execution, canonical evidence index, immutable proof-target identity, and pre/post identity equality | T3 | AUTH-TARGET@sha256:7b153de300a294b808bd93596cf81f4634962f9d382ac03d22771f57255919d3 | T1, T2, T3 |

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-CONTRACTS | `.agents/ARCHITECTURE.md`; `docs/adr/INDEX.md`; `docs/adr/0007-agent-cli-and-owner-consolidation.md`; `markdown-registry-contracts.md`; `operating-cadence-and-guardrails.md`; `source-summary-quality-guide.md`; `research-library-templates.md`; `atlas-workflow-result.schema.json`; `source-capture.schema.json`; `evals/agent-tooling.json`; `agent-cli-recipes.md`; `source-capture-mapping.md` | T1 | Ordered `sha256sum`-line bundle sha256:3695effbe1b04b5086e9b0ce9a4fd2e29a9754fd0f6a62c4b389c16faa7cdcc5 | `tests.test_atlas_harness_surface`; `AtlasToolingQualityTests.test_agent_tooling_fixture_is_lean_and_behavioral`; generated operation catalog | AC-CONTRACTS |
| TGT-RESEARCH | `scripts/atlas_state.py`; `scripts/atlas_research.py`; `tests/test_atlas_state.py`; `tests/test_atlas_research.py` | T2 | Ordered `sha256sum`-line bundle sha256:ee80a8214d9ed6073665d7187e828c596308ec609be91f3ce9a381329da8c6eb | Every freshness and purpose fixture; body-excluded hash; deterministic projection; four-target execute; rollback, exact recovery, and sole successor | AC-RESEARCH |
| TGT-INTEGRATED | AUTH-TARGET six-file manifest; TGT-CONTRACTS; TGT-RESEARCH; `scripts/atlas-instance.py`; `scaffold/MANIFEST.json`; actual façade and instance subprocess surfaces | T3 | AUTH-TARGET@sha256:7b153de300a294b808bd93596cf81f4634962f9d382ac03d22771f57255919d3 plus exact TGT-CONTRACTS and TGT-RESEARCH bundle identities | Ruff, complete Atlas suite, unbound capabilities, all-audience capabilities, URL normalization, framework inspection, temporary create/profile/bound hash/check, independent verifier | AC-INTEGRATED |

- TGT-CONTRACTS uses the listed path order exactly. Its member SHA-256 values are `39c6a56efe2f8a238cbb8ba439f6dd2ecf48318b547425dbd1b831b16a5f344f`, `54c567457f30a2b72a9d33f9db5979faa04363cf3f26a3a0f37f2ed043651586`, `da9ac35bc4d1acc65182ff13e75b4713b22a09e33c8abb034f8b5b1aec982c8a`, `3b886371e8036ff1b3c31c2c63799bf0b0f247c98fa6a62ae334534d16dd3cb0`, `4b079361750af4019ceda1ef3d94e4a4049fe05990c50ebc39eaaba6c8c1f744`, `128fbda00ecad332a4724b8157dd9f4b30a93c1610b8784808b876744ae0f3ec`, `5445a40bdd1b84501a313c1d48dfb6d5e6321f9ace24632dd05e613431ca7e14`, `c0aea38041b146de5adad5e16096c1ea7295d09727d8e2c444ecc1685e766214`, `1833b4b69859c209ea8f696293df71426d191ea9eb045d55ea7234e6d660bab0`, `9c87cdaa9625f02503bee21bc1556e6e0696ffe47b60b3a541f13e58e955ab26`, `f913f0dec3baf8b75c33e132629db210e61e6ae27bcadf5e745d3b2966dd8e6c`, and `ffcfc98a232864ef3bd7d3ae44d2f61a9f17e19cc52bde0c4bc74dc344e23e35` in the same order.
- TGT-RESEARCH uses the listed path order exactly. Its member SHA-256 values are `90d6b972d9704cef03c9bd1daacd56b9c6b85855165f7c3353d23d782a89389f`, `73ab85ec4491ab76cbf0f19a2102dd619670e0620e0fdc5aa1b5f63d172be5c6`, `1bf7f6c9ed1019831f0b023bd7b11d8635c467d3241422ba8e7ed67cb98bcf53`, and `75eccfb051f35985ee7c10bc349c987ff91602b693d4fc72ecc81d751a399be9` in the same order.

## Execution policy

- Assurance: Inherited high-consequence product assurance on AUTH-TARGET plus one fresh independent verification boundary for AC-CONTRACTS, AC-RESEARCH, and AC-INTEGRATED; no new review, repair, rerun, or curation is authorized.
- Topology: one-owner sequential single lineage.
- Max concurrency: 1
- Isolation: Shared current dirty worktree at Git HEAD `d8290d085f32483a9e7dc7cf9710803875e5383a`; preserve every pre-existing change and create no isolated worktree.
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: Stop on any AUTH-TARGET, TGT-CONTRACTS, TGT-RESEARCH, predecessor-plan, architecture, registry, or active-editor drift; semantically compare before any rebind and never reset, overwrite, or auto-merge.
- Decomposition: One `dev-implementation` proof owner executes T1 through T3 in order without product edits or delegation, then hands one immutable proof target to a separate `dev-verification` owner that independently reruns all three recipes.
- Effect limit: EFF-PLAN, EFF-EVIDENCE, EFF-TEMP
- Orchestrator profile: One-qualified-owner sequential projection; full orchestration and implementation subagents are unnecessary. The verifier is a separate read-only identity and receives only the exact target, authority, criteria, recipes, rule manifest, and bounded fixtures.

## Tasks

- [x] T1. Prove canonical cutover contract alignment
  completed 2026-08-16-2302
  - Owner: dev-implementation
  - Wave: W0
  - Depends on: none
  - Targets: TGT-CONTRACTS
  - Contracts: CONTRACT-CUTOVER, CONTRACT-TARGET
  - Criteria: AC-CONTRACTS
  - Effects: EFF-PLAN, EFF-EVIDENCE
  - Output: OUTP-T1
  - Receiver: T2
  - Verification: VR-CONTRACTS
  - Lineage: shared
  - Reconstruct AUTH-TARGET and both ordered proof bundles before executing the recipe. Require AUTH-PARENT, AUTH-REPAIR, AUTH-ARCH, and AUTH-REGISTRY to match their exact revisions; otherwise stop under BLK-TARGET-DRIFT.
  - Parse `atlas-workflow-result.schema.json`, `source-capture.schema.json`, and `evals/agent-tooling.json` with Python's standard JSON parser. Run `python3 -m unittest tests.test_atlas_harness_surface tests.test_atlas_quality.AtlasToolingQualityTests.test_agent_tooling_fixture_is_lean_and_behavioral` from `/Users/kim/dev/atlas/app` with `ATLAS_VAULT_PROFILE` absent and bytecode writes disabled.
  - In one read-only standard-library assertion, require the owner effect enum to be exactly `none|committed|partial|unknown`; the completed branch to allow only `none|committed`; the blocked `partial|unknown` branch to require an exact recovery object; eval cases `partial-blocks-exact-recovery` and `unknown-completed-rejected`; the recipe lifecycle index to equal the generated lifecycle catalog with no duplicate; the capture schema's exact eight required keys; all three mapping rows `GitHub file_read`, `OMP native reader`, and `Generic HTTP or browser`; and architecture/registry agreement on current zero-pending `research-complete` with only pass, topic index, subdomain index, and `TOPICS.md`.
  - Record command, exit, test count, key assertions, exact member hashes, and the unchanged bundle and AUTH-TARGET identities in OUTP-T1. Do not edit a failed contract; return the exact contradictory AC-CONTRACTS evidence.

- [x] T2. Prove research inspection publication and recovery
  completed 2026-08-16-2302
  - Owner: dev-implementation
  - Wave: W1
  - Depends on: T1
  - Targets: TGT-RESEARCH
  - Contracts: CONTRACT-RESEARCH, CONTRACT-TARGET
  - Criteria: AC-RESEARCH
  - Effects: EFF-PLAN, EFF-EVIDENCE, EFF-TEMP
  - Output: OUTP-T2
  - Receiver: T3
  - Verification: VR-RESEARCH
  - Lineage: shared
  - Reconstruct AUTH-TARGET, TGT-CONTRACTS, and TGT-RESEARCH after OUTP-T1; do not consume T1 evidence if any identity changed.
  - Run the original 1842 recipe exactly from `/Users/kim/dev/atlas/app` with no bound profile and bytecode writes disabled: `python3 -m unittest tests.test_atlas_state tests.test_atlas_research`.
  - Require direct fixture evidence for all published topic states and all three purpose payloads; body-only and whitespace-only changes under unchanged revisions preserve `inspection_sha256`; included revision or pending-set changes alter it; ineligible and forged projections write nothing; valid execution writes exactly pass, topic `INDEX.md`, subdomain `INDEX.md`, and reducer-derived `TOPICS.md` in order; no pending edge or fifth target changes; injected partial application rolls back or exposes the sole eligible successor; exact recovery accepts only the byte-identical request and terminalizes once.
  - Record command, exit, test count, scenario-to-observation map, temporary cleanup, exact member hashes, and unchanged proof identities in OUTP-T2. Any contradiction stops; no repair or retry is authorized.

- [x] T3. Prove the integrated cutover and freeze one target
  completed 2026-08-16-2302
  - Owner: dev-implementation
  - Wave: W2
  - Depends on: T2
  - Targets: TGT-INTEGRATED
  - Contracts: CONTRACT-CUTOVER, CONTRACT-RESEARCH, CONTRACT-TARGET
  - Criteria: AC-INTEGRATED
  - Effects: EFF-PLAN, EFF-EVIDENCE, EFF-TEMP
  - Output: OUTP-T3
  - Receiver: dev-verification
  - Verification: VR-INTEGRATED
  - Lineage: shared
  - Reconstruct every authority and target identity before proof. Run `ruff check scripts tests`, then `python3 -m unittest discover -s tests -p 'test_atlas_*.py'` from `/Users/kim/dev/atlas/app` with `ATLAS_VAULT_PROFILE` absent and bytecode writes disabled. Require Ruff exit 0 and the current complete suite to report 311 tests and `OK`.
  - Run the actual CLI recipes as subprocesses, not replacements by unit-test invocation: `python3 scripts/atlas_tool.py capabilities`; `python3 scripts/atlas_tool.py capabilities --all`; pipe `{"url":"https://example.test/a"}` to `python3 scripts/atlas_tool.py url normalize --input -`; and `python3 scripts/atlas-instance.py inspect-framework`. Require canonical version-2 JSON, empty stderr, exit 0, default discovery containing exactly 28 lifecycle operations, all discovery containing those 28 plus exactly 13 internal operations, normalized URL `https://example.test/a` with source ID `37f58c3315be`, and framework counts `product_owned:1`, `seed_once:7`, `total:8`.
  - Run one standard-library `tempfile.TemporaryDirectory` driver that invokes the actual CLIs. Name the returned directory `TMP_ROOT` and define `TMP_PROFILE` as `TMP_ROOT/vault/config/profiles/local.yml`. Create `TMP_ROOT/vault/instances/atlas` with `python3 scripts/atlas-instance.py --instances-root TMP_ROOT/vault/instances create --name atlas`; write only `TMP_PROFILE` with profile `local`, instance `atlas`, connector `local-fs`, and relative root `instances/atlas`; pipe `{"path":"vault://atlas/ARCHITECTURE.md"}` to `python3 scripts/atlas_tool.py --profile TMP_PROFILE vault hash --input -`; then run `python3 scripts/atlas-instance.py --instances-root TMP_ROOT/vault/instances check --name atlas`. Require create `completed`, bound hash `ok:true` with revision `sha256:39c6a56efe2f8a238cbb8ba439f6dd2ecf48318b547425dbd1b831b16a5f344f`, check `no-write`, canonical envelopes, empty stderr, exit 0, no host-root leakage, and absence of `TMP_ROOT` after context exit.
  - Write a session-local worker evidence index with exact fields `schema`, `outcome`, `base_target`, `authorities`, `proof_inputs`, `criteria`, `commands`, `effects`, and `temporary_cleanup`. Use schema literal `atlas-1842-cutover-worker-evidence/v1`; preserve command order; record exact inputs, exits, meaningful expected and observed values, test counts, and artifact hashes; require `effects.repository_product_changes` and every bound/profile/vault/sync/delivery list to be empty.
  - Write a session-local canonical proof-target manifest with exact fields `schema`, `outcome`, `base_target`, `authorities`, `proof_inputs`, and `worker_evidence_sha256`. Use schema literal `atlas-1842-cutover-proof-target/v1`; bind AUTH-PARENT, AUTH-REPAIR, AUTH-ARCH, and AUTH-REGISTRY revisions; bind TGT-CONTRACTS and TGT-RESEARCH bundle identities; bind the finalized worker evidence index SHA-256. Serialize each JSON object with sorted keys, compact separators, UTF-8, and one LF, then identify the target by SHA-256 of those exact bytes.
  - Reconstruct AUTH-TARGET and every proof input after cleanup. Hand only the immutable proof-target identity, its complete manifest and evidence index, exact current plan revision, the three criteria and recipes, consumed predecessor repair/review state, complete applicable-rule manifest, and prohibited-effect accounting to `dev-verification`. The verifier independently reruns VR-CONTRACTS, VR-RESEARCH, and VR-INTEGRATED; only aggregate `VERIFIED` permits T3, all three VRs, and this plan to complete.

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-CONTRACTS | Canonical contract cutover on the current repaired target | Architecture, ADR index/0007, core contracts, compact resumable result schema, source-capture schema/mapping, recipe asset, and lean eval matrix agree on owner-plus-mode routing, audience-filtered v2 CLI, exact owner effects `none`, `committed`, `partial`, and `unknown`, blocking `partial` or `unknown`, research eligibility, no hosted transport, and no Task-required or automatic engineering cycle. | TGT-CONTRACTS | T1 |
| AC-RESEARCH | Current, dirty, refreshing, blocked, absent, stale, interrupted, forged, and conflicting topic scenarios | Purpose payloads are exact; inspection hash binds identities, revisions, and pending IDs but not returned bodies; only current zero-pending topics publish; exactly four ordered targets commit; publication cannot alter pending edges or add a fifth target; exact rollback, recovery, and sole-successor behavior survives every boundary. | TGT-RESEARCH | T2 |
| AC-INTEGRATED | Complete unchanged AUTH-TARGET after T1 and T2 | Ruff and the full Atlas suite pass; actual CLI smoke proves pure URL normalization, lifecycle/all-audience discovery, framework inspection, temporary create/bind/check, and cleanup; one new immutable proof target is independently verified without product, predecessor-plan, bound-instance, profile, sync, credential, delivery, commit, or push effect. | TGT-INTEGRATED | T3 |

## Verification / Done criteria

- [x] VR-CONTRACTS. Validate canonical contract recipe schema and eval alignment
  completed 2026-08-16-2302
  - Criterion: AC-CONTRACTS
  - Proof class: worker smoke followed by fresh independent verification
  - Scenario / environment / fixture: From `/Users/kim/dev/atlas/app` with no bound profile, parse the three named JSON assets, run the exact T1 unittest command, and execute the T1 standard-library assertions against the immutable proof target.
  - Evidence form: Parser and tests exit 0; exact enums, invalid completed-effect tuple, recovery branch, lifecycle recipe/catalog parity, three capture mappings, research-complete preconditions/write set, bundle SHA-256, and pre/post AUTH-TARGET equality are recorded independently.
  - Target recheck: TGT-CONTRACTS
  - Receiver: dev-verification

- [x] VR-RESEARCH. Exercise purpose inspection four-target publication and exact recovery
  completed 2026-08-16-2302
  - Criterion: AC-RESEARCH
  - Proof class: worker smoke followed by fresh independent verification
  - Scenario / environment / fixture: From `/Users/kim/dev/atlas/app` with no bound profile, run `python3 -m unittest tests.test_atlas_state tests.test_atlas_research` across every freshness state, all three purpose payloads, hash-preimage fixtures, zero/nonzero pending edges, forged/stale projections, and failures before and after each ordered target.
  - Evidence form: Exit 0; body-only and whitespace-only changes under unchanged revisions preserve the hash; included revision or pending-set changes alter it; ineligible and forged paths write nothing; valid plan hashes and four-target order match; no fifth target or pending-edge mutation occurs; rollback, exact recovery, and sole successor terminalize once; bundle and AUTH-TARGET identities remain unchanged.
  - Target recheck: TGT-RESEARCH
  - Receiver: dev-verification

- [x] VR-INTEGRATED. Run Ruff full suite actual CLI smoke and immutable-target proof
  completed 2026-08-16-2302
  - Criterion: AC-INTEGRATED
  - Proof class: worker smoke followed by fresh independent verification
  - Scenario / environment / fixture: From `/Users/kim/dev/atlas/app` with no bound profile, run the exact T3 Ruff and 311-test suite commands; actual default/all capabilities, URL normalize, and inspect-framework commands; and the actual temporary create/profile/bound-hash/check driver with automatic cleanup.
  - Evidence form: Every command exits 0 with canonical contracted JSON and empty stderr; discovery is exactly 28 lifecycle plus 13 internal operations; URL and framework outputs match; temporary binding hashes AUTH-ARCH; the temporary root is absent; predecessor and product bytes remain unchanged; one canonical proof target and worker evidence index are rehashed before and after a separate verifier returns aggregate `VERIFIED` for all three criteria.
  - Target recheck: TGT-INTEGRATED
  - Receiver: dev-verification

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-T1 | T1 | Exact TGT-CONTRACTS bundle plus VR-CONTRACTS worker evidence | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | T2 | Common Handoff from dev-handoff binding exact authorities, bundle, assertions, commands, effects, blocker state, and receiver. |
| OUTP-T2 | T2 | Exact TGT-RESEARCH bundle plus VR-RESEARCH worker evidence | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | T3 | Common Handoff from dev-handoff binding exact authorities, target, scenario map, commands, temporary cleanup, effects, blocker state, and receiver. |
| OUTP-T3 | T3 | Canonical `atlas-1842-cutover-proof-target/v1` identity, complete manifest, worker evidence index, and all three proof recipes | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-verification | Common Handoff from dev-handoff binding exact plan and authority revisions, immutable target, criteria, recipes, command evidence, effect accounting, inherited consumed repair/review state, complete applicable-rule manifest, and one receiver; make no verification claim. |

- A `VERIFIED` dev-verification Common Handoff returns to `dev-implementation` for terminal accounting. `NOT VERIFIED` or `INCONCLUSIVE` stops this outcome with deduplicated AC IDs and exact evidence; neither authorizes code changes, another verifier, review, repair, or lifecycle reset.
- Set `Status: DONE` only after T1 through T3 and VR-CONTRACTS, VR-RESEARCH, and VR-INTEGRATED are checked, the separate verifier's aggregate verdict is `VERIFIED` on the unchanged proof target, every temporary root is absent, predecessor bytes are unchanged, and a nonempty Completion Summary records findings, decisions, delivered proof, and residual risks.

## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-TARGET-DRIFT | dev-implementation | Fresh AUTH-TARGET canonical reconstruction, both proof-bundle hashes, authority hashes, and semantic comparison | all | Any product member, contract, criterion, recipe, effect, target, predecessor, or plan byte drift after native approval stops. Material drift requires a revised plan and fresh native approval; never reset or absorb it. | All exact revisions reconstruct and the shared worktree is safe for read-only proof. |
| BLK-PROOF-FAILURE | dev-implementation | Exact failing command, scenario, expected and observed result, affected AC IDs, target pre/post identities, and temporary/effect accounting | all | This plan authorizes proof only. No failed worker or verifier result may enter repair, retry, review, diagnosis, or another proof pass under this identity. | Every recipe passes and a separate verifier returns aggregate `VERIFIED`, or new human authority creates a distinct outcome. |
| BLK-PREDECESSOR-LIFECYCLE | human plan owner | AUTH-PARENT and AUTH-REPAIR complete-byte hashes plus current active/archive classification | all | The 1842 repair token and review rerun remain consumed; 1519 remains archived DONE. This plan cannot checkbox, complete, resume, unarchive, revise, or replace either identity. | Both predecessor plans remain byte-identical at their bound hashes. |
| BLK-PROFILE-EFFECT | dev-implementation | Environment inventory, exact temporary profile path, command arguments, subprocess envelopes, and post-cleanup absence | T2, T3 | Any bound or non-development profile, `vault://atlas/` effect, or framework sync requires separate user authority and is prohibited here. | `ATLAS_VAULT_PROFILE` is absent, every explicit profile is under one OS-temporary root, and cleanup is proven. |
| BLK-STALE-PLANS | dev-implementation | Current temporary stale-plan gate and exact blocked identities | all | This outcome may not execute, revise, approve, or remove the gate for `2026-07-29-2056_atlas-evaluation-loop` or `2026-08-02-1332_atlas-topic-creation`. | Proof remains independent of both blocked identities. |

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-PARENT | terminal historical authority | `.agents/plans/2026-08-15-1842_IMPROVE_deep.md:246-262,264-285,293-299,328-360` | Source T7, the three remaining acceptance IDs, their original recipes, and consumed convergence only; never mutate or resume. |
| ANC-REPAIR | completed repair authority | `.agents/plans/archive/2026-08-16-1519_atlas-review-004-005-repair.md:350-362,396-402` | Bind AUTH-TARGET, closed findings, final verification/review/curation, and consumed repair/review history without reusing its criterion IDs. |
| ANC-CANONICAL | canonical product contracts | `.agents/ARCHITECTURE.md:47-115,159-175,188-220`; `.agents/skills/atlas-core/assets/markdown-registry-contracts.md:29-60,106-114,219-253` | Judge operation audiences, owner effects, purpose inspection, four-target publication, recovery, instance boundary, and no-write proof scope. |
| ANC-PROOF-ASSETS | recipe and schema bundle | `.agents/skills/atlas-core/assets/agent-cli-recipes.md`; `atlas-workflow-result.schema.json`; `source-capture.schema.json`; `source-capture-mapping.md`; `evals/agent-tooling.json`; `docs/adr/0007-agent-cli-and-owner-consolidation.md` | Execute VR-CONTRACTS without inventing operation literals, mappings, result tuples, or eval expectations. |
| ANC-VALIDATOR | sole Executor Plan validator | `/Users/kim/.agents/skills/dev-implementation/scripts/executor_plan.py` | Validate exact plan bytes with `--context omp --consumer planner` before native approval and use its backend preflight as the only ready transition. |

- ASM-TARGET: AUTH-TARGET and both proof bundles were reconstructed from current bytes during planning. Fallback: any mismatch at execution stops under BLK-TARGET-DRIFT; do not rebase evidence or modify the target.
- ASM-PROOF-ONLY: Current architecture and registry contracts are implementable and 1519 closed the product defects. Fallback: an observed need for any product edit returns `authority-change-required`; do not spend or recreate predecessor repair/review capacity.
- ASM-ENVIRONMENT: Repository Python requires 3.11 or newer, runtime dependencies are standard-library-only, and Ruff is already available in the established proof environment. Fallback: missing Python or Ruff is `transport-unavailable`; do not install dependencies or weaken the recipe.
- ASM-PROFILE: Proof commands require no ambient bound profile. Fallback: explicitly remove `ATLAS_VAULT_PROFILE` from each subprocess environment and use only the T3 OS-temporary profile; never inspect or mutate the ambient binding.
- ASM-ASSURANCE: AUTH-REPAIR's exact product target already has independent verification, approved review, and terminal curation; this outcome requires fresh verification only for its three projected 1842 IDs. Fallback: if backend policy requires a new review or curation for this proof-only target, stop `authority-change-required`; do not run or restore a predecessor review rerun and do not silently widen the plan.

## Completion Summary

- Findings: This identity was never executed. The exact proof recipes and repaired target were completed by `2026-08-16-2102_atlas-1842-local-proof` at `sha256:b8e2b0367b15c7389567bddd433873b383501222667caecb42d43276572b3c2b`, with aggregate `VERIFIED` for `AC-CONTRACTS`, `AC-RESEARCH`, and `AC-INTEGRATED`.
- Decisions: User 2026-08-16 cleanup approval closed this inert direct plan as superseded. Do not execute, revise, or revive it.
- Delivered behavior: none on this identity; successor 2102 delivered the proof.
- Residual risks: none within this unused identity.
