# Atlas Recovery Requirements

**Datetime**: 2026-08-06-1223
**Scope**: Requirements recovery for Atlas source-quality auditing, artifact-neutral repository guidance, deterministic TOPICS list migration, external shared-OMP activation dependency, and safe resumption of the agent-memory plan
**Summary**: Bind the current root-cause evidence into an approved Engineering Requirements Brief before any architecture, code, repository-plan, shared-binary, framework-sync, or bound-instance change. Preserve the completed research lineage where semantics remain unchanged and return the approved brief to `dev-ask` for a freshly classified specification and implementation route.
**Status**: PENDING

## Context

The current agent-memory plan is blocked at T4 because a later source-quality audit cannot reconstruct the genuine source-only evidence bundle required by `quality.validate_summary`; persisted summaries and manifest metadata are insufficient and must remain invalid substitutes. The same recovery must remove artifact identities and temporary stale-plan state from `.agents/AGENTS.md` while preserving equivalent fail-closed stale-plan behavior elsewhere, add a deterministic candidate seam for conditional legacy `TOPICS.md` list normalization, consume rather than duplicate the separate OMP PR workstream, and leave the original plan gated until all prerequisites are current. These changes affect shared contracts, a future shared executable installation, and living Markdown state, so the immutable downstream assurance profile is `high-consequence`.

## Route Overview

Goal: Establish an approved observable recovery contract that keeps `.agents/AGENTS.md` artifact-neutral, restores genuine source-only audit evidence, defines safe conditional TOPICS list migration, consumes the external OMP workstream, and makes the blocked agent-memory plan safely resumable.
Route: `dev-requirements → dev-ask (recompute)`; no specification, ticket, implementation, shipping, Atlas, or bound-instance action is authorized until the Engineering Requirements Brief is approved and the route is recomputed.
Why: Product direction is settled for artifact-neutral repository guidance and fail-closed evidence quality, but storage/retention behavior, stale-plan enforcement behavior, recapture drift/failure behavior, external OMP completion boundaries, and cross-instance migration acceptance still need one revision-bound observable contract. Direct implementation and specification are premature; diagnosis is skipped because the source-audit data-flow defect and missing migration seam are already evidenced.
Artifacts: `local://atlas-recovery-requirements-brief.md` plus one common Handoff returning the approved revision to `dev-ask`.
Gates: approval of this exact overview; human approval of every synthesized requirement; a recomputed Route Overview before downstream work; separate delivery authority for any shared OMP install; separate named approval for every bound-instance mutation, especially non-development profiles.
Execution: one owner; assurance: high-consequence.
First action: dispatch exactly one `dev-requirements` owner through the execution backend with the current authority identities and this plan; perform no repository mutation, Atlas/profile/vault/façade I/O, OMP build/install, or original-plan edit.

## Tasks

- [ ] T1. Bind current authority and conflicting directions
- [ ] T2. Establish complete observable recovery requirements
- [ ] T3. Draft and obtain approval for the Engineering Requirements Brief
- [ ] T4. Return the approved revision to dev-ask for route recomputation

## Approach

### T1. Bind current authority and conflicting directions

