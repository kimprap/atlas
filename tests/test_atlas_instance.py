from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "atlas-instance.py"
TOOL_PATH = ROOT / "scripts" / "atlas_tool.py"
SPEC = importlib.util.spec_from_file_location("atlas_instance", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
atlas_instance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(atlas_instance)

import atlas_state  # noqa: E402


ENVELOPE_KEYS = {
    "version",
    "ok",
    "op",
    "disposition",
    "result",
    "findings",
    "recovery",
}


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

    def manifest(self) -> dict[str, object]:
        return {
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

    def write_manifest(self, data: object | None = None) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(self.manifest() if data is None else data),
            encoding="utf-8",
        )

    def args(
        self,
        *,
        name: str | None = "personal",
        all_: bool = False,
        dry_run: bool = False,
    ) -> argparse.Namespace:
        return argparse.Namespace(
            instances_root=str(self.instances_root),
            name=name,
            all=all_,
            dry_run=dry_run,
        )

    def call_cli(self, *arguments: str) -> dict[str, object]:
        return atlas_instance.run(
            ["--instances-root", str(self.instances_root), *arguments]
        )

    def assert_envelope(
        self,
        response: dict[str, object],
        *,
        op: str,
        disposition: str,
    ) -> None:
        self.assertEqual(set(response), ENVELOPE_KEYS)
        self.assertEqual(response["version"], 2)
        self.assertEqual(response["ok"], disposition in {"completed", "no-write"})
        self.assertEqual(response["op"], op)
        self.assertEqual(response["disposition"], disposition)
        self.assertIsNone(response["recovery"])
        if response["ok"]:
            self.assertEqual(response["findings"], [])
        else:
            self.assertTrue(response["findings"])

    def snapshot(self, root: Path) -> dict[str, bytes]:
        if not root.exists():
            return {}
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

    def test_inspect_framework_reports_manifest_derived_files_and_counts(self) -> None:
        response = atlas_instance.cmd_inspect_framework(argparse.Namespace())

        self.assert_envelope(
            response,
            op="instance.inspect-framework",
            disposition="no-write",
        )
        result = response["result"]
        manifest = self.manifest()
        self.assertEqual(
            result["counts"],
            {
                "product_owned": len(manifest["product_owned"]),
                "seed_once": len(manifest["seed_once"]),
                "total": len(manifest["product_owned"]) + len(manifest["seed_once"]),
            },
        )
        self.assertEqual(result["files"]["product_owned"], manifest["product_owned"])
        self.assertEqual(result["files"]["seed_once"], manifest["seed_once"])

    def test_inspect_rejects_duplicate_and_colliding_destinations(self) -> None:
        cases = (
            (
                "duplicate",
                {
                    **self.manifest(),
                    "product_owned": [
                        {
                            "source": ".agents/ARCHITECTURE.md",
                            "dest": "ARCHITECTURE.md",
                        },
                        {
                            "source": ".agents/ARCHITECTURE.md",
                            "dest": "ARCHITECTURE.md",
                        },
                    ],
                },
                "FRAMEWORK_DESTINATION_DUPLICATE",
            ),
            (
                "cross-class",
                {
                    **self.manifest(),
                    "product_owned": [
                        {
                            "source": ".agents/ARCHITECTURE.md",
                            "dest": "summaries/INDEX.md",
                        }
                    ],
                },
                "FRAMEWORK_DESTINATION_DUPLICATE",
            ),
            (
                "ancestor",
                {
                    **self.manifest(),
                    "product_owned": [
                        {
                            "source": ".agents/ARCHITECTURE.md",
                            "dest": "summaries",
                        }
                    ],
                },
                "FRAMEWORK_DESTINATION_COLLISION",
            ),
        )
        for label, manifest, code in cases:
            with self.subTest(label=label):
                self.write_manifest(manifest)
                response = self.call_cli("inspect-framework")
                self.assert_envelope(
                    response,
                    op="instance.inspect-framework",
                    disposition="rejected",
                )
                self.assertEqual(response["findings"][0]["code"], code)
                self.assertFalse(self.instances_root.exists())

    def test_inspect_rejects_escaping_and_missing_sources_without_host_paths(
        self,
    ) -> None:
        escaping = self.manifest()
        escaping["product_owned"] = [
            {"source": "../ARCHITECTURE.md", "dest": "ARCHITECTURE.md"}
        ]
        self.write_manifest(escaping)
        outside = self.call_cli("create", "--name", "personal")
        self.assertEqual(
            outside["findings"][0]["code"], "FRAMEWORK_SOURCE_OUTSIDE_ROOT"
        )
        self.assertFalse((self.instances_root / "personal").exists())

        missing = self.manifest()
        missing["product_owned"] = [
            {"source": ".agents/MISSING.md", "dest": "ARCHITECTURE.md"}
        ]
        self.write_manifest(missing)
        unavailable = self.call_cli("create", "--name", "personal")
        self.assert_envelope(
            unavailable,
            op="instance.create",
            disposition="unavailable",
        )
        self.assertEqual(unavailable["findings"][0]["code"], "FRAMEWORK_SOURCE_MISSING")
        self.assertNotIn(str(self.root), json.dumps(unavailable, sort_keys=True))
        self.assertFalse((self.instances_root / "personal").exists())

    def test_create_sync_and_check_reuse_inspect_framework_once(self) -> None:
        atlas_instance.cmd_create(self.args())
        real_inspect = atlas_instance.inspect_framework
        cases = (
            (
                atlas_instance.cmd_inspect_framework,
                argparse.Namespace(),
                "instance.inspect-framework",
            ),
            (
                atlas_instance.cmd_create,
                self.args(name="preview", dry_run=True),
                "instance.create",
            ),
            (
                atlas_instance.cmd_sync_framework,
                self.args(dry_run=True),
                "instance.sync-framework",
            ),
            (atlas_instance.cmd_check, self.args(), "instance.check"),
        )
        for command, args, op in cases:
            with (
                self.subTest(op=op),
                mock.patch.object(
                    atlas_instance,
                    "inspect_framework",
                    wraps=real_inspect,
                ) as inspect,
            ):
                response = command(args)
                self.assertEqual(response["op"], op)
                self.assertEqual(inspect.call_count, 1)

    def test_create_materializes_manifest_files(self) -> None:
        response = atlas_instance.cmd_create(self.args())

        instance = self.instances_root / "personal"
        self.assert_envelope(
            response,
            op="instance.create",
            disposition="completed",
        )
        self.assertEqual(
            (instance / "ARCHITECTURE.md").read_text(encoding="utf-8"),
            "architecture-v1\n",
        )
        self.assertEqual(
            (instance / "summaries" / "INDEX.md").read_text(encoding="utf-8"),
            "seed-v1\n",
        )
        self.assertEqual(
            response["result"]["framework"]["counts"]["total"],
            len(self.manifest()["product_owned"]) + len(self.manifest()["seed_once"]),
        )

    def test_create_dry_run_reports_plan_and_writes_nothing(self) -> None:
        with mock.patch.object(atlas_instance, "copy_file") as copy:
            response = atlas_instance.cmd_create(self.args(dry_run=True))

        self.assert_envelope(
            response,
            op="instance.create",
            disposition="no-write",
        )
        self.assertTrue(response["result"]["dry_run"])
        self.assertEqual(
            response["result"]["product_owned"],
            {"changed": ["ARCHITECTURE.md"], "unchanged": []},
        )
        copy.assert_not_called()
        self.assertFalse(self.instances_root.exists())

    def test_create_rejects_existing_instance(self) -> None:
        atlas_instance.cmd_create(self.args())
        response = self.call_cli("create", "--name", "personal")

        self.assert_envelope(
            response,
            op="instance.create",
            disposition="rejected",
        )
        self.assertEqual(response["findings"][0]["code"], "INSTANCE_ALREADY_EXISTS")

    def test_instance_name_rejects_path_like_values(self) -> None:
        for name in ("", ".", "..", "nested/name", "nested\\name"):
            with (
                self.subTest(name=name),
                self.assertRaises(atlas_instance.InstanceCliError),
            ):
                atlas_instance.instance_dir(self.instances_root, name)

    def test_manifest_rejects_escaping_destination_before_create(self) -> None:
        manifest = self.manifest()
        manifest["product_owned"] = [
            {
                "source": ".agents/ARCHITECTURE.md",
                "dest": "../outside.md",
            }
        ]
        self.write_manifest(manifest)

        response = self.call_cli("create", "--name", "personal")

        self.assertEqual(
            response["findings"][0]["code"],
            "FRAMEWORK_DESTINATION_OUTSIDE_ROOT",
        )
        self.assertFalse((self.instances_root / "personal").exists())
        self.assertFalse((self.root / "outside.md").exists())

    def test_copy_failure_removes_whole_new_destination(self) -> None:
        with mock.patch.object(
            atlas_instance,
            "write_product_owned",
            side_effect=OSError("simulated copy failure"),
        ):
            response = self.call_cli("create", "--name", "personal")

        self.assert_envelope(
            response,
            op="instance.create",
            disposition="unavailable",
        )
        self.assertEqual(response["findings"][0]["code"], "INSTANCE_CREATE_IO_FAILURE")
        self.assertFalse((self.instances_root / "personal").exists())

    def test_sync_updates_only_product_owned_files(self) -> None:
        atlas_instance.cmd_create(self.args())
        instance = self.instances_root / "personal"
        instance_seed = instance / "summaries" / "INDEX.md"
        instance_seed.write_text("living-state\n", encoding="utf-8")
        self.architecture_source.write_text("architecture-v2\n", encoding="utf-8")

        response = atlas_instance.cmd_sync_framework(self.args())

        self.assert_envelope(
            response,
            op="instance.sync-framework",
            disposition="completed",
        )
        self.assertEqual(
            response["result"]["instances"],
            [
                {
                    "instance": "personal",
                    "changed": ["ARCHITECTURE.md"],
                    "unchanged": [],
                }
            ],
        )
        self.assertEqual(
            (instance / "ARCHITECTURE.md").read_text(encoding="utf-8"),
            "architecture-v2\n",
        )
        self.assertEqual(instance_seed.read_text(encoding="utf-8"), "living-state\n")

    def test_sync_dry_run_compares_and_writes_nothing(self) -> None:
        atlas_instance.cmd_create(self.args())
        instance = self.instances_root / "personal"
        self.architecture_source.write_text("architecture-v2\n", encoding="utf-8")
        before = self.snapshot(instance)

        with mock.patch.object(atlas_instance, "copy_file") as copy:
            response = atlas_instance.cmd_sync_framework(self.args(dry_run=True))

        self.assert_envelope(
            response,
            op="instance.sync-framework",
            disposition="no-write",
        )
        self.assertEqual(
            response["result"]["instances"][0]["changed"],
            ["ARCHITECTURE.md"],
        )
        self.assertEqual(response["result"]["counts"]["changed"], 1)
        copy.assert_not_called()
        self.assertEqual(self.snapshot(instance), before)

    def test_sync_all_preserves_unmanaged_files_and_seed_state(self) -> None:
        atlas_instance.cmd_create(self.args(name="personal"))
        atlas_instance.cmd_create(self.args(name="team"))
        legacy = self.instances_root / "personal" / "todos" / "TODOs.md"
        legacy.parent.mkdir()
        legacy_bytes = b"# personal legacy todo\n- preserve me\n"
        legacy.write_bytes(legacy_bytes)
        living_seed = self.instances_root / "team" / "summaries" / "INDEX.md"
        living_seed.write_text("living-state\n", encoding="utf-8")
        self.architecture_source.write_text("architecture-v2\n", encoding="utf-8")

        response = atlas_instance.cmd_sync_framework(self.args(name=None, all_=True))

        self.assertEqual(response["result"]["counts"]["instances"], 2)
        self.assertEqual(legacy.read_bytes(), legacy_bytes)
        self.assertEqual(living_seed.read_text(encoding="utf-8"), "living-state\n")
        for name in ("personal", "team"):
            self.assertEqual(
                (self.instances_root / name / "ARCHITECTURE.md").read_text(
                    encoding="utf-8"
                ),
                "architecture-v2\n",
            )

    def test_name_all_conflicts_fail_before_inspection_or_effect(self) -> None:
        for command in ("sync-framework", "check"):
            with (
                self.subTest(command=command),
                mock.patch.object(atlas_instance, "inspect_framework") as inspect,
                mock.patch.object(atlas_instance, "write_product_owned") as write,
            ):
                response = self.call_cli(
                    command,
                    "--name",
                    "personal",
                    "--all",
                )
                self.assert_envelope(
                    response,
                    op=f"instance.{command}",
                    disposition="rejected",
                )
                self.assertEqual(
                    response["findings"][0]["code"],
                    "INSTANCE_SELECTOR_CONFLICT",
                )
                inspect.assert_not_called()
                write.assert_not_called()
        self.assertFalse(self.instances_root.exists())

    def test_check_reports_product_owned_drift(self) -> None:
        atlas_instance.cmd_create(self.args())
        (self.instances_root / "personal" / "ARCHITECTURE.md").write_text(
            "drifted\n",
            encoding="utf-8",
        )

        response = atlas_instance.cmd_check(self.args())

        self.assert_envelope(
            response,
            op="instance.check",
            disposition="rejected",
        )
        self.assertEqual(
            response["findings"][0]["code"], "INSTANCE_PRODUCT_OWNED_DRIFT"
        )

    def test_check_default_all_passes_new_instances(self) -> None:
        atlas_instance.cmd_create(self.args(name="personal"))
        atlas_instance.cmd_create(self.args(name="team"))

        response = atlas_instance.cmd_check(self.args(name=None))

        self.assert_envelope(
            response,
            op="instance.check",
            disposition="no-write",
        )
        self.assertEqual(response["result"]["instances"], ["personal", "team"])
        self.assertEqual(response["result"]["counts"]["instances"], 2)

    def test_check_reports_living_registry_orphan(self) -> None:
        atlas_instance.cmd_create(self.args())
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

        response = atlas_instance.cmd_check(self.args())

        self.assertEqual(response["disposition"], "rejected")
        self.assertIn(
            "RELATION_ROW_OUTSIDE_TABLE",
            {item["code"] for item in response["findings"]},
        )


class AtlasProductionManifestTests(unittest.TestCase):
    def run_instance(
        self, instances_root: Path, *arguments: str
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--instances-root",
                str(instances_root),
                *arguments,
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )

    def assert_canonical_envelope(
        self,
        completed: subprocess.CompletedProcess,
        *,
        op: str,
        disposition: str,
    ) -> dict[str, object]:
        self.assertEqual(completed.stderr, b"")
        response = json.loads(completed.stdout)
        self.assertEqual(set(response), ENVELOPE_KEYS)
        self.assertEqual(response["op"], op)
        self.assertEqual(response["disposition"], disposition)
        self.assertEqual(completed.stdout, atlas_instance.atlas_cli.encode(response))
        return response

    def test_real_create_and_check_use_production_manifest_counts(self) -> None:
        manifest = json.loads((ROOT / "scaffold" / "MANIFEST.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            instances_root = Path(directory) / "instances"
            create = self.run_instance(
                instances_root,
                "create",
                "--name",
                "atlas",
            )
            check = self.run_instance(
                instances_root,
                "check",
                "--name",
                "atlas",
            )

            self.assertEqual(create.returncode, 0, create.stdout + create.stderr)
            created = self.assert_canonical_envelope(
                create,
                op="instance.create",
                disposition="completed",
            )
            self.assertEqual(
                created["result"]["framework"]["counts"],
                {
                    "product_owned": len(manifest["product_owned"]),
                    "seed_once": len(manifest["seed_once"]),
                    "total": len(manifest["product_owned"])
                    + len(manifest["seed_once"]),
                },
            )
            self.assertFalse((instances_root / "atlas" / "todos" / "TODOs.md").exists())
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            checked = self.assert_canonical_envelope(
                check,
                op="instance.check",
                disposition="no-write",
            )
            self.assertEqual(
                checked["result"]["counts"]["seed_once_per_instance"],
                len(manifest["seed_once"]),
            )

    def test_created_instance_binds_to_canonical_facade(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instances_root = root / "vault" / "instances"
            created = self.run_instance(
                instances_root,
                "create",
                "--name",
                "atlas",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)

            profile = root / "vault" / "config" / "profiles" / "local.yml"
            profile.parent.mkdir(parents=True)
            profile.write_text(
                "profile: local\n"
                "instance: atlas\n"
                "connector: local-fs\n"
                "local_fs:\n"
                "  root: instances/atlas\n",
                encoding="utf-8",
            )
            request = atlas_instance.atlas_cli.encode(
                {"path": "vault://atlas/ARCHITECTURE.md"}
            )
            bound = subprocess.run(
                [
                    sys.executable,
                    str(TOOL_PATH),
                    "--profile",
                    str(profile),
                    "vault",
                    "hash",
                    "--input",
                    "-",
                ],
                cwd=ROOT,
                input=request,
                check=False,
                capture_output=True,
            )

            self.assertEqual(bound.returncode, 0, bound.stdout + bound.stderr)
            self.assertEqual(bound.stderr, b"")
            response = json.loads(bound.stdout)
            self.assertEqual(response["op"], "vault.hash")
            self.assertTrue(response["ok"])
            expected = (
                "sha256:"
                + hashlib.sha256(
                    (ROOT / ".agents" / "ARCHITECTURE.md").read_bytes()
                ).hexdigest()
            )
            self.assertEqual(response["result"]["revision"], expected)
            self.assertNotIn(str(root), json.dumps(response, sort_keys=True))

    def test_machine_selector_conflict_is_canonical_and_zero_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            instances_root = Path(directory) / "instances"
            conflict = self.run_instance(
                instances_root,
                "sync-framework",
                "--name",
                "atlas",
                "--all",
            )

            self.assertEqual(conflict.returncode, 2)
            response = self.assert_canonical_envelope(
                conflict,
                op="instance.sync-framework",
                disposition="rejected",
            )
            self.assertEqual(
                response["findings"][0]["code"], "INSTANCE_SELECTOR_CONFLICT"
            )
            self.assertFalse(instances_root.exists())


if __name__ == "__main__":
    unittest.main()
