# Atlas agent tools and campaign closure

**Datetime**: 2026-07-27-0153
**Scope**: Atlas product contracts, dependency-free tool façade, isolated behavior qualification, retained-root disposition, and eligible predecessor-plan closure
**Summary**: Productize the smallest provider-neutral Atlas tool surface required by the source workflows, prove it with deterministic and fresh-context evals, sync the framework contract, then use the qualified surface to reach exact terminal dispositions for four historical roots and archive the three eligible predecessor plans. This plan owns umbrella tasks T1–T8 and must be `DONE` and archived before Plan B starts.
**Status**: DONE

## Execution intent

Deliver a deep Atlas tool module with one versioned call envelope over the existing URL, quality, state, source, and transaction owners. The local adapter must resolve the active profile, expose only logical `vault://atlas/…` identities, provide durable CAS/locking/tree deletion, and support lock-linearized source snapshots plus recoverable source, route, and refresh operations. Entry skills use the façade; commands remain thin; product behavior remains provider/model/harness neutral.

After product qualification, produce fresh authority/digest projections for the four retained roots. Preserve the canonical T2 recovery root by settled decision. Obtain one explicit terminal `delete|retain` decision for each of the primary, corroborating, and predecessor forensic roots; forensic deletion requires an additional irreversible-loss acknowledgment. Apply only approved exact digests, append durable terminal report amendments, truthfully terminalize rejected/not-reached predecessor work, archive eligible predecessors, complete this plan, and archive it atomically.

Creating this file does not start execution, authorize deletion, or approve a root disposition. At first execution, change this plan to `IN_PROGRESS`; leave Plan B `PENDING`.

## Dependencies and authority

- Umbrella coordinator: `.agents/plans/2026-07-26-1657_atlas-framework-tools-cleanup-and-thin-source-program.md`.
- Pending dependent Plan B: `.agents/plans/2026-07-27-0153_atlas-thin-error-source-review.md`.
- Canonical framework contract: `.agents/ARCHITECTURE.md`; `vault://atlas/ARCHITECTURE.md` is its product-owned bound snapshot.
- Existing pure owners: `scripts/atlas_url.py`, `scripts/atlas_quality.py`, `scripts/atlas_state.py`, and `scripts/atlas_source.py`.
- Existing operational owners: `.agents/skills/atlas-core/`, `atlas-source`, `atlas-acquire`, `atlas-route`, `atlas-refresh`, and `atlas-audit`.
- Durable historical reports:
  - `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-23--living-source-retrospective-conformance.md`
  - `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-21--living-source-quality-revisit.md`
- Never read a retained root as current semantic authority. Before any retained body is used for fixture extraction or disposition, recompute and bind the report-defined tree digest/count tuple.

## Tasks

- [x] T1. Bind child plans and freeze product/root authorities
  - completed 2026-07-28-0038
- [x] T2. Add red deterministic and behavioral evals
  - completed 2026-07-28-0059
- [x] T3. Define architecture and executable contracts
  - completed 2026-07-28-0102
- [x] T4. Implement and directly verify the tool family
  - completed 2026-07-28-0143
- [x] T5. Align skills and pass isolated qualification
  - completed 2026-07-28-0157
- [x] T6. Re-audit retained-root authority and loss
  - completed 2026-07-28-0204
- [x] T7. Apply exact terminal retained-root decisions
  - completed 2026-07-28-0222
- [x] T8. Close predecessors and archive Plan A
  - completed 2026-07-28-0228

## Ordered implementation

### T1 — Bind plans and freeze authorities

1. Change this plan from `PENDING` to `IN_PROGRESS`. Verify the umbrella links this exact active path and Plan B’s exact active path. Verify Plan B remains byte-identical with `Status: PENDING`.
2. Record a canonical execution-contract snapshot containing repository-relative product member IDs and SHA-256s, not host paths:
   - `.agents/ARCHITECTURE.md`, `.agents/AGENTS.md`;
   - the four current Python cores;
   - `atlas-core`, source/acquire/route/refresh/audit skills and matching command stubs;
   - eval/schema/template/quality/registry-contract assets this plan changes;
   - umbrella and both child-plan revisions.
3. Read the active profile declaration from `ATLAS_VAULT_PROFILE` when supplied, otherwise `../vault/config/profiles/local.yml`. Persist only `{profile,instance,connector}` and logical root `vault://atlas/`; never persist the resolved instance root.
4. Bind the bound architecture and four living registry revisions/hashes. This is a product/qualification baseline only; T1 performs no living research mutation.
5. Recompute the report-defined root manifest for each retained root—relative POSIX paths sorted bytewise; `D\t<relative>/\n` per directory and `F\t<sha256>\t<bytes>\t<relative>\n` per file—and compare the full digest/count tuple with the historical baseline:

| Root | Historical digest role |
|---|---|
| `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/` | Primary campaign baseline `17f7e41cd27a92472f85bcb5e6d9bdd906b31aeaf41b531ee3d1ec6f44cf244e` |
| `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/` | Sole canonical T2 recovery baseline `877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1` |
| `vault://atlas/tmp/living-source-retrospective-conformance-t2-recovery-2026-07-24/` | Independent corroborating recovery baseline `41782e802043363148f0e4a055b7d40fc9384d92979aade0c3d835690ba7b001` |
| `vault://atlas/tmp/source-quality-revisit-2026-07-21/` | Predecessor forensic baseline `17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a` |

6. A mismatch is not approval failure and is never silently rebased. Mark only that row `audit-required`, inspect its authority/loss anew, and later issue a fresh projection. Other exact rows remain usable.
7. Extract only recurring failure shapes needed by T2. Convert them to minimal synthetic fixtures. Do not copy living source prose, transaction bodies, host paths, provider prompts, or campaign helper implementations.

### T2 — Add red evals before production changes

