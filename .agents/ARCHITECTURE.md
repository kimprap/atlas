---
schema_version: 1
note_type: atlas-architecture
managed_by: atlas
last_updated: 2026-07-14
---

# Atlas Architecture

Atlas turns source evidence into durable Markdown artifacts, routes evidence to research topics, and refreshes topic answers through explicit, auditable state transitions. Vault content remains editor-friendly; every runtime reaches it through logical `vault://atlas/…` paths and the active connector profile.

This is the canonical framework contract. Author it only at `.agents/ARCHITECTURE.md`; `vault://atlas/ARCHITECTURE.md` is a product-owned instance snapshot. Read it before changing framework boundaries, state transitions, or workflow write sets.

## Contract ownership

Each concern has one primary owner:

| Concern | Canonical owner |
|---|---|
| Framework boundaries, invariants, modes, and freshness model | This file |
| Product-owned, seed-once, and never-touch provision classes | `scaffold/MANIFEST.json` |
| Registry schemas, source identity, reducer inputs/outputs, and legal transitions | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` |
| Operating cadence and automation guardrails | `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md` |
| End-to-end workflow procedures | Owning `.agents/skills/atlas-*/SKILL.md` |
| User-facing command dispatch | Thin `.agents/commands/atlas-*.md` stubs |

This file owns durable intent; specialized contracts own mechanics. Do not duplicate full schemas or checklists here. When an invariant changes, update this file first, then every affected contract, template, skill, and command in the same change.

## Product and instance boundary

| Class | Examples | Ownership |
|---|---|---|
| **product_owned** | `.agents/ARCHITECTURE.md` → instance `ARCHITECTURE.md` | Author in this package; `sync-framework` overwrites the instance snapshot. |
| **seed_once** | Empty registries, summary indexes, legacy `todos/` stub | Seed on instance creation; subsequent content is instance state. |
| **instance_owned** | Sources, runs, topics, passes, registries, editor config | Never re-seed; migrate living state explicitly. |

- The product package contains framework authoring surfaces, empty scaffold templates, provision tooling, and deployable runtime code.
- The bound instance contains living research state and is addressed only through `vault://atlas/…`.
- `scaffold/` contains empty-instance templates, not product bodies, real rows, runs, or topics.
- Provision bootstraps an instance; it is not application deployment. Deploy artifacts never contain instance research data.
- Do not hand-edit the instance architecture snapshot or copy framework trees into an instance.

## Framework invariants

- `vault://atlas/` is the only vault root. Do not create `vault://digest/` or another root.
- Host filesystem layout is not part of the contract; connector profiles provide storage portability.
- `vault://atlas/todos/` is legacy instance state. Preserve it unchanged and do not fold it into `summaries/`.
- Markdown registries are canonical. A different canonical store requires an explicit architecture and schema migration.
- Every managed artifact has `schema_version`, `note_type`, and `managed_by: atlas`.
- Source artifacts are evidence snapshots organized by acquisition/check time, not by a domain directory tree.
- A topic `INDEX.md` is the current answer contract; a research pass is provenance; a source artifact is evidence. These roles are not interchangeable.
- Research is vault-only unless the caller explicitly allows acquisition first; acquisition must materialize source artifacts before synthesis.
- Indexes and registries route work and summarize coverage. They do not duplicate full research bodies.
- Reducers patch managed sections and preserve user-owned content outside them.
- No workflow silently widens its write set or invents a parallel state convention.
- Routine source refresh and explicit `--resummarize` are distinct events. Resummarization is never implicit.
- Missing evidence is reported, not replaced with model priors.

## Instance shape

```text
vault://atlas/
├── ARCHITECTURE.md
├── todos/                         # legacy; preserve
└── summaries/
    ├── INDEX.md
    ├── domains/
    ├── sources/
    │   ├── INDEX.md
    │   ├── MANIFEST.md
    │   ├── runs/<YYYY>/<YYYY-MM>/
    │   └── artifacts/<YYYY>/<YYYY-MM>/
    ├── registry/
    │   ├── VOCAB.md
    │   ├── TOPICS.md
    │   └── RELATIONS.md
    └── research/<domain>/<subdomain>/
        ├── INDEX.md
        └── topics/<topic-slug>/
            ├── INDEX.md
            └── passes/
```

