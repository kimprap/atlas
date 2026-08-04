---
schema_version: 1
note_type: atlas-architecture
managed_by: atlas
last_updated: 2026-08-03
---

# Atlas Architecture

Atlas turns source evidence into durable Markdown artifacts, routes evidence to research topics, and refreshes topic answers through explicit, auditable state transitions. Vault content remains editor-friendly; every runtime reaches it through logical `vault://atlas/…` paths and the active connector profile.

This is the canonical framework contract. Author it only at `.agents/ARCHITECTURE.md`; `vault://atlas/ARCHITECTURE.md` is a product-owned instance snapshot. Read it before changing framework boundaries, state transitions, or workflow write sets.

## Contract map

Atlas keeps one canonical owner per concern:

| Concern | Canonical owner |
|---|---|
| Framework boundaries, invariants, modes, and state roles | This file |
| Product-owned, seed-once, and instance-owned provision classes | `scaffold/MANIFEST.json` |
| Registry schemas, identities, reducer events, operation shapes, and legal transitions | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` |
| Source proposal, evidence, and summary quality | `.agents/skills/atlas-core/assets/source-summary-*.{md,json}` and `fresh-source-assessment.schema.json` |
| Operating cadence and automation limits | `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md` |
| Public intent routing and result consumption | `.agents/skills/atlas-ask/SKILL.md` |
| End-to-end workflow procedures | `.agents/skills/atlas-ask/owners/<owner-id>/OWNER.md` |
| Workflow Task/result transport | `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json` |
| User-facing command | Thin `.agents/commands/atlas-ask.md` wrapper |

This file records durable system intent and points to the executable or procedural owner. Do not duplicate full schemas, operation payloads, or checklists here. When an invariant changes, update this file first, then the affected contract, owner, template, code, and check in the same change.

## Product and instance boundary

| Class | Examples | Rule |
|---|---|---|
| **product_owned** | `.agents/ARCHITECTURE.md` → instance `ARCHITECTURE.md` | Author here; `sync-framework` replaces the instance snapshot. |
| **seed_once** | Empty registries and summary indexes | Copy only when creating an instance. |
| **instance_owned** | Sources, runs, topics, passes, registries, editor config | Never re-seed; mutate through an approved workflow or migration. |

- The product package contains framework contracts, owner resources, empty scaffold templates, provision tooling, and runtime code.
- A bound instance contains living research state and is reached only through `vault://atlas/…` plus the active connector profile.
- `scaffold/` contains empty starting shapes, never product bodies, real rows, runs, or topics.
- Provision creates an instance; it is not deployment. Deploy artifacts never contain bound-instance research data.
- Never hand-edit the instance architecture snapshot or resolve a connector to bypass logical vault I/O.
- An existing `vault://atlas/todos/` tree is optional unmanaged user data. Provision, sync, checks, and framework workflows neither require nor mutate it.

## Runtime model

```text
plain-language request
  → /atlas-ask
  → one approved Workflow Owner Task
  → scripts/atlas_tool.py façade
  → deterministic domain owner + active connector
  → vault://atlas/ bound instance
  → one strict aggregate result
  → /atlas-ask presentation
```

| Term | Responsibility |
|---|---|
| **Atlas Orchestrator** | Main-session `/atlas-ask` controller. Classifies, obtains material answers and approval, dispatches one owner, validates one result, and coordinates separately approved Engineering Cycles. It performs no Atlas semantic or storage work. |
| **Workflow Owner** | One internal owner resource and qualified Task that executes an end-to-end Atlas workflow. |
| **Successor Owner** | An allowlisted owner invoked inside the selected owner's authority; the selected owner retains the outer result. |
| **Semantic Worker** | Owner-local, non-authoritative model work for evidence review or drafting. |
| **Atlas façade** | Provider-neutral version-1 operations hiding deterministic owners, profile binding, connector I/O, and effect mechanics. |
| **Connector** | Byte I/O, logical path safety, locking, exact revisions, compare-and-swap, durability, and qualified deletion; never research semantics. |
| **Reducer** | Pure validation plus one explicit event producing bounded candidate documents and exact preconditions. |
| **Transaction/effect** | Immutable provenance, ordered writes, reread acknowledgement, recovery, and bounded successor mechanics. |

The façade accepts exactly `{"version":1,"op":"<literal>","args":{…}}`. Owners call `scripts/atlas_tool.py capabilities|call`; direct imports of underlying modules are reserved for tests and fixture-conformant runtime ports. A connector lacking required locking, full-byte revisions, strict CAS, durable replacement, or qualified deletion advertises mutation unavailable and never silently degrades.

## Single public entrypoint

