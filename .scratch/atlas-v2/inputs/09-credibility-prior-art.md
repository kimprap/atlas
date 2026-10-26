# Research Evidence: prior art for weighting sources by credibility in search, fact-checking and LLM research/RAG systems

## Authority and scope
- Requesting owner: Wayfinder controller acting as `dev-ask` for ticket `issues/09-decide-source-credibility-weighting.md` (Atlas v2 map). Receiver: same controller.
- Governing revision: the settled v2 minimum (ticket 02), which this research does not reopen. Every source records author and publisher. Standing per-author and per-subject trust notes. When sources disagree, answers show who says what and which way they lean. Trust is re-judged over time. The user warned that strict weighting causes false negatives in both directions (a company over an unknown X account, and a respected practitioner over a company on his own subject).
- Bounded question, five parts. (1) Which signals are used. (2) How user-set trust combines with automatic judgement, and who takes precedence. (3) How trust changes over time. (4) Harms and false negatives of strict weighting: filter vs down-rank vs label. (5) Whether LLMs can judge author or publisher credibility from the page alone.
- Stop condition: 10–15 primary sources, with each part covered or a stated gap. Research only. This file makes no design decision.
- Access date for all sources: 2026-10-22 (via web search and reader extracts; quotes come from those extracts).

## Sources
Each entry gives the identity, date and link, then the claim relevant here.

**S1. Google, Search Quality Rater Guidelines ("General Guidelines"), 11 Sep 2025.** https://guidelines.raterhub.com/searchqualityevaluatorguidelines.pdf
- §3.4: "The most important member at the center of the E-E-A-T family is Trust." Experience means "first-hand or life experience for the topic". Expertise means "knowledge or skill for the topic". Authoritativeness means "known as a go-to source for the topic".
- §3.3: reputation of the website *and* the content creator. "Reputation research should be performed according to the topic of the page." When self-description conflicts with independent sources, "trust the independent sources."
- §3.3.5: "small websites may have little or no reputation information. This is not indicative of high or low quality." Also: "A lack of reputation about people who post personal content is neither a positive nor a negative sign."
- Limit: raters do not set rankings directly. The guidelines evaluate Google's systems.

**S2. Wikipedia, "Reliable sources/Perennial sources" (WP:RSP), live page as of about Jul 2026.** https://en.wikipedia.org/wiki/Wikipedia:Reliable_sources/Perennial_sources
- Four statuses: generally reliable "in its areas of expertise", no consensus (context-dependent), generally unreliable, deprecated. A separate blacklist is reserved for abuse.
- Deprecation raises an edit-filter warning that "can be dismissed". It does not block.
- "Consensus can change, and context matters tremendously." An entry is marked stale when it has not been discussed for four or more years. Only a newer RfC overturns an RfC. A change in consensus caused by changes in the source "does not apply to publications of the source from before the changes."

**S3. Wikipedia, "Verifiability" policy, self-published sources (WP:SPS), live page as of about Mar 2026.** https://en.wikipedia.org/wiki/Wikipedia:Verifiability
- Self-published material is "largely not acceptable". Exception: "Self-published sources may be considered reliable if published by an established subject-matter expert, whose work **in the relevant field** has previously been published by reliable, independent publications."
- This is a subject-scoped exception for individual practitioners. It never applies to claims about living people.

**S4. NewsGuard, "Website Rating Process and Criteria", page about Apr 2026, plus FAQ.** https://www.newsguardtech.com/ratings/rating-process-criteria/
- Nine pass/fail criteria, weighted to total 100. Credibility carries 75 points (e.g. "does not repeatedly publish false content" = 22). Transparency carries 25 (e.g. ownership and financing = 7.5). Some weights come from a secondary transcription.
- Bands: 75–99 Generally Credible, 60–74 Credible with Exceptions, 40–59 Proceed with Caution, 0–39 Maximum Caution. Platforms of user content get a "Platform" label and are not scored.
- Output is a written "Nutrition Label" explaining who is behind the site and why it got its score. Scoring is done by human journalists at publisher level. Individual authors are not scored.

