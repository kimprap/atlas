<!-- provisional-plan: local://repo-agent-memory-first-draft-plan.md -->

# Agent memory index

This is a provisional smart map, not a memory dump.

## Status

The memory system is not active. No memory has been promoted. `tmp/` is excluded from normal loading.

## Lookup order

While provisional, read `Status`, then `FIRST_DRAFT.md`/`WORKFLOW.md`, and stop. After activation, resolve scope in `Active memory map` and load only its linked records. Never scan all record files or `tmp/`.

## Active memory map

None — promotion begins only after the final design is approved and implemented.

## Temporary inputs

- [`tmp/2026-08-02-atlas-evidence-date-seam.md`](tmp/2026-08-02-atlas-evidence-date-seam.md) — un-ingested raw material; it is not an active memory record.

## Research comparison input

Baseline audit complete: retained strict handle `agent://AuditAgentMemoryState` returned a schema-valid `no-write` aggregate with aggregate effect `none`; `agent-memory` is absent, the two related topics are dirty, and the validated aggregate reports three topic-map drifts, three coverage-map drifts, and one leftover fixture-artifact finding. Full receipt: `local://atlas-baseline-audit-receipt.json`. The approved acquisition-enabled `atlas-research` attempt was then dispatched through the repaired strict transport and returned handle `agent://ResearchAgentMemory`, but was blocked before topic creation by `SUBDOMAIN_PROJECTION_INVALID` on the noncanonical harness subdomain topic-map link. Full receipt: `local://atlas-research-blocked-receipt.json`. No acquisition, synthesis, topic creation, source, pass, relation, registry, projection, or repository-memory mutation occurred; T3 remains incomplete pending a separately approved registry/projection repair and fresh research dispatch.

The approved `atlas-index` projection-repair route was dispatched once through repaired strict transport with retained handle `agent://AtlasIndexRepair` and full binding validation, then returned schema-valid `blocked` with aggregate effect `none`. The owner inspected `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` but no advertised owner-native façade operation supports canonicalizing existing subdomain topic-map links; no mutation, receipt, or touched target occurred. Before and after revision remained `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6`; protected registry, related-answer, source, run, pass, and tree revisions are preserved in `local://atlas-index-repair-receipt.json`. No fresh research retry overview was rendered because the repair did not succeed.

The separately approved `atlas-migrate` route completed through repaired strict transport with retained handle `agent://AtlasMigrateProjection` and exact binding validation. One acknowledged artifact CAS migration changed exactly three eligible managed `topic-map` Link cells in `vault://atlas/summaries/research/agent-systems/harness/INDEX.md` from `sha256:429e6b0e29625cdbed3ef0c707cb2b6ea53bff77438cacf7fa5ace58c12df2e6` to `sha256:7a76b262a1296eb9f629a613b3fb517668d4e90bcfcc0584ecedd87e15c80785`; complete-registry validation passed before and after, and no unrelated state changed. Full receipt: `local://atlas-projection-migration-receipt.json`. The unchanged research retry overview is persisted at `local://atlas-research-retry-route-overview.txt`; research remains undispatched pending separate approval.

The fresh `atlas-research` retry dispatched exactly once with retained handle `agent://AtlasResearchMemoryRetry`, exact binding, and strict-schema acceptance. Its returned `completed`/`committed` aggregate contains only a selected-source acquisition/materialization/routing substep and omits the required topic, dated pass, coverage ledger, projection, answer, citation, and final-audit receipts, so T3 rejected it as non-terminal without reconstructing missing state. Full diagnostic receipt: `local://atlas-research-retry-incomplete-receipt.json`. No additional Task or verifier was dispatched.

The fresh vault-only terminal `atlas-research` Task completed with retained handle `agent://AtlasResearchMemoryTerminal`, exact binding, and a schema-valid terminal aggregate. It created the dated pass, complete 21-row coverage receipt, seven-edge refresh/projection updates, eligible cited current answer, and final audit; acquisition and source duplication remained absent, and unrelated state was unchanged. Full receipt: `local://atlas-terminal-research-receipt.json`. T3 terminal research acceptance criteria are satisfied; T4 remains pending.

