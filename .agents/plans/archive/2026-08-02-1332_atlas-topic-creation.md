# Atomic topic create-or-confirm — implementation ticket plan

**Datetime**: 2026-08-02-1332
**Scope**: Product-side Atlas topic creation: the approved pure index owner, shared transaction extraction, façade operations, and the two owning skill callsites; development-only assurance and resumption of the existing blocked memory plan
**Summary**: Project approved revision `atlas-topic-create-r1` into a dependency-wired T1–T7 implementation graph. The graph adds deterministic topic planning and atomic create/recover façade operations while preserving source/route transaction bytes, existing workflow boundaries, and all stated no-write and no-migration limits.
**Status**: IN_PROGRESS

## Authority

- **Approved engineering specification**: `local://atlas-topic-creation-spec.md` snapshot `#6C8F`, revision `atlas-topic-create-r1`, state `APPROVED`, approved at `2026-08-02T13:32:43Z`.
- **Governing request bound by that specification**: `local://atlas-topic-creation-spec-input.md` snapshot `#BFCD`; it records the observed `/atlas-index` blocker that the exact multi-target topic write set had no applicable core transaction contract.
- **Specification-governing skills**: `skill://dev-specification` and `skill://dev-codebase-design`. This derivative ticket set is governed by `skill://dev-ticketing`; plan lifecycle and transport are governed by `rule://plan`, `rule://plan-impl-spec`, and `rule://plan-omp-transport`.
- **Approval evidence**: the human approved both resolved decisions bound to this revision: `Current insufficient shell` and `Index ops + shared transaction`; at `2026-08-02T14:21:42Z`, the human separately selected `Approve and execute` for this exact plan at SHA-256 `2f9b8fb2dfad37a84eacffff08d863e2bcdd3bf8204c29b1fdec3807d0154348`.
- **Canonical change order**: `.agents/ARCHITECTURE.md` → `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` and `.agents/skills/atlas-core/assets/research-library-templates.md` → `scripts/atlas_transaction.py`, `scripts/atlas_index.py`, and the façade/source adapters → `.agents/skills/atlas-index/SKILL.md` and `.agents/skills/atlas-research/SKILL.md` → the unchanged thin command stubs.
- **Current repository identities bound by the specification** (full-file SHA-256; an implementation executor must re-check the immutable target before changing it):
  - `.agents/ARCHITECTURE.md` — `0abb364fb01d576173cc4d757af03308f5efc7d154b8791aee53ac1dea9b2114`
  - `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — `725e60171174ee88b8f283069ed28532ca54a7d4b6a7571ad76ac4a26fb24b93`
  - `.agents/skills/atlas-core/assets/research-library-templates.md` — `67c4aab5afaa5d7c1ba8951943331cb5bff1c7fc7de0d609da1e599706dac197`
  - `.agents/skills/atlas-index/SKILL.md` — `9935cd91bc3692930c7d78cfa351806b4bfc4c682273647bbbb9db9966d3ad55`
  - `.agents/skills/atlas-research/SKILL.md` — `1210130dad044e4c651f016f66fb2af04a5e2a21422c7c483a09368f4c90529b`
  - `.agents/skills/atlas-answer/SKILL.md` — `a259552ffbd24e2618672e3dd0c7131ed553ff22217bc9aed951b77e2fff6468`
  - `.agents/commands/atlas-index.md` — `38f8605aeaa5651edde501b514703bdc8b479399505ba23d3f6e417352b518fe`
  - `.agents/commands/atlas-research.md` — `8d1bb04f5419dace26aa9e471640b420e0b0eb5ce36c737f53331cfffbab8bd3`
  - `scripts/atlas_tool.py` — `77742c397777c9cac95fcacee452c0fb800b06a3b5caea7001a410f224fe6afd`
  - `scripts/atlas_source.py` — `5cfdda3ab2c276c3954a34f6e9906b74388c51149089533e9d58ef0df96c89b6`
  - `scripts/atlas_state.py` — `09e19162f1c255148ffef2c1b5a3aab8cfb8cff2b578e4b714ca9f7a6e7fe8ca`
  - `scripts/atlas-instance.py` — `322996de8256ae7dd89ea380a0a4fa02c961d8ffcc83d765cfc336ac7944cc42`
- **Fixed resolved decisions**: a newly created topic is the current-but-insufficient initial snapshot: `status: active`, `coverage_state: insufficient`, `confidence: low`, `refresh_model: same-as-topic-creation`, `Freshness state: current`, zero dirty/pending/newest values, `Source watermark: 0`, blank `Last synthesized`, `last_researched` and subdomain `last_updated` equal to the explicit `created_on`, and a current-answer statement that no evidence-backed answer exists and acquisition/research is required. Creation creates no pass and does not synthesize evidence. Use exactly `index.create_topic`, `index.recover_topic`, `scripts/atlas_index.py`, and `scripts/atlas_transaction.py`; source/route callers migrate directly with no re-export or compatibility alias.
- **Authority limits**: exactly three mutation targets; no domain, subdomain, vocabulary/tag, `MANIFEST.md`, or `RELATIONS.md` creation; no caller-owned transaction choreography; no source/route transaction reuse for topic creation; no fallback host path; no schema/header/storage migration; no second registry backend; no research acquisition, model invocation, source artifact, relation edge, answer synthesis, hidden queue, deploy, or non-development write. The two known unrelated `SUBDOMAIN_TOPIC_MAP_DRIFT` findings and their unrelated entries are preserved byte-for-byte and are neither repaired nor treated as a requested-topic failure.

## Tasks

- [x] T1. Project canonical topic-creation contracts — Completed: 2026-08-02T14:26:17Z
- [x] T2. Extract shared transaction module compatibly — Completed: 2026-08-02T15:02:38Z
- [ ] T3. Implement deterministic topic planning
- [x] T4. Cut over topic-creation skill callsites — Completed: 2026-08-02T15:02:38Z
- [ ] T5. Integrate atomic index façade operations
- [ ] T6. Verify and review immutable implementation
- [ ] T7. Resume blocked agent-memory plan

## Execution intent

The completed implementation target is a provider-neutral version-1 façade that exposes `index.create_topic` and `index.recover_topic` only when the connector has the existing mutation capability, and otherwise fails closed with `MUTATION_UNAVAILABLE`. A pure index owner validates one semantic request against a complete registry/subdomain/topic byte snapshot, deterministically renders the exact three candidate outputs, and returns an internal plan or a compatible-existing confirmation. The façade binds full-byte revisions under one re-entrant connector mutation session, executes that plan through the extracted generic transaction module, validates the requested post-state before an `applied` terminal, and reports the standard envelope/receipt. Existing source/route records, IDs, target order, receipts, terminal placement, and recovery remain byte-identical. The checked-in topic-creation workflows call only the façade operations; thin commands remain dispatch-only.

This plan is ticketing authority only. It does not itself authorize a live Atlas write, instance synchronization, deploy, or any implementation. T5 smoke fixtures are isolated temporary fixtures; T6's sync/check is development-only and runs only after independent assurance. T7 resumes the prior plan's already-owned request and grants no new non-development authority.

## Fixed cross-ticket contract

Every ticket consumes the following immutable projection of `atlas-topic-create-r1`; none may reinterpret it.

### Façade envelope, capability, and errors

- Every public request remains exactly `{"version":1,"op":"<literal>","args":{…}}`. Every response remains exactly `{"version":1,"ok":true|false,"op":"<literal-or-null>","result":{},"findings":[]}` with sorted `{code,path,detail}` findings, canonical compact sorted-key UTF-8 JSON and one LF. Exit `0` means success/no-op, `2` deterministic rejection, and `3` binding/I/O/durability/conflict failure.
- Add `index.create_topic` and `index.recover_topic` to the sorted mutation-capable operation list. A connector lacking `conditional_replace` advertises only its safe read operations; either index mutation operation returns `MUTATION_UNAVAILABLE` and never falls back to a host path. No new top-level response field, CLI mode, or direct connector method is introduced.
- Deterministic owner findings use the exact families and paths from the specification: `INDEX_REQUEST_INVALID` at `args.<field>`; `REGISTRY_INVALID` at the owning registry; `SUBDOMAIN_INVALID` or `SUBDOMAIN_PROJECTION_INVALID` at the subdomain URI; `RELATED_TOPIC_UNKNOWN`/`RELATED_TOPIC_SELF` at the related-ID path; `TOPIC_ID_EXISTS`, `TOPIC_PATH_EXISTS`, `TOPIC_ORPHAN`, or `TOPIC_COMPATIBILITY_CONFLICT` at the conflicting topic URI/row; `TOPIC_RENDER_INVALID` at the candidate topic URI; `REVISION_STALE` at the changed target URI; and `TARGET_NOT_ALLOWED` at the target path. Details contain no timestamps, host paths, or model prose. Existing binding/connector/I/O/durability/manual codes and exit semantics remain `BINDING_INVALID`, `MUTATION_UNAVAILABLE`, `IO_FAILURE`, `TRANSACTION_RECOVERABLE`, `TRANSACTION_RECORD_INVALID`, `MANUAL_CONFLICT`, `TRANSACTION_UNKNOWN`, and `SUCCESSOR_TERMINAL_INELIGIBLE`.

### Exact create request and pure owner seam

- `index.create_topic.args` has exactly these keys, with no unknown or missing key:
  ```json
  {
    "version": 1,
    "topic_id": "<existing Atlas topic-id grammar>",
    "topic_path": "vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md",
    "domain": "<existing domain id>",
    "subdomain": "<existing subdomain id>",
    "canonical_title": "<nonempty title>",
    "aliases": [],
    "include_terms": [],
    "exclude_terms": [],
    "related_topic_ids": [],
    "status": "active",
    "coverage_state": "insufficient",
    "confidence": "low",
    "refresh_model": "same-as-topic-creation",
    "created_on": "YYYY-MM-DD"
  }
  ```
- Scalar strings are strict UTF-8, trimmed, and nonempty where shown. Existing Atlas ID/path normalization rules apply; `topic_path` is under the supplied domain/subdomain, has no query, fragment, or traversal, and names exactly `INDEX.md`. Arrays are unique, trimmed, and canonical UTF-8 byte ordered; an unnormalized request is rejected, not silently rewritten. Related IDs already exist, exclude `topic_id`, and do not imply a symmetric relation. Fixed constants are validated exactly. `created_on` is one explicit UTC date supplied by the checked-in skill in the façade request and bound into the receipt; no hidden renderer clock is permitted. The owner computes `sha256(canonical_json(args))`, with sorted keys, compact separators, UTF-8, and one LF only when persisted.
- The pure internal interface is exactly:
  ```text
  prepare_topic(
      request,
      manifest_text,
      topics_text,
      relations_text,
      subdomain_text,
      topic_text_or_missing
  ) -> TopicConfirmation | TopicPlan | Findings
  ```
  The owner receives semantic request data and bytes, never connector revisions, caller target bytes, CAS instructions, expected revisions, or rollback steps. `TopicPlan` contains the canonical request hash, immutable event data, exactly three ordered target paths, output bytes, and owner-specific candidate/post-validation inputs; it does not contain connector revisions. Identical inputs yield identical findings, bytes, order, and hashes.

### Targets, rendering, confirmation, and receipt

- Candidate targets are exactly and only, in order: (1) `vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md` with owner input `missing`; (2) the existing subdomain `vault://atlas/summaries/research/<domain>/<subdomain>/INDEX.md`; (3) `vault://atlas/summaries/registry/TOPICS.md`. No `MANIFEST.md` or `RELATIONS.md` bytes are mutation candidates. The façade binds `missing` and the two existing full-byte input revisions after pure planning and immediately before intent.
- The topic candidate follows `TOPIC-INDEX.md` exactly: schema version `1`, `note_type: research-topic`, `managed_by: atlas`, requested identity/scope/aliases/status/coverage/confidence, `freshness_window: P90D`, and every managed section. Its initial current-answer section says that no evidence-backed answer exists and acquisition/research is required; no pass, evidence-map row, relation edge, optional split file, source artifact, or unsupported answer is created.
- The subdomain candidate changes only managed projections required for the requested topic, adds the requested topic-map entry, derives coverage/freshness/stale/weak/related values from the candidate topic and canonical row, and preserves unrelated topic-map/projection entries plus every unmanaged byte, newline style, and final-newline state. It does not repair or normalize the two baseline drift entries.
- The `TOPICS.md` candidate adds one canonical row with the request identity and terms; initial derived fields are `Freshness state=current`, `Dirty count=0`, blank `Pending edge IDs`, blank `Newest pending source seq`, blank `Last synthesized`, `Source watermark=0`, and `Refresh model=same-as-topic-creation`. It preserves non-table bytes and input newline/final-newline convention. `last_researched` and subdomain `last_updated` equal `created_on`.
- If exact topic ID and path already exist, validate the topic and matching projection and compare exact structural identity: ID/path, domain/subdomain, canonical title, aliases, include terms, exclude terms, related IDs and ordering, status, and refresh model. A compatible result is `state: "confirmed"` with the three logical paths and current full-byte revisions, `transaction: null`, `receipt: null`, and successful validation; it performs no transaction or write and preserves answer, coverage, confidence, freshness/cache values, and all dates. An ID at another path, path for another ID, orphan file/row, or mismatched projection is a deterministic conflict, never confirmation.
- A successful create returns `ok:true`, `state: "created"`, the three paths, three lowercase `sha256:` output revisions, immutable transaction `event_uri`, `intent_uri`, existing phase URIs, and terminal URI, the specified receipt (`request_sha256`, `created_on`, `<16 hex>-a<6 digits>` transaction ID, base ID, attempt, predecessor, status `applied`, exactly three target entries in topic → subdomain → registry order, terminal hash, and target revisions), and `validation: {"ok": true, "findings": []}`. All revisions and acknowledgements come from connector rereads; callers never calculate them. The owner post-validator proves the requested projection and unchanged baseline findings, not globally clean subdomain state.

