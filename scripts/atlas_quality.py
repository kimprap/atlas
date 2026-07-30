#!/usr/bin/env python3
"""Deterministic Atlas source-summary and calibration validation."""

from __future__ import annotations

import argparse
import hashlib
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
INTEGER_FRONTMATTER_KEYS = frozenset({"schema_version", "source_seq"})
LIST_FRONTMATTER_KEYS = frozenset(
    {"subdomains", "secondary_domains", "canonical_tags", "candidate_terms"}
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PUBLICATION_DATE_RE = re.compile(r"^\d{4}-\d{2}(?:-\d{2})?$")
SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")
CONTENT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
URL_RE = re.compile(r"""https?://[^\s)>\]}"'`,;]+""")
HEADING_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
SECTION_ALIASES = {
    "Classification (post-draft Atlas annotation)": "Classification",
    "Routing notes (post-draft Atlas annotation)": "Routing notes",
}
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
    r"current (?:request|working tree|repository)|active (?:provider|harness)",
    re.IGNORECASE,
)
LOCATOR_RE = re.compile(
    r"^-\s+(?:(?:\*\*[^*]+:\*\*|`[^`]+:`)|"
    r"(?:\*\*[^*]+\*\*|`[^`]+`|[^*`\s][^\n]{0,119}?)(?::|\s+—))\s+\S",
    re.IGNORECASE,
)
REASON_RE = re.compile(
    r"^Verifier: (?P<locator>\S(?:.*\S)?) — (?P<claim>\S(?:.*\S)?) "
    r"\[relation=(?P<relation>direct|supporting|contradicting); "
    r"impact=(?P<impact>high|medium|low)\]$"
)
GENERIC_ASSESSMENT_NOTES = (
    "The canonical delivery surface determines the selected stability.",
    "The source-specific limits support this curation posture.",
    "The stated procedure or material can be evaluated within its described scope.",
    "The cited material answers a bounded source-intrinsic question.",
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
    raw_values: dict[str, str] = {}
    line_numbers: dict[str, int] = {}
    list_item_counts: dict[str, int] = {}
    last_key: str | None = None
    for index, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(("  - ", "\t- ")) and last_key is not None:
            item = _unquote(line.split("-", 1)[1])
            data[last_key] = f"{data[last_key]}, {item}".strip(", ")
            list_item_counts[last_key] = list_item_counts.get(last_key, 0) + 1
            continue
        if ":" not in line:
            findings.append(
                Finding("FRONTMATTER_LINE_INVALID", line=index, detail=line)
            )
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key or key in data:
            findings.append(
                Finding("FRONTMATTER_KEY_DUPLICATE", line=index, detail=key)
            )
            continue
        raw = value.strip()
        data[key] = _unquote(raw)
        raw_values[key] = raw
        line_numbers[key] = index
        last_key = key
    for key in INTEGER_FRONTMATTER_KEYS:
        raw = raw_values.get(key)
        if raw is not None and re.fullmatch(r"0|[1-9]\d*", raw) is None:
            findings.append(
                Finding(
                    "FRONTMATTER_INTEGER_TYPE_INVALID",
                    line=line_numbers[key],
                    detail=key,
                )
            )
    for key in LIST_FRONTMATTER_KEYS:
        raw = raw_values.get(key)
        if raw is None:
            continue
        valid = list_item_counts.get(key, 0) > 0 if raw == "" else False
        if raw:
            try:
                items = json.loads(raw)
            except json.JSONDecodeError:
                items = None
            valid = isinstance(items, list) and all(
                isinstance(item, str) for item in items
            )
        if not valid:
            findings.append(
                Finding(
                    "FRONTMATTER_LIST_TYPE_INVALID",
                    line=line_numbers[key],
                    detail=key,
                )
            )
    body = "\n".join(lines[end + 1 :])
    return data, body, findings


def _sections(body: str) -> tuple[dict[str, str], str]:
    matches = list(HEADING_RE.finditer(body))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        result[SECTION_ALIASES.get(match.group(1).strip(), match.group(1).strip())] = (
            body[start:end].strip()
        )
    intro_end = matches[0].start() if matches else len(body)
    return result, body[:intro_end].strip()


def _line_number(text: str, needle: str) -> int | None:
    index = text.find(needle)
    return None if index < 0 else text.count("\n", 0, index) + 1


def _strip_url(url: str) -> str:
    return url.rstrip(".,;:")


FORBIDDEN_EVIDENCE_ASSET_FIELDS = frozenset(
    {
        "media",
        "media_bytes",
        "assets",
        "asset_bytes",
        "asset_path",
        "binary",
        "binary_content",
        "binary_payload",
        "image",
        "images",
        "audio",
        "video",
        "screenshot",
        "screenshots",
        "attachment",
        "attachments",
    }
)


def _bundle_urls(bundle: Mapping[str, Any]) -> tuple[set[str], list[Finding]]:
    findings: list[Finding] = []
    allowed: set[str] = set()
    canonical = bundle.get("canonical_url")
    if not isinstance(canonical, str) or not canonical.startswith(
        ("http://", "https://")
    ):
        findings.append(Finding("EVIDENCE_CANONICAL_URL_INVALID", path="evidence"))
    else:
        allowed.add(canonical)
    for field_name in ("source_urls", "allowed_urls"):
        value = bundle.get(field_name, [])
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            findings.append(
                Finding("EVIDENCE_URL_LIST_INVALID", path="evidence", detail=field_name)
            )
        else:
            allowed.update(value)
    payload_text = bundle.get("payload_text")
    if isinstance(payload_text, str):
        for match in URL_RE.finditer(payload_text):
            allowed.add(_strip_url(match.group(0)))
    complete_text = bundle.get("complete_text")
    if isinstance(complete_text, str):
        for match in URL_RE.finditer(complete_text):
            allowed.add(_strip_url(match.group(0)))
    return allowed, findings


def _asset_field_findings(bundle: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for key in sorted(bundle):
        if key not in FORBIDDEN_EVIDENCE_ASSET_FIELDS:
            continue
        value = bundle[key]
        if value in (None, [], {}, ""):
            continue
        findings.append(
            Finding(
                "EVIDENCE_MEDIA_ASSET_REJECTED",
                path="evidence",
                detail=key,
            )
        )
    return findings


def _ranges_reconstruct_payload(
    complete_text: str,
    ranges: Any,
    payload_text: str,
) -> bool:
    if not isinstance(ranges, list) or not ranges:
        return False
    data = complete_text.encode("utf-8")
    parts: list[bytes] = []
    for item in ranges:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return False
        start, end = item[0], item[1]
        if not isinstance(start, int) or not isinstance(end, int):
            return False
        if start < 0 or end < start or end > len(data):
            return False
        parts.append(data[start:end])
    return b"".join(parts) == payload_text.encode("utf-8")


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


def _normalized_units(
    sections: Mapping[str, str], intro: str
) -> Iterable[tuple[str, str]]:
    blocks = {"Introduction": intro}
    blocks.update(
        {name: sections[name] for name in SEMANTIC_SECTIONS if name in sections}
    )
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
                    normalized = re.sub(
                        r"\W+", " ", " ".join(paragraph).casefold()
                    ).strip()
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
            findings.append(
                Finding("CHECKLIST_STATUS_INVALID", path=path, detail=str(status))
            )
        elif status == "fail":
            findings.append(
                Finding("CHECKLIST_ITEM_FAILED", path=path, detail=str(item_id))
            )
        if not isinstance(evidence, str) or not evidence.strip():
            findings.append(Finding("CHECKLIST_EVIDENCE_INVALID", path=path))
    if len(value) != len(CHECKLIST_IDS):
        findings.append(
            Finding(
                "CHECKLIST_LENGTH_INVALID",
                path="checklist",
                detail=f"expected {len(CHECKLIST_IDS)}",
            )
        )
    if tuple(ids) != CHECKLIST_IDS:
        findings.append(
            Finding(
                "CHECKLIST_ORDER_INVALID",
                path="checklist",
                detail=f"expected {list(CHECKLIST_IDS)!r}",
            )
        )
    if len(ids) != len(set(ids)):
        findings.append(Finding("CHECKLIST_ID_DUPLICATE", path="checklist"))
    for item_id in ids:
        if item_id not in CHECKLIST_IDS:
            findings.append(
                Finding("CHECKLIST_ID_UNKNOWN", path="checklist", detail=item_id)
            )
    return _normalize(findings)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_effective_content_hash(
    evidence_bundle: Mapping[str, Any],
) -> tuple[str | None, list[Finding]]:
    """Return effective content hash and text-evidence findings for one evidence bundle.

    `content_hash` is SHA-256 over complete extracted readable UTF-8 text bytes with no
    newline, Unicode, or whitespace normalization. A model-visible `payload_text` may be a
    projection only when complete text bytes match the explicit hash and exact byte ranges
    reconstruct the visible payload. Media and binary asset fields are rejected.
    """
    findings: list[Finding] = []
    if not isinstance(evidence_bundle, Mapping):
        return None, [Finding("EVIDENCE_BUNDLE_INVALID", path="evidence")]
    findings.extend(_asset_field_findings(evidence_bundle))

    payload_text = evidence_bundle.get("payload_text")
    if not isinstance(payload_text, str):
        return None, findings + [
            Finding("EVIDENCE_PAYLOAD_TEXT_INVALID", path="evidence")
        ]
    if payload_text == "":
        return None, findings + [
            Finding("EVIDENCE_PAYLOAD_TEXT_INVALID", path="evidence", detail="empty")
        ]

    payload_hash = _sha256_text(payload_text)
    explicit_hash = evidence_bundle.get("content_hash")
    if "payload_projection" in evidence_bundle:
        projection = evidence_bundle["payload_projection"]
        if not isinstance(projection, bool):
            findings.append(
                Finding(
                    "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
                    path="evidence",
                    detail=f"non-boolean {projection!r}",
                )
            )
            projection = None
    else:
        projection = False

    complete_text = evidence_bundle.get("complete_text")
    if complete_text is not None and not isinstance(complete_text, str):
        findings.append(
            Finding(
                "EVIDENCE_COMPLETE_TEXT_INVALID", path="evidence", detail="non-string"
            )
        )
        complete_text = None
    elif isinstance(complete_text, str) and complete_text == "":
        findings.append(
            Finding("EVIDENCE_COMPLETE_TEXT_INVALID", path="evidence", detail="empty")
        )
        complete_text = None

    if explicit_hash is None:
        if projection is True:
            findings.append(
                Finding(
                    "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
                    path="evidence",
                    detail="true without explicit content_hash",
                )
            )
        if complete_text is not None and complete_text != payload_text:
            findings.append(
                Finding(
                    "EVIDENCE_COMPLETE_TEXT_MISMATCH",
                    path="evidence",
                    detail="complete_text must equal payload_text when not projecting",
                )
            )
        return (None if findings else payload_hash), findings

    if not isinstance(explicit_hash, str) or not CONTENT_HASH_RE.fullmatch(
        explicit_hash
    ):
        findings.append(
            Finding(
                "EVIDENCE_CONTENT_HASH_INVALID",
                path="evidence",
                detail=str(explicit_hash),
            )
        )
        return None, findings

    required_projection = explicit_hash != payload_hash
    if projection is not None and projection != required_projection:
        findings.append(
            Finding(
                "EVIDENCE_PAYLOAD_PROJECTION_INVALID",
                path="evidence",
                detail=(
                    f"expected {required_projection} for "
                    f"explicit_hash_differs={required_projection}"
                ),
            )
        )

    if required_projection or projection is True:
        if complete_text is None:
            findings.append(
                Finding(
                    "EVIDENCE_PROJECTION_UNBACKED",
                    path="evidence",
                    detail="complete_text required for projection",
                )
            )
            return None, findings
        complete_hash = _sha256_text(complete_text)
        if complete_hash != explicit_hash:
            findings.append(
                Finding(
                    "EVIDENCE_COMPLETE_TEXT_HASH_MISMATCH",
                    path="evidence",
                    detail=f"complete={complete_hash} explicit={explicit_hash}",
                )
            )
            return None, findings
        ranges = evidence_bundle.get("projection_ranges")
        if not _ranges_reconstruct_payload(complete_text, ranges, payload_text):
            findings.append(
                Finding(
                    "EVIDENCE_PROJECTION_UNBACKED",
                    path="evidence",
                    detail="projection_ranges must reconstruct payload_text bytes",
                )
            )
            return None, findings
        return (None if findings else explicit_hash), findings

    if complete_text is not None and complete_text != payload_text:
        findings.append(
            Finding(
                "EVIDENCE_COMPLETE_TEXT_MISMATCH",
                path="evidence",
                detail="complete_text must equal payload_text when not projecting",
            )
        )
        return None, findings
    if complete_text is not None and _sha256_text(complete_text) != explicit_hash:
        findings.append(
            Finding(
                "EVIDENCE_COMPLETE_TEXT_HASH_MISMATCH",
                path="evidence",
                detail="complete_text hash must equal explicit content_hash",
            )
        )
        return None, findings
    return (None if findings else explicit_hash), findings


def validate_summary(
    artifact_text: str,
    evidence_bundle: Mapping[str, Any],
    checklist: Any,
) -> list[Finding]:
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
            findings.append(
                Finding("FRONTMATTER_ENUM_INVALID", detail=f"{key}={frontmatter[key]}")
            )
    if "source_id" in frontmatter and not SOURCE_ID_RE.fullmatch(
        frontmatter["source_id"]
    ):
        findings.append(Finding("SOURCE_ID_INVALID"))
    if "content_hash" in frontmatter and not CONTENT_HASH_RE.fullmatch(
        frontmatter["content_hash"]
    ):
        findings.append(Finding("CONTENT_HASH_INVALID"))
    try:
        if int(frontmatter.get("source_seq", "0")) <= 0:
            raise ValueError
    except ValueError:
        findings.append(Finding("SOURCE_SEQ_INVALID"))
    published = frontmatter.get("published", "")
    if (
        published
        and published != "Unknown"
        and not PUBLICATION_DATE_RE.fullmatch(published)
    ):
        findings.append(Finding("FRONTMATTER_DATE_INVALID", detail="published"))
    for key in (
        "routed_at",
        "first_seen",
        "last_checked",
        "last_summarized",
        "refresh_after",
    ):
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

    effective_hash, hash_findings = resolve_effective_content_hash(evidence_bundle)
    findings.extend(hash_findings)
    if (
        effective_hash is not None
        and "content_hash" in frontmatter
        and CONTENT_HASH_RE.fullmatch(frontmatter["content_hash"])
        and frontmatter["content_hash"] != effective_hash
    ):
        findings.append(
            Finding(
                "CONTENT_HASH_MISMATCH",
                detail=f"artifact={frontmatter['content_hash']} effective={effective_hash}",
            )
        )
    # Empty or unproven text evidence is fail-closed: identity findings already recorded.

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
            Finding(
                "PLACEHOLDER_UNRESOLVED",
                line=_line_number(artifact_text, match.group(0)),
                detail=match.group(0),
            )
        )

    assessment = _assessment_values(sections.get("Assessment", ""))
    for key in ASSESSMENT_LABELS.values():
        if key not in assessment:
            findings.append(
                Finding("ASSESSMENT_SIGNAL_MISSING", section="Assessment", detail=key)
            )
        elif frontmatter.get(key) != assessment[key]:
            findings.append(
                Finding(
                    "ASSESSMENT_FRONTMATTER_MISMATCH",
                    section="Assessment",
                    detail=f"{key}: {frontmatter.get(key)!r} != {assessment[key]!r}",
                )
            )
    assessment_text = sections.get("Assessment", "")
    for note in GENERIC_ASSESSMENT_NOTES:
        if note in assessment_text:
            findings.append(
                Finding(
                    "ASSESSMENT_NOTE_BOILERPLATE",
                    line=_line_number(artifact_text, note),
                    section="Assessment",
                    detail=note,
                )
            )

    semantic = _semantic_text(sections, intro)
    for pattern, code in (
        (GENERATED_CONTEXT_RE, "GENERATED_CONTEXT_LEAK"),
        (REPOSITORY_CONTEXT_RE, "REPOSITORY_CONTEXT_LEAK"),
    ):
        for match in pattern.finditer(semantic):
            findings.append(
                Finding(
                    code,
                    line=_line_number(artifact_text, match.group(0)),
                    detail=match.group(0),
                )
            )
    forbidden_terms = evidence_bundle.get("forbidden_context_terms", [])
    if not isinstance(forbidden_terms, list) or not all(
        isinstance(item, str) for item in forbidden_terms
    ):
        findings.append(Finding("EVIDENCE_FORBIDDEN_TERMS_INVALID", path="evidence"))
    else:
        for term in forbidden_terms:
            if term and re.search(re.escape(term), semantic, re.IGNORECASE):
                findings.append(Finding("AMBIENT_CONTEXT_LEAK", detail=term))

    allowed_urls, url_findings = _bundle_urls(evidence_bundle)
    findings.extend(url_findings)
    canonical = frontmatter.get("canonical_url")
    if (
        isinstance(evidence_bundle.get("canonical_url"), str)
        and canonical != evidence_bundle["canonical_url"]
    ):
        findings.append(Finding("CANONICAL_URL_MISMATCH"))
    for match in URL_RE.finditer(semantic):
        url = _strip_url(match.group(0))
        if url not in allowed_urls:
            findings.append(
                Finding(
                    "URL_OUTSIDE_EVIDENCE",
                    line=_line_number(artifact_text, match.group(0)),
                    detail=url,
                )
            )

    seen_units: dict[str, str] = {}
    for section, normalized in _normalized_units(sections, intro):
        previous = seen_units.get(normalized)
        if previous is not None:
            findings.append(
                Finding(
                    "EXACT_NORMALIZED_DUPLICATE",
                    section=section,
                    detail=f"duplicates {previous}",
                )
            )
        else:
            seen_units[normalized] = section

    if frontmatter.get("evidence_strength") == "high":
        evidence_lines = [
            line.strip()
            for line in sections.get("Evidence / examples", "").splitlines()
        ]
        if not any(LOCATOR_RE.match(line) for line in evidence_lines):
            findings.append(
                Finding("SOURCE_LOCATOR_MISSING", section="Evidence / examples")
            )

    routing = sections.get("Routing notes", "")
    verifier_lines = []
    for line in routing.splitlines():
        stripped = line.strip()
        if "Verifier:" in stripped:
            verifier_lines.append(stripped.lstrip("- ").strip())
    require_routing_reason = evidence_bundle.get("require_routing_reason") is True
    if (
        require_routing_reason
        and frontmatter.get("routing_status") == "routed"
        and not verifier_lines
    ):
        findings.append(Finding("ROUTING_REASON_MISSING", section="Routing notes"))
    for reason in verifier_lines:
        if REASON_RE.fullmatch(reason) is None:
            findings.append(
                Finding(
                    "ROUTING_REASON_INVALID", section="Routing notes", detail=reason
                )
            )
    if (
        require_routing_reason
        and re.search(
            r"Candidate topic matches considered:[^\n]+$", routing, re.MULTILINE
        )
        and not verifier_lines
        and frontmatter.get("routing_status") == "routed"
    ):
        findings.append(Finding("ROUTING_CANDIDATE_ONLY", section="Routing notes"))

    findings.extend(validate_checklist(checklist))
    return _normalize(findings)


def _strict_mapping(
    value: Any,
    required: frozenset[str],
    *,
    path: str,
    invalid_code: str,
    missing_code: str,
    unknown_code: str,
    findings: list[Finding],
) -> Mapping[str, Any] | None:
    if not isinstance(value, Mapping):
        findings.append(Finding(invalid_code, path=path))
        return None
    unknown = sorted(set(value) - required)
    missing = sorted(required - set(value))
    for key in unknown:
        findings.append(Finding(unknown_code, path=path, detail=key))
    for key in missing:
        findings.append(Finding(missing_code, path=path, detail=key))
    return value


def _is_int(value: Any) -> bool:
    return type(value) is int


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and CONTENT_HASH_RE.fullmatch(value) is not None


def _is_revision(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None
    )


def _is_http_url(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"https?://\S+", value) is not None


def _contains_context(value: Any) -> bool:
    if isinstance(value, str):
        return bool(
            GENERATED_CONTEXT_RE.search(value) or REPOSITORY_CONTEXT_RE.search(value)
        )
    if isinstance(value, Mapping):
        return any(_contains_context(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_context(item) for item in value)
    return False


def validate_proposal(proposal: Any, evidence_ledger: Any) -> list[Finding]:
    """Validate a model-owned source proposal against its source-local ledger."""
    findings: list[Finding] = []
    value = _strict_mapping(
        proposal,
        frozenset({"version", "metadata", "assessment", "claims", "links"}),
        path="proposal",
        invalid_code="PROPOSAL_SHAPE_INVALID",
        missing_code="PROPOSAL_FIELD_MISSING",
        unknown_code="PROPOSAL_UNKNOWN_KEY",
        findings=findings,
    )
    if value is None:
        return _normalize(findings)
    if not (_is_int(value.get("version")) and value.get("version") == VERSION):
        findings.append(Finding("PROPOSAL_VERSION_INVALID", path="proposal"))

    metadata = _strict_mapping(
        value.get("metadata"),
        frozenset({"title", "author", "publisher", "published", "source_kind"}),
        path="proposal.metadata",
        invalid_code="PROPOSAL_METADATA_INVALID",
        missing_code="PROPOSAL_FIELD_MISSING",
        unknown_code="PROPOSAL_UNKNOWN_KEY",
        findings=findings,
    )
    if metadata is not None:
        for key in ("title", "author", "publisher"):
            if not _is_nonempty_text(metadata.get(key)):
                findings.append(
                    Finding(
                        "PROPOSAL_TYPE_INVALID", path="proposal.metadata", detail=key
                    )
                )
        published = metadata.get("published")
        if not (
            published == "Unknown"
            or (
                isinstance(published, str)
                and PUBLICATION_DATE_RE.fullmatch(published) is not None
            )
        ):
            findings.append(
                Finding("PROPOSAL_PUBLICATION_INVALID", path="proposal.metadata")
            )
        if metadata.get("source_kind") not in ENUMS["source_kind"]:
            findings.append(
                Finding(
                    "PROPOSAL_ENUM_INVALID",
                    path="proposal.metadata",
                    detail="source_kind",
                )
            )

    assessment = _strict_mapping(
        value.get("assessment"),
        frozenset(ASSESSMENT_LABELS.values()),
        path="proposal.assessment",
        invalid_code="PROPOSAL_ASSESSMENT_INVALID",
        missing_code="PROPOSAL_FIELD_MISSING",
        unknown_code="PROPOSAL_UNKNOWN_KEY",
        findings=findings,
    )
    if assessment is not None:
        for key in ASSESSMENT_LABELS.values():
            if assessment.get(key) not in ENUMS[key]:
                findings.append(
                    Finding(
                        "PROPOSAL_ENUM_INVALID",
                        path="proposal.assessment",
                        detail=key,
                    )
                )

    ledger = _strict_mapping(
        evidence_ledger,
        frozenset({"version", "evidence", "links"}),
        path="ledger",
        invalid_code="PROPOSAL_LEDGER_INVALID",
        missing_code="PROPOSAL_LEDGER_INVALID",
        unknown_code="PROPOSAL_LEDGER_INVALID",
        findings=findings,
    )
    evidence_bindings: set[tuple[str, str]] = set()
    link_bindings: set[tuple[str, str, str]] = set()
    if ledger is not None:
        if not (_is_int(ledger.get("version")) and ledger.get("version") == VERSION):
            findings.append(Finding("PROPOSAL_LEDGER_INVALID", path="ledger"))
        ledger_evidence = ledger.get("evidence")
        if not isinstance(ledger_evidence, list):
            findings.append(Finding("PROPOSAL_LEDGER_INVALID", path="ledger.evidence"))
        else:
            for index, item in enumerate(ledger_evidence):
                item_value = _strict_mapping(
                    item,
                    frozenset({"locator", "ledger_id"}),
                    path=f"ledger.evidence[{index}]",
                    invalid_code="PROPOSAL_LEDGER_INVALID",
                    missing_code="PROPOSAL_LEDGER_INVALID",
                    unknown_code="PROPOSAL_LEDGER_INVALID",
                    findings=findings,
                )
                if (
                    item_value is not None
                    and _is_nonempty_text(item_value.get("locator"))
                    and _is_nonempty_text(item_value.get("ledger_id"))
                ):
                    evidence_bindings.add(
                        (item_value["locator"], item_value["ledger_id"])
                    )
                elif item_value is not None:
                    findings.append(
                        Finding(
                            "PROPOSAL_LEDGER_INVALID",
                            path=f"ledger.evidence[{index}]",
                        )
                    )
        ledger_links = ledger.get("links")
        if not isinstance(ledger_links, list):
            findings.append(Finding("PROPOSAL_LEDGER_INVALID", path="ledger.links"))
        else:
            for index, item in enumerate(ledger_links):
                item_value = _strict_mapping(
                    item,
                    frozenset({"url", "locator", "ledger_id"}),
                    path=f"ledger.links[{index}]",
                    invalid_code="PROPOSAL_LEDGER_INVALID",
                    missing_code="PROPOSAL_LEDGER_INVALID",
                    unknown_code="PROPOSAL_LEDGER_INVALID",
                    findings=findings,
                )
                if (
                    item_value is not None
                    and _is_http_url(item_value.get("url"))
                    and _is_nonempty_text(item_value.get("locator"))
                    and _is_nonempty_text(item_value.get("ledger_id"))
                ):
                    link_bindings.add(
                        (
                            item_value["url"],
                            item_value["locator"],
                            item_value["ledger_id"],
                        )
                    )
                elif item_value is not None:
                    findings.append(
                        Finding(
                            "PROPOSAL_LEDGER_INVALID", path=f"ledger.links[{index}]"
                        )
                    )

    claims = value.get("claims")
    if not isinstance(claims, list) or not claims:
        findings.append(Finding("PROPOSAL_CLAIMS_INVALID", path="proposal.claims"))
    else:
        for index, claim in enumerate(claims):
            claim_value = _strict_mapping(
                claim,
                frozenset({"statement", "evidence"}),
                path=f"proposal.claims[{index}]",
                invalid_code="PROPOSAL_CLAIM_INVALID",
                missing_code="PROPOSAL_FIELD_MISSING",
                unknown_code="PROPOSAL_UNKNOWN_KEY",
                findings=findings,
            )
            if claim_value is None:
                continue
            if not _is_nonempty_text(claim_value.get("statement")):
                findings.append(
                    Finding(
                        "PROPOSAL_TYPE_INVALID",
                        path=f"proposal.claims[{index}]",
                        detail="statement",
                    )
                )
            evidence = claim_value.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                findings.append(
                    Finding(
                        "PROPOSAL_EVIDENCE_INVALID",
                        path=f"proposal.claims[{index}]",
                    )
                )
                continue
            for evidence_index, reference in enumerate(evidence):
                reference_value = _strict_mapping(
                    reference,
                    frozenset({"locator", "ledger_id"}),
                    path=f"proposal.claims[{index}].evidence[{evidence_index}]",
                    invalid_code="PROPOSAL_EVIDENCE_INVALID",
                    missing_code="PROPOSAL_FIELD_MISSING",
                    unknown_code="PROPOSAL_UNKNOWN_KEY",
                    findings=findings,
                )
                if reference_value is None:
                    continue
                locator = reference_value.get("locator")
                ledger_id = reference_value.get("ledger_id")
                if not _is_nonempty_text(locator) or not _is_nonempty_text(ledger_id):
                    findings.append(
                        Finding(
                            "PROPOSAL_EVIDENCE_INVALID",
                            path=f"proposal.claims[{index}].evidence[{evidence_index}]",
                        )
                    )
                elif (locator, ledger_id) not in evidence_bindings:
                    findings.append(
                        Finding(
                            "PROPOSAL_EVIDENCE_LOCATOR_UNBOUND",
                            path=f"proposal.claims[{index}].evidence[{evidence_index}]",
                        )
                    )

    links = value.get("links")
    if not isinstance(links, list) or not links:
        findings.append(Finding("PROPOSAL_LINKS_INVALID", path="proposal.links"))
    else:
        for index, link in enumerate(links):
            link_value = _strict_mapping(
                link,
                frozenset({"url", "relation", "locator", "ledger_id"}),
                path=f"proposal.links[{index}]",
                invalid_code="PROPOSAL_LINK_INVALID",
                missing_code="PROPOSAL_FIELD_MISSING",
                unknown_code="PROPOSAL_UNKNOWN_KEY",
                findings=findings,
            )
            if link_value is None:
                continue
            url = link_value.get("url")
            locator = link_value.get("locator")
            ledger_id = link_value.get("ledger_id")
            if not _is_http_url(url):
                findings.append(
                    Finding(
                        "PROPOSAL_LINK_INVALID",
                        path=f"proposal.links[{index}]",
                        detail="url",
                    )
                )
            if link_value.get("relation") not in {"canonical", "related", "cited"}:
                findings.append(
                    Finding(
                        "PROPOSAL_ENUM_INVALID",
                        path=f"proposal.links[{index}]",
                        detail="relation",
                    )
                )
            if not _is_nonempty_text(locator) or not _is_nonempty_text(ledger_id):
                findings.append(
                    Finding("PROPOSAL_LINK_INVALID", path=f"proposal.links[{index}]")
                )
            elif (url, locator, ledger_id) not in link_bindings:
                findings.append(
                    Finding(
                        "PROPOSAL_LINK_LEDGER_UNBOUND",
                        path=f"proposal.links[{index}]",
                    )
                )

    if _contains_context(
        {
            "metadata": value.get("metadata"),
            "claims": value.get("claims"),
            "links": value.get("links"),
        }
    ):
        findings.append(Finding("PROPOSAL_CONTEXT_LEAK", path="proposal"))
    return _normalize(findings)


def validate_fresh_source_assessment(assessment: Any, packet: Any) -> list[Finding]:
    """Validate an assessment's sealed fresh-capture and review bindings."""
    findings: list[Finding] = []
    value = _strict_mapping(
        assessment,
        frozenset(
            {
                "version",
                "freeze",
                "packet",
                "capture",
                "identity_alignment",
                "page_form",
                "page_summary_adequacy",
                "resource_intent",
                "dimensions",
                "findings",
                "evidence",
                "review",
                "actions",
                "drift",
                "index",
            }
        ),
        path="fresh",
        invalid_code="FRESH_ASSESSMENT_INVALID",
        missing_code="FRESH_FIELD_MISSING",
        unknown_code="FRESH_UNKNOWN_KEY",
        findings=findings,
    )
    if value is None:
        return _normalize(findings)
    if not (_is_int(value.get("version")) and value.get("version") == VERSION):
        findings.append(Finding("FRESH_VERSION_INVALID", path="fresh"))

    assessment_packet = _strict_mapping(
        value.get("packet"),
        frozenset(
            {
                "packet_sha256",
                "capture_sha256",
                "text_blob_sha256",
                "ledger_sha256",
                "rubric_version",
            }
        ),
        path="fresh.packet",
        invalid_code="FRESH_PACKET_INVALID",
        missing_code="FRESH_PACKET_INVALID",
        unknown_code="FRESH_PACKET_UNKNOWN_KEY",
        findings=findings,
    )
    if isinstance(value.get("packet"), Mapping):
        for key in ("history", "provider", "request"):
            if key in value["packet"]:
                findings.append(
                    Finding("FRESH_CONTEXT_LEAK", path="fresh.packet", detail=key)
                )

    external_packet = _strict_mapping(
        packet,
        frozenset(
            {
                "version",
                "freeze",
                "packet_sha256",
                "capture_sha256",
                "text_blob_sha256",
                "ledger_sha256",
                "rubric_version",
                "text_blobs",
                "links",
            }
        ),
        path="packet",
        invalid_code="FRESH_PACKET_INVALID",
        missing_code="FRESH_PACKET_INVALID",
        unknown_code="FRESH_PACKET_UNKNOWN_KEY",
        findings=findings,
    )
    if isinstance(packet, Mapping):
        for key in ("history", "provider", "request"):
            if key in packet:
                findings.append(
                    Finding("FRESH_CONTEXT_LEAK", path="packet", detail=key)
                )
    if external_packet is not None and not (
        _is_int(external_packet.get("version"))
        and external_packet.get("version") == VERSION
        and _is_int(external_packet.get("rubric_version"))
        and external_packet.get("rubric_version") == VERSION
    ):
        findings.append(Finding("FRESH_PACKET_INVALID", path="packet"))
    if assessment_packet is not None and not (
        _is_int(assessment_packet.get("rubric_version"))
        and assessment_packet.get("rubric_version") == VERSION
    ):
        findings.append(Finding("FRESH_PACKET_INVALID", path="fresh.packet"))

    freeze_keys = frozenset(
        {
            "source_id",
            "source_seq",
            "canonical_url",
            "manifest_row_hash",
            "artifact_revision",
            "snapshot_hash",
        }
    )
    freeze = _strict_mapping(
        value.get("freeze"),
        freeze_keys,
        path="fresh.freeze",
        invalid_code="FRESH_FREEZE_INVALID",
        missing_code="FRESH_FREEZE_INVALID",
        unknown_code="FRESH_FREEZE_UNKNOWN_KEY",
        findings=findings,
    )
    packet_freeze = (
        _strict_mapping(
            external_packet.get("freeze"),
            freeze_keys,
            path="packet.freeze",
            invalid_code="FRESH_PACKET_INVALID",
            missing_code="FRESH_PACKET_INVALID",
            unknown_code="FRESH_PACKET_UNKNOWN_KEY",
            findings=findings,
        )
        if external_packet is not None
        else None
    )
    if freeze is not None:
        if not (
            isinstance(freeze.get("source_id"), str)
            and SOURCE_ID_RE.fullmatch(freeze["source_id"]) is not None
            and _is_int(freeze.get("source_seq"))
            and freeze["source_seq"] > 0
            and _is_http_url(freeze.get("canonical_url"))
            and _is_sha256(freeze.get("manifest_row_hash"))
            and _is_revision(freeze.get("artifact_revision"))
            and _is_sha256(freeze.get("snapshot_hash"))
        ):
            findings.append(Finding("FRESH_FREEZE_INVALID", path="fresh.freeze"))
    if freeze is not None and packet_freeze is not None and freeze != packet_freeze:
        findings.append(Finding("FRESH_FREEZE_MISMATCH", path="fresh.freeze"))

    if assessment_packet is not None and external_packet is not None:
        for key in (
            "packet_sha256",
            "capture_sha256",
            "text_blob_sha256",
            "ledger_sha256",
        ):
            if not _is_sha256(assessment_packet.get(key)):
                findings.append(
                    Finding("FRESH_PACKET_INVALID", path="fresh.packet", detail=key)
                )
            if assessment_packet.get(key) != external_packet.get(key):
                findings.append(
                    Finding(
                        "FRESH_PACKET_HASH_MISMATCH", path="fresh.packet", detail=key
                    )
                )

    capture = _strict_mapping(
        value.get("capture"),
        frozenset(
            {
                "state",
                "access",
                "representation",
                "text_blob_sha256",
                "final_url",
                "http_status",
            }
        ),
        path="fresh.capture",
        invalid_code="FRESH_CAPTURE_INVALID",
        missing_code="FRESH_CAPTURE_INVALID",
        unknown_code="FRESH_CAPTURE_UNKNOWN_KEY",
        findings=findings,
    )
    if capture is not None:
        if capture.get("state") not in {
            "completed",
            "pending-systemic",
            "invalid-input",
        }:
            findings.append(
                Finding("FRESH_CAPTURE_INVALID", path="fresh.capture", detail="state")
            )
        if capture.get("access") not in {
            "available",
            "unauthorized",
            "inaccessible",
            "response-error",
        }:
            findings.append(
                Finding("FRESH_CAPTURE_INVALID", path="fresh.capture", detail="access")
            )
        if capture.get("representation") not in {
            "readable-text",
            "empty",
            "non-text",
            "error-document",
            "not-applicable",
        }:
            findings.append(
                Finding(
                    "FRESH_CAPTURE_INVALID",
                    path="fresh.capture",
                    detail="representation",
                )
            )
        if capture.get("final_url") is not None and not _is_http_url(
            capture.get("final_url")
        ):
            findings.append(
                Finding(
                    "FRESH_CAPTURE_INVALID", path="fresh.capture", detail="final_url"
                )
            )
        status = capture.get("http_status")
        if status is not None and not (_is_int(status) and 100 <= status <= 599):
            findings.append(
                Finding(
                    "FRESH_CAPTURE_INVALID", path="fresh.capture", detail="http_status"
                )
            )
        if (
            assessment_packet is None
            or capture.get("text_blob_sha256")
            != assessment_packet.get("text_blob_sha256")
            or not _is_sha256(capture.get("text_blob_sha256"))
        ):
            findings.append(
                Finding("FRESH_TEXT_BLOB_HASH_MISMATCH", path="fresh.capture")
            )

    text_blobs: dict[str, str] = {}
    if external_packet is not None:
        blob_values = external_packet.get("text_blobs")
        if not isinstance(blob_values, list):
            findings.append(Finding("FRESH_PACKET_INVALID", path="packet.text_blobs"))
        else:
            for index, blob in enumerate(blob_values):
                blob_value = _strict_mapping(
                    blob,
                    frozenset({"sha256", "utf8_text"}),
                    path=f"packet.text_blobs[{index}]",
                    invalid_code="FRESH_PACKET_INVALID",
                    missing_code="FRESH_PACKET_INVALID",
                    unknown_code="FRESH_PACKET_UNKNOWN_KEY",
                    findings=findings,
                )
                if (
                    blob_value is None
                    or not _is_sha256(blob_value.get("sha256"))
                    or not isinstance(blob_value.get("utf8_text"), str)
                ):
                    findings.append(
                        Finding(
                            "FRESH_PACKET_INVALID", path=f"packet.text_blobs[{index}]"
                        )
                    )
                    continue
                encoded = blob_value["utf8_text"].encode("utf-8")
                if hashlib.sha256(encoded).hexdigest() != blob_value["sha256"]:
                    findings.append(
                        Finding(
                            "FRESH_TEXT_BLOB_HASH_MISMATCH",
                            path=f"packet.text_blobs[{index}]",
                        )
                    )
                    continue
                text_blobs[blob_value["sha256"]] = blob_value["utf8_text"]

    evidence = _strict_mapping(
        value.get("evidence"),
        frozenset({"excerpts", "links"}),
        path="fresh.evidence",
        invalid_code="FRESH_EVIDENCE_INVALID",
        missing_code="FRESH_EVIDENCE_INVALID",
        unknown_code="FRESH_EVIDENCE_UNKNOWN_KEY",
        findings=findings,
    )
    evidence_ids: set[str] = set()
    if evidence is not None:
        excerpts = evidence.get("excerpts")
        if not isinstance(excerpts, list):
            findings.append(
                Finding("FRESH_EVIDENCE_INVALID", path="fresh.evidence.excerpts")
            )
        else:
            for index, excerpt in enumerate(excerpts):
                excerpt_value = _strict_mapping(
                    excerpt,
                    frozenset(
                        {
                            "id",
                            "blob_sha256",
                            "start_byte",
                            "end_byte",
                            "excerpt_sha256",
                        }
                    ),
                    path=f"fresh.evidence.excerpts[{index}]",
                    invalid_code="FRESH_EXCERPT_INVALID",
                    missing_code="FRESH_EXCERPT_INVALID",
                    unknown_code="FRESH_EXCERPT_INVALID",
                    findings=findings,
                )
                if excerpt_value is None:
                    continue
                excerpt_id = excerpt_value.get("id")
                blob_hash = excerpt_value.get("blob_sha256")
                start = excerpt_value.get("start_byte")
                end = excerpt_value.get("end_byte")
                excerpt_hash = excerpt_value.get("excerpt_sha256")
                valid = (
                    _is_nonempty_text(excerpt_id)
                    and _is_sha256(blob_hash)
                    and _is_int(start)
                    and _is_int(end)
                    and start >= 0
                    and end > start
                    and _is_sha256(excerpt_hash)
                    and blob_hash in text_blobs
                )
                if valid:
                    raw = text_blobs[blob_hash].encode("utf-8")
                    valid = end <= len(raw)
                    if valid:
                        try:
                            excerpt_text = raw[start:end].decode("utf-8")
                        except UnicodeDecodeError:
                            valid = False
                        else:
                            valid = (
                                hashlib.sha256(excerpt_text.encode("utf-8")).hexdigest()
                                == excerpt_hash
                            )
                if not valid or excerpt_id in evidence_ids:
                    findings.append(
                        Finding(
                            "FRESH_EXCERPT_INVALID",
                            path=f"fresh.evidence.excerpts[{index}]",
                        )
                    )
                    continue
                evidence_ids.add(excerpt_id)

        packet_links: dict[str, Mapping[str, Any]] = {}
        if external_packet is not None:
            raw_packet_links = external_packet.get("links")
            if not isinstance(raw_packet_links, list):
                findings.append(Finding("FRESH_PACKET_INVALID", path="packet.links"))
            else:
                for link in raw_packet_links:
                    if isinstance(link, Mapping) and isinstance(link.get("id"), str):
                        packet_links[link["id"]] = link
        links = evidence.get("links")
        if not isinstance(links, list):
            findings.append(
                Finding("FRESH_EVIDENCE_INVALID", path="fresh.evidence.links")
            )
        else:
            link_keys = frozenset(
                {
                    "id",
                    "canonical_url",
                    "source_id",
                    "anchor",
                    "locator",
                    "normalization_status",
                    "raw_href_sha256",
                    "display",
                    "reason",
                }
            )
            for index, link in enumerate(links):
                link_value = _strict_mapping(
                    link,
                    link_keys,
                    path=f"fresh.evidence.links[{index}]",
                    invalid_code="FRESH_LINK_INVALID",
                    missing_code="FRESH_LINK_INVALID",
                    unknown_code="FRESH_LINK_INVALID",
                    findings=findings,
                )
                if link_value is None:
                    continue
                link_id = link_value.get("id")
                valid = (
                    _is_nonempty_text(link_id)
                    and (
                        link_value.get("canonical_url") is None
                        or _is_http_url(link_value.get("canonical_url"))
                    )
                    and (
                        link_value.get("source_id") is None
                        or (
                            isinstance(link_value.get("source_id"), str)
                            and SOURCE_ID_RE.fullmatch(link_value["source_id"])
                            is not None
                        )
                    )
                    and isinstance(link_value.get("anchor"), str)
                    and _is_nonempty_text(link_value.get("locator"))
                    and link_value.get("normalization_status")
                    in {"accepted", "rejected"}
                    and _is_sha256(link_value.get("raw_href_sha256"))
                    and _is_nonempty_text(link_value.get("display"))
                    and (
                        link_value.get("reason") is None
                        or _is_nonempty_text(link_value.get("reason"))
                    )
                )
                if not valid:
                    findings.append(
                        Finding(
                            "FRESH_LINK_INVALID", path=f"fresh.evidence.links[{index}]"
                        )
                    )
                elif link_id not in packet_links or packet_links[link_id] != link_value:
                    findings.append(
                        Finding(
                            "FRESH_LINK_LEDGER_UNBOUND",
                            path=f"fresh.evidence.links[{index}]",
                        )
                    )
                elif link_id in evidence_ids:
                    findings.append(
                        Finding(
                            "FRESH_LINK_INVALID", path=f"fresh.evidence.links[{index}]"
                        )
                    )
                else:
                    evidence_ids.add(link_id)

    dimension_keys = frozenset(
        {"capture", "identity", "page_form", "adequacy", "intent"}
    )
    dimensions = _strict_mapping(
        value.get("dimensions"),
        dimension_keys,
        path="fresh.dimensions",
        invalid_code="FRESH_DIMENSION_INVALID",
        missing_code="FRESH_DIMENSION_INVALID",
        unknown_code="FRESH_DIMENSION_INVALID",
        findings=findings,
    )
    if dimensions is not None:
        for name in dimension_keys:
            dimension = _strict_mapping(
                dimensions.get(name),
                frozenset({"state", "evidence_refs"}),
                path=f"fresh.dimensions.{name}",
                invalid_code="FRESH_DIMENSION_INVALID",
                missing_code="FRESH_DIMENSION_INVALID",
                unknown_code="FRESH_DIMENSION_INVALID",
                findings=findings,
            )
            if dimension is None:
                continue
            refs = dimension.get("evidence_refs")
            if (
                dimension.get("state") not in {"pass", "fail", "unassessed"}
                or not isinstance(refs, list)
                or not all(isinstance(item, str) for item in refs)
                or len(set(refs)) != len(refs)
                or any(item not in evidence_ids for item in refs)
            ):
                findings.append(
                    Finding(
                        "FRESH_DIMENSION_EVIDENCE_UNBOUND",
                        path=f"fresh.dimensions.{name}",
                    )
                )

    findings_value = value.get("findings")
    finding_codes: set[str] = set()
    if not isinstance(findings_value, list):
        findings.append(Finding("FRESH_FINDINGS_INVALID", path="fresh.findings"))
    else:
        allowed_finding_codes = {
            "aggregate",
            "thin-standalone",
            "canonical-mismatch",
            "inaccessible",
            "unauthorized",
            "empty",
            "non-text",
            "error-document",
            "insufficient",
            "response-error",
        }
        for index, finding in enumerate(findings_value):
            finding_value = _strict_mapping(
                finding,
                frozenset({"code", "dimensions", "evidence_refs"}),
                path=f"fresh.findings[{index}]",
                invalid_code="FRESH_FINDING_INVALID",
                missing_code="FRESH_FINDING_INVALID",
                unknown_code="FRESH_FINDING_INVALID",
                findings=findings,
            )
            if finding_value is None:
                continue
            code = finding_value.get("code")
            dimensions_for_finding = finding_value.get("dimensions")
            refs = finding_value.get("evidence_refs")
            if (
                code not in allowed_finding_codes
                or code in finding_codes
                or not isinstance(dimensions_for_finding, list)
                or not dimensions_for_finding
                or len(set(dimensions_for_finding)) != len(dimensions_for_finding)
                or any(name not in dimension_keys for name in dimensions_for_finding)
            ):
                findings.append(
                    Finding("FRESH_FINDING_INVALID", path=f"fresh.findings[{index}]")
                )
            else:
                finding_codes.add(code)
            if (
                not isinstance(refs, list)
                or not refs
                or not all(isinstance(item, str) for item in refs)
                or len(set(refs)) != len(refs)
                or any(item not in evidence_ids for item in refs)
            ):
                findings.append(
                    Finding(
                        "FRESH_FINDING_EVIDENCE_UNBOUND",
                        path=f"fresh.findings[{index}]",
                    )
                )

    identity = _strict_mapping(
        value.get("identity_alignment"),
        frozenset(
            {"normalized_final_url", "page_declared_canonical", "evidence_strength"}
        ),
        path="fresh.identity_alignment",
        invalid_code="FRESH_IDENTITY_INVALID",
        missing_code="FRESH_IDENTITY_INVALID",
        unknown_code="FRESH_IDENTITY_INVALID",
        findings=findings,
    )
    if identity is not None and (
        identity.get("normalized_final_url")
        not in {"same", "different", "indeterminate"}
        or identity.get("page_declared_canonical")
        not in {"same", "different", "indeterminate"}
        or identity.get("evidence_strength") not in {"high", "medium", "low"}
    ):
        findings.append(
            Finding("FRESH_IDENTITY_INVALID", path="fresh.identity_alignment")
        )

    page_form = value.get("page_form")
    if page_form not in {"standalone", "aggregate", "indeterminate", "not-applicable"}:
        findings.append(Finding("FRESH_PAGE_FORM_INVALID", path="fresh.page_form"))
    adequacy = _strict_mapping(
        value.get("page_summary_adequacy"),
        frozenset({"value", "page_supports"}),
        path="fresh.page_summary_adequacy",
        invalid_code="FRESH_ADEQUACY_INVALID",
        missing_code="FRESH_ADEQUACY_INVALID",
        unknown_code="FRESH_ADEQUACY_INVALID",
        findings=findings,
    )
    if adequacy is not None:
        supports = adequacy.get("page_supports")
        if (
            adequacy.get("value") not in {"sufficient", "insufficient", "unassessed"}
            or not isinstance(supports, list)
            or not all(isinstance(item, str) for item in supports)
            or len(set(supports)) != len(supports)
            or any(item not in evidence_ids for item in supports)
        ):
            findings.append(
                Finding("FRESH_ADEQUACY_INVALID", path="fresh.page_summary_adequacy")
            )

    intent = _strict_mapping(
        value.get("resource_intent"),
        frozenset(
            {
                "kind",
                "declared_text",
                "provenance",
                "fit",
                "missing_for_resource_intent",
            }
        ),
        path="fresh.resource_intent",
        invalid_code="FRESH_INTENT_INVALID",
        missing_code="FRESH_INTENT_INVALID",
        unknown_code="FRESH_INTENT_INVALID",
        findings=findings,
    )
    if intent is not None:
        kind = intent.get("kind")
        declared_text = intent.get("declared_text")
        provenance = intent.get("provenance")
        missing_intent = intent.get("missing_for_resource_intent")
        valid_declared = _is_nonempty_text(declared_text) and _is_nonempty_text(
            provenance
        )
        valid_undeclared = declared_text is None and provenance is None
        if (
            kind not in {"unknown", "page-itself", "declared"}
            or intent.get("fit") not in {"supports", "misses", "unassessed"}
            or not isinstance(missing_intent, list)
            or not all(isinstance(item, str) for item in missing_intent)
            or len(set(missing_intent)) != len(missing_intent)
            or any(item not in evidence_ids for item in missing_intent)
            or (kind == "declared" and not valid_declared)
            or (kind != "declared" and not valid_undeclared)
        ):
            findings.append(
                Finding("FRESH_INTENT_INVALID", path="fresh.resource_intent")
            )

    review = _strict_mapping(
        value.get("review"),
        frozenset({"primary", "secondary"}),
        path="fresh.review",
        invalid_code="FRESH_REVIEW_INVALID",
        missing_code="FRESH_REVIEW_INVALID",
        unknown_code="FRESH_REVIEW_INVALID",
        findings=findings,
    )
    review_records: list[Mapping[str, Any]] = []
    if review is not None:
        for role in ("primary", "secondary"):
            record = review.get(role)
            if role == "secondary" and record is None:
                continue
            record_value = _strict_mapping(
                record,
                frozenset(
                    {
                        "review_id",
                        "assessment_sha256",
                        "packet_sha256",
                        "blinded",
                        "verdict",
                    }
                ),
                path=f"fresh.review.{role}",
                invalid_code="FRESH_REVIEW_INVALID",
                missing_code="FRESH_REVIEW_INVALID",
                unknown_code="FRESH_REVIEW_INVALID",
                findings=findings,
            )
            if record_value is None:
                continue
            if (
                not _is_nonempty_text(record_value.get("review_id"))
                or not _is_sha256(record_value.get("assessment_sha256"))
                or not _is_sha256(record_value.get("packet_sha256"))
                or record_value.get("blinded") is not True
                or record_value.get("verdict")
                not in {"accepted", "flagged", "invalid", "ambiguous"}
            ):
                findings.append(
                    Finding("FRESH_REVIEW_INVALID", path=f"fresh.review.{role}")
                )
            else:
                review_records.append(record_value)

    actions = _strict_mapping(
        value.get("actions"),
        frozenset({"allowed", "recommended", "write_set"}),
        path="fresh.actions",
        invalid_code="FRESH_ACTION_INVALID",
        missing_code="FRESH_ACTION_INVALID",
        unknown_code="FRESH_ACTION_INVALID",
        findings=findings,
    )
    action_values = {
        "record-assessment",
        "ask-resource-intent",
        "ask-aggregate-scope",
        "queue-resolution",
        "no-write",
        "page-only",
        "add-companion",
        "replace",
        "defer",
    }
    write_values = {"assessment-record", "intent-record", "candidate-record"}
    if actions is not None:
        allowed = actions.get("allowed")
        recommended = actions.get("recommended")
        write_set = actions.get("write_set")
        valid_actions = (
            isinstance(allowed, list)
            and isinstance(recommended, list)
            and isinstance(write_set, list)
            and all(isinstance(item, str) and item in action_values for item in allowed)
            and all(
                isinstance(item, str) and item in action_values for item in recommended
            )
            and all(
                isinstance(item, str) and item in write_values for item in write_set
            )
            and len(set(allowed)) == len(allowed)
            and len(set(recommended)) == len(recommended)
            and len(set(write_set)) == len(write_set)
            and set(recommended).issubset(allowed)
            and not ("no-write" in allowed and write_set)
        )
        if not valid_actions:
            findings.append(Finding("FRESH_ACTION_INVALID", path="fresh.actions"))
        elif capture is not None and (
            capture.get("access") != "available"
            or capture.get("representation")
            in {"empty", "non-text", "error-document", "not-applicable"}
        ):
            if allowed != ["no-write"] or recommended != ["no-write"] or write_set:
                findings.append(Finding("FRESH_ACTION_INVALID", path="fresh.actions"))

    drift = _strict_mapping(
        value.get("drift"),
        frozenset(
            {
                "frozen_manifest_row_hash",
                "observed_manifest_row_hash",
                "status",
            }
        ),
        path="fresh.drift",
        invalid_code="FRESH_DRIFT_INVALID",
        missing_code="FRESH_DRIFT_INVALID",
        unknown_code="FRESH_DRIFT_INVALID",
        findings=findings,
    )
    if drift is not None:
        valid_drift = (
            _is_sha256(drift.get("frozen_manifest_row_hash"))
            and _is_sha256(drift.get("observed_manifest_row_hash"))
            and drift.get("status") in {"same", "drifted"}
            and (
                freeze is None
                or drift.get("frozen_manifest_row_hash")
                == freeze.get("manifest_row_hash")
            )
            and (
                drift.get("status") != "same"
                or drift.get("frozen_manifest_row_hash")
                == drift.get("observed_manifest_row_hash")
            )
        )
        if not valid_drift:
            findings.append(Finding("FRESH_DRIFT_INVALID", path="fresh.drift"))

    index = _strict_mapping(
        value.get("index"),
        frozenset(
            {
                "assessment_index_sha256",
                "source_ids",
                "source_count",
                "terminal_count",
                "assessment_sha256",
                "review_sha256",
                "candidate_sha256",
            }
        ),
        path="fresh.index",
        invalid_code="FRESH_INDEX_INVALID",
        missing_code="FRESH_INDEX_INVALID",
        unknown_code="FRESH_INDEX_INVALID",
        findings=findings,
    )
    if index is not None:
        source_ids = index.get("source_ids")
        valid_index = (
            all(
                _is_sha256(index.get(key))
                for key in (
                    "assessment_index_sha256",
                    "assessment_sha256",
                    "review_sha256",
                    "candidate_sha256",
                )
            )
            and isinstance(source_ids, list)
            and source_ids
            and all(
                isinstance(item, str) and SOURCE_ID_RE.fullmatch(item) is not None
                for item in source_ids
            )
            and len(set(source_ids)) == len(source_ids)
            and source_ids == sorted(source_ids)
            and _is_int(index.get("source_count"))
            and _is_int(index.get("terminal_count"))
            and index.get("source_count") == len(source_ids)
            and index.get("terminal_count") == len(source_ids)
            and (freeze is None or source_ids == [freeze.get("source_id")])
        )
        if not valid_index:
            findings.append(Finding("FRESH_INDEX_INVALID", path="fresh.index"))
        for record in review_records:
            if (
                record.get("assessment_sha256") != index.get("assessment_sha256")
                or assessment_packet is None
                or record.get("packet_sha256") != assessment_packet.get("packet_sha256")
            ):
                findings.append(Finding("FRESH_REVIEW_INVALID", path="fresh.review"))

    if capture is not None and capture.get("state") != "completed":
        findings.append(Finding("FRESH_TERMINALITY_INVALID", path="fresh.capture"))
    if "thin-standalone" in finding_codes and not (
        page_form == "standalone"
        and adequacy is not None
        and adequacy.get("value") == "sufficient"
        and intent is not None
        and intent.get("kind") == "declared"
        and intent.get("fit") == "misses"
    ):
        findings.append(Finding("FRESH_FINDING_INVALID", path="fresh.findings"))
    if "aggregate" in finding_codes and page_form != "aggregate":
        findings.append(Finding("FRESH_FINDING_INVALID", path="fresh.findings"))
    return _normalize(findings)


def _fixture_cases(fixture: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    named_sections = (
        "assessment_cases",
        "summary_cases",
        "routing_cases",
        "negative_audit_cases",
    )
    has_generic = "cases" in fixture
    has_named = any(section in fixture for section in named_sections)
    if has_generic == has_named:
        raise ValueError("fixture must contain either cases or the named case arrays")

    sections = ("cases",) if has_generic else named_sections
    cases: list[Mapping[str, Any]] = []
    for section in sections:
        value = fixture.get(section)
        if not isinstance(value, list):
            raise ValueError(f"fixture.{section} must be an array")
        for case in value:
            if (
                not isinstance(case, Mapping)
                or not isinstance(case.get("id"), str)
                or not case["id"]
                or "expected" not in case
            ):
                raise ValueError(f"invalid case in {section}")
            cases.append(case)
    return cases


_NAMED_CALIBRATION_PROMPTS = {
    "assessment_cases": (
        "Classify the sealed source evidence with the Atlas source-quality rubric. "
        "Return actual with exactly the listed result_fields and canonical assessment enums."
    ),
    "summary_cases": (
        "Evaluate the sealed source-summary evidence. Return actual with exactly the listed "
        "result_fields; when present, use the canonical seven-item checklist order."
    ),
    "routing_cases": (
        "Evaluate the sealed source-local routing evidence. Return actual with exactly the "
        "listed result_fields and no claim not supported by the evidence."
    ),
    "negative_audit_cases": (
        "Classify the sealed source-quality defect. Return actual with exactly the listed "
        "result_fields and canonical failure identifiers."
    ),
}


def _prepared_named_case(section: str, case: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {"id", "evidence", "expected", "metamorphic_group", "irrelevant_context"}
    unknown = sorted(set(case) - allowed)
    if unknown:
        raise ValueError(f"case {case['id']} has unknown fields: {unknown}")
    evidence = case.get("evidence")
    expected = case.get("expected")
    if (
        not isinstance(evidence, str)
        or not evidence
        or not isinstance(expected, Mapping)
    ):
        raise ValueError(f"case {case['id']} has invalid evidence or expected result")
    case_fixture: dict[str, Any] = {
        "evidence": evidence,
        "result_fields": list(expected),
    }
    for key in ("metamorphic_group", "irrelevant_context"):
        if key not in case:
            continue
        value = case[key]
        if not isinstance(value, str) or not value:
            raise ValueError(f"case {case['id']} has invalid {key}")
        case_fixture[key] = value
    return {
        "id": case["id"],
        "prompt": _NAMED_CALIBRATION_PROMPTS[section],
        "fixture": case_fixture,
    }


def prepare_calibration(fixture_text: str, case_ids: Sequence[str]) -> dict[str, Any]:
    """Return fixture-order model packets with expected values removed."""
    fixture = json.loads(fixture_text)
    if not isinstance(fixture, Mapping) or fixture.get("version") != VERSION:
        raise ValueError(f"fixture.version must be {VERSION}")
    cases = _fixture_cases(fixture)
    fixture_ids = [str(case["id"]) for case in cases]
    if len(set(fixture_ids)) != len(fixture_ids):
        raise ValueError("fixture contains duplicate case IDs")
    if (
        not isinstance(case_ids, Sequence)
        or isinstance(case_ids, (str, bytes))
        or not all(isinstance(case_id, str) and case_id for case_id in case_ids)
    ):
        raise ValueError("case_ids must be an array of nonempty strings")
    requested = list(case_ids)
    if len(set(requested)) != len(requested):
        raise ValueError("case_ids contains duplicate IDs")
    missing = sorted(set(fixture_ids) - set(requested))
    unknown = sorted(set(requested) - set(fixture_ids))
    if missing or unknown:
        raise ValueError(f"case_ids invalid: missing={missing}, unknown={unknown}")

    prepared: list[dict[str, Any]] = []
    if "cases" in fixture:
        for case in cases:
            if set(case) != {"id", "prompt", "fixture", "expected"}:
                raise ValueError(f"case {case['id']} is not preparation-compatible")
            prompt = case["prompt"]
            case_fixture = case["fixture"]
            if (
                not isinstance(prompt, str)
                or not prompt
                or not isinstance(case_fixture, Mapping)
            ):
                raise ValueError(f"case {case['id']} has invalid prompt or fixture")
            prepared.append(
                {"id": case["id"], "prompt": prompt, "fixture": dict(case_fixture)}
            )
    else:
        for section in _NAMED_CALIBRATION_PROMPTS:
            for case in fixture[section]:
                prepared.append(_prepared_named_case(section, case))
    return {"version": VERSION, "cases": prepared}


def validate_calibration(fixture_text: str, response_text: str) -> list[Finding]:
    """Exact-compare structured calibration outcomes to the versioned fixture."""
    findings: list[Finding] = []
    try:
        fixture = json.loads(fixture_text)
        response = json.loads(response_text)
    except json.JSONDecodeError as exc:
        return [
            Finding("CALIBRATION_JSON_INVALID", path="calibration", detail=str(exc))
        ]
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
        return _normalize(
            findings + [Finding("CALIBRATION_RESULTS_INVALID", path="response")]
        )
    actual: dict[str, Any] = {}
    for index, result in enumerate(results):
        if (
            not isinstance(result, Mapping)
            or set(result) != {"id", "actual"}
            or not isinstance(result.get("id"), str)
        ):
            findings.append(
                Finding("CALIBRATION_RESULT_INVALID", path=f"response.results[{index}]")
            )
            continue
        case_id = result["id"]
        if case_id in actual:
            findings.append(
                Finding(
                    "CALIBRATION_RESULT_DUPLICATE_ID", path="response", detail=case_id
                )
            )
        actual[case_id] = result["actual"]
    for case_id in sorted(set(expected) - set(actual)):
        findings.append(
            Finding("CALIBRATION_RESULT_MISSING", path="response", detail=case_id)
        )
    for case_id in sorted(set(actual) - set(expected)):
        findings.append(
            Finding("CALIBRATION_RESULT_UNKNOWN", path="response", detail=case_id)
        )
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
    payload = {
        "ok": not findings,
        "findings": [finding.to_dict() for finding in findings],
    }
    sys.stdout.write(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atlas_quality.py",
        description="Validate Atlas source summaries or calibration responses.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in (
        "validate-summary",
        "prepare-calibration",
        "validate-calibration",
    ):
        subparser = subparsers.add_parser(name)
        subparser.add_argument(
            "--input", required=True, help="Versioned JSON input path, or - for stdin"
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _load_input(args.input)
        allowed_by_command = {
            "validate-summary": {
                "version",
                "artifact_text",
                "evidence_bundle",
                "checklist",
            },
            "prepare-calibration": {"version", "fixture_text", "case_ids"},
            "validate-calibration": {
                "version",
                "fixture_text",
                "response_text",
            },
        }
        allowed = allowed_by_command[args.command]
        unknown = set(payload) - allowed
        missing = allowed - set(payload)
        if unknown or missing:
            raise ValueError(
                f"input fields invalid: missing={sorted(missing)}, unknown={sorted(unknown)}"
            )
        if args.command == "validate-summary":
            findings = validate_summary(
                payload["artifact_text"],
                payload["evidence_bundle"],
                payload["checklist"],
            )
            _emit(findings)
            return 0 if not findings else 2
        if args.command == "prepare-calibration":
            prepared = prepare_calibration(payload["fixture_text"], payload["case_ids"])
            sys.stdout.write(
                json.dumps(
                    prepared,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                )
                + "\n"
            )
            return 0
        findings = validate_calibration(
            payload["fixture_text"], payload["response_text"]
        )
        _emit(findings)
        return 0 if not findings else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"atlas-quality: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
