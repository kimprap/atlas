# Dev Ask Grilling Scope

**Datetime**: 2026-08-04-1557
**Scope**: Neutral one-context grilling classification and routing evaluation in the user-owned `dev-ask` workflow
**Summary**: Tighten only the grilling decision seam so a provisional engineering approach offered for refinement is interviewed before later lifecycle work, without routing implementation-ready, factual, requirements-gap, product-authority, or breadth-only requests through grilling. Prove the change with the user's repository-guidance prompt and objective near misses.
**Status**: DONE

## Context

The current `dev-ask` classifier names `grill-me` and `grill-with-docs`, but its closed `## Route outcomes` list omits a grilling lane and “Skip interviewing when authority is complete” does not distinguish final authority from a detailed proposal offered for refinement. Existing `R-GRILL` covers only an explicit stateless “stress-test” request. A fresh pre-change OMP smoke of the user’s exact prompt selected `grill-with-docs`, but emitted only `Route: grill-with-docs`, named only the first approval gate, and omitted the required return to `dev-ask`; the target is therefore a partially implicit, nondeterministic boundary rather than an always-wrong first-owner choice.

The intended end state is `dev-ask → grill-me|grill-with-docs → immutable decision-evidence artifact + common Handoff → dev-ask recomputation`. A proposal plus a request to refine/challenge/compare/validate/choose it is candidate intent, while a settled edit, factual/read-only request, ordinary requirements gap without a candidate approach, product-authority gap, route fog, or breadth alone retains its current route.

Affected targets, before any mutation:

1. `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/SKILL.md`
2. `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/evals.json`
3. `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/fixtures/r-approach-refinement/case.json` (new)
4. `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/fixtures/r-approach-refinement-near-miss-direct/case.json` (new)
5. `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/fixtures/r-approach-refinement-near-miss-readonly/case.json` (new)
6. `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/fixtures/r-approach-refinement-near-miss-requirements/case.json` (new)

`WORKFLOW.md`, `grill-me`, `grill-with-docs`, `dev-grilling`, `dev-handoff`, every non-grilling route contract, and installed harness configuration remain unchanged.

```text
Goal: Recognize a provisional codebase-grounded approach offered for refinement as one-context grilling intent without widening other routes.
Route: dev-implementation → dev-ask completion presentation
Why: Product intent and acceptance are settled for one cohesive skill/eval change. The user-global router is a shared authorization and compatibility surface, so compact is disqualified and high-consequence assurance applies; no requirements/specification/ticket stage is needed.
Artifacts: updated dev-ask skill, four-case router eval family and mirrored fixtures, verification/review evidence
Gates: approval of this exact plan/Route Overview; no destructive, credential, deployment, or external-effect gate
Execution: one owner; assurance: high-consequence
First action: re-read and report the six affected paths above, then edit only the grilling classification/outcome seams in `SKILL.md`.
```

## Tasks

- [x] T1. Define and install the neutral provisional-decision grilling scope
  completed 2026-08-04-1633
- [x] T2. Add the supplied documented-codebase prompt and near-miss routing evaluations
  completed 2026-08-04-1635
- [x] T3. Run the focused routing smoke and unchanged-route regressions
  completed 2026-08-04-2030

## Approach

### T1. Make candidate-approach refinement an explicit grilling lane

In `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/SKILL.md`, change only four grilling-scoping regions.

1. Replace `## Classify in order` item 3 with:

   ```markdown
   3. **Product authority and engineering requirements** — unresolved product strategy stops with `PRODUCT AUTHORITY REQUIRED`. Sufficient product authority with incomplete observable behavior, acceptance, engineering scope, or constraints routes to `dev-requirements`, except when the request first presents the one-context candidate-approach decision defined in item 5; interview that intent and return through `dev-ask` before resolving any remaining requirements gap.
   ```

2. Replace item 5 with:

   ```markdown
   5. **One-context intent decisions** — trigger this route only when the user presents a candidate approach, hypothesis, plan, or design direction and asks for decision-shaping scrutiny before execution—for example, refinement, challenge, stress-testing, validation, comparison, or choice; a detailed proposal remains unsettled intent even when it includes a preferred solution. Use `grill-with-docs` when the decision depends on current repository code, contracts, terminology, module boundaries, architecture, or guidance; otherwise use `grill-me`. Route the selected grill back to `dev-ask` for recomputation; grilling never authorizes implementation. Do not interview for a settled direct edit, a factual/read-only answer or research lookup, ordinary missing observable behavior/acceptance/scope/constraints with no candidate approach, unresolved product authority, route fog, or breadth alone.
   ```

