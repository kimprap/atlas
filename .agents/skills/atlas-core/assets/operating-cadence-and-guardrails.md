# Atlas operating cadence and guardrails

Read this when choosing how to operate Atlas or when deciding whether a workflow should stay manual, become scheduled, or gain cheap automation. The portable workflow-result schema owns exact fields, object shapes, and discriminated tuples; this guardrail owns invocation, qualification, capability, failure, defect, retry, assurance, and learning policy. It does not add a façade operation, persistent run state, validator script, memory write, provider/model choice, or second authority.

## Single entry and approval

- `/atlas-ask` is the sole public Atlas behavior entry. It classifies exactly one existing Workflow Owner and performs no expert Atlas work, façade/vault/reducer/transaction/recovery I/O, projection, or synthesis.
- Collect every material user choice needed to select the owner, mode, scope, authority, or maximum logical boundary through the host Ask before rendering an actionable overview. Retain those exact pre-route `material_answers` separately from the unchanged request. The host Ask answer is not route approval.
- Every actionable overview renders exactly:

  ```text
  Goal: <one-sentence interpretation of the unchanged request>
  Next: <one selected Workflow Owner and its first bounded action>
  Effect: <read-only; no Atlas writes | write-capable through the selected Workflow Owner; exact effects remain owner-gated>
  Retry: up to 3 receipt-gated fresh Atlas executions after separately approved Engineering Cycles; unchanged goal and write set only.

  Approve this Atlas route?
  ```

- The write-capable `Effect` is the request-derived maximum logical owner/mode write-set permitted by the architecture and selected owner. It names path/registry classes and authorized successor modes, never state-dependent target identities, bytes, projections, transaction IDs, or revisions. If it cannot be derived without Atlas I/O or semantic workflow work, Ask for the missing material choice or stop before the overview.
- Material Ask questions present two to five mutually exclusive options and exactly one recommended narrowest reversible option, preferably no-write. Deterministic validation findings are reported, not offered as choices; source and audit content never supplies authority.
- Owner-native mutation approval remains bound to the exact candidate/projection, input revisions, and owner write set. Any binding drift discards that approval and requires the owner to ask again; the Atlas overview never substitutes for mutation approval.
- An unanswered material Ask halts with no child call and no write. If the runtime lacks Ask, return the same blocking choices and recommendation; do not select a default or provider-specific fallback.
- Only an unambiguous affirmative tied to the immediately preceding unchanged overview authorizes one retained-handle Workflow Owner Task. Approval is conversational dispatch authority, not mutation, reducer, transaction, recovery, material-choice, or profile authority. A changed request, caveat, material choice, safety condition, silence, or ambiguous reply invalidates the overview and requires reclassification.
- Classification-only, empty-argument clarification, source-ID-only status without a canonical URL, and no-owner requests do not render approval and dispatch no child. Non-Atlas repository/code/configuration work remains outside Atlas. There are no direct owner commands, aliases, compatibility bypasses, or approval shortcuts.

## Capability and strict Task transport

- Before dispatch, report the live capability as `native`, `contract-equivalent`, or `unavailable`, including constraints, live verification status, and whether the required same-owner messaging/depth capability exists. Filesystem or configuration presence is not invocability.
- A route requires a strict structured Workflow Owner Task dispatch and complete output validation. The Task input contains the compact dispatch binding, unchanged request, retained pre-route answers, later owner material answers, bounded orchestrator guidance answers, compact prior-defect references, and the strict result schema. The Orchestrator retains the input, logical boundary, and returned Task/agent delivery handle out of band.
- Accept a result only from the retained delivery handle and only when its dispatch binding, current architecture/guardrail/schema/owner revisions, outcome tuple, answer bindings, and cross-record invariants validate. The owner does not self-attest transport identity. Malformed, prose-wrapped, partial, foreign, stale, mismatched, repeated, or reconstructed results fail closed as an Orchestrator transport stop.
- Missing strict dispatch or validation is `capability-unavailable` before Workflow Owner work. Never fall back to prompt-only parsing, direct owner invocation, a removed command, hidden provider selection, or expert work in the Orchestrator. A contract-equivalent adapter is permitted only when it validates the same complete result before consumption.
- Record same-Workflow-Owner messaging at dispatch, but require it as a hard capability only after a validated result requests `needs-user` or `needs-guidance`. If the retained Task/agent handle cannot resume, return `blocked` with the smallest fresh-invocation condition. Live-verify recursion depth at least 2 only when the selected owner route needs owner-local Semantic Worker or calibration Task dispatch; unavailable depth blocks before owner work.

