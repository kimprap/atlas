# Repository Agent Memory First Draft

**Datetime**: 2026-08-02-1456
**Scope**: Repository-native agent-memory first-draft artifacts and bounded Atlas acquisition/research
**Summary**: Preserve this session's raw lessons, establish the preferred directory-indexed memory draft and workflow context, and run bounded Atlas acquisition/research before any final memory architecture or ingestion is chosen.
**Status**: IN_PROGRESS

## Context

The repository currently has no `.agents/memory/` directory. This first pass must preserve raw session lessons under `.agents/memory/tmp/`, document the preferred dependency-free directory-and-index baseline in `.agents/memory/FIRST_DRAFT.md`, and explain its provenance/lifecycle in `.agents/memory/WORKFLOW.md`. The existing `lean-self-improving-agent-harness` topic overlaps only on persistent evidence, reviewed changes, authority, and rollback; its scope/current answer do not cover memory storage/indexes, staleness, incremental consolidation, bounded loading, long-tail relevance, or concurrent updates, so the research belongs in a dedicated `agent-memory` topic related to—not folded into—the lean-harness topic. T3 must exercise only the user-facing `/atlas-*` skill interfaces, preserving their gates and reporting any robust refusal as framework stress-test evidence instead of bypassing a blocked workflow with direct façade/artifact mutation.

## Tasks

- [x] T1. Preserve raw session lessons as temporary memory inputs — Completed: 2026-08-02T09:31:41Z
- [x] T2. Establish the preferred first-draft memory artifact set — Completed: 2026-08-02T09:31:41Z
- [ ] T3. Research agent memory through the current Atlas front door
- [ ] T4. Refine and verify the provisional memory proposal

## Approach
`local://repo-agent-memory-first-draft-plan.md` is the authoritative mutable execution artifact. Execution starts only from its approved `PENDING` content. When T1 begins, change its `Status` to `IN_PROGRESS`; perform no repository or Atlas mutation before approval. After each task's criteria pass, change its task row to `- [x] Tn. <text> — Completed: <YYYY-MM-DDTHH:MM:SSZ>` using observed UTC. After every criterion passes, append `## Completion Summary` and set `Status: DONE`. A blocker leaves only affected tasks unchecked and `Status: IN_PROGRESS`.
On success, `## Completion Summary` records the four repository artifacts, exact Atlas topic/pass/run/source paths, `/atlas-ask` dispatch handles and aggregate outcomes, baseline/final audit results, the instance-check result, and the explicit pre-implementation `grill-with-docs` gate. After `Status: DONE` and every verification criterion is present, archive the authoritative plan with `archive_plan_artifact` slug `repo-agent-memory-first-draft`.

### T1. Preserve raw session lessons as temporary memory inputs

- At execution start, inspect the exact four target paths and the `.agents/AGENTS.md` layout entry without following symlinks. Every newly created memory file begins with `<!-- provisional-plan: local://repo-agent-memory-first-draft-plan.md -->`. An absent target may be created. Any symlink, non-regular target, unexpected file/directory under `.agents/memory/`, existing target without that marker, or conflicting `memory/` layout row is preserved user work and blocks before overwrite/merge/rename/delete. A marked partial-run target may receive only missing plan-required sections or later-phase dynamic replacements; any populated conflict blocks. An already-correct layout row is a no-op.
- Create `.agents/memory/tmp/2026-08-02-atlas-evidence-date-seam.md` as one raw lineage bundle. Do not add frontmatter from the eventual memory schema, split it into promoted records, or link it from the active-memory portion of `INDEX.md`.
- Keep the raw file repository-visible; do not add a `.gitignore` exception or stage/ship it as part of this plan. Replace an isolated secret/private value with literal `[REDACTED]` plus an evidence-gap note; if the lesson cannot remain intelligible without sensitive content, do not create the file and leave T1 blocked.
- Write these raw lesson statements verbatim enough to survive later ingestion:
  1. **Qualified / already encoded:** `source.prepare` locally supplies inventory-owned `checked_on` only when a ready evidence bundle omits both `first_seen` and `fetched_at`; it creates one effective mapping with `first_seen = checked_on`, reuses it through `_evidence_identity`, `merge_artifact`, and summary validation, does not mutate the worker packet, and preserves fail-closed handling for any supplied invalid value.
  2. **Merged mechanism:** one effective evidence mapping must flow through every downstream consumer; keep this with the qualified lesson rather than as a separate final claim.
  3. **Rejected ownership expansion:** workers and `source-worker-result.schema.json` must not be required to synthesize registry-owned dates.
  4. **Rejected fallback expansion:** direct `source.merge_artifact` callers retain explicit-date validation because they have no inventory-owned `checked_on`.
  5. **Rejected/transient material:** the historical snapshot/parser signature was not reproducible at the declared target; manifest revisions, fixture values, agent status, probe output, and generic schema advice remain provenance rather than durable claims.
