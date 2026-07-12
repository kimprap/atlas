---
schema_version: 1
note_type: atlas-architecture
managed_by: atlas
last_updated: 2026-07-09
---

# Atlas Architecture

Atlas is an Obsidian-backed research framework for agent use. It turns source evidence into durable Markdown artifacts, routes those artifacts through a registry, and refreshes topic answers only through explicit, auditable state transitions.

Future agents that use, audit, or improve Atlas must read this file before changing framework behavior.

## Product vs instance

This file is the framework contract at `vault://atlas/ARCHITECTURE.md` on every bound instance. **Authoring** happens only in the Atlas app product repo (app-root `ARCHITECTURE.md`). Instance copies are **snapshots** materialised by the instance provision pipeline (`scripts/atlas-instance.py`), not a second edit surface.

| Class | Examples | Rule |
|---|---|---|
| **product_owned** | `ARCHITECTURE.md` | Edit in the app repo; `sync-framework` overwrites the instance snapshot. Do not hand-edit framework body only inside an instance. |
| **seed_once** | Empty registries, summary indexes, legacy `todos/` stub | Copied when an instance is created; later content is instance state. |
| **instance_owned** | Source artifacts, runs, topics, real todos, `.obsidian/` | Never re-seeded by provision; migrate living schemas with `/atlas-migrate`. |

Empty-instance templates live under the app `scaffold/` tree (see `scaffold/MANIFEST.json` and `scaffold/README.md`). Provision is **instance bootstrap**, not app deploy: Flue/Worker packaging is a separate future concern and must not ship personal instance data.

## Framework invariants

- `vault://atlas/` is the canonical vault root. Do not recreate or use a duplicate `vault://digest/` root.
- `vault://atlas/todos/` is legacy state. Preserve it unchanged; do not remove, rename, clean, migrate, or fold it into `summaries/`.
- Source artifacts are evidence snapshots and are stored by acquisition/check time, not by domain or subdomain.
- Research topics are deterministic answer contracts backed by source artifacts.
- Research synthesis is vault-only unless the caller explicitly chooses acquisition-first mode.
- Acquisition-first mode must materialize source artifacts before any topic synthesis uses the acquired evidence.
- Indexes route agents to the right artifact; they must not duplicate full research bodies.
- Topic folders start lean and split only when the documented thresholds are met.
- Every managed artifact has `schema_version`, `note_type`, and `managed_by: atlas`.
- Registry Markdown files are canonical state in Phase 1.
- Phase 1 canonical state is Markdown in the Obsidian vault; SQLite is not part of Phase 1.
- Future skills should rely on this file and the artifact contracts instead of inventing conventions.

## 12-Factor workflow basis

Atlas follows the 12-Factor Agents style: agents produce structured decisions, deterministic workflow code/checklists apply those decisions, and durable vault artifacts record the resulting state.

- **Structured outputs, deterministic application**: LLMs may propose route decisions, relation classifications, or delta-refresh patches, but Atlas workflows apply them through explicit checklists and schema checks.
- **Own the context window**: registry rows and bounded source/topic snippets are the context interface; agents must not load the whole vault when a registry lookup is sufficient.
- **Unify execution and business state**: source artifacts, manifest rows, relation rows, topic registry rows, pass files, and run logs are the durable workflow state. Do not add a separate ephemeral queue for the same facts.
- **Own control flow**: slash commands and scheduled workflows decide when to route, halt, delegate refresh, persist a pass, or answer. Hooks may only enforce cheap guardrails.
- **Small focused agents**: acquisition, route verification, topic refresh, answer lookup, index repair, and migration are separate workflows with narrow read/write sets.
- **Reducer model**: each workflow reads the current vault state plus one event, computes a bounded change, writes the new state, and records enough provenance to recompute or audit it later.

Do not add a separate `EVENTS.md` just to mimic event sourcing. For Phase 1, acquisition run logs, research pass files, source artifacts, manifest rows, and relation rows are the event/history records. Add a separate event log only in a future migration if audits cannot be reconstructed from those artifacts.

## Directory layout

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

