from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

try:
    import jsonschema
except ImportError:  # Optional test-only schema verifier.
    jsonschema = None


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_quality  # noqa: E402


CANONICAL = "https://example.com/source"
RELATED = "https://example.com/related"
DEFAULT_PAYLOAD = "Example source payload for quality validation."
DEFAULT_HASH = hashlib.sha256(DEFAULT_PAYLOAD.encode("utf-8")).hexdigest()
COMPLETE_BODY = "PREFIX " + DEFAULT_PAYLOAD + " SUFFIX"
COMPLETE_HASH = hashlib.sha256(COMPLETE_BODY.encode("utf-8")).hexdigest()
PAYLOAD_START = COMPLETE_BODY.encode("utf-8").index(DEFAULT_PAYLOAD.encode("utf-8"))
PAYLOAD_END = PAYLOAD_START + len(DEFAULT_PAYLOAD.encode("utf-8"))
EVAL_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "evals"
    / "source-summary-quality.json"
)
GUIDE_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "source-summary-quality-guide.md"
)
SKILL_PATH = ROOT / ".agents" / "skills" / "atlas-source" / "SKILL.md"
AGENT_TOOLING_EVAL_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "evals"
    / "agent-tooling.json"
)
PROPOSAL_SCHEMA_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "source-summary-proposal.schema.json"
)
FRESH_ASSESSMENT_SCHEMA_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "fresh-source-assessment.schema.json"
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
        "source_urls": [RELATED],
        "allowed_urls": [],
        "forbidden_context_terms": ["campaign alpha"],
        "payload_text": DEFAULT_PAYLOAD,
        "require_routing_reason": True,
        "unresolved_validation_caveat": False,
    }
    bundle.update(updates)
    return bundle


def projected_bundle(**updates: object) -> dict[str, object]:
    bundle = evidence_bundle(
        payload_text=DEFAULT_PAYLOAD,
        content_hash=COMPLETE_HASH,
        payload_projection=True,
        complete_text=COMPLETE_BODY,
        projection_ranges=[[PAYLOAD_START, PAYLOAD_END]],
    )
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
        "subdomains": '["test-subdomain"]',
        "secondary_domains": "[]",
        "canonical_tags": "[]",
        "candidate_terms": "[]",
        "routing_status": "routed",
        "routed_at": "2026-07-15",
        "first_seen": "2026-07-15",
        "last_checked": "2026-07-15",
        "last_summarized": "2026-07-15",
        "refresh_after": "2027-07-15",
        "content_hash": DEFAULT_HASH,
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
    native_keys = (
        atlas_quality.INTEGER_FRONTMATTER_KEYS | atlas_quality.LIST_FRONTMATTER_KEYS
    )
    frontmatter = "\n".join(
        f"{key}: {value}" if key in native_keys else f"{key}: {json.dumps(value)}"
        for key, value in values.items()
    )
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
| Coverage | `complete` | The complete canonical text payload was read. |
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
- **Related docs**: The source points to {RELATED} for optional background.

## Caveats / open questions

- The source supplies no independent comparative production validation.

## Routing notes

- Candidate topic matches considered: `test-topic`.
- Verifier: Rule A — Typed tool output creates the topic's control boundary [relation=direct; impact=high]

## Reuse cues

- How should an application validate model-selected tool calls before execution?

## Links