3. Replace the paragraph immediately after the ordered classifier with:

   ```markdown
   A user-named stage is a strong preference, not a gate bypass. Validate prerequisites and add only the smallest missing prerequisite path. If one fact changes the first owner, ask only that gating question. If materially different lifecycle routes remain, present two or three options and one recommendation; candidate-approach refinement uses `grill-me` or `grill-with-docs`, while ordinary missing observable behavior, acceptance, scope, or constraints remains owned by `dev-requirements`.
   ```

4. Insert this bullet in the closed `## Route outcomes` list immediately after the existing `dev-requirements` bullet:

   ```markdown
   - **Grilling lane** for the one-context candidate-approach/refinement intent defined in classification. Use `grill-me` when stateless and `grill-with-docs` when current codebase evidence is decision-bearing. The interview returns one immutable decision-evidence artifact plus the common Handoff to `dev-ask` for recomputation; it never authorizes requirements, specification, tickets, implementation, or another external effect.
   ```

Preserve classifier items 1–2, 4, and 6–8; frontmatter; all non-grilling Route outcomes; the seven Route Overview fields; approval/reapproval; one-first-dispatch; generic backend/Handoff handling; completion; and stop semantics. Do not add a keyword/regex matcher or copy `Atlas`, `AGENTS.md`, ADR, `INDEX.md`, “I suppose,” or another sample-specific token into routing guidance.

Do not edit `WORKFLOW.md`: its `## Interface` says `SKILL.md` owns classification, `## Module ownership` already assigns decision work to `dev-grilling`, and `## Maintenance` limits edits to interface/lifecycle/ownership/durable-contract/invariant changes. The grilling round trip already exists in `R-GRILL`, `dev-grilling`, and the generic Handoff/re-entry contract; this task only makes its trigger and closed outcome explicit.

### T2. Add one positive and three decisive near-miss evals

In `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/evals.json`, preserve the root `schema_version: 2`, `skill_name: "dev-ask"`, all existing cases, case order outside the grilling family, and the shared router criterion/proof/five-point rubric. Insert the four cases below after `R-GRILL` and before `R-GRILL-NEAR-MISS`. Every new case uses `layer: "router"`, `repetition_tier: "hard"`, `required_capabilities: []`, `absent_capabilities: []`, and copies `R-GRILL`’s criterion, proof, and rubric verbatim.

Also change only `expected.artifacts` in existing `R-GRILL` and `R-PROTOTYPE-NEAR-MISS` from `[]` to:

```json
["immutable decision-evidence artifact", "common Handoff"]
```

This aligns both existing grilling routes with the already-governing `dev-grilling` output contract. Do not change their inputs, owners, gates, routes, events, fixtures, or outcomes.

#### `R-APPROACH-REFINEMENT`

Use the user’s exact prior point-2 prompt, without a routing hint or paraphrase, in both manifest and fixture:

```text
repo-local rules could be configured to be automatically injected into any agent harness, this ensures discovery on any agent/subagent sessions. However, other contracts are not, i.e. adrs, architecture.md, etc. The only good place to ensure their discovery would be repo-local @.agents/AGENTS.md . Give me a refined approach to design this into AGENTS.md. I suppose for ADRs, given there is a shared INDEX.md cache mapping, this should be included instead of brittlely listing all ADRS in there, which could get stale very easily.
```

Set:

- `fixture_dir`: `fixtures/r-approach-refinement`
- `expected.artifacts`: `["immutable decision-evidence artifact", "common Handoff"]`
- `expected.first_owner`: `grill-with-docs`
- `expected.gates`: `["overview approval", "recomputed Route Overview approval"]`
- `expected.mode`: `one owner`
- `expected.outcome`: `documented-codebase interview dispatch`
- `expected.owners`: `["grill-with-docs", "dev-ask"]`
- `expected.route`: `grill-with-docs → dev-ask (recompute)`
- `required_events`: `["overview", "approval", "identity-recheck", "dispatch:grill-with-docs"]`
- `forbidden_events`: `["interview-bypass", "router-deep-interview", "mutation", "persistence", "dispatch:dev-requirements", "dispatch:dev-specification", "dispatch:dev-implementation"]`
- `scripted_replies`: `["APPROVE the current Route Overview"]`

The router trace stops after the simulated approved first dispatch. It promises, but never fabricates, the downstream interview’s decision evidence/Handoff.

#### `R-APPROACH-REFINEMENT-NEAR-MISS-DIRECT`

Use this exact request:

```text
The desired behavior, scope, architecture, compatibility, failure behavior, acceptance, and verification are already settled. Apply the bounded approved edit now; do not reconsider or refine the approach.
```

