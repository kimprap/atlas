---
description: Atlas product package — harness map, ownership, and working conventions.
alwaysApply: true
---

# Atlas app

Product package for the Atlas research framework: agent skills, one slash command, deterministic Markdown contracts, an empty vault scaffold, instance provision, and deployable runtime.

Living research is not in this repository. It lives in a bound instance reached only through logical `vault://atlas/…` paths and the active connector profile. The same product skills and contracts apply in every supported runtime; only the connector profile changes.

## Ownership

| Surface | Role |
|---|---|
| This product package | Author skills, command, contracts, `.agents/ARCHITECTURE.md`, `scaffold/`, provision tooling, and runtime code. |
| Bound instance (`vault://atlas/…`) | Living sources, registries, topics, passes, and product-owned framework snapshots. |
| `scaffold/` | Seed-once empty templates only; never product bodies or living rows. |

- Canonical framework contract: `.agents/ARCHITECTURE.md`. The instance copy is a product-owned snapshot updated through `sync-framework` only with separate authority.
- Vault root: `vault://atlas/` only. Do not invent a second root.
- Harness surface stays under this package's `.agents/`. Do not put instance data, credentials, or connector secrets in product artifacts.
- Harness-discovered seam rules are `.agents/rules/atlas-boundaries.md`, `atlas-reducer-discipline.md`, and `atlas-skill-surface.md`.

## Contract discovery

Load only the narrow authority required before deciding or editing:

| Task | Required discovery |
|---|---|
| Change framework ownership, public entry, owner modes, write sets, canonical state, deterministic runtime ownership, research eligibility, recovery, or migration | Read `.agents/ARCHITECTURE.md` first, then the owning artifact below. |
| Need accepted rationale for one of those decisions | Read `docs/adr/INDEX.md`, then only the matching row. |
| Work within an established seam | Read only its owning artifact; do not scan unrelated ADRs. |

ADRs explain why and never override `.agents/ARCHITECTURE.md`. When durable invariants change, update architecture → core contracts → front door/owners → command stub, then separately sync only intended bound instances if authorized.

## Layout

```text
.agents/
  AGENTS.md
  ARCHITECTURE.md                 canonical framework contract
  rules/                          ownership and front-door seams
  commands/atlas-ask.md           sole byte-thin public command
  skills/atlas-ask/SKILL.md       sole public classifier
  skills/atlas-ask/owners/        exactly three internal owner resources
  skills/atlas-core/              hidden contracts and CLI recipes
  plans/
scaffold/                          seed-once templates and manifest
scripts/atlas-instance.py         separate provision/sync/check CLI
scripts/atlas_cli.py              strict shared JSON/envelope/exit seam
scripts/atlas_tool.py             generated façade CLI and operation catalog
scripts/atlas_connector.py        profile binding and logical I/O
scripts/atlas_state.py            registry validation, reduction, inspection
scripts/atlas_source.py           capture normalization and source/route projection
scripts/atlas_research.py         research publication and recovery
scripts/atlas_transaction.py      generic transaction and recovery
```

Do not store instances or living research here. Add another runtime/library tree only when real code requires it.

## Source of truth

| Concern | Where |
|---|---|
| Framework invariants | `.agents/ARCHITECTURE.md` |
| Accepted rationale lookup | `docs/adr/INDEX.md` → matching ADR only |
| Reducers and workflow contracts | `.agents/skills/atlas-core/assets/` |
| Agent operation sequences and lifecycle command map | `.agents/skills/atlas-core/assets/agent-cli-recipes.md` |
| Reference domain behavior | `scripts/atlas_state.py`, `atlas_source.py`, `atlas_research.py`, `atlas_transaction.py` |
| Front-door classification | `.agents/skills/atlas-ask/SKILL.md` |
| Workflow procedures | `skill://atlas-ask/owners/<owner-id>/OWNER.md` |
| Thin command wrapper | `.agents/commands/atlas-ask.md` |
| Cross-cutting seams | `.agents/rules/` |
| Instance architecture snapshot | `vault://atlas/ARCHITECTURE.md` |

