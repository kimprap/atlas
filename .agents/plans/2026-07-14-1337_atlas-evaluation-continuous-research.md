# Atlas Evaluation and Continuous Research

**Datetime**: 2026-07-14-1337
**Scope**: Atlas product evaluation runner, first real eval corpora, human-approved research agenda, and bounded acquisition scheduler
**Summary**: Add reproducible baseline-versus-candidate evaluation using the completed AI coding workflow’s T5 cases, then add an explicit agenda and acquisition-only scheduler path whose behavior is covered by the same isolated eval system.
**Status**: PENDING
## Tasks

- [ ] T1. Resolve the completed AI coding workflow corpus
- [ ] T2. Implement the isolated Atlas eval runner
- [ ] T3. Materialize workflow and Atlas eval suites
- [ ] T4. Add research-agenda architecture and contracts
- [ ] T5. Implement agenda, acquisition, audit, and migration workflows
- [ ] T6. Add continuous-research regression cases
- [ ] T7. Verify, preflight, sync the contract, migrate, and record the baseline


## Context

Atlas needs a product-level evaluation system and an approved continuous-research loop that can be iterated from observed use rather than anecdotes. The first corpus will reuse the AI coding workflow plan’s T5 routing, transition, transport, cleanup, and disposable end-to-end cases, augmented by the concrete friction already observed: no persisted research agenda, no baseline-versus-candidate runner, and current checks that prove structure but not research quality or operator usability. The end state is an isolated eval runner with hard conformance gates and multidimensional reports, plus an explicit human-approved research agenda that a scheduler can use for bounded acquisition without automatic taxonomy promotion or synthesis.

## Approach

### T1. Resolve the completed AI coding workflow corpus

1. Before any product edit, locate exactly one completed copy of `2026-07-13-2349_ai-coding-workflow.md`: prefer `.agents/plans/archive/2026-07-13-2349_ai-coding-workflow.md`, otherwise use the active `.agents/plans/` path. Require `Status: DONE`, all T1–T6 checkboxes completed, and a completion summary naming the accepted public prefix, support-core directory, and its live `evals/evals.json`. If the plan is still pending/in progress, both copies exist, or the completion summary is ambiguous, stop this plan before edits; the source cases are not executable gold yet.
2. Resolve these execution values mechanically from the completed decision table, authored file list, live core, and completion summary:
   - `WORKFLOW_CORE`: absolute accepted support-core directory.
   - `WORKFLOW_PREFIX`: accepted public prefix without the trailing hyphen.
   - `WORKFLOW_REVISION`: recorded implementation revision or completion timestamp when no commit exists.
   - `WORKFLOW_PUBLIC_SKILLS`: exact accepted public skill names plus the support-core name.
   - `WORKFLOW_REFERENCE_URIS`: every authored `skill://<core>/references/<file>.md` URI.
   - `WORKFLOW_STAGE_MAP`: source case IDs 1–14 mapped to the accepted public skill, expected Stage value, and expected Next stage from the persisted T3 decision table. Multiple semantic roles may map to one accepted skill; if any source case has no owning accepted stage, stop because the prerequisite left behavior implicit.
3. Read `${WORKFLOW_CORE}/evals/evals.json` and require the live craft-skill envelope `skill_name` plus `evals[]` entries with `id`, `prompt`, `expected_output`, `files`, and `assertions`. Require source case IDs 1–14 from T4.7; names inside prompts may reflect the accepted T3 table. Do not copy those prompts into Atlas.
4. Record the T4/T5 handoff-name mismatch as required adapter behavior: legacy `Invoked skills` maps losslessly to `required_skills` and an empty `optional_skills`; when the accepted T5 output already separates required/optional arrays, preserve them. Normalize singular/plural durable and temporary artifact labels to arrays and missing `Inputs`/`Checks` to explicit empty arrays. The normalized result contract is:

   ```json
   {
     "stage": "string",
     "mode": "string",
     "inputs": ["string"],
     "required_skills": ["string"],
     "optional_skills": ["string"],
     "durable_artifacts": ["string"],
     "temporary_artifacts": ["string"],
     "cleanup_owner": "string",
     "checks": ["string"],
     "exit_criterion": "string",
     "next_stage": "string",
    "outcome": "continue|halt|complete",
    "details": {
      "acceptance_gate": "not_required|pending|accepted|rejected",
      "dependency_edges": [{"from": "string", "to": "string"}],
      "verification_events": ["test-red-before-production-edit|test-green-after-production-edit|diagnosis-before-edit|non-tdd-exception-declared|blocker-returned|no-false-completion|canonical-contract-not-invented|manual-stage-not-invoked"],
      "review_axes": {
        "spec": "not_run|pass|fail|inconclusive",
        "standards": "not_run|pass|fail|inconclusive"
      },
      "cleanup": "not_required|pending|complete|blocked",
      "delivery": "not_applicable|blocked|proposed|completed"
    }
   }
   ```

### T2. Implement the isolated Atlas eval runner

