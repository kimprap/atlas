# ADR 0006: Hosted audit recapture coordinator

## Status

Superseded

## Context

Exact-seven source-quality recapture formerly crossed prompt, worker-result, and temporary-filesystem boundaries. That transport made native callback objects indirect, required reconstruction and cleanup, and widened source-local work beyond the read-only audit owner even though the final result was one audit aggregate.

## Decision

Keep one selected `atlas-audit` owner and one outer result, but run recapture through the private hosted `source.audit_recapture` façade entry with a repository-owned, non-serializable `AuditRecaptureHostV1`. Freeze all seven persisted identities before callbacks, observe and assess each source sequentially through closed source-local packets, reuse the existing strict quality validator, recheck canonical revisions before a clean result, and return only ordered non-raw receipts and findings. The coordinator has no write or persistence authority, and the former successor, worker, serialized-result, and temporary-evidence transport is retired without a compatibility path. `.agents/ARCHITECTURE.md` remains normative.

## Consequences

Superseded by the 2026-08-13 lean-heart architecture. Hosted recapture is not a required Atlas seam. An inert hosted-only runtime operation may remain; ordinary JSON/CLI work and default `/atlas-ask` intents do not require it.