**S5. Yin, Han, Yu, "Truth Discovery with Multiple Conflicting Information Providers on the Web" (TruthFinder), KDD 2007, DOI 10.1145/1281192.1281309.** http://hanj.cs.illinois.edu/pdf/kdd07_xyin.pdf
- "a web site is trustworthy if it provides many pieces of true information, and a piece of information is likely to be true if it is provided by many trustworthy web sites". Both quantities are inferred iteratively, starting from equal trust for every site.
- Copying between sites breaks the independence assumption, so the paper adds a dampening factor. The full formulas were not verified in the PDF.

**S6. Ma et al., "FaitCrowd: Fine Grained Truth Discovery for Crowdsourced Data Aggregation", KDD 2015, DOI 10.1145/2783258.2783314.** https://cse.buffalo.edu/~lusu/papers/KDD2015Fenglong.pdf
- Prior methods "assume that a source has the same reliability degree on all the questions, but ignore the fact that sources' reliability may vary significantly among different topics."
- FaitCrowd estimates per-topic expertise jointly with the truth, and reports lower aggregation error than global-reliability baselines on two real datasets.

**S7. Li et al., "On the Discovery of Evolving Truth", KDD 2015, DOI 10.1145/2783258.2783277.** https://pmc.ncbi.nlm.nih.gov/articles/PMC4688022
- "The observed source reliability changes over time." Existing methods wrongly assume it is fixed.
- The paper updates source weights incrementally as data arrives, using a smoothing factor and a decay factor.

**S8. X, Community Notes documentation (`twitter/communitynotes`, `ranking-notes.md` and `writing-ability.md`), live repository as of 2026.** https://github.com/twitter/communitynotes/blob/main/documentation/under-the-hood/ranking-notes.md and https://github.com/twitter/communitynotes/blob/main/documentation/contributing/writing-ability.md
- Bridging: a matrix factorisation `r = μ + i_u + i_n + f_u·f_n`. The note intercept `i_n` is its helpfulness, so a note scores high only if raters who usually disagree both rate it helpful.
- Helpful at intercept ≥ 0.40. Polarised notes need a lower score before they are marked Not Helpful. Status is recomputed hourly and can flip.
- Contributor standing is earned. New contributors can only rate until their "Rating Impact" reaches 5, which rises when their ratings match the eventual status. Writing is locked again when 3 of their last 5 notes are rated Not Helpful.

**S9. Pan et al., "Not All Contexts Are Equal: Teaching LLMs Credibility-aware Generation" (CAG), EMNLP 2024, arXiv 2404.06809.** https://aclanthology.org/2024.emnlp-main.1109/
- "LLMs relying solely on internal knowledge to assess information credibility are unstable and unreliable." The paper therefore feeds *external* credibility labels (high, medium or low, based on relevance, timeliness and source) and fine-tunes the model to use them.
- The authors report that the model "supports customized credibility".

**S10. Deng et al., "CrAM: Credibility-Aware Attention Modification in LLMs for Combating Misinformation in RAG", AAAI 2025, arXiv 2406.11497.** https://arxiv.org/abs/2406.11497
- Training-free method that down-weights attention to low-credibility documents. Reports more than 20% improvement against misinformation pollution on NQ and TriviaQA.
- It explicitly *assumes* good credibility scores already exist. It also works with GPT-generated scores.

**S11. Hwang et al., "Retrieval-Augmented Generation with Estimation of Source Reliability" (RA-RAG), EMNLP 2025, arXiv 2410.22954.** https://aclanthology.org/2025.emnlp-main.1738/
- Standard RAG "relies solely on relevance… overlooking the heterogeneous reliability of these sources."
- Source reliability is estimated "by cross-checking information across multiple sources" without manual fact-checking. Answers are aggregated by reliability-weighted majority vote.

**S12. Wan, Wallace, Klein, "What Evidence Do Language Models Find Convincing?", ACL 2024, DOI 10.18653/v1/2024.acl-long.403.** https://aclanthology.org/2024.acl-long.403/
- Models "rely heavily on the relevance of a website to the query, while largely ignoring stylistic features that humans find important such as whether a text contains scientific references or is written with a neutral tone."
- Counterfactually raising a document's relevance raises how often the model sides with it.

