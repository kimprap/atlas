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

**Outcome:** Later vault-only research created the `agent-memory` topic, dated pass, coverage ledger, and current answer. The current answer supports this draft's Markdown/index/per-record baseline. Seven `EVIDENCE_PAYLOAD_TEXT_INVALID` source-quality findings remain residuals. No new audit or recapture ran for this proposal. The memory system stays inactive.

**Attempt 1 runner:** `agent://AtlasSkillInterfaceRun`. The settled structured receipt is at `history://AtlasSkillInterfaceRun` line 237. Command/skill activation is visible at lines 41–65 for row 1, lines 105–133 for rows 2–4, and lines 137–149 for row 5. The runner corrected one sequence-5 manifest-revision transcription typo at line 255; the exact value is `sha256:ea4f4c8b64185bb1927739d5cba91fbf079daaa039ad57ebb307da8f3e69ac1a`.

**Attempt 2 orchestrator:** Main, settled `2026-08-04T09:36:26Z`. The current plan and repository projection were byte-identical at SHA-256 `b41ef70cdd91e205a340764d5091f57fc0e4d3fbbe9be9d872d8cdef02b3c4c8`; `plan-artifact-sync` completed before the plan removed only its own stale-gate identity. No Workflow Owner Task handle was created.

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

#### Row 6

- Command stub: `.agents/commands/atlas-ask.md`
- Primary skill: `skill://atlas-ask`
- Selected owner: `atlas-audit`
- Raw arguments:

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

- Approved route overview:

```text
Goal: Audit the bounded Atlas state required for repository-native agent-memory research, covering `agent-memory`, `lean-self-improving-agent-harness`, `agentic-harness-architecture`, and their reachable manifest, topic, relation, and subdomain state.
Next: `atlas-audit` — validate the current registries and report topic existence, identity, metadata, freshness, answer boundaries, pending edges, and concrete findings without repair.
Effect: read-only; no Atlas writes
Retry: up to 3 receipt-gated fresh Atlas executions after separately approved Engineering Cycles; unchanged goal and write set only.

Approve this Atlas route?
```

- Approval evidence: the user replied `approved.` to the unchanged overview after current framework revalidation.
- Bound revisions: architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; workflow-result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`.
- Dispatch identity: `1B74B00E-DCBF-4ED4-A405-9C2B50A90E40`; retained Task/agent handle: `none` because preflight created no result/job.
- Terminal outcome: `capability-unavailable` before Workflow Owner work. The Task transport returned `Task AuditAgentMemoryState failed preflight: Invalid strict caller output schema: invalid JSON schema` with `results: []` and `totalDurationMs: 0`.
- Returned paths: topic `not inspected`; receipt `none`; successor `none`; source `none`; run `none`; pass `none`.
- Atlas effect: `none`; no profile, vault, façade, reducer, transaction, or owner operation ran.
- `blocker`:

```text
capability-unavailable: Task AuditAgentMemoryState failed preflight: Invalid strict caller output schema: invalid JSON schema
```

No current owner invocation followed row 6. The checked-in schema parsed as JSON, but the strict Task caller rejected it before dispatch; the local Python environment did not contain the optional `jsonschema` package for an independent Draft 2020-12 meta-schema check. Per the Atlas capability boundary, no permissive schema, prompt-only parsing, direct owner call, or manual vault inspection was attempted.



#### Row 7

- Command stub: `.agents/commands/atlas-ask.md`
- Primary skill: `skill://atlas-ask`
- Selected owner: `atlas-audit`
- Raw arguments:

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

- Approved route overview:

```text
Goal: Audit the bounded Atlas state required for repository-native agent-memory research.
Next: atlas-audit Workflow Owner — inspect the named topics and the reachable manifest, topic, and relation state without mutation.
Effect: read-only; no Atlas writes
Retry: up to 3 receipt-gated fresh Atlas executions after separately approved Engineering Cycles; unchanged goal and write set only.

Approve this Atlas route?
```

