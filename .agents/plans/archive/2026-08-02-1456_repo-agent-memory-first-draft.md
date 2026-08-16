# Repository Agent Memory First Draft

**Datetime**: 2026-08-02-1456
**Authority kind**: local-authority
**Scope**: Repository-native agent-memory first-draft artifacts and bounded Atlas acquisition/research
**Summary**: Preserve this session's raw lessons, establish the preferred directory-indexed memory draft and workflow context, and run bounded Atlas acquisition/research before any final memory architecture or ingestion is chosen.
**Status**: CLOSED

## Context

T1/T2 already preserved the raw lesson and established an inactive Markdown/index/per-record memory baseline; T3/T4 still must research, compare, refine, and present that proposal without implementing it. The strict Task defect was repaired and fully assured in `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949`, but the installed OMP was intentionally left unchanged and a reset installed-session smoke still reproduces the old schema-preflight failure. Resume only from a fresh OMP process launched directly from the verified checkout, then use the sole `/atlas-ask` front door for the bounded audit, acquisition-enabled research, current answer, and final audit. The final repository state remains provisional and inactive, preserves `.agents/memory/tmp/` byte-for-byte, and pauses for a fresh-session `grill-with-docs` refinement before any implementation.

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

- Execute this plan only in a fresh OMP process launched directly from the verified checkout with `bun --cwd=/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent src/cli.ts --cwd /Users/kim/dev/atlas/app`. Do not install, link, or replace the shared `omp` command.
- Before any `/atlas-ask` route, require SHA-256 `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db` for `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent/src/tools/jtd-to-json-schema.ts`, then run one no-effect live Task smoke with the complete `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json`, `schemaMode: strict`, and the exact valid `no-write` object from `.agents/plans/archive/2026-08-04-1949_strict-task-schema-transport-repair.md:225-246`. The smoke passes only when preflight creates a Task handle and the strict result returns; the literal `Invalid strict caller output schema: invalid JSON schema` is failure.
- If that repaired-process smoke fails, stop before Atlas/profile/vault/façade I/O and report the launched command, normalizer hash, schema hash, and exact Task result. Do not retry through the installed OMP, weaken the schema, reinstall/link the checkout, or bypass `/atlas-ask`.
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

- `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent/src/tools/jtd-to-json-schema.ts` — verified repaired normalizer whose live process must own Task preflight.
- `.agents/commands/atlas-ask.md` and `.agents/skills/atlas-ask/SKILL.md` — sole public wrapper, route approval, strict dispatch, and aggregate-result boundary.
- `.agents/skills/atlas-ask/owners/{atlas-audit,atlas-research,atlas-answer}/OWNER.md` — exact preflight, acquisition/research, current-answer, and final-audit procedures.
- `.agents/skills/atlas-core/assets/{operating-cadence-and-guardrails.md,atlas-workflow-result.schema.json}` — capability, approval, outcome, resume, and failure rules.
- `.agents/memory/{INDEX.md,FIRST_DRAFT.md,WORKFLOW.md}` — inactive proposal and evidence-comparison targets; `tmp/2026-08-02-atlas-evidence-date-seam.md` is immutable input.

## Verification / Done criteria

- [ ] `read .agents/memory` lists only the four planned Markdown targets, each with the exact provisional-plan marker; the temporary lesson hash remains `c94f3d05561acbf5cf4a58457474e77bf5207413a38d891f5042787e08f461cb`.
- [ ] `read .agents/memory/INDEX.md` shows no active memory, excludes `tmp/` from ordinary loading, and links only the accepted `agent-memory` topic/pass as research comparison evidence.
- [ ] `read .agents/memory/WORKFLOW.md` retains the seven planned sections, candidate-to-supersession lifecycle, one-owner mapping, canonical-owner precedence, bounded loading, and maintenance guidance; every research-driven change is source-cited.
- [ ] `read .agents/memory/FIRST_DRAFT.md` shows the preferred directory/index/per-record baseline, three layers, dependency-free invariant, provisional record shape, unverified injection caveat, full Atlas comparison, one trace-backed row per attempted `/atlas-ask` invocation, and one final proposed setup without activation.
- [ ] `read .agents/AGENTS.md:26-38` still shows only the provisional `memory/` layout entry; there is no active loader, learned-bullet section, memory body, rule, skill, hook, or architecture change from T3/T4.
- [ ] The executing OMP process was launched by the exact repaired-checkout command in T3, the normalizer hash is `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`, and the complete-schema live Task smoke creates a handle and returns the exact strict `no-write` payload before any Atlas I/O.
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
- The selected activation is direct execution from the verified checkout, not installation/linking. If the process identity or normalizer hash does not match, stop and relaunch with the exact T3 command; never mutate the shared installed OMP as an in-plan fallback.
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


