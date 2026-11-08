## Review rounds

| Step | Reviewer/event | Pass | Text | Outcome | Turn |
|---|---|---|---|---|---|
| 1 | A | post-rethink | 47c39b81 | accept · with notes<br>• Accepts the build order summary as written<br>• It matches the human's answers and keeps earlier decisions fixed<br>• Placing the quality check as stage 5 follows the human's 'after stage 4' answer<br>• Flags one conflict: an open prototype ticket would keep the map from resolving | 58 s · 11 tools · 259k tokens · wait 3 s |
| 2 | B | post-rethink | 47c39b81 | accept · with notes<br>• Accepts the summary after a second look: it matches the human's answers and earlier decisions<br>• Cutover, link, real-data, and the four new tickets follow the interview answers<br>• The extra quality-check stage is flagged as Main's placement and fits the human's answer | 61 s · 9 tools · 232k tokens · wait 3 s |
| 3 | B | later | 47c39b81 | edit<br>• An open prototype ticket would keep the map from returning to the spec route<br>• How that ticket is tracked once the map resolves is not stated<br>• The fix names the gap and leaves the choice to the human | 48 s · 3 tools · 212k tokens |
| 4 | A | later | 069027f1 | edit<br>• The open-ticket gap is real, but the fix offers an option the human already turned down<br>• Keeping the map open for the prototype is the rejected 'before the spec' option<br>• The human's answer means the prototype passes to the spec route as a stage-4 gate<br>• Also hands the spec route the choice of store for early smoke runs | 32 s · 1 tool · 63.7k tokens |
| 5 | B | later | c6ca6200 | accept<br>• Accepts the whole proposal: Summary, ticket 4, stages and Passed on agree<br>• Passing the summary-model ticket to the spec route fits the human's 'Before real data' answer<br>• The change list matches the difference from the original | 15 s · 1 tool · 82.3k tokens |
| 6 | apply | — | c6ca6200 | applied | — |
| 7 | cleanup | — | — | A, B disposed (observed exit) | — |

## Final proposal

**Proposal**