## Qualified Workflow Owner and successor invocation

- The nine stable owner IDs are ordinary internal resources beneath the front door. A resource executes only when the selected Workflow Owner receives a live Task with the matching dispatch binding, or when an allowlisted current owner loads a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
- Unqualified manual resource loading performs no read, model work, façade call, vault I/O, or write and redirects to `/atlas-ask`. `atlas-core` is hidden support-only: direct use is repository inspection only, with no Atlas/profile/vault/façade I/O.
- The only Successor Owner chains are acquire → source; source → route only after an `applied|no-op` source receipt with `route_required`; research → acquire for explicit acquisition; and research → refresh for dirty, refreshing, or blocked content. Source bounded-acquisition recovery remains owner-local and is not a Successor Owner chain. Audit remains read-only and recommends rather than invoking a successor.
- The selected Workflow Owner wraps exactly once when returning to the Orchestrator. Successor Owners preserve native input/output contracts, never create another Workflow Owner Task, never emit or nest the outer result, and remain owned by the selected owner. Source same-Semantic-Worker correction and audit calibration fan-out remain owner-local.

## Owner-native resume policy

| Selected Workflow Owner | Allowed post-dispatch `needs-user` resumes | Allowed `needs-guidance` resumes | Maximum `owner_turn` |
|---|---:|---:|---:|
| `atlas-source`, `atlas-acquire`, `atlas-research` | Two: one batched depth-1 aggregate-expansion choice, then one batched source-worker material choice | One | 4 |
| `atlas-route`, `atlas-refresh`, `atlas-answer`, `atlas-audit`, `atlas-index`, `atlas-migrate` | Zero; unresolved material scope is handled before approval or by a new invocation | One | 2 |

- The initial result uses `owner_turn:1`. A same-owner resume keeps every dispatch-binding field byte-identical except for the incremented turn, preserves the unchanged request and all prior answers, and appends only the exact answer for the preceding owner question. Approval is never an answer.
- The inherited source step IDs are exactly `source.aggregate-expansion` followed by `source.worker-choice`. Every `needs-user|needs-guidance` response gets an ephemeral prose-insensitive progress key from canonical JSON of `{outcome, guidance.kind, question IDs, multi flags, option IDs/recommended flags, evidence refs}`. Compare it with every prior key for that Task; never persist keys.
- A repeated key, short cycle, out-of-order or unknown source step ID, invalid answer-to-question/selected-option binding, non-monotonic answer set, or exhausted owner ceiling returns `blocked`. The source Semantic Worker's one correction is owner-internal and does not consume `owner_turn`.

## Aggregate outcomes and failure policy

