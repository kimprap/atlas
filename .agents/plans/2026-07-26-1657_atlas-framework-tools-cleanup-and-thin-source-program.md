# Atlas framework tools, retained-root closure, and thin-source campaign

**Datetime**: 2026-07-26-1657
**Scope**: Atlas product tooling/evals, retained campaign-root closure, and living thin/error-source decisions
**Summary**: Productize the smallest durable agent-tool surface proven by campaign failures, use it to verify and close retained historical campaigns before exact cleanup, then run a separate decision-gated campaign for thin/error sources. The executor materializes two repository plans because product/cleanup closure and living-source remediation have different authorities, mutation seams, and completion lifecycles.
**Status**: PENDING

## Context

Atlas currently has deterministic URL, quality, state, source-rendering, and transaction cores, but no product-owned agent tool that resolves the active `vault://atlas/` profile, returns undecorated exact bytes/JSON, performs strict compare-and-swap, or advertises those capabilities. That gap forced campaign agents to receive a parent-supplied host path and one-off Python for packet reads and canonical JSON writes. The requested end state is two serial repository plans: first, promote the minimal provider-neutral tool/eval surface and use it to audit, delete, and close the retained campaigns; second, review every current active source for thin/error behavior, obtain explicit decisions in five-row batches, and mutate only the approved affected rows.

## Tasks

- [ ] T1. Materialize two repository plans and freeze authorities
- [ ] T2. Add failing tool and behavior evals
- [ ] T3. Define first-class tool and thin-source contracts
- [ ] T4. Implement connector, discovery, and tool facade
- [ ] T5. Align agent surfaces and pass fresh-context evals
- [ ] T6. Re-audit four retained roots and authority loss
- [ ] T7. Delete only the exact approved retained roots
- [ ] T8. Close and archive eligible predecessor plans
- [ ] T9. Freeze all current sources for thin/error review
- [ ] T10. Capture and classify every frozen source
- [ ] T11. Resolve flagged sources in five-row batches
- [ ] T12. Apply only the final approved projection
- [ ] T13. Refresh affected topics and close the campaign

## Approach

### Program split and ordering

Use two repository plans, not one monolith:

1. `YYYY-MM-DD-HHMM_atlas-agent-tools-and-campaign-closure.md` owns T1–T8. It changes product contracts/code/evals, then deletes historical temporary roots and archives only the plans whose remaining gates that deletion closes.
2. `YYYY-MM-DD-HHMM_atlas-thin-error-source-review.md` owns T9–T13. Materialize it during T1 so its scope and dependency are durable, but leave it `PENDING` until Plan A is `DONE`; change it to `IN_PROGRESS` only when T9 starts.

If `.agents/plans/2026-07-26-1657_atlas-framework-tools-cleanup-and-thin-source-program.md` exists at execution time, treat it as the umbrella record and replace its research placeholders with links and lifecycle status for the two plans; do not create a second umbrella. The split is load-bearing: Plan A edits product-owned files and performs destructive historical cleanup, while Plan B operates on living research with repeated user decisions and source/route transactions.

### T1 — Materialize plans and freeze authorities

1. Start Plan A, create Plan B, and record exact hashes for `.agents/ARCHITECTURE.md`, `.agents/AGENTS.md`, the four existing Python cores, the source/acquire/route/refresh/audit skills, the bound `vault://atlas/ARCHITECTURE.md`, and all four living registries. Record the active-profile identity from `../vault/config/profiles/local.yml` (`profile: local`, `instance: atlas`, `connector: local-fs`, root `instances/atlas`) without persisting its host-resolved root.
2. Recompute the report-defined directory digest for each retained root: sort a UTF-8 manifest by relative POSIX path; emit `D\t<relative>/` per directory and `F\t<file-sha256>\t<bytes>\t<relative>` per file, each LF-terminated; hash the manifest. Bind the observed digest/count tuple before using any retained artifact for eval extraction:
   - `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23/` — expected `17f7e41cd27a92472f85bcb5e6d9bdd906b31aeaf41b531ee3d1ec6f44cf244e`.
   - `vault://atlas/tmp/living-source-retrospective-conformance-2026-07-23-t2-recovery/` — expected `877fd095759fabe8f0e235cb26232d227a46147a8842cdfa732f9c3dcfc210f1`.
   - `vault://atlas/tmp/living-source-retrospective-conformance-t2-recovery-2026-07-24/` — expected `41782e802043363148f0e4a055b7d40fc9384d92979aade0c3d835690ba7b001`.
   - `vault://atlas/tmp/source-quality-revisit-2026-07-21/` — expected `17d331a8120d4ddc87238dd5e4f321a5e6922a74433365e996242f4fff39e04a`.
