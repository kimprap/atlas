## Review rounds

| Step | Reviewer/event | Pass | Text | Outcome | Turn |
|---|---|---|---|---|---|
| 1 | A | post-rethink | 95298ecc | edit<br>• The catch-up skips topics Jev did not mark, which the map's Jev rule forbids; this is not flagged<br>• The proposal says Jev 'only flags' and calls unsearched topics 'quiet', which hides that conflict<br>• The cap stop on paid reads changes earlier no-stop rules without saying so | 135 s · 14 tools · 459k tokens · wait 4 s |
| 2 | B | post-rethink | 95298ecc | edit · superseded<br>• Matches the human's choices on redo, catch-up, spend, cap, window guard, citations, confirms<br>• Marks skip unmarked topics, yet the text says Jev only flags; the Jev rule tension is unflagged<br>• The redo count would never converge for escalated records<br>• The list of changes to ticket 06 misses three real changes | 226 s · 19 tools · 712k tokens · wait 4 s |
| 3 | B | later | f1bf2f48 | edit<br>• A's Jev-rule, not-searched count and cap-on-reads fixes are kept<br>• Escalated records keep the redo count from ever reaching zero<br>• Topic "nothing to save" and the wider research proposal are unlisted changes<br>• Unmarked topics need a Next option to search them; open details go to spec | 74 s · 2 tools · 287k tokens |
| 4 | A | later | a428cc03 | accept<br>• Accepts the revised proposal as a whole<br>• Flags the Jev-rule conflict; unmarked topics shown as not searched, with a way to search them<br>• The redo count now reaches zero, and the changes to ticket 06 are listed | 28 s · 2 tools · 202k tokens |
| 5 | apply | — | a428cc03 | applied | — |
| 6 | cleanup | — | — | A, B disposed (observed exit) | — |

## Final proposal

**Proposal**

