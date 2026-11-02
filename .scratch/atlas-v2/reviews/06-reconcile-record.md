## Review rounds

| Step | Reviewer/event | Pass | Text | Outcome | Turn |
|---|---|---|---|---|---|
| 1 | A | post-rethink | d12c37c8 | edit<br>• The list of changed earlier decisions misses the setup skill and the single vault<br>• Leaves out query rewriting and what happens when a role is missing, which the ticket asks<br>• Gives a Jev cost ratio that does not match ticket 11 | 217 s · 21 tools · 676k tokens · wait 2 s |
| 2 | B | post-rethink | d12c37c8 | edit · superseded<br>• Setup skill leaves out the human's note: Jev first, then Next if the Jev key is missing<br>• Fallback when the query-rewrite role is missing or fails stays open, though the ticket lists it<br>• Research cannot resume and inbox links never leave: no read path for plan items<br>• Two reasons overreach their sources; the one-vault standing decision change is unlisted | 527 s · 43 tools · 2.6M tokens · wait 3 s |
| 3 | B | later | 6d30a728 | edit<br>• Setup skill lacks the human's note: with no Jev it yields, with Next options<br>• Plan items cannot be read back and inbox links never leave, so research cannot resume<br>• Jev recording rule is missing; MCP and extension reasons overreach; two removals look asked<br>• Reviewer A's fixes (rewriting, missing role, two changed decisions, 35–90×) are right and kept | 198 s · 11 tools · 828k tokens |
| 4 | A | later | 4831ba61 | accept<br>• Accepts the revised summary as a whole<br>• The setup yield, plan readback, inbox exit and Jev records match the human's answers<br>• The new MCP and extension reasons match the scout's findings<br>• The change list matches the difference from the original | 27 s · 2 tools · 249k tokens |
| 5 | apply | — | 4831ba61 | applied | — |
| 6 | cleanup | — | — | A, B disposed (observed exit) | — |

## Final proposal

**Proposal**

