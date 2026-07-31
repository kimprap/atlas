# Robust OMP plan artifact synchronization and archival

**Datetime**: 2026-07-31-1718
**Scope**: OMP plan-mode artifact mirroring, repository plan identity, completion archiving, and the governing plan rules
**Summary**: Replace slug/mtime-based mirroring with stable plan identity derived from the session-local plan, preserve exact plan content across approve-and-execute session copies, and add an explicit atomic archive workflow with a lean tool map for agents.
**Status**: DONE

## Context

OMP plan approval can copy a `local://<slug>-plan.md` artifact into a fresh execution session, where later edits apply to the executor session’s copy rather than the planner session’s copy. The current `plan-artifact-sync.js` mirror finds repository targets by slug and newest mtime and rewrites `Datetime`, so copied sessions and repeated slugs can select or create the wrong repository record. The intended end state is one repository projection per plan identity, updated from either session copy without duplication, with completion archived only through an explicit proof-gated agent action.

## Tasks

- [x] T1. Replace the mirror helper with identity-based sync and archive operations
  completed 2026-07-31-2132
- [x] T2. Refactor the OMP extension and expose explicit plan archival
  completed 2026-07-31-2136
- [x] T3. Align the portable, repository, and OMP plan rules
  completed 2026-07-31-2136
- [x] T4. Prove copied-session convergence and archive behavior
  completed 2026-07-31-2251

## Approach

### T1. Replace the mirror helper with identity-based sync and archive operations

1. Replace the body of `/Users/kim/.dotfiles/bin/omp-copy-plan-artifact` with an executable Bun script while preserving its path. Bun is already the OMP extension runtime; using it removes shell-specific metadata parsing and keeps byte-preserving file operations, validation, and atomic rename behavior in one implementation.
2. Clean-cut the helper CLI to these two forms; update every caller in T2 and leave no compatibility parser for the current `--datetime` form:

   ```text
   omp-copy-plan-artifact sync --slug <slug> --content-file <path>
   omp-copy-plan-artifact archive --slug <slug> --content-file <path>
   ```

3. Add one metadata parser that reads the source as UTF-8 while retaining its original bytes for output. Require the first line to be the plan H1, and inspect only the metadata block between that H1 and the first `##` heading. In that block require exactly one canonical `**Datetime**: YYYY-MM-DD-HHMM` line; validate year `0001`–`9999`, real month/day including leap years, hour `00`–`23`, and minute `00`–`59`. Require the OMP kebab-case `<slug>` to match `[a-z0-9]+(?:-[a-z0-9]+)*`; do not lowercase or otherwise normalize it. For `archive`, also require exactly one `**Status**: DONE` line in that block. Empty/non-UTF-8 content, missing/duplicate/misplaced/invalid metadata, unsafe or noncanonical slugs, and non-regular source files exit nonzero before touching `.agents/plans/`.
4. Derive the sole identity and paths from source metadata, never time or directory scans:

   ```text
   plan id:       <Datetime>_<slug>
   active path:   .agents/plans/<plan-id>.md
   archive path:  .agents/plans/archive/<plan-id>.md
   ```

5. Before inspecting either repository path, acquire a cross-process per-identity lock at `<os.tmpdir()>/omp-plan-artifact-locks/<sha256(realpath(cwd) + NUL + plan-id)>.lock` using atomic directory creation. Write `owner.json` with the PID and creation time; on contention retry every 25 ms for at most 15 seconds. Reclaim a lock only when its recorded PID is no longer alive, or when its owner file is missing/malformed and the directory is older than one second; win reclamation by atomically renaming the lock directory to a unique tombstone before removal. Hold the lock from the first active/archive check through the final rename, release it in `finally`, and fail without repository mutation on timeout. This is the single concurrency boundary for all OMP processes.
6. For `sync`, while holding that lock, inspect only the exact active/archive paths and require any existing target to be a regular non-symlink file. Replace the sole existing target atomically from a uniquely created temporary file in the same directory; if neither exists, create the active target; if both exist, fail without modifying either. An archived plan therefore receives later appended overrides in place instead of being recreated as active.
7. For `archive`, validate `DONE`, acquire the same lock, then perform the final byte-exact sync and archive as one helper invocation: active-only is atomically replaced and renamed into `archive/`; archive-only is atomically replaced in place and reported already archived; neither creates the archive target directly; both fails without mutation. Keep stable success prefixes `plan-artifact-synced:`, `plan-artifact-archived:`, and `plan-artifact-already-archived:` for extension/tool output.

