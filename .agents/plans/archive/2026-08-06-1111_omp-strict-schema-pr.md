# OMP Strict JSON Schema PR

**Datetime**: 2026-08-06-1111
**Scope**: Upstream OMP strict output-schema normalization repair, regression tests, verification, and pull-request delivery
**Summary**: Port the already verified native JSON Schema preservation fix onto current upstream `can1357/oh-my-pi` `main`, reduce the contribution to the smallest behavior-defending production and test diff, and open a standards-compliant pull request after independent assurance and explicit delivery authorization.
**Status**: DONE

## Context

OMP v17.2.9 and upstream `main` commit `1e492d6ff9b8d4412591942b11fe06e1395ae80f` still recursively treat native JSON Schema container maps as JTD schema nodes. Against Atlas workflow-result schema SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`, the normalizer rewrites `$defs.ref` to `{"$ref":"#/$defs/[object Object]"}` and rewrites valid `properties`-without-`type` branches before strict validation. PRs #1363 and #1380 fixed the related re-walk of JSON Schema emitted from a pure JTD root, but no issue or PR found on 2026-08-06 covers this remaining native-root path; OMP explicitly permits a narrow bug fix to go straight to a PR, provided the human contributor reviews every file, personally exercises the fix, supplies a sentence in their own words, and approves publication.

## Tasks

- [x] T1. Bind current upstream target and reproduce the defect
  completed 2026-08-06-1214
- [x] T2. Port the minimal normalizer repair and regression tests
  completed 2026-08-06-1214
- [x] T3. Run focused and repository-required verification
  completed 2026-08-06-1214
- [x] T4. Complete independent verification and code review
  completed 2026-08-06-1316
- [x] T5. Deliver the approved branch and open the upstream PR
  completed 2026-08-07-2340

## Approach

### T1. Bind current upstream target and reproduce the defect

1. Require `/Users/kim/dev/oh-my-pi-strict-schema-pr-2026-08-06` to remain absent, clone `https://github.com/can1357/oh-my-pi.git` there from upstream `main`, and create branch `fix/native-json-schema-containers`. Leave `/Users/kim/dev/oh-my-pi-strict-schema-2026-08-04-1949` unchanged as verified evidence. Record the new checkout's `HEAD`, package version, `bun --version` (planning host: `1.3.14`), clean status, and current upstream `main` identity.
2. Re-read `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `packages/coding-agent/DEVELOPMENT.md`, and the current source/test regions. Require `normalizeMixedSchemaNode`, `jtdToJsonSchema`, `isJTDSchema`, `buildOutputValidator`, and the three existing normalizer tests to retain the planned interfaces. Run LSP references for `jtdToJsonSchema` and `isJTDSchema`; if no TypeScript server is available, search `\b(jtdToJsonSchema|isJTDSchema)\b` under `packages/coding-agent/src` and `packages/coding-agent/test`. At planning time `jtdToJsonSchema` has one production caller, `packages/coding-agent/src/tools/output-schema-validator.ts::buildOutputValidator`, and `isJTDSchema` has no external production caller; no signature or caller edit is planned.
3. Run `bun install --frozen-lockfile` from the clean root and `bun --cwd=packages/natives run build` to install the documented host addon. Never run root `bun run setup`, which would link or replace the installed OMP.
4. Before editing, execute current `jtdToJsonSchema` and `isValidJsonSchema` with:
   - the exact native test schema specified in T2.1; and
   - `/Users/kim/dev/atlas/app/.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json`, requiring SHA-256 `11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad`.
   Require each original input to be meta-valid, the minimal normalized `$defs` to become `{"$ref":"#/$defs/[object Object]"}`, the complete normalized schema to fail meta-validation, and `buildOutputValidator` to return `error: "invalid JSON schema"`. If current upstream already preserves both inputs by identity and accepts them, stop without creating an issue or duplicate PR and report the fixing identity.

### T2. Port the minimal normalizer repair and regression tests

1. In `packages/coding-agent/test/tools/jtd-to-json-schema.test.ts`, retain the existing pure-JTD, nested-JTD, and #1345 tests, add the following six focused tests, and run this file before the production edit. Require failures attributable to native-schema copying/corruption, not infrastructure:
   - `preserves native JSON Schema identity and content`: input is `{"$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":[{"required":["kind","target"],"properties":{"kind":{"const":"a"},"target":{"$ref":"#/$defs/ref"}}}],"$defs":{"ref":{"type":"object","properties":{"uri":{"type":"string"}}}}}`. Clone the expected value before conversion; require the returned object to be the input and both returned/input content to equal the clone.
   - `converts unambiguous nested JTD at single-schema positions`: for `not`, `if`, `then`, `else`, `items`, `contains`, `propertyNames`, `additionalProperties`, `unevaluatedProperties`, `unevaluatedItems`, and `contentSchema`, use `{ type: "object", annotation, [keyword]: { elements: { type: "string" } } }`; require a new root, the identical `annotation`, and `{ type: "array", items: { type: "string" } }` at the keyword.
   - `converts unambiguous nested JTD at schema-array positions`: repeat for `allOf`, `anyOf`, `oneOf`, and `prefixItems` with a one-element array; require new root/array objects, the identical annotation, and the same converted element.
   - `converts schema-map values without treating member names as schemas`: repeat for `properties`, `patternProperties`, `$defs`, `definitions`, and `dependentSchemas` with `{ ref: { const: "kept" }, nested: { elements: { type: "string" } } }`; require `ref` by identity and only `nested` converted.
   - `preserves data-valued and native extension members by complete identity`: use `dataValue = { elements: { type: "string" } }` inside valid `enum: [dataValue]`, `examples: [dataValue]`, and `default: dataValue`, plus `required: ["elements"]`, `dependentRequired: { x: ["elements"] }`, `$vocabulary: { "https://example.test/elements": true }`, and `allOf: [nativeExtension]` where `nativeExtension = { discriminator: "kind", mapping: { a: "#/$defs/a" } }`; require the complete input, nested data, `allOf` array, and `nativeExtension` by identity with unchanged content.
   - `preserves malformed and deprecated native keyword values for validation`: table-drive `{ type: "object", items: [] }`, `{ type: "object", properties: [] }`, `{ type: "object", oneOf: {} }`, `{ type: "object", dependencies: { x: { elements: { type: "string" } } } }`, and `{ type: "object", additionalItems: { elements: { type: "string" } } }`; require each returned input by identity and unchanged content.
   Do not add the Atlas fixture or edit output-validator/structured-subagent tests: the complete schema remains the manual behavior smoke, existing generic downstream tests remain, and duplicating the same domain contract at three levels violates OMP's test guidance.
2. In `packages/coding-agent/src/tools/jtd-to-json-schema.ts`, import and reuse `isRecord` from `@oh-my-pi/pi-utils`; delete `normalizeMixedSchemaNode` with no alias; and add these private signatures:
   - `isUnambiguousJTDSchema(schema: unknown): boolean`
   - `normalizeJsonSchemaNode(schema: unknown): unknown`
   - `normalizeJsonSchemaArray(value: unknown): unknown`
   - `normalizeJsonSchemaMap(value: unknown): unknown`
3. Keep `isJTDSchema(schema: unknown): boolean`, `jtdToJsonSchema(schema: unknown): unknown`, and `normalizeSchema(schema: unknown): { normalized?: unknown; error?: string }` unchanged. At the root, preserve current pure-JTD detection and call `convertSchema` once. Retain the prior #1345 invariant in one concise comment immediately above that return: `// convertSchema is recursive; re-walking its JSON Schema output caused #1345.` Within native JSON Schema, convert only object-valued `elements`, `values`, or `optionalProperties`; string-valued `ref`; a JTD-only primitive `type` (`timestamp`, `float32`, `float64`, `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`); or a discriminator form proven structurally unambiguous as follows. Do not rely on the current loose `isJTDDiscriminator` guard alone: require string `discriminator`, record-valued `mapping`, and for every own mapping member require a record containing `properties` and/or `optionalProperties`, with each present member record-valued. Implement that check inside `isUnambiguousJTDSchema` with `for…in` plus `Object.hasOwn` so it allocates no `Object.values` array; `convertSchema` may then reuse the existing guard. A native extension node with string-valued mapping entries remains unchanged, as does a nested node whose only signal is `properties` without `type`.
4. Recurse only through these schema-bearing keywords:
   - single schema: `not`, `if`, `then`, `else`, `items`, `contains`, `propertyNames`, `additionalProperties`, `unevaluatedProperties`, `unevaluatedItems`, `contentSchema`;
   - schema array: `allOf`, `anyOf`, `oneOf`, `prefixItems`;
   - schema map values: `properties`, `patternProperties`, `$defs`, `definitions`, `dependentSchemas`.
   Preserve boolean schemas, annotations, assertions, references, unknown keywords, data-valued members, deprecated `dependencies`/`additionalItems`, and malformed known-keyword containers unchanged so the existing meta-validator remains the rejection owner. Use copy-on-write arrays/maps/nodes and return the original object whenever no nested JTD conversion occurs. Add no other production comment.
