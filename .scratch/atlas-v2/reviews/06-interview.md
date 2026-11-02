# Ticket 06 interview: questions as shown and the human's answers

Ticket: ~/dev/atlas/.scratch/atlas-v2/issues/06-decide-atlas-v2-architecture.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label is the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Facts shown before round 1 (checked on g10, 2026-11-02):

- omp 18.15.0. `omp auth-gateway stdio` lets any process Atlas starts call omp model roles by name on omp's own login; probed: an `@smol` chat call answered from `anthropic/claude-opus-5-5`. It does not serve the Jev judge here: `GET /v1/models` lists no judge models and `/v1/systemone` with `@judge` or `openrouter/~typesafe/jev-latest` answers 404, even with `OPENROUTER_API_KEY` in the environment. So live Jev still needs an OpenRouter key.
- omp starts a plugin's stdio MCP server per session; MCP sampling is unsupported. Plugin custom tools must be TS/JS. Plugin settings are still not readable at run time.
- Reconcile needs a human approval text per run; only Retrace may start it without the brief; about $2 and several minutes per run; pinned to an exact omp version; it gives change bullets plus one computed line, no marked diff.
- last30days is not installed; many lanes need keys or a logged-in browser; its JSON lists each result's URL.
- Atlas v1 is about 35k lines of stdlib Python with Markdown registries and no search index; reusable: URL canonicalisation, the JSON envelope, the transaction journal.
- SQLite FTS5 (BM25) works here (Python 3.13.5, SQLite 3.46.1).

## Round 1

### shape
Question: "How do agents in any repo use Atlas?"
- MCP server + one skill (Recommended) — "The atlas plugin ships a Python MCP server that omp starts for each session. It offers a small set of Atlas tools. One `atlas` skill teaches the flows (proposals, confirms, Reconcile). Every repo gets the tools without file paths. Moving to the cloud later means running the same server over HTTP."
- Skill + CLI — "One `atlas` skill runs a bundled command-line tool through bash, like v1. There is no server, and each call sends and receives JSON. Moving to the cloud later means rewriting the CLI to call a remote service."
- omp extension tools — "Native omp tools written in TypeScript. They fit omp most closely, but extensions can't call a model by role, and this ties Atlas to omp internals."
Answer: "didn't we previously decided that this would be in a form of plugins? re-evaluate. is mcp a better fit here? Note that dotagents already is required by atlas, and it is a plugin." (note: make it explicitly configurable as well. setup per repo that integrates atlas, etc. this would allow easy transition when the db is cloud-hosted. suggest if counter option is superior.)

### storage
Question: "Where does Atlas keep its data?"
- One SQLite database (Recommended) — "Sources, claims, topics, versions, trust notes, tally and inbox all live in one SQLite file with built-in BM25 search. The file sits outside every repo, for example `~/.local/share/atlas/atlas.db`. Storage is for agents only, so search speed wins. It can later move to hosted SQLite or Postgres with few changes."
- Markdown files + search index — "Records are Markdown files as in v1, plus a SQLite index rebuilt from them. Easy to diff and track in git, but two copies must stay in sync."
Answer: One SQLite database

### model_calls
Question: "Who makes Atlas's model calls (summarize, rewrite searches, rerank)?"
- Atlas calls omp roles itself (Recommended) — "The server starts `omp auth-gateway stdio` and calls `atlas_summarize`, `atlas_query` and `atlas_rerank` by role name using omp's own login (a test call worked here). A later scheduled run with no agent works the same way, and Atlas records exactly which model answered."
- The calling agent does it — "Atlas only stores and searches. The agent summarizes and reranks through subagents set to those roles. Atlas has no model code, but every flow depends on the agent following the skill, and later automation would need a rewrite."
Answer: Atlas calls omp roles itself (note on Atlas calls omp roles itself: make it configurable from the single setup interface skill, etc. Utilize mise secrets handling for the repo as appropriate.)

### jev_key
Question: "How does Atlas reach Jev, given that omp's gateway doesn't offer it?"
- Own key file, read by Atlas (Recommended) — "`~/.config/atlas/openrouter.env` (mode 600) holds `OPENROUTER_API_KEY`. Atlas reads it only for Jev calls, as the secrets rule says. Make it a separate OpenRouter key with a spend limit if you want Atlas spending tracked separately."
- Reuse the global key — "Use the `OPENROUTER_API_KEY` that mise already gives every session. No new file, but Atlas spending mixes with other OpenRouter use."
- No live Jev in v2 — "No key. Opus reranks, and topic creation has no library-wide check. Jev stays for offline quality tests in eval sessions."
Answer: Own key file, read by Atlas

