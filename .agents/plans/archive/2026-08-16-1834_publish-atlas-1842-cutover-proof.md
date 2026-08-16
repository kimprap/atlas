# Publish and approve the remaining Atlas cutover proof plan

**Datetime**: 2026-08-16-1834
**Authority kind**: local-authority
**Scope**: Exact publication and native approval of the direct-repository Atlas 1842 cutover proof Executor Plan
**Summary**: Publish the validated proof-only Executor Plan as one new direct-repository authority and obtain native approval of its exact bytes. Do not execute its proof tasks under this publication plan.
**Status**: CLOSED

## Objective

- Outcome: OUT-ATLAS-1842-PROOF-PLAN-PUBLICATION
- Observable end state: `.agents/plans/2026-08-16-1824_atlas-1842-cutover-proof.md` exists as a safe active direct-repository `PENDING` Executor Plan at SHA-256 `2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b`, passes the sole planner validator, has no same-identity archive or local authority counterpart, and has native approval binding that exact path and revision before any proof task starts.
- Progress signal: AC-DIRECT-PLAN-READY gains one publication, validator, classification, or native-approval observation, or BLK-DIRECT-PLAN gains exact storage or transport evidence.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-USER | direct user intent | conversation://2026-08-16/atlas-1842-cutover-proof | sha256:1edb8acb95466235bb27ae320cd5bff6b71cbd559f9095fb1520a8da1cf94fae | Authorizes creation and native approval of the new direct-repository proof plan. It does not authorize proof execution before that exact plan receives native approval. |
| AUTH-DRAFT | validated prospective direct-plan bytes | `local://atlas-1842-cutover-proof-direct-draft.md` | sha256:2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b | Exact source bytes to publish without rewriting. The local draft is not plan authority and must never become the same-identity local counterpart. |
| AUTH-PLAN-RULE | portable plan lifecycle | `rule://plan` | sha256:0c864d0a799b797634fa04dc692f50ad9904ca135571d26cd89173ce16859922 | Governs header, identity, lifecycle, and exact native approval boundary. |
| AUTH-IMPL-RULE | Executor Plan body | `rule://plan-impl-spec` | sha256:58d6fabcf02fcaf890849dc3b6451719463275731c26e9ca5b5175ab48c006cb | Governs the direct plan's portable body and planner validation. |
| AUTH-STORAGE-RULE | repository plan storage | `rule://plan-repo-storage` | sha256:cd537adc74d2908dc08e2c2e380568b9ca78cdaf292915bca28d620e0f898dbd | Governs direct-repository generation, no-overwrite publication, classification, and postconditions. |
| AUTH-VALIDATOR | sole Executor Plan validator | `/Users/kim/.agents/skills/dev-implementation/scripts/executor_plan.py` | sha256:53b3446d073f6b27c4d60dca007e30e7260e8b287bd69083fb7d0dba4937c8d3 | Planner validation must return `executor-plan-validation/v1`, `status:valid`, empty issues, and the exact draft SHA-256. |

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-DIRECT-AUTHORITY | AUTH-USER@sha256:1edb8acb95466235bb27ae320cd5bff6b71cbd559f9095fb1520a8da1cf94fae | Publish the requested proof plan directly at its repository active path with `Authority kind: direct-repository`; do not substitute an OMP local-authority projection. |
| DEC-BYTE-EXACT | AUTH-DRAFT@sha256:2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b | Publish AUTH-DRAFT complete bytes unchanged. Any source drift requires a new planner draft and renewed approval of this publication plan. |
| DEC-STORAGE | AUTH-STORAGE-RULE@sha256:cd537adc74d2908dc08e2c2e380568b9ca78cdaf292915bca28d620e0f898dbd | Use the shared generation lock, safe regular-file checks, same-directory staging and fsync, no-overwrite publication, and exact postcondition. Never ordinary-write, rename over, promote, adopt, retry, or infer success from equality. |
| DEC-SEPARATE-APPROVAL | AUTH-PLAN-RULE@sha256:0c864d0a799b797634fa04dc692f50ad9904ca135571d26cd89173ce16859922 | Approval of this local publication plan authorizes only publication and review submission. The new direct plan remains non-executable until native review binds its exact repository URI, complete bytes, SHA-256, and PENDING status. |
| DEC-NO-PROOF | AUTH-USER@sha256:1edb8acb95466235bb27ae320cd5bff6b71cbd559f9095fb1520a8da1cf94fae | Do not run AC-CONTRACTS, AC-RESEARCH, AC-INTEGRATED, Ruff, Atlas tests, CLI smoke, or independent verification under this publication outcome. |

