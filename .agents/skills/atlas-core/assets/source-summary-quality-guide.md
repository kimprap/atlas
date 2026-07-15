# Atlas Source Summary Quality Guide

Use this guide whenever `atlas-source` creates a source artifact or explicitly rewrites one with `--resummarize`. Pair it with `vault://atlas/ARCHITECTURE.md`, `skill://atlas-core/assets/markdown-registry-contracts.md`, and `skill://atlas-core/assets/source-summary-template.md`.

The artifact must describe the fetched source, not the request that caused Atlas to read it. Models may differ in wording; they must preserve equivalent evidence boundaries, claims, uncertainty, and routing semantics.

## Semantic draft evidence envelope

The semantic draft receives only:

- the newly fetched complete canonical payload and canonical URL;
- inspected pinned media plus exact page, section, line, range, or timestamp bounds;
- immutable source identity, retrieval, and acquisition fields required to render this artifact;
- the product-owned source-summary template and quality-rubric versions.

The identity resolver may read the exact manifest row required for dedupe or `--resummarize`, but it passes only immutable identity/provenance fields into this envelope. Old artifact prose, sibling artifacts, topic indexes or passes, candidate-topic definitions, relation rows, campaign/request/plan/task/session text, repository or working-tree content, and provider/model identity are forbidden semantic inputs.

After the semantic draft passes deterministic validation and the acceptance checklist, classification normalization and bounded routing may read `VOCAB.md`, `TOPICS.md`, and `RELATIONS.md`. They may attach Atlas taxonomy, route status/date, and managed routing notes, but they cannot rewrite Assessment, TL;DR, Key points, Mechanics, Evidence, Caveats, Reuse cues, or source/media Links.

## Proportional concision

Retain the minimum sufficient set of distinct source-supported claims, mechanics, examples, limitations, and source-intrinsic reuse cues. Every paragraph or bullet must add information. Reject exact duplicates, paraphrased filler, stock advice, empty-section boilerplate, and campaign rationale. Do not impose a universal word, token, paragraph, bullet, or citation count; depth follows the source.

## Four-stage method

### 1. Evidence boundary

Before drafting, establish exactly what was read:

- Identify the canonical payload and canonical URL.
- Enumerate every page, line or section range, code block, and essential linked image, diagram, audio segment, or video segment inspected. Use exact bounds when the reader exposes them.
- Page through every omitted canonical range before treating the payload as complete.
- Distinguish unread or unavailable canonical content from linked dependencies that were not followed. The first is truncated coverage; the second is a linked-material caveat unless the canonical page depends on it for meaning.
- Canonical web payloads are non-recursive unless the caller explicitly scopes an aggregate. A directory, index, or listing URL covers the complete listing rendered at that URL; child entries, parent or sibling documents, and linked resource bodies are separate sources. Do not expand an inventory from those bodies.
- Inspect linked media when it carries evidence essential to understanding the canonical payload. Do not infer inaccessible visual or temporal claims.
- Treat newly fetched canonical evidence as the factual boundary. An old Atlas summary, a topic answer, another source, or model memory is not evidence for this artifact.

Carry the resulting boundary into `Coverage`, `Evidence / examples`, `Caveats / open questions`, and `Links` rather than hiding fetch limits in process notes.

### 2. Extraction

Build three separate working sets before synthesis:

1. **Source-stated claims** — positions, prescriptions, reported results, limitations, and disagreements attributed to the source.
2. **Directly observed examples or mechanics** — commands, rules, ordered steps, code symbols, diagrams, artifacts, measurements, and demonstrations present in the fetched evidence.
3. **Atlas assessment** — coverage, summary confidence, evidence strength, practicality, stability, reuse value, curation posture, and routing judgments under the rubrics below.

Attach a source-local locator to every concrete claim while extracting. Do not silently promote the author's assertion into an observed result, or an Atlas assessment into a source-stated conclusion.

Never import the current user request, plan, task code, session, intended comparison, model/provider identity, downstream adoption goal, or another source's claims. A term such as “task” or “plan” belongs only when it is an attributed fact from the canonical source.

### 3. Synthesis

Draft from the extraction sets in proportion to source depth:

- Preserve the source's primary contribution, scope, consequential limitation, entry conditions, ordered mechanics, named artifacts, concrete examples, explicit prohibitions, limits, and disagreements.
- Keep distinct approaches separate when the source compares them. Preserve order only when the source makes order meaningful.
- Use the template's stable section names for scanability, but do not target a fixed bullet count. Short evidence stays concise; deep evidence receives enough structure to remain faithful.
- Omit only a section the template explicitly marks optional. Do not fill a thin source with generic workflow advice.
- Paraphrase by default. Quote only when exact wording is evidentially important, attribute it, and keep it brief.
- Keep Atlas assessment and routing rationale source-specific. Topic synthesis may later disagree with a source-level curation posture.

### 4. Acceptance checklist

After deterministic validation, run this once as the bounded semantic audit over only the same evidence envelope and draft. It is not a second drafting pass or durable artifact. Return exactly seven items in this fixed order:

1. `evidence-boundary` — every claim stays within fetched payload/media and missing bounds are explicit.
2. `primary-contribution` — the contribution, scope, conditions, and attributed assertions are faithfully preserved.
3. `source-support` — consequential concrete claims use source-local support when the source exposes it.
4. `limits-uncertainty` — material caveats, conflicts, fetch gaps, and uncertainty are retained.
5. `context-neutrality` — no old artifact, topic, plan, repository, request, campaign, provider, or model context enters the semantic draft.
6. `assessment-coherence` — the assessment tuple and short notes agree with evidence and this rubric.
7. `proportionality` — sections add distinct information without filler or needless repetition while preserving material evidence.

