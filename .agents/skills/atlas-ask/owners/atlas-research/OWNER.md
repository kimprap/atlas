# atlas-research

## Qualification

Execute this resource only when the same agent has selected `atlas-research` through `/atlas-ask` and bound one mode, the unchanged request, retained material answers, and any approved Goal/Effect boundary. Any other load performs no further read, model work, façade call, profile or vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

This owner executes end-to-end in the current agent. Its refresh and topic-creation procedures are in process and emit no owner result. Only this outer owner returns the seven-field result defined by `atlas-workflow-result.schema.json`.

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/SKILL.md`
3. `skill://atlas-core/assets/agent-cli-recipes.md`
4. `skill://atlas-core/assets/research-library-templates.md`
5. `skill://atlas-core/assets/markdown-registry-contracts.md`

Discover the lifecycle surface with `python3 scripts/atlas_tool.py capabilities`. Use generated family/verb commands with one operation-args object, or the low-level call with the exact version-2 request envelope. Decode only the version-2 response envelope. Never import a domain module, resolve a host path, or reproduce topic identity, inspection binding, projection, transaction, or recovery mechanics.

## Modes

| Mode | Approval already bound | Scope |
|---|---|---|
| `answer` | No | Read-only answer from one purpose-bound topic inspection. |
| `research` | One Goal/Effect approval | Publish one research pass from an eligible inspection. |
| `refresh` | One Goal/Effect approval | Resolve existing pending evidence and stop. |
| `create` | One Goal/Effect approval | Create one topic under an existing domain/subdomain. |

Reject a mode or effect wider than the bound request. Topic ambiguity must have been resolved by at most one batched pre-approval clarification; post-dispatch material scope starts a new `/atlas-ask` invocation.

## Answer

Call `topic.inspect` once with purpose `answer`. Use only its managed topic sections, freshness state, and stable pending edge IDs.

- A current, zero-pending inspection may be answered as current and returns `effect: none`.
- A valid dirty topic returns `outcome: no-write`, `effect: none`, the managed topic content, an explicit dirty/stale warning, and the pending edge IDs. State clearly that the content is not current.
- An absent, orphaned, malformed, stale-binding, refreshing, blocked, or otherwise invalid inspection stops with the exact finding and no partial context.

Answer mode never invokes a refresh procedure, transaction, recovery, mutation, or write. It never hides staleness or turns an answer into research.

## In-process refresh procedure

Use this procedure only for approved `research` eligibility work or standalone `refresh`:

```text
topic.inspect with purpose refresh
  → draft one pass and topic-index candidate from that bounded snapshot
  → topic.inspect with purpose refresh immediately before the effect
  → refresh.execute
  → refresh.recover only with the exact original projection and candidate bytes when required
```

Require the immediate reinspection to bind the same topic and exact pending edge set expected by the refresh request. The façade owns start/complete transitions, ordered edge application, freshness derivation, journal, acknowledgement, and recovery. Never hand-author a reducer event, patch a registry, rebase the draft, or recover changed bytes.

A standalone `refresh` invocation stops after the terminal refresh receipt. It never continues into research publication.

## Research

1. Call `topic.inspect` with purpose `research`.
2. If the state is `dirty|refreshing|blocked`, run the in-process refresh procedure, then call `topic.inspect` again with purpose `research`.
3. Require the new inspection to be `current` with zero pending edge IDs. Never use the pre-refresh inspection for research preparation.
4. Draft only from the bounded research payload and templates. Record insufficiency rather than adding unbound evidence.
5. Call `research.prepare` with the current inspection binding and exact staged pass, topic index, and subdomain index bytes.
6. Pass the exact prepared request to `research.execute`; use `research.recover` only with that byte-identical original request when required.

The research reducer alone derives `TOPICS.md`. The ordered target set remains pass, topic `INDEX.md`, subdomain `INDEX.md`, then `TOPICS.md`; research never alters pending edges, writes a fifth target, or repairs unrelated state. Call a sole successor only when the façade exposes it through the research recovery contract.

## Create

Call `topic.inspect` for the requested topic and require an exact absence finding under the approved existing domain/subdomain. A conflicting, malformed, orphaned, or already-present topic is not absence.

For proven absence, call `index.create_topic` with the approved semantic identity request. The façade owns validation, rendering, target order, revisions, transaction, acknowledgement, and post-validation. If the attempt is recoverable, call `index.recover_topic` only with its exact transaction identity and byte-identical original request.

Create never synthesizes research or creates vocabulary, domains, subdomains, sources, relations, passes, aliases, or additional topics. It never uses a generic source/route transaction or direct conditional replacement.

## Resume ceiling

This owner may return `needs-guidance` once and has a maximum of two owner turns. Guidance may resolve only semantics inside the unchanged approved Goal/Effect from already-bound contracts or conversation evidence. Repeated guidance, a short cycle, Atlas-state inspection by the front door, a wider effect, or an exhausted ceiling is `blocked`. There is no post-dispatch `needs-user` resume.

## Result and recovery

Return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, with `owner: atlas-research`. Use only schema-defined outcome/effect pairs. Prepare, answer, and every observed no-write path use `effect: none`.

`partial|unknown` always returns `outcome: blocked`; copy only the exact façade-returned `{operation,identity}` into `next`. Never infer success, retry hidden work, broaden recovery, or expose a recovery path for an effect that did not return one. Otherwise `next` is `null`.