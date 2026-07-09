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

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `vault://atlas/summaries/registry/TOPICS.md`
5. the target topic `INDEX.md` only when the registry says it is current

## Workflow

- Resolve the requested topic against `TOPICS.md` before reading any topic file.
- If the topic is `current`, read the topic `INDEX.md`, then read optional split files only when `## Read next` points to them.
- If the topic is `dirty`, `refreshing`, or `blocked`, halt with topic path, freshness state, dirty count, and pending edge IDs.
- Do not answer from stale topic content plus unpersisted pending deltas.
- Cite source artifacts from the topic evidence map; raw URLs are not evidence unless materialized as source artifacts.

## Output

Return either a deterministic halt payload or the topic answer with source-artifact citations.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
