# Research Evidence: Faithful single-document claim extraction with a cheaper LLM, and whether a second pass helps

## Authority and scope
- Requesting owner: wayfinder session on ticket 'Decide source summarization method' (Atlas v2). No governing revisions given. No durable capture.
- Question: what primary sources show (with numbers) about (1) quote grounding / Citations / cheaper-model guidance, (2) same-model second pass, (3) cheap claim-vs-passage checkers, (4) schema forcing. Stopped after those four. All sources accessed 2026-11-09.

## Sources and findings

### 1. Quote grounding, Citations, cost guidance (Anthropic docs)
- **Reduce hallucinations** (platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations): for long documents ("(>20k tokens)"), ask the model to "extract word-for-word quotes first before performing its task"; "Verify with citations": after drafting, find a supporting quote for each claim, and "If it can't find a quote, it must retract the claim." It also lists best-of-N comparison, iterative refinement, and limiting answers to the provided documents. **No numbers are given.** The doc says these "don't eliminate" hallucinations.
- **Citations** (…/build-with-claude/citations, status stable): plain text is split into sentences. Each citation is a `char_location` with `cited_text`, `start_char_index` (0-indexed), and `end_char_index` (exclusive) (example lines ~444–449, 1072–1077). Custom-content documents are not split further and cite by block index. The doc says citations "are guaranteed to contain valid pointers to the provided documents" because the API extracts `cited_text` itself. `cited_text` does not count toward output tokens, and input tokens rise slightly. Per Anthropic's own evals, it is "significantly more likely to cite the most relevant quotes" than prompting alone (no number given). Supported models include claude-haiku-5-5, sonnet-5-5, and opus-5-5 ("All active models"). **Citations cannot be combined with structured outputs (`output_config.format`): the API returns a 400.** The workaround is to ask for "field: value" lines and parse them in code. A JSON-only prompt "might contain few or no citations."
- **Optimizing for cost and intelligence** (…/about-claude/models/optimizing-for-cost-and-intelligence):
  - "High-volume work with outputs you can check → Try Claude Haiku 5.5 first"; Haiku "suits high-volume and latency-sensitive work with checkable outputs."
  - GPQA Diamond: Haiku 5.5 scored 85% vs 91% for Opus 5.5 and Sonnet 5.5, at about 1/20 of Opus's cost per correct answer.
  - If outputs are checkable, run at `low` effort and re-run failures at `high`. On SWE-bench Pro this was about 40% cheaper at the same pass rate (about 97% vs 95.3%). Conditions: "you need a failure signal… a checker that passes bad work lets those failures through."
  - An advisor model gave no gain when the executor rarely consulted it, and on Chartography scored 7 points lower.
  - All of these are Anthropic-internal results, described as "directional, not guarantees." None are on summarization.

### 2. Same-model second pass
- **Huang et al. 2023, arXiv:2310.01798 (ICLR 2024)**: intrinsic self-correction, with no external feedback, lowered reasoning accuracy.
  - GPT-3.5 on CommonSenseQA: 75.8 → 38.1 (round 1).
  - GPT-4 on GSM8K: 95.5 → 89.0; on HotpotQA: 49 → 43.
  - Llama-2-70B on GSM8K: 62.0 → 36.5.
  - Gains reported in earlier papers "result from using oracle labels… and vanish when oracle labels are not available." Scope: reasoning tasks, not document-grounded extraction.
- **Dhuliawala et al. 2023, Chain-of-Verification, arXiv:2309.11495**: the second pass helped when verification questions were answered *independently of the draft*. This was closed-book (no document) with Llama 65B.
  - Wikidata precision: 0.17 → 0.36. Hallucinated entities per answer: 2.95 → 0.68, but correct entities also fell (0.59 → 0.38).
  - FActScore on biographies: 55.9 baseline, 60.8 joint, 63.7 factored, 71.4 factor+revise. Facts per bio: 16.6 → 12.3.
  - Variants that could see the draft "tend to repeat the hallucinations."
  - Yes/no verification questions did worse than open questions; the model "tends to agree with facts in a yes/no question format whether they are right or wrong."
- **Madaan et al. 2023, Self-Refine, arXiv:2303.17651**: about 20% absolute gain on average, mostly on preference and style tasks.
  - Math: no gain (GPT-4 92.9 → 93.1), attributed to "inability to accurately identify whether there is any error."
  - Gains depend on specific feedback. Sentiment reversal: 43.2 with specific feedback, 31.2 with generic, 0 with none.
  - Huang et al. flag Self-Refine for "sub-optimal prompt design" in its first-pass prompts.