5. Re-run `bun test packages/coding-agent/test/tools/jtd-to-json-schema.test.ts` and require all existing and six new cases to pass before broader verification.

### T3. Run focused and repository-required verification

From `/Users/kim/dev/oh-my-pi-strict-schema-pr-2026-08-06`, run in this order:

1. `bun test packages/coding-agent/test/tools/jtd-to-json-schema.test.ts`
2. The direct source smoke below; T1 records its pre-fix `invalid JSON schema` result, and after the fix it must print exactly `strict-schema-transport OK`:

   ```bash
   bun -e 'const { buildOutputValidator } = await import("./packages/coding-agent/src/tools/output-schema-validator.ts"); const schema = JSON.parse(await Bun.file("/Users/kim/dev/atlas/app/.agents/skills/atlas-core/assets/atlas-workflow-result.schema.json").text()); const built = buildOutputValidator(schema); if (built.error || !built.validator || built.jsonSchema !== schema) throw new Error(built.error ?? "schema identity lost"); console.log("strict-schema-transport OK");'
   ```

3. `bun check` from the repository root, satisfying the PR template's typecheck/lint gate.
4. `bun --cwd=packages/coding-agent run test` once as the complete coding-agent regression suite; focused coverage never substitutes for this run.

Record exact commands, counts, smoke output, and SHA-256 digests. The tracked diff must contain only `packages/coding-agent/src/tools/jtd-to-json-schema.ts`, `packages/coding-agent/test/tools/jtd-to-json-schema.test.ts`, and `packages/coding-agent/CHANGELOG.md`; the changelog's `[Unreleased] → Fixed` entry is exactly `- Fixed strict output schemas being rejected when native JSON Schema definition maps contain \`ref\` or applicator branches use \`properties\` without \`type\`.` Generated tool views, native addons, Atlas fixtures/tests, and the unrelated repaired-checkout LSP change must not be tracked. For any `bun check` or suite failure, rerun the exact failing case. If attribution remains uncertain, require `/Users/kim/dev/oh-my-pi-strict-schema-pr-base-2026-08-06` to be absent, add it as a detached worktree at the T1 base commit, run `bun install --frozen-lockfile` and `bun --cwd=packages/natives run build` there, and rerun the exact failure: a target-caused failure returns to T2; a base-identical failure is disclosed in PR evidence and may proceed only if focused checks and every PR CI job pass; an inconclusive failure blocks. Remove that worktree only after its evidence is recorded. Never suppress or skip a failure.

