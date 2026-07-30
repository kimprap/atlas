# Atlas Evaluation Loop

**Datetime**: 2026-07-29-2056
**Scope**: Manual Atlas framework evaluation: bounded bound-instance reads, isolated temporary mutation cases, local validation, and ignored product-local reports.
**Summary**: This plan grants future execution authority only. It defines a manual, revision-bound evaluation loop for the Atlas framework; it does not implement or activate that loop now.
**Status**: PENDING

## Context

The evaluator measures product behavior without deriving bound-instance write authority from findings. `.agents/ARCHITECTURE.md` remains the canonical framework owner; this plan and generated reports are neither Atlas evidence nor write authority. The loop is manual: cadence may trigger a human-run evaluation, never a scheduler or autonomous workflow.

## Tasks

- [ ] T1. Rebind and accept the evaluation subject
- [ ] T2. Establish the product evaluation contract
- [ ] T3. Implement the local validator and manual entrypoint
- [ ] T4. Implement the five evaluation lanes
- [ ] T5. Enforce the report and comparison contract
- [ ] T6. Prove the first baseline and lifecycle

## T1. Rebind and accept the evaluation subject

While this plan is `PENDING`, define one lexicographically sorted evaluation-member set. Use it unchanged for activation hashes, suite/report validation, cache invalidation, and comparison; hash raw bytes with SHA-256. Before a planned member exists, bind it as the literal `absent` state rather than omitting it:

```text
.agents/AGENTS.md
.agents/ARCHITECTURE.md
.agents/commands/atlas-eval.md
.agents/skills/atlas-audit/SKILL.md
.agents/skills/atlas-core/SKILL.md
.agents/skills/atlas-core/assets/evals/agent-tooling.json
.agents/skills/atlas-core/assets/evals/atlas-evaluation-report.schema.json
.agents/skills/atlas-core/assets/evals/atlas-framework-evaluation.json
.agents/skills/atlas-core/assets/evals/source-summary-quality.json
.agents/skills/atlas-core/assets/markdown-registry-contracts.md
.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md
.agents/skills/atlas-core/assets/source-summary-quality-guide.md
.agents/skills/atlas-core/assets/topic-research-quality-guide.md
.agents/skills/atlas-eval/SKILL.md
.agents/skills/atlas-source/SKILL.md
.agents/skills/atlas/SKILL.md
.gitignore
scripts/atlas_connector.py
scripts/atlas_eval.py
scripts/atlas_quality.py
scripts/atlas_source.py
scripts/atlas_state.py
scripts/atlas_tool.py
```

Call current façade capabilities and bind only its exposed `adapter`, `logical_root`, and sorted `operations`. Require `vault.read`, `vault.list`, `vault.hash`, `vault.digest_tree`, `source.snapshot_active`, `quality.prepare_calibration`, `quality.validate_calibration`, `quality.validate_summary`, and `state.validate`, plus the exact mutation operations declared by each isolated suite case before that case runs. Require product/bound architecture byte identity, clean `state.validate`, clean named instance check, and architecture plus all four registry revisions. Do not parse a profile file or infer profile, instance, or connector labels in this task.

Curate and present for one user acceptance a revision-bound corpus of at most 25 active source artifacts: up to five each from nonempty stable/high-evidence, moving/watch, valid aggregate-or-thin, recently added-or-resummarized, and source-kind/host-diversity strata. Add at most six current topics spanning every nonempty coverage state and recent refreshes. Deduplicate sources by source ID and topics by topic ID; retain each selection rationale. Inaccessible/error/no-write behavior belongs only to sealed workflow cases, never to a manufactured living-corpus record. A passing logical-root rebind plus accepted corpus changes this plan to `IN_PROGRESS`; otherwise it remains `PENDING`. Invalidate any reused report/cache when a member, architecture, registry, capability, corpus, or subject revision changes.

## T2. Establish the product evaluation contract

Update `.agents/ARCHITECTURE.md` first with a manual Evaluation mode: bound-instance reads only; mutation cases only in fresh OS-temporary instances/profiles; generated reports only in ignored product-local `.atlas-eval-results/`; findings grant no bound write authority. Extend the read-only capabilities result from `{adapter,logical_root,operations}` to exactly `{adapter,binding:{profile,instance,connector},logical_root,operations}`. The binding strings are non-secret logical identity; physical roots and credentials remain hidden. Update `atlas-core` and `markdown-registry-contracts.md` before implementation.

