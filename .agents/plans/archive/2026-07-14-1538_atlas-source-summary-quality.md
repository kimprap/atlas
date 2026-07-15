# Atlas Source Summary Quality and 12-Factor Coverage

**Datetime**: 2026-07-14-1538
**Scope**: Atlas source-summary generation contracts, cross-model and cross-harness qualification, regeneration of source sequences 5–35, and factor-level ingestion for HumanLayer's 12-Factor Agents.
**Summary**: Make Atlas source summaries source-grounded, context-neutral, model-agnostic, and structurally consistent without forcing identical prose; qualify that behavior through two OMP xhigh lanes and one Grok CLI high-effort lane; then regenerate the 31 AI-coding-workflow source artifacts and add one durable artifact for each of the twelve HumanLayer factors plus its Factor 13 appendix.
**Status**: DONE

## Context

The 31 source artifacts created on 2026-07-14 contain campaign-local language such as “T2 owns adoption,” repeated assessment/routing boilerplate, collapsed signal values, weak source locators, and three false `coverage: complete` claims caused by 300-line truncation. Source-summary shape is product-owned under `.agents/skills/atlas-core/assets/`, generation procedure is owned by `atlas-source`, and living summaries remain under `vault://atlas/`; command stubs stay thin. The intended end state is a reusable summary contract that different LLM families apply to the same evidence with equivalent coverage, claims, uncertainty, and routing decisions, plus complete factor-level evidence that extends—rather than replaces—the existing HumanLayer repository-root artifact.

## Tasks

- [x] T1. Strengthen source-summary contracts and ingestion behavior
  - completed 2026-07-14-1615
- [x] T2. Qualify summary behavior across model and harness configurations
  - completed 2026-07-14-2207
- [x] T3. Regenerate workflow source sequences 5–35
  - completed 2026-07-14-2305
- [x] T4. Ingest thirteen immutable 12-Factor source pages
  - completed 2026-07-14-2305
- [x] T5. Refresh affected research and verify integrity
  - completed 2026-07-15-0551

## Approach

### T1. Strengthen source-summary contracts and ingestion behavior

1. Update `.agents/ARCHITECTURE.md` in `Framework invariants`, `Mode ownership`, and `Source identity and routing` to distinguish routine refresh from explicit resummarization. Keep the existing write set. Add the exact event name `--resummarize`: it may rewrite an existing source artifact from newly fetched evidence even when `content_hash` is unchanged, but it must preserve `source_id`, `source_seq`, `canonical_url`, `first_seen`, `acquired_by`, `acquisition_run`, and the artifact path; routine unchanged refresh continues to update `last_checked` only. State that a resummarization updates `last_checked` and `last_summarized`, is never implicit, and must re-run bounded routing against the corrected artifact without reopening previously applied edges solely because prose changed.
2. Update `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` with deterministic `--resummarize` transitions:
   - Require an existing canonical URL or artifact path plus the explicit flag; missing or conflicting identities halt without writes.
   - Fetch the complete readable payload before scoring coverage. When the reader reports omitted lines, page until no omitted range remains. If full retrieval still fails, hash and summarize only the materialized payload, set `coverage: partial`, and record the exact missing range or asset.
   - Same hash: replace generated summary fields/body in place; preserve manifest identity/hash, acquisition provenance, and applied/rejected/superseded relation history; route-source may update existing `pending` edge fields, reject a no-longer-supported pending edge, or add a newly supported pending topic, but it must not convert an `applied` edge back to `pending` solely for a prose rewrite.
   - Changed hash: follow normal material-change routing. Mark old `pending` rows for the same source/topic and old hash `superseded`, preserve old `applied` rows as provenance, rerun candidate generation and the bounded verifier, and create a deterministic new pending edge only for an included candidate. If no candidate is included, create no replacement edge. Recompute topic dirty fields from `RELATIONS.md`.
   - After routing the current hash, set source `routing_status` and manifest `Route status` to `routed` when at least one current-hash relation is `pending` or `applied`, `no-topic-match` when no current-hash candidate is included, and `routing-blocked` only for a vocabulary/schema blocker. Historical edges for an old hash do not determine current-hash status.
   - Keep source-summary `schema_version: 1` and all current frontmatter keys/enums. This is a generation-contract refinement, not a schema migration.
3. Create `.agents/skills/atlas-core/assets/source-summary-quality-guide.md`; no existing asset owns this procedure. Keep it model/provider neutral and define the following four-stage method:
   - **Evidence boundary:** list exactly what canonical payload, pages/ranges, code blocks, and essential linked media were read; distinguish unread linked dependencies from truncation of the canonical payload.
   - **Extraction:** separate source-stated claims, directly observed examples/mechanics, and Atlas assessment. Never import the current user request, plan, task code, intended comparison, or another source's claims.
   - **Synthesis:** preserve the source's primary contribution, entry conditions, ordered mechanics, artifacts, examples, limits, and disagreements in proportion to source depth. Section names remain stable for scanability, but bullet counts are not fixed; omit only a section the template labels optional.
   - **Self-check:** reject unsupported facts, generic assessment notes, unmarked inference, false complete coverage, duplicated modal boilerplate, missing evidence locators, and session/task/model self-reference.
