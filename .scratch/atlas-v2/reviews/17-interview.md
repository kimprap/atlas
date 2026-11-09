# Ticket 17 interview: questions as shown and the human's answers

Ticket: ~/dev/atlas/.scratch/atlas-v2/issues/17-decide-v2-additions.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label is the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Facts shown before round 1 (checked on g10, 2026-11-09):

- omp's model login is a subscription. `omp auth-gateway stdio` `/v1/usage` reports Anthropic and xAI use as percent of 5-hour and weekly windows, not dollars (Claude 5-hour: 26% used at the time). Chat replies carry token counts (with cache reads/writes) but no cost, and `/v1/models` lists no prices. So omp-role spend can only be tokens plus a list-price estimate; the real limit is the window, which your coding sessions share. Jev via OpenRouter returns real dollars per call.
- Per-source costs at list price: summary ≈ $0.20 (Sonnet `high`, ticket 15); Jev claim check ≈ $0.0004. A Jev yes/no per followed topic for one new source ≈ $0.0001 [estimate: ~2K tokens at $0.042/Mtok], so 20 topics ≈ $0.002 per `add`.
- A topic's what's-new today (ticket 06) is one search plus one `atlas_answer` call per topic; a catch-up over N topics costs N of those unless marks narrow it.
- Every source keeps its cleaned page text (ticket 12), so a redo needs no page read.
- Ticket 06 set ten commands; tickets 12 and 13 each rejected an eleventh.

## Round 1

### redo-text
Question: "1. Upgrade old summaries: what text does a redo summarize?"
- Stored page text (Recommended) — "Redo from the cleaned page text Atlas already keeps (ticket 12). No page is read, quotes are checked against the same text, and it works when a page is gone. A page that changed since is still caught by ticket 12's 30-day re-read offer, which runs the claim-level update."
- Fresh read of each page — "Re-read every page in the batch, then summarize from scratch. Picks up page changes at the same time, but each page is read again, gone pages fail, and it overlaps ticket 12's re-read offer."
Answer, given exactly:

```text
why stored page text vs. new reread? which would give higher and more accurate summary?
```

### redo-trigger
Question: "2. What starts a redo?"
- By hand, with a status count (Recommended) — "`status` shows \"N summaries on an older rubric or summary model\" and its Next offers the redo. Nothing else prompts. You start it when the quality check (ticket 13) or a model change gives you a reason."
- Offered in replies — "Any reply that relies on an older record also offers a redo. You see it sooner, but it adds a line to many replies."
- Automatic after a default changes — "Atlas redoes summaries on its own after the rubric or model changes. No stop, but it spends without asking, which ticket 02 ruled out for v2."
Answer: By hand, with a status count

### redo-shape
Question: "3. Where does the redo live, and how big is it?"
- A mode of `add`, one confirm (Recommended) — "`add --redo`, so there is no 11th command; it uses `add`'s existing pipeline (ticket 16). Scope: by default every record not on the current rubric and summary model, or named links, or the sources a topic cites. It shows the count and an estimated cost, then runs after one confirm. Per-source outcomes as `add` has them; one bad source never blocks the batch."
- Its own command, `redo` — "Same behavior as an 11th command. Easier to find in `--help`, but it adds a command, which tickets 12 and 13 avoided."
Answer: A mode of `add`, one confirm

### redo-old
Question: "4. Your note said old summaries can be dropped. When is the old one dropped?"
- Only after the new one is stored (Recommended) — "The new summary replaces the old one once it passes ticket 16's checks; nothing of the old summary is kept except a line in the summary history (date, old rubric and model). A failed redo keeps the old summary and reports \"redo failed, old summary kept\"."
- Dropped first — "The old summary is removed before the redo. A failed redo leaves the source with no summary, the same as ticket 16's \"summary failed\" on a new source."
Answer: Only after the new one is stored

### redo-cites
Question: "5. Saved topic versions and query records cite claims. What happens when a redo changes or removes those claims?"
- Versions keep copies; topics flagged (Recommended) — "A saved topic version keeps its own copy of each claim it cites (text and quotes), so it stays readable after any redo. After a redo, code matches old and new claims by quote; a topic whose agreed version cites a claim that is now gone or changed is flagged, the same flag ticket 12 uses for a changed page. Query records are history and are never changed."
- Re-point citations, no flags — "Citations move to the matching new claim, and unmatched ones are dropped. Saved versions change silently, which conflicts with versions being agreed conclusions."
Answer: Versions keep copies; topics flagged

