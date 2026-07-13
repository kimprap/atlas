---
description: Atlas product package — harness map, ownership, and working conventions.
alwaysApply: true
---

# Atlas app

Product package for the Atlas research framework: agent skills, slash commands, Markdown reducer contracts, vault scaffold, instance provision, and deployable runtime.

Living research state is **not** in this repo. It lives on a **bound instance** and is reached only via logical `vault://atlas/…` paths through the active connector/profile. The same skills must work for local agents, CI, and serverless runtimes — only the connector profile changes.

## Ownership (short)

| Surface | Role |
|---|---|
| This product package | Author skills, commands, contracts, `.agents/ARCHITECTURE.md`, `scaffold/`, provision tooling |
| Bound instance (`vault://atlas/…`) | Living sources, registries, topics, passes |
| `scaffold/` | Seed-once empty templates only — never product bodies or living rows |

- Canonical framework contract: `.agents/ARCHITECTURE.md`. The instance copy is a product-owned snapshot updated through `sync-framework`.
- Vault root: `vault://atlas/` only. Do not invent a second root (e.g. `vault://digest/`).
- Harness surface stays under this package's `.agents/`. Do not ship instance data in deploy artifacts.

Seam details: `.agents/rules/atlas-boundaries.md`, `atlas-reducer-discipline.md`, `atlas-skill-surface.md`.

## Layout

```text
.agents/
  AGENTS.md          # this file
  ARCHITECTURE.md    # product-owned framework contract (author here)
  rules/             # ownership / freestyle / skill-surface seams
  commands/          # thin /atlas-* stubs → skill://…
  skills/            # entry skills + atlas-core contracts
  plans/
scaffold/            # seed-once templates + MANIFEST
scripts/atlas-instance.py
```

Do not store instances or living research here. Add a runtime/library tree only when real code needs it.

## Source of truth

| Concern | Where |
|---|---|
| Framework invariants | `.agents/ARCHITECTURE.md` |
| Deterministic reducers | `.agents/skills/atlas-core/assets/` |
| Workflow checklists | `.agents/skills/atlas-*/` |
| Thin command stubs | `.agents/commands/` |
| Cross-cutting seams | `.agents/rules/` |
| Instance architecture snapshot | `vault://atlas/ARCHITECTURE.md` (synced) |

When durable invariants change: **architecture → contracts → owning skill(s) → command stub**, then `sync-framework` if product-owned content changed.

## Entrypoints

| Entrypoint | Role |
|---|---|
| `atlas-source` | Explicit URL/file ingestion |
| `atlas-acquire` | Bounded discovery |
| `atlas-route` | Route status, relations, dirty cache |
| `atlas-research` | Vault-only synthesis; acquisition only when explicit |
| `atlas-refresh` | Dirty → current via one dated pass |
| `atlas-answer` | Freshness-gated read |
| `atlas-audit` | Read-only health |
| `atlas-index` | Vocab/topic promotion and repair |
| `atlas-migrate` | Explicit schema migration |

Prefer the matching `/atlas-*` (or `skill://…`) over freestyle vault mutation. Procedures live in skills; freestyle write-set limits live in rules.

## Provision

```bash
python3 scripts/atlas-instance.py create --name <id>
python3 scripts/atlas-instance.py sync-framework --name <id>   # or --all
python3 scripts/atlas-instance.py check
```

`create` seeds an empty instance; `sync-framework` overwrites **product_owned only**; living content is never re-seeded. Schema changes on living instances use `/atlas-migrate`.

## Working conventions

- Surgical changes. Prefer Conventional Commits (`feat(atlas): …`, `fix(route): …`).
- Keep command stubs thin; put checklists in skills and shared determinism in `atlas-core`.
- Smoke fixtures are temporary — remove before done; leave no verification rows on a bound instance.
- Ask before deploy, credential use, non-dev profile writes, or destructive registry repair.

## Verification

- Entry skills and matching command stubs exist for each `/atlas-*`.
- `scaffold/` remains seed-once only (no living rows, no product_owned bodies).
- `python3 scripts/atlas-instance.py check` passes for bound instances.
- Contracts and skills assume `vault://…` + connector, not vault files at repo root.
