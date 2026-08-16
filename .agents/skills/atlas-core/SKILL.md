---
name: atlas-core
description: >
  Hidden support contracts for Atlas CLI operations, deterministic state, source
  capture and quality, research publication, transactions, recovery, and owner results.
hide: true
disableModelInvocation: true
---

# atlas-core

This is hidden support for `/atlas-ask` and its three qualified internal owner resources. Direct invocation is not a workflow: allow repository inspection only, perform no Atlas/profile/vault/façade I/O, and return `Redirect: invoke /atlas-ask.`

## Generated façade CLI

`scripts/atlas_tool.py` owns one immutable operation catalog and generates dispatch, capabilities, help, and family/verb commands from it.

- `python3 scripts/atlas_tool.py capabilities` reports lifecycle operations.
- `python3 scripts/atlas_tool.py capabilities --all` additionally reports internal primitives and audience metadata.
- `python3 scripts/atlas_tool.py <family> <verb> --input -` consumes one exact operation-args JSON object from stdin; `--input <file>` consumes one UTF-8 file.
- `python3 scripts/atlas_tool.py call --input -` consumes exactly `{"version":2,"op":"<literal>","args":{...}}`.

A known internal command remains callable under the same access, connector, and authority checks. Discovery audience never grants mutation authority.

Machine stdout is canonical UTF-8 JSON plus one LF and stderr is empty. Human `--help` is the only prose output. Every machine response has exactly:

```text
version, ok, op, disposition, result, findings, recovery
```

`version` is `2`. Disposition is exactly `completed|no-write|rejected|unavailable|recovery-required|manual-intervention|internal-error`. Findings are normalized objects with exactly `code`, `path`, and `detail`. `recovery` is `null` unless the façade returns exact structured recovery. Nested domain records retain their own schema versions.

Read `assets/agent-cli-recipes.md` for the exact owner operation sequences and lifecycle command index. Owners use those literals and never invoke domain modules directly, derive connector paths or revisions, hand-author canonical projections, or reproduce transaction/recovery behavior.

## Contract index

- `assets/markdown-registry-contracts.md`: canonical tables, reducer events, managed sections, lifecycle effects, transaction and recovery invariants.
- `assets/atlas-workflow-result.schema.json`: sole seven-field outer owner result.
- `assets/source-capture-mapping.md` and `assets/source-capture.schema.json`: mapping of complete textual retrieval into `source.normalize_capture`.
- `assets/source-worker-result.schema.json`, `assets/source-summary-proposal.schema.json`, `assets/source-summary-quality-guide.md`, and `assets/source-summary-template.md`: source semantic drafting and validation.
- `assets/research-library-templates.md`: research pass and managed topic/subdomain shapes.
- `assets/operating-cadence-and-guardrails.md`: qualification, effect gates, bounded resumes, exact recovery, and two-phase migration.

## Ownership boundaries

Only a qualified selected owner may perform Atlas/profile/vault/façade I/O. It runs route, refresh, or topic-create procedures in process; there are no helper-owner chains. Only the outer owner emits `atlas-workflow-result.schema.json`.

The owner result has exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`. Owner is `atlas-source|atlas-research|atlas-maintain`; outcome is `completed|no-write|needs-user|needs-guidance|blocked|framework-defect`; effect is `none|committed|partial|unknown`. Prepare, preview, and observed no-write use `none`. `partial|unknown` always blocks and exposes only exact already-authorized recovery in `next`.

Model work may interpret evidence and draft bounded semantic content. It never owns canonical identity, Markdown placement, target order, cache arithmetic, revisions, transaction effects, write authority, or recovery inference.