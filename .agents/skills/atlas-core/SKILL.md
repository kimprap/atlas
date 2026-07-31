---
name: atlas-core
description: >
  Shared Atlas tool, reducer, source-quality, schema, and calibration contracts.
  Read only when another Atlas skill directs you here for provider-neutral operations,
  deterministic state, context-neutral source drafting, freshness, or audit rules.
hide: true
disableModelInvocation: true
---

# atlas-core

This is a support skill for Atlas command skills.

`scripts/atlas_tool.py` is the provider-neutral façade. It exposes only `capabilities(connector=None)` and `execute(request,connector=None)` plus canonical `capabilities` / `call --input <path|->` CLI commands. Requests and responses use the version-1 envelope in `assets/markdown-registry-contracts.md`.

| Family | Operations |
|---|---|
| Vault | `vault.read`, `vault.read_json`, `vault.list`, `vault.hash`, `vault.write_json`, `vault.conditional_replace`, `vault.digest_tree`, `vault.delete_tree` |
| URL / discovery | `url.normalize`, `url.resolve_reference`, `discovery.normalize` |
| Quality | `quality.validate_proposal`, `quality.validate_summary`, `quality.prepare_calibration`, `quality.validate_calibration`, `quality.validate_fresh_assessment` |
| State | `state.validate`, `state.reduce` |
| Source | `source.render_summary`, `source.merge_artifact`, `source.render_route_artifact`, `source.lookup`, `source.inventory`, `source.prepare`, `source.snapshot_active` |
| Transactions | `transaction.execute`, `transaction.recover`, `transaction.successor` |
| Effect | `effect.execute`, `effect.recover` |
| Refresh | `refresh.execute`, `refresh.recover` |

Read `assets/markdown-registry-contracts.md` for operation shapes, source identity, route guards, reducers, transactions, refresh recovery, deletion, freshness, managed-section patching, and fixture cleanup. Entry skills call the façade; direct imports of `scripts/atlas_state.py`, `atlas_quality.py`, `atlas_url.py`, `atlas_source.py`, `atlas_connector.py`, and `atlas_discovery.py` are reserved for tests and fixture-conformant runtime ports beneath it.

Read `assets/source-summary-proposal.schema.json`, `assets/source-summary-quality-guide.md`, and `assets/source-summary-template.md` for context-neutral source proposal, validation, rendering, and the seven-item acceptance gate. Read `assets/fresh-source-assessment.schema.json` for the orthogonal fresh observation contract. Checklists are validation output, never evidence.

Read `assets/evals/source-summary-quality.json` and `assets/evals/agent-tooling.json` only for optional read-only calibration or rubric development. Prepare blinded packets with `quality.prepare_calibration`; validate exact structured outcomes with `quality.validate_calibration`. Calibration never grants source-write authority.

Read `assets/operating-cadence-and-guardrails.md` when an entrypoint needs cadence, audit-first guardrails, hook limits, or deferred-phase boundaries.

Whenever `atlas-source` creates an artifact or explicitly rewrites one with `--resummarize`, it reads all of:

- `vault://atlas/ARCHITECTURE.md`
- `skill://atlas-core/assets/markdown-registry-contracts.md`
- `skill://atlas-core/assets/source-summary-quality-guide.md`
- `skill://atlas-core/assets/source-summary-template.md`

For research artifact shapes, pair the architecture and registry contracts with `skill://atlas-core/assets/research-library-templates.md`.