- Preserve these implementation/verification-lineage target paths and reported SHA-256 values, explicitly labeling them `reported by the named lineage; not recomputed while preserving this raw input`: `scripts/atlas_source.py` (`39f6bbe5853885c9331df566337c367c144cafd8eb6e0eed6ac3ea1ccee46a2d`), `tests/test_atlas_tool.py` (`4521a26fb39cb84a198768b0d88faa79a8475057749dd3067478952a09826e57`), `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` (`354b4b8b0dba94d04482f95e567e7dd53e85a2e14a4b9a4179d16c52e9465430`), `.agents/skills/atlas-source/SKILL.md` (`54015e082ea3f8a54c8913bf9e2b39bcbd26162f25a07b699e5aa7511e541eb7`), and unchanged `.agents/skills/atlas-core/assets/source-worker-result.schema.json` (`7aa0b607f8aa9b5d38ab1d3f0f30ede6e2cad44cbb78a27604ebeac16d4e3570`).
- Preserve the lineage handles `agent://DiagnoseAtlasIngestion`, `agent://ImplementEvidenceDateSeam`, `agent://VerifyEvidenceDateSeam`, `agent://ReviewEvidenceDateSeam`, and `agent://AssessEvidenceDateLearning`; label them session evidence rather than portable repository authority. Attribute `4/4 OK`, final review approval, and `CURATED` to those handles instead of claiming they were rerun while writing the raw file.
- Record the explicit evidence gap: no dedicated direct-merge missing-date unit test exists in the immutable target; that retained behavior is grounded by static inspection only.
- Keep this temporary repository input separate from living Atlas state under `vault://atlas/`; never copy Atlas topic rows or passes into `.agents/memory/`.

### T2. Establish the preferred first-draft memory artifact set

- Create `.agents/memory/INDEX.md` as a provisional smart map, not a memory dump. Give it these exact sections:
  - `## Status` — state that the memory system is not active, no memory has been promoted, and `tmp/` is excluded from normal loading.
  - `## Lookup order` — while provisional, read `Status`, then `FIRST_DRAFT.md`/`WORKFLOW.md`, and stop; after activation, resolve scope in `Active memory map` and load only its linked records. Never scan all record files or `tmp/`.
  - `## Active memory map` — the literal text `None — promotion begins only after the final design is approved and implemented.`
  - `## Temporary inputs` — link `tmp/2026-08-02-atlas-evidence-date-seam.md` and label it un-ingested raw material.
  - `## Research comparison input` — initial state is the literal `Pending — see FIRST_DRAFT.md`; T4 replaces it with accepted topic/pass links only after success, while a terminal contingency replaces it with the applicable pre-pass or post-pass blocker text defined below.
- Create `.agents/memory/WORKFLOW.md` using the observed `skill://dev-ask/WORKFLOW.md` documentation shape: `Purpose`, `Interface`, `Lifecycle`, `Artifact ownership`, `Inspiration and evidence`, `Invariants`, and `Maintenance`.
  - In `Purpose`, record the origin: the settled Atlas ingestion lesson was already encoded in its owning contract/skill/code/tests and the terminal curator correctly created no duplicate guidance, but no bounded repository memory map existed for residual cross-run discovery; the external sources motivated separating bootstrap, index, scoped records, and raw candidates.
  - Define the eventual interface as one small bootstrap instruction available to every repository agent/subagent, a bounded `INDEX.md` map, scoped records loaded only when relevant, and explicit exclusion of `tmp/` from ordinary reads.
  - Define the lifecycle as `settled outcome → raw candidate → qualification/deduplication/conflict check → human or designated-authority promotion → indexed active record → update or explicit supersession → historical retention`.
  - Assign one owner per artifact: `AGENTS.md` will eventually own only bootstrap/loading and precedence; `INDEX.md` owns discovery; each record owns one durable lesson; `tmp/` owns untrusted/un-ingested candidates; canonical contracts/code/tests remain the preferred owner when they can encode the behavior; Atlas owns research evidence only under `vault://atlas/`.
  - Cite Cursor's [Field Guide article section](https://cursor.com/blog/agent-swarm-model-economics#letting-agents-shape-the-environment), [`continual-learning` plugin](https://github.com/cursor/plugins/tree/14d9dfa06283faa94bf9931d3e98c189bc375680/continual-learning), commit-bound [`reflect`](https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/reflect/SKILL.md), [`recall`](https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/recall/SKILL.md), and [`automate-me`](https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/automate-me/SKILL.md); distinguish the private Field Guide, automatic transcript-to-`AGENTS.md` updater, human-reviewed skill curation, and on-demand transcript reconstruction.
  - Cite Matt Pocock's commit-bound [skills repository](https://github.com/mattpocock/skills/tree/2ab958093e83e0ec752e6c1c5932da465bf23e0c), [`teach`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/teach/SKILL.md), [learning-record format](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/teach/LEARNING-RECORD-FORMAT.md), [`domain-modeling`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/domain-modeling/SKILL.md), [`research`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/research/SKILL.md), and [`handoff`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/handoff/SKILL.md); distinguish deliberate repository artifacts and supersession from automatic general agent memory.
  - Attribute the provenance conclusion exactly: `Prior planning lineage reported direct inspection of the linked primary source bodies; see session evidence agent://ResearchAgentMemorySources, local://github-memory-source-bodies.md, and local://github-memory-sources.md. This executor did not reproduce that inspection.` Keep the durable primary URLs as the portable evidence. State only the reported narrow conclusion that no one inspected source alone supplies automatic cross-session availability, bounded relevance loading, provenance, authority, stale handling, conflict safety, and dependency-free repository persistence; T3 may confirm, narrow, or contradict it.
  - In `Maintenance`, say `WORKFLOW.md` is read only when designing, auditing, or changing the memory system; ordinary tasks use `INDEX.md` plus relevant active records only.
