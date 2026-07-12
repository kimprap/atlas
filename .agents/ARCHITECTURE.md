---
schema_version: 1
note_type: atlas-architecture
managed_by: atlas
last_updated: 2026-07-12
---

# Atlas Architecture

Atlas turns source evidence into durable Markdown artifacts, routes them through a registry, and refreshes topic answers only through explicit, auditable state transitions. Vault content is Markdown-first and editor-friendly (including Obsidian). Logical access is always `vault://atlas/…` via the active connector/profile — portable across local agents, CI, and serverless runtimes.

Read this file before changing framework behavior. Skill checklists and contracts must honor it unless an explicit migration revises the framework.

## Product vs instance

This file is the framework contract at `vault://atlas/ARCHITECTURE.md` on every bound instance. **Author** only in the product package at `.agents/ARCHITECTURE.md`. Instance copies are **snapshots** from `scripts/atlas-instance.py`, not a second edit surface.

| Class | Examples | Rule |
|---|---|---|
| **product_owned** | `.agents/ARCHITECTURE.md` → instance `ARCHITECTURE.md` | Edit in the product package; `sync-framework` overwrites the instance snapshot. |
| **seed_once** | Empty registries, summary indexes, legacy `todos/` stub | Copied on instance create; later content is instance state. |
| **instance_owned** | Source artifacts, runs, topics, real todos, editor config | Never re-seeded by provision; living schema changes use `/atlas-migrate`. |

Empty-instance templates live under app `scaffold/` (`scaffold/MANIFEST.json`, `scaffold/README.md`). Provision is **instance bootstrap**, not app deploy — do not ship instance research data in deploy artifacts.

## Framework invariants

- `vault://atlas/` is the only vault root (no `vault://digest/` or second root).
- `vault://atlas/todos/` is legacy: preserve unchanged; do not fold into `summaries/`.
- Source artifacts are evidence snapshots, stored by acquisition/check time (not by domain tree).
- Research topics are deterministic answer contracts backed by source artifacts.
- Research is vault-only unless the caller explicitly allows acquisition-first (then materialize sources before synthesis).
- Indexes route agents; they must not duplicate full research bodies.
- Topic folders start lean; optional splits only past documented thresholds.
- Every managed artifact has `schema_version`, `note_type`, and `managed_by: atlas`.
- Phase 1: Markdown registries are canonical; SQLite is not in scope.
- Skills and reducers rely on this file and artifact contracts — do not invent parallel conventions.

## Workflow basis

Agents propose structured decisions; deterministic checklists apply them; vault artifacts record state.

- **Structured outputs, deterministic application** — route/relation/delta proposals go through checklists and schema checks.
- **Own the context window** — prefer registry rows and bounded snippets over loading the whole vault.
- **Unify execution and business state** — artifacts, manifests, relations, topics, passes, and run logs are the workflow state (no parallel ephemeral queue of the same facts).
- **Own control flow** — slash commands (and later scheduled workflows) decide when to route, refresh, halt, or answer. Hooks may only enforce cheap guardrails.
- **Small focused workflows** — acquire, route, research, refresh, answer, audit, index, migrate have narrow read/write sets.
- **Reducer model** — read state + one event → bounded write + enough provenance to audit later.

Phase 1 history is the artifacts themselves (runs, passes, sources, relations). Add a separate event log only if audits cannot be reconstructed from those.

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
5. Update seed-once templates under app `scaffold/`, skill instructions, registry headers, and smoke checks in the same migration when the contract changes. After changing `.agents/ARCHITECTURE.md`, run `python3 scripts/atlas-instance.py sync-framework` so bound instances receive the product_owned snapshot.
6. Do not mix schema migration with unrelated topic synthesis or source acquisition.

Registry Markdown files are canonical until an explicit schema migration says otherwise.

## SQLite policy

- Phase 1: Markdown is canonical; do not introduce SQLite.
- Source artifacts, topic overviews, research passes, and run logs stay Markdown even if a registry cache appears later.
- A later SQLite cache (if ever) is **derived** at `vault://atlas/.atlas/registry.sqlite`, rebuilt from Markdown, accessed only through a dedicated adapter CLI — never ad hoc SQL or hand edits.
- Promoting SQLite to canonical storage requires an explicit migration with Markdown export views and rollback.

## Slash commands

Commands are the control plane for Atlas work. Thin stubs live in the product package under `.agents/commands/` and load the matching `skill://atlas-*` checklist. Prefer a slash command over freestyle vault mutation. Shared reducer rules live in `atlas-core`; this file owns write-set and freshness invariants.

### How to use

