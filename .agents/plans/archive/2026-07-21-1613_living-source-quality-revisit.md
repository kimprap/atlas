# Living source quality revisit (phased)

**Datetime**: 2026-07-21-1613
**Scope**: Frozen 503-source cohort on bound instance `atlas`; immediate promotion of lean text-only source-ingestion rules into the Atlas product; one bounded cohort review; no living rewrite before exact manifest approval
**Summary**: Stop the low-ROI exhaustive verifier campaign, productize the durable evidence and drafting lessons first, run one lean deterministic cohort review, and either open a separately approved rewrite manifest or switch to a ten-source cross-harness calibration plan. Source artifacts remain text-only; inaccessible or insufficiently textual links halt; aggregate pages require one concise scope clarification.
**Status**: DONE

## Execution intent

When done:

1. Every frozen living source has Phase-1 deterministic triage.
2. T4V6–T4V9 remain historical execution or negative evidence, not product runtime and not direct approval authority.
3. T4P makes future `atlas-source` behavior lean and durable before another cohort decision: accessible canonical text only, no retained media/assets, source-only drafting, exact text hashes, concise aggregate-page clarification, and fail-closed no-write outcomes.
4. T4L runs once over the frozen cohort with current product validators and a fixed regression set derived from every observed false-positive class; it does not build another combinatorial mutation harness.
5. Living artifact rewrites occur **only** if T4L is independently accepted and the user separately approves exact T4.5 manifest bytes or a deterministic subset.
6. If T4L tooling or review remains incomplete, T4.5 does not open. A separate ten-source comparative calibration plan becomes the next plan; no T4V10/T4V11 verification iteration is created.
7. A durable run log exists; the temp root is deleted only after cleanup approval; registries validate; the known pre-existing missing-`todos/` instance finding remains baselined unless repaired outside this plan.

## Context (fixed at plan authoring; re-count at T2)

| Fact | Value |
|---|---|
| Living sources | **503** active |
| Routed | **183** |
| no-topic-match | **320** |
| Registry validate | Zero findings (at authoring) |
| Instance check | **Fails**: missing `seed_once` path `vault://atlas/todos/TODOs.md` (removed by user earlier) |
| Staging envelopes | Deleted; re-capture required for evidence-backed work |
| Product gate | Open canonical text → clarify page-only vs child expansion only for an aggregate page → text-only envelope → draft → separate checklist → `validate-summary` → ≤1 revision → classify/route |

## Prerequisite (outside this plan’s write set)

**Choose one before T2, record the choice in the plan Completion path:**

| Option | Action |
|---|---|
| **A (recommended if clean check wanted)** | Separate bound-instance authorization: re-seed empty `todos/TODOs.md` from scaffold **only** if user explicitly approves that repair; then require full `atlas-instance.py check` green for the whole plan. |
| **B (default if todos stays gone)** | Baseline the known finding `instance missing seed path: vault://atlas/todos/TODOs.md`. Require final check to report **only** that known finding (no new findings). Do **not** recreate TODOs inside this plan. |

Default for execution unless user picks A at start: **B**.

Recorded execution choice at T2: **B**. Later executors must preserve that baseline unless the user separately authorizes prerequisite A; there is no remaining choice inside this plan.

## Tasks

- [x] T1. Materialize plan under `.agents/plans/`
  - completed 2026-07-21-1652
- [x] T2. Phase 0 — freeze inventory and baseline
  - completed 2026-07-21-1658 (prerequisite B; 503/183/320; registry validate 0; missing artifacts 0)
- [x] T3. Phase 1 — artifact-only triage (`atlas-audit` procedure)
  - completed 2026-07-21-1658 (501 pass, 2 structural_fail; P1=183 P2=69 P3=0)
- [x] T4. Phase 2 — capture, classify drift, same-hash semantic review
  - completed 2026-07-21-1710 — **SUPERSEDED as authority** (capture incomparability; see T4R). Artifacts kept under `captures/` + `reviews/` as negative execution evidence only.
- [x] T4R. Recover T4 — procedure-aligned recapture + reclassify + re-review (no living writes)
  - completed 2026-07-21-1745 — **SUPERSEDED as authority** (see T4S). Keep `captures-v2/`, `reviews-v2/`, `rewrite-manifest-v2.json` as negative evidence.
- [x] T4S. Bounded successor recapture (v3) — integrity fix only; no living writes
  - completed 2026-07-21-1840 — **SUPERSEDED as authority** (see T4V4). Keep `captures-v3/`, `reviews-v3/`, `rewrite-manifest-v3.json` as negative evidence.
  - Rejected approval SHA-256: `4d4dd268a5c93a322454b9104eb4e8ca99a06dabea2c916ec8f8c5bd8244e24d`
  - Defects: media `bytes_only` + complete coverage; X partial→complete by omission; binary PDF payloads; mutable external GH media
- [x] T4V4. Bounded successor recapture (v4) — evidence integrity only; no living writes
  - completed 2026-07-22 — **SUPERSEDED as approval authority by T4V5**. Preserve every T4V4 byte and A–G handoff as execution evidence; none may feed T4.5 directly.
  - Historical final checkpoint: 151 X targets; 147 status records; 4 profile records; 503 capture/classification rows; 6 same-hash review records; no living writes and no `rewrite-manifest-v4.json`.
  - Completion review found: 122 public-fxt status responses mislabeled as first-class `x_thread_fetch`; 78 X-native Article projections flattened from structured blocks, including 55 marked complete without sufficient structured-completeness proof and 41 complete rows with uninspected Article media entities; 122 accepted raw files mutated after exclusive creation; 4 profile evidence envelopes outside the product evidence schema; 101 rows with invalid/uninspected evidence-media state; 259 classification rows missing living coverage; and all 224 `source_changed` rows justified only by an assumed procedure match.
  - [x] T4V4-A. Repair and verify the X raw-freeze and semantic-projection helpers
    - completed 2026-07-21 (handoff `indexes/handoffs/T4V4-A.json`)
  - [x] T4V4-B. Supersede and rematerialize the five derived X smoke captures
    - completed 2026-07-21 (handoff `indexes/handoffs/T4V4-B.json`)
  - [x] T4V4-C. Capture the remaining 142 X status URLs in immutable batches
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V4-C.json`; later completion review rejected 122 status records as truthful first-class freezes)
  - [x] T4V4-D. Resolve the four X profile surfaces without credentials
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V4-D.json`; evidence envelopes require v5 correction)
  - [x] T4V4-E. Audit all 503 v4 evidence outcomes and classify comparability
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V4-E.json`; classification superseded)
  - [x] T4V4-F. Run hash-bound same-hash reviews and finalize dispositions
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V4-F.json`; reviews are reusable only by exact v5 hash validation)
  - [x] T4V4-G. Freeze the T4V4 completion handoff and open the T4.5 gate
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V4-G.json`; gate opening rejected by completion review)
- [x] T4V5. Recover T4V4 completion integrity — provenance, evidence, and classification only; no living writes
  - mechanically completed 2026-07-22 — **SUPERSEDED as approval authority by T4V6**. Preserve every T4V5 byte and A–F handoff as execution/negative evidence; none may feed T4.5 directly.
  - Post-completion audit reproduced the reported F hash and counts but rejected completion: five selected authority rows have invalid effective-content or complete-content bindings; `8b4da8b50a8d` is rewrite-eligible despite `evidence_payload_vs_file` and `payload_projection_true`; the delivered verifier omits required recomputation; the helper command surface drifted; and T4V5-F has empty `output_hashes` with no selected-files digest.
  - [x] T4V5-A. Implement the isolated v5 helper; freeze defects and the 503-row action plan
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V5-A.json`; helper `helpers/t4v5.py`; defects counts matched the v5 plan)
  - [x] T4V5-B. Process exactly 122 X statuses to truthful first-class captures or terminal no-write outcomes
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V5-B.json`; 13 batches; 122 accepted first-class)
  - [x] T4V5-C. Repair bounded evidence defects and freeze the final 503-row capture authority
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V5-C.json`; later strict audit rejected five authority rows)
  - [x] T4V5-D. Classify all 503 rows through the fixed decision table
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V5-D.json`; pre-review 6 needs_same_hash_review; later strict audit rejected one rewrite-eligible classification)
  - [x] T4V5-E. Produce source-isolated, locator-backed same-hash reviews
    - completed 2026-07-22 (handoff `indexes/handoffs/T4V5-E.json`; 3 pass_current, 3 quality_fail)
  - [x] T4V5-F. Attempt the complete verifier and intended T4.5 predecessor
    - mechanically completed 2026-07-22 (handoff `indexes/handoffs/T4V5-F.json`, SHA-256 `bb41035ab8589739e3f97d73a66f4a922cb69c2074652223205960e6513e06a8`; **rejected as T4.5 predecessor**)
- [x] T4V6. Attempt recovery of T4V5 false-positive completion through an independent strict verifier; no retrieval or living writes
  - mechanically completed 2026-07-22-0627 — **SUPERSEDED as approval authority; T4V7 and T4V8 were also rejected, and T4V9 is the planned successor**. Preserve all T4V6 bytes as execution/negative evidence; T4V6-E may not feed T4.5 directly.
  - Mechanical authority: 487 `v5_capture_reuse` + 16 `v6_terminal` = 503; selected-files digest `b9f94394bb8a69c4786561b390df8993237f9b19c3e66624e62ae37ea1108ea9`.
  - Mechanical final dispositions: blocked_evidence_regression 265, hash_baseline_incomparable 221, blocked_fetch 11, quality_fail 3, pass_current 3; claimed rewrite-eligible pre-approval 224.
  - Helpers: `helpers/t4v6.py` SHA-256 `1a853cc10a57a96889f7a2f774caa9947408414ff3df7d7abaffcc01cf0f49c2`; `helpers/t4v6_verify.py` SHA-256 `9600f8734f71d6b4be33fef28e2d62fe62d8bb250e06f429ef8f58dd381a358d`.
  - Contract SHA-256 `8e8a6ed9938ded8c3c265adf4fe1f15f6403c3447cac0096bc29e709e93930c4`; T4V6-E SHA-256 `d2462180b6f3281a08cf43ff0bb8225c3c3daeff28800f774419120e3b030739`; verification `74700a6a2d7ac5ec610728b7d232fd38d9d1af4ba8e07df8ecf9db9ae53d0cca`.
  - Post-completion mutation audit reproduced a false negative: changing the in-memory candidate `output_hashes.authority` to 64 zeroes and final E `output_hashes.authority` to 64 `f` characters still returned `findings: []` and no false check. The final verifier checks only map non-emptiness, not exact keys/values/paths; its self-test tests generic hash sensitivity rather than the protected graph.
  - No living writes; `indexes/rewrite-manifest-v4.json` absent.
  - [x] T4V6-A. Freeze the v6 execution contract and independently enumerate all v5 defects
    - completed 2026-07-22-0627 (handoff `indexes/handoffs/T4V6-A.json` SHA-256 `622e4e8ddbbf1671774b80b26d4003fa6df4e24ebdd4d76970a618ac0b32cf64`; 5 invalid capture IDs + 11 carried terminals + 5 global V5 defects)
  - [x] T4V6-B. Build a strict 503-row authority from exact v5 reuse or v6 terminal outcomes
    - completed 2026-07-22-0627 (handoff `indexes/handoffs/T4V6-B.json` SHA-256 `22778456ca03afb78b9492a33e35af355c6bf249b2a711e3286582ada07b1cf4`; authority `8f1c019eeb838151f89375cb7b651bbff28d0c310962ed667280d642f3b156b8`)
  - [x] T4V6-C. Reclassify all 503 rows and freeze the exact six-row review plan
    - completed 2026-07-22-0627 (handoff `indexes/handoffs/T4V6-C.json` SHA-256 `ef381082dc1646698acc36143e93254f739e7c31cb63aa60632cf2a4b84d691b`; pre-review 265/11/221/6)
  - [x] T4V6-D. Strictly revalidate and reuse the exact six source-isolated same-hash reviews
    - completed 2026-07-22-0627 (handoff `indexes/handoffs/T4V6-D.json` SHA-256 `ecf182f8f87062a064413aeb769a8a462ee09da7b3d186409ef875c662a7143a`; 3 quality_fail + 3 pass_current; no model rerun)
  - [x] T4V6-E. Attempt independent recomputation and freeze the intended T4.5 predecessor
    - mechanically completed 2026-07-22-0627 (candidate `71c2b7e1c4e0aa358ef432b6814a7e8305b538876e24e4b013ebad02c8c0ae9d`; E `d2462180b6f3281a08cf43ff0bb8225c3c3daeff28800f774419120e3b030739`; **rejected as T4.5 predecessor**)
- [x] T4V7. Rejected attempt to recover T4V6 false-positive verification; terminal rejected/negative outcome
  - [x] T4V7-A. Froze independent writer, verifier, adversary, and protected-graph contract; retained as negative evidence
  - [x] T4V7-B. Ran black-box graph mutations and independent recomputation; external review rejected the result
  - [ ] T4V7-C. Obtain separate external acceptance before opening T4.5 — **not reached; abandoned after external rejection**
  - external review rejected 2026-07-22-1458 — T4V7-A/B frozen bytes were execution/negative evidence only; no external acceptance existed and T4.5 remained blocked through this line.
- [x] T4V8. Rejected attempt at nonrecursive split-authorship verification; terminal rejected/negative outcome
  - rejected at T4V8-B after external pre-accept review: baseline verification passed, but the adversary caught only 3685/3688 mutations and produced `findings: ["uncaptured:3"]`.
  - The two helpers, contract, and pre-accept reports were retained as execution/negative evidence until the later approved cleanup. No T4V8 artifact fed T4.5.
  - [x] T4V8-A. Implemented two separately authored read-only modules and froze the declarative contract
  - [x] T4V8-B. Ran deterministic pre-accept verification and mutation reports; result rejected
  - [ ] T4V8-C. Create provisional external acceptance, validate it post-accept, and bind exact accepted hashes — **not reached; abandoned after pre-accept rejection**
- [x] T4V9. Rejected low-ROI exhaustive verification attempt; terminal rejected/negative outcome
  - Five-role execution took about five hours, never sealed R5 or any Atlas T4V9 path, and stopped at 6715/7365 caught mutations with 650 uncaught cases plus harness failures.
  - [x] T4V9-A. Historical candidate authorship attempt completed as non-executable negative evidence
  - [x] T4V9-B. Historical exhaustive rehearsal attempted and rejected
  - [ ] T4V9-C. Historical seal/acceptance step — **not reached; abandoned**
- [x] T4P. Productize lean text-only source ingestion before another cohort review
  - completed 2026-07-23-1739 — see `T4P accepted productization` annotation under Ordered implementation / T4P-D
  - [x] T4P-A. Promote concise text-only, accessibility, and aggregate-page interaction invariants
    - completed 2026-07-23-1739
  - [x] T4P-B. Simplify deterministic text evidence and disposition validation
    - completed 2026-07-23-1739
  - [x] T4P-C. Refine source drafting guidance and flexible quality calibration
    - completed 2026-07-23-1739
  - [x] T4P-D. Verify product behavior and bind exact product hashes in this plan
    - completed 2026-07-23-1739
- [x] T4L. Run one lean deterministic cohort acceptance review
  - completed 2026-07-23-2009 — `ACCEPTED_FOR_T4_5`; exact report hashes and counts are bound under Ordered implementation / T4L-C
  - [x] T4L-A. Validate all 503 actual rows with product rules
    - completed 2026-07-23-2009
  - [x] T4L-B. Run fixed regressions for every prior false-positive class
    - completed 2026-07-23-2009
  - [x] T4L-C. Obtain independent accept/reject review and choose the gated next path
    - completed 2026-07-23-2009 — independently accepted; T4.5 still requires separate explicit user authorization
- [x] T4.5. Freeze rewrite-manifest-v4 only from accepted T4L output and obtain living-write approval
  - completed 2026-07-23-2216 — user approved exact candidate SHA-256 `9cd10cb1c6ddfea3ef4e13808e08042877b5e9775ec32431523bea63ed06b66b` for both eligible rows; T5 execution remains separately blocked
- [x] T5. Phase 3 — rewrite only the approved queue (`--resummarize`)
  - completed 2026-07-23-2235 — both approved IDs rewritten same-hash; see Ordered implementation / T5 completion
- [x] T6. Phase 4 — validate; report reducer-affected topics; optional refresh gate
  - completed 2026-07-23-2242 — validate 0 findings; instance check B-only; affected_topic_ids []; no refresh
- [x] T7. Durable run log; cleanup approval; temp delete; archive plan
  - completed 2026-07-28-0222 under Plan A terminal cleanup authority

## Ordered implementation

### T1. Materialize plan

1. Write this plan to  
   `.agents/plans/2026-07-21-1613_living-source-quality-revisit.md`  
   with matching **Datetime**.
2. Set **Status**: `IN_PROGRESS` when T2 begins.
3. Do not change `.agents/ARCHITECTURE.md`.

### T2. Phase 0 — freeze inventory and baseline

**Temp root (working only):**  
`vault://atlas/tmp/source-quality-revisit-2026-07-21/`

**Layout:**

```text
inventory/
reviews/
rewrites/
indexes/
```

1. Re-count MANIFEST; freeze `inventory/snapshot.json` (source-id sorted):  
   `source_seq`, `source_id`, `canonical_url`, `artifact`, `route_status`, `content_hash`, `first_seen`, `manifest_row_sha256`, `artifact_sha256`.
2. Counts: total / routed / no-topic-match / host class (`github|x.com|other`).
3. `atlas_state.py validate` → require **zero** findings.
4. `atlas-instance.py check --name atlas` → apply prerequisite **A** or **B** above.
5. Halt if any artifact path is missing.

### T3. Phase 1 — artifact-only triage

Own procedure: **`atlas-audit`** read-only style (artifact + registries as needed). No envelopes, no living writes.

**Statuses (exact):**

| Status | Examples |
|---|---|
| `pass` | No deterministic concern |
| `needs_evidence_review` | Generated/repository context regex hit; ambiguous locator; claim needing source evidence to judge |
| `structural_fail` | Invalid frontmatter, missing section, placeholder, invalid enum, assessment table mismatch, invalid adopt **tuple** (high/high/stable only—no unresolved-caveat without evidence) |
| `unparseable` | Cannot parse via normal source assembler path |

**Outputs:** `indexes/triage.json` + per-row records if useful.

All non-`pass` IDs outside P1/P2 enter **P3** for Phase 2. Only Phase-2 evidence-backed results authorize a **quality** rewrite.

### T4. Phase 2 — capture, drift, same-hash review (historical; SUPERSEDED)

Original T4 + T4R + T4S outcomes are retained as checked historical tasks. T4V4 subsequently completed but failed completion review; capture/classification authority is now **T4V5**. Do not use `indexes/rewrite-manifest.json`, `rewrite-manifest-v2.json`, `rewrite-manifest-v3.json`, `indexes/phase2_classify_v4.json`, or `indexes/phase2_summary_v4.json` for T5.

Original cohort design (P1/P2/P3, P2 expansion) remains historical context only. T4V5 classifies the **full library** (503) for rewrite eligibility; model semantic review applies only to comparable same-hash rows.

### T4S. Bounded successor recapture (v3) — SUPERSEDED

Historical only. Manifest SHA-256 `4d4dd268…8244e24d` must **not** be approved. Defects: media `bytes_only` with `coverage: complete`; X fxtwitter partial→complete by omission; binary PDF payloads; mutable external GH media. Artifacts under `captures-v3/` / `reviews-v3/` retained as negative evidence.

### T4V4. Bounded successor recapture (v4) — completed, then superseded

#### Historical authority and checkpoint