- Approval evidence: The user selected `Approve` for the exact unchanged baseline-audit route overview rendered immediately before this invocation.
- Bound revisions: architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; workflow-result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`.
- Dispatch identity: `5e04c4c1-efda-4259-9ef3-33498d266863`; returned Task/agent delivery handle: `none` because strict result validation threw before `agent(...)` returned. The task UI registered the execution label `AuditAgentMemoryState`, but that label is not a returned retained handle and is not consumed as one.
- Terminal outcome: the Task result was rejected during complete strict aggregate validation with `schema_violation: dispatch.guardrail_revision: must match pattern`.
- Compact items: none accepted; the rejected payload is not a schema-valid aggregate and is not consumed.
- Returned paths: topic `none accepted`; receipt `none`; successor `none`; source `none`; run `none`; pass `none`.
- Aggregate effect: `none` from the Orchestrator; no validated owner effect was consumed.
- `blocker`:

```text
capability-unavailable: retained atlas-audit Task result failed complete strict aggregate validation: dispatch.guardrail_revision: must match pattern
```

No validated baseline findings or topic paths are available. Do not reconstruct owner output from the rejected payload, agent messages, history, or Atlas state.


### Strict Task source-repair evidence — 2026-08-04

- Owning source: OMP `v17.2.7`, commit `a5090f1f81cf0ac072fbd1ec949eebe6bbbc23a9`, in external checkout `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949`.
- Native prerequisite: public `@oh-my-pi/pi-natives-darwin-arm64@17.2.7`, registry integrity `sha512-eIvz6ZzHEnUyBPRfoLdXOf/VhvbUgcCp5V5YCeqVz+sEQ+AJjOyDl9ayjTIHR/2spnEJ6zgl4F7Xr/c/sMhWJQ==`, SHA-1 `1f8de55f4d1760e5e91b85460d63d34dd1074906`; copied addon SHA-256 `67de42fe9e7aa9c2c5e3a817f2b9f0c6b87e7252b8e3a3da1d9beb86e076055c`.
- Verified target SHA-256 values: normalizer `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; normalizer tests `dfc353ec75040fae7951e8b1a64f77fb66c8b83f58e73ec10ea556de63e4cf64`; validator tests `2349c7a35a361e6aaa8bc839ecd3e2b58f22c53f74bf67f8b7e38c548f808a14`; structured-subagent tests `f08aacc4bb7f5d1fd5fcc83224bf866408fa04572611d809be7de2d80c96c0d6`; user-config-isolated LSP regression `14acc6156ad7dced762945764e42fc2966c4d5242ccc749690b6f7adfb7e0e4a`; complete schema fixture `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; generated tool-view prerequisite `abf8a665d3ae62ecc74b7bc6da4a7f4706cfbb2b52a4344a53a995d10b9127ef`.
- Focused checks passed: normalizer `9/9`, validator `14/14`, structured-subagent `19/19`, complete LSP file `76/76`, and typecheck. Direct source smoke printed `strict-schema-transport OK`. The canonical Atlas schema and copied fixture remain byte-identical at SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`.
- Revised package evidence recorded `11,712` passes, `404` skips, and only the user-accepted unrelated collab tombstone timeout; the exact timeout case passed in isolation and pre/post target manifests were identical.
- Independent assurance: `agent://StrictSchemaVerifier` returned `VERIFIED`; distinct `agent://StrictSchemaReviewer` returned Standards `PASS`, Specification `PASS`, Overall `APPROVED`; `agent://StrictSchemaCurator` returned `NO DURABLE LEARNING`.
- Source-level strict-transport repair is verified in the external v17.2.7 checkout; the patched harness is not activated, no fresh /atlas-ask route has been approved or dispatched, and no Atlas I/O occurred. T3 and T4 remain unchecked and Status remains IN_PROGRESS.

#### Row 8

- Command stub: `.agents/commands/atlas-ask.md`
- Primary skill: `skill://atlas-ask`
- Selected owner: `atlas-audit`
- Raw arguments:

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

