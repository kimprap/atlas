# Atlas Markdown Registry Contracts

Deterministic contracts shared by Atlas command skills. Pair this file with `vault://atlas/ARCHITECTURE.md`. If the two diverge, update the architecture first, then update this file and the affected skills in the same change.

## Canonical registry tables

Each of `MANIFEST.md`, `TOPICS.md`, and `RELATIONS.md` owns exactly one canonical table with the exact scaffold header and separator. Its data region starts immediately after the separator and ends at the first line that is not a schema-shaped data row. A matching header elsewhere, a wrong cell count, or a schema-shaped row outside that region invalidates the whole registry. Orphan rows never contribute to identity, routing, freshness, or caches.

Validation rejects duplicate primary IDs, duplicate manifest canonical URLs or sequences, malformed source IDs or content hashes, invalid enums, relation edge IDs that do not match the deterministic formula, current-hash disagreements between manifest and relations, `Applied in pass` on non-`applied` rows, blank `Applied in pass` on `applied` rows, and topic caches that disagree with canonical relation rows.

For each topic, derive fields exactly from canonical relation rows:

- `Pending edge IDs`: pending rows stable-sorted by numeric `Source seq`, then `Edge ID`.
- `Dirty count`: the number of those pending rows.
- `Newest pending source seq`: the highest pending source sequence, or blank.
- `Source watermark`: the highest applied source sequence, or `0`.
- `Freshness state`: `dirty` when pending rows exist, `current` when none exist after a successful refresh, `refreshing` only after `refresh-start`, `blocked` only after `refresh-fail`, and `archived` only by explicit retirement.

Reducers replace only canonical table data rows. They preserve all non-table text byte-for-byte, preserve LF versus CRLF and final-newline state, and expose SHA-256 preconditions over exact UTF-8 input bytes. Connectors persist output only if all input document hashes still match.

## Reference reducer interface

`scripts/atlas_state.py` is the reference dependency-free implementation:

```text
validate_documents(manifest_text, topics_text, relations_text) -> list[Finding]
reduce_event(documents, event) -> ReductionResult
audit_instance(instance_root) -> list[Finding]
```

The CLI accepts a versioned JSON bundle through `--input <path|->`. `validate` emits only `ok` plus normalized findings. `reduce` emits input hashes, changed documents only, derived topic/source statuses, and applied edge IDs. Machine JSON goes to stdout; diagnostics go to stderr. If the reference implementation or a fixture-conformant port is unavailable, all Atlas mutation halts.

Every event rejects unknown and missing fields:

- `route-upsert`: `{type, source_id, content_hash, checked_on, outcome, edges[]}`. Each included edge is `{topic_id, relation, impact, confidence, reason}`. The reducer derives sequence, artifact path, and edge ID from the current manifest; preserves applied history; supersedes only old-hash pending rows; updates route status; and derives affected topic caches.
- `refresh-start`: `{type, topic_id, edge_ids, started_at}`. `edge_ids` must equal the complete pending set; set the topic to `refreshing` without changing relation status.
- `refresh-complete`: `{type, topic_id, edge_ids, pass_path, completed_on}`. Require the same complete pending set, apply it, set pass provenance, and derive `current` only when no pending rows remain.
- `refresh-fail`: `{type, topic_id, reason}`. Preserve pending edges and set the topic to `blocked`.
- `repair-table-placement`: `{type, registry}`. Rehome only schema-valid orphan rows whose primary IDs do not conflict. This is the sole reducer allowed to accept invalid input, and only when every finding is the matching orphan-row diagnostic.
- `repair-relation-notes`: `{type, repairs:[{edge_id, reason}]}`. Update Notes only; preserve every other relation field.

Normal events require fully valid input and must produce a fully valid candidate state. Validation, legal idempotent events, and deterministic rendering return byte-identical results for identical input.

## Canonical URL normalization

- Normalize every source input into one canonical URL before fetch or dedupe.
- Prefer `https` when the origin supports it.
- Drop obvious tracking query params.
- Resolve known aliases such as `x.com` -> `twitter.com` only when the canonical destination is clear.
- For GitHub sources, prefer the landing repo/page URL over raw blob URLs when the source is the repo itself.
- If one request expands to multiple canonical resources, split it into one source artifact per canonical URL.