1. Re-read and hash these exact authorities before requirements work:
   - `.agents/AGENTS.md` — planning SHA-256 `8265fcb796cd1258b4ad1dd9c8a0b12d948862e7cd8502fdd754a2ecc57d794b`; its only artifact-specific material is `## Temporary stale-plan gate`, currently naming three dated plan identities.
   - `.agents/ARCHITECTURE.md` — planning SHA-256 `d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; it owns product/instance separation, source evidence, migration, reducer, synchronization, and write-set boundaries.
   - `/Users/kim/.omp/agent/sessions/home-app-4e4900aa64f63b525858320505b495be06962e54a73f2b28cffa7af5c6f52813/2026-08-04T16-11-03-586Z_019fcd8a-f422-7000-9cec-d88dd01eeedb/local/repo-agent-memory-first-draft-plan.md` and `.agents/plans/2026-08-02-1456_repo-agent-memory-first-draft.md` — planning SHA-256 `a103123a5b6c24fbadeffb57e4f7c364ee0a3d8d676747026a1fcce63718eab0` for each; the local artifact remains authoritative, `IN_PROGRESS`, and T4-blocked.
   - `.agents/skills/atlas-ask/owners/atlas-audit/OWNER.md`, `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md`, `.agents/skills/atlas-ask/owners/atlas-migrate/OWNER.md`, `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`, `scripts/atlas_quality.py`, `scripts/atlas_source.py`, and `scripts/atlas_state.py` at their then-current hashes.
2. Treat the user's current direction as superseding the old gate-removal wording: `.agents/AGENTS.md` must contain stable repository context only—no dated plan IDs, local/session handles, hashes, receipts, or other artifact-specific blockers. Preserve the blocked behavior, not the current storage location: every currently gated plan must remain non-executable until its own current authority, reapproval, and projection reconciliation are proven through a replacement mechanism selected later by specification.
3. Bind the separate OMP session as an external dependency owner for the upstream JSON-schema PR. Do not clone, port, edit, build, install, push, or review that PR in this route. Require a future immutable handoff to distinguish upstream-PR completion from shared local activation; a merged or open PR alone does not prove the normal `omp` command is repaired.
4. If any named hash or plan authority drifted, or the local authoritative plan cannot be read, stop with a stale-authority Handoff to `dev-ask`; do not substitute the repository projection, historical receipts, or remembered prose.

### T2. Establish complete observable recovery requirements

1. Record the following `.agents/AGENTS.md` outcomes as fixed, not open design questions:
   - repository context and durable discovery guidance may remain;
   - all artifact identities and the temporary stale-plan table/section leave this always-loaded file;
   - removal must not make any currently gated plan executable;
   - a future agent encountering a stale, projection-only, drifted, blocked, or unreapproved plan must stop before execution and receive an exact recovery condition;
   - the specification, not the requirements owner, chooses the neutral enforcement seam and canonical owner.
2. Define the source-quality audit contract with these minimum observable outcomes:
   - a later bounded audit can obtain genuine source-only complete readable UTF-8 text, or an exact visible projection backed by complete bytes and ordered byte ranges, for each selected persisted source;
   - the recaptured evidence identity must match the persisted source ID, canonical URL, and artifact content hash before it can validate that artifact; changed, unavailable, unauthorized, empty, non-text, or hash-mismatched recapture fails closed with a source-specific finding and never silently audits different bytes;
   - `quality.validate_summary` remains unchanged or stricter and continues to reject generated summary prose, historical receipts, hashes without bytes, model context, sibling evidence, and ad hoc raw context as substitutes;
   - one bounded request can audit the seven target source IDs independently and return one complete aggregate, while one source's recapture failure does not fabricate or borrow evidence for another;
   - temporary evidence has an explicit creator, consumer, maximum cohort/cardinality, OS-temporary location boundary, provenance, lifecycle, cleanup owner, cleanup acknowledgement, cancellation behavior, and failure result; no temporary payload becomes living Atlas state by implication;
   - the path works after ordinary ingestion, not only while the original source worker packet remains in memory.
3. Resolve only these load-bearing requirements questions with the human, recommending the conservative default in each case:
   - raw-evidence retention: retain the current no-persistent-raw-evidence boundary and use bounded ephemeral recapture unless the human explicitly authorizes a new storage/privacy policy;
   - recapture drift: report an identity-bound audit inability rather than resummarize, overwrite, or evaluate a changed payload in the read-only audit;
   - cohort failure: return per-source findings and an overall issue result, but guarantee cleanup for every successfully captured sibling; never weaken all-or-nothing evidence identity;
   - stale-plan enforcement: require neutral, discoverable enforcement outside `.agents/AGENTS.md` that covers every current identity and future stale or blocked projection; downstream specification decides whether enforcement is per-plan, centralized, or adapter-owned.
4. Define the deterministic `TOPICS.md` migration contract exactly:
   - begin with a fresh qualified read-only inventory for every explicitly bound instance; the seven-cell repository example in `tests/test_atlas_tool.py:1460-1624` is synthetic and never proves a live defect;
   - target only `Aliases`, `Canonical tags`, `Include terms`, and `Exclude terms`; never include relation-derived `Pending edge IDs`;
   - select only logically valid values whose defect is legacy/noncanonical encoding, ordering, escaping, or spacing; reject blanks, duplicates, invalid escapes, Unicode surrogates, ambiguous values, and any semantic change;
   - decode with the existing Markdown-table plus semicolon list codec, sort by UTF-8 bytes, and re-encode semicolons, backslashes, control characters, table pipes, and literal `none` using the canonical codec;
   - preserve decoded value multisets, row order, every non-target cell, freshness/cache values, unmanaged/non-table bytes, newline convention, final-newline state, `MANIFEST.md`, and `RELATIONS.md`;
   - validate the complete candidate registry before writing, freeze the exact `TOPICS.md` revision, apply one acknowledged `vault.conditional_replace`, reread/hash, and run complete post-validation;
   - retain preimage/output hashes and one artifact-level CAS rollback boundary; conflict, ambiguous state, invalid candidate, missing acknowledgement, or incomplete rollback halts without force-write;
   - inventory may enumerate known instances, but mutation authority is separately named and approved per instance; non-development writes always require explicit approval.
5. Bind lineage preservation and invalidation:
   - a list-only semantics-preserving migration changes the full `TOPICS.md` revision and makes prior answer/final-audit current-state receipts historical, but preserves T3 source artifacts, pass, coverage ledger, relations, refresh receipt, and cited research when their bytes and semantics are unchanged;
   - any source resummarization or change to source artifact, manifest, relation, pass, coverage, topic-index, or answer input requires a fresh complete T3 research aggregate;
   - after product changes, sync only explicitly approved instances, prove a fresh normal-command shared-OMP strict no-effect Task handle/result against current Atlas revisions, inventory/migrate each named instance, run the seven-source audit, then revise and reapprove the original local plan before T4;
   - no old Atlas approval, handle, dispatch binding, current-answer receipt, or final-audit receipt may be represented as current.
6. Keep architecture choices out of the brief: it may require observable capability and failure behavior, but it must not choose the audit owner chain, new façade operation names/shapes, candidate-generator API, gate-registry format, transaction structure, or file/module decomposition.

### T3. Draft and obtain approval for the Engineering Requirements Brief

1. Create `local://atlas-recovery-requirements-brief.md` using the exact `dev-requirements` sections: `Authority`, `Observable behavior`, `Acceptance`, `Scope`, `Constraints`, `Evidence and assumptions`, `Open engineering questions`, and `Next owner`.
2. Include falsifiable acceptance for artifact-neutral `.agents/AGENTS.md`, stale-plan fail-closed behavior, seven-source audit evidence identity and cleanup, deterministic no-op-or-migrate behavior per instance, shared-OMP dependency proof, lineage preservation/invalidation, original-plan reapproval, projection reconciliation, and the exact T4 resume condition.
3. Mark every remaining question with one owner and blocking status. Do not synthesize product retention/privacy authority or implementation architecture. If a product choice remains unresolved, return the exact `PRODUCT AUTHORITY REQUIRED` stop from `dev-requirements` rather than producing an approvable brief.
4. Present the exact brief revision for human approval. Any caveat or changed condition creates a new revision and invalidates the prior approval; silence is not approval.

