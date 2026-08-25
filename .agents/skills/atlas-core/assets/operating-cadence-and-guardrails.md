# Atlas operating cadence and guardrails

This contract owns owner qualification, approval and effect gates, invocation-local resume ceilings, journal-backed exact recovery, and two-phase migration with bounded inline rollback. It adds no façade operation, provider choice, persistent run state, background work, or second authority.

## Qualification and approval

- `/atlas-ask` is the sole public Atlas behavior entry. It classifies from its exact owner/mode table before reading bound architecture, `atlas-core`, an owner resource, or the owner-result schema, and performs no semantic work, façade/profile/vault I/O, reducer work, projection, transaction, or recovery.
- Non-Atlas requests, empty goals, unresolved clarification, and classification-only outcomes load none of those Atlas resources. The front door does not preload contracts for an owner. After one owner result exists, it reads `atlas-workflow-result.schema.json`, validates that exact result once, and never reconstructs missing fields or accepts prose in its place.
- Internal owners are exactly `atlas-source`, `atlas-research`, and `atlas-maintain`. An unqualified direct owner load performs no Atlas I/O and redirects to `/atlas-ask`.
- Read-only modes are source `presence|answer`, research `answer`, and maintain `audit`. After any required material clarification, they dispatch without a write approval overview.
- Write-capable modes are source `ingest|resummarize|promote|reroute`, research `research|refresh|create`, and maintain `repair|migrate`. Before owner load, render exactly:

  ```markdown
  ## Goal
    <one concise sentence>

  ## Effect
    <maximum architecture-authorized logical owner/mode write set>

  ## Approval
    Reply **approve** to start.
  ```

- Ask at most one batched pre-approval clarification for an ambiguous request. Do not inspect Atlas state to invent the answer. Recommending a kebab-case topic slug and domain/subdomain pair from the request description is allowed. Naming a domain/subdomain authorizes insert-only compatible domain/subdomain `VOCAB.md` rows and creation of that missing subdomain index in the same topic transaction unless the user explicitly retains a stop-if-absent bound. A changed request, material answer, owner, mode, safety condition, or logical effect invalidates the overview.
- Approval is conversational dispatch authority only. It is not mutation, profile, credential, reducer, transaction, recovery, migration-commit, framework-sync, deploy, or shipping authority.
- The same agent loads one selected owner with the unchanged request and retained answers. Nested Task or structured transport is optional and never a capability stop.
- Non-Atlas repository, code, configuration, shell, and file work remains outside Atlas. Do not add direct owner commands, aliases, compatibility workflows, or an approval bypass.

## Owner execution and results