1. Update `.agents/ARCHITECTURE.md` first with a product-evaluation boundary: tracked suite/schema/fixture/adapter assets and the runner live in the app; generated reports are ignored product-development state; eval fixtures/results are never living research or source evidence; mutation cases use a disposable connector bound to an OS-temporary instance; live-instance cases are explicitly read-only; hard conformance, research quality, efficiency, and usability remain separate dimensions with no aggregate score. Add `evals/schema.json` as the owner of case/report wire shapes in the architecture source-of-truth table.
2. Add exact `.gitignore` entries `evals/results/` and `node_modules/`; create `package.json` with exactly `{ "private": true, "type": "module", "dependencies": { "@oh-my-pi/pi-coding-agent": "16.5.0" } }`, run `bun install` once to generate tracked `bun.lock`, and require every later install to use `bun install --frozen-lockfile`; create `evals/schema.json`, `scripts/atlas-eval.py`, `tests/test_atlas_eval.py`, and `evals/adapters/omp-eval-{driver,guard,vault,agenda}.ts` with one Bun test beside each adapter. Python remains stdlib-only. The pinned SDK is the one justified runtime dependency; do not add another package tree or package script.
3. Make `evals/schema.json` the single machine-readable contract for suites, reports, comparisons, and manual semantic-review verdicts:
   - Suite keys: `schema_version: 1`, `suite_id`, `suite_version`, `description`, `required_variables`, `subject_files`, `cases`. Each `subject_files` entry is `{ "key": "<logical stable key>", "path": "<variable-expanded path>" }`; hash sorted `key + NUL + file-bytes`, never an absolute host prefix, into `subject_hash`.
   - Case keys: `id`, `title`, `gate: hard|advisory`, `dimensions` from `conformance|research_quality|efficiency|usability`, `vault_mode: none|isolated|live-readonly`, `host_adapters: []|["agenda"]`, `fixture`, `steps`, `expected`. `host_adapters: ["agenda"]` is legal with `isolated` for full disposable agenda behavior and with `live-readonly` for read-only `status|capabilities`.
   - `fixture`: `atlas_instance: true|false`, `files` (relative-path→UTF-8 body), `copy` entries (`source`, `destination`), and optional `git_baseline` (`branch`, `message`, `user_name`, `user_email`). `atlas_instance: true` provisions `<case-root>/instances/atlas` with `scripts/atlas-instance.py create --instances-root <case-root>/instances --name atlas` before applying fixture overrides.
   - Every step requires `id`, `driver: process|omp`, `cwd: app|case|workflow-core`, `env`, and `timeout_seconds`. A `process` step additionally requires `argv` (array only) and forbids `prompt`, `prompt_source`, and `allowed_tools`. An `omp` step forbids `argv`, requires nonempty built-in `allowed_tools`, and requires exactly one of `prompt` or `prompt_source`. The Python runner starts `bun evals/adapters/omp-eval-driver.ts`, sends one validated JSON config on stdin (`cwd`, resolved `prompt`, built-in `tool_names`, exact `extension_paths`, exact `extension_tool_names`), and enforces the OS-process timeout. Extension paths are guard; plus vault for isolated mode; plus agenda when `host_adapters` is `["agenda"]`. Extension tool names are `[]` without a host/vault adapter, `["eval_vault"]` for ordinary isolated mode, `["eval_vault","eval_agenda"]` for isolated agenda mode, or `["eval_agenda"]` for live-readonly agenda mode. `prompt_source` is exactly `{ "type": "craft-skill-eval", "path": "<expanded path>", "source_eval_id": <integer> }`.
   - Expected keys: `exit_code`, `result_fields`, `output_contains`, `output_excludes`, `files_exist`, `files_absent`, `allowed_changed_paths`. `result_fields` is an exact recursive match after normalization; extra or missing keys fail. The workflow handoff `details` object uses exactly the enums/edge shape in T1.4, making acceptance, dependency, red→green/diagnosis/exception events, split review axes, cleanup, delivery, and near-miss behavior machine-checkable. Normalized skill/artifact arrays sort lexically; dependency edges, inputs, checks, and verification events preserve declared order. All omitted collections become empty arrays.
   - `files_exist`/`files_absent` are exact POSIX-relative file paths. Each `allowed_changed_paths` entry is an anchored POSIX-relative pattern: literal segments match exactly, `*` matches one or more non-`/` characters within one segment, and a terminal `/**` matches that directory and descendants; no other metacharacters are legal. After fixture and git-baseline setup, recursively snapshot every file under the whole case root (`none`) or instance root (`isolated`), then classify create/modify/delete. Every changed path must match at least one allowed pattern; newly created undeclared paths are never omitted. Runner prompts/reports stay outside the snapshot root, so there are no implicit ignored paths.
   Reject unknown keys, duplicate case/step IDs, undefined `${VARIABLE}` placeholders, fixture/copy paths escaping the case root, a prompt plus prompt_source, non-array commands, invalid driver/tool combinations, invalid path patterns, or a custom results root outside `<app>/evals/results/`.
4. Implement `omp-eval-driver.ts` with the pinned SDK. Validate stdin/config and create one session with explicit `cwd`, `discoverAuthStorage()`/`ModelRegistry` (no credential copy), `Settings.isolated({ "speechgen.enabled": false })`, `SessionManager.inMemory()`, `toolNames`, `customTools: []`, `preloadedCustomToolPaths: []`, `enableMCP: false`, `enableLsp: false`, `disableExtensionDiscovery: true`, and `additionalExtensionPaths` from the validated repo-owned list. The empty preloaded-path array is required: in SDK 16.5.0, `customTools: []` is additive and does not disable filesystem custom-tool discovery. After creation and before the prompt, call `session.setActiveToolsByName()` with exactly validated `tool_names + extension_tool_names`, then require `session.getActiveToolNames()` to equal that set. This removes the SDK’s always-registered `generate_image` auxiliary tool and every other undeclared tool from the active system prompt; an unexpected active tool or activation mismatch exits `2` before the prompt. Preserve normal skill/rule/context discovery, stream assistant text to stdout, report selected model metadata, execute exactly one `session.prompt()` call, and always dispose.
5. Implement `omp-eval-guard.ts` for every OMP step. Require `ATLAS_EVAL_ALLOWED_TOOLS` and register a fail-closed `tool_call` hook that blocks every tool name outside that comma-separated set. Count attempted/allowed/blocked calls by tool name and atomically write them on `agent_end` to required `ATLAS_EVAL_METRICS_PATH`, outside the snapshot root; capture provider usage only when exposed. The runner passes exactly the case’s built-ins plus validated `extension_tool_names`; no adapter tool is implicitly allowed. The runner measures elapsed time/stdout/stderr bytes independently. If session creation fails or the OS timeout kills the driver before `agent_end`, the metrics file may be absent: record `guard_metrics_status: "missing"` with all three tool-count maps and provider usage as `null`, mark the step `error`, and never interpret missing data as zero or a passing guard.
6. Implement `omp-eval-vault.ts` as the disposable connector for `vault_mode: isolated`:
   - register one custom tool named `eval_vault` with `{ op: "read|list|conditional_replace", path: "vault://atlas/<relative>", body?: string, expected_revision?: "missing|sha256:<hex>" }`;
   - require `ATLAS_EVAL_VAULT_ROOT` and `ATLAS_EVAL_LOCK_ROOT`, resolve only the `vault://atlas/` host beneath the vault root, reject query/fragment/path traversal, and return relative paths plus full-file `sha256:<hex>` revisions;
   - when `ATLAS_EVAL_AGENDA_EXCLUSIVE=1`, reject every operation whose normalized target is `vault://atlas/summaries/registry/AGENDA.md`; agenda-mode cases may access that file only through `eval_agenda`;
   - make `read` and `conditional_replace` acquire the same per-target lock, implemented as an atomic lock-directory creation under the runner-owned lock root outside the snapshot. Wait at most five seconds for the lock, then return an error; always remove it in `finally`, while case cleanup removes crash residue;
   - under that lock, `conditional_replace` hashes the full current bytes immediately before replacement, returns `conflict` unless the revision equals `expected_revision` (`"missing"` only when absent), writes a sibling temporary file, flushes it, atomically renames it, flushes the parent directory, and returns the new revision;
   - block every non-`eval_vault` tool whose serialized input contains `vault://atlas/` or the disposable root, so Atlas I/O cannot bypass the connector;
   - export pure path/hash/lock helpers for its test.
   Non-agenda isolated cases load guard plus vault, allow declared built-ins plus `eval_vault`, and state in the prompt that `eval_vault` is the only connector for logical Atlas paths. `disableExtensionDiscovery: true` plus the exact `additionalExtensionPaths` controls extensions; `preloadedCustomToolPaths: []` skips filesystem custom-tool scanning; the post-creation active-set reset excludes SDK auxiliary tools; and the guard remains the final call-time backstop. The adapters never consult the active personal profile.
   Add `omp-eval-agenda.ts` as a separate adapter loaded only for `host_adapters: ["agenda"]`. It registers `eval_agenda`, validates exact typed fields, invokes `scripts/atlas-agenda.py`, exposes no arbitrary command/body/path escape, and returns the script’s JSON/exit class unchanged. In `isolated` mode it accepts the T5.1 subcommands against `ATLAS_VAULT_PROFILE=<case-meta>/atlas-eval-profile.yml`, which the runner writes with connector `local-fs`, instance `atlas`, and an absolute disposable root. In `live-readonly` mode the runner first validates `../vault/config/profiles/local.yml` resolves local-fs instance `atlas`, passes that explicit profile, and the adapter accepts only `status` or `capabilities`; every mutation operation is rejected before process spawn. Isolated agenda cases state that `eval_agenda` is the only agenda path, use `eval_vault` for other Atlas paths, and allow both exact extension tools. Live agenda cases allow built-in `read` plus `eval_agenda`.