Do not pre-create `summaries/domains/<domain>.md`, subdomain folders, topic folders, optional split files, or `.atlas/` until a real source/topic or migration requires them.

## Artifact roles

| Artifact class | Role | Canonical location |
|---|---|---|
| `atlas-architecture` | Framework source of truth and change contract. | `vault://atlas/ARCHITECTURE.md` |
| `source-summary` | Evidence snapshot for one URL, repo, paper, thread, video, document, or other source. | `summaries/sources/artifacts/<YYYY>/<YYYY-MM>/` |
| `source-manifest` | Canonical URL/source-id registry used for dedupe, ordering, refresh metadata, and route status. | `summaries/sources/MANIFEST.md` |
| `source-acquisition-run` | Provenance log for a manual, scheduled, or research-triggered discovery run. | `summaries/sources/runs/<YYYY>/<YYYY-MM>/` |
| `subdomain-index` | Agent router and coverage map for one domain/subdomain. | `summaries/research/<domain>/<subdomain>/INDEX.md` |
| `research-topic` | Current deterministic answer contract for one durable topic. | `summaries/research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md` |
| `research-pass` | Dated investigation record and delta-application provenance. | `summaries/research/<domain>/<subdomain>/topics/<topic-slug>/passes/` |
| `atlas-vocab` | Canonical vocabulary and alias registry for domains, subdomains, tags, source kinds, and aliases. | `summaries/registry/VOCAB.md` |
| `atlas-topic-registry` | Topic lookup and freshness cache. | `summaries/registry/TOPICS.md` |
| `atlas-relations` | Source-topic edge ledger and pending/applied relation source of truth. | `summaries/registry/RELATIONS.md` |

A source artifact is evidence, not a topic answer. A topic `INDEX.md` is the current answer contract, not the audit trail. A research pass is provenance, not the current answer.

## Registry layer

The Phase 1 registry is Markdown:

```text
vault://atlas/summaries/registry/
├── VOCAB.md
├── TOPICS.md
└── RELATIONS.md
```

- `VOCAB.md` — canonical vocabulary and alias registry. This is the only place where canonical domains, subdomains, tags, source kinds, and reusable aliases are declared.
- `TOPICS.md` — topic registry and freshness cache. This is the quick lookup table for resolving a topic, checking dirty state, finding the topic path, and deciding refresh model without reading topic files.
- `RELATIONS.md` — source-topic edge ledger. This is the source of truth for pending/applied source-to-topic edges.

`VOCAB.md` canonical term header:

```md
| ID | Type | Label | Parent | Allowed aliases | Status | Notes |
|---|---|---|---|---|---|---|
```

`Type` is exactly one of `domain`, `subdomain`, `tag`, or `source-kind`. `Status` is exactly one of `active`, `deprecated`, or `reserved`.

`TOPICS.md` header:

```md
| Topic ID | Topic path | Domain | Subdomain | Canonical title | Aliases | Canonical tags | Include terms | Exclude terms | Freshness state | Dirty count | Pending edge IDs | Newest pending source seq | Last synthesized | Source watermark | Refresh model |
|---|---|---|---|---|---|---|---|---|---|---:|---|---:|---|---:|---|
```

`Freshness state` values:

```text
current | dirty | refreshing | blocked | archived
```

`Refresh model` values:

```text
same-as-topic-creation | smol-ok | manual-only
```

Default `Refresh model` for durable research topics is `same-as-topic-creation`.

`RELATIONS.md` header:

```md
| Edge ID | Source seq | Source ID | Source artifact | Source content hash | Topic ID | Relation | Impact | Confidence | Status | Created | Applied in pass | Notes |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|
```

Relation field values:

- `Relation`: `direct`, `supporting`, or `contradicting`.
- `Impact`: `high`, `medium`, or `low`.
- `Confidence`: `high`, `medium`, or `low`.
- `Status`: `pending`, `applied`, `rejected`, or `superseded`.

Do not store `background`, `duplicate`, or `out-of-scope` rows in `RELATIONS.md`; those outcomes belong only in acquisition or route run summaries.

Do not add `UNCLAIMED-SOURCES.md`. For unmatched sources, acquisition run logs may record counts and source IDs that matched no topic, but Atlas must not maintain a global unclaimed-source queue in Phase 1.