4. Put exact assessment and routing rubrics in the new guide so models converge on semantics rather than prose:
   - `coverage`: `complete` only when the full canonical payload was read; `partial` for truncated/unavailable canonical content; linked material is a caveat unless the page's meaning depends on it.
   - `confidence`: fidelity/ambiguity of the summary, not trust in the author's conclusions.
   - `evidence_strength`: `high` requires a primary source with concrete mechanics/examples and source-local locators; `medium` for primary but assertion/inventory/thin evidence; `low` for indirect, marketing-only, stub, or inaccessible evidence.
   - `practicality`: `high` when the material is executable/evaluable from the source; `medium` when it gives direction but delegates material procedure; `low` for description/inventory only; `n/a` when actionability does not apply.
   - `stability`: `stable` for immutable snapshots/durable principles, `moving` for mutable operational surfaces, `speculative` for predictions/exploration.
   - `reuse_value`: source-intrinsic likelihood of answering repeated questions—never “selected for this comparison.”
   - `recommended_posture`: an Atlas source-curation judgment, not a downstream product decision: `adopt` for stable/actionable/well-supported guidance, `trial` for actionable guidance needing bounded evaluation, `watch` for moving/speculative material, `reference-only` for descriptive/inventory/context evidence, and `ignore` for failed/out-of-scope/unreliable material. Topic synthesis may reach a different recommendation.
   - `relation`: `direct` when the source's primary contribution answers the topic scope, `supporting` when it supplies a mechanism/example/context, and `contradicting` when it conflicts with an existing claim.
   - `impact`: `high` for a source that changes a durable principle, stage boundary, or architecture decision; `medium` for one bounded mechanism/check; `low` for inventory or a narrow example.
   - Route `confidence` measures confidence in source-topic relevance, not source truth or universal effectiveness.
5. Refine `.agents/skills/atlas-core/assets/source-summary-template.md` rather than making it a rigid form:
   - Point authors to `source-summary-quality-guide.md` and keep frontmatter fields unchanged.
   - Replace the TL;DR prompt with source-only contribution, scope, and consequential limitation; remove “what future Atlas workflow should reuse it for.”
   - Require source-specific, falsifiable Assessment notes; do not prescribe stock sentences.
   - Make Key points and Approaches depth proportional instead of `3–7` bullets; `Approaches / mechanics` may be omitted only when the source contains no method.
   - Require every concrete Evidence bullet to start with a source-local locator when available: heading/section label, command or rule label, filename/code symbol, page/timestamp, or pinned linked asset.
   - Require Caveats to state source-specific limits and exact fetch bounds; generic lists of absent git/PR/delegation behavior are not sufficient by themselves.
   - Require Routing notes to cite a source-specific claim supporting relation/impact; topic IDs are permitted here, while plan/task/session references are not.
   - Keep Reuse cues as source-intrinsic future questions. Required sections remain header, TL;DR, Assessment, Classification, Key points, Evidence, Caveats, Routing notes, Reuse cues, and Links.
6. Update `.agents/skills/atlas-core/SKILL.md` to link the new quality guide and state that `atlas-source` reads it whenever it creates or explicitly resummarizes an artifact.
7. Update `.agents/skills/atlas-source/SKILL.md`:
   - Add `skill://atlas-core/assets/source-summary-quality-guide.md` to `Read first`.
   - Add the explicit `--resummarize` branch and the identity/hash/relation behavior above.
   - Require complete paged reads, essential linked-media inspection, source-only drafting, rubric scoring, locatable evidence, and the guide's self-check before writing.
   - Preserve normal unchanged-dedup behavior when the flag is absent.
8. Update `.agents/skills/atlas-audit/SKILL.md` with a bounded `--source-quality` audit mode and exact selectors `--source-seq <N|N-M>` plus repeatable `--source-id <id>`. It remains read-only and flags: generated references matching `\bT[0-9]+\b`, `this task|plan|conversation|comparison`, `selected explicitly for`, `owns adoption`, or `future Atlas workflow` unless clearly quoted from the source; `coverage: complete` paired with a truncation/unread-canonical-content caveat; identical Assessment note text dominating more than half a requested cohort; and high evidence strength with no source-local locator. Report paths/anchors; never auto-repair.
9. Leave `.agents/commands/atlas-source.md`, `.agents/commands/atlas-audit.md`, `atlas-acquire`, research templates, and scaffold files unchanged: command arguments already pass through, acquisition already delegates to `atlas-source`, and no artifact schema/write target changes.
10. Because `.agents/ARCHITECTURE.md` changes, sync only the named bound instance with `python3 scripts/atlas-instance.py sync-framework --name atlas`, then run `python3 scripts/atlas-instance.py check` before living-artifact work.

### T2. Qualify summary behavior across model and harness configurations

1. Create temporary output only under `/tmp/atlas-source-summary-quality/`; do not write fixtures into `vault://atlas/`. Create one prompt file per fixture under `/tmp/atlas-source-summary-quality/prompts/` and create output directories `outputs/omp-gpt-5.6-sol-xhigh/`, `outputs/omp-grok-4.5-xhigh/`, and `outputs/grok-cli-grok-4.5-high/`. Pass the same prompt bytes to all three execution lanes. For the first three fixtures, run analysis-only `atlas-source --resummarize` drafting with read-only tooling and the updated template/guide: OMP uses its unified `read` tool, while Grok CLI uses the case-sensitive native allowlist `Read,WebFetch` because that harness separates local-file and HTTP readers. OMP runs use `--no-session`; Grok CLI runs are isolated single turns with no resume, memory, or subagents. Run the reducer matrix as a contract-only dry run:
   - Thin wrapper: Matt `grill-with-docs` at `https://github.com/mattpocock/skills/blob/66898f60e8c744e269f8ce06c2b2b99ce7660d5f/skills/engineering/grill-with-docs/SKILL.md`.
   - Long workflow: Superpowers `subagent-driven-development` at `https://github.com/obra/superpowers/blob/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/subagent-driven-development/SKILL.md`; fetch all 425 lines, not the first 300.
   - Inventory-only source: existing Cursor Team Kit manifest source seq 7 at `https://github.com/cursor/plugins/tree/main/cursor-team-kit/skills`; read the complete directory listing but do not follow its skill folders for this fixture.
   - Reducer transition matrix: synthetic same-hash state with one `applied` edge, and changed-hash state with one old `pending` edge whose new bounded verifier result is `include: false`; this fixture reads the new contract only and writes no source.