Set:

- `fixture_dir`: `fixtures/r-approach-refinement-near-miss-direct`
- `expected.artifacts`: `["terminal evidence (promised downstream output)"]`
- `expected.first_owner`: `dev-implementation`
- `expected.gates`: `["overview approval"]`
- `expected.mode`: `one owner`
- `expected.outcome`: `direct implementation dispatch`
- `expected.owners`: `["dev-implementation", "dev-ask"]`
- `expected.route`: `dev-implementation → dev-ask completion presentation`
- `required_events`: `["overview", "approval", "identity-recheck", "dispatch:dev-implementation"]`
- `forbidden_events`: `["unnecessary-interview", "dispatch:grill-me", "dispatch:grill-with-docs"]`
- `scripted_replies`: `["APPROVE the current Route Overview"]`

#### `R-APPROACH-REFINEMENT-NEAR-MISS-READONLY`

Use this exact request:

```text
Explain the existing implementation and why its current approach behaves as it does. I am not proposing a change or asking for critique; answer from sufficient current evidence only.
```

Set:

- `fixture_dir`: `fixtures/r-approach-refinement-near-miss-readonly`
- `expected.artifacts`: `[]`
- `expected.first_owner`: `null`
- `expected.gates`: `[]`
- `expected.mode`: `none`
- `expected.outcome`: `immediate evidence-backed answer`
- `expected.owners`: `[]`
- `expected.route`: `direct answer`
- `required_events`: `["overview", "direct-answer"]`
- `forbidden_events`: `["dispatch", "mutation", "persistence"]`
- `scripted_replies`: `[]`

#### `R-APPROACH-REFINEMENT-NEAR-MISS-REQUIREMENTS`

Use this exact request:

```text
I want to change the behavior, but the observable result, failure handling, scope, constraints, and acceptance criteria are not settled. I have no candidate approach to refine.
```

Set:

- `fixture_dir`: `fixtures/r-approach-refinement-near-miss-requirements`
- `expected.artifacts`: `["Engineering Requirements Brief"]`
- `expected.first_owner`: `dev-requirements`
- `expected.gates`: `["overview approval", "requirements approval", "recomputed Route Overview approval"]`
- `expected.mode`: `one owner`
- `expected.outcome`: `requirements dispatch; return for recomputed overview`
- `expected.owners`: `["dev-requirements", "dev-ask"]`
- `expected.route`: `dev-requirements → dev-ask (recompute)`
- `required_events`: `["overview", "approval", "identity-recheck", "dispatch:dev-requirements"]`
- `forbidden_events`: `["interview-before-requirements", "dispatch:grill-me", "dispatch:grill-with-docs"]`
- `scripted_replies`: `["APPROVE the current Route Overview"]`

Create each named fixture `case.json` with exactly three keys in the existing fixture order: `"additional_files": []`, `"inputs"` byte-identical to the manifest case’s request object, and `"scripted_replies"` byte-identical to the manifest case. Do not add a runner, schema, reference, script, or second eval manifest; no existing equivalent or local runner exists under `dev-ask/evals/`.

### T3. Prove the new boundary without executing downstream work

After T1–T2, freeze the exact six-file target listed in Context. Run the deterministic registration/fixture checks and the fresh semantic smoke specified under Verification. The smoke is a read-only router simulation: it may record an approved first-dispatch event but must not conduct a grilling interview, invoke requirements/specification/implementation, or mutate any repository/system state.

Treat any correct first owner with a missing `dev-ask` return, missing recomputed-overview gate, missing decision-evidence/Handoff artifact, or extra downstream dispatch as a failure. Repair only T1/T2 under the same authority, then rerun the entire seven-case smoke; do not accept majority success.

## Critical files & anchors

- `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/SKILL.md` — `## Classify in order`, closed `## Route outcomes`, and the adjacent route-clarification paragraph; the only runtime behavior target.
- `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/evals.json` — schema-v2 router manifest; `R-GRILL`, `R-GRILL-NEAR-MISS`, and `R-PROTOTYPE-NEAR-MISS` are the patterns/compatibility sentinels.
- `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/fixtures/r-approach-refinement/case.json` — exact user-prompt positive transport.
- `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/fixtures/r-approach-refinement-near-miss-*/case.json` — three one-fact-changed guards for direct, read-only, and requirements routes.
- `/Users/kim/.dotfiles/.config/agents/skills/dev-ask/WORKFLOW.md` — `## Maintenance`; read-only authority proving no overview edit is warranted for a classifier-only clarification.

## Verification

