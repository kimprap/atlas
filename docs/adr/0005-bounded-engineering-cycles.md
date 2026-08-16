# ADR 0005: Bounded Engineering Cycles

## Status

Superseded

## Context

A reproducible product-framework defect may require engineering diagnosis or repair, but coupling that work to an Atlas task can create an unbounded retry loop or accidentally authorize mutation of a bound instance. No-repair findings can be useful terminal evidence even when no code changes.

## Decision

Route defects through a separately approved `dev-ask` lifecycle; let `dev-ask` choose the engineering route and `dev-implementation` own its attempts and assurance. A terminal repaired or no-repair result issues an ephemeral receipt only when current evidence permits a fresh equal-boundary Atlas execution. One original request may consume at most three sequential receipts and therefore at most four Atlas executions. Recovery defects additionally require proof that the native recovery request can be reconstructed from the unchanged request, material answers, and existing durable owner state; engineering never writes the bound instance.

## Consequences

Superseded by the 2026-08-13 lean-heart architecture. Atlas no longer requires Engineering Cycle retry or automatic engineering dispatch. A `framework-defect` may still present a separate `dev-ask` route; Atlas approval never authorizes engineering and never redispatches from a receipt.
