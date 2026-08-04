# atlas-answer

## Qualified invocation

This ordinary Workflow Owner resource may execute only when one of these qualified conditions holds:

1. The selected Workflow Owner receives a live `/atlas-ask` Task whose dispatch binding names `atlas-answer`.
2. An allowlisted current Workflow Owner loads this resource as a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
3. Any other load performs no further read, model work, façade call, profile/vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

Only the selected Workflow Owner emits one outer `atlas-workflow-result.schema.json` result. A Successor Owner preserves its native current output and never creates another Task or outer result.



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
