---
name: atlas
description: Route one free-form Atlas request to an expert owner; non-Atlas input has no owner and never selects atlas itself.
disableModelInvocation: true
---

# atlas

## Read first

1. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`


## Hard boundary

Invocation through `/atlas` is not Atlas intent. Never return `atlas` as `first_owner`. Before considering a material choice, short-circuit a request with no Atlas action target to no owner, no Ask, and an empty router write set.
## Contract

Accept one free-form request. Produce exactly one outcome:

1. Load exactly one existing owner skill with the unchanged request and any answered material choice.
2. Use Ask once for one unresolved material choice.
3. Report that no Atlas owner applies.

Do not call `scripts/atlas_tool.py`, inspect a profile or vault state, construct projections, synthesize, retry or recover a workflow, translate an Ask answer into reducer authority, or chain owners. Report child-owned successor requirements without appending a refresh or answer.

## Classification-only output

When asked to classify without executing a child, return `first_owner`, `ask_required`, and `router_write_set`. `first_owner` is the selected expert `atlas-*` owner or `null`; the `/atlas` router is never its own owner. A non-Atlas request returns `first_owner: null`, `ask_required: false`, and `router_write_set: []`.
A request is Atlas intent only when it asks to read or mutate Atlas state or invokes a named Atlas operation. Generic repository, code, configuration, shell, or file edits are non-Atlas even when invoked through `/atlas`; return `first_owner: null`, `ask_required: false`, and `router_write_set: []`.

## First-owner matrix

| Request signal | First owner |
|---|---|
| Explicit URL, repository, or file; evidence capture; staged promotion; resummarization | `skill://atlas-source` |
| Bounded feed, watchlist, inbox, repository list, author list, or query | `skill://atlas-acquire` |
| Source ID or bounded reroute | `skill://atlas-route` |
| Read, show, or answer a current topic | `skill://atlas-answer` |
| Synthesize, research, or rebuild a topic | `skill://atlas-research` |
| Apply pending evidence or refresh a topic | `skill://atlas-refresh` |
| Health, schema, quality, or calibration inspection | `skill://atlas-audit` |
| Explicit vocabulary promotion, topic-shell creation, or named supported registry repair | `skill://atlas-index` |
| Explicit old-to-new Markdown schema migration with target scope | `skill://atlas-migrate` |
| Non-Atlas request | No Atlas owner, capability claim, or vault action |

Keep research vault-only unless acquisition is explicit. When a request mentions multiple outcomes, select only its first explicit requested effect. Preserve existing source→route, acquire→source, research `--acquire`→acquire, freshness, repair, and migration gates inside their owners.

For an answer-plus-conditional-refresh ambiguity, Ask before selecting an owner: offer `answer-with-freshness-gate` and separately authorized dirty-topic refresh; recommend `answer-with-freshness-gate`. The answer path remains no-write and halts if stale.
