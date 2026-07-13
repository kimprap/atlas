---
name: atlas-research
description: >
  Atlas research synthesis entrypoint. Use when the user invokes
  /atlas-research or wants a durable Atlas topic synthesized from existing
  source artifacts, with acquisition only when explicitly allowed.
disableModelInvocation: true
---

# atlas-research

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `skill://atlas-core/assets/research-library-templates.md`
5. `vault://atlas/summaries/research/INDEX.md`
6. `vault://atlas/summaries/registry/TOPICS.md`
7. the relevant source artifacts and topic files

## Workflow

- Default to `--vault-only` and synthesize only from existing Atlas source artifacts and topic files.
- Use `--acquire` only when the user explicitly allows acquisition; in that mode, run `atlas-acquire` first, then synthesize from the materialized artifacts only.
- If the request targets an existing dirty topic, hand off to `atlas-refresh` instead of bypassing pending relation edges.
- For durable topic creation or intentional topic refresh, use `skill://atlas-core/assets/research-library-templates.md` for the subdomain index, topic `INDEX.md`, and dated pass shapes.
- Record insufficiency as topic coverage state or pass findings instead of inventing unsupported answers from raw web results.
- Keep optional split files threshold-driven and update `## Read next` when they are created.

## Output

Report the topic path, pass path, mode used (`vault-only` or `acquire`), source artifacts consulted, and any recorded insufficiency.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
