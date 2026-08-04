# Atlas

Atlas turns source evidence into current, traceable Markdown topic answers. This repository is the product package; living research belongs in a bound instance reached through `vault://atlas/…`.

## Use Atlas

Open this package as the agent project, bind the intended instance profile, then use the single public entrypoint:

```text
/atlas-ask <plain-language goal>
```

Atlas classifies the request, asks for any material choice, shows the maximum logical effect for approval, and dispatches one internal workflow owner. Former expert-specific commands are no longer public entrypoints.

| Goal | Example |
|---|---|
| Check or ingest a known source | `/atlas-ask ingest https://example.com/report` |
| Discover bounded sources | `/atlas-ask discover at most 10 sources from this feed` |
| Reroute sources | `/atlas-ask reroute source abc123` |
| Answer a current topic | `/atlas-ask answer the compiler tooling topic` |
| Research or rebuild a topic | `/atlas-ask rebuild the compiler tooling topic` |
| Apply pending evidence | `/atlas-ask refresh the compiler tooling topic` |
| Audit Atlas state | `/atlas-ask audit registry and source quality` |
| Promote vocabulary or create a topic shell | `/atlas-ask promote the term deterministic replay` |
| Run an explicit schema migration | `/atlas-ask migrate the declared Markdown scope` |

Behind the entrypoint:

```text
/atlas-ask
  → one approved internal Workflow Owner
  → scripts/atlas_tool.py
  → deterministic domain code + active connector
  → vault://atlas/ bound instance
```

The canonical agent contract is [`.agents/ARCHITECTURE.md`](.agents/ARCHITECTURE.md). It defines owner mapping, write boundaries, state roles, recovery, and migration rules.

## Product package versus instance

| Surface | Contains |
|---|---|
| This repository | Agent contracts, internal owners, runtime code, empty scaffold templates, and provision tooling |
| Bound instance | Living sources, registries, topics, passes, runs, and the synced architecture snapshot |
| `scaffold/` | Empty seed-once state for new instances only |

Never store living research, instance credentials, or connector secrets in this repository. Deploying the product and provisioning an instance are separate operations.

## Provision an instance

```bash
python3 scripts/atlas-instance.py create --name <id>
python3 scripts/atlas-instance.py sync-framework --name <id>
python3 scripts/atlas-instance.py check --name <id>
```

Use `--instances-root` when the default instance location does not apply. `sync-framework` updates product-owned files only; it never re-seeds living state.

## Develop the framework

Key surfaces:

```text
.agents/ARCHITECTURE.md                 canonical framework intent
.agents/commands/atlas-ask.md           thin public command
.agents/skills/atlas-ask/SKILL.md       orchestrator
.agents/skills/atlas-ask/owners/        internal workflow owners
.agents/skills/atlas-core/              deterministic contracts and schemas
scripts/atlas_*.py                      provider-neutral runtime
scaffold/                               empty instance templates
```

When durable behavior changes: update the architecture, affected contracts/owners/code/checks, sync the intended instance snapshot, and run the instance check.
