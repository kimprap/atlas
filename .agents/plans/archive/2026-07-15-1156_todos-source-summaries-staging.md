# TODOs bulk source-summary staging (Atlas-quality pass 1)

**Datetime**: 2026-07-15
**Scope**: Extract every link from `vault://atlas/todos/TODOs.md`, normalize/dedupe canonical URLs, and generate Atlas source-summary artifacts into a dedicated staging tree using the refined `/atlas-source` quality workflow — without writing living vault summaries, registries, or topics.
**Summary**: Run a high-volume, context-neutral source-ingestion campaign over the TODOs corpus with `grok-4.5(high)` parent + subagents, shadow MANIFEST dedupe, and hard quality gates; hold all artifacts under the bound instance’s **vault-local** `tmp/` tree for a later pass-2 review after quality-hardening (T4–T6) lands, then promote into `vault://atlas/summaries/`.
**Status**: DONE

## Context

- Quality-hardening plan [`.agents/plans/2026-07-15-0004_atlas-t5-quality-hardening.md`](.agents/plans/2026-07-15-0004_atlas-t5-quality-hardening.md) is mid-flight (T1–T3 complete; T4–T6 open). That work hardens context-neutral drafting, `scripts/atlas_quality.py`, calibration fixtures, reducer discipline, and adoption/stability gates. **This plan consumes those contracts as the quality bar**; it does not re-author product skills or complete T5 topic refresh.
- Living TODOs inventory lives only on the bound instance at `vault://atlas/todos/TODOs.md` (~662 lines). Approximate inventory after normalize+dedupe (host-resolved snapshot):
  - ~978 raw URL occurrences → ~483–477 unique after normalization (excluding obvious bare-filename autolinks such as `http://claude.md`)
  - Domain mix (approx.): GitHub ~244, X ~160, other web ~70+, YouTube ~5, arXiv ~1
  - Overlap with living `vault://atlas/summaries/sources/MANIFEST.md`: only a handful of URLs already ingested; nearly all TODOs links are new
- Framework rule: source semantic drafting is **context-neutral** and write-gated by deterministic validation + the seven-item acceptance checklist. Living registry mutation requires `atlas-route` + `scripts/atlas_state.py`. **Pass 1 deliberately avoids living registry/topic writes** so in-flight refinements and the later human review are not polluted.
- Earlier quality experiments used OS host staging under the system `/tmp/…` tree. **This campaign does not**: OS `/tmp` is wiped on reboot and is not bound to the instance. Staging lives under the vault instance’s own `tmp/` directory so artifacts survive restarts and stay next to the living vault without entering `summaries/`.

## Decisions

1. **Pass 1 is staging-only, on vault-local `tmp/` (not OS `/tmp`).**
   - **Logical path (preferred in skills/reports):** `vault://atlas/tmp/todos-source-summaries-2026-07-15/`
   - **Host resolve for the bound `atlas` instance (explicit):**
     `…/vault/instances/atlas/tmp/todos-source-summaries-2026-07-15/`
     e.g. `/Users/kim/dev/atlas/vault/instances/atlas/tmp/todos-source-summaries-2026-07-15/`
   - This is instance-owned ephemeral campaign state under the vault root. It is **not** product `scaffold/`, **not** living `summaries/`, and **not** the OS root temporary directory (`/tmp` on macOS/Linux).

   All generated source artifacts, shadow MANIFEST, run logs, ledgers, and envelopes write under:

   ```text
   vault://atlas/tmp/todos-source-summaries-2026-07-15/
     inventory/          # extracted + normalized URL tables
     envelopes/          # per-source evidence bundles (JSON)
     artifacts/          # source-summary Markdown (Atlas template)
     manifest/MANIFEST.md
     runs/               # batch/run reports
     calibration/        # calibration run evidence
     ledger/             # status per canonical_url (pending|done|skip|failed)
     prompts/            # frozen subagent batch prompts (optional)
   ```

   Do **not** write to `vault://atlas/summaries/**`, `RELATIONS.md`, `TOPICS.md`, living `MANIFEST.md`, or modify `TODOs.md`. Do **not** use `/tmp/…` (OS temp) for campaign artifacts.

