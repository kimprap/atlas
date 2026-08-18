# Atlas source walkability and prepared routing

**Datetime**: 2026-08-17-2251
**Authority kind**: local-authority
**Mode**: deep
**Scope**: Atlas front-door and source-owner read ordering, inventory terminals, the current worker gate, prepared route transactions, recipes, and generated façade discovery
**Summary**: Make ordinary source work executable from the owner and recipes without reopening the completed CLI cutover: classify before optional reads, stop after a non-actionable inventory, validate the existing worker packet before state reads, and prepare route transactions behind one lifecycle operation.
**Status**: DONE
**Completed At**: 2026-08-18-1418

## Objective

- Outcome: OUT-ATLAS-SOURCE-WALKABILITY
- Observable end state: An approved `/atlas-ask` source request keeps the existing Goal/Effect boundary, reaches one raw-input inventory gate before bound architecture or semantic work, returns one valid no-write result when no source is actionable, and otherwise uses the unchanged version-1 worker/proposal schemas, existing `source.prepare`, new `source.prepare_route`, and generic transaction execution.
- Progress signal: One named AC criterion becomes complete only when its exact changed target and declared proof recipe pass; file count, elapsed time, agent count, and prose agreement are not progress.

The selected scope is the merge-faithful execution-path cut. It preserves the shipped `/atlas-ask` public entry, exactly three owners, version-2 façade envelope, current nested version-1 schemas, current route candidate/verifier semantics, Markdown registry authority, connector boundary, and generic transaction/recovery seam. It does not retain the rejected version-2 evidence-table redesign or deterministic candidate-selection ontology and does not reopen the completed 1842 cutover.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-WALKABILITY | Human improvement request and two supplied diagnostic handoffs | history://01a0104f-e2ad-7000-8b0f-3bec1ab0ad99#skill-prompt | sha256:62d9b29b65e7a90b2ef517e0b16c886fc6949fa2f515fa410a4e274e5fcf0e70 | Planning requested; execution requires native approval of the revised exact plan bytes |
| AUTH-PLAN-REVIEW | Read-only review of the prior candidate | conversation://2026-08-18/plan-review | sha256:e61d2b847135de24a3f45e613be067db0dd6b8578eb16b4b40f3ed46d71ad3bc | Prior bytes rejected; REV-SCOPE-MERGE, REV-T1-CATALOG-LOCKSTEP, REV-T2-T4-PUBLIC-API, REV-TRANSPORT-AUTHORITY, and REV-FRONT-DOOR must be closed before approval |
| AUTH-SCOPE-CUT | Explicit human scope selection | conversation://2026-08-18/revision-scope | cut-to-merge-faithful/v1 | Planning authority for the narrow merge keep-set; not execution approval |
| AUTH-ARCHITECTURE | Canonical Atlas framework contract | .agents/ARCHITECTURE.md | sha256:39c6a56efe2f8a238cbb8ba439f6dd2ecf48318b547425dbd1b831b16a5f344f | Current governing architecture |
| AUTH-ADR7 | Accepted façade and owner-consolidation rationale | docs/adr/0007-agent-cli-and-owner-consolidation.md | sha256:da9ac35bc4d1acc65182ff13e75b4713b22a09e33c8abb034f8b5b1aec982c8a | Accepted |
| AUTH-1842-CLOSURE | Completed predecessor plan; constraint only | .agents/plans/archive/2026-08-15-1842_IMPROVE_deep.md | sha256:c314a506839f92ec21c336beef743e89379c4d6def8b714028fe2bf16c49f780 | DONE and non-executable |

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-CUT-TO-MERGE | AUTH-SCOPE-CUT/v1 | Implement only the two diagnostics' execution-path keep-set; current source worker/proposal schemas and current route candidate/verifier semantics remain unchanged |
| DEC-INVENTORY-FIRST | v2 | The qualified source owner calls default `capabilities` once, reads the source recipe, and sends the complete raw explicit URL set to one `source.inventory`; it performs no redundant owner-side `url.normalize` loop, and a mode-empty winner set is terminal |
| DEC-CURRENT-WORKER-GATE | v1 | Preserve the current version-1 worker/proposal schemas and `source.prepare` signatures; use one stateless schema-constrained tool-free semantic call, reject structurally invalid or nonfinal packets before bound-state reads, and leave semantic checklist adjudication in existing preparation |
| DEC-PREPARED-ROUTE | v1 | Add only lifecycle `source.prepare_route`; it accepts the existing lookup/read binding plus one existing reducer-ready decision, revalidates one consistent snapshot, returns a generic route transaction, and introduces no candidate ontology or route worker schema |
| DEC-ROUTE-DATE-PRESERVATION | AUTH-ARCHITECTURE | `route-upsert` verifies but never rewrites source content hash, last-checked date, last-summarized date, first-seen date, or refresh date; route `checked_on` remains relation-created and artifact-routed time |
| ADR-0007 | sha256:da9ac35bc4d1acc65182ff13e75b4713b22a09e33c8abb034f8b5b1aec982c8a | Preserve one generated façade, three owners, audience-filtered discovery, and mechanics behind explicit inspection; do not add helper owners or another domain CLI |
| DEC-PRESERVE-1842 | sha256:c314a506839f92ec21c336beef743e89379c4d6def8b714028fe2bf16c49f780 | Do not rebuild the v2 catalog, change the owner map, redesign evidence/routing policy, reopen REV-ATLAS-004 through REV-ATLAS-007, or execute the archived plan identity |
| DEC-STANDARD-ASSURANCE | v1 | Architecture, reducer, generated CLI, and agent behavior require independent verification, final review, and terminal learning; unchanged schemas, additive façade scope, and test-only external effects do not justify high-consequence execution |

## Scope, non-goals, and prohibited effects

