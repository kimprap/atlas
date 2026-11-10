---
description: Atlas omp plugin — layout, contracts, and working conventions.
alwaysApply: true
---

# Atlas

This repository is the omp plugin `atlas` (v2). The `atlas-ask` skill is the front door; it calls one CLI, `skills/atlas-ask/cli.py`, whose core decides everything that happens to data and keeps one SQLite store per profile under `~/.local/share/atlas/`. `atlas-init` is the only writer of `~/.config/atlas/config.toml`. v1 is history at tag `v1`; nothing from it is carried except link cleanup (`atlas/core/links.py`) and strict JSON input (`atlas/core/reply.py`).

## Contract discovery

| Task | Read first |
| - | - |
| Change layout, dependency direction, ownership, the CLI call or reply, approvals, ports, configuration, store, commands or release | `.agents/ARCHITECTURE.md` |
| Need the full design, a stage's scope or an acceptance check | `.agents/artifacts/atlas-v2-spec.md` (the approved specification) |
| Need the rationale behind a decision | `docs/adr/INDEX.md`, then only the matching ADR |
| Work inside an established module | that module and its tests only |

ADRs explain why and never override `.agents/ARCHITECTURE.md`. Change the architecture first, then code, skills and tests.

## Layout

```text
package.json                 plugin metadata (shipped)
skills/atlas-ask/            front door skill, cli.py, atlas/ package (shipped)
skills/atlas-init/           setup skill (shipped)
rules/                       dev-research rule (shipped)
tests/                       unittest suite (repo-only)
tools/                       release, quality and calibration tools (repo-only)
.githooks/pre-push           starts the release run after a push to main
.agents/                     this file, ARCHITECTURE.md, plans, artifacts
docs/adr/                    decision records
```

Only `package.json`, `skills/` and `rules/` ship; everything else is repo-only.

## Working conventions

- Python 3.11+ standard library only; no dependency install.
- Core (`skills/atlas-ask/atlas/core/`) names no host, repo or host setting and never imports `adapters` or `host`.
- Run the suite with `python3 -m unittest discover -s tests -t .`; one module with `python3 -m unittest tests.<module>`.
- After cloning, run `python3 tools/release/release.py setup` once to set the hooks path.
- Make surgical changes; add no aliases, shims or compatibility paths.
- Ask separately before a push, tag, release, plugin install, a write under `~/.config/atlas/`, `~/.local/share/atlas/` or `~/.local/state/atlas/`, or a paid model call.
- The stage 5 `eval` library build is deferred by the user until every other stage is complete (or as late as possible) and not yet run; do not run or propose `quality.py build-library --yes` before then unless asked, and see `.agents/ARCHITECTURE.md` "Quality check" for the steps and the GitHub token setup.
- Run a live omp smoke session as `ATLAS_PROFILE=<profile> omp -p --mode json --tools read,bash`: without `--tools` the agent may call `cli.py` through its eval tool, which drops `ATLAS_PROFILE` and opens the real `main` store (stage 5: one paid add wrote two `main` rows).
- Never touch the frozen v1 vault except the read-only calibration and quality imports.