2. Run every fixture once through exactly these three configured lanes, producing twelve primary outputs:
   - OMP `openai-codex/gpt-5.6-sol` with `--thinking xhigh`.
   - OMP `xai-oauth/grok-4.5` with `--thinking xhigh`.
   - Grok CLI `grok-4.5` with `--reasoning-effort high`.

   Use this artifact-fixture prompt, substituting only the fixture URL; store the reducer prompt separately so every lane receives identical fixture-specific text:

   ```text
   Read skill://atlas-source, skill://atlas-core/assets/source-summary-template.md, and skill://atlas-core/assets/source-summary-quality-guide.md. In analysis-only mode, draft the source artifact for <url> using --resummarize. Do not write files or vault state. Return the complete draft.
   ```

   For the reducer fixture use exactly: `Read skill://atlas-core/assets/markdown-registry-contracts.md. In analysis-only mode, reduce two cases: (A) source s/current hash h1 has one applied edge edge--s--t--h1 and same-hash summary prose is rewritten; (B) source s moves from h1 to h2, its only h1 edge is pending, and the bounded verifier excludes topic t. Return before/after source routing status, relation rows, and topic pending-edge/dirty fields. Do not write files or vault state.`

   OMP command shape, with `<omp-model>` set to each named OMP model and `<lane>` naming its output directory:

   ```bash
   omp -p --no-session --tools read \
     --skills 'atlas-source,atlas-core' \
     --cwd /Users/kim/Desktop/ng3/atlas/app \
     --model '<omp-model>' --thinking xhigh --max-time 180 \
     '@/tmp/atlas-source-summary-quality/prompts/<fixture>.txt' \
     > '/tmp/atlas-source-summary-quality/outputs/<lane>/<fixture>.txt'
   ```

   Grok CLI command shape:

   ```bash
   grok --prompt-file '/tmp/atlas-source-summary-quality/prompts/<fixture>.txt' \
     -m grok-4.5 \
     --reasoning-effort high \
     --output-format json \
     --tools 'Read,WebFetch' \
     --no-subagents --no-memory \
     --yolo --no-auto-update --max-turns 30 \
     > '/tmp/atlas-source-summary-quality/outputs/grok-cli-grok-4.5-high/<fixture>.json'
   ```

   Accept a Grok CLI run only when the command exits zero and stdout is a success JSON object with a nonempty string `.text`. Extract `.text` to the corresponding `<fixture>.txt`; retain `.sessionId`, `.stopReason`, `.usage`, and `.num_turns` in the raw JSON for transport evidence. Never resume these fixture sessions.

   Grok CLI built-in tool names are case-sensitive. Lowercase `--tools read` exposes no local or network reader in version `0.2.101`; `Read,WebFetch` is the read-only cross-harness equivalent of OMP's unified `read`.
3. Grade deterministic research behavior, not exact wording. All twelve outputs must have the expected artifact sections or reducer-state fields; zero generated task/session/comparison references; honest and identical canonical evidence bounds; source-specific Assessment notes; at least one locator-backed Evidence item for artifact fixtures; no unsupported ordering/artifacts; and no generic shared routing sentence. Claim sets must agree on source-stated entry conditions, mandatory phases, outputs, explicit prohibitions, and relation transitions. Require exact agreement for `coverage`, `stability`, `recommended_posture`, and whether `practicality` is `n/a`. For `confidence`, `evidence_strength`, `reuse_value`, and non-`n/a` `practicality`, use `low < medium < high`; values may differ by at most one step only when each differing value cites a distinct source fact.

   Separate hard contract failures from permissible quality differences:
   - A hard failure is an unsupported fact, missed mandatory mechanic, incomplete canonical read represented as complete, generated-context leak, missing required state transition, or rubric result outside the tolerances above. Re-run that lane once with identical prompt bytes. If the current guide already unambiguously requires the missed behavior and the repeat still fails, record a model/configuration limitation and block T2; do not add model-specific instructions.
   - Refine the template or guide only when the root cause is a source-independent missing or ambiguous contract that generalizes across fixtures. Make the smallest semantic clarification, then rerun the full twelve-output matrix.
   - Differences in prose, bullet count, section depth, emphasis among supported details, or overall polish are not failures. When all hard contracts pass but qualitative quality differs, use the OMP `openai-codex/gpt-5.6-sol` xhigh output as the preferred reference answer. Record the comparison; do not merge drafts or change the template/guide to make the other lanes imitate it.
   - None of the fixture drafts, including the preferred GPT reference, becomes factual input for T3; each later artifact is regenerated from its fetched source.
4. Require these fixture-specific results:
   - Thin wrapper: `coverage: complete`; do not invent the internals of `grilling` or `domain-modeling`; practicality and evidence strength cannot be `high`; posture is `reference-only`.
   - Long workflow: `coverage: complete`; include fresh implementer per task, brief/report artifacts, specification then quality review gates, fix loops, git-backed progress, and final whole-branch review; no truncation caveat.
   - Inventory: `coverage: complete` because the canonical directory listing was fully read; do not infer stage order or behavior from folder names; evidence strength and practicality are `low`; posture is `reference-only`.
   - Reducer matrix: same-hash resummarization preserves the `applied` edge, creates no pending edge, and leaves `routing_status: routed`; changed-hash exclusion marks the old pending edge `superseded`, creates no replacement edge, recomputes the old topic clean, and sets `routing_status: no-topic-match`.