**S13. Yang & Menczer, "Accuracy and Political Bias of News Source Credibility Ratings by Large Language Models", arXiv 2304.00228 v2/v3 (WebSci 2025).** https://arxiv.org/abs/2304.00228
- Covers 8 LLMs and more than 7,000 outlets, rated by name only. LLMs agree with each other (ρ≈0.81) but "only moderately with human expert evaluations (ρ≈0.59)".
- Larger models refuse to rate less popular sources. Smaller models hallucinate ratings.
- Default models show a liberal skew, and a model given a partisan persona rates in line with that persona.

**S14. Loru et al., "The simulation of judgment in LLMs" (preprint title: "Decoding AI Judgment…"), PNAS 2025/26, arXiv 2502.04426.** https://www.pnas.org/doi/10.1073/pnas.2518443122
- 6 LLMs rated outlets from homepage text and were compared with NewsGuard and MBFC. They flag unreliable sites well but misclassify many reliable ones (GPT-4o mini about 32–33%, Llama 4 Maverick about 35%).
- "lexical associations and statistical priors replace contextual reasoning". Reliable labels track "references to editorial standards and institutional transparency".

**S15. Ye et al., "Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge" (CALM), ICLR 2025, arXiv 2410.02736.** https://arxiv.org/abs/2410.02736
- Authority bias: judges prefer answers with authoritative references *even when the references are fake*. Quote and book references "strongly influence most models".

**S16. Sharma et al., "Towards Understanding Sycophancy in Language Models", ICLR 2024, arXiv 2310.13548.** https://arxiv.org/abs/2310.13548
- Five assistants tailor answers and feedback to the user's stated views. "Matching a user's views is one of the most predictive features of human preference judgments."

**S17. Aslett et al., "News credibility labels have limited average effects on news diet quality and fail to reduce misperceptions", Science Advances 8(18), May 2022, DOI 10.1126/sciadv.abl3844.** https://csmapnyu.org/research/academic-research/news-credibility-labels-have-limited-average-effects-on-news-diet-quality-and-fail-to-reduce-misperceptions
- Field experiment with the NewsGuard extension (n=3,337 surveyed, 968 with browsing traces). Source labels did not shift average consumption or misperceptions. There were possible gains for the heaviest consumers of misinformation.

**Product documentation, which shows how user control is exposed:**
- **P1. Kagi, "Website Info & Personalized Results" help page.** https://help.kagi.com/kagi/features/website-info-personalized-results.html
  - Per-domain Block, Lower, Normal (the default), Higher or Pin. A Pinned domain's relevant hits go to the top. Personalisation can be turned off per search. It is domain-level only.
- **P2. OpenAI web_search tool guide**, https://developers.openai.com/api/docs/guides/tools-web-search, and the ChatGPT deep research feature page, https://chatgpt.com/features/deep-research/
  - The API takes `allowed_domains` and `blocked_domains` (up to 100). The deep research page says: "Curate and approve a set of URLs… Deep research prioritizes these sources over general web results."
  - The API's "Prioritize reliable… sources" text is only a prompt example.
- **P3. Perplexity `search_domain_filter`.** https://docs.perplexity.ai/docs/search/filters/domain-filter
  - Allowlist *or* denylist, up to 20 entries, path-level entries allowed. It is a hard filter.
- **P4. Consensus, "How Consensus Works" and "The Consensus Meter" help pages.** https://help.consensus.app/en/articles/9922673-how-consensus-works
  - Quality signals are recency, citation count and journal reputation. These re-rank candidates that were first selected by relevance.
  - The Meter shows per-position aggregates (recency, methods, journal SJR, citations) as display badges.
  - Exact weights are not published.
- **P5. Elicit, "Paper Search".** https://elicit.com/solutions/search
  - Primary ranking is by semantic relevance. Citation count and recency are features, and an LLM re-ranks the top 1,000 by relevance.
  - Quality is controlled by user filters and screening criteria, which the user can override.

## Findings

### Established facts, by part

