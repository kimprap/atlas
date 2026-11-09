"""Core imports no adapter and no composition module (AC-X2).

Every ``atlas.core`` module is imported in a fresh interpreter in which any
import of ``atlas.adapters`` or ``atlas.host`` fails.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "skills" / "atlas-ask"

PROBE = """
import importlib, importlib.abc, json, pkgutil, sys

BLOCKED = ("atlas.adapters", "atlas.host")

class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if any(name == b or name.startswith(b + ".") for b in BLOCKED):
            raise ImportError(f"{name} is blocked")
        return None

sys.meta_path.insert(0, Block())
import atlas.core
imported, failed = [], {}
for module in pkgutil.walk_packages(atlas.core.__path__, "atlas.core."):
    try:
        importlib.import_module(module.name)
        imported.append(module.name)
    except ImportError as err:
        failed[module.name] = str(err)
try:
    import atlas.host
    blocked = False
except ImportError:
    blocked = True
loaded = sorted(m for m in sys.modules if any(m == b or m.startswith(b + ".") for b in BLOCKED))
print(json.dumps({"imported": imported, "failed": failed, "blocked": blocked, "loaded": loaded}))
"""


class BoundaryTests(unittest.TestCase):
    def test_core_imports_with_adapters_and_host_blocked(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-c", PROBE], cwd=PACKAGE_ROOT, capture_output=True, text=True, timeout=60, check=True
        )
        seen = json.loads(proc.stdout)
        self.assertTrue(seen["blocked"], "the probe did not block atlas.host, so it proves nothing")
        self.assertEqual(seen["failed"], {})
        self.assertEqual(seen["loaded"], [])
        expected = sorted(f"atlas.core.{p.stem}" for p in (PACKAGE_ROOT / "atlas" / "core").glob("*.py") if p.stem != "__init__")
        self.assertEqual(sorted(seen["imported"]), expected)


if __name__ == "__main__":
    unittest.main()
