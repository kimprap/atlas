# Strict Task Schema Transport Repair

**Datetime**: 2026-08-04-1949
**Scope**: OMP v17.2.7 Task output-schema normalization/preflight, exact Atlas workflow-result regression, and the existing agent-memory blocker handoff
**Summary**: Repair the harness layer that corrupts the standards-valid Atlas schema before strict Task preflight, prove the complete workflow-result contract passes and remains enforced within OMP’s existing schema subset, and record the verified activation boundary without performing Atlas I/O or installing the patched harness.
**Status**: DONE

## Context

The checked-in Atlas workflow-result schema at `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json` is valid Draft 2020-12 under Ajv 8.20.0, but OMP v17.2.7 rejects it before creating a Task handle. The defect is outside `/Users/kim/dev/atlas/app`: `jtdToJsonSchema` recursively applies JTD detection to native JSON Schema container maps, so the `$defs` member named `ref` becomes `{"$ref":"#/$defs/[object Object]"}` and native `properties` applicators without `type` are silently rewritten before `isValidJsonSchema` runs. The intended end state is a source-level OMP repair that preserves pure JTD and shape-valid unambiguous mixed-JTD support, preserves the complete Atlas schema plus native nodes in OMP’s existing supported subset by identity when no conversion is needed, and has complete-schema strict-preflight, semantic-validation, smoke, verification, review, and curation evidence.

### Route binding

Goal: Diagnose and repair strict Task rejection of the complete Atlas workflow-result schema without weakening its contract.
Route: `dev-diagnosing-bugs → dev-implementation → dev-ask completion presentation`
Why: Expected behavior is settled by the Atlas strict-transport contracts; the exact failure, minimal trigger, standards-valid control, and owning OMP v17.2.7 code path are reproducible. Requirements/specification/ticketing are unnecessary for this cohesive fix, but the newly established external shared-harness surface raises assurance from standard to high-consequence.
Artifacts: bounded diagnosis/fix contract; patched OMP source checkout; exact public 17.2.7 checkout-local native test prerequisite; exact workflow-result schema fixture; normalizer, validator, and strict-preflight regressions; direct smoke; independent verification/review/curation evidence; updated Atlas blocker handoff
Gates: this plan’s approval authorizes public credential-free npm artifact acquisition plus writes only in the named external OMP checkout and the named existing Atlas handoff artifacts; no Atlas/profile/vault/façade/owner/reducer/transaction I/O; no installed-binary replacement, staging, commit, push, deploy, release, or agent-memory activation; a separately authorized harness activation/restart and fresh `/atlas-ask` route approval remain required
Execution: one owner; assurance: high-consequence
First action: bind a clean OMP v17.2.7 source checkout and rerun the exact, minimized, and control preflight probes before editing.

## Tasks

- [x] T1. Bind external source and re-establish diagnosis
  - completed 2026-08-04-2132
- [x] T2. Add complete strict-preflight regressions and prove red
  - completed 2026-08-04-2144
  - user override: authorized the pinned `gen:tool-views` prerequisite after the tag checkout lacked its ignored generated asset; generated SHA-256 `abf8a665d3ae62ecc74b7bc6da4a7f4706cfbb2b52a4344a53a995d10b9127ef`
- [x] T3. Preserve native JSON Schema and prove green
  - completed 2026-08-04-2147
- [x] T4. Smoke repaired transport and freeze target
  - completed 2026-08-04-2207
  - user override: expanded the target to repair user-config leakage in the Windows virtualenv LSP regression and authorized a fresh package run; the revised run had 11,712 passes, 404 skips, and only the separately isolated passing collab tombstone timeout accepted as a confirmed full-suite flake
- [x] T5. Complete high-consequence independent assurance
  - completed 2026-08-04-2233
- [x] T6. Record repair evidence and gate Atlas resume
  - completed 2026-08-04-2237

## Approach

### T1. Bind external source and re-establish diagnosis

1. From `/Users/kim/dev/atlas/app`, verify the governing identities before any external write:
   - `omp --version` must print `omp/17.2.7`.
   - `sha256sum .agents/skills/atlas-core/assets/atlas-workflow-result.schema.json` must print `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`.
   - Re-read `.agents/ARCHITECTURE.md` dispatch/result invariants, `.agents/skills/atlas-ask/SKILL.md` `## Strict Workflow Owner Task`, and `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md` `## Capability and strict Task transport`. Drift in any behavior or schema identity returns to `dev-ask`; do not adapt the fix silently.
