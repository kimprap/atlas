Type: prototype
Parent: [Atlas v2](../map.md)
Blocked by: 16
Status: resolved

## Question

Which model should `atlas_summarize` start at? Sonnet 5.5 at medium, Sonnet 5.5 at high and Opus 5.5 at medium each summarize the same external sources from several topics, weighted towards code-related ones. Measure quality, cost and time per summary. The user's rule: "If quality is relatively similar across all summaries for models that cost less, then let's go with the more cost efficient model." (quoted from the user's note in [the ticket 07 interview](../reviews/07-interview.md), round 1, stages).

To settle when this ticket is grilled: how quality is judged (a blind side-by-side review by a model, the user's own spot checks, or both). Under `rule://decision-model`, a model may rank or flag but never decides; the user's rule above decides.

Changed on 2026-11-08, at the user's request ("I'd like to refine it first before the above inquiry is executed"): this ticket waits on [Decide source summarization method](16-decide-source-summarization-method.md). The models are compared under that method, and its rubric and checks may serve as the quality measure. If that method makes cheaper models viable, the user decides here whether to add them to the comparison.

Input from [Decide source summarization method](16-decide-source-summarization-method.md) (section "Passed on"), resolved 2026-11-09: the models are compared under that method, with its code checks part of the quality measure. Anthropic's cost guide recommends trying Haiku 5.5 first for output that can be checked; whether to add it to the comparison is the user's call here. Until this ticket picks a cheaper `atlas_summarize`, an escalation to the new `atlas_escalate` role reruns the same model.

Input from [Decide quality check](13-decide-quality-check.md) (section "Passed on"), resolved 2026-11-09: this ticket may use the quality check's summary-lane measures as its quality measure (key-point completeness, faithfulness and conciseness judged by Jev, pipeline counts, cost and time, and the user's blind spot check of 20 claims), run once by hand before the tool exists. Its own grilling decides. If it picks a cheaper model first, the quality check's one-time library build costs less.

It changes only the `atlas_summarize` default, which [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md) starts at `anthropic/claude-opus-5-5:medium`. The spec does not wait on it, but it must resolve before real sources go in at build stage 4. If it is still open when the map's other tickets close, the map closes it as passed on and the spec route carries it as that gate ([Decide Atlas build order](07-decide-atlas-build-order.md)).

## Answer

`atlas_summarize` starts at `anthropic/claude-sonnet-5-5:high`. On 16 pages it was level with Opus 5.5 `:medium` on key points covered and claims supported, at 36% of the cost. `atlas_escalate` stays Opus `:medium`. A claim now carries a list of 1–3 quotes instead of one.

Records:

- Interview, with every question as shown and the human's exact answers: [15-interview.md](../reviews/15-interview.md)
- Method, full tables and caveats: [summary model results](../inputs/15-summary-model-results-2026-11-09.md)

The human's deciding words, quoted exactly. To the spot check, as typed:

```text
S for all. Does the current design only support a single claim? What if there are multiple claims, especially in longer content sources? Would this just make the claim section longer to cover all the claims? Should we extend this into a list instead? Same thing as "Quote".
```

Then the chosen options: "Sonnet 5.5 high" (model), "Pass to the spec as evidence" (how the record tool is called), and "List of 1–3 quotes per claim" (quotes).

Prototype run on 2026-11-09 on g10 under the approved round 1 ("Approve"), paused once at the user's request and resumed. It decides only the `atlas_summarize` default; the quote change was the user's decision in round 3. Prototype and research tickets are not reviewed on their own (map Notes); the map's final Reconcile run, with every ticket open for change, covers the quote change.

### 1. What ran

