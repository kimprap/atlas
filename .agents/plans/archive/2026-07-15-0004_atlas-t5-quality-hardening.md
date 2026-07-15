# Atlas T5 Quality Hardening and Completion Plan

**Datetime**: 2026-07-15-0004
**Scope**: Harden Atlas contracts, repo-local agent surfaces, portable Python execution, source-quality gates, and living-state reducers; repair the reviewed T3/T4 defects; then execute and verify the existing T5 refresh.
**Summary**: Isolate source drafting behind a context-neutral evidence envelope; move registry and cache transitions behind a provider-neutral reducer; add deterministic source-quality validation and cross-harness conformance gates; repair the exact reviewed cohort; apply only the thirteen factor edges to `agentic-harness-architecture`; and complete the active source-summary-quality plan only after every strengthened gate passes.
**Status**: COMPLETE

## Context

The T3/T4 review established that source comprehension was mostly strong while control-plane quality was not. The current state is unsafe for T5 because:

- `vault://atlas/summaries/registry/RELATIONS.md:62-74` contains the thirteen T4 rows after the canonical table and its schema instructions. `TOPICS.md` counted those lines as pending anyway, so the cache and the Markdown document disagree about what the relation table contains.
- Source sequences 13-35 use immutable commit-pinned canonical URLs but record `stability: moving`.
- The two exact T2 fixtures regressed: sequence 9 (`grill-with-docs`) changed `evidence_strength` from `medium` to `low`; sequence 21 (`subagent-driven-development`) changed `stability / recommended_posture` from `stable / trial` to `moving / adopt`.
- Current T3/T4 relation Notes for sequences 5-48 preserve candidate lists, not the bounded verifier’s source-specific reason for inclusion, relation, and impact.
- Factor 9 records the nonexistent `img/195-factor-09-errors.gif`; the inspected pinned asset is `img/195-factor-9-errors.gif`.
- `python3 scripts/atlas-instance.py check` returned success because it checks provision/sync shape, not living registry structure or cache consistency.

The review also established what should not be redone: all 44 source identities and legal hash transitions passed; all required source sections exist; source-grounded extraction is strong; the 13 factor sources are complete and materially useful; generated-context leakage was absent; and the thirteen pending factor edges are the correct T5 input once their registry placement and provenance are repaired.

The quality target is broader than registry repair. Atlas must keep one canonical policy surface while remaining executable from different agent harnesses and SOTA models. The current product already has a strong source-only evidence rule, but the workflow still mixes source drafting with live taxonomy/routing context, and the earlier plan did not make concision, script portability, repo-local harness adapters, or an executable source-quality validator explicit.

The current checkout also has transport drift: `AGENTS.md` and the Cursor adapters resolve to the product `.agents/` tree, while `.grok/skills` and `.grok/rules` resolve to host-global configuration. A portable product cannot depend on that workstation state. Claude Code also needs thin project adapters to discover the same canonical skills/rules; no policy body may be copied into an adapter.

## Decisions

1. **Separate semantic judgment from state mutation.** The model may produce a source assessment, a context-neutral semantic draft, and bounded routing proposals. Pure validators and reducers own accepted shapes, Markdown row placement, edge IDs, legal relation transitions, and derived topic-cache values.
2. **Define determinism honestly.** Atlas guarantees deterministic state transitions, validation findings, identities, ordering, and pass/fail gates for a given input. It does not require identical prose from different SOTA models. A harness/model pair is write-enabled only when it passes the same provider-neutral conformance cases; failure halts mutation rather than selecting a provider-specific prompt.
3. **Make source drafting context-neutral by contract.** The semantic draft may use only the newly fetched canonical payload, inspected source media, exact retrieval bounds, immutable identity/retrieval metadata required by the artifact, and product-owned template/rubric versions. Old artifact prose, sibling artifacts, topic answers/passes, candidate-topic rows, relation notes, plans/tasks/session text, the current request, working-tree context, and provider/model identity are not evidence or draft inputs. Taxonomy normalization and routing run only after the draft passes.
4. **Do not require a harness-specific isolation primitive.** A fresh/forked model context is desirable when a host provides it, but the portable contract is the typed evidence envelope plus output/audit invariants. The same artifact and metamorphic context-perturbation checks apply when literal context-window isolation is unavailable.
5. **Keep storage connector-neutral.** Reducers and validators consume and return document text plus structured JSON. They never resolve `vault://`, open a local vault path, call a model, or write storage directly; each harness continues to use its active connector for I/O.
6. **Use scripts for repeated deterministic work, not shell orchestration.** Reference implementations use dependency-free Python 3 modules with JSON input/output. Bash may invoke them but contains no parsing, mutation, or business rules. Conformant ports in another runtime must pass the same byte-level fixtures.
7. **Use hard gates, not provider-specific prompts.** Static calibration cases, deterministic validators, and bounded semantic audits use the same expected outcomes in OMP, Grok, Codex, Claude Code, Cursor, CI, or a serverless runtime. Harness/model metadata belongs only in execution reports.
8. **Keep one canonical agent surface.** `.agents/ARCHITECTURE.md`, `atlas-core`, entry skills, rules, and command stubs own policy. `.agents/AGENTS.md` remains a concise always-loaded map. Host directories contain only symlinks or thin dispatch adapters to that surface; they never duplicate policy or depend on host-global Atlas files.
9. **Optimize for minimum sufficient summaries, not fixed length.** Every paragraph or bullet must add a distinct source-supported claim, mechanism, example, limitation, or source-intrinsic reuse cue. Exact duplicates, stock advice, campaign rationale, and empty boilerplate fail; no universal word, token, or bullet cap is introduced.
10. **Treat immutable evidence as immutable.** A GitHub blob or repository object pinned to a full commit is `stable` for this rubric even when the upstream project continues changing. Payload stability is not project release cadence.
11. **Do not mass-edit recommendations.** Correct stability mechanically, but re-evaluate `recommended_posture` source by source under the strengthened adoption gate. Sequence 21 is explicitly `trial`; the other sequence 13-35 postures must be justified from their own evidence and caveats.
12. **Do not broaden T5.** T5 applies only the thirteen `agentic-harness-architecture` factor edges. The 31 `ai-coding-workflow` edges remain pending for the separate AI-coding-workflow plan.
13. **Keep schema and command churn bounded.** No registry column or source-artifact frontmatter key changes. Source drafting and post-draft Atlas annotations become explicit phases within schema version 1. Command bodies remain thin; the seed-once scaffold remains empty-state only.
14. **Use one lean semantic acceptance checklist, not another scoring rubric.** The existing bounded post-generation audit answers seven binary, outcome-focused questions. It has no weighted score, prose matching, fixed length/citation count, or cumulative threshold. One failed item blocks the draft and names only the dimension to revise.

