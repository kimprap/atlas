## Review rounds

| Step | Reviewer/event | Pass | Text | Outcome | Turn |
|---|---|---|---|---|---|
| 1 | A | post-rethink | 7878f978 | edit<br>• Later decisions never reached tickets 02, 06, 07 and 12, or the map's list of model roles<br>• The Handoff passes two settled items to the spec route and leaves out tickets 14 and 15<br>• Nothing places the adapter test suite or moves OMP-only setup out of the shared core<br>• The Handoff is missing two required sections and names a skill, not an actor, as receiver | 182 s · 22 tools · 735k tokens · wait 4 s |
| 2 | B | post-rethink | 7878f978 | edit · superseded<br>• Handoff counts 13 tickets; the map indexes 16, and two spec-route lists are missing<br>• No ticket change or spec item from the three review criteria is named, though real gaps exist<br>• Handoff lacks the Changed targets/effects and Checks headings and the user-authority list | 412 s · 36 tools · 1.67M tokens · wait 4 s |
| 3 | B | later | 5f000781 | edit<br>• Back-link edits are right but wrongly say no design question is open; four points need the user<br>• Count says 13 tickets while the index has 16; ticket 07 already has a line for ticket 17<br>• Wide gather, re-read entry, human-stop replies and confirm defaults are missing | 84 s · 1 tool · 205k tokens |
| 4 | A | later | 9bf2e8ff | accept · with notes<br>• Accepts the Handoff with its fixes for missing back-links, the 16-ticket count and spec items<br>• The four proposed ticket changes are left to the user, which fits tickets the user confirmed<br>• Corrects the change list so it also names the three added Low risks | 31 s · 3 tools · 242k tokens |
| 5 | B | later | 9bf2e8ff | edit<br>• Changed targets makes saving the Reconcile record wait for confirmation, against the user's request<br>• Everything else in the proposal stands | 33 s · 1 tool · 216k tokens |
| 6 | A | later | e621e78f | accept<br>• Accepts the Handoff: the review record is now saved as the user asked, without waiting<br>• Corrects the change list: the original had one Low risk, so three were added, not four | 7 s · 1 tool · 129k tokens |
| 7 | apply | — | e621e78f | applied | — |
| 8 | cleanup | — | — | A, B disposed (observed exit) | — |

## Final proposal

**Proposal**

