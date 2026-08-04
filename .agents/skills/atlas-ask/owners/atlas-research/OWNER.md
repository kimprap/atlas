# atlas-research

## Qualified invocation

This ordinary Workflow Owner resource may execute only when one of these qualified conditions holds:

1. The selected Workflow Owner receives a live `/atlas-ask` Task whose dispatch binding names `atlas-research`.
2. An allowlisted current Workflow Owner loads this resource as a required Successor Owner in the same agent with the same root binding and `internal_caller` identity.
3. Any other load performs no further read, model work, façade call, profile/vault I/O, or write and returns `Redirect: invoke /atlas-ask.`

Only the selected Workflow Owner emits one outer `atlas-workflow-result.schema.json` result. A Successor Owner preserves its native current output and never creates another Task or outer result.



## Read first

1. Run `python3 scripts/atlas_tool.py capabilities`; require `vault.read`, `vault.list`, `vault.hash`, and `state.validate` for every research path, require `index.create_topic` for an explicitly approved absent-topic creation, and retain `vault.conditional_replace` only for the existing-topic update path.
2. Issue every façade request as a version-1 envelope with `python3 scripts/atlas_tool.py call --input <path|->`.
3. Read `vault://atlas/ARCHITECTURE.md`, `skill://atlas-core/assets/markdown-registry-contracts.md`, `skill://atlas-core/assets/operating-cadence-and-guardrails.md`, and `skill://atlas-core/assets/research-library-templates.md`.
4. Use `vault.read` for the research index and registries, and `vault.list` only for bounded relevant artifact/topic directories. Validate the current registry bundle with `state.validate` before relying on topic freshness or relation rows.

## Workflow

- Default to `--vault-only`: use façade reads of existing Atlas source artifacts and topic files, not host paths or raw web results.
- Use `--acquire` only when the user explicitly allows acquisition. Run the allowlisted Successor Owner resource `skill://atlas-ask/owners/atlas-acquire/OWNER.md` first; then synthesize only from the artifacts it has materialized and re-read through the façade.
- Resolve an existing topic only from the validated `TOPICS.md`/`RELATIONS.md` state. If it is dirty, refreshing, or blocked, hand off to the allowlisted Successor Owner resource `skill://atlas-ask/owners/atlas-refresh/OWNER.md` before treating its index as a current answer or bypassing pending edges.
- Keep topic selection, evidence interpretation, claims, answer structure, and insufficiency judgments in the harness. The façade validates deterministic state and performs vault I/O; it does not make research decisions or synthesize prose.
- When the validated registry has no matching topic and the user explicitly approves durable creation, keep the selected `--vault-only`/`--acquire` authority gate, then construct exactly one semantic request with exactly these keys (using the approved values, not target bytes or revisions):
  ```json
  {
    "version": 1,
    "topic_id": "<topic-id>",
    "topic_path": "vault://atlas/summaries/research/<domain>/<subdomain>/topics/<topic-slug>/INDEX.md",
    "domain": "<domain-id>",
    "subdomain": "<subdomain-id>",
    "canonical_title": "<canonical-title>",
    "aliases": [],
    "include_terms": [],
    "exclude_terms": [],
    "related_topic_ids": [],
    "status": "active",
    "coverage_state": "insufficient",
    "confidence": "low",
    "refresh_model": "same-as-topic-creation",
    "created_on": "YYYY-MM-DD"
  }
  ```
  Populate the arrays and scalar identity fields from the explicit approved request in the contract's required normalized form; do not add keys or silently rewrite values. At the start of this branch, the skill selects one explicit UTC calendar date and replaces the `YYYY-MM-DD` placeholder with that date; it carries the same value unchanged in the façade request and returned creation receipt. Issue exactly `{"version":1,"op":"index.create_topic","args":<that request>}`. This absent-topic branch invokes no `vault.conditional_replace`, source/route transaction operation, Markdown renderer, revision/hash calculation, target ordering, or rollback choreography; the façade alone owns those boundaries. Report the returned authority, exact topic/subdomain/registry paths, state/revisions, receipt, validation, and findings. A deterministic failure or nonterminal/recoverable result stops before wider research action; acquisition cannot create a topic or any domain, subdomain, alias, or tag as a side effect.
- For an existing topic and an intentional allowed research update, use `research-library-templates.md` for the subdomain index, topic `INDEX.md`, and dated-pass shapes. Use `vault.hash` and `vault.conditional_replace` for the allowed target artifacts; preserve the façade revisions and never reimplement connector/CAS behavior.
- Record insufficiency as topic coverage state or pass findings instead of inventing unsupported answers from raw web results. Keep optional split files threshold-driven and update `## Read next` when they are created.

## Output

Report the topic path, pass path, mode used (`vault-only` or `acquire`), source artifacts consulted, any recorded insufficiency, and for an absent-topic create the façade authority, state/paths/revisions, receipt, validation, and findings.

Fixture policy: any smoke fixtures created while testing Atlas entrypoints are temporary verification data only and must be removed from `vault://atlas/` before the verification task completes.
