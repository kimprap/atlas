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
| `atlas-research` | `research` | one Goal/Effect approval | Research or rebuild one named topic. |
| `atlas-research` | `refresh` | one Goal/Effect approval | Explicitly refresh one dirty, refreshing, or blocked topic. |
| `atlas-research` | `create` | one Goal/Effect approval | Create one absent topic under an existing domain/subdomain. |
| `atlas-maintain` | `audit` | none | Explicit bounded structural-integrity inspection. |
| `atlas-maintain` | `repair` | one Goal/Effect approval | Explicit repair of a named structural finding. |
| `atlas-maintain` | `migrate` | one Goal/Effect approval | Explicit versioned migration preview, commit, or recovery. |

Select only the first explicit requested effect. For explicit URLs, status plus “if sourced, what does the existing summary say?” is one source `answer` effect and outranks status-only source `presence`; status alone remains `presence`. A request to answer one named topic remains research `answer`. A source status request that names only an ID has no owner until the canonical URL is supplied. Default source work never starts feed/watchlist acquisition. Maintenance never activates from routine cadence, source-quality review, or an implicit “check everything.”

Research answer stays read-only even when the topic is dirty. Source answer reads only active artifacts selected by one manifest inventory and never fetches live content. Research may run refresh in process only after research mode is approved. Standalone refresh stops after refresh. Topic creation and routing are in-process procedures of the selected outer owner, never additional owners.

## One clarification boundary

Before any approval, one ambiguous request may produce one batched material clarification. Ask only questions whose answers change owner, mode, topic/source identity, scope, authority, safety boundary, or maximum logical write effect. Present two to five stable options with one narrow recommended option when choices exist.
For an unqualified request to read or summarize a live URL, ask whether to use an existing stored Atlas summary or start separately approved acquisition; do not infer either. For a request to inspect or summarize a repository collection, ask the user to choose the existing exact root-URL summary or provide the exact URLs to inspect. If unresolved, stop before owner load with no Atlas I/O; never crawl, prefix-search, auto-expand, or fetch.

Retain the unchanged request and the exact answers. A material ambiguity that remains after this batch stops without owner load. Deterministic findings, current Atlas state, target bytes, revisions, transaction IDs, and recovery identities are owner work and never front-door questions.

## Approval rule

Read-only modes source `presence|answer`, research `answer`, and maintain `audit` dispatch after classification and any necessary material clarification. They do not render or request an approval overview.

Every write-capable mode renders exactly one unchanged overview before owner load:

```markdown
## Goal
<one concise sentence interpreting the unchanged request and retained answers>

## Effect
<write-capable through atlas-source|atlas-research|atlas-maintain mode <mode>; maximum logical paths or registry classes; exact targets remain owner-gated>

## Approval
Reply **approve** to start.
```

Accept only an unambiguous approval tied to the immediately preceding unchanged Goal/Effect. A changed goal, effect, owner, mode, safety boundary, material answer, caveat, silence, or ambiguous reply requires reclassification and a new overview.

Approval is conversational dispatch authority only. It is not a mutation token, revision, projection, transaction, recovery, profile, credential, deployment, or instance-sync grant. Migration preview and commit are separate invocations; a commit receives its own candidate-bound Goal/Effect approval.

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
- `blocked`: stop or invoke only the already-authorized exact recovery in `next`.
- `framework-defect`: present concrete product-owned blocker evidence. Engineering requires a separate user-approved route; never dispatch it automatically.

`partial|unknown` always pairs with `blocked` and only exact already-authorized recovery in `next`. Never infer recovery, run an automatic audit/verify/repair loop, add a retry coordinator, or append a second workflow result.