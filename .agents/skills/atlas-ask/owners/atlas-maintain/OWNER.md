# atlas-maintain

## Qualification

Execute this resource only when the same agent has selected `atlas-maintain` through `/atlas-ask` and bound one mode, the unchanged request, retained material answers, and any approved Goal/Effect boundary. Any other load performs no further read, model work, façade call, profile or vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

This owner executes end-to-end in the current agent and alone returns the seven-field result defined by `atlas-workflow-result.schema.json`.

## Read first

1. `vault://atlas/ARCHITECTURE.md`
2. `skill://atlas-core/SKILL.md`
3. `skill://atlas-core/assets/agent-cli-recipes.md`
4. `skill://atlas-core/assets/markdown-registry-contracts.md`
5. only the logical artifacts named by the explicit integrity or migration scope

Discover the lifecycle surface with `python3 scripts/atlas_tool.py capabilities`; use `capabilities --all` only to inspect a contract-named internal primitive. Use generated family/verb commands with one operation-args object, or the low-level call with the exact version-2 request envelope. Decode only the version-2 response envelope. Never import a domain module, resolve a host path, or reproduce parsing, reduction, revision, transaction, or recovery mechanics.

## Modes

| Mode | Approval already bound | Scope |
|---|---|---|
| `audit` | No | Read-only inspection of an explicit structural integrity signal. |
| `repair` | One Goal/Effect approval | Exact reducer-authorized repair for an explicit structural finding. |
| `migrate` | One Goal/Effect approval per invocation | Exact versioned migration preview, separately approved commit, or exact recovery. |

Activate only for an explicit structural integrity signal or explicit versioned migration request. This owner has no generic acquisition, calibration, recurring audit, source-quality review, topic research, taxonomy design, self-healing, or background workflow.

## Audit

Read only the named bounded scope with `vault.read`, `vault.read_json`, `vault.list`, `vault.hash`, or `vault.digest_tree` as applicable, then call `state.validate` on each complete required state bundle. Report normalized findings with logical paths and anchors. Audit returns `effect: none` and performs no repair, migration apply, generic write, retry, or verification loop.

## Repair

Accept only a named structural finding and one exact core-defined repair event:

```text
repair-table-placement  {type,registry}
repair-relation-notes   {type,repairs:[{edge_id,reason}]}
```

Read and validate the complete affected state, then call the internal `transaction.execute` operation with exactly `{version:1,event}`. The façade owns the consistent reread, event validation, reduction, exact target set and preconditions, immutable journal, apply, acknowledgement, reread, and post-validation. Never hand-author candidate bytes, widen targets, repair taxonomy, infer an event from malformed state, or chain audit into automatic repair.

When the response requires recovery, call `transaction.recover` with exactly `{version:1,transaction_id,request}`, where `request` is the byte-identical original `{version:1,event}`. Never retry, rebase, force-write, substitute a generic vault write, or adapt a source/route transaction or aggregate effect. Consume only the façade's terminal result and exact recovery identity.

## Two-phase migration

Migration remains two-phase and each phase is a fresh `/atlas-ask` invocation.

### Inspect and preview

Call `migration.prepare_topics_lists` with `{}` for the current versioned TOPICS-list migration.

- `no-op` returns `completed` with `effect: none` and no commit approval.
- `candidate` returns `completed` with `effect: none`, the instance binding, inventory revisions, candidate identity, ordered human-visible changes, and the exact returned approval literal. It performs no apply.
- Invalid, ambiguous, unavailable, or stale preparation returns blocked/no-effect with exact normalized findings.

No preview result, plan approval, route approval, fixture, or candidate from another instance authorizes mutation.

### Separately approved commit or recovery

A second fresh `migrate` request must bind the exact instance ID, candidate identity, and byte-exact approval literal returned by preview, then receive its own unchanged Goal/Effect approval. Call `migration.apply_topics_lists` only with that exact triple.

Consume the returned state without relabeling it. `applied` is committed only after the façade acknowledges, rereads, and post-validates. A pre-effect stale candidate is blocked with `effect: none` and requires a new preview plus new approval. `rolled-back` is blocked. `manual-conflict`, incomplete apply, or observation disagreement is blocked with `effect: partial|unknown` as returned and exposes only the exact returned recovery operation and identity.

Never retry a forward apply, force-write, substitute bytes, use a generic transaction, or widen the migration. Exact recovery uses the façade-returned operation and identity byte-for-byte and nothing else.

## Resume ceiling

This owner may return `needs-guidance` once and has a maximum of two owner turns. Guidance may resolve only semantics inside the unchanged approved Goal/Effect from already-bound contracts or conversation evidence. Repeated guidance, a short cycle, a wider effect, or an exhausted ceiling is `blocked`. There is no post-dispatch `needs-user` resume.

## Result and recovery

Return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, with `owner: atlas-maintain`. Use only schema-defined outcome/effect pairs. Audit, prepare, preview, and every observed no-write path use `effect: none`.

`partial|unknown` always returns `outcome: blocked`; copy only the exact façade-returned `{operation,identity}` into `next`. Never infer success, add recovery metadata, or expose a recovery path when the façade returned none. Otherwise `next` is `null`.