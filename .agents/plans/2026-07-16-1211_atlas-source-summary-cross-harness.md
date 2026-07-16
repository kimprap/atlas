# Atlas Source-Summary Cross-Harness Evaluation and Promotion Plan

**Datetime**: 2026-07-16-1211
**Scope**: Atlas Source-Summary Cross-Harness Evaluation and Promotion Plan
**Summary**: Mirrored OMP plan artifact for Atlas Source-Summary Cross-Harness Evaluation and Promotion Plan.
**Status**: PENDING


**Datetime:** 2026-07-16-1222  
**Scope:** Close the Grok pass-1 staging campaign; harden canonical URL/source identity; compare 30 independently generated Atlas source summaries from OMP GPT-5.6-sol xhigh and Grok 4.5 high; apply only demonstrated provider-neutral refinements; promote the accepted 477-source staging set without refetching unchanged evidence; reconcile and remove temporary state.  
**Summary:** Freeze one stratified 30-source evidence cohort, render byte-identical tool-free prompts, run separate OMP and Grok lanes, validate and blind-review every pair against the seven-item Atlas rubric and the staged baseline, then use a deterministic source-upsert reducer to promote accepted artifacts into the living instance.  
**Status:** PENDING  

## Context

The completed Grok pass-1 campaign staged a 483-URL inventory as 477 accepted manifest rows, 478 artifact/evidence pairs, one failed row, and five quarantined rows without promoting living summaries. Its active plan remains `PASS1_COMPLETE`, not `DONE`, because the required parent-level semantic audit and closure record are missing. This execution plan closes that work first, then evaluates the same frozen 30-source evidence cohort across OMP and Grok before any provider-neutral refinement or living promotion.

## Approach

### Fixed decisions

- OMP uses exact model `openai-codex/gpt-5.6-sol` at `xhigh`; Grok CLI uses exact model `grok-4.5` at `high`. No model fallback is allowed. An unavailable model blocks its lane.
- The factual oracle is the frozen `evidence_bundle`, never OMP, Grok, or the pass-1 prose. OMP is the quality-reference lane and final reviewer; blind A/B labeling and a separate staged-baseline guard reduce self-preference.
- Both candidate lanes receive the exact same system string (`Follow the supplied Atlas task exactly. Return only the requested output.`) and rendered prompt bytes, with ambient extensions/rules/skills disabled and no tools, memory, subagents, plan mode, or write authority. Provider-specific differences are limited to CLI flag transport/model selection. The parent writes stdout into the lane named below.
- No `.claude/`, `CLAUDE.md`, `.grok/`, or provider-specific skill/rule changes. Existing `AGENTS.md` and `.cursor/{skills,rules}` repository aliases remain the harness surface; shared contracts stay under `.agents/`.
- Canonical X identity is `x.com`, matching the staging campaign. `twitter.com`, `www.twitter.com`, and `www.x.com` normalize to `x.com`. X-only `s=<ASCII digits>` is tracking noise; non-X or nonnumeric `s` survives.
- Candidate generation never sees the other lane or pass-1 artifact prose. Evaluation may read the original artifact only after both lane artifacts and their hashes are frozen.
- A shared contract change requires one stable contract-systemic code on at least three independent sources spanning at least two exact semantic strata, where `semantic_stratum = source_kind + ":" + coverage`. Batch and hash partitions freeze execution only; they are not evidence of semantic breadth. A provider-only failure is transport/artifact-local.
- Promotion reuses accepted staged evidence and prose. It does not refetch an absent living source; an existing living source with a different content hash is the sole case that must use fresh `/atlas-source --resummarize` evidence.
- Failed inventory row `fd3fe07e32f0` and the five quarantine rows are not in the 477-row staging manifest and are never promoted.

### State, ownership, and directory contract

- Read-only pass-1 root after closure: `STAGING = vault://atlas/tmp/todos-source-summaries-2026-07-15/`.
- Cross-harness root: `COMPARE = vault://atlas/tmp/source-summary-cross-harness-2026-07-16/`.
- T1 may resolve `STAGING_OS` through the active connector solely for local CLI `--cwd`/redirection; record it only in run metadata. Every durable plan/report path remains logical `vault://atlas/...`.
- Living writes remain under `vault://atlas/summaries/` and its canonical registries only; product contracts/scripts remain in this repository.
- At T4 set `APP_ROOT = Path.cwd().resolve()` only after asserting `.agents/ARCHITECTURE.md`, `scripts/atlas_quality.py`, and `tests/` exist there. Record the absolute transport path, `git rev-parse HEAD`, working-tree diff hash, and critical-file hashes in `shared/repo-snapshot.json`; every local Python command runs as `python3 "$APP_ROOT/scripts/..."`.

Create this layout schema; angle-bracket and brace components denote generated repetitions, never literal filenames:

```text
COMPARE/
  shared/
    cohort.json
    hashes.json
    repo-snapshot.json
    calibration-cases.json
    contract-snapshot/
      ARCHITECTURE.md
      atlas-source-SKILL.md
      source-summary-template.md
      source-summary-quality-guide.md
      source-summary-quality.json
    bundles/<source_id>.json
    prompts/calibration.md
    prompts/sources/<order>-<source_id>.md
    original-index.json
    review-schema.json
    single-review-schema.json
    tools/build-calibration-input.py
    tools/validate-review.py
    tools/resolve-review.py
    tools/render-repair-prompt.py
  sandboxes/{omp,grok,reviewer}/
  omp-gpt-5.6-sol-xhigh/
    attempts/<order>-<source_id>/g<generation>-t<transport>.md
    records/<order>-<source_id>/g<generation>.json
    prompts/<order>-<source_id>/g<generation>.md
    repair-inputs/<order>-<source_id>/g<generation>.json
    runs/calibration-{response,validation,validation-input}.json
    runs/calibration.{stderr,meta.json}
    runs/manifest.json
    runs/manifest-extensions/<order>-<source_id>/g<generation>.json
    runs/<order>-<source_id>/g<generation>-t<transport>.{stderr,meta.json,validation.json}
  grok-4.5-high/
    attempts/<order>-<source_id>/g<generation>-t<transport>.md
    records/<order>-<source_id>/g<generation>.json
    prompts/<order>-<source_id>/g<generation>.md
    repair-inputs/<order>-<source_id>/g<generation>.json
    runs/calibration-{response,validation,validation-input}.json
    runs/calibration.{stderr,meta.json}
    runs/manifest.json
    runs/manifest-extensions/<order>-<source_id>/g<generation>.json
    runs/<order>-<source_id>/g<generation>-t<transport>.{stderr,meta.json,validation.json}
  reports/
    structural/<lane>/<source_id>/<generation>.json
    review-inputs/{pairwise,baseline,single}/<review_id>.md
    review-responses/<phase>/<review_id>.json
    staged-records/<source_id>.json
    review-records/<phase>/<review_id>.json
    review-runs/<phase>/<review_id>/t<transport>.{response.json,stderr,meta.json}
    review-selections/<phase>/<source_id>/{selection-<version>.json,current.json}
    mappings.jsonl
    audit-partitions.json
    repairs/<source_id>/{prompts,attempts,runs,records}/...
    changed-hash/<source_id>/{bundle,prompts,attempts,runs,records}/...
    iterations/<iteration>/{contract-snapshot,hashes,calibration,manifests,prompts,records}/...
    governing/<version>/{contract-snapshot,hashes,calibration,cohort-selection.json,snapshot.json}
    governing-index.json
    living-snapshot/<snapshot_id>/{MANIFEST.md,RELATIONS.md,TOPICS.md,artifacts.json,snapshot.json}
    events/<source_id>/<event_type>-<event_sha256>.json
    transactions/<transaction_id>/{intent.json,prepared.json,backups/,progress/,aborted.json,committed.json,rolled-back.json,manual-conflict.json}
    promotion-maps/map-<version>.json
    promotion-maps/index.json
    final.json
    final.md
```

