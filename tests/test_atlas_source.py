from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_source  # noqa: E402
import atlas_state  # noqa: E402
import atlas_url  # noqa: E402


URL = "https://example.com/promoted-source"
SOURCE_ID = atlas_url.source_id_for(URL)
PAYLOAD = "Primary source payload.\n"
CONTENT_HASH = atlas_source.sha256(PAYLOAD.encode())
OLD_PAYLOAD = "Old source payload.\n"
OLD_HASH = atlas_source.sha256(OLD_PAYLOAD.encode())
ARTIFACT_PATH = (
    "summaries/sources/artifacts/2026/2026-07/"
    f"2026-07-19--{SOURCE_ID}--promoted-source.md"
)


def artifact(
    *,
    payload: str = PAYLOAD,
    source_seq: int = 99,
    first_seen: str = "2026-07-19",
    routing_status: str = "unrouted",
    routed_at: str = "",
    acquired_by: str = "manual",
    acquisition_run: str = "staged-run",
    marker: str = "Selected staged semantics.",
) -> str:
    content_hash = atlas_source.sha256(payload.encode())
    strings = {
        "note_type": "source-summary",
        "managed_by": "atlas",
        "source_id": SOURCE_ID,
        "canonical_url": URL,
        "source_kind": "article",
        "title": "Promoted source",
        "author": "Example author",
        "publisher": "Example publisher",
        "published": "2026-07-18",
        "primary_domain": "",
        "routing_status": routing_status,
        "routed_at": routed_at,
        "first_seen": first_seen,
        "last_checked": "2026-07-19",
        "last_summarized": "2026-07-19",
        "refresh_after": "2027-07-19",
        "content_hash": content_hash,
        "acquired_by": acquired_by,
        "acquisition_run": acquisition_run,
        "coverage": "complete",
        "confidence": "high",
        "evidence_strength": "high",
        "practicality": "high",
        "stability": "stable",
        "reuse_value": "high",
        "recommended_posture": "trial",
    }
    arrays = {"subdomains", "secondary_domains", "canonical_tags", "candidate_terms"}
    values: dict[str, str] = {}
    for key in atlas_source.FRONTMATTER_KEYS:
        if key == "schema_version":
            values[key] = "1"
        elif key == "source_seq":
            values[key] = str(source_seq)
        elif key in arrays:
            values[key] = "[]"
        else:
            values[key] = atlas_source.quoted(strings[key])
    body = f"""# Promoted source

**Source**: [Promoted source]({URL})  
**Source ID**: `{SOURCE_ID}`  
**Source seq**: `{source_seq}`  
**Kind**: `article`  
**Author**: Example author  
**Publisher**: Example publisher  
**Published**: 2026-07-18  
**First seen**: {first_seen}  
**Last checked**: 2026-07-19  
**Last summarized**: 2026-07-19  
**Refresh after**: 2027-07-19  
**Route status**: `{routing_status}`

> **TL;DR**: {marker}

## Assessment

{marker}

## Key points

- {marker}

## Evidence / examples

- Heading: {marker}

## Caveats / open questions

- None stated.

## Reuse cues

- What does the source contribute?

## Links

- Canonical: {URL}
"""
    return atlas_source.render_artifact(values, body)


def evidence(payload: str = PAYLOAD, *, first_seen: str = "2026-07-19") -> dict[str, object]:
    return {
        "version": 1,
        "canonical_url": URL,
        "source_urls": [URL],
        "allowed_urls": [URL],
        "media": [],
        "payload_text": payload,
        "fetched_at": first_seen,
    }


def source_event(*, payload: str = PAYLOAD, first_seen: str = "2026-07-19") -> dict[str, object]:
    return {
        "type": "source-upsert",
        "source_id": SOURCE_ID,
        "canonical_url": URL,
        "artifact": ARTIFACT_PATH,
        "first_seen": first_seen,
        "checked_on": "2026-07-19",
        "summarized_on": "2026-07-19",
        "content_hash": atlas_source.sha256(payload.encode()),
        "refresh_after": "2027-07-19",
    }


def source_state(
    *,
    payload: str = PAYLOAD,
    created: bool,
    source_seq: int = 1,
    first_seen: str = "2026-07-19",
    route_status: str = "unrouted",
) -> dict[str, object]:
    return {
        "created": created,
        "content_changed": created or payload != OLD_PAYLOAD,
        "source_seq": source_seq,
        "source_id": SOURCE_ID,
        "canonical_url": URL,
        "artifact": ARTIFACT_PATH,
        "first_seen": first_seen,
        "content_hash": atlas_source.sha256(payload.encode()),
        "route_status": route_status,
        "status": "active",
    }


