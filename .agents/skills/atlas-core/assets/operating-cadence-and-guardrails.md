# Atlas operating cadence and guardrails

This contract owns owner qualification, approval and effect gates, invocation-local resume ceilings, exact recovery, and two-phase migration. It adds no façade operation, provider choice, persistent run state, background work, or second authority.

## Qualification and approval

- `/atlas-ask` is the sole public Atlas behavior entry. It classifies from its exact owner/mode table before reading bound architecture, `atlas-core`, an owner resource, or the owner-result schema, and performs no semantic work, façade/profile/vault I/O, reducer work, projection, transaction, or recovery.
- Non-Atlas requests, empty goals, unresolved clarification, and classification-only outcomes load none of those Atlas resources. The front door does not preload contracts for an owner. After one owner result exists, it reads `atlas-workflow-result.schema.json`, validates that exact result once, and never reconstructs missing fields or accepts prose in its place.
- Internal owners are exactly `atlas-source`, `atlas-research`, and `atlas-maintain`. An unqualified direct owner load performs no Atlas I/O and redirects to `/atlas-ask`.
- Read-only modes are source `presence`, research `answer`, and maintain `audit`. After any required material clarification, they dispatch without a write approval overview.
- Write-capable modes are source `ingest|resummarize|promote|reroute`, research `research|refresh|create`, and maintain `repair|migrate`. Before owner load, render exactly:

  ```markdown
  ## Goal
    <one concise sentence>

  ## Effect
    <maximum architecture-authorized logical owner/mode write set>

  ## Approval
    Reply **approve** to start.
  ```

- Ask at most one batched pre-approval clarification for an ambiguous request. Do not inspect Atlas state to invent the answer. A changed request, material answer, owner, mode, safety condition, or logical effect invalidates the overview.
- Approval is conversational dispatch authority only. It is not mutation, profile, credential, reducer, transaction, recovery, migration-commit, framework-sync, deploy, or shipping authority.
- The same agent loads one selected owner with the unchanged request and retained answers. Nested Task or structured transport is optional and never a capability stop.
- Non-Atlas repository, code, configuration, shell, and file work remains outside Atlas. Do not add direct owner commands, aliases, compatibility workflows, or an approval bypass.

## Owner execution and results