- **Summary**
  
  - Redo summaries via `add --redo`: fresh read, stored text fallback, old dropped only on success
  - Catch-up is `ask` with no topic; Jev marks narrow it (Jev-rule conflict flagged)
  - Each paid call recorded; cap and window guard are soft stops that yield with every option
  - `add` records citing repos and files at the research rule's closing step; no 11th command
  - Per-profile confirm settings; version saves, limits and decision stops always stop
  
  **Details**
  
  ## Decide v2 additions
  
  Records:
  
  - Interview, with every question as shown and the human's exact answers: [17-interview.md](../reviews/17-interview.md)
  
  The six additions add one command mode and no new command. `add --redo` redoes summaries from a fresh read of each page. A catch-up is `ask` with no topic named, using topic marks that Jev sets when a source is added. Every paid call is recorded, and soft limits yield with every option in Next. `add` records the repos and files that rely on a source. Each profile gets a confirm setting for each type of change. Items marked "(Main)" were not asked.
  
  ### 1. Upgrade old summaries (stage 5)
  
  1. Started by hand. `status` shows "N summaries on an older rubric or summary model", and its Next offers the redo. Nothing else prompts.
  2. `add --redo` runs `add`'s pipeline (ticket 16). Its scope is, by default, every record not on the current rubric and summary model; otherwise named links or the sources a topic cites. A record counts as older when its rubric version differs, or when it was written without escalation by a model other than the current `atlas_summarize` model; an escalated record counts only on a rubric change, so a redo that needed escalation does not stay in the count. Its one confirm shows the count, the list-price estimate and the subscription window left.
  3. Each page is read again, and the new text replaces the stored text, hash and read date. If a page is unreadable or gone, the redo uses the stored text and says so. Sources the site table marks as unchangeable use the stored text. A page that now needs "pick scope" keeps its old summary and is listed.
  4. The old summary is dropped only after the new one passes ticket 16's checks, leaving one line in the summary history (date, old rubric and model). A failed redo keeps the old summary and reports "redo failed, old summary kept". Per-source outcomes follow `add`, and one bad source never blocks the batch.
  5. A saved topic version keeps its own copy of each claim it cites (text and quotes). After a redo, code matches old and new claims by quote. A topic whose agreed version cites a claim that is now gone or changed is flagged, with ticket 12's changed-page flag. Query records are history and never change. A redone source is matched to followed topics again, as in addition 3 (Main).
  
  ### 2. Catch-up across followed topics (stage 7)
  
  1. "What's new across my topics?" runs `ask` with no topic named. One reply:
     - first, topics with conclusion-changing evidence, each in brief (the changed conclusions, who says it, label) with its own "save as version N+1?";
     - then one count line for topics whose evidence changes no conclusion;
     - then one count of topics with no mark, which were not searched;
     - one closing Next.
  2. "New" means since each topic's agreed version, or since its "reviewed up to" date if that is later. "Nothing to save" is offered in Next for each topic shown, so you never have to remember it. Choosing it stores that date as the confirm; it creates no version and needs no Reconcile run.
  3. Cost: one search and one `atlas_answer` call per marked topic only. Unmarked topics cost nothing and are not searched; the closing Next offers "search the unmarked topics too" (one search and answer each). Without marks (no Jev), it falls back to one search per topic and says so (Main).
  
  ### 3. Match new sources to followed topics (stage 7)
  
  1. After `add` stores a source, and after a redo, Jev answers one yes/no per followed topic: "could this source change or add to a conclusion of this topic?" Jev reads the source's abstract and claims against the topic's brief and its agreed version's conclusions. A topic with no agreed version is matched on its brief only (Main).
  2. P ≥ 0.3 marks the topic "new evidence waiting". The probability and the Jev model version are stored. The catch-up's answer call decides what is shown. Conflict flagged, not rewritten: the map's Jev rule lets Jev only rank or flag, and a flag never removes an item from what is read, but here the catch-up skips an unmarked topic on Jev's probability alone. You chose this knowing a missed mark hides evidence (round 1, question 8); the final run should settle it. About $0.0001 per topic per source.
  3. Marks clear when a version is saved or the user picks "nothing to save".
  4. With Jev not set up, no marks are made. A failed Jev call notes "topics not matched" on that source, and the next catch-up searches.
  
  ### 4. Spend view and monthly cap (stage 2)
  
  1. Each paid call records its role, model, tokens (in, out, cache), its cost, and whether that cost is billed or estimated. Jev's cost is billed dollars from OpenRouter. omp roles on the subscription get a list-price estimate from a price table in settings, not in the core.
  2. `status` shows this month's spend per role and per profile, plus the subscription windows left. Each profile counts on its own, so `eval` stays separate.
  3. A host-neutral quota port gives window use and reset times. The OMP adapter fills it from `omp auth-gateway stdio` `/v1/usage`. The call port returns token use and billed-or-estimated cost (Main).
  4. Optional monthly cap per profile, unset by default. It counts billed costs only: Jev today, and omp roles if a later login bills per token.
     - It is a soft stop. From 80% of the cap (a setting) and past the cap, every paid command yields before its first paid call. Next lists continue anyway (this command only), raise the cap yourself in `config.toml`, and stop here.
     - Atlas never changes the cap or any other setting.
     - A batch that crosses 80% or the cap partway yields before its next item and is reported as not finished, with the same options (Main).
  5. Window guard for batches (an `add` of several links, a redo). Before each item, Atlas checks the windows of the providers the batch uses. At 90% used (a setting) of a 5-hour or weekly window, it yields and reports the batch as not finished, for example: "stopped: Claude 5-hour window at 91%: 12 of 40 done, 28 not started; resets 14:30".
     - Next lists continue now anyway (this batch only), rerun after the reset, and stop here.
     - A rerun needs no saved queue: `add` reports stored links as already stored, and a redo's default scope covers only records not yet on the current setup.
     - If a window is already at 90% when the batch is proposed, the batch's one confirm says so and counts as "continue anyway".
     - Single commands do not check.
  
  ### 5. Repos that relied on a source or topic (stage 8)
  
  1. At the end of research, the `atlas-research` rule's existing closing proposal passes `cited_in` (repo, file) to `add`, plus any topic versions relied on. The proposal now lists every source the research relied on, not only new ones, so the citation reaches links already stored; it also appears when only stored sources were relied on. There is no 11th command and no new kind of stop.
  2. The repo is its git remote `owner/name`, or the folder name when there is none, and the file is a path from the repo root. Both are plain text supplied by the caller and stored with the date; Atlas never checks them, so the core stays repo-agnostic.
  3. A later `add` with the same repo and file replaces that file's citations. `archive` also hides a citation.
  4. Catch-up, a topic's what's-new, and any `add`, re-read or redo reply that changes a claim name the repos and files citing that source or topic version, with their dates.
  
  ### 6. Per-action confirm setting (stage 2; honored by `atlas-ask` from stage 3)
  
  1. In each profile in `config.toml`: `confirm.<change> = always | never` for `add`, `add --redo`, `inbox add`, `note`, `archive`, `restore`, follow and unfollow, and starting a research plan. All default to `always`. `status` reports them, and `atlas-ask` skips a stop set to `never`.
  2. Always stop, whatever the setting:
     - "save as version N+1?";
     - cap and window yields;
     - decision stops: pick scope, summary failed, Jev not set up.
  
     Reconcile still reviews every research plan.
  
  ### Changes to earlier decisions
  
  - [Define Atlas v2 requirements](02-define-atlas-v2-requirements.md):
    - "The user may remove these stops later" becomes the confirm setting.
    - What's-new gains "nothing to save" and the catch-up across topics as the manual step towards the end goal.
    - A saved topic version keeps copies of the claims it cites.
    - Read-only asks are no longer always answered directly: from 80% of a set cap, a paid one yields first.
  - [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md):
    - `add` gains `--redo` and `cited_in`; `ask` with no topic is the catch-up.
    - `status` gains spend, windows, the redo count and the confirm settings.
    - `topic` gains "nothing to save", which stores the "reviewed up to" date; a topic's what's-new and the catch-up offer it in Next.
    - Section 6 item 7: the `atlas-research` closing proposal lists every source relied on, not only new ones, so citations reach stored sources.
    - `archive` also hides a citation.
    - The store gains call records, topic marks, "reviewed up to" dates, citations and copied claims in versions.
    - Profiles gain the cap, the 80% and 90% limits, the confirm settings and the price table.
    - Jev gains topic matching.
    - "Read commands run without a stop" changes: from 80% of a set cap, a paid read such as `ask` or `find` yields first. A change set to `never` runs without its one confirm.
  - [Decide source identity](12-decide-source-identity.md):
    - A redo you start also reads stored links again and refreshes their text, hash and read date; nothing re-reads on its own.
    - Ticket 12's changed-page flag also covers a redo.
  - [Decide source summarization method](16-decide-source-summarization-method.md):
    - A fourth port, quota, joins read, call and judge; the call port also returns token use and billed-or-estimated cost.
    - A redo summarizes from scratch, because the whole summary is being redone. Section 7's claim-level update still serves re-reads.
  - [Decide Atlas build order](07-decide-atlas-build-order.md): stage 2 adds call records, the spend view, cap, window guard and confirm settings; stage 5 adds `add --redo`; stage 7 adds marks and catch-up; stage 8 adds citations.
  
  ### Rejected alternatives
  
  - Redo from stored text only: a stale page gets an upgraded summary of old text. Fresh read only: gone pages fail.
  - Redo offered in replies, or run automatically: noise in many replies, or spending without asking.
  - A `redo`, `catchup` or `cite` command: an 11th command where an existing one fits.
  - Dropping the old summary first: a failed redo leaves no summary.
  - Re-pointing version citations: agreed versions would change silently.
  - Since the last catch-up: evidence you saw and did not save stops showing.
  - Matching on abstract and brief only: more marks that change nothing, so more answer calls. Opus matching without Jev: one Opus call per topic per source.
  - Jev dollars only: Atlas's share of your subscription window goes unseen.
  - A cap that counts estimates: a redo that bills nothing could hit a dollar cap. A hard stop, or "continue" for the rest of the month: you asked for a soft stop that yields on every command.
  - No window guard, or a guard on every call: a large redo can drain your coding window, or reads get stops.
  - "Paused, done" wording: reports unfinished work as done.
  - Recording lookups on `ask`/`find`: records what was searched, not what was relied on. Append-only citations: stale ones pile up.
  - One confirm switch: you cannot turn off only the stops that prove redundant. A fixed stop on research plan starts: Reconcile already reviews each plan.
  - Redo in stage 3: there is no better setup to redo towards before the quality check.
  
  ### Passed on to the spec route
  
  - Where the price table lives and how it is updated; the quota and call port shapes.
  - How a batch's cost and window use are estimated before the confirm.
  - Open details: how a rerun after a window stop skips finished items when a redo was scoped to named links or a topic; whether a `never` confirm and a cap or window yield make two stops; how marks that never change a conclusion stop costing an answer call in every catch-up; whether a catch-up over many marked topics counts as a batch for the window guard; whether a redo re-matches only sources whose claims changed.
  - The schemas for call records, marks, "reviewed up to" dates, citations and copied claims; the exact Next wording.
  - Checking the 0.3 match threshold on real topics once stage 7 has data.
  - How the `atlas-research` rule derives the repo name and file path.
  - From the map's ideas round: a shared test suite every host adapter must pass, plus a fake host, as a build requirement.

