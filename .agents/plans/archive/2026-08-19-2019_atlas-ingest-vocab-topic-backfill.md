# Atlas ingest vocabulary and topic backfill

**Datetime**: 2026-08-19-2019
**Authority kind**: local-authority
**Scope**: Atlas product contracts, source ingestion vocabulary promotion, topic-scoped source discovery, research backfill orchestration, evidence-rank enforcement, and their deterministic tests
**Summary**: Let routine ingest and changed-hash resummarization promote a capped source-intrinsic vocabulary, then let later approved research create a topic and backfill eligible active sources before refresh and publication.
**Status**: DONE
**Completed At**: 2026-08-20-1710

## Objective

- Outcome: OUT-ATLAS-VOCAB-BACKFILL
- Observable end state: A personal researcher can ingest a URL whose subject has no topic, retain canonical subject IDs on the source, and later create and research that topic with deterministic backfill of preexisting active sources.
- Progress signal: Only an owned acceptance criterion or an exact named blocker advances the outcome; file count, elapsed time, and partial scaffolding do not.

## Authority

| Authority ID | Kind | URI | Revision | Approval |
|---|---|---|---|---|
| AUTH-USER-HANDOFF | Direct user product and plan-creation authority | `conversation://2026-08-19/final-plan-creation-handoff` | `user-handoff-r1-2026-08-19` | Parent outcome and original plan creation approved; implementation was not approved. |
| AUTH-REVISION-HANDOFF | Direct user corrective plan authority | `conversation://2026-08-19/revision-handoff/atlas-ingest-vocab-topic-backfill` | `user-revision-handoff-r1-2026-08-19` | Revise and revalidate this same plan identity; implementation remains unapproved until native review binds the revised complete-byte SHA-256. |
| AUTH-REVISION-HANDOFF-R2 | Direct user corrective plan authority | `conversation://2026-08-19/revision-handoff-r2/atlas-ingest-vocab-topic-backfill` | `user-revision-handoff-r2-2026-08-19` | Correct the research-inspection locator/order and schema-versus-prepare classification requirement; implementation remains unapproved until native review binds the new complete-byte SHA-256. |
| AUTH-ARCH-BASE | Current canonical Atlas framework baseline | `repo://.agents/ARCHITECTURE.md` | `sha256:09de9b1cf69fc726932b8a3c45434156cf1e212e5dde15f3e3bf31584290a509` | May be revised only within the listed user handoffs; no bound-instance synchronization authority. |

## Governing decisions

| Decision ID | Revision | Execution effect |
|---|---|---|
| DEC-ARCH-FIRST | `AUTH-ARCH-BASE` | Revise framework write sets and lifecycles before dependent contracts, owners, runtime, or tests. |
| DEC-TWO-JOINS | `AUTH-USER-HANDOFF@user-handoff-r1-2026-08-19` | Implement capped ingest-to-vocabulary promotion and later research-topic-to-source backfill as one cohesive outcome. |
| DEC-FIRST-WRITER | `AUTH-REVISION-HANDOFF@user-revision-handoff-r1-2026-08-19` | Resolve each proposal token set against the existing legal table: insert on zero matches, byte-reuse one compatible match, and degrade every ambiguous or incompatible entry to a non-routing candidate term without blocking source persistence. |
| DEC-READY-COMPAT | `AUTH-REVISION-HANDOFF-R2@user-revision-handoff-r2-2026-08-19` | Keep worker packet version 1: `classification` is an optional closed schema property so existing ready packets validate, while `source.prepare` requires it for new and changed-hash ingest/resummarize. |
| DEC-ONE-READ-SEAM | `AUTH-USER-HANDOFF@user-handoff-r1-2026-08-19` | Add one lifecycle operation type for topic-scoped candidates; keep model glances bounded and all matching in code. |
| DEC-BACKFILL-WINDOW | `AUTH-REVISION-HANDOFF-R2@user-revision-handoff-r2-2026-08-19` | Use research inspection `topic.last_synthesized:null` to open backfill, including a retry after partial route writes; run attach work before any refresh and skip it after first synthesis. |
| DEC-CREATE-RELATION-FREE | `AUTH-USER-HANDOFF@user-handoff-r1-2026-08-19` | Keep standalone topic creation relation-free; research performs eligible backfill routes, refresh when dirty, then the existing four-target publication. |
| DEC-ACCEPTED-RESIDUALS | `AUTH-REVISION-HANDOFF@user-revision-handoff-r1-2026-08-19` | Accept sticky first-writer names, include-term-dependent cheap matching, and an unbounded number of glances inside the no-pass window; do not add search, a cap, or repair behavior. |
| DEC-HIGH-CONSEQUENCE | `skill://dev-implementation@current` | Use high-consequence assurance because this changes stored registry semantics, transaction recovery, and shared schemas; retain one cohesive sequential implementation owner. |

## Scope, non-goals, and prohibited effects

- Read surfaces: Exact repository targets and anchors below, their direct callers and fixtures, current generated operation discovery, and temporary local profiles created by existing tests.
  - Inspect only evidence needed to preserve existing behavior.
  - Discover operations through `python3 scripts/atlas_tool.py capabilities`.
- Change surfaces: Canonical contracts, the seed-once VOCAB policy, the worker schema, registry/source/research runtime seams, owner recipes, front-door Effect bounds, focused tests, and evals listed in the target map.
  - No living row is added to the scaffold.
- Non-goals: Embeddings, full-text search, a search index, multi-source attach events, ingest-created topics, vocabulary deletion/deprecation, source-kind invention, widened reroute-only UX, automatic audit/repair, helper owners, required subagents, pick lists, added resume states, or backfill on every research invocation after a first pass.
  - Also excluded: living attachment of the seven prior trading URLs; research on `mtf-ta-engine-ensemble`; credentials; TradingView login; deploy, release, or framework snapshot sync; source-summary artifact schema changes; canonical URL/source identity changes; relation-enum changes; research-ceiling changes; and topic-create target changes.
- Prohibited effects: No `vault://atlas/` write, bound-instance sync, non-development profile write, credential use, network acquisition, deployment, or Git shipping action during execution or verification.
  - Ingest classification creates no topic file, subdomain index, pass, or topic row.
  - Source ingest and changed-hash resummarize edit, delete, or deprecate no existing VOCAB row and never promote `source-kind`; same-hash paths and `promote` insert no vocabulary.
  - No unmatched source body, `candidate_terms`, or ambient request context reaches the research glance model.
  - No compatibility alias, alternate operation, second Atlas root, helper-owner chain, hidden retry/recovery loop, or new topic-tag requirement is added.

| Effect ID | Kind | Authority | Limit / reversibility |
|---|---|---|---|
| EFF-CONTRACT | Repository contract edit | AUTH-USER-HANDOFF, AUTH-REVISION-HANDOFF, AUTH-REVISION-HANDOFF-R2 | Only listed product Markdown/schema/scaffold targets; reversible before shipping; no instance projection. |
| EFF-RUNTIME | Repository code edit | AUTH-USER-HANDOFF, AUTH-REVISION-HANDOFF, AUTH-REVISION-HANDOFF-R2 | Only listed runtime symbols and generated catalog definitions; only named four-document lifecycle callers opt into VOCAB validation, while existing three-registry callers remain valid. |
| EFF-TEST | Temporary local fixture mutation | AUTH-USER-HANDOFF, AUTH-REVISION-HANDOFF-R2 | Existing temporary connectors/profiles only; fixtures remove every row, artifact, receipt, and empty directory. |

## Fixed shared contracts

| Contract ID | Surface | Owner task | Revision | Consumers |
|---|---|---|---|---|
| CONTRACT-VOCAB | Strict `VOCAB.md` parsing, proposal resolution, insert-only reduction, and artifact bindings | T2 | `atlas-vocab-upsert-r2` | T1, T2, T3 |
| CONTRACT-WORKER | Context-neutral version-1 optional-schema/required-prepare classification and cap validation | T2 | `atlas-source-classification-r3` | T1, T2 |
| CONTRACT-SOURCE-TX | Source event/binding in T2; four-document reads, ordered VOCAB/source/route targets, guard, post-validation, and recovery in T3 | T3 | `atlas-source-transaction-r2` | T1, T2, T3, T4 |
| CONTRACT-CANDIDATE | Topic-scoped candidate operation, four-rule matcher, bounded glance packet, named URL gaps, and revalidation binding | T3 | `atlas-topic-candidates-r1` | T1, T3, T4 |
| CONTRACT-BACKFILL | `topic.last_synthesized` no-pass research backfill before refresh and publication | T4 | `atlas-research-backfill-r3` | T1, T4 |
| CONTRACT-RANK | Direct/high-or-medium answer-authoring eligibility and deterministic publication guards | T5 | `atlas-answer-rank-r1` | T1, T5 |
| CONTRACT-COMPAT | Existing reroute, no-new-subject ingest, version-1 ready schema, no-preexisting-source research, command, envelope, and recovery behavior | T5 | `atlas-compatibility-r3` | T1, T5 |