## Attempt 2 Capability Blocker Handoff

**Settled:** 2026-08-04T09:36:26Z

- **Completed scope:** Reconciled and reapproved the current T3/T4 contract, synchronized it through `plan-artifact-sync`, removed only this plan identity from the repository stale-plan gate, revalidated the current front-door/architecture/guardrail/schema/audit-owner bindings, and recorded Attempt 2 in `.agents/memory/FIRST_DRAFT.md` and `INDEX.md`.
- **Blocked scope:** T3 and T4 remain unchecked and `Status` remains `IN_PROGRESS`. Living Atlas state was not inspected; topic creation, acquisition, research, final answer/audit, proposal refinement, and presentation did not start.
- **Exact blocker:** `/atlas-ask` `capability-unavailable`: `Task AuditAgentMemoryState failed preflight: Invalid strict caller output schema: invalid JSON schema`.
- **Transport evidence:** Dispatch `1B74B00E-DCBF-4ED4-A405-9C2B50A90E40` used the checked-in workflow-result schema at `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad` with `schemaMode: strict`. Task preflight returned `results: []` and `totalDurationMs: 0`; no Task/agent handle existed. The schema parsed as JSON; the local Python environment lacked the optional `jsonschema` package for a separate Draft 2020-12 meta-schema check.
- **Bound product revisions:** architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`.
- **Atlas effects:** none. No owner, profile, vault, façade, reducer, transaction, recovery, topic, source, run, pass, relation, or registry operation ran.
- **No fallback:** Per the current capability boundary, no permissive schema, simplified prompt schema, prose parsing, direct owner invocation, manual vault inspection, or compatibility bypass was attempted.
- **Resume condition:** strict Task transport must accept and enforce the complete checked-in workflow-result contract, or a proven contract-equivalent transport must validate that same complete result before consumption. Then revalidate current product revisions and obtain a fresh `/atlas-ask` route approval before dispatch.
- **Next owner:** human/harness capability owner or separately authorized engineering route for the strict-schema transport mismatch; then Main for a fresh plan attempt.

## Strict Task Source Repair Evidence

**Settled:** 2026-08-04T15:34:47Z

- **Source identity:** external checkout `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949`, OMP tag `v17.2.7`, commit `a5090f1f81cf0ac072fbd1ec949eebe6bbbc23a9`; the installed `omp/17.2.7` binary was not replaced, linked, or activated.
- **Native provenance:** public `@oh-my-pi/pi-natives-darwin-arm64@17.2.7` registry artifact, integrity `sha512-eIvz6ZzHEnUyBPRfoLdXOf/VhvbUgcCp5V5YCeqVz+sEQ+AJjOyDl9ayjTIHR/2spnEJ6zgl4F7Xr/c/sMhWJQ==`, SHA-1 `1f8de55f4d1760e5e91b85460d63d34dd1074906`; copied checkout-local addon SHA-256 `67de42fe9e7aa9c2c5e3a817f2b9f0c6b87e7252b8e3a3da1d9beb86e076055c`.
- **Verified target digests:** normalizer `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; normalizer tests `dfc353ec75040fae7951e8b1a64f77fb66c8b83f58e73ec10ea556de63e4cf64`; validator tests `2349c7a35a361e6aaa8bc839ecd3e2b58f22c53f74bf67f8b7e38c548f808a14`; structured-subagent tests `f08aacc4bb7f5d1fd5fcc83224bf866408fa04572611d809be7de2d80c96c0d6`; user-config-isolated LSP regression `14acc6156ad7dced762945764e42fc2966c4d5242ccc749690b6f7adfb7e0e4a`; complete fixture `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; generated tool-view prerequisite `abf8a665d3ae62ecc74b7bc6da4a7f4706cfbb2b52a4344a53a995d10b9127ef`.
- **Focused and smoke evidence:** normalizer `9/9`, validator `14/14`, structured-subagent `19/19`, complete LSP file `76/76`, and typecheck passed; direct source smoke printed `strict-schema-transport OK`; pure/unambiguous JTD, minimal native `$defs.ref`, copy-on-write, malformed fail-closed, complete strict-preflight dispatch, and valid/invalid workflow-result tuple controls passed. The canonical Atlas schema and copied fixture remain byte-identical at SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`.
- **Package evidence:** the user-authorized revised package run recorded `11,712` passes, `404` skips, and only the unrelated five-second collab tombstone timeout; that exact case passed in isolation and was explicitly accepted as a confirmed full-suite flake. Pre/post target manifests were identical.
- **Independent assurance:** `agent://StrictSchemaVerifier` returned `VERIFIED`; distinct `agent://StrictSchemaReviewer` returned Standards `PASS`, Specification `PASS`, Overall `APPROVED`, with model-family decorrelation unavailable as an explicit residual; `agent://StrictSchemaCurator` returned `NO DURABLE LEARNING`. No assurance role changed the target.
- **No-effect boundary:** no Atlas/profile/vault/façade/owner/reducer/transaction/topic/source/run/pass/relation/registry operation occurred; no commit, stage, push, deploy, release, harness install, replacement, or activation occurred.
- **Blocked scope remains unchanged:** T3 and T4 remain unchecked and `Status` remains `IN_PROGRESS`.
- **Remaining resume condition:** activate a verified harness build under separate authority, start a fresh OMP session, revalidate current Atlas product revisions, and obtain a new `/atlas-ask` audit route approval.