Work from `/Users/kim/.dotfiles`; no environment variables, credentials, network, disposable repository, or external effects are required.

1. Confirm the live OMP skill root still resolves to this source:

   ```bash
   readlink /Users/kim/.agents
   ```

   Expected stdout: `/Users/kim/.dotfiles/.config/agents`. Any other value blocks the live smoke; do not copy files into another harness root.

2. Parse the manifest, prove unique IDs, require every registered fixture, verify all four new manifest/fixture input pairs, and assert the two aligned existing artifact expectations:

   ```bash
   python3 -c 'import json,pathlib; p=pathlib.Path("/Users/kim/.dotfiles/.config/agents/skills/dev-ask/evals/evals.json"); d=json.loads(p.read_text()); cs=d["cases"]; by={c["id"]:c for c in cs}; new={"R-APPROACH-REFINEMENT","R-APPROACH-REFINEMENT-NEAR-MISS-DIRECT","R-APPROACH-REFINEMENT-NEAR-MISS-READONLY","R-APPROACH-REFINEMENT-NEAR-MISS-REQUIREMENTS"}; assert d["schema_version"]==2 and d["skill_name"]=="dev-ask"; assert len(by)==len(cs); assert new<=by.keys(); assert all((p.parent/c["fixture_dir"]/"case.json").is_file() for c in cs); assert all(json.loads((p.parent/by[i]["fixture_dir"]/"case.json").read_text())=={"additional_files":[],"inputs":by[i]["inputs"],"scripted_replies":by[i]["scripted_replies"]} for i in new); expected=["immutable decision-evidence artifact","common Handoff"]; assert by["R-GRILL"]["expected"]["artifacts"]==expected; assert by["R-PROTOTYPE-NEAR-MISS"]["expected"]["artifacts"]==expected; print("dev-ask grilling eval registration OK")'
   ```

   Expected stdout: `dev-ask grilling eval registration OK`.

3. Run the seven cases as a real two-turn OMP smoke, with three fresh read-only `scout` attempts per case (21 attempts total, one parallel `task` batch, under the 32-agent cap).

   Phase A gives each attempt only `skill://dev-ask`, that case’s `inputs` (never its `scripted_replies`), and:

   ```text
   Apply the installed dev-ask router to the supplied request. Emit the seven-field Route Overview and, for a direct-answer route, its immediate evidence-backed answer. Otherwise stop and wait for approval. Do not inspect eval definitions, perform downstream stage work, dispatch another agent, or mutate anything.
   ```

   Keep each attempt blind to `expected`, required/forbidden events, rubrics, sibling cases, prior outputs, and the approval reply. Grade the initial overview before continuing. If an approval-gated overview is wrong, do not approve it; record that attempt as failed. For every correct approval-gated overview, send the sole string from that case’s `scripted_replies` array via OMP `hub` to the same live agent ID, then collect its continuation through `approval`, fresh `identity-recheck`, and exactly one `dispatch:<first_owner>` semantic event; the continuation stops without running the dispatched owner. Direct-answer attempts receive no second turn.

   Grade the combined two-turn transcript against the manifest. All three attempts per case must match route, ordered owners, first owner, gates, artifacts, mode, outcome, required events, and forbidden-event absence. `R-APPROACH-REFINEMENT` must use the exact user prompt and select `grill-with-docs → dev-ask (recompute)`; `R-GRILL` must remain `grill-me → dev-ask (recompute)`; `R-PROTOTYPE-NEAR-MISS` must remain a no-prototype `grill-me` route with the aligned artifacts; the breadth near miss must remain the specification/ticket lane. No averaging or majority pass.

4. Freeze SHA-256 identities for the six affected files only. A fresh read-only `dev-verification` attempt must independently rerun steps 1–3 against those identities and return criterion-level `VERIFIED`; a distinct decorrelated `dev-code-review` attempt must return Standards `PASS`, Specification `PASS`, Overall `APPROVED`, with no repair. Run the required high-consequence terminal assessment without mutation: only `NO DURABLE LEARNING` completes this plan. A qualified guidance-write candidate returns `BLOCKED` with its proposed destination and requires separately approved affected-file scope; `CURATED` is not an in-scope success because any post-proof write would invalidate the six-file target.

The target passes only if the fresh positive smoke exposes both approvals and the `dev-ask` return, all three decisive near misses retain their owners, the existing stateless/no-prototype/breadth sentinels remain unchanged except for the two explicitly aligned artifact arrays, every fixture mirrors its manifest input, and no file beyond the six named targets changed.

## Assumptions & contingencies

