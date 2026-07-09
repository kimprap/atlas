---
schema_version: 1
note_type: sources-index
managed_by: atlas
last_updated: 2026-07-02
---

# Atlas Sources

Source summaries live under `artifacts/<YYYY>/<YYYY-MM>/`.

Acquisition run logs live under `runs/<YYYY>/<YYYY-MM>/`.

Dedupe is driven by `MANIFEST.md`.

Scheduled acquisition should use feeds, inboxes, or watchlists, not unconstrained web scraping.

Source acquisition does not directly mutate research topics. New or changed source artifacts must route through the registry layer first.

## Lookup order

1. Read `MANIFEST.md` by canonical URL or source ID.
2. Open the artifact path listed in the manifest.
3. Check route status before expecting a source to affect topic freshness.
4. Use acquisition run logs only for provenance and rejected/no-match counts.