### Recovery and transaction contract

- `index.recover_topic.args` has exactly:
  ```json
  {
    "version": 1,
    "transaction_id": "<attempt transaction id>",
    "request": {"<the exact original index.create_topic args object>"}
  }
  ```
  The request is byte-identical canonical JSON to the immutable event/intent and contains no target bytes, revisions, CAS fields, or rollback instructions. The ID comes from the recoverable finding or prior receipt.
- Recovery verifies immutable event, request hash, intent, paths, input/output hashes, backups, prepared record, and terminal records before touching a target; rereads every target under one session and classifies `input`, `output`, or `other`. All output is `applied`; all input without preparation is `aborted`; all input after preparation is `rolled-back`. Mixed state restores only output targets in reverse order: `TOPICS.md`, then subdomain, then deletion of the exclusively created topic, and verifies all input revisions. `other`, malformed/colliding records, missing backups, changed request, or a second successor yields `MANUAL_CONFLICT`/`TRANSACTION_RECORD_INVALID` with no force-write or substitution.
- Recovery returns terminal status, the same paths/revisions, immutable transaction URIs, the standard receipt, and `successor_eligible`; it only reports eligibility. If attempt zero is `aborted` or `rolled-back`, an exact original `index.create_topic` replay executes only the one eligible identical attempt-one with the same request and exact bytes. No later successor, rebased input, substituted bytes, or changed request is legal. Replay after applied state is a confirmation no-op.
- Extracted `scripts/atlas_transaction.py` owns only generic canonical JSON/hashing, immutable event/intent/backup/prepared/progress/terminal records, connector-port writes/rereads, input/output classification, qualified reverse rollback, and one-successor classification. Its internal plan API is owner-parametric: `TransactionTarget`, `TransactionPlan`, `ConnectorPort`, `build_transaction_plan`, `build_successor_plan`, `execute_transaction`, and `recover_transaction` accept an owner-supplied target allowlist/rank and deterministic identity binding; execution accepts the owner post-validator before an `applied` terminal. Source/route supplies the existing identity and rank; topic creation supplies its own approved rank and event identity. No caller-owned topic transaction or special rollback branch exists.
- One re-entrant connector mutation session spans complete preflight, event/intent binding, target preconditions, execution/recovery/successor, post-state validation, and reread. Resolve only logical `vault://atlas/…` paths with descriptor-relative no-follow traversal; reject traversal, query/fragment, credentials, symlink, special-file, invalid-UTF-8, and ambiguous profile inputs. Profiles without process-shared locking, full-byte revisions, strict CAS, durable replacement, and qualified rollback deletion are read-only. Never force-write, rebase, substitute candidate bytes, or infer state from progress.
- Transaction phase is validate complete state → render/validate candidates → bind input revisions → exclusive-create event and intent → persist backups/prepared → apply topic, subdomain, registry with durable CAS and exact reread → persist progress → owner post-validator plus complete registry validation → one terminal record/receipt. Failure before intent creates no record; failure after intent returns a recoverable immutable identity. Rollback restores only the two existing inputs and deletes only a newly created topic whose bytes equal transaction output. Source/route default validator and terminal bytes/placement remain unchanged.

# T1 — Project canonical topic-creation contracts

## Authority

- `local://atlas-topic-creation-spec.md#6C8F`, `atlas-topic-create-r1`, including both approved resolved decisions.
- T1 may consume the governing request and current identities above, but may not change the approved product contract.

## Objective

- Project the approved topic-creation interfaces, ownership boundaries, target set, template semantics, transaction invariants, and preservation limits into the canonical architecture/core/template contract surfaces so T2, T3, and T4 share one exact immutable contract.

## Ownership

- **May read**: `.agents/ARCHITECTURE.md`; `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`; `.agents/skills/atlas-core/assets/research-library-templates.md`; the approved specification and its bound request.
- **May change or produce**: only the relevant architecture/framework-boundary clauses in `.agents/ARCHITECTURE.md`, the registry/reducer/facade/transaction clauses in `markdown-registry-contracts.md`, and the subdomain/topic managed-section/template clauses in `research-library-templates.md`; a T1 completion handoff that names the resulting file revisions and the exact fixed interface checklist.
- **Must not change**: `scripts/**`, tests, `.agents/skills/atlas-index/**`, `.agents/skills/atlas-research/**`, either thin command, Atlas state, instance state, any write set, or any governing specification revision. Do not add a topic event to `atlas_state.py` or choose a new backend, migration, retry, or fallback.
- **Fixed shared interfaces/state**: the entire `Fixed cross-ticket contract` above, including `prepare_topic`, `index.create_topic`, `index.recover_topic`, exact constants, initial shell, three target order, generic transaction seam, source/route compatibility, post-validator placement, and all no-go boundaries.

## Dependencies

- **Blocking**: none; T1 is the graph root.
- **Handoff consumed by**: T2, T3, and T4, each from the same completed T1 contract revision/checklist. No sibling may infer contract text from another sibling's edits.

## Acceptance

- The three named canonical contract files project the approved operation/module names, exactly three target paths/order, request/recovery fields and constants, canonical request hash, compatible confirmation semantics, create receipt, stable findings, transaction phase/recovery/successor policy, and connector/security guarantees without adding behavior.
- The initial shell and freshness decision is represented exactly: active/insufficient/low/same-as-topic-creation, current, zero dirty/pending/newest, source watermark zero, blank last synthesized, creation date propagation, and no evidence/pass/answer synthesis.
- The ownership and preservation boundaries explicitly keep index semantics/rendering/planning in the index owner, byte I/O/CAS/durability/deletion in the connector, provenance/application/recovery/successor in the generic transaction module, and user authority/research decisions in workflows.
- The two known unrelated `SUBDOMAIN_TOPIC_MAP_DRIFT` entries are explicitly preserved baseline; no domain/subdomain creation, registry migration, relation/vocabulary/source/answer effect, or command thickening is introduced.
- T1 leaves no material choice for T2–T5: target rank/identity are owner-supplied internal transaction inputs, the owner post-validator precedes `applied`, and source/route callers migrate directly with no alias/re-export.

## Verification

- **Scenario**: compare each changed clause against snapshot `#6C8F` and the resolved-decision text, then inspect the three file revisions for only the approved projection.
- **Environment**: product package checkout at the specification-bound identities; no connector or Atlas instance mutation.
- **Proof class/evidence**: specification-to-contract review with an exact clause checklist, changed-file revision identifiers, and a no-drift/non-goal report. A changed target set, operation name, shell meaning, rollback rule, or source/route byte rule is a stop requiring a new specification revision, not a T1 repair.

## Execution policy

- T1 is one owner and one sequential contract projection; internal editorial decomposition is allowed only if every edit is checked against `#6C8F`.
- No implementation, tests, formatter, linter, façade invocation, instance sync, or Atlas state access is part of T1. T1 must complete before T2/T3/T4 start.
- The material decision gate is exact authority parity. No fallback or reinterpretation is permitted.

## Completion output

- Return the three canonical contract-file revisions and a fixed-interface checklist covering every item in `Fixed cross-ticket contract`, plus the no-drift evidence.
- **Observed T1 result:** architecture `5b02447c118767a649cf843f107cb4feb91c08870866e951059bd7f78a87f56f`; registry contract `1872441d69feb4eb298f73897af20e740a1468885c4a4210fb507341ea55ec19`; research templates `ac0af9ddab1a1269efb5aed804e2d05b4237647b41e1edc49a1969783361f5f7`. The projection fixes the request/operation/module seam, initial shell, exact target order, generic transaction ownership, compatible confirmation, recovery/successor limits, logical-connector boundary, unchanged source/route contract, and all no-go effects.
- Receiver: T2, T3, and T4 in parallel; parent `dev-ask` retains the authority handoff.

# T2 — Extract shared transaction module compatibly

## Authority

- `atlas-topic-create-r1` and the completed T1 contract handoff.
- Existing source/route record layout, old-record loading behavior, target rank, identity formula, and terminal placement are immutable compatibility baselines.

## Objective

- Move only generic transaction mechanics into `scripts/atlas_transaction.py`, migrate source/route callers directly to it, and demonstrate byte-identical source/route records, IDs, receipts, terminal behavior, and old-record recovery.

## Ownership

- **May read**: the transaction block in `scripts/atlas_source.py` (`canonical_json`, `sha256`, `TransactionTarget`, `TransactionPlan`, `ConnectorPort`, target ranking, `build_transaction_plan`, verified record helpers, `build_successor_plan`, `recover_transaction`, and `execute_transaction`); source/route adapters in `scripts/atlas_tool.py` (`_Port`, `_rank`, `_targets`, `_bind`, `_plan`, `_store_event`, `_receipt`, `_tx_result`, `_load_plan`, `_tx_execute`, `_tx_recover`, `_tx_successor`); `scripts/atlas_state.py`'s `plan_transaction_recovery`; `tests/test_atlas_source.py`, `tests/test_atlas_tool.py`, and connector fixtures.
- **May change or produce**: new `scripts/atlas_transaction.py` containing the generic mechanics and owner-parametric target-rank/allowlist, identity binding, and pre-terminal post-validator seam; direct source/route imports and narrowly required adapters in `scripts/atlas_source.py` and `scripts/atlas_tool.py`; source/route regression fixtures/assertions in `tests/test_atlas_source.py` and `tests/test_atlas_tool.py`.
- **Must not change**: topic semantics, `scripts/atlas_index.py`, the new index façade operations, workflow skills/commands, registry/template meaning, source artifact rendering, connector contract, existing record bytes, or any instance/Atlas state. Do not leave a wrapper, alias, re-export, deprecated import path, second backend, or source/route transaction reuse hook for topic creation.
- **Fixed shared interfaces/state**: `scripts/atlas_transaction.py` owns `canonical_json`, `sha256`, `TransactionTarget`, `TransactionPlan`, `ConnectorPort`, `build_transaction_plan`, `build_successor_plan`, `execute_transaction`, and `recover_transaction`. The plan builder rejects targets outside the owner-supplied rank/allowlist, preserves the owner-supplied identity binding, and retains attempt/predecessor invariants. Execution invokes an optional owner post-validator after target rereads/progress and before an `applied` terminal; omitted/default source/route behavior remains byte-identical. Direct callers pass source/route's current event record, target order, transaction root, and identity fields unchanged.

