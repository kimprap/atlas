#!/usr/bin/env python3
"""Deterministic Atlas Markdown registry validation and reduction.

The core API consumes and returns text. Only ``audit_instance`` touches a local
filesystem; connector adapters remain responsible for logical vault I/O and
optimistic writes.
"""

from __future__ import annotations

from datetime import date
import argparse
import hashlib
import unicodedata
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from atlas_url import normalize_canonical_url, source_id_for

VERSION = 1

MANIFEST_PATH = "summaries/sources/MANIFEST.md"
TOPICS_PATH = "summaries/registry/TOPICS.md"
RELATIONS_PATH = "summaries/registry/RELATIONS.md"

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
HEADERS = {
    "manifest": MANIFEST_HEADER,
    "topics": TOPICS_HEADER,
    "relations": RELATIONS_HEADER,
}
PATHS = {
    "manifest": MANIFEST_PATH,
    "topics": TOPICS_PATH,
    "relations": RELATIONS_PATH,
}

SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")
CONTENT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EDGE_ID_RE = re.compile(r"^edge--[0-9a-f]{12}--[a-z0-9][a-z0-9-]*--[0-9a-f]{8}$")
REASON_RE = re.compile(
    r"^Verifier: (?P<locator>\S(?:.*\S)?) — (?P<claim>\S(?:.*\S)?) "
    r"\[relation=(?P<relation>direct|supporting|contradicting); "
    r"impact=(?P<impact>high|medium|low)\]$"
)

ROUTE_STATUSES = {"unrouted", "routed", "no-topic-match", "routing-blocked"}
SOURCE_STATUSES = {"active", "archived"}
FRESHNESS_STATES = {"current", "dirty", "refreshing", "blocked", "archived"}
REFRESH_MODELS = {"same-as-topic-creation", "smol-ok", "manual-only"}
RELATIONS = {"direct", "supporting", "contradicting"}
LEVELS = {"high", "medium", "low"}
RELATION_STATUSES = {"pending", "applied", "rejected", "superseded"}


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    path: str
    line: int | None = None
    row: str | None = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "path": self.path}
        if self.line is not None:
            result["line"] = self.line
        if self.row is not None:
            result["row"] = self.row
        if self.detail:
            result["detail"] = self.detail
        return result


@dataclass
class ParsedTable:
    name: str
    path: str
    text: str
    lines: list[str]
    newline: str
    final_newline: bool
    header_index: int | None = None
    separator_index: int | None = None
    data_end: int | None = None
    rows: list[list[str]] = field(default_factory=list)
    row_lines: list[int] = field(default_factory=list)
    orphan_rows: list[list[str]] = field(default_factory=list)
    orphan_indices: list[int] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def _body(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith(("\n", "\r")):
        return line[:-1]
    return line


def _detect_newline(text: str) -> str:
    crlf = text.find("\r\n")
    lf = text.find("\n")
    if crlf != -1 and crlf == lf - 1:
        return "\r\n"
    return "\n"


def split_markdown_row(line: str) -> list[str] | None:
    value = _body(line).strip()
    if not value.startswith("|") or not value.endswith("|"):
        return None
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in value[1:-1]:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def _is_separator(cells: Sequence[str], expected: int) -> bool:
    return len(cells) == expected and all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in cells
    )


def _parse_table(name: str, text: str) -> ParsedTable:
    header = HEADERS[name]
    path = PATHS[name]
    lines = text.splitlines(keepends=True)
    parsed = ParsedTable(
        name=name,
        path=path,
        text=text,
        lines=lines,
        newline=_detect_newline(text),
        final_newline=text.endswith(("\n", "\r")),
    )
    matching_headers = [
        index
        for index, line in enumerate(lines)
        if tuple(split_markdown_row(line) or ()) == header
    ]
    if not matching_headers:
        parsed.findings.append(Finding(f"{name.upper()}_TABLE_HEADER_MISSING", path))
        return parsed
    parsed.header_index = matching_headers[0]
    for index in matching_headers[1:]:
        parsed.findings.append(
            Finding(f"{name.upper()}_SECOND_TABLE_HEADER", path, index + 1)
        )
    separator_index = parsed.header_index + 1
    parsed.separator_index = separator_index
    if separator_index >= len(lines):
        parsed.findings.append(
            Finding(
                f"{name.upper()}_TABLE_SEPARATOR_MISSING", path, parsed.header_index + 1
            )
        )
        return parsed
    separator = split_markdown_row(lines[separator_index])
    if separator is None or not _is_separator(separator, len(header)):
        parsed.findings.append(
            Finding(
                f"{name.upper()}_TABLE_SEPARATOR_INVALID", path, separator_index + 1
            )
        )
        return parsed

    index = separator_index + 1
    while index < len(lines):
        cells = split_markdown_row(lines[index])
        if cells is None:
            break
        if len(cells) != len(header) or _is_separator(cells, len(header)):
            parsed.findings.append(
                Finding(
                    f"{name.upper()}_ROW_WRONG_CELL_COUNT",
                    path,
                    index + 1,
                    detail=f"expected {len(header)} cells, found {len(cells)}",
                )
            )
            break
        parsed.rows.append(cells)
        parsed.row_lines.append(index + 1)
        index += 1
    parsed.data_end = index

    for orphan_index in range(index, len(lines)):
        cells = split_markdown_row(lines[orphan_index])
        if (
            cells is not None
            and len(cells) == len(header)
            and not _is_separator(cells, len(header))
        ):
            parsed.orphan_rows.append(cells)
            parsed.orphan_indices.append(orphan_index)
            code = (
                "RELATION_ROW_OUTSIDE_TABLE"
                if name == "relations"
                else f"{name.upper()}_ROW_OUTSIDE_TABLE"
            )
            parsed.findings.append(Finding(code, path, orphan_index + 1, row=cells[0]))
    return parsed


def _row_dict(header: Sequence[str], row: Sequence[str]) -> dict[str, str]:
    return dict(zip(header, row, strict=True))


def _find_duplicates(
    values: Iterable[tuple[str, int]], code: str, path: str
) -> list[Finding]:
    seen: dict[str, int] = {}
    findings: list[Finding] = []
    for value, line in values:
        if value in seen:
            findings.append(
                Finding(
                    code,
                    path,
                    line,
                    row=value,
                    detail=f"first appears on line {seen[value]}",
                )
            )
        else:
            seen[value] = line
    return findings


def _edge_id(source_id: str, topic_id: str, content_hash: str) -> str:
    topic_key = re.sub(r"[/ .]+", "-", topic_id)
    return f"edge--{source_id}--{topic_key}--{content_hash[:8]}"