- Preserve `captures/`, `captures-v2/`, `captures-v3/`, `captures-v4/`, their matching reviews, all raw/transport sidecars, and all superseded manifests/handoffs as immutable execution evidence. Never promote an output merely because its T4V4 handoff reported success.
- Former authority paths were `captures-v4/`, `reviews-v4/`, `indexes/phase2_classify_v4.json`, `indexes/phase2_summary_v4.json`, and T4V4-A…G handoffs. T4V5 may select a still-valid per-source v4 capture or review only by exact hash; the aggregate v4 classification and G handoff are not approval authority.
- `indexes/rewrite-manifest-v4.json` was not created. T4.5 may create it only after T4V5-F passes.
- T4V4-C opened with 5 accepted status raws and 142 pending. The intermediate reviewed checkpoint was 20 accepted and 127 pending: batch 0001 terminal 10/10; batch 0002 five accepted and five pending.
- Preserve every file under `indexes/x_raw_v4/` byte-for-byte, including post-creation annotations and mislabeled records. They are historical evidence, not v5 first-class raw authority. The five flawed pre-B captures remain under `captures-v4-x-derived-SUPERSEDED/`.
- Batch 0002’s five accepted IDs are `29d60ad36ead`, `2abb38a5d19b`, `2f40a62aa3ed`, `2f5bf37a8ca5`, and `36074526e1e1`. Its five pending IDs are `1ada9d65ee1b`, `1ff02e7f5eb2`, `23b9a79a0128`, `25509e16f696`, and `28279f4d7e09`.
- `cbe23bddd592` now retains the original 879,864-byte PDF, SHA-256 `87f7f0f323b1671e9202b3ebb1596e909e507c71ecd1b360b0075a5ee1727fe3`, plus `pdftotext` pages 1–27. Any progress note saying “no binary” is stale and must be corrected.
- T4V4 may mutate only this plan and `vault://atlas/tmp/source-quality-revisit-2026-07-21/`. It must not write living artifacts, `MANIFEST.md`, `TOPICS.md`, or `RELATIONS.md`.

#### Path and execution isolation

- All records use logical `vault://atlas/…` paths. Throwaway helpers must accept an explicit connector-resolved temp root or operate through vault tools; they must not embed `/Users/...` or another workstation path in code, metadata, or handoffs.
- Run product Python from the Atlas app working directory. Temporary helper code stays under `helpers/`; do not add a second product CLI or modify `.agents/ARCHITECTURE.md`.
- Capture and deterministic validation invoke no model. Model work begins only in T4V4-F, with one source/evidence/artifact tuple per context.
- Each subtask reads only its named input indexes and per-source files. It must not reconstruct the cohort from ambient directory order or from prior prose.

#### Raw X freeze contract

An accepted `indexes/x_raw_v4/<source_id>.json` is immutable and must contain:

```text
schema = x-raw-v4
ok = true
source_id
canonical_url
canonical_post_id
tool = x_thread_fetch
retrieved_at
raw_response
raw_response_sha256
validation_warnings
post-amendment: transport_form + transport_render_sha256 + transport_render_path
optional external article_url / article bytes-or-body / article metadata
```

1. Derive `canonical_post_id` from the normalized target URL and require exact equality with `raw_response.main_post.id`.
2. Require the observed first-class shape: `raw_response.tool == "x_thread_fetch"`, a mapping-valued `main_post`, and nonempty primary text. Reject a synopsis, placeholder, hand-authored reconstruction, or response whose canonical main post is absent. A deterministic parse from a hash-bound verbatim tool render is permitted under the transport contract below.
3. Compute `raw_response_sha256` exactly as SHA-256 over UTF-8 canonical JSON: `json.dumps(raw_response, sort_keys=True, ensure_ascii=False, separators=(",", ":"))`.
4. Exclusive-create the accepted raw file. An identical source ID + raw hash is an idempotent no-op. Remove the different-hash `--force` path: a different response is written under `indexes/x_raw_conflicts_v4/<source_id>/<raw_response_sha256>.json`, marks that source blocked for adjudication, and never replaces the accepted freeze.
5. Validate the canonical `main_post` text, not the longest text anywhere in the thread. A foreign reply cannot make an empty, truncated, or placeholder primary post pass.
6. Keep the complete canonical structured tool response in this sidecar even when it contains replies; after the amendment, retain the exact rendered transport in its separately hash-bound sidecar. Neither provenance representation is inserted wholesale into model-visible evidence.
7. When a meaning-essential linked article or PDF is fetched, retain immutable original bytes (or the exact reader payload when no binary transport exists), its SHA-256, extraction kind, and exact page/range bounds. Extraction output never substitutes for a missing original PDF when the binary was available.
8. `x_fetch_state_v4.json` is a rebuildable resume index, not authority. Recompute it from the frozen targets, accepted raws, verified public fallbacks, conflicts, profile results, and terminal attempt records; update it after every terminal source outcome without deleting prior evidence.

#### X-native Article and transport contract

Observed first-class behavior: `x_thread_fetch` can return the rendered body of an X-native Article directly in `raw_response.main_post.text`, rather than the short status preview exposed by public APIs. Accepted examples include `108d87a4b26b` (11,824 characters), `29d60ad36ead` (10,946), `2abb38a5d19b` (16,254), and `2f5bf37a8ca5` (10,266), each with a terminal body boundary in the frozen response. This is evidence about the observed tool surface, not a universal completeness assumption.

1. When `x_thread_fetch` resolves an X-native Article body into `main_post.text`, treat that body as canonical primary readable content. Do not write a separate `article_url`, refetch the same X-native body as linked material, or append a duplicate copy.
2. A public API title, preview, card, or approximately 42-character status stub is insufficient evidence and cannot become an accepted fallback capture. For an X-native Article, an allowed fallback is sufficient only if it independently exposes the full readable body.
3. `main_post.text` length alone never proves completeness. Require no explicit truncation/placeholder marker, a coherent terminal boundary, and exact `retrieval.missing` entries for announced-but-absent prompt/code/template blocks, uninspected essential media, or meaning-essential external links. `01ddb5858d00` remains partial despite 21,667 characters because named prompt bodies are absent.
4. Media or external documents referenced by the Article remain separate evidence surfaces. Missing meaning-essential assets keep coverage partial; their absence does not discard the captured Article body.
5. The transport boundary precedes parsing. When the harness exposes an agent-facing rendered response, exclusive-create its exact bytes at `indexes/x_tool_render_v4/<batch_id>/<source_id>.txt`, hash those bytes, then derive `indexes/x_tool_inbox_v4/<batch_id>/<source_id>.json` with `parse_x_thread_fetch_render_v4.py`. The accepted raw record binds both `transport_render_sha256` and the canonical structured `raw_response_sha256`. Never reconstruct an inbox object from a synopsis or memory.
6. The 20 already accepted rows predate the transport-sidecar requirement. Preserve them without refetch: the five smoke raws use `structured_raw_legacy`; the fifteen batch raws use `structured_inbox_legacy` and require parsed-object equality between inbox and accepted raw. Freeze those bindings in `indexes/x_transport_provenance_v4.json`. This bounded legacy status is retrieval provenance only; it cannot excuse a truncation, ID mismatch, or semantic defect.

`x_transport_provenance_v4.json` has `schema: x-transport-provenance-v4`, target-index SHA-256, accepted count, and source-ID-sorted rows. Every row binds `source_id`, `raw_response_sha256`, `transport_form` ∈ {`structured_raw_legacy`,`structured_inbox_legacy`,`rendered_text`}, and the accepted raw-file SHA-256. `structured_inbox_legacy` additionally binds inbox path/SHA-256 and requires `json.loads(inbox) == accepted_raw.raw_response`; `rendered_text` additionally binds render path/SHA-256, parser path/SHA-256, inbox path/SHA-256, and the same parsed-object equality. `structured_raw_legacy` is restricted to the five pre-batch smoke raws.
7. Before another fetch, make `verify_x_contract_v4.py --self-test` filesystem-isolated. Its overwrite-conflict fixture currently creates and deletes a real conflict sidecar, leaving `x_fetch_state_v4.json` with a stale `000c6356aae9` conflict. Run the fixture only under a temporary synthetic root and assert that real raw, conflict, capture, and state hashes are unchanged.

#### Stable semantic X projection

`phase2_capture_v4.build_x_payload_from_raw` must produce readable source content only:

1. Include the exact canonical primary-post text.
2. Include a thread continuation only when its stable author ID matches the primary author; if no stable ID is exposed, use case-insensitive exact username equality. If neither comparison is possible, include only the primary and add `self_thread_identity_unavailable` to `retrieval.missing` when thread items exist.
3. Exclude every third-party reply, quote, and its media from `payload_text`, `source_urls`, `allowed_urls`, and `media`. The raw sidecar retains them only as tool provenance.
4. Include a linked body only when the canonical post makes it meaning-essential and that exact body was frozen. Record `retrieval.linked_material_decision` as one of `included_meaning_essential`, `unfollowed_nonessential`, or `blocked_meaning_essential`; never include a link merely because old Atlas prose mentioned it. `blocked_meaning_essential` yields `partial` when the remaining payload still supports a bounded summary, otherwise `failed`/`blocked_fetch`.
5. Put only successfully fetched and inspected pinned media in the evidence `media` array; every such entry has `fetched: true` and `inspection_status` ∈ {`model_visible`, `nonessential_decorative`}. Exclude uninspected essential assets from `media`, record their exact URL/range under `retrieval.missing`, include only the URL in `allowed_urls` when needed for artifact linking, and require `coverage: partial`.
6. `payload_text` and the full readable-content hash must exclude `retrieved_at`, raw-response hashes, engagement counters, tool metadata, and full raw JSON. Keep those fields in retrieval metadata outside the semantic hash.
7. Metadata-only changes, engagement changes, and foreign-reply changes must leave the semantic payload and `effective_content_hash` unchanged. Primary text, included self-thread text, or included linked-body bytes changes must change the effective hash. Inspected-media changes must change the media/evidence hashes and invalidate any bound review; they change the effective content hash only when the inspected media projection is explicitly part of the hashed readable payload.
8. Long payloads follow the product projection contract: retain complete readable bytes separately; set explicit complete-content `content_hash`, `payload_projection: true`, and exact projection bounds. Never label a model-visible prefix as the complete readable payload.
9. Detect named-but-absent prompt/code/template bodies, not only a bare `Prompt:` line. Add the exact missing surface to `retrieval.missing` and keep coverage partial until the body is captured.
10. Old artifacts, living caveats, topic/relations state, sibling sources, plan text, and model memory are forbidden semantic inputs. They may be read only after capture for comparison/classification.

#### Resume, batch, and handoff contract

- `indexes/x_targets_v4.json` is source-ID sorted and hash-frozen. At T4V4-C opening, derive `targets_with_post_id - accepted_raw_ids`, stable-sort by `source_id`, and split exactly 142 IDs into 15 immutable batches of 10 except the final remainder. Inputs 0001–0015 now exist and must not be regenerated from the later 20/127 checkpoint.
- Batch inputs live at `indexes/x_raw_batches_v4/inputs/0001.json` … `0015.json`. Existing `x_batch_*.json` synopsis-era inputs are SUPERSEDED and must not be reused.
- Each input binds `schema`, `batch_id`, target-index SHA-256, ordered target rows, and count. Each completed result under `indexes/x_raw_batches_v4/results/<batch_id>.json` binds accepted raw hashes, post-amendment transport hashes, terminal no-write attempt hashes, capture/evidence hashes, remaining IDs, helper/verifier hashes, and zero-or-more blockers.
- `results/0001.json` is an immutable pre-amendment result and is not rewritten to add fields. The T4V4-C handoff binds its existing hash, the B-handoff materializer hash, and its ten rows’ provenance-index entries. Results 0002–0015 use the amended result contract.
- Process one source at a time: first-class fetch → exclusive transport freeze → deterministic parse → exclusive structured raw freeze → deterministic materialization → contract verifier. A rate limit or tool outage leaves the source pending; it is not a terminal `blocked_fetch`.
- After every batch, rebuild `x_fetch_state_v4.json`, run the X contract verifier, and update `indexes/T4V4_PROGRESS.md` with exact counts and the latest immutable result hash.
- On successful completion of each T4V4-A…G subtask, exclusive-create `indexes/handoffs/T4V4-<letter>.json` with: `schema`, `task`, `completed_at`, predecessor-handoff SHA-256 (`null` for A), frozen input URIs/hashes, output URIs/hashes, counts, named checks and results, `blockers: []`, and `next_task`. A blocked subtask remains unchecked and records its blocker in `T4V4_PROGRESS.md`; do not manufacture a successful handoff.
- Hash every file over exact bytes. When a handoff needs a directory digest, compute SHA-256 over UTF-8 `"<relative-posix-path>\t<file-sha256>\n"` rows sorted by relative path; empty directories are omitted.
- A fresh executor starts with this plan’s T4V4 section, `indexes/T4V4_PROGRESS.md`, the latest completed handoff, and only the next task’s frozen inputs. Prior chat/session history and superseded review prose are unnecessary and must not be imported.

#### T4V4-A. Repair and verify X helpers

Mutable targets for T4V4-A:

```text
helpers/x_raw_freeze_v4.py
helpers/phase2_capture_v4.py
helpers/write_x_capture_batch_v4.py
helpers/verify_x_contract_v4.py
indexes/x_fetch_state_v4.json
indexes/T4V4_PROGRESS.md
indexes/handoffs/T4V4-A.json
```

Read-only fixtures: `indexes/x_targets_v4.json`, the five accepted `indexes/x_raw_v4/*.json`, and their five current flawed `captures-v4/<source_id>/` directories.

1. Implement the raw and semantic contracts above; remove different-hash raw overwrite and successful-capture deletion during ordinary resume.
2. Make the accepted raw file and its hash the materialization input. A materializer-version correction may replace a derived capture only after the prior derived directory is preserved under a named SUPERSEDED root.
3. Add a deterministic verifier with `--self-test`, `--raw-only`, `--source-id <id>`, and `--all` modes. It exits nonzero on ID/hash mismatch, forbidden payload sections, foreign author/media inclusion, retrieval-dependent semantic hashes, evidence-file hash mismatch, or invalid coverage/media coupling.
4. Its in-memory invariance fixtures must prove:
   - changing only `retrieved_at`, engagement, or foreign replies leaves payload/effective hash unchanged;
   - changing primary text changes the effective hash;
   - a foreign reply cannot satisfy primary validation;
   - a different raw hash cannot overwrite an accepted freeze.
5. Syntax-check the helpers; run `x_raw_freeze_v4.py status`; run verifier `--self-test` and `--raw-only`; and confirm `--all` rejects all five known flawed X captures before T4V4-B. It may also inventory provisional non-X findings for T4V4-E; record the complete expected-negative result without modifying those rows. Write the T4V4-A handoff and do not resume the 142-source batch yet.

#### T4V4-B. Supersede and rematerialize five smoke captures

1. Preserve the five accepted raw freezes unchanged.
2. Move only the five flawed derived directories to `captures-v4-x-derived-SUPERSEDED/<source_id>/`; record each source/destination SHA-256 in the handoff. Do not delete them and do not disturb non-X `captures-v4` rows.
3. Rematerialize the five sources through the corrected helper and require:

| Source ID | Required observation |
|---|---|
| `000c6356aae9` | Exact primary post plus frozen full article; foreign replies absent; no placeholder; complete only if no meaning-essential surface remains missing |
| `01ddb5858d00` | Foreign `rizroze` reply/photo absent; named prompt bodies missing from tool text are explicit; coverage remains `partial` |
| `0cb74a2b44c5` | Empty prompt slots explicit in `missing`; coverage `partial` |
| `13a64a042505` | Demo video and unfetched CTA bounds explicit; coverage `partial` unless both are actually inspected |
| `cbe23bddd592` | Primary figure remains explicit missing media; PDF binary SHA/page bounds retained; no binary appears in `payload_text`; coverage `partial` |

4. For all five, recompute evidence and payload hashes from file bytes, run `atlas_quality.resolve_effective_content_hash`, require every evidence `media` item to pass the fetched/URL checks used by `validate-summary`, and run the X contract verifier.
5. Halt on any unexpected coverage upgrade, raw mutation, foreign content, semantic-hash instability, or `media.fetched != true`. Only a clean T4V4-B handoff authorizes T4V4-C.

#### T4V4-C. Capture remaining 142 X status URLs

T4V4-C preflight may mutate only the current temp helpers `verify_x_contract_v4.py`, `parse_x_thread_fetch_render_v4.py`, `process_x_batch_v4.py`, and `x_raw_freeze_v4.py`; `indexes/x_transport_provenance_v4.json`; the rebuildable state/progress files; post-amendment transport/inbox paths; the active batch result; and per-source raw/capture paths for IDs not already accepted. It must not rewrite A/B handoffs, accepted raw/capture bytes, or batch inputs.

1. Before another fetch, implement the Article/transport contract above and isolate the verifier self-test. Preserve the completed A/B handoffs as history; bind amended helper hashes in batch 0002 and the eventual T4V4-C handoff.
2. Rebuild `x_fetch_state_v4.json` once from authority after the isolation fix. Require 20 accepted raws, 127 pending statuses, no file under `x_raw_conflicts_v4/`, and `conflicts: []`; the stale self-test marker is not an authoritative conflict.
3. Freeze `x_transport_provenance_v4.json` for the existing 20 raws. Run `--self-test --raw-only --all`; require zero findings and byte-identical real state before/after the self-test.
4. Resume batch 0002 without refetching or rewriting its five accepted rows. Fetch only `1ada9d65ee1b`, `1ff02e7f5eb2`, `23b9a79a0128`, `25509e16f696`, and `28279f4d7e09`, then produce the immutable 10-row result.
5. For each pending source, call first-class `x_thread_fetch` for the exact canonical post ID. Freeze the transport before parsing, then exclusive-create the structured raw before semantic materialization. Never summarize, normalize, or compress the source text.
6. For an X-native Article, use `main_post.text` as the Article body. Mark it complete only when the Article checks above pass; otherwise retain the captured body with honest partial coverage. Do not substitute the public API preview or perform a redundant linked-Article fetch.
7. After one ordinary first-class retry, the only status fallback is a public unauthenticated browser/reader capture. Freeze its exact HTML/reader bytes and metadata under `indexes/x_fallback_v4/<source_id>.json`, label the surface `x_browser_public`, and never place it in `x_raw_v4` or label it `x_thread_fetch`. A preview/stub is insufficient. If neither surface exposes a sufficient canonical payload, write an immutable terminal attempt and classify `blocked_fetch`; do not invent text.
8. Materialize and verify each newly accepted first-class raw or sufficient public fallback independently. Existing accepted rows are verify-only during resume. No batch-wide context, old artifact read, or model call is permitted.
9. A batch completes only when every input ID has an accepted raw+capture, a verified public-fallback capture, or an exact terminal no-write attempt. Run the verifier and freeze the result record before opening the next batch.
10. T4V4-C completes when all 147 status targets are terminal and no authoritative raw conflict or pending retry remains. Success does not require every source to be fetchable; it requires every failure to be exact and non-invented.

#### T4V4-D. Resolve four X profile surfaces

Profile IDs are `0f073f561305`, `1f25e180d212`, `5292b65a42f8`, and `af4ac088e52f`.

1. Do not pass them to the status-only path and do not call `blocked_fetch:x_profile_no_status_id` terminal.
2. Try a profile-capable first-class connector, then a public unauthenticated browser/reader capture. Do not use credentials, an authenticated browser profile, or a non-dev connector without separate user approval.
3. If a sufficient readable canonical profile is captured, freeze it under `indexes/x_profile_v4/<source_id>.json` with an explicit profile surface, honest `complete|partial` coverage, and stable readable-content hash.
4. If allowed surfaces cannot expose sufficient content, record final `unsupported_surface` with attempted surfaces/errors and no rewrite path.
5. Freeze source-ID-sorted `indexes/x_profile_results_v4.json` and the T4V4-D handoff.

#### T4V4-E. Audit all 503 evidence outcomes and classify comparability