## Dependencies

- **Blocking**: T1 — its completed contract revision/checklist is the sole upstream interface authority.
- **Handoff produced**: `T2-transaction-compatibility` consisting of the new module revision, direct-import migration revision, and before/after fixture comparison evidence. T5 must consume this handoff and must not re-open source/route semantics.

## Acceptance

- All generic mechanics named by the specification are in `scripts/atlas_transaction.py`; `scripts/atlas_source.py` no longer owns or re-exports them, and source/route callers import the shared module directly.
- Owner-supplied target allowlist/rank and deterministic identity binding are explicit internal inputs. Topic creation can later provide its topic → subdomain → registry rank without source/route constants leaking across the seam.
- The source/route legacy identity formula, event hash/promotion hashes/source ID binding, target order (source artifact → `RELATIONS.md` → `TOPICS.md` → `MANIFEST.md`), event/intent/backup/prepared/progress/terminal JSON, transaction IDs, receipts, terminal placement/bytes, connector rereads, and one-successor rule are unchanged byte-for-byte.
- Current source/route records and old records load without conversion. Recovery still classifies reread input/output/other, performs qualified reverse rollback, detects manual conflict, and permits only the one identical successor from attempt-zero `aborted` or `rolled-back`.
- Source/route's existing validator/preflight behavior remains in its old ownership location; the new post-validator seam does not alter the default path. No topic target, topic event, or topic-specific branch is added here.

## Verification

- **Scenario**: run the existing source/route request-envelope, event-record, target-order, transaction-ID, receipt-hash, terminal-record, fault/recovery, old-record-loading, effect, and refresh fixtures once against the pre-extraction reference capture and once against the extracted implementation; compare complete bytes and sorted JSON, not only parsed fields.
- **Environment**: isolated connector/temp fixture with instrumented reads/writes; no bound-instance mutation. Use `tests/test_atlas_source.py` transaction fixtures and the existing `AtlasToolTests` transaction/effect/refresh methods in `tests/test_atlas_tool.py`.
- **Proof class/evidence**: source/route regression seam evidence: byte-for-byte event/intent/backup/prepared/progress/terminal records, IDs, receipts, target order, terminal placement, and recovery outcomes, including an old-record recovery case. Any byte difference blocks T2 and is not repaired by an alias or conversion.

## Execution policy

- T2 is independently runnable after T1 and owns only the shared transaction extraction plus source/route migration. It may internally split mechanical extraction and fixture comparison but must present one compatibility handoff.
- T2 runs before T5; T5 is the only consumer allowed to add index-specific façade wiring. T2 must not wait on T3 or T4.
- Decision gate: any source/route byte difference, missing old-record compatibility, or need for a compatibility alias stops for a new design/specification decision.

## Completion output

- Return `scripts/atlas_transaction.py`, direct source/route import/adapters, and regression evidence proving byte identity and old-record recovery.
- Receiver: T5 as one immutable lineage; parent `dev-ask` receives the compatibility handoff and proof.

# T3 — Implement deterministic topic planning

## Authority

- `atlas-topic-create-r1`, the T1 canonical contract handoff, the existing state owner in `scripts/atlas_state.py`, and `research-library-templates.md` as projected by T1.

## Objective

- Implement the pure `scripts/atlas_index.py` owner that validates one semantic topic request and byte snapshot, deterministically produces a confirmation or exact three-target plan, and proves request/compatibility/rendering behavior without connector mutation.

## Ownership

- **May read**: `scripts/atlas_state.py` (`validate_documents`, `reduce_event`, `plan_transaction_recovery` only as existing reference boundaries; no topic event is added), `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`, `.agents/skills/atlas-core/assets/research-library-templates.md`, the T1 handoff, and pure test/fixture conventions in `tests/test_atlas_state.py` and `tests/test_atlas_tool.py`.
- **May change or produce**: new `scripts/atlas_index.py` with `prepare_topic`, internal immutable `TopicPlan`/`TopicConfirmation` values, request/identity validation, compatibility checks, deterministic renderers, requested-projection validator inputs, and pure unit/property fixtures in new `tests/test_atlas_index.py` (plus narrowly required pure fixtures only).
- **Must not change**: `scripts/atlas_tool.py`, `scripts/atlas_transaction.py`, `scripts/atlas_source.py`, `scripts/atlas_state.py`, workflows/commands, connector methods, Atlas state, or any source/research behavior. The module imports no connector and performs no reads/writes/CAS/rollback.
- **Fixed shared interfaces/state**: exactly `prepare_topic(request, manifest_text, topics_text, relations_text, subdomain_text, topic_text_or_missing) -> TopicConfirmation | TopicPlan | Findings`; request fields/constants/hash; exact topic/subdomain/registry output semantics; exact finding families; baseline drift preservation; and internal `TopicPlan` contents from `Fixed cross-ticket contract`.

## Dependencies

- **Blocking**: T1 — consume only its completed canonical contract revision/checklist.
- **Handoff produced**: `T3-index-plan-contract` consisting of `scripts/atlas_index.py`, pure fixtures/tests, deterministic byte/hash evidence, and the exact internal plan/post-validator value contract. T5 must consume this plan contract without adding caller-supplied target material.

## Acceptance

- Valid normalized requests produce one canonical request hash, exactly topic → subdomain → `TOPICS.md` target order, deterministic output bytes and hashes, and no public input for target bytes, revisions, CAS, or rollback. Unordered/duplicate/whitespace arrays, invalid IDs/path/date/constants, unknown/self related IDs, and unnormalized values yield stable sorted `INDEX_REQUEST_INVALID`, `RELATED_TOPIC_UNKNOWN`, or `RELATED_TOPIC_SELF` findings with no plan.
- The complete registry bundle is validated with the existing state owner before planning; missing subdomain, domain/subdomain mismatch, invalid managed markers/frontmatter, invalid requested projection, orphan row/file, conflicting ID/path, and any invalid finding outside the two explicitly preserved baseline drifts produce the specified deterministic finding and no plan. The owner neither creates a domain/subdomain nor repairs unrelated projection entries.
- An absent topic yields an internal plan. An exact existing compatible topic yields `confirmed`, current paths/revisions, null transaction/receipt, successful validation, no target changes, and preserves existing answer/coverage/confidence/freshness/cache/dates. Mismatched row/frontmatter/scope/terms/related ordering/status/refresh model/projection yields `TOPIC_COMPATIBILITY_CONFLICT` before intent.
- Topic rendering follows `TOPIC-INDEX.md` exactly with the approved active/insufficient/low/current shell, `P90D`, date propagation, managed sections, and no evidence/pass/source/relation/answer fabrication. `TOPICS.md` rendering adds the exact canonical initial derived fields and preserves non-table bytes. Subdomain rendering updates only requested managed projections and preserves unrelated/unmanaged bytes, LF/CRLF behavior, and final-newline state, including unrelated `SUBDOMAIN_TOPIC_MAP_DRIFT` entries.
- The returned owner post-state validator inputs prove the requested projection and unchanged baseline findings without requiring a globally clean subdomain. The plan carries no connector revision and is safe for T5 to bind under a held mutation session.

## Verification

- **Scenario**: deterministic unit/property cases for valid normalized input, all request/registry/subdomain/orphan/conflict rejection families, absent and compatible-existing topic cases, each structural compatibility mismatch, baseline drift, and every renderer preservation case.
- **Environment**: pure Python tests with in-memory text snapshots; no connector, filesystem, `vault://` read, CAS, transaction record, or Atlas effect.
- **Proof class/evidence**: (1) canonical request/hash/target-order deterministic proof; (2) table-driven compatibility proof; and (3) byte-snapshot/hash proof over LF, CRLF, final-newline, managed/unmanaged, requested/unrelated projection, initial shell, and preserved drift cases. Tests must fail on a plausible wrong byte, changed ordering, accidental confirmation, hidden date, or plan containing caller target material.

## Execution policy

- T3 is independently runnable after T1 and runs in parallel with T2 and T4. It may internally split pure validation, compatibility, and rendering fixtures, but one owner retains the complete `prepare_topic` semantic boundary.
- No façade integration is needed for this ticket; T5 is the first ticket allowed to bind revisions or mutate a connector.
- Decision gate: any need for connector input, caller-supplied bytes/revisions, a topic event in `atlas_state.py`, or a changed target/initial shell stops for a new specification revision.

## Completion output

- Return `scripts/atlas_index.py`, pure tests/fixtures, and deterministic request/compatibility/rendering evidence plus the immutable `T3-index-plan-contract` handoff.
- Receiver: T5 as one immutable lineage; parent `dev-ask` receives the pure-owner proof.

# T4 — Cut over topic-creation skill callsites

## Authority

- `atlas-topic-create-r1`, T1's canonical contract handoff, `.agents/skills/atlas-index/SKILL.md`, `.agents/skills/atlas-research/SKILL.md`, and the two thin command identities.

## Objective

- Change only the owning skill procedures so approved absent-topic creation and named recovery use the new façade operations, while preserving existing-topic research/update behavior and leaving command stubs thin and unchanged.

## Ownership

- **May read**: `.agents/skills/atlas-index/SKILL.md`, `.agents/skills/atlas-research/SKILL.md`, `.agents/commands/atlas-index.md`, `.agents/commands/atlas-research.md`, and the T1 handoff.
- **May change or produce**: only the topic-creation/recovery callsite sections of `.agents/skills/atlas-index/SKILL.md` and the absent-topic branch of `.agents/skills/atlas-research/SKILL.md`; a callsite/command identity handoff to T5.
- **Must not change**: `.agents/commands/atlas-index.md`, `.agents/commands/atlas-research.md`, any scripts/tests/registry/template/instance state, existing-topic research/update/refresh/answer behavior, or any direct CAS/transaction implementation. Do not thicken the thin commands.
- **Fixed shared interfaces/state**: `atlas-index` invokes only `index.create_topic` for an approved absent-topic request and `index.recover_topic` for a named recoverable attempt; the checked-in skill supplies one explicit UTC `created_on` in the façade request and receipt, while raw slash arguments need not contain it. `atlas-research` invokes `index.create_topic` only for absent-topic creation and retains its current research/update seam for an existing topic. Neither skill constructs Markdown, computes hashes/revisions, invokes CAS, orders targets, or rolls back.

## Dependencies

- **Blocking**: T1 — consume its canonical contract handoff; T4 is independent of T2 and T3.
- **Handoff produced**: `T4-skill-callsite-contract` consisting of the two skill revisions, command byte-identity evidence, and a callsite map showing operation, request-date, receipt, recovery, and existing-topic branches. T5 consumes it after T2 and T3 arrive.

## Acceptance

- The approved absent-topic `/atlas-index` path constructs the exact semantic request and calls only `index.create_topic`; a named recoverable transaction calls only `index.recover_topic` with the exact original request and attempt transaction ID. It reports façade receipts/findings without recreating transaction choreography.
- The absent-topic `/atlas-research` path calls only `index.create_topic`; existing-topic research/update behavior and answer freshness gates remain unchanged. Acquisition cannot create domains, subdomains, aliases, tags, or topics as a side effect.
- Both skills remain façade-first and use logical `vault://atlas/…` identities. They do not hand-author Markdown, calculate revisions, call `vault.conditional_replace` for this capability, call source/route transaction operations, order targets, or implement rollback.
- The two command files remain byte-identical to their T1-bound identities and continue to dispatch only to their declared skills. No new CLI mode, helper, or command-side authority appears.
- The workflow output still reports explicit authority, named operation/receipt, exact paths/rows, and conflicts/blockers; a failure or nonterminal receipt stops before wider action and uses only the approved recovery operation.

## Verification

- **Scenario**: inspect the checked-in callsite paths and exercise the workflow contract with a static/mock façade boundary that records operation names and request shape; verify absent and existing-topic branches separately and confirm the named recovery path carries the original request.
- **Environment**: checked-in skill/command files and non-mutating callsite harness; no Atlas state or connector write.
- **Proof class/evidence**: workflow integration contract evidence: operation trace contains only `index.create_topic`/`index.recover_topic` for this capability, explicit `created_on` is present in the façade request, no direct CAS/choreography is reachable, and command-file SHA-256 remains the bound identity. The independent T6 assurance repeats this proof and owns the development sync/check gate; that is verification of T4's criterion, not a second workflow owner.

