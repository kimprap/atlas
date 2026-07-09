# Research Framework Vault Skill Implementation Plan

**Datetime**: 2026-06-30-1339
**Scope**: `vault://atlas/` research-library architecture, `.config/agents/skills/digest/` instructions/templates, and starter indexes/manifests under `vault://atlas/summaries/`.
**Summary**: Refine the research vault into an agent-first “atlas” with a stable `ARCHITECTURE.md` source of truth, source-summary dedupe, vault-only topic synthesis, optional acquisition-first refresh, lean topic files, and future-proof schema/versioning hooks. Source artifacts are time-bucketed evidence; research topics are deterministic answer contracts backed by source artifacts.
**Status**: DONE

## Context

This revision incorporates the user's latest framework decisions:

- The parent vault/root has already been renamed to `atlas`; implementation should verify `vault://atlas/` resolves and must not create a duplicate `digest` root.
- `vault://atlas/todos/` is a legacy folder and must not be removed, renamed, cleaned up, or treated as part of the new summaries architecture.
- Source artifacts should not be domain/subdomain organized. Domains and subdomains belong in frontmatter, tags, indexes, and research links.
- A single `summaries/sources/MANIFEST.md` is acceptable for expected scale. If it eventually grows beyond practical lookup size, shard later without changing source artifact identity.
- Per-topic folders should be lean: one canonical topic `INDEX.md` plus immutable dated passes by default. Extra split files are created only when thresholds are met.
- `ARCHITECTURE.md` should be the comprehensive source of truth for the framework. Future agents improving or using the framework should read it before making decisions.
- `ARCHITECTURE.md` should end with a succinct framework philosophy so future changes preserve the lean, robust, deterministic, and flexible design intent.
- Skills relevant to the framework will be created separately. This plan must make the vault architecture self-explanatory enough that future skills can rely on `ARCHITECTURE.md` instead of hallucinating conventions.

Decision: keep source ingestion, source acquisition, research synthesis, answer lookup, and rollups as separate modes with narrow file ownership. Research synthesis is vault-only by default. Live web search is allowed only in acquisition-first mode, where new web results must first become source-summary artifacts before they can affect topic research.

Atlas Phase 1 canonical state is Markdown in the Obsidian vault: source artifacts, acquisition run logs, topic `INDEX.md` files, research pass files, `summaries/sources/MANIFEST.md`, and `summaries/registry/*.md` tables. Do not build Atlas around SQLite in Phase 1, and do not store source summaries, research passes, topic overviews, or registry rows only in SQLite. Markdown remains the human-readable, Obsidian-native, linkable, inspectable source of truth.

SQLite is a later optimization, not the initial architecture. If registry Markdown files become operationally painful after persisted refresh workflows are stable, add SQLite as a derived registry/index cache only. The cache may accelerate lookup and consistency checks, but it must be rebuildable from Markdown artifacts and must not become the only copy of source/topic/relation state without a separate explicit schema-migration plan.

External-design basis: 12-Factor Agents is the first and primary architecture basis for Atlas. Anthropic agent guidance, HumanLayer harness engineering, and LangChain context engineering are supporting references only, not co-equal architecture drivers.

## Precedence and execution order

Apply `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` before executing this implementation plan. The routing-refresh plan is a plan-consolidation pass: it updates this plan with deterministic Atlas registry, freshness, SQLite, and workflow-control decisions. After that pass is complete, execute this revised plan top-to-bottom: verify the vault root, create `ARCHITECTURE.md`, update the legacy `digest` skill, update templates, create starter vault files, then run smoke checks.

Do not implement vault artifacts or skill changes from the older version of this plan before the routing-refresh pass is complete. The final implementation source of truth is this revised plan plus `vault://atlas/ARCHITECTURE.md` once created.

## Tasks

- [x] T1. Apply routing-refresh plan consolidation before implementation: update this plan with the registry layer, SQLite decision, 12-Factor design basis, dirty refresh workflow, and revised verification checks.
  completed 2026-07-02-1709
- [x] T2. Verify `vault://atlas/` resolves and preserve legacy `vault://atlas/todos/` without removing, renaming, cleaning, or migrating it.
  completed 2026-07-02-1726
- [x] T3. Establish `vault://atlas/ARCHITECTURE.md` as the framework source of truth, covering layout, artifact roles, registry layer, mode ownership, 12-Factor workflow basis, schema/versioning, source identity/dedupe, topic routing, dirty state, optional SQLite migration policy, future skill contracts, and framework philosophy.
  completed 2026-07-02-1726
- [x] T4. Rewrite `.config/agents/skills/digest/SKILL.md` so the current entrypoint reads `vault://atlas/ARCHITECTURE.md`, uses `vault://atlas/summaries/`, and defines source digest, acquisition, vault-only research, acquisition-first research, and rollup modes.
  completed 2026-07-02-1745
- [x] T5. Revise `.config/agents/skills/digest/assets/source-summary-template.md` so source summaries include canonical URL identity, dedupe metadata, refresh metadata, and shared assessment signals.
  completed 2026-07-02-1745
- [x] T6. Create `.config/agents/skills/digest/assets/research-library-templates.md` with templates for subdomain indexes, topic `INDEX.md`, dated passes, optional split files, and source acquisition run logs.
  completed 2026-07-02-1756
- [x] T7. Create starter vault files at `vault://atlas/summaries/INDEX.md`, `vault://atlas/summaries/sources/MANIFEST.md`, `vault://atlas/summaries/sources/INDEX.md`, and `vault://atlas/summaries/research/INDEX.md` without pre-creating empty domains, subdomains, or topics, while preserving `vault://atlas/todos/`.
  completed 2026-07-02-1756
- [x] T8. Verify the revised architecture, skill instructions, templates, source dedupe flow, topic split rules, legacy todos preservation, and smoke-test behavior.
  completed 2026-07-02-2019

## Verification / Done criteria

