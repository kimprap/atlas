# Research Library Templates

Reusable Atlas templates for research indexes, topic answer contracts, dated passes, optional split files, and source acquisition run logs. These templates follow `vault://atlas/ARCHITECTURE.md`; update that architecture first when changing schema or artifact roles.

## SUBDOMAIN-INDEX.md

Stored at `vault://atlas/summaries/research/<domain>/<subdomain>/INDEX.md`.

```md
---
schema_version: 1
note_type: subdomain-index
managed_by: atlas
domain: "<domain-id>"
subdomain: "<subdomain-id>"
last_updated: "YYYY-MM-DD"
tags: []
---

# <Subdomain>

## Routing scope

<!-- atlas:managed:start routing-scope -->
- Domain: `<domain-id>`
- Subdomain: `<subdomain-id>`
- Include: <short scope statement>
- Exclude: <near-miss topics routed elsewhere>
<!-- atlas:managed:end routing-scope -->

## Topic map

<!-- atlas:managed:start topic-map -->
| Topic | Default answer | Coverage | Freshness | Last updated | Link |
|---|---|---|---|---|---|
<!-- atlas:managed:end topic-map -->

## Default lookup order

<!-- atlas:managed:start default-lookup-order -->
1. Check `vault://atlas/summaries/registry/TOPICS.md` for topic path and freshness.
2. Read the topic `INDEX.md` when `Freshness state=current`.
3. Read optional split files only when the topic `INDEX.md` points to them.
<!-- atlas:managed:end default-lookup-order -->

## Coverage map

<!-- atlas:managed:start coverage-map -->
- Sufficient: <topics with usable current answers>
- Partial: <topics with known gaps>
- Insufficient: <topics needing acquisition>
<!-- atlas:managed:end coverage-map -->

## Stale or weak areas

<!-- atlas:managed:start stale-or-weak-areas -->
- <topic or gap> — <reason>
<!-- atlas:managed:end stale-or-weak-areas -->

## Acquisition watchlist

<!-- atlas:managed:start acquisition-watchlist -->
- <source class, feed, repo, author, query, or evidence gap>
<!-- atlas:managed:end acquisition-watchlist -->
```

Keep this file concise. It routes agents to topic folders and must not become the research body.

`index.create_topic` updates only the existing subdomain frontmatter `last_updated` and the managed `topic-map`, `coverage-map`, and `stale-or-weak-areas` projections for the requested topic. The topic-map row uses the canonical title, `Research required`, `Insufficient`, `Current`, the explicit `created_on`, and the topic path as its link. The coverage map places the topic only under `Insufficient`; the stale/weak entry states that no evidence-backed answer exists and acquisition/research is required. Existing projection entries retain their order and bytes; the new requested entry is inserted by canonical topic ID order. Routing scope, lookup order, watchlist, unmanaged content, newline convention, and final-newline state remain unchanged.

## TOPIC-INDEX.md

Stored at `vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md`.

```md
---
schema_version: 1
note_type: research-topic
managed_by: atlas
topic: "<topic-id>"
domain: "<domain-id>"
subdomain: "<subdomain-id>"
aliases: []
status: "active|archived|draft"
coverage_state: "sufficient|partial|insufficient|stale"
confidence: "high|medium|low"
last_researched: "YYYY-MM-DD"
freshness_window: "P90D"
tags: []
---

# <Topic>

## Agent answer contract

<!-- atlas:managed:start agent-answer-contract -->
- Present this topic as current only when `TOPICS.md` says `current`.
- If dirty, refreshing, or blocked, managed content may be returned only as explicitly stale/no-write with freshness state, dirty count, and pending edge IDs; never refresh from answer mode.
- Cite source artifacts from `## Evidence map`; raw URLs are not evidence unless also materialized as source artifacts.
<!-- atlas:managed:end agent-answer-contract -->

## Scope and routing

<!-- atlas:managed:start scope-and-routing -->
- Topic ID: `<topic-id>`
- Include: <canonical include terms>
- Exclude: <near misses>
- Related topics: <links or topic ids>
<!-- atlas:managed:end scope-and-routing -->

## Current answer

