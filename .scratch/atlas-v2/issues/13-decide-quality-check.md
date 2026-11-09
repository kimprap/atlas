Type: grilling
Parent: [Atlas v2](../map.md)
Blocked by: 16
Status: resolved

## Question

What form does Atlas's quality check take? It is run by hand, read-only, compares an old and a new version, and has no scheduling ([Atlas v1 notes](../inputs/atlas-v1-notes.md), note 1). The [map's standing decision on the Jev decision model](../map.md) (2026-10-29) makes pooled Jev grading plus the user's spot check the method, as tested in [Prototype retrieval on real summaries](08-prototype-retrieval-on-real-summaries.md) and [Prototype Jev reranking on real summaries](11-prototype-jev-reranking-on-real-summaries.md). Decide what it judges (summaries, search results, answers), the query set and graded pool it starts from, how it reuses the summary rubric and add-time claim checks from [Decide source summarization method](16-decide-source-summarization-method.md), and how it tells whether the Sound, Doubtful and Noise labels and backing counts from [Decide source credibility weighting](09-decide-source-credibility-weighting.md) help.

Changed on 2026-11-08: how Jev's claim-support flags work (left here by [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md), section 5) moved to [Decide source summarization method](16-decide-source-summarization-method.md), which checks claims when a source is added; this ticket waits on it.

Input from [Decide source summarization method](16-decide-source-summarization-method.md) (section "Passed on"), resolved 2026-11-09: this check reuses that ticket's rubric, its code checks, Jev's claim-support flags and the `atlas-rethink` report lines, all stored per source. It also owns the user's request for an explicit testing framework, made during live runs, to tune all of those decisions. That includes whether `atlas-rethink` stays: it is kept, tuned or removed depending on whether summaries improve consistently across runs.

Its form is decided before the spec; it is built in stage 5, right after the first usable Atlas, so later tuning is measured ([Decide Atlas build order](07-decide-atlas-build-order.md)). [Prototype summary model quality vs cost](15-prototype-summary-model-quality-vs-cost.md) judges summary quality in its own narrow way and may serve as evidence here.

## Answer

The quality check is a repo-only developer tool, run by hand, that compares two versions of Atlas on a frozen test library in its own `eval` profile. It has three lanes (summaries, search, answers), each run on its own. Jev does the pooled grading, code does the counting, and the user's small blind spot checks are the gate. Every measure is reported as a difference with a 95% interval; the user decides, and level quality means the cheaper version wins.

Records:

- Interview, with every question as shown and the human's exact answers: [13-interview.md](../reviews/13-interview.md)
- Reconcile run on the summary (`reconcile-20261109T040838Z-29bc37`, 5 turns, $2.10): [13-reconcile-record.md](../reviews/13-reconcile-record.md)

The human's deciding words, quoted exactly: "Confirm" to the summary after the interview, then, to start the review:

```text
approve reconcile. no yield reconcile.
```

Settled by grilling over two rounds on 2026-11-09 and reviewed by one Reconcile run on 2026-11-09. The reviewers kept the human's choices. They let a version that changes the abstract rerun search on rewritten library records, judged faithfulness alike when a version skips Jev's check, moved wide-gather recall to stage 7 when `find --wide` exists, added missing members of named source sets to the library, named the library build and promotion as the only reads outside `eval`, and passed four open test and spot-check rules to the spec. The human asked for no stop after the run, so these changes were not confirmed separately. Items marked "(Main)" were not asked.

### 1. Form and place

1. A script in `kimprap/atlas`, not shipped in the plugin and not reached through `atlas-ask`. It runs by hand from an omp session in `~/dev/atlas`, with no scheduling.
2. It calls Atlas core through its ports. A replay read adapter serves stored page text, so pages are never re-read and both versions see identical text.
3. Apart from the one-time library build (section 2) and promotion (item 4), it reads and writes only the `eval` profile store. Case data (queries, grades, key points, named source sets) and run results are rows there, which host-backup already copies; the repo holds code only (Main).
4. Promoting a real query reads one query record and its sources' stored page text from a named real profile and copies them into `eval`. Nothing is written to the real profile (Main; this reconciles "never touches a real profile" with "promote a real query").

### 2. Test library

1. Built once in stage 5 by adding the 516 links in ticket 08's graded pool to `eval`; links that no longer read are dropped and counted. The 47 queries and 1,535 grades are imported from git history (`570617c^`) and mapped by link through the frozen v1 vault's `canonical_url`, read only.
2. Library records are written once with the `atlas_summarize` default of the day and stay fixed for the search and answers lanes; the summary lane writes its own records on each run (Main). Because BM25 and the reranker read the abstract, a version that changes the abstract can also run the search lane on library records rewritten under each version from stored text, at about the build cost per version (Main).
3. About $25–40 once at Opus; less if [Prototype summary model quality vs cost](15-prototype-summary-model-quality-vs-cost.md) picks a cheaper model first.
4. New cases enter only when the user promotes them.

### 3. Comparing versions

1. A version is a git ref plus setting overrides: role models, `atlas-rethink` on or off, rubric version, Jev on or off.
2. Both versions run the same cases. The summary lane runs 3 times per version, because model output varies.
3. The report shows each measure's difference with a 95% paired-bootstrap interval, marked better, level or worse, plus cost and time per item. Nothing is decided in code.
4. The user's rule from ticket 15 is the default tie-break: level quality, cheaper wins. `atlas-rethink` stays only if it is better on the summary lane across runs; level means it is removed.

### 4. Summary lane

1. Cases:
   - 30 fixed pages chosen by kind (repo or docs, X post, paper, article, transcript), weighted towards code;
   - 3 pages with planted instructions, for the page-as-data rule;
   - real changed pages, as the user promotes them, for claim-level updates.
