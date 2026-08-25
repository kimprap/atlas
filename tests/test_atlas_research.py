from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import atlas_connector  # noqa: E402
import atlas_index  # noqa: E402
import atlas_research  # noqa: E402
import atlas_tool  # noqa: E402
import atlas_state  # noqa: E402
from tests.test_atlas_index import (  # noqa: E402
    empty_snapshot,
    prepare_topic,
    vocabulary_text,
)
from tests.test_atlas_tool import (  # noqa: E402
    SOURCE_A_URL as RESEARCH_SOURCE_URL,
    artifact_path as research_artifact_path,
    artifact_text as research_artifact_text,
    sha256_text,
    source_routing_digest,
)
from tests.test_atlas_state import document_revisions  # noqa: E402


class ResearchFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.connector = atlas_connector.LocalFilesystemConnector(
            atlas_connector.LocalProfile(
                profile="test",
                instance="atlas",
                connector="local-fs",
                root=self.root,
            )
        )
        initial = prepare_topic(*empty_snapshot())
        self.assertIsInstance(initial, atlas_index.TopicPlan)
        assert isinstance(initial, atlas_index.TopicPlan)
        args = empty_snapshot()
        self.initial_request = args[0]
        self.manifest = args[1]
        self.relations = args[3]
        self.topic = initial.candidate_topic_bytes.decode("utf-8")
        self.subdomain = initial.candidate_subdomain_bytes.decode("utf-8")
        documents = {
            "manifest": args[1],
            "topics": initial.candidate_topics_bytes.decode("utf-8"),
            "vocab": initial.candidate_vocab_bytes.decode("utf-8"),
            "relations": args[3],
        }
        source_id = atlas_state.source_id_for(RESEARCH_SOURCE_URL)
        source_artifact = research_artifact_path(RESEARCH_SOURCE_URL)
        source_hash = sha256_text("synthetic payload 1\n")
        classification_result = {
            "version": 1,
            "primary_domain": self.initial_request["vocabulary"]["domain"],
            "secondary_domains": [],
            "subdomains": [self.initial_request["vocabulary"]["subdomain"]],
            "tags": [],
            "routing_terms": [],
        }
        routing_sha256 = source_routing_digest(
            primary_domain=self.initial_request["domain"],
            subdomains=[self.initial_request["subdomain"]],
        )
        source_reduction = atlas_state.reduce_event(
            documents,
            {
                "version": 2,
                "type": "source-upsert",
                "mode": "routine",
                "source_id": source_id,
                "canonical_url": RESEARCH_SOURCE_URL,
                "artifact": source_artifact,
                "first_seen": "2026-07-28",
                "checked_on": "2026-07-28",
                "summarized_on": "2026-07-28",
                "content_hash": source_hash,
                "refresh_after": "2027-07-28",
                "source_routing_sha256": routing_sha256,
                "classification_action": "replace",
                "classification_input": {
                    "version": 1,
                    "status": "classified",
                    "result": classification_result,
                },
            },
        )
        self.assertTrue(source_reduction.ok, source_reduction.to_dict())
        documents.update(source_reduction.documents)
        route_reduction = atlas_state.reduce_event(
            documents,
            {
                "version": 2,
                "type": "route-upsert",
                "route_action": "candidate-route",
                "source_id": source_id,
                "content_hash": source_hash,
                "source_routing_sha256": routing_sha256,
                "checked_on": "2026-07-28",
                "outcome": "routed",
                "edges": [
                    {
                        "topic_id": self.initial_request["topic_id"],
                        "relation": "direct",
                        "impact": "high",
                        "confidence": "high",
                        "reason": (
                            "Verifier: Rule 2 — Synthetic evidence supports the answer "
                            "[relation=direct; impact=high]"
                        ),
                    }
                ],
                "excluded_topic_ids": [],
            },
        )
        self.assertTrue(route_reduction.ok, route_reduction.to_dict())
        documents.update(route_reduction.documents)
        selection = atlas_state.select_topic_state(
            documents, self.initial_request["topic_id"]
        )
        dispositions = [
            {
                "edge_id": relation["edge_id"],
                "generation": relation["generation"],
                "source_seq": relation["source_seq"],
                "source_id": relation["source_id"],
                "source_content_hash": relation["source_content_hash"],
                "source_routing_sha256": relation["source_routing_sha256"],
                "topic_scope_sha256": relation["topic_scope_sha256"],
                "work_kind": relation["work_kind"],
                "disposition": "incorporated",
            }
            for relation in selection.pending_edges
        ]
        start_reduction = atlas_state.reduce_event(
            documents,
            {
                "version": 2,
                "type": "refresh-start",
                "topic_id": self.initial_request["topic_id"],
                "inspection_sha256": "1" * 64,
                "expected_revisions": document_revisions(documents),
                "dispositions": dispositions,
                "started_at": "2026-08-01T00:00:00Z",
            },
        )
        self.assertTrue(start_reduction.ok, start_reduction.to_dict())
        documents.update(start_reduction.documents)
        complete_reduction = atlas_state.reduce_event(
            documents,
            {
                "version": 2,
                "type": "refresh-complete",
                "topic_id": self.initial_request["topic_id"],
                "inspection_sha256": "1" * 64,
                "expected_revisions": document_revisions(documents),
                "dispositions": dispositions,
                "pass_path": (
                    "summaries/research/research/methods/topics/new-topic/"
                    "passes/2026-08-01--baseline.md"
                ),
                "completed_on": "2026-08-01",
            },
        )
        self.assertTrue(complete_reduction.ok, complete_reduction.to_dict())
        documents.update(complete_reduction.documents)
        self.manifest = documents["manifest"]
        self.topics = documents["topics"]
        self.relations = documents["relations"]
        self.vocab = documents["vocab"]
        self.topic_path = initial.targets[0].path.removeprefix("vault://atlas/")
        self.subdomain_path = initial.targets[1].path.removeprefix("vault://atlas/")
        for path, text in (
            (atlas_state.MANIFEST_PATH, self.manifest),
            (atlas_state.TOPICS_PATH, self.topics),
            (atlas_state.RELATIONS_PATH, self.relations),
            (atlas_state.VOCAB_PATH, self.vocab),
            (self.topic_path, self.topic),
            (self.subdomain_path, self.subdomain),
        ):
            self.write(path, text)
        self.write(
            source_artifact,
            research_artifact_text(
                RESEARCH_SOURCE_URL,
                1,
                primary_domain=self.initial_request["domain"],
                subdomains=[self.initial_request["subdomain"]],
            ),
        )

    def uri(self, path: str) -> str:
        return "vault://atlas/" + path

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def read(self, path: str) -> str:
        return self.connector.read_text(self.uri(path))

    def set_relation_rank(self, relation: str, impact: str) -> None:
        ranked = self.relations.replace(
            "| direct | high | high | applied |",
            f"| {relation} | {impact} | high | applied |",
        ).replace(
            "[relation=direct; impact=high]",
            f"[relation={relation}; impact={impact}]",
        )
        self.write(atlas_state.RELATIONS_PATH, ranked)

    def inspection(self) -> dict[str, Any]:
        documents = {
            "manifest": self.read(atlas_state.MANIFEST_PATH),
            "topics": self.read(atlas_state.TOPICS_PATH),
            "relations": self.read(atlas_state.RELATIONS_PATH),
        }
        paths = atlas_state.select_topic_state(
            documents, self.initial_request["topic_id"]
        ).paths_for("research")
        registry_uris = {
            "manifest": self.uri(atlas_state.MANIFEST_PATH),
            "topics": self.uri(atlas_state.TOPICS_PATH),
            "relations": self.uri(atlas_state.RELATIONS_PATH),
        }
        snapshot = self.connector.consistent_read(
            [*registry_uris.values(), *(self.uri(path) for path in paths)]
        )
        decoded = {
            uri: {
                "revision": entry["revision"],
                "text": (
                    None if entry["bytes"] is None else entry["bytes"].decode("utf-8")
                ),
            }
            for uri, entry in snapshot.items()
        }
        return atlas_state.inspect_topic(
            {name: decoded[uri]["text"] for name, uri in registry_uris.items()},
            {path: decoded[self.uri(path)] for path in paths},
            self.initial_request["topic_id"],
            "research",
            {name: decoded[uri]["revision"] for name, uri in registry_uris.items()},
        )

    def pass_text(self) -> str:
        return """---
schema_version: 1
note_type: research-pass
managed_by: atlas
topic: "new-topic"
domain: "research"
subdomain: "methods"
requested: "2026-08-15T10:00:00Z"
completed: "2026-08-15T10:30:00Z"
mode: "vault-only"
coverage_state: "partial"
confidence: "medium"
tags: []
---

# Initial research

## Request

Explain the topic.

## Mode

Vault-only; current sources were sufficient.

## Coverage gate

- Existing source artifacts were sufficient: yes
- New acquisition was allowed: no
- Coverage result: `partial`

## Existing artifacts consulted

| Source artifact | Relevance | Notes |
|---|---|---|

## New source artifacts created

| Source artifact | Route status | Notes |
|---|---|---|

## Findings

- Evidence-backed guidance is available.

## Changes applied to topic INDEX.md

- Coverage metadata — advanced after the research pass.

## Gaps left open

- One known gap remains.

## Next acquisition needs

- Acquire a second source class.
"""

    def candidate_topic(self) -> str:
        value = self.topic.replace(
            'coverage_state: "insufficient"', 'coverage_state: "partial"'
        )
        value = value.replace('confidence: "low"', 'confidence: "medium"')
        value = value.replace(
            'last_researched: "2026-08-01"',
            'last_researched: "2026-08-15"',
        )
        return value.replace(
            "- No evidence-backed answer exists; acquisition and research are required.",
            (
                "- Use the evidence-backed method, while accounting for the known gap "
                f"([source](vault://atlas/{research_artifact_path(RESEARCH_SOURCE_URL)}))."
            ),
        )

    def request(self) -> dict[str, Any]:
        inspection = self.inspection()
        return {
            "version": 1,
            "topic_id": self.initial_request["topic_id"],
            "inspection_sha256": inspection["inspection_sha256"],
            "pass_uri": (
                "vault://atlas/summaries/research/research/methods/topics/"
                "new-topic/passes/2026-08-15--initial-research.md"
            ),
            "pass_text": self.pass_text(),
            "index_text": self.candidate_topic(),
            "completed_on": "2026-08-15",
        }


