# ADR 0003: Canonical Markdown state

## Status

Accepted

## Context

Atlas needs state that is inspectable, reviewable, and safe to recover across connectors. Derived indexes and freshness summaries are useful, but allowing them or an opaque store to become authority would make reducer decisions difficult to audit and rebuild.

## Decision

Keep canonical registry, source, relation, topic, and pass state in the established Markdown artifacts. Deterministic reducers validate and patch managed sections while preserving unmanaged content; projections and caches remain derived from canonical rows and relations. Any future storage layer requires an explicit architecture decision with deterministic rebuild or rollback.

## Consequences

Operators can inspect state through the logical vault and compare exact revisions. Recovery and migration retain a durable textual source of truth, at the cost of keeping reducer and projection updates explicit rather than hiding them behind an optimization layer.
