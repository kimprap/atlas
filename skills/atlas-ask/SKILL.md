---
name: atlas-ask
description: >
  Front door to Atlas, the user's local store of web sources with checked
  summaries and word-for-word quotes. Use when the user asks to summarize a
  link or page, or to add, keep or re-read a link in Atlas; when the user asks
  whether Atlas is set up; to search or ask their Atlas sources; or to work with
  Atlas topics, plans, notes, the inbox or archived items.
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

## Build the body

- `add` ("Summarize this link", "Add this to Atlas"): `{"items": [{"link": "<link>"}, ...]}`, one item per link the user named. When the user gives the page text itself, put it in the item as `"text"`; Atlas then stores that text and does not read the link.
- `add --reread` ("Re-read this source"): `{"items": [{"link": "<link>"}, ...]}` with links Atlas already stores.
- `inbox add` ("Keep this for later"): `{"add": ["<link>", ...]}`. `inbox list`: `{}`.
- Approval: when the user's own message asks for this change and names its links, add `"approval": {"by": "request", "words": "<the user's message, verbatim>"}`. Never write that approval from your own words or from an earlier message; without it, Atlas asks.

## Follow a choice

After the user picks a decision option or a Next line, follow its `then`:

- `{"resend": {...}}`: run the same command again. For a decision option, start from the body you sent and set each field the resend gives (its `items` replace yours). When the resend holds an `approval`, it replaces yours: add `"words": "<the user's reply, verbatim>"` to it. When it holds none, remove a `"by": "confirm"` approval from the body, because it answered the earlier question, not this one; keep a `"by": "request"` approval. Atlas asks again when the new body needs a confirm. For a Next line, send only the resend's fields as a new change, with no earlier approval. A `mode` in a resend is the flag to run with (`"reread"` is `--reread`); leave `mode` out of the body.
- `{"skill": "<name>"}`: run that skill.
- `{"stop": true}`: send nothing more.

## Show the reply

The reply holds `ok`, `op`, `result`, `problems`, `next` and `decisions`. The exit code says done (0), failed (1), bad input (2), not set up (3) or needs a decision (4).

1. Show each `result.needs_action` item first, whatever the exit code: its `what`, then its `fix` lines, then its `where` when set. On exit 3, lead the items with one sentence saying Atlas is not set up.
2. Say the outcome in plain words from the rest of `result`. For `status`, that is the `summary` line as given (it names the profile, the source and inbox counts, the judge and the Atlas version), saying Atlas is ready when the exit is 0 and no item was shown; show `detail` only when it is not null. For `add`, give each `items` entry's link and `result`, with its title, claim count and any flags or copies it lists.
3. Show each `problems` item as its `field` and `problem`.
4. Show each `decisions` item's `question` with its options' labels, then stop for the user's choice.
5. End with a Next line per `next` item, using its `label`. A `then` of `{"skill": "atlas-init"}` reads "run `atlas-init`".

Done when every part of the reply is shown and the answer ends with its Next lines. Leave Atlas settings and data to the CLI and `atlas-init`; never write them yourself.
