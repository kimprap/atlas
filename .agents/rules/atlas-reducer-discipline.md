---
description: Use when Atlas semantic, façade, profile, vault, topic-answer, or owner-resource work would bypass the /atlas-ask front door.
---

# Atlas front-door discipline

This rule prevents unsupported bypasses; it grants no Atlas I/O authority.

## Activation

**Apply when:** a direct request would perform Atlas semantic, façade, profile, or vault work; answer a topic; load an owner resource; call a removed owner path; or reconstruct owner recovery outside a qualified `/atlas-ask` workflow.

**Do not apply when:** one selected Workflow Owner is already running end-to-end in the same agent, work changes only the product package with no Atlas I/O, or architecture is only being explained.

## Boundary

Atlas semantic, façade, profile, and vault work never runs freestyle. Re-enter through `/atlas-ask`.

- `/atlas-ask` is the sole classifier and selects exactly one of `atlas-source`, `atlas-research`, or `atlas-maintain` plus one mode.
- Only that qualified same-agent owner may load its owner resource and call `scripts/atlas_tool.py`.
- Route, refresh, and topic-create procedures run in process inside the selected owner. Never load another owner resource or recreate an owner chain.
- An unqualified owner load performs no further read, model work, façade/profile/vault I/O, or write and redirects to `/atlas-ask`.
- Missing delegation facilities never stop same-agent execution. A genuinely missing façade operation returns `framework-defect` with concrete evidence; never fall back to direct vault edits.
- Never call a removed owner command, let the front door perform Atlas I/O, import a deterministic domain module as a workflow bypass, reconstruct a missing owner result, or infer recovery.
- A new write target requires an architecture change or explicit migration before workflow implementation.
- Model output never owns identity, Markdown placement, cache arithmetic, transaction effects, write authority, or recovery.
- Never add an automatic audit/verify/repair loop or retry coordinator.

## Non-goals

- Workflow procedures and write sets → `/atlas-ask`, the three owner resources, and `atlas-core` contracts
- Product package versus bound-instance ownership → `rule://atlas-boundaries`
- Skill, command, and shared-contract authoring → `rule://atlas-skill-surface`

## Activation checks

- **Positive:** “write `TOPICS.md` directly because owner execution is inconvenient”, “load the research owner and answer without `/atlas-ask`”
- **Near-miss:** “run an approved research mode end-to-end”, “edit `.agents/ARCHITECTURE.md` with no Atlas I/O”