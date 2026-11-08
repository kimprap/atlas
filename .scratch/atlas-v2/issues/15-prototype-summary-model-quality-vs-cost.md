Type: prototype
Parent: [Atlas v2](../map.md)

## Question

Which model should `atlas_summarize` start at? Sonnet 5.5 at medium, Sonnet 5.5 at high and Opus 5.5 at medium each summarize the same external sources from several topics, weighted towards code-related ones. Measure quality, cost and time per summary. The user's rule: "If quality is relatively similar across all summaries for models that cost less, then let's go with the more cost efficient model." (quoted from the user's note in [the ticket 07 interview](../reviews/07-interview.md), round 1, stages).

To settle when this ticket is grilled: how quality is judged (a blind side-by-side review by a model, the user's own spot checks, or both). Under `rule://decision-model`, a model may rank or flag but never decides; the user's rule above decides.

It changes only the `atlas_summarize` default, which [Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md) starts at `anthropic/claude-opus-5-5:medium`. The spec does not wait on it, but it must resolve before real sources go in at build stage 4. If it is still open when the map's other tickets close, the map closes it as passed on and the spec route carries it as that gate ([Decide Atlas build order](07-decide-atlas-build-order.md)).