3. Use retained artifacts only to extract recurring failure shapes. Convert each promoted case to a minimal synthetic fixture; never copy living source text, transaction bodies, host paths, provider prompts, or campaign-specific helper behavior into the product.

### T2 — Add red evals before implementation

1. Add `.agents/skills/atlas-core/assets/evals/agent-tooling.json` with exact top level `{version:1,cases:[...]}`. Each case has exactly `id`, `prompt`, `fixture`, and `expected`; expected values stay out of the model-visible packet. Cover:
   - capability discovery from the app root;
   - exact JSON read plus canonical sorted-key UTF-8/LF write using only logical paths;
   - sorted logical listing and full-byte SHA-256 revision;
   - stale compare-and-swap conflict with byte-identical target;
   - bounded discovery normalization/dedupe against a manifest;
   - one source transaction apply and recover on a disposable instance;
   - path traversal/query/fragment rejection;
   - thin standalone scope required, aggregate scope required, inaccessible no-write, substantive article no question, and untrusted evidence ignored;
   - a non-Atlas JSON-edit near miss that must not claim or require Atlas capabilities.
2. Add `.agents/skills/atlas-core/assets/source-summary-proposal.schema.json` as JSON Schema 2020-12 with `$id: "urn:atlas:source-summary-proposal:1"`, all T3 top-level/assessment keys required, `additionalProperties:false` at every object, nonempty strings, `key_points.minItems:1`, other section/link arrays allowed empty, and reusable `$defs` for claims/assessment items/links. `validate_proposal` remains the dependency-free executable owner; tests require it and the schema to accept/reject the same fixtures. Add red fixtures proving native types, supported month/day publication precision, attached claim locators, unknown-key rejection, and byte-identical repeated rendering. Include one metamorphic pair with different irrelevant request/provider context and identical evidence; require the same structural/assessment outcome and forbid leaked context without requiring identical prose.
3. Extend `scripts/atlas_quality.py::_fixture_cases` to accept either the existing named case arrays or one generic `cases` array, never both. Add CLI `prepare-calibration --input <path|->`; its version-1 input is exactly `{version,fixture_text,case_ids}`, it rejects unknown/duplicate/missing IDs, and it outputs `{version:1,cases:[{id,prompt,fixture}]}` in fixture order with no `expected` key. Keep `validate_calibration` exact response shape `{version:1,results:[{id,actual}]}` and current sorted findings/exit classes.
4. Add failing unit cases in `tests/test_atlas_tool.py`, `tests/test_atlas_connector.py`, `tests/test_atlas_discovery.py`, and the existing source/quality tests before production code. Assert observable bytes, revisions, state diffs, proposal/render invariants, and error codes; do not assert source prose, prompt wording, or provider identity.

### T3 — Define the durable contracts before code