- One selected owner executes end-to-end. Route, refresh preparation, and topic creation are allowlisted in-process procedures, not helper-owner chains. Only the selected owner emits the outer result.
- A qualified source owner calls default lifecycle `capabilities` exactly once and reads its mode-scoped recipe. For `presence|ingest|resummarize`, it sends all raw explicit URLs in request order to one `source.inventory`; it never loops through `url.normalize`. Presence freezes no winners, ingest freezes first-winner `new|active-due` entries, and resummarize freezes first-winner `active` entries.
- Presence and a write mode with no winners stop after capabilities plus inventory. They return `version:1`, `owner:"atlas-source"`, `outcome:"no-write"`, `effect:"none"`, a nonempty inventory-backed summary, one or more no-write items covering returned dispositions, and `next:null`; they perform no bound architecture, capture-contract, worker-schema, model, lookup, preparation, route, transaction, or write work. Only a nonempty winner set loads bound architecture and mode-scoped contracts. `promote|reroute` skip inventory.
- The compact result has exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`. Only the front door validates the completed owner result with `atlas-workflow-result.schema.json`.
- Outcomes are `completed|no-write|needs-user|needs-guidance|blocked|framework-defect`. Effects are `none|committed|partial|unknown`.
- Prepare, inspect, preview, rollback-to-proven-preimage, and every observed no-write path report `effect: none`. `partial` requires journal evidence of incomplete apply. `unknown` requires post-intent crash or observation disagreement. Both always block.
- `next` is null except for the exact already-authorized recovery operation and identity after `partial|unknown`. Never return dispatch bindings, attempt counters, revision bundles, engineering-cycle state, or learning candidates.
- Mixed sibling results use precedence: `partial|unknown` → `blocked`; proven product defect → `framework-defect`; material choice → `needs-user`; bounded semantic gap → `needs-guidance`; other blocker → `blocked`; all no-write → `no-write`; otherwise `completed`.
- A reproducible product-owned discrepancy may return one `framework-defect` with concrete evidence. Presenting a separate `dev-ask` route requires separate engineering approval. Atlas never automatically dispatches engineering, retries an owner, or starts an audit/verify/repair loop.

## Invocation-local resumes

| Owner | `needs-user` | `needs-guidance` | Maximum owner turns |
|---|---:|---:|---:|
| `atlas-source` | At most two: aggregate choice, then worker choice | At most one | 4 |
| `atlas-research` | None after dispatch | At most one | 2 |
| `atlas-maintain` | None after dispatch | At most one | 2 |

- Resume ceilings exist only in the current invocation. Do not return or persist counters, progress keys, retry state, defect queues, or background ledgers.
- A resume preserves the unchanged request, approved Goal/Effect, and prior material answers. It adds only the answer to the immediately preceding question.
- `needs-user` carries one batched material question set. `needs-guidance` carries one bounded missing-semantic set with exact evidence references. It may resolve only semantics inside the unchanged Goal/Effect.
- A repeated question, invalid answer binding, exhausted ceiling, new product decision, or wider effect returns `blocked` or starts a new front-door invocation; never widen silently.

## Exact recovery

- Write owners use the deterministic operation that prepared the effect and its native recovery operation. A recovery request is byte-identical to the authorized original request and binds its durable transaction identity.
- Classify actual current bytes and immutable journal records. Never infer success from progress, retry hidden work, reconstruct missing semantics, force-write drift, or rebase onto changed state.
- `source.prepare` and `source.prepare_route` return generic transactions that pass unchanged through `transaction.execute|recover`; `transaction.successor` runs only when the façade reports the sole eligible successor. Route preparation revalidates the lookup-bound snapshot and route-only reduction before execution. `effect.execute|recover` is not an adapter for either path.
- Research publication writes exactly pass, topic `INDEX.md`, subdomain `INDEX.md`, and `TOPICS.md` in that order. Refresh, topic creation, source/route, aggregate effect, and migration retain their own exact recovery contracts.
- A connector or capability gap returns unavailable before intent. Never fall back to direct vault edits, a host filesystem path, prompt-only parsing, or a removed command.

## Two-phase migration

- Migration activates only for an explicit versioned request through `atlas-maintain` mode `migrate`.
- Phase one inspects complete current state and produces a deterministic preview/candidate with `effect: none`.
- Phase two requires a separate exact commit approval bound to instance, candidate hash, operation, and write set. Apply only that candidate or invoke its exact recovery.
- A changed candidate, instance binding, target revision, or requested schema requires a new preview and approval. Never bulk-adopt, flatten, or re-seed living state.

## Immediate operating cadence

- Source URL work: `atlas-source` mode `presence|ingest|resummarize|promote|reroute`. Default work never starts or resumes a feed/watchlist or implicit acquisition.
- Topic work: `atlas-research` mode `answer|research|refresh|create`. Answer is read-only; approved research may refresh in process and must re-inspect current state before publication.
- Structural work: `atlas-maintain` mode `audit|repair|migrate`. Audit is read-only; repair requires an explicit structural finding; migrate remains two-phase.
- Hooks may run cheap deterministic checks only. No hook or daemon runs synthesis, mutation, recurring audit, or hidden recovery.
- Product framework text is authored at `.agents/ARCHITECTURE.md`. Any bound-instance `sync-framework` remains a separately approved effect, followed by `python3 scripts/atlas-instance.py check`.

## Deferred capabilities

Instance-sync atomicity, symlink-hardening redesign, multi-instance partial recovery, scheduling, watchlists, SQLite, FTS, vector retrieval, dynamic connector loading, and self-healing mutation require separate architecture and approval. Markdown remains canonical and rebuildable.