5. All three named lanes are required. Before the matrix, confirm the configured transports with:

   ```bash
   omp models find gpt-5.6-sol
   omp models find grok-4.5
   grok -p "Reply with exactly: pong" \
     -m grok-4.5 \
     --reasoning-effort high \
     --output-format json \
     --yolo --no-auto-update \
     | jq -e -r 'select(.text == "pong") | .text'
   ```

   On a transport failure, preserve the raw error and exact command, verify the existing model/auth configuration once, and retry once without changing the prompt; do not substitute another model or harness, and do not initiate a new login automatically. A persistent failure blocks T2. Record the twelve-output comparison and any permitted qualitative differences in the execution log before deleting `/tmp/atlas-source-summary-quality/`.

#### T2 execution record — 2026-07-14

- Transport checks passed for OMP `openai-codex/gpt-5.6-sol` xhigh, OMP `xai-oauth/grok-4.5` xhigh, and Grok CLI `grok-4.5` high; the Grok `pong` smoke returned exactly `pong`.
- Fixture prompt bytes stayed unchanged across lanes and reruns. SHA-256: thin wrapper `97d5babb9055780dd82dd48d3f98719a222f718293b0776c39e5e66392ed0559`; long workflow `b25c1d5ca5810c85c9af2e62cc81af3db8e2f6b9ac5c5a3dbcedf1cb0aee50ca`; inventory `275e2d26091d4c9907dc279b04a4f4a54e58f67132be1054a3586bd64945ac3f`; reducer `e56bdf9ca171891eca1550a6115127c0393ecd0cfdb45356337400b788a170a9`.
- Transport corrections and later override:
  - OMP GPT long-workflow and inventory initially exhausted `--max-time 180` on both the primary run and one identical-prompt retry. The user explicitly approved raising only those ceilings to `--max-time 360`; later full-matrix reruns retained 180 seconds for thin/reducer and 360 seconds for long/inventory.
  - Grok CLI `0.2.101` treats built-in tool names as case-sensitive and splits local and HTTP reads. Lowercase `--tools read` exposed no reader; a direct smoke proved `Read` and `WebFetch`. The lane therefore used the read-only `Read,WebFetch` allowlist. No credential mutation, session resume, memory, subagent, shell, or write tool was used.
  - Final Grok CLI JSON outputs all exited successfully with nonempty `.text`, `.sessionId`, `.usage`, and `stopReason: EndTurn`; `num_turns` were 13, 11, 18, and 4 for thin, long, inventory, and reducer respectively.
- Two source-independent contract gaps were corrected without model-specific prompting:
  - `evidence_strength` now distinguishes substantive but thin primary claims (`medium`) from inventory-only name/existence evidence (`low`).
  - Canonical directory/index/listing payloads are explicitly non-recursive, and generated draft reports share the artifact's context-neutrality rule.
  - Each refinement triggered a complete twelve-output rerun. The final matrix below is the accepted post-refinement round; diagnostic earlier rounds were not used as replacement source evidence.

Rubric tuples are `coverage / confidence / evidence_strength / practicality / stability / reuse_value / recommended_posture`.

| Lane | Fixture | Final deterministic result | Qualitative observation |
|---|---|---|---|
| OMP GPT-5.6-Sol xhigh | Thin wrapper | `complete / high / medium / medium / stable / medium / reference-only`; hard checks pass | Most concise source-only draft; precise delegation boundary. |
| OMP Grok-4.5 xhigh | Thin wrapper | Same tuple; hard checks pass | Equivalent claims with a compact mode/identity report. |
| Grok CLI 4.5 high | Thin wrapper | Same tuple; hard checks pass | More operational preamble; no invented `/grilling` or `/domain-modeling` internals. |
| OMP GPT-5.6-Sol xhigh | Long workflow | `complete / high / high / high / stable / high / trial`; hard checks pass | Deepest proportional synthesis and clearest separation of source claims from caveats. |
| OMP Grok-4.5 xhigh | Long workflow | Same tuple; hard checks pass | More compressed while preserving every mandatory phase and prohibition. |
| Grok CLI 4.5 high | Long workflow | Same tuple; hard checks pass | More verbose operational framing; canonical 425-line workflow mechanics remain complete. |
| OMP GPT-5.6-Sol xhigh | Inventory | `complete / high / low / low / moving / medium / reference-only`; hard checks pass | Concise inventory with no recursive child evidence. |
| OMP Grok-4.5 xhigh | Inventory | Same tuple; hard checks pass | Name clusters are explicitly bounded as name-only inference. |
| Grok CLI 4.5 high | Inventory | Same tuple; hard checks pass | Most exhaustive name enumeration; child bodies and parent README remain separate sources. |
| OMP GPT-5.6-Sol xhigh | Reducer | Applied edge preserved; no pending clone; `routed`; old pending → `superseded`; no replacement; topic clean; `no-topic-match` | Clearest explicit before/after field table. |
| OMP Grok-4.5 xhigh | Reducer | Same transitions; hard checks pass | Equivalent concise reducer explanation. |
| Grok CLI 4.5 high | Reducer | Same transitions; hard checks pass | Equivalent side-by-side reduction with raw transport metadata retained until cleanup. |

- Shared hard checks passed: nine artifacts retained required sections, all nine had locator-backed evidence and source-specific Assessment notes, the exact context-leak regex returned no matches across all twelve outputs, all long-workflow outputs contained the fresh-implementer, brief/report, dual-review, fix-loop, git-progress, and final whole-branch mechanics, all inventory outputs stayed non-recursive, and all three reducer outputs agreed on the required transitions.
- Permitted quality differences were prose length, section depth, detail emphasis, and operational framing. Per the approved adjudication rule, OMP GPT-5.6-Sol xhigh is the preferred qualitative reference; no drafts were merged and no rule was added to imitate GPT prose.
- The fixture drafts are qualification evidence only. They were not written to `vault://atlas/`, no emitted Grok session was resumed, and none may supply facts to T3.

