# atlas-source

## Qualification

Execute this resource only when the same agent has selected `atlas-source` through `/atlas-ask` and bound one mode, the unchanged request, retained material answers, and any approved Goal/Effect boundary. Any other load performs no further read, model work, façade call, profile or vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

This owner executes end-to-end in the current agent. In-process semantic and route procedures emit no owner result. Only this outer owner returns the seven-field result defined by `atlas-workflow-result.schema.json`.

## Discovery and conditional reads

After qualification, call default `python3 scripts/atlas_tool.py capabilities` exactly once and never use `--all`. Read only the `Source a URL` recipe and the recipe for the selected mode in `skill://atlas-core/assets/agent-cli-recipes.md`.

For `presence|ingest|resummarize`, run the inventory gate below before reading bound architecture, `skill://atlas-core/SKILL.md`, capture or summary contracts, the worker schema, an artifact, or any registry beyond inventory. Presence and a write-mode empty winner set stop at that gate.

Only a nonempty `ingest|resummarize` winner set then reads, in order:

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/SKILL.md`
3. `skill://atlas-core/assets/source-capture-mapping.md`
4. `skill://atlas-core/assets/source-summary-quality-guide.md`
5. `skill://atlas-core/assets/source-summary-template.md`
6. `skill://atlas-core/assets/markdown-registry-contracts.md`

`promote` and `reroute` never enter inventory. After qualification and default discovery, `promote` loads bound architecture, core, the quality guide, summary template, and registry contract; `reroute` loads bound architecture, core, the quality guide, and registry contract. Do not read capture-only contracts for either mode.

Use generated family/verb commands with one operation-args object as shown in the recipes. Decode only the version-2 response envelope. Never import a domain module, derive a host path, or reproduce identity, rendering, reducer, transaction, or recovery mechanics.

## Modes

| Mode | Approval already bound | Scope |
|---|---|---|
| `presence` | No | Read-only presence for explicit URL(s). |
| `ingest` | One Goal/Effect approval | Routine capture of explicit URL(s). |
| `resummarize` | One Goal/Effect approval | Fresh capture of explicit active URL(s). |
| `promote` | One Goal/Effect approval | Frozen staged identity/evidence pair only. |
| `reroute` | One Goal/Effect approval | Route-only update for exactly one active canonical URL. |

Reject a mode or effect wider than the bound request. Default source work accepts explicit URLs only. It never starts or resumes a feed, watchlist, inbox, repository list, author list, query sweep, or acquisition run.

## Presence, ingest, and resummarize inventory

Send the complete raw explicit URL set in request order to exactly one `source.inventory` call. Do not call a separate URL-normalization operation; inventory alone owns normalization, source-ID derivation, collision detection, deduplication, manifest classification, and first-winner selection.
The qualified operation trace starts with the required default `capabilities` call and then this one inventory call. A terminal inventory result does not omit or erase the discovery operation.

- `presence` uses intent `presence` and reports every returned disposition, but it has no actionable entries or winners. Here, actionable means continuing past inventory, not reporting an entry; its actionable disposition list is exactly `[]`.
- `ingest` uses intent `routine` and freezes only first-winner entries with disposition `new|active-due`.
- `resummarize` uses intent `resummarize` and freezes only first-winner entries with disposition `active`.

The complete disposition set is `new|active-due|active-not-due|active|archived|duplicate|rejected`. Preserve inventory-owned canonical identities, `checked_on`, `manifest_revision`, winner references, findings, and request ordering.

Presence always stops. If an ingest or resummarize winner set is empty, return exactly one result shaped as:

```json
{"version":1,"owner":"atlas-source","outcome":"no-write","effect":"none","summary":"<nonempty inventory-backed reason>","items":[{"id":"<input label or canonical URL>","status":"no-write","summary":"<returned disposition and reason>"}],"next":null}
```

Cover every returned disposition in one or more items. After this terminal, perform no bound-architecture or capture-contract read, worker-schema or model call, lookup, preparation, route, transaction, or write.

## Capture and semantic wave

For each frozen actionable winner, call `source.lookup` to bind its inventory-selected identity, obtain one complete textual capture, and map it exactly through `source-capture-mapping.md`. Pass the eight-key capture record to `source.normalize_capture`. Incomplete, truncated, nontext, empty, malformed, or unmappable input is terminal no-write for that URL: stop before artifact or registry writes and report the URL and reason. Retain only textual evidence and links; never retain media.

Call `source.worker_schema` once for the complete nonempty wave. For each unique normalized winner, run one stateless structured completion with that returned schema bound before generation and with history, tools, skill discovery, repository context, profile/vault I/O, and delegation disabled. The prompt uses the frozen inventory identity, selected `routine|resummarize` mode, and normalized capture; requires exactly the existing version-1 worker packet; and states verbatim that every proposal claim `{locator,ledger_id}` equals one evidence_ledger.evidence pair and every proposal link `{url,locator,ledger_id}` equals one evidence_ledger.links triple. Consume completions in deterministic source-ID order.

Gate every completion before another current-state read:

- Structurally malformed output stops that URL with terminal no-write.
- `kind:no-write` stops that URL with its reason.
- `kind:needs-input` may ask only the existing `source.worker-choice` question and return to the same frozen completion once.
- `kind:expanded` may ask only the existing `source.aggregate-expansion` question for a recognized aggregate page. `page-only` keeps the page, `expand` resolves its bounded depth-1 references with `url.resolve_reference` and replaces the frozen inventory wave with one complete combined-set inventory, and no answer stops. Expansion never adds an owner-side normalization loop.
- Only a schema-valid `kind:ready` packet proceeds to `source.prepare`.

One `needs-guidance` is allowed. Preserve every frozen input across resumes; never refetch or reconstruct it. Owner ceilings remain two ordered `needs-user` resumes, one `needs-guidance` resume, and four owner turns. A repeated question, short cycle, unknown or out-of-order step, answer mismatch, widened effect, or exhausted ceiling is `blocked`.

## Prepared source transaction

Process settled winners in deterministic source-ID order. Call `source.prepare` with the inventory identity, `checked_on`, exact mode `routine|resummarize`, and complete ready packet. Do not call the standalone proposal or summary quality operations: preparation alone validates the worker, proposal-ledger bindings, checklist, rendered summary, state reduction, and transaction targets.

- `terminal|rejected` stops that URL without a transaction or write.
- The first `needs-revision` permits one complete replacement from the same stateless worker with every frozen semantic input unchanged, then one final `source.prepare`. A second `needs-revision` stops without writing.
- `prepared` exposes result.transaction; pass it unchanged to generic execution.

```text
source.prepare
  → transaction.execute with the returned transaction
  → transaction.recover only with the exact returned transaction_id when required
  → transaction.successor only when the façade reports the sole eligible successor
```

The recovery and successor arrows are conditional branches, not an unconditional sequence. Do not call `transaction.recover` when execution exposes no exact recovery.

An `applied|no-op` receipt is terminal for that transaction. A successor is eligible only when the façade reports an `aborted|rolled-back` attempt-zero predecessor.

Do not convert the prepared transaction to another envelope or call aggregate effect operations after preparation. A nonterminal, `partial`, or `unknown` receipt blocks later writes and exposes only the façade-returned exact recovery operation and identity.

After an `applied|no-op` source receipt with `route_required:true`, run the route procedure below in process. It emits no second owner result.

## In-process route procedure

Preserve the existing bounded owner-side candidate enumeration and verifier. The final decision is exactly `{outcome,edges}` under the current route enums and reason sibling-equality rule; excluded candidates never enter preparation.

For an ordinary post-source route, run:

```text
one fresh source.lookup after the source receipt
  → vault.read for the bound artifact, MANIFEST, TOPICS, and RELATIONS
  → state.validate
  → one bounded candidate/verifier route decision
  → source.prepare_route with the lookup binding, route date, read revisions, and decision
  → transaction.execute with the returned transaction
  → transaction.recover only with the exact returned transaction_id when required
  → transaction.successor only when the façade reports the sole eligible successor
```

For explicit `reroute`, require exactly one canonical URL and run:

```text
source.lookup
  → source.lookup for the same canonical URL again
  → vault.read for the bound artifact, MANIFEST, TOPICS, and RELATIONS
  → state.validate
  → one bounded candidate/verifier route decision
  → source.prepare_route with the second lookup binding, route date, read revisions, and decision
  → transaction.execute with the returned transaction
  → transaction.recover only with the exact returned transaction_id when required
  → transaction.successor only when the façade reports the sole eligible successor
```

For either path, require the manifest read revision to equal the binding's `manifest_revision`; pass the artifact, TOPICS, and RELATIONS read revisions as `expected_revisions`. `source.prepare_route` revalidates one consistent snapshot and returns only `prepared`, terminal `unchanged`, or `rejected`. Execute only `prepared`; every other state stops without a transaction or write.

The two explicit-reroute lookups must be equal active bindings, including manifest revision. Drift stops before candidate work. Explicit reroute performs no inventory, active snapshot, capture, normalization, semantic source drafting, source preparation, or source-content rewrite. Neither route path changes source content hash, first-seen, checked, summarized, or refresh dates; route `checked_on` supplies only relation `Created` and artifact `routed_at`. Never adapt route work through aggregate effect execution or reproduce reducer, renderer, projection, transaction, or recovery mechanics in prose.

## Promote

`promote` accepts exactly one frozen staged artifact/evidence pair and never refetches, substitutes, or redrafts it. Call `source.prepare` with exactly `{mode:promote,artifact_uri,evidence_uri}` from the unchanged approved request. The façade reads and freezes that pair, binds exact identity, revisions, promotion provenance, current state, and target preconditions, and returns the prepared source transaction inputs.

Pass the returned `{event_record,targets}` unchanged to `transaction.execute`; use `transaction.recover` only with the exact returned transaction ID when required, and call `transaction.successor` only when the façade reports the sole eligible successor. Promotion preparation is `effect: none`. A nonterminal, `partial`, or `unknown` receipt blocks later work and exposes only the exact returned recovery operation and identity.

## Result and recovery

Return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, with `owner: atlas-source`. Use only schema-defined outcome/effect pairs. Prepare, presence, and every observed no-write path use `effect: none`.

`partial|unknown` always returns `outcome: blocked`; copy only the exact façade-returned `{operation,identity}` into `next`. Never infer success, retry hidden work, broaden recovery, or expose transaction internals when no recovery is required. Otherwise `next` is `null`.