1. Add `.agents/skills/atlas-core/assets/evals/agent-tooling.json` with exact top-level `{version:1,cases:[…]}`. Each case has exactly `id`, `prompt`, `fixture`, and `expected`; preparation removes `expected` before model execution.
2. Add `.agents/skills/atlas-core/assets/source-summary-proposal.schema.json` and `.agents/skills/atlas-core/assets/fresh-source-assessment.schema.json`, JSON Schema 2020-12. Production validation remains dependency-free; `jsonschema` is a test-only optional dependency used to prove schema/executable parity.
3. Extend `scripts/atlas_quality.py::_fixture_cases` to accept either existing named arrays or one generic `cases` array, never both. Add `prepare-calibration --input <path|->`; input is exactly `{version,fixture_text,case_ids}`, rejects unknown/duplicate/missing IDs, and emits fixture-order `{version:1,cases:[{id,prompt,fixture}]}` without expected values. Preserve the existing exact `validate-calibration` response and finding/exit classes.
4. Write failing direct tests before implementation in `tests/test_atlas_connector.py`, `tests/test_atlas_discovery.py`, `tests/test_atlas_tool.py`, and existing URL/quality/state/source tests. Add fresh-context eval cases only for behavior that cannot be proven by direct imported-unit tests.
5. Direct red cases must cover:
   - strict profile parsing, logical URI/path traversal/query/fragment/credential rejection, no-symlink descriptor traversal, exact text/JSON bytes, sorted listing, full-byte revisions, CAS conflicts, durable write acknowledgment, and capability truth;
   - `source.snapshot_active` including a deliberately paused artifact-first/MANIFEST-last writer and a concurrent addition at the lock boundary;
   - bounded discovery normalization/dedupe, first provenance, overflow/rejected URLs, byte-identical rerendering;
   - proposal schema/executable parity, native types, publication precision, evidence locators/ledgers, unknown-key/context-leakage rejection, deterministic rendering;
   - `quality.validate_fresh_assessment` freeze/packet/hash/excerpt/link/dimension/finding/index invariants and metamorphic blinding from history/provider/request context;
   - route rejection for archived sources and route-event hash mismatch at both reducer and façade guard seams;
   - source/route transaction apply, injected failure, exact recover, one legal identical successor, collision, and `manual-conflict`;
   - refresh same-edge-set intent, pass/index binding, stale revision, pass collision, failure after start, failure after pass/index, recovery, concurrent route exclusion, and terminal receipt;
   - digest-bound delete traversal/symlink/special-file rejection, approval-token mismatch, drift, atomic quarantine, erase failure, exact resume, and final absence;
   - one non-Atlas JSON-edit near miss that neither claims nor requires Atlas capabilities.
6. Fresh behavior cases must cover thin standalone intent required, aggregate scope required, inaccessible no-write, substantive article no question, untrusted evidence ignored, and deterministic allowed-action/write-set consequences. Expected prose is never asserted.
7. Capture the initial red run and exact failing cases in this plan’s execution log before T3/T4.

### T3 — Update canonical architecture, then contracts

1. Update `.agents/ARCHITECTURE.md` first. Add the domain language below and preserve existing ownership:
   - **product contract**: product-authored framework authority;
   - **bound instance**: living research state reached only through connector/profile and logical URI;
   - **Atlas tool façade**: small provider-neutral public operation family over pure domain owners and a profile-selected storage adapter;
   - **connector**: byte I/O, lock, CAS, durability, and deletion implementation only;
   - **profile**: non-secret binding declaration selecting instance/connector;
   - **active-source snapshot**: lock-linearized identity/revision vector, not copied source prose;
   - **FreshSourceAssessment**: orthogonal fresh observation object; classes are derived findings;
   - **resolution decision**, **mutation projection**, **effect claim**, **member/effect receipt**, **source residual**, **refresh projection**, and **cleanup defer** as distinct authorities.
2. Define one normal call envelope:
   - success: `{"version":1,"ok":true,"op":"<literal-or-null>","result":{},"findings":[]}`;
   - validation/state/conflict: same envelope with `ok:false`, `result:null`, and sorted exact `{code,path,detail}` findings;
   - canonical sorted-key compact UTF-8 JSON plus one LF;
   - exit `0` success/no-op, `2` deterministic validation/state rejection, `3` binding/I/O/conflict.
3. Define the initial adapter `atlas-local-fs-cas-v1`:
   - select `ATLAS_VAULT_PROFILE`, else `../vault/config/profiles/local.yml`;
   - accept only the verified scalar `profile/instance/connector/local_fs.root` shape and reject duplicate/unknown/type-confused YAML constructs;
   - resolve relative root against the vault repository containing `config/profiles/`;
   - expose only `vault://atlas/<relative>` and never a host path;
   - reject traversal, query, fragment, credentials, symlink/special-file traversal, invalid UTF-8 for text/JSON, and mutation on unsupported connectors/profiles;
   - capabilities report actually callable operations; unsupported mutation is read-only `mutation_unavailable`, never fallback.
4. Define exact operation literals and version-1 shapes in `markdown-registry-contracts.md` and `atlas-core/SKILL.md`:
   - `vault.read`, `vault.read_json`, `vault.list`, `vault.hash`, `vault.write_json`, `vault.conditional_replace`, `vault.digest_tree`, `vault.delete_tree`;
   - `url.normalize`, `discovery.normalize`;
   - `quality.validate_proposal`, `quality.validate_summary`, `quality.prepare_calibration`, `quality.validate_calibration`, `quality.validate_fresh_assessment`;
   - `state.validate`, `state.reduce`;
   - `source.render_summary`, `source.merge_artifact`, `source.render_route_artifact`, `source.snapshot_active`;
   - `transaction.execute`, `transaction.recover`, `transaction.successor`;
   - `refresh.execute`, `refresh.recover`.
5. Storage operation invariants:
   - revisions are exactly `missing|sha256:<64 lowercase hex>` over full bytes;
   - JSON writes use sorted keys, compact separators, UTF-8, and one LF;
   - conditional replace requires exact expected revision and reread acknowledgment;
   - tree digest uses the T1 manifest algorithm and rejects symlinks/special files;
   - delete request binds `{path,expected_digest,projection_sha256,approval,report_revision}` and requires exact `approval == "DELETE_TREE <path> <expected_digest> <projection_sha256>"`;
   - delete verifies under the root lock, writes an operation tombstone, atomically renames to deterministic same-parent quarantine, erases deepest-first, and succeeds only when original and quarantine are absent. `quarantined-not-erased` is not success and resumes only from the exact tombstone. Atomic rename absence makes the capability unavailable.
6. `source.snapshot_active` holds one instance mutation session while it reads MANIFEST, selects all `Status: active` rows, reads each referenced artifact only to validate UTF-8/machine identity and compute full-byte revision, and returns no body. Result binds MANIFEST revision, active count, source-ID set hash, and rows containing sequence/ID/canonical URL/logical artifact URI/content hash/route status/manifest-row hash/artifact revision.
7. Keep source proposal metadata model-owned only where semantic: title/author/publication/source kind/assessment and source-local claims/links. Identity, sequence, canonical link, acquisition, artifact path, routing, reducer fields, and current time remain caller/reducer-owned. `validate_proposal` owns executable semantics; deterministic renderer owns canonical Markdown.
8. `FreshSourceAssessment` stores independent fields for capture state, access/representation, identity alignment/evidence strength, page form, proportional page-summary adequacy, explicit row-intent fit, findings, evidence locators, link-ledger binding, review independence, and drift binding. `thin-standalone` requires explicit user intent; `unknown` intent is terminal but cannot derive thinness. Input failures, response outcomes, and semantic findings remain distinct.
9. Fix route ownership at every seam: `atlas_state.route-upsert` rejects archived sources and any event content hash unequal to current MANIFEST; façade/workflow preflight also rejects artifact/path/ID/URL/hash disagreement before invoking the reducer.
10. `refresh.execute` accepts an exact approved topic projection plus supplied pass/index candidate bytes; it performs no synthesis. It binds topic ID, complete ordered edge set, registry/index input revisions, pass URI expected missing, pass/index output hashes, dates, and transaction root. Under one re-entrant mutation session it persists immutable intent/phase records, runs start over that exact set, creates/acknowledges pass and index outputs, runs complete over the same set, validates final state, and emits terminal receipt. `refresh.recover` reconstructs the identical request and classifies exact records/bytes; it never completes a changed edge set or substitutes pass/index bytes. Recoverable failure reaches a durable `blocked` outcome with reason and pending edges; conflict halts.
11. Source/route transaction authorization remains typed, target-allowlisted, hash-bound, and self-contained. Event/target outputs are immutable; one automatic successor is legal only from the exact verified `aborted|rolled-back` predecessor terminal. No zero-target transaction is used by campaign workflows.
12. Thin-source resolutions are compositional, not an overloaded enum. Replacement is additive; no source retirement/reactivation transition is introduced. Update architecture → core contracts/quality guide → owning skills → command stubs only if their dispatch reference changes.