### T4. Complete independent verification and code review

Freeze the two code/test files plus changelog by SHA-256. A fresh verifier reruns the focused test and direct source smoke, checks the complete-suite and `bun check` evidence, and returns `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE` without editing. After `VERIFIED`, a distinct reviewer evaluates only the same digests for native JSON Schema preservation, JTD compatibility, malformed-input fail-closed behavior, avoidable allocations, observable-contract test fidelity, comment concision, scope discipline, and current OMP contribution rules. `NOT VERIFIED`, `INCONCLUSIVE`, or `CHANGES REQUIRED` returns to T2, then requires a new T3 target and fresh T4 assurance.

### T5. Deliver the approved branch and open the upstream PR

1. Before staging, commit, push, fork, or PR effects, present the exact diff, digests, and proposed PR body to the user. OMP's `CONTRIBUTING.md` requires the human contributor to review every changed file, understand the behavior, run the relevant checks, exercise the fix, and provide at least one sentence in their own words. Require the user to personally run, from `/Users/kim/dev/oh-my-pi-strict-schema-pr-2026-08-06`, the focused normalizer test, `bun check`, the complete coding-agent suite, and the direct source smoke from T3; record their exact counts/results, including any T3-approved base-identical failure. Any discrepancy from T3 blocks delivery until diagnosed. Insert the user's explanation sentence verbatim under `## Why`; do not generate or paraphrase it. Obtain explicit authorization for the exact staging, commit, fork/push, and PR actions only after those human inputs exist; do not publish autonomously.
2. Stage only the three paths allowed by T3 and verify the staged diff contains no generated files, credentials, machine-local paths, or unrelated changes. The branch and subject are plan choices matching recent OMP practice and PR #1363, not documented repository requirements. Validate this literal Conventional Commit/PR title before committing: `fix(coding-agent/tools): preserve native JSON Schema containers`. Create one initial commit; never amend, rebase, force-push, or push to upstream.
3. Resolve the authenticated GitHub login through the GitHub adapter without reading token/config files, verify `<login>/oh-my-pi` is an existing fork, add it as remote `fork` using `https://github.com/<login>/oh-my-pi.git`, and run `git push --set-upstream fork fix/native-json-schema-containers`. If the fork or write-capable authenticated adapter is absent, stop with that exact prerequisite rather than creating an account/fork, requesting credentials, or pushing elsewhere.
4. Use the GitHub `pr_create` operation for repository `can1357/oh-my-pi`, base `main`, head `<login>:fix/native-json-schema-containers`, `draft: false`, and the same title, with this repository-template content:
   - `## What`: preserve native JSON Schema container maps; continue converting pure root and shape-valid unambiguous nested JTD.
   - `## Why`: the user's verbatim sentence first; then state that native `$defs` maps may legally contain a member named `ref`, and native applicator branches may use `properties` without `type`; generic recursion misclassified both. Link PR #1363 as related context and state that this fixes the remaining native-root path. Do not create a new issue.
   - `## Testing`: report the user's exact focused-test count, `bun check` result, complete coding-agent-suite count, and pre-fix failure/post-fix `strict-schema-transport OK` smoke without including the local absolute schema path. Check `bun check`, local test, and user-facing changelog boxes truthfully.
