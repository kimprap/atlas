# Atlas

The omp plugin `atlas`: the `atlas-ask` skill calls one CLI, `skills/atlas-ask/cli.py`. Python 3.11+ standard library only; never add a dependency.

## Commands

- Full check, from the repository root: `python3 -m unittest discover -s tests -t .` and `python3 ~/.omp/plugins/node_modules/dotagents/skills/craft-skill/scripts/check_skills.py skills`; the release run gates on both.
- One module: `python3 -m unittest tests.<module>`.
- After cloning, run `python3 tools/release/release.py setup` once to set the hooks path.
- Live omp smoke session: `ATLAS_PROFILE=<profile> omp -p --mode json --tools read,bash`. Without `--tools` the agent may call `cli.py` through its eval tool, which drops `ATLAS_PROFILE` and opens the real `main` store.

## Boundaries

- Ask separately before a tag, release, plugin install, a write under `~/.config/atlas/`, `~/.local/share/atlas/` or `~/.local/state/atlas/`, or a paid model call such as a live omp session.
- `atlas-init` is the only writer of `~/.config/atlas/config.toml`.
- Open the frozen v1 vault `~/dev/atlas-v1-vault/` read-only, and only to import from it; never write it.

## Source of truth and structure

- Only `package.json`, `skills/` and `rules/` ship; `tools/`, `tests/` and the rest are repo-only.
- When a change touches what the canonical contract states, change the contract first, then code, skills and tests.

## Conventions

- Core (`skills/atlas-ask/atlas/core/`) never imports `atlas.adapters` or `atlas.host` and names no host, repo or host setting; `tests/test_boundary.py` checks the imports.