`shared/bundles/<source_id>.json` is versioned JSON containing only immutable identity/provenance plus the complete original envelope nested as `evidence_bundle`; it must not contain `artifact_text`, artifact body excerpts, campaign request text, topic state, or provider identity. `shared/original-index.json` maps IDs to pass-1 artifacts but is evaluator-only. `hashes.json` records SHA-256 for every other shared file and every canonical product contract; each lane's immutable `runs/manifest.json` records the SHA-256 of `hashes.json`, and the completion audit records both lane-manifest hashes.

### Frozen 30-source cohort

Common artifact and evidence paths below are relative to `STAGING`. Strata are derived only from staging sequence: early `1-159`, middle `160-318`, late `319-477`. The fixed table contains 12 early, 12 middle, and 6 late rows; 18 repos, 6 threads, 3 articles, 1 docs page, 1 video, 1 paper; 27 complete and 3 partial. No substitution is allowed: any selected-row identity/hash/bundle mismatch blocks T4 and keeps the cohort unchanged. Run batches in A→E order with a barrier after each batch; concurrency may be at most three independent source processes within a lane.

| Batch | Order | Seq | Source ID | Kind | Coverage | Canonical URL | Staged artifact | Evidence |
|---|---:|---:|---|---|---|---|---|---|
| A | 1 | 86 | `97416d4ba885` | repo | complete | https://github.com/badlogic/pi-mono | `artifacts/2026/2026-07/2026-07-15--97416d4ba885--pi-mono.md` | `envelopes/97416d4ba885.json` |
| A | 2 | 253 | `2a905ba6996d` | article | complete | https://anthropic.com/engineering/harness-design-long-running-apps | `artifacts/2026/2026-07/2026-07-15--2a905ba6996d--harness-design-long-running-apps.md` | `envelopes/2a905ba6996d.json` |
| A | 3 | 287 | `f6b93302265d` | article | complete | https://openai.com/index/harness-engineering | `artifacts/2026/2026-07/2026-07-15--f6b93302265d--harness-engineering.md` | `envelopes/f6b93302265d.json` |
| A | 4 | 329 | `f4003266c381` | thread | complete | https://x.com/akshay_pachaar/status/2041146899319971922 | `artifacts/2026/2026-07/2026-07-15--f4003266c381--agent-harness-deep-dive.md` | `envelopes/f4003266c381.json` |
| A | 5 | 143 | `abed17357c3a` | repo | complete | https://github.com/howdymary/hermes-agent-metaharness | `artifacts/2026/2026-07/2026-07-15--abed17357c3a--hermes-agent-metaharness.md` | `envelopes/abed17357c3a.json` |
| A | 6 | 144 | `e9eb05e2bf38` | repo | complete | https://github.com/humanlayer/12-factor-agents | `artifacts/2026/2026-07/2026-07-15--e9eb05e2bf38--12-factor-agents.md` | `envelopes/e9eb05e2bf38.json` |
| B | 7 | 129 | `f4e0adf84666` | repo | complete | https://github.com/github/spec-kit | `artifacts/2026/2026-07/2026-07-15--f4e0adf84666--spec-kit.md` | `envelopes/f4e0adf84666.json` |
| B | 8 | 241 | `33623ca9fb6e` | repo | complete | https://github.com/yeachan-heo/oh-my-claudecode | `artifacts/2026/2026-07/2026-07-15--33623ca9fb6e--oh-my-claudecode.md` | `envelopes/33623ca9fb6e.json` |
| B | 9 | 103 | `a90e1fa2514d` | repo | complete | https://github.com/code-yeongyu/oh-my-openagent | `artifacts/2026/2026-07/2026-07-15--a90e1fa2514d--oh-my-openagent.md` | `envelopes/a90e1fa2514d.json` |
| B | 10 | 233 | `86aea030f36f` | repo | complete | https://github.com/vercel-labs/open-agents | `artifacts/2026/2026-07/2026-07-15--86aea030f36f--open-agents.md` | `envelopes/86aea030f36f.json` |
| B | 11 | 401 | `60dee7b38a08` | thread | complete | https://x.com/mattpocockuk/status/2048159313357598989 | `artifacts/2026/2026-07/2026-07-15--60dee7b38a08--mattpocock-afk-agents-day-night.md` | `envelopes/60dee7b38a08.json` |
| B | 12 | 154 | `f226959a357f` | repo | complete | https://github.com/karpathy/autoresearch | `artifacts/2026/2026-07/2026-07-15--f226959a357f--autoresearch.md` | `envelopes/f226959a357f.json` |
| C | 13 | 82 | `82a901da1b9b` | repo | complete | https://github.com/anthropics/skills | `artifacts/2026/2026-07/2026-07-15--82a901da1b9b--anthropic-skills.md` | `envelopes/82a901da1b9b.json` |
| C | 14 | 250 | `4a5a5c2b4be3` | docs | complete | https://agentskills.io/ | `artifacts/2026/2026-07/2026-07-15--4a5a5c2b4be3--agentskills.md` | `envelopes/4a5a5c2b4be3.json` |
| C | 15 | 165 | `3757de6abc6b` | repo | complete | https://github.com/microsoft/SkillOpt | `artifacts/2026/2026-07/2026-07-15--3757de6abc6b--skillopt.md` | `envelopes/3757de6abc6b.json` |
| C | 16 | 187 | `2009754ac555` | repo | complete | https://github.com/oraios/serena | `artifacts/2026/2026-07/2026-07-15--2009754ac555--serena.md` | `envelopes/2009754ac555.json` |
| C | 17 | 230 | `401c6af5b51d` | repo | complete | https://github.com/vercel-labs/agent-browser | `artifacts/2026/2026-07/2026-07-15--401c6af5b51d--agent-browser.md` | `envelopes/401c6af5b51d.json` |
| C | 18 | 453 | `4b892172ad31` | thread | complete | https://x.com/tonygentilcore/status/2075234683202531403 | `artifacts/2026/2026-07/2026-07-15--4b892172ad31--glean-coding-harness-programmatic-tools.md` | `envelopes/4b892172ad31.json` |
| D | 19 | 112 | `f66817e443f3` | repo | complete | https://github.com/e2b-dev/e2b | `artifacts/2026/2026-07/2026-07-15--f66817e443f3--e2b.md` | `envelopes/f66817e443f3.json` |
| D | 20 | 273 | `70fd9e30950d` | article | complete | https://howtoeval.com/ | `artifacts/2026/2026-07/2026-07-15--70fd9e30950d--howto-eval-ai-agents.md` | `envelopes/70fd9e30950d.json` |
| D | 21 | 379 | `e177f213abb6` | thread | partial | https://x.com/intuitiveml/status/2048912026018484317 | `artifacts/2026/2026-07/2026-07-15--e177f213abb6--intuitiveml-self-healing-agent-harness.md` | `envelopes/e177f213abb6.json` |
| D | 22 | 382 | `108d87a4b26b` | thread | partial | https://x.com/ishaansehgal/status/2065129901427130678 | `artifacts/2026/2026-07/2026-07-15--108d87a4b26b--ishaansehgal-log-is-the-agent.md` | `envelopes/108d87a4b26b.json` |
| D | 23 | 317 | `a1bf4630d391` | thread | partial | https://x.com/0xMovez/status/2045541438079836253/video/1 | `artifacts/2026/2026-07/2026-07-15--a1bf4630d391--0xmovez-anthropic-vibe-coding-video.md` | `envelopes/a1bf4630d391.json` |
| D | 24 | 475 | `858ff7924b69` | video | complete | https://youtu.be/tnP_Q5mS1I8?si=nsDIK8f4h5cgH05r | `artifacts/2026/2026-07/2026-07-15--858ff7924b69--stitch-design-decision-creative-direction.md` | `envelopes/858ff7924b69.json` |
| E | 25 | 1 | `a2cb64316448` | paper | complete | https://arxiv.org/abs/2606.24937 | `artifacts/2026/2026-07/2026-07-15--a2cb64316448--hitchhikers-guide-agentic-ai.md` | `envelopes/a2cb64316448.json` |
| E | 26 | 76 | `2f4fe8c56a5a` | repo | complete | https://github.com/aidenybai/react-scan | `artifacts/2026/2026-07/2026-07-15--2f4fe8c56a5a--react-scan.md` | `envelopes/2f4fe8c56a5a.json` |
| E | 27 | 111 | `bebec19dda3a` | repo | complete | https://github.com/drizzle-team/drizzle-orm | `artifacts/2026/2026-07/2026-07-15--bebec19dda3a--drizzle-orm.md` | `envelopes/bebec19dda3a.json` |
| E | 28 | 146 | `5596cebd2066` | repo | complete | https://github.com/hyperknot/openfreemap | `artifacts/2026/2026-07/2026-07-15--5596cebd2066--openfreemap.md` | `envelopes/5596cebd2066.json` |
| E | 29 | 168 | `c750f525fc3d` | repo | complete | https://github.com/microsoft/qlib | `artifacts/2026/2026-07/2026-07-15--c750f525fc3d--qlib.md` | `envelopes/c750f525fc3d.json` |
| E | 30 | 234 | `876fe6c1edb8` | repo | complete | https://github.com/volcengine/OpenViking | `artifacts/2026/2026-07/2026-07-15--876fe6c1edb8--OpenViking.md` | `envelopes/876fe6c1edb8.json` |


