# Custom AI Coding Workflow

**Datetime**: 2026-07-13-2349
**Scope**: Research, design, author, and evaluate a cohesive host-global AI coding workflow under `/Users/kim/.dotfiles/.config/agents/skills/`.
**Summary**: Use Atlas to preserve source evidence and the durable workflow recommendation, then implement a minimal set of user-facing workflow skills backed by one support core and existing reusable skills, and verify discovery, dispatch, stage transitions, and cleanup.
**Status**: IN_PROGRESS

## Context

The requested end state is a custom end-to-end AI coding workflow informed by Matt Pocock's engineering skills, obra's Superpowers, Cursor Team Kit, and the user's existing host-global skills. The workflow must expose a small, consistently prefixed set of concise user-invoked stages, keep reusable procedure in clearly named non-surfacing skills, route context dynamically to the correct underlying skills, and preserve the comparative research and final decisions in Atlas for later iteration. All shipped workflow artifacts belong under `/Users/kim/.dotfiles/.config/agents/skills/`; Atlas receives living research only at `vault://atlas/…`.

## Tasks

- [x] T1. Establish workflow research topic and ingest sources
  - completed 2026-07-14-1416
- [ ] T2. Compare source workflows and local reusable skills
- [ ] T3. Conclude naming, stages, and routing interface
- [ ] T4. Author thin stage skills and support core
- [ ] T5. Evaluate invocation, behavior, transitions, and cleanup
- [ ] T6. Review final workflow and update durable contracts

## Approach

### T1. Establish workflow research topic and ingest sources

1. Use `/atlas-index` to create a separate durable topic under the existing `agent-systems` domain and `harness` subdomain, rather than widening the existing `agentic-harness-architecture` topic. Use topic ID `ai-coding-workflow`, canonical title `AI coding workflow`, path `vault://atlas/summaries/research/agent-systems/harness/topics/ai-coding-workflow/INDEX.md`, aliases `agentic coding workflow; coding workflow skills`, include terms `AI coding workflow; agentic coding workflow; coding-agent workflow; coding workflow skills; brainstorming; specification iteration; implementation planning; test-driven implementation; code review; verification; housekeeping; workflow skill orchestration`, exclude terms `model training; foundation-model architecture; generic IDE feature; Atlas product maintenance; non-coding personal productivity workflow`, no canonical tags, and refresh model `same-as-topic-creation`. Create the `TOPICS.md` row first, then the lean topic folder from the Atlas research templates.
2. Invoke `/atlas-source` separately for the three explicit repository roots so each becomes a durable source artifact and manifest row: `https://github.com/mattpocock/skills`, `https://github.com/obra/superpowers`, and `https://github.com/cursor/plugins/tree/main/cursor-team-kit/skills`. Let `atlas-source` canonicalize/deduplicate and run `atlas-route` for each new or materially changed source. Resolve each repository's current `main` commit, then ingest immutable `blob/<commit>/…/SKILL.md` URLs for the exact skills selected for comparison in T2; repository-root summaries alone are not sufficient evidence for stage-level claims. Do not substitute uncaptured live-web text for Atlas evidence.
3. Record the resulting Atlas topic path, the three repository-root source artifacts, and one immutable source artifact for every skill page actually compared in T2—including each artifact path, source ID/sequence, and route edge—in the execution log before comparative synthesis. If `vault://atlas/` is unavailable, stop before source research and repair/reselect the active Atlas connector profile; do not write research into this product repository or a raw filesystem substitute.

#### T1 execution log

- Topic: `vault://atlas/summaries/research/agent-systems/harness/topics/ai-coding-workflow/INDEX.md`
- Topic state after routing: `dirty`; 31 pending edges; newest pending source seq `35`; source watermark `0`.
- Immutable repository snapshots:
  - Matt Pocock: `66898f60e8c744e269f8ce06c2b2b99ce7660d5f`
  - obra/Superpowers: `d884ae04edebef577e82ff7c4e143debd0bbec99`
  - Cursor plugins: `3fe2823ce17c1656c222d4b7c59d3f82fbf20143`