## Research Basis

- The [Agent Skills specification](https://agentskills.io/specification) treats instructions, scripts, references, and assets as one portable package and recommends progressive disclosure.
- OpenAI’s [skill-eval guidance](https://developers.openai.com/blog/eval-skills) separates outcome, process, style, and efficiency goals and combines deterministic checks with structured qualitative grading.
- Anthropic’s [agent-eval guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) recommends deterministic graders where possible, model graders where semantics require them, isolated trials, balanced positive/negative cases, and outcome grading over brittle tool-path assertions.
- Viv’s [harness-engineering notes](https://x.com/Vtrivedy10/status/2068039292400566719) emphasize model–harness–task fit, eval-driven iteration, and clean context per subtask. Atlas therefore earns write support through one conformance contract rather than assuming SOTA models are fungible.

## Tasks

- [x] T1. Define product agent-surface and deterministic reducer invariants
  - completed 2026-07-15-1121
- [x] T2. Harden context-neutral quality provenance concision and calibration
  - completed 2026-07-15-1121
- [x] T3. Repair reviewed source artifacts and relation state
  - completed 2026-07-15-1148
- [x] T4. Pass the strengthened pre-refresh quality gate
  - completed 2026-07-15-1234
- [x] T5. Apply factor evidence and complete topic refresh
  - completed 2026-07-15-1245
- [x] T6. Reconcile final state and close repository plan
  - completed 2026-07-15-1254

## Approach

### T1. Define product, agent-surface, and deterministic reducer invariants

#### Product and agent contract order

1. Update `.agents/ARCHITECTURE.md` first, under `## Reducer model`, `## Source identity and routing`, and `## Freshness model`:
   - model output is a typed proposal, not a Markdown mutation;
   - each registry owns exactly one canonical table with one exact header/separator and one contiguous data-row region;
   - schema-shaped rows outside that region invalidate the registry and cannot contribute to routing or freshness;
   - route/refresh/index operations validate the complete input state, reduce one explicit event, validate the complete candidate state, and only then expose documents for connector writes;
   - `RELATIONS.md` remains canonical and `TOPICS.md` remains derived;
   - connector adapters own reads/writes only; reducer logic is provider-, harness-, and storage-neutral.
   - source semantic drafting consumes an explicit source-only envelope; classification and routing are later phases and never become factual evidence for the draft;
   - structural determinism and semantic variability are separate: candidate prose may vary, accepted state and gates may not.
2. Update `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` to make those invariants executable and unambiguous:
   - define canonical table bounds as header + separator + immediately contiguous rows, ending at the first non-row line;
   - reject a second matching header, wrong cell count, schema-shaped orphan rows, duplicate primary IDs, invalid enums, malformed source IDs/hashes, invalid deterministic edge IDs, and contradictory applied/pending fields;
   - define topic derivation exactly: pending IDs stable-sorted by source sequence, dirty count from pending rows, newest pending sequence from the same set, and source watermark as the highest applied source sequence;
   - require current-hash manifest/relation consistency and require `Applied in pass` only for `applied` rows;
   - define the machine-checkable relation reason shape: `Verifier: <source-local locator> — <source-specific claim> [relation=<row relation>; impact=<row impact>]`.
3. Align the repo-local agent and transport surfaces after the canonical contract:
   - update `.agents/AGENTS.md` only as a concise map: name the reference reducer and quality-validator scripts; keep detailed rules in architecture, `atlas-core`, and owning skills;
   - update `.agents/rules/atlas-reducer-discipline.md` so freestyle source/registry mutation must load the matching Atlas skill and use validated script output; prohibit model-authored table placement, cache arithmetic, and source-quality fallback writes;
   - leave `.agents/rules/atlas-boundaries.md` and `.agents/rules/atlas-skill-surface.md` unchanged; their existing ownership, logical-vault, change-order, and thin-adapter rules already match the target design;
   - keep top-level `AGENTS.md` and existing Cursor adapters pointed at `.agents/`;
   - repoint `.grok/skills` and `.grok/rules` from host-global configuration to `../.agents/skills` and `../.agents/rules`;
   - add `CLAUDE.md -> .agents/AGENTS.md`; add per-entry symlinks under `.claude/skills/` and per-rule symlinks under `.claude/rules/` to the canonical `.agents/` files;
   - Codex and OMP continue using native `.agents/`/`AGENTS.md` discovery; `.agents/commands/atlas-*.md` bodies remain unchanged because they already forward raw arguments to owning skills.

#### Reducer implementation

4. Add `scripts/atlas_state.py` as a deep, pure-text module plus CLI. Its public surface is:
   - `validate_documents(manifest_text, topics_text, relations_text) -> list[Finding]`;
   - `reduce_event(documents, event) -> ReductionResult`;
   - `audit_instance(instance_root) -> list[Finding]` as the local-filesystem adapter used only by provision checks.
   - Python 3 standard library only; no Bash parsing, third-party package, network, connector, model call, random ID, implicit current time, locale-dependent comparison, environment-dependent policy, or current-working-directory assumption;
   - every date/time and identity enters through validated input; sorting and JSON key order are explicit;
   - preserve the exact UTF-8 input newline convention and final-newline state; compute precondition hashes from the exact UTF-8 input bytes;
   - emit machine JSON on stdout, diagnostics on stderr, documented nonzero exit codes on failure, bounded output, and useful `--help`;
   - make validation, route upsert, and repair events idempotent where the state transition permits it.
5. The CLI accepts a versioned JSON bundle from `--input <path|->`. The bundle contains logical path + full text for `manifest`, `topics`, and `relations`, plus one optional event. It emits JSON only:
   - `python3 scripts/atlas_state.py validate --input <bundle>` returns `ok` and normalized findings (`code`, logical path, line/row identifier, detail), never replacement documents;
   - `python3 scripts/atlas_state.py reduce --input <bundle>` returns `ok`, input-document SHA-256 preconditions, replacement text for only changed documents, derived topic/source statuses, and the applied edge IDs;
   - a connector may persist reducer output only while all current document hashes still equal those preconditions. On mismatch it must re-read and re-reduce.
6. Define event payloads exactly in `markdown-registry-contracts.md` and validate unknown/missing fields:
   - `route-upsert`: `{type, source_id, content_hash, checked_on, outcome, edges[]}` where each included edge supplies `{topic_id, relation, impact, confidence, reason}`; derive sequence/path/edge ID from current manifest state, insert or update inside the table, preserve exact applied history, supersede only old-hash pending edges, update manifest route status, and recompute affected topics;
   - `refresh-start`: `{type, topic_id, edge_ids, started_at}` where `edge_ids` must equal the complete pending set for that topic; set `refreshing` without changing relation status;
   - `refresh-complete`: `{type, topic_id, edge_ids, pass_path, completed_on}`; require the same complete set, apply it, set pass provenance, and return `current` only when no pending rows remain;
   - `refresh-fail`: `{type, topic_id, reason}`; preserve pending edges and set the topic to `blocked`;
   - `repair-table-placement`: `{type, registry}`; rehome only unambiguous schema-valid orphan rows with unique nonconflicting IDs;
   - `repair-relation-notes`: `{type, repairs:[{edge_id, reason}]}`; update Notes only, preserving IDs, tuples, status, creation dates, and applied-pass provenance.
7. Normal reductions require a fully valid input state. `repair-table-placement` is the sole exception: it may proceed only when every input finding is the matching orphan-row diagnostic; any malformed, duplicate, or conflicting row still blocks with no output.
8. Preserve all non-table prose byte-for-byte. The reducer may replace only canonical table data rows; it must not rewrite schema instructions or user-owned prose.
   - `scripts/atlas_state.py` is the reference implementation. Another runtime may use a conformant port only if it passes the same event fixtures byte-for-byte; when neither implementation is available, mutating Atlas workflows halt rather than fall back to model-authored table edits.
9. Import `audit_instance` from `scripts/atlas_state.py` in `scripts/atlas-instance.py`. Make the existing `check` command fail for living registry errors instead of adding an opt-in flag. Keep provision/product-owned/scaffold checks unchanged.

#### Workflow integration

10. Update the owning skills, not command stubs:
   - `.agents/skills/atlas-route/SKILL.md`: produce structured verifier decisions, call `route-upsert`, and use only validated reducer output for relation/manifest/topic writes;
   - `.agents/skills/atlas-refresh/SKILL.md`: validate before `refresh-start`, require the exact pending set, and use `refresh-complete` or `refresh-fail` for final relation/cache transitions;
   - `.agents/skills/atlas-index/SKILL.md`: use explicit repair events for registry repair and reject ambiguous or taxonomy-changing fixes;
   - `.agents/skills/atlas-audit/SKILL.md`: report reducer diagnostic codes and never count orphan rows as canonical state.
11. Add `tests/test_atlas_state.py`, `tests/test_atlas_harness_surface.py`, and focused extensions to `tests/test_atlas_instance.py` with isolated temporary instances. Required behavioral fixtures:
   - the reviewed T4 shape (valid-looking rows after prose) fails with `RELATION_ROW_OUTSIDE_TABLE`;
   - `repair-table-placement` moves all and only valid orphan rows before the table terminator;
   - route insertion lands inside the table and recomputes stable pending order/cache values;
   - current-hash applied edges are not reopened;
   - changed-hash routing supersedes only old pending edges;
   - refresh rejects a partial pending set, supports start/complete, and leaves pending + `blocked` on failure;
   - applied pass paths, edge IDs, enums, duplicates, source identities, and topic cache mismatches fail deterministically;
   - empty scaffold registries remain valid and `atlas-instance.py check` still passes a newly created instance.
   - LF/CRLF input, final-newline preservation, stable JSON output, input-hash preconditions, idempotent events, and unknown fields behave identically across repeated runs;
   - every repo-local host adapter resolves inside this package’s `.agents/` tree, no host-global Atlas surface wins, each entry skill has its matching command, and command bodies remain thin.

### T2. Harden context-neutral quality, provenance, concision, and calibration

1. Update `.agents/skills/atlas-core/assets/source-summary-quality-guide.md`:
   - **semantic draft envelope**: newly fetched canonical payload, canonical URL, inspected pinned media, retrieval bounds, immutable identity/acquisition fields needed to render the artifact, and product-owned template/rubric versions only;
   - **forbidden draft context**: old artifact prose, sibling artifacts, topic indexes/passes, relation rows, candidate-topic definitions, campaign/request/plan/session text, working-tree or repository content, and provider/model identity;
   - the identity resolver may read the exact manifest row needed for dedupe/resummarization, but it passes only immutable identity/provenance fields into the draft envelope;
   - classification normalization and bounded routing may read `VOCAB.md`, `TOPICS.md`, and `RELATIONS.md` only after the semantic draft passes; they may annotate Atlas metadata but may not rewrite source claims;
   - **concision**: retain the minimum sufficient distinct claims/mechanics/examples/limits; prohibit exact duplicates, paraphrased filler, stock advice, empty-section boilerplate, and campaign rationale; use no fixed word/token/bullet limit;
   - **lean acceptance checklist**: run once after deterministic validation and use it as the bounded semantic audit, not as an additional model pass. Return exactly seven stable items:
     1. `evidence-boundary` — every claim stays within the fetched payload/media and missing bounds are explicit;
     2. `primary-contribution` — the source’s contribution, scope, conditions, and attributed assertions are faithfully preserved;
     3. `source-support` — consequential concrete claims use source-local support when the source exposes it;
     4. `limits-uncertainty` — material caveats, conflicts, fetch gaps, and uncertainty are retained;
     5. `context-neutrality` — no old artifact, topic, plan, repository, request, campaign, provider, or model context enters the semantic draft;
     6. `assessment-coherence` — the assessment tuple and short notes agree with the evidence and rubric;
     7. `proportionality` — sections add distinct information without filler or needless repetition while preserving all material evidence;
   - each item returns only `{id, status: pass|fail, evidence}`. `evidence` is one short source/draft locator or failure reason; its wording is not graded. No `n/a` state is needed because “when present/available” is built into the item definitions. Any `fail` rejects the draft; revise the failed dimension and rerun the same checklist.
   - **evidence strength**: a thin primary source that directly and authoritatively establishes one bounded operational mechanism is normally `medium`; `low` is inventory, naming-only, illustrative, or indirect evidence; length alone is never the deciding factor;
   - **stability**: score the canonical payload and supported principle, not the upstream project’s activity; a full-commit GitHub blob/tree/API object is an immutable snapshot and therefore `stable`;
   - **recommended posture**: `adopt` requires `evidence_strength: high`, `practicality: high`, `stability: stable`, and no unresolved caveat that requires local validation; otherwise use `trial`, `watch`, or `reference-only` according to the existing rubric;
   - **routing reason**: an included result must preserve a source-local locator, a source-specific claim, and explicit justification for the selected relation and impact. Candidate-list boilerplate is invalid.
2. Update `.agents/skills/atlas-core/assets/source-summary-template.md` without changing schema version 1: identify source identity/retrieval metadata, Assessment, TL;DR, Key points, Mechanics, Evidence, Caveats, Reuse cues, and source/media Links as the context-neutral semantic draft; identify canonical taxonomy, route status/date, and `## Routing notes` as post-draft Atlas annotations; prohibit topic/repo/vault context in semantic sections; ask for payload/pin stability; and use the exact relation-reason shape in the managed routing annotation.
3. Add `scripts/atlas_quality.py` as the dependency-free deterministic validator used by `atlas-source` and `atlas-audit`:
   - `validate_summary(artifact_text, evidence_bundle) -> list[Finding]` checks schema/frontmatter, required sections, enums and adoption coupling, unresolved placeholders, exact normalized duplicates, forbidden generated/repository context in semantic sections, source/media URL membership in the envelope, source-local locator shape, and the semantic/routing boundary;
   - `validate_calibration(fixture_text, response_text) -> list[Finding]` exact-compares structured assessment/routing/audit responses to the versioned fixture contract;
   - CLI modes `validate-summary` and `validate-calibration` use the same dependency-free Python, UTF-8, structured stdout/stderr, stable ordering, and exit-code contract as `atlas_state.py`;
   - deterministic checks do not pretend to judge semantic faithfulness or paraphrased redundancy; those remain bounded model-audit dimensions calibrated by exact fixtures.
   - exact-validate the checklist’s seven IDs, order, `pass|fail` statuses, uniqueness, and nonempty evidence field. Do not score or compare evidence-note prose, and do not add a second checklist-specific script or artifact.
4. Add `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` as dependency-free, versioned fixtures. Use top-level `assessment_cases`, `summary_cases`, `routing_cases`, and `negative_audit_cases`; every case has a stable `id`, bounded evidence text, and an objective `expected` object:
   - thin primary wrapper (`grill-with-docs`): `complete / high / medium / medium / stable / medium / reference-only` for coverage, confidence, evidence strength, practicality, stability, reuse, and posture;
   - comprehensive operational controller (`subagent-driven-development`): `complete / high / high / high / stable / high / trial`;
   - commit-pinned source in an actively moving repository: `stability: stable`;
   - repository/directory inventory without procedures: `evidence_strength: low`, `reference-only`;
   - unresolved deployment caveat despite strong evidence: reject `adopt` and choose `trial`;
   - positive and near-miss route reasons, including rejection of candidate-list-only Notes;
   - generated-context leakage and missing-locator negative cases.
   - summary cases specify required source claims/caveats, forbidden imported claims/context terms, and distinct-information obligations rather than exact prose or fixed length;
   - a metamorphic pair presents the same source under different irrelevant campaign/repository context and requires the same assessment tuple and source claims with no ambient-context leakage;
   - add repo/vault leakage in semantic sections, exact/semantic redundancy, and stock filler negative cases.
   - `summary_cases.expected` records checklist statuses and required failure IDs, not checklist-note prose; include one positive all-pass case and one isolated failure for each checklist item.
5. Update `.agents/skills/atlas-core/SKILL.md` to expose the reducer contract, quality-validator contract, source envelope, and eval asset to owning skills without making `atlas-core` user-invocable.
6. Update `.agents/skills/atlas-source/SKILL.md` into an explicit staged workflow:
   - resolve canonical identity and extract only immutable identity/provenance fields; do not expose old artifact prose to the semantic draft;
   - fetch and build the source-only evidence envelope;
   - before any write-capable invocation, run the static calibration once for the active harness/model/template version; a batch runs it before its first write, and any wrong result means zero invocation writes;
   - derive a structured assessment and semantic draft independently for each source; never inherit a previous artifact’s tuple, phrasing, or candidate topics as a batch default;
   - run `atlas_quality.py validate-summary`, then use the seven-item acceptance checklist as the bounded semantic auditor over only the same evidence envelope plus the draft; this replaces the generic semantic-audit step rather than adding another model pass;
   - only after both gates pass, read bounded vocabulary/topic/relation rows, produce classification and route proposals, call the registry reducer, and attach post-draft Atlas annotations;
   - validate field coupling, route reason shape, media-fetch ledger, and the complete candidate cohort before connector writes;
   - for referenced/inspected media, persist the exact successfully fetched pinned URL, not a reconstructed path.
7. Extend `.agents/skills/atlas-audit/SKILL.md`:
   - add `--source-quality-calibration` as a read-only product-fixture mode;
   - in `--source-quality`, run deterministic validation first, then the same seven-item checklist for source-only grounding, fidelity, support, uncertainty, context-neutrality, assessment coherence, and proportional concision;
   - flag commit-pinned `moving`, any `adopt` tuple that fails the adoption gate, thin-primary `low` when the primary claim is substantive, malformed/nonmatching relation Notes, and referenced media that was not the successfully fetched asset;
   - retain existing context-leak, coverage, repeated-note, source-locator, identity, and registry checks.
8. Add `tests/test_atlas_quality.py`: parse every eval case; cover semantic-section boundaries, forbidden external context, URL/media-ledger membership, duplicate/placeholder detection, adoption coupling, positive/near-miss route reasons, deterministic JSON/exit behavior, context-perturbation fixture shape, one valid seven-item checklist, and missing/unknown/duplicate/failed checklist items. Keep exact checks on IDs/status/invariants, not freeform wording or one exact tool-call sequence.
9. Define one cross-harness/model conformance protocol in the quality guide and audit skill:
   - every native host uses the same skill, evidence bundle, fixture version, Python validator, and expected JSON; provider/harness/model are report metadata only;
   - verify live discovery from the app directory and record resolved hashes/paths for `.agents/AGENTS.md`, the owning skill, `atlas-core`, and both Python scripts so a host-global copy cannot silently win;
   - a harness without Python may use only a fixture-conformant port; a harness/model pair that cannot run or pass the cases is mutation-disabled, not approximately supported;
   - do not use new credentials merely to expand the matrix; run semantic trials for already configured pairs and preserve the same self-calibration gate for every later write-enabled pair.

### T3. Repair reviewed source artifacts and relation state

All bound-instance writes use logical `vault://atlas/...` paths through the active connector. Before writes, retain the three registry texts and the exact touched artifacts in an ephemeral local rollback bundle; do not add backups to the repo or vault.

1. Sync the updated product-owned architecture only to the local development instance `atlas`, then verify product-owned alignment. Do not write any non-development profile.
2. Use `repair-table-placement` to move the exact thirteen sequence 36-48 rows into the canonical `RELATIONS.md` table. Preserve every edge ID, tuple, status, date, and blank applied-pass value.
3. Treat each artifact correction as an explicit same-hash resummarization under the strengthened `atlas-source` contract. The semantic draft receives only the new evidence envelope and preserved immutable identity/provenance fields; old artifact prose and registry/topic context remain outside that phase. Preserve `source_id`, `source_seq`, `canonical_url`, artifact path, first-seen/acquisition provenance, and content hash; update `last_checked`/`last_summarized` and the matching manifest summary date:
   - sequence 9: restore `evidence_strength: medium`; keep the accepted `complete / high / medium / medium / stable / medium / reference-only` tuple;
   - sequences 13-35: set `stability: stable` because every canonical URL is full-commit pinned; evaluate posture independently per artifact under the new adoption gate;
   - sequence 21: restore `recommended_posture: trial` and the exact accepted `complete / high / high / high / stable / high / trial` tuple;
   - sequence 44: replace the broken Factor 9 media URL with the exact inspected pinned `img/195-factor-9-errors.gif` URL and retain the media-specific caveat.
4. A content-hash mismatch for any of these immutable canonical payloads is a blocker, not a changed-hash refresh. Stop and diagnose retrieval/normalization rather than fabricating a transition.
5. Re-run the bounded verifier for every existing relation row, sequences 1-48, and use `repair-relation-notes` to normalize Notes to the required locator/claim/relation/impact form. For sequences 5-48, reject candidate-list boilerplate. Preserve all relation values unless the bounded verifier produces source-specific evidence that the reviewed tuple is wrong; any tuple change must be reported explicitly rather than folded into the Notes repair.
6. Recompute, do not hand-edit, caches after repair. Required pre-T5 state:
   - `agentic-harness-architecture`: `dirty`, 13 pending edges (sequences 36-48), newest pending sequence 48, source watermark 4;
   - `ai-coding-workflow`: `dirty`, 31 pending edges (sequences 5-35), newest pending sequence 35, source watermark 0;
   - initial applied edges 1-4 retain their original applied pass;
   - no duplicate source, manifest, relation, topic, or artifact identity is created.

### T4. Pass the strengthened pre-refresh quality gate

T5 must not start until every gate below passes:

1. Run the focused Python tests for `atlas_state`, `atlas_quality`, `atlas_instance`, and the repo-local harness surface.
2. Run the deterministic reducer and source-quality fixture validators directly; repeated runs over identical bundles must produce byte-identical JSON and replacement documents.
3. Run `/atlas-audit --source-quality-calibration`; require every exact enum tuple, context-perturbation case, all seven acceptance-checklist items, and positive/negative provenance case to pass under the active model. Run the same fixture in every other already configured write-enabled harness/model pair. Record provider/harness/model metadata only in the execution report.
4. Verify native discovery from the app directory: each claimed write-enabled host must resolve the repo-local AGENTS/rules/skill/script surface, preserve command arguments, and avoid host-global Atlas precedence. An unavailable or failing pair remains mutation-disabled and is not claimed as qualified.
5. Run the bounded source-quality audit for exact source sequences 5-48 and the registry audit for sequences 1-48. Required result: zero findings for structure, identity, hash transition, frontmatter, required sections, context/repository leakage, coverage, proportional concision, rubric coupling, relation provenance, media links, and cache derivation.
6. Re-fetch the corrected Factor 9 pinned media URL and establish that it resolves to the inspected animation; establish that the old URL fails and is absent from durable Atlas state.
7. Run `python3 scripts/atlas-instance.py check --name atlas`; it must now fail the old malformed fixture in tests and pass the repaired bound instance.
8. If a gate fails, repair the source contract or exact affected state and rerun the complete bounded gate. Do not start refresh from a partially clean cohort, weaken a fixture for one model, or add a provider-specific prompt.

### T5. Apply factor evidence and complete topic refresh

Execute the existing T5 intent in `.agents/plans/2026-07-14-1538_atlas-source-summary-quality.md`; do not synthesize `ai-coding-workflow`.

1. Read the exact pending set for `agentic-harness-architecture` and call `refresh-start` with all thirteen edge IDs for sequences 36-48. Any missing or extra edge blocks the refresh.
2. Create one pass first at `vault://atlas/summaries/research/agent-systems/harness/topics/agentic-harness-architecture/passes/<YYYY-MM-DD>--12-factor-agent-factor-coverage.md` with:
   - `mode: vault-only`, `coverage_state: partial`, `confidence: medium`;
   - the thirteen existing artifacts consulted;
   - one source-outcome row per edge, preserving relation/impact/confidence and the repaired verifier rationale;
   - findings grouped by structured tool calls, prompt/context ownership, execution/business-state unification, launch/pause/resume and human contact, compact errors/small agents, stateless reduction, trigger boundaries, and prefetch trade-offs;
   - exact managed sections changed, registry transition, checks, and remaining independent-evidence gaps.
3. Patch only managed regions of the existing topic `INDEX.md` plus frontmatter fields:
   - keep `coverage_state: partial` and `confidence: medium`; advance `last_researched` to the pass date;
   - retain 5-8 current-answer bullets, strengthening existing deterministic-core, tool-interface, state/lifecycle, and verification/back-pressure claims with factor citations rather than replacing the answer wholesale;
   - add bounded recommendation-matrix entries only where the factor pages add a distinct decision (typed tool calls, compact error feedback, stateless reducer loop, prefetch trade-off);
   - replace the obsolete caveat that detailed factor pages were not materialized with the narrower caveat that the pages remain one practitioner framework without independent comparative validation;
   - extend the existing `## Evidence map` with one explicit row per factor/appendix artifact. The resulting table remains below the 25-40 row split threshold, so do not create `SOURCES.md` or any optional split file;
   - add the pass to `recent-changes` and `read-next`; retain the initial synthesis pass and original sequence 1 root artifact as provenance.
4. Call `refresh-complete` with the exact thirteen edges and pass path. Required result:
   - edges 36-48 are `applied` and name this pass;
   - `agentic-harness-architecture` is `current`, dirty count 0, no pending IDs/newest pending sequence, last synthesized on the pass date, source watermark 48;
   - source artifacts and manifest identities remain unchanged and routed.
5. Confirm `ai-coding-workflow` remains `dirty` with the same 31 sequence 5-35 pending edges, newest sequence 35, and source watermark 0. Do not create a pass or topic synthesis for it.
6. Any failure after `refresh-start` uses `refresh-fail`: leave unapplied edges pending, set the topic `blocked`, and report the exact failed write. Never report T5 complete from partial state.

### T6. Reconcile final state and close repository plan

1. Re-run:
   - focused Python reducer, quality, instance, and harness-surface tests;
   - deterministic fixture validation and byte-stability checks;
   - source-quality calibration for every currently write-enabled harness/model pair;
   - repo-local discovery/precedence smokes;
   - exact sequence 5-48 source-quality audit;
   - full manifest/relation/topic integrity and cache audit;
   - `python3 scripts/atlas-instance.py check --name atlas`.
2. Exercise the observable topic behavior:
   - `/atlas-answer agentic-harness-architecture` must pass its freshness gate and answer from the updated source-backed topic;
   - `/atlas-answer ai-coding-workflow` must halt as dirty and report the 31 pending edges rather than synthesizing or auto-refreshing.
3. Update `.agents/plans/2026-07-14-1538_atlas-source-summary-quality.md` without rewriting historical task outcomes:
   - append the T3/T4 post-completion review findings and exact repairs to the execution/completion record;
   - mark T5 complete only after the refresh and all strengthened checks pass;
   - record the pass path, applied edge IDs, corrected enum/media decisions, calibration result, audit counts, and check command result;
   - set status `DONE`, add completion timestamp/summary, and atomically move this plan to `.agents/plans/archive/`.
4. Leave `.agents/plans/2026-07-13-2349_ai-coding-workflow.md` in progress with T1 complete and T2-T6 unchanged. Its Atlas topic remains dirty until that plan explicitly synthesizes it.
5. Remove any temporary test instances, local request bundles, or smoke fixtures. Do not leave verification rows or repair backups in `vault://atlas/`, `scaffold/`, or the repo.

## Critical Files and Anchors

### Product package

- `.agents/AGENTS.md` — concise always-loaded map updated only for the reducer/validator runtime surface.
- `.agents/ARCHITECTURE.md` — semantic/state determinism boundary, context-neutral source envelope, canonical/derived state, and legal freshness transitions.
- `.agents/rules/atlas-reducer-discipline.md` — freestyle fail-closed use of the reducer and quality validator.
- `.agents/rules/atlas-boundaries.md`, `.agents/rules/atlas-skill-surface.md` — audited seam contracts; no content change planned.
- `.agents/skills/atlas-core/SKILL.md` — support-skill pointers to reducer, quality, envelope, and calibration contracts.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — table boundaries, edge/reason shape, relation and cache transitions.
- `.agents/skills/atlas-core/assets/source-summary-quality-guide.md` — context envelope, concision, scoring, provenance, and conformance rubrics.
- `.agents/skills/atlas-core/assets/source-summary-template.md` — context-neutral semantic sections versus post-draft Atlas annotations.
- `.agents/skills/atlas-core/assets/evals/source-summary-quality.json` — provider-neutral assessment, summary, routing, and negative-audit fixtures.
- `.agents/skills/atlas-source/SKILL.md` — evidence envelope, per-source draft, pre-write calibration, deterministic validation, semantic audit, then routing.
- `.agents/skills/atlas-route/SKILL.md`, `.agents/skills/atlas-refresh/SKILL.md`, `.agents/skills/atlas-index/SKILL.md`, `.agents/skills/atlas-audit/SKILL.md` — reducer and audit integration.
- `.agents/commands/atlas-*.md` — audited thin dispatch stubs; no body changes planned.
- `AGENTS.md`, `CLAUDE.md`, `.cursor/{skills,rules}`, `.grok/{skills,rules}`, `.claude/{skills,rules}` — thin repo-local discovery adapters to `.agents/`.
- `scripts/atlas_state.py` — pure parser/validator/reducer and local audit adapter.
- `scripts/atlas_quality.py` — pure source-artifact/calibration validator.
- `scripts/atlas-instance.py` — provision check extended to call the living-state audit.
- `tests/test_atlas_state.py`, `tests/test_atlas_quality.py`, `tests/test_atlas_harness_surface.py`, `tests/test_atlas_instance.py` — deterministic state, quality, packaging, and provision coverage.

### Bound instance

- `vault://atlas/ARCHITECTURE.md` — synced product-owned snapshot.
- `vault://atlas/summaries/sources/MANIFEST.md` — preserved identities and repaired summary dates.
- `vault://atlas/summaries/registry/RELATIONS.md` — canonical row placement, normalized verifier Notes, T5 application provenance.
- `vault://atlas/summaries/registry/TOPICS.md` — reducer-derived caches for both affected topics.
- Exact repaired source artifacts: sequences 9, 13-35, and 44.
- `vault://atlas/summaries/research/agent-systems/harness/topics/agentic-harness-architecture/INDEX.md` — bounded managed-section delta.
- `vault://atlas/summaries/research/agent-systems/harness/topics/agentic-harness-architecture/passes/<date>--12-factor-agent-factor-coverage.md` — new T5 provenance pass.

### Plan lifecycle

- `.agents/plans/2026-07-14-1538_atlas-source-summary-quality.md` — execution record to complete and archive.
- `.agents/plans/2026-07-13-2349_ai-coding-workflow.md` — read-only state check; do not advance or archive.

## Verification / Done Criteria

- [x] The old T4 layout is a deterministic failing fixture; no canonical parser counts its orphan rows.
- [x] Normal route and refresh events can only render rows inside the canonical relation table and always derive topic caches from validated rows.
- [x] `atlas_state.py` and `atlas_quality.py` are dependency-free Python 3 tools with structured I/O, stable exit behavior, no hidden connector/model/network/time/cwd dependency, and byte-stable repeated outputs; no Bash script contains Atlas business logic.
- [x] Repo-local AGENTS/rules/skills are canonical; Grok, Claude Code, Cursor, Codex, and OMP discovery resolves to this package rather than a host-global Atlas copy; command/skill entrypoints preserve arguments and thin dispatch.
- [x] Every write-enabled harness/model pair runs the same fixture version and expected outputs. An unqualified or failing pair performs no Atlas mutation; no provider-specific prompt or relaxed rubric exists.
- [x] Source semantic drafts use only the declared evidence envelope. Taxonomy/routing happen afterward and cannot alter factual claims.
- [x] The context-perturbation pair yields the same assessment and source claims without task/plan/repo/topic/provider leakage.
- [x] Summaries are proportionate and minimum-sufficient: required claims/caveats are present, redundancy and stock filler are absent, and no brittle universal length cap is enforced.
- [x] The semantic acceptance checklist contains exactly seven binary outcome questions, is the existing bounded semantic audit rather than an extra model pass, and grades no exact wording, length, citation count, weighted score, or tool path.
- [x] Sequence 9 and 21 match the exact T2-qualified assessment tuples.
- [x] Sequences 13-35 are `stable`; every posture is independently justified and every `adopt` passes the high/high/stable/no-unresolved-caveat gate.
- [x] Factor 9 stores and resolves the exact inspected pinned media URL; the broken URL is absent from durable state.
- [x] Every relation row sequence 1-48 has source-local, source-specific verifier provenance matching its relation and impact columns.
- [x] The exact T3/T4 source cohort (sequences 5-48) has zero strengthened source-quality findings.
- [x] The thirteen factor edges apply in one pass; `agentic-harness-architecture` becomes current with watermark 48 and retains original root/pass provenance.
- [x] `ai-coding-workflow` remains dirty with exactly the unchanged 31 sequence 5-35 pending edges.
- [x] Focused tests, deterministic validators, provider-neutral calibration, native discovery smokes, bound-instance audit, media check, and `atlas-instance.py check --name atlas` all pass.
- [x] No provider-specific behavioral rule, parallel registry backend, new schema column, scaffold living row, optional topic split, duplicate source/edge, host-global Atlas dependency, or temporary fixture remains.
- [x] The source-summary-quality repository plan is complete and archived; the AI-coding-workflow plan is not advanced.

## Assumptions and Stop Conditions

- Instance `atlas` is the local development profile already bound by `vault://atlas/`; any evidence that it is non-development requires approval before sync or repair writes.
- The reviewed sequence 9, 13-35, and 44 canonical payloads are immutable. A hash mismatch stops repair for diagnosis.
- Python 3 is the reference runtime because Atlas provision tooling already uses it and it expresses the parser/validator without shell dependencies. A runtime without Python may mutate only through a port that passes the same byte-level fixtures.
- “Agent/model agnostic” means one policy, typed inputs/outputs, deterministic state, and conformance-gated support. It does not claim that every present or future SOTA model emits identical prose or passes without qualification.
- Literal fresh-context execution is host-dependent. The portable hard requirement is that the draft evidence bundle excludes external context and the artifact passes deterministic leakage checks plus context-perturbation and bounded semantic audits.
- Repo-local host adapters may be added or repointed, but no host-global skill/rule installation or credential use is part of this plan.
- A reducer/parser ambiguity, source identity conflict, required taxonomy change, unexpected relation tuple change, harness-precedence conflict, or failed conformance gate stops before T5. Do not guess, silently widen the write set, weaken the rubric, or repair vocabulary/topic scope from this plan.
- Cross-provider semantic quality cannot be mathematically guaranteed by prose alone. Structural state and deterministic audit dimensions are exact; open-ended groundedness and concision fail closed through shared calibration plus bounded post-generation audit.

## Completion Summary

Completed 2026-07-15-1254.

- Added dependency-free deterministic state and source-quality validators, integrated them into Atlas skills, rules, instance checks, and repo-local harness discovery, and covered them with 38 focused tests.
- Repaired the 48-source living state without changing source identities: one canonical relation table, 54 exact verifier reasons, calibrated summary decisions, exact pinned media, and zero strengthened findings across sequences 5–48.
- Qualified the shared 24-case calibration on OMP `openai-codex/gpt-5.6-sol` and Grok CLI 0.2.101 `grok-4.5`; repeated validator output was byte-identical.
- Created `passes/2026-07-15--factor-evidence-refresh.md`, applied exactly the thirteen sequence 36–48 edges, and refreshed only `agentic-harness-architecture` to `current` with watermark 48.
- Preserved `ai-coding-workflow` as `dirty` with its unchanged 31 sequence 5–35 pending edges; its separate plan remains `IN_PROGRESS` at T2.
- Archived the completed source-summary-quality plan. Removed temporary qualification outputs, request bundles, repair backups, and smoke data.
- Final proof: 38 tests pass; exact 44-artifact audit has zero blockers; state audit is clean; `python3 scripts/atlas-instance.py check --name atlas` reports `check OK`.

## Post-completion override

On 2026-07-15, the user clarified that Claude Code is not part of the active
harness setup and that Grok uses the existing manually managed host-global
`.grok/{skills,rules}` symlinks. The custom `CLAUDE.md` and `.claude/` adapters
were removed, `.grok/{skills,rules}` were restored to their prior targets, and
harness-surface tests now enforce only the canonical repo-local `AGENTS.md` and
`.cursor/{skills,rules}` aliases. The provider-neutral Atlas contracts,
validators, and shared calibration remain unchanged.