The separately approved read-only `atlas-answer` Task completed with retained handle `agent://AtlasAnswerMemoryFinal`, exact binding, and a schema-valid `completed`/`none` aggregate. It returned the current evidence-cited answer, recommendation matrix, caveats, evidence map, gaps, and read-next links; the preferred Markdown/index/per-record baseline is supported, with no materialized contradiction and explicit quantitative/propagation/retention/conflict gaps. Full receipt: `local://atlas-final-answer-receipt.json`. T4's separate final `atlas-audit` route remains pending approval.

The separately approved read-only `atlas-audit` Task completed with retained handle `agent://AtlasAuditMemoryFinal`, exact binding, and a schema-valid `completed`/`none` aggregate. Registry/projection and coverage-ledger checks are clean with zero new target-reachable registry findings, but each of the seven bounded source-quality checks returned `EVIDENCE_PAYLOAD_TEXT_INVALID` because no canonical source-only payload/evidence envelope is materialized. Full receipt: `local://atlas-final-audit-receipt.json`.

## T4 proposal from existing evidence

Compared the provisional draft (`FIRST_DRAFT.md`, `WORKFLOW.md`, this index) to the existing `agent-memory` topic, pass, and answer. No new audit or recapture ran.

- Topic: `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/INDEX.md`
- Pass: `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/passes/2026-08-05--vault-only-agent-memory-research.md`
- Coverage receipt: `vault://atlas/summaries/research/agent-systems/harness/topics/agent-memory/passes/2026-08-05--vault-only-agent-memory-coverage.json` at sha256:937921ae5162da3351e3ae3a31af1377f5a31d292b88dc32beddc5fe7493cecb
- Answer receipt: `local://atlas-final-answer-receipt.json` from `agent://AtlasAnswerMemoryFinal`
- Audit receipt: `local://atlas-final-audit-receipt.json` from `agent://AtlasAuditMemoryFinal`

The current answer supports the provisional baseline: repository Markdown plus bounded `INDEX.md` plus scoped per-record files; bootstrap separate from durable records; session material as a candidate; explicit provenance/authority/supersession; hybrid retrieval optional and derived; no embeddings or daemon as authority. No materialized artifact contradicts that baseline.

Residuals kept, not repaired:

1. `EVIDENCE_PAYLOAD_TEXT_INVALID` at `050d13a3c637` (`2026-08-05--050d13a3c637--memory-bank.md`)
2. `EVIDENCE_PAYLOAD_TEXT_INVALID` at `175cba93472d` (`2026-08-05--175cba93472d--custom-instructions-with-agents.md.md`)
3. `EVIDENCE_PAYLOAD_TEXT_INVALID` at `2f838ab26661` (`2026-08-05--2f838ab26661--auto-memory.md`)
4. `EVIDENCE_PAYLOAD_TEXT_INVALID` at `7e495abb14d3` (`2026-08-05--7e495abb14d3--memsearch.md`)
5. `EVIDENCE_PAYLOAD_TEXT_INVALID` at `c50578e9878d` (`2026-08-05--c50578e9878d--agentmemory.md`)
6. `EVIDENCE_PAYLOAD_TEXT_INVALID` at `ea4c4eea324c` (`2026-08-05--ea4c4eea324c--memoria.md`)
7. `EVIDENCE_PAYLOAD_TEXT_INVALID` at `f1c064262dc8` (`2026-08-05--f1c064262dc8--how-claude-remembers-your-project.md`)

Also residual: twelve fixed references without artifacts; no controlled reliability/cost comparison; automatic subagent propagation, retention thresholds, and interoperable conflict policy remain unproven.

The memory system is still not active. `tmp/` is unchanged and is not loaded. Implementation still needs a later explicit route.
