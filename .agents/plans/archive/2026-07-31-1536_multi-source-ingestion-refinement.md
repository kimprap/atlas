# Lean multi-source ingestion and snapshot parser repair

**Datetime**: 2026-07-31-1536
**Scope**: Atlas explicit multi-URL presence and ingestion, parent/worker orchestration, and the `source.snapshot_active` Markdown parser defect
**Summary**: Unblock the current source workflow first, then add only the smallest reusable batch seams needed to keep deterministic Atlas mechanics out of workers and the coordinator. Preserve existing reducers, renderers, transactions, routing, acquisition logs, and recovery semantics.
**Status**: DONE

## Context

The previous plan revision became too broad. It attempted to redesign packet lineage, route classification, transaction/effect ingress, acquisition-run recovery, connector sessions, and evaluation infrastructure at the same time. That increases implementation time and creates brittle cross-module contracts.

The observed workflow needs a narrower repair:

1. `source.snapshot_active` currently fails before reading artifacts when a valid Markdown table uses normal alignment padding. `scripts/atlas_tool.py::_rows` searches for an unpadded header byte string and later splits rows naively, while `atlas_state` trims cells and understands escaped pipes. `state.validate` and `source.lookup` therefore accept the same MANIFEST that `_rows` rejects.
2. Multi-URL source work repeats normalization and manifest inspection and exposes deterministic reducer/render/transaction preparation to the parent.
3. Source workers should fetch, assess, and draft only. They should not author source IDs, registry rows, reducer events, target documents, revisions, or transaction behavior.
4. `atlas-acquire` should delegate one bounded candidate set to `atlas-source`, not start an independent full source workflow for every URL.
5. Verification should be proportional: one parser regression, focused batch behavior tests, one disposable-profile owner smoke, then the existing Atlas suite once.

This plan supersedes the earlier expansive revision at the same URI.

## Design

### Keep the existing framework

Retain these owners and semantics unchanged:

- `atlas_state` remains the canonical Markdown parser and reducer owner.
- Existing quality validators, source renderers/merge logic, and `transaction.execute|recover|successor` remain authoritative.
- Source and route effects remain separate serial transactions.
- `atlas-route` keeps its current candidate selection and route workflow.
- `atlas-acquire` keeps its current acquisition-run Markdown format and one final conditional write.
- Existing transaction records provide idempotence and recovery. Do not add run handoffs, continuation-token digests, a new effect ingress, or a second recovery protocol.
- No bound-instance schema, scaffold, connector, command-stub, or vault-root change.

### Add only three public façade operations

1. `url.resolve_reference`
   - Input: one normalized absolute HTTP(S) base URL and one nonempty URI reference.
   - Output: canonical absolute URL plus Atlas source ID.
   - Implementation: `urllib.parse.urljoin`, then the existing `atlas_url` normalizer and source-ID function.
   - Reads and writes nothing.

2. `source.inventory`
   - Input: `{intent, inputs}` where intent is `presence|routine|resummarize` and each bounded input is `{label,url,depth}` with depth `0|1`.
   - Normalizes every URL through the existing URL owner, validates MANIFEST once through the canonical `atlas_state` parser, deduplicates by canonical URL, detects source-ID collisions, and returns request-order entries plus one shared check date for write-capable intents.
   - Each entry contains only façade-derived identity, the canonical manifest row when present, a first-occurrence winner reference, and one disposition: `new|active-due|active-not-due|active|archived|duplicate|rejected`.
   - Presence mode never reads artifacts. Routine and resummarize inventory also remain read-only; per-source preparation performs the later artifact/state checks against current state.

3. `source.prepare`
   - Input: one inventory-derived identity/mode plus one final worker packet.
   - Re-reads and validates current state for only that source, so earlier serial sibling commits do not stale a whole-batch snapshot.
   - Reuses existing quality, reducer, summary rendering, merge, and source-event owners internally.
   - Returns one of:
     - `prepared`: exact existing `transaction.execute` arguments, source outcome, and whether routing is required;
     - `terminal`: no transaction, with the deterministic skip/no-write/unchanged outcome;
     - `needs-revision`: quality findings for one targeted retry by the same worker;
     - `rejected`: normalized findings and no transaction.
   - It never writes and never accepts caller-authored source IDs, event records, targets, revisions, paths, sequence numbers, or outcomes.

