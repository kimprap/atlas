# Atlas v2

## Destination

Enough decisions are settled to write the Atlas v2 specification and its build order. The specification is written afterwards, in a separate `dev-ask` route. The skill plugins ship first, planned in [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md), and Atlas v2 builds on them.

## Notes

Domain: the redesign of Atlas (the user's agent-facing research library), shipped as the omp plugin `atlas`.

Split on 2026-10-22: at the user's request, the plugin release (export, release, evals, bootstrap migration, its build order and Check runtime ADR dependencies) moved to [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md), which is planned and built first. The plugin decisions below (Research omp plugin capabilities, Decide repo and catalog layout, Decide shipped skills and personal layer) stay here and are indexed in both maps.

Consult `dev-grilling` and `dev-domain-modeling` for grilling tickets, `dev-research` for research tickets, and `dev-codebase-design` for repository layout and Atlas architecture. Treat `~/.dotfiles` as the source of truth for the skills; current upstream and Atlas v1 sources are evidence, not authority.

Standing decisions from charting (round 1):

- **Audience:** the user for now, built public-ready. Personal settings (models, paths, preferences) live in a separate layer so publishing later is cleanup, not a rewrite.
- **Agent tools:** omp only. Claude Code, Grok, and Cursor come later.
- **Vault:** one vault on this Mac. Repositories reach it through a service, never by file path, so moving it to cloud hosting later costs little.
- **Storage:** agents only. No Obsidian browsing, so storage is whatever searches best.
- **Old vault:** `~/dev/atlas-v1-vault/instances/atlas` (679 summaries, 10 topics) is frozen read-only. A source is re-added from its original link when it is next needed.

Standing decision on Atlas models (user, 2026-10-19, after [Prototype retrieval on real summaries](issues/08-prototype-retrieval-on-real-summaries.md)):

- Atlas's model work runs on omp's frontier model through its own omp model roles, following Reconcile's `second_opinion_a`/`second_opinion_b` pattern.
- There are three roles: `atlas_summarize` (writes source summaries), `atlas_query` (rewrites searches) and `atlas_rerank` (orders results). Each starts at `anthropic/claude-opus-5-5:medium`.
- omp roles can only be chat models, so embeddings cannot use one. The default search is BM25 plus query rewriting plus an LLM rerank, with no vectors. Embeddings are an optional add-on with their own endpoint setting, like mnemopi's `embeddingModel`.
- The roles go into omp `config.yml` when Atlas is built; nothing reads them before then.
- Accepted cost: each search makes paid Opus calls of about 2–4 s. The test ran the reranker at `:high`, so `:medium` is untested.

Standing decision on the Jev decision model (user, 2026-10-29, after the dotfiles route that mapped TypeSafe's Jev cookbook; evidence in [Jev decision model research](inputs/jev-decision-model-research-2026-10-29.md)):

- The user: "Generally, i feel like adding Jev decision model would be beneficial and cost efficient." Under `rule://decision-model`, Jev may only rank or flag; it never filters, drops or decides.
- Jev becomes Atlas's default reranker only after test runs that compare Jev with Opus on quality, speed and cost. Quality: nDCG@10 on the queries and graded pool of [Prototype retrieval on real summaries](issues/08-prototype-retrieval-on-real-summaries.md), plus fresh spot checks by the user and the user's six-source trading list, grading any new top-10 results that fall outside the pooled 1,535 pairs. Speed: wall time per query. Cost: cost per query. Until then the 2026-10-19 decision on Atlas models stands. The test runs can run in an omp eval session; a Jev reranker inside Atlas runs out of process (omp extensions have no judge call), so it also needs the credential decision below.
- Pooled Jev grading, as in ticket 08, is the quality-judging method; the user's spot check stays the gate. Caveat: Jev also produced the ticket-08 grades, so a Jev reranker is scored by its own model family, and Jev rated 4 of the 6 trading sources as not relevant.
- Claim-locator support checks and near-duplicate checks use Jev only to flag items the agent or the user then reads. The locator check, canonical URL and content hash stay deterministic.
- Live Jev calls from Atlas run out of process and need a direct provider credential, which the user decides in [Decide Atlas v2 architecture](issues/06-decide-atlas-v2-architecture.md).
- Ruled out: topic labels, probabilistic freshness detection, and credibility weighting.

Standing preference for how agents respond (from [Define Atlas v2 requirements](issues/02-define-atlas-v2-requirements.md); applies to every agent reply on this effort, not only Atlas):

- Concise, high-level, plain language and formatting, in the style of Reconcile and Retrace output. This governs formatting, not the content of the changes.
- Changes get one short proposal with suggested next steps and one confirm; read-only asks are answered directly.

Standing review plan (user, 2026-10-21): Reconcile runs on each decision as it is made.

- One catch-up run reviewed the decisions up to and including [Decide shipped skills and personal layer](~/.dotfiles/.scratch/atlas-and-skill-plugins/issues/05-decide-shipped-skills-and-personal-layer.md), with the map's standing decisions and tickets 02 and 04 open for change. It changed none of them ([record](~/.dotfiles/.scratch/atlas-and-skill-plugins/reviews/05-reconcile-record.md)).
- Each remaining decision ticket ([Decide Atlas v2 architecture](issues/06-decide-atlas-v2-architecture.md) and [Decide Atlas build order](issues/07-decide-atlas-build-order.md)) gets one Reconcile run on its summary before the user confirms it and the ticket closes. Earlier decisions stay fixed in these runs; reviewers flag conflicts instead of rewriting.
- Research and prototype tickets are evidence and are not reviewed on their own.
- Once the map is resolved, one final run reviews the closing Handoff, with every ticket open for change, before the map goes back to `dev-ask`. It checks for contradictions between tickets and gaps toward the destination.
- Reconcile records are kept in `reviews/`.

Standing rule on secrets (user, 2026-11-02): Atlas follows `rule://secrets`, added to all repositories. Each secret Atlas needs (for example a direct Jev provider key) has one mode-600 home outside every repository, such as `~/.config/atlas/<name>.env`, and is loaded only for the command that needs it. The repository names each key and how to create it, never a value. Atlas never prints, logs or commits a value, and never puts a key in a repository mise `[env]`, a tracked `.env`, a shell profile or argv. Only keys every session needs go in the global mise env.

Constraints while charting:

- `~/dev/atlas-v1-vault` (the frozen v1 vault) is read-only.
- No installs or releases. Commit only when the user asks.

Context:

- Current Atlas is this repo, `~/dev/atlas` (`kimprap/atlas`; v1 is tagged `v1`, v2 is built on main); last feature commit `0ad4f0a` (2026-08-25, open-world source routing).
- On 2026-11-02 Atlas work moved from the Mac to g10. The repo, formerly `~/dev/atlas/app`, is now `~/dev/atlas`; the v1 vault, formerly `~/dev/atlas/vault`, moved out of it to `~/dev/atlas-v1-vault` (local-only git, summaries untracked).
- Skills reach other repositories today through the `~/.agents` symlink created by `.config/scripts/bootstrap`.
- Seed source for Atlas v2 (link only, no summary yet): <https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence>

## Decisions so far

<!-- One named gist/link pointer per resolved child ticket. The detailed answer lives only in that ticket. -->
- [Research omp plugin capabilities](~/.dotfiles/.scratch/atlas-and-skill-plugins/issues/01-research-omp-plugin-capabilities.md) — On omp 18.11.2 one plugin can carry skills, agents, rules, commands, hooks, extensions, tools and MCP servers; one marketplace catalog can list plugins from other repos pinned by ref/sha; `omp plugin link` is a live symlink. Gaps: plugin settings are not readable by skills at run time, skills reach bundled helpers only via `realpath skill://…`, and marketplace installs skip dependency installs.
- [Research label-free source retrieval](issues/03-research-label-free-source-retrieval.md) — BM25 is a strong floor for agent queries (best with agent query rewriting); keyword + embeddings + reranker has the best evidence; at ≤10k summaries exact vector search suffices; SQLite FTS5, LanceDB and Postgres+pgvector move to hosting largely unchanged; no published benchmark matches LLM-written summaries, so a local test on real data is the open gap.
- [Define Atlas v2 requirements](issues/02-define-atlas-v2-requirements.md) — Manual v2 built for later automation: text web pages, deliberate adds summarized at once and bulk links held in an inbox; claims-first agent-only records; stored-first answers in three formats; topics as briefs with user-confirmed numbered versions, followed unless unfollowed, showing only conclusion-changing news; Reconcile on every research plan and proposed revision; credibility weighting deferred to its own ticket.
- [Prototype retrieval on real summaries](issues/08-prototype-retrieval-on-real-summaries.md) — On the 673 v1 summaries, a reranker is the biggest gain, and the LLM reranker beats Nemotron. After reranking, embeddings add nothing over BM25 with agent query rewriting. Reuse cues barely help, while a short TL;DR helps a little. A top-10 search misses much of what the user counts as a broad topic's sources.
- [Decide repo and catalog layout](~/.dotfiles/.scratch/atlas-and-skill-plugins/issues/04-decide-repo-and-catalog-layout.md) — Dotfiles `.config/agents/` stays the source, with the ADRs, and becomes an omp plugin that this Mac links. A public release copy, `kimprap/dotagents`, holds one plugin at its root and is filled by an export script. Atlas stays in `kimprap/atlas` as plugin `atlas` (v1 tagged, v2 on main). Both are git-package installs, with the catalog later. Helpers are called through `"$(realpath skill://<owner>)/…"`, and the controller moves into the `reconcile` skill folder.
- [Decide shipped skills and personal layer](~/.dotfiles/.scratch/atlas-and-skill-plugins/issues/05-decide-shipped-skills-and-personal-layer.md) — Nearly everything ships in `dotagents`. The `bump-*`, `mnemopi-*` and `optimize-retrace` skills, `naming-taste`, `key-remaps.js`, `ttsr-guard.py`, this Mac's omp configs and the base `AGENTS.md` stay personal. Model choices go in omp `modelRoles` and machine paths are found at run time. Each plugin ships a settings registry, and a rewritten init-ask sets up roles, the global `AGENTS.md` (linked as `~/.omp/agent/AGENTS.md`) and an optional papercut ledger with one approval. An item-level manifest makes the export fail on unlisted items and personal paths. The omp version stays pinned exactly. There is no help skill.
- [Decide source credibility weighting](issues/09-decide-source-credibility-weighting.md) — No automatic credibility score and nothing hidden for who wrote it. Trust notes (who, subject, lean, reason, date) and independent-backing counts show at answer time and never change search. The answering model labels claims Sound, Doubtful or Noise and adds a Model view in the same call. Trust is re-judged from a tally kept during existing work. Reconcile reviews research plans before they are shown and topic revisions only when the user chooses to save, marking what it changed. Every answer ends with a Next. All of these are signals, not bindings.

## Not yet specified

- How summaries and search results are judged for quality: run by hand, compare the old and new versions, read-only, no scheduling ([Atlas v1 notes](inputs/atlas-v1-notes.md), note 1). The pooled LLM grading plus user spot-check from [Prototype retrieval on real summaries](issues/08-prototype-retrieval-on-real-summaries.md) is one tested method. It also judges whether the claim labels and backing counts from [Decide source credibility weighting](issues/09-decide-source-credibility-weighting.md) help. The standing decision on the Jev decision model (2026-10-29) makes pooled Jev grading the method.
- How a source's identity is decided and duplicates are caught, e.g. X links with and without `s=<digits>` ([Atlas v1 notes](inputs/atlas-v1-notes.md), note 6). The standing decision on the Jev decision model (2026-10-29) allows Jev only to flag near-duplicate candidates.
- How the Atlas plugin is linked on this Mac and released (tags, catalog entry), building on the release and bootstrap decisions in [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md).
- How `dev-research` uses Atlas from other repos. On 2026-10-29 dotagents dropped its `atlas-research` rule, which described Atlas v1 topic states (`current`, `dirty`, `refreshing`, `blocked`) and explicit refresh. [Decide Atlas v2 architecture](issues/06-decide-atlas-v2-architecture.md) decides whether the Atlas plugin ships a replacement rule and what it says.

## Out of scope

- Obsidian browsing of the vault.
- Agent tools other than omp.
- The skill plugin release, export, evals and bootstrap migration, including Check runtime ADR dependencies (formerly ticket 10): moved to [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md).
- Converting or repairing the old vault.
- Building anything; implementation starts only after the specifications exist.