7. Implement these reusable symbols in `scripts/atlas-eval.py`:
   - `load_suite(path: Path, variables: dict[str, str]) -> dict`
   - `validate_suite(data: object) -> dict`
   - `materialize_fixture(case: dict, root: Path) -> None`
   - `run_step(step: dict, root: Path, env: dict[str, str]) -> dict`
   - `extract_marked_json(output: str) -> dict`
   - `evaluate_case(case: dict, step_results: list[dict], root: Path) -> dict`
   - `write_report(report: dict, results_root: Path) -> Path`
   - `compare_reports(baseline: dict, candidate: dict) -> dict`
8. Expose only:

   ```text
   python3 scripts/atlas-eval.py validate --suite <json> [--var NAME=VALUE ...]
   python3 scripts/atlas-eval.py run --suite <json> --label <slug> --revision <string> [--case <id> ...] [--var NAME=VALUE ...] [--results-root <path>] [--dry-run]
   python3 scripts/atlas-eval.py compare --baseline <report.json> --candidate <report.json> [--review-verdict <json>] [--results-root <path>]
   ```

   Default results root is `evals/results/`. Exit `0` for valid/all-hard-pass/no-regression, `1` for a hard case/regression, and `2` for invalid input, missing tools, incompatible reports, or unmet prerequisites.
9. For OMP steps, wrap the prompt with:

   ```text
   ATLAS_EVAL_RESULT_START
   {single JSON object}
   ATLAS_EVAL_RESULT_END
   ```

   Parse exactly one marked object. A malformed/additional marker is an error. Legacy T5 `Invoked skills` maps losslessly to `required_skills` with `optional_skills: []`; never infer optionality. Singular artifact labels become one-element arrays; missing Inputs/Checks become empty arrays.
10. Enforce vault modes:
   - `none`: reject `vault://atlas/` in case text/argv and load only the guard;
   - `isolated`: require `atlas_instance: true`, set `ATLAS_EVAL_VAULT_ROOT=<case-root>/instances/atlas`, `ATLAS_EVAL_LOCK_ROOT=<case-meta>/locks` outside the snapshot, and declared built-ins `["read"]`, then load guard plus vault. When `host_adapters` is `["agenda"]`, also set `ATLAS_EVAL_AGENDA_EXCLUSIVE=1`, load agenda, and create the disposable profile. The vault adapter rejects the agenda path in that mode; all non-agenda Atlas I/O goes through `eval_vault`, and agenda I/O goes through `eval_agenda`.
   - `live-readonly`: forbid fixtures and the vault adapter, require every OMP step to use built-ins `allowed_tools: ["read"]`, and require an empty changed-path expectation. Load guard only when `host_adapters` is empty. With `host_adapters: ["agenda"]`, prevalidate the bound local-fs `atlas` profile, load the agenda adapter in `status|capabilities`-only mode, include `eval_agenda` in the exact active/guard sets, and reject every mutation before subprocess spawn.
11. Run each case in its own temporary root. Snapshot the whole case root for `none` or `<case-root>/instances/atlas` for `isolated` after fixture/baseline setup and before steps; recursively evaluate create/modify/delete plus exact exit codes/results/output/files/allowed paths; always delete the working root. On failure, copy only stdout, stderr, normalized output, and diff metadata into results.
12. Write `report.json` and compact `report.md` with `schema_version`, run/suite IDs, suite version, label, revision, `subject_hash`, `case_pack_hash`, timestamps, available model/provider metadata, per-case statuses/artifact paths, and separate dimension summaries. Every step records exact keys `status: "pass|fail|error"`, `duration_ms`, `stdout_bytes`, `stderr_bytes`, `guard_metrics_status: "not_applicable|complete|missing"`, `attempted_tool_calls`, `allowed_tool_calls`, and `blocked_tool_calls` as name→count maps or `null`, and `provider_usage` as an exposed usage object or `null`. Process steps use `not_applicable` with all four guard/provider fields `null`. OMP `complete` requires a valid guard metrics file and non-null tool-count maps; OMP `missing` is legal only for a pre-`agent_end` error/timeout and forces `status: "error"`. Define `case_pack_hash` over canonical resolved-suite JSON, imported craft-skill prompts/expected outputs/assertions, fixture bytes, `evals/schema.json`, pinned package/lock, driver, guard, vault adapter, and agenda adapter/script for suites that use them, using logical keys rather than host prefixes. Missing provider usage is `null`, never zero. Do not emit one score.
13. `compare` requires equal suite ID/version, case IDs, `case_pack_hash`, and per-case gate/dimension declarations. Changed corpora require a fresh baseline under the new hash. A baseline hard-pass becoming candidate fail/error is a regression; any candidate hard failure exits `1`. For advisory outputs, write randomized A/B `review-packet.md`, private `mapping.json`, and `review-verdict.template.json`. Verdict keys are `schema_version`, `comparison_id`, `reviewer`, `dimensions` (`citation_faithfulness`, `coverage`, `gap_honesty`, `operator_utility`, each `A|B|tie|not_applicable`), `overall: A|B|tie`, and `notes`; semantic review never overrides hard failure.

### T3. Materialize workflow and Atlas eval suites

1. Add `evals/cases/ai-coding-workflow-t5.json`. It references `${WORKFLOW_CORE}/evals/evals.json` by source IDs 1–14 and writes the accepted `WORKFLOW_STAGE_MAP`, public-skill list, prefix, and reference URIs resolved in T1 into the tracked case expectations. It must not duplicate external prompts or retain a provisional name that differs from the accepted table.
2. Map all fourteen source cases to structured expected fields:
   - cases 1–4: shape modes, conditional `grilling`/`eng-prototype`, acceptance gates, artifact cleanup owner, and next stage;
   - cases 5–6: unresolved-preference halt and tracer-bullet dependency graph;
   - cases 7–9: TDD, diagnosis-before-edit, and explicit non-TDD exception;
   - cases 10–11: separate Spec/Standards axes and `INCONCLUSIVE` behavior;
   - cases 12–13: blocker return, no false completion, no invented canonical contract, cleanup, and proposed-only shipping;
   - case 14: natural-language near miss must not claim a manual workflow stage ran.
3. Add four aggregate T5 cases after the fourteen imported prompts:
   - `t5-discovery`: `grok inspect --json` finds exactly the T1 `WORKFLOW_PUBLIC_SKILLS`, each once, without a bundled-name collision.
   - `t5-resolution`: `omp read` resolves every URI in `WORKFLOW_PUBLIC_SKILLS` and `WORKFLOW_REFERENCE_URIS`.
   - `t5-native-transport`: Grok `/<accepted-public-skill>` and OMP `/skill:<accepted-public-skill>` no-write prompts receive arguments and load the same accepted core reference.
   - `t5-slugify-journey`: materialize T5’s exact Python fixture under a temporary root, create its local baseline commit, execute shape→plan→implement→review→finish, observe a new example fail before production edits, require all specified slugify examples to pass, forbid commit/push/PR after the baseline fixture commit, remove workflow-owned scratch/review artifacts, and delete the temporary repository.
