# Ticket 15 interview: questions as shown and the human's answers

Ticket: ~/dev/atlas/.scratch/atlas-v2/issues/15-prototype-summary-model-quality-vs-cost.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label is the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Facts and proposal shown before round 1 (2026-11-09, g10):

- Ticket claimed; unblocked because Decide source summarization method is resolved.
- Proposed run in `.scratch/atlas-v2/prototypes/15-summary-model/`: ticket 16's method as throwaway Python. Each page is read once with `omp read` and cached, so every model sees the same text. Draft through `omp auth-gateway stdio` with the forced record tool, code checks, one `atlas-rethink` turn, Jev claim-support flags (through omp eval's judge, as ticket 11 did, because `~/.config/atlas/openrouter.env` does not exist yet), one repair turn, drops. Hard failures get one Opus `:medium` escalation, and its cost counts against the failing model.
- Sources picked from the frozen v1 manifest (read only) and read live. The manifest is 56% GitHub and 28% X, so the default 16 was 7 repos, 4 X posts, 3 docs or blog pages, 1 paper and 1 trading source.
- Measured per summary: code-check outcome, claims dropped, Jev flags, rethink line, escalation, tokens including thinking, cost and wall time.
- Watch item: forced tool use removes explicit thinking, so Sonnet `:medium` and `:high` may behave the same; the run shows whether their thinking tokens differ.
- Cost about $10–20 estimated; stops at $30.
- The user's rule decides; models only rank or flag. Results table plus summary pairs to spot-check.
- Disposal: the folder is deleted when this ticket closes; the result table goes into the ticket answer.

## Round 1

### quality
Question: "How is summary quality judged?"
- Checks + Jev + blind Grok ranking + your spot check (Recommended) — "Faithfulness comes from ticket 16's own checks: quotes found, dropped claims, Jev flags, escalations. Coverage comes from Grok 4.7, which sees the page and the summaries with model names hidden and in shuffled order, and ranks them per source. Grok is not an Anthropic model, so it shouldn't favor Opus. You spot-check pairs; your call decides."
- Checks + Jev + blind Opus ranking + your spot check — "Same, but Opus ranks. It reads long pages well, but it may favor its own summaries even with names hidden."
- Checks + Jev + your spot check only — "Cheapest. Measures only whether claims are supported, not whether a summary misses the page's main points."
- Your spot checks only — "You read summaries side by side. Slowest for you, and checks only what you read."
Answer: Checks + Jev + blind Grok ranking + your spot check, with this note, given exactly:

```text
for sources to test-run the summarization, make sure to take longer content sources, and varying topics. varying within the coding realm, and topic not related to coding at all as well, i.e. robots/tax/health/etc. The latter should account for only ~20% while coding-realm is 80%. Note as well, grok4.7 could hallucinate, so make sure that points that grok raised are actually valid and high-value.
```

### haiku
Question: "Add Haiku 5.5 to the comparison (Anthropic's cost guide suggests trying it first for output that can be checked)?"
- Add Haiku 5.5 (Recommended) — "Four models. Haiku costs about 1/20 of Sonnet per token, so it adds almost nothing to the run's cost; ticket 16's checks will show whether it holds up."
- Keep the three — "Sonnet medium, Sonnet high, Opus medium, as in your original draft."
Answer: Add Haiku 5.5, with this note, given exactly:

```text
sure, and let's try on high and xhigh.
```

### sample
Question: "How many sources?"
- 16 (Recommended) — "7 repos, 4 X posts, 3 docs/blog, 1 paper, 1 trading. Enough to see failures by page type; about $10–20."
- 8 — "Half the cost and time; one or two of each type, so weaker evidence."
- 30 — "Steadier numbers; about twice the cost and a longer spot check."
Answer: 16, with this note, given exactly:

```text
see earlier comments as well.
```

### run
Question: "Run the prototype as proposed?"
- Approve (Recommended) — "Build and run in the throwaway folder, stop at $30, then bring results and spot-check pairs."
- Change first — "Tell me what to change."
Answer: Approve

## Pause and resume

The user paused the run mid-judging ("minimal pause for now."). On resume the user wrote, exactly: "i started the other ticket as i started this session, and it seems that ticket is related to this session. That session has complete. Check to see if any finalized decisions changes anything we're doing for this session. otherwise, continue." Main found that [Decide quality check](../issues/13-decide-quality-check.md) changed nothing already settled here. It adopted that ticket's conciseness measure, its spot-check form (20 claims, half Jev-flagged, shown without flags) and paired 95% intervals, but not its 3 runs per version (about $37 more, past the $30 cap). It also chose the move to `tool_choice: auto` without asking, after a probe showed forced tool use removes thinking.

