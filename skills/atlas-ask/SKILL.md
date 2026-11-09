---
name: atlas-ask
description: >
  Front door to Atlas, the user's local store of web sources with checked
  summaries and word-for-word quotes. Use when the user asks whether Atlas is set
  up, asks to add a link to Atlas, to search or ask their Atlas sources, or to
  work with Atlas topics, plans, notes, the inbox or archived items.
---

# atlas-ask

Turn the user's request into one Atlas command, run the Atlas CLI once, and show its reply. The CLI decides everything that happens to Atlas data; this skill only passes the request and shows the answer.

## Call the CLI

Run in bash, with one JSON object as the body on stdin:

```bash
python3 "$(realpath skill://atlas-ask)/cli.py" <command> [<action>] [--detail|--redo|--reread|--wide] <<'JSON'
{}
JSON
```

- Pick the command from the request: `status` (for example "Is Atlas set up?"), `add`, `inbox`, `find`, `ask`, `topic`, `plan`, `note`, `archive` or `restore`.
- Send `{}` when the command takes no fields; the CLI reads exactly one JSON object and rejects anything else as bad input.
- Run the call once; it is done when the command exits and its one stdout line is a JSON reply.

## Show the reply

The reply holds `ok`, `op`, `result`, `problems`, `next` and `decisions`. The exit code says done (0), failed (1), bad input (2), not set up (3) or needs a decision (4).

1. Say the outcome in plain words from `result`. On exit 3, say that Atlas is not set up and show each `result.needs_action` item: its `what`, then its `fix` lines.
2. Show each `problems` item as its `field` and `problem`.
3. Show each `decisions` item's `question` with its options' labels, then stop for the user's choice.
4. End with a Next line per `next` item, using its `label`. A `then` of `{"skill": "atlas-init"}` reads "run `atlas-init`".

Done when every part of the reply is shown and the answer ends with its Next lines. Leave Atlas settings and data to the CLI and `atlas-init`; never write them yourself.