2. **Pass 2 is out of this plan’s execution body** but is a named handoff: after quality-hardening T4–T6 (or an explicit “contracts frozen” signal), re-review every staged artifact against the final contracts, then promote via real `/atlas-source` into the living vault (with living-manifest dedupe and `/atlas-route`).

3. **Canonical URL normalization before any fetch or identity.** Apply once, store both `raw_url` and `canonical_url`. Identity = `source_id = sha256(canonical_url)[:12]` (Atlas convention). Dedupe authority for pass 1 = staging `MANIFEST.md` only (also consult living MANIFEST as **read-only** to mark `already_in_vault` for pass-2 priority, not as a skip of staging if the user wants a fresh quality sample — default: **still stage** if living artifact predates the refined quality bar, flag `living_overlap=true`).

4. **Normalization rules (preserve destination):**
   - Scheme/host lowercase; strip trailing `/` on non-root paths; drop URL fragment `#…`
   - Map `twitter.com` / `mobile.twitter.com` / `www.x.com` → `x.com` (single host for identity)
   - Drop tracking query params: all `utm_*`; for X status/profile URLs drop integer `s=<digits>` only (share/source suffix). **Keep** other query keys (`t=`, video params, etc.) when removing them would change the resource
   - Do **not** expand GitHub repo roots into trees/blobs; one URL → one source (Atlas non-recursive rule)
   - Reject or quarantine bare-filename autolinks (`http://claude.md`, `http://vision.md`, …) unless they resolve to a real registered host after a HEAD/GET check
   - Repair only unambiguous markdown typos when the intended URL is adjacent (e.g. `h[ttps://…` → `https://…`); log every repair

5. **Workflow skill ownership (correct Atlas entrypoints):**
   | Role | Skill / command | Pass 1 use |
   |---|---|---|
   | Source fetch + draft + quality gates | `/atlas-source` → `skill://atlas-source` | **Required** for every new canonical URL |
   | Shared contracts | `skill://atlas-core` assets (template, quality guide, registry contracts, evals) | Read-only support |
   | Deterministic structural gate | `scripts/atlas_quality.py validate-summary` | **Required** before accepting an artifact |
   | Calibration | `scripts/atlas_quality.py validate-calibration` + `skill://atlas-core/assets/evals/source-summary-quality.json` | Once per harness/model/template version before first write |
   | Route into topics | `/atlas-route` | **Forbidden** in pass 1 (no living registry writes). Optional **shadow** routing notes only if written inside the staged artifact’s post-draft section without registry I/O |
   | Research / refresh / answer / index / migrate | `/atlas-research`, `/atlas-refresh`, `/atlas-answer`, `/atlas-index`, `/atlas-migrate` | **Out of scope** for pass 1 |
   | Read-only health on staging tree | `/atlas-audit` patterns via `atlas_quality.py` | Spot-check samples; not living-instance mutation |

6. **Model pin.** Parent orchestrator and **every** summarization subagent use **`grok-4.5` at high effort** (`grok-4.5(high)` / harness-equivalent high). Do not mix models in pass 1. Record model/effort only in run reports — never in semantic draft bodies.

7. **Parallelism.** Parent owns the ledger and merges results. Subagents receive a **closed batch** of pre-normalized canonical URLs (no TODOs file rewrite, no sibling drafts, no plan prose as evidence). Approximate batch sizing for context fit:

   | Kind | Est. unique | Batch size / subagent | Est. subagents |
   |---|---:|---:|---:|
   | `github_repo` (README-primary) | ~229 | 2–3 | ~80–110 |
   | `github_path` (blob/tree/docs) | ~15 | 2–3 | ~6 |
   | `x_status` (post/thread) | ~156 | 8–12 | ~15–20 |
   | `youtube` | ~5 | 2–3 | ~2 |
   | `web_other` / arxiv / docs | ~70+ | 3–5 | ~15–25 |
   | **Total** | **~477** | | **~120–160 subagents**, run in **waves of 8–16 concurrent** |

   Adjust batch size down when a single repo README is huge or multi-media; never share one evidence envelope across sources.

