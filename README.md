# Atlas

Atlas is an omp plugin that reads the web sources you name, stores one checked summary per source with word-for-word quotes, and searches and answers from those summaries. It runs on your machine, keeps its data in a local SQLite store per profile, and asks before a change you did not ask for in so many words and before any large paid batch.

## Use

Ask in an omp session; the `atlas-ask` skill turns the request into one Atlas command and shows the result, any decision Atlas needs from you, and what to do next:

```text
Is Atlas set up?
Add https://example.com/report to Atlas.
What do my sources say about compiler caching?
```

The first time, Atlas replies that it is not set up and points to `atlas-init`. Ask "Set up Atlas." and `atlas-init` lists every write in one approval question: the profile in `~/.config/atlas/config.toml` (`main` unless you name another, with its store `~/.local/share/atlas/<profile>.db`, judge `jev` unless you choose `opus`, the default limits and confirm settings, and the default price rows for the cost estimates), `default_profile = "main"` (changed from `smoke` when an earlier setup made `smoke` the default), the store itself, and the five `atlas_*` model roles in your host config (on omp, `modelRoles` in `~/.omp/agent/config.yml`; when that file is a link, the change lands in the linked repository and committing it is yours). The same question names the closing test search and its paid calls: one `find` through the real rerank path. On your answer it makes the approved writes, shows `status`, runs the test search and reports which models answered and which fallback is active; with judge `jev` and no key in place it waits, offering Opus for the profile instead. It keeps every other value already saved and never sets the monthly cap; add `cap_usd = <USD>` to the profile yourself to set one. Ask "Run the test search." to run it again on a profile already set up.

For judge `jev`, put the line `OPENROUTER_API_KEY=<your OpenRouter key>` in `~/.config/atlas/openrouter.env` yourself and run `chmod 600` on it; Atlas reads that file only at mode 600 and never writes or shows it. To raise GitHub's limit when adding repos, set `GITHUB_TOKEN` (else `GH_TOKEN`) in the environment omp runs in; Atlas sends it only to `api.github.com` and never writes, loads or shows it.

Behind the skill is one CLI:

```text
python3 "$(realpath skill://atlas-ask)/cli.py" <command> [<action>] [--redo|--reread|--wide|--detail] < body.json
```

Its ten commands are `status`, `add`, `inbox`, `find`, `ask`, `topic`, `plan`, `note`, `archive` and `restore`. Each reads one JSON object on stdin and writes one JSON line with `ok`, `op`, `result`, `problems`, `next` and `decisions`; the exit code says done (0), failed (1), bad input (2), not set up (3) or needs a decision (4).

## Install

```bash
omp plugin install github:kimprap/atlas#v2.0.0   # a released version
omp plugin link ~/dev/atlas                      # a live checkout
```

Python 3.11 or newer; no other dependency.

## Develop

- Contract: [`.agents/ARCHITECTURE.md`](.agents/ARCHITECTURE.md); working conventions: [`.agents/AGENTS.md`](.agents/AGENTS.md).
- Tests: `python3 -m unittest discover -s tests -t .`
- Setup after cloning: `python3 tools/release/release.py setup` (sets the pre-push hook that tags releases).

Atlas v1 (Markdown vault, `/atlas-ask` owners) is kept at tag `v1`.
