# atlas-migrate

## Qualified invocation

This ordinary Workflow Owner resource may execute only when one of these qualified conditions holds:

1. The selected Workflow Owner receives a live `/atlas-ask` Task whose dispatch binding names `atlas-migrate`.
2. An allowlisted current Workflow Owner loads this resource as a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
3. Any other load performs no further read, model work, façade call, profile/vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

Only the selected Workflow Owner emits one outer `atlas-workflow-result.schema.json` result. A Successor Owner preserves its native current output and never creates another Task or outer result.



## Read first

1. `vault://atlas/ARCHITECTURE.md` (runtime snapshot; author product text at `.agents/ARCHITECTURE.md`)
2. `skill://atlas-core/SKILL.md`
3. `skill://atlas-core/assets/markdown-registry-contracts.md`
4. `skill://atlas-core/assets/operating-cadence-and-guardrails.md`
5. only the declared migration-scope artifacts

## Façade-first workflow

- Handle only an explicit, approved Atlas Markdown migration. The request must identify the old and new shape, exact target artifacts, eligibility/scope, preservation rule for unmanaged content, deterministic verification boundary, and rollback authority before any write.
- Begin with `scripts/atlas_tool.py capabilities`. Read each declared target through `vault.read` and bind its current revision with `vault.hash`; inspect only the named logical scope. Do not resolve a profile/root, use host-path I/O, invoke underlying Python owners, or recompute state/revisions/CAS mechanics.
- Use `state.validate` for each compatible complete registry bundle before planning and after each candidate. Use `state.reduce` only where the migration's declared change is an existing contract-defined reducer event; never forge reducer output or claim a newer schema is validated by a core contract that does not define it.
- Freeze the approved target list and exact expected revisions before the first mutation. Apply only approved candidate bytes through `vault.conditional_replace`, and accept a write only from its façade acknowledgement. A conflict, unexpected revision, missing acknowledgement, or validation failure halts the migration before any wider effect.
- Keep rollback explicit and scoped: use `transaction.execute`, `transaction.recover`, or `transaction.successor` only when the migration includes a core-allowlisted source/route transaction, and follow its receipt gate. Do not invent a transaction record, connector rollback, deletion, or recovery protocol for another schema change. When no applicable transaction contract exists, the approved migration must define its artifact-by-artifact rollback boundary; a failed boundary halts for a new explicit recovery/migration decision, never a force-write.
- Prefer additive, row-by-row or artifact-by-artifact changes and preserve user-owned content and unmanaged sections. Reject storage, retrieval, canonical-owner, or write-target changes that the architecture and declared migration scope do not authorize.
- If the migration changes product-owned `.agents/ARCHITECTURE.md`, identify intended bound instances, obtain required approval before non-development writes, sync only those named instances, then run the existing instance check. Update `scaffold/` templates only when empty-state shape changes; never re-seed living rows.

## Output

Report the approved old/new shape, exact logical scope, preconditions, named façade operations and any transaction receipts, applied/rolled-back/halted status per target, and the verification result. Do not relabel a conflict or incomplete rollback as a completed migration.
