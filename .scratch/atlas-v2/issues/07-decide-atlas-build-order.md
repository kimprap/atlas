Type: grilling
Parent: [Atlas v2](../map.md)
Blocked by: 06
Also blocked by: the [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md) map being resolved, since Atlas builds on `dotagents`.

## Question

In what order is Atlas v2 built, and which parts depend on the `dotagents` plugin release? Known constraint: the skill plugins ship before any Atlas release that relies on Reconcile.

Input from [Decide source credibility weighting](09-decide-source-credibility-weighting.md): after a save, Atlas shows what Reconcile changed compared with the draft. The user will add that diff to the Reconcile skill in a separate session, and it must land before Atlas relies on it.

Input from [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md): three dotfiles changes land before Atlas relies on them, and the user plans to build them first in the dotfiles repo (Handoff of 2026-11-02):

- dotagents' Reconcile gains a trusted-caller entry for Atlas, as Retrace has, so the `atlas-ask` skill can run Reconcile with the user's own words as approval.
- The Reconcile diff above.
- `host-backup` copies `~/.local/share/atlas/*.db` with its SQLite online-backup step, before Atlas holds real data.

The architecture also sets the build's shape: a fresh v2 on main that keeps only `atlas_url.py` and the CLI's JSON input and exit handling, and removes the v1 runtime, owners, scaffold, instance tooling, command stub and v1 `ARCHITECTURE.md` in the cutover.

This ticket was "Decide build order" until 2026-10-22, when the plugin release moved to its own map. The plugin half of its question went to [Decide plugin build order](~/.dotfiles/.scratch/skill-plugins/issues/04-decide-plugin-build-order.md).
