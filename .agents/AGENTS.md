---
description: Atlas app project guide — product, skills, contracts, and deployable runtime.
alwaysApply: true
---

# Atlas app guide

## Project overview

`~/Desktop/ng3/atlas/app` is the **product repo**: agent skills, slash commands, deterministic Markdown reducer contracts, scaffold for empty vaults, and the future deployable runtime (e.g. Flue agent on Cloudflare Workers) that runs Atlas workflows against a bound vault.

It does **not** own personal research state. Living knowledge banks live in the sibling `../vault` project (instances + connectors). Logical access is always `vault://atlas/...`, resolved by the active vault connector/profile—not by assuming Markdown sits at this repo root.

Umbrella parent `~/Desktop/ng3/atlas` is a filesystem namespace only (**not** git). Machine dotfiles must not host Atlas product skills or commands.

## Philosophy

- **Deep modules over sprawl.** Each `/atlas-*` entrypoint is a narrow workflow with a small read/write set. Shared behavior lives in `atlas-core` contracts, not copy-pasted checklists.
- **Deterministic reducers, structured LLM proposals.** Models propose routes/deltas; checklists and schema contracts apply them. No silent registry rewrites.
- **Vault-agnostic runtime.** App code depends on logical vault paths + a storage port (connector interface from the vault repo), never on a single filesystem layout or Obsidian APIs.
- **Offline-first contracts.** The same skills must be valid for local agents and remote Workers; environment only swaps the connector profile.
- **Starter vs instance.** This repo ships `scaffold/` (empty registries, source-kind vocabulary) as a **template for new vault instances**, not as runtime source. Instances accumulate real sources/topics only under `../vault/instances/`.
- **Harness locality.** Agent surface is under `.agents/` only (skills, commands, plans, AGENTS.md). Do not symlink or copy into `~/.dotfiles`.

## Source of truth

- Product architecture: `ARCHITECTURE.md` at app root.
- Reducer contracts: `.agents/skills/atlas-core/assets/`.
- Slash commands: `.agents/commands/*.md` (thin wrappers → `skill://…`).
- Operating cadence/guardrails: companion asset next to contracts.
- Instance data and connector profiles: `~/Desktop/ng3/atlas/vault` only.
- Plans: `.agents/plans/` here for app work; vault/connector plans prefer `../vault/.agents/plans/`.

If architecture and contracts diverge, update architecture first, then contracts and affected skills in the same change.

## Layout

```text
app/
├── .agents/
│   ├── AGENTS.md
│   ├── commands/            # /atlas-* slash commands (OMP-native)
│   ├── skills/              # atlas-*, atlas-core, digest
│   └── plans/
├── ARCHITECTURE.md          # product SO
├── scaffold/                # empty instance template for new vaults
├── README.md
└── .gitignore
```

Do not store `instances/`, personal research rows, or `.obsidian/` in this repo.  
Do not invent a `src/` directory until there is real runtime/library code to put there.

## Entrypoints

| Entrypoint | Role |
|---|---|
| `atlas-source` | Explicit URL ingestion |
| `atlas-acquire` | Bounded discovery only |
| `atlas-route` | Route status, relations, dirty cache |
| `atlas-research` | Vault-only default; `--acquire` escape hatch |
| `atlas-refresh` | Dirty → current via one dated pass |
| `atlas-answer` | Freshness-gated read |
| `atlas-audit` | Read-only validator |
| `atlas-index` | Vocab/topic promotion and repair |
| `atlas-migrate` | Explicit schema migration |
| `digest` | Compatibility shim → `/atlas-*` |

## Runtime binding

- **Local:** vault profile `local` → `local-fs` → `../vault/instances/personal`.
- **Remote:** deploy this package; inject vault profile `cloud`. Do not ship personal Markdown in the deploy artifact.
- Open agent sessions with cwd = this repo so `.agents/skills` and `.agents/commands` auto-discover.

## Agent workflow conventions

- Surgical changes; Conventional Commits (`feat(atlas): ...`, `fix(route): ...`).
- New behavior: update contracts + owning skill + architecture if invariants change; keep command stubs thin.
- Smoke tests use temporary fixtures; clean before done. Never leave smoke rows in a personal instance.
- Do not reintroduce `vault://digest` or a second vault root.
- Ask before deploy, credential use, production profile writes, or destructive registry repair.

## Verification

- Skills under `.agents/skills/` for all entrypoints; `digest` remains a thin shim.
- Commands under `.agents/commands/` for each `/atlas-*` entrypoint.
- `scaffold/` has starter registries only (no personal research rows, no `runs/`).
- Contracts load without assuming repo-root vault files.
