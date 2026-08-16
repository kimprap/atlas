from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_state  # noqa: E402


HASH_A = "a" * 64
HASH_B = "b" * 64
SOURCE_ID = "190b4acf8d15"
TOPIC_ID = "test-topic"
ARTIFACT = "summaries/sources/artifacts/2026/2026-07/example.md"
PASS_PATH = (
    "summaries/research/test/test-subdomain/topics/test-topic/"
    "passes/2026-07-15--pass.md"
)


def table(
    header: tuple[str, ...],
    rows: list[list[str]],
    *,
    newline: str = "\n",
    tail: str = "",
) -> str:
    rendered = [
        "---",
        "schema_version: 1",
        "---",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "|".join("---" for _ in header) + "|",
    ]
    rendered.extend("| " + " | ".join(row) + " |" for row in rows)
    text = newline.join(rendered)
    if tail:
        text += newline + tail
    return text


def manifest_row(
    *, content_hash: str = HASH_A, route_status: str = "unrouted"
) -> list[str]:
    return [
        "1",
        SOURCE_ID,
        "https://example.com/source",
        ARTIFACT,
        "2026-07-15",
        "2026-07-15",
        "2026-07-15",
        content_hash,
        "2027-07-15",
        route_status,
        "active",
    ]


def relation_row(
    *,
    content_hash: str = HASH_A,
    status: str = "pending",
    pass_path: str = "",
    notes: str | None = None,
) -> list[str]:
    if notes is None:
        notes = (
            "Verifier: Heading Example — Source establishes the mechanism "
            "[relation=direct; impact=high]"
        )
    return [
        atlas_state._edge_id(SOURCE_ID, TOPIC_ID, content_hash),
        "1",
        SOURCE_ID,
        ARTIFACT,
        content_hash,
        TOPIC_ID,
        "direct",
        "high",
        "high",
        status,
        "2026-07-15",
        pass_path,
        notes,
    ]


def topic_row(
    *,
    state: str = "current",
    pending: list[list[str]] | None = None,
    applied: list[list[str]] | None = None,
    last_synthesized: str = "",
) -> list[str]:
    pending = pending or []
    applied = applied or []
    pending = sorted(pending, key=lambda row: (int(row[1]), row[0]))
    return [
        TOPIC_ID,
        "summaries/research/test/test-subdomain/topics/test-topic/INDEX.md",
        "test",
        "test-subdomain",
        "Test topic",
        "",
        "",
        "test",
        "",
        state,
        str(len(pending)),
        "; ".join(row[0] for row in pending),
        str(max((int(row[1]) for row in pending), default="")),
        last_synthesized,
        str(max((int(row[1]) for row in applied), default=0)),
        "same-as-topic-creation",
    ]


def documents(
    *,
    relations: list[list[str]] | None = None,
    state: str | None = None,
    content_hash: str = HASH_A,
    route_status: str | None = None,
    newline: str = "\n",
    final_newline: bool = True,
) -> dict[str, str]:
    relations = relations or []
    pending = [row for row in relations if row[9] == "pending"]
    applied = [row for row in relations if row[9] == "applied"]
    if state is None:
        state = "dirty" if pending else "current"
    if route_status is None:
        route_status = "routed" if pending or applied else "unrouted"
    values = {
        "manifest": table(
            atlas_state.MANIFEST_HEADER,
            [manifest_row(content_hash=content_hash, route_status=route_status)],
            newline=newline,
        ),
        "topics": table(
            atlas_state.TOPICS_HEADER,
            [topic_row(state=state, pending=pending, applied=applied)],
            newline=newline,
        ),
        "relations": table(atlas_state.RELATIONS_HEADER, relations, newline=newline),
    }
    if final_newline:
        values = {name: text + newline for name, text in values.items()}
    return values


def route_event(*, content_hash: str = HASH_A) -> dict[str, object]:
    return {
        "type": "route-upsert",
        "source_id": SOURCE_ID,
        "content_hash": content_hash,
        "checked_on": "2026-07-15",
        "outcome": "routed",
        "edges": [
            {
                "topic_id": TOPIC_ID,
                "relation": "direct",
                "impact": "high",
                "confidence": "high",
                "reason": (
                    "Verifier: Heading Example — Source establishes the mechanism "
                    "[relation=direct; impact=high]"
                ),
            }
        ],
    }


def empty_documents() -> dict[str, str]:
    return {
        "manifest": table(atlas_state.MANIFEST_HEADER, []) + "\n",
        "topics": table(atlas_state.TOPICS_HEADER, [topic_row(state="current")]) + "\n",
        "relations": table(atlas_state.RELATIONS_HEADER, []) + "\n",
    }


def source_event(
    *,
    url: str = "https://example.com/new-source",
    content_hash: str = HASH_A,
    artifact: str | None = None,
) -> dict[str, object]:
    source_id = atlas_state.source_id_for(url)
    if artifact is None:
        artifact = (
            "summaries/sources/artifacts/2026/2026-07/"
            f"2026-07-19--{source_id}--new-source.md"
        )
    return {
        "type": "source-upsert",
        "source_id": source_id,
        "canonical_url": url,
        "artifact": artifact,
        "first_seen": "2026-07-19",
        "checked_on": "2026-07-19",
        "summarized_on": "2026-07-19",
        "content_hash": content_hash,
        "refresh_after": "2027-07-19",
    }