- Read surfaces: The exact targets and anchors below, their current callers and tests, the two supplied OMP diagnostic transcripts, the plan-review handoff, the completed 1842 plan, and test-managed connector state used by smoke fixtures.
- Change surfaces: TGT-CONTRACTS and TGT-CUTOVER only. TGT-CUTOVER is one indivisible runtime/catalog/front-door/owner/recipe/test cutover so a new operation, its generated adapter, its caller, and exact catalog tests cannot diverge.
- Non-goals: Version-2 evidence tables, UUID evidence IDs, worker/proposal schema migration, source-prepare signature changes, deterministic route-candidate selection, route worker schemas, candidate keys/digests/cursors, source advancement, research publication, answer, refresh, topic creation, maintain modes, migration, provisioning, instance synchronization, hosted recapture, search or embeddings, a fourth owner, helper-owner chains, a new public command, a second transaction engine, or compatibility aliases.
- Prohibited effects: No bound `vault://atlas/` write, no non-development profile write, no `sync-framework`, no deploy, no credentials, no commit, no push, no release, no destructive registry repair, and no mutation of the archived 1842 plan or the two stale-plan identities named in repository policy.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-PRODUCT-EDIT | Reversible product-package mutation | AUTH-WALKABILITY, AUTH-SCOPE-CUT | Only TGT-CONTRACTS and TGT-CUTOVER on the current worktree; patch-reversible; no Git delivery effect |
| EFF-TEMP-EVAL | Ephemeral development-profile and transcript mutation | AUTH-WALKABILITY, AUTH-SCOPE-CUT | OS-temporary test profiles, prompts, fixture packets, receipts, and transcripts only; remove all temporary state before target freeze |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-WALKABLE-ENTRY | Front-door classification, approval timing, source inventory gate, conditional reads, and terminal owner result | T1 | v2 | T2, T3, T4, T5 |
| CONTRACT-CURRENT-WORKER | Existing version-1 worker/proposal packet, pre-read structural gate, tool-free completion, and existing quality/render ownership | T1 | v1 | T2, T3, T4, T5 |
| CONTRACT-PREPARED-ROUTE | Existing route decision, snapshot binding, route-only reduction, prepared transaction, and generic execution/recovery | T1 | v1 | T2, T3, T4, T5 |
| CONTRACT-CATALOG-RECIPES | Generated lifecycle operation, exact audiences/counts, owner-visible recipes, and current façade envelopes | T1 | v1 | T2, T3, T4, T5 |
| CONTRACT-IMMUTABLE-PROOF | Integrated smoke, cleanup, target digest, independent verification, final review, and assessment | T3 | v2 | T4, T5, T6 |

### CONTRACT-WALKABLE-ENTRY

1. Update `.agents/ARCHITECTURE.md` first, then `markdown-registry-contracts.md`, `operating-cadence-and-guardrails.md`, and `source-summary-quality-guide.md`. `/atlas-ask` classifies from its own exact owner/mode map before reading architecture, `atlas-core`, or the owner-result schema. Non-Atlas, empty-goal, unresolved clarification, and classification-only paths load none of those resources. Existing Goal/Effect timing is unchanged: write-capable modes obtain one unchanged approval before owner load; `presence|answer|audit` dispatch without an overview.
2. The front door loads no architecture or core contract on behalf of an owner. It reads `atlas-workflow-result.schema.json` only after an owner result exists, validates exactly one result, and never reconstructs missing fields or accepts prose as a result. The result schema remains byte-identical at sha256:c0aea38041b146de5adad5e16096c1ea7295d09727d8e2c444ecc1685e766214.
3. A qualified source owner calls default `python3 scripts/atlas_tool.py capabilities` exactly once, never `--all`, then reads the `Source a URL` recipe. For `presence|ingest|resummarize`, it calls `source.inventory` exactly once with the complete raw explicit URL set in request order. `source.inventory` remains the sole normalization/dedupe owner; do not add an owner-side `url.normalize` loop. Preserve the complete dispositions `new|active-due|active-not-due|active|archived|duplicate|rejected`.
4. Freeze eligibility from that result exactly once: presence has no winners; ingest selects first-winner entries with `new|active-due`; resummarize selects first-winner entries with `active`. Presence always stops. If a write-mode winner set is empty, return exactly `version:1`, `owner:"atlas-source"`, `outcome:"no-write"`, `effect:"none"`, a nonempty inventory-backed summary, one or more `{id,status:"no-write",summary}` items covering the returned dispositions, and `next:null`. The trace ends after capabilities and inventory: no bound architecture, capture contract, worker schema, model call, lookup, preparation, route, transaction, or write.
5. Only a nonempty winner set loads `vault://atlas/ARCHITECTURE.md` and the mode-scoped capture mapping, quality guide, summary template, and registry contract. It then looks up, captures, normalizes, and processes winners in deterministic source-ID order. `promote` and `reroute` do not enter inventory; after qualification/capabilities they load only their recipe and mode-relevant contracts.

### CONTRACT-CURRENT-WORKER

1. Keep `source-worker-result.schema.json` and `source-summary-proposal.schema.json` byte-for-byte at their bound version-1 hashes. Keep ordinary `source.prepare` exactly `{identity:{canonical_url,checked_on},mode:routine|resummarize,worker}` and promotion exactly `{mode:promote,artifact_uri,evidence_uri}`. No capture argument, schema migration, compatibility union, evidence table, or proposal rewrite is permitted.
2. After one `source.worker_schema` call per nonempty wave, run one stateless structured completion per winner with the returned schema passed before generation and with history, tool access, skill discovery, repository context, profile/vault I/O, and agent delegation disabled. The prompt requires the existing worker packet and states the current cross-field rules verbatim: every proposal claim `{locator,ledger_id}` must equal one `evidence_ledger.evidence` pair; every proposal link `{url,locator,ledger_id}` must equal one `evidence_ledger.links` triple. Consume completions in deterministic source-ID order.
3. In ordinary `_source_prepare`, run existing `atlas_source.validate_worker_result(worker)` and reject `needs-input|expanded` as `WORKER_PACKET_NOT_FINAL` before `_documents(connector)` or any registry/artifact read. Keep the same gate inside `prepare_source` defensively. Do not move semantic `CHECKLIST_ITEM_FAILED`, current-state eligibility, proposal validation, rendering, or summary validation ahead of state: schema-valid `ready` packets preserve the existing current-state-before-semantic-failure precedence.
4. The owner no longer calls `quality.validate_proposal` or `quality.validate_summary`. Existing `source.prepare` remains the sole operation that validates the packet, validates proposal/ledger relations, renders, validates the rendered summary/checklist, reduces, and prepares a transaction. Both quality operations remain lifecycle-visible with unchanged signatures and audiences for explicit inspection.
5. Add deterministic expected/actual detail to existing `PROPOSAL_EVIDENCE_LOCATOR_UNBOUND` and `PROPOSAL_LINK_LEDGER_UNBOUND` findings: canonical JSON of the sorted allowed pair/triple set followed by canonical JSON of the actual pair/triple. Do not add a finding family or change pass/fail semantics.

