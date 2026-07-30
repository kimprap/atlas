# Living source retrospective conformance

**Datetime**: 2026-07-23-2322
**Scope**: Close the retained living-source-quality revisit safely, then revalidate the current 503-source Atlas cohort from fresh canonical text and apply only exact user-approved corrections.
**Status**: DONE

## Context

Atlas currently has 503 active living source rows and no missing source artifacts. The prior revisit corrected two sources, but its T7 cleanup remains open because the T5 executor did not retain the required source/route transaction records; that provenance cannot be reconstructed after the fact. Its durable report remains at `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-21--living-source-quality-revisit.md`, its retained campaign root is `vault://atlas/tmp/source-quality-revisit-2026-07-21/`, and its active plan is `.agents/plans/2026-07-21-1613_living-source-quality-revisit.md`.

The Atlas product already defines the behavior this campaign must apply: source evidence is canonical UTF-8 text plus textual URLs; inaccessible or insufficient text is a no-write; genuine aggregate pages require a user choice between page-only, selected child expansion, or deferral; content transitions require complete comparable text; and every successful living mutation uses separate recoverable source and route transactions. The historical campaign root is forensic evidence only—never semantic input for revalidation, drafting, classification, or routing.

The intended end state is a hash-frozen current product baseline, a fresh current-product disposition for every original source, exact approval and later-override provenance, complete transaction closure for every successful write, validated registries, selectively refreshed dirty topics, a durable report, and cleanup/archive only after explicit approval.

## Tasks

- [x] T1. Activate and freeze the execution contract
  completed 2026-07-24-1242
- [x] T2. Freeze and preflight the current product
  completed 2026-07-24-1249
  canonical recovery 2026-07-24-1350: parent pointer `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t2-preflight-recovery.json` (`040b49a9389bfb3a2993f7003b7b038bff42e67d37e9a1f6cd5f1989ed28e97d`) binds authoritative T2 `cd2762eb612e99c41d46cb39f4a99cef253752d0b7a61e4fb1856871feb44c6d`. The later Grok recovery authority `b2f197cf83bcba11aaef833296e498b7a3a3b55c22b6d8e1ab5af046f5d5353e` is independent corroboration only and does not create a second authority chain.
- [x] T3. Freeze the current 503-source cohort
  completed 2026-07-24-1255
  canonical rebind 2026-07-24-1350: parent pointer `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t3-rebind.json` (`d05223be215f28838e7e7a517c4aa914afd06766ac6442ba35db438ace95269a`) binds authoritative T3 rebind `0bd2d49e6baae1d39800cea23aabe0b301c9ea7ce1d5a28f95c36ef7a61c3f08`. The later Grok rebind `65c54589689d96bbd57afb233ee2edb5f6cb47d47d038f77c4236b477fd0268b` independently reconfirmed all 503 rows and frozen bytes but is non-authoritative.
- [x] T4. Resolve the predecessor cleanup gate
  completed 2026-07-24-1443
  disposition: user chose **defer and continue**. Gate `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t4-predecessor-cleanup-gate.json` (`29f58cdde40a035a462b3e3e7b57f4a61331d2232f2cf7a462af223f3e615686`) and disposition `…/indexes/t4-predecessor-cleanup-disposition.json` (`cc5022bd3950f6e984594cbb1c14c06e3efe1e1002acfce2cef1eda4ece90ff2`) bind the unchanged exact root digest. The predecessor root and plan remain untouched as forensic evidence, are excluded from semantic input, and T5 may proceed.
- [x] T5. Revalidate all frozen sources from fresh text
  started 2026-07-24-1500: `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t5-dispatch.json` (`502476adc21922c8af4277e29276ed8e0345fbf8ea1b5015b2c1ee456204eba4`) binds 26 source-ID-sorted packets covering all 503 frozen rows; frozen authority/product/living checks passed before dispatch.
  completed 2026-07-24-1550: `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t5-revalidation.json` (`5f407c795173abdcce7c58932a8607727463b26ced218d8e2d914b523f339f85`) binds 26 verified batch indexes and all 503 rows. Counts: 420 `changed_hash`, 7 `quality_fail_same_hash`, 7 `pass_current`, 34 `pending_aggregate_scope`, 28 `blocked_insufficient_text`, and 7 `blocked_non_text`; 427 rows are rewrite-eligible and 34 aggregate manifests retain 18,924 normalized child URLs.
  verification: session bindings `dfbec68c9a71f6f7783abb08c5a4f66dd5d39d78d9e32d467e484b567824c018` and refinement closure `46e8de63330cc388325883c4a5b49213f0055f6f53b57c8f043dbdcd9ba4df5a` bind 29 Grok sessions, targeted repairs, 2,043 surviving batch files, and removal of 576 transport artifacts. Product APIs, registry validation, exact product/living bytes, artifact identity, every surviving bound-path/hash, and persisted predecessor/sibling-path scans returned zero findings. Six worker traces did consult schema/path material outside their packet despite the isolation instruction; no persisted semantic cross-reference or API mismatch survived, but T7 independent review remains mandatory before any approval or living write.
