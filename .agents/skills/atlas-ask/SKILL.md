---
name: atlas-ask
description: >
  Sole public Atlas behavior entrypoint. Classify one request to an exact owner and
  mode, obtain any material clarification and required Goal/Effect approval, then
  run that owner end-to-end in the same agent.
disableModelInvocation: true
---

# atlas-ask

## Classification boundary

Classify from this skill's exact owner/mode map before reading `.agents/ARCHITECTURE.md`, `skill://atlas-core`, `atlas-workflow-result.schema.json`, or any owner resource. Non-Atlas requests, empty goals, unresolved clarification, and classification-only requests stop without loading any of those resources or performing Atlas I/O.

The front door never loads architecture or core contracts on an owner's behalf. A qualified owner owns its conditional contract and bound-architecture read order.

## Sole front door

Accept one plain-language Atlas request. Empty arguments ask for the Atlas goal. `/atlas-ask` is the only public Atlas behavior interface and the sole classifier. Owner resources are internal files, not commands or independently callable skills.

The front door performs no Atlas semantic work, façade operation, profile or vault inspection, capture, synthesis, reducer, projection, transaction, recovery, or engineering work. It never loads more than one outer owner, reconstructs a missing result, or treats prose as a machine result.

A generic repository, code, configuration, shell, or file-edit request is non-Atlas. Return it without an Atlas owner, capability claim, approval, or Atlas I/O.

## Exact owner and mode map

| Owner | Mode | Approval | Classification signal |
|---|---|---|---|
| `atlas-source` | `presence` | none | Presence or manifest-backed status for explicit URL(s). |
| `atlas-source` | `answer` | none | Manifest-backed status for explicit URL(s) plus a concise account of each existing active stored summary. |
| `atlas-source` | `ingest` | one Goal/Effect approval | Capture explicit URL(s) through routine source work. |
| `atlas-source` | `resummarize` | one Goal/Effect approval | Resummarize explicit active URL(s); valid unclassified state is corrected from the stored summary without recapture. |
| `atlas-source` | `promote` | one Goal/Effect approval | Promote one explicitly named frozen staged schema-2 artifact/evidence pair. |
| `atlas-source` | `reroute` | one Goal/Effect approval | Explicitly revalidate exactly one active source named by canonical URL across every active topic; valid unclassified state is corrected first. |
| `atlas-research` | `answer` | none | Read or answer one named topic without writing. |
| `atlas-research` | `research` | one Goal/Effect approval | Research/rebuild one named topic; if absent, create it with compatible domain/subdomain/tag vocabulary and missing subdomain index, then publish the first pass. |
| `atlas-research` | `refresh` | one Goal/Effect approval | Explicitly refresh one dirty, refreshing, or blocked topic through a fresh bound frontier. |
| `atlas-research` | `create` | one Goal/Effect approval | Create one absent topic, or revise aliases/canonical tags/include/exclude scope of one fixed-identity topic, with compatible vocabulary and derived frontier projections in process. |
| `atlas-maintain` | `audit` | none | Explicit bounded structural-integrity inspection. |
| `atlas-maintain` | `repair` | one Goal/Effect approval | Explicit repair of a named structural finding. |
| `atlas-maintain` | `migrate` | one Goal/Effect approval | Explicit versioned taxonomy backfill, vocabulary insertion, source-taxonomy remediation, or source-topic-routing-v2 preview; separately approved candidate-bound commit; or exact returned lineage recovery. |

Select only the first explicit requested effect. URL status plus a request for the existing summary is source answer; status alone is presence. A named topic answer remains research answer. A source request naming only an ID needs its canonical URL. A request to change an existing topic's aliases, canonical tags, include terms, or exclude terms selects research create; any title/domain/subdomain/path change is a different identity and requires clarification. A named versioned migration preview/apply/recovery selects only maintain migrate and exactly one lineage.

Research answer stays read-only even when dirty. Source answer reads only manifest-selected active artifacts and never fetches. Research may create on exact absence and refresh only inside approved research. Topic create/scope, route, and refresh remain procedures of the selected outer owner, never extra owners.

`vocabulary-domain-insertion-v1` requires exactly one explicit lowercase-kebab `domain_id`. A `vocabulary-subdomain-insertion-v1` request names exactly one lowercase-kebab `subdomain_id` and one existing active lowercase-kebab `parent_domain_id`; never infer, insert, activate, or alias-select the parent.

## One clarification boundary

Before any approval, one ambiguous request may produce one batched material clarification. Ask only questions whose answers change owner, mode, topic/source identity, scope, authority, safety boundary, or maximum logical write effect. Present two to five stable options with one narrow recommended option when choices exist.
For an unqualified request to read or summarize a live URL, ask whether to use an existing stored Atlas summary or start separately approved acquisition; do not infer either. For a request to inspect or summarize a repository collection, ask the user to choose the existing exact root-URL summary or provide the exact URLs to inspect. If unresolved, stop before owner load with no Atlas I/O; never crawl, prefix-search, auto-expand, or fetch.
For an unbound topic research/create request, recommend a kebab-case topic slug and domain/subdomain pair from request text only; do not inspect the vault. Naming domain/subdomain/tags authorizes only compatible insert-only rows plus the missing subdomain index in the same topic transaction. Retain approved labels/aliases or default each label to its ID and aliases to empty. Ask in the same batch whether an existing same-identity topic should be confirmed unchanged or have only aliases/tags/include/exclude scope revised. Never infer a topic move, rename, or parent substitution.

