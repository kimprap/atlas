---
name: atlas-init
description: >
  Set up Atlas, the user's local store of web sources: its settings file, its
  store and the host's model roles, with one approval. Use when an Atlas reply
  says Atlas is not set up or names `atlas-init`, or when the user asks to set up
  or configure Atlas or one of its profiles.
---

# atlas-init

Set up one Atlas profile with one approval: gather what is missing, ask once naming every write, then on the user's answer make the approved writes and show `status`. Nothing is written before that answer, because the question is the user's only chance to see each change.

The key stays the user's: never create, change, remove, read or show `~/.config/atlas/openrouter.env` or the value of `OPENROUTER_API_KEY`. When `status` reports a problem with that file, pass on its fix lines so the user places the key themselves.

## 1. Choose the profile and judge

- Profile: the one the user names, else `ATLAS_PROFILE`, else `smoke`. Use a name of letters, digits, `_` and `-` only; for any other name, say so and stop.
- Read `~/.config/atlas/config.toml` if it exists. Keep every value saved there; this skill only adds what is missing.
- Judge: the profile's saved `judge`, else the one the user names (`jev` or `opus`), else `jev`.
- Store: the profile's saved `store`, else `~/.local/share/atlas/<profile>.db`.

Done when profile, judge and store are known; ask nothing here.

## 2. Check what is missing

Run `status` once:

```bash
python3 "$(realpath skill://atlas-ask)/cli.py" status <<'JSON'
{"profile": "<profile>"}
JSON
```

- Exit 1, or any `problems` item: show each problem and stop.
- Role items are the `result.needs_action` items whose `what` reads `Role <role> is missing`. Each holds the host's own `fix` lines for that role and the file `where` they go into. Merge them into one role block: a line that repeats across items, such as the block header, appears once, followed by every item's own lines in item order.
- When the role items share one `where`, check whether it is a link with `realpath`; a resolved path that differs from `where` is the file the link points to.
- Nothing to write when the settings file already holds the profile with its `store` and `judge`, and there is no role item: show the reply as "5. Show the result" says, and stop; ask nothing.

Done when the reply is read and the role block, if any, is merged.

## 3. Ask once

Send one message that lists every write, then ends with one question. Leave out an item with nothing to write.

1. Settings file `~/.config/atlas/config.toml`, with the exact lines to add:
   - a new file is exactly:

     ```toml
     default_profile = "smoke"

     [profiles.<profile>]
     store = "<store>"
     judge = "<judge>"
     ```

   - an existing file keeps every line; add `default_profile = "smoke"` as the first line only when the file has no `default_profile` (this Atlas build keeps `smoke` the default whatever profile is set up), add the `[profiles.<profile>]` table at the end when it is missing, and add a missing `store` or `judge` line directly under that table's header.
2. When `<store>` does not exist yet: the store `<store>` with its `-wal` and `-shm` files, which the closing `status` creates.
3. When there are role items: the merged role block, shown exactly, into their `where`. When `where` is a link, say which file it points to, that the change lands in that file's repository, and that committing it stays with the user. A role item with no `where`, or whose fix lines are plain sentences rather than file lines, is no write: list its role and model for the user to add by hand.

When the judge is `jev`, always add, as the user's own step and not a write of yours: put the line `OPENROUTER_API_KEY=<your OpenRouter key>` in `~/.config/atlas/openrouter.env`, then run `chmod 600 ~/.config/atlas/openrouter.env`. Say that you never read, write, check or show the key; the closing `status` checks the file.

End the message with the one question: "May I make these writes? Reply yes for all of them, or name the ones to make." Then stop and wait for the answer. Done when the question is sent and nothing has been written.

## 4. Write what was approved

Make only the writes the answer approves, in this order:

1. Settings file: create `~/.config/atlas/` if needed, then write or edit the file with exactly the lines shown.
2. Role lines: edit the resolved file `where` points to, in place, so a link stays a link. Keep every line already there; add each line of the merged role block that the file does not have yet, under the existing block header line it belongs to, with the indentation shown. Commit nothing.
3. When the store was approved, or already exists, run `status` once more with the same call as in "2. Check what is missing"; it opens the store and creates it on first use. Without that approval, skip `status` and say it would create the store.

Done when each approved write is made and checked: the settings file and the role file read back with the shown lines, and the closing `status` replied.

## 5. Show the result

Show the closing `status` reply: each `result.needs_action` item first (its `what`, then its `fix` lines and its `where`), then `result.summary`, then each `problems` item, then one Next line per `next` item's `label`. For an item about the judge's key file, say that the user applies its fix lines themselves and that you never read, write or show the key. Name any write the user did not approve as not made. Done when the answer ends with the Next lines.
