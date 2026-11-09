## Review rounds

| Step | Reviewer/event | Pass | Text | Outcome | Turn |
|---|---|---|---|---|---|
| 1 | A | post-rethink | ae5d006f | edit<br>• The proposal matches the human's answers and the earlier decisions, with one gap<br>• It drops the chosen promise of no extra commits and no background writes to the repo<br>• It never says where the background run makes and pushes the tag; that goes to the spec route | 68 s · 14 tools · 425k tokens · wait 3 s |
| 2 | B | post-rethink | ae5d006f | edit · superseded<br>• Retry rule narrows the human's answer; a failed run can leave shipped changes untagged<br>• Two tag-visibility gaps for status are missing from the passed-on list | 117 s · 17 tools · 524k tokens · wait 3 s |
| 3 | B | later | d2221f89 | edit<br>• The no-background-writes sentence is right, but the retry rule still narrows the human's answer<br>• A failed run can leave shipped changes untagged until the next shipped change<br>• Passed on still lacks which tag is current when HEAD is past the last tag | 32 s · 2 tools · 187k tokens |
| 4 | A | later | 8d60ac5e | accept<br>• Accepts the proposal as changed by both reviewers<br>• Retry, tag placement and current-tag questions now match the human's answers<br>• The change list matches the difference from the original | 10 s · 1 tool · 79.6k tokens |
| 5 | apply | — | 8d60ac5e | applied | — |
| 6 | cleanup | — | — | A, B disposed (observed exit) | — |

## Final proposal

**Proposal**

- **Summary**
  
  - Atlas v2 runs on g10 only, through the link; a Mac install comes with the hosted store.
  - Auto tag per plugin-changing push: a background run tests, then tags; the push never waits.
  - Tags v2.0.0, patch per tag, minor per store migration; the tag is the version.
  - Tag message + GitHub Release; omp exact, dotagents by identity; warn, never block.
  - No catalog or upgrade mechanism; stage 1 adds package.json, hook and release script.
  
  **Details**
  
  ### 1. Where Atlas runs
  
  1. v2 runs only on g10, through `omp plugin link ~/dev/atlas` (stage 1). The Mac does not install it; it uses Atlas by working on g10, so there is one library. A Mac install comes with the hosted store adapter, after v2.
  2. The plugin stays installable. Stage 1's `package.json` has `name: atlas`, version `2.0.0` and the `omp` field. One git install of `github:kimprap/atlas` in a throwaway home is proven in stage 1, after the first tag (Main: the stage).
  3. No upgrade mechanism in v2, because the link is live. No sync extension, so the architecture's "no omp extension" still holds (Main).
  4. No marketplace catalog.
  
  ### 2. Tags
  
  5. Atlas tags automatically per push, built in stage 1 with the plugin shell.
  6. How it runs:
     - `.githooks/pre-push` in `kimprap/atlas` starts a detached run, so the push never waits.
     - After the push exits, and only if `origin/main` is the pushed commit, the run executes Atlas's Python tests and `check_skills` on that commit. It tags only if both pass.
     - Passes are cached by an input hash. The run uses nice 19 and one lock, and `notify` reports the outcome. A failure skips the tag, and the next push retries.
     - The release script and hook live in the Atlas repo, and a repo setup task sets `core.hooksPath`. dotfiles stays unaware of Atlas.
  7. A push gets a tag only when the shipped plugin files (skills, rules, CLI, `package.json`) at the pushed commit differ from the latest tag. Pushes touching only docs, `.scratch` or tests add no shipped change, so they get no tag on their own. After a failed run, the next push still tags the shipped changes left untagged.
  8. The first tag is `v2.0.0`. Each tag bumps the patch, and the minor bumps when the push adds a store migration (SQLite `user_version`). So rolling back across a minor means the store is newer than the code.
  9. The tag is the version. `package.json` stays at `2.0.0` and changes only by hand. `status` shows `git describe` when Atlas runs from a checkout. Matching `package.json` to tags comes back when other machines install. No extra commits and no background writes to `~/dev/atlas`.
  10. Each tag is annotated. Its message lists the commit subjects since the last tag, the exact omp version, and dotagents' identity: the dotfiles commit when linked, the version when installed. A GitHub Release is created from it. There is no CHANGELOG file.
  
  ### 3. Compatibility
  
  11. Atlas warns and never blocks. `status` warns when omp differs from the version recorded on the current tag. dotagents problems already surface through Reconcile's `ready atlas-ask` check and the "not cross-checked" fallback.
  
  ### Changes to earlier decisions
  
  - [Decide Atlas build order](07-decide-atlas-build-order.md), stage 1 also adds `package.json`, the release script, the pre-push hook and its setup task, and the throwaway-home git install smoke.
  - [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md), `status` also shows the Atlas version and warns on an omp mismatch.
  
  ### Rejected alternatives
  
  - Mac install with its own store: a second library that drifts, and re-adding sources costs summary calls again. Mac reaching g10's store: needs the remote adapter that the architecture puts after v2.
  - Hand tags at milestones or no tags: the human chose automatic tags per push. Patch-only numbers: rolling back would not show that the store is newer than the code.
  - Blocking pre-push checks: every push waits. Tagging every push: tags that change nothing Atlas runs.
  - Generalizing `dotagents.py`: dotfiles would have to know about Atlas. Building tagging at stage 4: stages 1–3 would have no rollback points.
  - Tag message only: no GitHub Release. A release commit per tag: local main lags one commit behind after every tag.
  - An exact omp pin that refuses to run: every omp update would stop Atlas. Recording omp only: a regression caused by dotagents would leave no trace.
  - A catalog entry: a catalog repo to maintain, for marketplace auto-update only.
  
  ### Passed on
  
  - To the spec route:
    - the exact list of shipped plugin paths;
    - how a push that adds a migration is detected;
    - how `check_skills` is reached from the Atlas repo;
    - the setup task's form;
    - where `status` reads the tag's omp version, which tags count (the repo already has `v1`), and which tag is current when HEAD is past the last tag;
    - where the background run makes and pushes the tag and keeps its cache, lock and log, given no background writes to `~/dev/atlas`;
    - what the throwaway-home install smoke covers when dotagents is absent there.
  - To the later effort that brings the hosted store: Mac install, an upgrade mechanism, `package.json` tracking tags, and which repo files a git install should ship.
  

