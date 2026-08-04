# atlas-route

## Qualified invocation

This ordinary Workflow Owner resource may execute only when one of these qualified conditions holds:

1. The selected Workflow Owner receives a live `/atlas-ask` Task whose dispatch binding names `atlas-route`.
2. An allowlisted current Workflow Owner loads this resource as a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
3. Any other load performs no further read, model work, façade call, profile/vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

Only the selected Workflow Owner emits one outer `atlas-workflow-result.schema.json` result. A Successor Owner preserves its native current output and never creates another Task or outer result.



## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core`
3. `skill://atlas-core/assets/markdown-registry-contracts.md`
4. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`

## Façade boundary

Use `scripts/atlas_tool.py capabilities|call`. `vault.read`, `state.validate`, `state.reduce`, `source.render_route_artifact`, and the transaction operations own deterministic reads, validation, projection, rendering, and effects. The agent owns only bounded candidate selection and evidence-based route decisions; it never hand-edits a relation, cache, or route field.

## Workflow

- Read the bounded source artifact, its manifest row, and the complete manifest/topic/relation bundle with `vault.read`. Run `state.validate` before proposing a normal route event; any finding stops normal routing.
- Before candidate work, guard the source explicitly: its active manifest row and artifact must agree on artifact path, source ID, canonical URL, content identity, and current route state. Any absent, archived, malformed, or disagreeing value stops before reduction or a transaction.
- Normalize source metadata against `VOCAB.md`: canonical tags must already exist; useful noncanonical phrases stay candidate terms. Form candidates only from exact domain/subdomain matches, canonical-tag overlap, alias/include-term matches in title/TL;DR/key points, and absence of exclude terms.
- For each candidate, the bounded verifier reads only the source artifact and candidate topic row/path/scope and returns `include`, `relation`, `impact`, `confidence`, and `reason`. Every included reason is exactly `Verifier: <source-local locator> — <source-specific claim> [relation=<relation>; impact=<impact>]`. It does not read raw web content or rewrite topic files.
- After the guard and completed semantic decision, call `state.reduce` once with the complete `route-upsert` event. It is a projection only: it derives legal edges, statuses, row placement, and affected cache documents; it does not choose candidates or supply verifier reasoning. If none are included, use `outcome: no-topic-match` and an empty edge list. Use `routing-blocked` only for a vocabulary or schema blocker.
- Call `source.render_route_artifact` with the reduction's route event/status and the current artifact. Persist only its artifact result and the changed documents from that projection in one `transaction.execute` route transaction. On an incomplete effect, call `transaction.recover`; call `transaction.successor` only when the façade declares the single eligible successor. A non-`applied`/`no-op` receipt stops without a force write.
- Never write a topic `INDEX.md`, reopen an applied edge, increment caches, place relation rows, or substitute a model-authored table edit.

## Output

Report routed source scope, created/updated edge IDs, terminal route status, and any missing canonical term that blocked routing.
