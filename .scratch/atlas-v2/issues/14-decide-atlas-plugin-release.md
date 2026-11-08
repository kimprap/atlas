Type: grilling
Parent: [Atlas v2](../map.md)

## Question

How is the `atlas` plugin released and installed beyond g10? Decide tags, installing on the Mac, and any catalog entry. Linking on g10 is settled: `omp plugin link ~/dev/atlas` in build stage 1 ([Decide Atlas build order](07-decide-atlas-build-order.md)). Atlas is its own plugin repo (`kimprap/atlas`), so dotagents' export hook does not apply; build on the release and bootstrap decisions in [Skill plugins release](~/.dotfiles/.scratch/skill-plugins/map.md) (private repo, git installs from `main`, a shipped extension that upgrades daily, no catalog) where they fit.

Decided before the spec, so the spec covers the whole lifecycle, including the plugin metadata created in stage 1.
