# Atlas Guidance Discovery Alignment

**Datetime**: 2026-08-04-1423
**Scope**: Repository-local Atlas guidance discovery, scoped rule alignment, ADR lookup integrity, and harness-surface verification
**Summary**: Make the always-applied repository guidance a lean discovery router for canonical non-rule contracts, align the three auto-discovered Atlas seam rules with the redesigned single-entry architecture, and prevent ADR lookup drift without listing individual ADRs in `AGENTS.md`.
**Status**: DONE

## Context

`.agents/AGENTS.md` is the repository bootstrap available to agent and subagent sessions, while `.agents/ARCHITECTURE.md` and ADR bodies are canonical or explanatory documents that are not assumed to inject automatically. The current `Conditional rationale` pointer is too compressed, `atlas-reducer-discipline.md` still describes a former freestyle/direct-owner fallback, and four ADR index links target headings removed by the architecture redesign. The end state keeps `AGENTS.md` small: it routes tasks to the normative architecture, the ADR index, and the owning contract; it does not duplicate those documents or enumerate ADR files.

## Tasks

- [x] T1. Install the canonical contract-discovery bootstrap in `.agents/AGENTS.md`
  - completed 2026-08-04-1438
- [x] T2. Align the three Atlas seam rules with the redesigned front door and ownership boundaries
  - completed 2026-08-04-1440
- [x] T3. Repair ADR lookup anchors and add deterministic harness-surface regressions
  - completed 2026-08-04-1442
- [x] T4. Verify focused behavior, fresh-agent discovery, and package invariants
  - completed 2026-08-04-1542

## Approach

### T1. Install the canonical contract-discovery bootstrap

In `.agents/AGENTS.md`, replace the existing `Seam details:` line with exactly:

```markdown
Harness-discovered seam rules: `.agents/rules/atlas-boundaries.md`, `atlas-reducer-discipline.md`, and `atlas-skill-surface.md`. This file bootstraps discovery of canonical non-rule contracts; it does not duplicate rule bodies.
```

Replace the complete `## Conditional rationale` section with:

```markdown
## Contract discovery

Load only the narrow authority required before deciding or editing:

| Task | Required discovery |
|---|---|
| Change a framework boundary, product/instance ownership, public entry or owner dispatch, canonical state/projection, mode/write set, deterministic runtime ownership, acquisition/research boundary, Engineering Cycle, or migration | Read `.agents/ARCHITECTURE.md` first; it is normative. Then read the owning artifact from `## Source of truth`. |
| Need accepted rationale for one of those decisions | Read `docs/adr/INDEX.md`, then only rows whose `Task trigger` matches. |
| Work within an established seam without changing durable behavior | Read only the owning artifact from `## Source of truth`; do not scan ADRs. |

ADRs explain why and never override `.agents/ARCHITECTURE.md`. Do not list individual ADRs here; `docs/adr/INDEX.md` owns ADR inventory and trigger mapping.
```

Insert this exact row immediately after `Framework invariants` in the existing `## Source of truth` table:

```markdown
| Accepted architecture rationale lookup | `docs/adr/INDEX.md` → matching ADR only |
```

Preserve the existing `alwaysApply: true` frontmatter, ownership summary, layout, stale-plan gate, entrypoints, tool inventory, and verification bullets. Do not add architecture content, ADR titles, owner checklists, memory-loader instructions, or harness-specific injection internals to this always-loaded file.

### T2. Align the three Atlas seam rules

Preserve `.agents/rules/atlas-reducer-discipline.md` as the discovered rule identity, but replace its complete content with:

```markdown
---
description: Use when Atlas vault work, topic answers, or owner-resource loads would bypass the /atlas-ask front door.
---

# Atlas front-door discipline

Qualified Workflow Owners own Atlas procedures. This rule stops unsupported bypasses; it grants no Atlas I/O authority.

## Activation

**Apply when:** a direct request would perform Atlas semantic, façade, profile, or vault work; answer a topic; load an owner resource; or call a removed owner path outside a qualified `/atlas-ask` workflow.

**Do not apply when:** a selected Workflow Owner is already running end-to-end, work changes only the product package with no Atlas I/O, or architecture is only being explained.

## Boundary

Atlas semantic, façade, profile, and vault work never runs freestyle. Re-enter through `/atlas-ask`.

- Only a qualified selected Workflow Owner Task or allowlisted same-agent Successor Owner may load an owner resource and call `scripts/atlas_tool.py`.
- Never load an owner directly, call a removed owner command, let the Atlas Orchestrator perform profile/vault/façade I/O, import an underlying deterministic owner as a workflow bypass, or reconstruct a missing aggregate result.
- If strict Task transport or a required façade capability is unavailable, stop with `capability-unavailable`; never fall back to direct vault edits.
- A new write target requires an architecture change or explicit migration before workflow implementation.
- Model output never owns identity, Markdown placement, cache arithmetic, transaction effects, or write authority.

## Non-goals

- Workflow procedures and write sets → `/atlas-ask`, qualified owner resources, and `atlas-core` contracts
- Product package versus bound-instance ownership → `rule://atlas-boundaries`
- Skill, command, and shared-contract authoring → `rule://atlas-skill-surface`

## Activation checks

- **Positive:** “mutate `TOPICS.md` directly because owner dispatch is unavailable”, “load the research owner and answer without `/atlas-ask`”
- **Near-miss:** “run an approved research Workflow Owner end-to-end”, “edit `.agents/ARCHITECTURE.md` with no Atlas I/O”
```

This removes the duplicated per-owner write-set catalogue, direct deterministic-owner fallback, and generic `Patch posture`; those remain owned by `.agents/ARCHITECTURE.md`, `atlas-core`, deterministic tools, and qualified owner resources. Keep the rule description-only—no `alwaysApply`, condition, scope, or TTSR metadata.

In `.agents/rules/atlas-skill-surface.md`, preserve the current path-scoped `globs` and add exactly these two bullets under `## Surface shape`:

```markdown
- The Atlas Orchestrator dispatches exactly one strict Workflow Owner Task and consumes one aggregate result. It performs no Atlas semantic, façade, profile, vault, reducer, projection, transaction, or recovery work and never reconstructs a missing result.
- A framework defect crosses a separately approved `dev-ask` boundary. Atlas approval never authorizes engineering; Engineering Cycle receipts remain ephemeral and bounded, with no persistent defect queue, retry ledger, or orchestrator-owned recovery state.
```

Do not copy owner-turn ceilings, successor matrices, wire schemas, or receipt algorithms into the rule.

In `.agents/rules/atlas-boundaries.md`, add this exact bullet under `## Seams that default wrong`:

```markdown
- `vault://atlas/todos/` is optional unmanaged user data. Provision, framework sync, package checks, and Atlas framework workflows neither require nor mutate it.
```

Preserve every other product/instance/scaffold boundary.

### T3. Repair ADR lookup anchors and add deterministic regressions

Update only the canonical-section link label and fragment in the five-row `docs/adr/INDEX.md` table; preserve each ADR number/title, task trigger, relative ADR-body link, and every accepted ADR body:

1. ADR 0001 → label `Single public entrypoint`, fragment `#single-public-entrypoint`.
2. ADR 0002 → retain `Product and instance boundary`, fragment `#product-and-instance-boundary`.
3. ADR 0003 → label `Canonical instance state`, fragment `#canonical-instance-state`.
4. ADR 0004 → label `Mode and write ownership`, fragment `#mode-and-write-ownership`.
5. ADR 0005 → label `Dispatch and result invariants`, fragment `#dispatch-and-result-invariants`.

Extend `tests/test_atlas_harness_surface.py` using the existing `AtlasHarnessSurfaceTests` text-contract style; do not add a parser dependency.

