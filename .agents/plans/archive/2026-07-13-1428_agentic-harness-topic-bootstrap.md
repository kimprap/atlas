# Bootstrap the Agentic Harness Architecture topic

**Datetime**: 2026-07-13-1428
**Scope**: Bootstrap the first `agentic-harness-architecture` topic on the bound `atlas` instance from four explicit sources and temporary request framing.
**Summary**: Create canonical vocabulary and a lean topic shell, ingest and route the fixed source packet, persist the initial answer through the dirty-topic refresh path, verify the current answer, then remove the temporary handoff.
**Status**: DONE

## Context

Use `temp-agentic-harness.md` as temporary request framing for the first durable Atlas topic about agent-harness design. The file is not evidence, an Atlas source artifact, a topic contract, scaffold content, or product architecture; the durable result must be registry rows, four materialized source artifacts, one topic `INDEX.md`, and one dated pass on the bound `atlas` instance. Delete the temporary handoff from the app repository only after the persisted topic can be answered through Atlas.

The live assertions that `VOCAB.md` contains only source kinds and `TOPICS.md` is empty are unverified because `vault://atlas/…` was unavailable while Obsidian was not running. The execution therefore begins with a read-only state gate and has explicit conflict fallbacks.

## Tasks

- [x] T1. Bind the `atlas` instance and pass the read-only vocabulary/topic conflict gate.
  completed 2026-07-13-0953
- [x] T2. Promote `agent-systems` / `harness` and create the lean `agentic-harness-architecture` topic shell through `/atlas-index`.
  completed 2026-07-13-0953
- [x] T3. Materialize the four fixed URLs through `/atlas-source` without treating the temporary handoff as evidence.
  completed 2026-07-13-0953
- [x] T4. Re-run bounded routing for all four source IDs and establish the topic's persisted pending-edge set.
  completed 2026-07-13-0953
- [x] T5. Apply the first source-backed answer and dated pass through `/atlas-refresh`.
  completed 2026-07-13-0953
- [x] T6. Verify `/atlas-answer`, registry consistency, and product integrity, then remove `temp-agentic-harness.md`.
  completed 2026-07-13-0953

## Verification / Done criteria

Run from `/Users/kim/Desktop/ng3/atlas/app` with the `atlas` instance bound to logical `vault://atlas/`:

- [x] `read vault://atlas/summaries/registry/VOCAB.md` shows exactly one active `agent-systems` domain row and one active `harness` subdomain row with parent `agent-systems`.
- [x] `read vault://atlas/summaries/sources/MANIFEST.md` shows one identity for each of the four canonical URLs, with no duplicate source IDs or URLs.
- [x] `read vault://atlas/summaries/registry/TOPICS.md` shows `agentic-harness-architecture` at the exact planned path with `Freshness state=current`, `Dirty count=0`, no pending edge IDs, a nonblank `Last synthesized`, and a watermark equal to the maximum applied source sequence.
- [x] `read vault://atlas/summaries/registry/RELATIONS.md` shows every included source-topic edge as `applied` with the same initial pass path; excluded sources are absent from the edge ledger and documented in the pass.
- [x] `read vault://atlas/summaries/research/agent-systems/harness/topics/agentic-harness-architecture/INDEX.md` shows a source-backed current answer, evidence-map artifact links, explicit gaps, and no use of the temporary handoff as evidence.
- [x] The dated initial pass records request framing, source outcomes, managed sections changed, registry updates, coverage, and checks.
- [x] `/atlas-answer agentic-harness-architecture` returns the current answer without a freshness halt and cites materialized source artifacts.
- [x] `python3 scripts/atlas-instance.py check` exits 0.
- [x] `temp-agentic-harness.md` is absent from the app root only after every preceding criterion passes.

## Approach

### 1. Bind and gate the target instance before writes

- Run from the Atlas app package so `.agents/commands/` and `.agents/skills/` resolve, and bind the `atlas` instance as `vault://atlas/` through the active connector/profile. Do not access `../vault/instances/atlas` directly.
- Read `vault://atlas/ARCHITECTURE.md`, `summaries/registry/VOCAB.md`, `TOPICS.md`, `RELATIONS.md`, and `summaries/sources/MANIFEST.md`.
- Confirm that none of these IDs already has a conflicting meaning:
  - domain `agent-systems`
  - subdomain `harness` under `agent-systems`
  - topic `agentic-harness-architecture`
- Reuse an exact existing row only when its label, parent, topic path, and scope match this plan. If any ID exists with different ownership, meaning, parent, or path, stop before writes and report the exact conflicting row; do not invent an alternate ID.
- If the topic already has a non-placeholder answer or a completed pass, stop: this plan is for first creation, not rebuild. If the connector cannot read the logical vault paths, stop without writes.

### 2. Create canonical vocabulary and the lean topic shell through `/atlas-index`

Invoke `/atlas-index` with one explicit request containing all of the following decisions:

