## Backlog

- [ ] Build the bulk runner for large add batches #dev #bulk-runner
  - Start when: the user asks for it; it is the first deferred step after stage 8 (built as bd3974e) and the user defers it as far back as possible, so never start or propose it unasked
  - Source: spec .agents/artifacts/atlas-v2-spec.md section 6 'Bulk runner' (the user's request, 2026-11-12); session 01a1cec1-5da8-7749-890e-2e1a9b20698e (2026-11-12); moved from .agents/AGENTS.md and ARCHITECTURE.md on 2026-11-23
  - Outcome: a repo-only tool (never shipped) that carries the eval library build's and stage 9's hundreds of adds in lanes, time-boxed slices, a ledger under ~/.local/state/atlas/<profile>/bulk/, parked decisions and a GitHub token check; spec section 6 holds the behavior, its route settles names, file layout and tests.
  - Offline to build: no paid call. Goes through dev-ask as its own route.
- [ ] Build the eval library (AC-5.5) through the bulk runner #dev #quality #bulk-runner
  - Start when: the bulk runner card is Done, a GitHub token is set in the environment omp starts from, and the user asks for the build
  - Source: spec section 6 and AC-5.5; deferred by the user on 2026-11-10 and moved after stages 6 to 8 on 2026-11-11; session 01a1cec1-5da8-7749-890e-2e1a9b20698e (2026-11-12); moved from .agents/AGENTS.md and ARCHITECTURE.md on 2026-11-23
  - Paid: ask separately before the paid run (AGENTS.md). Run it as its own dev-ask route. The eval profile exists (~/.local/share/atlas/eval.db) and holds no source; the build has never run against a real read, model or judge call, so its first run may meet decisions or read failures the offline tests do not show.
  - Observed 2026-11-10: build-library printed about $72.10 at list price (about $0.14 per link) for 515 links, plus Jev calls on the OpenRouter key; the spec's $10 to 15 does not match it. Wall time estimated, not measured: 2 to 5 minutes per link serial, about 17 to 43 hours over several window stops, so run in slices. 288 links are github.com (191 repo roots needing GitHub's tree API) and 144 are x.com.
  - Judge the build by the dropped list on stderr: many repo roots dropped as 'unreadable: error' probably mean no token was set; take any high u to the user. The bulk runner replaces build-library's own add loop, so its commands and stops change with it (spec section 6 'Users').
  - GitHub token, the user's steps: create a fine-grained personal access token with read-only access to public repositories, export it as GITHUB_TOKEN in the environment omp starts from (quality.py's shell inherits it from omp), and start omp from there. Agents never create, read or store the token.
- [ ] Decide from the summary lane whether atlas-rethink stays #dev #quality
  - Start when: the eval library card is Done and the user asks for the summary-lane comparison
  - Source: spec section 4.15 (the atlas-rethink rule, fixed before the first run); ticket 16 section 5; the revisit condition of the retired skills/atlas-ask/prompts/MAINTENANCE.md, removed on 2026-11-23
  - Rule: atlas-rethink stays only if, across 3 runs, faithfulness or completeness is better and neither is worse; any other result (level, mixed, worse) removes it. Cost and time inform the user only. Paid: quality.py run makes model and judge calls.
  - Record the outcome as a verdict line under .agents/verdicts/skills-atlas-ask-prompts-atlas-rethink-md.md, which holds the Taken line for the lens.
- [ ] Bring the v1 vault's sources into main (stage 9) #dev #v1-import #bulk-runner
  - Start when: the eval library card is Done, a GitHub token is set, and the user asks for stage 9
  - Source: spec section 6 stage 9 row and section 5 compatibility line (the user's requests, 2026-11-11 and 2026-11-12); session 01a1cec1-5da8-7749-890e-2e1a9b20698e (2026-11-12); moved from .agents/AGENTS.md and ARCHITECTURE.md on 2026-11-23
  - Each link summarized once: copy the eval library's source records into main with no model call, add only the v1 links the library lacks, then add --reread the copies; the adds and re-reads go through the bulk runner. Scope, cost and acceptance are left to its own route (spec section 12).
  - Paid, and writes the real main store: ask separately before both. The frozen v1 vault is read only, for its links. After it, the user creates the first real topics.
- [ ] Check the 0.3 marks threshold on main's first real topics (AC-7.4) #dev #topics
  - Start when: real topics on main have marks and at least one catch-up answer (after stage 9), and the user asks
  - Source: spec AC-7.4 and section 4.12; deferred by the user on 2026-11-11; session 01a1cec1-5da8-7749-890e-2e1a9b20698e (2026-11-12); moved from .agents/AGENTS.md and ARCHITECTURE.md on 2026-11-23
  - Command: python3 tools/quality/quality.py marks-report --profile main (read-only, no call, writes nothing). The user reads the rows and keeps 0.3 or changes it; a change is a spec 4.12 amendment, then MARK_AT in atlas/core/marks.py and its tests. Until then do not change 0.3.

## Next

## In progress

## Done
