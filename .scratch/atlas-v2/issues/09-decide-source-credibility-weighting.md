Type: grilling
Status: resolved
Parent: [Atlas v2 and portable skill plugins](../map.md)
Blocked by: 02

## Question

Should Atlas weight sources by credibility, and if so, how? Start from prior art (gathered as a short research step), then decide: what signals count (author, publisher, track record, subject expertise); how per-author, per-subject trust notes interact with automatic judgement; how trust changes over time (an unknown author who becomes relevant); and how to avoid false negatives from weighting that is too strict. The v2 minimum is already settled in [Define Atlas v2 requirements](02-define-atlas-v2-requirements.md); this ticket decides anything beyond it.

## Answer

Settled by grilling with the user on 2026-10-22 over seven rounds, and confirmed by the user ("Confirm", twice: once for the reviewed proposal, once for the final version with items 13 and 15 updated). Every question, with its options as shown and the user's answers quoted exactly, is in [the interview record](../reviews/09-interview.md). Evidence: [prior-art research](../inputs/09-credibility-prior-art.md) (17 primary sources and 5 product docs) and counts over the read-only v1 library (in the interview record's header).

Cross-checked by Reconcile run `reconcile-20261021T184301Z-938527` (5 turns, 2.18 USD; [record](../reviews/09-reconcile-record.md)). On the user's request ("the redesign decisions are all opened for challenge … The Reconcile integrate, however, should be integrated. Where and when should it be used are open for changes."), the run reopened every answer in this ticket and ticket 02's credibility and Reconcile sections. The reviewers kept the design. They added the rules on how notes relate to labels, what happens when the label check fails, the tally reset, and reviewing a revision offered inside an answer. The user then replaced that last rule (rounds 6–7), so items 13 and 15 changed after the run and were not re-reviewed. The map's final Reconcile run covers them.

The user's deciding words that shaped the design, quoted exactly:

- "all these added logic, weighting, count for independent backing, are all naive, presumably, so let's take them as a signal, not a binding, for now."
- "re-reading the summaries every time will be a lot of work, and presumably unncessary"
- "we might want to utilize and leverage its intelligence into our workflow. … This would allow for counter arguments/pros/cons evaluation, etc. … the analysis llm-model gives should be robust, i.e. good/bad/noise/relevant, just like the high/low-value guage i have llm-model judge with they return \"Risks\" after a dev-* workflow execution."
- "The idea for reconcile is to use it mainly for work that will get persisted"
- "persist the change regardless of whether the text changes after Reconcile, but indicate, within the summary output of the usual Reconcile formatting, the new changes Reconcile made that the original text doesn't have."
- "Make this consistent across the framework, just like how i have \"Next\" for cwd skills."

### Who said it

1. No automatic credibility score for sources, authors or publishers. The only signals about who said something are the user's trust notes and independent backing (item 6). An unknown author starts neutral and is never penalised.
2. Nothing is hidden, filtered or ranked lower because of who wrote it. Only the existing per-source archive hides a source. There is no block list in v2.
3. Trust notes take effect only at answer time, and visibly. Search and rerank ignore them, so a note never pushes a source out of results. When sources disagree, the answer shows who says what and which side a note leans to, quoting the note.
4. A trust note holds: who (an author or a publisher), subject (free text, e.g. "agent skills"), lean (towards or against), reason, and date. The answering agent judges whether a question falls under a note's subject, and says so when it applies the note.
5. Author: the page's byline, otherwise the GitHub owner or X handle from the link. Publisher: the organisation behind the site. GitHub, X and YouTube are recorded as the platform, not as the publisher. Each author has one name form, with handles kept as aliases, so a note matches all of that author's sources.

### Independent backing

6. Answers say "backed by N independent sources" for each claim they show. Sources are independent when their authors and publishers differ; a source that cites or links another counts once with it. The count covers only the sources retrieved for that answer, so it can undercount.

### The model's own assessment

7. In the same call that already writes an answer or a draft revision (no extra call, no extra reads), the model labels each claim it shows, with one reason per label:
   - Sound: can carry a conclusion.
   - Doubtful: names a specific flaw or contrary evidence; do not rely on it alone.
   - Noise: not worth acting on; says why (e.g. hype, off-subject, repeat).

   Labels judge a claim on its content and evidence, never on its author's reputation or a trust note. A note that applies is shown beside the label, never folded into it. Relevance stays the reranker's job. Lists sort Sound, Doubtful, Noise, and nothing is hidden. The label format is checked fail-closed, as the completion Risks labels are. If the check fails, the claims are shown unlabelled and the answer or revision says so; nothing is withheld.
8. The model adds a short Model view: counterarguments, pros and cons, and what the sources miss. It is marked as the model's own view and never counts as backing. When the model's own knowledge conflicts with a newer source, both are shown; the model never overrides a source.
9. Answers show the labels and Model view, name the model that wrote them, and keep nothing. A draft topic revision carries them, and a saved version keeps them, labelled as the model's view, with the writing model and thinking level (e.g. `anthropic/claude-opus-5-5:xhigh`). Source records stay page-only, as [Define Atlas v2 requirements](02-define-atlas-v2-requirements.md) requires.