- Create `.agents/memory/FIRST_DRAFT.md` with these exact high-level sections and decisions:
  - `## Status and decision boundary` — provisional baseline for later comparison; not executable authority and not permission to ingest `tmp/`.
  - `## Preferred shape` — `.agents/memory/INDEX.md`, one file per accepted memory, `tmp/`, and `WORKFLOW.md`; avoid one monolithic `MEMORY.md`.
  - `## Three layers` — canonical owning artifacts, durable scoped memory, and ephemeral execution/handoff state.
  - `## Loading interface` — eventual `AGENTS.md` bootstrap of at most a few lines through the repository's declared `alwaysApply: true` surface; it requires every agent/subagent to read `INDEX.md` before non-trivial work and then load only scope-matched records. Linked-file byte transclusion and repository-`AGENTS.md` propagation to subagents are unverified: final implementation must prove them with a live parent/subagent trace or bind the index path explicitly in each child Context Pack without duplicating memory bodies.
  - `## Provisional record shape` — one Markdown file with `id`, `status`, `scope`, `recorded`, `authority`, exact `sources`, and `supersedes`; body contains one claim plus future-agent implication. Label the schema provisional.
  - `## Required invariants` — Markdown/Git only; explicit authority; evidence; canonical-owner precedence; conflict blocking; supersession rather than silent deletion; relevance loading; candidate/promotion separation; transient state and secrets excluded; raw `tmp/` inputs never loaded as active memory; no external service, vector store, embeddings, daemon, or hidden transcript crawler.
  - `## Unresolved scale questions for Atlas` — stale detection and revalidation, incremental update/CAS behavior, index growth/sharding, old-but-active relevance, temporal versus semantic ranking without external retrieval, conflict/concurrency, pruning versus archival, provenance cost, and deterministic rebuild.
  - `## Atlas framework stress test` — start with `Pending`; after T3/T4, record one row per attempted invocation—not merely per command name—with command stub, primary skill, literal raw arguments from the runner receipt, runner/history handle and line anchors, terminal outcome, returned receipts/topic/source/pass/run paths, and `blocker`. Use literal `none` for success. For a refusal, copy its code/detail verbatim; when no formal code exists use `NO_CODE` and the verbatim terminal detail. Treat a safe refusal as evidence, not permission for a workaround.
  - `## Deferred first ingestion` — after the final design and loader are implemented and verified, process every file then present in `tmp/` as the first candidate batch; qualification may merge/reject candidates, but preserve the original raw file as ingestion provenance unless a later approved final policy explicitly authorizes archival or removal.
  - `## Next comparison` — compare this baseline against T3's dated Atlas pass in a later dedicated task; keep the dedicated directory/index preference unless evidence establishes a leaner and equally robust interface.
- In the `.agents/AGENTS.md` layout code block, insert the exact line `  memory/          # provisional memory draft, workflow, index, and raw tmp inputs` beside the existing `.agents/` children so the repository map remains accurate. Do not add the loader instruction, modify `dev-continual-learning`, create a rule/hook/skill, or change `.agents/ARCHITECTURE.md` in this task: the system is deliberately not active until the Atlas comparison selects the final interface, so no durable runtime invariant changes yet.

### T3. Research agent memory through the current Atlas front door

