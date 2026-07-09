---
name: atlas-migrate
description: >
  Atlas schema-migration entrypoint. Use when the user invokes /atlas-migrate
  or requests an explicit Atlas Markdown schema migration with a defined target,
  rollback path, and verification checks.
disableModelInvocation: true
---

# atlas-migrate

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
3. `.agents/plans/2026-07-07-1145_atlas-command-cutover.md`

Current cutover role: handle only explicit Atlas Markdown migrations. Prefer additive changes, preserve user content, define rollback before edits, and refuse any implicit SQLite, FTS, vector-retrieval, or direct-SQL path while those phases remain deferred.

Treat command arguments as migration scope and target schema details. Do not use this entrypoint for normal source, research, refresh, answer, audit, or index work.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