## Scope, non-goals, and prohibited effects

- Read surfaces: AUTH-DRAFT; current active/archive/local-counterpart classification for identity `2026-08-16-1824_atlas-1842-cutover-proof`; AUTH-PLAN-RULE; AUTH-IMPL-RULE; AUTH-STORAGE-RULE; AUTH-VALIDATOR; native plan-review result.
- Change surfaces: This local-authority plan's lifecycle and managed projection; the one absent direct-repository target `.agents/plans/2026-08-16-1824_atlas-1842-cutover-proof.md`; ephemeral generation lock and same-directory staged bytes removed by their owning generation.
- Non-goals: Executing or revising the direct plan; proving any Atlas criterion; changing product bytes; mutating the active 1842 plan or archived 1519 plan; creating a same-identity local authority; archival, delivery, commit, push, deploy, release, bound profile, vault, or framework-sync work.
- Prohibited effects: No ordinary write to the direct plan path, overwrite, rollback, force operation, lock reclamation without the published safe conditions, active/archive ambiguity, local counterpart, product edit, proof command, Atlas/profile/vault I/O, stale-plan-gate edit, Git state change, or native-approval inference from validator success or storage publication.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-META-PLAN | local plan lifecycle | AUTH-USER plus native approval of this exact local plan | Only this publication plan and its managed projection may advance through their normal lifecycle. |
| EFF-DIRECT-PLAN | direct-repository plan create | AUTH-USER plus native approval of this publication plan | Create exactly `.agents/plans/2026-08-16-1824_atlas-1842-cutover-proof.md` from AUTH-DRAFT under the shared generation protocol. No replacement or archive effect is authorized. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-DIRECT-BYTES | Exact path, direct-repository header, PENDING lifecycle, complete prospective bytes, and SHA-256 | T1 | AUTH-DRAFT@sha256:2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b | T1 |
| CONTRACT-STORAGE | One safe direct-repository generation with absent active/archive/local counterpart precondition and exact postcondition | T1 | AUTH-STORAGE-RULE@sha256:cd537adc74d2908dc08e2c2e380568b9ca78cdaf292915bca28d620e0f898dbd | T1 |
| CONTRACT-NATIVE-APPROVAL | Native review binds exact repository path, complete bytes, SHA-256, and PENDING state before execution | T1 | AUTH-PLAN-RULE@sha256:0c864d0a799b797634fa04dc692f50ad9904ca135571d26cd89173ce16859922 | T1 |

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-DIRECT-PLAN | `.agents/plans/2026-08-16-1824_atlas-1842-cutover-proof.md`; same-identity archive; current-session `local://atlas-1842-cutover-proof-plan.md`; AUTH-DRAFT; native plan review | T1 | Active, archive, and local counterpart observed absent; AUTH-DRAFT sha256:2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b | AUTH-VALIDATOR planner consumer; backend preflight after native approval | AC-DIRECT-PLAN-READY |

## Execution policy

- Assurance: Planner-only exact-byte publication with structural validation, storage postcondition, and native approval; no product implementation assurance stage.
- Topology: one-owner sequential single lineage.
- Max concurrency: 1
- Isolation: Shared current repository; publish one absent plan path without modifying or absorbing any existing dirty-worktree byte.
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: Stop on source drift, active/archive/local presence, unsafe path, lock contention, target race, validator drift, or native-review mismatch; never retry, overwrite, merge, or promote.
- Decomposition: One canonical `planner` owner publishes the exact draft, validates final bytes, submits native review, and waits for the exact approval result. No delegation or proof execution.
- Effect limit: EFF-META-PLAN, EFF-DIRECT-PLAN
- Orchestrator profile: One qualified planner with no code implementation or delegation. If native direct-repository approval is unavailable, return `transport-unavailable` without creating a local-authority substitute.

## Tasks

