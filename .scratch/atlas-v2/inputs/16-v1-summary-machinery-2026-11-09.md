# Atlas v1 summary machinery: evidence for ticket 16 (scout report, 2026-11-09)

Read-only survey of v1's summary rubric, schemas, validators, plans and ~14 vault summaries. Agent output kept as evidence; not a decision.

**Caveat on method:** no shell, so no `git show v1:` or /tmp scripts. I read the working-tree copies of the named files (tag ref exists at .git/refs/tags/v1; not diffed). Because v1 vault stores no page text (the plan says envelopes were deleted: living-source-quality-revisit.md Context table 'Staging envelopes | Deleted'), the requested verbatim-locator fraction is **not measurable**; I characterized locators and used grep counts instead. No temp files were created.

### 1. What guided the model
- Four-stage method (evidence boundary → extraction with three separate sets → synthesis → 7-item checklist): quality-guide.md. Locator for every concrete claim attached 'while extracting' (guide §2). Paraphrase by default, quote only if wording matters.
- Checklist ids, order fixed: evidence-boundary, primary-contribution, source-support, limits-uncertainty, context-neutrality, assessment-coherence, proportionality; each `{id,status:pass|fail,evidence}` (guide + worker schema `checklist` minItems=maxItems=7 with prefixItems). Wording of `evidence` 'is not graded'.
- Rubrics: coverage/confidence/evidence_strength/practicality/stability/reuse_value/posture enums with definitions (guide 'Assessment rubric'); proposal schema requires all 7.
- Output shape: proposal.schema.json — claims[{statement, evidence[{locator, ledger_id}]}] (≥1), links[{url,relation,locator,ledger_id}] (≥1). Locator is just `minLength:1` text. Untrusted-evidence wrapper tags and 'ignore embedded instructions' rule.
- Worker is stateless, tool-free, no repo/vault context (guide §'Structured proposal'). Prompt 'enforces exact proposal/ledger locator equality'.

### 2. What code checked afterwards
- `_validate_proposal` (atlas_quality.py:1034-1310): strict keys/enums/date shape; every claim evidence `(locator, ledger_id)` must be in `evidence_ledger.evidence` (`PROPOSAL_EVIDENCE_LOCATOR_UNBOUND`, :1290-ish) and links likewise (`PROPOSAL_LINK_LEDGER_UNBOUND`); regex context leak (`GENERATED_CONTEXT_RE` :132, `REPOSITORY_CONTEXT_RE` :137 → `PROPOSAL_CONTEXT_LEAK` :1309). **The ledger is model-authored, so this proves self-consistency, not that the locator exists on the page.** `_line_number` (:304) is only used to report finding lines.
- `validate_summary` (:666-1005): frontmatter keys/enums, adopt coupling (`ADOPT_COUPLING_INVALID`), content-hash equals effective hash, canonical URL match, URLs in summary must be in evidence bundle (`URL_OUTSIDE_EVIDENCE`), exact normalized duplicate sentences, placeholder/boilerplate notes, `SOURCE_LOCATOR_MISSING` only when evidence_strength=high (regex `LOCATOR_RE`), routing-reason regex `Verifier: <locator> — <claim> [relation=..; impact=..]`.
- Plan T5 states the limit outright: 'deterministic checks do not pretend to judge semantic faithfulness or paraphrased redundancy' (archive/2026-07-15-0004_atlas-t5-quality-hardening.md:166) and 'Cross-provider semantic quality cannot be mathematically guaranteed… open-ended groundedness and concision fail closed through shared calibration plus bounded post-generation audit' (:348).
- No quote/substring/line-range verification against payload_text exists in scripts/ (grep for payload find/`in payload` yielded none; `.find(` only in `_line_number`).

### 3. Retry / failure
- Gates return `{state:'needs-revision', findings}` (atlas_source.py:2514, 2607, 2691, 2957-2971, 3089). Guide line 92: 'An initial `needs-revision` permits at most one targeted same-worker complete replacement; classifier transport or framing failure performs no prepare or write.' Final failed gate → 'stops without a write'. Inaccessible/insufficient text or aggregate page → halt, ask once (`page-only|expand|stop-without-writing`); no answer = no write.
- Observed failure: worker returned partial `kind:ready` without `evidence_ledger`, `proposal`, `checklist`, `refresh_after` (archive/2026-08-02-1452_swarm-source-recovery.md:9-22); fix was a ref-free structured-output schema + coordinator reading the direct reply.

### 4. Eval set
`evals/source-summary-quality.json` is a *calibration fixture*, not a page corpus: 7 assessment_cases (expected enum tuples from a one-sentence description), summary_cases (all-pass; one isolated fail per checklist item; context-perturbation pair a/b; four domain cases), 3 routing_cases, ~21 negative_audit_cases (context leaks, redundancy, unbacked metadata attribution, invented repo structure, prompt injection, inaccessible/thin no-write, aggregate-page question, date precision, frontmatter types, boilerplate notes). `validate_calibration` exact-compares model verdicts to expected JSON. It measures whether a model-as-reviewer reproduces pass/fail labels, not whether claims are on a real page.

