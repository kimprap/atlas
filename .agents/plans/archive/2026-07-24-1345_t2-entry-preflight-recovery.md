# T2 entry preflight recovery

**Datetime**: 2026-07-24-1345
**Scope**: Repair the deficient T2 entry-behavior and fixture-cleanup gates for the living-source retrospective conformance campaign without overwriting its immutable, incorrectly passing T2 index or silently rebasing T3.
**Summary**: Run the five frozen entry cases in isolated fresh agent contexts, remove residual preflight fixtures, exclusive-create a superseding T2 authority, and rebind T3 only after product/living drift rechecks pass.
**Status**: DONE

## Context

Parent campaign: `.agents/plans/2026-07-23-2322_living-source-retrospective-conformance.md`  
Parent root: `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/`

Independent review found T3 cohort data mechanically sound, but T2 did not satisfy the complete execution contract:

1. The five entry cases were not run in isolated fresh agent contexts (static contract/API assertions only).
2. Preflight smoke fixtures remain under `preflight/fixtures/`.

Because T3 binds the deficient T2 preflight SHA (`d09332ce…74ec25`), the parent authority chain is not promotable to T4. Parent `indexes/t2-preflight.json` is immutable and must not be overwritten. Recovery uses a separate root and superseding indexes.

## Tasks

- [x] T1. Activate recovery plan, exclusive-create recovery root, freeze parent bindings
  completed 2026-07-24-1346
- [x] T2. Remove parent preflight fixture tree and verify absence
  completed 2026-07-24-1347
- [x] T3. Run five entry cases in isolated fresh agents; exact-validate structured responses
  completed 2026-07-24-1349
- [x] T4. Exclusive-create superseding T2 authority without overwriting parent `t2-preflight.json`
  completed 2026-07-24-1350
- [x] T5. Recheck product/living drift; exclusive-create T3 rebind to corrected T2 authority
  completed 2026-07-24-1350
- [x] T6. Annotate parent plan gate for T4 and complete this recovery plan
  completed 2026-07-24-1350

## Approach

### T1 — Activate and freeze parent bindings

Require this plan `PENDING` with all tasks open. Set `IN_PROGRESS`. Exclusive-create recovery root:

`vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/`

Exclusive-create `preflight/execution-contract.md` as a byte snapshot of this recovery plan, then `indexes/parent-bindings.json` binding:

- parent plan path
- parent execution-contract SHA-256 `d4a28f2b6e4f0dce3e61b32df21b3326b8ab62c2276118aef871b0b80cbdf35b`
- parent product-baseline SHA-256 `dc644845dfa5a9615c51350768b7262d7e1e42dbc6fbce2e02f13db226ceeb17`
- parent product-union SHA-256 `fc1be1f85fb428bce0bfbb7f2c244727533fb9c735fbdfea7f94c82fced352e3`
- deficient parent T2 preflight SHA-256 `d09332ce2bab5322c3077a6ff94d1146b1fda26c5f58c78f4ee2a6fe6d74ec25`
- parent cohort-freeze SHA-256 `3ded74a6458c61f556c1e4db020ebd7d9eb6a49fd5ea5cacc4a068e0827c5a4e`
- deficiency reasons (entry-context, fixture-residue)

Do not mutate parent indexes. Deterministic JSON is canonical sorted-key UTF-8 plus one LF.

### T2 — Remove preflight fixtures

Delete only:

`vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/preflight/fixtures/`

and its entire tree (`probe/`, `summaries/`, `transactions/`). Do not delete unit-test or instance-check transcripts, cohort registry snapshots, or indexes. Persist `indexes/fixtures-cleanup.json` with before/after path listing, file count, and verified-absence flag. Halt if any fixture path remains.

### T3 — Fresh-agent entry cases

Cases (from frozen eval SHA `15556c82ee7c7b70012149fa3b423d65a84df1faddb59d88b9eede4b0b6a2347`):

1. `audit-inaccessible-text-no-write`
2. `audit-thin-insufficient-text-no-write`
3. `audit-aggregate-page-scope-required`
4. `audit-aggregate-page-only-no-child-bodies`
5. `audit-normal-article-not-aggregate`

For each case, spawn one isolated fresh agent with:

- only the case `id`, `evidence`, and required structured output schema derived from `expected`
- product entry contracts: `atlas-source` skill entry clauses, architecture accessibility/aggregate clauses, quality-guide entry accessibility section
- analysis-only / no vault writes / no sibling case context / no parent campaign narrative

Each agent returns exactly one JSON object. Exact-validate against the eval `expected` fields:

| Case | Required exact matches |
|---|---|
| inaccessible | `write=false`, `failure_ids` contains `inaccessible-or-insufficient-text`, every `fallback_forbidden` listed as not used |
| thin | `write=false`, `failure_ids` contains `inaccessible-or-insufficient-text` |
| aggregate scope | `ask_scope=true`, `choices` exact set `page-only`+`expand`, `write_without_answer=false` |
| page-only | `scope=page-only`, `child_bodies_imported=false`, `failure_ids=[]` |
| normal article | `ask_scope=false`, `write_allowed_after_validation=true` |

Persist one packet per case under `entry-cases/<id>.json` binding prompt hash, agent metadata, raw response, parsed object, and validation. Any fail stops recovery (product repair would be a separate plan).

### T4 — Superseding T2 authority

Exclusive-create recovery `indexes/t2-preflight-recovery.json` that:

- binds parent product-baseline and execution-contract SHAs
- records deficient parent T2 SHA as `supersedes_t2_preflight_sha256` (not rewritten)
- embeds fixture cleanup result and all five entry-case packet hashes
- re-records or references still-valid unit-test / instance-check / fixture-smoke evidence from parent preflight (those gates were independently verified clean)
- sets `passed=true` only when entry cases and fixture cleanup both pass
- is the sole T2 authority for subsequent parent-campaign tasks