## Post-reset Live Transport Recheck

**Checked:** 2026-08-04T15:57:11Z

- The reset OMP session was tested with the complete checked-in workflow-result schema, `schemaMode: strict`, and a static valid `no-write` result requiring no file, Atlas, profile, vault, façade, network, shell, or test access.
- Live Task preflight still returned `Task StrictSchemaResetSmoke failed preflight: Invalid strict caller output schema: invalid JSON schema`, with `results: []` and `totalDurationMs: 0`.
- No Task handle or external effect was created. The reset session therefore is not executing the verified repaired schema-normalization path recorded above.
- Execution remains gated on launching a fresh Atlas session from the repaired checkout or separately authorizing installation/linking of that checkout; a plain reset of the installed OMP session is insufficient.
- **Selected activation:** launch the fresh continuation directly from the verified checkout using the exact T3 command; leave the installed/shared OMP untouched.



## Attempt 3 Aggregate-Validation Blocker Handoff

**Settled:** 2026-08-04T17:10:46Z

- **Completed scope:** Reverified T1/T2 without modifying the raw input; launched a fresh OMP v17.2.7 process with the exact repaired-checkout command; confirmed normalizer SHA-256 `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db` and complete workflow-result schema SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; and completed the full-schema `schemaMode: strict` no-effect smoke with returned handle `agent://StrictTaskNoEffectSmoke` and the exact valid `no-write` payload.
- **Route evidence:** The baseline request classified to `atlas-audit`. The Orchestrator rendered the exact read-only route overview and the user selected `Approve` for that unchanged overview. Dispatch `5e04c4c1-efda-4259-9ef3-33498d266863` bound architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`, guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`, result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`, and audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`.
- **Blocked scope:** T3 and T4 remain unchecked and `Status` remains `IN_PROGRESS`. No baseline aggregate was consumed; research, acquisition, topic creation, final answer/audit, and proposal refinement did not run.
- **Exact blocker:** `capability-unavailable: retained atlas-audit Task result failed complete strict aggregate validation: dispatch.guardrail_revision: must match pattern`.
- **Returned-handle evidence:** The strict Task execution was visible under label `AuditAgentMemoryState`, but `agent(...)` threw `schema_violation` before returning its handle object. The returned delivery handle is therefore `none`; the label is not consumed as a retained handle.
- **Atlas effects:** The approved route was read-only. The Orchestrator accepted no owner result and performed no direct Atlas/profile/vault/façade/reducer/transaction operation or write. No validated topic, source, run, pass, relation, registry, or baseline finding is available from this attempt.
- **Repository evidence:** `.agents/memory/FIRST_DRAFT.md` records Row 7 without reconstructing the rejected payload. `.agents/memory/INDEX.md` records the terminal comparison blocker. The raw temporary lesson remains unchanged at SHA-256 `c94f3d05561acbf5cf4a58457474e77bf5207413a38d891f5042787e08f461cb`. Post-edit `python3 scripts/atlas-instance.py check` exited zero and printed `check OK`.
- **No fallback:** Per the aggregate-result boundary, no rejected owner payload, agent history, living state, direct owner/core/profile/vault/façade call, permissive schema, prompt parsing, legacy command, or research dispatch substituted for the missing valid aggregate.
- **Discarded route draft:** After the aggregate failure, the repaired process drafted an `atlas-research` overview internally but did not present it to the user. It created no valid `/atlas-ask` invocation, approval, Task, or Atlas effect and is not resumable or recorded as an attempted invocation row.
- **Resume condition:** A fresh process must revalidate the complete strict transport and current product revisions, render a new baseline-audit overview, obtain new approval, and return one complete schema-valid audit aggregate plus a returned retained handle. The current approval and rejected execution cannot be resumed or reused.
- **Next owner:** human/harness capability owner if the strict binding failure is reproducible; otherwise Main for a fresh approved baseline-audit attempt after this blocker is reconciled into the current plan authority.
## Attempt 4 Validated Baseline-Audit Receipt — 2026-08-04

