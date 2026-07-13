# Improvement Plan: Decouple legacy assets and harden Atlas maintenance

**Datetime**: 2026-07-12-2346
**Mode**: standard
**Scope**: Active Atlas package documentation, skill assets, and instance-provision safety
**Summary**: Move shared Atlas templates into `atlas-core`, remove the legacy `digest` skill after migrating every active caller, align active guidance with the refined architecture, remove the approved temporary research handoff, and add focused provision safety coverage. Preserve archived plans as historical records.
**Status**: DONE

## Findings

- `.agents/skills/digest/assets/` — `source-summary-template.md` and `research-library-templates.md` are shared Atlas product contracts, but six active Atlas skills load them through the legacy compatibility shim. Move both assets under `atlas-core`, update live `skill://` references, then remove `.agents/skills/digest/` entirely as approved by the user.
- `README.md:3-14,34,67-73,106`, `.agents/AGENTS.md:31,55-68`, and `.agents/rules/atlas-skill-surface.md:34` — stale “future”/“SO” wording and live `digest` compatibility guidance remain, and the README links to the removed `ARCHITECTURE.md#slash-commands` heading. Remove the retired entrypoint and point the write-set link to `#mode-ownership`.
- `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md:11,19-27`, `.agents/skills/atlas-index/SKILL.md:30`, and `.agents/skills/atlas-migrate/SKILL.md:17-21` — phase-number wording, a hard-coded future script path, and unconditional `sync-framework --all` conflict with the new durable architecture and non-development write-approval boundary.
- `scripts/atlas-instance.py:87-99` — `create` makes the destination before all manifest sources are preflighted, so a missing or malformed source can leave a partial instance that blocks retry. No focused provision tests currently exist.
- `temp-agentic-harness.md` — tracked, unreferenced, 1,600+ line research handoff at the product root. The user approved its removal from this product package.

## Scope

**In scope**:
- `.agents/skills/atlas-core/`
- Active `.agents/skills/atlas-{source,acquire,research,refresh,index,migrate}/SKILL.md`
- `.agents/skills/digest/` removal after asset migration
- `README.md`, `.agents/AGENTS.md`, `scaffold/README.md`
- `.agents/rules/atlas-boundaries.md`, `.agents/rules/atlas-skill-surface.md`
- `scripts/atlas-instance.py`
- `tests/test_atlas_instance.py`
- `temp-agentic-harness.md` removal

**Out of scope**:
- `.agents/plans/archive/` — historical references must remain unchanged.
- Bound-instance living rows and seed-once content — tests use temporary roots only.
- New storage backends, schema migrations, runtime deployment, or workflow behavior.

## Execution intent

When complete, `atlas-core` owns every shared Atlas template; no active skill, rule, command, or user-facing document exposes `/digest` or depends on `.agents/skills/digest/`; active guidance uses durable architecture boundaries; failed instance creation leaves no partial destination; and the temporary research handoff is absent from the product repository.

## Critical anchors

- `.agents/ARCHITECTURE.md` — ownership, write-set, freshness, and migration invariants.
- `.agents/skills/atlas-core/SKILL.md` — support-skill asset router.
- `.agents/rules/atlas-skill-surface.md` — thin command and shared-contract ownership.
- `scaffold/MANIFEST.json` — current manifest shape and ownership classes; do not change its schema.
- `scripts/atlas-instance.py::{load_manifest,cmd_create,cmd_sync_framework,cmd_check}` — provision behavior under test.
- `.agents/plans/archive/` — immutable historical record; stale historical paths are allowed there.

## Implementation decisions

- Move both template files without changing their content unless a migrated link requires it.
- Remove the entire `digest` skill only after every active template caller resolves through `atlas-core`.
- Keep `vault://digest/` prohibitions where they protect the single-root invariant; remove only the retired `/digest` command/skill surface.
- Use stdlib `unittest`, `tempfile`, and `unittest.mock`; add no dependency or test framework.
- Validate the current manifest shape and safe relative paths without publishing a new manifest schema.
- Delete `temp-agentic-harness.md`; do not move its research into the bound instance.

## Tasks

- [x] T1. Move `source-summary-template.md` and `research-library-templates.md` from `.agents/skills/digest/assets/` to `.agents/skills/atlas-core/assets/`; update every active template reference in `atlas-core`, source, acquire, research, refresh, and index skills; leave archived plans untouched.
  completed 2026-07-13-0011
- [x] T2. Remove `.agents/skills/digest/` and every active `/digest` entrypoint or compatibility-shim reference; repair the README architecture anchor and stale terminology; replace phase-specific and hard-coded future-path language with durable architecture/migration boundaries; make migration synchronization target explicit instance names and require approval before non-development writes; fix the missing section break in `atlas-acquire`; delete `temp-agentic-harness.md`.
  completed 2026-07-13-0017
- [x] T3. Preflight manifest entry shape, relative paths, and all source/template existence before `cmd_create` creates its destination. Add dependency-free `unittest` coverage for successful create, existing-instance rejection, invalid names/paths, product-owned-only sync, drift detection, and failure without a partial destination.
  completed 2026-07-13-0016
- [x] T4. Run focused tests and Atlas checks; search active files for stale legacy skill/asset references, broken architecture anchors, phase-only restrictions, and unconditional `sync-framework --all`; inspect the final in-scope diff and preserve all unrelated current work.
  completed 2026-07-13-0018

## Verification / Done criteria

- [x] `python3 -m unittest discover -s tests -p 'test_*.py'` exits 0.
- [x] `python3 scripts/atlas-instance.py check` exits 0; any required non-development snapshot write is separately approved before synchronization.
- [x] A content search outside `.agents/plans/archive/` finds no `skill://digest`, `.agents/skills/digest`, retired `/digest` entrypoint guidance, `#slash-commands`, `authoring SO`, `framework SO`, `in this phase`, or unconditional `sync-framework --all` guidance.
- [x] `.agents/skills/digest/` and `temp-agentic-harness.md` are absent; shared Atlas templates resolve from `skill://atlas-core/assets/`.
- [x] Provision tests prove that a failed create leaves no destination directory and that sync does not overwrite seed-once state.
- [x] `git status --porcelain` reports only the pre-existing reviewed changes plus files explicitly named by T1-T3.

## STOP conditions

- An active caller outside the listed skills depends on the physical `digest/assets` paths and cannot migrate in the same change.
- Manifest preflight requires changing the published manifest schema rather than validating its current shape.
- Verification would write a non-development bound instance without explicit approval.

## Completion Summary

- T1 moved both shared templates into `atlas-core` and migrated every active caller; archived plans retain historical paths.
- T2 removed the legacy `digest` skill, retired entrypoint guidance, stale phase/path wording, and the broken architecture anchor. `temp-agentic-harness.md` was restored afterward at the user's direction for separate handling.
- T3 added manifest preflight, safe relative-path validation, transactional create cleanup, and eight dependency-free provision behavior tests.
- T4 verified tests, bound-instance consistency, active-reference cleanup, file layout, and diff hygiene.
- Residual risk: none identified in the executed scope; alternative storage, deployment, and living-instance migration remain explicit future decisions.
- Outcome: Atlas now has one primary skill surface, shared contracts under `atlas-core`, durable maintenance guidance, and tested provision safety.