### T4 — Implement the deep tool family

1. Add `scripts/atlas_connector.py` with `resolve_profile`, logical URI resolution, `LocalFilesystemConnector`, sorted list/revision/CAS/digest/delete, and re-entrant `mutation_session()`.
2. Use descriptor-relative traversal (`openat`-style directory FDs and no-follow checks) for every local path operation. Keep the instance-wide lock at the OS temp lock directory keyed by SHA-256 of the resolved instance root. Do not expose that path.
3. Durable mutation sequence is sibling temp write → file `fsync` → atomic replace/create → parent directory `fsync` → exact reread. Delete uses the T3 quarantine protocol. Tests simulate write/rename/erase interruption and lock re-entry.
4. Add `scripts/atlas_discovery.py::normalize_candidates`. Scope is exactly `{kind,identifier,limit}`; candidates exactly `{url,discovered_from,label}`. Normalize through `atlas_url`, preserve first provenance, dedupe canonical identity, classify `new|existing-active|existing-archived|rejected`, include MANIFEST status where present, and stable-sort by source ID then canonical URL. It never fetches, crawls, scores, or decides officialness.
5. Implement `atlas_quality.validate_proposal`, `atlas_quality.validate_fresh_source_assessment`, and `atlas_source.render_summary_proposal` behind the T3 contracts. Extend current owners; do not create parallel validators/renderers.
6. Implement `source.snapshot_active` in the façade as the domain-specific lock-scoped read. A generic `read_many` or caller-held lock lease is explicitly out of scope.
7. Implement `refresh.execute|refresh.recover` as domain operations reusing the state reducer, connector CAS/durability, and immutable transaction/receipt conventions. Do not add a scheduler or synthesis engine.
8. Add `scripts/atlas_tool.py` with only public Python `capabilities(connector=None)` and `execute(request,connector=None)` plus CLI `capabilities` and `call --input <path|->`. Operation handlers stay private. Pure ops delegate to existing owners; connector ops translate logical URI only at the storage seam.
9. Transaction calls hold the same re-entrant mutation session across event binding, all target preconditions, execute/recover/successor, reread, and response. Refresh holds it across the complete supplied effect. Source snapshot holds it only for its coherent read interval.
10. Add new scripts to the repository-local dependency-free harness allowlist. Production modules stay stdlib-only. Do not add MCP transport, provider SDK, network client, campaign helper, generic filesystem API, public lock lease, or compatibility shim.
11. Run the direct unit suite. Fix product code until all red tests from T2 pass; do not weaken fixtures, error codes, durability, or path boundaries to obtain green.

### T5 — Align agent surfaces and qualify behavior

1. Update `.agents/AGENTS.md` with a compact `Agent tools` table and script layout. Do not edit `/Users/kim/.agents/AGENTS.md`.
2. Make `atlas-core/SKILL.md` the concise operation/contract index. Entry skills retain human workflow sequencing and semantic decisions but route mechanics through named operations:
   - source: URL/evidence/proposal validation/render, snapshot/merge, source then route transaction;
   - acquire: harness discovery then `discovery.normalize`, ordinary per-source ingestion;
   - route: state validation/reduction, explicit route guard, artifact render, recoverable transaction;
   - refresh: harness synthesis then `refresh.execute|refresh.recover` with exact projection;
   - audit: read-only façade calls plus calibration orchestration.
3. Remove duplicate host-path, hash/CAS, proposal-shape, and transaction prose once core contracts own it. Keep command stubs unchanged unless a stale dispatch reference must be corrected; no full checklist moves into command files.
4. Extend `atlas-audit --agent-tools-calibration` as read-only orchestration. Provision an OS-temporary instance and temporary profile; snapshot product/temporary write sets; prepare blinded packets; invoke fresh task contexts; validate exact outputs; remove the entire temporary instance after proof.
5. Use two bounded packet families—deterministic tool behavior and semantic source behavior—each below 50 KiB. Start one pilot, inspect the resolved harness/model, then run at most four contexts concurrently. If any lane would resolve to Grok 4.5 xhigh, override it with GPT-5.6 Terra xhigh. Do not encode either model in product behavior.
6. Require canonical outputs/write sets/identities/transitions/rendered structure/scope gates across fresh contexts. Prose may vary but evidence-backed claims, forbidden-context absence, proposal/checklist/render/summary validation, and allowed actions must pass. Use a blind second review only for failed/ambiguous rows.
7. Record provider/harness/model as execution metadata. Claim cross-context reproducibility only; never claim cross-provider equivalence unless a second provider actually ran.
8. Isolated qualification must include snapshot paused-writer consistency, strict CAS, transaction recovery/successor, refresh interruption/recovery, deletion quarantine/resume, traversal/symlink rejection, discovery dedupe, assessment blinding, and the non-Atlas near miss.
9. Run the full required unit suite once. Sync `.agents/ARCHITECTURE.md` to the bound instance only after all product checks and isolated qualification pass. Reread both and require byte identity, then run read-only capabilities/state/audit checks against `vault://atlas/`.
10. Record the pre-existing missing `vault://atlas/todos/TODOs.md` audit finding as the sole accepted baseline. Any additional finding fails qualification; do not repair unrelated TODO state in this plan.

### T6 — Re-audit authority and irreversible loss

1. Recompute fresh digest/count tuples through the qualified `vault.digest_tree`. Do not treat T1/historical values as current authorization.
2. Produce one Plan-A-owned four-row cleanup projection. For each row bind root URI, fresh digest/counts, authority class, preserved external authority URI/hash, exact irreversible loss, recommendation, and current decision state.
3. Apply the settled authority model:
   - sole canonical T2 recovery root: terminal `retained-by-decision`, no deletion question;
   - primary campaign root: compact durable report is sufficient terminal authority; eligible for independent delete/retain decision;
   - corroborating recovery root: canonical recovery plus durable report is sufficient; eligible for independent delete/retain decision;
   - predecessor forensic root: eligible only with a separate structured acknowledgment that deletion permanently loses the only remaining forensic traces for two rewrites whose transaction provenance never existed. No reconstruction is permitted.