- **Summary**
  
  - Prerequisites met: dotagents v0.5.1 linked; dotfiles Reconcile and backup changes landed
  - Four new map tickets; the summary-model one passes to the spec route as a stage-4 gate
  - Stage 1 removes v1 in one commit and links the atlas plugin on g10
  - Eight stages, each ending in a smoke run; Atlas is first usable at stage 4
  - Real sources from stage 4, after the summary-model prototype; later schema changes migrate
  
  **Details**
  
  ## Decide Atlas build order
  
  ### 1. Prerequisites (met; nothing waits on dotfiles)
  
  - The Skill plugins release map is resolved; `dotagents` is published at v0.5.1 (checked 2026-11-08) and linked on g10.
  - The dotfiles tasks from the 2026-11-02 Handoff have landed: host-backup stages `~/.local/share/atlas/*.db` (`1e92343`); Reconcile marks reviewer changes and admits `atlas-ask` as a trusted caller with a `ready atlas-ask` check (`9ffc1e4`); the fixed pre-approval wording (`61b125d`); `init-ask` reads only dotagents' own settings (`fd49a85`).
  - So the ticket's constraint "the skill plugins ship before any Atlas release that relies on Reconcile" is met, and the ticket's "Also blocked by" no longer applies.
  
  ### 2. Decided on this map before the spec is written
  
  New tickets on the Atlas v2 map:
  
  1. **Decide source identity** (grilling): canonical link rules (for example X links with and without `s=<digits>`), the content hash, and Jev's near-duplicate flags. Before the spec, because stage 2's schema and stage 3's `add` depend on it. Graduates the map's open item on source identity.
  2. **Decide the quality check** (grilling): the form of the hand-run, read-only check (pooled Jev grading plus the user's spot check), including Jev's claim-support flags and whether claim labels and backing counts help. Its form is decided before the spec; it is built in stage 5. Graduates the map's open item on quality judging.
  3. **Decide Atlas plugin release** (grilling): tags, installing on the Mac, and any catalog entry. Before the spec. Atlas is its own plugin repo, so dotagents' export hook does not apply. Graduates the rest of the map's open item on linking and release; linking itself is settled below.
  4. **Prototype summary model quality vs cost** (prototype), as the human's quoted draft describes: Sonnet 5.5 at medium, Sonnet 5.5 at high and Opus 5.5 at medium summarize the same external sources from several topics, weighted towards code-related ones; quality, cost and time are measured per summary; if quality is about the same, the cheapest model wins. It changes only the `atlas_summarize` default, so the spec does not wait on it; it must resolve before real sources go in at stage 4. A map resolves only when every ticket is closed, so this ticket passes to the spec route as a stage-4 gate and the map closes without it; the human chose this timing over the option in which "the map stays open until it resolves" (Main: how the ticket is tracked there was not asked; see Passed on). Its own grilling decides how quality is judged.
  
  ### 3. Build stages
  
  One specification, then these stages in order. Each stage ends with a smoke run through the `atlas-ask` skill.
  
  1. **Cutover and plugin shell.** One commit deletes the v1 runtime, owners, scaffold, instance tooling, command stub, v1 `ARCHITECTURE.md`, v1 rules and tests. It keeps `atlas_url.py` and the CLI's JSON/exit handling and rewrites `AGENTS.md` for v2. The two blocked v1 plans (evaluation loop, topic creation) close as superseded. v1 stays at tag `v1`. The plugin shell is linked on g10 with `omp plugin link ~/dev/atlas`, so `skill://atlas-ask` and the bundled CLI path work from the first smoke run.
  2. **Store and plumbing.** The whole schema, `config.toml` profiles, the reply and exit seam, `status`, the omp-gateway and Jev clients, and `atlas-init` without its test search.
  3. **Sources in.** `add` and `inbox`.
  4. **First usable Atlas.** `find` and `ask` (query records, tally lines), plus `atlas-init`'s test search. Real sources start here, once the summary-model prototype has resolved. From the first real row, any schema change is a numbered migration (SQLite `user_version`); host-backup already covers the store.
  5. **Quality check**, in the form its ticket decides, so later tuning (abstract, rerank, answer prompts, claim labels) is measured. (Main: placed directly after stage 4, which renumbers the later stages.)
  6. **Notes and archive.** `note`, `archive`, `restore`.
  7. **Topics and research.** `topic`, `plan`, `find --wide`, and Reconcile in `atlas-ask` through the trusted-caller entry.
  8. **dev-research rule.** The `atlas-research` rule.
  
  ### Rejected alternatives
  
  - Building v2 beside v1 and removing v1 last: v1's rules and `AGENTS.md` keep loading into every build session.
  - CLI first, skills last: nothing is usable end to end until the end.
  - Real data with wipes allowed until v2 is complete: re-adding sources costs new summary calls. Real data only after the last stage: no real use for the whole build.
  - Linking at the end: the `realpath skill://atlas-ask` pattern stays untested.
  - Deciding source identity in the spec route: the spec would carry an open design question.
  - Building the quality check after the last stage, or leaving it out of v2: tuning during the build would be judged by smoke runs and spot checks only.
  - The summary-model prototype before the spec (delays the spec by one session) or with no ordering (early sources keep Opus-written summaries).
  - The release ticket during the build (the spec has a known gap) or out of scope (v2 runs only on g10).
  
  ### Passed on
  
  - To the new tickets above: their questions as written there.
  - To the spec route (`dev-ask`), after the map resolves: the summary-model prototype, as a gate before real sources go in at stage 4; how stages are cut into plans; which profile the stage 2 and 3 smoke runs use, so test rows stay out of the real store; and whether v1's ADRs 0001–0007 stay as history (Main: not asked).
  

**Changes**

- The Summary says the summary-model prototype passes to the spec route as a stage-4 gate
- The prototype ticket notes that a map resolves only when every ticket is closed
- Passed on gives the spec route the prototype gate and the store for early smoke runs
- Summary: 4 of 5 points unchanged · Details: edited

## Diff

```diff
--- original
+++ final
@@ -1,7 +1,7 @@
 **Summary**
 
 - Prerequisites met: dotagents v0.5.1 linked; dotfiles Reconcile and backup changes landed
-- Four new map tickets: source identity, quality check, release, summary model
+- Four new map tickets; the summary-model one passes to the spec route as a stage-4 gate
 - Stage 1 removes v1 in one commit and links the atlas plugin on g10
 - Eight stages, each ending in a smoke run; Atlas is first usable at stage 4
 - Real sources from stage 4, after the summary-model prototype; later schema changes migrate
@@ -23,7 +23,7 @@
 1. **Decide source identity** (grilling): canonical link rules (for example X links with and without `s=<digits>`), the content hash, and Jev's near-duplicate flags. Before the spec, because stage 2's schema and stage 3's `add` depend on it. Graduates the map's open item on source identity.
 2. **Decide the quality check** (grilling): the form of the hand-run, read-only check (pooled Jev grading plus the user's spot check), including Jev's claim-support flags and whether claim labels and backing counts help. Its form is decided before the spec; it is built in stage 5. Graduates the map's open item on quality judging.
 3. **Decide Atlas plugin release** (grilling): tags, installing on the Mac, and any catalog entry. Before the spec. Atlas is its own plugin repo, so dotagents' export hook does not apply. Graduates the rest of the map's open item on linking and release; linking itself is settled below.
-4. **Prototype summary model quality vs cost** (prototype), as the human's quoted draft describes: Sonnet 5.5 at medium, Sonnet 5.5 at high and Opus 5.5 at medium summarize the same external sources from several topics, weighted towards code-related ones; quality, cost and time are measured per summary; if quality is about the same, the cheapest model wins. It changes only the `atlas_summarize` default, so it does not block the spec; it must resolve before real sources go in at stage 4. Its own grilling decides how quality is judged.
+4. **Prototype summary model quality vs cost** (prototype), as the human's quoted draft describes: Sonnet 5.5 at medium, Sonnet 5.5 at high and Opus 5.5 at medium summarize the same external sources from several topics, weighted towards code-related ones; quality, cost and time are measured per summary; if quality is about the same, the cheapest model wins. It changes only the `atlas_summarize` default, so the spec does not wait on it; it must resolve before real sources go in at stage 4. A map resolves only when every ticket is closed, so this ticket passes to the spec route as a stage-4 gate and the map closes without it; the human chose this timing over the option in which "the map stays open until it resolves" (Main: how the ticket is tracked there was not asked; see Passed on). Its own grilling decides how quality is judged.
 
 ### 3. Build stages
 
@@ -52,4 +52,4 @@
 ### Passed on
 
 - To the new tickets above: their questions as written there.
-- To the spec route (`dev-ask`), after the map resolves: how stages are cut into plans, and whether v1's ADRs 0001–0007 stay as history (Main: not asked).
+- To the spec route (`dev-ask`), after the map resolves: the summary-model prototype, as a gate before real sources go in at stage 4; how stages are cut into plans; which profile the stage 2 and 3 smoke runs use, so test rows stay out of the real store; and whether v1's ADRs 0001–0007 stay as history (Main: not asked).
```

## Spend

| Reviewer | Model | Tokens | Cost |
|---|---|---|---|
| A | anthropic/claude-opus-5-5 · medium | 323,177 | 0.718893 USD |
| B | anthropic/claude-sonnet-5-5 · high | 526,400 | 0.513498 USD |
| Total | | 849,577 | 1.232391 USD |
