# Ticket 07 interview: questions as shown and the human's answers

Ticket: ~/dev/atlas/.scratch/atlas-v2/issues/07-decide-atlas-build-order.md
Each question is copied as shown to the human, with every option's label and full description. "Answer" is the human's reply exactly as given. A chosen option's label is the human's answer. The "(Recommended)" marker was the assistant's recommendation, not the human's choice.

Facts shown before round 1 (checked on g10, 2026-11-06):

- Prerequisites are done. The Skill plugins release map is resolved, and `dotagents` is published at v0.4.1 and linked on g10. The dotfiles tasks from the 2026-11-02 Handoff have landed:
  - host-backup now backs up `~/.local/share/atlas/*.db` (`1e92343`).
  - Reconcile marks what reviewers changed and accepts `atlas-ask` as a trusted caller, with a `ready atlas-ask` check (`9ffc1e4`).
  - The fixed pre-approval wording is in (`61b125d`).
  - `init-ask` now reads only dotagents' own settings (`fd49a85`).
- The repo still holds v1. Main has the full v1 runtime, owners, scaffold, rules, ADRs 0001–0007 and tests. `AGENTS.md` still blocks two v1 plans (evaluation loop, topic creation) that v2 replaces.
- No Atlas data or config exists yet. Neither `~/.config/atlas` nor `~/.local/share/atlas` is present.

## Round 1

### cutover
Question: "When does v1 leave main?"
- Remove v1 first (Recommended) — "Stage 1 is one commit that deletes the v1 runtime, owners, scaffold, instance tooling, command stub, v1 ARCHITECTURE.md, v1 rules and tests. It keeps atlas_url.py and the CLI's JSON/exit handling and rewrites AGENTS.md for v2. The two blocked v1 plans close as superseded. v1 stays at tag v1. Reason: v1's rules and AGENTS.md load into every session in this repo and would steer v2 build agents toward v1 contracts."
- Build beside v1, remove last — "v1 stays runnable during the build and goes in the last stage. Two designs coexist on main, and v1's rules keep loading into every build session."
Answer: Remove v1 first

### stages
Question: "In what order are the parts built?"
- Thin usable stages (Recommended) — "1 Cutover plus plugin shell. 2 Store (full schema), config, reply/exit seam, `status`, omp-gateway and Jev clients, `atlas-init` without the test search. 3 `add` and `inbox`. 4 `find` and `ask` (query records, tally lines) plus atlas-init's test search: the first usable Atlas. 5 `note`, `archive`, `restore`. 6 `topic`, `plan`, `find --wide` and Reconcile in atlas-ask. 7 The `atlas-research` rule. Each stage ends with a smoke run through the atlas-ask skill."
- CLI first, skills last — "Build all ten commands, then write the atlas-ask and atlas-init skills on top. Less skill rework, but nothing is usable end to end until the end."
Answer: Thin usable stages, with this note, given exactly:

````text
also take this into account as well: add this to the relevant ticket for this repo's map:

prompt:

```
is this the final ticket? i would like to add another task where it compares quality and cost between these models on various topics during summarization external sources, but weighted more on code-related: sonnet5.5:medium vs. sonnet5.5:high vs. opus5.5:medium. If quality is relatively similar across all summaries for models that cost less, then let's go with the more cost efficient model.
```

response:

```
No, it's not the last ticket. After ticket 06 closes, the map still has:

- **Decide Atlas build order** (ticket 07). It's also waiting on the Skill plugins release map.
- **Open items not yet turned into tickets:** how to judge quality, source identity with Jev's flags, and plugin linking and release.

Your comparison fits as a new prototype ticket, like tickets 08 and 11. I can add it to the map when I close 06. The draft:

- **Title:** Prototype summary model quality vs cost.
- **Models:** Sonnet 5.5 at medium, Sonnet 5.5 at high and Opus 5.5 at medium.
- **What runs:** each model summarizes the same external sources from several topics, with more weight on code-related ones.
- **What's measured:** quality, cost and time for each summary.
- **Rule:** if quality is about the same, pick the cheapest model.
- **Changes:** only the default for `atlas_summarize`. The ticket 06 decision currently starts every role at Opus medium, so this is a model setting, not an architecture change, and ticket 06 doesn't need reopening.

Two things to settle when the ticket is grilled:

- **How quality gets judged.** Options: a blind side-by-side review by a model, your own spot checks, or both. This overlaps the open "quality judging" item on the map, so the ticket could settle a narrow version of it.
- **Whether it runs before ticket 07.** It probably should, so the build starts with the right default model. It's cheap either way, because roles are config.

When you reply **confirm**, also say "add the summary model ticket", and I'll create it with ticket 06's closing changes.
```
````