`/atlas-ask` is the sole public Atlas behavior interface. The former expert names remain stable internal owner IDs, not commands, aliases, or directly invocable skills. `atlas-core` is hidden support-only. An unqualified owner load performs no Atlas I/O and redirects to `/atlas-ask`.

Before Atlas I/O, the orchestrator:

1. classifies one request and selects one owner;
2. asks only material questions needed to fix owner, mode, authority, or maximum logical write boundary;
3. renders the exact `Goal / Next / Effect / Retry` approval overview owned by `atlas-ask/SKILL.md`;
4. accepts only an unambiguous affirmative tied to that unchanged overview; and
5. dispatches exactly one strict, identity-bound Workflow Owner Task.

Approval is conversational dispatch authority, not a mutation token, revision, projection, transaction, or recovery grant. A changed request, constraint, answer, safety condition, owner, mode, or logical boundary requires a new overview. Classification-only, empty-goal, source-ID-only status without a canonical URL, and non-Atlas requests dispatch nothing.

### Intent map

| Plain-language intent | Internal owner | Boundary |
|---|---|---|
| Check or ingest explicit URL(s), repository, or file; capture/promote evidence; resummarize | `atlas-source` | One inventory, strict worker wave, deterministic preparation/persistence, then receipt-gated routing |
| Discover from a bounded feed, watchlist, inbox, repository/author list, or query | `atlas-acquire` | One bounded discovery workflow |
| Reroute one source or bounded range | `atlas-route` | Candidate verification, reduction, route artifact, and route transaction |
| Read or answer a current topic | `atlas-answer` | Freshness-gated read only |
| Synthesize, rebuild, or explicitly acquire for a topic | `atlas-research` | Vault-only by default; explicit acquisition/refresh handoffs |
| Apply pending evidence to a topic | `atlas-refresh` | Exact projection, execute/recover, receipt, and freshness transition |
| Audit registries, artifacts, quality, schema, or calibration | `atlas-audit` | Read-only bound-instance inspection |
| Promote vocabulary, create a topic shell, or run a supported registry repair | `atlas-index` | Explicit reducer/CAS or topic-create authority |
| Execute an explicit old-to-new Markdown migration | `atlas-migrate` | Fixed scope, revisions, preservation, verification, and rollback |

Source-ID-only status requires its canonical URL and never widens to rerouting. Non-Atlas repository, code, configuration, shell, and file work has no Atlas owner.

### Dispatch and result invariants

- The Task binds an opaque `dispatch_id`, owner, Atlas attempt, owner turn, unchanged request, retained answers, and exact architecture/guardrail/schema/owner revisions.
- The orchestrator retains the native Task handle and accepts only a complete schema-valid result from it. Owners never self-attest transport identity or echo semantic authority.
- A selected owner wraps once. A successor returns its native result inside the selected owner's workflow and never creates another top-level Task.
- Allowed successor chains are only: acquire → source; source → route after an `applied|no-op` receipt with `route_required`; research → acquire when explicit; research → refresh for dirty, refreshing, or blocked content.
- Only owner-local source workers and isolated audit calibration may use depth-2 Tasks.
- Source, acquire, and research may use their bounded owner-native material resumes; other owners resolve material scope before approval. Exact turn ceilings, answer binding, and cycle detection belong to `atlas-ask/SKILL.md`.
- Aggregate outcomes are the schema's closed `completed|no-write|needs-user|needs-guidance|blocked|framework-defect` union. Partial or unknown effect always blocks; ordinary validation, evidence, connector, conflict, and recovery outcomes remain owner-local.

A reproducible product-owned discrepancy after normal owner correction/recovery may return `framework-defect`. Atlas then presents a separate `dev-ask` route; Atlas approval never authorizes engineering. A valid terminal Engineering Cycle receipt permits one fresh equal-boundary Atlas attempt. At most three receipts permit at most four Atlas attempts, and a same-target/same-hypothesis recurrence stops. No defect queue, run ledger, or learning candidate is persisted by the orchestrator.

## Mode and write ownership