- [x] `read vault://atlas/` confirms the Atlas vault root resolves.
- [x] `read vault://atlas/todos/` confirms the legacy todos folder still exists and was not removed or migrated.
- [x] `read .agents/plans/2026-06-30-1339_research-framework-vault.md` shows `## Precedence and execution order` and states that `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` must be applied before this implementation plan is executed.
- [x] `read vault://atlas/ARCHITECTURE.md` shows `12-Factor workflow basis`, `Registry layer`, `Deterministic routing`, `Dirty state and refresh`, `SQLite policy`, `Future skill contract`, and `Framework philosophy`.
- [x] `read vault://atlas/ARCHITECTURE.md` states that Phase 1 canonical state is Markdown and SQLite is not part of Phase 1.
- [x] `read vault://atlas/summaries/registry/VOCAB.md`, `read vault://atlas/summaries/registry/TOPICS.md`, and `read vault://atlas/summaries/registry/RELATIONS.md` show the exact table headers specified in this plan.
- [x] `grep` on `.config/agents/skills/digest/SKILL.md` for `vault://digest` returns no matches.
- [x] `grep` on `.config/agents/skills/digest/SKILL.md` for `sqlite|SQLite|registry.sqlite` returns no Phase 1 implementation instructions; SQLite may appear only as a future phase or migration policy.
- [x] Routing smoke test: create or use one source artifact with `canonical_tags` values present in `VOCAB.md` and one existing topic row in `TOPICS.md` whose include terms match the source. Run the route-source workflow. Expected: `RELATIONS.md` has one pending edge, `TOPICS.md` marks exactly that topic dirty, source manifest `Route status` becomes `routed`, and no topic `INDEX.md` is changed.
- [x] No-match smoke test: route one source artifact that matches no `TOPICS.md` row. Expected: no `RELATIONS.md` row is added, no topic row is dirty, source artifact and manifest `Route status` become `no-topic-match`, and no `UNCLAIMED-SOURCES.md` file exists.
- [x] Vocabulary-drift check: after acquisition, every value in source artifact `canonical_tags` exists in `VOCAB.md`; any new noncanonical phrase appears only in `candidate_terms`.
- [x] Dirty quick-answer check: with a `TOPICS.md` row marked `dirty` from pending edges, invoke the quick-answer workflow for that topic in Phase 1. Expected: it halts with topic path, dirty count, and pending edge IDs; it does not answer from stale topic `INDEX.md` and does not compose an unpersisted pending-delta answer.
- [x] Delta refresh check: run `/atlas-refresh --topic <topic-id>` on a dirty topic. Expected: one pass file is created, topic `INDEX.md` managed sections are patched with the smallest required diff, `RELATIONS.md` pending edges become `applied` with `Applied in pass` set, `TOPICS.md` recomputes the topic to `current` with `Dirty count` 0, and `/atlas-answer` can answer afterward.
- [x] Registry consistency check: for every `TOPICS.md` row, `Dirty count` equals the number of `RELATIONS.md` rows where `Topic ID` matches and `Status=pending`; `Pending edge IDs` exactly lists those edge IDs; `Freshness state` is `current` iff `Dirty count` is 0 unless the topic is `archived`.
- [x] Explicit source digestion smoke test: invoke `/digest https://github.com/karpathy/autoresearch` or explicitly prompt the agent to use the `digest` skill on that URL. Expected: one source artifact appears under `vault://atlas/summaries/sources/artifacts/<current-year>/<current-year-month>/`, the manifest gains one row keyed by canonical URL/source-id with `Source seq` and `Route status`, route-source checks the registry files after artifact creation, and repeating the same URL skips duplicate summarization without creating duplicate relation edges.
- [x] Vault-only research smoke test: after at least one relevant source artifact exists, invoke `/digest research --vault-only programmatic agent engineering`. Expected: topic files appear under `vault://atlas/summaries/research/agentic-development/agent-research/topics/programmatic-agent-engineering/`; `TOPICS.md` has or receives a matching topic row; no raw web URL is cited unless a corresponding source artifact exists; any insufficiency is recorded as `coverage_state: partial|insufficient` instead of overclaiming.
- [x] Acquisition-first smoke test: invoke `/digest research --acquire "best way to create sourdough"` or explicitly ask for research with acquisition allowed. Expected: new source summaries are created first under `sources/artifacts/...`; the source manifest records `Source seq` and `Route status`; route-source checks `VOCAB.md`, `TOPICS.md`, and `RELATIONS.md`; topic synthesis under `research/cooking/bread/topics/sourdough-method/INDEX.md` links to source artifacts.
- [x] If a smoke test cannot be run through a slash command because the slash command does not exist yet, run the equivalent explicit agent prompt using the relevant skill and record that as the verification method in the completion summary.

## Approach

### T1. Apply routing-refresh plan consolidation before implementation

Apply `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` first by updating this plan with the registry layer, SQLite decision, 12-Factor design basis, dirty refresh workflow, and revised verification checks. Do not create vault files, skill files, templates, SQLite files, or Atlas scripts during this consolidation task.

### T2. Verify Atlas root and preserve legacy todos

Before writing framework files, verify `vault://atlas/` resolves. The user has already renamed the vault/root from `digest` to `atlas`; implementation should treat `atlas` as canonical and should not create a duplicate `digest` root.

Also verify `vault://atlas/todos/` exists. This is a legacy folder. Do not remove, rename, migrate, clean, or fold it into `summaries/`. The new framework may leave it untouched and may mention it in `ARCHITECTURE.md` only as legacy state.

### T3. Establish `ARCHITECTURE.md`

Create `vault://atlas/ARCHITECTURE.md` as the source of truth for the framework. Future agents that use, audit, or improve the research framework must read this file before changing behavior.

`ARCHITECTURE.md` must include these sections:

