# Atlas framework tools, retained-root closure, and thin-source campaign

**Datetime**: 2026-07-26-1657
**Scope**: Atlas product tooling/evals, retained campaign-root closure, and living thin/error-source decisions
**Summary**: Productize the smallest durable agent-tool surface proven by campaign failures, use it to verify and close retained historical campaigns before exact cleanup, then run a separate decision-gated campaign for thin/error sources. The executor materializes two repository plans because product/cleanup closure and living-source remediation have different authorities, mutation seams, and completion lifecycles.
**Status**: DONE

## Context

Atlas currently has deterministic URL, quality, state, source-rendering, and transaction cores, but no product-owned agent tool that resolves the active `vault://atlas/` profile, returns undecorated exact bytes/JSON, performs strict compare-and-swap, or advertises those capabilities. That gap forced campaign agents to receive a parent-supplied host path and one-off Python for packet reads and canonical JSON writes. The requested end state is two serial repository plans: first, promote the minimal provider-neutral tool/eval surface and use it to audit, delete, and close the retained campaigns; second, review every current active source for thin/error behavior, obtain explicit decisions in five-row batches, and mutate only the approved affected rows.

## Execution intent

This file is the sole program coordinator. It starts and observes the two materialized child plans in strict order, mirrors their terminal task outcomes, and archives last. It does not duplicate product implementation authority from Plan A or living-instance mutation authority from Plan B.

Exact child plans:

- Plan A: `.agents/plans/archive/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md`
- Plan B: `.agents/plans/archive/2026-07-27-0153_atlas-thin-error-source-review.md`

Both children begin `PENDING`. Starting umbrella T1 changes Plan A—not Plan B—to `IN_PROGRESS`. Plan B may start only after Plan A is `DONE` and exists under `.agents/plans/archive/`.

## Tasks

- [x] T1. Bind materialized child plans and freeze authorities
- [x] T2. Observe Plan A red tool and behavior evals
- [x] T3. Observe Plan A durable contract definitions
- [x] T4. Observe Plan A tool-family implementation
- [x] T5. Observe Plan A agent-surface qualification
- [x] T6. Observe Plan A retained-root authority audit
- [x] T7. Observe Plan A approved retained-root dispositions
- [x] T8. Observe Plan A predecessor closure and archival
- [x] T9. Observe Plan B current-source cohort freeze
  - completed 2026-07-28-0905
- [x] T10. Observe Plan B fresh capture and assessment closure
  - completed 2026-07-28-1809
- [x] T11. Observe Plan B five-row user decision closure
  - completed 2026-07-29-0259
- [x] T12. Observe Plan B approved-effect execution closure
  - completed 2026-07-29
- [x] T13. Observe Plan B refresh, report, cleanup, and archival
  - completed 2026-07-29-1058

## Approach

### Materialized authority split

| Child | Exact active path | Owns | Initial state |
|---|---|---|---|
| Plan A | `.agents/plans/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md` | Product architecture/contracts/code/evals, isolated qualification, four retained-root dispositions, three eligible predecessor plans | `PENDING` |
| Plan B | `.agents/plans/2026-07-27-0153_atlas-thin-error-source-review.md` | Fixed current-source cohort, fresh source assessment, user resolutions, approved source/route effects, affected-topic refresh, durable report, new campaign-root cleanup | `PENDING` |

The split is load-bearing. Plan A may author product-owned files and operate on the four historical temporary roots only through its explicit cleanup protocol. Plan B may mutate current living source/topic state only after Plan A is archived and its own pre-start rebind passes. Neither child may create another umbrella.

### Program gates

1. **Start Plan A only.** Verify both child files and these links, change Plan A to `IN_PROGRESS`, and freeze the product/profile/bound-instance authorities required by its T1. Leave Plan B byte-identical and `PENDING`.
2. **Run Plan A T2–T5.** Red evals precede contracts and implementation. Architecture changes precede core contracts, owning skills, and unchanged thin command stubs. Product-to-bound architecture sync occurs only after direct tests and isolated qualification pass.
3. **Run Plan A T6–T8.** Re-audit all four roots by fresh digest and authority. The canonical T2 recovery root is retained by decision. The primary, corroborating, and predecessor forensic roots receive independent exact `delete|retain` decisions; forensic deletion additionally requires the irreversible-provenance-loss acknowledgment. An explicit Plan-A `retained-by-decision` is terminal; an unanswered/withheld row keeps the owning predecessor and Plan A open.
4. **Archive Plan A before Plan B.** Plan A may become `DONE` only after its tasks, verification, Completion Summary, selected root dispositions, and eligible predecessor archives are terminal. Move it atomically to `.agents/plans/archive/`; a `DONE` child left active does not unblock Plan B.
5. **Rebind and start Plan B.** While Plan B is still `PENDING`, record its read-only pre-start rebind in the plan execution log. Only a passed rebind permits `IN_PROGRESS`, exclusive campaign-root creation, and T9.
6. **Run Plan B T9–T13.** Membership freezes at the lock-linearized `source.snapshot_active` observation. Fresh assessment, explicit row intent, user resolution, projection approval, effect execution, affected-topic approval/refresh, durable reporting, and campaign cleanup remain distinct hash-bound authorities.
7. **Archive Plan B, then this umbrella.** Finalize the external report and delete the Plan-B campaign root before Plan B `DONE`. After its atomic archive, update this file with both child archive paths/hashes and the final report binding, complete every task/criterion, append Completion Summary, set `DONE`, and atomically archive this umbrella last.