4. Add `evals/cases/atlas-contracts.json` plus synthetic fixture overrides under `evals/fixtures/atlas-contracts/`. Every case uses `vault_mode: isolated`, provisions an Atlas instance, invokes the owning Atlas skill through OMP with `eval_vault`, and asserts the resulting temporary instance state—not a proposed write set. Cover source dedupe, no-topic-match without an edge, deterministic route rerun, route never writing topic `INDEX.md`, dirty answer halt, refresh `dirty→refreshing→current`, blocked partial refresh, freshness-cache recomputation, managed-section preservation, and answer’s empty write set.
5. Add `evals/cases/atlas-research-quality.json` plus entirely synthetic evidence under `evals/fixtures/research-quality/`; do not copy the personal Atlas topic or its materialized external sources. Cases use isolated provisioned instances and execute `/atlas-research` behavior through OMP. Include supporting, irrelevant keyword-overlap, contradictory, and insufficient packets. Hard assertions require artifact IDs for substantive claims, no raw-URL/model-prior evidence, contradiction reflected in confidence/caveats, unresolved evidence in gaps, and actual writes confined to declared topic/pass paths. The pairwise packet grades citation faithfulness, coverage, gap honesty, and operator utility separately.
6. Add `evals/cases/atlas-live-readonly.json` as the first observational corpus over accumulated real state. Mark every case `vault_mode: live-readonly`; permit only built-in `read`, with `host_adapters: ["agenda"]` and read-only `eval_agenda` added only to the post-migration agenda-status case. Include full `/atlas-audit`, `/atlas-answer agentic-harness-architecture`, and `/atlas-agenda status`. Report source/topic/relation counts, freshness distribution, audit findings, current-answer availability, citation-artifact use, and agenda row count; any proposed write is a hard failure. Later representative topics are added explicitly as tracked cases rather than discovered by broad vault crawling.
7. Unit-test schema validation, vault-mode/host-adapter restrictions, variable substitution, external craft-skill loading, exact prompt precedence, result-marker parsing, fixture traversal rejection, disposable instance provisioning, allowed-write diffing, temp cleanup, report generation, portable hashes, comparison incompatibility, hard-regression detection, process-step `not_applicable` guard metrics, missing OMP guard metrics on pre-agent failure/timeout, and absence of an aggregate score. Bun tests prove SDK automatic extension discovery is disabled; only the exact validated `additionalExtensionPaths` load; `preloadedCustomToolPaths: []` skips filesystem custom-tool discovery; speech generation, MCP, LSP, and session persistence remain disabled; the post-creation active set equals declared built-ins plus exact extension tools and excludes `generate_image`; guard allowlisting works; the vault adapter enforces path isolation, strict locked conditional replacement, and agenda-path rejection in agenda mode; and the agenda adapter accepts only typed operations, runs full commands only against the disposable profile, exposes only `status|capabilities` in live-readonly mode, and leaves bound agenda bytes unchanged. Mock subprocesses in Python unit tests; focused agent suites run only in T7.

### T4. Add research-agenda architecture and contracts

1. Update `.agents/ARCHITECTURE.md` before downstream files:
   - add `summaries/registry/AGENDA.md` to the instance shape;
   - define `Research agenda` as approved future acquisition intent, distinct from `TOPICS.md` identity/freshness, `RELATIONS.md` pending evidence, and acquisition run provenance;
   - add `Agenda` mode, whose only direct write target is `AGENDA.md`;
   - add `Scheduled acquisition` mode, which reads approved agenda rows and delegates the existing acquisition/route write set: source artifacts, `MANIFEST.md`, one run log, source route status, `RELATIONS.md`, and derived topic dirty-cache fields;
   - define abandoned-run recovery as a restricted Scheduled acquisition path: for already materialized, provenance-matched sources it may use the existing route write set—source routing metadata/status, manifest route status, `RELATIONS.md`, and relation-derived topic dirty-cache fields—but may not append to the incomplete run log, create/delete source artifacts or manifest rows, or change source identity/evidence content;
   - require host vault mutation port operation `conditional_replace(path, expected_revision, body) -> new_revision|conflict` for every agenda mutation. Local OMP/Grok execution uses the product-owned strict adapter `atlas-local-fs-cas-v1` implemented by `scripts/atlas-agenda.py`; it compares a full-file SHA-256 revision while holding the per-agenda lock and performs one atomic replacement. The built-in hashline `edit` tool is explicitly not this port because it may recover stale hunks. Other connector kinds must provide an equivalently strict adapter or report mutation capability unavailable. Scheduled acquisition v1 is a single writer per instance, enforced by a persisted `running` claim before source work;
   - forbid scheduled taxonomy/topic creation, topic-answer patches, research passes, refresh, synthesis hooks, and a parallel pending-work queue.
2. Add `scaffold/summaries/registry/AGENDA.md` with frontmatter `schema_version: 1`, `note_type: atlas-research-agenda`, `managed_by: atlas`, and `last_updated: YYYY-MM-DD`, followed by this exact table; every agenda mutation updates `last_updated`:

   ```text
   Agenda ID | Topic ID | Question / gap | Scope type | Scope | Priority | Cadence | Source cap | No-change limit | No-change streak | Status | Approval | Approved at | In-flight run | Last run | Last outcome | Last run log | Next due
   ```

   Use exact enums:
   - `Scope type`: `query|feed|inbox|watchlist|repo-list|author-list`
   - `Priority`: `high|medium|low`
   - `Cadence`: `manual` or `P<n>D` where `n` is a positive integer
   - `Status`: `proposed|active|running|paused|blocked|completed|retired`
   - `Approval`: `pending|human`
   - `Last outcome`: blank or `changed|no-change|partial|blocked|abandoned`
   Agenda IDs are unique lowercase `agenda--<kebab-case>`. Table text is single-line trimmed Markdown with literal pipes escaped.