```md
# Atlas Architecture

## Framework invariants
## 12-Factor workflow basis
## Directory layout
## Artifact roles
## Mode ownership
## Source identity and dedupe
## Source refresh policy
## Topic routing
## Topic split policy
## Managed sections
## Schema migration
## SQLite policy
## Future skill contract
## Framework philosophy
```

`## 12-Factor workflow basis` must appear immediately after `## Framework invariants`:

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

Do not add a separate `EVENTS.md` just to mimic event sourcing. For Phase 1, acquisition run logs, research pass files, source artifacts, manifest rows, and relation rows are the event/history records. Add a separate event log only in a future migration if audits cannot be reconstructed from those artifacts.

Required invariants:

- Source artifacts are evidence snapshots and are stored by time, not by domain/subdomain.
- Research topics are deterministic answer contracts backed by source artifacts.
- Research synthesis is vault-only unless the caller explicitly chooses acquisition-first mode.
- Acquisition-first mode must materialize source artifacts before synthesis.
- Indexes route agents to the right artifact; they must not duplicate full research bodies.
- Topic folders start lean and split only when thresholds are met.
- Every managed artifact has `schema_version`, `note_type`, and `managed_by: atlas`.
- Future skills are separate from this plan; they should rely on `ARCHITECTURE.md` and the artifact contracts instead of inventing conventions.
- `vault://atlas/todos/` is legacy state. Preserve it unchanged; do not make it part of the managed summaries architecture.
- Phase 1 canonical state is Markdown in the Obsidian vault; SQLite is not part of Phase 1.

Directory layout:

```text
vault://atlas/
├── ARCHITECTURE.md
├── todos/                 # legacy; preserve untouched
└── summaries/
    ├── INDEX.md
    ├── domains/
    │   └── <domain>.md
    ├── sources/
    │   ├── INDEX.md
    │   ├── MANIFEST.md
    │   ├── runs/
    │   │   └── <YYYY>/
    │   │       └── <YYYY-MM>/
    │   │           └── <YYYY-MM-DD>--<run-slug>.md
    │   └── artifacts/
    │       └── <YYYY>/
    │           └── <YYYY-MM>/
    │               └── <YYYY-MM-DD>--<kind>--<slug>--<source-id>.md
    ├── registry/
    │   ├── VOCAB.md
    │   ├── TOPICS.md
    │   └── RELATIONS.md
    └── research/
        ├── INDEX.md
        └── <domain>/
            └── <subdomain>/
                ├── INDEX.md
                └── topics/
                    └── <topic-slug>/
                        ├── INDEX.md
                        ├── passes/
                        │   └── <YYYY-MM-DD>--<pass-slug>.md
                        ├── SOURCES.md optional
                        ├── DECISIONS.md optional
                        └── HISTORY.md optional
```

Registry layer:

```text
vault://atlas/summaries/registry/
├── VOCAB.md
├── TOPICS.md
└── RELATIONS.md
```

- `VOCAB.md` — canonical vocabulary and alias registry. This is the only place where canonical domains, subdomains, tags, source kinds, and reusable aliases are declared.
- `TOPICS.md` — topic registry and freshness cache. This is the quick lookup table for resolving a topic, checking dirty state, finding the topic path, and deciding refresh model without reading topic files.
- `RELATIONS.md` — source-topic edge ledger. This is the source of truth for pending/applied source-to-topic edges.

Do not add `UNCLAIMED-SOURCES.md`. For unmatched sources, acquisition run logs may record counts and source IDs that matched no topic, but Atlas must not maintain a global unclaimed-source queue in this iteration.

Mode ownership:

| Mode | Reads | Writes |
|---|---|---|
| source digest | source manifest | one source artifact, source manifest, source index |
| source acquisition | feeds/inbox/watchlists, source manifest | source artifacts, source manifest, acquisition run log |
| research vault-only | architecture, source manifest, source artifacts, subdomain/topic indexes | topic `INDEX.md`, one pass file, subdomain index |
| research acquisition-first | same as source acquisition, then vault-only research | source artifacts first, then topic files |
| answer lookup | TOPICS.md, topic `INDEX.md` only when current, source artifacts when provenance is needed | nothing |
| rollup | managed artifacts | root/domain/source/research/subdomain indexes |

Dirty state and refresh:

```text
A topic is dirty iff RELATIONS.md contains at least one row with Status=pending for that Topic ID.
```

`TOPICS.md` is a denormalized quick lookup cache. Marking a topic dirty means recomputing these `TOPICS.md` columns from `RELATIONS.md`:

- `Freshness state`: `dirty` when pending edges exist, `current` when none exist, `refreshing` only while a refresh subagent is actively applying a pass, `blocked` when the last refresh attempt failed and pending edges remain, `archived` when the topic is intentionally inactive.
- `Dirty count`: count of `pending` relation edges for the topic.
- `Pending edge IDs`: comma-separated pending edge IDs, stable sorted by `Source seq` ascending.
- `Newest pending source seq`: max `Source seq` among pending edges; blank or `0` when none exist.
- `Source watermark`: max source seq incorporated by the latest successful refresh pass.

Quick-answer behavior:

- Quick answer must read `TOPICS.md` first after resolving a topic.
- If `Freshness state=current`, quick answer may read the topic `INDEX.md` and answer.
- If `Freshness state=dirty|refreshing|blocked`, quick answer must not answer from topic `INDEX.md` plus unpersisted pending deltas.
- Current safe Phase 1 behavior: quick answer halts with topic path, freshness state, dirty count, and pending edge IDs.
- Later fresh-answer Phase 2 behavior: quick answer delegates `/atlas-refresh --topic <topic-id>` to a refresh subagent using the topic row's `Refresh model`; only after the refresh subagent persists the delta and `TOPICS.md` returns to `current` may quick answer produce the answer.

Delta refresh checklist:

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

