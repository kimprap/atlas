from __future__ import annotations

import base64
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_quality  # noqa: E402
import atlas_source  # noqa: E402
import atlas_transaction  # noqa: E402
import atlas_state  # noqa: E402
import atlas_url  # noqa: E402


URL = "https://example.com/promoted-source"
SOURCE_ID = atlas_url.source_id_for(URL)
PAYLOAD = "Primary source payload.\n"
CONTENT_HASH = atlas_transaction.sha256(PAYLOAD.encode())
OLD_PAYLOAD = "Old source payload.\n"
OLD_HASH = atlas_transaction.sha256(OLD_PAYLOAD.encode())
ARTIFACT_PATH = (
    "summaries/sources/artifacts/2026/2026-07/"
    f"2026-07-19--{SOURCE_ID}--promoted-source.md"
)


def source_target_allowed(path: str) -> bool:
    return path.startswith("summaries/sources/artifacts/") or path in {
        atlas_state.RELATIONS_PATH,
        atlas_state.TOPICS_PATH,
        atlas_state.MANIFEST_PATH,
    }


def source_target_rank(path: str) -> tuple[int, str]:
    if path.startswith("summaries/sources/artifacts/"):
        return 0, path
    order = {
        atlas_state.RELATIONS_PATH: 1,
        atlas_state.TOPICS_PATH: 2,
        atlas_state.MANIFEST_PATH: 3,
    }
    if path not in order:
        raise atlas_transaction.TransactionError(
            f"transaction target is outside the source/route write set: {path}"
        )
    return order[path], path


def source_identity(
    record: dict[str, object], event_hash: str
) -> atlas_transaction.TransactionIdentity:
    return atlas_transaction.TransactionIdentity(
        base={
            "event_record_sha256": event_hash,
            "source_id": record.get("source_id"),
        },
        intent={
            "event_type": record.get("event_type"),
            "source_id": record.get("source_id"),
        },
    )


def source_plan(
    event_record: dict[str, object],
    targets: tuple[atlas_transaction.TransactionTarget, ...],
    *,
    event_path: str = "events/source-upsert.json",
    attempt: int = 0,
    predecessor: str | None = None,
) -> atlas_transaction.TransactionPlan:
    return atlas_transaction.build_transaction_plan(
        event_path=event_path,
        event_record=event_record,
        targets=targets,
        target_allowlist=source_target_allowed,
        target_rank=source_target_rank,
        identity_binding=source_identity,
        attempt=attempt,
        predecessor_sha256=predecessor,
    )


def source_successor(
    plan: atlas_transaction.TransactionPlan,
    *,
    event_path: str,
    event_record: dict[str, object],
    terminal_record: bytes,
) -> atlas_transaction.TransactionPlan:
    return atlas_transaction.build_successor_plan(
        plan,
        event_path=event_path,
        event_record=event_record,
        terminal_record=terminal_record,
        target_allowlist=source_target_allowed,
        target_rank=source_target_rank,
        identity_binding=source_identity,
    )


def execute_source(
    connector: Any, transaction_root: str, plan: atlas_transaction.TransactionPlan
) -> str:
    return atlas_transaction.execute_transaction(
        connector,
        transaction_root,
        plan,
        target_allowlist=source_target_allowed,
        target_rank=source_target_rank,
    )


def recover_source(
    connector: Any, transaction_root: str, plan: atlas_transaction.TransactionPlan
) -> str:
    return atlas_transaction.recover_transaction(
        connector,
        transaction_root,
        plan,
        target_allowlist=source_target_allowed,
        target_rank=source_target_rank,
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
    content_hash = atlas_transaction.sha256(payload.encode())
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


def evidence(
    payload: str = PAYLOAD, *, first_seen: str = "2026-07-19"
) -> dict[str, object]:
    return {
        "version": 1,
        "canonical_url": URL,
        "source_urls": [URL],
        "allowed_urls": [URL],
        "payload_text": payload,
        "fetched_at": first_seen,
    }


def projected_evidence(
    payload: str = "bounded model-visible payload",
    *,
    first_seen: str = "2026-07-19",
) -> dict[str, object]:
    complete = f"LEAD {payload} TRAIL"
    start = complete.encode("utf-8").index(payload.encode("utf-8"))
    end = start + len(payload.encode("utf-8"))
    return {
        "version": 1,
        "canonical_url": URL,
        "source_urls": [URL],
        "allowed_urls": [URL],
        "payload_text": payload,
        "content_hash": atlas_transaction.sha256(complete.encode("utf-8")),
        "payload_projection": True,
        "complete_text": complete,
        "projection_ranges": [[start, end]],
        "fetched_at": first_seen,
    }


def source_event(
    *, payload: str = PAYLOAD, first_seen: str = "2026-07-19"
) -> dict[str, object]:
    return {
        "type": "source-upsert",
        "source_id": SOURCE_ID,
        "canonical_url": URL,
        "artifact": ARTIFACT_PATH,
        "first_seen": first_seen,
        "checked_on": "2026-07-19",
        "summarized_on": "2026-07-19",
        "content_hash": atlas_transaction.sha256(payload.encode()),
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
        "content_hash": atlas_transaction.sha256(payload.encode()),
        "route_status": route_status,
        "status": "active",
    }


def summary_proposal(*, published: str = "2026-05") -> dict[str, object]:
    return {
        "version": 1,
        "metadata": {
            "title": "Synthetic source proposal",
            "author": "Example author",
            "publisher": "Example publisher",
            "published": published,
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
                "url": f"{URL}#rule-2",
                "relation": "related",
                "locator": "Rule 2",
                "ledger_id": "ledger-rule-2",
            }
        ],
    }