Create `.agents/skills/atlas-core/assets/evals/atlas-framework-evaluation.json` with exactly `schema_version: 1`, `suite_id: "atlas-framework"`, `description`, `product_members`, `required_capabilities`, `hard_gates`, `source_quality`, `topic_quality`, `workflow_cases`, and `comparison`. `product_members` exactly equals the T1 ordered list; `required_capabilities` is sorted and unique. Each hard gate is `{id,executor:"command"|"facade",request,expected}`; command requests are argv arrays, façade requests are version-1 envelopes, and expected contains only applicable `exit_code`, `ok`, and `finding_count`. `source_quality` names `source-summary-quality.json`, `atlas-source --capture-evidence`, the seven dimensions, `max_subjects: 25`, and cache keys `suite_revision|corpus_sha256|subject_id|subject_revision|capture_sha256`. `topic_quality` names its fixed dimensions and `max_subjects: 6`; workflow cases name isolated temporary-profile contracts. `comparison` declares matching bindings, blinded A/B review, hard-failure precedence, and no aggregate score.

## T3. Implement the local validator and manual entrypoint

Extend `scripts/atlas_connector.py` and `scripts/atlas_tool.py` so `capabilities` returns the exact T2 shape from the resolved profile dataclass. Add connector/tool tests for exact logical binding values and absence of a physical root or credentials. Re-run capabilities before the first corpus/report read, require all suite-declared operations, and bind `{profile,instance,connector}` only from that response.

Add dependency-free `scripts/atlas_eval.py` with public `validate_suite(data: object) -> dict`, `validate_report(data: object) -> dict`, `compare_reports(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict`, and canonical sorted-key compact JSON plus LF output. Its CLI is exactly `validate-suite --input <path>`, `validate-report --input <path>`, and `compare --baseline <path> --candidate <path> --output <path>`. Validation exits 0 for schema-valid input and 2 for invalid input. `compare` exits 0 only for compatible `eligible`, 1 for compatible `ineligible|inconclusive`, and 2 for invalid or incompatible bindings. It imports only the standard library and performs no vault, profile, network, or model work.

Create `.agents/skills/atlas-eval/SKILL.md` with `name: atlas-eval`, a manual-evaluation trigger description, and `disableModelInvocation: true`. It reads architecture, `atlas-core`, operating guardrails, suite, report schema, and quality guides, then alone orchestrates façade reads, fresh semantic reviewers, isolated temporary profiles, local report assembly, and cleanup. Add a thin `.agents/commands/atlas-eval.md`; register it in `.agents/AGENTS.md` and `README.md`. Its forms are `/atlas-eval baseline --suite atlas-framework [--output <path>]`, `/atlas-eval run --suite atlas-framework [--reuse-from <report>] [--output <path>]`, and `/atlas-eval compare --baseline <report> --candidate <report> [--output <path>]`. Explicit output must stay under `.atlas-eval-results/` and reject escaping paths.

Extend `/atlas` with one exact row: an explicit `atlas-framework` baseline/run/compare selects `atlas-eval`; one-shot health, registry/source-quality inspection, and calibration remain `atlas-audit`; unresolved `Evaluate Atlas quality` asks before an owner and recommends one-shot read-only audit. Add sealed `atlas-router-eval` and `atlas-router-audit-eval-ask` cases to `agent-tooling.json`, using the current exact router-result shape and a ten-owner forbidden set. The fixtures are:

```json
{"request":"Run the atlas-framework candidate evaluation using .atlas-eval-results/baseline.json."}
```

```json
{"first_owner":"atlas-eval","ask_required":false,"recommended_choice":null,"router_write_set":[],"forbidden_owners":["atlas-acquire","atlas-answer","atlas-audit","atlas-index","atlas-migrate","atlas-refresh","atlas-research","atlas-route","atlas-source"]}
```

and:

```json
{"request":"Evaluate Atlas quality."}
```

```json
{"first_owner":null,"ask_required":true,"recommended_choice":"one-shot-read-only-audit","router_write_set":[],"forbidden_owners":["atlas-acquire","atlas-answer","atlas-audit","atlas-eval","atlas-index","atlas-migrate","atlas-refresh","atlas-research","atlas-route","atlas-source"]}
```

