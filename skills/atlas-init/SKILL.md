---
name: atlas-init
description: >
  Set up Atlas, the user's local store of web sources: its settings file, its
  store and the host's model roles, with one approval, then run one test search.
  Use when an Atlas reply says Atlas is not set up or names `atlas-init`, or when
  the user asks to set up or configure Atlas or one of its profiles, or to run
  Atlas's test search.
---

# atlas-init

Set up one Atlas profile with one approval: gather what is missing, ask once naming every write and the test search, then on the user's answer make the approved writes, show `status` and end with one test search. Nothing is written or searched before that answer, because the question is the user's only chance to see each change and each paid call. When there is nothing to write, ask nothing and run the test search straight away, so "Run the test search." on a profile already set up runs it.

The key stays the user's: never create, change, remove, read or show `~/.config/atlas/openrouter.env` or the value of `OPENROUTER_API_KEY`. When `status` reports a problem with that file, pass on its fix lines so the user places the key themselves.

## 1. Choose the profile and judge

- Profile: the one the user names, else `ATLAS_PROFILE`, else `main`. Use a name of letters, digits, `_` and `-` only; for any other name, say so and stop.
- Read `~/.config/atlas/config.toml` if it exists. Keep every value saved there; this skill only adds what is missing, and changes only the two lines "3. Ask once" names: `default_profile = "smoke"` when it sets up `main`, and the profile's `judge` when the user names the other judge.
- Judge: the one the user names (`jev` or `opus`, for example "use Opus for this profile"), else the profile's saved `judge`, else `jev`.
- Store: the profile's saved `store`, else `~/.local/share/atlas/<profile>.db`.
- Price rows: read `prices.default.toml` in this skill's folder (`"$(realpath skill://atlas-init)/prices.default.toml"`). Each `[prices."<model>"]` table there is one row with its four lines.
- Test question: `What do my sources say about <subject>?` when the user names a subject for the test search, else `What do my sources say?`.

Done when profile, judge, store, the default price rows and the test question are known; ask nothing here.

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
- Nothing to write when the settings file already holds the profile with its `store`, the chosen `judge`, every stage 3 setting and every confirm setting shown in "3. Ask once", its `default_profile` line needs no change, the file holds every default price row's `[prices."<model>"]` table, and there is no role item: ask nothing, and go to "5. Run the test search" with this `status` reply as the closing one.

Done when the reply is read and the role block, if any, is merged.

## 3. Ask once

Send one message that lists every write and the test search, then ends with one question. Leave out an item with nothing to write.

1. Settings file `~/.config/atlas/config.toml`, with the exact lines to add or change:
   - a new file is exactly the following, then every default price row with its four lines, in file order, each table after one blank line:

     ```toml
     default_profile = "main"

     [profiles.<profile>]
     store = "<store>"
     judge = "<judge>"
     max_page_tokens = 150000
     judge_concurrency = 8
     rethink = true
     near_copy = 0.90
     reread_days = 30
     reread_new_text = 0.05
     cap_warn = 0.80
     window_stop = 0.90

     [profiles.<profile>.confirm]
     add = "always"
     add_redo = "always"
     add_reread = "always"
     inbox_add = "always"
     follow = "always"
     unfollow = "always"
     plan_start = "always"
     ```

   - an existing file keeps every line and every saved value except the two changes below; add `default_profile = "main"` as the first line when the file has no `default_profile`, add the `[profiles.<profile>]` table at the end when it is missing, and add each missing line of that table shown above (`store`, `judge` and the stage 3 settings) directly under that table's header. Add the `[profiles.<profile>.confirm]` table at the end when it is missing, and each of its missing lines shown above directly under its header. Add each default price row whose `[prices."<model>"]` table the file lacks at the end, with its four lines; a row already there stays as it is.
   - Change of the default: when the profile is `main` and the file's line is `default_profile = "smoke"`, change that line to `default_profile = "main"`, and name it as a change: `default_profile` from `smoke` to `main`, so Atlas uses `main` wherever no profile is named. Any other `default_profile` stays as it is.
   - Change of the judge: when the user named a judge other than the profile's saved `judge`, change that line, and name it as a change from the saved judge to the named one.
   - Never write `cap_usd`: the monthly cap stays unset. Say the user may add `cap_usd = <USD>` under `[profiles.<profile>]` by hand to set one.