- One selected owner executes end-to-end. Route, no-pass research backfill, refresh preparation, topic create/scope revision, and separately selected migration procedures run in process, not through helper-owner chains. Only the selected owner emits the outer result.
- A qualified source owner calls default lifecycle `capabilities` exactly once and reads its mode-scoped recipe. Presence/answer/ingest/resummarize send all raw explicit URLs once to `source.inventory` with intent presence/presence/routine/resummarize. Presence freezes no winners; answer selects active unique first winners; ingest selects new/active-due first winners; resummarize selects active first winners. `promote|reroute` skip inventory.
- Presence and a write mode with no winners stop after capabilities plus inventory with the exact seven-field no-write result and no later contract, worker, model, lookup, prepare, route, transaction, or write work. Only a nonempty ingest/resummarize winner set loads mode contracts.
- Summary and classifier delivery are independent. One strict ready-summary completion contains no classification. One complete terminal classifier object is mapped through finite precedence to classified or one of three semantic-unavailable reasons. Only normalized `classificationInput` enters `source.prepare`. Transport/framing/non-object/nonterminal failure writes nothing. Classified new/changed/corrected state may append only compatible domain/subdomain/tag vocabulary; exact semantic unavailable alone materializes unclassified/routing-blocked state. Promotion invokes no classifier and preserves staged schema-2 semantics.
- Source answer keeps presence-intent operation actionability empty, then owner-selects only those active first winners. It reads the returned `artifact_uri` field in each selected entry's `manifest_row` sequentially in first-winner order, reuses a winner's account for duplicates, and never reads archived, new, rejected, or nonwinner entries.
- A source-answer account is a concise paraphrase of only that call's nonempty `vault.read.result.text`. Every selected read must succeed: the first missing, unreadable, or whitespace-empty artifact stops later reads, suppresses all accounts, and returns request-order blocked items under `blocked|none`, `next:null`, with no recovery or fallback. Each blocked item is exactly `{"id":"<request label>","summary":"<failure reason>","recovery_required":false}` and has no `status`. A malformed catalog, envelope, or result returns `framework-defect|none`; each defect item is exactly `{"id":"<request label>","summary":"<contradiction>","evidence_refs":["<operation or field>"]}` and has no `status` or `recovery_required`. At least one account yields `completed|none`; no eligible account yields `no-write|none`; an unsuccessful inventory yields `blocked|none` and no artifact read.
- The compact result has exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`. Only the front door validates the completed owner result with `atlas-workflow-result.schema.json`.
- Outcomes are `completed|no-write|needs-user|needs-guidance|blocked|framework-defect`. Effects are `none|committed|partial|unknown`.
- Prepare, inspect, and preview report `effect:none`. Journal-backed partial/unknown blocks with only the exact façade-returned recovery. Source-taxonomy remediation and source-topic-routing-v2 use separate named journal/recovery lineages: applied maps completed/committed; proven aborted/rolled-back maps blocked/none; manual conflict maps blocked/unknown with null next. Taxonomy backfill and both vocabulary insertions retain their one-file no-recovery result mapping. No lineage transfers a candidate, approval, request, target, or recovery.
- `next` is otherwise null. A blocked result invokes recovery only when `next` is a nonnull schema-valid recovery object. `recovery_required:true` with `next:null` flags human/manual intervention and grants no executable authority. Never return dispatch bindings, attempt counters, revision bundles, engineering-cycle state, or learning candidates.
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
- `source.prepare`, `source.prepare_route`, and `index.prepare_topic_scope` return generic version-1 transactions that pass unchanged through `transaction.execute|recover`; successor runs only when the façade names the sole eligible successor. Source/route guards rederive schema-2 routing/frontier projections. Topic-scope guards rederive vocabulary/index/frontier/cache projections. Expanded target allowlists never authorize a different event. `effect.execute|recover` is not an adapter.
- Research publication writes pass, topic index, subdomain index, TOPICS in order. No-pass backfill uses separate sequential source route transactions. Refresh begins with `refresh.prepare` and exact disposition-bound frontier work. Topic create is public version 3 with canonical tags; scope revision has fixed identity. Source/route, refresh, topic create/scope, aggregate effect, source-taxonomy remediation, and source-topic-routing-v2 retain their native exact recovery boundaries. One terminal partial sequence stops without hidden retry.
- A connector or capability gap returns unavailable before intent. Never fall back to direct vault edits, a host filesystem path, prompt-only parsing, or a removed command.

## Two-phase migration

- Migration activates only for an explicit versioned request through atlas-maintain migrate. Select exactly one lineage—taxonomy backfill, vocabulary-domain insertion, vocabulary-subdomain insertion, source-taxonomy remediation, or source-topic-routing-v2—before I/O; ambiguity stops.
- Phase one inspects its exact complete state and returns deterministic preview/candidate with no effect.
- Phase two requires separate commit approval bound to instance, candidate hash, operation, inventory, and write set. Regenerate and apply only that candidate. One-file lineages retain bounded forward/rollback compare-and-swap and no recovery. Source-taxonomy remediation retains its fixed 13-artifact journal. Source-topic-routing-v2 uses only its active source/topic/subdomain/core-registry candidate allowlist and isolated migration root. No migration retries, rebases, force-writes, or invokes another.
- A changed candidate, instance binding, active set, registry, sibling, target revision, operation, write set, or requested schema requires a new preview and approval before any intent. Never bulk-adopt, flatten, re-seed living state, execute an ambiguous migration, or reconstruct recovery.

## Immediate operating cadence

- Source URL work: atlas-source modes remain presence, answer, ingest, resummarize, promote, reroute. Presence/answer are read-only. Classified ingest/resummarize uses summary then independent classifier. Unclassified resummarize/reroute may classify one revision-bound stored artifact without recapture or date/content change. Reroute explicitly revalidates every active topic only after classified state. Promotion preserves staged schema 2.
- Topic work: atlas-research modes remain answer, research, refresh, create. Answer is read-only. Create/research-after-absence may insert compatible domain/subdomain/tag vocabulary and create the topic/subdomain index in one generic transaction. Create with zero candidates remains current/insufficient/null synthesis. Scope revision changes only aliases/tags/include/exclude under fixed identity and runs a normal candidate scan after its receipt. Research backfill routes normal candidates only while last_synthesized is null; refresh uses `refresh.prepare`; publication requires a fresh current zero-pending inspection and only eligible applied evidence.
- Structural work: `atlas-maintain` mode `audit|repair|migrate`. Audit is read-only; repair requires an explicit structural finding; migrate remains two-phase.
- Hooks may run cheap deterministic checks only. No hook or daemon runs synthesis, mutation, recurring audit, or hidden recovery.
- Product framework text is authored at `.agents/ARCHITECTURE.md`. Any bound-instance `sync-framework` remains a separately approved effect, followed by `python3 scripts/atlas-instance.py check`.

## Deferred capabilities

Instance-sync atomicity, symlink-hardening redesign, multi-instance partial recovery, scheduling, watchlists, SQLite, FTS, vector retrieval, dynamic connector loading, and self-healing mutation require separate architecture and approval. Markdown remains canonical and rebuildable.