Retain the unchanged request and exact answers. Remaining material ambiguity stops before owner load. Migration clarification selects exactly one of taxonomy backfill, vocabulary-domain-insertion-v1, vocabulary-subdomain-insertion-v1, source-taxonomy-remediation-v1, or source-topic-routing-v2 and preview/apply/exact recovery; never ask the user to invent mappings, paths, revisions, candidate material, or recovery identity.


## Approval rule

Read-only modes source `presence|answer`, research `answer`, and maintain `audit` dispatch after classification and any necessary material clarification. They do not render or request an approval overview.

Every write-capable mode renders exactly one unchanged overview before owner load:
For source ingest/resummarize, Effect names possible insert-only VOCAB rows, schema-2 source artifact and MANIFEST routing identity/status, relation frontier, and derived freshness. Reroute names stored classification correction only when current state is valid unclassified, plus complete explicit topic revalidation; it never authorizes recapture or content/date change. Promotion names only the frozen pair and its derived source/route effects.
For source-taxonomy remediation or source-topic-routing-v2, Effect identifies exactly preview, candidate-bound apply, or already-returned recovery and its isolated target classes/journal. Every stage is a separate invocation/approval. It never includes another migration, research, source workflow, framework sync, deployment, Git, or shipping.
For `vocabulary-domain-insertion-v1`, substitute only the retained explicit values into one of these invariant overviews. Preview is exactly:

```markdown
## Goal
Preview vocabulary-domain-insertion-v1 for the explicit top-level domain ID `<domain_id>`.

## Effect
Run read-only through atlas-maintain mode migrate; inspect only `vault://atlas/summaries/registry/VOCAB.md` and produce at most one candidate for the canonical `<domain_id>` domain row; write nothing.

## Approval
Reply **approve** to start.
```

Apply is a fresh invocation and exactly:

```markdown
## Goal
Apply vocabulary-domain-insertion-v1 candidate `<candidate_sha256>` for the explicit top-level domain ID `<domain_id>` in Atlas instance `<instance_id>`.

## Effect
Run write-capable through atlas-maintain mode migrate; conditionally replace only `vault://atlas/summaries/registry/VOCAB.md` with the exact candidate output; create no journal or recovery operation and write no other path.

## Approval
Reply **approve** to start.
```

Changing the ID, lineage, row type, candidate, instance, or effect requires a new overview. Preview approval, the returned literal, any other migration approval, engineering approval, framework-sync approval, or shipping approval never substitutes for the fresh apply approval.

For `vocabulary-subdomain-insertion-v1`, substitute only the retained explicit values into one of these invariant overviews. Preview is exactly:

```markdown
## Goal
Preview vocabulary-subdomain-insertion-v1 for the explicit subdomain ID `<subdomain_id>` under the existing active top-level domain ID `<parent_domain_id>`.

## Effect
Run read-only through atlas-maintain mode migrate; inspect only `vault://atlas/summaries/registry/VOCAB.md` and produce at most one candidate for the canonical `<subdomain_id>` subdomain row parented by `<parent_domain_id>`; write nothing.

## Approval
Reply **approve** to start.
```

Apply is a fresh invocation and exactly:

```markdown
## Goal
Apply vocabulary-subdomain-insertion-v1 candidate `<candidate_sha256>` for the explicit subdomain ID `<subdomain_id>` under the existing active top-level domain ID `<parent_domain_id>` in Atlas instance `<instance_id>`.

## Effect
Run write-capable through atlas-maintain mode migrate; conditionally replace only `vault://atlas/summaries/registry/VOCAB.md` with the exact candidate output; create no journal or recovery operation and write no other path.

## Approval
Reply **approve** to start.
```

Changing either ID, lineage, row type, parent rule, candidate, instance, or effect requires a new overview. This lineage never inserts or activates its parent. Preview approval, the returned literal, domain-insertion approval, source-remediation approval, backfill approval, engineering approval, framework-sync approval, Git authority, or shipping approval never substitutes for fresh apply approval.

For `source-topic-routing-v2`, preview is a fresh invocation and exactly:

```markdown
## Goal
Preview source-topic-routing-v2 against Atlas instance `<instance_id>`.

## Effect
Run read-only through atlas-maintain mode migrate; inspect the complete source/topic routing inventory and produce at most one candidate; write nothing.

## Approval
Reply **approve** to start.
```

Apply is a separate candidate-bound invocation and exactly:

```markdown
## Goal
Apply source-topic-routing-v2 candidate `<candidate_sha256>` to Atlas instance `<instance_id>`.