4. Obtain one independent blind review of the projection’s root/digest/authority/loss mapping. The reviewer does not choose dispositions.
5. Append the reviewed projection to both durable reports using CAS. Preserve historical retain-all entries unchanged and label this as a later Plan-A-owned decision frontier. Avoid self/cross-report hash cycles; bind resulting report hashes in this plan execution log.

### T7 — Obtain and apply exact terminal decisions

1. Present one decision round with exactly three required row decisions: primary `delete|retain`, corroborating `delete|retain`, and forensic `delete-with-acknowledgment|retain`. The canonical recovery row is displayed as already `retained-by-decision` but is not selectable.
2. Approval is digest/projection/report bound with no wall-clock expiry. Persist every explicit retain/delete and the structured forensic acknowledgment in this plan plus terminal report appendices before any deletion. No answer remains `awaiting-decision` and keeps Plan A open; it authorizes nothing.
3. For each approved delete row, derive and show exact `DELETE_TREE <root-uri> <tree-digest> <projection-sha256>`. Recompute the digest immediately before the call. Drift invalidates only that row and requires a new projection/review/decision; unaffected row decisions remain valid.
4. Delete serially: corroborating recovery as the small canary, then primary campaign, then predecessor forensic last. Stop on the first operational/integrity failure; do not attempt later roots until the failed/quarantined row is terminally reconciled.
5. Use only `vault.delete_tree`; verify original and quarantine absent. If interrupted, resume from exact tombstone/quarantine. If both are absent after persisted approval but no tool return survived, record qualified `absence-after-approved-intent` without falsely claiming witnessed deletion.
6. Append terminal per-row outcomes to both durable reports: `retained-by-decision|deleted|absence-after-approved-intent|drifted|quarantined-not-erased|failed`, preserved authority, irreversible loss, pre-deletion digest, tool/absence proof, and predecessor report revision. Bind current report hashes externally in this plan.
7. Verify no living/product operational reference requires a deleted root. Historical logical paths remain in reports/plans with terminal disposition; do not scrub audit history.

### T8 — Truthfully close predecessors and Plan A

1. Amend `.agents/plans/2026-07-21-1613_living-source-quality-revisit.md` append-only:
   - preserve task codes and historical negative evidence;
   - rewrite only active labels needed to make terminal meaning truthful;
   - mark T4V7–T4V9 parents and actually executed A/B work as terminal rejected/negative outcomes;
   - record never-reached acceptance/post-accept steps as explicit `not-reached` terminal dispositions, never accepted;
   - terminalize cleanup from the Plan-A row result and preserve the permanent provenance exception;
   - update report/archive references, verification, Completion Summary, and `DONE` only when its own criteria are satisfied.
2. Amend `.agents/plans/2026-07-24-1345_t2-entry-preflight-recovery.md` with its final archive destination and Plan-A closure binding; do not rewrite its already-`DONE` historical outcome.
3. Amend `.agents/plans/2026-07-23-2322_living-source-retrospective-conformance.md` append-only:
   - preserve T1–T12 and historical retain-all decision;
   - terminalize T13 from the new four-row dispositions;
   - record the canonical recovery retention and other actual outcomes without duplicating Plan A’s projection/approval authority;
   - update report/archive references, Completion Summary, and `DONE` only when its criteria pass.
4. Archive with one atomic move each, in exact order: quality revisit → T2 recovery → retrospective conformance. Append final archive destinations to living reports/umbrella while retaining historical path provenance. Do not edit archived plan bytes after the move.
5. Leave `2026-07-13-2349_ai-coding-workflow.md` and `2026-07-14-1337_atlas-evaluation-continuous-research.md` active and unchanged.
6. Re-run Plan-A verification. Check every task/criterion, append Completion Summary with decisions/findings/residual risks/report hashes/root outcomes/predecessor archive paths, set `Status: DONE`, and atomically move this plan to `.agents/plans/archive/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md`.
7. Update the still-active umbrella with Plan A’s archive path/hash. Do not start or edit Plan B execution state in T8.

## Critical anchors

- `.agents/ARCHITECTURE.md:8-23,45-67,112-181` — ownership, text-only evidence, reducer/transaction/refresh seams, source identity.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — canonical registry/reducer/transaction contracts.
- `.agents/skills/atlas-core/assets/source-summary-quality-guide.md` and `source-summary-template.md` — semantic evidence and rendered artifact contracts.
- `scripts/atlas_url.py::normalize_canonical_url,source_id_for`.
- `scripts/atlas_quality.py::resolve_effective_content_hash,validate_summary,_fixture_cases,validate_calibration`.
- `scripts/atlas_state.py::validate_documents,reduce_event,plan_transaction_recovery`.
- `scripts/atlas_source.py::merge_artifact,render_route_artifact,build_event_record,build_transaction_plan,execute_transaction,recover_transaction,build_successor_plan`.
- `scaffold/MANIFEST.json` and `scripts/atlas-instance.py` — provision/sync ownership and bound-instance checks.

## Skill outcomes captured

- **Grilling:** three-stage red proof; exact proposal/evidence semantics; deep façade terms; strict profile/path/lock/durability contracts; one-call typed execution; one successor; provider-neutral qualification; four-root authority model; row-isolated approval/drift; stop-on-operational-failure deletion; truthful negative predecessor closure; exact archive order.
- **Domain modeling:** the terms in T3 are canonical vocabulary to add to architecture/contracts. Source dimensions and action fields remain orthogonal/compositional. `retained-by-decision` is terminal for Plan-A historical roots; `awaiting-decision` is not.
- **Codebase design:** one deep `atlas_tool` façade hides profile resolution, connector I/O, lock choreography, pure-owner dispatch, and recoverable execution. Pure owners remain independently importable; no parallel allocator/validator/renderer exists.

## Execution log

### T1 — Authority freeze — 2026-07-28-0038

- Plan A entered `IN_PROGRESS`; umbrella links resolve to the exact child paths.
- Plan B baseline remains `PENDING` at SHA-256 `f93f7b2c4154b8c5d107b039598b4ebc58cc749b2b660847eb9ec3ef02e5b840`; later T1 verification must match these bytes.
- Active binding persists only `{profile: local, instance: atlas, connector: local-fs}` and logical root `vault://atlas/`.
- All four report-defined retained-root tuples exactly match their historical baselines; no row is `audit-required`.
- Recurring failure shapes were reduced to the synthetic labels in the snapshot; no living prose, transaction body, helper implementation, host path, provider prompt, or request context was copied.
- Canonical compact sorted-key snapshot SHA-256 (including one LF): `0fa786faa412ddeb134a4a0d7b254c75866a1a7b0608a9c6c083b7206614a6e5`.