| Seq | Source | Source ID | Artifact | Route edge |
|---:|---|---|---|---|
| 5 | Matt Pocock repository root | `637c99109af3` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--637c99109af3--matt-pocock-skills.md` | `edge--637c99109af3--ai-coding-workflow--6dcf70df` |
| 6 | obra/Superpowers repository root | `8c6014a36ca9` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--8c6014a36ca9--obra-superpowers.md` | `edge--8c6014a36ca9--ai-coding-workflow--1b098d73` |
| 7 | Cursor Team Kit skills root | `5c3a33bb2588` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--5c3a33bb2588--cursor-team-kit-skills.md` | `edge--5c3a33bb2588--ai-coding-workflow--785aa899` |
| 8 | Matt `ask-matt` | `1e63d09007f4` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--1e63d09007f4--matt-ask-matt.md` | `edge--1e63d09007f4--ai-coding-workflow--33a6b946` |
| 9 | Matt `grill-with-docs` | `c81003a6c90e` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--c81003a6c90e--matt-grill-with-docs.md` | `edge--c81003a6c90e--ai-coding-workflow--b6f8ef05` |
| 10 | Matt `to-spec` | `47acd0111078` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--47acd0111078--matt-to-spec.md` | `edge--47acd0111078--ai-coding-workflow--480609bd` |
| 11 | Matt `to-tickets` | `26abf4ab553d` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--26abf4ab553d--matt-to-tickets.md` | `edge--26abf4ab553d--ai-coding-workflow--c5e44bbb` |
| 12 | Matt `implement` | `1bb984f41e17` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--1bb984f41e17--matt-implement.md` | `edge--1bb984f41e17--ai-coding-workflow--d4d83b43` |
| 13 | Matt `tdd` | `73bf3457d70f` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--73bf3457d70f--matt-tdd.md` | `edge--73bf3457d70f--ai-coding-workflow--9f48c538` |
| 14 | Matt `code-review` | `5573cb1375aa` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--5573cb1375aa--matt-code-review.md` | `edge--5573cb1375aa--ai-coding-workflow--116faf5f` |
| 15 | Matt `triage` | `45b4cce44c12` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--45b4cce44c12--matt-triage.md` | `edge--45b4cce44c12--ai-coding-workflow--2ae2a9da` |
| 16 | Matt `diagnosing-bugs` | `21587b906a86` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--21587b906a86--matt-diagnosing-bugs.md` | `edge--21587b906a86--ai-coding-workflow--fd1e4abe` |
| 17 | Matt `prototype` | `3a7519cda85d` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--3a7519cda85d--matt-prototype.md` | `edge--3a7519cda85d--ai-coding-workflow--a17864c7` |
| 18 | Superpowers `brainstorming` | `75e8bd575766` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--75e8bd575766--superpowers-brainstorming.md` | `edge--75e8bd575766--ai-coding-workflow--dedf65d5` |
| 19 | Superpowers `writing-plans` | `1e28b6b13b4b` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--1e28b6b13b4b--superpowers-writing-plans.md` | `edge--1e28b6b13b4b--ai-coding-workflow--be4a0749` |
| 20 | Superpowers `executing-plans` | `4a59b0549eaf` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--4a59b0549eaf--superpowers-executing-plans.md` | `edge--4a59b0549eaf--ai-coding-workflow--0a70d738` |
| 21 | Superpowers `subagent-driven-development` | `355dd83e50b9` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--355dd83e50b9--superpowers-subagent-driven-development.md` | `edge--355dd83e50b9--ai-coding-workflow--ba8b8663` |
| 22 | Superpowers `test-driven-development` | `daeadbe9a0e0` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--daeadbe9a0e0--superpowers-test-driven-development.md` | `edge--daeadbe9a0e0--ai-coding-workflow--04dec4ea` |
| 23 | Superpowers `systematic-debugging` | `8b7f4f4ae6e3` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--8b7f4f4ae6e3--superpowers-systematic-debugging.md` | `edge--8b7f4f4ae6e3--ai-coding-workflow--88e65200` |
| 24 | Superpowers `requesting-code-review` | `24aad600eab1` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--24aad600eab1--superpowers-requesting-code-review.md` | `edge--24aad600eab1--ai-coding-workflow--95c61506` |
| 25 | Superpowers `receiving-code-review` | `5cb40c37e967` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--5cb40c37e967--superpowers-receiving-code-review.md` | `edge--5cb40c37e967--ai-coding-workflow--57ec1fee` |
| 26 | Superpowers `verification-before-completion` | `dd4783669de0` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--dd4783669de0--superpowers-verification-before-completion.md` | `edge--dd4783669de0--ai-coding-workflow--963f6b63` |
| 27 | Superpowers `finishing-a-development-branch` | `976826fa3f65` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--976826fa3f65--superpowers-finishing-a-development-branch.md` | `edge--976826fa3f65--ai-coding-workflow--c8861bbf` |
| 28 | Cursor `workflow-from-chats` | `b05767a03e45` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--b05767a03e45--cursor-workflow-from-chats.md` | `edge--b05767a03e45--ai-coding-workflow--b81b8d6d` |
| 29 | Cursor `check-compiler-errors` | `49949449ba8a` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--49949449ba8a--cursor-check-compiler-errors.md` | `edge--49949449ba8a--ai-coding-workflow--fe4cdaab` |
| 30 | Cursor `run-smoke-tests` | `0625f99d10ef` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--0625f99d10ef--cursor-run-smoke-tests.md` | `edge--0625f99d10ef--ai-coding-workflow--31c554bd` |
| 31 | Cursor `verify-this` | `d48936aad15f` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--d48936aad15f--cursor-verify-this.md` | `edge--d48936aad15f--ai-coding-workflow--56fb7eba` |
| 32 | Cursor `deslop` | `6a6cf8e0b1f4` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--6a6cf8e0b1f4--cursor-deslop.md` | `edge--6a6cf8e0b1f4--ai-coding-workflow--0b889f28` |
| 33 | Cursor `make-pr-easy-to-review` | `4c5ffa011860` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--4c5ffa011860--cursor-make-pr-easy-to-review.md` | `edge--4c5ffa011860--ai-coding-workflow--ebee8403` |
| 34 | Cursor `review-and-ship` | `3c7ecb40ca29` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--3c7ecb40ca29--cursor-review-and-ship.md` | `edge--3c7ecb40ca29--ai-coding-workflow--eda2dc10` |
| 35 | Cursor `thermo-nuclear-code-quality-review` | `4d9eca04c6c7` | `summaries/sources/artifacts/2026/2026-07/2026-07-14--4d9eca04c6c7--cursor-thermo-nuclear-code-quality-review.md` | `edge--4d9eca04c6c7--ai-coding-workflow--2dd9ae58` |