- Add `test_contract_discovery_routes_architecture_and_indexed_rationale`. It must assert that `.agents/AGENTS.md` retains `alwaysApply: true`, contains `## Contract discovery`, identifies `.agents/ARCHITECTURE.md` as normative, points to `docs/adr/INDEX.md` and matching triggers only, contains the `Accepted architecture rationale lookup` source-of-truth row, and does not match `r"docs/adr/000\d|000\d-[a-z0-9-]+\.md"`.
- In that test, compute architecture anchors exactly as `{re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-") for heading in re.findall(r"^## (.+)$", architecture, flags=re.MULTILINE)}`. Extract index fragments with `re.findall(r"\.\./\.\./\.agents/ARCHITECTURE\.md#([^)]+)", index)`, assert the list length is five, and assert every extracted fragment is in the architecture-anchor set. This converts the observed stale-link failure into a deterministic regression without a parser dependency.
- Add `test_repo_rules_encode_current_front_door_boundaries`. It must read all three Atlas rules and assert: reducer guidance names `/atlas-ask`, `scripts/atlas_tool.py`, `qualified selected Workflow Owner Task`, `capability-unavailable`, and `never fall back to direct vault edits`; reducer guidance contains neither the literal `/atlas-*` nor `scripts/atlas_state.py`/`scripts/atlas_quality.py`; skill-surface guidance contains the exact two new bullets from T2; boundary guidance contains the exact unmanaged-`todos/` bullet from T2.

Keep the existing removed-public-path, five-ADR inventory/body-shape, stale-plan gate, single-command, and owner-resource assertions unchanged.

### T4. Verify the discovery behavior and package

From `/Users/kim/dev/atlas/app`, run the focused regression first:

```bash
python3 -m unittest tests.test_atlas_harness_surface
```

It must exit zero and prove the new contract-discovery text, absence of individual ADR listings in `AGENTS.md`, current ADR anchor resolution, narrowed anti-bypass rule, one-owner orchestrator boundary, separate Engineering Cycle authority, and unmanaged `todos/` boundary.

Then run the complete Atlas test set and read-only package check:

```bash
python3 -m unittest discover -s tests -p 'test_atlas_*.py'
python3 scripts/atlas-instance.py check --name atlas
```

Both must exit zero. Do not run `sync-framework`: `.agents/ARCHITECTURE.md` and the product-owned instance snapshot are unchanged by this plan.

Finally, launch one fresh read-only `scout` subagent from the repository root with no Context Pack containing contract paths and no permission to search files or use tools. Give it exactly this behavioral prompt:

```text
Answer only from repository guidance already injected into this fresh session:
1. How must a direct request to mutate Atlas topic state be routed?
2. Before changing Atlas research write-set semantics, which non-rule authority is read first, and how is accepted rationale selected?
Do not inspect repository files.
```

The smoke passes only if the fresh subagent routes mutation through `/atlas-ask`, identifies `.agents/ARCHITECTURE.md` as the normative first read, selects rationale through `docs/adr/INDEX.md` and only matching ADR triggers, and does not propose scanning every ADR or directly invoking an owner/tool/vault path. Record this as OMP parent/subagent evidence only; the static root `AGENTS.md`, `.cursor/rules`, and `.cursor/skills` alias test remains the cross-harness packaging proof. If the fresh subagent lacks the injected repository guidance, stop and report the harness capability gap; do not compensate by duplicating contracts into rules or adding a new guidance file.

## Critical files & anchors

- `.agents/AGENTS.md` — `## Conditional rationale`, early seam pointer, and `## Source of truth`; becomes the lean non-rule contract-discovery bootstrap.
- `.agents/rules/atlas-reducer-discipline.md` — stale `/atlas-*` description and freestyle/direct deterministic-owner fallback; refactor to fail-closed front-door discipline.
- `.agents/rules/atlas-skill-surface.md` — `## Surface shape`; add only the redesigned orchestrator and Engineering Cycle authoring invariants.
- `docs/adr/INDEX.md` — five-row task-trigger cache whose architecture fragments must resolve without listing ADRs in always-loaded guidance.
- `tests/test_atlas_harness_surface.py` — existing public-surface, active-guidance, ADR inventory, and root-alias regression owner.