- [x] T6. Resolve aggregate-page scope and child candidates
  completed 2026-07-24-1625: `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t6-closure.json` (`8fb5e53376c10504922e460bc5ad23db7939747909f489d8fdbfd1e0d78cc7cb`) binds the deterministic 503-row merge, 34 aggregate candidates, user delegation **“auto-choose from your recommendation, for all asks.”**, seven isolated Grok recommendation sessions, 34 exact decisions, eleven accepted fresh page-only resolutions, and all finalized no-write scope rows. Decisions: 11 `page-only`, 18 `expand`, 5 `defer`; final cohort: 431 `changed_hash`, 7 `quality_fail_same_hash`, 7 `pass_current`, 28 `blocked_insufficient_text`, 7 `blocked_non_text`, 18 `aggregate_expand_selected`, and 5 `aggregate_deferred`, with 438 rewrite-eligible rows.
  expansion candidate `…/indexes/t6-expansion-candidates.json` (`41b301ac4f7b0d918c049eba02d44e275fe017da0c33438ca7cd8fd75426aa43`) contains 222 exact selected URLs: 221 new pending rows and one existing frozen no-write, with zero normalization, deduplication, source-ID collision, binding, registry, product-drift, or living-drift findings. No living write or T8 approval is implied; T7 independent acceptance remains mandatory.
- [x] T7. Build and independently review cohort closure
  completed 2026-07-24-1645: `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t7-conformance-report.json` (`36176487df81c960874cd8bc12e4fcee4259cde73e616b4c28e9b4af862bdf9a`) deterministically binds all 503 final rows, native findings, eligibility derivations, frozen authority, batch inputs, scope resolutions, and the stable seven-row `pass_current` sample. Exact final projection: 438 rewrite-eligible rows; 431 `changed_hash`, 7 `quality_fail_same_hash`, 7 `pass_current`, 28 `blocked_insufficient_text`, 7 `blocked_non_text`, 18 `aggregate_expand_selected`, and 5 `aggregate_deferred`.
  independent review: isolated Grok 4.5 high-reasoning review `…/indexes/t7-independent-review.json` (`18bfcd215c1eee46199bd8d3fe9908ddcb137c31c60ed0f9bd56f398d158bc55`) recomputed the 2,687-file / 34,971,032-byte corpus, all 26 batch closures, every eligible and no-write row, all 34 aggregate decisions, the 222-child deduplication, pass sample, registry state, bound paths, and authority boundary. Decision `ACCEPTED`; all twelve checks true; findings and blockers empty.
  closure `…/indexes/t7-closure.json` (`d5fa493d425dd4555f7c30de1106f278a500770d495d78f252361076640d451b`) permits T8 pending-manifest construction and exact approval presentation only. It does not approve a manifest or authorize any living, child-ingestion, topic-refresh, or cleanup write.
- [x] T8. Build pending manifests and obtain exact approvals
  completed 2026-07-24-1701: deterministic pending candidates `…/indexes/t8-rewrite-candidate.json` (`e7855d62d1ff1ce7c114b2e58204ead41f742694f82b2aaeaa65baf351f8cc15`, 1,125,446 bytes, 438 rows) and `…/indexes/t8-child-ingestion-candidate.json` (`4006ee55f91200ad2c3cbc71be4ef1c29c2ec776905ad98e2a73cadcf77c4ff4`, 302,533 bytes, 221 rows) bind exact sorted source IDs/URLs, unchanged reviewed rows, concurrency/evidence/scope authority, and no-write pending status.
  approval request `…/indexes/t8-approval-request.json` (`d4c617f67b1670ccaa3f56e6016a597e21aa799416d82d4ca083117b08000dc8`) presented both exact whole-candidate hashes and all subset/no-approval alternatives. User decision: **“Approve both exact candidates.”**
  approved projections `…/indexes/t8-rewrite-approved.json` (`87b75ce95026a92fb161872e424bcde29c6d80f157c4caa24d5e3e4987e069e3`) and `…/indexes/t8-child-ingestion-approved.json` (`2a21e15939c5daebc1807637f00859cf6035fc2fcdd740ed0c18c72801aef518`) copy all parent rows unchanged. Closure `…/indexes/t8-closure.json` (`3100bcc3aac3717b99fd92e8df7f53cb0e6548f7077865d35b4db8ddf4833fe0`) authorizes T9 attempts for exactly those 438 rewrites and 221 child ingestions, subject to every T9 fresh-evidence, validation, concurrency, reducer, source-transaction, and route-transaction gate.