### CONTRACT-VOCAB

- Add `validate_vocab(vocab_text: str) -> list[Finding]` and change `validate_documents(manifest_text, topics_text, relations_text, *, vocab_text: str | None = None) -> list[Finding]`. Omitting `vocab_text` preserves current three-registry validation; supplying it additionally validates VOCAB. T2 adds these pure seams. T3 is the first lifecycle slice to consistent-read VOCAB and pass `vocab_text` from `source.prepare`, `source.prepare_route`, `state.validate`, and `source.candidates_for_topic`.
- Keep `index.create_topic` and every other existing caller on the three-registry form. Topic creation does not read or write VOCAB. Do not add `scripts/atlas_index.py` as a hidden pass-through target unless a later acceptance criterion explicitly requires create to reject malformed VOCAB; no criterion in this plan does.
- Parse exactly one table with the existing header `ID | Type | Label | Parent | Allowed aliases | Status | Notes`. Require kebab-case IDs matching `[a-z0-9][a-z0-9-]*`, unique IDs, type `domain|subdomain|tag|source-kind`, status `active|deprecated|reserved`, nonblank labels, and the existing canonical semicolon-list codec for allowed aliases. Preserve current parent rules: domain/source-kind parent is empty, subdomain parent names one existing domain, and tag parent is optional; ingest always inserts a new tag with an empty parent. Do not require label or allowed-alias tokens to be unique across rows of any type. Existing source-kind rows, including the seed's repeated `guide` alias, are legal and immutable.
- Resolve one proposal entry by trimming its ID, label, and aliases, applying ASCII `A-Z` to `a-z` folding, and comparing the resulting tokens with every existing row ID, label, and decoded allowed alias. Zero matched rows inserts only when the proposal position is domain, subdomain, or tag. Exactly one compatible row reuses its ID without changing any byte. Two or more matched rows, any source-kind hit, a type mismatch, or a subdomain whose proposed/resolved parent does not equal the resolved domain ID inserts nothing for that entry; append the worker's nonblank label to `candidate_terms` under existing first-winner deduplication and continue preparing the source.
- Insert new rows as `active`; ingest never writes `reserved`. Preserve the worker label and aliases, give a new subdomain the resolved domain ID as parent, give every new tag an empty parent, leave Notes empty, and append in domain, subdomain, then worker tag order without rewriting existing rows or surrounding prose. No source event edits, deletes, deprecates, or repairs a row.
- Resolve domain, then subdomain, then at most three tags. Bind `primary_domain`, `subdomains`, and `canonical_tags` only to IDs present after the upsert. Any unresolved proposal phrase remains in `candidate_terms` and is non-routing. `secondary_domains` stays empty for a new source and unchanged for an existing source.
- A malformed VOCAB table or malformed worker classification stops preparation before transaction targets. Identity ambiguity or incompatibility in an otherwise valid proposal is not a table invariant violation and does not stop source persistence.

### CONTRACT-WORKER

- Keep `source-worker-result.schema.json` packet `version:1`. Add `classification` to `kind:"ready"` properties but not to that variant's `required` array. When present, it is a closed object with exactly required members `domain`, `subdomain`, `tags`, and `candidate_terms`. Domain is null or a closed object with required nonblank string `id`, nonblank string `label`, and unique-nonblank-string array `aliases`; subdomain is null or the same closed object plus required nonblank string `parent`; tags is an array of at most three domain-shaped closed objects; candidate terms is a unique-nonblank-string array. Alias, tag, and candidate-term arrays may be empty. A missing property remains a valid version-1 no-subject ready packet; a present object with null domain/subdomain and empty arrays is also valid. There is no source-kind field.
- The worker remains stateless, tool-free, and context-neutral: it receives only frozen source identity and normalized source evidence. Classification is source-intrinsic and is accepted only after the existing ready proposal, ledger, checklist, and quality gates pass. Runtime preparation enforces kebab-case IDs, list/string shapes, the tag cap, and that a nonnull subdomain's parent equals the resolved nonnull domain.
- `source.prepare` requires the property to be present with a populated-or-empty classification object for a new source and changed-hash ingest/resummarize. Absence in either path returns a deterministic preparation finding and no transaction targets. Same-hash paths and `promote` ignore missing or present classification, preserve existing classification/VOCAB bytes, and insert no vocabulary.
- Do not change `source-summary-proposal.schema.json`. Classification remains an optional ready-worker schema property whose state-dependent requirement is owned only by `source.prepare`, not a second proposal or sidecar schema. T4 adds classification objects to recipe examples and updates eval/front-door Effect language; T2 does not need recipe, harness, or `test_atlas_tool` edits for schema validity.

### CONTRACT-SOURCE-TX

- T2 adds `classification:null|classification-object` to `source-upsert`, reduces a present object against optional `vocab` document bytes, returns resolved bindings plus changed VOCAB bytes, and renders only resolved IDs into the artifact. New and changed-hash preparation never emits this event with null classification; same-hash and `promote` do not insert VOCAB. This classification/event/artifact contract is consumed by T2 even though T3 owns façade reads, target order, transaction guards, and recovery.
- A well-formed ambiguous or incompatible proposal entry adds no VOCAB row, contributes its label to non-routing `candidate_terms`, and does not block the source write. A missing classification for new/changed-hash preparation, a malformed present classification, or a malformed VOCAB document yields deterministic preparation findings and no transaction targets.
- T3 makes a source transaction include VOCAB only when its bytes change. Canonical target rank is VOCAB, source artifact, RELATIONS, TOPICS, MANIFEST; route-only transactions retain their relative artifact, RELATIONS, TOPICS, MANIFEST order. The allowlist, immutable event record, optimistic revisions, rollback, successor, and post-validation cover VOCAB without another approval or recovery mechanism.
- T3 passes the consistently read VOCAB bytes into pure source preparation and route preparation, `state.validate`, and candidate discovery. Post-validation validates VOCAB whenever it was supplied. Existing three-registry callers and `index.create_topic` remain callable without a fourth positional argument.
- T3 updates only façade fixtures that exercise new or changed-hash `source.prepare` to pass an explicit populated-or-empty classification object. Ready packets used only for schema, harness, same-hash, or `promote` compatibility may remain property-absent and valid.
- Same-hash source operations and `promote` never produce a VOCAB target. Changed-hash resummarize may append newly unseen entries but never rewrites an existing row.

### CONTRACT-CANDIDATE

- Add lifecycle consistent-read operation `source.candidates_for_topic` with exact required args `{topic_id,named_urls}` and optional `source_id` for one-pair revalidation. Named URLs normalize/deduplicate in request order; malformed args reject before state reads.
- Under one consistent snapshot, validate MANIFEST, TOPICS, RELATIONS, and VOCAB; select only active manifest rows; verify artifact identity/current content hash; and parse only title plus TL;DR, Key points, and Classification. Return no full body and no projection for an unmatched source.
- The shared pure predicate admits an unnamed pair only when at least one positive rule matches and no exclude term matches: (1) topic domain equals source primary or secondary domain, or topic subdomain is in source subdomains; (2) topic/source canonical-tag sets overlap; (3) a topic alias or include term occurs in source title, TL;DR, or Key points; (4) no topic exclude term occurs in those fields. Candidate terms are ignored. Text matching uses NFKC, Unicode casefold, non-alphanumeric-to-space normalization, whitespace collapse, and contiguous token-sequence matching; canonical IDs compare exactly.
- An active named URL bypasses positive and exclude cheap-match filters and is glanced when the research owner invokes this operation inside the no-pass backfill window. Missing, archived, or otherwise inactive named URLs are ordered acquisition gaps and never trigger ingest. Any source/topic relation already present for the source's current content hash suppresses that pair from both the initial candidate list and revalidation.
- Return candidates in source-sequence order. Each candidate contains source identity/hash/artifact revision, stable topic-scope hash, rule/exclude hits, `named`, the exact three-part untrusted glance packet, complete current-hash pending edges for that source in `source.prepare_route` edge shape, fresh artifact/TOPICS/RELATIONS expected revisions, and a `candidate_sha256` over only the source revision/projection, topic routing scope, named status, and match facts. It also returns registry revisions and ordered gaps.
- Research freezes the initial candidate list and verifier decisions. Before each included write, call the same operation with `source_id`, require the pair and original `candidate_sha256` to remain exact, then use its fresh pending-edge base and expected revisions. Disappearance because an equal current-hash relation now exists is no-write for that pair; any other drift blocks before route preparation. Excluded pairs are never written.