### T4. Return the approved revision to dev-ask for route recomputation

1. Emit one common Handoff containing the approved brief path/hash, current authority hashes, fixed high-consequence assurance, external OMP dependency state, all resolved decisions, remaining nonblocking assumptions, and `dev-ask` as the sole receiver.
2. Re-enter `dev-ask` for a fresh Route Overview. Because the recovery crosses framework architecture, strict owner/façade contracts, deterministic migration, shared executable activation, bound-instance effects, and multiple verification lineages, the expected artifact depth is an engineering specification followed by dependency-wired tickets; this expectation is not authorization and must be recomputed from the approved brief.
3. Perform no repository edit, Atlas/profile/vault/façade I/O, OMP build/install, plan-gate removal, framework sync, or instance mutation in this requirements route.

## Critical files & anchors

- `.agents/AGENTS.md` — `## Temporary stale-plan gate`; the artifact-specific always-loaded content that must become neutral without releasing blocked plans.
- `.agents/ARCHITECTURE.md` — `Product and instance boundary`, `Source lifecycle`, and `Migration and extension`; normative owner of source evidence, write targets, sync, and migration boundaries.
- `/Users/kim/.omp/agent/sessions/home-app-4e4900aa64f63b525858320505b495be06962e54a73f2b28cffa7af5c6f52813/2026-08-04T16-11-03-586Z_019fcd8a-f422-7000-9cec-d88dd01eeedb/local/repo-agent-memory-first-draft-plan.md` — authoritative blocked plan and exact T4 resume constraints.
- `.agents/skills/atlas-ask/owners/atlas-audit/OWNER.md` — bounded source-quality mode currently requires a source-only evidence bundle but owns no later evidence acquisition seam.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — façade operation inventory, list/reducer contracts, and persisted source identity boundaries.

