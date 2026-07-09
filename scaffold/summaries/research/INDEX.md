---
schema_version: 1
note_type: research-index
managed_by: atlas
last_updated: 2026-07-02
---

# Atlas Research

Research subdomains live under `<domain>/<subdomain>/`.

Each subdomain has `INDEX.md`.

Durable topics live under `topics/<topic-slug>/INDEX.md`.

Topic indexes are deterministic answer contracts backed by source artifacts.

Vault-only synthesis is default, and acquisition-first must materialize source artifacts before synthesis.

Optional split files are created only when the split thresholds in `ARCHITECTURE.md` are met.

## Lookup order

1. Resolve the topic in `vault://atlas/summaries/registry/TOPICS.md`.
2. If `Freshness state=current`, read the topic `INDEX.md`.
3. If `Freshness state=dirty|refreshing|blocked`, halt or refresh according to `vault://atlas/ARCHITECTURE.md`; do not answer from stale topic content.
4. Read optional split files only when the topic `INDEX.md` points to them.
