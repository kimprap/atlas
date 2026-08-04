# Atlas architecture rationale index

Architecture remains normative at [`.agents/ARCHITECTURE.md`](../../.agents/ARCHITECTURE.md). Read this index only when the task trigger matches, then load only the linked ADR; ordinary sessions do not inject or scan ADR bodies.

| Number / title | Task trigger | Canonical `.agents/ARCHITECTURE.md` section | ADR |
|---|---|---|---|
| 0001 — Single-entry Atlas orchestration | Public Atlas entry, Workflow Owner dispatch, or orchestration boundary | [Single-entry Atlas orchestration](../../.agents/ARCHITECTURE.md#single-entry-atlas-orchestration) | [0001](./0001-single-entry-atlas-orchestration.md) |
| 0002 — Separate product and instance state | Product/instance boundary, scaffold ownership, or framework snapshot sync | [Product and instance boundary](../../.agents/ARCHITECTURE.md#product-and-instance-boundary) | [0002](./0002-separate-product-and-instance-state.md) |
| 0003 — Canonical Markdown state | Canonical state, reducer, projection, or migration ownership | [State and artifact roles](../../.agents/ARCHITECTURE.md#state-and-artifact-roles) | [0003](./0003-canonical-markdown-state.md) |
| 0004 — Vault-only research and explicit acquisition | Research evidence boundary or explicit acquisition behavior | [Mode ownership](../../.agents/ARCHITECTURE.md#mode-ownership) | [0004](./0004-vault-only-research-and-explicit-acquisition.md) |
| 0005 — Bounded Engineering Cycles | Product defects, recovery escalation, receipt, or bounded retry | [Product defects, recovery, and separately approved Engineering Cycles](../../.agents/ARCHITECTURE.md#product-defects-recovery-and-separately-approved-engineering-cycles) | [0005](./0005-bounded-engineering-cycles.md) |