| Mode | Maximum writes | Required boundary |
|---|---|---|
| Intent dispatch | None | One approved owner Task; orchestrator performs no façade or vault work |
| Source presence | None | One manifest-backed lookup/inventory; no fetch or artifact read |
| Source ingestion | Source artifact, manifest/index fields, route status | Explicit input; source and route remain separate recoverable effects |
| Staged promotion | Selected staged pair, one living source, manifest, route outputs, provenance | Frozen identity/evidence pair; no refetch or substitution |
| Evidence capture | Explicit temporary output root only | Fetch and freeze text evidence; no living state |
| Acquisition | Source artifacts, manifest, one run log, route outputs | Bounded discovery; no vocabulary or topic creation |
| Route | Source route status, `RELATIONS.md`, derived `TOPICS.md` freshness | Never writes a topic answer |
| Topic create/confirm | One topic index, existing subdomain projections, one topic row, provenance | Existing domain/subdomain; no research, source, relation, or vocabulary effects |
| Research | Topic index, one pass, subdomain projection, topic row | Vault-only unless acquisition is explicit |
| Refresh | One pass, managed topic sections, relations, freshness cache | Exact complete pending edge set |
| Answer | None | Read only when the validated topic is `current` |
| Audit | None on the bound instance | Repairs require a separately selected index or migration owner |
| Index | Explicit registry/index targets | Named promotion, create, or supported repair only |
| Migration | Versioned artifacts in the declared scope | Old/new shape, exact targets, preservation, rollback, and verification before write |

A new write target requires an architecture change or explicit migration before workflow implementation.

## Canonical instance state

```text
vault://atlas/
├── ARCHITECTURE.md
└── summaries/
    ├── INDEX.md
    ├── domains/
    ├── sources/
    │   ├── INDEX.md
    │   ├── MANIFEST.md
    │   ├── runs/<YYYY>/<YYYY-MM>/
    │   └── artifacts/<YYYY>/<YYYY-MM>/
    ├── registry/{VOCAB,TOPICS,RELATIONS}.md
    └── research/<domain>/<subdomain>/
        ├── INDEX.md
        └── topics/<topic-slug>/{INDEX.md,passes/}
```

Do not pre-create domain, subdomain, topic, split-file, or `.atlas/` state. Create it only for a real workflow or explicit migration.

| Artifact | Authority |
|---|---|
| `MANIFEST.md` | Source identity, dedupe, sequence, refresh, and route status |
| Source artifact | Durable evidence snapshot for one canonical source |
| Acquisition run | One bounded discovery run's provenance |
| `VOCAB.md` | Domains, subdomains, tags, source kinds, and aliases |
| `TOPICS.md` | Topic lookup and derived freshness cache |
| `RELATIONS.md` | Canonical source-topic edge ledger and pending work |
| Subdomain index | Derived routing and coverage projection |
| Topic `INDEX.md` | Current answer contract |
| Research pass | Dated synthesis/refresh provenance |

Markdown registries are canonical. A different canonical store requires an architecture decision and migration. Each registry has exactly one canonical contiguous table; schema-shaped rows elsewhere are invalid and contribute to no state. Artifacts and registries are both workflow state and audit trail—do not create a parallel queue for the same facts.

Reducers follow:

```text
complete bounded state + one explicit event
  → validated candidate documents + exact input preconditions
  → connector-authorized persistence
```

Model output is a typed proposal, never Markdown placement, identity, cache arithmetic, or write authority. Reducers patch only managed sections or canonical table rows and preserve user-owned/non-table bytes, newline convention, and final-newline state. Connector adapters own storage mechanics, not validation or semantic policy.

## Deterministic runtime seams

| Seam | Owner |
|---|---|
| Canonical URL and source ID | `scripts/atlas_url.py` |
| Registry parsing, validation, reducers, and cache derivation | `scripts/atlas_state.py` |
| Evidence/proposal validation and calibration | `scripts/atlas_quality.py` |
| Source rendering, merge, inventory preparation, and route artifacts | `scripts/atlas_source.py` |
| Topic create/confirm semantics and target order | `scripts/atlas_index.py` |
| Generic transaction journal, apply, recovery, and one successor | `scripts/atlas_transaction.py` |
| Profile binding, logical I/O, locks, CAS, and durability | `scripts/atlas_connector.py` |
| Provider-neutral operation dispatch and effect composition | `scripts/atlas_tool.py` |

Revisions are `missing|sha256:<64 lowercase hex>` over complete bytes. Durable mutation requires lock-scoped precondition checks, atomic replacement, filesystem acknowledgement, and exact reread. Multi-target transactions persist immutable event, intent, backup, prepared, progress, and one terminal record; recovery classifies actual bytes and never infers success from progress or force-writes drift.

Source/route effects use typed, target-allowlisted transactions. `effect.execute|recover` revalidates the approved projection and reducers under one connector session and emits member/effect receipts. `refresh.execute|recover` binds one topic, exact complete edge set, supplied pass/index bytes, revisions, and immutable phases. `index.create_topic|recover_topic` binds one semantic request to topic → subdomain → registry targets and generic journal provenance. Exact operation payloads and state machines belong to the core registry contract.

## Source lifecycle