**Settled:** 2026-08-04T18:08:34Z

- **Completed scope:** Reverified the exact repaired OMP process identity from daemon metadata and live PID, confirmed the exact launch command `bun --cwd=/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent src/cli.ts --cwd /Users/kim/dev/atlas/app`, verified normalizer SHA-256 `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db` and complete workflow-result schema SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`, and completed the no-effect `schemaMode: strict` smoke with returned handle `agent://StrictTaskNoEffectSmoke` and the exact valid `no-write` payload.
- **Route evidence:** The plan's baseline request classified to `atlas-audit`. The Orchestrator rendered the exact read-only route overview and the user selected `Approve` for that unchanged overview.
- **Dispatch binding:** `dispatch-atlas-audit-2026-08-05-fresh-1`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`; every returned dispatch field matched exactly.
- **Returned handle and aggregate:** `agent://AuditAgentMemoryState`; schema-valid outcome `no-write`; aggregate effect `none`; one item `atlas-audit.bounded-state` with status `no-write`; blocker `none`.
- **Validated baseline findings:** `agent-memory` is absent; the related topics exist at their canonical paths, are active/sufficient/medium, and are dirty with 9 and 30 pending edge IDs; state validation returned no malformed table placement, duplicate/invalid IDs, enum/hash/path disagreement, cache disagreement, or provenance issue; finding counts were `TOPIC_NOT_REGISTERED=1`, `SUBDOMAIN_TOPIC_MAP_DRIFT=3`, `SUBDOMAIN_COVERAGE_MAP_DRIFT=3`, and `LEFTOVER_FIXTURE_ARTIFACTS=1`. The complete aggregate summary and all pending IDs/anchors are preserved in `local://atlas-baseline-audit-receipt.json`.
- **Atlas effects:** The selected route was read-only. No research, acquisition, topic creation, source, pass, relation, registry, profile, façade, reducer, transaction, recovery, or repository-memory mutation was dispatched or consumed.
- **Resume condition:** Render the exact acquisition-enabled `atlas-research` route overview below, then stop pending a separately relayed approval; do not dispatch research under the baseline-audit approval.

## Attempt 5 Blocked Acquisition-Enabled Research — 2026-08-05

**Settled:** 2026-08-05T02:28:30Z