2. Clone the public source without touching the installed binary:
   - Target: `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949`.
   - Command: `git clone --branch v17.2.7 --single-branch https://github.com/can1357/oh-my-pi.git /Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949`.
   - `git -C /Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949 rev-parse HEAD` must print tag commit `a5090f1f81cf0ac072fbd1ec949eebe6bbbc23a9`; `packages/coding-agent/package.json` version and the root workspace catalog entry for `@oh-my-pi/pi-coding-agent` must both be `17.2.7`. Then run `bun install --frozen-lockfile --ignore-scripts` in that checkout. Do not run setup/generators, link, install, or replace `~/.local/bin/omp`; a missing generated prerequisite is a blocker to report, not permission to widen the target.
   - Provision only the checkout-local macOS arm64 test prerequisite. Require `packages/natives/native/pi_natives.darwin-arm64.node` to be absent, create `.native-artifact/npm-cache/` inside the checkout, and scrub `NPM_TOKEN`, `NODE_AUTH_TOKEN`, and `YARN_NPM_AUTH_TOKEN`; use `npm_config_userconfig=/dev/null`, `npm_config_cache=.native-artifact/npm-cache`, and the public `https://registry.npmjs.org` only so npm writes no user cache/config. First query `npm view @oh-my-pi/pi-natives-darwin-arm64@17.2.7 version dist.integrity dist.shasum dist.tarball --json`, then run the identically scrubbed `npm pack --ignore-scripts --registry=https://registry.npmjs.org --pack-destination .native-artifact @oh-my-pi/pi-natives-darwin-arm64@17.2.7`. Require archive name `oh-my-pi-pi-natives-darwin-arm64-17.2.7.tgz`, SHA-1 `1f8de55f4d1760e5e91b85460d63d34dd1074906`, package version `17.2.7`, and registry integrity `sha512-eIvz6ZzHEnUyBPRfoLdXOf/VhvbUgcCp5V5YCeqVz+sEQ+AJjOyDl9ayjTIHR/2spnEJ6zgl4F7Xr/c/sMhWJQ==`; extract only `package/pi_natives.darwin-arm64.node` into `packages/natives/native/` with its basename, then record its SHA-256. Do not run package lifecycle scripts, Bazel, setup, link, or any global install. Keep the addon through independent verification; `.native-artifact/` is disposable staging and must be removed only after the final test/review target no longer needs it.
3. Re-run each failing red-capable probe twice to confirm a deterministic verdict, without Atlas I/O:
   - Strict Task with the exact parsed Atlas schema and `schemaMode:"strict"` must fail before dispatch with `Invalid strict caller output schema: invalid JSON schema` and no handle.
   - Strict Task with `{"$defs":{"ref":{}}}` must fail identically.
   - Strict Task with `{"$defs":{"reference":{}}}` and a no-tool worker returning `{}` must dispatch and complete with `{}`.
   - A disposable full-schema control that only renames internal `$defs.ref`, updates its local references, and adds redundant `type:"object"` to native applicators with `properties` must pass strict preflight and return the exact valid `no-write` object from T2. This proves the remaining complete keyword set is accepted, but it is diagnostic only and must never replace the canonical schema.
   - Run the exact standards-control fresh JS Eval cell in `### Exact direct probes`; Ajv 8.20.0 Draft 2020-12 `validateSchema` and `compile` must both succeed and print `draft-2020-12-schema OK`. Use only the already installed Ajv tree named there; do not install a validator into the Atlas repository.
4. Preserve the ranked falsifiable diagnosis record:
   - H1 — mixed JTD normalization corrupts a native schema container. Prediction: the minimal `$defs.ref` shape fails while the identical renamed-key control passes; source emulation exposes the malformed `$defs`. Observed: confirmed.
   - H2 — the canonical schema is invalid Draft 2020-12. Prediction: an independent 2020-12 meta-schema check or compilation fails. Observed: Ajv accepts and compiles it; falsified.
   - H3 — an unsupported known JSON Schema keyword is rejected directly by the hand-rolled meta-validator. Prediction: the disposable full-schema control still fails after removing both JTD ambiguity triggers. Observed: that control passes strict preflight and enforces the valid `no-write` object; falsified.
   - H4 — a later Task/provider adapter rejects an otherwise accepted local schema. Prediction: preflight succeeds and a handle/provider request exists. Observed: `results: []`, zero-duration preflight, and no handle; falsified.
