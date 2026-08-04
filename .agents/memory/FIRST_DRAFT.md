<!-- provisional-plan: local://repo-agent-memory-first-draft-plan.md -->

# Repository agent memory first draft

## Status and decision boundary

This is a provisional baseline for later comparison. It is not executable authority and is not permission to ingest `tmp/`.

## Preferred shape

Prefer `.agents/memory/INDEX.md`, one file per accepted memory, `tmp/`, and `WORKFLOW.md`; avoid one monolithic `MEMORY.md`.

## Three layers

1. **Canonical owning artifacts** — contracts, code, tests, and other artifacts that remain authoritative when they can encode a behavior.
2. **Durable scoped memory** — one accepted record per durable lesson, discovered through the bounded index and loaded only when relevant.
3. **Ephemeral execution/handoff state** — transient task, run, and handoff context that is not promoted to durable memory.

## Loading interface

The eventual interface is an `AGENTS.md` bootstrap of at most a few lines through the repository's declared `alwaysApply: true` surface. It requires every agent/subagent to read `INDEX.md` before non-trivial work and then load only scope-matched records.

Linked-file byte transclusion and repository-`AGENTS.md` propagation to subagents are unverified. Final implementation must prove them with a live parent/subagent trace or bind the index path explicitly in each child Context Pack without duplicating memory bodies.

The provisional draft does not activate this loader.

## Provisional record shape

The provisional schema is one Markdown file with `id`, `status`, `scope`, `recorded`, `authority`, exact `sources`, and `supersedes`. Its body contains one claim plus the future-agent implication. This record shape is provisional, not final memory-schema authority.

## Required invariants

- Markdown/Git only.
- Explicit authority.
- Evidence for each durable claim.
- Canonical-owner precedence.
- Conflict blocking.
- Supersession rather than silent deletion.
- Relevance loading.
- Candidate/promotion separation.
- Transient state and secrets excluded.
- Raw `tmp/` inputs never loaded as active memory.
- No external service, vector store, embeddings, daemon, or hidden transcript crawler.

## Unresolved scale questions for Atlas

- Stale detection and revalidation.
- Incremental update/CAS behavior.
- Index growth/sharding.
- Old-but-active relevance.
- Temporal versus semantic ranking without external retrieval.
- Conflict/concurrency.
- Pruning versus archival.
- Provenance cost.
- Deterministic rebuild.

## Atlas framework stress test

**Outcome:** `PASS_SAFE_BLOCK`. The checked-in Atlas interfaces were exercised by one runner until `/atlas-index` reached an unsupported multi-target topic-creation boundary. No Atlas mutation occurred. The related topics were dirty, so ownership comparison was inconclusive; `agent-memory` was absent; the required dedicated topic could not be created without inventing a transaction contract.

**Runner:** `agent://AtlasSkillInterfaceRun`. The settled structured receipt is at `history://AtlasSkillInterfaceRun` line 237. Command/skill activation is visible at lines 41–65 for row 1, lines 105–133 for rows 2–4, and lines 137–149 for row 5. The runner corrected one sequence-5 manifest-revision transcription typo at line 255; the exact value is `sha256:ea4f4c8b64185bb1927739d5cba91fbf079daaa039ad57ebb307da8f3e69ac1a`.

### Attempted invocation rows

#### Row 1

- Command stub: `.agents/commands/atlas-audit.md`
- Primary skill: `skill://atlas-audit`
- Raw arguments:

```text
Audit registry and research-topic integrity for agent-memory, lean-self-improving-agent-harness, agentic-harness-architecture, and their bounded source/relation state.
```

- Terminal outcome: read-only audit completed with status `ISSUE`; `state.validate` returned `ok: true`, and the audit reported two `SUBDOMAIN_TOPIC_MAP_DRIFT` findings for dirty related topics.
- Returned paths: agent-memory topic `none (absent)`; receipt `none`; successor `none`; source `none`; run `none`; pass `none`.
- `blocker`: `none`

#### Row 2

- Command stub: `.agents/commands/atlas-answer.md`
- Primary skill: `skill://atlas-answer`
- Raw arguments:

```text
Return the current topic scope, answer contract, evidence map, gaps, and read-next links solely to assess whether this topic owns repository-native agent memory.
```

- Terminal outcome: deterministic freshness halt for `lean-self-improving-agent-harness`; freshness `dirty`, dirty count `9`.
- Returned paths: topic `vault://atlas/summaries/research/agent-systems/harness/topics/lean-self-improving-agent-harness/INDEX.md`; receipt `none`; successor `none`; source `none`; run `none`; pass `none`.
- `blocker`:

```text
NO_CODE: Topic path: vault://atlas/summaries/research/agent-systems/harness/topics/lean-self-improving-agent-harness/INDEX.md
Freshness state: dirty
Dirty count: 9
Pending edge IDs: edge--0508e01bccfc--lean-self-improving-agent-harness--f656f3b7; edge--50b3e8c09d96--lean-self-improving-agent-harness--e0bc83f9; edge--7e746ddbc1d0--lean-self-improving-agent-harness--54853479; edge--86d5a7049191--lean-self-improving-agent-harness--b99833c4; edge--8b346f57130e--lean-self-improving-agent-harness--76b184fc; edge--eaeeb9beb835--lean-self-improving-agent-harness--35b0679e; edge--ab9804dff1da--lean-self-improving-agent-harness--49fa9cd3; edge--c69cd3b0e6e6--lean-self-improving-agent-harness--708bef81; edge--ef463732cff6--lean-self-improving-agent-harness--9329e1d5
```

#### Row 3

- Command stub: `.agents/commands/atlas-answer.md`
- Primary skill: `skill://atlas-answer`
- Raw arguments:

```text
Return the current topic scope, answer contract, evidence map, gaps, and read-next links solely to assess whether this topic owns repository-native agent memory.
```

- Terminal outcome: deterministic freshness halt for `agentic-harness-architecture`; freshness `dirty`, dirty count `30`.
- Returned paths: topic `vault://atlas/summaries/research/agent-systems/harness/topics/agentic-harness-architecture/INDEX.md`; receipt `none`; successor `none`; source `none`; run `none`; pass `none`.
- `blocker`:

```text
NO_CODE: Topic path: vault://atlas/summaries/research/agent-systems/harness/topics/agentic-harness-architecture/INDEX.md
Freshness state: dirty
Dirty count: 30
Pending edge IDs: edge--04733803fcdc--agentic-harness-architecture--3b1f8958; edge--0918305f546d--agentic-harness-architecture--3a0b02b1; edge--12c3965a666c--agentic-harness-architecture--d0e7d81c; edge--4f28575995de--agentic-harness-architecture--e0153b7f; edge--50b3e8c09d96--agentic-harness-architecture--e0bc83f9; edge--5fb4fefbd4cb--agentic-harness-architecture--515c0eaa; edge--778aff69f59e--agentic-harness-architecture--291d0125; edge--7e746ddbc1d0--agentic-harness-architecture--54853479; edge--86d5a7049191--agentic-harness-architecture--b99833c4; edge--8b346f57130e--agentic-harness-architecture--76b184fc; edge--9e0f126b01bb--agentic-harness-architecture--891a383b; edge--a9d282499094--agentic-harness-architecture--9aabb2d8; edge--aa1b1ea88e57--agentic-harness-architecture--6d8e9df6; edge--c71fc314b4e4--agentic-harness-architecture--70c0fc7a; edge--c81365f99fcf--agentic-harness-architecture--f837bac7; edge--cddc9a2d075a--agentic-harness-architecture--5792394c; edge--eaeeb9beb835--agentic-harness-architecture--35b0679e; edge--feacb1c4ff8c--agentic-harness-architecture--34a16413; edge--ff7a301cf76d--agentic-harness-architecture--9bbe6138; edge--199d442d5281--agentic-harness-architecture--49dcacb2; edge--1f5bcd011229--agentic-harness-architecture--86855ca5; edge--5ab11d71ea30--agentic-harness-architecture--5f7b9c14; edge--6d302abbb73d--agentic-harness-architecture--37bb76b0; edge--9336444a8725--agentic-harness-architecture--3070f89e; edge--c69cd3b0e6e6--agentic-harness-architecture--708bef81; edge--cfade8e4b07f--agentic-harness-architecture--d1069b81; edge--db96a95a18e2--agentic-harness-architecture--786f505a; edge--e5b92aed7772--agentic-harness-architecture--90b5cd48; edge--ef463732cff6--agentic-harness-architecture--9329e1d5; edge--c836a9a1d3a3--agentic-harness-architecture--9acc699c
```

#### Row 4

- Command stub: `.agents/commands/atlas-answer.md`
- Primary skill: `skill://atlas-answer`
- Raw arguments:

```text
Return the current topic scope, answer contract, evidence map, gaps, and read-next links solely to assess whether this topic owns repository-native agent memory.
```

- Terminal outcome: deterministic unknown-topic halt for `agent-memory`.
- Returned paths: prospective topic `summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md` was not present; receipt `none`; successor `none`; source `none`; run `none`; pass `none`.
- `blocker`:

```text
NO_CODE: Topic `agent-memory` is not present in the validated Atlas topic registry; no topic INDEX.md was read.
```

#### Row 5

- Command stub: `.agents/commands/atlas-index.md`
- Primary skill: `skill://atlas-index`
- Raw arguments:

```text
Create or confirm the durable Atlas research topic `agent-memory`.
Topic path: summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md
Domain: agent-systems
Subdomain: harness
Canonical title: Agent memory
Aliases: repository agent memory; coding-agent memory; agent memory setup
Include: agent memory; coding-agent memory; repository-native memory; persistent agent context; long-term agent memory; memory index; memory record; memory curation; memory consolidation; memory supersession; stale memory; relevance loading
Exclude: foundation-model memory; model weights; GPU or operating-system memory; generic RAG; personal note-taking; uncurated chat/session history; Atlas product maintenance
Related topics: lean-self-improving-agent-harness; agentic-harness-architecture
Status: active
Initial coverage: insufficient
Initial confidence: low
Refresh model: same-as-topic-creation
If an exact compatible topic already exists, confirm it without changing its
current coverage, confidence, answer, or freshness; the initial values above
apply only when creating the topic.
Do not promote new vocabulary or tags.
```

- Terminal outcome: safe block before any write; capabilities, presence/hash reads, and `state.validate` completed.
- Returned paths: topic `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md` not created; receipt `none`; successor `none`; source `none`; run `none`; pass `none`.
- `blocker`:

```text
NO_CODE: Unsupported multi-target topic creation: the exact multi-target write set has no applicable core transaction contract; halt for a contract extension or explicit migration rather than hand-rolling a transaction or rollback.
```

No `/atlas-source`, `/atlas-research`, `/atlas-refresh`, final `/atlas-answer`, or final `/atlas-audit` invocation followed row 5. This is evidence that the user-facing boundary failed safely; it is not permission to bypass that boundary and not a completed Atlas comparison.

## Deferred first ingestion

After the final design and loader are implemented and verified, process every file then present in `tmp/` as the first candidate batch. Qualification may merge or reject candidates, but preserve the original raw file as ingestion provenance unless a later approved final policy explicitly authorizes archival or removal.

## Next comparison

Compare this baseline against T3's dated Atlas pass in a later dedicated task. Keep the dedicated directory/index preference unless evidence establishes a leaner and equally robust interface.