def apply_result(
    docs: dict[str, str], result: atlas_state.ReductionResult
) -> dict[str, str]:
    return {**docs, **result.documents}


def managed_index(names: tuple[str, ...], *, label: str) -> str:
    lines = ["---", "schema_version: 1", "---", "", f"# {label}", ""]
    for name in names:
        lines.extend(
            [
                f"## {name}",
                f"<!-- atlas:managed:start {name} -->",
                f"{label} {name}",
                f"<!-- atlas:managed:end {name} -->",
                "",
            ]
        )
    return "\n".join(lines)


def inspection_revisions() -> dict[str, str]:
    return {
        "manifest": "sha256:" + "1" * 64,
        "topics": "sha256:" + "2" * 64,
        "relations": "sha256:" + "3" * 64,
    }


def inspection_artifacts(
    docs: dict[str, str], purpose: str
) -> dict[str, dict[str, str]]:
    paths = atlas_state.select_topic_state(docs, TOPIC_ID).paths_for(purpose)
    result: dict[str, dict[str, str]] = {}
    for index, path in enumerate(paths, 4):
        if path.endswith("/topics/test-topic/INDEX.md"):
            text = managed_index(atlas_state.TOPIC_MANAGED_SECTIONS, label="topic")
        elif path.endswith("/test-subdomain/INDEX.md"):
            text = managed_index(
                atlas_state.SUBDOMAIN_MANAGED_SECTIONS, label="subdomain"
            )
        else:
            text = "# Source summary\n\nEvidence.\n"
        result[path] = {
            "revision": "sha256:" + str(index) * 64,
            "text": text,
        }
    return result


