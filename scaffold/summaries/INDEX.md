---
schema_version: 1
note_type: atlas-summaries-index
managed_by: atlas
last_updated: 2026-07-02
---

# Atlas Summaries

Atlas summaries are the managed research-library layer under `vault://atlas/summaries/`. Read `vault://atlas/ARCHITECTURE.md` before changing framework behavior, schemas, routing, or mode ownership.

## Artifact classes

- `source-summary` — evidence snapshot for one URL/repo/paper/thread/video/doc.
- `source-manifest` — canonical URL/source-id registry used for dedupe.
- `source-acquisition-run` — provenance log for a manual or scheduled discovery run.
- `subdomain-index` — agent router and coverage map for one domain/subdomain.
- `research-topic` — current deterministic answer contract for one durable topic.
- `research-pass` — dated, non-canonical investigation record.
- `atlas-vocab` — canonical vocabulary and alias registry for domains, subdomains, tags, source kinds, and aliases.
- `atlas-topic-registry` — topic lookup and freshness cache.
- `atlas-relations` — source-topic edge ledger and pending/applied relation source of truth.

## Managed roots

| Root | Purpose |
|---|---|
| `sources/` | Source artifacts, dedupe manifest, source index, and acquisition run logs. |
| `registry/` | Canonical vocabulary, topic freshness cache, and source-topic relation ledger. |
| `research/` | Subdomain indexes, durable topic answer contracts, and research passes. |

Do not create `domains/<domain>.md`, subdomain directories, or topic folders until a real source/topic requires them.
