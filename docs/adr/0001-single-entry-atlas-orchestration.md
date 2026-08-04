# ADR 0001: Single-entry Atlas orchestration

## Status

Accepted

## Context

The former Atlas surface exposed a generic router, nine direct expert commands, and workflows that could be entered without one common approval and transport boundary. That made owner selection, retained request context, and defect escalation inconsistent while the underlying owner procedures remained deterministic and useful.

## Decision

Use `/atlas-ask` as the sole public Atlas behavior entry. The main-session Atlas Orchestrator classifies one bounded goal, obtains material choices before approval, presents the exact route overview, dispatches one identity-bound strict Workflow Owner Task, and consumes one aggregate result. The nine owner IDs remain ordinary internal resources; their qualified native chains, façade boundaries, and write sets remain with the selected owner. `.agents/ARCHITECTURE.md` remains the normative contract.

## Consequences

Users have one understandable entrypoint and one approval boundary. Direct command and unqualified owner bypasses disappear, while owner-native behavior does not move into the Orchestrator. Transport, defect routing, and bounded retry can be shared without making the Orchestrator an expert Atlas worker or a second state owner.