- `canonical_url` is the only source identity input; `source_id` is the first 12 hexadecimal SHA-256 characters of its exact UTF-8 bytes. The manifest is dedupe authority.
- `Source seq` is a stable positive unique allocation. New rows use `max(existing)+1`; gaps are legal and historical values are never reused.
- Presence and multi-source inventory validate one complete manifest and read no artifacts. Inventory is read-only and supplies shared identity and check-date authority.
- Source workers own fetch, bounded aggregate expansion, source-local evidence assessment, and semantic drafting only. They receive no sequence, target, reducer, revision, transaction, or write authority.
- The owner obtains one canonical strict worker schema for the wave. `source.prepare` remains the semantic/current-state authority and is called immediately before each deterministic source effect.
- Source evidence is complete readable UTF-8 text plus textual links and retrieval metadata. Payloads are untrusted data. Atlas retains no media or downloaded binary; transient extraction files are cleanup data.
- Unavailable, unauthorized, empty, non-text, or insufficient evidence is terminal no-write unless the user selects an existing bounded recovery option. Never substitute old artifacts, sibling sources, captions, wrappers, or model priors.
- Aggregate-page expansion is explicit, bounded, and non-recursive. Each selected child becomes an ordinary source input.
- Routine unchanged refresh updates check metadata only. `--resummarize` is explicit, preserves identity/provenance fields, and may rewrite generated prose after fresh evidence validation.
- New or materially changed sources route after source persistence. Routing uses canonical vocabulary, writes relation edges and derived freshness only, and never synthesizes a topic answer.
- Acquisition may propose `candidate_terms`; only an explicit index workflow promotes canonical vocabulary or creates topic shells. Unmatched sources remain in source/run state—there is no unclaimed-source queue.

Exact evidence shapes, summary gates, correction limit, publication precision, frontmatter types, source events, and route transitions belong to the core assets and `atlas-source` owner.

## Topic lifecycle

Topic-shell creation is deterministic index mutation, not synthesis. It creates or confirms one topic under an existing domain/subdomain, with exactly topic index → subdomain projection → topic registry targets. Initial values and confirmation compatibility are defined by the core registry contract. It creates no research pass, source, relation, vocabulary, domain, or subdomain.

`RELATIONS.md` is canonical for pending evidence; `TOPICS.md` is a derived lookup cache:

```text
current --pending edge--> dirty --refresh starts--> refreshing
refreshing --success and no pending edges--> current
refreshing --failure with pending edges--> blocked
current|dirty|blocked --explicit retirement--> archived
```

- Dirty count, pending edge IDs, newest pending source sequence, and source watermark are recomputed from valid persisted relations; never increment caches blindly.
- Refresh binds one complete pending edge set. It writes one pass, patches managed topic sections, applies that same set, and recomputes caches. Partial failure preserves pending work and reaches `blocked`, never false completion.
- Research is vault-only unless acquisition is explicit. Source evidence must be materialized before synthesis.
- Answer reads `TOPICS.md` first and reads answer content only when freshness is `current`; automatic refresh-before-answer is not implicit.
- Subdomain topic maps and coverage buckets are projections of `TOPICS.md` plus topic frontmatter, never authority.

Topic folders start with `INDEX.md` and `passes/`. Add linked `SOURCES.md` around 25–40 evidence rows, `DECISIONS.md` after more than three decision branches, or `HISTORY.md` after roughly ten recent changes. Readers enter through the topic index.

## Migration and extension

- Schema changes are explicit, versioned migrations with old/new shape, exact target scope and revisions, preservation rules, deterministic verification, and rollback authority fixed before writes.
- The selected `atlas-migrate` owner reads and hashes only declared targets, validates old and candidate state, and applies approved bytes through `vault.conditional_replace`. It uses `state.reduce` only when a contract-defined event already owns the change.
- When no transaction contract applies, migration uses the approved artifact-by-artifact rollback boundary; conflict or incomplete rollback halts rather than force-writing.
- Preserve user content and unmanaged sections. Prefer additive, row-by-row, or artifact-by-artifact changes.
- Update affected scaffold shapes, contracts, owners, and checks with the migration; never re-seed living state.
- SQLite, FTS, vector indexes, schedulers, self-healing mutation, or a new canonical store require an explicit architecture decision and deterministic rebuild or rollback.

After changing this product-owned contract, sync only the intended bound instance with `python3 scripts/atlas-instance.py sync-framework --name <id>`, then run `python3 scripts/atlas-instance.py check --name <id>`. Obtain separate approval before a non-development profile write.

## Design posture

Prefer readable Markdown state transitions over hidden optimization. Keep the public surface singular, owner boundaries narrow, deterministic mechanics centralized, provenance durable, and implementation details replaceable.
