from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS_ROOT = (ROOT / ".agents").resolve()


class AtlasHarnessSurfaceTests(unittest.TestCase):
    def assert_resolves_under_agents(self, path: Path) -> None:
        self.assertTrue(path.is_symlink(), f"expected symlink: {path}")
        resolved = path.resolve(strict=True)
        self.assertTrue(
            resolved.is_relative_to(AGENTS_ROOT),
            f"{path} resolves outside canonical .agents: {resolved}",
        )

    def test_canonical_repo_local_aliases_resolve_under_agents(self) -> None:
        for relative in (
            "AGENTS.md",
            ".cursor/skills",
            ".cursor/rules",
        ):
            with self.subTest(path=relative):
                self.assert_resolves_under_agents(ROOT / relative)

    def test_single_public_atlas_behavior_pair_and_owner_resources(self) -> None:
        skills_root = ROOT / ".agents" / "skills"
        command_root = ROOT / ".agents" / "commands"
        public_skill = skills_root / "atlas-ask" / "SKILL.md"
        core_skill = skills_root / "atlas-core" / "SKILL.md"
        self.assertTrue(public_skill.is_file())
        self.assertTrue(core_skill.is_file())

        public_skills = sorted(
            path.parent.name
            for path in skills_root.glob("*/SKILL.md")
            if path.parent.name != "atlas-core"
        )
        self.assertEqual(public_skills, ["atlas-ask"])
        self.assertEqual(
            sorted(path.stem for path in command_root.glob("*.md")),
            ["atlas-ask"],
        )

        command_text = (command_root / "atlas-ask.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(command_text.splitlines()), 12)
        self.assertIn("skill://atlas-ask", command_text)
        self.assertIn("$ARGUMENTS", command_text)
        self.assertNotIn("## Workflow", command_text)
        self.assertNotIn("scripts/atlas_tool.py", command_text)

        owner_root = skills_root / "atlas-ask" / "owners"
        expected_owner_ids = {
            "atlas-source",
            "atlas-acquire",
            "atlas-route",
            "atlas-research",
            "atlas-refresh",
            "atlas-answer",
            "atlas-audit",
            "atlas-index",
            "atlas-migrate",
        }
        owner_paths = sorted(owner_root.glob("*/OWNER.md"))
        self.assertEqual(
            {path.parent.name for path in owner_paths}, expected_owner_ids
        )
        self.assertEqual(len(owner_paths), 9)
        self.assertEqual(list(owner_root.rglob("SKILL.md")), [])
        self.assertEqual(
            [
                path.parent.name
                for path in skills_root.glob("*/SKILL.md")
                if path.parent.name.startswith("atlas-")
                and path.parent.name not in {"atlas-ask", "atlas-core"}
            ],
            [],
        )
        for path in owner_paths:
            with self.subTest(owner=path.parent.name):
                text = path.read_text(encoding="utf-8")
                self.assertFalse(text.startswith("---\n"))
                self.assertIn("## Qualified invocation", text)
                self.assertIn("The selected Workflow Owner receives a live `/atlas-ask` Task", text)
                self.assertIn("Any other load performs no further read", text)
                self.assertIn("Redirect: invoke /atlas-ask.", text)
                self.assertIn("one outer `atlas-workflow-result.schema.json` result", text)

        core_text = core_skill.read_text(encoding="utf-8")
        self.assertIn("hide: true", core_text)
        self.assertIn("disableModelInvocation: true", core_text)
        self.assertIn("Direct invocation is never a user workflow", core_text)
        self.assertIn("redirect to `/atlas-ask`", core_text)

    def test_reference_scripts_are_repo_local_and_dependency_free(self) -> None:
        allowed_by_script = {
            "atlas_state.py": {"atlas_url"},
            "atlas_quality.py": set(),
            "atlas_url.py": set(),
            # atlas_source delegates generic provenance/application/recovery to
            # atlas_transaction while retaining source projection ownership.
            "atlas_source.py": {
                "atlas_url",
                "atlas_state",
                "atlas_quality",
                "atlas_transaction",
            },
            "atlas_transaction.py": set(),
            "atlas_index.py": {"atlas_state"},
            "atlas_connector.py": set(),
            "atlas_discovery.py": {"atlas_url"},
            "atlas_tool.py": {
                "atlas_connector",
                "atlas_discovery",
                "atlas_index",
                "atlas_quality",
                "atlas_source",
                "atlas_state",
                "atlas_transaction",
                "atlas_url",
            },
        }
        for name, allowed_local in allowed_by_script.items():
            path = ROOT / "scripts" / name
            self.assertTrue(path.is_file(), f"missing reference script: {path}")
            self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = {
                node.names[0].name.split(".", 1)[0]
                if isinstance(node, ast.Import)
                else (node.module or "").split(".", 1)[0]
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
            }
            external = (
                imported - set(sys.stdlib_module_names) - allowed_local - {"__future__"}
            )
            self.assertEqual(
                external, set(), f"{name} has external imports: {sorted(external)}"
            )

    def test_atlas_ask_overview_precedes_capability_and_task_dispatch(self) -> None:
        path = ROOT / ".agents" / "skills" / "atlas-ask" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        goal = text.index("Goal:")
        next_action = text.index("Next:", goal)
        effect = text.index("Effect:", next_action)
        retry = text.index("Retry:", effect)
        approval = text.index("Approve this Atlas route?", retry)
        capability = text.index("After approval, live-verify", approval)
        task = text.index("Send exactly the schema-owned `dispatch-input`", capability)

        self.assertLess(goal, next_action)
        self.assertLess(next_action, effect)
        self.assertLess(effect, retry)
        self.assertLess(retry, approval)
        self.assertLess(approval, capability)
        self.assertLess(capability, task)

    def test_atlas_ask_binds_unchanged_request_and_logical_boundary(self) -> None:
        text = (
            ROOT / ".agents" / "skills" / "atlas-ask" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("unchanged original request", text)
        self.assertIn("retained pre-route `material_answers`", text)
        self.assertIn("maximum logical architecture write boundary", text)
        self.assertIn("without Atlas I/O", text)
        self.assertIn("Approval is conversational dispatch authority", text)
        self.assertIn("never sent to the Workflow Owner", text)
        for forbidden_operation in (
            "scripts/atlas_tool.py",
            "vault://atlas/",
            "source.inventory",
            "state.reduce",
            "transaction.execute",
            "refresh.execute",
        ):
            self.assertNotIn(forbidden_operation, text)

    def test_owner_guards_chains_and_outer_result_are_bounded(self) -> None:
        skills_root = ROOT / ".agents" / "skills"
        front_door = (skills_root / "atlas-ask" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for chain in (
            "atlas-acquire` → `atlas-source",
            "atlas-source` → `atlas-route",
            "atlas-research` → `atlas-acquire",
            "atlas-research` → `atlas-refresh",
        ):
            self.assertIn(chain, front_door)
        self.assertIn("selected owner wraps exactly once", front_door.lower())
        self.assertIn("only from the retained handle", front_door.lower())
        self.assertIn("atlas-workflow-result.schema.json", front_door)
        self.assertIn("partial|unknown effect → blocked", front_door)
        self.assertIn("source.aggregate-expansion", front_door)
        self.assertIn("source.worker-choice", front_door)
        self.assertIn("every prior key", front_door)
        self.assertIn("Maximum `owner_turn`", front_door)
        self.assertIn("source semantic worker correction", front_door.lower())
        self.assertIn("owner-local", front_door.lower())
        source_text = (
            skills_root / "atlas-ask" / "owners" / "atlas-source" / "OWNER.md"
        ).read_text(encoding="utf-8")
        self.assertIn("one synchronous same-worker message/reply", source_text)
        self.assertIn("entire returned reply body", source_text)
        self.assertIn("complete-wholesale", source_text)

    def test_active_guidance_has_no_removed_public_paths(self) -> None:
        roots = [
            ROOT / ".agents" / "AGENTS.md",
            ROOT / ".agents" / "rules",
            ROOT / ".agents" / "skills" / "atlas-ask" / "SKILL.md",
            ROOT / ".agents" / "skills" / "atlas-core" / "SKILL.md",
            ROOT / ".agents" / "commands",
            ROOT / "README.md",
            ROOT / "scaffold",
        ]
        legacy_token = (
            r"(?:atlas-(?:source|acquire|route|research|refresh|answer|audit|index|migrate)|atlas)"
            r"(?!-[A-Za-z0-9])"
        )
        legacy = re.compile(
            rf"`/{legacy_token}`|(?<![\w:/-])/{legacy_token}(?![\w-])"
        )
        internal_owner_uri = re.compile(
            r"skill://atlas-ask/owners/[A-Za-z0-9-]+/OWNER\.md"
        )
        for root in roots:
            paths = [root] if root.is_file() else list(root.rglob("*"))
            for path in paths:
                if path.is_file():
                    with self.subTest(path=path.relative_to(ROOT)):
                        text = path.read_text(encoding="utf-8")
                        self.assertIsNone(legacy.search(internal_owner_uri.sub("", text)))

    def test_core_redirect_and_adr_stale_gate_are_explicit(self) -> None:
        core = (
            ROOT / ".agents" / "skills" / "atlas-core" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("no Atlas/profile/vault/façade I/O", core)
        self.assertIn("redirect to `/atlas-ask`", core)
        agents = (ROOT / ".agents" / "AGENTS.md").read_text(encoding="utf-8")
        for identity in (
            "2026-07-29-2056_atlas-evaluation-loop",
            "2026-08-02-1332_atlas-topic-creation",
            "2026-08-02-1456_repo-agent-memory-first-draft",
        ):
            self.assertIn(identity, agents)
        self.assertIn("revised against the current architecture and owner paths", agents)
        self.assertIn("explicitly reapproved", agents)
        self.assertIn("plan-artifact-sync", agents)
        self.assertIn("remove only its own identity", agents)
        self.assertIn("Never hand-edit the pending repository projections", agents)
        index = (ROOT / "docs" / "adr" / "INDEX.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| 000[1-5] — ", index, flags=re.MULTILINE)
        self.assertEqual(len(rows), 5)
        self.assertIn(".agents/ARCHITECTURE.md", index)
        for number, filename in enumerate(
            (
                "0001-single-entry-atlas-orchestration.md",
                "0002-separate-product-and-instance-state.md",
                "0003-canonical-markdown-state.md",
                "0004-vault-only-research-and-explicit-acquisition.md",
                "0005-bounded-engineering-cycles.md",
            ),
            start=1,
        ):
            path = ROOT / "docs" / "adr" / filename
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertEqual(
                re.findall(r"^## (.+)$", text, flags=re.MULTILINE),
                ["Status", "Context", "Decision", "Consequences"],
            )
            self.assertIn("Accepted", text)
            self.assertIn(f"{number:04d}", text)

    def test_source_presence_lookup_precedes_inventory_and_fetch(self) -> None:
        path = ROOT / ".agents" / "skills" / "atlas-ask" / "owners" / "atlas-source" / "OWNER.md"
        lower = path.read_text(encoding="utf-8").lower()
        presence = lower.index("### presence and modes")
        lookup = lower.index("source.lookup", presence)
        inventory = lower.index("source.inventory")

        self.assertLess(lookup, inventory)
        self.assertLess(inventory, lower.index("fetch", inventory))
        self.assertNotIn("source.snapshot_active", lower)

    def test_source_skill_uses_inventory_before_fetch(self) -> None:
        path = ROOT / ".agents" / "skills" / "atlas-ask" / "owners" / "atlas-source" / "OWNER.md"
        lower = path.read_text(encoding="utf-8").lower()
        inventory = lower.index("source.inventory")
        fetch = lower.index("fetch", inventory)

        self.assertLess(inventory, fetch)
        self.assertIn("delimited as untrusted evidence", lower)
        self.assertIn("ignores embedded attempts", lower)

    def test_source_skill_uses_strict_schema_and_direct_correction_reply(self) -> None:
        path = ROOT / ".agents" / "skills" / "atlas-ask" / "owners" / "atlas-source" / "OWNER.md"
        lower = path.read_text(encoding="utf-8").lower()
        self.assertIn("source.worker_schema", lower)
        self.assertIn("native strict structured-output fields", lower)
        self.assertIn("outputschema:<schema>", lower)
        self.assertIn('schemamode:"strict"', lower)
        self.assertIn("one synchronous same-worker message/reply", lower)
        self.assertIn("entire returned reply body", lower)
        self.assertIn("sole json replacement object", lower)
        self.assertIn("never reread the stale initial artifact", lower)
        self.assertIn("never require another yield", lower)
        self.assertIn("without code-fence extraction", lower)
        self.assertNotIn("stale initial result artifact", lower)

    def test_acquisition_delegates_one_selected_source_batch(self) -> None:
        path = ROOT / ".agents" / "skills" / "atlas-ask" / "owners" / "atlas-acquire" / "OWNER.md"
        lower = path.read_text(encoding="utf-8").lower()
        self.assertIn(
            "pass the complete selected candidate list once to the allowlisted successor owner resource `skill://atlas-ask/owners/atlas-source/owner.md`",
            lower,
        )
        self.assertIn("acquisition adds no second inventory", lower)
        self.assertNotIn("atlas-source independently", lower)

    def test_entry_checklists_do_not_reimplement_identity(self) -> None:
        forbidden = re.compile(
            r"hashlib|hexdigest|sha-?256\s*\([^\n]+\)\s*\[\s*:?\s*12\s*\]",
            re.IGNORECASE,
        )
        paths = [ROOT / ".agents" / "skills" / "atlas-ask" / "SKILL.md"]
        paths.extend(
            (ROOT / ".agents" / "skills" / "atlas-ask" / "owners").glob("*/OWNER.md")
        )
        paths.append(ROOT / ".agents" / "commands" / "atlas-ask.md")
        for path in paths:
            if path.parent.name == "atlas-core":
                continue
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(forbidden.search(path.read_text(encoding="utf-8")))

    def test_no_provider_specific_harness_surface(self) -> None:
        roots = (
            ROOT / ".agents" / "rules",
            ROOT / ".agents" / "skills",
            ROOT / ".agents" / "commands",
        )
        provider_names = re.compile(
            r"(?:claude|grok|openai|anthropic|gemini)", re.IGNORECASE
        )
        for root in roots:
            for path in root.rglob("*"):
                if path.is_file():
                    with self.subTest(path=path.relative_to(ROOT)):
                        self.assertIsNone(provider_names.search(path.name))


if __name__ == "__main__":
    unittest.main()