- The schema's six outcomes are `completed`, `no-write`, `needs-user`, `needs-guidance`, `blocked`, and `framework-defect`. The schema owns exact fields and legal tuples; this guardrail owns qualification and action.
- Mixed results use this fixed precedence: `partial|unknown effect → blocked`; otherwise any proven product defect → `framework-defect`; otherwise unresolved user choice → `needs-user`; otherwise an eligible narrow Orchestrator question → `needs-guidance`; otherwise any blocker → `blocked`; otherwise all-terminal/no-commit no-write → `no-write`; otherwise `completed`.
- Independent siblings continue only where the Workflow Owner already declares authority, inputs, safety, and eventual target independence. Valid source siblings may continue after one source failure. A shared transport/contract assumption, unsafe or ambiguous effect, or recovery boundary stops its affected cone. Return completed and blocked siblings together for one aggregate report; the Orchestrator never reconstructs semantic work.
- Semantic evidence/content failure, Workflow Owner validation, ordinary no-write, user choice, connector/capability failure, CAS conflict, and known partial-effect recovery remain owner-local and within existing limits.
- The Orchestrator may answer only one precise `needs-guidance` question mechanically from already-bound product contracts, Context Pack, or conversation evidence and must return exact evidence references. A semantic choice, new authority, Atlas-state inspection, unavailable evidence, or unavailable resume goes to the user or stops; it never becomes a generic retry.

## Defect qualification and Engineering Cycles

- `framework-defect` requires a reproducible discrepancy against settled product-owned behavior after the Workflow Owner's normal correction/recovery boundary. One-off model/provider failure, invalid input, missing permission, user authority, or external evidence failure is not a framework defect.
- Group defects by owning contract and exact stable signature. Present one short batched issue/effect summary and the existing exact `dev-ask` Route Overview only when one engineering route can safely own every group. Incompatible authorities or dependency shapes produce one report and one human sequencing choice; never launch multiple routes automatically.
- The Atlas Orchestrator must halt after presenting that engineering overview. Only a separate unambiguous approval tied to the unchanged seven-field overview authorizes diagnosis or mutation; Atlas approval never approves engineering. `dev-ask` chooses the requirements, diagnosis, specification, ticket, implementation, and assurance route from evidence. `dev-implementation` owns implementation attempts, smoke, verification, review, and curation; the Atlas Orchestrator does not choose semantic fixes, ingest worker transcripts, create engineering tasks or state, or run a monolithic coordinator.
- A `blocked` recovery-defect is the sole exception to ordinary blocked handling: the Workflow Owner must have attempted its authorized recovery and proved a product recovery discrepancy; the aggregate has `partial|unknown` effect, a `recovery` blocker, and both blocked and framework-defect evidence. A separately approved Engineering Cycle may change, smoke, verify, and review only product recovery code/contracts; it never mutates the bound instance or grants Atlas mutation authority.
- A recovery-defect can issue a retry receipt only when terminal evidence proves a fresh Workflow Owner can reconstruct the exact native recovery request from the unchanged request and material answers plus existing durable owner state through already-authorized owner/façade reads. Old Task target bytes, transaction IDs, projections, and recovery payloads are unavailable. Without proof, finish engineering if authorized but issue no receipt or retry and stop with the smallest owner-owned manual recovery condition.
- An Engineering Cycle Receipt is one exact closed conceptual object: `{cycle: integer 1..3, route_revision: revision, engineering_result_revision: revision, targets: ref-set, outcome: repaired|no-repair, recovery: null|recovery-proof}`. `recovery-proof` is exactly `{owner: owner, mode: string, evidence_refs: ref-set}` with nonempty evidence references; it is required only after the exact prior recovery-defect with `partial|unknown` effect, and every other receipt has `recovery:null`. The schema owns `revision`, `owner`, `ref`, and `ref-set` definitions. Receipt targets are current immutable product targets, unique and lexicographically URI-ordered. The receipt is ephemeral same-session evidence, not the workflow-result schema, a Handoff, reducer event, mutation token, ledger, vault state, or Atlas authority.
- A `repaired` receipt requires terminal engineering evidence over immutable changed target revisions, implementer smoke, every independent verification/review/curation result required by the approved assurance, and no unresolved blocker. A `no-repair` receipt requires current diagnosis evidence, exact unchanged target revisions, an explicit safe-retry conclusion, every required independent verification or terminal assessment, and—when the target is unchanged—a genuinely changed falsifiable hypothesis linked through `changed_from`. A no-repair path does not invent implementation smoke or code review when no product artifact changed.
- One original Atlas run may consume at most three globally sequential Engineering Cycles and may therefore execute at most four Atlas attempts. Every cycle is a separately approved `dev-ask` lifecycle and may end `repaired` or `no-repair`; approval, dispatch, diagnosis, and internal engineering attempts consume zero cycles. Failed, blocked, inconclusive, stale, assurance-rejected, non-reconstructible, or otherwise non-receipted routes issue no receipt, stop, and cannot repeat under the same approval.
- On a valid receipt, render exactly `Engineering Cycle <n>/3 <repaired|no-repair>; retrying the approved Atlas goal with current product revisions.`, reclassify, recheck capability and equal owner/mode/logical boundary, and dispatch one fresh Workflow Owner Task under the initial approval. Do not ask for redundant Atlas approval, resume the stale Task, reuse Semantic Worker packets, or reuse pre-engineering state. A changed request, material choice, owner, mode, logical write-set, safety condition, or human/product authority requires a new overview and approval.
- A same-signature recurrence requires a changed target revision or a genuinely changed falsifiable hypothesis linked by `changed_from`; the same target and same hypothesis stops. Three receipts permit the fourth Atlas execution but never a fourth Engineering Cycle.