- Verification: all 31 artifacts were re-read with matching source ID, sequence, canonical URL, content hash, and `routing_status: routed`; all 31 manifest rows and pending relation edges resolve; `python3 scripts/atlas-instance.py check` returned `check OK`.


### T2. Compare source workflows and local reusable skills

1. Build the comparison only from the Atlas artifacts created in T1. Cover these official source candidates before pruning:
   - Matt Pocock: `ask-matt`, `grill-with-docs`, `to-spec`, `to-tickets`, `implement`, `tdd`, `code-review`, `triage`, `diagnosing-bugs`, and `prototype`.
   - obra/Superpowers: `brainstorming`, `writing-plans`, `executing-plans`, `subagent-driven-development`, `test-driven-development`, `systematic-debugging`, `requesting-code-review`, `receiving-code-review`, `verification-before-completion`, and `finishing-a-development-branch`.
   - Cursor Team Kit: `workflow-from-chats`, `check-compiler-errors`, `run-smoke-tests`, `verify-this`, `deslop`, `make-pr-easy-to-review`, `review-and-ship`, and `thermo-nuclear-code-quality-review`.
2. Compare each candidate on the same decision-bearing dimensions: user/manual versus model activation; stage purpose and entry condition; handoff/next-stage rule; required user gates; codebase exploration; spec and ticket artifact ownership; task sizing/dependencies; TDD and debugging behavior; review axes; verification evidence; commit/PR/CI behavior; context handoffs/delegation; temporary artifact lifecycle; and assumptions about a tracker or harness. Record "adopt", "adapt", "existing local equivalent", or "reject" with one evidence citation and one reason for every candidate.
3. Audit the existing local skills before proposing any new core procedure. Reuse `/Users/kim/.dotfiles/.config/agents/skills/grilling/`, `grill-with-docs/`, `domain-modeling/`, `eng-codebase-design/`, `eng-prototype/`, `eng-diagnosing-bugs/`, `eng-tdd/`, `improve/`, and `craft-skill/` where their current contracts fit. Do not fork their procedures into the workflow; a workflow core may only state when and with what context to invoke them. Preserve their current names by default because they are shared capabilities, not workflow-private internals.
4. Invoke `/atlas-research --vault-only` for `ai-coding-workflow` after all selected skill pages have Atlas artifacts and route edges. Because routing is expected to make the existing topic `dirty`, honor `atlas-research`'s mandatory handoff to `/atlas-refresh`; refresh is the only normal dirty→current transition and must create the dated pass, apply pending edges, and recompute the topic cache. The resulting current answer must contain: a source comparison matrix; a recommended stage graph; an adoption/rejection matrix; an artifact lifecycle table distinguishing durable from temporary outputs; activation/transport findings for OMP and Grok; unresolved preference choices for T3; an evidence map; and the source artifacts used. Unsupported claims remain explicit gaps.
5. Record licensing in the pass: Matt Pocock's repository is MIT (`Copyright (c) 2026 Matt Pocock`), obra/Superpowers is MIT (`Copyright (c) 2025 Jesse Vincent`), and Cursor Team Kit is MIT (`Copyright (c) 2026 Cursor`). Reimplement the selected behavior in original wording. If any substantial source text or template is retained, bundle the corresponding full license notice with the adapted skill and link it directly from that skill; a source URL or metadata field alone is not a replacement for the MIT notice.
6. Pressure-test this provisional synthesis in the Atlas answer: adopt Matt's thin wrappers, main-flow/on-ramp distinction, tracer-bullet dependency edges, and separate Spec/Standards review axes; adapt Superpowers' one-question design loop, explicit plan execution, red verification, technical handling of review feedback, and fresh evidence gate without importing its blanket always-design/worktree/commit mandates; adapt Cursor's falsifiable verification, focused smoke/type checks, diff cleanup, reviewability, and ship-readiness checks without hard-coding Cursor-only commands. Reject any borrowed rule that duplicates the stronger local contract or makes every task pay for a rare path.

### T3. Conclude naming, stages, and routing interface