### Exact generation and review protocol

#### Frozen prompts and process isolation

For each source, render one candidate prompt by concatenating, in this exact order: a fixed instruction header; the complete frozen architecture source-identity/reducer excerpt; the full frozen `atlas-source` skill; the full template; the full quality guide; and that source's canonical bundle JSON. End with: `Return only the complete Markdown source-summary artifact. Do not use fenced code blocks.` The header requires `--resummarize`, context-neutral drafting, unchanged immutable provenance, every template section, explicit coverage/caveats, no ambient campaign/topic/provider facts, and no model-exposed retrieval or tool use. Record the exact UTF-8/LF prompt SHA-256.

Create empty lane and reviewer sandbox directories and run each harness with its sandbox as `--cwd`, never `APP_ROOT`. Candidate prompts are identical bytes across lanes. The provider API transport remains necessary; the isolation claim is narrower and measurable: the model receives only the system string plus prompt, the configured tool surface is empty, and the empty sandbox tree hash is unchanged. Preflight each exact command with an inert prompt that asks for an unavailable file write; require a normal text refusal/result, no marker file, unchanged sandbox hash, and the exact configured model. If a flag is unsupported, stop instead of relaxing isolation. No claim of OS-level process isolation is made.

#### Calibration

Render hashed `shared/calibration-cases.json` by preserving top-level `version` and each ordered case object byte-semantically except deleting its `expected` member, then canonicalizing compact sorted-key JSON plus LF. Render the model prompt from the frozen guide plus those answer-free bytes; the complete hashed fixture stays validator-only. Response schema is exact `{"version":1,"results":[{"id":<string>,"actual":<JSON value>},...]}`; the builder joins IDs to private expected values before validation. Run:

```bash
omp --cwd "$COMPARE_OS/sandboxes/omp" \
  --model openai-codex/gpt-5.6-sol --thinking xhigh \
  --system-prompt 'Follow the supplied Atlas task exactly. Return only the requested output.' \
  --no-session --no-extensions --no-rules --no-skills --no-lsp --no-tools \
  --max-time 20m --mode text \
  -p @"$COMPARE_OS/shared/prompts/calibration.md" \
  > "$COMPARE_OS/omp-gpt-5.6-sol-xhigh/runs/calibration-response.json" \
  2> "$COMPARE_OS/omp-gpt-5.6-sol-xhigh/runs/calibration.stderr"

grok --cwd "$COMPARE_OS/sandboxes/grok" \
  --model grok-4.5 --reasoning-effort high \
  --system-prompt-override 'Follow the supplied Atlas task exactly. Return only the requested output.' \
  --no-memory --no-subagents --no-plan --tools "" --max-turns 1 \
  --verbatim --output-format plain \
  --prompt-file "$COMPARE_OS/shared/prompts/calibration.md" \
  > "$COMPARE_OS/grok-4.5-high/runs/calibration-response.json" \
  2> "$COMPARE_OS/grok-4.5-high/runs/calibration.stderr"
```

For each lane, run the hashed campaign-local builder:

```bash
python3 "$COMPARE_OS/shared/tools/build-calibration-input.py" \
  --fixture "$APP_ROOT/.agents/skills/atlas-core/assets/evals/source-summary-quality.json" \
  --response "$COMPARE_OS/$LANE/runs/calibration-response.json" \
  --output "$COMPARE_OS/$LANE/runs/calibration-validation-input.json"
python3 "$APP_ROOT/scripts/atlas_quality.py" validate-calibration \
  --input "$COMPARE_OS/$LANE/runs/calibration-validation-input.json" \
  > "$COMPARE_OS/$LANE/runs/calibration-validation.json"
```

The builder writes compact sorted-key JSON with exactly `version: 1`, `fixture_text: <the fixture file's exact UTF-8 text>`, and `response_text: <the response file's exact UTF-8 text>`. The validator emits only `{"findings":[],"ok":true}` on success. Independently parse the response and require exactly the 24 unique fixture IDs from the four fixture arrays; record the sorted IDs and count in `calibration.meta.json`. Exit `0`, the exact success JSON, and 24/24 unique IDs are separate mandatory gates.

#### Candidate commands and immutable attempts

For every process, the parent sets `LANE`, `ORDER`, `SOURCE_ID`, `GENERATION` (`0..2`), `TRANSPORT` (`0..2`), and the absolute `PROMPT` path, creates the target directory, and records their resolved values. OMP:

```bash
omp --cwd "$COMPARE_OS/sandboxes/omp" \
  --model openai-codex/gpt-5.6-sol --thinking xhigh \
  --system-prompt 'Follow the supplied Atlas task exactly. Return only the requested output.' \
  --no-session --no-extensions --no-rules --no-skills --no-lsp --no-tools \
  --max-time 20m --mode text -p @"$PROMPT" \
  > "$COMPARE_OS/omp-gpt-5.6-sol-xhigh/attempts/$ORDER-$SOURCE_ID/g$GENERATION-t$TRANSPORT.md" \
  2> "$COMPARE_OS/omp-gpt-5.6-sol-xhigh/runs/$ORDER-$SOURCE_ID/g$GENERATION-t$TRANSPORT.stderr"
```

Grok:

```bash
grok --cwd "$COMPARE_OS/sandboxes/grok" \
  --model grok-4.5 --reasoning-effort high \
  --system-prompt-override 'Follow the supplied Atlas task exactly. Return only the requested output.' \
  --no-memory --no-subagents --no-plan --tools "" --max-turns 1 \
  --verbatim --output-format plain --prompt-file "$PROMPT" \
  > "$COMPARE_OS/grok-4.5-high/attempts/$ORDER-$SOURCE_ID/g$GENERATION-t$TRANSPORT.md" \
  2> "$COMPARE_OS/grok-4.5-high/runs/$ORDER-$SOURCE_ID/g$GENERATION-t$TRANSPORT.stderr"
```

Attempts are immutable. A transport failure is only timeout, nonzero exit, or zero-byte stdout; retry the identical prompt at `t1`, then `t2`, and stop that generation after the first exit-zero nonempty output. Invalid Markdown, deterministic validator findings, or semantic review failures are artifact failures, not transport failures; they may open `g1` and then `g2`; never overwrite an attempt or passing generation.