- Use only the checked-in `.agents/commands/atlas-ask.md` wrapper and `skill://atlas-ask`. The main session remains the Atlas Orchestrator; it never calls a Workflow Owner resource, `atlas-core`, the façade, a profile, or `vault://atlas/` directly. The former direct `/atlas-audit`, `/atlas-answer`, `/atlas-index`, `/atlas-source`, `/atlas-research`, `/atlas-refresh`, and `/atlas-migrate` instructions are historical evidence only.
- Keep one ordered receipt per attempted `/atlas-ask` invocation: sequence number, literal raw request in an LF-preserving fenced block, selected owner, exact rendered route overview, approval evidence, retained Task/agent handle, aggregate outcome/effect, compact item summaries, returned topic/pass/run/source paths, and exact blocker or `none`. Record only validated aggregate results from the retained handle; never reconstruct missing owner output from history or Atlas state.
- Plan approval does not approve Atlas I/O. Immediately before each owner dispatch, `/atlas-ask` must render its current exact route overview and receive an unambiguous approval tied to that overview. Before the first dispatch, live-classify strict Task transport as `native`, `contract-equivalent`, or `unavailable`; require strict schema output, retained-handle identity, same-owner messaging, and recursion depth at least 2 for the research → acquire → source/Semantic Worker chain. `unavailable` stops before Atlas/profile/vault/façade I/O.
- Run the following read-only preflight request first. It must classify to `atlas-audit`; any other classification stops for plan reconciliation rather than bypassing the front door.

  ```text
  Audit the bounded Atlas state required for repository-native agent-memory research.
  For `agent-memory`, `lean-self-improving-agent-harness`, and
  `agentic-harness-architecture`, report existence; canonical topic ID, logical
  path, domain, subdomain, title, status, coverage, confidence, freshness, refresh
  model, aliases, include/exclude terms, related-topic IDs, answer-contract scope,
  pending edge IDs, and concrete registry/topic/subdomain findings. Also validate
  the manifest, topic, and relation state reachable from those topics. Read-only:
  do not repair, refresh, create, acquire, ingest, or mutate anything.
  ```

- Preserve every baseline finding. A missing `agent-memory` topic is the expected create branch, not an audit defect. An existing topic is compatible only when its ID/path/domain/subdomain/title, aliases, include/exclude terms, related-topic IDs, active status, `same-as-topic-creation` refresh model, and answer contract match the research boundary below. A target-affecting validation finding or incompatible existing topic blocks before writes. Unrelated findings remain baseline evidence and are neither repaired nor hidden by this plan.
- After the preflight succeeds, run exactly one write-capable research request. It must classify to `atlas-research`; the approved maximum logical write boundary is limited to: absent `agent-memory` topic creation through `index.create_topic`; one bounded acquisition run; source/manifest/relation effects for selected candidates through the research → acquire → source chain; and the `agent-memory` pass, topic index, freshness, relations, and owning subdomain/topic projections. It must not change either related topic's answer, vocabulary, unrelated registry rows, product files, or another topic.

  ```text
  Research repository-native agent memory for a host-owned coding-agent harness,
  with explicit bounded acquisition. If the exact compatible `agent-memory` topic
  is absent, create it before synthesis using only this approved semantic identity:

  Topic ID: agent-memory
  Topic path: vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md
  Domain: agent-systems
  Subdomain: harness
  Canonical title: Agent memory
  Aliases: repository agent memory; coding-agent memory; agent memory setup
  Include: agent memory; coding-agent memory; repository-native memory; persistent
  agent context; long-term agent memory; memory index; memory record; memory
  curation; memory consolidation; memory supersession; stale memory; relevance
  loading
  Exclude: foundation-model memory; model weights; GPU or operating-system memory;
  generic RAG; personal note-taking; uncurated chat/session history; Atlas product
  maintenance
  Related topics: lean-self-improving-agent-harness;
  agentic-harness-architecture
  Status: active
  Initial coverage: insufficient
  Initial confidence: low
  Refresh model: same-as-topic-creation

  If that exact compatible topic already exists, preserve its current answer,
  coverage, confidence, and freshness until this research workflow updates it.
  Stop without writes if the existing identity or answer boundary is incompatible.
  Do not promote vocabulary or tags.

  Evaluate this preferred provisional baseline:
  - Markdown/Git only, with `.agents/memory/INDEX.md`, one file per accepted scoped
    memory, `.agents/memory/tmp/` for untrusted candidates, and `WORKFLOW.md`.
  - Three layers: canonical contracts/code/tests; durable scoped memory only for
    residual cross-run knowledge; ephemeral execution/handoff state.
  - Bounded index-first loading, explicit authority/provenance, conflict blocking,
    supersession instead of silent deletion, candidate/promotion separation, and
    no ordinary loading of `tmp/`.
  - No database, vector store, embeddings, daemon, hidden transcript crawler, or
    external service.
  - Repository `AGENTS.md` injection and subagent propagation remain unverified and
    must be proven before activation.

  Compare that baseline with a monolithic memory document, hierarchical or
  topic-sharded indexes, append-only logs with compacted/materialized indexes, and
  database/vector-backed stores. Evaluate automatic agent/subagent loading,
  context budget, stale or contradictory records, incremental consolidation,
  old-but-active relevance at corpus scale, supersession/archival, provenance and
  authority, concurrent/conflicting writes, deterministic rebuild/rollback,
  repository portability, maintenance cost, and dependency cost. Prefer the
  provisional baseline unless cited Atlas evidence establishes a leaner or more
  robust setup without a worse authority, portability, or operational boundary.
  State every supported refinement, contradiction, rejected alternative, and
  unresolved gap. Do not implement or activate the repository memory system.

  Acquisition scope kind: query
  Acquisition identifier: repository-native agent memory for a host-owned coding
  agent harness, bounded loading, stale-memory handling, incremental consolidation,
  long-tail relevance, provenance/authority, and conflict-safe updates
  Positive limit after canonicalization and deduplication: 20

  Fixed primary/source-backed references:
  - https://cursor.com/blog/agent-swarm-model-economics
  - https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/continual-learning/README.md
  - https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/continual-learning/agents/agents-memory-updater.md
  - https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/continual-learning/hooks/continual-learning-stop.ts
  - https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/reflect/SKILL.md
  - https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/recall/SKILL.md
  - https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/automate-me/SKILL.md
  - https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/setup-matt-pocock-skills/SKILL.md
  - https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/domain-modeling/SKILL.md
  - https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/research/SKILL.md
  - https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/handoff/SKILL.md
  - https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/teach/SKILL.md
  - https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/teach/LEARNING-RECORD-FORMAT.md

  Consider at most 16 additional primary/source-backed candidates. Rank them by
  uncovered-criterion coverage, submit at most the strongest seven so the selected
  fixed-plus-additional cohort remains within 20, and record every considered but
  unsubmitted candidate as overflow. Do not substitute listicles, generic RAG
  prose, prior local excerpts, or model memory for materialized Atlas evidence.
  ```