- Add or reuse this domain row:
  - ID: `agent-systems`
  - Type: `domain`
  - Label: `Agent systems`
  - Parent: blank
  - Allowed aliases: `agent systems`
  - Status: `active`
  - Notes: `Systems and runtimes for reliable LLM-agent execution.`
- Add or reuse this subdomain row:
  - ID: `harness`
  - Type: `subdomain`
  - Label: `Harness`
  - Parent: `agent-systems`
  - Allowed aliases: `agent harness; agent harnesses; harness engineering`
  - Status: `active`
  - Notes: `Context, tools, control flow, state, verification, and orchestration around LLM calls.`
- Create the topic row and lean folder:
  - Topic ID: `agentic-harness-architecture`
  - Topic path: `summaries/research/agent-systems/harness/topics/agentic-harness-architecture/INDEX.md`
  - Domain: `agent-systems`
  - Subdomain: `harness`
  - Canonical title: `Agentic harness architecture`
  - Aliases: `agent harness design; harness engineering; 12-factor agents runtime`
  - Canonical tags: blank; do not promote speculative tags for this bootstrap
  - Include terms: `agent harness; agentic harness; harness engineering; 12-factor agents; building effective agents; context engineering; agent runtime; tool interface; agent control flow; agent state; verification; back-pressure; agent orchestration`
  - Exclude terms: `Atlas product maintenance; research-vault operations; model training; foundation-model architecture; domain-specific agent applications`
  - Initial freshness: `current`
  - Dirty count: `0`
  - Pending edge IDs: blank
  - Newest pending source seq: `0`
  - Last synthesized: blank
  - Source watermark: `0`
  - Refresh model: `same-as-topic-creation`
- Create only the template-backed topic `INDEX.md` and `passes/` directory. Initialize the topic as `status: draft`, `coverage_state: insufficient`, and `confidence: low`. Do not create `SOURCES.md`, `DECISIONS.md`, `HISTORY.md`, or unrelated domain/topic folders.
- Verify the `VOCAB.md` rows, `TOPICS.md` row, subdomain index link, and exact topic path before ingesting sources.

### 3. Materialize the four known sources through `/atlas-source`

Invoke one `/atlas-source` request with exactly these inputs; do not use `/atlas-acquire` for them:

1. `https://github.com/humanlayer/12-factor-agents`
2. `https://www.anthropic.com/engineering/building-effective-agents`
3. `https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents`
4. `https://docs.langchain.com/oss/python/langchain/context-engineering`

For each input:

- Follow `atlas-source` canonicalization and manifest dedupe. Reuse an unchanged artifact instead of creating a duplicate.
- Materialize one source artifact under `summaries/sources/artifacts/<YYYY>/<YYYY-MM>/` and one manifest identity keyed by canonical URL/source ID.
- Use only existing canonical vocabulary: `primary_domain: agent-systems`, `subdomains: [harness]`; leave unsupported taxonomy in `candidate_terms` rather than promoting it.
- Treat `temp-agentic-harness.md` only as a checklist of questions and source leads. Do not cite it, copy its claims into evidence sections, or create a source artifact from it.
- Allow the source workflow to route every new or materially changed artifact after writing it. An unchanged existing artifact still proceeds to the explicit routing check in the next step.
- If fetch coverage is partial or failed, persist the truthful coverage state and exact gap; never substitute claims from the temporary handoff.

### 4. Re-run bounded routing and establish the dirty set

Invoke `/atlas-route` for the four resulting source IDs as one bounded scope, even when `/atlas-source` already routed them. This makes pre-existing unchanged artifacts and newly created artifacts converge on the same current topic definition without duplicate edges.

- Candidate generation must use the topic row created in step 2 and the canonical source metadata from step 3.
- Expect each in-scope source to produce or reuse one deterministic relation edge for `agentic-harness-architecture`; let the bounded verifier choose `direct` versus `supporting`, impact, and confidence from source evidence.
- If a source remains `no-topic-match`, rerun routing once after confirming the exact include terms and canonical domain/subdomain above are present. If it still does not match, preserve the verifier decision and record that source as an excluded lead in the first pass; do not force an edge or hand-edit `RELATIONS.md`.
- Recompute `TOPICS.md` from `RELATIONS.md`. Before synthesis, the topic must be `dirty` when at least one pending edge exists, with dirty count and pending edge IDs exactly matching persisted pending relations.
- If no source produces a pending edge, stop before synthesis and retain `temp-agentic-harness.md`; report the four route decisions because the evidence pipeline did not establish a refresh input.

### 5. Produce the first durable answer through `/atlas-refresh`

Invoke `/atlas-refresh agentic-harness-architecture` rather than `/atlas-research`. The topic shell already exists and routing has made it dirty; the current `atlas-research` contract hands an existing dirty topic to `atlas-refresh`.