3. Add the schema and complete transition/concurrency contract to `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`:

   | Operation | Allowed from | Result |
   |---|---|---|
   | `propose` | missing ID | create `proposed/pending`; No-change streak = `0`; blank Approved at, In-flight run, Last run/outcome/log, and Next due |
   | `propose` | existing ID | error |
   | `update` with no changed value | `proposed|active|paused|blocked` | no-op |
   | priority-only `update` | `proposed|active|paused|blocked` | change only Priority and `last_updated`; retain status, approval, Approved at, No-change streak, Next due, and run history |
   | material `update` | `proposed|active|paused|blocked` | `proposed/pending`; clear Approved at and Next due; reset No-change streak to `0`; preserve Last run/outcome/log |
   | any `update` | `running|completed|retired` | error |
   | `approve` | `proposed/pending` | validate Topic ID; set `active/human`, Approved at = action date, Next due = action date for periodic or blank for manual |
   | `approve` | `active/human` | no-op |
   | `approve` | any other state | error |
   | `pause` | `active|blocked` | `paused`; clear Next due |
   | `pause` | `paused` | no-op |
   | `resume` | `paused|blocked` with retained human approval | revalidate Topic ID/bounds; set `active`; Next due = action date for periodic or blank for manual |
   | `resume` | `active/human` | no-op |
   | `recover --abandon-claim` | `running/human` whose In-flight run is absent | explicit human break-glass: set `active`, clear In-flight run, and make periodic cadence due on the action date |
   | `recover --abandon-claim` | `running/human` whose In-flight run exists but is schema-incomplete | preserve it byte-identical; run the deterministic provenance reconciliation below; set `blocked`, Last outcome = `abandoned`, Last run/log = recovery date/path; clear In-flight run only after the final conditional agenda replacement succeeds |
   | `recover --abandon-claim` | `running/human` whose In-flight run is complete | error; use `run`/`run-due` reconciliation |
   | `complete` | `active|paused|blocked` | `completed`; clear Next due |
   | `complete` | `completed` | no-op |
   | `retire` | `proposed|active|paused|blocked|completed` | `retired`; clear Next due |
   | `retire` | `retired` | no-op |
   | explicit `run` or selected `run-due` | `active/human`, with no `running` row | conditionally replace exact agenda snapshot with `running`, blank Next due, and reserved In-flight run path; start acquisition only after claim success |
   | `run`/`run-due` recovery | exactly one `running/human` row with its complete In-flight run log | reduce log, clear In-flight run, persist outcome, return without another acquisition |
   | `run`/`run-due` while claim lacks complete log | any `running` row | halt without new acquisition or agenda write |
   | any unlisted operation/state pair | any | error |

   Material fields are Topic ID, Question/gap, Scope type, Scope, Cadence, Source cap, and No-change limit. Priority is the only non-material editable field. Every mutation conditionally replaces the just-read whole-agenda revision; a conflict re-reads, reports competing state, and halts without retry/work. A host port without `conditional_replace` may run capabilities/status only. At most one row may be `running`. Reuse the existing acquisition-run layout and reserve `summaries/sources/runs/<YYYY>/<YYYY-MM>/<YYYY-MM-DD>--<agenda-id>--r<N>.md`, where `N` is one plus the largest existing suffix for that Agenda ID. Transition errors halt without writes; successful mutations update `last_updated`; no-ops write nothing. Pause/resume/complete/retire preserve approval/history. Claim/reconciliation/recovery alone change In-flight run; reconciliation or explicit abandoned recovery alone change Last run/outcome/log. `retired` is terminal.
   For schema-incomplete-log recovery, list source artifacts under `summaries/sources/artifacts/` and select only those whose valid frontmatter `acquisition_run` exactly equals the reserved In-flight run path. Stable-sort matches by `source_seq`. For each match, require its Source ID, canonical URL, actual logical artifact path, and content hash to agree with the existing `MANIFEST.md` row; mismatches become reported blockers and are not repaired. Rerun the existing deterministic route workflow for each valid match with acquisition-run logging suppressed, then recompute affected `TOPICS.md` dirty-cache fields from `RELATIONS.md`. Permit only the existing route write set: source routing metadata/status, manifest route status, relation edges, and derived cache fields. Do not create/delete source artifacts or manifest rows, alter source identity/evidence content, change the incomplete log, or infer candidates from its malformed body. If routing or cache recomputation fails, leave the agenda row `running` so the same explicit recovery can retry idempotently. After reconciliation completes, conditionally replace the original running claim with `blocked/abandoned`; a conflict also leaves the claim for a later explicit recovery.
4. After recovery finds zero `running` rows, select periodic `active/human` rows with `Next due <= as-of`, stable-sorted by priority `high→medium→low`, then Next due ascending, then Agenda ID. `run-due` requires a positive explicit limit and selects at most that many. `manual` cadence is never automatic but may run by explicit ID.
5. Define outcome reduction from the persisted acquisition run:
   - `changed`: at least one created/refreshed source and no blocked source; reset streak to 0;
   - `partial`: at least one created/refreshed source plus at least one blocked source; reset streak to 0;
   - `no-change`: no created/refreshed or blocked source; duplicates, rejected leads, and no-topic-match are allowed; increment streak and pause/blank Next due when it reaches No-change limit;
   - `blocked`: no created/refreshed source and at least one blocked source; set `blocked` and blank Next due.
   Every reduction starts from the matching `running` claim, sets Last run/outcome/log from the complete immutable log, and clears In-flight run. `changed`, `partial`, and below-threshold `no-change` return to `active`; periodic cadence computes Next due from completion date; manual leaves it blank.
6. Extend `.agents/skills/atlas-core/assets/research-library-templates.md`. New logs contain `agenda_id: ""`, `source_cap: 0`, `created_sources: []`, `refreshed_sources: []`, `skipped_duplicates: []`, `blocked_sources: []`, `rejected_sources: []`, and `deferred_by_bound: []`; legacy logs may omit these arrays, but agenda-backed runs populate all. Add `## Deferred by bound`. Write agenda-backed logs through sibling-temp plus atomic rename, so reserved path is absent or schema-complete; preserve any nonconforming incomplete final path for explicit recovery. Direct acquisition keeps blank agenda ID/source cap 0. Agenda `run-due` uses `trigger: cron`; explicit agenda `run` uses `trigger: manual`; direct-acquisition trigger semantics stay unchanged. No run body or agenda row contains synthesis.
7. Update `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md` to define continuous research v1 as approved-agenda acquisition/routing only. Keep scheduled refresh, automatic answer-before-refresh, and model synthesis deferred.

### T5. Implement agenda, acquisition, audit, and migration workflows

1. Add stdlib-only `scripts/atlas-agenda.py` and `tests/test_atlas_agenda.py`. The script owns agenda parsing/rendering, every T4.3 transition, due ordering, claim/reduction preparation, and local connector CAS; the skill remains the human-facing orchestrator. Resolve the binding from `ATLAS_VAULT_PROFILE` when set, otherwise `../vault/config/profiles/local.yml`; parse only the existing scalar YAML subset (`profile`, `instance`, `connector`, and nested `local_fs.root`), resolve relative roots from the vault repository, require instance `atlas` and connector `local-fs`, allow read-only `vault://atlas/ARCHITECTURE.md` only for capabilities, allow read/replace of `vault://atlas/summaries/registry/AGENDA.md`, and reject duplicate/unknown structural keys, aliases, traversal, or every other logical path.
   Implement adapter ID `atlas-local-fs-cas-v1` with full-byte revisions `sha256:<hex>`. For reads and mutations, acquire `fcntl.flock(LOCK_EX)` on `<tempdir>/atlas-agenda-locks/<sha256(real-agenda-path)>.lock`; while holding it, read/hash the whole agenda, compare the caller’s expected revision, render the full replacement, write/fsync a sibling temp file, `os.replace` it, fsync the parent directory, and return the new revision. A mismatch returns `conflict` before rendering or writing. All Atlas agenda writers must use this adapter; built-in hashline `edit` is forbidden. `capabilities` is read-only: it validates binding kind, POSIX lock support, adapter version, and a full-byte read of `vault://atlas/ARCHITECTURE.md` without creating the lock or writing.
   Expose only:
   ```text
   python3 scripts/atlas-agenda.py capabilities
   python3 scripts/atlas-agenda.py status [<agenda-id>]
   python3 scripts/atlas-agenda.py propose <all-fields> --expected-revision <sha256> --as-of <YYYY-MM-DD>
   python3 scripts/atlas-agenda.py update <agenda-id> <changed-fields> --expected-revision <sha256> --as-of <YYYY-MM-DD>
   python3 scripts/atlas-agenda.py transition <approve|pause|resume|complete|retire> <agenda-id> --expected-revision <sha256> --as-of <YYYY-MM-DD> [--actor human]
   python3 scripts/atlas-agenda.py recover <agenda-id> --abandon-claim --actor human --expected-revision <sha256> --as-of <YYYY-MM-DD>
   python3 scripts/atlas-agenda.py recover-finalize <agenda-id> --actor human --expected-revision <sha256> --as-of <YYYY-MM-DD>
   python3 scripts/atlas-agenda.py claim <agenda-id> --expected-revision <sha256> --as-of <YYYY-MM-DD>
   python3 scripts/atlas-agenda.py claim-due --expected-revision <sha256> --as-of <YYYY-MM-DD> --limit <positive-int>
   python3 scripts/atlas-agenda.py reduce <agenda-id> --expected-revision <sha256> --run-log <vault-path> --as-of <YYYY-MM-DD>
   ```
   `status` and every successful/no-op mutation emit one JSON object containing `adapter_id`, `revision_kind`, `revision`, `operation`, `outcome`, and the addressed row/claim payload when applicable. `claim-due` selects and claims at most one row per call; the skill repeats sequentially up to the user limit. `recover` finalizes an absent-log claim directly, returns `reconcile_required` plus ordered source IDs/revision for a schema-incomplete log without writing, and rejects a complete log; after the skill performs T4.3 reconciliation, `recover-finalize` conditionally records `blocked/abandoned`. Exit `0` for success/no-op, `1` for validation/state error, `2` for unavailable binding/capability, and `3` for revision conflict. Never retry a conflict.
   Unit tests cover strict profile parsing, byte-stable parse/render, every transition/no-op/error, due ordering and one-at-a-time claims, complete-log reduction, both abandoned-recovery branches, read-only capabilities, and CAS. The CAS race test starts two worker processes from the same reported revision, synchronizes them before replacement, and requires exactly one exit `0`/`new_revision`, one exit `3`/`conflict`, one resulting row mutation, and no lost competing update.
