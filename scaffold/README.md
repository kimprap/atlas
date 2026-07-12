# Vault instance scaffold

Empty-state **seed** for new Atlas vault instances. Not runtime code, not personal research data, and not an app deploy artifact.

## File classes

| Class | Where authored | Provision behavior |
|---|---|---|
| **product_owned** | App product (e.g. root `ARCHITECTURE.md`) | Injected on `create`; overwritten by `sync-framework` |
| **seed_once** | This directory (`summaries/…`, `todos/` stub) | Copied only on `create`; never overwritten by sync |
| **instance_owned** | Living instance only | Never provisioned again (artifacts, runs, topics, real todos, `.obsidian/`) |

Manifest: [`MANIFEST.json`](MANIFEST.json).

**Do not** put product_owned bodies under this tree. Agents and humans edit product architecture at app root; the provision script materializes it into each instance root as `vault://atlas/ARCHITECTURE.md`.

## Commands

Run from the app repo root:

```bash
# New empty instance under ../vault/instances/<name>/
python3 scripts/atlas-instance.py create --name work

# Refresh product_owned snapshots (e.g. after editing ARCHITECTURE.md)
python3 scripts/atlas-instance.py sync-framework --name personal
python3 scripts/atlas-instance.py sync-framework --all

# Fail on product_owned drift or missing seed templates
python3 scripts/atlas-instance.py check
```

Override instance parent with `--instances-root /path/to/instances` when needed.

After `create`, bind a vault profile/connector to the new instance root before agent use. Living data stays under `../vault/instances/` only.

## Out of scope

- Flue / Worker / app release packaging
- Migrating living registry **rows** (use `/atlas-migrate` for schema changes on existing instances)
- Syncing personal notes between machines (use vault git/R2/backup — not this scaffold)
