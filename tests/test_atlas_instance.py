from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "atlas-instance.py"
SPEC = importlib.util.spec_from_file_location("atlas_instance", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
atlas_instance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(atlas_instance)

import atlas_state


def empty_registry(header: tuple[str, ...]) -> str:
    return (
        "---\nschema_version: 1\n---\n\n"
        + "| "
        + " | ".join(header)
        + " |\n|"
        + "|".join("---" for _ in header)
        + "|\n"
    )


class AtlasInstanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.app_root = self.root / "app"
        self.scaffold_dir = self.app_root / "scaffold"
        self.instances_root = self.root / "instances"
        self.manifest_path = self.scaffold_dir / "MANIFEST.json"
        self.architecture_source = self.app_root / ".agents" / "ARCHITECTURE.md"
        self.seed_source = self.scaffold_dir / "summaries" / "INDEX.md"
        self.registry_sources = {
            "summaries/sources/MANIFEST.md": empty_registry(
                atlas_state.MANIFEST_HEADER
            ),
            "summaries/registry/TOPICS.md": empty_registry(atlas_state.TOPICS_HEADER),
            "summaries/registry/RELATIONS.md": empty_registry(
                atlas_state.RELATIONS_HEADER
            ),
        }

        self.architecture_source.parent.mkdir(parents=True)
        self.architecture_source.write_text("architecture-v1\n", encoding="utf-8")
        self.seed_source.parent.mkdir(parents=True)
        self.seed_source.write_text("seed-v1\n", encoding="utf-8")
        for relative, text in self.registry_sources.items():
            path = self.scaffold_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.write_manifest()

        patcher = mock.patch.multiple(
            atlas_instance,
            APP_ROOT=self.app_root,
            SCAFFOLD_DIR=self.scaffold_dir,
            MANIFEST_PATH=self.manifest_path,
            DEFAULT_INSTANCES_ROOT=self.instances_root,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_manifest(self, data: object | None = None) -> None:
        if data is None:
            data = {
                "schema_version": 1,
                "product_owned": [
                    {
                        "source": ".agents/ARCHITECTURE.md",
                        "dest": "ARCHITECTURE.md",
                    }
                ],
                "seed_once": ["summaries/INDEX.md", *self.registry_sources],
                "never_touch": ["summaries/research/**"],
            }
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")

    def args(
        self, *, name: str | None = "personal", all_: bool = False
    ) -> argparse.Namespace:
        return argparse.Namespace(
            instances_root=str(self.instances_root),
            name=name,
            all=all_,
        )

    def run_command(self, command, args: argparse.Namespace) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = command(args)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_create_materializes_owned_and_seed_files(self) -> None:
        result, output, errors = self.run_command(
            atlas_instance.cmd_create,
            self.args(),
        )

        instance = self.instances_root / "personal"
        self.assertEqual(result, 0)
        self.assertEqual(errors, "")
        self.assertIn("created instance", output)
        self.assertEqual(
            (instance / "ARCHITECTURE.md").read_text(encoding="utf-8"),
            "architecture-v1\n",
        )
        self.assertEqual(
            (instance / "summaries" / "INDEX.md").read_text(encoding="utf-8"),
            "seed-v1\n",
        )

    def test_create_rejects_existing_instance(self) -> None:
        self.run_command(atlas_instance.cmd_create, self.args())

        result, _, errors = self.run_command(atlas_instance.cmd_create, self.args())

        self.assertEqual(result, 1)
        self.assertIn("instance already exists", errors)

    def test_instance_name_rejects_path_like_values(self) -> None:
        for name in ("", ".", "..", "nested/name", "nested\\name"):
            with self.subTest(name=name), self.assertRaises(SystemExit):
                atlas_instance.instance_dir(self.instances_root, name)

    def test_manifest_rejects_escaping_destination_before_create(self) -> None:
        self.write_manifest(
            {
                "product_owned": [
                    {
                        "source": ".agents/ARCHITECTURE.md",
                        "dest": "../outside.md",
                    }
                ],
                "seed_once": ["summaries/INDEX.md"],
            }
        )

        with self.assertRaises(SystemExit):
            atlas_instance.cmd_create(self.args())

        self.assertFalse((self.instances_root / "personal").exists())
        self.assertFalse((self.root / "outside.md").exists())

    def test_missing_source_fails_without_partial_destination(self) -> None:
        self.architecture_source.unlink()

        with self.assertRaises(SystemExit):
            atlas_instance.cmd_create(self.args())

        self.assertFalse((self.instances_root / "personal").exists())

    def test_copy_failure_removes_new_destination(self) -> None:
        with mock.patch.object(
            atlas_instance,
            "write_product_owned",
            side_effect=OSError("simulated copy failure"),
        ):
            with self.assertRaises(OSError):
                atlas_instance.cmd_create(self.args())

        self.assertFalse((self.instances_root / "personal").exists())

    def test_sync_updates_only_product_owned_files(self) -> None:
        self.run_command(atlas_instance.cmd_create, self.args())
        instance = self.instances_root / "personal"
        instance_seed = instance / "summaries" / "INDEX.md"
        instance_seed.write_text("living-state\n", encoding="utf-8")
        self.architecture_source.write_text("architecture-v2\n", encoding="utf-8")

        result, output, errors = self.run_command(
            atlas_instance.cmd_sync_framework,
            self.args(),
        )

        self.assertEqual(result, 0)
        self.assertEqual(errors, "")
        self.assertIn("synced product_owned", output)
        self.assertEqual(
            (instance / "ARCHITECTURE.md").read_text(encoding="utf-8"),
            "architecture-v2\n",
        )
        self.assertEqual(instance_seed.read_text(encoding="utf-8"), "living-state\n")

    def test_sync_preserves_unmanaged_legacy_todo_and_check_succeeds(self) -> None:
        self.run_command(atlas_instance.cmd_create, self.args())
        legacy_todo = self.instances_root / "personal" / "todos" / "TODOs.md"
        legacy_todo.parent.mkdir()
        legacy_bytes = b"# personal legacy todo\n- preserve me\n"
        legacy_todo.write_bytes(legacy_bytes)

        result, output, errors = self.run_command(
            atlas_instance.cmd_sync_framework,
            self.args(),
        )
        check_result, check_output, check_errors = self.run_command(
            atlas_instance.cmd_check,
            self.args(),
        )

        self.assertEqual(result, 0)
        self.assertEqual(errors, "")
        self.assertIn("synced product_owned", output)
        self.assertEqual(legacy_todo.read_bytes(), legacy_bytes)
        self.assertEqual(check_result, 0)
        self.assertEqual(check_errors, "")
        self.assertIn("check OK", check_output)

    def test_check_reports_product_owned_drift(self) -> None:
        self.run_command(atlas_instance.cmd_create, self.args())
        (self.instances_root / "personal" / "ARCHITECTURE.md").write_text(
            "drifted\n",
            encoding="utf-8",
        )

        result, output, _ = self.run_command(atlas_instance.cmd_check, self.args())

        self.assertEqual(result, 1)
        self.assertIn("product_owned drift", output)

    def test_check_passes_new_empty_instance(self) -> None:
        self.run_command(atlas_instance.cmd_create, self.args())

        result, output, errors = self.run_command(atlas_instance.cmd_check, self.args())

        self.assertEqual(result, 0)
        self.assertEqual(errors, "")
        self.assertIn("check OK", output)

    def test_check_reports_living_registry_orphan(self) -> None:
        self.run_command(atlas_instance.cmd_create, self.args())
        relations = self.instances_root / "personal" / atlas_state.RELATIONS_PATH
        row = [
            "edge--123456789abc--test-topic--aaaaaaaa",
            "1",
            "123456789abc",
            "summaries/sources/example.md",
            "a" * 64,
            "test-topic",
            "direct",
            "high",
            "high",
            "pending",
            "2026-07-15",
            "",
            "orphan",
        ]
        relations.write_text(
            relations.read_text(encoding="utf-8")
            + "\nSchema notes.\n| "
            + " | ".join(row)
            + " |\n",
            encoding="utf-8",
        )

        result, output, _ = self.run_command(atlas_instance.cmd_check, self.args())

        self.assertEqual(result, 1)
        self.assertIn("RELATION_ROW_OUTSIDE_TABLE", output)


class AtlasProductionManifestTests(unittest.TestCase):
    def test_create_omits_retired_todo_seed_and_check_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            instances_root = Path(directory) / "instances"
            create = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--instances-root",
                    str(instances_root),
                    "create",
                    "--name",
                    "atlas",
                ],
                cwd=SCRIPT_PATH.parent.parent,
                check=False,
                capture_output=True,
                text=True,
            )
            check = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--instances-root",
                    str(instances_root),
                    "check",
                    "--name",
                    "atlas",
                ],
                cwd=SCRIPT_PATH.parent.parent,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(create.returncode, 0, create.stderr)
            self.assertIn("seed_once: 7 file(s)", create.stdout)
            self.assertFalse((instances_root / "atlas" / "todos" / "TODOs.md").exists())
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            self.assertIn("check OK", check.stdout)


if __name__ == "__main__":
    unittest.main()