class AtlasStateTests(unittest.TestCase):
    def assert_valid(self, docs: dict[str, str]) -> None:
        self.assertEqual(
            atlas_state.validate_documents(
                docs["manifest"], docs["topics"], docs["relations"]
            ),
            [],
        )

    def test_lookup_manifest_row_returns_canonical_hit(self) -> None:
        expected = dict(zip(atlas_state.MANIFEST_HEADER, manifest_row(), strict=True))
        found, findings = atlas_state.lookup_manifest_row(
            table(atlas_state.MANIFEST_HEADER, [manifest_row()]) + "\n",
            "https://example.com/source",
        )

        self.assertEqual(findings, [])
        self.assertEqual(found, expected)

    def test_lookup_manifest_row_returns_unambiguous_absence(self) -> None:
        found, findings = atlas_state.lookup_manifest_row(
            table(atlas_state.MANIFEST_HEADER, [manifest_row()]) + "\n",
            "https://example.com/absent",
        )

        self.assertEqual(findings, [])
        self.assertIsNone(found)

    def test_lookup_manifest_row_returns_archived_hit(self) -> None:
        archived = manifest_row()
        archived[-1] = "archived"
        found, findings = atlas_state.lookup_manifest_row(
            table(atlas_state.MANIFEST_HEADER, [archived]) + "\n",
            "https://example.com/source",
        )

        self.assertEqual(findings, [])
        self.assertIsNotNone(found)
        self.assertEqual(found["Status"], "archived")

    def test_lookup_manifest_row_rejects_malformed_and_duplicate_tables(self) -> None:
        row = manifest_row()
        malformed = (
            table(
                atlas_state.MANIFEST_HEADER,
                [row],
                tail="End.\n\n| " + " | ".join(row) + " |",
            )
            + "\n"
        )
        duplicate = table(atlas_state.MANIFEST_HEADER, [row, row]) + "\n"

        malformed_row, malformed_findings = atlas_state.lookup_manifest_row(
            malformed, "https://example.com/source"
        )
        duplicate_row, duplicate_findings = atlas_state.lookup_manifest_row(
            duplicate, "https://example.com/source"
        )

        self.assertIsNone(malformed_row)
        self.assertEqual(
            {finding.code for finding in malformed_findings},
            {"MANIFEST_ROW_OUTSIDE_TABLE"},
        )
        self.assertIsNone(duplicate_row)
        self.assertEqual(
            {finding.code for finding in duplicate_findings},
            {
                "MANIFEST_DUPLICATE_SOURCE_ID",
                "MANIFEST_DUPLICATE_SOURCE_SEQ",
                "MANIFEST_DUPLICATE_CANONICAL_URL",
            },
        )

    def test_lookup_manifest_row_rejects_invalid_noncanonical_and_mismatched_identity(
        self,
    ) -> None:
        cases = [
            ("not a URL", SOURCE_ID, "MANIFEST_CANONICAL_URL_INVALID"),
            (
                "https://EXAMPLE.com/source",
                SOURCE_ID,
                "MANIFEST_CANONICAL_URL_NOT_NORMALIZED",
            ),
            (
                "https://example.com/source",
                "ffffffffffff",
                "MANIFEST_SOURCE_ID_URL_MISMATCH",
            ),
        ]
        for url, source_id, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                row = manifest_row()
                row[1] = source_id
                row[2] = url
                found, findings = atlas_state.lookup_manifest_row(
                    table(atlas_state.MANIFEST_HEADER, [row]) + "\n",
                    "https://example.com/source",
                )

                self.assertIsNone(found)
                self.assertIn(expected_code, {finding.code for finding in findings})

    def test_orphan_relation_rows_fail_and_repair_moves_only_rows(self) -> None:
        row = relation_row()
        docs = documents(relations=[], state="current", route_status="routed")
        docs["topics"] = (
            table(
                atlas_state.TOPICS_HEADER,
                [topic_row(state="dirty", pending=[row])],
            )
            + "\n"
        )
        docs["relations"] += (
            "\nUse these exact values.\n\n" + "| " + " | ".join(row) + " |\n"
        )
        findings = atlas_state.validate_documents(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        self.assertEqual(
            [finding.code for finding in findings], ["RELATION_ROW_OUTSIDE_TABLE"]
        )

        result = atlas_state.reduce_event(
            docs, {"type": "repair-table-placement", "registry": "relations"}
        )
        self.assertTrue(result.ok)
        repaired = dict(docs)
        repaired.update(result.documents)
        self.assert_valid(repaired)
        self.assertLess(
            repaired["relations"].index(row[0]),
            repaired["relations"].index("Use these exact values."),
        )
        self.assertEqual(repaired["relations"].count(row[0]), 1)

    def test_route_inserts_inside_table_and_derives_cache(self) -> None:
        docs = documents()
        result = atlas_state.reduce_event(docs, route_event())
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived[TOPIC_ID]["dirty_count"], 1)
        edge_id = atlas_state._edge_id(SOURCE_ID, TOPIC_ID, HASH_A)
        self.assertEqual(result.derived[TOPIC_ID]["pending_edge_ids"], [edge_id])
        replacement = result.documents["relations"]
        self.assertIn(edge_id, replacement)
        self.assert_valid({**docs, **result.documents})

    def test_route_rejects_archived_source_and_manifest_hash_drift(self) -> None:
        archived = documents()
        archived["manifest"] = archived["manifest"].replace(
            "| active |", "| archived |"
        )
        archived_result = atlas_state.reduce_event(archived, route_event())
        self.assertFalse(archived_result.ok)
        self.assertEqual(archived_result.documents, {})
        self.assertEqual(
            [finding.code for finding in archived_result.findings],
            ["EVENT_SOURCE_ARCHIVED"],
        )

        mismatch_result = atlas_state.reduce_event(
            documents(), route_event(content_hash=HASH_B)
        )
        self.assertFalse(mismatch_result.ok)
        self.assertEqual(mismatch_result.documents, {})
        self.assertEqual(
            [finding.code for finding in mismatch_result.findings],
            ["EVENT_CONTENT_HASH_MISMATCH"],
        )

    def test_same_hash_route_does_not_reopen_applied_edge(self) -> None:
        applied = relation_row(status="applied", pass_path=PASS_PATH)
        docs = documents(relations=[applied], state="current")
        result = atlas_state.reduce_event(docs, route_event())
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived[TOPIC_ID]["dirty_count"], 0)
        self.assertEqual(result.derived[TOPIC_ID]["source_watermark"], 1)
        self.assertNotIn("relations", result.documents)

    def test_refresh_requires_complete_set_and_supports_start_complete(self) -> None:
        pending = relation_row()
        docs = documents(relations=[pending], state="dirty")
        bad = atlas_state.reduce_event(
            docs,
            {
                "type": "refresh-start",
                "topic_id": TOPIC_ID,
                "edge_ids": [],
                "started_at": "2026-07-15T00:00:00Z",
            },
        )
        self.assertFalse(bad.ok)
        self.assertEqual(bad.findings[0].code, "REFRESH_PENDING_SET_MISMATCH")

        edge_ids = [pending[0]]
        started = atlas_state.reduce_event(
            docs,
            {
                "type": "refresh-start",
                "topic_id": TOPIC_ID,
                "edge_ids": edge_ids,
                "started_at": "2026-07-15T00:00:00Z",
            },
        )
        self.assertTrue(started.ok, started.findings)
        refreshing = {**docs, **started.documents}
        self.assertEqual(started.derived[TOPIC_ID]["freshness_state"], "refreshing")

        completed = atlas_state.reduce_event(
            refreshing,
            {
                "type": "refresh-complete",
                "topic_id": TOPIC_ID,
                "edge_ids": edge_ids,
                "pass_path": PASS_PATH,
                "completed_on": "2026-07-15",
            },
        )
        self.assertTrue(completed.ok, completed.findings)
        self.assertEqual(completed.applied_edge_ids, edge_ids)
        self.assertEqual(completed.derived[TOPIC_ID]["freshness_state"], "current")
        self.assertEqual(completed.derived[TOPIC_ID]["dirty_count"], 0)
        self.assert_valid({**refreshing, **completed.documents})

    def test_refresh_fail_preserves_pending_and_blocks(self) -> None:
        pending = relation_row()
        docs = documents(relations=[pending], state="refreshing")
        result = atlas_state.reduce_event(
            docs,
            {
                "type": "refresh-fail",
                "topic_id": TOPIC_ID,
                "reason": "pass write failed",
            },
        )
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived[TOPIC_ID]["freshness_state"], "blocked")
        self.assertEqual(result.derived[TOPIC_ID]["pending_edge_ids"], [pending[0]])
        self.assertNotIn("relations", result.documents)

    def test_invalid_edge_id_and_cache_fail_deterministically(self) -> None:
        pending = relation_row()
        pending[0] = "edge--wrong"
        docs = documents(relations=[pending], state="dirty")
        first = atlas_state.validate_documents(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        second = atlas_state.validate_documents(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        self.assertEqual(first, second)
        self.assertIn("RELATION_EDGE_ID_INVALID", {finding.code for finding in first})

    def test_repair_notes_changes_only_notes(self) -> None:
        pending = relation_row(notes="old note")
        docs = documents(relations=[pending], state="dirty")
        reason = (
            "Verifier: Rule 1 — Source requires bounded state "
            "[relation=direct; impact=high]"
        )
        result = atlas_state.reduce_event(
            docs,
            {
                "type": "repair-relation-notes",
                "repairs": [{"edge_id": pending[0], "reason": reason}],
            },
        )
        self.assertTrue(result.ok, result.findings)
        before = atlas_state._parse_table("relations", docs["relations"]).rows[0]
        after = atlas_state._parse_table(
            "relations", result.documents["relations"]
        ).rows[0]
        self.assertEqual(before[:-1], after[:-1])
        self.assertEqual(after[-1], reason)

    def test_newline_and_final_newline_are_preserved(self) -> None:
        for newline in ("\n", "\r\n"):
            for final_newline in (True, False):
                with self.subTest(newline=repr(newline), final_newline=final_newline):
                    docs = documents(newline=newline, final_newline=final_newline)
                    result = atlas_state.reduce_event(docs, route_event())
                    self.assertTrue(result.ok, result.findings)
                    for replacement in result.documents.values():
                        self.assertEqual(replacement.endswith(newline), final_newline)
                        if newline == "\r\n":
                            self.assertNotIn("\n", replacement.replace("\r\n", ""))

    def test_unknown_event_field_fails_without_documents(self) -> None:
        event = route_event()
        event["provider"] = "forbidden"
        result = atlas_state.reduce_event(documents(), event)
        self.assertFalse(result.ok)
        self.assertEqual(result.documents, {})
        self.assertIn(
            "EVENT_FIELD_UNKNOWN", {finding.code for finding in result.findings}
        )

    def test_source_upsert_create_sequence_and_idempotent_replay(self) -> None:
        event = source_event()
        docs = empty_documents()
        result = atlas_state.reduce_event(docs, event)
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived["source"]["source_seq"], 1)
        self.assertTrue(result.derived["source"]["created"])
        candidate = apply_result(docs, result)
        self.assert_valid(candidate)

        replay = atlas_state.reduce_event(candidate, event)
        self.assertTrue(replay.ok, replay.findings)
        self.assertEqual(replay.documents, {})
        self.assertFalse(replay.derived["source"]["created"])
        self.assertFalse(replay.derived["source"]["content_changed"])

        second = atlas_state.reduce_event(documents(), source_event())
        self.assertTrue(second.ok, second.findings)
        self.assertEqual(second.derived["source"]["source_seq"], 2)

    def test_source_sequence_gaps_validate_and_allocate_after_max(self) -> None:
        second_url = "https://example.com/source-four"
        second = manifest_row()
        second[0] = "4"
        second[1] = atlas_state.source_id_for(second_url)
        second[2] = second_url
        second[3] = "summaries/sources/artifacts/2026/2026-07/source-four.md"
        docs = documents()
        docs["manifest"] = (
            table(
                atlas_state.MANIFEST_HEADER,
                [manifest_row(), second],
            )
            + "\n"
        )

        self.assert_valid(docs)
        result = atlas_state.reduce_event(docs, source_event())
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived["source"]["source_seq"], 5)

    def test_source_upsert_same_hash_preserves_route_history(self) -> None:
        event = source_event()
        docs = apply_result(
            empty_documents(), atlas_state.reduce_event(empty_documents(), event)
        )
        route = {
            "type": "route-upsert",
            "source_id": event["source_id"],
            "content_hash": HASH_A,
            "checked_on": "2026-07-19",
            "outcome": "routed",
            "edges": [
                {
                    "topic_id": TOPIC_ID,
                    "relation": "direct",
                    "impact": "high",
                    "confidence": "high",
                    "reason": (
                        "Verifier: Heading Example — Source establishes the mechanism "
                        "[relation=direct; impact=high]"
                    ),
                }
            ],
        }
        routed_result = atlas_state.reduce_event(docs, route)
        self.assertTrue(routed_result.ok, routed_result.findings)
        routed = apply_result(docs, routed_result)
        replay = atlas_state.reduce_event(routed, event)
        self.assertTrue(replay.ok, replay.findings)
        self.assertEqual(replay.documents, {})
        self.assertEqual(replay.derived["source"]["route_status"], "routed")

    def test_source_upsert_changed_hash_supersedes_pending_and_resets_route(
        self,
    ) -> None:
        initial_event = source_event()
        docs = empty_documents()
        docs = apply_result(docs, atlas_state.reduce_event(docs, initial_event))
        route = {
            "type": "route-upsert",
            "source_id": initial_event["source_id"],
            "content_hash": HASH_A,
            "checked_on": "2026-07-19",
            "outcome": "routed",
            "edges": [
                {
                    "topic_id": TOPIC_ID,
                    "relation": "direct",
                    "impact": "high",
                    "confidence": "high",
                    "reason": (
                        "Verifier: Heading Example — Source establishes the mechanism "
                        "[relation=direct; impact=high]"
                    ),
                }
            ],
        }
        docs = apply_result(docs, atlas_state.reduce_event(docs, route))
        changed = atlas_state.reduce_event(docs, source_event(content_hash=HASH_B))
        self.assertTrue(changed.ok, changed.findings)
        candidate = apply_result(docs, changed)
        self.assert_valid(candidate)
        manifest = atlas_state._parse_table("manifest", candidate["manifest"]).rows[0]
        relation = atlas_state._parse_table("relations", candidate["relations"]).rows[0]
        topic = atlas_state._parse_table("topics", candidate["topics"]).rows[0]
        self.assertEqual(manifest[9], "unrouted")
        self.assertEqual(relation[9], "superseded")
        self.assertEqual(topic[9:13], ["current", "0", "", ""])

    def test_source_upsert_rejects_identity_archive_dates_and_paths(self) -> None:
        mismatch = source_event()
        mismatch["source_id"] = "0" * 12
        result = atlas_state.reduce_event(empty_documents(), mismatch)
        self.assertFalse(result.ok)
        self.assertIn(
            "EVENT_SOURCE_ID_URL_MISMATCH", {item.code for item in result.findings}
        )

        invalid_date = source_event()
        invalid_date["checked_on"] = "2026-02-30"
        result = atlas_state.reduce_event(empty_documents(), invalid_date)
        self.assertFalse(result.ok)
        self.assertIn("EVENT_DATE_INVALID", {item.code for item in result.findings})

        source_id = source_event()["source_id"]
        invalid_paths = (
            f"/summaries/sources/artifacts/2026/2026-07/2026-07-19--{source_id}--x.md",
            f"vault://atlas/summaries/sources/artifacts/2026/2026-07/2026-07-19--{source_id}--x.md",
            f"summaries/sources/artifacts/tmp/2026-07/2026-07-19--{source_id}--x.md",
            f"summaries/sources/artifacts/2026/../2026-07/2026-07-19--{source_id}--x.md",
            f"summaries/other/artifacts/2026/2026-07/2026-07-19--{source_id}--x.md",
            "summaries/sources/artifacts/2026/2026-07/wrong.md",
        )
        for artifact in invalid_paths:
            with self.subTest(artifact=artifact):
                result = atlas_state.reduce_event(
                    empty_documents(), source_event(artifact=artifact)
                )
                self.assertFalse(result.ok)
                self.assertTrue(
                    any(
                        item.code.startswith("EVENT_ARTIFACT_PATH")
                        for item in result.findings
                    )
                )

        event = source_event()
        docs = apply_result(
            empty_documents(), atlas_state.reduce_event(empty_documents(), event)
        )
        docs["manifest"] = docs["manifest"].replace("| active |", "| archived |")
        result = atlas_state.reduce_event(docs, event)
        self.assertFalse(result.ok)
        self.assertIn("EVENT_SOURCE_ARCHIVED", {item.code for item in result.findings})

        mismatch_path = dict(event)
        mismatch_path["artifact"] = str(event["artifact"]).replace(
            "new-source.md", "other.md"
        )
        active_docs = docs.copy()
        active_docs["manifest"] = active_docs["manifest"].replace(
            "| archived |", "| active |"
        )
        result = atlas_state.reduce_event(active_docs, mismatch_path)
        self.assertFalse(result.ok)
        self.assertIn(
            "EVENT_ARTIFACT_PATH_MISMATCH", {item.code for item in result.findings}
        )

    def test_transaction_recovery_truth_table_and_reverse_restore_order(self) -> None:
        artifact = "summaries/sources/artifacts/new.md"
        manifest = atlas_state.MANIFEST_PATH
        intent = {
            "targets": [
                {"path": artifact, "input_sha256": None, "output_sha256": HASH_A},
                {"path": manifest, "input_sha256": HASH_A, "output_sha256": HASH_B},
            ]
        }
        inputs = {artifact: None, manifest: HASH_A}
        self.assertEqual(
            atlas_state.plan_transaction_recovery(intent, None, inputs).action,
            "prepare",
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                intent, None, inputs, abort=True
            ).action,
            "aborted",
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                intent, {"version": 1}, {artifact: HASH_A, manifest: HASH_B}
            ).action,
            "applied",
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                intent, {"version": 1}, inputs
            ).action,
            "rolled-back",
        )
        mixed = atlas_state.plan_transaction_recovery(
            intent, {"version": 1}, {artifact: HASH_A, manifest: HASH_A}
        )
        self.assertEqual(mixed.action, "rollback")
        self.assertEqual(mixed.restore_paths, [artifact])
        both_output = atlas_state.plan_transaction_recovery(
            intent, {"version": 1}, {artifact: HASH_A, manifest: HASH_B}
        )
        self.assertEqual(both_output.action, "applied")
        conflict = atlas_state.plan_transaction_recovery(
            intent, {"version": 1}, {artifact: "c" * 64, manifest: HASH_A}
        )
        self.assertEqual(conflict.action, "manual-conflict")

        rollback_both = atlas_state.plan_transaction_recovery(
            intent,
            {"version": 1},
            {artifact: HASH_A, manifest: HASH_B},
        )
        self.assertEqual(rollback_both.action, "applied")
        four = {
            "targets": [
                {"path": artifact, "input_sha256": None, "output_sha256": HASH_A},
                {
                    "path": atlas_state.RELATIONS_PATH,
                    "input_sha256": HASH_A,
                    "output_sha256": HASH_B,
                },
                {
                    "path": atlas_state.TOPICS_PATH,
                    "input_sha256": HASH_A,
                    "output_sha256": "c" * 64,
                },
                {"path": manifest, "input_sha256": HASH_A, "output_sha256": HASH_B},
            ]
        }
        rollback = atlas_state.plan_transaction_recovery(
            four,
            {"version": 1},
            {
                artifact: HASH_A,
                atlas_state.RELATIONS_PATH: HASH_B,
                atlas_state.TOPICS_PATH: HASH_A,
                manifest: HASH_B,
            },
        )
        self.assertEqual(
            rollback.restore_paths,
            [manifest, atlas_state.RELATIONS_PATH, artifact],
        )
        self.assertEqual(
            atlas_state.plan_transaction_recovery(
                {"targets": []}, {"version": 1}, {}
            ).action,
            "no-op",
        )

    def test_topics_list_candidate_a9_a10_codec_preservation_and_idempotence(
        self,
    ) -> None:
        pending = relation_row()
        for newline in ("\n", "\r\n"):
            for final_newline in (True, False):
                with self.subTest(newline=repr(newline), final_newline=final_newline):
                    docs = documents(
                        relations=[pending],
                        newline=newline,
                        final_newline=final_newline,
                    )
                    row = topic_row(
                        state="dirty",
                        pending=[pending],
                    )
                    row[5] = "z; a"
                    row[6] = "none"
                    row[7] = r"pipe\|value; semi\;colon"
                    row[8] = r"back\\\\slash; control\u{1}"
                    unmanaged = newline + "Unmanaged bytes — preserve exactly."
                    docs["topics"] = table(
                        atlas_state.TOPICS_HEADER,
                        [row],
                        newline=newline,
                        tail=unmanaged,
                    )
                    if final_newline:
                        docs["topics"] += newline
                    before = docs["topics"]
                    result = atlas_state.prepare_topics_list_candidate(
                        docs["manifest"], before, docs["relations"]
                    )
                    self.assertEqual(result.state, "candidate", result.findings)
                    self.assertIsNotNone(result.text)
                    self.assertEqual(result.text.endswith(newline), final_newline)
                    self.assertIn("Unmanaged bytes — preserve exactly.", result.text)
                    before_row = next(
                        atlas_state.split_markdown_row(line)
                        for line in before.splitlines()
                        if TOPIC_ID in line
                    )
                    after_row = next(
                        atlas_state.split_markdown_row(line)
                        for line in result.text.splitlines()
                        if TOPIC_ID in line
                    )
                    self.assertEqual(before_row[9:], after_row[9:])
                    replay = atlas_state.prepare_topics_list_candidate(
                        docs["manifest"], result.text, docs["relations"]
                    )
                    self.assertEqual(replay.state, "no-op", replay.findings)
                    self.assertIsNone(replay.text)
                    self.assertEqual(replay.changes, ())

        invalid_cases = {
            "blank": "a; ",
            "duplicate": "a; a",
            "dangling": "a\\",
            "unicode": r"a\u{x}",
            "surrogate": r"a\u{d800}",
        }
        for name, value in invalid_cases.items():
            with self.subTest(invalid=name):
                row = topic_row()
                row[5] = value
                docs = documents()
                docs["topics"] = table(atlas_state.TOPICS_HEADER, [row]) + "\n"
                result = atlas_state.prepare_topics_list_candidate(
                    docs["manifest"], docs["topics"], docs["relations"]
                )
                self.assertEqual(result.state, "invalid")
                self.assertIn(
                    {
                        "blank": "TOPICS_LIST_BLANK",
                        "duplicate": "TOPICS_LIST_DUPLICATE",
                        "dangling": "TOPICS_LIST_ESCAPE_INVALID",
                        "unicode": "TOPICS_LIST_ESCAPE_INVALID",
                        "surrogate": "TOPICS_LIST_SURROGATE",
                    }[name],
                    {finding.code for finding in result.findings},
                )

        row = topic_row()
        row[5] = r"question\?mark; z"
        docs = documents()
        docs["topics"] = table(atlas_state.TOPICS_HEADER, [row]) + "\n"
        escaped = atlas_state.prepare_topics_list_candidate(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        self.assertEqual(escaped.state, "candidate", escaped.findings)
        self.assertIn("question?mark; z", escaped.text)

    def test_topics_list_candidate_indexes_post_validation_rows_once(self) -> None:
        class CountingRows(list):
            def __init__(self, rows: list[object]) -> None:
                super().__init__(rows)
                self.iterations = 0

            def __iter__(self):
                self.iterations += 1
                return super().__iter__()

        rows = []
        for index in range(12):
            row = topic_row()
            topic_id = f"test-topic-{index:03d}"
            row[0] = topic_id
            row[1] = (
                f"summaries/research/test/test-subdomain/topics/{topic_id}/INDEX.md"
            )
            row[4] = f"Test topic {index:03d}"
            row[5:9] = ["z; a", "y; b", "x; c", "w; d"]
            rows.append(row)
        docs = documents()
        docs["topics"] = table(atlas_state.TOPICS_HEADER, rows) + "\n"

        original = atlas_state._topics_row_cell_spans
        calls = 0
        tracked_rows: list[CountingRows] = []

        def tracked(text: str):
            nonlocal calls
            calls += 1
            parsed = original(text)
            if calls == 2:
                counted = CountingRows(parsed)
                tracked_rows.append(counted)
                return counted
            return parsed

        with patch.object(atlas_state, "_topics_row_cell_spans", side_effect=tracked):
            result = atlas_state.prepare_topics_list_candidate(
                docs["manifest"], docs["topics"], docs["relations"]
            )
        self.assertEqual(result.state, "candidate", result.findings)
        self.assertEqual(calls, 2)
        self.assertEqual(tracked_rows[0].iterations, 1)

    def test_topics_list_candidate_combines_unrelated_findings_and_only_patches_targets(
        self,
    ) -> None:
        docs = documents()
        row = topic_row()
        row[5] = "z; a"
        row[10] = "7"
        docs["topics"] = (
            table(
                atlas_state.TOPICS_HEADER,
                [row],
                tail="\nPending edge lookalike and unmanaged note",
            )
            + "\n"
        )
        bad_manifest = docs["manifest"].replace(HASH_A, "not-a-hash")
        result = atlas_state.prepare_topics_list_candidate(
            bad_manifest, docs["topics"], docs["relations"]
        )
        self.assertEqual(result.state, "invalid")
        codes = {finding.code for finding in result.findings}
        self.assertIn("MANIFEST_CONTENT_HASH_INVALID", codes)
        self.assertNotEqual(codes, {"TOPICS_LIST_SEMANTIC_CHANGE"})

    def test_research_complete_updates_only_topic_synthesis_date(self) -> None:
        docs = documents()
        event = {
            "type": "research-complete",
            "topic_id": TOPIC_ID,
            "inspection_sha256": "1" * 64,
            "pass_path": (
                "summaries/research/test/test-subdomain/topics/test-topic/"
                "passes/2026-07-20--initial-research.md"
            ),
            "pass_sha256": "2" * 64,
            "topic_index_sha256": "3" * 64,
            "subdomain_index_sha256": "4" * 64,
            "completed_on": "2026-07-20",
        }
        result = atlas_state.reduce_event(docs, event)
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(set(result.documents), {"topics"})
        candidate = apply_result(docs, result)
        self.assertIn("2026-07-20", candidate["topics"])
        replay = atlas_state.reduce_event(candidate, event)
        self.assertTrue(replay.ok, replay.findings)
        self.assertEqual(replay.documents, {})

    def test_select_topic_state_classifies_all_published_states(self) -> None:
        pending = relation_row(status="pending")
        cases = {
            "current": documents(),
            "dirty": documents(relations=[pending], state="dirty"),
            "refreshing": documents(relations=[pending], state="refreshing"),
            "blocked": documents(relations=[pending], state="blocked"),
        }
        for expected, docs in cases.items():
            with self.subTest(expected=expected):
                selection = atlas_state.select_topic_state(docs, TOPIC_ID)
                self.assertEqual(selection.state, expected)
                self.assertEqual(selection.topic["topic_id"], TOPIC_ID)
                self.assertEqual(selection.findings, ())

        absent = documents()
        absent["topics"] = table(atlas_state.TOPICS_HEADER, []) + "\n"
        self.assertEqual(
            atlas_state.select_topic_state(absent, TOPIC_ID).state, "absent"
        )
        archived = documents(state="archived")
        archived_selection = atlas_state.select_topic_state(archived, TOPIC_ID)
        self.assertEqual(archived_selection.state, "absent")
        self.assertIsNone(archived_selection.topic)

        invalid = documents(state="dirty")
        invalid_selection = atlas_state.select_topic_state(invalid, TOPIC_ID)
        self.assertEqual(invalid_selection.state, "invalid")
        self.assertIsNone(invalid_selection.topic)
        self.assertTrue(invalid_selection.findings)

    def test_inspection_rejects_absent_and_invalid_without_partial_context(
        self,
    ) -> None:
        absent = documents()
        absent["topics"] = table(atlas_state.TOPICS_HEADER, []) + "\n"
        invalid = documents(state="dirty")
        for expected, docs in (
            ("TOPIC_INSPECTION_ABSENT", absent),
            ("TOPIC_INSPECTION_INVALID", invalid),
        ):
            with self.subTest(expected=expected):
                with self.assertRaises(atlas_state.TopicInspectionError) as caught:
                    atlas_state.inspect_topic(
                        docs, {}, TOPIC_ID, "answer", inspection_revisions()
                    )
                self.assertEqual(caught.exception.code, expected)

    def test_inspection_hash_changes_with_pending_ids_not_bodies(self) -> None:
        first_edge = relation_row(status="pending", content_hash=HASH_A)
        first_docs = documents(
            relations=[first_edge], state="dirty", content_hash=HASH_A
        )
        first_artifacts = inspection_artifacts(first_docs, "refresh")
        first = atlas_state.inspect_topic(
            first_docs,
            first_artifacts,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )

        changed_bodies = {
            path: {**artifact, "text": artifact["text"] + "\n"}
            for path, artifact in first_artifacts.items()
        }
        body_only = atlas_state.inspect_topic(
            first_docs,
            changed_bodies,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )
        self.assertEqual(first["inspection_sha256"], body_only["inspection_sha256"])

        second_edge = relation_row(status="pending", content_hash=HASH_B)
        second_docs = documents(
            relations=[second_edge], state="dirty", content_hash=HASH_B
        )
        second_artifacts = inspection_artifacts(second_docs, "refresh")
        second = atlas_state.inspect_topic(
            second_docs,
            second_artifacts,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )
        self.assertNotEqual(first["pending_edge_ids"], second["pending_edge_ids"])
        self.assertNotEqual(first["inspection_sha256"], second["inspection_sha256"])

    def test_answer_inspection_is_bounded_and_hash_excludes_bodies(self) -> None:
        docs = documents()
        artifacts = inspection_artifacts(docs, "answer")
        result = atlas_state.inspect_topic(
            docs, artifacts, TOPIC_ID, "answer", inspection_revisions()
        )
        self.assertEqual(result["purpose"], "answer")
        self.assertEqual(set(result["payload"]), {"managed_sections", "freshness"})
        self.assertEqual(result["relations"], [])
        self.assertEqual(len(result["artifact_revisions"]), 1)

        topic_path = topic_row()[1]
        changed = {
            **artifacts,
            topic_path: {
                **artifacts[topic_path],
                "text": artifacts[topic_path]["text"].replace(
                    "topic current-answer", "changed current-answer"
                ),
            },
        }
        same_binding = atlas_state.inspect_topic(
            docs, changed, TOPIC_ID, "answer", inspection_revisions()
        )
        self.assertEqual(result["inspection_sha256"], same_binding["inspection_sha256"])
        changed[topic_path] = {
            **changed[topic_path],
            "revision": "sha256:" + "9" * 64,
        }
        changed_binding = atlas_state.inspect_topic(
            docs, changed, TOPIC_ID, "answer", inspection_revisions()
        )
        self.assertNotEqual(
            result["inspection_sha256"], changed_binding["inspection_sha256"]
        )

    def test_research_and_refresh_inspections_select_only_related_sources(
        self,
    ) -> None:
        applied = relation_row(status="applied", pass_path=PASS_PATH)
        research_docs = documents(relations=[applied], state="current")
        research_artifacts = inspection_artifacts(research_docs, "research")
        research = atlas_state.inspect_topic(
            research_docs,
            research_artifacts,
            TOPIC_ID,
            "research",
            inspection_revisions(),
        )
        self.assertEqual(
            research["payload"]["source_summaries"][0]["source_id"], SOURCE_ID
        )
        self.assertIn("subdomain_index", research["payload"])
        self.assertEqual(research["pending_edge_ids"], [])

        pending = relation_row(status="pending")
        refresh_docs = documents(relations=[pending], state="dirty")
        refresh_artifacts = inspection_artifacts(refresh_docs, "refresh")
        refresh = atlas_state.inspect_topic(
            refresh_docs,
            refresh_artifacts,
            TOPIC_ID,
            "refresh",
            inspection_revisions(),
        )
        self.assertEqual(refresh["pending_edge_ids"], [pending[0]])
        self.assertEqual(
            refresh["payload"]["pending_edges"][0]["relation"]["edge_id"],
            pending[0],
        )
        self.assertNotIn("subdomain_index", refresh["payload"])

    def test_inspection_fails_without_partial_payload_for_missing_artifact(
        self,
    ) -> None:
        docs = documents()
        artifacts = inspection_artifacts(docs, "answer")
        artifacts.clear()
        with self.assertRaises(atlas_state.TopicInspectionError) as caught:
            atlas_state.inspect_topic(
                docs, artifacts, TOPIC_ID, "answer", inspection_revisions()
            )
        self.assertEqual(caught.exception.code, "TOPIC_INSPECTION_UNAVAILABLE")

    def test_audit_instance_accepts_empty_scaffold_registries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                atlas_state.MANIFEST_PATH: table(atlas_state.MANIFEST_HEADER, [])
                + "\n",
                atlas_state.TOPICS_PATH: table(atlas_state.TOPICS_HEADER, []) + "\n",
                atlas_state.RELATIONS_PATH: table(atlas_state.RELATIONS_HEADER, [])
                + "\n",
            }
            for relative, text in paths.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            self.assertEqual(atlas_state.audit_instance(root), [])


if __name__ == "__main__":
    unittest.main()