2. Add `.agents/skills/atlas-agenda/SKILL.md` with `disableModelInvocation: true` and a thin `.agents/commands/atlas-agenda.md` stub. The user interface is:

   ```text
   /atlas-agenda status [<agenda-id>]
   /atlas-agenda capabilities
   /atlas-agenda propose --id <agenda--slug> --topic <topic-id-or-blank> --question <text> --scope-type <enum> --scope <text> --priority <enum> --cadence <manual|P<n>D> --source-cap <positive-int> --no-change-limit <positive-int>
   /atlas-agenda update <agenda-id> [--topic <id>] [--question <text>] [--scope-type <enum>] [--scope <text>] [--priority <enum>] [--cadence <manual|P<n>D>] [--source-cap <positive-int>] [--no-change-limit <positive-int>]
   /atlas-agenda approve|pause|resume|complete|retire <agenda-id>
   /atlas-agenda recover <agenda-id> --abandon-claim
   /atlas-agenda run <agenda-id>
   /atlas-agenda run-due --as-of <YYYY-MM-DD> --limit <positive-int>
   ```

   Empty/status/capabilities are read-only. On local OMP/Grok, the skill invokes `scripts/atlas-agenda.py`; in isolated agenda evals, `eval_agenda` invokes the same script against the disposable profile. `capabilities` must report adapter ID `atlas-local-fs-cas-v1`, logical root, profile kind, instance ID, revision kind `sha256`, and `conditional_replace: available|unavailable` without writing. A profile declaration, optional `write(..., etag?)` documentation, or built-in hashline `edit` is insufficient. Before every mutation the skill obtains `status.revision` and passes it as `--expected-revision`; exit `3` reports the competing state and halts without retry. `approve`, `recover`, and `recover-finalize` require `--actor human`; because the skill has `disableModelInvocation: true`, it passes that flag only while executing the matching direct user-issued command, never from `run`/`run-due` or an inferred action. The script’s full replacement may change only `last_updated` plus the addressed row. Duplicate IDs, missing rows, invalid enums/bounds, nonexistent active Topic IDs, non-human approval/recovery attempts, illegal transitions, or malformed dates halt without writes.
3. `run`/`run-due` first call script `status`. More than one `running` row is an integrity error. If exactly one is running, a complete matching In-flight run is passed to `reduce` and the command returns without new acquisition; a missing/incomplete log halts and names explicit `recover --abandon-claim`. With zero running rows, call `claim` or sequential `claim-due`, then only after its strict conditional claim succeeds delegate separately to `skill://atlas-acquire` with the returned exact scope, cap, agenda ID, trigger, and reserved path. After the complete immutable log exists, call `status`, require the same claim, and pass its revision to `reduce`. Claim/reduction conflict halts without retry; post-log conflict is recoverable next invocation. Failure after claim but before a complete log leaves `running`; failure before claim leaves it byte-identical.
4. Extend `.agents/skills/atlas-acquire/SKILL.md` and its thin command description to accept `--agenda-item <id> --source-cap <n> --trigger <manual|cron> --run-log <reserved-vault-path>`. Validate the current `running` row, exact reserved path, and cap; enumerate in provider order; canonicalize/dedupe through `MANIFEST.md`; and materialize at most the first N new or materially changed sources. Unchanged duplicates do not consume the cap. Record remaining new/changed candidates under `Deferred by bound`, then use existing `atlas-source`/route behavior and persist the immutable run at the reserved path. Direct bounded queries remain supported without agenda arguments.
5. Extend `.agents/skills/atlas-audit/SKILL.md` read-only checks: agenda schema/enums/unique IDs; at most one `running` row; running rows require human approval and a valid reserved In-flight path; active rows require human approval/existing topic/valid bounds; due-date/cadence consistency; Last run-log references exist; a complete in-flight log is flagged for reconciliation; `abandoned` requires a blocked row and preserved schema-incomplete log; cron logs have an approved agenda ID; no run exceeds Source cap; and no scheduled run records synthesis. Findings name Agenda ID and run-log path.
6. Extend `.agents/rules/atlas-reducer-discipline.md` with the freestyle guard that only approved active rows may drive scheduled acquisition and that agenda execution cannot widen into index/research/refresh. Add `atlas-agenda` to `.agents/AGENTS.md` and `README.md`, including the app-as-agent-project instruction and the manual agenda→bounded acquire→dirty-topic review flow. Update the scaffold `summaries/INDEX.md` artifact-class and registry-root descriptions so new instances expose `atlas-research-agenda`.
7. Add `scaffold/summaries/registry/AGENDA.md` to `seed_once` in `scaffold/MANIFEST.json`; do not add it to `product_owned` or create living rows in scaffold. Existing `cmd_create`/`cmd_check` behavior then covers presence. Extend `tests/test_atlas_instance.py` to assert a new instance receives the empty agenda and sync does not overwrite a living agenda row.
8. Define migration ID `agenda-v1` in the registry contract and execute it through `skill://atlas-migrate`: old shape has no `AGENDA.md` or agenda artifact-class entry; new shape is the empty scaffold-compatible registry plus the two surgical `summaries/INDEX.md` description updates from step 6. Preflight requires the agenda path absent or already schema-valid and preserves unrelated index text. Rollback may delete the file and revert those two index descriptions only while the agenda has zero rows and no acquisition run references an agenda ID; otherwise rollback halts and preserves data. Verification is agenda-aware audit plus provision check.

### T6. Add continuous-research regression cases