- The research pass must account for every fixed and considered additional reference in an ordered coverage ledger with: origin, additional-candidate rank or `n/a`, submitted state, raw reference, normalization outcome, canonical source/artifact or `none`, included/excluded/blocked/overflow disposition, exact reason, supported or unreviewed claims, and source ID/artifact path or `none`. It must report the acquisition run, topic path, dated pass path, counts by origin/disposition, ranked additions/overflow, any displacement, ordered materialized source IDs/artifact paths, and explicit insufficiencies.
- Honor only owner-native `needs-user`/`needs-guidance` resumes and allowlisted Successor Owners on the retained handle and within the schema ceilings. A `blocked`, `framework-defect`, partial/unknown effect, stale binding, missing required receipt, or incompatible state stops T3 under the current aggregate-result policy. Do not dispatch a generic verifier, infer success from owner prose, or manually inspect/repair living state. T3 completes only when the validated research aggregate returns the exact topic and pass paths plus the complete coverage receipt and leaves the target in a state eligible for a current answer.

### T4. Refine and verify the provisional memory proposal

- Through a separately approved `/atlas-ask` route, run this read-only final answer request. It must classify to `atlas-answer` and return a `current` answer with source-artifact citations:

  ```text
  Return the current `agent-memory` answer, recommendation matrix, caveats,
  evidence map, gaps, and read-next links. Explicitly compare the preferred
  repository Markdown/index/per-record baseline with the researched alternatives,
  and identify which baseline decisions are supported, contradicted, or still
  unproven. Read-only; do not refresh or mutate anything.
  ```

- If the answer returns a deterministic freshness halt, do not read around it. At most once, present and obtain approval for a new explicit `/atlas-ask` refresh route for the complete pending `agent-memory` set, then repeat the answer request under a fresh approved read-only route. Any second halt or nonterminal/ambiguous refresh effect blocks T4.
- Through another separately approved read-only `/atlas-ask` route, run a final `atlas-audit` request resolved with the actual pass path, materialized source IDs, and complete coverage receipt:

  ```text
  Audit <exact-agent-memory-pass-path> and the `agent-memory` topic, relation,
  freshness, and owning-subdomain projections. Run bounded source-quality audit
  for these materialized source IDs: <ordered-source-ids>.
  Compare the pass's ordered coverage ledger with this expected receipt verbatim:
  <exact-complete-research-coverage-receipt>
  Report clean/issue status, finding counts, concrete paths/anchors, missing,
  extra, or changed ledger fields, and any new target-reachable registry finding
  relative to the recorded baseline audit. Read-only; do not repair anything.
  ```

