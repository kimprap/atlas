# Atlas Command Cutover Plan

**Datetime**: 2026-07-07-1145
**Scope**: Atlas command/workflow surface for `.config/agents/skills/digest/`, future `.config/agents/skills/atlas-*` entrypoints, and Markdown state under `vault://atlas/`.
**Summary**: Promote the verified Atlas Phase 1 Markdown workflows from the temporary `digest` adapter into dedicated Atlas command behavior, add deterministic audit coverage, and keep smoke fixtures temporary so `vault://atlas/` remains a clean starter framework after verification.
**Status**: DONE

## Context

The archived implementation plan `.agents/plans/archive/2026-06-30-1339_research-framework-vault.md` completed the Phase 1 Atlas framework and used temporary smoke fixtures to verify source ingestion, routing, dirty-answer halts, and delta refresh. Those fixtures are not product data and must not remain part of the Atlas setup.

The canonical framework source of truth is `vault://atlas/ARCHITECTURE.md`. Phase 1 canonical state remains Markdown in the Obsidian vault. SQLite is out of scope until a later, explicit adapter phase.

Current repository discovery shows no repo-local `.config/agents/commands/` directory. The existing repo-local agent behavior surface is skills under `.config/agents/skills/`. Therefore the implementation fallback is pre-decided: if OMP still has no supported repo-local slash-command file location when this plan is executed, implement Atlas entrypoints as skills named `atlas-source`, `atlas-acquire`, `atlas-route`, `atlas-research`, `atlas-refresh`, `atlas-answer`, `atlas-audit`, `atlas-index`, and `atlas-migrate`, with `/atlas-*` documented as invocation aliases in each skill. Do not create a SQLite adapter or `atlas-index/scripts/atlas-registry.py` in this plan.

## Execution intent

End state:

- Atlas workflows have dedicated `/atlas-*` behavior instead of relying on `/digest` as the main entrypoint.
- `digest` is narrowed to a compatibility shim after the new Atlas entrypoints pass smoke checks.
- Deterministic Markdown reducers/audit checks protect source identity, routing, freshness, managed sections, and vocabulary discipline.
- Verification uses temporary fixtures only; final verification removes fixture artifacts, registry rows, run logs, topic indexes, and empty fixture directories from `vault://atlas/`.
- `vault://atlas/` ends in clean starter shape: architecture, summaries indexes, empty manifest/topic/relation registries, source-kind vocabulary rows, and preserved `vault://atlas/todos/`.

## Tasks

- [x] T1. Confirm clean starter vault and fixture policy
  completed 2026-07-07-1549
- [x] T2. Establish Atlas entrypoint structure
  completed 2026-07-07-1549
- [x] T3. Extract deterministic reducer contracts
  completed 2026-07-07-1601
- [x] T4. Implement source, acquire, route, and index workflows
  completed 2026-07-07-1601
- [x] T5. Implement research, refresh, and answer workflows
  completed 2026-07-07-1609
- [x] T6. Implement read-only Atlas audit workflow
  completed 2026-07-07-1609
- [x] T7. Run isolated smoke suite with cleanup
  completed 2026-07-07-1634
- [x] T8. Demote digest to compatibility shim
  completed 2026-07-08-1724
- [x] T9. Document cadence, guardrails, and deferred phases
  completed 2026-07-08-1724

## Ordered implementation

### T1. Confirm clean starter vault and fixture policy

- Read `vault://atlas/`, `vault://atlas/todos/`, and `vault://atlas/summaries/`.
- Verify there are no source artifact fixture directories under `vault://atlas/summaries/sources/artifacts/` or run-log fixture directories under `vault://atlas/summaries/sources/runs/`.
- Verify `vault://atlas/summaries/research/` contains only `INDEX.md` unless real user-created topics were added after this plan was written.
- Verify `MANIFEST.md`, `TOPICS.md`, and `RELATIONS.md` contain headers plus no smoke-test data rows.
- Verify `VOCAB.md` contains only framework starter vocabulary, especially source-kind rows; do not retain smoke domains, subdomains, or tags such as `agentic-development`, `agent-research`, `cooking`, `bread`, `programmatic-agents`, `autonomous-research`, `sourdough`, `recipe`, or `baking` unless the user has intentionally re-added them after this plan.
- Add or preserve a short fixture policy in the relevant Atlas command/skill docs: smoke fixtures may be created only during verification and must be fully removed before completion.

