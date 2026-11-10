"""No unused import and no dead module-level name in the repository's Python.

The repository installs no linter, so this is the suite's lint check. An
import kept for its side effect carries ``# noqa: F401`` on its line.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ("skills", "tools", "tests")


def loaded_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def exported_names(tree: ast.Module) -> set[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            return {str(value) for value in ast.literal_eval(node.value)}
    return set()


def unused_imports(tree: ast.Module, lines: list[str]) -> list[tuple[int, str]]:
    used = loaded_names(tree) | exported_names(tree)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if any("noqa: F401" in line for line in lines[node.lineno - 1 : node.end_lineno]):
            continue
        for alias in node.names:
            name = (alias.asname or alias.name).split(".")[0]
            if name != "*" and name not in used:
                found.append((node.lineno, name))
    return found


def module_names(tree: ast.Module) -> list[tuple[int, str]]:
    found = []
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        found += [(node.lineno, t.id) for t in targets if isinstance(t, ast.Name) and not t.id.startswith("__")]
    return found


class LintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {}
        for folder in FOLDERS:
            for path in sorted((ROOT / folder).rglob("*.py")):
                text = path.read_text(encoding="utf-8")
                cls.sources[path.relative_to(ROOT).as_posix()] = (ast.parse(text), text.splitlines())

    def test_no_import_is_unused(self) -> None:
        found = [f"{path}:{line} {name}" for path, (tree, lines) in self.sources.items() for line, name in unused_imports(tree, lines)]
        self.assertEqual(found, [])

    def test_no_module_level_name_is_never_read(self) -> None:
        read = set().union(*(loaded_names(tree) | exported_names(tree) for tree, _ in self.sources.values()))
        found = [f"{path}:{line} {name}" for path, (tree, _) in self.sources.items() for line, name in module_names(tree) if name not in read]
        self.assertEqual(found, [])

    def test_the_scan_sees_an_unused_import_and_honours_the_marker(self) -> None:
        text = "import os\nimport json  # noqa: F401\nimport sys\nprint(sys.argv)\n"
        self.assertEqual(unused_imports(ast.parse(text), text.splitlines()), [(1, "os")])


if __name__ == "__main__":
    unittest.main()