1. Add `evals/cases/atlas-agenda.json` with synthetic registry/run fixtures for:
   - empty status;
   - proposed or pending item excluded from execution;
   - active human-approved periodic item selected;
   - manual cadence excluded from `run-due`;
   - priority/date/ID stable ordering and explicit limit;
   - material scope edit resetting approval;
   - priority-only edit retaining approval;
   - propose/approve/pause/resume/complete/retire legal transitions, terminal-state rejection, and every declared idempotent no-op;
   - changed/partial outcomes resetting the no-change streak;
   - no-change threshold pausing the row;
   - blocked outcome requiring resume;
   - two script/adapter invocations claiming the same full agenda revision: `atlas-local-fs-cas-v1` or isolated `eval_agenda` yields exactly one success and one conflict, with exactly one acquisition/run log and no lost update;
   - a claimed row with no log blocks all scheduled work until human `recover --abandon-claim`;
   - schema-incomplete claimed log stays byte-identical; recovery selects only source artifacts whose `acquisition_run` matches the reserved path, rejects manifest/artifact mismatches without repair, idempotently reruns route and relation-derived cache recomputation for valid matches, records `abandoned`, clears the claim to blocked only after successful reconciliation, and then requires resume;
   - capability status is available only from the named strict adapter (`atlas-local-fs-cas-v1` in the live local preflight; the same script behind isolated `eval_agenda`); missing adapter, non-SHA revision, unsupported connector, or profile-only declaration permits capabilities/status but every mutation performs zero writes;
   - missing topic, invalid enum/bound/date, duplicate ID, and illegal transition producing zero writes;
   - manual and cron run-log provenance plus source-cap deferral;
   - interrupted post-claim/pre-log and post-log/pre-reduction recovery paths;
   - agenda audit findings for unapproved cron execution and invalid abandoned provenance.
2. Add an actual scheduled-acquisition case whose allowed changed paths are only `AGENDA.md`, source artifacts, `MANIFEST.md`, one acquisition run, source route fields, `RELATIONS.md`, and derived freshness fields in `TOPICS.md`. Explicitly forbid vocabulary rows, topic creation/path fields, topic `INDEX.md`, research passes, optional topic split files, and any second work queue.
3. Execute every agenda case with `vault_mode: isolated` and `host_adapters: ["agenda"]`: `eval_agenda` invokes the same `scripts/atlas-agenda.py` reducer/CAS against the disposable profile, while `eval_vault` serves all other Atlas paths. Other Atlas-state cases use isolated `eval_vault` only. Compare actual temporary-state transitions and write sets to the contracts. No case may resolve the active connector/profile or physical bound instance. Only T7 performs the intended additive live migration after every isolated gate passes.

### T7. Verify, preflight, sync the contract, migrate, and record the baseline

1. Run `bun install --frozen-lockfile`, focused Python/Bun unit tests, and validate every suite before any bound-instance write. Execute the AI coding workflow, Atlas contracts, research-quality, and agenda suites; validate but do not execute live-readonly. Any hard failure blocks all bound-instance writes.
2. Exercise `compare` with two reports from the same unchanged case pack and require no hard regression; use a unit fixture with one baseline pass/candidate fail to require exit `1`; generate the blinded research-quality packet and validate a completed verdict without allowing it to override hard gates.
3. In the app-root agent session invoke read-only `/atlas-agenda capabilities` against bound `atlas`. Require the command to invoke `scripts/atlas-agenda.py capabilities` and report adapter `atlas-local-fs-cas-v1`, revision kind `sha256`, target identity `atlas`, and `conditional_replace: available` after a full-byte read of `vault://atlas/ARCHITECTURE.md`. The preflight must not create a lock or call replacement. Missing script/lock support, unsupported connector, profile-only declaration, built-in hashline `edit`, or ambiguous capability blocks architecture sync and migration.
4. Sync the product-owned architecture snapshot with `python3 scripts/atlas-instance.py sync-framework --name atlas`. Read `vault://atlas/ARCHITECTURE.md` and require Agenda/Scheduled acquisition modes, write sets, conditional-replace port, and eval isolation boundary to match app. Do not run provision check yet: the seed-once agenda path is intentionally absent until migration.
5. Invoke `/atlas-migrate agenda-v1` against bound local `atlas`. It creates only the empty agenda registry and two declared index-description changes; it must not add agenda rows, sources, relations, topic changes, passes, run logs, or eval artifacts.
6. Run `python3 scripts/atlas-instance.py check`, then `atlas-live-readonly`. Expected: check/audit clean; current topic answers from materialized citations; agenda valid/empty; conditional replace still available; no cron logs; empty write set.
7. Run all five suites once more as the first named baseline using `WORKFLOW_REVISION` for workflow and `plan:2026-07-14-1345` for Atlas. Keep reports under ignored `evals/results/`; record paths, subject/case-pack hashes, and hard/advisory outcomes in completion summary. Eval output is product-development evidence, never an Atlas source.
8. Re-run focused Python/Bun tests and confirm no OS-temporary fixture remains. Set plan `DONE` only after every criterion passes; do not commit, install cron, or deploy without a separate explicit request.

## Critical files & anchors

- `.agents/plans/2026-07-13-2349_ai-coding-workflow.md` or its archived counterpart — T4.7/T5 owns the first fourteen routing cases, transport checks, exact slugify fixture, and final accepted workflow path.
- `scripts/atlas-agenda.py` — new deterministic agenda reducer and `atlas-local-fs-cas-v1` adapter; the only local agenda mutation path and the concurrency-test target.
- `.agents/ARCHITECTURE.md` — canonical artifact roles, mode write sets, freshness machine, explicit-scheduler seam, and scheduled-synthesis deferral.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — existing deterministic source/relation/cache contracts and the owner of the new agenda schema, transitions, due order, and migration ID.
- `evals/schema.json` — new exact suite/report/comparison/verdict wire contract; its pinned SDK driver and adapters enforce execution isolation.

## Verification / Done criteria

All commands run from `/Users/kim/dev/atlas/app`. Set `WORKFLOW_CORE` and `WORKFLOW_REVISION` to the exact values recorded by the completed AI coding workflow plan; accepted public names and reference URIs are already materialized in the tracked suite during T3.

- [ ] Focused deterministic tests pass before and after live verification:

  ```bash
  bun install --frozen-lockfile
  python3 -m unittest discover -s tests -p 'test_*.py'
  bun test evals/adapters/*.test.ts
  ```

- [ ] All tracked suites validate without executing model/tool steps:

  ```bash
  python3 scripts/atlas-eval.py validate --suite evals/cases/ai-coding-workflow-t5.json --var WORKFLOW_CORE="$WORKFLOW_CORE"
  python3 scripts/atlas-eval.py validate --suite evals/cases/atlas-contracts.json
  python3 scripts/atlas-eval.py validate --suite evals/cases/atlas-research-quality.json
  python3 scripts/atlas-eval.py validate --suite evals/cases/atlas-agenda.json
  python3 scripts/atlas-eval.py validate --suite evals/cases/atlas-live-readonly.json
  ```

- [ ] AI coding workflow T5 executes as one isolated corpus:

  ```bash
  python3 scripts/atlas-eval.py run --suite evals/cases/ai-coding-workflow-t5.json --label first-baseline --revision "$WORKFLOW_REVISION" --var WORKFLOW_CORE="$WORKFLOW_CORE"
  ```

  Expected: source IDs 1–14 plus discovery, resolution, native transport, and slugify journey all hard-pass; the slugify case observes red before green, leaves no post-baseline commit, reports separate review axes, removes owned temporary artifacts, and deletes its temporary repository.

