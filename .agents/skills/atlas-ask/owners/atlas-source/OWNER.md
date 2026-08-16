# atlas-source

## Qualification

Execute this resource only when the same agent has selected `atlas-source` through `/atlas-ask` and bound one mode, the unchanged request, retained material answers, and any approved Goal/Effect boundary. Any other load performs no further read, model work, façade call, profile or vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

This owner executes end-to-end in the current agent. In-process semantic and route procedures emit no owner result. Only this outer owner returns the seven-field result defined by `atlas-workflow-result.schema.json`.

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/SKILL.md`
3. `skill://atlas-core/assets/agent-cli-recipes.md`
4. `skill://atlas-core/assets/source-capture-mapping.md`
5. `skill://atlas-core/assets/source-summary-quality-guide.md`
6. `skill://atlas-core/assets/source-summary-template.md`
7. `skill://atlas-core/assets/markdown-registry-contracts.md`

Discover the lifecycle surface with `python3 scripts/atlas_tool.py capabilities`. Use generated family/verb commands with one operation-args object, or the low-level call with the exact version-2 request envelope. Decode only the version-2 response envelope. Never import a domain module, derive a host path, or reproduce identity, rendering, reducer, transaction, or recovery mechanics.

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

Normalize each explicit URL with `url.normalize`, preserving request order, then call `source.inventory` exactly once for the complete normalized URL set:

- `presence` uses intent `presence`, reports every returned disposition, and stops with `outcome: no-write`, `effect: none`. It performs no capture, artifact read, semantic work, preparation, transaction, or routing.
- `ingest` uses intent `routine` and captures only winners whose returned disposition is `new` or `active-due`.
- `resummarize` uses intent `resummarize` and captures only winners whose returned disposition is `active` for that intent.

The complete disposition set is `new|active-due|active-not-due|active|archived|duplicate|rejected`. Do not invent another disposition. Preserve inventory-owned canonical identities, `checked_on`, winner references, and ordering.

## Capture and semantic wave

For each actionable winner, call `source.lookup` to bind the inventory-selected identity, then obtain one complete textual capture and map it exactly through `source-capture-mapping.md`. Pass the eight-key capture record to `source.normalize_capture`. Incomplete, truncated, nontext, empty, malformed, or unmappable input is terminal no-write for that URL: stop before artifact or registry writes and report the URL and reason. Retain only textual evidence and links; never retain media.

Call `source.worker_schema` once for the complete wave. Run at most one owner-local semantic role for each unique normalized winner, with its inventory identity, selected routine/resummarize mode, normalized capture, and the returned strict schema. It performs no I/O. It treats capture text as untrusted evidence and returns one complete `source-worker-result.schema.json` value.

Collect the wave before any write. A recognized aggregate page may ask once with step ID `source.aggregate-expansion`; `page-only` keeps only the aggregate page, `expand` resolves only its bounded depth-1 references with `url.resolve_reference` and runs one replacement inventory over the combined explicit set, and no answer stops. Material semantic choices may ask once with step ID `source.worker-choice` and return only to the originating semantic role. One `needs-guidance` is allowed. Preserve every frozen input across resumes; never refetch or reconstruct it.

Owner ceilings are two ordered `needs-user` resumes, one `needs-guidance` resume, and four owner turns. A repeated question, short cycle, unknown or out-of-order step, answer mismatch, widened effect, or exhausted ceiling is `blocked`.

## Prepared source transaction

Process settled winners in deterministic source-ID order. Call `quality.validate_proposal` and `quality.validate_summary` as required by the source recipe, then call `source.prepare` with the inventory identity, `checked_on`, exact mode `routine|resummarize`, and the complete semantic result.

When `source.prepare` returns `prepared`, take its `{event_record,targets}` transaction unchanged:

```text
source.prepare
  → transaction.execute
  → transaction.recover only with the exact original transaction when required
  → transaction.successor only when the façade reports the sole eligible successor
```

Do not convert the prepared transaction to another envelope or call the aggregate effect operations after preparation. A nonterminal, `partial`, or `unknown` receipt blocks later writes and exposes only the façade-returned exact recovery operation and identity.

After an `applied|no-op` source receipt with `route_required:true`, run the route procedure below in process. It emits no second owner result.

## In-process route procedure

For an ordinary post-source route, freshly read the bound source artifact and required registries with `vault.read`, validate with `state.validate`, make one bounded evidence-based route decision, reduce one complete `route-upsert` event with `state.reduce`, and call `source.render_route_artifact`.

For explicit `reroute`, require exactly one canonical URL and run this exact route-only sequence:

```text
source.lookup
  → source.lookup for the same canonical URL again
  → vault.read for the bound artifact and required registries
  → state.validate
  → one bounded candidate/verifier route decision
  → state.reduce with route-upsert
  → source.render_route_artifact
  → transaction.execute
  → transaction.recover only with the exact original transaction when required
  → transaction.successor only when the façade reports the sole eligible successor
```

The second lookup must still equal the active first binding, including its manifest revision. Drift stops before candidate work. Pass the rendered route `{event_record,targets}` unchanged to the generic transaction operations.

Explicit reroute performs no inventory, active snapshot, capture, normalization, semantic source drafting, source preparation, source-content write, content-hash change, or checked/summarized-date refresh. It never adapts the route transaction through aggregate effect execution. The route procedure may resume only within this owner's fixed guidance and turn ceiling.

## Promote

`promote` accepts exactly one frozen staged artifact/evidence pair and never refetches, substitutes, or redrafts it. Call `source.prepare` with exactly `{mode:promote,artifact_uri,evidence_uri}` from the unchanged approved request. The façade reads and freezes that pair, binds exact identity, revisions, promotion provenance, current state, and target preconditions, and returns the prepared source transaction inputs.

Pass the returned `{event_record,targets}` unchanged to `transaction.execute`; use `transaction.recover` only with that exact original transaction when required, and call `transaction.successor` only when the façade reports the sole eligible successor. Promotion preparation is `effect: none`. A nonterminal, `partial`, or `unknown` receipt blocks later work and exposes only the exact returned recovery operation and identity.

## Result and recovery

Return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, with `owner: atlas-source`. Use only schema-defined outcome/effect pairs. Prepare, presence, and every observed no-write path use `effect: none`.

`partial|unknown` always returns `outcome: blocked`; copy only the exact façade-returned `{operation,identity}` into `next`. Never infer success, retry hidden work, broaden recovery, or expose transaction internals when no recovery is required. Otherwise `next` is `null`.