- `/Users/kim/.agents` currently resolves to `/Users/kim/.dotfiles/.config/agents`, so fresh OMP subagents exercise the edited canonical source without a deployment/copy step. If that binding drifts, stop with the observed path and require a separately authorized harness-install decision.
- No behavioral eval runner or runner reference exists under `dev-ask/evals/`; the fresh isolated OMP batch is the runnable semantic smoke, while the Python command is only deterministic manifest/fixture proof. If an official runner becomes discoverable before execution, run these same seven IDs through it in addition to—not instead of—the OMP smoke; never invent CLI syntax.
- `WORKFLOW.md` remains unchanged because the grilling route, decision evidence, common Handoff, and router re-entry already exist; only trigger precedence and the closed Route-outcome inventory change. If `WORKFLOW.md` or a supporting owner contract drifts and contradicts this fact before execution, stop for plan/authority revision rather than broadening writes.
- The exact supplied prompt is a documented-codebase decision because the proposed discovery design depends on repository-local contracts; select `grill-with-docs`. A stateless prompt with the same refinement intent selects `grill-me`.
- Scope is semantic and conjunctive: candidate approach/design plus an explicit request for decision-shaping scrutiny before execution; refinement, challenge, stress-testing, validation, comparison, and choice are examples rather than a keyword list. Never match on sample nouns, tentative phrasing alone, repository vocabulary alone, planning language alone, file count, or request size.
- A fresh attempt that selects the right first owner but omits the `dev-ask` recomputation boundary, the downstream approval gate, or the promised decision-evidence/Handoff artifacts is a failed smoke, not a partial pass.
- Terminal curation has no write authority under this six-file plan. Do not reinterpret a candidate as permission to modify one of the targets or another guidance file after verification.

## Completion Summary

Completed 2026-08-04-2030.

- Installed the conjunctive candidate-approach/refinement classifier and closed grilling outcome in `dev-ask/SKILL.md`. Documented-codebase decisions route through `grill-with-docs`; stateless decisions use `grill-me`; both return immutable decision evidence plus the common Handoff to `dev-ask` for recomputation.
- Registered the exact supplied prompt, three decisive near misses, mirrored fixtures, and the two authorized existing grilling-artifact alignments. No runner, schema, script, reference, or workflow-contract edit was added.
- Final six-file target:
  - `SKILL.md` — `dae5dcfe52a7f97b082252dd1a730ae2e31655092c93dee8ec409d802feed3c6`
  - `evals/evals.json` — `793fe1f3b19153c701416724595a9effaa93a2a431c569ea0f9be82f09820fbc`
  - positive fixture — `acd7f655a6736c8a5737cce59194ea2e7d693a7a2d13db89574ce528ab4630b3`
  - direct near-miss fixture — `e3e08250ec44f021d68079a784f293b1b511d5abdbdf819712e71a81e5ff4339`
  - read-only near-miss fixture — `e1b9f1ef57deae489817d4ca9edf24fe8f7f735c29bae873813906b5041f9707`
  - requirements near-miss fixture — `154413654c2a5f0fc91f1da5c0f760937c529e9db6f1b951374bcba26187b100`
- Verification:
  - Live binding remained `/Users/kim/.agents -> /Users/kim/.dotfiles/.config/agents`.
  - Deterministic manifest/fixture proof returned `dev-ask grilling eval registration OK`.
  - Batch I ran one parallel batch of 21 fresh blind scouts: three attempts for each of seven cases. All routed attempts stopped, accepted the exact approval, reread `dev-ask`, rechecked identity, and recorded one prospective first owner without invoking it; all direct-answer attempts remained one-turn and effect-free.
  - `agent://GrillScopeVerifierJ` independently returned aggregate `VERIFIED` against the immutable target and bound rule manifest.
  - `agent://GrillScopeReviewer` returned Standards `PASS`, Specification `PASS`, Overall `APPROVED`, with no findings or advisories.
  - `agent://GrillScopeLearning` returned corrected terminal outcome `NO DURABLE LEARNING`; no guidance write occurred.
- Evidence transport:
  - `local://dev-ask-grilling-scope-smoke-i.json`
  - `local://dev-ask-grilling-scope-rule-manifest.json`
  - Batch G was diagnostic-only because four Phase-A payloads were not visible before continuation. Batch H failed pre-semantically on an invalid output schema. Neither was used as final proof or mutated the target.
- Residual risk: the smoke intentionally proves router classification and prospective first-owner dispatch only; downstream grilling, requirements, specification, and implementation work were not executed. Reviewer/verifier model-family separation was not recorded, but role, context, and attempt identities were distinct and the reviewer reported no blocking assurance gap.
