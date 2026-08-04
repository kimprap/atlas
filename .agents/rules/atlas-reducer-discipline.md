---
description: Use for freestyle Atlas vault mutation or answers when not following an /atlas-* skill checklist.
---

# Atlas reducer discipline

Skills own full procedures. This rule only constrains freestyle defaults so agents do not invent write sets or answer from dirty state.

Applies to any bound instance and runtime (local agent, CI, serverless). All vault I/O uses logical `vault://atlas/…` paths via the active connector — not assumed host paths.

## Activation

**Apply when:** freestyle work would create/update sources, registries, topics, passes, or produce a topic answer without using `/atlas-ask` to select the matching Workflow Owner and qualified internal resource.

**Do not apply when:** already executing the `/atlas-ask` front door and selected owner end-to-end, pure product-package edits with no vault writes, or read-only explanation of architecture.

Prefer `/atlas-ask` with the explicit source, acquisition, route, research, refresh, answer, audit, index, or migrate intent. Never bypass the front door with a removed direct owner command or unqualified owner resource.

Before any freestyle mutation, load the matching `/atlas-ask` intent and owner procedure. Registry or freshness writes must come only from validated `scripts/atlas_state.py` reducer output whose input hashes still match; source-artifact writes must pass `scripts/atlas_quality.py`. If either reference tool or a fixture-conformant port is unavailable, halt mutation.

## Write-set seams

- No silent write-set widening. New write targets need an architecture or migration update first.
- **Route** never writes topic `INDEX.md` — only route status, `RELATIONS.md`, and dirty-cache fields on `TOPICS.md`.
- **Answer** is read-only. If freshness ≠ `current`, halt (`dirty`, `refreshing`, or `blocked`) — no invented auto-refresh and no answer from pending deltas.
- **Acquire / source** never create domains, tags, topics, or aliases. Noncanonical phrases → `candidate_terms`; promotion is index/research work.
- **Research** is vault-only unless acquisition is explicitly allowed.
- **Audit** is read-only unless the caller uses an explicit repair entrypoint through `/atlas-ask`.
- Dirty counts / pending edge IDs / freshness are **recomputed from `RELATIONS.md`** — never incremented blindly.
- Never let model output choose Markdown table placement, calculate cache arithmetic, or author a fallback registry mutation. Models propose typed assessments, summaries, verifier reasons, and route decisions; deterministic tools accept or reject and render state.
- Source drafting is context-neutral. Taxonomy and routing occur only after the semantic draft passes and cannot rewrite source claims.

## Patch posture

- Patch managed sections; do not rewrite whole files unless empty or structurally broken.
- Preserve freeform notes outside managed sections.
- Optional split files (`SOURCES.md`, `DECISIONS.md`, `HISTORY.md`) only after documented size thresholds — do not pre-create.
- Missing evidence → report the gap; do not fill with model priors.

## Non-goals

- Route algorithms, edge-ID formulas, registry enums → `.agents/ARCHITECTURE.md` / `vault://atlas/ARCHITECTURE.md`, `skill://atlas-core/assets/markdown-registry-contracts.md`
- Full pass/section checklists → `skill://atlas-ask/owners/<owner-id>/OWNER.md` resources
- Ownership of product package vs bound instance → `rule://atlas-boundaries` (or `.agents/rules/atlas-boundaries.md`)

## Activation checks

- **Positive:** freestyle “route this source and update the topic answer”, “answer even though the topic is dirty”, “add a new vocab tag while acquiring”
- **Near-miss:** “explain how route-source works”, “edit an owner resource only through its qualified `/atlas-ask` workflow”