### Confirmed cross-plan contracts

- The product surface remains provider-, harness-, model-, and storage-neutral. Persisted living references use logical `vault://atlas/…` URIs only.
- Plan A adds one deep façade over existing pure owners, including lock-linearized `source.snapshot_active`, deterministic `quality.validate_fresh_assessment`, and recoverable `refresh.execute|refresh.recover`. Network fetch/search and model calls remain harness capabilities.
- Deletion is exact-row, digest-bound, no-clock-expiry, quarantine-then-erase. A missing/invalid approval authorizes nothing; drift invalidates only its row.
- Plan B treats the historical 503/MANIFEST tuple as provenance, not current-state authority. Later additions after the T9 snapshot cutoff belong to another campaign.
- `FreshSourceAssessment` stores orthogonal capture, representation, identity, page-form, page-summary-adequacy, and explicit-intent-fit observations. Flat source classes are derived findings only and may coexist.
- Row decisions are append-only intent, not mutation approval. Whole-cohort projections account for every frozen row; approval is hash-bound, row-local, and one-use.
- Expected source-level defer/error/no-op outcomes may be terminal residuals. Shared-integrity failure, unresolved source/route recovery, `manual-conflict`, or affected-topic refresh failure blocks Plan B closure.
- The one durable Markdown run report embeds the compact exhaustive row/effect ledger. Report revisions form a predecessor-hash append chain; Plan B Completion Summary owns the final report hash.

### Ordered task map

- **T1:** Validate the materialized children and umbrella links; start Plan A and freeze its authorities.
- **T2:** Complete Plan A T2 and record red eval fixtures/results.
- **T3:** Complete Plan A T3 and record architecture/contract hashes.
- **T4:** Complete Plan A T4 and record implementation/test hashes.
- **T5:** Complete Plan A T5, isolated qualification, architecture sync, and provider-neutrality evidence.
- **T6:** Complete Plan A T6 fresh four-root authority projection and independent review.
- **T7:** Complete Plan A T7 row decisions, approved deletions/retentions, terminal report amendments, and absence proofs.
- **T8:** Complete Plan A T8 truthful predecessor amendments, archive order, Completion Summary, and Plan A archive.
- **T9:** Complete Plan B T9 pre-start rebind, activation, fixed-cohort snapshot, and freeze validation.
- **T10:** Complete Plan B T10 all-row fresh capture, assessment, intent clarification, targeted blind review, and candidate discovery.
- **T11:** Complete Plan B T11 five-row decision rounds, candidate-union confirmations, whole-cohort projection, and final approval.
- **T12:** Complete Plan B T12 prepared material, one-use effect claims, source/route transactions or named no-writes, recovery, and member/effect receipts.
- **T13:** Complete Plan B T13 approved affected-topic refreshes, final checks, external report append chain, root cleanup, Completion Summary, and archive.

### Skill outcomes captured

- **Grilling:** settled every T1–T13 authority, error, approval, drift, recovery, retention, and archive branch; no open executor choice remains.
- **Domain modeling:** established `product contract`, `bound instance`, `Atlas tool façade`, `connector`, `profile`, `active-source snapshot`, `FreshSourceAssessment`, `derived finding`, `row intent`, `resolution decision`, `mutation projection`, `effect claim`, `member receipt`, `coalesced effect receipt`, `source residual`, `refresh projection`, and `cleanup defer`.
- No standalone ADR is required. `.agents/ARCHITECTURE.md` remains the canonical durable framework authority; the child plans record implementation sequencing and campaign-specific decisions.

## Critical files & anchors