- [ ] Atlas and agenda suites execute without resolving or mutating the bound instance:

  ```bash
  python3 scripts/atlas-eval.py run --suite evals/cases/atlas-contracts.json --label first-baseline --revision plan:2026-07-14-1345
  python3 scripts/atlas-eval.py run --suite evals/cases/atlas-research-quality.json --label first-baseline --revision plan:2026-07-14-1345
  python3 scripts/atlas-eval.py run --suite evals/cases/atlas-agenda.json --label first-baseline --revision plan:2026-07-14-1345
  ```

  Expected: every hard contract passes; every logical `vault://atlas/` path is served by the disposable adapter; generated state stays under OS-temporary roots and ignored `evals/results/`; no fixture/report touches `scaffold/` or the physical bound instance.

- [ ] Baseline/candidate comparison behavior is proven:
  - comparing two unchanged-subject reports exits `0` with no hard regression;
  - the unit fixture containing one baseline hard-pass and candidate hard-fail exits `1`;
  - incompatible suite IDs/versions/case sets exit `2`;
  - a blinded research-quality packet plus completed review verdict preserves separate dimensions and cannot override a hard failure;
  - neither reports nor comparisons contain an aggregate score.
  - process steps record guard metrics as `not_applicable`; OMP steps with valid metrics use `complete`; pre-`agent_end` failure/timeout uses `missing`, null counts, and step error rather than fabricated zeros.

- [ ] Agenda behavior is observable in isolated cases:
  - proposed/unapproved/manual/non-due rows never enter `run-due`;
  - approved due rows sort high→medium→low, date, ID and obey the explicit limit;
  - material scope edits revoke approval;
  - the complete operation/state matrix, terminal rejections, and idempotent no-ops match T4.3;
  - source cap defers excess candidates;
  - no-change pauses at its configured limit;
  - blocked rows require resume;
  - concurrent claims serialize through strict full-file CAS: two workers using one `sha256` revision produce exactly one `new_revision`, one `conflict`, one row mutation/run, and no lost update; the loser halts before acquisition, while interrupted winners require explicit recovery or deterministic post-log reconciliation;
  - missing/incomplete claims require explicit abandon recovery; incomplete provenance stays byte-identical, only provenance-matched valid sources are rerouted, manifest/source mismatches are reported without repair, failed reconciliation leaves `running`, and successful reconciliation records `blocked/abandoned` before ordinary resume;
  - scheduled acquisition changes only agenda plus existing acquisition/route paths and never taxonomy, topic-body, pass, refresh, or synthesis paths.

- [ ] The active bound mutation-port preflight is read-only and available. In the app-root agent session invoke:

  ```text
  /atlas-agenda capabilities
  ```

  Expected: `scripts/atlas-agenda.py capabilities` identifies local development instance `atlas`, adapter `atlas-local-fs-cas-v1`, revision kind `sha256`, and `conditional_replace: available` after a full-byte architecture read; it creates no lock and changes no bound file. Missing script/`fcntl` support, unsupported connector, profile-only declaration, built-in hashline `edit`, or ambiguous capability blocks sync/migration.

- [ ] Product-owned architecture is synchronized before the schema migration:

  ```bash
  python3 scripts/atlas-instance.py sync-framework --name atlas
  ```

  Expected: `vault://atlas/ARCHITECTURE.md` contains Agenda/Scheduled acquisition modes, exact write sets, the `conditional_replace` port, and disposable-eval isolation. Do not run provision `check` before migration.

- [ ] The additive live migration succeeds only after isolated gates and architecture sync pass. In the app-root agent session invoke:

  ```text
  /atlas-migrate agenda-v1
  ```

  Expected: `vault://atlas/summaries/registry/AGENDA.md` exists with valid schema and zero rows; only the two declared `summaries/INDEX.md` descriptions change; no source, relation, topic, pass, or run-log row is added.

- [ ] Instance structure is valid after migration:

  ```bash
  python3 scripts/atlas-instance.py check
  ```

  Expected: `check OK`, one `atlas` instance, updated seed-once count, and no product-owned drift.

- [ ] After sync, migration, and provision check, the read-only live corpus passes:
  ```bash
  python3 scripts/atlas-eval.py run --suite evals/cases/atlas-live-readonly.json --label first-baseline --revision plan:2026-07-14-1345
  ```
  Expected: `/atlas-audit` reports no agenda/registry/artifact issue, `/atlas-answer agentic-harness-architecture` returns its current artifact-cited answer, `/atlas-agenda status` reports a valid empty agenda with conditional replacement available, the report includes source/topic/relation/freshness counts, and the case performs no write. No cron-linked run log exists because verification never performs live acquisition.

- [ ] `evals/results/` is ignored and contains the named baseline reports; each report records suite/case-pack hash, revision, hard/advisory outcomes, and artifact paths. No report is materialized as an Atlas source or topic.

- [ ] No OS-temporary eval repository remains. The plan is marked `DONE` with completion timestamps and a summary only after every criterion above is observed.

## Assumptions & contingencies

- The AI coding workflow plan executes first. If it is not `DONE` with one unambiguous support-core/eval path, this plan stops at T1 without product changes; it never manufactures the pending T5 corpus.
- The accepted workflow prefix may differ from `devflow`. All T5 suite names come from `WORKFLOW_PREFIX`/`WORKFLOW_CORE`; provisional names are never compatibility aliases.
- OMP and Grok are required only for live T5/agent cases. If either executable or native transport is unavailable, unit/schema work may be diagnosed, but T7 and plan completion stop; do not substitute filesystem discovery for transport proof or silently drop those cases.
- The intended migration target is the bound local development instance named `atlas`. If `vault://atlas/` is unavailable or the active profile is non-local/non-development, stop before migration/sync and do not write through the physical filesystem or another vault name.
- If `/atlas-agenda capabilities` reports `unavailable`, stop before architecture sync/migration and leave this plan `IN_PROGRESS`; do not add a declarative profile flag or perform a write probe. An unsupported/non-local target is an environment blocker; a defect in `atlas-local-fs-cas-v1` is unfinished T5 implementation and must be corrected and reverified before T7.
- If `AGENDA.md` already exists, `agenda-v1` is a no-op only when it is schema-valid; an invalid or conflicting file halts without overwrite. Rollback deletes only an empty, unreferenced agenda file.
- Continuous research v1 deliberately stops at approved, bounded acquisition and routing. It does not install cron/launchd, schedule refresh, run synthesis, answer dirty topics, or promote taxonomy. A future external scheduler invokes `run-due` with an explicit limit.
- The migrated personal agenda starts empty. The user adds and approves real interests later through `/atlas-agenda`; eval fixtures never become living rows.
- Human pairwise review is the semantic authority in this plan. The runner does not add an automatic LLM judge or allow advisory quality judgments to waive deterministic failures.
- Generated results are local product-development artifacts under ignored `evals/results/`. They are not living Atlas evidence, are not synced to instances, and are not committed unless a later request establishes a curated baseline policy.
- No commit, push, PR, deployment, credential copying, cloud-profile write, or host scheduler installation is part of this plan. Agent eval calls use already configured OMP/Grok authentication only during explicit T7 execution.