- [x] T9. Execute approved existing-source rewrites
  completed 2026-07-25-2229: final reviewed authority `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t9-final-effective-candidates-v1.json` (`903df408dcf86cdfeb95ed01240f83bcf87508faa157c3e0e66d18b376b071ea`) binds 431 accepted existing-source projections: 424 changed-hash, 7 same-hash, 232 routed, and 199 no-topic-match. Seven exact no-writes are bound at `…/indexes/t9-pretransaction-no-writes-v3.json` (`610eeb3272a1a222c1a17176bc884404e0791c4d5d2a641683d43c53493ad891`); all retained living bytes remained unchanged.
  execution: all 431 source transactions reached verified `applied` terminals. Source closure `…/indexes/t9-source-transaction-closure-v1.json` (`c5b8efb85b3964bac957489b4e9dba1a17f597530bf060281c788c4a8a9e8016`) binds events, intents, backups, progress, terminals, and current source-phase bytes. Thirty-four legacy artifacts required the bounded one-time quoted-`schema_version` normalization adapter before the strict product merge; original bytes remain in transaction inputs/backups and the closure preserves the systemic finding. No approved child source was written or received a transaction.
- [x] T10. Verify transactions and living-state closure
  completed 2026-07-25-2229: transaction/living closure `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t9-transaction-living-closure-v1.json` (`1ebc49e496c191ed543f1885364417566b27e218080835d09d31f2ae42d24f28`) independently binds 431 successful source terminals, 431 successful route terminals, every final artifact hash, and the seven byte-identical no-writes. Final state: 503 unique active sources, 250 routed, 253 no-topic-match, 521 relation rows, two dirty topics, zero registry findings, zero product/no-write drift, bound architecture equal to product, and only the accepted pre-existing `todos/TODOs.md` instance-check prerequisite.
- [x] T11. Gate and run affected-topic refreshes
  completed 2026-07-25-1727: user-approved refresh projection `…/indexes/t11-topic-refresh-approved-v1.json` applied exactly 186 pending edges to `agentic-harness-architecture` and 106 to `ai-coding-workflow`, in topic-ID order. Both accepted INDEX/pass pairs are live; both topics are `current` with zero dirty/pending edges. Closure `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t11-refresh-closure-v2.json` (`9fbb6c388900b8cf48395bf202a4bece5f1a3a979e81ef61c8921b4944f682b0`) and independent acceptance `…/indexes/t11-refresh-closure-review-v1.json` (`386bc8f4dfffcf6be537c8fad484f8e02c8e0b0642dc89817aae82448e17ae46`) bind 292 applied edges, zero registry/product/source drift, and 503 preserved source artifacts. One initial wrong-order event was reducer-rejected before writes; v2 rebound the unchanged approved set to canonical pending-edge order.
- [x] T12. Write the durable conformance report
  completed 2026-07-26-0028: durable run report `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-23--living-source-retrospective-conformance.md` is 256,269 bytes / final SHA-256 `87b7cf60ca3ffb2a043369d5480c553d2cc1c91f60a242d28a6dd1525f2965b8`. It binds all 503 final outcomes, 431 source/route event and terminal hash pairs, seven exact pretransaction no-writes, the 221 retired child candidates, final registries, two accepted refreshes, predecessor provenance exception, four retained-root digests, and the explicit retain-all cleanup decision.
- [x] T13. Apply approved cleanup and archive plans
  - historical decision 2026-07-26-0028: user selected **Retain all** at the exact cleanup gate. All four retained roots reverified against the T12 digests; zero files/directories were deleted. The report recorded the decision and cleanup/archival remained deferred.
  - completed 2026-07-28-0222 under later Plan A authority: canonical T2 recovery remains `retained-by-decision`; the corroborating recovery, primary campaign, and predecessor forensic roots were deleted serially after exact approval, matching immediate digest preflights, and qualified absence proof.

## Approach

### T1 — Activate and freeze the execution contract

This plan is already materialized at `.agents/plans/2026-07-23-2322_living-source-retrospective-conformance.md`. At execution start, require `Status: PENDING`, all T1–T13 checkboxes still open, and no prior completion annotations; halt if execution has already started or the plan has concurrent edits. Set it to `IN_PROGRESS`, check tasks only after their observable result exists, and let only the orchestrator annotate it. Use `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/` as the sole new campaign root; require it absent or empty and exclusive-create every artifact.

After setting `IN_PROGRESS`—but before checking T1—exclusive-create `preflight/execution-contract.md` as an immutable byte-for-byte snapshot of the repository plan selected for execution. Read it back, freeze its SHA-256 for every campaign index/approval, then mark T1 complete; later lifecycle annotations change only the repository plan, never the frozen contract. Persist deterministic JSON as canonical sorted-key UTF-8 plus one LF, use logical `vault://atlas/...` paths, bind every input/output by SHA-256, and preserve validator findings losslessly from each owning API—never collapse them into a smaller campaign-only diagnostic shape. Do not add campaign helpers, databases, alternate plans, or product code.

### T2 — Freeze and preflight the current product

