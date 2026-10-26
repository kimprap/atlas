# Ticket 09 interview: questions as shown and the human's answers

Ticket: /Users/kim/dev/atlas/app/.scratch/atlas-v2/issues/09-decide-source-credibility-weighting.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label and description are the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Evidence shown with the questions: [prior-art research](../inputs/09-credibility-prior-art.md) and a count over the v1 library (673 source summaries, read-only): author "Unknown" in 433; 291 of those are github.com and 85 are x.com links; publisher "Unknown" in 395; the X platform appears as "X" (49), "x.com" (15) and "X (Twitter)" (9); 186 of 207 named authors appear once.

## Round 1

### auto_score
Question: "Should Atlas judge credibility automatically? Prior art (inputs/09-credibility-prior-art.md): LLM credibility ratings agree with experts only moderately (ρ≈0.59), lean on memorised fame, misjudge about a third of reliable outlets, and nobody has measured them on individual authors. Learned track records need many overlapping claims per source, which a personal library lacks."
- No automatic score; notes plus corroboration (Recommended) — "Credibility comes from your trust notes. Answers also say how many independent stored sources back a claim. Unknown authors start neutral, never penalised. Matches ticket 02 dropping v1's assessment ratings."
- LLM credibility label at answer time — "The answering model labels each cited source (e.g. high/medium/low with a reason). Shown, never used to filter. Risks the fame bias against unknown X accounts and niche practitioners."
- Learned per-author track record — "Atlas tracks how often each author's claims are later backed or contradicted, per subject. Needs much more data than the library has; better suited to the later automated version."
Answer: No automatic score; notes plus corroboration

### notes_apply
Question: "Where do your trust notes (e.g. 'lean towards Matt Pocock on agent skills') take effect? Research shows models over-agree with views the user states, so a hidden note can tilt answers silently."
- Answer time, visibly (Recommended) — "Search and rerank ignore notes, so notes never push a source out of results. When sources disagree, the answer shows who says what and which side your note leans to, quoting the note."
- Answer time plus a search boost — "As above, and noted authors also move up in search (like Kagi's raise/lower). Better recall of favoured voices; can crowd out others in a top-10."
- Notes decide conflicts — "When a noted author disagrees with others, the answer adopts the noted side and mentions the rest briefly. Strongest lean; most false-negative risk."
Answer: Answer time, visibly

### exclusion
Question: "Can anything be hidden because of who wrote it? Deployed systems avoid automatic exclusion; hard filters are explicit user tools."
- Never by credibility (Recommended) — "Only the existing per-source archive hides a source. No block list in v2. A weak source still appears, labelled by who wrote it."
- User block list — "You can block an author or publisher; their sources leave search and answers until unblocked. Explicit and reversible, but a forgotten block causes silent misses."
Answer: Never by credibility

### author_record
Question: "How author and publisher are recorded. In the v1 library, 64% of summaries say author 'Unknown', but 376 of those 433 are GitHub or X links whose owner or handle is in the URL. Publisher is often the platform, split as 'X', 'x.com' and 'X (Twitter)'."
- Derive and normalise (Recommended) — "Author: byline, else the GitHub owner or X handle from the link. Publisher: the organisation behind the site; GitHub, X and YouTube are recorded as the platform, not the publisher. One name form per author, with handles kept as aliases so a note matches all their sources."
- Page byline only — "Record only what the page states; 'unknown' otherwise. Simpler, but most notes would match nothing."
Answer: Derive and normalise

## Round 2

### note_shape
Question: "What a trust note holds and how it matches. v2 has no fixed labels, so a note's subject can't point at a tag."
- Who, subject, lean, reason, date (Recommended) — "Who is an author or a publisher. Subject is free text ('agent skills'). Lean is towards or against. The answering agent judges whether a question falls under the subject, and says so when it applies a note."
- Notes tied to topics — "A note applies only inside the topics you name. Exact, but a question outside those topics never uses it."
- Lean towards only — "Same as the first option, but no 'against' notes. Simpler; can't express 'treat vendor benchmarks with caution'."
Answer: Who, subject, lean, reason, date