def _validate_manifest(
    table: ParsedTable,
) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    by_id: dict[str, dict[str, str]] = {}
    records = [_row_dict(MANIFEST_HEADER, row) for row in table.rows]
    findings.extend(
        _find_duplicates(
            (
                (row["Source ID"], line)
                for row, line in zip(records, table.row_lines, strict=True)
            ),
            "MANIFEST_DUPLICATE_SOURCE_ID",
            table.path,
        )
    )
    findings.extend(
        _find_duplicates(
            (
                (row["Source seq"], line)
                for row, line in zip(records, table.row_lines, strict=True)
            ),
            "MANIFEST_DUPLICATE_SOURCE_SEQ",
            table.path,
        )
    )
    findings.extend(
        _find_duplicates(
            (
                (row["Canonical URL"], line)
                for row, line in zip(records, table.row_lines, strict=True)
            ),
            "MANIFEST_DUPLICATE_CANONICAL_URL",
            table.path,
        )
    )
    for row, line in zip(records, table.row_lines, strict=True):
        source_id = row["Source ID"]
        if not SOURCE_ID_RE.fullmatch(source_id):
            findings.append(
                Finding("MANIFEST_SOURCE_ID_INVALID", table.path, line, source_id)
            )
        canonical_url = row["Canonical URL"]
        try:
            normalized_url = normalize_canonical_url(canonical_url)
        except ValueError as exc:
            findings.append(
                Finding(
                    "MANIFEST_CANONICAL_URL_INVALID",
                    table.path,
                    line,
                    source_id,
                    str(exc),
                )
            )
        else:
            if normalized_url != canonical_url:
                findings.append(
                    Finding(
                        "MANIFEST_CANONICAL_URL_NOT_NORMALIZED",
                        table.path,
                        line,
                        source_id,
                        f"expected {normalized_url}",
                    )
                )
            expected_source_id = source_id_for(normalized_url)
            if source_id != expected_source_id:
                findings.append(
                    Finding(
                        "MANIFEST_SOURCE_ID_URL_MISMATCH",
                        table.path,
                        line,
                        source_id,
                        f"expected {expected_source_id}",
                    )
                )
        try:
            sequence = int(row["Source seq"])
            if sequence <= 0:
                raise ValueError
        except ValueError:
            findings.append(
                Finding("MANIFEST_SOURCE_SEQ_INVALID", table.path, line, source_id)
            )
        if not CONTENT_HASH_RE.fullmatch(row["Content hash"]):
            findings.append(
                Finding("MANIFEST_CONTENT_HASH_INVALID", table.path, line, source_id)
            )
        if row["Route status"] not in ROUTE_STATUSES:
            findings.append(
                Finding("MANIFEST_ROUTE_STATUS_INVALID", table.path, line, source_id)
            )
        if row["Status"] not in SOURCE_STATUSES:
            findings.append(
                Finding("MANIFEST_STATUS_INVALID", table.path, line, source_id)
            )
        for field_name in (
            "First seen",
            "Last checked",
            "Last summarized",
            "Refresh after",
        ):
            if row[field_name] and not DATE_RE.fullmatch(row[field_name]):
                findings.append(
                    Finding(
                        "MANIFEST_DATE_INVALID", table.path, line, source_id, field_name
                    )
                )
        by_id[source_id] = row
    return findings, by_id


def validated_manifest_rows(
    manifest_text: str,
) -> tuple[list[dict[str, str]], list[Finding]]:
    """Return all valid canonical MANIFEST rows in table order."""
    table = _parse_table("manifest", manifest_text)
    findings = _normalize_findings(table.findings)
    if findings:
        return [], findings
    manifest_findings, by_id = _validate_manifest(table)
    findings = _normalize_findings(manifest_findings)
    if findings:
        return [], findings
    return list(by_id.values()), []


def lookup_manifest_row(
    manifest_text: str, canonical_url: str
) -> tuple[dict[str, str] | None, list[Finding]]:
    """Return the canonical MANIFEST row for one normalized URL."""
    rows, findings = validated_manifest_rows(manifest_text)
    if findings:
        return None, findings
    row = next(
        (item for item in rows if item["Source ID"] == source_id_for(canonical_url)),
        None,
    )
    if row is None or row["Canonical URL"] != canonical_url:
        return None, []
    return row, []


def _registry_decode_scalar(raw: str) -> str:
    """Decode the small Markdown scalar grammar used by registry cells."""
    decoded: list[str] = []
    index = 0
    while index < len(raw):
        char = raw[index]
        if char != "\\":
            decoded.append(char)
            index += 1
            continue
        if index + 1 >= len(raw):
            decoded.append("\\")
            index += 1
            continue
        next_char = raw[index + 1]
        if next_char == "\\":
            decoded.append("\\")
            index += 2
            continue
        if next_char == "u" and raw.startswith("\\u{", index):
            close = raw.find("}", index + 3)
            if close != -1:
                digits = raw[index + 3 : close]
                try:
                    codepoint = int(digits, 16)
                except ValueError:
                    codepoint = -1
                if (
                    1 <= len(digits) <= 6
                    and 0 <= codepoint <= 0x10FFFF
                    and not 0xD800 <= codepoint <= 0xDFFF
                ):
                    decoded.append(chr(codepoint))
                    index = close + 1
                    continue
        if not next_char.isalnum():
            decoded.append(next_char)
            index += 2
            continue
        decoded.append("\\")
        index += 1
    return "".join(decoded)
def _registry_encode_scalar(
    value: str,
    *,
    reserved: str = "|",
    protect_literals: bool = False,
) -> str:
    result: list[str] = []
    protect = protect_literals and value == "none"
    for index, char in enumerate(value):
        if protect and index == 0:
            result.append(f"\\u{{{ord(char):04x}}}")
        elif char == "\\":
            result.append("\\\\")
        elif (
            char in reserved
            or char in "\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029"
            or unicodedata.category(char) in {"Cc", "Cf", "Zl", "Zp"}
        ):
            result.append(f"\\u{{{ord(char):04x}}}" if char not in reserved else "\\" + char)
        else:
            result.append(char)
    return "".join(result)


def _registry_markdown_decode(raw: str) -> str:
    """Decode the enclosing Markdown-table layer without consuming list escapes."""
    decoded: list[str] = []
    index = 0
    while index < len(raw):
        char = raw[index]
        if char == "\\" and index + 1 < len(raw) and raw[index + 1] in {"\\", "|"}:
            decoded.append(raw[index + 1])
            index += 2
            continue
        decoded.append(char)
        index += 1
    return "".join(decoded)


def _registry_markdown_encode(raw: str) -> str:
    """Encode the enclosing Markdown-table layer around a registry cell."""
    encoded: list[str] = []
    for char in raw:
        if char == "\\":
            encoded.append("\\\\")
        elif char == "|":
            encoded.append("\\|")
        else:
            encoded.append(char)
    return "".join(encoded)




def _registry_list(raw: str) -> tuple[list[str] | None, bool]:
    """Return decoded list and whether its bytes are canonical."""
    if raw == "":
        return [], True
    source = _registry_markdown_decode(raw)
    pieces: list[str] = []
    current: list[str] = []
    escaped = False
    for char in source:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            current.append(char)
            escaped = True
        elif char == ";":
            pieces.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    pieces.append("".join(current).strip())
    values = [_registry_decode_scalar(item) for item in pieces]
    canonical_inner = "; ".join(
        _registry_encode_scalar(item, reserved=";", protect_literals=True)
        for item in values
    )
    canonical = _registry_markdown_encode(canonical_inner)
    scalar_valid = all(
        all(unicodedata.category(char) != "Cs" for char in value)
        for value in values
    )
    return values, canonical == raw and scalar_valid