### CONTRACT-PREPARED-ROUTE

1. Preserve the existing owner-side candidate enumeration and bounded verifier. The final decision is exactly `{outcome,edges}` where outcome is `routed|no-topic-match|routing-blocked`; each included edge is exactly `{topic_id,relation,impact,confidence,reason}` with current enums and the current `Verifier: LOCATOR — CLAIM [relation=RELATION; impact=IMPACT]` sibling-equality rule. Excluded candidates are filtered before preparation. No runtime candidate selector, worker schema, digest, key, cursor, or completeness claim is added.
2. Add lifecycle operation `source.prepare_route`, generated command `source prepare-route`, with exact family args:

```json
{
  "binding": {
    "canonical_url": "https://example.test/source",
    "manifest_revision": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "row": {
      "source_seq": 1,
      "source_id": "28463fd26efb",
      "canonical_url": "https://example.test/source",
      "artifact_uri": "vault://atlas/summaries/sources/artifacts/2026/2026-08/2026-08-17--28463fd26efb--example.md",
      "first_seen": "2026-08-17",
      "last_checked": "2026-08-17",
      "last_summarized": "2026-08-17",
      "content_hash": "1111111111111111111111111111111111111111111111111111111111111111",
      "refresh_after": "",
      "route_status": "unrouted",
      "status": "active"
    }
  },
  "checked_on": "2026-08-18",
  "expected_revisions": {
    "artifact": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
    "topics": "sha256:3333333333333333333333333333333333333333333333333333333333333333",
    "relations": "sha256:4444444444444444444444444444444444444444444444444444444444444444"
  },
  "decision": {"outcome": "no-topic-match", "edges": []}
}
```

3. `binding` is copied unchanged from the latest successful `source.lookup`; explicit reroute retains two equal lookups and passes the second, while post-source routing performs one fresh lookup after the source receipt. `expected_revisions` are copied from the owner reads used for route context and `state.validate`; the manifest read revision must equal `binding.manifest_revision`. Validate all argument shapes, enums, dates, revisions, URL/source-ID agreement, unique topics, and reason sibling equality before connector I/O where current pure validation permits.
4. Under one `connector.consistent_read`, reread exactly MANIFEST, TOPICS, RELATIONS, and `binding.row.artifact_uri`. Require present strict UTF-8 bytes, exact supplied revisions, valid registries, byte-equivalent current manifest row/binding, active state, and artifact identity/hash/route-status agreement. Derive event `source_id` and `content_hash` from the bound row; combine them only with supplied `checked_on` and decision; reuse `atlas_state.reduce_event`, `atlas_source.build_event_record(event_type="route-upsert", route_decision=decision)`, `_route_projection`, and `_rank`.
5. Return exactly one of: `{state:"prepared",transaction:{event_record,targets}}`; `{state:"terminal",outcome:"unchanged",reason:"route preparation has no changed targets"}`; or `{state:"rejected",findings:[...]}` for reducible semantic/state rejection. Malformed or stale request/snapshot failures use existing version-2 envelope/finding taxonomy. Every non-prepared path has no transaction and no write.
6. In `atlas_state.reduce_event` route-upsert, keep pre-mutation content-hash equality rejection, remove the redundant content-hash assignment, remove the `Last checked` assignment, and remove the now-unreachable old-hash supersession branch. Route `checked_on` still supplies relation `Created` and artifact `routed_at`; source `First seen`, `Last checked`, `Last summarized`, `Refresh after`, and `Content hash` remain byte-identical.
7. The owner passes `result.transaction` unchanged to `transaction.execute`; uses `transaction.recover` only with the returned exact transaction identity; and invokes `transaction.successor` only when advertised eligible. Existing `_bind`, `_route_guard`, target order, journal, recovery, successor, connector, and write-set behavior remain unchanged.

### CONTRACT-CATALOG-RECIPES

1. Preserve all current 41 operation literals and audiences, then add only lifecycle `source.prepare_route`: default discovery has 29 lifecycle operations, `--all` has 42 unique operations, and 13 remain internal. `quality.validate_proposal` and `quality.validate_summary` remain lifecycle; `state.reduce`, `source.render_route_artifact`, and generic transaction operations remain internal but callable under current checks.
2. Rewrite only the source recipes into mode-scoped executable steps. Every façade step includes the generated family command and a complete copyable operation-args JSON object for raw-input inventory, lookup, normalized capture, worker schema, ordinary/promote source preparation, route preparation, execute, recover, and successor. Every result state says STOP, ask the existing bounded question, make the one allowed same-worker replacement, execute the returned transaction, or expose exact recovery. Do not send owners to Python/tests or to `capabilities --all` for payload discovery.
3. Update `atlas-source/OWNER.md`, `/atlas-ask`, `agent-tooling.json`, `tests/test_atlas_harness_surface.py`, and exact catalog tests in the same atomic task as the new handler and catalog entry. The source owner no longer names direct quality-validation calls or the internal `state.reduce`/`source.render_route_artifact` assembly path.

### CONTRACT-IMMUTABLE-PROOF

