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

- One selected owner executes end-to-end. Route, no-pass research backfill, refresh preparation, and topic creation are allowlisted in-process procedures, not helper-owner chains. Only the selected owner emits the outer result.
- A qualified source owner calls default lifecycle `capabilities` exactly once and reads its mode-scoped recipe. For `presence|answer|ingest|resummarize`, it sends all raw explicit URLs in request order to one `source.inventory` with intent `presence|presence|routine|resummarize` respectively; it never loops through `url.normalize`. Presence freezes no winners, answer selects unique first-winner entries whose disposition and returned `manifest_row` field `status` are both `active`, ingest freezes first-winner `new|active-due` entries, and resummarize freezes first-winner `active` entries.
- Presence and a write mode with no winners stop after capabilities plus inventory. They return `version:1`, `owner:"atlas-source"`, `outcome:"no-write"`, `effect:"none"`, a nonempty inventory-backed summary, one or more no-write items covering returned dispositions, and `next:null`; they perform no bound architecture, capture-contract, worker-schema, model, lookup, preparation, route, transaction, or write work. Only a nonempty ingest or resummarize winner set loads bound architecture and mode-scoped contracts. `promote|reroute` skip inventory.
- Each new or changed-hash source worker emits one capped source-intrinsic classification after the existing semantic/checklist gates. `source.prepare` resolves it against `VOCAB.md`, may append only compatible domain, subdomain, and tag rows, and binds only resulting IDs. Identity conflicts become non-routing candidate terms and do not block the source; malformed classification or vocabulary yields no targets. Same-hash work and `promote` preserve taxonomy and vocabulary bytes. Ingest classification creates no topic, subdomain index, relation, or pass.
- Source answer keeps presence-intent operation actionability empty, then owner-selects only those active first winners. It reads the returned `artifact_uri` field in each selected entry's `manifest_row` sequentially in first-winner order, reuses a winner's account for duplicates, and never reads archived, new, rejected, or nonwinner entries.
- A source-answer account is a concise paraphrase of only that call's nonempty `vault.read.result.text`. Every selected read must succeed: the first missing, unreadable, or whitespace-empty artifact stops later reads, suppresses all accounts, and returns request-order blocked items under `blocked|none`, `next:null`, with no recovery or fallback. Each blocked item is exactly `{"id":"<request label>","summary":"<failure reason>","recovery_required":false}` and has no `status`. A malformed catalog, envelope, or result returns `framework-defect|none`; each defect item is exactly `{"id":"<request label>","summary":"<contradiction>","evidence_refs":["<operation or field>"]}` and has no `status` or `recovery_required`. At least one account yields `completed|none`; no eligible account yields `no-write|none`; an unsuccessful inventory yields `blocked|none` and no artifact read.
- The compact result has exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`. Only the front door validates the completed owner result with `atlas-workflow-result.schema.json`.
- Outcomes are `completed|no-write|needs-user|needs-guidance|blocked|framework-defect`. Effects are `none|committed|partial|unknown`.
- Prepare, inspect, and preview report `effect: none`. Journal-backed `partial` requires evidence of an exact output prefix and journal-backed `unknown` requires post-intent crash or observation disagreement; both block with the exact façade-returned recovery operation and transaction identity in `next`. Source-taxonomy remediation uses this rule; its `applied` maps to `completed|committed|next:null`, proven `aborted|rolled-back` maps to `blocked|none|next:null`, and `manual-conflict` maps to `blocked|unknown|next:null`. Taxonomy-backfill remains distinct: `applied` maps to `completed|committed|next:null`; proven-preimage `rolled-back`, including sibling drift, maps to `blocked|none|next:null`; `manual-conflict` maps to `blocked|unknown|next:null` with at least one `recovery_required:true` item and no recovery operation.
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
- `source.prepare` and `source.prepare_route` return generic transactions that pass unchanged through `transaction.execute|recover`; `transaction.successor` runs only when the façade reports the sole eligible successor. A changed-vocabulary source transaction orders `VOCAB.md` first and covers it with the same immutable records, rollback, recovery, successor, and post-validation. Route preparation revalidates the lookup-bound artifact plus all four documents and never targets VOCAB. `effect.execute|recover` is not an adapter for either path.
- Research publication still writes exactly pass, topic `INDEX.md`, subdomain `INDEX.md`, and `TOPICS.md` in that order. Eligible no-pass backfill uses separate sequential source route transactions before refresh or publication; a terminal partial sequence stops the invocation without hidden retry. Refresh, topic creation, source/route, aggregate effect, and source-taxonomy remediation retain their journal-backed exact recovery contracts. Source-taxonomy remediation permits only its 13 fixed source artifacts under its dedicated migration journal and has no successor. Taxonomy backfill instead uses only its bounded inline VOCAB rollback and returns no recovery operation. The two migration lineages never call, chain, or transfer approval/candidate/request/recovery values to each other.
- A connector or capability gap returns unavailable before intent. Never fall back to direct vault edits, a host filesystem path, prompt-only parsing, or a removed command.

## Two-phase migration

- Migration activates only for an explicit versioned request through `atlas-maintain` mode `migrate`. Select exactly one of taxonomy backfill or source-taxonomy remediation from the unchanged request; ambiguity stops before I/O.
- Phase one inspects complete current state and produces a deterministic preview/candidate with `effect: none`.
- Phase two requires a separate exact commit approval bound to instance, candidate hash, operation, and write set. Regenerate and apply only that candidate. Taxonomy backfill attempts at most one forward VOCAB CAS and one exact output-to-preimage rollback CAS, then stops for manual intervention if the preimage is unproved. Source-taxonomy remediation uses only its fixed 13-path transaction, numeric-sequence CAS, complete post-validation, and exact named recovery; it never retries, rebases, force-writes, or invokes backfill.
- A changed candidate, instance binding, active set, registry, sibling, target revision, operation, write set, or requested schema requires a new preview and approval before any intent. Never bulk-adopt, flatten, re-seed living state, execute an ambiguous migration, or reconstruct recovery.

## Immediate operating cadence

- Source URL work: `atlas-source` mode `presence|answer|ingest|resummarize|promote|reroute`. Presence and answer are read-only. New and changed-hash ingest/resummarize may perform insert-only vocabulary promotion; same-hash paths and `promote` do not. Default work never starts or resumes a feed/watchlist or implicit acquisition.
- Topic work: `atlas-research` mode `answer|research|refresh|create`. Answer is read-only. Approved create, or research after an absence finding, may insert only missing compatible domain/subdomain `VOCAB.md` rows and creates the topic and any missing subdomain index in one generic topic transaction. Research then repeats inspection, and only while `topic.last_synthesized` is null enumerates and glances bounded active-source candidates and routes included pairs sequentially. It re-inspects before any optional in-process refresh, re-inspects current/zero-pending afterward, then publishes. Standalone refresh never enumerates or backfills. Only direct `high|medium` evidence may author answer-bearing sections; weaker evidence remains limited to maps, caveats, edge cases, and gaps.
- Structural work: `atlas-maintain` mode `audit|repair|migrate`. Audit is read-only; repair requires an explicit structural finding; migrate remains two-phase.
- Hooks may run cheap deterministic checks only. No hook or daemon runs synthesis, mutation, recurring audit, or hidden recovery.
- Product framework text is authored at `.agents/ARCHITECTURE.md`. Any bound-instance `sync-framework` remains a separately approved effect, followed by `python3 scripts/atlas-instance.py check`.

## Deferred capabilities

Instance-sync atomicity, symlink-hardening redesign, multi-instance partial recovery, scheduling, watchlists, SQLite, FTS, vector retrieval, dynamic connector loading, and self-healing mutation require separate architecture and approval. Markdown remains canonical and rebuildable.