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
| `atlas-source` | `resummarize` | one Goal/Effect approval | Freshly summarize explicit active URL(s). |
| `atlas-source` | `promote` | one Goal/Effect approval | Promote one explicitly named frozen staged artifact/evidence pair. |
| `atlas-source` | `reroute` | one Goal/Effect approval | Reroute exactly one active source named by canonical URL. |
| `atlas-research` | `answer` | none | Read or answer one named topic without writing. |
| `atlas-research` | `research` | one Goal/Effect approval | Research or rebuild one named topic; if absent, create it with any missing compatible domain/subdomain vocabulary rows and subdomain index in process, then publish the first pass. |
| `atlas-research` | `refresh` | one Goal/Effect approval | Explicitly refresh one dirty, refreshing, or blocked topic. |
| `atlas-research` | `create` | one Goal/Effect approval | Create one absent topic with any missing compatible domain/subdomain vocabulary rows and subdomain index in the same transaction. |
| `atlas-maintain` | `audit` | none | Explicit bounded structural-integrity inspection. |
| `atlas-maintain` | `repair` | one Goal/Effect approval | Explicit repair of a named structural finding. |
| `atlas-maintain` | `migrate` | one Goal/Effect approval | Explicit versioned taxonomy-backfill, `vocabulary-domain-insertion-v1`, `vocabulary-subdomain-insertion-v1`, or source-taxonomy-remediation preview; separately approved candidate-bound commit; or exact returned source-remediation recovery. |

Select only the first explicit requested effect. For explicit URLs, status plus “if sourced, what does the existing summary say?” is one source `answer` effect and outranks status-only source `presence`; status alone remains `presence`. A request to answer one named topic remains research `answer`. A source status request that names only an ID has no owner until the canonical URL is supplied. An explicit `vocabulary-domain-insertion-v1` request naming exactly one top-level `domain_id` and preview or exact candidate-bound apply selects only `atlas-maintain/migrate`. An explicit `vocabulary-subdomain-insertion-v1` request naming exactly one lowercase-kebab `subdomain_id`, exactly one lowercase-kebab `parent_domain_id`, and preview or exact candidate-bound apply also selects only `atlas-maintain/migrate`. A vocabulary insertion request with a missing or multiple required ID, a combined parent-and-child insertion, generic row/type control, or any tag, topic, source, manifest, relation, pass, research, backfill, remediation, framework-sync, Git, or shipping effect stops before owner load and Atlas I/O. An explicit `source-taxonomy-remediation-v1` preview, apply, or returned recovery selects only `atlas-maintain/migrate`; an explicit taxonomy-backfill request selects the same owner/mode but a different owner procedure. An unqualified “fix taxonomy” or request that could mean multiple lineages is ambiguous and stops for clarification before approval, owner load, profile, façade, or vault I/O. Default source work never starts feed/watchlist acquisition. Maintenance never activates from routine cadence, source-quality review, or an implicit “check everything.”

Research answer stays read-only even when the topic is dirty. Source answer reads only active artifacts selected by one manifest inventory and never fetches live content. Research may run create in process after an exact absence finding, and may run refresh in process only after research mode is approved. Standalone refresh stops after refresh. Topic creation and routing are in-process procedures of the selected outer owner, never additional owners.

## One clarification boundary

Before any approval, one ambiguous request may produce one batched material clarification. Ask only questions whose answers change owner, mode, topic/source identity, scope, authority, safety boundary, or maximum logical write effect. Present two to five stable options with one narrow recommended option when choices exist.
For an unqualified request to read or summarize a live URL, ask whether to use an existing stored Atlas summary or start separately approved acquisition; do not infer either. For a request to inspect or summarize a repository collection, ask the user to choose the existing exact root-URL summary or provide the exact URLs to inspect. If unresolved, stop before owner load with no Atlas I/O; never crawl, prefix-search, auto-expand, or fetch.
For an unbound topic-research request, recommend a kebab-case topic slug and a kebab-case domain/subdomain pair from the request description only. Do not inspect the vault. Naming a domain/subdomain authorizes insert-only compatible domain/subdomain `VOCAB.md` rows plus creation of the missing subdomain index in the same topic transaction; do not add a parent-must-already-exist constraint. Retain explicitly approved labels and aliases; otherwise the owner uses the approved ID as label and `[]` aliases. In the same batch, ask whether to update an existing same-identity topic or create a new topic if that identity is already present. If the request both names a domain/subdomain and also says not to invent a parent, or to create only if that parent already exists, ask one fork: create the named compatible vocabulary parent and subdomain index if missing, then the topic (recommended), or stop if the named parent is absent. A request to research or produce a first draft of a named or recommended topic is `research`; shell-only creation remains `create`.

