---
name: digest
description: >
  Legacy Atlas compatibility adapter for old /digest invocations. Use only
  when the user explicitly invokes /digest or references the old digest
  workflow, then forward to the matching /atlas-* entrypoint.
disableModelInvocation: true
---

# digest

`digest` is a temporary compatibility shim. The dedicated Atlas entrypoints own source ingestion, acquisition, routing, research, refresh, answer, audit, index, and migration behavior.

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
3. choose the matching Atlas entrypoint skill before doing any work

## Forwarding rules

- `/digest <url...>` or legacy “digest these sources” requests -> `skill://atlas-source`
- `/digest acquire <scope>` -> `skill://atlas-acquire`
- `/digest route <source-id-or-range>` -> `skill://atlas-route`
- `/digest research --vault-only <topic>` -> `skill://atlas-research`
- `/digest research --acquire <topic>` -> `skill://atlas-research`
- `/digest refresh <topic>` -> `skill://atlas-refresh`
- `/digest answer <topic>` -> `skill://atlas-answer`
- `/digest rollup` or `/digest index` -> `skill://atlas-index`
- `/digest migrate <scope>` -> `skill://atlas-migrate`

## Compatibility behavior

- Preserve the user intent from the legacy `/digest` invocation, but execute the matching Atlas workflow instead of reintroducing digest-owned contracts here.
- Do not duplicate Atlas source, route, research, refresh, answer, audit, index, or migration checklists in this shim.
- If the legacy request is ambiguous, map it to the narrowest Atlas entrypoint that can satisfy it and state the forwarding decision.
- Keep using `vault://atlas/` as the only vault root. Do not recreate or reference any `vault://digest/` path.

## Output

Report which Atlas entrypoint handled the request, any translated flags or scope, and the resulting Atlas artifact or registry paths.
