# Atlas source-summary cross-harness lean completion

**Datetime**: 2026-07-20-1207
**Scope**: Lean completion of parent T8–T11
**Summary**: Close the OMP/Grok comparison from evidence already collected, remove runtime harness qualification as a source-write prerequisite, promote the accepted staged set with existing reducers, and close the campaign. No further candidate, repair, pairwise, baseline, or calibration model calls are required.
**Status**: DONE
**Approved**: 2026-07-20-1408 by user; approved PENDING SHA-256 `b1b09bfecff67dd747b25ada1e3d09a2559146b11d6fb05f7990182eedd38e4f`
**Revised**: 2026-07-20-2313 by user request; this lean override replaces the remaining strict qualification and rerun gates.

## Execution intent

The campaign answers an engineering question, not a benchmark question: can the repository-configured OMP `openai-codex/gpt-5.6-sol` xhigh and Grok CLI `grok-4.5` high produce useful Atlas source summaries from one provider-neutral product surface?

That question is already answered by the completed runs:

- Both lanes produced 30/30 deterministically valid cohort artifacts.
- The direct-cwd OMP reviewer produced complete pairwise and staged-baseline review corpora.
- Review orientation changed material judgments often enough that model-review outcomes are descriptive, not a reliable provider-neutral ranking or promotion gate.
- One paper bundle exposed a campaign evidence-packaging defect; more generation cannot repair evidence absent from the prompt.

Completion therefore preserves the durable quality seam—source-only evidence, honest coverage, the shared template, deterministic validation, the seven-item checklist, and provider-neutral product text—while dropping campaign machinery that does not improve source artifacts.

## Lean completion decisions

1. **No more model reruns.** Do not build an evidence successor for `a2cb64316448`; do not resume repairs for `108d87a4b26b`; do not rerun affected pairwise or baseline rows. Preserve the current `none` outcomes as limitations.
2. **Comparison, not adjudication.** Freeze one descriptive report over existing T5–T8 evidence. A 30/30 non-`none` reducer result is no longer required. No generated comparison candidate becomes promotion authority merely because the OMP reviewer selected it.
3. **No universal provider winner.** Report objective generation reliability and the reviewer’s observed preferences separately. State prominently that the reviewer used OMP GPT-5.6-sol xhigh and that orientation instability limits ranking claims.
4. **Accepted staging remains the promotion source.** The pass-1 accepted manifest plus its complete deterministic sweep is sufficient for this one campaign. Do not semantically re-review the other 447 rows and do not generate repair candidates.
5. **Runtime quality stays simple.** Normal source generation uses the repository-configured active SOTA harness from the app working directory, one source-only envelope, the shared template, `validate-summary`, and the seven-item checklist. At most one targeted revision follows a failed item.
6. **Calibration becomes optional.** Keep the 32-case fixture and `validate-calibration` as read-only developer diagnostics; remove them as a mandatory first-write or per-harness mutation gate.
7. **Prior accepted staged selection is reusable.** `--promote-staged` may reuse a hash-bound accepted campaign row instead of invoking a fresh semantic reviewer. Exact identity/evidence/artifact agreement and `validate-summary` remain hard requirements.
8. **No new harness framework.** Add no controller, reviewer protocol, schema package, sandbox, provider adapter, lifecycle journal, or campaign test framework. Existing campaign machinery is historical evidence and is deleted only at approved cleanup.
9. **Two safety approvals remain.** Living synchronization/promotion and deletion of the two temporary roots still require their explicit approvals. These are the only remaining pauses.

## Historical evidence retained

| Evidence | Result |
|---|---|
| `reports/t5-qualification.json` (`sha256:dc0fa2f7ce67c02fc0d8d076af160c16fc91879703b4a5afd2557cdc299856e7`) | Both configured lanes passed the frozen calibration and native-surface exercises. |
| `reports/t6-omp-qualification.json` (`sha256:f94a754611e3e40f93005b70c3fa00a7e8d123fbaa9bdaa42d8a5332f7bd7c9e`) | OMP produced 30 deterministic-pass candidates: 28 at `g0`, one at `g1`, one at `g2`. |
| `reports/t7-grok-qualification.json` (`sha256:bdc369258313d0457674f2a3916f93e9bf4513e48bceeb9daffcce490578825f`) | Grok produced 30 deterministic-pass candidates: 25 at `g0`, four at `g1`, one at `g2`. |
| `reports/iterations/dual-orientation-reviewer-01/manifest.json` (`sha256:a49ee7f9ff0a9238f4197d3df8a941d709203cd57eb8dc8a7c1cf67b5d489b3d`) | Frozen commutative reducer and direct-cwd reviewer configuration. |
| `reports/t8-recovery-blocked-01.json` (`sha256:7a8e47ffdba86e733164211e09d998a1914a552fed60b8b343c036eadd90d003`) | First capped repair blocker; preserved. |
| `reports/t8-recovery-blocked-02.json` (`sha256:2d3dbcd6ce9f7ffbdf77daf482e17be12c72798a875d33403e6b269b8da495cc`) | Temporary reviewer quota blocker; later resolved. |
| `reports/t8-recovery-blocked-03.json` (`sha256:0b93b03c468583589b39ca42d918e98b95f9cbf3cb7911b82620cd4f49b3b011`) | Final strict-gate state: pairwise 28 selected/2 `none`; baseline 27 selected/3 `none`; all 60 baseline orientations present. |