Retain the unchanged request and the exact answers. A material ambiguity that remains after this batch stops without owner load. A taxonomy migration clarification may select only `taxonomy backfill`, `vocabulary-domain-insertion-v1`, `vocabulary-subdomain-insertion-v1`, or `source-taxonomy-remediation-v1`; it never asks for mappings, paths, fields, revisions, candidate material, or recovery identity. Vocabulary-domain insertion additionally requires exactly one explicit lowercase kebab-case top-level domain ID and either preview or candidate-bound apply. Vocabulary-subdomain insertion requires exactly one explicit lowercase kebab-case subdomain ID, exactly one explicit lowercase kebab-case parent domain ID, and either preview or candidate-bound apply; it never offers to insert, activate, alias-select, or infer the parent. Neither vocabulary insertion can be combined with another taxonomy or framework effect. Deterministic findings, current Atlas state, target bytes, revisions, transaction IDs, and recovery identities are owner work and never front-door questions.

## Approval rule

Read-only modes source `presence|answer`, research `answer`, and maintain `audit` dispatch after classification and any necessary material clarification. They do not render or request an approval overview.

Every write-capable mode renders exactly one unchanged overview before owner load:
For source ingest or resummarize, that Effect names possible insert-only `VOCAB.md` rows plus the existing source, manifest, route, relation, and derived-freshness classes.
For source-taxonomy remediation, the Effect names either read-only preview; the exact candidate-bound 13-source-artifact transaction plus immutable dedicated journal; or the exact already-returned recovery identity. Each preview, apply, and recovery invocation receives its own unchanged Goal/Effect approval and never includes `VOCAB.md`, backfill, research, reroute, resummarization, framework sync, deployment, or shipping.
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

Changing either ID, lineage, row type, parent rule, candidate, instance, or effect requires a new overview. Preview approval, the returned literal, domain-insertion approval, source-remediation approval, backfill approval, engineering approval, framework-sync approval, Git authority, or shipping approval never substitutes for the fresh apply approval.


```markdown
## Goal
<one concise sentence interpreting the unchanged request and retained answers>

## Effect
<write-capable through atlas-source|atlas-research|atlas-maintain mode <mode>; maximum logical paths or registry classes; for source ingest or resummarize, include possible insert-only `VOCAB.md` rows, source artifact, manifest fields, route status, relations, and derived freshness; for research, include eligible preexisting-source route fields, relations, derived freshness, manifest route status, and publication targets; for research create or research that names a domain/subdomain, include possible insert-only compatible domain/subdomain `VOCAB.md` rows plus the topic index, missing subdomain index, and topic row in the same transaction unless the retained answer is to stop if the parent is absent; exact targets remain owner-gated>

## Approval
Reply **approve** to start.
```

Accept only an unambiguous approval tied to the immediately preceding unchanged Goal/Effect. A changed goal, effect, owner, mode, safety boundary, material answer, caveat, silence, or ambiguous reply requires reclassification and a new overview.

Approval is conversational dispatch authority only. It is not a mutation token, revision, projection, transaction, recovery, profile, credential, deployment, Git, or instance-sync grant. Migration preview and commit are separate invocations; a commit receives its own candidate-bound Goal/Effect approval. Vocabulary-domain insertion never chains to or transfers candidate, approval, request, transaction, or recovery authority to taxonomy backfill or source-taxonomy remediation. Vocabulary-subdomain insertion never chains to or transfers candidate, approval, request, transaction, or recovery authority to vocabulary-domain insertion, taxonomy backfill, or source-taxonomy remediation, and never inserts or activates its parent. Source-taxonomy remediation recovery is also a fresh invocation with its own unchanged approval and may use only the exact façade-returned operation and identity.

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