## Mode ownership

| Mode | Reads | Writes |
|---|---|---|
| Source digest | `ARCHITECTURE.md`, source manifest, source template, explicit input source. | One source artifact, source manifest, source index, route status. |
| Source acquisition | `ARCHITECTURE.md`, feeds/inbox/watchlists/search results, source manifest, registry files for routing. | Source artifacts, source manifest, acquisition run log, relation edges when routing succeeds. |
| Route source | `ARCHITECTURE.md`, `VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, source manifest, one source artifact. | Source routing status, `RELATIONS.md`, affected `TOPICS.md` dirty cache fields. |
| Research vault-only | `ARCHITECTURE.md`, source manifest, source artifacts, registry rows, subdomain/topic indexes. | Topic `INDEX.md`, one pass file, subdomain index, topic registry row when intentionally creating or refreshing a topic. |
| Research acquisition-first | Same as source acquisition, then vault-only research. | Source artifacts first, then topic files and registry rows. |
| Refresh dirty topic | `ARCHITECTURE.md`, registry files, target topic `INDEX.md`, pending source artifacts, optional split files referenced by the topic. | One pass file, managed sections in topic `INDEX.md`, `RELATIONS.md` statuses, `TOPICS.md` freshness cache. |
| Answer lookup | `TOPICS.md`, topic `INDEX.md` only when current, source artifacts when provenance is needed. | Nothing. |
| Rollup | Managed artifacts and registry/index files. | Root/domain/source/research/subdomain indexes only. |
| Audit | Managed artifacts and registry/index files. | Nothing by default. |
| Migration | Current schema artifacts plus explicit migration plan. | Versioned migration edits only. |

No mode may silently widen its write set. If a workflow needs a new write target, update this architecture or a schema migration first.

## Source identity and dedupe

Source artifacts use canonical URL identity:

1. Canonicalize URL before fetch/summarize.
2. Compute `source_id` from canonical URL, for example a shortened `sha256(canonical_url)` safe for filenames.
3. Lookup `source_id` and canonical URL in `summaries/sources/MANIFEST.md`.
4. If present and not due for refresh, skip summarization.
5. If present and refresh is due, fetch and compare `content_hash`.
6. If content is unchanged, update `last_checked` only.
7. If content materially changed, update the existing source artifact or create a revision only when historical snapshots are needed.
8. If absent, create a new source artifact and append one manifest row.

`source_seq` is a monotonically increasing integer assigned in `summaries/sources/MANIFEST.md`; it is the cheap ordering key for routing and refresh.

Source summary frontmatter includes:

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

`canonical_tags` may contain only IDs already present in `VOCAB.md`. `candidate_terms` may contain source-specific useful phrases, but they are not canonical and must not be used as routing keys.

## Source refresh policy

`refresh_after` is advisory. A workflow may refresh a source when one of these is true:

- the caller explicitly requests refresh;
- `refresh_after` has passed;
- an acquisition run observes that the canonical URL changed materially;
- a topic refresh requires recency and the source is stale for that topic's freshness window.

If refresh fetches unchanged content, update `last_checked` and keep `content_hash`, `last_summarized`, and route edges unchanged. Do not create duplicate artifacts or duplicate relation edges for unchanged content.

If content materially changes, update the existing source artifact or create a revision only when historical snapshots are needed. After any changed source artifact write, run route-source unless the source is a duplicate skip with unchanged `content_hash`.

Source acquisition should use feeds, inboxes, watchlists, explicit queries, or bounded search. It must not use unconstrained web scraping.

## Topic routing

Topic IDs are stable lowercase path-like or kebab-case identifiers that map to durable topic paths under:

```text
summaries/research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md
```

A topic row in `TOPICS.md` owns the topic path, domain, subdomain, canonical title, aliases, canonical tags, include terms, exclude terms, freshness state, and refresh model.

Acquisition and source digest workflows must not create canonical tags, aliases, domains, subdomains, or topic IDs ad hoc. When a source suggests a useful noncanonical phrase, store it in `candidate_terms`. Promote vocabulary or create topics only through explicit index/research workflows that check for duplicates and conflicts.

Routing never writes topic `INDEX.md`. It only updates source route status, relation edges, and dirty cache fields in `TOPICS.md`.

## Deterministic routing

Route-source is a reducer over one new or updated source artifact:

1. Read `vault://atlas/ARCHITECTURE.md`, `summaries/registry/VOCAB.md`, `summaries/registry/TOPICS.md`, `summaries/registry/RELATIONS.md`, `summaries/sources/MANIFEST.md`, and the new/updated source artifact.
2. Normalize source artifact metadata against `VOCAB.md`; keep only canonical IDs in `canonical_tags`; move noncanonical useful phrases to `candidate_terms`.
3. Build candidate topics from `TOPICS.md` using exact domain/subdomain matches, canonical tag overlap, alias/include-term matches in the source title/TL;DR/key points, and absence of topic `Exclude terms`.
4. If no candidates exist, set the source artifact `routing_status` to `no-topic-match`, update manifest `Route status` to `no-topic-match`, record the count/source IDs in the acquisition run log when one exists, and stop. Do not write `RELATIONS.md` and do not dirty any topic.
5. For each candidate topic, run a bounded verifier using only the source summary plus the candidate topic row/path/scope. The verifier must output structured rows with `include: true|false`, `relation`, `impact`, `confidence`, and `reason`.
6. For each verifier row where `include: true`, create or update one relation edge in `RELATIONS.md`.
7. After relation rows are merged, recompute every affected topic's dirty fields in `TOPICS.md` from `RELATIONS.md`; never increment dirty counts blindly.
8. Set the source artifact `routing_status` and manifest `Route status` to `routed` if at least one pending relation edge was written; otherwise set both to `no-topic-match`.