1. Implementation smoke runs changed-contract tests, the full Atlas suite, generated family-command subprocesses, and fixture-driven owner reasoning only against test-managed profiles and tool-free structured completion. It observes one active-not-due terminal, malformed/nonfinal worker rejection before any state read, one prepared route, stale/revision rejection, generic transaction execution, route-date preservation, and one unchanged replay.
2. Remove every synthetic row, artifact, receipt, prompt, transcript, profile, and empty directory before target freeze. Freeze one SHA-256 identity over the exact intended changed files and an evidence index. Product-package completion neither authorizes nor requires bound-instance framework sync, migration, deploy, commit, push, credentials, or non-development profile writes.
3. Independent verification rebinds and reruns the complete declared proof without repair. Only VERIFIED proceeds to one read-only Standards and Specification review. Review blockers return to the implementation backend under the current parent; advisories remain terminal. The final Standard continual-learning assessment mutates no user-level guidance and records skipped unauthorized curation.

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-CONTRACTS | `.agents/ARCHITECTURE.md`, `markdown-registry-contracts.md`, `operating-cadence-and-guardrails.md`, `source-summary-quality-guide.md` | T1 | sha256:39c6a56efe2f8a238cbb8ba439f6dd2ecf48318b547425dbd1b831b16a5f344f, sha256:3b886371e8036ff1b3c31c2c63799bf0b0f247c98fa6a62ae334534d16dd3cb0, sha256:4b079361750af4019ceda1ef3d94e4a4049fe05990c50ebc39eaaba6c8c1f744, sha256:128fbda00ecad332a4724b8157dd9f4b30a93c1610b8784808b876744ae0f3ec in listed order | T2 through T5; source owner; generated catalog | AC-CONTRACTS |
| TGT-CUTOVER | `agent-cli-recipes.md`, `atlas-ask/SKILL.md`, `atlas-source/OWNER.md`, `agent-tooling.json`, `scripts/atlas_quality.py`, `scripts/atlas_source.py`, `scripts/atlas_state.py`, `scripts/atlas_tool.py`, `tests/test_atlas_quality.py`, `tests/test_atlas_source.py`, `tests/test_atlas_state.py`, `tests/test_atlas_tool.py`, `tests/test_atlas_harness_surface.py` | T2 | sha256:f913f0dec3baf8b75c33e132629db210e61e6ae27bcadf5e745d3b2966dd8e6c, sha256:2881edcf4515a24f920c41efaf9a3e302bb5e05a9e75719dfdf3e88a454e2c68, sha256:30d1231eb338d2a8a0b606e385c2d3792a717743f18b1310b1645339766988aa, sha256:9c87cdaa9625f02503bee21bc1556e6e0696ffe47b60b3a541f13e58e955ab26, sha256:1037ef50ce11a4d24ab61199d010dfce2b559765cb967d9af338391a8cfc7941, sha256:bc8479f27e040831ced6969daf1b8600bcbd1027bfe797d550fbeeb0ddd47ec3, sha256:90d6b972d9704cef03c9bd1daacd56b9c6b85855165f7c3353d23d782a89389f, sha256:778a82749de882e6ac0a1f57b56551c9b36f60d8dc114b57660703721263a98d, sha256:aa27ad0a298787358b12fec01664b75559f414cfe878c6ec0bd0585f9623a2c3, sha256:d3c7d38d14d915bdb3d985aaa29b5a297962308c287be420fea2f6574a5bfd18, sha256:1bf7f6c9ed1019831f0b023bd7b11d8635c467d3241422ba8e7ed67cb98bcf53, sha256:da40fbb80da7f6a25e2e0120fb06a6830060eac3744e06cfcbf66b4218f6d1a8, sha256:44aa2f9d01f90ab50901118ab614c2bfda8d169730c3c170961671c7573295b4 in listed order | generated commands, current schemas, owner eval, generic transaction guards | AC-CUTOVER |
| TGT-SCHEMA-BASE | `atlas-workflow-result.schema.json`, `source-worker-result.schema.json`, `source-summary-proposal.schema.json` | T2 | sha256:c0aea38041b146de5adad5e16096c1ea7295d09727d8e2c444ecc1685e766214, sha256:fec5397db2d857735dd704e7f65eef59cac4aa051ead11e8d0292e8bd7d5518e, sha256:a52b340a1affd4d572dd914b8e0be604152a1fdaf9b7044890f9c15b0edb0a3f in listed order | unchanged owner and worker wire contracts | AC-CUTOVER |
| TGT-INTEGRATED | Complete intended TGT-CONTRACTS and TGT-CUTOVER bytes plus test-managed smoke state | T3 | dependency identities OUTP-T1 and OUTP-T2 | ruff, full Atlas suite, generated family-command subprocesses, completion eval, cleanup digest | AC-INTEGRATED |
| TGT-VERIFIED | Immutable implementation target and evidence index from T3 | T4 | OUTP-T3 exact SHA-256 identity | decorrelated verifier | AC-VERIFIED |
| TGT-REVIEW | Exact VERIFIED target and verification evidence from T4 | T5 | OUTP-T4 verified identity | read-only Standards and Specification reviewer | AC-REVIEWED |
| TGT-LEARNING | Settled reviewed outcome and terminal advisories from T5 | T6 | OUTP-T5 reviewed identity | Standard continual-learning assessment and dev-ask | AC-LEARNING |

## Execution policy

- Assurance: standard
- Topology: shared-sequential
- Max concurrency: 1
- Isolation: One shared worktree and one implementation owner through T3; T4 through T6 use separate read-only lifecycle identities against the immutable T3 target.
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: T2 is one indivisible runtime/catalog/front-door/owner/recipe/test cutover. Do not delegate its operation contract and its generated adapter/caller to separate owners. Preserve unexpected user changes and rebind rather than overwrite them.
- Decomposition: T1 fixes canonical contracts; T2 performs the atomic executable cutover; T3 runs integrated smoke, cleanup, and target freeze; T4 independently verifies; T5 performs the final read-only review; T6 performs the terminal Standard continual-learning assessment.
- Effect limit: EFF-PRODUCT-EDIT, EFF-TEMP-EVAL
- Orchestrator profile: Full orchestration and isolated implementation lineages are not required. `dev-implementation` keeps one cohesive implementation owner for T1 through T3. No `dev-integration` fan-in is permitted or necessary.
- Transport: This is a `local-authority` OMP plan. Approval, task state, completion, and archive lifecycle use native harness plan transport; `.agents/plans/2026-08-17-2251_atlas-source-walkability.md` is only the repository projection.

Compact is disqualified because the change alters canonical architecture, reducer state semantics, a generated lifecycle catalog, façade/recipe lockstep, and agent control flow. Standard is selected over high-consequence because the worker/proposal/result schemas and existing route semantics remain unchanged, the new operation only prepares an existing generic transaction, execution is confined to product files plus disposable test profiles, and independent verification plus final review cover the residual misrouting risk.

## Tasks

