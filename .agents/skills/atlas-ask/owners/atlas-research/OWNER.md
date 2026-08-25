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
| `research` | One Goal/Effect approval | Publish one pass; exact absence may create the topic with compatible domain/subdomain/tag vocabulary and missing subdomain index in process. |
| `refresh` | One Goal/Effect approval | Apply one exact disposition per bound pending frontier row and stop. |
| `create` | One Goal/Effect approval | Create one absent version-3 topic, or revise aliases/canonical tags/include/exclude scope of one fixed-identity topic. |

Reject wider effect. Topic ambiguity must be resolved before approval; post-dispatch identity/scope change starts a new `/atlas-ask`.

Create/research absence authority must name compatible domain/subdomain/tag VOCAB plus topic/subdomain/TOPICS classes. Existing scope revision authority must name fixed topic identity plus possible compatible tag VOCAB, topic/subdomain indexes, RELATIONS, and TOPICS. A narrower approval authorizes neither.

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
  → draft one pass and topic-index bytes plus one disposition per pending frontier
  → refresh.prepare with the original inspection hash and exact bytes
  → refresh.execute with the returned request
  → refresh.recover only with the byte-identical request and returned identity
```

`refresh.prepare` performs the immediate second inspection. Require the same topic and complete ordered generation/semantic/revision frontier; current-empty, missing/extra/reordered work, or substituted bytes stop. The façade owns version-2 start/complete events, exact `incorporated|reviewed-no-change` dispositions, Created preservation, cache derivation, journal, acknowledgement, and recovery. Never hand-author an event, patch a registry, rebase a draft, or recover changed bytes.

A standalone `refresh` invocation stops after the terminal refresh receipt. It never continues into research publication.

## Research

1. Call `topic.inspect` with purpose `research`.
2. If the finding is exact `TOPIC_INSPECTION_ABSENT`, run the in-process create procedure, then call `topic.inspect` again with purpose `research`. Do not skip create because the parent index is missing. Skip create only when retained answers explicitly require stopping if the parent is absent.
3. If the topic is present and the retained answer is to create a new topic instead, return `needs-guidance` once for a different kebab-case slug or stop `blocked`. Do not overwrite the existing topic in that case.
4. When last_synthesized is null, call `source.candidates_for_topic` once with exact topic ID and request-order named URLs. Freeze candidates, acquisition gaps, and skipped sources. Valid unclassified sources are visible skips with `SOURCE_CLASSIFICATION_UNAVAILABLE`, not gaps. Any blocking structural finding stops the scan. Glance every candidate once using only returned classified taxonomy/routing terms, title, TL;DR, and Key points; typed hits/rank are diagnostics. Produce one settled verifier exclusion or inclusion. Named sources bypass positive match, not exclusion. When synthesis is nonnull, skip discovery/glances.
5. For each included candidate in source order, reissue the candidate call with its source ID. Require candidate hash and source content/routing/topic-scope identities; exact-current evidence is pair no-write and other drift stops. Call `source.lookup` and require identity/content/routing equality. Send the unchanged normal route action, frontier, revisions, verifier edge, and empty exclusions to `source.prepare_route`; pass its returned transaction through `transaction.execute`, exact `transaction.recover`, and sole eligible `transaction.successor`. Exclusions are never written. Carry gaps/skips without acquisition or suppression.
6. Call `topic.inspect` again with purpose `research` after the optional backfill work and before any refresh decision.
7. If this new inspection is `dirty|refreshing|blocked`, run the in-process refresh procedure. Backfill never follows or runs inside refresh.
8. Call `topic.inspect` again with purpose `research` and require `current` with zero pending edge IDs. Never use the pre-create, pre-backfill, or pre-refresh inspection for research preparation.
9. Draft only from the bounded research payload and templates. Record insufficiency rather than adding unbound evidence. Carry acquisition gaps from candidate discovery into the research gaps section without acquiring them.
10. Call `research.prepare` with the current inspection binding and exact staged pass, topic index, and subdomain index bytes.
11. Pass the exact prepared request to `research.execute`; use `research.recover` only with that byte-identical original request when required.

The research reducer alone derives `TOPICS.md`. Backfill uses only existing source-route writes. The publication target set remains pass, topic `INDEX.md`, subdomain `INDEX.md`, then `TOPICS.md`; research publication never alters pending edges, writes a fifth target, or repairs unrelated state. Call a sole successor only when the façade exposes it through the research recovery contract.

## Create or revise scope

Call `topic.inspect` first. Exact absence may use `index.create_topic`; malformed/orphaned/conflicting state is not absence. A present exact identity may use `index.prepare_topic_scope` only when the approved request changes aliases, canonical tags, include terms, or exclude terms. Title, topic ID/path, domain, and subdomain never move in place.

Create builds exact public version 3 with canonical tags and closed vocabulary `{domain,subdomain,tags}` from approved IDs/labels/aliases. Missing compatible vocabulary or subdomain index is not a blocker; `index.create_topic` inserts/materializes them in the same transaction. It creates no relation/pass/source/source-kind. A zero-candidate shell remains current, insufficient, and null synthesis; later matching ingest follows normal routing.

Scope revision builds exact version-1 `index.prepare_topic_scope` with current topic path, normalized arrays, tag-only vocabulary, and approved revised_on. Pass its returned generic transaction unchanged to `transaction.execute`, exact `transaction.recover`, and sole eligible `transaction.successor`. Identical scope has no target but still proceeds to a fresh candidate scan. Applied changes derive one pending scope-change child per historical pair; owners never edit relations/caches.

After an applied/no-op create or scope receipt, take a fresh research inspection and run the same normal candidate/glance/verifier/route procedure over historical active sources. A zero-match create writes no relation/pass and returns current/insufficient/null synthesis. A zero-match scope revision simply leaves the frontier unchanged. Standalone create stops after these route receipts and never publishes a pass.

The façade owns vocabulary resolution, managed rendering, scope digest, target order, frontier/cache effects, recovery, and post-validation. For create recovery call `index.recover_topic` only with its exact returned identity and byte-identical request. Stop on any finding. Never load atlas-maintain, invoke migration, directly replace bytes, or create an owner chain.

## Resume ceiling

This owner may return `needs-guidance` once and has a maximum of two owner turns. Guidance may resolve only semantics inside the unchanged approved Goal/Effect from already-bound contracts or conversation evidence. Repeated guidance, a short cycle, Atlas-state inspection by the front door, a wider effect, or an exhausted ceiling is `blocked`. There is no post-dispatch `needs-user` resume.

## Result and recovery

Return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, with `owner: atlas-research`. Use only schema-defined outcome/effect pairs. Prepare, answer, and every observed no-write path use `effect: none`.

`partial|unknown` always returns `outcome: blocked`; copy only the exact façade-returned `{operation,identity}` into `next`. Never infer success, retry hidden work, broaden recovery, or expose a recovery path for an effect that did not return one. Otherwise `next` is `null`.