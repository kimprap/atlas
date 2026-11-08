Type: grilling
Parent: [Atlas v2](../map.md)
Blocked by: 16

## Question

What form does Atlas's quality check take? It is run by hand, read-only, compares an old and a new version, and has no scheduling ([Atlas v1 notes](../inputs/atlas-v1-notes.md), note 1). The [map's standing decision on the Jev decision model](../map.md) (2026-10-29) makes pooled Jev grading plus the user's spot check the method, as tested in [Prototype retrieval on real summaries](08-prototype-retrieval-on-real-summaries.md) and [Prototype Jev reranking on real summaries](11-prototype-jev-reranking-on-real-summaries.md). Decide what it judges (summaries, search results, answers), the query set and graded pool it starts from, how it reuses the summary rubric and add-time claim checks from [Decide source summarization method](16-decide-source-summarization-method.md), and how it tells whether the Sound, Doubtful and Noise labels and backing counts from [Decide source credibility weighting](09-decide-source-credibility-weighting.md) help.

Changed on 2026-11-08: how Jev's claim-support flags work (left here by [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md), section 5) moved to [Decide source summarization method](16-decide-source-summarization-method.md), which checks claims when a source is added; this ticket waits on it.

Its form is decided before the spec; it is built in stage 5, right after the first usable Atlas, so later tuning is measured ([Decide Atlas build order](07-decide-atlas-build-order.md)). [Prototype summary model quality vs cost](15-prototype-summary-model-quality-vs-cost.md) judges summary quality in its own narrow way and may serve as evidence here.