```json
{"bound_members":{"vault://atlas/ARCHITECTURE.md":{"bytes":19204,"revision":"sha256:f4b76b5d1e8fc78420db0129ebedf52e7380e0a8a6d0fbce2b7bc3e1460c8db7"},"vault://atlas/summaries/registry/RELATIONS.md":{"bytes":296982,"revision":"sha256:9fcfd6ebcc615d5b42b008a535f252ee0ec24466be7ef14e020e1e0fc45ad2e1"},"vault://atlas/summaries/registry/TOPICS.md":{"bytes":2089,"revision":"sha256:2d3f4d8efecd427719e4c1bbfa6217d67f507dbfb933e239cecd4f7eec7f3a27"},"vault://atlas/summaries/registry/VOCAB.md":{"bytes":1720,"revision":"sha256:d2d5991720f61d92140d2477059d507e150ce280d868e8ad7fd169fcec060693"},"vault://atlas/summaries/sources/MANIFEST.md":{"bytes":157924,"revision":"sha256:de6612bccd0f2cb3e5e16daf98c4eaa5f86af4ace72698097be805d4554d3c04"}},"kind":"atlas-plan-a-execution-contract-snapshot","logical_root":"vault://atlas/","plan_b":{"path":".agents/plans/2026-07-27-0153_atlas-thin-error-source-review.md","sha256":"f93f7b2c4154b8c5d107b039598b4ebc58cc749b2b660847eb9ec3ef02e5b840","status":"PENDING"},"product_members":{".agents/AGENTS.md":"bc64254bac8c1e7f5276b101f8fdbfebfb6c266aef95cb25c91e3c206338f79e",".agents/ARCHITECTURE.md":"f4b76b5d1e8fc78420db0129ebedf52e7380e0a8a6d0fbce2b7bc3e1460c8db7",".agents/commands/atlas-acquire.md":"3a9b9baf94c42e14ad81f005ecbef9c7f7f30df4f216ff1766fa65db788d8f18",".agents/commands/atlas-audit.md":"2b9d9a5c5683bd500df00863ddc95e1f9d007fee78d0e9f9c9ef4818cd707e22",".agents/commands/atlas-refresh.md":"5c11873bd9606a9c4d58ed97d6d242a6edd3a1844d4cf67d1770d7d006f8343c",".agents/commands/atlas-route.md":"9d4d35bfc055002aa44a8a92e3b29275898e96ee11d4b4a0179513aa87fe019b",".agents/commands/atlas-source.md":"6eb454e3710d6b02ad3a131f9faa2a53939976b16103820a7b2f32abbe3706ad",".agents/plans/2026-07-26-1657_atlas-framework-tools-cleanup-and-thin-source-program.md":"74150f321e417ef972586fb53659224aa8bf32c235be6e6e0765c53d47b27622",".agents/plans/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md":"c05d07601debe6d1805a02178d58a861fb536c578ef7d8a04be3392942023a69",".agents/plans/2026-07-27-0153_atlas-thin-error-source-review.md":"f93f7b2c4154b8c5d107b039598b4ebc58cc749b2b660847eb9ec3ef02e5b840",".agents/skills/atlas-acquire/SKILL.md":"c1f5595546ee204db744b35f247cd7f12f725defd84388d69d8fffaef6a4a00f",".agents/skills/atlas-audit/SKILL.md":"a78fb2aa9316bf7c6d0fd4ccb8e042b600b09fab2fab24455d6fa9b68c5e6413",".agents/skills/atlas-core/SKILL.md":"e0f263037979a525ac54bd140fa59630079e202a0e5cedad7e16e165f66f0c94",".agents/skills/atlas-core/assets/evals/agent-tooling.json":"missing",".agents/skills/atlas-core/assets/evals/source-summary-quality.json":"b36351591c03ee5a4c40ef13e084938db513f0ee35bbe3fb600946401ef5f06b",".agents/skills/atlas-core/assets/fresh-source-assessment.schema.json":"missing",".agents/skills/atlas-core/assets/markdown-registry-contracts.md":"fc22fb94b3d49b43ae92ce5e8c7e176c95c05539a4cd8a9c6de4b014552b66c5",".agents/skills/atlas-core/assets/source-summary-proposal.schema.json":"missing",".agents/skills/atlas-core/assets/source-summary-quality-guide.md":"78eda60d870439383a2fb5cf3b63c7934771e94889df25e5a6f8d43243c3252c",".agents/skills/atlas-core/assets/source-summary-template.md":"40be9383d955d2781ab32588737f168cda0fe5b6ce9b626c9ca7c2f2029710e3",".agents/skills/atlas-refresh/SKILL.md":"d490cde3249a26667f4b6598f78c650fa23a9a3503c6722c7518a298822d2bf6",".agents/skills/atlas-route/SKILL.md":"06467cae4011c47420d182fc99edf07f21d8273050249e4add6d60f0354fe1bc",".agents/skills/atlas-source/SKILL.md":"542b7570eb0a664ff26e4ee4b8b97e4506a6dc3c2ee5a2abb0a1b45cf5f99fe2","scripts/atlas_quality.py":"fb33356471ec89ef5ee8507c6a8bf98f3a43d292fe05299953e90c813a091da9","scripts/atlas_source.py":"09721ab1dc0389a7a992cf9301fad1bc1ea156e43067badc7b9149c657e4cfac","scripts/atlas_state.py":"5b0f0fce8527264b472ad03d9bece2a4e53d3b853a24368db3546a7d7b885721","scripts/atlas_url.py":"44458a64a352e1a0baa69cc46d7ffceb2e998852a78b4ade72306acdc5cdd729"},"profile":{"connector":"local-fs","instance":"atlas","profile":"local"},"retained_roots":{"vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/":{"content_bytes":48140,"digest":"877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1","directories":3,"files":16,"historical_match":true,"manifest_bytes":1933,"rejected":[]},"vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/":{"content_bytes":368091181,"digest":"17f7e41cd27a92472f85bcb5e6d9bdd906b31aeaf41b531ee3d1ec6f44cf244e","directories":4393,"files":15448,"historical_match":true,"manifest_bytes":2315223,"rejected":[]},"vault://atlas/tmp/living-source-retrospective-conformance-t2-recovery-2026-07-24/":{"content_bytes":45149,"digest":"41782e802043363148f0e4a055b7d40fc9384d92979aade0c3d835690ba7b001","directories":8,"files":24,"historical_match":true,"manifest_bytes":3255,"rejected":[]},"vault://atlas/tmp/source-quality-revisit-2026-07-21/":{"content_bytes":1169266405,"digest":"17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a","directories":3282,"files":20161,"historical_match":true,"manifest_bytes":2414596,"rejected":[]}},"synthetic_fixture_shapes":["native-number-frontmatter-vs-quoted-scalar","publication-precision-unsupported-day","source-claim-or-link-without-evidence-locator","untrusted-evidence-provider-or-request-context-leakage","aggregate-scope-without-explicit-user-intent","inaccessible-or-non-text-input-must-not-write","route-current-hash-or-status-disagreement","durable-transaction-record-or-backup-absence"],"version":1}
```