Use the existing version-1 façade envelope. Add no new dependency.

### One small worker contract

Add one strict `source-worker-result.schema.json` union. It covers only model/harness-owned work:

- `ready`: source identity copied from the assignment, fetched evidence envelope, proposal, seven-item checklist, and proposed next refresh date;
- `needs-input`: source-local reason and one of the existing choice sets (`page-only|expand|stop-without-writing` or `replacement-input|bounded-acquisition|stop-without-writing`);
- `expanded`: the approved aggregate's bounded depth-1 links; the container itself is not prepared as a source;
- `no-write`: source-local reason and no evidence/proposal/transaction fields.

The packet grants no write authority. `source.prepare` must revalidate identity, evidence, quality, and current Atlas state before it can return a transaction.

Do not add continuation hashes or persisted packet state. The coordinator ties a response to the assigned worker/agent and source ID in the current invocation. A material choice is asked once for the complete worker wave, then sent only to the originating worker. One failed correction or missing worker result becomes a per-source no-write/rejected outcome; it does not fabricate a packet or force valid siblings to fail.

### Bounded owner flow

`atlas-source` should use this order:

1. Pure single-URL presence stays on `source.lookup`. Multi-URL presence uses one `source.inventory` call.
2. A request explicitly asking for children/descendants may fetch and enumerate only the disclosed bounded scope. Normalize the root before fetch; resolve relative links through `url.resolve_reference`; default to depth 1 and a finite node cap. Call `source.inventory` once for the complete enumerated set. Do not fetch for ordinary presence.
3. For ingestion, call `source.inventory` once for all explicit inputs. Dispatch at most one worker per unique actionable winner, using bounded host concurrency. Duplicate, archived, and not-due entries do not get workers.
4. Collect the whole worker wave before any source write. Batch all material choices into one Ask. Approved aggregate expansion is depth 1 only; reinventory the combined root/child set once before dispatching child workers so dedupe remains façade-owned.
5. After all workers and choices settle, process winners in deterministic source-ID order. For each final packet, call `source.prepare` immediately before the existing transaction operation. On `needs-revision`, return the findings once to the same worker and retry preparation once. On `prepared`, execute using the returned arguments unchanged and preserve the existing recover/successor rules. A nonterminal transaction receipt stops later writes rather than inventing recovery authority.
6. Invoke existing `atlas-route` only for source outcomes that currently require routing. Keep the route owner and route transaction unchanged.
7. Return one compact batch result with per-input outcome, duplicate winner, source identity when known, artifact/route result when committed, and normalized failure/no-write reason. Re-running the same request is the resume mechanism: completed sources are skipped or refreshed according to current MANIFEST state and existing transaction idempotence.

`atlas-acquire` should keep discovery and its run log, but pass `discovery.normalize`'s selected bounded candidate list to one `atlas-source` invocation. It groups the returned batch outcomes with existing rejected/overflow rows and writes the existing run log once. It does not add a second inventory, reducer, renderer, or transaction path.

## Tasks

- [x] T0. Repair canonical Markdown row parsing
  completed 2026-07-31-0946 UTC

1. In `scripts/atlas_state.py`, expose the existing escape-aware, whitespace-normalizing Markdown row splitter as the shared pure table-cell parser. Keep `atlas_state` as its only semantic owner.
2. In `scripts/atlas_tool.py::_rows`, use that parser for header matching and data rows while preserving each original raw row for the existing hash/revision checks. Remove byte-exact unpadded header matching and naive `split("|")` behavior.
3. Cover all current `_rows` consumers, not only `source.snapshot_active`; padded TOPICS/RELATIONS headers and escaped pipes must parse exactly as `state.validate` parses them.
4. Add a regression fixture with padded columns and at least one escaped pipe. Prove the same documents pass `state.validate`, `source.lookup`, and `source.snapshot_active` and that snapshot reads the expected active artifact.
5. Run the read-only `source.snapshot_active` façade call against the current development binding. Require `ok:true` before continuing to T1; do not mutate or repair the bound instance.