Also exclusive-create a parent-root pointer only if exclusive-create succeeds and does not overwrite:

`vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/indexes/t2-preflight-recovery.json`

as a byte-identical copy or a minimal pointer document binding the recovery index SHA. Prefer a pointer document if a full copy risks confusion; never replace `t2-preflight.json`.

### T5 — T3 rebind

Recheck all 16 product baseline files and living watch paths against parent product-baseline. Require zero drift and product/bound architecture byte identity. Require cohort-freeze file SHA still `3ded74a6…27c5a4e` and its internal `t2_preflight_sha256` still the deficient value (historical). Exclusive-create `indexes/t3-rebind.json` that:

- binds cohort-freeze SHA and its historical deficient T2 SHA
- binds recovery T2 SHA as `authoritative_t2_preflight_sha256`
- records product/living recheck results
- states T3 semantic freeze remains authoritative; only T2 authority is superseded

Mirror a pointer under the parent indexes directory without mutating `cohort-freeze.json`.

### T6 — Parent gate annotation and completion

Append a short recovery note to the parent plan (do not uncheck historical T2/T3 outcomes) stating T4 may proceed only when both recovery T2 and T3-rebind indexes pass and are bound. Complete this recovery plan’s Completion Summary and set `Status: DONE`. Archive only if the user requests archive; otherwise leave under active plans until the parent campaign completes.

## Critical files & anchors

- Parent plan: `.agents/plans/2026-07-23-2322_living-source-retrospective-conformance.md` lines 42–56, 179–180 (T2 entry + verification)
- Eval cases: `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` negative_audit_cases (five audit-* entry cases)
- Entry contracts: `.agents/skills/atlas-source/SKILL.md` open/clarify steps; `.agents/ARCHITECTURE.md` accessibility/aggregate; quality-guide entry section
- Parent indexes: `…/indexes/{product-baseline,t2-preflight,cohort-freeze}.json`
- Recovery root: `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/`

## Verification / Done criteria

- [x] Recovery root exclusive-created; parent indexes unchanged except optional exclusive-create recovery pointers
- [x] Parent `preflight/fixtures/` absent (zero files)
- [x] Five isolated agent responses exact-match eval expectations; all packets pass
- [x] Parent `t2-preflight.json` SHA remains `d09332ce…74ec25` (unmodified)
- [x] Recovery T2 index exists, `passed=true`, binds entry + cleanup evidence
- [x] Product and living drift recheck zero; T3 rebind exists and points at recovery T2
- [x] Parent plan notes T4 precondition uses recovery authority

## Assumptions & contingencies

- Product behavior is unchanged; recovery proves entry behavior rather than repairing product code.
- If any entry case fails, stop and open a product-repair plan; do not weaken expected fields.
- If product/living drift appears during T5, stop; do not rebind T3 onto a drifted baseline.
- Historical parent T2/T3 completion timestamps remain forensic truth of the deficient pass; recovery supersedes authority without rewriting history.

## Completion Summary

Recovery established superseding T2 authority without rewriting parent immutable indexes.

**Delivered**
- Recovery root: `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/`
- Parent bindings SHA-256: `e75540b63a6769e18a7d49c31b938d05cfea994caf039ad90f9a86ad8d03c3c1`
- Fixtures cleanup: 31 files removed; `preflight/fixtures/` verified absent; cleanup index SHA-256 `e6b6f9a10eb5488744e2984fc8a93b775fec03ab04767f3dd0b304c310879d75`
- Five isolated read-only subagents exact-validated against eval expectations; entry-cases index SHA-256 `0e076fa7226c8d397da9e2d99f3459365931487e6bcf970360e87c8aae3c7711`
- Superseding T2 recovery index SHA-256 `cd2762eb612e99c41d46cb39f4a99cef253752d0b7a61e4fb1856871feb44c6d` (`passed=true`)
- T3 rebind SHA-256 `0bd2d49e6baae1d39800cea23aabe0b301c9ea7ce1d5a28f95c36ef7a61c3f08` (`passed=true`); cohort freeze bytes unchanged at `3ded74a6458c61f556c1e4db020ebd7d9eb6a49fd5ea5cacc4a068e0827c5a4e`
- Parent pointers exclusive-created: `indexes/t2-preflight-recovery.json`, `indexes/t3-rebind.json`
- Deficient parent `t2-preflight.json` remains SHA-256 `d09332ce2bab5322c3077a6ff94d1146b1fda26c5f58c78f4ee2a6fe6d74ec25` (unmodified)
- Product baseline and living watch paths: zero drift; product/bound architecture byte-identical

**Residual**
- Parent T2/T3 historical completion annotations remain forensic records of the deficient pass.
- Parent campaign T4 may proceed only with recovery T2 + T3-rebind authority bindings above.
- Recovery plan left active (not archived) until parent campaign completion unless user requests archive.

## Plan A terminal closure — 2026-07-28-0222

- This plan's recovery outcome remains `DONE`. Its canonical recovery root `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/` is terminal `retained-by-decision` at `sha256:877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1`.
- Plan A projection `sha256:13872a97fd6a9357315b527f0c71d90cb4c8e87546768578f89a93723c92ba06` preserved this root as the sole detailed canonical T2 authority. The noncanonical corroborating recovery root was separately deleted after exact approval and same-digest preflight.
- The parent retrospective campaign root was deleted after its own exact approval. The durable retrospective report preserves the accepted T2 result and authority hashes; this retained canonical recovery root preserves the full record set.
- Final archive destination: `.agents/plans/archive/2026-07-24-1345_t2-entry-preflight-recovery.md`.
