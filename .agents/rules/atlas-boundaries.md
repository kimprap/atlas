---
description: Use when deciding where Atlas product files, scaffold templates, or bound-instance state may live or be edited.
---

# Atlas ownership boundaries

Portable across local agents, CI, and serverless runtimes. Prefer logical vault paths and the active connector profile — never assume a host filesystem layout.

## Activation

**Apply when:** editing or placing architecture, scaffold, provision, skills/commands packaging, vault binding, deploy artifacts, or choosing product vs instance as the write surface.

**Do not apply when:** ordinary skill checklist execution already covers the task; pure vault content work with a clear `/atlas-*` entrypoint; connector implementation details outside this product package.

| Surface | Edit here | Do not put here |
|---|---|---|
| Product package (this app) | Skills, commands, contracts, `.agents/ARCHITECTURE.md`, `scaffold/`, provision tooling, deployable runtime | Living research rows, instance notes, credentials, connector secrets |
| Bound instance (`vault://atlas/…`) | Instance state (sources, registries, topics, passes, optional editor config) | Framework authoring source of truth |
| `scaffold/` | Seed-once empty templates | Product bodies, living rows, `runs/`, real topics |

## Seams that default wrong

- Author framework text only at `.agents/ARCHITECTURE.md`. Bound instances hold product-owned snapshots at `vault://atlas/ARCHITECTURE.md`; sync only intended instances, then run `python3 scripts/atlas-instance.py check`. Never hand-copy framework trees into an instance.
- Logical vault root is `vault://atlas/` only. Resolve via the active connector/profile. No `vault://digest/` or second vault root.
- Keep the agent harness under this product's `.agents/`. Do not install product skills/commands into host-global agent config outside the product package.
- Provision bootstraps empty instances; it is not app deploy. Deploy artifacts must not embed instance research data.
- Ask before deploy, credential use, non-dev profile writes, or destructive registry repair.

## Non-goals

- Provision CLI encyclopedia → `scripts/atlas-instance.py`, `scaffold/README.md`
- Connector/profile internals → vault binding project / storage port
- Reducer checklists → `/atlas-*` skills and `atlas-core` contracts

## Activation checks

- **Positive:** “edit architecture only on the bound instance snapshot”, “seed a real topic under scaffold/”, “install Atlas product skills into host-global agent config”
- **Near-miss:** “fix a typo in README.md”, “run `/atlas-answer` on a topic”