- **Summary**
  
  - Plugin `atlas`: skills `atlas-ask` and `atlas-init`, a dev-research rule, and a bundled Python CLI
  - One SQLite store per profile; each repo picks a profile in mise; only the store moves to the cloud
  - Atlas calls omp roles through omp's gateway; Jev reranks and gathers with Atlas's own key file
  - Reconcile through a trusted-caller entry; without it, work goes ahead marked "not cross-checked"
  - Ten intent commands with a slim JSON reply and Next; fresh v2 code; host-backup covers the store
  
  **Details**
  
  # Decide Atlas v2 architecture: decision summary
  
  Settled by grilling over four rounds on 2026-11-02. Every question, its options as shown and the human's exact answers are in the interview record (`~/dev/atlas/.scratch/atlas-v2/reviews/06-interview.md`). Items marked "(Main)" were not asked; they are Main's design choices inside the human's answers.
  
  ## 1. Shape and surface
  
  1. Atlas is the omp plugin `atlas` in `kimprap/atlas` (ticket 04). It requires the `dotagents` plugin for Reconcile.
  2. The plugin ships:
     - `atlas-ask`: the front door. It turns a plain-language request into one flow, makes the one proposal and confirm for changes, runs Reconcile when the flow needs it, and shows results with a closing Next.
     - `atlas-init`: the single setup skill (section 3).
     - `atlas-research`: a short rule for `dev-research` (section 6).
     - A bundled Python CLI inside the `atlas-ask` skill folder, run as `python3 "$(realpath skill://atlas-ask)/…"` with JSON on stdin and JSON on stdout, the same pattern dotagents uses for the Reconcile controller.
  3. No MCP server and no omp extension. Reasons: same pattern as dotagents; model calls stay local either way, so MCP's cloud advantage does not apply (section 4); omp's MCP client times out at 30 s by default, never replays a call that was cut off, loads tools into every session, and needs a manual `/mcp reload` after changes.
  
  ## 2. Commands and replies
  
  ### Ten intent commands
  
  Each command is one whole user action. Sources are named by their canonical link and topics by their name, so no opaque ids reach the user or the skill (Main).
  
  | Command | Kind | Does |
  | - | - | - |
  | `ask` | read | Answers a question, a source or a topic (its what's-new) in the matching ticket 02 format |
  | `find` | read | Ranked stored sources, no answer writing; `--wide` runs the Jev check over the whole library |
  | `status` | read | Profile, store, roles and models, Jev, Reconcile readiness, counts, inbox size |
  | `add` | change | One or many link-plus-text items: summarize, store, skip unchanged repeats |
  | `inbox` | change (`list` read) | Add links in bulk unsummarized; list them; a link leaves the inbox once `add` stores it (Main) |
  | `topic` | change (`list` read) | Create, draft, save, follow, unfollow; list topics |
  | `plan` | change (`show` read) | Save a reviewed research plan; mark an item done or skipped; `show` lists its open items so research can resume (Main) |
  | `note` | change | Set or change a trust note |
  | `archive` | change | Hide a source, topic or note; kept and restorable; never a hard delete |
  | `restore` | change | Bring an archived item back |
  
  Read commands run without a stop. Change commands run only after the user's one confirm, except tally lines, which Atlas stores without a stop (ticket 09 item 10).
  
  ### What the user does and sees
  
  | The user says | Flow | The user sees, ending with Next |
  | - | - | - |
  | "What do we know about X?" | `ask` | Answer first; claims with sources, Sound/Doubtful/Noise labels, backing counts; who disagrees, with any trust note; gaps; Model view; writing model; ranker. Next: research the gaps, save as a topic |
  | "Summarize this link" | `ask`; if not stored, confirm → agent reads the page → `add` → `ask` | Source format: TL;DR, claims that matter, caveats, author and date, link. Next: ask a question about it, see topics that cite it |
  | "Add these links" | confirm → `add` | Per link: added, already stored, updated (topics citing it flagged), unreadable (nothing stored), or a page of links (asks: this page or each link). Next: ask about them |
  | "Save these for later" | confirm → `inbox add` | How many went to the inbox. Next: review the inbox |
  | "Create a topic on X" | `find --wide` → plan → Reconcile → shown → confirm → `topic create`, `plan save` → research (`add`, `plan mark`) → `topic draft` | The reviewed plan with Reconcile's changes; then the draft understanding. Next: "Save this as version 1?" |
  | "What's new on X?" | `ask` (topic) | Agreed version and date; conclusion-changing evidence with who, backing, label and note; count of other new sources; draft revision. Next: save as version N+1, list the other sources, research more |
  | "Yes, save it" | Reconcile → `topic save` | Saved version N+1 with Reconcile's changes marked as given. Next: what to follow up |
  | A tally proposal, or "lean towards Y on Z" | confirm → `note set` | The note as saved |
  | "Is Atlas set up?" | `status` | What is ready and what is missing. Next: the fix for each missing part |
  
  ### Reply
  
  1. Every command returns `{ok, op, result, problems, next}`. Exit codes: 0 done, 1 failed, 2 bad input, 3 not set up.
  2. `problems`: each names the source (by link) and field at fault. One bad source never blocks a search or a batch; it is reported and the rest proceed (v1 lesson).
  3. `next`: one to three plain options the skill shows as Next. Every user-facing reply ends with Next, matching ticket 09 item 15.
  4. `result` carries what the user reads or the next step needs: titles, links, authors, dates, outcomes, labels, models, flagged topics, Reconcile changes. It leaves out low-value metadata: content hashes, timings, sequence numbers, schema versions, internal ids. Stored records still keep hashes and dates (ticket 02).
  5. v1's `version`, `disposition` and `recovery` are dropped because each SQLite write is one all-or-nothing transaction.
  
  ## 3. Configuration and setup
  
  1. `~/.config/atlas/config.toml` holds named profiles. Each profile has a store (a local SQLite path now, a URL later) and a Jev setting: on, or "Opus" when the user chose the fallback. It also holds a default profile, used when a repo names none (Main).
  2. Keys live in `~/.config/atlas/<name>.env` (mode 600). Atlas reads them itself, only for the call that needs them, per the secrets rule. The repo documents each key name and how to create it, never a value.
  3. A repo that uses Atlas adds one non-secret line to its `mise.toml` `[env]`: `ATLAS_PROFILE = "<name>"`. Moving a repo to a cloud store means adding a profile and changing that line.
  4. `atlas-init` is one re-runnable skill with one approval:
     - For the user: adds the four Atlas roles to omp's `modelRoles`, writes `config.toml`, creates the store, and says how to create the key file.
     - For a repo: adds the profile line, which also turns on the `atlas-research` rule there.
     - Jev comes first: if the profile has no Jev setup, `atlas-init` yields before the test search, with Next: use a fallback such as Opus for this profile, or set up Jev first.
     - It ends with one test search through the real rerank path and reports which models answered and which fallback is active.
     - dotagents' `init-ask` stays dotagents-only.
  
  ## 4. Storage and the cloud seam
  
  1. One SQLite database per profile at `~/.local/share/atlas/<profile>.db`, with FTS5 BM25 search. It holds sources (with the stored record), claims, topics and versions, plans and items, the inbox, trust notes, and the tally. Archive hides; nothing is hard-deleted.
  2. Records and BM25 search sit behind one store interface. SQLite is the only adapter in v2. A hosted store at a profile URL is a later adapter.
  3. Only the store moves to the cloud. Model calls, Jev and Reconcile stay with the local CLI on the user's omp login.
  4. Backup: `host-backup` (dotfiles) copies `~/.local/share/atlas/*.db` with the same SQLite online-backup step it uses for `~/.omp/agent`, into the existing encrypted restic repository on Drive (`dev-backups/machines/<host>/restic`), every 4 hours with its retention (last 6, 14 daily, 8 weekly, 12 monthly). Atlas has no backup code. The dotfiles change lands before Atlas holds real data.
  
  ## 5. Models
  
  1. Atlas makes its own model calls through `omp auth-gateway stdio`, by role name, on omp's login: `atlas_summarize`, `atlas_query`, `atlas_rerank`, and a new `atlas_answer`. Each starts at `anthropic/claude-opus-5-5:medium`. Atlas records the model the gateway reports and the role's thinking level.
  2. `atlas_answer` writes answers and draft topic revisions, with their labels and Model view, in the one call ticket 09 allows. Atlas checks the label format in code right after the call; if the check fails, the claims are shown unlabelled and the answer says so. The same call returns any tally lines.
  3. Jev (`~typesafe/jev-latest` through OpenRouter Decisions) is called directly with `OPENROUTER_API_KEY` from `~/.config/atlas/openrouter.env`, because omp's gateway does not serve judge models here. In v2 Jev:
     - reranks by default: one yes/no per query and candidate over the top 30 of BM25 with `atlas_query` rewriting, on the title plus the first 700 characters, sorted by probability;
     - runs the wide gather: one yes/no per stored source, "is this about the same area as the brief?"; sources at P ≥ 0.3 go into the plan as candidates for the agent to read, with the count shown; nothing is dropped.
  4. Order: Jev, then the `atlas_rerank` Opus role, then BM25 order. Every answer notes which ranker ran. Atlas records each Jev probability and the Jev model version that answered (decision-model rule).
     - Jev not set up for the profile: Atlas stops before searching or gathering, with Next: set up Jev (`atlas-init`) or use Opus for this profile. The choice is saved, so it is asked once.
     - Jev set up but a call fails: Opus ranks that search, and the answer says so.
     - Without Jev the wide gather rewrites the brief into several searches, takes the BM25 top 100 of each, and reranks with Opus.
     - A missing Atlas role: the command stops with exit 3 and prints the exact `modelRoles` lines to add (ticket 05 decision 4), with Next: run `atlas-init`. A failed `atlas_query` call: BM25 searches the request as written, and the answer says so (Main).
  5. Jev's claim-support and near-duplicate flags stay allowed uses (map standing decision, 2026-10-29) but are not part of this decision; they belong to the map's open items on quality judging and source identity (Main).
  6. No embeddings in v2, and no embedding setting.
  
  ## 6. Sources, research and Reconcile
  
  1. Adding a source: the calling agent reads the page with omp's reader and gives `add` the link plus the text. Atlas normalizes the link (v1's `atlas_url.py`), compares the content hash, skips unchanged repeats, summarizes with `atlas_summarize` from the page only, and stores. A later scheduled fetcher would be one more caller of `add`.
  2. The stored record keeps a neutral 1–2 sentence abstract written from the page; BM25 and the reranker read it. No reuse cues. Answers still write their own TL;DR.
  3. The inbox takes bulk links from any discovery tool. last30days is not built in; installed later, it is one more caller.
  4. Research: the calling agent drafts the plan (questions, searches, stored sources from `find --wide`, pages to fetch) (Main). After review and the user's confirm, `plan save` stores it with its items. The agent runs the items with its own web search, and may use subagents, marking each done or skipped, so research can resume. Atlas runs no task queue.
  5. Reconcile:
     - dotagents gains a trusted-caller entry for Atlas, as Retrace has. The `atlas-ask` skill runs the controller; the CLI never does.
     - Approval is the user's own words: the research request for a plan, the "yes" to "Save this as version N+1?" for a revision.
     - The candidate is the plan text, or the draft revision with its labels and Model view. After the run, `plan save` or `topic save` stores the reviewed text, the reviewer models, the run, and Reconcile's Changes, shown as given and not re-summarized.
     - When Reconcile cannot run (dotagents missing, a refusal such as a version pin after an omp update): Atlas shows the plan or saves the version marked "not cross-checked: <reason>", and Next offers to set up Reconcile first or to go on without it.
  6. Trust notes and the tally are tables in the store, changed only through Atlas commands. After 3 tally lines for one person and subject, Atlas proposes a note; that pair's count restarts after the proposal.
  7. The `atlas-research` rule: in a repo with `ATLAS_PROFILE` set, `dev-research` first asks Atlas (`find` or `ask`, read-only, no stop); at the end it proposes adding the new sources it relied on, with one confirm. It replaces the dropped v1 rule and has no v1 topic states.
  
  ## 7. Code
  
  1. v2 is built fresh on main. Carried over: `atlas_url.py` (link normalization) and the CLI's strict JSON input and exit handling from `atlas_cli.py`, reshaped to the slim reply.
  2. The v1 runtime, owners, scaffold and instance tooling are removed in the cutover; so are the command stub and v1 `ARCHITECTURE.md` (Main). v1 stays at tag `v1`.
  
  ## Changes to earlier decisions
  
  All follow from the human's answers in this interview.
  
  - Map standing decision on Atlas models (2026-10-19):
    - three roles become four (`atlas_answer` added);
    - "Embeddings are an optional add-on with their own endpoint setting" is dropped;
    - the default reranker is Jev, because ticket 11's test runs met the standing Jev decision's condition and the human chose it.
  - Ticket 02 stored record: a short neutral abstract returns (the TL;DR stays dropped from the record).
  - Ticket 09's rejection of a separate `atlas_assess` role still holds: `atlas_answer` is the one call that writes the answer, not an extra call.
  - The map's open item on how `dev-research` uses Atlas is settled here (section 6, item 7).
  - Map standing decision on the vault (charting round 1): one vault becomes one store per profile. Repos reach a store through the bundled Atlas CLI by profile name instead of a running service, and still never by file path.
  - Ticket 05: init-ask no longer sets up Atlas through Atlas's registry (decision 9 and the rejected separate Atlas setup); `atlas-init` does. Atlas has four roles, not three (decision 4).
  
  ## Rejected alternatives
  
  - MCP server in the plugin: 30 s default timeout, no replay of cut-off calls, tools in every session, a manual `/mcp reload` after changes; its cloud advantage needs model calls in the cloud, which have no omp login there.
  - omp extension tools: extensions have no documented completion call on a chosen role, so they would spawn the same gateway from TypeScript or lean on undocumented internals.
  - Markdown files plus an index: two copies to keep in sync.
  - The calling agent doing model work: every flow depends on the agent, and automation needs a rewrite.
  - Reusing the global OpenRouter key: Atlas spending mixes with other use. No live Jev: loses the default reranker and the wide gather.
  - Built-in last30days: keys and logged-in browsers in Atlas.
  - No abstract: slightly worse search. Reuse cues: no measured gain.
  - Showing Reconcile's brief each time: one more stop per plan and per save. Blocking until Reconcile works: one omp update could stop all saving.
  - An embedding add-on: no measured gain after reranking.
  - One global config: a repo cannot use a different store.
  - Extending dotagents' `init-ask`: dotagents would have to know about Atlas.
  - Opus as the default reranker: about 35–90× the cost and 2× slower for level quality.
  - Stopping on every failed Jev call: an outage would stop every search.
  - An Atlas task queue: a scheduler v2 does not need.
  - No dev-research rule: Atlas is skipped unless asked.
  - The round-3 list of about 12 commands and v1's seven-field reply: shallower commands; fields built for v1's journal.
  - Evolving v1 in place: most of it is tied to labels, topic states and Markdown registries that v2 drops.
  - All of Atlas as a hosted service: needs its own model keys.
  - An Atlas daily snapshot, or the store under `~/.omp/agent/atlas/`: duplicates restic, or puts Atlas data in omp's folder.
  
  ## Passed on
  
  - To [Decide Atlas build order](~/dev/atlas/.scratch/atlas-v2/issues/07-decide-atlas-build-order.md): before Atlas relies on them, dotagents' trusted-caller entry for Atlas, the Reconcile diff from ticket 09, and the host-backup change for `~/.local/share/atlas/*.db`.
  - To the map's open items: quality judging, and source identity with Jev's near-duplicate and claim-support flags; plugin linking and release.
  - To the dotfiles repo (Handoff at the end of this session): the host-backup change, and a semi-fixed "proceed without yielding" trigger for Reconcile and dev-ask route overviews.
  - After this ticket closes: delete the ticket 08 and 11 prototype folders, as their results say.
  

**Changes**

- Reranks the top 30 of BM25 with query rewriting; adds missing-role and failed-query rules
- Flags two more changed earlier decisions (Atlas setup, single vault); cost gap is 35–90×
- Setup yields with Next when Jev is missing; Jev probabilities and model version are recorded
- Adds plan show and inbox exit; fixes MCP and extension reasons; marks two removals (Main)
- Summary: unchanged · Details: edited

## Spend

| Reviewer | Model | Tokens | Cost |
|---|---|---|---|
| A | anthropic/claude-opus-5-5 · high | 925,247 | 1.705913 USD |
| B | anthropic/claude-sonnet-5-5 · xhigh | 3,430,030 | 2.389324 USD |
| Total | | 4,355,277 | 4.095237 USD |
