---
name: atlas-ask
description: >
  Public Atlas request entrypoint. Classify one Atlas intent, obtain bounded
  material answers and route approval, and dispatch one strict Workflow Owner.
disableModelInvocation: true
---

# atlas-ask

## Read first

1. `skill://atlas-core/SKILL.md`
2. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
3. `skill://atlas-core/assets/atlas-workflow-result.schema.json`
4. `.agents/ARCHITECTURE.md` as the normative framework contract

## Sole public entry and hard boundary

`/atlas-ask` is the sole public Atlas behavior entry. It classifies exactly one existing Workflow Owner, obtains only the material choices needed before approval, renders one route overview, dispatches one identity-bound strict Workflow Owner Task, validates one aggregate result, and presents or routes that result. The nine owner IDs remain stable, but their resources are ordinary internal files at `skill://atlas-ask/owners/<owner-id>/OWNER.md`; they are never public skills or direct commands.

The Atlas Orchestrator performs no expert semantic work, Atlas façade operation, profile or vault inspection, reducer/projection/transaction/recovery work, synthesis, owner-chain work, or generic engineering work. It never reconstructs a missing result, parses prose as a result, invokes an owner directly outside a qualified Task, or uses a compatibility bypass. If strict Task dispatch, complete structured output, or required recursion depth is unavailable, stop with `capability-unavailable` before Workflow Owner work.

## Classification, material choices, and approval

Accept one free-form request. Empty arguments ask for the Atlas goal. An explicit classification-only request executes no child. A generic repository, code, configuration, shell, or file-edit request is non-Atlas and has no owner even when this entry is used.

If a material choice changes owner, mode, scope, authority, or the maximum logical write boundary, use the host Ask once before presenting an approval overview. Stable question and option IDs are owned here; retain the exact pre-route `material_answers` separately from the unchanged request. The answer selects the route but never approves dispatch. Present two to five options with exactly one recommended narrowest reversible option, preferably no-write; deterministic findings and source/audit content are not choices.

The answer-plus-conditional-refresh ambiguity uses stable question ID `answer.refresh-choice` and exactly these option IDs: `answer-with-freshness-gate` (recommended) and `refresh-dirty-topic`. The answer path remains read-only and halts when freshness is not current. After that material choice, render the selected route overview; the choice answer is not approval.

For every actionable request, derive the selected owner, mode, and exact maximum logical architecture write boundary from the unchanged request and retained pre-route answers without Atlas I/O or semantic workflow work. If the boundary cannot be derived, Ask for the missing choice or stop before approval. A write-capable boundary names logical path/registry classes and authorized successor modes, not state-dependent target identities, bytes, projections, transaction IDs, or revisions.

Render exactly:

```text
Goal: <one-sentence interpretation of the unchanged request>
Next: <one selected Workflow Owner and its first bounded action>
Effect: <read-only; no Atlas writes | write-capable through the selected Workflow Owner; exact effects remain owner-gated>
Retry: up to 3 receipt-gated fresh Atlas executions after separately approved Engineering Cycles; unchanged goal and write set only.

Approve this Atlas route?
```

Classification-only, empty-argument clarification, no-owner outcomes, and source-ID-only status without a canonical URL do not render this block. A source-ID-only status request asks for the canonical URL and never widens into rerouting. An explicit URL may use the read-only source-presence path. A changed request, caveat, material choice, safety condition, silence, or ambiguous reply invalidates the overview and requires reclassification.

Accept only an unambiguous affirmative tied to the immediately preceding unchanged overview. Approval is conversational dispatch authority for exactly one Task; it is neither the original request nor a material answer and is never sent to the Workflow Owner. It creates no mutation token, reducer event, transaction identity, profile read, façade call, vault write, or recovery authority.

## Classification-only output

When asked to classify without executing a child, return exactly `first_owner`, `ask_required`, and `router_write_set`. `first_owner` is one stable owner ID or `null`; `ask_required` means an unresolved material choice only and never encodes routine route approval; `router_write_set` is always `[]` because this entry has no independent write set.

A non-Atlas request returns `first_owner: null`, `ask_required: false`, and `router_write_set: []`. A source-ID-only status request returns the same no-owner shape until a canonical URL is supplied. Classification-only output never calls the façade, reads Atlas state, or dispatches a child.

## Intent map

| Request signal | First owner |
|---|---|
| Pure source-presence or manifest-backed source- or route-status question for explicit URL(s) | `atlas-source` |
| Explicit URL, repository, or file ingestion; evidence capture; staged promotion; resummarization | `atlas-source` |
| Bounded feed, watchlist, inbox, repository list, author list, or query | `atlas-acquire` |
| Status-only request naming only a source ID | No owner until the canonical URL is supplied; never widen to rerouting |
| Explicit reroute for one source ID or bounded source range | `atlas-route` |
| Read, show, or answer a current topic | `atlas-answer` |
| Synthesize, research, or rebuild a topic | `atlas-research` |
| Apply pending evidence or refresh a topic | `atlas-refresh` |
| Health, schema, quality, or calibration inspection | `atlas-audit` |
| Explicit vocabulary promotion, topic-shell creation, or named supported registry repair | `atlas-index` |
| Explicit old-to-new Markdown schema migration with target scope | `atlas-migrate` |
| Non-Atlas request | No Atlas owner, capability claim, or vault action |