def _validate_topics_shape(
    table: ParsedTable,
) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    records = [_row_dict(TOPICS_HEADER, row) for row in table.rows]
    findings.extend(
        _find_duplicates(
            (
                (row["Topic ID"], line)
                for row, line in zip(records, table.row_lines, strict=True)
            ),
            "TOPIC_DUPLICATE_ID",
            table.path,
        )
    )
    by_id: dict[str, dict[str, str]] = {}
    for row, line in zip(records, table.row_lines, strict=True):
        topic_id = row["Topic ID"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic_id):
            findings.append(Finding("TOPIC_ID_INVALID", table.path, line, topic_id))
        domain, subdomain = row["Domain"], row["Subdomain"]
        for field_name, value in (("Domain", domain), ("Subdomain", subdomain)):
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", value):
                findings.append(
                    Finding("TOPIC_SCOPE_INVALID", table.path, line, topic_id, field_name)
                )
        expected_path = (
            f"summaries/research/{domain}/{subdomain}/topics/{topic_id}/INDEX.md"
        )
        if (
            not row["Topic path"]
            or row["Topic path"] != expected_path
            or "\\" in row["Topic path"]
            or "?" in row["Topic path"]
            or "#" in row["Topic path"]
        ):
            findings.append(
                Finding("TOPIC_PATH_INVALID", table.path, line, topic_id)
            )
        title = _registry_decode_scalar(row["Canonical title"])
        if not title.strip():
            findings.append(Finding("TOPIC_TITLE_INVALID", table.path, line, topic_id))
        elif (
            _registry_encode_scalar(title) != row["Canonical title"]
            or any(unicodedata.category(char) in {"Cs"} for char in title)
        ):
            findings.append(
                Finding("TOPIC_TITLE_NONCANONICAL", table.path, line, topic_id)
            )
        for field_name in ("Aliases", "Canonical tags", "Include terms", "Exclude terms"):
            values, canonical = _registry_list(row[field_name])
            if (
                values is None
                or not canonical
                or len(set(values)) != len(values)
                or values != sorted(values, key=lambda item: item.encode("utf-8"))
            ):
                findings.append(
                    Finding(
                        "TOPIC_LIST_INVALID",
                        table.path,
                        line,
                        topic_id,
                        field_name,
                    )
                )
            elif any(not value.strip() for value in values):
                findings.append(
                    Finding(
                        "TOPIC_LIST_INVALID",
                        table.path,
                        line,
                        topic_id,
                        field_name,
                    )
                )
        if row["Freshness state"] not in FRESHNESS_STATES:
            findings.append(
                Finding("TOPIC_FRESHNESS_INVALID", table.path, line, topic_id)
            )
        if row["Refresh model"] not in REFRESH_MODELS:
            findings.append(
                Finding("TOPIC_REFRESH_MODEL_INVALID", table.path, line, topic_id)
            )
        for field_name in ("Dirty count", "Source watermark"):
            try:
                if int(row[field_name]) < 0:
                    raise ValueError
            except ValueError:
                findings.append(
                    Finding(
                        "TOPIC_NUMBER_INVALID",
                        table.path,
                        line,
                        topic_id,
                        field_name,
                    )
                )
        if row["Newest pending source seq"]:
            try:
                if int(row["Newest pending source seq"]) <= 0:
                    raise ValueError
            except ValueError:
                findings.append(
                    Finding(
                        "TOPIC_NUMBER_INVALID",
                        table.path,
                        line,
                        topic_id,
                        "Newest pending source seq",
                    )
                )
        if row["Last synthesized"]:
            if not DATE_RE.fullmatch(row["Last synthesized"]):
                findings.append(
                    Finding("TOPIC_DATE_INVALID", table.path, line, topic_id)
                )
            else:
                try:
                    date.fromisoformat(row["Last synthesized"])
                except ValueError:
                    findings.append(
                        Finding("TOPIC_DATE_INVALID", table.path, line, topic_id)
                    )
        by_id[topic_id] = row
    return findings, by_id


def _validate_relations(
    table: ParsedTable,
    manifest: Mapping[str, dict[str, str]],
    topics: Mapping[str, dict[str, str]],
) -> tuple[list[Finding], list[dict[str, str]]]:
    findings: list[Finding] = []
    records = [_row_dict(RELATIONS_HEADER, row) for row in table.rows]
    findings.extend(
        _find_duplicates(
            (
                (row["Edge ID"], line)
                for row, line in zip(records, table.row_lines, strict=True)
            ),
            "RELATION_DUPLICATE_EDGE_ID",
            table.path,
        )
    )
    for row, line in zip(records, table.row_lines, strict=True):
        edge_id = row["Edge ID"]
        source_id = row["Source ID"]
        manifest_row = manifest.get(source_id)
        if not EDGE_ID_RE.fullmatch(edge_id):
            findings.append(
                Finding("RELATION_EDGE_ID_INVALID", table.path, line, edge_id)
            )
        if not CONTENT_HASH_RE.fullmatch(row["Source content hash"]):
            findings.append(
                Finding("RELATION_CONTENT_HASH_INVALID", table.path, line, edge_id)
            )
        elif edge_id != _edge_id(
            source_id, row["Topic ID"], row["Source content hash"]
        ):
            findings.append(
                Finding("RELATION_EDGE_ID_MISMATCH", table.path, line, edge_id)
            )
        if row["Relation"] not in RELATIONS:
            findings.append(Finding("RELATION_KIND_INVALID", table.path, line, edge_id))
        if row["Impact"] not in LEVELS:
            findings.append(
                Finding("RELATION_IMPACT_INVALID", table.path, line, edge_id)
            )
        if row["Confidence"] not in LEVELS:
            findings.append(
                Finding("RELATION_CONFIDENCE_INVALID", table.path, line, edge_id)
            )
        if row["Status"] not in RELATION_STATUSES:
            findings.append(
                Finding("RELATION_STATUS_INVALID", table.path, line, edge_id)
            )
        if not DATE_RE.fullmatch(row["Created"]):
            findings.append(Finding("RELATION_DATE_INVALID", table.path, line, edge_id))
        if row["Status"] == "applied" and not row["Applied in pass"]:
            findings.append(
                Finding("RELATION_APPLIED_PASS_MISSING", table.path, line, edge_id)
            )
        if row["Status"] != "applied" and row["Applied in pass"]:
            findings.append(
                Finding("RELATION_APPLIED_PASS_FORBIDDEN", table.path, line, edge_id)
            )
        if manifest_row is None:
            findings.append(
                Finding("RELATION_SOURCE_UNKNOWN", table.path, line, edge_id)
            )
        else:
            if row["Source seq"] != manifest_row["Source seq"]:
                findings.append(
                    Finding("RELATION_SOURCE_SEQ_MISMATCH", table.path, line, edge_id)
                )
            if row["Source artifact"] != manifest_row["Artifact"]:
                findings.append(
                    Finding("RELATION_ARTIFACT_MISMATCH", table.path, line, edge_id)
                )
            if (
                row["Status"] == "pending"
                and row["Source content hash"] != manifest_row["Content hash"]
            ):
                findings.append(
                    Finding("RELATION_PENDING_HASH_STALE", table.path, line, edge_id)
                )
        if row["Topic ID"] not in topics:
            findings.append(
                Finding("RELATION_TOPIC_UNKNOWN", table.path, line, edge_id)
            )
    return findings, records


def _pending_for_topic(
    relations: Sequence[dict[str, str]], topic_id: str
) -> list[dict[str, str]]:
    rows = [
        row
        for row in relations
        if row["Topic ID"] == topic_id and row["Status"] == "pending"
    ]
    return sorted(rows, key=lambda row: (int(row["Source seq"]), row["Edge ID"]))


def _applied_for_topic(
    relations: Sequence[dict[str, str]], topic_id: str
) -> list[dict[str, str]]:
    return [
        row
        for row in relations
        if row["Topic ID"] == topic_id and row["Status"] == "applied"
    ]


def _validate_topic_caches(
    table: ParsedTable,
    topics: Mapping[str, dict[str, str]],
    relations: Sequence[dict[str, str]],
) -> list[Finding]:
    findings: list[Finding] = []
    line_by_id = {
        row[0]: line for row, line in zip(table.rows, table.row_lines, strict=True)
    }
    for topic_id, row in topics.items():
        line = line_by_id[topic_id]
        pending = _pending_for_topic(relations, topic_id)
        applied = _applied_for_topic(relations, topic_id)
        expected_ids = "; ".join(item["Edge ID"] for item in pending)
        expected_dirty = str(len(pending))
        expected_newest = str(
            max((int(item["Source seq"]) for item in pending), default="")
        )
        expected_watermark = str(
            max((int(item["Source seq"]) for item in applied), default=0)
        )
        expectations = {
            "Dirty count": expected_dirty,
            "Pending edge IDs": expected_ids,
            "Newest pending source seq": expected_newest,
            "Source watermark": expected_watermark,
        }
        for field_name, expected in expectations.items():
            if row[field_name] != expected:
                findings.append(
                    Finding(
                        "TOPIC_CACHE_MISMATCH",
                        table.path,
                        line,
                        topic_id,
                        f"{field_name}: expected {expected!r}, found {row[field_name]!r}",
                    )
                )
        state = row["Freshness state"]
        if pending and state not in {"dirty", "refreshing", "blocked"}:
            findings.append(
                Finding(
                    "TOPIC_FRESHNESS_MISMATCH",
                    table.path,
                    line,
                    topic_id,
                    "pending edges require dirty, refreshing, or blocked",
                )
            )
        if not pending and state not in {"current", "archived"}:
            findings.append(
                Finding(
                    "TOPIC_FRESHNESS_MISMATCH",
                    table.path,
                    line,
                    topic_id,
                    "no pending edges require current or archived",
                )
            )
    return findings


