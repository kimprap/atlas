# Handoff: dotfiles changes to build before the Atlas v2 redesign continues

## Outcome
- [Decide Atlas v2 architecture](../issues/06-decide-atlas-v2-architecture.md) is resolved (2026-11-02). It passes five dotfiles tasks to the user, who asked to build them first: "don't forget the handoff for tasks i should impl first in dotfiles before we proceed with the redesign".
- Planning only: this Handoff authorizes no implementation. Each task goes through `dev-ask` in `~/.dotfiles`, which picks the route and gets approval.
- Suggested order: 1 (small and self-contained), 2 and 3 (both Reconcile controller work, so plan them together), 4, then 5 (a check only).

### 1. host-backup copies the Atlas stores
- Need: Atlas v2 keeps one SQLite database per profile at `~/.local/share/atlas/<profile>.db`. Atlas has no backup code; host-backup covers the stores, and this lands before Atlas holds real data. The user's answer (round 4, `backup2`): "host-backup copies it safely … add this to the list of tasks for the handoff that i will continue from the dotfiles repo."
- Where: `~/.dotfiles/.config/scripts/host-backup`.
  - `stage_databases` (lines 117–137) copies each live `*.db` under `~/.omp/agent` with SQLite's online backup API into `$DB_STAGE/<path relative to $HOME>`, in rollback-journal mode.
  - `backup_paths` (139–150) does not include `~/.local/share/atlas`.
  - `backup_excludes` (152–158) skips raw `*.db*` files only under `~/.omp/agent`.
- Change: stage `~/.local/share/atlas/*.db` the same way, into the same `$DB_STAGE` and the same restic repository on Drive (`dev-backups/machines/<host>/restic`, every 4 hours, same retention). No raw live database bytes enter the snapshot. Nothing breaks when the folder does not exist yet.
- Acceptance: with a throwaway `~/.local/share/atlas/test.db`, one backup run leaves `$DB_STAGE/.local/share/atlas/test.db`, which opens and passes `PRAGMA integrity_check`. The snapshot holds no `-wal`, `-shm` or raw copy of it. A run with no `~/.local/share/atlas` still succeeds.

### 2. Reconcile shows a diff of the reviewed text
- Need: from [Decide source credibility weighting](../issues/09-decide-source-credibility-weighting.md), Passed on: "the Reconcile skill gains a diff of the reviewed text against the original (the user will build it in a separate session); it lands before Atlas relies on it." After a save, Atlas shows what Reconcile changed, as given and not re-summarized.
- Today the front's **Changes** field is reviewer-written bullets plus one computed line (`Summary: unchanged · Details: edited`); there is no marked diff of the text.
- Open in its route: the diff's form (marked words or lines), where it appears (record, front, or a separate output Atlas can read), and how a caller gets it without parsing the front.

### 3. Reconcile accepts Atlas as a trusted caller
- Need: Atlas's `atlas-ask` skill runs Reconcile on a research plan, and on a draft topic revision when the user says yes to saving it. The approval is the user's own words (the research request, or the "yes"), so Atlas shows no Reconcile brief. Atlas stores the reviewed text, the reviewer models, the run and Reconcile's Changes.
- Today:
  - The trusted-caller allowlist is exactly `retrace` (`skills/reconcile/references/controller-contract.md` lines 18–25; `acp-controller/controller.mjs` line 1115: "Caller must be exactly `retrace`").
  - Delegated entry exists only in process inside a Retrace run. The controller CLI has no delegated `reconcile` entry.
  - Direct entry needs a rendered brief and the `{text, at}` approval.
- Open in its route: how Atlas is admitted (a new allowlisted caller, or a documented pre-approved direct run whose approval text is the user's words), what Atlas must send, and a cheap check Atlas can run so it can mark work "not cross-checked: <reason>" when Reconcile is missing or refuses, for example after an omp update breaks the version pin.

### 4. A fixed trigger for "proceed without yielding"
- Need: the user reports mixed results from free-form pre-approval wording. They want a semi-fixed trigger format, with clear scenario rules, for Reconcile and for `dev-ask` route overviews.
- Today:
  - Reconcile `SKILL.md` lines 273–297 accept any explicit pre-approval, with the example "Once reconcile brief is ready, you may proceed with the execution. Yield none. This message serves as that approval.", and list when a pre-approved run still stops.
  - `dev-ask` `SKILL.md` "Compact approval presentation" (line 164) decides whether a route starts without another approval.
- The user's example scenarios, in a dev-workflow continuation:
  - "yield only after Reconcile" means stop once Reconcile returns.
  - "no yields for all" means go straight on to dev-workflow implementation after Reconcile returns.
- A data point from this session: "reconcile without yield" was read as skipping only the brief's approval stop. Main then stopped after the run for the grilling confirm, which a grilling interview requires. A fixed format should say which stops a trigger skips and which it never skips.

### 5. Check the dotagents spec for Atlas setup
- Ticket 06 changes [Decide shipped skills and personal layer](~/.dotfiles/.scratch/atlas-and-skill-plugins/issues/05-decide-shipped-skills-and-personal-layer.md): `init-ask` no longer sets up Atlas through Atlas's settings registry (decision 9), because Atlas's own `atlas-init` does. Atlas has four roles, not three (decision 4).
- Today `skills/init-ask` has no Atlas mention, and `settings-registry.json` lists only dotagents settings. So nothing needs changing now, but the [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md) specification route must not add Atlas registry handling to `init-ask`.

## Changed targets/effects
- none in `~/.dotfiles`. This Handoff is a file in `~/dev/atlas/.scratch/atlas-v2/handoffs/`.

## Checks
- Facts above read on 2026-11-02 at dotfiles `fd436e7` with a clean working tree: host-backup lines 117–158; controller-contract lines 18–25; controller.mjs line 1115; Reconcile SKILL.md lines 273–297; dev-ask SKILL.md line 164; no Atlas match under `skills/init-ask`, `skills/reconcile` or `skills/dev-research`.
- No task here has been built or run.

## Blocker/risk
- High: Atlas relies on tasks 1–3. Task 1 must land before Atlas holds real data, and tasks 2 and 3 before Atlas runs Reconcile. [Decide Atlas build order](../issues/07-decide-atlas-build-order.md) records this.
- Low: tasks 2 and 3 change the Reconcile controller, which is pinned to omp/18.15.0, acpx 0.21.1 and SDK 1.9.0 and has an offline suite. Plan them together, so the controller changes once.

## Next receiver
- The user's next `~/.dotfiles` session, running `dev-ask` on this Handoff.