Generation zero uses the frozen prompt. `g1|g2` repair input is exact `version`, `source_id`, `parent_record_sha256`, nullable `trigger_review_record_sha256`, `trigger_type:deterministic|semantic`, and sorted `findings`. Deterministic finding is `{kind:deterministic,code,path}`. Semantic finding is one of `{kind:status,code:status-fail,dimension,evidence}`, `{kind:correction,code:factual-correction,dimension,claim,correction,evidence}`, or `{kind:defect,code,class,dimension,evidence}` from a validated review. Every failure projects at least one finding. The hashed renderer adds only canonical findings after the same header/contracts/bundle—never prior artifact prose—and each extension binds parent/repair/renderer/prompt/contract hashes.

After a nonempty exit-zero attempt, run `validate-summary`. Generated record keys are exactly `version`, `record_type: generated`, `lane`, `source_id`, nullable `cohort_order`, `staging_seq`, `generation`, `attempt_path`, `prompt_sha256`, `bundle_sha256`, `output_sha256`, `validation_sha256`, `contract_snapshot_sha256`, nullable `repair_input_sha256`, `repair_renderer_sha256`, `parent_record_sha256`, `trigger_review_record_sha256`, and `status`. T6-T8 carry cohort order; non-cohort T9 uses null. Only `deterministic-pass` enters review. Attempt metadata binds flags/model/harness/hashes/timestamps/exit/bytes/sandbox/failure class, never credentials/reasoning.

For every staged operand write an immutable `staged-records/<source_id>.json` with exactly `version`, `record_type: staged`, `source_id`, `artifact_path`, `bundle_path`, `artifact_sha256`, `bundle_sha256`, `deterministic_report_sha256`, `pass1_manifest_row_sha256`, `semantic_review_origin: pass1|t9`, `semantic_review_record_sha256`, and `seven_statuses`. T8 uses the exact T1 pass-1 record; T9 uses its validated single-review record. A staged record is not eligible until this record exists with seven passes, no corrections, and no defects. Resolver operands are the typed union `{record_type:generated|staged,record_path,record_sha256}`.

#### Review schemas, consistency, and resolution

Pairwise/baseline review has exact top-level `version`, `phase`, `source_id`, labels, dimensions, factual corrections, defects, overall. Each of seven dimensions is exact `{id,left_status,right_status,winner,evidence}`; evidence is nonempty allowed `{url,locator}`. Correction is exact `{side,dimension,claim,correction,evidence}`. Defect is exact `{side,dimension,code,class,detail,evidence}` with side `left|right|both`, class `artifact-local|contract-systemic`, and the same anchored evidence. Unknown/empty fields fail.

The validator enforces dimension consistency. A side is eligible only when its deterministic report has zero findings, all seven statuses pass, and no factual correction or artifact-local/contract-systemic defect applies to it. For a staged side, the resolver additionally verifies its bound semantic-review hash/statuses; a failed T1 staged operand is forced ineligible in T8 by an exact eligibility constraint binding that pass-1 record, just as a failed T9 staged operand is ineligible during repair baseline. `overall` must name an eligible side; `fail-both` iff neither is eligible. Transport defects never enter semantic review.

Single review top-level is exact `version`, `phase:single`, `source_id`, `dimensions`, `factual_corrections`, `defects`, `overall`. Seven dimensions are `{id,status,evidence}`; corrections `{dimension,claim,correction,evidence}`; defects `{dimension,code,class,detail,evidence}` with anchored evidence. Overall pass requires seven passes, no corrections/defects; every other combination is rejected.

Before rendering a pairwise prompt, append a canonical JSON line to evaluator-only `reports/mappings.jsonl`. The last source-ID hex digit chooses pairwise A (even: OMP; odd: Grok); B is the other lane. The prompt exposes only A/B. A validated review record at `reports/review-records/<phase>/<review_id>.json` binds the raw response hash, prompt hash, schema/validator hashes, both typed operand records, both deterministic reports, and any `eligibility_constraints`. `resolve-review.py` consumes only this record plus the mapping. If neither side is eligible, it returns `none` and T8 repairs before baseline. Otherwise `overall:left|right` selects the mapped eligible provider and `tie` selects OMP, which must be eligible.

Derive `review_id` as `<phase>-<source_id>-<first16>` where `<first16>` is SHA-256 over compact sorted-key JSON `{phase,source_id,operand_record_sha256s,contract_snapshot_sha256}`. Operand or contract changes therefore create a new immutable ID. After each resolved review, append `selection-<six-digit-N>.json` binding its predecessor, review-record hash, result, and contract hash, then atomically write/reread `current.json` to that selection. Gate counts refer only to current pointers; all superseded responses, records, and selections remain.

After pairwise freezes, append a second mapping: second-to-last source-ID hex digit chooses baseline A (even: selected generated; odd: staged), B is the other. Tie retains generated; fail-both blocks; staged may win only with eligible typed/deterministic/semantic records. Forced constraint is exact `{operand,forced_ineligible:true,reason:failed-single-review|content-hash-mismatch,staged_record_sha256,evidence_record_sha256}`; resolver verifies either a failed single review binding that staged artifact or a fresh same-identity capture whose content hash differs, then rejects selecting it. T8 requires 30 current pairwise and 30 baseline selections; pairwise `none` after `g2` blocks without baseline; superseded records do not count.

Render review prompts as fixed review instructions, frozen guide, frozen bundle, then labeled artifact bytes. Set `REVIEW_PHASE`, `REVIEW_ID`, `TRANSPORT` (`0..2`), and absolute `REVIEW_PROMPT`; run:

```bash
omp --cwd "$COMPARE_OS/sandboxes/reviewer" \
  --model openai-codex/gpt-5.6-sol --thinking xhigh \
  --system-prompt 'Follow the supplied Atlas task exactly. Return only the requested output.' \
  --no-session --no-extensions --no-rules --no-skills --no-lsp --no-tools \
  --max-time 20m --mode text -p @"$REVIEW_PROMPT" \
  > "$COMPARE_OS/reports/review-runs/$REVIEW_PHASE/$REVIEW_ID/t$TRANSPORT.response.json" \
  2> "$COMPARE_OS/reports/review-runs/$REVIEW_PHASE/$REVIEW_ID/t$TRANSPORT.stderr"
```

Use the same transport classification/cap as generation. Validate the first exit-zero nonempty response against the phase schema before resolution, preserve every response, and copy a schema-valid raw response byte-for-byte to `reports/review-responses/<phase>/<review_id>.json` only if absent or hash-identical. Then write the immutable validated review record described above; resolver and audit consume the record, never an unbound raw response. Metadata records prompt/output/schema/validator/resolver/contract hashes, command flags, exact model/harness, timestamps, exit code, byte count, and sandbox hashes. Reviewer prompts never include `original-index.json`, provider mappings, lane metadata, prior reviews, living state, or provider names.

#### Contract iterations

An artifact-local defect repairs only that source. A shared contract proposal requires the same contract-systemic code on at least three independent sources spanning two `source_kind:coverage` semantic strata. For iteration `01` or `02`, create a complete immutable snapshot, hashes, both calibration runs, prompts/attempts/records, and reviews; every record binds its governing snapshot. Do not mutate initial shared material or lane manifests.

At most two shared contract iterations. Each immutable governing state has exact contract/hashes, two calibrations, and complete 30-row selection. Every referenced record must match the row's contract/prompt/bundle/operand hashes. Contract change reruns all 30 chains. Evidence-only successor reruns changed rows but may carry forward unchanged current reviews/selections only after exact hash equality. Advance the index only after complete validation; never overwrite.

### Ordered tasks

