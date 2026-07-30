# Atlas Lean First-Invocation Plan

**Datetime**: 2026-07-30-1434
**Scope**: Atlas front-door approval and canonical source-presence lookup
**Summary**: Make the generic `/atlas` module present one brief route overview and obtain one exact approval before its first dispatch, while giving source-presence questions a bounded manifest-backed read path instead of the full ingestion path.
**Status**: DONE

## Context

The demonstrated request, “have you sourced <URL>?”, should not enter Atlas ingestion merely because it contains a URL. Today the generic `atlas` module dispatches immediately and `atlas-source` reaches for the lock-linearized all-active snapshot, which reads all registries and every active artifact; the intended end state instead presents one brief first-dispatch overview, waits for one exact approval, then answers through one manifest-backed point lookup. The selected deep-module seam is the existing Atlas façade: one raw URL hides normalization, canonical MANIFEST parsing/validation, identity matching, logical-path projection, and failure formatting without adding a cache or router vault access. `eng-flow` is an interaction reference only and is not modified by this plan.

## Tasks

- [x] T1. Define front-door approval and source-lookup contracts.
  - completed 2026-07-30-1501
- [x] T2. Implement the bounded manifest-backed lookup module.
  - completed 2026-07-30-1507
- [x] T3. Refine router, source-owner, command, and eval interfaces.
  - completed 2026-07-30-1512
- [x] T4. Prove behavior and sync the development framework snapshot.
  - completed 2026-07-30-1613 after independent verification, review-derived route-status repair, renewed verification, approved final review, framework resync/check, and terminal curation

## Approach

### T1 — Define front-door approval and source-lookup contracts

1. Update `.agents/ARCHITECTURE.md` first, in its **Atlas front door** definition, framework invariant, context-read invariant, Mode ownership table, and Source identity section:
   - An actionable initial `/atlas` request classifies one existing `atlas-*` owner, emits the exact three-field overview below, and stops before dispatch.
   - An unambiguous affirmative replying to the immediately preceding unchanged overview authorizes exactly that one dispatch; it is conversational authority only, with no token, hash, ledger, profile read, façade call, or vault write.
   - A changed constraint, caveat, different request, silence, or ambiguous response invalidates the pending overview; reclassify and render a replacement instead of dispatching.
   - The approval authorizes dispatch only. It is not reducer, mutation, destructive-effect, recovery, or material-choice authority.
   - Direct `/atlas-*` invocation bypasses this generic-router gate. Explicit classification-only requests, empty-argument goal clarification, and no-Atlas-owner outcomes execute no child and therefore do not add a dispatch approval.
   - Preserve the current unresolved-material-choice Ask. If it is needed to select an owner, resolve it first, then render the overview; the choice answer is not route approval.

   The skill-facing overview interface is exactly:

   ```text
   Goal: <one-sentence interpretation of the unchanged request>
   Next: <one selected skill://atlas-* owner and its first bounded action>
   Effect: <“read-only; no Atlas writes” or “write-capable through the selected owner; exact effects remain owner-gated”>

   Approve this Atlas route?
   ```

   For the demonstrated request, `Next` says `atlas-source` will normalize the URL and inspect its canonical source-manifest row; `Effect` is read-only with no fetch or Atlas write.
   Use `Effect: read-only; no Atlas writes` for source presence, route-status-only, `atlas-answer`, and `atlas-audit` requests. Use `Effect: write-capable through the selected owner; exact effects remain owner-gated` for source ingestion/resummarization, acquisition, rerouting, research, refresh, index, and migration. This is a conservative capability disclosure, not mutation approval.

2. In the same architecture-first change, add **Source presence lookup** as a no-write mode. Its performance/read contract is one complete `summaries/sources/MANIFEST.md` byte read plus an in-memory linear scan; it reads no artifact, TOPICS, RELATIONS, active-source snapshot, profile state beyond normal connector binding, or parallel cache.

