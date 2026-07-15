from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_quality  # noqa: E402


CANONICAL = "https://example.com/source"
MEDIA = "https://example.com/media/pinned.gif"
EVAL_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "evals"
    / "source-summary-quality.json"
)


def checklist(*, failed: str | None = None) -> list[dict[str, str]]:
    return [
        {
            "id": item_id,
            "status": "fail" if item_id == failed else "pass",
            "evidence": "Rule A" if item_id != failed else "missing bounded evidence",
        }
        for item_id in atlas_quality.CHECKLIST_IDS
    ]


def evidence_bundle(**updates: object) -> dict[str, object]:
    bundle: dict[str, object] = {
        "version": 1,
        "canonical_url": CANONICAL,
        "source_urls": [],
        "allowed_urls": [],
        "media": [{"url": MEDIA, "fetched": True, "bound": "animation frames 1-10"}],
        "forbidden_context_terms": ["campaign alpha"],
        "checklist": checklist(),
        "require_routing_reason": True,
        "unresolved_validation_caveat": False,
    }
    bundle.update(updates)
    return bundle


def artifact(**frontmatter_updates: str) -> str:
    values = {
        "schema_version": "1",
        "note_type": "source-summary",
        "managed_by": "atlas",
        "source_id": "123456789abc",
        "source_seq": "1",
        "canonical_url": CANONICAL,
        "source_kind": "docs",
        "title": "Example source",
        "author": "Example author",
        "publisher": "Example publisher",
        "published": "Unknown",
        "primary_domain": "test",
        "subdomains": "[test-subdomain]",
        "secondary_domains": "[]",
        "canonical_tags": "[]",
        "candidate_terms": "[]",
        "routing_status": "routed",
        "routed_at": "2026-07-15",
        "first_seen": "2026-07-15",
        "last_checked": "2026-07-15",
        "last_summarized": "2026-07-15",
        "refresh_after": "2027-07-15",
        "content_hash": "a" * 64,
        "acquired_by": "manual",
        "acquisition_run": "",
        "coverage": "complete",
        "confidence": "high",
        "evidence_strength": "high",
        "practicality": "high",
        "stability": "stable",
        "reuse_value": "medium",
        "recommended_posture": "trial",
    }
    values.update(frontmatter_updates)
    frontmatter = "\n".join(f"{key}: {json.dumps(value)}" for key, value in values.items())
    return f"""---
{frontmatter}
---

# Example source

**Source**: [Example source]({CANONICAL})
**Source ID**: `123456789abc`
**Source seq**: `1`

> **TL;DR**: The source defines a typed tool boundary and names its validation limit.

## Assessment

| Signal | Value | Notes |
|---|---|---|
| Coverage | `complete` | The complete canonical page and pinned animation were inspected. |
| Confidence | `high` | Rule A and the example directly support the summary. |
| Evidence strength | `high` | Rule A supplies a concrete mechanism and locator. |
| Practicality | `high` | The rule and example are executable. |
| Stability | `stable` | The payload is immutable. |
| Reuse value | `medium` | It answers a bounded typed-tool question. |
| Recommended posture | `trial` | The mechanism needs bounded local evaluation. |

## Classification

- Primary domain: `test`
- Subdomains: `test-subdomain`

## Key points

- The application validates typed tool output before execution.
- The source does not establish comparative production performance.

## Approaches / mechanics

- Parse the model output, validate the typed shape, and then execute application code.

## Evidence / examples

- **Rule A**: Tool calls are structured outputs interpreted by deterministic application code.
- **Pinned animation**: The inspected asset demonstrates the bounded error exchange.

## Caveats / open questions

- The source supplies no independent comparative production validation.

## Routing notes

- Candidate topic matches considered: `test-topic`.
- Verifier: Rule A — Typed tool output creates the topic's control boundary [relation=direct; impact=high]

## Reuse cues

- How should an application validate model-selected tool calls before execution?

## Links

- Canonical: {CANONICAL}
- Referenced or inspected media: {MEDIA} — inspected pinned animation
"""