1. Update `.agents/ARCHITECTURE.md` first. Define one agent-facing tool family over the existing pure cores and connector port. The family owns capability discovery, exact logical vault I/O, bounded discovery normalization, canonical JSON, strict full-byte CAS, directory digests/approved temp-tree deletion, typed summary proposal rendering, and recoverable transaction execution. Business rules stay in `atlas_url`, `atlas_quality`, `atlas_state`, and `atlas_source`; network fetch/search and model calls remain harness capabilities, not connector behavior.
2. Define the initial storage adapter as `atlas-local-fs-cas-v1`. It reads `ATLAS_VAULT_PROFILE` when set, otherwise `../vault/config/profiles/local.yml`; accepts only the verified scalar profile shape; resolves relative `local_fs.root` against the vault repository containing `config/profiles/`; maps only `vault://atlas/<relative>` beneath that root; and rejects traversal, query, fragment, symlink escape, invalid UTF-8 where text/JSON is required, and all non-`local` mutation profiles. Unsupported connectors may report capabilities but return `mutation_unavailable` before any write.
3. Add the semantic proposal contract to the architecture and `source-summary-quality-guide.md`. The model returns exactly:
   ```json
   {
     "version": 1,
     "title": "string",
     "author": "string",
     "published": "YYYY-MM-DD|YYYY-MM|Unknown",
     "source_kind": "article|paper|repo|thread|video|docs|other",
     "assessment": {
       "coverage": {"value": "complete|partial|failed", "note": "string"},
       "confidence": {"value": "high|medium|low", "note": "string"},
       "evidence_strength": {"value": "high|medium|low", "note": "string"},
       "practicality": {"value": "high|medium|low|n/a", "note": "string"},
       "stability": {"value": "stable|moving|speculative", "note": "string"},
       "reuse_value": {"value": "high|medium|low", "note": "string"},
       "recommended_posture": {"value": "adopt|trial|watch|reference-only|ignore", "note": "string"}
     },
     "tldr": "string",
     "key_points": [{"text": "string", "locators": ["string"]}],
     "mechanics": [{"text": "string", "locators": ["string"]}],
     "evidence": [{"text": "string", "locators": ["string"]}],
     "caveats": [{"text": "string", "locators": ["string"]}],
     "reuse_cues": [{"text": "string", "locators": ["string"]}],
     "links": [{"url": "string", "relevance": "string"}]
   }
   ```
   Prose and section-array lengths may vary. `key_points` must be nonempty; `mechanics`, `evidence`, `caveats`, `reuse_cues`, and related `links` may be empty when the source has no supported content for that section, and the renderer emits the heading without synthetic filler. Claim `locators` may be empty only when the evidence reader exposes no finer locator; consequential claims still require locators when available under the existing quality guide. Unknown keys, empty required strings, unsupported links/locators, invalid enums, or context leakage fail. The renderer supplies the canonical link from source state; proposal `links` are related textual URLs present in evidence. Identity/acquisition/routing fields never come from the model. Add `atlas_quality.validate_proposal(proposal, evidence_bundle) -> list[Finding]`; after it and the seven-item checklist pass, call `atlas_source.render_summary_proposal(proposal, classification, source_state) -> str`, where classification is exactly `{primary_domain,subdomains,secondary_domains,canonical_tags,candidate_terms}`. The renderer owns native frontmatter types, fixed section order/headings, source identity/provenance, and exact final LF; `validate_summary` remains the final artifact gate.
4. Update `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` with one canonical call response:
   ```json
   {"version":1,"ok":true,"op":"<literal-or-null>","result":{},"findings":[]}
   ```
   Use sorted keys, compact separators, UTF-8, and one trailing LF. Parsed validation/state/conflict failures return the same envelope with `ok:false`, `result:null`, and sorted `{code,path,detail}` findings; malformed request JSON may emit stderr only. Exit `0` success/no-op, `2` validation/state rejection, and `3` binding/I/O/conflict.
5. Expose these operation literals and exact operation fields:
   - `vault.read|vault.read_json`: `{path}` → `{path,revision,body|value}`; missing is `VAULT_NOT_FOUND`.
   - `vault.list`: `{path,recursive}` → sorted `{path,kind,revision}` entries; directory revisions are `null`.
   - `vault.hash`: `{path}` → `{path,revision,bytes}`.
   - `vault.write_json`: `{path,expected_revision,value}` and `vault.conditional_replace`: `{path,expected_revision,body}` → `{path,previous_revision,revision,outcome}`; revision is `missing|sha256:<64 lowercase hex>`.
   - `vault.digest_tree`: `{path}` → `{path,digest,files,directories,content_bytes,manifest_bytes}`.
   - `vault.delete_tree`: `{path,expected_digest,approval}` → the same counts plus `outcome:"deleted"`.
   - `discovery.normalize`: `{scope,candidates,manifest_text}` using T4's exact shapes.
   - `url.normalize`, `quality.validate_proposal`, `quality.validate_summary`, `state.validate`, `state.reduce`, `source.render_summary`, `source.merge_artifact`, and `source.render_route_artifact`: `{input:<the owning function/CLI's version-1 payload>}` → the owning canonical result inside `result`.
   - `transaction.execute`: `{transaction_root,event_path,event_record,targets,attempt,predecessor_sha256}`. Each target is exactly `{path,input_revision,output_body}`; attempt `0` requires predecessor `null`. Under the instance lock, canonicalize and exclusive-create `event_record` at `event_path` (an existing byte-identical record is idempotent; any other bytes collide), re-read every target and verify `input_revision`, build/execute through the existing helpers, and return `{status,base_transaction_id,transaction_id,intent_sha256,terminal_path,terminal_sha256}`.
   - `transaction.recover`: the same fields plus `{abort_unprepared}`. Require the canonical event record already at `event_path`, reconstruct the identical plan from current request bytes, call `recover_transaction`, and return the same terminal result.
   - `transaction.successor`: `{transaction_root,event_path,event_record,targets,predecessor:{attempt,predecessor_sha256,terminal_path}}`. Reconstruct that exact predecessor plan, verify the named terminal is its exact `aborted|rolled-back` terminal, call `build_successor_plan` to derive attempt `n+1`, execute under the instance lock, and return the same terminal result.
   `capabilities` returns the normal envelope with result `{tool:"atlas",logical_root:"vault://atlas/",adapter:{id,profile,instance,mutation},operations:[sorted literals]}` and never includes a resolved host path.