3. Update `.agents/skills/atlas-core/assets/operating-cadence-and-guardrails.md` so the dispatch approval is explicitly distinct from host Ask: the existing Ask rules still apply only to unresolved material owner/scope/write-set/destructive/authority choices. An unanswered route approval dispatches nothing; an answered material Ask still requires the overview afterward.

4. Update `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` with the new operation and its exact wire contract:

   ```json
   {"version":1,"op":"source.lookup","args":{"url":"<raw HTTP(S) URL>"}}
   ```

   A successful `result` has exactly `canonical_url`, `manifest_revision`, and `row`. `row` is `null` for an unambiguous absence or:

   ```json
   {
     "source_seq": 312,
     "source_id": "91fc906a9943",
     "canonical_url": "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f",
     "artifact_uri": "vault://atlas/summaries/sources/artifacts/...",
     "first_seen": "YYYY-MM-DD",
     "last_checked": "YYYY-MM-DD",
     "last_summarized": "YYYY-MM-DD",
     "content_hash": "<64 lowercase hex>",
     "refresh_after": "YYYY-MM-DD",
     "route_status": "unrouted|routed|no-topic-match|routing-blocked",
     "status": "active|archived"
   }
   ```

   `manifest_revision` is `sha256:<64 lowercase hex>` over the exact bytes read. Do not add a redundant `found` flag or expose raw Markdown column names. Invalid URL input is `URL_INVALID`; unreadable/missing MANIFEST is the existing `IO_FAILURE`; strict UTF-8 decode failure is `MANIFEST_UTF8_INVALID` at `vault://atlas/summaries/sources/MANIFEST.md`; malformed, duplicate, noncanonical, or URL/source-ID-inconsistent MANIFEST state returns deterministic MANIFEST findings with no false absence. An archived row is found and reported as archived.

### T2 — Implement the bounded manifest-backed lookup module

1. In `scripts/atlas_state.py`, extend `_validate_manifest` to enforce the already-documented identity invariant for every row using the existing `normalize_canonical_url` and `source_id_for` imports:
   - `MANIFEST_CANONICAL_URL_INVALID` when normalization rejects the cell;
   - `MANIFEST_CANONICAL_URL_NOT_NORMALIZED` when normalization changes it;
   - `MANIFEST_SOURCE_ID_URL_MISMATCH` when the row’s ID is not derived from its normalized URL.

   Add exactly:

   ```python
   def lookup_manifest_row(
       manifest_text: str, canonical_url: str
   ) -> tuple[dict[str, str] | None, list[Finding]]:
   ```

   It composes `_parse_table("manifest", manifest_text)` and `_validate_manifest`, returns normalized findings before lookup, derives the expected source ID with `source_id_for(canonical_url)`, and returns one row only when both `Canonical URL` and `Source ID` match. It does not parse TOPICS/RELATIONS or expose another Markdown parser. The planning-time bound MANIFEST check observed 154 rows, zero structural findings, and zero URL/ID mismatches, so this enforcement aligns existing state rather than defining a migration.

2. In `scripts/atlas_tool.py`, add private `_source_lookup(connector, args)` beside `_snapshot` and dispatch `source.lookup` to it:
   - Parse exactly one `url` argument with existing `_args`/`_text`.
   - Reuse `atlas_url.normalize_canonical_url`; map its `ValueError` to the same `URL_INVALID` at `args.url` used by `url.normalize`.
   - Call `connector.read_bytes(MANIFEST)` exactly once. Map strict decode failure to `Failure("MANIFEST_UTF8_INVALID", MANIFEST, "manifest is not valid UTF-8")`, compute `manifest_revision` from those same bytes, then call `atlas_state.lookup_manifest_row`.
   - Pass helper findings through existing `_reject`.
   - Convert only the matching row to the typed snake-case result above, including integer `source_seq` and `_logical(row["Artifact"])`; return `row: null` when absent.
   - Add `source.lookup` to both sorted `OPERATIONS` and `_READ_ONLY_OPERATIONS`. Do not call `_mutations`, `mutation_session`, `_documents`, `_snapshot`, `vault.read`, `connector.revision`, or `atlas_source.parse_artifact`.

   Keep `source.snapshot_active` unchanged: it remains the distinct lock-linearized cohort interface for workflows that need every active source and verified artifact revisions. No change belongs in `scripts/atlas_source.py`, `scripts/atlas_url.py`, `scripts/atlas_connector.py`, scaffold state, or living source rows.