1. Enumerate only the 503 source IDs from `inventory/snapshot.json`; require exactly one v4 capture or terminal no-write record for each.
2. Re-audit every media-bearing row. Every evidence `media` entry must be fetched and inspected; missing essential media belongs only in `retrieval.missing` with `coverage: partial`. No `coverage: complete` row may have missing meaning-essential media, mutable external GitHub media, or unresolved range bounds.
3. Retain the verified non-X corrections: external GitHub media commit-pinned; `26035151aad9` PDF text with page bounds; `e3852e2611b` inspected model-visible media. Recheck their exact bytes rather than trusting the progress note.
4. Safe v3 non-media raw/HTML may remain copied only when its v4 record binds the predecessor hashes and the current verifier finds none of the v3 defect classes.
5. Classify in this order: identity → capture sufficiency → coverage regression → hash/procedure comparability → effective readable-content hash → same-hash-review eligibility.
6. `source_changed` requires comparable semantic scope/procedure and genuinely different readable content. A raw-response hash, timestamp, engagement counter, extractor formatting change, or foreign-reply change is never proof of source change.
7. Use `hash_baseline_incomparable` when usable evidence is not weaker than living evidence but historical content-hash provenance/projection cannot be compared. Use `blocked_evidence_regression` when the new surface is strictly weaker or drops a previously represented meaning-essential surface.
8. Re-read current manifest row and artifact hashes only for concurrency classification. Do not silently repartition the frozen cohort; changed/deleted rows become `concurrent_drift`.
9. Write source-ID-sorted `indexes/phase2_classify_v4.json` and `indexes/phase2_summary_v4.json`, both binding the snapshot, helper/verifier, capture, and current living hashes.
10. Every classification row contains: source identity/path/route fields; frozen and current manifest-row/artifact hashes; living content hash/coverage; capture/evidence hashes; captured effective hash/coverage/surface/missing/media state; comparability boolean/reason; disposition; model-review required/completed flags; optional bucket/proposed path. The top-level record binds its schema, snapshot SHA-256, helper/verifier hashes, ordered row count, and disposition counts.

#### T4V4-F. Run hash-bound same-hash reviews and finalize dispositions

1. Queue only rows whose stable effective hash equals the living content hash and whose evidence is sufficient for review.
2. Each model invocation receives exactly one source-only evidence envelope and the one living artifact as a separately delimited untrusted artifact. No sibling, topic, campaign, or prior review context.
3. Produce the exact seven checklist IDs in this order: `evidence-boundary`, `primary-contribution`, `source-support`, `limits-uncertainty`, `context-neutrality`, `assessment-coherence`, `proportionality`.
4. Run `validate-summary(artifact_text, evidence_bundle, checklist)`. This is review-only: do not revise or write the living artifact in T4V4.
5. Freeze each review under `reviews-v4/` with artifact, evidence-bundle, effective-content, checklist, model/harness metadata, and review-record hashes. Existing v1–v3 reviews never authorize a v4 result.
6. Same-hash all-pass becomes `pass_current`; a deterministic or semantic failure becomes `quality_fail` with proposed path `same-hash`. An artifact that cannot be parsed enough to review becomes `unreviewable_artifact`, not an inferred quality failure.
7. Rebuild the classification and summary indexes after all reviews. Require exactly 503 classified rows and no “pending review” state.

#### T4V4-G. Freeze completion handoff

1. Run the full v4 contract verifier over targets, raws, captures, media, PDFs, reviews, classification, and current concurrency hashes.
2. Require zero unexplained partial→complete upgrades, binary-in-text payloads, mutable essential media, evidence media lacking successful inspection, raw conflicts, pending targets, or review-hash mismatches.
3. Record counts for every disposition, semantic-review count, no-model count, blocked/unsupported count, and the exact 503-ID union hash computed as SHA-256 of `"\n".join(sorted(source_ids)) + "\n"`. Report `full_library_classified: true`; never report `full_library_reviewed: true`.
4. Freeze `indexes/handoffs/T4V4-G.json`, update `T4V4_PROGRESS.md`, and check T4V4 plus T4V4-A…G only after every handoff is present and hash-valid.
5. Halt. T4.5 is a separate task and approval gate.

### T4V5. Completion-integrity recovery — mechanically executed, superseded

T4V5 is read-only with respect to living state. It may update this plan and create only the v5 paths named below under `vault://atlas/tmp/source-quality-revisit-2026-07-21/`. Every T4V4 file is an immutable input. T4V5 completion alone authorizes neither T4.5 nor T5.

Post-completion audit rejected T4V5-F as approval authority. This section remains the historical execution contract and may not be re-executed, edited into compliance, or used to open T4.5. T4V6 and T4V7 were its mechanically executed successors and are both rejected; no current approval authority exists pending a plan-amended successor.

#### Fixed implementation and serialization contract

1. Create one new helper, `helpers/t4v5.py`; no other helper may write a v5 path. It must require `--root <connector-resolved-temp-root>`, reject a root outside the logical temp root, and expose only:

   ```text
   self-test
   preflight
   ingest-x-render --batch-id ID --source-id SID --render-file FILE
   materialize-x --source-id SID
   repair-evidence
   build-authority
   classify [--reviews-complete]
   ingest-review --source-id SID --input FILE --raw-output FILE --checklist FILE
   verify --scope preflight|x|evidence|classification|reviews|all
   ```

   Run it from the Atlas app working directory as `python3 <root>/helpers/t4v5.py --root <root> <subcommand>`. It may import only product modules `scripts/atlas_quality.py` and `scripts/atlas_url.py`; it must not import or execute any `helpers/*v4.py`. V4 helpers are read-only defect evidence.
2. The only new non-helper write roots are `indexes/x_tool_render_v5/`, `indexes/x_raw_v5/`, `indexes/x_raw_conflicts_v5/`, `indexes/x_raw_batches_v5/`, `captures-v5-overrides/`, `reviews-v5/`, and the exact v5 index/handoff files named in A–F. Any attempted write elsewhere is a STOP.
3. Canonical object hash is SHA-256 of UTF-8 `json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))` with no trailing newline. JSON record files use `json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"` and bind their actual file SHA-256 separately. Directory digest is SHA-256 of UTF-8 lines `relative_posix_path + "\0" + file_sha256 + "\n"`, sorted by relative path.
4. A semantic projection is source content only. Its `payload_text` is `json.dumps(projection, sort_keys=True, ensure_ascii=False, indent=2)` with no trailing newline; `content_hash` is SHA-256 of those exact UTF-8 bytes and `payload_projection` is `false`. No retrieval timestamp, engagement, raw/transport hash, wrapper text, cache URL, or old living prose enters the projection.
5. Final evidence `media` rows have exactly `url`, `fetched`, `local_path`, `sha256`, `bytes`, `content_type`, `bound`, `media_role`, `inspection_status`, and `inspection_notes`. `fetched` is `true`; `inspection_status` is `model_visible|nonessential_decorative`. Avatar/icon/badge/chrome media may be decorative only when the source metadata identifies that role; every other decodable fetched asset is `model_visible`. Unfetched, undecodable, or unclassified assets are absent from `media`, present in `retrieval.missing`, and force `coverage: partial`.
6. Every A–F handoff has exactly: `schema: t4v5-handoff-v1`, `task`, `completed_at`, `predecessor_handoff_sha256`, `input_hashes`, `output_hashes`, `counts`, `completed_ids_sha256`, `terminal_no_write_ids_sha256`, `checks`, `blockers`, and `next_task`. Completion requires `blockers: []`; A binds T4V4-G as predecessor and B–F bind the immediately preceding v5 handoff.

#### T4V5-A. Helper, defects, and action plan

1. Implement `t4v5.py` first. `self-test` must use a newly created operating-system temporary directory and prove: exclusive-create/idempotent same-hash/different-hash conflict behavior; canonical-ID rejection; foreign-reply exclusion; retrieval/engagement/foreign-reply hash invariance; same-author and primary-text hash sensitivity; exact Article text retention; fxt/reverse-render input rejection; coverage state transitions; media-state normalization; frontmatter coverage parsing; the classification table below; and byte-identical real v4/v5 roots before/after the test.
2. `preflight` reads only the frozen inventory and named T4V4 inputs. Exclusive-create `indexes/T4V5_DEFECTS.json` with per-source defect codes from this closed enum: `X_FXT_MISLABELED`, `X_ARTICLE_PROJECTION_UNPROVEN`, `RAW_POST_CREATE_MUTATION`, `PROFILE_EVIDENCE_SCHEMA_INVALID`, `EVIDENCE_MEDIA_STATE_INVALID`, `LIVING_COVERAGE_UNPARSED`, `COMPARABILITY_ASSUMED`, `HANDOFF_ASSERTION_CONTRADICTED`.
3. Require the observed code counts before proceeding: 122 fxt-mislabeled rows; 78 Article-projection rows; 122 post-create raw mutations; 4 profile-schema rows; 101 invalid-media rows; 259 unparsed-coverage rows; 224 assumed-comparability rows. A changed count is a blocker, not an invitation to adjust the plan.
4. Exclusive-create source-ID-sorted `indexes/capture-authority-v5-plan.json` with all 503 IDs. Each row binds the snapshot row and contains a sorted `actions` array from `verify_v4`, `refetch_x_first_class`, `repair_profile`, `repair_media`, `terminal_no_write`. Require exactly 122 `refetch_x_first_class` rows and exactly the four known profile IDs as `repair_profile`. In the same `preflight` invocation, exclusive-create `indexes/x_targets_v5.json` from those 122 rows and require the diagnostic split 78 Article-bearing/44 ordinary-status.
5. Run `verify --scope preflight`; freeze `indexes/handoffs/T4V5-A.json` with helper hash, defect/action-plan hashes, exact counts, and `next_task: T4V5-B`. Do not create a final capture-authority file in A.

#### T4V5-B. Truthful X replacement capture

1. Read the exact 122 rows from the A-bound `indexes/x_targets_v5.json`. Public-fxt snapshots may have established its 78/44 diagnostic split during A only; they are never semantic input or fallback evidence.
2. Freeze `indexes/x_raw_batches_v5/plan.json` before fetching with the exact 13 partitions: batch `0001` is the fixed smoke IDs `37a76cea0926`, `3907d2af9c57`, `3a7652f38c0e`, `37d41c4042ee`, `38923fdf644e`; remove those five from the sorted target list; batches `0002`–`0012` receive the next 10 IDs each; `0013` receives the final 7. Exclusive-create only input `0001` initially, binding the A handoff SHA-256. After each result freezes, create the next input from the frozen plan partition and bind the preceding result SHA-256.
3. For each ID, call first-class `x_thread_fetch` for the exact canonical post ID. Before parsing or creating structured data, exclusive-create the exact agent-facing result bytes at `indexes/x_tool_render_v5/<batch_id>/<source_id>.txt`. Do not create this file from JSON, fxt data, a template, `stage_and_freeze_render_v4.py`, or any reverse renderer.
4. Run `ingest-x-render`, then `materialize-x`. The raw record is exclusive-created at `indexes/x_raw_v5/<source_id>.json` with exactly: `schema: x-raw-v5`, `ok`, `source_id`, `canonical_url`, `canonical_post_id`, `tool: x_thread_fetch`, `retrieved_at`, `transport_path`, `transport_sha256`, `parser_sha256`, `raw_response`, `raw_response_sha256`, and `validation_warnings`. Require `raw_response.main_post.id == canonical_post_id`, nonempty primary text, canonical raw-response hash, and no public-fxt wrapper fields. Different bytes go only to `x_raw_conflicts_v5/` and block that ID.
5. The X semantic projection has exactly:

   ```json
   {
     "surface": "x_thread_fetch",
     "primary_post": {"id": "...", "username": "...", "text": "..."},
     "same_author_continuation": [
       {"id": "...", "username": "...", "text": "..."}
     ],
     "linked_material": []
   }
   ```

   Preserve parsed text without post-parse trimming or whitespace normalization, and preserve same-author continuation in raw tool order. Include a thread item only when its username casefold equals the primary username casefold; otherwise exclude it. `linked_material` contains only separately frozen readable bodies, never ordinary unfollowed hyperlinks or duplicate X-native Article text.
6. For an X-native Article, `raw_response.main_post.text` is the primary body and appears once. Structured Article blocks, when present, are provenance sidecars only; do not flatten, render, compare, or substitute them. Their declared media/attachments still participate in missing/media checks. Title/card/preview/stub text is never sufficient.
7. Coverage is mechanical: `failed` when canonical ID or primary text is unavailable; `partial` when `retrieval.missing` is nonempty, the tool reports truncation/warning, same-author identity is unresolved, or a tool-declared attachment/media/Article body is absent; otherwise `complete`. Ordinary hyperlinks do not downgrade coverage unless the canonical payload declares them as an attached Article/document required to render the post.
8. Run `verify --scope x` after every source and freeze one immutable batch result only when all its IDs are accepted first-class captures or exact terminal no-write outcomes. Retry one source-local first-class failure once; a second source-local deleted/private/not-found failure is terminal `blocked_fetch`. Rate limit, global connector outage, or unavailable `x_thread_fetch` is a task blocker with that ID still pending, never 122 inferred `blocked_fetch` rows. T4V5 permits no status fallback surface. Never reopen successful IDs or a completed batch.
9. Batch `0001` must pass before `0002`. No batch opens before its predecessor result hash exists. T4V5-B completes only after all 13 results exist, all 122 IDs are terminal, conflicts/pending are empty, `verify --scope x` is clean, and `indexes/handoffs/T4V5-B.json` is frozen.

#### T4V5-C. Evidence repair and final capture authority

1. `repair-evidence` processes only IDs/actions from `capture-authority-v5-plan.json`; it may not discover work by directory scan. Rebuild the four profile overrides from their frozen public-fxt user snapshots after exact canonical-handle matching.
2. Profile projection has exactly `surface`, `user_id`, `handle`, `display_name`, `bio`, `location`, `website`, `joined`, and `protected`. Missing optional fields are JSON `null`. Counts, avatar/banner URLs, retrieval metadata, and raw hashes remain provenance. Coverage is complete only for this explicitly bounded profile-metadata scope; it never claims timeline coverage.
3. For `repair_media`, promote a nested inspection only when its retained local bytes match its recorded SHA-256/byte count and its status is one of the two allowed final statuses. Otherwise remove the row from semantic media, add `media_uninspected_essential:<url>` to `retrieval.missing`, and force partial coverage. Preserve original bytes in place; never move or rewrite v4 sidecars.
4. Recompute every override from selected bytes. Revalidate all 25 non-fxt status rows as `verify_v4`, explicitly including the five original X smoke rows; v4 reuse fails if identity, raw/evidence/effective hashes, source-only projection, source-specific missing bounds, media state, or coverage is invalid.
5. `build-authority` exclusive-creates `indexes/capture-authority-v5.json` with exactly 503 sorted rows. A row has exactly `source_id`, `selection: v4_reuse|v5_override|terminal_no_write`, `capture_path`, `capture_sha256`, `evidence_path`, `evidence_sha256`, `effective_content_hash`, `coverage`, `surface`, `surface_contract_id`, `surface_contract_complete`, `raw_or_terminal_path`, `raw_or_terminal_sha256`, `terminal_disposition`, `lineage_input_sha256`, `historical_hash_proof`, and `validation_codes`. Capture/evidence fields are null only for terminal no-write; `terminal_disposition` is non-null only for terminal no-write; absent historical proof is JSON `null`.
6. Run `verify --scope evidence`; require one selection per inventory ID, no extra ID, valid final media schema, no binary in `payload_text`, no unexplained coverage upgrade, and exact retained PDF/media hashes including the named `cbe23bddd592`, `26035151aad9`, and `e385c2e2611b` bounds. Freeze `indexes/handoffs/T4V5-C.json`.

#### T4V5-D. Fixed classification table

1. `classify` reads only inventory, final capture authority, current manifest/artifact bytes, and review authority when `--reviews-complete` is supplied. Parse every artifact with `scripts.atlas_quality._parse_frontmatter`; zero missing/invalid living coverage is required.
2. Apply this first-match table—no other branch or reason is allowed:

   | Condition | Disposition |
   |---|---|
   | Current manifest-row or artifact hash differs from the frozen inventory | `concurrent_drift` |
   | Authority selection is terminal no-write | its exact terminal disposition |
   | Selected capture/evidence fails v5 validation | `blocked_evidence_regression` |
   | Captured coverage ranks below living coverage | `blocked_evidence_regression` |
   | Effective hash equals living content hash | `needs_same_hash_review` before E |
   | Hash differs; capture is complete; and `historical_hash_proof` below validates | `source_changed` |
   | Hash differs; capture is complete; no missing bounds; surface contract validates; historical proof absent/incomparable | `hash_baseline_incomparable` |
   | Any remaining different-hash case | `blocked_evidence_regression` |

3. `historical_hash_proof` validates only when an authority row binds an immutable historical evidence path/file SHA-256, its effective hash equals the living content hash, and its projection schema/scope identifier exactly equals the selected capture’s. Hostname, procedure name, artifact prose, or hash difference alone is never proof. Therefore `source_changed` is expected to be zero unless such bytes are actually present.
4. Exclusive-create pre-review `indexes/phase2_classify_v5-pre-review.json` and `indexes/phase2_summary_v5-pre-review.json`. Each classification row has exactly: `source_id`, `source_seq`, `canonical_url`, `artifact`, `route_status`, `frozen_manifest_row_sha256`, `frozen_artifact_sha256`, `current_manifest_row_sha256`, `current_artifact_sha256`, `living_content_hash`, `living_coverage`, `authority_row_sha256`, `authority_selection`, `evidence_bundle_sha256`, `effective_content_hash`, `captured_coverage`, `surface`, `missing`, `media_state`, `historical_hash_proof`, `comparable`, `comparability_reason`, `decision_rule`, `disposition`, `bucket`, `proposed_path`, `model_review_required`, `model_review_completed`, `review_authority_row_sha256`, and `error`. `decision_rule` is exactly `concurrent_drift|terminal_no_write|capture_invalid|coverage_regression|same_hash|historical_hash_proven|complete_baseline_incomparable|different_hash_ineligible`. Classification top level has exactly `schema`, `classified_at`, `snapshot_sha256`, `capture_authority_sha256`, `helper_sha256`, `current_cohort_sha256`, `ordered_row_count`, `source_id_union_sha256`, `by_disposition`, `rows`, and `findings`. Summary has exactly `schema`, `summarized_at`, `classification_sha256`, `snapshot_sha256`, `capture_authority_sha256`, `total`, `by_disposition`, `rewrite_counts`, `review_counts`, and `blockers`. Require 503 rows, recomputed counts, no unknown field/disposition/rule, no `assumed`, and no pending state except `needs_same_hash_review`.
5. Run `verify --scope classification`; freeze `indexes/handoffs/T4V5-D.json` bound to the pre-review files.

#### T4V5-E. Source-isolated same-hash review

1. Queue exactly the `needs_same_hash_review` rows. No v4 review is reusable: the current v4 records lack separately frozen source-isolated model inputs and raw model outputs. Do not search for or infer alternate provenance.
2. For each queued ID, exclusive-create `reviews-v5/<source_id>/input.json` with exactly `schema: review-input-v5`, `source_id`, `artifact_path`, `artifact_sha256`, `evidence_path`, `evidence_sha256`, `effective_content_hash`, and the ordered `checklist_ids`. Invoke the active model with exactly that one evidence envelope and separately delimited untrusted artifact; freeze the verbatim response as `raw-output.txt`.
3. Parse exactly seven checklist items in the fixed order into `checklist.json`. Every pass evidence string must contain at least one concrete `source:<payload locator>` or `artifact:<section/line locator>`; generic evidence such as “pass,” “none,” “no issue,” or “no independent failure” is invalid. A fail uses a source/artifact locator plus the failure reason.
4. Run `validate-summary(artifact, evidence, checklist)`. This task is review-only: no revision. `ingest-review` refuses an input/output/checklist hash mismatch and exclusive-creates `review.json` with exactly `schema`, `source_id`, `artifact_sha256`, `evidence_sha256`, `effective_content_hash`, `input_sha256`, `raw_output_sha256`, `checklist_sha256`, `model`, `harness`, `validate_summary_findings`, and `review_outcome`. The review file’s own SHA-256 exists only in review authority, never as a self-hash.
5. After every review is ingested, exclusive-create source-ID-sorted `indexes/review-authority-v5.json`; each row has exactly `source_id`, `input_path`, `input_sha256`, `raw_output_path`, `raw_output_sha256`, `checklist_path`, `checklist_sha256`, `review_path`, and `review_sha256`. Then run `classify --reviews-complete` to exclusive-create final `indexes/phase2_classify_v5.json` and `indexes/phase2_summary_v5.json`: all-pass becomes `pass_current`; deterministic or semantic failure becomes `quality_fail`/`same-hash`; parse failure becomes `unreviewable_artifact`. Require zero `needs_same_hash_review`, run `verify --scope reviews`, and freeze `indexes/handoffs/T4V5-E.json`.

