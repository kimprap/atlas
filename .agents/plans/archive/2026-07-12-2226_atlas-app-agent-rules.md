# Atlas app agent rules (high-value, non-brittle)

**Datetime**: 2026-07-12-2226
**Scope**: `atlas/app` local agent rules under `cwd/.agents/rules/` only; no skill/contract/schema rewrites
**Summary**: Add three rulebook rules that cover ownership, freestyle reducer discipline, and skill-surface authoring — the seams where freestyle agents fail without loading `/atlas-*` skills — without duplicating architecture tables or skill checklists.
**Status**: DONE

## Execution intent

End state:

- `cwd/.agents/rules/` exists with exactly three Tier-1 rule files (unless Tier-2 is explicitly expanded later).
- Each rule is rulebook-style (`alwaysApply: false`), one purpose, ~30–80 lines, with explicit non-goals and pointers to SO files.
- Rules do not re-encode registry schemas, edge-ID formulas, or full `/atlas-*` checklists.
- No always-apply Atlas rule is added; `.agents/AGENTS.md` stays the always-on product map.
- Living vault instances, `ARCHITECTURE.md` body, skills, and contracts are unchanged by this work.

## Context (why)

| Surface | Role | Gap |
|---|---|---|
| `.agents/AGENTS.md` (`alwaysApply: true`) | Product map | Dense; not a write-seam interrupt |
| `ARCHITECTURE.md` + `atlas-core` assets | Framework SO + contracts | Only loaded when pointed at |
| `.agents/skills/atlas-*` | Workflow checklists | Most entry skills `disableModelInvocation: true` — not auto-loaded freestyle |
| `.agents/commands/*.md` | Thin `skill://…` wrappers | Slash-only |
| `cwd/.agents/rules/` | **Missing** | No local ownership/reducer/authoring guardrails |

**Principle:** skills own procedures; architecture/contracts own schemas; **local rules own the few cross-cutting seams where freestyle agents default wrong without loading a skill.**

**Location hard requirement:** all local-level rules live under **`/Users/kim/Desktop/ng3/atlas/app/.agents/rules/`** (`cwd/.agents/rules/`). Do not place product rules in `~/.dotfiles`, `~/.agents/rules/`, or `.grok/rules/` for this work.

Reference style only: `/Users/kim/.dotfiles/.agents/rules/{nvim,nvim-testing,omp-lsp}.md` and global plan/git under `~/.agents/rules/` (do not re-home those).

## What rules own vs not

| Own in rules | Keep out of rules |
|---|---|
| Product / vault / scaffold ownership seams | Full route/refresh/answer checklists → skills |
| Write-set / mode discipline (reducer level) | Registry column enums, edge ID formula → contracts |
| Skill/command authoring when editing `.agents/` | Artifact templates → digest assets |
| Smoke-fixture + destructive-action guardrails (short) | Generic git/plan conventions → global rules |
| Short deferred-capability fence (Tier-2 only) | Instance content repair playbooks → audit/migrate skills |

## Tier-1 rule specs (implement these)

### R1 — `atlas-boundaries.md` (ownership & binding)

- **Type:** rulebook; `alwaysApply: false`
- **Failure mode:** research state in app repo; hand-edit instance `ARCHITECTURE.md`; product bodies under `scaffold/`; `vault://digest` or second root; provision treated as deploy; skills copied to dotfiles
- **Body must include:**
  - App = product (skills, contracts, app-root `ARCHITECTURE.md` authoring, scaffold, provision script)
  - `../vault/instances/<id>/` = living instance state only
  - `scaffold/` = seed-once empty templates only (no product_owned bodies, personal rows, `runs/`, topics)
  - Author framework at app-root `ARCHITECTURE.md`; materialize with `python3 scripts/atlas-instance.py sync-framework` then `check` — never hand-copy trees
  - Logical vault root `vault://atlas/` only
  - Harness surface stays under `.agents/`; do not install product skills into machine dotfiles
  - Ask before deploy, credential use, production profile writes, or destructive registry repair
  - Explicit **Non-goals** (CLI flag encyclopedia, connector internals)
- **Frontmatter:**
  ```yaml
  ---
  description: Atlas product vs vault vs scaffold ownership and binding seams for this app repo.
  alwaysApply: false
  ---
  ```

### R2 — `atlas-reducer-discipline.md` (freestyle workflow)