1. Open an agent session with the **product package** as project root so commands and skills resolve.
2. Bind a vault profile/connector so `vault://atlas/…` reaches the intended instance.
3. Invoke `/atlas-<name> …` with the intent below. Pass scope args (URL, topic id, flags) as the skill documents.
4. For product/framework edits (not vault content), use ordinary repo workflows — not these commands.

Do not put LLM synthesis in hooks. Hooks (later) may only enforce cheap guardrails; full workflows stay on slash commands.

### When to use (by intent)

Each table: **Use when** / **Skip when** / **Writes** (summary). Full checklists live in the skill.

#### Bring evidence in

| Command | Use when | Skip when | Writes |
|---|---|---|---|
| `/atlas-source` | You have explicit URLs, files, or repos to ingest | Open-ended discovery, topic synthesis | Source artifacts, `MANIFEST.md`, route fields |
| `/atlas-acquire` | Bounded discovery (feed, inbox, watchlist, scoped query) | Unconstrained crawl; single known URL (use source) | Artifacts, manifest, run log, edges when routing succeeds |

#### Connect evidence to topics

| Command | Use when | Skip when | Writes |
|---|---|---|---|
| `/atlas-route` | Re-route one source or a bounded range; fix route status | Creating topics or rewriting answers | Route status, `RELATIONS.md`, dirty cache on `TOPICS.md` |
| `/atlas-index` | Promote vocab/topics, repair registry consistency (explicit) | Routine acquire/research; silent ad hoc tags | Registry/index files when promotion/repair is explicit |

#### Produce or refresh answers

| Command | Use when | Skip when | Writes |
|---|---|---|---|
| `/atlas-research` | Create or intentionally rebuild a durable topic from vault sources | Applying pending edges only (use refresh); ad hoc web answer | Topic `INDEX.md`, pass, topic registry row |
| `/atlas-refresh` | Topic is dirty/blocked and pending edges should be applied | Answering while dirty without persisting a pass | Pass, managed topic sections, `RELATIONS.md`, `TOPICS.md` |
| `/atlas-answer` | Need the current answer; registry freshness is `current` | Dirty/refreshing/blocked (halt and report; refresh first in Phase 1) | None |

`/atlas-research` defaults vault-only. Acquisition-first requires an explicit allow flag, then materializes sources before synthesis.

#### Maintain health and schema

| Command | Use when | Skip when | Writes |
|---|---|---|---|
| `/atlas-audit` | Periodic or pre/post-change health report | You already know the repair and want to mutate | None by default |
| `/atlas-migrate` | Explicit schema/version migration with scope and rollback | Normal research, acquire, or refresh | Versioned migration edits only |

#### Compatibility

| Command | Use when | Skip when | Writes |
|---|---|---|---|
| `/digest` | Legacy invocation that must forward to `/atlas-*` | New work (use the matching `/atlas-*` directly) | Via forwarded entrypoint |

### Typical flows

| Intent | Flow |
|---|---|
| Known URL → maybe dirty topics | `/atlas-source` (routes after change) → `/atlas-refresh` if dirty → `/atlas-answer` |
| Watchlist batch | `/atlas-acquire` → audit dirty set → `/atlas-refresh` per topic or batch policy |
| New durable topic | Ensure sources exist → `/atlas-research` (vault-only) → later acquire/route as needed |
| “What do we believe?” | `/atlas-answer`; if halted dirty → `/atlas-refresh` then answer |
| Registry smells wrong | `/atlas-audit` → `/atlas-index` or `/atlas-migrate` as recommended |

## Phases (deferred automation)

Do not jump phases without the exit criteria of the prior one.

1. **Markdown registry + safe answer** — route-source, dirty marking, `/atlas-answer` halts when not `current`. No SQLite.
2. **Persisted refresh before answer** — stable `/atlas-refresh`; optional answer path may delegate refresh after pass commits.
3. **Refresh scheduling** — separate refresh job; acquisition stays cheap and does not refresh topics. Honor a context budget.
4. **Optional SQLite registry cache** — only if Markdown lookup/consistency is observably painful; derived cache only.
5. **Priority routing** — order work by impact/relation/refresh model after refresh quality is stable.
6. **Rollups / retrieval** — only if volume forces it; explicit adapter + rebuild plan.
7. **Self-healing repair** — rebuild caches, drift detection, migrate through `/atlas-migrate`.

## Philosophy

Lean files, provenance over guesses, intentional schema migration, report gaps instead of inventing answers, expand by threshold, keep skills replaceable under this contract. Prefer a readable Markdown state transition over a hidden optimization until it clearly improves lookup, consistency, or scale without weakening provenance.