Both use the existing route-only prompt and never execute a child. Add `tests/test_atlas_eval.py` for valid/invalid suite and report shapes, canonical output, safe/exclusive output paths, every CLI exit branch, incompatible bindings, hard-failure precedence, semantic regression/preference/tie verdicts, and unknown-key/path/capability/product-member rejection. Extend harness-surface tests so `atlas-eval` and `atlas_eval.py` receive thin-command, provider-neutral, and dependency-free checks. The skill—not `scripts/atlas_eval.py`—owns every Ask, model, and vault action.

## T4. Implement the five evaluation lanes

1. **Deterministic whole-state hard gates.** Run complete product tests, instance check, architecture byte identity, registry/state validation, source/manifest/route/relation consistency, topic freshness derivation, managed markers, applied-pass existence, source-artifact-only evidence, empty answer write set, temporary-fixture hygiene, and product/bound write-set equality.
2. **Bounded source quality.** On every baseline/run invoke `atlas-source --capture-evidence <canonical-url> --output-root <fresh-os-temporary-root>` for each accepted source, bind canonical capture SHA-256/content hash to the artifact revision, then apply the existing seven dimensions. Reuse a semantic row only after a new capture matches its capture hash and all T3 cache keys. If capture is unavailable, non-text, or insufficient, create one `blocked` workflow boundary row and no seven-dimension grades; never use old prose as evidence or write living state. Record product/bound digests before and after capture, remove every capture root, and treat cleanup failure as a hard failure.
3. **Topic quality.** For each accepted current topic, independently record `pass|issue|inconclusive` for claim-to-source faithfulness, admitted-set coverage, contradiction handling, gap honesty, confidence coherence, recommendation usefulness, caveat preservation, evidence-map completeness, and proportionality/redundancy. Every issue cites exact topic/source anchors; no aggregate score is legal.
4. **Isolated workflow regressions.** Reuse temporary-profile/unit-test seams for inaccessible/non-text/insufficient no-write recovery, aggregate scope Ask, source dedupe, no-topic-match, route idempotence, dirty-answer halt, `dirty→refreshing→current`, partial refresh to `blocked`, recovery/successor behavior, managed-section preservation, source-only evidence rejection, cleanup, and write allowlists. Never run a mutation case on the bound profile.
5. **Baseline/candidate comparison.** Require identical suite/corpus/subject/dimension bindings, randomize A/B labels for a fresh independent semantic reviewer, record dimensions separately, and make any hard failure ineligible regardless of semantic preference.

## T5. Enforce the report and comparison contract

Create a report schema that rejects unknown keys and requires exactly `schema_version: 1`, `kind: "atlas-evaluation-report"`, `run_id` (`YYYYMMDDTHHMMSSZ--atlas-framework--baseline|candidate`), `created_at` (UTC RFC-3339 seconds), `mode:"baseline"|"candidate"`, `suite:{id,revision}`, `product_members:[{path,sha256}]`, `bound:{profile,instance,connector,logical_root,architecture_revision,registry_revisions:{manifest,vocab,topics,relations}}`, `corpus:{sha256,members}`, `lanes:{hard_gates,source_quality,topic_quality,workflow}`, `hard_gate_status:"pass"|"fail"|"blocked"`, `write_sets:{product:{before,after},bound:{before,after},temporary:{before,after}}`, `cleanup:{status:"pass"|"fail",temporary_roots}`, and `refinement_packets`.

Corpus members are `{kind:"source"|"topic",id,path,revision,strata,rationale}` sorted by kind then ID. Hard-gate/workflow rows are `{id,status:"pass"|"fail"|"blocked",evidence,findings}`. Available-source rows are `{subject_id,subject_revision,capture_sha256,dimension,status:"pass"|"issue"|"inconclusive",evidence,findings,reused_from}`; topic rows omit `capture_sha256`. `reused_from` is null or a prior report hash. Every source has exactly seven dimension rows with one capture hash, or no dimension rows plus exactly one `blocked` workflow row `source-capture:<source-id>`; blocked capture is never graded from old prose. Each refinement packet is exactly `{finding,observed_runs,frequency,severity,evidence,reproduction,canonical_owner,smallest_candidate_change}`.