- [x] T1. Fix merge-faithful source contracts before executable changes
  completed 2026-08-18-0116
  - Owner: implementation-owner
  - Wave: W0
  - Depends on: none
  - Targets: TGT-CONTRACTS
  - Contracts: CONTRACT-WALKABLE-ENTRY, CONTRACT-CURRENT-WORKER, CONTRACT-PREPARED-ROUTE, CONTRACT-CATALOG-RECIPES
  - Criteria: AC-CONTRACTS
  - Effects: EFF-PRODUCT-EDIT
  - Output: OUTP-T1
  - Receiver: dev-implementation
  - Verification: VR-CONTRACTS
  - Lineage: shared

- [x] T2. Cut over runtime, catalog, front door, owner, recipes, and tests atomically
  completed 2026-08-18-0143
  - Owner: implementation-owner
  - Wave: W1
  - Depends on: T1
  - Targets: TGT-CUTOVER, TGT-SCHEMA-BASE
  - Contracts: CONTRACT-WALKABLE-ENTRY, CONTRACT-CURRENT-WORKER, CONTRACT-PREPARED-ROUTE, CONTRACT-CATALOG-RECIPES
  - Criteria: AC-CUTOVER
  - Effects: EFF-PRODUCT-EDIT
  - Output: OUTP-T2
  - Receiver: dev-implementation
  - Verification: VR-CUTOVER
  - Lineage: shared

- [x] T3. Smoke integrated behavior, clean temporary state, and freeze one target
  completed 2026-08-18-0150
  - Owner: implementation-owner
  - Wave: W2
  - Depends on: T2
  - Targets: TGT-INTEGRATED
  - Contracts: CONTRACT-WALKABLE-ENTRY, CONTRACT-CURRENT-WORKER, CONTRACT-PREPARED-ROUTE, CONTRACT-CATALOG-RECIPES, CONTRACT-IMMUTABLE-PROOF
  - Criteria: AC-INTEGRATED
  - Effects: EFF-TEMP-EVAL
  - Output: OUTP-T3
  - Receiver: dev-implementation
  - Verification: VR-INTEGRATED
  - Lineage: shared

- [x] T4. Independently verify the immutable implementation target
  completed 2026-08-18-1356
  - verified target `sha256:fb9452bdfaf5014b43b41e7723dcc936b1cf30f1d0585873d9d502f39e647205`
  - the calendar-precedence continuation grant used semantic attempt 1/2 and returned aggregate `VERIFIED` after closing REVIEW-ATLAS-WALK-006; all prior repair and review counters remain consumed
  - Owner: dev-verification
  - Wave: W3
  - Depends on: T3
  - Targets: TGT-VERIFIED
  - Contracts: CONTRACT-WALKABLE-ENTRY, CONTRACT-CURRENT-WORKER, CONTRACT-PREPARED-ROUTE, CONTRACT-CATALOG-RECIPES, CONTRACT-IMMUTABLE-PROOF
  - Criteria: AC-VERIFIED
  - Effects: EFF-TEMP-EVAL
  - Output: OUTP-T4
  - Receiver: dev-implementation
  - Verification: VR-VERIFIED
  - Lineage: shared

- [x] T5. Review the verified target against standards and specification
  completed 2026-08-18-1411
  - APPROVED target `sha256:fb9452bdfaf5014b43b41e7723dcc936b1cf30f1d0585873d9d502f39e647205`; Standards PASS, Specification PASS, no blockers or advisories
  - Owner: dev-code-review
  - Wave: W4
  - Depends on: T4
  - Targets: TGT-REVIEW
  - Contracts: CONTRACT-WALKABLE-ENTRY, CONTRACT-CURRENT-WORKER, CONTRACT-PREPARED-ROUTE, CONTRACT-CATALOG-RECIPES, CONTRACT-IMMUTABLE-PROOF
  - Criteria: AC-REVIEWED
  - Effects: none
  - Output: OUTP-T5
  - Receiver: dev-implementation
  - Verification: VR-REVIEWED
  - Lineage: shared

- [x] T6. Run the terminal Standard continual-learning assessment
  completed 2026-08-18-1418
  - outcome `NO DURABLE LEARNING`; no guidance mutation, Deep candidate, or papercut outcome
  - Owner: dev-continual-learning
  - Wave: W5
  - Depends on: T5
  - Targets: TGT-LEARNING
  - Contracts: CONTRACT-IMMUTABLE-PROOF
  - Criteria: AC-LEARNING
  - Effects: none
  - Output: OUTP-T6
  - Receiver: dev-ask
  - Verification: VR-LEARNING
  - Lineage: shared

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-CONTRACTS | Four canonical contract files at their bound base hashes plus AUTH-SCOPE-CUT | Architecture and core contracts express one conditional entry/read order, exact no-winner terminal, unchanged current worker/proposal wire contract, current route decision plus one prepared-transaction operation, 29/13/42 catalog arithmetic, route-date preservation, and no rejected redesign vocabulary | TGT-CONTRACTS | T1 |
| AC-CUTOVER | Current runtime/catalog/front-door/owner/recipe/test files, current schema bytes, malformed/nonfinal workers, source inventory fixtures, valid/stale route bindings, and route events dated after source dates | Front door classifies before optional reads; source no-winner trace stops after one raw-input inventory; malformed/nonfinal worker fails before state reads; current schemas and source.prepare args are unchanged; source.prepare_route returns only the specified prepared/terminal/rejected forms; prepared output executes through the generic transaction seam; route-only reduction preserves source dates/hash; recipes are copyable; discovery is exactly 29 lifecycle, 13 internal, and 42 unique operations | TGT-CUTOVER, TGT-SCHEMA-BASE | T2 |
| AC-INTEGRATED | Exact intended changed bytes plus clean test-managed profile state and blind owner fixtures | Ruff, full Atlas tests, generated family commands, selected-route and no-topic-match scenarios, active-not-due early stop, pre-state worker rejection, stale binding, generic execution/recovery, blind owner trace comparisons, cleanup, and pre/post product-tree digest checks pass; one immutable target and evidence index are frozen | TGT-INTEGRATED | T3 |
| AC-VERIFIED | OUTP-T3 immutable target and complete declared check set | A decorrelated read-only verifier reruns the complete proof at the exact digest and returns VERIFIED with no missing, stale, or inconclusive criterion | TGT-VERIFIED | T4 |
| AC-REVIEWED | Exact VERIFIED target from T4 | One final read-only Standards and Specification review returns APPROVED with no eligible blocking finding; advisories remain terminal residual risk and never repair the target | TGT-REVIEW | T5 |
| AC-LEARNING | Settled reviewed outcome, verification evidence, and terminal advisories | One Standard assessment returns CURATED or NO DURABLE LEARNING, records skipped unauthorized mutation, and hands complete terminal accounting to dev-ask | TGT-LEARNING | T6 |

