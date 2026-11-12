---
name: atlas-ask
description: >
  Front door to Atlas, the user's local store of web sources with checked
  summaries and word-for-word quotes. Use when the user asks to summarize a
  link or page, or to add, keep, re-read or redo old summaries of a link in Atlas; when the user asks
  whether Atlas is set up; to search or ask their Atlas sources; or to work with
  Atlas topics, plans, notes, the inbox, archived items or repo citations.
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

- `add` ("Summarize this link", "Add this to Atlas"): `{"items": [{"link": "<link>"}, ...]}`, one item per link the user named. When the user gives the page text itself, put it in the item as `"text"`; Atlas then stores that text and does not read the link. To record which file of which repo relied on the sources (the `atlas-research` rule does this at the end of a research run), add `"cited_in": {"repo": "<owner/name>", "file": "<path from the repo root>"}`, with `"topics": [{"topic": "<topic name>", "version": <saved version number>}, ...]` for the topic versions it relied on, to the same `add`. Never add a `request` approval to an `add` with `cited_in`, and never write `join` yourself (only the resends of Atlas's own decisions carry it): Atlas always answers with one `confirm` decision that states the repo, the file, how many links and topic versions it would cite and, when 2 or more links must be read, the estimate and window use. Show that confirm and wait for the user's answer. A later `add` with the same repo and file replaces that file's citations.
- `add --reread` ("Re-read this source"): `{"items": [{"link": "<link>"}, ...]}` with links Atlas already stores.
- `add --redo` ("Redo old summaries", "Rebuild the summaries on the old rubric"): `{}` redoes every stored summary Atlas counts as older (its `status` Next says how many); `{"links": ["<link>", ...]}` redoes only the links the user named; `{"topic": "<topic name>"}` redoes only the sources a topic's saved versions cite that are older (name links or a topic, never both). Never add `force` yourself: Atlas offers it as the `already_current` decision's option when every named link, or every source a topic cites, is already on the current setup. Redo is always paid at scale, so never add a `request` approval to it: Atlas asks one confirm that states the count, an "about $… at list price" estimate and the window use. Show that confirm and wait for the user's answer before anything else; only the user's yes goes ahead.
- `inbox add` ("Keep this for later"): `{"add": ["<link>", ...]}`. `inbox list`: `{}`.
- `find` ("Which of my sources cover X?") and `ask` ("What do we know about X?"): `{"question": "<the question>", "original": "<the user's message, verbatim>"}`. Write `question` so it stands on its own: resolve a follow-up such as "what about the second one?" from the chat into what it means. Optionally add `"phrasings": ["<search phrasing>", ...]`, a few short keyword phrasings a source would use, and `"context": "<a few lines>"`: the goal, what the user already ruled out, the repo. `find` and `ask` change nothing but their query record and tally, so never add a `request` approval to them.
- `find --wide` ("Find everything that could matter for X", "Which of my sources are even near this?"): `{"brief": "<the brief, standing on its own>"}` with optional `"phrasings": [...]` and `"context": "<a few lines>"`, and no `question` or `original`. It asks Jev about every stored source, so it shows sources the keyword search misses; the reply's Next offers the rest, ordered by P, as a resend with `{"rest": true}`: send it only if the user asks for more. Like `find`, never add a `request` approval.
- `ask` for a catch-up ("What's new?", "What's new on <topic>?"): `{"whats_new": true}` for every followed topic or `{"topic": "<topic name>"}` for one, with no `question`. It searches each topic's brief for sources saved since its agreed version and answers only where there is news. It saves nothing and takes no `request` approval; a `window` or `cap` decision is shown like any other. When the user picks "save as the next version" for a topic, run `topic draft` for it and then `topic save`; when the user picks "nothing to save", run `topic nothing_to_save`.
- `note` ("Lean towards Simon Willison on agent skills", "Be careful with <who> on <subject>"): `{"who": "<who>", "subject": "<subject>", "lean": "towards" | "against", "reason": "<why>"}` with `"approval": {"by": "request", "words": "<the user's message, verbatim>"}`, as one call with no second confirm. `who` is an author or a publisher. When the user gives no reason, `reason` is the user's message, verbatim. The same call changes the note already held for that who and subject.
- `archive` ("Archive this link", "Archive my note on <who>", "Archive the topic <name>", "Archive the citations of <file> in <repo>") and `restore` ("Restore this link", "Restore my note on <who>", "Restore the topic <name>", "Restore the citations of <file> in <repo>"): `{"link": "<link>"}`, `{"note": {"who": "<who>", "subject": "<subject>"}}`, `{"topic": "<topic name>"}` or `{"citation": {"repo": "<owner/name>", "file": "<path from the repo root>"}}`, with the same `request` approval when the user's own message asks for it (for a citation, when it names both the repo and the file). Archiving hides a source from `find`, `ask` and `add` results, a note from answers, a topic from the catch-up and from matching, or a file's citations from the replies that name who cites a claim; restoring returns it (a citation restore brings back only the citations archived last, not the ones a later `add` replaced); nothing is deleted, and an archived topic keeps its versions and plans.
- Topics ("Which topics do I have?", "Follow the topic <name>", "Stop following <name>", "Nothing to save for <name>"): `topic list` takes `{}`; `topic follow` and `topic unfollow` take `{"name": "<topic name>"}`, with a `request` approval when the user's own message names the topic; `topic nothing_to_save` takes `{"name": "<topic name>"}` and no approval, because the user's pick of the "nothing to save" Next line is its confirm: it stores today's date as reviewed and clears the topic's marks, and makes no version.
- `topic create` ("Create a topic on X") and `plan save` (a research plan) start a plan; follow "Plan a topic" below, which runs Reconcile first. `topic create` takes `{"name": "<topic name>", "brief": "<what the topic is about, as the user said it>"}`; `plan save` takes `{"topic": "<topic name>", "text": "<the plan as you wrote it>", "items": [{"kind": "question" | "search" | "source" | "page", "text": "<the item>"}, ...], "review": <the review>}`. Both start a plan, so never add an approval to either: send both bodies with no approval, and each returns its own `plan_start` decision, which carry one and the same question. Show that one question; after the user's yes, resend `topic create` and then `plan save`, each with its own decision's `go` approval and the user's reply as `words`. A `plan save` for a topic that is not stored yet is answered with its decision first, so the user is asked once before either is saved. `review` is `{"status": "complete" | "not_cross_checked", "text": "<the reviewed text>", "run": "<run>", "reviewers": ["<model>", ...], "changes": "<what the review changed, as given>", "diff": "<diff>" (optional), "reason": "<why not>" (only when not cross-checked)}`; "Run Reconcile" below says how to fill it. Atlas stores the reviewed `text`, never the plan text beside it.
- `topic draft` ("Draft what we know about <name>"): `{"name": "<topic name>"}` with an optional `"context": "<a few lines>"`. It searches the topic's brief and writes a draft revision; it stores nothing and asks no approval, so never add one.
- `topic save` ("Save this as version N"): `{"name": "<topic name>", "draft": <draft>}`, where `<draft>` is the `result.draft` of the last `topic draft` reply, exactly as given. Atlas always answers with a `version_save` decision, whatever the settings: show it and wait. Never add a `request` approval; only the user's yes to that decision saves. After that yes, follow "Save a version" below: Reconcile reviews the draft, and the save is resent with the `review` (the same fields as for `plan save`) and the `go` approval of that decision, the user's reply as `words`.
- `plan mark` ("Mark item 2 done", "Skip item 3"): `{"plan": <the plan number>, "item": <the item number>, "state": "done" | "skipped"}`, with the numbers `plan save` and `plan show` give; it asks nothing. `plan show` ("What is left on the plan for <name>?"): `{}` or `{"topic": "<topic name>"}`.
- Approval: when the user's own message asks for this change and names its links (for a note, its who; for a topic, its name; for a citation, its repo and file), add `"approval": {"by": "request", "words": "<the user's message, verbatim>"}`. Never write that approval from your own words or from an earlier message; without it, Atlas asks. Never send it with a note proposal from `ask`, with a plan start, with a version save, or with an `add` that has `cited_in`.

## Run Reconcile

Reconcile reviews every research plan and every draft revision before it is saved. It is the dotagents `reconcile` skill; only this skill calls it, only as below, and the CLI never does. Do the steps once per plan or draft.

1. Check that it is ready, in bash from the repository root, and read the one JSON line it prints:

   ```bash
   node "$(realpath skill://reconcile)/acp-controller/cli.mjs" ready atlas-ask
   ```

   `{"ready":true}` (exit 0): go on to step 2. `{"ready":false,"reason":"…"}` (exit 2), or a `reconcile` skill that does not resolve (the reason is that Reconcile is not installed): go to step 5 with that reason. When the user asks whether Atlas is set up, run this beside `status` and add one line: Reconcile is ready, or is not and why. It is not an action item and does not change whether Atlas is ready.
2. Write one JSON request as `request.json` in a new folder from `mktemp -d` (under `/tmp`, never named `acp-controller-…`), with `python3` and `json.dump` since the text holds quotes and line breaks. Its `record` and `output` lie in that same folder:

   ```json
   {
     "caller": "atlas-ask",
     "goal": "<what is reviewed, for example: Review the research plan for <topic>>",
     "level": "direct",
     "candidate": {"text": "**Summary**\n\n- <1 to 7 points, each at most 100 characters>\n\n**Details**\n\n<the plan or the draft revision in full, with its labels, reasons and Model view>"},
     "intent": ["<the user's words, exactly as sent>", "<absolute path of this skill's SKILL.md>"],
     "context": ["<the sources and evidence it rests on: each link and title, and for a draft the claims it cites with their quotes>"],
     "mode": "conversation",
     "cap": "none",
     "approval": {"text": "<the same words, exactly>", "at": "<ISO-8601 time the user sent them>"},
     "record": "<absolute folder>/reconcile-record.md",
     "output": "<absolute folder>/output.json"
   }
   ```

   The user's words are the research request for a plan, or their yes to "Save this as version N?" for a draft; `intent` must hold them byte for byte. Take the skill's path from `realpath skill://atlas-ask`.
3. Run it in bash with `timeout: 0` and no `async`, `pty` or `name`, naming the request by its absolute path (never through a shell variable):

   ```bash
   node "$(realpath skill://reconcile)/acp-controller/cli.mjs" reconcile < <absolute folder>/request.json
   ```

   A call that ends without a record (timed out, cancelled): run the same command again; it attaches to the same run and starts nothing.
4. Read `output.json`. It counts only when its `status` matches the exit code: `0` `complete`, `1` `stopped` or `parked`, `2` `refused`, `3` `failed`. On `complete`, the review is `{"status": "complete", "text": <its text>, "run": <its run>, "reviewers": ["<role> <model>", ...] (one text per `reviewers` entry), "changes": <its changes, one per line, an empty text when none>, "diff": <its diff, left out when null>}`. Show the user its `summary` and `changes` as given, then go on with the flow. Keep the request folder and give the user its path: Atlas stores only the run id, and the folder's `reconcile-record.md` is the run's record.
5. Any other result is "not cross-checked": the reason is the readiness `reason`, the output's `reason`, or "Reconcile wrote no output (exit <code>)" when no output counts. Say so, show the reason, and give two Next lines: "Set up Reconcile first" (send nothing more; nothing is saved) and "Go on without it". Never go on without Reconcile unless the user picks that; a parked run is left for the human to repair or dispose. On "Go on without it", use the review `{"status": "not_cross_checked", "reason": "<the reason>", "text": "<the plan or draft text as you wrote it>"}`; Atlas stores the plan or version as `not cross-checked: <reason>`.

## Plan a topic

"Create a topic on X":

1. Run `find --wide` with the brief and show the sources, so the plan rests on what Atlas holds.
2. Write the plan from the brief and those sources: its `text` and its `items` (searches to run, questions to answer, sources and pages to read).
3. Run Reconcile on the plan, as above, with the user's request as its words.
4. Show the reviewed plan (the review's `text`) with Reconcile's `summary` and `changes`, or, on "Go on without it", the plan as written with the reason it is not cross-checked.
5. Send `topic create`, then `plan save` with the `review`, each with no approval. When the review changed the plan, write `items` again from the reviewed text first, so the `items` you send match the text Atlas stores. Show the one `plan_start` question their decisions carry, and wait. Nothing is stored before the user's yes.
6. After the yes, resend each as "Follow a choice" says, `topic create` first, and show both results.

## Save a version

"Save this as version N", or a catch-up's "save as the next version" after `topic draft`:

1. Send `topic save` with the draft and no approval. Show its `version_save` decision and wait for the user's answer.
2. After the yes, run Reconcile on the draft revision (its `text` with its claims, labels and Model view), with that yes as its words.
3. Resend `topic save` with the same body, the `review` and that decision's `go` approval, the user's reply as `words`, and show the saved version with Reconcile's `changes` as given. The version carries its `cross_check`, `complete` or `not cross-checked: <reason>`.

"Nothing to save" for a topic runs no Reconcile: send `topic nothing_to_save` as above.

## Follow a choice

After the user picks a decision option or a Next line, follow its `then`:

- `{"resend": {...}}`: run the same command again. For a decision option, start from the body you sent and set each field the resend gives (its `items` replace yours, and so does its `cited_in` when it has one). When the resend holds an `approval`, it replaces yours: add `"words": "<the user's reply, verbatim>"` to it. When it holds none, remove a `"by": "confirm"` approval from the body, because it answered the earlier question, not this one; keep a `"by": "request"` approval. Atlas asks again when the new body needs a confirm. For a Next line, send only the resend's fields as a new change, with no earlier approval. A `mode` in a resend is the flag to run with (`"reread"` is `--reread`); leave `mode` out of the body.
- `{"skill": "<name>"}`: run that skill.
- `{"stop": true}`: send nothing more. One exception: when `ask`'s `next` offers a note proposal (its label starts "save a note" or "change the note", or counts note proposals) and `result.note_proposals` is not empty, show each proposal to the user (who, subject, lean, reason, links) and ask whether to save it. Send nothing until the user says yes to one; then send it as a `note` call with that proposal's `who`, `subject`, `lean` and `reason` and no `approval`, so Atlas asks its own one confirm, and show that `confirm` decision as for any other change. When a proposal has no lean (a tie), first ask the user for `towards` or `against`; `note` requires a lean. A declined proposal is dropped; Atlas counts that pair's tally lines again from zero.

## Show the reply

The reply holds `ok`, `op`, `result`, `problems`, `next` and `decisions`. The exit code says done (0), failed (1), bad input (2), not set up (3) or needs a decision (4).

1. Show each `result.needs_action` item first, whatever the exit code: its `what`, then its `fix` lines, then its `where` when set. On exit 3, lead the items with one sentence saying Atlas is not set up.
2. Say the outcome in plain words from the rest of `result`. For `status`, that is the `summary` line as given (it names the profile, the source and inbox counts, the judge and the Atlas version), saying Atlas is ready when the exit is 0 and no item was shown; show `detail` only when it is not null. For `add`, give each `items` entry's link and `result`, with its title, then its `abstract` under the link and title when it carries one, then its claim count, any flags or copies it lists, its `item_links` (after `already added as <n> items`) and its `replies_log` path (after a failed summary); when the body held `cited_in`, also say `result.cited_in`: the repo and file, how many sources and topic versions it cited and how many earlier citations it replaced. For `add --redo`, give the `redone` count, then each `items` entry's link and `result`; for `redone` also its title, `abstract`, claim count, any flags and its `page` (the page was read again, or the stored text was used and why); for `kept: needs scope`, say the old summary was kept and the page needs a scope choice, with the `problems` item that names it; for `redo failed, old summary kept`, its `replies_log` path. An empty `items` list with no decision means there was nothing to redo. For `note`, give the note as saved (who, subject, lean, reason, date) and its `result` (`saved new`, or `changed` with the earlier lean it names). For `archive` and `restore`, give the `result` (`archived`, `restored`, `already archived <date>`, `not archived`, `not restored` or `not stored`) with the link, the note or the citation's repo and file it names. For `find`, list each `sources` entry with its link, title, author, date and last read, in the order given. For `ask`, give the `answer` first; then each `claims` entry with its `label` and `reason` when it carries them, each note in its `notes` beside the label (who, subject, lean, reason, date), its source links and its `backing`; when `labels` is not `checked`, say the claims are unlabelled and why, as `labels` gives it; then the `disagreements`, the `gaps`, the `model_view` marked as the model's own view, the `writing_model`, and any `tally_lines` Atlas kept, then each `note_proposals` entry (who, subject, its lean or that the evidence is tied, its reason and links). For both, name the `ranker` (its `name` and `model`), and show `question_as_searched` when present, so the user can catch a wrong rephrasing.
   For `topic` and `plan`: for `topic create`, `topic follow`, `topic unfollow` and `topic nothing_to_save`, give the `topic` (name, brief, whether it is followed, its agreed `version` and when it was saved, when it was last reviewed with nothing to save, and its archived date when set) and the `result` (`created`, `already stored`, `followed`, `already followed`, `unfollowed`, `not followed` or `nothing to save`, with `marks_cleared` for the last). For `topic list`, give each topic that way. For `topic draft`, name the `ranker` and the `sources`, then give the `draft`: its `text` first, then each `claims` entry with its `label` and `reason`, its source links and its `backing`; when `labels` is not `checked`, say the claims are unlabelled and why; then the `disagreements`, the `gaps`, the `model_view` marked as the model's own view and the `writing_model`; the `cites` of a claim are for `topic save`, not for the user. When `draft` is null, say no stored source matches the brief. For `topic save`, give the saved version's number and date, its `cross_check` status (`complete`, or `not cross-checked: <reason>`), its `reviewers`, `run` and `changes` as given, and how many claims it copied. For `plan save` and `plan show`, give each plan's number, topic, date, `cross_check`, `run`, reviewed `text` and `open_items`, newest first, with the `done` and `skipped` counts; for `plan mark`, the item as marked and how many items are still open.
   For `find --wide`: name the `ranker`, say how many sources are shown and how many are left (`counts.rest`), then give each `sources` entry's link, title, `p` and `found_by` (`jev`: only Jev's P found it; `bm25`: only the keyword search; `both`); when the `ranker` is `atlas_rerank`, say the sources carry no P. For a catch-up, give the `summary` line, then each `changed` topic: the `answer`, its `claims` with `label`, `reason` and source links, `disagreements`, `gaps`, `model_view`, the `new` and `marked` source links, and the `version` it would become (`next_version`); then the `no_change` topics and the `quiet` topics by name, and any `unanswered` topic with its reason. Its Next lines say how to save a new version or mark nothing to save; they are the user's to pick, never yours. For `add` and `add --redo`, a `topics_marked` list names the topics the source was marked for, a `topics` of `topics not matched` says the match failed, and `topics_flagged` names the topics whose agreed version cites a claim that changed. A `cited_in` list on an `add --reread` or `add --redo` item or on a catch-up `changed` topic says who cites the changed claim: give each entry's repo, file and date, with its source `link` or its `topic` and `version`, so the user can see which repo files rest on it.
3. Show each `problems` item as its `field` and `problem`.
4. Show each `decisions` item's `question` with its options' labels, then stop for the user's choice.
5. End with a Next line per `next` item, using its `label`. A `then` of `{"skill": "atlas-init"}` reads "run `atlas-init`".

Done when every part of the reply is shown and the answer ends with its Next lines. Leave Atlas settings and data to the CLI and `atlas-init`; never write them yourself.