### T3. Regenerate workflow source sequences 5–35

1. Begin only after all three T2 lanes pass the hard contract and their twelve-output comparison is recorded. Execute before the original AI coding workflow plan resumes comparative synthesis. Read `vault://atlas/summaries/sources/MANIFEST.md` and select exactly source sequences `5` through `35`; this is the closed 31-artifact cohort: three repository roots, ten Matt pages, ten Superpowers pages, and eight Cursor pages. Capture `source_seq`, `source_id`, canonical URL, artifact path, content hash, route status, and edge IDs in `/tmp/atlas-source-summary-quality/before.tsv` for reconciliation.
2. Invoke `/atlas-source --resummarize <canonical-url>` separately in source-sequence order for all 31. The fetched source—not the old summary, current topic answer, or any plan requirements—is the sole factual input. Mutable repository roots may legitimately change; commit-pinned pages must retain canonical URLs.
3. Rewrite each artifact in place under `vault://atlas/summaries/sources/artifacts/2026/2026-07/` with source-specific TL;DR, Assessment notes/values, proportional sections, locator-backed evidence, specific caveats, routing rationale, and reuse cues. Remove every “T2 owns…,” “Selected explicitly for the AI coding workflow comparison,” “later comparison,” modal routing sentence, current plan/session reference, and cross-source adoption claim; retain a task/session term only when it is an attributed fact from the source.
4. Preserve `source_id`, `source_seq`, canonical URL, `first_seen`, `acquired_by`, `acquisition_run`, and artifact path. Update `last_checked`/`last_summarized` to execution date. If the complete readable payload hash matches, keep the manifest hash and same-hash edge identity; if it differs, apply the verifier-conditional changed-hash/supersession transition from T1.
5. Specifically repair the three truncated artifacts:
   - seq 21 `355dd83e50b9` (`subagent-driven-development`, previously 300/425 lines),
   - seq 22 `daeadbe9a0e0` (`test-driven-development`, previously 300/378 lines),
   - seq 23 `8b7f4f4ae6e3` (`systematic-debugging`, previously 300/303 lines).
   Fetch every line before claiming complete coverage; changed full-content hashes supersede old pending hashes, and replacement edges are created only when the bounded verifier includes the topic.
6. Re-run route-source for every regenerated source under the resummarize rules. Update same-hash pending edges in place; for changed hashes supersede stale pending rows before applying the verifier result. Replace modal routing boilerplate with evidence-specific reasons, recompute `ai-coding-workflow` dirty fields from current pending rows only, and do not synthesize that topic here while its original T2 remains unchecked.
7. Run `/atlas-audit --source-quality --source-seq 5-35`; fix every finding before proceeding.

### T4. Ingest thirteen immutable 12-Factor source pages

1. Keep existing repo-root source seq 1 (`e9eb05e2bf38`) and its applied edge unchanged; factor pages extend rather than replace that root evidence. Use the pinned repository commit `d20c728368bf9c189d6d7aab704744decb6ec0cc`; do not re-resolve to a later `main` because the plan intentionally records one reproducible evidence snapshot.
2. Invoke `/atlas-source` separately for these 13 canonical blob URLs, using `source_kind: docs`, the updated quality guide, and the next manifest sequence available at execution time (currently expected to start at 36):
   - `content/factor-01-natural-language-to-tool-calls.md`
   - `content/factor-02-own-your-prompts.md`
   - `content/factor-03-own-your-context-window.md`
   - `content/factor-04-tools-are-structured-outputs.md`
   - `content/factor-05-unify-execution-state.md`
   - `content/factor-06-launch-pause-resume.md`
   - `content/factor-07-contact-humans-with-tools.md`
   - `content/factor-08-own-your-control-flow.md`
   - `content/factor-09-compact-errors.md`
   - `content/factor-10-small-focused-agents.md`
   - `content/factor-11-trigger-from-anywhere.md`
   - `content/factor-12-stateless-reducer.md`
   - `content/appendix-13-pre-fetch.md`

   Prefix every path with `https://github.com/humanlayer/12-factor-agents/blob/d20c728368bf9c189d6d7aab704744decb6ec0cc/`.
3. Read each full Markdown page and every distinct embedded image/GIF that carries substantive evidence. Rewrite repository-owned `/blob/main/img/...` references to the same pinned commit for inspection/citation; keep GitHub user-attachment URLs unchanged. Use the image reader for still images; for an animated GIF, inspect its decoded frames or browser-rendered animation rather than inferring motion from the first frame. Record supporting media under `Links`, not as separate manifest rows. Factor 12 is diagram-dependent: inspect both `img/1c0-stateless-reducer.png` and `img/1c5-agent-foldl.png`; do not claim complete interpretive coverage if either cannot be decoded.
4. Produce one source-intrinsic artifact per page. Keep short factors proportionally concise, but capture their exact principle, mechanism, examples/diagrams, tradeoffs, and what the page does not establish. Treat Appendix 13 as an honorable mention in its title/caveat rather than silently presenting it as one of the core twelve. Paraphrase rather than retaining substantial source text; record that repository content/images are CC BY-SA 4.0 and code is Apache 2.0 when code excerpts are discussed.
5. Do not ingest the nine `factor-1-…` through `factor-9-…` redirect stubs, `content/brief-history-of-software.md`, packages, drafts, images as standalone sources, or other repository material.
6. Route factors 1–12 as expected direct candidates for `agentic-harness-architecture`; route Appendix 13 as expected supporting evidence. The bounded verifier remains authoritative and must give source-specific relation/impact/confidence reasons. Create deterministic pending edges and recompute the topic from `RELATIONS.md`; preserve seq 1's applied edge and source watermark until refresh.

   Expected verifier results are fixed unless fetched evidence directly contradicts them:

   | Page | Relation | Impact | Confidence |
   |---|---|---|---|
   | Factors 1–5 | direct | high | high |
   | Factor 6 | direct | medium | high |
   | Factor 7 | direct | medium | high |
   | Factor 8 | direct | high | high |
   | Factors 9–11 | direct | medium | high |
   | Factor 12 | direct | medium | high when both diagrams are decoded; medium if coverage is partial |
   | Appendix 13 | supporting | medium | high |

   A verifier result outside this table blocks routing until the artifact and source are re-read; do not silently choose another value.