### T2. Refactor the OMP extension and expose explicit plan archival

1. In `/Users/kim/.dotfiles/.config/agents/harnesses/omp/extensions/plan-artifact-sync.js`, import and reuse `resolveLocalUrlToPath` from `@oh-my-pi/pi-coding-agent/internal-urls` with `ctx.localProtocolOptions`; do not reimplement OMP’s session-local root, containment, Windows-short-root, or fresh-session copy logic. The active installed SDK is `17.2.1` and exposes this subpath.
2. Delete `humanizeSlug`, `ensureRequiredPlanHeader`, `resolveMirrorDatetime`, `slugToDatetime`, the `date` subprocess, and all slug/mtime candidate scanning. Replace `Bun.spawn` and temporary content files with `pi.exec(script, [operation, "--slug", slug, "--content-file", sourcePath], {cwd})`, passing the actual resolved local plan file to T1.
3. Keep the extension stateless: every automatic sync and explicit archive awaits one helper invocation, and T1’s shared per-identity lock serializes the full repository transition across same-process and cross-process callers. Add no promise map, retries, lock state, or identity cache to the extension.
4. Keep one post-success `tool_result` listener:
   - `write` qualifies only when `event.input.path` is exactly `local://<slug>-plan.md`.
   - Default hashline `edit` does not reliably expose `details.path`; extract each exact `[local://<slug>-plan.md#<TAG>]` section header from `event.input.input` instead. Resolve only those logical URLs and deduplicate them. A working-tree path or replacement-body text that merely ends in `-plan.md` does not qualify.
   - Resolve each qualified URL through the current event context, reread the post-tool file, and invoke `sync`. Do not trust untyped result-detail paths and do not scan prior session directories. Catch automatic-sync failures, show one actionable warning, and leave the successful tool result unchanged.
5. Add one `before_agent_start` listener for the protocol-shaped approved execution prompt: require the prompt to begin `Plan approved.` and contain the exact instruction ``You MUST read `local://<slug>-plan.md` before executing.`` Resolve that URL through the current context and invoke `sync`. OMP `17.2.1` copies local artifacts and rewrites the reviewed plan into the fresh session before dispatching this event, while the copy itself emits no tool result; this hook reconciles review-overlay edits and the executor copy without guessing from `session_switch`. Warn and allow execution to continue if this non-authoritative projection fails.
6. Register one agent-callable tool with the exact surface:

   ```text
   archive_plan_artifact({slug: string})
   ```

   Set `loadMode: "essential"` so OMP `17.2.1` advertises the tool directly under that name instead of placing its default discoverable form behind `xd://`. Its description must say that it synchronizes and atomically archives the current session’s completed `local://<slug>-plan.md` only after the base completion contract is satisfied. Build its schema with the extension API’s injected `pi.zod`, validate the same slug pattern, resolve the source through `resolveLocalUrlToPath`, invoke T1’s `archive`, return the helper’s success text, and surface a nonzero helper result as a tool error. Do not infer archival from `Status: DONE`, `agent_end`, `session_stop`, or a session-switch event.
7. The approve-and-execute path therefore converges twice without cross-session state: `before_agent_start` synchronizes the copied approved content immediately, and later executor edits synchronize the same identity because the copy retains `Datetime` and slug. No cross-session symlink, prior-session scan, process-local identity registry, or approval-specific repository write is added.

### T3. Align the portable, repository, and OMP plan rules