**Done**: the reported valid padded MANIFEST no longer produces `canonical table header is missing`, and `_rows` has no independent cell-splitting convention.

- [x] T1. Add the two batch seams and worker schema
  completed 2026-07-31-0946 UTC

1. Update `.agents/ARCHITECTURE.md` with only durable invariants: bounded inventory, workers own semantic drafting only, façade preparation owns deterministic mechanics, serial per-source effects, and no persistent batch state. Put exact request/result fields in `markdown-registry-contracts.md`, not in architecture.
2. Add `source-worker-result.schema.json` and the concise `url.resolve_reference`, `source.inventory`, and `source.prepare` contracts.
3. Implement `url.resolve_reference` in `scripts/atlas_url.py` and expose it through `scripts/atlas_tool.py` only after its handler exists.
4. Implement `source.inventory` in `scripts/atlas_tool.py` using one canonical MANIFEST parse and existing URL identity functions. It must preserve input order, return one winner for duplicate canonical URLs, reject source-ID collisions, and perform no artifact read or write.
5. Implement `source.prepare` as a shallow façade handler backed by cohesive helpers in `scripts/atlas_source.py`. Compose existing validators/reducers/renderers rather than copying their rules. Prepare one source against current state and return existing transaction arguments unchanged.
6. Add focused tests for new/active-due/active-not-due/archived/duplicate inputs, unrelated sibling revision changes, malformed packets, one quality revision, no-write, and transaction-ready output. Assert no operation writes.

**Done**: three new operations are callable, no old public operation changes shape, and deterministic source preparation is no longer agent-authored.

- [x] T2. Cut over the two owner workflows
  completed 2026-07-31-0946 UTC

1. Update `atlas-source` to the bounded flow above. Keep its existing evidence and quality guidance; replace repeated normalization/snapshot/reducer/render/merge mechanics with inventory, worker packets, and just-in-time preparation.
2. Update `atlas-acquire` to call `atlas-source` once for its selected list and retain the existing run-log format and write path.
3. Update `.agents/skills/atlas-core/SKILL.md` and `.agents/AGENTS.md` only after all three operations are callable. Command stubs remain unchanged.
4. Delete obsolete source-skill instructions that tell the coordinator to reproduce deterministic preparation. Do not leave aliases, alternative batch flows, scratch-file fallbacks, or compatibility branches.
5. Preserve current route and transaction recovery behavior. If execution exposes a real missing primitive, stop and amend this plan rather than widening implementation into route/effect/recovery redesign.

**Done**: one bounded multi-URL invocation performs at most two inventory calls (the second only after approved expansion), one worker per unique actionable source, one preparation per final packet plus at most one quality retry, and existing serial transactions without coordinator-authored reducer/render/target data.

- [x] T3. Verify once and hand off
  completed 2026-07-31-0946 UTC

1. Run the parser and façade tests that directly cover T0/T1.
2. Run one disposable local-profile actual-owner smoke with a small fixed set: existing active, new, duplicate alias, and one no-write source. Check one inventory, no duplicate worker, serial transaction behavior, route delegation only for committed route-required sources, and no scratch artifact.
3. Run the Atlas test suite once after the smoke passes:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --group test python -m unittest discover -s tests -p 'test_atlas_*.py'
python3 scripts/atlas-instance.py check --name atlas
```

4. Remove temporary profile/server/session data. Confirm no fixture source, transaction, or run-log row remains on a bound instance.
5. Append one completion summary with changed files, observed call counts, targeted/full command results, the development `source.snapshot_active` proof, and any real residual risk. Mark each task complete with a UTC timestamp, set status to `DONE`, and archive only if repository plan-storage rules require it.

Do not add another reviewer loop, persistent evaluator, fixture corpus, benchmark harness, or repeated full-suite pass.

## Files

Expected changes only:

- `.agents/ARCHITECTURE.md`
- `.agents/AGENTS.md`
- `.agents/skills/atlas-core/SKILL.md`
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md`
- `.agents/skills/atlas-core/assets/source-worker-result.schema.json` (new)
- `.agents/skills/atlas-source/SKILL.md`
- `.agents/skills/atlas-acquire/SKILL.md`
- `scripts/atlas_state.py`
- `scripts/atlas_url.py`
- `scripts/atlas_source.py`
- `scripts/atlas_tool.py`
- `tests/test_atlas_state.py`
- `tests/test_atlas_url.py`
- `tests/test_atlas_source.py`
- `tests/test_atlas_tool.py`
- `tests/test_atlas_harness_surface.py`

