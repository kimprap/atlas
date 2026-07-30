from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import atlas_connector  # noqa: E402
import atlas_tool  # noqa: E402
import atlas_state  # noqa: E402


MANIFEST_URI = "vault://atlas/summaries/sources/MANIFEST.md"
TOPICS_URI = "vault://atlas/summaries/registry/TOPICS.md"
RELATIONS_URI = "vault://atlas/summaries/registry/RELATIONS.md"
INDEX_URI = "vault://atlas/summaries/research/test/topics/test-topic/INDEX.md"
REPORT_URI = "vault://atlas/summaries/sources/runs/2026/2026-07/report.md"
TOPIC_ID = "test-topic"
SOURCE_A_URL = "https://example.test/synthetic-a"
SOURCE_B_URL = "https://example.test/synthetic-b"
SOURCE_C_URL = "https://example.test/synthetic-c"

OPERATIONS = tuple(
    sorted(
        {
            "vault.read",
            "vault.read_json",
            "vault.list",
            "vault.hash",
            "vault.write_json",
            "vault.conditional_replace",
            "vault.digest_tree",
            "vault.delete_tree",
            "url.normalize",
            "discovery.normalize",
            "quality.validate_proposal",
            "quality.validate_summary",
            "quality.prepare_calibration",
            "quality.validate_calibration",
            "quality.validate_fresh_assessment",
            "state.validate",
            "state.reduce",
            "source.render_summary",
            "source.merge_artifact",
            "source.render_route_artifact",
            "source.lookup",
            "source.snapshot_active",
            "effect.execute",
            "effect.recover",
            "transaction.execute",
            "transaction.recover",
            "transaction.successor",
            "refresh.execute",
            "refresh.recover",
        }
    )
)