7. Record all 13 canonical URLs, assigned sequences/IDs, artifact paths, hashes, media consulted, and edge IDs in the execution log before synthesis.

#### T3 execution record — 2026-07-14

- Captured pre-state for sequences 5–35 in `/tmp/atlas-source-summary-quality/before.tsv` (identity, path, hash, route status, edge IDs).
- Resummarized all 31 sources from newly fetched canonical payloads only; identity (`source_id`, `source_seq`, `canonical_url`, `first_seen`, `acquired_by`, `acquisition_run`, artifact path) preserved.
- Hash outcomes: **25 same-hash** (pinned skill pages; pending edges updated in place) and **6 changed-hash** with old pending edges superseded and verifier-included current-hash pending edges created:
  - seq 5–6 mutable repository READMEs
  - seq 7 directory listing (normalized complete listing payload)
  - seq 21–23 full-payload repairs for previously truncated Superpowers skills (`subagent-driven-development`, `test-driven-development`, `systematic-debugging`)
- All 31 route to `ai-coding-workflow` as `pending`; `ai-coding-workflow` dirty fields recomputed from `RELATIONS.md` (dirty count 31, newest pending seq 35). No topic synthesis performed.
- `/atlas-audit --source-quality --source-seq 5-35`: clean (zero context-leak, coverage-honesty, modal-note, evidence-locator, relation, or dirty-cache findings).

#### T4 execution record — 2026-07-14

- Left seq 1 (`e9eb05e2bf38`) and its applied harness edge unchanged.
- Ingested 13 pinned pages at commit `d20c728368bf9c189d6d7aab704744decb6ec0cc` as sequences **36–48** (`source_kind: docs`).

| Seq | Source ID | Page | Edge ID | Route |
|---:|---|---|---|---|
| 36 | `0fa2db7aeb31` | factor-01-natural-language-to-tool-calls | `edge--0fa2db7aeb31--agentic-harness-architecture--` + hash8 | direct/high/high |
| 37 | `149814f21669` | factor-02-own-your-prompts | `edge--149814f21669--agentic-harness-architecture--` + hash8 | direct/high/high |
| 38 | `722462e48754` | factor-03-own-your-context-window | `edge--722462e48754--agentic-harness-architecture--` + hash8 | direct/high/high |
| 39 | `4b9eae14bf0b` | factor-04-tools-are-structured-outputs | `edge--4b9eae14bf0b--agentic-harness-architecture--` + hash8 | direct/high/high |
| 40 | `f06e2fbdc39d` | factor-05-unify-execution-state | `edge--f06e2fbdc39d--agentic-harness-architecture--` + hash8 | direct/high/high |
| 41 | `24ad3be119e0` | factor-06-launch-pause-resume | `edge--24ad3be119e0--agentic-harness-architecture--` + hash8 | direct/medium/high |
| 42 | `c22b807f706b` | factor-07-contact-humans-with-tools | `edge--c22b807f706b--agentic-harness-architecture--` + hash8 | direct/medium/high |
| 43 | `ae89d8448e80` | factor-08-own-your-control-flow | `edge--ae89d8448e80--agentic-harness-architecture--` + hash8 | direct/high/high |
| 44 | `dbc175af55bb` | factor-09-compact-errors | `edge--dbc175af55bb--agentic-harness-architecture--` + hash8 | direct/medium/high |
| 45 | `107ec74f87db` | factor-10-small-focused-agents | `edge--107ec74f87db--agentic-harness-architecture--` + hash8 | direct/medium/high |
| 46 | `e385c2e2611b` | factor-11-trigger-from-anywhere | `edge--e385c2e2611b--agentic-harness-architecture--` + hash8 | direct/medium/high |
| 47 | `2cb6ae348d5f` | factor-12-stateless-reducer | `edge--2cb6ae348d5f--agentic-harness-architecture--` + hash8 | direct/medium/high |
| 48 | `9df0d5523773` | appendix-13-pre-fetch | `edge--9df0d5523773--agentic-harness-architecture--` + hash8 | supporting/medium/high |

- Full IDs, hashes, artifact paths, and media lists: `/tmp/atlas-source-summary-quality/meta/t4-applied.json`.
- Media: repository images/GIFs inspected at the pinned commit; user-attachment URLs kept unchanged. Factor 9 markdown names `195-factor-09-errors.gif` while the repo file is `195-factor-9-errors.gif` (fetched/inspected; noted in artifact). Factor 12 both diagrams decoded (`1c0-stateless-reducer.png`, `1c5-agent-foldl.png`).
- No redirect stubs or `brief-history-of-software.md` ingested.
- `agentic-harness-architecture` dirty count 13 (pending factor edges only); source watermark remains 4; seq 1 applied edge preserved.
- `/atlas-audit --source-quality` for the 13 factor source IDs: clean. `python3 scripts/atlas-instance.py check` → `check OK`.