### T2. Establish Atlas entrypoint structure

- First check whether the current OMP version exposes a supported repo-local slash-command location.
- If a command directory exists and is documented, place `/atlas-*` command definitions there.
- If no such location exists, use the pre-decided fallback: create skills under `.config/agents/skills/atlas-*/SKILL.md` for:
  - `atlas-source`
  - `atlas-acquire`
  - `atlas-route`
  - `atlas-research`
  - `atlas-refresh`
  - `atlas-answer`
  - `atlas-audit`
  - `atlas-index`
  - `atlas-migrate`
- Each entrypoint must read `vault://atlas/ARCHITECTURE.md` first and must point to the shared contracts from T3.
- Keep descriptions narrow enough that the right entrypoint triggers predictably.
- Do not create `.config/agents/skills/atlas-index/scripts/atlas-registry.py` or any SQLite-related script.

### T3. Extract deterministic reducer contracts

Create shared Atlas contract material in the same surface chosen in T2. Prefer one shared asset if skills are used, for example `.config/agents/skills/atlas-core/assets/markdown-registry-contracts.md`, unless OMP command files provide a better native include mechanism.

Contracts must define:

- canonical URL normalization rules
- `source_id` derivation from canonical URL
- `content_hash` derivation from fetched source content
- source manifest dedupe and refresh behavior
- source artifact frontmatter requirements
- legal `routing_status` values
- canonical tag discipline against `VOCAB.md`
- `candidate_terms` handling
- deterministic `Edge ID` format
- route-source candidate generation
- bounded route verifier output shape
- relation row status transitions
- topic dirty-state recomputation from `RELATIONS.md`
- quick-answer freshness gate
- managed-section patch boundaries
- fixture cleanup requirements

### T4. Implement source, acquire, route, and index workflows

Implement or document executable behavior for:

- `/atlas-source <url...>`
  - explicit URLs only
  - one source artifact per new or changed canonical URL
  - manifest dedupe before summarization
  - route-source after artifact write unless unchanged duplicate
- `/atlas-acquire <watchlist-or-query>`
  - bounded sources only: watchlists, feeds, inboxes, repo lists, author lists, or explicitly scoped queries
  - materialize source artifacts first
  - write acquisition run logs
  - never update topic answers directly
- `/atlas-route <source-id-or-range>`
  - reducer only
  - may update source artifact route status, manifest route status, `RELATIONS.md`, and `TOPICS.md` dirty cache
  - must not edit topic `INDEX.md`
- `/atlas-index`
  - explicit vocabulary/topic promotion and repair
  - no ad hoc taxonomy creation from acquisition
  - no SQLite adapter in this plan

### T5. Implement research, refresh, and answer workflows

Implement or document executable behavior for:

- `/atlas-research --vault-only <topic>`
  - default research mode
  - reads existing source artifacts and topic registry
  - records insufficiency instead of inventing unsupported answers
- `/atlas-research --acquire <topic>`
  - explicit escape hatch
  - runs acquisition first
  - materializes and routes source artifacts before synthesis
- `/atlas-refresh --topic <topic-id>`
  - only normal transition from dirty to current
  - creates one dated pass
  - patches managed sections only
  - marks applied relation edges with `Applied in pass`
  - recomputes `TOPICS.md`
- `/atlas-answer <topic>`
  - reads `TOPICS.md` before topic `INDEX.md`
  - halts on `dirty`, `refreshing`, or `blocked`
  - answers only when current
  - reads optional split files only through `## Read next`
  - cites source artifacts, not raw URLs

### T6. Implement read-only Atlas audit workflow

Implement `/atlas-audit` as a read-only validator. It must not repair state unless called through a separate explicit repair/index workflow.

Minimum checks:

