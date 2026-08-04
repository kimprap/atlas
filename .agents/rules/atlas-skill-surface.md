---
description: Use when creating or editing Atlas skills, slash commands, or shared reducer contracts in this product package.
globs:
  - ".agents/skills/**"
  - ".agents/commands/**"
---

# Atlas skill surface

Portable product harness: the same front door, owner resources, and contracts remain valid for local agents and remote/serverless runtimes. Environment only swaps the vault connector profile.

## Activation

**Apply when:** adding or changing the `/atlas-ask` entry skill, its ordinary internal Workflow Owner resources, `atlas-core` contracts, or the thin command wrapper under this product's `.agents/`.

**Do not apply when:** living vault content work, instance provision only, or host-global agent config outside this product package.

## Change order

When an invariant or write set changes:

1. `.agents/ARCHITECTURE.md`
2. `atlas-core` contracts (`.agents/skills/atlas-core/assets/`)
3. The `/atlas-ask` front door and internal owner resources
4. Thin `.agents/commands/atlas-ask.md` wrapper

If product-owned architecture changed, sync the intended bound instance(s), then run `python3 scripts/atlas-instance.py check`; obtain any required approval before a non-development profile write.

## Surface shape

- The only public Atlas command is `.agents/commands/atlas-ask.md`: a thin `skill://atlas-ask` wrapper that preserves raw arguments and contains no workflow checklist.
- `/atlas-ask` is the only public Atlas behavior skill. The nine stable owner IDs are ordinary `skill://atlas-ask/owners/<owner-id>/OWNER.md` resources loaded only by a qualified Workflow Owner Task or allowlisted same-agent Successor Owner call.
- `atlas-core` is hidden support-only. Direct use permits repository inspection but performs no Atlas/profile/vault/façade I/O and redirects to `/atlas-ask`.
- Do not add direct owner commands, aliases, compatibility workflows, unqualified owner loads, or a second vault root.
- Checklists live in the front door and owner resources; shared determinism lives in `atlas-core` only.
- A new mode, write target, state transition, or invariant needs an architecture or migration change; a skill bullet alone cannot establish it.
- Any workflow that creates smoke fixtures must specify cleanup; never leave verification rows in a bound instance.
- Skills and contracts use logical `vault://atlas/…` paths, not a fixed host tree.
- Do not add a parallel registry backend or storage helper outside explicit architecture and migration work.

## Non-goals

- Artifact frontmatter catalogs → contracts/templates
- Harness transport / host agent install details
- Freestyle vault write-set discipline → `rule://atlas-reducer-discipline` (or `.agents/rules/atlas-reducer-discipline.md`)
- Product package vs instance ownership → `rule://atlas-boundaries`

## Activation checks

- **Positive:** “put the full route checklist in the slash command file”, “add a new write target only to an owner resource”, “add a second registry backend inside an owner”
- **Near-miss:** “run a refresh intent through `/atlas-ask`”, “typo in `.agents/ARCHITECTURE.md` prose only” (architecture edits may still require framework snapshot sync; this rule governs the skill/command surface)