### T2 — Red eval and test baseline — 2026-07-28-0059

- Five delegated `task` contexts exposed `openai-codex/gpt-5.6-terra` without a reasoning-tier field. They initially halted without reading or editing; the user then explicitly authorized trusting the configured `openai-codex/gpt-5.6-terra:xhigh` default despite that harness metadata limitation. No Grok lane ran.
- Added strict JSON Schema 2020-12 proposal/fresh-assessment assets, eight synthetic fresh-context cases, and direct connector/discovery/tool/quality/source/state tests. Packet sizes were 6,066 bytes for agent tooling and 22,027 bytes for the existing semantic fixture.
- Initial required-suite red run: 102 tests, three failures, nine errors. Exact red cases:
  - import errors for `tests.test_atlas_connector`, `tests.test_atlas_discovery`, and `tests.test_atlas_tool` because the three planned production modules did not exist;
  - `test_fixture_cases_accepts_exclusive_generic_or_named_arrays`;
  - `test_prepare_calibration_validates_blinds_and_preserves_fixture_order`;
  - `test_proposal_schema_and_executable_parity`;
  - `test_proposal_publication_locator_ledger_and_determinism`;
  - `test_fresh_assessment_validates_freeze_packet_and_reference_bindings`;
  - `test_fresh_assessment_rejects_unblinded_context_and_nonterminal_rows`;
  - `test_render_summary_proposal_is_deterministic_and_preserves_ownership`;
  - `test_event_record_and_transaction_ids_are_hash_bound`;
  - `test_route_rejects_archived_source_and_manifest_hash_drift`.
- Implemented only the T2 fixture-family and `prepare-calibration` owner changes after the red capture. Targeted verification passed: two tests, zero failures.

### T3 — Canonical architecture and executable contracts — 2026-07-28-0102

- Added canonical domain language, façade envelope, strict local adapter, snapshot, transaction, refresh, route, fresh-assessment, and compositional-resolution invariants to `.agents/ARCHITECTURE.md` first.
- Added all 26 operation literals and exact connector/proposal/assessment/snapshot/transaction/refresh contracts to `atlas-core`; updated the quality guide/template after the owning contract. Command dispatch did not change, so command stubs stayed byte-identical.
- Verified both schemas parse as JSON Schema 2020-12, every operation literal is indexed, and every required domain term is present.
- Contract SHA-256s: architecture `9db6acd7fd1f46db2e235618c4eff8a069927bb30312fc1a54b60663eced8819`; core skill `9e4173c7994a2d5383b44fa1fec6bd627456495ce5dd753f4a2ed8b6205d882a`; registry/tool contracts `d0f9a18f10128e5ee3477fa53efe4fb5cc3b6a9714c021d1dad283f0a134b4dd`; quality guide `00aaa3bbc44c8352fce22696250b8893637018fc35720a4879172b28f5730dff`; template `1cb5504c1a5ba5b489c061f8ec79a85c02096e9537e210a764fe1c3705afb51a`; proposal schema `a52b340a1affd4d572dd914b8e0be604152a1fdaf9b7044890f9c15b0edb0a3f`; fresh-assessment schema `2dda873e64fa1cd0a1c74ae8f9e0a19c9d0edda63d6098741fa17909ec834a1e`.

### T4 — Deep tool family implementation — 2026-07-28-0143

- Added strict `atlas-local-fs-cas-v1`, bounded discovery normalization, executable proposal/fresh-assessment validators, canonical proposal rendering, and the 26-operation `atlas_tool` façade. Added the source-transaction-only internal single-file rollback primitive to architecture/core after implementation exposed that connector seam.
- Preserved pure-owner boundaries and stdlib-only production. `atlas_tool` holds re-entrant mutation sessions across transaction and refresh effects; source snapshot returns only the coherent identity/revision vector.
- Corrected red-fixture defects that were not product failures: YAML scalar separator handling, case-insensitive macOS filename collision, route-hash test sequencing, relation edge hash over LF bytes, unavailable-profile placement, quarantine permission restoration, and terminal-manual-conflict simulation.
- Direct required suite: 131 tests, zero failures. CLI smoke returned canonical success for adapter `atlas-local-fs-cas-v1`, logical root `vault://atlas/`, and all 26 sorted operations without a host path.

### T5 — Façade-first skills and isolated qualification — 2026-07-28-0157

- Updated `.agents/AGENTS.md`, `atlas-core`, and all nine entry skills to keep fetch/search/synthesis and semantic decisions in the harness while routing identity, validation, rendering, state, CAS, transaction, refresh, and audit mechanics through the named façade. Command stubs stayed unchanged. Extended blinded packet preparation to the existing 44-case named source fixture; the prepared family is 18,625 bytes and contains no `expected` key.
- Qualification used fresh isolated `task` contexts whose resolved metadata was `openai-codex/gpt-5.6-terra:xhigh`; no Grok lane ran. The pilot confirmed the model but exposed a coordinator response-schema defect. Initial schema-stripped responses were discarded before semantic verdict. With the exact schema, four summary and four negative-audit cases exact-validated; the deterministic primary response mismatched only by returning fields from both case families, and its one blind second review exact-validated all eight rows, including assessment blinding, scope/no-write gates, untrusted-evidence resistance, deterministic write sets, and the non-Atlas JSON near miss.
- Full verification initially found two stale skill-text assertions after the intentional façade cutover. The assertions were updated to defend the new observable `url.normalize` and no-write/untrusted-evidence contracts; the complete required suite then passed: 132 tests, zero failures. Those isolated temporary-profile tests cover exact bytes, strict CAS, lock-linearized snapshots, traversal/symlink rejection, discovery dedupe, transaction recovery/successor, refresh interruption/recovery, and quarantine deletion/resume.
- Synced only the product-owned architecture snapshot to local instance `atlas`. Product and bound bytes are identical at SHA-256 `d9f905c29b0b561e193359c5ccf067549fea74d24c42bf9e18440c1e1cbebf46`. Bound capabilities report `atlas-local-fs-cas-v1`, `vault://atlas/`, and the exact 26 sorted operations without a host path; bound `state.validate` returned zero findings. The instance check/audit reported only the pre-existing missing `vault://atlas/todos/TODOs.md` baseline; a bounded logical-vault listing found no SQLite/database, unclaimed-source, or smoke-fixture residual.

### T6 — Reviewed root authority and loss frontier — 2026-07-28-0204