- **Summary**
  
  - Map resolved: all 16 indexed tickets closed, Not yet specified empty
  - Later decisions never reached tickets 02, 06, 07, 12 or the map; the Handoff lists the edits
  - Spec route gets the Passed on lists of tickets 07, 12, 13, 14, 15, 16 and 17
  - Four ticket changes and five spec items proposed; the user confirms the changes first
  - Low risk: catch-up cost and 0.3 match threshold are estimates until stage 7 data
  
  **Details**
  
  # Handoff: Wayfinder map Atlas v2, resolved
  
  ## Outcome
  - Map ~/dev/atlas/.scratch/atlas-v2/map.md is resolved: all 16 index entries are closed (the 13 tickets in `issues/` plus dotfiles tickets 01, 04 and 05), no ticket is open, and Not yet specified is empty. The decision index is the map's Decisions so far, ending with Decide v2 additions.
  - The final review found two kinds of gap. First, later decisions never reached the tickets they changed: tickets 12 and 16 list changes to tickets 02, 06 and 12, but those tickets carry no Later change line for them. These lines record decisions already made; Main applies them once the user confirms this Handoff:
    - Ticket 02: Later change lines for tickets 12 and 16. The stored record gains the cleaned page text, other links and the scope choice; a changed page gets the check in code and the claim-level update, so "A changed page is re-summarized" is stale; images are accepted; each claim gains its quote, position and basis tag; each record gains its summary history.
    - Ticket 06: Later change lines for tickets 12 and 16. `add` gains the outcomes "pick scope", "already stored as <link>" and "re-read, no meaningful change"; links get the three-layer cleanup and stored links are matched before any read; Atlas reads pages through the read port, so section 6 item 1's "the calling agent reads the page" no longer holds and `add` takes links; a fifth role, `atlas_escalate`, so section 3 item 4 (`atlas-init` writes "the four Atlas roles") and section 5 item 1 say five; the omp gateway and Jev calls sit behind ports as adapters.
    - Ticket 12: a Later change line for ticket 16. `add` does the stored-link lookup itself; quotes are the claim locators; removing the reader's header and counter lines and detecting "pick scope" from the `Method` line move into the OMP adapter, so core uses the read port's kind hint.
    - Ticket 07: Later change lines for tickets 15 and 16 (ticket 17 already has one). Stage 2's "omp-gateway and Jev clients" become the call, judge and quota ports with their OMP and Jev adapters; stage 3's `add` brings the read port and its OMP adapter; stage 4's summary-model gate is met (`atlas_summarize` starts at Sonnet 5.5 `high`).
    - Map: the standing decision on Atlas models gains "Changed on 2026-11-09 by Decide source summarization method: a fifth role, `atlas_escalate`"; "one vault on this Mac" becomes g10 (ticket 14); the index lines for 06 ("four omp roles") and 07 ("The summary-model prototype must resolve before real data") are updated.
  - Passed to the spec route: the "Passed on" lists of tickets 07, 12, 13, 14, 15, 16 and 17 (the other nine index entries carry no spec-route list). Two carried items are already settled and drop out: ticket 07's summary-model gate (ticket 15 resolved it) and ticket 12's "how the agent looks up a stored link before reading it" (ticket 16 settled it). This review adds five spec items:
    1. One adapter contract and where the shared test suite and fake host sit. Ports are split across tickets (store interface, 06 section 4; read, call and judge, 16; quota, 17), and Reconcile review, setup and diagnostics are not ports. Define one list of ports plus optional capabilities, each with a fallback when absent (Reconcile's "not cross-checked" is one, and a new harness has no dotagents trusted-caller entry). Ticket 07 has no stage for the suite and fake host: recommended placement is with the stage 2 ports, covering the read, call, judge and quota ports, with the OMP adapter and ticket 13's replay read adapter passing it.
    2. Which setup and status facts the OMP adapter supplies, so core names no omp setting: the `modelRoles` lines printed on exit 3 (ticket 06 section 5 item 4), `atlas-init`'s role setup, and `status`'s omp version warning (ticket 14 item 11).
    3. Stage 2 size. Ticket 07 stage 2 now holds the whole schema, `config.toml`, the clients, call records, spend view, cap, window guard, confirm settings, `status` and `atlas-init`, before anything is usable at stage 4. Decide which wait for the stage that first uses them (the cap, window guard and confirm settings first matter at stage 3's batch `add`), and ship no setting without a consumer.
    4. `status` size. It now shows profile, store, roles, Jev, Reconcile, counts, inbox, version, spend, windows, redo count and confirm settings (tickets 06, 14, 17). Specify a reply that lists what needs action first, each with its fix, and puts the rest behind a detail option.
    5. Jev as one dependency. Jev serves rerank, wide gather, claim support, copy flags and topic marks through an OpenRouter endpoint named `alpha` (ticket 16's evidence file). Rerank and wide gather fall back to Opus, support checks and marks skip, and the copy flags' not-set-up case is open (ticket 12). State each degraded behavior in one table, and put request and reply shape checks in the judge port's contract tests.
  - Second, four open points this review proposes as ticket changes. Each needs the user's decision before the spec relies on it, and a confirmed one gets a Later change note in its ticket:
    1. Ticket 06 section 5 item 3, wide gather: Jev's P >= 0.3 set alone decides which stored sources the agent reads. Ticket 17 settled the same pattern by searching every topic "so Jev never decides what is read". Proposed: Jev's candidates are added to the BM25 candidates from the agent's phrasings, and the rest by P are one Next away. The form is the user's call.
    2. Tickets 12 and 17, re-read: ticket 12's 30-day offer leads to a user-accepted re-read with a change check, but ticket 17 names only `add --redo`, which summarizes from scratch, so ticket 16 section 7's claim-level update has no entry point. Proposed: name it, for example an `add` mode `--reread` that runs ticket 12's change check and ticket 16's update, and keep `--redo` as the rebuild.
    3. Tickets 06 and 17, reply and confirm: cap and window yields, pick scope and summary failed all wait for a human, but the reply has `ok`, exit codes 0-3 (done, failed, bad input, not set up) and a Next, with no outcome for them. Ticket 17 section 6 has `atlas-ask` skip a stop set to `never`, so the confirm policy lives in skill prose that every new host front door must copy. Proposed: one "needs a decision" outcome with typed options, and the CLI enforces the confirm setting; the mechanism is the user's call.
    4. Tickets 06 and 17, confirm defaults (the user set the current ones): every change defaults to `always`, so "Add these links" or "Summarize this link" asks a second time after the user said so. Option: a change the user asked for in so many words runs on that request, as Reconcile already takes the user's words as approval (ticket 06 section 6 item 5), while agent-proposed changes (research-end source adds, note and tally proposals, plan starts, version saves) and paid-at-scale ones (a redo, a batch of links) keep their one confirm. The user may instead keep `always` and flip single settings.
  - Route impact: changed. The map returns to dev-ask to plan the Atlas v2 spec route.
  
  ## Changed targets/effects
  - The Reconcile record is saved in `.scratch/atlas-v2/reviews/`, as the user asked.
  - None yet for the ticket and map edits listed in Outcome: they are applied only after the user confirms this Handoff.
  - On the user's confirmation: the Handoff goes to `dev-ask`; the map gets no new Decisions-so-far line.
  
  ## Checks
  - Map resolved
    Behavior: every indexed ticket is resolved and Not yet specified is empty
    Check: read each ticket's Status line and the map's Not yet specified section; expect resolved and empty
    Observed: the 13 files in `issues/` and dotfiles tickets 01, 04 and 05 are resolved, matching the 16 index entries; the section holds only its comment; pass
  - Spec-route lists
    Behavior: every index entry that passes work to the spec route is named in Outcome
    Check: read each ticket's Passed on section; expect lists only in tickets 07, 12, 13, 14, 15, 16 and 17
    Observed: the other nine entries carry none; pass
  - Back-link and ticket-change findings rest on ticket text only; nothing was run.
  
  ## Blocker/risk
  - Low: the catch-up cost (about $0.02 for 20 topics) and the 0.3 match threshold are estimates until real topics exist (stage 7 data). Without Jev, the Opus rerank cost of a catch-up is not estimated anywhere.
  - Low: the summary-model default rests on 16 pages with one run per setup, and Jev both steered the repairs and judged support (ticket 15 caveats); the quality check re-measures it.
  - Low: ticket 13 asks the user for about 10 minutes of spot checks per lane per run plus a 30-claim label review; its own passed-on item on narrowing them should be settled early in the spec.
  - Low: ticket changes 1, 3 and 4 reverse parts of tickets the user confirmed; if the user declines one, the spec follows the ticket as written.
  
  ## Next receiver
  - Main, as the dev-ask route owner: after the user confirms this Handoff, apply the Outcome edits, take the user's decision on the four proposed ticket changes, then plan the Atlas v2 spec route. It reads this Handoff, the map and the 16 indexed tickets.
  - Unresolved human authority, none granted by this Handoff: the four ticket changes; approving the spec and its build order; every build stage; every commit; installs and releases (map constraints).

**Changes**

- Counts 16 index entries and lists back-link edits for tickets 02, 06, 07, 12 and the map
- Adds tickets 14 and 15 to the spec route and drops two settled carried items
- Adds four proposed ticket changes and five spec items, including the adapter suite's stage
- Adds Changed targets, Checks, three more Low risks, and a receiver with the user authority needed
- Summary: 1 of 5 points unchanged · Details: edited

## Diff

```diff
--- original
+++ final
@@ -1,9 +1,9 @@
 **Summary**
 
-- Map resolved: all 13 tickets closed, Not yet specified empty
-- Decision index is the map's Decisions so far, ending with Decide v2 additions
-- Spec route gets ticket 07's list and the Passed on lists of tickets 12, 13, 16 and 17
-- Passed on includes a shared host-adapter test suite plus a fake host
+- Map resolved: all 16 indexed tickets closed, Not yet specified empty
+- Later decisions never reached tickets 02, 06, 07, 12 or the map; the Handoff lists the edits
+- Spec route gets the Passed on lists of tickets 07, 12, 13, 14, 15, 16 and 17
+- Four ticket changes and five spec items proposed; the user confirms the changes first
 - Low risk: catch-up cost and 0.3 match threshold are estimates until stage 7 data
 
 **Details**
@@ -11,12 +11,48 @@
 # Handoff: Wayfinder map Atlas v2, resolved
 
 ## Outcome
-- Map ~/dev/atlas/.scratch/atlas-v2/map.md is resolved: all 13 tickets closed, no open tickets, Not yet specified is empty. The decision index is the map's Decisions so far, ending with Decide v2 additions.
-- Passed to the spec route: ticket 07's list and the "Passed on" lists of tickets 12, 13, 16 and 17, including the shared test suite every host adapter must pass, plus a fake host.
-- Route impact: changed
+- Map ~/dev/atlas/.scratch/atlas-v2/map.md is resolved: all 16 index entries are closed (the 13 tickets in `issues/` plus dotfiles tickets 01, 04 and 05), no ticket is open, and Not yet specified is empty. The decision index is the map's Decisions so far, ending with Decide v2 additions.
+- The final review found two kinds of gap. First, later decisions never reached the tickets they changed: tickets 12 and 16 list changes to tickets 02, 06 and 12, but those tickets carry no Later change line for them. These lines record decisions already made; Main applies them once the user confirms this Handoff:
+  - Ticket 02: Later change lines for tickets 12 and 16. The stored record gains the cleaned page text, other links and the scope choice; a changed page gets the check in code and the claim-level update, so "A changed page is re-summarized" is stale; images are accepted; each claim gains its quote, position and basis tag; each record gains its summary history.
+  - Ticket 06: Later change lines for tickets 12 and 16. `add` gains the outcomes "pick scope", "already stored as <link>" and "re-read, no meaningful change"; links get the three-layer cleanup and stored links are matched before any read; Atlas reads pages through the read port, so section 6 item 1's "the calling agent reads the page" no longer holds and `add` takes links; a fifth role, `atlas_escalate`, so section 3 item 4 (`atlas-init` writes "the four Atlas roles") and section 5 item 1 say five; the omp gateway and Jev calls sit behind ports as adapters.
+  - Ticket 12: a Later change line for ticket 16. `add` does the stored-link lookup itself; quotes are the claim locators; removing the reader's header and counter lines and detecting "pick scope" from the `Method` line move into the OMP adapter, so core uses the read port's kind hint.
+  - Ticket 07: Later change lines for tickets 15 and 16 (ticket 17 already has one). Stage 2's "omp-gateway and Jev clients" become the call, judge and quota ports with their OMP and Jev adapters; stage 3's `add` brings the read port and its OMP adapter; stage 4's summary-model gate is met (`atlas_summarize` starts at Sonnet 5.5 `high`).
+  - Map: the standing decision on Atlas models gains "Changed on 2026-11-09 by Decide source summarization method: a fifth role, `atlas_escalate`"; "one vault on this Mac" becomes g10 (ticket 14); the index lines for 06 ("four omp roles") and 07 ("The summary-model prototype must resolve before real data") are updated.
+- Passed to the spec route: the "Passed on" lists of tickets 07, 12, 13, 14, 15, 16 and 17 (the other nine index entries carry no spec-route list). Two carried items are already settled and drop out: ticket 07's summary-model gate (ticket 15 resolved it) and ticket 12's "how the agent looks up a stored link before reading it" (ticket 16 settled it). This review adds five spec items:
+  1. One adapter contract and where the shared test suite and fake host sit. Ports are split across tickets (store interface, 06 section 4; read, call and judge, 16; quota, 17), and Reconcile review, setup and diagnostics are not ports. Define one list of ports plus optional capabilities, each with a fallback when absent (Reconcile's "not cross-checked" is one, and a new harness has no dotagents trusted-caller entry). Ticket 07 has no stage for the suite and fake host: recommended placement is with the stage 2 ports, covering the read, call, judge and quota ports, with the OMP adapter and ticket 13's replay read adapter passing it.
+  2. Which setup and status facts the OMP adapter supplies, so core names no omp setting: the `modelRoles` lines printed on exit 3 (ticket 06 section 5 item 4), `atlas-init`'s role setup, and `status`'s omp version warning (ticket 14 item 11).
+  3. Stage 2 size. Ticket 07 stage 2 now holds the whole schema, `config.toml`, the clients, call records, spend view, cap, window guard, confirm settings, `status` and `atlas-init`, before anything is usable at stage 4. Decide which wait for the stage that first uses them (the cap, window guard and confirm settings first matter at stage 3's batch `add`), and ship no setting without a consumer.
+  4. `status` size. It now shows profile, store, roles, Jev, Reconcile, counts, inbox, version, spend, windows, redo count and confirm settings (tickets 06, 14, 17). Specify a reply that lists what needs action first, each with its fix, and puts the rest behind a detail option.
+  5. Jev as one dependency. Jev serves rerank, wide gather, claim support, copy flags and topic marks through an OpenRouter endpoint named `alpha` (ticket 16's evidence file). Rerank and wide gather fall back to Opus, support checks and marks skip, and the copy flags' not-set-up case is open (ticket 12). State each degraded behavior in one table, and put request and reply shape checks in the judge port's contract tests.
+- Second, four open points this review proposes as ticket changes. Each needs the user's decision before the spec relies on it, and a confirmed one gets a Later change note in its ticket:
+  1. Ticket 06 section 5 item 3, wide gather: Jev's P >= 0.3 set alone decides which stored sources the agent reads. Ticket 17 settled the same pattern by searching every topic "so Jev never decides what is read". Proposed: Jev's candidates are added to the BM25 candidates from the agent's phrasings, and the rest by P are one Next away. The form is the user's call.
+  2. Tickets 12 and 17, re-read: ticket 12's 30-day offer leads to a user-accepted re-read with a change check, but ticket 17 names only `add --redo`, which summarizes from scratch, so ticket 16 section 7's claim-level update has no entry point. Proposed: name it, for example an `add` mode `--reread` that runs ticket 12's change check and ticket 16's update, and keep `--redo` as the rebuild.
+  3. Tickets 06 and 17, reply and confirm: cap and window yields, pick scope and summary failed all wait for a human, but the reply has `ok`, exit codes 0-3 (done, failed, bad input, not set up) and a Next, with no outcome for them. Ticket 17 section 6 has `atlas-ask` skip a stop set to `never`, so the confirm policy lives in skill prose that every new host front door must copy. Proposed: one "needs a decision" outcome with typed options, and the CLI enforces the confirm setting; the mechanism is the user's call.
+  4. Tickets 06 and 17, confirm defaults (the user set the current ones): every change defaults to `always`, so "Add these links" or "Summarize this link" asks a second time after the user said so. Option: a change the user asked for in so many words runs on that request, as Reconcile already takes the user's words as approval (ticket 06 section 6 item 5), while agent-proposed changes (research-end source adds, note and tally proposals, plan starts, version saves) and paid-at-scale ones (a redo, a batch of links) keep their one confirm. The user may instead keep `always` and flip single settings.
+- Route impact: changed. The map returns to dev-ask to plan the Atlas v2 spec route.
+
+## Changed targets/effects
+- The Reconcile record is saved in `.scratch/atlas-v2/reviews/`, as the user asked.
+- None yet for the ticket and map edits listed in Outcome: they are applied only after the user confirms this Handoff.
+- On the user's confirmation: the Handoff goes to `dev-ask`; the map gets no new Decisions-so-far line.
 
+## Checks
+- Map resolved
+  Behavior: every indexed ticket is resolved and Not yet specified is empty
+  Check: read each ticket's Status line and the map's Not yet specified section; expect resolved and empty
+  Observed: the 13 files in `issues/` and dotfiles tickets 01, 04 and 05 are resolved, matching the 16 index entries; the section holds only its comment; pass
+- Spec-route lists
+  Behavior: every index entry that passes work to the spec route is named in Outcome
+  Check: read each ticket's Passed on section; expect lists only in tickets 07, 12, 13, 14, 15, 16 and 17
+  Observed: the other nine entries carry none; pass
+- Back-link and ticket-change findings rest on ticket text only; nothing was run.
+
 ## Blocker/risk
-- Low: the catch-up cost (about $0.02 for 20 topics) and the 0.3 match threshold are estimates until real topics exist (stage 7 data).
+- Low: the catch-up cost (about $0.02 for 20 topics) and the 0.3 match threshold are estimates until real topics exist (stage 7 data). Without Jev, the Opus rerank cost of a catch-up is not estimated anywhere.
+- Low: the summary-model default rests on 16 pages with one run per setup, and Jev both steered the repairs and judged support (ticket 15 caveats); the quality check re-measures it.
+- Low: ticket 13 asks the user for about 10 minutes of spot checks per lane per run plus a 30-claim label review; its own passed-on item on narrowing them should be settled early in the spec.
+- Low: ticket changes 1, 3 and 4 reverse parts of tickets the user confirmed; if the user declines one, the spec follows the ticket as written.
 
 ## Next receiver
-- dev-ask, to plan the Atlas v2 spec route after this review
\ No newline at end of file
+- Main, as the dev-ask route owner: after the user confirms this Handoff, apply the Outcome edits, take the user's decision on the four proposed ticket changes, then plan the Atlas v2 spec route. It reads this Handoff, the map and the 16 indexed tickets.
+- Unresolved human authority, none granted by this Handoff: the four ticket changes; approving the spec and its build order; every build stage; every commit; installs and releases (map constraints).
\ No newline at end of file
```

## Spend

| Reviewer | Model | Tokens | Cost |
|---|---|---|---|
| A | anthropic/claude-opus-5-5 · medium | 1,106,346 | 1.659193 USD |
| B | anthropic/claude-sonnet-5-5 · high | 2,088,291 | 1.771964 USD |
| Total | | 3,194,637 | 3.431157 USD |