1. Present the Atlas current answer to the user, then run the naming/interface workshop one question at a time. Use `skill://craft-name` for the prefix discussion and present ten materially different, collision-checked candidates: `devflow-` (recommended), `codeflow-`, `engflow-`, `buildflow-`, `craftflow-`, `devcycle-`, `coding-`, `software-`, `shipflow-`, and `delivery-`. Recommend `devflow-` because it is short, clearly coding-workflow related, groups lexically, and avoids the active Grok bundled names `implement`, `review`, `code-review`, `design`, and `execute-plan`. Reject bare stage names and any full candidate stage set that collides with the live inventory.
2. Conclude and record one namespace convention before choosing stage labels:
   - Public manual stages: `<prefix><stage>`, for example `devflow-implement`.
   - Workflow-private support skills: `<prefix>core[-<capability>]`, for example `devflow-core`; the `core` segment is the stable "not intended as a user stage" marker because OMP and Grok still expose every discovered skill as an invocable command.
   - Shared capabilities: retain existing semantic names such as `eng-tdd` and `grilling`; they are dependencies of the workflow, not members of its private namespace.
3. Review the provisional five-stage public interface with the user: `shape`, `plan`, `implement`, `review`, `finish`. Recommend this set because it keeps the visible interface at five commands while `shape` dynamically handles both the prior S1a brainstorming branch and S1b existing-spec iteration branch. Discuss additions/removals only against a concrete entry condition and unique output; do not add a public stage that is only an alias for an existing stage mode.
4. Conclude the exact stage contract in a single decision table before authoring files. Each public stage row must contain: final command name; exact frontmatter description (≤1024 characters); manual/model activation flag; user-visible purpose; accepted inputs; branch/skip conditions; required and optional underlying skills; durable output; temporary output and deletion point; exit criterion; next recommended stage; and failure/escalation behavior. The recommended branch contract is:
   - `shape`: idea/no spec → `grilling`, codebase exploration, and `domain-modeling` only when durable terms/decisions change; existing spec → spec-iteration against code/contracts; runnable or visual uncertainty → explicit `eng-prototype` detour with deletion after the decision is captured; decision-complete input → recommend `plan` without re-interviewing.
   - `plan`: turn the approved shape/spec into one execution plan; use existing plan rules, `eng-codebase-design` for seam/interface decisions, and tracer-bullet tasks with blocking edges only when work genuinely spans independent sessions.
   - `implement`: execute the accepted plan/task frontier; invoke `eng-diagnosing-bugs` before implementation for an unreproduced bug and `eng-tdd` at agreed observable seams for behavior changes; stop with fresh focused proof and recommend `review`.
   - `review`: pin the comparison base and originating requirement, then review separate Spec/intent and Standards/quality axes plus direct behavioral verification; keep findings severitized and evidence-backed, and never silently widen into shipping.
   - `finish`: resolve or explicitly triage review findings, update an existing canonical contract only when the change altered the concern it owns, remove temporary prototypes/scratch/evaluation artifacts, run final fresh verification, and prepare a focused commit/PR; commit, push, history rewrite, or PR creation remains user-approved.
5. Conclude the artifact policy in the same workshop. Default to project-native locations and tracker conventions when declared; otherwise use `.agents/specs/YYYY-MM-DD-HHMM_<slug>.md` only for a spec that must survive the current session, the repository's plan contract for implementation plans, conversation/PR comments for review findings unless persistence is requested, and tagged `.scratch/<slug>/` or OS-temp paths for disposable work. Atlas stores research about this workflow, never project implementation specs or transient coding work.
6. Persist the accepted namespace, exact public stage set, stage decision table, artifact policy, and source-derived rationale into the Atlas topic with one dated `vault-only` decision pass. This accepted table—not the provisional names above—is the sole authoring input for T4. Do not create skill directories until the user has explicitly accepted the table.

### T4. Author thin stage skills and support core

1. Use `skill://craft-skill`. Create one directory per accepted public stage directly under `/Users/kim/.dotfiles/.config/agents/skills/`, plus one workflow-private core directory following the accepted convention. Under the recommended default this is:

   ```text
   /Users/kim/.dotfiles/.config/agents/skills/
   ├── devflow-shape/SKILL.md
   ├── devflow-plan/SKILL.md
   ├── devflow-implement/SKILL.md
   ├── devflow-review/SKILL.md
   ├── devflow-finish/SKILL.md
   └── devflow-core/
       ├── SKILL.md
       ├── references/
       │   ├── shape.md
       │   ├── plan.md
       │   ├── implement.md
       │   ├── review.md
       │   └── finish.md
       └── evals/evals.json
   ```

   If T3 changes names or stage count, substitute the accepted table one-for-one; do not keep aliases for provisional names.