## Execution policy

- T4 is independently runnable after T1 and runs in parallel with T2 and T3. It may not wait for façade implementation; its contract trace uses the fixed operation names and request shape.
- No skill invocation against a bound instance is authorized by T4. T5 owns isolated integrated smoke; T6 owns approved development-only sync/check after independent assurance.
- Decision gate: a need to change a command, existing-topic research seam, direct-I/O fallback, or raw-argument contract stops for human/specification authority.

## Completion output

- Return the two skill revisions, unchanged command identity evidence, and the `T4-skill-callsite-contract` handoff.
- Receiver: T5 after T2 and T3; parent `dev-ask` receives the callsite proof.

# T5 — Integrate atomic index façade operations

## Authority

- `atlas-topic-create-r1`, T1's canonical contract, and all three required upstream handoffs: `T2-transaction-compatibility`, `T3-index-plan-contract`, and `T4-skill-callsite-contract`.
- T5 is the neutral fan-in owner. Arrival order of T2, T3, and T4 has no semantic precedence; all three immutable lineages are required before integration.

## Objective

- Add the two façade operations and their capability/dispatch, binding, generic transaction, post-validation, receipt, recovery, replay, and isolated smoke behavior end to end without changing any non-approved target or bound instance.

## Ownership

- **May read**: `scripts/atlas_tool.py` (`OPERATIONS`, `_READ_ONLY_OPERATIONS`, `_mutations`, `_connector`, `_capabilities`, `_Port`, `_dispatch`, `_pure`, `capabilities`, `execute`, `_exception`, and migrated source/route transaction adapters); `scripts/atlas_index.py`'s `prepare_topic`/plan/confirmation values; `scripts/atlas_transaction.py`'s generic plan/execute/recover/successor API; `scripts/atlas_state.py` `validate_documents`; T2/T3/T4 handoffs; connector interfaces and templates.
- **May change or produce**: façade operation registry/capability reporting and index dispatch/handlers in `scripts/atlas_tool.py`; narrowly required façade-to-owner/transaction adapters; integration and fault-injection tests in `tests/test_atlas_tool.py` and any temporary isolated fixture harness needed for the target seams. T5 may consume but must not redesign the T2/T3/T4 owned modules/contracts.
- **Must not change**: `MANIFEST.md`/`RELATIONS.md` candidate bytes, source/route semantics, `atlas_state.py` event ownership, workflows/commands beyond the T4 handoff, answer/refresh behavior, connector public methods, target set/order, schema/header/storage, host-path fallback, instance/Atlas state, or any non-development write. No caller-owned transaction, force-write, alternate helper, bespoke rollback, retry, or hidden queue.
- **Fixed shared interfaces/state**: exact envelope/request/recovery/confirmation/create receipt; one connector mutation session; owner receives full-byte snapshots and returns byte-only plan; façade binds revisions after plan; generic transaction module executes topic rank/identity and owner post-validator; complete registry validation plus requested post-state validator precede `applied`; transaction provenance is under `.atlas/transactions` only.

## Dependencies

- **Blocking**: T2, T3, and T4. T5 must name and consume all three handoffs; it may not infer missing content from the repository or choose a semantic winner.
- **Handoff produced**: `T5-atomic-index-implementation` consisting of the immutable integrated target, targeted test output, instrumented connector evidence, fault/recovery/replay receipts, and isolated fixture cleanup evidence. T6 consumes this one immutable target; T7 consumes T6's assurance plus the prior-plan resume authority.

## Acceptance

- `capabilities()` advertises exactly the two new mutation operations in sorted order when `conditional_replace` is available; a read-only connector omits both, and both calls return `MUTATION_UNAVAILABLE` without host-path fallback. The existing version-1 response/envelope/exit semantics remain exact.
- `index.create_topic` accepts exactly the approved args, routes to `atlas_index.prepare_topic`, reads the complete registry bundle plus existing subdomain and missing-or-existing topic through the configured logical connector, and never accepts caller target bytes/revisions/CAS/rollback. A pure compatible confirmation returns no transaction/write and preserves all existing answer/cache/date values.
- A create holds one re-entrant mutation session from preflight through event/intent, all input binding, generic execution/recovery, owner post-validation, complete registry validation, and reread. It binds every existing target's full-byte revision immediately before intent, writes exactly topic → subdomain → `TOPICS.md`, persists immutable event/intent/backups/prepared/progress/terminal records, rereads exact output revisions, and returns the specified paths/revisions/URIs/receipt/validation. Instrumentation proves no fourth target document is read for mutation or written.
- The owner-specific candidate/post-state validator runs before an `applied` terminal and proves the requested projection plus unchanged baseline drift; a post-validation failure is recoverable and never returns `created` from partial state. Complete registry validation remains required and does not demand a globally clean subdomain.
- `index.recover_topic` accepts exactly the attempt ID and byte-identical original request, verifies all immutable records/backups/hashes before target access, rereads all three targets under one session, classifies input/output/other, and returns standard terminal paths/revisions/URIs/receipt plus `successor_eligible`. It performs qualified reverse rollback only; it never runs a successor itself.
- Mixed input/output restores only output targets in `TOPICS.md` → subdomain → exclusive new-topic deletion order and verifies all input revisions. Drift, malformed/colliding record, changed request, missing backup, second successor, or unknown transaction returns the specified stable conflict/record finding without force-write or substitution. Attempt-zero `aborted`/`rolled-back` permits only one exact identical attempt-one replay; applied replay is a confirmed no-op.
- Stable owner and façade findings map exactly to the fixed families/paths; recoverable failures identify immutable intent URI and transaction ID and do not claim success. Binding, connector, durability, manual-conflict, and successor exit behavior remains unchanged.
- Security and operational boundaries hold: logical connector only, no traversal/query/fragment/credentials/symlink/special-file/invalid-UTF-8/ambiguous profile, read-only profile fail-closed, qualified deletion only, exactly three target documents plus transaction provenance, no relation/source/vocabulary/pass/acquisition/answer effect.
- Isolated temporary-fixture smoke and all targeted tests exercise capability, successful mutation, preflight/CAS, post-validation, conflict/recovery, replay, and the T2/T3/T4 contracts. Temporary fixtures are removed and no fixture remains under `vault://atlas/`; T5 does not run development sync/check or mutate the bound instance.

## Verification

- **Scenario**: use an instrumented local connector/temp profile to run one valid create, compatible confirmation, read-only capability calls, stale subdomain/registry preflight, injected failure after each target application, post-validation fault, mixed recovery, output drift, malformed/colliding records, changed request, missing backup, second successor, applied replay, and sole identical attempt-one replay. Exercise the exact CLI envelope and inspect receipts/findings.
- **Environment**: isolated connector fixture only; no non-development profile and no bound-instance write. Track document-target reads/writes separately from transaction-record reads to prove no fourth mutation target.
- **Proof class/evidence**: connector integration and fault-injection evidence plus targeted test output, complete receipt/terminal bytes, reread revisions, operation capability lists, rollback bytes, successor eligibility, and fixture cleanup. T5 must run the thing, not only parse metadata, but it does not issue the T6 development sync/check.

## Execution policy

- T5 starts only after all three upstream lineages are present and integrates them neutrally. It owns the façade seam and integrated smoke; it may internally split handlers, tests, and fault adapters but no split may claim a second transaction/index authority.
- T5 is the first ticket allowed to connect the pure owner to a mutation connector, and it must use the extracted generic transaction module rather than source/route operations or a bespoke branch.
- Decision gates: any upstream handoff conflict, changed fixed contract, target-count/order change, need for non-dev/bound-instance write, missing owner post-validator, or source/route regression blocks integration and returns the immutable target to parent without repair.

## Completion output

- Return the immutable integrated implementation, all targeted test/smoke evidence, exact operation/receipt/recovery traces, instrumented no-fourth-target evidence, and fixture cleanup confirmation.
- Receiver: T6 for independent verification and review; parent `dev-ask` retains all three input lineages and T5's fan-in record.

### Attempt 1 verification handoff

- **Target:** `local://atlas-topic-t5-target.md#CEB2`; all 16 recorded SHA-256 identities were independently rechecked.
- **Verdict:** `NOT_VERIFIED` from `agent://VerifyAtomicTopicTarget`. T1-T4 and every exercised T5 criterion passed except the final-target post-intent durability path.
- **Observed blocker:** an injected `OSError` after the final `TOPICS.md` bytes were durably replaced caused generic one-shot recovery to return `applied`; `index.create_topic` then incorrectly returned `ok: true`, `state: created` instead of `TRANSACTION_RECOVERABLE`. Exact `index.recover_topic` subsequently returned `applied`.
- **Repair scope:** preserve generic source/route defaults and bytes while making the index owner opt into surfacing any recovered post-intent exception as `TRANSACTION_RECOVERABLE`; strengthen all three after-write assertions and no-fourth-target instrumentation. T5 remains open until a new immutable target passes independent verification.

### Attempt 2 immutable target

- **Target:** `local://atlas-topic-t5-target-r2.md#EC01`; only `scripts/atlas_transaction.py`, `scripts/atlas_tool.py`, and `tests/test_atlas_tool.py` changed from attempt 1.
- **Repair:** generic transaction execution gained an owner-opted post-intent applied-recovery surface with the existing source/route behavior as the default; topic creation opts in and now reports final-target acknowledgement loss as `TRANSACTION_RECOVERABLE`.
- **Smoke:** focused topic checks 4/4; integrated source/index/tool checks 75/75; full discovery 188/188; isolated real CLI create/confirm passed with exact target order and fixture cleanup.

# T6 — Verify and review immutable implementation

## Authority

- `atlas-topic-create-r1`, the immutable T5 target and its `T5-atomic-index-implementation` evidence, and the independent assurance contracts `skill://dev-verification` and `skill://dev-code-review`.
- This ticket is assurance, not implementation. After independent verification and review pass, the approved development-only integration gate is `python3 scripts/atlas-instance.py sync-framework --name atlas`, followed by `python3 scripts/atlas-instance.py check`.

## Objective

- Independently verify every declared acceptance criterion against one immutable T5 target, review it against repository/specification standards, run the product-package instance check, and perform only the approved development-only sync/check gate after assurance passes.

## Ownership

- **May read**: the immutable T5 target, T5 evidence, all upstream handoffs, approved spec snapshot, governing architecture/core/template/skill/command anchors, and temporary-fixture state.
- **May change or produce**: independent verification/review evidence; development-only framework synchronization and check effects after the gates; cleanup of temporary verification fixtures under the development fixture scope. The parent/backend, not the implementer, invokes `dev-verification`, `dev-code-review`, the instance check, and the sync gate.
- **Must not change**: implementation code, tests, canonical contract meaning, source/route records, workflows/commands, non-development or bound-production Atlas state, or any ticket result to make a check pass. Do not repair findings, reformat, merge, ship, deploy, or authorize a workaround.
- **Fixed shared interfaces/state**: independent evidence must cover all T1–T5 criteria, including source/route byte compatibility, pure owner seams, operation/capability, successful mutation, preflight/CAS, conflict/recovery, replay, and workflow contract. T6 is the independent verifier/reviewer and gate owner, not a second semantic implementation owner.

## Dependencies

- **Blocking**: T5 only, after T5 has a settled immutable target and integrated evidence.
- **Handoff produced**: `T6-assurance-and-development-gate` containing fresh `dev-verification` result, `dev-code-review` result, instance `sync-framework`/`check` output, cleanup proof, and any exact blocker. T7 may proceed only from a passing handoff; a safe blocker produces a new handoff and stops.

## Acceptance