- **Completed scope:** Revalidated the repaired process and complete strict transport, rendered the exact acquisition-enabled `atlas-research` route, received the user's `Approve`, dispatched one strict `atlas-research` Task, validated the returned aggregate, and preserved the ordered receipt.
- **Dispatch binding:** `dispatch-atlas-research-2026-08-05-fresh-1`; returned handle `agent://ResearchAgentMemory`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; research owner `sha256:b4741629c88c4b9981ffc45af67afb650987887e5a4a515b284bc57e5a45e06d`; every returned binding field matched exactly.
- **Aggregate:** schema-valid `blocked`, aggregate effect `none`; items `agent-memory-topic-create` (`blocked`) and `bounded-acquisition-and-research` (`no-write`); blocker kind `owner`; guidance `null`; defects `[]`; learning candidate `null`.
- **Exact blocker:** `SUBDOMAIN_PROJECTION_INVALID` before intent or any write because `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` contains noncanonical `[Open](topics/agentic-harness-architecture/INDEX.md)`; `index.create_topic` stopped before acquisition.
- **Effects:** topic creation, acquisition, synthesis, source, pass, run, relation, registry, projection, profile, façade, and repository-memory effects were all absent. Source manifest remained `unchanged` at `sha256:ea4f4c8b64185bb1927739d5cba91fbf079daaa039ad57ebb307da8f3e69ac1a`; relations remained `unchanged` at `sha256:aabc9dacef7991a7e58508b3bb5c49f1d7069c237bee954971c5603e8172d2a6`.
- **Receipt:** `local://atlas-research-blocked-receipt.json`; projection path/revision `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` / `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6`; current answer not eligible; no citations, run paths, pass paths, or source artifacts.
- **Resume condition:** Separately approve a registry/projection repair that canonicalizes the existing harness subdomain topic-map links without changing either related topic's answer or vocabulary. Then run a fresh `/atlas-ask` research dispatch to rerun the approved topic-create gate. This blocked attempt cannot resume into acquisition.
- **Plan state:** T3 and T4 remain incomplete; no direct Orchestrator Atlas/profile/vault/façade/owner I/O occurred. The next owner route is not approved or dispatched.


## Attempt 6 Blocked Projection Repair — 2026-08-05

**Settled:** 2026-08-05

- **Completed scope:** Revalidated the exact approved `atlas-index` repair overview from `local://atlas-repair-route-overview.txt`, verified the repaired OMP process and complete strict transport, completed the no-effect strict smoke, dispatched exactly one strict `atlas-index` Task, validated the complete aggregate from retained handle `agent://AtlasIndexRepair`, and preserved ordered receipt `local://atlas-index-repair-receipt.json`.
- **Dispatch binding:** `dispatch-atlas-index-2026-08-05-repair-1`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; atlas-index owner `sha256:7c62ee5c86b6c0fb0b044c759e6edf7092e813502f2fb72d5aeef03c1c7da2ce`; every returned binding field matched exactly.
- **Aggregate:** schema-valid `blocked`, aggregate effect `none`; item `atlas-index-topic-map-repair` (`blocked`); blocker kind `capability`; guidance `null`; defects `[]`; learning candidate `null`.
- **Exact blocker:** No advertised owner-native façade operation supports canonicalizing existing subdomain topic-map links. `index.create_topic` and `index.recover_topic` are not repair operations, and the owner contract's `repair-table-placement` and `repair-relation-notes` events do not apply. No mutation, conditional replace, transaction, or façade receipt was issued.
- **Before/after:** `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` remained `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6`; touched targets `[]`. Protected revisions and complete tree digests are preserved in `local://atlas-index-repair-receipt.json`.
- **Plan state:** T3 and T4 remain incomplete. The repair did not succeed, so no fresh research retry overview was rendered or dispatched. No direct Orchestrator Atlas/profile/vault/façade/owner I/O occurred.

## Attempt 7 Completed Link-Cell Migration — 2026-08-05

**Settled:** 2026-08-05

- **Completed scope:** Revalidated the exact approved `atlas-migrate` overview from `local://atlas-projection-migration-route-overview.txt`, verified repaired strict transport, completed the no-effect strict smoke, dispatched exactly one strict `atlas-migrate` Task, validated the complete aggregate from retained handle `agent://AtlasMigrateProjection`, and preserved ordered receipt `local://atlas-projection-migration-receipt.json`.
- **Dispatch binding:** `dispatch-atlas-migrate-2026-08-05-projection-1`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; atlas-migrate owner `sha256:e2aad4d008f205d1ac75d694b26f7d511a1d04f0bb14d11958ea5d5c0eee4269`; every returned binding field matched exactly.
- **Aggregate:** schema-valid `completed`, aggregate effect `committed`; item `topic-map-link-projection-migration` (`completed`); blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- **Migration:** exactly three eligible managed `topic-map` Link cells changed in `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` from preimage `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6` to acknowledged output `sha256:7a76b262a1296eb9f629a613b3fb517668d4e90bcfcc0584ecedd87e15c80785`; no other target changed.
- **Verification:** complete-registry `state.validate` passed before planning, after candidate preparation, and after mutation with no findings; row order, non-Link bytes/cells, unmanaged content, newline state, and registry revisions were preserved. The post-migration no-agent-memory structural probe returned no `SUBDOMAIN_PROJECTION_INVALID`, no transaction/intent/receipt, and only unrelated `TOPIC_COMPATIBILITY_CONFLICT` findings.
- **Rollback:** not invoked because post-validation passed; exact preimage/output revisions and one-artifact CAS rollback authority are preserved in the receipt. No transaction was invented; no `agent-memory` creation, acquisition, research, freshness/coverage correction, or unrelated mutation occurred.
- **Next route:** the unchanged fresh acquisition-enabled research overview is persisted at `local://atlas-research-retry-route-overview.txt`; research remains undispatched pending separately relayed approval. T3 and T4 remain incomplete.