#### T4V5-F. Claimed complete verifier and handoff — rejected

1. Run `verify --scope all`. It recomputes from frozen bytes: all 503 authority selections; transport/raw identity and canonical hashes; conflict/pending state; semantic invariance; Article/profile/media/coverage contracts; current concurrency; the fixed classification rule for every row; review input/output/checklist/record hashes; counts; and the 503-ID union hash.
2. Require zero findings, zero duplicate/missing/extra IDs, zero authoritative conflicts/pending reviews, zero unproven `source_changed`, and no `indexes/rewrite-manifest-v4.json`. Compute the selected capture/evidence directory digest by the fixed serialization contract.
3. `indexes/T4V5_PROGRESS.md` and `indexes/handoffs/T4V5-F.json` were frozen, but their completion assertion is superseded: the F handoff has empty `output_hashes`, no selected capture/evidence digest, and does not prove that one helper produced every final artifact.
4. T4V5 and A–F remain checked as mechanically executed negative evidence only. They do not authorize T4.5 or any living write.

#### Historical dispositions emitted by T4V5

| Disposition | Exact meaning | Rewrite path |
|---|---|---|
| `pass_current` | Comparable same hash; checklist and deterministic validator pass | none |
| `quality_fail` | Comparable same hash; semantic or deterministic artifact failure | `same-hash` |
| `source_changed` | Comparable procedure/scope; readable source content genuinely changed | `changed-hash` |
| `hash_baseline_incomparable` | Usable, non-weaker evidence; historical hash/projection cannot be compared | `changed-hash` with bucket `hash_baseline_migration` |
| `blocked_fetch` | Allowed status/source fetch paths exhausted with no sufficient payload | none |
| `unsupported_surface` | Canonical surface has no supported unauthenticated capture path | none |
| `blocked_evidence_regression` | New evidence is weaker/narrower than living represented coverage | none |
| `identity_conflict` | Normalized URL/source ID/post ID disagree | none |
| `unreviewable_artifact` | Living artifact cannot be parsed sufficiently for a valid review | none |
| `concurrent_drift` | Frozen manifest/artifact identity hashes no longer match current living state | none |

Product mutation paths remain **only** `same-hash` and `changed-hash`. These historical T4V5 dispositions do not create a third reducer path and are not a rewrite queue. `stale_content` is forbidden.

### T4V6. Strict frozen-byte recovery — mechanically executed, superseded

T4V6 is a bounded integrity successor, not another source-acquisition campaign. It performs **no network/tool retrieval, no source generation, no routing, and no living write**. It reads the frozen inventory, living manifest/artifact bytes for concurrency only, and immutable T4V5 outputs. It never modifies, deletes, or silently repairs T4V4/T4V5 bytes. A defective selected capture becomes a source-specific v6 terminal no-write result; missing content remains missing.

Post-completion audit rejects T4V6-E as approval authority. `verify_all`/`verify_final` prove only that candidate/final `output_hashes` are nonempty, not that their key sets and values equal current files; they check A–D presence without recomputing the complete predecessor/input/output graph. The review verifier checks six outcomes and aggregate counts but not every review-authority binding or every nonreview final transition. The selected-files verifier recomputes listed hashes/digest but not exact closure against every authority/media/terminal/validation reference. The verifier self-test uses generic hash-sensitivity assertions instead of executing the production verifier against one-field mutations. A read-only in-memory-overlay reproduction changed both candidate and final authority-output hashes to impossible values and still returned `findings: []`. Preserve all bytes; do not patch or promote them.

#### Closed implementation, paths, and serialization

1. Create exactly two helpers under the temp root:
   - `helpers/t4v6.py`: the sole writer for every v6 data artifact after helper creation;
   - `helpers/t4v6_verify.py`: independent and read-only; it must not import `t4v6.py` or any v4/v5 helper, must open the temp root read-only, and emits one JSON object to stdout.
2. Both helpers may import only product modules `scripts.atlas_quality`, `scripts.atlas_url`, and `scripts.atlas_state`. They must not execute another helper, shell command, network client, model client, or connector mutation. `t4v6_verify.py` must not call writer functions or trust stored `checks`, `validation_codes`, dispositions, counts, or hashes without recomputation.
3. `helpers/t4v6.py` exposes only:

   ```text
   self-test
   preflight
   build-authority
   classify
   finalize-reviews
   freeze-candidate
   attest --verification-file FILE
   freeze-handoff --task A|B|C|D --verification-file FILE
   ```

   `helpers/t4v6_verify.py` exposes only:

   ```text
   self-test
   verify --scope preflight|evidence|classification|reviews|all|final
   ```

   Any extra command, command alias, implicit mode, or write from the verifier is a blocker. T4V6 performs no model invocation and creates no new review input/output bytes.
4. Apart from the two helper files, the only new v6 paths are:
   - `indexes/T4V6_CONTRACT.json`, `T4V6_DEFECTS.json`, `capture-authority-v6-plan.json`, `capture-authority-v6.json`, `selected-files-v6.json`;
   - `indexes/terminal-outcomes-v6/<source_id>.json`, `indexes/validation-reports-v6/<source_id>.json`;
   - `indexes/phase2_classify_v6-pre-review.json`, `phase2_summary_v6-pre-review.json`, `review-plan-v6.json`, `review-authority-v6.json`, `phase2_classify_v6.json`, `phase2_summary_v6.json`;
   - `indexes/verifications-v6/T4V6-A.json` through `T4V6-D.json`, `indexes/T4V6_PROGRESS.md`, `T4V6_VERIFICATION.json`;
   - `indexes/handoffs/T4V6-A.json` through `T4V6-D.json`, `T4V6-E-candidate.json`, and `T4V6-E.json`.

   Any other v6 path or any write to a predecessor path is a STOP.
5. Canonical object hash remains SHA-256 of UTF-8 `json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))` with no trailing newline. JSON files are `json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"`. File hashes bind actual bytes. A selected-files digest is SHA-256 of UTF-8 lines `logical_path + "\0" + file_sha256 + "\n"`, sorted by logical path; it is computed only from `selected-files-v6.json`, never an ambient directory scan.
6. `source_id_union_sha256` is SHA-256 of UTF-8 `"\n".join(sorted(source_ids)) + "\n"`. Every v6 row list is source-ID sorted and has exactly 503 unique IDs unless it is the exact six-ID review plan.
7. `indexes/T4V6_CONTRACT.json` has exactly `schema: t4v6-contract-v1`, `plan_path`, `source_plan_sha256`, `predecessor_f_path`, `predecessor_f_sha256`, `inventory_path`, `inventory_sha256`, `writer_path`, `writer_sha256`, `verifier_path`, `verifier_sha256`, `allowed_v6_paths`, `known_invalid_source_ids`, `expected_authority_counts`, `expected_pre_review_counts`, `expected_review_queue_ids`, `serialization`, and `classification_rules`. A–E bind this immutable contract hash. Later plan checkbox annotations do not change the frozen execution contract.
8. A–D handoffs have exactly `schema: t4v6-handoff-v1`, `task`, `completed_at`, `predecessor_handoff_sha256`, `contract_sha256`, `writer_sha256`, `verifier_sha256`, `verification_report_path`, `verification_report_sha256`, `input_hashes`, `output_hashes`, `counts`, `completed_ids_sha256`, `terminal_no_write_ids_sha256`, `checks`, `blockers`, and `next_task`. A binds the rejected T4V5-F bytes as historical predecessor; B–D chain to the preceding v6 handoff. Empty `output_hashes`, stored-boolean-only checks, and omitted digests are invalid. After each A–D producer command, capture the independent verifier stdout in an OS temporary file and call `freeze-handoff`; that command validates and exclusive-copies the report to `indexes/verifications-v6/T4V6-<TASK>.json` before creating the handoff.
9. Every verifier stdout object has exactly `schema: t4v6-verification-v1`, `scope`, `verified_at`, `contract_sha256`, `writer_sha256`, `verifier_sha256`, `target_path`, `target_sha256`, `selected_files_sha256`, `selected_files_digest`, `source_id_union_sha256`, `counts`, `checks`, and `findings`. Fields not applicable to a stage are explicit JSON `null`, never omitted. `freeze-handoff` accepts only the exact scope for its task (`preflight`, `evidence`, `classification`, `reviews`), exit-success output with `findings: []`, matching helper/contract/output hashes, and every required check `true`.

#### T4V6-A. Contract, isolated tests, and independent defect inventory

1. Freeze helper bytes first, then run both `self-test` commands in separate newly-created OS temporary directories. Hash the real predecessor/v6 roots before and after; require byte identity except for the two just-created helper files. Tests must prove:
   - exclusive-create, same-byte idempotence, and different-byte rejection;
   - exact command surfaces and write allowlist;
   - canonical object/file/selected-files hashing;
   - evidence effective-hash resolution through `atlas_quality.resolve_effective_content_hash`;
   - rejection of stale authority effective hashes;
   - rejection of `payload_projection: true` without separately retained complete readable bytes matching explicit `content_hash` and exact bounds;
   - rejection of missing/mismatched capture, evidence, payload, complete-content, raw, media, and terminal bytes;
   - coverage downgrade and incomplete surface-contract rejection;
   - manifest-row/artifact concurrency drift;
   - fixed first-match classification recomputation;
   - review hash, checklist locator/order, `validate_summary`, and outcome recomputation;
   - pending/conflict, handoff-chain, empty-output-hash, missing-selected-digest, and pre-existing rewrite-manifest rejection;
   - verifier read-only behavior and one-bit mutation tests for each protected field.
2. `preflight` reads the frozen 503-row inventory; T4V5-F; T4V5 helper, authority, classification, summary, review authority, reviews, handoffs, progress, selected capture/evidence/payload/raw/media bytes; and current living manifest/artifact bytes. It must not reuse any v5 verifier result or import v5 logic.
3. Independently recompute and require these known source defects:
   - `AUTHORITY_EFFECTIVE_HASH_MISMATCH` for exactly `415cb2575966`, `88ce6b23737c`, `a1b588fd2c4e`, and `afac539bd2a8`: `resolve_effective_content_hash(evidence)` differs from the v5 authority/capture effective hash;
   - `UNBACKED_PAYLOAD_PROJECTION` for exactly `8b4da8b50a8d`: `payload_projection: true` and `projection_bounds: chars 0-120000 of 2862691`, but no separately retained complete readable-content bytes recompute to the explicit complete-content hash;
   - `REWRITE_ELIGIBLE_INVALID_CAPTURE` for exactly `8b4da8b50a8d`;
   - `CARRIED_FORWARD_V5_TERMINAL` for exactly `02452225dfa3`, `4a05fe207626`, `67710e994bff`, `915a177852f9`, `9540725d387f`, `a907fe9cab7d`, `afac21e55023`, `c796355b5344`, `e8a778988ec0`, `f6f7ca6ca48a`, `fb63de03ff34`;
   - global defects `V5_HELPER_COMMAND_SURFACE_DRIFT`, `V5_FINAL_WRITER_UNPROVEN`, `V5_FINAL_OUTPUT_HASHES_EMPTY`, `V5_SELECTED_DIGEST_ABSENT`, and `V5_VERIFY_ALL_INCOMPLETE`.
4. Use only this closed source-defect/state enum: `CARRIED_FORWARD_V5_TERMINAL`, `AUTHORITY_ROW_SCHEMA_INVALID`, `CAPTURE_FILE_MISSING`, `CAPTURE_SHA_MISMATCH`, `EVIDENCE_FILE_MISSING`, `EVIDENCE_SHA_MISMATCH`, `PAYLOAD_FILE_MISSING`, `PAYLOAD_SHA_MISMATCH`, `AUTHORITY_EFFECTIVE_HASH_MISMATCH`, `PAYLOAD_DECLARATION_INVALID`, `UNBACKED_PAYLOAD_PROJECTION`, `RAW_BINDING_INVALID`, `MEDIA_BINDING_INVALID`, `COVERAGE_CONTRACT_INVALID`, `SURFACE_CONTRACT_INVALID`, `CONCURRENCY_DRIFT`, `CLASSIFICATION_MISMATCH`, `REVIEW_BINDING_INVALID`, `REWRITE_ELIGIBLE_INVALID_CAPTURE`. Unknown codes are forbidden.
5. Exclusive-create `indexes/T4V6_DEFECTS.json` with exactly `schema: t4v6-defects-v1`, `generated_at`, `contract_sha256`, `predecessor_authority_sha256`, `global_defects`, `counts`, `rows`, and `findings`. Each source row has exactly `source_id`, `predecessor_authority_row_sha256`, `defect_codes`, `observed`, and `expected`. Exclusive-create `capture-authority-v6-plan.json` with exactly `schema: capture-authority-v6-plan`, `generated_at`, `contract_sha256`, `predecessor_authority_sha256`, `count`, and `rows`; each row has exactly `source_id`, `action: strict_v5_capture_reuse|v6_terminal`, `predecessor_authority_row_sha256`, `defect_codes`, `terminal_disposition`, and `reason_code`. Require:
   - 487 `strict_v5_capture_reuse`;
   - 11 `v6_terminal` carrying forward exactly `02452225dfa3`, `4a05fe207626`, `67710e994bff`, `915a177852f9`, `9540725d387f`, `a907fe9cab7d`, `afac21e55023`, `c796355b5344`, `e8a778988ec0`, `f6f7ca6ca48a`, `fb63de03ff34`;
   - 5 `v6_terminal` for exactly `415cb2575966`, `88ce6b23737c`, `8b4da8b50a8d`, `a1b588fd2c4e`, `afac539bd2a8`;
   - no capture repair, refetch, or inferred replacement.

   Any additional source defect, changed known-ID set, count drift, current concurrency drift, or inability to reproduce a global defect creates a nonempty A blocker and halts before B. Do not silently widen the terminal set.
6. Run `t4v6_verify.py verify --scope preflight`, capturing stdout byte-for-byte in a new OS temporary file. Require exit 0, `findings: []`, the exact known defect sets, and exact helper/contract/plan hashes. Call `t4v6.py freeze-handoff --task A --verification-file <file>`; it exclusive-copies the report to `indexes/verifications-v6/T4V6-A.json` and creates `indexes/handoffs/T4V6-A.json` with nonempty output hashes and `next_task: T4V6-B`.

#### T4V6-B. Strict 503-row capture authority

1. `build-authority` reads only `capture-authority-v6-plan.json` and its explicitly named predecessor rows/files. It must not discover replacement captures, select by mtime/directory order, or write capture/evidence bytes.
2. Exclusive-create one terminal record for each of the exact 16 terminal IDs at `indexes/terminal-outcomes-v6/<source_id>.json`, with exactly `schema: t4v6-terminal-v1`, `source_id`, `predecessor_authority_row_sha256`, `disposition`, `reason_code`, `defect_codes`, and `created_at`.
   - The 11 carried-forward IDs retain their exact v5 terminal disposition and use `reason_code: carried_forward_v5_terminal`.
   - The five invalid-capture IDs use `disposition: blocked_evidence_regression` and `reason_code: selected_capture_failed_strict_validation`.
3. Before authority creation, exclusive-create `indexes/validation-reports-v6/<source_id>.json` for all 503 IDs with exactly `schema: t4v6-source-validation-v1`, `source_id`, `predecessor_authority_row_sha256`, `checks`, and `findings`. `checks` has exactly `row_schema`, `capture_exists`, `capture_sha`, `evidence_exists`, `evidence_sha`, `payload_exists`, `payload_sha`, `effective_hash`, `projection_backing`, `raw_binding`, `media_bindings`, `coverage`, `surface_contract`, `identity`, `conflicts_absent`, `later_attempt_absent`, and `concurrency`; a check is boolean for applicable capture validation and JSON `null` only for terminal-only fields. `findings` is the sorted closed-enum defect list.
4. Exclusive-create `indexes/capture-authority-v6.json` with exactly 503 source-ID-sorted rows. Every row has exactly `source_id`, `selection: v5_capture_reuse|v6_terminal`, `predecessor_authority_path`, `predecessor_authority_sha256`, `predecessor_authority_row_sha256`, `capture_path`, `capture_sha256`, `evidence_path`, `evidence_sha256`, `payload_path`, `payload_sha256`, `complete_content_path`, `complete_content_sha256`, `raw_path`, `raw_sha256`, `effective_content_hash`, `coverage`, `surface`, `surface_contract_id`, `surface_contract_complete`, `terminal_path`, `terminal_sha256`, `terminal_disposition`, `validation_codes`, `validation_report_path`, and `validation_report_sha256`.
   - `v5_capture_reuse`: capture/evidence/payload/complete-content fields and effective hash are non-null; terminal fields are null; `validation_codes: []`; `surface_contract_complete` is a recomputed JSON boolean and may be `false` for a valid bounded/partial capture. `raw_path`/`raw_sha256` are non-null together when the predecessor binds immutable raw transport and otherwise both null; null raw is allowed only when the selected surface contract does not claim raw transport.
   - `v6_terminal`: capture/evidence/payload/complete-content/raw/effective/coverage/surface fields are null; terminal and validation-report fields are non-null; `validation_codes` contains the exact source defects or carry-forward state code.
   - `payload_projection: false` requires `payload_sha256 == effective_content_hash` and `complete_content_path/hash == payload_path/hash`.
   - `payload_projection: true` requires a distinct, immutable complete-content file whose bytes recompute to explicit `content_hash`, plus exact model-visible projection bounds. No T4V6 reuse is expected to satisfy this branch; expected projected reuse count is zero.
5. For every one of the 487 reused captures, independently verify:
   - exact predecessor authority row/file hashes and exact capture/evidence/payload/raw hashes;
   - evidence version, canonical URL, retrieval bounds/missing fields, media schema, and source-only payload; compare `evidence.payload_text.encode("utf-8")` directly to payload file bytes without universal-newline or whitespace normalization;
   - `resolve_effective_content_hash` returns no finding and equals authority/capture effective hashes;
   - coverage follows `complete > partial > failed`, never upgrades over explicit missing/truncation/uninspected essential media, and is not weaker than living coverage when later considered rewrite-eligible;
   - every media `local_path` exists and its SHA-256/byte count/content type/inspection status match; no binary semantic payload or mutable unretained essential media exists;
   - identity and surface contract are exact; no selected authoritative conflict or later capture attempt exists.
6. Exclusive-create `indexes/selected-files-v6.json` with exactly `schema`, `generated_at`, `authority_sha256`, `count`, `rows`, and `digest`. Each row has exactly `source_id`, `role: capture|evidence|payload|complete_content|raw|media|terminal|validation_report`, `logical_path`, and `file_sha256`; include every selected capture, evidence, payload, distinct complete-content, raw, media, terminal, and validation-report file exactly once by `(source_id, role, logical_path)`. Recompute the digest from these rows.
7. Require authority counts `487 v5_capture_reuse + 16 v6_terminal = 503`, zero projected reuse, zero nonterminal validation codes, and zero missing/duplicate/extra IDs. Run the independent verifier with `--scope evidence`, capture its exact stdout, then call `freeze-handoff --task B --verification-file <file>`. The writer copies the report to `indexes/verifications-v6/T4V6-B.json` and freezes `indexes/handoffs/T4V6-B.json`, binding authority, selected-files index/digest, all 503 validation-report hashes, all 16 terminal-record hashes, and `next_task: T4V6-C`.

#### T4V6-C. Independent reclassification and exact review plan

1. Parse current `MANIFEST.md` with the product registry table parser. Hash each exact Markdown row line plus `"\n"` and require equality with the inventory row hash. Hash each current artifact byte-for-byte and parse coverage/content hash with `atlas_quality._parse_frontmatter`. Missing/invalid living coverage, source ID, content hash, artifact, or row is `concurrent_drift` and blocks completion.
2. Apply the exact first-match table from T4V5-D, except that every v6 terminal row returns its terminal disposition before hash comparison. A nonterminal row with any validation code is a verifier failure, not an alternate classification branch. `source_changed` still requires byte-level historical proof; expected count is zero.
3. Exclusive-create `indexes/phase2_classify_v6-pre-review.json` and `phase2_summary_v6-pre-review.json` using the exact v5 classification row/top-level/summary field sets with schema names changed only to `phase2-classify-v6` and `phase2-summary-v6`. Every classification row binds the canonical v6 authority-row hash and selected evidence hash.
4. If A found only the known defects, require exact pre-review dispositions:
   - `blocked_evidence_regression: 265`;
   - `blocked_fetch: 11`;
   - `hash_baseline_incomparable: 221`;
   - `needs_same_hash_review: 6`;
   - total `503`, with `source_changed: 0`.

   Any count or source-ID difference is a C blocker; do not reinterpret it.