### T5. Refresh affected research and verify integrity

1. After all T3 routing is reconciled and all 13 factor edges are pending, invoke `/atlas-refresh` for `agentic-harness-architecture` and apply every current pending edge for the topic. If the factor edges are the only pending set, create pass `12-factor-agent-factor-coverage`, keep `coverage_state: partial` and confidence `medium`, retain the evidence table in `INDEX.md`, and finish with 17 distinct applied sources. If T3 legitimately added other pending evidence to this topic, create pass `source-quality-and-12-factor-coverage`, apply that evidence in the same transition, recompute coverage/confidence from the expanded evidence rather than forcing the expected values, and split the evidence table only if the documented threshold is actually exceeded. In both branches, update the evidence map/current answer and close the explicit gap that detailed factor pages were not materialized.
2. Handle `ai-coding-workflow` according to its original plan state without inventing a second synthesis:
   - If `.agents/plans/2026-07-13-2349_ai-coding-workflow.md` T2 is still unchecked, leave the topic dirty for that task's required comparison/refresh.
   - If T2 is already complete, inspect the post-regeneration pending cache. When pending replacements or newly supported edges exist, run one dated vault-only quality-refresh pass, preserve accepted decisions while updating evidence citations, and finish `current`. When no pending edge exists, verify the topic remained `current` and create no empty pass.
3. Run `/atlas-audit --source-quality --source-seq 5-35`, then run the same audit with one repeatable `--source-id` argument for each of the 13 new factor IDs recorded in T4. Expected: zero context-leak, coverage-honesty, modal-note, evidence-locator, manifest, relation, or dirty-cache findings in the explicit 44-artifact set; do not widen this quality audit to unrelated source rows.
4. Re-read all 44 target artifacts (31 regenerated plus 13 new) and verify frontmatter/header agreement, source-local evidence, source-specific Assessment/Routing notes, canonical links, and media caveats. Compare the 31-row post-state with `/tmp/atlas-source-summary-quality/before.tsv`: identity/sequence/path changes are forbidden; hash and edge changes must correspond only to complete-payload or mutable-source changes, old pending rows must be superseded, and new edges must match included verifier results.
5. From `/Users/kim/Desktop/ng3/atlas/app`, run:

   ```bash
   python3 scripts/atlas-instance.py check
   ```

   Expected output includes `check OK` and instance `atlas`.
6. Use the built-in `grep` tool over the explicit 44 target artifact paths with `\bT[0-9]+\b|this (task|plan|conversation|comparison)|selected explicitly for|owns adoption|future Atlas workflow`. Expected: no generated-context matches; a clearly source-attributed verbatim match is reviewed rather than mechanically rewritten.
7. Confirm `agentic-harness-architecture` is `current`, has no pending edges, includes the 13 factor artifacts in its applied evidence, and retains the original seq 1 provenance. Confirm `ai-coding-workflow` state matches step 2. Remove `/tmp/atlas-source-summary-quality/` and its reconciliation ledger only after all checks pass; leave no smoke sources, fixture rows, or temporary vault artifacts.

## Critical files & anchors

- `.agents/ARCHITECTURE.md` — framework invariants and source-ingestion mode; owns the explicit-resummarization event boundary.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — source identity/hash, relation transitions, and dirty recomputation that regeneration must preserve.
- `.agents/skills/atlas-core/assets/source-summary-template.md` — copied artifact shape and flexible section guidance.
- `.agents/skills/atlas-source/SKILL.md` — sole source-summary creation path; `atlas-acquire` already delegates here.
- `vault://atlas/summaries/sources/MANIFEST.md` — authoritative cohort, dedupe, sequence, canonical URL, hash, and artifact-path ledger.
- `.agents/skills/atlas-core/assets/source-summary-quality-guide.md` — model-neutral evidence boundary, rubric, drafting, and self-check procedure.
- `.agents/skills/atlas-audit/SKILL.md` — read-only quality mode and exact cohort selectors.
- `vault://atlas/summaries/registry/RELATIONS.md` and `TOPICS.md` — relation status and denormalized dirty-state reconciliation.

## Verification

- Product behavior: three source shapes plus the reducer matrix run through exactly the OMP `openai-codex/gpt-5.6-sol` xhigh, OMP `xai-oauth/grok-4.5` xhigh, and Grok CLI `grok-4.5` high-effort lanes, producing twelve contract-conformant outputs with equivalent factual coverage and state transitions but no identical-prose requirement; qualitative differences use the GPT output as the preferred reference without template overfitting.
- Regeneration behavior: source sequences 5–35 retain identity/path, contain no generated campaign/task language, have honest full-read coverage, source-specific Assessment/Routing notes, and locator-backed evidence; the prior 300-line truncation mismatches disappear.
- New evidence behavior: exactly 13 new HumanLayer page artifacts exist for the listed pinned URLs; factor 12 includes both diagrams; redirect stubs and `brief-history-of-software.md` have no manifest rows.
- Reducer behavior: changed hashes supersede old pending rows and create replacements only for included verifier results; same-hash resummarization does not duplicate or reopen applied edges; routing status reflects current-hash relations; dirty fields equal `RELATIONS.md`; factor refresh returns `agentic-harness-architecture` to `current`.
- Integrity: both explicit-scope `/atlas-audit --source-quality` runs report clean, `python3 scripts/atlas-instance.py check` returns `check OK`, all 44 target artifacts pass direct inspection, and all temporary evaluation/reconciliation artifacts are removed.

## Assumptions & contingencies

