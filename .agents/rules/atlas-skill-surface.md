---
description: Use when creating or editing Atlas skills, slash commands, owner resources, or shared reducer contracts in this product package.
globs:
  - ".agents/skills/**"
  - ".agents/commands/**"
---

# Atlas skill surface

The same front door, owner resources, recipes, and contracts apply in every supported runtime. Environment changes only the active connector profile.

## Activation

**Apply when:** changing `/atlas-ask`, one of its three internal owner resources, `atlas-core` contracts, or the thin command wrapper under this product's `.agents/`.

**Do not apply when:** executing living vault work through a selected owner, provisioning an instance only, or changing host-global agent configuration outside this product package.

## Change order

When an invariant or write set changes:

1. `.agents/ARCHITECTURE.md`
2. `.agents/skills/atlas-core/assets/`
3. `.agents/skills/atlas-ask/SKILL.md` and its owner resources
4. `.agents/commands/atlas-ask.md`

If product-owned architecture changed, sync only separately approved intended instances and run the instance check. Product-package approval never authorizes a bound-instance write.

## Surface shape

- `.agents/commands/atlas-ask.md` is the only public Atlas command. It is a byte-thin `skill://atlas-ask` wrapper, preserves raw arguments, and contains no workflow checklist.
- `/atlas-ask` is the only public Atlas behavior skill and sole classifier. It maps one request to one exact owner plus mode.
- Read-only source `presence|answer`, research `answer`, and maintain `audit` dispatch without approval. Every write-capable mode gets one unchanged Goal/Effect approval before owner load.
- The same agent loads exactly one internal owner resource: `atlas-source`, `atlas-research`, or `atlas-maintain`. Missing delegation facilities never stop execution.
- Route, refresh, and topic-create procedures run in process inside the selected owner; never create or load helper-owner resources.
- The front door performs no Atlas semantic, façade, profile, vault, reducer, projection, transaction, or recovery work and never reconstructs a missing result.
- `atlas-core` is hidden support-only. Direct use permits repository inspection but performs no Atlas/profile/vault/façade I/O and redirects to `/atlas-ask`.
- Owner resources use `agent-cli-recipes.md`, the generated operation catalog, the version-2 machine envelope, and the seven-field owner result.
- Do not add direct owner commands, aliases, compatibility workflows, unqualified owner loads, or a second vault root.
- Checklists live in the front door and owner resources; shared determinism lives in `atlas-core` assets and runtime modules.
- A new mode, write target, state transition, or invariant requires an architecture or migration change; a skill bullet alone cannot establish it.
- Any workflow-created smoke fixture must be removed; never leave verification rows in a bound instance.
- Skills and contracts use logical `vault://atlas/…` paths, not a fixed host tree.
- Never add an automatic audit/verify/repair loop, parallel registry backend, or storage helper outside explicit architecture and migration authority.

## Non-goals

- Artifact frontmatter catalogs → contracts and templates
- Host agent installation details
- Freestyle vault write-set discipline → `rule://atlas-reducer-discipline`
- Product package versus instance ownership → `rule://atlas-boundaries`

## Activation checks

- **Positive:** “put the route procedure in the slash command”, “add a fourth owner for answers”, “add a new write target only to an owner resource”
- **Near-miss:** “run refresh mode through `/atlas-ask`”, “fix architecture prose without changing the skill surface”