**Part 1: signals.**
- *Author and publisher identity:* S1 (creator and site reputation), S4 (transparency criteria; publisher level only), S3 (author track record in the field).
- *Track record and accuracy history:* S4 (repeated false content is worth 22 of 100 points), S5, S7, S11 (estimated from agreement with other sources), S8 (rater track record).
- *Per-subject expertise:* S1 (reputation researched "according to the topic"), S2 ("in its areas of expertise"), S3 ("in the relevant field"), S6 (per-topic reliability beats global reliability).
- *Recency:* S9 (timeliness is part of the credibility label), P4 (recency is a ranking signal), S7 (time-varying reliability).
- *Corroboration:* S5, S11 (agreement-based), S8 (agreement *across people who usually disagree*, not raw majority).
- *Coverage of the systems:* publisher-level systems are mature (S2, S4). Author-level systems are judgement-based (S1, S3) or crowd-based (S8). Signal-level LLM credibility work exists but was only skimmed for this file: the Pastel paper (arXiv 2309.07601) and the survey arXiv 2410.21360.

**Part 2: user-set trust vs automatic judgement.**
- Products expose user trust as explicit tiers that override or bias automatic ranking. The tiers are Kagi's block, lower, raise and pin (P1), allow and deny filters (P2, P3), and "curated" sources prioritised over the general web (P2).
- Pin and allowlist give the human absolute precedence. Raise and lower bias ranking but leave automatic relevance in force (P1).
- CAG reports support for "customized credibility", meaning credibility supplied from outside the model, so a user's labels can be fed in place of the model's judgement (S9).
- CrAM and CAG both treat credibility scores as an *external input* the model consumes, not something it must infer (S9, S10).
- Wikipedia's precedence is human consensus over any single rating, with context overriding the list (S2). Even deprecation is a dismissible warning (S2).
- No source found documents per-*author* plus per-*topic* user trust notes combined with automatic scoring in a research assistant. Kagi works per domain. OpenAI and Perplexity filter by domain or URL.

**Part 3: trust over time.**
- Trust is re-estimated as evidence arrives, with decay, because "observed source reliability changes over time" (S7).
- Standing is earned from agreement with later consensus and lost after repeated misses (S8). Statuses are recomputed hourly and can flip (S8).
- Ratings go stale after 4 years without discussion. A re-rating is not applied backwards to older output (S2).
- An unknown starts neutral: equal starting trust in TruthFinder (S5), and an absence of reputation is "neither a positive nor a negative sign" (S1).

**Part 4: harms of strict weighting.**
- Deployed systems mostly avoid hard exclusion based on reputation alone. Wikipedia's harshest common tier warns and lets the editor dismiss it, and blacklisting is reserved for abuse (S2). Google treats missing reputation as neutral (S1). Both Wikipedia (S3) and NewsGuard (S4, the "Platform" label) keep an explicit exception path for individual experts or user-content platforms instead of scoring them as a publisher.
- Hard filters exist only as explicit, user-chosen tools (P2, P3). Perplexity's filter is either allow-only or deny-only.
- Display-only source labels had little average behavioural effect in a field test (S17). That makes labels low-risk, but also weak at changing what readers rely on.
- LLM credibility judgements are biased in several documented ways:
  - political skew and persona-driven skew (S13);
  - lexical priors, and over-flagging of reliable outlets (S14);
  - preference for fake authoritative citations (S15);
  - weak coverage of less popular sources, through refusal or hallucination (S13);
  - a tendency to tailor to stated user views (S16).
- Inference: the last point applies to stated trust notes, but no source tests trust notes directly.

**Part 5: can LLMs judge credibility from a page alone?**
- Moderately, at publisher level, and mostly from prior knowledge rather than the page: ρ≈0.54–0.59 against experts (S13).
- From homepage content they catch unreliable outlets but misjudge many reliable ones (S14).
- They largely ignore on-page credibility cues such as references and neutral tone, and follow relevance instead (S12).
- CAG's authors call LLM-internal credibility assessment "unstable and unreliable" (S9).
- No source found measures LLM accuracy at judging an *individual author's* expertise from a page.