Create a product-baseline index containing current hashes for the architecture, source/refresh skills, shared quality/registry contracts, source-summary eval/template, Atlas command stubs used here, and `scripts/atlas_{quality,source,state,url,instance}.py`. Require `vault://atlas/ARCHITECTURE.md` to byte-match `.agents/ARCHITECTURE.md`; any later drift in this behavior-owning surface or the bound architecture stops the campaign rather than silently adopting a new baseline. Run the existing tests below as verification, but do not make unrelated test-file bytes part of the runtime freeze.

Run from the app root:

```text
python3 -m unittest tests.test_atlas_quality tests.test_atlas_source tests.test_atlas_state tests.test_atlas_url tests.test_atlas_instance tests.test_atlas_harness_surface
python3 scripts/atlas-instance.py check --name atlas
```

The tests must pass. The instance check may report only the known missing `vault://atlas/todos/TODOs.md` prerequisite; any other finding stops.

Exercise the real deterministic seams under a campaign-owned fixture path: empty/media/unbacked evidence rejection; exact `same-hash|changed-hash` classification; one-target apply; zero-target no-op; rollback/recovery; exclusive-create collision; and verified delete. Adapt the active Atlas connector/profile to `atlas_source.ConnectorPort` in evaluator-local code only, prove exact-byte read/create/write/delete acknowledgements, and persist no adapter. Also run the five frozen fresh-context entry cases for inaccessible text, insufficient text, aggregate scope required, page-only without child bodies, and a normal article that must not trigger an aggregate question. Any failure opens a separate product-repair plan and invalidates this campaign root.

### T3 — Freeze the current 503-source cohort

After preflight, read the living source manifest, all referenced artifacts, and the three registries through `vault://atlas/...`; require 503 active unique source IDs, no missing artifacts, valid normalized canonical URLs/derived IDs, manifest/frontmatter identity, and zero `atlas_state.validate_documents` findings. Freeze source-ID-sorted rows with source identity, sequence, URL, artifact, route/status fields, living content hash, and exact manifest-row/artifact hashes. Bind the complete MANIFEST/TOPICS/RELATIONS/VOCAB bytes and the source-ID union hash.

This execution-time freeze is authoritative. If the cohort is no longer exactly 503 or any product/registry byte changes while freezing, stop for a new scoped plan; do not force old counts onto new living state.

### T4 — Resolve the predecessor cleanup gate

Recompute the predecessor plan/report hashes and a deterministic relative-path/size/file-hash digest of `vault://atlas/tmp/source-quality-revisit-2026-07-21/`. Present those exact values, the prior final-state counts, and the unreconstructible T5 transaction-provenance exception. Ask for one explicit disposition:

- approve deletion of that exact root/digest while accepting that only final-state replay survives; or
- defer cleanup and continue with the old plan/root untouched.

Approval records the exception in the predecessor durable report, verifies the root deletion, completes its T7/Completion Summary, and archives the old plan. Deferral is allowed and does not block fresh revalidation, but the old root remains excluded from semantic evidence and must be offered again at T13. Never invent retroactive transaction records.

### T5 — Revalidate all frozen sources from fresh text

Split the source-ID-sorted cohort into bounded batches of at most 20 rows and dispatch the batches in one parallel wave within the harness concurrency cap. Give every fresh agent only the frozen product contract, its packet, the row-bound living artifacts, and this evidence boundary; agents must not read sibling outputs or the predecessor temp root.

For each source, the agent must:

1. Recheck packet, product, manifest-row, and artifact hashes.
2. Open only the canonical URL, preferring static/reader text and using browser rendering only when needed. Persist complete extracted canonical UTF-8 source text and textual URLs, never transport wrappers, truncation markers, media, binary assets, or model reconstruction.
3. Emit a no-write disposition when text is inaccessible, unauthorized, empty, non-text, fetch-failed, or insufficient for a faithful summary.
4. If the supplied page is genuinely an index whose child pages hold the substantive content, retain complete supplied-page text plus normalized child URLs and mark it pending scope; do not read child bodies.
5. Otherwise validate evidence with `atlas_quality.resolve_effective_content_hash` and classify only through `atlas_source.classify_hash_transition`. A complete comparable equal hash is `same-hash`; a complete comparable unequal hash is `changed-hash`; invalid/incomplete evidence or disagreement between living manifest and artifact hashes is no-write/incomparable.
6. For `same-hash`, run the canonical seven-item checklist and `atlas_quality.validate_summary` against the living artifact. Valid summaries pass current; findings make the row a possible same-hash rewrite. For `changed-hash`, mark the living summary stale without reviewing or reusing its prose.

Persist one capture/evidence bundle and one row result per source, plus a batch index that binds their hashes and counts. Each row must carry enough information to independently prove identity, capture completeness/projection, native validator findings, transition, checklist binding, disposition, eligibility, and proposed `same-hash|changed-hash` path. Only same-hash quality failures and proven changed-hash rows are rewrite-eligible; all other outcomes are exact no-writes. Batch agents make no living, registry, topic, or product writes.

### T6 — Resolve aggregate-page scope and child candidates

