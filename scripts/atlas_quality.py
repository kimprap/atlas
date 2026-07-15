#!/usr/bin/env python3
"""Deterministic Atlas source-summary and calibration validation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

VERSION = 1

CHECKLIST_IDS = (
    "evidence-boundary",
    "primary-contribution",
    "source-support",
    "limits-uncertainty",
    "context-neutrality",
    "assessment-coherence",
    "proportionality",
)

REQUIRED_FRONTMATTER = (
    "schema_version",
    "note_type",
    "managed_by",
    "source_id",
    "source_seq",
    "canonical_url",
    "source_kind",
    "title",
    "author",
    "publisher",
    "published",
    "primary_domain",
    "subdomains",
    "secondary_domains",
    "canonical_tags",
    "candidate_terms",
    "routing_status",
    "routed_at",
    "first_seen",
    "last_checked",
    "last_summarized",
    "refresh_after",
    "content_hash",
    "acquired_by",
    "acquisition_run",
    "coverage",
    "confidence",
    "evidence_strength",
    "practicality",
    "stability",
    "reuse_value",
    "recommended_posture",
)
REQUIRED_SECTIONS = (
    "Assessment",
    "Classification",
    "Key points",
    "Evidence / examples",
    "Caveats / open questions",
    "Routing notes",
    "Reuse cues",
    "Links",
)
SEMANTIC_SECTIONS = {
    "Assessment",
    "Key points",
    "Approaches / mechanics",
    "Evidence / examples",
    "Caveats / open questions",
    "Reuse cues",
    "Links",
}
ENUMS = {
    "note_type": {"source-summary"},
    "managed_by": {"atlas"},
    "source_kind": {"article", "paper", "repo", "thread", "video", "docs", "other"},
    "routing_status": {"unrouted", "routed", "no-topic-match", "routing-blocked"},
    "acquired_by": {"manual", "acquisition-run", "research-acquire"},
    "coverage": {"complete", "partial", "failed"},
    "confidence": {"high", "medium", "low"},
    "evidence_strength": {"high", "medium", "low"},
    "practicality": {"high", "medium", "low", "n/a"},
    "stability": {"stable", "moving", "speculative"},
    "reuse_value": {"high", "medium", "low"},
    "recommended_posture": {"adopt", "trial", "watch", "reference-only", "ignore"},
}
ASSESSMENT_LABELS = {
    "Coverage": "coverage",
    "Confidence": "confidence",
    "Evidence strength": "evidence_strength",
    "Practicality": "practicality",
    "Stability": "stability",
    "Reuse value": "reuse_value",
    "Recommended posture": "recommended_posture",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")
CONTENT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
URL_RE = re.compile(r"""https?://[^\s)>\]}"'`,;]+""")
HEADING_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(
    r"<(?:resource title|canonical url|source_id|source_seq|person or org|site or org|"
    r"topic ids or none|exact missing [^>\n]+|noncanonical useful phrases[^>\n]*)>"
    r"|\bYYYY-MM-DD\b|\b(?:complete\|partial\|failed|high\|medium\|low)\b",
    re.IGNORECASE,
)
GENERATED_CONTEXT_RE = re.compile(
    r"\bT[0-9]+\b|this (?:task|plan|conversation|comparison)|"
    r"selected explicitly for|owns adoption|future Atlas workflow",
    re.IGNORECASE,
)
REPOSITORY_CONTEXT_RE = re.compile(
    r"vault://atlas/|\.agents/plans/|scripts/atlas_(?:state|quality)\.py|"
    r"current (?:request|working tree|repository)|active (?:model|provider|harness)",
    re.IGNORECASE,
)
LOCATOR_RE = re.compile(
    r"^-\s+(?:\*\*[^*]+\*\*|`[^`]+`|(?:Heading|Section|Rule|Command|File|"
    r"Page|Timestamp|Asset|Diagram|Code|Step)\b[^:]{0,100}):\s+\S",
    re.IGNORECASE,
)
REASON_RE = re.compile(
    r"^Verifier: (?P<locator>\S(?:.*\S)?) — (?P<claim>\S(?:.*\S)?) "
    r"\[relation=(?P<relation>direct|supporting|contradicting); "
    r"impact=(?P<impact>high|medium|low)\]$"
)


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str = "artifact"
    line: int | None = None
    section: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "path": self.path}
        if self.line is not None:
            result["line"] = self.line
        if self.section is not None:
            result["section"] = self.section
        if self.detail:
            result["detail"] = self.detail
        return result


