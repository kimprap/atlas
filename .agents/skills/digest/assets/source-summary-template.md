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
published: "YYYY-MM-DD"
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

<!-- Copy this template. Keep frontmatter keys unless ARCHITECTURE.md changes the schema. Delete optional body sections that would be empty. -->
<!-- Frontmatter is the machine source of truth. The rendered header and Assessment table below are for humans. Keep them in sync. -->
<!-- source_id is derived from canonical_url, e.g. shortened sha256(canonical_url). source_seq is assigned in summaries/sources/MANIFEST.md. -->
<!-- canonical_tags may contain only IDs already present in vault://atlas/summaries/registry/VOCAB.md. Put useful noncanonical phrases in candidate_terms. -->
<!-- routing_status is set by route-source after the artifact is written, unless this artifact is an unchanged duplicate skip. -->

# <resource title>

**Source**: [<resource title>](<canonical url>)  
**Source ID**: `<source_id>`  
**Source seq**: `<source_seq>`  
**Kind**: `<article|paper|repo|thread|video|docs|other>`  
**Author**: <person or org>  
**Publisher**: <site or org>  
**Published**: <YYYY-MM-DD or Unknown>  
**First seen**: <YYYY-MM-DD>  
**Last checked**: <YYYY-MM-DD>  
**Last summarized**: <YYYY-MM-DD>  
**Refresh after**: <YYYY-MM-DD>  
**Route status**: `<unrouted|routed|no-topic-match|routing-blocked>`

> **TL;DR**: 1-2 sentences on the main point, why it matters, and what future Atlas workflow should reuse it for.

## Assessment

| Signal | Value | Notes |
|---|---|---|
| Coverage | `complete|partial|failed` | Fetch/read completeness. |
| Confidence | `high|medium|low` | Summary fidelity. |
| Evidence strength | `high|medium|low` | Source quality, specificity, corroboration, and concrete proof. |
| Practicality | `high|medium|low|n/a` | Whether a future human/agent can use the approach. |
| Stability | `stable|moving|speculative` | Expected durability. |
| Reuse value | `high|medium|low` | Likelihood future agents should reopen this artifact. |
| Recommended posture | `adopt|trial|watch|reference-only|ignore` | Best next stance. |

## Classification

- Primary domain: `<canonical domain id from VOCAB.md>`
- Subdomains: `<canonical subdomain ids from VOCAB.md>`
- Secondary domains: `<canonical domain ids from VOCAB.md>`
- Canonical tags: `<canonical tag ids from VOCAB.md>`
- Candidate terms: `<noncanonical useful phrases; not routing keys>`

## Key points

- 3-7 dense bullets.
- Prefer concrete claims, named systems, numbers, dates, and direct tradeoffs.

## Approaches / mechanics

- Methods, architectures, workflows, protocols, clinical pathways, investment processes, interventions, decision rules, or compared options.
- If the source compares multiple approaches, keep them separate.

## Evidence / examples

- Benchmarks, user reports, code pointers, case studies, citations, quoted claims, or other specifics.
- Include numbers and dates when they matter.
- Link to the source artifact itself when using this note as evidence in topic research.

## Caveats / open questions

- Limits, assumptions, conflicts, unclear points, missing context, or what the source does not prove.
- If coverage is partial or failed, say why here: paywall, JS-heavy page, rate limit, login wall, repo too large, unavailable media, or fetch error.

## Routing notes

- Candidate topic matches considered: `<topic ids or none>`.
- Route decision reason: `<why this source should or should not dirty matching topics>`.
- Missing vocabulary, if any: `<exact missing domain/subdomain/tag/source-kind id or none>`.

## Reuse cues

- The future questions or tasks this note is most useful for.
- Add 2-5 natural-language queries or tasks another agent would plausibly run later, for example `agent harnesses ranked by community effectiveness` or `factor models with out-of-sample decay data`.

## Links

- Canonical: <canonical url>
- Referenced: <url> — <why it matters>
