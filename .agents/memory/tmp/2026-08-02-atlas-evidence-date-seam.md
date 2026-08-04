<!-- provisional-plan: local://repo-agent-memory-first-draft-plan.md -->

# Raw lineage bundle: Atlas evidence-date and source-worker transport seams

This repository-visible file is one temporary raw lineage bundle. It is un-ingested input, not a promoted memory record, and must remain separate from living Atlas state under `vault://atlas/`.

## Disposition groups

### 1. Qualified / already encoded

`source.prepare` locally supplies inventory-owned `checked_on` only when a ready evidence bundle omits both `first_seen` and `fetched_at`; it creates one effective mapping with `first_seen = checked_on`, reuses it through `_evidence_identity`, `merge_artifact`, and summary validation, does not mutate the worker packet, and preserves fail-closed handling for any supplied invalid value.

### 2. Merged mechanism

One effective evidence mapping must flow through every downstream consumer; keep this with the qualified lesson rather than as a separate final claim.

### 3. Rejected ownership expansion

Workers and `source-worker-result.schema.json` must not be required to synthesize registry-owned dates.

### 4. Rejected fallback expansion

Direct `source.merge_artifact` callers retain explicit-date validation because they have no inventory-owned `checked_on`.

### 5. Rejected/transient material

The historical snapshot/parser signature was not reproducible at the declared target; manifest revisions, fixture values, agent status, probe output, and generic schema advice remain provenance rather than durable claims.

## Reported implementation and verification lineage

The following implementation/verification-lineage target paths and SHA-256 values are reported by the named lineage; not recomputed while preserving this raw input:

- `scripts/atlas_source.py` — `39f6bbe5853885c9331df566337c367c144cafd8eb6e0eed6ac3ea1ccee46a2d`
- `tests/test_atlas_tool.py` — `4521a26fb39cb84a198768b0d88faa79a8475057749dd3067478952a09826e57`
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — `354b4b8b0dba94d04482f95e567e7dd53e85a2e14a4b9a4179d16c52e9465430`
- `.agents/skills/atlas-source/SKILL.md` — `54015e082ea3f8a54c8913bf9e2b39bcbd26162f25a07b699e5aa7511e541eb7`
- unchanged `.agents/skills/atlas-core/assets/source-worker-result.schema.json` — `7aa0b607f8aa9b5d38ab1d3f0f30ede6e2cad44cbb78a27604ebeac16d4e3570`

## Session evidence handles

The following lineage handles are session evidence rather than portable repository authority:

- `agent://DiagnoseAtlasIngestion`
- `agent://ImplementEvidenceDateSeam`
- `agent://VerifyEvidenceDateSeam`
- `agent://ReviewEvidenceDateSeam`
- `agent://AssessEvidenceDateLearning`

The lineage-reported `4/4 OK` is attributed to `agent://VerifyEvidenceDateSeam`; final review approval is attributed to `agent://ReviewEvidenceDateSeam`; and `CURATED` is attributed to `agent://AssessEvidenceDateLearning`. These outcomes are session evidence and were not rerun while writing this raw file.

## Explicit evidence gap

No dedicated direct-merge missing-date unit test exists in the immutable target; that retained behavior is grounded by static inspection only.

## Separation boundary

Keep this temporary repository input separate from living Atlas state under `vault://atlas/`; never copy Atlas topic rows or passes into `.agents/memory/`.


## Subsequent settled sourcing lineage

The evidence-date fix remained correct, but it addressed only one gate in the end-to-end source-worker path. Later retries exposed additional independent contract gaps. Each earlier fix allowed the packet to advance far enough to reveal the next latent gap; that progression does not invalidate the earlier fixes.

### Attempt accounting

- Across the reported live lineage, the user ran three earlier `swarm` source invocations. Each stopped without Atlas writes.
- After the transport and correction-handoff fix, the same-session execution dispatched exactly one actual source-drafting subagent, `DraftSwarmSource`. Its first and only terminal result was a complete `kind:"ready"` packet; `source.prepare` accepted it without a correction or source-worker retry.
- The resulting prepared source transaction and required route transaction both applied. Two later read-only route-verifier subagents classified candidate topics; they were not additional source-worker attempts.
- Diagnostic schema-probe subagents were no-Atlas-effect transport experiments. Do not count them as live sourcing attempts.
- The reported sequence therefore contains four actual source-worker attempts: three earlier failed invocations plus the one final successful invocation.

### Failure stack