- Fresh read-only `dev-verification` independently exercises the approved request/owner, compatibility, rendering, capability, mutation, preflight/CAS, recovery/replay, source/route, and skill/command criteria against the immutable T5 target; it does not trust T5's conclusion or repair the target.
- `dev-code-review` runs after required verification/integration against that same immutable target and reports only evidence-backed findings against the approved spec and repository standards. Any finding remains a blocker until its owning implementation ticket receives a new approved revision; T6 does not patch it.
- Parent/backend runs `python3 scripts/atlas-instance.py sync-framework --name atlas`, then `python3 scripts/atlas-instance.py check`, only after independent verification and review pass. The gate is development-only, `check` is separately evidenced, and no non-development profile or unrelated instance state is written.
- Temporary smoke fixtures are absent from `vault://atlas/` after the gate; no source/run/pass/topic/transaction effect outside T5's isolated fixture scope remains. The existing unrelated baseline drift is still preserved.
- T6 records a complete pass/fail/block result and never marks an unchecked criterion complete. A failed assurance, review, instance check, sync, or cleanup stops before T7 and emits an exact handoff.

## Verification

- **Scenario**: run the independent verifier and reviewer on the immutable T5 target; then execute the development-only `sync-framework --name atlas` → `check` gate and inspect fixture absence and repository/instance boundaries.
- **Environment**: exact product checkout/T5 revision; development profile only for the approved gate; read-only evidence for verification/review; no production/live profile.
- **Proof class/evidence**: fresh verifier attestation and review report, command stdout/exit evidence for both instance commands, exact fixture cleanup listing, and a no-unapproved-effect report. The evidence must distinguish the implementation target from development sync/check effects.

## Execution policy

- T6 is independent assurance of T5: no T5 implementer conclusion, sibling mutable state, or prose substitute is trusted. It does not fan in additional implementation work and does not edit to repair.
- The mandatory order is independent verification → code review → development-only `sync-framework` → development-only `check` → fixture cleanup/final boundary check. If a prior step fails, do not run a later effectful step.
- Decision gate: any unresolved spec drift, review finding, failed verifier, failed instance check, unexpected non-development effect, or fixture residue blocks T7 and requires a new owner/handoff rather than a local repair.

## Completion output

- Return fresh verification/review results, development-only sync/check evidence, cleanup proof, and the immutable target identity.
- Receiver: T7 only on a clean/pass handoff; otherwise parent `dev-ask` receives the exact blocker and no resume is authorized.

### Attempt 2 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR2` returned aggregate `VERIFIED`; all 16 target hashes matched before/after fresh evidence and every declared T1–T5 criterion passed in the exercised scenarios.
- **Review:** `agent://ReviewAtomicTopicTargetR2` returned `CHANGES_REQUIRED` with five material gaps outside the verified scenario set: recovery omitted owner post-validation; canonical partial pre-prepared backups were rejected; matching event-only acknowledgement loss stranded retry; evolved compatible topics were compared to initial-shell projections; related topics rendered bare IDs rather than canonical links.
- **Disposition:** T3 and T5 reopened. Two disjoint repair owners must address the pure planning/rendering findings and façade/recovery findings, after which parent smoke, a new immutable target, fresh independent verification, and fresh review repeat. No sync/check gate or T7 resume is authorized from this failed review.

### Attempt 3 immutable target

- **Target:** `local://atlas-topic-t5-target-r3.md#4368`; revision 3 repairs all five attempt-2 review findings in pure planning/rendering and façade/recovery seams.
- **Smoke:** pure-owner checks 18/18; focused recovery/order checks 6/6; integrated source/index/tool/harness checks 92/92; full discovery 195/195; isolated related-topic CLI create/confirm passed with exact link and cleanup.
- **Gate state:** a fresh independent verifier and fresh exact-target review remain mandatory; no attempt-2 assurance result carries forward.

### Attempt 3 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR3` returned `VERIFIED`; all 16 hashes matched before/after and freshly executed every prior criterion plus the five attempt-2 review repairs.
- **Review:** `agent://ReviewAtomicTopicTargetR3` returned `CHANGES_REQUIRED`: post-intent/receipt I/O could lose transaction identity; registry canonical title was not compared; accepted comma/angle titles conflicted with coverage parsing; related links lacked canonical-path validation and label escaping; impossible terminal/phase combinations were accepted.
- **Disposition:** T3 and T5 reopened for disjoint pure-input/rendering and façade/failure-mapping repairs. Fresh smoke, immutable target, independent verification, and review must repeat; sync/check and T7 remain blocked.

### Attempt 4 immutable target

- **Target:** `local://atlas-topic-t5-target-r4.md#CD29`; revision 4 repairs all five attempt-3 review findings in the pure owner and façade failure/record seams.
- **Parent evidence:** exact repair tests passed after correcting one nonexistent unittest method name; index/tool suites 70/70; full discovery 202/202; isolated real CLI create/confirm returned `created` then `confirmed` with exact target order and fixture cleanup.
- **Gate state:** fresh independent verification and fresh exact-target review remain mandatory; no prior assurance result carries forward. Sync/check and T7 remain blocked until both pass.

### Attempt 4 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR4` returned `VERIFIED`; all 16 hashes matched before/after, all T1–T5 criteria and attempt-3 repair scenarios passed, full discovery passed 202/202, and disposable fixtures were removed.
- **Review:** `agent://ReviewAtomicTopicTargetR4` returned `CHANGES_REQUIRED` with six blockers: recovery-side operational faults lost identity; exact scaffold-text titles collided with placeholders; duplicate canonical titles collapsed coverage/stale membership; attempt-one predecessor verification was incomplete; managed markers could overlap or appear out of order; create shape errors bypassed owner field findings.
- **Disposition:** T3 and T5 reopened for disjoint pure projection/marker and façade recovery/lineage/request repairs. A new smoke, immutable target, fresh verifier, and fresh reviewer are mandatory; no sync/check or T7 resume is authorized.

### Attempt 5 immutable target

- **Target:** `local://atlas-topic-t5-target-r6.md#B5EA`; revision 6 repairs all six attempt-4 review findings plus the parent-observed per-bucket extra-title edge. The earlier revision-5 target was superseded before evidence because its plan snapshot identity became stale after this assurance entry was appended.
- **Parent evidence:** all six focused repair regressions passed; full discovery passed 208/208; a fresh isolated production CLI create/confirm returned `created` then `confirmed`, preserved exact topic → subdomain → `TOPICS.md` receipt order, and removed its temporary profile.
- **Gate state:** fresh independent verification and fresh exact-target review remain mandatory; no prior assurance result carries forward. Sync/check and T7 remain blocked until both pass.

### Attempt 5 assurance handoff

- **Verification:** after one intentionally stopped stale-target run, `agent://VerifyAtomicTopicTargetR6` returned `VERIFIED`; all 16 revision-6 hashes matched before/after and every T1–T5 criterion passed in fresh targeted modules, direct production CLI/fault traces, and disposable profiles.
- **Review:** `agent://ReviewAtomicTopicTargetR6` returned `CHANGES_REQUIRED` with six blockers: event-only attempt-one replay is stranded; recovery classification I/O loses identity; preflight read I/O is mislabeled as semantic invalidity; accepted Markdown delimiter titles are rejected; em-dash titles break stale parsing; duplicate/unrecognized scope lines can confirm.
- **Disposition:** T3 and T5 remain reopened for disjoint pure parser/rendering and façade replay/failure-mapping repairs. A new parent smoke, immutable target, independent verification, and review must repeat; sync/check and T7 remain blocked.

### Attempt 6 assurance handoff

- **Target:** `local://atlas-topic-t5-target-r7.md#1F5A`.
- **Verification:** `agent://VerifyAtomicTopicTargetR7` returned `VERIFIED`; all 16 revision-7 hashes matched before/after and every T1–T5 criterion passed in fresh targeted modules, direct production traces, and disposable profiles.
- **Review:** `agent://ReviewAtomicTopicTargetR7` returned `CHANGES_REQUIRED` with five blockers: accepted Unicode line-boundary titles do not round-trip; valid delimiter-bearing string-array entries are rejected; inserting a coverage entry normalizes existing separator bytes; attempt-one recovery can lose identity during predecessor I/O; stored event requests are not fully owner-validated.
- **Disposition:** T3 and T5 remain reopened for two disjoint root repairs: one unified lossless Markdown scalar/list/projection codec with byte-preserving insertion, and one current-intent-first recovery/complete-event-validation seam. Fresh smoke, immutable target, verification, and review repeat; sync/check and T7 remain blocked.

### Attempt 7 immutable target

- **Target:** `local://atlas-topic-t5-target-r8.md`; revision 8 repairs all five attempt-6 review findings at two roots: a unified reversible Markdown scalar/list/projection codec with byte-preserving coverage insertion, and current-intent-first recovery with complete embedded-request validation.
- **Parent evidence:** focused regressions passed after correcting the new codec fixture and middle-insertion seam; pure index plus façade suites passed 88/88; full discovery passed 220/220; a fresh production CLI create returned `created`, exact replay returned `confirmed`, arbitrary delimiter/control-bearing title and list values round-tripped semantically, and the disposable profile was removed.
- **Gate state:** fresh immutable hashes, independent verification, and independent exact-target review remain mandatory. No sync/check or T7 resume is authorized until both assurance stages pass.

### Attempt 7 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR8` returned corrected aggregate `VERIFIED`; raw pre/post hashes matched all 16 revision-8 identities, full discovery passed 220/220, focused and production CLI codec/recovery traces passed, and disposable fixtures were absent.
- **Review:** `agent://ReviewAtomicTopicTargetR8` returned `CHANGES_REQUIRED` with three blockers: versionless legacy raw projection text can be mis-decoded as the new codec; stored event validation omits related-topic self/existence/path semantics; unreadable drifted targets during recovery classification map to request invalid instead of manual conflict.
- **Disposition:** T3 and T5 remain reopened. The bounded repair must make existing-state matching accept only exact legacy raw or exact canonical encoded representations, factor related-topic semantics into event validation using the embedded TOPICS input before live reads, and classify connector-rejected target objects as manual conflict without writes. A new smoke, immutable target, verification, and review repeat; sync/check and T7 remain blocked.

### Attempt 8 immutable target

- **Target:** `local://atlas-topic-t5-target-r9.md`; revision 9 repairs the three attempt-7 review findings through expected-value-bound legacy/canonical matching, shared pure related-topic event validation, and exact manual-conflict classification for connector-rejected live targets.
- **Parent evidence:** initial agent integration had a malformed insertion and a missing nested table/list layer; parent restored the request block, removed the duplicate definition, added exact table-layer list matching, and reran evidence. Six focused repair scenarios passed; pure index plus façade suites passed 93/93; full discovery passed 225/225; a fresh production CLI legacy-looking/control/delimiter create returned `created`, exact replay returned `confirmed`, all semantics round-tripped, receipt order stayed topic → subdomain → `TOPICS.md`, and the disposable profile was removed.
- **Gate state:** fresh immutable hashes, independent verification, and independent exact-target review remain mandatory. No sync/check or T7 resume is authorized until both assurance stages pass.

### Attempt 9 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR9` returned `VERIFIED`; all fresh criteria passed and all 16 target hashes matched before/after. Its malformed `scripts/atlas_state.py` JSON field was a report-only transcription error; the verifier confirmed the already-observed exact pre/post hash `09e19162f1c255148ffef2c1b5a3aab8cfb8cff2b578e4b714ca9f7a6e7fe8ca`.
- **Review:** `agent://ReviewAtomicTopicTargetR9` returned `Standards: FAIL`, `Specification: FAIL`, `Overall: CHANGES REQUIRED` with six blockers: rebased attempt-zero replay after unrelated input drift; rollback writes/deletion not bound to the classified output revision; missing exact raw `TOPICS.md` Topic-ID matching; ambiguous stale-label prefix matching; inverted raw initial-answer stale predicate; and connector-rejected immutable-record reads escaping the record-invalid taxonomy.
- **Disposition:** T3 and T5 are reopened for two disjoint owning repairs. The pure owner must repair exact raw ID and stale membership semantics. The transaction/façade owner must bind rollback mutations to exact output bytes, prevent same-request rebasing across transaction identities, and map unreadable provenance as record-invalid while preserving target/manual-conflict and source/route behavior. A new smoke, immutable target, verification, and review repeat; sync/check and T7 remain blocked.

### Attempt 9 immutable target