1. Update `/Users/kim/.dotfiles/.config/agents/rules/plan.md` only with portable semantics: `Datetime` is immutable plan identity metadata after creation; harness copies/forks preserve the header; execution updates the authoritative harness artifact rather than a repository projection; later completion-summary overrides append without changing identity.
2. Update `/Users/kim/.dotfiles/.config/agents/rules/plan-repo-storage.md` with repository projection behavior owned by that companion: materialized `<Datetime>_<slug>.md` identity, byte-exact projection, exact active/archive lookup, archived-in-place override updates, fail-closed duplicate handling, per-identity serialization across writers, and explicit atomic archival only after the base `DONE` contract. State that adapters never select by slug plus newest mtime and never rewrite plan metadata.
3. Correct `/Users/kim/.dotfiles/.config/agents/skills/improve/references/plan-template.md:3,118` so `/improve` reads both contracts and assigns only lifecycle/content metadata to `plan.md`; filename, active/archive location, and archive mechanics belong to `plan-repo-storage.md`. Do not change the `/improve` skill or template shape.
4. Add the narrow description-only rule `/Users/kim/.dotfiles/.config/agents/rules/plan-omp-transport.md` instead of placing OMP tool names in the portable rules. Its operation map is:

   | Phase | Authoritative target | Agent mechanism |
   |---|---|---|
   | Draft/create | `local://<slug>-plan.md`, with canonical lowercase kebab-case slug | `write` |
   | Read/resume approved work | same `local://` artifact | `read` before execution |
   | Track execution | plan `## Tasks` codes | `todo`, with each completed item followed by the corresponding plan `edit` |
   | Incremental revision and completion record | same `local://` artifact | `edit`; verification itself uses only the plan’s named task-specific tools |
   | Review/approval | approved local slug | `write` to `xd://propose` |
   | Repository materialization, approved-copy reconciliation, and later sync | `.agents/plans/<Datetime>_<slug>.md` or its archived location | automatic `plan-artifact-sync`; never edit the projection directly while the local authority exists |
   | Completion archival | current completed local artifact | `archive_plan_artifact({slug})` after tasks, verification criteria, `Status: DONE`, and Completion Summary are present |

   Give the rule a concise `description` only—no `alwaysApply`, glob, condition, or TTSR metadata—and include positive activation for materialized OMP plans plus near misses for repository-native plans and non-plan Markdown.

### T4. Prove copied-session convergence and archive behavior

1. Add `/Users/kim/.dotfiles/.config/agents/harnesses/omp/extensions/plan-artifact-sync.test.js` using `bun:test`. Exercise the real helper through a fake extension API that captures `tool_result`/`before_agent_start` handlers and registered tools; use temporary cwd and two temporary OMP artifact roots rather than the user’s real `.agents/plans/`.
2. Cover helper contracts: metadata-derived filename, canonical lowercase slug enforcement without normalization, byte-exact output, real-calendar validation, invalid/duplicate/misplaced metadata rejection without writes, active/archive ambiguity rejection, non-`DONE` archive rejection, active-to-archive rename, idempotent archive refresh, and post-archive sync that updates only the archived path.
3. Cover the reported workflow end to end: emit a planner-session `write`; simulate a review-overlay update; copy the same local plan into a second artifact root; emit the approved `before_agent_start`; change the plan to `DONE` with completion evidence; emit the executor-session hashline `edit`; and assert that exactly one repository filename exists and contains the executor content. Invoke `archive_plan_artifact`, assert the active file disappeared and the same identity exists once under `archive/`, then emit a later executor edit and assert no active duplicate is recreated.
4. Add near-miss and concurrency coverage: a working-tree `<slug>-plan.md` edit and non-approved prompt are ignored; two distinct `Datetime` values with the same slug create two legitimate identities. For the cross-process regression, create the helper’s computed lock directory with the live test PID, start real `sync` and `archive` child processes against the same `DONE` source and active identity, release the gate lock after both are waiting, and assert both finish with exactly one archived file and no active duplicate. Also verify dead-owner reclamation and live-owner timeout leave no partial repository file.

## Critical files & anchors