### catchup-shape
Question: "6. Catch-up across followed topics: what does it look like?"
- A form of `ask`, one reply (Recommended) — "\"What's new across my topics?\" runs `ask` with no topic named; no 11th command. One reply: topics with conclusion-changing evidence first, each shown briefly (the changed conclusions, who says it, label) with its own \"save as version N+1?\"; topics with only other new sources as one count line; quiet topics as one count. Ends with one Next."
- Its own command, `catchup` — "Same reply from an 11th command."
Answer: A form of `ask`, one reply

### catchup-since
Question: "7. What does \"new\" mean in a catch-up?"
- Since each topic's agreed version (Recommended) — "The same comparison a topic's what's-new already makes. Nothing is missed if you skip a catch-up; evidence keeps showing until you save a version (or, from round 2, dismiss it). Marks from addition 3 clear when a version is saved."
- Since the last catch-up — "Shorter replies, but evidence you saw and did not save stops showing, and Atlas must keep a catch-up timestamp per profile."
Answer: Since each topic's agreed version

### match-what
Question: "8. When a source is added, what does Jev compare to mark followed topics?"
- Source vs brief + agreed conclusions (Recommended) — "One yes/no per followed topic: \"could this source change or add to a conclusion of this topic?\", reading the new source's abstract and claims against the topic's brief and its agreed version's conclusions. Marks at P ≥ 0.3, like the wide gather, because a missed mark hides evidence while a wrong mark costs one answer call at catch-up. Stores the probability and Jev model version. About $0.0001 per topic per source."
- Abstract vs brief only — "\"Is this source about this topic's area?\", which is cheaper to judge and catches more, but marks many sources that change nothing, so catch-up does more answer calls."
Answer: Source vs brief + agreed conclusions

### match-off
Question: "9. When Jev is not set up for a profile, or its calls fail, what happens to marks?"
- No marks; search per topic (Recommended) — "No marks are made. Catch-up and what's-new fall back to today's path, a search per topic, and say so. A failed Jev call during `add` notes \"topics not matched\" for that source, and the next catch-up searches."
- Opus yes/no per topic — "`atlas_rerank` answers the same yes/no per followed topic. Same marks, but one Opus call per topic per added source, which uses up your subscription window."
Answer: No marks; search per topic

### spend-measure
Question: "10. What does Atlas record and show for spending?"
- Tokens, estimate, Jev dollars, window (Recommended) — "Each paid call stores role, model, tokens (in, out, cache), and the cost: real dollars for Jev, a list-price estimate for omp roles. `status` shows this month per role and per profile, plus the omp subscription window left, as the OMP adapter reports it. Each profile counts apart, so `eval` spend stays separate. Prices come from a small settings table, not from the core."
- Jev dollars only — "Record only what costs real money (Jev). Simpler, but you cannot see how much of your subscription window Atlas used."
Answer: Tokens, estimate, Jev dollars, window

### uses-record
Question: "11. Who records that a repo relied on a source or topic, and through which command?"
- The rule's closing step, through `add` (Recommended) — "At the end of research, the `atlas-research` rule already proposes adding the new sources it relied on, with one confirm. `add` gains an optional `cited_in` (repo, file) that applies to every link in the batch, including ones already stored, plus any topic versions relied on. No 11th command, no new stop. Catch-up, a topic's what's-new, and a changed-claim report name the repos and files that cite the source or version."
- An 11th command, `cite` — "A separate change command that any session can call at any time. More flexible, but adds a command and a confirm."
- Automatic on `ask`/`find` — "Query records store the calling repo (no file) with no confirm. This records what was looked up, not what was relied on."
Answer: The rule's closing step, through `add`

### confirm-scope
Question: "12. Per-action confirm setting: where and for which changes?"
- Per profile, per change type (Recommended) — "In each profile in `config.toml`: `confirm.<change> = always | never` for `add`, `add --redo`, `inbox add`, `note`, `archive`, `restore`, follow/unfollow and starting a research plan. Defaults are all `always`. The CLI reports the settings in `status`, and `atlas-ask` skips a stop set to `never`. Round 2 decides which stops can never be turned off."
- One switch per profile — "`confirm = always | never` for all changes at once. Simpler, but you cannot turn off only the stops that prove redundant."
Answer: Per profile, per change type

Reply shown before round 2, to the human's redo-text question:

- Faithfulness to the page is the same either way: the same pipeline runs and every quote is checked against whatever text was used.
- Stored text: the page as of its last read; any change in the summary comes only from the new setup; no reads; gone and locked pages still work; reader improvements are not used.
- Fresh read: the page as it is now; any change comes from the setup and the page; one read per page (direct fetch free, X through Grok uses the xAI window); gone and locked pages need a fallback; reader improvements are used.
- Ticket 12's "never re-read on its own" existed because pages went into the agent's context; since ticket 16 Atlas reads pages itself, and a redo is started by the user. The recommendation changed to a fresh read with stored text as the fallback.

