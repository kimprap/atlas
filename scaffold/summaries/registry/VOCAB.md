---
schema_version: 1
note_type: atlas-vocab
managed_by: atlas
last_updated: 2026-08-19
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

- New and changed-hash source ingest/resummarize may append source-intrinsic `domain`, `subdomain`, and `tag` proposals after complete worker validation. Same-hash work and `promote` never change this table.
- Resolve each trimmed ASCII-case-folded proposal token set against every row ID, label, and decoded allowed alias. Reuse exactly one compatible match byte-for-byte; append a zero-match eligible proposal; degrade ambiguity, source-kind contact, type mismatch, or parent mismatch to the source artifact's non-routing `candidate_terms`.
- New rows are `active`, preserve the worker label and aliases, leave Notes empty, use the resolved domain ID as a new subdomain's parent, and give new tags an empty parent. Append in domain, subdomain, then worker tag order without rewriting existing rows or surrounding prose.
- Source workflows never add, edit, delete, deprecate, reserve, or repair a `source-kind` row. Labels and allowed aliases need not be unique across rows or types; the repeated `guide` alias above is valid.
- IDs use lowercase kebab-case matching `[a-z0-9][a-z0-9-]*`.
- `Type` is exactly one of `domain`, `subdomain`, `tag`, or `source-kind`.
- `Parent` is empty for domains/source-kinds, the parent domain for subdomains, and optional for tags; ingest-created tags use an empty parent.
- `Status` is exactly one of `active`, `deprecated`, or `reserved`; ingest writes only `active`.