- Require exact coverage-ledger agreement, no unresolved target/source-quality finding, and no new target-reachable registry finding relative to the baseline. Preserve unrelated baseline findings as residual evidence; do not widen this plan into repair.
- Compare the accepted Atlas answer/pass against `.agents/memory/FIRST_DRAFT.md`, `WORKFLOW.md`, and `INDEX.md`. Keep the directory/index/per-record baseline unless cited Atlas evidence establishes a better setup under the user's stated preference. Update only provisional design text and research links:
  - In `FIRST_DRAFT.md`, record the accepted topic/pass/answer evidence, a criterion-by-criterion comparison, supported and rejected refinements, unresolved proof gaps, and one coherent final proposed setup. Preserve the provisional status, dependency-free default, and explicit unverified loader/subagent-propagation gate unless evidence directly changes them.
  - In `WORKFLOW.md`, revise lifecycle, ownership, invariants, or maintenance only where the accepted evidence warrants it; keep canonical contracts/code/tests ahead of residual memory and keep `tmp/` outside ordinary loading.
  - In `INDEX.md`, replace only the pending research-comparison line with exact accepted topic/pass links and keep `Active memory map` at `None`.
  - Do not modify `.agents/memory/tmp/2026-08-02-atlas-evidence-date-seam.md`, activate a loader, promote a memory, create a rule/skill/hook, change `.agents/ARCHITECTURE.md`, or implement any proposed mechanism.
- Populate `FIRST_DRAFT.md`'s stress-test table with one row per attempted `/atlas-ask` invocation using the recorded wrapper/owner/overview/approval/handle/result receipt. A safe stop records the exact aggregate blocker and leaves T3/T4 unchecked; never invent a legacy command code.
- Run `python3 scripts/atlas-instance.py check` after the repository proposal edits. It must exit zero and print `check OK`; this package check is separate from the owner-native Atlas evidence and must not mutate living state.
- Present the final proposed setup, evidence-backed deviations from the initial draft, unresolved risks, and explicit non-implementation state. Then stop with a short handoff naming a fresh-session `grill-with-docs` refinement as the mandatory next gate. Only after that presentation and every criterion below passes may T3/T4 be completed, the plan marked `DONE`, summarized, synchronized, and archived.

## Critical files & anchors

- `.agents/commands/atlas-ask.md` and `skill://atlas-ask` — sole public wrapper, classification, route approval, strict Task dispatch, and aggregate-result consumption.
- `skill://atlas-ask/owners/atlas-audit/OWNER.md` — read-only baseline/final state and bounded source-quality checks.
- `skill://atlas-ask/owners/atlas-research/OWNER.md` — vault-only/acquire modes, absent-topic creation, acquisition and refresh successor chains, and topic/pass output.
- `skill://atlas-ask/owners/atlas-answer/OWNER.md` — current-only answer and deterministic freshness halt.
- `skill://atlas-core/assets/operating-cadence-and-guardrails.md` and `atlas-workflow-result.schema.json` — approval, capability, retry, resume, effect, and closed aggregate-result rules.
- `.agents/ARCHITECTURE.md:14-69,160-210` — product/instance boundary, singular runtime flow, canonical living state, and topic-creation/research effects.
- `.agents/memory/{INDEX.md,FIRST_DRAFT.md,WORKFLOW.md}` — provisional product-side comparison and proposal targets; `.agents/memory/tmp/2026-08-02-atlas-evidence-date-seam.md` remains immutable raw input in this recovery.
- `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md` — dedicated living research target, reachable only through the approved owner route.

## Verification / Done criteria

