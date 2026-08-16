# ADR 0007: Agent CLI and owner consolidation

## Status

Accepted

## Context

Atlas had one public front door but still exposed duplicated domain CLIs, manually synchronized façade lists, nine internal owner resources, helper-owner chains, and provider-shaped source capture. Agents had to remember transport details and internal mechanics before performing a lifecycle task. Research publication also lacked one owner for a bounded, recoverable four-target write.

## Decision

Keep `/atlas-ask` as the sole user-facing Atlas interface. Give agents one generated `scripts/atlas_tool.py` command tree backed by one immutable operation catalog and strict version-2 JSON envelope. Keep `scripts/atlas-instance.py` separate for framework and instance administration.

Consolidate internal work into three mode-aware owners: `atlas-source`, `atlas-research`, and `atlas-maintain`. Read-only modes need no write approval; each write-capable mode gets one Goal/Effect approval. Owners execute allowed route, refresh, and topic-create procedures in process and emit one compact terminal or bounded-resume result.

Expose lifecycle operations in default discovery and retain low-level primitives under explicit `capabilities --all`. Use purpose-specific topic inspection, transport-neutral source capture, and one recoverable research publication owner with exactly four ordered targets. Do not add provider plugins, hosted callbacks, hidden retries, background services, or a second public command.

A useful OptMem design lesson is structural rather than terminological: an agent tool is easier to remember when it presents a few lifecycle verbs while keeping necessary mechanics available behind explicit inspection. Atlas applies that lesson through audience-filtered discovery without copying OptMem concepts, names, or behavior.

## Consequences

Agents discover one stable lifecycle surface instead of memorizing parallel CLIs and helper chains. Internal primitives remain testable and callable without becoming the default user model. Owner results and recovery become transport-neutral, and research publication gains one deterministic recovery boundary.

The cutover removes the internal version-1 façade, hosted recapture, direct domain CLIs, and seven superseded owners without compatibility aliases. Existing instance-sync durability remains unchanged and requires a separate reliability decision.