class AtlasResearchTests(ResearchFixture):
    def test_topic_inspect_cli_uses_selector_on_temporary_profile(self) -> None:
        profile = self.root / "config" / "profiles" / "local.yml"
        profile.parent.mkdir(parents=True)
        profile.write_text(
            "\n".join(
                (
                    "profile: local",
                    "instance: atlas",
                    "connector: local-fs",
                    "local_fs:",
                    "  root: .",
                    "",
                )
            ),
            encoding="utf-8",
        )
        input_path = self.root / "topic-inspect.json"
        input_path.write_text(
            json.dumps(
                {
                    "version": 2,
                    "op": "topic.inspect",
                    "args": {
                        "topic_id": self.initial_request["topic_id"],
                        "purpose": "research",
                    },
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "atlas_tool.py"),
                "call",
                "--input",
                str(input_path),
            ],
            check=False,
            capture_output=True,
            env={**os.environ, "ATLAS_VAULT_PROFILE": str(profile)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["op"], "topic.inspect")
        self.assertEqual(
            response["result"]["topic_id"], self.initial_request["topic_id"]
        )
        self.assertEqual(
            result.stdout,
            json.dumps(
                response, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            + b"\n",
        )

    def test_execute_rejects_self_consistent_request_mismatched_projection_without_writes(
        self,
    ) -> None:
        request = self.request()
        prepared = atlas_research.prepare(self.connector, request)
        decoded_request, record, plan = atlas_research._decode_prepared(prepared)
        forged_pass = (
            request["pass_text"]
            .replace(
                "Evidence-backed guidance is available.",
                "Different evidence-backed guidance is available.",
            )
            .encode("utf-8")
        )
        forged_targets = (
            type(plan.targets[0])(
                plan.targets[0].path, plan.targets[0].input_bytes, forged_pass
            ),
            *plan.targets[1:],
        )
        forged_event = {
            **record,
            "reducer_event": {
                **record["reducer_event"],
                "pass_sha256": atlas_research._sha256(forged_pass),
            },
            "output_sha256": {
                target.path: atlas_research._sha256(target.output_bytes)
                for target in forged_targets
            },
        }
        forged_plan = atlas_research._plan(forged_event, forged_targets)
        forged = atlas_research._prepared_value(
            decoded_request, forged_event, forged_plan
        )

        class RecordingConnector:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.writes: list[str] = []
                self.deletes: list[str] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def conditional_replace(self, uri: str, *args: Any) -> Any:
                self.writes.append(uri)
                return self._inner.conditional_replace(uri, *args)

            def delete(self, uri: str, expected_revision: str) -> None:
                self.deletes.append(uri)
                self._inner.delete(uri, expected_revision)

        governing = (
            atlas_state.MANIFEST_PATH,
            atlas_state.TOPICS_PATH,
            atlas_state.RELATIONS_PATH,
            self.topic_path,
            self.subdomain_path,
        )
        before = {path: self.read(path) for path in governing}
        recording = RecordingConnector(self.connector)
        with self.assertRaises(atlas_research.ResearchError) as caught:
            atlas_research.execute(recording, forged)
        self.assertEqual(caught.exception.code, "RESEARCH_PREPARED_INVALID")
        self.assertEqual(caught.exception.path, "args.prepared")
        self.assertEqual(recording.writes, [])
        self.assertEqual(recording.deletes, [])
        self.assertEqual({path: self.read(path) for path in governing}, before)
        self.assertEqual(self.connector.revision(request["pass_uri"]), "missing")
        self.assertEqual(
            self.connector.revision(
                atlas_research.ROOT_URI
                + f"{atlas_research.TRANSACTION_ROOT}/{forged_plan.transaction_id}/event.json"
            ),
            "missing",
        )

    def test_execute_rejects_type_distinct_event_versions_without_writes(
        self,
    ) -> None:
        request = self.request()
        prepared = atlas_research.prepare(self.connector, request)
        decoded_request, record, plan = atlas_research._decode_prepared(prepared)

        class RecordingConnector:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.writes: list[str] = []
                self.deletes: list[str] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def conditional_replace(self, uri: str, *args: Any) -> Any:
                self.writes.append(uri)
                return self._inner.conditional_replace(uri, *args)

            def delete(self, uri: str, expected_revision: str) -> None:
                self.deletes.append(uri)
                self._inner.delete(uri, expected_revision)

        governing = (
            atlas_state.MANIFEST_PATH,
            atlas_state.TOPICS_PATH,
            atlas_state.RELATIONS_PATH,
            self.topic_path,
            self.subdomain_path,
        )
        before = {path: self.read(path) for path in governing}
        for version in (True, 1.0):
            with self.subTest(version=version):
                forged_event = {**record, "version": version}
                forged_plan = atlas_research._plan(forged_event, plan.targets)
                forged = atlas_research._prepared_value(
                    decoded_request,
                    forged_event,
                    forged_plan,
                )
                recording = RecordingConnector(self.connector)
                with self.assertRaises(atlas_research.ResearchError) as caught:
                    atlas_research.execute(recording, forged)
                self.assertEqual(caught.exception.code, "RESEARCH_PREPARED_INVALID")
                self.assertEqual(recording.writes, [])
                self.assertEqual(recording.deletes, [])
                self.assertEqual(
                    {path: self.read(path) for path in governing},
                    before,
                )
                self.assertEqual(
                    self.connector.revision(request["pass_uri"]),
                    "missing",
                )
                self.assertEqual(
                    self.connector.revision(
                        atlas_research.ROOT_URI
                        + (
                            f"{atlas_research.TRANSACTION_ROOT}/"
                            f"{forged_plan.transaction_id}/event.json"
                        )
                    ),
                    "missing",
                )

    def test_execute_rejects_stale_snapshot_before_journal_write(self) -> None:
        request = self.request()
        prepared = atlas_research.prepare(self.connector, request)
        self.write(self.topic_path, self.topic + "\n")

        class RecordingConnector:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.writes: list[str] = []
                self.deletes: list[str] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def conditional_replace(self, uri: str, *args: Any) -> Any:
                self.writes.append(uri)
                return self._inner.conditional_replace(uri, *args)

            def delete(self, uri: str, expected_revision: str) -> None:
                self.deletes.append(uri)
                self._inner.delete(uri, expected_revision)

        governing = (
            atlas_state.MANIFEST_PATH,
            atlas_state.TOPICS_PATH,
            atlas_state.RELATIONS_PATH,
            self.topic_path,
            self.subdomain_path,
        )
        before = {path: self.read(path) for path in governing}
        recording = RecordingConnector(self.connector)
        with self.assertRaises(atlas_research.ResearchError) as caught:
            atlas_research.execute(recording, prepared)
        self.assertEqual(caught.exception.code, "RESEARCH_INSPECTION_STALE")
        self.assertEqual(recording.writes, [])
        self.assertEqual(recording.deletes, [])
        self.assertEqual({path: self.read(path) for path in governing}, before)
        self.assertEqual(self.connector.revision(request["pass_uri"]), "missing")
        self.assertEqual(
            self.connector.revision(
                atlas_research.ROOT_URI
                + (
                    f"{atlas_research.TRANSACTION_ROOT}/"
                    f"{prepared['transaction_id']}/event.json"
                )
            ),
            "missing",
        )

    def test_prepare_locks_only_registries_for_absent_and_invalid_selection(
        self,
    ) -> None:
        class RecordingConnector:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.snapshots: list[tuple[str, ...]] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def consistent_read(self, paths: list[str]) -> dict[str, dict[str, Any]]:
                self.snapshots.append(tuple(paths))
                return self._inner.consistent_read(paths)

        registry_uris = (
            atlas_research.MANIFEST_URI,
            atlas_research.TOPICS_URI,
            atlas_research.RELATIONS_URI,
        )
        request = self.request()
        absent_connector = RecordingConnector(self.connector)
        with self.assertRaises(atlas_research.ResearchError) as absent:
            atlas_research.prepare(
                absent_connector, {**request, "topic_id": "missing-topic"}
            )
        self.assertEqual(absent.exception.code, "TOPIC_INSPECTION_ABSENT")
        self.assertEqual(absent_connector.snapshots, [registry_uris])

        self.write(atlas_state.TOPICS_PATH, "malformed\n")
        invalid_connector = RecordingConnector(self.connector)
        with self.assertRaises(atlas_research.ResearchError) as invalid:
            atlas_research.prepare(invalid_connector, request)
        self.assertEqual(invalid.exception.code, "TOPIC_INSPECTION_INVALID")
        self.assertEqual(invalid_connector.snapshots, [registry_uris])

    def test_research_snapshot_rejects_candidate_to_locked_selection_drift(
        self,
    ) -> None:
        class DriftingConnector:
            def __init__(
                self,
                inner: Any,
                apply_locked_documents: Any,
            ) -> None:
                self._inner = inner
                self._apply_locked_documents = apply_locked_documents

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def consistent_read(self, paths: list[str]) -> dict[str, dict[str, Any]]:
                self._apply_locked_documents()
                return self._inner.consistent_read(paths)

        current = {
            "manifest": self.read(atlas_state.MANIFEST_PATH),
            "topics": self.read(atlas_state.TOPICS_PATH),
            "relations": self.read(atlas_state.RELATIONS_PATH),
        }
        source_url = "https://example.test/selection-drift"
        source_id = atlas_state.source_id_for(source_url)
        source_artifact = (
            "summaries/sources/artifacts/2026/2026-08/"
            f"2026-08-16--{source_id}--selection-drift.md"
        )
        source = atlas_state.reduce_event(
            current,
            {
                "version": 2,
                "type": "source-upsert",
                "mode": "routine",
                "source_id": source_id,
                "canonical_url": source_url,
                "artifact": source_artifact,
                "first_seen": "2026-08-16",
                "checked_on": "2026-08-16",
                "summarized_on": "2026-08-16",
                "content_hash": "d" * 64,
                "refresh_after": "2027-08-16",
                "source_routing_sha256": "sha256:" + "d" * 64,
                "classification_action": "mark-unclassified",
                "classification_input": {
                    "version": 1,
                    "status": "semantic-unavailable",
                    "disposition": "SOURCE_CLASSIFICATION_UNAVAILABLE",
                    "reason": "schema-invalid",
                },
            },
        )
        self.assertTrue(source.ok, source.findings)
        pending = dict(current)
        pending.update(source.documents)
        route = atlas_state.reduce_event(
            pending,
            {
                "version": 2,
                "type": "route-upsert",
                "route_action": "candidate-route",
                "source_id": source_id,
                "content_hash": "d" * 64,
                "source_routing_sha256": "sha256:" + "d" * 64,
                "checked_on": "2026-08-16",
                "outcome": "routed",
                "edges": [
                    {
                        "topic_id": self.initial_request["topic_id"],
                        "relation": "direct",
                        "impact": "high",
                        "confidence": "high",
                        "reason": (
                            "Verifier: Heading Example — Source establishes "
                            "the mechanism [relation=direct; impact=high]"
                        ),
                    }
                ],
                "excluded_topic_ids": [],
            },
        )
        self.assertTrue(route.ok, route.findings)
        pending.update(route.documents)
        cases = {
            "same-path-pending": pending,
            "active-to-absent": {
                **current,
                "topics": current["topics"].replace("| current |", "| archived |", 1),
            },
            "active-to-invalid": {
                **current,
                "topics": "malformed\n",
            },
        }
        request = self.request()
        for name, locked_documents in cases.items():
            with self.subTest(name=name):
                for path, text in current.items():
                    self.write(getattr(atlas_state, f"{path.upper()}_PATH"), text)

                def apply_locked_documents() -> None:
                    for path, text in locked_documents.items():
                        self.write(getattr(atlas_state, f"{path.upper()}_PATH"), text)

                connector = DriftingConnector(
                    self.connector,
                    apply_locked_documents,
                )
                with self.assertRaises(atlas_research.ResearchError) as caught:
                    atlas_research.prepare(connector, request)
                self.assertEqual(
                    caught.exception.code,
                    "TOPIC_INSPECTION_UNAVAILABLE",
                )

    def test_research_snapshot_rejects_lock_drift_before_candidate_artifact_decode(
        self,
    ) -> None:
        request = self.request()
        pass_path = self.root / request["pass_uri"].removeprefix(
            atlas_research.ROOT_URI
        )
        pass_path.parent.mkdir(parents=True, exist_ok=True)
        malformed_pass = b"\xff"
        pass_path.write_bytes(malformed_pass)

        class DriftingConnector:
            def __init__(self, fixture: ResearchFixture) -> None:
                self._fixture = fixture
                self._inner = fixture.connector
                self.snapshots: list[tuple[str, ...]] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def consistent_read(self, paths: list[str]) -> dict[str, dict[str, Any]]:
                self.snapshots.append(tuple(paths))
                self._fixture.write(
                    atlas_state.TOPICS_PATH,
                    self._fixture.topics.replace("| current |", "| archived |", 1),
                )
                return self._inner.consistent_read(paths)

        connector = DriftingConnector(self)
        with self.assertRaises(atlas_research.ResearchError) as caught:
            atlas_research.prepare(connector, request)
        self.assertEqual(caught.exception.code, "TOPIC_INSPECTION_UNAVAILABLE")
        self.assertEqual(len(connector.snapshots), 1)
        self.assertIn(request["pass_uri"], connector.snapshots[0])
        self.assertEqual(pass_path.read_bytes(), malformed_pass)

    def test_research_without_eligible_evidence_preserves_answer_sections(
        self,
    ) -> None:
        self.set_relation_rank("supporting", "low")
        request = self.request()
        authored_answer = (
            "- Use the evidence-backed method, while accounting for the known gap "
            f"([source](vault://atlas/{research_artifact_path(RESEARCH_SOURCE_URL)}))."
        )
        self.assertIn(authored_answer, request["index_text"])
        request["index_text"] = request["index_text"].replace(authored_answer, "")
        before = {
            path: self.read(path)
            for path in (
                atlas_state.MANIFEST_PATH,
                atlas_state.TOPICS_PATH,
                atlas_state.RELATIONS_PATH,
                self.topic_path,
                self.subdomain_path,
            )
        }

        with self.assertRaises(atlas_research.ResearchError) as caught:
            atlas_research.prepare(self.connector, request)

        self.assertEqual(caught.exception.code, "ANSWER_EVIDENCE_REQUIRED")
        self.assertEqual(caught.exception.path, "args.index_text")
        self.assertEqual(
            {
                path: self.read(path)
                for path in (
                    atlas_state.MANIFEST_PATH,
                    atlas_state.TOPICS_PATH,
                    atlas_state.RELATIONS_PATH,
                    self.topic_path,
                    self.subdomain_path,
                )
            },
            before,
        )

    def test_research_without_eligible_evidence_rejects_stale_coverage(
        self,
    ) -> None:
        self.set_relation_rank("supporting", "low")
        request = self.request()
        request["index_text"] = self.topic.replace(
            'coverage_state: "insufficient"', 'coverage_state: "stale"'
        ).replace(
            'last_researched: "2026-08-01"',
            'last_researched: "2026-08-15"',
        )

        with self.assertRaises(atlas_research.ResearchError) as caught:
            atlas_research.prepare(self.connector, request)

        self.assertEqual(caught.exception.code, "ANSWER_COVERAGE_INELIGIBLE")
        self.assertEqual(caught.exception.path, "args.index_text")

    def test_research_rejects_ineligible_answer_citations(self) -> None:
        for impact in ("low", "medium"):
            with self.subTest(impact=impact):
                self.set_relation_rank("supporting", impact)
                request = self.request()
                before = {
                    path: self.read(path)
                    for path in (
                        atlas_state.MANIFEST_PATH,
                        atlas_state.TOPICS_PATH,
                        atlas_state.RELATIONS_PATH,
                        self.topic_path,
                        self.subdomain_path,
                    )
                }
                with self.assertRaises(atlas_research.ResearchError) as caught:
                    atlas_research.prepare(self.connector, request)
                self.assertEqual(caught.exception.code, "ANSWER_EVIDENCE_INELIGIBLE")
                self.assertEqual(caught.exception.path, "args.index_text")
                self.assertEqual(
                    {
                        path: self.read(path)
                        for path in (
                            atlas_state.MANIFEST_PATH,
                            atlas_state.TOPICS_PATH,
                            atlas_state.RELATIONS_PATH,
                            self.topic_path,
                            self.subdomain_path,
                        )
                    },
                    before,
                )

    def test_research_allows_supporting_low_in_evidence_map_only(self) -> None:
        source_path = research_artifact_path(RESEARCH_SOURCE_URL)
        evidence_header = "|---|---|---|---|\n<!-- atlas:managed:end evidence-map -->"
        for impact in ("low", "medium"):
            with self.subTest(relation="supporting", impact=impact):
                self.set_relation_rank("supporting", impact)
                request = self.request()
                candidate = self.topic.replace(
                    'last_researched: "2026-08-01"',
                    'last_researched: "2026-08-15"',
                ).replace(
                    evidence_header,
                    (
                        "|---|---|---|---|\n"
                        f"| Caveat | [source](vault://atlas/{source_path}) "
                        f"| {impact} | Supporting only |\n"
                        "<!-- atlas:managed:end evidence-map -->"
                    ),
                )
                request["index_text"] = candidate
                prepared = atlas_research.prepare(self.connector, request)
                self.assertEqual(len(prepared["targets"]), 4)
                current = atlas_state._managed_sections(
                    candidate,
                    atlas_state.TOPIC_MANAGED_SECTIONS,
                    self.topic_path,
                )
                baseline = atlas_state._managed_sections(
                    self.topic,
                    atlas_state.TOPIC_MANAGED_SECTIONS,
                    self.topic_path,
                )
                self.assertEqual(current["current-answer"], baseline["current-answer"])
                self.assertEqual(current["decision-tree"], baseline["decision-tree"])

        for impact in ("high", "medium"):
            with self.subTest(relation="direct", impact=impact):
                self.set_relation_rank("direct", impact)
                prepared = atlas_research.prepare(
                    self.connector,
                    self.request(),
                )
                self.assertEqual(len(prepared["targets"]), 4)

    def test_prepare_is_deterministic_and_execute_writes_exact_four_targets(
        self,
    ) -> None:
        request = self.request()
        first = atlas_research.prepare(self.connector, request)
        second = atlas_research.prepare(self.connector, request)
        facade_prepared = atlas_tool.execute(
            {"version": 2, "op": "research.prepare", "args": request},
            self.connector,
        )
        self.assertTrue(facade_prepared["ok"], facade_prepared)
        self.assertEqual(facade_prepared["result"]["prepared"], first)
        self.assertEqual(first, second)
        self.assertEqual(
            [target["path"] for target in first["targets"]],
            [
                (
                    "summaries/research/research/methods/topics/new-topic/"
                    "passes/2026-08-15--initial-research.md"
                ),
                self.topic_path,
                self.subdomain_path,
                atlas_state.TOPICS_PATH,
            ],
        )
        manifest_before = self.read(atlas_state.MANIFEST_PATH)
        relations_before = self.read(atlas_state.RELATIONS_PATH)

        response = atlas_tool.execute(
            {
                "version": 2,
                "op": "research.execute",
                "args": {"prepared": first},
            },
            self.connector,
        )
        self.assertTrue(response["ok"], response)
        result = response["result"]
        self.assertEqual(result["status"], "applied")
        self.assertEqual(self.read(self.topic_path), request["index_text"])
        self.assertEqual(self.read(first["targets"][0]["path"]), request["pass_text"])
        self.assertIn(
            "| New topic | See topic answer | Partial | Current |",
            self.read(self.subdomain_path),
        )
        self.assertIn("2026-08-15", self.read(atlas_state.TOPICS_PATH))
        self.assertEqual(self.read(atlas_state.MANIFEST_PATH), manifest_before)
        self.assertEqual(self.read(atlas_state.RELATIONS_PATH), relations_before)

    def test_stale_inspection_and_pass_collision_fail_before_writes(self) -> None:
        request = self.request()
        stale = {**request, "inspection_sha256": "0" * 64}
        with self.assertRaises(atlas_research.ResearchError) as caught:
            atlas_research.prepare(self.connector, stale)
        self.assertEqual(caught.exception.code, "RESEARCH_INSPECTION_STALE")
        self.connector.conditional_replace(
            request["pass_uri"], "missing", b"existing\n"
        )
        with self.assertRaises(atlas_research.ResearchError) as collision:
            atlas_research.prepare(self.connector, request)
        self.assertEqual(collision.exception.code, "RESEARCH_PASS_COLLISION")
        self.assertEqual(self.read(self.topic_path), self.topic)

    def test_partial_write_rolls_back_and_exposes_one_recorded_successor(self) -> None:
        request = self.request()
        prepared = atlas_research.prepare(self.connector, request)
        topic_uri = self.uri(self.topic_path)

        class FailingOnce:
            def __init__(
                self, wrapped: atlas_connector.LocalFilesystemConnector
            ) -> None:
                self.wrapped = wrapped
                self.failed = False

            def __getattr__(self, name: str) -> Any:
                return getattr(self.wrapped, name)

            def conditional_replace(
                self, uri: str, expected_revision: str, value: bytes
            ) -> dict[str, str]:
                result = self.wrapped.conditional_replace(uri, expected_revision, value)
                if uri == topic_uri and not self.failed:
                    self.failed = True
                    raise atlas_connector.ConnectorIOError(
                        "synthetic post-write interruption"
                    )
                return result

        interrupted = atlas_research.execute(FailingOnce(self.connector), prepared)
        self.assertEqual(interrupted["status"], "rolled-back")
        self.assertEqual(interrupted["next"]["operation"], "research.execute")
        successor = interrupted["next"]["args"]["prepared"]
        self.assertTrue(successor["transaction_id"].endswith("-a000001"))
        self.assertEqual(self.read(self.topic_path), self.topic)
        self.assertEqual(self.connector.revision(request["pass_uri"]), "missing")

        completed = atlas_research.execute(self.connector, successor)
        self.assertEqual(completed["status"], "applied")
        self.assertNotIn("next", completed)
        self.assertEqual(self.read(self.topic_path), request["index_text"])

    def test_exact_recovery_preserves_request_and_sole_successor(self) -> None:
        request = self.request()
        prepared = atlas_research.prepare(self.connector, request)
        topic_uri = self.uri(self.topic_path)

        class FailingOnce:
            def __init__(
                self, wrapped: atlas_connector.LocalFilesystemConnector
            ) -> None:
                self.wrapped = wrapped
                self.failed = False

            def __getattr__(self, name: str) -> Any:
                return getattr(self.wrapped, name)

            def conditional_replace(
                self, uri: str, expected_revision: str, value: bytes
            ) -> dict[str, str]:
                result = self.wrapped.conditional_replace(uri, expected_revision, value)
                if uri == topic_uri and not self.failed:
                    self.failed = True
                    raise atlas_connector.ConnectorIOError(
                        "synthetic post-write interruption"
                    )
                return result

        interrupted = atlas_research.execute(FailingOnce(self.connector), prepared)
        successor = interrupted["next"]
        recovered = atlas_research.recover(
            self.connector, prepared["transaction_id"], request
        )
        self.assertEqual(recovered["status"], "rolled-back")
        self.assertEqual(recovered["next"], successor)
        successor_prepared = recovered["next"]["args"]["prepared"]
        self.assertEqual(successor_prepared["request"], request)
        self.assertEqual(successor_prepared["attempt"], 1)
        completed = atlas_research.execute(self.connector, successor_prepared)
        self.assertEqual(completed["status"], "applied")
        self.assertNotIn("next", completed)

    def test_recovery_rejects_a_changed_original_request(self) -> None:
        request = self.request()
        prepared = atlas_research.prepare(self.connector, request)
        atlas_research.execute(self.connector, prepared)
        changed = {**request, "pass_text": request["pass_text"] + "\n"}
        with self.assertRaises(atlas_research.ResearchError) as caught:
            atlas_research.recover(self.connector, prepared["transaction_id"], changed)
        self.assertEqual(caught.exception.code, "RESEARCH_RECOVERY_INVALID")


if __name__ == "__main__":
    unittest.main()