- [ ] `read .agents/memory` lists only the four planned Markdown targets, each with the exact provisional-plan marker; the temporary lesson hash remains `c94f3d05561acbf5cf4a58457474e77bf5207413a38d891f5042787e08f461cb`.
- [ ] `read .agents/memory/INDEX.md` shows no active memory, excludes `tmp/` from ordinary loading, and links only the accepted `agent-memory` topic/pass as research comparison evidence.
- [ ] `read .agents/memory/WORKFLOW.md` retains the seven planned sections, candidate-to-supersession lifecycle, one-owner mapping, canonical-owner precedence, bounded loading, and maintenance guidance; every research-driven change is source-cited.
- [ ] `read .agents/memory/FIRST_DRAFT.md` shows the preferred directory/index/per-record baseline, three layers, dependency-free invariant, provisional record shape, unverified injection caveat, full Atlas comparison, one trace-backed row per attempted `/atlas-ask` invocation, and one final proposed setup without activation.
- [ ] `read .agents/AGENTS.md:26-38` still shows only the provisional `memory/` layout entry; there is no active loader, learned-bullet section, memory body, rule, skill, hook, or architecture change from T3/T4.
- [ ] Every Atlas attempt enters through `.agents/commands/atlas-ask.md`, records one approved overview and retained strict Task handle, validates one schema-owned aggregate result, and performs no direct owner/core/profile/vault/façade I/O in the Orchestrator.
- [ ] The live capability gate reports strict Task transport, retained-handle identity, same-owner messaging, and required recursion depth as `native` or proven contract-equivalent before owner work; unavailable capability stops with no Atlas effect.
- [ ] The initial `atlas-audit` aggregate records current bounded state and exact baseline findings for `agent-memory` and both related topics; an absent target is distinguished from an incompatible or invalid target.
- [ ] The `atlas-research` aggregate either confirms the exact compatible topic or creates it through `index.create_topic`, keeps the logical write boundary exact, and returns its topic path, dated pass path, mode, acquisition run, and ordered materialized source artifacts.
- [ ] The research coverage ledger accounts for all 13 fixed references and at most 16 considered additions, selects at most seven additions and at most 20 normalized positives, exposes every required field, and records ranked overflow/displacement and unsupported gaps without raw-web/model substitution.
- [ ] Any owner-native acquire/source/refresh successor and same-owner resume stays on the retained root binding, within the approved boundary and schema ceilings, and ends with a terminal known effect; no generic verifier or legacy owner command substitutes for the aggregate result.
- [ ] The final `atlas-answer` aggregate returns a `current` evidence-cited answer and explicit baseline comparison; no stale topic content is read around a freshness halt.
- [ ] The final `atlas-audit` aggregate reports exact pass-ledger agreement, bounded source-quality results for every materialized source ID, no unresolved target finding, and no new target-reachable registry finding relative to the baseline.
- [ ] Direct comparison preserves the first-draft setup unless cited Atlas evidence proves a better boundary, records every accepted/rejected refinement and remaining proof gap, and leaves the system provisional, inactive, and un-ingested.
- [ ] From `/Users/kim/dev/atlas/app`, `python3 scripts/atlas-instance.py check` exits zero and prints `check OK` after the proposal edits.
- [ ] T1–T4 rows use the checked-plus-UTC-`Completed:` form, `## Completion Summary` records the final proposal/evidence/residual risks and `grill-with-docs` gate, final `Status` is `DONE`, and the byte-exact plan projection is archived only after all prior criteria pass.

## Assumptions & contingencies

- `.agents/memory/tmp/` is intentionally repository-visible: planning found no applicable `.gitignore` rule. Do not add one. Redact isolated sensitive values exactly as T1 specifies; if safe intelligible redaction is impossible, block T1 rather than persist the raw lesson.
- The dedicated-topic decision remains fixed: `lean-self-improving-agent-harness` and `agentic-harness-architecture` are related context, not fallback owners. An incompatible existing `agent-memory` topic blocks before acquisition or research writes; do not merge, rename, repurpose, or bypass it.
- A validated aggregate `blocked`, `framework-defect`, partial/unknown effect, stale binding, unavailable capability, or missing required receipt stops the affected task under the current guardrail. Only a separately approved `dev-ask` Engineering Cycle may address a proven product defect; no legacy command, direct core call, manual vault inspection, or ad hoc retry is permitted.
- Owner-native `needs-user` and `needs-guidance` resumes preserve the same handle/binding and exact answer sets. A new material choice, owner, mode, safety condition, authority, or logical write boundary requires a fresh `/atlas-ask` overview and approval.
- Unavailable, archived, rejected, duplicate, or insufficient sources remain explicit coverage gaps. Continue only with owner-validated materialized evidence; never replace a required source with prior `local://` excerpts, raw web content, listicles, or model knowledge.
- Research insufficiency is acceptable when honestly recorded; fabricated completeness is not. The first-draft directory/index preference wins ties and remains unchanged unless cited evidence proves a materially better authority, loading, portability, conflict, or maintenance boundary.
- `.agents/memory/**` remains provisional product documentation. T4 may refine only `INDEX.md`, `FIRST_DRAFT.md`, and `WORKFLOW.md`; it never modifies `tmp/`, activates loading, promotes records, or grants implementation authority.
- Completion of this plan ends at an evidence-backed proposal and handoff. A fresh-session explicit `grill-with-docs` refinement and later separately approved implementation route are mandatory before any memory-system activation.



## Attempt 1 Blocker Handoff

**Settled:** 2026-08-02T09:58:36Z