- Approved route overview:

```text
Goal: Audit the bounded Atlas state required for repository-native agent-memory research.
Next: atlas-audit Workflow Owner — inspect the named topics and the reachable manifest, topic, and relation state without mutation.
Effect: read-only; no Atlas writes
Retry: up to 3 receipt-gated fresh Atlas executions after separately approved Engineering Cycles; unchanged goal and write set only.

Approve this Atlas route?
```

- Approval evidence: The user selected `Approve` for the exact unchanged baseline-audit route overview rendered immediately before this invocation.
- Preflight evidence: exact repaired-checkout launch command; normalizer SHA-256 `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; complete workflow-result schema SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; no-effect strict smoke returned `agent://StrictTaskNoEffectSmoke` with the exact valid `no-write` payload.
- Bound revisions: architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; workflow-result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`.
- Dispatch identity: `dispatch-atlas-audit-2026-08-05-fresh-1`; returned Task/agent delivery handle: `agent://AuditAgentMemoryState`.
- Terminal outcome: `no-write`; aggregate effect: `none`; the one validated item is `atlas-audit.bounded-state` with status `no-write`: `Read-only bounded audit completed with no bound-instance writes; one missing topic, six projection drifts, and one leftover temporary fixture artifact were reported with clean registry/provenance checks.`
- Baseline findings from the validated aggregate: `agent-memory` is absent; `lean-self-improving-agent-harness` and `agentic-harness-architecture` exist at their canonical topic paths and are active/sufficient/medium but dirty with 9 and 30 pending edge IDs respectively; registry validation returned no malformed table placement, duplicate/invalid IDs, enum/hash/path disagreement, cache disagreement, or provenance issue; the aggregate counted `TOPIC_NOT_REGISTERED=1`, `SUBDOMAIN_TOPIC_MAP_DRIFT=3`, `SUBDOMAIN_COVERAGE_MAP_DRIFT=3`, and `LEFTOVER_FIXTURE_ARTIFACTS=1`.
- Returned topic paths: `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md` (absent), `vault://atlas/summaries/research/agent-systems/harness/topics/lean-self-improving-agent-harness/INDEX.md`, and `vault://atlas/summaries/research/agent-systems/harness/topics/agentic-harness-architecture/INDEX.md`. Returned pass, run, and source paths: `none`.
- Full validated aggregate receipt, including the complete summary and all pending IDs/anchors: `local://atlas-baseline-audit-receipt.json`.
- `blocker`: `none`

No research, acquisition, topic creation, source, pass, relation, registry, or repository-memory mutation was dispatched under this approval. The next `atlas-research` route is only a rendered proposal pending separate approval.

#### Row 9

- Command stub: `.agents/commands/atlas-ask.md`
- Primary skill: `skill://atlas-ask`
- Selected owner: `atlas-research`
- Raw arguments (the exact LF-preserving request is also retained in `local://atlas-research-blocked-receipt.json`):

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

- Approved route overview:

```text
Goal: Research repository-native agent memory for a host-owned coding-agent harness, with explicit bounded acquisition.
Next: atlas-research Workflow Owner — confirm or create the exact compatible agent-memory topic before synthesis, then run one bounded acquisition-enabled research workflow within the approved topic, source, run, pass, relation, and projection boundary.
Effect: write-capable through the selected Workflow Owner; exact effects remain owner-gated
Retry: up to 3 receipt-gated fresh Atlas executions after separately approved Engineering Cycles; unchanged goal and write set only.

Approve this Atlas route?
```