Do not pre-create domain files, subdomain/topic folders, optional topic split files, or `.atlas/`. Create them only for real state or an explicit migration.

## State and artifact roles

| Artifact | Role |
|---|---|
| Source manifest | Canonical source identity, dedupe, ordering, refresh, and route-status registry |
| Source artifact | Durable evidence snapshot for one canonical source |
| Acquisition run | Provenance for one bounded discovery run |
| Vocabulary registry | Canonical domains, subdomains, tags, source kinds, and aliases |
| Topic registry | Topic lookup and freshness cache |
| Relation registry | Canonical source-topic edge ledger |
| Subdomain index | Router and coverage map |
| Topic index | Current answer contract |
| Research pass | Dated synthesis or refresh provenance |

Artifacts, registries, relations, topics, passes, and run logs are both workflow state and audit trail. Do not maintain a parallel ephemeral queue for the same facts. Add a separate event log only if audits cannot be reconstructed from persisted artifacts.

## Reducer model

Atlas workflows follow:

```text
bounded state + one explicit event → bounded writes + persisted provenance
```

- Agents may propose structured route, relation, or delta decisions; deterministic contracts validate and apply them.
- Model output is a typed proposal, never an instruction to place Markdown rows or calculate cache fields.
- Each registry owns one canonical table: one exact header/separator followed by one immediately contiguous data-row region. A second header or schema-shaped row outside that region invalidates the complete registry; invalid rows contribute to neither routing nor freshness.
- Every route, refresh, and index mutation validates the complete input state, reduces one explicit event, validates the complete candidate state, and only then exposes changed documents plus exact input hashes for connector writes.
- Connector adapters own reads, optimistic hash checks, and writes only. Validation and reduction are provider-, harness-, model-, and storage-neutral.
- Freeform source prose may vary across conformant models. Accepted proposal shapes, state transitions, ordering, identities, findings, and gates are deterministic for identical input.
- Control flow belongs to slash-command workflows or an explicit scheduler. Hooks may enforce cheap deterministic guardrails but never run synthesis.
- Context reads stay bounded: registry rows and targeted artifacts before broad vault content.
- Managed sections are the only regions reducers may patch automatically:

```md
<!-- atlas:managed:start <section-name> -->
...
<!-- atlas:managed:end <section-name> -->
```

Whole-file rewrites are allowed only for empty or structurally broken managed artifacts. Registry reducers replace only canonical table data rows and preserve every byte of non-table prose, including newline convention and final-newline state.

## Mode ownership

| Mode | Allowed writes | Required boundary |
|---|---|---|
| Source ingestion | One source artifact, source manifest/index fields, route status | Explicit input; route every new or materially changed source; rewrite an existing generated summary only for explicit `--resummarize` |
| Acquisition | Source artifacts, manifest, one run log, route outputs | Bounded discovery only; never create vocabulary or topics |
| Route | Source route status, `RELATIONS.md`, derived dirty fields in `TOPICS.md` | Never write topic `INDEX.md` |
| Research | Topic `INDEX.md`, one pass, subdomain index, topic registry row | Vault-only by default; acquisition-first must be explicit |
| Refresh | One pass, managed topic sections, relation statuses, topic freshness cache | Apply persisted pending edges; preserve provenance on failure |
| Answer | Nothing | Read `TOPICS.md` first; answer only when the topic is `current` |
| Audit | Nothing by default | Repairs require an explicit index or migration workflow |
| Index / rollup | Explicit registry and index targets | Promotion and repair are intentional, conflict-checked operations |
| Migration | Versioned artifacts within the declared migration scope | Define old/new shape, rollback, and verification before writes |

If a workflow needs a new write target, change this contract or execute an explicit migration before changing the workflow.

## Source identity and routing