### last30days
Question: "How does last30days plug in?"
- Not built in; links go to the inbox (Recommended) — "Atlas takes lists of links from any discovery tool through one 'add to inbox' call. If you install last30days later, it is just one more caller, since its JSON lists each result's link. Atlas needs no keys or browser sessions."
- Built-in last30days source — "Atlas runs last30days on request and files the results in the inbox. last30days must be installed, plus keys or a logged-in browser for X, TikTok and others."
Answer: Not built in; links go to the inbox

### abstract
Question: "What else does each stored source record keep for search?"
- Short abstract; no reuse cues (Recommended) — "Each record keeps a neutral 1–2 sentence abstract written from the page alone. In ticket 08 an abstract improved search slightly (+0.014 to +0.018), and the reranker reads it. Reuse cues gave no gain. Answers still write their own TL;DR for each question."
- Neither — "Keep the record exactly as ticket 02 decided. Search is slightly worse."
Answer: Short abstract; no reuse cues (note on Short abstract; no reuse cues: dotagents currently allows instruction to skip yielding, i.e. i've been adding "proceed reconcile without yielding" to allow reconcile invocation to proceed with the execution right away, skipping the overview part. If this is not robust or doesn't give a consistent behavior, propose changes. This might make my custom instructions to proceed without yield for future sessions more lean as well, i.e. a specific short forms to trigger the no yield, etc. Note, i have also combined the no yields with dev-workflow route overview as well, sometimes. i.e. when a dev-workflow route-overview is given, i trigger reconcile with "proceed with reconclie and route overview impl right away, with no yields for both". Mixed results, although more times, agent succesfully proceeded with reconcile + impl without yielding.)

### reconcile_call
Question: "How does Atlas start Reconcile for research plans and saved versions?"
- Atlas becomes a trusted caller (Recommended) — "dotagents lets Atlas start Reconcile without showing the brief, as Retrace already does. Your words are the approval: your research request for a plan, your 'yes' to 'Save as version N+1?' for a revision. The agent runs Reconcile (several minutes, about $2); the Atlas server never does. dotagents must change before Atlas relies on this, which goes to the build-order ticket."
- Show Reconcile's brief each time — "No dotagents change, but each review shows Reconcile's own brief and asks for approval: one more stop for every plan and every save."
Answer: Atlas becomes a trusted caller

### reconcile_missing
Question: "What happens when Reconcile can't run (dotagents is missing, or Reconcile refuses after an omp update)?"
- Go ahead, marked unreviewed (Recommended) — "Atlas shows the plan, or saves the version, marked 'not cross-checked: <reason>'. Reviews are signals, not requirements, so nothing blocks."
- Block until it works — "Plans and saves wait until Reconcile runs. Every saved version is reviewed, but one omp update can stop all saving."
Answer: Go ahead, marked unreviewed (note on Go ahead, marked unreviewed: report to human, with "Next" for options on what they could do next, i.e. setup reconcile first, or proceed without reconcile, etc.)

### embeddings
Question: "Does v2 ship the optional embedding add-on?"
- Not in v2 (Recommended) — "After reranking, embeddings added nothing (0.903 vs 0.902). v2 ships BM25, search rewriting and reranking only. If embeddings are added later, Atlas calls an embedding model by name through the same omp gateway, with no separate endpoint or key. This replaces the 'own endpoint setting' part of the 2026-10-19 decision."
- Optional add-on in v2 — "Ship an optional embedding setting now, with results merged into search. More code and a second index, for no measured gain."
Answer: Not in v2 (note on Not in v2: if not required, then drop it.)

## Round 2