`Edge ID` is:

```text
edge--<source_id>--<topic_id>--<source_content_hash_8>
```

Replace `/`, spaces, and dots in `topic_id` with `-` when building the edge ID.

If `VOCAB.md` is missing a needed canonical term, do not create it from acquisition. Store the term in `candidate_terms`, set `routing_status: routing-blocked` only when routing cannot proceed without the missing term, and report the exact missing term in the acquisition or route run output.

## Dirty state and refresh

A topic is dirty iff `RELATIONS.md` contains at least one row with `Status=pending` for that `Topic ID`.

`TOPICS.md` is a denormalized quick lookup cache. Marking a topic dirty means recomputing these columns from `RELATIONS.md`:

- `Freshness state`: `dirty` when pending edges exist, `current` when none exist, `refreshing` only while a refresh subagent is actively applying a pass, `blocked` when the last refresh attempt failed and pending edges remain, `archived` when the topic is intentionally inactive.
- `Dirty count`: count of `pending` relation edges for the topic.
- `Pending edge IDs`: comma-separated pending edge IDs, stable sorted by `Source seq` ascending.
- `Newest pending source seq`: max `Source seq` among pending edges; blank or `0` when none exist.
- `Source watermark`: max source seq incorporated by the latest successful refresh pass.

Quick-answer behavior:

- Quick answer must read `TOPICS.md` first after resolving a topic.
- If `Freshness state=current`, quick answer may read the topic `INDEX.md` and answer.
- If `Freshness state=dirty|refreshing|blocked`, quick answer must not answer from topic `INDEX.md` plus unpersisted pending deltas.
- Safe Phase 1 behavior: quick answer halts with topic path, freshness state, dirty count, and pending edge IDs.
- Later Phase 2 behavior: quick answer may delegate `/atlas-refresh --topic <topic-id>` to a refresh subagent using the topic row's `Refresh model`; only after the refresh subagent persists the delta and `TOPICS.md` returns to `current` may quick answer produce the answer.

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

## Topic split policy

New topics start with only:

```text
topics/<topic-slug>/
├── INDEX.md
└── passes/
```

Optional split files are created only when they improve scanability:

- `SOURCES.md` — create when the topic `INDEX.md` evidence map exceeds about 25-40 rows or makes the topic index hard to scan. Keep a short source summary in `INDEX.md` and move the full evidence table here.
- `DECISIONS.md` — create when the topic needs more than three distinct decision matrices, personas, environments, or recommendation branches.
- `HISTORY.md` — create when `## Recent changes` exceeds about 10 entries. Keep the latest 3 entries in `INDEX.md` and move older entries here.

When a split file is created, add it under `## Read next` in the topic `INDEX.md`. Future agents should read topic `INDEX.md` first, then optional split files only when the relevant section points to them.

## Managed sections

Agents should patch managed sections instead of rewriting whole files unless a file is empty or structurally broken.

Managed section convention:

```md
<!-- atlas:managed:start <section-name> -->
...
<!-- atlas:managed:end <section-name> -->
```

Managed sections define the only regions a reducer may patch automatically. Freeform user notes outside managed sections are user-owned and must be preserved.

## Schema migration

Every managed artifact includes `schema_version`, `note_type`, and `managed_by: atlas` in frontmatter. Schema changes must be explicit and versioned.

Migration rules:

1. Read this architecture and the affected artifact contract before editing.
2. Define the old shape, new shape, migration scope, rollback path, and verification checks.
3. Preserve user content and unmanaged sections.
4. Prefer additive migrations that can be applied row-by-row or artifact-by-artifact.
5. Update seed-once templates under app `scaffold/`, skill instructions, registry headers, and smoke checks in the same migration when the contract changes. After changing this architecture file, run `python3 scripts/atlas-instance.py sync-framework` so bound instances receive the product_owned snapshot.
6. Do not mix schema migration with unrelated topic synthesis or source acquisition.

Registry Markdown files are canonical until an explicit schema migration says otherwise.

## SQLite policy

- Phase 1 uses Markdown as canonical state. SQLite is not part of Phase 1.
- Source artifacts, topic overviews, research passes, and acquisition run logs stay as Markdown files even if SQLite is introduced later.
- Registry Markdown files are canonical until an explicit schema migration says otherwise.
- A later SQLite registry cache may be introduced only after Markdown routing, persisted delta refresh, and registry consistency checks are working.
- If introduced, SQLite is a derived cache at `vault://atlas/.atlas/registry.sqlite`, rebuilt from Markdown by an Atlas registry adapter. Do not hand-edit the database and do not let agents issue ad hoc SQL.
- If a future migration promotes SQLite from derived cache to canonical registry storage, that migration must keep Markdown export views for Obsidian browsing and must define rollback back to Markdown.

Future SQLite adapter contract:

```md
If SQLite is introduced, create `.agents/skills/atlas-index/scripts/atlas-registry.py` as the sole database interface. Copy the local Python CLI style used by `.agents/skills/mnemopi-cleanup/scripts/mnemopi-status`: stdlib Python, `argparse`, `pathlib`, `sqlite3`, explicit JSON output, explicit exit codes, and no ORM dependency. The Phase 4 adapter supports `init`, `rebuild`, `check`, and read-only `query` commands first. It does not expose direct table CRUD while Markdown remains canonical. If a later migration makes SQLite canonical for registries, add mutation commands only through structured event commands such as `apply-source-routed`, `apply-topic-refreshed`, and `promote-vocab-term`; agents still must not issue ad hoc SQL.
```

Do not create `.agents/skills/atlas-index/` during Phase 1 just to reserve the path.

## Future skill contract