### CONTRACT-BACKFILL

- Standalone `create` remains relation-free. Standalone `refresh` remains unchanged and never invokes candidate discovery, glances, or backfill.
- Approved `research` uses only the existing research-inspection field `topic.last_synthesized` as the window predicate. A null value after create or partial route work opens backfill; a nonnull value written by either `refresh-complete` or `research-complete` closes it. Do not add `current_pass` to the research inspection payload or test `freshness.last_synthesized` as a second authority.
- Execute the research owner in this exact order:
  1. Call `topic.inspect` with purpose `research`; on exact absence, run in-process create and call the same research inspection again.
  2. When that inspection has `topic.last_synthesized:null`, call `source.candidates_for_topic`, glance the frozen candidates, and run every included `source.prepare_route` sequentially. When nonnull, skip candidate enumeration and glances. Active named MANIFEST URLs are must-consider only in the null window; missing named URLs become acquisition gaps and never trigger ingest.
  3. Call `topic.inspect` with purpose `research` again after the optional backfill work and before any refresh decision.
  4. If this new inspection is `dirty|refreshing|blocked`, run the existing in-process refresh procedure. Backfill never follows or runs inside refresh.
  5. Call `topic.inspect` with purpose `research` again, require `current` with zero pending edge IDs, then run the existing four-target research publication.
- Glance each initial candidate once with only TL;DR, Key points, and Classification. Output is exactly excluded `{include:false,reason}` or included `{include:true,relation,impact,confidence,reason}` under existing enums. Same-domain/wrong-purpose is excluded; close evidence is `direct` with `high|medium`; mild attachment is `supporting` with `low|medium`; the verifier may use `contradicting` but it is never answer-authoring eligible.
- For each include in source-sequence order, revalidate the pair, call one fresh `source.lookup`, require its row identity/hash to equal the candidate, construct the complete route decision from the fresh preserved pending-edge base plus the new edge, call existing `source.prepare_route`, and execute/recover/succeed exactly as the current route recipe. Every write is sequential and fail-closed; no target-only route semantic or multi-source event is added.
- If one include commits and a later include reaches an exact terminal failure, stop that invocation before refresh. A new approved research invocation still sees `topic.last_synthesized:null`; candidate discovery suppresses already-related current-hash pairs and returns the remaining unmatched sources for fresh glances. This is a new invocation, not a hidden retry or added resume state.
- Carry acquisition gaps into the research gaps section without acquiring them. Keep the current owner turn/resume ceiling, create's empty relation set, and later ingest's ordinary source-centric routing.

### CONTRACT-RANK

- A source can author `Current answer` or `Decision tree` only when its topic relation is `direct`, impact is `high|medium`, and status is selected pending for refresh or applied for research. Add `relation`, `impact`, `confidence`, and `answer_authoring_eligible` to bounded inspection source summaries.
- Supporting, contradicting, and direct/low sources may appear only in evidence map, caveats, edge cases, and gaps. If no eligible source exists, `coverage_state` is only `insufficient|partial` and candidate `Current answer` and `Decision tree` bytes equal the prior managed sections.
- Refresh execution and research preparation both enforce the rule. Every source-artifact URI cited in those two sections must resolve to an eligible source; each non-placeholder changed section must cite at least one eligible artifact. The source-rank allowlist is reducer-derived, never model-declared.

### CONTRACT-COMPAT

- Preserve the version-2 façade envelope, worker packet version 1, existing operation literals except for the one addition, one public skill, exactly three internal owners, byte-thin raw-argument command, hidden core, current transaction/recovery identities, and all existing route enums.
- Existing one-URL reroute, ingest with a present classification that resolves entirely to existing IDs or is empty, same-hash paths, `promote`, research with no preexisting source candidates, and three-registry validation callers retain their observable outcomes. A ready packet with no classification remains schema-valid; only new or changed-hash `source.prepare` deliberately returns a stable no-target finding for that absence. The source proposal schema, command stub, scaffold manifest ownership classes, `index.create_topic` target/read set, and bound instances remain unchanged.

## Target map