- Approval evidence: The user selected `Approve` for the exact unchanged atlas-research route overview rendered immediately before this invocation.
- Preflight evidence: launch command `bun --cwd=/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent src/cli.ts --cwd /Users/kim/dev/atlas/app`; normalizer SHA-256 `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; complete workflow-result schema SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; research owner `sha256:b4741629c88c4b9981ffc45af67afb650987887e5a4a515b284bc57e5a45e06d`.
- Dispatch identity: `dispatch-atlas-research-2026-08-05-fresh-1`; returned Task/agent delivery handle: `agent://ResearchAgentMemory`.
- Binding validation: every dispatch field matched exactly, including guardrail revision `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`.
- Terminal outcome: `blocked`; aggregate effect: `none`; compact items: `agent-memory-topic-create` (`blocked`) and `bounded-acquisition-and-research` (`no-write`).
- Topic effect: no topic was created; requested topic ID/path remained `agent-memory` / `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md`.
- Run, pass, source artifacts, current answer, and citations: `none`; current answer was not eligible because no topic was created and no current answer was returned.
- Source-manifest effect: `unchanged`; revision `sha256:ea4f4c8b64185bb1927739d5cba91fbf079daaa039ad57ebb307da8f3e69ac1a`.
- Relation effect: `unchanged`; revision `sha256:aabc9dacef7991a7e58508b3bb5c49f1d7069c237bee954971c5603e8172d2a6`.
- Projection effect: path `vault://atlas/summaries/research/agent-systems/harness/INDEX.md`; revision `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6`; finding `SUBDOMAIN_PROJECTION_INVALID: noncanonical [Open](topics/agentic-harness-architecture/INDEX.md) link`; no topic, source, pass, run, or relation projection was written.
- `resume`: A separately authorized registry/projection repair must canonicalize the existing harness subdomain topic-map links without changing either related topic's answer or vocabulary, then a fresh `/atlas-ask` research dispatch must rerun the approved topic-create gate before any acquisition or synthesis; this blocked attempt cannot resume into acquisition.
- `guidance`: `null`
- `defects`: `[]`
- `learning_candidate`: `null`
- `blocker`:

```text
kind: owner
detail: The bound harness subdomain projection is structurally incompatible with the index.create_topic owner contract: its topic-map contains noncanonical [Open](topics/agentic-harness-architecture/INDEX.md) links, so index.create_topic returns SUBDOMAIN_PROJECTION_INVALID before intent and the research owner must stop before acquisition.
```

- Full validated aggregate receipt: `local://atlas-research-blocked-receipt.json`.

No acquisition, synthesis, topic creation, source, pass, relation, registry, projection, or repository-memory mutation was dispatched or consumed under this approval. T3 remains incomplete; the next route is a separately approved registry/projection repair followed by a fresh research dispatch.

### Strict Task projection-repair evidence — 2026-08-05

#### Row 10

- Approval evidence: The user selected `Approve` for the exact unchanged `atlas-index` repair overview persisted at `local://atlas-repair-route-overview.txt`.
- Route: `atlas-index` Workflow Owner — canonicalize only existing topic-map links in `vault://atlas/summaries/research/agent-systems/harness/INDEX.md`; preserve both related topic answers, vocabulary, canonical registries, sources, relations, runs, passes, and all unrelated state.
- Preflight evidence: repaired process command `bun --cwd=/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent src/cli.ts --cwd /Users/kim/dev/atlas/app`; normalizer SHA-256 `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; complete workflow-result schema SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; atlas-index owner `sha256:7c62ee5c86b6c0fb0b044c759e6edf7092e813502f2fb72d5aeef03c1c7da2ce`; no-effect strict smoke returned `agent://StrictTaskNoEffectSmoke-2` with `no-write` / `none`.
- Dispatch identity: `dispatch-atlas-index-2026-08-05-repair-1`; returned Task/agent delivery handle: `agent://AtlasIndexRepair`.
- Binding validation: every dispatch field matched exactly, including guardrail revision `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`.
- Terminal outcome: schema-valid `blocked`; aggregate effect `none`; item `atlas-index-topic-map-repair` (`blocked`); guidance `null`; defects `[]`; learning candidate `null`.
- Exact blocker: The qualified atlas-index façade advertises no owner-native projection-repair/canonicalization operation for existing subdomain topic-map links. `index.create_topic` and `index.recover_topic` are creation/recovery operations; the owner contract's `repair-table-placement` and `repair-relation-notes` events do not apply. No mutation operation, conditional replace, direct edit, transaction, or receipt was issued.
- Before/after revision: target `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` remained `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6`; touched targets `[]`.
- Protected revisions: `VOCAB.md` `sha256:d2d5991720f61d92140d2477059d507e150ce280d868e8ad7fd169fcec060693`; `TOPICS.md` `sha256:bedca425ccaac8a32db7f1bda7696c146a6f27a09895d2160c935b385769dfb7`; `RELATIONS.md` `sha256:aabc9dacef7991a7e58508b3bb5c49f1d7069c237bee954971c5603e8172d2a6`; source manifest `sha256:ea4f4c8b64185bb1927739d5cba91fbf079daaa039ad57ebb307da8f3e69ac1a`; related topic answers and protected tree digests are preserved in the receipt.
- Full validated aggregate receipt: `local://atlas-index-repair-receipt.json`.
- Resume: This attempt cannot resume into repair or research. A future qualified atlas-index contract and advertised façade operation for this exact projection repair are required; do not use `index.create_topic`, `repair-table-placement`, `repair-relation-notes`, direct Markdown editing, or `vault.conditional_replace` as substitutes.
- Plan state: T3 and T4 remain incomplete. No successful repair occurred, so no fresh research retry overview was rendered or dispatched. No direct Orchestrator Atlas/profile/vault/façade/owner I/O occurred.

