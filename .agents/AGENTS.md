---
description: Atlas omp plugin — commands, boundaries, structure and pointers.
alwaysApply: true
---

# Atlas

This repository is the omp plugin `atlas` (v2): the `atlas-ask` skill calls one CLI, `skills/atlas-ask/cli.py`, whose core decides everything that happens to data and keeps one SQLite store per profile under `~/.local/share/atlas/`. Python 3.11+ standard library only; no dependency install.

## Commands

- Full check: `python3 -m unittest discover -s tests -t .`; one module: `python3 -m unittest tests.<module>`.
- After cloning, run `python3 tools/release/release.py setup` once to set the hooks path.
- Live omp smoke session: `ATLAS_PROFILE=<profile> omp -p --mode json --tools read,bash`. Without `--tools` the agent may call `cli.py` through its eval tool, which drops `ATLAS_PROFILE` and opens the real `main` store.

## Boundaries

- Ask separately before a push, tag, release, plugin install, a write under `~/.config/atlas/`, `~/.local/share/atlas/` or `~/.local/state/atlas/`, or a paid model call. A push to `main` starts the release run, which tags and publishes.
- `atlas-init` is the only writer of `~/.config/atlas/config.toml`.
- Never touch the frozen v1 vault except the read-only calibration and quality imports and stage 9's read-only use of its links.

## Structure

- Only `package.json`, `skills/` and `rules/` ship; everything else is repo-only.
- `.scratch/atlas-v2/` holds the v2 design tickets and reviews; the specification cites them as the authority for their decisions.

## Conventions

- Core (`skills/atlas-ask/atlas/core/`) names no host, repo or host setting and never imports `adapters` or `host`.

## Pointers

- When you change layout, dependency direction, ownership, the CLI call or reply, approvals, ports, configuration, store, commands or release, read `ARCHITECTURE.md` first and change it before code, skills and tests.
- When you need a stage's scope, the build order or an acceptance check, read `.agents/artifacts/atlas-v2-spec.md`.
- When you need the reason behind a decision, run `records.py index decision-record`, then `records.py show` only the matching one; decision records explain why and never override `ARCHITECTURE.md`.