- Keep source-summary schema version 1 and `recommended_posture`; the defect is context-coupled scoring/notes, not a missing field. The new rubric defines posture as source curation so no all-artifact schema migration is needed.
- Execute this plan before the original AI coding workflow T2 when possible. If that task already ran, the T5 quality-refresh branch prevents stale current answers without rewriting accepted decisions.
- The 12-Factor snapshot is intentionally pinned to `d20c728368bf9c189d6d7aab704744decb6ec0cc`; later upstream commits require a separate normal source refresh, not silent substitution during this execution.
- The current next free source sequence is 36, but the manifest is authoritative. If other sources are added first, allocate the then-next 13 monotonic sequences; never renumber existing rows.
- If essential linked media cannot be fetched after reader-mode, raw, and image-tool attempts, keep the page artifact with `coverage: partial`, name the inaccessible asset, and do not infer its visual claim. Factor 12 remains incomplete until both repository diagrams are inspected.
- No persistent eval runner exists in this product today. Use temporary cross-model and cross-harness outputs for this plan; do not preempt the separate pending Atlas evaluation-runner plan by adding another runner or registry backend.
- The two Grok lanes intentionally compare harness transport as well as model behavior; do not collapse them into one result. Grok CLI may emit a persisted `sessionId`, but fixture runs remain single-turn and are never resumed.
- The GPT preference adjudicates only qualitative quality after hard contracts pass. It does not relax deterministic evidence, coverage, rubric, or reducer requirements for either Grok lane and does not make GPT fixture prose a source for later artifacts.

## T5 completion record — 2026-07-15

### Post-completion review and repairs

- The strengthened review found that the original T3/T4 clean result did not cover canonical relation-table placement, exact relation-reason provenance, context-neutral calibration, or sufficiently strict concision and adoption coupling.
- Repaired `RELATIONS.md` into one canonical table, preserved all 54 historical/current rows, and normalized every Notes cell to `Verifier: <source-local locator> — <source-specific claim> [relation=<row relation>; impact=<row impact>]`.
- Same-hash resummarization repaired the reviewed cohort (sequences 9, 13–35, and 44) without changing source identity, sequence, canonical URL, artifact path, or content hash. The final exact sequence 5–48 audit additionally repaired source-supported defects in 5, 8, 10, 12, 19, 20, 28, 36–43, and 45–48.
- Sequence 9 now has `complete/high/medium/medium/stable/medium/reference-only`; sequence 21 has `complete/high/high/high/stable/high/trial`; every sequence 13–35 artifact is `stable`.
- The adoption gate moved sequences 40, 45, and 48 to `trial` because their actionable guidance still lacks measured outcomes or a required threshold. Unsupported licensing, authorship, state-machine, and cross-source claims were removed.
- Factor 9 now stores only the fetched pinned `img/195-factor-9-errors.gif` asset; the broken reconstructed `img/195-factor-09-errors.gif` URL is absent.

### Refresh result

- Created `summaries/research/agent-systems/harness/topics/agentic-harness-architecture/passes/2026-07-15--factor-evidence-refresh.md`.
- Applied exactly these thirteen edges in that pass:
  - `edge--0fa2db7aeb31--agentic-harness-architecture--870254f6`
  - `edge--149814f21669--agentic-harness-architecture--74f565ec`
  - `edge--722462e48754--agentic-harness-architecture--340e5734`
  - `edge--4b9eae14bf0b--agentic-harness-architecture--fcfbb2bc`
  - `edge--f06e2fbdc39d--agentic-harness-architecture--57ab26c6`
  - `edge--24ad3be119e0--agentic-harness-architecture--b6574ff3`
  - `edge--c22b807f706b--agentic-harness-architecture--a956a083`
  - `edge--ae89d8448e80--agentic-harness-architecture--59e95822`
  - `edge--dbc175af55bb--agentic-harness-architecture--2488387b`
  - `edge--107ec74f87db--agentic-harness-architecture--3e0f0b57`
  - `edge--e385c2e2611b--agentic-harness-architecture--a62d37e5`
  - `edge--2cb6ae348d5f--agentic-harness-architecture--e10509eb`
  - `edge--9df0d5523773--agentic-harness-architecture--f2ff7379`
- `agentic-harness-architecture` is `current`, dirty count 0, no pending IDs, last synthesized `2026-07-15`, source watermark 48. The initial sequence 1 edge and 2026-07-13 pass remain applied provenance.
- `ai-coding-workflow` remains `dirty` with the unchanged 31 sequence 5–35 pending edges, newest pending sequence 35, and source watermark 0. Its separate plan was not advanced.

### Final verification

- Provider-neutral calibration: 24/24 cases passed for OMP `openai-codex/gpt-5.6-sol` and Grok CLI 0.2.101 `grok-4.5`; repeated validator output was byte-identical (`23410d5b…`).
- Exact source-quality cohort: 44 artifacts (sequences 5–48), zero semantic or deterministic blockers; repeated direct CLI aggregate digest `9fe4b1a6…`.
- Registry audit: 48 contiguous manifest rows, 54 unique relation rows, zero relation-reason mismatches, and clean reducer output; repeated state-validator output `{"findings":[],"ok":true}` with digest `23410d5b…`.
- Focused suites: 38 tests passed.
- `python3 scripts/atlas-instance.py check --name atlas`: `check OK`, instance `atlas`, one product-owned entry, eight seed-once templates.
- Answer smoke: `agentic-harness-architecture` passed the current-state gate from the refreshed `INDEX.md`; `ai-coding-workflow` halted dirty with 31 pending edge IDs.

## Completion summary

Completed 2026-07-15T05:51:14Z. Source summaries, calibration, deterministic reducers, relation provenance, and the detailed factor refresh now satisfy the strengthened product contract. T5 applied only the thirteen factor edges, preserved the original topic provenance, and left the separate AI coding workflow synthesis pending.
