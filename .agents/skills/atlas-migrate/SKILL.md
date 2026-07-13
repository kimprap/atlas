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

1. `vault://atlas/ARCHITECTURE.md` (runtime snapshot; author product text at `.agents/ARCHITECTURE.md`)
2. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`

Handle only explicit Atlas Markdown migrations. Prefer additive changes, preserve user content, define rollback before edits, and reject storage or retrieval changes that the architecture and migration scope do not authorize.

Treat command arguments as migration scope and target schema details. Do not use this entrypoint for normal source, research, refresh, answer, audit, or index work.

If the migration changes product-owned `.agents/ARCHITECTURE.md`, identify the intended bound instances, obtain required approval before non-development writes, sync only those named instances, then run `python3 scripts/atlas-instance.py check`. Update `scaffold/` templates only when empty-state shape changes; never re-seed living rows.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