- **Kamoi et al. 2024 survey, arXiv:2406.01297**: "no prior work demonstrates successful self-correction with feedback from prompted LLMs, except for… tasks… exceptionally suited"; self-correction "works well in tasks that can use reliable external feedback."

### 3. Cheap external support checkers
- **MiniCheck, Tang, Laban, Durrett, arXiv:2404.10774 (EMNLP 2024)**: MiniCheck-FT5 (770M parameters) checks claim sentences against grounding documents.
  - Balanced accuracy on LLM-AggreFact: about 74.7 vs GPT-4 about 75.3. It matches Claude-3 Opus.
  - Cost on the 13K-item test set: $0.24 vs $107 for GPT-4 ("more than 400 times cheaper").
  - Splitting claims into atomic facts was "not needed": +0.3 for GPT-4 at extra cost ($212 vs $107), −1.4 for MiniCheck-FT5. Removing context-dependent wording from claims also did not help.
- **LLM-AggreFact leaderboard** (llm-aggrefact.github.io, read 2026-11-09; 11 datasets):
  - Top: nimble-v4-max 79.5.
  - **Jev 1.13.0: 78.7.**
  - Bespoke-MiniCheck-7B: 77.4. Claude-3.5 Sonnet: 77.2. gpt-4o: 75.9. MiniCheck-Flan-T5-L: 75.0.
  - Best-to-worst dataset spread is wide: ExpertQA about 59–61, REVEAL about 86–91.
- **FActScore, Min et al. 2023, arXiv:2305.14251**: splits text into atomic facts and scores the share supported by a knowledge source. Its automated estimator has "less than a 2% error rate" against human FActScore. Note: this is an aggregate error rate, not per-claim accuracy.

### 4. Structured outputs
- **Structured outputs** (…/build-with-claude/structured-outputs, stable): constrained decoding means output is "Always valid" and "No retries needed for schema violations."
- Exceptions where output may not match the schema: `stop_reason: "refusal"` and `"max_tokens"`.
- Haiku 5.5 is supported.
- The first request with a new schema compiles a grammar (cached 24h). Each optional field "roughly doubles" grammar state.
- **Cannot be combined with Citations** (400 error).
- No vendor numbers on how often format failures happen without constraints.

### Sources searched with no usable result
- No primary source found with a measured effect of quote-first prompting or the Citations feature on faithfulness (Anthropic gives no figure).
- No paper found testing a same-model second pass specifically on single-document extraction.

## Contradictions and gaps
- CoVe (positive) vs Huang and Kamoi (negative) differ in setup:
  - CoVe's benefit came from answering verification questions independently of the draft and from factored cross-checking, measured on closed-book facts with a base LLM.
  - Huang's failures are reasoning tasks where the model re-judges its own answer.
  - Neither covers checking extracted text against a document that is supplied.
- MiniCheck and LLM-AggreFact numbers are balanced accuracy around 75–80, so roughly 1 in 5 support judgments are wrong even for top checkers [INFERENCE from BAcc].
- Anthropic's cost-page figures come from coding and QA benchmarks, not summarization.

## Explicit inferences
- [INFERENCE] Citations' character ranges plus `cited_text` would let Atlas check locators in code against the stored text. But Citations rules out structured outputs in the same call, so the two approaches compete for one call.
- [INFERENCE] The "re-run failures" pattern needs a reliable failure signal. A code-level check that a quote appears on the page is such a signal. Jev's support flags are external but probabilistic (about 78.7 BAcc).

## Decision coverage
- **Supports:**
  - Grounding claims in verbatim spans that can be checked mechanically.
  - An independent checker (code or a separate model) is better supported than a same-model recheck that sees the draft.
  - Small or cheap checkers reach frontier-model accuracy on claim-vs-document support.
  - Schema forcing removes parse failures, except for refusals and truncation.
- **Does not decide:** the check-failure policy, update/diff method, X-reply selection, or whether Haiku is enough for Atlas pages. Those need a measurement on Atlas's own workload, as the cost doc's four-step method directs.

## Freshness and capture
- Stored evidence: not applicable. Durable capture: none.

## Next owner
- Wayfinder session for 'Decide source summarization method'.