- [ ] T1. Close and archive the pass-1 staging plan
  - Resolve `STAGING` from `runs/campaign-meta.json`; record current contract hashes and living `MANIFEST.md`, `RELATIONS.md`, and `TOPICS.md` hashes without rolling back concurrent living changes.
  - For each of the 478 stored envelope JSON files, read raw bytes through the connector, pair it with the matched artifact, build the exact version-1 `validate-summary` input, and run `scripts/atlas_quality.py`. Require 478 parsed, zero read errors, and zero deterministic findings. Reconcile `483 = 433 done + 44 partial + 1 failed + 5 quarantine`, 477 accepted manifest rows, 478 artifact/envelope pairs, zero pending rows, and no staging artifact path in the living manifest.
  - Require set equality between the 477 accepted manifest IDs and IDs having exactly one accepted artifact plus exactly one envelope; reject duplicate IDs/paths and unmatched halves. The 478th pair must be source `fd3fe07e32f0`, the explicitly failed non-manifest operand; require it absent from accepted manifests, cohort selection, and every promotion input. The five quarantined rows have no promotable pair.
  - Complete an independent semantic audit of all 30 frozen-cohort originals. For each source render a frozen prompt from the quality guide, full artifact bytes, envelope, and exact review schema; run OMP `openai-codex/gpt-5.6-sol` xhigh with the exact system/isolation/time flags in the calibration command, an empty `STAGING/runs/spot-audit-sandbox/`, and immutable prompt/response/stderr/meta paths. Allow three identical transport attempts and no semantic repair.
  - Validate exact `{version:1,source_id,dimensions:[{id,status,evidence:[{url,locator}]}],factual_corrections:[{dimension,claim,correction,evidence:[{url,locator}]}],defects:[{code,dimension,detail,evidence:[{url,locator}]}],overall}`: seven IDs once, pass/fail, allowed URLs, nonempty locators, stable checklist defect codes. Full reviews remain in staging. Canonical spot rows add `finding_projections:[{kind:status|correction|defect,code,dimension,evidence_refs:[{url,locator_sha256}]}]` to the source/artifact/evidence/review hashes, statuses, codes/count, overall, and disposition. Any nonpassing status/correction/defect must project; eligible iff none.
  - Append closure counts, audit pass/fail/disposition totals, contract hashes, living-drift note, and proof commands to `.agents/plans/2026-07-15-1156_todos-source-summaries-staging.md`; set `Status: DONE`; atomically move it to `.agents/plans/archive/2026-07-15-1156_todos-source-summaries-staging.md`.
  - **Acceptance:** the archived plan is `DONE`; all counts reconcile; 30 schema-valid semantic reviews and projections exist; every failure has a stable checklist code and `repair-in-T8` disposition; instance check reports `check OK`; staging is otherwise unchanged.

- [ ] T2. Implement one deterministic canonical URL and source-ID owner
  - Update `.agents/ARCHITECTURE.md` first, then `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` and `source-summary-template.md`, then `.agents/skills/atlas-source/SKILL.md`.
  - Add dependency-free `scripts/atlas_url.py` with `normalize_canonical_url(url: str) -> str`, `source_id_for(canonical_url: str) -> str`, and a JSON-emitting `normalize` CLI. Normalize `str.strip()` input through `urllib.parse.urlsplit`; require explicit HTTP(S), reject userinfo, hostless/invalid authority, malformed `%` escapes, zone-scoped IPv6, and invalid ports. Lowercase and preserve the supplied scheme (no network-driven HTTP→HTTPS upgrade). Normalize IPv4/IPv6 with `ipaddress`; serialize IPv6 in brackets; otherwise IDNA-encode the lowercase hostname, remove one terminal DNS dot, and canonicalize `twitter.com`, `www.twitter.com`, and `www.x.com` to `x.com`. Drop default port 80/443 and preserve other numeric ports. Preserve an empty path and root `/` distinctly for compatibility; for any longer path remove trailing `/` characters only, without decoding, dot-segment resolution, or percent-escape case changes. Always remove the fragment and an empty `?` delimiter. Split a nonempty raw query only on `&`; split each component on its first `=`; preserve surviving raw components, empty components, order, `+`, semicolons, duplicate names, and percent-escape case byte-for-byte. For drop predicates only, first require every `%` escape to be two hex digits, then decode names/values with `urllib.parse.unquote(..., encoding="utf-8", errors="strict")` (never `unquote_plus`): drop ASCII-case-insensitive decoded names beginning `utm_`; on `x.com` only, drop decoded name exactly `s` when its decoded value matches ASCII `[0-9]+`; preserve every other component. Join survivors with `&` and omit `?` when none remain. `source_id_for` normalizes its input before computing `sha256(normalized_url.encode("utf-8")).hexdigest()[:12]`.
  - In `atlas-source`, invoke the helper before fetch, bundle creation, living/staging lookup, dedupe, identity, or sequence allocation. Agents must not recompute identity from prose.
  - Add `tests/test_atlas_url.py` for input trimming; scheme/host case and scheme preservation; credentials; default/nondefault/invalid ports; IPv4, bracketed IPv6, rejected zone IDs, IDNA, and trailing DNS dots; X aliases; empty/root/non-root paths and trailing slashes; fragments and empty queries; `utm_*`; X `s=20` in first/middle/last position; duplicate `s`; `s=abc`; empty `s`; Unicode digits; percent-encoded ASCII digits; malformed escapes/UTF-8; `+`; semicolons; empty query components; non-X `s`; survivor byte/order/escape-case preservation; invalid schemes; idempotence; and exact known SHA-256 prefixes. Add skill-surface assertions that normalization precedes fetch/dedupe and no checklist contains a second identity implementation.
  - Audit all 483 inventory URLs and the living manifest through the new helper before changing any stored identity. Expected staging result: the 158 raw X `s=<digits>` aliases collapse to their existing no-`s` canonical rows and no accepted source ID changes. Any other ID change blocks implementation and requires explicit `/atlas-migrate`; never rewrite IDs in place.
  - **Acceptance:** URL tests and harness-surface tests pass; normalization is idempotent; staged accepted identity set remains 477/477 unchanged.