- Fresh `vault.digest_tree` exposed a façade defect: depth-first manifest emission disagreed with the report-defined global relative-path ordering for a directory whose descendants sort after a sibling file. Added a focused red case, changed the connector to globally sort manifest entries, and verified red → green plus the complete 132-test required suite.
- Recomputed all four roots through the corrected qualified façade. Fresh tuples match the durable historical tuples: primary `sha256:17f7e41cd27a92472f85bcb5e6d9bdd906b31aeaf41b531ee3d1ec6f44cf244e` / 15,448 files / 4,393 directories / 368,091,181 bytes; canonical T2 recovery `sha256:877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1` / 16 / 3 / 48,140; corroborating recovery `sha256:41782e802043363148f0e4a055b7d40fc9384d92979aade0c3d835690ba7b001` / 24 / 8 / 45,149; predecessor forensic `sha256:17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a` / 20,161 / 3,282 / 1,169,266,405.
- Built four-row authority/loss projection `sha256:13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`. Canonical T2 recovery is terminal `retained-by-decision`; primary, corroborating, and forensic rows are `awaiting-decision`. Recommendations are delete, delete, and retain respectively; awaiting states authorize nothing.
- One independent `openai-codex/gpt-5.6-terra:xhigh` blind reviewer passed all four root/digest/count/authority/external-authority/irreversible-loss mappings and chose no disposition.
- Appended the reviewed projection to both reports with strict CAS. Resulting revisions: retrospective `sha256:075c9757b79130d56b3cf059d77beae6154700fc54d79f8309a287810ce49701`; predecessor quality revisit `sha256:b6a38cc1b53814c1e2936e1093b5debc6c184a74f2e853bc37fe58dc4c096e28`. Reports contain only pre-append lineage inputs; resulting revisions are bound here to avoid self/cross-report hash cycles.

### T7 — Terminal approval authority — 2026-07-28

- Binding: projection `sha256:13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`; reviewed-frontier report revisions retrospective `sha256:075c9757b79130d56b3cf059d77beae6154700fc54d79f8309a287810ce49701` and predecessor quality revisit `sha256:b6a38cc1b53814c1e2936e1093b5debc6c184a74f2e853bc37fe58dc4c096e28`.
- User decisions: canonical T2 recovery `retained-by-decision` (fixed); primary campaign `delete`; corroborating T2 recovery `delete`; predecessor forensic `delete-with-acknowledgment`.
- Structured forensic acknowledgment: the user explicitly acknowledged permanent loss of the only remaining forensic traces for two rewrites whose required transaction records and exact backups never existed; the provenance gap cannot be reconstructed, and no fabricated reconstruction is permitted.
- Exact approved serial calls:
  1. `DELETE_TREE vault://atlas/tmp/living-source-retrospective-conformance-t2-recovery-2026-07-24 sha256:41782e802043363148f0e4a055b7d40fc9384d92979aade0c3d835690ba7b001 sha256:13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`
  2. `DELETE_TREE vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23 sha256:17f7e41cd27a92472f85bcb5e6d9bdd906b31aeaf41b531ee3d1ec6f44cf244e sha256:13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`
  3. `DELETE_TREE vault://atlas/tmp/source-quality-revisit-2026-07-21 sha256:17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a sha256:13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`
- Approval has no wall-clock expiry. Each call still requires an immediate same-digest preflight. This section records authority only; it claims no deletion outcome.

#### Approval serialization correction — 2026-07-28

- No deletion was attempted under the three command strings above. They incorrectly serialized `projection_sha256` with a `sha256:` prefix; the qualified façade requires the raw 64-hex value.
- The user explicitly confirmed the corrected strings below. Root, digest, execution order, dispositions, projection value, and structured forensic acknowledgment are unchanged:
  1. `DELETE_TREE vault://atlas/tmp/living-source-retrospective-conformance-t2-recovery-2026-07-24 sha256:41782e802043363148f0e4a055b7d40fc9384d92979aade0c3d835690ba7b001 13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`
  2. `DELETE_TREE vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23 sha256:17f7e41cd27a92472f85bcb5e6d9bdd906b31aeaf41b531ee3d1ec6f44cf244e 13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`
  3. `DELETE_TREE vault://atlas/tmp/source-quality-revisit-2026-07-21 sha256:17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a 13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06`

#### Terminal execution outcomes — 2026-07-28-0222

- Persisted the corrected approval strings and forensic acknowledgment to both reports before deletion. Deletion request report binding was retrospective revision `sha256:b307c329c5c4915c5ee28a506cca9a2672fff2e1a0a8eaf9ed4e2e09ac3df796`.
- Every immediate `vault.digest_tree` preflight matched the approved digest. Serial `vault.delete_tree` outcomes:
  1. corroborating recovery `deleted`; quarantine `vault://atlas/tmp/.atlas-quarantine-4fe205655ced3eaa025276966c2c3dbd8f14927d37e5c3a37e42ce57db5184ad`;
  2. primary campaign `deleted`; quarantine `vault://atlas/tmp/.atlas-quarantine-dac1abda48ed5b63e77141aa394e0447e9cae194d9110b5caa280eb9155d47f5`;
  3. predecessor forensic `deleted`; quarantine `vault://atlas/tmp/.atlas-quarantine-a4b30aea68951fe6f0fe8e4f2c498486c9a596b7c8b6543e84f79c5dd3431260`.
- Each tool result was `ok:true`, `status:deleted`; by the qualified deletion contract this witnesses both original and quarantine absence. No row drifted, failed, or remained quarantined. Canonical T2 recovery remains `retained-by-decision` at its bound digest.
- Appended all four terminal outcomes, preserved authority, exact loss, pre-deletion digest, and tool/absence proof to both durable reports with CAS. Resulting revisions: retrospective `sha256:288cb2507a768e9e58bb1e127542b7e83b334fd1bf7c9e2a41a8ee1941995e24`; predecessor quality revisit `sha256:6757ae9e944de7c04ce554e0ed1dc314061d1e8b551eb6732ab99caea67f8f72`.
- Product operational surfaces and the four living registries contain no deleted-root reference; post-deletion `state.validate` returned zero findings. Historical logical paths remain intact in reports and plans.

### T8 — Predecessor and Plan A closure — 2026-07-28-0228

- Appended final archive destinations to both durable reports through CAS. Final report revisions: retrospective `sha256:ede6fc2fe10257caaad8d5a82707bedc14edf4f88670953cded643ff03363b09`; predecessor quality revisit `sha256:a10401506d1815a260a7c6eaf4d47d2be7ab9dd2dc8f57f605b969bc27764877`.
- Truthfully terminalized predecessor rejected/not-reached work, permanent provenance loss, root outcomes, completion summaries, and statuses. Archived by atomic moves in the required order:
  1. `.agents/plans/archive/2026-07-21-1613_living-source-quality-revisit.md` — `sha256:cc2b97b6259914342b0d0db5c350a601c54539e92a469f4596bbbeb43941c45c`;
  2. `.agents/plans/archive/2026-07-24-1345_t2-entry-preflight-recovery.md` — `sha256:67c85266a9f12b7611dd483b428f0dc5d1066a5046f9dff3be9022e908f618fe`;
  3. `.agents/plans/archive/2026-07-23-2322_living-source-retrospective-conformance.md` — `sha256:c48e9802e39d98eddad458f901d66b7919a730a1413fff042e404396cc9ec303`.