class AtlasQualityTests(unittest.TestCase):
    def test_valid_summary_and_checklist_pass(self) -> None:
        self.assertEqual(atlas_quality.validate_summary(artifact(), evidence_bundle()), [])

    def test_eval_asset_has_all_categories_and_context_pair(self) -> None:
        fixture = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        cases = atlas_quality._fixture_cases(fixture)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(fixture["assessment_cases"])
        self.assertTrue(fixture["summary_cases"])
        self.assertTrue(fixture["routing_cases"])
        self.assertTrue(fixture["negative_audit_cases"])
        groups: dict[str, list[dict[str, object]]] = {}
        for case in fixture["summary_cases"]:
            if "metamorphic_group" in case:
                groups.setdefault(case["metamorphic_group"], []).append(case)
        pair = groups["compact-errors-context-neutral"]
        self.assertEqual(len(pair), 2)
        self.assertEqual(pair[0]["evidence"], pair[1]["evidence"])
        self.assertEqual(pair[0]["expected"]["assessment"], pair[1]["expected"]["assessment"])
        self.assertEqual(pair[0]["expected"]["required_claims"], pair[1]["expected"]["required_claims"])

    def test_semantic_boundary_flags_ambient_context_only_in_semantic_sections(self) -> None:
        semantic = artifact().replace(
            "- The application validates typed tool output before execution.",
            "- Campaign alpha validates typed tool output before execution.",
        )
        findings = atlas_quality.validate_summary(semantic, evidence_bundle())
        self.assertIn("AMBIENT_CONTEXT_LEAK", {finding.code for finding in findings})

        annotation = artifact().replace(
            "- Primary domain: `test`",
            "- Primary domain: `test`\n- Annotation note: campaign alpha",
        )
        findings = atlas_quality.validate_summary(annotation, evidence_bundle())
        self.assertNotIn("AMBIENT_CONTEXT_LEAK", {finding.code for finding in findings})

    def test_repository_context_and_generated_context_are_rejected(self) -> None:
        text = artifact().replace(
            "- The application validates typed tool output before execution.",
            "- This task uses vault://atlas/ because it was selected explicitly for T5.",
        )
        codes = {finding.code for finding in atlas_quality.validate_summary(text, evidence_bundle())}
        self.assertIn("GENERATED_CONTEXT_LEAK", codes)
        self.assertIn("REPOSITORY_CONTEXT_LEAK", codes)

    def test_url_and_media_must_belong_to_fetched_ledger(self) -> None:
        text = artifact().replace(MEDIA, "https://example.com/media/reconstructed.gif")
        codes = {finding.code for finding in atlas_quality.validate_summary(text, evidence_bundle())}
        self.assertIn("URL_OUTSIDE_EVIDENCE", codes)

        unfetched = evidence_bundle(
            media=[{"url": MEDIA, "fetched": False, "bound": "unavailable"}]
        )
        codes = {finding.code for finding in atlas_quality.validate_summary(artifact(), unfetched)}
        self.assertIn("EVIDENCE_MEDIA_NOT_FETCHED", codes)
        self.assertIn("URL_OUTSIDE_EVIDENCE", codes)

    def test_duplicate_placeholder_and_adoption_coupling(self) -> None:
        duplicated = artifact().replace(
            "- The source does not establish comparative production performance.",
            "- The application validates typed tool output before execution.",
        )
        codes = {finding.code for finding in atlas_quality.validate_summary(duplicated, evidence_bundle())}
        self.assertIn("EXACT_NORMALIZED_DUPLICATE", codes)

        placeholder = artifact().replace("Example source", "<resource title>", 1)
        codes = {finding.code for finding in atlas_quality.validate_summary(placeholder, evidence_bundle())}
        self.assertIn("PLACEHOLDER_UNRESOLVED", codes)

        invalid_adopt = artifact(
            evidence_strength="medium",
            recommended_posture="adopt",
        ).replace(
            "| Evidence strength | `high` |",
            "| Evidence strength | `medium` |",
        ).replace(
            "| Recommended posture | `trial` |",
            "| Recommended posture | `adopt` |",
        )
        codes = {finding.code for finding in atlas_quality.validate_summary(invalid_adopt, evidence_bundle())}
        self.assertIn("ADOPT_COUPLING_INVALID", codes)

    def test_high_evidence_requires_source_locator(self) -> None:
        text = artifact().replace("- **Rule A**:", "- The rule says")
        text = text.replace("- **Pinned animation**:", "- The animation shows")
        codes = {finding.code for finding in atlas_quality.validate_summary(text, evidence_bundle())}
        self.assertIn("SOURCE_LOCATOR_MISSING", codes)

    def test_routing_reason_positive_and_near_miss(self) -> None:
        self.assertEqual(atlas_quality.validate_summary(artifact(), evidence_bundle()), [])
        candidate_only = artifact().replace(
            "- Verifier: Rule A — Typed tool output creates the topic's control boundary [relation=direct; impact=high]",
            "- Candidate topic matches considered: `test-topic`, `other-topic`.",
        )
        codes = {finding.code for finding in atlas_quality.validate_summary(candidate_only, evidence_bundle())}
        self.assertIn("ROUTING_REASON_MISSING", codes)
        self.assertIn("ROUTING_CANDIDATE_ONLY", codes)

        mismatch = artifact().replace("impact=high]", "impact=medium]")
        codes = {finding.code for finding in atlas_quality.validate_summary(mismatch, evidence_bundle())}
        self.assertNotIn("ROUTING_REASON_INVALID", codes)
        fixture = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        near_miss = next(case for case in fixture["routing_cases"] if case["id"] == "route-reason-impact-mismatch")
        self.assertIn("routing-reason-row-mismatch", near_miss["expected"]["failure_ids"])

    def test_checklist_shape_missing_unknown_duplicate_and_fail(self) -> None:
        self.assertEqual(atlas_quality.validate_checklist(checklist()), [])

        missing = checklist()[:-1]
        codes = {finding.code for finding in atlas_quality.validate_checklist(missing)}
        self.assertIn("CHECKLIST_LENGTH_INVALID", codes)
        self.assertIn("CHECKLIST_ORDER_INVALID", codes)

        unknown = checklist()
        unknown[-1]["id"] = "unknown"
        codes = {finding.code for finding in atlas_quality.validate_checklist(unknown)}
        self.assertIn("CHECKLIST_ID_UNKNOWN", codes)

        duplicate = checklist()
        duplicate[-1]["id"] = duplicate[0]["id"]
        codes = {finding.code for finding in atlas_quality.validate_checklist(duplicate)}
        self.assertIn("CHECKLIST_ID_DUPLICATE", codes)

        failed = checklist(failed="limits-uncertainty")
        findings = atlas_quality.validate_checklist(failed)
        self.assertEqual(
            [finding.detail for finding in findings if finding.code == "CHECKLIST_ITEM_FAILED"],
            ["limits-uncertainty"],
        )

    def test_calibration_exact_compare_and_failure(self) -> None:
        fixture_text = EVAL_PATH.read_text(encoding="utf-8")
        fixture = json.loads(fixture_text)
        results = [
            {"id": case["id"], "actual": deepcopy(case["expected"])}
            for case in atlas_quality._fixture_cases(fixture)
        ]
        response = json.dumps({"version": 1, "results": results})
        self.assertEqual(atlas_quality.validate_calibration(fixture_text, response), [])

        results[0]["actual"] = {"coverage": "failed"}
        findings = atlas_quality.validate_calibration(
            fixture_text, json.dumps({"version": 1, "results": results})
        )
        self.assertEqual([finding.code for finding in findings], ["CALIBRATION_RESULT_MISMATCH"])

    def test_cli_json_is_deterministic(self) -> None:
        payload = {
            "version": 1,
            "artifact_text": artifact(),
            "evidence_bundle": evidence_bundle(),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "quality.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "scripts" / "atlas_quality.py"),
                "validate-summary",
                "--input",
                str(path),
            ]
            first = subprocess.run(command, check=False, capture_output=True)
            second = subprocess.run(command, check=False, capture_output=True)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, b"")
        self.assertEqual(json.loads(first.stdout), {"findings": [], "ok": True})


if __name__ == "__main__":
    unittest.main()
