Type: grilling
Parent: [Atlas v2](../map.md)

## Question

How does `atlas_summarize` turn a page's text into the stored record reliably enough that a cheaper model can do the work? Decide the method, not the model:

- what guides the model (a checklist or rubric, a fixed output shape);
- what Atlas checks in code after the call (for example, that each claim's locator points at text that is really on the page);
- whether a second pass pays for itself (the same model rechecking its own work, a different checker such as Jev's claim-support flags, or none), and what it checks;
- what `add` does when a check fails (retry, store with a marker, or stop with nothing stored).

Settled inputs, not reopened here: the stored record's fields and the page-only rule ([Define Atlas v2 requirements](02-define-atlas-v2-requirements.md), stored record); summaries come from the `atlas_summarize` role in Atlas's own call, with a neutral 1–2 sentence abstract ([Decide Atlas v2 architecture](06-decide-atlas-v2-architecture.md), sections 5 and 6). Under the [map's standing decision on the Jev decision model](../map.md) (2026-10-29), Jev may only flag claims for the agent or the user to read; the locator check stays deterministic.

Evidence to weigh: v1's summary machinery (quality guide, checklist, worker and proposal schemas, eval set under `.agents/skills/atlas-core/assets/` at tag `v1`) and what the v1 plans learned from it; [Prototype retrieval on real summaries](08-prototype-retrieval-on-real-summaries.md) and [Prototype Jev reranking on real summaries](11-prototype-jev-reranking-on-real-summaries.md).

The user's request, quoted exactly (2026-11-08):

> Additionally, has the source summarization mechanic been decided? I'd like to refine it first before the above inquiry is executed. Generally, the idea is, i'd like to have a robust framework where agents could perform source extraction and summarization deterministically. This would allow us to use less capable models to execute the task, thereby saving tokens cost. something like a checklist/rubric of things agents should take into account,  an engine to validate the summarization work(?), or similarly to dev-impl, a 2nd pass on the same agent to "rethink", for atlas, specifically passing a "rethink" might not be appropriate, but evaluate if the mechanic of a 2nd pass would be beneficial or not. For rethink, it is a simple 2nd pass that primarily it used to make sure agents do not hallucinate, albeit 2nd guessing the same agent in the same session, etc. These are just some example mechanic of the said robust framework. I expect you to suggest alternatives, preferably a more intelligent one. THis is merely my rough initial thoughts.

"The above inquiry" is [Prototype summary model quality vs cost](15-prototype-summary-model-quality-vs-cost.md), which now waits on this ticket. The user asked for alternatives to these examples; the grilling brings them with evidence.

Decided before the spec, because build stage 3's `add` depends on it ([Decide Atlas build order](07-decide-atlas-build-order.md)). This ticket owns the add-time claim checks, including Jev's claim-support flags at add time; [Decide quality check](13-decide-quality-check.md) keeps the hand-run check and reuses this ticket's rubric and checks.

Input from [Decide source identity](12-decide-source-identity.md) (section "Passed on"): the update method that revises only the claims affected by a page's changed parts; claim locators that point at the stored page text, which identity's change check relies on; choosing which author replies continue an X post; and, as evidence for this ticket's token-cost aim, the page text reaches `add` through the calling agent's context today. Settled there and not reopened here: the cleaned page text is stored, a changed page gets a check in code before any model call, and a re-add never updates on its own.
