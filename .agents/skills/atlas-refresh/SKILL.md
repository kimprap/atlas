---
name: atlas-refresh
description: >
  Atlas dirty-topic refresh entrypoint. Use when the user invokes
  /atlas-refresh or wants pending Atlas relation edges applied to a dirty topic
  through a persisted delta pass.
disableModelInvocation: true
---

# atlas-refresh

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `skill://atlas-core/assets/research-library-templates.md`
5. `vault://atlas/summaries/registry/TOPICS.md`
6. `vault://atlas/summaries/registry/RELATIONS.md`
7. the target topic `INDEX.md` and any optional split files it references
8. the pending source artifacts named by `Pending edge IDs`

## Workflow

- Refresh is the only normal transition from `dirty` to `current`.
- Set the target topic to `refreshing` before writing the pass file.
- Create one dated pass first under `topics/<topic-slug>/passes/`.
- Patch only managed sections of the topic `INDEX.md` unless the file is empty or structurally broken.
- Scale patch size to the delta: small evidence additions should stay small; only rewrite answer sections when pending sources materially change the topic answer.
- Mark refreshed relation rows `applied` and set `Applied in pass`.
- Recompute the topic row in `TOPICS.md` from `RELATIONS.md`; never hand-edit dirty counters.
- If any required write fails after `refreshing` is set, leave edges pending and mark the topic `blocked` instead of pretending refresh succeeded.

## Output

Report the pass path, applied edge IDs, resulting topic freshness state, and any blocked-state reason.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
