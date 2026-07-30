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

1. Run `python3 scripts/atlas_tool.py capabilities`; require `vault.read`, `vault.hash`, `state.validate`, `refresh.execute`, and `refresh.recover`.
2. Issue every façade request as a version-1 envelope with `python3 scripts/atlas_tool.py call --input <path|->`.
3. Read `vault://atlas/ARCHITECTURE.md`, `skill://atlas-core/assets/markdown-registry-contracts.md`, `skill://atlas-core/assets/operating-cadence-and-guardrails.md`, and `skill://atlas-core/assets/research-library-templates.md`.
4. Use `vault.read` for `MANIFEST.md`, `TOPICS.md`, `RELATIONS.md`, the target topic `INDEX.md`, its referenced split files, and the source artifacts named by its pending edges. Retain the façade-returned revisions.

## Workflow

- Call `state.validate` on the current registry bundle before selecting the target. Use the validated topic cache and complete persisted pending edge set; invalid state, a non-dirty topic, or a missing/extra/reordered edge blocks the refresh.
- Use `vault.hash` to verify that the dated pass URI is missing. The target topic index revision, manifest/topics/relations revisions, pass URI, and ordered pending edge IDs must come from the façade-observed state.
- Complete harness synthesis before mutation. Using only the selected materialized source artifacts and topic context, make the dated `pass_text` and candidate `index_text`; patch only managed topic-index sections unless the index is empty or structurally broken. Keep the evidence interpretation, answer, and scope decisions human/harness-owned. `refresh.execute` does no synthesis.
- Approve one complete refresh projection with exactly the contract fields, including the façade-observed revisions, exact ordered edge IDs, `pass_expected_revision: "missing"`, candidate-byte SHA-256 values, dates, and transaction root. Bind it to the exact supplied `pass_text` and `index_text`; after approval, do not alter or substitute either bytes, hashes, revisions, or edges.
- Call `refresh.execute` with exactly `{version:1,op:"refresh.execute",args:{projection,pass_text,index_text}}`. The façade alone persists its immutable intent/phases, applies the start and complete transitions, writes the pass and index, applies edges, recomputes freshness, and emits the receipt.
- Only after an interrupted, uncertain, or pre-existing execution, call `refresh.recover` with the identical projection and identical pass/index text. Never recover a changed candidate or changed edge set. Do not issue refresh reducer events, conditional replacements, manual recovery, or transaction/CAS writes outside the façade.

## Output

Report the façade receipt's pass path, applied edge IDs, resulting topic freshness state, and any blocked-state reason.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
