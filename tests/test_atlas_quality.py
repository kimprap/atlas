from __future__ import annotations

import hashlib
import json
import sys
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
SKILL_PATH = (
    ROOT / ".agents" / "skills" / "atlas-ask" / "owners" / "atlas-source" / "OWNER.md"
)
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
WORKFLOW_RESULT_SCHEMA_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "atlas-workflow-result.schema.json"
)

CURRENT_WORKFLOW_BINDING = {
    "dispatch_id": "dispatch-atlas-source-0001",
    "owner": "atlas-source",
    "atlas_attempt": 1,
    "owner_turn": 1,
    "architecture_revision": (
        "sha256:fda1ede6483a8ba873070aaadfc0353b2c5e4bc47a7cc11a312c4950fd994cd0"
    ),
    "guardrail_revision": (
        "sha256:6dd928067b5a9991d451b60fab88a65f8a665899eaf9a4958ec1653b785785f2"
    ),
    "result_schema_revision": (
        "sha256:11d2aa065a2fd6d30eead75ef77fbd9391020ed825193cb5498fc4ee488372ad"
    ),
    "owner_revision": (
        "sha256:d93c4412138d6eed7145b1ef065c970800045bb6e8baea3d8f31d5229c50c7ff"
    ),
}

WORKFLOW_BINDING_FIELDS = frozenset(CURRENT_WORKFLOW_BINDING)
CURRENT_ROUTE_OWNER_REVISION = (
    "sha256:d29f6b2540efcc3f3bebc9a4e98b2ccfd23216a38d0e9d16ef29ca33c3e2263a"
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
**Source ID**: `{values["source_id"]}`
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


class AtlasToolingQualityTests(unittest.TestCase):
    def _schema_errors(
        self,
        path: Path,
        value: object,
        *,
        schema_ref: str | None = None,
    ) -> list[object]:
        if jsonschema is None:
            return []
        schema = json.loads(path.read_text(encoding="utf-8"))
        if schema_ref is not None:
            schema = {
                "$schema": schema["$schema"],
                "$ref": schema_ref,
                "$defs": schema["$defs"],
            }
        validator = jsonschema.Draft202012Validator(schema)
        return list(validator.iter_errors(value))

    def test_agent_tooling_fixture_is_lean_and_behavioral(self) -> None:
        fixture_text = AGENT_TOOLING_EVAL_PATH.read_text(encoding="utf-8")
        fixture = json.loads(fixture_text)
        self.assertEqual(set(fixture), {"version", "cases"})
        self.assertEqual(fixture["version"], 1)
        self.assertLess(len(fixture_text.encode("utf-8")), 50 * 1024)
        expected_ids = [
            "owner-mode-source",
            "owner-mode-research",
            "owner-mode-maintain",
            "read-only-presence-no-approval",
            "read-only-answer-no-approval",
            "write-one-approval",
            "ambiguous-batched-clarification",
            "task-transport-absent",
            "discovery-lifecycle-default",
            "discovery-all-audiences",
            "owner-result-completed",
            "owner-result-no-write",
            "owner-result-needs-user",
            "owner-result-needs-guidance",
            "source-resume-ceiling",
            "other-owner-resume-ceiling",
            "partial-blocks-exact-recovery",
            "unknown-completed-rejected",
            "source-inventory-contract",
            "source-empty-inventory-terminal",
            "source-worker-preread-gate",
            "source-prepared-route",
            "source-transaction-owner",
            "research-dirty-continuation",
            "answer-dirty-no-write",
            "framework-defect-terminal",
        ]
        self.assertEqual([case["id"] for case in fixture["cases"]], expected_ids)
        for case in fixture["cases"]:
            self.assertEqual(set(case), {"id", "prompt", "fixture", "expected"})
            self.assertIsInstance(case["prompt"], str)
            self.assertTrue(case["prompt"])
            self.assertIsInstance(case["fixture"], dict)
            self.assertIsInstance(case["expected"], dict)

    def test_source_inventory_evals_define_actionability_and_terminal_order(
        self,
    ) -> None:
        fixture = json.loads(AGENT_TOOLING_EVAL_PATH.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in fixture["cases"]}
        inventory = cases["source-inventory-contract"]
        terminal = cases["source-empty-inventory-terminal"]

        self.assertIn("continue past inventory", inventory["prompt"])
        self.assertIn("reporting an entry is not actionability", inventory["prompt"])
        self.assertEqual(inventory["expected"]["presence_actionable"], [])
        self.assertIn("default capabilities", terminal["prompt"])
        self.assertEqual(
            terminal["expected"]["operations"],
            ["capabilities", "source.inventory"],
        )
        transaction = cases["source-transaction-owner"]
        self.assertIn("both receipt cases", transaction["prompt"])
        self.assertIn("only operations actually invoked", transaction["prompt"])
        receipt_cases = {case["id"]: case for case in transaction["fixture"]["cases"]}
        self.assertFalse(
            receipt_cases["applied"]["execute_receipt"]["successor_eligible"]
        )
        self.assertEqual(
            receipt_cases["rolled-back-successor"]["recovery_receipt"],
            {
                "status": "rolled-back",
                "successor_eligible": True,
                "transaction_id": "tx-1",
            },
        )
        self.assertEqual(
            transaction["expected"]["applied_operations"],
            ["transaction.execute"],
        )
        self.assertEqual(
            transaction["expected"]["rolled_back_successor_operations"],
            [
                "transaction.execute",
                "transaction.recover",
                "transaction.successor",
            ],
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
        result = atlas_quality.prepare_calibration(
            fixture_text, list(reversed(fixture_ids))
        )
        expected_cases = [
            {
                "id": case["id"],
                "prompt": case["prompt"],
                "fixture": case["fixture"],
            }
            for case in fixture["cases"]
        ]
        expected = {"version": 1, "cases": expected_cases}
        self.assertEqual(result, expected)
        for case in result["cases"]:
            self.assertEqual(set(case), {"id", "prompt", "fixture"})

        invalid_case_ids = [
            fixture_ids[:-1],
            fixture_ids[:-1] + [fixture_ids[0]],
            fixture_ids[:-1] + ["unknown-case"],
        ]
        for case_ids in invalid_case_ids:
            with self.assertRaises(ValueError):
                atlas_quality.prepare_calibration(fixture_text, case_ids)

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
        self.assertEqual(
            atlas_quality.validate_proposal_structure(valid, proposal_ledger()), []
        )

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
        self.assertEqual(
            atlas_quality.validate_proposal_structure(context_leak, proposal_ledger()),
            [],
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
        bad_locator_findings = atlas_quality.validate_proposal(
            bad_locator, proposal_ledger()
        )
        self.assertIn(
            "PROPOSAL_EVIDENCE_LOCATOR_UNBOUND",
            {finding.code for finding in bad_locator_findings},
        )
        self.assertEqual(
            atlas_quality.validate_proposal_structure(bad_locator, proposal_ledger()),
            [],
        )
        self.assertEqual(
            next(
                finding.detail
                for finding in bad_locator_findings
                if finding.code == "PROPOSAL_EVIDENCE_LOCATOR_UNBOUND"
            ),
            'expected=[["section-a","evidence-a"]]; '
            'actual=["missing-locator","evidence-a"]',
        )
        bad_link = proposal()
        bad_link["links"][0]["ledger_id"] = "missing-link"
        bad_link_findings = atlas_quality.validate_proposal(bad_link, proposal_ledger())
        self.assertIn(
            "PROPOSAL_LINK_LEDGER_UNBOUND",
            {finding.code for finding in bad_link_findings},
        )
        self.assertEqual(
            next(
                finding.detail
                for finding in bad_link_findings
                if finding.code == "PROPOSAL_LINK_LEDGER_UNBOUND"
            ),
            'expected=[["https://example.com/source","canonical-link","link-a"]]; '
            'actual=["https://example.com/source","canonical-link","missing-link"]',
        )
        invalid_ledger_id = proposal_ledger()
        invalid_ledger_id["evidence"][0]["ledger_id"] = "bad id"
        self.assertIn(
            "PROPOSAL_LEDGER_INVALID",
            {
                finding.code
                for finding in atlas_quality.validate_proposal_structure(
                    proposal(), invalid_ledger_id
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


if __name__ == "__main__":
    unittest.main()