## Round 2

Shown before round 2: the table below, the caveats (one run per setup; Jev both steered repairs and judged support), and the spot-check file `spotcheck.md` (20 claims from Opus, Sonnet high and Haiku xhigh, half Jev-flagged, without labels).

| Setup | Key points covered | Claims supported (Jev) | $/summary | Grok rank |
|---|---:|---:|---:|---:|
| Opus medium (current) | 90.7% | 89.9% | 0.559 | 2.6 |
| **Sonnet high** | 90.1% (level) | 88.3% (level) | 0.202 | 1.6 |
| Sonnet medium | 86.0% | 83.5% (worse) | 0.164 | 4.4 |
| Haiku xhigh | 81.8% (−9, borderline) | 93.5% | 0.069 | 3.7 |
| Haiku high | 77.7% (worse) | 93.0% | 0.016 | 4.5 |
| Haiku / Sonnet, forced tool | 71.5% / 83.3% | 82.4% / 83.6% | 0.008 / 0.122 | 6.8 / 4.4 |

### spotcheck
Question: "Spot check: read spotcheck.md and reply with one line like `1 S, 2 N, …` (S = supported as written, N = not). Use 'Other' to type it."
- Skip the spot check — "Decide without it. The ticket records the result as not spot-checked, and Jev's flag accuracy stays unmeasured."
Answer, given exactly:

```text
S for all. Does the current design only support a single claim? What if there are multiple claims, especially in longer content sources? Would this just make the claim section longer to cover all the claims? Should we extend this into a list instead? Same thing as "Quote".
```

### model
Question: "Your rule: if quality is about the same, the cheaper model wins. Which model should `atlas_summarize` start at?"
- Sonnet 5.5 high (Recommended) — "Level with Opus on key points covered and claims supported (both intervals include 0), and Grok's top pick. 64% cheaper ($0.20 vs $0.56 per summary) and faster. `atlas_escalate` stays Opus medium."
- Haiku 5.5 xhigh — "88% cheaper than Opus ($0.07). Most claims supported, but it covers about 9 points fewer key points out of 100 (interval −18.7 to +0.6) and is the slowest; it hit the output cap once."
- Keep Opus 5.5 medium — "No change. Highest key-point coverage by a small margin, at almost 3x Sonnet high's cost."
Answer: Sonnet 5.5 high

### tool
Question: "Forced tool use turns thinking off, and quality drops without it. How should the record tool be called?"
- Pass to the spec as evidence (Recommended) — "This ticket records that `tool_choice: auto` with \"answer only by calling `record`\" keeps thinking and that every draft called the tool. The spec route settles its passed-on item on thinking under the forced tool. Ticket 16 stays unchanged."
- Change ticket 16 now — "Ticket 16 section 2 item 3 becomes \"auto tool choice; code checks the tool was called; a missing call is a hard failure\". This adds a 'Changes to earlier decisions' entry here."
Answer: Pass to the spec as evidence

## Round 3

Shown before round 3: "Your spot check: all 20 supported, including the 10 claims Jev had flagged. So in this sample Jev's flags were wrong 10 times out of 10, and your question points at the reason." Then: a record already holds a list of claims (Sonnet high wrote 12–67 per summary, median 23; the FTS5 docs got 67), each with exactly one quote of up to 25 words. In 7 of the 10 flagged claims the claim says more than its one quote covers: the quote is only a lead-in, or the claim joins 2–3 facts and the quote covers one. Code can check only that one quote, and Jev reads it literally.

### quotes
Question: "Should a claim carry a list of quotes instead of one?"
- List of 1–3 quotes per claim (Recommended) — "Each quote is at most 25 words and is found on the page in code. Jev reads the passages around all of a claim's quotes. A lead-in or a claim joining several facts can then cite each part, so every part is checked. Claims stay one self-contained sentence. Changes ticket 16 section 2 item 1 and section 3 item 1; the map's final Reconcile run reviews the change."
- Keep one quote, split compound claims — "The rubric adds \"one fact per claim; a quote must contain the fact, not lead into it\". Smaller change to ticket 16, but records get longer and a fact spread over a list or table still can't be quoted."
- Pass to the spec as evidence — "Ticket 16 stays as it is. The spec route weighs this sample and decides the quote shape there."
Answer: List of 1–3 quotes per claim