## Agent façade

Discover lifecycle operations with:

```text
python3 scripts/atlas_tool.py capabilities
python3 scripts/atlas_tool.py capabilities --all
```

The default view exposes lifecycle operations. `--all` additionally exposes internal primitives and their audience; audience affects discovery, never authority. Family commands consume one operation-args object from `--input -` or a UTF-8 file. Low-level `call --input` consumes exactly `{"version":2,"op":"<literal>","args":{…}}`.

Machine stdout is canonical UTF-8 JSON plus one LF. Every response has exactly `version`, `ok`, `op`, `disposition`, `result`, `findings`, and `recovery`. Use `agent-cli-recipes.md`; never call runtime owners directly or derive connector paths, revisions, canonical projections, transaction effects, or recovery in agent prose.

## Public entry and owners

`/atlas-ask <plain-language intent>` is the sole public Atlas behavior entry. It classifies one request and loads exactly one internal owner in the same agent:

| Owner | Modes |
|---|---|
| `atlas-source` | `presence`, `ingest`, `resummarize`, `promote`, `reroute` |
| `atlas-research` | `answer`, `research`, `refresh`, `create` |
| `atlas-maintain` | `audit`, `repair`, `migrate` |

Read-only `presence`, `answer`, and `audit` dispatch without approval. Every write-capable mode receives one unchanged Goal/Effect approval before owner load. Migration preview and commit are separate invocations with separate candidate-bound approval.

Owners execute end-to-end and return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`. Route, refresh, and topic-create procedures run in process inside the selected owner; do not create helper-owner chains. Missing delegation facilities never block same-agent execution.

`skill://atlas-core` is hidden support-only. Direct use permits repository inspection but performs no Atlas/profile/vault/façade I/O and redirects to `/atlas-ask`. Users never invoke owner resources directly. Do not add direct owner commands, public aliases, compatibility workflows, automatic audit/verify/repair loops, or a second Atlas root.

## Provision

```bash
python3 scripts/atlas-instance.py create --name <id>
python3 scripts/atlas-instance.py sync-framework --name <id>   # or --all
python3 scripts/atlas-instance.py check
```

`create` seeds an empty instance. `sync-framework` overwrites product-owned files only and never re-seeds living state. Schema changes on living instances use `/atlas-ask` with an explicit versioned migration intent and separate effect authority.

## Working conventions

- Make surgical changes and preserve established contracts.
- Keep the command stub byte-thin; put classification in `/atlas-ask`, procedures in the three owners, and determinism in `atlas-core` plus runtime code.
- Use logical vault paths and the active connector; never resolve a host tree in skills.
- Smoke fixtures are temporary. Remove every row, artifact, receipt, and empty directory before completion.
- Ask separately before deploy, credentials, non-development profile writes, bound-instance sync, or destructive registry repair.

## Temporary stale-plan gate

After this cutover, do not execute either plan identity:

- `2026-07-29-2056_atlas-evaluation-loop`
- `2026-08-02-1332_atlas-topic-creation`

Each remains blocked until its authoritative local artifact is revised against current architecture and owner paths, explicitly reapproved, and reconciled to its repository projection by `plan-artifact-sync`. That approved plan may then remove only its own identity from this gate. Never hand-edit pending repository projections.

## Surface checks

- One public Atlas behavior skill and one raw-argument-preserving command.
- Exactly three internal owner resources with the mode map above.
- `atlas-core` hidden and direct use readless/write-free.
- Version-2 CLI envelope and recipe operation literals aligned with the generated catalog.
- No removed owner paths, provider aliases, helper-owner chains, or direct domain CLI workflows.
- `scaffold/` remains seed-once and contains no living rows or product-owned bodies.
- Contracts and skills use `vault://atlas/…` plus the active connector.