5. Exclusive-create `indexes/review-plan-v6.json` with exactly `schema: review-plan-v6`, `generated_at`, `contract_sha256`, `classification_sha256`, `count`, and `rows`. It contains exactly these six same-hash IDs, source-ID sorted:
   `014c8965ebc7`, `26035151aad9`, `6b6e4ed050aa`, `8aeb0868619b`, `939a1222bce1`, `e385c2e2611b`.
   Each row has exactly `source_id`, `artifact_path`, `artifact_sha256`, `evidence_path`, `evidence_sha256`, `effective_content_hash`, `v5_input_path`, `v5_input_sha256`, `v5_raw_output_path`, `v5_raw_output_sha256`, `v5_checklist_path`, `v5_checklist_sha256`, `v5_review_path`, `v5_review_sha256`, `v5_review_authority_row_sha256`, and `action: strict_v5_review_reuse`.
6. Run the independent verifier with `--scope classification`; require exact recomputation of all 503 decisions and the six-ID queue. Capture its exact stdout and call `freeze-handoff --task C --verification-file <file>` to freeze the report and `indexes/handoffs/T4V6-C.json` with nonempty hashes and `next_task: T4V6-D`.

#### T4V6-D. Strict review authority

1. For each of the six review-plan rows, independently revalidate the v5 review:
   - exact input schema and hashes bind the current artifact and selected v6 evidence/effective hash;
   - raw model output, checklist, review record, and v5 review-authority hashes exist and match;
   - checklist has exactly the seven fixed IDs in order and every pass/fail evidence string has a concrete `source:` or `artifact:` locator;
   - rerun `validate_summary(current_artifact, selected_evidence, checklist)` and require exact normalized finding equality;
   - recompute the review outcome from checklist failures, deterministic findings, and parse status; never trust stored `review_outcome`.
2. Expected strict reuse outcomes are:
   - `quality_fail`: `014c8965ebc7`, `26035151aad9`, `e385c2e2611b`;
   - `pass_current`: `6b6e4ed050aa`, `8aeb0868619b`, `939a1222bce1`.
3. Any failed v5 review binding, locator check, deterministic-validator recomputation, or outcome recomputation is a D blocker. Do not invoke a model, create `reviews-v6/`, alter the review plan, or infer a replacement review.
4. `finalize-reviews` exclusive-creates source-ID-sorted `indexes/review-authority-v6.json`. Each row has exactly `source_id`, `selection: v5_review_reuse`, `input_path`, `input_sha256`, `raw_output_path`, `raw_output_sha256`, `checklist_path`, `checklist_sha256`, `review_path`, `review_sha256`, `recomputed_findings`, and `recomputed_outcome`.
5. The same command exclusive-creates final `indexes/phase2_classify_v6.json` and `phase2_summary_v6.json`. Require zero `needs_same_hash_review`, exactly six completed semantic reviews, no unreviewable review, and exact final dispositions `blocked_evidence_regression: 265`, `hash_baseline_incomparable: 221`, `blocked_fetch: 11`, `quality_fail: 3`, `pass_current: 3`.
6. Run the independent verifier with `--scope reviews`; it must rerun every hash, locator, validator, outcome, and final classification transition. Capture its exact stdout and call `freeze-handoff --task D --verification-file <file>` to freeze the report and `indexes/handoffs/T4V6-D.json` with nonempty output hashes and `next_task: T4V6-E`.

#### T4V6-E. Candidate, independent verification, and final attestation

1. `freeze-candidate` recomputes all hashes/counts and exclusive-creates `indexes/T4V6_PROGRESS.md` plus `indexes/handoffs/T4V6-E-candidate.json`. The candidate has the A–D handoff fields except `verification_report_path`/`verification_report_sha256` are explicit `null`, `task: T4V6-E-candidate`, predecessor T4V6-D SHA-256, `blockers: ["PENDING_INDEPENDENT_VERIFY"]`, and `next_task: T4V6-E-attest`. Its nonempty `input_hashes`/`output_hashes` bind contract, writer/verifier, inventory, T4V5-F, all A–D handoffs and frozen stage-verification reports, v6 defects/plan/authority/selected-files/digest, pre/final classification/summary, review plan/authority, progress, exact counts, and the 503-ID union hash.
2. Run `t4v6_verify.py verify --scope all`, capturing stdout byte-for-byte to a newly-created OS temporary file. The independent verifier must recompute, not trust:
   - exact helper command surfaces, read/write boundaries, schemas, canonical serialization, and allowlist;
   - predecessor immutability and complete A–D/candidate SHA chain;
   - all 503 authority rows and every selected file byte/hash, including complete-content and media bindings;
   - projection declarations/backing bytes, semantic invariance, coverage, surface, identity, conflict/pending state, and current concurrency;
   - all 503 fixed-table decisions, disposition counts, proposed paths, and source-ID union;
   - all six review inputs/raw outputs/checklists/records, `validate_summary` findings, outcomes, and final transitions;
   - absence of unexpected IDs/files, pending/conflicts, unproven `source_changed`, nonterminal validation codes, and `indexes/rewrite-manifest-v4.json`.
3. The stdout object uses the exact common verification schema with `scope: all`, `target_path` set to the candidate logical path, `target_sha256` set to the candidate file SHA-256, and non-null selected-files/source-union fields. Require exit 0, `findings: []`, every named check `true`, and hashes equal the candidate.
4. Call `t4v6.py attest --verification-file <os-temp-file>`. It rejects any schema/hash/finding mismatch, exclusive-copies the exact report bytes to `indexes/T4V6_VERIFICATION.json`, and exclusive-creates `indexes/handoffs/T4V6-E.json`. The final handoff:
   - chains to T4V6-D and binds the E candidate/report/progress plus every candidate input/output hash;
   - has nonempty `output_hashes`, including candidate, verification report, progress, authority, selected-files index/digest, final classification/summary, and review authority;
   - reports exact disposition/review/no-model/terminal counts, `full_library_classified: true`, `full_library_reviewed: false`, `blockers: []`, and `next_task: T4.5`.
5. Run `t4v6_verify.py verify --scope final` after E exists. It reruns the full verifier and additionally validates the E wrapper/report/candidate chain. T4V6 completes only when this fresh run exits 0 with `findings: []`; otherwise preserve all bytes, leave T4V6 unchecked, and halt.
6. Only after the final run passes, update the durable plan once: mark T4V6 and A–E complete, record hashes/counts, and retain T4V5 as superseded negative evidence. No living write or rewrite manifest is authorized.


### T4V7. Black-box adversarial verification successor — rejected during external acceptance

T4V7 was verification-only. It performed no retrieval, model invocation, capture/classification/review generation, routing, living write, or T4V4/T4V5/T4V6 mutation. External review rejected it as approval authority; preserve its frozen bytes without repair. The agent that implemented or ran T4V7-A/B remains **not allowed to declare T4V7 complete or open T4.5**.

#### T4V7-A. Three-way implementation and frozen contract

1. Create exactly three helpers with no shared imports between them:
   - `helpers/t4v7.py`: sole writer for v7 execution artifacts;
   - `helpers/t4v7_verify.py`: independent read-only production verifier using one `verify_graph(reader, scope)` path for baseline and overlays;
   - `helpers/t4v7_adversary.py`: independent black-box runner. It must not import writer/verifier modules; it invokes the verifier CLI in child processes, creates overlays only in OS temporary directories, and never writes under the Atlas instance.
   Non-stdlib imports are limited to product modules `scripts.atlas_quality`, `scripts.atlas_url`, and `scripts.atlas_state`. None may import or execute a v4/v5/v6 helper, use network/model/connector mutation, or discover unspecified roots.
2. Closed command surfaces, each with required global `--root <connector-resolved-temp-root>`:

   ```text
   t4v7.py self-test
   t4v7.py freeze-contract --writer-self-test FILE --verifier-self-test FILE --adversary-self-test FILE
   t4v7.py freeze-candidate
   t4v7.py freeze-adversary --report FILE
   t4v7.py attest --verification-file FILE

   t4v7_verify.py self-test
   t4v7_verify.py verify --scope all|final [--overlay FILE]

   t4v7_adversary.py self-test
   t4v7_adversary.py run --scope all|final|sentinel --verifier FILE --contract FILE --workers 4
   ```

   `--overlay` is accepted only for an OS-temporary overlay with the frozen contract SHA and one mutation ID; it changes reads, never files. Any alias, implicit mode, extra command, root write by verifier/adversary, or different worker count is a blocker.
3. Exactly ten new paths are allowed:
   - helpers: `helpers/t4v7.py`, `helpers/t4v7_verify.py`, `helpers/t4v7_adversary.py`;
   - writer-owned: `indexes/T4V7_CONTRACT.json`, `indexes/T4V7_SELF_TEST.json`, `indexes/handoffs/T4V7-candidate.json`, `indexes/T4V7_ADVERSARY.json`, `indexes/T4V7_VERIFICATION.json`, `indexes/handoffs/T4V7.json`;
   - external-reviewer-owned: `indexes/T4V7_EXTERNAL_ACCEPTANCE.json`.
   Use exclusive-create, same-byte idempotence, and different-byte rejection. The executor/writer must never create the external-acceptance file.
4. All verifier reads flow through `verify_graph(reader, scope)`. HostReader is read-only. OverlayReader delegates unchanged paths to HostReader and substitutes/tombstones only paths declared by one overlay. Self-tests and production use this same function; toy validators and “concept” hash tests do not count.
5. Freeze `T4V7_SELF_TEST.json` as a bundle of exact writer/verifier/adversary self-test stdout bytes and SHA-256s. Writer tests exclusive-create/allowlist/attestation rejection. Verifier tests every semantic branch against a minimal valid in-memory graph. Adversary tests its process runner against known-good and deliberately accepting/rejecting fake verifier CLIs, proving baseline-pass, expected-diagnostic matching, timeout/non-JSON rejection, and no Atlas-root writes.
6. `T4V7_CONTRACT.json` binds the plan-at-freeze SHA, all three helper hashes, self-test bundle, T4V5-F, T4V6 contract/helpers/A–E/candidate/stage reports/final verification, inventory, current manifest and all 503 living artifacts, authority, selected-files index/digest, classifications/summaries, review plan/authority and six complete review byte sets. It contains exact expected counts, serialization, commands, paths, `protected_bindings`, `protected_json_pointers`, and `mutation_requirements`, each sorted and duplicate-free. The source plan and not-yet-created v7 outputs are excluded from `protected_bindings` to avoid self-reference.
7. `mutation_requirements` is generated by the writer from the frozen schemas/graph and is never supplied by the production verifier. Each row has `mutation_id`, `mode: integrity|semantic`, target path/pointer, cascade paths, expected stable finding code, and applicable scope. Integrity mode changes one target byte without updating parents. Semantic mode changes one field/collection and recomputes every declared outer hash/digest so only the independent semantic invariant can catch it. During `run`, the adversary independently enumerates the required set from its own schema table plus the contract’s protected graph and requires exact equality before launching any mutation; `freeze-adversary` rejects a set mismatch.

#### T4V7-B. Black-box mutation run and complete recomputation

1. `freeze-candidate` creates `indexes/handoffs/T4V7-candidate.json` with exact schema, contract/helper/self-test hashes, `status: PENDING_INDEPENDENT_VERIFY`, explicit null report fields, exact counts/unions/digest, and `(role, logical_path)`-sorted protected bindings. It has no free-form hash maps.
2. Run the adversary with `--scope all --workers 4`. It first invokes an empty-overlay baseline and requires exit 0, every check true, and `findings: []`. It then executes every contract mutation separately against the actual frozen graph through verifier subprocesses. A mutation counts as caught only when the verifier exits nonzero and returns its exact expected stable finding; unrelated setup/hash/parser failure is not acceptance. Results are sorted after parallel execution.
3. Mutation coverage includes:
   - one-byte mutation of every protected target;
   - every A–D/candidate/E schema, predecessor/report/helper/contract edge and every T4V6 `input_hashes`/`output_hashes` key/value;
   - selected-files wrong/omitted/extra/duplicate rows, recomputed-digest closure omission, and every authority-selected target;
   - representative reuse/terminal field and validation-check false/null mutations; projection, identity, surface, coverage, bounds, media, conflicts/later attempts, and concurrency;
   - every classification field/branch, source-ID omission/duplicate, count-preserving disposition swap, summary/union binding;
   - every review-plan/authority field and bound input/raw/checklist/review/artifact/evidence byte, checklist/locator/finding/outcome/final-transition mutation;
   - rewrite-manifest presence and every candidate/final wrapper field.
4. Five mandatory named semantic sentinels must be present and caught after cascade recomputation:
   - `v6_candidate_authority_output_hash_wrong`;
   - `v6_final_authority_output_hash_wrong`;
   - `selected_files_omit_row_recompute_digest`;
   - `classification_swap_preserve_counts`;
   - `review_authority_outcome_rebind`.
5. The adversary emits exact `t4v7-adversary-v1` JSON: scope, baseline stdout/SHA, helper/contract/candidate hashes, worker count, independently enumerated mutation IDs/digest, per-mutation overlay/stdout hashes and expected/observed finding, caught/wrong/missing/duplicate IDs, sentinel results, root before/after digest, checks, findings. Require exact contract/adversary mutation-set equality, all mutations caught by expected code, all five sentinels true, root byte identity, every check true, and `findings: []`. Capture stdout outside Atlas; `freeze-adversary` validates and copies exact bytes to `T4V7_ADVERSARY.json`.
6. Independently run `t4v7_verify.py verify --scope all` without overlay and capture stdout outside Atlas. It must directly recompute every protected binding; complete A→B→C→D plus D→candidate/E and candidate→verification→E graph; exact selected-files closure; all 503 authority/evidence/concurrency/classification rows; all six complete review bindings, `validate_summary` findings and outcomes; exact final transitions/counts; and absence of pending/conflicts/projected reuse/nonterminal codes/drift/rewrite manifests. Stored T4V6 booleans/counts/dispositions/hashes are never semantic approval.
7. `attest --verification-file` requires the frozen adversary report plus exact zero-finding baseline verification, then creates `T4V7_VERIFICATION.json` and `handoffs/T4V7.json`. The final handoff binds every v7/T4V6 input and report by named path/hash, has no free-form map, records exact counts/digests, `blockers: ["PENDING_EXTERNAL_ACCEPTANCE"]`, and `next_task: T4V7-external-review`.

#### T4V7-C. Separate external acceptance

1. `verify --scope final` has exactly two valid external-acceptance states: `PENDING` requires acceptance-file absence plus final-handoff blocker `PENDING_EXTERNAL_ACCEPTANCE`/next-task `T4V7-external-review`; `ACCEPTED` requires a hash-valid acceptance file with `decision: ACCEPTED_FOR_T4_5` binding that same handoff and the fresh independent-review reports. Any mixed/third state is a finding.
2. The T4V7 executor stops after reporting hashes for contract, self-test, candidate, adversary report, verification report, and final handoff. It leaves T4V7/A–C unchecked and must not create `T4V7_EXTERNAL_ACCEPTANCE.json`.
3. A separate agent/session that did not author the helpers or execute T4V7-A/B independently:
   - confirms helper hashes and closed imports/commands/write sets;
   - reruns `t4v7_verify.py verify --scope final` without overlay;
   - requires `external_acceptance_state: PENDING`, acceptance-file absence, and the exact pending blocker/next-task in the final handoff;
   - reruns `t4v7_adversary.py run --scope final --workers 4`, including all five named sentinels;
   - requires root byte identity, exact mutation-set equality, every mutation caught by expected code, every check true, and `findings: []`;
   - inspects the reports rather than accepting an executor summary.
4. Only that reviewer may exclusive-create `indexes/T4V7_EXTERNAL_ACCEPTANCE.json`, exactly `schema: t4v7-external-acceptance-v1`, reviewer/session identity, reviewed-at timestamp, plan/contract/helper/self-test/candidate/adversary/verification/final-handoff hashes, fresh verifier/adversary stdout hashes, mutation-set/sentinel results, root before/after digest, checks, findings, and `decision: ACCEPTED_FOR_T4_5`. Any finding, missing/false check, wrong sentinel, helper drift, or prior creation by the executor rejects acceptance.
5. After acceptance exists, the separate reviewer—not the executor—runs `verify --scope final` once more, requires `external_acceptance_state: ACCEPTED`, then marks T4V7 and A–C complete with exact hashes/counts. T4V6 remains superseded. T4V7 authorizes no manifest or living write; T4.5 still requires explicit go-ahead.

> **External review 2026-07-22-1458 — REJECTED.** All reported helper/artifact hashes matched. A fresh unmodified `verify --scope final` returned exit 0, `findings: []`, and `external_acceptance_state: PENDING`; a fresh 679-mutation final adversary run returned exit 0, all five sentinels true, and identical root digests. Those green reports are not acceptance because production-path review reproduced three false positives:
>
> 1. An OS-temporary overlay changed `handoffs/T4V7.json.named_path_hashes.T4V7_CONTRACT` to 64 zeroes; final verification still returned exit 0, every check true, and `findings: []`.
> 2. An OS-temporary acceptance overlay containing only `decision: ACCEPTED_FOR_T4_5` and the real final-handoff hash—no schema, reviewer identity, report hashes, mutation results, root digest, checks, or findings—returned exit 0, every check true, `findings: []`, and `external_acceptance_state: ACCEPTED`.
> 3. A fake verifier emitted only `unrelated::<sentinel-id>::noise` findings. `t4v7_adversary.py run --scope sentinel` nevertheless returned exit 0, every sentinel true, and `findings: []` because `mutation_caught` accepts substring matches rather than the exact expected finding.
>
> Static inspection confirms the causes: final verification does not validate the T4V7 candidate, frozen adversary/verification reports, final named bindings, or the full external-acceptance schema/bindings; the 679-row mutation set has no T4V7 candidate/final/external-acceptance targets despite the required wrapper coverage; writer/adversary use duplicated enumeration code rather than independently derived schemas; and the contract declares all three helper paths writer-owned in addition to the six allowed execution artifacts. `T4V7_EXTERNAL_ACCEPTANCE.json` and `rewrite-manifest-v4.json` remain absent. T4V7/A–C stay unchecked. Per the frozen contract, do not patch T4V7 in place; amend the plan outside T4V7 before any successor attempt.

### T4V8. Nonrecursive split-authorship verification successor — rejected at pre-accept

T4V8 removes the candidate/final-handoff recursion that defeated T4V7 and creates no candidate or final handoff. Its approval authority is not a verifier-authored wrapper: it is the exact tuple of contract, helper, deterministic pre/post report, and external-acceptance hashes recorded in this durable plan by a separate reviewer. The user approval recorded 2026-07-22 authorizes T4V8-A–C only; it does not authorize T4.5, a rewrite manifest, model invocation, routing, or any living write.

Execution intent: independently accept or reject the frozen T4V6 per-source outcomes while preserving every T4V4–T4V7 and living byte. A T4V8 finding freezes the eight v8 paths as negative evidence and requires a new plan amendment; no in-place repair or same-name retry is allowed.

Execution outcome: T4V8 froze `helpers/t4v8_verify.py` (`982dcfedf603e85c1b5836f0ba8e5647d4b95c60534548cf706bbc61beaa5941`), `helpers/t4v8_adversary.py` (`d8e37a41e0f9ec8522f8abf84da400e83ccf91efbf93254179e890ffedbfd152`), `indexes/T4V8_CONTRACT.json` (`ca8cc67738ea5722664e55b23b888ec415b892aad36114ee2079257f63c4fdba`), passing pre-accept verification (`474cbe1e63546f35f2100df94c4d7733d3d72319f903411372f7655c707c1a6f`), and failing pre-accept adversary evidence (`ddf9152b707012376e04189bf2fd2b4bb06361c82e373084625cede4cfd3cf64`). Roles were verifier author `5657F025-DE44-4A15-80C9-01D96E0957BF`, adversary author `role2-20260722153306-85409`, coordinator `9EF73B9E-7AC0-4298-8079-75393F765164`, and external reviewer `role4-20260722T085857Z-90394`.