<!-- atlas:managed:start current-answer -->
- 5-8 bullets max.
- Directly usable by an answering agent.
- Each substantive claim should be backed by `## Evidence map`.
<!-- atlas:managed:end current-answer -->

## Decision tree

<!-- atlas:managed:start decision-tree -->
- If <condition>, choose <recommendation> because <evidence>.
<!-- atlas:managed:end decision-tree -->

## Recommendation matrix

<!-- atlas:managed:start recommendation-matrix -->
| Situation | Recommendation | Evidence | Confidence |
|---|---|---|---|
<!-- atlas:managed:end recommendation-matrix -->

## Edge cases

<!-- atlas:managed:start edge-cases -->
- <edge case> — <handling>
<!-- atlas:managed:end edge-cases -->

## Caveats / failure modes

<!-- atlas:managed:start caveats-failure-modes -->
- <caveat or failure mode> — <impact>
<!-- atlas:managed:end caveats-failure-modes -->

## Evidence map

<!-- atlas:managed:start evidence-map -->
| Claim / use | Source artifact | Evidence strength | Notes |
|---|---|---|---|
<!-- atlas:managed:end evidence-map -->

### Not-yet-digested external leads

Raw external URLs may appear here only as leads that still need source artifacts. Do not cite this subsection as evidence in an answer.

## Gaps and acquisition needs

<!-- atlas:managed:start gaps-and-acquisition-needs -->
- <gap> — <needed source or acquisition query>
<!-- atlas:managed:end gaps-and-acquisition-needs -->

## Recent changes

<!-- atlas:managed:start recent-changes -->
- YYYY-MM-DD — <change> — <pass link>
<!-- atlas:managed:end recent-changes -->

## Read next

<!-- atlas:managed:start read-next -->
- <optional split file or related topic>
<!-- atlas:managed:end read-next -->
```

Outside the explicit initial shell below, `## Current answer` is 5-8 bullets max and must be directly usable by an answering agent. `## Evidence map` links to source artifacts first. Raw external URLs may appear only in the clearly marked not-yet-digested subsection.

### Initial create-or-confirm shell

For an absent topic, `index.create_topic` renders this template without its instructional placeholders. Frontmatter is exactly the requested identity/scope with `schema_version: 1`, `note_type: research-topic`, `managed_by: atlas`, `aliases` from the normalized request, `status: active`, `coverage_state: insufficient`, `confidence: low`, `last_researched: <created_on>`, `freshness_window: P90D`, and `tags: []`.

- Keep the three `agent-answer-contract` rules.
- Fill `scope-and-routing` from canonical include terms, exclude terms, and byte-ordered related topic IDs; render `none` for an empty list.
- Render `current-answer` as exactly `- No evidence-backed answer exists; acquisition and research are required.`
- Keep the recommendation and evidence-map table headers/separators but add no data rows.
- Leave `decision-tree`, `edge-cases`, `caveats-failure-modes`, `recent-changes`, and not-yet-digested leads empty.
- Render `gaps-and-acquisition-needs` as exactly `- Evidence-backed answer unavailable — acquire and research relevant sources.`
- Render `read-next` from byte-ordered related topic links, or leave it empty.

Creation adds no pass, evidence row, source artifact, relation edge, optional split file, supported answer, or hidden timestamp. A compatible existing topic is validated against structural identity and its projections but is not rerendered; its answer, coverage, confidence, freshness/cache values, and dates remain byte-for-byte unchanged.

## passes/YYYY-MM-DD--<pass-slug>.md

Stored under `vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/passes/`.