3. Add behavior-defining tests at the existing interfaces:
   - `tests/test_atlas_state.py`: canonical hit, absence, archived hit, malformed/duplicate table rejection, noncanonical URL, and URL/ID mismatch through `lookup_manifest_row`.
   - `tests/test_atlas_tool.py`: add `source.lookup` to the exact operation inventory; test canonical-equivalent raw URL normalization, typed active row, `row: null`, archived row without an artifact file, `URL_INVALID`, `MANIFEST_UTF8_INVALID`, manifest finding propagation, and exact same-byte revision.
   - Add a delegating recording connector in `tests/test_atlas_tool.py` that exposes production `read_bytes` but fails if lookup requests a mutation session or reads any URI except MANIFEST. Give it `conditional_replace: unavailable`; assert `capabilities()` still advertises and `execute()` still runs `source.lookup`, then assert its complete read log is exactly `[MANIFEST_URI]` so repeated MANIFEST reads also fail the contract.

### T3 — Refine router, source-owner, command, and eval interfaces

1. Revise `.agents/skills/atlas/SKILL.md` as a thin, stateless router:
   - Preserve `name: atlas` and `disableModelInvocation: true`; change the description to state that generic invocation presents one approved first-owner route before dispatch.
   - Add a source-presence/status signal before the generic explicit-URL ingestion signal; both select `skill://atlas-source`, but the overview distinguishes the read-only first action.
   - For normal actionable requests, render `Goal` / `Next` / `Effect`, ask the exact approval sentence, and halt. Do not load the child before approval.
   - Accept only an unambiguous affirmative tied to the latest unchanged overview. On acceptance, load exactly the selected owner with the original unchanged request and any separately answered material choice, then exit the router; never pass the word “approved” as the child request or add a second router gate.
   - Preserve the existing classification-only JSON shape (`first_owner`, `ask_required`, `router_write_set`), non-Atlas short circuit, answer/conditional-refresh material Ask, no router I/O/write set, and direct expert invocation. In classification-only output, `ask_required` continues to mean an unresolved material choice; it does not encode the normal runtime dispatch approval because the probe cannot dispatch.

2. Add an early terminal **Source presence lookup** branch to `.agents/skills/atlas-source/SKILL.md`, before flags, snapshot, fetch, evidence, or ingestion:
   - Preserve `name: atlas-source` and `disableModelInvocation: true`; change the description from ingestion-only to explicit-source presence lookup or ingestion.
   - Pure questions such as “have you sourced <URL>?”, “is <URL> in Atlas?”, “what is its Atlas source status?”, and “check whether <URL> has been ingested” call only `source.lookup`.
   - Report `Sourced: yes|no`, canonical URL, and, when found, source ID/sequence, artifact URI, checked/summarized/refresh dates, route status, and active/archived status. Do not read the artifact to invent a title; the manifest revision is lookup provenance and need not appear in the brief answer.
   - `row: null` stops as not sourced and never falls through to ingestion. Malformed URL or invalid MANIFEST is an error/no-write result, not “not sourced.” For several explicit URLs in a pure presence request, call the singular operation once per URL in request order and report one result per URL; do not create a bulk façade method.
   - “Source”, “ingest”, “add”, “import”, “check and add if missing”, mode flags, and resummarization remain write-capable ingestion intents on the existing path. “Have you sourced and routed?” may use the row’s `route_status`; relation-level explanation still belongs to `atlas-route`.