## Verification / Done criteria

- [x] VR-CONTRACTS. Validate the merge-faithful canonical contract cut
  - Criterion: AC-CONTRACTS
  - Proof class: worker smoke
  - Scenario / environment / fixture: Inspect every changed heading against CONTRACT-WALKABLE-ENTRY through CONTRACT-CATALOG-RECIPES; run `python3 -B -m unittest tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_one_public_skill_command_and_exact_three_owner_resources tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_cli_and_owner_result_contracts_are_not_conflated tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_domain_modules_are_libraries_without_direct_cli_entrypoints tests.test_atlas_harness_surface.AtlasHarnessSurfaceTests.test_active_surface_has_no_removed_paths_or_transport_aliases`.
  - Evidence form: Passing targeted results plus a changed-section map that contains the four fixed contracts, excludes version-2 evidence/candidate ontology, and preserves one public entry, three owners, one façade, and generic transaction ownership.
  - Target recheck: TGT-CONTRACTS
  - Receiver: dev-implementation

- [x] VR-CUTOVER. Prove the atomic runtime, catalog, front-door, owner, recipe, and test cutover
  - completed 2026-08-18-0143
  - Criterion: AC-CUTOVER
  - Proof class: worker smoke
  - Scenario / environment / fixture: Run `python3 -B -m unittest tests.test_atlas_quality tests.test_atlas_source tests.test_atlas_state tests.test_atlas_tool tests.test_atlas_harness_surface`, `python3 scripts/atlas_tool.py capabilities`, `python3 scripts/atlas_tool.py capabilities --all`, and `python3 scripts/atlas_tool.py source prepare-route --help`. Cover exact quality expected/actual detail, one raw inventory call and terminal no-winner trace, front-door load order, malformed and nonfinal worker rejection before connector reads, schema-valid ready current-state precedence, prepared/no-changed/rejected route forms, stale row/revision/identity failures, selected and no-topic-match decisions, generic transaction execution/recovery/successor, route-date preservation, exact recipe command/payload parity, and exact audience arithmetic.
  - Evidence form: Passing command outputs; canonical envelopes; read logs; zero writes on rejected paths; exact target order and transaction identity; before/after source, relation, topic, and route artifact fields; `sha256sum` equality for all three TGT-SCHEMA-BASE files.
  - Target recheck: TGT-CUTOVER, TGT-SCHEMA-BASE
  - Receiver: dev-implementation

- [x] VR-INTEGRATED. Exercise the changed path, clean temporary state, and freeze one digest
  - completed 2026-08-18-0150
  - Criterion: AC-INTEGRATED
  - Proof class: implementer integrated smoke
  - Scenario / environment / fixture: Snapshot the product tree after implementation; run `ruff check scripts tests` and `python3 -B -m unittest discover -s tests -p 'test_atlas*.py'`; run actual generated family-command subprocesses for source inventory, source prepare, source lookup, source prepare-route, transaction execute, eligible recover/successor, and unchanged replay against one test-managed OS-temporary profile; run the updated `source-inventory-contract` and `source-transaction-owner` fixtures from `agent-tooling.json` as separate stateless tool-free structured completions using the exact owner/recipe bytes, without revealing each case's expected trace/result, and compare their structured outputs afterward.
  - Evidence form: Full command results; exact operation traces and completion-call counts; schema-bound completion records; source/route receipt and final registry/artifact bytes; cleanup inventory; an identical pre/post-smoke product-tree digest; one SHA-256 identity over TGT-CONTRACTS plus TGT-CUTOVER and a complete criterion-to-evidence index.
  - Target recheck: TGT-INTEGRATED
  - Receiver: dev-implementation

- [x] VR-VERIFIED. Independently rerun every acceptance proof at the frozen target
  - completed 2026-08-18-1356
  - verified target `sha256:fb9452bdfaf5014b43b41e7723dcc936b1cf30f1d0585873d9d502f39e647205`; current grant-cycle semantic attempt 1/2 used
  - Criterion: AC-VERIFIED
  - Proof class: independent verification
  - Scenario / environment / fixture: A fresh decorrelated `dev-verification` identity rebinds OUTP-T3, reruns VR-CONTRACTS through VR-INTEGRATED without repair, checks every declared unchanged schema hash, confirms temporary-state cleanup, and compares the target digest before and after.
  - Evidence form: One immutable verification result with VERIFIED, NOT VERIFIED, or INCONCLUSIVE per criterion and one aggregate verdict.
  - Target recheck: TGT-VERIFIED
  - Receiver: dev-implementation

- [x] VR-REVIEWED. Perform the sole final Standards and Specification pass
  - completed 2026-08-18-1411
  - APPROVED target `sha256:fb9452bdfaf5014b43b41e7723dcc936b1cf30f1d0585873d9d502f39e647205`
  - Criterion: AC-REVIEWED
  - Proof class: final read-only review
  - Scenario / environment / fixture: `dev-code-review` receives only the exact VERIFIED target, AUTH-SCOPE-CUT, governing decisions, fixed contracts, acceptance, and verification evidence; it inspects correctness, compatibility, security, failure behavior, and specification alignment without mutation.
  - Evidence form: One APPROVED, CHANGES REQUIRED, or BLOCKED review bound to the exact target, with blockers separated from advisories.
  - Target recheck: TGT-REVIEW
  - Receiver: dev-implementation

