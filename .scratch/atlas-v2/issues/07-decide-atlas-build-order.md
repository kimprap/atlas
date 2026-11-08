Type: grilling
Parent: [Atlas v2](../map.md)
Blocked by: 06
Also blocked by: the [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md) map being resolved, since Atlas builds on `dotagents`.
Status: resolved

## Question

In what order is Atlas v2 built, and which parts depend on the `dotagents` plugin release? Known constraint: the skill plugins ship before any Atlas release that relies on Reconcile.

Input from [Decide source credibility weighting](09-decide-source-credibility-weighting.md): after a save, Atlas shows what Reconcile changed compared with the draft. The user will add that diff to the Reconcile skill in a separate session, and it must land before Atlas relies on it.

Input from [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md): three dotfiles changes land before Atlas relies on them, and the user plans to build them first in the dotfiles repo (Handoff of 2026-11-02):

- dotagents' Reconcile gains a trusted-caller entry for Atlas, as Retrace has, so the `atlas-ask` skill can run Reconcile with the user's own words as approval.
- The Reconcile diff above.
- `host-backup` copies `~/.local/share/atlas/*.db` with its SQLite online-backup step, before Atlas holds real data.

The architecture also sets the build's shape: a fresh v2 on main that keeps only `atlas_url.py` and the CLI's JSON input and exit handling, and removes the v1 runtime, owners, scaffold, instance tooling, command stub and v1 `ARCHITECTURE.md` in the cutover.

This ticket was "Decide build order" until 2026-10-22, when the plugin release moved to its own map. The plugin half of its question went to [Decide plugin build order](~/.dotfiles/.scratch/skill-plugins/issues/04-decide-plugin-build-order.md).

## Answer

Prerequisites are met, so nothing in Atlas waits on dotfiles. Before the spec, the map decides source identity, the quality check's form and the plugin release. The summary-model prototype must resolve before real sources go in. The build then runs in eight stages, each ending in a smoke run through `atlas-ask`: v1 is removed and the plugin linked first, and Atlas is first usable at stage 4, where real data and migrations start.

Records:

- Interview, with every question as shown and the human's exact answers: [07-interview.md](../reviews/07-interview.md)
- Reconcile run on the summary: [07-reconcile-record.md](../reviews/07-reconcile-record.md)

The human's deciding words after the review, quoted exactly: "approve - dotagents version has been updated. adjust accordingly." (the run's approval), then, to the two questions after the run, the options "Accept the reviewers' change" and "Confirm" (both shown in full in the interview record). The accepted option reads: "The ticket is created on this map now, so it can run in a parallel session. If it is still open when the map's other tickets close, the map closes it as passed on, and the spec route carries it as a gate before real sources go in at stage 4. This matches your round-2 choice that the spec does not wait on it."

Settled by grilling over two rounds on 2026-11-06 and reviewed by one Reconcile run on 2026-11-08. The final proposal follows; items marked "(Main)" were not asked.

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
