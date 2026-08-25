from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_quality  # noqa: E402
import atlas_source  # noqa: E402

AGENTS_ROOT = ROOT / ".agents"
SKILLS_ROOT = AGENTS_ROOT / "skills"
OWNER_ROOT = SKILLS_ROOT / "atlas-ask" / "owners"
FRONT_DOOR = SKILLS_ROOT / "atlas-ask" / "SKILL.md"
CORE = SKILLS_ROOT / "atlas-core" / "SKILL.md"
RECIPES = SKILLS_ROOT / "atlas-core" / "assets" / "agent-cli-recipes.md"
TOOLING_EVALS = SKILLS_ROOT / "atlas-core" / "assets" / "evals" / "agent-tooling.json"
RESULT_SCHEMA = (
    SKILLS_ROOT / "atlas-core" / "assets" / "atlas-workflow-result.schema.json"
)
TOOL = ROOT / "scripts" / "atlas_tool.py"

OWNERS = {"atlas-source", "atlas-research", "atlas-maintain"}
REMOVED_OWNERS = {
    "atlas-acquire",
    "atlas-answer",
    "atlas-audit",
    "atlas-index",
    "atlas-migrate",
    "atlas-refresh",
    "atlas-route",
}
MODE_MAP = {
    ("atlas-source", "presence"): "none",
    ("atlas-source", "answer"): "none",
    ("atlas-source", "ingest"): "one Goal/Effect approval",
    ("atlas-source", "resummarize"): "one Goal/Effect approval",
    ("atlas-source", "promote"): "one Goal/Effect approval",
    ("atlas-source", "reroute"): "one Goal/Effect approval",
    ("atlas-research", "answer"): "none",
    ("atlas-research", "research"): "one Goal/Effect approval",
    ("atlas-research", "refresh"): "one Goal/Effect approval",
    ("atlas-research", "create"): "one Goal/Effect approval",
    ("atlas-maintain", "audit"): "none",
    ("atlas-maintain", "repair"): "one Goal/Effect approval",
    ("atlas-maintain", "migrate"): "one Goal/Effect approval",
}
INVENTORY_INTENTS = {"presence", "routine", "resummarize"}
INVENTORY_DISPOSITIONS = {
    "new",
    "active-due",
    "active-not-due",
    "active",
    "archived",
    "duplicate",
    "rejected",
}
LIFECYCLE_OPERATIONS = {
    "effect.execute",
    "effect.recover",
    "index.create_topic",
    "index.recover_topic",
    "migration.apply_source_taxonomy_remediation",
    "migration.prepare_source_taxonomy_remediation",
    "migration.recover_source_taxonomy_remediation",
    "migration.apply_taxonomy_backfill",
    "migration.prepare_taxonomy_backfill",
    "migration.apply_vocabulary_domain_insertion",
    "migration.prepare_vocabulary_domain_insertion",
    "migration.apply_vocabulary_subdomain_insertion",
    "migration.prepare_vocabulary_subdomain_insertion",
    "quality.validate_proposal",
    "quality.validate_summary",
    "refresh.execute",
    "refresh.recover",
    "research.execute",
    "research.prepare",
    "research.recover",
    "source.inventory",
    "source.candidates_for_topic",
    "source.lookup",
    "source.normalize_capture",
    "source.prepare",
    "source.prepare_route",
    "source.snapshot_active",
    "source.worker_schema",
    "state.validate",
    "topic.inspect",
    "url.normalize",
    "url.resolve_reference",
    "vault.digest_tree",
    "vault.hash",
    "vault.list",
    "vault.read",
    "vault.read_json",
}
OWNER_REQUIRED_OPERATIONS = {
    "atlas-source": {
        "url.resolve_reference",
        "source.inventory",
        "source.lookup",
        "source.normalize_capture",
        "source.worker_schema",
        "source.prepare",
        "source.prepare_route",
        "vault.read",
        "state.validate",
        "transaction.execute",
        "transaction.recover",
        "transaction.successor",
    },
    "atlas-research": {
        "source.candidates_for_topic",
        "source.lookup",
        "source.prepare_route",
        "transaction.execute",
        "transaction.recover",
        "transaction.successor",
        "topic.inspect",
        "refresh.execute",
        "refresh.recover",
        "research.prepare",
        "research.execute",
        "research.recover",
        "index.create_topic",
        "index.recover_topic",
    },
    "atlas-maintain": {
        "vault.read",
        "vault.read_json",
        "vault.list",
        "vault.hash",
        "vault.digest_tree",
        "transaction.execute",
        "transaction.recover",
        "state.validate",
        "migration.prepare_source_taxonomy_remediation",
        "migration.apply_source_taxonomy_remediation",
        "migration.recover_source_taxonomy_remediation",
        "migration.prepare_taxonomy_backfill",
        "migration.apply_taxonomy_backfill",
        "migration.prepare_vocabulary_domain_insertion",
        "migration.apply_vocabulary_domain_insertion",
        "migration.prepare_vocabulary_subdomain_insertion",
        "migration.apply_vocabulary_subdomain_insertion",
    },
}
OPERATION_LITERAL = re.compile(r"[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\Z")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    match = re.search(rf"(?m)^(?P<marks>#+) {re.escape(heading)}\s*$", text)
    if match is None:
        raise AssertionError(f"missing Markdown section: {heading}")
    level = len(match.group("marks"))
    following = re.search(rf"(?m)^#{{1,{level}}} ", text[match.end() :])
    end = len(text) if following is None else match.end() + following.start()
    return text[match.end() : end]


def fenced_block_after(text: str, marker: str) -> str:
    start = text.index(marker)
    match = re.search(r"```text\n(?P<body>.*?)\n```", text[start:], re.DOTALL)
    if match is None:
        raise AssertionError(f"missing text block after: {marker}")
    return match.group("body")


def operation_literals(text: str) -> set[str]:
    values = re.findall(r"(?<!`)`([^`\n]+)`(?!`)", text)
    for block in re.findall(r"```text\n(.*?)\n```", text, re.DOTALL):
        values.extend(
            re.findall(
                r"(?<![a-z0-9_.])([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)(?![a-z0-9_.])",
                block,
            )
        )
    return {value for value in values if OPERATION_LITERAL.fullmatch(value)}


