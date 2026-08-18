# Atlas bound-instance framework snapshot sync

**Datetime**: 2026-08-18-1451
**Authority kind**: local-authority
**Scope**: One-instance product-owned framework snapshot sync for bound instance `atlas`
**Summary**: Replace only the stale `vault://atlas/ARCHITECTURE.md` product-owned snapshot with the exact current product architecture bytes, then prove equality and run the instance-wide read-only check. Do not mutate living instance state or any other instance.
**Status**: DONE
**Completed At**: 2026-08-18-1527

## Context

Product HEAD `7aa30466167a7bd8ba9c5558e2fa0da7732854ec` contains `.agents/ARCHITECTURE.md` at SHA-256 `c995908e5aa8b31e7d9584015a4420e709969cb92f43917ae5bb251572928a77`; qualified nonempty source flows and `promote|reroute` read its bound-instance snapshot. The only discovered instance is `atlas`, whose snapshot currently hashes to `371e63ae11a68ec065c1895fc679a95270e701b3064c0e9c2a9334a6e5984ac6`; the current dry-run reports only `ARCHITECTURE.md` as changed. The intended end state is exact byte equality at the product digest, reached only through `scripts/atlas-instance.py sync-framework --name atlas` after a separate instance-write approval.

## Tasks

- [x] T1. Revalidate the exact single-instance sync effect
  completed 2026-08-18-1523
- [x] T2. Obtain effect approval and sync the snapshot
  completed 2026-08-18-1526
- [x] T3. Prove snapshot equality and classify check findings
  completed 2026-08-18-1527

## Approach

### T1. Revalidate the exact single-instance sync effect

From `/Users/kim/dev/atlas/app`, run:

```text
sha256sum .agents/ARCHITECTURE.md ../vault/instances/atlas/ARCHITECTURE.md
python3 scripts/atlas-instance.py sync-framework --name atlas --dry-run
```

Require all of the following before proposing any write:

- The product digest is exactly `c995908e5aa8b31e7d9584015a4420e709969cb92f43917ae5bb251572928a77`.
- The manifest projection is exactly one `product_owned` mapping, `.agents/ARCHITECTURE.md` to `ARCHITECTURE.md`; its seven `seed_once` paths remain inventory only.
- The envelope is version `2`, `ok:true`, `op:"instance.sync-framework"`, `disposition:"no-write"`, `findings:[]`, and `result.dry_run:true`.
- `result.instances` contains only `atlas`; for the observed stale state, `changed:["ARCHITECTURE.md"]`, `unchanged:[]`, and aggregate counts `instances:1`, `product_owned_per_instance:1`, `changed:1`, `unchanged:0`.
- The destination digest remains `371e63ae11a68ec065c1895fc679a95270e701b3064c0e9c2a9334a6e5984ac6`.

If the destination already equals the required product digest and the dry-run instead reports `changed:[]` and `unchanged:["ARCHITECTURE.md"]`, skip T2's approval and write, then execute T3 as an already-satisfied no-write outcome. If the product digest, destination stale digest, selected instance, mapping, changed destination set, or envelope differs in any other way, stop before mutation and report the changed identity/effect; do not substitute `--all`, another instance, or another product digest.

### T2. Obtain effect approval and sync the snapshot

After T1 passes, request a separate human approval with this exact effect boundary:

```text
Goal: Synchronize the product-owned architecture snapshot for bound instance `atlas`.
Effect: Overwrite only `vault://atlas/ARCHITECTURE.md`, from SHA-256 `371e63ae11a68ec065c1895fc679a95270e701b3064c0e9c2a9334a6e5984ac6` to `c995908e5aa8b31e7d9584015a4420e709969cb92f43917ae5bb251572928a77`, using `python3 scripts/atlas-instance.py sync-framework --name atlas`. Do not overwrite seed_once files or living instance data.
Reply approve to run this instance write.
```

Plan approval, product-package approval, and the earlier dry-run do not grant this instance write. After explicit approval, immediately rerun both T1 commands and require the same digests and dry-run effect to close the time-of-check/time-of-use gap. Then run exactly:

```text
python3 scripts/atlas-instance.py sync-framework --name atlas
```

Require a version-2 success envelope with `ok:true`, `op:"instance.sync-framework"`, `disposition:"completed"`, `result.dry_run:false`, only instance `atlas`, and the same one-file pre-write comparison. Do not run `create`, `--all`, `/atlas-ask migrate`, a hand copy, a scaffold edit, or any source/registry/topic/pass/todo/editor/profile operation.

If the write command fails or returns an unexpected envelope, do not retry it. Proceed only with T3's read-only byte, dry-run, and check commands to classify actual state, then report the command failure and observed bytes; a nonmatching destination remains blocked for fresh human recovery authority.

### T3. Prove snapshot equality and classify check findings

Run, in order:

```text
cmp -s .agents/ARCHITECTURE.md ../vault/instances/atlas/ARCHITECTURE.md
sha256sum .agents/ARCHITECTURE.md ../vault/instances/atlas/ARCHITECTURE.md
python3 scripts/atlas-instance.py sync-framework --name atlas --dry-run
python3 scripts/atlas-instance.py check --name atlas
```

Require `cmp` exit `0`; both digests exactly `c995908e5aa8b31e7d9584015a4420e709969cb92f43917ae5bb251572928a77`; the post-state dry-run to report `changed:[]`, `unchanged:["ARCHITECTURE.md"]`, `changed:0`, and `unchanged:1`; and `check` to contain no `INSTANCE_PRODUCT_OWNED_MISSING` or `INSTANCE_PRODUCT_OWNED_DRIFT` finding for `instance/atlas/ARCHITECTURE.md`. The currently observed pre-sync check has exactly the one drift finding, so a clean post-sync state is expected to return `ok:true`, `disposition:"no-write"`, and `findings:[]`.

If `check` reports only findings outside the selected product-owned snapshot while byte comparison and the post-state dry-run pass, report the snapshot sync as complete and preserve every finding as a separate, separately authorized maintenance or administration candidate; do not repair living rows, seed paths, scaffold integrity, or other surfaces. If byte comparison fails, the post-state dry-run still reports drift, or `check` reports a product-owned missing/drift finding for `instance/atlas/ARCHITECTURE.md`, report this plan as failed and stop without retry or hand repair. Report the pre- and post-sync digests and the final command dispositions; do not commit, push, deploy, rewrite a profile, use credentials, or sync another instance.

## Critical files & anchors

- `.agents/ARCHITECTURE.md` — authoritative product source; source lifecycle lines 183–192 contain the inventory gating, `source.prepare_route`, and route-date preservation behavior this snapshot must carry.
- `scaffold/MANIFEST.json` — sole projection authority; `product_owned[0]` maps `.agents/ARCHITECTURE.md` to `ARCHITECTURE.md`, while seven `seed_once` paths are excluded from sync.
- `scripts/atlas-instance.py` — `cmd_sync_framework` (lines 418–473) compares and overwrites only manifest-declared product-owned files; `cmd_check` (lines 488–569) also audits seed structure and living registries.
- `../vault/instances/atlas/ARCHITECTURE.md` (`vault://atlas/ARCHITECTURE.md`) — the one approved destination; never edit it directly.

## Verification / Done criteria

- [x] The pre-effect dry-run targets only `atlas`, reports only `ARCHITECTURE.md` changed, and exposes exactly one product-owned mapping plus seven untouched seed-once paths.
- [x] A separate explicit human approval binds instance `atlas`, the one destination, and the exact old-to-new digest transition before the non-dry-run command.
- [x] Exact byte comparison exits `0`, and both source and destination report SHA-256 `c995908e5aa8b31e7d9584015a4420e709969cb92f43917ae5bb251572928a77`.
- [x] A post-state dry-run reports `ARCHITECTURE.md` unchanged and no changed product-owned destination.
- [x] `check --name atlas` reports no product-owned missing/drift finding for `instance/atlas/ARCHITECTURE.md`; every unrelated finding is preserved and reported without repair.
- [x] The completion report records write/no-write disposition, both final digests, check disposition/findings, and confirms that no other instance or instance surface was mutated.

## Assumptions & contingencies

- This plan binds exactly the discovered `atlas` instance at the administration CLI's default instances root. Naming a different instance or a fleet requires a revised, separately approved plan; never widen this plan with `--all`.
- The approved product effect identity is the architecture digest plus the manifest's one product-owned mapping, not merely the current Git HEAD. An unrelated HEAD change may proceed only if both remain identical; any effect-identity change requires plan revision and fresh approval.
- An already-equal destination is a successful no-write completion. A newly different nonmatching destination is possible user or process drift and must not be overwritten under the stale digest transition.
- The holistic `check` command may expose living-registry, seed-structure, scaffold-integrity, or other defects that this snapshot sync neither causes nor authorizes. Direct byte equality and a clean post-state sync dry-run determine snapshot completion; unrelated findings become separately authorized maintenance or administration outcomes.

## Completion Summary

- Write disposition: `completed`; `python3 scripts/atlas-instance.py sync-framework --name atlas` reported only instance `atlas` and only `ARCHITECTURE.md` changed. The framework inventory remained one `product_owned` mapping and seven untouched `seed_once` paths.
- Pre-sync SHA-256: source `c995908e5aa8b31e7d9584015a4420e709969cb92f43917ae5bb251572928a77`; destination `371e63ae11a68ec065c1895fc679a95270e701b3064c0e9c2a9334a6e5984ac6`.
- Final proof: `cmp -s` exited `0`; both source and destination SHA-256 values are `c995908e5aa8b31e7d9584015a4420e709969cb92f43917ae5bb251572928a77`.
- Post-state dry-run disposition: `no-write`, with `changed:0`, `unchanged:1`, and `ARCHITECTURE.md` unchanged for only `atlas`.
- Instance check disposition: `no-write`, `ok:true`, `findings:[]`; no product-owned missing/drift or unrelated findings remain.
- No other mutation command ran. No other instance or instance surface was mutated; no commit, push, deploy, profile rewrite, credential use, or additional sync occurred.
