---
name: atlas-route
description: >
  Atlas route-source entrypoint. Use when the user invokes /atlas-route or
  wants to re-run deterministic source-to-topic routing for one source or a
  bounded source range.
disableModelInvocation: true
---

# atlas-route

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/markdown-registry-contracts.md`
3. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
4. `vault://atlas/summaries/sources/MANIFEST.md`
5. `vault://atlas/summaries/registry/VOCAB.md`
6. `vault://atlas/summaries/registry/TOPICS.md`
7. `vault://atlas/summaries/registry/RELATIONS.md`
8. the source artifact or bounded source range being routed

## Workflow

- Route-source is a reducer. It must not edit topic `INDEX.md`.
- Normalize source metadata against `VOCAB.md`; keep only canonical IDs in `canonical_tags` and move useful noncanonical phrases into `candidate_terms`.
- Build candidate topics from exact domain or subdomain matches, canonical tag overlap, alias or include-term matches in title/TL;DR/key points, and absence of `Exclude terms`.
- If no candidates survive, set source and manifest route status to `no-topic-match`, optionally log the outcome in the acquisition run log, and stop without writing `RELATIONS.md`.
- For each candidate, run a bounded verifier that outputs only `include`, `relation`, `impact`, `confidence`, and `reason`.
- For each included candidate, create or update one relation edge using the deterministic `Edge ID` contract.
- Recompute every affected topic row's dirty fields from `RELATIONS.md`; never increment dirty counts blindly.
- Set source and manifest route status to `routed` only when at least one pending relation edge exists.

## Output

Report the source scope routed, created or updated edge IDs, route status, and any missing canonical term that blocked routing.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
