# Atlas app

Product package for the Atlas research framework: agent skills, slash commands, Markdown reducer contracts, empty vault **scaffold**, instance provision, and future deployable runtime.

Living research state is **not** stored here. It lives on a **bound instance** and is accessed only as `vault://atlas/…` through the active connector/profile. The same package is meant to run under local agents, CI, or serverless — only the vault binding changes.

Framework contract (authoring SO): [`.agents/ARCHITECTURE.md`](.agents/ARCHITECTURE.md). Instance snapshots land at `vault://atlas/ARCHITECTURE.md` via provision.

## Layout

```text
.agents/
  AGENTS.md           # always-on product map
  ARCHITECTURE.md     # product_owned framework SO
  rules/              # ownership / freestyle / skill-surface seams
  commands/           # thin /atlas-* stubs → skill://…
  skills/             # entry skills + atlas-core + digest shim
  plans/
scaffold/             # seed-once templates + MANIFEST
scripts/atlas-instance.py
```

## Slash commands

Commands are the control plane for vault work. Stubs under `.agents/commands/` load `skill://atlas-*` when the agent project root is this package (or a parent that contains it).

### How to use

1. Open the agent with **this product package** as cwd/project root.
2. Bind a vault profile so `vault://atlas/…` resolves to the intended instance.
3. Invoke `/atlas-<name>` for the intent below instead of freestyle vault edits.
4. Framework/product code changes use normal repo workflows — not these commands.

Full write-sets and invariants: [`.agents/ARCHITECTURE.md` § Slash commands](.agents/ARCHITECTURE.md#slash-commands).

### When to use (by intent)

#### Bring evidence in

| Command | Use when | Skip when |
|---|---|---|
| `/atlas-source` | Explicit URLs, files, or repos | Open-ended discovery |
| `/atlas-acquire` | Bounded feed/inbox/watchlist/query | Unconstrained crawl; single known URL → source |

#### Connect evidence to topics

| Command | Use when | Skip when |
|---|---|---|
| `/atlas-route` | Re-route a source or bounded range | Writing topic answers |
| `/atlas-index` | Explicit vocab/topic promotion or registry repair | Routine acquire/research |

#### Produce or refresh answers

| Command | Use when | Skip when |
|---|---|---|
| `/atlas-research` | Create/rebuild a durable topic from vault sources | Pending-edge apply only → refresh |
| `/atlas-refresh` | Dirty/blocked topic; apply pending edges | Answering without a persisted pass |
| `/atlas-answer` | Freshness is `current` | Dirty/refreshing/blocked (halt; refresh first) |

#### Maintain health and schema

| Command | Use when | Skip when |
|---|---|---|
| `/atlas-audit` | Health report (read-only) | You already intend a known mutation |
| `/atlas-migrate` | Explicit schema migration | Normal research/acquire/refresh |

#### Compatibility

| Command | Use when | Skip when |
|---|---|---|
| `/digest` | Legacy entry that must forward to `/atlas-*` | New work |

`atlas-core` is shared contracts only (not a user command).

### Typical flows

| Intent | Flow |
|---|---|
| Known URL → answer | `/atlas-source` → `/atlas-refresh` if dirty → `/atlas-answer` |
| Watchlist batch | `/atlas-acquire` → refresh dirty topics as needed |
| New durable topic | Sources in vault → `/atlas-research` (vault-only default) |
| Registry health | `/atlas-audit` → `/atlas-index` or `/atlas-migrate` if needed |

## Instance provision

`scaffold/` is seed-once empty state for new instances — not the app implementation and not a deploy package.

| Class | Authored in | Behavior |
|---|---|---|
| **product_owned** | Product package (e.g. `.agents/ARCHITECTURE.md`) | Injected on create as instance `ARCHITECTURE.md`; overwritten by `sync-framework` |
| **seed_once** | `scaffold/**` | Copied only on create |
| **instance_owned** | Bound instance only | Never re-seeded by provision |

```bash
python3 scripts/atlas-instance.py create --name <id>
python3 scripts/atlas-instance.py sync-framework --name <id>   # or --all
python3 scripts/atlas-instance.py check
```

Override instance parent with `--instances-root` when the default binding layout does not apply. Details: [`scaffold/README.md`](scaffold/README.md), [`scaffold/MANIFEST.json`](scaffold/MANIFEST.json).

## Vault binding

Workflows use `vault://atlas/…`. The active profile selects a connector (local filesystem, object store, remote API, etc.). Open this package as the agent project so skills and commands auto-discover. Do not install product skills into host-global agent config outside this package.

## Deploy (later)

Runtime packaging is separate from instance bootstrap. Deploy artifacts should include runtime + skills/contracts — not bound-instance research trees.
