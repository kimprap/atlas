# ADR 0001: Single-entry Atlas orchestration

## Status

Accepted

## Context

The former Atlas surface exposed a generic router, nine direct expert commands, and workflows that could be entered without one common approval and transport boundary. Later the front door required a harness-specific strict Task dispatch. That made owner selection consistent but stalled same-agent local and serverless runtimes that already load an owner in process.

## Decision

Use `/atlas-ask` as the sole public Atlas behavior entry. The same agent classifies one bounded goal, obtains material choices before approval, presents a Goal and Effect overview, and loads the selected owner in the same agent. Nested Task or JSON-schema transport is optional and never a stop. Internal owner IDs remain ordinary resources; their façade boundaries and write sets remain with the selected owner. `.agents/ARCHITECTURE.md` remains the normative contract.

## Consequences

Users have one understandable entrypoint and one approval boundary. Direct command and unqualified owner bypasses disappear, while owner-native behavior does not move into the front door. Harness-specific Task transport is no longer a capability stop.