### Strict Task migration evidence — 2026-08-05

#### Row 11

- Approval evidence: The user selected `Approve` for the exact unchanged `atlas-migrate` overview persisted at `local://atlas-projection-migration-route-overview.txt`.
- Route: one explicit old-to-new migration limited to `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` and only the managed `topic-map` table's eligible `Link` cells. Old cells were exact `[Open](topics/<topic-id>/INDEX.md)` values whose ID matched the row's canonical TOPICS ID; new cells are plain root-relative `summaries/research/agent-systems/harness/topics/<topic-id>/INDEX.md` scalars.
- Preflight evidence: repaired process command `bun --cwd=/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent src/cli.ts --cwd /Users/kim/dev/atlas/app`; normalizer SHA-256 `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; complete workflow-result schema SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; atlas-migrate owner `sha256:e2aad4d008f205d1ac75d694b26f7d511a1d04f0bb14d11958ea5d5c0eee4269`; no-effect strict smoke returned `agent://StrictTaskNoEffectSmokeMigration` with `no-write` / `none`.
- Dispatch identity: `dispatch-atlas-migrate-2026-08-05-projection-1`; returned Task/agent delivery handle: `agent://AtlasMigrateProjection`.
- Binding validation: every dispatch field matched exactly, including guardrail revision `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`.
- Terminal outcome: schema-valid `completed`; aggregate effect `committed`; item `topic-map-link-projection-migration` (`completed`); blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- Migration receipt: `local://atlas-projection-migration-receipt.json`.
- Before/after: one acknowledged `vault.conditional_replace` changed the sole target from preimage `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6` to output `sha256:7a76b262a1296eb9f629a613b3fb517668d4e90bcfcc0584ecedd87e15c80785`; exactly three eligible cells changed; no other target was touched.
- Verification: compatible complete-registry `state.validate` passed before planning, after candidate preparation, and after mutation with no findings; row order, non-Link cells, unmanaged content, newline state, and preimage hash were preserved; MANIFEST `sha256:ea4f4c8b64185bb1927739d5cba91fbf079daaa039ad57ebb307da8f3e69ac1a`, TOPICS `sha256:bedca425ccaac8a32db7f1bda7696c146a6f27a09895d2160c935b385769dfb7`, and RELATIONS `sha256:aabc9dacef7991a7e58508b3bb5c49f1d7069c237bee954971c5603e8172d2a6` remained unchanged.
- Structural preflight: the pre-write probe reported `SUBDOMAIN_PROJECTION_INVALID` for the old encoding; the post-migration no-agent-memory existing-topic probe reported no `SUBDOMAIN_PROJECTION_INVALID`, returned no transaction/intent/receipt, and did not create `agent-memory`. It reported only unrelated `TOPIC_COMPATIBILITY_CONFLICT` topic-frontmatter findings.
- Rollback: not invoked; the post-validation condition passed. The exact preimage and output revision remain in the receipt for the one-artifact CAS rollback boundary. No transaction was invented; no acquisition, research, freshness/coverage correction, or unrelated mutation occurred.
- Fresh retry route: the unchanged acquisition-enabled research overview was rendered and persisted at `local://atlas-research-retry-route-overview.txt`; no research Task was dispatched and the separate approval gate is open.

