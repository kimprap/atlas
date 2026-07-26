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


    def test_each_entry_skill_has_a_thin_argument_preserving_command(self) -> None:
        skills = {
            path.parent.name
            for path in (ROOT / ".agents" / "skills").glob("atlas-*/SKILL.md")
            if path.parent.name != "atlas-core"
        }
        commands = {
            path.stem: path for path in (ROOT / ".agents" / "commands").glob("atlas-*.md")
        }
        self.assertEqual(set(commands), skills)
        for name, path in commands.items():
            with self.subTest(command=name):
                text = path.read_text(encoding="utf-8")
                self.assertIn(f"skill://{name}", text)
                self.assertIn("$ARGUMENTS", text)
                self.assertNotIn("## Workflow", text)
                self.assertLessEqual(len(text.splitlines()), 12)

    def test_reference_scripts_are_repo_local_and_dependency_free(self) -> None:
        allowed_by_script = {
            "atlas_state.py": {"atlas_url"},
            "atlas_quality.py": set(),
            "atlas_url.py": set(),
            # atlas_source reuses atlas_quality as the sole text-hash/projection owner.
            "atlas_source.py": {"atlas_url", "atlas_state", "atlas_quality"},
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
            external = imported - set(sys.stdlib_module_names) - allowed_local - {"__future__"}
            self.assertEqual(external, set(), f"{name} has external imports: {sorted(external)}")

    def test_source_skill_uses_canonical_identity_before_fetch(self) -> None:
        path = ROOT / ".agents" / "skills" / "atlas-source" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        helper = lower.index("scripts/atlas_url.py")
        self.assertLess(helper, lower.index("fetch", helper))
        self.assertLess(helper, lower.index("dedupe", helper))
        self.assertIn("BEGIN_UNTRUSTED_EVIDENCE_BUNDLE_JSON", text)
        self.assertIn("END_UNTRUSTED_EVIDENCE_BUNDLE_JSON", text)

    def test_entry_checklists_do_not_reimplement_identity(self) -> None:
        forbidden = re.compile(r"hashlib|hexdigest|sha-?256\s*\([^\n]+\)\s*\[\s*:?\s*12\s*\]", re.IGNORECASE)
        paths = list((ROOT / ".agents" / "skills").glob("atlas-*/SKILL.md"))
        paths.extend((ROOT / ".agents" / "commands").glob("atlas-*.md"))
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
        provider_names = re.compile(r"(?:claude|grok|openai|anthropic|gemini)", re.IGNORECASE)
        for root in roots:
            for path in root.rglob("*"):
                if path.is_file():
                    with self.subTest(path=path.relative_to(ROOT)):
                        self.assertIsNone(provider_names.search(path.name))


if __name__ == "__main__":
    unittest.main()
