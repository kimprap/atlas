<!-- provisional-plan: local://repo-agent-memory-first-draft-plan.md -->

# Agent memory workflow

## Purpose

The origin is the settled Atlas ingestion lesson: it was already encoded in its owning contract/skill/code/tests and the terminal curator correctly created no duplicate guidance, but no bounded repository memory map existed for residual cross-run discovery. The external sources motivated separating bootstrap, index, scoped records, and raw candidates.

## Interface

The eventual interface is one small bootstrap instruction available to every repository agent/subagent, a bounded `INDEX.md` map, scoped records loaded only when relevant, and explicit exclusion of `tmp/` from ordinary reads.

## Lifecycle

`settled outcome → raw candidate → qualification/deduplication/conflict check → human or designated-authority promotion → indexed active record → update or explicit supersession → historical retention`

## Artifact ownership

One owner applies to each artifact:

- `AGENTS.md` will eventually own only bootstrap/loading and precedence.
- `INDEX.md` owns discovery.
- Each record owns one durable lesson.
- `tmp/` owns untrusted/un-ingested candidates.
- Canonical contracts/code/tests remain the preferred owner when they can encode the behavior.
- Atlas owns research evidence only under `vault://atlas/`.

## Inspiration and evidence

### Cursor

- Cursor's [Field Guide article section](https://cursor.com/blog/agent-swarm-model-economics#letting-agents-shape-the-environment)
- Cursor's [`continual-learning` plugin](https://github.com/cursor/plugins/tree/14d9dfa06283faa94bf9931d3e98c189bc375680/continual-learning)
- Commit-bound [`reflect`](https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/reflect/SKILL.md)
- Commit-bound [`recall`](https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/recall/SKILL.md)
- Commit-bound [`automate-me`](https://github.com/cursor/plugins/blob/14d9dfa06283faa94bf9931d3e98c189bc375680/pstack/skills/automate-me/SKILL.md)

These sources must be distinguished: the Field Guide is private, the transcript-to-`AGENTS.md` updater is automatic, skill curation is human-reviewed, and transcript reconstruction is on-demand.

### Matt Pocock

- Matt Pocock's commit-bound [skills repository](https://github.com/mattpocock/skills/tree/2ab958093e83e0ec752e6c1c5932da465bf23e0c)
- [`teach`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/teach/SKILL.md)
- [Learning-record format](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/teach/LEARNING-RECORD-FORMAT.md)
- [`domain-modeling`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/domain-modeling/SKILL.md)
- [`research`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/engineering/research/SKILL.md)
- [`handoff`](https://github.com/mattpocock/skills/blob/2ab958093e83e0ec752e6c1c5932da465bf23e0c/skills/productivity/handoff/SKILL.md)

These sources distinguish deliberate repository artifacts and supersession from automatic general agent memory.

Prior planning lineage reported direct inspection of the linked primary source bodies; see session evidence agent://ResearchAgentMemorySources, local://github-memory-source-bodies.md, and local://github-memory-sources.md. This executor did not reproduce that inspection.

The reported narrow conclusion is that no one inspected source alone supplies automatic cross-session availability, bounded relevance loading, provenance, authority, stale handling, conflict safety, and dependency-free repository persistence.

The existing `agent-memory` topic, `2026-08-05` vault-only pass, and current answer confirm that conclusion for the repository-native baseline. They do not activate this workflow. Seven `EVIDENCE_PAYLOAD_TEXT_INVALID` findings remain residuals and were not repaired by a new audit.

The durable primary URLs above are the portable evidence.

## Invariants

- Markdown/Git only.
- Explicit authority.
- Evidence is retained.
- Canonical-owner precedence.
- Conflicts block rather than silently resolve.
- Supersession is used rather than silent deletion.
- Relevance loading is bounded.
- Candidate and promotion remain separate.
- Transient state and secrets are excluded.
- Raw `tmp/` inputs are never loaded as active memory.
- No external service, vector store, embeddings, daemon, or hidden transcript crawler.

## Maintenance

`WORKFLOW.md` is read only when designing, auditing, or changing the memory system; ordinary tasks use `INDEX.md` plus relevant active records only.
