from __future__ import annotations

import base64
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
from typing import Any, Iterator, Mapping
from urllib.parse import urljoin
from unittest.mock import patch

try:
    import jsonschema
except ImportError:  # Optional test-only schema verifier.
    jsonschema = None


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import atlas_connector  # noqa: E402
import atlas_index  # noqa: E402
import atlas_quality  # noqa: E402
import atlas_tool  # noqa: E402
import atlas_source  # noqa: E402
import atlas_transaction  # noqa: E402
import atlas_state  # noqa: E402


MANIFEST_URI = "vault://atlas/summaries/sources/MANIFEST.md"
TOPICS_URI = "vault://atlas/summaries/registry/TOPICS.md"
RELATIONS_URI = "vault://atlas/summaries/registry/RELATIONS.md"
INDEX_URI = (
    "vault://atlas/summaries/research/test/test-subdomain/topics/test-topic/INDEX.md"
)
REPORT_URI = "vault://atlas/summaries/sources/runs/2026/2026-07/report.md"
TOPIC_ID = "test-topic"
SOURCE_A_URL = "https://example.test/synthetic-a"
SOURCE_B_URL = "https://example.test/synthetic-b"
TOPIC_SUBDOMAIN_URI = "vault://atlas/summaries/research/test/test-subdomain/INDEX.md"
TOPIC_CREATE_URI = (
    "vault://atlas/summaries/research/test/test-subdomain/topics/new-topic/INDEX.md"
)
SOURCE_C_URL = "https://example.test/synthetic-c"
WORKER_SCHEMA_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "source-worker-result.schema.json"
)
PROPOSAL_SCHEMA_PATH = WORKER_SCHEMA_PATH.with_name(
    "source-summary-proposal.schema.json"
)

ALL_OPERATIONS = tuple(
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
            "url.resolve_reference",
            "discovery.normalize",
            "quality.validate_proposal",
            "quality.validate_summary",
            "quality.prepare_calibration",
            "quality.validate_calibration",
            "state.validate",
            "state.reduce",
            "source.render_summary",
            "source.normalize_capture",
            "source.merge_artifact",
            "source.render_route_artifact",
            "source.lookup",
            "source.inventory",
            "source.prepare",
            "source.prepare_route",
            "source.worker_schema",
            "source.snapshot_active",
            "migration.prepare_topics_lists",
            "migration.apply_topics_lists",
            "effect.execute",
            "effect.recover",
            "transaction.execute",
            "transaction.recover",
            "transaction.successor",
            "refresh.execute",
            "refresh.recover",
            "index.create_topic",
            "index.recover_topic",
            "topic.inspect",
            "research.prepare",
            "research.execute",
            "research.recover",
        }
    )
)
LIFECYCLE_OPERATIONS = tuple(
    operation
    for operation in ALL_OPERATIONS
    if operation
    not in {
        "discovery.normalize",
        "quality.prepare_calibration",
        "quality.validate_calibration",
        "source.merge_artifact",
        "source.render_route_artifact",
        "source.render_summary",
        "state.reduce",
        "transaction.execute",
        "transaction.recover",
        "transaction.successor",
        "vault.conditional_replace",
        "vault.delete_tree",
        "vault.write_json",
    }
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
            f"**Route status**: `{route_status}`",
            "",
            "## Reuse cues",
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


def padded_table(header: tuple[str, ...], rows: list[list[str]]) -> str:
    rendered = [
        "---",
        "schema_version: 1",
        "---",
        "",
        "|  " + "  |  ".join(header) + "  |",
        "|  " + "  |  ".join("---" for _ in header) + "  |",
    ]
    rendered.extend("|  " + "  |  ".join(row) + "  |" for row in rows)
    return "\n".join(rendered) + "\n"


def manifest_row(
    url: str,
    sequence: int,
    *,
    status: str = "active",
    route_status: str = "unrouted",
) -> list[str]:
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
        route_status,
        status,
    ]


def manifest_text(rows: list[list[str]]) -> str:
    return table(MANIFEST_HEADER, rows)


def relation_id(url: str) -> str:
    content_hash = sha256_text("synthetic payload 1\n")
    return f"edge--{source_id(url)}--{TOPIC_ID}--{content_hash[:8]}"


def relation_row(
    url: str = SOURCE_A_URL,
    *,
    status: str = "pending",
    applied_in_pass: str = "",
) -> list[str]:
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
        status,
        "2026-07-28",
        applied_in_pass,
        "Verifier: synthetic — synthetic [relation=direct; impact=high]",
    ]


def topics_text(
    *,
    pending_edge_ids: list[str] | None = None,
    state: str = "current",
    source_watermark: str = "0",
) -> str:
    pending_edge_ids = pending_edge_ids or []
    return table(
        TOPICS_HEADER,
        [
            [
                TOPIC_ID,
                "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
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
                source_watermark,
                "same-as-topic-creation",
            ]
        ],
    )


def relations_text(rows: list[list[str]] | None = None) -> str:
    return table(RELATIONS_HEADER, rows or [])


def topic_subdomain_text() -> str:
    return (
        "\n".join(
            (
                "---",
                "schema_version: 1",
                "note_type: subdomain-index",
                "managed_by: atlas",
                'domain: "test"',
                'subdomain: "test-subdomain"',
                'last_updated: "2026-07-28"',
                "tags: []",
                "---",
                "",
                "# Test subdomain",
                "",
                "## Routing scope",
                "<!-- atlas:managed:start routing-scope -->",
                "- Domain: `test`",
                "- Subdomain: `test-subdomain`",
                "- Include: test",
                "- Exclude: none",
                "<!-- atlas:managed:end routing-scope -->",
                "",
                "## Topic map",
                "<!-- atlas:managed:start topic-map -->",
                "| Topic | Default answer | Coverage | Freshness | Last updated | Link |",
                "|---|---|---|---|---|---|",
                "| Synthetic topic | Existing answer | Insufficient | Current | 2026-07-28 | summaries/research/test/test-subdomain/topics/test-topic/INDEX.md |",
                "<!-- atlas:managed:end topic-map -->",
                "",
                "## Default lookup order",
                "<!-- atlas:managed:start default-lookup-order -->",
                "1. Check `vault://atlas/summaries/registry/TOPICS.md` for topic path and freshness.",
                "2. Read the topic `INDEX.md` when `Freshness state=current`.",
                "3. Read optional split files only when the topic `INDEX.md` points to them.",
                "<!-- atlas:managed:end default-lookup-order -->",
                "",
                "## Coverage map",
                "<!-- atlas:managed:start coverage-map -->",
                "- Sufficient: <topics with usable current answers>",
                "- Partial: <topics with known gaps>",
                "- Insufficient: <topics needing acquisition>",
                "<!-- atlas:managed:end coverage-map -->",
                "",
                "## Stale or weak areas",
                "<!-- atlas:managed:start stale-or-weak-areas -->",
                "- <topic or gap> — <reason>",
                "<!-- atlas:managed:end stale-or-weak-areas -->",
                "",
                "## Acquisition watchlist",
                "<!-- atlas:managed:start acquisition-watchlist -->",
                "- feeds — check later",
                "<!-- atlas:managed:end acquisition-watchlist -->",
            )
        )
        + "\n"
    )


def topic_create_args(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "version": 1,
        "topic_id": "new-topic",
        "topic_path": TOPIC_CREATE_URI,
        "domain": "test",
        "subdomain": "test-subdomain",
        "canonical_title": "New topic",
        "aliases": [],
        "include_terms": ["test"],
        "exclude_terms": [],
        "related_topic_ids": [],
        "status": "active",
        "coverage_state": "insufficient",
        "confidence": "low",
        "refresh_model": "same-as-topic-creation",
        "created_on": "2026-08-02",
    }
    value.update(overrides)
    return value


def topic_registry_text() -> str:
    row = [
        TOPIC_ID,
        "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
        "test",
        "test-subdomain",
        "Synthetic topic",
        "",
        "",
        "test",
        "",
        "current",
        "0",
        "",
        "",
        "",
        "0",
        "same-as-topic-creation",
    ]
    return table(TOPICS_HEADER, [row])


def source_worker_packet(url: str) -> dict[str, Any]:
    payload = (
        "The source requires a verified handoff before mutation. "
        f"Rule 2 specifies the sequence and links to {url}#rule-2.\n"
    )
    return {
        "version": 1,
        "kind": "ready",
        "identity": {"canonical_url": url, "source_id": source_id(url)},
        "evidence_bundle": {
            "version": 1,
            "canonical_url": url,
            "source_urls": [f"{url}#rule-2"],
            "allowed_urls": [],
            "payload_text": payload,
            "fetched_at": "2026-07-31",
            "require_routing_reason": False,
            "unresolved_validation_caveat": False,
        },
        "evidence_ledger": {
            "version": 1,
            "evidence": [{"locator": "Rule 2", "ledger_id": "ledger-rule-2"}],
            "links": [
                {
                    "url": f"{url}#rule-2",
                    "locator": "Rule 2",
                    "ledger_id": "ledger-rule-2",
                }
            ],
        },
        "proposal": {
            "version": 1,
            "metadata": {
                "title": "Synthetic batch source",
                "author": "Example author",
                "publisher": "Example publisher",
                "published": "2026-07-31",
                "source_kind": "article",
            },
            "assessment": {
                "coverage": "complete",
                "confidence": "high",
                "evidence_strength": "high",
                "practicality": "high",
                "stability": "stable",
                "reuse_value": "high",
                "recommended_posture": "trial",
            },
            "claims": [
                {
                    "statement": "The source requires a verified handoff before mutation.",
                    "evidence": [{"locator": "Rule 2", "ledger_id": "ledger-rule-2"}],
                }
            ],
            "links": [
                {
                    "url": f"{url}#rule-2",
                    "relation": "related",
                    "locator": "Rule 2",
                    "ledger_id": "ledger-rule-2",
                }
            ],
        },
        "checklist": [
            {
                "id": item_id,
                "status": "pass",
                "evidence": "Rule 2 bounded source evidence",
            }
            for item_id in atlas_quality.CHECKLIST_IDS
        ],
        "refresh_after": "2027-07-31",
    }


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
    return {"version": 2, "op": op, "args": args}


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


class AfterWriteFailureConnector:
    def __init__(
        self,
        inner: Any,
        *,
        suffix: str,
        stop_process: bool = False,
    ) -> None:
        self._inner = inner
        self._suffix = suffix
        self._stop_process = stop_process
        self._interrupted = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
        path = str(args[0] if args else kwargs["path"])
        result = self._inner.conditional_replace(*args, **kwargs)
        if not self._interrupted and path.endswith(self._suffix):
            self._interrupted = True
            if self._stop_process:
                raise SystemExit(f"synthetic process stop: {path}")
            raise OSError(f"synthetic acknowledgement loss: {path}")
        return result


class RecoveryReadFailureConnector:
    def __init__(self, inner: Any, *, suffix: str) -> None:
        self._inner = inner
        self._suffix = suffix
        self._interrupted = False
        self._reads_after_interrupt = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def read_bytes(self, uri: str) -> bytes:
        if self._interrupted:
            self._reads_after_interrupt += 1
            if self._reads_after_interrupt == 2:
                raise OSError(f"synthetic recovery read failure: {uri}")
        return self._inner.read_bytes(uri)

    def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
        path = str(args[0] if args else kwargs["path"])
        result = self._inner.conditional_replace(*args, **kwargs)
        if not self._interrupted and path.endswith(self._suffix):
            self._interrupted = True
            raise OSError(f"synthetic interrupted replacement: {path}")
        return result


class AppliedRevisionFailureConnector:
    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self._applied = False
        self._failed = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def revision(self, uri: str) -> str:
        if self._applied and not self._failed:
            self._failed = True
            raise OSError(f"synthetic receipt revision failure: {uri}")
        return self._inner.revision(uri)

    def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
        path = str(args[0] if args else kwargs["path"])
        result = self._inner.conditional_replace(*args, **kwargs)
        if path.endswith("/applied.json"):
            self._applied = True
        return result


class RecoveryFaultConnector:
    def __init__(
        self,
        inner: Any,
        *,
        suffix: str,
        operation: str,
        error: str,
    ) -> None:
        self._inner = inner
        self._suffix = suffix
        self._operation = operation
        self._error = error
        self._faulted = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def _matches(self, path: str) -> bool:
        return path.endswith(self._suffix)

    def _raise(self, path: str) -> None:
        self._faulted = True
        message = f"synthetic recovery {self._operation} failure: {path}"
        if self._error == "transaction":
            raise atlas_transaction.TransactionError(message)
        raise OSError(message)

    def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
        path = str(args[0] if args else kwargs["path"])
        result = self._inner.conditional_replace(*args, **kwargs)
        if (
            not self._faulted
            and self._operation == "conditional_replace"
            and self._matches(path)
        ):
            self._raise(path)
        return result

    def revision(self, uri: str) -> str:
        if not self._faulted and self._operation == "revision" and self._matches(uri):
            self._raise(uri)
        return self._inner.revision(uri)

    def read_bytes(self, uri: str) -> bytes:
        if not self._faulted and self._operation == "read_bytes" and self._matches(uri):
            self._raise(uri)
        return self._inner.read_bytes(uri)

    def list(self, path: str) -> list[str]:
        if not self._faulted and self._operation == "list" and self._matches(path):
            self._raise(path)
        return self._inner.list(path)


class ClassificationValueErrorConnector:
    def __init__(self, inner: Any, *, path: str) -> None:
        self._inner = inner
        self._path = path

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def read_bytes(self, uri: str) -> bytes:
        if uri == self._path or uri.removeprefix("vault://atlas/") == self._path:
            raise ValueError(f"symlink is not allowed: {uri}")
        return self._inner.read_bytes(uri)


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


class RecordingTopicConnector:
    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.reads: list[str] = []
        self.writes: list[str] = []
        self.deletes: list[str] = []
        self.mutation_sessions = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def _logical(self, value: str) -> str:
        return value if value.startswith("vault://") else f"vault://atlas/{value}"

    def capabilities(self) -> dict[str, Any]:
        return self._inner.capabilities()

    def mutation_session(self) -> Any:
        self.mutation_sessions += 1
        return self._inner.mutation_session()

    def read_bytes(self, uri: str) -> bytes:
        logical = self._logical(uri)
        self.reads.append(logical)
        return self._inner.read_bytes(uri)

    def revision(self, uri: str) -> str:
        logical = self._logical(uri)
        self.reads.append(logical)
        return self._inner.revision(uri)

    def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
        value = args[0] if args else kwargs["path"]
        logical = self._logical(str(value))
        self.writes.append(logical)
        return self._inner.conditional_replace(*args, **kwargs)

    def delete(self, path: str, expected_revision: str) -> None:
        logical = self._logical(path)
        self.deletes.append(logical)
        self._inner.delete(path, expected_revision)


class StaleTopicConnector(RecordingTopicConnector):
    def __init__(self, inner: Any) -> None:
        super().__init__(inner)
        self._drifted = False

    def read_bytes(self, uri: str) -> bytes:
        raw = super().read_bytes(uri)
        if uri == TOPIC_SUBDOMAIN_URI and not self._drifted:
            self._drifted = True
            current = self._inner.revision(TOPIC_SUBDOMAIN_URI)
            self._inner.conditional_replace(
                TOPIC_SUBDOMAIN_URI,
                current,
                b"stale subdomain\n",
            )
        return raw


class ReadOnlyTopicConnector:
    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def capabilities(self) -> dict[str, Any]:
        capabilities = dict(self._inner.capabilities())
        capabilities["conditional_replace"] = "unavailable"
        capabilities["operations"] = [
            operation
            for operation in capabilities["operations"]
            if operation
            not in {
                "conditional_replace",
                "delete",
                "delete_tree",
                "mutation_session",
                "write_json",
            }
        ]
        return capabilities


class RecordingReadOnlyConnector:
    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.read_log: list[str] = []

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def capabilities(self) -> dict[str, Any]:
        capabilities = dict(self._inner.capabilities())
        capabilities["conditional_replace"] = "unavailable"
        capabilities["operations"] = [
            operation
            for operation in capabilities["operations"]
            if operation
            not in {
                "conditional_replace",
                "delete",
                "delete_tree",
                "mutation_session",
                "write_json",
            }
        ]
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


def topic_transaction_id(response: Mapping[str, Any]) -> str:
    paths = [
        finding["path"]
        for finding in response["findings"]
        if finding["path"].endswith("/intent.json")
    ]
    if len(paths) != 1:
        raise AssertionError(response)
    return Path(paths[0]).parent.name


def topic_event_transaction_id(fixture: TemporaryAtlasProfile) -> str:
    paths = [
        path
        for path in fixture.connector().list("vault://atlas/.atlas/transactions/topics")
        if path.endswith("/event.json")
    ]
    if len(paths) != 1:
        raise AssertionError(paths)
    return Path(paths[0]).parent.name


def topic_transaction_root(fixture: TemporaryAtlasProfile, transaction_id: str) -> str:
    suffix = f"/{transaction_id}/event.json"
    matches = [
        path.removesuffix("/event.json")
        for path in fixture.connector().list("vault://atlas/.atlas/transactions/topics")
        if path.endswith(suffix)
    ]
    if len(matches) != 1:
        raise AssertionError(matches)
    return matches[0]


def write_topic_transaction_records(
    fixture: TemporaryAtlasProfile,
    request_value: dict[str, Any],
    targets: tuple[atlas_transaction.TransactionTarget, ...],
    *,
    status: str = "applied",
) -> str:
    request_hash = atlas_index.sha256(atlas_index.canonical_json(request_value))
    namespace = atlas_index.topic_namespace_sha256(request_value)
    uri_targets = tuple(
        atlas_index.TopicTarget(
            atlas_tool._logical(target.path),
            target.input_bytes,
            target.output_bytes,
        )
        for target in targets
    )
    base_id = atlas_index.topic_base_transaction_id(request_value, uri_targets)
    event_record = {
        "version": 1,
        "event_type": atlas_index.TOPIC_CREATE_EVENT_TYPE,
        "owner": atlas_index.TOPIC_OWNER_ID,
        "topic_namespace_sha256": namespace,
        "base_transaction_id": base_id,
        "request_sha256": request_hash,
        "request": request_value,
    }
    plan = atlas_tool._index_plan(event_record, targets)
    base = f"vault://atlas/{plan.transaction_root}/{plan.transaction_id}"
    fixture.put(
        f"{base}/event.json",
        atlas_transaction.canonical_json(
            atlas_transaction.event_record_value(event_record, plan)
        ).decode("utf-8"),
    )
    fixture.put(
        f"{base}/intent.json",
        atlas_transaction.canonical_json(plan.intent).decode("utf-8"),
    )
    backup_hashes: list[str] = []
    for index, target in enumerate(plan.targets):
        backup = atlas_transaction.canonical_json(
            {
                "version": 1,
                "path": target.path,
                "input_sha256": (
                    None
                    if target.input_bytes is None
                    else atlas_transaction.sha256(target.input_bytes)
                ),
                "input_base64": (
                    None
                    if target.input_bytes is None
                    else base64.b64encode(target.input_bytes).decode("ascii")
                ),
            }
        )
        backup_hashes.append(atlas_transaction.sha256(backup))
        fixture.put(f"{base}/backups/{index:06d}.json", backup.decode("utf-8"))
    intent_hash = atlas_transaction.sha256(
        atlas_transaction.canonical_json(plan.intent)
    )
    fixture.put(
        f"{base}/prepared.json",
        atlas_transaction.canonical_json(
            {
                "version": 1,
                "intent_sha256": intent_hash,
                "backup_sha256s": backup_hashes,
            }
        ).decode("utf-8"),
    )
    if status == "applied":
        for index, target in enumerate(plan.targets):
            fixture.put(
                f"{base}/progress/{index:06d}.json",
                atlas_transaction.canonical_json(
                    {
                        "version": 1,
                        "index": index,
                        "path": target.path,
                        "output_sha256": atlas_transaction.sha256(target.output_bytes),
                    }
                ).decode("utf-8"),
            )
    terminal = {"version": 1, "status": status, "intent_sha256": intent_hash}
    if status == "applied":
        terminal["owner_proof"] = {
            "owner": atlas_index.TOPIC_OWNER_ID,
            "policy": "topic-post-v1",
            "request_sha256": request_hash,
            "target_output_sha256s": [
                atlas_transaction.sha256(target.output_bytes) for target in plan.targets
            ],
        }
    fixture.put(
        f"{base}/{status}.json",
        atlas_transaction.canonical_json(terminal).decode("utf-8"),
    )
    return plan.transaction_id