def summary_render_context() -> dict[str, object]:
    return {
        "note_type": "source-summary",
        "managed_by": "atlas",
        "primary_domain": "testing",
        "subdomains": ["unit"],
        "secondary_domains": [],
        "canonical_tags": ["deterministic"],
        "candidate_terms": ["handoff"],
        "routed_at": "2026-07-20",
        "last_checked": "2026-07-20",
        "last_summarized": "2026-07-20",
        "refresh_after": "2027-07-20",
        "acquired_by": "manual",
        "acquisition_run": "source-render-test",
    }


class LocalConnector:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.failure: tuple[str, str, bool] | None = None
        self.failed = False

    def inject(
        self, operation: str, path_fragment: str, *, after: bool = False
    ) -> None:
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
        if (operation, after) == (
            expected_operation,
            expected_after,
        ) and fragment in value:
            self.failed = True
            raise OSError(f"injected {operation} failure: {value}")

    def read(self, value: str) -> bytes | None:
        path = self._path(value)
        return path.read_bytes() if path.is_file() else None

    def read_record(self, value: str) -> bytes | None:
        return self.read(value)

    def create(self, value: str, data: bytes) -> None:
        self._fail("create", value, after=False)
        path = self._path(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
        self._fail("create", value, after=True)

    def write(
        self,
        value: str,
        data: bytes,
        expected_revision: str | None = None,
    ) -> None:
        self._fail("write", value, after=False)
        path = self._path(value)
        current = path.read_bytes() if path.is_file() else None
        actual = (
            "missing"
            if current is None
            else "sha256:" + atlas_transaction.sha256(current)
        )
        if expected_revision is not None and actual != expected_revision:
            raise ValueError("revision conflict")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        self._fail("write", value, after=True)

    def delete(self, value: str, expected_revision: str | None = None) -> None:
        self._fail("delete", value, after=False)
        path = self._path(value)
        current = path.read_bytes() if path.is_file() else None
        actual = (
            "missing"
            if current is None
            else "sha256:" + atlas_transaction.sha256(current)
        )
        if expected_revision is not None and actual != expected_revision:
            raise ValueError("revision conflict")
        if path.exists():
            path.unlink()


class RecordingLocalConnector(LocalConnector):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.creates: list[str] = []
        self.writes: list[str] = []
        self.deletes: list[str] = []

    def create(self, value: str, data: bytes) -> None:
        self.creates.append(value)
        super().create(value, data)

    def write(
        self,
        value: str,
        data: bytes,
        expected_revision: str | None = None,
    ) -> None:
        self.writes.append(value)
        super().write(value, data, expected_revision)

    def delete(self, value: str, expected_revision: str | None = None) -> None:
        self.deletes.append(value)
        super().delete(value, expected_revision)


class RollbackDriftConnector(LocalConnector):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.drift_path: str | None = None
        self.drift_bytes = b"out-of-band drift\n"

    def write(
        self,
        value: str,
        data: bytes,
        expected_revision: str | None = None,
    ) -> None:
        if self.drift_path == value and expected_revision is not None:
            self._path(value).write_bytes(self.drift_bytes)
            self.drift_path = None
        super().write(value, data, expected_revision)


class AtlasSourceTests(unittest.TestCase):
    def test_prepare_source_rejects_malformed_and_nonfinal_workers_before_state(
        self,
    ) -> None:
        invalid_documents = {
            "manifest": "malformed\n",
            "topics": "malformed\n",
            "relations": "malformed\n",
        }
        nonfinal = {
            "version": 1,
            "kind": "needs-input",
            "identity": {"canonical_url": URL, "source_id": SOURCE_ID},
            "reason": "aggregate page requires a choice",
            "choices": ["page-only", "expand", "stop-without-writing"],
        }
        cases = (
            ({}, "WORKER_KIND_INVALID"),
            (nonfinal, "WORKER_PACKET_NOT_FINAL"),
        )

        for worker, expected_code in cases:
            with self.subTest(code=expected_code):
                result = atlas_source.prepare_source(
                    invalid_documents,
                    canonical_url=URL,
                    checked_on="2026-08-17",
                    mode="routine",
                    worker=worker,
                    living_artifact_text=None,
                )
                self.assertEqual(result["state"], "rejected")
                self.assertEqual(result["findings"][0]["code"], expected_code)

        nested_invalid = {
            "version": 1,
            "kind": "ready",
            "identity": {"canonical_url": URL, "source_id": SOURCE_ID},
            "evidence_bundle": {},
            "evidence_ledger": {},
            "proposal": {},
            "checklist": [],
            "refresh_after": "2027-08-17",
        }
        nested_result = atlas_source.prepare_source(
            invalid_documents,
            canonical_url=URL,
            checked_on="2026-08-17",
            mode="routine",
            worker=nested_invalid,
            living_artifact_text=None,
        )
        self.assertEqual(nested_result["state"], "rejected")
        self.assertIn(
            "WORKER_EVIDENCE_BUNDLE_INVALID",
            {finding["code"] for finding in nested_result["findings"]},
        )

    def test_normalize_capture_preserves_exact_text_and_metadata(self) -> None:
        requested = "https://example.test/source"
        final = "https://example.test/source.md"
        text = "URL: not transport framing\n\nRésumé 東京.\r\n"
        capture = {
            "version": 1,
            "requested_url": requested,
            "final_url": final,
            "content_type": "text/markdown; charset=utf-8",
            "method": "github-file-read",
            "complete": True,
            "notes": ["redirect followed", ""],
            "text": text,
        }

        result = atlas_source.normalize_capture(capture)

        self.assertEqual(
            result,
            {
                "version": 1,
                "canonical_url": requested,
                "final_url": final,
                "content_type": "text/markdown; charset=utf-8",
                "method": "github-file-read",
                "complete": True,
                "notes": ["redirect followed", ""],
                "text": text,
                "content_hash": atlas_transaction.sha256(text.encode("utf-8")),
                "payload_bytes": len(text.encode("utf-8")),
            },
        )

    def test_normalize_capture_normalizes_urls_without_parsing_text(self) -> None:
        text = "Content-Type: text/plain\n\n---\n\nLiteral source bytes.\n"
        result = atlas_source.normalize_capture(
            {
                "version": 1,
                "requested_url": "HTTPS://EXAMPLE.TEST:443/source?utm_source=x",
                "final_url": "https://example.test/source",
                "content_type": "text/plain",
                "method": "http",
                "complete": True,
                "notes": [],
                "text": text,
            }
        )
        self.assertEqual(result["canonical_url"], "https://example.test/source")
        self.assertEqual(result["final_url"], "https://example.test/source")
        self.assertEqual(result["text"], text)

    def test_normalize_capture_fails_closed_on_noncanonical_shapes(self) -> None:
        valid = {
            "version": 1,
            "requested_url": "https://example.test/source",
            "final_url": "https://example.test/source",
            "content_type": "text/plain",
            "method": "http",
            "complete": True,
            "notes": [],
            "text": "payload\n",
        }
        invalid = (
            {**valid, "alias": "unexpected"},
            {key: value for key, value in valid.items() if key != "notes"},
            {**valid, "version": 2},
            {**valid, "complete": False},
            {**valid, "content_type": "application/json"},
            {**valid, "method": ""},
            {**valid, "notes": "none"},
            {**valid, "notes": [1]},
            {**valid, "text": ""},
            {**valid, "text": "\ud800"},
            {**valid, "requested_url": "file:///tmp/source"},
            {**valid, "final_url": "not-a-url"},
        )
        for capture in invalid:
            with self.subTest(capture=capture):
                with self.assertRaises(atlas_source.SourceError):
                    atlas_source.normalize_capture(capture)

    def test_new_merge_injects_reducer_identity_and_replays_byte_identically(
        self,
    ) -> None:
        merged = atlas_source.merge_artifact(
            artifact(),
            evidence(),
            source_event(),
            source_state(created=True),
        )
        parsed = atlas_source.parse_artifact(merged)
        self.assertEqual(atlas_source.scalar(parsed.values, "source_id"), SOURCE_ID)
        self.assertEqual(atlas_source.scalar(parsed.values, "source_seq"), "1")
        self.assertEqual(
            atlas_source.scalar(parsed.values, "routing_status"), "unrouted"
        )
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

    def test_artifact_frontmatter_requires_native_integer_and_list_shapes(self) -> None:
        valid = artifact()
        invalid_artifacts = (
            valid.replace("schema_version: 1", 'schema_version: "1"'),
            valid.replace("source_seq: 99", 'source_seq: "99"'),
            valid.replace("candidate_terms: []", 'candidate_terms: "[]"'),
            valid.replace("candidate_terms: []", 'candidate_terms: "agent tooling"'),
        )
        for invalid in invalid_artifacts:
            with self.subTest(invalid=invalid.splitlines()[1:6]):
                with self.assertRaises(atlas_source.SourceError):
                    atlas_source.parse_artifact(invalid)

    def test_render_summary_proposal_is_deterministic_and_preserves_ownership(
        self,
    ) -> None:
        proposal = summary_proposal()
        caller_context = summary_render_context()
        reducer_state = source_state(
            created=True,
            source_seq=7,
            route_status="routed",
        )
        first = atlas_source.render_summary_proposal(
            proposal=proposal,
            caller_context=caller_context,
            source_state=reducer_state,
        )
        second = atlas_source.render_summary_proposal(
            proposal=proposal,
            caller_context=caller_context,
            source_state=reducer_state,
        )
        self.assertEqual(first, second)

        parsed = atlas_source.parse_artifact(first)
        self.assertEqual(
            atlas_source.scalar(parsed.values, "source_id"),
            reducer_state["source_id"],
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "source_seq"),
            str(reducer_state["source_seq"]),
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "canonical_url"),
            reducer_state["canonical_url"],
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "routing_status"),
            reducer_state["route_status"],
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "content_hash"),
            reducer_state["content_hash"],
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "acquired_by"),
            caller_context["acquired_by"],
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "last_checked"),
            caller_context["last_checked"],
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "title"), "Synthetic source proposal"
        )
        self.assertEqual(atlas_source.scalar(parsed.values, "published"), "2026-05")
        self.assertIn("schema_version: 1\n", first)
        self.assertIn("source_seq: 7\n", first)
        self.assertIn('subdomains: ["unit"]', first)
        self.assertIn('canonical_tags: ["deterministic"]', first)
        self.assertIn('candidate_terms: ["handoff"]', first)
        self.assertIn('published: "2026-05"', first)
        self.assertNotIn("2026-05-01", first)
        self.assertIn("Rule 2", parsed.body)
        self.assertIn(
            "The source requires a verified handoff before mutation.",
            parsed.body,
        )
        self.assertIn(f"{URL}#rule-2", parsed.body)

        contaminated = {**proposal, "source_id": "0" * 12}
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.render_summary_proposal(
                proposal=contaminated,
                caller_context=caller_context,
                source_state=reducer_state,
            )

    def test_valid_proposal_renders_a_valid_canonical_summary(self) -> None:
        proposal = summary_proposal()
        ledger = {
            "version": 1,
            "evidence": [{"locator": "Rule 2", "ledger_id": "ledger-rule-2"}],
            "links": [
                {
                    "url": f"{URL}#rule-2",
                    "locator": "Rule 2",
                    "ledger_id": "ledger-rule-2",
                }
            ],
        }
        self.assertEqual(atlas_quality.validate_proposal(proposal, ledger), [])
        payload = (
            "The source requires a verified handoff before mutation. "
            f"Rule 2 specifies the sequence and links to {URL}#rule-2.\n"
        )
        rendered = atlas_source.render_summary_proposal(
            proposal=proposal,
            caller_context=summary_render_context(),
            source_state=source_state(
                payload=payload,
                created=True,
                source_seq=7,
                route_status="routed",
            ),
        )
        evidence_bundle = {
            "version": 1,
            "canonical_url": URL,
            "source_urls": [f"{URL}#rule-2"],
            "allowed_urls": [],
            "forbidden_context_terms": ["campaign alpha"],
            "payload_text": payload,
            "require_routing_reason": False,
            "unresolved_validation_caveat": False,
        }
        checklist = [
            {
                "id": item_id,
                "status": "pass",
                "evidence": "Rule 2 bounded source evidence",
            }
            for item_id in atlas_quality.CHECKLIST_IDS
        ]
        self.assertEqual(
            atlas_quality.validate_summary(rendered, evidence_bundle, checklist),
            [],
        )

    def test_existing_same_hash_replaces_semantics_and_preserves_living_provenance(
        self,
    ) -> None:
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
        self.assertEqual(
            atlas_source.scalar(parsed.values, "acquired_by"), "acquisition-run"
        )
        self.assertEqual(
            atlas_source.scalar(parsed.values, "acquisition_run"), "original-run"
        )
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
        self.assertEqual(
            atlas_source.scalar(parsed.values, "routing_status"), "unrouted"
        )
        self.assertEqual(atlas_source.scalar(parsed.values, "routed_at"), "")
        self.assertEqual(
            atlas_source.scalar(parsed.values, "acquired_by"), "acquisition-run"
        )
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

    def test_merge_accepts_backed_projection_for_bounded_payload(self) -> None:
        bounded = projected_evidence()
        event = source_event()
        event["content_hash"] = bounded["content_hash"]
        state = source_state(created=True)
        state["content_hash"] = bounded["content_hash"]
        staged = artifact().replace(
            f"content_hash: {json.dumps(CONTENT_HASH)}",
            f"content_hash: {json.dumps(bounded['content_hash'])}",
        )
        # artifact() uses render path - fix via parse/rebuild if needed
        parsed = atlas_source.parse_artifact(artifact())
        values = dict(parsed.values)
        values["content_hash"] = atlas_source.quoted(str(bounded["content_hash"]))
        staged = atlas_source.render_artifact(values, parsed.body)
        merged = atlas_source.merge_artifact(staged, bounded, event, state)
        self.assertEqual(
            atlas_source.scalar(
                atlas_source.parse_artifact(merged).values, "content_hash"
            ),
            bounded["content_hash"],
        )

        bad = dict(bounded)
        bad["content_hash"] = "invalid"
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.merge_artifact(staged, bad, event, state)

    def test_evidence_identity_projection_matrix(self) -> None:
        # Matching payload-only hash
        self.assertEqual(
            atlas_source.evidence_identity(evidence())["content_hash"],
            CONTENT_HASH,
        )

        # Empty payload is no-write / identity invalid
        empty = evidence("")
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(empty)

        # Media fields rejected
        media = evidence()
        media["media"] = [{"url": "https://example.com/x.png", "fetched": True}]
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(media)

        # No explicit hash, projection true
        bad = evidence()
        bad["payload_projection"] = True
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(bad)

        # Explicit matching hash, projection omitted
        matching = evidence()
        matching["content_hash"] = CONTENT_HASH
        self.assertEqual(
            atlas_source.evidence_identity(matching)["content_hash"], CONTENT_HASH
        )

        # Explicit matching hash, projection false
        matching["payload_projection"] = False
        self.assertEqual(
            atlas_source.evidence_identity(matching)["content_hash"], CONTENT_HASH
        )

        # Explicit matching hash, projection true
        matching["payload_projection"] = True
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(matching)

        # Explicit mismatching hash without projection backing
        projected = evidence("bounded model-visible payload")
        projected["content_hash"] = "c" * 64
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(projected)

        projected["payload_projection"] = False
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(projected)

        # Declaration true without complete_text still fails (unbacked)
        projected["payload_projection"] = True
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(projected)

        # Fully backed projection
        backed = projected_evidence()
        self.assertEqual(
            atlas_source.evidence_identity(backed)["content_hash"],
            backed["content_hash"],
        )

        # Non-boolean projection
        for value in ("true", 1, 0):
            bad_type = evidence()
            bad_type["payload_projection"] = value
            with self.assertRaises(atlas_source.SourceError):
                atlas_source.evidence_identity(bad_type)

        # Malformed explicit hash
        bad_hash = evidence()
        bad_hash["content_hash"] = "not-a-hash"
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.evidence_identity(bad_hash)

        # merge-artifact rejects invalid projection cases
        invalid_merge = evidence("bounded model-visible payload")
        invalid_merge["content_hash"] = CONTENT_HASH
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.merge_artifact(
                artifact(), invalid_merge, source_event(), source_state(created=True)
            )

    def test_classify_hash_transition_same_changed_and_no_write(self) -> None:
        self.assertEqual(
            atlas_source.classify_hash_transition(None, evidence()),
            "changed-hash",
        )
        self.assertEqual(
            atlas_source.classify_hash_transition(CONTENT_HASH, evidence()),
            "same-hash",
        )
        other = "d" * 64
        self.assertEqual(
            atlas_source.classify_hash_transition(other, evidence()),
            "changed-hash",
        )
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.classify_hash_transition(CONTENT_HASH, evidence(""))
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.classify_hash_transition("not-a-hash", evidence())
        media = evidence()
        media["binary_content"] = "AAAA"
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.classify_hash_transition(CONTENT_HASH, media)

    def test_merge_rejects_staged_evidence_event_identity_disagreement(self) -> None:
        bad = evidence()
        bad["payload_text"] = "different payload"
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.merge_artifact(
                artifact(), bad, source_event(), source_state(created=True)
            )

    def test_route_renderer_changes_only_route_fields_and_sets_checked_date(
        self,
    ) -> None:
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
        self.assertEqual(
            atlas_source.scalar(after.values, "routing_status"), "no-topic-match"
        )
        self.assertEqual(atlas_source.scalar(after.values, "routed_at"), "2026-07-20")
        route_line = re_line(after.body, "**Route status**:")
        self.assertEqual(route_line, "**Route status**: `no-topic-match`")

    def test_route_renderer_replaces_verifier_reasons_from_route_event(self) -> None:
        routed_event = {
            "type": "route-upsert",
            "source_id": SOURCE_ID,
            "content_hash": CONTENT_HASH,
            "checked_on": "2026-07-20",
            "outcome": "routed",
            "edges": [
                {
                    "topic_id": "test-topic",
                    "relation": "direct",
                    "impact": "high",
                    "confidence": "high",
                    "reason": (
                        "Verifier: README lines 10-20 — source-local claim "
                        "[relation=direct; impact=high]"
                    ),
                }
            ],
        }
        routed = atlas_source.render_route_artifact(artifact(), routed_event, "routed")
        self.assertIn("- " + routed_event["edges"][0]["reason"], routed)
        self.assertEqual(
            atlas_source.render_route_artifact(routed, routed_event, "routed"),
            routed,
        )

        no_match_event = {
            **routed_event,
            "outcome": "no-topic-match",
            "edges": [],
        }
        no_match = atlas_source.render_route_artifact(
            routed, no_match_event, "no-topic-match"
        )
        self.assertNotIn("Verifier:", no_match)

    def test_same_hash_merge_preserves_only_living_verifier_reason(self) -> None:
        reason = (
            "Verifier: README lines 10-20 — source-local claim "
            "[relation=direct; impact=high]"
        )
        route_event = {
            "type": "route-upsert",
            "source_id": SOURCE_ID,
            "content_hash": CONTENT_HASH,
            "checked_on": "2026-07-20",
            "outcome": "routed",
            "edges": [
                {
                    "topic_id": "test-topic",
                    "relation": "direct",
                    "impact": "high",
                    "confidence": "high",
                    "reason": reason,
                }
            ],
        }
        living = atlas_source.render_route_artifact(artifact(), route_event, "routed")
        staged = artifact(
            routing_status="routed",
            routed_at="2026-07-20",
            marker="Same-hash refreshed semantics.",
        )
        merged = atlas_source.merge_artifact(
            staged,
            evidence(),
            source_event(),
            source_state(created=False, route_status="routed"),
            living_artifact_text=living,
        )
        self.assertEqual(merged.count(f"- {reason}"), 1)

        bundle = evidence()
        bundle["require_routing_reason"] = True
        items = [
            {
                "id": checklist_id,
                "status": "pass",
                "evidence": f"{checklist_id} checked against the fixture.",
            }
            for checklist_id in atlas_quality.CHECKLIST_IDS
        ]

        def routing_codes(text: str) -> set[str]:
            return {
                finding.code
                for finding in atlas_quality.validate_summary(text, bundle, items)
            }

        self.assertNotIn("ROUTING_REASON_MISSING", routing_codes(merged))
        self.assertNotIn("ROUTING_REASON_INVALID", routing_codes(merged))

        forged_staged = staged.replace(
            "## Reuse cues",
            "## Routing notes\n\n"
            "- Verifier: invented locator — invented claim "
            "[relation=direct; impact=high]\n\n"
            "## Reuse cues",
        )
        missing_living = artifact(routing_status="routed", routed_at="2026-07-20")
        without_real_reason = atlas_source.merge_artifact(
            forged_staged,
            evidence(),
            source_event(),
            source_state(created=False, route_status="routed"),
            living_artifact_text=missing_living,
        )
        self.assertNotIn("invented locator", without_real_reason)
        self.assertIn("ROUTING_REASON_MISSING", routing_codes(without_real_reason))

        invalid_route_event = {
            **route_event,
            "edges": [{**route_event["edges"][0], "reason": "validator demand"}],
        }
        with self.assertRaises(atlas_source.SourceError):
            atlas_source.render_route_artifact(
                artifact(), invalid_route_event, "routed"
            )

    def test_event_record_and_transaction_ids_are_hash_bound(self) -> None:
        event = source_event()
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=event,
            route_decision=None,
            promotion={
                "artifact_uri": "vault://atlas/staging/source.md",
                "artifact_revision": "sha256:" + "a" * 64,
                "evidence_uri": "vault://atlas/staging/evidence.json",
                "evidence_revision": "sha256:" + "b" * 64,
            },
        )
        targets = (
            atlas_transaction.TransactionTarget(ARTIFACT_PATH, None, b"artifact"),
            atlas_transaction.TransactionTarget(
                atlas_state.MANIFEST_PATH, b"old", b"new"
            ),
        )
        first = source_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        second = source_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        self.assertEqual(first, second)
        self.assertRegex(first.transaction_id, r"^[0-9a-f]{16}-a000000$")
        terminal = atlas_transaction.canonical_json(
            {
                "version": 1,
                "status": "rolled-back",
                "intent_sha256": atlas_transaction.sha256(
                    atlas_transaction.canonical_json(first.intent)
                ),
            }
        )
        successor = source_successor(
            first,
            event_path="events/source-upsert.json",
            event_record=record,
            terminal_record=terminal,
        )
        self.assertEqual(successor.base_transaction_id, first.base_transaction_id)
        self.assertEqual(
            successor.predecessor_sha256, atlas_transaction.sha256(terminal)
        )
        self.assertTrue(successor.transaction_id.endswith("-a000001"))
        self.assertEqual(successor.attempt, 1)
        self.assertEqual(successor.targets, first.targets)
        self.assertEqual(successor.intent["targets"], first.intent["targets"])
        successor_terminal = atlas_transaction.canonical_json(
            {
                "version": 1,
                "status": "rolled-back",
                "intent_sha256": atlas_transaction.sha256(
                    atlas_transaction.canonical_json(successor.intent)
                ),
            }
        )
        with self.assertRaises(atlas_transaction.TransactionError):
            source_successor(
                successor,
                event_path="events/source-upsert.json",
                event_record=record,
                terminal_record=successor_terminal,
            )
        applied_terminal = atlas_transaction.canonical_json(
            {
                "version": 1,
                "status": "applied",
                "intent_sha256": atlas_transaction.sha256(
                    atlas_transaction.canonical_json(first.intent)
                ),
            }
        )
        with self.assertRaises(atlas_transaction.TransactionError):
            source_successor(
                first,
                event_path="events/source-upsert.json",
                event_record=record,
                terminal_record=applied_terminal,
            )
        with self.assertRaises(atlas_transaction.TransactionError):
            source_successor(
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
        paths = (
            ARTIFACT_PATH,
            atlas_state.RELATIONS_PATH,
            atlas_state.TOPICS_PATH,
            atlas_state.MANIFEST_PATH,
        )
        inputs = (None, b"relations-old", b"topics-old", b"manifest-old")
        outputs = (b"artifact-new", b"relations-new", b"topics-new", b"manifest-new")
        targets = tuple(
            atlas_transaction.TransactionTarget(path, before, after)
            for path, before, after in zip(paths, inputs, outputs, strict=True)
        )
        plan = source_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            for path, value in zip(paths, inputs, strict=True):
                if value is not None:
                    connector.write(path, value)
            self.assertEqual(
                execute_source(connector, "transactions", plan),
                "applied",
            )
            for path, expected in zip(paths, outputs, strict=True):
                self.assertEqual(connector.read(path), expected)
            self.assertEqual(
                recover_source(connector, "transactions", plan),
                "applied",
            )
            for path, expected in zip(paths, outputs, strict=True):
                self.assertEqual(connector.read(path), expected)
            base = f"transactions/{plan.transaction_id}"
            intent = atlas_transaction.canonical_json(plan.intent)
            intent_sha256 = atlas_transaction.sha256(intent)
            self.assertEqual(connector.read(f"{base}/intent.json"), intent)
            backups: list[bytes] = []
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
                backups.append(backup)
                self.assertEqual(
                    connector.read(f"{base}/backups/{index:06d}.json"),
                    backup,
                )
                self.assertEqual(
                    connector.read(f"{base}/progress/{index:06d}.json"),
                    atlas_transaction.canonical_json(
                        {
                            "version": 1,
                            "index": index,
                            "path": target.path,
                            "output_sha256": atlas_transaction.sha256(
                                target.output_bytes
                            ),
                        }
                    ),
                )
            self.assertEqual(
                connector.read(f"{base}/prepared.json"),
                atlas_transaction.canonical_json(
                    {
                        "version": 1,
                        "intent_sha256": intent_sha256,
                        "backup_sha256s": [
                            atlas_transaction.sha256(item) for item in backups
                        ],
                    }
                ),
            )
            self.assertEqual(
                connector.read(f"{base}/applied.json"),
                atlas_transaction.canonical_json(
                    {
                        "version": 1,
                        "status": "applied",
                        "intent_sha256": intent_sha256,
                    }
                ),
            )
            self.assertIsNotNone(connector.read(f"{base}/intent.json"))
            self.assertIsNotNone(connector.read(f"{base}/prepared.json"))
            self.assertIsNotNone(connector.read(f"{base}/applied.json"))
            for index in range(4):
                self.assertIsNotNone(connector.read(f"{base}/backups/{index:06d}.json"))
                self.assertIsNotNone(
                    connector.read(f"{base}/progress/{index:06d}.json")
                )

    def test_recovery_rejects_nonprefix_progress_without_mutation_and_backfills_suffix(
        self,
    ) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        paths = (
            ARTIFACT_PATH,
            atlas_state.RELATIONS_PATH,
            atlas_state.TOPICS_PATH,
            atlas_state.MANIFEST_PATH,
        )
        inputs = (None, b"relations-old", b"topics-old", b"manifest-old")
        outputs = (b"artifact-new", b"relations-new", b"topics-new", b"manifest-new")
        targets = tuple(
            atlas_transaction.TransactionTarget(path, before, after)
            for path, before, after in zip(paths, inputs, outputs, strict=True)
        )
        plan = source_plan(
            event_path="events/source-upsert.json", event_record=record, targets=targets
        )
        base = f"transactions/{plan.transaction_id}"
        record_paths = (
            f"{base}/intent.json",
            *(f"{base}/backups/{index:06d}.json" for index in range(len(targets))),
            f"{base}/prepared.json",
            *(f"{base}/progress/{index:06d}.json" for index in range(len(targets))),
            f"{base}/applied.json",
        )

        for corruption, expected_message in (
            ("valid", "transaction progress records are not a cumulative prefix"),
            ("collision", "transaction progress record collision"),
        ):
            with (
                self.subTest(corruption=corruption),
                tempfile.TemporaryDirectory() as directory,
            ):
                connector = RecordingLocalConnector(Path(directory))
                for path, value in zip(paths, inputs, strict=True):
                    if value is not None:
                        connector.write(path, value)
                self.assertEqual(
                    execute_source(connector, "transactions", plan), "applied"
                )
                transaction_root = connector.root / "transactions" / plan.transaction_id
                if corruption == "valid":
                    (transaction_root / "progress" / "000000.json").unlink()
                (transaction_root / "applied.json").unlink()
                if corruption == "collision":
                    (transaction_root / "progress" / "000001.json").write_bytes(
                        b"collision\n"
                    )
                before_records = {path: connector.read(path) for path in record_paths}
                before_targets = {path: connector.read(path) for path in paths}
                connector.creates.clear()
                connector.writes.clear()
                connector.deletes.clear()

                with self.assertRaisesRegex(
                    atlas_transaction.TransactionError, expected_message
                ):
                    recover_source(connector, "transactions", plan)

                self.assertEqual(connector.creates, [])
                self.assertEqual(connector.writes, [])
                self.assertEqual(connector.deletes, [])
                self.assertEqual(
                    {path: connector.read(path) for path in record_paths},
                    before_records,
                )
                self.assertEqual(
                    {path: connector.read(path) for path in paths},
                    before_targets,
                )

        with tempfile.TemporaryDirectory() as directory:
            connector = RecordingLocalConnector(Path(directory))
            for path, value in zip(paths, inputs, strict=True):
                if value is not None:
                    connector.write(path, value)
            self.assertEqual(execute_source(connector, "transactions", plan), "applied")
            transaction_root = connector.root / "transactions" / plan.transaction_id
            (transaction_root / "progress" / "000003.json").unlink()
            (transaction_root / "applied.json").unlink()
            connector.creates.clear()
            connector.writes.clear()
            connector.deletes.clear()

            self.assertEqual(recover_source(connector, "transactions", plan), "applied")
            self.assertEqual(
                connector.creates,
                [
                    f"{base}/progress/000003.json",
                    f"{base}/applied.json",
                ],
            )
            self.assertEqual(connector.writes, [])
            self.assertEqual(connector.deletes, [])

    def test_rollback_revision_drift_preserves_out_of_band_bytes(self) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        targets = (
            atlas_transaction.TransactionTarget(ARTIFACT_PATH, None, b"artifact-new"),
            atlas_transaction.TransactionTarget(
                atlas_state.RELATIONS_PATH,
                b"relations-old",
                b"relations-new",
            ),
        )
        plan = source_plan(
            event_path="events/source-upsert.json",
            event_record=record,
            targets=targets,
        )
        with tempfile.TemporaryDirectory() as directory:
            connector = RollbackDriftConnector(Path(directory))
            connector.write(atlas_state.RELATIONS_PATH, b"relations-old")
            self.assertEqual(execute_source(connector, "transactions", plan), "applied")
            (
                connector.root / "transactions" / plan.transaction_id / "applied.json"
            ).unlink()
            connector._path(ARTIFACT_PATH).unlink()
            connector.drift_path = atlas_state.RELATIONS_PATH
            with self.assertRaises(atlas_transaction.TransactionTargetConflict):
                recover_source(connector, "transactions", plan)
            self.assertIsNone(connector.read(ARTIFACT_PATH))
            self.assertEqual(
                connector.read(atlas_state.RELATIONS_PATH),
                connector.drift_bytes,
            )

    def test_transaction_failures_restore_or_commit_deterministically(self) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        paths = (
            ARTIFACT_PATH,
            atlas_state.RELATIONS_PATH,
            atlas_state.TOPICS_PATH,
            atlas_state.MANIFEST_PATH,
        )
        inputs = (None, b"relations-old", b"topics-old", b"manifest-old")
        outputs = (b"artifact-new", b"relations-new", b"topics-new", b"manifest-new")
        targets = tuple(
            atlas_transaction.TransactionTarget(path, before, after)
            for path, before, after in zip(paths, inputs, outputs, strict=True)
        )
        plan = source_plan(
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
                    status = execute_source(connector, "transactions", plan)
                    self.assertEqual(status, expected_status)
                    expected_values = outputs if status == "applied" else inputs
                    for path, expected in zip(paths, expected_values, strict=True):
                        self.assertEqual(connector.read(path), expected)
                    self.assertEqual(
                        recover_source(connector, "transactions", plan),
                        expected_status,
                    )
                    for path, expected in zip(paths, expected_values, strict=True):
                        self.assertEqual(connector.read(path), expected)

    def test_owner_post_validator_failure_rolls_back_before_applied_terminal(
        self,
    ) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        target = atlas_transaction.TransactionTarget(ARTIFACT_PATH, None, b"new")
        plan = source_plan(
            event_path="events/source-upsert.json",
            event_record=record,
            targets=(target,),
        )

        def reject_post_state(
            connector: atlas_transaction.ConnectorPort,
            transaction_plan: atlas_transaction.TransactionPlan,
        ) -> None:
            raise atlas_transaction.TransactionError("post-state mismatch")

        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            status = atlas_transaction.execute_transaction(
                connector,
                "transactions",
                plan,
                target_allowlist=source_target_allowed,
                target_rank=source_target_rank,
                post_validator=reject_post_state,
            )
            self.assertEqual(status, "rolled-back")
            self.assertIsNone(connector.read(ARTIFACT_PATH))
            base = f"transactions/{plan.transaction_id}"
            self.assertIsNone(connector.read(f"{base}/applied.json"))
            self.assertIsNotNone(connector.read(f"{base}/rolled-back.json"))

    def test_zero_target_collision_and_manual_conflict(self) -> None:
        record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=SOURCE_ID,
            event=source_event(),
            route_decision=None,
        )
        no_op = source_plan(
            event_path="events/source-upsert.json", event_record=record, targets=()
        )
        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            self.assertEqual(
                execute_source(connector, "transactions", no_op),
                "no-op",
            )

        target = atlas_transaction.TransactionTarget(ARTIFACT_PATH, None, b"new")
        plan = source_plan(
            event_path="events/source-upsert.json",
            event_record=record,
            targets=(target,),
        )
        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            base = f"transactions/{plan.transaction_id}"
            connector.create(
                f"{base}/intent.json",
                atlas_transaction.canonical_json(plan.intent),
            )
            self.assertEqual(
                recover_source(connector, "transactions", plan),
                "aborted",
            )
            self.assertIsNone(connector.read(f"{base}/backups/000000.json"))
            self.assertIsNone(connector.read(f"{base}/prepared.json"))
            self.assertIsNotNone(connector.read(f"{base}/aborted.json"))

        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            base = f"transactions/{plan.transaction_id}"
            connector.create(f"{base}/intent.json", b"collision\n")
            with self.assertRaises(atlas_transaction.TransactionError):
                execute_source(connector, "transactions", plan)
            self.assertEqual(connector.read(f"{base}/intent.json"), b"collision\n")

        with tempfile.TemporaryDirectory() as directory:
            connector = LocalConnector(Path(directory))
            base = f"transactions/{plan.transaction_id}"
            intent_raw = atlas_transaction.canonical_json(plan.intent)
            connector.create(f"{base}/intent.json", intent_raw)
            backup = atlas_transaction.canonical_json(
                {
                    "version": 1,
                    "path": ARTIFACT_PATH,
                    "input_sha256": None,
                    "input_base64": None,
                }
            )
            connector.create(f"{base}/backups/000000.json", backup)
            prepared = atlas_transaction.canonical_json(
                {
                    "version": 1,
                    "intent_sha256": atlas_transaction.sha256(intent_raw),
                    "backup_sha256s": [atlas_transaction.sha256(backup)],
                }
            )
            connector.create(f"{base}/prepared.json", prepared)
            connector.write(ARTIFACT_PATH, b"unexpected")
            self.assertEqual(
                recover_source(connector, "transactions", plan),
                "manual-conflict",
            )
            self.assertIsNotNone(connector.read(f"{base}/manual-conflict.json"))
            self.assertEqual(connector.read(ARTIFACT_PATH), b"unexpected")


def re_line(text: str, prefix: str) -> str:
    return next(line for line in text.splitlines() if line.startswith(prefix))


if __name__ == "__main__":
    unittest.main()