The `a2cb64316448` bundle’s `coverage:"complete"` claim conflicts with its model-visible truncation after Chapter 14. Record this as an evidence-package limitation and exclude that row from provider-quality conclusions. Do not edit the frozen bundle or infer that the shared Atlas contract failed.

## Tasks

- [x] T1. Freeze and fixture-test the commutative reducer
  - completed 2026-07-20-1423
- [x] T2. Complete dual-orientation pairwise review and repairs
  - completed 2026-07-20-1717
  - Historical strict acceptance was later invalidated by repair lineage. The complete review corpus remains valid descriptive evidence; current state is 28 selected and two `none`.
- [x] T3. Complete dual-orientation staged-baseline review
  - completed 2026-07-20-2313 under the user-approved descriptive criterion
  - All 60 orientation reviews and 30 swap-invariant reductions exist. Current baseline state is 27 selected and three `none`; no rerun is required.
- [x] T4. Freeze comparison and apply lean framework refinement
  - completed 2026-07-20-2320
  - `COMPARE/reports/t8-comparison-final.json` (`sha256:f237ce97c14bcc5c369ddd96c0a4e6b1589db2d6d2397983f3219aa9d3092d2f`) binds the existing qualifications, blockers, resolution indexes, limitations, and lean product hashes. Focused repository verification ran 62 tests (`OK`); reducer fixtures ran six tests (`OK`); no model call ran.
- [x] T5. Build lean 477-row disposition map
  - completed 2026-07-20-2331
  - Final preflight map `COMPARE/reports/promotion-maps/map-lean-v3.json` (`sha256:7d34f1bd5eaadc170f32347c5a4dcb68c8302b8563c29d7767cc02e4d65465da`) supersedes the preserved v1/v2 maps. It contains 475 `promote-staged` and two `preserve-newer-living` rows, excludes all six nonaccepted rows, and projects final living count 523.
  - Preflight found 15 accepted envelopes whose staged `content_hash` binds complete readable content while `payload_text` is the bounded model-visible projection. `reports/promotion-projections/evidence-content-hash-record.json` (`sha256:173484c0afa49a541104a6f33156c0108216707058c3aa87f1252535eb7e2a6b`) adds explicit hashes without changing payload or artifact semantics. It also preserved the earlier `d80c4110de71` canonical-URL projection and added one rendered-metadata projection for `d8ff876dfb1e` (`sha256:f332822a189c74e9beb4fd86fefbb990d0a5214fd29b19a8f3e7ae32c480a2f2`).
  - Source merge now accepts explicit complete-content hashes for bounded payload projections and normalizes schema-valid block-sequence frontmatter. `scripts/atlas_source.py` is `sha256:ed75ca937c3ad675a03d31d05c4c595e0c27b90b8ab5d8c0fbd5e458d241351b`; 12 focused source tests passed.
  - Full in-memory promotion plus deterministic routing preflight succeeded: 475 projected artifacts, final manifest count 523, 138 routed / 337 no-topic-match, 209 new pending edges, and zero final registry findings.
- [x] T6. Obtain approval, promote, and reconcile living state
  - completed 2026-07-21-0010
  - User approved map v3 at `2026-07-21T00:00:37+07:00`; `COMPARE/reports/promotion-approval-v3.json` is `sha256:e32a6bb22082a902057b80a41454cb91f8296476c76f90ad5d482aab9ed81e0f`. Framework sync and its immediate instance check passed after approval.
  - All 475 source-upsert and 475 route-upsert transactions terminalized `applied`; zero terminal anomalies or manual conflicts occurred. The two preserved newer living sources remained byte-identical.
  - Final reconciliation: 523 manifest rows, all 477 accepted IDs present, 138 promoted sources routed, 337 no-topic-match, 209 new pending edges, zero registry/artifact/identity/path findings, and matching product/living architecture hash `6c10ec55240b4d0f16133e430a7b8296b02b95ab06f0f6261e1a9ea0325deb48`.