class LocalConnector:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.failure: tuple[str, str, bool] | None = None
        self.failed = False

    def inject(self, operation: str, path_fragment: str, *, after: bool = False) -> None:
        self.failure = (operation, path_fragment, after)
        self.failed = False

    def _path(self, value: str) -> Path:
        path = self.root / value
        resolved_parent = path.parent.resolve()
        if not resolved_parent.is_relative_to(self.root.resolve()):
            raise OSError("path escapes connector root")
        return path

    def _fail(self, operation: str, value: str, *, after: bool) -> None:
        if self.failure is None or self.failed:
            return
        expected_operation, fragment, expected_after = self.failure
        if (operation, after) == (expected_operation, expected_after) and fragment in value:
            self.failed = True
            raise OSError(f"injected {operation} failure: {value}")

    def read(self, value: str) -> bytes | None:
        path = self._path(value)
        return path.read_bytes() if path.is_file() else None

    def create(self, value: str, data: bytes) -> None:
        self._fail("create", value, after=False)
        path = self._path(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
        self._fail("create", value, after=True)

    def write(self, value: str, data: bytes) -> None:
        self._fail("write", value, after=False)
        path = self._path(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self._fail("write", value, after=True)

    def delete(self, value: str) -> None:
        self._fail("delete", value, after=False)
        path = self._path(value)
        if path.exists():
            path.unlink()
        self._fail("delete", value, after=True)


class AtlasSourceTests(unittest.TestCase):
    def test_new_merge_injects_reducer_identity_and_replays_byte_identically(self) -> None:
        merged = atlas_source.merge_artifact(
            artifact(),
            evidence(),
            source_event(),
            source_state(created=True),
        )
        parsed = atlas_source.parse_artifact(merged)
        self.assertEqual(atlas_source.scalar(parsed.values, "source_id"), SOURCE_ID)
        self.assertEqual(atlas_source.scalar(parsed.values, "source_seq"), "1")
        self.assertEqual(atlas_source.scalar(parsed.values, "routing_status"), "unrouted")
        self.assertEqual(atlas_source.scalar(parsed.values, "routed_at"), "")
        self.assertIn("Selected staged semantics.", parsed.body)
        self.assertEqual(
            merged,
            atlas_source.merge_artifact(
                artifact(), evidence(), source_event(), source_state(created=True)
            ),
        )
        self.assertEqual(list(parsed.values), list(atlas_source.FRONTMATTER_KEYS))
        self.assertNotIn("\r", merged)
        self.assertTrue(merged.endswith("\n"))

    def test_existing_same_hash_replaces_semantics_and_preserves_living_provenance(self) -> None:
        living = artifact(
            source_seq=7,
            first_seen="2026-01-02",
            routing_status="routed",
            routed_at="2026-02-03",
            acquired_by="acquisition-run",
            acquisition_run="original-run",
            marker="Old living semantics.",
        )
        merged = atlas_source.merge_artifact(
            artifact(marker="Corrected staged semantics."),
            evidence(),
            source_event(first_seen="2026-01-02"),
            source_state(
                created=False,
                source_seq=7,
                first_seen="2026-01-02",
                route_status="routed",
            ),
            living_artifact_text=living,
        )
        parsed = atlas_source.parse_artifact(merged)
        self.assertIn("Corrected staged semantics.", parsed.body)
        self.assertNotIn("Old living semantics.", parsed.body)
        self.assertEqual(atlas_source.scalar(parsed.values, "source_seq"), "7")
        self.assertEqual(atlas_source.scalar(parsed.values, "first_seen"), "2026-01-02")
        self.assertEqual(atlas_source.scalar(parsed.values, "acquired_by"), "acquisition-run")
        self.assertEqual(atlas_source.scalar(parsed.values, "acquisition_run"), "original-run")
        self.assertEqual(atlas_source.scalar(parsed.values, "routing_status"), "routed")
        self.assertEqual(atlas_source.scalar(parsed.values, "routed_at"), "2026-02-03")

    def test_changed_hash_requires_fresh_capture_and_resets_routing(self) -> None:
        living = artifact(
            payload=OLD_PAYLOAD,
            source_seq=7,
            first_seen="2026-01-02",
            routing_status="routed",
            routed_at="2026-02-03",
            acquired_by="acquisition-run",
            acquisition_run="original-run",
            marker="Old living semantics.",
        )
        kwargs = {
            "staged_artifact_text": artifact(marker="Fresh selected semantics."),
            "evidence_bundle": evidence(),
            "event": source_event(first_seen="2026-01-02"),
            "source_state": source_state(
                created=False,
                source_seq=7,
                first_seen="2026-01-02",
                route_status="unrouted",
            ),
            "living_artifact_text": living,
        }
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.merge_artifact(**kwargs)
        merged = atlas_source.merge_artifact(**kwargs, fresh_capture=True)
        parsed = atlas_source.parse_artifact(merged)
        self.assertEqual(atlas_source.scalar(parsed.values, "routing_status"), "unrouted")
        self.assertEqual(atlas_source.scalar(parsed.values, "routed_at"), "")
        self.assertEqual(atlas_source.scalar(parsed.values, "acquired_by"), "acquisition-run")
        self.assertIn("Fresh selected semantics.", parsed.body)

    def test_merge_normalizes_block_sequence_frontmatter(self) -> None:
        staged = artifact().replace(
            "candidate_terms: []",
            "candidate_terms:\n  - ChromaFs\n  - 'virtual docs'",
        )
        merged = atlas_source.merge_artifact(
            staged, evidence(), source_event(), source_state(created=True)
        )
        self.assertIn('candidate_terms: ["ChromaFs","virtual docs"]', merged)

    def test_merge_accepts_explicit_hash_for_bounded_payload(self) -> None:
        bounded = evidence("bounded model-visible payload")
        bounded["content_hash"] = CONTENT_HASH
        bounded["payload_projection"] = True
        merged = atlas_source.merge_artifact(
            artifact(), bounded, source_event(), source_state(created=True)
        )
        self.assertEqual(
            atlas_source.scalar(atlas_source.parse_artifact(merged).values, "content_hash"),
            CONTENT_HASH,
        )

        bounded["content_hash"] = "invalid"
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.merge_artifact(
                artifact(), bounded, source_event(), source_state(created=True)
            )

    def test_evidence_identity_projection_matrix(self) -> None:
        # Matching payload-only hash
        self.assertEqual(
            atlas_source.resolve_effective_content_hash(evidence()),
            CONTENT_HASH,
        )

        # No explicit hash, projection true
        bad = evidence()
        bad["payload_projection"] = True
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.resolve_effective_content_hash(bad)

        # Explicit matching hash, projection omitted
        matching = evidence()
        matching["content_hash"] = CONTENT_HASH
        self.assertEqual(atlas_source.resolve_effective_content_hash(matching), CONTENT_HASH)

        # Explicit matching hash, projection false
        matching["payload_projection"] = False
        self.assertEqual(atlas_source.resolve_effective_content_hash(matching), CONTENT_HASH)

        # Explicit matching hash, projection true
        matching["payload_projection"] = True
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.resolve_effective_content_hash(matching)

        complete = "c" * 64
        # Explicit mismatching hash, projection omitted
        projected = evidence("bounded model-visible payload")
        projected["content_hash"] = complete
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.resolve_effective_content_hash(projected)

        # Explicit mismatching hash, projection false
        projected["payload_projection"] = False
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.resolve_effective_content_hash(projected)

        # Explicit mismatching hash, projection true
        projected["payload_projection"] = True
        self.assertEqual(atlas_source.resolve_effective_content_hash(projected), complete)

        # Non-boolean projection
        for value in ("true", 1, 0):
            bad_type = evidence()
            bad_type["payload_projection"] = value
            with self.assertRaises(atlas_source.SourceError):
                atlas_source.resolve_effective_content_hash(bad_type)

        # Malformed explicit hash
        bad_hash = evidence()
        bad_hash["content_hash"] = "not-a-hash"
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.resolve_effective_content_hash(bad_hash)

        # merge-artifact rejects invalid projection cases
        invalid_merge = evidence("bounded model-visible payload")
        invalid_merge["content_hash"] = CONTENT_HASH
        # missing projection while hashes differ
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.merge_artifact(
                artifact(), invalid_merge, source_event(), source_state(created=True)
            )

    def test_merge_rejects_staged_evidence_event_identity_disagreement(self) -> None:
        bad = evidence()
        bad["payload_text"] = "different payload"
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.merge_artifact(
                artifact(), bad, source_event(), source_state(created=True)
            )

    def test_route_renderer_changes_only_route_fields_and_sets_checked_date(self) -> None:
        original = artifact()
        event = {
            "type": "route-upsert",
            "source_id": SOURCE_ID,
            "content_hash": CONTENT_HASH,
            "checked_on": "2026-07-20",
            "outcome": "no-topic-match",
            "edges": [],
        }
        rendered = atlas_source.render_route_artifact(original, event, "no-topic-match")
        before = atlas_source.parse_artifact(original)
        after = atlas_source.parse_artifact(rendered)
        for key in atlas_source.FRONTMATTER_KEYS:
            if key not in {"routing_status", "routed_at"}:
                self.assertEqual(before.values[key], after.values[key], key)
        self.assertEqual(atlas_source.scalar(after.values, "routing_status"), "no-topic-match")
        self.assertEqual(atlas_source.scalar(after.values, "routed_at"), "2026-07-20")
        route_line = re_line(after.body, "**Route status**:")
        self.assertEqual(route_line, "**Route status**: `no-topic-match`")

    def test_merge_cli_is_deterministic(self) -> None:
        payload = {
            "version": 1,
            "staged_artifact_text": artifact(),
            "evidence_bundle": evidence(),
            "event": source_event(),
            "source_state": source_state(created=True),
            "living_artifact_text": None,
            "fresh_capture": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "scripts/atlas_source.py"),
                "merge-artifact",
                "--input",
                str(path),
            ]
            first = subprocess_run(command)
            second = subprocess_run(command)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, b"")
        self.assertTrue(json.loads(first.stdout)["ok"])

    def test_event_record_and_transaction_ids_are_hash_bound(self) -> None:
        event = source_event()
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=event,
            route_decision=None,
            promotion_map_sha256="a" * 64,
            promotion_row_sha256="b" * 64,
            require_promotion=True,
        )
        targets = (
            atlas_source.TransactionTarget(ARTIFACT_PATH, None, b"artifact"),
            atlas_source.TransactionTarget(atlas_state.MANIFEST_PATH, b"old", b"new"),
        )
        first = atlas_source.build_transaction_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        second = atlas_source.build_transaction_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        self.assertEqual(first, second)
        self.assertRegex(first.transaction_id, r"^[0-9a-f]{16}-a000000$")
        terminal = atlas_source.canonical_json(
            {
                "version": 1,
                "status": "rolled-back",
                "intent_sha256": atlas_source.sha256(atlas_source.canonical_json(first.intent)),
            }
        )
        successor = atlas_source.build_successor_plan(
            first,
            event_path="events/source-upsert.json",
            event_record=record,
            terminal_record=terminal,
        )
        self.assertEqual(successor.base_transaction_id, first.base_transaction_id)
        self.assertEqual(successor.predecessor_sha256, atlas_source.sha256(terminal))
        self.assertTrue(successor.transaction_id.endswith("-a000001"))
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.build_successor_plan(
                first,
                event_path="events/source-upsert.json",
                event_record=record,
                terminal_record=b"malformed\n",
            )

    def test_transactions_use_actual_connector_paths_commit_and_recover(self) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        paths = (ARTIFACT_PATH, atlas_state.RELATIONS_PATH, atlas_state.TOPICS_PATH, atlas_state.MANIFEST_PATH)
        inputs = (None, b"relations-old", b"topics-old", b"manifest-old")
        outputs = (b"artifact-new", b"relations-new", b"topics-new", b"manifest-new")
        targets = tuple(
            atlas_source.TransactionTarget(path, before, after)
            for path, before, after in zip(paths, inputs, outputs, strict=True)
        )
        plan = atlas_source.build_transaction_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            for path, value in zip(paths, inputs, strict=True):
                if value is not None:
                    connector.write(path, value)
            self.assertEqual(
                atlas_source.execute_transaction(connector, "transactions", plan),
                "applied",
            )
            for path, expected in zip(paths, outputs, strict=True):
                self.assertEqual(connector.read(path), expected)
            self.assertEqual(
                atlas_source.recover_transaction(connector, "transactions", plan),
                "applied",
            )
            base = f"transactions/{plan.transaction_id}"
            self.assertIsNotNone(connector.read(f"{base}/intent.json"))
            self.assertIsNotNone(connector.read(f"{base}/prepared.json"))
            self.assertIsNotNone(connector.read(f"{base}/applied.json"))
            for index in range(4):
                self.assertIsNotNone(connector.read(f"{base}/backups/{index:06d}.json"))
                self.assertIsNotNone(connector.read(f"{base}/progress/{index:06d}.json"))

    def test_transaction_failures_restore_or_commit_deterministically(self) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        paths = (ARTIFACT_PATH, atlas_state.RELATIONS_PATH, atlas_state.TOPICS_PATH, atlas_state.MANIFEST_PATH)
        inputs = (None, b"relations-old", b"topics-old", b"manifest-old")
        outputs = (b"artifact-new", b"relations-new", b"topics-new", b"manifest-new")
        targets = tuple(
            atlas_source.TransactionTarget(path, before, after)
            for path, before, after in zip(paths, inputs, outputs, strict=True)
        )
        plan = atlas_source.build_transaction_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        failures = (
            ("create", "intent.json", True, "aborted"),
            ("create", "backups/000000.json", True, "aborted"),
            ("create", "backups/000001.json", True, "aborted"),
            ("create", "backups/000002.json", True, "aborted"),
            ("create", "backups/000003.json", True, "aborted"),
            ("create", "prepared.json", True, "rolled-back"),
            ("write", ARTIFACT_PATH, False, "rolled-back"),
            ("write", ARTIFACT_PATH, True, "rolled-back"),
            ("write", atlas_state.RELATIONS_PATH, True, "rolled-back"),
            ("write", atlas_state.TOPICS_PATH, True, "rolled-back"),
            ("write", atlas_state.MANIFEST_PATH, True, "applied"),
            ("create", "progress/000003.json", True, "applied"),
            ("create", "applied.json", True, "applied"),
        )
        for operation, fragment, after, expected_status in failures:
            with self.subTest(operation=operation, fragment=fragment, after=after):
                with tempfile.TemporaryDirectory() as directory:
                    connector = LocalConnector(Path(directory))
                    for path, value in zip(paths, inputs, strict=True):
                        if value is not None:
                            connector.write(path, value)
                    connector.inject(operation, fragment, after=after)
                    status = atlas_source.execute_transaction(connector, "transactions", plan)
                    self.assertEqual(status, expected_status)
                    expected_values = outputs if status == "applied" else inputs
                    for path, expected in zip(paths, expected_values, strict=True):
                        self.assertEqual(connector.read(path), expected)

    def test_zero_target_collision_and_manual_conflict(self) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        no_op = atlas_source.build_transaction_plan(
            event_path="events/source-upsert.json", event_record=record, targets=()
        )
        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            self.assertEqual(
                atlas_source.execute_transaction(connector, "transactions", no_op),
                "no-op",
            )

        target = atlas_source.TransactionTarget(ARTIFACT_PATH, None, b"new")
        plan = atlas_source.build_transaction_plan(
            event_path="events/source-upsert.json", event_record=record, targets=(target,)
        )
        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            base = f"transactions/{plan.transaction_id}"
            connector.create(
                f"{base}/intent.json",
                atlas_source.canonical_json(plan.intent),
            )
            self.assertEqual(
                atlas_source.recover_transaction(connector, "transactions", plan),
                "rolled-back",
            )
            self.assertIsNotNone(connector.read(f"{base}/backups/000000.json"))
            self.assertIsNotNone(connector.read(f"{base}/prepared.json"))
            self.assertIsNotNone(connector.read(f"{base}/rolled-back.json"))

        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            base = f"transactions/{plan.transaction_id}"
            connector.create(f"{base}/intent.json", b"collision\n")
            with self.assertRaises(atlas_source.SourceError):
                atlas_source.execute_transaction(connector, "transactions", plan)

        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            base = f"transactions/{plan.transaction_id}"
            intent_raw = atlas_source.canonical_json(plan.intent)
            connector.create(f"{base}/intent.json", intent_raw)
            backup = atlas_source.canonical_json(
                {
                    "version": 1,
                    "path": ARTIFACT_PATH,
                    "input_sha256": None,
                    "input_base64": None,
                }
            )
            connector.create(f"{base}/backups/000000.json", backup)
            prepared = atlas_source.canonical_json(
                {
                    "version": 1,
                    "intent_sha256": atlas_source.sha256(intent_raw),
                    "backup_sha256s": [atlas_source.sha256(backup)],
                }
            )
            connector.create(f"{base}/prepared.json", prepared)
            connector.write(ARTIFACT_PATH, b"unexpected")
            self.assertEqual(
                atlas_source.recover_transaction(connector, "transactions", plan),
                "manual-conflict",
            )
            self.assertIsNotNone(connector.read(f"{base}/manual-conflict.json"))


def re_line(text: str, prefix: str) -> str:
    return next(line for line in text.splitlines() if line.startswith(prefix))


def subprocess_run(command: list[str]):
    import subprocess

    return subprocess.run(command, check=False, capture_output=True)


if __name__ == "__main__":
    unittest.main()