def _normalize_findings(findings: Iterable[Finding]) -> list[Finding]:
    unique = {finding for finding in findings}
    return sorted(
        unique,
        key=lambda item: (
            item.path,
            item.line if item.line is not None else -1,
            item.code,
            item.row or "",
            item.detail,
        ),
    )


def _parse_documents(documents: Mapping[str, str]) -> dict[str, ParsedTable]:
    missing = set(HEADERS) - set(documents)
    extra = set(documents) - set(HEADERS)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {sorted(missing)}")
        if extra:
            details.append(f"unknown {sorted(extra)}")
        raise ValueError("document keys invalid: " + ", ".join(details))
    return {name: _parse_table(name, documents[name]) for name in HEADERS}


def validate_documents(
    manifest_text: str, topics_text: str, relations_text: str
) -> list[Finding]:
    """Validate the complete canonical Atlas registry state."""
    documents = {
        "manifest": manifest_text,
        "topics": topics_text,
        "relations": relations_text,
    }
    parsed = _parse_documents(documents)
    structural = _normalize_findings(
        finding for table in parsed.values() for finding in table.findings
    )
    if structural:
        return structural

    manifest_findings, manifest = _validate_manifest(parsed["manifest"])
    topic_findings, topics = _validate_topics_shape(parsed["topics"])
    relation_findings, relations = _validate_relations(
        parsed["relations"], manifest, topics
    )
    semantic = manifest_findings + topic_findings + relation_findings
    if not semantic:
        semantic.extend(_validate_topic_caches(parsed["topics"], topics, relations))
    return _normalize_findings(semantic)


def _documents_text(documents: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in HEADERS:
        value = documents.get(name)
        if isinstance(value, str):
            result[name] = value
        elif isinstance(value, Mapping) and isinstance(value.get("text"), str):
            result[name] = value["text"]
        else:
            raise ValueError(f"documents.{name} must be text or an object with text")
    if set(documents) != set(HEADERS):
        extra = sorted(set(documents) - set(HEADERS))
        if extra:
            raise ValueError(f"unknown document keys: {extra}")
    return result


def _hashes(documents: Mapping[str, str]) -> dict[str, str]:
    return {
        name: hashlib.sha256(text.encode("utf-8")).hexdigest()
        for name, text in sorted(documents.items())
    }


def _render_row(cells: Sequence[str], newline: str) -> str:
    return "| " + " | ".join(cells) + " |" + newline


def _replace_rows(table: ParsedTable, rows: Sequence[Sequence[str]]) -> str:
    if table.separator_index is None or table.data_end is None:
        raise ValueError(f"cannot render invalid {table.name} table")
    rendered = [_render_row(row, table.newline) for row in rows]
    prefix = list(table.lines[: table.separator_index + 1])
    if rendered and prefix and not prefix[-1].endswith(("\n", "\r")):
        prefix[-1] += table.newline
    lines = prefix + rendered + table.lines[table.data_end :]
    text = "".join(lines)
    if not table.final_newline and text.endswith(table.newline):
        text = text[: -len(table.newline)]
    return text


def _rehome_relation_orphans(table: ParsedTable) -> str:
    if table.separator_index is None or table.data_end is None:
        raise ValueError("relation table is not repairable")
    existing = {row[0] for row in table.rows}
    for row in table.orphan_rows:
        if row[0] in existing:
            raise ValueError(f"conflicting orphan Edge ID: {row[0]}")
        existing.add(row[0])
    rows = table.rows + table.orphan_rows
    orphan_set = set(table.orphan_indices)
    suffix = [
        line
        for index, line in enumerate(
            table.lines[table.data_end :], start=table.data_end
        )
        if index not in orphan_set
    ]
    rendered = [_render_row(row, table.newline) for row in rows]
    prefix = list(table.lines[: table.separator_index + 1])
    if rendered and prefix and not prefix[-1].endswith(("\n", "\r")):
        prefix[-1] += table.newline
    text = "".join(prefix + rendered + suffix)
    if not table.final_newline and text.endswith(table.newline):
        text = text[: -len(table.newline)]
    return text


def _mutable_rows(table: ParsedTable, header: Sequence[str]) -> list[dict[str, str]]:
    return [_row_dict(header, row) for row in table.rows]


def _rows_from_dicts(
    rows: Sequence[Mapping[str, str]], header: Sequence[str]
) -> list[list[str]]:
    return [[row[field] for field in header] for row in rows]


def _require_event(event: Mapping[str, Any], required: set[str]) -> list[Finding]:
    event_type = str(event.get("type", ""))
    actual = set(event)
    findings: list[Finding] = []
    for name in sorted(required - actual):
        findings.append(
            Finding("EVENT_FIELD_MISSING", "event", row=event_type, detail=name)
        )
    for name in sorted(actual - required):
        findings.append(
            Finding("EVENT_FIELD_UNKNOWN", "event", row=event_type, detail=name)
        )
    return findings


def _validate_reason(
    reason: Any, relation: str, impact: str, row: str
) -> list[Finding]:
    if not isinstance(reason, str):
        return [
            Finding(
                "RELATION_REASON_INVALID",
                "event",
                row=row,
                detail="reason must be text",
            )
        ]
    match = REASON_RE.fullmatch(reason)
    if match is None:
        return [
            Finding("RELATION_REASON_INVALID", "event", row=row, detail="reason shape")
        ]
    if match.group("relation") != relation or match.group("impact") != impact:
        return [Finding("RELATION_REASON_MISMATCH", "event", row=row)]
    return []


def _event_error(code: str, detail: str, row: str | None = None) -> list[Finding]:
    return [Finding(code, "event", row=row, detail=detail)]


def _parse_event_date(value: Any, field_name: str) -> tuple[date | None, list[Finding]]:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return None, _event_error("EVENT_DATE_INVALID", f"{field_name}={value}")
    try:
        return date.fromisoformat(value), []
    except ValueError:
        return None, _event_error("EVENT_DATE_INVALID", f"{field_name}={value}")


def _validate_source_artifact_path(
    value: Any,
    source_id: str,
    first_seen: str,
    *,
    is_new: bool,
    existing_path: str | None = None,
) -> list[Finding]:
    if not isinstance(value, str) or not value:
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", str(value))
    if "\\" in value or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", value)
    path = PurePosixPath(value)
    raw_parts = value.split("/")
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", value)
    if any(part.lower() == "tmp" for part in raw_parts):
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", value)
    prefix = ["summaries", "sources", "artifacts"]
    if raw_parts[: len(prefix)] != prefix:
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", value)
    if existing_path is not None and value != existing_path:
        return _event_error("EVENT_ARTIFACT_PATH_MISMATCH", value)
    if not is_new:
        return []
    remaining = raw_parts[len(prefix) :]
    if len(remaining) != 3:
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", value)
    year, month, filename = remaining
    if year != first_seen[:4] or month != first_seen[:7]:
        return _event_error("EVENT_ARTIFACT_PATH_DATE_MISMATCH", value)
    expected = re.compile(
        rf"^{re.escape(first_seen)}--{re.escape(source_id)}--[A-Za-z0-9][A-Za-z0-9._-]*\.md$"
    )
    if expected.fullmatch(filename) is None:
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", value)
    return []


def _topic_row(
    topics: Sequence[dict[str, str]], topic_id: str
) -> dict[str, str] | None:
    return next((row for row in topics if row["Topic ID"] == topic_id), None)


def _recompute_topics(
    topics: list[dict[str, str]],
    relations: Sequence[dict[str, str]],
    *,
    states: Mapping[str, str] | None = None,
    synthesized: Mapping[str, str] | None = None,
) -> None:
    states = states or {}
    synthesized = synthesized or {}
    for topic in topics:
        topic_id = topic["Topic ID"]
        pending = _pending_for_topic(relations, topic_id)
        applied = _applied_for_topic(relations, topic_id)
        topic["Dirty count"] = str(len(pending))
        topic["Pending edge IDs"] = "; ".join(row["Edge ID"] for row in pending)
        topic["Newest pending source seq"] = (
            str(max(int(row["Source seq"]) for row in pending)) if pending else ""
        )
        topic["Source watermark"] = str(
            max((int(row["Source seq"]) for row in applied), default=0)
        )
        if topic_id in states:
            topic["Freshness state"] = states[topic_id]
        elif topic["Freshness state"] != "archived":
            topic["Freshness state"] = "dirty" if pending else "current"
        if topic_id in synthesized:
            topic["Last synthesized"] = synthesized[topic_id]


def _derived(topics: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    return {
        row["Topic ID"]: {
            "freshness_state": row["Freshness state"],
            "dirty_count": int(row["Dirty count"]),
            "pending_edge_ids": [
                value for value in row["Pending edge IDs"].split("; ") if value
            ],
            "newest_pending_source_seq": (
                int(row["Newest pending source seq"])
                if row["Newest pending source seq"]
                else None
            ),
            "source_watermark": int(row["Source watermark"]),
        }
        for row in sorted(topics, key=lambda item: item["Topic ID"])
    }


@dataclass
class ReductionResult:
    ok: bool
    preconditions: dict[str, str]
    documents: dict[str, str] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    derived: dict[str, Any] = field(default_factory=dict)
    applied_edge_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "preconditions": dict(sorted(self.preconditions.items())),
            "documents": dict(sorted(self.documents.items())),
            "findings": [finding.to_dict() for finding in self.findings],
            "derived": self.derived,
            "applied_edge_ids": self.applied_edge_ids,
        }


@dataclass(frozen=True)
class RecoveryPlan:
    action: str
    classifications: dict[str, str]
    restore_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "classifications": dict(self.classifications),
            "restore_paths": list(self.restore_paths),
        }