If a dirty topic is `blocked`, `/atlas-answer` must halt and print the blocked state plus pending edge IDs. It must not trigger another refresh automatically until `/atlas-refresh --retry-blocked <topic-id>` is explicitly requested in a later skill contract.

Managed section convention:

```md
<!-- atlas:managed:start <section-name> -->
...
<!-- atlas:managed:end <section-name> -->
```

Agents should patch managed sections instead of rewriting whole files unless a file is empty or structurally broken.

SQLite policy must appear under `## Schema migration` or immediately before `## Future skill contract`:

```md
## SQLite policy

- Phase 1 uses Markdown as canonical state. SQLite is not part of Phase 1.
- Source artifacts, topic overviews, research passes, and acquisition run logs stay as Markdown files even if SQLite is introduced later.
- Registry Markdown files are canonical until an explicit schema migration says otherwise.
- A later SQLite registry cache may be introduced only after Markdown routing, persisted delta refresh, and registry consistency checks are working.
- If introduced, SQLite is a derived cache at `vault://atlas/.atlas/registry.sqlite`, rebuilt from Markdown by an Atlas registry adapter. Do not hand-edit the database and do not let agents issue ad hoc SQL.
- If a future migration promotes SQLite from derived cache to canonical registry storage, that migration must keep Markdown export views for Obsidian browsing and must define rollback back to Markdown.
```

Future skill contract requirements:

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

Keep the legacy `digest` skill temporarily. `digest` is a compatibility adapter for source ingestion during transition and is removed only after `/atlas-source`, `/atlas-acquire`, `/atlas-research`, `/atlas-refresh`, and `/atlas-answer` exist and pass smoke checks.

Hook policy:

- Do not put LLM synthesis in hooks/extensions.
- Use slash commands for full workflow checklists and any LLM work.
- Hooks/extensions may later enforce cheap idempotent guardrails only: route after a source artifact write, reject answer attempts on dirty topics, or surface registry consistency failures.
- Because `.config/agents/harnesses/omp/config.yml` currently shows no Atlas-specific extension, the current implementation uses explicit slash-command workflows first and leaves hook automation to a later phase.

Automation phases:

1. **Phase 1 — Markdown registry and safe freshness**: implement `VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, route-source, dirty marking, and `/atlas-answer` halting on dirty topics. Do not implement SQLite. Move to Phase 2 when route-source creates stable relation edges without vocabulary drift and quick answers never silently use dirty topics.
2. **Phase 2 — Persisted refresh before answer**: implement `/atlas-refresh --topic <topic-id>` and allow a fresh-answer path to delegate a refresh subagent before answering. Move to Phase 3 when persisted delta passes reliably patch only affected managed sections and registry consistency checks pass.
3. **Phase 3 — Dedicated refresh cron**: create a separate refresh cron that processes dirty topics using the same refresh checklist. Source acquisition cron remains cheap and does not refresh topics. The refresh cron stops before the next topic when estimated context would exceed a configurable context budget, initially documented as `max_context_tokens: 200000`.
4. **Phase 4 — Optional SQLite registry cache**: add SQLite only if Markdown registry lookup or consistency checks are observably painful after Phase 3. SQLite is a derived cache at `vault://atlas/.atlas/registry.sqlite`, rebuilt from Markdown, and accessed only through `.config/agents/skills/atlas-index/scripts/atlas-registry.py`. Do not store source artifacts, research passes, or topic overviews in SQLite. If no lookup pain exists, skip this phase.
5. **Phase 5 — Priority and impact routing**: use `Impact`, `Relation`, topic `Refresh model`, and archived/manual-only states to order refresh work. Move here only after Phase 3 refresh quality is stable; Phase 4 is optional.
6. **Phase 6 — Hierarchical rollups and optional retrieval adapter**: add subdomain/domain rollups or lexical/vector retrieval only if source volume makes direct topic refresh too large. Retrieval storage may use SQLite FTS or a separate vector adapter only after a migration plan defines the adapter interface and rebuild path.
7. **Phase 7 — Self-healing audit and migration**: add repair workflows that rebuild registry caches from source/topic artifacts, detect broken links/schema drift, and apply explicit migrations through `/atlas-migrate`.

Future SQLite adapter contract:

```md
If SQLite is introduced, create `.config/agents/skills/atlas-index/scripts/atlas-registry.py` as the sole database interface. Copy the local Python CLI style used by `.config/agents/skills/mnemopi-cleanup/scripts/mnemopi-status`: stdlib Python, `argparse`, `pathlib`, `sqlite3`, explicit JSON output, explicit exit codes, and no ORM dependency. The Phase 4 adapter supports `init`, `rebuild`, `check`, and read-only `query` commands first. It does not expose direct table CRUD while Markdown remains canonical. If a later migration makes SQLite canonical for registries, add mutation commands only through structured event commands such as `apply-source-routed`, `apply-topic-refreshed`, and `promote-vocab-term`; agents still must not issue ad hoc SQL.
```

If `.config/agents/skills/atlas-index/` does not exist when Phase 4 is reached, create that skill as part of the Phase 4 migration plan. Do not create it during Phase 1 just to reserve the path.

Framework philosophy must appear near the end of `ARCHITECTURE.md`, after operational contracts. Keep it succinct but explicit:

- Lean by default: start with the fewest files that preserve deterministic lookup.
- Robust by provenance: every research answer traces back to source-summary artifacts.
- Flexible by schema: version artifacts and migrate intentionally instead of relying on implicit conventions.
- Deterministic by contract: when evidence is missing, report the gap rather than filling it with model priors.
- Expand by threshold: create optional split files only when topic size or complexity makes them necessary.
- Separate framework from skills: future skills can change, but they must honor `ARCHITECTURE.md` unless explicitly revising the framework.

Atlas is deterministic scaffolding around nondeterministic agents. Keep the interface small, state durable, reducers explicit, and model work bounded. Prefer a readable Markdown state transition over a hidden optimization until the optimization demonstrably improves lookup, consistency, or scale without weakening provenance.