```md
---
schema_version: 1
note_type: research-pass
managed_by: atlas
topic: "<topic-id>"
domain: "<domain-id>"
subdomain: "<subdomain-id>"
requested: "YYYY-MM-DDTHH:MM:SSZ"
completed: "YYYY-MM-DDTHH:MM:SSZ"
mode: "vault-only|acquisition-first"
coverage_state: "sufficient|partial|insufficient|stale"
confidence: "high|medium|low"
tags: []
---

# <Pass title>

## Request

<original request or refresh trigger>

## Mode

<vault-only or acquisition-first; include why>

## Coverage gate

- Existing source artifacts were sufficient: <yes|no>
- New acquisition was allowed: <yes|no>
- Coverage result: `<sufficient|partial|insufficient|stale>`

## Existing artifacts consulted

| Source artifact | Relevance | Notes |
|---|---|---|

## New source artifacts created

| Source artifact | Route status | Notes |
|---|---|---|

## Findings

- <finding with source artifact reference>

## Changes applied to topic INDEX.md

- <managed section patched> — <summary of diff>

## Gaps left open

- <gap> — <why unresolved>

## Next acquisition needs

- <query, feed, repo, author, or source class>
```

Pass files are immutable provenance except typo/link fixes.

## optional/SOURCES.md

Create only when the topic `INDEX.md` evidence map exceeds about 25-40 rows or makes the topic index hard to scan. Keep a short source summary in `INDEX.md` and move the full evidence table here.

```md
---
schema_version: 1
note_type: research-topic-sources
managed_by: atlas
topic: "<topic-id>"
domain: "<domain-id>"
subdomain: "<subdomain-id>"
last_updated: "YYYY-MM-DD"
---

# Sources for <Topic>

## Evidence table

<!-- atlas:managed:start evidence-table -->
| Claim / use | Source artifact | Evidence strength | Last checked | Notes |
|---|---|---|---|---|
<!-- atlas:managed:end evidence-table -->

## Source quality notes

<!-- atlas:managed:start source-quality-notes -->
- <source artifact> — <quality or limitation>
<!-- atlas:managed:end source-quality-notes -->
```

## optional/DECISIONS.md

Create only when the topic needs more than three distinct decision matrices, personas, environments, or recommendation branches.

```md
---
schema_version: 1
note_type: research-topic-decisions
managed_by: atlas
topic: "<topic-id>"
domain: "<domain-id>"
subdomain: "<subdomain-id>"
last_updated: "YYYY-MM-DD"
---

# Decisions for <Topic>

## Decision contexts

<!-- atlas:managed:start decision-contexts -->
| Context | Primary recommendation | Alternatives | Evidence | Confidence |
|---|---|---|---|---|
<!-- atlas:managed:end decision-contexts -->

## Personas / environments

<!-- atlas:managed:start personas-environments -->
| Persona / environment | Decision rule | Notes |
|---|---|---|
<!-- atlas:managed:end personas-environments -->
```

## optional/HISTORY.md

Create only when `## Recent changes` exceeds about 10 entries. Keep the latest 3 entries in `INDEX.md` and move older entries here.

```md
---
schema_version: 1
note_type: research-topic-history
managed_by: atlas
topic: "<topic-id>"
domain: "<domain-id>"
subdomain: "<subdomain-id>"
last_updated: "YYYY-MM-DD"
---

# History for <Topic>

## Change log

<!-- atlas:managed:start change-log -->
| Date | Pass | Change | Notes |
|---|---|---|---|
<!-- atlas:managed:end change-log -->
```

## sources/runs/YYYY-MM-DD--<run-slug>.md

Stored under `vault://atlas/summaries/sources/runs/<YYYY>/<YYYY-MM>/`.

```md
---
schema_version: 1
note_type: source-acquisition-run
managed_by: atlas
started: "YYYY-MM-DDTHH:MM:SSZ"
completed: "YYYY-MM-DDTHH:MM:SSZ"
trigger: "manual|cron|research-acquire"
query_or_watchlist: ""
created_sources: 0
skipped_duplicates: 0
coverage_notes: ""
---

# Source acquisition run

## Trigger

<trigger, request, cron name, or research-acquire topic>

## Queries / feeds

- <query, feed, inbox, watchlist, or source class>

## Created source artifacts

| Source seq | Source ID | Artifact | Route status | Notes |
|---:|---|---|---|---|

## Skipped duplicates

| Source ID | Canonical URL | Existing artifact | Reason |
|---|---|---|---|

## Rejected sources

| URL or source | Reason |
|---|---|

## Follow-up acquisition gaps

- <gap, query, source class, or blocked access>
```

Run logs are provenance for scheduled jobs and must not contain topic synthesis.
