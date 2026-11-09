# ADR 0010: One SQLite store per profile with numbered migrations from the first real row

## Status

Accepted

## Context

Atlas v1 kept its state as canonical Markdown files in an instance vault. v2 keeps sources, claims, quotes, topics, versions, plans, notes, call records and approvals, and searches them with BM25. A repo must be able to choose which library it uses, and test and smoke runs must never write into the real one. Once real rows exist, a schema change followed by a code rollback can leave a store the code cannot read.

## Decision

- Each profile in `~/.config/atlas/config.toml` names one SQLite file, in WAL mode with foreign keys on and FTS5 BM25 search. A repo picks its profile with `ATLAS_PROFILE`; the separate `smoke` and `eval` profiles keep test rows out of `main`.
- Records and search sit behind one store interface. SQLite is its only v2 adapter; a hosted store is a later adapter.
- Writes are one transaction per item, so a stop keeps finished work. Archive hides; nothing is hard-deleted.
- Before the first real profile (build stage 4), the schema is rebuilt from `schema_dev.sql` when it changes. Stage 4 freezes it into `migrations/0001_baseline.sql` with `PRAGMA user_version = 1`; every later schema change is the next numbered migration, applied in one transaction when the store opens.
- The release run tags only when the shipped files changed, and bumps the minor version when that change adds a migration, the patch otherwise. A store whose `user_version` is newer than the code stops with exit 1: "store is newer than this Atlas; check out a newer tag".

## Consequences

Rolling back past a minor version leaves the store newer than the code, which stops instead of guessing; recovery is restoring the store from backup or checking out a newer tag. Before stage 4 only the disposable `smoke` store exists, so rebuilding it loses nothing. Backup stays outside Atlas: the host's backup job copies the store files. Rejected: Markdown files plus an index (two copies to keep in sync); one global store (a repo cannot use a different library); patch-only version numbers (a rollback would not show that the store is newer than the code).
