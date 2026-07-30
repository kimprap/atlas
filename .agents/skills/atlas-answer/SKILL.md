---
name: atlas-answer
description: >
  Atlas answer lookup entrypoint. Use when the user invokes /atlas-answer or
  wants the current Atlas topic answer returned only when registry freshness
  permits it.
disableModelInvocation: true
---

# atlas-answer

## Read first

1. Run `python3 scripts/atlas_tool.py capabilities`; require `vault.read`, `vault.hash`, and `state.validate`.
2. Issue every façade request as a version-1 envelope with `python3 scripts/atlas_tool.py call --input <path|->`.
3. Read `vault://atlas/ARCHITECTURE.md`, `skill://atlas-core/assets/markdown-registry-contracts.md`, and `skill://atlas-core/assets/operating-cadence-and-guardrails.md`.
4. Use `vault.read` for `MANIFEST.md`, `TOPICS.md`, and `RELATIONS.md`, then call `state.validate` on the complete registry bundle before resolving a requested topic.

## Workflow

- Resolve the requested topic only from the façade-read, state-validated registry. Validation findings or an unknown topic are deterministic halt conditions.
- If the validated topic is `dirty`, `refreshing`, or `blocked`, halt with its path, freshness state, dirty count, and pending edge IDs. Do not call `vault.read` for its topic `INDEX.md`, optional split files, or stale answer content.
- Only for a validated `current` topic, call `vault.read` for its `INDEX.md`, then read optional split files only when `## Read next` points to them.
- After reading the topic content, use `vault.hash` to confirm the `TOPICS.md` revision has not changed and call `state.validate` again. Return the content only if the topic remains `current`; otherwise discard the read bytes and return the deterministic freshness halt.
- Cite source artifacts from the topic evidence map; raw URLs are not evidence unless materialized as source artifacts. Keep citation choice and answer composition in the harness, not the façade.

## Output

Return either a deterministic halt payload or the topic answer with source-artifact citations.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
