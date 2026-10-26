## Review rounds

| Step | Reviewer/event | Pass | Text | Outcome | Turn |
|---|---|---|---|---|---|
| 1 | A | post-rethink | 77ed7ac9 | edit<br>• Does not say how trust notes affect the model's labels, so a note could tilt them unseen<br>• A failed label check has no defined outcome, which risks withholding answers<br>• A declined note proposal could come back after every new tally line<br>• The Reconcile scope wording and the record of ticket 02's change are inaccurate | 170 s · 14 tools · 352k tokens · wait 1 s |
| 2 | B | post-rethink | 77ed7ac9 | edit · superseded<br>• Notes and labels are both applied in one pass, but how they interact is never stated<br>• Reconcile scope is inconsistent: what's new vs the revision it offers, and note proposals<br>• Earlier-decision additions omit the tally, the backing count and publisher notes<br>• Summary hides backing counts and signals-only; Details use bare ticket numbers | 276 s · 15 tools · 391k tokens · wait 1 s |
| 3 | B | later | 65976716 | edit<br>• A revision inside a what's-new answer has no review rule; note-proposal wording contradicts itself<br>• Changes list omits the backing count, the tally and publisher notes<br>• Summary leaves out backing counts and signals-only; Details use bare ticket numbers<br>• Keeps the other reviewer's note rule, failure outcome, tally reset and Reconcile wording | 130 s · 1 tool · 126k tokens |
| 4 | A | later | 631b362b | accept<br>• Accepts the revised resolution of ticket 09<br>• A revision offered inside an answer is now reviewed, matching the requirements ticket<br>• The changes record and the Summary now match the Details<br>• The note rule, failed-check outcome, tally reset and Reconcile wording are all kept | 30 s · 1 tool · 83.7k tokens |
| 5 | A | closure | 631b362b | accept<br>• Accepts the whole revised resolution of ticket 09 against the human's intent<br>• Items 7, 10 and 13 agree with each other and with the changes record<br>• The Summary points are all supported by the Details | 9 s · 1 tool · 89.3k tokens |
| 6 | apply | — | 631b362b | applied | — |
| 7 | cleanup | — | — | A, B disposed (observed exit) | — |

## Final proposal

**Proposal**

