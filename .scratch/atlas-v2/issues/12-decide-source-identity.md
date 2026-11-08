Type: grilling
Status: claimed
Parent: [Atlas v2](../map.md)

## Question

How does Atlas decide a source's identity and catch duplicates? Decide the canonical link rules (for example X links with and without `s=<digits>`, [Atlas v1 notes](../inputs/atlas-v1-notes.md), note 6, starting from v1's `atlas_url.py`), how the content hash marks an unchanged repeat or an update, and how Jev's near-duplicate flags work. Under the [map's standing decision on the Jev decision model](../map.md) (2026-10-29), Jev may only flag near-duplicate candidates for the agent or the user to read; the canonical link and content hash stay deterministic.

Decided before the spec, because the build's stage 2 schema (the sources table's key) and stage 3 `add` depend on it ([Decide Atlas build order](07-decide-atlas-build-order.md)). `add`'s per-link outcomes (added, already stored, updated, unreadable, a page of links) are set by [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md), section 2.