5. Bind the diagnosis before implementation: `packages/coding-agent/src/tools/jtd-to-json-schema.ts::normalizeMixedSchemaNode` treats schema containers as schema nodes. At `$defs`, the definition key `ref` activates `isJTDSchema`; `convertSchema` emits a `$ref` whose value is the stringified definition object; `isValidJsonSchema` then rejects that malformed `$defs` map. The same generic recursion rewrites valid `oneOf`/`anyOf` branches containing `properties` without `type`, so renaming one Atlas definition would only hide the first symptom and would not preserve enforcement.

### T2. Add complete strict-preflight regressions and prove red

1. Copy `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json` byte-for-byte into the OMP checkout at `packages/coding-agent/test/fixtures/atlas-workflow-result.schema.json`. Before copying, require the source SHA-256 from T1; the fixture is a regression snapshot, not a new authority.
2. In `packages/coding-agent/test/tools/jtd-to-json-schema.test.ts`, use the exact native input `{"$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"required":["kind","target"],"properties":{"kind":{"const":"a"},"target":{"$ref":"#/$defs/ref"}}}],"$defs":{"ref":{"type":"object","properties":{"uri":{"type":"string"}}}}}`; clone an immutable expected snapshot before the call, then assert `jtdToJsonSchema(input)` is the same object and deep-equals that pre-call snapshot. This must fail on unmodified v17.2.7 and catch the malformed `$defs` map, erased branch, and in-place mutation.
3. In the same test file, add table-driven positional controls using the exact keyword sets from T3:
   - For every single-schema keyword, place `{elements:{type:"string"}}` at that position and require conversion to `{type:"array",items:{type:"string"}}`.
   - For every schema-array keyword, place that same nested JTD form as its sole element and require the same element conversion.
   - For every schema-map keyword, use `{ref:{const:"kept"},nested:{elements:{type:"string"}}}`; require the member named `ref` and its `const` to survive while only `nested` converts, with copy-on-write cloning limited to the changed path.
   - Put `{"elements":{"type":"string"}}` inside `enum`, `examples`, and `default`; use `required:["elements"]`, `dependentRequired:{"x":["elements"]}`, and `$vocabulary:{"https://example.test/elements":true}`; require complete identity preservation. Under an explicitly native root, malformed `items:[]`, `properties:[]`, and `oneOf:{}` plus deprecated `dependencies` must also remain untouched for the existing meta-validator to reject.
4. In `packages/coding-agent/test/tools/output-schema-validator.test.ts`, import `atlasWorkflowResultSchema` from `../fixtures/atlas-workflow-result.schema.json` with `{ type: "json" }` and assert:
   - Clone an expected snapshot before the call. `buildOutputValidator(atlasWorkflowResultSchema)` has no `error`, returns a validator, returns the identical imported object as `jsonSchema`, and leaves both it and the imported fixture deeply equal to the pre-call snapshot.
   - This exact valid `no-write` result succeeds:

     ```json
     {
       "version": 1,
       "dispatch": {
         "dispatch_id": "dispatch-1",
         "owner": "atlas-audit",
         "atlas_attempt": 1,
         "owner_turn": 1,
         "architecture_revision": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
         "guardrail_revision": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
         "result_schema_revision": "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
         "owner_revision": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
       },
       "outcome": "no-write",
       "summary": "No writes required.",
       "items": [{"id": "audit-1", "status": "no-write", "summary": "No defects found."}],
       "aggregate_effect": "none",
       "resume": null,
       "guidance": null,
       "blocker": null,
       "defects": [],
       "learning_candidate": null
     }
     ```
   - Mutating only `aggregate_effect` to `"committed"` fails, and mutating only the item status to `"completed"` fails. These probes defend discriminated tuple enforcement after preflight acceptance.
5. In `packages/coding-agent/test/task/structured-subagent.test.ts`, import the same `atlasWorkflowResultSchema` from `../fixtures/atlas-workflow-result.schema.json` with `{ type: "json" }` and add a strict caller-schema case around `runStructuredSubagent`: mock discovery and executor as existing neighboring tests do, pass `outputSchema: atlasWorkflowResultSchema` plus `schemaMode:"strict"`, assert executor dispatch occurs exactly once and receives that exact object, then remove the temporary artifact directory. Unmodified v17.2.7 must fail before the executor call.
6. Run the exact three new test files on unmodified production source and require failures attributable to the new contract assertions before any normalizer edit. Record the failing test names/messages; a compile, fixture, native-addon, or unrelated infrastructure failure is not valid red evidence and must be corrected without touching production code. Existing JTD tests must remain green; no test may rely on Atlas I/O, model/provider output, network state, or the installed OMP binary.