8. **Failure policy.** Fetch failure → still write a staged artifact with `coverage: failed|partial`, honest bounds, and ledger status `failed`/`partial`. Do not invent content from model priors. Transient network errors: one retry; then mark `retryable` for a later wave.

9. **No product/framework edits** in this plan unless a contract bug blocks all writes — then halt and open a fix under the quality-hardening plan rather than freestyle.

## Prerequisites (before first staging write)

1. Confirm bound instance check still passes: `python3 scripts/atlas-instance.py check`.
2. Confirm refined assets exist and are the intended bar:
   - `skill://atlas-source`
   - `skill://atlas-core/assets/source-summary-quality-guide.md`
   - `skill://atlas-core/assets/source-summary-template.md`
   - `skill://atlas-core/assets/evals/source-summary-quality.json`
   - `scripts/atlas_quality.py`
3. **Calibration gate (once):** parent runs every case in `source-summary-quality.json` through the active `grok-4.5(high)` lane and exact-validates with `python3 scripts/atlas_quality.py validate-calibration`. Any fail → **zero writes**. Record under `calibration/`.
4. Create the empty staging root at `vault://atlas/tmp/todos-source-summaries-2026-07-15/` (mkdir on the bound instance, not OS `/tmp`) and freeze the inventory snapshot (hash of `TODOs.md` + generation timestamp).

If quality-hardening later changes the template/rubric version mid-campaign: stop new waves, bump `template_version` in the ledger, and either re-calibrate + resummarize affected rows or mark them `stale_for_pass2`.

## Tasks

- [x] T0. Persist this plan under `.agents/plans/2026-07-15-1156_todos-source-summaries-staging.md`
  - completed 2026-07-15
- [x] T1. Inventory, normalize, dedupe, and classify all TODOs URLs into a staging queue
  - completed 2026-07-15
- [x] T2. Calibrate `grok-4.5(high)` once; initialize shadow MANIFEST + ledger
  - completed 2026-07-15
- [x] T3. Wave-dispatch summarization subagents (Atlas source workflow → staging only)
  - completed 2026-07-15 — 120 batches / 10 waves
- [x] T4. Parent merge, structural quality sweep, coverage report
  - completed 2026-07-15 — see `vault://atlas/tmp/todos-source-summaries-2026-07-15/runs/pass1-report.md`
- [x] T5. Pass-1 freeze + pass-2 handoff checklist (no living promotion yet)
  - completed 2026-07-15 — see `runs/pass2-handoff.md`

## Approach

### T1. Inventory, normalize, dedupe, classify

**Owner:** parent agent (read-only vs vault living content).

1. Read `vault://atlas/todos/TODOs.md` (or host resolve `…/vault/instances/atlas/todos/TODOs.md` via the active connector). Do not edit it.
2. Extract every `http(s)://…` token from Markdown links and bare URLs.
3. For each raw URL apply the normalization rules in Decisions §4; emit one inventory row:

   ```text
   inv_id | section_heading | raw_url | canonical_url | source_kind | host | living_overlap | status
   ```

   Persist `inventory/urls.tsv` + `inventory/urls.json` and a short `inventory/README.md` with counts.
4. Collapse to unique `canonical_url`. Keep `raw_urls[]` for audit (especially X `s=` variants).
5. Classify `source_kind` for template frontmatter: `repo|docs|article|thread|video|paper|other`.
6. Quarantine suspicious hosts to `inventory/quarantine.tsv` (require explicit parent decision before summarizing).
7. Optionally attach TODOs section headings as **non-evidence metadata** on the ledger only — never pass section labels into the semantic draft envelope.

**Verification:** unique count, X URLs with `s=` reduced to cleaned canonicals, no two ledger rows share a `canonical_url`.

### T2. Calibration + shadow registry

**Owner:** parent.

