# Atlas Routing, Freshness, and Registry Plan

**Datetime**: 2026-07-01-2313
**Scope**: Update the Atlas implementation plan so routing, freshness, registry ownership, optional SQLite, and workflow control are deterministic and 12-Factor-first.
**Summary**: Execute this plan before implementing `.agents/plans/2026-06-30-1339_research-framework-vault.md`. The output is a revised first Atlas plan that uses Markdown artifacts and Markdown registries as Phase 1 canonical state, defers SQLite to a later derived-index phase, makes routing/dirty-refresh behavior deterministic, and treats Atlas workflows as 12-Factor-style reducers around small focused agents.
**Status**: DONE

## Context

The requested refinement changes the Atlas implementation order and the framework architecture before any vault or skill files are implemented. The first Atlas plan, `.agents/plans/2026-06-30-1339_research-framework-vault.md`, is the foundation implementation plan; this routing-refresh plan must be applied first so that the foundation plan includes deterministic registries, dirty refresh semantics, SQLite deferral, and 12-Factor-first workflow control. The intended end state is a lean Obsidian-vault framework where Markdown source artifacts, Markdown topic artifacts, and Markdown registry tables are the canonical Phase 1 state; SQLite is not used for Phase 1 and is allowed later only as a derived registry/index cache behind a deterministic script interface.

Grounded findings to preserve in the revised first plan:

- `.agents/plans/2026-06-30-1339_research-framework-vault.md` currently targets `vault://atlas/`, preserves `vault://atlas/todos/`, stores source artifacts under `vault://atlas/summaries/sources/artifacts/<YYYY>/<YYYY-MM>/`, stores topic artifacts under `vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/`, and currently has no registry layer.
- `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` is the repo-local mirror of this `local://atlas-routing-refresh-plan.md` artifact. Do not hand-edit the mirror while planning; update `local://atlas-routing-refresh-plan.md` only.
- `.config/agents/skills/digest/SKILL.md` is still the legacy `digest` skill and currently uses freeform URL-summary facets such as `domain/...`, `topic/...`, and `kind/...`.
- `.config/agents/skills/digest/assets/source-summary-template.md` does not yet include Atlas `source_seq`, canonical registry tags, candidate terms, routing status, or relation-edge metadata.
- `.config/agents/harnesses/omp/config.yml` has `vault.enabled: true` and no Atlas-specific hook/extension.
- Local repo exploration found only one direct SQLite usage: `.config/agents/skills/mnemopi-cleanup/scripts/mnemopi-status`, a Python stdlib read-only inspector for Mnemopi banks. No Atlas CRUD helper, shared DB layer, ORM, or general SQLite abstraction exists.
- Local script patterns favor stdlib Python for agent skill scripts (`argparse`, `pathlib`, explicit JSON output, explicit exit codes) and Bun JavaScript for OMP event extensions.
- Primary framework basis is [12-Factor Agents](https://github.com/humanlayer/12-factor-agents): structured model outputs handled by deterministic code, unified execution/business state, owned control flow, small focused agents, and reducer-style state transitions. Anthropic agent guidance, HumanLayer harness engineering, and LangChain context engineering are supporting references only.

## Implementation sequence summary

Implement the two Atlas plans as one ordered chain, not as two parallel implementation tracks.

1. **Apply this routing-refresh plan first** (`.agents/plans/2026-07-01-2313_atlas-routing-refresh.md`, mirrored from `local://atlas-routing-refresh-plan.md`). Its work is plan consolidation only: update `.agents/plans/2026-06-30-1339_research-framework-vault.md` with precedence, Markdown-first storage, deferred SQLite policy, 12-Factor workflow basis, registry schemas, route-source reducer behavior, dirty/delta refresh behavior, slash-command contracts, phases, and verification.
2. **Do not create vault files, skill files, templates, SQLite files, or Atlas scripts while applying this routing-refresh plan.** The only runtime artifact touched by the routing-refresh plan is the first implementation plan file.
3. **After the routing-refresh edits are verified, mark `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` DONE and archive it** using the local plan conventions for completed plans. Its decisions have then been absorbed into the first implementation plan.
4. **Execute the revised first implementation plan next** (`.agents/plans/2026-06-30-1339_research-framework-vault.md`). Run its tasks top-to-bottom after revision: verify `vault://atlas/` and `vault://atlas/todos/`; create `vault://atlas/ARCHITECTURE.md`; update the legacy `digest` skill; update the source template; create the research-library template asset; create starter vault files including `VOCAB.md`, `TOPICS.md`, and `RELATIONS.md`; then run the registry/source/research smoke checks.
5. **Keep Phase 1 Markdown-only.** The revised first plan must not implement SQLite. SQLite appears only as a later optional Phase 4 derived registry cache behind `.config/agents/skills/atlas-index/scripts/atlas-registry.py`.

## Tasks

- [x] T1. Make execution order explicit before changing architecture
  completed 2026-07-02-1457
- [x] T2. Choose Markdown canonical state and defer SQLite
  completed 2026-07-02-1457
- [x] T3. Prioritize 12-Factor Agents as the architecture basis
  completed 2026-07-02-1635
- [x] T4. Add the Markdown registry layer to the foundation plan
  completed 2026-07-02-1635
- [x] T5. Update source contracts and route-source reducer behavior
  completed 2026-07-02-1704
- [x] T6. Define dirty state, quick-answer behavior, and persisted delta refresh
  completed 2026-07-02-1704
- [x] T7. Update slash command contracts, hooks policy, phases, and SQLite adapter timing
  completed 2026-07-02-1709
- [x] T8. Replace verification in the foundation plan
  completed 2026-07-02-1709

## Approach

### T1. Make execution order explicit before changing architecture

Edit `.agents/plans/2026-06-30-1339_research-framework-vault.md` first, before any vault files, skill files, templates, or registry files are implemented. Add this section immediately after its existing `## Context` section:

```md
## Precedence and execution order

Apply `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` before executing this implementation plan. The routing-refresh plan is a plan-consolidation pass: it updates this plan with deterministic Atlas registry, freshness, SQLite, and workflow-control decisions. After that pass is complete, execute this revised plan top-to-bottom: verify the vault root, create `ARCHITECTURE.md`, update the legacy `digest` skill, update templates, create starter vault files, then run smoke checks.

Do not implement vault artifacts or skill changes from the older version of this plan before the routing-refresh pass is complete. The final implementation source of truth is this revised plan plus `vault://atlas/ARCHITECTURE.md` once created.
```

Then update the first plan's task list so the first three tasks are these exact tasks, preserving the remaining implementation tasks after them and renumbering the old T1-T7 as needed:

```md
- [ ] T1. Apply routing-refresh plan consolidation before implementation: update this plan with the registry layer, SQLite decision, 12-Factor design basis, dirty refresh workflow, and revised verification checks.
- [ ] T2. Verify `vault://atlas/` resolves and preserve legacy `vault://atlas/todos/` without removing, renaming, cleaning, or migrating it.
- [ ] T3. Establish `vault://atlas/ARCHITECTURE.md` as the framework source of truth, covering layout, artifact roles, registry layer, mode ownership, 12-Factor workflow basis, schema/versioning, source identity/dedupe, topic routing, dirty state, optional SQLite migration policy, future skill contracts, and framework philosophy.
```

Keep the mirror `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` out of the first plan's implementation steps except as the precedence reference above. The mirrored file is not an Atlas runtime artifact and is not copied into the vault.

Failure handling for this step: if `.agents/plans/2026-06-30-1339_research-framework-vault.md` already contains a `## Precedence and execution order` section, replace that whole section instead of appending a duplicate. If the mirrored routing-refresh filename differs only by datetime because plan mirroring regenerated it, use the latest `.agents/plans/*_atlas-routing-refresh.md` mirror path in the precedence sentence and keep this `local://atlas-routing-refresh-plan.md` as the planning source of truth.

### T2. Choose Markdown canonical state and defer SQLite

Update `.agents/plans/2026-06-30-1339_research-framework-vault.md` so the first plan makes this storage decision explicit in `## Context`, `## Assumptions & contingencies`, and the planned `vault://atlas/ARCHITECTURE.md` content:

```md
Atlas Phase 1 canonical state is Markdown in the Obsidian vault: source artifacts, acquisition run logs, topic `INDEX.md` files, research pass files, `summaries/sources/MANIFEST.md`, and `summaries/registry/*.md` tables. Do not build Atlas around SQLite in Phase 1, and do not store source summaries, research passes, topic overviews, or registry rows only in SQLite. Markdown remains the human-readable, Obsidian-native, linkable, inspectable source of truth.

SQLite is a later optimization, not the initial architecture. If registry Markdown files become operationally painful after persisted refresh workflows are stable, add SQLite as a derived registry/index cache only. The cache may accelerate lookup and consistency checks, but it must be rebuildable from Markdown artifacts and must not become the only copy of source/topic/relation state without a separate explicit schema-migration plan.
```

Add this exact subsection to the first plan's `ARCHITECTURE.md` requirements under `## Schema migration` or immediately before `## Future skill contract`:

```md
## SQLite policy

- Phase 1 uses Markdown as canonical state. SQLite is not part of Phase 1.
- Source artifacts, topic overviews, research passes, and acquisition run logs stay as Markdown files even if SQLite is introduced later.
- Registry Markdown files are canonical until an explicit schema migration says otherwise.
- A later SQLite registry cache may be introduced only after Markdown routing, persisted delta refresh, and registry consistency checks are working.
- If introduced, SQLite is a derived cache at `vault://atlas/.atlas/registry.sqlite`, rebuilt from Markdown by an Atlas registry adapter. Do not hand-edit the database and do not let agents issue ad hoc SQL.
- If a future migration promotes SQLite from derived cache to canonical registry storage, that migration must keep Markdown export views for Obsidian browsing and must define rollback back to Markdown.
```

Do not add SQLite files, SQLite scripts, package dependencies, or database migrations to the first implementation phase. The old single-manifest policy remains valid for Phase 1, except it must coexist with the new registry files added in T4.

Failure handling for this step: if the implementer finds existing Atlas SQLite code despite the current repo search showing none, do not reuse it unless it already provides a single deterministic registry adapter interface. If it is only raw SQL snippets, leave it unused and keep Phase 1 Markdown-only.

### T3. Prioritize 12-Factor Agents as the architecture basis

Update the first plan so `vault://atlas/ARCHITECTURE.md` includes a `## 12-Factor workflow basis` section immediately after `## Framework invariants`. The section must contain these bullets exactly:

```md
## 12-Factor workflow basis

Atlas follows the 12-Factor Agents style: agents produce structured decisions, deterministic workflow code/checklists apply those decisions, and durable vault artifacts record the resulting state.

- **Structured outputs, deterministic application**: LLMs may propose route decisions, relation classifications, or delta-refresh patches, but Atlas workflows apply them through explicit checklists and schema checks.
- **Own the context window**: registry rows and bounded source/topic snippets are the context interface; agents must not load the whole vault when a registry lookup is sufficient.
- **Unify execution and business state**: source artifacts, manifest rows, relation rows, topic registry rows, pass files, and run logs are the durable workflow state. Do not add a separate ephemeral queue for the same facts.
- **Own control flow**: slash commands and scheduled workflows decide when to route, halt, delegate refresh, persist a pass, or answer. Hooks may only enforce cheap guardrails.
- **Small focused agents**: acquisition, route verification, topic refresh, answer lookup, index repair, and migration are separate workflows with narrow read/write sets.
- **Reducer model**: each workflow reads the current vault state plus one event, computes a bounded change, writes the new state, and records enough provenance to recompute or audit it later.
```

Update `## Framework philosophy` in the first plan's planned `ARCHITECTURE.md` content so it ends with this paragraph:

```md
Atlas is deterministic scaffolding around nondeterministic agents. Keep the interface small, state durable, reducers explicit, and model work bounded. Prefer a readable Markdown state transition over a hidden optimization until the optimization demonstrably improves lookup, consistency, or scale without weakening provenance.
```

In the first plan's external-design notes, make 12-Factor Agents the first and primary basis. Keep Anthropic, HumanLayer harness engineering, and LangChain context engineering as supporting references, not co-equal architecture drivers.

Failure handling for this step: do not add a separate `EVENTS.md` just to mimic event sourcing. For Phase 1, acquisition run logs, research pass files, source artifacts, manifest rows, and relation rows are the event/history records. Add a separate event log only in a future migration if audits cannot be reconstructed from those artifacts.

### T4. Add the Markdown registry layer to the foundation plan

Update the first plan's directory layout, starter vault files, and `ARCHITECTURE.md` requirements to add this registry directory:

```text
vault://atlas/summaries/registry/
├── VOCAB.md
├── TOPICS.md
└── RELATIONS.md
```

Use these exact file roles:

- `VOCAB.md` — canonical vocabulary and alias registry. This is the only place where canonical domains, subdomains, tags, source kinds, and reusable aliases are declared.
- `TOPICS.md` — topic registry and freshness cache. This is the quick lookup table for resolving a topic, checking dirty state, finding the topic path, and deciding refresh model without reading topic files.
- `RELATIONS.md` — source-topic edge ledger. This is the source of truth for pending/applied source-to-topic edges.

Do not add `UNCLAIMED-SOURCES.md`. For unmatched sources, acquisition run logs may record counts and source IDs that matched no topic, but Atlas must not maintain a global unclaimed-source queue in this iteration.

Update the first plan's starter vault files list to these seven files:

```md
1. `vault://atlas/summaries/INDEX.md`
2. `vault://atlas/summaries/sources/MANIFEST.md`
3. `vault://atlas/summaries/sources/INDEX.md`
4. `vault://atlas/summaries/research/INDEX.md`
5. `vault://atlas/summaries/registry/VOCAB.md`
6. `vault://atlas/summaries/registry/TOPICS.md`
7. `vault://atlas/summaries/registry/RELATIONS.md`
```

Specify `VOCAB.md` in the first plan with this exact starter content:

```md
---
schema_version: 1
note_type: atlas-vocab
managed_by: atlas
last_updated: YYYY-MM-DD
---

# Atlas Vocabulary

## Canonical terms

| ID | Type | Label | Parent | Allowed aliases | Status | Notes |
|---|---|---|---|---|---|---|

## Promotion rules

- Acquisition workflows may suggest `candidate_terms` in source artifacts but must not add rows here.
- Add a row only from `/atlas-index --promote-term` or `/atlas-research --create-topic` after checking for duplicate or conflicting IDs.
- IDs use lowercase kebab-case.
- `Type` is exactly one of `domain`, `subdomain`, `tag`, or `source-kind`.
- `Parent` is empty for domains/source-kinds, the parent domain for subdomains, and optional for tags.
- `Status` is exactly one of `active`, `deprecated`, or `reserved`.
```

Specify `TOPICS.md` in the first plan with this exact starter content:

```md
---
schema_version: 1
note_type: atlas-topic-registry
managed_by: atlas
last_updated: YYYY-MM-DD
---

# Atlas Topic Registry

| Topic ID | Topic path | Domain | Subdomain | Canonical title | Aliases | Canonical tags | Include terms | Exclude terms | Freshness state | Dirty count | Pending edge IDs | Newest pending source seq | Last synthesized | Source watermark | Refresh model |
|---|---|---|---|---|---|---|---|---|---|---:|---|---:|---|---:|---|
```

Use these exact `Freshness state` values:

```text
current | dirty | refreshing | blocked | archived
```

Use these exact `Refresh model` values:

```text
same-as-topic-creation | smol-ok | manual-only
```

Default `Refresh model` for durable research topics is `same-as-topic-creation`.

Specify `RELATIONS.md` in the first plan with this exact starter content:

```md
---
schema_version: 1
note_type: atlas-relations
managed_by: atlas
last_updated: YYYY-MM-DD
---

# Atlas Source-Topic Relations

| Edge ID | Source seq | Source ID | Source artifact | Source content hash | Topic ID | Relation | Impact | Confidence | Status | Created | Applied in pass | Notes |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|
```

Use these exact relation-field values:

- `Relation`: `direct`, `supporting`, or `contradicting`.
- `Impact`: `high`, `medium`, or `low`.
- `Confidence`: `high`, `medium`, or `low`.
- `Status`: `pending`, `applied`, `rejected`, or `superseded`.

Do not store `background`, `duplicate`, or `out-of-scope` rows in `RELATIONS.md`; those outcomes belong only in acquisition or route run summaries.

Failure handling for this step: if registry files already exist in `vault://atlas/summaries/registry/`, merge rows and preserve user content. Do not overwrite existing rows unless the row key is identical and the planned schema requires adding missing columns.

### T5. Update source contracts and route-source reducer behavior

Update the first plan's source summary template contract and source manifest contract.

Add these fields to source summary frontmatter in `.config/agents/skills/digest/assets/source-summary-template.md`:

```yaml
source_seq: 0
canonical_tags: []
candidate_terms: []
routing_status: "unrouted|routed|no-topic-match|routing-blocked"
routed_at: "YYYY-MM-DD"
```

Keep `tags: []` only if the first plan says every value must be a canonical ID from `VOCAB.md`; otherwise replace `tags: []` with `canonical_tags: []`.

Update the manifest starter table in the first plan to this exact header:

```md
| Source seq | Source ID | Canonical URL | Artifact | First seen | Last checked | Last summarized | Content hash | Refresh after | Route status | Status |
|---:|---|---|---|---|---|---|---|---|---|---|
```

Add these source-routing invariants to the first plan:

- `source_seq` is a monotonically increasing integer assigned in `summaries/sources/MANIFEST.md`; it is the cheap ordering key for routing and refresh.
- `canonical_tags` may contain only IDs already present in `VOCAB.md`.
- `candidate_terms` may contain source-specific phrases that seem useful but are not canonical and must not be used as routing keys.
- Daily acquisition must not create canonical tags, aliases, domains, subdomains, or topic IDs.
- A source artifact write/update must be followed by the route-source workflow unless the source is a duplicate skip with unchanged `content_hash`.

Define the route-source reducer workflow exactly in the first plan:

1. Read `vault://atlas/ARCHITECTURE.md`, `summaries/registry/VOCAB.md`, `summaries/registry/TOPICS.md`, `summaries/registry/RELATIONS.md`, `summaries/sources/MANIFEST.md`, and the new/updated source artifact.
2. Normalize the source artifact metadata against `VOCAB.md`; keep only canonical IDs in `canonical_tags`; move noncanonical useful phrases to `candidate_terms`.
3. Build candidate topics from `TOPICS.md` using exact domain/subdomain matches, canonical tag overlap, alias/include-term matches in the source title/TL;DR/key points, and absence of topic `Exclude terms`.
4. If no candidates exist, set the source artifact `routing_status` to `no-topic-match`, update manifest `Route status` to `no-topic-match`, record the count/source IDs in the acquisition run log when one exists, and stop. Do not write `RELATIONS.md` and do not dirty any topic.
5. For each candidate topic, run a bounded verifier using only the source summary plus the candidate topic row/path/scope. The verifier must output structured rows with `include: true|false`, `relation`, `impact`, `confidence`, and `reason`.
6. For each verifier row where `include: true`, create or update one relation edge in `RELATIONS.md`. `Edge ID` is `edge--<source_id>--<topic_id>--<source_content_hash_8>` with `/`, spaces, and dots in `topic_id` replaced by `-`.
7. After relation rows are merged, recompute every affected topic's dirty fields in `TOPICS.md` from `RELATIONS.md`; never increment dirty counts blindly.
8. Set the source artifact `routing_status` and manifest `Route status` to `routed` if at least one pending relation edge was written; otherwise set both to `no-topic-match`.

Failure handling for this step: if `VOCAB.md` is missing a needed canonical term, do not create it from acquisition. Store the term in `candidate_terms`, set `routing_status: routing-blocked` only when routing cannot proceed without the missing term, and report the exact missing term in the acquisition or route run output.

### T6. Define dirty state, quick-answer behavior, and persisted delta refresh

Update the first plan so dirty state is defined by `RELATIONS.md`, not by hand-maintained topic frontmatter:

```text
A topic is dirty iff RELATIONS.md contains at least one row with Status=pending for that Topic ID.
```

`TOPICS.md` is a denormalized quick lookup cache. Marking a topic dirty means recomputing these `TOPICS.md` columns from `RELATIONS.md`:

- `Freshness state`: `dirty` when pending edges exist, `current` when none exist, `refreshing` only while a refresh subagent is actively applying a pass, `blocked` when the last refresh attempt failed and pending edges remain, `archived` when the topic is intentionally inactive.
- `Dirty count`: count of `pending` relation edges for the topic.
- `Pending edge IDs`: comma-separated pending edge IDs, stable sorted by `Source seq` ascending.
- `Newest pending source seq`: max `Source seq` among pending edges; blank or `0` when none exist.
- `Source watermark`: max source seq incorporated by the latest successful refresh pass.

Update quick-answer behavior in the first plan:

- Quick answer must read `TOPICS.md` first after resolving a topic.
- If `Freshness state=current`, quick answer may read the topic `INDEX.md` and answer.
- If `Freshness state=dirty|refreshing|blocked`, quick answer must not answer from topic `INDEX.md` plus unpersisted pending deltas.
- Current safe Phase 1 behavior: quick answer halts with topic path, freshness state, dirty count, and pending edge IDs.
- Later fresh-answer Phase 2 behavior: quick answer delegates `/atlas-refresh --topic <topic-id>` to a refresh subagent using the topic row's `Refresh model`; only after the refresh subagent persists the delta and `TOPICS.md` returns to `current` may quick answer produce the answer.

Define the delta refresh checklist exactly in the first plan:

1. Read `ARCHITECTURE.md`, `VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, the target topic `INDEX.md`, pending source artifacts listed by `Pending edge IDs`, and any optional split files referenced by the topic `INDEX.md`.
2. Set the target topic `Freshness state` to `refreshing` in `TOPICS.md` before writing the pass file.
3. Create the research pass file first at `topics/<topic-slug>/passes/YYYY-MM-DD--pending-source-delta.md` with frontmatter `schema_version`, `note_type: research-pass`, `managed_by: atlas`, `topic_id`, `trigger: pending-source-refresh`, `input_edges`, `input_sources`, `started`, `completed`, `coverage_state`, and `confidence`.
4. In the pass body, include `## Delta summary`, `## Source artifacts applied`, `## Changes required`, `## Managed sections patched`, `## Registry updates`, and `## Checks`.
5. Patch only managed sections in topic `INDEX.md`. Do not rewrite the whole file unless the file is empty or structurally broken.
6. Scale patch size to delta size: append evidence-map rows and recent-change bullets for small supporting deltas; update `Current answer`, `Decision tree`, or `Recommendation matrix` only when pending sources materially change the topic answer; update caveats/gaps when evidence contradicts or weakens prior claims.
7. Mark applied relation rows in `RELATIONS.md` as `applied` and set `Applied in pass` to the pass path.
8. Recompute the topic row in `TOPICS.md` from `RELATIONS.md`; if no pending edges remain, set `Freshness state=current`, `Dirty count=0`, clear `Pending edge IDs`, clear `Newest pending source seq`, set `Last synthesized` to the completion date, and set `Source watermark` to the max applied source seq.
9. If any required write fails after `refreshing` was set, leave relation rows `pending`, set `Freshness state=blocked`, and add the failure reason to the pass file if it exists; otherwise add the failure reason to the refresh run output. Do not mark edges applied on partial failure.
10. Run registry consistency checks before answering or marking the refresh complete.

Failure handling for this step: if a dirty topic is `blocked`, `/atlas-answer` must halt and print the blocked state plus pending edge IDs. It must not trigger another refresh automatically until `/atlas-refresh --retry-blocked <topic-id>` is explicitly requested in a later skill contract.

### T7. Update slash command contracts, hooks policy, phases, and SQLite adapter timing

Update the first plan's `Future skill contract` requirements with this table:

| Command | Role | Writes |
|---|---|---|
| `/atlas-source` | Ingest explicit URLs/files/repos into source artifacts, manifest rows, and route-source workflow. | source artifacts, source manifest, registry route fields |
| `/atlas-acquire` | Bounded acquisition from feeds/watchlists/inbox/search, then source ingestion and route-source workflow. | source artifacts, source manifest, acquisition run logs, relation edges |
| `/atlas-route` | Re-run route-source workflow for one source or source range. | source routing status, `RELATIONS.md`, `TOPICS.md` dirty cache |
| `/atlas-research` | Create or intentionally refresh durable topic research from vault sources; acquisition only with explicit flag. | topic `INDEX.md`, pass files, topic registry rows |
| `/atlas-refresh` | Apply pending relation edges to dirty topics through persisted delta passes. | pass files, topic `INDEX.md`, `RELATIONS.md`, `TOPICS.md` |
| `/atlas-answer` | Resolve topic and answer only when registry says topic is current; otherwise halt with deterministic dirty-state output in Phase 1. | none |
| `/atlas-index` | Maintain and repair `VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, manifest consistency, and broken links. | registry/index files only when repair or promotion flag is explicit |
| `/atlas-audit` | Read-only vault health report for dirty topics, schema drift, orphaned relations, and registry inconsistency. | none by default |
| `/atlas-migrate` | Apply explicit schema migrations. | versioned migration edits only |

Keep the legacy `digest` skill temporarily. Update the first plan to say `digest` is a compatibility adapter for source ingestion during transition and is removed only after `/atlas-source`, `/atlas-acquire`, `/atlas-research`, `/atlas-refresh`, and `/atlas-answer` exist and pass smoke checks.

Update hook policy in the first plan:

- Do not put LLM synthesis in hooks/extensions.
- Use slash commands for full workflow checklists and any LLM work.
- Hooks/extensions may later enforce cheap idempotent guardrails only: route after a source artifact write, reject answer attempts on dirty topics, or surface registry consistency failures.
- Because `.config/agents/harnesses/omp/config.yml` currently shows no Atlas-specific extension, the current implementation uses explicit slash-command workflows first and leaves hook automation to a later phase.

Replace the old automation phases in the first plan with these exact phases:

1. **Phase 1 — Markdown registry and safe freshness**: implement `VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, route-source, dirty marking, and `/atlas-answer` halting on dirty topics. Do not implement SQLite. Move to Phase 2 when route-source creates stable relation edges without vocabulary drift and quick answers never silently use dirty topics.
2. **Phase 2 — Persisted refresh before answer**: implement `/atlas-refresh --topic <topic-id>` and allow a fresh-answer path to delegate a refresh subagent before answering. Move to Phase 3 when persisted delta passes reliably patch only affected managed sections and registry consistency checks pass.
3. **Phase 3 — Dedicated refresh cron**: create a separate refresh cron that processes dirty topics using the same refresh checklist. Source acquisition cron remains cheap and does not refresh topics. The refresh cron stops before the next topic when estimated context would exceed a configurable context budget, initially documented as `max_context_tokens: 200000`.
4. **Phase 4 — Optional SQLite registry cache**: add SQLite only if Markdown registry lookup or consistency checks are observably painful after Phase 3. SQLite is a derived cache at `vault://atlas/.atlas/registry.sqlite`, rebuilt from Markdown, and accessed only through `.config/agents/skills/atlas-index/scripts/atlas-registry.py`. Do not store source artifacts, research passes, or topic overviews in SQLite. If no lookup pain exists, skip this phase.
5. **Phase 5 — Priority and impact routing**: use `Impact`, `Relation`, topic `Refresh model`, and archived/manual-only states to order refresh work. Move here only after Phase 3 refresh quality is stable; Phase 4 is optional.
6. **Phase 6 — Hierarchical rollups and optional retrieval adapter**: add subdomain/domain rollups or lexical/vector retrieval only if source volume makes direct topic refresh too large. Retrieval storage may use SQLite FTS or a separate vector adapter only after a migration plan defines the adapter interface and rebuild path.
7. **Phase 7 — Self-healing audit and migration**: add repair workflows that rebuild registry caches from source/topic artifacts, detect broken links/schema drift, and apply explicit migrations through `/atlas-migrate`.

Add this future SQLite adapter contract to the first plan but mark it as Phase 4 only, not Phase 1 work:

```md
If SQLite is introduced, create `.config/agents/skills/atlas-index/scripts/atlas-registry.py` as the sole database interface. Copy the local Python CLI style used by `.config/agents/skills/mnemopi-cleanup/scripts/mnemopi-status`: stdlib Python, `argparse`, `pathlib`, `sqlite3`, explicit JSON output, explicit exit codes, and no ORM dependency. The Phase 4 adapter supports `init`, `rebuild`, `check`, and read-only `query` commands first. It does not expose direct table CRUD while Markdown remains canonical. If a later migration makes SQLite canonical for registries, add mutation commands only through structured event commands such as `apply-source-routed`, `apply-topic-refreshed`, and `promote-vocab-term`; agents still must not issue ad hoc SQL.
```

Failure handling for this step: if `.config/agents/skills/atlas-index/` does not exist when Phase 4 is reached, create that skill as part of the Phase 4 migration plan. Do not create it during Phase 1 just to reserve the path.

### T8. Replace verification in the foundation plan

Update `.agents/plans/2026-06-30-1339_research-framework-vault.md` verification so it proves the new plan state before implementation and the new behavior after implementation.

Add these plan-content checks:

```md
- [ ] `read .agents/plans/2026-06-30-1339_research-framework-vault.md` shows `## Precedence and execution order` and states that `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` must be applied before this implementation plan is executed.
- [ ] `read vault://atlas/ARCHITECTURE.md` shows `12-Factor workflow basis`, `Registry layer`, `Deterministic routing`, `Dirty state and refresh`, `SQLite policy`, `Future skill contract`, and `Framework philosophy`.
- [ ] `read vault://atlas/ARCHITECTURE.md` states that Phase 1 canonical state is Markdown and SQLite is not part of Phase 1.
- [ ] `read vault://atlas/summaries/registry/VOCAB.md`, `read vault://atlas/summaries/registry/TOPICS.md`, and `read vault://atlas/summaries/registry/RELATIONS.md` show the exact table headers specified in this plan.
- [ ] `grep` on `.config/agents/skills/digest/SKILL.md` for `vault://digest` returns no matches.
- [ ] `grep` on `.config/agents/skills/digest/SKILL.md` for `sqlite|SQLite|registry.sqlite` returns no Phase 1 implementation instructions; SQLite may appear only as a future phase or migration policy.
```

Add these behavior checks:

```md
- [ ] Routing smoke test: create or use one source artifact with `canonical_tags` values present in `VOCAB.md` and one existing topic row in `TOPICS.md` whose include terms match the source. Run the route-source workflow. Expected: `RELATIONS.md` has one pending edge, `TOPICS.md` marks exactly that topic dirty, source manifest `Route status` becomes `routed`, and no topic `INDEX.md` is changed.
- [ ] No-match smoke test: route one source artifact that matches no `TOPICS.md` row. Expected: no `RELATIONS.md` row is added, no topic row is dirty, source artifact and manifest `Route status` become `no-topic-match`, and no `UNCLAIMED-SOURCES.md` file exists.
- [ ] Vocabulary-drift check: after acquisition, every value in source artifact `canonical_tags` exists in `VOCAB.md`; any new noncanonical phrase appears only in `candidate_terms`.
- [ ] Dirty quick-answer check: with a `TOPICS.md` row marked `dirty` from pending edges, invoke the quick-answer workflow for that topic in Phase 1. Expected: it halts with topic path, dirty count, and pending edge IDs; it does not answer from stale topic `INDEX.md` and does not compose an unpersisted pending-delta answer.
- [ ] Delta refresh check: run `/atlas-refresh --topic <topic-id>` on a dirty topic. Expected: one pass file is created, topic `INDEX.md` managed sections are patched with the smallest required diff, `RELATIONS.md` pending edges become `applied` with `Applied in pass` set, `TOPICS.md` recomputes the topic to `current` with `Dirty count` 0, and `/atlas-answer` can answer afterward.
- [ ] Registry consistency check: for every `TOPICS.md` row, `Dirty count` equals the number of `RELATIONS.md` rows where `Topic ID` matches and `Status=pending`; `Pending edge IDs` exactly lists those edge IDs; `Freshness state` is `current` iff `Dirty count` is 0 unless the topic is `archived`.
```

Keep the existing smoke tests for explicit source digestion, duplicate source skipping, vault-only research, and acquisition-first research, but update their expected outputs so routing status and registry files are checked after source artifact creation.

Failure handling for this step: if a smoke test cannot be run through a slash command because the slash command does not exist yet, run the equivalent explicit agent prompt using the relevant skill and record that as the verification method in the completion summary.

## Critical files & anchors

- `.agents/plans/2026-06-30-1339_research-framework-vault.md` — foundation Atlas implementation plan; execute this routing-refresh plan against it before vault/skill implementation.
- `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` — mirror of this local plan; use as the precedence reference in the foundation plan, but do not hand-edit the mirror while planning.
- `.config/agents/skills/digest/SKILL.md` — legacy skill whose freeform facet routing must be replaced by Atlas registry contracts during implementation.
- `.config/agents/skills/digest/assets/source-summary-template.md` — source template that must gain `source_seq`, canonical tags, candidate terms, and routing status.
- `.config/agents/skills/mnemopi-cleanup/scripts/mnemopi-status` — local stdlib-Python SQLite CLI style to copy only if the optional Phase 4 SQLite adapter is later implemented.

## Verification

Before resolving this plan, read `local://atlas-routing-refresh-plan.md` and confirm it contains all of these exact decisions:

```text
Phase 1 canonical state is Markdown
SQLite is not part of Phase 1
Optional SQLite registry cache
12-Factor workflow basis
Precedence and execution order
Do not add `UNCLAIMED-SOURCES.md`
```

After approval and execution of this plan, verify the foundation plan was updated with these exact checks from the repo root:

```text
read .agents/plans/2026-06-30-1339_research-framework-vault.md
```

Expected observable content:

- `## Precedence and execution order`
- `12-Factor workflow basis`
- `SQLite policy`
- `vault://atlas/summaries/registry/`
- `VOCAB.md`, `TOPICS.md`, and `RELATIONS.md`
- `Phase 1 canonical state is Markdown`
- `SQLite is not part of Phase 1`
- `Optional SQLite registry cache`
- route-source workflow steps 1-8
- dirty state defined by pending rows in `RELATIONS.md`
- Phase 1 `/atlas-answer` halts on dirty topics

Run these text checks after the foundation plan edit:

```text
grep pattern: "Phase 1 canonical state is Markdown|SQLite is not part of Phase 1|Optional SQLite registry cache" paths: [".agents/plans/2026-06-30-1339_research-framework-vault.md"]
grep pattern: "UNCLAIMED-SOURCES.md" paths: [".agents/plans/2026-06-30-1339_research-framework-vault.md"]
grep pattern: "12-Factor workflow basis|Reducer model|Own control flow" paths: [".agents/plans/2026-06-30-1339_research-framework-vault.md"]
```

Expected results:

- The SQLite grep returns the Markdown-first and optional-cache policy only.
- The `UNCLAIMED-SOURCES.md` grep returns only negative instructions saying not to add it.
- The 12-Factor grep returns the planned architecture basis and reducer/control-flow text.

No shell command is required to verify this local plan. Use `read`/`grep` tools; do not edit cwd plan files while still in plan mode.

## Assumptions & contingencies

- Recommendation is settled: do not build Atlas around SQLite for everything, and do not use SQLite in Phase 1. The robust lean default is Markdown canonical artifacts plus Markdown registries because they are Obsidian-native, human-readable, linkable, inspectable, and directly available through `vault://`.
- Hybrid SQLite is settled as a later optional optimization: if needed, use SQLite only as a derived registry/index cache first; keep daily source summaries, research passes, topic overviews, and acquisition logs as Markdown.
- If SQLite is introduced later, use a single deterministic adapter script instead of raw SQL from agents. The script path is `.config/agents/skills/atlas-index/scripts/atlas-registry.py`; it is not created in Phase 1.
- The first implementation plan must not be executed until this routing-refresh plan has been applied to it. After this routing-refresh plan is applied, implement the revised first plan top-to-bottom.
- The repo-local routing-refresh file `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` is an auto-mirrored artifact of `local://atlas-routing-refresh-plan.md`; planning edits happen only in `local://atlas-routing-refresh-plan.md`.
- If later execution discovers the mirror filename changed by datetime, update the precedence reference to the latest `.agents/plans/*_atlas-routing-refresh.md` mirror and continue; do not duplicate routing-refresh plans.
- Existing local SQLite code is read-only and Mnemopi-specific. It provides script style only, not reusable Atlas CRUD logic.

## Completion Summary

T1-T8 were applied to `.agents/plans/2026-06-30-1339_research-framework-vault.md`. The foundation plan now has explicit routing-refresh precedence, Markdown-first canonical state, deferred SQLite policy, 12-Factor workflow basis, Markdown registry schemas, source routing and dirty-refresh reducer contracts, slash-command ownership, hook guardrail policy, phased rollout, and revised verification. SQLite remains out of Phase 1 and appears only as an optional Phase 4 derived registry cache behind `.config/agents/skills/atlas-index/scripts/atlas-registry.py`. No vault runtime files, skill files, templates, SQLite files, or Atlas scripts were created while applying this routing-refresh plan. The foundation plan T1 is marked complete; execute the revised foundation plan from T2 next.
