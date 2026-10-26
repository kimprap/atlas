Type: grilling
Parent: [Atlas v2](../map.md)
Blocked by: 06
Also blocked by: the [Skill plugins release](/Users/kim/.dotfiles/.scratch/skill-plugins/map.md) map being resolved, since Atlas builds on `dotagents`.

## Question

In what order is Atlas v2 built, and which parts depend on the `dotagents` plugin release? Known constraint: the skill plugins ship before any Atlas release that relies on Reconcile.

Input from [Decide source credibility weighting](09-decide-source-credibility-weighting.md): after a save, Atlas shows what Reconcile changed compared with the draft. The user will add that diff to the Reconcile skill in a separate session, and it must land before Atlas relies on it.

This ticket was "Decide build order" until 2026-10-22, when the plugin release moved to its own map. The plugin half of its question went to [Decide plugin build order](/Users/kim/.dotfiles/.scratch/skill-plugins/issues/04-decide-plugin-build-order.md).
