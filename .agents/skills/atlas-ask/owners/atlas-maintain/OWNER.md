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
| `migrate` | One Goal/Effect approval per invocation | Exactly one versioned taxonomy-backfill, `vocabulary-domain-insertion-v1`, `vocabulary-subdomain-insertion-v1`, or source-taxonomy-remediation preview; separately approved candidate-bound commit; or exact returned source-remediation recovery. |

Activate only for an explicit structural integrity signal or explicit versioned migration request. Before any migration I/O, select exactly one contract-named lineage from the unchanged request. Ambiguity among taxonomy backfill, `vocabulary-domain-insertion-v1`, `vocabulary-subdomain-insertion-v1`, and source-taxonomy remediation returns `blocked|none|next:null`; do not call capabilities, profile, façade, vault, or another owner until a fresh clarified invocation. Vocabulary-domain insertion requires exactly one explicit top-level domain ID and preview or exact candidate-bound apply. Vocabulary-subdomain insertion requires exactly one explicit subdomain ID, one explicit parent domain ID, and preview or exact candidate-bound apply; it never inserts, activates, alias-selects, or infers the parent. Any additional taxonomy, source, topic, manifest, relation, pass, research, framework-sync, Git, or shipping effect is out of scope. This owner has no generic acquisition, calibration, recurring audit, source-quality review, topic research, taxonomy design, self-healing, or background workflow.

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

## Two-phase taxonomy backfill

Migration remains two-phase and each phase is a fresh `/atlas-ask` invocation. This owner never combines preview and apply, loads another owner, or invents a recovery operation.

### Inspect and preview

Call `migration.prepare_taxonomy_backfill` with exactly `{}`.

- `no-op` returns `completed` with `effect: none`, `next:null`, and no commit approval.
- `candidate` returns `completed` with `effect: none`, `next:null`, the instance binding, complete registry and active-artifact inventory, candidate identity, ordered human-visible changes, and exact returned approval literal. It performs no apply.
- A taxonomy blocker returns `blocked` with `effect: none`, `next:null`, every normalized artifact/field finding, and only the read-only preview operation as guidance. It exposes no candidate or approval.
- Invalid, unavailable, locked-set-mismatched, or stale preparation returns blocked/no-effect with exact normalized findings.

No preview result, plan approval, route approval, fixture, or candidate from another instance authorizes mutation.

### Separately approved commit

A second fresh `migrate` request must bind the exact instance ID, candidate identity, and byte-exact approval literal returned by preview, then receive its own unchanged Goal/Effect approval. Call `migration.apply_taxonomy_backfill` only with that exact triple.

Consume the nested state and façade disposition without relabeling:

- `applied` → `outcome:"completed"`, `effect:"committed"`, `next:null`.
- `rolled-back` with proven preimage, including sibling-drift rollback → `outcome:"blocked"`, `effect:"none"`, `next:null`.
- `manual-conflict` → `outcome:"blocked"`, `effect:"unknown"`, `next:null`, with at least one blocked item whose `recovery_required` is `true`.
- A pre-effect stale candidate → `outcome:"blocked"`, `effect:"none"`, `next:null`; require a new preview and approval.

Never retry a forward apply, force-write, substitute bytes, use a generic transaction, widen the migration, fabricate lineage, or expose a recovery operation. Manual conflict requires separately authorized human audit/repair; the failed apply is never resumed.

## Candidate-bound vocabulary-domain insertion

Preview and apply are separate fresh `/atlas-ask` invocations with separate unchanged approvals. This lineage never invokes taxonomy backfill or source remediation, loads another owner, scans topic/source inventory, hand-authors bytes, creates a journal or recovery operation, retries, rebases, force-writes, syncs framework state, deploys, or ships.

### Inspect and preview

Call `migration.prepare_vocabulary_domain_insertion` with exactly `{"domain_id":"<retained-domain-id>"}`.

- `candidate` → `outcome:"completed"`, `effect:"none"`, `next:null`; expose the domain ID, binding and vocabulary revisions, candidate identity, exactly one human-visible row change, and the byte-exact approval literal, but never `preimage_text`, `text`, registry bytes, profile path, or host path.
- compatible `no-op` → `outcome:"completed"`, `effect:"none"`, `next:null`; state that the exact ID is already a compatible domain and expose no approval, apply guidance, or commit authority.
- invalid ID, malformed registry, incompatible row, token conflict, binding drift, unavailable operation, or I/O rejection → `outcome:"blocked"`, `effect:"none"`, `next:null`; expose only normalized findings and no candidate or literal.

