---
description: Use when Atlas vault work, topic answers, or owner-resource loads would bypass the /atlas-ask front door.
---

# Atlas front-door discipline

Qualified Workflow Owners own Atlas procedures. This rule stops unsupported bypasses; it grants no Atlas I/O authority.

## Activation

**Apply when:** a direct request would perform Atlas semantic, façade, profile, or vault work; answer a topic; load an owner resource; or call a removed owner path outside a qualified `/atlas-ask` workflow.

**Do not apply when:** a selected Workflow Owner is already running end-to-end, work changes only the product package with no Atlas I/O, or architecture is only being explained.

## Boundary

Atlas semantic, façade, profile, and vault work never runs freestyle. Re-enter through `/atlas-ask`.

- Only a qualified selected Workflow Owner Task or allowlisted same-agent Successor Owner may load an owner resource and call `scripts/atlas_tool.py`.
- Never load an owner directly, call a removed owner command, let the Atlas Orchestrator perform profile/vault/façade I/O, import an underlying deterministic owner as a workflow bypass, or reconstruct a missing aggregate result.
- If strict Task transport or a required façade capability is unavailable, stop with `capability-unavailable`; never fall back to direct vault edits.
- A new write target requires an architecture change or explicit migration before workflow implementation.
- Model output never owns identity, Markdown placement, cache arithmetic, transaction effects, or write authority.

## Non-goals

- Workflow procedures and write sets → `/atlas-ask`, qualified owner resources, and `atlas-core` contracts
- Product package versus bound-instance ownership → `rule://atlas-boundaries`
- Skill, command, and shared-contract authoring → `rule://atlas-skill-surface`

## Activation checks

- **Positive:** “mutate `TOPICS.md` directly because owner dispatch is unavailable”, “load the research owner and answer without `/atlas-ask`”
- **Near-miss:** “run an approved research Workflow Owner end-to-end”, “edit `.agents/ARCHITECTURE.md` with no Atlas I/O”