Context shown before round 2: ticket 04 already set Atlas as the omp plugin `atlas`; an MCP server and a CLI both ship inside it. Re-evaluated in favour of the skill plus bundled CLI: same pattern as dotagents (Reconcile's helper via `$(realpath skill://…)`); model calls stay local through omp's login, so in the cloud only the store moves, which is one setting either way; omp's MCP client times out after 30 s by default (`OMP_MCP_TIMEOUT_MS`, `omp://mcp-runtime-lifecycle.md:105`), does not replay a call cut off after dispatch (line 152), loads tools into every session, and needs a restart after changes. On "proceed without yielding": Reconcile's SKILL.md (lines 273–297) already defines invocation pre-approval ("… Yield none. This message serves as that approval."); as a trusted caller Atlas does not need it; a shorter trigger is a dotagents change outside this map.

### shape2
Question: "Inside the `atlas` plugin, how do agents use Atlas?"
- Skill + bundled CLI (Recommended) — "One `atlas` skill runs `python3 \"$(realpath skill://atlas)/…\"` with JSON in and out, as Reconcile does. There is no server, and every call is one process. Moving the database to the cloud later is one setting."
- MCP server in the plugin — "A Python stdio MCP server that omp starts for each session, plus the skill. Native tools, but 30 s call timeouts, no retry of cut-off calls, tools loaded in every session, and a restart after changes."
Answer: Skill + bundled CLI

### config
Question: "How is Atlas configured, per user and per repo?"
- Profiles; repo picks one in mise (Recommended) — "`~/.config/atlas/config.toml` holds named profiles, each with a store (a local SQLite path now, a URL later) and whether Jev is on. Keys live in `~/.config/atlas/<name>.env` (mode 600), read only by Atlas. A repo that uses Atlas adds one plain line to its `mise.toml` `[env]`: `ATLAS_PROFILE = \"personal\"`. That line holds no secret, so the secrets rule allows it. Moving to the cloud means adding a profile and changing that line."
- One global config only — "Same files, but no per-repo choice: every repo uses the same store. Simpler, but a work repo can't point at a different store."
Answer: Profiles; repo picks one in mise (note on Profiles; repo picks one in mise: make naming consistent with dotagents plugin. atlas-init? init-atlas?)

### setup
Question: "What is the single setup interface?"
- `atlas-setup` skill in the atlas plugin (Recommended) — "One skill you can re-run safely, with one approval. For you: it adds the Atlas roles to omp config, writes config.toml, creates the store and says how to create the key file. For a repo: it adds the profile line. It ends with one test search through the real rerank path and reports which models answered and which fallback is active. dotagents' init-ask stays dotagents-only."
- Extend dotagents init-ask — "init-ask also sets up Atlas when the plugin is installed. One setup for everything, but dotagents then has to know about Atlas."
Answer: `atlas-setup` skill in the atlas plugin (note on `atlas-setup` skill in the atlas plugin: default is Jev, and it should always prioritize Jev. If Jev is not present, yield, with Next giving human options whether to use fallback, i.e. opus, etc, or allow human to setup Jev first.)

### reranker
Question: "Which reranker is the default, and what happens when it fails?"
- Jev, then Opus, then BM25 (Recommended) — "Jev reranks on title plus the first 700 characters (about 2× faster and 35–90× cheaper; quality about level with Opus). If Jev is off or fails, the `atlas_rerank` Opus role takes over. If that fails too, results stay in BM25 order. Each answer notes which ranker ran."
- Opus, then Jev, then BM25 — "Keep Opus as the default, which the check without Jev as grader slightly favours, and use Jev only as the cheap fallback. About $0.04–0.07 and 4.7 s per search."
Answer: Jev, then Opus, then BM25

### gather
Question: "How do topic creation and research plans find stored sources beyond a top-10 search?"
- Jev check over the whole library (Recommended) — "One Jev yes/no per source: 'is this about the same area as the brief?' Sources at P ≥ 0.3 go into the plan as candidates for the agent to read, with the count shown. It drops nothing. In ticket 11 this found all 6 trading sources for $0.03. Without Jev: rewrite the brief into several searches, take the BM25 top 100 of each, and rerank with Opus."
- Several searches only — "Always use the fallback: several rewritten searches plus a rerank. No Jev dependency, but it misses sources the way ticket 08's top 10 did."
Answer: Jev check over the whole library

### writer
Question: "Who writes answers and draft topic revisions (with labels and the Model view)?"
- Atlas role `atlas_answer` (Recommended) — "A fourth role, Opus `:medium` to start. Atlas writes the answer or draft in the one call ticket 09 allows, checks the Sound/Doubtful/Noise labels in code (showing claims unlabelled if the check fails), and records the exact model and thinking level. The agent shows the result as given. This also works for later automatic updates with no agent."
- The calling agent — "Atlas returns the evidence (claims, notes, backing counts), and the agent writes the answer, then sends it to an Atlas check for labels. No extra role, but the model name comes from the agent itself, and automation would need a writer later."
Answer: Atlas role `atlas_answer`

### notes
Question: "How are trust notes and the trust tally kept?"
- In the store; propose at 3 lines (Recommended) — "Notes and tally are SQLite tables, changed only through Atlas commands. Notes change after your confirm. The answer call returns any tally lines, and Atlas stores them without a stop. After 3 lines for one person and subject, Atlas proposes a note."
- Same, propose at 5 lines — "Fewer proposals, slower to notice a change in trust."
Answer: In the store; propose at 3 lines

### fetch
Question: "Who reads a web page when a source is added?"
- The calling agent (Recommended) — "The agent reads the page with omp's reader (which handles JavaScript sites and PDFs) and gives Atlas the link plus the text. Atlas checks the hash, skips unchanged repeats, summarizes and stores. A later scheduled fetcher would be just another caller of the same command."
- Atlas fetches itself — "Atlas downloads and extracts pages on its own. Works without an agent today, but plain Python extraction is weaker on JavaScript-heavy pages."
Answer: The calling agent

### research
Question: "Is research split into tasks after the plan step?"
- Plan items tracked; agent runs them (Recommended) — "The reviewed plan is stored with its items (questions, searches, stored sources, pages to fetch). Each item is marked done or skipped as the agent works, so research can resume. The agent uses its own web search and may use subagents; Atlas runs no task queue."
- Atlas task queue — "Atlas stores tasks with owners and status and hands them out to workers. Ready for later automation, but it is a scheduler v2 doesn't need yet."
Answer: Plan items tracked; agent runs them

### devresearch
Question: "Does the atlas plugin ship a rule telling `dev-research` how to use Atlas from other repos?"
- Yes, a short rule (Recommended) — "In repos set up for Atlas, dev-research first asks Atlas (read-only, no stop). At the end, it proposes adding the new sources it relied on, with one confirm. This replaces the dropped v1 `atlas-research` rule, without v1's topic states."
- No rule — "dev-research ignores Atlas unless you say so in the request."
Answer: Yes, a short rule

### noyield
Question: "Where does the short 'proceed without yielding' trigger for Reconcile and route overviews go?"
- Note it for dotagents (Recommended) — "I add one line to the Skill plugins release map's 'Not yet specified' section: a short, reliable pre-approval trigger for Reconcile and dev-ask route overviews. Atlas doesn't need it."
- Leave it — "No note. Bring it up in a dotagents session when you want it."
Answer: Leave it (note on Leave it: give me handoff instead, and i'll make the change form dotfiles repo instead. i also want it to be a semi-fixed format, with clear rules to handle the different scenarios to proceed without yields, i.e. in a continuation of a dev-workflow-triggered session, invoking reconcile and flagging to yield only reconcile should only stop after reconcile is done, or if human flag to proceed without yields for all, then after reconcile retuns, it should continue with dev-workflow impl right away, etc. i will finalize with dotfiles repo agent later.)

## Round 3

Context shown before round 3: dotagents names front doors domain-first (`dev-ask`, `product-ask`) and actions verb-first (`init-ask`, `bump-omp`). The no-yield note gets its own Handoff to the dotfiles agent at the end of this session.

### names
Question: "What are the two skills called?"
- `atlas-ask` and `init-atlas` (Recommended) — "The front door stays `atlas-ask`, like `dev-ask` and `product-ask`, and keeps v1's name. Setup is `init-atlas`, like `init-ask`."
- `atlas` and `atlas-init` — "Shorter and grouped by prefix, but this breaks dotagents' verb-first rule for actions."
Answer: `atlas-ask` and `init-atlas` (note on `atlas-ask` and `init-atlas`: let's make it `atlas-init` instead.)

### jev_missing
Question: "Jev comes first. What does Atlas do without it?"
- Stop if not set up; fall back if a call fails (Recommended) — "If the profile has no Jev key, Atlas stops before searching or gathering and ends with Next: set up Jev (`init-atlas`) or use Opus for this profile. It saves your choice in the profile, so it asks only once. If Jev is set up but a call fails (network, outage), Atlas uses Opus for that search and says so."
- Stop on every Jev problem — "Also stop when a Jev call fails, with the same Next. Opus never ranks without your say-so, but an outage stops every search."
Answer: Stop if not set up; fall back if a call fails

### commands
Question: "What does the bundled CLI offer the skill?"
- One command per action, v1 JSON reply (Recommended) — "About 12 commands: search, answer (about a question, a source or a topic), add (link plus text), inbox (add, list, review), source archive/restore, topic (create, draft, save, follow/unfollow, archive), plan (store, mark item), note (propose, set), status. Each returns v1's JSON reply (version, ok, op, disposition, result, findings, recovery) and v1's exit codes. No internal primitives are exposed."
- v1-style operation catalog — "A `capabilities` list plus lower-level operations the skill chains together. More flexible, but the skill must sequence the steps correctly, which is where v1 got heavy."
Answer: One command per action, v1 JSON reply (note on One command per action, v1 JSON reply: note, this could all be redesigned as well. revisit and see if they could be improved/refactored or not. everything including architecture + framework execution designs are all candidates for the refactoring. Only the high level mechanic of what the Atlas framework is for should be kept, i.e. a personalized library of knowledge that grow with you, etc. all finalized decisions will go through a round of reconcile afterwards. )

### v1code
Question: "What happens to the v1 code on main?"
- Fresh v2; keep two helpers (Recommended) — "Build v2 new on main. Carry over only link normalization (`atlas_url.py`) and the JSON reply plus exit codes (`atlas_cli.py`). Remove the v1 runtime, owners, scaffold and instance tooling in the cutover; v1 stays at tag `v1`. SQLite transactions replace v1's journal."
- Evolve v1 in place — "Change v1's modules step by step. This keeps working code, but most of it is tied to labels, topic states and Markdown registries that v2 drops."
Answer: Fresh v2; keep two helpers

### cloud
Question: "What moves to the cloud later?"
- Only the store (Recommended) — "Records and BM25 search sit behind one store interface: SQLite now, a hosted store at a profile URL later. Model calls, Jev and Reconcile stay with the local CLI on your omp login. Moving to the cloud means one new store adapter plus a profile change."
- All of Atlas as a service — "Run the whole CLI logic in the cloud. Needed for phone or push use without this machine, but it needs its own model keys, because omp's login stays local."
Answer: Only the store

### backups
Question: "How is the single SQLite file protected?"
- Daily snapshot, keep 14 (Recommended) — "Before the first write each day, Atlas copies the database with SQLite's `VACUUM INTO` to `~/.local/share/atlas/backups/`, keeping the last 14. A few MB each. Restoring means copying one file back."
- System backups only — "Atlas does nothing extra. A bad write or delete has no undo unless your machine backups cover the file."
Answer: Daily snapshot, keep 14 (note on Daily snapshot, keep 14: checkout the 4hour backup that i have already setup on this g10 that uploads to Drive, and see how this changes backup for atlas for this first redesign version. this was implemented from the dotfiles repo. i believe the backup should already covers the sqlite db, as the entire atlas dir gets backed up, or if it is better practice to also backup sqlite db separately, then sure, but upload to the same Drive, "dev-backup", with proper folder structure. propose.)

## Round 4

Context shown before round 4: `host-backup` (dotfiles; `~/.dotfiles/.config/scripts/host-backup`, `host-backup.timer`) runs restic every 4 hours (02, 06, 10, 14, 18, 22:00) and copies the encrypted repository to Drive at `gdrive:dev-backups/machines/<host>/restic`, keeping last 6, daily 14, weekly 8, monthly 12 (lines 30, 251–252). It backs up `~/dev`, `~/.omp/agent`, `~/.dotfiles` and a few files (lines 139–150), not `~/.local/share/atlas/`. Live `*.db` files are copied with SQLite's online backup API only under `~/.omp/agent` (lines 117–137); elsewhere a live database is copied as raw bytes. The round-3 Atlas snapshot would duplicate restic, so it was reopened.

### backup2
Question: "How is the Atlas database backed up?"
- host-backup copies it safely (Recommended) — "The database lives at `~/.local/share/atlas/<profile>.db`. A small dotfiles change makes `host-backup` copy that folder with the same SQLite backup step it uses for `~/.omp/agent`. Copies go into the existing restic repository on Drive (`dev-backups/machines/<host>/restic`): every 4 hours, encrypted, with the same retention. Atlas has no backup code of its own. The dotfiles change goes in your no-yield Handoff and lands before Atlas holds real data."
- Keep it under `~/.omp/agent/atlas/` — "Covered today with no dotfiles change, but Atlas data sits inside omp's own folder."
- Atlas snapshot as well — "The round-3 daily snapshot, plus host-backup. Two backup mechanisms for one file."
Answer: host-backup copies it safely (note on host-backup copies it safely: sounds good. add this to the list of tasks for the handoff that i will continue from the dotfiles repo.)

### commands2
Question: "Redesigned CLI: ten commands, each a whole user action. Use this set?"
- Ten intent commands (Recommended) — "Read-only (no confirm): `ask` (one command for all three answer formats: a question, a source or a topic's what's-new), `find` (ranked sources with no answer writing, for dev-research and plans; `--wide` runs the Jev check over the whole library) and `status` (profile, store, roles, Jev, Reconcile). Changes (after one confirm): `add` (one or many link-plus-text items), `inbox` (add, list), `topic` (create, draft, save, follow, unfollow), `plan` (save, mark item), `note` (set), plus `archive` and `restore` for any source, topic or note. Fewer, deeper commands than round 3's list."
- Round 3's list — "About 12 commands, with separate search and answer and per-object archive commands."
Answer: Ten intent commands (note on Ten intent commands: make sure to think from the perspective of the user while they are using. what kind of questions/interactions would they have, and given those scenarios, what interfaces would best fit them. note, the way how these interfaces respond should also be though thoroughly. i.e. like the "Next" or a section where agent guides users of what they could do next, or simply, what's next, etc.)

### reply
Question: "What does every command return?"
- Slim reply (Recommended) — "`{ok, op, result, problems, next}`. Each problem names the source and field at fault (v1's lesson). `next` lists options the skill shows as Next, for example 'set up Jev or use Opus'. Exit codes: 0 done, 1 failed, 2 bad input, 3 not set up. v1's `disposition` and `recovery` go, because each SQLite write is all-or-nothing."
- v1's seven-field reply — "Keep `version`, `ok`, `op`, `disposition`, `result`, `findings` and `recovery`, which were built for v1's multi-file journal."
Answer: Slim reply (note on Slim reply: this looks compact and concise, good. However, make sure we're not losing details that might be useful for users. They should not be brittle/redundant, like some metadata that are low-value.)

## After the first Reconcile run

Context: the first Reconcile run's final proposal (`06-reconcile-record.md`) was shown with a request to confirm. In a side ("btw") discussion the human asked the question below and Main answered as quoted. The human then replied with the message quoted after them.

### btw question (the human's words, exactly)

```
is there a way to make it better to use by leveraging the parent agent that is receiving the user requests? note, the agent used will always be current most frontier SOTA model. i.e. let the main agent distill/rephrase from any relevant context in the chat session thus far before triggering the relevant cli? This would mean cli could get additional context. Or is this something the design already does? what do you think?
```

### btw response (Main's words, as shown)

```
Only partly. Some steps already use the main agent's view of the conversation, but quick questions don't.

**Where the main agent already shapes the input**
- `atlas-ask` turns your plain-language request into a command, so it already picks the topic, the link or the question.
- For topic creation, the main agent drafts the brief and the plan, and that brief drives the wide search.
- For new sources, the main agent reads the page and passes Atlas the text.

**Where it doesn't**
- For `ask` and `find`, the question goes to the CLI as written. The CLI's own query-rewrite step then rewrites it on Opus without the chat history. So a follow-up like "what about the second one?" or "the trade-off we discussed" loses its meaning.

I think your idea is better, and it's a small change:
- **Self-contained question:** `ask` and `find` accept a question the main agent writes so it stands on its own, plus optional search phrasings and a few lines of context such as the goal, what you already ruled out and the repo.
- **Rewrite only as a fallback:** when the agent supplies phrasings, the CLI skips its own rewrite. The rewrite step stays for calls with no agent, such as a future scheduled fetcher or a bare CLI call.
- **Better context for writing:** the answer-writing call also gets the context, so the answer and gaps fit what you're actually trying to decide.
- **Traceability:** Atlas saves both your original words and the agent's version, so a strange result can be traced to how the question was rephrased.

**Risks**
- The main agent can carry its own assumptions into the search and narrow it too early. Keeping your original words alongside its version, and listing gaps in the answer, limits this.
- Answers become a little less repeatable, because the same question can be rephrased differently.

The design doesn't include this yet. To add it, put it in your reply when you confirm, for example "ask/find take an agent-written question and context; the CLI rewrite is only the fallback". I'd record it as a change from the interview.
```

### The human's reply (exactly)

"looks good, but once more on the following design decision, per "btw" discussion. amend it to the final proposal" — followed by the btw question and response above — "reconcile without yield."
