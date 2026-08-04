---
schema_version: 1
note_type: atlas-vocab
managed_by: atlas
last_updated: 2026-07-02
---

# Atlas Vocabulary

## Canonical terms

| ID | Type | Label | Parent | Allowed aliases | Status | Notes |
|---|---|---|---|---|---|---|
| article | source-kind | Article |  | blog post; guide | active | Source summary kind. |
| paper | source-kind | Paper |  | academic paper | active | Source summary kind. |
| repo | source-kind | Repository |  | github repo; code repository | active | Source summary kind. |
| thread | source-kind | Thread |  | x thread; forum thread | active | Source summary kind. |
| video | source-kind | Video |  | talk; demo | active | Source summary kind. |
| docs | source-kind | Documentation |  | guide; manual | active | Source summary kind. |
| other | source-kind | Other |  | misc | active | Source summary kind fallback. |

## Promotion rules

- Acquisition workflows may suggest `candidate_terms` in source artifacts but must not add rows here.
- Add a row only through `/atlas-ask` with an explicit vocabulary promotion, topic-shell, or supported registry-repair intent after checking for duplicate or conflicting IDs.
- IDs use lowercase kebab-case.
- `Type` is exactly one of `domain`, `subdomain`, `tag`, or `source-kind`.
- `Parent` is empty for domains/source-kinds, the parent domain for subdomains, and optional for tags.
- `Status` is exactly one of `active`, `deprecated`, or `reserved`.
