# Atlas app

Agent harness surface, Markdown reducer contracts, and empty vault **scaffold** for the Atlas research product.

Sibling vault (instances + connectors): `../vault/`.

Umbrella parent `../` is not a git repository.

## Layout

```text
app/
├── .agents/
│   ├── AGENTS.md
│   ├── commands/          # OMP slash commands (/atlas-*)
│   ├── skills/            # skill bodies + contracts
│   └── plans/
├── ARCHITECTURE.md        # product source of truth
├── scaffold/              # empty vault instance template (not runtime code)
├── README.md
└── .gitignore
```

## Skills & commands

Skills under `.agents/skills/`:

- `atlas-source`, `atlas-acquire`, `atlas-route`, `atlas-research`
- `atlas-refresh`, `atlas-answer`, `atlas-audit`, `atlas-index`, `atlas-migrate`
- `atlas-core` (shared contracts; not a user entrypoint)
- `digest` (compatibility shim → `/atlas-*`)

Slash command stubs under `.agents/commands/` load when OMP cwd is this repo (or walks up to it).

`scaffold/` is a **starter vault tree** for new instances (empty registries/indexes). It is not the app implementation. Future runtime code (Worker/Flue) would live under something like `src/` when introduced.

## Vault binding

Workflows use logical paths `vault://atlas/...`. The active profile in `../vault/config/` selects a connector (`local-fs` offline, `r2` / `remote-api` online).

Open this repo as the agent project cwd so `.agents/skills` and `.agents/commands` auto-discover. Skills are not installed into machine dotfiles.

## Deploy (later)

Flue / Cloudflare Worker packaging is out of scope for the initial layout. Deploy artifacts must include runtime + skills/contracts, not `../vault/instances/**`.
