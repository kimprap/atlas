---
name: atlas-index
description: >
  Atlas vocabulary and registry maintenance entrypoint. Use when the user
  invokes /atlas-index or wants an explicitly approved Atlas term promotion,
  topic creation, or registry repair without acquisition-driven taxonomy drift.
disableModelInvocation: true
---

# atlas-index

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/SKILL.md`
3. `skill://atlas-core/assets/markdown-registry-contracts.md`
4. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
5. `skill://atlas-core/assets/research-library-templates.md`
6. `vault://atlas/summaries/registry/VOCAB.md`
7. `vault://atlas/summaries/registry/TOPICS.md`
8. `vault://atlas/summaries/registry/RELATIONS.md`
9. `vault://atlas/summaries/sources/MANIFEST.md`

## Façade-first workflow

- Start with `scripts/atlas_tool.py capabilities`. Before any read or mutation, require the advertised operation named by the applicable core contract.
- Read every registry, manifest, and named topic artifact through `vault.read`; obtain its exact current revision through `vault.hash`. Use `state.validate` on the complete registry bundle before a repair and `state.reduce` only with a contract-defined event. Do not invoke `atlas_state.py`, parse host paths, calculate revisions, or reproduce reducer output in the checklist.
- Accept only an explicit user-approved vocabulary promotion, durable topic creation, or named registry-repair request. Candidate terms, acquisition output, an audit finding, or a plausible taxonomy relationship never supplies promotion authority.
- For repair, permit only `repair-table-placement` for matching schema-valid orphan-row diagnostics and `repair-relation-notes` for reason-only changes. Reject ambiguous rows, duplicate/conflicting IDs, malformed cells, taxonomy changes, and any repair that widens beyond the named event.
- For a reducer-backed repair, take the candidate documents exclusively from `state.reduce`, revalidate them with `state.validate`, and use `vault.conditional_replace` only for each explicit approved target at the revision returned by `vault.hash`. The façade owns the compare-and-swap acknowledgement; no hand-authored placement, freshness calculation, hash/CAS, or rollback choreography is allowed.
- A vocabulary promotion remains an explicit semantic decision and may change only its approved `VOCAB.md` target through that same revision-bound façade call. A durable topic creation must preserve the registry/schema authority and use the core template contract for its newly authorized paths; when its exact multi-target write set has no applicable core transaction contract, halt for a contract extension or explicit migration rather than hand-rolling a transaction or rollback. Do not create a topic, domain, subdomain, alias, or tag as a side effect of acquisition or repair.
- `transaction.execute`, `transaction.recover`, and `transaction.successor` are reserved for their core-allowlisted source/route effects. If this request encounters such an existing effect, use the named transaction operation and its receipt/recovery gate. Do not fabricate a transaction record or use a source/route transaction to smuggle an index mutation. For a multi-target index change without an applicable core transaction contract, halt for a contract extension or explicit migration rather than hand-rolling a transaction or rollback.
- On a conflict, failed acknowledgement, nonterminal receipt, or failed post-state validation, stop before a wider write. Recover only through the applicable named core transaction operation; do not force-write, infer rollback state, or silently broaden the repair.
- Keep acquisition from creating domains, subdomains, aliases, tags, or topics as a side effect. Do not introduce a second registry backend or storage helper; storage ownership changes require an explicit architecture decision and migration.

## Output

Report the explicit authority, named façade operations/receipts, exact registry rows or topic paths changed, and any duplicate, conflict, unsupported multi-target effect, or failed validation that prevented promotion or repair.