### 5. Lessons from plans (quotes)
- Original defects: 'campaign-local language such as “T2 owns adoption,” repeated assessment/routing boilerplate, collapsed signal values, weak source locators, and three false `coverage: complete` claims caused by 300-line truncation' (archive/2026-07-14-1538_atlas-source-summary-quality.md:10). Truncation repairs: seq 21–23 (300/425, 300/378, 300/303 lines) (:186-189).
- Cross-model: OMP GPT-5.6-Sol 28 g0 / 1 g1 / 1 g2 first-pass validator passes vs Grok 25 g0 / 4 g1 / 1 g2 (archive/2026-07-16-1211_atlas-source-summary-cross-harness.md:359); material 'orientation noise' in LLM reviewer (:360); three OMP and six Grok deterministic-fail predecessors (:340, :349). Two validator successors were needed to align validator with template (:341).
- Quality-guide eval A/B: hard failures were source-independent contract gaps fixed twice ('evidence_strength now distinguishes substantive but thin primary claims', 'Canonical directory… non-recursive' – 2026-07-14-1538:154-157).
- Cohort audit found 'unsupported licensing, authorship, state-machine, and cross-source claims were removed' and 3 adopt→trial downgrades (2026-07-14-1538:327).
- X: 'A foreign reply cannot make an empty, truncated, or placeholder primary post pass' and 'main_post.text length alone never proves completeness' (2026-07-21-1613_living-source-quality-revisit.md:256, :267); 503-source recapture mostly ended 'blocked_evidence_regression 265, hash_baseline_incomparable 221' (:97).
- Task-schema transport failures: 'Task cannot resolve sibling source-summary-proposal.schema.json' (swarm-source-recovery.md:15-19).

### 6. X author-reply rule precedent (v1)
2026-07-21-1613_living-source-quality-revisit.md:279-283: 'Include a thread continuation only when its stable author ID matches the primary author; if no stable ID is exposed, use case-insensitive exact username equality. If neither… include only the primary and add `self_thread_identity_unavailable` to `retrieval.missing`'; third-party replies/quotes excluded; hash must exclude counters. v2 (issue 12:66) instead stores post+author replies by handle and has the summarizing model keep only replies that continue the post.

### 7. Vault sample (~14 read: kumo, seeking-leverage, own-the-outer-loop, eval-engineering, auto-memory, memsearch, swarm, next.js-pagespeed, 7-rules, tradingview-mcp, factor-12, uisavior; frontmatter of ~30)
All 673 are schema_version 1; 382 GitHub-host, 191 X; 23 `coverage: partial`.
- **Locator forms**: section/heading names (`## Phase B: Fan out`, `README.md > "For Agent Users" > "Embedding"`), file/status ids (`status 1945481700068204971`), rule labels; almost never quotes or line ranges. Vague/non-locating: `primary-post-text` (Next.js), `opening`, `Seeking Leverage opening`, `capture.text — primary post section…` (leaks pipeline term; 1 file), `Quick Start (5 Minutes)` on a 25 KB README with 1 evidence bullet.
- **Overlong locators**: auto-memory & memsearch locators run 300+ chars and are concatenated into every Assessment note; 22 artifacts have a Coverage note >300 chars.
- **Claim/locator mismatch pattern**: one claim repeated under many locators (memsearch: same sentence under 3–4 different README headings; Auto Memory repeats a 'Source-local assessment' claim under four locators) — ledger binding passes because the pairs match, though the locator doesn't specifically support the claim.
- **Thin extraction** (3-claim summaries): kumo/own-the-outer-loop have 3 one-line claims; TradingView README (25,300 bytes) yields 1 key point; 'Unknown' author/publisher on many docs.
- **Boilerplate from renderer, not model**: `atlas_source.py:1654-1664` assessment notes ('The claim at X directly supports the summary'), :1708 caveat 'The proposal establishes only the source-local claims bound to the listed evidence locators.' (183 of 673 artifacts), :1721 reuse cues 'What evidence does the source give for this claim: <claim>' (189 of 673). Rubric fields (confidence/strength) were thus not backed by notes in these.
- **Leakage**: context-leak regex (T#, 'this task', vault://, .agents/plans) over all summaries: **0 matches**. No overt repo-context leakage observed.
- **Fidelity risks I could not verify** (no page text): claims paraphrased from X threads may include material from replies; `published` dates inferred (X 'Published 2026-07-29' unverified) [INFERENCE]. A TL;DR can be a single copied key point (Seeking Leverage; Kumo).

### 8. Issues 08/11 bearing on content
- 08: TL;DR 'small significant gains, +0.018 for hybrid and +0.014 for BM25'; reuse cues 'no significant gain for BM25 (+0.001) or hybrid (+0.007)'; v1 full note vs v2 claims-first 'same for BM25 (0.752 both)'; 'The extra v1 sections bring no search benefit beyond the TL;DR and cues effects'; abstract/cues decision owned by ticket 06 (resolved: 1–2 sentence abstract, no cues — 06:151, 176).
- 11: 'Reading the whole record does not help Jev rerank (+0.010 nDCG, not significant)'; Jev rerank was on title + 700 chars. Nothing on claim quality.

### 9. Directly implied by evidence (no recommendation)
- v1's locator check was a pair-equality between two model-authored lists; a substring/anchor check against stored cleaned text was never run (hence ticket 12 item 8 relies on locators pointing into stored text).
- Second pass in v1 = the same model's 7-item self-checklist plus (in qualification only) a different-model reviewer (GPT-5.6-sol); reviewer noise measured at 25/30 and 28/30 orientation agreement (cross-harness:359).
- Cheaper-model evidence in v1: none on cost; only 2 frontier models compared (OMP GPT, Grok), both succeeded within ≤2 repair generations.