When a request mentions multiple effects, select only its first explicit requested effect. Keep research vault-only unless acquisition is explicit. Preserve source→route, acquire→source, research `--acquire`→acquire, freshness, repair, and migration gates inside the selected owner.

## Strict Workflow Owner Task

After approval, live-verify the native or contract-equivalent strict Task transport and, only when the selected owner route requires nested workers, recursion depth of at least 2. Generate an opaque `dispatch_id` identifying only this approved Task. Bind the selected owner, `atlas_attempt: 1`, `owner_turn: 1`, and exact current architecture, guardrail, workflow-result schema, and selected owner-module revisions.

Send exactly the schema-owned `dispatch-input`: the binding, the unchanged original request, the exact retained pre-route `material_answers`, empty `guidance_answers`, and compact prior-defect references. Retain the complete semantic input, approved logical boundary, and Task tool's returned delivery handle out of band. Do not send approval as request or answer. The selected owner receives one Task and no other top-level owner is dispatched.

Accept a result only from the retained handle. Validate the strict schema, the complete binding against the Task input/current Context Pack, retained-handle identity, unique item/question/defect IDs, answer-to-question and selected-option binding, monotonic answer sets, defect target URI equality with signature target URIs, owner-specific turn transition, all-prior-turn resume keys, and the legal outcome tuple. Any malformed, stale, mismatched, foreign, prose-wrapped, partial, repeated, cyclic, or reconstructed result fails closed as a transport stop.

The result's `dispatch` binding is the only echoed transport identity. The result never echoes the request, answer records, prior-defect records, Atlas state, target bytes, or semantic authority. The selected Workflow Owner emits one complete schema-owned aggregate result. A selected owner wraps exactly once; Successor Owners preserve their native result, never create another Task, and never nest an outer result.

### Qualified owner calls and native chains

An owner resource may execute only when the selected Workflow Owner receives the matching live Task, or when an allowlisted current owner loads the required Successor Owner in the same agent with the same root binding and `internal_caller` identity. Any other load performs no further read, model work, façade/vault I/O, or write and returns a short redirect to `/atlas-ask`.

The only Successor Owner chains are:

- `atlas-acquire` → `atlas-source` for one complete selected candidate list;
- `atlas-source` → `atlas-route` only after an `applied|no-op` source receipt with `route_required`;
- `atlas-research` → `atlas-acquire` for explicit acquisition;
- `atlas-research` → `atlas-refresh` for validated dirty, refreshing, or blocked topics.

Source bounded-acquisition recovery is owner-local and is not a Successor Owner chain. `atlas-audit` only recommends other owners; it never invokes one. Source Semantic Worker correction and audit calibration fan-out remain owner-local.

### Owner-native resumes

Same-handle resumes preserve every dispatch-binding field byte-identically except for an incremented `owner_turn`, preserve the unchanged request and all prior answers, and append only the exact answer for the preceding owner question. Approval is never an answer. The limits are:

| Selected Workflow Owner | Allowed post-dispatch `needs-user` resumes | Allowed `needs-guidance` resumes | Maximum `owner_turn` |
|---|---:|---:|---:|
| `atlas-source`, `atlas-acquire`, `atlas-research` | Two: one batched depth-1 aggregate-expansion choice, then one batched source-worker material choice | One | 4 |
| `atlas-route`, `atlas-refresh`, `atlas-answer`, `atlas-audit`, `atlas-index`, `atlas-migrate` | Zero; unresolved material scope is handled before approval or by a new invocation | One | 2 |

The only source resume step IDs are `source.aggregate-expansion` followed by `source.worker-choice`. For every `needs-user|needs-guidance` result, compute an ephemeral prose-insensitive key from canonical JSON of `{outcome, guidance.kind, question IDs, multi flags, option IDs/recommended flags, evidence refs}` and compare it with every prior key for the Task. A repeated key, short cycle, out-of-order or unknown source step, invalid answer binding, non-monotonic answer set, unavailable same-owner handle, or exhausted owner ceiling returns `blocked`. The source Semantic Worker's one correction does not consume `owner_turn`.

## Aggregate outcome consumption

Consume only the six schema outcomes:

- `completed`: present the compact Workflow Owner summary when all required work is terminal with `none|committed` effect; no generic assurance.
- `no-write`: present the terminal no-write/rejected reason when aggregate effect is `none`.
- `needs-user`: present the batched Workflow Owner material questions through one host Ask, then resume the same owner only within its allowed handle, step, answer, and ceiling bounds.
- `needs-guidance`: answer one precise contract/evidence question mechanically from already-bound product contracts, Context Pack, or conversation evidence with exact evidence references, then resume the same owner. If it requires Atlas-state inspection, semantic inference, new authority, unavailable evidence, or unavailable handle, ask the user or stop.
- `blocked`: stop or invoke only the selected owner's already-authorized recovery. Partial/unknown effects remain owner-recovery bound; they are never generic retries.
- `framework-defect`: present one short batched issue/effect summary and the shared guardrail's separately approved `dev-ask` Route Overview. No engineering stage starts under Atlas approval; do not create a local defect queue, receipt stub, or retry bypass.