1. **Acquisition-date ownership:** a worker packet could omit both `first_seen` and `fetched_at`, although routine preparation already had authoritative inventory-owned `checked_on`. The preparation-local fallback recorded above fixed this without requiring workers to invent registry dates.
2. **Nested packet contract:** the canonical worker-result schema described itself as the strict packet union while leaving `proposal` and `evidence_ledger` structurally opaque. A worker could satisfy the advertised schema and still fail downstream proposal/ledger validation. The schema was tightened to reference the canonical proposal schema and a closed evidence-ledger shape, while semantic tuple binding remained runtime-owned.
3. **Evidence-envelope contract:** `evidence_bundle` was still too opaque to require its stable core. A worker could omit `version`, `canonical_url`, or nonempty `payload_text` and pass the advertised worker schema before failing preparation, including the observed `EVIDENCE_VERSION_INVALID` rejection. The schema now owns only that minimum core and keeps projection/hash/range/list/media/caveat semantics in existing runtime validators.
4. **Initial worker transport:** prompt text requested a complete packet, but the Task dispatch had no native strict output schema. The worker returned a partial `kind:"ready"` object with a corrupt evidence key and without required top-level fields. This was not an Atlas reducer or transaction failure; malformed generation crossed an unenforced transport boundary.
5. **Schema-dialect mismatch:** the canonical schema could not be passed directly to the Task transport because it contained a sibling proposal `$ref`, proposal-local refs after naive embedding, and checklist `allOf` refinements unsupported by the transport surface. A deterministic, fail-closed projection now derives one finite, reference-free Task schema from the canonical worker and proposal schemas. It is generation guidance, not a second authoritative validator.
6. **Correction handoff:** on an earlier retry, the assigned worker returned the complete corrected packet in the synchronous same-worker reply. The coordinator then reread the stale initial terminal artifact and incorrectly required another publish or yield. The direct reply was the correction result; treating it as missing worker output converted a successful correction into a false terminal no-write.

### Root-cause synthesis

The repeated failures were not one unexplained flaky-subagent problem. The framework split one packet contract across canonical JSON Schema, prompt-only transport, downstream semantic validators, and an ambiguous correction-publication convention. Validation remained correctly fail-closed, but invalid packets were rejected progressively at later gates.

For future diagnosis, trace the complete path before changing one validator in isolation:

```text
canonical packet schema
→ harness-compatible native output schema
→ initial worker delivery
→ complete-object handoff
→ source.prepare structural and semantic validation
→ one synchronous same-worker whole-packet correction
→ prepared transaction
```

The robust boundary is:

- derive the harness schema deterministically from canonical assets rather than copy-maintaining another schema;
- fail closed on unreadable, malformed, external, cyclic, dynamically referenced, or shape-drifted schema assets;
- bind every initial source worker to the native strict schema;
- pass the complete worker object unchanged to `source.prepare`;
- keep `source.prepare`, evidence validation, checklist validation, proposal/ledger tuple binding, rendering, and transaction construction authoritative;
- on one `needs-revision`, consume the same worker's synchronous direct reply as one complete replacement JSON body;
- never reread the stale initial result, merge fields, reconstruct evidence, strip prose/code fences, require a second publication, add persistence, or add another retry.

### Efficient proof and retry discipline

- Before another live source write, use the generated schema in no-Atlas-effect harness probes that prove both sides of the boundary: complete `ready`/`no-write` packets succeed, legal extensible evidence survives, and the recorded partial `ready` packet is rejected by the transport.
- Run implementation smoke after the cohesive contract change, then one independent verification and one distinct review against a bound immutable target. Do not turn every intermediate correction into a verifier/reviewer loop.
- A later gate exposing a different legitimate rejection is not evidence that a prior narrow fix was false. Reassess whether the earlier fix preserved its ownership boundary, then repair the newly proven owner without adding source-specific fallbacks.

## Final observed `swarm` outcome

The final same-session run reported:

- canonical URL: `https://github.com/cursor/plugins/blob/main/pstack/skills/swarm/SKILL.md`
- source ID: `c836a9a1d3a3`
- source sequence: `633`
- source status: `active`
- route status: `routed`
- content hash: `9acc699c0478dc62618f2e45fb4b902f434b079b23c50cc3756689e8187d392d`
- artifact revision: `sha256:3770c16a93904bb875b3b42ada4f8db13a309053f5d7f53111433c5205f3735e`
- MANIFEST revision: `sha256:ea4f4c8b64185bb1927739d5cba91fbf079daaa039ad57ebb307da8f3e69ac1a`
- RELATIONS revision: `sha256:aabc9dacef7991a7e58508b3bb5c49f1d7069c237bee954971c5603e8172d2a6`
- TOPICS revision: `sha256:3feb7097eabeb0b600e71b41bb4c8b08768a0505bbe07610273fffd19360438e`
- source receipt SHA-256: `66694d573912e9fa501db8916543e17d82c35b97a46b66184cca6e7a929299b1`
- route receipt SHA-256: `862b686a31dbb779659cda6642bc56cb9c470e5e4a540c0dd190a25d325d1f82`