## Attempt 8 Non-Terminal Research Retry Aggregate — 2026-08-05

**Settled:** 2026-08-05

- **Completed scope:** Revalidated the exact approved fresh research overview from `local://atlas-research-retry-route-overview.txt`, verified the completed migration receipt and repaired strict transport, completed the no-effect strict smoke, dispatched exactly one fresh strict `atlas-research` Task at `atlas_attempt: 2`, validated the complete transport binding from retained handle `agent://AtlasResearchMemoryRetry`, and preserved diagnostic receipt `local://atlas-research-retry-incomplete-receipt.json`.
- **Dispatch binding:** `dispatch-atlas-research-2026-08-05-retry-2`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; research owner `sha256:b4741629c88c4b9981ffc45af67afb650987887e5a4a515b284bc57e5a45e06d`; every returned binding field matched exactly.
- **Returned aggregate:** schema-valid `completed`, aggregate effect `committed`; item `selected-source-route-chain` (`completed`); blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- **Non-terminal result:** The returned aggregate reports only a selected-additional-source acquisition/materialization/routing substep and omits the required exact `agent-memory` topic path, dated pass path, complete coverage receipt, final projection paths, current answer, citations, and final audit receipt. Strict transport and binding were valid, but T3 could not consume this as terminal success.
- **No reconstruction:** Topic-create, acquisition, source, run, pass, relation, projection, answer, and final-audit receipts are recorded as absent/not returned in `local://atlas-research-retry-incomplete-receipt.json`; no owner messages or living state were substituted.
- **Stop condition:** T3 stops under the missing-required-receipt/partial-completion boundary. The parked handle was not resumed, no generic verifier or second research Task was dispatched, and no new Engineering Cycle receipt was available or consumed. T3 and T4 remain incomplete.

## Attempt 9 Completed Terminal Vault-Only Research — 2026-08-05

**Settled:** 2026-08-05

- **Completed scope:** Revalidated the exact approved terminal research overview from `local://atlas-terminal-research-route-overview.txt`, verified the completed migration lineage and repaired strict transport, completed the no-effect strict smoke, dispatched exactly one fresh strict vault-only `atlas-research` Task, validated the complete terminal aggregate from retained handle `agent://AtlasResearchMemoryTerminal`, and preserved ordered receipt `local://atlas-terminal-research-receipt.json`.
- **Dispatch binding:** `dispatch-atlas-research-2026-08-05-terminal-1`; fresh owner invocation with `atlas_attempt: 1`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; research owner `sha256:b4741629c88c4b9981ffc45af67afb650987887e5a4a515b284bc57e5a45e06d`; every returned binding field matched exactly.
- **Aggregate:** schema-valid `completed`, aggregate effect `committed`; items `agent-memory-research-pass`, `agent-memory-refresh-and-projections`, and `agent-memory-answer-and-final-audit` all `completed`; blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- **Terminal evidence:** exact topic path, dated pass path, complete 21-row coverage receipt, owning projections, eligible cited current answer, final audit receipt, and all bounded effects are present in the aggregate and receipt. Seven pending edges were refreshed; TOPICS is current with dirty count 0 and no pending edge IDs; acquisition run, source preparation/fetch, duplicate/rerouted source, source/manifest mutation, vocabulary mutation, related-topic answer mutation, and unrelated mutation are all absent.
- **Receipts and revisions:** pass `sha256:bd8786a3fdd18b08505bd561e120411746f9569f7ca4fdf530ceb5df8dec4166`; coverage `sha256:937921ae5162da3351e3ae3a31af1377f5a31d292b88dc32beddc5fe7493cecb`; final audit `sha256:b0a31fc896e6302b56f8d4039fcde4b72a3bbad93c91318ea6198454413768c4`; harness projection `sha256:cfa0a22a80aeaa3b61d33d768fc65fc5abb61475b8625308e6c3ee4992e0629f`; refresh receipt `sha256:cd5f6628798f5f9adf3bc42262cf2def8d83b0ac2eb98f8b8797e0c39ad54559`.
- **T3 state:** terminal research acceptance criteria are satisfied. Explicit insufficiencies remain preserved in the pass/audit; T4 refinement and verification remain pending. No direct Orchestrator Atlas/profile/vault/façade/owner I/O occurred.