def assert_order(test: unittest.TestCase, text: str, tokens: list[str]) -> None:
    offset = 0
    for token in tokens:
        found = text.find(token, offset)
        test.assertGreaterEqual(found, 0, f"missing ordered token: {token}")
        offset = found + len(token)


def operation_specs() -> tuple[set[str], int]:
    tree = ast.parse(read(TOOL), filename=str(TOOL))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_operation"
    ]
    operations: list[str] = []
    for call in calls:
        value: ast.AST | None = None
        for keyword in call.keywords:
            if keyword.arg in {"op", "operation"}:
                value = keyword.value
                break
        if value is None and call.args:
            value = call.args[0]
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            raise AssertionError(
                "operation catalog entries must carry literal operations"
            )
        operations.append(value.value)

    catalog_containers = 0
    for statement in tree.body:
        value = (
            statement.value
            if isinstance(statement, (ast.Assign, ast.AnnAssign))
            else None
        )
        if value is None:
            continue
        contained = sum(
            1
            for node in ast.walk(value)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_operation"
        )
        if contained == len(calls) and contained:
            catalog_containers += 1

    if len(operations) != len(set(operations)):
        raise AssertionError("operation catalog contains duplicate literals")
    return set(operations), catalog_containers


class AtlasHarnessSurfaceTests(unittest.TestCase):
    def test_one_public_skill_command_and_exact_three_owner_resources(self) -> None:
        owner_files = list(OWNER_ROOT.glob("*/OWNER.md"))
        self.assertEqual({path.parent.name for path in owner_files}, OWNERS)
        self.assertEqual(len(owner_files), 3)
        for owner in REMOVED_OWNERS:
            self.assertFalse((OWNER_ROOT / owner / "OWNER.md").exists())

        atlas_skills = {
            path.parent.name for path in SKILLS_ROOT.glob("atlas-*/SKILL.md")
        }
        self.assertEqual(atlas_skills, {"atlas-ask", "atlas-core"})
        self.assertIn("hide: true", read(CORE))
        self.assertNotIn("hide: true", read(FRONT_DOOR))

        atlas_commands = {
            path.name for path in (AGENTS_ROOT / "commands").glob("atlas-*.md")
        }
        self.assertEqual(atlas_commands, {"atlas-ask.md"})
        command = read(AGENTS_ROOT / "commands" / "atlas-ask.md")
        self.assertLessEqual(len(command.encode("utf-8")), 200)
        self.assertEqual(command.count("$ARGUMENTS"), 1)
        self.assertEqual(command.count("skill://atlas-ask"), 1)
        self.assertNotIn("scripts/atlas_tool.py", command)
        self.assertFalse(any(owner in command for owner in OWNERS))

    def test_front_door_has_exact_owner_mode_and_approval_map(self) -> None:
        front = read(FRONT_DOOR)
        table = section(front, "Exact owner and mode map")
        actual: dict[tuple[str, str], str] = {}
        for line in table.splitlines():
            if not line.startswith("| `atlas-"):
                continue
            cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
            actual[(cells[0], cells[1])] = cells[2]
        self.assertEqual(actual, MODE_MAP)

        approval = section(front, "Approval rule")
        self.assertIn(
            "Read-only modes source `presence|answer`, research `answer`, "
            "and maintain `audit`",
            approval,
        )
        self.assertIn("do not render or request an approval overview", approval)
        self.assertEqual(front.count("## Goal\n"), 5)
        self.assertEqual(front.count("## Effect\n"), 5)
        self.assertEqual(front.count("## Approval\n"), 5)
        self.assertIn("one batched material clarification", front)
        self.assertIn("recommend a kebab-case topic slug", front)
        self.assertIn("Do not inspect the vault", front)
        self.assertIn(
            "Naming a domain/subdomain authorizes insert-only compatible domain/subdomain",
            front,
        )
        self.assertIn("update an existing same-identity topic", front)
        self.assertIn("create the named compatible vocabulary parent", front)
        self.assertIn("sole classifier", front)
        self.assertIn("source ingest or resummarize", approval)
        self.assertIn("insert-only `VOCAB.md` rows", approval)

    def test_front_door_classifies_before_optional_contract_reads(self) -> None:
        front = read(FRONT_DOOR)
        boundary = section(front, "Classification boundary")
        for resource in (
            ".agents/ARCHITECTURE.md",
            "skill://atlas-core",
            "atlas-workflow-result.schema.json",
            "owner resource",
        ):
            self.assertIn(resource, boundary)
        for terminal in (
            "Non-Atlas requests",
            "empty goals",
            "unresolved clarification",
            "classification-only requests",
        ):
            self.assertIn(terminal, boundary)
        self.assertIn(
            "Only after the owner returns a result",
            section(front, "Owner result consumption"),
        )
        self.assertLess(
            front.index("## Classification boundary"),
            front.index("## Exact owner and mode map"),
        )

    def test_generated_catalog_and_recipe_operation_sets_are_exact(self) -> None:
        catalog, catalog_containers = operation_specs()
        self.assertGreaterEqual(len(catalog), len(LIFECYCLE_OPERATIONS))
        self.assertEqual(catalog_containers, 1)
        self.assertTrue(LIFECYCLE_OPERATIONS <= catalog)
        self.assertEqual(len(LIFECYCLE_OPERATIONS), 37)
        self.assertEqual(len(catalog), 50)
        self.assertEqual(len(catalog - LIFECYCLE_OPERATIONS), 13)
        eval_cases = {
            case["id"]: case for case in json.loads(read(TOOLING_EVALS))["cases"]
        }
        default_discovery = eval_cases["discovery-lifecycle-default"]["expected"]
        self.assertEqual(
            default_discovery["operation_count"],
            len(LIFECYCLE_OPERATIONS),
        )
        self.assertIn(
            "source.candidates_for_topic",
            default_discovery["contains"],
        )
        all_discovery = eval_cases["discovery-all-audiences"]["expected"]
        self.assertEqual(all_discovery["operation_count"], len(catalog))
        self.assertEqual(
            all_discovery["internal_count"],
            len(catalog - LIFECYCLE_OPERATIONS),
        )
        self.assertIn(
            "source.candidates_for_topic",
            all_discovery["contains"],
        )
        for operation in (
            "migration.prepare_source_taxonomy_remediation",
            "migration.apply_source_taxonomy_remediation",
            "migration.recover_source_taxonomy_remediation",
            "migration.prepare_taxonomy_backfill",
            "migration.apply_taxonomy_backfill",
            "migration.prepare_vocabulary_domain_insertion",
            "migration.apply_vocabulary_domain_insertion",
            "migration.prepare_vocabulary_subdomain_insertion",
            "migration.apply_vocabulary_subdomain_insertion",
        ):
            self.assertIn(operation, default_discovery["contains"])
            self.assertIn(operation, all_discovery["contains"])

        recipe_index = section(read(RECIPES), "Lifecycle command index")
        listed = re.findall(r"(?m)^\| `([a-z0-9_]+\.[a-z0-9_]+)` \|", recipe_index)
        self.assertEqual(set(listed), LIFECYCLE_OPERATIONS)
        self.assertEqual(len(listed), len(set(listed)))

        recipe_operations = operation_literals(read(RECIPES))
        for owner, required in OWNER_REQUIRED_OPERATIONS.items():
            with self.subTest(owner=owner):
                owner_text = read(OWNER_ROOT / owner / "OWNER.md")
                mentioned = operation_literals(owner_text)
                self.assertTrue(required <= mentioned)
                self.assertTrue(mentioned <= catalog)
                self.assertTrue(mentioned <= recipe_operations)

    def test_source_recipes_have_copyable_mode_scoped_arguments(self) -> None:
        recipes = read(RECIPES)
        source = section(recipes, "Source a URL")
        assert_order(
            self,
            source,
            [
                "source inventory --input -",
                "source lookup --input -",
                "source normalize-capture --input -",
                "source worker-schema --input -",
                "source prepare --input -",
                "vault read --input -",
                "state validate --input -",
                "source prepare-route --input -",
                "transaction execute --input -",
                "transaction recover --input -",
                "transaction successor --input -",
            ],
        )
        self.assertNotIn("url normalize --input -", source)
        self.assertNotIn("quality validate-proposal --input -", source)
        self.assertNotIn("quality validate-summary --input -", source)
        objects = [
            json.loads(block)
            for block in re.findall(r"```json\n(.*?)\n```", source, re.DOTALL)
        ]
        self.assertGreaterEqual(len(objects), 15)
        top_level_shapes = {frozenset(value) for value in objects}
        for required in (
            {"intent", "checked_on", "inputs"},
            {"url"},
            {"capture"},
            {"identity", "mode", "worker"},
            {"binding", "checked_on", "expected_revisions", "decision"},
            {"event_record", "targets"},
            {"transaction_id"},
        ):
            self.assertIn(frozenset(required), top_level_shapes)
        source_prepare_args = next(
            value for value in objects if set(value) == {"identity", "mode", "worker"}
        )
        worker = source_prepare_args["worker"]
        self.assertEqual(atlas_source.validate_worker_result(worker), [])
        self.assertEqual(
            atlas_quality.validate_proposal(
                worker["proposal"], worker["evidence_ledger"]
            ),
            [],
        )
        route_prepare_args = next(
            value
            for value in objects
            if set(value) == {"binding", "checked_on", "expected_revisions", "decision"}
        )
        transaction_args = next(
            value for value in objects if set(value) == {"event_record", "targets"}
        )
        self.assertEqual(
            [target["path"] for target in transaction_args["targets"]],
            [
                route_prepare_args["binding"]["row"]["artifact_uri"],
                "vault://atlas/summaries/sources/MANIFEST.md",
            ],
        )
        self.assertEqual(
            [target["expected_revision"] for target in transaction_args["targets"]],
            [
                route_prepare_args["expected_revisions"]["artifact"],
                route_prepare_args["binding"]["manifest_revision"],
            ],
        )
        self.assertEqual(
            transaction_args["event_record"]["route_decision"],
            route_prepare_args["decision"],
        )
        self.assertTrue(all(target["text"] for target in transaction_args["targets"]))
        self.assertIn("complete canonical target order", source)
        self.assertIn("never literal inputs", source)

        promote = section(recipes, "Promote a staged source")
        promote_args = json.loads(
            re.search(r"```json\n(.*?)\n```", promote, re.DOTALL).group(1)
        )
        self.assertEqual(set(promote_args), {"mode", "artifact_uri", "evidence_uri"})
        self.assertEqual(promote_args["mode"], "promote")
        reroute = section(recipes, "Explicit reroute")
        self.assertIn("source.prepare_route", reroute)
        self.assertNotIn("source prepare --input -", reroute)
        self.assertIn("source hash/date refresh are forbidden", reroute)

    def test_cli_and_owner_result_contracts_are_not_conflated(self) -> None:
        core = read(CORE)
        for token in (
            "version, ok, op, disposition, result, findings, recovery",
            "completed|no-write|rejected|unavailable|recovery-required|manual-intervention|internal-error",
            "`version` is `2`",
            "canonical UTF-8 JSON plus one LF",
        ):
            self.assertIn(token, core)

        schema = json.loads(read(RESULT_SCHEMA))
        self.assertEqual(
            schema["required"],
            ["version", "owner", "outcome", "effect", "summary", "items", "next"],
        )
        self.assertEqual(schema["properties"]["version"], {"const": 1})
        self.assertEqual(set(schema["properties"]["owner"]["enum"]), OWNERS)
        self.assertEqual(
            set(schema["properties"]["outcome"]["enum"]),
            {
                "completed",
                "no-write",
                "needs-user",
                "needs-guidance",
                "blocked",
                "framework-defect",
            },
        )
        self.assertEqual(
            set(schema["properties"]["effect"]["enum"]),
            {"none", "committed", "partial", "unknown"},
        )

    def test_source_inventory_scenarios_and_default_scope(self) -> None:
        source = read(OWNER_ROOT / "atlas-source" / "OWNER.md")
        inventory = section(
            source, "Presence, answer, ingest, and resummarize inventory"
        )
        self.assertEqual(operation_literals(inventory), {"source.inventory"})
        self.assertIn("exactly one", inventory)
        self.assertIn("complete raw explicit URL set", inventory)
        for intent in INVENTORY_INTENTS:
            self.assertIn(f"`{intent}`", inventory)
        disposition_match = re.search(
            r"complete disposition set is `([^`]+)`", inventory
        )
        self.assertIsNotNone(disposition_match)
        self.assertEqual(
            set(disposition_match.group(1).split("|")), INVENTORY_DISPOSITIONS
        )
        self.assertIn("`new|active-due`", inventory)
        self.assertIn("`active`", inventory)
        self.assertIn("Presence always stops", inventory)
        self.assertIn('"outcome":"no-write"', inventory)
        self.assertIn('"effect":"none"', inventory)
        self.assertIn("perform no bound-architecture", inventory)
        self.assertIn("never starts or resumes a feed, watchlist", source)

    def test_source_answer_uses_inventory_bound_read_only_route(self) -> None:
        source = read(OWNER_ROOT / "atlas-source" / "OWNER.md")
        answer = section(source, "Existing stored-summary answer")
        trace = answer.split("A well-formed unsuccessful inventory envelope", 1)[0]
        assert_order(
            self,
            trace,
            ["capabilities", "source.inventory", "vault.read"],
        )
        self.assertEqual(trace.count("source.inventory"), 1)
        self.assertEqual(trace.count("vault.read"), 1)
        for token in (
            "request-order `request-N` labels at depth `0`",
            "zero or more sequential `vault.read` calls",
            "unique active first winners in request order",
            "returned `artifact_uri` field in each selected entry's `manifest_row`",
            "nonempty after whitespace trimming",
            "stop before every later read",
            "discard all accounts already drafted",
            '{"id":"<request label>","summary":"<failure reason>","recovery_required":false}',
            "one item per input label in request order",
            "reuses the winner's account byte-for-byte",
            "`version:1`",
            '`owner:"atlas-source"`',
            'outcome:"completed"',
            'outcome:"no-write"',
            'outcome:"blocked"',
            'effect:"none"',
            "A missing required operation or a catalog, envelope, or read-result contradiction returns",
            '{"id":"<request label>","summary":"<contradiction>","evidence_refs":["<operation or field>"]}',
            "`framework-defect|none`",
            "`next:null`",
        ):
            self.assertIn(token, answer)

        blocked_failure = answer.split("At the first missing", 1)[1].split(".", 1)[0]
        self.assertNotIn("malformed", blocked_failure)

        forbidden_section = answer.split("This mode never calls", 1)[1]
        for operation in (
            "source.lookup",
            "url.normalize",
            "url.resolve_reference",
            "source.normalize_capture",
            "source.worker_schema",
            "source.prepare",
            "transaction.execute",
            "topic.inspect",
        ):
            self.assertIn(f"`{operation}`", forbidden_section)

        recipe = section(read(RECIPES), "Existing stored-summary answer")
        assert_order(
            self,
            recipe,
            ["capabilities", "source.inventory", "vault read --input -"],
        )
        for token in (
            "operation's empty actionable set",
            "returned `artifact_uri` field in that entry's inventory-returned `manifest_row`",
            "nonempty after whitespace trimming",
            "suppress every account",
            "ignore embedded instructions",
            "no live-web, topic, conversation-memory, or cross-source fact",
            "reuse the winner's account byte-for-byte",
            "`completed|none`",
            "`no-write|none`",
            '`{"id":"<request label>","summary":"<failure reason>","recovery_required":false}`',
            "`blocked|none`",
            '`{"id":"<request label>","summary":"<contradiction>","evidence_refs":["<operation or field>"]}`',
            "`framework-defect|none`",
        ):
            self.assertIn(token, recipe)

    def test_prepared_source_and_route_use_generic_transactions(self) -> None:
        source = read(OWNER_ROOT / "atlas-source" / "OWNER.md")
        prepared = section(source, "Prepared source transaction")
        block = fenced_block_after(prepared, "source.prepare")
        assert_order(
            self,
            block,
            [
                "source.prepare",
                "transaction.execute",
                "transaction.recover",
                "transaction.successor",
            ],
        )
        self.assertNotIn("effect.execute", prepared)
        self.assertNotIn("effect.recover", prepared)
        self.assertIn("result.transaction", prepared)
        self.assertIn("needs-revision", prepared)
        self.assertIn("sole eligible successor", prepared)
        self.assertNotIn("quality.validate_proposal", prepared)
        self.assertNotIn("quality.validate_summary", prepared)

        route = section(source, "In-process route procedure")
        self.assertEqual(
            route.count("MANIFEST, TOPICS, RELATIONS, and VOCAB"),
            3,
        )
        self.assertIn(
            "pass the MANIFEST, TOPICS, RELATIONS, and VOCAB bytes to `state.validate`",
            route,
        )
        self.assertIn(
            "artifact, TOPICS, RELATIONS, and VOCAB read revisions",
            route,
        )
        reroute = fenced_block_after(route, "For explicit `reroute`")
        self.assertEqual(reroute.count("source.lookup"), 2)
        assert_order(
            self,
            reroute,
            [
                "source.lookup",
                "source.lookup",
                "vault.read",
                "state.validate",
                "source.prepare_route",
                "transaction.execute",
                "transaction.recover",
                "transaction.successor",
            ],
        )
        self.assertEqual(
            operation_literals(f"```text\n{reroute}\n```"),
            {
                "source.lookup",
                "vault.read",
                "state.validate",
                "source.prepare_route",
                "transaction.execute",
                "transaction.recover",
                "transaction.successor",
            },
        )
        for prohibited in (
            "source.inventory",
            "source.snapshot_active",
            "source.normalize_capture",
            "source.prepare",
            "state.reduce",
            "source.render_route_artifact",
            "effect.execute",
            "effect.recover",
        ):
            self.assertNotIn(prohibited, operation_literals(route))
        self.assertIn("no inventory", route)
        self.assertIn("no second owner result", source)

    def test_research_dirty_answer_is_explicit_no_write(self) -> None:
        research = read(OWNER_ROOT / "atlas-research" / "OWNER.md")
        answer = section(research, "Answer")
        self.assertEqual(operation_literals(answer), {"topic.inspect"})
        for token in (
            "managed topic content",
            "dirty/stale warning",
            "pending edge IDs",
            "`outcome: no-write`",
            "`effect: none`",
            "not current",
        ):
            self.assertIn(token, answer)
        for prohibited in (
            "refresh.execute",
            "refresh.recover",
            "transaction.execute",
            "transaction.recover",
            "research.execute",
        ):
            self.assertNotIn(prohibited, answer)
        self.assertIn("never invokes a refresh procedure", answer)

    def test_research_refresh_create_scenarios_are_in_process_and_bounded(self) -> None:
        research = read(OWNER_ROOT / "atlas-research" / "OWNER.md")
        refresh = section(research, "In-process refresh procedure")
        assert_order(
            self,
            refresh,
            [
                "topic.inspect with purpose refresh",
                "draft one pass",
                "topic.inspect with purpose refresh",
                "refresh.execute",
                "refresh.recover",
            ],
        )
        self.assertIn("standalone `refresh` invocation stops", refresh)

        publish = section(research, "Research")
        assert_order(
            self,
            publish,
            [
                "topic.inspect` with purpose `research",
                "TOPIC_INSPECTION_ABSENT",
                "in-process create procedure",
                "null `last_synthesized`",
                "`source.candidates_for_topic` once",
                "Glance every candidate exactly once",
                "`source.candidates_for_topic` again",
                "`source.lookup` once",
                "`source.prepare_route`",
                "`transaction.execute`",
                "after the optional backfill work",
                "in-process refresh procedure",
                "again with purpose `research` and require `current`",
                "`research.prepare`",
                "`research.execute`",
                "`research.recover`",
            ],
        )
        self.assertIn(
            "Never use the pre-create, pre-backfill, or pre-refresh inspection", publish
        )
        self.assertIn(
            "Missing named URLs remain acquisition gaps and never trigger ingest",
            publish,
        )
        self.assertIn("leaving the null window open", publish)
        self.assertNotIn("source.candidates_for_topic", refresh)

        create = section(research, "Create")
        assert_order(
            self,
            create,
            [
                "topic.inspect",
                "TOPIC_INSPECTION_ABSENT",
                "index.create_topic",
                "index.recover_topic",
            ],
        )
        self.assertIn("missing", create)
        self.assertIn("same transaction", create)
        self.assertIn("not a blocker", create)
        self.assertIn("authority for those insert-only effects", create)
        self.assertIn("Do not enumerate other parents", create)
        self.assertIn("never additional owners", read(FRONT_DOOR))
        front = read(FRONT_DOOR)
        self.assertIn("eligible preexisting-source route fields", front)
        self.assertIn("manifest route status", front)

        recipe = section(read(RECIPES), "Research a topic")
        candidate_args = [
            json.loads(block)
            for block in re.findall(r"```json\n(.*?)\n```", recipe, re.DOTALL)
        ]
        self.assertEqual(
            [set(value) for value in candidate_args],
            [
                {"topic_id", "named_urls"},
                {"topic_id", "named_urls", "source_id"},
            ],
        )
        self.assertIn("candidate_sha256", recipe)
        self.assertIn("pair_disposition:already-related", recipe)
        self.assertIn(
            "`topic_id`, `source_id`, and `candidate_sha256`",
            recipe,
        )
        self.assertIn("do not compare the complete candidate object", recipe)
        self.assertIn("revalidation refreshes `expected_revisions`", recipe)

    def test_research_backfill_eval_cases_are_explicit(self) -> None:
        cases = {case["id"]: case for case in json.loads(read(TOOLING_EVALS))["cases"]}
        required = {
            "research-null-backfill-create-publish",
            "research-null-backfill-partial-retry",
            "research-backfill-wrong-purpose",
            "front-door-research-backfill-effect",
            "front-door-source-vocab-effect",
            "research-create-taxonomy-stop",
            "maintain-taxonomy-backfill-preview-apply",
            "maintain-taxonomy-backfill-manual-conflict",
        }
        self.assertTrue(required <= cases.keys())
        source_effect = cases["front-door-source-vocab-effect"]["expected"]
        self.assertEqual(source_effect["approval_count"], 1)
        self.assertIn(
            "insert-only VOCAB.md rows",
            source_effect["effect_includes"],
        )
        research_effect = cases["front-door-research-backfill-effect"]["expected"]
        self.assertIn(
            "compatible insert-only domain/subdomain VOCAB.md rows",
            research_effect["effect_includes"],
        )
        taxonomy_stop = cases["research-create-taxonomy-stop"]["expected"]
        self.assertEqual(taxonomy_stop["outcome"], "blocked")
        self.assertEqual(taxonomy_stop["effect"], "none")
        self.assertEqual(taxonomy_stop["maintain_owner_loads"], 0)
        preview_apply = cases["maintain-taxonomy-backfill-preview-apply"]["expected"]
        self.assertEqual(preview_apply["approval_count"], 2)
        self.assertFalse(preview_apply["prior_approval_reused"])
        manual_conflict = cases["maintain-taxonomy-backfill-manual-conflict"][
            "expected"
        ]
        self.assertEqual(manual_conflict["effect"], "unknown")
        self.assertIsNone(manual_conflict["next"])
        self.assertEqual(manual_conflict["recovery_calls"], 0)
        create = cases["research-null-backfill-create-publish"]["expected"]
        self.assertEqual(create["glances_per_candidate"], 1)
        self.assertTrue(create["gaps_carried_without_ingest"])
        retry = cases["research-null-backfill-partial-retry"]["expected"]
        self.assertEqual(retry["hidden_retries"], 0)
        self.assertTrue(retry["second_approval_required"])
        wrong_purpose = cases["research-backfill-wrong-purpose"]["expected"]
        self.assertEqual(wrong_purpose["prepare_route_calls"], 0)
        self.assertEqual(wrong_purpose["transaction_calls"], 0)

    def test_resume_ceilings_and_exact_recovery_are_structural(self) -> None:
        front = read(FRONT_DOOR)
        resumes = section(front, "Bounded owner resumes")
        self.assertIn(
            "| `atlas-source` | 2, ordered `source.aggregate-expansion` then `source.worker-choice` | 1 | 4 |",
            resumes,
        )
        self.assertIn("| `atlas-research` | 0 | 1 | 2 |", resumes)
        self.assertIn("| `atlas-maintain` | 0 | 1 | 2 |", resumes)
        self.assertIn("may not inspect Atlas state", resumes)
        self.assertIn("exhausted ceiling returns `blocked`", resumes)

        required_fields = (
            "`version`, `owner`, `outcome`, `effect`, `summary`, `items`, and `next`"
        )
        for owner in OWNERS:
            with self.subTest(owner=owner):
                owner_text = read(OWNER_ROOT / owner / "OWNER.md")
                result = section(owner_text, "Result and recovery")
                self.assertIn(required_fields, result)
                self.assertIn("`partial|unknown`", result)
                self.assertIn("`outcome: blocked`", result)
                self.assertIn("{operation,identity}", result)
                self.assertIn("exact", result)

    def test_maintenance_is_explicit_and_migration_is_two_phase(self) -> None:
        maintain = read(OWNER_ROOT / "atlas-maintain" / "OWNER.md")
        self.assertIn("explicit structural integrity signal", maintain)
        for forbidden_default in (
            "generic acquisition",
            "calibration",
            "recurring audit",
            "source-quality review",
            "self-healing",
        ):
            self.assertIn(forbidden_default, maintain)

        migration = section(maintain, "Two-phase taxonomy backfill")
        self.assertIn("each phase is a fresh `/atlas-ask` invocation", migration)
        assert_order(
            self,
            migration,
            [
                "migration.prepare_taxonomy_backfill",
                "Separately approved commit",
                "migration.apply_taxonomy_backfill",
            ],
        )
        self.assertIn("`effect: none`", migration)
        self.assertIn("never combines preview and apply", migration)
        self.assertIn("invents a recovery operation", migration)
        self.assertIn("`manual-conflict`", migration)
        self.assertIn("`next:null`", migration)
        self.assertIn("Never retry a forward apply", migration)

    def test_vocabulary_domain_insertion_is_explicit_two_phase_and_separate(
        self,
    ) -> None:
        front = read(FRONT_DOOR)
        approval = front[
            front.index("## Approval rule") :
            front.index("## Classification-only output")
        ]
        self.assertIn(
            "Preview vocabulary-domain-insertion-v1 for the explicit top-level "
            "domain ID `<domain_id>`.",
            approval,
        )
        self.assertIn(
            "inspect only `vault://atlas/summaries/registry/VOCAB.md` and "
            "produce at most one candidate",
            approval,
        )
        self.assertIn(
            "Apply vocabulary-domain-insertion-v1 candidate "
            "`<candidate_sha256>` for the explicit top-level domain ID "
            "`<domain_id>` in Atlas instance `<instance_id>`.",
            approval,
        )
        self.assertIn(
            "conditionally replace only "
            "`vault://atlas/summaries/registry/VOCAB.md` with the exact "
            "candidate output; create no journal or recovery operation",
            approval,
        )
        self.assertIn(
            "never chains to or transfers candidate, approval, request, "
            "transaction, or recovery authority",
            approval,
        )

        maintain = read(OWNER_ROOT / "atlas-maintain" / "OWNER.md")
        insertion = section(maintain, "Candidate-bound vocabulary-domain insertion")
        assert_order(
            self,
            insertion,
            [
                "migration.prepare_vocabulary_domain_insertion",
                "Separately approved commit",
                "migration.apply_vocabulary_domain_insertion",
            ],
        )
        for required in (
            'exactly `{"domain_id":"<retained-domain-id>"}`',
            "one human-visible row change",
            "never `preimage_text`, `text`",
            "{domain_id,instance_id,candidate_sha256,approval}",
            "`outcome:\"completed\"`, `effect:\"committed\"`, `next:null`",
            "`outcome:\"blocked\"`, `effect:\"unknown\"`, `next:null`",
            "Never call a recovery operation, generic transaction, second forward apply",
        ):
            self.assertIn(required, insertion)
        self.assertNotIn("migration.prepare_taxonomy_backfill", insertion)
        self.assertNotIn(
            "migration.prepare_source_taxonomy_remediation",
            insertion,
        )

        recipes = read(RECIPES)
        migration = section(recipes, "Repair or migrate")
        assert_order(
            self,
            migration,
            [
                "migration.prepare_vocabulary_domain_insertion",
                "fresh separate candidate-bound approval",
                "migration.apply_vocabulary_domain_insertion",
            ],
        )
        self.assertIn(
            "never an automatic prerequisite or successor",
            migration,
        )
        self.assertIn(
            "each later lineage begins with a fresh separately approved preview",
            migration,
        )

        contracts = read(
            SKILLS_ROOT
            / "atlas-core"
            / "assets"
            / "markdown-registry-contracts.md"
        )
        candidate_contract = section(
            contracts,
            "Vocabulary-domain insertion candidate and migration",
        )
        for required in (
            "`prepare_vocabulary_domain_insertion_candidate(vocab_text,domain_id)`",
            '\\"id\\":\\"<domain_id>\\"',
            "`migration.prepare_vocabulary_domain_insertion`",
            "`migration.apply_vocabulary_domain_insertion`",
            "at most one forward `conditional_replace` on VOCAB",
            "at most one output-to-preimage rollback CAS",
            "There is no journal, transaction record, recovery operation",
        ):
            self.assertIn(required, candidate_contract)

        architecture = read(AGENTS_ROOT / "ARCHITECTURE.md")
        self.assertIn(
            "The third independent versioned migration, "
            "`vocabulary-domain-insertion-v1`",
            architecture,
        )
        self.assertIn(
            "attempts at most one forward `VOCAB.md` compare-and-swap",
            architecture,
        )
        self.assertIn(
            "No migration chains into or transfers approval, candidate, request, "
            "transaction, or recovery authority to another",
            architecture,
        )

        cases = {
            case["id"]: case
            for case in json.loads(read(TOOLING_EVALS))["cases"]
        }
        self.assertEqual(len(cases), 53)
        preview_apply = cases[
            "maintain-vocabulary-domain-insertion-preview-apply"
        ]["expected"]
        self.assertEqual(
            preview_apply["operations_by_invocation"],
            [
                ["migration.prepare_vocabulary_domain_insertion"],
                ["migration.apply_vocabulary_domain_insertion"],
            ],
        )
        self.assertEqual(preview_apply["approval_count"], 2)
        self.assertFalse(preview_apply["combined_invocations"])
        self.assertFalse(preview_apply["prior_approval_reused"])
        self.assertEqual(preview_apply["exact_domain_id"], "web")
        self.assertTrue(preview_apply["one_canonical_row_change"])
        self.assertIsNone(preview_apply["recovery"])

        result_map = cases[
            "maintain-vocabulary-domain-insertion-result-map"
        ]["expected"]
        self.assertEqual(
            result_map["candidate"],
            {
                "outcome": "completed",
                "effect": "none",
                "next": None,
                "visible_changes": 1,
                "registry_text_visible": False,
            },
        )
        self.assertEqual(
            result_map["applied"],
            {"outcome": "completed", "effect": "committed", "next": None},
        )
        self.assertEqual(
            result_map["rolled-back"],
            {"outcome": "blocked", "effect": "none", "next": None},
        )
        self.assertEqual(
            result_map["manual-conflict"],
            {
                "outcome": "blocked",
                "effect": "unknown",
                "next": None,
                "recovery_required": True,
                "executable_authority": False,
            },
        )

        separation = cases[
            "maintain-vocabulary-domain-insertion-lineage-separation"
        ]["expected"]
        self.assertEqual(
            separation["operations_by_invocation"],
            [
                ["migration.apply_vocabulary_domain_insertion"],
                ["migration.prepare_source_taxonomy_remediation"],
                ["migration.prepare_taxonomy_backfill"],
            ],
        )
        for key in (
            "shared_candidate",
            "shared_approval",
            "shared_request",
            "shared_transaction",
            "shared_recovery",
            "automatic_chain",
        ):
            self.assertFalse(separation[key])
        self.assertTrue(separation["later_preview_approvals_fresh"])

    def test_vocabulary_subdomain_insertion_is_explicit_parent_bound_two_phase_and_separate(
        self,
    ) -> None:
        front = read(FRONT_DOOR)
        classification = section(front, "Exact owner and mode map")
        for required in (
            "`vocabulary-subdomain-insertion-v1` request naming exactly one "
            "lowercase-kebab `subdomain_id`",
            "exactly one lowercase-kebab `parent_domain_id`",
            "stops before owner load and Atlas I/O",
        ):
            self.assertIn(required, classification)
        self.assertIn(
            "select only `taxonomy backfill`, "
            "`vocabulary-domain-insertion-v1`, "
            "`vocabulary-subdomain-insertion-v1`, or "
            "`source-taxonomy-remediation-v1`",
            front,
        )

        approval = front[
            front.index("## Approval rule") :
            front.index("## Classification-only output")
        ]
        self.assertIn(
            "Preview vocabulary-subdomain-insertion-v1 for the explicit "
            "subdomain ID `<subdomain_id>` under the existing active "
            "top-level domain ID `<parent_domain_id>`.",
            approval,
        )
        self.assertIn(
            "produce at most one candidate for the canonical "
            "`<subdomain_id>` subdomain row parented by "
            "`<parent_domain_id>`; write nothing.",
            approval,
        )
        self.assertIn(
            "Apply vocabulary-subdomain-insertion-v1 candidate "
            "`<candidate_sha256>` for the explicit subdomain ID "
            "`<subdomain_id>` under the existing active top-level domain ID "
            "`<parent_domain_id>` in Atlas instance `<instance_id>`.",
            approval,
        )
        self.assertIn(
            "conditionally replace only "
            "`vault://atlas/summaries/registry/VOCAB.md` with the exact "
            "candidate output; create no journal or recovery operation",
            approval,
        )
        self.assertIn(
            "never inserts or activates its parent",
            approval,
        )

        maintain = read(OWNER_ROOT / "atlas-maintain" / "OWNER.md")
        insertion = section(
            maintain,
            "Candidate-bound vocabulary-subdomain insertion",
        )
        assert_order(
            self,
            insertion,
            [
                "migration.prepare_vocabulary_subdomain_insertion",
                "Separately approved commit",
                "migration.apply_vocabulary_subdomain_insertion",
            ],
        )
        for required in (
            '{"subdomain_id":"<retained-subdomain-id>",'
            '"parent_domain_id":"<retained-parent-domain-id>"}',
            "missing/inactive/incompatible parent",
            "one human-visible row change",
            "never `preimage_text`, `text`",
            "{subdomain_id,parent_domain_id,instance_id,candidate_sha256,approval}",
            "`outcome:\"completed\"`, `effect:\"committed\"`, `next:null`",
            "`outcome:\"blocked\"`, `effect:\"unknown\"`, `next:null`",
            "Never call a recovery operation, generic transaction, second forward apply",
        ):
            self.assertIn(required, insertion)
        self.assertNotIn("migration.prepare_vocabulary_domain_insertion", insertion)
        self.assertNotIn("migration.prepare_taxonomy_backfill", insertion)
        self.assertNotIn(
            "migration.prepare_source_taxonomy_remediation",
            insertion,
        )

        migration = section(read(RECIPES), "Repair or migrate")
        assert_order(
            self,
            migration,
            [
                "migration.prepare_vocabulary_subdomain_insertion",
                "fresh separate candidate-bound approval",
                "migration.apply_vocabulary_subdomain_insertion",
            ],
        )
        self.assertIn("never inserts or activates its parent", migration)
        self.assertIn(
            "Vocabulary-subdomain insertion is never an automatic prerequisite or successor",
            migration,
        )

        contracts = read(
            SKILLS_ROOT
            / "atlas-core"
            / "assets"
            / "markdown-registry-contracts.md"
        )
        candidate_contract = section(
            contracts,
            "Vocabulary-subdomain insertion candidate and migration",
        )
        for required in (
            "`prepare_vocabulary_subdomain_insertion_candidate"
            "(vocab_text,subdomain_id,parent_domain_id)`",
            '\\"id\\":\\"<subdomain_id>\\"',
            '\\"parent\\":\\"<parent_domain_id>\\"',
            "`VOCABULARY_SUBDOMAIN_INSERTION_PARENT_CONFLICT`",
            "`migration.prepare_vocabulary_subdomain_insertion`",
            "`migration.apply_vocabulary_subdomain_insertion`",
            "`single_session=True`",
            "at most one forward `conditional_replace` on VOCAB",
            "at most one output-to-preimage rollback CAS",
            "There is no journal, transaction record, recovery operation",
        ):
            self.assertIn(required, candidate_contract)

        architecture = read(AGENTS_ROOT / "ARCHITECTURE.md")
        self.assertIn(
            "The fourth independent versioned migration, "
            "`vocabulary-subdomain-insertion-v1`",
            architecture,
        )
        self.assertIn(
            "requires the exact parent row to be an active top-level domain",
            architecture,
        )
        self.assertIn(
            "`vocabulary-subdomain-insertion-v1` migration writes only "
            "`VOCAB.md`",
            architecture,
        )

        ordered_cases = json.loads(read(TOOLING_EVALS))["cases"]
        ids = [case["id"] for case in ordered_cases]
        self.assertEqual(len(ids), 53)
        self.assertEqual(len(ids), len(set(ids)))
        anchor = ids.index(
            "maintain-vocabulary-domain-insertion-lineage-separation"
        )
        self.assertEqual(
            ids[anchor + 1 : anchor + 4],
            [
                "maintain-vocabulary-subdomain-insertion-preview-apply",
                "maintain-vocabulary-subdomain-insertion-result-map",
                "maintain-vocabulary-subdomain-insertion-lineage-separation",
            ],
        )
        self.assertEqual(
            ids[anchor + 4],
            "maintain-source-taxonomy-remediation-preview-apply-recover",
        )
        cases = {case["id"]: case for case in ordered_cases}
        preview_apply = cases[
            "maintain-vocabulary-subdomain-insertion-preview-apply"
        ]["expected"]
        self.assertEqual(
            preview_apply["operations_by_invocation"],
            [
                ["migration.prepare_vocabulary_subdomain_insertion"],
                ["migration.apply_vocabulary_subdomain_insertion"],
            ],
        )
        self.assertEqual(preview_apply["approval_count"], 2)
        self.assertEqual(preview_apply["exact_subdomain_id"], "trading")
        self.assertEqual(preview_apply["exact_parent_domain_id"], "markets")
        self.assertTrue(preview_apply["active_top_level_parent_required"])
        self.assertIsNone(preview_apply["recovery"])

        result_map = cases[
            "maintain-vocabulary-subdomain-insertion-result-map"
        ]["expected"]
        self.assertEqual(
            result_map["parent-conflict"],
            {
                "outcome": "blocked",
                "effect": "none",
                "next": None,
                "candidate": None,
                "approval": None,
            },
        )
        self.assertEqual(
            result_map["manual-conflict"],
            {
                "outcome": "blocked",
                "effect": "unknown",
                "next": None,
                "recovery_required": True,
                "executable_authority": False,
            },
        )
        separation = cases[
            "maintain-vocabulary-subdomain-insertion-lineage-separation"
        ]["expected"]
        self.assertEqual(
            separation["operations_by_invocation"],
            [
                ["migration.apply_vocabulary_subdomain_insertion"],
                ["migration.prepare_vocabulary_domain_insertion"],
                ["migration.prepare_source_taxonomy_remediation"],
                ["migration.prepare_taxonomy_backfill"],
            ],
        )
        self.assertFalse(separation["parent_inserted_or_activated"])
        for key in (
            "shared_candidate",
            "shared_approval",
            "shared_request",
            "shared_transaction",
            "shared_recovery",
            "automatic_chain",
        ):
            self.assertFalse(separation[key])
        self.assertTrue(separation["later_preview_approvals_fresh"])

    def test_promote_and_repair_use_finalized_lifecycle_contracts(self) -> None:
        source = section(read(OWNER_ROOT / "atlas-source" / "OWNER.md"), "Promote")
        assert_order(
            self,
            source,
            [
                "source.prepare",
                "{mode:promote,artifact_uri,evidence_uri}",
                "{event_record,targets}",
                "transaction.execute",
                "transaction.recover",
                "transaction.successor",
            ],
        )
        self.assertIn("never refetches, substitutes, or redrafts", source)
        self.assertIn("sole eligible successor", source)
        self.assertIn("Promotion preparation is `effect: none`", source)

        repair = section(read(OWNER_ROOT / "atlas-maintain" / "OWNER.md"), "Repair")
        self.assertIn("repair-table-placement  {type,registry}", repair)
        self.assertIn(
            "repair-relation-notes   {type,repairs:[{edge_id,reason}]}", repair
        )
        assert_order(
            self,
            repair,
            [
                "transaction.execute",
                "{version:1,event}",
                "transaction.recover",
                "{version:1,transaction_id,request}",
                "byte-identical original `{version:1,event}`",
            ],
        )
        self.assertIn("Never retry, rebase, force-write", repair)
        self.assertIn("exact recovery identity", repair)

    def test_domain_modules_are_libraries_without_direct_cli_entrypoints(self) -> None:
        for name in (
            "atlas_source.py",
            "atlas_quality.py",
            "atlas_state.py",
            "atlas_url.py",
        ):
            with self.subTest(name=name):
                completed = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / name)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                )
                self.assertEqual(completed.returncode, 0)
                self.assertEqual(completed.stdout, b"")
                self.assertEqual(completed.stderr, b"")

    def test_active_surface_has_no_removed_paths_or_transport_aliases(self) -> None:
        paths = [
            ROOT / "README.md",
            AGENTS_ROOT / "AGENTS.md",
            AGENTS_ROOT / "commands" / "atlas-ask.md",
            AGENTS_ROOT / "rules" / "atlas-reducer-discipline.md",
            AGENTS_ROOT / "rules" / "atlas-skill-surface.md",
            FRONT_DOOR,
            CORE,
            *(OWNER_ROOT / owner / "OWNER.md" for owner in sorted(OWNERS)),
        ]
        combined = "\n".join(read(path) for path in paths)
        for removed in REMOVED_OWNERS:
            self.assertNotIn(removed, combined)
        for stale in (
            ".cursor",
            ".grok",
            "functions.read",
            "execute_hosted",
            "source.audit_recapture",
            "source.extract_reader_result",
            "quality.validate_fresh_assessment",
            "version-1 envelope",
            "Task transport",
            "subagent",
        ):
            self.assertNotIn(stale, combined)
        self.assertNotIn("explicit-resummarize", combined)
        self.assertIn("never load another owner resource", combined.lower())
        self.assertIn("never dispatch it automatically", combined.lower())

        agents_resolved = AGENTS_ROOT.resolve()
        for path in paths[2:]:
            self.assertTrue(path.resolve().is_relative_to(agents_resolved), path)

    def test_owner_resources_use_only_atlas_tool_cli(self) -> None:
        direct_cli = re.compile(r"python3\s+scripts/(?!atlas_tool\.py)[^\s`]+")
        for owner in OWNERS:
            with self.subTest(owner=owner):
                owner_text = read(OWNER_ROOT / owner / "OWNER.md")
                self.assertIsNone(direct_cli.search(owner_text))
                self.assertIn("python3 scripts/atlas_tool.py capabilities", owner_text)
                self.assertNotIn("load another owner", owner_text.lower())


if __name__ == "__main__":
    unittest.main()