Preview performs no apply. A preview result, returned literal, prior migration approval, engineering approval, framework-sync approval, or shipping approval is not apply approval.

### Separately approved commit

A fresh `migrate` request must bind the exact returned `domain_id`, `instance_id`, `candidate_sha256`, and byte-exact `APPLY ATLAS VOCABULARY DOMAIN INSERTION V1 …` literal and receive its own candidate-bound Goal/Effect approval. Call `migration.apply_vocabulary_domain_insertion` only with `{domain_id,instance_id,candidate_sha256,approval}`, copying all four values unchanged.

- pre-effect approval, stale, unavailable, or I/O rejection → `outcome:"blocked"`, `effect:"none"`, `next:null`; never silently no-op, regenerate guidance, or apply a replacement candidate;
- terminal `applied` / façade `completed` → `outcome:"completed"`, `effect:"committed"`, `next:null`;
- terminal `rolled-back` / façade `no-write` with proven exact preimage → `outcome:"blocked"`, `effect:"none"`, `next:null`;
- terminal `manual-conflict` / façade `manual-intervention` → `outcome:"blocked"`, `effect:"unknown"`, `next:null`; every affected item marks `recovery_required:true`, but that flag grants no executable recovery.

Never call a recovery operation, generic transaction, second forward apply, or another migration. After any terminal, taxonomy backfill or source remediation is eligible only through a separately requested fresh preview and later separate approval. No candidate, approval, request, transaction, recovery identity, or automatic control flow transfers.

## Candidate-bound vocabulary-subdomain insertion

Preview and apply are separate fresh `/atlas-ask` invocations with separate unchanged approvals. This lineage never invokes vocabulary-domain insertion, taxonomy backfill, or source remediation; inserts or activates the parent; loads another owner; scans topic/source inventory; hand-authors bytes; creates a journal or recovery operation; retries; rebases; force-writes; syncs framework state; uses Git; deploys; or ships.

### Inspect and preview

Call `migration.prepare_vocabulary_subdomain_insertion` with exactly `{"subdomain_id":"<retained-subdomain-id>","parent_domain_id":"<retained-parent-domain-id>"}`.

- `candidate` → `outcome:"completed"`, `effect:"none"`, `next:null`; expose both IDs, binding and vocabulary revisions, candidate identity, exactly one human-visible row change, and the byte-exact approval literal, but never `preimage_text`, `text`, registry bytes, profile path, or host path.
- compatible `no-op` → `outcome:"completed"`, `effect:"none"`, `next:null`; state that the exact child is already a compatible subdomain under the named parent and expose no approval, apply guidance, or commit authority.
- invalid ID, malformed registry, missing/inactive/incompatible parent, incompatible child, token conflict, binding drift, unavailable operation, or I/O rejection → `outcome:"blocked"`, `effect:"none"`, `next:null`; expose only normalized findings and no candidate or literal. A parent conflict never invokes parent insertion or activation.

Preview performs no apply. A preview result, returned literal, domain-insertion approval, source-remediation approval, backfill approval, engineering approval, framework-sync approval, Git authority, or shipping approval is not apply approval.

### Separately approved commit

A fresh `migrate` request must bind the exact returned `subdomain_id`, `parent_domain_id`, `instance_id`, `candidate_sha256`, and byte-exact `APPLY ATLAS VOCABULARY SUBDOMAIN INSERTION V1 …` literal and receive its own candidate-bound Goal/Effect approval. Call `migration.apply_vocabulary_subdomain_insertion` only with `{subdomain_id,parent_domain_id,instance_id,candidate_sha256,approval}`, copying all five values unchanged.

- pre-effect approval, stale, unavailable, or I/O rejection → `outcome:"blocked"`, `effect:"none"`, `next:null`; never silently no-op, regenerate guidance, insert/activate a parent, or apply a replacement candidate;
- terminal `applied` / façade `completed` → `outcome:"completed"`, `effect:"committed"`, `next:null`;
- terminal `rolled-back` / façade `no-write` with proven exact preimage → `outcome:"blocked"`, `effect:"none"`, `next:null`;
- terminal `manual-conflict` / façade `manual-intervention` → `outcome:"blocked"`, `effect:"unknown"`, `next:null`; every affected item marks `recovery_required:true`, but that flag grants no executable recovery.

Never call a recovery operation, generic transaction, second forward apply, or another migration. After any terminal, vocabulary-domain insertion, taxonomy backfill, or source remediation is eligible only through a separately requested fresh preview and later separate approval. No candidate, approval, request, transaction, recovery identity, or automatic control flow transfers.

## Candidate-bound source-taxonomy remediation