2. Give every public `SKILL.md` minimal frontmatter: exact directory-matching `name`, a description that starts with the stage outcome and enumerates each accepted input branch, and `disable-model-invocation: true` so it is an explicit user stage. Its body must be a thin transport: read `skill://<accepted-prefix>core`, read the assigned stage reference, pass the user's arguments/current conversation/current repository artifacts, and execute that reference. Do not duplicate procedures or routing tables in wrappers.
   Under the default interface, start from these exact descriptions and revise them only through the T3 user decision:

   ```text
   devflow-shape: Shape coding work into decision-complete input for planning. Use only when the user invokes /devflow-shape to brainstorm a new coding idea, iterate an existing code spec, or decide whether research or prototyping is needed.
   devflow-plan: Turn approved coding requirements into an executable plan. Use only when the user invokes /devflow-plan with an accepted idea, spec, issue, or conversation that is ready for implementation planning.
   devflow-implement: Implement accepted coding work with focused behavioral proof. Use only when the user invokes /devflow-implement with an approved plan, agent-ready ticket, or explicitly bounded task.
   devflow-review: Review coding changes against their requirements, repository standards, and fresh behavioral evidence. Use only when the user invokes /devflow-review with a working-tree, branch, commit-range, or PR target.
   devflow-finish: Finish reviewed coding work by triaging findings, updating owned durable contracts, cleaning temporary artifacts, and running final verification. Use only when the user invokes /devflow-finish after implementation or review.
   ```

   Use this exact wrapper body shape, substituting only the accepted names and stage:

   ```markdown
   Read `skill://devflow-core` and `skill://devflow-core/references/<stage>.md`.
   Execute the `<stage>` stage with the user's arguments, current conversation, repository context, and supplied artifacts. Return the standard stage handoff.
   ```
3. Make the support skill the single workflow contract and set `disable-model-invocation: true` because only a public wrapper should load it. Add `metadata.sources: "mattpocock/skills; obra/superpowers; cursor/plugins"` for provenance without claiming those projects own this adaptation. Under the default interface, use this exact description: `Support-only orchestration for devflow stages. Read only when a devflow wrapper invokes it. Shape routes ideas and specs to grilling, domain modeling, or prototyping; plan uses codebase design and plan contracts; implement uses diagnosis for unreproduced bugs and TDD for behavior changes; review checks requirements, standards, and behavior; finish owns findings, durable contracts, cleanup, and completion evidence.` Its body owns only the ordered stage graph, shared artifact vocabulary, transition/skip semantics, evidence-before-claims rule, and a dispatch table from stage to reference/underlying skills. Put stage-specific checklists in the five references so loading one stage does not load every stage's procedure.
4. Encode these cross-stage invariants exactly once in the core: explore discoverable facts before asking; user settles preferences; no implementation before an accepted spec/plan when one is required; one tracer-bullet behavior at a time; review uses a pinned base and requirement source; finish cannot claim completion without fresh checks; temporary artifacts carry an owner and deletion stage; canonical contracts update only for durable decisions they already own; no automatic commit/push/PR/destructive git operation. Standardize every stage handoff on these exact fields: `Stage`, `Mode`, `Inputs`, `Invoked skills`, `Durable artifacts`, `Temporary artifacts / cleanup owner`, `Checks`, `Exit criterion`, and `Next stage`.
5. Give each stage reference the following ordered procedure; the accepted T3 table may rename/remove a stage but may not leave its behavior implicit:
   - `shape.md`: classify `new idea`, `existing spec`, or `decision-complete`; inspect the applicable code and declared canonical contracts before questions; invoke `grilling` one question at a time for unresolved preferences; invoke `domain-modeling` only when a domain term or hard-to-reverse decision actually changes; invoke `eng-prototype` only for a runnable/visual question and create a named cleanup owner before prototyping; write a durable spec only when the result must cross sessions; self-check contradictions/placeholders; obtain user acceptance; return the accepted artifact and `plan`. Empty intent asks one purpose/success question; discoverable unknowns are researched, not asked.
   - `plan.md`: read the accepted input and repository plan/canonical contracts; halt back to `shape` if requirements still contain a user decision; inspect existing implementations, exported-symbol callers, tests, and project commands; use `eng-codebase-design` only for a real seam/interface decision; emit the repository/harness-standard execution plan with vertical tasks and observable checks; add blocking edges only for genuine dependencies and ticketize only when the accepted work exceeds one session; self-review requirement coverage and placeholders; after confirming all load-bearing decisions were copied, delete any shaping notes/handoff explicitly marked temporary while retaining approved durable specs; return the plan path and `implement`. Missing tracker configuration falls back to the repository plan artifact, never to an invented tracker.
   - `implement.md`: require an accepted plan/task or an explicitly bounded direct task; preserve unrelated work; for a bug without a red-capable reproduction invoke `eng-diagnosing-bugs` before editing; for behavior changes invoke `eng-tdd` at the plan's agreed public seam and record each red→green slice; for docs/config/generated changes where a failing automated test cannot express the behavior, state the exception and run the smallest behavioral smoke check; verify each task before advancing; stop on an unresolved user decision or failed specified check; return changed behavior, exact evidence, remaining plan state, and `review`. Do not review, commit, push, or perform finish-stage housekeeping here.
   - `review.md`: resolve the target and fixed point from the working tree/branch/PR before reading the diff; resolve the originating spec/issue/plan and repository standards/canonical contracts; review `Spec / intent` and `Standards / quality` as separate axes, adding correctness/security/regression findings under the axis whose contract they violate; run the smallest direct behavior check capable of falsifying the claimed change; use independent parallel reviewers only when the host policy/user permits and the diff warrants isolation; report `Blocker`, `Important`, and `Note` findings with file/anchor, violated requirement, evidence, and remediation; if no spec exists, mark only the Spec axis `INCONCLUSIVE` and continue the other axis. Default is read-only; return findings plus `finish`, or `implement` when a blocker requires code changes.
   - `finish.md`: require implementation evidence and review findings, or record the user's explicit review skip; send unresolved blockers back to `implement`, require explicit disposition for important findings, and record notes as accepted/deferred/dismissed with reasons; apply `canonical-project-contracts` and update only existing owners of changed durable concerns; update required docs/changelog only after behavior works; delete every temporary artifact named by prior stage handoffs; run the full relevant final verification fresh and read its output; report actual status, remaining risks, and a proposed focused commit/PR description. Ask before commit, push, PR creation, history rewrite, deploy, credential use, or destructive cleanup outside workflow-owned temporary paths.
6. Reuse the local skills from T2 by exact `skill://` reference. Add a new reusable skill only if the accepted stage table contains procedure not owned by the core references or any existing skill; name it `<accepted-prefix>core-<capability>`, give it a distinct discovery description, and add a positive plus near-miss eval. Do not rename existing `eng-*`, `grilling`, or `domain-modeling` skills and do not create command-file copies.
7. Create `devflow-core/evals/evals.json` (or the accepted equivalent) in the existing `craft-skill/evals/evals.json` shape. Assertions test the standard handoff fields, not exact prose. Include these stable cases, renaming only accepted command labels:
   1. New feature idea with unresolved UX choice → `shape/new-idea`, `grilling`, no implementation, next `shape` until accepted.
   2. Existing code spec with two ambiguous requirements → `shape/spec-iteration`, code/contract inspection before questions, next `plan` only after acceptance.
   3. Decision-complete spec → `shape/decision-complete`, no redundant interview, next `plan`.
   4. State/UI question requiring a runnable answer → `shape/prototype-detour`, `eng-prototype`, named temporary path/cleanup owner, then return to `shape`.
   5. Plan input with an unresolved user preference → halt to `shape`; no plan artifact.
   6. Accepted multi-session spec with two independent slices and one dependent integration → `plan/multi-session`, tracer-bullet tasks with exact blocking edges.
   7. Accepted behavior task → `implement/feature`, `eng-tdd`, red→green evidence, next `review`.
   8. Bug report without a red-capable reproduction → `implement/bug-diagnosis`, `eng-diagnosing-bugs` before edits.
   9. Configuration-only task with no meaningful failing test → `implement/non-tdd-exception`, stated reason plus focused smoke check.
   10. Working-tree review with fixed point and spec → separate Spec and Standards axes plus direct verification.
   11. Review with no requirement source → Spec `INCONCLUSIVE`, Standards and behavior still run; no invented spec.
   12. Finish with an unresolved blocker → return to `implement`; no completion claim or shipping action.
   13. Finish with no canonical contract and one owned scratch artifact → no contract creation, scratch deletion, fresh final check, proposed—not executed—commit/PR.
   14. Natural-language near miss such as “explain TDD” without a stage invocation → no claim that a manual `devflow-*` stage auto-ran.