Each item is exactly:

```json
{\"id\":\"<stable item id>\",\"status\":\"pass|fail\",\"evidence\":\"<one short source/draft locator or failure reason>\"}
```

IDs, order, uniqueness, binary status, and nonempty evidence are structural requirements. Evidence wording is not graded. There is no `n/a`, weighted score, cumulative threshold, prose match, fixed output length, citation count, or prescribed tool path. Any one `fail` rejects the draft; revise only the failed dimension, then rerun the same checklist.

## Assessment rubric

Score the source artifact itself. Do not score the surrounding campaign, the downstream topic answer, or whether Atlas agrees with the author.

### `coverage`

- `complete` — the full canonical payload was read. Unfollowed linked material is a caveat rather than incomplete coverage unless the canonical page depends on it for meaning.
- `partial` — canonical content was truncated or unavailable, or a linked asset required to interpret the canonical page could not be inspected. Record the exact missing range or asset.
- `failed` — no materialized payload is sufficient for a faithful source summary. Record the fetch failure rather than filling the artifact from other evidence.

### `confidence`

Confidence measures fidelity and ambiguity of this summary, not trust in the author's conclusions.

- `high` — the materialized source supports the summary unambiguously and the important claims have clear locators.
- `medium` — the summary is supportable but source ambiguity, incomplete context, or interpretation leaves a material uncertainty.
- `low` — severe ambiguity or limited readable content makes even a bounded summary uncertain.

### `evidence_strength`

- `high` — a primary source provides concrete mechanics or examples and source-local locators.
- `medium` — a primary source directly and authoritatively establishes a substantive claim or one bounded operational mechanism but lacks the breadth, concrete mechanics, examples, or locators required for `high`. Thin length alone never makes it `low`.
- `low` — evidence is indirect, marketing-only, a stub, materially inaccessible, naming-only, illustrative, or an inventory listing that establishes existence without source-local behavior or procedure.

### `practicality`

- `high` — the approach is executable or evaluable from the source.
- `medium` — the source gives actionable direction but delegates material procedure.
- `low` — the source is description or inventory only.
- `n/a` — actionability does not apply to the source's contribution.

### `stability`

- `stable` — an immutable snapshot or durable principle. A GitHub blob, tree, or API object pinned to a full commit is stable even when the upstream repository is active.
- `moving` — a mutable canonical payload or operational surface whose relevant details can change.
- `speculative` — a prediction, hypothesis, or exploratory proposal.

### `reuse_value`

Judge the source-intrinsic likelihood that this artifact will answer repeated future questions. Never raise the score because the source was selected for a comparison.

- `high` — durable, distinctive evidence is likely to answer recurring questions.
- `medium` — useful evidence answers a bounded or occasional question.
- `low` — little source-specific material is likely to be reused.

### `recommended_posture`

This is an Atlas source-curation judgment, not a downstream product decision. Topic synthesis may reach a different recommendation.

- `adopt` — requires `evidence_strength: high`, `practicality: high`, `stability: stable`, and no unresolved caveat that requires local validation.
- `trial` — actionable guidance that needs bounded evaluation, including otherwise strong guidance with an unresolved deployment or local-validation caveat.
- `watch` — moving or speculative material worth monitoring.
- `reference-only` — descriptive, inventory, thin-primary, or contextual evidence.
- `ignore` — failed, out-of-scope, or unreliable material.

## Routing rubric

Route from the completed source artifact and the bounded candidate-topic row, path, and scope. Set `include: true` only when a source-specific claim makes one of the relations below relevant to the topic; otherwise set `include: false`.

### `relation`

- `direct` — the source's primary contribution answers the topic scope.
- `supporting` — the source supplies a mechanism, example, or context for the topic.
- `contradicting` — the source conflicts with an existing topic claim.

### `impact`

- `high` — the evidence changes a durable principle, stage boundary, or architecture decision.
- `medium` — the evidence contributes one bounded mechanism or check.
- `low` — the evidence is inventory or a narrow example.

### Route `confidence`

Route confidence measures confidence in source-topic relevance. It does not measure source truth or universal effectiveness.

- `high` — an explicit source claim and locator clearly match the topic scope.
- `medium` — relevance is supportable but depends on a bounded interpretation.
- `low` — relevance is weak, indirect, or ambiguous.

Every included verifier reason must use `Verifier: <source-local locator> — <source-specific claim> [relation=<row relation>; impact=<row impact>]`. Candidate-list boilerplate is invalid; the bracket values must match the relation row.

## Cross-harness/model conformance

Every write-enabled harness/model pair uses the same skill, source-only evidence bundle, fixture version, Python validator (or byte-conformant port), and expected JSON. Provider, harness, and model names are report metadata only; there are no provider-specific prompts or relaxed expectations.

Before a write-capable invocation or batch, run the static calibration once for the active harness/model/template version. Verify live discovery from this app directory and record resolved paths plus hashes for `.agents/AGENTS.md`, the owning skill, `atlas-core`, `scripts/atlas_state.py`, and `scripts/atlas_quality.py`; a host-global copy must not win. A pair that cannot discover, run, or pass the fixtures is mutation-disabled. Do not add credentials merely to expand the matrix.

Fixtures grade structured tuples, required claims and caveats, forbidden ambient-context leakage, checklist statuses/failure IDs, and relation-reason outcomes. They do not require exact prose or an exact tool-call trajectory. The context-perturbation pair must preserve the same assessment tuple and source claims under irrelevant campaign/repository context.