### T3. Preserve native JSON Schema and prove green

1. Before editing, run LSP references for exported `jtdToJsonSchema` and `isJTDSchema` in the local checkout and bind every discovered caller. Change only `packages/coding-agent/src/tools/jtd-to-json-schema.ts`; keep both exported signatures stable, so no caller migration or compatibility alias is permitted.
2. Replace generic recursive `normalizeMixedSchemaNode` with a context-aware native-JSON-Schema walker:
   - At `jtdToJsonSchema` root, retain current pure-JTD detection and call `convertSchema` once; `convertSchema` remains the recursive owner for that JTD tree.
   - Otherwise walk a native JSON Schema node. Convert only shape-valid unambiguous nested JTD forms: `elements` or `values` whose value is a non-array object; `optionalProperties` whose value is a non-array object; `discriminator` satisfying existing `isJTDDiscriminator`; `ref` whose value is a string; or a JTD-only primitive `type` value (`timestamp`, `float32`, `float64`, `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`). A nested node whose only JTD signal is `properties` without `type` remains native JSON Schema because that shape is valid and ambiguous under Draft 2020-12.
   - Recurse as schema nodes only through single-schema keywords `not`, `if`, `then`, `else`, `items`, `contains`, `propertyNames`, `additionalProperties`, `unevaluatedProperties`, `unevaluatedItems`, and `contentSchema`.
   - Recurse element-by-element through schema-array keywords `allOf`, `anyOf`, `oneOf`, and `prefixItems`.
   - Recurse value-by-value, never over the map object itself, through schema-map keywords `properties`, `patternProperties`, `$defs`, `definitions`, and `dependentSchemas`.
   - Preserve all annotation, assertion, reference, unknown-keyword, and data-valued members verbatim; preserve malformed known keyword values so the existing meta-validator rejects them rather than the normalizer repairing or hiding them.
   - At any recognized schema position, preserve boolean schemas by identity. Preserve non-object/non-boolean values and malformed array/object containers unchanged so `isValidJsonSchema` remains the sole rejection authority.
   - Leave deprecated `dependencies`, obsolete `additionalItems`, and array-valued `items` untouched; the existing OMP meta-validator intentionally rejects them. Walking `contentSchema` and `unevaluated*` preserves schema structure only and does not expand the current value-validator semantics. This repair guarantees the exact Atlas contract and OMP’s existing supported subset, not universal Draft 2020-12 or arbitrary extension-keyword semantics.
3. Make the walker copy-on-write: return the original schema/map/array object when no nested JTD conversion occurs, and clone only the changed node plus its ancestor path when a conversion occurs. The complete native Atlas schema must therefore return by object identity with zero deep-copy allocation; pure or nested JTD conversion may allocate its required projection.
4. Use private helpers `isUnambiguousJTDSchema(schema: unknown): boolean`, `normalizeJsonSchemaNode(schema: unknown): unknown`, `normalizeJsonSchemaArray(value: unknown): unknown`, and `normalizeJsonSchemaMap(value: unknown): unknown`. Delete `normalizeMixedSchemaNode`; leave no alias or compatibility path.
5. Preserve existing pure-JTD conversion and the current unambiguous nested-JTD-in-JSON-Schema test. Do not change `output-schema-validator.ts`, `meta-validator.ts`, the Atlas schema, or any Atlas contract: those are consumers/evidence, not the defect owner.
6. Run the same three focused test files from T2 after the production edit and require all new and existing cases green. Record the exact commands and test counts before entering smoke.

### T4. Smoke repaired transport and freeze target

1. From the OMP checkout, run `bun --cwd=packages/coding-agent run check:types`.
2. Run the exact repaired-source fresh JS Eval cell in `### Exact direct probes`; it imports `buildOutputValidator` from the patched source, reads the live Atlas schema by absolute path, and must print `strict-schema-transport OK` only after every assertion below passes:
   - no build error and a validator exists;
   - returned `jsonSchema` is the same parsed object and deep-equals the input;
   - the exact valid `no-write` object from T2 succeeds;
   - the `aggregate_effect:"committed"` and item-status `"completed"` mutations both fail.
   This is the no-model, no-Atlas-I/O smoke of the changed transport seam; it is not a substitute for the strict Task preflight regression.
