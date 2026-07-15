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
- Validate the complete manifest/topic/relation bundle with `scripts/atlas_state.py validate` before proposing a mutation. Orphan rows and any other finding block normal routing.
- Normalize source metadata against `VOCAB.md`; keep only canonical IDs in `canonical_tags` and move useful noncanonical phrases into `candidate_terms`.
- Build candidate topics from exact domain or subdomain matches, canonical tag overlap, alias or include-term matches in title/TL;DR/key points, and absence of `Exclude terms`.
- For each candidate, produce only the structured verifier fields `include`, `relation`, `impact`, `confidence`, and `reason`. Every included reason must be `Verifier: <source-local locator> — <source-specific claim> [relation=<relation>; impact=<impact>]`; candidate-list prose is invalid.
- Submit the complete included result as one `route-upsert` event. The reducer derives sequence, artifact path, deterministic edge IDs, legal hash transitions, route status, row placement, and every affected topic cache.
- Persist only changed documents returned by a successful reduction, and only while their exact SHA-256 preconditions still match freshly read connector state. A mismatch requires re-read and re-reduce.
- If no candidates survive, use `outcome: no-topic-match` with an empty edge list. Use `routing-blocked` only for an actual vocabulary or schema blocker.
- Never hand-place relation rows, reopen an applied edge, increment dirty counters, or fall back to a model-authored table edit when the reference reducer or a fixture-conformant port is unavailable.

## Output

Report the source scope routed, created or updated edge IDs, route status, and any missing canonical term that blocked routing.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
