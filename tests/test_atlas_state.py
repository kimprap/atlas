from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_state  # noqa: E402


HASH_A = "a" * 64
HASH_B = "b" * 64
SOURCE_ID = "123456789abc"
TOPIC_ID = "test-topic"
ARTIFACT = "summaries/sources/artifacts/2026/2026-07/example.md"
PASS_PATH = "summaries/research/test/topics/test-topic/passes/2026-07-15--pass.md"


def table(header: tuple[str, ...], rows: list[list[str]], *, newline: str = "\n", tail: str = "") -> str:
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


def manifest_row(*, content_hash: str = HASH_A, route_status: str = "unrouted") -> list[str]:
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
        "summaries/research/test/topics/test-topic/INDEX.md",
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


class AtlasStateTests(unittest.TestCase):
    def assert_valid(self, docs: dict[str, str]) -> None:
        self.assertEqual(
            atlas_state.validate_documents(
                docs["manifest"], docs["topics"], docs["relations"]
            ),
            [],
        )

    def test_orphan_relation_rows_fail_and_repair_moves_only_rows(self) -> None:
        row = relation_row()
        docs = documents(relations=[], state="current", route_status="routed")
        docs["topics"] = table(
            atlas_state.TOPICS_HEADER,
            [topic_row(state="dirty", pending=[row])],
        ) + "\n"
        docs["relations"] += (
            "\nUse these exact values.\n\n" + "| " + " | ".join(row) + " |\n"
        )
        findings = atlas_state.validate_documents(
            docs["manifest"], docs["topics"], docs["relations"]
        )
        self.assertEqual([finding.code for finding in findings], ["RELATION_ROW_OUTSIDE_TABLE"])

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

    def test_same_hash_route_does_not_reopen_applied_edge(self) -> None:
        applied = relation_row(status="applied", pass_path=PASS_PATH)
        docs = documents(relations=[applied], state="current")
        result = atlas_state.reduce_event(docs, route_event())
        self.assertTrue(result.ok, result.findings)
        self.assertEqual(result.derived[TOPIC_ID]["dirty_count"], 0)
        self.assertEqual(result.derived[TOPIC_ID]["source_watermark"], 1)
        self.assertNotIn("relations", result.documents)

    def test_changed_hash_supersedes_only_old_pending(self) -> None:
        pending = relation_row(status="pending")
        docs = documents(relations=[pending], state="dirty")
        result = atlas_state.reduce_event(docs, route_event(content_hash=HASH_B))
        self.assertTrue(result.ok, result.findings)
        parsed = atlas_state._parse_table("relations", result.documents["relations"])
        rows = [atlas_state._row_dict(atlas_state.RELATIONS_HEADER, row) for row in parsed.rows]
        old = next(row for row in rows if row["Source content hash"] == HASH_A)
        new = next(row for row in rows if row["Source content hash"] == HASH_B)
        self.assertEqual(old["Status"], "superseded")
        self.assertEqual(new["Status"], "pending")

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
            {"type": "refresh-fail", "topic_id": TOPIC_ID, "reason": "pass write failed"},
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
        after = atlas_state._parse_table("relations", result.documents["relations"]).rows[0]
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
        self.assertIn("EVENT_FIELD_UNKNOWN", {finding.code for finding in result.findings})

    def test_cli_json_is_byte_stable(self) -> None:
        docs = documents()
        bundle = {"version": 1, "documents": docs}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bundle.json"
            path.write_text(json.dumps(bundle), encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "scripts" / "atlas_state.py"),
                "validate",
                "--input",
                str(path),
            ]
            first = subprocess.run(command, check=False, capture_output=True)
            second = subprocess.run(command, check=False, capture_output=True)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, b"")
        self.assertEqual(json.loads(first.stdout), {"findings": [], "ok": True})

    def test_audit_instance_accepts_empty_scaffold_registries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {
                atlas_state.MANIFEST_PATH: table(atlas_state.MANIFEST_HEADER, []) + "\n",
                atlas_state.TOPICS_PATH: table(atlas_state.TOPICS_HEADER, []) + "\n",
                atlas_state.RELATIONS_PATH: table(atlas_state.RELATIONS_HEADER, []) + "\n",
            }
            for relative, text in paths.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
            self.assertEqual(atlas_state.audit_instance(root), [])


if __name__ == "__main__":
    unittest.main()