def plan_transaction_recovery(
    intent: Mapping[str, Any],
    prepared: Mapping[str, Any] | None,
    current_hashes: Mapping[str, str | None],
    *,
    abort: bool = False,
) -> RecoveryPlan:
    """Classify a transaction from reread hashes without performing storage I/O."""
    if not isinstance(intent, Mapping):
        raise ValueError("intent must be an object")
    targets = intent.get("targets")
    if not isinstance(targets, list):
        raise ValueError("intent.targets must be an array")
    if prepared is not None and not isinstance(prepared, Mapping):
        raise ValueError("prepared must be an object or null")
    normalized: list[tuple[str, str | None, str]] = []
    seen: set[str] = set()
    for index, target in enumerate(targets):
        if not isinstance(target, Mapping) or set(target) != {
            "path",
            "input_sha256",
            "output_sha256",
        }:
            raise ValueError(f"intent.targets[{index}] has invalid fields")
        path = target.get("path")
        input_hash = target.get("input_sha256")
        output_hash = target.get("output_sha256")
        if not isinstance(path, str) or not path or path in seen:
            raise ValueError(f"intent.targets[{index}].path is invalid")
        if input_hash is not None and (
            not isinstance(input_hash, str)
            or CONTENT_HASH_RE.fullmatch(input_hash) is None
        ):
            raise ValueError(f"intent.targets[{index}].input_sha256 is invalid")
        if (
            not isinstance(output_hash, str)
            or CONTENT_HASH_RE.fullmatch(output_hash) is None
        ):
            raise ValueError(f"intent.targets[{index}].output_sha256 is invalid")
        if input_hash == output_hash:
            raise ValueError(f"intent.targets[{index}] is not a changed target")
        seen.add(path)
        normalized.append((path, input_hash, output_hash))
    if set(current_hashes) != seen:
        raise ValueError("current_hashes must contain exactly the target paths")

    classifications: dict[str, str] = {}
    for path, input_hash, output_hash in normalized:
        current = current_hashes[path]
        if current == output_hash:
            classifications[path] = "output"
        elif current == input_hash:
            classifications[path] = "input"
        else:
            classifications[path] = "other"

    if prepared is None:
        if any(value != "input" for value in classifications.values()):
            return RecoveryPlan("manual-conflict", classifications)
        return RecoveryPlan("aborted" if abort else "prepare", classifications)
    if not normalized:
        return RecoveryPlan("no-op", classifications)
    if "other" in classifications.values():
        return RecoveryPlan("manual-conflict", classifications)
    if all(value == "output" for value in classifications.values()):
        return RecoveryPlan("applied", classifications)
    if all(value == "input" for value in classifications.values()):
        return RecoveryPlan("rolled-back", classifications)
    restore = [
        path for path, _, _ in reversed(normalized) if classifications[path] == "output"
    ]
    return RecoveryPlan("rollback", classifications, restore)


def _failed(
    documents: Mapping[str, str], findings: Iterable[Finding]
) -> ReductionResult:
    return ReductionResult(
        False, _hashes(documents), findings=_normalize_findings(findings)
    )