- Use the execution date and pass slug `initial-agentic-harness-synthesis`, yielding `passes/<YYYY-MM-DD>--initial-agentic-harness-synthesis.md` unless the owning skill enforces its canonical pending-delta slug; in that case use the skill-owned slug without creating a second pass.
- Use pending Atlas source artifacts as the only evidence. Use `temp-agentic-harness.md` only to frame coverage around context selection, tools/skills, control flow, state, verification/back-pressure, orchestration/delegation, hooks, and human approval.
- Patch the template topic into a usable current answer. Every substantive claim must cite a materialized source artifact in the evidence map. Unsupported handoff claims become `Gaps and acquisition needs`, not answer claims.
- Record the four source outcomes in the pass: applied relation/source artifact, or excluded/failed lead with the exact reason.
- On success, mark applied relation rows with the pass path and recompute the topic row to `current`, `Dirty count=0`, blank pending edge IDs, `Last synthesized=<execution date>`, and `Source watermark=<maximum applied source seq>`.
- On any partial write failure, leave unapplied edges pending, set the topic to `blocked`, retain `temp-agentic-harness.md`, and stop without answering.

### 6. Prove the topic and remove the temporary handoff

- Invoke `/atlas-answer agentic-harness-architecture`.
- Require a normal current-topic answer, not a dirty/refreshing/blocked halt. Confirm the answer reads the topic contract and cites Atlas source artifacts rather than raw URLs or `temp-agentic-harness.md`.
- Confirm the topic folder contains `INDEX.md` and exactly one initial pass plus only threshold-justified optional split files; this bootstrap should normally have no optional split files.
- After those checks pass, delete `temp-agentic-harness.md` from the Atlas app root. Do not copy it into `scaffold/`, product architecture, or the bound instance.
- Run `python3 scripts/atlas-instance.py check` from the app root to confirm product-owned/scaffold integrity; this check is read-only and does not validate living research semantics, which are covered by the registry and answer checks above.

## Critical files & anchors

- `.agents/ARCHITECTURE.md` — `Mode ownership`, `Source identity and routing`, and `Freshness model` define the index/source/route/refresh write boundaries.
- `.agents/skills/atlas-index/SKILL.md` — owns explicit vocabulary promotion and lean topic creation from `atlas-core` templates.
- `.agents/skills/atlas-source/SKILL.md` — owns explicit URL ingestion, canonical identity, dedupe, and automatic routing after changed artifacts.
- `.agents/skills/atlas-route/SKILL.md` — owns bounded verifier decisions, deterministic edges, and dirty-cache recomputation.
- `.agents/skills/atlas-refresh/SKILL.md` — owns the persisted dirty-to-current transition and blocked-state failure behavior.

## Assumptions & contingencies

- The `atlas` instance is the intended write target. If another connector/profile is active, stop before writes rather than rebinding or guessing.
- The target vocabulary and topic are assumed absent or exact reusable placeholders. Any conflicting existing ID/path stops execution with the exact row reported; no alternate taxonomy is invented.
- The four URLs are the complete fixed source packet for this bootstrap. `/atlas-acquire` is not used unless a later, separate request authorizes additional bounded discovery.
- Initial topic synthesis uses `/atlas-refresh` because a pre-created topic becomes dirty when `/atlas-source` routes evidence. `/atlas-research` remains the creation/rebuild workflow for a topic not already represented by a dirty shell.
- Partial or failed source coverage is recorded honestly and may produce a partial topic answer. It does not permit using the temporary handoff as evidence.
- `temp-agentic-harness.md` remains until the topic is current and `/atlas-answer` succeeds; any blocked or zero-edge outcome retains the file for diagnosis.

## Completion Summary

- Verified that the renamed Obsidian instance resolves as `vault://atlas/`; the physical instance remains isolated under the sibling binding repository at `vault/instances/atlas/`.
- Added active `agent-systems` and `harness` vocabulary rows, one canonical topic row, a lean subdomain index, and a lean topic folder.
- Materialized four source artifacts with unique canonical identities and source sequences `1` through `4`. The 12-Factor Agents artifact records partial coverage; the other requested pages record complete page coverage.
- Routed all four sources as `direct`, `high` impact, `high` confidence edges. The explicit rerun reused the deterministic edge IDs and created no duplicates.
- Applied all four edges through `passes/2026-07-13--initial-agentic-harness-synthesis.md`. The topic is `current`, has no pending edges, was last synthesized on `2026-07-13`, and has source watermark `4`.
- Published a seven-rule current answer covering deterministic runtime ownership, evidence-gated autonomy, context control planes, tool interfaces, progressive disclosure, inspectable state/lifecycle, and compact verification back-pressure. Coverage remains `partial` with `medium` confidence because the packet has no contradictory evidence, detailed 12-Factor pages were not materialized, and several formal interface/state questions remain open.
- Verified registry consistency programmatically: 9 vocabulary rows, 4 unique manifest identities, 1 current topic row, and 4 unique applied relations pointing to the same pass.
- Verified the freshness-gated answer path, the one-pass lean folder shape, absence of temporary-handoff citations in topic/source evidence, and `python3 scripts/atlas-instance.py check`.
- Deleted `temp-agentic-harness.md` only after all preceding checks passed.