| Target ID | Path / surface | Owner task | Base identity | Callers / fixtures | Criteria |
|---|---|---|---|---|---|
| TGT-ARCH | `.agents/ARCHITECTURE.md` write-set, source, and topic lifecycle sections | T1 | `sha256:09de9b1cf69fc726932b8a3c45434156cf1e212e5dde15f3e3bf31584290a509` | all owners and contracts | AC-ARCH |
| TGT-CORE-CONTRACT | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` | T1 | `sha256:c82b9f03a1153a29cc3d4d70869897d746476d97974410065111369231d915d2` | reducers, façade, recipes | AC-ARCH |
| TGT-CADENCE | `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md` | T1 | `sha256:4c3c27818ac56faa3e7067f31fec198ca625776a600a9da3a75fe58593c18e3e` | owner guardrails | AC-ARCH |
| TGT-SOURCE-GUIDANCE | `source-summary-template.md`; `source-summary-quality-guide.md` | T1 | `sha256:1cb5504c1a5ba5b489c061f8ec79a85c02096e9537e210a764fe1c3705afb51a`; `sha256:1b9f8292f7471c5f6b12f12b0cd3f86044a9d812dbda5d727b580a739e45e04f` | source worker and renderer | AC-ARCH |
| TGT-RESEARCH-TEMPLATE | `.agents/skills/atlas-core/assets/research-library-templates.md` | T1 | `sha256:a66edc16273f9e69a9611b5c9653ef9d8bda2701ca5da166e9c683ecf50f3bfa` | research/refresh drafts | AC-ARCH |
| TGT-VOCAB-SCAFFOLD | `scaffold/summaries/registry/VOCAB.md` table/promotion policy | T1 | `sha256:55790ea32fc4148432101ba6d927b86cb99b0a3e4ecb0408efedc46d34272bde` | provision and instance checks | AC-ARCH |
| TGT-WORKER-SCHEMA | `.agents/skills/atlas-core/assets/source-worker-result.schema.json` optional ready-classification definition | T2 | `sha256:fec5397db2d857735dd704e7f65eef59cac4aa051ead11e8d0292e8bd7d5518e` | `source.worker_schema`, source owner, legacy ready fixtures | AC-VOC-INSERT, AC-VOC-VALIDATION |
| TGT-STATE-VOCAB | `scripts/atlas_state.py` optional VOCAB validation, strict parser/renderer, and source-upsert reduction | T2 | `sha256:c5f0bd66cc4fd81808699497fc20716ab42d34922a7fca36a44122f6422468fc` | pure state/source preparation and later façade opt-in | AC-VOC-INSERT, AC-VOC-REUSE, AC-VOC-NOCHURN, AC-VOC-VALIDATION |
| TGT-SOURCE-CLASSIFY | `scripts/atlas_source.py` ready-worker validation, summary context, proposal resolution, and source preparation | T2 | `sha256:02db21700e50e4c818cf21a27cab6391cb2a85637ffc5b23d4bce9d5682b42b3` | `source.prepare`, `promote` | AC-VOC-INSERT, AC-VOC-REUSE, AC-VOC-NOCHURN, AC-VOC-VALIDATION |
| TGT-SOURCE-OWNER | `.agents/skills/atlas-ask/owners/atlas-source/OWNER.md` version-1 worker and preparation procedure | T2 | `sha256:fdd15dccece4c14179b537063758aadf57cb76acd84f3f12d6db51941491d314` | source ingest/resummarize | AC-VOC-INSERT, AC-VOC-NOCHURN |
| TGT-TEST-VOCAB | `tests/test_atlas_state.py`; `tests/test_atlas_source.py`; `tests/test_atlas_instance.py` VOCAB/classification fixtures | T2 | `sha256:2f6bcea9bc9242015b1fbaf7f98fe6f8fd45c7975789abcb0ed1e472eb74988e`; `sha256:926dc951ff4ac6d191e77b6e5c5c72422b087039c0e67a7d125b56f7a7204b39`; `sha256:9c4fb783df2430cc1809af23864337e19e963f8ba20bf95f4131c2b14937fc1c` | pure reducer/source/scaffold fixtures | AC-VOC-INSERT, AC-VOC-REUSE, AC-VOC-NOCHURN, AC-VOC-VALIDATION |
| TGT-STATE-CANDIDATE | `scripts/atlas_state.py` shared candidate predicate and bounded relation/rank projections | T3 | `sha256:c5f0bd66cc4fd81808699497fc20716ab42d34922a7fca36a44122f6422468fc` | candidate operation, inspection | AC-CANDIDATES, AC-NAMED-GAPS |
| TGT-TOOL-SOURCE | `scripts/atlas_tool.py` named four-document reads, source targets/policy, candidate operation, catalog, and recovery binding | T3 | `sha256:1dcd0c12d8a7f54be2e04a84b530f38d680ad785788be53a03d03f11eefdb055` | CLI families, transactions, owners | AC-CANDIDATES, AC-NAMED-GAPS, AC-PREPARE-REVALIDATION, AC-VOC-RECOVERY |
| TGT-TEST-TOOL-SOURCE | `tests/test_atlas_tool.py` source/VOCAB/candidate/transaction fixtures | T3 | `sha256:5cc0796f98de150c054a7b557c812762aae6097735e0bafd0b0c2a2848f15668` | local connector and fault fixtures | AC-CANDIDATES, AC-NAMED-GAPS, AC-PREPARE-REVALIDATION, AC-VOC-RECOVERY |
| TGT-RECIPES | `.agents/skills/atlas-core/assets/agent-cli-recipes.md` source classification examples and research command traces | T4 | `sha256:699bbae390af000577e65ec4af71eedbbfa38467498776a7db21e3c675b77652` | both write owners | AC-BACKFILL, AC-WRONG-PURPOSE, AC-FRONTDOOR |
| TGT-RESEARCH-OWNER | `.agents/skills/atlas-ask/owners/atlas-research/OWNER.md` inspect/backfill/inspect/refresh/inspect/publish procedure | T4 | `sha256:53d3160f0d5c76225003ebe68c38c2c1070f6810aaf0e3b9c6fbc3cbc9feae81` | approved research mode | AC-BACKFILL, AC-WRONG-PURPOSE |
| TGT-FRONTDOOR | `.agents/skills/atlas-ask/SKILL.md` research/source Effect bounds | T4 | `sha256:45ef778a4c591b3c7fe84ee8fd0db32ed2b02fac1706e475ae717777abc3ba9f` | `/atlas-ask` classification | AC-FRONTDOOR |
| TGT-EVAL | `.agents/skills/atlas-core/assets/evals/agent-tooling.json` owner/effect/backfill cases | T4 | `sha256:d235020271cda00a9d11016f48344f09266980cc313d39ae4f1e182998daf988` | harness eval loader | AC-BACKFILL, AC-WRONG-PURPOSE, AC-FRONTDOOR |
| TGT-HARNESS-TEST | `tests/test_atlas_harness_surface.py` schema/eval/catalog/owner assertions | T4 | `sha256:2165147e4197027c2f5d13e8548ebc723cf12e325fd69a923f3b0280997a80f5` | packaged harness surface | AC-FRONTDOOR |
| TGT-TEST-BACKFILL | `tests/test_atlas_tool.py` create-to-publish, no-pass retry, and missing-URL scenarios | T4 | `sha256:5cc0796f98de150c054a7b557c812762aae6097735e0bafd0b0c2a2848f15668` | temporary topic/source transactions | AC-BACKFILL, AC-WRONG-PURPOSE |
| TGT-STATE-RANK | `scripts/atlas_state.py` answer-authoring eligibility and inspection source summaries | T5 | `sha256:c5f0bd66cc4fd81808699497fc20716ab42d34922a7fca36a44122f6422468fc` | refresh/research preparation | AC-RANK, AC-REGRESSION |
| TGT-TOOL-RANK | `scripts/atlas_tool.py` refresh answer-section guard | T5 | `sha256:1dcd0c12d8a7f54be2e04a84b530f38d680ad785788be53a03d03f11eefdb055` | `refresh.execute`, `refresh.recover` | AC-RANK |
| TGT-RESEARCH-RANK | `scripts/atlas_research.py` research answer-section guard | T5 | `sha256:73ab85ec4491ab76cbf0f19a2102dd619670e0620e0fdc5aa1b5f63d172be5c6` | `research.prepare`, `research.execute`, `research.recover` | AC-RANK, AC-REGRESSION |
| TGT-TEST-RANK | `tests/test_atlas_tool.py`; `tests/test_atlas_research.py` rank and compatibility fixtures | T5 | `sha256:5cc0796f98de150c054a7b557c812762aae6097735e0bafd0b0c2a2848f15668`; `sha256:75eccfb051f35985ee7c10bc349c987ff91602b693d4fc72ecc81d751a399be9` | refresh/research transaction fixtures | AC-RANK, AC-REGRESSION |

## Execution policy

- Assurance: high-consequence
- Topology: one-owner-sequential
- Max concurrency: 1
- Isolation: none
- Lineages: shared
- Fan-in task: none
- Fan-in inputs: none
- Contention policy: One owner edits coupled contracts, runtime, and tests in order; unexpected same-target drift stops for an exact rebind rather than overwrite.
- Decomposition: Exactly T1 through T5; no worker subdivision, subplanner, helper owner, or parallel branch without a newly approved route.
- Effect limit: EFF-CONTRACT, EFF-RUNTIME, EFF-TEST
- Orchestrator profile: one-owner-sequential

Separate decorrelated verification and final review follow implementation, then the required continual-learning assessment. Work stays in the current checkout and preserves unrelated user changes. If the declared profile is unavailable, stop `transport-unavailable` rather than change model, provider, or topology. The backend schedules the high-consequence `dev-verification` → `dev-code-review` → `dev-continual-learning` tail once after T5; this plan does not duplicate it as numbered tasks.

## Tasks

- [x] T1. Align architecture and shared contracts
  completed 2026-08-19-2243
  - Owner: dev-implementation worker
  - Intent: Align the canonical product contracts with the approved two-join behavior.
  - Methods: none
  - Wave: W0
  - Depends on: none
  - Targets: TGT-ARCH, TGT-CORE-CONTRACT, TGT-CADENCE, TGT-SOURCE-GUIDANCE, TGT-RESEARCH-TEMPLATE, TGT-VOCAB-SCAFFOLD
  - Contracts: CONTRACT-VOCAB, CONTRACT-WORKER, CONTRACT-SOURCE-TX, CONTRACT-CANDIDATE, CONTRACT-BACKFILL, CONTRACT-RANK, CONTRACT-COMPAT
  - Criteria: AC-ARCH
  - Effects: EFF-CONTRACT
  - Output: OUTP-T1
  - Receiver: dev-implementation worker
  - Verification: VR-1
  - Lineage: shared

- [x] T2. Implement vocabulary promotion and source binding
  completed 2026-08-20-1710
  - Owner: dev-implementation worker
  - Intent: Make source classification safely promote and bind canonical vocabulary.
  - Methods: none
  - Wave: W1
  - Depends on: T1
  - Targets: TGT-WORKER-SCHEMA, TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-SOURCE-OWNER, TGT-TEST-VOCAB
  - Contracts: CONTRACT-VOCAB, CONTRACT-WORKER, CONTRACT-SOURCE-TX
  - Criteria: AC-VOC-INSERT, AC-VOC-REUSE, AC-VOC-NOCHURN, AC-VOC-VALIDATION
  - Effects: EFF-RUNTIME, EFF-TEST
  - Output: OUTP-T2
  - Receiver: dev-implementation worker
  - Verification: VR-2, VR-3, VR-4, VR-5
  - Lineage: shared

- [x] T3. Implement topic-scoped candidate discovery
  completed 2026-08-20-1710
  - Owner: dev-implementation worker
  - Intent: Make topic-scoped source discovery deterministic and transaction-safe.
  - Methods: none
  - Wave: W2
  - Depends on: T2
  - Targets: TGT-STATE-CANDIDATE, TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE
  - Contracts: CONTRACT-VOCAB, CONTRACT-SOURCE-TX, CONTRACT-CANDIDATE
  - Criteria: AC-CANDIDATES, AC-NAMED-GAPS, AC-PREPARE-REVALIDATION, AC-VOC-RECOVERY
  - Effects: EFF-RUNTIME, EFF-TEST
  - Output: OUTP-T3
  - Receiver: dev-implementation worker
  - Verification: VR-6, VR-7, VR-8, VR-14
  - Lineage: shared

- [x] T4. Wire research through the no-pass backfill window
  completed 2026-08-20-1710
  - Owner: dev-implementation worker
  - Intent: Backfill an approved research topic with `topic.last_synthesized:null` before any refresh and publication.
  - Methods: none
  - Wave: W3
  - Depends on: T3
  - Targets: TGT-RECIPES, TGT-RESEARCH-OWNER, TGT-FRONTDOOR, TGT-EVAL, TGT-HARNESS-TEST, TGT-TEST-BACKFILL
  - Contracts: CONTRACT-BACKFILL, CONTRACT-CANDIDATE, CONTRACT-SOURCE-TX
  - Criteria: AC-BACKFILL, AC-WRONG-PURPOSE, AC-FRONTDOOR
  - Effects: EFF-CONTRACT, EFF-TEST
  - Output: OUTP-T4
  - Receiver: dev-implementation worker
  - Verification: VR-9, VR-10, VR-11
  - Lineage: shared

- [x] T5. Enforce answer-authoring evidence rank
  completed 2026-08-20-1710
  - Owner: dev-implementation worker
  - Intent: Prevent weak attachments from authoring answer-bearing topic sections.
  - Methods: none
  - Wave: W4
  - Depends on: T4
  - Targets: TGT-STATE-RANK, TGT-TOOL-RANK, TGT-RESEARCH-RANK, TGT-TEST-RANK
  - Contracts: CONTRACT-RANK, CONTRACT-COMPAT
  - Criteria: AC-RANK, AC-REGRESSION
  - Effects: EFF-RUNTIME, EFF-TEST
  - Output: OUTP-T5
  - Receiver: dev-verification
  - Verification: VR-12, VR-13
  - Lineage: shared

## Acceptance

| Criterion ID | Condition / input | Expected observable / threshold | Surface | Owning task |
|---|---|---|---|---|
| AC-ARCH | Inspect every changed canonical contract and scaffold policy after T1. | Source ingest/changed-hash resummarize explicitly owns insert-only VOCAB; the exact `Allowed aliases` header, `reserved` status, legal source-kind alias overlap, optional validation seam, schema-optional/prepare-required classification, pre-refresh `topic.last_synthesized` backfill, ranking, write prohibitions, and recovery ownership agree with no second convention. | TGT-ARCH, TGT-CORE-CONTRACT, TGT-CADENCE, TGT-SOURCE-GUIDANCE, TGT-RESEARCH-TEMPLATE, TGT-VOCAB-SCAFFOLD | T1 |
| AC-VOC-INSERT | Prepare a cooking-like new source against the current source-kind scaffold VOCAB, including the overlapping `guide` alias on `article` and `docs`. | The starting table validates; exactly one domain, at most one subdomain, and at most three tags are appended; new tags have empty parents; the prepared artifact binds only resulting canonical IDs; candidate terms stay non-routing; no topic path, row, index, or pass is created. | TGT-WORKER-SCHEMA, TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-SOURCE-OWNER, TGT-TEST-VOCAB | T2 |
| AC-VOC-REUSE | Prepare a second source whose proposed alias unambiguously identifies an ingest-created cooking domain or tag. | The existing compatible canonical ID is bound, no duplicate row is inserted, and VOCAB bytes are unchanged. | TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-TEST-VOCAB | T2 |
| AC-VOC-NOCHURN | Exercise routine same hash, resummarize same hash, changed-hash resummarize, and `promote`. | Both same-hash paths and `promote` preserve VOCAB bytes; changed hash may append only newly unseen compatible rows and cannot edit/delete existing rows. | TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-SOURCE-OWNER, TGT-TEST-VOCAB | T2 |
| AC-VOC-VALIDATION | Validate a legacy version-1 ready packet without classification, then prepare it for new/changed-hash work; also feed invalid present classification IDs/types/caps, a malformed VOCAB header/status/parent, and valid proposals that hit ambiguous source-kind aliases, incompatible types, or a mismatched subdomain parent. | The missing-classification packet is schema-valid but new/changed-hash preparation returns a stable finding with no targets; same-hash and `promote` ignore it. Invalid present worker/table structure also yields no targets; the overlapping source-kind table remains valid; each proposal identity conflict inserts no VOCAB row, moves its label to candidate terms, and still prepares the source using only resolved IDs. | TGT-WORKER-SCHEMA, TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-TEST-VOCAB | T2 |
| AC-CANDIDATES | Evaluate a matrix covering all four forward rules in both source/topic orientations. | Topic-scoped results equal the documented forward predicate, exclusion wins for unnamed sources, candidate terms never match, candidates are source-sequence ordered, and unmatched bodies are absent from output. | TGT-STATE-CANDIDATE, TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE | T3 |
| AC-NAMED-GAPS | Inside a no-pass window, request one unmatched active named URL, one missing URL, and one already-related current-hash URL. | The unmatched active source is returned for glance, missing/inactive input is an ordered acquisition gap with no ingest, and the already-related pair is not glanced again. | TGT-STATE-CANDIDATE, TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE | T3 |
| AC-PREPARE-REVALIDATION | Route two included sources sequentially while preserving another topic's current-hash pending edge, then inject candidate/source/topic drift. | Each decision carries the complete pending base plus one new edge; valid sequential writes preserve prior pending work; changed candidate identity blocks before preparation and existing transaction recovery remains exact. | TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE | T3 |
| AC-VOC-RECOVERY | Inject a transaction fault after the VOCAB-first target is acknowledged during a changed-hash or new-source write. | Existing `transaction.recover` uses the original transaction identity and bytes to restore or complete the VOCAB-first target; no partial state is accepted and post-validation includes VOCAB. | TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE | T3 |
| AC-BACKFILL | First research-create and publish a cooking topic whose research inspection has `topic.last_synthesized:null`. Separately, create another null-synthesized topic, commit one included route, force the second include to an exact terminal failure before refresh, then begin a new approved research invocation. | Create is relation-free; candidate discovery/routes run before the next inspection and any refresh; the successful path reaches pending, refresh-applied, then four-target publication. After partial failure the topic remains `topic.last_synthesized:null`; retry omits the already-related current-hash pair, glances/routes the remaining source, then inspects, refreshes, re-inspects current/zero-pending, and publishes. | TGT-RECIPES, TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST-BACKFILL | T4 |
| AC-WRONG-PURPOSE | Add one same-domain but wrong-purpose source beside the included cooking source during the no-pass window. | Both candidates are glanced; the wrong-purpose result is `include:false`, creates no edge, and contributes nothing to answer-bearing sections. | TGT-RECIPES, TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST-BACKFILL | T4 |
| AC-FRONTDOOR | Classify source ingest/resummarize and research-create/research intents through the packaged surface. | Goal/Effect bounds name possible insert-only VOCAB and eligible no-pass backfill/refresh/publish effects without changing approval count; capabilities expose exactly one added lifecycle operation; command remains raw and byte-thin; exactly three owners remain. | TGT-FRONTDOOR, TGT-RECIPES, TGT-EVAL, TGT-HARNESS-TEST | T4 |
| AC-RANK | Attach only supporting/low or supporting/medium evidence and attempt to change Current answer/Decision tree or mark coverage sufficient. | Refresh and research preparation reject answer-authoring or sufficient coverage; evidence-map/caveat-only use remains valid; only direct/high-or-medium applied/selected evidence can author or be cited in those sections. | TGT-STATE-RANK, TGT-TOOL-RANK, TGT-RESEARCH-RANK, TGT-TEST-RANK | T5 |
| AC-REGRESSION | Run existing one-URL reroute, ingest with no unseen subjects, same-hash paths, `promote`, research with no preexisting sources, three-registry topic create, transaction recovery, instance checks, and full Atlas tests. | Existing observable envelopes, outcomes, target sets/order where unchanged, optional `validate_documents` callers, and cleanup guarantees pass; no bound-instance bytes change. | TGT-STATE-RANK, TGT-RESEARCH-RANK, TGT-TEST-RANK | T5 |

## Verification / Done criteria

- [x] VR-1. Independently compare the exact changed contract sections and run `python3 -m unittest tests.test_atlas_harness_surface tests.test_atlas_instance`.
  - Criterion: AC-ARCH
  - Proof class: independent verification
  - Scenario / environment / fixture: Repository checkout only; inspect architecture-first ordering, exact write sets, exact VOCAB header/status/parent/alias-overlap rules, scaffold seed-once status, and forbidden-effect absences.
  - Evidence form: Passing command plus exact target digests and a criterion-by-criterion contract consistency record.
  - Target recheck: TGT-ARCH, TGT-CORE-CONTRACT, TGT-CADENCE, TGT-SOURCE-GUIDANCE, TGT-RESEARCH-TEMPLATE, TGT-VOCAB-SCAFFOLD
  - Receiver: dev-verification

- [x] VR-2. Run `python3 -m unittest tests.test_atlas_source.AtlasSourceTests.test_source_upsert_inserts_capped_vocab_and_binds_artifact_without_topic_files`.
  - Criterion: AC-VOC-INSERT
  - Proof class: independent verification
  - Scenario / environment / fixture: New cooking-like source and the unchanged source-kind scaffold VOCAB whose `article` and `docs` rows both allow alias `guide`.
  - Evidence form: Passing assertion over accepted starting bytes, exact appended VOCAB rows, artifact frontmatter, and absent topic paths.
  - Target recheck: TGT-WORKER-SCHEMA, TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-SOURCE-OWNER, TGT-TEST-VOCAB
  - Receiver: dev-verification

- [x] VR-3. Run `python3 -m unittest tests.test_atlas_source.AtlasSourceTests.test_source_upsert_reuses_alias_without_rewriting_vocab`.
  - Criterion: AC-VOC-REUSE
  - Proof class: independent verification
  - Scenario / environment / fixture: Second source proposes the existing cooking identity through an alias.
  - Evidence form: Passing canonical-ID binding assertion and byte-equal before/after VOCAB digest.
  - Target recheck: TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-TEST-VOCAB
  - Receiver: dev-verification

- [x] VR-4. Run `python3 -m unittest tests.test_atlas_source.AtlasSourceTests.test_same_hash_resummarize_preserves_vocab_bytes tests.test_atlas_source.AtlasSourceTests.test_changed_hash_inserts_only_unseen_vocab_rows tests.test_atlas_source.AtlasSourceTests.test_promote_preserves_vocab_bytes`.
  - Criterion: AC-VOC-NOCHURN
  - Proof class: independent verification
  - Scenario / environment / fixture: Same URL under routine same-hash, explicit same-hash resummarize, changed-hash resummarize, then `promote`.
  - Evidence form: Passing byte-digest and row-delta assertions for all four transitions.
  - Target recheck: TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-SOURCE-OWNER, TGT-TEST-VOCAB
  - Receiver: dev-verification

- [x] VR-5. Run `python3 -m unittest tests.test_atlas_state.AtlasStateTests.test_validate_vocab_accepts_seed_alias_overlap_and_rejects_malformed_rows tests.test_atlas_source.AtlasSourceTests.test_ready_schema_allows_missing_classification_but_prepare_requires_it_for_new_or_changed tests.test_atlas_source.AtlasSourceTests.test_worker_classification_caps_and_types tests.test_atlas_source.AtlasSourceTests.test_source_prepare_degrades_vocab_identity_conflicts_to_candidate_terms`.
  - Criterion: AC-VOC-VALIDATION
  - Proof class: independent verification
  - Scenario / environment / fixture: Legacy version-1 ready packet without classification across schema validation and each prepare state; current seed table; malformed present classification/table matrix; valid ambiguous source-kind/type/parent matches.
  - Evidence form: Schema acceptance for the missing property; stable no-target prepare finding only for new/changed-hash absence; unchanged same-hash/`promote`; zero targets for malformed structure; byte-valid source preparation and exact candidate-term fallback for identity conflicts.
  - Target recheck: TGT-WORKER-SCHEMA, TGT-STATE-VOCAB, TGT-SOURCE-CLASSIFY, TGT-TEST-VOCAB
  - Receiver: dev-verification

- [x] VR-6. Run `python3 -m unittest tests.test_atlas_tool.AtlasToolTests.test_candidates_for_topic_inverts_four_forward_rules tests.test_atlas_tool.AtlasToolTests.test_candidates_for_topic_ignores_candidate_terms_and_omits_unmatched_bodies`.
  - Criterion: AC-CANDIDATES
  - Proof class: independent verification
  - Scenario / environment / fixture: Deterministic topic/source matrix for domain, subdomain, tags, phrase matching, exclude precedence, and candidate-term-only near misses.
  - Evidence form: Equality against the shared predicate in both orientations and exact bounded output keys.
  - Target recheck: TGT-STATE-CANDIDATE, TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE
  - Receiver: dev-verification

- [x] VR-7. Run `python3 -m unittest tests.test_atlas_tool.AtlasToolTests.test_candidates_for_topic_named_active_and_missing_gap`.
  - Criterion: AC-NAMED-GAPS
  - Proof class: independent verification
  - Scenario / environment / fixture: Active unmatched, missing, archived, and already-related named URLs in one request-order fixture.
  - Evidence form: Exact candidate/gap arrays, zero capture/source-prepare calls, and unchanged source registries.
  - Target recheck: TGT-STATE-CANDIDATE, TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE
  - Receiver: dev-verification

- [x] VR-8. Run `python3 -m unittest tests.test_atlas_tool.AtlasToolTests.test_candidates_for_topic_revalidation_preserves_pending_edges tests.test_atlas_tool.AtlasToolTests.test_candidates_for_topic_revalidation_rejects_drift`.
  - Criterion: AC-PREPARE-REVALIDATION
  - Proof class: independent verification
  - Scenario / environment / fixture: Two sequential includes, one unrelated pending edge, then controlled artifact/topic-scope drift.
  - Evidence form: Exact relation-row set after valid writes and a no-write stale-candidate finding before invalid preparation.
  - Target recheck: TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE
  - Receiver: dev-verification

- [x] VR-14. Run `python3 -m unittest tests.test_atlas_tool.AtlasToolTests.test_source_transaction_recovers_vocab_first_faults`.
  - Criterion: AC-VOC-RECOVERY
  - Proof class: independent verification
  - Scenario / environment / fixture: Changed-hash or new-source transaction fault injected after VOCAB acknowledgement under a temporary local connector.
  - Evidence form: Exact original recovery identity/request, terminal complete-or-rolled-back receipt, restored or completed VOCAB-first bytes, and successful four-document post-validation.
  - Target recheck: TGT-TOOL-SOURCE, TGT-TEST-TOOL-SOURCE
  - Receiver: dev-verification

- [x] VR-9. Run `python3 -m unittest tests.test_atlas_tool.AtlasToolTests.test_research_create_backfills_refreshes_and_publishes tests.test_atlas_tool.AtlasToolTests.test_research_backfill_retry_when_topic_last_synthesized_is_null`.
  - Criterion: AC-BACKFILL
  - Proof class: independent verification
  - Scenario / environment / fixture: Successful absent-topic flow plus a second flow whose research payload has `topic.last_synthesized:null`, one committed include, one exact terminal include failure before refresh, and a fresh approved research invocation.
  - Evidence form: Exact `inspect → candidate/glance/route → inspect → refresh-if-needed → inspect-current/zero-pending → publish` trace; null synthesis through partial failure; no second glance for the already-related pair; fresh glance/route for the remaining source; final nonnull synthesis and eligible citation.
  - Target recheck: TGT-RECIPES, TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST-BACKFILL
  - Receiver: dev-verification

- [x] VR-10. Run `python3 -m unittest tests.test_atlas_tool.AtlasToolTests.test_research_backfill_excludes_same_domain_wrong_purpose`.
  - Criterion: AC-WRONG-PURPOSE
  - Proof class: independent verification
  - Scenario / environment / fixture: One close and one wrong-purpose source sharing the topic domain inside a no-pass backfill window.
  - Evidence form: Two bounded glance packets, one pending/applied edge, and no excluded artifact URI in answer-bearing sections.
  - Target recheck: TGT-RECIPES, TGT-RESEARCH-OWNER, TGT-EVAL, TGT-TEST-BACKFILL
  - Receiver: dev-verification

- [x] VR-11. Run `python3 -m unittest tests.test_atlas_harness_surface` and smoke `python3 scripts/atlas_tool.py capabilities`.
  - Criterion: AC-FRONTDOOR
  - Proof class: independent verification
  - Scenario / environment / fixture: Packaged skill/owner/eval/schema/catalog surface without a bound profile.
  - Evidence form: Passing surface suite and canonical JSON catalog showing one added lifecycle literal with unchanged envelope.
  - Target recheck: TGT-FRONTDOOR, TGT-RECIPES, TGT-EVAL, TGT-HARNESS-TEST
  - Receiver: dev-verification

- [x] VR-12. Run `python3 -m unittest tests.test_atlas_tool.AtlasToolTests.test_refresh_rejects_supporting_low_answer_authoring tests.test_atlas_research.AtlasResearchTests.test_research_rejects_ineligible_answer_citations tests.test_atlas_research.AtlasResearchTests.test_research_allows_supporting_low_in_evidence_map_only`.
  - Criterion: AC-RANK
  - Proof class: independent verification
  - Scenario / environment / fixture: Supporting low/medium and direct high/medium relation combinations across refresh and research preparation.
  - Evidence form: Stable rejection findings for answer-bearing misuse and passing evidence-map-only/direct-eligible candidates.
  - Target recheck: TGT-STATE-RANK, TGT-TOOL-RANK, TGT-RESEARCH-RANK, TGT-TEST-RANK
  - Receiver: dev-verification

- [x] VR-13. Run `python3 -m unittest discover -s tests -p 'test_atlas_*.py'` and compare the repository-owned scaffold tree before/after the suite.
  - Criterion: AC-REGRESSION
  - Proof class: independent verification
  - Scenario / environment / fixture: Full local Atlas suite, including existing reroute, unchanged ingest, same-hash and `promote`, no-candidate research, three-registry topic create, optional VOCAB validation, recovery, and instance cleanup fixtures.
  - Evidence form: Full passing test output, unchanged scaffold digest outside intended contract edits, no temporary fixture residue, and no bound-instance operation in logs.
  - Target recheck: TGT-STATE-RANK, TGT-RESEARCH-RANK, TGT-TEST-RANK
  - Receiver: dev-verification

## Result / Handoff

| Output ID | Producing task | Artifact / identity | Allowed outcomes | Receiver | Handoff contract |
|---|---|---|---|---|---|
| OUTP-T1 | T1 | Exact revisions of TGT-ARCH through TGT-VOCAB-SCAFFOLD | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation worker | Common Handoff binds all three user authorities, AC-ARCH, VR-1, changed contract digests, and any authority conflict. |
| OUTP-T2 | T2 | Exact revisions of pure vocabulary/source implementation and fixtures | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation worker | Common Handoff binds AC-VOC-INSERT through AC-VOC-VALIDATION, version-1 optional classification schema, state-dependent prepare requirement, optional validation signatures, resolved artifact bindings, and proposal-conflict fallback evidence. |
| OUTP-T3 | T3 | Exact four-document source/candidate/catalog/transaction revisions | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation worker | Common Handoff binds AC-CANDIDATES, AC-NAMED-GAPS, AC-PREPARE-REVALIDATION, and AC-VOC-RECOVERY; include operation schema, drift evidence, target order, preserved pending-edge map, and exact recovery state. |
| OUTP-T4 | T4 | Exact research owner/recipe/front-door/eval/backfill revisions | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-implementation worker | Common Handoff binds AC-BACKFILL through AC-FRONTDOOR, successful and partial-retry `topic.last_synthesized:null` traces, exact pre-refresh ordering, gaps, and no extra authority/effect. |
| OUTP-T5 | T5 | Exact final shared-lineage repository target | completed, blocked, failed, timed-out, cancelled, transport-unavailable, authority-change-required | dev-verification | Common Handoff binds AC-RANK and AC-REGRESSION, every worker smoke result, full target digest, accepted residuals, and high-consequence verification preconditions. |

## Blockers and recovery

| Blocker ID | Owner | Recovery evidence | Affected tasks | Revision / approval boundary | Ready condition |
|---|---|---|---|---|---|
| BLK-APPROVAL | dev-ask / human authority | Fresh native preflight names this exact plan identity, complete-byte SHA-256, `PENDING` status, and explicit execution approval. | T1-T5 | Any plan byte change invalidates approval. | Exact published bytes are structurally valid and explicitly approved for execution. |
| BLK-CONTRACT-DRIFT | T1 | Exact changed upstream digest plus semantic diff against AUTH-USER-HANDOFF, AUTH-REVISION-HANDOFF, AUTH-REVISION-HANDOFF-R2, and AUTH-ARCH-BASE. | T1-T5 | Material scope/write-set/interface change returns to human authority; unrelated drift may be rebound only when proven nonsemantic. | All user authorities and base identities are current, or a revised exact plan is approved. |
| BLK-VOCAB-MALFORMED | T2 | Stable parser/schema/preparation finding naming the malformed header, row, parent, status, ID, worker field, or state-required missing classification plus proof of zero transaction targets. | T2-T5 | Proposal identity conflicts are nonblocking candidate-term fallbacks; malformed canonical bytes require separate maintain/vocab repair authority. | The table validates and a present worker classification validates; new/changed-hash preparation has an explicit classification object; no cross-row alias deduplication or ingest repair is attempted. |
| BLK-CANDIDATE-DRIFT | T4 | Initial and revalidation `candidate_sha256`, source hash, topic-scope hash, and no-write façade finding. | T4-T5 | No hidden retry or stale semantic reuse; a fresh approved research invocation owns changed evidence. | The pair is unchanged or already related; otherwise current work stops with exact drift evidence. |
| BLK-PARTIAL-TRANSACTION | T3 | Exact façade disposition, transaction identity, acknowledged targets, current revisions, and returned recovery operation. | T3-T5 | Only the existing byte-identical `transaction.recover`/eligible successor path is authorized. A later research invocation may resume candidate enumeration only when no pass exists. | Recovery reaches an exact terminal receipt and four-document post-validation passes; ambiguity returns to human authority. |
| BLK-FORBIDDEN-EFFECT | T1 | Evidence that implementation would require a bound-instance sync, living migration, credential, deploy, destructive repair, second owner, or new storage/search subsystem. | T1-T5 | Outside the listed user authorities and every EFF limit. | A separately approved authority/route revises the plan; no partial implementation proceeds. |

- exhausted token at 2026-08-20-0224
  - trying: Complete the high-consequence final review after the repaired aggregate independently verified all 14 frozen acceptance criteria.
  - found: BLK-RVW-CANDIDATE-REVALIDATION-EQUALITY, BLK-RVW-CAPABILITY-EVAL-COUNTS, BLK-RVW-SOURCE-UPSERT-CLASSIFICATION, and BLK-RVW-SOURCE-SUCCESSOR-POSTVALIDATION; four changed-contract consumers still contradict candidate revalidation, catalog discovery, exact event shape, or VOCAB-aware successor completion.
  - tried: The consumed consolidated repair corrected three earlier verification blockers and the second verifier passed every frozen criterion; it did not change or directly exercise these four reviewer-traced consumer branches.
  - target: sha256:1f6b049ad1f6a415f949378ab46ba70e028bc377d625b06e8c193815b8f34a99
  - remaining: AC-PREPARE-REVALIDATION, AC-BACKFILL, AC-FRONTDOOR, AC-VOC-RECOVERY, AC-REGRESSION, CONTRACT-SOURCE-TX consumers / dev-implementation
  - grant: continue 2026-08-20-1045
  - opinion: absent

- exhausted review-rerun at 2026-08-20-1133
  - trying: Settle the high-consequence outcome after the original rerun inspected the continuation-verified repair.
  - found: BLK-RVW-SOURCE-TRANSACTION-REDUCTION, BLK-RVW-READY-NULL-CLASSIFICATION, BLK-RVW-NO-ELIGIBLE-FALLBACK, and BLK-RVW-CANDIDATE-SNAPSHOT-TERMINAL; ordinary source transaction ingress bypasses reducer projection, present-null ready classification bypasses its schema, no-eligible answer fallback permits erasure/stale coverage, and candidate terminal states bypass the consistent snapshot.
  - tried: The continuation repair closed candidate equality, catalog count, and successor dispatch findings and partially closed strict classification; aggregate verification passed all frozen criteria, but its fixtures did not exercise these four direct static counterexamples and the original rerun found them before approval.
  - target: sha256:c3656d0c04ebf38e6db8cad1aafe80c6b81bdbc74583c39ff592d1ec8cb72b2d
  - remaining: AC-VOC-NOCHURN, AC-VOC-VALIDATION, AC-VOC-RECOVERY, AC-CANDIDATES, AC-NAMED-GAPS, AC-RANK, AC-REGRESSION / dev-implementation
  - grant: continue 2026-08-20-1200
  - opinion: absent

- continuation repair completed at 2026-08-20-1233
  - trying: Close the four original-rerun blockers without changing the frozen acceptance scope.
  - found: Ordinary and aggregate source transaction ingress now rederive source events and exact registry/artifact projections before durable records, source and route attempts invoke source-aware post-validation before `applied`, present-null ready classification is rejected at the packet boundary, no-eligible answer edits preserve current managed answer sections, and candidate absence/finding terminals now derive only from the locked snapshot.
  - tried: Five direct blocker counterexamples passed; the complete source/tool/research consumer suites passed 162 tests; `python3 -m unittest discover -s tests -p 'test_atlas_*.py'` passed 358 tests.
  - target: sha256:3817395d752cd496a89a837dccb97034f8f2f87fa53905269329b61dd58e01cf
  - remaining: Run continuation independent verification, then the grant-scoped final Standards and Specification review.
  - grant: continue 2026-08-20-1200
  - opinion: absent

- exhausted token at 2026-08-20-1302
  - trying: Settle the high-consequence outcome after the continuation repair received fresh proof over all fourteen frozen acceptance criteria.
  - found: BLK-V4-CANONICAL-CATALOG-COUNT and BLK-V4-AGGREGATE-RECOVERY-CONSUMER; the canonical operation list/count omits the candidate operation, and aggregate recovery can apply a source without source-aware post-validation or reject an acknowledged immutable effect event.
  - tried: The continuation repair closed the four original-rerun blockers and eleven criteria verified; fresh catalog and aggregate recovery counterexamples found two new outcome-blocking consumers across the remaining three criteria.
  - target: sha256:3817395d752cd496a89a837dccb97034f8f2f87fa53905269329b61dd58e01cf
  - remaining: AC-ARCH, AC-VOC-RECOVERY, AC-REGRESSION / dev-implementation
  - grant: continue 2026-08-20-1324
  - opinion: absent

- exhausted token at 2026-08-20-1418
  - trying: Settle the high-consequence outcome after repairing the two attempt-4 blockers under `continue 2026-08-20-1324`.
  - found: `BLK-V4-AGGREGATE-RECOVERY-CONSUMER` is verified closed, but `BLK-V4-CANONICAL-CATALOG-COUNT` remains because the repaired canonical lifecycle block added `source.candidates_for_topic` by replacing the line that also contained `source.normalize_capture`; the block therefore still lists 29 operations while every runtime/package consumer and adjacent prose declare 30.
  - tried: Independent attempt 5 rechecked the immutable target, rules, all fourteen frozen criteria, 46 focused tests, live capabilities, the sealed 360-test regression evidence, recovery failure paths, and exact catalog sets; twelve criteria verified and only `AC-ARCH` plus `AC-FRONTDOOR` failed.
  - target: sha256:4d284c2aa97fb5c4d9d99c47dfed90af72944af6787db60a84f3b52326909f8f
  - remaining: AC-ARCH, AC-FRONTDOOR / dev-implementation
  - grant: continue 2026-08-20-1426
  - opinion: absent

- exhausted token at 2026-08-20-1511
  - trying: Settle the high-consequence outcome after attempt-6 independent verification authorized the current grant-scoped final Standards and Specification review.
  - found: `BLK-RVW-NO-ELIGIBLE-FALLBACK` and `BLK-RVW-SOURCE-UPSERT-CLASSIFICATION`; the no-eligible rank guard still admits `coverage_state: stale`, and same-hash source reduction still admits a malformed non-null classification value.
  - tried: Continuation repair completed at 2026-08-20-1547: enforced the explicit no-eligible `insufficient|partial` coverage allowlist and unconditional non-null source-event classification shape validation. Three focused counterexamples failed before the repair and passed after it; ten impacted tests and the full 362-test Atlas suite passed, with scaffold digest unchanged.
  - target: sha256:e4aa5edebd87b548123953cd1e6caa54182d723471066969056b6460edfc8954
  - remaining: Independent verification of the unchanged fourteen criteria, then one grant-scoped final review only after VERIFIED / dev-implementation
  - grant: continue 2026-08-20-1520
  - opinion: absent

## Critical anchors and assumptions

| Anchor ID | Kind | Exact reference | Execution role |
|---|---|---|---|
| ANC-ARCH-WRITES | Canonical contract | `.agents/ARCHITECTURE.md` `Owner write sets`, `Source lifecycle`, `Topic lifecycle`, `Deterministic runtime seams` | Must change first and bound every dependent edit. |
| ANC-REGISTRY | Core contract | `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` `Reference reducer interface`, `Source artifact frontmatter`, `Route-source candidate generation`, `Source and route transaction records` | Own exact registry/event/matcher/recovery semantics. |
| ANC-SOURCE-PREPARE | Runtime | `scripts/atlas_source.py::validate_worker_result`, `prepare_source`, `_summary_context` | Preserve malformed present-packet rejection, enforce missing classification only after selecting a new/changed-hash prepare state, preserve the same-hash short circuit, and keep `promote` no-VOCAB. |
| ANC-STATE | Runtime | `scripts/atlas_state.py::validate_documents`, new `validate_vocab`, `reduce_event`, `inspect_topic` | Own optional canonical parsing, proposal resolution, reductions, and the existing research payload's `topic.last_synthesized` backfill-window signal; do not add `current_pass` there. |
| ANC-FACADE | Runtime | `scripts/atlas_tool.py::_documents`, `_validate`, `_source_prepare`, `_source_prepare_route`, new `_source_candidates_for_topic`, `_operations`, `_source_transaction_policy` | Restrict four-document reads to the four named lifecycle paths; own catalog, target order, post-validation, and recovery binding. |
| ANC-RESEARCH | Runtime | `scripts/atlas_research.py::prepare_research` and transaction policy/post-validation helpers | Keep publication at exactly four ordered targets and enforce applied evidence rank. |
| ANC-OWNERS | Workflow | `atlas-source/OWNER.md` `Capture and semantic wave`, `Prepared source transaction`, `In-process route procedure`; `atlas-research/OWNER.md` create/research/refresh procedures | Keep one qualified same-agent owner, run eligible backfill before refresh, and retain unchanged approval/resume ceilings and standalone refresh behavior. |
| ANC-COMMAND | Public surface | `.agents/commands/atlas-ask.md` | Must remain byte-thin and unchanged. |
| ANC-UNCHANGED-SCHEMA | Compatibility | `.agents/skills/atlas-core/assets/source-summary-proposal.schema.json`; `scaffold/MANIFEST.json` | No classification sidecar schema and no scaffold ownership-class change. |
| ANC-NO-INSTANCE | Ownership | `rule://atlas-boundaries`; repository `.agents/AGENTS.md` | Product edits only; no `vault://atlas/` or instance synchronization. |
| ANC-RESIDUAL-FIRST-WRITER | Accepted residual | `AUTH-REVISION-HANDOFF` first-writer rule | Names such as `food` versus `cooking` remain sticky; only unambiguous alias reuse mitigates them. |
| ANC-RESIDUAL-MATCHING | Accepted residual | `AUTH-REVISION-HANDOFF` candidate/backfill limits | Include-term quality still bounds cheap matching, and glance count remains unbounded while no pass exists; do not expand scope. |