MANIFEST_HEADER = (
    "Source seq",
    "Source ID",
    "Canonical URL",
    "Artifact",
    "First seen",
    "Last checked",
    "Last summarized",
    "Content hash",
    "Refresh after",
    "Route status",
    "Status",
)
TOPICS_HEADER = (
    "Topic ID",
    "Topic path",
    "Domain",
    "Subdomain",
    "Canonical title",
    "Aliases",
    "Canonical tags",
    "Include terms",
    "Exclude terms",
    "Freshness state",
    "Dirty count",
    "Pending edge IDs",
    "Newest pending source seq",
    "Last synthesized",
    "Source watermark",
    "Refresh model",
)
RELATIONS_HEADER = (
    "Edge ID",
    "Source seq",
    "Source ID",
    "Source artifact",
    "Source content hash",
    "Topic ID",
    "Relation",
    "Impact",
    "Confidence",
    "Status",
    "Created",
    "Applied in pass",
    "Notes",
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def source_id(url: str) -> str:
    return sha256_text(url)[:12]


def artifact_path(url: str) -> str:
    return (
        "summaries/sources/artifacts/2026/2026-07/"
        f"2026-07-28--{source_id(url)}--synthetic.md"
    )


def artifact_uri(url: str) -> str:
    return f"vault://atlas/{artifact_path(url)}"


def artifact_text(url: str, sequence: int, *, route_status: str = "unrouted") -> str:
    payload = f"synthetic payload {sequence}\n"
    content_hash = sha256_text(payload)
    return "\n".join(
        (
            "---",
            "schema_version: 1",
            "note_type: source-summary",
            "managed_by: atlas",
            f"source_id: {source_id(url)}",
            f"source_seq: {sequence}",
            f"canonical_url: {url}",
            'source_kind: "article"',
            'title: "Synthetic source"',
            'author: ""',
            'publisher: ""',
            'published: "2026-07-28"',
            'primary_domain: ""',
            "subdomains: []",
            "secondary_domains: []",
            "canonical_tags: []",
            "candidate_terms: []",
            f'routing_status: "{route_status}"',
            'routed_at: ""',
            'first_seen: "2026-07-28"',
            'last_checked: "2026-07-28"',
            'last_summarized: "2026-07-28"',
            'refresh_after: "2027-07-28"',
            f"content_hash: {content_hash}",
            'acquired_by: "manual"',
            'acquisition_run: ""',
            'coverage: "complete"',
            'confidence: "high"',
            'evidence_strength: "high"',
            'practicality: "high"',
            'stability: "stable"',
            'reuse_value: "high"',
            'recommended_posture: "trial"',
            "---",
            "",
            "# Synthetic source",
            "",
        )
    )


def table(header: tuple[str, ...], rows: list[list[str]]) -> str:
    rendered = [
        "---",
        "schema_version: 1",
        "---",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    rendered.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(rendered) + "\n"


def manifest_row(url: str, sequence: int, *, status: str = "active") -> list[str]:
    return [
        str(sequence),
        source_id(url),
        url,
        artifact_path(url),
        "2026-07-28",
        "2026-07-28",
        "2026-07-28",
        sha256_text(f"synthetic payload {sequence}\n"),
        "2027-07-28",
        "unrouted",
        status,
    ]


def manifest_text(rows: list[list[str]]) -> str:
    return table(MANIFEST_HEADER, rows)


def relation_id(url: str) -> str:
    content_hash = sha256_text("synthetic payload 1\n")
    return f"edge--{source_id(url)}--{TOPIC_ID}--{content_hash[:8]}"


def relation_row(url: str = SOURCE_A_URL) -> list[str]:
    return [
        relation_id(url),
        "1",
        source_id(url),
        artifact_path(url),
        sha256_text("synthetic payload 1\n"),
        TOPIC_ID,
        "direct",
        "high",
        "high",
        "pending",
        "2026-07-28",
        "",
        "Verifier: synthetic — synthetic [relation=direct; impact=high]",
    ]


def topics_text(
    *, pending_edge_ids: list[str] | None = None, state: str = "current"
) -> str:
    pending_edge_ids = pending_edge_ids or []
    return table(
        TOPICS_HEADER,
        [
            [
                TOPIC_ID,
                "summaries/research/test/topics/test-topic/INDEX.md",
                "test",
                "test-subdomain",
                "Synthetic topic",
                "",
                "",
                "test",
                "",
                state,
                str(len(pending_edge_ids)),
                "; ".join(pending_edge_ids),
                "1" if pending_edge_ids else "",
                "",
                "0",
                "same-as-topic-creation",
            ]
        ],
    )


def relations_text(rows: list[list[str]] | None = None) -> str:
    return table(RELATIONS_HEADER, rows or [])


class TemporaryAtlasProfile:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.vault = self.root / "vault"
        self.profile = self.vault / "config" / "profiles" / "local.yml"
        self.instance = self.vault / "instances" / "atlas"

    def __enter__(self) -> TemporaryAtlasProfile:
        self.profile.parent.mkdir(parents=True)
        self.instance.mkdir(parents=True)
        self.profile.write_text(
            "\n".join(
                (
                    "profile: local",
                    "instance: atlas",
                    "connector: local-fs",
                    "local_fs:",
                    "  root: instances/atlas",
                    "",
                )
            ),
            encoding="utf-8",
        )
        self.put(MANIFEST_URI, manifest_text([manifest_row(SOURCE_A_URL, 1)]))
        self.put(TOPICS_URI, topics_text())
        self.put(RELATIONS_URI, relations_text())
        self.put(artifact_uri(SOURCE_A_URL), artifact_text(SOURCE_A_URL, 1))
        self.put(INDEX_URI, "# Synthetic index\n")
        self.put(REPORT_URI, "# Synthetic report\n")
        return self

    def __exit__(self, *_: object) -> None:
        self._temporary.cleanup()

    def connector(self) -> Any:
        return atlas_connector.LocalFilesystemConnector(
            atlas_connector.resolve_profile(profile_path=self.profile)
        )

    def put(self, uri: str, text: str) -> None:
        relative = uri.removeprefix("vault://atlas/")
        destination = self.instance / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")


@contextmanager
def temporary_profile() -> Iterator[TemporaryAtlasProfile]:
    with TemporaryAtlasProfile() as fixture:
        yield fixture


def request(op: str, args: dict[str, Any]) -> dict[str, Any]:
    return {"version": 1, "op": op, "args": args}


class InterruptingConnector:
    def __init__(self, inner: Any, *, path: str, after_write: bool) -> None:
        self._inner = inner
        self._path = path
        self._after_write = after_write
        self._interrupted = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
        path = str(args[0] if args else kwargs["path"])
        should_interrupt = not self._interrupted and path in {
            self._path,
            self._path.removeprefix("vault://atlas/"),
        }
        if should_interrupt and not self._after_write:
            self._interrupted = True
            raise OSError(f"synthetic interrupted replacement: {path}")
        result = self._inner.conditional_replace(*args, **kwargs)
        if should_interrupt:
            self._interrupted = True
            raise OSError(f"synthetic interrupted replacement: {path}")
        return result


class DriftingConnector:
    def __init__(self, inner: Any, *, path: str) -> None:
        self._inner = inner
        self._path = path
        self._drifted = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
        path = str(args[0] if args else kwargs["path"])
        if not self._drifted and path == self._path:
            self._drifted = True
            revision = self._inner.revision(path)
            self._inner.conditional_replace(path, revision, b"manual conflict\n")
            raise OSError(f"synthetic conflicting replacement: {path}")
        return self._inner.conditional_replace(*args, **kwargs)


class RecordingReadOnlyConnector:
    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.read_log: list[str] = []

    def capabilities(self) -> dict[str, Any]:
        capabilities = dict(self._inner.capabilities())
        capabilities["conditional_replace"] = "unavailable"
        return capabilities

    def read_bytes(self, uri: str) -> bytes:
        if uri != MANIFEST_URI:
            raise AssertionError(f"unexpected read: {uri}")
        self.read_log.append(uri)
        return self._inner.read_bytes(uri)

    def mutation_session(self) -> Any:
        raise AssertionError("source lookup requested a mutation session")


def invoke(
    fixture: TemporaryAtlasProfile,
    op: str,
    *,
    connector: Any | None = None,
    **args: Any,
) -> dict[str, Any]:
    return atlas_tool.execute(
        request(op, args),
        connector=fixture.connector() if connector is None else connector,
    )


def response_findings(response: dict[str, Any]) -> list[tuple[str, str, str]]:
    return [
        (finding["code"], finding["path"], finding["detail"])
        for finding in response["findings"]
    ]


class AtlasToolTests(unittest.TestCase):
    maxDiff = None

    def assert_envelope(
        self, response: dict[str, Any], *, ok: bool, op: str | None
    ) -> None:
        self.assertEqual(set(response), {"version", "ok", "op", "result", "findings"})
        self.assertEqual(response["version"], 1)
        self.assertIs(response["ok"], ok)
        self.assertEqual(response["op"], op)
        self.assertEqual(
            response_findings(response), sorted(response_findings(response))
        )
        if ok:
            self.assertIsInstance(response["result"], dict)
            self.assertEqual(response["findings"], [])
        else:
            self.assertIsNone(response["result"])
            self.assertTrue(response["findings"])

    def revision(self, fixture: TemporaryAtlasProfile, uri: str) -> str:
        response = invoke(fixture, "vault.hash", path=uri)
        self.assert_envelope(response, ok=True, op="vault.hash")
        revision = response["result"]["revision"]
        self.assertRegex(revision, r"^(missing|sha256:[0-9a-f]{64})$")
        return revision

    def read_text(self, fixture: TemporaryAtlasProfile, uri: str) -> str:
        response = invoke(fixture, "vault.read", path=uri)
        self.assert_envelope(response, ok=True, op="vault.read")
        self.assertEqual(set(response["result"]), {"path", "text", "revision"})
        return response["result"]["text"]

    def conditional_replace(
        self,
        fixture: TemporaryAtlasProfile,
        uri: str,
        text: str,
        *,
        expected_revision: str | None = None,
    ) -> dict[str, Any]:
        if expected_revision is None:
            expected_revision = self.revision(fixture, uri)
        response = invoke(
            fixture,
            "vault.conditional_replace",
            path=uri,
            expected_revision=expected_revision,
            text=text,
        )
        self.assert_envelope(response, ok=True, op="vault.conditional_replace")
        self.assertEqual(self.read_text(fixture, uri), text)
        return response

    def transaction_args(
        self,
        fixture: TemporaryAtlasProfile,
        *,
        route_url: str = SOURCE_A_URL,
        output_text: str | None = None,
    ) -> dict[str, Any]:
        route_hash = sha256_text("synthetic payload 1\n")
        target_uri = artifact_uri(route_url)
        event = {
            "type": "route-upsert",
            "source_id": source_id(route_url),
            "content_hash": route_hash,
            "checked_on": "2026-07-28",
            "outcome": "no-topic-match",
            "edges": [],
        }
        event_record = {
            "version": 1,
            "event_type": "route",
            "source_id": source_id(route_url),
            "promotion_map_sha256": None,
            "promotion_row_sha256": None,
            "event": event,
            "route_decision": {"outcome": "no-topic-match", "edges": []},
        }
        return {
            "event_record": event_record,
            "targets": [
                {
                    "path": target_uri,
                    "expected_revision": self.revision(fixture, target_uri),
                    "text": output_text
                    if output_text is not None
                    else artifact_text(route_url, 1, route_status="no-topic-match"),
                }
            ],
        }

    def effect_args(
        self,
        fixture: TemporaryAtlasProfile,
        *,
        effect_id: str,
        with_transactions: bool,
    ) -> dict[str, Any]:
        source_url = SOURCE_B_URL if with_transactions else SOURCE_A_URL
        origin = {"kind": "synthetic-origin", "source_seq": 1}
        origin_sha256 = sha256_text(
            json.dumps(
                origin, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            + "\n"
        )
        effect_core = {
            "effect_id": effect_id,
            "effect_kind": "independent-candidate",
            "candidate_status": "new" if with_transactions else "existing-active",
            "identity": {
                "source_id": source_id(source_url),
                "canonical_url": source_url,
            },
            "origins": [origin],
        }
        effect_sha256 = sha256_text(
            json.dumps(
                effect_core, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            + "\n"
        )
        effect = {**effect_core, "effect_sha256": effect_sha256}
        authority_root = f"vault://atlas/tmp/effect-authority/{effect_id}"
        projection_uri = authority_root + "/projection.json"
        projection = {
            "version": 1,
            "kind": "t11-mutation-projection-v1",
            "effects": [effect],
            "effect_hashes": [effect_sha256],
        }
        projection_write = invoke(
            fixture, "vault.write_json", path=projection_uri, value=projection
        )
        self.assert_envelope(projection_write, ok=True, op="vault.write_json")
        projection_revision = self.revision(fixture, projection_uri)
        approval_uri = authority_root + "/approval.json"
        approval = {
            "version": 1,
            "kind": "projection-approval-v1",
            "projection_uri": projection_uri,
            "projection_revision": projection_revision,
            "projection_whole_byte_sha256": projection_revision.removeprefix("sha256:"),
            "effect_hashes": [effect_sha256],
            "effect_uses": [
                {
                    "effect_id": effect_id,
                    "effect_sha256": effect_sha256,
                    "use_limit": 1,
                    "consumed": False,
                }
            ],
        }
        approval_write = invoke(
            fixture, "vault.write_json", path=approval_uri, value=approval
        )
        self.assert_envelope(approval_write, ok=True, op="vault.write_json")

        transactions: list[dict[str, Any]] = []
        allowed_target_paths: list[str] = []
        if with_transactions:
            documents = {
                "manifest": self.read_text(fixture, MANIFEST_URI),
                "topics": self.read_text(fixture, TOPICS_URI),
                "relations": self.read_text(fixture, RELATIONS_URI),
            }
            content_hash = sha256_text("synthetic payload 2\n")
            source_event = {
                "type": "source-upsert",
                "source_id": source_id(source_url),
                "canonical_url": source_url,
                "artifact": artifact_path(source_url),
                "first_seen": "2026-07-28",
                "checked_on": "2026-07-28",
                "summarized_on": "2026-07-28",
                "content_hash": content_hash,
                "refresh_after": "2027-07-28",
            }
            source_result = atlas_state.reduce_event(documents, source_event)
            self.assertTrue(source_result.ok, source_result.to_dict())
            self.assertEqual(set(source_result.documents), {"manifest"})
            source_artifact = artifact_text(source_url, 2)
            source_manifest = source_result.documents["manifest"]
            transactions.append(
                {
                    "stage": "source",
                    "event_record": {
                        "version": 1,
                        "event_type": "source",
                        "source_id": source_id(source_url),
                        "promotion_map_sha256": None,
                        "promotion_row_sha256": None,
                        "event": source_event,
                        "route_decision": None,
                    },
                    "targets": [
                        {
                            "path": artifact_uri(source_url),
                            "expected_revision": "missing",
                            "text": source_artifact,
                        },
                        {
                            "path": MANIFEST_URI,
                            "expected_revision": self.revision(fixture, MANIFEST_URI),
                            "text": source_manifest,
                        },
                    ],
                }
            )
            routed_documents = {**documents, **source_result.documents}
            route_event = {
                "type": "route-upsert",
                "source_id": source_id(source_url),
                "content_hash": content_hash,
                "checked_on": "2026-07-28",
                "outcome": "no-topic-match",
                "edges": [],
            }
            route_result = atlas_state.reduce_event(routed_documents, route_event)
            self.assertTrue(route_result.ok, route_result.to_dict())
            self.assertEqual(set(route_result.documents), {"manifest"})
            transactions.append(
                {
                    "stage": "route",
                    "event_record": {
                        "version": 1,
                        "event_type": "route",
                        "source_id": source_id(source_url),
                        "promotion_map_sha256": None,
                        "promotion_row_sha256": None,
                        "event": route_event,
                        "route_decision": {
                            "outcome": "no-topic-match",
                            "edges": [],
                        },
                    },
                    "targets": [
                        {
                            "path": artifact_uri(source_url),
                            "expected_revision": "sha256:"
                            + sha256_text(source_artifact),
                            "text": artifact_text(
                                source_url, 2, route_status="no-topic-match"
                            ),
                        },
                        {
                            "path": MANIFEST_URI,
                            "expected_revision": "sha256:"
                            + sha256_text(source_manifest),
                            "text": route_result.documents["manifest"],
                        },
                    ],
                }
            )
            allowed_target_paths = sorted([artifact_uri(source_url), MANIFEST_URI])
        return {
            "authority": {
                "projection_uri": projection_uri,
                "projection_revision": projection_revision,
                "approval_uri": approval_uri,
                "approval_revision": self.revision(fixture, approval_uri),
                "effect_id": effect_id,
                "effect_sha256": effect_sha256,
            },
            "checks": [
                {
                    "path": REPORT_URI,
                    "expected_revision": self.revision(fixture, REPORT_URI),
                }
            ],
            "allowed_target_paths": allowed_target_paths,
            "members": [
                {
                    "member_id": "member-0001",
                    "role": "candidate" if with_transactions else "parent",
                    "origin_sha256": origin_sha256,
                    "context": {"source_url": source_url},
                }
            ],
            "context": {"campaign": "synthetic-effect-test"},
            "transactions": transactions,
            "no_write_code": None if with_transactions else "existing-active-no-op",
            "receipt_root": (f"vault://atlas/tmp/effect-receipts/{effect_id}"),
        }

    def refresh_args(
        self, fixture: TemporaryAtlasProfile, *, pass_uri: str | None = None
    ) -> dict[str, Any]:
        edge_id = relation_id(SOURCE_A_URL)
        pass_uri = pass_uri or (
            "vault://atlas/summaries/research/test/topics/test-topic/passes/"
            "2026-07-28--synthetic.md"
        )
        pass_text = "# Synthetic pass\n"
        index_text = "# Synthetic index\n\n- Synthetic pass\n"
        return {
            "projection": {
                "version": 1,
                "topic_id": TOPIC_ID,
                "edge_ids": [edge_id],
                "manifest_revision": self.revision(fixture, MANIFEST_URI),
                "topics_revision": self.revision(fixture, TOPICS_URI),
                "relations_revision": self.revision(fixture, RELATIONS_URI),
                "index_uri": INDEX_URI,
                "index_revision": self.revision(fixture, INDEX_URI),
                "pass_uri": pass_uri,
                "pass_expected_revision": "missing",
                "pass_sha256": sha256_text(pass_text),
                "index_sha256": sha256_text(index_text),
                "started_at": "2026-07-28",
                "completed_on": "2026-07-28",
                "transaction_root": "vault://atlas/.atlas/refresh/synthetic",
            },
            "pass_text": pass_text,
            "index_text": index_text,
        }

    def prepare_dirty_topic(self, fixture: TemporaryAtlasProfile) -> None:
        edge_id = relation_id(SOURCE_A_URL)
        self.conditional_replace(
            fixture,
            RELATIONS_URI,
            relations_text([relation_row()]),
        )
        self.conditional_replace(
            fixture,
            TOPICS_URI,
            topics_text(pending_edge_ids=[edge_id], state="dirty"),
        )
        self.assert_envelope(
            invoke(fixture, "state.validate"), ok=True, op="state.validate"
        )

    def test_capabilities_are_exact_sorted_truthful_and_logical(self) -> None:
        with temporary_profile() as fixture:
            response = atlas_tool.capabilities(connector=fixture.connector())
            self.assert_envelope(response, ok=True, op="capabilities")
            result = response["result"]
            self.assertEqual(result["adapter"], "atlas-local-fs-cas-v1")
            self.assertEqual(result["logical_root"], "vault://atlas/")
            self.assertEqual(result["operations"], list(OPERATIONS))
            self.assertEqual(result["operations"], sorted(result["operations"]))
            self.assertNotIn(
                str(fixture.instance), json.dumps(response, sort_keys=True)
            )

            write = invoke(
                fixture,
                "vault.write_json",
                path="vault://atlas/tmp/canonical.json",
                value={"z": [3, 2], "a": {"b": True}},
            )
            self.assert_envelope(write, ok=True, op="vault.write_json")
            self.assertEqual(
                self.read_text(fixture, "vault://atlas/tmp/canonical.json"),
                '{"a":{"b":true},"z":[3,2]}\n',
            )

    def test_source_lookup_reads_one_manifest_on_a_read_only_connector(self) -> None:
        with temporary_profile() as fixture:
            connector = RecordingReadOnlyConnector(fixture.connector())
            capabilities = atlas_tool.capabilities(connector=connector)
            self.assert_envelope(capabilities, ok=True, op="capabilities")
            self.assertIn("source.lookup", capabilities["result"]["operations"])

            response = invoke(
                fixture,
                "source.lookup",
                connector=connector,
                url=(" HTTPS://EXAMPLE.TEST/synthetic-a?utm_source=fixture#fragment "),
            )

            self.assert_envelope(response, ok=True, op="source.lookup")
            self.assertEqual(
                response["result"],
                {
                    "canonical_url": SOURCE_A_URL,
                    "manifest_revision": (
                        "sha256:"
                        + sha256_text(manifest_text([manifest_row(SOURCE_A_URL, 1)]))
                    ),
                    "row": {
                        "source_seq": 1,
                        "source_id": source_id(SOURCE_A_URL),
                        "canonical_url": SOURCE_A_URL,
                        "artifact_uri": artifact_uri(SOURCE_A_URL),
                        "first_seen": "2026-07-28",
                        "last_checked": "2026-07-28",
                        "last_summarized": "2026-07-28",
                        "content_hash": sha256_text("synthetic payload 1\n"),
                        "refresh_after": "2027-07-28",
                        "route_status": "unrouted",
                        "status": "active",
                    },
                },
            )
            self.assertEqual(connector.read_log, [MANIFEST_URI])

    def test_source_lookup_returns_unambiguous_absence(self) -> None:
        with temporary_profile() as fixture:
            response = invoke(fixture, "source.lookup", url=SOURCE_B_URL)

            self.assert_envelope(response, ok=True, op="source.lookup")
            self.assertEqual(response["result"]["canonical_url"], SOURCE_B_URL)
            self.assertIsNone(response["result"]["row"])

    def test_source_lookup_returns_archived_row_without_reading_artifact(self) -> None:
        with temporary_profile() as fixture:
            fixture.put(
                MANIFEST_URI,
                manifest_text([manifest_row(SOURCE_B_URL, 7, status="archived")]),
            )
            connector = RecordingReadOnlyConnector(fixture.connector())

            response = invoke(
                fixture,
                "source.lookup",
                connector=connector,
                url=SOURCE_B_URL,
            )

            self.assert_envelope(response, ok=True, op="source.lookup")
            self.assertEqual(response["result"]["row"]["source_seq"], 7)
            self.assertEqual(response["result"]["row"]["status"], "archived")
            self.assertEqual(connector.read_log, [MANIFEST_URI])

    def test_source_lookup_rejects_invalid_url_and_invalid_manifest_utf8(self) -> None:
        with temporary_profile() as fixture:
            invalid_url = invoke(fixture, "source.lookup", url="not a URL")
            self.assert_envelope(invalid_url, ok=False, op="source.lookup")
            self.assertEqual(response_findings(invalid_url)[0][0], "URL_INVALID")
            self.assertEqual(response_findings(invalid_url)[0][1], "args.url")

            manifest_path = fixture.instance / "summaries" / "sources" / "MANIFEST.md"
            manifest_path.write_bytes(b"\xff")
            invalid_utf8 = invoke(fixture, "source.lookup", url=SOURCE_A_URL)
            self.assert_envelope(invalid_utf8, ok=False, op="source.lookup")
            self.assertEqual(
                response_findings(invalid_utf8),
                [
                    (
                        "MANIFEST_UTF8_INVALID",
                        MANIFEST_URI,
                        "manifest is not valid UTF-8",
                    )
                ],
            )

    def test_source_lookup_propagates_manifest_identity_findings(self) -> None:
        with temporary_profile() as fixture:
            row = manifest_row(SOURCE_A_URL, 1)
            row[1] = "ffffffffffff"
            fixture.put(MANIFEST_URI, manifest_text([row]))

            response = invoke(fixture, "source.lookup", url=SOURCE_A_URL)

            self.assert_envelope(response, ok=False, op="source.lookup")
            self.assertEqual(
                response_findings(response)[0][0],
                "MANIFEST_SOURCE_ID_URL_MISMATCH",
            )

    def test_execute_has_exact_envelope_and_non_atlas_json_edit_is_unknown_noop(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(before, ok=True, op="vault.digest_tree")

            malformed = atlas_tool.execute(
                {"version": 2, "op": "vault.read", "args": {}}
            )
            self.assert_envelope(malformed, ok=False, op="vault.read")
            self.assertEqual(response_findings(malformed)[0][0], "VERSION_UNSUPPORTED")

            near_miss = atlas_tool.execute(
                request(
                    "json.edit",
                    {"path": "settings.json", "patch": {"feature": "on"}},
                ),
                connector=fixture.connector(),
            )
            self.assert_envelope(near_miss, ok=False, op="json.edit")
            self.assertEqual(response_findings(near_miss)[0][0], "OP_UNKNOWN")
            self.assertEqual(
                atlas_tool.capabilities(connector=fixture.connector())["result"][
                    "operations"
                ],
                list(OPERATIONS),
            )

            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(after, ok=True, op="vault.digest_tree")
            self.assertEqual(after["result"], before["result"])

    def test_cli_is_canonical_and_maps_validation_binding_and_success_exits(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            env = {**os.environ, "ATLAS_VAULT_PROFILE": str(fixture.profile)}
            command = [sys.executable, str(ROOT / "scripts" / "atlas_tool.py")]

            capabilities = subprocess.run(
                [*command, "capabilities"],
                check=False,
                capture_output=True,
                env=env,
            )
            self.assertEqual(capabilities.returncode, 0, capabilities.stderr)
            self.assertEqual(capabilities.stderr, b"")
            parsed = json.loads(capabilities.stdout)
            self.assert_envelope(parsed, ok=True, op="capabilities")
            self.assertEqual(
                capabilities.stdout,
                json.dumps(
                    parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ).encode("utf-8")
                + b"\n",
            )

            input_path = fixture.root / "unknown.json"
            input_path.write_text(
                json.dumps(request("not.atlas", {})), encoding="utf-8"
            )
            unknown = subprocess.run(
                [*command, "call", "--input", str(input_path)],
                check=False,
                capture_output=True,
                env=env,
            )
            self.assertEqual(unknown.returncode, 2)
            unknown_response = json.loads(unknown.stdout)
            self.assert_envelope(unknown_response, ok=False, op="not.atlas")
            self.assertEqual(response_findings(unknown_response)[0][0], "OP_UNKNOWN")

            unavailable_profile = fixture.profile.parent / "unavailable.yml"
            unavailable_profile.write_text(
                "profile: synthetic\ninstance: atlas\nconnector: unsupported\n"
                "local_fs:\n  root: instances/atlas\n",
                encoding="utf-8",
            )
            unavailable_input = fixture.root / "unavailable.json"
            unavailable_input.write_text(
                json.dumps(
                    request(
                        "vault.conditional_replace",
                        {
                            "path": "vault://atlas/tmp/no-write.txt",
                            "expected_revision": "missing",
                            "text": "x\n",
                        },
                    )
                ),
                encoding="utf-8",
            )
            unavailable = subprocess.run(
                [*command, "call", "--input", str(unavailable_input)],
                check=False,
                capture_output=True,
                env={**env, "ATLAS_VAULT_PROFILE": str(unavailable_profile)},
            )
            self.assertEqual(unavailable.returncode, 3)
            unavailable_response = json.loads(unavailable.stdout)
            self.assert_envelope(
                unavailable_response, ok=False, op="vault.conditional_replace"
            )
            self.assertEqual(
                response_findings(unavailable_response)[0][0], "MUTATION_UNAVAILABLE"
            )

    def test_snapshot_is_lock_linearized_across_an_artifact_first_manifest_last_writer(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            artifact_written = threading.Event()
            release_manifest = threading.Event()
            writer_result: dict[str, dict[str, Any]] = {}

            def artifact_first_writer() -> None:
                writer_result["artifact"] = invoke(
                    fixture,
                    "vault.conditional_replace",
                    path=artifact_uri(SOURCE_B_URL),
                    expected_revision="missing",
                    text=artifact_text(SOURCE_B_URL, 2),
                )
                artifact_written.set()
                self.assertTrue(release_manifest.wait(timeout=2))
                manifest = self.read_text(fixture, MANIFEST_URI)
                writer_result["manifest"] = invoke(
                    fixture,
                    "vault.conditional_replace",
                    path=MANIFEST_URI,
                    expected_revision=f"sha256:{sha256_text(manifest)}",
                    text=manifest_text(
                        [manifest_row(SOURCE_A_URL, 1), manifest_row(SOURCE_B_URL, 2)]
                    ),
                )

            writer = threading.Thread(target=artifact_first_writer)
            writer.start()
            self.assertTrue(artifact_written.wait(timeout=2))

            snapshot = invoke(fixture, "source.snapshot_active")
            self.assert_envelope(snapshot, ok=True, op="source.snapshot_active")
            result = snapshot["result"]
            self.assertEqual(
                set(result),
                {"manifest_revision", "active_count", "source_id_set_sha256", "rows"},
            )
            self.assertEqual(result["active_count"], 1)
            self.assertEqual(
                [row["source_id"] for row in result["rows"]], [source_id(SOURCE_A_URL)]
            )
            self.assertEqual(
                set(result["rows"][0]),
                {
                    "source_seq",
                    "source_id",
                    "canonical_url",
                    "artifact_uri",
                    "content_hash",
                    "route_status",
                    "manifest_row_sha256",
                    "artifact_revision",
                },
            )
            self.assertNotIn("body", result["rows"][0])

            release_manifest.set()
            writer.join(timeout=2)
            self.assertFalse(writer.is_alive())
            self.assert_envelope(
                writer_result["artifact"], ok=True, op="vault.conditional_replace"
            )
            self.assert_envelope(
                writer_result["manifest"], ok=True, op="vault.conditional_replace"
            )

            committed = invoke(fixture, "source.snapshot_active")
            self.assert_envelope(committed, ok=True, op="source.snapshot_active")
            self.assertEqual(committed["result"]["active_count"], 2)
            self.assertEqual(
                [row["source_id"] for row in committed["result"]["rows"]],
                [source_id(SOURCE_A_URL), source_id(SOURCE_B_URL)],
            )

    def test_snapshot_excludes_a_concurrent_addition_waiting_at_its_lock_boundary(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            ready = threading.Barrier(2)
            release_addition = threading.Event()
            writer_result: dict[str, dict[str, Any]] = {}

            def waiting_addition() -> None:
                ready.wait(timeout=2)
                self.assertTrue(release_addition.wait(timeout=2))
                writer_result["artifact"] = invoke(
                    fixture,
                    "vault.conditional_replace",
                    path=artifact_uri(SOURCE_C_URL),
                    expected_revision="missing",
                    text=artifact_text(SOURCE_C_URL, 2),
                )
                manifest = self.read_text(fixture, MANIFEST_URI)
                writer_result["manifest"] = invoke(
                    fixture,
                    "vault.conditional_replace",
                    path=MANIFEST_URI,
                    expected_revision=f"sha256:{sha256_text(manifest)}",
                    text=manifest_text(
                        [manifest_row(SOURCE_A_URL, 1), manifest_row(SOURCE_C_URL, 2)]
                    ),
                )

            writer = threading.Thread(target=waiting_addition)
            writer.start()
            ready.wait(timeout=2)
            snapshot = invoke(fixture, "source.snapshot_active")
            self.assert_envelope(snapshot, ok=True, op="source.snapshot_active")
            self.assertEqual(snapshot["result"]["active_count"], 1)
            release_addition.set()
            writer.join(timeout=2)
            self.assertFalse(writer.is_alive())
            self.assert_envelope(
                writer_result["artifact"], ok=True, op="vault.conditional_replace"
            )
            self.assert_envelope(
                writer_result["manifest"], ok=True, op="vault.conditional_replace"
            )
            later = invoke(fixture, "source.snapshot_active")
            self.assert_envelope(later, ok=True, op="source.snapshot_active")
            self.assertEqual(later["result"]["active_count"], 2)

    def test_route_facade_preflight_rejects_manifest_artifact_identity_disagreement(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(before, ok=True, op="vault.digest_tree")
            args = self.transaction_args(fixture)
            args["event_record"]["event"]["content_hash"] = "f" * 64
            response = invoke(fixture, "transaction.execute", **args)
            self.assert_envelope(response, ok=False, op="transaction.execute")
            self.assertEqual(
                response_findings(response)[0][0], "ROUTE_PREFLIGHT_HASH_MISMATCH"
            )
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(after, ok=True, op="vault.digest_tree")
            self.assertEqual(after["result"], before["result"])

    def test_transaction_execute_recover_and_one_successor_hold_a_reentrant_session_and_reread(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.transaction_args(fixture)
            executed = invoke(fixture, "transaction.execute", **args)
            self.assert_envelope(executed, ok=True, op="transaction.execute")
            receipt = executed["result"]["receipt"]
            self.assertEqual(receipt["status"], "applied")
            self.assertEqual(receipt["attempt"], 0)
            self.assertEqual(
                receipt["target_revisions"][artifact_uri(SOURCE_A_URL)],
                self.revision(fixture, artifact_uri(SOURCE_A_URL)),
            )
            self.assertIn("intent_uri", executed["result"])
            self.assertIn("phase_uris", executed["result"])
            self.assertEqual(
                self.read_text(fixture, artifact_uri(SOURCE_A_URL)),
                args["targets"][0]["text"],
            )

            recovered = invoke(
                fixture,
                "transaction.recover",
                transaction_id=receipt["transaction_id"],
            )
            self.assert_envelope(recovered, ok=True, op="transaction.recover")
            self.assertEqual(recovered["result"]["receipt"], receipt)

            successor = invoke(
                fixture,
                "transaction.successor",
                transaction_id=receipt["transaction_id"],
            )
            self.assert_envelope(successor, ok=False, op="transaction.successor")
            self.assertEqual(
                response_findings(successor)[0][0], "SUCCESSOR_TERMINAL_INELIGIBLE"
            )

    def test_transaction_recovery_successor_collision_and_manual_conflict_are_exact(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.transaction_args(fixture)
            stale_target = args["targets"][0]
            self.conditional_replace(
                fixture,
                stale_target["path"],
                artifact_text(SOURCE_A_URL, 1, route_status="routed"),
            )
            rejected = invoke(fixture, "transaction.execute", **args)
            self.assert_envelope(rejected, ok=False, op="transaction.execute")
            self.assertEqual(response_findings(rejected)[0][0], "REVISION_STALE")

            self.conditional_replace(
                fixture,
                stale_target["path"],
                artifact_text(SOURCE_A_URL, 1),
            )
            manual_args = self.transaction_args(fixture)
            interrupted = invoke(
                fixture,
                "transaction.execute",
                connector=DriftingConnector(
                    fixture.connector(),
                    path=manual_args["targets"][0]["path"],
                ),
                **manual_args,
            )
            self.assert_envelope(interrupted, ok=False, op="transaction.execute")
            intent_paths = [
                finding["path"]
                for finding in interrupted["findings"]
                if finding["path"].endswith("/intent.json")
            ]
            self.assertEqual(len(intent_paths), 1)
            transaction_id = Path(intent_paths[0]).parent.name
            manual_conflict = invoke(
                fixture,
                "transaction.recover",
                transaction_id=transaction_id,
            )
            self.assert_envelope(manual_conflict, ok=False, op="transaction.recover")
            self.assertEqual(
                response_findings(manual_conflict)[0][0],
                "MANUAL_CONFLICT",
            )

    def test_transaction_recovery_allows_one_identical_successor_only_from_rolled_back_attempt(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.transaction_args(fixture)
            interrupted = invoke(
                fixture,
                "transaction.execute",
                connector=InterruptingConnector(
                    fixture.connector(),
                    path=args["targets"][0]["path"],
                    after_write=False,
                ),
                **args,
            )
            self.assert_envelope(interrupted, ok=False, op="transaction.execute")
            intent_paths = [
                finding["path"]
                for finding in interrupted["findings"]
                if finding["path"].endswith("/intent.json")
            ]
            self.assertEqual(len(intent_paths), 1)
            transaction_id = Path(intent_paths[0]).parent.name

            rolled_back = invoke(
                fixture,
                "transaction.recover",
                transaction_id=transaction_id,
            )
            self.assert_envelope(rolled_back, ok=True, op="transaction.recover")
            previous_receipt = rolled_back["result"]["receipt"]
            self.assertEqual(previous_receipt["status"], "rolled-back")

            successor = invoke(
                fixture,
                "transaction.successor",
                transaction_id=transaction_id,
            )
            self.assert_envelope(successor, ok=True, op="transaction.successor")
            successor_receipt = successor["result"]["receipt"]
            self.assertEqual(successor_receipt["attempt"], 1)
            self.assertEqual(successor_receipt["status"], "applied")
            self.assertEqual(
                successor_receipt["predecessor_sha256"], previous_receipt["sha256"]
            )
            self.assertEqual(
                successor_receipt["targets"],
                previous_receipt["targets"],
            )

            exhausted = invoke(
                fixture,
                "transaction.successor",
                transaction_id=successor_receipt["transaction_id"],
            )
            self.assert_envelope(exhausted, ok=False, op="transaction.successor")
            self.assertEqual(
                response_findings(exhausted)[0][0],
                "SUCCESSOR_TERMINAL_INELIGIBLE",
            )

    def test_effect_execute_claims_source_then_route_and_returns_immutable_receipts(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.effect_args(
                fixture, effect_id="effect-0001", with_transactions=True
            )
            executed = invoke(fixture, "effect.execute", **args)
            self.assert_envelope(executed, ok=True, op="effect.execute")
            result = executed["result"]
            self.assertEqual(
                set(result),
                {
                    "claim",
                    "members",
                    "effect",
                    "closure",
                    "transactions",
                    "outcome",
                },
            )
            self.assertEqual(result["outcome"], "applied")
            self.assertEqual(
                [item["stage"] for item in result["transactions"]],
                ["source", "route"],
            )
            self.assertEqual(
                [item["receipt"]["status"] for item in result["transactions"]],
                ["applied", "applied"],
            )
            self.assertEqual(
                self.read_text(fixture, artifact_uri(SOURCE_B_URL)),
                artifact_text(SOURCE_B_URL, 2, route_status="no-topic-match"),
            )
            manifest = self.read_text(fixture, MANIFEST_URI)
            self.assertIn(source_id(SOURCE_B_URL), manifest)
            self.assertIn(SOURCE_B_URL, manifest)
            self.assertIn("no-topic-match", manifest)
            validated = invoke(fixture, "state.validate")
            self.assert_envelope(validated, ok=True, op="state.validate")

            closure = json.loads(self.read_text(fixture, result["closure"]["uri"]))
            self.assertEqual(closure["validation"], {"findings": []})
            self.assertEqual(closure["outcome"], "applied")
            self.assertEqual(closure["claim"], result["claim"])
            self.assertEqual(len(result["members"]), 1)

            repeated = invoke(fixture, "effect.execute", **args)
            self.assert_envelope(repeated, ok=True, op="effect.execute")
            self.assertEqual(repeated["result"], result)
            recovered = invoke(fixture, "effect.recover", **args)
            self.assert_envelope(recovered, ok=True, op="effect.recover")
            self.assertEqual(recovered["result"], result)

            collided = dict(args)
            collided["context"] = {"campaign": "different-request"}
            collision = invoke(fixture, "effect.execute", **collided)
            self.assert_envelope(collision, ok=False, op="effect.execute")
            self.assertEqual(
                response_findings(collision)[0][0], "EFFECT_CLAIM_COLLISION"
            )

    def test_effect_recovery_resumes_a_claim_and_one_target_failure_uses_one_successor(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.effect_args(
                fixture, effect_id="effect-0002", with_transactions=True
            )
            interrupted_claim = invoke(
                fixture,
                "effect.execute",
                connector=InterruptingConnector(
                    fixture.connector(),
                    path=args["receipt_root"] + "/claim.json",
                    after_write=True,
                ),
                **args,
            )
            self.assert_envelope(interrupted_claim, ok=False, op="effect.execute")
            self.assertEqual(response_findings(interrupted_claim)[0][0], "IO_FAILURE")
            self.assertNotEqual(
                self.revision(fixture, args["receipt_root"] + "/claim.json"),
                "missing",
            )
            self.assertEqual(
                self.revision(fixture, args["receipt_root"] + "/closure.json"),
                "missing",
            )
            recovered = invoke(fixture, "effect.recover", **args)
            self.assert_envelope(recovered, ok=True, op="effect.recover")
            self.assertEqual(
                [
                    item["receipt"]["attempt"]
                    for item in recovered["result"]["transactions"]
                ],
                [0, 0],
            )

        with temporary_profile() as fixture:
            args = self.effect_args(
                fixture, effect_id="effect-0005", with_transactions=True
            )
            recovered_target = invoke(
                fixture,
                "effect.execute",
                connector=InterruptingConnector(
                    fixture.connector(),
                    path=artifact_uri(SOURCE_B_URL),
                    after_write=True,
                ),
                **args,
            )
            self.assert_envelope(recovered_target, ok=True, op="effect.execute")
            result = recovered_target["result"]
            self.assertEqual(result["outcome"], "applied")
            self.assertEqual(
                [item["receipt"]["attempt"] for item in result["transactions"]],
                [1, 0],
            )
            self.assertEqual(
                [item["receipt"]["status"] for item in result["transactions"]],
                ["applied", "applied"],
            )
            self.assertEqual(
                self.read_text(fixture, artifact_uri(SOURCE_B_URL)),
                artifact_text(SOURCE_B_URL, 2, route_status="no-topic-match"),
            )
            validated = invoke(fixture, "state.validate")
            self.assert_envelope(validated, ok=True, op="state.validate")

    def test_effect_no_write_and_preclaim_stale_guards_are_exact(self) -> None:
        with temporary_profile() as fixture:
            no_write_args = self.effect_args(
                fixture, effect_id="effect-0003", with_transactions=False
            )
            unknown = invoke(fixture, "effect.recover", **no_write_args)
            self.assert_envelope(unknown, ok=False, op="effect.recover")
            self.assertEqual(response_findings(unknown)[0][0], "EFFECT_CLAIM_UNKNOWN")
            manifest_revision = self.revision(fixture, MANIFEST_URI)
            artifact_revision = self.revision(fixture, artifact_uri(SOURCE_A_URL))
            no_write = invoke(fixture, "effect.execute", **no_write_args)
            self.assert_envelope(no_write, ok=True, op="effect.execute")
            self.assertEqual(no_write["result"]["outcome"], "existing-active-no-op")
            self.assertEqual(no_write["result"]["transactions"], [])
            self.assertEqual(self.revision(fixture, MANIFEST_URI), manifest_revision)
            self.assertEqual(
                self.revision(fixture, artifact_uri(SOURCE_A_URL)),
                artifact_revision,
            )

        with temporary_profile() as fixture:
            stale_args = self.effect_args(
                fixture, effect_id="effect-0004", with_transactions=True
            )
            self.conditional_replace(
                fixture,
                REPORT_URI,
                "# Changed prepared evidence\n",
            )
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(before, ok=True, op="vault.digest_tree")
            stale = invoke(fixture, "effect.execute", **stale_args)
            self.assert_envelope(stale, ok=False, op="effect.execute")
            self.assertEqual(response_findings(stale)[0][0], "EFFECT_PREPARED_STALE")
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(after, ok=True, op="vault.digest_tree")
            self.assertEqual(after["result"], before["result"])
            self.assertEqual(
                self.revision(fixture, stale_args["receipt_root"] + "/claim.json"),
                "missing",
            )

    def test_refresh_binds_exact_ordered_edges_input_revisions_outputs_intent_and_terminal_receipt(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_dirty_topic(fixture)
            args = self.refresh_args(fixture)
            response = invoke(fixture, "refresh.execute", **args)
            self.assert_envelope(response, ok=True, op="refresh.execute")
            receipt = response["result"]["receipt"]
            self.assertEqual(receipt["status"], "current")
            self.assertEqual(receipt["topic_id"], TOPIC_ID)
            self.assertEqual(receipt["edge_ids"], [relation_id(SOURCE_A_URL)])
            self.assertEqual(receipt["pass_uri"], args["projection"]["pass_uri"])
            self.assertEqual(receipt["pass_sha256"], args["projection"]["pass_sha256"])
            self.assertEqual(
                receipt["index_sha256"], args["projection"]["index_sha256"]
            )
            self.assertEqual(
                receipt["input_revisions"],
                {
                    key.removesuffix("_revision"): value
                    for key, value in args["projection"].items()
                    if key
                    in {
                        "manifest_revision",
                        "topics_revision",
                        "relations_revision",
                        "index_revision",
                    }
                },
            )
            self.assertEqual(
                self.read_text(fixture, args["projection"]["pass_uri"]),
                args["pass_text"],
            )
            self.assertEqual(self.read_text(fixture, INDEX_URI), args["index_text"])
            self.assertTrue(
                response["result"]["intent_uri"].startswith("vault://atlas/")
            )
            self.assertGreaterEqual(len(response["result"]["phase_uris"]), 3)

            recovered = invoke(fixture, "refresh.recover", **args)
            self.assert_envelope(recovered, ok=True, op="refresh.recover")
            self.assertEqual(recovered["result"]["receipt"], receipt)

    def test_refresh_rejects_stale_revisions_wrong_edge_set_and_pass_collision_without_substitution(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_dirty_topic(fixture)
            stale = self.refresh_args(fixture)
            self.conditional_replace(fixture, INDEX_URI, "# Later synthetic index\n")
            stale_response = invoke(fixture, "refresh.execute", **stale)
            self.assert_envelope(stale_response, ok=False, op="refresh.execute")
            self.assertEqual(response_findings(stale_response)[0][0], "REVISION_STALE")
            self.assertEqual(
                self.revision(fixture, stale["projection"]["pass_uri"]), "missing"
            )

            wrong_edges = self.refresh_args(fixture)
            wrong_edges["projection"]["edge_ids"] = []
            wrong_response = invoke(fixture, "refresh.execute", **wrong_edges)
            self.assert_envelope(wrong_response, ok=False, op="refresh.execute")
            self.assertEqual(
                response_findings(wrong_response)[0][0], "REFRESH_EDGE_SET_MISMATCH"
            )

            collision = self.refresh_args(fixture)
            self.conditional_replace(
                fixture,
                collision["projection"]["pass_uri"],
                "# Existing synthetic pass\n",
                expected_revision="missing",
            )
            collision_response = invoke(fixture, "refresh.execute", **collision)
            self.assert_envelope(collision_response, ok=False, op="refresh.execute")
            self.assertEqual(
                response_findings(collision_response)[0][0], "PASS_COLLISION"
            )
            self.assertNotEqual(
                self.read_text(fixture, INDEX_URI), collision["index_text"]
            )

    def test_refresh_failure_after_start_and_after_pass_or_index_is_recoverable_not_completed(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_dirty_topic(fixture)
            after_start = self.refresh_args(fixture)
            self.conditional_replace(
                fixture,
                after_start["projection"]["pass_uri"],
                "# Existing synthetic pass\n",
                expected_revision="missing",
            )
            blocked_after_start = invoke(fixture, "refresh.execute", **after_start)
            self.assert_envelope(blocked_after_start, ok=False, op="refresh.execute")
            self.assertEqual(
                response_findings(blocked_after_start)[0][0], "PASS_COLLISION"
            )
            self.assertIn("blocked", self.read_text(fixture, TOPICS_URI))

        with temporary_profile() as fixture:
            self.prepare_dirty_topic(fixture)
            after_pass = self.refresh_args(fixture)
            interrupted_pass = invoke(
                fixture,
                "refresh.execute",
                connector=InterruptingConnector(
                    fixture.connector(),
                    path=after_pass["projection"]["pass_uri"],
                    after_write=True,
                ),
                **after_pass,
            )
            self.assert_envelope(interrupted_pass, ok=False, op="refresh.execute")
            self.assertEqual(
                self.read_text(fixture, after_pass["projection"]["pass_uri"]),
                after_pass["pass_text"],
            )
            self.assertEqual(self.read_text(fixture, INDEX_URI), "# Synthetic index\n")
            recovered_pass = invoke(fixture, "refresh.recover", **after_pass)
            self.assert_envelope(recovered_pass, ok=True, op="refresh.recover")
            self.assertEqual(recovered_pass["result"]["receipt"]["status"], "blocked")

        with temporary_profile() as fixture:
            self.prepare_dirty_topic(fixture)
            after_index = self.refresh_args(fixture)
            interrupted_index = invoke(
                fixture,
                "refresh.execute",
                connector=InterruptingConnector(
                    fixture.connector(),
                    path=INDEX_URI,
                    after_write=True,
                ),
                **after_index,
            )
            self.assert_envelope(interrupted_index, ok=False, op="refresh.execute")
            self.assertEqual(
                self.read_text(fixture, after_index["projection"]["pass_uri"]),
                after_index["pass_text"],
            )
            self.assertEqual(
                self.read_text(fixture, INDEX_URI), after_index["index_text"]
            )
            recovered_index = invoke(fixture, "refresh.recover", **after_index)
            self.assert_envelope(recovered_index, ok=True, op="refresh.recover")
            self.assertEqual(recovered_index["result"]["receipt"]["status"], "current")

    def test_refresh_and_route_transactions_are_exclusive_at_the_shared_mutation_boundary(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_dirty_topic(fixture)
            refresh = self.refresh_args(fixture)
            route = self.transaction_args(fixture)
            start = threading.Barrier(3)
            results: dict[str, dict[str, Any]] = {}

            def run_refresh() -> None:
                start.wait(timeout=2)
                results["refresh"] = invoke(fixture, "refresh.execute", **refresh)

            def run_route() -> None:
                start.wait(timeout=2)
                results["route"] = invoke(fixture, "transaction.execute", **route)

            refresh_thread = threading.Thread(target=run_refresh)
            route_thread = threading.Thread(target=run_route)
            refresh_thread.start()
            route_thread.start()
            start.wait(timeout=2)
            refresh_thread.join(timeout=2)
            route_thread.join(timeout=2)
            self.assertFalse(refresh_thread.is_alive())
            self.assertFalse(route_thread.is_alive())
            self.assertEqual(
                sum(response["ok"] for response in results.values()),
                1,
            )
            rejected = next(
                response for response in results.values() if not response["ok"]
            )
            self.assertIn(
                response_findings(rejected)[0][0],
                {
                    "REVISION_STALE",
                    "ROUTE_PREFLIGHT_HASH_MISMATCH",
                    "REFRESH_CONCURRENT_MUTATION",
                },
            )

    def delete_args(
        self, fixture: TemporaryAtlasProfile, target: str
    ) -> dict[str, Any]:
        digest = invoke(fixture, "vault.digest_tree", path=target)
        self.assert_envelope(digest, ok=True, op="vault.digest_tree")
        expected_digest = digest["result"]["digest"]
        projection_sha256 = sha256_text("synthetic deletion projection\n")
        return {
            "path": target,
            "expected_digest": expected_digest,
            "projection_sha256": projection_sha256,
            "approval": f"DELETE_TREE {target} {expected_digest} {projection_sha256}",
            "report_revision": self.revision(fixture, REPORT_URI),
        }

    def test_delete_tree_requires_exact_approval_rechecks_drift_and_is_terminal_only_on_absence(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            target = "vault://atlas/tmp/delete-target"
            self.conditional_replace(
                fixture,
                f"{target}/nested/synthetic.txt",
                "synthetic\n",
                expected_revision="missing",
            )
            args = self.delete_args(fixture, target)
            rejected = dict(args, approval="DELETE_TREE incorrect")
            approval_failure = invoke(fixture, "vault.delete_tree", **rejected)
            self.assert_envelope(approval_failure, ok=False, op="vault.delete_tree")
            self.assertEqual(
                response_findings(approval_failure)[0][0], "DELETE_APPROVAL_INVALID"
            )
            self.assertEqual(
                self.read_text(fixture, f"{target}/nested/synthetic.txt"), "synthetic\n"
            )

            self.conditional_replace(
                fixture,
                f"{target}/drift.txt",
                "drift\n",
                expected_revision="missing",
            )
            drift = invoke(fixture, "vault.delete_tree", **args)
            self.assert_envelope(drift, ok=False, op="vault.delete_tree")
            self.assertEqual(response_findings(drift)[0][0], "DELETE_DIGEST_STALE")

            fresh = self.delete_args(fixture, target)
            deleted = invoke(fixture, "vault.delete_tree", **fresh)
            self.assert_envelope(deleted, ok=True, op="vault.delete_tree")
            self.assertEqual(deleted["result"]["status"], "deleted")
            absent = invoke(fixture, "vault.hash", path=target)
            self.assert_envelope(absent, ok=True, op="vault.hash")
            self.assertEqual(absent["result"]["revision"], "missing")

    def test_delete_tree_quarantine_is_not_success_and_exact_request_resumes_after_erase_failure(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            target = "vault://atlas/tmp/quarantine-target"
            locked_uri = f"{target}/locked/synthetic.txt"
            self.conditional_replace(
                fixture,
                locked_uri,
                "synthetic\n",
                expected_revision="missing",
            )
            locked_directory = fixture.instance / "tmp" / "quarantine-target" / "locked"
            locked_directory.chmod(0o500)
            try:
                args = self.delete_args(fixture, target)
                quarantined = invoke(fixture, "vault.delete_tree", **args)
                self.assert_envelope(quarantined, ok=False, op="vault.delete_tree")
                self.assertEqual(
                    response_findings(quarantined)[0][0], "QUARANTINED_NOT_ERASED"
                )
                self.assertEqual(self.revision(fixture, target), "missing")
            finally:
                for candidate in fixture.instance.glob("tmp/.atlas-quarantine-*"):
                    for directory in sorted(candidate.rglob("*"), reverse=True):
                        if directory.is_dir():
                            directory.chmod(0o700)
                    candidate.chmod(0o700)

            resumed = invoke(fixture, "vault.delete_tree", **args)
            self.assert_envelope(resumed, ok=True, op="vault.delete_tree")
            self.assertEqual(resumed["result"]["status"], "deleted")
            self.assertEqual(self.revision(fixture, target), "missing")


if __name__ == "__main__":
    unittest.main()
