from __future__ import annotations

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
        for name in ("atlas_state.py", "atlas_quality.py"):
            path = ROOT / "scripts" / name
            self.assertTrue(path.is_file(), f"missing reference script: {path}")
            self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))


if __name__ == "__main__":
    unittest.main()