- [x] T7. Persist final audit, obtain cleanup approval, and archive
  - `COMPARE/reports/final.json` (`sha256:35f0ccaaceb17953eb62b531b78e2316bbb525868635fed5c46fcbd0338d7044`) freezes comparison, product, approval, transaction, reconciliation, and verification facts before cleanup.
  - User explicitly approved deletion of both named temporary roots at `2026-07-21T00:33:20+07:00`; `COMPARE/reports/cleanup-approval.json` is `sha256:40213f575e18ae72e99eab2aed5a5b3d38906837017afcc4d77131fe8b6bd038`.
  - completed 2026-07-21-0036
  - Both approved temporary roots were deleted after the recorded approval. `vault://atlas/tmp/` is empty; living and product surfaces contain no stale campaign-root reference.
  - Post-cleanup verification ran 79 focused tests (`OK`), `atlas-instance.py check --name atlas` (`check OK`), a zero-finding registry validation with final hashes unchanged from the audit, and the canonical URL/source-ID smoke.

## Ordered implementation

### T4. Freeze comparison and refine the durable quality seam

1. Write only `COMPARE/reports/t8-comparison-final.json`; do not create a governing-selection tree or another verifier/controller.
2. Bind the T5, T6, T7, reducer-manifest, three blocker, current pairwise-resolution, and current baseline-resolution hashes.
3. Record exact observed counts:
   - candidate deterministic pass: OMP 30/30 and Grok 30/30;
   - first passing generation: OMP `28 g0 / 1 g1 / 1 g2`, Grok `25 g0 / 4 g1 / 1 g2`;
   - current pairwise: OMP 27, Grok 1, `none` 2;
   - current baseline: OMP-generated 26, Grok-generated 1, staged 0, `none` 3;
   - orientation selection agreement: pairwise 25/30 and baseline 28/30.
4. State the bounded conclusion: both configured harnesses are viable; OMP needed fewer generation repairs in this cohort; the OMP-reviewed semantic result favors OMP but cannot establish a provider-neutral winner; the source-only product contract transferred without a provider branch.
5. Apply the already-authorized lean product refinement in this order:
   - `.agents/skills/atlas-core/assets/source-summary-quality-guide.md`: make calibration an optional developer diagnostic and specify the one-draft/one-targeted-revision runtime loop.
   - `.agents/skills/atlas-core/SKILL.md`: remove calibration as a prerequisite for first write; keep the fixture discoverable for audits.
   - `.agents/skills/atlas-source/SKILL.md`: remove the write-support calibration stage; use the active repository-configured harness from the app directory; allow a hash-bound accepted staged row to satisfy promotion’s prior semantic-selection requirement; retain deterministic validation and exact source/evidence checks.
   - `.agents/skills/atlas-audit/SKILL.md`: retain `--source-quality-calibration` as an optional read-only diagnostic.
6. Do not change `.agents/ARCHITECTURE.md`, rules, command stubs, templates, fixture expectations, or Python reducers/validators unless a focused test proves a direct contradiction. The invariant and write set do not change.
7. Run focused source-quality, source-reducer, harness-surface, and instance tests. No model call is part of T4 verification.

### T5. Build the promotion disposition map without a 447-row model audit

1. Reuse the archived pass-1 accepted manifest and `runs/closure/deterministic-sweep.json`; re-run `validate-summary` over the 477 accepted artifact/evidence pairs only if the product validation code changed.
2. Capture one read-only living manifest/artifact snapshot after T4.
3. Write one source-ID-sorted `COMPARE/reports/promotion-maps/map-lean.json` with exactly 477 unique accepted rows. Each row binds the staged manifest row, artifact/evidence paths and hashes, normalized identity, staged content hash, current living hash when present, and one disposition:
   - `promote-staged` when the source is absent or living content hash matches staging;
   - `preserve-newer-living` when the same source ID has a different living content hash.
4. Never overwrite a differing living hash, refetch it, or regenerate it in this campaign. It counts as reconciled when the canonical source ID remains present and the current living artifact validates.
5. Require the failed row `fd3fe07e32f0` and five quarantine rows to be absent. Hash the map and record disposition counts.

### T6. Approve once, then use the existing safe write path

1. Present the map hash, disposition counts, expected final source-count formula, sync target `atlas`, and write roots `vault://atlas/ARCHITECTURE.md` and `vault://atlas/summaries/`. Obtain explicit promotion approval before the first bound-instance write.
2. After approval, sync the product-owned framework snapshot and run `python3 scripts/atlas-instance.py check --name atlas`.
3. For every `promote-staged` row, execute the existing `atlas-source --promote-staged` path with the map/row binding. Let the owning skill, `scripts/atlas_state.py`, and `scripts/atlas_source.py` handle optimistic checks, transaction recovery, merge, and routing. Do not add campaign orchestration abstractions.
4. Leave `preserve-newer-living` rows byte-unchanged.
5. Reconcile all 477 accepted source IDs as promoted/no-op/preserved, verify unique normalized identity, terminal route state for written rows, no `tmp/` artifact path, complete state validation, and a clean instance check.