5. Watch the complete PR workflow with GitHub `run_watch` for the pushed head. Require every non-skipped current PR job—`Resolve release metadata`, `Lint, type check & web build`, `Build native addons (bazel)`, `Test TS workspace fast`, `Test coding-agent singleton/global-state (TS)`, `Test TS native/integration packages`, `Test coding-agent UI/TUI (TS)`, `Test coding-agent runtime/session (TS)`, `Test coding-agent native/unit (TS)`, `Test CLI smoke (TS)`, and `Install method smoke tests`—plus any additional GitHub-reported check to pass. A deterministic target defect ends shipping and returns to T2; after fresh verification/review and renewed user authorization, append one corrective commit to the same branch rather than rewriting history, then watch a new complete check set. A flake, infrastructure failure, or permission failure is retried only when GitHub marks rerun safe or otherwise stops with exact evidence. Do not comment on the PR; the human contributor owns maintainer responses.

## Critical files & anchors

- `packages/coding-agent/src/tools/jtd-to-json-schema.ts` — `normalizeMixedSchemaNode`, stable exports, and context-aware walker seam; current-main blob `ff5728504f78c910d98e42ff106aecb36a1dcc11` is unchanged from v17.2.7.
- `packages/coding-agent/test/tools/jtd-to-json-schema.test.ts` — three existing pure/mixed JTD/#1345 cases and the six focused native-position regressions.
- `packages/coding-agent/src/tools/output-schema-validator.ts` — unchanged `buildOutputValidator` integration used by the real-world smoke.
- `CONTRIBUTING.md` — focused-fix allowance plus mandatory human review, direct exercise, own-words sentence, and supervised publication.
- `.github/PULL_REQUEST_TEMPLATE.md` — exact `What`/`Why`/`Testing` body and local-check/changelog checklist.

## Verification / Done criteria

- [x] Current upstream `main` identity is recorded and the untouched minimal and complete-schema probes reproduce the corruption; otherwise execution stops with evidence of the upstream fix.
- [x] The six new normalizer cases fail for the intended copying/corruption reason before the production edit and pass afterward with all existing cases.
- [x] The minimal native schema and complete Atlas schema return by identity, preserve `$defs.ref` and `properties`-without-`type` branches, and remain accepted by `isValidJsonSchema`.
- [x] Existing pure-root and unambiguous nested JTD outputs remain unchanged; positional tests prove copy-on-write conversion only at recognized schema positions.
- [x] The direct source smoke prints `strict-schema-transport OK`; `bun check`, the focused file, and the complete coding-agent suite pass, or any base-identical local failure is conclusively isolated and disclosed while every PR check passes. Integrated evidence: focused `9/0/110`, smoke exact, TypeScript/lint green; stable-rustfmt and Windows-virtualenv LSP failures reproduced identically on current upstream `3a8591a8a`.
- [x] The tracked diff contains only the normalizer, its focused test, and the exact Unreleased changelog entry; no Atlas fixture/test, downstream duplicate, generated artifact, or unrelated repair is present.
- [x] Independent verifier returns `VERIFIED` and reviewer returns `APPROVED` for unchanged target digests.
- [x] The user reviews every file, understands the behavior, personally runs the focused test, `bun check`, complete coding-agent suite, and direct smoke, supplies the exact results plus a verbatim own-words sentence, and explicitly authorizes the exact delivery effects. Integrated-target evidence and authorization were supplied on 2026-08-06; verbatim sentence: `re-used primitive list, as per comment.`
- [x] The approved initial commit is titled `fix(coding-agent/tools): preserve native JSON Schema containers`; branch history was never rewritten and corrective work used separately verified, authorized conventional commits. The non-draft PR targeted `can1357/oh-my-pi:main`, followed the template, linked #1363 only as context, and merged as `73b91d89d4eacd363d91e320c6941c38030071d7`. No PR checks ran: the first-time-fork workflow completed `action_required` with zero jobs and was later deleted. The upstream maintainer merge plus the user's explicit acceptance and cleanup instruction superseded that final gate; this record does not claim CI passed.

