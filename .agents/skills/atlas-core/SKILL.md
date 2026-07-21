---
name: atlas-core
description: >
  Shared Atlas reducer, source-quality, schema, and calibration contracts.
  Read only when another Atlas skill directs you here for deterministic state,
  context-neutral source drafting, routing, freshness, or audit rules.
hide: true
disableModelInvocation: true
---

# atlas-core

This is a support skill for Atlas command skills.

Read `assets/markdown-registry-contracts.md` when an Atlas entrypoint needs deterministic rules for source identity, manifest dedupe, route-source, dirty-state recomputation, quick-answer freshness gates, managed-section patching, or fixture cleanup.

`scripts/atlas_state.py` is the connector-neutral reference registry validator/reducer. Read the event contracts before route, refresh, or repair writes; persist output only under matching input hashes.

Read `assets/source-summary-quality-guide.md` and `assets/source-summary-template.md` for the source-only semantic envelope, proportional concision, seven-item acceptance checklist, and semantic/post-draft boundary. `scripts/atlas_quality.py` is the deterministic artifact/calibration validator. `validate-summary` takes the source-only evidence bundle and a separate checklist argument; the checklist is generated validation output, not source evidence.

Read `assets/evals/source-summary-quality.json` only for optional read-only source-quality calibration or rubric development. Every host uses the same fixtures and expected JSON; calibration is not a source-write prerequisite.

Read `assets/operating-cadence-and-guardrails.md` when an Atlas entrypoint needs the current operating cadence, audit-first guardrails, hook limits, or deferred-phase boundaries.

Whenever `atlas-source` creates an artifact or explicitly rewrites one with `--resummarize`, it reads all of:

- `vault://atlas/ARCHITECTURE.md`
- `skill://atlas-core/assets/markdown-registry-contracts.md`
- `skill://atlas-core/assets/source-summary-quality-guide.md`
- `skill://atlas-core/assets/source-summary-template.md`

For research artifact shapes, pair the architecture and registry contracts with `skill://atlas-core/assets/research-library-templates.md`.