The verifier self-test passed 38/38 and its baseline returned exit 0, `verification_completed: true`, `findings: []`, byte-identical output, and root identity. The adversary self-test passed 24/24, but the full pre-accept run caught 3685/3688 mutations. `source_disposition:6b6e4ed050aa`, `source_disposition:8aeb0868619b`, and `source_disposition:939a1222bce1` each returned exit 0 with no finding because the generic `wrong_value` path set an already-`pass_current` row to `pass_current`.

Static review also rejected T4V8's coverage claims: the 503 requirements declare family `wrong_value` while dispatching strategy `source_disposition`; the specialized strategy hard-codes `quality_fail`; mutation enumeration contains an always-true `or True`; the report hard-codes `mutation_set_equal: True`; contract `mutation_requirements` bypass independent derivation; recursive family×pointer×binding coverage is incomplete, including living-byte coverage; and final classification can fall back to hard-coded pass/quality-fail ID sets when review authority is absent. These are successor requirements, not permissions to repair T4V8.

The original T4V8-A–C procedure below is retained only as the historical execution contract. It is non-executable after rejection: do not rerun, patch, accept, or complete it; the next possible execution task is T4V9 after explicit approval.

#### T4V8-A. Two deep modules, split authorship, and declarative contract

1. Create exactly two read-only modules with these closed interfaces:

   ```text
   t4v8_verify.py --root ROOT self-test
   t4v8_verify.py --root ROOT verify --contract FILE --phase preaccept|postaccept [--overlay FILE]

   t4v8_adversary.py --root ROOT self-test
   t4v8_adversary.py --root ROOT run --contract FILE --verifier FILE --phase preaccept|postaccept --suite full|sentinel --workers 4
   ```

   `t4v8_verify.py` owns one deep `verify_graph(reader, contract, phase)` implementation used by host and overlay readers. `t4v8_adversary.py` treats the verifier only as a subprocess protocol; it must not import, execute in-process, parse, or inspect verifier source. Neither helper imports any T4V4–T4V7 helper. Non-stdlib imports are limited to product `scripts.atlas_quality`, `scripts.atlas_url`, and `scripts.atlas_state`. No extra command, alias, implicit phase, network/model/connector mutation, or Atlas write is allowed.
2. Enforce four recorded process roles:
   - verifier-author session writes only `helpers/t4v8_verify.py`;
   - a different adversary-author session writes only `helpers/t4v8_adversary.py` and receives the frozen interface/schema requirements, not verifier implementation text;
   - a coordinator that authored neither helper verifies both self-test stdout objects and exclusive-creates only `indexes/T4V8_CONTRACT.json`;
   - a later external-reviewer session that held none of those roles runs T4V8-B/C and owns only the five report/acceptance files.
   Any shared helper implementation, copied mutation enumerator, role reuse, or wider write set is a blocker.
3. Exactly eight T4V8 paths are allowed:
   - `helpers/t4v8_verify.py`;
   - `helpers/t4v8_adversary.py`;
   - `indexes/T4V8_CONTRACT.json`;
   - `indexes/T4V8_PREACCEPT_VERIFICATION.json`;
   - `indexes/T4V8_PREACCEPT_ADVERSARY.json`;
   - `indexes/T4V8_EXTERNAL_ACCEPTANCE.json`;
   - `indexes/T4V8_POSTACCEPT_VERIFICATION.json`;
   - `indexes/T4V8_POSTACCEPT_ADVERSARY.json`.
   Each owner uses exclusive-create, same-byte idempotence, and different-byte rejection. Temporary overlays/stdout live only in OS temporary directories.
4. `T4V8_CONTRACT.json` has exact schema `t4v8-contract-v1` and binds:
   - this plan's SHA-256 at T4V8 freeze, both helper byte hashes and distinct author-session identities, exact commands/ownership/allowed paths, deterministic serialization, and both self-test stdout hashes/results;
   - T4V5-F; every frozen T4V6 helper/contract/A–E/candidate/stage report/verification/inventory/authority/selected-file/classification/summary/review-plan/review-authority/review byte; all selected capture/evidence/payload/complete-content/raw/media/terminal/validation bytes; current manifest plus all 503 living artifact hashes;
   - every frozen T4V7 helper/contract/self-test/candidate/adversary/verification/final byte as negative evidence, plus required absence of `T4V7_EXTERNAL_ACCEPTANCE.json` and both rewrite manifests;
   - exact source-ID sets, review IDs, expected-but-untrusted 487/16 and 265/11/221/3/3 assertions, selected-files digest, and the complete schema/invariant/sentinel catalogs below.
   Bindings are sorted unique `{role, logical_path, sha256}` rows. The contract cannot bind its own hash; reports and the later plan annotation bind it.
5. The contract is declarative data, not executable mutation code:
   - `schema_catalog` gives exact required keys/types/enums/nullability and `additional_properties: false` for every critical T4V6 handoff/authority/selected-file/classification/review row, deterministic report, and T4V8 acceptance object;
   - `invariant_catalog` gives stable exact finding codes and required target roles for the full hash graph, selected-file one-to-one closure, 503 authority/evidence/concurrency/classification outcomes, six reviews, counts/unions, T4V7 negative bindings, acceptance bindings, and manifest absence;
   - `mutation_families` requires wrong value/type/enum/hash/path, omission, forbidden null/false, unexpected property, raw duplicate key, and array omission/extra/duplicate/reorder for every applicable schema pointer; one-byte mutation for every target binding; every handoff map key/value plus omitted/extra key; at least one source-specific disposition-relevant mutation for each of 503 IDs; every classification/review branch; and every acceptance field in `postaccept`;
   - baseline exact-key validation means an omitted catalog field makes the real artifact an unexpected property, preventing a shared catalog omission from silently passing.
6. Ten mandatory semantic/protocol sentinels are exact IDs:
   - `v6_candidate_authority_output_hash_wrong`;
   - `v6_final_authority_output_hash_wrong`;
   - `selected_files_omit_row_recompute_digest`;
   - `classification_swap_preserve_counts`;
   - `review_authority_outcome_rebind`;
   - `t4v7_final_named_binding_wrong`;
   - `t4v8_acceptance_schema_missing`;
   - `t4v8_acceptance_report_hash_wrong`;
   - `t4v8_acceptance_unexpected_field`;
   - `diagnostic_substring_rejected`.
   Mutation acceptance requires the exact expected code as a complete finding-list element, nonzero verifier exit, `verification_completed: true`, and absence of setup/parser/internal-error findings. Prefix/suffix/substring matches are forbidden.
7. Both modules emit deterministic canonical JSON with no timestamp, host path, random temp path, scheduling order, or environment-dependent field. Parallel results sort by mutation ID. A phase's reported protected-root digest excludes only that phase's two not-yet/frozen report destinations so reruns remain byte-identical; independently, each run compares the complete before/after path→hash inventory including those destinations in memory and requires `workspace_identity: true`, catching any write. Self-tests use the production interfaces and include malformed/duplicate-key JSON, exact-vs-substring diagnostics, expected-plus-unrelated-failure rejection, non-JSON, timeout, exit-code mismatch, phase mismatch, overlay restriction, report-destination presence, protected-digest stability, and full-workspace identity cases.

#### T4V8-B. Deterministic pre-accept verification

1. The external reviewer first confirms the exact eight-path namespace, role separation, helper/contract hashes, closed imports/commands/write sets, self-tests, contract key sets, target-role closure, and that external acceptance plus both rewrite manifests are absent.
2. Run `verify --phase preaccept` without overlay. It must require acceptance absence and directly recompute—not trust stored claims:
   - every contract/helper/target byte and complete T4V5-F → T4V6 A→B→C→D plus D→candidate/E and candidate→verification→E graph;
   - exact selected-file digest and one-to-one authority closure, rejecting missing/unrelated/duplicate paths;
   - all 503 authority schemas, payload bytes/effective hashes, projection backing, coverage/bounds/surface/identity/media/raw/conflict/later-attempt/validation/concurrency fields;
   - all 503 first-match pre/final classifications, counts/unions/summaries, zero unproven `source_changed`, exact six-ID queue, and no pending/conflict/drift/projected reuse;
   - all six artifact/evidence/input/raw/checklist/review bindings, exact checklist order/locators, fresh `validate_summary`, outcome, review authority, and final transition;
   - frozen T4V7 negative bindings, known defect evidence, and rewrite-manifest absence.
3. Run the adversary `--phase preaccept --suite full --workers 4`. It generates mutations generically from `schema_catalog` plus `mutation_families`, never from verifier source or a duplicated writer enumerator. Each mutation uses a single OS-temp overlay and verifier subprocess. Require exact mutation-ID set/coverage-matrix equality, exact diagnostic membership, all applicable sentinels, no wrong/missing/duplicate IDs, deterministic stdout, root byte identity, every report check true, and `findings: []`.
4. The reviewer captures both stdout byte streams outside Atlas, reruns each once for byte identity, validates exact report schemas/key sets directly against the contract, then exclusive-copies the bytes to `T4V8_PREACCEPT_VERIFICATION.json` and `T4V8_PREACCEPT_ADVERSARY.json`. Any mismatch or finding stops before acceptance.

#### T4V8-C. External acceptance, post-accept verification, and plan binding

1. Only the external reviewer may exclusive-create `T4V8_EXTERNAL_ACCEPTANCE.json`, exact schema `t4v8-external-acceptance-v1`, with no extra keys: decision `ACCEPTED_FOR_POSTACCEPT_VERIFY`, reviewer/session identity, reviewed-at timestamp, plan-at-freeze/contract/helper hashes, both pre-accept report hashes, target-graph/selected-files/source-union/mutation-set digests, mutation count, exact applicable pre-accept sentinel results, exact required post-accept sentinel IDs, root before/after digest, exact checks, and `findings: []`. The file alone is never T4.5 authority.
2. Run `verify --phase postaccept` without overlay. It repeats every pre-accept recomputation and additionally requires the acceptance file's exact schema/key set/types/decision and every declared hash/digest/count/check/finding binding. A missing, extra, duplicate, null, stale, or wrong acceptance field is a finding.
3. Run the adversary `--phase postaccept --suite full --workers 4`. It repeats all graph/protocol mutations and additionally applies every schema mutation family to every acceptance field/raw key. All ten sentinels, including malformed-acceptance and substring rejection, must be caught by exact diagnostics with root byte identity and deterministic output.
4. Capture, rerun for byte identity, validate, and exclusive-copy exact stdout to `T4V8_POSTACCEPT_VERIFICATION.json` and `T4V8_POSTACCEPT_ADVERSARY.json`. If either fails, the unbound acceptance remains rejected negative evidence and a new amendment is required.
5. Only after both post-accept reports pass, the external reviewer updates this plan once with a `T4V8 accepted authority` annotation containing all eight path hashes, plan-at-freeze hash, exact counts/digests/mutation coverage, author/reviewer session identities, and acceptance timestamp. That plan annotation—not any helper-authored handoff—is the nonrecursive T4.5 trust anchor. Then and only then check T4V8/A–C complete. T4.5 remains blocked pending separate explicit user go-ahead.

### T4V9. Exhaustive five-role verification attempt — rejected and retired

T4V9 is not retried. It took about five hours, optimized for proving a temporary verification graph rather than improving future source quality, and still ended with incomplete diagnostic calibration.

Observed outcome:

- R1 verifier `5509ef4b-116f-417a-9142-c70355c18685`, R2 oracle `6b305090-9db3-43d8-a96e-8298da9d9308`, R3 adversary `CEB46080-E200-474C-93F0-367485049C85`, and R4 coordinator `7a003ef1-569e-4a84-b953-ddbc3c2fc234` produced OS-temporary candidates; R5 never sealed;
- candidate SHA-256 values were verifier `47459a8d4c742e9fc9945f1ba558be76e2d83173a5927bd18a67cfc3c7c24f54`, oracle `50448a73083455a90008a539c40165dbb84729e2b11b27e34b3c2963e5320d79`, adversary `75a33dc1057a6359ee6ed176cbf57679a5f90da39040e96a192f12aa74a23550`, and contract `e80ae0f14e74f7f2b9201b4cd45d537f2548a19793ef476758b47817de43b980`;
- self-tests and baseline/oracle/sentinel-only checks passed, but full adversary runs improved only from 1027/7365 to 6715/7365;
- residuals were 530 schema-diagnostic mismatches, 120 binding-diagnostic misses, 18 no-ops, 15 missing pointers, one complete-matrix mismatch, 76 uncaught zero-exit cases, and false full-run sentinels;
- R1 hard-coded a workstation product path and did not bind imported product bytes;
- all eleven T4V9 Atlas paths, all T4V8 acceptance/post paths, and both rewrite manifests remained absent; no predecessor or living byte changed.

The durable lessons move into T4P contracts, product validators, skills, and regression tests. The candidate modules, 7365-row matrix, role choreography, and mutation cross-product do not become Atlas product features.

#### T4V9-A. Historical candidate attempt

Preserve only the identities, hashes, and findings above. `/tmp/t4v9-roles/` is disposable OS-temporary state and is never approval authority.

#### T4V9-B. Historical rehearsal attempt

The green baseline and sentinel-only run do not override the failed full run. Do not repair, rerun, seal, or copy the candidates into Atlas.

#### T4V9-C. Historical acceptance step

Not reached. No T4V9 report, acceptance, or authority path may be created. The next executable task is T4P after explicit approval.

### T4P. Lean text-only Atlas source productization

Entry gate: explicit T4P execution approval. T4P changes only product-owned architecture/contracts/scripts/skills/tests and, after any required connector approval, the product-owned architecture snapshot. It performs no cohort rewrite, model generation, route mutation, manifest creation, or temp cleanup.

Execution intent: make the normal `atlas-source` path carry the value from the re-review. Keep the interface short and model-guided; use deterministic code only for exact text/schema/hash checks, not for brittle page-type heuristics or provider-specific scraping.

#### T4P-A. Durable source-entry invariants

1. Update `.agents/ARCHITECTURE.md` first with four concise invariants:
   - a source summary artifact is Markdown text only; Atlas retains no image, audio, video, screenshot, binary document, or downloaded media asset for a source summary;
   - readable text may be extracted transiently from HTML, Markdown, or a text-bearing document such as PDF, but only the extracted text and textual source links may enter the summary/evidence path; transient source files are cleanup data, never living assets;
   - if the canonical link cannot be opened, requires unavailable authorization, resolves to an error/empty/non-text payload, or exposes too little text for a faithful summary, halt before any artifact or registry write and notify the user with the URL and short reason;
   - when the opened page is an **aggregate page**—its primary purpose is listing child resources whose own pages contain the substantive material—ask one concise scope question before ingestion: summarize only the page text, or expand the discovered child entries as separate sources.
2. Keep aggregate-page recognition intentionally semantic, not a hard-coded URL/domain/link-count classifier. A normal article with supporting links is not an aggregate page. If clearly page-only or clearly a single substantive source, do not ask.
3. For `page-only`, read and summarize only text on the supplied canonical page; never import child bodies. For `expand`, report the discovered child count, obtain the user's choice once, and ingest each chosen child URL independently through the ordinary `atlas-source` path. Do not create a custom scraper, provider branch, or aggregate source identity.
4. If the user does not answer the scope question, halt without writing. The prompt remains one short question with two concrete choices; do not encode an interview script.

#### T4P-B. Simplified deterministic text validation

1. Update `atlas-core/assets/markdown-registry-contracts.md`, `source-summary-quality-guide.md`, and `source-summary-template.md` to remove retained-media requirements and make the canonical URL plus extracted UTF-8 text the semantic boundary. The template may contain textual links but no embeds, attachment blocks, media inventories, or asset paths.
2. Keep one deep deterministic owner in `scripts/atlas_quality.py`:
   - require nonempty `payload_text` and compare `payload_text.encode("utf-8")` directly with any transient retained text bytes;
   - compute `content_hash` from complete extracted readable text bytes with no universal-newline, Unicode, or whitespace normalization;
   - permit a model-visible projection only when transient complete extracted text bytes match the explicit hash and exact byte ranges reconstruct the visible text;
   - reject media/asset payload fields, binary content, unsupported extra fields, unbacked projection, and artifact/evidence hash disagreement with exact findings.
3. Make `scripts/atlas_source.py` reuse that owner instead of mirroring effective-hash logic. Preserve only `same-hash|changed-hash` reducer modes; an inaccessible, partial, or unproven comparison is a no-write result, not a guessed transition. `hash_baseline_migration` may remain a reporting reason, never a reducer mode; `stale_content` stays forbidden.
4. Do not add a page classifier, scraper, media pipeline, or campaign CLI. Retrieval and aggregate-page scope are agent interaction decisions in `atlas-source`; Python remains responsible only for exact deterministic validation and reduction.

#### T4P-C. Concise drafting and quality calibration

1. Update `.agents/skills/atlas-source/SKILL.md` with a short entry sequence:
   - open the supplied canonical link;
   - halt and notify on inaccessible or insufficient textual content;
   - ask the one aggregate-page scope question only when needed;
   - build a text-only source envelope;
   - draft, run the separate seven-item checklist and `validate-summary`, permit at most one targeted revision, then classify/route/write.
2. Keep the seven checklist IDs and high-signal semantics: primary contribution, material mechanics/examples, source support, consequential limits/uncertainty, context neutrality, assessment coherence, and proportionality. Do not add exact prose, section-length, bullet-count, citation-count, or similarity thresholds.
3. Add only compact positive and near-miss cases to `assets/evals/source-summary-quality.json` for inaccessible text, aggregate page-only versus child expansion, thin/insufficient text, primary-contribution loss, missing mechanics, missing limits, unsupported claims, and filler. Calibration remains optional and read-only.
4. Keep all durable instructions provider-neutral. The active repository harness/model is transport; no Grok-specific or OMP-specific prompt branch enters Atlas product artifacts.

#### T4P-D. Product verification and binding

1. Add behavioral tests in `tests/test_atlas_quality.py` and `tests/test_atlas_source.py` for exact text bytes/hashes, binary/media-field rejection, projections, inaccessible/insufficient no-write results, and comparable transitions. Each test must fail on a former false-positive path rather than assert prose in a skill file.
2. Run:

   ```text
   python3 -m unittest tests.test_atlas_quality tests.test_atlas_source tests.test_atlas_harness_surface
   python3 scripts/atlas-instance.py check
   ```

   Unit tests must pass. Under prerequisite B, the instance check may report only the known missing `vault://atlas/todos/TODOs.md` seed path.
3. Perform two read-only skill smokes with no Atlas writes: one inaccessible URL result must halt with a concise notification; one supplied aggregate-page result must produce one concise page-only/expand question. Grade behavior, not exact wording.
4. If architecture changed, sync the product-owned bound snapshot only after any required connector/profile approval, then repeat the instance check.
5. Record a `T4P accepted productization` annotation in this plan with exact changed product paths/hashes, tests, smoke outcomes, snapshot status, and confirmation that no living source/registry byte or rewrite manifest changed. Then check T4P/A–D.

##### T4P accepted productization (2026-07-23-1739)

Product-only change. No living source artifact, MANIFEST, RELATIONS, TOPICS, VOCAB, rewrite manifest, or T4L path was written. No model generation and no cohort rewrite.

**Unit tests:** `python3 -m unittest tests.test_atlas_quality tests.test_atlas_source tests.test_atlas_harness_surface` → 43 OK.

**Instance check (prerequisite B):** only known finding `instance missing seed path: vault://atlas/todos/TODOs.md`. Product-owned `ARCHITECTURE.md` synced to bound instance `atlas` and byte-matches product.

**Smokes (read-only, no Atlas writes):**
- Empty / media-backed evidence returns fail-closed identity findings (`EVIDENCE_PAYLOAD_TEXT_INVALID`, `EVIDENCE_MEDIA_ASSET_REJECTED`); `classify_hash_transition` raises rather than guessing a reducer mode.
- `atlas-source` skill + quality guide encode inaccessible-link halt (URL + short reason, no fallback) and one aggregate page-only/expand question; normal articles do not force the question. Graded by procedure coverage tests, not exact wording.

