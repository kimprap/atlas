# Atlas app

Agent harness surface, Markdown reducer contracts, empty vault **scaffold**, and **instance provision** for the Atlas research product.

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
├── ARCHITECTURE.md        # sole authoring SO for framework (product_owned)
├── scaffold/              # seed-once empty vault templates + MANIFEST
├── scripts/
│   └── atlas-instance.py  # create | sync-framework | check
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

## Instance provision (scaffold)

`scaffold/` is a **starter vault seed** for new instances (empty registries/indexes). It is not the app implementation and not a deploy package.

| Class | Authored in | Behavior |
|---|---|---|
| **product_owned** | App root (e.g. `ARCHITECTURE.md`) | Injected on create; overwritten by `sync-framework` |
| **seed_once** | `scaffold/**` | Copied only on create |
| **instance_owned** | `../vault/instances/<id>/` only | Never re-seeded by provision |

```bash
# New empty instance → ../vault/instances/<name>/
python3 scripts/atlas-instance.py create --name work

# After editing ARCHITECTURE.md, refresh instance snapshots
python3 scripts/atlas-instance.py sync-framework --name personal
python3 scripts/atlas-instance.py sync-framework --all

# Detect product_owned drift / missing templates
python3 scripts/atlas-instance.py check
```

Details: [`scaffold/README.md`](scaffold/README.md). Manifest: [`scaffold/MANIFEST.json`](scaffold/MANIFEST.json).

This pipeline is **not** Flue/Worker release. Future runtime code would live under something like `src/` when introduced.

## Vault binding

Workflows use logical paths `vault://atlas/...`. The active profile in `../vault/config/` selects a connector (`local-fs` offline, `r2` / `remote-api` online).

Open this repo as the agent project cwd so `.agents/skills` and `.agents/commands` auto-discover. Skills are not installed into machine dotfiles.

## Deploy (later)

Flue / Cloudflare Worker packaging is out of scope for the initial layout. Deploy artifacts must include runtime + skills/contracts, not `../vault/instances/**`. Instance provision stays a separate local/bootstrap concern.