No planned change to `atlas-route`, transaction/effect modules, connector/profile code, acquisition-run schema/templates, command stubs, scaffold, or bound-instance data.

## Completion criteria

- [x] `source.snapshot_active` accepts the same padded/escaped canonical tables as `state.validate` and succeeds against the current development instance.
- [x] Multi-URL presence uses one MANIFEST inventory read; single-URL presence still uses `source.lookup`.
- [x] Multi-source ingestion dispatches no duplicate/archived/not-due worker and uses no scratch packet files.
- [x] Workers return only semantic packets; source IDs, state events, rendering, targets, revisions, and transaction behavior remain façade-owned.
- [x] Preparation is just-in-time per source, so earlier sibling commits do not stale later prepared transactions.
- [x] Existing transaction recovery and route ownership remain unchanged.
- [x] `atlas-acquire` delegates one bounded batch and writes its existing run log once.
- [x] Focused tests, one disposable actual-owner smoke, the Atlas suite, and instance check pass once; temporary state is removed.

## Decisions

- Fix the shared parser first because it is the current hard blocker and the same duplicate `_rows` parser affects snapshot, route guards, and effect preflight.
- Add three façade operations and one worker schema only. This captures the high-value deterministic seams without redesigning routing, transactions, effects, connector locking, or acquisition recovery.
- Use rerun plus existing transaction idempotence as recovery for a stopped batch. Persistent resumable batch state is not justified by the observed workload.
- Prefer per-source isolation and bounded parallel drafting over a whole-set atomic batch. Atlas already persists one source and one route transaction at a time; preserving that model is faster to implement and easier to recover.

## Completion Summary

Completed 2026-07-31-0946 UTC.

- Changed `scripts/atlas_state.py`, `scripts/atlas_url.py`, `scripts/atlas_source.py`, and `scripts/atlas_tool.py`; added shared padded/escaped table parsing, `url.resolve_reference`, read-only `source.inventory`, and just-in-time `source.prepare`.
- Changed `.agents/ARCHITECTURE.md`, `atlas-core` contracts/schema, `atlas-source`, `atlas-acquire`, and façade guidance. Command stubs, route/effect/recovery modules, connector/profile code, scaffold, and acquisition-run shape remain unchanged.
- Changed `tests/test_atlas_url.py`, `tests/test_atlas_tool.py`, and `tests/test_atlas_harness_surface.py`. Focused runs passed: state 23, URL 16, source 18, façade 27, harness 9 tests. Full Atlas suite passed: 157 tests.
- Development `source.snapshot_active` returned `ok:true`, `active_count:612`, and MANIFEST revision `sha256:613de51a7c9862648623067dd55134a95b441e79d37f716e86a8a318fb40ccac`.
- Disposable actual-owner smoke observed one inventory, dispositions `active-not-due,new,duplicate,new`, two unique worker assignments, one applied source transaction, one route-eligible committed source, one no-write terminal, and no scratch artifact. Its temporary profile root was removed; development lookup for the synthetic new URL returned `row:null`.
- `python3 scripts/atlas-instance.py sync-framework --name atlas` synchronized the changed product-owned architecture snapshot. `python3 scripts/atlas-instance.py check --name atlas` then passed.
- The documented `uv run --group test` form is unavailable because this repository has no `test` dependency group; the equivalent direct `python3 -m unittest discover -s tests -p 'test_atlas_*.py'` suite passed.
- Residual risk: the disposable smoke verified route eligibility after an applied source receipt but did not execute a model/harness `atlas-route` invocation; existing route transaction/recovery tests and the preserved route owner cover that seam.