6. Extend the source-ingestion invariant: a semantically thin standalone page that can support only a proportional page summary but cannot support the user's stated resource intent requires an explicit decision before writing. Allowed decisions are `page-only`, `expand-selected`, `replace-source-url`, or `defer`; aggregate pages allow `page-only`, `expand-selected`, or `defer`. Detection is semantic, never a URL/domain/link-count/length classifier. `page-only` is unavailable when the page has insufficient readable text. `replace-source-url` ingests the selected URL as a new independent source and leaves the original source byte-identical; it does not invent an unsupported source-retirement transition.

### T4 — Implement the minimal first-class tool family

1. Add `scripts/atlas_connector.py`:
   - `resolve_profile(path: str | None = None) -> VaultProfile`;
   - `logical_relative_path(uri: str) -> str`;
   - `LocalFilesystemConnector`, implementing `atlas_source.ConnectorPort` plus sorted `list`, `revision`, `conditional_replace`, `digest_tree`, digest-bound `delete_tree`, and re-entrant `mutation_session()` context management.
   Use one instance-wide lock file at `<tempfile.gettempdir()>/atlas-tool-locks/<sha256(real-instance-root)>.lock` with `fcntl.flock(LOCK_EX)` for every create/write/delete/CAS/transaction call. `mutation_session()` owns the OS lock on first entry and maintains a connector-local depth count so `atlas_source.execute_transaction` can call connector methods without relocking; the final exit unlocks in `finally`. Use exclusive create, sibling-temp write + `fsync` + `os.replace` + parent `fsync`, and reread acknowledgement. `delete_tree` accepts only an existing descendant of `vault://atlas/tmp/`, exact `expected_digest`, and literal `approval: "delete-approved-root"`; it recomputes the digest while holding the instance lock, refuses symlinks/special files, deletes files then deepest directories, and reports exact counts. A mismatch performs zero deletions.
2. Add `scripts/atlas_discovery.py` with `normalize_candidates(scope, candidates, manifest_text) -> dict`. Require scope exactly `{kind,identifier,limit}` where `kind` is `explicit|feed|inbox|watchlist|repo-list|author-list|query|page-links` and `limit` is a positive integer. Candidate rows are exactly `{url,discovered_from,label}`. Reject an input count above the declared limit; normalize through `atlas_url.normalize_canonical_url`, dedupe by canonical URL/source ID, classify each as `new|existing|rejected`, preserve the first provenance row, and stable-sort outputs by source ID then canonical URL. It never fetches, crawls, scores officialness, or creates Atlas state.
3. Implement `atlas_quality.validate_proposal` and `atlas_source.render_summary_proposal` from T3. The renderer consumes no current time, connector, network, model, or ambient context; callers supply every identity/date/classification value. Add tool ops `quality.validate_proposal` and `source.render_summary` only after the owning functions pass direct tests.
4. Add `scripts/atlas_tool.py` with:
   - `capabilities(connector: AtlasConnectorPort | None) -> dict`;
   - `execute(request: Mapping[str, Any], connector: AtlasConnectorPort | None = None) -> dict`;
   - CLI `python3 scripts/atlas_tool.py capabilities` and `python3 scripts/atlas_tool.py call --input <path|->`.
   `vault.read_json` parses exact connector bytes. `vault.write_json` serializes `value` with `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"` and delegates strict CAS. Pure operations call existing owners. Transaction operations convert logical URIs to connector-relative paths, hold the same instance mutation lock for the whole execute/recover/successor call, and reuse `build_event_record`, `build_transaction_plan`, `execute_transaction`, `recover_transaction`, and `build_successor_plan`; durable results contain logical record paths only.