- **Target:** `local://atlas-topic-t5-target-r10.md#DCC2`; revision 10 repairs all six attempt-9 review findings: exact raw Topic-ID and stale-membership semantics, expected-revision rollback, same-request lineage binding, immutable-record error taxonomy, and recovery probe identity.
- **Parent evidence:** six focused repair regressions passed; owner/facade integration passed 93/93; the final five recovery-boundary scenarios passed; full discovery passed 232/232.
- **Gate state:** fresh independent verification and exact-target review remain mandatory. No sync/check or T7 resume is authorized until both assurance stages pass.

### Attempt 10 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR10` returned `VERIFIED`; every T1–T5 and revision-10 repair criterion passed fresh proof, all 16 hashes matched before/after, 129 targeted tests passed, and disposable profiles were removed.
- **Review:** `agent://ReviewAtomicTopicTargetR10` returned `Standards: FAIL`, `Specification: FAIL`, `Overall: CHANGES REQUIRED` with two pure-owner blockers: ambiguous legacy delimiter text can confirm both a singleton list value and a multi-value list, and duplicate requested stale entries collapse to one dictionary assignment and can confirm.
- **Disposition:** T3 remains reopened for one bounded compatibility repair. Fail closed when a legacy singleton list spelling is syntactically ambiguous with a delimiter list or the empty sentinel, at both topic scope and `TOPICS.md` table layers; account for every complete stale label and reject relevant multiplicity other than one. Add regressions, rerun smoke, create a new immutable target, and repeat fresh verification and review. Sync/check and T7 remain blocked.

### Attempt 10 immutable target

- **Target:** `local://atlas-topic-t5-target-r11.md#AAB9`; revision 11 repairs both attempt-10 review findings at the pure compatibility boundary: ambiguous delimiter/sentinel legacy singleton list spellings fail closed at topic and table layers, and stale matching separately accounts for assigned members and every relevant label.
- **Parent evidence:** both regressions reproduced all five false confirmations before the repair and passed afterward; six focused compatibility scenarios passed; the pure owner suite passed 40/40; full discovery passed 234/234; a fresh real CLI delimiter-singleton create/confirm passed and its disposable profile was removed.
- **Gate state:** fresh independent verification and exact-target review remain mandatory. No sync/check or T7 resume is authorized until both assurance stages pass.

### Attempt 11 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR11` returned `VERIFIED`; all T1–T5 criteria passed fresh targeted proof, all 16 hashes matched before/after, canonical delimiter singleton create/confirm passed, and fixtures were removed.
- **Review:** `agent://ReviewAtomicTopicTargetR11` returned `Standards: FAIL`, `Specification: FAIL`, `Overall: CHANGES REQUIRED` with five blockers: canonical list encodings can confirm a distinct literal escape-looking request; stale title labels can collide with another topic's ID label; accepted noncanonical `last_updated` key spacing is not updated; missing progress-prefix records can be accepted with a later record/terminal; and malformed existing successor events are reported as ordinary successor exhaustion.
- **Disposition:** T3 and T5 are reopened for two disjoint owning repairs. T3 must prioritize specification-level exact structural identity over the plan's impossible acceptance of ambiguous recognized legacy escape spellings, preserve only unambiguous legacy forms, disambiguate title-vs-ID stale labels, and update every accepted `last_updated` key spelling or reject it before planning. T5 must validate progress as one cumulative prefix and fully validate an existing successor event before reporting ineligibility. Add root regressions, rerun smoke, create a new immutable target, and repeat fresh verification/review. Sync/check and T7 remain blocked.

### Attempt 11 immutable target

- **Target:** `local://atlas-topic-t5-target-r12.md#328A`; revision 12 repairs all five attempt-11 review findings at their owning roots: injective canonical/legacy compatibility, title-vs-ID stale-label ambiguity, complete accepted `last_updated` updates, cumulative progress/`applied` semantics including recovery backfill, and validated successor exhaustion.
- **Parent evidence:** 12 focused repair regressions passed; seven owner/facade suites passed 191/191; full discovery passed 240/240; disposable real CLI create/confirm passed and its profile was removed.
- **Gate state:** fresh independent verification and exact-target review remain mandatory. No sync/check or T7 resume is authorized until both assurance stages pass.

### Attempt 12 assurance handoff

- **Verification:** `agent://VerifyAtomicTopicTargetR12` returned `VERIFIED`; all T1–T5 and cumulative repair criteria passed fresh owner suites, custom codec/recovery traces, real CLI create/confirm, cleanup proof, and exact pre/post hashes for all 16 target files.
- **Review:** `ReviewAtomicTopicTargetR12` returned `Standards: FAIL`, `Specification: FAIL`, `Overall: CHANGES REQUIRED`. Its task-result wrapper reported a schema violation after emitting the review; the reviewer supplied the same plain-prose verdict and evidence directly. Four blockers remain: stale labels still accept ambiguous raw escape spellings; non-prefix pre-prepared backups are accepted; generic applied recovery mutates missing progress before validating the complete set; and invalid-UTF-8 array items reach UTF-8 sorting and lose the owner finding taxonomy.
- **Disposition:** T3 and T5/T2 reopen at the two owning roots. T3 must use the injective scalar compatibility rule for stale title labels and exclude invalid array items from all sorting/semantic processing after recording their exact owner finding. T5/T2 must require backup records to be one canonical prefix before target access and validate the complete generic progress set before any backfill, then append only a missing suffix for a valid all-output recovery. Preserve source/route bytes and every existing operational classification. Add root regressions, rerun smoke, create a new immutable target, and repeat fresh verification/review. Sync/check and T7 remain blocked.

### Attempt 13 immutable target

- **Target:** `local://atlas-topic-t5-target-r13.md#4F74`; revision 13 repairs all four attempt-12 review findings at their owning roots: injective stale-title matching, invalid UTF-8 array exclusion with stable findings, canonical backup prefixes before preparation, and validate-before-backfill generic progress.
- **Parent evidence:** four exact regressions passed; changed owner suites passed 131/131; seven pure/index/facade suites passed 195/195; repository discovery passed 244/244; direct counterexample probes now fail closed; disposable CLI returned exact invalid-request, created, and confirmed outcomes and removed its profile.
- **Gate state:** fresh independent verification and exact-target review remain mandatory. No sync/check or T7 resume is authorized until both assurance stages pass.

### Attempt 13 verification handoff

- **Verdict:** `agent://VerifyAtomicTopicTargetR13` returned `VERIFIED` for `local://atlas-topic-t5-target-r13.md#4F74` against specification `#6C8F` and current plan `#EF50`.
- **Fresh evidence:** all 16 hashes matched before and after; pure owner 45/45, source 21/21, façade 65/65, harness 10/10, and full discovery 244/244 passed; direct stale-escape, surrogate-array, backup-gap, progress gap/collision/prefix, concurrency, recovery, and real CLI create/confirm scenarios passed; disposable fixtures were removed and no bound instance was accessed.
- **Identity note:** the immutable target names the freeze-time pre-target plan snapshot `#EB1D`; `#EF50` is its successor that only records target `#4F74`. No target or authority bytes drifted.
- **Gate state:** exact-target code review is now authorized. Sync/check and T7 remain blocked pending review approval.

### Attempt 13 review handoff

- **Review:** `agent://ReviewAtomicTopicTargetR13` returned `Standards: FAIL`, `Specification: FAIL`, `Overall: CHANGES REQUIRED`; all 17 relevant worktree dependencies were not frozen because `scripts/atlas_connector.py` was omitted from the 16-file target, unknown surrogate field names can escape CLI response encoding, recovered plans do not require the topic input to be missing, and an existing `applied` terminal bypasses owner post-validation of stored/live output bytes.
- **Disposition:** T2/T5/T3 reopen at three bounded roots. Freeze `scripts/atlas_connector.py` with the connector/transaction lineage; reject non-UTF-8 request field names at the safe parent path without echoing them; enforce topic-missing plus existing subdomain/registry input invariants while loading every topic transaction event; and independently owner-post-validate all-output state before honoring an existing `applied` terminal. Preserve valid unknown-field paths, rolled-back/aborted reporting, exact recovery identities, source/route behavior, and every prior repair. Add exact regressions, rerun smoke, freeze the complete 17-file target, then repeat fresh verification/review. Sync/check and T7 remain blocked.

### Attempt 14 paused implementation handoff

- **Outcome:** `blocked` by the user's explicit pause after both bounded repair tasks completed and before parent validation. Pre-state was attempt-13 `CHANGES REQUIRED`; post-state is an unverified partial revision with every descendant settled and no external effect.
- **Implemented, not yet validated:** `RepairUnknownUnicodeFieldNames` changed `scripts/atlas_index.py` and `tests/test_atlas_index.py` so unsafe request field names produce one UTF-8-safe parent-path owner finding while valid unknown names retain exact paths. `RepairRecoveredOwnerInvariants` changed `scripts/atlas_tool.py` and `tests/test_atlas_tool.py` so every recovered event requires inputs `(missing, existing, existing)`, existing applied state receives fresh owner post-validation, semantic failures are record-invalid, and operational read failures retain their established taxonomy.
- **Partial identities:** `scripts/atlas_connector.py` `5d53a078cc0ce5ea296d7fc2c59991a4e6033d94f66dfd01290df236aa1437c7`; `scripts/atlas_index.py` `1f29ef7d73f55bfb2c6cf4aa7b4b4cb09908c7dc47d6b9c0e211725ffd91ab3e`; `scripts/atlas_tool.py` `38eb9f150e8b4fb569da7e76d8bb67e0dfa6ae4bc52128d7ba2dcca800656e72`; `tests/test_atlas_index.py` `425491674a05e9dcd60c1daca531458a3a54cb3e4178c2ca1c3d6d6764bfcf5b`; `tests/test_atlas_tool.py` `62cf1fc3d5f737d5952bfbcbc988b4a85db491143e182d808166eb3395a39beb`.
- **Evidence boundary:** the attempt-13 failures were reproduced before repair: surrogate unknown-key CLI exited `1` with `UnicodeEncodeError`; a hash-consistent existing-topic-input record returned `rolled-back`; and hash-consistent invalid applied outputs returned `applied`. No test, smoke, formatter, linter, target freeze, verification, review, sync/check, bound-instance write, or shipping action ran after the attempt-14 edits. The partial revision is diagnostic only until validated.
- **Next receiver:** `dev-implementation` may resume from this handoff under the unchanged spec `#6C8F`. First re-read and validate the five partial identities, run the new focused regressions and prior counterexamples, then owner/full suites and disposable CLI smoke. If they pass, freeze a complete **17-file** target that adds `scripts/atlas_connector.py`, obtain fresh independent verification and review, and only then run the already-authorized development sync/check gate. T7 remains blocked.

### Systemic audit handoff