### T7. Retain the result, clean with approval, and archive both plans

1. Write concise `COMPARE/reports/final.json` with comparison-report hash, product hashes, promotion-map hash, approval hash, disposition/transaction/reconciliation counts, final registry hashes, and verification results.
2. Append the same compact facts to both active plans so the archived plans remain the durable audit after campaign deletion.
3. Present the final report hash and exact temporary roots:
   - `vault://atlas/tmp/todos-source-summaries-2026-07-15/`
   - `vault://atlas/tmp/source-summary-cross-harness-2026-07-16/`
4. Obtain explicit cleanup approval naming both roots. Delete only those roots, then prove they are absent and no living/product path references them.
5. Run focused Atlas tests and the instance check, complete every remaining checkbox, set both plans `DONE`, append completion summaries, and atomically move both plans to `.agents/plans/archive/`.

## Critical anchors

- Parent plan: `.agents/plans/2026-07-16-1211_atlas-source-summary-cross-harness.md`
- Accepted staging closure: `STAGING/runs/closure/deterministic-sweep.json` and `STAGING/manifest/MANIFEST.md`
- Comparison qualifications: `COMPARE/reports/t5-qualification.json`, `t6-omp-qualification.json`, `t7-grok-qualification.json`
- Current review evidence: `COMPARE/reports/dual-orientation/resolutions/{pairwise,baseline}/`
- Promotion owners: `.agents/skills/atlas-source/SKILL.md`, `scripts/atlas_source.py`, `scripts/atlas_state.py`
- Durable quality owners: `.agents/skills/atlas-core/assets/source-summary-quality-guide.md`, `.agents/skills/atlas-core/SKILL.md`

## Verification / Done criteria

```bash
python3 -B COMPARE/reports/iterations/dual-orientation-reviewer-01/test_dual_review.py
python3 -m unittest \
  tests.test_atlas_source tests.test_atlas_state tests.test_atlas_quality \
  tests.test_atlas_harness_surface tests.test_atlas_instance
python3 scripts/atlas-instance.py check --name atlas
```

- [x] The comparison report binds the existing evidence and reproduces the observed counts without any new model call.
- [x] Product text has one provider-neutral runtime path: evidence envelope → draft → deterministic validation → seven-item checklist → at most one targeted revision.
- [x] Calibration remains available as a read-only diagnostic but is not a source-write prerequisite.
- [x] The promotion map contains exactly 477 accepted IDs with only `promote-staged|preserve-newer-living`; all six excluded rows are absent.
- [x] Explicit approval of map v3 predates framework sync and every living write.
- [x] All 477 accepted IDs reconcile to valid living sources, with clean state validation and instance check.
- [x] Explicit cleanup approval names both deleted roots; both plans are `DONE`, have completion summaries, and are archived.

## STOP conditions

- An accepted staged artifact/evidence pair fails deterministic validation or has an identity conflict that cannot be resolved by a manifest-authoritative, metadata-only campaign projection.
- A living source has a conflicting canonical identity rather than only a newer content hash.
- Existing transaction recovery reports `manual-conflict` or cannot restore/complete safely.
- T6 reaches the living-write approval gate or T7 reaches the destructive-cleanup approval gate.

## Completion summary

- **Outcome:** Closed the OMP/Grok exercise as a descriptive comparison, retained one provider-neutral evidence → draft → deterministic validation → seven-item checklist → one-revision runtime path, and kept calibration optional.
- **Promotion:** Reconciled all 477 accepted IDs into 523 valid living sources. All 475 source and 475 route transactions applied; two newer living rows were preserved; 138 promoted sources routed, 337 had no topic match, and 209 pending edges were created.
- **Audit retained here:** Final campaign report `sha256:35f0ccaaceb17953eb62b531b78e2316bbb525868635fed5c46fcbd0338d7044`; manifest `a886d1d70ec1de5580b30850292809027a3cb9293af9dd3a65bc4f2dff4bcaa5`; topics `beab817b9e24d4dfa124b6c290cac3e4c3038d016f1072f5857a53b90ac86320`; relations `221550218f6dfc4ac83bccadc6236d28a8c35a3b6b0ef62da6f2faf2d9c7f3f5`.
- **Deviation:** The approved lean revision replaced strict rerun and universal-selection gates. Promotion preflight required metadata-only projections for one canonical URL, 15 explicit complete-content hashes, and one rendered metadata field, plus corresponding source-merge parser support; no semantic source text or frozen staging input was rewritten.
- **Verification:** 79 focused tests passed; instance check passed; final registry validation returned zero findings; product and living architecture hashes match; normalization returned `https://x.com/example/status/1?foo=a&bar=b` / `abca97778de4`; both approved temporary roots are absent.
- **Remaining work:** None.
