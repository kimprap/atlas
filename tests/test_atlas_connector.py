from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_connector  # noqa: E402


PROFILE_TEXT = """\
profile: local
instance: atlas
connector: local-fs
local_fs:
  root: instances/atlas
"""


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class ConnectorFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.workspace = Path(self.temp_dir.name)
        self.app_root = self.workspace / "app"
        self.vault_root = self.workspace / "vault"
        self.profile_dir = self.vault_root / "config" / "profiles"
        self.instance_root = self.vault_root / "instances" / "atlas"
        self.app_root.mkdir()
        self.profile_dir.mkdir(parents=True)
        self.instance_root.mkdir(parents=True)
        self.profile_path = self.profile_dir / "local.yml"
        self.profile_path.write_text(PROFILE_TEXT, encoding="utf-8")
        self.profile = atlas_connector.resolve_profile(profile_path=self.profile_path)
        self.connector = atlas_connector.LocalFilesystemConnector(self.profile)

    def uri(self, relative: str) -> str:
        return "vault://atlas/" + relative

    def write_fixture(self, relative: str, value: bytes) -> Path:
        path = self.instance_root.joinpath(*PurePosixPath(relative).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return path

    def assert_rejected(self, callback):
        with self.assertRaises((ValueError, OSError)) as caught:
            callback()
        return caught.exception

    def delete_request(self, uri: str, digest: dict[str, object]) -> dict[str, str]:
        expected_digest = str(digest["digest"])
        projection_sha256 = "c" * 64
        return {
            "expected_digest": expected_digest,
            "projection_sha256": projection_sha256,
            "approval": f"DELETE_TREE {uri} {expected_digest} {projection_sha256}",
            "report_revision": "sha256:" + "d" * 64,
        }


class LocalProfileTests(ConnectorFixture):
    def test_profile_accepts_only_the_exact_scalar_local_shape(self) -> None:
        self.assertEqual(self.profile.profile, "local")
        self.assertEqual(self.profile.instance, "atlas")
        self.assertEqual(self.profile.connector, "local-fs")
        self.assertEqual(self.profile.root, self.instance_root.resolve())

        malformed = {
            "duplicate": """\
profile: local
profile: local
instance: atlas
connector: local-fs
local_fs:
  root: instances/atlas
""",
            "unknown-top-level": """\
profile: local
instance: atlas
connector: local-fs
extra: forbidden
local_fs:
  root: instances/atlas
""",
            "unknown-local-fs": """\
profile: local
instance: atlas
connector: local-fs
local_fs:
  root: instances/atlas
  extra: forbidden
""",
            "mapping-scalar": """\
profile:
  name: local
instance: atlas
connector: local-fs
local_fs:
  root: instances/atlas
""",
            "sequence-root": """\
profile: local
instance: atlas
connector: local-fs
local_fs:
  root:
    - instances/atlas
""",
        }
        for name, value in malformed.items():
            with self.subTest(shape=name):
                path = self.profile_dir / f"{name}.yml"
                path.write_text(value, encoding="utf-8")
                self.assert_rejected(
                    lambda path=path: atlas_connector.resolve_profile(profile_path=path)
                )

    def test_environment_profile_overrides_the_cwd_relative_default(self) -> None:
        default_root = self.vault_root / "instances" / "atlas"
        override_root = self.vault_root / "instances" / "alternate"
        override_root.mkdir(parents=True)
        override_path = self.profile_dir / "alternate.yml"
        override_path.write_text(
            PROFILE_TEXT.replace("instances/atlas", "instances/alternate"),
            encoding="utf-8",
        )

        with working_directory(self.app_root), patch.dict(os.environ, {}, clear=True):
            selected_default = atlas_connector.resolve_profile()
        with (
            working_directory(self.app_root),
            patch.dict(
                os.environ,
                {"ATLAS_VAULT_PROFILE": str(override_path)},
                clear=True,
            ),
        ):
            selected_environment = atlas_connector.resolve_profile()

        self.assertEqual(selected_default.root, default_root.resolve())
        self.assertEqual(selected_environment.root, override_root.resolve())
        self.assertNotEqual(selected_default.root, selected_environment.root)


class LocalFilesystemConnectorTests(ConnectorFixture):
    def test_logical_uris_reject_traversal_query_fragment_and_credentials(self) -> None:
        self.write_fixture("keep.txt", b"inside")
        (self.instance_root.parent / "escape.txt").write_bytes(b"outside")
        rejected = (
            "vault://atlas/../escape.txt",
            "vault://atlas/%2e%2e/escape.txt",
            "vault://atlas/keep.txt?ignored=true",
            "vault://atlas/keep.txt#fragment",
            "vault://user@atlas/keep.txt",
            "vault://other/keep.txt",
        )
        for uri in rejected:
            with self.subTest(uri=uri):
                self.assert_rejected(lambda uri=uri: self.connector.read_bytes(uri))
        self.assertEqual(self.connector.read_bytes(self.uri("keep.txt")), b"inside")

    def test_descriptor_safe_access_rejects_in_root_symlinks(self) -> None:
        self.write_fixture("target.txt", b"must not be reached through a link")
        (self.instance_root / "alias.txt").symlink_to("target.txt")

        error = self.assert_rejected(
            lambda: self.connector.read_text(self.uri("alias.txt"))
        )
        self.assertIn("symlink", str(error).lower())
        self.assertEqual(
            self.connector.read_text(self.uri("target.txt")),
            "must not be reached through a link",
        )

    def test_text_json_and_revision_are_exact_full_byte_operations(self) -> None:
        text_bytes = b"first\r\nsecond\n"
        json_bytes = b'{"label":"\xc3\xa9","values":[2,1]}\n'
        self.write_fixture("raw.txt", text_bytes)
        self.write_fixture("raw.json", json_bytes)

        self.assertEqual(
            self.connector.read_text(self.uri("raw.txt")), "first\r\nsecond\n"
        )
        self.assertEqual(self.connector.read_bytes(self.uri("raw.json")), json_bytes)
        self.assertEqual(
            self.connector.read_json(self.uri("raw.json")),
            {"label": "é", "values": [2, 1]},
        )
        self.assertEqual(self.connector.revision(self.uri("missing.txt")), "missing")
        self.assertEqual(
            self.connector.revision(self.uri("raw.txt")),
            "sha256:" + hashlib.sha256(text_bytes).hexdigest(),
        )

        outcome = self.connector.write_json(
            self.uri("written.json"), {"z": 1, "a": "é"}
        )
        expected = b'{"a":"\xc3\xa9","z":1}\n'
        expected_revision = "sha256:" + hashlib.sha256(expected).hexdigest()
        self.assertEqual(
            outcome,
            {
                "status": "replaced",
                "revision": expected_revision,
                "acknowledged_revision": expected_revision,
            },
        )
        self.assertEqual(self.connector.read_bytes(self.uri("written.json")), expected)

    def test_text_and_json_reject_invalid_utf8(self) -> None:
        self.write_fixture("bad.txt", b"\xff")
        self.write_fixture("bad.json", b'{"value":"\xff"}')

        self.assert_rejected(lambda: self.connector.read_text(self.uri("bad.txt")))
        self.assert_rejected(lambda: self.connector.read_json(self.uri("bad.json")))

    def test_list_is_bytewise_sorted_logical_uris(self) -> None:
        for name in ("z.txt", "B.txt", "a.txt", "é.txt"):
            self.write_fixture(f"listed/{name}", name.encode("utf-8"))

        self.assertEqual(
            self.connector.list(self.uri("listed")),
            [
                self.uri("listed/B.txt"),
                self.uri("listed/a.txt"),
                self.uri("listed/z.txt"),
                self.uri("listed/é.txt"),
            ],
        )

    def test_conditional_replace_is_strict_and_returns_a_durable_reread(self) -> None:
        uri = self.uri("replace.txt")
        first_bytes = b"first\r\n"
        first_revision = "sha256:" + hashlib.sha256(first_bytes).hexdigest()
        first = self.connector.conditional_replace(uri, "missing", first_bytes)
        self.assertEqual(
            first,
            {
                "status": "replaced",
                "revision": first_revision,
                "acknowledged_revision": first_revision,
            },
        )

        competing = self.assert_rejected(
            lambda: self.connector.conditional_replace(uri, "missing", b"second")
        )
        self.assertIn("revision", str(competing).lower())
        self.assertEqual(self.connector.read_bytes(uri), first_bytes)

        no_change = self.connector.conditional_replace(uri, first_revision, first_bytes)
        self.assertEqual(
            no_change,
            {
                "status": "no_change",
                "revision": first_revision,
                "acknowledged_revision": first_revision,
            },
        )
        fresh_connector = atlas_connector.LocalFilesystemConnector(self.profile)
        self.assertEqual(fresh_connector.revision(uri), first["acknowledged_revision"])
        self.assertEqual(fresh_connector.read_bytes(uri), first_bytes)

    def test_capabilities_advertise_only_a_callable_mutation_port(self) -> None:
        capabilities = self.connector.capabilities()
        self.assertEqual(capabilities["adapter"], "atlas-local-fs-cas-v1")
        self.assertEqual(capabilities["root"], "vault://atlas/")
        self.assertEqual(capabilities["conditional_replace"], "available")
        self.assertNotIn(
            str(self.instance_root), json.dumps(capabilities, sort_keys=True)
        )

        with self.connector.mutation_session():
            outcome = self.connector.conditional_replace(
                self.uri("capability.txt"), "missing", b"callable"
            )
        self.assertEqual(outcome["status"], "replaced")
        self.assertEqual(
            self.connector.read_bytes(self.uri("capability.txt")), b"callable"
        )


class MutationSessionTests(ConnectorFixture):
    def connector_subprocess(self, body: str) -> subprocess.CompletedProcess[str]:
        bootstrap = """\
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[2])
import atlas_connector
profile = atlas_connector.resolve_profile(profile_path=Path(sys.argv[1]))
connector = atlas_connector.LocalFilesystemConnector(profile)
"""
        return subprocess.run(
            [
                sys.executable,
                "-c",
                textwrap.dedent(bootstrap + body),
                str(self.profile_path),
                str(ROOT / "scripts"),
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

    def test_mutation_session_is_reentrant_across_connectors_in_one_process(
        self,
    ) -> None:
        result = self.connector_subprocess(
            """\
other = atlas_connector.LocalFilesystemConnector(profile)
with connector.mutation_session():
    with other.mutation_session():
        print("reentrant")
"""
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "reentrant\n")

    def test_mutation_session_serializes_another_process(self) -> None:
        bootstrap = """\
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[2])
import atlas_connector
profile = atlas_connector.resolve_profile(profile_path=Path(sys.argv[1]))
connector = atlas_connector.LocalFilesystemConnector(profile)
with connector.mutation_session():
    print("locked", flush=True)
    if sys.stdin.readline() != "release\\n":
        raise SystemExit(2)
"""
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                textwrap.dedent(bootstrap),
                str(self.profile_path),
                str(ROOT / "scripts"),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        entered = threading.Event()
        failures: list[BaseException] = []

        def contend() -> None:
            try:
                with self.connector.mutation_session():
                    entered.set()
            except BaseException as error:  # pragma: no cover - asserted below
                failures.append(error)

        try:
            self.assertEqual(process.stdout.readline(), "locked\n")
            contender = threading.Thread(target=contend, daemon=True)
            contender.start()
            self.assertFalse(entered.wait(0.3))
            self.assertIsNotNone(process.stdin)
            process.stdin.write("release\n")
            process.stdin.flush()
            self.assertEqual(process.wait(timeout=5), 0, process.stderr.read())
            contender.join(timeout=5)
            self.assertFalse(contender.is_alive())
            self.assertEqual(failures, [])
            self.assertTrue(entered.is_set())
        finally:
            if process.poll() is None:
                if process.stdin is not None:
                    process.stdin.write("release\n")
                    process.stdin.flush()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()


class TreeDigestAndDeletionTests(ConnectorFixture):
    def test_tree_digest_uses_the_canonical_manifest_tuple(self) -> None:
        self.write_fixture("tree/nested/item.bin", b"ab")
        self.write_fixture("tree/zero.bin", b"")
        self.write_fixture("tree/nested.txt", b"c")
        (self.instance_root / "tree" / "empty").mkdir()
        item_hash = hashlib.sha256(b"ab").hexdigest()
        zero_hash = hashlib.sha256(b"").hexdigest()
        nested_file_hash = hashlib.sha256(b"c").hexdigest()
        manifest = (
            "D\tempty/\n"
            "D\tnested/\n"
            f"F\t{nested_file_hash}\t1\tnested.txt\n"
            f"F\t{item_hash}\t2\tnested/item.bin\n"
            f"F\t{zero_hash}\t0\tzero.bin\n"
        ).encode("utf-8")
        expected = {
            "digest": "sha256:" + hashlib.sha256(manifest).hexdigest(),
            "directories": 2,
            "files": 3,
            "bytes": 3,
        }

        self.assertEqual(self.connector.digest_tree(self.uri("tree")), expected)

    def test_tree_digest_and_delete_reject_symlink_and_special_members(self) -> None:
        self.write_fixture("link-tree/plain.txt", b"plain")
        (self.instance_root / "link-tree" / "linked.txt").symlink_to("plain.txt")
        link_uri = self.uri("link-tree")
        link_error = self.assert_rejected(lambda: self.connector.digest_tree(link_uri))
        self.assertIn("symlink", str(link_error).lower())
        link_request = self.delete_request(link_uri, {"digest": "sha256:" + "1" * 64})
        delete_link_error = self.assert_rejected(
            lambda: self.connector.delete_tree(link_uri, **link_request)
        )
        self.assertIn("symlink", str(delete_link_error).lower())
        self.assertEqual(
            self.connector.read_bytes(self.uri("link-tree/plain.txt")), b"plain"
        )

        special_path = self.instance_root / "special-tree" / "pipe"
        special_path.parent.mkdir()
        os.mkfifo(special_path)
        special_uri = self.uri("special-tree")
        special_error = self.assert_rejected(
            lambda: self.connector.digest_tree(special_uri)
        )
        self.assertIn("special", str(special_error).lower())
        special_request = self.delete_request(
            special_uri, {"digest": "sha256:" + "2" * 64}
        )
        delete_special_error = self.assert_rejected(
            lambda: self.connector.delete_tree(special_uri, **special_request)
        )
        self.assertIn("special", str(delete_special_error).lower())

    def test_delete_tree_rejects_traversal_approval_mismatch_and_digest_drift(
        self,
    ) -> None:
        outside = self.instance_root.parent / "outside"
        outside.mkdir()
        (outside / "file.txt").write_bytes(b"outside")
        outside_hash = hashlib.sha256(b"outside").hexdigest()
        traversal = "vault://atlas/../outside"
        traversal_digest = {
            "digest": "sha256:"
            + hashlib.sha256(
                f"F\t{outside_hash}\t7\tfile.txt\n".encode("utf-8")
            ).hexdigest()
        }
        traversal_request = self.delete_request(traversal, traversal_digest)
        traversal_error = self.assert_rejected(
            lambda: self.connector.delete_tree(traversal, **traversal_request)
        )
        self.assertIn("traversal", str(traversal_error).lower())
        self.assertEqual((outside / "file.txt").read_bytes(), b"outside")

        self.write_fixture("approval/file.txt", b"initial")
        approval_uri = self.uri("approval")
        approval_digest = self.connector.digest_tree(approval_uri)
        mismatch = self.delete_request(approval_uri, approval_digest)
        mismatch["approval"] += " altered"
        approval_error = self.assert_rejected(
            lambda: self.connector.delete_tree(approval_uri, **mismatch)
        )
        self.assertIn("approval", str(approval_error).lower())
        self.assertEqual(self.connector.digest_tree(approval_uri), approval_digest)

        self.write_fixture("drift/file.txt", b"before")
        drift_uri = self.uri("drift")
        old_digest = self.connector.digest_tree(drift_uri)
        revision = self.connector.revision(self.uri("drift/file.txt"))
        self.connector.conditional_replace(
            self.uri("drift/file.txt"), revision, b"after"
        )
        drift_error = self.assert_rejected(
            lambda: self.connector.delete_tree(
                drift_uri, **self.delete_request(drift_uri, old_digest)
            )
        )
        self.assertIn("digest", str(drift_error).lower())
        self.assertEqual(
            self.connector.read_bytes(self.uri("drift/file.txt")), b"after"
        )

    def test_delete_tree_quarantines_deterministically_and_resumes_only_exact_request(
        self,
    ) -> None:
        self.write_fixture("delete-me/blocked/record.txt", b"preserve-until-erased")
        target_uri = self.uri("delete-me")
        target_digest = self.connector.digest_tree(target_uri)
        request = self.delete_request(target_uri, target_digest)
        blocked = self.instance_root / "delete-me" / "blocked"
        blocked.chmod(0o500)
        quarantine_path: Path | None = None
        try:
            first = self.connector.delete_tree(target_uri, **request)
            self.assertEqual(first["status"], "quarantined-not-erased")
            quarantine_uri = first["quarantine_uri"]
            self.assertTrue(quarantine_uri.startswith("vault://atlas/"))
            self.assertNotIn(str(self.instance_root), json.dumps(first, sort_keys=True))
            relative_quarantine = quarantine_uri.removeprefix("vault://atlas/")
            quarantine_path = self.instance_root.joinpath(
                *PurePosixPath(relative_quarantine).parts
            )
            self.assertEqual(quarantine_path.parent, self.instance_root)
            self.assertEqual(self.connector.digest_tree(quarantine_uri), target_digest)
            self.assert_rejected(lambda: self.connector.digest_tree(target_uri))

            wrong_resume = dict(request)
            wrong_resume["report_revision"] = "sha256:" + "e" * 64
            resume_error = self.assert_rejected(
                lambda: self.connector.delete_tree(target_uri, **wrong_resume)
            )
            self.assertIn("resume", str(resume_error).lower())
            self.assertEqual(self.connector.digest_tree(quarantine_uri), target_digest)

            (quarantine_path / "blocked").chmod(0o700)
            resumed = self.connector.delete_tree(target_uri, **request)
            self.assertEqual(resumed["status"], "deleted")
            self.assertEqual(resumed["quarantine_uri"], quarantine_uri)
            self.assert_rejected(lambda: self.connector.digest_tree(target_uri))
            self.assert_rejected(lambda: self.connector.digest_tree(quarantine_uri))
        finally:
            if quarantine_path is not None:
                blocked_after_rename = quarantine_path / "blocked"
                if blocked_after_rename.exists():
                    blocked_after_rename.chmod(0o700)
            elif blocked.exists():
                blocked.chmod(0o700)


if __name__ == "__main__":
    unittest.main()