def reduce_event(
    documents: Mapping[str, Any], event: Mapping[str, Any]
) -> ReductionResult:
    """Validate and reduce one explicit event without performing storage I/O."""
    try:
        texts = _documents_text(documents)
    except ValueError as exc:
        return ReductionResult(
            False, {}, findings=_event_error("DOCUMENT_BUNDLE_INVALID", str(exc))
        )
    if not isinstance(event, Mapping):
        return _failed(texts, _event_error("EVENT_INVALID", "event must be an object"))
    event_type = event.get("type")
    if not isinstance(event_type, str):
        return _failed(texts, _event_error("EVENT_TYPE_INVALID", "type must be text"))

    parsed = _parse_documents(texts)
    input_findings = validate_documents(
        texts["manifest"], texts["topics"], texts["relations"]
    )

    if event_type == "repair-table-placement":
        shape = _require_event(event, {"type", "registry"})
        if shape:
            return _failed(texts, shape)
        if event.get("registry") not in {"relations", "RELATIONS.md", RELATIONS_PATH}:
            return _failed(
                texts,
                _event_error("REPAIR_REGISTRY_UNSUPPORTED", str(event.get("registry"))),
            )
        if input_findings and any(
            item.code != "RELATION_ROW_OUTSIDE_TABLE" for item in input_findings
        ):
            return _failed(texts, input_findings)
        relation_table = parsed["relations"]
        if not relation_table.orphan_rows:
            if input_findings:
                return _failed(texts, input_findings)
            topics = _mutable_rows(parsed["topics"], TOPICS_HEADER)
            return ReductionResult(True, _hashes(texts), derived=_derived(topics))
        try:
            replacement = _rehome_relation_orphans(relation_table)
        except ValueError as exc:
            return _failed(texts, _event_error("REPAIR_AMBIGUOUS", str(exc)))
        candidate = dict(texts)
        candidate["relations"] = replacement
        candidate_findings = validate_documents(
            candidate["manifest"], candidate["topics"], candidate["relations"]
        )
        if candidate_findings:
            return _failed(texts, candidate_findings)
        candidate_parsed = _parse_documents(candidate)
        topics = _mutable_rows(candidate_parsed["topics"], TOPICS_HEADER)
        return ReductionResult(
            True,
            _hashes(texts),
            documents={"relations": replacement},
            derived=_derived(topics),
        )

    if input_findings:
        return _failed(texts, input_findings)

    manifest_rows = _mutable_rows(parsed["manifest"], MANIFEST_HEADER)
    topic_rows = _mutable_rows(parsed["topics"], TOPICS_HEADER)
    relation_rows = _mutable_rows(parsed["relations"], RELATIONS_HEADER)
    changed: set[str] = set()
    applied_edge_ids: list[str] = []
    event_findings: list[Finding] = []
    source_derived: dict[str, Any] = {}

    if event_type == "source-upsert":
        event_findings.extend(
            _require_event(
                event,
                {
                    "type",
                    "source_id",
                    "canonical_url",
                    "artifact",
                    "first_seen",
                    "checked_on",
                    "summarized_on",
                    "content_hash",
                    "refresh_after",
                },
            )
        )
        source_id = event.get("source_id")
        canonical_url = event.get("canonical_url")
        artifact = event.get("artifact")
        content_hash = event.get("content_hash")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
            event_findings.extend(
                _event_error("EVENT_SOURCE_ID_INVALID", str(source_id))
            )
        normalized_url: str | None = None
        if not isinstance(canonical_url, str):
            event_findings.extend(
                _event_error("EVENT_CANONICAL_URL_INVALID", str(canonical_url))
            )
        else:
            try:
                normalized_url = normalize_canonical_url(canonical_url)
            except (TypeError, ValueError) as exc:
                event_findings.extend(
                    _event_error("EVENT_CANONICAL_URL_INVALID", str(exc))
                )
            else:
                if normalized_url != canonical_url:
                    event_findings.extend(
                        _event_error(
                            "EVENT_CANONICAL_URL_NOT_NORMALIZED", canonical_url
                        )
                    )
                if (
                    isinstance(source_id, str)
                    and source_id_for(normalized_url) != source_id
                ):
                    event_findings.extend(
                        _event_error("EVENT_SOURCE_ID_URL_MISMATCH", source_id)
                    )
        if not isinstance(content_hash, str) or not CONTENT_HASH_RE.fullmatch(
            content_hash
        ):
            event_findings.extend(
                _event_error("EVENT_CONTENT_HASH_INVALID", str(content_hash))
            )
        parsed_dates: dict[str, date] = {}
        for field_name in (
            "first_seen",
            "checked_on",
            "summarized_on",
            "refresh_after",
        ):
            parsed_date, findings = _parse_event_date(event.get(field_name), field_name)
            event_findings.extend(findings)
            if parsed_date is not None:
                parsed_dates[field_name] = parsed_date
        if len(parsed_dates) == 4:
            if not (
                parsed_dates["first_seen"]
                <= parsed_dates["summarized_on"]
                <= parsed_dates["checked_on"]
                <= parsed_dates["refresh_after"]
            ):
                event_findings.extend(
                    _event_error(
                        "EVENT_DATE_ORDER_INVALID",
                        "first_seen <= summarized_on <= checked_on <= refresh_after",
                    )
                )
        existing_by_id = next(
            (row for row in manifest_rows if row["Source ID"] == source_id), None
        )
        existing_by_url = next(
            (row for row in manifest_rows if row["Canonical URL"] == canonical_url),
            None,
        )
        if (
            existing_by_id is not None
            and existing_by_id["Canonical URL"] != canonical_url
        ):
            event_findings.extend(
                _event_error("EVENT_SOURCE_ID_URL_MISMATCH", str(canonical_url))
            )
        if existing_by_url is not None and existing_by_url["Source ID"] != source_id:
            event_findings.extend(
                _event_error("EVENT_SOURCE_ID_URL_MISMATCH", str(source_id))
            )
        is_new = existing_by_id is None and existing_by_url is None
        if existing_by_id is not None and existing_by_id["Status"] == "archived":
            event_findings.extend(_event_error("EVENT_SOURCE_ARCHIVED", str(source_id)))
        if isinstance(source_id, str) and isinstance(event.get("first_seen"), str):
            event_findings.extend(
                _validate_source_artifact_path(
                    artifact,
                    source_id,
                    event["first_seen"],
                    is_new=is_new,
                    existing_path=(
                        existing_by_id["Artifact"]
                        if existing_by_id is not None
                        else None
                    ),
                )
            )
        if event_findings:
            return _failed(texts, event_findings)
        assert (
            isinstance(source_id, str)
            and isinstance(canonical_url, str)
            and isinstance(artifact, str)
            and isinstance(content_hash, str)
        )
        if is_new:
            source = {
                "Source seq": str(
                    max((int(row["Source seq"]) for row in manifest_rows), default=0)
                    + 1
                ),
                "Source ID": source_id,
                "Canonical URL": canonical_url,
                "Artifact": artifact,
                "First seen": str(event["first_seen"]),
                "Last checked": str(event["checked_on"]),
                "Last summarized": str(event["summarized_on"]),
                "Content hash": content_hash,
                "Refresh after": str(event["refresh_after"]),
                "Route status": "unrouted",
                "Status": "active",
            }
            manifest_rows.append(source)
            content_changed = True
        else:
            assert existing_by_id is not None
            source = existing_by_id
            old_hash = source["Content hash"]
            content_changed = old_hash != content_hash
            source["Last checked"] = str(event["checked_on"])
            source["Last summarized"] = str(event["summarized_on"])
            source["Content hash"] = content_hash
            source["Refresh after"] = str(event["refresh_after"])
            if content_changed:
                source["Route status"] = "unrouted"
                for row in relation_rows:
                    if (
                        row["Source ID"] == source_id
                        and row["Status"] == "pending"
                        and row["Source content hash"] != content_hash
                    ):
                        row["Status"] = "superseded"
                _recompute_topics(topic_rows, relation_rows)
                changed.update({"topics", "relations"})
        manifest_rows.sort(key=lambda row: int(row["Source seq"]))
        changed.add("manifest")
        source_derived = {
            "source": {
                "created": is_new,
                "content_changed": content_changed,
                "source_seq": int(source["Source seq"]),
                "source_id": source_id,
                "canonical_url": canonical_url,
                "artifact": source["Artifact"],
                "first_seen": source["First seen"],
                "content_hash": source["Content hash"],
                "route_status": source["Route status"],
                "status": source["Status"],
            }
        }

    elif event_type == "route-upsert":
        event_findings.extend(
            _require_event(
                event,
                {"type", "source_id", "content_hash", "checked_on", "outcome", "edges"},
            )
        )
        source_id = event.get("source_id")
        content_hash = event.get("content_hash")
        checked_on = event.get("checked_on")
        outcome = event.get("outcome")
        edges = event.get("edges")
        if not isinstance(source_id, str) or not SOURCE_ID_RE.fullmatch(source_id):
            event_findings.extend(
                _event_error("EVENT_SOURCE_ID_INVALID", str(source_id))
            )
        if not isinstance(content_hash, str) or not CONTENT_HASH_RE.fullmatch(
            content_hash
        ):
            event_findings.extend(
                _event_error("EVENT_CONTENT_HASH_INVALID", str(content_hash))
            )
        if not isinstance(checked_on, str) or not DATE_RE.fullmatch(checked_on):
            event_findings.extend(_event_error("EVENT_DATE_INVALID", str(checked_on)))
        if outcome not in {"routed", "no-topic-match", "routing-blocked"}:
            event_findings.extend(_event_error("EVENT_OUTCOME_INVALID", str(outcome)))
        if not isinstance(edges, list):
            event_findings.extend(
                _event_error("EVENT_EDGES_INVALID", "edges must be an array")
            )
            edges = []
        source = next(
            (row for row in manifest_rows if row["Source ID"] == source_id), None
        )
        if source is None:
            event_findings.extend(_event_error("EVENT_SOURCE_UNKNOWN", str(source_id)))
        elif source["Status"] == "archived":
            event_findings.extend(_event_error("EVENT_SOURCE_ARCHIVED", source_id))
        elif (
            isinstance(content_hash, str)
            and CONTENT_HASH_RE.fullmatch(content_hash)
            and content_hash != source["Content hash"]
        ):
            event_findings.extend(
                _event_error("EVENT_CONTENT_HASH_MISMATCH", content_hash)
            )
        included_topics: set[str] = set()
        normalized_edges: list[dict[str, str]] = []
        for index, edge in enumerate(edges):
            row_id = str(index)
            if not isinstance(edge, Mapping):
                event_findings.extend(
                    _event_error("EVENT_EDGE_INVALID", "edge must be an object", row_id)
                )
                continue
            expected = {"topic_id", "relation", "impact", "confidence", "reason"}
            actual = set(edge)
            for name in sorted(expected - actual):
                event_findings.append(
                    Finding("EVENT_FIELD_MISSING", "event", row=row_id, detail=name)
                )
            for name in sorted(actual - expected):
                event_findings.append(
                    Finding("EVENT_FIELD_UNKNOWN", "event", row=row_id, detail=name)
                )
            topic_id = edge.get("topic_id")
            relation = edge.get("relation")
            impact = edge.get("impact")
            confidence = edge.get("confidence")
            if (
                not isinstance(topic_id, str)
                or _topic_row(topic_rows, topic_id) is None
            ):
                event_findings.extend(
                    _event_error("EVENT_TOPIC_UNKNOWN", str(topic_id), row_id)
                )
            elif topic_id in included_topics:
                event_findings.extend(
                    _event_error("EVENT_TOPIC_DUPLICATE", topic_id, row_id)
                )
            else:
                included_topics.add(topic_id)
            if relation not in RELATIONS:
                event_findings.extend(
                    _event_error("EVENT_RELATION_INVALID", str(relation), row_id)
                )
            if impact not in LEVELS:
                event_findings.extend(
                    _event_error("EVENT_IMPACT_INVALID", str(impact), row_id)
                )
            if confidence not in LEVELS:
                event_findings.extend(
                    _event_error("EVENT_CONFIDENCE_INVALID", str(confidence), row_id)
                )
            if isinstance(relation, str) and isinstance(impact, str):
                event_findings.extend(
                    _validate_reason(edge.get("reason"), relation, impact, row_id)
                )
            if not event_findings or all(item.row != row_id for item in event_findings):
                normalized_edges.append({name: str(edge[name]) for name in expected})
        if outcome == "routed" and not normalized_edges:
            event_findings.extend(
                _event_error(
                    "EVENT_OUTCOME_EDGE_MISMATCH", "routed requires an included edge"
                )
            )
        if outcome != "routed" and normalized_edges:
            event_findings.extend(
                _event_error(
                    "EVENT_OUTCOME_EDGE_MISMATCH",
                    "non-routed outcome cannot include edges",
                )
            )
        if event_findings:
            return _failed(texts, event_findings)
        assert (
            source is not None
            and isinstance(content_hash, str)
            and isinstance(checked_on, str)
        )
        old_hash = source["Content hash"]
        source["Content hash"] = content_hash
        source["Last checked"] = checked_on
        if old_hash != content_hash:
            for row in relation_rows:
                if (
                    row["Source ID"] == source_id
                    and row["Status"] == "pending"
                    and row["Source content hash"] != content_hash
                ):
                    row["Status"] = "superseded"
        for row in relation_rows:
            if (
                row["Source ID"] == source_id
                and row["Source content hash"] == content_hash
                and row["Status"] == "pending"
                and row["Topic ID"] not in included_topics
            ):
                row["Status"] = "rejected"
        for edge in normalized_edges:
            edge_id = _edge_id(source_id, edge["topic_id"], content_hash)
            existing = next(
                (row for row in relation_rows if row["Edge ID"] == edge_id), None
            )
            if existing is not None and existing["Status"] == "applied":
                continue
            values = {
                "Edge ID": edge_id,
                "Source seq": source["Source seq"],
                "Source ID": source_id,
                "Source artifact": source["Artifact"],
                "Source content hash": content_hash,
                "Topic ID": edge["topic_id"],
                "Relation": edge["relation"],
                "Impact": edge["impact"],
                "Confidence": edge["confidence"],
                "Status": "pending",
                "Created": checked_on,
                "Applied in pass": "",
                "Notes": edge["reason"],
            }
            if existing is None:
                relation_rows.append(values)
            elif existing["Status"] in {"pending", "rejected"}:
                existing.update(values)
        current = [
            row
            for row in relation_rows
            if row["Source ID"] == source_id
            and row["Source content hash"] == content_hash
            and row["Status"] in {"pending", "applied"}
        ]
        source["Route status"] = "routed" if current else str(outcome)
        relation_rows.sort(key=lambda row: (int(row["Source seq"]), row["Edge ID"]))
        _recompute_topics(topic_rows, relation_rows)
        changed.update({"manifest", "topics", "relations"})

    elif event_type == "refresh-start":
        event_findings.extend(
            _require_event(event, {"type", "topic_id", "edge_ids", "started_at"})
        )
        topic_id = event.get("topic_id")
        edge_ids = event.get("edge_ids")
        started_at = event.get("started_at")
        topic = (
            _topic_row(topic_rows, str(topic_id)) if isinstance(topic_id, str) else None
        )
        if topic is None:
            event_findings.extend(_event_error("EVENT_TOPIC_UNKNOWN", str(topic_id)))
        if not isinstance(edge_ids, list) or not all(
            isinstance(item, str) for item in edge_ids
        ):
            event_findings.extend(
                _event_error("EVENT_EDGE_IDS_INVALID", "edge_ids must be strings")
            )
            edge_ids = []
        if not isinstance(started_at, str) or not started_at:
            event_findings.extend(
                _event_error("EVENT_STARTED_AT_INVALID", str(started_at))
            )
        pending = _pending_for_topic(relation_rows, str(topic_id))
        expected = [row["Edge ID"] for row in pending]
        if edge_ids != expected:
            event_findings.extend(
                _event_error("REFRESH_PENDING_SET_MISMATCH", f"expected {expected!r}")
            )
        if event_findings:
            return _failed(texts, event_findings)
        assert topic is not None
        if topic["Freshness state"] != "refreshing":
            topic["Freshness state"] = "refreshing"
            changed.add("topics")

    elif event_type == "refresh-complete":
        event_findings.extend(
            _require_event(
                event, {"type", "topic_id", "edge_ids", "pass_path", "completed_on"}
            )
        )
        topic_id = event.get("topic_id")
        edge_ids = event.get("edge_ids")
        pass_path = event.get("pass_path")
        completed_on = event.get("completed_on")
        topic = (
            _topic_row(topic_rows, str(topic_id)) if isinstance(topic_id, str) else None
        )
        if topic is None:
            event_findings.extend(_event_error("EVENT_TOPIC_UNKNOWN", str(topic_id)))
        if not isinstance(edge_ids, list) or not all(
            isinstance(item, str) for item in edge_ids
        ):
            event_findings.extend(
                _event_error("EVENT_EDGE_IDS_INVALID", "edge_ids must be strings")
            )
            edge_ids = []
        if not isinstance(pass_path, str) or not pass_path:
            event_findings.extend(
                _event_error("EVENT_PASS_PATH_INVALID", str(pass_path))
            )
        if not isinstance(completed_on, str) or not DATE_RE.fullmatch(completed_on):
            event_findings.extend(_event_error("EVENT_DATE_INVALID", str(completed_on)))
        pending = _pending_for_topic(relation_rows, str(topic_id))
        expected = [row["Edge ID"] for row in pending]
        already = [row for row in relation_rows if row["Edge ID"] in edge_ids]
        idempotent = (
            bool(edge_ids)
            and len(already) == len(edge_ids)
            and all(
                row["Status"] == "applied" and row["Applied in pass"] == pass_path
                for row in already
            )
        )
        if edge_ids != expected and not idempotent:
            event_findings.extend(
                _event_error("REFRESH_PENDING_SET_MISMATCH", f"expected {expected!r}")
            )
        if event_findings:
            return _failed(texts, event_findings)
        if not idempotent:
            edge_set = set(edge_ids)
            for row in relation_rows:
                if row["Edge ID"] in edge_set:
                    row["Status"] = "applied"
                    row["Applied in pass"] = str(pass_path)
            _recompute_topics(
                topic_rows,
                relation_rows,
                states={str(topic_id): "current"},
                synthesized={str(topic_id): str(completed_on)},
            )
            changed.update({"relations", "topics"})
            applied_edge_ids = list(edge_ids)

    elif event_type == "refresh-fail":
        event_findings.extend(_require_event(event, {"type", "topic_id", "reason"}))
        topic_id = event.get("topic_id")
        reason = event.get("reason")
        topic = (
            _topic_row(topic_rows, str(topic_id)) if isinstance(topic_id, str) else None
        )
        if topic is None:
            event_findings.extend(_event_error("EVENT_TOPIC_UNKNOWN", str(topic_id)))
        if not isinstance(reason, str) or not reason.strip():
            event_findings.extend(
                _event_error("EVENT_REASON_INVALID", "reason must be nonempty")
            )
        if topic is not None and not _pending_for_topic(relation_rows, str(topic_id)):
            event_findings.extend(
                _event_error("REFRESH_PENDING_SET_EMPTY", str(topic_id))
            )
        if event_findings:
            return _failed(texts, event_findings)
        assert topic is not None
        if topic["Freshness state"] != "blocked":
            topic["Freshness state"] = "blocked"
            changed.add("topics")

    elif event_type == "repair-relation-notes":
        event_findings.extend(_require_event(event, {"type", "repairs"}))
        repairs = event.get("repairs")
        if not isinstance(repairs, list):
            event_findings.extend(
                _event_error("EVENT_REPAIRS_INVALID", "repairs must be an array")
            )
            repairs = []
        seen: set[str] = set()
        normalized: list[tuple[dict[str, str], str]] = []
        for index, repair in enumerate(repairs):
            row_id = str(index)
            if not isinstance(repair, Mapping):
                event_findings.extend(
                    _event_error(
                        "EVENT_REPAIR_INVALID", "repair must be an object", row_id
                    )
                )
                continue
            expected = {"edge_id", "reason"}
            for name in sorted(expected - set(repair)):
                event_findings.append(
                    Finding("EVENT_FIELD_MISSING", "event", row=row_id, detail=name)
                )
            for name in sorted(set(repair) - expected):
                event_findings.append(
                    Finding("EVENT_FIELD_UNKNOWN", "event", row=row_id, detail=name)
                )
            edge_id = repair.get("edge_id")
            target = next(
                (row for row in relation_rows if row["Edge ID"] == edge_id), None
            )
            if target is None:
                event_findings.extend(
                    _event_error("EVENT_EDGE_UNKNOWN", str(edge_id), row_id)
                )
                continue
            if str(edge_id) in seen:
                event_findings.extend(
                    _event_error("EVENT_EDGE_DUPLICATE", str(edge_id), row_id)
                )
                continue
            seen.add(str(edge_id))
            event_findings.extend(
                _validate_reason(
                    repair.get("reason"),
                    target["Relation"],
                    target["Impact"],
                    str(edge_id),
                )
            )
            if isinstance(repair.get("reason"), str):
                normalized.append((target, repair["reason"]))
        if event_findings:
            return _failed(texts, event_findings)
        for target, reason in normalized:
            if target["Notes"] != reason:
                target["Notes"] = reason
                changed.add("relations")

    else:
        return _failed(texts, _event_error("EVENT_TYPE_UNKNOWN", event_type))

    replacements: dict[str, str] = {}
    if "manifest" in changed:
        replacements["manifest"] = _replace_rows(
            parsed["manifest"], _rows_from_dicts(manifest_rows, MANIFEST_HEADER)
        )
    if "topics" in changed:
        replacements["topics"] = _replace_rows(
            parsed["topics"], _rows_from_dicts(topic_rows, TOPICS_HEADER)
        )
    if "relations" in changed:
        replacements["relations"] = _replace_rows(
            parsed["relations"], _rows_from_dicts(relation_rows, RELATIONS_HEADER)
        )
    candidate = dict(texts)
    candidate.update(replacements)
    candidate_findings = validate_documents(
        candidate["manifest"], candidate["topics"], candidate["relations"]
    )
    if candidate_findings:
        return _failed(texts, candidate_findings)
    return ReductionResult(
        True,
        _hashes(texts),
        documents={
            name: text for name, text in replacements.items() if text != texts[name]
        },
        derived={**_derived(topic_rows), **source_derived},
        applied_edge_ids=applied_edge_ids,
    )