- **Audit:** `local://atlas-topic-systemic-audit.md#FEEB` records the approved bounded codec/transaction audit. Four parallel read-only audits modeled the codec identity, transaction recovery, cross-machine composition, and R2–R13 escape history; no repository, test, plan-authority, bound-instance, sync/check, or shipping effect occurred.
- **Outcome:** `authority-change-required`. Attempt 14 remains diagnostic and unverified. Direct probes confirmed non-prefix backup acceptance, non-total surrogate response encoding, capability-shape trust, connector/semantic error collapse, and an incomplete registry identity oracle. The terminal probe exposed an r1 specification contradiction: complete valid terminals must remain historical authority after later product evolution, while malformed/nonterminal journals require strict validation. The historical loop came from implicit versionless identity plus duplicated façade/generic journal ownership, not isolated missing regressions.
- **Resolution:** approved r2 uses canonical requested identity, request-scoped unrelated-drift handling, strict malformed-journal validation with valid-history source compatibility, topic-identity-scoped input-bound a0/a1 lineages, historical terminal owner proof, typed deep owner/transaction/connector seams, and executable registry-field validation.
- **Gate state:** the systemic audit and authority-change gate are complete. No attempt-14 symptom repair, assurance reuse, sync/check, or T7 resume is authorized.
- **Approved resolution:** documented alignment evidence is `local://atlas-topic-r2-grill-decisions.md#851F`; `local://atlas-topic-creation-spec-r2.md#9DB0` is approved `atlas-topic-create-r2` and supersedes r1 plus every R2–R14 partial/review target.
- **Next route:** `dev-ask` → one cohesive `dev-implementation` → fresh `dev-verification` → exact-target `dev-code-review` → the already bounded development-only sync/check gate. No derivative ticket graph or repeated human approval is required unless semantic authority changes.
- **r2 implementation attempt:** `local://atlas-topic-r2-implementation-contract.md#9E34` binds high-consequence, one-lineage ownership, AC1–AC12, valid-history compatibility, degraded behavior, and the no-ticket/no-repeated-approval route. Fresh owner `ImplementAtlasTopicR2` is running; Main retains smoke/freeze/verification/review authority.
- **r2 attempt 1 result:** `FAILED` after an incomplete four-file Handoff. Main’s fresh affected-suite diagnostic ran 183 tests with 33 failures and 138 errors (`artifact://772`), including an immediate `FRESHNESS_WINDOW` `NameError`, global registry-validation cascades, source valid-history record regression, and incomplete AC/contracts/tests. No target was frozen and no assurance evidence is reusable.
- **r2 attempt 2:** same-owner repair is authorized under unchanged contract `#9E34`; the failure is deterministic and reproduced in 3.68 seconds. `ImplementAtlasTopicR2` must repair owning roots and return a complete Handoff before Main reruns smoke.
- **r2 attempt 2 result:** `FAILED`. Main’s fresh six-module acceptance smoke ran 184 tests with 21 failures and 8 errors (`artifact://871`). Deterministic roots remain in topic predecessor fault classification, uninitialized recovery state, exact replay/successor/terminal eligibility, historical owner-output revalidation, generic manual-conflict semantics, and missing expert-skill surface files. No target was frozen and no assurance evidence is reusable.
- **r2 attempt 3:** authorize one fresh-context same-owner repair under unchanged contract `#9E34`, using the systemic audit closure ledger rather than another isolated counterexample patch. Main retains smoke/freeze/verification/review authority.
- **r2 attempt 3 result:** `FAILED`. Main’s fresh six-module smoke ran 188 tests with 5 failures and 73 errors (`artifact://872`). Most errors cascade from two structural state-machine defects introduced in the shared transaction owner (`_target_records` has no `targets` accumulator; `recover_transaction` uses `terminal_path` before assignment). Five independent failures show recovery prevalidation now misclassifies hash-consistent invalid embedded event requests as `INDEX_REQUEST_INVALID` instead of `TRANSACTION_RECORD_INVALID`. No target was frozen; no assurance evidence is reusable.
- **Mandatory fallback:** implementation is stopped. Run one fresh systemic audit of the r2 implementation/workflow failure, then decide between one consolidated clean repair and specification simplification. No fourth patch attempt, verification, review, sync/check, or T7 resume is authorized before that decision.
- **Post-attempt systemic audit:** `local://atlas-topic-r2-implementation-audit.md#443C` reconciles all 78 non-passing attempt-three outcomes to two structural transaction cascades plus one provenance-order defect, records latent shared-seam risks, and incorporates four parallel read-only audits. The approved r2 contract is coherent; no repository, test, bound-instance, sync/check, or shipping effect occurred during the audit.
- **Decision:** choose one consolidated clean repair under unchanged `atlas-topic-create-r2`; do not simplify AC1–AC12 or restore deprecated expert entrypoints. One fresh owner receives one exact coupled repair boundary. Main runs structural gates and ordered behavioral proof; any failed/unclassified check ends the attempt without a same-lineage patch cycle.
- **Consolidated repair contract:** `local://atlas-topic-r2-consolidated-repair-contract.md#FB72` binds the only post-audit implementation attempt, exact allowed surfaces, deep-seam replacement requirements, current atlas-ask compatibility, Main-owned structural/behavioral gates, and a stop-on-any-failure rule. It introduces no new semantic authority.

- **Consolidated repair result:** `FAILED` at Main's focused behavioral gate. Structural checks passed (`py_compile`; no undefined/unbound local in touched runtime files), then a 30-case focused run produced 27 passes and 3 failures. All three are stale acceptance constructions: two expect live-target reinterpretation after a valid `rolled-back` terminal, and one expects a successful fresh-base topic creation to leave the requested subdomain projection unchanged. Exact evidence and target hashes: `local://atlas-topic-r2-final-repair-failure.md#F18B`.
- **Stop state:** the final post-audit attempt is exhausted. No full suite, CLI smoke, target freeze, verification, review, curation, development sync/check, bound-instance write, or T7 resume is eligible from that attempt.
- **Fresh revision authorization:** the human explicitly authorized the recomputed unchanged lifecycle route and one fresh task revision. `local://atlas-topic-r2-acceptance-migration-contract.md#8109` permits one fresh owner to update only `tests/test_atlas_tool.py`, aligning the three stale constructions with r2 AC4/AC8/AC9/AC10 while preserving every runtime byte. Main retains all smoke/freeze/assurance/integration gates; any runtime change need returns `authority-change-required`.
- **Acceptance migration results:** the authorized r1 test migration corrected three stale r1 constructions; its first focused run passed 2/3 and exposed one assertion that incorrectly forbade the required `manual-conflict.json` terminal write. Revision r2 `local://atlas-topic-r2-acceptance-migration-r2-contract.md#D827` corrected that control/product boundary. The next full suite passed 187/188 and exposed one source fixture that combined a progress-prefix gap with a later collision while expecting collision precedence; revision r3 `local://atlas-topic-r2-acceptance-migration-r3-contract.md#B868` isolated the two invalid histories. No runtime file changed during r1-r3.
- **Main smoke:** structural gates passed; the exact migrated trio passed 3/3; the complete focused transaction/lineage gate passed 30/30; the corrected source progress case passed; the affected connector/state/index/source/tool/harness suite passed 188/188; and a disposable current-module CLI scenario proved attempt-zero create/confirm plus interrupted recovery, eligible attempt-one replay, reconfirmation, and fixture cleanup.
- **Frozen target:** `local://atlas-topic-r2-immutable-target.md#DE55` binds 19 product/runtime/test files plus the applicable rule manifest and all Main smoke evidence. It is eligible for fresh high-consequence `dev-verification`; sync/check and T7 remain blocked until verification and exact-target review pass.
- **Independent verification:** fresh verifier `VerifyAtlasTopicR2Final` rechecked all target/rule hashes, passed structural/import checks, 84 focused tests, the 188-test affected suite, and a disposable CLI lifecycle, and returned aggregate `VERIFIED`. Its authority mapping was later found defective by review: verification contract `#0F40` re-labelled the governing AC ledger and conflated three mutation targets with six bound inputs, so its regression evidence is reusable only as smoke input after repair.
- **Exact-target review:** distinct reviewer `ReviewAtlasTopicR2Final` returned `Standards: FAIL`, `Specification: FAIL`, `Overall: CHANGES REQUIRED` with six blockers preserved at `local://atlas-topic-r2-review-failure.md#43AD`: raw topic-frontmatter canonicality, registry-list UTF-8 ordering, duplicate public JSON keys, marker-sentinel values, pre-intent typed connector taxonomy, and missing index-owned recovery binding. All target/rule hashes remained unchanged; no advisory or effect occurred.
- **Paused repair boundary:** `local://atlas-topic-r2-review-repair-contract.md#DF8C` binds one cohesive six-blocker repair attempt and exact allowed surfaces. The user requested a pause immediately before its next subagent deployment. No repair owner has been dispatched; repaired smoke, new freeze, corrected verification, rereview, sync/check, and T7 remain blocked.

# T7 — Resume blocked agent-memory plan

## Authority

- `atlas-topic-create-r1`, the passing T6 assurance handoff, and the existing mutable plan `local://repo-agent-memory-first-draft-plan.md`.
- Resume authority is the existing plan's row-5 `/atlas-index` request and its Attempt 1 Blocker Handoff, which records: `NO_CODE`: `Unsupported multi-target topic creation: the exact multi-target write set has no applicable core transaction contract; halt for a contract extension or explicit migration rather than hand-rolling a transaction or rollback.` The existing plan's T1/T2 remain complete; do not redo them.

## Objective

- Resume that exact row-5 `/atlas-index` topic-shell request through the checked-in command and skill interface now that the approved façade contract exists, then continue only the successor chain already authorized by the prior plan; a new safe blocker stops immediately and is recorded as a new handoff.

## Ownership

- **May read**: `local://repo-agent-memory-first-draft-plan.md`, its Attempt 1 Blocker Handoff and exact raw `/atlas-index` request, T6 assurance, `.agents/commands/atlas-index.md` → `.agents/skills/atlas-index/SKILL.md`, and façade receipts returned by that checked-in skill.
- **May change or produce**: only the prior plan's remaining T3/T4 execution records and its explicitly required receipt/handoff fields, through the prior plan's own authority and checked-in skills. Produce a success receipt or an exact new blocker handoff; continue prior-plan user-facing successors only when their own criteria authorize them.
- **Must not change**: this ticket's fixed topic contract, scripts, tests, command/skill code, unrelated repository memory artifacts, related-topic state, or any Atlas state through direct I/O. Do not redo prior work, hand-author Markdown/registry/index bytes, bypass the command/skill, use a source/route transaction, introduce a migration, or widen the prior plan. This ticket grants no new non-development write authority; any effect must already be authorized by the prior plan and current checked-in skill.
- **Fixed shared interfaces/state**: the exact prior-plan `/atlas-index` request is replayed byte-for-byte from its recorded row; façade operation is `index.create_topic` (or `index.recover_topic` only for a named recoverable attempt); compatible existing topic confirms without changing answer/freshness; safe refusal is evidence, not permission for a workaround.

## Dependencies

- **Blocking**: T6 passing `T6-assurance-and-development-gate`.
- **Handoff consumed**: `local://repo-agent-memory-first-draft-plan.md`'s existing row-5 request, Attempt 1 blocker/resume condition, and prior receipts. T7 must not reconstruct the raw request from memory or rerun completed T1/T2.
- **Handoff produced**: an exact prior-plan continuation receipt and completed successor/handoff record, or a new blocker handoff naming the active checked-in command/skill, literal raw arguments, terminal code/detail, and the first safe stop.

## Acceptance

- The exact prior-plan row-5 `/atlas-index` request enters through `.agents/commands/atlas-index.md` and `.agents/skills/atlas-index/SKILL.md`; no direct façade/core/connector call is made outside the active skill. The receipt records literal raw arguments, operation, request date, result state, paths/revisions/transaction identity when present, and blocker as `none` or the exact reported code/detail.
- A newly absent topic either creates the prior plan's exact topic shell through `index.create_topic`, or an exact compatible topic returns confirmation with no topic/answer/freshness rewrite. No vocabulary/tag promotion, domain/subdomain creation, unrelated drift repair, source write, pass, relation, acquisition, or answer synthesis is introduced by the resume.
- If the façade returns a recoverable failure, recovery uses only `index.recover_topic` with the named attempt and exact original request; recovery only reports eligibility, and any replay uses only the one exact eligible successor. No force-write, rebasing, substituted bytes, or direct rollback is performed.
- On any new safe blocker, malformed receipt, unsupported operation, failed validation, conflict, or nonterminal result, stop before wider action and record an exact new handoff in the prior plan; do not substitute another topic, direct write, migration, or workaround.
- If the row-5 request succeeds, continue the prior plan's already-defined source/research/verification successor chain only through its checked-in skills and only within its original authority. T7 does not select a final memory architecture or alter the new topic contract.

## Verification

- **Scenario**: drive the prior plan's exact `/atlas-index` raw request through its command/skill entry, inspect the terminal façade receipt, and, if required by that receipt, use the exact named recovery operation. Then verify the prior plan's next-owner/successor condition or record the first safe blocker verbatim.
- **Environment**: the current checked-in product package and the prior plan's authorized profile only; no direct host-path or vault mutation. Any permitted prior-plan effect is recorded by its active skill, not by T7 choreography.
- **Proof class/evidence**: user-facing skill-interface trace with literal raw arguments, command/skill path, returned receipt/paths/revisions, and exact blocker/handoff. T7 is complete only when the prior plan has a success continuation or a durable safe-block handoff; it never claims success from a partial/nonterminal result.