class AtlasToolTests(unittest.TestCase):
    maxDiff = None

    def prepare_topic_fixture(self, fixture: TemporaryAtlasProfile) -> None:
        fixture.put(TOPICS_URI, topic_registry_text())
        fixture.put(TOPIC_SUBDOMAIN_URI, topic_subdomain_text())

    def prepare_audit_fixture(self, fixture: TemporaryAtlasProfile) -> list[str]:
        urls = [f"https://example.test/source-{index}" for index in range(1, 8)]
        rows = [manifest_row(url, index) for index, url in enumerate(urls, start=1)]
        fixture.put(MANIFEST_URI, manifest_text(rows))
        fixture.put(RELATIONS_URI, relations_text())
        fixture.put(TOPICS_URI, topics_text())
        for index, url in enumerate(urls, start=1):
            fixture.put(artifact_uri(url), artifact_text(url, index))
        return urls

    def assert_envelope(
        self, response: dict[str, Any], *, ok: bool, op: str | None
    ) -> None:
        self.assertEqual(
            set(response),
            {
                "version",
                "ok",
                "op",
                "disposition",
                "result",
                "findings",
                "recovery",
            },
        )
        self.assertEqual(response["version"], 2)
        self.assertIs(response["ok"], ok)
        self.assertEqual(response["op"], op)
        self.assertEqual(
            response_findings(response), sorted(response_findings(response))
        )
        if ok:
            self.assertIn(response["disposition"], {"completed", "no-write"})
            self.assertIsInstance(response["result"], dict)
            self.assertEqual(response["findings"], [])
            self.assertIsNone(response["recovery"])
        else:
            self.assertIn(
                response["disposition"],
                {
                    "rejected",
                    "needs-guidance",
                    "needs-retry",
                    "unavailable",
                    "recovery-required",
                    "manual-intervention",
                    "internal-error",
                },
            )
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

    def test_topic_inspect_locks_registries_for_absent_and_invalid_selection(
        self,
    ) -> None:
        class SnapshotRecordingConnector:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.snapshots: list[tuple[str, ...]] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def consistent_read(self, paths: list[str]) -> dict[str, dict[str, Any]]:
                self.snapshots.append(tuple(paths))
                return self._inner.consistent_read(paths)

        registry_uris = (MANIFEST_URI, TOPICS_URI, RELATIONS_URI)
        with temporary_profile() as fixture:
            absent_connector = SnapshotRecordingConnector(fixture.connector())
            absent = invoke(
                fixture,
                "topic.inspect",
                connector=absent_connector,
                topic_id="missing-topic",
                purpose="answer",
            )
            self.assertFalse(absent["ok"])
            self.assertEqual(response_findings(absent)[0][0], "TOPIC_INSPECTION_ABSENT")
            self.assertEqual(absent_connector.snapshots, [registry_uris])

            fixture.put(TOPICS_URI, "malformed\n")
            invalid_connector = SnapshotRecordingConnector(fixture.connector())
            invalid = invoke(
                fixture,
                "topic.inspect",
                connector=invalid_connector,
                topic_id=TOPIC_ID,
                purpose="answer",
            )
            self.assertFalse(invalid["ok"])
            self.assertEqual(
                response_findings(invalid)[0][0], "TOPIC_INSPECTION_INVALID"
            )
            self.assertEqual(invalid_connector.snapshots, [registry_uris])

    def test_topic_inspect_rejects_candidate_to_locked_selection_drift(
        self,
    ) -> None:
        class DriftingConnector:
            def __init__(
                self,
                inner: Any,
                fixture: TemporaryAtlasProfile,
                locked_manifest: str | None,
                locked_topics: str,
                locked_relations: str,
            ) -> None:
                self._inner = inner
                self._fixture = fixture
                self._locked_manifest = locked_manifest
                self._locked_topics = locked_topics
                self._locked_relations = locked_relations

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def consistent_read(self, paths: list[str]) -> dict[str, dict[str, Any]]:
                if self._locked_manifest is not None:
                    self._fixture.put(MANIFEST_URI, self._locked_manifest)
                self._fixture.put(TOPICS_URI, self._locked_topics)
                self._fixture.put(RELATIONS_URI, self._locked_relations)
                return self._inner.consistent_read(paths)

        pending_edge = relation_id(SOURCE_A_URL)
        cases = {
            "same-path-pending": (
                manifest_text([manifest_row(SOURCE_A_URL, 1, route_status="routed")]),
                topics_text(
                    pending_edge_ids=[pending_edge],
                    state="dirty",
                    source_watermark="0",
                ),
                relations_text([relation_row()]),
            ),
            "active-to-absent": (
                None,
                table(TOPICS_HEADER, []),
                relations_text(),
            ),
            "active-to-invalid": (
                None,
                "malformed\n",
                relations_text(),
            ),
        }
        for name, (
            locked_manifest,
            locked_topics,
            locked_relations,
        ) in cases.items():
            with self.subTest(name=name), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                connector = DriftingConnector(
                    fixture.connector(),
                    fixture,
                    locked_manifest,
                    locked_topics,
                    locked_relations,
                )
                response = invoke(
                    fixture,
                    "topic.inspect",
                    connector=connector,
                    topic_id=TOPIC_ID,
                    purpose="answer",
                )
                self.assertFalse(response["ok"])
                self.assertEqual(
                    response_findings(response)[0][0],
                    "TOPIC_INSPECTION_UNAVAILABLE",
                )
                self.assertIsNone(response["result"])

    def test_research_execute_declares_snapshot_and_mutation_capabilities(
        self,
    ) -> None:
        class NoConsistentReadConnector:
            consistent_read = None

            def __init__(self, inner: Any) -> None:
                self._inner = inner

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def capabilities(self) -> dict[str, Any]:
                values = dict(self._inner.capabilities())
                values["operations"] = [
                    operation
                    for operation in values["operations"]
                    if operation != "consistent_read"
                ]
                return values

        expected_methods = {
            "read_text",
            "consistent_read",
            "read_bytes",
            "revision",
            "list",
            "mutation_session",
            "conditional_replace",
            "delete",
        }
        with temporary_profile() as fixture:
            available = atlas_tool.capabilities(fixture.connector())
            execute_spec = next(
                operation
                for operation in available["result"]["operations"]
                if operation["operation"] == "research.execute"
            )
            self.assertEqual(set(execute_spec["connector_methods"]), expected_methods)

            connector = NoConsistentReadConnector(fixture.connector())
            unavailable = atlas_tool.capabilities(connector)
            advertised = {
                operation["operation"]
                for operation in unavailable["result"]["operations"]
            }
            self.assertNotIn("research.execute", advertised)
            self.assertIn("research.recover", advertised)
            rejected = invoke(
                fixture, "research.execute", connector=connector, prepared={}
            )
            self.assertFalse(rejected["ok"])
            self.assertEqual(response_findings(rejected)[0][0], "MUTATION_UNAVAILABLE")

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
            "promotion": None,
            "event": event,
            "route_decision": {"outcome": "no-topic-match", "edges": []},
        }
        documents = {
            "manifest": self.read_text(fixture, MANIFEST_URI),
            "topics": self.read_text(fixture, TOPICS_URI),
            "relations": self.read_text(fixture, RELATIONS_URI),
        }
        reduction = atlas_state.reduce_event(documents, event)
        self.assertTrue(reduction.ok, reduction.to_dict())
        candidate_documents = {**documents, **reduction.documents}
        row, findings = atlas_state.lookup_manifest_row(
            candidate_documents["manifest"], route_url
        )
        self.assertEqual(findings, [])
        self.assertIsNotNone(row)
        assert row is not None
        target_uri = artifact_uri(route_url)
        current_artifact = self.read_text(fixture, target_uri)
        rendered_artifact = atlas_source.render_route_artifact(
            current_artifact,
            event,
            row["Route status"],
        )
        artifact_output = output_text if output_text is not None else rendered_artifact
        projected: list[tuple[str, str]] = []
        if artifact_output != current_artifact:
            projected.append((target_uri, artifact_output))
        for name, uri in (
            ("relations", RELATIONS_URI),
            ("topics", TOPICS_URI),
            ("manifest", MANIFEST_URI),
        ):
            if name in reduction.documents:
                projected.append((uri, reduction.documents[name]))
        self.assertTrue(projected)
        return {
            "event_record": event_record,
            "targets": [
                {
                    "path": uri,
                    "expected_revision": self.revision(fixture, uri),
                    "text": text,
                }
                for uri, text in projected
            ],
        }

    def prepare_route_args(
        self,
        fixture: TemporaryAtlasProfile,
        *,
        decision: dict[str, Any] | None = None,
        checked_on: str = "2026-08-17",
    ) -> dict[str, Any]:
        lookup = invoke(fixture, "source.lookup", url=SOURCE_A_URL)
        self.assert_envelope(lookup, ok=True, op="source.lookup")
        if decision is None:
            decision = {"outcome": "no-topic-match", "edges": []}
        return {
            "binding": lookup["result"],
            "checked_on": checked_on,
            "expected_revisions": {
                "artifact": self.revision(fixture, artifact_uri(SOURCE_A_URL)),
                "topics": self.revision(fixture, TOPICS_URI),
                "relations": self.revision(fixture, RELATIONS_URI),
            },
            "decision": decision,
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
                        "promotion": None,
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
            route_artifact = atlas_source.render_route_artifact(
                source_artifact,
                route_event,
                "no-topic-match",
            )
            transactions.append(
                {
                    "stage": "route",
                    "event_record": {
                        "version": 1,
                        "event_type": "route",
                        "source_id": source_id(source_url),
                        "promotion": None,
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
                            "text": route_artifact,
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
            "vault://atlas/summaries/research/test/test-subdomain/topics/test-topic/passes/"
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

    def test_state_validate_preserves_registry_findings_and_input_taxonomy(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            documents = {
                "manifest": self.read_text(fixture, MANIFEST_URI),
                "topics": topic_registry_text().replace(
                    "| Synthetic topic |  |  | test |  |",
                    "| Synthetic topic | z; a |  | z; test |  |",
                ),
                "relations": self.read_text(fixture, RELATIONS_URI),
            }

            invalid = invoke(fixture, "state.validate", documents=documents)
            self.assert_envelope(invalid, ok=False, op="state.validate")
            self.assertEqual(
                response_findings(invalid),
                [
                    (
                        "TOPIC_LIST_INVALID",
                        "summaries/registry/TOPICS.md",
                        '{"detail":"Aliases","line":7,"row":"test-topic"}',
                    ),
                    (
                        "TOPIC_LIST_INVALID",
                        "summaries/registry/TOPICS.md",
                        '{"detail":"Include terms","line":7,"row":"test-topic"}',
                    ),
                ],
            )

            malformed_cases = (
                (
                    "missing",
                    {
                        key: value
                        for key, value in documents.items()
                        if key != "relations"
                    },
                    "args.documents.relations",
                    "document is missing",
                ),
                (
                    "extra",
                    {**documents, "unexpected": documents["manifest"]},
                    "args.documents.unexpected",
                    "document key is unknown",
                ),
                (
                    "non-text",
                    {**documents, "topics": []},
                    "args.documents.topics",
                    "document must be text",
                ),
                (
                    "non-object",
                    [],
                    "args.documents",
                    "documents must be an object",
                ),
            )
            for label, malformed, path, detail in malformed_cases:
                with self.subTest(label=label):
                    response = invoke(fixture, "state.validate", documents=malformed)
                    self.assert_envelope(response, ok=False, op="state.validate")
                    self.assertEqual(
                        response_findings(response),
                        [("STATE_INPUT_INVALID", path, detail)],
                    )

    def test_state_validate_preserves_owner_finding_locations_and_duplicates(
        self,
    ) -> None:
        class ObjectFinding:
            code = "OWNER_FINDING"
            path = "owner.path"
            line = 9
            row = "second"
            detail = "same"

        with temporary_profile() as fixture:
            documents = {
                "manifest": self.read_text(fixture, MANIFEST_URI),
                "topics": self.read_text(fixture, TOPICS_URI),
                "relations": self.read_text(fixture, RELATIONS_URI),
            }
            mapping = {
                "code": "OWNER_FINDING",
                "path": "owner.path",
                "line": 8,
                "row": "first",
                "detail": "same",
            }
            duplicate = dict(mapping)
            plain = {
                "code": "PLAIN_FINDING",
                "path": "owner.path",
                "detail": "unchanged",
            }
            with patch.object(
                atlas_state,
                "validate_documents",
                return_value=[mapping, ObjectFinding(), duplicate, plain],
            ):
                response = invoke(fixture, "state.validate", documents=documents)

            self.assert_envelope(response, ok=False, op="state.validate")
            self.assertEqual(
                response_findings(response),
                [
                    (
                        "OWNER_FINDING",
                        "owner.path",
                        '{"detail":"same","line":8,"row":"first"}',
                    ),
                    (
                        "OWNER_FINDING",
                        "owner.path",
                        '{"detail":"same","line":9,"row":"second"}',
                    ),
                    ("PLAIN_FINDING", "owner.path", "unchanged"),
                ],
            )

    def test_state_validate_synthetic_list_pair_through_facade(self) -> None:
        def topic_row(
            topic_id: str,
            title: str,
            *,
            aliases: str = "",
            canonical_tags: str = "",
            include_terms: str = "test",
            exclude_terms: str = "",
        ) -> list[str]:
            return [
                topic_id,
                f"summaries/research/test/test-subdomain/topics/{topic_id}/INDEX.md",
                "test",
                "test-subdomain",
                title,
                aliases,
                canonical_tags,
                include_terms,
                exclude_terms,
                "current",
                "0",
                "",
                "",
                "",
                "0",
                "same-as-topic-creation",
            ]

        pre_rows = [
            topic_row(
                "synthetic-alpha",
                "Synthetic alpha",
                aliases="z; a",
                canonical_tags="tag-b; tag-a",
                include_terms="term-z; term-a",
            ),
            topic_row(
                "synthetic-beta",
                "Synthetic beta",
                aliases="beta-z; beta-a",
                exclude_terms="exclude-z; exclude-a",
            ),
            topic_row(
                "synthetic-gamma",
                "Synthetic gamma",
                include_terms="gamma-z; gamma-a",
                exclude_terms="gamma-exclude-z; gamma-exclude-a",
            ),
        ]
        post_rows = [list(row) for row in pre_rows]
        canonical_cells = (
            (0, 5, "a; z"),
            (0, 6, "tag-a; tag-b"),
            (0, 7, "term-a; term-z"),
            (1, 5, "beta-a; beta-z"),
            (1, 8, "exclude-a; exclude-z"),
            (2, 7, "gamma-a; gamma-z"),
            (2, 8, "gamma-exclude-a; gamma-exclude-z"),
        )
        for row_index, column_index, canonical in canonical_cells:
            post_rows[row_index][column_index] = canonical
        pre = table(TOPICS_HEADER, pre_rows)
        post = table(TOPICS_HEADER, post_rows)
        self.assertEqual(
            sum(
                before != after
                for before_row, after_row in zip(pre_rows, post_rows, strict=True)
                for before, after in zip(before_row, after_row, strict=True)
            ),
            7,
        )

        command = [
            sys.executable,
            str(ROOT / "scripts" / "atlas_tool.py"),
            "call",
            "--input",
            "-",
        ]
        with temporary_profile() as fixture:
            fixture.put(TOPICS_URI, post)
            env = {**os.environ, "ATLAS_VAULT_PROFILE": str(fixture.profile)}

            def call(request_value: dict[str, Any]) -> tuple[int, dict[str, Any]]:
                completed = subprocess.run(
                    command,
                    cwd=ROOT,
                    env=env,
                    input=json.dumps(request_value).encode("utf-8"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(completed.stderr, b"")
                return completed.returncode, json.loads(completed.stdout)

            manifest_code, manifest_response = call(
                request("vault.read", {"path": MANIFEST_URI})
            )
            relations_code, relations_response = call(
                request("vault.read", {"path": RELATIONS_URI})
            )
            self.assertEqual(manifest_code, 0)
            self.assertEqual(relations_code, 0)
            self.assert_envelope(manifest_response, ok=True, op="vault.read")
            self.assert_envelope(relations_response, ok=True, op="vault.read")

            manifest = manifest_response["result"]["text"]
            relations = relations_response["result"]["text"]

            def validate(topics: str) -> tuple[int, dict[str, Any]]:
                return call(
                    request(
                        "state.validate",
                        {
                            "documents": {
                                "manifest": manifest,
                                "topics": topics,
                                "relations": relations,
                            }
                        },
                    )
                )

            pre_code, pre_response = validate(pre)
            expected_pairs = [
                (7, "synthetic-alpha", "Aliases"),
                (7, "synthetic-alpha", "Canonical tags"),
                (7, "synthetic-alpha", "Include terms"),
                (8, "synthetic-beta", "Aliases"),
                (8, "synthetic-beta", "Exclude terms"),
                (9, "synthetic-gamma", "Include terms"),
                (9, "synthetic-gamma", "Exclude terms"),
            ]
            expected_findings = sorted(
                (
                    "TOPIC_LIST_INVALID",
                    "summaries/registry/TOPICS.md",
                    json.dumps(
                        {"detail": detail, "line": line, "row": row},
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
                for line, row, detail in expected_pairs
            )
            self.assertEqual(pre_code, 2)
            self.assert_envelope(pre_response, ok=False, op="state.validate")
            self.assertEqual(response_findings(pre_response), expected_findings)
            self.assertEqual(len(pre_response["findings"]), 7)

            post_code, post_response = validate(post)
            self.assertEqual(post_code, 0)
            self.assert_envelope(post_response, ok=True, op="state.validate")
            self.assertEqual(response_findings(post_response), [])

            live_code, live_response = call(request("state.validate", {}))
            self.assertEqual(live_code, 0)
            self.assert_envelope(live_response, ok=True, op="state.validate")
            self.assertEqual(response_findings(live_response), [])

    def test_capabilities_are_exact_sorted_truthful_and_logical(self) -> None:
        with temporary_profile() as fixture:
            response = atlas_tool.capabilities(connector=fixture.connector())
            self.assert_envelope(response, ok=True, op="capabilities")
            result = response["result"]
            self.assertEqual(result["binding"]["adapter"], "atlas-local-fs-cas-v1")
            self.assertEqual(result["binding"]["logical_root"], "vault://atlas/")
            operations = [item["operation"] for item in result["operations"]]
            self.assertEqual(operations, list(LIFECYCLE_OPERATIONS))
            self.assertEqual(operations, sorted(operations))
            all_response = atlas_tool.capabilities(
                connector=fixture.connector(),
                include_internal=True,
            )
            self.assert_envelope(all_response, ok=True, op="capabilities")
            all_operations = [
                item["operation"] for item in all_response["result"]["operations"]
            ]
            self.assertEqual(all_operations, list(ALL_OPERATIONS))
            self.assertEqual(
                [spec.literal for spec in atlas_tool.operation_specs()],
                list(ALL_OPERATIONS),
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

    def test_reference_resolution_is_read_only_and_canonical(self) -> None:
        with temporary_profile() as fixture:
            response = invoke(
                fixture,
                "url.resolve_reference",
                base_url="https://example.test/guides/current",
                reference="source?utm_source=fixture#section",
            )
            self.assert_envelope(response, ok=True, op="url.resolve_reference")
            self.assertEqual(
                response["result"]["canonical_url"],
                "https://example.test/guides/source",
            )
            self.assertEqual(
                response["result"]["source_id"],
                source_id("https://example.test/guides/source"),
            )

    def test_source_inventory_reads_manifest_once_and_classifies_inputs(self) -> None:
        with temporary_profile() as fixture:
            active_due = manifest_row(SOURCE_A_URL, 1)
            active_due[8] = "2020-01-01"
            active_not_due = manifest_row(SOURCE_B_URL, 2)
            active_not_due[8] = "2999-01-01"
            fixture.put(
                MANIFEST_URI,
                manifest_text(
                    [
                        active_due,
                        active_not_due,
                        manifest_row(SOURCE_C_URL, 3, status="archived"),
                    ]
                ),
            )
            connector = RecordingReadOnlyConnector(fixture.connector())

            response = invoke(
                fixture,
                "source.inventory",
                connector=connector,
                intent="routine",
                checked_on="2026-08-15",
                inputs=[
                    {"label": "due", "url": SOURCE_A_URL, "depth": 0},
                    {"label": "not due", "url": SOURCE_B_URL, "depth": 1},
                    {
                        "label": "duplicate",
                        "url": "HTTPS://EXAMPLE.TEST/synthetic-b?utm_source=fixture",
                        "depth": 1,
                    },
                    {"label": "archived", "url": SOURCE_C_URL, "depth": 0},
                    {"label": "new", "url": "https://example.test/new", "depth": 0},
                    {"label": "invalid", "url": "not a URL", "depth": 0},
                ],
            )

            self.assert_envelope(response, ok=True, op="source.inventory")
            entries = response["result"]["entries"]
            self.assertEqual(
                [item["disposition"] for item in entries],
                [
                    "active-due",
                    "active-not-due",
                    "duplicate",
                    "archived",
                    "new",
                    "rejected",
                ],
            )
            self.assertEqual(
                [item["label"] for item in entries],
                ["due", "not due", "duplicate", "archived", "new", "invalid"],
            )
            self.assertEqual(entries[2]["winner_input_index"], 1)
            self.assertEqual(
                entries[0]["manifest_row"]["source_id"], source_id(SOURCE_A_URL)
            )
            self.assertEqual(response["result"]["checked_on"], "2026-08-15")
            self.assertEqual(connector.read_log, [MANIFEST_URI])

            collision_connector = RecordingReadOnlyConnector(fixture.connector())
            with patch.object(
                atlas_tool.atlas_url, "source_id_for", return_value="f" * 12
            ):
                collision = invoke(
                    fixture,
                    "source.inventory",
                    connector=collision_connector,
                    intent="presence",
                    checked_on="2026-08-15",
                    inputs=[
                        {
                            "label": "first collision",
                            "url": "https://example.test/collision-a",
                            "depth": 0,
                        },
                        {
                            "label": "second collision",
                            "url": "https://example.test/collision-b",
                            "depth": 0,
                        },
                    ],
                )
            self.assert_envelope(collision, ok=True, op="source.inventory")
            self.assertEqual(
                [entry["disposition"] for entry in collision["result"]["entries"]],
                ["rejected", "rejected"],
            )
            self.assertEqual(
                {
                    entry["findings"][0]["code"]
                    for entry in collision["result"]["entries"]
                },
                {"SOURCE_ID_COLLISION"},
            )
            self.assertEqual(collision_connector.read_log, [MANIFEST_URI])

    def test_topics_list_migration_is_two_phase_and_cas_guarded(self) -> None:
        class CountingConnector:
            def __init__(self, inner: Any) -> None:
                self.inner = inner
                self.cas_paths: list[str] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self.inner, name)

            def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
                path = str(args[0] if args else kwargs["path"])
                self.cas_paths.append(path)
                return self.inner.conditional_replace(*args, **kwargs)

        with temporary_profile() as fixture:
            urls = self.prepare_audit_fixture(fixture)
            counter = CountingConnector(fixture.connector())
            no_op = invoke(
                fixture,
                "migration.prepare_topics_lists",
                connector=counter,
            )
            self.assert_envelope(no_op, ok=True, op="migration.prepare_topics_lists")
            self.assertEqual(no_op["result"]["state"], "no-op")
            self.assertEqual(no_op["result"]["candidate"], None)
            self.assertEqual(counter.cas_paths, [])

            topic_lines = topics_text().splitlines()
            for index, line in enumerate(topic_lines):
                cells = atlas_state.split_markdown_row(line)
                if cells and cells[0] == TOPIC_ID:
                    cells[5] = "z; a"
                    topic_lines[index] = "| " + " | ".join(cells) + " |"
            fixture.put(TOPICS_URI, "\n".join(topic_lines) + "\n")
            candidate = invoke(
                fixture,
                "migration.prepare_topics_lists",
                connector=counter,
            )
            self.assert_envelope(
                candidate, ok=True, op="migration.prepare_topics_lists"
            )
            candidate_value = candidate["result"]["candidate"]
            self.assertEqual(candidate["result"]["state"], "candidate")
            self.assertEqual(
                candidate_value["approval_literal"],
                "APPLY ATLAS TOPICS LISTS "
                + candidate["result"]["binding"]["instance_id"]
                + " "
                + candidate_value["candidate_sha256"],
            )
            approval_args = {
                "instance_id": candidate["result"]["binding"]["instance_id"],
                "candidate_sha256": candidate_value["candidate_sha256"],
                "approval": candidate_value["approval_literal"],
            }
            denied = invoke(
                fixture,
                "migration.apply_topics_lists",
                connector=counter,
                **{**approval_args, "approval": "wrong"},
            )
            self.assert_envelope(denied, ok=False, op="migration.apply_topics_lists")
            self.assertEqual(counter.cas_paths, [])

            stale_manifest = manifest_text(
                [
                    manifest_row(url, index, status="archived")
                    for index, url in enumerate(urls, start=1)
                ]
            )
            fixture.put(MANIFEST_URI, stale_manifest)
            stale = invoke(
                fixture,
                "migration.apply_topics_lists",
                connector=counter,
                **approval_args,
            )
            self.assert_envelope(stale, ok=False, op="migration.apply_topics_lists")
            self.assertEqual(stale["findings"][0]["code"], "MIGRATION_CANDIDATE_STALE")
            self.assertEqual(counter.cas_paths, [])
            fixture.put(
                MANIFEST_URI,
                manifest_text(
                    [
                        manifest_row(url, index)
                        for index, url in enumerate(urls, start=1)
                    ]
                ),
            )

            applied = invoke(
                fixture,
                "migration.apply_topics_lists",
                connector=counter,
                **approval_args,
            )
            self.assert_envelope(applied, ok=True, op="migration.apply_topics_lists")
            self.assertEqual(applied["result"]["state"], "applied")
            self.assertEqual(counter.cas_paths, [TOPICS_URI])

            invalid_counter = CountingConnector(fixture.connector())
            invalid_lines = topics_text().splitlines()
            for index, line in enumerate(invalid_lines):
                cells = atlas_state.split_markdown_row(line)
                if cells and cells[0] == TOPIC_ID:
                    cells[5] = "a; a"
                    invalid_lines[index] = "| " + " | ".join(cells) + " |"
            fixture.put(TOPICS_URI, "\n".join(invalid_lines) + "\n")
            invalid = invoke(
                fixture,
                "migration.prepare_topics_lists",
                connector=invalid_counter,
            )
            self.assert_envelope(invalid, ok=False, op="migration.prepare_topics_lists")
            self.assertEqual(invalid_counter.cas_paths, [])

    def test_normalize_capture_facade_is_pure_and_fails_closed(self) -> None:
        capture = {
            "version": 1,
            "requested_url": "HTTPS://Example.test:443/synthetic",
            "final_url": "https://example.test/synthetic.md",
            "content_type": "text/markdown",
            "method": "md-suffix",
            "complete": True,
            "notes": ["Found .md suffix version"],
            "text": "# Synthetic\n\nRésumé 東京.\n",
        }
        response = atlas_tool.execute(
            request("source.normalize_capture", {"capture": capture}),
            connector=object(),
        )
        self.assert_envelope(response, ok=True, op="source.normalize_capture")
        self.assertEqual(
            response["result"]["canonical_url"], "https://example.test/synthetic"
        )
        self.assertEqual(response["result"]["final_url"], capture["final_url"])
        self.assertEqual(response["result"]["method"], capture["method"])
        self.assertEqual(
            response["result"]["content_hash"],
            hashlib.sha256(capture["text"].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            response["result"]["payload_bytes"],
            len(capture["text"].encode("utf-8")),
        )

        for field, invalid_value in (
            ("complete", False),
            ("content_type", "application/octet-stream"),
        ):
            with self.subTest(field=field):
                invalid = atlas_tool.execute(
                    request(
                        "source.normalize_capture",
                        {"capture": {**capture, field: invalid_value}},
                    ),
                    connector=object(),
                )
                self.assert_envelope(invalid, ok=False, op="source.normalize_capture")
                self.assertEqual(invalid["findings"][0]["code"], "CAPTURE_INVALID")

    def test_source_worker_schema_facade_is_exact_and_transport_safe(self) -> None:
        response = atlas_tool.execute(request("source.worker_schema", {}))
        self.assert_envelope(response, ok=True, op="source.worker_schema")
        self.assertEqual(set(response["result"]), {"schema"})
        schema = response["result"]["schema"]
        repeat = atlas_tool.execute(request("source.worker_schema", {}))
        self.assert_envelope(repeat, ok=True, op="source.worker_schema")
        self.assertEqual(repeat["result"], response["result"])

        def walk(value: Any) -> list[dict[str, Any]]:
            if isinstance(value, dict):
                return [value, *sum((walk(item) for item in value.values()), [])]
            if isinstance(value, list):
                return sum((walk(item) for item in value), [])
            return []

        nodes = walk(schema)
        for node in nodes:
            self.assertFalse({"$ref", "$defs", "$id", "$schema", "allOf"} & set(node))
        variants = schema["oneOf"]
        self.assertEqual(
            {item["properties"]["kind"]["const"] for item in variants},
            {"ready", "needs-input", "expanded", "no-write"},
        )
        ready = next(
            item for item in variants if item["properties"]["kind"]["const"] == "ready"
        )
        self.assertTrue(ready["properties"]["evidence_bundle"]["additionalProperties"])
        self.assertEqual(
            [
                item["properties"]["id"]["const"]
                for item in ready["properties"]["checklist"]["prefixItems"]
            ],
            list(atlas_quality.CHECKLIST_IDS),
        )

        invalid_args = atlas_tool.execute(
            request("source.worker_schema", {"schema": schema})
        )
        self.assert_envelope(invalid_args, ok=False, op="source.worker_schema")
        self.assertEqual(invalid_args["findings"][0]["code"], "ARGUMENTS_INVALID")

    def test_source_worker_schema_preserves_variants_and_fails_closed(self) -> None:
        worker_schema = json.loads(WORKER_SCHEMA_PATH.read_text(encoding="utf-8"))
        proposal_schema = json.loads(PROPOSAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        worker_original = json.loads(json.dumps(worker_schema))
        proposal_original = json.loads(json.dumps(proposal_schema))
        schema = atlas_source.project_worker_transport_schema(
            worker_schema,
            proposal_schema,
        )
        self.assertEqual(worker_schema, worker_original)
        self.assertEqual(proposal_schema, proposal_original)
        extended_worker = json.loads(json.dumps(worker_schema))
        extended_worker["$defs"]["ready"]["properties"]["future"] = {
            "type": "string",
            "minLength": 1,
        }
        extended_projection = atlas_source.project_worker_transport_schema(
            extended_worker,
            proposal_schema,
        )
        extended_ready = next(
            item
            for item in extended_projection["oneOf"]
            if item["properties"]["kind"]["const"] == "ready"
        )
        self.assertEqual(
            extended_ready["properties"]["future"],
            {"type": "string", "minLength": 1},
        )

        if jsonschema is not None:
            validator = jsonschema.Draft202012Validator(schema)
            ready = source_worker_packet(SOURCE_B_URL)
            ready["evidence_bundle"]["evidence_bundle_extension"] = {"attempt": 1}
            no_write = {
                "version": 1,
                "kind": "no-write",
                "identity": ready["identity"],
                "reason": "source text was unavailable",
            }
            needs_input = {
                "version": 1,
                "kind": "needs-input",
                "identity": ready["identity"],
                "reason": "aggregate page requires a choice",
                "choices": ["page-only", "expand", "stop-without-writing"],
            }
            expanded = {
                "version": 1,
                "kind": "expanded",
                "identity": ready["identity"],
                "children": [{"label": "child", "reference": SOURCE_B_URL}],
            }
            for packet in (ready, no_write, needs_input, expanded):
                with self.subTest(kind=packet["kind"]):
                    self.assertEqual(list(validator.iter_errors(packet)), [])
            partial = source_worker_packet(SOURCE_B_URL)
            del partial["evidence_ledger"]
            self.assertTrue(list(validator.iter_errors(partial)))

        malformed = json.loads(json.dumps(worker_schema))
        malformed["$defs"]["checklist"]["prefixItems"].pop()
        residual_ref = json.loads(json.dumps(worker_schema))
        residual_ref["$defs"]["ready"]["properties"]["future"] = {
            "$ref": "https://outside.example/schema.json"
        }
        with self.assertRaises(ValueError):
            atlas_source.project_worker_transport_schema(residual_ref, proposal_schema)
        checklist_drift = json.loads(json.dumps(worker_schema))
        checklist_drift["$defs"]["checklist"]["prefixItems"][0]["allOf"][1][
            "properties"
        ]["id"]["const"] = "unexpected-check"
        with self.assertRaises(ValueError):
            atlas_source.project_worker_transport_schema(
                checklist_drift, proposal_schema
            )
        checklist_refinement_drift = json.loads(json.dumps(worker_schema))
        checklist_refinement_drift["$defs"]["checklist"]["prefixItems"][0]["allOf"][1][
            "description"
        ] = "unexpected refinement"
        with self.assertRaises(ValueError):
            atlas_source.project_worker_transport_schema(
                checklist_refinement_drift, proposal_schema
            )
        with self.assertRaises(ValueError):
            atlas_source.project_worker_transport_schema(malformed, proposal_schema)
        cyclic: dict[str, Any] = {}
        cyclic["cycle"] = cyclic
        with self.assertRaises(ValueError):
            atlas_source.project_worker_transport_schema(cyclic, proposal_schema)
        cyclic_resource = json.loads(json.dumps(worker_schema))
        cyclic_resource["$defs"]["cycle"] = {"$ref": "#/$defs/cycle"}
        cyclic_resource["$defs"]["ready"]["properties"]["future"] = {
            "$ref": "#/$defs/cycle"
        }
        with self.assertRaises(ValueError):
            atlas_source.project_worker_transport_schema(
                cyclic_resource, proposal_schema
            )
        unsupported_ref = json.loads(json.dumps(worker_schema))
        unsupported_ref["$defs"]["ready"]["properties"]["future"] = {
            "$dynamicRef": "#/$defs/ready"
        }
        with self.assertRaises(ValueError):
            atlas_source.project_worker_transport_schema(
                unsupported_ref, proposal_schema
            )

        with patch.object(
            atlas_tool,
            "WORKER_SCHEMA_PATH",
            ROOT / "missing-worker-schema.json",
        ):
            unavailable = atlas_tool.execute(request("source.worker_schema", {}))
        self.assert_envelope(unavailable, ok=False, op="source.worker_schema")
        self.assertEqual(
            unavailable["findings"][0]["code"],
            "WORKER_SCHEMA_INVALID",
        )
        self.assertEqual(unavailable["findings"][0]["path"], "assets")

        with patch.object(
            atlas_tool,
            "PROPOSAL_SCHEMA_PATH",
            ROOT / "tests" / "test_atlas_tool.py",
        ):
            malformed_assets = atlas_tool.execute(request("source.worker_schema", {}))
        self.assert_envelope(malformed_assets, ok=False, op="source.worker_schema")
        self.assertEqual(
            malformed_assets["findings"][0]["code"],
            "WORKER_SCHEMA_INVALID",
        )
        self.assertEqual(malformed_assets["findings"][0]["path"], "assets")

        with patch.object(
            atlas_source,
            "project_worker_transport_schema",
            side_effect=RuntimeError("unexpected defect"),
        ):
            unexpected = atlas_tool.execute(request("source.worker_schema", {}))
        self.assert_envelope(unexpected, ok=False, op="source.worker_schema")
        self.assertEqual(unexpected["disposition"], "internal-error")
        self.assertEqual(
            response_findings(unexpected)[0][0], "FRAMEWORK_INTERNAL_ERROR"
        )

    def test_source_worker_schema_composes_ledger_and_proposal_offline(
        self,
    ) -> None:
        worker_schema = json.loads(WORKER_SCHEMA_PATH.read_text(encoding="utf-8"))
        proposal_schema = json.loads(PROPOSAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        ready = worker_schema["$defs"]["ready"]
        ledger = worker_schema["$defs"]["evidence_ledger"]
        evidence_bundle = worker_schema["$defs"]["evidence_bundle"]

        self.assertEqual(
            ready["properties"]["evidence_bundle"],
            {"$ref": "#/$defs/evidence_bundle"},
        )
        self.assertTrue(evidence_bundle["additionalProperties"])
        self.assertEqual(
            evidence_bundle["required"],
            ["version", "canonical_url", "payload_text"],
        )
        self.assertEqual(evidence_bundle["properties"]["version"], {"const": 1})
        self.assertEqual(
            evidence_bundle["properties"]["canonical_url"],
            {"$ref": "#/$defs/nonempty_text"},
        )
        self.assertEqual(
            evidence_bundle["properties"]["payload_text"],
            {"$ref": "#/$defs/nonempty_text"},
        )
        self.assertEqual(
            evidence_bundle["properties"]["first_seen"], {"type": "string"}
        )
        self.assertEqual(
            evidence_bundle["properties"]["fetched_at"], {"type": "string"}
        )

        self.assertEqual(
            ready["properties"]["evidence_ledger"],
            {"$ref": "#/$defs/evidence_ledger"},
        )
        self.assertEqual(
            ready["properties"]["proposal"],
            {"$ref": "source-summary-proposal.schema.json"},
        )
        self.assertEqual(
            urljoin(worker_schema["$id"], ready["properties"]["proposal"]["$ref"]),
            proposal_schema["$id"],
        )
        self.assertFalse(ledger["additionalProperties"])
        self.assertEqual(ledger["required"], ["version", "evidence", "links"])
        self.assertEqual(ledger["properties"]["version"], {"const": 1})
        self.assertEqual(
            ledger["properties"]["evidence"]["items"],
            {"$ref": "#/$defs/evidence_ledger_entry"},
        )
        self.assertEqual(
            ledger["properties"]["links"]["items"],
            {"$ref": "#/$defs/evidence_ledger_link"},
        )
        for definition_name, required in (
            ("evidence_ledger_entry", ["locator", "ledger_id"]),
            ("evidence_ledger_link", ["url", "locator", "ledger_id"]),
        ):
            definition = worker_schema["$defs"][definition_name]
            self.assertFalse(definition["additionalProperties"])
            self.assertEqual(definition["required"], required)
            self.assertEqual(
                definition["properties"]["locator"],
                {"$ref": "#/$defs/nonempty_text"},
            )
            self.assertEqual(
                definition["properties"]["ledger_id"],
                {"$ref": "#/$defs/ledger_id"},
            )
        self.assertEqual(
            worker_schema["$defs"]["evidence_ledger_link"]["properties"]["url"],
            {"$ref": "#/$defs/absolute_http_url"},
        )
        self.assertEqual(
            worker_schema["$defs"]["ledger_id"]["pattern"],
            "^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$",
        )
        self.assertEqual(
            worker_schema["$defs"]["absolute_http_url"]["pattern"],
            "^https?://\\S+$",
        )

        if jsonschema is not None:
            from referencing import Registry, Resource

            registry = Registry().with_resources(
                [
                    (
                        worker_schema["$id"],
                        Resource.from_contents(worker_schema),
                    ),
                    (
                        proposal_schema["$id"],
                        Resource.from_contents(proposal_schema),
                    ),
                ]
            )
            validator = jsonschema.Draft202012Validator(
                worker_schema, registry=registry
            )
            self.assertEqual(
                list(validator.iter_errors(source_worker_packet(SOURCE_B_URL))),
                [],
            )
            arbitrary_extension = source_worker_packet(SOURCE_B_URL)
            arbitrary_extension["evidence_bundle"]["future_retrieval_metadata"] = {
                "attempt": 1
            }
            self.assertEqual(
                list(validator.iter_errors(arbitrary_extension)),
                [],
            )
            missing_evidence_version = source_worker_packet(SOURCE_B_URL)
            del missing_evidence_version["evidence_bundle"]["version"]
            wrong_evidence_version = source_worker_packet(SOURCE_B_URL)
            wrong_evidence_version["evidence_bundle"]["version"] = 2
            null_evidence_version = source_worker_packet(SOURCE_B_URL)
            null_evidence_version["evidence_bundle"]["version"] = None
            missing_canonical_url = source_worker_packet(SOURCE_B_URL)
            del missing_canonical_url["evidence_bundle"]["canonical_url"]
            missing_payload_text = source_worker_packet(SOURCE_B_URL)
            del missing_payload_text["evidence_bundle"]["payload_text"]
            empty_payload_text = source_worker_packet(SOURCE_B_URL)
            empty_payload_text["evidence_bundle"]["payload_text"] = ""
            for malformed in (
                missing_evidence_version,
                wrong_evidence_version,
                null_evidence_version,
                missing_canonical_url,
                missing_payload_text,
                empty_payload_text,
            ):
                self.assertTrue(list(validator.iter_errors(malformed)))

            malformed_shape = source_worker_packet(SOURCE_B_URL)
            malformed_shape["evidence_ledger"]["evidence"] = {}
            malformed_entry = source_worker_packet(SOURCE_B_URL)
            malformed_entry["evidence_ledger"]["evidence"][0]["locator"] = ""
            malformed_link = source_worker_packet(SOURCE_B_URL)
            malformed_link["evidence_ledger"]["links"][0]["url"] = (
                "mailto:ledger@example.test"
            )
            for malformed in (
                malformed_shape,
                malformed_entry,
                malformed_link,
            ):
                self.assertTrue(list(validator.iter_errors(malformed)))

    def test_source_prepare_rejects_worker_packets_before_connector_reads(
        self,
    ) -> None:
        class NoReadConnector:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.reads: list[str] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def read_text(self, path: str) -> str:
                self.reads.append(path)
                raise AssertionError(f"unexpected read: {path}")

            def consistent_read(self, paths: list[str]) -> dict[str, Any]:
                self.reads.extend(paths)
                raise AssertionError(f"unexpected snapshot: {paths}")

        with temporary_profile() as fixture:
            connector = NoReadConnector(fixture.connector())
            identity = {
                "canonical_url": SOURCE_B_URL,
                "source_id": source_id(SOURCE_B_URL),
            }
            missing_bundle_version = source_worker_packet(SOURCE_B_URL)
            del missing_bundle_version["evidence_bundle"]["version"]
            invalid_ledger_id = source_worker_packet(SOURCE_B_URL)
            invalid_ledger_id["evidence_ledger"]["evidence"][0]["ledger_id"] = "bad id"
            empty_author = source_worker_packet(SOURCE_B_URL)
            empty_author["proposal"]["metadata"]["author"] = ""
            empty_links = source_worker_packet(SOURCE_B_URL)
            empty_links["proposal"]["links"] = []
            unknown_proposal_field = source_worker_packet(SOURCE_B_URL)
            unknown_proposal_field["proposal"]["unknown"] = True
            cases = (
                ({}, "WORKER_KIND_INVALID"),
                (
                    {
                        "version": 1,
                        "kind": "needs-input",
                        "identity": identity,
                        "reason": "aggregate page requires a choice",
                        "choices": [
                            "page-only",
                            "expand",
                            "stop-without-writing",
                        ],
                    },
                    "WORKER_PACKET_NOT_FINAL",
                ),
                (missing_bundle_version, "WORKER_EVIDENCE_BUNDLE_INVALID"),
                (invalid_ledger_id, "PROPOSAL_LEDGER_INVALID"),
                (empty_author, "PROPOSAL_TYPE_INVALID"),
                (empty_links, "PROPOSAL_LINKS_INVALID"),
                (unknown_proposal_field, "PROPOSAL_UNKNOWN_KEY"),
            )

            for worker, expected_code in cases:
                with self.subTest(code=expected_code):
                    response = invoke(
                        fixture,
                        "source.prepare",
                        connector=connector,
                        identity={
                            "canonical_url": SOURCE_B_URL,
                            "checked_on": "2026-08-17",
                        },
                        mode="routine",
                        worker=worker,
                    )
                    self.assert_envelope(response, ok=True, op="source.prepare")
                    self.assertEqual(response["result"]["state"], "rejected")
                    self.assertEqual(
                        response["result"]["findings"][0]["code"], expected_code
                    )
                    self.assertEqual(connector.reads, [])

    def test_source_prepare_preserves_ledger_findings_for_one_correction(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            malformed = source_worker_packet(SOURCE_C_URL)
            malformed["evidence_ledger"]["evidence"] = {}
            malformed_original = json.loads(json.dumps(malformed))
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            raw_missing_version = source_worker_packet(SOURCE_C_URL)
            del raw_missing_version["evidence_bundle"]["version"]
            raw_missing_version_original = json.loads(json.dumps(raw_missing_version))
            missing_version = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=raw_missing_version,
            )
            self.assert_envelope(missing_version, ok=True, op="source.prepare")
            self.assertEqual(
                missing_version["result"],
                {
                    "state": "rejected",
                    "findings": [
                        {
                            "code": "WORKER_EVIDENCE_BUNDLE_INVALID",
                            "path": "worker.evidence_bundle.version",
                            "detail": "expected version 1",
                        }
                    ],
                },
            )
            self.assertNotIn("transaction", missing_version["result"])
            self.assertEqual(raw_missing_version, raw_missing_version_original)

            revision = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=malformed,
            )
            self.assert_envelope(revision, ok=True, op="source.prepare")
            self.assertEqual(revision["result"]["state"], "rejected")
            self.assertEqual(
                [
                    (finding["code"], finding["path"], finding["detail"])
                    for finding in revision["result"]["findings"]
                ],
                [("PROPOSAL_LEDGER_INVALID", "ledger.evidence", "")],
            )
            self.assertNotIn("transaction", revision["result"])
            self.assertEqual(malformed, malformed_original)

            corrected = source_worker_packet(SOURCE_C_URL)
            del corrected["evidence_bundle"]["fetched_at"]
            corrected_original = json.loads(json.dumps(corrected))
            prepared = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=corrected,
            )
            self.assert_envelope(prepared, ok=True, op="source.prepare")
            self.assertEqual(prepared["result"]["state"], "prepared")
            self.assertEqual(
                prepared["result"]["transaction"]["event_record"]["event"][
                    "first_seen"
                ],
                "2026-07-31",
            )
            self.assertEqual(corrected, corrected_original)
            invalid_identity = source_worker_packet(SOURCE_C_URL)
            invalid_identity["identity"]["canonical_url"] = None
            for invalid_worker in (
                {"evidence_bundle": {"version": 1}},
                "corrected envelope",
                {"version": 1, "kind": "ready"},
                invalid_identity,
            ):
                invalid_original = json.loads(json.dumps(invalid_worker))
                rejected = invoke(
                    fixture,
                    "source.prepare",
                    identity={
                        "canonical_url": SOURCE_C_URL,
                        "checked_on": "2026-07-31",
                    },
                    mode="routine",
                    worker=invalid_worker,
                )
                self.assert_envelope(rejected, ok=True, op="source.prepare")
                self.assertEqual(rejected["result"]["state"], "rejected")
                self.assertNotIn("transaction", rejected["result"])
                self.assertEqual(invalid_worker, invalid_original)

            arbitrary_extension = source_worker_packet(SOURCE_C_URL)
            arbitrary_extension["evidence_bundle"]["future_retrieval_metadata"] = {
                "attempt": 1
            }
            arbitrary_extension_original = json.loads(json.dumps(arbitrary_extension))
            extension_prepared = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=arbitrary_extension,
            )
            self.assert_envelope(extension_prepared, ok=True, op="source.prepare")
            self.assertEqual(extension_prepared["result"]["state"], "prepared")
            self.assertEqual(arbitrary_extension, arbitrary_extension_original)

            no_write = {
                "version": 1,
                "kind": "no-write",
                "identity": {
                    "canonical_url": SOURCE_C_URL,
                    "source_id": source_id(SOURCE_C_URL),
                },
                "reason": "worker did not return a corrected ready packet",
            }
            no_write_original = json.loads(json.dumps(no_write))
            exhausted = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=no_write,
            )
            self.assert_envelope(exhausted, ok=True, op="source.prepare")
            self.assertEqual(exhausted["result"]["state"], "terminal")
            self.assertEqual(exhausted["result"]["outcome"], "no-write")
            self.assertNotIn("transaction", exhausted["result"])
            self.assertEqual(no_write, no_write_original)
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after["result"], before["result"])

    def test_source_prepare_supplies_missing_evidence_date_locally(self) -> None:
        with temporary_profile() as fixture:
            checked_on = "2026-07-31"
            packet = source_worker_packet(SOURCE_B_URL)
            del packet["evidence_bundle"]["fetched_at"]
            original_packet = json.loads(json.dumps(packet))
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            prepared = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_B_URL, "checked_on": checked_on},
                mode="routine",
                worker=packet,
            )
            self.assert_envelope(prepared, ok=True, op="source.prepare")
            result = prepared["result"]
            self.assertEqual(result["state"], "prepared")
            expected_artifact = (
                "vault://atlas/summaries/sources/artifacts/2026/2026-07/"
                f"{checked_on}--{source_id(SOURCE_B_URL)}--synthetic-batch-source.md"
            )
            event = result["transaction"]["event_record"]["event"]
            self.assertEqual(event["first_seen"], checked_on)
            self.assertEqual(
                event["artifact"], expected_artifact.removeprefix("vault://atlas/")
            )
            self.assertEqual(
                [target["path"] for target in result["transaction"]["targets"]],
                [expected_artifact, MANIFEST_URI],
            )
            self.assertEqual(packet, original_packet)
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after["result"], before["result"])

    def test_source_prepare_rejects_present_null_evidence_date(self) -> None:
        with temporary_profile() as fixture:
            packet = source_worker_packet(SOURCE_B_URL)
            packet["evidence_bundle"]["fetched_at"] = None
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            rejected = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_B_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=packet,
            )
            self.assert_envelope(rejected, ok=True, op="source.prepare")
            result = rejected["result"]
            self.assertEqual(result["state"], "rejected")
            self.assertNotIn("transaction", result)
            self.assertIn(
                "WORKER_EVIDENCE_BUNDLE_INVALID",
                [finding["code"] for finding in result["findings"]],
            )
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after["result"], before["result"])

    def test_source_prepare_returns_only_current_transaction_inputs(self) -> None:
        with temporary_profile() as fixture:
            packet = source_worker_packet(SOURCE_B_URL)
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            prepared = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_B_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=packet,
            )
            self.assert_envelope(prepared, ok=True, op="source.prepare")
            result = prepared["result"]
            self.assertEqual(result["state"], "prepared")
            self.assertEqual(result["outcome"], "created")
            self.assertIs(result["route_required"], True)
            self.assertEqual(
                [target["path"] for target in result["transaction"]["targets"]],
                [
                    "vault://atlas/summaries/sources/artifacts/2026/2026-07/"
                    f"2026-07-31--{source_id(SOURCE_B_URL)}--synthetic-batch-source.md",
                    MANIFEST_URI,
                ],
            )
            self.assertEqual(
                result["transaction"]["event_record"]["source_id"],
                source_id(SOURCE_B_URL),
            )
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after["result"], before["result"])

            fixture.put(
                TOPICS_URI,
                topics_text().replace("Synthetic topic", "Retitled synthetic topic"),
            )
            sibling_changed = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_B_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=packet,
            )
            self.assert_envelope(sibling_changed, ok=True, op="source.prepare")
            self.assertEqual(sibling_changed["result"]["state"], "prepared")
            self.assertNotIn(
                TOPICS_URI,
                [
                    target["path"]
                    for target in sibling_changed["result"]["transaction"]["targets"]
                ],
            )

            malformed = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker={},
            )
            self.assert_envelope(malformed, ok=True, op="source.prepare")
            self.assertEqual(malformed["result"]["state"], "rejected")

            invalid_structure_packet = json.loads(
                json.dumps(source_worker_packet(SOURCE_C_URL))
            )
            invalid_structure_packet["proposal"]["metadata"]["title"] = ""
            invalid_structure = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=invalid_structure_packet,
            )
            self.assert_envelope(invalid_structure, ok=True, op="source.prepare")
            self.assertEqual(invalid_structure["result"]["state"], "rejected")
            self.assertIn(
                "PROPOSAL_TYPE_INVALID",
                [
                    finding["code"]
                    for finding in invalid_structure["result"]["findings"]
                ],
            )

            rejected_checklist_packet = json.loads(
                json.dumps(source_worker_packet(SOURCE_C_URL))
            )
            rejected_checklist_packet["checklist"][0]["status"] = "unknown"
            rejected_checklist = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=rejected_checklist_packet,
            )
            self.assert_envelope(rejected_checklist, ok=True, op="source.prepare")
            self.assertEqual(rejected_checklist["result"]["state"], "rejected")
            self.assertIn(
                "CHECKLIST_STATUS_INVALID",
                [
                    finding["code"]
                    for finding in rejected_checklist["result"]["findings"]
                ],
            )

            checklist_retry_packet = json.loads(
                json.dumps(source_worker_packet(SOURCE_C_URL))
            )
            checklist_retry_packet["checklist"][0]["status"] = "fail"
            before_checklist_retry = invoke(
                fixture, "vault.digest_tree", path="vault://atlas/"
            )
            checklist_retry = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker=checklist_retry_packet,
            )
            self.assert_envelope(checklist_retry, ok=True, op="source.prepare")
            self.assertEqual(checklist_retry["result"]["state"], "needs-revision")
            self.assertNotIn("transaction", checklist_retry["result"])
            self.assertIn(
                "CHECKLIST_ITEM_FAILED",
                [finding["code"] for finding in checklist_retry["result"]["findings"]],
            )
            after_checklist_retry = invoke(
                fixture, "vault.digest_tree", path="vault://atlas/"
            )
            self.assertEqual(
                after_checklist_retry["result"], before_checklist_retry["result"]
            )

            no_write = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_C_URL, "checked_on": "2026-07-31"},
                mode="routine",
                worker={
                    "version": 1,
                    "kind": "no-write",
                    "identity": {
                        "canonical_url": SOURCE_C_URL,
                        "source_id": source_id(SOURCE_C_URL),
                    },
                    "reason": "source text is unavailable",
                },
            )
            self.assert_envelope(no_write, ok=True, op="source.prepare")
            self.assertEqual(no_write["result"]["state"], "terminal")
            self.assertEqual(no_write["result"]["outcome"], "no-write")

    def test_source_promotion_freezes_pair_and_returns_generic_transaction(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            worker = source_worker_packet(SOURCE_B_URL)
            source_prepared = invoke(
                fixture,
                "source.prepare",
                identity={
                    "canonical_url": SOURCE_B_URL,
                    "checked_on": "2026-07-31",
                },
                mode="routine",
                worker=worker,
            )
            self.assert_envelope(source_prepared, ok=True, op="source.prepare")
            source_result = source_prepared["result"]
            self.assertEqual(source_result["state"], "prepared")
            target = source_result["transaction"]["targets"][0]
            staged_uri = "vault://atlas/staging/source-b.md"
            evidence_uri = "vault://atlas/staging/source-b.evidence.json"
            evidence_text = (
                json.dumps(
                    worker,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
            fixture.put(staged_uri, target["text"])
            fixture.put(evidence_uri, evidence_text)

            class SnapshotConnector:
                def __init__(self, inner: Any) -> None:
                    self._inner = inner
                    self.calls: list[tuple[str, ...]] = []

                def __getattr__(self, name: str) -> Any:
                    return getattr(self._inner, name)

                def consistent_read(
                    self,
                    paths: list[str],
                ) -> dict[str, dict[str, Any]]:
                    self.calls.append(tuple(paths))
                    return self._inner.consistent_read(paths)

            class DriftingSnapshotConnector(SnapshotConnector):
                def consistent_read(
                    self,
                    paths: list[str],
                ) -> dict[str, dict[str, Any]]:
                    snapshot = super().consistent_read(paths)
                    if len(self.calls) == 1:
                        fixture.put(staged_uri, target["text"] + "\n")
                    return snapshot

            drifted = invoke(
                fixture,
                "source.prepare",
                connector=DriftingSnapshotConnector(fixture.connector()),
                mode="promote",
                artifact_uri=staged_uri,
                evidence_uri=evidence_uri,
            )
            self.assert_envelope(
                drifted,
                ok=True,
                op="source.prepare",
            )
            self.assertEqual(drifted["result"]["state"], "rejected")
            self.assertEqual(
                drifted["result"]["findings"][0]["code"],
                "SOURCE_PROMOTION_STALE",
            )
            fixture.put(staged_uri, target["text"])

            connector = SnapshotConnector(fixture.connector())
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            promoted = invoke(
                fixture,
                "source.prepare",
                connector=connector,
                mode="promote",
                artifact_uri=staged_uri,
                evidence_uri=evidence_uri,
            )
            self.assert_envelope(
                promoted,
                ok=True,
                op="source.prepare",
            )
            result = promoted["result"]
            self.assertEqual(result["state"], "prepared")
            self.assertEqual(
                result["identity"],
                {
                    "canonical_url": SOURCE_B_URL,
                    "source_id": source_id(SOURCE_B_URL),
                },
            )
            self.assertEqual(
                connector.calls,
                [
                    (staged_uri, evidence_uri, MANIFEST_URI),
                    (
                        staged_uri,
                        evidence_uri,
                        MANIFEST_URI,
                        TOPICS_URI,
                        RELATIONS_URI,
                        target["path"],
                    ),
                ],
            )
            self.assertEqual(
                result["promotion"],
                {
                    "artifact_uri": staged_uri,
                    "artifact_revision": (
                        "sha256:" + hashlib.sha256(target["text"].encode()).hexdigest()
                    ),
                    "evidence_uri": evidence_uri,
                    "evidence_revision": (
                        "sha256:" + hashlib.sha256(evidence_text.encode()).hexdigest()
                    ),
                },
            )
            self.assertEqual(
                result["transaction"]["event_record"]["promotion"],
                result["promotion"],
            )
            self.assertEqual(
                [item["path"] for item in result["transaction"]["targets"]],
                [target["path"], MANIFEST_URI],
            )
            after_prepare = invoke(
                fixture,
                "vault.digest_tree",
                path="vault://atlas/",
            )
            self.assertEqual(after_prepare["result"], before["result"])

            tampered_transaction = json.loads(json.dumps(result["transaction"]))
            tampered_transaction["targets"][0]["text"] += "\n"
            before_tampered = invoke(
                fixture,
                "vault.digest_tree",
                path="vault://atlas/",
            )
            tampered = invoke(
                fixture,
                "transaction.execute",
                **tampered_transaction,
            )
            self.assert_envelope(tampered, ok=False, op="transaction.execute")
            self.assertEqual(
                response_findings(tampered)[0][0],
                "SOURCE_PROMOTION_PROJECTION_MISMATCH",
            )
            after_tampered = invoke(
                fixture,
                "vault.digest_tree",
                path="vault://atlas/",
            )
            self.assertEqual(after_tampered["result"], before_tampered["result"])

            fixture.put(staged_uri, target["text"] + "\n")
            before_stale = invoke(
                fixture,
                "vault.digest_tree",
                path="vault://atlas/",
            )
            stale = invoke(
                fixture,
                "transaction.execute",
                **result["transaction"],
            )
            self.assert_envelope(stale, ok=False, op="transaction.execute")
            self.assertEqual(
                response_findings(stale)[0][0],
                "SOURCE_PROMOTION_STALE",
            )
            after_stale = invoke(
                fixture,
                "vault.digest_tree",
                path="vault://atlas/",
            )
            self.assertEqual(after_stale["result"], before_stale["result"])
            fixture.put(staged_uri, target["text"])

            applied = invoke(
                fixture,
                "transaction.execute",
                **result["transaction"],
            )
            self.assert_envelope(applied, ok=True, op="transaction.execute")
            self.assertEqual(applied["result"]["receipt"]["status"], "applied")
            self.assertEqual(self.read_text(fixture, staged_uri), target["text"])
            self.assertEqual(self.read_text(fixture, evidence_uri), evidence_text)

    def test_source_prepare_prioritizes_current_state_over_failed_checklist(
        self,
    ) -> None:
        cases = (
            (
                "archived",
                SOURCE_C_URL,
                "routine",
                manifest_text([manifest_row(SOURCE_C_URL, 3, status="archived")]),
                "terminal",
                "archived",
                None,
            ),
            (
                "active_not_due",
                SOURCE_A_URL,
                "routine",
                None,
                "terminal",
                "active-not-due",
                None,
            ),
            (
                "resummarize_absent",
                SOURCE_C_URL,
                "resummarize",
                None,
                "rejected",
                None,
                "SOURCE_NOT_FOUND",
            ),
        )
        for (
            path,
            canonical_url,
            mode,
            manifest,
            expected_state,
            expected_outcome,
            expected_finding,
        ) in cases:
            with self.subTest(path=path), temporary_profile() as fixture:
                if manifest is not None:
                    fixture.put(MANIFEST_URI, manifest)
                failed_packet = source_worker_packet(canonical_url)
                failed_packet["checklist"][0]["status"] = "fail"
                before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")

                response = invoke(
                    fixture,
                    "source.prepare",
                    identity={
                        "canonical_url": canonical_url,
                        "checked_on": "2026-07-31",
                    },
                    mode=mode,
                    worker=failed_packet,
                )

                self.assert_envelope(response, ok=True, op="source.prepare")
                result = response["result"]
                self.assertEqual(result["state"], expected_state)
                self.assertNotIn("transaction", result)
                if expected_outcome is not None:
                    self.assertEqual(result["outcome"], expected_outcome)
                else:
                    self.assertIn(
                        expected_finding,
                        [finding["code"] for finding in result["findings"]],
                    )
                after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
                self.assertEqual(after["result"], before["result"])

    def test_source_prepare_defers_calendar_date_validation_until_eligible_state(
        self,
    ) -> None:
        cases = (
            (
                "archived",
                SOURCE_C_URL,
                manifest_text([manifest_row(SOURCE_C_URL, 3, status="archived")]),
                "terminal",
                "archived",
                None,
            ),
            (
                "active_not_due",
                SOURCE_A_URL,
                None,
                "terminal",
                "active-not-due",
                None,
            ),
            (
                "eligible_new",
                SOURCE_C_URL,
                None,
                "rejected",
                None,
                "EVENT_DATE_INVALID",
            ),
        )
        for (
            path,
            canonical_url,
            manifest,
            expected_state,
            expected_outcome,
            expected_finding,
        ) in cases:
            with self.subTest(path=path), temporary_profile() as fixture:
                if manifest is not None:
                    fixture.put(MANIFEST_URI, manifest)
                packet = source_worker_packet(canonical_url)
                packet["refresh_after"] = "2027-02-30"
                before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")

                response = invoke(
                    fixture,
                    "source.prepare",
                    identity={
                        "canonical_url": canonical_url,
                        "checked_on": "2026-07-31",
                    },
                    mode="routine",
                    worker=packet,
                )

                self.assert_envelope(response, ok=True, op="source.prepare")
                result = response["result"]
                self.assertEqual(result["state"], expected_state)
                self.assertNotIn("transaction", result)
                if expected_outcome is not None:
                    self.assertEqual(result["outcome"], expected_outcome)
                else:
                    self.assertIn(
                        expected_finding,
                        [finding["code"] for finding in result["findings"]],
                    )
                after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
                self.assertEqual(after["result"], before["result"])

    def test_source_prepare_prioritizes_current_state_over_unbound_proposal(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            packet = source_worker_packet(SOURCE_A_URL)
            packet["proposal"]["claims"][0]["evidence"][0]["locator"] = "unbound"

            response = invoke(
                fixture,
                "source.prepare",
                identity={
                    "canonical_url": SOURCE_A_URL,
                    "checked_on": "2026-07-31",
                },
                mode="routine",
                worker=packet,
            )

            self.assert_envelope(response, ok=True, op="source.prepare")
            self.assertEqual(response["result"]["state"], "terminal")
            self.assertEqual(response["result"]["outcome"], "active-not-due")
            self.assertNotIn("transaction", response["result"])

    def test_source_prepare_checks_failed_checklist_before_existing_same_content(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            packet = source_worker_packet(SOURCE_A_URL)
            packet["evidence_bundle"]["payload_text"] = "synthetic payload 1\n"

            before_all_pass = invoke(
                fixture, "vault.digest_tree", path="vault://atlas/"
            )
            all_pass = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_A_URL, "checked_on": "2027-07-28"},
                mode="routine",
                worker=packet,
            )
            self.assert_envelope(all_pass, ok=True, op="source.prepare")
            self.assertEqual(all_pass["result"]["state"], "prepared")
            self.assertEqual(all_pass["result"]["outcome"], "checked-unchanged")
            self.assertIs(all_pass["result"]["route_required"], False)
            self.assertIn("transaction", all_pass["result"])
            self.assertEqual(
                [
                    target["path"]
                    for target in all_pass["result"]["transaction"]["targets"]
                ],
                [MANIFEST_URI],
            )
            self.assertEqual(
                all_pass["result"]["transaction"]["event_record"]["event"][
                    "checked_on"
                ],
                "2027-07-28",
            )
            after_all_pass = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after_all_pass["result"], before_all_pass["result"])

            failed_packet = json.loads(json.dumps(packet))
            failed_packet["checklist"][0]["status"] = "fail"
            before_failed = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            failed = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_A_URL, "checked_on": "2027-07-28"},
                mode="routine",
                worker=failed_packet,
            )
            self.assert_envelope(failed, ok=True, op="source.prepare")
            self.assertEqual(failed["result"]["state"], "needs-revision")
            self.assertNotIn("transaction", failed["result"])
            self.assertIn(
                "CHECKLIST_ITEM_FAILED",
                [finding["code"] for finding in failed["result"]["findings"]],
            )
            after_failed = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after_failed["result"], before_failed["result"])

            invalid_packet = json.loads(json.dumps(packet))
            invalid_packet["checklist"][0]["status"] = "invalid"
            invalid = invoke(
                fixture,
                "source.prepare",
                identity={"canonical_url": SOURCE_A_URL, "checked_on": "2027-07-28"},
                mode="routine",
                worker=invalid_packet,
            )
            self.assert_envelope(invalid, ok=True, op="source.prepare")
            self.assertEqual(invalid["result"]["state"], "rejected")
            self.assertIn(
                "CHECKLIST_STATUS_INVALID",
                [finding["code"] for finding in invalid["result"]["findings"]],
            )

    def test_source_lookup_reads_one_manifest_on_a_read_only_connector(self) -> None:
        with temporary_profile() as fixture:
            connector = RecordingReadOnlyConnector(fixture.connector())
            capabilities = atlas_tool.capabilities(connector=connector)
            self.assert_envelope(capabilities, ok=True, op="capabilities")
            operations = [
                item["operation"] for item in capabilities["result"]["operations"]
            ]
            self.assertIn("source.lookup", operations)
            self.assertNotIn("source.extract_reader_result", operations)

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

    def test_padded_escaped_tables_match_validation_lookup_and_snapshot(self) -> None:
        with temporary_profile() as fixture:
            topic = [
                TOPIC_ID,
                "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
                "test",
                "test-subdomain",
                "Synthetic topic",
                r"Synthetic \| alias",
                "",
                "test",
                "",
                "current",
                "0",
                "",
                "",
                "",
                "0",
                "same-as-topic-creation",
            ]
            fixture.put(
                MANIFEST_URI,
                padded_table(MANIFEST_HEADER, [manifest_row(SOURCE_A_URL, 1)]),
            )
            fixture.put(TOPICS_URI, padded_table(TOPICS_HEADER, [topic]))
            fixture.put(RELATIONS_URI, padded_table(RELATIONS_HEADER, []))

            validated = invoke(fixture, "state.validate")
            self.assert_envelope(validated, ok=True, op="state.validate")

            lookup = invoke(fixture, "source.lookup", url=SOURCE_A_URL)
            self.assert_envelope(lookup, ok=True, op="source.lookup")
            self.assertEqual(
                lookup["result"]["row"]["source_id"], source_id(SOURCE_A_URL)
            )

            snapshot = invoke(fixture, "source.snapshot_active")
            self.assert_envelope(snapshot, ok=True, op="source.snapshot_active")
            self.assertEqual(
                snapshot["result"]["rows"][0]["artifact_uri"],
                artifact_uri(SOURCE_A_URL),
            )
            self.assertEqual(
                atlas_tool._rows(
                    padded_table(TOPICS_HEADER, [topic]),
                    TOPICS_HEADER,
                    TOPICS_URI,
                )[0][0]["Aliases"],
                r"Synthetic \| alias",
            )
            self.assertEqual(
                atlas_tool._rows(
                    padded_table(RELATIONS_HEADER, []),
                    RELATIONS_HEADER,
                    RELATIONS_URI,
                ),
                [],
            )

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
                {"version": 1, "op": "vault.read", "args": {}}
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
            advertised = atlas_tool.capabilities(connector=fixture.connector())[
                "result"
            ]["operations"]
            self.assertEqual(
                [item["operation"] for item in advertised],
                list(LIFECYCLE_OPERATIONS),
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

    def test_source_prepare_route_generated_family_command_is_read_only(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.prepare_route_args(fixture)
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "atlas_tool.py"),
                    "source",
                    "prepare-route",
                    "--input",
                    "-",
                ],
                input=json.dumps(args).encode("utf-8"),
                check=False,
                capture_output=True,
                env={**os.environ, "ATLAS_VAULT_PROFILE": str(fixture.profile)},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stderr, b"")
            response = json.loads(completed.stdout)
            self.assert_envelope(response, ok=True, op="source.prepare_route")
            self.assertEqual(response["result"]["state"], "prepared")
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after["result"], before["result"])

    def test_source_prepare_route_executes_selected_decision_and_replays_unchanged(
        self,
    ) -> None:
        class SnapshotRecorder:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.calls: list[tuple[str, ...]] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def consistent_read(self, paths: list[str]) -> dict[str, Any]:
                self.calls.append(tuple(paths))
                return self._inner.consistent_read(paths)

        decision = {
            "outcome": "routed",
            "edges": [
                {
                    "topic_id": TOPIC_ID,
                    "relation": "direct",
                    "impact": "high",
                    "confidence": "high",
                    "reason": (
                        "Verifier: synthetic — selected route "
                        "[relation=direct; impact=high]"
                    ),
                }
            ],
        }
        with temporary_profile() as fixture:
            before_digest = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            manifest_before, findings = atlas_state.lookup_manifest_row(
                self.read_text(fixture, MANIFEST_URI), SOURCE_A_URL
            )
            self.assertEqual(findings, [])
            self.assertIsNotNone(manifest_before)
            assert manifest_before is not None
            artifact_before = atlas_source.parse_artifact(
                self.read_text(fixture, artifact_uri(SOURCE_A_URL))
            ).values

            recorder = SnapshotRecorder(fixture.connector())
            prepared = invoke(
                fixture,
                "source.prepare_route",
                connector=recorder,
                **self.prepare_route_args(fixture, decision=decision),
            )
            self.assertEqual(
                recorder.calls,
                [(MANIFEST_URI, TOPICS_URI, RELATIONS_URI, artifact_uri(SOURCE_A_URL))],
            )

            self.assert_envelope(prepared, ok=True, op="source.prepare_route")
            self.assertEqual(set(prepared["result"]), {"state", "transaction"})
            self.assertEqual(prepared["result"]["state"], "prepared")
            transaction = prepared["result"]["transaction"]
            self.assertEqual(
                [target["path"] for target in transaction["targets"]],
                [artifact_uri(SOURCE_A_URL), RELATIONS_URI, TOPICS_URI, MANIFEST_URI],
            )
            after_prepare = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after_prepare["result"], before_digest["result"])

            executed = invoke(fixture, "transaction.execute", **transaction)

            self.assert_envelope(executed, ok=True, op="transaction.execute")
            self.assertEqual(executed["result"]["receipt"]["status"], "applied")
            manifest_after, findings = atlas_state.lookup_manifest_row(
                self.read_text(fixture, MANIFEST_URI), SOURCE_A_URL
            )
            self.assertEqual(findings, [])
            self.assertIsNotNone(manifest_after)
            assert manifest_after is not None
            manifest_preserved = (
                "First seen",
                "Last checked",
                "Last summarized",
                "Content hash",
                "Refresh after",
            )
            self.assertEqual(
                {field: manifest_after[field] for field in manifest_preserved},
                {field: manifest_before[field] for field in manifest_preserved},
            )
            self.assertEqual(manifest_after["Route status"], "routed")
            artifact_after = atlas_source.parse_artifact(
                self.read_text(fixture, artifact_uri(SOURCE_A_URL))
            ).values
            artifact_preserved = (
                "first_seen",
                "last_checked",
                "last_summarized",
                "refresh_after",
                "content_hash",
            )
            self.assertEqual(
                {field: artifact_after[field] for field in artifact_preserved},
                {field: artifact_before[field] for field in artifact_preserved},
            )
            self.assertEqual(
                atlas_source.scalar(artifact_after, "routing_status"), "routed"
            )
            self.assertEqual(
                atlas_source.scalar(artifact_after, "routed_at"), "2026-08-17"
            )
            relation = atlas_tool._rows(
                self.read_text(fixture, RELATIONS_URI),
                atlas_state.RELATIONS_HEADER,
                RELATIONS_URI,
            )[0][0]
            self.assertEqual(relation["Created"], "2026-08-17")
            self.assertEqual(relation["Notes"], decision["edges"][0]["reason"])
            self.assert_envelope(
                invoke(fixture, "state.validate"), ok=True, op="state.validate"
            )

            replay = invoke(
                fixture,
                "source.prepare_route",
                **self.prepare_route_args(fixture, decision=decision),
            )
            self.assert_envelope(replay, ok=True, op="source.prepare_route")
            self.assertEqual(
                replay["result"],
                {
                    "state": "terminal",
                    "outcome": "unchanged",
                    "reason": "route preparation has no changed targets",
                },
            )

    def test_source_prepare_route_supports_no_topic_match(self) -> None:
        with temporary_profile() as fixture:
            prepared = invoke(
                fixture,
                "source.prepare_route",
                **self.prepare_route_args(fixture),
            )
            self.assert_envelope(prepared, ok=True, op="source.prepare_route")
            self.assertEqual(prepared["result"]["state"], "prepared")
            self.assertEqual(
                [
                    target["path"]
                    for target in prepared["result"]["transaction"]["targets"]
                ],
                [artifact_uri(SOURCE_A_URL), MANIFEST_URI],
            )

            executed = invoke(
                fixture,
                "transaction.execute",
                **prepared["result"]["transaction"],
            )

            self.assert_envelope(executed, ok=True, op="transaction.execute")
            row, findings = atlas_state.lookup_manifest_row(
                self.read_text(fixture, MANIFEST_URI), SOURCE_A_URL
            )
            self.assertEqual(findings, [])
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["Route status"], "no-topic-match")
            self.assertEqual(self.read_text(fixture, RELATIONS_URI), relations_text())

    def test_source_prepare_route_rejects_stale_invalid_and_archived_inputs(
        self,
    ) -> None:
        class SnapshotRecordingConnector:
            def __init__(self, inner: Any) -> None:
                self._inner = inner
                self.snapshots: list[tuple[str, ...]] = []

            def __getattr__(self, name: str) -> Any:
                return getattr(self._inner, name)

            def consistent_read(self, paths: list[str]) -> dict[str, Any]:
                self.snapshots.append(tuple(paths))
                return self._inner.consistent_read(paths)

        with temporary_profile() as fixture:
            stale_args = self.prepare_route_args(fixture)
            stale_args["expected_revisions"]["topics"] = "sha256:" + "0" * 64
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            stale = invoke(fixture, "source.prepare_route", **stale_args)
            self.assert_envelope(stale, ok=False, op="source.prepare_route")
            self.assertEqual(response_findings(stale)[0][0], "REVISION_STALE")
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after["result"], before["result"])

        with temporary_profile() as fixture:
            decision = {
                "outcome": "routed",
                "edges": [
                    {
                        "topic_id": TOPIC_ID,
                        "relation": "direct",
                        "impact": "high",
                        "confidence": "high",
                        "reason": (
                            "Verifier: synthetic — invalid sibling "
                            "[relation=supporting; impact=high]"
                        ),
                    }
                ],
            }
            args = self.prepare_route_args(fixture, decision=decision)
            connector = SnapshotRecordingConnector(fixture.connector())
            invalid = invoke(
                fixture,
                "source.prepare_route",
                connector=connector,
                **args,
            )
            self.assert_envelope(invalid, ok=False, op="source.prepare_route")
            self.assertEqual(response_findings(invalid)[0][0], "REQUEST_INVALID")
            self.assertEqual(connector.snapshots, [])

            invalid_topic_args = self.prepare_route_args(
                fixture,
                decision={
                    "outcome": "routed",
                    "edges": [
                        {
                            "topic_id": "bad id",
                            "relation": "direct",
                            "impact": "high",
                            "confidence": "high",
                            "reason": (
                                "Verifier: synthetic — invalid topic "
                                "[relation=direct; impact=high]"
                            ),
                        }
                    ],
                },
            )
            invalid_topic = invoke(
                fixture,
                "source.prepare_route",
                connector=connector,
                **invalid_topic_args,
            )
            self.assert_envelope(invalid_topic, ok=False, op="source.prepare_route")
            self.assertEqual(
                response_findings(invalid_topic)[0][:2],
                ("REQUEST_INVALID", "args.decision.edges[0].topic_id"),
            )
            self.assertEqual(connector.snapshots, [])

        with temporary_profile() as fixture:
            fixture.put(
                MANIFEST_URI,
                manifest_text([manifest_row(SOURCE_A_URL, 1, status="archived")]),
            )
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            archived = invoke(
                fixture,
                "source.prepare_route",
                **self.prepare_route_args(fixture),
            )
            self.assert_envelope(archived, ok=True, op="source.prepare_route")
            self.assertEqual(archived["result"]["state"], "rejected")
            self.assertIn(
                "EVENT_SOURCE_ARCHIVED",
                [finding["code"] for finding in archived["result"]["findings"]],
            )
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after["result"], before["result"])

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

    def test_route_empty_complete_decision_rejects_current_pending_projection(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_dirty_topic(fixture)
            args = self.transaction_args(fixture)
            self.assertEqual(
                [target["path"] for target in args["targets"]],
                [artifact_uri(SOURCE_A_URL), RELATIONS_URI, TOPICS_URI, MANIFEST_URI],
            )

            executed = invoke(fixture, "transaction.execute", **args)
            self.assert_envelope(executed, ok=True, op="transaction.execute")
            self.assertEqual(executed["result"]["receipt"]["status"], "applied")

            relation = atlas_tool._rows(
                self.read_text(fixture, RELATIONS_URI),
                atlas_state.RELATIONS_HEADER,
                RELATIONS_URI,
            )[0][0]
            topic = atlas_tool._rows(
                self.read_text(fixture, TOPICS_URI),
                atlas_state.TOPICS_HEADER,
                TOPICS_URI,
            )[0][0]
            manifest_row_after, findings = atlas_state.lookup_manifest_row(
                self.read_text(fixture, MANIFEST_URI), SOURCE_A_URL
            )
            self.assertEqual(findings, [])
            self.assertIsNotNone(manifest_row_after)
            assert manifest_row_after is not None
            self.assertEqual(relation["Status"], "rejected")
            self.assertEqual(topic["Freshness state"], "current")
            self.assertEqual(topic["Dirty count"], "0")
            self.assertEqual(topic["Pending edge IDs"], "")
            self.assertEqual(manifest_row_after["Route status"], "no-topic-match")
            self.assert_envelope(
                invoke(fixture, "state.validate"), ok=True, op="state.validate"
            )

    def test_route_empty_complete_decision_preserves_applied_history_and_routed_status(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            fixture.put(
                MANIFEST_URI,
                manifest_text([manifest_row(SOURCE_A_URL, 1, route_status="routed")]),
            )
            fixture.put(
                TOPICS_URI,
                topics_text(source_watermark="1"),
            )
            fixture.put(
                RELATIONS_URI,
                relations_text(
                    [
                        relation_row(
                            status="applied",
                            applied_in_pass="summaries/research/test/passes/synthetic.md",
                        )
                    ]
                ),
            )
            fixture.put(
                artifact_uri(SOURCE_A_URL),
                artifact_text(SOURCE_A_URL, 1, route_status="routed"),
            )
            self.assert_envelope(
                invoke(fixture, "state.validate"), ok=True, op="state.validate"
            )
            registries_before = {
                uri: self.read_text(fixture, uri)
                for uri in (MANIFEST_URI, TOPICS_URI, RELATIONS_URI)
            }
            args = self.transaction_args(fixture)
            self.assertEqual(
                [target["path"] for target in args["targets"]],
                [artifact_uri(SOURCE_A_URL)],
            )

            executed = invoke(fixture, "transaction.execute", **args)
            self.assert_envelope(executed, ok=True, op="transaction.execute")
            self.assertEqual(executed["result"]["receipt"]["status"], "applied")
            self.assertEqual(
                {
                    uri: self.read_text(fixture, uri)
                    for uri in (MANIFEST_URI, TOPICS_URI, RELATIONS_URI)
                },
                registries_before,
            )
            applied = atlas_tool._rows(
                self.read_text(fixture, RELATIONS_URI),
                atlas_state.RELATIONS_HEADER,
                RELATIONS_URI,
            )[0][0]
            manifest_row_after, findings = atlas_state.lookup_manifest_row(
                self.read_text(fixture, MANIFEST_URI), SOURCE_A_URL
            )
            self.assertEqual(findings, [])
            self.assertIsNotNone(manifest_row_after)
            assert manifest_row_after is not None
            self.assertEqual(applied["Status"], "applied")
            self.assertEqual(
                applied["Applied in pass"],
                "summaries/research/test/passes/synthetic.md",
            )
            self.assertEqual(manifest_row_after["Route status"], "routed")
            routed = atlas_source.parse_artifact(
                self.read_text(fixture, artifact_uri(SOURCE_A_URL))
            ).values
            self.assertEqual(atlas_source.scalar(routed, "routing_status"), "routed")
            self.assertEqual(atlas_source.scalar(routed, "routed_at"), "2026-07-28")

    def test_route_preflight_rejects_tampered_and_incomplete_exact_projections(
        self,
    ) -> None:
        for mutation in ("tampered-bytes", "incomplete-target-set"):
            with self.subTest(mutation=mutation), temporary_profile() as fixture:
                args = self.transaction_args(fixture)
                if mutation == "tampered-bytes":
                    args["targets"][0]["text"] += "\n"
                else:
                    args["targets"].pop()
                before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
                self.assert_envelope(before, ok=True, op="vault.digest_tree")

                rejected = invoke(fixture, "transaction.execute", **args)
                self.assert_envelope(rejected, ok=False, op="transaction.execute")
                self.assertEqual(
                    response_findings(rejected)[0][0],
                    "ROUTE_PREFLIGHT_PROJECTION_MISMATCH",
                )
                after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
                self.assert_envelope(after, ok=True, op="vault.digest_tree")
                self.assertEqual(after["result"], before["result"])

    def test_effect_preclaim_rejects_tampered_route_renderer_projection_without_writes(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.effect_args(
                fixture, effect_id="effect-0006", with_transactions=True
            )
            args["transactions"][1]["targets"][0]["text"] += "\n"
            projection_uri = args["authority"]["projection_uri"]
            approval_uri = args["authority"]["approval_uri"]
            projection = json.loads(self.read_text(fixture, projection_uri))
            effect = projection["effects"][0]
            effect["origins"][0]["transactions_sha256"] = atlas_transaction.sha256(
                atlas_transaction.canonical_json(args["transactions"])
            )
            args["members"][0]["origin_sha256"] = atlas_transaction.sha256(
                atlas_transaction.canonical_json(effect["origins"][0])
            )
            effect_core = {
                key: value for key, value in effect.items() if key != "effect_sha256"
            }
            effect_sha256 = atlas_transaction.sha256(
                atlas_transaction.canonical_json(effect_core)
            )
            effect["effect_sha256"] = effect_sha256
            projection["effect_hashes"] = [effect_sha256]
            fixture.put(
                projection_uri,
                atlas_transaction.canonical_json(projection).decode("utf-8"),
            )
            projection_revision = self.revision(fixture, projection_uri)

            approval = json.loads(self.read_text(fixture, approval_uri))
            approval["projection_revision"] = projection_revision
            approval["projection_whole_byte_sha256"] = projection_revision.removeprefix(
                "sha256:"
            )
            approval["effect_hashes"] = [effect_sha256]
            approval["effect_uses"][0]["effect_sha256"] = effect_sha256
            fixture.put(
                approval_uri,
                atlas_transaction.canonical_json(approval).decode("utf-8"),
            )
            args["authority"].update(
                {
                    "projection_revision": projection_revision,
                    "approval_revision": self.revision(fixture, approval_uri),
                    "effect_sha256": effect_sha256,
                }
            )
            before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(before, ok=True, op="vault.digest_tree")

            rejected = invoke(fixture, "effect.execute", **args)
            self.assert_envelope(rejected, ok=False, op="effect.execute")
            self.assertEqual(
                response_findings(rejected)[0][0],
                "ROUTE_PREFLIGHT_PROJECTION_MISMATCH",
            )
            after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assert_envelope(after, ok=True, op="vault.digest_tree")
            self.assertEqual(after["result"], before["result"])

    def test_repair_requests_use_validated_generic_transactions(
        self,
    ) -> None:
        repair_request = {
            "version": 1,
            "event": {
                "type": "repair-table-placement",
                "registry": "relations",
            },
        }

        def arrange(fixture: TemporaryAtlasProfile) -> str:
            row = relation_row()
            fixture.put(
                MANIFEST_URI,
                manifest_text([manifest_row(SOURCE_A_URL, 1, route_status="routed")]),
            )
            fixture.put(
                TOPICS_URI,
                topics_text(
                    pending_edge_ids=[row[0]],
                    state="dirty",
                    source_watermark="0",
                ),
            )
            fixture.put(
                RELATIONS_URI,
                relations_text()
                + "\nUse these exact values.\n\n"
                + "| "
                + " | ".join(row)
                + " |\n",
            )
            return row[0]

        with temporary_profile() as fixture:
            edge_id = arrange(fixture)
            repaired = invoke(fixture, "transaction.execute", **repair_request)
            self.assert_envelope(repaired, ok=True, op="transaction.execute")
            self.assertEqual(repaired["result"]["status"], "applied")
            repair_targets = repaired["result"]["receipt"]["targets"]
            self.assertEqual(len(repair_targets), 1)
            self.assertEqual(
                repair_targets[0]["path"],
                RELATIONS_URI.removeprefix("vault://atlas/"),
            )
            self.assertEqual(
                set(repair_targets[0]),
                {"path", "input_sha256", "output_sha256"},
            )
            relations = self.read_text(fixture, RELATIONS_URI)
            self.assertEqual(relations.count(edge_id), 1)
            self.assertLess(
                relations.index(edge_id), relations.index("Use these exact values.")
            )
            self.assert_envelope(
                invoke(fixture, "state.validate"), ok=True, op="state.validate"
            )

            before_replay = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            replayed = invoke(fixture, "transaction.execute", **repair_request)
            self.assert_envelope(replayed, ok=True, op="transaction.execute")
            self.assertEqual(replayed["disposition"], "no-write")
            after_replay = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
            self.assertEqual(after_replay["result"], before_replay["result"])

        with temporary_profile() as fixture:
            arrange(fixture)
            interrupted = invoke(
                fixture,
                "transaction.execute",
                connector=InterruptingConnector(
                    fixture.connector(),
                    path=RELATIONS_URI,
                    after_write=False,
                ),
                **repair_request,
            )
            self.assert_envelope(interrupted, ok=False, op="transaction.execute")
            self.assertEqual(interrupted["disposition"], "recovery-required")
            recovery = interrupted["recovery"]
            self.assertEqual(recovery["operation"], "transaction.recover")

            recovered = invoke(
                fixture,
                recovery["operation"],
                **recovery["args"],
            )
            self.assert_envelope(recovered, ok=True, op="transaction.recover")
            self.assertEqual(recovered["result"]["status"], "rolled-back")
            self.assertEqual(recovered["disposition"], "no-write")

            retried = invoke(fixture, "transaction.execute", **repair_request)
            self.assert_envelope(retried, ok=True, op="transaction.execute")
            self.assertEqual(retried["result"]["status"], "applied")
            self.assert_envelope(
                invoke(fixture, "state.validate"), ok=True, op="state.validate"
            )

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

    def test_route_transaction_records_and_old_loader_preserve_complete_bytes(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            args = self.transaction_args(fixture)
            executed = invoke(fixture, "transaction.execute", **args)
            self.assert_envelope(executed, ok=True, op="transaction.execute")
            receipt = executed["result"]["receipt"]
            transaction_id = receipt["transaction_id"]
            connector = fixture.connector()
            base = f".atlas/transactions/{transaction_id}"

            def read_record(name: str) -> bytes:
                return connector.read_bytes(f"vault://atlas/{base}/{name}")

            port = atlas_tool._Port(connector)
            record, plan = atlas_tool._load_plan(port, transaction_id)
            self.assertEqual(plan.transaction_id, transaction_id)
            self.assertEqual(
                read_record("event.json"),
                atlas_transaction.canonical_json(
                    atlas_transaction.event_record_value(record, plan)
                ),
            )
            intent = atlas_transaction.canonical_json(plan.intent)
            intent_sha256 = atlas_transaction.sha256(intent)
            self.assertEqual(read_record("intent.json"), intent)

            backup_bytes: list[bytes] = []
            for index, target in enumerate(plan.targets):
                backup = atlas_transaction.canonical_json(
                    {
                        "version": 1,
                        "path": target.path,
                        "input_sha256": (
                            None
                            if target.input_bytes is None
                            else atlas_transaction.sha256(target.input_bytes)
                        ),
                        "input_base64": (
                            None
                            if target.input_bytes is None
                            else base64.b64encode(target.input_bytes).decode("ascii")
                        ),
                    }
                )
                backup_bytes.append(backup)
                self.assertEqual(
                    read_record(f"backups/{index:06d}.json"),
                    backup,
                )
                progress = atlas_transaction.canonical_json(
                    {
                        "version": 1,
                        "index": index,
                        "path": target.path,
                        "output_sha256": atlas_transaction.sha256(target.output_bytes),
                    }
                )
                self.assertEqual(
                    read_record(f"progress/{index:06d}.json"),
                    progress,
                )
            prepared = atlas_transaction.canonical_json(
                {
                    "version": 1,
                    "intent_sha256": intent_sha256,
                    "backup_sha256s": [
                        atlas_transaction.sha256(item) for item in backup_bytes
                    ],
                }
            )
            self.assertEqual(read_record("prepared.json"), prepared)
            terminal = atlas_transaction.canonical_json(
                {
                    "version": 1,
                    "status": "applied",
                    "intent_sha256": intent_sha256,
                }
            )
            self.assertEqual(read_record("applied.json"), terminal)
            self.assertEqual(receipt["sha256"], atlas_transaction.sha256(terminal))
            self.assertEqual(
                receipt["targets"],
                [target.intent_value() for target in plan.targets],
            )
            self.assertEqual(
                [target.path for target in plan.targets],
                [
                    target["path"].removeprefix("vault://atlas/")
                    for target in args["targets"]
                ],
            )
            self.assertTrue(
                executed["result"]["phase_uris"][-1].endswith("/applied.json")
            )

            before = read_record("event.json"), read_record("intent.json")
            loaded_record, loaded_plan = atlas_tool._load_plan(port, transaction_id)
            self.assertEqual(loaded_record, record)
            self.assertEqual(loaded_plan, plan)
            self.assertEqual(
                before,
                (read_record("event.json"), read_record("intent.json")),
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

    def test_transaction_successor_rejects_legacy_tampered_and_incomplete_route_projections_without_writes(
        self,
    ) -> None:
        for mutation in ("tampered-bytes", "incomplete-target-set"):
            with self.subTest(mutation=mutation), temporary_profile() as fixture:
                args = self.transaction_args(fixture)
                if mutation == "tampered-bytes":
                    args["targets"][0]["text"] += "\n"
                else:
                    args["targets"].pop()

                record = atlas_tool._event(args["event_record"])
                pending, expected = atlas_tool._targets(args["targets"])
                connector = fixture.connector()
                with connector.mutation_session():
                    targets = atlas_tool._bind(connector, pending, expected)
                    plan = atlas_tool._plan(record, targets)
                    atlas_transaction.store_event(
                        atlas_tool._Port(connector),
                        plan.transaction_root,
                        record,
                        plan,
                    )

                interrupting = InterruptingConnector(
                    fixture.connector(),
                    path=args["targets"][0]["path"],
                    after_write=False,
                )
                with interrupting.mutation_session():
                    status = atlas_transaction.execute_transaction(
                        atlas_tool._Port(interrupting),
                        plan.transaction_root,
                        plan,
                        target_allowlist=atlas_tool._target_allowed,
                        target_rank=atlas_tool._rank,
                    )
                self.assertEqual(status, "rolled-back")

                before = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
                self.assert_envelope(before, ok=True, op="vault.digest_tree")
                rejected = invoke(
                    fixture,
                    "transaction.successor",
                    transaction_id=plan.transaction_id,
                )
                self.assert_envelope(rejected, ok=False, op="transaction.successor")
                self.assertEqual(
                    response_findings(rejected)[0][0],
                    "ROUTE_PREFLIGHT_PROJECTION_MISMATCH",
                )
                after = invoke(fixture, "vault.digest_tree", path="vault://atlas/")
                self.assert_envelope(after, ok=True, op="vault.digest_tree")
                self.assertEqual(after["result"], before["result"])

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
                args["transactions"][1]["targets"][0]["text"],
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
                args["transactions"][1]["targets"][0]["text"],
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

    def test_index_capability_and_read_only_fail_closed(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            connector = fixture.connector()
            advertised = atlas_tool.capabilities(connector)
            self.assert_envelope(advertised, ok=True, op="capabilities")
            advertised_operations = [
                item["operation"] for item in advertised["result"]["operations"]
            ]
            self.assertEqual(advertised_operations, list(LIFECYCLE_OPERATIONS))
            read_only = ReadOnlyTopicConnector(connector)
            unavailable = atlas_tool.capabilities(read_only)
            self.assert_envelope(unavailable, ok=True, op="capabilities")
            unavailable_operations = [
                item["operation"] for item in unavailable["result"]["operations"]
            ]
            self.assertNotIn("index.create_topic", unavailable_operations)
            self.assertNotIn("index.recover_topic", unavailable_operations)
            create = invoke(
                fixture,
                "index.create_topic",
                connector=read_only,
                **topic_create_args(),
            )
            self.assert_envelope(create, ok=False, op="index.create_topic")
            self.assertEqual(response_findings(create)[0][0], "MUTATION_UNAVAILABLE")
            recover = invoke(
                fixture,
                "index.recover_topic",
                connector=read_only,
                version=1,
                transaction_id="0" * 16 + "-a000000",
                request=topic_create_args(),
            )
            self.assert_envelope(recover, ok=False, op="index.recover_topic")
            self.assertEqual(
                response_findings(recover)[0][0],
                "MUTATION_UNAVAILABLE",
            )

    def test_mutation_gate_accepts_alternate_adapter_and_rejects_wrong_root(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)

            missing = object()

            class LyingCapabilityConnector(RecordingTopicConnector):
                def __init__(self, inner: Any, field: str, value: Any) -> None:
                    super().__init__(inner)
                    self._field = field
                    self._value = value

                def capabilities(self) -> dict[str, Any]:
                    values = dict(self._inner.capabilities())
                    if self._value is missing:
                        values.pop(self._field, None)
                    else:
                        values[self._field] = self._value
                    return values

            for label, value in (
                ("logical-root", "vault://other/"),
                ("missing-logical-root", missing),
            ):
                with self.subTest(label=label):
                    connector = LyingCapabilityConnector(
                        fixture.connector(), "logical_root", value
                    )
                    response = invoke(
                        fixture,
                        "index.create_topic",
                        connector=connector,
                        **topic_create_args(),
                    )
                    self.assert_envelope(response, ok=False, op="index.create_topic")
                    self.assertEqual(
                        response_findings(response)[0],
                        (
                            "BINDING_INVALID",
                            "connector",
                            "capabilities are invalid",
                        ),
                    )
                    self.assertEqual(connector.reads, [])
                    self.assertEqual(connector.writes, [])
                    self.assertEqual(connector.deletes, [])

            alternate = LyingCapabilityConnector(
                fixture.connector(), "adapter", "alternate-cas-adapter"
            )
            accepted = invoke(
                fixture,
                "index.create_topic",
                connector=alternate,
                **topic_create_args(),
            )
            self.assert_envelope(accepted, ok=True, op="index.create_topic")
            read_only = RecordingTopicConnector(
                ReadOnlyTopicConnector(fixture.connector())
            )
            unavailable = invoke(
                fixture,
                "vault.conditional_replace",
                connector=read_only,
                path="vault://atlas/tmp/mutation-gate-control.txt",
                expected_revision="missing",
                text="control\n",
            )
            self.assert_envelope(unavailable, ok=False, op="vault.conditional_replace")
            self.assertEqual(
                response_findings(unavailable)[0][0], "MUTATION_UNAVAILABLE"
            )
            self.assertEqual(read_only.reads, [])
            self.assertEqual(read_only.writes, [])
            self.assertEqual(read_only.deletes, [])

            valid = invoke(
                fixture,
                "vault.conditional_replace",
                path="vault://atlas/tmp/mutation-gate-control.txt",
                expected_revision="missing",
                text="control\n",
            )
            self.assert_envelope(valid, ok=True, op="vault.conditional_replace")

    def test_catalog_method_requirements_use_call_time_callable_checks(self) -> None:
        spec = next(
            item
            for item in atlas_tool.operation_specs()
            if item.literal == "index.create_topic"
        )
        self.assertEqual(
            spec.connector_methods,
            {
                "conditional_replace",
                "delete",
                "list",
                "mutation_session",
                "read_bytes",
                "read_text",
                "revision",
            },
        )

        class MethodConnector(RecordingTopicConnector):
            def __init__(self, inner: Any, method: str, value: Any) -> None:
                super().__init__(inner)
                self._method = method
                self._value = value

            def __getattribute__(self, name: str) -> Any:
                if name == object.__getattribute__(self, "_method"):
                    value = object.__getattribute__(self, "_value")
                    if isinstance(value, BaseException):
                        raise value
                    return value
                return super().__getattribute__(name)

        for method in sorted(spec.connector_methods):
            with self.subTest(method=method), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                connector = MethodConnector(fixture.connector(), method, None)
                response = invoke(
                    fixture,
                    "index.create_topic",
                    connector=connector,
                    **topic_create_args(),
                )
                self.assert_envelope(response, ok=False, op="index.create_topic")
                self.assertEqual(
                    response_findings(response)[0],
                    (
                        "BINDING_INVALID",
                        "connector",
                        f"declared connector method {method} is not callable",
                    ),
                )
                self.assertEqual(connector.reads, [])
                self.assertEqual(connector.writes, [])
                self.assertEqual(connector.deletes, [])
                self.assertEqual(connector.mutation_sessions, 0)

        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            connector = MethodConnector(fixture.connector(), "write_json", None)
            response = invoke(
                fixture,
                "index.create_topic",
                connector=connector,
                **topic_create_args(),
            )
            self.assert_envelope(response, ok=True, op="index.create_topic")

    def test_index_create_shape_findings_are_generic_before_any_io(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            missing = topic_create_args()
            del missing["created_on"]
            unknown = topic_create_args()
            unknown["extra"] = "reject"
            for label, args, expected_path in (
                ("missing", missing, "args.created_on"),
                ("unknown", unknown, "args.extra"),
            ):
                with self.subTest(case=label):
                    connector = RecordingTopicConnector(fixture.connector())
                    response = invoke(
                        fixture,
                        "index.create_topic",
                        connector=connector,
                        **args,
                    )
                    self.assert_envelope(response, ok=False, op="index.create_topic")
                    self.assertEqual(
                        response_findings(response)[0][:2],
                        ("ARGUMENTS_INVALID", expected_path),
                    )
                    self.assertEqual(connector.reads, [])
                    self.assertEqual(connector.writes, [])
                    self.assertEqual(connector.deletes, [])

            non_object = atlas_tool.execute(
                request("index.create_topic", []), connector=connector
            )
            self.assert_envelope(non_object, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(non_object)[0][:2],
                ("REQUEST_INVALID", "args"),
            )
            self.assertEqual(connector.reads, [])
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])

    def test_index_projection_identity_matrix_rejects_before_writes(self) -> None:
        cases = (
            (
                "unresolved",
                lambda text: text.replace(
                    "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
                    "summaries/research/test/test-subdomain/topics/missing-topic/INDEX.md",
                    1,
                ),
                "SUBDOMAIN_PROJECTION_INVALID",
                {},
            ),
            (
                "wrong-domain",
                lambda text: text.replace(
                    "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
                    "summaries/research/other/test-subdomain/topics/test-topic/INDEX.md",
                    1,
                ),
                "SUBDOMAIN_PROJECTION_INVALID",
                {},
            ),
            (
                "wrong-subdomain",
                lambda text: text.replace(
                    "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
                    "summaries/research/test/other/topics/test-topic/INDEX.md",
                    1,
                ),
                "SUBDOMAIN_PROJECTION_INVALID",
                {},
            ),
            (
                "unsafe",
                lambda text: text.replace(
                    "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
                    "summaries/research/test/test-subdomain/topics/../test-topic/INDEX.md",
                    1,
                ),
                "SUBDOMAIN_PROJECTION_INVALID",
                {},
            ),
            (
                "malformed",
                lambda text: text.replace(
                    "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
                    "external://topic",
                    1,
                ),
                "SUBDOMAIN_PROJECTION_INVALID",
                {},
            ),
            (
                "related-noncanonical",
                lambda text: text.replace(
                    "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
                    r"summaries/research/test/test-subdomain/topics/test\-topic/INDEX.md",
                    1,
                ),
                "TOPIC_COMPATIBILITY_CONFLICT",
                {"related_topic_ids": [TOPIC_ID]},
            ),
        )
        for name, mutate, code, overrides in cases:
            with self.subTest(case=name), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                original = topic_subdomain_text()
                fixture.put(TOPIC_SUBDOMAIN_URI, mutate(original))
                connector = RecordingTopicConnector(fixture.connector())
                response = invoke(
                    fixture,
                    "index.create_topic",
                    connector=connector,
                    **topic_create_args(**overrides),
                )
                self.assert_envelope(response, ok=False, op="index.create_topic")
                self.assertEqual(response_findings(response)[0][0], code)
                self.assertEqual(connector.writes, [])
                self.assertEqual(connector.deletes, [])
                self.assertFalse(
                    any("/.atlas/transactions/" in path for path in connector.reads)
                )

    def test_cli_duplicate_public_json_keys_are_safe_and_side_effect_free(self) -> None:
        command = [
            sys.executable,
            str(ROOT / "scripts" / "atlas_tool.py"),
            "call",
            "--input",
            "-",
        ]
        duplicate_top_level = (
            b'{"version":2,"op":"vault.read","op":"vault.list",'
            b'"args":{"path":"vault://atlas/missing"}}'
        )
        duplicate_nested = (
            b'{"version":2,"op":"vault.read",'
            b'"args":{"path":"vault://atlas/missing",'
            b'"path":"vault://atlas/rejected"}}'
        )
        responses = []
        for payload in (duplicate_top_level, duplicate_nested):
            completed = subprocess.run(
                command,
                input=payload,
                capture_output=True,
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            responses.append(completed.stdout)
        decoded = [json.loads(response) for response in responses]
        for response in decoded:
            self.assert_envelope(response, ok=False, op=None)
            self.assertEqual(
                response_findings(response)[0][:2], ("REQUEST_INVALID", "input")
            )
        self.assertEqual(
            [response_findings(response)[0][2] for response in decoded],
            ["duplicate object key 'op'", "duplicate object key 'path'"],
        )

    def test_transaction_preintent_typed_reread_errors_preserve_taxonomy(self) -> None:
        targets = tuple(
            atlas_transaction.TransactionTarget(
                f"target-{index}",
                None,
                f"output-{index}".encode("ascii"),
            )
            for index in range(3)
        )
        plan = atlas_transaction.TransactionPlan(
            "a" * 16,
            "a" * 16 + "-a000000",
            0,
            None,
            {},
            targets,
            "transactions",
        )

        class ReadPort:
            def __init__(self, error: BaseException) -> None:
                self.error = error
                self.reads = 0
                self.creates: list[str] = []
                self.writes: list[str] = []

            def read(self, _path: str) -> bytes | None:
                self.reads += 1
                if self.reads == 2:
                    raise self.error
                return None

            def read_record(self, _path: str) -> bytes | None:
                return None

            def create(self, path: str, _data: bytes) -> None:
                self.creates.append(path)

            def write(self, path: str, _data: bytes, _expected: str) -> None:
                self.writes.append(path)

            def delete(self, _path: str, _expected: str) -> None:
                raise AssertionError("delete must not run before intent")

        binding_port = ReadPort(atlas_connector.ConnectorBindingError("unsafe"))
        with self.assertRaises(atlas_connector.ConnectorBindingError):
            atlas_transaction.execute_transaction(binding_port, "transactions", plan)
        binding_response = atlas_tool._exception(
            "transaction.execute", atlas_connector.ConnectorBindingError("unsafe")
        )
        self.assertEqual(response_findings(binding_response)[0][0], "BINDING_INVALID")
        self.assertEqual(binding_port.creates, [])
        self.assertEqual(binding_port.writes, [])

        semantic_port = ReadPort(ValueError("semantic reread conflict"))
        with self.assertRaises(atlas_transaction.TransactionTargetConflict):
            atlas_transaction.execute_transaction(semantic_port, "transactions", plan)
        conflict_response = atlas_tool._exception(
            "transaction.execute",
            atlas_transaction.TransactionTargetConflict("target-1"),
        )
        self.assertEqual(response_findings(conflict_response)[0][0], "MANUAL_CONFLICT")
        self.assertEqual(semantic_port.creates, [])
        self.assertEqual(semantic_port.writes, [])

    def test_topic_recovery_routes_binding_reconstruction_to_index_owner(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            with self.assertRaises(SystemExit):
                invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix="/progress/000002.json",
                        stop_process=True,
                    ),
                    **args,
                )
            transaction_id = topic_event_transaction_id(fixture)
            with patch.object(
                atlas_index,
                "load_topic_binding",
                wraps=atlas_index.load_topic_binding,
            ) as loader:
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "applied")
            self.assertGreater(loader.call_count, 0)

    def test_index_create_materializes_missing_subdomain(self) -> None:
        with temporary_profile() as fixture:
            fixture.put(TOPICS_URI, topic_registry_text())
            created = invoke(
                fixture,
                "index.create_topic",
                **topic_create_args(),
            )
            self.assert_envelope(created, ok=True, op="index.create_topic")
            self.assertEqual(created["result"]["state"], "created")
            subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
            self.assertIn("note_type: subdomain-index", subdomain)
            self.assertIn('domain: "test"', subdomain)
            self.assertIn('subdomain: "test-subdomain"', subdomain)
            self.assertIn("new-topic", subdomain)
            topic = self.read_text(fixture, TOPIC_CREATE_URI)
            self.assertIn('topic: "new-topic"', topic)
            registry = self.read_text(fixture, TOPICS_URI)
            self.assertIn("new-topic", registry)

    def test_index_create_confirm_receipt_and_exact_three_target_order(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            connector = RecordingTopicConnector(fixture.connector())
            args = topic_create_args()
            created = invoke(
                fixture,
                "index.create_topic",
                connector=connector,
                **args,
            )
            self.assert_envelope(created, ok=True, op="index.create_topic")
            result = created["result"]
            self.assertEqual(result["state"], "created")
            self.assertEqual(
                list(result["paths"]),
                ["topic", "subdomain", "registry"],
            )
            self.assertEqual(
                [item["path"] for item in result["receipt"]["targets"]],
                [TOPIC_CREATE_URI, TOPIC_SUBDOMAIN_URI, TOPICS_URI],
            )
            self.assertEqual(
                [item["path"] for item in result["receipt"]["targets"]],
                list(result["paths"].values()),
            )
            transaction_id = result["receipt"]["transaction_id"]
            transaction_root = topic_transaction_root(fixture, transaction_id)
            expected_writes = [
                f"{transaction_root}/event.json",
                f"{transaction_root}/intent.json",
                f"{transaction_root}/backups/000000.json",
                f"{transaction_root}/backups/000001.json",
                f"{transaction_root}/backups/000002.json",
                f"{transaction_root}/prepared.json",
                TOPIC_CREATE_URI,
                f"{transaction_root}/progress/000000.json",
                TOPIC_SUBDOMAIN_URI,
                f"{transaction_root}/progress/000001.json",
                TOPICS_URI,
                f"{transaction_root}/progress/000002.json",
                f"{transaction_root}/applied.json",
            ]
            self.assertEqual(connector.writes, expected_writes)
            transaction_writes = [
                path
                for path in connector.writes
                if path.startswith(transaction_root + "/")
            ]
            self.assertEqual(
                transaction_writes,
                [
                    path
                    for path in expected_writes
                    if path.startswith(transaction_root + "/")
                ],
            )
            non_transaction_writes = [
                path
                for path in connector.writes
                if not path.startswith(transaction_root + "/")
            ]
            self.assertEqual(
                non_transaction_writes,
                [TOPIC_CREATE_URI, TOPIC_SUBDOMAIN_URI, TOPICS_URI],
            )
            self.assertNotIn(MANIFEST_URI, non_transaction_writes)
            self.assertNotIn(RELATIONS_URI, non_transaction_writes)
            self.assertEqual(connector.deletes, [])
            before_confirm = len(connector.writes)
            confirmed = invoke(
                fixture,
                "index.create_topic",
                connector=connector,
                **args,
            )
            self.assert_envelope(confirmed, ok=True, op="index.create_topic")
            self.assertEqual(confirmed["result"]["state"], "confirmed")
            self.assertIsNone(confirmed["result"]["transaction"])
            self.assertIsNone(confirmed["result"]["receipt"])
            self.assertEqual(len(connector.writes), before_confirm)
            self.assertEqual(connector.deletes, [])

    def test_index_create_rejects_stale_bound_subdomain_before_intent(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            connector = StaleTopicConnector(fixture.connector())
            response = invoke(
                fixture,
                "index.create_topic",
                connector=connector,
                **topic_create_args(),
            )
            self.assert_envelope(response, ok=False, op="index.create_topic")
            self.assertEqual(response_findings(response)[0][0], "REVISION_STALE")
            self.assertEqual(
                self.revision(fixture, TOPIC_CREATE_URI),
                "missing",
            )

    def test_index_post_validation_failure_rolls_back_without_created_result(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            before_subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
            before_topics = self.read_text(fixture, TOPICS_URI)
            with patch.object(
                atlas_index.TopicPostValidation,
                "validate",
                side_effect=atlas_transaction.TransactionError(
                    "synthetic post-validation failure"
                ),
            ):
                response = invoke(
                    fixture,
                    "index.create_topic",
                    **topic_create_args(),
                )
            self.assert_envelope(response, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(response)[0][0],
                "TRANSACTION_RECOVERABLE",
            )
            self.assertEqual(self.revision(fixture, TOPIC_CREATE_URI), "missing")
            self.assertEqual(
                self.read_text(fixture, TOPIC_SUBDOMAIN_URI),
                before_subdomain,
            )
            self.assertEqual(self.read_text(fixture, TOPICS_URI), before_topics)

    def test_index_post_intent_faults_keep_identity_until_exact_recovery(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            initial = invoke(
                fixture,
                "index.create_topic",
                connector=RecoveryReadFailureConnector(
                    fixture.connector(),
                    suffix="/topics/new-topic/INDEX.md",
                ),
                **args,
            )
            self.assert_envelope(initial, ok=False, op="index.create_topic")
            finding = response_findings(initial)[0]
            self.assertEqual(finding[0], "TRANSACTION_RECOVERABLE")
            txid = topic_transaction_id(initial)
            self.assertEqual(
                finding[1],
                topic_transaction_root(fixture, txid) + "/intent.json",
            )
            self.assertEqual(
                finding[2],
                f"transaction {txid} requires exact-request recovery",
            )
            recovered = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=txid,
                request=args,
            )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "rolled-back")
            self.assertTrue(recovered["result"]["successor_eligible"])
            self.assertEqual(self.revision(fixture, TOPIC_CREATE_URI), "missing")

        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            initial = invoke(
                fixture,
                "index.create_topic",
                connector=AppliedRevisionFailureConnector(fixture.connector()),
                **args,
            )
            self.assert_envelope(initial, ok=False, op="index.create_topic")
            finding = response_findings(initial)[0]
            self.assertEqual(finding[0], "TRANSACTION_RECOVERABLE")
            txid = topic_transaction_id(initial)
            self.assertEqual(
                finding[1],
                topic_transaction_root(fixture, txid) + "/intent.json",
            )
            self.assertEqual(
                finding[2],
                f"transaction {txid} requires exact-request recovery",
            )
            recovered = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=txid,
                request=args,
            )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "applied")
            self.assertFalse(recovered["result"]["successor_eligible"])
            self.assertEqual(
                self.revision(fixture, TOPIC_CREATE_URI),
                recovered["result"]["receipt"]["target_revisions"][TOPIC_CREATE_URI],
            )

    def test_index_recovery_operational_faults_preserve_identity_for_exact_retry(
        self,
    ) -> None:
        fault_cases = (
            ("rollback", "conditional_replace", TOPIC_SUBDOMAIN_URI),
            ("terminal", "conditional_replace", "/rolled-back.json"),
            ("receipt", "revision", TOPIC_CREATE_URI),
        )
        for error in ("oserror", "transaction"):
            for stage, operation, suffix in fault_cases:
                with (
                    self.subTest(error=error, stage=stage),
                    temporary_profile() as fixture,
                ):
                    self.prepare_topic_fixture(fixture)
                    args = topic_create_args()
                    with self.assertRaises(SystemExit):
                        invoke(
                            fixture,
                            "index.create_topic",
                            connector=AfterWriteFailureConnector(
                                fixture.connector(),
                                suffix=TOPIC_SUBDOMAIN_URI,
                                stop_process=True,
                            ),
                            **args,
                        )
                    transaction_id = topic_event_transaction_id(fixture)
                    interrupted = invoke(
                        fixture,
                        "index.recover_topic",
                        connector=RecoveryFaultConnector(
                            fixture.connector(),
                            suffix=suffix,
                            operation=operation,
                            error=error,
                        ),
                        version=1,
                        transaction_id=transaction_id,
                        request=args,
                    )
                    self.assert_envelope(
                        interrupted, ok=False, op="index.recover_topic"
                    )
                    finding = response_findings(interrupted)[0]
                    self.assertEqual(finding[0], "TRANSACTION_RECOVERABLE")
                    self.assertEqual(
                        finding[1],
                        topic_transaction_root(fixture, transaction_id)
                        + "/intent.json",
                    )
                    self.assertEqual(
                        finding[2],
                        f"transaction {transaction_id} requires exact-request recovery",
                    )
                    recovered = invoke(
                        fixture,
                        "index.recover_topic",
                        version=1,
                        transaction_id=transaction_id,
                        request=args,
                    )
                    self.assert_envelope(recovered, ok=True, op="index.recover_topic")
                    self.assertEqual(recovered["result"]["status"], "rolled-back")
                    self.assertTrue(recovered["result"]["successor_eligible"])

    def test_index_rejects_impossible_terminal_phase_combinations_without_successor(
        self,
    ) -> None:
        def terminal_text(
            fixture: TemporaryAtlasProfile, transaction_id: str, status: str
        ) -> str:
            intent = fixture.connector().read_bytes(
                topic_transaction_root(fixture, transaction_id) + "/intent.json"
            )
            intent_value = json.loads(intent.decode("utf-8"))
            value: dict[str, Any] = {
                "version": 1,
                "status": status,
                "intent_sha256": atlas_transaction.sha256(intent),
            }
            if status == "applied":
                value["owner_proof"] = {
                    "owner": atlas_index.TOPIC_OWNER_ID,
                    "policy": "topic-post-v1",
                    "request_sha256": intent_value["request_sha256"],
                    "target_output_sha256s": [
                        target["output_sha256"] for target in intent_value["targets"]
                    ],
                }
            return atlas_transaction.canonical_json(value).decode("utf-8")

        impossible = (
            ("aborted", "/prepared.json"),
            ("no-op", "/prepared.json"),
            ("rolled-back", "/backups/000000.json"),
            ("applied", "/backups/000000.json"),
        )
        for status, suffix in impossible:
            with self.subTest(status=status), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                before_subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
                before_topics = self.read_text(fixture, TOPICS_URI)
                before_topic = self.revision(fixture, TOPIC_CREATE_URI)
                with self.assertRaises(SystemExit):
                    invoke(
                        fixture,
                        "index.create_topic",
                        connector=AfterWriteFailureConnector(
                            fixture.connector(),
                            suffix=suffix,
                            stop_process=True,
                        ),
                        **args,
                    )
                transaction_id = topic_event_transaction_id(fixture)
                fixture.put(
                    f"{topic_transaction_root(fixture, transaction_id)}/{status}.json",
                    terminal_text(fixture, transaction_id, status),
                )
                rejected = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                self.assert_envelope(rejected, ok=False, op="index.recover_topic")
                self.assertEqual(
                    response_findings(rejected)[0][0],
                    "TRANSACTION_RECORD_INVALID",
                )
                self.assertEqual(
                    self.read_text(fixture, TOPIC_SUBDOMAIN_URI),
                    before_subdomain,
                )
                self.assertEqual(self.read_text(fixture, TOPICS_URI), before_topics)
                self.assertEqual(self.revision(fixture, TOPIC_CREATE_URI), before_topic)
                self.assertEqual(
                    len(
                        [
                            path
                            for path in fixture.connector().list(
                                "vault://atlas/.atlas/transactions"
                            )
                            if path.endswith("/event.json")
                        ]
                    ),
                    1,
                )

        controls = (
            ("aborted", "/backups/000000.json", True),
            ("rolled-back", "/prepared.json", True),
            ("applied", "/progress/000002.json", False),
            ("manual-conflict", "/prepared.json", False),
        )
        for status, suffix, successor_eligible in controls:
            with self.subTest(control=status), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                with self.assertRaises(SystemExit):
                    invoke(
                        fixture,
                        "index.create_topic",
                        connector=AfterWriteFailureConnector(
                            fixture.connector(),
                            suffix=suffix,
                            stop_process=True,
                        ),
                        **args,
                    )
                transaction_id = topic_event_transaction_id(fixture)
                fixture.put(
                    f"{topic_transaction_root(fixture, transaction_id)}/{status}.json",
                    terminal_text(fixture, transaction_id, status),
                )
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                if status == "manual-conflict":
                    self.assert_envelope(recovered, ok=False, op="index.recover_topic")
                    self.assertEqual(
                        response_findings(recovered)[0][0], "MANUAL_CONFLICT"
                    )
                else:
                    self.assert_envelope(recovered, ok=True, op="index.recover_topic")
                    self.assertEqual(recovered["result"]["status"], status)
                    self.assertEqual(
                        recovered["result"]["successor_eligible"],
                        successor_eligible,
                    )

    def test_index_recovery_runs_owner_validation_before_applied_terminal(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            before_subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
            before_topics = self.read_text(fixture, TOPICS_URI)
            with self.assertRaises(SystemExit):
                invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix="/progress/000002.json",
                        stop_process=True,
                    ),
                    **args,
                )
            txid = topic_event_transaction_id(fixture)
            transaction_root = fixture.instance / topic_transaction_root(
                fixture, txid
            ).removeprefix("vault://atlas/")
            self.assertFalse((transaction_root / "applied.json").exists())
            with patch.object(
                atlas_index.TopicPostValidation,
                "validate",
                side_effect=atlas_transaction.TransactionError(
                    "synthetic recovery post-validation failure"
                ),
            ):
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=txid,
                    request=args,
                )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "rolled-back")
            self.assertFalse((transaction_root / "applied.json").exists())
            self.assertEqual(self.revision(fixture, TOPIC_CREATE_URI), "missing")
            self.assertEqual(
                self.read_text(fixture, TOPIC_SUBDOMAIN_URI),
                before_subdomain,
            )
            self.assertEqual(self.read_text(fixture, TOPICS_URI), before_topics)

    def test_index_partial_unprepared_backups_recover_and_replay(self) -> None:
        for index in range(3):
            with self.subTest(index=index), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                before_subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
                before_topics = self.read_text(fixture, TOPICS_URI)
                interrupted = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=f"/backups/{index:06d}.json",
                    ),
                    **args,
                )
                self.assert_envelope(interrupted, ok=False, op="index.create_topic")
                self.assertEqual(
                    response_findings(interrupted)[0][0],
                    "TRANSACTION_RECOVERABLE",
                )
                txid = topic_transaction_id(interrupted)
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=txid,
                    request=args,
                )
                self.assert_envelope(recovered, ok=True, op="index.recover_topic")
                self.assertEqual(recovered["result"]["status"], "aborted")
                self.assertEqual(
                    self.revision(fixture, TOPIC_CREATE_URI),
                    "missing",
                )
                self.assertEqual(
                    self.read_text(fixture, TOPIC_SUBDOMAIN_URI),
                    before_subdomain,
                )
                self.assertEqual(self.read_text(fixture, TOPICS_URI), before_topics)
                replay = invoke(fixture, "index.create_topic", **args)
                self.assert_envelope(replay, ok=True, op="index.create_topic")
                self.assertEqual(replay["result"]["state"], "created")
                self.assertEqual(replay["result"]["receipt"]["attempt"], 1)

    def test_index_recovery_rejects_nonprefix_unprepared_backups_before_targets(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            interrupted = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix="/backups/000001.json",
                ),
                **args,
            )
            self.assert_envelope(interrupted, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(interrupted)[0][0],
                "TRANSACTION_RECOVERABLE",
            )
            transaction_id = topic_transaction_id(interrupted)
            transaction_root = fixture.instance / topic_transaction_root(
                fixture, transaction_id
            ).removeprefix("vault://atlas/")
            (transaction_root / "backups" / "000000.json").unlink()
            self.assertTrue((transaction_root / "backups" / "000001.json").is_file())
            self.assertFalse((transaction_root / "prepared.json").exists())

            connector = RecordingTopicConnector(fixture.connector())
            rejected = invoke(
                fixture,
                "index.recover_topic",
                connector=connector,
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(rejected, ok=False, op="index.recover_topic")
            finding = response_findings(rejected)[0]
            self.assertEqual(
                finding[:2],
                (
                    "TRANSACTION_RECORD_INVALID",
                    topic_transaction_root(fixture, transaction_id)
                    + "/backups/000001.json",
                ),
            )
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])
            self.assertNotIn(TOPIC_CREATE_URI, connector.reads)
            self.assertNotIn(TOPIC_SUBDOMAIN_URI, connector.reads)
            self.assertNotIn(TOPICS_URI, connector.reads)

    def test_index_attempt_one_requires_verified_unique_predecessor_before_targets(
        self,
    ) -> None:
        for corruption in ("collision", "corrupt-intent"):
            with self.subTest(corruption=corruption), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                initial = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix="/backups/000000.json",
                    ),
                    **args,
                )
                self.assert_envelope(initial, ok=False, op="index.create_topic")
                self.assertEqual(
                    response_findings(initial)[0][0],
                    "TRANSACTION_RECOVERABLE",
                )
                predecessor_id = topic_transaction_id(initial)
                replay = invoke(fixture, "index.create_topic", **args)
                self.assert_envelope(replay, ok=True, op="index.create_topic")
                self.assertEqual(replay["result"]["receipt"]["attempt"], 1)
                successor_id = replay["result"]["receipt"]["transaction_id"]
                predecessor_root = fixture.instance / topic_transaction_root(
                    fixture, predecessor_id
                ).removeprefix("vault://atlas/")
                if corruption == "collision":
                    intent = (predecessor_root / "intent.json").read_bytes()
                    intent_hash = atlas_transaction.sha256(intent)
                    (predecessor_root / "applied.json").write_bytes(
                        atlas_transaction.canonical_json(
                            {
                                "version": 1,
                                "status": "applied",
                                "intent_sha256": intent_hash,
                            }
                        )
                    )
                else:
                    (predecessor_root / "intent.json").write_bytes(b"corrupt\n")

                connector = RecordingTopicConnector(fixture.connector())
                rejected = invoke(
                    fixture,
                    "index.recover_topic",
                    connector=connector,
                    version=1,
                    transaction_id=successor_id,
                    request=args,
                )
                self.assert_envelope(rejected, ok=False, op="index.recover_topic")
                self.assertEqual(
                    response_findings(rejected)[0][0],
                    "TRANSACTION_RECORD_INVALID",
                )
                self.assertNotIn(TOPIC_CREATE_URI, connector.reads)
                self.assertNotIn(TOPIC_SUBDOMAIN_URI, connector.reads)
                self.assertNotIn(TOPICS_URI, connector.reads)
                event_paths = [
                    path
                    for path in fixture.connector().list(
                        "vault://atlas/.atlas/transactions"
                    )
                    if path.endswith("/event.json")
                ]
                self.assertEqual(
                    {Path(path).parent.name for path in event_paths},
                    {predecessor_id, successor_id},
                )

    def test_index_event_only_ack_loss_retries_and_later_records_fail_closed(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            before_subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
            before_topics = self.read_text(fixture, TOPICS_URI)
            initial = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix="/event.json",
                ),
                **args,
            )
            self.assert_envelope(initial, ok=False, op="index.create_topic")
            self.assertEqual(response_findings(initial)[0][0], "IO_FAILURE")
            txid = topic_event_transaction_id(fixture)
            transaction_root = fixture.instance / topic_transaction_root(
                fixture, txid
            ).removeprefix("vault://atlas/")
            self.assertFalse((transaction_root / "intent.json").exists())
            self.assertEqual(self.revision(fixture, TOPIC_CREATE_URI), "missing")
            self.assertEqual(
                self.read_text(fixture, TOPIC_SUBDOMAIN_URI),
                before_subdomain,
            )
            self.assertEqual(self.read_text(fixture, TOPICS_URI), before_topics)
            retry = invoke(fixture, "index.create_topic", **args)
            self.assert_envelope(retry, ok=True, op="index.create_topic")
            self.assertEqual(retry["result"]["state"], "created")
            self.assertEqual(retry["result"]["receipt"]["transaction_id"], txid)

        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            initial = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix="/event.json",
                ),
                **args,
            )
            self.assert_envelope(initial, ok=False, op="index.create_topic")
            txid = topic_event_transaction_id(fixture)
            fixture.put(
                f"{topic_transaction_root(fixture, txid)}/backups/000000.json",
                "later record without intent\n",
            )
            later = invoke(fixture, "index.create_topic", **args)
            self.assert_envelope(later, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(later)[0][0],
                "TRANSACTION_RECORD_INVALID",
            )

        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            initial = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix="/event.json",
                ),
                **args,
            )
            self.assert_envelope(initial, ok=False, op="index.create_topic")
            txid = topic_event_transaction_id(fixture)
            fixture.put(
                f"{topic_transaction_root(fixture, txid)}/event.json",
                "corrupt event\n",
            )
            corrupt = invoke(fixture, "index.create_topic", **args)
            self.assert_envelope(corrupt, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(corrupt)[0][0],
                "TRANSACTION_RECORD_INVALID",
            )

    def test_index_attempt_one_event_only_ack_loss_resumes_exact_successor(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            initial = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix=TOPIC_CREATE_URI,
                ),
                **args,
            )
            self.assert_envelope(initial, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(initial)[0][0],
                "TRANSACTION_RECOVERABLE",
            )
            predecessor_id = topic_transaction_id(initial)
            successor_id = predecessor_id[:-8] + "-a000001"
            event_loss = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix="/event.json",
                ),
                **args,
            )
            self.assert_envelope(event_loss, ok=False, op="index.create_topic")
            self.assertEqual(response_findings(event_loss)[0][0], "IO_FAILURE")
            event_paths = [
                path
                for path in fixture.connector().list(
                    "vault://atlas/.atlas/transactions"
                )
                if path.endswith("/event.json")
            ]
            self.assertEqual(
                {Path(path).parent.name for path in event_paths},
                {predecessor_id, successor_id},
            )
            replay = invoke(fixture, "index.create_topic", **args)
            self.assert_envelope(replay, ok=True, op="index.create_topic")
            self.assertEqual(replay["result"]["state"], "created")
            self.assertEqual(replay["result"]["receipt"]["attempt"], 1)
            self.assertEqual(
                replay["result"]["receipt"]["transaction_id"],
                successor_id,
            )
            self.assertEqual(replay["result"]["receipt"]["status"], "applied")
            self.assertEqual(
                {
                    Path(path).parent.name
                    for path in fixture.connector().list(
                        "vault://atlas/.atlas/transactions"
                    )
                    if path.endswith("/event.json")
                },
                {predecessor_id, successor_id},
            )
            for path in (TOPIC_CREATE_URI, TOPIC_SUBDOMAIN_URI, TOPICS_URI):
                self.assertNotEqual(self.revision(fixture, path), "missing")

        for corruption in ("corrupted", "different", "later"):
            with self.subTest(corruption=corruption), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                initial = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_CREATE_URI,
                    ),
                    **args,
                )
                self.assert_envelope(initial, ok=False, op="index.create_topic")
                predecessor_id = topic_transaction_id(initial)
                successor_id = predecessor_id[:-8] + "-a000001"
                event_loss = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix="/event.json",
                    ),
                    **args,
                )
                self.assert_envelope(event_loss, ok=False, op="index.create_topic")
                successor_event = (
                    fixture.instance
                    / topic_transaction_root(fixture, successor_id).removeprefix(
                        "vault://atlas/"
                    )
                    / "event.json"
                )
                if corruption == "corrupted":
                    successor_event.write_bytes(b"corrupt event\n")
                elif corruption == "different":
                    value = json.loads(successor_event.read_bytes().decode("utf-8"))
                    changed_request = dict(value["event_record"]["request"])
                    changed_request["created_on"] = "2026-08-03"
                    value["event_record"]["request"] = changed_request
                    value["event_record"]["request_sha256"] = atlas_index.sha256(
                        atlas_index.canonical_json(changed_request)
                    )
                    successor_event.write_bytes(atlas_transaction.canonical_json(value))
                else:
                    fixture.put(
                        f"{topic_transaction_root(fixture, successor_id)}/backups/000000.json",
                        "later record\n",
                    )
                before_revisions = {
                    path: self.revision(fixture, path)
                    for path in (
                        TOPIC_CREATE_URI,
                        TOPIC_SUBDOMAIN_URI,
                        TOPICS_URI,
                    )
                }
                rejected = invoke(fixture, "index.create_topic", **args)
                self.assert_envelope(rejected, ok=False, op="index.create_topic")
                self.assertEqual(
                    response_findings(rejected)[0][0],
                    "TRANSACTION_RECORD_INVALID",
                )
                self.assertEqual(
                    {path: self.revision(fixture, path) for path in before_revisions},
                    before_revisions,
                )
                self.assertEqual(
                    {
                        Path(path).parent.name
                        for path in fixture.connector().list(
                            "vault://atlas/.atlas/transactions"
                        )
                        if path.endswith("/event.json")
                    },
                    {predecessor_id, successor_id},
                )

    def test_index_recovery_rejects_nonprefix_progress_before_live_targets(
        self,
    ) -> None:
        for corruption in ("gap", "applied-incomplete"):
            with self.subTest(corruption=corruption), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                suffix = (
                    "/progress/000002.json"
                    if corruption == "gap"
                    else "/progress/000001.json"
                )
                with self.assertRaises(SystemExit):
                    invoke(
                        fixture,
                        "index.create_topic",
                        connector=AfterWriteFailureConnector(
                            fixture.connector(),
                            suffix=suffix,
                            stop_process=True,
                        ),
                        **args,
                    )
                transaction_id = topic_event_transaction_id(fixture)
                transaction_root = fixture.instance / topic_transaction_root(
                    fixture, transaction_id
                ).removeprefix("vault://atlas/")
                if corruption == "gap":
                    (transaction_root / "progress" / "000001.json").unlink()
                else:
                    intent = (transaction_root / "intent.json").read_bytes()
                    intent_hash = atlas_transaction.sha256(intent)
                    fixture.put(
                        f"{topic_transaction_root(fixture, transaction_id)}/applied.json",
                        atlas_transaction.canonical_json(
                            {
                                "version": 1,
                                "status": "applied",
                                "intent_sha256": intent_hash,
                            }
                        ).decode("utf-8"),
                    )
                connector = RecordingTopicConnector(fixture.connector())
                before_revisions = {
                    path: self.revision(fixture, path)
                    for path in (
                        TOPIC_CREATE_URI,
                        TOPIC_SUBDOMAIN_URI,
                        TOPICS_URI,
                    )
                }
                rejected = invoke(
                    fixture,
                    "index.recover_topic",
                    connector=connector,
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                self.assert_envelope(rejected, ok=False, op="index.recover_topic")
                finding = response_findings(rejected)[0]
                self.assertEqual(finding[0], "TRANSACTION_RECORD_INVALID")
                self.assertEqual(
                    finding[1],
                    topic_transaction_root(fixture, transaction_id)
                    + "/progress/000002.json",
                )
                self.assertEqual(connector.writes, [])
                self.assertEqual(connector.deletes, [])
                self.assertEqual(
                    {path: self.revision(fixture, path) for path in before_revisions},
                    before_revisions,
                )
                for path in (
                    TOPIC_CREATE_URI,
                    TOPIC_SUBDOMAIN_URI,
                    TOPICS_URI,
                ):
                    self.assertNotIn(path, connector.reads)

    def test_index_recovery_valid_existing_successor_is_terminal_ineligible(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            interrupted = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix=TOPIC_CREATE_URI,
                ),
                **args,
            )
            self.assert_envelope(interrupted, ok=False, op="index.create_topic")
            predecessor_id = topic_transaction_id(interrupted)
            recovered = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=predecessor_id,
                request=args,
            )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "rolled-back")
            successor = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix="/event.json",
                ),
                **args,
            )
            self.assert_envelope(successor, ok=False, op="index.create_topic")
            self.assertEqual(response_findings(successor)[0][0], "IO_FAILURE")
            connector = RecordingTopicConnector(fixture.connector())
            exhausted = invoke(
                fixture,
                "index.recover_topic",
                connector=connector,
                version=1,
                transaction_id=predecessor_id,
                request=args,
            )
            self.assert_envelope(exhausted, ok=True, op="index.recover_topic")
            self.assertEqual(exhausted["result"]["status"], "rolled-back")
            self.assertFalse(exhausted["result"]["successor_eligible"])
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])
            for path in (
                TOPIC_CREATE_URI,
                TOPIC_SUBDOMAIN_URI,
                TOPICS_URI,
            ):
                self.assertNotIn(path, connector.reads)

    def test_index_recovery_rejects_malformed_existing_successor_before_targets(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            interrupted = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix=TOPIC_CREATE_URI,
                ),
                **args,
            )
            self.assert_envelope(interrupted, ok=False, op="index.create_topic")
            predecessor_id = topic_transaction_id(interrupted)
            recovered = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=predecessor_id,
                request=args,
            )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "rolled-back")
            successor = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix="/event.json",
                ),
                **args,
            )
            self.assert_envelope(successor, ok=False, op="index.create_topic")
            self.assertEqual(response_findings(successor)[0][0], "IO_FAILURE")
            successor_id = predecessor_id[:-8] + "-a000001"
            successor_event = (
                fixture.instance
                / topic_transaction_root(fixture, successor_id).removeprefix(
                    "vault://atlas/"
                )
                / "event.json"
            )
            successor_event.write_bytes(b"malformed successor\n")
            connector = RecordingTopicConnector(fixture.connector())
            rejected = invoke(
                fixture,
                "index.recover_topic",
                connector=connector,
                version=1,
                transaction_id=predecessor_id,
                request=args,
            )
            self.assert_envelope(rejected, ok=False, op="index.recover_topic")
            self.assertEqual(
                response_findings(rejected)[0][0],
                "TRANSACTION_RECORD_INVALID",
            )
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])
            for path in (
                TOPIC_CREATE_URI,
                TOPIC_SUBDOMAIN_URI,
                TOPICS_URI,
            ):
                self.assertNotIn(path, connector.reads)

    def test_index_recovery_probe_faults_keep_identity_for_exact_retry(self) -> None:
        for stage in ("verification", "successor", "classification"):
            with self.subTest(stage=stage), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                with self.assertRaises(SystemExit):
                    invoke(
                        fixture,
                        "index.create_topic",
                        connector=AfterWriteFailureConnector(
                            fixture.connector(),
                            suffix=TOPIC_SUBDOMAIN_URI,
                            stop_process=True,
                        ),
                        **args,
                    )
                transaction_id = topic_event_transaction_id(fixture)
                if stage == "verification":
                    suffix = "/intent.json"
                elif stage == "successor":
                    suffix = f"/{transaction_id[:-8]}-a000001/event.json"
                else:
                    suffix = TOPIC_CREATE_URI
                interrupted = invoke(
                    fixture,
                    "index.recover_topic",
                    connector=RecoveryFaultConnector(
                        fixture.connector(),
                        suffix=suffix,
                        operation="read_bytes",
                        error="oserror",
                    ),
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                self.assert_envelope(interrupted, ok=False, op="index.recover_topic")
                finding = response_findings(interrupted)[0]
                if stage == "verification":
                    self.assertEqual(finding[0], "IO_FAILURE")
                    self.assertEqual(finding[1], "index.recover_topic")
                    continue
                self.assertEqual(finding[0], "TRANSACTION_RECOVERABLE")
                self.assertEqual(
                    finding[1],
                    topic_transaction_root(fixture, transaction_id) + "/intent.json",
                )
                self.assertEqual(
                    finding[2],
                    f"transaction {transaction_id} requires exact-request recovery",
                )
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                self.assert_envelope(recovered, ok=True, op="index.recover_topic")
                self.assertEqual(recovered["result"]["status"], "rolled-back")
                self.assertTrue(recovered["result"]["successor_eligible"])

    def test_index_attempt_one_predecessor_probe_faults_keep_current_identity(
        self,
    ) -> None:
        fault_cases = (
            ("event", "read_bytes", "event.json"),
            ("intent", "read_bytes", "intent.json"),
            ("list", "list", ""),
            ("terminal", "read_bytes", "rolled-back.json"),
        )
        for label, operation, suffix_name in fault_cases:
            with self.subTest(probe=label), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                initial = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_SUBDOMAIN_URI,
                    ),
                    **args,
                )
                self.assert_envelope(initial, ok=False, op="index.create_topic")
                predecessor_id = topic_transaction_id(initial)
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=predecessor_id,
                    request=args,
                )
                self.assert_envelope(recovered, ok=True, op="index.recover_topic")
                self.assertEqual(recovered["result"]["status"], "rolled-back")
                attempt_one = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_CREATE_URI,
                    ),
                    **args,
                )
                self.assert_envelope(attempt_one, ok=False, op="index.create_topic")
                current_id = topic_transaction_id(attempt_one)
                predecessor_id = current_id[:-8] + "-a000000"
                suffix = (
                    f"/{predecessor_id}/{suffix_name}"
                    if suffix_name
                    else f"/{predecessor_id}"
                )
                connector = RecordingTopicConnector(
                    RecoveryFaultConnector(
                        fixture.connector(),
                        suffix=suffix,
                        operation=operation,
                        error="oserror",
                    )
                )
                interrupted = invoke(
                    fixture,
                    "index.recover_topic",
                    connector=connector,
                    version=1,
                    transaction_id=current_id,
                    request=args,
                )
                self.assert_envelope(interrupted, ok=False, op="index.recover_topic")
                finding = response_findings(interrupted)[0]
                self.assertEqual(finding[0], "TRANSACTION_RECOVERABLE")
                self.assertEqual(
                    finding[1],
                    topic_transaction_root(fixture, current_id) + "/intent.json",
                )
                self.assertEqual(
                    finding[2],
                    f"transaction {current_id} requires exact-request recovery",
                )
                self.assertEqual(connector.writes, [])
                self.assertEqual(connector.deletes, [])
                self.assertNotIn(TOPIC_CREATE_URI, connector.reads)
                self.assertNotIn(TOPIC_SUBDOMAIN_URI, connector.reads)
                self.assertNotIn(TOPICS_URI, connector.reads)

    def test_index_recovery_current_intent_boundary_is_io_or_record_invalid(
        self,
    ) -> None:
        for state in ("unreadable", "missing", "malformed"):
            with self.subTest(state=state), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                initial = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_SUBDOMAIN_URI,
                    ),
                    **args,
                )
                self.assert_envelope(initial, ok=False, op="index.create_topic")
                transaction_id = topic_transaction_id(initial)
                intent = (
                    fixture.instance
                    / topic_transaction_root(fixture, transaction_id).removeprefix(
                        "vault://atlas/"
                    )
                    / "intent.json"
                )
                if state == "missing":
                    intent.unlink()
                    connector: Any = fixture.connector()
                elif state == "malformed":
                    intent.write_bytes(b"malformed intent\n")
                    connector = fixture.connector()
                else:
                    connector = RecoveryFaultConnector(
                        fixture.connector(),
                        suffix=f"/{transaction_id}/intent.json",
                        operation="read_bytes",
                        error="oserror",
                    )
                recording = RecordingTopicConnector(connector)
                response = invoke(
                    fixture,
                    "index.recover_topic",
                    connector=recording,
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                self.assert_envelope(response, ok=False, op="index.recover_topic")
                finding = response_findings(response)[0]
                self.assertEqual(
                    finding[0],
                    "IO_FAILURE"
                    if state == "unreadable"
                    else "TRANSACTION_RECORD_INVALID",
                )
                self.assertEqual(recording.writes, [])
                self.assertEqual(recording.deletes, [])
                self.assertNotIn(TOPIC_CREATE_URI, recording.reads)
                self.assertNotIn(TOPIC_SUBDOMAIN_URI, recording.reads)
                self.assertNotIn(TOPICS_URI, recording.reads)

    def test_index_recovery_rejects_hash_consistent_invalid_embedded_requests(
        self,
    ) -> None:
        invalid_requests = (
            ("status", "bogus"),
            ("created_on", "2026-99-99"),
            ("include_terms", ["z", "test"]),
            ("canonical_title", "New topic "),
            ("topic_path", TOPIC_CREATE_URI + "?invalid"),
        )
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            created = invoke(fixture, "index.create_topic", **args)
            self.assert_envelope(created, ok=True, op="index.create_topic")
            original_id = created["result"]["receipt"]["transaction_id"]
            original_event_path = (
                fixture.instance
                / topic_transaction_root(fixture, original_id).removeprefix(
                    "vault://atlas/"
                )
                / "event.json"
            )
            original_event = json.loads(original_event_path.read_bytes())
            targets = tuple(
                atlas_transaction.TransactionTarget(
                    row["path"],
                    (
                        None
                        if row["input_base64"] is None
                        else base64.b64decode(row["input_base64"], validate=True)
                    ),
                    base64.b64decode(row["output_base64"], validate=True),
                )
                for row in original_event["targets"]
            )
            for field, invalid in invalid_requests:
                with self.subTest(field=field):
                    invalid_request = dict(args)
                    invalid_request[field] = invalid
                    event_record = dict(original_event["event_record"])
                    event_record["request"] = invalid_request
                    event_record["request_sha256"] = atlas_index.sha256(
                        atlas_index.canonical_json(invalid_request)
                    )
                    plan = atlas_tool._index_plan(
                        event_record,
                        targets,
                        original_event["attempt"],
                        original_event["predecessor_sha256"],
                    )
                    event_bytes = atlas_transaction.canonical_json(
                        atlas_transaction.event_record_value(event_record, plan)
                    )
                    fixture.put(
                        f"vault://atlas/{plan.transaction_root}/{plan.transaction_id}/event.json",
                        event_bytes.decode("utf-8"),
                    )
                    connector = RecordingTopicConnector(fixture.connector())
                    rejected = invoke(
                        fixture,
                        "index.recover_topic",
                        connector=connector,
                        version=1,
                        transaction_id=plan.transaction_id,
                        request=invalid_request,
                    )
                    self.assert_envelope(rejected, ok=False, op="index.recover_topic")
                    self.assertEqual(
                        response_findings(rejected)[0][0],
                        "TRANSACTION_RECORD_INVALID",
                    )
                    self.assertEqual(connector.writes, [])
                    self.assertEqual(connector.deletes, [])
                    self.assertNotIn(TOPIC_CREATE_URI, connector.reads)
                    self.assertNotIn(TOPIC_SUBDOMAIN_URI, connector.reads)
                    self.assertNotIn(TOPICS_URI, connector.reads)

    def test_index_recovery_rejects_related_semantics_before_live_targets(
        self,
    ) -> None:
        cases = (
            ("self", ["new-topic"], None),
            ("unknown", ["missing-topic"], None),
            ("canonical-path", ["test-topic"], "wrong-topic"),
        )
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            created = invoke(fixture, "index.create_topic", **args)
            self.assert_envelope(created, ok=True, op="index.create_topic")
            original_id = created["result"]["receipt"]["transaction_id"]
            original_event = json.loads(
                (
                    fixture.instance
                    / topic_transaction_root(fixture, original_id).removeprefix(
                        "vault://atlas/"
                    )
                    / "event.json"
                ).read_bytes()
            )
            original_targets = tuple(
                atlas_transaction.TransactionTarget(
                    row["path"],
                    (
                        None
                        if row["input_base64"] is None
                        else base64.b64decode(row["input_base64"], validate=True)
                    ),
                    base64.b64decode(row["output_base64"], validate=True),
                )
                for row in original_event["targets"]
            )
            for label, related_ids, mismatched_topic in cases:
                with self.subTest(case=label):
                    invalid_request = dict(args)
                    invalid_request["related_topic_ids"] = related_ids
                    targets = original_targets
                    if mismatched_topic is not None:
                        topics_input = targets[2].input_bytes
                        assert topics_input is not None
                        mismatched_topics = topics_input.replace(
                            b"summaries/research/test/test-subdomain/topics/"
                            b"test-topic/INDEX.md",
                            (
                                b"summaries/research/test/test-subdomain/topics/"
                                + mismatched_topic.encode("utf-8")
                                + b"/INDEX.md"
                            ),
                        )
                        targets = (
                            targets[0],
                            targets[1],
                            atlas_transaction.TransactionTarget(
                                targets[2].path,
                                mismatched_topics,
                                targets[2].output_bytes,
                            ),
                        )
                    transaction_id = write_topic_transaction_records(
                        fixture,
                        invalid_request,
                        targets,
                    )
                    transaction_root = fixture.instance / topic_transaction_root(
                        fixture, transaction_id
                    ).removeprefix("vault://atlas/")
                    for name in (
                        "event.json",
                        "intent.json",
                        "prepared.json",
                        "applied.json",
                    ):
                        self.assertTrue((transaction_root / name).exists())
                    connector = RecordingTopicConnector(fixture.connector())
                    rejected = invoke(
                        fixture,
                        "index.recover_topic",
                        connector=connector,
                        version=1,
                        transaction_id=transaction_id,
                        request=invalid_request,
                    )
                    self.assert_envelope(rejected, ok=False, op="index.recover_topic")
                    finding = response_findings(rejected)[0]
                    self.assertEqual(finding[0], "TRANSACTION_RECORD_INVALID")
                    self.assertTrue(
                        finding[1].startswith(
                            "vault://atlas/.atlas/transactions/topics/"
                        )
                        and finding[1].endswith("/event.json")
                    )
                    self.assertEqual(atlas_tool._exit(rejected), 2)
                    self.assertEqual(connector.writes, [])
                    self.assertEqual(connector.deletes, [])
                    self.assertNotIn(TOPIC_CREATE_URI, connector.reads)
                    self.assertNotIn(TOPIC_SUBDOMAIN_URI, connector.reads)
                    self.assertNotIn(TOPICS_URI, connector.reads)

    def test_index_recovery_rejects_existing_topic_input_before_target_access(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()

            def write_bytes(uri: str, value: bytes) -> None:
                destination = fixture.instance / uri.removeprefix("vault://atlas/")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(value)

            existing_topic = b"existing topic\n"
            write_bytes(TOPIC_CREATE_URI, existing_topic)
            subdomain_input = (
                fixture.instance / TOPIC_SUBDOMAIN_URI.removeprefix("vault://atlas/")
            ).read_bytes()
            topics_input = (
                fixture.instance / TOPICS_URI.removeprefix("vault://atlas/")
            ).read_bytes()

            def relative(uri: str) -> str:
                return uri.removeprefix("vault://atlas/")

            targets = (
                atlas_transaction.TransactionTarget(
                    relative(TOPIC_CREATE_URI),
                    existing_topic,
                    b"replacement topic\n",
                ),
                atlas_transaction.TransactionTarget(
                    relative(TOPIC_SUBDOMAIN_URI),
                    subdomain_input,
                    b"replacement subdomain\n",
                ),
                atlas_transaction.TransactionTarget(
                    relative(TOPICS_URI),
                    topics_input,
                    b"replacement topics\n",
                ),
            )
            transaction_id = write_topic_transaction_records(
                fixture,
                args,
                targets,
                status="rolled-back",
            )
            connector = RecordingTopicConnector(fixture.connector())
            rejected = invoke(
                fixture,
                "index.recover_topic",
                connector=connector,
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(rejected, ok=False, op="index.recover_topic")
            finding = response_findings(rejected)[0]
            self.assertEqual(finding[0], "TRANSACTION_RECORD_INVALID")
            self.assertEqual(
                finding[1],
                topic_transaction_root(fixture, transaction_id) + "/event.json",
            )
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])
            self.assertNotIn(TOPIC_CREATE_URI, connector.reads)
            self.assertNotIn(TOPIC_SUBDOMAIN_URI, connector.reads)
            self.assertNotIn(TOPICS_URI, connector.reads)

    def test_index_recovery_honors_existing_applied_owner_proof(self) -> None:
        for output_case in ("invalid-utf8", "invalid-structure"):
            with self.subTest(output_case=output_case), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                _, owner_result = atlas_tool._index_prepare(
                    fixture.connector(),
                    args,
                )
                self.assertIsInstance(owner_result, atlas_index.TopicPlan)
                assert isinstance(owner_result, atlas_index.TopicPlan)
                outputs = [target.output_bytes for target in owner_result.targets]
                outputs[0] = (
                    b"\xff\xfe"
                    if output_case == "invalid-utf8"
                    else b"not a topic index\n"
                )

                def write_bytes(uri: str, value: bytes) -> None:
                    destination = fixture.instance / uri.removeprefix("vault://atlas/")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(value)

                targets = tuple(
                    atlas_transaction.TransactionTarget(
                        target.path.removeprefix("vault://atlas/"),
                        target.input_bytes,
                        outputs[index],
                    )
                    for index, target in enumerate(owner_result.targets)
                )
                for target in targets:
                    write_bytes(f"vault://atlas/{target.path}", target.output_bytes)
                transaction_id = write_topic_transaction_records(
                    fixture,
                    args,
                    targets,
                    status="applied",
                )
                connector = RecordingTopicConnector(fixture.connector())
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    connector=connector,
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                self.assert_envelope(recovered, ok=True, op="index.recover_topic")
                self.assertEqual(recovered["result"]["status"], "applied")
                self.assertEqual(
                    recovered["result"]["validation"],
                    {"ok": True, "findings": []},
                )
                self.assertEqual(connector.writes, [])
                self.assertEqual(connector.deletes, [])
                for target in targets:
                    self.assertNotIn(
                        f"vault://atlas/{target.path}",
                        connector.reads,
                    )
                for target in targets:
                    self.assertEqual(
                        (fixture.instance / target.path).read_bytes(),
                        target.output_bytes,
                    )

        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            _, owner_result = atlas_tool._index_prepare(
                fixture.connector(),
                args,
            )
            self.assertIsInstance(owner_result, atlas_index.TopicPlan)
            assert isinstance(owner_result, atlas_index.TopicPlan)

            def write_bytes(uri: str, value: bytes) -> None:
                destination = fixture.instance / uri.removeprefix("vault://atlas/")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(value)

            targets = tuple(
                atlas_transaction.TransactionTarget(
                    target.path.removeprefix("vault://atlas/"),
                    target.input_bytes,
                    target.output_bytes,
                )
                for target in owner_result.targets
            )
            for target in targets:
                write_bytes(f"vault://atlas/{target.path}", target.output_bytes)
            transaction_id = write_topic_transaction_records(
                fixture,
                args,
                targets,
                status="applied",
            )
            recovered = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "applied")
            self.assertEqual(
                recovered["result"]["validation"],
                {"ok": True, "findings": []},
            )

            faulted_connector = RecordingTopicConnector(
                RecoveryFaultConnector(
                    fixture.connector(),
                    suffix=MANIFEST_URI,
                    operation="read_bytes",
                    error="oserror",
                )
            )
            faulted = invoke(
                fixture,
                "index.recover_topic",
                connector=faulted_connector,
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(faulted, ok=True, op="index.recover_topic")
            self.assertEqual(faulted["result"]["status"], "applied")
            self.assertEqual(
                faulted["result"]["validation"],
                {"ok": True, "findings": []},
            )
            self.assertEqual(faulted_connector.writes, [])
            self.assertEqual(faulted_connector.deletes, [])
            self.assertNotIn(MANIFEST_URI, faulted_connector.reads)
            transaction_fault_connector = RecordingTopicConnector(
                RecoveryFaultConnector(
                    fixture.connector(),
                    suffix=MANIFEST_URI,
                    operation="read_bytes",
                    error="transaction",
                )
            )
            transaction_faulted = invoke(
                fixture,
                "index.recover_topic",
                connector=transaction_fault_connector,
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(
                transaction_faulted,
                ok=True,
                op="index.recover_topic",
            )
            self.assertEqual(transaction_faulted["result"]["status"], "applied")
            self.assertEqual(
                transaction_faulted["result"]["validation"],
                {"ok": True, "findings": []},
            )
            self.assertEqual(transaction_fault_connector.writes, [])
            self.assertEqual(transaction_fault_connector.deletes, [])
            self.assertNotIn(MANIFEST_URI, transaction_fault_connector.reads)

    def test_index_recovery_connector_value_error_is_binding_invalid(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            with self.assertRaises(SystemExit):
                invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_SUBDOMAIN_URI,
                        stop_process=True,
                    ),
                    **args,
                )
            transaction_id = topic_event_transaction_id(fixture)
            transaction_root = fixture.instance / topic_transaction_root(
                fixture, transaction_id
            ).removeprefix("vault://atlas/")
            before = {
                path.relative_to(transaction_root): path.read_bytes()
                for path in transaction_root.rglob("*.json")
            }

            connector = RecordingTopicConnector(
                ClassificationValueErrorConnector(
                    fixture.connector(),
                    path=TOPIC_CREATE_URI,
                )
            )
            recovered = invoke(
                fixture,
                "index.recover_topic",
                connector=connector,
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(recovered, ok=False, op="index.recover_topic")
            finding = response_findings(recovered)[0]
            self.assertEqual(finding[0], "BINDING_INVALID")
            self.assertEqual(finding[1], "connector")
            self.assertEqual(atlas_tool._exit(recovered), 3)
            self.assertIn(TOPIC_CREATE_URI, connector.reads)
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])
            after = {
                path.relative_to(transaction_root): path.read_bytes()
                for path in transaction_root.rglob("*.json")
            }
            self.assertEqual(before, after)

    def test_index_immutable_record_value_errors_are_record_invalid_before_targets(
        self,
    ) -> None:
        for stage in (
            "event.json",
            "intent.json",
            "backups/000000.json",
            "prepared.json",
            "progress/000000.json",
            "rolled-back.json",
        ):
            with self.subTest(stage=stage), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                interrupted = invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_SUBDOMAIN_URI,
                    ),
                    **args,
                )
                self.assert_envelope(
                    interrupted,
                    ok=False,
                    op="index.create_topic",
                )
                transaction_id = topic_transaction_id(interrupted)
                record_path = (
                    f"{topic_transaction_root(fixture, transaction_id)}/{stage}"
                )
                connector = RecordingTopicConnector(
                    ClassificationValueErrorConnector(
                        fixture.connector(),
                        path=record_path,
                    )
                )
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    connector=connector,
                    version=1,
                    transaction_id=transaction_id,
                    request=args,
                )
                self.assert_envelope(
                    recovered,
                    ok=False,
                    op="index.recover_topic",
                )
                finding = response_findings(recovered)[0]
                self.assertEqual(finding[0], "TRANSACTION_RECORD_INVALID")
                self.assertEqual(finding[1], record_path)
                self.assertEqual(connector.writes, [])
                self.assertEqual(connector.deletes, [])
                self.assertNotIn(TOPIC_CREATE_URI, connector.reads)
                self.assertNotIn(TOPIC_SUBDOMAIN_URI, connector.reads)
                self.assertNotIn(TOPICS_URI, connector.reads)

    def test_index_rollback_drift_is_manual_conflict_without_overwrite(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            with self.assertRaises(SystemExit):
                invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_SUBDOMAIN_URI,
                        stop_process=True,
                    ),
                    **args,
                )
            topic_before = self.read_text(fixture, TOPIC_CREATE_URI)
            transaction_id = topic_event_transaction_id(fixture)
            connector = RecordingTopicConnector(
                DriftingConnector(
                    fixture.connector(),
                    path=TOPIC_SUBDOMAIN_URI,
                )
            )
            recovered = invoke(
                fixture,
                "index.recover_topic",
                connector=connector,
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(
                recovered,
                ok=False,
                op="index.recover_topic",
            )
            finding = response_findings(recovered)[0]
            self.assertEqual(finding[0], "MANUAL_CONFLICT")
            self.assertEqual(finding[1], TOPIC_SUBDOMAIN_URI)
            self.assertEqual(
                self.read_text(fixture, TOPIC_SUBDOMAIN_URI),
                "manual conflict\n",
            )
            self.assertEqual(self.read_text(fixture, TOPIC_CREATE_URI), topic_before)
            self.assertEqual(connector.deletes, [])

    def test_index_preflight_read_oserror_is_io_failure_without_transaction_write(
        self,
    ) -> None:
        for uri in (
            MANIFEST_URI,
            TOPICS_URI,
            TOPIC_SUBDOMAIN_URI,
            TOPIC_CREATE_URI,
        ):
            with self.subTest(uri=uri), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                connector = RecordingTopicConnector(
                    RecoveryFaultConnector(
                        fixture.connector(),
                        suffix=uri,
                        operation="read_bytes",
                        error="oserror",
                    )
                )
                response = invoke(
                    fixture,
                    "index.create_topic",
                    connector=connector,
                    **topic_create_args(),
                )
                self.assert_envelope(response, ok=False, op="index.create_topic")
                finding = response_findings(response)[0]
                self.assertEqual(finding[0], "IO_FAILURE")
                self.assertEqual(finding[1], "index.create_topic")
                self.assertEqual(connector.writes, [])
                self.assertFalse(
                    (fixture.instance / ".atlas" / "transactions").exists()
                )

    def test_index_faults_recover_and_exact_replay_only_one_successor(self) -> None:
        for path in (TOPIC_CREATE_URI, TOPIC_SUBDOMAIN_URI, TOPICS_URI):
            with self.subTest(path=path), temporary_profile() as fixture:
                self.prepare_topic_fixture(fixture)
                args = topic_create_args()
                before_subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
                before_topics = self.read_text(fixture, TOPICS_URI)
                interrupted = invoke(
                    fixture,
                    "index.create_topic",
                    connector=InterruptingConnector(
                        fixture.connector(),
                        path=path,
                        after_write=True,
                    ),
                    **args,
                )
                self.assert_envelope(interrupted, ok=False, op="index.create_topic")
                self.assertEqual(
                    response_findings(interrupted)[0][0],
                    "TRANSACTION_RECOVERABLE",
                )
                txid = topic_transaction_id(interrupted)
                recovered = invoke(
                    fixture,
                    "index.recover_topic",
                    version=1,
                    transaction_id=txid,
                    request=args,
                )
                self.assert_envelope(recovered, ok=True, op="index.recover_topic")
                expected_status = "applied" if path == TOPICS_URI else "rolled-back"
                self.assertEqual(recovered["result"]["status"], expected_status)
                self.assertEqual(
                    recovered["result"]["successor_eligible"],
                    expected_status == "rolled-back",
                )
                if expected_status == "rolled-back":
                    self.assertEqual(
                        self.read_text(fixture, TOPIC_SUBDOMAIN_URI),
                        before_subdomain,
                    )
                    self.assertEqual(self.read_text(fixture, TOPICS_URI), before_topics)
                    self.assertEqual(
                        self.revision(fixture, TOPIC_CREATE_URI),
                        "missing",
                    )
                    replay = invoke(
                        fixture,
                        "index.create_topic",
                        **args,
                    )
                    self.assert_envelope(replay, ok=True, op="index.create_topic")
                    self.assertEqual(replay["result"]["receipt"]["attempt"], 1)
                    second = invoke(
                        fixture,
                        "index.recover_topic",
                        version=1,
                        transaction_id=txid,
                        request=args,
                    )
                    self.assert_envelope(second, ok=True, op="index.recover_topic")
                    self.assertEqual(second["result"]["status"], "rolled-back")
                    self.assertFalse(second["result"]["successor_eligible"])
                    self.assertEqual(
                        second["result"]["receipt"]["transaction_id"],
                        txid,
                    )
                else:
                    self.assertFalse(recovered["result"]["successor_eligible"])
                    confirmed = invoke(
                        fixture,
                        "index.create_topic",
                        **args,
                    )
                    self.assert_envelope(confirmed, ok=True, op="index.create_topic")
                    self.assertEqual(confirmed["result"]["state"], "confirmed")

    def test_index_namespace_closure_blocks_fresh_and_selected_changed_request_lineages(
        self,
    ) -> None:
        def roll_back_initial(fixture: TemporaryAtlasProfile) -> dict[str, Any]:
            args = topic_create_args()
            interrupted = invoke(
                fixture,
                "index.create_topic",
                connector=AfterWriteFailureConnector(
                    fixture.connector(),
                    suffix=TOPIC_SUBDOMAIN_URI,
                ),
                **args,
            )
            self.assert_envelope(interrupted, ok=False, op="index.create_topic")
            transaction_id = topic_transaction_id(interrupted)
            recovered = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(recovered, ok=True, op="index.recover_topic")
            self.assertEqual(recovered["result"]["status"], "rolled-back")
            self.assertTrue(recovered["result"]["successor_eligible"])
            return args

        namespace_uri = (
            "vault://atlas/"
            f"{atlas_tool.TRANSACTION_ROOT}/topics/"
            f"{atlas_index.topic_namespace_sha256(topic_create_args())}"
        )

        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = roll_back_initial(fixture)
            changed = dict(args)
            changed["created_on"] = "2026-08-03"
            connector = RecordingTopicConnector(fixture.connector())
            blocked = invoke(
                fixture,
                "index.create_topic",
                connector=connector,
                **changed,
            )
            self.assert_envelope(blocked, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(blocked)[0],
                (
                    "TRANSACTION_RECOVERABLE",
                    namespace_uri,
                    "topic transaction namespace is not closed",
                ),
            )
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])
            self.assertEqual(
                len(
                    [
                        path
                        for path in fixture.connector().list(
                            "vault://atlas/.atlas/transactions/topics"
                        )
                        if path.endswith("/event.json")
                    ]
                ),
                1,
            )

        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = roll_back_initial(fixture)
            original_subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
            fixture.put(
                TOPIC_SUBDOMAIN_URI,
                original_subdomain.replace(
                    'last_updated: "2026-07-28"',
                    'last_updated: "2026-07-29"',
                ),
            )
            changed = dict(args)
            changed["created_on"] = "2026-08-03"

            class PreIntentFailureConnector:
                def __init__(self, inner: Any) -> None:
                    self._inner = inner
                    self._failed = False

                def __getattr__(self, name: str) -> Any:
                    return getattr(self._inner, name)

                def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
                    path = str(args[0] if args else kwargs["path"])
                    if not self._failed and path.endswith("/intent.json"):
                        self._failed = True
                        raise OSError("synthetic pre-intent failure")
                    return self._inner.conditional_replace(*args, **kwargs)

            interrupted = invoke(
                fixture,
                "index.create_topic",
                connector=PreIntentFailureConnector(fixture.connector()),
                **changed,
            )
            self.assert_envelope(interrupted, ok=False, op="index.create_topic")
            self.assertEqual(response_findings(interrupted)[0][0], "IO_FAILURE")
            self.assertEqual(
                len(
                    [
                        path
                        for path in fixture.connector().list(
                            "vault://atlas/.atlas/transactions/topics"
                        )
                        if path.endswith("/event.json")
                    ]
                ),
                2,
            )

            fixture.put(TOPIC_SUBDOMAIN_URI, original_subdomain)
            connector = RecordingTopicConnector(fixture.connector())
            blocked = invoke(
                fixture,
                "index.create_topic",
                connector=connector,
                **args,
            )
            self.assert_envelope(blocked, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(blocked)[0],
                (
                    "TRANSACTION_RECOVERABLE",
                    namespace_uri,
                    "topic transaction namespace is not closed",
                ),
            )
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])

    def test_index_replay_changed_binding_allocates_fresh_base(self) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            with self.assertRaises(SystemExit):
                invoke(
                    fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        fixture.connector(),
                        suffix=TOPIC_SUBDOMAIN_URI,
                        stop_process=True,
                    ),
                    **args,
                )
            transaction_id = topic_event_transaction_id(fixture)
            recovered = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=transaction_id,
                request=args,
            )
            self.assert_envelope(
                recovered,
                ok=True,
                op="index.recover_topic",
            )
            self.assertEqual(recovered["result"]["status"], "rolled-back")
            before = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
            fixture.put(
                TOPIC_SUBDOMAIN_URI,
                before.replace(
                    'last_updated: "2026-07-28"',
                    'last_updated: "2026-07-29"',
                ),
            )
            replay = invoke(
                fixture,
                "index.create_topic",
                **args,
            )
            self.assert_envelope(replay, ok=True, op="index.create_topic")
            self.assertEqual(replay["result"]["state"], "created")
            self.assertNotEqual(
                replay["result"]["receipt"]["transaction_id"],
                transaction_id,
            )
            self.assertEqual(replay["result"]["receipt"]["attempt"], 0)
            self.assertEqual(
                [item["path"] for item in replay["result"]["receipt"]["targets"]],
                [TOPIC_CREATE_URI, TOPIC_SUBDOMAIN_URI, TOPICS_URI],
            )
            self.assertNotEqual(
                self.revision(fixture, TOPIC_CREATE_URI),
                "missing",
            )
            topic = self.read_text(fixture, TOPIC_CREATE_URI)
            self.assertIn('topic: "new-topic"', topic)
            self.assertIn("# New topic", topic)
            subdomain = self.read_text(fixture, TOPIC_SUBDOMAIN_URI)
            self.assertIn('last_updated: "2026-08-02"', subdomain)
            self.assertIn(
                "| New topic | Research required | Insufficient | Current | "
                "2026-08-02 | "
                "summaries/research/test/test-subdomain/topics/new-topic/INDEX.md |",
                subdomain,
            )
            self.assertIn("- Insufficient: New topic", subdomain)
            self.assertIn(
                "- New topic — No evidence-backed answer exists; "
                "acquisition/research is required.",
                subdomain,
            )
            self.assertIn(
                "## Routing scope\n"
                "<!-- atlas:managed:start routing-scope -->\n"
                "- Domain: `test`\n"
                "- Subdomain: `test-subdomain`\n"
                "- Include: test\n"
                "- Exclude: none\n"
                "<!-- atlas:managed:end routing-scope -->",
                subdomain,
            )
            self.assertIn(
                "## Default lookup order\n"
                "<!-- atlas:managed:start default-lookup-order -->\n"
                "1. Check `vault://atlas/summaries/registry/TOPICS.md` "
                "for topic path and freshness.\n"
                "2. Read the topic `INDEX.md` when `Freshness state=current`.\n"
                "3. Read optional split files only when the topic `INDEX.md` "
                "points to them.\n"
                "<!-- atlas:managed:end default-lookup-order -->",
                subdomain,
            )
            self.assertIn(
                "## Acquisition watchlist\n"
                "<!-- atlas:managed:start acquisition-watchlist -->\n"
                "- feeds — check later\n"
                "<!-- atlas:managed:end acquisition-watchlist -->",
                subdomain,
            )
            topics = self.read_text(fixture, TOPICS_URI)
            self.assertIn(
                "| new-topic | "
                "summaries/research/test/test-subdomain/topics/new-topic/INDEX.md | "
                "test | test-subdomain | New topic |  |  | test |  | current | "
                "0 |  |  |  | 0 | same-as-topic-creation |",
                topics,
            )

            event_paths = [
                path
                for path in fixture.connector().list(
                    "vault://atlas/.atlas/transactions"
                )
                if path.endswith("/event.json")
            ]
            self.assertEqual(len(event_paths), 2)

    def test_index_recovery_rejects_request_mismatch_record_corruption_and_output_drift(
        self,
    ) -> None:
        with temporary_profile() as fixture:
            self.prepare_topic_fixture(fixture)
            args = topic_create_args()
            interrupted = invoke(
                fixture,
                "index.create_topic",
                connector=InterruptingConnector(
                    fixture.connector(),
                    path=TOPIC_SUBDOMAIN_URI,
                    after_write=True,
                ),
                **args,
            )
            self.assert_envelope(interrupted, ok=False, op="index.create_topic")
            self.assertEqual(
                response_findings(interrupted)[0][0],
                "TRANSACTION_RECOVERABLE",
            )
            txid = topic_transaction_id(interrupted)
            mismatch = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=txid,
                request=topic_create_args(created_on="2026-08-01"),
            )
            self.assert_envelope(mismatch, ok=False, op="index.recover_topic")
            self.assertEqual(
                response_findings(mismatch)[0][0],
                "MANUAL_CONFLICT",
            )
            transaction_root = fixture.instance / topic_transaction_root(
                fixture, txid
            ).removeprefix("vault://atlas/")
            backup = transaction_root / "backups" / "000001.json"
            self.assertTrue(backup.exists())
            backup_bytes = backup.read_bytes()
            backup.unlink()
            missing_backup = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=txid,
                request=args,
            )
            self.assert_envelope(
                missing_backup,
                ok=False,
                op="index.recover_topic",
            )
            self.assertFalse(missing_backup["ok"])
            self.assertEqual(
                response_findings(missing_backup)[0][0],
                "TRANSACTION_RECORD_INVALID",
            )
            backup.write_bytes(backup_bytes)
            backup.write_text("corrupt\n", encoding="utf-8")
            corrupted = invoke(
                fixture,
                "index.recover_topic",
                version=1,
                transaction_id=txid,
                request=args,
            )
            self.assert_envelope(
                corrupted,
                ok=False,
                op="index.recover_topic",
            )
            self.assertEqual(
                response_findings(corrupted)[0][0],
                "TRANSACTION_RECORD_INVALID",
            )
        with temporary_profile() as drift_fixture:
            self.prepare_topic_fixture(drift_fixture)
            drift_args = topic_create_args()
            with self.assertRaises(SystemExit):
                invoke(
                    drift_fixture,
                    "index.create_topic",
                    connector=AfterWriteFailureConnector(
                        drift_fixture.connector(),
                        suffix=TOPIC_SUBDOMAIN_URI,
                        stop_process=True,
                    ),
                    **drift_args,
                )
            drift_txid = topic_event_transaction_id(drift_fixture)
            drift_fixture.put(TOPIC_CREATE_URI, "output drift\n")
            drift_connector = RecordingTopicConnector(drift_fixture.connector())
            drift = invoke(
                drift_fixture,
                "index.recover_topic",
                connector=drift_connector,
                version=1,
                transaction_id=drift_txid,
                request=drift_args,
            )
            self.assert_envelope(drift, ok=False, op="index.recover_topic")
            self.assertEqual(response_findings(drift)[0][0], "MANUAL_CONFLICT")
            self.assertEqual(
                self.read_text(drift_fixture, TOPIC_CREATE_URI),
                "output drift\n",
            )
            drift_transaction_root = topic_transaction_root(drift_fixture, drift_txid)
            self.assertEqual(
                drift_connector.writes,
                [f"{drift_transaction_root}/manual-conflict.json"],
            )
            self.assertNotIn(TOPIC_CREATE_URI, drift_connector.writes)
            self.assertNotIn(TOPIC_SUBDOMAIN_URI, drift_connector.writes)
            self.assertNotIn(TOPICS_URI, drift_connector.writes)
            self.assertEqual(drift_connector.deletes, [])

    def test_migration_effect_matrix_preserves_ack_recovery_and_lineage(self) -> None:
        class EffectConnector:
            def __init__(self, inner: Any, mode: str) -> None:
                self.inner = inner
                self.mode = mode
                self.cas_paths: list[str] = []
                self._forwarded = False

            def __getattr__(self, name: str) -> Any:
                return getattr(self.inner, name)

            def read_bytes(self, uri: str) -> bytes:
                if self._forwarded:
                    if self.mode == "post-reread" and uri == MANIFEST_URI:
                        raise OSError("synthetic post-validation reread failure")
                    if self.mode == "post-topic-binding" and uri == TOPICS_URI:
                        raise atlas_connector.ConnectorBindingError(
                            "synthetic post-effect binding failure"
                        )
                return self.inner.read_bytes(uri)

            def _archive_manifest(self) -> None:
                current = self.inner.revision(MANIFEST_URI)
                archived = manifest_text(
                    [manifest_row(SOURCE_A_URL, 1, status="archived")]
                ).encode("utf-8")
                self.inner.conditional_replace(MANIFEST_URI, current, archived)

            def conditional_replace(self, *args: Any, **kwargs: Any) -> Any:
                path = str(args[0] if args else kwargs["path"])
                if path != TOPICS_URI:
                    return self.inner.conditional_replace(*args, **kwargs)
                self.cas_paths.append(path)
                ordinal = len(self.cas_paths)
                if ordinal == 1:
                    if self.mode == "conflict":
                        raise atlas_connector.ConnectorConflictError(
                            "synthetic forward conflict"
                        )
                    if self.mode == "input":
                        raise OSError("synthetic forward acknowledgement loss")
                    result = self.inner.conditional_replace(*args, **kwargs)
                    self._forwarded = True
                    if self.mode == "other":
                        current = result["revision"]
                        self.inner.conditional_replace(
                            TOPICS_URI, current, b"manual conflict\n"
                        )
                        raise OSError("synthetic unknown forward effect")
                    if self.mode == "post-sibling":
                        self._archive_manifest()
                    if self.mode in {
                        "malformed-ack",
                        "rollback-conflict",
                        "rollback-malformed",
                    }:
                        return {"status": "replaced"}
                    if self.mode == "wrong-ack":
                        return dict(
                            result,
                            acknowledged_revision="sha256:" + "0" * 64,
                        )
                    if self.mode == "extra-ack":
                        return dict(result, unexpected="field")
                    return result
                if self.mode == "rollback-conflict":
                    current = self.inner.revision(TOPICS_URI)
                    self.inner.conditional_replace(
                        TOPICS_URI, current, b"manual rollback conflict\n"
                    )
                    return self.inner.conditional_replace(*args, **kwargs)
                if self.mode == "rollback-malformed":
                    self.inner.conditional_replace(*args, **kwargs)
                    return {}
                return self.inner.conditional_replace(*args, **kwargs)

        def candidate_args(fixture: TemporaryAtlasProfile) -> dict[str, str]:
            lines = topics_text().splitlines()
            for index, line in enumerate(lines):
                cells = atlas_state.split_markdown_row(line)
                if cells and cells[0] == TOPIC_ID:
                    cells[5] = "z; a"
                    lines[index] = "| " + " | ".join(cells) + " |"
            fixture.put(TOPICS_URI, "\n".join(lines) + "\n")
            prepared = invoke(fixture, "migration.prepare_topics_lists")
            self.assert_envelope(prepared, ok=True, op="migration.prepare_topics_lists")
            candidate = prepared["result"]["candidate"]
            assert candidate is not None
            return {
                "instance_id": prepared["result"]["binding"]["instance_id"],
                "candidate_sha256": candidate["candidate_sha256"],
                "approval": candidate["approval_literal"],
            }

        cases = (
            ("applied", "applied", "list-only", "output", False),
            ("input", "rolled-back", "restored-preimage", "input", False),
            ("malformed-ack", "rolled-back", "restored-preimage", "output", True),
            ("wrong-ack", "rolled-back", "restored-preimage", "output", True),
            ("extra-ack", "rolled-back", "restored-preimage", "output", True),
            ("post-reread", "rolled-back", "unknown", "output", True),
            ("post-sibling", "rolled-back", "unknown", "output", True),
            ("post-topic-binding", "manual-conflict", "unknown", "other", False),
            ("rollback-conflict", "manual-conflict", "unknown", "output", True),
            ("rollback-malformed", "manual-conflict", "unknown", "output", True),
            ("other", "manual-conflict", "unknown", "other", False),
        )
        for mode, expected_state, expected_lineage, classification, rollback in cases:
            with self.subTest(mode=mode), temporary_profile() as fixture:
                args = candidate_args(fixture)
                connector = EffectConnector(fixture.connector(), mode)
                response = invoke(
                    fixture,
                    "migration.apply_topics_lists",
                    connector=connector,
                    **args,
                )
                self.assert_envelope(
                    response, ok=True, op="migration.apply_topics_lists"
                )
                result = response["result"]
                self.assertEqual(result["state"], expected_state)
                self.assertEqual(result["lineage"]["classification"], expected_lineage)
                self.assertEqual(result["forward"]["classification"], classification)
                self.assertEqual(
                    result["rollback"] is not None,
                    rollback,
                )
                self.assertLessEqual(len(connector.cas_paths), 2)
                self.assertTrue(all(path == TOPICS_URI for path in connector.cas_paths))
                if rollback:
                    self.assertEqual(len(connector.cas_paths), 2)
                    self.assertEqual(
                        result["rollback"]["preimage_confirmed"],
                        expected_state == "rolled-back",
                    )
                else:
                    self.assertEqual(len(connector.cas_paths), 1)
                codes = {finding["code"] for finding in result["findings"]}
                if mode == "input":
                    self.assertIn("MIGRATION_FORWARD_FAILED", codes)
                if mode in {"malformed-ack", "wrong-ack", "extra-ack"}:
                    self.assertIn("MIGRATION_FORWARD_ACK_INVALID", codes)
                if mode == "post-reread":
                    self.assertIn("MIGRATION_POST_VALIDATION_FAILED", codes)
                if mode == "post-topic-binding":
                    self.assertIn("MIGRATION_EFFECT_UNKNOWN", codes)
                if mode == "post-sibling":
                    self.assertIn("MIGRATION_SIBLING_DRIFT", codes)
                if mode == "rollback-conflict":
                    self.assertIn("MIGRATION_ROLLBACK_FAILED", codes)
                if mode == "rollback-malformed":
                    self.assertIn("MIGRATION_ROLLBACK_FAILED", codes)
                if mode == "other":
                    self.assertIn("MIGRATION_EFFECT_UNKNOWN", codes)

        with temporary_profile() as fixture:
            args = candidate_args(fixture)
            connector = EffectConnector(fixture.connector(), "conflict")
            response = invoke(
                fixture,
                "migration.apply_topics_lists",
                connector=connector,
                **args,
            )
            self.assert_envelope(response, ok=False, op="migration.apply_topics_lists")
            self.assertEqual(
                response_findings(response)[0][0],
                "MIGRATION_CANDIDATE_STALE",
            )
            self.assertEqual(connector.cas_paths, [TOPICS_URI])

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