## Attempt 10 Completed Read-Only Final Answer — 2026-08-05

**Settled:** 2026-08-05

- **Completed scope:** Revalidated the exact approved answer overview from `local://atlas-final-answer-route-overview.txt`, verified the repaired strict transport and current revisions, completed the no-effect strict smoke, dispatched exactly one strict read-only `atlas-answer` Task, validated the complete aggregate from retained handle `agent://AtlasAnswerMemoryFinal`, and preserved ordered receipt `local://atlas-final-answer-receipt.json`.
- **Dispatch binding:** `dispatch-atlas-answer-2026-08-05-final-1`; `atlas_attempt: 1`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; answer owner `sha256:4206b3c51f942db49924b792ec4296a704468e08a6d89caaf6964107c84cb582`; every returned binding field matched exactly.
- **Aggregate:** schema-valid `completed`, aggregate effect `none`; five required answer items completed; blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- **Answer evidence:** the validated current topic was current with dirty count 0 and no pending edge IDs; initial and final `state.validate` were clean; TOPICS hash was unchanged after reading the topic INDEX and its three `## Read next` artifacts. The aggregate returned the current answer, recommendation matrix, caveats, evidence map, gaps, read-next links, seven materialized citations, and explicit supported/contradicted/unproven comparison against monolithic, hierarchical/topic-sharded, append-only-compacted, and database/vector-backed alternatives.
- **Effects:** read-only; no refresh, mutation, acquisition, reroute, creation, repair, or unrelated state change occurred. No prior receipt was reconstructed or reused.
- **T4 state:** answer acceptance is complete. The separately approved final `atlas-audit` route remains pending; T4 and the plan remain incomplete until that audit and the subsequent provisional-draft comparison/verification gates pass.

## Attempt 11 Blocked Final Audit — 2026-08-05

**Settled:** 2026-08-05

- **Completed scope:** Revalidated the exact approved final audit overview and resolved request from `local://atlas-final-audit-route-overview.txt`, verified repaired strict transport and current revisions, completed the no-effect strict smoke, dispatched exactly one strict read-only `atlas-audit` Task, validated the complete aggregate from retained handle `agent://AtlasAuditMemoryFinal`, and preserved ordered receipt `local://atlas-final-audit-receipt.json`.
- **Dispatch binding:** `dispatch-atlas-audit-2026-08-05-final-1`; `atlas_attempt: 1`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`; every returned binding field matched exactly.
- **Aggregate:** schema-valid `completed`, aggregate effect `none`; four audit items completed; blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- **Clean checks:** the 21-row coverage ledger matched the expected receipt exactly; missing/extra/changed ledger fields were none; complete-registry `state.validate` returned zero findings; new target-reachable registry findings relative to the baseline were zero; unrelated baseline insufficiencies were retained as residual evidence.
- **Blocking source-quality result:** `quality.validate_summary` ran for all seven exact source artifacts and returned one `EVIDENCE_PAYLOAD_TEXT_INVALID` finding at `evidence.payload_text` per artifact, seven unresolved findings total. No canonical source-only payload/evidence envelope was available in the bounded read-only state; no summary prose, old receipt, acquisition, or substituted context was used.
- **T4 stop:** the required no-unresolved-target/source-quality condition failed. No repair, refresh, acquisition, retry, prior-receipt reconstruction, direct owner call, or scope widening occurred. Do not proceed to proposal edits, package check, or final completion until a separately authorized route resolves the missing source-only evidence payloads without weakening the audit boundary.

Close note: Terminal-closed 2026-08-13-2155 by approved plan `2026-08-13-1718_atlas-lean-heart-and-memory-t4` at sha256:a735fa42f75e76063772ea07303c8b83c6c238c1794d1ee145a3d8505140bab6 under AUTH-USER-GRANT. This identity is cancelled, not resumed. CLOSED is terminal; a later resume needs a new plan identity.