def audit_instance(instance_root: str | Path) -> list[Finding]:
    """Read and validate one local instance for the provision checker."""
    root = Path(instance_root)
    texts: dict[str, str] = {}
    findings: list[Finding] = []
    for name, relative in PATHS.items():
        path = root / relative
        if not path.is_file():
            findings.append(Finding("REGISTRY_FILE_MISSING", relative))
            continue
        try:
            texts[name] = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            findings.append(Finding("REGISTRY_UTF8_INVALID", relative, detail=str(exc)))
    if findings:
        return _normalize_findings(findings)
    return validate_documents(texts["manifest"], texts["topics"], texts["relations"])


def _load_bundle(path: str) -> dict[str, Any]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("bundle must be an object")
    if value.get("version") != VERSION:
        raise ValueError(f"bundle.version must be {VERSION}")
    allowed = {"version", "documents", "event"}
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f"unknown bundle keys: {sorted(unknown)}")
    if not isinstance(value.get("documents"), Mapping):
        raise ValueError("bundle.documents must be an object")
    return value


def _emit(payload: Mapping[str, Any]) -> None:
    sys.stdout.write(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )
    sys.stdout.write("\n")


def _cmd_validate(bundle: Mapping[str, Any]) -> int:
    texts = _documents_text(bundle["documents"])
    findings = validate_documents(
        texts["manifest"], texts["topics"], texts["relations"]
    )
    _emit({"ok": not findings, "findings": [finding.to_dict() for finding in findings]})
    return 0 if not findings else 2


def _cmd_reduce(bundle: Mapping[str, Any]) -> int:
    if "event" not in bundle:
        raise ValueError("reduce requires bundle.event")
    result = reduce_event(bundle["documents"], bundle["event"])
    _emit(result.to_dict())
    return 0 if result.ok else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atlas_state.py",
        description="Validate or reduce Atlas Markdown registries without storage I/O.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "reduce"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument(
            "--input", required=True, help="Versioned JSON bundle path, or - for stdin"
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        bundle = _load_bundle(args.input)
        if args.command == "validate":
            return _cmd_validate(bundle)
        return _cmd_reduce(bundle)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"atlas-state: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