5. Add the three new scripts to `tests/test_atlas_harness_surface.py::test_reference_scripts_are_repo_local_and_dependency_free`. Keep them stdlib-only; permit only the current local core imports. Do not add an MCP server, provider SDK, network client, campaign helper, mega-workflow tool, or slash command.

### T5 — Align agent surfaces and run the evals

1. Update `.agents/AGENTS.md` (the canonical local file reached by the root `AGENTS.md` symlink) with a compact `Agent tools` table containing the capabilities command, `call --input -`, bounded discovery intake, typed proposal rendering, and the rule that agents persist only logical URIs. Add the three scripts to its layout. Do not edit host-global `/Users/kim/.agents/AGENTS.md`.
2. Update `atlas-core/SKILL.md`; `atlas-source`, `atlas-acquire`, `atlas-route`, `atlas-refresh`, and `atlas-audit` to invoke the façade instead of parent-supplied host paths or hand-built JSON. `atlas-source` requests the typed semantic proposal, validates it before reading routing state, then renders deterministically. `atlas-acquire` calls `discovery.normalize` after bounded harness discovery and before per-item `atlas-source`. Keep command stubs unchanged because the tool is not a user workflow entrypoint. Remove duplicate connector/hash/CAS/proposal-shape prose from entry skills once core contracts own it.
3. Extend `atlas-audit` with read-only `--agent-tools-calibration`: prepare blinded cases, run them in fresh contexts against an OS-temporary provisioned Atlas instance/profile, validate exact outcomes, and report provider/harness/model only as execution metadata. First run one pilot and inspect the resolved model. Use newly spawned default task agents; if any lane would resolve to Grok 4.5 xhigh, override that lane with GPT-5.6 Terra xhigh. Keep at most four agents concurrent, each packet below 50 KiB, one semantic pass, and a second reviewer only for a failed/ambiguous row.
4. Qualify behavior, not identical prose. Require identical canonical tool outputs, write sets, source identities, transitions, rendered structure, and scope gates across fresh contexts. Proposal prose may vary, but every required claim/caveat must remain evidence-backed, all context perturbation terms must stay absent, and both outputs must pass `validate_proposal`, the seven-item checklist, deterministic rendering, and `validate_summary`. Record cross-context evidence only; do not claim cross-provider empirical equivalence unless a second provider actually ran. Provider-neutrality is additionally enforced by the existing provider-name ban and absence of provider branches.
5. Sync `.agents/ARCHITECTURE.md` to the bound local instance only after product tests and isolated evals pass, then rerun the read-only capability check against `vault://atlas/`. Do not use the new tool to mutate living research during this task.

### T6–T8 — Retained-root cleanup and plan closure

1. Recompute each of the four digests with `vault.digest_tree` after product/eval closure. Audit by authority class, not filename heuristics:
   - Primary campaign root: detailed captures, evidence/checklists, review packets, candidates, transaction backups, and terminal bodies. The durable 2026-07-23 report already preserves all 503 final outcomes and all 431 source/route event and terminal hash pairs; living artifacts/registries are outside the root.
   - Two T2 recovery roots: full fresh-context preflight/corroboration records. The durable report preserves accepted outcomes and hashes, not the record bodies.
   - Predecessor forensic root: only remaining pre-write snapshots and forensic traces for two valid historical rewrites whose transaction history never existed. Deletion irreversibly discards those traces; no reconstruction or fabricated transaction record is allowed.
