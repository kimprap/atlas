# Improvement Plan: Refine Atlas and run the first deliberate tranche

**Datetime**: 2026-07-29-2356
**Mode**: standard
**Scope**: Source-sequence audit semantics, completed follow-up-plan cleanup, and one bounded real-use tranche for `lean self-improving agent harness setup`.
**Summary**: Align the audit with the reducer’s stable monotonic source-sequence contract, remove the stale incomplete framework-followups mirror, then exercise the framework end to end on one exact topic and a prebound source cohort without broad acquisition or evaluation-loop implementation.
**Status**: CLOSED

## Context

The framework-followup implementation is present in the dirty working tree, the local instance passes structural validation, and the new `/atlas` router has transport coverage. Before ordinary use, Atlas needs one false-positive audit rule corrected and one deliberate topic workflow that proves source fidelity, routing, refresh, answer usefulness, and read-only post-audit behavior on real state. The repository plan `.agents/plans/2026-07-29-2056_atlas-framework-followups.md` is an incomplete `PENDING` mirror of already-delivered work and is stale; execution removes that untracked file rather than archiving it as historical evidence.

## Findings

- `scripts/atlas_state.py::_validate_manifest` accepts positive unique `Source seq` values, rejects duplicates, and allocates a new source as `max(existing Source seq) + 1`; it does not require a gapless range.
- `.agents/skills/atlas-audit/SKILL.md` currently says to check source-sequence continuity, which produced a warning for 20 historical gaps even though `state.validate` returned zero findings. Renumbering would destabilize source identities and relation references without improving reducer correctness.
- `.agents/plans/2026-07-29-2056_atlas-framework-followups.md` still says `Status: PENDING` and `Research in progress`, while its declared TODO retirement, `/atlas` router, deferred evaluation plan, clean instance check, and synchronized architecture snapshot are present. It was never completed as a plan record and contains no execution evidence worth preserving.
- The working tree contains broad prior Atlas work with no staged changes. This plan must preserve all unrelated modified, deleted, archived, and untracked paths and touch only the exact refinement/tranche surfaces it names.

## Tasks

- [ ] T1. Align source-sequence audit semantics
- [ ] T2. Remove the stale framework-followups mirror
- [ ] T3. Rebind and approve the exact first-tranche write set
- [ ] T4. Ingest and route the first-tranche source cohort
- [ ] T5. Build, refresh, answer, and audit the topic
- [ ] T6. Verify invariants and record the tranche outcome

## Approach

Research in progress. The final steps will bind the exact existing topic state, source cohort, workflow calls, approval boundaries, and verification receipts before execution.

## Critical files & anchors

- `.agents/skills/atlas-audit/SKILL.md` — manifest audit checklist containing the false gap-continuity requirement.
- `scripts/atlas_state.py::_validate_manifest` and `reduce_event(source-upsert)` — executable source-sequence validation and `max + 1` allocation owners.
- `.agents/plans/2026-07-29-2056_atlas-framework-followups.md` — stale incomplete mirror to remove.

## Verification

Research in progress.

## Assumptions & contingencies

- The deferred `.agents/plans/2026-07-29-2056_atlas-evaluation-loop.md` remains `PENDING`; this refinement does not implement `atlas-eval`.

## Closure Summary

- Closed 2026-07-30 as a stale preliminary mirror, per user instruction.
- A later approved execution artifact fully specified and completed the no-acquisition tranche. This file's unbound ingestion task and `Research in progress` sections were never the canonical execution record, so its tasks remain unchecked rather than being relabeled as completed.
- Delivered outcome: legal source-sequence gaps and subdomain projection checks are contracted and covered; the generic router boundary is qualified; `lean-self-improving-agent-harness` is `current` with seven applied edges, dirty count `0`, and source watermark `123`; the final bounded audit was clean and the complete suite passed `139` tests.
- `.agents/plans/2026-07-29-2056_atlas-evaluation-loop.md` remains the separate `PENDING` future-work plan.