## Round 2

### redo-text
Question: "1. What text does a redo summarize?"
- Fresh read, stored text as fallback (Recommended) — "Each page is read again; the new text replaces the stored text, hash and read date. If a page is unreadable or gone, the redo uses the stored text and says so. Sources the site table marks as unchangeable (X post, pinned commit, versioned arXiv paper) use stored text, so no read and no Grok call. A page that now needs \"pick scope\" keeps its old summary and is listed for you. Topics citing changed claims are flagged as decided in round 1."
- Stored text only — "No reads. Any change in a summary comes only from the new setup, but a page that changed since its last read gets an upgraded summary of old text until a re-read."
- Fresh read only — "Always read again. Gone or locked pages fail and keep their old summary."
Answer: Fresh read, stored text as fallback

### dismiss
Question: "2. Can you clear a topic's new evidence without saving a version?"
- Yes, "nothing to save" (Recommended) — "Answering \"nothing to save\" for a topic in a catch-up or what's-new stores a \"reviewed up to <date>\" on the topic; that answer is the confirm. New evidence is then counted from the later of the agreed version and that date, and marks before it clear. It is not a new version and needs no Reconcile run."
- No — "Evidence keeps showing until you save a version. Simpler, but a topic with evidence you judged unimportant repeats in every catch-up."
Answer: Yes, "nothing to save", with this note, given exactly:

```text
make sure this is provided as an option of the next step to human, as guidance, without requiring human to memorize such action.
```

### spend-cap
Question: "3. Monthly cap: what does it count and what happens at the limit?"
- Billed money only; hard stop (Recommended) — "Optional per profile, unset by default. It counts only costs an adapter reports as billed: Jev today, and omp roles too if a later login bills per token. Replies warn from 80%. At 100%, paid calls stop before they start: a batch finishes its current item and reports the rest as not done, `find` falls back to BM25 order as ticket 06's ranker chain already does, and Next offers to raise the cap or wait for next month."
- Everything, estimates included — "The cap also counts list-price estimates for omp roles. Protects against heavy use, but a redo that bills nothing on your subscription could hit a dollar cap."
- Warn only — "Replies warn past the cap; nothing stops."
Answer: Billed money only; hard stop, with this note, given exactly:

```text
soft stop only, as warnings. yield first, but allow human to proceed. again, this should be presented as guidance in the response as all next steps human could make.
```

### window-guard
Question: "4. Should batches protect your omp subscription window?"
- Yes, batches pause at 90% (Recommended) — "Before each item in a batch (an `add` of several links, a redo), Atlas checks the window through a host-neutral quota port that the OMP adapter fills from `/v1/usage`. At 90% used (a setting) on the 5-hour or weekly window, it pauses and reports done, remaining and the reset time, with Next: resume after the reset. A batch's confirm also shows the count, the list-price estimate and the window left. Single commands do not check."
- No guard — "The estimate before the confirm is the only protection; a large redo can use up the window your coding sessions need."
- Guard every paid call — "Even a single `ask` stops near the limit. Safest for the window, but it adds a stop to reads."
Answer: Yes, batches pause at 90%, with this note, given exactly:

```text
pausing and reporting done seems false positive. if the window limit is reached and triggered a stop, it should report honestly, unless the work is actually done.
```

### fixed-stops
Question: "5. Which stops can never be turned off by the confirm setting?"
- Version saves, limits, decisions (Recommended) — "Always stop: \"save as version N+1?\" (you agree a conclusion), a cap stop or window pause, and decision stops (pick scope, summary failed, Jev not set up). Starting a research plan and a redo can be set to `never`; Reconcile still reviews every plan."
- Also research plan starts — "As above, plus starting a research plan always stops, because research spends the most (web searches, many summaries)."
Answer: Version saves, limits, decisions

### cite-ident
Question: "6. How are a citing repo and file identified, and what about stale citations?"
- Plain text; latest batch per file wins (Recommended) — "The caller passes the repo as its git remote `owner/name`, or the folder name when there is none, and the file as a path from the repo root. Atlas stores both as text with the date and never checks them. A later `add` with the same repo and file replaces that file's citations, so rerunning research updates them. `archive` hides one. Replies show citations with their date."
- Append only — "Citations only accumulate; stale ones stay until archived."
Answer: Plain text; latest batch per file wins