- [ ] T3. Add deterministic staged-artifact promotion and recoverable reducer writes
  - Add provider-neutral `/atlas-source --promote-staged <artifact-uri> --evidence <envelope-uri>` and `/atlas-source --capture-evidence <url> --output-root <COMPARE-subtree>`. Capture-evidence fetches and freezes only a source evidence bundle under the explicit temporary root; it never drafts prose or touches living artifacts/registries.
  - Add `scripts/atlas_source.py merge-artifact` as the sole deterministic artifact assembler and a `source-upsert` event in `.agents/ARCHITECTURE.md`, `markdown-registry-contracts.md`, and `scripts/atlas_state.py`. Event fields are exactly `type`, `source_id`, `canonical_url`, `artifact`, `first_seen`, `checked_on`, `summarized_on`, `content_hash`, and `refresh_after`. `artifact` is a connector-neutral relative path under `summaries/sources/artifacts/`; reject absolute paths, URI schemes, `.`/`..`, any `tmp` segment, the wrong prefix, or a new-source filename outside `YYYY/YYYY-MM/YYYY-MM-DD--<source_id>--<slug>.md`. For an existing ID it must equal the manifest path.
  - Reducer behavior: re-normalize URL/ID; validate dates/hash/path; allocate `max(Source seq)+1` only for a new ID; preserve existing sequence, first-seen, artifact path, and manifest `Status`; block archived sources; update mutable dates/hash. Changed hash supersedes old-hash pending relations, recomputes affected topic caches, and sets manifest `Route status` to `unrouted`; same hash preserves relation history and current manifest route status. Return candidate documents and optimistic input hashes; perform no storage I/O.
  - Artifact merge matrix is field-exact. **New:** require staged artifact, envelope, and event agree on source ID/URL/content hash/first-seen; copy staged `acquired_by`, `acquisition_run`, all semantic fields, and body; inject reducer sequence/path, `routing_status: unrouted`, and empty `routed_at`. **Existing same hash:** take semantic fields/body from the selected staged artifact, but overwrite `source_seq`, `canonical_url`, `first_seen`, `acquired_by`, `acquisition_run`, artifact path, manifest-derived route status, and existing `routed_at` from living state; use event dates/refresh hash fields. **Existing changed hash:** accepted only from fresh capture-evidence plus a fresh selected artifact; preserve living identity/acquisition provenance/path, use new semantic/body/hash/dates, and set routing status unrouted/routed-at empty. Manifest `Status` and artifact `routing_status` are distinct. Render template order, UTF-8, and LF deterministically. Idempotent replay means applying the same event to its already-produced state returns identical candidate bytes/hashes and no additional relation transition; it does not mean same-hash promotion preserves the old prose bytes.
  - Add a pure deterministic route-artifact renderer in `scripts/atlas_source.py`. Given the current artifact and validated route-upsert outcome, change only frontmatter `routing_status`/`routed_at` and rendered `**Route status**`; set `routed_at` to event `checked_on` for every terminal outcome. Include this artifact output in route-upsert optimistic targets so artifact and manifest status cannot diverge.
  - Persist canonical event exact `{version,event_type,source_id,promotion_map_sha256,promotion_row_sha256,event,route_decision}`; map/row hashes are nullable outside T10 and required/nonnullable there. T10 verifies row membership before reduction/recovery. Build ordered targets, then derive `base_transaction_id = first16(sha256(canonical {event_record_sha256,promotion_map_sha256,promotion_row_sha256,source_id,targets}))`.
  - Transaction path/ID is `<base_transaction_id>-a<six-digit-attempt>`. Attempt zero has null predecessor; each later attempt names the reread-verified terminal SHA-256 of the immediately preceding `aborted|rolled-back` attempt. Exclusive-create intent keys are exact version/base/transaction/attempt/predecessor, event path/hash/type, map/row/source hashes, and ordered target input/output hashes. Reread intent, backups, and prepared; zero targets terminalize `no-op`; otherwise apply artifact→RELATIONS→TOPICS→MANIFEST with output rereads/progress, then `applied`.
  - Recovery: intent without prepared may complete preparation or abort only while all targets equal inputs. With prepared, `other` is manual conflict; all output commits applied; all input rolls back; mixed input/output restores reverse order and verifies inputs before rolled-back. After inputs are verified, aborted/rolled-back does not advance promotion: create the next attempt with identical event/outputs. Only `applied|no-op` advances; manual conflict blocks. Restore manifest before deleting a new artifact; progress never overrides hashes; connector write+reread is the sole acknowledgement.
  - Extend `atlas_state.py` with a pure recovery planner and `atlas_source.py` with source/route artifact renderers. Test create, replay, same/changed hash, sequence collision, URL-ID mismatch, archived source, path rejection, provenance, source merge bytes, route-status/date synchronization, event/transaction collision, zero-target commit, crashes after each backup and during intent/prepared acknowledgement, pre-write abort, every input/output/other recovery class, every living-write failure, restart, rollback, record failure, and manual conflict. Exercise actual connector paths with disposable fixtures.
  - **Acceptance:** new, existing-same-hash, and route fixtures succeed and replay byte-identically; each injected failure restores exact original living bytes or deterministically commits; no fixture remains; terminal transaction records prove every attempted write; full state/source/harness tests pass.

- [ ] T4. Freeze cohort, contracts, tools, manifests, and prompt bytes
  - Verify every selected table row against raw staging manifest, artifact, and envelope bytes. Require derived stratum, source ID, normalized canonical URL, source kind, coverage, content hash, artifact path, and evidence path agreement. Any mismatch blocks; there is no fallback or substitution.
  - Write `shared/cohort.json` as exact `{version:1, rows:[...]}`; every ordered row has exactly `batch`, `order`, `stratum`, `staging_seq`, `source_id`, `canonical_url`, `source_kind`, `coverage`, `content_hash`, `artifact`, and `evidence`. Require the fixed 30/12-12-6/27-3/kind counts after parsing this file.
  - Materialize stripped bundles, complete initial contracts, prompts, evaluator-only original index, repository snapshot, review schemas, private calibration oracle, answer-free calibration cases, builder, validator, resolver, and tests. `hashes.json` covers every shared file and canonical contract. Set `shared/` read-only after hashing; only parent evaluation and the builder may read the original index/private oracle.
  - Create each immutable lane `runs/manifest.json` with exact `version`, `lane`, `model`, `effort`, `harness_version`, `shared_hashes_sha256`, and 30 ordered entries of `order`, `source_id`, `bundle_sha256`, and `prompt_sha256`; freeze before calibration. Each lane manifest hash is recorded outside `shared`.
  - **Acceptance:** 30 unique IDs/URLs and exact declared distributions; 30 prompt hashes; no bundle contains artifact text, staged prose, or provider/campaign context; both lane manifests bind identical bundle/prompt hashes and the same shared hash; campaign-tool tests accept canonical calibration/pairwise/baseline/single/resolver fixtures and reject unknown fields, inconsistent winners, missing/duplicate dimensions, bad evidence URLs, empty anchors, invalid enums, and ineligible selections.

- [ ] T5. Qualify both harnesses against the same calibration
  - Run repository harness-surface tests; resolve/record `APP_ROOT`, `COMPARE_OS`, `omp`/`grok` versions, exact model resolution, critical file hashes, command flags, and empty sandbox hashes. Do not add harness adapters.
  - Execute the exact preflights and calibration commands above. Build each validation input with the hashed builder, validate all 24 fixture cases, record the exact sorted response IDs, and freeze response/validation/meta files.
  - **Acceptance:** both lanes return exit zero, exact 24/24 validator success, and identical sorted IDs; projected calibration prompts contain no `expected` key/value while builder inputs bind the full private fixture hash; prompt, fixture, contract, and sandbox hashes match.

- [ ] T6. Generate 30 OMP reference candidates
  - Run batches A→E with the exact OMP command, fresh process per source, maximum concurrency three, immutable attempt paths, and the transport/generation caps above. Validate every exit-zero output immediately; never regenerate a passing generation.
  - **Acceptance:** exactly 30 source IDs have one immutable OMP `deterministic-pass` generation record bound to an existing Markdown attempt; every process has metadata/stderr/validation, every retry is preserved, sandbox hashes are unchanged, and no model-exposed tool was enabled.

- [ ] T7. Generate 30 Grok comparison candidates
  - Run the same batches and prompt hashes with the exact Grok command, immutable attempt paths, and identical caps. OMP output, pass-1 prose, provider mappings, and living state are not supplied to Grok and are unreachable through the empty model tool surface.
  - **Acceptance:** exactly 30 source IDs have one immutable Grok `deterministic-pass` generation record bound to an existing Markdown attempt; every process has metadata/stderr/validation, every retry is preserved, sandbox hashes are unchanged, and tool/subagent/memory/plan modes were disabled by recorded flags.

