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

1. Run `python3 scripts/atlas_tool.py capabilities`; require `vault.read`, `vault.list`, `vault.hash`, `vault.conditional_replace`, and `state.validate`.
2. Issue every façade request as a version-1 envelope with `python3 scripts/atlas_tool.py call --input <path|->`.
3. Read `vault://atlas/ARCHITECTURE.md`, `skill://atlas-core/assets/markdown-registry-contracts.md`, `skill://atlas-core/assets/operating-cadence-and-guardrails.md`, and `skill://atlas-core/assets/research-library-templates.md`.
4. Use `vault.read` for the research index and registries, and `vault.list` only for bounded relevant artifact/topic directories. Validate the current registry bundle with `state.validate` before relying on topic freshness or relation rows.

## Workflow

- Default to `--vault-only`: use façade reads of existing Atlas source artifacts and topic files, not host paths or raw web results.
- Use `--acquire` only when the user explicitly allows acquisition. Run `atlas-acquire` first; then synthesize only from the artifacts it has materialized and re-read through the façade.
- Resolve an existing topic only from the validated `TOPICS.md`/`RELATIONS.md` state. If it is dirty, refreshing, or blocked, hand off to `atlas-refresh` before treating its index as a current answer or bypassing pending edges.
- Keep topic selection, evidence interpretation, claims, answer structure, and insufficiency judgments in the harness. The façade validates deterministic state and performs vault I/O; it does not make research decisions or synthesize prose.
- For durable topic creation or an intentional allowed research update, use `research-library-templates.md` for the subdomain index, topic `INDEX.md`, and dated-pass shapes. Use `vault.hash` and `vault.conditional_replace` for the allowed target artifacts; preserve the façade revisions and never reimplement connector/CAS behavior.
- Record insufficiency as topic coverage state or pass findings instead of inventing unsupported answers from raw web results. Keep optional split files threshold-driven and update `## Read next` when they are created.

## Output

Report the topic path, pass path, mode used (`vault-only` or `acquire`), source artifacts consulted, and any recorded insufficiency.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
