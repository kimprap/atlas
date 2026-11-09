# Atlas architecture rationale index

Architecture remains normative at [`.agents/ARCHITECTURE.md`](../../.agents/ARCHITECTURE.md). Read this index only when the task trigger matches, then load only the linked ADR; ordinary sessions do not inject or scan ADR bodies.

| Number / title | Disposition | Task trigger | Canonical `.agents/ARCHITECTURE.md` section | ADR |
|---|---|---|---|---|
| 0001 — Single-entry Atlas orchestration | Superseded by Atlas v2 (code at tag v1) | Public Atlas entry, same-agent owner load, or orchestration boundary | [Atlas architecture](../../.agents/ARCHITECTURE.md) | [0001](./0001-single-entry-atlas-orchestration.md) |
| 0002 — Separate product and instance state | Superseded by Atlas v2 (code at tag v1) | Product/instance boundary, scaffold ownership, or framework snapshot sync | [Atlas architecture](../../.agents/ARCHITECTURE.md) | [0002](./0002-separate-product-and-instance-state.md) |
| 0003 — Canonical Markdown state | Superseded by Atlas v2 (code at tag v1) | Canonical state, reducer, projection, or migration ownership | [Atlas architecture](../../.agents/ARCHITECTURE.md) | [0003](./0003-canonical-markdown-state.md) |
| 0004 — Vault-only research and explicit acquisition | Superseded by Atlas v2 (code at tag v1) | Research evidence boundary or explicit acquisition behavior | [Atlas architecture](../../.agents/ARCHITECTURE.md) | [0004](./0004-vault-only-research-and-explicit-acquisition.md) |
| 0005 — Bounded Engineering Cycles | Superseded by Atlas v2 (code at tag v1) | Product defects or retired Engineering Cycle retry | [Atlas architecture](../../.agents/ARCHITECTURE.md) | [0005](./0005-bounded-engineering-cycles.md) |
| 0006 — Hosted audit recapture coordinator | Superseded by Atlas v2 (code at tag v1) | Retired hosted recapture requirement | [Atlas architecture](../../.agents/ARCHITECTURE.md) | [0006](./0006-hosted-audit-recapture-coordinator.md) |
| 0007 — Agent CLI and owner consolidation | Superseded by Atlas v2 (code at tag v1) | Agent-facing CLI, operation audience, owner-plus-mode map, compact owner result, or research publication owner | [Atlas architecture](../../.agents/ARCHITECTURE.md) | [0007](./0007-agent-cli-and-owner-consolidation.md) |
| 0008 — Host-neutral core behind ports | Accepted | Host seam, port shape, new adapter, contract suite, fake host, or cross-check fallback | [Ports and capabilities](../../.agents/ARCHITECTURE.md#ports-and-capabilities) | [0008](./0008-host-neutral-core-behind-ports.md) |
| 0009 — The CLI decides every stop | Accepted | Reply `decisions`, confirm settings, `approval` labels, paid-at-scale changes, or fixed stops | [Approvals](../../.agents/ARCHITECTURE.md#approvals) | [0009](./0009-cli-decides-every-stop.md) |
| 0010 — One SQLite store per profile with numbered migrations from the first real row | Accepted | Store layout, profiles, schema change, migration, or release minor bump | [Store](../../.agents/ARCHITECTURE.md#store) | [0010](./0010-one-sqlite-store-per-profile-with-numbered-migrations.md) |