- **Completed scope:** T1 and T2. Created `.agents/memory/tmp/2026-08-02-atlas-evidence-date-seam.md`, `.agents/memory/INDEX.md`, `.agents/memory/WORKFLOW.md`, and `.agents/memory/FIRST_DRAFT.md`; added only the provisional `memory/` layout row to `.agents/AGENTS.md`.
- **Blocked scope:** T3 and T4 remain unchecked and `Status` remains `IN_PROGRESS`.
- **Exact blocker:** `/atlas-index` `NO_CODE`: Unsupported multi-target topic creation: the exact multi-target write set has no applicable core transaction contract; halt for a contract extension or explicit migration rather than hand-rolling a transaction or rollback.
- **Atlas effects:** none. One checked-in-interface runner completed an initial `/atlas-audit`, three bounded `/atlas-answer` reuse assessments, and `/atlas-index` preflight, then stopped before any write. No source, run, pass, topic, receipt, successor, transaction, recovery, refresh, relation, or registry effect was created.
- **Receipts:** `local://atlas-skill-interface-run-receipt.md`, SHA-256 `0ba2aa78361006b9ef57efa4d475a35c1cdeea803a02ce54d2297d6c6e403561`; runner `history://AtlasSkillInterfaceRun`, settled receipt line 237 and correction line 255.
- **Independent verification:** `agent://VerifyMemorySafeBlock` returned `VERIFIED_SAFE_BLOCK`; all repository-target hashes matched, the dedicated topic remained absent, the manifest/registry revisions matched the runner correction, and no attributable source/run/pass existed.
- **Parent integration check:** `python3 scripts/atlas-instance.py check` exited zero and printed `check OK`, `instances: atlas`, `product_owned entries: 1`, and `seed_once templates: 7`.
- **Parent review:** no standards finding in the completed repository artifacts or safe-refusal capture. T1/T2 satisfy their specification; the full plan is not complete because T3/T4 success-path acceptance is unreachable at the missing transaction seam.
- **Residual state:** `.agents/memory/` is provisional and inactive; `tmp/` is un-ingested; no loader or promoted record exists. Two pre-existing `SUBDOMAIN_TOPIC_MAP_DRIFT` findings and dirty related topics remain outside this attempt's write set.
- **Resume condition:** an approved Atlas framework contract extension or explicit migration must provide the exact multi-target `agent-memory` topic-creation effect. Then resume this same plan at the row-5 `/atlas-index` request through its checked-in command/skill interface; do not redo T1/T2 or bypass with direct core I/O.
- **Next owner:** human/Atlas framework architect for the contract or migration decision, then Main for a new revision-bound execution attempt.

## Recovery Reconciliation — 2026-08-04

**Reconciled:** 2026-08-04T06:51:59Z
**Current stage:** `IN_PROGRESS`; T1/T2 complete, T3 attempt 1 ended in an independently verified safe block and has not resumed, T4 not started.
**Resume state:** `PREREQUISITE_SATISFIED; PLAN_RECONCILIATION_REQUIRED`.

- The former multi-target topic-creation prerequisite is complete in the final independently verified and approved Atlas framework target `/tmp/atlas-framework-final-immutable-target.txt`, SHA-256 `c64adfc6eb95779605ff306763c695285c3497943374912bd1a36a6c61344178`. This closes only the framework prerequisite; it does not complete T3 or T4 and does not prove that an `agent-memory` topic or research pass exists.
- The historical T3/T4 execution contract names former public `/atlas-audit`, `/atlas-answer`, `/atlas-index`, `/atlas-source`, `/atlas-research`, and `/atlas-migrate` interfaces. The current package exposes only `/atlas-ask`; a fresh session must revise and reapprove T3/T4 against the current owner paths before any Atlas I/O. Do not execute the legacy checklist verbatim.
- Preserve all T1/T2 outcomes and historical blocker evidence. Do not redo T1/T2. `.agents/memory/tmp/` is externally maintained raw input; do not modify it during recovery.
- This reconciliation restores plan authority and records the exact recovery point only. It authorizes no topic creation, acquisition, research, vault mutation, agent-memory implementation, loader activation, or promotion.
- **Next owner:** a fresh-session plan recovery owner. First revalidate the current `/atlas-ask` capability and Atlas state, then revise only T3/T4 and their verification criteria, obtain approval, and continue. The user intends to review the resulting refined setup with an explicit `grill-with-docs` stage before implementation.

## T3/T4 Execution Contract Revision — 2026-08-04

**Revised:** 2026-08-04T07:06:02Z
**Resume state:** `AWAITING_PLAN_AND_ATLAS_PREFLIGHT_APPROVAL`

- Replaced only the prospective T3/T4 execution contract, their supporting anchors/contingencies, and their verification criteria. T1/T2 outcomes, Attempt 1 evidence, and the temporary lesson remain unchanged.
- Revalidated the checked-in singular `/atlas-ask` surface, nine internal owner IDs, strict result schema, current research absent-topic creation path, and harness-declared strict Task/handle capabilities without Atlas I/O. Live transport/depth verification and living Atlas state inspection remain gated by the first approved route.
- Collapsed the former legacy command sequence into four bounded front-door intents: baseline audit; one acquisition-enabled research workflow that can create the absent exact topic and use native successor chains; final current answer; final bounded audit. Any freshness recovery is a separately approved conditional route.
- Preserved the user's design preference: the repository Markdown/index/per-record first draft remains the default unless materialized Atlas evidence proves a better setup. The terminal deliverable is a refined inactive proposal followed by a `grill-with-docs` handoff, never implementation or activation.

