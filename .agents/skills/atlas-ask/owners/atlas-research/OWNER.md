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
| `research` | One Goal/Effect approval | Publish one research pass; if the topic is absent, create it with any missing compatible domain/subdomain vocabulary rows and subdomain index in process. |
| `refresh` | One Goal/Effect approval | Resolve existing pending evidence and stop. |
| `create` | One Goal/Effect approval | Create one topic with any missing compatible domain/subdomain vocabulary rows and subdomain index in the same transaction. |

Reject a mode or effect wider than the bound request. Topic ambiguity must have been resolved by at most one batched pre-approval clarification; post-dispatch material scope starts a new `/atlas-ask` invocation.

For `create`, or `research` that names a domain/subdomain for an absent topic, require the bound Goal/Effect to name possible insert-only compatible domain/subdomain `VOCAB.md` rows plus the topic index, missing subdomain index, and topic row in the same transaction. A narrower approval does not authorize topic creation.

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
2. If the finding is exact `TOPIC_INSPECTION_ABSENT`, run the in-process create procedure, then call `topic.inspect` again with purpose `research`. Do not skip create because the parent index is missing. Skip create only when retained answers explicitly require stopping if the parent is absent.
3. If the topic is present and the retained answer is to create a new topic instead, return `needs-guidance` once for a different kebab-case slug or stop `blocked`. Do not overwrite the existing topic in that case.
4. When this inspection's `topic` record has null `last_synthesized`, call `source.candidates_for_topic` once with the exact topic ID and request-order named URLs. Freeze its source-sequence-ordered candidate list and acquisition gaps. Glance every candidate exactly once using only its TL;DR, Key points, and Classification packet. The glance result is exactly excluded `{include:false,reason}` or included `{include:true,relation,impact,confidence,reason}` under the existing route enums. Same-domain/wrong-purpose is excluded; close evidence is `direct` with `high|medium`; mild attachment is `supporting` with `low|medium`; `contradicting` is permitted but cannot author an answer. Missing named URLs remain acquisition gaps and never trigger ingest. When `last_synthesized` is nonnull, skip candidate discovery and every glance.
5. For each frozen included candidate in source-sequence order, call `source.candidates_for_topic` again with the same topic ID and named URLs plus that candidate's `source_id`. An equal current-hash relation appearing since the frozen list makes only that pair a no-write; any other disappearance or `candidate_sha256` drift stops before route preparation. For an exact candidate, call `source.lookup` once with its canonical URL and require equal source identity and content hash. Construct one complete route decision from the revalidated pending-edge base plus the new edge, call `source.prepare_route`, then use `transaction.execute`, `transaction.recover`, and `transaction.successor` exactly as the source route recipe permits. Never write an excluded pair. Every included write is sequential and fail-closed; terminal failure stops the invocation before refresh, leaving the null window open for a separately approved research invocation.
6. Call `topic.inspect` again with purpose `research` after the optional backfill work and before any refresh decision.
7. If this new inspection is `dirty|refreshing|blocked`, run the in-process refresh procedure. Backfill never follows or runs inside refresh.
8. Call `topic.inspect` again with purpose `research` and require `current` with zero pending edge IDs. Never use the pre-create, pre-backfill, or pre-refresh inspection for research preparation.
9. Draft only from the bounded research payload and templates. Record insufficiency rather than adding unbound evidence. Carry acquisition gaps from candidate discovery into the research gaps section without acquiring them.
10. Call `research.prepare` with the current inspection binding and exact staged pass, topic index, and subdomain index bytes.
11. Pass the exact prepared request to `research.execute`; use `research.recover` only with that byte-identical original request when required.

The research reducer alone derives `TOPICS.md`. Backfill uses only existing source-route writes. The publication target set remains pass, topic `INDEX.md`, subdomain `INDEX.md`, then `TOPICS.md`; research publication never alters pending edges, writes a fifth target, or repairs unrelated state. Call a sole successor only when the façade exposes it through the research recovery contract.

## Create

Call `topic.inspect` for the requested topic and require an exact `TOPIC_INSPECTION_ABSENT` finding. A conflicting, malformed, orphaned, or already-present topic is not absence.

Build the exact public version-2 create request from the approved semantic identity. The domain and subdomain members of its closed `vocabulary` object use the approved canonical IDs. Preserve explicitly retained labels and aliases; otherwise use each approved ID as its label and `[]` aliases.

A missing requested subdomain `INDEX.md` or compatible domain/subdomain vocabulary row is not a blocker. Do not enumerate other parents, relocate the topic, or return `blocked` solely because either is absent. Call `index.create_topic` with the approved semantic identity; that operation inserts any missing compatible domain/subdomain vocabulary rows and creates the missing parent index in the same transaction. Stop for parent absence only when the unchanged request or retained answers explicitly require the parent to already exist. A named domain/subdomain in an approved create or research write is authority for those insert-only effects. A stale `vault://atlas/ARCHITECTURE.md` snapshot cannot forbid that write.

The façade owns vocabulary resolution, validation, rendering, target roles and order, revisions, transaction, acknowledgement, and post-validation. Stop on any taxonomy finding with that exact finding and no write. Never load `atlas-maintain`, invoke a migration preview/apply, or create an owner chain. If the attempt is recoverable, call `index.recover_topic` only with its exact transaction identity and byte-identical original request.

Create never synthesizes research or creates source-kind/tag vocabulary, sources, relations, passes, aliases beyond the approved proposals, or additional topics. It never uses a generic source/route transaction or direct conditional replacement.

## Resume ceiling

This owner may return `needs-guidance` once and has a maximum of two owner turns. Guidance may resolve only semantics inside the unchanged approved Goal/Effect from already-bound contracts or conversation evidence. Repeated guidance, a short cycle, Atlas-state inspection by the front door, a wider effect, or an exhausted ceiling is `blocked`. There is no post-dispatch `needs-user` resume.

## Result and recovery

Return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, with `owner: atlas-research`. Use only schema-defined outcome/effect pairs. Prepare, answer, and every observed no-write path use `effect: none`.

`partial|unknown` always returns `outcome: blocked`; copy only the exact façade-returned `{operation,identity}` into `next`. Never infer success, retry hidden work, broaden recovery, or expose a recovery path for an effect that did not return one. Otherwise `next` is `null`.