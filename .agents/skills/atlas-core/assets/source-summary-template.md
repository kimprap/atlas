---
schema_version: 1
note_type: source-summary
managed_by: atlas
source_id: ""
source_seq: 0
canonical_url: "<canonical url>"
source_kind: "article|paper|repo|thread|video|docs|other"
title: "<resource title>"
author: "<person or org>"
publisher: "<site or org>"
published: "YYYY-MM or YYYY-MM-DD"
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
---

<!-- Copy this template. Keep all frontmatter keys unless vault://atlas/ARCHITECTURE.md changes the schema. -->
<!-- Read skill://atlas-core/assets/source-summary-quality-guide.md and validate model-owned semantics against source-summary-proposal.schema.json before deterministic rendering. -->
<!-- Keep every required body section. Approaches / mechanics is optional only when the source contains no method. -->
<!-- Frontmatter is the machine source of truth. Keep the rendered header and Assessment table in sync. -->
<!-- source_id is derived from canonical_url, e.g. shortened sha256(canonical_url). source_seq is assigned in summaries/sources/MANIFEST.md. -->
<!-- primary_domain, subdomains, and canonical_tags contain only IDs present after source.prepare's insert-only VOCAB reduction. Put unresolved or noncanonical phrases in candidate_terms. -->
<!-- routing_status is set by route-source after the artifact is written, unless this artifact is an unchanged duplicate skip. -->
<!-- Context-neutral semantic draft: identity/retrieval metadata, Assessment, TL;DR, Key points, Approaches / mechanics, Evidence / examples, Caveats / open questions, Reuse cues, and textual source Links. Use only the declared text-only evidence envelope. -->
<!-- Post-draft Atlas annotations: the source worker proposes a capped source-intrinsic domain, subdomain, tags, and candidate terms only after the semantic draft passes. The reducer resolves or appends legal vocabulary and renders canonical IDs; topic, repo, request, and vault context never rewrite source claims. -->
<!-- Score payload stability, not project activity. A full-commit-pinned GitHub payload is stable. Retain no media or binary assets. -->

# <resource title>

**Source**: [<resource title>](<canonical url>)  
**Source ID**: `<source_id>`  
**Source seq**: `<source_seq>`  
**Kind**: `<article|paper|repo|thread|video|docs|other>`  
**Author**: <person or org>  
**Publisher**: <site or org>  
**Published**: <YYYY-MM, YYYY-MM-DD, or Unknown>
**First seen**: <YYYY-MM-DD>  
**Last checked**: <YYYY-MM-DD>  
**Last summarized**: <YYYY-MM-DD>  
**Refresh after**: <YYYY-MM-DD>  
**Route status**: `<unrouted|routed|no-topic-match|routing-blocked>`

> **TL;DR**: 1–2 source-only sentences stating the primary contribution, its scope, and the most consequential limitation.

## Assessment

| Signal | Value | Notes |
|---|---|---|
| Coverage | `complete|partial|failed` | <Exact canonical text read and missing bounds, if any.> |
| Confidence | `high|medium|low` | <What makes this summary faithful or materially uncertain.> |
| Evidence strength | `high|medium|low` | <Which source mechanics, examples, and locators support this rating.> |
| Practicality | `high|medium|low|n/a` | <What can or cannot be executed or evaluated from this source.> |
| Stability | `stable|moving|speculative` | <The immutable, durable, mutable, or exploratory fact behind this rating.> |
| Reuse value | `high|medium|low` | <Which recurring source-intrinsic question this evidence can answer.> |
| Recommended posture | `adopt|trial|watch|reference-only|ignore` | <Source-specific curation rationale, not a downstream product decision.> |

Each Notes cell must be source-specific and falsifiable by re-reading the cited evidence. Do not reuse stock assessment sentences across artifacts.

## Classification (post-draft Atlas annotation)

- Primary domain: `<resolved canonical domain id from VOCAB.md or blank>`
- Subdomains: `<resolved canonical subdomain ids from VOCAB.md>`
- Secondary domains: `<preserved canonical domain ids for an existing source; empty for a new source>`
- Canonical tags: `<up to three resolved canonical tag ids from VOCAB.md>`
- Candidate terms: `<first-winner noncanonical or unresolved useful phrases; not routing keys>`

The source worker proposes one source-intrinsic domain, one subdomain, at most three tags, and candidate terms only after the context-neutral semantic draft passes deterministic validation and the seven-item acceptance checklist. `source.prepare` resolves existing compatible identities or appends legal domain/subdomain/tag rows, never source kinds; the artifact contains only resolved IDs.

## Key points

- Use as many dense bullets as the source's depth requires; do not pad or truncate to a target count.
- Preserve the primary contribution, entry conditions, explicit claims or prohibitions, important artifacts, and consequential limits.

## Approaches / mechanics

- Describe source-stated methods, architectures, workflows, protocols, pathways, processes, interventions, decision rules, or compared options in their meaningful order.
- Keep compared approaches separate. Omit this section only when the source contains no method.

## Evidence / examples

- Start every concrete bullet with a source-local locator when available: heading or section label, command or rule label, filename or code symbol, page, line, or timestamp.
- Record benchmarks, reports, code pointers, case studies, citations, attributed claims, examples, numbers, and dates only when supported by the established text evidence boundary.
- Link to this artifact when later using it as topic evidence; do not substitute the artifact path for a source-local locator.

## Caveats / open questions

- State source-specific limits, assumptions, conflicts, unclear points, missing context, and what the source does not establish.
- State exact fetch bounds and missing canonical text ranges for `partial` or `failed` coverage.
- A generic inventory of absent git, PR, delegation, or unrelated workflow behavior is not sufficient by itself.

## Routing notes (post-draft Atlas annotation)

- Candidate topic matches considered: `<topic ids or none>`.
- For each included route: `Verifier: <source-local locator> — <source-specific claim> [relation=<row relation>; impact=<row impact>]`.
- The bracket values must equal the relation row. Candidate-list-only Notes are invalid provenance.
- Topic IDs are permitted here. Generated plan, task, session, campaign, comparison, repository, model, provider, and downstream-ownership references are not.
- Unresolved vocabulary, if any: `<exact non-routing domain/subdomain/tag proposal label or none>`.

## Reuse cues

- Record only source-intrinsic future questions this artifact can answer.
- Use plausible natural-language queries; never justify reuse by the current request, comparison, or campaign.

## Links

- Canonical: <canonical url>
- Related textual source links (optional): <url> — <source-specific relevance; only URLs present in the text evidence envelope>
- Do not embed, attach, or inventory media assets. Textual URLs only.