Independently merge all batch outputs, require exactly the 503 frozen source IDs once each, verify every row/hash/count, and produce the preliminary cohort index plus a source-ID-sorted aggregate candidate index. Generate deterministic index bytes twice before exclusive-create.

Present aggregate candidates to the user in groups of at most 20. For each parent require exactly one of:

- `page-only` using the already-frozen complete supplied-page text;
- `expand` with an exact subset of the frozen normalized child URLs; or
- `defer`, an exact no-write for this campaign.

Do not infer a default, recursively crawl, or add a child URL not frozen in the candidate. For every page-only parent, dispatch a fresh scope-resolution agent with only the frozen supplied-page evidence, living baseline, and exact decision; without refetching or reading children, it performs T5’s hash classification and same-hash checklist/quality validation and emits one finalized replacement row bound to the pending row and decision. Expand/defer decisions likewise emit finalized no-write scope-resolution rows. Normalize and deduplicate selected child URLs globally, merge all selecting parent IDs, reject source-ID collisions, and mark children already present in the frozen cohort as existing no-writes. The remaining new child rows form a pending expansion-candidate index; no child body is opened yet.

### T7 — Build and independently review cohort closure

Project non-aggregate rows plus scope resolutions into one deterministic source-ID-sorted 503-row conformance report. Recompute counts from rows and require eligibility to be derivable only from complete evidence, valid identity/concurrency bindings, and the two allowed rewrite paths. Bind every capture, evidence file, checklist, packet, scope decision, and child candidate by path/hash.

Dispatch a distinct read-only reviewer with the frozen product/state and all campaign indexes. It must independently verify complete cohort membership, packet arithmetic, every eligible row, every blocked/incomparable reason, all aggregate decisions/child deduplication, and a stable deterministic sample of pass-current rows. The reviewer returns final review bytes only; the orchestrator validates and exclusive-creates them. Acceptance opens T8. Execution or product rejection freezes this root and opens a separate recovery/repair plan—there is no in-root rerun or weakening of checks.

### T8 — Build pending manifests and obtain exact approvals

From reviewer-accepted rows only, build deterministic pending candidates for:

- existing-source rewrites, carrying the frozen row, current artifact/manifest hashes, complete evidence, checklist when required, and proposed transition; and
- new child ingestions, carrying canonical URL, derived source ID, all selecting parent IDs, and scope-decision bindings.

Pending bytes authorize no living write. Present each candidate’s exact path, SHA-256, byte/row counts, and sorted IDs/URLs. The user may approve the exact whole candidate hash, an exact deterministic source-ID subset, or none. Persist every nonempty approval as a separate canonical projection of parent rows with its own hash; execution must consume only these approved projections. No self-approval, implicit approval, or use of superseded manifests is permitted.

### T9 — Execute approved existing-source rewrites

Generate and review approved rows in evidence-isolated batches, but apply living writes sequentially because they share MANIFEST/TOPICS/RELATIONS. Verify the revised product baseline and approved projection once per batch; immediately before each write, recheck only that row's artifact/manifest concurrency and the registry state produced by the preceding outcome.

For each existing-source rewrite, give an OMP `openai-codex/gpt-5.6-terra:xhigh` worker only the complete fresh T5 evidence and immutable identity/acquisition fields already bound by the T7-accepted and T8-approved row. Draft from that evidence, run the seven-item checklist and `atlas_quality.validate_summary`, and permit at most one targeted revision. A distinct Terra reviewer compares the complete candidate against the same evidence; only rejected rows receive one focused correction and re-review.

This is deliberately lean: T9 does not refetch evidence already proven complete and current for this campaign, rerun T5/T7 corpus closure, conduct cross-model comparisons, or add campaign-specific mutation fuzzing. Deterministic checks bind inputs/outputs and protect living writes; semantic review protects summary quality.

The earlier 221-row child-ingestion approval remains part of T8 history but is not execution authority after the 2026-07-24-1752 existing-sources-only override. Record those rows as `retired_by_user_scope` with no fetch, identity allocation, transaction, or living write.

For every successful rewrite:

1. Use `atlas_state.reduce_event` and `atlas_source.merge_artifact` to build the source candidate; require zero candidate artifact/registry validation findings before writing.
2. Persist a canonical `atlas_source.build_event_record` under the campaign root, then use `build_transaction_plan`, `execute_transaction`, and `recover_transaction` for the source transaction.
3. Advance only after a verified `applied|no-op` source terminal; then perform bounded routing, reduce/render it with the existing state/source helpers, require zero route-candidate findings, and execute a separate route transaction, including a zero-target no-op when appropriate.
4. Call `build_successor_plan` only for a verified `aborted|rolled-back` terminal using its exact terminal bytes. Permit one recoverable successor. If source recovery still fails, halt with no committed row; if route recovery fails after a committed source transaction, preserve the valid source state and all records, emit a blocked outcome, stop before T10, and open a separate recovery plan to finish routing or explicitly authorize compensation. The current executor never invents a compensating write.
5. Revalidate complete registries and persist one outcome ledger binding approval, evidence/checklist, pre/post hashes, event/transaction terminals, revision count, affected topics, and findings.