| Command | Role | Writes |
|---|---|---|
| `/atlas-source` | Ingest explicit URLs/files/repos into source artifacts, manifest rows, and route-source workflow. | Source artifacts, source manifest, registry route fields. |
| `/atlas-acquire` | Bounded acquisition from feeds/watchlists/inbox/search, then source ingestion and route-source workflow. | Source artifacts, source manifest, acquisition run logs, relation edges. |
| `/atlas-route` | Re-run route-source workflow for one source or source range. | Source routing status, `RELATIONS.md`, `TOPICS.md` dirty cache. |
| `/atlas-research` | Create or intentionally refresh durable topic research from vault sources; acquisition only with explicit flag. | Topic `INDEX.md`, pass files, topic registry rows. |
| `/atlas-refresh` | Apply pending relation edges to dirty topics through persisted delta passes. | Pass files, topic `INDEX.md`, `RELATIONS.md`, `TOPICS.md`. |
| `/atlas-answer` | Resolve topic and answer only when registry says topic is current; otherwise halt with deterministic dirty-state output in Phase 1. | None. |
| `/atlas-index` | Maintain and repair `VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, manifest consistency, and broken links. | Registry/index files only when repair or promotion flag is explicit. |
| `/atlas-audit` | Read-only vault health report for dirty topics, schema drift, orphaned relations, and registry inconsistency. | None by default. |
| `/atlas-migrate` | Apply explicit schema migrations. | Versioned migration edits only. |

Keep the legacy `digest` skill temporarily. `digest` is a compatibility adapter for source ingestion during transition and is removed only after `/atlas-source`, `/atlas-acquire`, `/atlas-research`, `/atlas-refresh`, and `/atlas-answer` exist and pass smoke checks.

Hook policy:

- Do not put LLM synthesis in hooks/extensions.
- Use slash commands for full workflow checklists and any LLM work.
- Hooks/extensions may later enforce cheap idempotent guardrails only: route after a source artifact write, reject answer attempts on dirty topics, or surface registry consistency failures.
- If no Atlas-specific extension exists, use explicit slash-command workflows first and leave hook automation to a later phase.

Automation phases:

1. **Phase 1 — Markdown registry and safe freshness**: implement `VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, route-source, dirty marking, and `/atlas-answer` halting on dirty topics. Do not implement SQLite. Move to Phase 2 when route-source creates stable relation edges without vocabulary drift and quick answers never silently use dirty topics.
2. **Phase 2 — Persisted refresh before answer**: implement `/atlas-refresh --topic <topic-id>` and allow a fresh-answer path to delegate a refresh subagent before answering. Move to Phase 3 when persisted delta passes reliably patch only affected managed sections and registry consistency checks pass.
3. **Phase 3 — Dedicated refresh cron**: create a separate refresh cron that processes dirty topics using the same refresh checklist. Source acquisition cron remains cheap and does not refresh topics. The refresh cron stops before the next topic when estimated context would exceed a configurable context budget, initially documented as `max_context_tokens: 200000`.
4. **Phase 4 — Optional SQLite registry cache**: add SQLite only if Markdown registry lookup or consistency checks are observably painful after Phase 3. SQLite is a derived cache at `vault://atlas/.atlas/registry.sqlite`, rebuilt from Markdown, and accessed only through `.agents/skills/atlas-index/scripts/atlas-registry.py`. Do not store source artifacts, research passes, or topic overviews in SQLite. If no lookup pain exists, skip this phase.
5. **Phase 5 — Priority and impact routing**: use `Impact`, `Relation`, topic `Refresh model`, and archived/manual-only states to order refresh work. Move here only after Phase 3 refresh quality is stable; Phase 4 is optional.
6. **Phase 6 — Hierarchical rollups and optional retrieval adapter**: add subdomain/domain rollups or lexical/vector retrieval only if source volume makes direct topic refresh too large. Retrieval storage may use SQLite FTS or a separate vector adapter only after a migration plan defines the adapter interface and rebuild path.
7. **Phase 7 — Self-healing audit and migration**: add repair workflows that rebuild registry caches from source/topic artifacts, detect broken links/schema drift, and apply explicit migrations through `/atlas-migrate`.

## Framework philosophy

- Lean by default: start with the fewest files that preserve deterministic lookup.
- Robust by provenance: every research answer traces back to source-summary artifacts.
- Flexible by schema: version artifacts and migrate intentionally instead of relying on implicit conventions.
- Deterministic by contract: when evidence is missing, report the gap rather than filling it with model priors.
- Expand by threshold: create optional split files only when topic size or complexity makes them necessary.
- Separate framework from skills: future skills can change, but they must honor `ARCHITECTURE.md` unless explicitly revising the framework.

Atlas is deterministic scaffolding around nondeterministic agents. Keep the interface small, state durable, reducers explicit, and model work bounded. Prefer a readable Markdown state transition over a hidden optimization until the optimization demonstrably improves lookup, consistency, or scale without weakening provenance.