## Verification / Done criteria

- [x] Focused contract proof: `python3 -m unittest tests.test_atlas_harness_surface` from the app root.
- [x] Full package proof: `python3 -m unittest discover -s tests -p 'test_atlas_*.py'`.
- [x] Bound-instance invariant proof without mutation: `python3 scripts/atlas-instance.py check --name atlas`.
- [x] Fresh-session behavior: one no-tools OMP scout answers the two injected-guidance scenarios exactly as specified in T4.
- [x] Final inspection: `.agents/AGENTS.md` contains no individual ADR filename or duplicated ADR decision text; all three rule frontmatters remain minimal; `atlas-skill-surface.md` retains its current `globs`; no fourth rule, architecture edit, ADR-body edit, skill/command edit, instance write, or framework sync exists.

## Assumptions & contingencies

- `.agents/AGENTS.md` remains the repository’s `alwaysApply: true` bootstrap and the root `AGENTS.md`/Cursor aliases remain governed by the existing harness-surface test. The implementation changes the canonical `.agents/` files only, never aliases.
- `.agents/ARCHITECTURE.md` remains normative and unchanged. If an equivalent section is renamed before implementation, update the ADR index to the current equivalent heading and its derived fragment; if the underlying decision changed rather than only the heading, stop for authority drift instead of guessing a new mapping.
- ADRs remain accepted rationale, not authority. Preserve all five bodies and let `docs/adr/INDEX.md` alone own their inventory and task-trigger map.
- No new repo-local rule is warranted: deterministic runtime seams are already owned by architecture, contracts, code, and tests; adding a runtime/orchestration/Engineering Cycle rule would duplicate the selected scoped owners.
- The fresh-subagent check proves the currently available OMP injection path, not every third-party harness implementation. If it fails, report the exact missing injection behavior and leave the contract changes unclaimed rather than broadening always-loaded guidance.

## Execution overrides

- 2026-08-04-1456: T4 exposed 27 pre-existing `test_atlas_tool.py` failures outside the original six-file guidance target. The user explicitly authorized expanding T4 to repair `scripts/atlas_tool.py` as required by the current architecture, registry contract, and existing regressions, then rerun the complete Atlas verification.
- 2026-08-04-1526: The user explicitly resolved the T3 heading-level mismatch by authorizing architecture-anchor derivation from Markdown headings `##` through `######`. This preserves the precise ADR 0005 link to `### Dispatch and result invariants` without editing or synchronizing `.agents/ARCHITECTURE.md`.

## Completion Summary

- Delivered the lean contract-discovery bootstrap, fail-closed Atlas front-door rule, scoped orchestrator/Engineering Cycle and unmanaged-`todos/` boundaries, and five precise ADR architecture links.
- T4 exposed 27 existing façade regressions. Under the 2026-08-04-1456 user override, repaired canonical connector capability and eight-method mutation preflight, state-validation input/finding projection, and topic-transaction namespace closure; the owning façade matrix now covers the public mutation methods and missing `logical_root`.
- The user authorized real Markdown heading levels for ADR anchor validation at 2026-08-04-1526, preserving the precise H3 link without architecture or instance-snapshot mutation.
- Verification passed: harness 16/16; owning façade module 77/77; complete Atlas suite 272/272 twice; `atlas-instance.py check --name atlas`; and the no-tools `FreshGuidanceSmoke`.
- High-consequence assurance completed on the exact eight-file target: `agent://AtlasGuidanceVerifier3` returned `VERIFIED`; distinct `agent://AtlasGuidanceReview3` returned Standards `PASS`, Specification `PASS`, Overall `APPROVED`, with no findings. Earlier assurance attempts were invalidated and renewed after a reviewer caught a 63-character digest transcription.
- Residual risk: verifier/reviewer model-family separation was not asserted, and the complete 272-test proof was implementer-run while independent proof covered the focused 16-test and owning 77-test modules. The user explicitly waived terminal continual-learning assessment for this task.
