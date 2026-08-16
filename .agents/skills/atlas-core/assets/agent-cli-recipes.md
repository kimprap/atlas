# Atlas agent CLI recipes

Use `/atlas-ask` for user intent. A selected owner discovers commands with `python3 scripts/atlas_tool.py capabilities` and invokes the generated family/verb form with one operation-args object from `--input -` or a UTF-8 file. Low-level `call --input` consumes the full version-2 envelope. Operation literals below are exact.

## Source a URL

`url.normalize` for each explicit URL → one `source.inventory` with intent `presence|routine|resummarize` → presence stops read-only; routine selects only `new|active-due`; resummarize selects only `active` → `source.lookup` → external capture → `source.normalize_capture` → `source.worker_schema` → model proposal → `quality.validate_proposal` and `quality.validate_summary` → `source.prepare` → pass its transaction unchanged to `transaction.execute`, or to `transaction.recover` when required → call `transaction.successor` only when the façade reports the sole eligible successor → run the source owner's route procedure in process.

## Promote a staged source

For one explicitly selected frozen pair, call `source.prepare` with only `mode: promote`, `artifact_uri`, and `evidence_uri`. Pass its transaction unchanged to `transaction.execute`, or to `transaction.recover` when required; call `transaction.successor` only when the façade reports the sole eligible successor. Promotion never refetches, substitutes, or rewrites the staged pair.

## Answer a topic

`topic.inspect` with purpose `answer` → return managed topic content, freshness, and pending IDs. Perform no refresh, transaction, or write. Dirty content is explicitly stale and never presented as current.

## Research a topic

`topic.inspect` with purpose `research` → if state is `dirty|refreshing|blocked`, run the Refresh recipe in process and re-inspect → require `current` with zero pending edges → model draft → `research.prepare` → `research.execute`, or `research.recover` with the exact original request when required.

## Refresh a dirty topic

`topic.inspect` with purpose `refresh` → model draft from that bounded snapshot → re-run `topic.inspect` immediately before the effect → `refresh.execute`, or `refresh.recover` with the exact original request when required. Standalone refresh stops after this receipt.

## Create a topic

`topic.inspect` proves absence under the requested existing domain/subdomain → `index.create_topic`, or `index.recover_topic` with its exact original request when required. Topic creation does not synthesize research or create vocabulary, domains, subdomains, sources, relations, or passes.

## Explicit reroute

`source.lookup` → a fresh `source.lookup` for the same canonical URL → `vault.read` for the bound artifact and registries → `state.validate` → bounded route decision → `state.reduce` with `route-upsert` → `source.render_route_artifact` → `transaction.execute`, or `transaction.recover` when required → `transaction.successor` only when eligible. Calls to `source.snapshot_active`, `source.inventory`, capture, `source.prepare`, source-content writes, and source hash/date refresh are forbidden.

## Repair or migrate

`vault.read`, `vault.read_json`, `vault.list`, `vault.hash`, or `vault.digest_tree` plus `state.validate` → for one explicit reducer-authorized repair, call internal `transaction.execute` with exactly `version` and `event`, then call `transaction.recover` only with its exact returned transaction identity and byte-identical original request. For the current versioned migration, call `migration.prepare_topics_lists` → obtain separate candidate-bound approval → call `migration.apply_topics_lists` → use only its exact returned recovery operation and identity.

## Preview versus commit

Prepare, inspect, and preview operations return owner effect `none`. Execute and apply operations own writes. `partial|unknown` always blocks and reuses the returned recovery operation and identity byte-for-byte. `effect.execute` and `effect.recover` remain a lifecycle pair for the aggregate-effect envelope; neither is the adapter after `source.prepare` or route rendering.

## Lifecycle command index

Each lifecycle command appears exactly once. `capabilities --all` additionally reveals internal primitives used by the recipes.

| Operation literal | Family command |
|---|---|
| `effect.execute` | `effect execute` |
| `effect.recover` | `effect recover` |
| `index.create_topic` | `index create-topic` |
| `index.recover_topic` | `index recover-topic` |
| `migration.apply_topics_lists` | `migration apply-topics-lists` |
| `migration.prepare_topics_lists` | `migration prepare-topics-lists` |
| `quality.validate_proposal` | `quality validate-proposal` |
| `quality.validate_summary` | `quality validate-summary` |
| `refresh.execute` | `refresh execute` |
| `refresh.recover` | `refresh recover` |
| `research.execute` | `research execute` |
| `research.prepare` | `research prepare` |
| `research.recover` | `research recover` |
| `source.inventory` | `source inventory` |
| `source.lookup` | `source lookup` |
| `source.normalize_capture` | `source normalize-capture` |
| `source.prepare` | `source prepare` |
| `source.snapshot_active` | `source snapshot-active` |
| `source.worker_schema` | `source worker-schema` |
| `state.validate` | `state validate` |
| `topic.inspect` | `topic inspect` |
| `url.normalize` | `url normalize` |
| `url.resolve_reference` | `url resolve-reference` |
| `vault.digest_tree` | `vault digest-tree` |
| `vault.hash` | `vault hash` |
| `vault.list` | `vault list` |
| `vault.read` | `vault read` |
| `vault.read_json` | `vault read-json` |