- **Summary**
  
  - No automatic credibility score; nothing is hidden for who wrote it; unknown authors start neutral.
  - Trust notes and backing counts show at answer time and never change search; both are signals only.
  - Same-pass model labels (Sound, Doubtful, Noise) and a Model view; kept only in topic versions.
  - Trust is re-judged from a tally kept during existing work; the agent proposes, the user confirms.
  - Reconcile reviews plans and revisions, now with labels; read-only answers only when asked.
  
  **Details**
  
  Proposal: resolution of the wayfinder ticket "Decide source credibility weighting" (ticket 09).
  
  *Who said it*
  
  1. No automatic credibility score for sources, authors or publishers. The signals about who said it are the user's trust notes and independent backing (item 6). An unknown author starts neutral and is never penalised.
  2. Nothing is hidden, filtered or ranked lower because of who wrote it. Only the existing per-source archive hides a source. There is no block list in v2.
  3. Trust notes take effect only at answer time, and visibly. Search and rerank ignore them, so a note never pushes a source out of results. When sources disagree, the answer shows who says what and which side a note leans to, quoting the note.
  4. A trust note holds: who (an author or a publisher), subject (free text, e.g. "agent skills"), lean (towards or against), reason, and date. The answering agent judges whether a question falls under a note's subject, and says so when it applies the note.
  5. Author: the page's byline, otherwise the GitHub owner or X handle from the link. Publisher: the organisation behind the site; GitHub, X and YouTube are recorded as the platform, not as the publisher. Each author has one name form, with handles kept as aliases, so a note matches all of that author's sources.
  
  *Independent backing*
  
  6. Answers say "backed by N independent sources" for each claim they show. Sources are independent when their authors and publishers differ; a source that cites or links another counts once with it. The count covers only the sources retrieved for that answer, so it can undercount.
  
  *The model's own assessment*
  
  7. In the same call that already writes an answer or a proposed revision (no extra call, no extra reads), the model labels each claim it shows, with one reason per label:
     - Sound: can carry a conclusion.
     - Doubtful: names a specific flaw or contrary evidence; do not rely on it alone.
     - Noise: not worth acting on; says why (e.g. hype, off-subject, repeat).
     Labels judge a claim on its content and evidence, never its author's reputation or a trust note; an applicable note is shown beside the label, never folded into it. Relevance stays the reranker's job. Lists sort Sound, Doubtful, Noise, and nothing is hidden. The label format is checked fail-closed, as the completion Risks labels are: if the check fails, the claims are shown unlabelled and the answer or revision says so; nothing is withheld.
  8. The model adds a short Model view: counterarguments, pros and cons, and what the sources miss. It is marked as the model's own view and never counts as backing. When the model's own knowledge conflicts with a newer source, both are shown; the model never overrides a source.
  9. Answers show the labels and Model view, name the model that wrote them, and keep nothing. A proposed topic revision carries them, and a confirmed version keeps them, labelled as the model's view, with the writing model and thinking level (e.g. `anthropic/claude-opus-5-5:xhigh`). Source records stay page-only, as the Define Atlas v2 requirements ticket requires.
  
  *Re-judging trust over time*
  
  10. Re-judging uses only work already being done: the sources already read for the current answer or revision. There is never a separate pass or a re-read of summaries. When one of those sources shows a noted author backed or contradicted by independent sources, or an un-noted author behind a conclusion-changing claim, the agent adds one line to a tally: who, subject, source link, direction. When a who-and-subject pair reaches a set number of lines, the agent proposes adding or changing a note, with those lines as its evidence, and acts on one confirm. After a proposal, confirmed or declined, that pair's count starts again, so a declined proposal does not return on the next line. Note proposals are not cross-checked automatically (item 13).
  
  *What's new*
  
  11. Credibility does not decide what a topic's "what's new" list shows. Any evidence that would change an agreed conclusion is shown, with who says it, its backing count, its label and any note that applies.
  
  *Reconcile*
  
  12. Reconcile keeps the review points of Define Atlas v2 requirements: every research plan and every proposed revision. A proposed revision now includes its labels and Model view, so reviewers check those too; they may change a label or add a counterargument, each change shown with its reason. A confirmed version also records the reviewer models and the Reconcile run.
  13. Reconcile is mainly for work that leads to persisted conclusions: research plans and proposed revisions. Read-only answers (what's new, questions, what a source or topic says), source summaries, the inbox and note proposals are not reviewed automatically. The user can invoke Reconcile on any of them. A proposed revision offered inside an answer is still reviewed before the user sees it; the rest of that answer is not reviewed automatically.
  
  *Signals, not bindings*
  
  14. Notes, backing counts, labels, the Model view and tally proposals inform the user and the answering agent. None of them filters a source or decides a conclusion. The user's confirmed topic versions remain the only agreed conclusions.
  
  *Changes to earlier decisions*
  
  - Changed in the reopened "Independent cross-check (Reconcile)" section of Define Atlas v2 requirements: source summaries, read-only answers and the inbox were never cross-checked; now they are not cross-checked automatically, and the user may invoke Reconcile on any of them (item 13). Nothing else is overturned.
  - Additions to Define Atlas v2 requirements: trust notes may name a publisher and carry a lean, reason and date (item 4); the stored record gains a platform field, used instead of the publisher for GitHub, X and YouTube, and author handle aliases (item 5); answers gain a backing count, labels, a Model view and the writing model's name (items 6-9); Atlas keeps a tally of trust evidence lines, which the agent adds without a confirm (item 10); confirmed topic versions also keep the labels, Model view, writing model, reviewer models and Reconcile run (items 9 and 12); a revision offered inside an answer is still reviewed (item 13).
  
  *Passed on*
  
  - To Decide Atlas v2 architecture (ticket 06): where trust notes and the tally are stored and edited; whether answers and revisions are written by the calling agent or an Atlas role, and so which model is recorded; what runs the fail-closed label check; the tally's line count; how Atlas hands labels and the Model view to Reconcile.
  - To quality judging in the map's "Not yet specified" list: labels and backing counts are naive signals, and whether they help is judged there.
  

## Spend

| Reviewer | Model | Tokens | Cost |
|---|---|---|---|
| A | anthropic/claude-opus-5-5 · high | 525,385 | 1.141753 USD |
| B | anthropic/claude-sonnet-5-5 · xhigh | 516,468 | 1.037209 USD |
| Total | | 1,041,853 | 2.178962 USD |