- [ ] T1. Publish validate and natively approve the direct proof plan
  - Owner: planner
  - Wave: W0
  - Depends on: none
  - Targets: TGT-DIRECT-PLAN
  - Contracts: CONTRACT-DIRECT-BYTES, CONTRACT-STORAGE, CONTRACT-NATIVE-APPROVAL
  - Criteria: AC-DIRECT-PLAN-READY
  - Effects: EFF-META-PLAN, EFF-DIRECT-PLAN
  - Output: OUTP-DIRECT-PLAN
  - Receiver: dev-implementation
  - Verification: VR-DIRECT-PLAN-READY
  - Lineage: shared
  - Reread AUTH-DRAFT and require SHA-256 `2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b`. Rehash AUTH-PLAN-RULE, AUTH-IMPL-RULE, AUTH-STORAGE-RULE, and AUTH-VALIDATOR. Reconfirm the exact active, archive, and `local://atlas-1842-cutover-proof-plan.md` counterpart are absent and safe parent directories resolve inside `/Users/kim/dev/atlas/app`.
  - Canonicalize repository root `/Users/kim/dev/atlas/app` and plan identity `2026-08-16-1824_atlas-1842-cutover-proof`. Compute `GENERATION_KEY` as SHA-256 over the canonical root, one NUL byte, and the plan identity; atomically claim `${TMPDIR}/omp-plan-artifact-locks/GENERATION_KEY.lock` and create `owner.json` without overwrite using the current PID, ISO creation time, and one unguessable token. Hold that exact generation through observation, staging, publication, reread, and postcondition; release only when `owner.json` still contains the same token.
  - Require active, archive, and local counterpart to remain absent; require destination components to be safe directories with no symlink target. Stage AUTH-DRAFT complete bytes in the active directory using an exclusive unique regular file, fsync the staged file, reread and compare the source and staged SHA-256, and recheck the generation plus all three identity locations. Publish to the absent active path with a no-overwrite hard link, fsync the directory, remove only the owned staging file, then reread the active file and require byte equality, `direct-repository`, `PENDING`, exact identity, absent archive, absent local counterpart, and SHA-256 `2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b`. On contention, drift, unsafe state, raced destination, or unverifiable ownership, preserve observed objects and stop with `effect=none` before publication or `effect=possible-complete` after a possibly completed publication.
  - Run `python3 /Users/kim/.agents/skills/dev-implementation/scripts/executor_plan.py .agents/plans/2026-08-16-1824_atlas-1842-cutover-proof.md --context omp --consumer planner` from `/Users/kim/dev/atlas/app`. Require schema `executor-plan-validation/v1`, `status:valid`, empty issues, and `plan_sha256:2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b`.
  - Submit the exact repository plan through native plan review. Require the approval record to bind the exact active path, complete SHA-256, `direct-repository`, and `PENDING` status. Validator success or publication alone is not approval. Do not start direct-plan T1 or any Atlas proof before the native approval result is current.
  - After approval, reread and rehash active, archive, local counterpart, AUTH-DRAFT, and the native approval binding. Emit OUTP-DIRECT-PLAN to `dev-implementation`; the receiver must run backend preflight against the same exact path and approval before any proof task becomes ready.

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-DIRECT-PLAN-READY | Exact AUTH-DRAFT, absent direct-plan identity, current storage rules, sole planner validator, and native plan review | One safe active direct-repository PENDING plan exists at SHA-256 `2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b`; archive and local counterpart are absent; validator is valid; native approval binds exact path, bytes, revision, and status; no proof or unrelated effect occurred. | TGT-DIRECT-PLAN | T1 |

## Verification / Done criteria