A comparison rejects unknown keys and contains exactly `schema_version: 1`, `kind: "atlas-evaluation-comparison"`, `comparison_id` (`YYYYMMDDTHHMMSSZ--atlas-framework--compare`), `created_at`, `baseline_sha256`, `candidate_sha256`, `bindings_match`, `label_map`, `hard_regressions`, `semantic_changes`, and `verdict`. Compatibility requires identical suite ID/revision, corpus SHA-256, member IDs/revisions, and dimension sets. `label_map` is exactly `{A:"baseline"|"candidate",B:"baseline"|"candidate"}` with opposite values; `hard_regressions` is sorted unique strings. Each semantic change is `{subject_id,dimension,baseline_status,candidate_status,preference:"baseline"|"candidate"|"tie"|"inconclusive",reason}` sorted by subject then dimension. A hard regression is always `ineligible`; otherwise return `eligible` only for a candidate preference with no hard failure, and `inconclusive` for ties or unavailable comparison.

## T6. Prove the first baseline and lifecycle

First run complete product tests, suite/report validator tests, transport calibration, and every isolated mutation case against fresh OS-temporary profiles. Record product/bound preflight digests, but do not claim architecture identity or emit a baseline while product/bound architecture differs. Present one exact approval gate with the capability-returned binding tuple, product and bound architecture revisions, candidate product hash, and write set `vault://atlas/ARCHITECTURE.md` only. On approval, halt `atlas-eval`; an executor outside the read-only evaluation skill runs the named `sync-framework` for that approved target. Re-run capabilities and all binding checks after sync.

Only after sync, run complete bound-read-only deterministic hard gates, fresh source captures, topic reviews, and isolated-lane receipts; emit and validate the first baseline from that post-sync run. Require unchanged product and living `summaries/`/`.atlas/` digests across read-only work, only declared temporary effects for isolated/capture work, proven cleanup, architecture byte identity, and a clean named instance check. Create a schema-valid candidate self-comparison fixture with baseline-equivalent bindings and lane content but required different run metadata, requiring `inconclusive` and exit 1. Compare baseline with a compatible synthetic candidate containing one declared hard regression, requiring `ineligible` and exit 1. Archive reports only under `.atlas-eval-results/`; do not add them to Atlas state.

## Critical anchors

- `.agents/ARCHITECTURE.md` — canonical framework and future manual Evaluation mode owner.
- `scripts/atlas_connector.py` and `scripts/atlas_tool.py` — qualified capabilities and logical binding owner.
- `scripts/atlas_quality.py`, `scripts/atlas_source.py`, and `scripts/atlas_state.py` — existing deterministic quality, capture, and state owners.
- `.agents/skills/atlas-core/assets/evals/agent-tooling.json` and `source-summary-quality.json` — sealed calibration contracts.
- `.agents/skills/atlas/SKILL.md` — first-owner router; future `atlas-eval` extension point.
- `.agents/plans/archive/2026-07-14-1337_atlas-evaluation-continuous-research.md` — closed historical predecessor; do not resurrect its implementation.

## Cadence and constraints

Run deterministic audit after nontrivial Atlas changes and monthly; bounded semantic review after 25 new/changed sources or five topic refreshes; full isolated lanes before and after framework behavior changes; and immediate regression execution after any integrity, recovery, citation, or false-completion incident. Cadence creates no scheduler or counters.

Do not add `AGENDA.md`, agenda migration, cron/launchd, continuous acquisition, automatic refresh/synthesis/mutation, provider SDK/runtime dependency, host adapter set, second pending-work queue, or a copied 409-line runner design. This plan does not depend on `eng-flow`.

## Verification / Done criteria

- [ ] The accepted T1 member set and all bound revisions/capabilities are recorded without parsing profile files.
- [ ] The complete suite/report schema, validator, manual skill/command, and calibration fixtures accept only their declared contracts.
- [ ] Bound-instance reads leave product, `summaries/`, and `.atlas/` digests unchanged; all mutation cases use fresh OS-temporary instances/profiles and prove cleanup.
- [ ] The first post-sync baseline and required comparison exit branches are schema-valid and observed.

## Assumptions and fallbacks

- A failed logical-root rebind, missing required capability, architecture mismatch, unaccepted corpus, or failed hard gate blocks activation and report emission; it does not create a fallback profile or write path.
- Inaccessible source capture creates the one declared blocked workflow row; it never grades old artifact prose.
- The user approval in T6 is the only authorization for the named product-owned architecture snapshot sync. No report finding authorizes a bound mutation.