1. Run the static calibration suite once for `grok-4.5(high)` against `skill://atlas-core/assets/evals/source-summary-quality.json`; validate with `scripts/atlas_quality.py validate-calibration`. Halt on failure.
2. Seed empty staging files:
   - `manifest/MANIFEST.md` — same table shape as living source manifest, sequences starting at `1` **within the staging tree only** (do not continue living sequence numbers; pass 2 reassigns living `source_seq`)
   - `ledger/status.jsonl` — one line per canonical URL
3. Read living MANIFEST once (read-only) and mark `living_overlap` + living `source_id` when present.
4. Freeze product asset hashes used for the campaign (ARCHITECTURE, quality guide, template, atlas_quality.py) into `runs/campaign-meta.json`.

### T3. Wave-dispatch summarization subagents

**Owner:** parent orchestrates; subagents execute Atlas source procedure.

#### Subagent contract (every worker)

- **Model:** `grok-4.5` high effort only (`model` pin on `spawn_subagent`).
- **Capability:** full execute (fetch + write under vault-local staging root only: `vault://atlas/tmp/todos-source-summaries-2026-07-15/`). Prefer isolation when available so sibling drafts do not leak context.
- **Must load before drafting:**
  1. `skill://atlas-source` (primary checklist — treat as `/atlas-source` invocation)
  2. `skill://atlas-core/assets/source-summary-quality-guide.md`
  3. `skill://atlas-core/assets/source-summary-template.md`
  4. Explicit vault-local staging write-root (`vault://atlas/tmp/todos-source-summaries-2026-07-15/`) + batch URL list (pre-normalized)
- **Must not load as evidence:** TODOs file body, plan text, living topic answers, sibling artifacts, other batch items’ drafts, provider identity.
- **Per URL procedure (mirror atlas-source):**
  1. Confirm `canonical_url` not already `done` in staging ledger (dedupe).
  2. Fetch complete readable payload (README/docs/reader mode preferred; page omitted ranges; inspect meaning-critical media with pinned URLs).
  3. Build source-only evidence envelope JSON under `envelopes/<source_id>.json`.
  4. Draft artifact with schema v1 template into `artifacts/<YYYY>/<YYYY-MM>/<date>--<source_id>--<slug>.md`.
  5. Run `python3 scripts/atlas_quality.py validate-summary` against artifact + envelope; fix until clean.
  6. Run the **seven-item** acceptance checklist once over the same envelope+draft; any fail → revise that dimension and re-run both gates.
  7. **Only after semantic gates pass:** optional light Classification fields using **read-only** copy of living `VOCAB.md` if available — never create vocab/topics; put unknowns in `candidate_terms`. Set `routing_status: unrouted` for all pass-1 rows (no `/atlas-route`).
  8. Append/update staging MANIFEST row; append ledger `done|partial|failed`.
  9. Return a compact report: `canonical_url`, `source_id`, path, coverage, assessment tuple, gate status — **not** full prose (parent merges metadata).

#### Parent dispatch loop

1. Partition the queue into kind-aware batches (sizes in Decisions §7).
2. Launch waves of **8–16 concurrent** subagents (raise only if the host stays stable; lower on rate limits).
3. On subagent completion: merge MANIFEST/ledger atomically (file lock or single-writer parent); never let two writers append the same `canonical_url`.
4. On subagent crash: mark batch `retryable`, requeue unfinished URLs only.
5. Respect API/rate limits for X and GitHub: serialise within a subagent; jitter between waves.

#### Explicit non-goals for subagents

- No `/atlas-route`, `/atlas-research`, `/atlas-refresh`, `/atlas-answer`, `/atlas-index`, `/atlas-migrate`
- No living vault writes
- No rewriting TODOs
- No “improve” or product refactors

### T4. Merge and quality sweep

**Owner:** parent after all waves (or after each major wave checkpoint).

1. Recompute: queued vs done vs partial vs failed vs quarantine.
2. Structural sweep: every `done` artifact runs `validate-summary` again in batch (catch merge errors).
3. Spot semantic audit: sample **≥20** artifacts stratified by kind (repo/X/web/video) with the seven-item checklist; record failures in `runs/spot-audit.md`.
4. Dedupe audit: no duplicate `canonical_url` / `source_id` in staging MANIFEST; every X raw `s=` variant maps to one row.
5. Produce `runs/pass1-report.md`:
   - counts by kind and coverage
   - top failure reasons
   - living_overlap list
   - calibration + asset hashes
   - residual risks for pass 2