- **Type:** rulebook; `alwaysApply: false`
- **Failure mode:** freestyle work rewrites whole topics, answers dirty topics, promotes vocab during acquire, pre-creates optional split files, silently widens write sets
- **Body must include (principles only; point to skills for procedures):**
  - Prefer matching `/atlas-*` or `skill://atlas-*` over ad-hoc vault mutation for source/route/research/refresh/answer/audit/index/migrate
  - No silent write-set widening; architecture or migration first if a new write target is needed
  - Route never writes topic `INDEX.md` (route status + `RELATIONS.md` + dirty cache on `TOPICS.md` only)
  - Answer is read-only; halt when freshness ≠ `current` (no invented auto-refresh)
  - Acquire/source do not create domains/tags/topics; noncanonical phrases → `candidate_terms`
  - Research defaults vault-only; acquisition only with explicit allow
  - Dirty fields recomputed from `RELATIONS.md` (never blind increments)
  - Patch managed sections only; preserve user-owned freeform notes
  - Optional split files threshold-driven only
  - On insufficiency: report the gap; do not fill with model priors
  - Explicit **Non-goals** (no route algorithm, pass section lists, or frontmatter schemas)
- **Frontmatter:**
  ```yaml
  ---
  description: Freestyle Atlas reducer write-set and freshness discipline when not inside an /atlas-* skill.
  alwaysApply: false
  ---
  ```

### R3 — `atlas-skill-surface.md` (harness authoring)

- **Type:** rulebook + globs; `alwaysApply: false`
- **Failure mode:** fat command stubs; duplicated checklists; contracts drift from architecture; new entrypoint without architecture row; Phase-1 SQLite helpers
- **Body must include:**
  - Change order: **`ARCHITECTURE.md` → atlas-core contracts → owning skill(s) → thin command stub**; then `sync-framework` if product_owned changed
  - Commands stay thin (`skill://…` + args); checklists in skills; shared determinism in `atlas-core`
  - `atlas-core` remains support-only (no user entrypoint)
  - Do not reintroduce a second vault root or expand `digest` into a full workflow
  - New behavior needs architecture mode/write-set note or explicit migration, not only a skill bullet
  - Fixture-cleanup obligation on entry skills; no leftover smoke rows in personal instances
  - Phase 1: no ad hoc SQLite registry path under skills
  - Explicit **Non-goals** (YAML field catalogs; OMP skill tutorial)
- **Frontmatter:**
  ```yaml
  ---
  description: Conventions for authoring Atlas skills, thin slash commands, and shared contracts in this repo.
  alwaysApply: false
  globs:
    - ".agents/skills/**"
    - ".agents/commands/**"
    - ".agents/skills/atlas-core/assets/**"
  ---
  ```

## Tier-2 (do not implement in this plan)

Deferred unless freestyle failures prove need after Tier-1:

| File | Layer | Trigger idea |
|---|---|---|
| `atlas-scaffold-writes.md` | TTSR tool-only | writes under `scaffold/**`, provision script, product_owned |
| `atlas-instance-writes.md` | TTSR tool-only | writes under `../vault/instances/**` / living registry paths (careful noise) |
| `atlas-phase-boundaries.md` | small rulebook | SQLite, EVENTS.md, UNCLAIMED-SOURCES, LLM-in-hooks, unconstrained crawl, pre-created domain folders |

Also **do not create:** always-apply Atlas bible; full schema/header rules; per-entrypoint skill mirrors; local git/plan rules (globals already cover).

## Critical anchors

| Path / symbol | Use |
|---|---|
| `cwd/.agents/rules/` | **Only** create location for local rules |
| `cwd/.agents/AGENTS.md` | Always-on product map; do not duplicate; optional one-line pointer only if discovery is weak |
| `cwd/ARCHITECTURE.md` | Mode ownership, phase deferrals — point, don’t paste |
| `cwd/.agents/skills/atlas-core/assets/markdown-registry-contracts.md` | Schemas/reducers — point |
| `cwd/.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md` | Cadence/hooks — point |
| `cwd/scaffold/MANIFEST.json` | product_owned vs seed_once vs never_touch |
| `cwd/scripts/atlas-instance.py` | create / sync-framework / check |
| `/Users/kim/.dotfiles/.agents/rules/*.md` | Frontmatter/style reference only |
| `craft-rule` skill | rulebook default; TTSR only with narrow scope |

## Assumptions and fallbacks