**Changes**

- A push is tagged when shipped files differ from the latest tag; the next push retries
- Item 9 adds the human's no extra commits and no background writes to the checkout
- Passed on adds tag placement, run state, which tags count and which is current
- Summary: unchanged · Details: edited

## Diff

```diff
--- original
+++ final
@@ -21,11 +21,11 @@
 6. How it runs:
    - `.githooks/pre-push` in `kimprap/atlas` starts a detached run, so the push never waits.
    - After the push exits, and only if `origin/main` is the pushed commit, the run executes Atlas's Python tests and `check_skills` on that commit. It tags only if both pass.
-   - Passes are cached by an input hash. The run uses nice 19 and one lock, and `notify` reports the outcome. A failure skips the tag, and the next qualifying push retries.
+   - Passes are cached by an input hash. The run uses nice 19 and one lock, and `notify` reports the outcome. A failure skips the tag, and the next push retries.
    - The release script and hook live in the Atlas repo, and a repo setup task sets `core.hooksPath`. dotfiles stays unaware of Atlas.
-7. Only pushes that change shipped plugin files (skills, rules, CLI, `package.json`) get a tag. Pushes touching only docs, `.scratch` or tests do not.
+7. A push gets a tag only when the shipped plugin files (skills, rules, CLI, `package.json`) at the pushed commit differ from the latest tag. Pushes touching only docs, `.scratch` or tests add no shipped change, so they get no tag on their own. After a failed run, the next push still tags the shipped changes left untagged.
 8. The first tag is `v2.0.0`. Each tag bumps the patch, and the minor bumps when the push adds a store migration (SQLite `user_version`). So rolling back across a minor means the store is newer than the code.
-9. The tag is the version. `package.json` stays at `2.0.0` and changes only by hand. `status` shows `git describe` when Atlas runs from a checkout. Matching `package.json` to tags comes back when other machines install.
+9. The tag is the version. `package.json` stays at `2.0.0` and changes only by hand. `status` shows `git describe` when Atlas runs from a checkout. Matching `package.json` to tags comes back when other machines install. No extra commits and no background writes to `~/dev/atlas`.
 10. Each tag is annotated. Its message lists the commit subjects since the last tag, the exact omp version, and dotagents' identity: the dotfiles commit when linked, the version when installed. A GitHub Release is created from it. There is no CHANGELOG file.
 
 ### 3. Compatibility
@@ -54,6 +54,7 @@
   - how a push that adds a migration is detected;
   - how `check_skills` is reached from the Atlas repo;
   - the setup task's form;
-  - where `status` reads the tag's omp version;
+  - where `status` reads the tag's omp version, which tags count (the repo already has `v1`), and which tag is current when HEAD is past the last tag;
+  - where the background run makes and pushes the tag and keeps its cache, lock and log, given no background writes to `~/dev/atlas`;
   - what the throwaway-home install smoke covers when dotagents is absent there.
 - To the later effort that brings the hosted store: Mac install, an upgrade mechanism, `package.json` tracking tags, and which repo files a git install should ship.
```

## Spend

| Reviewer | Model | Tokens | Cost |
|---|---|---|---|
| A | anthropic/claude-opus-5-5 · medium | 504,620 | 0.830076 USD |
| B | anthropic/claude-sonnet-5-5 · high | 711,241 | 0.596911 USD |
| Total | | 1,215,861 | 1.426987 USD |