The route created two pending edges, for `agentic-harness-architecture` and `ai-coding-workflow`. Pending topic refresh is a separate normal workflow, not an incomplete source ingestion.

## Subsequent reported target and assurance lineage

The following final target identities are reported by the independently verified and reviewed lineage; they are retained here as provenance rather than recomputed memory authority:

- `.agents/ARCHITECTURE.md` — `0abb364fb01d576173cc4d757af03308f5efc7d154b8791aee53ac1dea9b2114`
- `.agents/skills/atlas-core/SKILL.md` — `5d3e5dab94d3399f007ef56a008899f1ad715c7bb6db72c7fbb7e4c27dd41c12`
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — `725e60171174ee88b8f283069ed28532ca54a7d4b6a7571ad76ac4a26fb24b93`
- `.agents/skills/atlas-core/assets/source-worker-result.schema.json` — `fec5397db2d857735dd704e7f65eef59cac4aa051ead11e8d0292e8bd7d5518e`
- `.agents/skills/atlas-core/assets/source-summary-proposal.schema.json` — `a52b340a1affd4d572dd914b8e0be604152a1fdaf9b7044890f9c15b0edb0a3f`
- `.agents/skills/atlas-source/SKILL.md` — `2072bffe232b716e9c37db386571cd09948e70138305319c131e3e5687379c20`
- `scripts/atlas_source.py` — `5cfdda3ab2c276c3954a34f6e9906b74388c51149089533e9d58ef0df96c89b6`
- `scripts/atlas_tool.py` — `77742c397777c9cac95fcacee452c0fb800b06a3b5caea7001a410f224fe6afd`
- `tests/test_atlas_tool.py` — `596bd5ddf1bdca4bdf59de2e43d5c2096a38fd5a9602d7760e52a0a4f823de82`
- `tests/test_atlas_harness_surface.py` — `5d6d238b336b70edc1f37dfa7a4eda388ba2b35d97c3c03fdeaaf85e918b2353`

Later session evidence handles:

- `agent://DiagnoseProposalLedgerRetry`
- `agent://ImplementWorkerNestedContract`
- `agent://VerifyWorkerNestedContract`
- `agent://ReviewWorkerNestedContract`
- `agent://AssessNestedContractLearning`
- `agent://DiagnoseEvidenceEnvelopeRetry`
- `agent://ImplementEvidenceCoreContract`
- `agent://VerifyEvidenceCoreContract`
- `agent://ImplementWorkerTransport`
- `agent://DraftSwarmSource`
- `agent://VerifySwarmRecoveryTarget`
- `agent://ReviewSwarmRecoveryTarget`
- `agent://AssessSwarmRecoveryLearning`

The final independent verifier reported two consecutive focused-suite runs of `80 tests ... OK`, successful native strict delivery of a valid terminal packet, provider-side rejection of an incomplete `ready` packet, valid live state and receipt identities, and `atlas-instance.py check` success. The distinct reviewer reported Standards `PASS`, Specification `PASS`, and Overall `APPROVED`. The terminal assessment reported `NO DURABLE LEARNING` because the reusable corrections were already encoded in canonical product guidance.

The completed execution plan is archived at `.agents/plans/archive/2026-08-02-1452_swarm-source-recovery.md`, reported SHA-256 `676242214f6350c2470688f821ae82f6b34669456628b3dd1f3feebdacde5cb6`.

## Deferred or transient raw observations

- The route transaction was first supplied in noncanonical target order and was rejected before any write; the existing canonical target-order contract already prevented damage, so this is not a new durable rule.
- The independent verifier gathered detailed evidence but its structured handoff schema allowed empty evidence arrays. This is one process observation without a second settled recurrence or severe consequence; retain it as raw input, not promoted guidance.
- An unrelated concurrent `.agents/AGENTS.md` memory-layout change caused target drift during verification. The verifier rebound to the preserved current file and reran all required evidence. Existing target-identity and concurrent-change discipline already owns this behavior.