- [x] VR-LEARNING. Complete the required terminal Standard assessment
  - completed 2026-08-18-1418
  - `NO DURABLE LEARNING`; complete project-rule manifest rechecked and target unchanged
  - Criterion: AC-LEARNING
  - Proof class: terminal continual-learning assessment
  - Scenario / environment / fixture: `dev-continual-learning` assesses only directly impacted project-owned guidance after the review settles, preserves the prohibition on user-level AGENTS mutation and unapproved effects, and does not reopen an approved target for advisory cleanup.
  - Evidence form: CURATED or NO DURABLE LEARNING result plus skipped-mutation and terminal-advisory accounting in the Common Handoff.
  - Target recheck: TGT-LEARNING
  - Receiver: dev-ask

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-T1 | T1 | Exact TGT-CONTRACTS revision and changed-section map | completed, blocked, failed, timed-out, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with target revision, fixed-contract accounting, AC-CONTRACTS delta, VR-CONTRACTS result, blockers, route impact, and receiver |
| OUTP-T2 | T2 | Exact TGT-CUTOVER revision, unchanged TGT-SCHEMA-BASE hashes, and worker-smoke evidence | completed, blocked, failed, timed-out, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with selected minimal cut, dependency identity OUTP-T1, AC-CUTOVER delta, VR-CUTOVER result, operation/audience counts, effects, and receiver |
| OUTP-T3 | T3 | Immutable implementation SHA-256 and complete criterion-to-evidence index | completed, blocked, failed, timed-out, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with OUTP-T1 and OUTP-T2 identities, AC-INTEGRATED verdict, exact target, attempts, cleanup, effects, residual risk, and receiver |
| OUTP-T4 | T4 | Immutable independent-verification result bound to OUTP-T3 | completed, blocked, failed, timed-out, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with criterion verdicts, rerun evidence, identity separation, unchanged-target proof, aggregate verdict, and receiver |
| OUTP-T5 | T5 | Exact final review result bound to the VERIFIED target | completed, blocked, failed, timed-out, transport-unavailable, authority-change-required | dev-implementation | Common Handoff with eligible blockers, terminal advisories, specification disposition, exact target identity, inherited attempts, and receiver |
| OUTP-T6 | T6 | Terminal Standard assessment and complete completion evidence index | completed, blocked, failed, timed-out, transport-unavailable, authority-change-required | dev-ask | Common Handoff with curation result, skipped mutations, residual risk, all criteria/effects accounted, route impact, and completion receiver |

## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-STALE-BASE | dev-implementation | Re-read changed target and classify semantic impact against AUTH-WALKABILITY, AUTH-SCOPE-CUT, AUTH-ARCHITECTURE, contracts, targets, and criteria | T1, T2, T3, T4, T5, T6 | Unrelated bytes permit exact rebind; changed authority, scope, contract, acceptance, topology, effect, or capability requires revised plan bytes and native reapproval | Current exact base and authority revisions are bound without overwriting user work |
| BLK-ATOMIC-CUTOVER | implementation-owner | One causal report naming the missing contract-equivalent implementation seam and every affected caller/test | T2, T3 | T2 may not complete with the operation, catalog, generated adapter, owner, recipe, or exact tests out of lockstep; a need for a new schema/candidate ontology is authority-change-required | The complete T2 cutover satisfies CONTRACT-WALKABLE-ENTRY through CONTRACT-CATALOG-RECIPES as one revision |
| BLK-STRUCTURED-COMPLETION | implementation-owner | Live proof that the schema is passed to a stateless tool-free completion before generation and that hidden expectations are withheld from owner-eval prompts | T2, T3, T4 | No permissive JSON, post-hoc repair, unstructured model turn, tool-capable semantic worker, or expected-answer leakage is equivalent | OMP `completion(prompt, schema=...)` or a contract-equivalent harness primitive is available and transcript-verifiable |
| BLK-SCHEMA-DRIFT | dev-implementation | Exact incompatibility showing why one unchanged schema/signature cannot express an approved observable | T2, T3, T4, T5 | Any edit to TGT-SCHEMA-BASE, ordinary `source.prepare` args, route candidate semantics, or evidence ontology exceeds AUTH-SCOPE-CUT and requires revised authority/plan bytes | All approved behavior is implemented with byte-identical TGT-SCHEMA-BASE and current route decisions |
| BLK-BOUND-EFFECT | dev-implementation | Exact profile path/type and proof it is OS-temporary and test-managed | T2, T3, T4 | Any bound instance, non-development profile, sync, credential, deploy, commit, push, release, or destructive effect needs separate human authority and is outside this plan | All runtime commands target disposable temporary profiles and cleanup is complete |
| BLK-ASSURANCE | dev-implementation | Stable finding IDs, affected AC criteria, exact target, causal impact map, eligible repair evidence, and inherited attempt/review state | T4, T5, T6 | Verification and review never repair; use only backend-authorized same-outcome repair, then rerun eligible proof/review; authority conflict returns to its owner | Exact repaired target is freshly VERIFIED and reviewed with no blocker or inconclusive criterion |
| BLK-TRANSPORT | dev-implementation | Native OMP proposal/approval/task-state error, current local plan identity, idempotence, and any partial-effect inventory | all | Do not substitute direct-repository approval, hand-edit task state, or execute from the projection; two safe short transport retries maximum | Native local-authority plan approval and execution state are live, or execution stops transport-unavailable without product mutation |

- exhausted token at 2026-08-18-0232
  - trying: Complete AC-REVIEWED by repairing both original-initial review blockers on the verified target.
  - found: REVIEW-ATLAS-WALK-001 nested schema-invalid ready workers can reach state reads; REVIEW-ATLAS-WALK-002 ordinary source.prepare recipe payload violates the unchanged schemas.
  - tried: Clarified owner, recipe, and evaluation semantics after the verification failure; nested worker-schema validation and schema-valid recipe fields were not changed.
  - target: sha256:fa34feee2234c2f459c4736379a261cd345a229e8ff822760ed07253e6f148b9
  - remaining: AC-CUTOVER, AC-VERIFIED, AC-REVIEWED / dev-implementation
  - grant: continue 2026-08-18-1139
  - opinion: absent

