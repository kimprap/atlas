# Executor direct-repository slug preflight repair

**Datetime**: 2026-08-15-2319
**Authority kind**: local-authority
**Scope**: Shared Executor Plan backend slug classification and the blocked Atlas preflight
**Summary**: Accept safe repository-native direct-plan slugs without weakening local-authority slug rules, then prove the unchanged Atlas plan is eligible.
**Status**: DONE
**Completed At**: 2026-08-16-0014

## Objective

- Outcome: OUT-EXECUTOR-DIRECT-SLUG
- Observable end state: Direct-repository plan identity `2026-08-15-1842_IMPROVE_deep` passes backend preflight while local-authority and unsafe slug inputs still fail closed.
- Progress signal: One of AC-DIRECT through AC-PRESERVE is proven, or BLK-WORKTREE or BLK-ATLAS-DRIFT is resolved.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-USER | human | conversation://2026-08-15/executor-direct-slug-repair | decision:repair-harness-preflight@2026-08-15 | approved |

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-DIRECT-SLUG | decision:repair-harness-preflight@2026-08-15 | Preserve the approved direct-repository plan path and permit its safe repository-native slug. |
| DEC-LOCAL-SLUG | sha256:af0d6173498a78537999acf539f27f9312e84d919a16653990a0f3a2c8072f5c | Keep OMP-created local-authority slugs lowercase kebab-case. |
| DEC-PREFLIGHT | sha256:58d6fabcf02fcaf890849dc3b6451719463275731c26e9ca5b5175ab48c006cb | Keep one fail-closed planner/backend validator and no alternate ready transition. |

## Scope, non-goals, and prohibited effects

- Read surfaces: Current plan contracts, executor implementation and tests, the approved Atlas plan, and its six bound target bundles.
- Change surfaces: `/Users/kim/.dotfiles/.config/agents/skills/dev-implementation/scripts/executor_plan.py` and `/Users/kim/.dotfiles/.config/agents/skills/dev-implementation/scripts/test_executor_plan.py` only.
- Non-goals: Plan identity migration, Atlas implementation, transport aliases, bound-instance access, and changes to existing unrelated user work.
- Prohibited effects: No repository-plan rewrite, vault or profile mutation, framework synchronization, staging, commit, push, deployment, credential use, or external mutation.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-USER-CONFIG | user-config-write | AUTH-USER | Two named script files only; preserve pre-existing changes and remain reversible before delivery. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-SLUG | Authority-specific backend slug grammar | T1 | DEC-DIRECT-SLUG@decision:repair-harness-preflight | T1, T2 |
| CONTRACT-PREFLIGHT | executor-plan-preflight/v1 result and fail-closed readiness | T1 | DEC-PREFLIGHT@sha256:58d6fabcf02fcaf890849dc3b6451719463275731c26e9ca5b5175ab48c006cb | T1, T2 |
| CONTRACT-ATLAS | Approved Atlas plan path, SHA, and six bundle identities | T2 | sha256:2d9a838d7f357052f55b3ad714da80718a3f0167f7923cce5c8e6eeabb2e39b7 | T2 |

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-EXECUTOR | /Users/kim/.dotfiles/.config/agents/skills/dev-implementation/scripts/executor_plan.py | T1 | sha256:05464fec55215e75f407bf2f70032e6897587766aa805e0b3cdf1ff59c72eb2c | backend CLI and preflight_file callers | AC-DIRECT, AC-LOCAL, AC-UNSAFE |
| TGT-TESTS | /Users/kim/.dotfiles/.config/agents/skills/dev-implementation/scripts/test_executor_plan.py | T1 | sha256:02c59da826b39d6d304e6caeb99b3816b42720370992883450c7135d06e28c63 | ExecutorPlanPreflightTests | AC-DIRECT, AC-LOCAL, AC-UNSAFE |
| TGT-ATLAS-PREFLIGHT | .agents/plans/2026-08-15-1842_IMPROVE_deep.md backend readiness | T2 | sha256:2d9a838d7f357052f55b3ad714da80718a3f0167f7923cce5c8e6eeabb2e39b7 | exact OMP backend preflight and six target-bundle hashes | AC-ATLAS, AC-PRESERVE |

## Execution policy