## Effect
Run write-capable through atlas-maintain mode migrate; write only the candidate-listed active source artifacts, non-archived topic/subdomain indexes, MANIFEST, RELATIONS, TOPICS, and immutable records under `.atlas/transactions/migrations/source-topic-routing-v2`; write no VOCAB, archived artifact, research pass, framework, deployment, Git, or other migration state.

## Approval
Reply **approve** to start.
```

Recovery receives its own overview naming the exact returned transaction ID and byte-identical apply request. Its Effect is limited to classifying/restoring only that journal's candidate targets and may not regenerate a different candidate or invoke another migration.


```markdown
## Goal
<one concise sentence interpreting the unchanged request and retained answers>

## Effect
<write-capable through atlas-source|atlas-research|atlas-maintain mode <mode>; maximum logical paths or registry classes; source ingest/resummarize names optional compatible VOCAB plus schema-2 artifact/MANIFEST/frontier/freshness; reroute names optional stored unclassified correction plus complete explicit revalidation; research names eligible route/frontier/freshness and publication targets; create names compatible domain/subdomain/tag VOCAB plus topic/subdomain/TOPICS, or fixed-identity scope revision across topic/subdomain/RELATIONS/TOPICS; refresh names exact bound frontier dispositions and pass/index/cache targets; migration names only its separately selected preview, candidate apply, or returned recovery>

## Approval
Reply **approve** to start.
```

Accept only an unambiguous approval tied to the immediately preceding unchanged Goal/Effect. A changed goal, effect, owner, mode, safety boundary, material answer, caveat, silence, or ambiguous reply requires reclassification and a new overview.

Approval is conversational dispatch authority only, never a mutation token, revision, transaction, recovery, profile, credential, Git, deploy, sync, or shipping grant. Each migration never chains to or transfers candidate, approval, request, transaction, or recovery authority to another lineage. Taxonomy backfill, both vocabulary insertions, source-taxonomy remediation, and source-topic-routing-v2 keep distinct candidates, targets, and journals. A source-topic routing approval authorizes no bound-instance framework sync or unrelated source/research effect.

## Classification-only output

When the request explicitly asks only for classification, execute no owner and return exactly:

```text
owner: atlas-source|atlas-research|atlas-maintain|null
mode: presence|ingest|resummarize|promote|reroute|answer|research|refresh|create|audit|repair|migrate|null
clarification_required: true|false
approval_required: true|false
front_door_write_set: []
```

Classification-only work performs no façade, profile, vault, or owner call.

## Same-agent owner execution

After any required approval, load exactly `skill://atlas-ask/owners/<owner-id>/OWNER.md` in this agent with the selected owner and mode, unchanged request, retained material answers, and approved maximum logical effect. Missing delegation facilities never block execution. Do not load architecture or `atlas-core` first; the selected owner performs its own conditional reads. Do not load another owner resource; allowed route, refresh, and topic-create procedures run in process inside the selected owner.

An unqualified direct owner load remains readless and write-free and redirects to `/atlas-ask`. A required façade operation that is genuinely absent returns one `framework-defect` owner result with concrete catalog/contract evidence; never bypass it with direct vault edits.

## Bounded owner resumes

Same-owner resumes preserve the unchanged request, material answers, approval boundary, prior result, and exact answer to the immediately preceding question. Resume ceilings are invocation-local and never appear in the result.

| Owner | `needs-user` resumes | `needs-guidance` resumes | Maximum owner turns |
|---|---:|---:|---:|
| `atlas-source` | 2, ordered `source.aggregate-expansion` then `source.worker-choice` | 1 | 4 |
| `atlas-research` | 0 | 1 | 2 |
| `atlas-maintain` | 0 | 1 | 2 |

Post-approval guidance may resolve only semantics inside the unchanged Goal/Effect from already-bound contracts or conversation evidence. It may not inspect Atlas state, request new authority, imply a wider effect, or change owner/mode. A repeated question, short cycle, invalid answer binding, unknown or out-of-order source step, wider effect, or exhausted ceiling returns `blocked`.

## Owner result consumption

Only after the owner returns a result, read `skill://atlas-core/assets/atlas-workflow-result.schema.json`. Consume exactly one result with fields `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, validate it against that schema, and never reconstruct missing fields or accept prose in its place.

- `completed`: present the compact terminal summary; effect is `none|committed`.
- `no-write`: present the terminal no-write reason; effect is `none`.
- `needs-user`: ask the one batched source question and resume only within the source ceiling.
- `needs-guidance`: resolve the one bounded semantic question or stop within the owner ceiling.
- `blocked`: invoke recovery only when `next` is a nonnull schema-valid recovery object; otherwise stop. `recovery_required:true` with `next:null` is a manual-intervention flag and grants no operation.
- `framework-defect`: present concrete product-owned blocker evidence. Engineering requires a separate user-approved route; never dispatch it automatically.

`partial` always pairs with `blocked` and a nonnull exact already-authorized recovery in `next`. `unknown` normally does the same; the sole null-`next` alternative is blocked manual intervention with every item `recovery_required:true`. Never infer recovery, run an automatic audit/verify/repair loop, add a retry coordinator, or append a second workflow result.