- `/Users/kim/.dotfiles/.config/agents/harnesses/omp/extensions/plan-artifact-sync.js` — `tool_result`/`before_agent_start` reconciliation and essential `archive_plan_artifact`.
- `/Users/kim/.dotfiles/bin/omp-copy-plan-artifact` — sole owner of metadata validation, cross-process serialization, identity-to-path resolution, atomic sync, and atomic archive.
- `/Users/kim/.dotfiles/.config/agents/rules/plan.md` plus `plan-repo-storage.md` — portable lifecycle versus repository materialization/archive ownership.
- `/Users/kim/.dotfiles/.config/agents/rules/plan-omp-transport.md` — OMP-only tool/transport map; new because no existing harness shim owns this seam.
- `/Users/kim/.dotfiles/.config/agents/skills/improve/references/plan-template.md` — adjacent caller with currently incorrect ownership guidance.

## Verification / Done criteria

- [x] From `/Users/kim/.dotfiles`, `bun test ./.config/agents/harnesses/omp/extensions/plan-artifact-sync.test.js` exits `0`; its assertions cover copied planner/executor convergence, review-overlay reconciliation, direct essential-tool archival, archived-in-place later overrides, fail-closed validation, and overlapping cross-process sync/archive with no duplicate.
- [x] A direct CLI smoke in a temporary cwd creates a byte-identical `.agents/plans/2026-07-31-1718_demo.md` from a `local/demo-plan.md` containing `**Datetime**: 2026-07-31-1718`, then `archive` against the contract-complete `**Status**: DONE` source leaves no active file and one byte-identical archive file. The temporary cwd and lock artifacts are removed after observation; the Atlas repository and live OMP session are not used as fixtures.
- [x] In a fresh OMP session, `rule://plan-omp-transport` resolves as a rulebook rule and its positive OMP-plan request receives the operation map; a fresh unrelated non-plan request does not activate it.
- [x] In a disposable repository and fresh OMP session, `archive_plan_artifact({slug: "demo"})` is available directly, rejects a non-`DONE` local fixture without creating a repository plan, then returns `plan-artifact-archived:` for the completed fixture and leaves exactly one archived identity.

## Assumptions & contingencies

- Repository mirroring remains enabled because it provides durable workspace discovery beyond a session-local OMP artifact; `local://` remains authoritative for a harness-originated plan even after its repository projection is archived.
- Archived projections are not immutable snapshots: a later, explicitly appended plan override from the same authoritative local artifact updates the exact archived identity in place and never recreates an active duplicate. This preserves one current durable record and the existing historical text inside it.
- Archival is not inferred merely from observing `Status: DONE`; the executing agent invokes the explicit archive action only after the plan contract’s task, verification, and completion-summary requirements are satisfied. The helper independently requires the canonical `DONE` metadata as a fail-safe, not as authority to trigger the transition.
- The implementation targets the active OMP SDK `17.2.1`. If `@oh-my-pi/pi-coding-agent/internal-urls` or `ctx.localProtocolOptions` is unavailable at execution time, stop rather than reconstructing `local://` paths or scanning session directories.
- The helper lock serializes the complete active/archive decision and mutation across OMP processes. Concurrent syncs are last-lock-holder-wins at the one exact location; concurrent sync/archive operations end archive-only regardless of acquisition order because each caller rechecks location after acquiring the same lock.

## Completion Summary

- Replaced slug/mtime mirroring with metadata-derived identity, byte-exact atomic sync, explicit archive states, and per-identity cross-process recovery serialization.
- Added the essential `archive_plan_artifact` tool, copied-session reconciliation, OMP transport guidance, and aligned portable/repository plan ownership.
- Verified with the targeted Bun suite (`9 pass`, `68 expectations`), direct archive smoke, fresh OMP rule-map and runtime-tool probes, and an independent final review (`APPROVED`) of helper SHA-256 `564abf2c33907f1e577e5a1136a0085e9a28c4530a9add7e59d65fcc639cc7e3`.
- Bun `1.3.14` treats a bare hidden-path test argument as a filter; the criterion records the equivalent explicit path form `./.config/...`, which passed.