3. After the direct smoke succeeds, record a pre-suite SHA-256 manifest for the changed normalizer, three test files, complete fixture, and checkout-local native addon. The main orchestration owner—not a delegated worker—then runs `bun --cwd=packages/coding-agent test` exactly once as the package-wide regression check, captures the raw command/result, and records an identical post-suite manifest.
4. Freeze the target only if the pre/post manifests are identical; bind the tag commit plus those digests as the immutable target. Do not create a commit, patch-install the live binary, run `setup`, or link the checkout.

### T5. Complete high-consequence independent assurance

1. Dispatch a fresh non-implementer verifier with the immutable digests, exact high-consequence criteria, and no worker reasoning. It must independently re-run the focused tests, typecheck, direct source smoke, pure-JTD control, minimal `$defs.ref` case, and the patched-source `structured-subagent` complete strict-preflight regression; target digests must match before and after. For the package-wide criterion, it independently inspects the raw orchestrator command/result plus identical pre/post suite manifests rather than rerunning the project-wide suite. It must not expect the still-running installed OMP process to use unactivated source. Any missing proof is `INCONCLUSIVE`; any contradiction is `NOT VERIFIED`; neither role repairs.
2. Dispatch a distinct fresh reviewer after `VERIFIED`. Review the exact verified target for complete-Atlas and supported native JSON Schema preservation, pure/unambiguous-mixed JTD compatibility, malformed supported-native-schema fail-closed behavior, public API stability, allocation/copy behavior, test fidelity, and scope discipline. High-consequence attempts use decorrelated role profiles or model families when available and disclose any same-model residual.
3. Run the required terminal `dev-continual-learning` assessment after review with no guidance writes authorized in this route. `NO DURABLE LEARNING` satisfies the gate and names the exact sources assessed. A qualified candidate or any need to curate must return `BLOCKED` with suggested destination/evidence to `dev-ask`; do not write guidance, modify user-level policy, or activate the provisional agent-memory design.
4. Completion requires verifier `VERIFIED`, reviewer `APPROVED`, curation `NO DURABLE LEARNING`, exact criterion accounting, and no stale target, unresolved finding, blocker, or installed/live-harness claim.
5. `NOT VERIFIED` or `CHANGES REQUIRED` returns to a new bounded implementation attempt under this unchanged fix contract, followed by fresh smoke, target digests, verification, and review. `INCONCLUSIVE`, curation `BLOCKED`, broader mixed-dialect compatibility, a changed canonical schema, or an architecture/interface expansion blocks and returns to `dev-ask`; no assurance role chooses or applies a workaround.
6. After all terminal assurance conditions are satisfied, remove only the checkout’s `.native-artifact/` tarball staging directory. Retain the copied checkout-local addon and its recorded digest so the verified test environment remains reproducible; do not remove or modify any source/test target after verification.

### T6. Record repair evidence and gate Atlas resume

