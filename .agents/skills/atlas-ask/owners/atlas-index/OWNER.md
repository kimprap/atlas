# atlas-index

## Qualified invocation

This ordinary Workflow Owner resource may execute only when one of these qualified conditions holds:

1. The selected Workflow Owner receives a live `/atlas-ask` Task whose dispatch binding names `atlas-index`.
2. An allowlisted current Workflow Owner loads this resource as a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
3. Any other load performs no further read, model work, façade call, profile/vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

Only the selected Workflow Owner emits one outer `atlas-workflow-result.schema.json` result. A Successor Owner preserves its native current output and never creates another Task or outer result.



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
- A vocabulary promotion remains an explicit semantic decision and may change only its approved `VOCAB.md` target through that same revision-bound façade call. For an explicitly approved absent-topic creation, require the advertised `index.create_topic` capability and construct exactly one semantic request with exactly these keys (using the approved values, not target bytes or revisions):
  ```json
  {
    "version": 1,
    "topic_id": "<topic-id>",
    "topic_path": "vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md",
    "domain": "<domain-id>",
    "subdomain": "<subdomain-id>",
    "canonical_title": "<canonical-title>",
    "aliases": [],
    "include_terms": [],
    "exclude_terms": [],
    "related_topic_ids": [],
    "status": "active",
    "coverage_state": "insufficient",
    "confidence": "low",
    "refresh_model": "same-as-topic-creation",
    "created_on": "YYYY-MM-DD"
  }
  ```
  Populate the arrays and scalar identity fields from the explicit approved request in the contract's required normalized form; do not add keys or silently rewrite values. At the start of this branch, the skill selects one explicit UTC calendar date and replaces the `YYYY-MM-DD` placeholder with that date; it reuses the same value unchanged in the request and receipt, and the renderer must not obtain a hidden date. Issue exactly `{"version":1,"op":"index.create_topic","args":<that request>}` through the façade. This operation alone owns validation, rendering, request hashing, the topic → subdomain → `TOPICS.md` target set, revisions, CAS, durability, and rollback. Do not hand-author Markdown, calculate revisions, invoke `vault.conditional_replace`, order targets, or call source/route transaction operations for topic creation.
- If that named create attempt returns a recoverable/nonterminal result, stop before any wider action and retain the exact original request object and returned attempt transaction ID. A user-named recoverable attempt is recovered only by requiring `index.recover_topic` and issuing exactly `{"version":1,"op":"index.recover_topic","args":{"version":1,"transaction_id":"<attempt-id>","request":<the byte-identical original request>}}`. Report the returned terminal state, authority/paths/revisions, receipt, validation, findings, and `successor_eligible`; recovery only classifies/restores through the façade, and the skill never force-writes, substitutes bytes, performs rollback choreography, or invokes a successor/replay operation.
- Topic provenance is closed by stable identity, not full-request scanning: the façade validates every sibling under the topic namespace digest and every immutable input/output-bound base before reading live targets. Exact event-only replay may continue only when the owner reproduces identical canonical request, inputs, outputs, and base; a stale event is never rebound and must be closed as `aborted` by the named recovery operation. Once intent exists, creation stops and only named recovery may classify or apply effects.
- Each base has only `a000000` and one exact `a000001` successor. A changed input/output binding never consumes a doomed stale successor; a fresh base is considered only after every prior sibling is a valid closed non-applied terminal and no exact successor remains executable. Applied historical terminals remain immutable authority and do not require rereading old product bytes. No global transaction scan, mutable latest pointer, pruning, retry beyond a1, or direct CAS workflow is permitted.
- `transaction.execute`, `transaction.recover`, and `transaction.successor` are reserved for their core-allowlisted source/route effects. If this request encounters such an existing effect, use the named transaction operation and its receipt/recovery gate. Do not fabricate a transaction record or use a source/route transaction to smuggle an index mutation. On a conflict, failed acknowledgement, nonterminal receipt, or failed post-state validation, stop before a wider write. Recover only through the applicable named core operation with the exact original request; do not force-write, infer rollback state, or silently broaden the repair.
- Keep acquisition from creating domains, subdomains, aliases, tags, or topics as a side effect. Do not introduce a second registry backend or storage helper; storage ownership changes require an explicit architecture decision and migration.

## Output

Report the explicit user authority and returned named façade operation; for topic creation or recovery, report the returned state, exact topic/subdomain/registry paths, revisions, transaction provenance, receipt (or `null` for confirmation), validation, findings, and `successor_eligible` when returned. Also report any duplicate, conflict, unsupported multi-target effect, or failed validation that prevented promotion or repair.