- Canonicalize each source before fetch, dedupe, and identity generation.
- Derive `source_id` from canonical identity and use the source manifest as the dedupe authority.
- Derive `content_hash` from readable source content.
- A routine unchanged refresh updates `last_checked` only; it does not rewrite the artifact or create a duplicate relation.
- Explicit `--resummarize` requires an existing canonical identity and newly fetched evidence. It may rewrite generated summary fields and body even when `content_hash` is unchanged, but it preserves `source_id`, `source_seq`, `canonical_url`, `first_seen`, `acquired_by`, `acquisition_run`, and the artifact path.
- Source semantic drafting consumes an explicit source-only evidence envelope: the newly fetched canonical payload, inspected pinned media, exact retrieval bounds, immutable identity/retrieval metadata needed by the artifact, and product-owned template/rubric versions. Old artifacts, taxonomy, topics, relations, plans, request/session text, repository context, and provider identity are not semantic evidence.
- Classification normalization and bounded routing occur only after the semantic draft passes. They may attach Atlas annotations but must not rewrite factual source claims.
- Resummarization updates `last_checked` and `last_summarized`, is never implicit, and re-runs bounded routing against the corrected artifact. It must not reopen a previously `applied` edge solely because summary prose changed.
- A new or materially changed source re-enters routing.
- Acquisition and source ingestion may record noncanonical phrases as `candidate_terms`; they never create canonical vocabulary, aliases, or topics.
- Routing uses registry-owned vocabulary and bounded verification. It writes relation edges and recomputes affected topic freshness fields; it does not synthesize topic answers.
- Unmatched sources remain recorded in source/run state. Do not create a global unclaimed-source queue.

Exact normalization, IDs, schemas, verifier output, and legal transitions belong to `atlas-core/assets/markdown-registry-contracts.md`.

## Freshness model

`RELATIONS.md` is canonical for pending source-topic work. `TOPICS.md` is a derived lookup cache:
Only rows inside the validated canonical relation table contribute to pending work. `TOPICS.md` never legitimizes an invalid or orphan relation row.

```text
current --pending edge--> dirty --refresh starts--> refreshing
refreshing --success, no pending edges--> current
refreshing --failure, pending edges remain--> blocked
current|dirty|blocked --explicit retirement--> archived
```

- A topic is dirty exactly when it has at least one pending relation edge.
- Recompute dirty count, pending edge IDs, newest pending source sequence, and source watermark from persisted relations; never increment caches blindly.
- Refresh persists one pass, patches managed topic sections, marks applied edges, then recomputes the topic cache.
- Partial refresh failure leaves unapplied edges pending and moves the topic to `blocked`; it never reports success from partial state.
- Refresh transitions are explicit reducer events: `refresh-start` requires the complete pending edge set; `refresh-complete` applies that same complete set and pass provenance; `refresh-fail` preserves pending edges and records `blocked`.
- Answer is freshness-gated. `dirty`, `refreshing`, and `blocked` topics halt with their state and pending-edge details.
- Automatic refresh-before-answer is not part of the current contract; adding it requires an explicit workflow decision.

## Topic growth

New topic folders contain only `INDEX.md` and `passes/`. Add optional files only when they materially improve scanability:

- `SOURCES.md` when the evidence map grows beyond roughly 25–40 rows.
- `DECISIONS.md` when more than three distinct decision matrices or recommendation branches are needed.
- `HISTORY.md` when recent changes exceed roughly ten entries; retain the latest three in `INDEX.md`.

Every split file must be linked from the topic index. Readers open the topic index first and follow only relevant links.

## Migration and extension policy

- Schema changes are explicit, versioned migrations. Define old shape, new shape, scope, rollback, and verification.
- Preserve user content and unmanaged sections; prefer additive, row-by-row or artifact-by-artifact migration.
- Update affected scaffold templates, contracts, skills, and checks with the migration.
- SQLite, FTS, vector indexes, scheduled synthesis, and self-healing mutation are not implicit extensions. Introduce them only through an explicit architecture decision with deterministic rebuild or rollback.
- Any later cache remains derived from canonical Markdown unless a migration explicitly changes canonical ownership.

After changing this product-owned contract, sync the intended bound instance snapshot with `scripts/atlas-instance.py sync-framework`, then run `scripts/atlas-instance.py check`. Obtain any required approval before writing a non-development profile.

## Design posture

Prefer readable Markdown state transitions over hidden optimization. Keep workflows narrow, provenance durable, files lean, and implementation details replaceable behind these contracts.