### T5. Pass-1 freeze and pass-2 handoff (document only)

Do **not** promote in this plan. Handoff checklist for a future plan/session:

1. Wait until quality-hardening **T4–T6 complete** (or explicit freeze of template/rubric versions).
2. Re-run calibration if product assets changed.
3. For each staged row: open the link, compare artifact vs refined bar, fix via staged `--resummarize` procedure or delete and regenerate.
4. Promote survivors with real `/atlas-source` against living vault (connector writes):
   - living MANIFEST dedupe by `canonical_url`
   - allocate living `source_seq`
   - then `/atlas-route` only when promotion is intentional
5. Keep the vault-local staging tree until promotion reconciliation finishes; then delete `vault://atlas/tmp/todos-source-summaries-2026-07-15/` (and empty parent `vault://atlas/tmp/` if unused) only after an explicit user OK. Do not leave campaign rows under living `summaries/`.

## Critical files / assets (read; staging writes only under vault-local `tmp/`)

| Path | Role |
|---|---|
| `vault://atlas/todos/TODOs.md` | URL inventory source (read-only) |
| `vault://atlas/summaries/sources/MANIFEST.md` | Living dedupe reference (read-only in pass 1) |
| `vault://atlas/ARCHITECTURE.md` | Framework invariants |
| `.agents/skills/atlas-source/SKILL.md` | Primary ingestion procedure |
| `.agents/skills/atlas-core/assets/source-summary-quality-guide.md` | Envelope, concision, 7-item checklist |
| `.agents/skills/atlas-core/assets/source-summary-template.md` | Schema v1 artifact shape |
| `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` | Calibration fixtures |
| `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` | Identity/hash/manifest rules |
| `scripts/atlas_quality.py` | `validate-summary` / `validate-calibration` |
| `.agents/plans/2026-07-15-0004_atlas-t5-quality-hardening.md` | Quality-bar context; do not complete T5 here |
| `vault://atlas/tmp/todos-source-summaries-2026-07-15/**` | **Only** write surface for pass 1 (vault-local `tmp/`, not OS `/tmp`) |

## Reuse

- Campaign layout idea from [`.agents/plans/2026-07-14-1538_atlas-source-summary-quality.md`](.agents/plans/2026-07-14-1538_atlas-source-summary-quality.md), **relocated** from OS `/tmp/…` to durable vault-local `vault://atlas/tmp/…`.
- Context-neutral envelope + gates from quality-hardening T2 / current `atlas-source` skill.
- Identity: `source_id = sha256(canonical_url)[:12]` per contracts/template comments.
- Subagent isolation + model pin via `spawn_subagent` (`model: grok-4.5`, high effort).

## Verification

1. Staging root exists only under `vault://atlas/tmp/todos-source-summaries-2026-07-15/` (host: `vault/instances/atlas/tmp/…`); nothing campaign-owned under OS `/tmp`. App package `git status` clean of unintended product edits; living `summaries/` registries unchanged.
2. `inventory/urls.json` unique `canonical_url` count matches ledger rows; X `s=` stripped where applicable; destination still resolves to the same status/repo.
3. Calibration directory shows all eval cases passed for `grok-4.5(high)` before first artifact write.
4. Every `done` artifact:
   - matches template schema v1 keys
   - passes `python3 scripts/atlas_quality.py validate-summary`
   - has a matching envelope file
   - contains no plan/TODOs/sibling/provider leakage in semantic sections
5. Staging MANIFEST has unique sequences and unique canonical URLs; no living `RELATIONS.md` / `TOPICS.md` / living MANIFEST mutations.
6. `runs/pass1-report.md` lists remaining `failed`/`partial`/`quarantine` with reasons.
7. TODOs file byte-identical to campaign start.

## Completion evidence