**Living concurrency (unchanged by T4P):**
- `summaries/sources/MANIFEST.md` SHA-256 `1ddc4ac63464a7cba632b00bafd1250063ad5f62a20725cd6cb1d35daebc0987`
- `indexes/rewrite-manifest-v4.json` absent
- `indexes/T4L_COHORT_VALIDATION.json` / `T4L_EXTERNAL_REVIEW.json` absent

**Changed product paths (SHA-256 of on-disk bytes):**

| Path | SHA-256 |
|---|---|
| `.agents/ARCHITECTURE.md` | `fd3df0f628965e6e83a5b06a786c051340560f07d1be700e89df8b7dffe813c4` |
| bound instance `ARCHITECTURE.md` (synced) | `fd3df0f628965e6e83a5b06a786c051340560f07d1be700e89df8b7dffe813c4` |
| `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` | `fc22fb94b3d49b43ae92ce5e8c7e176c95c05539a4cd8a9c6de4b014552b66c5` |
| `.agents/skills/atlas-core/assets/source-summary-quality-guide.md` | `2f078b38a730ea0ad5da83552175f3b5c1286f9b380a23d3ad8fb9c15852f37f` |
| `.agents/skills/atlas-core/assets/source-summary-template.md` | `933f9b7b2fb43b9d6ee4bf01076e3fa9665677bf024591cfcb3e09455f38dca2` |
| `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` | `15556c82ee7c7b70012149fa3b423d65a84df1faddb59d88b9eede4b0b6a2347` |
| `.agents/skills/atlas-source/SKILL.md` | `ac233c6df691bfc37a915a44c62722f93e8d7d214213be7d1664248076fb752d` |
| `scripts/atlas_quality.py` | `ace1cdd1b67997734e3787315f2d68b7a5dd50c48ae8e25f3837696c2141cab1` |
| `scripts/atlas_source.py` | `ec1b4fec9eaf0bd7393f6ad817b40c6b40a65ce0ecd20f8cc680d8ef2d6f2b46` |
| `tests/test_atlas_quality.py` | `313da4f693ab26465e55fb483835f97e66fd659c8a3beeef9bc0d36ad7a39dfb` |
| `tests/test_atlas_source.py` | `d7122c3cce81c6afacc39f42f190f030e05c85652db4867514000b38865fee86` |
| `tests/test_atlas_harness_surface.py` | `2a86d23561d60fdd5b4c533164c746b05e41d47c5f87bf248c9bf3c3ce4f4d20` |

**Behavior delivered:**
- Text-only source summaries; media/binary asset fields rejected.
- Nonempty raw UTF-8 `payload_text`; `content_hash` without newline/Unicode/whitespace normalization.
- Projection allowed only when `complete_text` hashes to the explicit hash and `projection_ranges` reconstruct `payload_text`.
- `atlas_source` reuses `atlas_quality.resolve_effective_content_hash`; `classify_hash_transition` returns only `same-hash|changed-hash` or raises for unproven evidence.
- Skill entry: open → halt if inaccessible/insufficient → optional aggregate scope question → text-only envelope → draft → seven-item checklist + `validate-summary` → classify/route/write.

### T4L. One lean deterministic cohort review

T4L is the only remaining acceptance attempt in this plan. It uses productized validators and permanent regression tests; it creates no helper module, oracle, mutation matrix, candidate/final wrapper, model output, retrieval, route, or living write.

Exactly two temp paths are allowed:

- `vault://atlas/tmp/source-quality-revisit-2026-07-21/indexes/T4L_COHORT_VALIDATION.json`;
- `vault://atlas/tmp/source-quality-revisit-2026-07-21/indexes/T4L_EXTERNAL_REVIEW.json`.

#### T4L-A. Validate actual cohort rows

1. Require the accepted T4P plan annotation/current product hashes, exact frozen 503-ID cohort, unchanged living concurrency hashes, and absence of both T4L paths and both rewrite manifests.
2. Run current product validators against every actual selected row using text only. Recompute identity, exact text/effective/living hashes, projection backing, coverage, disposition, classification, and the six existing review/checklist outcomes. Media files or claims are neither required nor accepted; a row whose fidelity depends on non-text evidence is explicit no-write.
3. Exclusive-create source-ID-sorted `T4L_COHORT_VALIDATION.json` with exact 503 rows, product hashes, input hashes, validation findings, disposition, and `eligible: true|false`. Invalid/blocked rows are legitimate classified results; incompleteness means a missing/unbound/unexplained row or failed validator, not merely `eligible: false`.

#### T4L-B. Fixed regression proof

1. Run the permanent unit/eval cases covering every observed false-positive family: wrong or missing output binding, malformed wrapper/acceptance, substring diagnostic, no-op alternate value, family/strategy mismatch, constant-true/set-equality shortcut, missing review fallback, unsupported provenance/media, unbacked projection, incomplete text, assumed comparability, and classification swap.
2. Use one representative positive and one near-miss per invariant family. Do not enumerate every schema family × pointer × binding; test behavior at the owning product interface.
3. Require deterministic report bytes, exact 503-ID closure, all product tests green, no unexplained finding, and no T4L or living byte drift beyond the declared validation report.

#### T4L-C. Independent review and one-run decision

1. A reviewer who did not create the cohort report verifies its exact schema/hash, 503-row closure/arithmetic, current product bindings, every fixed regression result, the five historically invalid capture IDs, the six review rows, and a source-ID-sorted cross-domain sample of additional eligible/blocked rows.
2. The reviewer exclusive-creates `T4L_EXTERNAL_REVIEW.json` with `decision: ACCEPTED_FOR_T4_5|REJECTED_INCOMPLETE`, exact report/product/plan hashes, reviewed rows, findings, and checks.
3. `ACCEPTED_FOR_T4_5` requires all checks true, no unexplained finding, and every row either product-valid eligible or exact no-write. Record both T4L hashes/counts in this plan and check T4L/A–C.
4. `REJECTED_INCOMPLETE` ends the cohort-verification approach immediately. Do not repair T4L, create T4V10/T4V11, or open T4.5. Materialize the separate ten-source comparative calibration plan specified under **Triggered successor plan** and halt this plan's rewrite path.

##### T4L accepted cohort review (2026-07-23-2009)

- Plan SHA-256 at validation/review: `879476e5ec13be3287f3432d80f8461826beb79369032441dac2b8dd02b1c545`.
- Cohort report: `vault://atlas/tmp/source-quality-revisit-2026-07-21/indexes/T4L_COHORT_VALIDATION.json`, SHA-256 `604025ff149e49c1f5e0dec3d3d2d6d9d6f890b8fee0132263bd04189cbed5fb`.
- Independent review: `vault://atlas/tmp/source-quality-revisit-2026-07-21/indexes/T4L_EXTERNAL_REVIEW.json`, SHA-256 `3dd3b2b89dd7d23e88446b0d0de4316e4cc22c6862b1464b645f24527164dcd3`, decision `ACCEPTED_FOR_T4_5`, checks all true, findings empty.
- The independent `T4LReviewer` authored the exact external-review bytes. Because its reviewer tool surface was read-only, Main acted only as the connector persistence adapter: exclusive-created the returned 7,697 bytes and verified byte identity and SHA-256 without editing.
- Recomputed closure: 503 total, 2 eligible, 501 exact no-write. Dispositions: 266 `blocked_evidence_regression`, 11 `blocked_fetch`, 221 `hash_baseline_incomparable`, 3 `pass_current`, 2 `quality_fail`.
- Exact eligible IDs: `014c8965ebc7` and `26035151aad9`, both proposed `same-hash`. All five historically invalid captures, all 166 media-backed evidence rows, all 95 incomplete-coverage rows, all 221 unproven historical transitions, all 16 terminals, and all 3 pass-current rows remain no-write.
- The six prior review/checklist rows were rebound and rerun: 3 `quality_fail`, 3 `pass_current`; `e385c2e2611b` narrowed from `quality_fail` to `blocked_evidence_regression` under the text-only media rejection.
- Ten representative invariant-family regressions passed; the targeted product suite ran 43 tests successfully. The cohort report round-tripped byte-identically, all 3,075 selected-file bindings matched, registries validated, protected living/product digests were unchanged, frozen T4V8 hashes matched, and both rewrite manifests remained absent.
- This acceptance authorizes no manifest or living write. It opens only the separate T4.5 approval gate below.

### T4.5. Freeze rewrite-manifest-v4 from accepted T4L output and obtain living-write approval

T4.5 starts only after `T4L_EXTERNAL_REVIEW.json` says `ACCEPTED_FOR_T4_5`, its exact hashes/counts are plan-bound, and the user separately authorizes manifest creation.

1. Recheck the T4P product hashes, both T4L hashes, exact 503-row closure, current manifest/artifact concurrency, and absence of both rewrite manifests.
2. Exclusive-create source-ID-sorted `indexes/rewrite-manifest-v4.json`, status `PENDING_USER_APPROVAL`, binding the current plan, T4P productization, T4L validation/review, current cohort hashes, counts, and rows.
3. Include only `T4L_COHORT_VALIDATION.json` rows with `eligible: true`, empty product validation findings, proven comparable text hashes, sufficient textual evidence, and proposed path `same-hash|changed-hash`. Bind exact source/artifact/manifest/text-evidence/checklist hashes and disposition reason.
4. Exclude every inaccessible, insufficient-text, non-text-dependent, media-dependent, blocked, unsupported, terminal, pass-current, concurrent, unbacked-projection, or unproven-comparability row.
5. Recompute eligible and exclusion counts from rows; preserve no historical target such as 224.
6. Halt until the user approves the exact manifest SHA-256 or exact source-ID subset. A subset becomes deterministic `rewrite-manifest-v4-approved.json` with parent hash, exact IDs, unchanged rows, approval timestamp, and projection hash. T5 starts only from that approved file.

##### T4.5 candidate manifest (2026-07-23-1425)

- Pre-annotation plan SHA-256: `a364e7bf88e3a0dafe07599a49e832386abf9445631f39ce3fc47f83f61858cf` (bound inside the candidate as `plan_sha256`).
- Candidate path: `vault://atlas/tmp/source-quality-revisit-2026-07-21/indexes/rewrite-manifest-v4.json`
- Candidate SHA-256: `9cd10cb1c6ddfea3ef4e13808e08042877b5e9775ec32431523bea63ed06b66b` (7604 bytes; `built_at` `2026-07-23T14:25:56+00:00`).
- Status: `PENDING_USER_APPROVAL` — not approved; `rewrite-manifest-v4-approved.json` absent; T5 blocked; candidate authorizes no living write.
- Counts: eligible 2 / same-hash 2 / changed-hash 0; excluded total 501 = blocked_evidence_regression 266 + blocked_fetch 11 + hash_baseline_incomparable 221 + pass_current 3.
- Exact eligible source IDs (source-ID-sorted): `014c8965ebc7`, `26035151aad9` — both disposition `quality_fail`, proposed_path `same-hash`.
- T4L authority bound: cohort `604025ff149e49c1f5e0dec3d3d2d6d9d6f890b8fee0132263bd04189cbed5fb`, external `3dd3b2b89dd7d23e88446b0d0de4316e4cc22c6862b1464b645f24527164dcd3`, decision `ACCEPTED_FOR_T4_5`.
- T4.5 and T5 remain unchecked pending separate approval of this exact SHA-256 or an exact deterministic source-ID subset.

##### T4.5 exact-manifest approval (2026-07-23-2216)

- The user explicitly approved the complete 7,604-byte candidate with SHA-256 `9cd10cb1c6ddfea3ef4e13808e08042877b5e9775ec32431523bea63ed06b66b`.
- Approval scope is the exact two-row manifest: `014c8965ebc7` and `26035151aad9`, both `same-hash` / `quality_fail`; no subset was requested and `rewrite-manifest-v4-approved.json` remains absent.
- Candidate bytes remain immutable at status `PENDING_USER_APPROVAL`; this plan annotation records the external exact-byte approval without changing the approved hash.
- Plan SHA-256 immediately before recording approval: `40f20ce6e0e3bca55a56cca1685809565c2f54522815085432e42f7fc8434ed1`.
- This completes T4.5 only. It does not authorize T5 retrieval, generation, routing, source/registry mutation, or cleanup; those remain behind their separate execution gates.

### T5. Phase 3 — approved rewrites only

Entrypoint: **`atlas-source --resummarize`** (not freestyle repair).
T5 is blocked until T4P and T4L are plan-bound, T4.5 has explicit go-ahead, and an exact manifest or deterministic subset is separately approved.

For each **approved** ID only:

1. Reopen the canonical link through the productized text-only path. If it is inaccessible, insufficiently textual, or now an unresolved aggregate page, record no-write and notify; never fall back to old prose, media, sibling sources, or model priors.
2. Require exact agreement with the approved T4.5 row for canonical URL, text evidence/effective hash, artifact and manifest concurrency, disposition, and checklist bindings. Any drift becomes `concurrent_drift` and needs new approval.
3. Run the full product path: canonical text → source-only draft → separate checklist → `validate-summary` → at most one targeted revision → source and route transactions. Persist only the Markdown source artifact and normal registries/run records; retain no media/asset file.
4. Before write, current manifest row and artifact hashes must match the approved record; otherwise skip without silent rebase.
5. Snapshot `TOPICS.md` and `RELATIONS.md` **before** the write batch item (or before each write) for later diff.
6. Record:

```text
rewrites/<source_id>--<before_artifact_sha256_12>.json
```

Bind before/after artifact hashes, disposition, route outcome, revision count (g0/g1), and `affected_topic_ids` computed by the **deterministic before/after diff** below (not from a reducer field that does not exist).

7. **`affected_topic_ids` (exact, no reducer API change):**  
   `atlas_state.ReductionResult.derived` is a full topic snapshot, **not** an affected-ID list. Do **not** extend the reducer interface in this plan.  
   After each successful source/route write (or after the approved rewrite batch), compute:

   - compare pre/post `TOPICS.md` rows by **Topic ID** (any field change counts);
   - compare pre/post `RELATIONS.md` rows by **Edge ID**; collect **Topic ID** of every added, removed, or changed relation row;
   - stable-sort the union of those Topic IDs as `affected_topic_ids`.

   Accumulate the union of those sets across all successful rewrites for T6.

##### T5 completion (2026-07-23-2235)

User authorized T5 for exact candidate SHA-256 `9cd10cb1c6ddfea3ef4e13808e08042877b5e9775ec32431523bea63ed06b66b`, IDs `014c8965ebc7` and `26035151aad9` only.

**Preconditions (matched):** plan at T5 start `d90984fa37cd0478bfb5f60e48223c5a3ad844303357c057bca88bd49ded3aad`; candidate bytes/hash immutable; living MANIFEST `1ddc4ac63464a7cba632b00bafd1250063ad5f62a20725cd6cb1d35daebc0987`; both approved artifact/content hashes matched living rows; fresh fetch of both canonical URLs returned HTTP 200 with effective content hashes equal to approved living hashes (same-hash; no concurrent drift); neither URL is aggregate/inaccessible.

**Pre-write snapshots (SHA-256):** TOPICS `b3cff36de6d2f8c8848719348a0d0aa588664947bfb5fac4865cf7ede397e070`; RELATIONS `f26afc6fadc5b77a46c6165e02e7cb20d63b090f11d7b2aaea84efd3e8e9d763` (also under `tmp/…/t5-pre-snapshots/`).

| source_id | transition | before artifact SHA-256 | after artifact SHA-256 | content_hash (unchanged) | route | rewrite record |
|---|---|---|---|---|---|---|
| `014c8965ebc7` | same-hash | `1e2c9f7ec0dfc92c153b1734bee946ef6a37d1344d6c1ae80d32c46ad597ad50` | `a69a9cdb5a48ec5038a9d2d5baf52e634311980781ca2a98dd283d4b7c32f3cf` | `32d718cbf63db68a428c8b6ebfda763d2c4251e635e96572cde8bda02befb4bd` | `no-topic-match` | `rewrites/014c8965ebc7--1e2c9f7ec0df.json` |
| `26035151aad9` | same-hash | `29096f92b897d86ad7ec25d57c0a050d5ce36c8f3f48ad7c3c54d70bdaa39574` | `f5d62099d111212d444a487d82db9de2afc20c510394b42709c6547f19c11a96` | `4fb898bc6eaa1acfd07deb9274ead0ce190790b698b77fcd09d9443ef99c51b6` | `no-topic-match` | `rewrites/26035151aad9--29096f92b897.json` |

**Quality fixes (g0):** removed payload-unsupported claims that caused prior `quality_fail` (014c: RunPod-like off-site infra; 2603: PDF metadata Adobe InDesign/CreationDate). Both drafts pass seven-item checklist + `atlas_quality.validate_summary` with empty findings. No media/assets retained. No second revision required.

**Registry / topics:** `atlas_state.validate_documents` → 0 findings after both source+route reduces. Post TOPICS/RELATIONS byte-identical to pre-snapshots → `affected_topic_ids` union **[]**. Post MANIFEST SHA-256 `b8c193e0b5b2e84ce60a8cd2003299ade29f139b7470f8e9c35d7ed14256ec72` (dates last_checked/last_summarized → 2026-07-23; content hashes unchanged). Instance check: only prerequisite B (`missing todos/TODOs.md`).

**Not done here:** T6 refresh decision (none needed — empty affected set, but T6 still reports/validates formally); T7 run log/cleanup. Candidate `rewrite-manifest-v4.json` left immutable; no approved subset file created.

### T6. Phase 4 — validate and topic decision gate

1. `atlas_state.py validate` → zero findings.
2. `atlas-instance.py check --name atlas` → per prerequisite A or B.
3. Report the **union of `affected_topic_ids`** from T5’s deterministic before/after TOPICS/RELATIONS diffs (covers supersede/reject, route flips, cache-only changes).
4. For each affected topic report: dirty?, pending edge IDs, contributing sources, whether topic was `current` before revisit.
5. **No automatic full refresh.**  
   Present the set and **ask** whether to refresh some/all. If not approved, complete with them dirty and state that `/atlas-answer` remains blocked for those topics until refresh.

##### T6 completion (2026-07-23-2242)

**Plan pre-hash (T6 start):** `b75c398a89061eed50d6f3d3a39d6536a6f34947f19eb0bb2061bee1971021e1` (matches post-T5 annotation).

**T5 re-verify (no writes):** rewrite records present for `014c8965ebc7` and `26035151aad9`; candidate `rewrite-manifest-v4.json` SHA-256 still `9cd10cb1c6ddfea3ef4e13808e08042877b5e9775ec32431523bea63ed06b66b`; living artifacts still match T5 after hashes (`a69a9cdb5a48…`, `f5d62099d111…`); content hashes unchanged; living MANIFEST SHA-256 still `b8c193e0b5b2e84ce60a8cd2003299ade29f139b7470f8e9c35d7ed14256ec72`.

**Validate:** `atlas_state.py validate` (API + CLI JSON bundle) → `findings: []` / `ok: true` (count **0**).

**Instance check:** `python3 scripts/atlas-instance.py check --name atlas` → fails only prerequisite B: missing `vault://atlas/todos/TODOs.md` (seed path). No other findings.

**Affected topics (independent recompute):**  
- Pre TOPICS SHA-256 `b3cff36de6d2f8c8848719348a0d0aa588664947bfb5fac4865cf7ede397e070`  
- Post TOPICS SHA-256 `b3cff36de6d2f8c8848719348a0d0aa588664947bfb5fac4865cf7ede397e070`  
- Pre RELATIONS SHA-256 `f26afc6fadc5b77a46c6165e02e7cb20d63b090f11d7b2aaea84efd3e8e9d763`  
- Post RELATIONS SHA-256 `f26afc6fadc5b77a46c6165e02e7cb20d63b090f11d7b2aaea84efd3e8e9d763`  
- TOPICS.md and RELATIONS.md **byte-identical** pre-snapshot vs living; topic-row diffs `[]`; edge-row diffs `[]`.  
- **`affected_topic_ids` union: `[]`** (matches T5 rewrite records and T5 completion).  
- Per-topic dirty/pending/contributors/pre-freshness: **N/A** (empty set).

