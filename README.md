# Atlas app

Atlas turns collected sources into current, traceable topic answers. This repository is the product package: agent skills, slash commands, framework contracts, empty instance templates, provision tooling, and runtime assets.

Living research does **not** live here. It lives in a bound instance and is accessed as `vault://atlas/…` through the active connector profile. The same package can run under local agents, CI, or serverless runtimes; only the vault binding changes.

The canonical framework contract is [`.agents/ARCHITECTURE.md`](.agents/ARCHITECTURE.md). Provision copies its product-owned snapshot to `vault://atlas/ARCHITECTURE.md`.

## Layout

```text
.agents/
  AGENTS.md           # always-on product map
  ARCHITECTURE.md     # product-owned framework contract
  rules/              # ownership / freestyle / skill-surface seams
  commands/           # thin /atlas and /atlas-* stubs → skill://…
  skills/             # /atlas router, expert entry skills, and atlas-core contracts
  plans/
scaffold/             # seed-once templates + MANIFEST
scripts/atlas-instance.py
```

## Slash commands

Use `/atlas` as the optional low-friction front door: it presents one first-owner route for approval before dispatch. Direct expert slash commands bypass that gate. Each command keeps reads and writes within the framework boundaries.

### How to use them

1. Open this product package as the agent project.
2. Bind the intended instance so `vault://atlas/…` resolves through the active profile.
3. Start with `/atlas` when you want intent routed to one owner, or choose the direct expert command that matches your goal below.
4. Use normal repository workflows for product or framework code changes.

Detailed write boundaries: [`.agents/ARCHITECTURE.md` § Mode ownership](.agents/ARCHITECTURE.md#mode-ownership).

### Optional front door

| Command | Use this when… | Boundary |
|---|---|---|
| `/atlas` | You want one free-form Atlas request classified, previewed, and approved before its first dispatch. | It selects one owner or asks one material question; it does not inspect vault state, write, or chain workflows. |

### Bring evidence in

| Command | Use this when… | Use something else when… |
|---|---|---|
| `/atlas-source` | You want to check whether a specific URL is sourced, or ingest a known URL, file, or repository. | You want discovery from a defined feed or query → `/atlas-acquire`. |
| `/atlas-acquire` | You want to discover and ingest sources from a defined feed, inbox, watchlist, or query. | You already know the exact item → `/atlas-source`. It is not an open-ended web crawler. |

### Connect evidence to topics

| Command | Use this when… | Use something else when… |
|---|---|---|
| `/atlas-route` | A stored source is unrouted, linked to the wrong topics, or needs routing reviewed. | You need to create or update a topic answer → `/atlas-research` or `/atlas-refresh`. |
| `/atlas-index` | You need to promote vocabulary or a topic, or repair a registry or index. | You are doing routine ingestion, routing, research, or refresh work. |

### Create, update, or read answers

| Command | Use this when… | Use something else when… |
|---|---|---|
| `/atlas-research` | You want to create a durable topic answer, or deliberately rebuild one, from evidence already in the vault. | An existing topic only needs newly linked evidence applied → `/atlas-refresh`. |
| `/atlas-refresh` | An existing topic is `dirty` or `blocked` because linked evidence is waiting to be applied. | You are creating a new topic or rebuilding it from scratch → `/atlas-research`. |
| `/atlas-answer` | You want to read a topic with a freshness check. | The topic needs updating; refresh `dirty` or `blocked` topics first. |

### Check health or change schema

| Command | Use this when… | Use something else when… |
|---|---|---|
| `/atlas-audit` | You want a read-only health report before deciding what to fix. | You already know the required repair → `/atlas-index`, or the schema must change → `/atlas-migrate`. |
| `/atlas-migrate` | You need to move existing instance data to a declared schema version. | You are doing normal ingestion, research, routing, or refresh work. |

`atlas-core` contains shared contracts for these workflows; it is not a user command.

### Typical workflows

`/atlas` is optional at the start of any workflow below: it delegates the first named effect to one expert owner. Direct commands remain the shortest expert path.

| Goal | Workflow |
|---|---|
| Add a known source | `/atlas-source` → refresh any topic marked `dirty` → `/atlas-answer` |
| Discover sources from a defined feed or query | `/atlas-acquire` → refresh affected topics → `/atlas-answer` |
| Create a durable topic from evidence already in the vault | `/atlas-research` → `/atlas-answer` |
| Correct source-to-topic links | `/atlas-route` → refresh any newly `dirty` topics → `/atlas-answer` |
| Check and repair instance health | `/atlas-audit` → `/atlas-index` for registry/index repairs, or `/atlas-migrate` for schema changes |

`/atlas-answer` does not refresh automatically. If it reports a topic as `dirty` or `blocked`, run `/atlas-refresh` and then ask again.

## Instance provision

`scaffold/` contains empty starting state for new instances. It is copied during instance creation; it is not the app implementation or a deployment package.

| Class | What belongs here | What provision does |
|---|---|---|
| **product_owned** | Framework files authored in this package, such as `.agents/ARCHITECTURE.md` | Copies them on create; `sync-framework` replaces the instance snapshot. |
| **seed_once** | Empty starting templates under `scaffold/` | Copies them only when creating an instance. |
| **instance_owned** | Living sources, topics, passes, registries, and other instance data | Never overwrites or re-seeds them. |

An already-existing `vault://atlas/todos/` tree is optional unmanaged user data, not a scaffold class. Provision, sync, and check neither seed, require, inspect, migrate, nor delete it.

```bash
python3 scripts/atlas-instance.py create --name <id>
python3 scripts/atlas-instance.py sync-framework --name <id>
python3 scripts/atlas-instance.py check
```

Use `--instances-root` when the default instance location does not apply. See [`scaffold/README.md`](scaffold/README.md) and [`scaffold/MANIFEST.json`](scaffold/MANIFEST.json) for details.

## Vault binding

Atlas workflows always use `vault://atlas/…`. The active profile selects the storage connector, such as a local filesystem, object store, or remote API. Open this package as the agent project so its skills and commands are discovered; do not install them into host-global agent configuration.

## Deployment boundary

Deploying the product and creating an instance are separate operations. Deploy artifacts may include runtime code and product harness contracts, but never bound-instance research data.
