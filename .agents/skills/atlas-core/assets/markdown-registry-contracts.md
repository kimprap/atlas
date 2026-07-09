# Atlas Markdown Registry Contracts

Deterministic contracts shared by Atlas command skills. Pair this file with `vault://atlas/ARCHITECTURE.md`. If the two diverge, update the architecture first, then update this file and the affected skills in the same change.

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
- An unchanged `content_hash` means refresh updates `last_checked` only and must not create duplicate artifacts or duplicate relation edges.

## Source manifest dedupe and refresh

- `summaries/sources/MANIFEST.md` is the canonical dedupe registry.
- Lookup by both `Source ID` and `Canonical URL` before summarization.
- If the source exists and refresh is not due, skip summarization and report the existing artifact path.
- If refresh is due, fetch first, compare `content_hash`, and update only `last_checked` when unchanged.
- If the source is absent, allocate the next monotonically increasing `Source seq` and append one manifest row.
- After any new or changed source artifact write, run route-source unless the result was an unchanged duplicate skip.

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
- `routed` -> at least one pending relation edge exists.
- `no-topic-match` -> routing found no candidate topic worth dirtying.
- `routing-blocked` -> routing cannot proceed without an explicit vocabulary or schema repair.

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

If no candidates survive, set source and manifest route status to `no-topic-match`, optionally note the outcome in the acquisition run log, and stop without writing `RELATIONS.md`.

## Bounded verifier output shape

For each candidate topic, the verifier must emit structured output with these fields:

```yaml
include: true|false
relation: direct|supporting|contradicting
impact: high|medium|low
confidence: high|medium|low
reason: "short evidence-based explanation"
```

The verifier reads only the source artifact plus the candidate topic row/path/scope. It must not use raw web content or rewrite topic files.

## Relation row transitions

- Allowed `Relation`: `direct`, `supporting`, `contradicting`
- Allowed `Impact`: `high`, `medium`, `low`
- Allowed `Confidence`: `high`, `medium`, `low`
- Allowed `Status`: `pending`, `applied`, `rejected`, `superseded`
- New included routing results create or update one `pending` relation edge per `(source_id, topic_id, content_hash)`.
- Refresh moves topic-specific pending rows to `applied` and sets `Applied in pass`.
- Do not store `background`, `duplicate`, or `out-of-scope` rows in `RELATIONS.md`.

## Dirty-state recomputation from `RELATIONS.md`

A topic is dirty iff `RELATIONS.md` contains at least one `pending` row for that topic.

Recompute these `TOPICS.md` fields from relations; never increment them blindly:

- `Freshness state`
- `Dirty count`
- `Pending edge IDs`
- `Newest pending source seq`
- `Source watermark`

Sorting rule: `Pending edge IDs` must be stable-sorted by `Source seq` ascending.

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
