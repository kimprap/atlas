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
- Validate the complete registry bundle. Read the reducer-derived complete pending edge set and call `refresh-start` with exactly that ordered set; a missing or extra edge blocks the refresh.
- Persist the returned `TOPICS.md` replacement only while the reducer's exact input hashes still match, then create one dated pass under `topics/<topic-slug>/passes/`.
- Patch only managed sections of the topic `INDEX.md` unless the file is empty or structurally broken. Scale patch size to the delta; small evidence additions stay small.
- After the pass and topic patch both persist, call `refresh-complete` with the same complete edge set, pass path, and explicit completion date. Persist only validated changed documents under matching hash preconditions.
- `refresh-complete` alone marks relation rows `applied`, sets `Applied in pass`, and derives the final topic cache. Never hand-edit relation status, dirty counters, pending IDs, newest sequence, or watermark.
- If any required write fails after `refresh-start`, call `refresh-fail`; preserve unapplied edges as pending and persist `blocked`. Never report success from partial state.
- If `scripts/atlas_state.py` or a fixture-conformant port cannot run, halt before mutation rather than approximating the transition.

## Output

Report the pass path, applied edge IDs, resulting topic freshness state, and any blocked-state reason.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