- Ticket 16's `add` pipeline in throwaway Python through `omp auth-gateway stdio`: draft, code checks, `atlas-rethink`, Jev claim support, one repair turn, drops, and one Opus `:medium` escalation on a hard failure.
- 16 pages, each read once with `omp read`: 13 about code (repos, blogs, docs, PEP 703, an OWASP guide, the ReAct paper, two X posts) and 3 not (Figure's Helix robot, IRS Publication 4681, LPI choline), 2.9K–43K tokens each.
- 7 setups, one run per page each: Haiku 5.5 `high` and `xhigh`, Sonnet 5.5 `medium` and `high`, Opus 5.5 `medium`, plus Haiku and Sonnet with the forced tool, which turns thinking off. The thinking setups used `tool_choice: auto` and the line "answer only by calling `record`" (Main, after a probe).
- Quality was measured following ticket 13's summary lane where possible:
  - completeness: share of the page's key points stated, judged by Jev;
  - faithfulness: share of claims Jev judges supported;
  - conciseness;
  - pipeline counts;
  - Grok 4.7's blind ranking;
  - the user's blind spot check of 20 claims.
- Key points: Grok drafted 159. Code checked each quote, Jev checked support, and Main reviewed every point for validity and value; 153 were kept. Grok's 149 error reports went through the same checks: 36 confirmed by Jev, 25 of them valid after Main's review, mostly minor.
- Spend: $18.65 for summaries and about $0.14 for Jev; Grok ran on the `xai-oauth` login.

### 2. Results

| Setup | Key points covered | Δ vs Opus [95%] | Claims supported | Δ vs Opus [95%] | Grok rank | $/summary | Model s |
|---|---:|---|---:|---|---:|---:|---:|
| Haiku high | 77.7% | −13.0 [−20.4, −5.2] | 93.0% | +3.2 [−2.0, +9.3] | 4.5 | 0.016 | 70 |
| Haiku xhigh | 81.8% | −8.9 [−18.7, +0.6] | 93.5% | +3.6 [−1.5, +9.3] | 3.7 | 0.069 | 162 |
| Haiku, forced tool | 71.5% | −19.3 [−27.2, −11.0] | 82.4% | −7.5 [−16.7, +1.2] | 6.8 | 0.008 | 21 |
| Sonnet medium | 86.0% | −4.8 [−13.8, +3.6] | 83.5% | −6.4 [−11.5, −1.8] | 4.4 | 0.164 | 47 |
| **Sonnet high** | 90.1% | −0.7 [−5.8, +4.0] | 88.3% | −1.6 [−7.2, +4.1] | 1.6 | 0.202 | 75 |
| Sonnet, forced tool | 83.3% | −7.4 [−17.6, +1.3] | 83.6% | −6.3 [−11.3, −1.4] | 4.4 | 0.122 | 49 |
| Opus medium | 90.7% | — | 89.9% | — | 2.6 | 0.559 | 98 |

- Sonnet `high` is level with Opus on both measures and Grok's top pick; under the user's rule the cheaper model wins.
- Without thinking, quality drops for both Haiku and Sonnet.
- Two runs hit the 32K output cap and escalated: Haiku `xhigh` on the FTS5 docs and Sonnet `medium` on PEP 703.
- Spot check: the user judged all 20 claims supported, including all 10 that Jev had flagged. In 7 of those 10, the claim said more than its one quote covered (a lead-in quote, or one quote for a claim joining 2–3 facts).

Caveats: one run per setup per page (ticket 13's lane runs 3); Jev both steered the repairs and judged support; Grok's key points were checked by code, Jev and Main but not by the user. A passage-cutter bug gave Jev the wrong passage for 104 of 2,166 claims during the run (3–6% per setup); every measure was re-judged with the fix, but the summaries were not rerun.

### 3. Quotes per claim

1. Each claim, recommendation and caveat carries a list of 1–3 quotes, each at most 25 words and copied word for word. A claim stays one self-contained sentence.
2. Code finds every quote on the stored page after normalization and stores each position.
3. After the repair turn, a claim is dropped if any of its quotes is still not on the page, because the part it cites is unchecked (Main).
4. Jev's one request per claim holds the claim and the passages around all of its quotes.
5. On a changed page, a claim is affected when any of its quotes is gone or sits in a changed region.

### Changes to earlier decisions

- [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md), section 5 item 1, and the map's standing decision on Atlas models: `atlas_summarize` starts at `anthropic/claude-sonnet-5-5:high`. The other roles keep their defaults, and `atlas_escalate` stays `anthropic/claude-opus-5-5:medium`, so an escalation now runs a stronger model.
- [Decide source summarization method](16-decide-source-summarization-method.md): section 2 item 1 (rubric: claims, recommendations and caveats), section 3 item 1 (locator), section 4 step 6 (drops), section 6 item 2 (Jev request) and section 7 item 1 (affected claims) follow section 3 above. Section 4 item 7's "until ticket 15 picks a cheaper one" is settled.
- [Define Atlas v2 requirements](02-define-atlas-v2-requirements.md), stored record, as changed by ticket 16: each claim holds its quotes and their positions instead of one quote and one position.

### Passed on

- To the spec route:
  - Thinking under the forced tool (ticket 16's passed-on item): forced tool use removes thinking, and quality drops without it. `tool_choice: auto` with "answer only by calling `record`" kept thinking, and every draft called the tool. The spec settles how the tool is called.
  - The summary role's output cap: 32K tokens cut off 2 of 112 runs; Sonnet `high` had none.
  - Jev's claim-support threshold and near-threshold reruns: 0 of 10 flagged claims in the spot check were unsupported. Measure again once claims carry quote lists.
  - Claim-count bounds: the prototype used at most max(15, 10 + page tokens / 700); Sonnet `high` wrote 12–67 claims (median 23).
  - The 150K-token length setting must fit the role model's context; Haiku 5.5's context is 100K.
- To the quality check's first run ([Decide quality check](13-decide-quality-check.md)): its one-time library build uses Sonnet `high`, so it costs less than the Opus estimate.

The prototype folder was deleted on 2026-11-09 when this ticket closed; method and tables are in the results file above.