### T4. Rewrite the digest skill entrypoint and routing rules

Edit `.config/agents/skills/digest/SKILL.md`; preserve `name: digest`. Update the description so this current skill can operate against the Atlas framework while future framework-specific skills remain separate:

```yaml
description: >
  Turn URLs, source-discovery runs, and research requests into reusable Atlas
  Obsidian artifacts. Use when the user provides links for source summaries,
  asks to acquire sources, researches or refreshes a topic, or wants Atlas
  indexes and rollups maintained for deterministic agent lookup.
```

Opening defaults:

```md
Use `vault://atlas/ARCHITECTURE.md` as the source of truth for the research framework.

Default source artifact root: `vault://atlas/summaries/sources/artifacts/<YYYY>/<YYYY-MM>/`.
Default source manifest: `vault://atlas/summaries/sources/MANIFEST.md`.
Default research topic root: `vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/`.

Suggested manual invocations:

- `/digest <url...>` — summarize explicit sources.
- `/digest acquire <watchlist-or-query>` — discover sources and write source artifacts only.
- `/digest research --vault-only <topic>` — synthesize or refresh a topic from existing source artifacts only.
- `/digest research --acquire <topic>` — acquire source artifacts first, then synthesize from those artifacts.
- `/digest rollup` — refresh Atlas indexes and rollups from existing artifacts.
```

Mode rules:

1. **Source mode** — explicit URLs only. Canonicalize each URL, lookup `source_id` in `MANIFEST.md`, skip duplicates unless refresh is due, then write one source artifact per new/changed canonical URL.
2. **Acquisition mode** — scheduled or manual source discovery. Search feeds, inboxes, or query watchlists; dedupe through `MANIFEST.md`; create source artifacts; write a run log. Do not update topic answers.
3. **Research mode, vault-only default** — synthesize durable research questions using existing source artifacts and topic files. If coverage is insufficient, record the gap; do not invent an answer from raw web results.
4. **Research mode, acquisition-first escape hatch** — when the caller explicitly allows acquisition, perform source acquisition first, materialize source artifacts, then synthesize from those artifacts.
5. **Rollup mode** — update `summaries/INDEX.md`, `summaries/sources/INDEX.md`, `summaries/research/INDEX.md`, `summaries/domains/<domain>.md`, and subdomain `INDEX.md` files from existing artifacts.

Routing examples:

- “What's the best way to create sourdough?” -> `research/cooking/bread/topics/sourdough-method/INDEX.md`.
- “Best cost-effective yet performant cloud infrastructure to host Flue AI for programmatic agent harness services” -> `research/infrastructure/agent-service-hosting/topics/flue-agent-harness-hosting/INDEX.md`.
- “Best framework to implement Flue as a personal intelligent assistant as a chatbot in Telegram/Line/etc.” -> `research/agentic-development/personal-assistants/topics/flue-chatbot-assistant-framework/INDEX.md`.
- “Research frontend motion and subliminal micro-detail design skills for agents” -> `research/coding/frontend-design/topics/frontend-motion-and-microinteraction-skills/INDEX.md` with secondary tags for `agentic-development` and `design`.

### T5. Revise the source summary template and dedupe policy

Edit `.config/agents/skills/digest/assets/source-summary-template.md`. Preserve useful existing fields and add or normalize:

```yaml
schema_version: 1
note_type: source-summary
managed_by: atlas
source_id: ""
source_seq: 0
canonical_url: ""
source_kind: "article|paper|repo|thread|video|docs|other"
title: ""
primary_domain: ""
subdomains: []
secondary_domains: []
canonical_tags: []
candidate_terms: []
routing_status: "unrouted|routed|no-topic-match|routing-blocked"
routed_at: "YYYY-MM-DD"
first_seen: "YYYY-MM-DD"
last_checked: "YYYY-MM-DD"
last_summarized: "YYYY-MM-DD"
refresh_after: "YYYY-MM-DD"
content_hash: ""
acquired_by: "manual|acquisition-run|research-acquire"
acquisition_run: ""
coverage: "complete|partial|failed"
confidence: "high|medium|low"
evidence_strength: "high|medium|low"
practicality: "high|medium|low|n/a"
stability: "stable|moving|speculative"
reuse_value: "high|medium|low"
recommended_posture: "adopt|trial|watch|reference-only|ignore"
```

Deduplication rules:

1. Canonicalize URL before fetch/summarize.
2. Compute `source_id` from canonical URL, e.g. `sha256(canonical_url)` shortened for filenames.
3. Lookup `source_id` and canonical URL in `summaries/sources/MANIFEST.md`.
4. If present and not due for refresh, skip summarization.
5. If present and refresh is due, fetch and compare `content_hash`.
6. If content is unchanged, update `last_checked` only.
7. If content materially changed, update the existing source artifact or create a revision only when historical snapshots are needed.
8. If absent, create a new source artifact and append one manifest row.


Source-routing invariants:

- `source_seq` is a monotonically increasing integer assigned in `summaries/sources/MANIFEST.md`; it is the cheap ordering key for routing and refresh.
- `canonical_tags` may contain only IDs already present in `VOCAB.md`.
- `candidate_terms` may contain source-specific phrases that seem useful but are not canonical and must not be used as routing keys.
- Daily acquisition must not create canonical tags, aliases, domains, subdomains, or topic IDs.
- A source artifact write/update must be followed by the route-source workflow unless the source is a duplicate skip with unchanged `content_hash`.

Route-source reducer workflow:

1. Read `vault://atlas/ARCHITECTURE.md`, `summaries/registry/VOCAB.md`, `summaries/registry/TOPICS.md`, `summaries/registry/RELATIONS.md`, `summaries/sources/MANIFEST.md`, and the new/updated source artifact.
2. Normalize the source artifact metadata against `VOCAB.md`; keep only canonical IDs in `canonical_tags`; move noncanonical useful phrases to `candidate_terms`.
3. Build candidate topics from `TOPICS.md` using exact domain/subdomain matches, canonical tag overlap, alias/include-term matches in the source title/TL;DR/key points, and absence of topic `Exclude terms`.
4. If no candidates exist, set the source artifact `routing_status` to `no-topic-match`, update manifest `Route status` to `no-topic-match`, record the count/source IDs in the acquisition run log when one exists, and stop. Do not write `RELATIONS.md` and do not dirty any topic.
5. For each candidate topic, run a bounded verifier using only the source summary plus the candidate topic row/path/scope. The verifier must output structured rows with `include: true|false`, `relation`, `impact`, `confidence`, and `reason`.
6. For each verifier row where `include: true`, create or update one relation edge in `RELATIONS.md`. `Edge ID` is `edge--<source_id>--<topic_id>--<source_content_hash_8>` with `/`, spaces, and dots in `topic_id` replaced by `-`.
7. After relation rows are merged, recompute every affected topic's dirty fields in `TOPICS.md` from `RELATIONS.md`; never increment dirty counts blindly.
8. Set the source artifact `routing_status` and manifest `Route status` to `routed` if at least one pending relation edge was written; otherwise set both to `no-topic-match`.