### T5. Evaluate invocation, behavior, transitions, and cleanup

1. Verify discovery before behavior. From `/Users/kim/Desktop/ng3/atlas/app`, run `grok inspect --json` and assert with `jq -e` that the accepted public names and core name appear exactly once, resolve to the authored `SKILL.md` files through the active agent-config bridge, and do not shadow a bundled skill. Under the recommended default, the expected sorted set is exactly `devflow-core`, `devflow-finish`, `devflow-implement`, `devflow-plan`, `devflow-review`, and `devflow-shape`.
2. Verify OMP resolution independently with `omp read skill://<name>` for every accepted public stage and `omp read skill://<accepted-prefix>core/references/<stage>.md` for every stage reference. A missing URI, wrong directory/frontmatter name, or collision is a failure even if Grok discovers a copy elsewhere.
3. Run every durable case in `<accepted-prefix>core/evals/evals.json` against a fresh session. Use read-only routing runs first:

   ```bash
   omp -p --no-session --tools read \
     --skills '<accepted-prefix>*,eng-*,grilling,domain-modeling,craft-skill' \
     --cwd /tmp --max-time 120 \
     'Read skill://<public-stage>. In analysis-only mode, route this eval case and report: Stage, Mode, Required skills, Optional skills, Durable artifact, Temporary artifact and cleanup owner, Exit criterion, Next stage. Do not write files.'
   ```

   For each case, compare those fields with the JSON assertions. Positive cases must select the intended branch; near misses must not claim that a manual public stage was automatically invoked; missing inputs must produce the specified question or halt rather than inventing a spec, fixed point, test seam, or verification result.