2. When `<store>` does not exist yet: the store `<store>` with its `-wal` and `-shm` files, which the closing `status` creates.
3. When there are role items: the merged role block, shown exactly, into their `where`. When `where` is a link, say which file it points to, that the change lands in that file's repository, and that committing it stays with the user. A role item with no `where`, or whose fix lines are plain sentences rather than file lines, is no write: list its role and model for the user to add by hand.
4. The test search, after the writes: one `find` for the test question on profile `<profile>`, through the real rerank path. Name its paid calls: one `atlas_query` rewrite call, and, only when stored sources match, one Jev request per matching source (at most 30) when the judge is `jev`, or one `atlas_rerank` call when the judge is `opus` or Jev fails. Say it adds one query record and one call record per paid call to the store, and that it waits for the user's key step when the judge is `jev` and the key is not in place.

When the judge is `jev`, always add, as the user's own step and not a write of yours: put the line `OPENROUTER_API_KEY=<your OpenRouter key>` in `~/.config/atlas/openrouter.env`, then run `chmod 600 ~/.config/atlas/openrouter.env`. Say that you never read, write, check or show the key; the closing `status` checks the file.

End the message with the one question: "May I make these writes and run the test search? Reply yes for all of them, or name the ones to make." Then stop and wait for the answer. Done when the question is sent and nothing has been written or searched.

## 4. Write what was approved

Make only the writes the answer approves, in this order:

1. Settings file: create `~/.config/atlas/` if needed, then write or edit the file with exactly the lines shown.
2. Role lines: edit the resolved file `where` points to, in place, so a link stays a link. Keep every line already there; add each line of the merged role block that the file does not have yet, under the existing block header line it belongs to, with the indentation shown. Commit nothing.
3. When the store was approved, or already exists, run `status` once more with the same call as in "2. Check what is missing"; it opens the store and creates it on first use. Without that approval, skip `status` and say it would create the store.

Done when each approved write is made and checked: the settings file and the role file read back with the shown lines, and the closing `status` replied.

## 5. Run the test search

Run it when the answer approved it or there was nothing to write, and the closing `status` exited 0 or listed only the judge's items. Otherwise say why it did not run and go to "6. Show the result".

- Jev first: when the judge is `jev` and the closing `status` lists an item about the judge (its key file, or no judge chosen), do not search. Say the test search waits for Jev, and give these two Next lines: put the key in place as that item's fix lines say, then ask "Run the test search."; or use Opus for this profile instead, by asking "Use Opus for profile <profile>." (this skill then changes the judge line on one approval). Go to "6. Show the result".
- Search once, with `original` the user's message verbatim:

  ```bash
  python3 "$(realpath skill://atlas-ask)/cli.py" find <<'JSON'
  {"profile": "<profile>", "question": "<test question>", "original": "<the user's message>"}
  JSON
  ```

- Exit 4: show each decision's `question` and its options' `label`s as the Next lines, and stop; resend nothing. Exit 1, 2 or 3: show its `problems` and `result.needs_action` items, and stop.
- Exit 0: run `status` once with `--detail` (the same call as in "2. Check what is missing", with `--detail` after `status`) to read `detail.roles`, the model each role uses. Then report:
  - Which models answered: the rewrite, `atlas_query` with its model from `detail.roles`, unless a `problems` item on `phrasings` says the rewrite failed (then say so, and that the question was searched as given; `result.question_as_searched` only shows that the test question differs from the user's message, and says nothing about the rewrite); the ranker, from `result.ranker`: Jev with its version (`model`) when `name` is `jev`, `atlas_rerank` with its `model` when `name` is `atlas_rerank`, none when `name` is `bm25`. When `result.sources` is empty, no stored source matched, so no ranker answered: say so, and name the profile's ranker, Jev or `atlas_rerank` with its model from `detail.roles`.
  - The active fallback: from each `problems` item on `ranker`, the fallback it names (`atlas_rerank` ranked the search when Jev failed; BM25 order when `atlas_rerank` failed); else, when the judge is `opus`, Opus (`atlas_rerank` with its model) in place of Jev for every search of this profile; else none, with `atlas_rerank` and its model as the fallback when Jev fails.
  - How many sources the search found.

Done when the test search ran and is reported, or the reason it did not run is given.

## 6. Show the result

Show the closing `status` reply: each `result.needs_action` item first (its `what`, then its `fix` lines and its `where`), then `result.summary`, then each `problems` item; then the test search's report from "5. Run the test search"; then one Next line per `next` item's `label` of the closing `status`, after any Next lines step 5 gave. For an item about the judge's key file, say that the user applies its fix lines themselves and that you never read, write or show the key. Name any write the user did not approve as not made. Done when the answer ends with the Next lines.