### Contradictions and gaps
- **Do stylistic cues sway LLMs?** S12 finds stylistic and credibility cues barely move models. S15 finds fake citations do sway LLM *judges*. The tasks differ (answer selection vs pairwise judging), so these can both hold, but S15 means on-page authority markers can be spoofed.
- **Does the LLM skew reflect partisanship?** S13 attributes the political skew to LLM bias. S14 argues it comes from lexical cues, not partisan preference. The two agree on the observed asymmetry and differ on its cause.
- **What the agreement numbers measure:** "agreement with experts" in S13 and S14 measures alignment with NewsGuard and MBFC, which are themselves contested, not ground truth.
- **Topic-scoped trust:** S6's per-topic gain comes from crowdsourced QA with many answers per source. Its reported gain may not transfer to a small personal library (inference).
- **Gaps:**
  - No primary source covers per-author, per-topic *user* trust notes in an LLM research tool.
  - No source measures LLM accuracy on author expertise.
  - No evidence on how trust notes in a prompt interact with sycophancy (S16 is indirect).
  - Gemini deep research and Perplexity publish no documented source-weighting method beyond filters. Not searched in depth.
  - Elicit's own page and a secondary review disagree on whether citations are weighted (P5).

### Explicit inferences
- [INFERENCE] Truth-discovery methods (S5, S6, S7, S11) need many overlapping claims per source. A personal library with few sources per question may not give enough overlap for reliable automatic estimates.
- [INFERENCE] Because LLM credibility ratings lean on memorised reputation (S13, S14), they are likely to under-rate unknown X accounts and niche practitioners, which is the false negative the user named. They may also over-rate established brands on subjects outside their expertise, which is the inverse case the user named.
- [INFERENCE] S16 together with S15 suggests that a trust note phrased as "lean towards X" could push an LLM answerer to over-agree with X. The note may need to be applied as visible metadata or as a ranking input rather than only as prompt text. This is untested.

## Decision coverage
What the evidence supports for each option, without choosing between them:

- **(a) No weighting, display only (who says what, and their lean).**
  - For it: it matches the settled v2 minimum. It avoids every false-negative path. Wikipedia's "context matters" and dismissible warnings (S2) and Google's neutral treatment of missing reputation (S1) point toward labels over exclusion.
  - Against it: labels change behaviour little on average (S17). Plain relevance ranking lets well-matched but weak pages win (S12, S11).
- **(b) Ranking boost from user trust notes only.**
  - For it: this is the dominant pattern in search and research products (P1 raise/lower/pin, P2 curated sources prioritised, P3 filters). It keeps the human as the final authority. CAG and CrAM show externally supplied credibility can be consumed effectively (S9, S10).
  - Limits: coverage is limited to sources the user has noted, and unknown sources stay neutral, which S1 supports. Kagi-style systems work per domain. Per-author ranking is undocumented.
- **(c) Automatic credibility score.**
  - For it: truth discovery and RA-RAG show agreement-based reliability estimates improve answers *when there is enough overlapping evidence* (S5, S11).
  - Against LLM-judged scores specifically: they show moderate expert agreement, political and lexical bias, weak coverage of less popular sources, and susceptibility to fake authority (S13, S14, S15, S9). That is the false-negative risk the user described.
  - Unsupported: no evidence covers automatic *author-expertise* scoring from pages.
- **(d) Per-subject trust.**
  - For it: subject scoping appears in every mature framework (S1, S2, S3) and in FaitCrowd (S6), and it directly handles the practitioner-over-company case through S3's "in the relevant field" exception.
  - Open: whether a small library has enough data to *learn* per-subject trust automatically (S6 needs many answers per source). As user-set notes, it is consistent with (b).
- **Cross-cutting, supported by evidence:**
  - Re-evaluation over time: S7 decay, S8 earned and lost standing, S2 staleness and no backwards re-rating.
  - A neutral starting point for unknown authors (S1, S5).
  - Keeping hard exclusion as an explicit user act, not an automatic one (S2, P2, P3).
- **Not decided here:** which option or combination to adopt, the exact precedence order between notes and any automatic signal, and whether trust notes are applied in retrieval ranking, the answer prompt, display, or several of these.

## Freshness and capture
- Stored-evidence freshness: not applicable. No research store was used, and all evidence was gathered fresh on 2026-10-22.
- Capture: `/Users/kim/dev/atlas/app/.scratch/atlas-v2/inputs/09-credibility-prior-art.md`

## Next owner
- Wayfinder controller acting as `dev-ask` for ticket `issues/09-decide-source-credibility-weighting.md`.