- `.agents/plans/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md` — Plan A implementation and historical-cleanup authority.
- `.agents/plans/2026-07-27-0153_atlas-thin-error-source-review.md` — Plan B living-source/refresh/report/cleanup authority.
- `.agents/ARCHITECTURE.md` — canonical framework invariants, vocabulary, write sets, and tool seams.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — reducer, transaction, refresh, call-envelope, and recovery contracts.
- `scripts/atlas_url.py`, `scripts/atlas_quality.py`, `scripts/atlas_state.py`, `scripts/atlas_source.py` — existing pure owners Plan A must deepen rather than duplicate.
- `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-23--living-source-retrospective-conformance.md` and `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-21--living-source-quality-revisit.md` — durable historical cleanup/closure authorities.

## Verification / Done criteria

- [x] Plan A is `DONE` under `.agents/plans/archive/`, with all T1–T8 tasks/criteria observed, product/bound architecture byte-identical, direct tests and isolated behavior qualification passing, and no provider-specific product branch.
- [x] The canonical T2 recovery root is retained-by-decision; every other historical root has its independently approved terminal disposition, fresh digest binding, durable-report amendment, and deletion absence proof when applicable.
- [x] The three eligible predecessor plans satisfy their own completion contracts and exist only under `.agents/plans/archive/`; the two unrelated active plans remain active and unchanged.
- [x] Plan B started only after a passed pre-start rebind and archived Plan A; its T9 freeze accounts exactly once for every source active at the snapshot cutoff.
- [x] Every frozen row has terminal fresh assessment accounting; every flagged/intent-clarification row has explicit user authority; pending silence never becomes page-only, defer, or approval.
- [x] Every approved effect has one terminal member/effect receipt; changed/new sources have verified source then route closure; expected no-writes have no transaction; no unapproved parent/source byte changed.
- [x] Every receipt-derived affected dirty topic reached `current` through an exact approved refresh projection; empty refresh is an explicit no-op; no blocked/refreshing/manual-conflict state remains.
- [x] Final state/quality checks pass with no unexplained finding beyond the exact pre-existing missing `vault://atlas/todos/TODOs.md` baseline.
- [x] The external thin/error report embeds the compact exhaustive ledger, final state/receipt bindings, residual source outcomes, report append chain, and exact campaign-root cleanup disposition.
- [x] The Plan-B campaign root and any deterministic quarantine are absent after exact approved cleanup; retention/awaiting-decision is not labeled completion.
- [x] Plan B is `DONE` under `.agents/plans/archive/`; this umbrella records both child archive paths/hashes and the final report binding, has all tasks/criteria checked plus Completion Summary, and archives last.

## Assumptions & contingencies

- The child plan files are planning artifacts only. Their creation does not start execution, authorize living mutation, approve deletion, or satisfy umbrella T1.
- The initial mutation adapter is local POSIX `local-fs`. Unsupported, ambiguous, non-local, non-locking, non-atomic-rename, or non-durable profiles remain read-only and block every mutation/delete/transaction; no host-path fallback exists.
- The current 503/MANIFEST tuple and historical campaign records are provenance only. Plan B uses current lock-linearized state and never reads a deleted predecessor root as semantic evidence.
- `replace-source-url` is additive because Atlas has no legal retirement/reactivation transition. The original stays byte-identical; an archived selected candidate remains an explicit no-op.
- Plan-A historical roots may terminalize `retained-by-decision`; unanswered/withheld rows may not. Plan-B campaign-root retention/awaiting-decision is deliberately not completion. Source-level defer and named source errors are different terminal residuals.
- Semantic work uses fresh default task contexts after a resolved-model pilot. Any lane resolving to Grok 4.5 xhigh is replaced with GPT-5.6 Terra xhigh; provider/model identity remains execution metadata only.
- Any material drift invalidates the narrowest dependent authority: root row, source row/effect, refresh topic, or report cleanup approval. No silent rebase, force-write, fabricated provenance, compatibility shim, or second umbrella is permitted.


## Plan A terminal handoff — 2026-07-28-0228

- Plan A archived atomically at `.agents/plans/archive/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md`, SHA-256 `5dddc59a3fd362282ce79408d29b480c0c3aea9364842865a32d5ae97544448b`.
- Its three eligible predecessors are archived at the paths and hashes bound in the Plan A Completion Summary. The final historical reports are retrospective `sha256:ede6fc2fe10257caaad8d5a82707bedc14edf4f88670953cded643ff03363b09` and quality revisit `sha256:a10401506d1815a260a7c6eaf4d47d2be7ab9dd2dc8f57f605b969bc27764877`.
- Canonical T2 recovery is retained by decision. Corroborating recovery, primary campaign, and predecessor forensic roots are deleted with matching digest preflights and qualified absence proof; the permanent predecessor provenance loss remains explicitly recorded.
- Final Plan A verification: 132 required tests passed, façade capabilities exposed adapter `atlas-local-fs-cas-v1` and all 26 operations, `state.validate` returned zero findings, and product/bound architecture matched at `sha256:d9f905c29b0b561e193359c5ccf067549fea74d24c42bf9e18440c1e1cbebf46`.
- Plan B remains `PENDING` and byte-identical to its frozen baseline at `sha256:f93f7b2c4154b8c5d107b039598b4ebc58cc749b2b660847eb9ec3ef02e5b840`. No Plan B execution state or campaign root was started.

