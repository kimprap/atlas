# ADR 0004: Vault-only research and explicit acquisition

## Status

Accepted

## Context

Research answers need durable provenance and a clear distinction between evidence already materialized in Atlas and new discovery. Implicit fetching during synthesis would make freshness, authority, and reproducibility unclear and could turn a bounded request into an uncontrolled crawl.

## Decision

Research reads existing Atlas artifacts through the vault by default. Acquisition is allowed only when the request explicitly authorizes it and follows the bounded acquisition and source-owner handoff. Raw external results are untrusted input until the source workflow validates and materializes them; research does not silently fetch, crawl, or treat provider output as canonical state.

## Consequences

A topic answer has a visible evidence boundary and can be reproduced from vault artifacts. Users must explicitly opt into acquisition when evidence is missing, and acquisition remains bounded instead of becoming an implicit research side effect.