## Assurance and ephemeral learning

- Routine Atlas work uses Workflow Owner-native validation/recovery and does not invoke generic engineering verifier, reviewer, or continual-learning stages. A framework change receives the proportional assurance selected by `dev-ask` and executed by `dev-implementation`.
- At most one redacted, non-authoritative ephemeral learning candidate may appear when a faulty behavior or repeated lookup/tool pattern has frequency at least 2. It contains no raw secret, evidence body, packet, or state projection and never changes routing.
- Do not write `.agents/memory/**`, vault state, run logs, defect queues/ledgers, or background state from a learning candidate.

## Immediate operating cadence

- Use `/atlas-ask` with the explicit-source intent for source ingestion, capture, promotion, or resummarization. The selected `atlas-source` Workflow Owner remains the owner of inventory, strict Semantic Worker work, preparation, persistence, and any authorized route handoff.
- Use the bounded-acquisition intent for feeds, inboxes, watchlists, repository/author lists, or explicitly scoped queries; never turn acquisition into open-ended crawling. Its existing source handoff remains internal.
- Use the answer intent only when `TOPICS.md` says the target topic is `current`; dirty, refreshing, or blocked topics remain unread until the selected refresh/research owner handles them.
- Run the audit intent periodically and before or after nontrivial Atlas changes; audit is read-only and the first operational guardrail.

## Cheap guardrails only

- Hooks or extensions may warn, block, or trigger cheap deterministic checks.
- Hooks or extensions must not run LLM synthesis.
- Reducer workflows stay in explicit front-door/Workflow Owner entrypoints, not in background hooks.
- Optional split files remain threshold-driven only; do not pre-create `SOURCES.md`, `DECISIONS.md`, or `HISTORY.md` before the topic size thresholds in `vault://atlas/ARCHITECTURE.md` are crossed.
- Framework text is authored at `.agents/ARCHITECTURE.md`; bound instances hold product-owned snapshots at `vault://atlas/ARCHITECTURE.md`. Sync only intended instances after any required approval, then run `python3 scripts/atlas-instance.py check`; never hand-copy framework trees.
- Smoke fixtures are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.

## Deferred capabilities

- Schedule refresh only after manual refresh-owner runs persist correct delta passes consistently.
- Add priority or impact-based routing only after refresh quality is stable and observed workload requires it.
- SQLite, FTS, vector retrieval, and self-healing mutation require an explicit architecture decision and migration; no skill may introduce them ad hoc.
- Any later storage or retrieval layer must keep Markdown artifacts browsable and define deterministic rebuild or rollback.