4. Exercise the workflow end to end in one disposable repository at `/tmp/devflow-e2e-<timestamp>/` (substitute the accepted prefix in prompts). Create a baseline Python module and `unittest` suite, initialize one local baseline commit with repository-local test identity, and supply a decision-complete spec to add one observable `slugify(value: str) -> str` behavior: lowercase ASCII text, trim outer separators, collapse runs of spaces/hyphens to one hyphen, and return `\"\"` for empty/all-separator input. The expected stage evidence is:
   Use these exact baseline files so the evaluator makes no fixture-design choice:

   ```python
   # text_tools.py
   def slugify(value: str) -> str:
       return value
   ```

   ```python
   # tests/test_text_tools.py
   import unittest

   from text_tools import slugify


   class SlugifyTests(unittest.TestCase):
       def test_keeps_plain_ascii_word(self):
           self.assertEqual(slugify("word"), "word")


   if __name__ == "__main__":
       unittest.main()
   ```

   Store the behavior paragraph from step 4 as `SPEC.md`. Run the baseline suite, then create the fixed point with `git init -b main`, `git add text_tools.py tests/test_text_tools.py SPEC.md`, and `git -c user.name='Devflow Eval' -c user.email='devflow@example.invalid' commit -m 'test: establish devflow fixture'`. During `implement`, add separate examples for `Hello World → hello-world`, `--Hello   World-- → hello-world`, `A---B → a-b`, and ` ---  → \"\"`; the first new example must be observed failing against the baseline implementation before production edits.
   - `shape` selects existing-spec/decision-complete mode without restarting brainstorming and recommends `plan`.
   - `plan` creates one vertical-slice task with the public function as the test seam and the exact command `python3 -m unittest discover -s tests -v`.
   - `implement` records the focused test failing for missing behavior before implementation, then passing after the minimal implementation; configuration-only/TDD exceptions are not applicable.
   - `review` pins the baseline commit and the spec, reports Spec and Standards separately, and directly reruns the behavior command; no issue is reported merely because the fixture is small.
   - `finish` has no existing canonical contract to update, removes its owned scratch/review artifacts, reruns the full fixture suite, reports remaining findings truthfully, and does not commit, push, or open a PR without an explicit instruction.
5. Run the fixture command once more after `finish`; expected output is all tests passing with no warnings. Confirm the fixture contains no prototype, `.scratch/`, review report, debug log, or generated handoff that was marked temporary. Then run `rm -rf -- /tmp/devflow-e2e-<timestamp>` using the exact workflow-owned path created in step 4 and verify that path no longer exists; the fixture and its git history are verification-only and must not enter the dotfiles repository or Atlas.
6. Run one Grok transport smoke test for an accepted public stage using its native `/<skill-name>` invocation and one OMP interactive smoke test using `/skill:<skill-name>`, each with a no-write routing prompt. Confirm the wrapper receives arguments and loads the same core reference; filesystem presence alone is not transport proof.

### T6. Review final workflow and update durable contracts

1. Audit the authored workflow against the accepted Atlas decision table and `skill://craft-skill`: every public stage has one unique entry condition/output, wrappers contain no duplicated checklist, the core/reference links resolve, every underlying skill invocation is conditional and explicit, and descriptions distinguish positive triggers from near misses. Remove any wrapper or helper that fails the deletion test instead of preserving a shallow alias.
2. Review the final dotfiles changes for accidental edits, duplicate skill names, copied third-party prose without the required MIT notice, machine-local paths inside portable skill bodies, stale provisional names, automatic git/deploy behavior, and unowned temporary artifacts. Fix findings and rerun the affected T5 checks.
3. Apply `rule://canonical-project-contracts` to the dotfiles repository. Update an existing canonical contract only if this implementation changes a durable concern that document already owns; do not create a new architecture/domain/design document merely to describe the workflow, and do not add specialty workflow detail to foundational `AGENTS.md`. The workflow's durable design record remains the Atlas topic.
4. Run `/atlas-research --vault-only` for a final implementation pass that updates the topic's current answer with the accepted public commands, private naming convention, stage graph, exact artifact lifecycle, implemented file paths, evaluation evidence, attribution posture, and any rejected source patterns. Link the initial comparison pass and the user-decision pass; do not cite local eval output as external source evidence.
5. From `/Users/kim/Desktop/ng3/atlas/app`, run `python3 scripts/atlas-instance.py check`; expected result is exit 0 after all Atlas writes. Re-run the exact Grok inventory assertion and OMP `skill://` reads from T5 after any final edits.
6. Mark T1–T6 complete with timestamps only after every verification criterion below is observed, set the plan status to `DONE`, and append a completion summary containing the final names, Atlas topic/pass paths, files authored, source adaptations, checks and observed outcomes, and any residual portability limitation. Do not commit or push the dotfiles unless the user separately requests it.

## Critical files & anchors

- `omp://skills.md` — OMP discovery and transport contract: one-level skill directories, `skill://` resolution, and hidden/manual skills still receiving `/skill:<name>` commands.
- `vault://atlas/summaries/registry/TOPICS.md` — current registry containing the broader `agentic-harness-architecture` topic; create or resolve the narrower workflow topic through `/atlas-index`.
- `/Users/kim/.dotfiles/.config/agents/skills/grill-with-docs/SKILL.md` — existing seven-line manual thin-wrapper pattern to preserve rather than replacing with copied procedure.
- `/Users/kim/.dotfiles/.config/agents/skills/eng-tdd/SKILL.md` — existing observable-seam and vertical-slice implementation discipline to compose.
- `/Users/kim/.dotfiles/.config/agents/skills/craft-skill/SKILL.md` — frontmatter, thin-orchestrator, reference, eval, transport, and cleanup rules for the authored skills.