### T10 — Verify transactions and living-state closure

Using the existing modules and the preflighted connector—not outcome-ledger assertions alone—independently traverse every started source and route attempt. Enter T10 only when T9 has no blocked outcome. Verify event bytes, intent identity, target order, input/output hashes, backups, prepared/progress records, terminal exclusivity, rollback/successor chains, and current target bytes. Every completed mutation must end with successful source and route terminals; every pretransaction no-write must have no transaction and byte-identical pre/post living hashes. Missing provenance, manual conflict, malformed/colliding records, unrecognized current bytes, or failed rollback stops completion and cleanup.

Write one transaction-closure index preserving mutation kind `rewrite`, transaction kind (`source|route`), attempt/predecessor linkage, terminal hashes, target hashes, and native findings. Bind the 221 child rows once as `retired_by_user_scope`, outside the transaction set. Then run full `atlas_state.validate_documents`, verify every manifest artifact path/hash/frontmatter identity, and rerun the instance check allowing only the known TODO prerequisite. Compute affected topic IDs from exact pre/post TOPICS rows and RELATIONS edges across successful writes.

### T11 — Gate and run affected-topic refreshes

Build a topic-refresh candidate only from affected topics that are reducer-derived `dirty` and have a nonempty complete current pending-edge set. Exclude affected topics that are current or pending-edge-empty; they must never authorize `/atlas-refresh`.

If candidates exist, present their exact path/hash and rows and require approval of the exact candidate or an exact topic-ID subset. Persist a separate approved projection; withheld approval records deferral. If none exist, record not-applicable without asking. Refresh approved topics only, in topic-ID order, through `skill://atlas-refresh`, rechecking the product, complete pending-edge/contributor projection, current dirty state, and cumulative registry hashes before each refresh. Revalidate after each; never refresh all topics by default.

### T12 — Write the durable conformance report

Write `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-23--living-source-retrospective-conformance.md` using the existing run-log frontmatter/section conventions. It must bind the frozen product/cohort, exact 503 disposition counts, aggregate decisions, pending and approved manifests, per-row outcomes, transaction-closure index, registry validation, affected-topic/refresh decision, predecessor provenance exception, and residual no-write/deferred rows. Include a compact transaction table with source/route event and terminal hashes for every successful write so it remains the audit index after temporary recovery records are removed.

Compute and verify the report hash, then compute deterministic directory digests for the new campaign root and any still-retained predecessor root. Present exact paths, digests, counts, and the tradeoff: deletion removes transaction backups and detailed captures but preserves the durable report and final living state.

### T13 — Apply approved cleanup and archive plans

Require explicit approval naming each exact root/digest to delete; no approval means no deletion. For approved roots, verify every successful transaction is terminal/recoverable and represented in the durable report, confirm no evidence still needed for a pending approval or deferred refresh exists only there, delete exactly the approved roots, and verify absence. Append the cleanup decision/results and final hashes to the appropriate durable report(s).

Only after all requested cleanup is resolved, all task criteria pass, and no approval/recovery gate remains: complete each plan’s Completion Summary, set `Status: DONE`, and atomically move it to `.agents/plans/archive/`. If cleanup is deferred, keep the relevant plan/root `IN_PROGRESS`; do not archive around the open gate.

## Orchestration model updated 2026-07-24-1752

OMP GPT-5.6 Sol xhigh owns campaign orchestration, authority selection, deterministic validation, approval boundaries, transaction execution, and final review. OMP task subagents using `openai-codex/gpt-5.6-terra:xhigh` own evidence-isolated source drafting and semantic review. No Grok CLI process may generate, review, refine, or authorize T9 output after this override.

Use bounded packets and return hash-bound files rather than source bodies to the orchestrator. Generator and reviewer contexts receive only their packet, approved fresh evidence, required product contracts, and post-draft taxonomy snapshot; never sibling prose or living artifacts. Mechanical hashing, exact-byte comparison, reducers, transaction execution/recovery, and registry validation remain local. The pre-override Grok T9 traces are forensic only and cannot authorize a living write.

## Execution grouping for a ~200k context window

Use six resumable execution blocks. Persist each block’s compact handoff as hashes, counts, decisions, and next preconditions under the campaign root; the next block rereads those artifacts rather than inheriting conversation history.