### real_data
Question: "When does Atlas start holding real sources, and how does the schema change after that?"
- From stage 4, with migrations (Recommended) — "Stage 2 creates the whole schema. Real sources go in once `find` and `ask` work. Any later schema change is a numbered migration (SQLite user_version), so nothing is lost. host-backup already covers the store."
- From stage 4, wipe allowed — "Same start, no migration code until v2 is complete; a schema change recreates the store. Sources are re-added from their links, which costs new summary calls."
- Only after stage 7 — "Throwaway stores during the build, real use starts when everything is built. No migrations, but no real use for the whole build."
Answer: From stage 4, with migrations

### link
Question: "When is the atlas plugin linked on g10?"
- Link in stage 1 (Recommended) — "`omp plugin link ~/dev/atlas` in stage 1, as dotagents did, so `skill://atlas-ask` and the bundled CLI path work from the first smoke run. How Atlas is released and installed on other machines (tags, Mac) becomes its own map ticket."
- Link at the end — "Build and test through the CLI's repo path; link when v2 is complete. The skill's `realpath skill://atlas-ask` pattern is untested until then."
Answer: Link in stage 1

### identity
Question: "The map's open item on source identity (canonical link rules, e.g. X `s=` params, content hash, Jev near-duplicate flags) feeds `add` and the sources table. When is it decided?"
- New ticket, before the spec (Recommended) — "A grilling ticket on this map, decided before the spec is written, because stage 2's schema and stage 3's `add` depend on it."
- In the spec route — "No map ticket; the spec route decides it. Fewer sessions, but the spec carries an open design question."
Answer: New ticket, before the spec

### quality
Question: "Where does the quality check (pooled Jev grading plus your spot check, run by hand, read-only) fit?"
- New ticket, built after stage 4 (Recommended) — "A ticket on this map decides its form before the spec. It is built right after the first usable Atlas, so later tuning (abstract, rerank, answer prompts, claim labels) is measured."
- New ticket, built after stage 7 — "Same ticket; built once v2 is complete. Tuning during the build is judged by smoke runs and spot checks only."
- Out of scope for v2 — "No quality check in v2; it returns as a later effort."
Answer: New ticket, built after stage 4

## Round 2

Shown before round 2: "Round 1 is settled. I'll add your summary-model comparison as a new prototype ticket when this ticket closes, as the draft you quoted describes. Its own grilling decides how it judges quality."

### summary_model
Question: "When must the new 'Prototype summary model quality vs cost' ticket resolve, relative to the build?"
- Before real data (stage 4) (Recommended) — "Stages 1–3 can start without it, because `atlas_summarize` is only a model-role setting. It must resolve before real sources go in at stage 4, so stored summaries come from the chosen model from the first real row."
- Before the spec — "The map stays open until it resolves, and the spec states the measured default. Delays the spec by one prototype session."
- Any time — "No ordering. Sources added before it resolves keep their Opus-written summaries (each records its model)."
Answer: Before real data (stage 4)

### release
Question: "Linking is settled (stage 1 on g10). The rest of the map's open item on plugin release (tags, installing on the Mac, any catalog entry) becomes a new ticket. When must it resolve?"
- Before the spec (Recommended) — "A small grilling ticket on this map, so the spec covers the whole lifecycle, including the plugin metadata created in stage 1. Atlas is its own plugin repo, so dotagents' export hook does not apply."
- Before the last stage — "The spec leaves release open, and the ticket resolves during the build. The map can close sooner, but the spec has a known gap."
- Out of scope — "v2 runs only on g10 through the link; release returns as a later effort."
Answer: Before the spec

## Reconcile approval and confirmation

Brief approval (2026-11-08), given exactly: "approve - dotagents version has been updated. adjust accordingly." Main updated the candidate and the facts from dotagents v0.4.1 to v0.5.1 (newest tag on 2026-11-08) and omp 18.16.0 to 18.18.0 before the run.

After the run ([record](07-reconcile-record.md)), shown with the front and this note: "One change touches your summary-model answer. You chose "Before real data (stage 4)" over "Before the spec — the map stays open until it resolves". A map closes only when it has no open tickets, so the reviewers moved the open prototype to the spec route."

### prototype_tracking
Question: "How is the summary-model prototype tracked once the other map tickets close?"
- Accept the reviewers' change (Recommended) — "The ticket is created on this map now, so it can run in a parallel session. If it is still open when the map's other tickets close, the map closes it as passed on, and the spec route carries it as a gate before real sources go in at stage 4. This matches your round-2 choice that the spec does not wait on it."
- Keep it a plain map ticket — "The map stays open until the prototype resolves, so the spec waits on it. That is the 'Before the spec' timing you turned down in round 2."
Answer: Accept the reviewers' change

### confirm
Question: "Confirm the reconciled summary above (prerequisites met at dotagents v0.5.1; four new map tickets; eight stages, first usable at stage 4; real sources from stage 4 with migrations) so 'Decide Atlas build order' closes?"
- Confirm (Recommended) — "Close 'Decide Atlas build order' with the final proposal in the record, add the four new tickets and update the map."
- Change something — "Say what to change; the ticket stays open."
Answer: Confirm