Each preview, apply, and recovery phase is one fresh `/atlas-ask` invocation with its own unchanged Goal/Effect approval. This lineage never invokes taxonomy backfill, vocabulary-domain insertion, or vocabulary-subdomain insertion; reads or writes `VOCAB.md` directly; loads another owner; reroutes; resummarizes; researches; syncs framework state; deploys; ships; retries; or reconstructs recovery.

### Inspect and preview

Call `migration.prepare_source_taxonomy_remediation` with exactly `{}`.

- `no-op` → `outcome:"completed"`, `effect:"none"`, `next:null`; expose no approval or commit authority.
- `candidate` → `outcome:"completed"`, `effect:"none"`, `next:null`; items carry the returned binding and inventory identity, ordered 13-target human-visible changes, candidate identity, and byte-exact approval literal, but no artifact text.
- Any target, observation, vocabulary-precondition, closure, snapshot, binding, or availability rejection → `outcome:"blocked"`, `effect:"none"`, `next:null` with every normalized finding and no candidate/approval.

### Separately approved commit

A fresh `migrate` request must bind the exact returned instance ID, candidate SHA-256, and byte-exact `APPLY ATLAS SOURCE TAXONOMY REMEDIATION V1 …` literal, then receive its own candidate-bound approval. Call `migration.apply_source_taxonomy_remediation` only with `{instance_id,candidate_sha256,approval}` and copy all three values unchanged.

- pre-effect rejected, stale, or unavailable → `outcome:"blocked"`, `effect:"none"`, `next:null`;
- terminal `applied` / façade `completed` → `outcome:"completed"`, `effect:"committed"`, `next:null`;
- terminal `aborted|rolled-back` / façade `no-write` with proven exact preimages → `outcome:"blocked"`, `effect:"none"`, `next:null`;
- façade `recovery-required` with an exact output prefix → `outcome:"blocked"`, `effect:"partial"` and copy only `{operation:"migration.recover_source_taxonomy_remediation",identity:<returned transaction_id>}` to `next`;
- façade `recovery-required` with unreadable or disagreed observation → `outcome:"blocked"`, `effect:"unknown"` and copy the same exact returned operation/identity to `next`;
- terminal `manual-conflict` → `outcome:"blocked"`, `effect:"unknown"`, `next:null`; every item marks `recovery_required:true` and grants no executable authority.

### Exact named recovery

Only a fresh request containing the façade-returned source-remediation recovery may receive approval for recovery. Call `migration.recover_source_taxonomy_remediation` with exactly `{version:1,transaction_id,request:{instance_id,candidate_sha256,approval}}`, where `request` is byte-identical to the original decoded apply args. Consume only the returned journal-derived terminal using the same applied, aborted/rolled-back, recovery-required, or manual-conflict mapping above. Never substitute a transaction ID, rebuild request fields, regenerate a candidate from partial state, use generic `transaction.recover`, create a successor, or call recovery after a pre-intent rejection.

After committed source remediation, a taxonomy-backfill, vocabulary-domain-insertion, or vocabulary-subdomain-insertion preview is eligible only as a separate fresh explicitly requested and approved invocation. It shares no candidate, approval, request, transaction, recovery, or automatic control flow with this lineage.

## Resume ceiling

This owner may return `needs-guidance` once and has a maximum of two owner turns. Guidance may resolve only semantics inside the unchanged approved Goal/Effect from already-bound contracts or conversation evidence. Repeated guidance, a short cycle, a wider effect, or an exhausted ceiling is `blocked`. There is no post-dispatch `needs-user` resume.

## Result and recovery

Return exactly `version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`, with `owner: atlas-maintain`. Use only schema-defined outcome/effect pairs. Audit, prepare, preview, and every observed no-write path use `effect: none`.

Journal-backed `partial|unknown` returns `outcome: blocked` and copies only the exact façade-returned `{operation,identity}` into `next`. Taxonomy-backfill, vocabulary-domain-insertion, vocabulary-subdomain-insertion, and source-taxonomy-remediation terminal `manual-conflict` use `blocked|unknown|next:null`, and every item marks `recovery_required:true`; that flag is not executable authority. Vocabulary candidate/no-op preview maps to `completed|none|next:null`; invalid/parent-conflict/conflict/stale/unavailable prepare and pre-effect apply rejection map to `blocked|none|next:null`; `applied` maps to `completed|committed|next:null`; proven `rolled-back` maps to `blocked|none|next:null`. Never infer success, add recovery metadata, expose registry text, or expose a recovery path when the façade returned none. Otherwise `next` is `null`.