### Strict Task research-retry evidence — 2026-08-05

#### Row 12

- Approval evidence: The user selected `Approve` for the exact unchanged fresh research overview persisted at `local://atlas-research-retry-route-overview.txt`.
- Dispatch identity: `dispatch-atlas-research-2026-08-05-retry-2`; `atlas_attempt: 2`; returned Task/agent delivery handle: `agent://AtlasResearchMemoryRetry`.
- Binding validation: the strict result transport accepted the complete schema; every returned dispatch field matched exactly, including architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`, guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`, result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`, and research owner `sha256:b4741629c88c4b9981ffc45af67afb650987887e5a4a515b284bc57e5a45e06d`.
- Migration dependency: completed receipt `local://atlas-projection-migration-receipt.json`; canonical projection output revision `sha256:7a76b262a1296eb9f629a613b3fb517668d4e90bcfcc0584ecedd87e15c80785`; the prior blocked research Task and approval were not reused.
- Returned aggregate: schema-valid `completed` with aggregate effect `committed`; item `selected-source-route-chain` (`completed`); blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- Exact returned result: The aggregate reports only a selected-additional-source acquisition/materialization/routing substep and names seven selected source IDs, but returns no exact `agent-memory` topic path, dated pass path, complete coverage receipt, final projection paths, current answer, citations, or final audit receipt.
- T3 consumption gate: retained binding and strict schema were valid, but the result is non-terminal and not consumable under the authoritative T3 contract. Required topic/pass/coverage evidence is missing; no missing path or receipt was reconstructed from owner messages or living state.
- Preserved receipt: `local://atlas-research-retry-incomplete-receipt.json`. Topic-create, acquisition, source, run, pass, relation, projection, answer, and final-audit receipts are recorded as absent/not returned rather than inferred.
- Stop condition: T3 stops under the missing-required-receipt/partial-completion boundary. Do not resume the parked handle, dispatch a generic verifier, dispatch another research Task under this approval, or infer success from the substep aggregate. No new Engineering Cycle receipt was available or consumed.

### Strict Task terminal research evidence — 2026-08-05

#### Row 13