1. Reconcile parent authority before any handoff write. Verify `.agents/plans/2026-08-02-1456_repo-agent-memory-first-draft.md` still has SHA-256 `d548bfb3359f461c8c2e060912d427285975b99e80c02658ec89a4512428f598`. At plan authoring time, `local://repo-agent-memory-first-draft-plan.md` is absent: if it remains absent, restore it byte-for-byte from that projection using `read` plus `write`; if it exists, require byte equality with the projection. Any digest or byte mismatch stops for authority reconciliation; do not choose a newer-looking plan or overwrite either artifact.
2. In the reconciled local authority, preserve `## Attempt 2 Capability Blocker Handoff` as historical evidence and append a new dated `## Strict Task Source Repair Evidence` section with the source/tag identity, copied-native provenance and digest, changed-target digests, focused/package smoke, verifier/reviewer/curation verdicts, no-effect statement, and activation boundary. Keep `Status: IN_PROGRESS` and T3/T4 unchecked. State the remaining resume condition exactly: activate a verified harness build under separate authority, start a fresh OMP session, revalidate current Atlas product revisions, and obtain a new `/atlas-ask` audit route approval.
3. Immediately before synchronization, re-require the repository projection’s original SHA-256 `d548bfb3359f461c8c2e060912d427285975b99e80c02658ec89a4512428f598`; drift stops before any repository handoff edit. Then run `/Users/kim/.dotfiles/bin/omp-copy-plan-artifact sync --slug repo-agent-memory-first-draft --content-file local://repo-agent-memory-first-draft-plan.md`, require byte equality between local authority and `.agents/plans/2026-08-02-1456_repo-agent-memory-first-draft.md`, and record their common post-sync SHA-256. Never hand-edit that projection.
4. Immediately before memory-handoff edits, re-require the local authority and repository projection to remain byte-identical at the recorded post-sync digest. Then preserve `.agents/memory/FIRST_DRAFT.md` Attempt 2/row 6 byte-for-byte and do not create row 7. Immediately before `## Deferred first ingestion`, append a dated `### Strict Task source-repair evidence` note containing the owning OMP tag/commit, copied-native provenance/digest, changed-target digests, focused/package smoke, verifier/reviewer/curation verdicts, and this literal boundary: `Source-level strict-transport repair is verified in the external v17.2.7 checkout; the patched harness is not activated, no fresh /atlas-ask route has been approved or dispatched, and no Atlas I/O occurred. T3 and T4 remain unchecked and Status remains IN_PROGRESS.` In `.agents/memory/INDEX.md` `## Research comparison input`, retain `Blocked` and replace only its explanatory text with: `Blocked — OMP v17.2.7 strict-transport repair is verified only in the external checkout; the patched harness is not activated and no fresh /atlas-ask route is approved or dispatched. The comparison remains pending until the complete checked-in workflow-result contract is accepted by the activated strict transport and a fresh approved route produces a validated aggregate result.` Do not change `Active memory map`, add topic/pass links, activate loading, promote memory, or touch `tmp/`.
5. Complete this repair plan’s own lifecycle only after T1–T5, T6 steps 1–4, and every done criterion are satisfied: check its task boxes, set `Status: DONE`, append a concise `## Completion Summary` with exact evidence and residual activation boundary, then call `archive_plan_artifact` with slug `strict-task-schema-transport-repair`. Do not archive a blocked, inconclusive, stale, or partially evidenced plan.
6. Stop before harness installation/replacement or any Atlas/profile/vault/façade/owner/reducer/transaction/topic/source/run/pass/relation/registry operation. Return the engineering completion presentation plus the exact activation and fresh-approval boundary; do not resume T3/T4 in this route.

## Critical files & anchors

- `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent/src/tools/jtd-to-json-schema.ts` — `isJTDSchema`, `convertSchema`, `normalizeMixedSchemaNode`, and `jtdToJsonSchema`; canonical defect owner.
- `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent/test/tools/jtd-to-json-schema.test.ts` — red/green native-position, JTD compatibility, identity, and copy-on-write regression owner.
- `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent/test/tools/output-schema-validator.test.ts` — semantic contract-preservation seam after normalization.
- `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent/test/task/structured-subagent.test.ts` — actual strict caller preflight-before-dispatch seam.
- `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/natives/native/pi_natives.darwin-arm64.node` — exact checkout-local 17.2.7 package-suite prerequisite; never an installed harness replacement or source target.
- `.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json` — complete canonical regression input, bound to SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`.
- `.agents/plans/2026-08-02-1456_repo-agent-memory-first-draft.md` — current byte-verified restoration source for the absent session-local parent authority; after restoration, only `local://repo-agent-memory-first-draft-plan.md` may be edited and the projection is adapter-owned.

## Verification / Done criteria

