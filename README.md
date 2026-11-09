# Atlas

Atlas is an omp plugin that reads the web sources you name, stores one checked summary per source with word-for-word quotes, and searches and answers from those summaries. It runs on your machine, keeps its data in a local SQLite store per profile, and asks before a change you did not ask for in so many words and before any large paid batch.

## Use

Ask in an omp session; the `atlas-ask` skill turns the request into one Atlas command and shows the result, any decision Atlas needs from you, and what to do next:

```text
Is Atlas set up?
Add https://example.com/report to Atlas.
What do my sources say about compiler caching?
```

The first time, Atlas replies that it is not set up and points to `atlas-init`, which writes `~/.config/atlas/config.toml` and the model roles with one approval.

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