If `VOCAB.md` is missing a needed canonical term, do not create it from acquisition. Store the term in `candidate_terms`, set `routing_status: routing-blocked` only when routing cannot proceed without the missing term, and report the exact missing term in the acquisition or route run output.

Single manifest policy:

- Keep one `summaries/sources/MANIFEST.md` by default. Thousands of rows are acceptable for the expected scale and simpler for agents.
- If the manifest exceeds roughly 10,000 rows or lookup becomes slow/noisy, shard by year under `summaries/sources/manifests/<YYYY>.md` and keep `MANIFEST.md` as a compact routing index.

Keep meanings narrow:

- `coverage` = fetch/read completeness.
- `confidence` = summary fidelity.
- `evidence_strength` = source quality, specificity, corroboration, and concrete proof.
- `practicality` = whether a future human/agent can use the approach.
- `stability` = expected durability.
- `reuse_value` = likelihood future agents should reopen this artifact.
- `recommended_posture` = best next stance.

Insert a rendered `## Assessment` table with the same five assessment signals and require it to stay in sync with frontmatter.

### T6. Create the research library template asset

Create `.config/agents/skills/digest/assets/research-library-templates.md` as one durable asset. It must contain these top-level headings:

```md
# Research Library Templates

## SUBDOMAIN-INDEX.md
## TOPIC-INDEX.md
## passes/YYYY-MM-DD--<pass-slug>.md
## optional/SOURCES.md
## optional/DECISIONS.md
## optional/HISTORY.md
## sources/runs/YYYY-MM-DD--<run-slug>.md
```

`SUBDOMAIN-INDEX.md` contract:

- frontmatter: `schema_version`, `note_type: subdomain-index`, `managed_by: atlas`, `domain`, `subdomain`, `last_updated`, `tags`;
- sections: `# <Subdomain>`, `## Routing scope`, `## Topic map`, `## Default lookup order`, `## Coverage map`, `## Stale or weak areas`, `## Acquisition watchlist`;
- `## Topic map` table: `Topic | Default answer | Coverage | Freshness | Last updated | Link`;
- keep this file concise; it routes agents to topic folders and must not become the research body.

`TOPIC-INDEX.md` contract:

- stored at `research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md`;
- frontmatter: `schema_version`, `note_type: research-topic`, `managed_by: atlas`, `topic`, `domain`, `subdomain`, `aliases`, `status`, `coverage_state: sufficient|partial|insufficient|stale`, `confidence: high|medium|low`, `last_researched`, `freshness_window`, `tags`;
- sections in exact order:
  - `# <Topic>`
  - `## Agent answer contract`
  - `## Scope and routing`
  - `## Current answer`
  - `## Decision tree`
  - `## Recommendation matrix`
  - `## Edge cases`
  - `## Caveats / failure modes`
  - `## Evidence map`
  - `## Gaps and acquisition needs`
  - `## Recent changes`
  - `## Read next`
- `## Current answer` is 5-8 bullets max and must be directly usable by an answering agent.
- `## Evidence map` links to source artifacts first. Raw external URLs may appear only in a clearly marked not-yet-digested subsection.

`passes/YYYY-MM-DD--<pass-slug>.md` contract:

- frontmatter: `schema_version`, `note_type: research-pass`, `managed_by: atlas`, `topic`, `domain`, `subdomain`, `requested`, `completed`, `mode: vault-only|acquisition-first`, `coverage_state`, `confidence`, `tags`;
- sections: `# <Pass title>`, `## Request`, `## Mode`, `## Coverage gate`, `## Existing artifacts consulted`, `## New source artifacts created`, `## Findings`, `## Changes applied to topic INDEX.md`, `## Gaps left open`, `## Next acquisition needs`;
- pass files are immutable provenance except typo/link fixes.

Optional split files:

- `SOURCES.md` — create when the topic `INDEX.md` evidence map exceeds about 25-40 rows or makes the topic index hard to scan. Keep a short source summary in `INDEX.md` and move the full evidence table here.
- `DECISIONS.md` — create when the topic needs more than three distinct decision matrices, personas, environments, or recommendation branches.
- `HISTORY.md` — create when `## Recent changes` exceeds about 10 entries. Keep the latest 3 entries in `INDEX.md` and move older entries here.

Split-file rules:

- Do not create optional split files for new/small topics.
- When a split file is created, add it to the topic `INDEX.md` under `## Read next`.
- Future agents should prefer reading topic `INDEX.md` first, then optional split files only when the relevant section points to them.
- Optional split files use the same frontmatter base: `schema_version`, `note_type`, `managed_by: atlas`, `topic`, `domain`, `subdomain`, `last_updated`.