- [x] Exact current schema reproduces `Invalid strict caller output schema: invalid JSON schema` before the fix, with no Task handle or Atlas effect.
- [x] Minimal `{"$defs":{"ref":{}}}` reproduces the rejection; renamed-key control dispatches and returns `{}`.
- [x] Disposable full-schema control passes strict preflight and returns the exact valid `no-write` object, proving no other checked-in construct is the first rejection.
- [x] Ajv 8.20.0 accepts and compiles the exact canonical schema as Draft 2020-12.
- [x] Canonical Atlas schema and copied OMP regression fixture both have SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`.
- [x] Exact public `@oh-my-pi/pi-natives-darwin-arm64@17.2.7` artifact matches the bound registry integrity/SHA-1, and the copied checkout-local addon SHA-256 is recorded.
- [x] All three new regression files fail for their intended assertions on unmodified source before the normalizer edit, then pass after it.
- [x] `bun test packages/coding-agent/test/tools/jtd-to-json-schema.test.ts` passes in the external OMP checkout.
- [x] `bun test packages/coding-agent/test/tools/output-schema-validator.test.ts` passes and proves valid/invalid workflow-result behavior.
- [x] `bun test packages/coding-agent/test/task/structured-subagent.test.ts` passes and proves the complete schema crosses strict preflight to executor dispatch.
- [x] `bun --cwd=packages/coding-agent run check:types` passes.
- [x] Main orchestration ran the user-authorized revised `bun --cwd=packages/coding-agent test` after smoke: `11,712` passed, `404` skipped, and only the explicitly accepted collab tombstone full-suite timeout remained; its exact isolated case passed.
- [x] Direct `buildOutputValidator` smoke prints `strict-schema-transport OK` for the live canonical schema and rejects both discriminated-tuple mutations.
- [x] Fresh verifier reports `VERIFIED` against unchanged pre/post target digests; distinct reviewer reports `APPROVED`; write-free terminal curation reports `NO DURABLE LEARNING`.
- [x] Parent-plan authority/projection are reconciled and byte-identical before memory-handoff edits; T3/T4 remain unchecked and no Atlas or harness-activation effect occurred.
- [x] `.native-artifact/` staging is removed only after assurance; the digest-bound checkout-local addon remains and no verified source/test target changes afterward.
- [x] This repair plan is `DONE`, has its completion summary, and is archived under slug `strict-task-schema-transport-repair`; the parent agent-memory plan remains `IN_PROGRESS`.

### Exact direct probes

Run the standards control as a fresh JS Eval cell (`reset:true`):

```js
const { createRequire } = await import("node:module");
const ajvRoot =
  "/Users/kim/.local/share/nvim/mason/packages/yaml-language-server/node_modules/yaml-language-server/node_modules/ajv";