- [ ] T8. Blind-compare, refine, and select the 30-source cohort
  - Finish the current pairwise round before repair and aggregate stable codes; a threshold-qualified shared contract iteration takes precedence. Otherwise each structurally failing or pairwise-ineligible side advances only its own lane from side-specific findings; both advance when both fail, a passing side never regenerates, and pairwise reruns after the round. `none` after either required side reaches `g2` blocks. Baseline starts only with an eligible generated operand.
  - Grok may propose a provider-neutral contract patch only from anonymized repeated-defect tuples. OMP reviews it against architecture, both calibrations, affected pairs, and non-regression gates. Never add provider labels/instructions to shared skills, templates, guides, fixtures, validators, or resolver.
  - After any contract change, rerun all 30 pairwise and baseline chains under that contract; regenerate only candidates whose model-visible prompt hash changed, and rerun deterministic reports for every selected operand. Create an immutable governing snapshot whose 30-row selection binds source, current pairwise/baseline records, mappings, typed operand, artifact/evidence, seven statuses, prompt/contract hashes, and predecessor. Advance the index only when every referenced record binds that snapshot, both calibrations pass, and no selection is `none`.
  - **Acceptance:** at least 60 initial attempts and exactly 30 selected lineages are accounted for; exactly 30 current pairwise plus 30 current baseline selections resolve to snapshot-bound records; all superseded reviews remain; selected sides have zero factual/seven-item failures; both final calibrations pass.

- [ ] T9. Audit all 477 sources, repair failures, and freeze the promotion map
  - Capture the living snapshot with two complete collections. Each collection reads MANIFEST→RELATIONS→TOPICS, then every targeted living artifact and its required-frontmatter projection. Accept only when the two complete registry/artifact collections are byte-identical; retry the pair at most twice. Validate identity, hash, path, provenance, route status, and routed-at agreement; store exact registry bytes, artifact hashes/projections, and snapshot hash.
  - Freeze source-ID-sorted `audit-partitions.json` rows exact `{source_id,workload_partition,source_kind,coverage,semantic_stratum}`; the first hex nibble defines workload `p0|p1`, while semantic stratum is exact `source_kind:coverage`. Bind row and file hash in every T9 review. Only semantic strata satisfy the shared-change threshold.
  - Read the indexed governing snapshot; deterministically validate all 477. Use snapshot-bound selected statuses for the cohort; render full seven-dimension single-artifact reviews for the other 447, binding the audit row. Review partial coverage first, but partial alone is not failure.
  - A threshold-qualified systemic defect may consume only remaining global iterations. Rerun both calibrations, all 30 cohort chains, all 447 non-cohort semantic reviews, every deterministic report, and any prompt-changed candidate; require every current record to bind the new governing snapshot, index it, then restart all 477 validation. Otherwise keep the index unchanged.
  - The 30 cohort rows use only current governing selections. A passing non-cohort staged review selects `staged`. A failing non-cohort row uses its staged record as `g0` parent and exact defect-code/evidence-anchor repair input; run only OMP `openai-codex/gpt-5.6-sol` xhigh with the frozen OMP command, two generations and three transport attempts each, then deterministic validation, independent single review, and baseline against the forced-ineligible staged operand. Bind model/effort/command/prompt/parent lineage; failure after the cap blocks.
  - Allocate immutable `promotion-maps/map-<six-digit-N>.json`. Metadata is exact `{schema_version:1,map_version:N,living_snapshot_sha256,governing_snapshot_sha256,final_contract_sha256,cohort_selection_sha256,supersedes_map_sha256,rows}`. Every source-ID-sorted row has exactly `source_id`, `canonical_url`, `normalized_url_sha256`, `workload_partition`, `semantic_stratum`, `living_partition`, nullable `living_artifact_sha256`, nullable `living_artifact_frontmatter_sha256`, `staging_evidence_sha256`, `selected_evidence_sha256`, `selected_artifact_path`, `selected_artifact_sha256`, `content_hash`, `selection`, typed `selected_record`, `seven_statuses`, `review_record_sha256s`, `lineage_record_sha256s`, and nullable prior-row `supersedes`. First-map supersession is null; changed-hash rows are provisional `needs-fresh`, never indexed.
  - Fresh-capture changed-hash rows without old prose. Non-cohort: fresh OMP `g0`, validate/single-review, baseline old staged forced ineligible. Batch changed cohort rows: regenerate both lanes and rerun pairwise/baseline for those rows; carry forward each unchanged row only after exact contract/prompt/bundle/operand/selection hash validation. Index one complete successor before rebuilding a full superseding map, replacing only changed lineage, then validate/index exact map/governing/contract/cohort hashes.
  - **Acceptance:** 477/477 deterministic validations and seven-item semantic decisions exist; the indexed map has every row `omp|grok|staged`, zero `needs-fresh|none`, all typed records/hashes resolve, six excluded inventory rows remain absent, snapshot/partition counts reconcile, and exactly 477 unique source IDs and normalized URLs exist.

- [ ] T10. Promote, route, and reconcile living Atlas state
  - Validate indexes, discover every current-map transaction intent, and recover all valid nonterminals before any equality gate. Apply full map-snapshot equality only when no intent bound to the current indexed map exists. Reconstruct the frontier from current-map/row-bound transactions only; earlier-map transactions remain audit history and never classify current rows.
  - Require `applied|no-op` source/route pairs to form one contiguous map-row/event-order prefix, with at most the next row `source-committed`; any later current-map transaction is manual conflict. Current state must equal the latest current-map terminal output targeting each path, or map input/absence if untouched; other drift returns to T9. Aborted/rolled-back attempts create the next scoped attempt and do not advance.
  - For untouched, reduce/persist source-upsert with current map/row hashes, reusing hash-identical event bytes/dates. For source-committed, never rerun source: route the committed artifact/current registries, reuse/create one scoped route event, and persist/recover it. Continue from first incomplete row. Empty candidates are `no-topic-match`; schema blockers `routing-blocked`; no topic/manual edge; T10 never edits map/governing state.
  - Process at most 25 source+route pairs per batch. After every event run complete `atlas_state.py validate`; after every batch run `python3 "$APP_ROOT/scripts/atlas-instance.py" check --name atlas`. Reconcile by source ID and normalized URL, never staging sequence. Expected final living count is snapshot unique IDs plus staging IDs absent from the snapshot.
  - **Acceptance:** every one of the 477 IDs is present exactly once; the count formula holds; all artifact paths resolve under `summaries/sources/artifacts/`; no path references `tmp/`; every route attempt ends `routed|no-topic-match|routing-blocked`; every transaction is terminal with no manual conflict; complete state validation and instance check are clean; final registry/artifact/event hashes are recorded.