## Verification

- [ ] Atlas topic creation and evidence: `ai-coding-workflow` (or the conflict-resolved equivalent recorded in T1) has the three repository-root artifacts, immutable artifacts for every compared skill page, route provenance, an initial comparison pass, an accepted user-decision pass, and a final implementation pass. `/atlas-answer` returns the topic only in `current` state.
- [ ] Atlas integrity: from `/Users/kim/Desktop/ng3/atlas/app`, `python3 scripts/atlas-instance.py check` exits 0 after all topic/registry writes.
- [ ] Grok discovery: from `/Users/kim/Desktop/ng3/atlas/app`, the following default-interface command exits 0; if T3 accepted different names, replace only the prefix and expected array with the accepted table:

  ```bash
  grok inspect --json | jq -e '
    ([.skills[] | select(.name | startswith("devflow-")) | .name] | sort)
    == ["devflow-core","devflow-finish","devflow-implement","devflow-plan","devflow-review","devflow-shape"]
  '
  ```

- [ ] OMP resolution: each of these default-interface commands returns the intended authored body/reference with no collision or missing-file error (substitute the accepted names when T3 overrides the default):

  ```bash
  omp read skill://devflow-shape
  omp read skill://devflow-plan
  omp read skill://devflow-implement
  omp read skill://devflow-review
  omp read skill://devflow-finish
  omp read skill://devflow-core
  omp read skill://devflow-core/references/shape.md
  omp read skill://devflow-core/references/plan.md
  omp read skill://devflow-core/references/implement.md
  omp read skill://devflow-core/references/review.md
  omp read skill://devflow-core/references/finish.md
  ```

- [ ] Routing evals: every case in the core's `evals/evals.json` produces the asserted stage mode, underlying skills, artifact ownership, exit criterion, and next stage; positive and near-miss cases are both exercised in fresh sessions.
- [ ] End-to-end behavior: the disposable `slugify` fixture records red-before-green evidence, then `python3 -m unittest discover -s tests -v` exits 0 after implementation and again after finish; shape skips redundant interviewing, review reports Spec and Standards separately, and finish performs no unauthorized commit/push/PR or canonical-contract creation.
- [ ] Native transport: one Grok `/<accepted-stage>` and one OMP `/skill:<accepted-stage>` no-write smoke invocation pass arguments to the same core reference and produce the same routing decision.
- [ ] Artifact hygiene: `/tmp/devflow-e2e-<timestamp>/` and all temporary prototypes, scratch files, review reports, debug logs, and handoffs created by evals are deleted; Atlas source/topic/pass artifacts and the core `evals/evals.json` remain because they are durable.
- [ ] Source and interface fidelity: the final skills match the accepted Atlas stage table one-for-one, reuse rather than duplicate existing local skills, contain no stale provisional names, and either use original wording or carry the complete applicable MIT notice for substantial retained text.

## Assumptions & contingencies

- The Atlas research belongs in a new `ai-coding-workflow` topic because the current `agentic-harness-architecture` topic covers broader harness architecture. If `/atlas-index` reports an equivalent existing topic or conflicting ID at execution time, update that exact topic instead of creating a duplicate and record the resolved topic path in every later task.
- `devflow-` plus five public stages (`shape`, `plan`, `implement`, `review`, `finish`) is the recommended default, not a hidden implementation choice. T3 intentionally gives the user the final decision; once accepted and persisted in Atlas, that table mechanically replaces the provisional names everywhere and no compatibility aliases remain.
- OMP registers `/skill:<name>` for discovered skills even when hidden, and Grok reports discovered skills as user-invocable. Therefore "non-surfacing" means support-only by contract and the `-core` naming marker, not invisibility in every command palette. Public stages and the support core use explicit parent/user invocation rather than `alwaysApply`.
- All three source repositories are MIT-licensed as of this plan: Matt Pocock (2026), Jesse Vincent/obra (2025), and Cursor (2026). The default is original wording with source provenance in Atlas; if execution retains a substantial source body/template, include that repository's complete license notice with the adapted skill.
- The target is the dotfiles source tree at `/Users/kim/.dotfiles/.config/agents/skills/`; active `~/.agents`, `.grok`, Cursor, or other harness views are transports/symlinks, not additional authoring copies. If a host fails to discover the source, repair the existing bridge rather than copying the workflow into another root.
- No existing dotfiles canonical contract was found that owns this specialty workflow. Unless execution discovers a newly applicable declared owner, T6 leaves foundational `AGENTS.md` and rules unchanged; durable workflow rationale lives in Atlas and executable procedure lives in the skills.
- The workshop's user-decision gates are required execution steps, not choices delegated to the implementer. T4 must not begin until the user either explicitly accepts the final stage table or explicitly authorizes the stated recommended defaults. Mere deferral is not acceptance; if neither authorization is given, pause at T3 rather than inventing or silently selecting another option.