Closed 2026-07-19. Pass-1 remains a staging-only campaign; living promotion and all semantic repairs are owned by `.agents/plans/2026-07-16-1211_atlas-source-summary-cross-harness.md`.

- Frozen inventory: 477 accepted manifest rows, 478 artifacts, and 478 evidence envelopes. The extra artifact/envelope pair is failed non-manifest source `fd3fe07e32f0`; the five quarantined rows have no promotable pair.
- Complete deterministic revalidation: 478/478 artifact-envelope pairs parsed, 478 unique source IDs on both sides, exact artifact/evidence set equality, and zero validator findings. Evidence: `runs/closure/deterministic-sweep.json` (`sha256:d41ce491534dfc991252f508518d3b3c8052fd2faf40ed43244da0c445b6f6bc`).
- Frozen, stratified 30-source semantic audit: 30/30 transport-clean and schema-valid; 6 eligible without repair; 24 retained as `repair-in-T8` findings for the successor plan. Evidence: `runs/spot-audit/manifest.json` (`sha256:57a09d3eb0e534a2a6a899e3875417997396d46e46e21231b3921770081c7614`) and `runs/spot-audit/summary.json` (`sha256:feddfcb1284e8a3f000d4397e16f64f4fc34cbb62acc2b3e622041421541a59e`).
- Closure anchors: `runs/campaign-meta.json` (`sha256:a2074fdad4e815126d58758cae94177863740cf9e6a45aee1ea1e96515739a76`), `manifest/MANIFEST.md` (`sha256:682e92d1119edec755387ad86e1db150afe7363ccd065d4f6ce9ee6b5230bc6c`), and `runs/pass1-report.json` (`sha256:734a903fec5171fc4d7ae7d9a3c10662691188b0f6c0ce093f858d892673661b`).
- Pre-change closure snapshot: `runs/closure/state-snapshot.json` (`sha256:261e8ec79a438d5e7b7738e2928fe5dd8019bf05d07124c99f1e76e4dcdc884b`) records the exact eight governing contract/tool hashes, current living registry hashes, original campaign-start hashes, and `living_drift: true` for all three registries. These were preserved as concurrent living changes; closure performed no rollback.
- Proof commands: the complete pair sweep invoked `scripts/atlas_quality.py validate-summary` for every artifact/envelope input and produced the hashed zero-finding report above; `python3 scripts/atlas-instance.py check` returned `check OK: instances: atlas | product_owned entries: 1 | seed_once templates: 8` before successor-plan T2 changed the product-owned architecture contract.
- The frozen staging tree is intentionally retained. No living source, registry, or topic write is part of this closure.

## Risks / mitigations

| Risk | Mitigation |
|---|---|
| ~120–160 subagents / rate limits | Waves of 8–16; per-host pacing; retry ledger |
| Quality contracts change mid-flight | Freeze asset hashes; stop waves on template drift; mark `stale_for_pass2` |
| Context leakage via batch prompts | Closed URL list only; no TODOs body; isolation when available |
| Huge GitHub READMEs / monorepos | Smaller batches; `coverage: partial` with exact missing bounds; no recursive child expansion |
| X / login walls | Honest `failed`/`partial`; no invented thread text |
| Accidental living vault writes | Subagent prompt allows writes only under `vault://atlas/tmp/todos-source-summaries-2026-07-15/`; forbids `summaries/` registry mutation and OS `/tmp`; parent verifies living MANIFEST/RELATIONS/TOPICS mtime/hash unchanged |
| Scale underestimation | Report checkpoints every wave; user may pause after any wave |

## Out of scope

- Completing quality-hardening T4–T6 or applying factor edges / topic refresh
- Living `/atlas-route`, `/atlas-research`, `/atlas-refresh`, topic answers
- Editing product skills/architecture unless blocked (then halt)
- Deleting or rewriting TODOs entries
- Pass-2 promotion into living summaries (handoff only)

## Execution note (when approved)

1. Save a dated copy under `.agents/plans/` if not already present.
2. Run T1→T2 serially, then T3 in waves, T4 continuous, T5 as freeze doc.
3. Prefer one long-lived parent session owning the ledger over disconnected parallel parents.