2. Append a cleanup projection to both durable reports naming every exact root/digest, preserved external authority, and irreversible loss. Present one destructive approval gate with the four exact root/digest rows; recommend deletion of all four because the user requested cleanup, but permit deselection. A withheld row is no-delete and keeps its owning plan open.
3. For each approved row, call operator-only `vault.delete_tree` with the approved digest and literal approval token, then require the root to be absent. If any digest drifted, perform zero deletion for that root, re-audit it, and present a new exact projection; never silently rebase approval.
4. Update report hashes and plan execution logs after deletion. Complete and atomically move these eligible plans to `.agents/plans/archive/` only after their own open cleanup tasks and done criteria are satisfied:
   - `.agents/plans/2026-07-24-1345_t2-entry-preflight-recovery.md` (already `DONE`, active only because archival was deferred);
   - `.agents/plans/2026-07-21-1613_living-source-quality-revisit.md`;
   - `.agents/plans/2026-07-23-2322_living-source-retrospective-conformance.md`.
   Leave `.agents/plans/2026-07-13-2349_ai-coding-workflow.md` and `.agents/plans/2026-07-14-1337_atlas-evaluation-continuous-research.md` active: their incomplete workflow/agenda scope is not closed by this cleanup. Mark Plan A `DONE` and archive it only after every selected root and applicable predecessor plan reaches its recorded terminal disposition.

### T9 — Freeze the post-framework source cohort

1. Require Plan A `DONE`, bound/product architecture byte identity, a successful isolated tool qualification, and zero `atlas_state.validate_documents` findings. Freeze every current `active` MANIFEST row, not a hard-coded count; the expected starting point is the verified 503-source state with MANIFEST SHA-256 `de6612bccd0f2cb3e5e16daf98c4eaa5f86af4ace72698097be805d4554d3c04`.
2. Create one campaign root `vault://atlas/tmp/thin-error-source-review-<YYYY-MM-DD>/`. Persist a canonical sorted-key freeze containing the MANIFEST revision, source-ID union hash, every source sequence/ID/URL/artifact/revision, product contract hashes, and the prior report's disposition only as provenance. Do not read any deleted predecessor temp root.
3. If the active count or manifest hash changed, include all current active rows and record the drift before classification; never omit concurrent user sources or restore a stale 503-row cohort.

### T10 — Capture and classify every source without living writes

1. Fetch the canonical URL for every frozen row through the active harness. Capture complete readable UTF-8 text and textual links only under the campaign root; retain no media/binary. Record exact outcomes `text|inaccessible|unauthorized|empty|non-text|error-page|insufficient-text`, retrieval bounds, raw-text SHA-256, redirect/final URL, and errors. A global connector/rate-limit outage leaves affected rows pending; it never mass-classifies them as errors.
2. Run deterministic high-recall indicators over all rows—root homepage, existing coverage/assessment posture, prior no-write/aggregate disposition, text/word/link counts, redirect identity, and fetch outcome—but use them only to build bounded model packets. They cannot decide thinness, aggregate scope, or officialness.
3. Perform one semantic classification over every frozen row using only the fresh canonical text/URL plus deterministic metadata. Return exactly one class: `substantive`, `thin-standalone`, `aggregate`, `inaccessible`, `non-text`, `insufficient-text`, `error-page`, or `canonical-mismatch`, with `page_supports`, `missing_for_resource_intent`, and source-local evidence. Do not regenerate or review the living summary. Centrally validate one terminal row per source; target-review only conflicting/invalid rows.
4. For flagged rows, run bounded discovery through the harness, then `discovery.normalize`: visible canonical-page links first; if insufficient, at most one official-site/repository query; at most ten candidates and no recursive crawl. A model may recommend official companion/replacement URLs, but the user selects them. Existing MANIFEST URLs are labeled `existing`; they never allocate a duplicate.
5. Freeze a decision manifest with exact row fields: `source_seq`, `source_id`, `canonical_url`, `living_artifact_revision`, `fresh_content_hash`, `classification`, `fetch_outcome`, `page_supports`, `missing_for_resource_intent`, `companion_candidates[{canonical_url,source_id,status,discovered_from,reason}]`, `recommended_action`, `allowed_actions`, `decision`, `selected_urls`, `replacement_url`, and `decided_at`. `decision` starts `pending`; substantive rows are recorded `not-flagged` outside the user queue.

### T11 — Resolve the flagged queue with the user