| Block | Tasks | Recommended execution shape | Estimated peak live context |
|---|---|---|---|
| A — Foundation | T1–T4 | One orchestrator performs activation, product preflight, cohort freeze, then stops at the predecessor cleanup decision. | 50k–90k tokens |
| B — Revalidation | T5 | Thin orchestrator plus bounded fresh workers. Keep each packet at ≤20 rows and target ≤120k tokens; make unusually long sources singleton packets and close/continue any worker before 150k. | Orchestrator 30k–60k; worker 40k–150k |
| C — Scope and approval | T6–T8 | One orchestrator merges indexes; fresh agents finalize page-only rows; one independent reviewer checks closure. Page aggregate decisions and rewrite/expansion approvals remain explicit pauses. | 70k–140k tokens |
| D — Mutation and closure | T9–T10 | Thin orchestrator runs bounded Terra generation/review batches, then applies accepted rows in global order and uses a distinct verifier for transaction closure. Never accumulate source bodies in the orchestrator. | Orchestrator 40k–80k; worker/reviewer 40k–140k |
| E — Topic refresh | T11 | Separate approval-bound session because current pending edges and dirty state must be reread immediately before refresh. | 30k–80k tokens |
| F — Report and cleanup | T12–T13 | One session writes/verifies the durable report, then pauses for exact cleanup approval before deletion/archive. | 60k–120k tokens |

Treat 150k tokens as the operational ceiling, leaving roughly 25% of a 200k window for tool output, reasoning, and recovery. The plan plus targeted product contracts should consume under 40k; the orchestrator must read row indexes and hashes, not all 503 evidence bodies. Start a fresh context after any external approval pause, at a block boundary, or whenever the active context approaches 150k. Blocks may share one outer execution run, but approval gates must never be crossed automatically.

## Critical files & anchors

- `scripts/atlas_source.py` — `classify_hash_transition`, artifact/route rendering, `ConnectorPort`, and transaction build/execute/recover/successor APIs; use these rather than campaign reimplementations.
- `scripts/atlas_state.py` — `reduce_event`, `validate_documents`, registry paths, and transaction-recovery planning; all living registry changes flow through this reducer.
- `scripts/atlas_quality.py` — `resolve_effective_content_hash`, checklist/summary validation, and native finding serialization; this remains the sole text-identity/quality owner.
- `.agents/skills/atlas-refresh/SKILL.md` — dirty-topic/pending-edge authority and refresh transaction sequence for T11.
- `.agents/plans/2026-07-21-1613_living-source-quality-revisit.md` — predecessor T7 gate and completion/archive criteria; never use its temp artifacts as source content.

## Verification

1. **Product and connector preflight:** run the two T2 commands from `/Users/kim/dev/atlas/app`; require unit-test exit zero and only the known TODO prerequisite from the instance check. Record exact stdout/stderr hashes and verify no product or living byte changed during fixture smokes.
2. **Entry behavior:** run the five selected cases from `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` in isolated fresh contexts. Expected observable results: inaccessible/thin → no write; aggregate → one page-only/expand decision and no child-body access; page-only → no child bodies; normal article → no scope question.
3. **Cohort closure:** independently require 503 unique frozen IDs and exactly one final row per ID; all packet, capture, evidence, checklist, decision, and row hashes must resolve, counts must recompute from rows, and product/living baselines must remain frozen until approved mutations begin.
4. **Mutation behavior:** for every approved existing-source row, verify one of two observable outcomes: byte-identical no-write with a reason, or validated source and route terminals whose output hashes equal current living bytes. Bind all 221 retired child rows to the later user override and require zero child transactions or living rows. Exercise at least one zero-target route no-op when naturally produced; never fabricate a fixture living write.
5. **Failure behavior:** the campaign-local transaction smoke must prove that an injected target failure rolls back or creates one hash-linked successor only after `aborted|rolled-back`; an unrecoverable source failure halts with no commit, while an unrecoverable route failure after source commit preserves records/state and opens the separate recovery path defined in T9.
6. **Final state:** rerun complete registry validation and `python3 scripts/atlas-instance.py check --name atlas`; compare manifest/artifact identities, transaction closure, topic refresh outputs, durable-report hashes, and approved cleanup results. No campaign is complete while a started transaction, pending approval, deferred required decision, or approved-but-unverified deletion remains.

## Assumptions & contingencies

- The product behavior is already final; this plan applies it to living data. If the T2 baseline or preflight fails, stop and open a separate product-repair plan, then restart conformance under a new root rather than rebasing this campaign.
- The execution-time cohort must still contain exactly 503 valid active sources. Content changes before T3 are accepted only by the new freeze; count/identity/schema drift requires a new scoped plan. Any post-freeze drift halts without rebasing.
- Fresh canonical text is semantic authority. Historical captures, old source prose for changed-hash rows, topic/pass prose, request text, and model priors never fill evidence gaps.
- The active connector/profile must provide exact-byte create/read/write/delete semantics compatible with `ConnectorPort`. If the runtime cannot prove that seam, halt before source work; do not add a product-owned connector as campaign scope.
- The predecessor transaction gap is irreparable. Cleanup may be approved only with the explicit recorded provenance loss; otherwise retain its plan/root.
- All aggregate, rewrite, expansion, topic-refresh, and cleanup approvals are external gates. Empty/withheld approval always means no write, no refresh, or no deletion respectively; the executor never chooses on the user’s behalf.

