# Atlas architecture rationale index

Architecture remains normative at [`.agents/ARCHITECTURE.md`](../../.agents/ARCHITECTURE.md). Read this index only when the task trigger matches, then load only the linked ADR; ordinary sessions do not inject or scan ADR bodies.

| Number / title | Disposition | Task trigger | Canonical `.agents/ARCHITECTURE.md` section | ADR |
|---|---|---|---|---|
| 0001 — Single-entry Atlas orchestration | Accepted, amended | Public Atlas entry, same-agent owner load, or orchestration boundary | [Single public entrypoint](../../.agents/ARCHITECTURE.md#single-public-entrypoint) | [0001](./0001-single-entry-atlas-orchestration.md) |
| 0002 — Separate product and instance state | Accepted | Product/instance boundary, scaffold ownership, or framework snapshot sync | [Product and instance boundary](../../.agents/ARCHITECTURE.md#product-and-instance-boundary) | [0002](./0002-separate-product-and-instance-state.md) |
| 0003 — Canonical Markdown state | Accepted | Canonical state, reducer, projection, or migration ownership | [Canonical instance state](../../.agents/ARCHITECTURE.md#canonical-instance-state) | [0003](./0003-canonical-markdown-state.md) |
| 0004 — Vault-only research and explicit acquisition | Accepted | Research evidence boundary or explicit acquisition behavior | [Mode and write ownership](../../.agents/ARCHITECTURE.md#mode-and-write-ownership) | [0004](./0004-vault-only-research-and-explicit-acquisition.md) |
| 0005 — Bounded Engineering Cycles | Superseded | Product defects or retired Engineering Cycle retry | [Dispatch and result invariants](../../.agents/ARCHITECTURE.md#dispatch-and-result-invariants) | [0005](./0005-bounded-engineering-cycles.md) |
| 0006 — Hosted audit recapture coordinator | Superseded | Retired hosted recapture requirement | [Deterministic runtime seams](../../.agents/ARCHITECTURE.md#deterministic-runtime-seams) | [0006](./0006-hosted-audit-recapture-coordinator.md) |
| 0007 — Agent CLI and owner consolidation | Accepted | Agent-facing CLI, operation audience, owner-plus-mode map, compact owner result, or research publication owner | [Runtime model](../../.agents/ARCHITECTURE.md#runtime-model) | [0007](./0007-agent-cli-and-owner-consolidation.md) |
