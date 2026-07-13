---
description: Use for freestyle Atlas vault mutation or answers when not following an /atlas-* skill checklist.
---

# Atlas reducer discipline

Skills own full procedures. This rule only constrains freestyle defaults so agents do not invent write sets or answer from dirty state.

Applies to any bound instance and runtime (local agent, CI, serverless). All vault I/O uses logical `vault://atlas/…` paths via the active connector — not assumed host paths.

## Activation

**Apply when:** freestyle work would create/update sources, registries, topics, passes, or produce a topic answer without loading the matching `/atlas-*` / `skill://atlas-*` checklist.

**Do not apply when:** already executing an `/atlas-*` skill end-to-end (follow that skill + contracts), pure product-package edits with no vault writes, or read-only explanation of architecture.

Prefer the matching entrypoint for source, route, research, refresh, answer, audit, index, or migrate.

## Write-set seams

- No silent write-set widening. New write targets need an architecture or migration update first.
- **Route** never writes topic `INDEX.md` — only route status, `RELATIONS.md`, and dirty-cache fields on `TOPICS.md`.
- **Answer** is read-only. If freshness ≠ `current`, halt (`dirty`, `refreshing`, or `blocked`) — no invented auto-refresh and no answer from pending deltas.
- **Acquire / source** never create domains, tags, topics, or aliases. Noncanonical phrases → `candidate_terms`; promotion is index/research work.
- **Research** is vault-only unless acquisition is explicitly allowed.
- **Audit** is read-only unless the caller uses an explicit repair entrypoint.
- Dirty counts / pending edge IDs / freshness are **recomputed from `RELATIONS.md`** — never incremented blindly.

## Patch posture

- Patch managed sections; do not rewrite whole files unless empty or structurally broken.
- Preserve freeform notes outside managed sections.
- Optional split files (`SOURCES.md`, `DECISIONS.md`, `HISTORY.md`) only after documented size thresholds — do not pre-create.
- Missing evidence → report the gap; do not fill with model priors.

## Non-goals

- Route algorithms, edge-ID formulas, registry enums → `.agents/ARCHITECTURE.md` / `vault://atlas/ARCHITECTURE.md`, `skill://atlas-core/assets/markdown-registry-contracts.md`
- Full pass/section checklists → owning skills
- Ownership of product package vs bound instance → `rule://atlas-boundaries` (or `.agents/rules/atlas-boundaries.md`)

## Activation checks

- **Positive:** freestyle “route this source and update the topic answer”, “answer even though the topic is dirty”, “add a new vocab tag while acquiring”
- **Near-miss:** “explain how route-source works”, “edit `.agents/skills/atlas-route/SKILL.md` only”