### stages
Question: "7. Build stages for the six additions (ticket 07's eight stages)?"
- As listed (Recommended) — "Stage 2: call records, the spend view in `status`, cap, window guard, and the confirm settings in `config.toml` (honored by `atlas-ask` from stage 3). Stage 3: summary history already records rubric and model. Stage 5: `add --redo`, with the quality check that tells you when a redo pays off. Stage 7: marks and catch-up, with topics. Stage 8: repo citations, with the `atlas-research` rule."
- Redo in stage 3 — "`add --redo` is built with `add`. Available earlier, but there is no better setup to redo towards before the quality check exists."
Answer: As listed

## Round 3

### cap-proceed
Question: "1. The cap is a soft stop: Atlas yields first and you may go on. How long does \"continue anyway\" last?"
- Rest of the month, warnings only (Recommended) — "The first paid call past the cap yields once. Next lists every option: continue anyway, raise the cap in `config.toml`, or stop here. After \"continue anyway\", the rest of the month only warns: one line per reply with spend against the cap. Raising the cap or a new month resets it. From 80%, replies carry the same warning line."
- This command only — "Every paid command past the cap yields again until you raise the cap or the month ends. Tighter, but a stop on each command."
Answer: This command only, with this note, given exactly:

```text
sounds good, yield everytime the cap is reached, or close to reaching. do not change the config unless human changes it themselves.
```

### window-proceed
Question: "2. When the window guard trips in a batch, how is it reported, and what can you do?"
- Honest "not finished"; three Next options (Recommended) — "Before the next item, Atlas yields and reports the batch as not finished, never as done, for example: \"stopped: Claude 5-hour window at 91% — 12 of 40 done, 28 not started; resets 14:30\". Next lists: continue now anyway (this batch only), rerun after the reset, or stop here. A rerun needs no saved queue: `add` reports stored links as already stored, and a redo's default scope is only records not yet on the current setup. If the window is already at 90% when the batch is proposed, its one confirm says so and serves as \"continue anyway\"."
- No "continue now" — "Same honest report, but only \"rerun after the reset\" or \"stop here\"; the guard cannot be overridden."
Answer: Honest "not finished"; three Next options

## Final confirmation

Question: the full proposed answer, shown in the same message (the full text is the ticket's "Proposed answer" section), then: "Confirm the proposed answer above for Decide v2 additions? Per the map's review plan, a Reconcile run on this summary comes next, before the ticket closes." Options: "Confirm" — "The summary stands as written. Next: run Reconcile on it, then close the ticket."; "Change something" — "Name what to change; the changed summary is shown again before Reconcile."
Answer: Confirm

## Reconcile run

The human's approval of the run's brief, given exactly: "approve". Run `reconcile-20261109T073435Z-64b849` (4 turns, $2.34); record: [17-reconcile-record.md](17-reconcile-record.md).

## After the Reconcile run

The run's front was shown verbatim, then this note, before the question:

- One applied change touches your round-1 answer on topic matching (question 8). The reviewers found that a catch-up skips any topic Jev did not mark, so Jev alone decides what gets read. The map's Jev rule says Jev "never filters, drops or decides". The reviewers flagged the conflict and left it for the final run.
  - Before: "Jev only flags (map rule), and the catch-up's answer call decides what is shown."
  - After: "Conflict flagged, not rewritten: … here the catch-up skips an unmarked topic on Jev's probability alone. You chose this knowing a missed mark hides evidence (round 1, question 8); the final run should settle it."
- I recommend settling it now so it doesn't sit open until the final run.

### marks-rule
Question: "How should catch-up use Jev's topic marks, given the Jev rule \"never filters, drops or decides\"?"
- Search every topic; marks only add and order (Recommended) — "Catch-up searches every followed topic for sources added since its agreed version or \"reviewed up to\" date: BM25 plus the Jev rerank, about $0.001 and 2–3 s each (ticket 11), run concurrently. An answer call runs only for a topic whose search returns a new source, or whose marks name one. Marked topics come first, and a marked source always goes to the answer call even when the search misses it, so marks add and never remove. A topic with nothing new is \"quiet\". About $0.02 for 20 topics plus one answer call per topic with news [estimate]. This fits the Jev rule, so no conflict remains."
- Keep as reconciled — "Unmarked topics are not searched and show as one \"not searched\" count, with a Next to search them too. Cheapest, but Jev's probability alone decides which topics get read. The conflict stays flagged for the final run."
- Exception to the Jev rule — "As reconciled, and the map records that topic marks may narrow a catch-up as a named exception you approve, so the final run does not reopen it."
Answer: Search every topic; marks only add and order