1. Order the queue by class (`inaccessible`, `non-text`, `insufficient-text`, `error-page`, `canonical-mismatch`, `thin-standalone`, `aggregate`), then numeric source sequence. Present five sources per `ask` batch. Each preview shows URL, what the current page supports, what is missing, fetch status, recommendation, and exact official candidate URLs.
2. Offer only actions legal for the row:
   - `page-only`: text is sufficient; keep or rebuild a proportional summary from that page only.
   - `expand-selected`: add selected official pages as independent companion sources; never merge their claims into the parent.
   - `replace-source-url`: add one selected better URL as a new source; leave the original byte-identical.
   - `defer`: exact no-write.
   Inaccessible/non-text/insufficient rows offer only replacement or defer unless a later successful fresh fetch changes their class. Aggregates do not offer replacement unless classification also found a canonical mismatch.
3. Recommend at most five companion URLs per row. If the user chooses expansion from a larger catalog, page child URLs in multi-select groups of five and obtain one final union confirmation. Persist each answered batch immediately as canonical JSON plus hash; an interruption resumes at the first `pending` row. No answer is `pending`, never page-only or implicit approval.
4. After every flagged row is terminal, build a separate exact mutation projection: existing-source page-only rebuilds, new companion sources, new replacement sources, duplicate/existing skips, and deferred/no-write rows. Present that projection once for final approval; edits rebuild only its affected rows, never all living summaries.

### T12 — Execute only the approved projection

1. Re-read every affected living artifact and registry revision. Drift invalidates only that row and returns it to decision review; unchanged rows retain approval.
2. `page-only`: validate fresh text and the current artifact. If hash and artifact are valid, record no-op; otherwise generate one source-bound candidate, run `atlas_quality.validate_summary` plus the seven-item checklist, and permit exactly one targeted revision.
3. `expand-selected` and `replace-source-url`: invoke ordinary `atlas-source` separately for each selected URL. Deduplicate through current MANIFEST. Companion/replacement claims remain in their own artifacts; parent/original bytes remain unchanged unless separately approved for page-only.
4. For every changed existing or new source, use `state.reduce`, `source.merge_artifact`, a recoverable `transaction.execute` source transaction, then bounded routing and a separate recoverable route transaction. Successors are legal only after a verified `aborted|rolled-back` terminal. Stop closure on `manual-conflict`; never force-write or invent compensation.
5. Publish a transaction-closure index binding decisions, evidence/candidate/checklist hashes, event/intent/terminal hashes, current target revisions, no-op/duplicate outcomes, and exact no-write rows. Require one terminal result per approved action and no transaction for unapproved/deferred rows.

### T13 — Refresh, report, clean, and archive

1. Derive affected topics only from validated source/route reducer output. Refresh only currently dirty affected topics with their complete reducer-owned pending-edge order; present the exact topic/edge projection before refresh. Use `refresh-start`, one dated pass/topic patch, and `refresh-complete`; on failure use `refresh-fail`.
2. Validate all registries and every changed/new artifact, verify no unapproved source byte changed, and run the instance check allowing only the pre-existing missing `vault://atlas/todos/TODOs.md` prerequisite if it is still the sole finding.
3. Write one durable source-run report under `vault://atlas/summaries/sources/runs/<YYYY>/<YYYY-MM>/` with the complete cohort filter, every user decision, affected candidates, transaction and refresh closure, final registry hashes, model/harness execution metadata, and residual deferred/error rows.
4. Compute the new campaign-root digest, present its exact cleanup projection, delete it only after explicit approval with `vault.delete_tree`, update the report with the final disposition/hash, then complete/archive Plan B and the umbrella plan. Retained rows keep Plan B open; never relabel retained temporary evidence as completed cleanup.

## Critical files & anchors

- `.agents/ARCHITECTURE.md` — framework invariants around logical vault paths, source evidence/scope gates, connector ownership, and deterministic transitions.
- `scripts/atlas_source.py:439-502,515-565,600-624,641-790` — `build_event_record`, `ConnectorPort`, transaction plan/execute/recover/successor APIs that the façade must reuse.
- `scripts/atlas_quality.py:891-953` — current exact calibration response contract; extend by blinding fixture preparation, not a second semantic validator.
- `.agents/skills/atlas-source/SKILL.md:26-59,61-95` — current ingestion/resummarization workflow and the owning location for the thin-standalone decision gate.
- `vault://atlas/summaries/sources/runs/2026/2026-07/2026-07-23--living-source-retrospective-conformance.md` — canonical 503-row outcome, transaction closure, retained-root digest algorithm, and T13 retention decision.