## Assumptions & contingencies

- The contribution starts in the exact absent path `/Users/kim/dev/oh-my-pi-strict-schema-pr-2026-08-06`; never overwrite or repurpose another checkout. If upstream advances but the named interfaces and defect are unchanged, branch from the new `main` tip and execute this contract. If a named interface/test seam changed materially, stop for plan revision; do not improvise a port.
- The verified v17.2.7 checkout is read-only evidence, not the delivery tree. Its Atlas fixture, Atlas-specific downstream tests, generated tool view, native addon, and unrelated LSP regression are never copied into the PR.
- The six generic normalizer cases are the permanent upstream regressions; the complete Atlas schema remains only the real-world pre/post smoke. This matches OMP's observable-contract and non-duplication test guidance.
- `fix/native-json-schema-containers` and `fix(coding-agent/tools): preserve native JSON Schema containers` are selected from recent OMP practice and the related #1363 PR because no contributor branch, commit, or PR-title format is documented.
- A root document whose only JTD/JSON Schema signal is `properties` without `type` remains governed by the existing root `isJTDSchema` behavior because the unchanged API has no dialect marker. The repair resolves ambiguous nested nodes inside an already-native root; changing root dialect selection requires a separate interface decision.
- The PR claims preservation of native JSON Schema structure within OMP's existing accepted subset, not universal Draft 2020-12 evaluation; `meta-validator.ts` and value-validation semantics remain unchanged.
- OMP's human-contribution rules are delivery gates, not delegable checks. Missing human diff review, personal focused/check/suite/smoke results, own-words sentence, or exact delivery authorization leaves the locally verified branch complete but blocks publication.
- Current workflow jobs are expected even though repository metadata does not expose an enforced required-check set to this session. If the authenticated contributor lacks a fork or push permission, stop with that prerequisite; never authenticate on the user's behalf, force-push, or push directly to upstream.

## Completion Summary

- **Delivered behavior**: Native JSON Schema container maps and applicator branches remain intact while pure-root and unambiguous nested JTD continue to convert. Root and nested JTD primitive detection share one own-membership table; the deliberate root-versus-nested `properties` asymmetry remains covered.
- **Verification**: Focused test `9 pass`, `0 fail`, `110 expect() calls`; direct smoke `strict-schema-transport OK`; `bun check` passed for the contributor; the complete coding-agent suite's sole Windows-virtualenv LSP failure was reproduced identically on current upstream. Independent assurance returned `VERIFIED`, Standards/Specification `PASS`, overall `APPROVED`, and `NO DURABLE LEARNING`.
- **Delivery**: Corrective commit `7dcfd9422`, upstream integration merge `cde7f7f30`, and mechanical changelog separator `3ba60e31d` were pushed without history rewriting. PR #7816 was refreshed with current evidence and merged into `can1357/oh-my-pi:main` on 2026-08-07 as `73b91d89d4eacd363d91e320c6941c38030071d7`.
- **User override**: The PR workflow remained `action_required` with zero jobs and was later deleted; no CI pass is claimed. After observing the upstream merge, the user accepted the result and explicitly ordered full cleanup, superseding the unavailable pre-merge check-watch gate.
- **Cleanup**: Deleted `kimprap/fix/native-json-schema-containers` and removed `/Users/kim/dev/oh-my-pi-strict-schema-pr-2026-08-06`. The fork repository remains intact; no upstream branch, PR comment, or unrelated checkout was altered.
- **Residual risk**: Upstream accepted the contribution without observable PR CI. Local and independent evidence cover the changed schema behavior; the existing root dialect ambiguity remains intentionally out of scope.
