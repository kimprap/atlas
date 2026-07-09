---
schema_version: 1
note_type: atlas-relations
managed_by: atlas
last_updated: 2026-07-02
---

# Atlas Source-Topic Relations

| Edge ID | Source seq | Source ID | Source artifact | Source content hash | Topic ID | Relation | Impact | Confidence | Status | Created | Applied in pass | Notes |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|

Use these exact relation-field values:

- `Relation`: `direct`, `supporting`, or `contradicting`.
- `Impact`: `high`, `medium`, or `low`.
- `Confidence`: `high`, `medium`, or `low`.
- `Status`: `pending`, `applied`, `rejected`, or `superseded`.

Do not store `background`, `duplicate`, or `out-of-scope` rows in `RELATIONS.md`; those outcomes belong only in acquisition or route run summaries.
