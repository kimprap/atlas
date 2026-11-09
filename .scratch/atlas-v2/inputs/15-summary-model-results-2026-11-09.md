# Ticket 15 prototype results: summary model quality vs cost (2026-11-09, g10)

Method: ticket 16's `add` pipeline (draft → code checks → `atlas-rethink` → checks + Jev claim support → one repair turn → drops → one Opus `:medium` escalation on hard failure) in `harness.py`, through `omp auth-gateway stdio` (omp 18.18.2). 16 pages read once with `omp read` (`sources.json`, `pages/`): 13 about code (2 repos, 3 blogs, 4 docs/spec pages, 1 security guide, 1 paper, 2 X posts) and 3 not (Figure Helix robot, IRS Pub 4681 canceled debts, LPI choline), 2.9K–43K tokens each. One run per page per setup. Jev: `jev-1.14-20261014` through omp eval `judge_batch`. Grok 4.7 (`xai-oauth`) judged blind, with summaries labelled by shuffled letters.

Quality measures (following ticket 13's summary lane where possible):

- Completeness: share of the page's key points the summary states (Jev, one yes/no per key point). Key points: Grok drafted 159; code checked each quote on the page, Jev checked support, and Main reviewed all for validity and value: 6 dropped as low value, 153 kept. Ticket 13 has Opus draft key points and the user review them; here the interview chose Grok.
- Faithfulness: share of final claims Jev judges supported (≥0.8) against the passage around the claim's quote, re-judged after the run with a fixed passage cutter.
- Conciseness: share of claims that state a key point (Jev). Detailed summaries score lower by construction.
- Grok blind rank (1 = best of 7), as a secondary signal.
- Paired 95% bootstrap intervals over the 16 pages, versus Opus `:medium`.

| Setup | Completeness | Δ vs Opus [95%] | Faithful | Δ vs Opus [95%] | Concise | Grok rank | Claims | $/summary | Model s (median) |
|---|---:|---|---:|---|---:|---:|---:|---:|---:|
| Haiku 5.5 high | 77.7% | −13.0 [−20.4, −5.2] | 93.0% | +3.2 [−2.0, +9.3] | 52% | 4.5 | 22.6 | 0.016 | 70 |
| Haiku 5.5 xhigh | 81.8% | −8.9 [−18.7, +0.6] | 93.5% | +3.6 [−1.5, +9.3] | 49% | 3.7 | 25.1 | 0.069 | 162 |
| Haiku 5.5, forced tool (no thinking) | 71.5% | −19.3 [−27.2, −11.0] | 82.4% | −7.5 [−16.7, +1.2] | 69% | 6.8 | 10.7 | 0.008 | 21 |
| Sonnet 5.5 medium | 86.0% | −4.8 [−13.8, +3.6] | 83.5% | −6.4 [−11.5, −1.8] | 55% | 4.4 | 15.6 | 0.164 | 47 |
| Sonnet 5.5 high | 90.1% | −0.7 [−5.8, +4.0] | 88.3% | −1.6 [−7.2, +4.1] | 48% | 1.6 | 25.1 | 0.202 | 75 |
| Sonnet 5.5, forced tool (no thinking) | 83.3% | −7.4 [−17.6, +1.3] | 83.6% | −6.3 [−11.3, −1.4] | 59% | 4.4 | 14.1 | 0.122 | 49 |
| Opus 5.5 medium (current default) | 90.7% | — | 89.9% | — | 45% | 2.6 | 22.2 | 0.559 | 98 |

Cost includes any escalation. Model seconds are the sum of a summary's model calls; wall time under the run's queue is not meaningful.

Pipeline counts:

| Setup | Hard failures → escalated | Runs with draft check failures | Draft quotes not on page | Claims dropped |
|---|---:|---:|---:|---:|
| Haiku high | 0 | 10 | 2 | 0 |
| Haiku xhigh | 1 (cut off on the FTS5 docs) | 12 | 4 | 0 |
| Haiku forced | 0 | 13 | 7 | 1 |
| Sonnet medium | 1 (cut off on PEP 703) | 12 | 5 | 1 |
| Sonnet high | 0 | 13 | 8 | 0 |
| Sonnet forced | 0 | 13 | 3 | 1 |
| Opus medium | 0 | 15 | 16 | 0 |

Grok's error reports: 149 in total. Code found every item and page quote. Jev agreed the statement was not supported as written for 36 of the 121 factual reports. Main's review of those 36: 8 invalid (fair readings), 3 unclear, 25 valid but mostly minor (lost hedges such as "may no longer" → "can no longer", dropped conditions, added evaluative words). Each setup has 1–2 valid errors worth noting. The most serious: Haiku forced called Crush "open-source" (the page lists the FSL-1.1-MIT license).

Findings:

- Forced tool use removes thinking: Haiku `high` and `xhigh` gave identical output in a probe. Without thinking, both Haiku and Sonnet lose quality (Haiku −19 completeness; Sonnet −6 faithfulness, significant). With `tool_choice: auto` plus "answer only by calling `record`", every draft called the tool.
- Sonnet `high` is level with Opus `:medium` on completeness and faithfulness (both intervals include 0), ranked first by Grok, at 36% of the cost and faster.
- Haiku `xhigh` is the most faithful but misses more key points (−8.9, interval just touching 0), at 12% of Opus's cost but slowest.
- Non-coding pages (3) show the same order.

Caveats:

- One run per setup per page; ticket 13's lane runs 3 because output varies.
- A passage-cutter bug during the run gave Jev passages without the claim's quote for 104 of 2,166 final claims (3–6% per setup, even). Some repair turns were set off by false flags. All measures above were re-judged with the fixed cutter; the summaries were not rerun (the cap would be exceeded).
- Jev both steered the repairs and judges faithfulness, so faithfulness is not independent; the user's spot check is the gate.
- Grok drafted the key points; they were checked by code, Jev and Main, but not yet by the user.
- Prices: Anthropic catalog rates from ticket 16's input; Opus rates are [INFERENCE] from other catalogs.

Spend: $18.65 for summaries, about $0.14 for Jev judging; Grok via `xai-oauth` (token counts in `judging/*__grok.json`).

Spot check (user, 2026-11-09): 20 claims from Opus medium (7), Sonnet high (7) and Haiku xhigh (6), half Jev-flagged, shown blind with the page passage. The user judged all 20 supported, so 0 of 10 Jev flags marked an unsupported claim. In 7 of the 10 flagged claims, the claim said more than its one quote covered.