3. Keep command bodies thin but make their interface descriptions truthful:
   - `.agents/commands/atlas.md`: change only its description to say the generic command presents and approves one first-owner route before dispatch.
   - `.agents/commands/atlas-source.md`: change its description and final argument sentence to say the direct command checks source presence or ingests explicit sources; retain `$ARGUMENTS` forwarding and the empty-input clarification.
   - `.agents/skills/atlas-core/SKILL.md` and `.agents/AGENTS.md`: add `source.lookup` to the state/source façade inventories.
   - `README.md`: update only the `/atlas` and `/atlas-source` rows plus the short front-door sentence to describe first-dispatch approval and presence lookup. Do not copy workflow checklists into commands or README.

4. Extend the existing skill eval/surface proof without asserting generated prose:
   - In `.agents/skills/atlas-core/assets/evals/agent-tooling.json`, retain all 23 existing cases and insert these five cases after `atlas-router-source`, raising the total to 28. The fifth case is the review-derived guard that prevents a read-only source-ID status request from dispatching the write-capable route owner:
     - `atlas-router-source-presence-overview`: initial request `Have you sourced https://example.com/article?`; expected `{first_owner:"atlas-source", approval_required:true, overview_fields:["Goal","Next","Effect"], dispatch_count:0, router_write_set:[]}`.
     - `atlas-router-source-presence-approved`: the same original request, its immediately preceding read-only `atlas-source` overview, and reply `approved`; expected `{first_owner:"atlas-source", approval_required:false, dispatch_count:1, forwarded_request:"unchanged", router_write_set:[]}`.
     - `atlas-router-source-presence-changed-reply`: the same original request/overview and reply `Approved, but resummarize it`; expected `{first_owner:"atlas-source", approval_accepted:false, approval_required:true, dispatch_count:0, reoverview_effect:"write-capable", router_write_set:[]}`.
     - `atlas-source-presence-lookup`: direct owner request `Have you sourced https://example.com/article?`; expected `{mode:"source-presence-lookup", operations:["source.lookup"], fetch:false, artifact_reads:[], write_set:[]}`.
     - `atlas-router-source-id-status-needs-url`: initial request `What is the route status of source ID 0123456789ab?`; expected `{first_owner:null, required_input:"canonical_url", approval_required:false, dispatch_count:0, router_write_set:[], forbidden_owners:["atlas-route"]}`.
   - In `tests/test_atlas_quality.py::test_agent_tooling_fixture_is_generic_bounded_and_behavioral`, update the exact fixture count/order and assert the five exact expected mappings above. Do not change the existing classification-only owner mappings, answer/conditional-refresh material-choice expectation, source-recovery Ask, or non-Atlas near misses.
   - In `tests/test_atlas_harness_surface.py`, assert the three overview labels and approval appear before child loading in `atlas/SKILL.md`; assert the source-presence branch and `source.lookup` appear before `source.snapshot_active` and fetch in `atlas-source/SKILL.md`; retain thin-command and no-reimplemented-identity checks.

### T4 — Prove behavior and sync the development framework snapshot

Run the focused and full verification in the order below. Only after code, contract, skill, and eval proof passes, sync the product-owned architecture to the repository’s intended local development instance `atlas`, then run the instance checker. If the checker reports unrelated concurrent living-state drift, report the exact deterministic findings and do not repair living state under this plan.

## Critical files & anchors

- `.agents/skills/atlas/SKILL.md` — `Contract`, `Classification-only output`, and `First-owner matrix`; the generic router interface and approval order.
- `.agents/skills/atlas-source/SKILL.md` — `Resolve mode and evidence boundary`; the terminal presence branch must precede ingestion.
- `.agents/skills/atlas-core/assets/markdown-registry-contracts.md` — Atlas façade operation table, canonical URL rules, active snapshot, and manifest dedupe semantics.
- `scripts/atlas_state.py` — `_parse_table`, `_validate_manifest`, and new `lookup_manifest_row`; the canonical registry implementation locality.
- `scripts/atlas_tool.py` — `OPERATIONS`, `_READ_ONLY_OPERATIONS`, `_snapshot`, `_dispatch`, and new `_source_lookup`; the external façade seam.

## Verification / Done criteria

Run from `/Users/kim/dev/atlas/app`; the unit/eval commands require no environment variables and use temporary local profiles.