## `source_id` and `content_hash`

- `source_id` is derived from `canonical_url`, for example shortened `sha256(canonical_url)` safe for filenames.
- `content_hash` is derived from the fetched readable source content, not from the URL string.
- A changed `content_hash` means the source materially changed and must re-enter routing.
- An unchanged `content_hash` during routine refresh updates `last_checked` only and must not create duplicate artifacts or relation edges.

## Source manifest dedupe and refresh

- `summaries/sources/MANIFEST.md` is the canonical dedupe registry.
- Lookup by both `Source ID` and `Canonical URL` before summarization.
- If the source exists and refresh is not due, skip summarization and report the existing artifact path.
- If refresh is due, fetch first, compare `content_hash`, and update only `last_checked` when unchanged.
- If the source is absent, allocate the next monotonically increasing `Source seq` and append one manifest row.
- After any new or changed source artifact write, run route-source unless the result was an unchanged duplicate skip.

## Complete readable payload boundary

- Fetch the complete readable canonical payload before computing `content_hash` or scoring `coverage`.
- When a reader reports omitted lines or ranges, page through every omitted range until no canonical payload remains unread.
- If complete retrieval still fails, hash and summarize only the materialized payload, set `coverage: partial`, and name the exact missing range or asset in `Caveats / open questions`.

## Explicit `--resummarize` transition

- Accept `--resummarize` only with an existing canonical URL or exact artifact path. Resolve the input to exactly one manifest row; a missing identity or conflicting URL/path identity halts before any write.
- Re-fetch evidence under the complete-readable-payload boundary before comparing the new `content_hash` or drafting.
- Preserve `source_id`, `source_seq`, `canonical_url`, `first_seen`, `acquired_by`, `acquisition_run`, and the artifact path. Every successful resummarization updates `last_checked` and `last_summarized`.
- Keep source-summary `schema_version: 1` and every existing frontmatter key and enum. Resummarization refines generated content; it is not a schema migration.

### Same `content_hash`

- Replace generated summary frontmatter values and body in place while preserving the manifest identity, manifest `content_hash`, acquisition provenance, and every existing `applied`, `rejected`, or `superseded` relation as history.
- Re-run the bounded verifier against every existing current-hash `pending` topic plus newly generated candidates.
- Route-source may update fields on an existing `pending` edge, move a no-longer-supported `pending` edge to `rejected`, or add a deterministic `pending` edge for a newly included topic.
- Never convert an `applied` edge back to `pending` or create a replacement pending edge for it solely because generated prose changed.

### Changed `content_hash`

- Follow normal material-change routing. Update the artifact and manifest hash in place without changing source identity or path.
- Mark every old-hash `pending` row for this source, across its topic pairs, `superseded`; preserve old `applied` rows as provenance.
- Re-run candidate generation and the bounded verifier. Create the deterministic current-hash `pending` edge only when the verifier returns `include: true`; an excluded candidate gets no replacement edge.
- Recompute every affected topic's dirty fields from `RELATIONS.md`.

### Route status after resummarization

- After routing the current hash, set artifact `routing_status` and manifest `Route status` to `routed` when at least one current-hash relation is `pending` or `applied`.
- Set both statuses to `no-topic-match` when no current-hash relation is included.
- Use `routing-blocked` only when a vocabulary or schema blocker prevents routing.
- Historical relations for an old hash do not determine current-hash route status.

## Source artifact frontmatter

Every Atlas source artifact must keep these machine-owned keys:

```yaml
schema_version: 1
note_type: source-summary
managed_by: atlas
source_id: ""
source_seq: 0
canonical_url: ""
source_kind: "article|paper|repo|thread|video|docs|other"
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

## Legal routing status values

Use only:

```text
unrouted | routed | no-topic-match | routing-blocked
```

- `unrouted` -> artifact exists but route-source has not run yet.
- `routed` -> at least one relation for the current source hash is `pending` or `applied`.
- `no-topic-match` -> no candidate relation was included for the current source hash.
- `routing-blocked` -> routing cannot proceed without an explicit vocabulary or schema repair.
- Relations for historical source hashes do not determine the current route status.

## Canonical tags and candidate terms

- `canonical_tags` may contain only IDs already present in `VOCAB.md`.
- Acquisition and source ingestion must not promote new canonical tags ad hoc.
- Useful noncanonical phrases belong in `candidate_terms`.
- `candidate_terms` are hints for later explicit promotion or routing review; they are not canonical routing keys.

## Deterministic `Edge ID`

Use exactly:

```text
edge--<source_id>--<topic_id>--<source_content_hash_8>
```

Before interpolation, replace `/`, spaces, and dots in `topic_id` with `-`.

## Route-source candidate generation

Build candidate topics from `TOPICS.md` using only:

1. exact domain/subdomain matches
2. canonical tag overlap
3. alias/include-term matches in the source title, TL;DR, or key points
4. absence of topic `Exclude terms`

If no candidates survive generation, write no new relation and determine source and manifest route status from current-hash relations under the legal routing-status rules above. Otherwise, run the bounded verifier before deciding whether a candidate is included.

## Bounded verifier output shape

For each candidate topic, the verifier must emit structured output with these fields:

```yaml
include: true|false
relation: direct|supporting|contradicting
impact: high|medium|low
confidence: high|medium|low
reason: "short evidence-based explanation"
```

For every included relation, `reason` must use exactly this machine-checkable shape:

```text
Verifier: <source-local locator> — <source-specific claim> [relation=<row relation>; impact=<row impact>]
```

Candidate-list boilerplate is not verifier provenance. The bracket values must equal the row's `Relation` and `Impact`.

The verifier reads only the source artifact plus the candidate topic row/path/scope. It must not use raw web content or rewrite topic files.

## Relation row transitions

- Allowed `Relation`: `direct`, `supporting`, `contradicting`
- Allowed `Impact`: `high`, `medium`, `low`
- Allowed `Confidence`: `high`, `medium`, `low`
- Allowed `Status`: `pending`, `applied`, `rejected`, `superseded`
- An included result creates or updates one `pending` relation edge per `(source_id, topic_id, content_hash)`, unless that exact edge is already `applied`.
- Same-hash resummarization may update a `pending` row or mark it `rejected`; it preserves `applied`, `rejected`, and `superseded` history.
- Changed-hash routing marks old-hash `pending` rows `superseded` before creating verifier-included current-hash pending rows. Excluded candidates create no replacement.
- Refresh moves the complete topic-specific pending set to `applied` and sets nonblank `Applied in pass`.
- Do not store `background`, `duplicate`, or `out-of-scope` rows in `RELATIONS.md`.

## Dirty-state recomputation from `RELATIONS.md`

A topic is dirty iff `RELATIONS.md` contains at least one `pending` row for that topic.

Recompute these `TOPICS.md` fields from relations; never increment them blindly:

- `Freshness state`
- `Dirty count`
- `Pending edge IDs`
- `Newest pending source seq`
- `Source watermark`

Sorting rule: `Pending edge IDs` must be stable-sorted by `Source seq` ascending, then `Edge ID`; dirty count and newest pending sequence use the same set, and source watermark is the highest applied source sequence.

## Quick-answer freshness gate

- Read `TOPICS.md` before any topic `INDEX.md`.
- If the topic is `current`, answer may proceed.
- If the topic is `dirty`, `refreshing`, or `blocked`, halt with topic path, freshness state, dirty count, and pending edge IDs.
- Do not answer from stale topic content plus unpersisted pending deltas.

## Managed-section patch boundaries

- Reducers patch managed sections, not whole files, unless the target file is empty or structurally broken.
- Managed sections use:

```md
<!-- atlas:managed:start <section-name> -->
...
<!-- atlas:managed:end <section-name> -->
```

- Preserve user-owned notes outside managed regions.
- Route-source never writes topic `INDEX.md`.

## Fixture cleanup requirements

Smoke fixtures are temporary verification data only.

After any Atlas smoke run:

- remove smoke source artifacts
- remove smoke acquisition run logs
- remove smoke topic folders, passes, and subdomain indexes
- remove smoke manifest, topic, relation, and vocabulary rows
- remove empty fixture directories
- rerun audit checks against the clean starter vault

Do not leave verification fixtures as part of the baseline Atlas setup.
