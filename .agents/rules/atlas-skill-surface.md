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

When invariants move:

1. `.agents/ARCHITECTURE.md`
2. `atlas-core` contracts (`.agents/skills/atlas-core/assets/`)
3. Owning entry skill(s)
4. Thin command stub (`.agents/commands/`)

If product_owned architecture changed: `python3 scripts/atlas-instance.py sync-framework` then `check`.

## Surface shape

- Commands: thin wrappers (`skill://…` + args) — no full checklists in command files.
- Checklists live in entry skills; shared determinism in `atlas-core` only.
- `atlas-core` is support-only (not a user entrypoint).
- Keep `digest` as a compatibility shim; do not expand it into a second workflow stack or second vault root.
- New behavior needs an architecture mode/write-set note (or explicit migration), not only a skill bullet.
- Entry skills keep smoke-fixture cleanup; never leave verification rows in a bound instance.
- Skills and contracts depend on logical `vault://atlas/…` paths, not a fixed host tree.
- Phase 1: no ad hoc SQLite registry helpers under skills.

## Non-goals

- Artifact frontmatter catalogs → contracts/templates
- Harness transport / host agent install details
- Freestyle vault write-set discipline → `rule://atlas-reducer-discipline` (or `.agents/rules/atlas-reducer-discipline.md`)
- Product package vs instance ownership → `rule://atlas-boundaries`

## Activation checks

- **Positive:** “put the full route checklist in the slash command file”, “add `/atlas-foo` with only a skill bullet and no architecture note”, “add SQLite under atlas-index for Phase 1”
- **Near-miss:** “refresh a dirty topic via `/atlas-refresh`”, “typo in `.agents/ARCHITECTURE.md` prose only” (architecture edit still may need sync-framework; this rule is about skill/command surface shape)