- [ ] T11. Persist the audit, obtain cleanup approval, delete temporary state, and archive
  - The post-cleanup audit owner is this plan. Append an `AUDIT-START v1` fenced root of compact sorted-key JSON+LF. Category order is header, pass1, calibration-attempt, generation-attempt, artifact-record, review-attempt, review-projection, governing-snapshot, governing-index, map-header/map-row, map-index, transaction, reconciliation.
  - Within categories sort respectively: singleton; `source_id`; `(lane,transport)`; `(source_id,lane,generation,transport)`; `(source_id,record_type,record_sha256)`; `(source_id,phase,review_id,transport)`; `(source_id,phase,review_id)`; `version`; singleton; `(map_version,header-before-row,source_id-or-empty)`; singleton; `(promotion_map_sha256,source_id,event_type,attempt,transaction_id)`; singleton. Header keys are exactly `type`, `version`, `canonicalization`, `repository_snapshot_sha256`, `tool_sha256s`, `contract_snapshot_sha256s`, `schema_sha256s`, `schema_objects`, `lane_manifest_sha256s`, `calibration_record_sha256s`, `pass1_closure_sha256`, `expected_key_sets`.
  - Derive `expected_key_sets` from reread lane manifests, every immutable attempt/record/review index, governing/map indexes, every transaction intent across all maps, and the current-map terminal frontier; include failed/superseded keys. Verifier requires exact row/set equality, fixed 30/477 gates, cross-record hashes, and one valid current frontier. Closed `schema_objects` maps every row type to its full schema; verifier hash is in tools.
  - Pass-1 rows retain source/artifact/evidence/review hashes, statuses, disposition, and all status/correction/defect projections with dimension, stable code, and allowed URL plus locator SHA-256. Attempt rows retain exact identifiers/hashes/flags/model/harness/time/exit/failure fields and nullable tagged `repair_trigger`: deterministic `{kind,code,path}`, status/defect `{kind,code,class?,dimension,evidence_refs}`, or correction `{kind,code,dimension,claim_sha256,correction_sha256,evidence_refs}`; trigger type must match.
  - Artifact records embed complete metadata. Review projections retain review/mapping/operand/selection hashes, statuses/winners/codes/classes/correction dimensions/evidence refs/result/state. Mapping exact `{version,phase,source_id,a_record_sha256,b_record_sha256,selector_name,selector_input,selector_result,mapping_sha256}` reproduces resolution; no source prose survives.
  - Governing projections retain snapshot/predecessor/contract/cohort/calibration hashes plus index. Audit map-row projections copy each immutable map row and add nullable source/route transaction IDs; maps themselves remain unchanged. Transactions retain map/row, event/route, attempt/predecessor, preparation/terminal/target/progress/classification hashes; route reason becomes hash. Reconciliation retains named final hashes/counts/checks.
  - Implement/test repository audit verifier, then append/recheck audit root/SHA. Canonical `reports/final.json` is compact sorted-key JSON+LF exact `{version:1,lane_models,counts,dimension_aggregates,selection_counts,contract_changes,governing_snapshot_sha256,promotion_map_sha256,reconciliation_sha256,audit_sha256,conclusions}`; conclusions are provider-neutral strings without source prose. Derive `final.md`, append exact JSON bytes as fenced `FINAL-REPORT v1` plus its SHA outside the audit root, and verify the active plan in `IN_PROGRESS` mode. Present the retained report/reconciliation/paths for approval.
  - Append/reread `CLEANUP-APPROVAL v1` outside the root as canonical `{paths:[STAGING,COMPARE],approved_at,approver:"user",message_sha256,final_report_sha256,audit_sha256}`; report hash is the retained JSON block hash. Only then delete both roots, prove no references/residue, append post-cleanup proof without changing retained blocks, set DONE, archive, and run verifier in DONE mode; DONE recomputes report/approval hashes.
  - **Acceptance:** the archived plan is the durable source-level audit; its root reconstructs every candidate/review/promotion/route decision without temporary prose; all temporary campaign trees are absent; product tests, state validation, instance check, and archived-root verification pass.

## Critical files & anchors

- `.agents/ARCHITECTURE.md` — canonical source identity, semantic evidence boundary, reducer model, and source-upsert invariants; update first when the durable contract changes.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — exact URL/source-ID rules, manifest schema, reducer events, optimistic hashes, and canonical artifact-path contract.
- `.agents/skills/atlas-core/assets/source-summary-template.md` and `source-summary-quality-guide.md` — immutable frontmatter, seven-item semantic rubric, coverage/caveat requirements, and model-agnostic output contract.
- `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` — private 24-case calibration oracle; expected outcomes never enter model-visible prompts or relax for a provider.
- `.agents/skills/atlas-source/SKILL.md` — normalize-before-fetch/dedupe, `--resummarize`, `--promote-staged`, provenance branching, transaction recovery, and output behavior.
- `.agents/skills/atlas-route/SKILL.md` — complete route-upsert event, existing-topic bounds, and transaction-backed persistence.
- `scripts/atlas_url.py` (new) — sole canonical URL/source-ID implementation and CLI.
- `scripts/atlas_source.py` (new) — deterministic new/same-hash/changed-hash artifact merge CLI.
- `scripts/atlas_state.py` — pure registry validation/reduction plus transaction-recovery planning; no connector storage I/O.
- `scripts/atlas_quality.py` — deterministic calibration and source-summary validation.
- `scripts/verify_atlas_audit.py` (new) — durable closed-schema, hash-chain, ordering, and post-cleanup audit verifier.
- `tests/test_atlas_url.py`, `tests/test_atlas_source.py`, and `tests/test_verify_atlas_audit.py` (new), plus state, quality, harness-surface, and instance tests — identity, merge, recovery, audit, and surface coverage.
- `.agents/plans/2026-07-15-1156_todos-source-summaries-staging.md`, `vault://atlas/tmp/todos-source-summaries-2026-07-15/`, and `vault://atlas/summaries/sources/MANIFEST.md` — pass-1 closure record, frozen staging input, and living dedupe authority.
- `COMPARE/shared/tools/{build-calibration-input.py,validate-review.py,resolve-review.py}` — campaign-local exact calibration/review/resolution owners, hashed and deleted only after their behavior is embedded in the durable audit.

## Verification

```bash
python3 -m unittest \
  tests.test_atlas_url tests.test_atlas_source tests.test_atlas_state \
  tests.test_atlas_quality tests.test_verify_atlas_audit \
  tests.test_atlas_harness_surface tests.test_atlas_instance
python3 -m unittest discover -s tests -p 'test_atlas*.py'
python3 "$APP_ROOT/scripts/atlas-instance.py" check --name atlas
python3 "$APP_ROOT/scripts/atlas_url.py" normalize \
  --url 'https://twitter.com/example/status/1?foo=a&s=20&utm_source=x&bar=b#frag'
```

Expected normalization is canonical URL `https://x.com/example/status/1?foo=a&bar=b` and source ID `abca97778de4`. Campaign proof requires: 478/478 deterministic pass-1 validations; 24/24 calibration per lane; 30 OMP and 30 Grok passing candidate records; 30 pairwise and 30 baseline decisions; seven-item decisions for all 477 selected rows; exactly 477 indexed promotion rows; one terminal source-upsert and route result per row; clean state/instance checks; exact living-count reconciliation; and an independently revalidated archived audit root.

## Assumptions & contingencies

- The active `atlas` connector remains the only storage boundary. Host filesystem paths may appear in run metadata for CLI transport, never in product contracts, registry rows, artifacts, or audit rows.
- `STAGING` remains immutable after T1 closure and available through T11 approval. A missing or changed staged input blocks the affected task; it is never reconstructed from pass-1 prose.
- The installed OMP and Grok versions must accept the exact isolation/model flags. T5 blocks a lane if either preflight fails; no provider adapter, model fallback, tool enablement, or reduced effort is allowed.
- Provider API network is required for model calls, and `/atlas-source --capture-evidence` may fetch the named source. Candidates/reviewers receive no model-exposed network/filesystem tools. Transport retries follow the exact per-generation `t0..t2` cap; artifact repairs follow their separate generation cap.
- Any T4 identity/hash mismatch blocks the fixed cohort. A T6-T9 generated mismatch preserves the attempt, marks that candidate ineligible, and uses only the defined repair path. A T10 identity/content mismatch stops or returns to T9; living identity is never rewritten in place without explicit migration.
- Model prose is nondeterministic; reproducibility comes from fixed prompt/model/effort bytes, immutable attempts, exact validators/resolvers, and preserved selection lineage, not an expectation of byte-identical independent generations.
- Contract regression rejects the proposed snapshot and retains the prior passing one. Never weaken a fixture or expected outcome to make a provider pass. The two-iteration cap is global across T8 and T9.
- The connector does not promise a multi-file atomic write. T3's acknowledged prepared record, exact backups, fixed order, hash verification, recovery truth table, and rollback are mandatory. One clean optimistic retry is allowed; a second conflict, unrecognized hash, or malformed transaction state stops without force-writing.
- Concurrent living writes are allowed between evaluation phases. Snapshot drift never triggers silent repartition: T10 returns to T9 snapshot/fresh-evidence finalization and emits a new immutable map version.
- The active repository plan with a reread-verified audit block is durable before cleanup because destructive operations touch only the two vault temporary roots. Archiving occurs after cleanup and revalidates the same root.
- Cleanup is destructive and last. No temporary tree is removed until living reconciliation is clean, the active-plan audit root validates, and the user explicitly approves the named paths.