- [ ] VR-DIRECT-PLAN-READY. Prove exact publication validation classification and approval
  - Criterion: AC-DIRECT-PLAN-READY
  - Proof class: planner publication proof and native approval observation
  - Scenario / environment / fixture: From `/Users/kim/dev/atlas/app`, rehash AUTH-DRAFT and all governing rules; classify active, archive, and local counterpart before and after one generation; validate the published file with AUTH-VALIDATOR; observe the native plan-review binding; rehash every identity location after approval.
  - Evidence form: Source and final SHA-256 are identical; storage generation owner and effect are recorded; active is safe direct-repository PENDING; archive and local counterpart are absent; validator report is valid with empty issues; native approval names the exact path/revision/status; changed-artifact closure contains only the direct plan plus this local plan's managed lifecycle; zero Atlas proof or product effect is recorded.
  - Target recheck: TGT-DIRECT-PLAN
  - Receiver: dev-implementation

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-DIRECT-PLAN | T1 | Exact direct-repository plan path and SHA-256, storage postcondition, validator report, native approval binding, and no-proof effect accounting | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation | Common Handoff from dev-handoff binding exact authorities, direct plan, storage effect, validation, approval, unchanged identities, prohibited effects, and one receiver. |

## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-DIRECT-PLAN | planner | Exact source/rule hashes, active/archive/local classification, generation owner, stage/publication observation, validator report, and native-review result | T1 | Any draft, rule, identity, safety, generation, validator, or approval drift stops. Source revision requires a new publication-plan revision and fresh approval; post-publication uncertainty requires read-only classification before any new authority. | AUTH-DRAFT and governing rules match; identity is safely absent before publication or exact after publication; validator is valid; native approval binds the exact current active file. |
| BLK-DIRECT-TRANSPORT | human plan owner | Native direct-repository review capability result and exact unavailable boundary | T1 | Do not substitute local authority, prose approval, equality, sync receipt, or another plan identity. | Native review can bind the exact direct-repository URI and revision, or the outcome remains `transport-unavailable`. |

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-DRAFT | validated prospective plan | `local://atlas-1842-cutover-proof-direct-draft.md`@sha256:2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b | Sole publication source; never rewrite during T1. |
| ANC-ACTIVE | direct authority target | `.agents/plans/2026-08-16-1824_atlas-1842-cutover-proof.md` | Sole active publication and native approval target. |
| ANC-STORAGE | direct storage contract | `rule://plan-repo-storage`@sha256:cd537adc74d2908dc08e2c2e380568b9ca78cdaf292915bca28d620e0f898dbd | Own generation, no-overwrite publication, classification, and postcondition. |
| ANC-VALIDATOR | planner validator | `/Users/kim/.agents/skills/dev-implementation/scripts/executor_plan.py`@sha256:53b3446d073f6b27c4d60dca007e30e7260e8b287bd69083fb7d0dba4937c8d3 | Sole structural validity report before native review. |
| ANC-BACKEND | execution boundary | `rule://plan`@sha256:0c864d0a799b797634fa04dc692f50ad9904ca135571d26cd89173ce16859922; `rule://plan-impl-spec`@sha256:58d6fabcf02fcaf890849dc3b6451719463275731c26e9ca5b5175ab48c006cb | Native approval plus backend preflight are the only path from publication to direct-plan readiness. |

- ASM-DRAFT: AUTH-DRAFT is available at its exact local URI and revision until publication completes. Fallback: missing or changed bytes stop `authority-change-required`; do not reconstruct or rewrite them from prose.
- ASM-ABSENCE: Active, archive, and same-identity local counterpart were observed absent during planning. Fallback: any presence triggers BLK-DIRECT-PLAN classification and no publication; never replace, adopt, promote, or delete it.
- ASM-NATIVE-REVIEW: The current harness may expose native review for a repository-native plan. Fallback: if it cannot bind the direct repository URI and SHA-256, return `transport-unavailable`; do not create a local-authority substitute or execute the proof.

## Completion Summary

- Findings: Publication of `.agents/plans/2026-08-16-1824_atlas-1842-cutover-proof.md` at `sha256:2e64f250a4109cf1419f488b89f34e6a5604fe115929b5e9e0631ef6be4d2a7b` succeeded. Native approval of that direct plan was not obtained.
- Decisions: User 2026-08-16 cancelled the remaining approval work. `2026-08-16-2102_atlas-1842-local-proof` became the executable proof identity. This wrapper is `CLOSED`, not `DONE`, because `AC-DIRECT-PLAN-READY`'s approval clause was never observed.
- Delivered behavior: 1824 was published as `direct-repository` at the bound hash; later close-out treated it as superseded by 2102.
- Residual risks: A `CLOSED` identity cannot be archived under the current storage contract, so this managed projection remains active.