- Assurance: high-consequence
- Topology: one-owner
- Max concurrency: 1
- Isolation: shared lineage preserving the existing dirty worktree
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: T1 completes and passes targeted tests before T2 invokes the real Atlas preflight.
- Decomposition: no child delegation
- Effect limit: EFF-USER-CONFIG only
- Orchestrator profile: not required for one-owner execution

## Tasks

- [x] T1. Repair authority-specific slug validation
  completed 2026-08-15-2328
  - Owner: implementation-owner
  - Wave: W0
  - Depends on: none
  - Targets: TGT-EXECUTOR, TGT-TESTS
  - Contracts: CONTRACT-SLUG, CONTRACT-PREFLIGHT
  - Criteria: AC-DIRECT, AC-LOCAL, AC-UNSAFE
  - Effects: EFF-USER-CONFIG
  - Output: OUTP-T1
  - Receiver: T2
  - Verification: VR-DIRECT, VR-LOCAL, VR-UNSAFE
  - Lineage: shared
- [x] T2. Revalidate the unchanged Atlas execution authority
  completed 2026-08-15-2359
  - Owner: implementation-owner
  - Wave: W1
  - Depends on: T1
  - Targets: TGT-ATLAS-PREFLIGHT
  - Contracts: CONTRACT-SLUG, CONTRACT-PREFLIGHT, CONTRACT-ATLAS
  - Criteria: AC-ATLAS, AC-PRESERVE
  - Effects: none
  - Output: OUTP-T2
  - Receiver: dev-verification
  - Verification: VR-ATLAS, VR-PRESERVE
  - Lineage: shared

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-DIRECT | Direct-repository slug `IMPROVE_deep` in OMP and Grok contexts | Both contexts return one eligible direct result with plan ID `2026-08-09-1700_IMPROVE_deep`. | TGT-EXECUTOR, TGT-TESTS | T1 |
| AC-LOCAL | Local-authority bytes with slug `IMPROVE_deep` | Preflight returns unavailable with `PLAN_PREFLIGHT_UNAVAILABLE`; lowercase kebab-case local behavior remains eligible. | TGT-EXECUTOR, TGT-TESTS | T1 |
| AC-UNSAFE | Leading, trailing, repeated, dotted, or path-separator slug forms | Every input fails closed with `PLAN_PREFLIGHT_UNAVAILABLE` and no filesystem mutation. | TGT-EXECUTOR, TGT-TESTS | T1 |
| AC-ATLAS | Exact approved Atlas plan and direct slug `IMPROVE_deep` | Backend preflight returns `eligible`, `direct`, and `repository-active` for SHA `2d9a838d7f357052f55b3ad714da80718a3f0167f7923cce5c8e6eeabb2e39b7`. | TGT-ATLAS-PREFLIGHT | T2 |
| AC-PRESERVE | Post-repair source and Atlas target recheck | Pre-existing unrelated changes remain intact and all six approved target-bundle hashes equal their bound values. | TGT-ATLAS-PREFLIGHT | T2 |

## Verification / Done criteria

- [x] VR-DIRECT. Exercise repository-native direct slugs in both contexts
  - Criterion: AC-DIRECT
  - Proof class: worker smoke
  - Scenario / environment / fixture: ExecutorPlanPreflightTests with one direct `IMPROVE_deep` active plan in OMP and Grok
  - Evidence form: two eligible direct result payloads with exact plan identity
  - Target recheck: TGT-EXECUTOR, TGT-TESTS
  - Receiver: T2
- [x] VR-LOCAL. Exercise the unchanged local-authority grammar
  - Criterion: AC-LOCAL
  - Proof class: worker smoke
  - Scenario / environment / fixture: local-authority `IMPROVE_deep` negative case plus existing lowercase local fixtures
  - Evidence form: stable unavailable issue for uppercase local and eligible results for lowercase local
  - Target recheck: TGT-EXECUTOR, TGT-TESTS
  - Receiver: T2
- [x] VR-UNSAFE. Exercise unsafe repository slug boundaries
  - Criterion: AC-UNSAFE
  - Proof class: worker smoke
  - Scenario / environment / fixture: leading, trailing, repeated, dotted, and separated negative slug cases
  - Evidence form: stable unavailable results and unchanged fixture bytes
  - Target recheck: TGT-EXECUTOR, TGT-TESTS
  - Receiver: T2
