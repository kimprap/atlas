Type: grilling
Parent: [Atlas v2](../map.md)
Blocked by: 01, 02, 03, 08, 09, 11

## Question

What is the Atlas v2 architecture? Decide the MCP server tools, the storage, which model writes the summaries (the calling agent or Atlas itself), how discovery sources such as `last30days` plug in, how Atlas calls Reconcile for research plans and proposed revisions (an optional capability, with a fallback so Atlas works without it), whether research is broken into tasks with a separate plan step, and the boundary that keeps later cloud hosting cheap.

Retrieval inputs from [Prototype retrieval on real summaries](08-prototype-retrieval-on-real-summaries.md) to decide here:

- The retrieval stack's open parts. The default is already set by the map's standing decision on Atlas models: BM25 plus `atlas_query` rewriting plus `atlas_rerank`, with no vectors. Still open: the fallback when a role is missing or fails, and the shape of the optional embedding add-on. Jev is a candidate reranker or fallback; the [map's standing decision on the Jev decision model](../map.md) (2026-10-29) makes it the default reranker only after test runs against Opus ([Jev decision model research](../inputs/jev-decision-model-research-2026-10-29.md)).
- How the `atlas_summarize` role is called. The map's standing decision on Atlas models says summaries come from that role, not from whatever model the calling agent is running.
- Whether the stored record keeps a short TL;DR-style abstract or reuse cues for search.
- How topic creation gathers candidate sources wider than a top-10 search.

Lessons from v1 to respect (from [Atlas v1 notes](../inputs/atlas-v1-notes.md), note 3):

- One bad source must never block every search.
- Every error names the source and field at fault.

Input from [Decide repo and catalog layout](~/.dotfiles/.scratch/atlas-and-skill-plugins/issues/04-decide-repo-and-catalog-layout.md): Atlas is its own plugin, `atlas`, in `kimprap/atlas`. It reaches Reconcile through `skill://reconcile` from the `dotagents` plugin, whose controller lives in the `reconcile` skill folder. The fallback when `dotagents` isn't installed is still decided here.

Input from [Decide source credibility weighting](09-decide-source-credibility-weighting.md), still decided here:

- Where trust notes and the trust-evidence tally are stored and edited, and the tally's line count.
- Whether answers and revisions are written by the calling agent or an Atlas role, and so which model each answer and saved version records.
- What runs the fail-closed check of the Sound, Doubtful and Noise labels.
- How Atlas hands a draft revision, with its labels and Model view, to Reconcile after the user chooses to save. Atlas shows Reconcile's marked changes as given, not re-summarised.

Input from the [map's standing decision on the Jev decision model](../map.md) (2026-10-29) and [Jev decision model research](../inputs/jev-decision-model-research-2026-10-29.md), still decided here: live Jev calls from Atlas (a Jev reranker or fallback, claim-support flags and near-duplicate flags) run out of process, because omp extensions have no judge call, and so need a direct provider credential. The user decides here whether Atlas gets that credential and how it is kept, under the map's standing rule on secrets. Also decided here: whether Atlas's setup skill runs one test judgment through the real rerank path and reports which model answered and the fallback in use.
