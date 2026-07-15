---
name: atlas-index
description: >
  Atlas vocabulary and registry maintenance entrypoint. Use when the user
  invokes /atlas-index or wants explicit Atlas term promotion, topic creation,
  or registry repair without ad hoc acquisition-driven taxonomy drift.
disableModelInvocation: true
---

# atlas-index

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `skill://atlas-core/assets/research-library-templates.md`
5. `vault://atlas/summaries/registry/VOCAB.md`
6. `vault://atlas/summaries/registry/TOPICS.md`
7. `vault://atlas/summaries/registry/RELATIONS.md`
8. `vault://atlas/summaries/sources/MANIFEST.md`

## Workflow

- Accept only explicit promotion, topic-creation, or registry-repair requests.
- For vocabulary promotion, check for duplicate or conflicting IDs before adding a `VOCAB.md` row.
- For topic creation, create the `TOPICS.md` row first, then create the subdomain/topic structure from `skill://atlas-core/assets/research-library-templates.md` only when the request explicitly asks for a durable topic.
- For repair, validate the complete registry bundle first. Use only explicit reducer events: `repair-table-placement` for unambiguous schema-valid orphan rows and `repair-relation-notes` for reason-only changes.
- Reject ambiguous rows, duplicate/conflicting IDs, malformed cells, taxonomy changes, and any repair that would widen beyond the named event. Taxonomy promotion remains a separate explicit operation.
- Persist only successful reducer output while exact input hashes still match; never place rows or calculate freshness fields by hand.
- Keep acquisition from creating domains, subdomains, aliases, tags, or topics as a side effect.
- Do not introduce a second registry backend or storage helper through this skill; storage ownership changes require an explicit architecture decision and migration.

## Output

Report exactly which registry rows, topic paths, or repair actions changed, plus any duplicate/conflict that prevented promotion.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