def _normalize(findings: Iterable[Finding]) -> list[Finding]:
    return sorted(
        set(findings),
        key=lambda item: (
            item.path,
            item.line if item.line is not None else -1,
            item.section or "",
            item.code,
            item.detail,
        ),
    )


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[Finding]]:
    lines = text.splitlines()
    findings: list[Finding] = []
    if not lines or lines[0].strip() != "---":
        return {}, text, [Finding("FRONTMATTER_MISSING", line=1)]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, text, [Finding("FRONTMATTER_UNTERMINATED", line=1)]
    data: dict[str, str] = {}
    last_key: str | None = None
    for index, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(("  - ", "\t- ")) and last_key is not None:
            item = _unquote(line.split("-", 1)[1])
            data[last_key] = f"{data[last_key]}, {item}".strip(", ")
            continue
        if ":" not in line:
            findings.append(Finding("FRONTMATTER_LINE_INVALID", line=index, detail=line))
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or key in data:
            findings.append(Finding("FRONTMATTER_KEY_DUPLICATE", line=index, detail=key))
            continue
        data[key] = _unquote(value)
        last_key = key
    body = "\n".join(lines[end + 1 :])
    return data, body, findings


def _sections(body: str) -> tuple[dict[str, str], str]:
    matches = list(HEADING_RE.finditer(body))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        result[match.group(1).strip()] = body[start:end].strip()
    intro_end = matches[0].start() if matches else len(body)
    return result, body[:intro_end].strip()


def _line_number(text: str, needle: str) -> int | None:
    index = text.find(needle)
    return None if index < 0 else text.count("\n", 0, index) + 1


def _strip_url(url: str) -> str:
    return url.rstrip(".,;:")