const requireAjv = createRequire(`${ajvRoot}/package.json`);
const Ajv2020 = requireAjv(`${ajvRoot}/dist/2020.js`).default;
const schema = JSON.parse(
  await Bun.file(
    "/Users/kim/dev/atlas/app/.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json",
  ).text(),
);
const ajv = new Ajv2020({ strict: false, allErrors: true });
if (!ajv.validateSchema(schema)) throw new Error(JSON.stringify(ajv.errors));
ajv.compile(schema);
console.log("draft-2020-12-schema OK");
```

Run the repaired-source smoke as a separate fresh JS Eval cell (`reset:true`):

```js
const { buildOutputValidator } = await import(
  "/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949/packages/coding-agent/src/tools/output-schema-validator.ts"
);
const schema = JSON.parse(
  await Bun.file(
    "/Users/kim/dev/atlas/app/.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json",
  ).text(),
);
const before = JSON.stringify(schema);
const built = buildOutputValidator(schema);
if (built.error || !built.validator) throw new Error(built.error ?? "validator unavailable");
if (
  built.jsonSchema !== schema ||
  JSON.stringify(schema) !== before ||
  JSON.stringify(built.jsonSchema) !== before
) {
  throw new Error("native JSON Schema was copied or changed in place");
}
const valid = {
  version: 1,
  dispatch: {
    dispatch_id: "dispatch-1",
    owner: "atlas-audit",
    atlas_attempt: 1,
    owner_turn: 1,
    architecture_revision: `sha256:${"a".repeat(64)}`,
    guardrail_revision: `sha256:${"b".repeat(64)}`,
    result_schema_revision: `sha256:${"c".repeat(64)}`,
    owner_revision: `sha256:${"d".repeat(64)}`,
  },
  outcome: "no-write",
  summary: "No writes required.",
  items: [{ id: "audit-1", status: "no-write", summary: "No defects found." }],
  aggregate_effect: "none",
  resume: null,
  guidance: null,
  blocker: null,
  defects: [],
  learning_candidate: null,
};
if (!built.validator.validate(valid).success) throw new Error("valid workflow result rejected");
if (built.validator.validate({ ...valid, aggregate_effect: "committed" }).success) {
  throw new Error("invalid no-write effect accepted");
}
if (
  built.validator.validate({
    ...valid,
    items: [{ id: "audit-1", status: "completed", summary: "No defects found." }],
  }).success
) {
  throw new Error("invalid no-write item accepted");
}
console.log("strict-schema-transport OK");
```

## Assumptions & contingencies

- Approval of this plan is the required revised-scope authority for source writes outside `/Users/kim/dev/atlas/app`, limited to `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949`. If that path already exists, do not overwrite it: use `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949-2` only after proving the first path was not created by this plan, and bind the substituted absolute path in every task/evidence record.
- The repair targets installed behavior `omp/17.2.7`, so source begins at immutable tag `v17.2.7`, commit `a5090f1f81cf0ac072fbd1ec949eebe6bbbc23a9`; it does not opportunistically rebase onto newer upstream code. If the tag no longer matches that commit, the observed normalizer, or package version, stop before edits and return to `dev-ask`.
- The package-wide suite depends on the exact public macOS arm64 native leaf bound in T1. If npm metadata, archive name, version, integrity, SHA-1, extracted package shape, or host platform/architecture differs, stop before tests; do not build an unreviewed addon, use the cached 17.2.1 binary, or weaken the suite.
- Native JSON Schema preservation wins at ambiguous nested `properties`-without-`type` nodes. Pure root JTD remains supported, and shape-valid unambiguous nested JTD remains supported. A root `properties`-only document and a native extension keyword whose shape exactly matches JTD remain inherently ambiguous under the unchanged API; changing that requires an explicit dialect marker/interface contract and is not authorized here. If existing tests prove a materially broader mixed-format public contract, stop for interface/scope reapproval rather than adding heuristics.
- The guarantee is the complete current Atlas schema plus OMP’s existing validated subset. Deprecated `dependencies`, obsolete tuple keywords, and runtime semantics for `contentSchema`/`unevaluated*` remain under their current validators; do not describe this repair as universal Draft 2020-12 support.
- No Atlas schema rewrite is permitted: renaming `$defs.ref`, adding redundant `type` annotations, flattening references, dropping `contains|minContains|maxContains|oneOf|anyOf`, or using permissive/prose validation would hide or weaken the harness defect.
- A verified source checkout is not an active repair in the current OMP process. No result may claim strict transport is available to `/atlas-ask` until a separately authorized build activation and fresh session prove the same complete-schema preflight; the subsequent Atlas audit also requires fresh product-revision validation and route approval.

## Completion Summary

- Repaired OMP v17.2.7 mixed-schema normalization in the external checkout at commit `a5090f1f81cf0ac072fbd1ec949eebe6bbbc23a9`: native JSON Schema now walks only recognized schema positions, preserves unchanged nodes by identity, converts only pure root or shape-valid unambiguous nested JTD, and leaves malformed supported-native values for fail-closed validation.
- Added the byte-identical Atlas workflow-result fixture plus normalizer, semantic-validator, and strict `runStructuredSubagent` regressions. The immutable source/test/native/generated target is recorded in the parent handoff; canonical schema and fixture SHA-256 are both `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`.
- User-approved execution overrides generated the tag-omitted tool-view prerequisite, isolated user LSP configuration in the Windows pyright/pylsp regression, and accepted the sole full-suite collab tombstone timeout after its exact isolated case passed. Focused results were normalizer `9/9`, validator `14/14`, structured-subagent `19/19`, complete LSP `76/76`, plus passing typecheck and `strict-schema-transport OK`; the revised package run recorded `11,712` passes and `404` skips.
- Independent assurance completed on unchanged digests: `agent://StrictSchemaVerifier` returned `VERIFIED`; distinct `agent://StrictSchemaReviewer` returned Standards `PASS`, Specification `PASS`, Overall `APPROVED`; `agent://StrictSchemaCurator` returned `NO DURABLE LEARNING`. Model-family decorrelation was not exposed and remains an explicit assurance residual.
- Restored and synchronized `local://repo-agent-memory-first-draft-plan.md` with its repository projection at common SHA-256 `e33a4546718160e0f05bc1ef58fcd60d87556249c28b5a2e0e886999ea944e22`; appended source-repair evidence without changing parent T3/T4 or `Status: IN_PROGRESS`; updated only the prescribed inactive memory handoff notes and created no row 7.
- Removed only `.native-artifact/` staging after assurance. The copied checkout-local addon remains at SHA-256 `67de42fe9e7aa9c2c5e3a817f2b9f0c6b87e7252b8e3a3da1d9beb86e076055c`.
- No installed harness, Atlas/profile/vault/façade/owner/reducer/transaction/topic/source/run/pass/relation/registry, commit, stage, push, deploy, or release effect occurred. Remaining boundary: activate a verified harness build under separate authority, start a fresh OMP session, revalidate current Atlas product revisions, and obtain a new `/atlas-ask` audit route approval.