- manifest source seq continuity
- duplicate canonical URLs
- duplicate source IDs
- missing source artifact paths
- source frontmatter shape
- invalid `canonical_tags`
- `candidate_terms` not promoted as tags
- relation source/topic references exist
- duplicate `Edge ID`
- valid relation/status/impact/confidence values
- pending/applied status consistency
- `TOPICS.md` dirty counts match pending relations
- `Pending edge IDs` exactness
- `Source watermark` correctness
- applied relations have existing `Applied in pass` paths
- topic path existence
- topic managed-section marker pairing
- raw URL citations in managed answer/evidence sections
- unexpected SQLite/database files under Atlas
- unexpected `UNCLAIMED-SOURCES.md`
- leftover smoke fixture artifacts or fixture vocabulary rows

### T7. Run isolated smoke suite with cleanup

Run the command smoke suite through the new Atlas entrypoints, then clean every fixture artifact before marking this task complete.

Smoke coverage:

1. `/atlas-source https://github.com/karpathy/autoresearch`
2. repeat the same source ingestion and verify duplicate skip
3. no-match source route with a safe throwaway source
4. `/atlas-research --vault-only "programmatic agent engineering"`
5. `/atlas-research --acquire "best way to create sourdough"` or an equivalent bounded throwaway topic
6. dirty `/atlas-answer <topic>` halt
7. `/atlas-refresh --topic <topic-id>`
8. `/atlas-answer <topic>` after refresh
9. `/atlas-audit`

Cleanup requirements after smoke:

- delete smoke source artifacts
- delete smoke acquisition run logs
- delete smoke topic folders, passes, and subdomain indexes
- delete smoke manifest rows
- delete smoke relation rows
- delete smoke topic rows
- delete smoke vocabulary rows
- remove empty smoke directories
- rerun `/atlas-audit` against the clean starter vault

### T8. Demote digest to compatibility shim

After T7 passes:

- Rewrite `.config/agents/skills/digest/SKILL.md` so it forwards users to the Atlas entrypoints.
- Remove duplicated Atlas workflow checklists from `digest`; the dedicated Atlas entrypoints own those contracts.
- Keep `digest` only as a thin compatibility adapter for old `/digest` invocations.
- Do not delete `digest` in this plan unless a separate user instruction explicitly asks for removal.
- Ensure `digest` still has no `vault://digest` references.

### T9. Document cadence, guardrails, and deferred phases

Record the operational decisions in the Atlas entrypoint docs or a small scoped Atlas rule:

- manual source ingestion is allowed anytime
- acquisition must be bounded
- dirty topics require refresh before answer
- periodic `/atlas-audit` is the first guardrail
- hooks/extensions may warn or block cheaply but must not run LLM synthesis
- optional split files are threshold-driven only
- cron refresh is deferred until `/atlas-refresh` is stable
- priority routing is deferred until refresh quality is stable
- SQLite, FTS, vector retrieval, and self-healing migrations are deferred to later explicit plans

## Critical anchors

- `vault://atlas/ARCHITECTURE.md` — framework source of truth.
- `vault://atlas/todos/TODOs.md` — legacy state; preserve unchanged.
- `vault://atlas/summaries/INDEX.md` — artifact class overview.
- `vault://atlas/summaries/sources/MANIFEST.md` — canonical source identity and dedupe registry.
- `vault://atlas/summaries/sources/INDEX.md` — source storage rules.
- `vault://atlas/summaries/research/INDEX.md` — research topic storage rules.
- `vault://atlas/summaries/registry/VOCAB.md` — canonical vocabulary.
- `vault://atlas/summaries/registry/TOPICS.md` — topic freshness registry.
- `vault://atlas/summaries/registry/RELATIONS.md` — source-topic relation registry.
- `.config/agents/skills/digest/SKILL.md` — temporary compatibility adapter to demote after cutover.
- `.config/agents/skills/digest/assets/source-summary-template.md` — source artifact schema reference.
- `.config/agents/skills/digest/assets/research-library-templates.md` — research artifact schema reference.
- `.agents/plans/archive/2026-06-30-1339_research-framework-vault.md` — completed Phase 1 plan and smoke-test provenance.
- `.agents/plans/archive/2026-07-01-2313_atlas-routing-refresh.md` — completed routing-refresh predecessor.
- `.config/agents/harnesses/omp/config.yml` — current OMP harness config; no command directory was present when this plan was written.

## Verification / Done criteria