- [x] `python3 -m unittest tests/test_atlas_url.py tests/test_atlas_state.py tests/test_atlas_source.py tests/test_atlas_tool.py` passes. The new tests prove one raw URL produces one bounded typed row/absence, only MANIFEST bytes are read, read-only connectors work, archived rows remain visible, and malformed identity/state never becomes false absence.
- [x] `python3 -m unittest tests/test_atlas_quality.py tests/test_atlas_harness_surface.py` passes. The evals prove initial overview/no dispatch, exact approval/one dispatch, changed reply/no dispatch, preserved material Ask, presence mode with only `source.lookup`, and source-ID-only status requiring a canonical URL without dispatching `atlas-route`.
- [x] `python3 -m unittest discover -s tests` passes once after the focused checks.
- [x] `python3 scripts/atlas_tool.py capabilities` returns `source.lookup` in the sorted operations list.
- [x] The following end-to-end read-only smoke succeeds:

  ```bash
  printf '%s\n' '{"version":1,"op":"source.lookup","args":{"url":"https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f"}}' \
    | python3 scripts/atlas_tool.py call --input -
  ```

  Expected observable output: `ok:true`, the canonical gist URL, a `sha256:` MANIFEST revision, and a row whose `source_id` is `91fc906a9943`, without source fetch or Atlas mutation. If concurrent user work legitimately removes that living row, do not change code or recreate it; the deterministic fixture-backed hit/absence tests remain the acceptance proof and the smoke reports `row:null`.
- [x] Capture the active-harness transcript for `/atlas have you sourced https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f?`. Before approval, inspect the transcript/tool trace and observe only `Goal` / `Next` / `Effect` plus `Approve this Atlas route?`, with no `skill://atlas-source` load and no Atlas façade/vault/fetch call. Reply `approved`; the same trace must then show exactly one `skill://atlas-source` load and one `source.lookup` call carrying the original URL, no `source.snapshot_active`, fetch, artifact read, write, or second router approval. In separate fresh invocations, capture that `Approved, but resummarize it` produces a replacement write-capable overview with zero child dispatches, and direct `/atlas-source have you sourced <URL>?` bypasses the router gate. Retain these observed traces as the execution evidence rather than treating fixture text alone as behavioral proof.
- [x] The review-derived route-status regression is reproduced by active-harness trace `019fb230-7858-7000-b534-4f3b143dbf31` (source-ID-only status incorrectly presented `atlas-route` as read-only) and closed by trace `019fb234-325b-7000-a946-0b56897883d8` (canonical-URL clarification, no overview, approval, child load, façade call, or write). Fresh post-repair traces `019fb235-aafc-7000-9ee0-51428aff048a` and `019fb236-d36a-7000-a72e-d877d9e685cd` re-prove the explicit-URL initial gate, one approved `source.lookup` dispatch, and changed-reply reoverview against the repaired target.
- [x] `python3 scripts/atlas-instance.py sync-framework --name atlas` succeeds only after the behavior checks, then `python3 scripts/atlas-instance.py check` passes with the product-owned architecture snapshot current.

## Assumptions & contingencies

- “First invocation” means the initial actionable turn of each new generic `/atlas` request. Its approval continuation and selected expert workflow do not repeat the router gate; a later new `/atlas` goal receives a new overview.
- Dispatch approval is ordinary conversational approval, matching the demonstrated `eng-flow` behavior; it is not a two-option host Ask. Existing expert-owned Ask gates remain because they authorize different material choices and effects.
- The one-operation raw-URL interface is deliberate: requiring callers to invoke `url.normalize` and pass a canonical pair would leak identity ordering through the seam. `source.lookup` internally reuses the sole normalizer, so no normalization convention is duplicated.
- `MANIFEST.md` remains canonical and the point lookup remains an $O(n)$ scan of one Markdown table. Do not add an index/cache until observed scale requires an explicit architecture decision.
- If implementation-time MANIFEST validation exposes concurrent invalid living rows, finish and verify the product change against temporary fixtures, report the exact rows/findings, and leave repair to an explicitly authorized `atlas-index` or migration workflow.