- Approval evidence: The user selected `Approve` for the exact unchanged terminal research overview persisted at `local://atlas-terminal-research-route-overview.txt`.
- Dispatch identity: `dispatch-atlas-research-2026-08-05-terminal-1`; fresh `atlas-research` Task; returned delivery handle `agent://AtlasResearchMemoryTerminal`. Attempt 8's handle and approval were not reused.
- Binding validation: strict schema accepted the complete aggregate and every returned binding field matched exactly. Normalizer `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; research owner `sha256:b4741629c88c4b9981ffc45af67afb650987887e5a4a515b284bc57e5a45e06d`.
- Terminal aggregate: schema-valid `completed`; aggregate effect `committed`; items `agent-memory-research-pass`, `agent-memory-refresh-and-projections`, and `agent-memory-answer-and-final-audit` all `completed`; blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- Exact terminal paths: topic `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md`; dated pass `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/passes/2026-08-05--vault-only-agent-memory-research.md`; coverage receipt `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/passes/2026-08-05--vault-only-agent-memory-coverage.json`; final audit `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/passes/2026-08-05--vault-only-agent-memory-final-audit.json`; owning projection `vault://atlas/summaries/research/agent-systems/harness/INDEX.md`.
- Coverage: complete ordered 21-row receipt with 13 fixed references, eight current materialized additional artifacts, seven included target-routed artifacts, one adjacent excluded artifact, one fixed artifact excluded as related-topic-only, and twelve fixed references explicitly unreviewed; no ranking receipt was available and no omitted receipt was reconstructed.
- State and answer: topic index revision `sha256:6f1058b8291a6ea535bbcbd6279cf078f83f3307d42659700e5bfeff379fae61`; coverage `partial`, confidence `medium`; TOPICS current with dirty count 0 and no pending edge IDs; current seven-bullet answer is eligible and cites the seven materialized target artifacts.
- Refresh/projections: owner-native refresh receipt `vault://atlas/.atlas/refresh/agent-memory--2026-08-05--vault-only/receipt.json` at `sha256:cd5f6628798f5f9adf3bc42262cf2def8d83b0ac2eb98f8b8797e0c39ad54559` applied exactly seven pending edges; final TOPICS `sha256:2c3607e6e95e3d0203c3f0995985abf58858a514cc893b182c16fb84797375ff`, RELATIONS `sha256:af35a7fa193cd3952d621d0872d023d4f82439ca7fc44957aa083a22b955420c`, MANIFEST `sha256:6ed1729cc7fd38d4a6145ff4334e804a107615425a7743df38333aecfa21602b`, owning projection `sha256:cfa0a22a80aeaa3b61d33d768fc65fc5abb61475b8625308e6c3ee4992e0629f`.
- Effects: acquisition run `none`; no topic creation, source preparation/fetch, duplicate or rerouted source, source/manifest mutation, vocabulary mutation, related-topic answer mutation, or unrelated-state mutation. Committed effects are limited to the agent-memory pass/index, seven-edge refresh/freshness, coverage receipt, owning projection, refresh provenance, current cited answer, and final audit receipt.
- Full validated receipt: `local://atlas-terminal-research-receipt.json`.
- T3 state: terminal research acceptance criteria are satisfied; T4 refinement/verification remains pending. Explicit insufficiencies are preserved in the pass/audit: twelve absent fixed artifacts, no controlled cross-architecture comparison, and unresolved automatic subagent propagation, retention/decay, and interoperable conflict-resolution protocols.

### Strict Task final answer evidence — 2026-08-05

#### Row 14

- Approval evidence: The user selected `Approve` for the exact unchanged final answer overview persisted at `local://atlas-final-answer-route-overview.txt`.
- Dispatch identity: `dispatch-atlas-answer-2026-08-05-final-1`; selected owner `atlas-answer`; returned delivery handle `agent://AtlasAnswerMemoryFinal`.
- Binding validation: strict transport accepted the complete aggregate and every returned binding field matched exactly. Normalizer `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; answer owner `sha256:4206b3c51f942db49924b792ec4296a704468e08a6d89caaf6964107c84cb582`.
- Strict aggregate: schema-valid `completed` with aggregate effect `none`; items `agent-memory-current-answer`, `agent-memory-recommendation-matrix`, `agent-memory-evidence-map`, `agent-memory-caveats-and-gaps`, and `agent-memory-read-next` all `completed`; blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- Current-state proof: exact topic `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md` at `sha256:6f1058b8291a6ea535bbcbd6279cf078f83f3307d42659700e5bfeff379fae61`; validated `current`, dirty count `0`, no pending edge IDs; initial and final `state.validate` clean; unchanged TOPICS revision `sha256:2c3607e6e95e3d0203c3f0995985abf58858a514cc893b182c16fb84797375ff`.
- Answer content: the current answer recommends the repository Markdown/index/per-record baseline as canonical, separates bootstrap instructions from durable records, requires review-gated candidate promotion, preserves explicit provenance/lifecycle/supersession, keeps derived retrieval rebuildable, and permits database/vector/service layers only conditionally with a repository fallback.
- Comparison: the baseline is marked supported; no materialized target-routed artifact contradicts it. Hierarchical/topic-sharded indexes are supported as a bounded extension; monolithic-memory superiority, append-only compaction as canonical replacement, topic-sharding thresholds, vector/database break-even, reliability/cost/latency claims, automatic subagent propagation, retention/decay thresholds, and interoperable conflict resolution remain unproven.
- Evidence and limits: the answer cites seven materialized source artifacts, includes caveats, an evidence map, explicit gaps, and read-next links. Coverage remains `partial` with `medium` confidence; twelve fixed references lack current artifacts and were not inferred; no refresh or mutation occurred.
- Full validated receipt: `local://atlas-final-answer-receipt.json`.
- T4 state: answer acceptance is complete; the separate read-only `atlas-audit` route for pass, topic, relation, freshness, owning projection, materialized source IDs, and exact coverage-ledger comparison remains pending approval. No direct Orchestrator Atlas/profile/vault/façade/owner I/O occurred.