- [x] `read vault://atlas/` confirms the Atlas vault root resolves.
- [x] `read vault://atlas/todos/` confirms legacy todos still exists and was not cleaned, renamed, or migrated.
- [x] `read vault://atlas/summaries/sources/` shows only starter files after final smoke cleanup, unless real user data was intentionally added during execution.
- [x] `read vault://atlas/summaries/research/` shows only `INDEX.md` after final smoke cleanup, unless real user data was intentionally added during execution.
- [x] `MANIFEST.md`, `TOPICS.md`, and `RELATIONS.md` contain no smoke-test rows after final smoke cleanup.
- [x] `VOCAB.md` contains no smoke-only domain/subdomain/tag rows after final smoke cleanup.
- [x] Atlas entrypoints exist for source, acquire, route, research, refresh, answer, audit, index, and migrate behavior using the chosen OMP-supported surface.
- [x] Source ingestion smoke proves duplicate source ingestion skips duplicate artifact and duplicate relation creation.
- [x] No-match route smoke proves no relation edge, no dirty topic, no `UNCLAIMED-SOURCES.md`.
- [x] Research smoke proves vault-only mode does not acquire sources.
- [x] Acquisition-first smoke proves acquisition materializes source artifacts before topic synthesis.
- [x] Dirty answer smoke proves `/atlas-answer` halts with topic path, dirty count, and pending edge IDs.
- [x] Delta refresh smoke proves `/atlas-refresh` creates one pass, patches managed sections, applies pending edges, recomputes topic freshness, and enables answer afterward.
- [x] `/atlas-audit` passes after final smoke cleanup.
- [x] `.config/agents/skills/digest/SKILL.md` is a compatibility shim and contains no `vault://digest` reference.
- [x] No `.sqlite`, `.db`, or `.config/agents/skills/atlas-index/scripts/atlas-registry.py` file is created by this plan.

## Assumptions and fallbacks

- If OMP exposes no repo-local command directory, implement Atlas entrypoints as skills under `.config/agents/skills/atlas-*/SKILL.md`; this is the chosen fallback, not an open decision.
- If OMP later documents a command directory before execution starts, use that native command surface and keep shared contracts in command assets or equivalent includes.
- If smoke tests must write into `vault://atlas/`, they must clean up before completion. Temporary fixture persistence is allowed only within the active verification task.
- If a smoke cleanup step encounters user-created data mixed with fixtures, stop destructive cleanup for that path and report the conflicting path explicitly.
- If command implementation reveals that one entrypoint must be split further for reliable triggering, split it only along existing command boundaries and update this plan before implementation continues.

## Out of scope

- No SQLite registry/cache adapter.
- No direct SQL by agents.
- No vector retrieval.
- No cron refresh implementation.
- No LLM synthesis inside hooks/extensions.
- No migration or cleanup of `vault://atlas/todos/`.
- No permanent smoke fixtures in `vault://atlas/`.
- No deletion of `digest` without separate user instruction.

## Completion Summary

- T1-T3 confirmed the clean starter vault, established the Atlas entrypoint surface, and centralized deterministic Markdown reducer contracts in `atlas-core`.
- T4-T6 moved source, acquisition, route, research, refresh, answer, audit, index, and migrate behavior into dedicated Atlas skill entrypoints with read-only audit coverage.
- T7 exercised the Atlas workflow end to end with temporary fixtures, then removed every smoke artifact and restored `vault://atlas/` to starter shape.
- T8 demoted `digest` to a thin compatibility shim that forwards legacy `/digest` invocations to the matching `/atlas-*` entrypoint instead of owning Atlas workflow contracts.
- T9 recorded the operating cadence and guardrails in `atlas-core/assets/operating-cadence-and-guardrails.md` and wired Atlas skills to read it.
- Delivered state: dedicated Atlas command skills are in place, `digest` is transitional only, the starter vault is clean, and no SQLite/database helper was introduced.
- Residual risk: slash-command execution was validated through the command-backed skill surfaces and persisted workflow artifacts, not through a separate interactive slash-command runner.
- Outcome: the Atlas command cutover is complete for the Phase 1 / early Phase 2 manual-operation model; future work should proceed as a new dated plan rather than extending this archived cutover plan.