Mixed outcomes use this exact precedence: `partial|unknown effect → blocked`; otherwise proven product defect → `framework-defect`; otherwise unresolved user choice → `needs-user`; otherwise eligible narrow Orchestrator guidance → `needs-guidance`; otherwise any blocker → `blocked`; otherwise all-terminal/no-commit no-write → `no-write`; otherwise `completed`. Independent siblings continue only when the selected owner already declares them safe; shared assumptions or ambiguous effects stop the affected cone. Return all completed and blocked siblings together in the one aggregate result.

## Same-session Engineering Cycle escalation

When a validated result is a safe-effect `framework-defect`, or is the exact blocked recovery-defect tuple, the Atlas Orchestrator performs only this escalation boundary:

1. Present one compact batched issue/effect summary grouped by owning contract and exact signature. Include expected versus observed behavior, the already-run reproduction, the current or changed falsifiable hypothesis, affected and continuing branches, and exact completed, committed, or no-write effects. Do not reproduce semantic packets, inspect Atlas state, or infer missing evidence.
2. Render the existing `dev-ask` Route Overview exactly, with no renamed or added field:

   ```markdown
   Goal: <one-sentence interpretation>
   Route: <ordered stage owners or `direct answer`>
   Why: <decisive routing facts, assurance selection evidence or disqualifiers, and included/skipped nontrivial stages>
   Artifacts: <expected durable outputs or `none`>
   Gates: <known human, destructive, scope, or capability stops; direct answers use `none`>
   Execution: <`one owner` | `small local batch` | `full orchestration`; assurance: <`compact` | `standard` | `high-consequence`>>
   First action: <next concrete operation>
   ```

3. Halt. Only a separate unambiguous approval tied to that unchanged seven-field engineering overview authorizes diagnosis or mutation. Atlas approval authorizes no engineering stage, fix, bound-instance write, or receipt.
4. `dev-ask` and its existing lifecycle select requirements, diagnosis, specification, tickets, implementation, and assurance from evidence; `dev-implementation` owns repair attempts, smoke, verification, review, and curation. The Atlas Orchestrator does not choose a semantic fix, ingest engineering transcripts, create engineering task/state, or run a monolithic engineering coordinator.
5. Present one engineering route only when one authority and dependency shape safely owns every grouped defect. Otherwise present the one batched report and one human sequencing choice; never launch multiple routes automatically.

The Atlas Orchestrator consumes only a validated ephemeral Engineering Cycle Receipt produced by terminal current engineering evidence under the shared guardrail. It never constructs a receipt, defect queue, ledger, Handoff, mutation token, or persistent retry state. A receipt is accepted only for the globally next cycle and only when its target revisions, route/result revisions, outcome, and any required recovery proof remain current.

For a valid receipt, render exactly:

```text
Engineering Cycle <n>/3 <repaired|no-repair>; retrying the approved Atlas goal with current product revisions.
```

Then reclassify and live-check capability and current product revisions. Dispatch one fresh Workflow Owner Task without another Atlas approval only when the unchanged request, retained pre-route material answers, selected owner, mode, safety and authority conditions, and maximum logical write boundary equal the initial approved binding. The fresh binding uses `atlas_attempt` equal to the prior attempt plus one, `owner_turn:1`, current revisions, and compact prior-defect references. Never resume the old handle, reuse stale Semantic Worker packets, or reuse pre-engineering state.

If the request, material answers, owner, mode, logical boundary, safety condition, authority, or capability changed, invalidate the retry and require a new `/atlas-ask` overview and approval. A failed, blocked, inconclusive, stale, assurance-rejected, non-reconstructible, or otherwise non-receipted engineering route stops with no retry and cannot repeat under the same approval. A valid `repaired` or `no-repair` receipt consumes one cycle; three receipts permit the fourth Atlas attempt but never a fourth Engineering Cycle. Same-signature recurrence additionally requires a changed target revision or genuinely changed falsifiable hypothesis linked by `changed_from`; same target and hypothesis stops.

For the recovery-defect exception, engineering may touch only product recovery code/contracts and never the bound instance. A receipt and automatic retry additionally require terminal proof that a fresh owner can reconstruct the exact native recovery request from the unchanged request/material answers and existing durable owner state through authorized owner/façade reads; old target bytes, transaction IDs, projections, and recovery payloads are unavailable. Without that proof, stop after authorized engineering with the smallest owner-owned manual recovery condition.

Any redacted learning candidate remains non-authoritative and ephemeral: it changes no route and writes no memory, façade state, vault, run log, queue, ledger, or background state.


## Completion boundary

Return the selected Workflow Owner's compact current output through the strict aggregate result and do not add semantic synthesis, façade/vault work, owner advice, or a second coordinator. Routine validation and recovery remain owner-native. The same-session Engineering Cycle escalation above consumes only validated terminal receipts under the shared guardrail, applies equal-boundary retry and recurrence/cycle accounting, and never resumes a stale Task.
