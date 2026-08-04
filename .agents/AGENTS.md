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

## Conditional rationale

Architecture, product/instance-boundary, canonical-state, acquisition, or Engineering Cycle work reads `docs/adr/INDEX.md` and then only the matching ADRs. Ordinary sessions do not scan the index or ADR bodies; `.agents/ARCHITECTURE.md` remains normative.


## Layout

```text
.agents/
  AGENTS.md          # this file
  ARCHITECTURE.md    # product-owned framework contract (author here)
  rules/             # ownership / freestyle / skill-surface seams
  commands/          # one thin /atlas-ask stub → skill://atlas-ask
  skills/            # /atlas-ask behavior, internal owner resources, and atlas-core contracts
  plans/
  memory/          # provisional memory draft, workflow, index, and raw tmp inputs
scaffold/            # seed-once templates + MANIFEST
scripts/atlas-instance.py  # provision/sync + living-state check
scripts/atlas_tool.py      # provider-neutral façade CLI: capabilities / call
scripts/atlas_connector.py # connector/profile owner beneath the façade
scripts/atlas_url.py       # canonical URL normalization owner
scripts/atlas_discovery.py # bounded discovery normalization owner
scripts/atlas_quality.py   # source proposal, summary, and calibration owner
scripts/atlas_state.py     # registry validation and reduction owner
scripts/atlas_source.py    # source rendering, merge, and route-artifact owner

Do not store instances or living research here. Add a runtime/library tree only when real code needs it.

## Source of truth

| Concern | Where |
|---|---|
| Framework invariants | `.agents/ARCHITECTURE.md` |
| Deterministic reducers | `.agents/skills/atlas-core/assets/` |
| Reference registry reducer | `scripts/atlas_state.py` |
| Reference source-quality validator | `scripts/atlas_quality.py` |
| Workflow checklists | `.agents/skills/atlas-ask/SKILL.md` and `skill://atlas-ask/owners/<owner-id>/OWNER.md` resources |
| Thin command wrapper | `.agents/commands/atlas-ask.md` |
| Cross-cutting seams | `.agents/rules/` |
| Instance architecture snapshot | `vault://atlas/ARCHITECTURE.md` (synced) |

When durable invariants change: **architecture → contracts → owning skill(s) → command stub**, then `sync-framework` if product-owned content changed.

## Agent tools

Use `scripts/atlas_tool.py capabilities` to inspect the active qualified surface and `call --input <path|->` for deterministic work. It accepts only the version-1 envelope. Agents retain fetch/search, user clarification, bounded semantic decisions, model drafting, and checklists; they pass typed results into the façade. They do not invoke its owners directly or derive connector paths, revisions, or transaction effects.

| Family | Operations |
|---|---|
| Vault façade | `vault.read`, `vault.read_json`, `vault.list`, `vault.hash`, `vault.write_json`, `vault.conditional_replace`, `vault.digest_tree`, `vault.delete_tree` |
| Identity / discovery façade | `url.normalize`, `url.resolve_reference`, `discovery.normalize` |
| Quality façade | `quality.validate_proposal`, `quality.validate_summary`, `quality.prepare_calibration`, `quality.validate_calibration`, `quality.validate_fresh_assessment` |
| State / source façade | `state.validate`, `state.reduce`, `source.render_summary`, `source.merge_artifact`, `source.render_route_artifact`, `source.lookup`, `source.inventory`, `source.worker_schema`, `source.prepare`, `source.snapshot_active` |
| Effect façade | `transaction.execute`, `transaction.recover`, `transaction.successor`, `refresh.execute`, `refresh.recover` |

## Entrypoints

| Entrypoint | Role |
|---|---|
| `/atlas-ask <plain-language intent>` | Sole public Atlas behavior entry; classifies one bounded goal, obtains material choices and route approval, dispatches one strict Workflow Owner Task, and consumes one aggregate result. |
| `skill://atlas-ask/owners/<owner-id>/OWNER.md` | Ordinary internal Workflow Owner resource, loadable only through a qualified selected Task or allowlisted same-agent Successor Owner call. |
| `skill://atlas-core` | Hidden support-only contracts and façade reference; direct use permits repository inspection but no Atlas/profile/vault/façade I/O and redirects to `/atlas-ask`. |

Use `/atlas-ask` for every Atlas intent. Users do not invoke direct owner commands or owner resources; the front door preserves each owner's native write set, recovery, and internal chain.

The thin command wrapper preserves raw arguments and the strict aggregate result remains the only front-door result boundary. Non-Atlas repository, code, configuration, and shell work remains outside Atlas.

## Provision

```bash
python3 scripts/atlas-instance.py create --name <id>
python3 scripts/atlas-instance.py sync-framework --name <id>   # or --all
python3 scripts/atlas-instance.py check
```

`create` seeds an empty instance; `sync-framework` overwrites **product_owned only**; living content is never re-seeded. Schema changes on living instances use `/atlas-ask` with the explicit migration intent.

## Working conventions

- Surgical changes. Prefer Conventional Commits (`feat(atlas): …`, `fix(route): …`).
- Keep command stubs thin; put checklists in skills and shared determinism in `atlas-core`.
- Smoke fixtures are temporary — remove before done; leave no verification rows on a bound instance.
- Ask before deploy, credential use, non-dev profile writes, or destructive registry repair.

## Temporary stale-plan gate

After this cutover, do not execute any of these plan identities:

- `2026-07-29-2056_atlas-evaluation-loop`
- `2026-08-02-1332_atlas-topic-creation`
- `2026-08-02-1456_repo-agent-memory-first-draft`

Each named plan remains blocked until its authoritative local artifact is revised against the current architecture and owner paths, explicitly reapproved, and reconciled to its repository projection by `plan-artifact-sync`. That approved plan may then remove only its own identity from this gate. Never hand-edit the pending repository projections.

## Verification

- `/atlas-ask` is the sole public Atlas behavior and has one thin argument-preserving command wrapper.
- Nine Workflow Owner IDs remain ordinary internal resources; no direct owner commands, aliases, or top-level owner skills are active.
- `atlas-core` remains hidden support-only and direct use performs no Atlas I/O.
- `scaffold/` remains seed-once only (no living rows, no product_owned bodies).
- `python3 scripts/atlas-instance.py check` passes for bound instances.
- Contracts and skills assume `vault://atlas/…` plus the active connector, not vault files at repository root.