### Re-judging trust over time

10. Re-judging uses only work already being done: the sources already read for the current answer or revision. There is never a separate pass or a re-read of summaries. The agent adds one line to a tally (who, subject, source link, direction) when one of those sources shows either:
    - a noted author backed or contradicted by independent sources; or
    - an un-noted author behind a conclusion-changing claim.

    When a who-and-subject pair reaches a set number of lines, the agent proposes adding or changing a note, with those lines as its evidence, and acts on one confirm. After a proposal, confirmed or declined, that pair's count starts again, so a declined proposal does not return on the next line. Note proposals are not cross-checked automatically (item 13).

### What's new

11. Credibility does not decide what a topic's "what's new" list shows. Any evidence that would change an agreed conclusion is shown, with who says it, its backing count, its label and any note that applies.

### Reconcile

12. Reconcile still reviews every research plan and every topic revision. A revision now includes its labels and Model view, so reviewers check those too. They may change a label or add a counterargument, each change shown with its reason. A saved version also records the reviewer models and the Reconcile run.
13. Reconcile runs only before something is saved:
    - A research plan is reviewed before the user sees it, because work is about to start.
    - A topic revision, including a topic's first agreed understanding, comes as a quick unreviewed draft. The answer ends with Next: "Save this as version N+1?" On yes, Reconcile reviews the draft and the reviewed version is saved. The user then gets the usual short summary, marking what Reconcile added or changed compared with the draft.
    - Read-only answers (what's new, questions, what a source or topic says), source summaries, the inbox and note proposals are never reviewed automatically. The user can invoke Reconcile on any of them.

### Signals, not bindings

14. Notes, backing counts, labels, the Model view and tally proposals inform the user and the answering agent. None of them filters a source or decides a conclusion. The user's saved topic versions remain the only agreed conclusions.

### Answer shape

15. Every Atlas answer has one concise shape: the answer first, then a short Next saying what the user can do with it (e.g. save a revision, research a gap, follow up). This matches the Next in the framework's other skills.

### Changes to earlier decisions

All of these follow from the user's answers in this interview.

- In ticket 02's "Independent cross-check (Reconcile)" section:
  - A topic revision was cross-checked "before the user sees it". It is now cross-checked after the user chooses to save it, and before it is saved (item 13).
  - Source summaries, read-only answers and the inbox were "never cross-checked". They are now not cross-checked automatically, and the user may invoke Reconcile on any of them.
- In ticket 02's "Topics" section, a revision "becomes the next version when the user confirms". The user's confirm now comes before the review, and the saved version may include reviewer changes, which are marked (item 13).
- Additions to ticket 02:
  - Trust notes may name a publisher and carry a lean, reason and date (item 4).
  - The stored record gains a platform field, used instead of the publisher for GitHub, X and YouTube, plus author handle aliases (item 5).
  - Answers gain a backing count, labels, a Model view, the writing model's name and a closing Next (items 6–9 and 15).
  - Atlas keeps a tally of trust-evidence lines, which the agent adds without a confirm (item 10).
  - Saved topic versions also keep the labels, the Model view, the writing model, the reviewer models and the Reconcile run (items 9 and 12).

### Rejected alternatives

- An LLM credibility label per source, or a learned per-author track record: these lean on fame (they misjudge about a third of reliable outlets), are unmeasured on individual authors, and need more overlapping claims than a personal library has.
- Notes that boost search, or notes that decide conflicts: both carry false-negative risk and hide the tilt.
- A user block list: a forgotten block causes silent misses.
- Byline-only author records: most notes would match nothing (64% of v1 authors are "Unknown").
- Notes tied to topics, or "lean towards" notes only: these miss questions outside a topic and cannot express caution.
- Notes that only change when asked, or notes that expire: trust goes stale, or is judged by age instead of evidence.
- Counting every stored source as backing: reposts inflate the count. A whole-library count per claim: costs one more search per claim.
- Re-reading the sources to review notes: too costly. A tally-free check limited to the current batch misses patterns spread across many batches.
- Model view without labels: hard to scan. A separate `atlas_assess` role: one more paid call each time.
- Storing labels on source records: they go stale, and the model's view would mix into page-only summaries.
- Reconcile on every "what's new" answer, or reviewers doing the labelling: both put a paid review on read-only work, and the second leaves read-only answers unlabelled.
- Two confirms on every save: always two stops. Asking again only when reviewers changed the draft: the user chose to save on the first yes and mark the changes instead.

### Passed on

- To [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md): where trust notes and the tally are stored and edited; whether answers and revisions are written by the calling agent or an Atlas role, and so which model is recorded; what runs the fail-closed label check; the tally's line count; how Atlas hands a draft revision, its labels and Model view to Reconcile; and that Atlas shows Reconcile's marked changes as given, not re-summarised.
- To [Decide Atlas build order](07-decide-atlas-build-order.md): the Reconcile skill gains a diff of the reviewed text against the original (the user will build it in a separate session); it lands before Atlas relies on it.
- To quality judging in the map's "Not yet specified" list: labels and backing counts are naive signals, and whether they help is judged there.