`sources/runs/YYYY-MM-DD--<run-slug>.md` contract:

- frontmatter: `schema_version`, `note_type: source-acquisition-run`, `managed_by: atlas`, `started`, `completed`, `trigger: manual|cron|research-acquire`, `query_or_watchlist`, `created_sources`, `skipped_duplicates`, `coverage_notes`;
- sections: `# Source acquisition run`, `## Trigger`, `## Queries / feeds`, `## Created source artifacts`, `## Skipped duplicates`, `## Rejected sources`, `## Follow-up acquisition gaps`;
- run logs are provenance for scheduled jobs and must not contain topic synthesis.

### T7. Create starter vault files

Create or merge these files without overwriting user content:

1. `vault://atlas/summaries/INDEX.md`
2. `vault://atlas/summaries/sources/MANIFEST.md`
3. `vault://atlas/summaries/sources/INDEX.md`
4. `vault://atlas/summaries/research/INDEX.md`
5. `vault://atlas/summaries/registry/VOCAB.md`
6. `vault://atlas/summaries/registry/TOPICS.md`
7. `vault://atlas/summaries/registry/RELATIONS.md`

`summaries/registry/VOCAB.md` starts with this content:

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

`summaries/registry/TOPICS.md` starts with this content:

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

`summaries/registry/RELATIONS.md` starts with this content:

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

If registry files already exist in `vault://atlas/summaries/registry/`, merge rows and preserve user content. Do not overwrite existing rows unless the row key is identical and the planned schema requires adding missing columns.

`summaries/INDEX.md` must define artifact classes:

- `source-summary` — evidence snapshot for one URL/repo/paper/thread/video/doc.
- `source-manifest` — canonical URL/source-id registry used for dedupe.
- `source-acquisition-run` — provenance log for a manual or scheduled discovery run.
- `subdomain-index` — agent router and coverage map for one domain/subdomain.
- `research-topic` — current deterministic answer contract for one durable topic.
- `research-pass` — dated, non-canonical investigation record.
- `atlas-vocab` — canonical vocabulary and alias registry for domains, subdomains, tags, source kinds, and aliases.
- `atlas-topic-registry` — topic lookup and freshness cache.
- `atlas-relations` — source-topic edge ledger and pending/applied relation source of truth.

`summaries/sources/MANIFEST.md` starts with this table:

```md
# Source Manifest

Canonical URL registry for Atlas source dedupe.

| Source seq | Source ID | Canonical URL | Artifact | First seen | Last checked | Last summarized | Content hash | Refresh after | Route status | Status |
|---:|---|---|---|---|---|---|---|---|---|---|
```

`summaries/sources/INDEX.md` must state:

- source summaries live under `artifacts/<YYYY>/<YYYY-MM>/`;
- acquisition run logs live under `runs/<YYYY>/<YYYY-MM>/`;
- dedupe is driven by `MANIFEST.md`;
- scheduled acquisition should use feeds, inboxes, or watchlists, not unconstrained web scraping;
- source acquisition does not directly mutate research topics.

`summaries/research/INDEX.md` must state:

- research subdomains live under `<domain>/<subdomain>/`;
- each subdomain has `INDEX.md`;
- durable topics live under `topics/<topic-slug>/INDEX.md`;
- topic indexes are deterministic answer contracts backed by source artifacts;
- vault-only synthesis is default, and acquisition-first must materialize source artifacts before synthesis;
- optional split files are created only when the split thresholds in `ARCHITECTURE.md` are met.

Do not pre-create `domains/<domain>.md`, subdomain directories, or topic folders until the first real source/topic requires them.

Preserve `vault://atlas/todos/` exactly as-is. Do not move legacy todos into `summaries/` and do not delete the folder even if it appears unrelated to the new Atlas architecture.

### T8. Verify changed behavior and lifecycle

Run the plan-content checks and behavior checks in `## Verification / Done criteria` using `read`, `grep`, slash commands when available, or equivalent explicit agent prompts when a slash command does not exist yet.

Run smoke tests in this order:

1. source mode with `https://github.com/karpathy/autoresearch`, then route-source registry checks;
2. repeat source mode with the same URL to prove manifest dedupe skips duplicate summarization and duplicate relation edges;
3. vault-only research mode for `programmatic agent engineering`;
4. acquisition-first research mode for `best way to create sourdough`;
5. dirty quick-answer halt on a topic with pending relation edges;
6. delta refresh on a dirty topic, then answer only after `TOPICS.md` returns to `current`.

The smoke tests fail if:

- duplicate source artifacts are created for the same canonical URL without a refresh reason;
- duplicate relation edges are created for an unchanged duplicate source;
- source artifacts are stored under domain/subdomain folders;
- source artifact or manifest `Route status` is missing or wrong after route-source;
- registry dirty counts in `TOPICS.md` disagree with pending rows in `RELATIONS.md`;
- quick answer uses a dirty, refreshing, or blocked topic `INDEX.md` instead of halting;
- research synthesis cites raw web results without source artifacts;
- topic paths skip the subdomain layer;
- a new small topic creates optional split files prematurely;
- indexes, registry files, or the manifest are not updated.

When implementation is complete, update this plan file in place: set `Status: DONE`, mark each task complete with `completed <timestamp>`, append `## Completion Summary`, create `.agents/plans/archive/` if missing, and move the finished plan with:

```bash
mv .agents/plans/2026-06-30-1339_research-framework-vault.md .agents/plans/archive/
```

## Critical files & anchors