- Canonical: {CANONICAL}
- Related textual source links: {RELATED} — optional background named in the source
"""


def codes_for(
    text: str | None = None,
    bundle: dict[str, object] | None = None,
    items: list | None = None,
) -> set[str]:
    return {
        finding.code
        for finding in atlas_quality.validate_summary(
            artifact() if text is None else text,
            evidence_bundle() if bundle is None else bundle,
            checklist() if items is None else items,
        )
    }


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def proposal() -> dict[str, object]:
    return {
        "version": 1,
        "metadata": {
            "title": "Synthetic proposal",
            "author": "Synthetic author",
            "publisher": "Synthetic publisher",
            "published": "2026-05",
            "source_kind": "article",
        },
        "assessment": {
            "coverage": "complete",
            "confidence": "high",
            "evidence_strength": "high",
            "practicality": "high",
            "stability": "stable",
            "reuse_value": "medium",
            "recommended_posture": "trial",
        },
        "claims": [
            {
                "statement": "A synthetic claim has a source-local evidence reference.",
                "evidence": [{"locator": "section-a", "ledger_id": "evidence-a"}],
            }
        ],
        "links": [
            {
                "url": CANONICAL,
                "relation": "canonical",
                "locator": "canonical-link",
                "ledger_id": "link-a",
            }
        ],
    }


def proposal_ledger() -> dict[str, object]:
    return {
        "version": 1,
        "evidence": [{"locator": "section-a", "ledger_id": "evidence-a"}],
        "links": [
            {
                "url": CANONICAL,
                "locator": "canonical-link",
                "ledger_id": "link-a",
            }
        ],
    }


def fresh_assessment() -> dict[str, object]:
    text = "Synthetic text."
    text_hash = digest(text)
    excerpt_hash = digest("Synthetic")
    manifest_row_hash = digest("manifest-row")
    packet_hash = digest("packet")
    capture_hash = digest("capture")
    ledger_hash = digest("ledger")
    assessment_hash = digest("assessment")
    review_hash = digest("review")
    candidate_hash = digest("candidate")
    return {
        "version": 1,
        "freeze": {
            "source_id": "123456789abc",
            "source_seq": 1,
            "canonical_url": CANONICAL,
            "manifest_row_hash": manifest_row_hash,
            "artifact_revision": f"sha256:{digest('artifact')}",
            "snapshot_hash": digest("snapshot"),
        },
        "packet": {
            "packet_sha256": packet_hash,
            "capture_sha256": capture_hash,
            "text_blob_sha256": text_hash,
            "ledger_sha256": ledger_hash,
            "rubric_version": 1,
        },
        "capture": {
            "state": "completed",
            "access": "available",
            "representation": "readable-text",
            "text_blob_sha256": text_hash,
            "final_url": CANONICAL,
            "http_status": 200,
        },
        "identity_alignment": {
            "normalized_final_url": "same",
            "page_declared_canonical": "same",
            "evidence_strength": "high",
        },
        "page_form": "standalone",
        "page_summary_adequacy": {
            "value": "sufficient",
            "page_supports": ["excerpt-a"],
        },
        "resource_intent": {
            "kind": "declared",
            "declared_text": "A bounded synthetic resource.",
            "provenance": "excerpt-a",
            "fit": "misses",
            "missing_for_resource_intent": [],
        },
        "dimensions": {
            "capture": {"state": "pass", "evidence_refs": ["excerpt-a"]},
            "identity": {"state": "pass", "evidence_refs": ["link-a"]},
            "page_form": {"state": "pass", "evidence_refs": ["excerpt-a"]},
            "adequacy": {"state": "pass", "evidence_refs": ["excerpt-a"]},
            "intent": {"state": "fail", "evidence_refs": ["excerpt-a"]},
        },
        "findings": [
            {
                "code": "thin-standalone",
                "dimensions": ["page_form", "adequacy", "intent"],
                "evidence_refs": ["excerpt-a"],
            }
        ],
        "evidence": {
            "excerpts": [
                {
                    "id": "excerpt-a",
                    "blob_sha256": text_hash,
                    "start_byte": 0,
                    "end_byte": 9,
                    "excerpt_sha256": excerpt_hash,
                }
            ],
            "links": [
                {
                    "id": "link-a",
                    "canonical_url": RELATED,
                    "source_id": None,
                    "anchor": "Related synthetic link",
                    "locator": "section-a",
                    "normalization_status": "accepted",
                    "raw_href_sha256": digest("related-href"),
                    "display": "Related synthetic link",
                    "reason": None,
                }
            ],
        },
        "review": {
            "primary": {
                "review_id": "primary-a",
                "assessment_sha256": assessment_hash,
                "packet_sha256": packet_hash,
                "blinded": True,
                "verdict": "flagged",
            },
            "secondary": None,
        },
        "actions": {
            "allowed": ["queue-resolution"],
            "recommended": ["queue-resolution"],
            "write_set": ["assessment-record"],
        },
        "drift": {
            "frozen_manifest_row_hash": manifest_row_hash,
            "observed_manifest_row_hash": manifest_row_hash,
            "status": "same",
        },
        "index": {
            "assessment_index_sha256": digest("assessment-index"),
            "source_ids": ["123456789abc"],
            "source_count": 1,
            "terminal_count": 1,
            "assessment_sha256": assessment_hash,
            "review_sha256": review_hash,
            "candidate_sha256": candidate_hash,
        },
    }


def fresh_packet(assessment_value: dict[str, object]) -> dict[str, object]:
    packet = assessment_value["packet"]
    assert isinstance(packet, dict)
    return {
        "version": 1,
        "freeze": deepcopy(assessment_value["freeze"]),
        "packet_sha256": packet["packet_sha256"],
        "capture_sha256": packet["capture_sha256"],
        "text_blob_sha256": packet["text_blob_sha256"],
        "ledger_sha256": packet["ledger_sha256"],
        "rubric_version": 1,
        "text_blobs": [
            {"sha256": packet["text_blob_sha256"], "utf8_text": "Synthetic text."}
        ],
        "links": deepcopy(assessment_value["evidence"]["links"]),
    }


class AtlasQualityTests(unittest.TestCase):
    def test_valid_summary_and_checklist_pass(self) -> None:
        self.assertEqual(
            atlas_quality.validate_summary(artifact(), evidence_bundle(), checklist()),
            [],
        )

    def test_publication_date_accepts_reduced_month_precision(self) -> None:
        self.assertNotIn(
            "FRONTMATTER_DATE_INVALID",
            codes_for(text=artifact(published="2026-05")),
        )
        self.assertNotIn(
            "FRONTMATTER_DATE_INVALID",
            codes_for(text=artifact(published="2026-05-01")),
        )
        self.assertIn(
            "FRONTMATTER_DATE_INVALID",
            codes_for(text=artifact(published="May 2026")),
        )
        self.assertIn(
            "FRONTMATTER_DATE_INVALID",
            codes_for(text=artifact(published="2026")),
        )

    def test_frontmatter_requires_native_integer_and_list_shapes(self) -> None:
        quoted_integer = artifact().replace("schema_version: 1", 'schema_version: "1"')
        quoted_list = artifact().replace("candidate_terms: []", 'candidate_terms: "[]"')
        scalar_list = artifact().replace(
            "candidate_terms: []", 'candidate_terms: "agent tooling"'
        )
        self.assertIn(
            "FRONTMATTER_INTEGER_TYPE_INVALID", codes_for(text=quoted_integer)
        )
        self.assertIn("FRONTMATTER_LIST_TYPE_INVALID", codes_for(text=quoted_list))
        self.assertIn("FRONTMATTER_LIST_TYPE_INVALID", codes_for(text=scalar_list))

    def test_assessment_rejects_known_generic_notes(self) -> None:
        text = artifact().replace(
            "The payload is immutable.",
            "The canonical delivery surface determines the selected stability.",
        )
        self.assertIn("ASSESSMENT_NOTE_BOILERPLATE", codes_for(text=text))

    def test_template_annotation_headings_are_canonical_sections(self) -> None:
        text = (
            artifact()
            .replace(
                "## Classification",
                "## Classification (post-draft Atlas annotation)",
            )
            .replace(
                "## Routing notes",
                "## Routing notes (post-draft Atlas annotation)",
            )
        )
        self.assertEqual(
            atlas_quality.validate_summary(text, evidence_bundle(), checklist()),
            [],
        )

    def test_eval_asset_has_all_categories_and_context_pair(self) -> None:
        fixture = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        cases = atlas_quality._fixture_cases(fixture)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), 44)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(fixture["assessment_cases"]), 7)
        self.assertEqual(len(fixture["summary_cases"]), 14)
        self.assertEqual(len(fixture["routing_cases"]), 3)
        self.assertEqual(len(fixture["negative_audit_cases"]), 20)
        groups: dict[str, list[dict[str, object]]] = {}
        for case in fixture["summary_cases"]:
            if "metamorphic_group" in case:
                groups.setdefault(case["metamorphic_group"], []).append(case)
        pair = groups["compact-errors-context-neutral"]
        self.assertEqual(len(pair), 2)
        self.assertEqual(pair[0]["evidence"], pair[1]["evidence"])
        self.assertEqual(
            pair[0]["expected"]["assessment"], pair[1]["expected"]["assessment"]
        )
        self.assertEqual(
            pair[0]["expected"]["required_claims"],
            pair[1]["expected"]["required_claims"],
        )

        expected_new_ids = {
            "assessment-database-data-coherence",
            "assessment-geospatial-partial-coverage",
            "summary-product-design-primary-contribution",
            "summary-frontend-observability-source-support",
            "summary-markets-backtest-live-uncertainty",
            "summary-knowledge-context-conflicting-claims",
            "audit-untrusted-ignore-template",
            "audit-untrusted-disclosure-request",
            "audit-inaccessible-text-no-write",
            "audit-thin-insufficient-text-no-write",
            "audit-aggregate-page-scope-required",
            "audit-aggregate-page-only-no-child-bodies",
            "audit-normal-article-not-aggregate",
            "audit-explicit-timestamp-publication-date",
            "audit-reduced-precision-publication-date",
        }
        self.assertTrue(expected_new_ids.issubset(ids))
        aggregate_scope = next(
            case
            for case in fixture["negative_audit_cases"]
            if case["id"] == "audit-aggregate-page-scope-required"
        )
        self.assertEqual(
            aggregate_scope["expected"]["recommended_choice"],
            "page-only",
        )
        untrusted = [
            case
            for case in fixture["negative_audit_cases"]
            if case["id"]
            in {"audit-untrusted-ignore-template", "audit-untrusted-disclosure-request"}
        ]
        self.assertEqual(len(untrusted), 2)
        for case in untrusted:
            self.assertEqual(
                case["expected"],
                {
                    "failure_ids": ["evidence-boundary", "context-neutrality"],
                    "defect_codes": ["untrusted-instruction-followed"],
                },
            )

    def test_quality_guide_declares_untrusted_prompt_boundaries(self) -> None:
        text = GUIDE_PATH.read_text(encoding="utf-8")
        self.assertIn("BEGIN_UNTRUSTED_EVIDENCE_BUNDLE_JSON", text)
        self.assertIn("END_UNTRUSTED_EVIDENCE_BUNDLE_JSON", text)
        self.assertIn("BEGIN_UNTRUSTED_ARTIFACT_<LABEL>", text)
        self.assertIn("END_UNTRUSTED_ARTIFACT_<LABEL>", text)
        self.assertIn("untrusted-instruction-followed", text)

    def test_semantic_boundary_flags_ambient_context_only_in_semantic_sections(
        self,
    ) -> None:
        semantic = artifact().replace(
            "- The application validates typed tool output before execution.",
            "- Campaign alpha validates typed tool output before execution.",
        )
        findings = atlas_quality.validate_summary(
            semantic, evidence_bundle(), checklist()
        )
        self.assertIn("AMBIENT_CONTEXT_LEAK", {finding.code for finding in findings})

        annotation = artifact().replace(
            "- Primary domain: `test`",
            "- Primary domain: `test`\n- Annotation note: campaign alpha",
        )
        findings = atlas_quality.validate_summary(
            annotation, evidence_bundle(), checklist()
        )
        self.assertNotIn("AMBIENT_CONTEXT_LEAK", {finding.code for finding in findings})

    def test_repository_context_and_generated_context_are_rejected(self) -> None:
        text = artifact().replace(
            "- The application validates typed tool output before execution.",
            "- This task uses vault://atlas/ because it was selected explicitly for T5.",
        )
        self.assertIn("GENERATED_CONTEXT_LEAK", codes_for(text))
        self.assertIn("REPOSITORY_CONTEXT_LEAK", codes_for(text))

    def test_source_attributed_active_model_is_not_repository_context(self) -> None:
        text = artifact().replace(
            "- The application validates typed tool output before execution.",
            "- The source says each harness component encodes an assumption about what the active model cannot do alone.",
        )
        self.assertNotIn("REPOSITORY_CONTEXT_LEAK", codes_for(text))

    def test_url_must_belong_to_text_evidence_ledger(self) -> None:
        text = artifact().replace(RELATED, "https://example.com/not-in-evidence")
        self.assertIn("URL_OUTSIDE_EVIDENCE", codes_for(text))

    def test_media_and_binary_asset_fields_are_rejected(self) -> None:
        for field, value in (
            ("media", [{"url": "https://example.com/x.gif", "fetched": True}]),
            ("binary_content", "AAAA"),
            ("assets", [{"path": "/tmp/x.png"}]),
            ("screenshot", "data:image/png;base64,AAA"),
        ):
            codes = codes_for(bundle=evidence_bundle(**{field: value}))
            self.assertIn("EVIDENCE_MEDIA_ASSET_REJECTED", codes, field)
            effective, findings = atlas_quality.resolve_effective_content_hash(
                evidence_bundle(**{field: value})
            )
            self.assertIsNone(effective)
            self.assertTrue(
                any(f.code == "EVIDENCE_MEDIA_ASSET_REJECTED" for f in findings)
            )

        # Empty media list is treated as absent and does not fail.
        self.assertEqual(
            atlas_quality.validate_summary(
                artifact(),
                evidence_bundle(media=[]),
                checklist(),
            ),
            [],
        )

    def test_exact_payload_url_is_inside_evidence_boundary(self) -> None:
        payload_url = "https://example.com/source.git@vX.Y.Z"
        payload = f"Install with {payload_url}"
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        text = artifact(content_hash=payload_hash).replace(
            "- The application validates typed tool output before execution.",
            f"- The source installs from {payload_url}.",
        )
        codes = codes_for(text=text, bundle=evidence_bundle(payload_text=payload))
        self.assertNotIn("URL_OUTSIDE_EVIDENCE", codes)
        self.assertNotIn("CONTENT_HASH_MISMATCH", codes)

    def test_duplicate_placeholder_and_adoption_coupling(self) -> None:
        duplicated = artifact().replace(
            "- The source does not establish comparative production performance.",
            "- The application validates typed tool output before execution.",
        )
        self.assertIn("EXACT_NORMALIZED_DUPLICATE", codes_for(duplicated))

        placeholder = artifact().replace("Example source", "<resource title>", 1)
        self.assertIn("PLACEHOLDER_UNRESOLVED", codes_for(placeholder))

        invalid_adopt = (
            artifact(
                evidence_strength="medium",
                recommended_posture="adopt",
            )
            .replace(
                "| Evidence strength | `high` |",
                "| Evidence strength | `medium` |",
            )
            .replace(
                "| Recommended posture | `trial` |",
                "| Recommended posture | `adopt` |",
            )
        )
        self.assertIn("ADOPT_COUPLING_INVALID", codes_for(invalid_adopt))

    def test_high_evidence_requires_source_locator(self) -> None:
        text = artifact().replace("- **Rule A**:", "- The rule says")
        text = text.replace("- **Related docs**:", "- Related docs show")
        self.assertIn("SOURCE_LOCATOR_MISSING", codes_for(text))

    def test_high_evidence_accepts_em_dash_after_bold_locator(self) -> None:
        text = artifact().replace("- **Rule A**:", "- **Rule A** —")
        text = text.replace("- **Related docs**:", "- **Related docs** —")
        self.assertNotIn("SOURCE_LOCATOR_MISSING", codes_for(text))

    def test_high_evidence_accepts_colon_inside_bold_locator(self) -> None:
        text = artifact().replace("- **Rule A**:", "- **Rule A:**")
        text = text.replace("- **Related docs**:", "- **Related docs:**")
        self.assertNotIn("SOURCE_LOCATOR_MISSING", codes_for(text))

    def test_high_evidence_accepts_plain_colon_locator(self) -> None:
        text = artifact().replace(
            "- **Rule A**:", "- Status header / definition block:"
        )
        text = text.replace("- **Related docs**:", "- README Quick Start block:")
        self.assertNotIn("SOURCE_LOCATOR_MISSING", codes_for(text))

    def test_high_evidence_accepts_plain_em_dash_locator(self) -> None:
        text = artifact().replace("- **Rule A**:", '- README "## Origin" —')
        text = text.replace("- **Related docs**:", "- ROOT LISTING —")
        self.assertNotIn("SOURCE_LOCATOR_MISSING", codes_for(text))

    def test_routing_reason_positive_and_near_miss(self) -> None:
        self.assertEqual(
            atlas_quality.validate_summary(artifact(), evidence_bundle(), checklist()),
            [],
        )
        candidate_only = artifact().replace(
            "- Verifier: Rule A — Typed tool output creates the topic's control boundary [relation=direct; impact=high]",
            "- Candidate topic matches considered: `test-topic`, `other-topic`.",
        )
        codes = codes_for(candidate_only)
        self.assertIn("ROUTING_REASON_MISSING", codes)
        self.assertIn("ROUTING_CANDIDATE_ONLY", codes)

        mismatch = artifact().replace("impact=high]", "impact=medium]")
        self.assertNotIn("ROUTING_REASON_INVALID", codes_for(mismatch))
        fixture = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        near_miss = next(
            case
            for case in fixture["routing_cases"]
            if case["id"] == "route-reason-impact-mismatch"
        )
        self.assertIn(
            "routing-reason-row-mismatch", near_miss["expected"]["failure_ids"]
        )

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
        codes = {
            finding.code for finding in atlas_quality.validate_checklist(duplicate)
        }
        self.assertIn("CHECKLIST_ID_DUPLICATE", codes)

        failed = checklist(failed="limits-uncertainty")
        findings = atlas_quality.validate_checklist(failed)
        self.assertEqual(
            [
                finding.detail
                for finding in findings
                if finding.code == "CHECKLIST_ITEM_FAILED"
            ],
            ["limits-uncertainty"],
        )
        self.assertIn("CHECKLIST_ITEM_FAILED", codes_for(items=failed))

    def test_effective_hash_and_projection_matrix(self) -> None:
        self.assertIn(
            "EVIDENCE_PAYLOAD_TEXT_INVALID",
            codes_for(bundle=evidence_bundle(payload_text=None)),
        )
        self.assertIn(
            "EVIDENCE_PAYLOAD_TEXT_INVALID",
            codes_for(bundle=evidence_bundle(payload_text=123)),
        )
        self.assertIn(
            "EVIDENCE_PAYLOAD_TEXT_INVALID",
            codes_for(bundle=evidence_bundle(payload_text="")),
        )

        # No explicit hash, artifact matches payload hash → pass
        self.assertEqual(
            atlas_quality.validate_summary(artifact(), evidence_bundle(), checklist()),
            [],
        )

        # No explicit hash, artifact differs
        self.assertIn(
            "CONTENT_HASH_MISMATCH",
            codes_for(text=artifact(content_hash=COMPLETE_HASH)),
        )

        # No explicit hash, projection true
        self.assertIn(
            "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
            codes_for(bundle=evidence_bundle(payload_projection=True)),
        )

        # Explicit matching hash, projection omitted → pass
        matching = evidence_bundle(content_hash=DEFAULT_HASH)
        self.assertEqual(
            atlas_quality.validate_summary(artifact(), matching, checklist()),
            [],
        )

        # Explicit matching hash, projection false → pass
        self.assertEqual(
            atlas_quality.validate_summary(
                artifact(),
                evidence_bundle(content_hash=DEFAULT_HASH, payload_projection=False),
                checklist(),
            ),
            [],
        )

        # Explicit matching hash, projection true → fail (declaration)
        self.assertIn(
            "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
            codes_for(
                bundle=evidence_bundle(
                    content_hash=DEFAULT_HASH, payload_projection=True
                )
            ),
        )

        # Explicit mismatching hash, projection omitted → fail
        self.assertIn(
            "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
            codes_for(
                text=artifact(content_hash=COMPLETE_HASH),
                bundle=evidence_bundle(content_hash=COMPLETE_HASH),
            ),
        )

        # Explicit mismatching hash, projection false → fail
        self.assertIn(
            "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
            codes_for(
                text=artifact(content_hash=COMPLETE_HASH),
                bundle=evidence_bundle(
                    content_hash=COMPLETE_HASH, payload_projection=False
                ),
            ),
        )

        # Explicit mismatching hash, projection true without complete_text → unbacked
        self.assertIn(
            "EVIDENCE_PROJECTION_UNBACKED",
            codes_for(
                text=artifact(content_hash=COMPLETE_HASH),
                bundle=evidence_bundle(
                    content_hash=COMPLETE_HASH, payload_projection=True
                ),
            ),
        )

        # Backed projection → pass
        self.assertEqual(
            atlas_quality.validate_summary(
                artifact(content_hash=COMPLETE_HASH),
                projected_bundle(),
                checklist(),
            ),
            [],
        )

        # Wrong complete_text hash
        self.assertIn(
            "EVIDENCE_COMPLETE_TEXT_HASH_MISMATCH",
            codes_for(
                text=artifact(content_hash=COMPLETE_HASH),
                bundle=projected_bundle(complete_text="not the complete body"),
            ),
        )

        # Ranges that do not reconstruct payload
        self.assertIn(
            "EVIDENCE_PROJECTION_UNBACKED",
            codes_for(
                text=artifact(content_hash=COMPLETE_HASH),
                bundle=projected_bundle(projection_ranges=[[0, 1]]),
            ),
        )

        # Non-boolean projection
        for bad in ("true", 1, 0):
            self.assertIn(
                "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
                codes_for(bundle=evidence_bundle(payload_projection=bad)),
            )

        # Malformed explicit hash
        self.assertIn(
            "EVIDENCE_CONTENT_HASH_INVALID",
            codes_for(bundle=evidence_bundle(content_hash="not-a-hash")),
        )

        # Artifact differs from effective explicit hash
        self.assertIn(
            "CONTENT_HASH_MISMATCH",
            codes_for(
                text=artifact(content_hash=DEFAULT_HASH),
                bundle=projected_bundle(),
            ),
        )

        # No universal-newline normalization: CRLF payload differs from LF hash
        crlf = DEFAULT_PAYLOAD.replace(" ", "\r\n", 1)
        crlf_hash = hashlib.sha256(crlf.encode("utf-8")).hexdigest()
        self.assertNotEqual(crlf_hash, DEFAULT_HASH)
        self.assertIn(
            "CONTENT_HASH_MISMATCH",
            codes_for(
                text=artifact(content_hash=DEFAULT_HASH),
                bundle=evidence_bundle(payload_text=crlf),
            ),
        )

    def test_skill_encodes_inaccessible_and_aggregate_entry_behavior(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("stop before artifact or registry writes", lower)
        self.assertIn("report the url and reason", lower)
        self.assertIn("aggregate page", lower)
        self.assertIn("page-only", lower)
        self.assertIn("expand", lower)
        self.assertIn("no answer stops", lower)
        self.assertIn(
            "retain only textual evidence and links; never retain media", lower
        )
        guide = GUIDE_PATH.read_text(encoding="utf-8")
        self.assertIn("aggregate page", guide.lower())
        self.assertIn("too little text", guide.lower())

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
        self.assertEqual(
            [finding.code for finding in findings], ["CALIBRATION_RESULT_MISMATCH"]
        )

    def test_cli_json_is_deterministic(self) -> None:
        payload = {
            "version": 1,
            "artifact_text": artifact(),
            "evidence_bundle": evidence_bundle(),
            "checklist": checklist(),
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

    def test_cli_missing_checklist_is_input_error(self) -> None:
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
            result = subprocess.run(command, check=False, capture_output=True)
        self.assertEqual(result.returncode, 3)
        self.assertIn(b"missing", result.stderr.lower())
        self.assertIn(b"checklist", result.stderr.lower())


class AtlasToolingQualityTests(unittest.TestCase):
    def _schema_errors(self, path: Path, value: object) -> list[object]:
        if jsonschema is None:
            return []
        schema = json.loads(path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        return list(validator.iter_errors(value))

    def _quality_cli(
        self, command: str, payload: dict[str, object]
    ) -> subprocess.CompletedProcess[bytes]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "atlas_quality.py"),
                    command,
                    "--input",
                    str(path),
                ],
                check=False,
                capture_output=True,
            )

    def test_agent_tooling_fixture_is_generic_bounded_and_behavioral(self) -> None:
        fixture_text = AGENT_TOOLING_EVAL_PATH.read_text(encoding="utf-8")
        fixture = json.loads(fixture_text)
        self.assertEqual(set(fixture), {"version", "cases"})
        self.assertEqual(fixture["version"], 1)
        self.assertLess(len(fixture_text.encode("utf-8")), 50 * 1024)
        self.assertEqual(len(fixture["cases"]), 28)
        self.assertEqual(
            [case["id"] for case in fixture["cases"]],
            [
                "fresh-thin-standalone-intent-required",
                "fresh-thin-standalone-declared-intent",
                "fresh-aggregate-scope-required",
                "fresh-inaccessible-no-write",
                "source-recovery-decision-gate",
                "fresh-substantive-article-no-scope-question",
                "fresh-untrusted-evidence-ignored",
                "fresh-action-write-set-deterministic",
                "atlas-router-source",
                "atlas-router-source-presence-overview",
                "atlas-router-source-presence-approved",
                "atlas-router-source-presence-changed-reply",
                "atlas-source-presence-lookup",
                "atlas-router-source-id-status-needs-url",
                "atlas-router-acquire",
                "atlas-router-route",
                "atlas-router-answer",
                "atlas-router-research",
                "atlas-router-refresh",
                "atlas-router-audit",
                "atlas-router-index",
                "atlas-router-migrate",
                "atlas-router-answer-refresh-ask",
                "atlas-router-json-edit-near-miss",
                "audit-source-sequence-gap-allowed",
                "audit-subdomain-index-projection-drift",
                "atlas-router-generic-repository-edit-near-miss",
                "non-atlas-json-edit-near-miss",
            ],
        )
        for case in fixture["cases"]:
            self.assertEqual(set(case), {"id", "prompt", "fixture", "expected"})
            self.assertIsInstance(case["fixture"], dict)
            self.assertIsInstance(case["expected"], dict)

        by_id = {case["id"]: case["expected"] for case in fixture["cases"]}
        self.assertEqual(
            by_id["atlas-router-source-presence-overview"],
            {
                "first_owner": "atlas-source",
                "approval_required": True,
                "overview_fields": ["Goal", "Next", "Effect"],
                "dispatch_count": 0,
                "router_write_set": [],
            },
        )
        self.assertEqual(
            by_id["atlas-router-source-presence-approved"],
            {
                "first_owner": "atlas-source",
                "approval_required": False,
                "dispatch_count": 1,
                "forwarded_request": "unchanged",
                "router_write_set": [],
            },
        )
        self.assertEqual(
            by_id["atlas-router-source-presence-changed-reply"],
            {
                "first_owner": "atlas-source",
                "approval_accepted": False,
                "approval_required": True,
                "dispatch_count": 0,
                "reoverview_effect": "write-capable",
                "router_write_set": [],
            },
        )
        self.assertEqual(
            by_id["atlas-source-presence-lookup"],
            {
                "mode": "source-presence-lookup",
                "operations": ["source.lookup"],
                "fetch": False,
                "artifact_reads": [],
                "write_set": [],
            },
        )
        self.assertEqual(
            by_id["atlas-router-source-id-status-needs-url"],
            {
                "first_owner": None,
                "required_input": "canonical_url",
                "approval_required": False,
                "dispatch_count": 0,
                "router_write_set": [],
                "forbidden_owners": ["atlas-route"],
            },
        )
        self.assertEqual(
            by_id["fresh-thin-standalone-intent-required"]["required_questions"],
            ["resource-intent"],
        )
        self.assertEqual(
            by_id["fresh-aggregate-scope-required"]["required_questions"],
            ["aggregate-scope"],
        )
        self.assertEqual(
            by_id["fresh-aggregate-scope-required"]["recommended_choice"],
            "page-only",
        )
        self.assertEqual(by_id["fresh-inaccessible-no-write"]["write_set"], [])
        self.assertEqual(
            by_id["source-recovery-decision-gate"],
            {
                "ask_required": True,
                "options": [
                    "replacement-input",
                    "bounded-acquisition",
                    "stop-without-writing",
                ],
                "recommended_choice": "stop-without-writing",
                "write_set": [],
                "evidence_substitution": False,
            },
        )
        self.assertEqual(
            by_id["fresh-substantive-article-no-scope-question"]["required_questions"],
            [],
        )
        self.assertEqual(
            by_id["fresh-untrusted-evidence-ignored"],
            by_id["fresh-substantive-article-no-scope-question"],
        )
        self.assertEqual(
            by_id["fresh-action-write-set-deterministic"]["write_set"],
            ["assessment-record"],
        )
        self.assertEqual(
            by_id["non-atlas-json-edit-near-miss"]["claimed_atlas_capabilities"],
            [],
        )
        self.assertEqual(
            by_id["non-atlas-json-edit-near-miss"]["required_atlas_capabilities"],
            [],
        )
        self.assertEqual(
            by_id["audit-source-sequence-gap-allowed"],
            {"findings": [], "next_source_seq": 5, "write_set": []},
        )
        self.assertEqual(
            by_id["audit-subdomain-index-projection-drift"],
            {
                "findings": [
                    "SUBDOMAIN_TOPIC_MAP_DRIFT",
                    "SUBDOMAIN_COVERAGE_MAP_DRIFT",
                ],
                "repair_owner": "atlas-research",
                "write_set": [],
            },
        )
        owner_cases = [
            "atlas-router-source",
            "atlas-router-acquire",
            "atlas-router-route",
            "atlas-router-answer",
            "atlas-router-research",
            "atlas-router-refresh",
            "atlas-router-audit",
            "atlas-router-index",
            "atlas-router-migrate",
        ]
        self.assertEqual(
            {by_id[case]["first_owner"] for case in owner_cases},
            {
                "atlas-source",
                "atlas-acquire",
                "atlas-route",
                "atlas-answer",
                "atlas-research",
                "atlas-refresh",
                "atlas-audit",
                "atlas-index",
                "atlas-migrate",
            },
        )
        for case in owner_cases:
            self.assertEqual(
                set(by_id[case]),
                {
                    "first_owner",
                    "ask_required",
                    "recommended_choice",
                    "router_write_set",
                    "forbidden_owners",
                },
            )
            self.assertEqual(by_id[case]["router_write_set"], [])
        self.assertEqual(
            by_id["atlas-router-answer-refresh-ask"]["recommended_choice"],
            "answer-with-freshness-gate",
        )
        self.assertTrue(by_id["atlas-router-answer-refresh-ask"]["ask_required"])
        repository_edit_expected = {
            "first_owner": None,
            "ask_required": False,
            "recommended_choice": None,
            "router_write_set": [],
            "forbidden_owners": [
                "atlas-acquire",
                "atlas-answer",
                "atlas-audit",
                "atlas-index",
                "atlas-migrate",
                "atlas-refresh",
                "atlas-research",
                "atlas-route",
                "atlas-source",
            ],
        }
        self.assertEqual(
            by_id["atlas-router-json-edit-near-miss"],
            repository_edit_expected,
        )
        self.assertEqual(
            by_id["atlas-router-generic-repository-edit-near-miss"],
            repository_edit_expected,
        )

    def test_fixture_cases_accepts_exclusive_generic_or_named_arrays(self) -> None:
        generic = json.loads(AGENT_TOOLING_EVAL_PATH.read_text(encoding="utf-8"))
        named = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        generic_cases = atlas_quality._fixture_cases(generic)
        named_cases = atlas_quality._fixture_cases(named)
        self.assertEqual(generic_cases, generic["cases"])
        self.assertEqual(len(named_cases), 44)
        self.assertEqual(len({case["id"] for case in named_cases}), len(named_cases))
        mixed = deepcopy(generic)
        mixed["assessment_cases"] = []
        with self.assertRaises(ValueError):
            atlas_quality._fixture_cases(mixed)

    def test_prepare_calibration_validates_blinds_and_preserves_fixture_order(
        self,
    ) -> None:
        fixture_text = AGENT_TOOLING_EVAL_PATH.read_text(encoding="utf-8")
        fixture = json.loads(fixture_text)
        fixture_ids = [case["id"] for case in fixture["cases"]]
        payload = {
            "version": 1,
            "fixture_text": fixture_text,
            "case_ids": list(reversed(fixture_ids)),
        }
        result = self._quality_cli("prepare-calibration", payload)
        expected_cases = [
            {
                "id": case["id"],
                "prompt": case["prompt"],
                "fixture": case["fixture"],
            }
            for case in fixture["cases"]
        ]
        expected = {"version": 1, "cases": expected_cases}
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        self.assertEqual(
            result.stdout,
            (
                json.dumps(
                    expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                )
                + "\n"
            ).encode("utf-8"),
        )
        self.assertEqual(json.loads(result.stdout), expected)
        for case in json.loads(result.stdout)["cases"]:
            self.assertEqual(set(case), {"id", "prompt", "fixture"})

        invalid_payloads = [
            {**payload, "unexpected": True},
            {**payload, "case_ids": fixture_ids[:-1]},
            {**payload, "case_ids": fixture_ids[:-1] + [fixture_ids[0]]},
            {**payload, "case_ids": fixture_ids[:-1] + ["unknown-case"]},
        ]
        for invalid in invalid_payloads:
            invalid_result = self._quality_cli("prepare-calibration", invalid)
            self.assertEqual(invalid_result.returncode, 3)
            self.assertEqual(invalid_result.stdout, b"")

    def test_prepare_calibration_blinds_named_source_fixture_below_limit(
        self,
    ) -> None:
        fixture_text = EVAL_PATH.read_text(encoding="utf-8")
        fixture = json.loads(fixture_text)
        cases = atlas_quality._fixture_cases(fixture)
        prepared = atlas_quality.prepare_calibration(
            fixture_text, [case["id"] for case in cases]
        )
        serialized = json.dumps(
            prepared, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

        self.assertEqual(len(prepared["cases"]), 44)
        self.assertLess(len(serialized.encode("utf-8")), 50 * 1024)
        self.assertNotIn('"expected"', serialized)
        self.assertEqual(
            prepared["cases"][0]["fixture"],
            {
                "evidence": fixture["assessment_cases"][0]["evidence"],
                "result_fields": list(fixture["assessment_cases"][0]["expected"]),
            },
        )
        perturbed = next(
            case
            for case in prepared["cases"]
            if case["id"] == "summary-context-perturbation-a"
        )
        self.assertIn("irrelevant_context", perturbed["fixture"])

    def test_proposal_schema_and_executable_parity(self) -> None:
        valid = proposal()
        if jsonschema is not None:
            self.assertEqual(self._schema_errors(PROPOSAL_SCHEMA_PATH, valid), [])
        self.assertEqual(atlas_quality.validate_proposal(valid, proposal_ledger()), [])

        invalid_native = deepcopy(valid)
        invalid_native["metadata"]["published"] = 2026
        invalid_precision = deepcopy(valid)
        invalid_precision["metadata"]["published"] = "2026"
        invalid_unknown = deepcopy(valid)
        invalid_unknown["metadata"]["unexpected"] = True
        for invalid in (invalid_native, invalid_precision, invalid_unknown):
            if jsonschema is not None:
                self.assertTrue(self._schema_errors(PROPOSAL_SCHEMA_PATH, invalid))
            self.assertTrue(atlas_quality.validate_proposal(invalid, proposal_ledger()))

        context_leak = deepcopy(valid)
        context_leak["claims"][0]["statement"] = (
            "The current request selects this claim."
        )
        self.assertIn(
            "PROPOSAL_CONTEXT_LEAK",
            {
                finding.code
                for finding in atlas_quality.validate_proposal(
                    context_leak, proposal_ledger()
                )
            },
        )
        self.assertIn(
            "PROPOSAL_UNKNOWN_KEY",
            {
                finding.code
                for finding in atlas_quality.validate_proposal(
                    invalid_unknown, proposal_ledger()
                )
            },
        )

    def test_proposal_publication_locator_ledger_and_determinism(self) -> None:
        for published in ("Unknown", "2026-05", "2026-05-01"):
            value = proposal()
            value["metadata"]["published"] = published
            if jsonschema is not None:
                self.assertEqual(self._schema_errors(PROPOSAL_SCHEMA_PATH, value), [])
            self.assertEqual(
                atlas_quality.validate_proposal(value, proposal_ledger()), []
            )

        bad_locator = proposal()
        bad_locator["claims"][0]["evidence"][0]["locator"] = "missing-locator"
        self.assertIn(
            "PROPOSAL_EVIDENCE_LOCATOR_UNBOUND",
            {
                finding.code
                for finding in atlas_quality.validate_proposal(
                    bad_locator, proposal_ledger()
                )
            },
        )
        bad_link = proposal()
        bad_link["links"][0]["ledger_id"] = "missing-link"
        self.assertIn(
            "PROPOSAL_LINK_LEDGER_UNBOUND",
            {
                finding.code
                for finding in atlas_quality.validate_proposal(
                    bad_link, proposal_ledger()
                )
            },
        )

        invalid = deepcopy(bad_link)
        invalid["metadata"]["unknown"] = True
        first = [
            finding.to_dict()
            for finding in atlas_quality.validate_proposal(invalid, proposal_ledger())
        ]
        second = [
            finding.to_dict()
            for finding in atlas_quality.validate_proposal(
                json.loads(json.dumps(invalid)), proposal_ledger()
            )
        ]
        self.assertEqual(first, second)

    def test_fresh_assessment_schema_rejects_unknown_keys(self) -> None:
        value = fresh_assessment()
        if jsonschema is not None:
            self.assertEqual(
                self._schema_errors(FRESH_ASSESSMENT_SCHEMA_PATH, value), []
            )
            unknown_top = deepcopy(value)
            unknown_top["unexpected"] = True
            self.assertTrue(
                self._schema_errors(FRESH_ASSESSMENT_SCHEMA_PATH, unknown_top)
            )
            unknown_nested = deepcopy(value)
            unknown_nested["capture"]["unexpected"] = True
            self.assertTrue(
                self._schema_errors(FRESH_ASSESSMENT_SCHEMA_PATH, unknown_nested)
            )

    def test_fresh_assessment_validates_freeze_packet_and_reference_bindings(
        self,
    ) -> None:
        value = fresh_assessment()
        packet = fresh_packet(value)
        self.assertEqual(
            atlas_quality.validate_fresh_source_assessment(value, packet), []
        )

        freeze_mismatch = fresh_packet(value)
        freeze_mismatch["freeze"]["source_id"] = "abcdef123456"
        self.assertIn(
            "FRESH_FREEZE_MISMATCH",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    value, freeze_mismatch
                )
            },
        )

        packet_hash_mismatch = deepcopy(value)
        packet_hash_mismatch["packet"]["packet_sha256"] = digest("other-packet")
        self.assertIn(
            "FRESH_PACKET_HASH_MISMATCH",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    packet_hash_mismatch, fresh_packet(value)
                )
            },
        )

        blob_hash_mismatch = deepcopy(value)
        blob_hash_mismatch["capture"]["text_blob_sha256"] = digest("other-text")
        self.assertIn(
            "FRESH_TEXT_BLOB_HASH_MISMATCH",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    blob_hash_mismatch, packet
                )
            },
        )

        invalid_excerpt = deepcopy(value)
        invalid_excerpt["evidence"]["excerpts"][0]["end_byte"] = 99
        self.assertIn(
            "FRESH_EXCERPT_INVALID",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    invalid_excerpt, packet
                )
            },
        )

        unbound_link = deepcopy(value)
        unbound_link["evidence"]["links"][0]["id"] = "link-other"
        self.assertIn(
            "FRESH_LINK_LEDGER_UNBOUND",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    unbound_link, packet
                )
            },
        )

        invalid_dimension = deepcopy(value)
        invalid_dimension["dimensions"]["capture"]["evidence_refs"] = ["missing-ref"]
        self.assertIn(
            "FRESH_DIMENSION_EVIDENCE_UNBOUND",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    invalid_dimension, packet
                )
            },
        )

        invalid_finding = deepcopy(value)
        invalid_finding["findings"][0]["evidence_refs"] = ["missing-ref"]
        self.assertIn(
            "FRESH_FINDING_EVIDENCE_UNBOUND",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    invalid_finding, packet
                )
            },
        )

        invalid_index = deepcopy(value)
        invalid_index["index"]["source_count"] = 2
        self.assertIn(
            "FRESH_INDEX_INVALID",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    invalid_index, packet
                )
            },
        )

    def test_fresh_assessment_rejects_unblinded_context_and_nonterminal_rows(
        self,
    ) -> None:
        value = fresh_assessment()
        packet = fresh_packet(value)
        for context_name in ("history", "provider", "request"):
            context_leak = deepcopy(value)
            context_leak["packet"][context_name] = {"opaque": True}
            self.assertIn(
                "FRESH_CONTEXT_LEAK",
                {
                    finding.code
                    for finding in atlas_quality.validate_fresh_source_assessment(
                        context_leak, packet
                    )
                },
            )

        nonterminal = deepcopy(value)
        nonterminal["capture"]["state"] = "pending-systemic"
        self.assertIn(
            "FRESH_TERMINALITY_INVALID",
            {
                finding.code
                for finding in atlas_quality.validate_fresh_source_assessment(
                    nonterminal, packet
                )
            },
        )


if __name__ == "__main__":
    unittest.main()