### rejudge
Question: "Trust must be re-judged over time (settled in ticket 02). With no automatic score, how does a note change?"
- Agent proposes, you confirm (Recommended) — "When a topic revision or answer shows an un-noted author backing several conclusion-changing claims on a subject, or a noted author contradicted by independent sources, the agent proposes adding or changing a note, with the evidence. One confirm, like other changes."
- Only when you ask — "Notes change only on request. No proposals; trust can go stale unnoticed."
- Notes expire — "Each note asks to be re-confirmed after a set time (e.g. 12 months). Catches staleness by age, not by evidence."
Answer: Agent proposes, you confirm (note: care on how we could do this efficiently as well. re-reading the summaries every time will be a lot of work, and presumably unncessary, especially if the topic-related summaries grew in quantity.)

### corroboration
Question: "What counts as independent backing for a claim? A thread that reposts a blog post says the same thing twice from one origin."
- Different origin only (Recommended) — "Count sources by different authors and publishers, and count once when one cites or links another. Answers say 'backed by N independent sources'."
- Every stored source — "Count every source that makes the claim. Simpler; reposts inflate the count."
Answer: Different origin only (note: all these added logic, weighting, count for independent backing, are all naive, presumably, so let's take them as a signal, not a binding, for now. Unless you have a strong opinion on it.)

### whats_new
Question: "Does credibility affect a topic's 'what's new' list (only evidence that would change an agreed conclusion is shown)?"
- No; shown with who and backing (Recommended) — "Any conclusion-changing evidence is shown, with who says it, its independent-backing count, and any note that applies. Matches 'never hidden by credibility'."
- Single unknown voices go to the count — "A claim from one un-noted author with no other backing goes into the 'other new sources' count, not the list. Less noise; an early unknown voice can be missed."
Answer: No; shown with who and backing (note: this is fine, but take into account my previous comment)

## Round 3

### rejudge_cost
Question: "Agreed: notes, backing counts and proposals are signals, never binding. No strong objection from me. To re-judge trust without re-reading summaries:"
- Piggyback plus a small tally (Recommended) — "Only sources the agent already read for the current answer or revision are checked; never a separate pass. When one shows a noted author backed or contradicted, or an un-noted author behind a conclusion-changing claim, the agent adds one line (who, subject, source link, direction) to a tally. It proposes a note change once a tally line count is reached. No re-reading, ever."
- Piggyback only — "Same check, but no tally: a proposal needs the current batch alone to show the pattern. Nothing new stored; misses patterns spread across many small batches."
- Review on request — "You ask 'review my notes' and the agent re-reads the relevant sources. Thorough but costly, which is what you want to avoid."
Answer: Piggyback plus a small tally (note: additionally, given that i will be running frontier llm-model at all times for Atlas topic/research related queries, we might want to utilize and leverage its intelligence into our workflow. All topics that will be created, the llm-model will more than likely is an expert in the field as well, so their analysis will be relevant. This would allow for counter arguments/pros/cons evaluation, etc. Propose how might we do this efficiently. Note, the analysis llm-model gives should be robust, i.e. good/bad/noise/relevant, just like the high/low-value guage i have llm-model judge with they return "Risks" after a dev-* workflow execution. This should be kept robust and non brittle.)

### backing_scope
Question: "The independent-backing count covers:"
- Sources already retrieved (Recommended) — "Only the sources the search returned for this answer. No extra reads; can undercount, which is fine for a signal."
- Whole library — "A separate search for every claim shown. More complete; one more search per claim."
Answer: Sources already retrieved

### note_crosscheck
Question: "Ticket 02 cross-checks research plans and proposed revisions with Reconcile. Are proposed note changes cross-checked too?"
- No (Recommended) — "A note is your own preference and a proposal already shows its evidence; a review adds cost and delay for little gain."
- Yes — "Reconcile reviews each proposed note change before you see it. Catches a proposal built on thin evidence."
Answer: No

Context for round 4: the "Risks" gauge the human refers to is the completion input contract (`.config/agents/references/completion-presentation-input.md`): each line carries one fixed label, `High`, `Low` or `Negligible`, each defined by what to do about it, with a reason, sorted, and checked fail-closed by `completion-presentation/scripts/render.py`.

## Round 4

### model_view
Question: "Using the frontier model's own expertise. Proposal modelled on your Risks gauge (fixed labels, each defined by what to do, one reason each, checked fail-closed). This judges claims on their merits, not authors by fame, so 'no automatic credibility score of sources' still holds."
- Same-pass labels plus model view (Recommended) — "In the call that already writes an answer or proposed revision (no extra call, no extra reads), the model labels each claim it shows: Sound (can carry a conclusion), Doubtful (names a specific flaw or contrary evidence; don't rely on it alone), Noise (not worth acting on; says why: hype, off-subject, repeat). Relevance stays the reranker's job. It adds a short Model view: counterarguments, pros/cons, what the sources miss, marked as the model's own view and never counted as backing. Nothing hidden; lists sort Sound, Doubtful, Noise. If its own knowledge conflicts with a newer source, both are shown; it never overrides a source. Revisions still get Reconcile's cross-check."
- Model view only, no labels — "The counterarguments/pros-cons section, but claims stay unlabelled. Fewer moving parts; harder to scan a long what's-new list."
- Separate assessment role — "A new atlas_assess role reviews each answer or revision in its own call. Independent of the writer, but one more paid 2–4 s call every time."
Answer: Same-pass labels plus model view (note: re-evaluate how Reconcile should be integrated with this new change as well. I still want Reconcile to be integrated.)

### view_storage
Question: "Where does the model's assessment live?"
- Topic versions only (Recommended) — "Answers show it and keep nothing. A proposed topic revision carries it, and a confirmed version keeps it, labelled as the model's view. Source records stay page-only, as ticket 02 requires."
- Also on source records — "Labels are saved per claim so later answers reuse them. Saves tokens, but labels go stale as new evidence arrives and mix the model's view into page-only summaries."
Answer: Topic versions only (note: include the model used as well, i.e. "anthropic/claude-opus-5-5:xhigh", etc.)

## Round 5

### reconcile_fit
Question: "How Reconcile fits the model's labels and Model view. Today (ticket 02) Reconcile checks every research plan and every proposed revision, including a topic's first agreed understanding; it never checks summaries, read-only answers or the inbox."
- Same review points, wider check (Recommended) — "Reconcile still runs on every plan and proposed revision. Its reviewers now also check the revision's claim labels and Model view: they may change a label or add a counterargument, each change shown with its reason. A confirmed version records the writer model (e.g. anthropic/claude-opus-5-5:xhigh), the reviewer models and the Reconcile run. Read-only answers, summaries and note proposals stay unreviewed; an answer names the model that wrote its labels. No new review calls."
- Also review 'what's new' answers — "As above, plus Reconcile checks the labels on every 'what's new' answer before you see it. That reopens ticket 02, which keeps read-only answers unreviewed, and adds a paid review to every check."
- Reviewers do the labelling — "The writer adds no labels; Reconcile's reviewers label claims during the revision review. Labels come from independent models, but read-only answers get none."
Answer: Same review points, wider check (note: yes. summaries, etc are tedious work, and reconcile or model view would be mostly redundant. My current idea, if i understand the current framework design correctly, is that the model view could be one of the candidates for the "proposal" that Reconcile will run on. The idea for reconcile is to use it mainly for work that will get persisted, so "what's new", or "what is this topic talking about", or any read-only inquiries (that might include analysis, or not), do not require Reconcile, unless user invokes it themselves.)

## Reconcile run

Run `reconcile-20261021T184301Z-938527` on the drafted resolution ([record](09-reconcile-record.md)). The human's approvals, exact:

- First brief: "approve - the redesign decisions are all opened for challenge, in case there are smarter ways to do what we're trying to achieve. One that is more robust, efficient, reliable, and not overly restricting (like the v1). The Reconcile integrate, however, should be integrated. Where and when should it be used are open for changes."
- Revised brief (reopened every ticket 09 answer, ticket 02's "Credibility (v2 minimum)" section, and where and when Reconcile is used in ticket 02's "Independent cross-check (Reconcile)" section; Reconcile stays integrated): "approve - review B, change thinking level to xhigh."
- Models-changed gate: "approve"

## Round 6 (after the Reconcile run)

### inline_revision
Question: "A proposed revision offered inside a 'what's new' answer: reviewed by Reconcile before you see it?"
- Keep the reviewers' line (Recommended) — "The revision part is reviewed, and the rest of the answer isn't. Matches 'Reconcile for work that gets persisted', because a confirmed revision becomes a topic version."
- Review only when I confirm — "The 'what's new' answer arrives unreviewed and fast. Reconcile runs on the revision only after you say you want it, before it is saved."
Answer: Keep the reviewers' line (note: does "What's new" persist? Isn't it only a read-only query? How does the current design work again? The inquiry seems to be like a simple question that agent could quickly answer. Or should we split it into 2 steps? 1 is the quick answer, without reconcile, with an ending note, or "Next", asking if user wants to persist it, in which Reconcile would be run before they persist. The persisted changes finalized after the Reconcile run should be summarized to user, as usual. Revisit this. For output format, make sure the follow the same principle of concise summaries, and the formatting should be consistent across all inquiries.)

### confirm
Question: "Confirm the resolution above (Summary here; Details items 1–14 in the record) to close the ticket?"
- Confirm (Recommended) — "I record your answers, close the ticket, add it to the map's Decisions so far, and pass the listed items on to ticket 06."
- Change something first — "Name the item to change."
Answer: Confirm

Assistant's factual reply at that time (evidence, not a decision): "what's new" is read-only, but ticket 02's topic answer ends with "a proposed revision to confirm", and ticket 02 cross-checks every proposed revision "before the user sees it", so every "what's new" answer would wait on a paid Reconcile run.

## Round 7

### two_step
Question: "Two steps: (1) the 'what's new' answer comes fast and unreviewed, and ends with a short Next: 'Save this as version N+1?'. (2) On yes, Reconcile reviews the draft revision before anything is saved. After the review:"
- Save; ask again only if changed (Recommended) — "If reviewers accept the draft unchanged, it is saved and you get the usual short summary. If they changed it, you see the changes (before and after) and confirm once more. Fewest stops; you never save text you haven't seen."
- Always confirm the reviewed text — "After every review you see the reviewed revision and confirm again before it saves. Always two stops."
- Save and summarise — "Your first yes covers reviewer changes; the version saves and the summary lists what reviewers changed. One stop; a change you'd reject is saved, and you'd have to revise it."
Answer: Save; ask again only if changed (note: persist the change regardless of whether the text changes after Reconcile, but indicate, within the summary output of the usual Reconcile formatting, the new changes Reconcile made that the original text doesn't have. What do you think? This is actually something i have in mind that i would like to refine the Reconcile skill itself as well. Currently, Reconcile only shows the final proposal/summary, but it doesn't currently show how the reconciled proposal differs from the final reconcile output. If Reconcile benefits from this, does making the change only on Reconcile skill itself enough to propogate this capability onto Atlas, i.e. the changes diff to be shown to user, etc.? If you agree, i'll fix it in a separate session.)

### scope
Question: "Apply the same split everywhere a read-only answer offers something to save, with the same concise answer shape and a closing Next?"
- Yes, all inquiries (Recommended) — "Every read-only answer (what's new, questions, what a source or topic says) uses one shape: short answer first, then Next when something could be saved. Reconcile runs only after you choose to save. Research plans keep being reviewed before you see them, because you only see a plan when work is about to start."
- Only 'what's new' — "Other answers keep their own shapes."
Answer: Yes, all inquiries (note: Yes, the "Next" part will be useful for users. It guides the user on how the framework is meant to be used. User could forget, or maybe had no idea since the start, what they are suppose to do with the output. Make this consistent across the framework, just like how i have "Next" for cwd skills.)

Assistant's reply at that time: agreed with saving on yes and marking reviewer changes, since versions are numbered and a disliked change is undone by the next revision. A diff built by the Reconcile controller reaches Atlas through `skill://reconcile`, provided Atlas shows Reconcile's marked changes as given rather than re-summarising them (passed on to ticket 06); the build order gets the constraint that the Reconcile diff lands before Atlas relies on it (passed on to ticket 07). Items 13 and 15 were changed after the Reconcile run and were not re-reviewed; the map's final Reconcile run covers them.

## Final confirmation

Question: "Confirm ticket 09 as the reviewed proposal plus the updated items 13 and 15, the added changes and the pass-ons shown above?"
- Confirm (Recommended) — "I record the answer, close the ticket, update the map, and pass the items on to the Atlas architecture and build-order tickets."
- Change something first — "Name the item."
Answer: Confirm
