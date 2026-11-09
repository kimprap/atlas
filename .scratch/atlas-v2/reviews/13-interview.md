# Ticket 13 interview: questions as shown and the human's answers

Ticket: ~/dev/atlas/.scratch/atlas-v2/issues/13-decide-quality-check.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label is the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Facts shown before round 1 (checked on g10, 2026-11-09):

- Ticket 08's test set survives in git history (`570617c^`): 47 queries (7 real, 34 with one target source each, 6 broad) and 1,535 graded pairs over 516 v1 sources; 413 of them are graded relevant to at least one query. Each v1 source id maps to its link through the frozen vault's `canonical_url`, so the grades can be reused by link.
- v2 stores each page's cleaned text (ticket 12). A test library can replay pages from storage: no re-reads, and both versions see identical text.
- v1's evaluation plan (never run; `.agents/plans/archive/2026-07-29-2056_atlas-evaluation-loop.md`) had the same shape: fixed corpus, read-only on the live library, baseline vs candidate, blind A/B by a fresh reviewer. Its machinery is tied to v1 files and is not reusable.
- Research on judging summaries: FineSurE ([ACL 2024](https://arxiv.org/abs/2407.00908)) scores faithfulness (share of summary sentences with no errors), completeness (share of the page's key facts covered) and conciseness (share of sentences tied to a key fact). These per-fact checks track human judgment better than one score per summary, and key facts written by people work better than model-written ones.
- Rough costs: re-adding 516 pages at Opus medium ≈ $25–40 once [INFERENCE: ticket 16's ≈$0.05 per summary plus rethink and Jev]; a Jev search ≈ $0.001, so the 47 queries ≈ $0.05 per version; Jev checks per page < $0.01.

## Round 1

### lanes
Question: "1. What does the quality check judge?"
- Three lanes: summaries, search, answers (Recommended) — "Each lane has its own fixed cases and runs on its own. A change to the rubric or `atlas-rethink` runs only the summary lane, a ranker change only search, an answer-prompt or label change only answers. Covers every tuning target build stage 5 names (abstract, rerank, answer prompts, claim labels) plus the rethink."
- Summaries and search only — "No answers lane. Whether the Sound/Doubtful/Noise labels and backing counts help, which ticket 09 left to this check, is judged only by your day-to-day use."
- One end-to-end score — "Each case runs add → find → ask and gets one overall grade. Fewer cases to keep, but a drop cannot be traced to the step that caused it."
Answer: Three lanes: summaries, search, answers, with this note, given exactly:

```text
thoroughly think this through. make sure this is complete enough, given what it is trying to do.
```

### where
Question: "2. Where does it run, and what may it write?"
- Repo-only dev tool, own eval profile (Recommended) — "A script in the Atlas repo, not shipped in the plugin and not reached through `atlas-ask`; run by hand from an omp session in `~/dev/atlas`. It calls Atlas core through its ports (a replay adapter serves stored page text), reads and writes only a separate `eval` profile store, and never touches a real profile. Run results are kept as rows in that store, which host-backup already copies."
- An 11th CLI command, `eval` — "Shipped in the plugin and reached through `atlas-ask`, so later public users can tune their own setup. Adds a command, setup and docs to the shipped surface before anyone else uses Atlas."
- Ad-hoc eval sessions, as in tickets 08 and 11 — "A throwaway script per question. Nothing to build in stage 5, but each comparison rebuilds its setup and results cannot be compared across runs."
Answer: Repo-only dev tool, own eval profile

### library
Question: "3. What test library and query set does it start from?"
- Ticket 08's pool, re-added once (Recommended) — "Build the `eval` profile by adding the 516 links in ticket 08's graded pool once (links that no longer read are dropped and counted). Reuse the 47 queries and 1,535 grades by link. Pages are then replayed from stored text, never re-read, so every run sees the same pages. New cases enter only when you promote a real query from the store's query records. About $25–40 once at Opus; much less if ticket 15 picks a cheaper model first."
- All 673 v1 links — "The same, plus 157 ungraded sources as extra distractors for search. About 30% more to build; when they reach a top 10 they get Jev grades as new pairs."
- Start empty, grow from real use — "No seed. Cases come only from promoted query records after stage 4. Nothing to build up front, but stage 5 starts with a tiny, ungraded library and no link back to tickets 08 and 11."
Answer: Ticket 08's pool, re-added once

### compare
Question: "4. How are an old and a new version compared, and who decides?"
- Paired runs, intervals, you decide (Recommended) — "A version is a git ref plus setting overrides (role models, rethink on/off, rubric version, Jev on/off). Both run the same cases; the summary lane runs 3 times per version because model output varies. The report shows each measure's difference with a 95% paired-bootstrap interval, marked better, level or worse, plus cost and time. Nothing is decided in code. Your ticket-15 rule is the default tie-break: level quality, cheaper wins. So `atlas-rethink` stays only if it is better on the summary lane across runs; level means it is removed."
- One run per version — "Cheaper and faster, but a lucky run can look like a gain. The rethink decision is the most exposed to this."
- Fixed pass thresholds decide — "Code marks the new version pass or fail against set thresholds. Quicker to read, but thresholds must be chosen before there is any data, and code would decide instead of you."
Answer: Paired runs, intervals, you decide

Coverage shown before round 2, in answer to the lanes note:

| Setting to tune | Where it is judged |
|---|---|
| Rubric, kind cues, `atlas-rethink`, repair turn, escalation, `atlas_summarize` model | Summary lane |
| Jev's claim-support flags (are they right?) | Summary lane: your spot check of flagged and unflagged claims |
| Ignoring instructions inside a page | Summary lane: 3 pages with planted instructions |
| Updating a changed page (only the affected claims are revised) | Summary lane: real changed pages, added as you promote them |
| Abstract, reranker (Jev → Opus → BM25), `atlas_query` rewrite | Search lane |
| `find --wide` (gathering sources for a new topic) | Search lane: recall of the source sets you name for broad briefs |
| Labels, backing counts, Model view, gaps, the TL;DR in source answers | Answers lane |
| Topic "what's new" filter | Answers lane, from stage 7, when topics exist |
| Cost and time | Every lane |
| Changes in how Jev grades over time | Every lane: your agreement with Jev's grades is stored with each run |

Not judged here:

| Setting | Why not |
|---|---|
| Link cleaning, joining pages with ≥90% the same text, Jev's possible-copy flags, the changed-page check | Each is right or wrong, so tests cover it (ticket 12's tested per-site table), plus smoke runs |
| Page reading (the omp adapter, X posts read through Grok) | Smoke runs cover it. The check replays stored page text, so a reader change never reaches it |
| Research plans and topic revisions | Reconcile reviews each one before it is saved |
| Proposals to add or change trust notes | Too rare to measure; your confirm is the check |

## Round 2

### summary
Question: "1. How is the summary lane scored?"
- Key points, Jev checks, your spot check (Recommended) — "30 fixed pages from the library, chosen by kind (repo or docs, X post, paper, article, transcript) and weighted towards code. Each page gets a key-point list once: Opus drafts it from the page, you review it, and it never changes after that (FineSurE's method). Per run: completeness = share of key points the record states (Jev, one question per key point); faithfulness = share of claims with no Jev flag left after `add`, plus code-check results; conciseness = share of claims that state a key point (Jev). Also counted: rethink corrections, repair turns, dropped claims, escalations, \"summary failed\", cost and time. Your spot check: 20 claims per run, half flagged and half not, shown without their flags, which also measures how often Jev's flags are right."
- Blind pairwise preference — "Per page, Opus sees both versions' records unlabelled and picks the better one; you check a sample. Nothing to prepare, but it says which is better, not what is missing, and scores cannot be compared across runs."
- Pipeline counts only — "Code checks, Jev flags, drops, escalations, cost and time. Free and automatic, but nothing measures missed main points, which is what rethink lens 4 targets."
Answer: Key points, Jev checks, your spot check

### search
Question: "2. How is the search lane scored?"
- Ticket 11's method plus wide gather (Recommended) — "All 47 queries. nDCG@10 on the graded pool; new top-10 pairs graded by Jev, 10 of them shown to you. Because Jev is also the default reranker, two checks do not use Jev as grader: each single-target query's source rank (in top 10, MRR), and recall of source sets you named for broad briefs (R1's six trading sources to start; you can add sets). `find --wide` gets the same recall check. Each query keeps fixed phrasings (ticket 08's rewrites), so ranker changes are compared on the same input; a separate mode runs without phrasings to test `atlas_query`. Time and cost per query."
- nDCG only — "Simpler, but a Jev reranker is then graded only by Jev, the bias ticket 11 found."
Answer: Ticket 11's method plus wide gather

### answers
Question: "3. How is the answers lane scored, including whether labels and backing counts help?"
- Code and Jev checks, your blind label review (Recommended) — "16 cases: the 13 real and broad queries as questions, plus 3 'about a source' asks; topic what's-new cases join from stage 7. In code: label format, and backing counts recounted from the cited sources' authors and publishers (ticket 09's rule). Jev: does each cited source's stored claim support the answer's claim (flags only). You: label 30 shown claims per run yourself before seeing the model's label, so agreement with you, and how often Doubtful and Noise are right, is measured. For a new answer version you also see both answers side by side, unlabelled, and pick one or call them level; that covers Model view, gaps and readability. Keeping, tuning or dropping labels and counts is your call on the report, under the same tie rule."
- Your side-by-side pick only — "No label review; you compare answers with and without labels and counts. Tells whether they feel useful, not whether they are right."
- Jev grades the labels — "Jev labels each claim Sound, Doubtful or Noise and agreement with the answer model is reported. None of your time, but it measures model-against-model agreement, and Jev would be making a judgment the decision-model rule allows only as a signal."
Answer: Code and Jev checks, your blind label review

### coverage
Question: "4. Is the coverage in the two tables above complete?"
- As drafted (Recommended) — "Three lanes as mapped. Identity rules and reading are covered by tests and smoke runs; plans and revisions by Reconcile."
- Also add a reading lane — "Re-reads the case links when the reader adapter changes and reports unreadable pages, size changes and X-thread differences. Pages change on their own, so differences are hard to blame on the reader."
- Also measure Jev's copy flags — "A fixed set of known copies and non-copies; reports how often Jev's possible-copy flag is right. Needs copy pairs, which the library has few of today."
Answer: As drafted

### gate
Question: "5. How much of your time does a run take, and when is a result trusted?"
- Small fixed samples; results wait for them (Recommended) — "Per run: search 10 new grades, summaries 20 claims, answers 30 labels plus side-by-sides, about 10 minutes per lane [estimate]. Once: reviewing the 30 pages' key points. A report stays marked 'not spot-checked' until you finish. If you disagree with more than 2 in 10 of Jev's answers, that lane's Jev measures are marked unreliable for the run."
- Spot check only when a default would change — "Runs that would not change a default skip your check. Less of your time, but drift in Jev's grading goes unnoticed between decisions."
Answer: Small fixed samples; results wait for them

## Final confirmation

Question: the full proposed answer, shown in the same message (the full text is the ticket's "Proposed answer" section), then: "Confirm the proposed answer above for Decide quality check? Per the map's review plan, a Reconcile run on this summary comes next, before the ticket closes." Options: "Confirm" — "The summary stands as written. Next: run Reconcile on it, then close the ticket."; "Change something" — "Name what to change; the changed summary is shown again before Reconcile."
Answer: Confirm

## After the confirmation

The human's words that started the Reconcile run, given exactly:

```text
approve reconcile. no yield reconcile.
```

The run (`reconcile-20261109T040838Z-29bc37`, [record](13-reconcile-record.md)) ended with a final proposal. Its front was shown verbatim, and per "no yield" the reviewed answer was written into the ticket without a further question.