## Verification / Done criteria

- [ ] Every named authority is re-read and bound to a current digest; the original local plan and repository projection remain byte-identical and unmodified.
- [ ] The approved brief makes `.agents/AGENTS.md` artifact-neutral while preserving explicit fail-closed behavior for every currently gated plan.
- [ ] The approved brief defines genuine source-only evidence identity, recapture drift/failure behavior, seven-source cohort behavior, temporary ownership/cleanup, and invalid substitutes without weakening `quality.validate_summary`.
- [ ] The approved brief defines deterministic inventory, eligibility, codec, byte-preservation, validation, CAS, rollback, per-instance approval, no-op, and failure behavior for the four eligible `TOPICS.md` list fields.
- [ ] The approved brief distinguishes the external upstream OMP PR from separately authorized shared normal-command activation and duplicates no OMP source work.
- [ ] T3 preservation versus invalidation conditions, fresh answer/audit requirements, stale-receipt prohibition, original-plan reapproval, projection reconciliation, and exact T4 resume conditions are complete and falsifiable.
- [ ] Every open question has an owner and blocking status; no implementation architecture is selected by requirements.
- [ ] The human explicitly approves the exact brief revision, and the common Handoff returns that immutable revision to `dev-ask` for recomputation.
- [ ] Repository files, the authoritative original plan, its projection, Atlas/profile/vault state, shared OMP bytes, and bound instances are unchanged by this route.

## Assumptions & contingencies

- The user's artifact-neutrality direction is settled authority: removing only the memory plan's line from the existing `.agents/AGENTS.md` gate is insufficient because the entire dated gate is stale-prone context.
- The other OMP session owns the upstream JSON-schema PR only unless its immutable handoff proves more. If it also completes rollback-protected shared installation and a fresh normal-command strict no-effect smoke, consume that proof; otherwise retain shared activation as an unresolved external dependency and do not duplicate it here.
- No living seven-cell defect is assumed. A later qualified inventory produces either a validated no-op or a separately approved migration; repository fixtures and historical receipts cannot authorize writes.
- The no-persistent-raw-evidence boundary is the recommended default, not permission for the requirements owner to decide retention/privacy policy. Any durable raw-evidence proposal requires explicit human authority and a revised brief.
- The downstream route remains high-consequence because it changes shared contracts, may replace a shared executable, and can mutate living canonical registries. A lower assurance profile requires a revised Route Overview and explicit approval.
- If current authority, scope, external OMP ownership, or any load-bearing identity changes before dispatch, invalidate this overview and return to `dev-ask`; do not continue from partial or historical evidence.