**Changes**

- Flags the Jev-rule conflict; unmarked topics shown as not searched, with a Next to search them
- Redo count rule: escalated records count as older only on a rubric change
- Research closing proposal covers every source relied on, so stored ones get citations
- Changes list adds cap yields on reads, topic "nothing to save", and spec questions
- Summary: 4 of 5 points unchanged · Details: edited

## Diff

```diff
--- original
+++ final
@@ -1,7 +1,7 @@
 **Summary**
 
 - Redo summaries via `add --redo`: fresh read, stored text fallback, old dropped only on success
-- Catch-up is `ask` with no topic; Jev marks topics on add; "nothing to save" offered in Next
+- Catch-up is `ask` with no topic; Jev marks narrow it (Jev-rule conflict flagged)
 - Each paid call recorded; cap and window guard are soft stops that yield with every option
 - `add` records citing repos and files at the research rule's closing step; no 11th command
 - Per-profile confirm settings; version saves, limits and decision stops always stop
@@ -19,7 +19,7 @@
 ### 1. Upgrade old summaries (stage 5)
 
 1. Started by hand. `status` shows "N summaries on an older rubric or summary model", and its Next offers the redo. Nothing else prompts.
-2. `add --redo` runs `add`'s pipeline (ticket 16). Its scope is, by default, every record not on the current rubric and summary model; otherwise named links or the sources a topic cites. Its one confirm shows the count, the list-price estimate and the subscription window left.
+2. `add --redo` runs `add`'s pipeline (ticket 16). Its scope is, by default, every record not on the current rubric and summary model; otherwise named links or the sources a topic cites. A record counts as older when its rubric version differs, or when it was written without escalation by a model other than the current `atlas_summarize` model; an escalated record counts only on a rubric change, so a redo that needed escalation does not stay in the count. Its one confirm shows the count, the list-price estimate and the subscription window left.
 3. Each page is read again, and the new text replaces the stored text, hash and read date. If a page is unreadable or gone, the redo uses the stored text and says so. Sources the site table marks as unchangeable use the stored text. A page that now needs "pick scope" keeps its old summary and is listed.
 4. The old summary is dropped only after the new one passes ticket 16's checks, leaving one line in the summary history (date, old rubric and model). A failed redo keeps the old summary and reports "redo failed, old summary kept". Per-source outcomes follow `add`, and one bad source never blocks the batch.
 5. A saved topic version keeps its own copy of each claim it cites (text and quotes). After a redo, code matches old and new claims by quote. A topic whose agreed version cites a claim that is now gone or changed is flagged, with ticket 12's changed-page flag. Query records are history and never change. A redone source is matched to followed topics again, as in addition 3 (Main).
@@ -29,15 +29,15 @@
 1. "What's new across my topics?" runs `ask` with no topic named. One reply:
    - first, topics with conclusion-changing evidence, each in brief (the changed conclusions, who says it, label) with its own "save as version N+1?";
    - then one count line for topics whose evidence changes no conclusion;
-   - then one count of quiet topics;
+   - then one count of topics with no mark, which were not searched;
    - one closing Next.
 2. "New" means since each topic's agreed version, or since its "reviewed up to" date if that is later. "Nothing to save" is offered in Next for each topic shown, so you never have to remember it. Choosing it stores that date as the confirm; it creates no version and needs no Reconcile run.
-3. Cost: one search and one `atlas_answer` call per marked topic only. Unmarked topics cost nothing. Without marks (no Jev), it falls back to one search per topic and says so (Main).
+3. Cost: one search and one `atlas_answer` call per marked topic only. Unmarked topics cost nothing and are not searched; the closing Next offers "search the unmarked topics too" (one search and answer each). Without marks (no Jev), it falls back to one search per topic and says so (Main).
 
 ### 3. Match new sources to followed topics (stage 7)
 
 1. After `add` stores a source, and after a redo, Jev answers one yes/no per followed topic: "could this source change or add to a conclusion of this topic?" Jev reads the source's abstract and claims against the topic's brief and its agreed version's conclusions. A topic with no agreed version is matched on its brief only (Main).
-2. P ≥ 0.3 marks the topic "new evidence waiting". The probability and the Jev model version are stored. Jev only flags (map rule), and the catch-up's answer call decides what is shown. About $0.0001 per topic per source.
+2. P ≥ 0.3 marks the topic "new evidence waiting". The probability and the Jev model version are stored. The catch-up's answer call decides what is shown. Conflict flagged, not rewritten: the map's Jev rule lets Jev only rank or flag, and a flag never removes an item from what is read, but here the catch-up skips an unmarked topic on Jev's probability alone. You chose this knowing a missed mark hides evidence (round 1, question 8); the final run should settle it. About $0.0001 per topic per source.
 3. Marks clear when a version is saved or the user picks "nothing to save".
 4. With Jev not set up, no marks are made. A failed Jev call notes "topics not matched" on that source, and the next catch-up searches.
 
@@ -58,7 +58,7 @@
 
 ### 5. Repos that relied on a source or topic (stage 8)
 
-1. At the end of research, the `atlas-research` rule's existing proposal to add the sources it relied on passes `cited_in` (repo, file) to `add`, plus any topic versions relied on. The citation applies to every link in the batch, including links already stored. There is no 11th command and no new stop.
+1. At the end of research, the `atlas-research` rule's existing closing proposal passes `cited_in` (repo, file) to `add`, plus any topic versions relied on. The proposal now lists every source the research relied on, not only new ones, so the citation reaches links already stored; it also appears when only stored sources were relied on. There is no 11th command and no new kind of stop.
 2. The repo is its git remote `owner/name`, or the folder name when there is none, and the file is a path from the repo root. Both are plain text supplied by the caller and stored with the date; Atlas never checks them, so the core stays repo-agnostic.
 3. A later `add` with the same repo and file replaces that file's citations. `archive` also hides a citation.
 4. Catch-up, a topic's what's-new, and any `add`, re-read or redo reply that changes a claim name the repos and files citing that source or topic version, with their dates.
@@ -79,13 +79,17 @@
   - "The user may remove these stops later" becomes the confirm setting.
   - What's-new gains "nothing to save" and the catch-up across topics as the manual step towards the end goal.
   - A saved topic version keeps copies of the claims it cites.
+  - Read-only asks are no longer always answered directly: from 80% of a set cap, a paid one yields first.
 - [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md):
   - `add` gains `--redo` and `cited_in`; `ask` with no topic is the catch-up.
   - `status` gains spend, windows, the redo count and the confirm settings.
+  - `topic` gains "nothing to save", which stores the "reviewed up to" date; a topic's what's-new and the catch-up offer it in Next.
+  - Section 6 item 7: the `atlas-research` closing proposal lists every source relied on, not only new ones, so citations reach stored sources.
   - `archive` also hides a citation.
   - The store gains call records, topic marks, "reviewed up to" dates, citations and copied claims in versions.
   - Profiles gain the cap, the 80% and 90% limits, the confirm settings and the price table.
   - Jev gains topic matching.
+  - "Read commands run without a stop" changes: from 80% of a set cap, a paid read such as `ask` or `find` yields first. A change set to `never` runs without its one confirm.
 - [Decide source identity](12-decide-source-identity.md):
   - A redo you start also reads stored links again and refreshes their text, hash and read date; nothing re-reads on its own.
   - Ticket 12's changed-page flag also covers a redo.
@@ -115,6 +119,7 @@
 
 - Where the price table lives and how it is updated; the quota and call port shapes.
 - How a batch's cost and window use are estimated before the confirm.
+- Open details: how a rerun after a window stop skips finished items when a redo was scoped to named links or a topic; whether a `never` confirm and a cap or window yield make two stops; how marks that never change a conclusion stop costing an answer call in every catch-up; whether a catch-up over many marked topics counts as a batch for the window guard; whether a redo re-matches only sources whose claims changed.
 - The schemas for call records, marks, "reviewed up to" dates, citations and copied claims; the exact Next wording.
 - Checking the 0.3 match threshold on real topics once stage 7 has data.
 - How the `atlas-research` rule derives the repo name and file path.
```

## Spend

| Reviewer | Model | Tokens | Cost |
|---|---|---|---|
| A | anthropic/claude-opus-5-5 · medium | 661,321 | 1.251764 USD |
| B | anthropic/claude-sonnet-5-5 · high | 999,103 | 1.084437 USD |
| Total | | 1,660,424 | 2.336201 USD |