## Verification / Done criteria

- [ ] From `/Users/kim/dev/atlas/app`, `python3 -m unittest tests.test_atlas_connector tests.test_atlas_discovery tests.test_atlas_tool tests.test_atlas_quality tests.test_atlas_source tests.test_atlas_state tests.test_atlas_url tests.test_atlas_instance tests.test_atlas_harness_surface` passes.
- [ ] An isolated smoke provisions `atlas` under an OS temporary root, supplies a temporary `local-fs` profile via `ATLAS_VAULT_PROFILE`, and runs `python3 scripts/atlas_tool.py capabilities`; output names adapter `atlas-local-fs-cas-v1`, every declared op, logical root `vault://atlas/`, and no resolved host path.
- [ ] In that smoke, `vault.read_json` reads a logical packet, `vault.write_json` produces exact sorted-key compact UTF-8 plus one LF, a stale revision exits `3` without changing bytes, and `transaction.execute` followed by `transaction.recover` reports the same verified terminal.
- [ ] `discovery.normalize` maps duplicate URL spellings to one canonical source, separates a MANIFEST duplicate from a new candidate, rejects overflow/traversal, and returns byte-identical output on two runs.
- [ ] Blinded fresh-context cases all satisfy exact gates and write sets; the packet-roundtrip case needs no parent host-path correction; thin/aggregate/inaccessible/substantive cases produce the required decision/no-write behavior; the near miss does not claim Atlas work. Resolved models are recorded, and no Grok 4.5 xhigh lane runs without the required GPT-5.6 Terra xhigh override.
- [ ] Product and bound architecture are byte-identical after sync; rules/skills/commands contain no provider-specific branch; command stubs remain thin and unchanged.
- [ ] Every selected historical root matches its approved digest immediately before deletion, is absent afterward, and both durable reports record preserved authority and irreversible loss. All three eligible predecessor plans satisfy the plan completion contract and exist only under `.agents/plans/archive/`.
- [ ] Plan B accounts for every active frozen source exactly once and every flagged source has an explicit user decision; unanswered/deferred/error rows have no transaction.
- [ ] Every approved changed/new source has validated source and route terminals matching current living bytes; page-only claims use only parent text; companions/replacements are independent source IDs; duplicates allocate no row.
- [ ] Final registries have zero `atlas_state.validate_documents` findings, only affected dirty topics were refreshed with canonical pending-edge order, and no unapproved living artifact/registry byte changed.
- [ ] The thin/error report binds the cohort, decisions, transactions, refreshes, final hashes, and exact campaign-root cleanup disposition; all applicable Plan B tasks and verification boxes are checked before atomic archival.

## Assumptions & contingencies

- The product-owned local agent file is `.agents/AGENTS.md`; root `AGENTS.md` is its verified symlink. Host-global `/Users/kim/.agents/AGENTS.md` remains untouched.
- The initial production adapter is local POSIX `local-fs`. If the active profile is unsupported, ambiguous, non-local for mutation, or lacks lock/atomic-replace semantics, capabilities remain read-only and every write/delete/transaction halts; no host-path fallback is permitted.
- The current cohort is 503 active sources, but Plan B is bound to every active row observed at T9. Concurrent additions are included; concurrent identity/artifact drift reopens only affected decisions.
- `replace-source-url` is additive because Atlas has no legal source-retirement event. The old source remains valid and byte-identical; adding retirement semantics would require a separate architecture/reducer plan.
- Historical cleanup intentionally trades detailed campaign/preflight bodies and predecessor forensic traces for a lean vault after durable reports bind the accepted outcomes. Any root whose digest or authority map changes is excluded until a new exact approval.
- The missing `vault://atlas/todos/TODOs.md` check finding is pre-existing and unrelated. If any second instance finding appears, closure stops until that new finding is fixed.
- Semantic agent work uses newly spawned default task contexts after one resolved-model pilot. A lane that would use Grok 4.5 xhigh is replaced with GPT-5.6 Terra xhigh; model/provider identity is execution metadata and never product behavior.