### Strict Task final audit evidence — 2026-08-05

#### Row 15

- Approval evidence: The user selected `Approve` for the exact unchanged final audit overview and resolved request persisted at `local://atlas-final-audit-route-overview.txt`.
- Dispatch identity: `dispatch-atlas-audit-2026-08-05-final-1`; selected owner `atlas-audit`; returned delivery handle `agent://AtlasAuditMemoryFinal`.
- Binding validation: strict transport accepted the complete aggregate and every returned binding field matched exactly. Normalizer `304b7f0199dc691332532dbacf782178e45137f1acf381c4510ec269a99822db`; architecture `sha256:d92d1121461b4362931d08268efae2bfd87b4a5bab5f0cab3c6e6f85af5cd077`; guardrail `sha256:8a9556089fc9f4a32e94a3a4b1085c24d15f3f63a3478cc8054d1ff5ad6fd39c`; result schema `sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`; audit owner `sha256:6508454083b0200607db401c9a887795f78f7946419b9f947e19a866f27870d6`.
- Strict aggregate: schema-valid `completed` with aggregate effect `none`; items `agent-memory-registry-and-projection-audit`, `agent-memory-source-quality-audit`, `agent-memory-coverage-ledger-audit`, and `agent-memory-baseline-delta` all `completed`; blocker `null`; guidance `null`; defects `[]`; learning candidate `null`.
- Clean checks: coverage ledger agreement is exact; expected missing, extra, and changed ledger fields are none; complete-registry `state.validate` returned zero findings; new target-reachable registry findings relative to the recorded baseline are zero; unrelated baseline insufficiencies remain residual evidence.
- Blocking finding: bounded `quality.validate_summary` returned one `EVIDENCE_PAYLOAD_TEXT_INVALID` finding at `evidence.payload_text` for each of the seven exact source artifacts, seven unresolved source-quality findings total. The artifacts expose content-hash identity but no canonical source-only payload/evidence envelope was available in the bounded read-only cohort; summary prose, old receipts, and acquisition were not substituted.
- Stop condition: T4's required no-unresolved-target/source-quality condition is not satisfied. No repair, refresh, acquisition, retry, direct owner call, prior-receipt reconstruction, or scope widening occurred.
- Full validated receipt: `local://atlas-final-audit-receipt.json`.
- T4 state: final audit is terminally blocked on the missing source-only evidence payloads. Do not proceed to proposal edits, package check, or final completion until a separately authorized route resolves this blocker without weakening the source-quality boundary.

## Deferred first ingestion

After the final design and loader are implemented and verified, process every file then present in `tmp/` as the first candidate batch. Qualification may merge or reject candidates, but preserve the original raw file as ingestion provenance unless a later approved final policy explicitly authorizes archival or removal.

## Next comparison

Compare this baseline against T3's dated Atlas pass in a later dedicated task. Keep the dedicated directory/index preference unless evidence establishes a leaner and equally robust interface.
