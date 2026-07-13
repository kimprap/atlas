---
description: Use when creating or editing Atlas skills, slash commands, or shared reducer contracts in this product package.
globs:
  - ".agents/skills/**"
  - ".agents/commands/**"
---

# Atlas skill surface

Portable product harness: the same skills and contracts must remain valid for local agents and remote/serverless runtimes. Environment only swaps the vault connector profile.

## Activation

**Apply when:** adding or changing entry skills, `atlas-core` contracts, or `/atlas-*` command stubs under this product's `.agents/`.

**Do not apply when:** living vault content work, instance provision only, or host-global agent config outside this product package.

## Change order

When an invariant or write set changes:

1. `.agents/ARCHITECTURE.md`
2. `atlas-core` contracts (`.agents/skills/atlas-core/assets/`)
3. Owning entry skill(s)
4. Thin command stub (`.agents/commands/`)

If product-owned architecture changed, sync the intended bound instance(s), then run `python3 scripts/atlas-instance.py check`; obtain any required approval before a non-development profile write.

## Surface shape

- Commands: thin wrappers (`skill://…` + args) — no full checklists in command files.
- Checklists live in entry skills; shared determinism in `atlas-core` only.
- `atlas-core` is support-only (not a user entrypoint).
- Do not reintroduce a compatibility workflow stack or a second vault root.
- A new mode, write target, state transition, or invariant needs an architecture or migration change; a skill bullet alone cannot establish it.
- Any skill that creates smoke fixtures must specify cleanup; never leave verification rows in a bound instance.
- Skills and contracts use logical `vault://atlas/…` paths, not a fixed host tree.
- Do not add a parallel registry backend or storage helper outside explicit architecture and migration work.

## Non-goals

- Artifact frontmatter catalogs → contracts/templates
- Harness transport / host agent install details
- Freestyle vault write-set discipline → `rule://atlas-reducer-discipline` (or `.agents/rules/atlas-reducer-discipline.md`)
- Product package vs instance ownership → `rule://atlas-boundaries`

## Activation checks

- **Positive:** “put the full route checklist in the slash command file”, “add a new write target only to a skill”, “add a second registry backend inside atlas-index”
- **Near-miss:** “refresh a dirty topic via `/atlas-refresh`”, “typo in `.agents/ARCHITECTURE.md` prose only” (architecture edit still may need sync-framework; this rule is about skill/command surface shape)