2. Each page has a key-point list written once: Opus drafts it from the page, the user reviews it, and it never changes after that.
3. Measures, following FineSurE ([ACL 2024](https://arxiv.org/abs/2407.00908)) with Jev as the judge:
   - completeness: share of key points the record states (one Jev question per key point);
   - faithfulness: share of claims with no Jev flag left after `add`, plus code-check results; when Jev did not check a version's records (Jev off, or "support not checked"), the quality check asks Jev the same support question after `add`, so both versions are judged alike (Main);
   - conciseness: share of claims that state a key point (Jev);
   - pipeline counts: rethink corrections, repair turns, dropped claims, escalations, "summary failed";
   - planted-instruction pages: whether the record follows a planted instruction (Main);
   - cost and time per summary.
4. Spot check: 20 claims per run, half flagged and half not, shown to the user without their flags. This also measures how often Jev's flags are right.

### 5. Search lane

1. All 47 queries, each with fixed phrasings (ticket 08's rewrites), so ranker changes are compared on the same input. A separate mode runs without phrasings to test `atlas_query`.
2. nDCG@10 on the graded pool; new top-10 pairs are graded by Jev and pooled.
3. Because Jev is also the default reranker, two checks do not use Jev as grader: each single-target query's source rank (in top 10, MRR), and recall of source sets the user names for broad briefs (R1's six trading sources to start; any set member missing from the 516 is added to the library once).
4. `find --wide` gets the same recall check once it exists (stage 7, [Decide Atlas build order](07-decide-atlas-build-order.md)); until then recall is measured on the top-10 search.
5. Time and cost per query. Spot check: 10 new Jev grades per run.

### 6. Answers lane

1. Cases: the 13 real and broad queries as questions, plus 3 "about a source" asks. Topic what's-new cases join from stage 7.
2. In code: the label format, and backing counts recounted from the cited sources' authors and publishers (ticket 09's rule).
3. Jev flags answer claims that the stored claims they cite do not support.
4. The user labels 30 shown claims per run before seeing the model's label. The report gives agreement with the user and how often Doubtful and Noise are right.
5. For a new answer version, the user sees both answers side by side, unlabelled, and picks one or calls them level. This covers the Model view, gaps and readability.
6. Whether labels and backing counts help is the user's call on the report, under the same tie rule.

### 7. Spot checks

1. About 10 minutes per lane per run [estimate]; once, reviewing the 30 pages' key points.
2. A report stays marked "not spot-checked" until the user finishes.
3. If the user disagrees with more than 2 in 10 of Jev's answers, that lane's Jev measures are marked unreliable for the run.
4. The user's agreement with Jev is stored with each run, so drift in Jev's grading shows.

### 8. Not judged here

- Link cleaning, the ≥90% same-text join, Jev's possible-copy flags and the changed-page check: tests (ticket 12's tested per-site table) and smoke runs.
- Page reading: smoke runs; replayed text never reaches the reader.
- Research plans and topic revisions: Reconcile, before each is saved.
- Trust note proposals: the user's confirm.

### Changes to earlier decisions

- [Decide source summarization method](16-decide-source-summarization-method.md), section 5 item 3: "kept, tuned or removed depending on whether summaries improve consistently across runs" gets its test: better on the summary lane across 3 runs; level means removed.
- [Decide Atlas build order](07-decide-atlas-build-order.md), stage 5: also builds the `eval` library once (Main).

### Rejected alternatives

- Summaries and search only: whether labels and backing counts help would rest on day-to-day use alone. One end-to-end score: a drop cannot be traced to its step.
- An 11th shipped `eval` command: adds shipped surface before anyone else uses Atlas. Ad-hoc eval sessions: results cannot be compared across runs.
- All 673 v1 links: about 30% more to build for extra distractors. Starting empty: a tiny, ungraded library and no link to tickets 08 and 11.
- One run per version: a lucky run looks like a gain. Fixed pass thresholds: chosen before any data, and code would decide.
- Blind pairwise preference for summaries: says which, not what is missing, and is not comparable across runs. Pipeline counts only: missed main points go unmeasured.
- nDCG only: a Jev reranker graded only by Jev.
- Side-by-side picks only for answers: says whether labels feel useful, not whether they are right. Jev grading the labels: model-against-model agreement, and a judgment the decision-model rule allows only as a signal.
- A reading lane, or measuring Jev's copy flags: reader differences are hard to separate from page changes, and the library has few copy pairs.
- Spot checks only when a default would change: Jev drift goes unnoticed between decisions.

### Passed on

- To [Prototype summary model quality vs cost](15-prototype-summary-model-quality-vs-cost.md): it may use the summary lane's measures as its quality measure, run once by hand before the tool exists. Its own grilling decides.
- To the spec route:
  - the tool's commands and arguments;
  - the case and run-row schema in the `eval` store;
  - the key-point prompt;
  - how the 30 pages and the spot-check samples are chosen;
  - the bootstrap settings;
  - how planted-instruction pages are made and checked, and what a promoted changed page copies (its old and new text, and its old record);
  - which summary-lane measures must be better for `atlas-rethink` to stay, and how mixed results read, fixed before the first run;
  - whether the summary lane's 20 spot-check claims are per run or per comparison of 3 runs;
  - which Jev measures each lane's spot check covers: completeness, conciseness and the answers lane's support flags have no user sample yet, so the user decides whether to add one or narrow item 7.3 to the sampled measures;
  - keeping the tool's folder out of the shipped files that ticket 14's tag check compares;
  - showing each run's estimated cost before it starts.