- Final verification: 132 required unit tests passed; façade capabilities returned adapter `atlas-local-fs-cas-v1`, logical root `vault://atlas/`, and all 26 sorted operations; `state.validate` returned zero findings; product/bound architecture matched at `sha256:d9f905c29b0b561e193359c5ccf067549fea74d24c42bf9e18440c1e1cbebf46`.
- Root verification: canonical T2 recovery remains at `sha256:877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1`; the three approved deleted roots return missing-path `IO_FAILURE`. Instance check reports only the accepted missing `vault://atlas/todos/TODOs.md` seed.
- Plan B remains byte-identical to its T1 baseline, `PENDING`, at `sha256:f93f7b2c4154b8c5d107b039598b4ebc58cc749b2b660847eb9ec3ef02e5b840`. Unrelated active plans were not edited.

## Verification / Done criteria

- [x] Red evidence was recorded before implementation; all required direct tests and semantic eval cases exist and defend observable contracts.
- [x] `python3 -m unittest tests.test_atlas_connector tests.test_atlas_discovery tests.test_atlas_tool tests.test_atlas_quality tests.test_atlas_source tests.test_atlas_state tests.test_atlas_url tests.test_atlas_instance tests.test_atlas_harness_surface` passes from the app root.
- [x] Schema/executable parity passes for proposal and fresh-assessment fixtures using test-only JSON Schema 2020-12 validation; production modules remain stdlib-only.
- [x] Isolated capabilities output names adapter `atlas-local-fs-cas-v1`, logical root `vault://atlas/`, sorted exact operations, and no resolved host path.
- [x] Isolated smoke proves exact read/JSON bytes, CAS conflict/no-change, durable reread, traversal/symlink rejection, snapshot linearization, discovery determinism, source/route recovery, one successor, refresh same-set recovery, and quarantine deletion/resume.
- [x] Fresh-context cases pass exact semantic gates/write sets; no Grok 4.5 xhigh lane ran without GPT-5.6 Terra xhigh override; no cross-provider claim is made without a second provider run.
- [x] Entry skills are façade-first, core contracts own mechanics, command stubs remain thin, and product/rules/skills contain no provider-specific behavior branch.
- [x] Product and bound architecture bytes match after sync; `state.validate` is zero; audit has no finding beyond the exact known missing `vault://atlas/todos/TODOs.md` baseline.
- [x] The canonical recovery root is retained by decision. Each other historical root has one explicit terminal decision and a durable report outcome; every approved deletion matches its exact digest and has witnessed/qualified absence; every explicit retention remains present at its bound digest or has a recorded later drift.
- [x] Both durable reports remain usable without deleted roots and preserve accepted outcomes, authority, irreversible loss, and non-self-referential revision lineage.
- [x] Quality revisit, T2 recovery, and retrospective conformance plans satisfy their own tasks/criteria/summaries and exist only under archive paths in the required order; unrelated active plans are unchanged.
- [x] All Plan-A tasks and verification boxes are checked, Completion Summary is appended, status is `DONE`, and this plan is atomically archived. Plan B remains `PENDING` until then.

## Assumptions and fallbacks

- The product-owned local agent file is `.agents/AGENTS.md`; `/Users/kim/.agents/AGENTS.md` is out of scope.
- Local POSIX `local-fs` is the only initial mutation adapter. A profile/connector lacking strict parsing, descriptor-safe traversal, process-shared lock, durable atomic replace, or same-filesystem atomic quarantine rename remains read-only.
- A failed product test, qualification case, architecture sync, registry check, root audit, required user decision, deletion/quarantine reconciliation, predecessor criterion, or report CAS blocks the dependent phase. Do not weaken the gate or start Plan B.
- Explicit `retain` is terminal for a Plan-A historical root; silence/withholding is not. The Plan-B campaign-root cleanup contract is intentionally stricter and is owned by Plan B.
- Existing source/route transaction history is never fabricated. The predecessor forensic exception remains explicit whether its root is deleted or retained.
- No deploy, credential use, non-dev profile mutation, source/topic living write, force operation, compatibility alias, or host-path fallback is authorized by this plan.

## Completion Summary

Plan A delivered one provider-neutral Atlas façade, aligned the framework/skills to it, qualified deterministic and semantic behavior, resolved every retained-root disposition, and closed all three eligible predecessor plans.

**Product**
- Added `scripts/atlas_tool.py` with the version-1 request/response envelope over 26 operations, plus strict local profile resolution, descriptor-safe logical paths, process-shared mutation locking, durable CAS/atomic replacement, canonical tree digests, lock-linearized snapshots, recoverable source/route/refresh execution, and qualified quarantine deletion.
- Updated architecture, shared contracts, product agent ownership, and all nine entry skills to keep semantic work in the harness while routing deterministic identity, validation, state, CAS, transaction, refresh, and audit mechanics through the façade.
- Added deterministic schemas/evals and direct behavioral coverage. Production remains stdlib-only and provider/model/harness neutral.

**Terminal authority**
- Retained canonical T2 recovery at `sha256:877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1`.
- Deleted the corroborating recovery, primary campaign, and predecessor forensic roots after exact user decisions, immediate matching digest preflights, and qualified original/quarantine absence.
- The forensic deletion permanently removed the only remaining traces for two predecessor rewrites lacking required transaction records and exact backups. The user explicitly acknowledged this irreversible loss; no reconstruction was fabricated.
- Final durable reports: retrospective `sha256:ede6fc2fe10257caaad8d5a82707bedc14edf4f88670953cded643ff03363b09`; quality revisit `sha256:a10401506d1815a260a7c6eaf4d47d2be7ab9dd2dc8f57f605b969bc27764877`.

**Verification**
- Final required suite: 132 tests, zero failures.
- CLI smoke: canonical success envelope, adapter `atlas-local-fs-cas-v1`, logical root `vault://atlas/`, 26 exact operations.
- Bound state: `state.validate` zero; architecture byte identity at `sha256:d9f905c29b0b561e193359c5ccf067549fea74d24c42bf9e18440c1e1cbebf46`; only the pre-existing missing `vault://atlas/todos/TODOs.md` instance finding remains.
- Plan B is still `PENDING` and byte-identical to the frozen baseline.

**Archive**
- Predecessor archive paths and hashes are recorded in the T8 execution log.
- Plan A destination: `.agents/plans/archive/2026-07-27-0153_atlas-agent-tools-and-campaign-closure.md`.

**Residual**
- The missing TODO seed remains outside this plan.
- The canonical recovery root remains intentionally retained; future deletion requires new exact authority.
- Fresh-context qualification used the explicitly authorized configured `openai-codex/gpt-5.6-terra:xhigh` lane. No cross-provider equivalence claim is made.