## Execution policy

- T7 is a terminal resumptive ticket after T6, not a back edge to T4 or a new implementation fan-out. It may not reopen or redesign any earlier ticket.
- Run only the prior plan's row-5 request first. Follow its existing successor chain only after a terminal successful/confirmed result and only through the owning checked-in skill. A new safe blocker stops the chain immediately.
- Decision gate: prior-plan authority missing/stale, T6 not clean, command/skill bypass, changed raw request, non-approved effect, or any safe blocker stops T7 and records a new handoff to the parent/human authority.

## Completion output

- Return the prior-plan continuation receipt and next-owner handoff, or the exact safe-blocker handoff with no workaround and no unapproved effect.
- Receiver: the owner of `local://repo-agent-memory-first-draft-plan.md` for the prior-plan successor; parent `dev-ask` receives the terminal T7 result.

## Criterion accounting

Each approved specification test seam has exactly one ticket owner. Independent assurance in T6 rechecks these criteria but does not create a second implementation/state owner.

| Approved specification test seam | Sole ticket owner | Required task-specific proof | Boundary preventing overlap |
|---|---|---|---|
| Pure request and owner seam: canonical request hash, exact three-target order, deterministic bytes, no caller target material, all request/registry/subdomain/orphan/conflict findings | T3 | Pure unit/property cases over normalized, invalid, baseline-drift, and conflicting snapshots | T3 has no connector or façade mutation; T5 only consumes its plan |
| Pure compatibility seam: absent plan, exact compatible confirmation/no-op, each mismatch conflict, preservation of existing answer/coverage/confidence/freshness/dates | T3 | Table-driven pure compatibility matrix and unchanged-byte assertions | Compatibility belongs only to `atlas_index.py`; workflows do not decide it |
| Pure rendering seam: topic shell, canonical row, requested subdomain projections, LF/CRLF/final newline, unrelated/unmanaged preservation, baseline drift post-validator | T3 | Byte/hash snapshots and owner post-state validator assertions | Renderers are pure; façade only binds revisions and executes |
| Façade capability seam: exactly two sorted mutation operations, read-only omission and `MUTATION_UNAVAILABLE` without host fallback | T5 | Connector capability integration tests with read-only and mutation-capable profiles | Capability/dispatch belongs only to `atlas_tool.py` fan-in |
| Successful mutation seam: exact three targets/order, immutable records, rereads, post-validator/registry validation, specified receipt, no fourth mutation target | T5 | Instrumented isolated connector smoke and receipt/terminal assertions | T5 owns integrated façade/transaction behavior; T2 owns only source/route compatibility |
| Preflight and CAS seam: stale-before-intent, post-each-application recoverability, exact reverse rollback, post-validation never reports created partial | T5 | Fault injection at each target and post-validation with input-byte/revision comparison | Topic transaction execution is only T5 through generic T2 API |
| Conflict/recovery seam: mixed rollback, output drift, changed request, malformed record, missing backup, second successor, exact recovery | T5 | Recovery/fault/byte-replay fixtures and stable finding assertions | Recovery operation/owner mapping is T5; T7 only consumes a terminal receipt |
| Replay seam: applied confirmation, one eligible identical attempt-one after attempt-zero abort/rollback, no self-successor/rebase/substitution | T5 | Replay and successor eligibility tests in isolated connector | T5 owns façade replay; T6 only verifies |
| Source/route regression seam: request/envelope, records, order, IDs, receipt hashes, terminals, old recovery, existing suite | T2 | Before/after fixture byte comparison and source/effect/refresh regression output | T2 owns direct extraction/migration; T5 must preserve its handoff |
| Skill/command contract seam: atlas-index/research operation callsites, no direct CAS/choreography, thin commands unchanged, development sync/check and fixture cleanup | T4 for workflow/command implementation; T6 is the sole independent gate owner for sync/check evidence | T4 callsite trace and command identity; T6 fresh interface proof plus ordered development-only `sync-framework` → `check` and cleanup | T4 changes only skill callsites; T6 verifies/gates but does not edit them |

No criterion is unowned. No criterion is authorized twice as mutable behavioral/state work.

## Graph proof and execution topology

- **Edges**: `T1 → T2`, `T1 → T3`, `T1 → T4`, `T2 → T5`, `T3 → T5`, `T4 → T5`, `T5 → T6`, `T6 → T7`.
- **Levels**: level 0: T1; level 1: T2 ∥ T3 ∥ T4; level 2: T5 (neutral fan-in); level 3: T6 (independent assurance of one immutable T5 target); level 4: T7 (prior-plan resumption).
- **Acyclic proof**: every edge advances from a lower level to a higher level; T7's prior-plan successor is an external resumptive handoff, not an edge back to T4/T5. There is no cycle, unnamed blocker, or dependent task marked independent.
- **Fan-in rule**: T5 cannot start until all three named handoffs arrive. T2, T3, and T4 each bind the same T1 revision and own disjoint mutable surfaces: transaction/source adapters, pure index owner, and skill callsites respectively. T5 is the only façade/integration authority. T6 reads one immutable target and owns no implementation state. T7 owns only the prior plan's continuation.
- **No overlapping state authority**: architecture/core/template contract is T1; generic provenance/application/recovery is T2; topic semantics/planning/rendering is T3; workflow callsites are T4; connector-bound façade integration is T5; assurance/gate evidence is T6; prior-plan runtime continuation is T7. The connector remains the sole byte-I/O/CAS/durability owner throughout.

## Critical anchors

- `local://atlas-topic-creation-spec.md#6C8F` — approved authority, interfaces, data, security, test seams, boundaries, resolved decisions, and approval limits.
- `local://repo-agent-memory-first-draft-plan.md` — prior mutable plan; its Attempt 1 Blocker Handoff and exact row-5 `/atlas-index` request are T7 authority.
- `.agents/ARCHITECTURE.md` — product/instance seam, logical vault identity, managed-section preservation, façade envelopes, connector/session invariants, and write-set boundary.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — `MANIFEST.md`/`TOPICS.md`/`RELATIONS.md` table shapes, deterministic cache derivation, `validate_documents`, `reduce_event`, full-byte revisions, and source/route transaction record contract.
- `.agents/skills/atlas-core/assets/research-library-templates.md` — `SUBDOMAIN-INDEX.md` and `TOPIC-INDEX.md` managed markers, initial answer contract, and optional-section boundaries.
- `scripts/atlas_tool.py` — `OPERATIONS`, `_READ_ONLY_OPERATIONS`, `_mutations`, `_Port`, source/route transaction adapters, `_dispatch`, `capabilities`, `execute`, and `_exception`.
- `scripts/atlas_source.py` — current `canonical_json`, `sha256`, `TransactionTarget`, `TransactionPlan`, `ConnectorPort`, `build_transaction_plan`, `build_successor_plan`, `recover_transaction`, and `execute_transaction` extraction source; source/route renderers remain outside T2's generic move.
- `scripts/atlas_transaction.py` — approved new generic transaction owner and direct source/route migration target.
- `scripts/atlas_index.py` — approved new pure topic owner and `prepare_topic` seam.
- `scripts/atlas_state.py` — existing `validate_documents`, `reduce_event`, and `plan_transaction_recovery`; no topic-create event is permitted.
- `.agents/skills/atlas-index/SKILL.md` and `.agents/skills/atlas-research/SKILL.md` — only workflow callsites changed by T4.
- `.agents/commands/atlas-index.md` and `.agents/commands/atlas-research.md` — thin dispatch stubs, unchanged.
- `tests/test_atlas_source.py`, `tests/test_atlas_tool.py`, `tests/test_atlas_state.py`, and the pure `tests/test_atlas_index.py` seam — task-specific regression/integration fixtures; test files are not implementation authority.
- `python3 scripts/atlas-instance.py sync-framework --name atlas` followed by `python3 scripts/atlas-instance.py check` — T6 development-only gate after independent assurance.

## Assumptions and pre-decided fallbacks

- The specification-bound file identities are the implementation baseline. If a target changed before implementation, re-read and rebind the authority; if the change alters a fixed interface, target, shell, transaction rule, or source/route byte contract, stop for a new specification revision rather than patching this one.
- Existing Atlas ID/path normalization, registry tables, state validation, managed markers, connector capabilities, and template text remain authoritative. No ticket invents a normalization rule, date, retry, migration, backend, event, or fallback.
- Unrelated baseline `SUBDOMAIN_TOPIC_MAP_DRIFT` entries are preserved and included in requested post-validation as baseline; a globally clean subdomain is not required. Invalid requested projection or invalid unrelated registry finding outside the explicitly preserved baseline remains a deterministic no-write rejection.
- A connector profile missing any required mutation guarantee is read-only: return `MUTATION_UNAVAILABLE`, never use host paths, and never weaken CAS/locking/durability/deletion.
- Preflight invalidity yields a stable no-write finding; stale input before intent yields `REVISION_STALE` with no intent/write; post-intent interruption or durability failure yields `TRANSACTION_RECOVERABLE`; reread `other` or immutable mismatch yields `MANUAL_CONFLICT`; post-validation failure recovers through the same transaction identity. No force-write, rebase, substituted bytes, or progress inference is allowed.
- Existing source/route records are loaded as-is without conversion. Any byte mismatch is a compatibility stop, not permission for an alias or migration.
- T5 uses isolated temporary fixtures only. T6's `sync-framework`/`check` is development-only and runs only after independent verification/review; no non-development profile is written. Temporary fixture residue blocks completion until removed.
- T7 uses the prior plan's exact raw request and successor rules. A new safe blocker is recorded verbatim and stops; it is never replaced by direct I/O, another topic, or an architecture workaround.

## Ticketing decision

- **Ticketing defect**: none. The approved revision is complete for derivative ticketing: fixed interfaces and ownership are present, all specification test seams have one owner, dependencies form an acyclic named graph, and no ticket authorizes a forbidden effect.
- Any change to the approved target set, initial shell/freshness meaning, operation/module names, compatibility, errors/rollback, source/route byte behavior, or non-development authority invalidates this ticket set and requires a new specification revision and approval.

## Verification / Done criteria

All criteria remain unchecked while `Status` is `PENDING`. The implementation plan is complete only when each relevant ticket row is checked with its observed completion timestamp and every criterion below has fresh evidence.

- [ ] The implementation target remains bound to `atlas-topic-create-r1`, spec snapshot `#6C8F`, both approved decisions, and the specification-bound file identities; no material contract drift was silently accepted.
- [ ] T1's architecture/core/template projection contains every fixed request, response, target, shell, compatibility, transaction, recovery, security, ownership, preservation, and no-go clause without redesign.
- [ ] T2's shared transaction extraction has no source/route alias/re-export/deprecated path and proves byte-identical source/route records, IDs, receipts, terminals, order, and old-record recovery.
- [ ] T3's pure owner proves deterministic request/hash/order/rendering, every specified rejection, exact compatibility confirmation/conflict, newline/unmanaged preservation, baseline drift handling, and no connector mutation.
- [ ] T4's skill callsites invoke only the approved index operations for absent-topic creation/recovery, preserve existing-topic research behavior, and leave both thin commands unchanged.
- [ ] T5's isolated integrated smoke and targeted tests prove exact capability, envelope, three-target mutation, immutable provenance, reread revisions, owner post-validation before terminal, stale/CAS/recovery/conflict/replay behavior, stable findings, no fourth target, and cleanup.
- [ ] T6's independent `dev-verification` and `dev-code-review` pass against one immutable target; development-only `sync-framework` then `check` pass; no non-development effect or temporary fixture remains.
- [ ] T7 resumes the exact prior-plan row-5 `/atlas-index` request through checked-in skills, records a terminal success continuation or an exact new safe-blocker handoff, and introduces no bypass or new authority.
- [ ] The full criterion-accounting table is satisfied exactly once, the DAG remains acyclic with all fan-in handoffs named, and no overlapping behavioral/state authority or forbidden non-goal effect is present.