- Assumptions: none

## Completion Summary

- Completed `OUT-ATLAS-VOCAB-BACKFILL` at exact product target `sha256:e4aa5edebd87b548123953cd1e6caa54182d723471066969056b6460edfc8954`.
- Delivered capped insert-only vocabulary promotion and canonical source binding, topic-scoped candidate discovery, no-pass-window research backfill before refresh/publication, and answer-authoring evidence-rank enforcement.
- Independent verification `local://atlas-vocab-backfill-verification-attempt-7-result.md@sha256:c5c28ab38ab17c4da53b53c21969f858944299df26f58b9ee21abeb4ff9dfa31` verified all fourteen frozen acceptance criteria. Sealed regression evidence `local://atlas-vocab-backfill-final-regression-attempt-7.json@sha256:31cddb7af23c4e8b453b5bd6347561e1682b8ec7ee0b78f7454e637ea2ad94f2` records 362 Atlas tests `OK` with an unchanged scaffold digest.
- Current user closure authority stopped the review/repair loop after the independently verified target, prohibited another same-outcome repair, successor plan/outcome, or continuation grant, and classified later review findings as residual/proof ceremony.
- Grant-scoped review `local://atlas-vocab-backfill-grant-review-attempt-2-result.md@sha256:958939953d9a5345545bc99c6e235de10d950048144584e7f29590ba2130ce55` was consumed with `CHANGES REQUIRED`; its sole finding `BLK-RVW-CANDIDATE-PENDING-BASE-HASH` is accepted residual risk. If a candidate source's current-hash pending-edge base changes between enumeration and revalidation, the current candidate hash can classify that otherwise valid refresh as drift before route preparation. No repair or successor work was opened.
- Terminal Standard assessment `local://atlas-vocab-backfill-learning-result.md@sha256:96f85de18eee8d029328118d19090fd7ffec9ec22d514fcce4ede26e17701b26` returned `NO DURABLE LEARNING`; no product or guidance bytes changed.
- Existing accepted residuals remain `ANC-RESIDUAL-FIRST-WRITER` and `ANC-RESIDUAL-MATCHING`. No bound-instance, profile, vault, synchronization, deployment, release, shipping, or Git effect occurred.