- exhausted review-rerun at 2026-08-18-1235
  - trying: Complete AC-REVIEWED by repairing all three original-rerun blockers on the verified target.
  - found: REVIEW-ATLAS-WALK-003 combines an applied receipt with impossible successor eligibility; REVIEW-ATLAS-WALK-004 omits the route-artifact transaction target; REVIEW-ATLAS-WALK-005 reads bound state before rejecting a noncanonical topic ID.
  - tried: Resolved REVIEW-ATLAS-WALK-001 and REVIEW-ATLAS-WALK-002, clarified conditional transaction semantics, and completed granted semantic attempts 1/2 and 2/2; the impossible applied-successor fixture, incomplete route transaction example, and pre-read topic-ID grammar were not repaired.
  - target: sha256:83be884eda083539671364a8bc06010d8d6e96548c27cd0dc8490c69920a1d67
  - remaining: AC-CUTOVER, AC-INTEGRATED, AC-VERIFIED, AC-REVIEWED / dev-implementation
  - grant: continue 2026-08-18-1240
  - opinion: absent

- exhausted review-rerun at 2026-08-18-1333
  - trying: Complete AC-REVIEWED by repairing the grant-scoped review blocker on the verified target.
  - found: REVIEW-ATLAS-WALK-006 treats a schema-valid impossible calendar refresh_after as structural and bypasses current-state precedence.
  - tried: Closed REVIEW-ATLAS-WALK-003 through REVIEW-ATLAS-WALK-005, returned aggregate VERIFIED in current grant attempt 1/2, and consumed the grant-scoped review pass; the early date.fromisoformat check was not removed and invalid-calendar precedence was not tested.
  - target: sha256:6fa9594603630d97056bc2fd97c031b8da6ad51d923ee7f5399d8f7d3e920ea8
  - remaining: AC-CUTOVER, AC-INTEGRATED, AC-VERIFIED, AC-REVIEWED / dev-implementation
  - grant: continue 2026-08-18-1339
  - opinion: absent

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-ARCHITECTURE | Canonical contract | `.agents/ARCHITECTURE.md` at sha256:39c6a56efe2f8a238cbb8ba439f6dd2ecf48318b547425dbd1b831b16a5f344f | Change first; governs one public entry, owner/runtime ownership, semantic anonymity, write sets, and source/route invariants |
| ANC-OWNER | Owner procedure | `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md` at sha256:30d1231eb338d2a8a0b606e385c2d3792a717743f18b1310b1645339766988aa | Current unconditional preload and owner-assembled route path to replace without changing modes or result shape |
| ANC-RECIPES | Operation recipes | `.agents/skills/atlas-core/assets/agent-cli-recipes.md` at sha256:f913f0dec3baf8b75c33e132629db210e61e6ae27bcadf5e745d3b2966dd8e6c | Current lifecycle map; source recipes become complete, copyable, and terminal-explicit |
| ANC-TOOL | Generated façade | `scripts/atlas_tool.py` at sha256:778a82749de882e6ac0a1f57b56551c9b36f60d8dc114b57660703721263a98d | Sole catalog and connector orchestration seam; owns the additive prepared-route operation and generic transaction guards |
| ANC-WORKER-SCHEMA | Current worker wire contract | `.agents/skills/atlas-core/assets/source-worker-result.schema.json` at sha256:fec5397db2d857735dd704e7f65eef59cac4aa051ead11e8d0292e8bd7d5518e | Must remain byte-identical; schema-constrained generation and pre-read structural/finality gate use this exact shape |

- ASM-CAPABILITY: The active OMP harness exposes Python `completion(prompt, schema=...)` as a stateless tool-free structured completion. Fallback: stop the affected source with BLK-STRUCTURED-COMPLETION before model work.
- ASM-PRESERVED-SCHEMAS: The current outer result, worker, and proposal schemas already express the merge-faithful behavior. Fallback: stop with BLK-SCHEMA-DRIFT; do not mutate or translate them under this authority.
- ASM-PREPARED-ROUTE: Current `source.lookup`, route decision, route renderer/event constructor, reducer, projections, guards, and generic transaction engine suffice for `source.prepare_route`. Fallback: stop T2 at BLK-ATOMIC-CUTOVER rather than add candidate selection, another transaction seam, or direct owner writes.
- ASM-FRONT-DOOR: `/atlas-ask`'s exact owner/mode table is sufficient to classify before architecture/core loads, and the owner-result schema is not needed until a result exists. Fallback: preserve zero Atlas I/O and return an authority-change-required handoff if repository evidence disproves either condition.
- ASM-TEST-PROFILES: Existing test-managed connector fixtures can provision disposable profiles without touching a bound instance. Fallback: stop at BLK-BOUND-EFFECT rather than repoint a command.
- ASM-NO-SYNC: Product-package completion neither requires nor authorizes bound-instance framework synchronization. Fallback: report product/bound snapshot difference as deferred, not as a framework defect.
- ASM-PLAN-TRANSPORT: Native OMP local-authority transport, not repository projection, owns approval and execution state. Fallback: BLK-TRANSPORT; never execute or approve `.agents/plans/2026-08-17-2251_atlas-source-walkability.md` directly.


## Completion Summary

- Delivered the approved source walk: front-door classification before optional reads, one raw-input inventory with a terminal no-winner result, unchanged version-1 worker/proposal schemas, structural and finality rejection before state, current-state precedence before semantic worker evaluation, and reducer-owned calendar validation.
- Added one lifecycle `source.prepare_route` operation backed by one consistent snapshot and the existing generic transaction engine; generated discovery remains exactly 29 lifecycle plus 13 internal operations, 42 total.
- Final immutable product target: `sha256:fb9452bdfaf5014b43b41e7723dcc936b1cf30f1d0585873d9d502f39e647205` over 17 canonical records. Independent verification passed Ruff, target formatting, the full 323-test Atlas suite, and fresh generated-family command smokes with complete temporary-state cleanup. Final review returned Standards PASS, Specification PASS, and APPROVED with no blockers or advisories.
- Preserved the three frozen schema hashes and used the existing reducer and transaction seams rather than adding compatibility paths, another schema, another catalog, owner-side reconstruction, or direct bound-instance writes.
- Terminal Standard assessment returned `NO DURABLE LEARNING`: existing architecture, contracts, owner procedure, recipes, runtime, fixtures, tests, and scoped rules already own the durable behavior; no authorized guidance delta, Deep candidate, or papercut settlement remained.
- Residual risk: owner procedures still depend on the harness honoring the documented stateless schema-bound tool-free completion boundary. Bound-instance framework synchronization was intentionally unauthorized and not performed; any intended snapshot update remains a separate approved effect.
