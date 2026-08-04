# Vault instance scaffold

Empty-state **seed** for new Atlas vault instances. Not runtime code, not personal research data, and not an app deploy artifact.

## File classes

| Class | Where authored | Provision behavior |
|---|---|---|
| **product_owned** | Product package (e.g. `.agents/ARCHITECTURE.md`) | Injected on `create` as instance-root `ARCHITECTURE.md`; overwritten by `sync-framework` |
| **seed_once** | This directory (`summaries/…`) | Copied only on `create`; never overwritten by sync |
| **instance_owned** | Living instance only | Never provisioned again (artifacts, runs, topics, legacy personal todos, `.obsidian/`) |


An already-existing `vault://atlas/todos/` tree is optional unmanaged user data. Provision, sync, and check neither seed, require, inspect, migrate, nor delete it.
Manifest: [`MANIFEST.json`](MANIFEST.json).

**Do not** put product_owned bodies under this tree. Agents and humans edit product architecture at `.agents/ARCHITECTURE.md`; the provision script materializes it into each instance root as `vault://atlas/ARCHITECTURE.md`.

## Commands

Run from the app repo root:

```bash
# New empty instance under ../vault/instances/<name>/
python3 scripts/atlas-instance.py create --name work

# Refresh one intended product_owned snapshot after approval when required
python3 scripts/atlas-instance.py sync-framework --name atlas

# Fail on product_owned drift or missing seed templates
python3 scripts/atlas-instance.py check
```

Prefer explicit `--name` targets. Obtain approval before writing a non-development profile; reserve `--all` for an explicitly approved fleet-wide sync.

Override instance parent with `--instances-root /path/to/instances` when needed.

After `create`, bind a vault profile/connector to the new instance root before agent use. Living data stays under `../vault/instances/` only.

## Out of scope

- Application release packaging or runtime deployment
- Migrating living registry **rows** (use `/atlas-ask` with the explicit migration intent for schema changes on existing instances)
- Syncing personal notes between machines (use vault git/R2/backup — not this scaffold)