## Recovery authority (2026-07-24-1350)

Independent review blocked promotion past T3: T2 entry cases were static contract/API assertions rather than isolated fresh-agent runs, and `preflight/fixtures/` residue remained. Do not treat parent `indexes/t2-preflight.json` (SHA-256 `d09332ce2bab5322c3077a6ff94d1146b1fda26c5f58c78f4ee2a6fe6d74ec25`) as T2 authority.

**Required before T4 (completed via recovery plan `.agents/plans/2026-07-24-1345_t2-entry-preflight-recovery.md`):**

| Artifact | Path | SHA-256 |
|---|---|---|
| Recovery plan | `.agents/plans/2026-07-24-1345_t2-entry-preflight-recovery.md` | (repository plan; status DONE) |
| Recovery root | `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/` | — |
| Authoritative T2 | `…/t2-recovery/indexes/t2-preflight-recovery.json` | `cd2762eb612e99c41d46cb39f4a99cef253752d0b7a61e4fb1856871feb44c6d` |
| T3 rebind | `…/t2-recovery/indexes/t3-rebind.json` | `0bd2d49e6baae1d39800cea23aabe0b301c9ea7ce1d5a28f95c36ef7a61c3f08` |
| Parent T2 pointer | `…/conformance-2026-07-23/indexes/t2-preflight-recovery.json` | `040b49a9389bfb3a2993f7003b7b038bff42e67d37e9a1f6cd5f1989ed28e97d` |
| Parent T3 pointer | `…/conformance-2026-07-23/indexes/t3-rebind.json` | `d05223be215f28838e7e7a517c4aa914afd06766ac6442ba35db438ace95269a` |
| Cohort freeze (unchanged) | `…/indexes/cohort-freeze.json` | `3ded74a6458c61f556c1e4db020ebd7d9eb6a49fd5ea5cacc4a068e0827c5a4e` |
| Deficient T2 (forensic only) | `…/indexes/t2-preflight.json` | `d09332ce2bab5322c3077a6ff94d1146b1fda26c5f58c78f4ee2a6fe6d74ec25` |

Fixtures under `preflight/fixtures/` were removed (31 files); verified absent. Five entry cases ran as isolated read-only subagents and exact-matched eval expectations. Product/living drift recheck at rebind: zero. T4 may proceed using recovery T2 + T3-rebind authority; do not silently patch or re-freeze parent T2/T3 indexes.

The later Grok-driven recovery under `vault://atlas/tmp/living-source-retrospective-conformance-t2-recovery-2026-07-24/` is retained as independent corroboration only. To preserve a single chain of authority, all subsequent tasks consume the parent-root pointers at lines 209–210 and their bound 2026-07-24-1350 recovery artifacts.


## Completion Summary

The retrospective conformance campaign revalidated the complete frozen 503-source cohort from fresh text, applied 431 approved existing-source rewrites through recoverable source and route transactions, retired all 221 child candidates without writes, refreshed the two exact affected topics, and reached terminal cleanup.

**Delivered**
- Final cohort: 503 unique active sources; 250 routed; 253 no-topic-match; 431 successful source terminals; 431 successful route terminals; seven exact pretransaction no-writes; zero registry findings.
- Final topic state: `agentic-harness-architecture` and `ai-coding-workflow` are current after 292 total approved pending edges; zero pending edges remain for those topics.
- Durable report: `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-23--living-source-retrospective-conformance.md` — terminal revision `sha256:ede6fc2fe10257caaad8d5a82707bedc14edf4f88670953cded643ff03363b09`.
- The report preserves all 503 outcomes, successful source/route event and terminal hashes, no-write rows, retired child decisions, accepted refreshes, cleanup authority, terminal root outcomes, and final predecessor archive destinations.

**Terminal roots**
- Retained: canonical T2 recovery `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery` at `sha256:877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1`.
- Deleted with matching same-digest preflights and qualified original/quarantine absence: corroborating T2 recovery `sha256:41782e802043363148f0e4a055b7d40fc9384d92979aade0c3d835690ba7b001`; primary campaign `sha256:17f7e41cd27a92472f85bcb5e6d9bdd906b31aeaf41b531ee3d1ec6f44cf244e`; predecessor forensic `sha256:17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a`.
- The predecessor forensic deletion permanently removed the only remaining traces for two rewrites whose required transaction records and exact backups never existed. This loss was explicitly acknowledged; no reconstruction was fabricated.

**Archived predecessors and destination**
- Quality revisit: `.agents/plans/archive/2026-07-21-1613_living-source-quality-revisit.md`.
- Canonical T2 recovery: `.agents/plans/archive/2026-07-24-1345_t2-entry-preflight-recovery.md`.
- This plan: `.agents/plans/archive/2026-07-23-2322_living-source-retrospective-conformance.md`.
- The known missing `vault://atlas/todos/TODOs.md` instance seed remains an accepted pre-existing finding; no other bound-instance finding was introduced.
