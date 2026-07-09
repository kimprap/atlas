# Atlas framework

Agent skills, Markdown reducer contracts, and empty vault **scaffold** for the Atlas research framework.

Sibling vault (instances + connectors): `../vault/`.

Umbrella parent `../` is not a git repository.

## Skills

Under `skills/`:

- `atlas-source`, `atlas-acquire`, `atlas-route`, `atlas-research`
- `atlas-refresh`, `atlas-answer`, `atlas-audit`, `atlas-index`, `atlas-migrate`
- `atlas-core` (shared contracts; not a user entrypoint)
- `digest` (compatibility shim → `/atlas-*`)

Architecture: `ARCHITECTURE.md`. Clean starter tree: `scaffold/`.

## Vault binding

Workflows use logical paths `vault://atlas/...`. The active profile in `../vault/config/` selects a connector (`local-fs` offline, `r2` / `remote-api` online).

## Local harness continuity

Until the agent harness loads skills from this repo natively, machine config may symlink:

```text
~/.dotfiles/.config/agents/skills/<name> → ~/Desktop/ng3/atlas/framework/skills/<name>
~/.dotfiles/.grok/skills/<name>          → same
```

Product skill bodies are owned here only.

## Deploy (later)

Flue / Cloudflare Worker packaging is out of scope for the initial scaffold. Deploy artifacts must include runtime + skills/contracts, not `../vault/instances/**`.
