# ADR 0002: Separate product and instance state

## Status

Accepted

## Context

Atlas framework contracts, scaffold templates, and provision tooling belong to the product package, while sources, registries, topics, and passes belong to a bound research instance. Treating those surfaces as one tree risks copying living data into the product or editing a snapshot as if it were framework authority.

## Decision

Author framework decisions in the product package, with `.agents/ARCHITECTURE.md` as the canonical contract. Access living state only through the logical `vault://atlas/` root and the active connector profile. Keep `scaffold/` limited to empty seed-once templates, and update an intended instance snapshot only through the existing framework-sync path.

## Consequences

Product changes can be packaged and provisioned without embedding research data. Instance content remains independently owned and protected from re-seeding, while framework drift has one explicit synchronization boundary. Connector portability remains a deployment concern rather than a second architecture authority.