def _bundle_urls(bundle: Mapping[str, Any]) -> tuple[set[str], list[Finding]]:
    findings: list[Finding] = []
    allowed: set[str] = set()
    canonical = bundle.get("canonical_url")
    if not isinstance(canonical, str) or not canonical.startswith(("http://", "https://")):
        findings.append(Finding("EVIDENCE_CANONICAL_URL_INVALID", path="evidence"))
    else:
        allowed.add(canonical)
    for field_name in ("source_urls", "allowed_urls"):
        value = bundle.get(field_name, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            findings.append(Finding("EVIDENCE_URL_LIST_INVALID", path="evidence", detail=field_name))
        else:
            allowed.update(value)
    media = bundle.get("media", [])
    if not isinstance(media, list):
        findings.append(Finding("EVIDENCE_MEDIA_INVALID", path="evidence"))
    else:
        for index, item in enumerate(media):
            if not isinstance(item, Mapping) or not isinstance(item.get("url"), str):
                findings.append(Finding("EVIDENCE_MEDIA_INVALID", path="evidence", detail=str(index)))
                continue
            if item.get("fetched") is not True:
                findings.append(Finding("EVIDENCE_MEDIA_NOT_FETCHED", path="evidence", detail=item["url"]))
                continue
            allowed.add(item["url"])
    return allowed, findings


def _assessment_values(section: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        field = ASSESSMENT_LABELS.get(cells[0])
        if field:
            values[field] = cells[1].strip("`")
    return values


def _semantic_text(sections: Mapping[str, str], intro: str) -> str:
    parts = [intro]
    parts.extend(sections[name] for name in SEMANTIC_SECTIONS if name in sections)
    return "\n".join(parts)


def _normalized_units(sections: Mapping[str, str], intro: str) -> Iterable[tuple[str, str]]:
    blocks = {"Introduction": intro}
    blocks.update({name: sections[name] for name in SEMANTIC_SECTIONS if name in sections})
    for section, text in blocks.items():
        paragraph: list[str] = []
        for line in text.splitlines() + [""]:
            stripped = line.strip()
            if stripped.startswith(("- ", "* ")):
                normalized = re.sub(r"\W+", " ", stripped[2:].casefold()).strip()
                if len(normalized) >= 40:
                    yield section, normalized
            elif not stripped:
                if paragraph:
                    normalized = re.sub(r"\W+", " ", " ".join(paragraph).casefold()).strip()
                    if len(normalized) >= 40:
                        yield section, normalized
                    paragraph = []
            elif not stripped.startswith(("|", "#", ">")):
                paragraph.append(stripped)


def validate_checklist(value: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(value, list):
        return [Finding("CHECKLIST_INVALID", path="checklist", detail="expected array")]
    ids: list[str] = []
    for index, item in enumerate(value):
        path = f"checklist[{index}]"
        if not isinstance(item, Mapping):
            findings.append(Finding("CHECKLIST_ITEM_INVALID", path=path))
            continue
        expected_keys = {"id", "status", "evidence"}
        for key in sorted(expected_keys - set(item)):
            findings.append(Finding("CHECKLIST_FIELD_MISSING", path=path, detail=key))
        for key in sorted(set(item) - expected_keys):
            findings.append(Finding("CHECKLIST_FIELD_UNKNOWN", path=path, detail=key))
        item_id = item.get("id")
        status = item.get("status")
        evidence = item.get("evidence")
        if not isinstance(item_id, str):
            findings.append(Finding("CHECKLIST_ID_INVALID", path=path))
        else:
            ids.append(item_id)
        if status not in {"pass", "fail"}:
            findings.append(Finding("CHECKLIST_STATUS_INVALID", path=path, detail=str(status)))
        elif status == "fail":
            findings.append(Finding("CHECKLIST_ITEM_FAILED", path=path, detail=str(item_id)))
        if not isinstance(evidence, str) or not evidence.strip():
            findings.append(Finding("CHECKLIST_EVIDENCE_INVALID", path=path))
    if len(value) != len(CHECKLIST_IDS):
        findings.append(
            Finding("CHECKLIST_LENGTH_INVALID", path="checklist", detail=f"expected {len(CHECKLIST_IDS)}")
        )
    if tuple(ids) != CHECKLIST_IDS:
        findings.append(
            Finding("CHECKLIST_ORDER_INVALID", path="checklist", detail=f"expected {list(CHECKLIST_IDS)!r}")
        )
    if len(ids) != len(set(ids)):
        findings.append(Finding("CHECKLIST_ID_DUPLICATE", path="checklist"))
    for item_id in ids:
        if item_id not in CHECKLIST_IDS:
            findings.append(Finding("CHECKLIST_ID_UNKNOWN", path="checklist", detail=item_id))
    return _normalize(findings)


def validate_summary(artifact_text: str, evidence_bundle: Mapping[str, Any]) -> list[Finding]:
    """Validate deterministic source-artifact and evidence-envelope invariants."""
    findings: list[Finding] = []
    if not isinstance(artifact_text, str):
        return [Finding("ARTIFACT_TEXT_INVALID")]
    if not isinstance(evidence_bundle, Mapping):
        return [Finding("EVIDENCE_BUNDLE_INVALID", path="evidence")]
    if evidence_bundle.get("version") != VERSION:
        findings.append(Finding("EVIDENCE_VERSION_INVALID", path="evidence"))

    frontmatter, body, frontmatter_findings = _parse_frontmatter(artifact_text)
    findings.extend(frontmatter_findings)
    for key in REQUIRED_FRONTMATTER:
        if key not in frontmatter:
            findings.append(Finding("FRONTMATTER_KEY_MISSING", detail=key))
    for key in frontmatter:
        if key not in REQUIRED_FRONTMATTER:
            findings.append(Finding("FRONTMATTER_KEY_UNKNOWN", detail=key))
    if frontmatter.get("schema_version") != "1":
        findings.append(Finding("SCHEMA_VERSION_INVALID"))
    for key, allowed in ENUMS.items():
        if key in frontmatter and frontmatter[key] not in allowed:
            findings.append(Finding("FRONTMATTER_ENUM_INVALID", detail=f"{key}={frontmatter[key]}"))
    if "source_id" in frontmatter and not SOURCE_ID_RE.fullmatch(frontmatter["source_id"]):
        findings.append(Finding("SOURCE_ID_INVALID"))
    if "content_hash" in frontmatter and not CONTENT_HASH_RE.fullmatch(frontmatter["content_hash"]):
        findings.append(Finding("CONTENT_HASH_INVALID"))
    try:
        if int(frontmatter.get("source_seq", "0")) <= 0:
            raise ValueError
    except ValueError:
        findings.append(Finding("SOURCE_SEQ_INVALID"))
    for key in ("published", "routed_at", "first_seen", "last_checked", "last_summarized", "refresh_after"):
        value = frontmatter.get(key, "")
        if value and value != "Unknown" and not DATE_RE.fullmatch(value):
            findings.append(Finding("FRONTMATTER_DATE_INVALID", detail=key))
    if frontmatter.get("recommended_posture") == "adopt":
        coupling = (
            frontmatter.get("evidence_strength") == "high"
            and frontmatter.get("practicality") == "high"
            and frontmatter.get("stability") == "stable"
            and evidence_bundle.get("unresolved_validation_caveat") is not True
        )
        if not coupling:
            findings.append(Finding("ADOPT_COUPLING_INVALID"))

    sections, intro = _sections(body)
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            findings.append(Finding("SECTION_MISSING", section=name))
    if not re.search(r">\s*\*\*TL;DR\*\*:\s*\S", intro):
        findings.append(Finding("TLDR_MISSING", section="Introduction"))

    if PLACEHOLDER_RE.search(artifact_text):
        match = PLACEHOLDER_RE.search(artifact_text)
        assert match is not None
        findings.append(
            Finding("PLACEHOLDER_UNRESOLVED", line=_line_number(artifact_text, match.group(0)), detail=match.group(0))
        )

    assessment = _assessment_values(sections.get("Assessment", ""))
    for key in ASSESSMENT_LABELS.values():
        if key not in assessment:
            findings.append(Finding("ASSESSMENT_SIGNAL_MISSING", section="Assessment", detail=key))
        elif frontmatter.get(key) != assessment[key]:
            findings.append(
                Finding(
                    "ASSESSMENT_FRONTMATTER_MISMATCH",
                    section="Assessment",
                    detail=f"{key}: {frontmatter.get(key)!r} != {assessment[key]!r}",
                )
            )

    semantic = _semantic_text(sections, intro)
    for pattern, code in (
        (GENERATED_CONTEXT_RE, "GENERATED_CONTEXT_LEAK"),
        (REPOSITORY_CONTEXT_RE, "REPOSITORY_CONTEXT_LEAK"),
    ):
        for match in pattern.finditer(semantic):
            findings.append(
                Finding(code, line=_line_number(artifact_text, match.group(0)), detail=match.group(0))
            )
    forbidden_terms = evidence_bundle.get("forbidden_context_terms", [])
    if not isinstance(forbidden_terms, list) or not all(isinstance(item, str) for item in forbidden_terms):
        findings.append(Finding("EVIDENCE_FORBIDDEN_TERMS_INVALID", path="evidence"))
    else:
        for term in forbidden_terms:
            if term and re.search(re.escape(term), semantic, re.IGNORECASE):
                findings.append(Finding("AMBIENT_CONTEXT_LEAK", detail=term))

    allowed_urls, url_findings = _bundle_urls(evidence_bundle)
    findings.extend(url_findings)
    canonical = frontmatter.get("canonical_url")
    if isinstance(evidence_bundle.get("canonical_url"), str) and canonical != evidence_bundle["canonical_url"]:
        findings.append(Finding("CANONICAL_URL_MISMATCH"))
    for match in URL_RE.finditer(semantic):
        url = _strip_url(match.group(0))
        if url not in allowed_urls:
            findings.append(
                Finding("URL_OUTSIDE_EVIDENCE", line=_line_number(artifact_text, match.group(0)), detail=url)
            )

    seen_units: dict[str, str] = {}
    for section, normalized in _normalized_units(sections, intro):
        previous = seen_units.get(normalized)
        if previous is not None:
            findings.append(
                Finding("EXACT_NORMALIZED_DUPLICATE", section=section, detail=f"duplicates {previous}")
            )
        else:
            seen_units[normalized] = section

    if frontmatter.get("evidence_strength") == "high":
        evidence_lines = [line.strip() for line in sections.get("Evidence / examples", "").splitlines()]
        if not any(LOCATOR_RE.match(line) for line in evidence_lines):
            findings.append(Finding("SOURCE_LOCATOR_MISSING", section="Evidence / examples"))

    routing = sections.get("Routing notes", "")
    verifier_lines = []
    for line in routing.splitlines():
        stripped = line.strip()
        if "Verifier:" in stripped:
            verifier_lines.append(stripped.lstrip("- ").strip())
    require_routing_reason = evidence_bundle.get("require_routing_reason") is True
    if require_routing_reason and frontmatter.get("routing_status") == "routed" and not verifier_lines:
        findings.append(Finding("ROUTING_REASON_MISSING", section="Routing notes"))
    for reason in verifier_lines:
        if REASON_RE.fullmatch(reason) is None:
            findings.append(Finding("ROUTING_REASON_INVALID", section="Routing notes", detail=reason))
    if require_routing_reason and re.search(r"Candidate topic matches considered:[^\n]+$", routing, re.MULTILINE) and not verifier_lines and frontmatter.get("routing_status") == "routed":
        findings.append(Finding("ROUTING_CANDIDATE_ONLY", section="Routing notes"))

    findings.extend(validate_checklist(evidence_bundle.get("checklist")))
    return _normalize(findings)


def _fixture_cases(fixture: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    cases: list[Mapping[str, Any]] = []
    for section in ("assessment_cases", "summary_cases", "routing_cases", "negative_audit_cases"):
        value = fixture.get(section)
        if not isinstance(value, list):
            raise ValueError(f"fixture.{section} must be an array")
        for case in value:
            if not isinstance(case, Mapping) or not isinstance(case.get("id"), str) or "expected" not in case:
                raise ValueError(f"invalid case in {section}")
            cases.append(case)
    return cases


def validate_calibration(fixture_text: str, response_text: str) -> list[Finding]:
    """Exact-compare structured calibration outcomes to the versioned fixture."""
    findings: list[Finding] = []
    try:
        fixture = json.loads(fixture_text)
        response = json.loads(response_text)
    except json.JSONDecodeError as exc:
        return [Finding("CALIBRATION_JSON_INVALID", path="calibration", detail=str(exc))]
    if not isinstance(fixture, Mapping) or fixture.get("version") != VERSION:
        return [Finding("CALIBRATION_FIXTURE_VERSION_INVALID", path="fixture")]
    if not isinstance(response, Mapping) or response.get("version") != VERSION:
        return [Finding("CALIBRATION_RESPONSE_VERSION_INVALID", path="response")]
    try:
        cases = _fixture_cases(fixture)
    except ValueError as exc:
        return [Finding("CALIBRATION_FIXTURE_INVALID", path="fixture", detail=str(exc))]
    expected = {str(case["id"]): case["expected"] for case in cases}
    if len(expected) != len(cases):
        findings.append(Finding("CALIBRATION_FIXTURE_DUPLICATE_ID", path="fixture"))
    results = response.get("results")
    if not isinstance(results, list):
        return _normalize(findings + [Finding("CALIBRATION_RESULTS_INVALID", path="response")])
    actual: dict[str, Any] = {}
    for index, result in enumerate(results):
        if not isinstance(result, Mapping) or set(result) != {"id", "actual"} or not isinstance(result.get("id"), str):
            findings.append(Finding("CALIBRATION_RESULT_INVALID", path=f"response.results[{index}]"))
            continue
        case_id = result["id"]
        if case_id in actual:
            findings.append(Finding("CALIBRATION_RESULT_DUPLICATE_ID", path="response", detail=case_id))
        actual[case_id] = result["actual"]
    for case_id in sorted(set(expected) - set(actual)):
        findings.append(Finding("CALIBRATION_RESULT_MISSING", path="response", detail=case_id))
    for case_id in sorted(set(actual) - set(expected)):
        findings.append(Finding("CALIBRATION_RESULT_UNKNOWN", path="response", detail=case_id))
    for case_id in sorted(set(expected) & set(actual)):
        if actual[case_id] != expected[case_id]:
            findings.append(
                Finding(
                    "CALIBRATION_RESULT_MISMATCH",
                    path="response",
                    detail=f"{case_id}: expected {json.dumps(expected[case_id], sort_keys=True)}",
                )
            )
    return _normalize(findings)


def _load_input(path: str) -> Mapping[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, Mapping) or value.get("version") != VERSION:
        raise ValueError(f"input.version must be {VERSION}")
    return value


def _emit(findings: Sequence[Finding]) -> None:
    payload = {"ok": not findings, "findings": [finding.to_dict() for finding in findings]}
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atlas_quality.py",
        description="Validate Atlas source summaries or calibration responses.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("validate-summary", "validate-calibration"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--input", required=True, help="Versioned JSON input path, or - for stdin")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _load_input(args.input)
        allowed = (
            {"version", "artifact_text", "evidence_bundle"}
            if args.command == "validate-summary"
            else {"version", "fixture_text", "response_text"}
        )
        unknown = set(payload) - allowed
        missing = allowed - set(payload)
        if unknown or missing:
            raise ValueError(f"input fields invalid: missing={sorted(missing)}, unknown={sorted(unknown)}")
        if args.command == "validate-summary":
            findings = validate_summary(payload["artifact_text"], payload["evidence_bundle"])
        else:
            findings = validate_calibration(payload["fixture_text"], payload["response_text"])
        _emit(findings)
        return 0 if not findings else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"atlas-quality: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