- `.config/agents/rules/plan.md` — filename, metadata, stable task codes, verification, completion summary, archive move.
- `.config/agents/rules/plan-impl-spec.md` — implementation-plan completeness and handoff expectations.
- `.config/agents/skills/skill-craft/SKILL.md` — preserve skill identity and prefer the smallest durable asset set.
- `.config/agents/skills/digest/SKILL.md` — existing entrypoint to rewrite for Atlas.
- `.config/agents/skills/digest/assets/source-summary-template.md` — existing source template to extend.
- `vault://atlas/summaries/registry/VOCAB.md` — canonical vocabulary and alias registry.
- `vault://atlas/summaries/registry/TOPICS.md` — topic registry and freshness cache.
- `vault://atlas/summaries/registry/RELATIONS.md` — source-topic edge ledger.
- `.config/agents/harnesses/omp/config.yml` — currently has no Atlas-specific extension; explicit slash-command workflows come first.
- `.config/agents/skills/mnemopi-cleanup/scripts/mnemopi-status` — stdlib Python SQLite CLI style to copy only for the optional Phase 4 adapter.
- `.config/agents/skills/atlas-index/scripts/atlas-registry.py` — future Phase 4-only SQLite registry adapter path; do not create in Phase 1.

## Assumptions & contingencies

- The user has already renamed the vault/root to `atlas`; implementation should verify `vault://atlas/` resolves and should not create or use `vault://digest/`.
- `vault://atlas/todos/` is legacy state. Preserve it unchanged unless the user separately asks to migrate or remove it.
- Keep the user-facing skill name `digest` for this plan unless the user explicitly asks to rename it. Future Atlas-specific skills will be created separately.
- `ARCHITECTURE.md` is the contract future agents and skills must read before modifying or using the framework.
- The framework should optimize for deterministic future lookup, not maximum same-session freshness.
- Vault-only synthesis is the default because it preserves provenance and repeatability. Acquisition-first is the explicit escape hatch for stale or missing evidence.
- If source coverage is insufficient, the correct output is a coverage gap or acquisition request, not a confident answer.
- A single manifest is acceptable at expected scale. Shard only after lookup performance or file size becomes a real problem.
- If the vault grows too large, split by workflow skill or manifest shard; do not change source identity, topic identity, or artifact roles without an `ARCHITECTURE.md` schema migration note.
- Atlas Phase 1 canonical state is Markdown in the Obsidian vault: source artifacts, acquisition run logs, topic `INDEX.md` files, research pass files, `summaries/sources/MANIFEST.md`, and `summaries/registry/*.md` tables. Do not build Atlas around SQLite in Phase 1, and do not store source summaries, research passes, topic overviews, or registry rows only in SQLite.
- SQLite is a later optimization, not the initial architecture. If registry Markdown files become operationally painful after persisted refresh workflows are stable, add SQLite as a derived registry/index cache only, rebuildable from Markdown artifacts and guarded by a separate explicit schema-migration plan.
- Do not add SQLite files, SQLite scripts, package dependencies, or database migrations to Phase 1.
- Do not add `UNCLAIMED-SOURCES.md`; unmatched sources belong in acquisition run logs and source route status, not a global queue.
- If registry files already exist, merge rows and preserve user content; overwrite only identical row keys when adding planned schema columns.
- Slash commands own Atlas workflows; hooks/extensions may only enforce cheap guardrails and must not run LLM synthesis.
- `digest` remains only as a compatibility adapter until `/atlas-source`, `/atlas-acquire`, `/atlas-research`, `/atlas-refresh`, and `/atlas-answer` exist and pass smoke checks.
- Optional SQLite adapter work is Phase 4 only. Do not create `.config/agents/skills/atlas-index/scripts/atlas-registry.py` or `.config/agents/skills/atlas-index/` during Phase 1 just to reserve the path.

## Completion Summary

Completed 2026-07-02-2019.

- Verified `vault://atlas/` resolves and `vault://atlas/todos/TODOs.md` remains preserved.
- Verified the precedence section still requires `.agents/plans/2026-07-01-2313_atlas-routing-refresh.md` before this implementation plan.
- Verified `vault://atlas/ARCHITECTURE.md` contains the required 12-Factor basis, registry layer, deterministic routing, dirty refresh, SQLite policy, future skill contract, and framework philosophy sections.
- Verified `.config/agents/skills/digest/SKILL.md` contains no `vault://digest` reference and no Phase 1 SQLite implementation instruction.
- Verified registry headers in `VOCAB.md`, `TOPICS.md`, and `RELATIONS.md`.
- Ran explicit equivalent harness prompts/workflows because Atlas-specific slash commands are not created in Phase 1.
- Source digestion smoke: materialized `karpathy/autoresearch` as source seq 1 under `vault://atlas/summaries/sources/artifacts/2026/2026-07/`, routed it to `programmatic-agent-engineering`, marked the topic dirty, and verified duplicate digestion skips duplicate artifact/relation creation.
- No-match routing smoke: materialized `https://example.com/` as source seq 2 with `Route status=no-topic-match`, no relation edge, and no `UNCLAIMED-SOURCES.md`.
- Vault-only research smoke: created `agentic-development/agent-research/topics/programmatic-agent-engineering/INDEX.md` plus a vault-only pass; no new source rows were added.
- Acquisition-first research smoke: acquired/materialized The Clever Carrot sourdough guide as source seq 3, recorded an acquisition run log, and created `cooking/bread/topics/sourdough-method/INDEX.md`.
- Dirty quick-answer smoke: routed The Perfect Loaf as source seq 4, set `sourdough-method` dirty with pending edge `edge--baeb4fb5078b--sourdough-method--fd717920`, and verified the quick-answer gate halted with topic path, dirty count, and pending edge ID rather than answering from stale topic content.
- Delta refresh smoke: created `2026-07-02--delta-refresh-perfect-loaf.md`, patched managed sections of `sourdough-method/INDEX.md`, marked the pending edge applied with `Applied in pass`, recomputed `TOPICS.md` to `current` with dirty count 0/source watermark 4, and verified answer eligibility afterward.
- Registry consistency script passed: four manifest rows, three relation rows, two current topics, no pending edges, all canonical tags in `VOCAB.md`, and no Phase 1 SQLite database files.
