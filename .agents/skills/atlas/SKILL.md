---
name: atlas
description: Present one generic Atlas request as an approval-gated first-owner route; non-Atlas input has no owner.
disableModelInvocation: true
---

# atlas

## Read first

1. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`


## Hard boundary

Invocation through `/atlas` is not Atlas intent. Never return `atlas` as `first_owner`. Before considering a material choice, short-circuit a request with no Atlas action target to no owner, no approval, no Ask, and an empty router write set. Direct `/atlas-*` invocation bypasses this router gate.

## Contract

Accept one free-form request. Empty arguments ask for the Atlas goal. An explicit classification-only request uses the output below and executes no child.

If an unresolved material choice changes the owner, scope, write set, destructive effect, or authority, use the host Ask once before presenting a route. The choice answer selects the route but does not approve dispatch.

For an actionable initial request:

1. Classify exactly one existing `skill://atlas-*` owner without loading it.
2. Render exactly:

   ```text
   Goal: <one-sentence interpretation of the unchanged request>
   Next: <one selected skill://atlas-* owner and its first bounded action>
   Effect: <“read-only; no Atlas writes” or “write-capable through the selected owner; exact effects remain owner-gated”>

   Approve this Atlas route?
   ```

3. Halt with no child dispatch.

For a pure source-presence or explicit-URL route-status request, `Next` says `skill://atlas-source` will normalize the URL and inspect its canonical source-manifest row. Use `Effect: read-only; no Atlas writes` for source presence, manifest-backed route-status-only, `atlas-answer`, and `atlas-audit` requests. Use `Effect: write-capable through the selected owner; exact effects remain owner-gated` for source ingestion or resummarization, acquisition, rerouting, research, refresh, index, and migration. The effect line discloses capability; it does not authorize mutation.

A status-only request naming only a source ID is Atlas intent but has no executable owner: `source.lookup` requires a raw URL, while `atlas-route` owns rerouting rather than status queries. Request the canonical URL without rendering an overview or dispatching a child. In classification-only output return `first_owner: null`, `ask_required: false`, and `router_write_set: []`; never reinterpret status as rerouting.

Accept only an unambiguous affirmative tied to the immediately preceding unchanged overview. After approval, load exactly the selected owner with the original unchanged request and any separately answered material choice, then exit the router. Never forward the approval reply as the child request, add a second router gate, or chain another owner.

A changed constraint, caveat, different request, silence, or ambiguous reply invalidates the pending overview. Reclassify and render a replacement instead of dispatching. In particular, `Approved, but resummarize it` is a changed write-capable request, not approval of a read-only presence route.

Do not call `scripts/atlas_tool.py`, inspect a profile or vault state, construct projections, synthesize, retry or recover a workflow, translate approval or an Ask answer into reducer authority, or chain owners. Report child-owned successor requirements without appending a refresh or answer.

## Classification-only output

When asked to classify without executing a child, return `first_owner`, `ask_required`, and `router_write_set`. `first_owner` is the selected expert `atlas-*` owner or `null`; the `/atlas` router is never its own owner. `ask_required` means an unresolved material choice only; it does not encode the routine runtime dispatch approval because this probe cannot dispatch.

A non-Atlas request returns `first_owner: null`, `ask_required: false`, and `router_write_set: []`. A request is Atlas intent only when it asks to read or mutate Atlas state or invokes a named Atlas operation. Generic repository, code, configuration, shell, or file edits are non-Atlas even when invoked through `/atlas`.

## First-owner matrix

| Request signal | First owner |
|---|---|
| Pure source-presence or manifest-backed source- or route-status question for explicit URL(s) | `skill://atlas-source` |
| Explicit URL, repository, or file ingestion; evidence capture; staged promotion; resummarization | `skill://atlas-source` |
| Bounded feed, watchlist, inbox, repository list, author list, or query | `skill://atlas-acquire` |
| Status-only request naming only a source ID | No owner until the canonical URL is supplied; never widen to rerouting |
| Explicit reroute for one source ID or bounded source range | `skill://atlas-route` |
| Read, show, or answer a current topic | `skill://atlas-answer` |
| Synthesize, research, or rebuild a topic | `skill://atlas-research` |
| Apply pending evidence or refresh a topic | `skill://atlas-refresh` |
| Health, schema, quality, or calibration inspection | `skill://atlas-audit` |
| Explicit vocabulary promotion, topic-shell creation, or named supported registry repair | `skill://atlas-index` |
| Explicit old-to-new Markdown schema migration with target scope | `skill://atlas-migrate` |
| Non-Atlas request | No Atlas owner, capability claim, or vault action |

Keep research vault-only unless acquisition is explicit. When a request mentions multiple outcomes, select only its first explicit requested effect. Preserve existing source→route, acquire→source, research `--acquire`→acquire, freshness, repair, and migration gates inside their owners.

For an answer-plus-conditional-refresh ambiguity, Ask before selecting an owner: offer `answer-with-freshness-gate` and separately authorized dirty-topic refresh; recommend `answer-with-freshness-gate`. The answer path remains no-write and halts if stale. After that material choice, render the selected route overview; the choice answer is not dispatch approval.