**Refresh decision:** **none / not applicable** — no topics affected by T5; no refresh required or approved. `/atlas-answer` is not newly blocked by T5 (pre-existing dirty topics unchanged by this campaign).

**T7 still blocked:** durable run log, cleanup approval, temp delete, and plan archive remain open; Status stays `IN_PROGRESS`.

### T7. Durable run log, cleanup approval, archive

**Durable report path (only shape allowed):**

```text
vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-21--living-source-quality-revisit.md
```

Frontmatter:

```yaml
schema_version: 1
note_type: source-acquisition-run
managed_by: atlas
started: "..."
completed: "..."
trigger: "manual"
query_or_watchlist: "living source quality revisit"
created_sources: 0
skipped_duplicates: 0
coverage_notes: "<pass_current / no-write, quality_fail, source_changed, hash_baseline_migration, rewrite, blocked_* counts — pass_current is not a duplicate>"
```

`skipped_duplicates` is always `0` for this revisit (pass/no-write sources are **not** duplicates). Record pass/no-write counts only in `coverage_notes` and the report body.

Body sections: frozen cohort; capture/review scope; quality failures; source changes; hash-baseline migrations; rewrites; blocked/unsupported/concurrent rows; evidence downgrades prevented; affected/dirty topics; exact hash-bound disposition indexes; sources not model-reviewed and why; residual risk.

Archived **product** plan Completion Summary keeps only: report path + SHA-256 + aggregate counts — **not** hundreds of living IDs.

**Cleanup gate (mandatory):**

1. Present durable report path/hash, deterministic temp-root directory digest, blocked/deferred counts, and confirmation that no still-needed envelope exists only under temp.
2. Obtain **explicit cleanup approval**.
3. Delete exactly:  
   `vault://atlas/tmp/source-quality-revisit-2026-07-21/`
4. Verify absence.
5. Append `## Completion Summary` to this plan with the durable report path/SHA-256, aggregate disposition/rewrite counts, material residual risks, and cleanup approval/result. Do not copy hundreds of source IDs into the plan.
6. Check T7 and every remaining done criterion, set plan Status to `DONE`, then move it atomically to `.agents/plans/archive/`.

##### T7 pre-cleanup gate (2026-07-23-2254)

- T6 was independently accepted against plan SHA-256 `21901810f11ce90e0dbd13bfcc328b9547a0dfd353f4a2b17fe067419bf1ecf9`; registry validation remained clean and instance check remained prerequisite-B-only.
- Durable report: `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-21--living-source-quality-revisit.md` — SHA-256 `6c59c3352878fbac8b43610999d0ec87a3460b40da96678fd14d16928a4bd1b4` (9,188 bytes).
- Aggregate final authority: 503 rows; three `pass_current`; two approved `quality_fail` rows rewritten `same-hash`; 266 `blocked_evidence_regression`; 11 `blocked_fetch`; 221 `hash_baseline_incomparable`; zero approved `changed-hash`; zero affected topics.
- Temporary root digest for `vault://atlas/tmp/source-quality-revisit-2026-07-21/`: `d5faf615f40ad6e5cdd0b56069f7b0e92822fa1a6fc0595e3986cf0377c5df60`, computed as SHA-256 over relative-path-sorted records `D\0path\n`, `F\0path\0size\0sha256\n`, and `L\0path\0target\n`. Closure: 3,282 directories, 20,161 regular files, zero symlinks, 1,169,266,405 file bytes, and no special entries.
- Living dependency scan found no source, registry, topic, product contract, or framework snapshot dependent on the temp root; only this durable report contains provenance references to paths scheduled for deletion.
- **Cleanup blocker:** no persisted `atlas_source` event record or transaction attempt (`intent.json`, `prepared.json`, terminal `applied.json` / `no-op.json`) exists for either T5 rewrite anywhere under `vault://atlas/`. The two outcome records and pre-write snapshots prove observed final-state consistency but do not reconstruct required pre-write crash-recovery provenance.
- No retroactive transaction record was fabricated. Because the temp root contains the only T5 pre-write snapshots and evidence available to investigate that process nonconformance, the required “no still-needed envelope exists only under temp” confirmation is not currently true.
- Cleanup is not approved; no temp byte was deleted. T7 remains unchecked, plan status remains `IN_PROGRESS`, and archival is blocked pending the user’s explicit disposition of this exception.

##### T7 transaction-provenance investigation (2026-07-23-2254)

- The user explicitly chose **retain and investigate**; cleanup approval was withheld.
- Exhaustive vault checks found no T5 source/route event record, transaction directory, `intent.json`, `prepared.json`, progress record, or terminal record. `t5-work/` is empty, and the two rewrite outcome records do not bind event/evidence/checklist/manifest/transaction hashes.
- No file beneath the temporary root matches either pre-rewrite artifact SHA-256, so exact artifact backup bytes are unavailable. The retained pre-snapshots cover `MANIFEST.md`, `TOPICS.md`, and `RELATIONS.md` only.
- Read-only deterministic replay from those registry snapshots applied both exact `source-upsert` events and their empty `no-topic-match` `route-upsert` events. Every reducer call returned zero findings; replay produced current `MANIFEST.md` SHA-256 `b8c193e0b5b2e84ce60a8cd2003299ade29f139b7470f8e9c35d7ed14256ec72` byte-for-byte and preserved TOPICS `b3cff36de6d2f8c8848719348a0d0aa588664947bfb5fac4865cf7ede397e070` plus RELATIONS `f26afc6fadc5b77a46c6165e02e7cb20d63b090f11d7b2aaea84efd3e8e9d763`.
- Final state is valid, but the required historical crash-recovery protocol cannot be recreated truthfully. Retroactive transaction records would fabricate pre-write timing, backups, connector acknowledgements, and terminal state, so none were created.
- The durable report was updated with this finding: SHA-256 `611a53de50e5f677b45f956bbffc3415cfcbec60e5928e51d0ee5f455fd826e6` (10,138 bytes). Temporary-root digest remains `d5faf615f40ad6e5cdd0b56069f7b0e92822fa1a6fc0595e3986cf0377c5df60`.
- Plan SHA-256 before recording this investigation: `37461e8dabddc182445d51fd77af3c628d546d7759af92b9b2777c277741e67b`.
- No cleanup occurred. T7 remains unchecked, status remains `IN_PROGRESS`, and the active plan stays unarchived pending a later exact cleanup decision.

## Critical anchors

| Anchor | Role |
|---|---|
| `.agents/ARCHITECTURE.md` | Canonical text-only source, inaccessible-link, and aggregate-page scope invariants |
| `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` | Exact source/evidence/reducer schemas |
| `.agents/skills/atlas-core/assets/source-summary-quality-guide.md` | High-signal text drafting and seven-item quality contract |
| `.agents/skills/atlas-core/assets/source-summary-template.md` | Text-only Markdown artifact shape |
| `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` | Flexible positive/near-miss calibration cases |
| `.agents/skills/atlas-source/SKILL.md` | Concise open → clarify-if-aggregate → draft → validate → write workflow |
| `scripts/atlas_quality.py`, `scripts/atlas_source.py` | Deterministic text/hash validation and source reduction |
| `tests/test_atlas_quality.py`, `tests/test_atlas_source.py` | Permanent regressions for observed false positives |
| Deleted predecessor campaign root | Historical 503-row freeze and T4L indexes; terminal digest/outcome preserved in the durable report |
| Deleted T4V4–T4V9 evidence | Historical negative findings only; never direct approval authority; deletion permanently removed the retained forensic bytes under explicit acknowledgment |
| `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-21--living-source-quality-revisit.md` | Durable aggregate outcomes, final-state replay, permanent provenance exception, terminal cleanup result, and archive destination |
| `vault://atlas/summaries/sources/MANIFEST.md` + living artifacts | Optimistic targets only after exact T4.5 approval |

## Locked decisions

- Stop the exhaustive verification line at T4V9. No T4V10/T4V11 and no productized mutation campaign.
- T4P precedes the one lean T4L review so time spent improves future ingestion even if the cohort path is rejected.
- Source summary artifacts and their retained evidence are text-only. Canonical/source URLs remain textual fields; media/assets are never downloaded into or kept by Atlas source-summary state.
- Text extracted transiently from HTML, Markdown, or text-bearing documents is allowed; binary/media-only or insufficient-text links halt without a source write.
- Aggregate-page handling is a concise model-guided interaction, not a hard-coded classifier: ask page-only versus expanded child sources only when the page primarily indexes substantive child resources.
- Child expansion uses the normal `atlas-source` path per URL; no custom scraper, aggregate identity, provider branch, or hidden recursive crawl.
- The seven-item checklist remains high-level and evidence-bound. No fixed length, exact prose, similarity score, weighted score, or mandatory calibration.
- T4L validates actual rows plus representative regressions at product interfaces. It does not seek exhaustive family × pointer mutation coverage.
- T4L receives one execution/review attempt. A tooling/review incompleteness triggers the separate ten-source plan; expected no-write rows do not.
- OMP/Grok comparative work, if triggered, refines provider-neutral durable artifacts. OMP output is a quality reference, while the canonical source text remains factual authority.
- No full-library regeneration occurs in this plan. After a successful ten-source fallback, the user separately decides whether Grok regenerates all sources.
- No automatic all-topic refresh, source delete, new registry backend, source schema migration, or scaffold media surface.

## Verification / Done criteria

- [x] Inventory freeze + baseline recorded; prerequisite B applied.
- [x] Phase-1 covers all 503 frozen living artifacts with the exact status enum.
- [x] T4V5 mechanically emitted helper/capture/classification/review/handoff artifacts, then post-completion audit rejected its approval authority; its bytes remain preserved as negative evidence.
- [x] T4V6 mechanically emitted its helpers, 503-row authority, selected-files index, classifications, six review reuses, A–E handoffs, and a zero-finding final-verifier result; all bytes remain frozen.
- [x] Post-completion mutation reproduction proves the T4V6 verifier accepts impossible candidate/final output hashes with `findings: []`; T4V6-E is rejected as approval authority.
- [x] T4V6 recorded the five known invalid selected source IDs, 487 reuse/16 terminal split, pre-review 265/11/221/6, and final 265/11/221/3/3; these remain assertions for a successor to independently re-establish.
- [x] T4V7-A/B mechanically emitted its three helpers, contract, self-test, candidate, adversary, verification, and final handoff; fresh baseline and 679-mutation runs were green and root-identical.
- [x] Separate external review reproduced T4V7 final-wrapper, malformed-acceptance, and substring-diagnostic false positives; T4V7 external acceptance and T4.5 authority were rejected.
- [x] Approved plan amendment defines T4V8's nonrecursive authority, split authorship, eight-path write set, declarative schemas, exact-diagnostic mutation families, pre/post acceptance phases, and separate T4.5 gate.
- [x] T4V8 verifier/adversary were authored by distinct sessions, self-tests passed, the baseline verifier returned zero findings, and the coordinator froze its contract.
- [x] T4V8 pre-accept adversary caught 3685/3688 mutations and froze `findings: ["uncaptured:3"]`; the three exact misses were the already-`pass_current` review IDs.
- [x] Static review confirmed T4V8 no-op dispatch, family/strategy mismatch, hard-coded disposition/fallback, incomplete recursive/living coverage, constant-true enumeration, and constant-true mutation-set gate; acceptance/post reports were correctly not created.
- [x] The first unsealed T4V9 rehearsal preserved every Atlas byte, passed self-tests/baseline/oracle/sentinel-only checks, and correctly rejected full runs at 1027/7365 then 6715/7365 rather than greenwashing 650 uncaught rows plus 34 harness failures.
- [x] The unsealed T4V9 review identified reusable repair requirements: real recursive schema diagnostics, universal byte-binding diagnostics, pre-enumeration applicability, exact complete-matrix equality, declared product-dependency hashes, and no hard-coded workstation imports.
- [x] T4P architecture/contracts/template/validator/skill agree on text-only source summaries, no retained media/assets, inaccessible/insufficient-text halt, and concise aggregate-page scope clarification.
- [x] Product tests cover exact text hashes, projections, media/binary rejection, no-write transitions, and every durable prior false-positive family without exact-prose assertions.
- [x] Read-only T4P smokes prove inaccessible-link notification and one concise aggregate page-only/expand question; product hashes and bound snapshot are recorded.
- [x] T4L validates exactly 503 actual rows with current product hashes and classifies every row as eligible or exact no-write.
- [x] Fixed representative regressions pass; no combinatorial mutation matrix, custom verifier helper, or hidden fallback remains.
- [x] Independent T4L review binds both exact reports and returns `ACCEPTED_FOR_T4_5`; otherwise the triggered successor-plan specification is materialized and T4.5 remains closed.
- [x] T4.5 manifest bytes contain only accepted T4L eligible rows and their SHA-256 is explicitly approved before any living mutation.
- [x] T5 writes only approved rows through the text-only path; inaccessible, aggregate-ambiguous, non-text, or concurrent rows stop without silent rebase.
- [x] Registry validation is clean; instance check matches prerequisite A/B.
- [x] Affected topics are reported via TOPICS/RELATIONS before/after diff; refresh decision recorded.
- [x] Durable run log is written; temp root deleted only after cleanup approval; plan archived.

## Assumptions and fallbacks

- T4V4–T4V8 Atlas bytes remain frozen negative evidence. T4V9 created no Atlas byte and is retired.
- Historical media/raw captures may remain under the existing temp root until the separately approved T7 cleanup, but T4P/T4L/T5 never select, copy, or require them.
- “Text-only” permits Markdown prose and textual URLs. It forbids embedded/downloaded images, audio, video, screenshots, archives, PDFs, and other binary assets in source-summary state; a PDF may be read only through transient extracted text.
- “Aggregate page” means a page whose primary utility is its catalog/list of child resources and whose child pages hold the substantive content. Link count alone is not the test.
- A supplied page with enough standalone text is summarized directly unless the user asks for expansion. The agent asks only when page-only versus child expansion materially changes scope.
- An unavailable link, authentication wall, fetch error, empty body, media-only source, or text too thin for faithful summary is a terminal no-write for that invocation and a concise user notification.
- T4L `eligible: false` is not an incomplete run when the row has an exact supported no-write reason. Incomplete means missing coverage, unexplained findings, broken product behavior, or reviewer uncertainty.
- Prerequisite B remains: final instance check may report only the known missing `vault://atlas/todos/TODOs.md`.

## Triggered successor plan: ten-source cross-harness calibration

Materialize a new dated repository plan only if T4L-C returns `REJECTED_INCOMPLETE`. The new plan must not continue the 503-row verifier campaign. Its end state is a lean, provider-neutral Atlas framework whose Grok CLI 4.5/high summaries are consistently comparable in high-signal quality to fresh OMP `gpt-5.6-sol:xhigh` references on ten substantial text sources.

Required design:

1. Select exactly ten accessible, sufficiently rich, text-first sources across different domains and source shapes. Exclude thin pages, media-dependent sources, inaccessible links, and unresolved aggregate pages. Freeze canonical URLs and exact extracted text hashes.
2. Split six development sources and four holdout sources before generation. Do not use holdout gaps to tune the framework until the final evaluation.
3. From the app working directory, use the user's normal configured Grok CLI 4.5/high and OMP `gpt-5.6-sol:xhigh` harnesses. Create no patched/custom binary, transport wrapper, campaign harness, or provider-specific product prompt.
4. Generate one OMP reference and one Grok candidate per source from the identical source-only text envelope. Every invocation starts in a fresh context with no prior artifact, comparison, framework-edit rationale, or sibling-source prose.
5. Compare each pair against canonical source text using flexible high-level dimensions: primary contribution, material mechanics/examples, source support, consequential limits/uncertainty, factual fidelity, signal-to-noise, and text-only compliance. Use `meets|needs-refinement` plus concise evidence locators; do not score exact wording, style, length, or semantic similarity.
6. Treat OMP as a quality reference, not factual authority. A reference omission or unsupported claim is not copied into the framework; canonical source text wins.
7. Promote a framework change only for a recurring gap across at least two development sources or one severe correctness/evidence-boundary failure. Update the narrowest durable owner and add one positive plus one near-miss regression; never add source-, domain-, or provider-specific prompt branches.
8. After each durable change, start fresh Grok contexts and rerun only affected development sources. When development sources meet the rubric, run all four holdouts once. Any holdout-driven framework change requires one final fresh run across all ten.
9. Finish only when all ten pass deterministic product gates and an independent reviewer finds no material high-signal deficit versus the reference/source under the flexible rubric. Preserve artifacts/reports needed to prove the result; do not retain source media/assets.
10. Halt and present framework hashes, ten-source outcomes, remaining risks, and the proposed full-library regeneration procedure. Grok regeneration of all living sources requires a new explicit user approval and is not part of that calibration plan.
## STOP conditions

- Any T4V7/T4V8/T4V9 artifact is promoted as approval authority or any T4V9 Atlas path is created.
- T4P persists or requires media/assets, adds a provider/domain-specific scraper, introduces a brittle aggregate-page classifier, or duplicates source/effective-hash logic.
- `atlas-source` falls back to old prose, model priors, sibling sources, media captions, or cached wrappers when the canonical link/text is unavailable.
- An aggregate page is recursively expanded without the user's page-only/expand choice, or a normal substantive page triggers needless interrogation.
- Product rules add fixed length, exact prose, citation count, similarity score, weighted threshold, mandatory calibration, or provider-specific quality expectations.
- T4L creates a helper/oracle/adversary, enumerates schema-family × pointer mutations, invokes a model, retrieves new evidence, changes living state, or runs a repair iteration after review.
- T4L omits a source ID, treats an unexplained finding as no-write, accepts unbound product/report bytes, or widens eligibility from historical assertions without current product proof.
- T4.5 starts without accepted exact T4L reports and separate user authorization, or approval does not bind exact manifest bytes/IDs.
- T5 retains a media/asset file, writes an inaccessible/insufficient/aggregate-ambiguous source, or no longer matches its approved text/concurrency hashes.
- If the ten-source fallback is triggered: either harness receives prior comparison context, a custom binary/wrapper is introduced, OMP prose overrides source truth, framework rules overfit one source/provider, holdouts leak into tuning, or full-library regeneration begins without separate approval.
- Any product architecture change is not propagated through atlas-core, owning skill, behavioral tests, and the approved framework snapshot sync.

## Non-goals

- Repair or certify every historical T4 verifier artifact
- Exhaustive mutation coverage
- Rewrite or regenerate all 503 sources in this plan
- Persist or summarize media assets
- Build a generic-page scraper or recursive crawler
- Add provider-specific product prompts or binaries
- Make calibration mandatory
- Match exact OMP prose, style, length, or scoring
- Auto-refresh every dirty topic
- Productize hard delete

## Completion Summary

The 503-source revisit completed its lean productization, accepted cohort review, two exact same-hash rewrites, registry validation, durable reporting, and later Plan-A-authorized cleanup.

**Delivered**
- Durable report: `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-21--living-source-quality-revisit.md` — terminal revision `sha256:a10401506d1815a260a7c6eaf4d47d2be7ab9dd2dc8f57f605b969bc27764877`.
- Final cohort authority: 503 rows; three `pass_current`; two approved `quality_fail` rows rewritten `same-hash`; 266 `blocked_evidence_regression`; 11 `blocked_fetch`; 221 `hash_baseline_incomparable`; zero approved changed-hash rows; zero affected topics.
- T4V7–T4V9 executed work is terminal rejected/negative evidence. Acceptance and post-accept steps that were never reached are explicitly abandoned, not accepted.
- Registry validation remains zero-finding. The instance check retains only prerequisite B: missing `vault://atlas/todos/TODOs.md`.

**Cleanup and residual risk**
- The user later approved deletion with structured acknowledgment of permanent loss. Immediate preflight matched `sha256:17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a`; qualified `vault.delete_tree` returned `deleted` and witnessed original/quarantine absence.
- This permanently removed the only remaining forensic traces for two rewrites whose required transaction records and exact artifact backups never existed. The provenance gap cannot be reconstructed and no reconstruction was fabricated. Durable outcomes and final-state replay remain in the report.
- Canonical T2 recovery remains separately retained by decision at `sha256:877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1`.

**Archive destination**
- `.agents/plans/archive/2026-07-21-1613_living-source-quality-revisit.md`
