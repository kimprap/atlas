# Atlas

Atlas captures explicit URLs as durable Markdown summaries and answers or researches named topics from related vault summaries. This repository is the product package; living research belongs in a bound instance reached through `vault://atlas/…` and the active connector profile.

## Use Atlas

Open this package as the agent project, bind the intended instance profile, and use the sole public behavior entrypoint:

```text
/atlas-ask <plain-language goal>
```

`/atlas-ask` classifies one request to one internal owner and mode:

| Owner | Modes |
|---|---|
| `atlas-source` | `presence`, `ingest`, `resummarize`, `promote`, `reroute` |
| `atlas-research` | `answer`, `research`, `refresh`, `create` |
| `atlas-maintain` | `audit`, `repair`, `migrate` |

Read-only `presence`, `answer`, and `audit` run after classification and any necessary material clarification without an approval overview. Every write-capable mode receives one unchanged approval boundary before its owner runs:

```markdown
## Goal
<one concise interpretation of the unchanged request>

## Effect
<selected owner and mode; maximum logical write boundary; exact targets remain owner-gated>

## Approval
Reply **approve** to start.
```

A changed goal, effect, owner, mode, safety boundary, or material answer requires a new overview. Approval is dispatch authority only; it is not a profile, credential, transaction, recovery, deployment, or instance-sync grant. Migration preview and commit are separate candidate-bound invocations.

| Goal | Example |
|---|---|
| Check a source without writing | `/atlas-ask is https://example.com/report already sourced?` |
| Ingest explicit URLs | `/atlas-ask ingest https://example.com/report` |
| Answer a topic without writing | `/atlas-ask answer the compiler tooling topic` |
| Research a topic | `/atlas-ask research the compiler tooling topic` |
| Inspect a named structural concern | `/atlas-ask audit the TOPICS registry structure` |

Answer mode never refreshes. If a topic is dirty, Atlas returns its managed content only as explicitly stale/no-write with pending edge IDs. Approved research may refresh in process, re-inspect, and publish only after the topic is current with zero pending edges.

Behind the entrypoint:

```text
/atlas-ask
  → one same-agent owner + mode
  → scripts/atlas_tool.py generated CLI
  → deterministic domain code + active connector
  → vault://atlas/ bound instance
  → one seven-field owner result
```

The canonical framework contract is [`.agents/ARCHITECTURE.md`](.agents/ARCHITECTURE.md). It defines classification, write boundaries, state roles, recovery, and migration rules. Owner procedures use [the agent CLI recipes](.agents/skills/atlas-core/assets/agent-cli-recipes.md) and never load helper owners.

## Product package versus instance

| Surface | Contains |
|---|---|
| This repository | Agent contracts, three internal owners, runtime code, empty scaffold templates, and provision tooling |
| Bound instance | Living sources, registries, topics, passes, runs, and the synced architecture snapshot |
| `scaffold/` | Empty seed-once state for new instances only |

Never store living research, instance credentials, or connector secrets in this repository. Deploying the product, provisioning an instance, and synchronizing an existing instance are separate effects.

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
.agents/ARCHITECTURE.md                           canonical framework intent
.agents/commands/atlas-ask.md                     byte-thin public command
.agents/skills/atlas-ask/SKILL.md                 sole classifier
.agents/skills/atlas-ask/owners/{atlas-source,atlas-research,atlas-maintain}/
.agents/skills/atlas-core/assets/agent-cli-recipes.md
scripts/atlas_cli.py                              shared strict JSON/envelope seam
scripts/atlas_tool.py                             generated operation catalog and CLI
```

Discover lifecycle operations with `python3 scripts/atlas_tool.py capabilities`; use `capabilities --all` to inspect internal primitives and audience metadata. Family commands consume one operation-args object. Low-level `call --input` consumes `{"version":2,"op":"<literal>","args":{…}}`; responses contain exactly `version`, `ok`, `op`, `disposition`, `result`, `findings`, and `recovery`.