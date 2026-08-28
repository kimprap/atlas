#!/usr/bin/env python3
"""Deterministic Atlas source-summary and calibration validation."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence, TypeGuard


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
    "classification_status",
    "routing_terms",
    "source_routing_sha256",
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
    "classification_status": {"classified", "unclassified"},
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
OBJECT_ARRAY_FRONTMATTER_KEYS = frozenset({"routing_terms"})
ROUTING_TERM_TYPES = {"domain", "subdomain", "tag", "topic"}
ROUTING_TERM_CONFIDENCES = {"high", "medium", "low"}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PUBLICATION_DATE_RE = re.compile(r"^\d{4}-\d{2}(?:-\d{2})?$")
SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")
CONTENT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
ROUTING_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
LEDGER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
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
    for key in OBJECT_ARRAY_FRONTMATTER_KEYS:
        raw = raw_values.get(key)
        if raw is None:
            continue
        try:
            items = json.loads(raw)
        except json.JSONDecodeError:
            items = None
        if not isinstance(items, list) or any(
            not isinstance(item, dict) for item in items
        ):
            findings.append(
                Finding(
                    "FRONTMATTER_OBJECT_ARRAY_TYPE_INVALID",
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
    if frontmatter.get("schema_version") != "2":
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
    source_routing_sha256 = frontmatter.get("source_routing_sha256")
    if source_routing_sha256 is not None and not ROUTING_SHA256_RE.fullmatch(
        source_routing_sha256
    ):
        findings.append(Finding("SOURCE_ROUTING_SHA256_INVALID"))
    routing_terms: list[Any] | None = None
    raw_routing_terms = frontmatter.get("routing_terms")
    if raw_routing_terms is not None:
        try:
            parsed_routing_terms = json.loads(raw_routing_terms)
        except json.JSONDecodeError:
            parsed_routing_terms = None
        if isinstance(parsed_routing_terms, list):
            routing_terms = parsed_routing_terms
            if len(routing_terms) > 24:
                findings.append(Finding("ROUTING_TERMS_LIMIT_EXCEEDED"))
            seen_routing_terms: set[tuple[str, str]] = set()
            for index, term in enumerate(routing_terms):
                if not isinstance(term, dict) or set(term) != {
                    "type",
                    "value",
                    "confidence",
                }:
                    findings.append(
                        Finding("ROUTING_TERM_SHAPE_INVALID", detail=str(index))
                    )
                    continue
                term_type = term.get("type")
                value = term.get("value")
                confidence = term.get("confidence")
                if (
                    term_type not in ROUTING_TERM_TYPES
                    or confidence not in ROUTING_TERM_CONFIDENCES
                    or not isinstance(value, str)
                    or not value.strip()
                ):
                    findings.append(
                        Finding("ROUTING_TERM_VALUE_INVALID", detail=str(index))
                    )
                    continue
                identity = (
                    str(term_type),
                    unicodedata.normalize("NFKC", value).casefold(),
                )
                if identity in seen_routing_terms:
                    findings.append(
                        Finding("ROUTING_TERM_DUPLICATE", detail=str(index))
                    )
                seen_routing_terms.add(identity)
    classification_status = frontmatter.get("classification_status")
    if (
        classification_status == "classified"
        and not frontmatter.get("primary_domain", "").strip()
    ):
        findings.append(Finding("CLASSIFICATION_PRIMARY_DOMAIN_REQUIRED"))
    if classification_status == "unclassified":
        if frontmatter.get("primary_domain", "").strip():
            findings.append(Finding("UNCLASSIFIED_DOMAIN_INVALID"))
        for key in ("subdomains", "secondary_domains", "canonical_tags"):
            try:
                values = json.loads(frontmatter.get(key, "[]"))
            except json.JSONDecodeError:
                continue
            if values:
                findings.append(Finding("UNCLASSIFIED_TERMS_INVALID", detail=key))
        if routing_terms:
            findings.append(
                Finding("UNCLASSIFIED_TERMS_INVALID", detail="routing_terms")
            )
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


def _is_nonempty_text(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and CONTENT_HASH_RE.fullmatch(value) is not None


def _is_revision(value: Any) -> bool:
    return (
        isinstance(value, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None
    )


def _is_http_url(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and re.fullmatch(r"https?://\S+", value) is not None


def _is_ledger_id(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and LEDGER_ID_RE.fullmatch(value) is not None


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


def _binding_detail(allowed: Iterable[tuple[str, ...]], actual: tuple[Any, ...]) -> str:
    expected = json.dumps(
        sorted(allowed), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    observed = json.dumps(
        actual, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return f"expected={expected}; actual={observed}"


def _validate_proposal(
    proposal: Any, evidence_ledger: Any, *, semantic: bool
) -> list[Finding]:
    """Validate a model-owned source proposal and its source-local ledger."""
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
                    and _is_ledger_id(item_value.get("ledger_id"))
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
                    and _is_ledger_id(item_value.get("ledger_id"))
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
                if not _is_nonempty_text(locator) or not _is_ledger_id(ledger_id):
                    findings.append(
                        Finding(
                            "PROPOSAL_EVIDENCE_INVALID",
                            path=f"proposal.claims[{index}].evidence[{evidence_index}]",
                        )
                    )
                elif semantic and (locator, ledger_id) not in evidence_bindings:
                    findings.append(
                        Finding(
                            "PROPOSAL_EVIDENCE_LOCATOR_UNBOUND",
                            path=f"proposal.claims[{index}].evidence[{evidence_index}]",
                            detail=_binding_detail(
                                evidence_bindings, (locator, ledger_id)
                            ),
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
            if not _is_nonempty_text(locator) or not _is_ledger_id(ledger_id):
                findings.append(
                    Finding("PROPOSAL_LINK_INVALID", path=f"proposal.links[{index}]")
                )
            elif semantic and (url, locator, ledger_id) not in link_bindings:
                findings.append(
                    Finding(
                        "PROPOSAL_LINK_LEDGER_UNBOUND",
                        path=f"proposal.links[{index}]",
                        detail=_binding_detail(
                            link_bindings, (url, locator, ledger_id)
                        ),
                    )
                )

    if semantic and _contains_context(
        {
            "metadata": value.get("metadata"),
            "claims": value.get("claims"),
            "links": value.get("links"),
        }
    ):
        findings.append(Finding("PROPOSAL_CONTEXT_LEAK", path="proposal"))
    return _normalize(findings)


def validate_proposal_structure(proposal: Any, evidence_ledger: Any) -> list[Finding]:
    """Validate the unchanged proposal and ledger schemas without semantic bindings."""
    return _validate_proposal(proposal, evidence_ledger, semantic=False)


def validate_proposal(proposal: Any, evidence_ledger: Any) -> list[Finding]:
    """Validate a model-owned source proposal against its source-local ledger."""
    return _validate_proposal(proposal, evidence_ledger, semantic=True)


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