## Plan B T9 handoff — 2026-07-28-0905

- Plan B passed its amended exact-self-append pre-start guard, entered `IN_PROGRESS`, and exclusively created `vault://atlas/tmp/thin-error-source-review-2026-07-28/`.
- User-approved schema-only migrations repaired `11` active artifacts whose quoted `schema_version` blocked the qualified snapshot; every target used exact CAS/reread and no registry, semantic, or non-schema artifact byte changed.
- Immutable T9 freeze `sha256:c493b0a1c25100c8e3de5d112e713e5b12d63667cb961048e83d4ce18a364ef9` contains exactly `503` active rows at MANIFEST `sha256:de6612bccd0f2cb3e5e16daf98c4eaa5f86af4ace72698097be805d4554d3c04`, source-ID-set SHA-256 `608c5e58f261f0054d88455ce272b3bc986d3e399f25bd6ddbeb99f013e6c67e`, with exact identity/revision and no omitted/extra row.


## Plan B terminal handoff — 2026-07-29-1058

- Plan B archived atomically at `.agents/plans/archive/2026-07-27-0153_atlas-thin-error-source-review.md`, SHA-256 `9277f535cfdf61624bd3d00a36a2fd3bf5ea793cef4f1fbd4c54ba53bb1bcff2`.
- Its fixed `503`-source cohort closed with all `503` terminal assessments and projection rows, all `161` flagged rows explicitly resolved, and all `36` approved effects terminal. Applied state is exactly `19` approved existing-source updates, `14` approved additive identities, `66` source/route transaction receipts, and three named no-writes.
- Receipt-derived refresh closed `12` edges across `agentic-harness-architecture` and `ai-coding-workflow`; both topics are `current` with zero pending edges.
- Durable report: `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-28--thin-error-source-review.md`, terminal H2 successor revision `sha256:5797e07916158fd35700ed2ea4c6036533b21e811c59187a160d70b1fa524c67`.
- The exact approved campaign tree (`7,995` files; `241` directories; `217,301,823` bytes; digest `sha256:c949a0ba573309ca649b6474729ca51b8fc4abbbfa8f88ea19ef72f46addf8ac`) was deleted through `vault.delete_tree`; subsequent logical listing/digest checks find neither root nor quarantine.
- Final living state has `517` active sources, zero registry findings, both architecture copies at `sha256:4d4433015beadb403441e081040b273bbc1bc16e63f5ae514f2960203545bb99`, and no audit finding beyond the accepted missing TODO seed path.

## Completion Summary

**Completed**: 2026-07-29

**Outcome**: Completed the serial Atlas program. Plan A qualified the provider-neutral façade, closed the retained historical campaigns, and archived first. Plan B then froze and reviewed the live source cohort, executed only approved living effects, refreshed only receipt-derived dirty topics, published the terminal report, deleted its temporary root under exact approval, and archived second. This umbrella archives last.

**Child archives**:

- Plan A: `.agents/plans/archive/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md`, SHA-256 `5dddc59a3fd362282ce79408d29b480c0c3aea9364842865a32d5ae97544448b`.
- Plan B: `.agents/plans/archive/2026-07-27-0153_atlas-thin-error-source-review.md`, SHA-256 `9277f535cfdf61624bd3d00a36a2fd3bf5ea793cef4f1fbd4c54ba53bb1bcff2`.

**Final report**: `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-28--thin-error-source-review.md` at `sha256:5797e07916158fd35700ed2ea4c6036533b21e811c59187a160d70b1fa524c67`.

**Verification**: `136` product tests pass; façade advertises `atlas-local-fs-cas-v1` and `28` operations; product/bound architecture bytes match; current MANIFEST/TOPICS/RELATIONS validate with zero findings; `517` active sources snapshot cleanly; both affected topics are current with zero pending edges; all requested campaign and quarantine paths are absent.

**Residual**: `vault://atlas/todos/TODOs.md` remains the sole accepted pre-existing missing seed path. The canonical Plan-A recovery root remains retained by decision. Plan-B cleanup intentionally removed campaign-local evidence bodies after terminal hashes and exhaustive ledgers were preserved externally. No remaining program task or approval is open.