1. **ASSUMPTION:** OMP (and compatible harnesses used with this repo) discover `cwd/.agents/rules/*.md`. **FALLBACK if not:** add a single pointer line under Agent workflow conventions in `.agents/AGENTS.md` listing the three rule basenames — no content duplication.
2. **ASSUMPTION:** Execution scope is Tier-1 only. **FALLBACK:** if user asks for stream-time write correction in the same pass, implement at most one of scaffold-write or instance-write TTSR with tool-only scope and re-verify near-miss negatives; do not ship both without noise testing.
3. **ASSUMPTION:** No AGENTS.md slim-down in this pass. **FALLBACK:** only the optional one-line rules pointer from (1).
4. **ASSUMPTION:** Global plan/git rules remain authoritative for plans and commits. **FALLBACK:** never create local copies of those rules.

## Tasks

- [x] T1. Create `cwd/.agents/rules/` and write `atlas-boundaries.md` per R1 (frontmatter + body + non-goals)
  completed 2026-07-12-2227
- [x] T2. Write `atlas-reducer-discipline.md` per R2
  completed 2026-07-12-2227
- [x] T3. Write `atlas-skill-surface.md` per R3 (include globs)
  completed 2026-07-12-2227
- [x] T4. Optionally add one pointer line in `.agents/AGENTS.md` only if rule discovery is uncertain; otherwise skip with a note
  completed 2026-07-12-2227
- [x] T5. Run verification checklist (mechanical + positive/near-miss activation notes); leave Tier-2 uncreated
  completed 2026-07-12-2227

## Ordered implementation (maps to tasks)

1. **T1** — `mkdir -p .agents/rules` if needed; write R1 first (ownership is the highest-cost freestyle failure).
2. **T2** — write R2; keep body principle-level; link mentally to mode ownership in `ARCHITECTURE.md` without pasting the table.
3. **T3** — write R3 with globs targeting skill/command/contract paths only.
4. **T4** — decide pointer: if harness docs/user practice already load `.agents/rules`, skip; else one line under Agent workflow conventions.
5. **T5** — verify; do not touch vault instances, scaffold content, or skill bodies.

## Verification / Done criteria

- [x] `ls .agents/rules/` lists exactly: `atlas-boundaries.md`, `atlas-reducer-discipline.md`, `atlas-skill-surface.md` (no Tier-2 files)
- [x] Each file has YAML frontmatter with `description` and `alwaysApply: false` (R3 also has `globs`)
- [x] No rule has `alwaysApply: true`
- [x] No rule inlines registry table headers, edge-ID formulas, or full workflow checklists
- [x] Each rule has an explicit Non-goals (or equivalent) subsection
- [x] `python3 scripts/atlas-instance.py check` still exits 0 (rules work must not mutate instances)
- [x] Delivered work paths are `.agents/rules/**` (+ this plan under `.agents/plans/`); no `.agents/AGENTS.md` edit; pre-existing untracked files outside this scope left untouched
- [x] Positive activation notes documented (in completion summary or plan note):
  - boundaries: “edit architecture only on personal instance”, “seed a topic under scaffold”, “copy skills to dotfiles”
  - reducer: freestyle “route and also rewrite topic answer”, “answer while dirty”
  - skill-surface: “put full checklist in the slash command file”
- [x] Near-miss negatives documented: pure README typo; read-only architecture explain; ordinary git commit (global git rule only)

## Skill outcomes to capture

- From architecture/product read: freestyle agents miss skill contracts because entry skills are invocation-gated — rules must cover **seams**, not re-host checklists.
- From craft-rule heuristics: rulebook-first; TTSR deferred; no always-apply Atlas layer; one purpose per file; non-goals required.
- No eng-tdd/domain-modeling skill run required for this harness-policy work.

## Completion Summary

- **Delivered (T1–T3):** three rulebook rules under `.agents/rules/`:
  - `atlas-boundaries.md` — product / vault / scaffold ownership
  - `atlas-reducer-discipline.md` — freestyle write-set + freshness posture
  - `atlas-skill-surface.md` — skill/command/contract authoring + globs
- **T4 skipped:** no AGENTS.md pointer; repo already uses `.agents/` locality and rules dir is the standard OMP surface.
- **T5:** `atlas-instance.py check` OK; each rule ~33–39 lines, `alwaysApply: false`, Non-goals present; no Tier-2 files; no schema/checklist paste.
- **Activation notes (intended):**
  - boundaries → wrong authoring surface / scaffold seed / dotfile skill install
  - reducer → freestyle route+topic rewrite / answer-while-dirty
  - skill-surface → fat slash-command checklists
- **Near-misses (should stay quiet):** README typo; read-only architecture explain; ordinary git commit (global git rule).
- **Residual risk:** rulebook load depends on harness discovery of `cwd/.agents/rules/`; no TTSR stream interrupts yet (Tier-2 deferred by design).
- **Outcome:** plan complete; Tier-1 seams shipped without touching skills, contracts, architecture, or instances.