- [x] VR-ATLAS. Invoke the exact previously blocked backend preflight
  - Criterion: AC-ATLAS
  - Proof class: worker smoke
  - Scenario / environment / fixture: approved Atlas direct plan with canonical repository root, current session local root, and exact same-identity local counterpart
  - Evidence form: eligible executor-plan-preflight/v1 JSON with exact identity and digest
  - Target recheck: TGT-ATLAS-PREFLIGHT
  - Receiver: dev-verification
- [x] VR-PRESERVE. Rehash approval boundaries after the repair
  - Criterion: AC-PRESERVE
  - Proof class: independent verification
  - Scenario / environment / fixture: exact two-file repair diff, approved plan SHA, and six established bundle hash commands
  - Evidence form: isolated intended hunks and seven matching SHA-256 values
  - Target recheck: TGT-ATLAS-PREFLIGHT
  - Receiver: dev-verification

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-T1 | T1 | TGT-EXECUTOR and TGT-TESTS exact post-edit revisions | completed, blocked, failed | T2 | Common Handoff from dev-handoff |
| OUTP-T2 | T2 | TGT-ATLAS-PREFLIGHT at approved plan revision | completed, blocked, transport-unavailable, authority-change-required | dev-verification | Common Handoff from dev-handoff |


## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-WORKTREE | implementation-owner | Fresh target diff proving pre-existing changes can be preserved | T1 | New user decision only if unrelated bytes must be overwritten or removed | Intended slug hunks are separable from existing work. |
| BLK-ATLAS-DRIFT | implementation-owner | Fresh plan and six-bundle SHA-256 comparison | T2 | Atlas plan revision and approval required for material drift | Exact plan SHA and all six bundle hashes match the approved baseline. |

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-PLAN | rule | rule://plan@sha256:18957065c857fb88e1e863a0bef89e826366d2c04c598478ad610f67e7d77624 | Defines authority, lifecycle, and exact-byte approval. |
| ANC-IMPL | rule | rule://plan-impl-spec@sha256:58d6fabcf02fcaf890849dc3b6451719463275731c26e9ca5b5175ab48c006cb | Defines the single parser and backend result contract. |
| ANC-OMP | rule | rule://plan-omp-transport@sha256:af0d6173498a78537999acf539f27f9312e84d919a16653990a0f3a2c8072f5c | Defines lowercase local-authority creation slugs and exact counterpart binding. |
| ANC-REPO | rule | rule://plan-repo-storage@sha256:438b416aa40ed11ac1241d3a7d831483a018e041c833a9d2996da3a91e0c83c2 | Defines repository-native direct identity and safe exact-path resolution. |
| ANC-EXECUTOR | script | /Users/kim/.dotfiles/.config/agents/skills/dev-implementation/scripts/executor_plan.py:18-20,1862-1984 | Owns authority-specific slug validation. |

- Assumptions: none

## Completion Summary

- Outcome: `OUT-EXECUTOR-DIRECT-SLUG` completed. Direct-repository slug `IMPROVE_deep` is eligible in OMP and Grok; local-authority and unsafe variants remain fail-closed without mutation.
- Final target: `sha256:979c3bc0f142d9ca83d48b7c7c42a0bd91137ac4b75203f16368b8f9b5c390cc` over executor `396b804c…681`, tests `aaff25e6…bd7`, and unchanged Atlas plan `2d9a838d…39b7`.
- Acceptance: `AC-DIRECT`, `AC-LOCAL`, `AC-UNSAFE`, `AC-ATLAS`, and `AC-PRESERVE` independently verified; `BLK-WORKTREE` and `BLK-ATLAS-DRIFT` resolved.
- Assurance: final verification `agent://VerifyPreserveEvidence` returned `VERIFIED`; initial review `agent://ReviewDirectSlugRepair` returned `APPROVED`; terminal curation `agent://AssessDirectSlugLearning` returned `NO DURABLE LEARNING`.
- Preservation: exact pre-repair bases authenticated, only six authorized hunks differ, the approved Atlas plan and six target bundles retain their bound SHA-256 values, and no Atlas repository, profile, vault, instance, or external effect occurred.
- Recovery accounting: semantic attempts remain `1/2`; post-assurance repair `1/1` was consumed by content-addressed evidence repair `sha256:ed88c4179f41b7a2da8cad5e645a7a244ea5db3e07b3e48198b3808cb48035e1`; no blocker remains.
