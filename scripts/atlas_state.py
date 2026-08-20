#!/usr/bin/env python3
"""Deterministic Atlas Markdown registry validation and reduction.

The core API consumes and returns text. Only ``audit_instance`` touches a local
filesystem; connector adapters remain responsible for logical vault I/O and
optimistic writes.
"""

from __future__ import annotations

from datetime import date
import hashlib
import unicodedata
import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from atlas_url import normalize_canonical_url, source_id_for

VERSION = 1

MANIFEST_PATH = "summaries/sources/MANIFEST.md"
TOPICS_PATH = "summaries/registry/TOPICS.md"
RELATIONS_PATH = "summaries/registry/RELATIONS.md"
VOCAB_PATH = "summaries/registry/VOCAB.md"

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
VOCAB_HEADER = (
    "ID",
    "Type",
    "Label",
    "Parent",
    "Allowed aliases",
    "Status",
    "Notes",
)
HEADERS = {
    "manifest": MANIFEST_HEADER,
    "topics": TOPICS_HEADER,
    "relations": RELATIONS_HEADER,
}
TABLE_HEADERS = {**HEADERS, "vocab": VOCAB_HEADER}
PATHS = {
    "manifest": MANIFEST_PATH,
    "topics": TOPICS_PATH,
    "relations": RELATIONS_PATH,
}
TABLE_PATHS = {**PATHS, "vocab": VOCAB_PATH}

SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")
CONTENT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EDGE_ID_RE = re.compile(r"^edge--[0-9a-f]{12}--[a-z0-9][a-z0-9-]*--[0-9a-f]{8}$")
VOCAB_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
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
VOCAB_TYPES = {"domain", "subdomain", "tag", "source-kind"}
VOCAB_STATUSES = {"active", "deprecated", "reserved"}

TOPIC_MANAGED_SECTIONS = (
    "agent-answer-contract",
    "scope-and-routing",
    "current-answer",
    "decision-tree",
    "recommendation-matrix",
    "edge-cases",
    "caveats-failure-modes",
    "evidence-map",
    "gaps-and-acquisition-needs",
    "recent-changes",
    "read-next",
)
SUBDOMAIN_MANAGED_SECTIONS = (
    "routing-scope",
    "topic-map",
    "default-lookup-order",
    "coverage-map",
    "stale-or-weak-areas",
    "acquisition-watchlist",
)
INSPECTION_PURPOSES = {"answer", "research", "refresh"}
REVISION_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ANSWER_AUTHORING_SECTIONS = ("current-answer", "decision-tree")
INITIAL_CURRENT_ANSWER = (
    "- No evidence-backed answer exists; acquisition and research are required."
)
SOURCE_ARTIFACT_REFERENCE_RE = re.compile(
    r"(?:vault://atlas/)?summaries/sources/artifacts/[^\s\]\[()<>`\"'|]+?\.md"
)


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
    header = TABLE_HEADERS[name]
    path = TABLE_PATHS[name]
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
            result.append(
                f"\\u{{{ord(char):04x}}}" if char not in reserved else "\\" + char
            )
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
        all(unicodedata.category(char) != "Cs" for char in value) for value in values
    )
    return values, canonical == raw and scalar_valid


_TOPICS_LIST_FIELDS = (
    "Aliases",
    "Canonical tags",
    "Include terms",
    "Exclude terms",
)


def _strict_registry_list(
    raw: str,
) -> tuple[list[str] | None, bool, str | None]:
    """Decode one target cell through the existing registry-list codec."""
    if raw == "":
        return [], True, None

    source = _registry_markdown_decode(raw)
    index = 0
    while index < len(source):
        if source[index] != "\\":
            index += 1
            continue
        if index + 1 >= len(source):
            return None, False, "TOPICS_LIST_ESCAPE_INVALID"
        next_char = source[index + 1]
        if next_char == "\\":
            index += 2
            continue
        if source.startswith("\\u{", index):
            close = source.find("}", index + 3)
            if close < 0:
                return None, False, "TOPICS_LIST_ESCAPE_INVALID"
            digits = source[index + 3 : close]
            if not re.fullmatch(r"[0-9A-Fa-f]{1,6}", digits):
                return None, False, "TOPICS_LIST_ESCAPE_INVALID"
            codepoint = int(digits, 16)
            if codepoint > 0x10FFFF:
                return None, False, "TOPICS_LIST_ESCAPE_INVALID"
            if 0xD800 <= codepoint <= 0xDFFF:
                return None, False, "TOPICS_LIST_SURROGATE"
            index = close + 1
            continue
        if not next_char.isalnum():
            index += 2
            continue
        return None, False, "TOPICS_LIST_ESCAPE_INVALID"

    values, canonical = _registry_list(raw)
    if values is None:
        return None, False, "TOPICS_LIST_AMBIGUOUS"
    if any(not value.strip() for value in values):
        return values, False, "TOPICS_LIST_BLANK"
    if len(set(values)) != len(values):
        return values, False, "TOPICS_LIST_DUPLICATE"
    if any(unicodedata.category(char) == "Cs" for value in values for char in value):
        return values, False, "TOPICS_LIST_SURROGATE"
    return values, canonical, None


def _topics_row_cell_spans(
    text: str,
) -> list[tuple[int, str, list[str], list[tuple[int, int]]]]:
    """Return raw value spans for rows in the canonical TOPICS table."""
    header = TOPICS_HEADER
    lines = text.splitlines(keepends=True)
    offsets: list[int] = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)
    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if tuple(split_markdown_row(line) or ()) == header
        ),
        None,
    )
    if header_index is None or header_index + 1 >= len(lines):
        return []
    separator = split_markdown_row(lines[header_index + 1])
    if separator is None or not _is_separator(separator, len(header)):
        return []
    result: list[tuple[int, str, list[str], list[tuple[int, int]]]] = []
    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        cells = split_markdown_row(line)
        if cells is None:
            break
        if len(cells) != len(header) or _is_separator(cells, len(header)):
            break
        body = _body(line)
        left = len(body) - len(body.lstrip())
        right = len(body.rstrip())
        if right <= left or body[left:right][0] != "|" or body[left:right][-1] != "|":
            break
        pipes: list[int] = []
        escaped = False
        for position in range(left, right):
            char = body[position]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "|":
                pipes.append(position)
        if len(pipes) != len(header) + 1:
            break
        spans: list[tuple[int, int]] = []
        for cell_index in range(len(header)):
            start, end = pipes[cell_index] + 1, pipes[cell_index + 1]
            raw = body[start:end]
            leading = len(raw) - len(raw.lstrip())
            trailing = len(raw) - len(raw.rstrip())
            if leading + trailing >= len(raw):
                value_start = value_end = start + leading
            else:
                value_start = start + leading
                value_end = end - trailing
            spans.append((offsets[index] + value_start, offsets[index] + value_end))
        result.append((index + 1, cells[0], cells, spans))
    return result


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
                    Finding(
                        "TOPIC_SCOPE_INVALID", table.path, line, topic_id, field_name
                    )
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
            findings.append(Finding("TOPIC_PATH_INVALID", table.path, line, topic_id))
        title = _registry_decode_scalar(row["Canonical title"])
        if not title.strip():
            findings.append(Finding("TOPIC_TITLE_INVALID", table.path, line, topic_id))
        elif _registry_encode_scalar(title) != row["Canonical title"] or any(
            unicodedata.category(char) in {"Cs"} for char in title
        ):
            findings.append(
                Finding("TOPIC_TITLE_NONCANONICAL", table.path, line, topic_id)
            )
        for field_name in (
            "Aliases",
            "Canonical tags",
            "Include terms",
            "Exclude terms",
        ):
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


def _decode_vocab_scalar(raw: str) -> str:
    return _registry_decode_scalar(_registry_markdown_decode(raw))


def _encode_vocab_scalar(value: str) -> str:
    inner = _registry_encode_scalar(value, reserved="")
    return _registry_markdown_encode(inner)


def _encode_registry_list(values: Sequence[str]) -> str:
    inner = "; ".join(
        _registry_encode_scalar(value, reserved=";", protect_literals=True)
        for value in values
    )
    return _registry_markdown_encode(inner)


def _validated_vocab(
    vocab_text: str,
) -> tuple[ParsedTable, list[dict[str, Any]], list[Finding]]:
    table = _parse_table("vocab", vocab_text)
    structural = _normalize_findings(table.findings)
    if structural:
        return table, [], structural

    raw_rows = [_row_dict(VOCAB_HEADER, row) for row in table.rows]
    findings = _find_duplicates(
        (
            (row["ID"], line)
            for row, line in zip(raw_rows, table.row_lines, strict=True)
        ),
        "VOCAB_DUPLICATE_ID",
        table.path,
    )
    records: list[dict[str, Any]] = []
    for row, line in zip(raw_rows, table.row_lines, strict=True):
        row_id = row["ID"]
        row_type = row["Type"]
        label = _decode_vocab_scalar(row["Label"])
        parent = row["Parent"]
        aliases, aliases_canonical = _registry_list(row["Allowed aliases"])
        if not VOCAB_ID_RE.fullmatch(row_id):
            findings.append(Finding("VOCAB_ID_INVALID", table.path, line, row_id))
        if row_type not in VOCAB_TYPES:
            findings.append(Finding("VOCAB_TYPE_INVALID", table.path, line, row_id))
        if not label.strip() or _encode_vocab_scalar(label) != row["Label"]:
            findings.append(Finding("VOCAB_LABEL_INVALID", table.path, line, row_id))
        if (
            aliases is None
            or not aliases_canonical
            or any(not alias.strip() for alias in aliases)
            or len(set(aliases)) != len(aliases)
        ):
            findings.append(Finding("VOCAB_ALIASES_INVALID", table.path, line, row_id))
            aliases = aliases or []
        if row["Status"] not in VOCAB_STATUSES:
            findings.append(Finding("VOCAB_STATUS_INVALID", table.path, line, row_id))
        records.append(
            {
                "id": row_id,
                "type": row_type,
                "label": label,
                "parent": parent,
                "aliases": list(aliases),
                "status": row["Status"],
                "raw": row,
            }
        )

    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        by_id.setdefault(str(record["id"]), record)
    for record, line in zip(records, table.row_lines, strict=True):
        row_id = str(record["id"])
        row_type = str(record["type"])
        parent = str(record["parent"])
        parent_record = by_id.get(parent)
        parent_valid = (
            parent_record is not None and parent_record.get("type") == "domain"
        )
        if row_type in {"domain", "source-kind"} and parent:
            findings.append(Finding("VOCAB_PARENT_INVALID", table.path, line, row_id))
        elif row_type == "subdomain" and not parent_valid:
            findings.append(Finding("VOCAB_PARENT_INVALID", table.path, line, row_id))
        elif row_type == "tag" and parent and not parent_valid:
            findings.append(Finding("VOCAB_PARENT_INVALID", table.path, line, row_id))
    return table, records, _normalize_findings(findings)


def validate_vocab(vocab_text: str) -> list[Finding]:
    """Validate the complete canonical Atlas vocabulary table."""
    if not isinstance(vocab_text, str):
        raise TypeError("vocab_text must be text")
    return _validated_vocab(vocab_text)[2]


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
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    *,
    vocab_text: str | None = None,
) -> list[Finding]:
    """Validate the complete canonical Atlas registry state."""
    documents = {
        "manifest": manifest_text,
        "topics": topics_text,
        "relations": relations_text,
    }
    parsed = _parse_documents(documents)
    vocab_findings = validate_vocab(vocab_text) if vocab_text is not None else []
    structural = _normalize_findings(
        [
            *(finding for table in parsed.values() for finding in table.findings),
            *vocab_findings,
        ]
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


def prepare_topics_list_candidate(
    manifest_text: str,
    topics_text: str,
    relations_text: str,
) -> TopicsListCandidateResult:
    """Prepare a deterministic, span-preserving TOPICS list normalization."""
    baseline = _normalize_findings(
        validate_documents(manifest_text, topics_text, relations_text)
    )
    rows = _topics_row_cell_spans(topics_text)
    target_indices = {
        field: TOPICS_HEADER.index(field) for field in _TOPICS_LIST_FIELDS
    }
    analyzed: dict[
        tuple[int, str, str],
        tuple[str, list[str], bool, str, tuple[int, int]],
    ] = {}
    candidate_findings: list[Finding] = []
    for line, topic_id, cells, spans in rows:
        for field_name in _TOPICS_LIST_FIELDS:
            index = target_indices[field_name]
            raw = cells[index]
            values, _, error = _strict_registry_list(raw)
            if error is not None or values is None:
                candidate_findings.append(
                    Finding(
                        error or "TOPICS_LIST_AMBIGUOUS",
                        TOPICS_PATH,
                        line,
                        topic_id,
                        field_name,
                    )
                )
                continue
            ordered_values = sorted(values, key=lambda value: value.encode("utf-8"))
            canonical_raw = _registry_markdown_encode(
                "; ".join(
                    _registry_encode_scalar(
                        value,
                        reserved=";",
                        protect_literals=True,
                    )
                    for value in ordered_values
                )
            )
            analyzed[(line, topic_id, field_name)] = (
                raw,
                values,
                raw == canonical_raw,
                canonical_raw,
                spans[index],
            )

    if candidate_findings:
        return TopicsListCandidateResult(
            "invalid",
            findings=tuple(_normalize_findings([*baseline, *candidate_findings])),
        )

    allowed_baseline: set[tuple[int, str, str]] = set()
    for finding in baseline:
        if (
            finding.code == "TOPIC_LIST_INVALID"
            and finding.path == TOPICS_PATH
            and finding.line is not None
            and finding.row is not None
            and finding.detail in _TOPICS_LIST_FIELDS
        ):
            allowed_baseline.add((finding.line, finding.row, finding.detail))
        else:
            return TopicsListCandidateResult(
                "invalid",
                findings=tuple(baseline),
            )
    noncanonical = {
        key for key, (_, _, canonical, _, _) in analyzed.items() if not canonical
    }
    if not allowed_baseline.issubset(noncanonical):
        mismatched = sorted(
            allowed_baseline - noncanonical,
            key=lambda item: (item[0], item[1].encode("utf-8"), item[2]),
        )
        findings = [
            Finding(
                "TOPICS_LIST_SEMANTIC_CHANGE",
                TOPICS_PATH,
                line,
                topic_id,
                field,
            )
            for line, topic_id, field in mismatched
        ]
        return TopicsListCandidateResult(
            "invalid",
            findings=tuple(_normalize_findings(findings)),
        )
    if not noncanonical:
        return TopicsListCandidateResult("no-op")

    replacements: list[tuple[int, int, str]] = []
    changes: list[dict[str, Any]] = []
    for line, topic_id, cells, _ in rows:
        for field_name in _TOPICS_LIST_FIELDS:
            key = (line, topic_id, field_name)
            if key not in noncanonical:
                continue
            raw, values, _, canonical_raw, span = analyzed[key]
            replacements.append((span[0], span[1], canonical_raw))
            changes.append(
                {
                    "topic_id": topic_id,
                    "line": line,
                    "field": field_name,
                    "before": raw,
                    "after": canonical_raw,
                }
            )

    candidate_parts: list[str] = []
    cursor = 0
    for start, end, replacement in replacements:
        candidate_parts.append(topics_text[cursor:start])
        candidate_parts.append(replacement)
        cursor = end
    candidate_parts.append(topics_text[cursor:])
    candidate_text = "".join(candidate_parts)

    post_findings = _normalize_findings(
        validate_documents(manifest_text, candidate_text, relations_text)
    )
    if post_findings:
        return TopicsListCandidateResult(
            "invalid",
            findings=tuple(post_findings),
        )

    candidate_rows = _topics_row_cell_spans(candidate_text)
    candidate_by_identity = {(row[0], row[1]): row for row in candidate_rows}
    for (line, topic_id, field_name), (_, values, _, _, _) in analyzed.items():
        if (line, topic_id, field_name) not in noncanonical:
            continue
        matching = candidate_by_identity.get((line, topic_id))
        if matching is None:
            return TopicsListCandidateResult(
                "invalid",
                findings=(
                    Finding(
                        "TOPICS_LIST_SEMANTIC_CHANGE",
                        TOPICS_PATH,
                        line,
                        topic_id,
                        field_name,
                    ),
                ),
            )
        candidate_value, candidate_canonical, candidate_error = _strict_registry_list(
            matching[2][TOPICS_HEADER.index(field_name)]
        )
        if (
            candidate_error is not None
            or candidate_value is None
            or not candidate_canonical
            or sorted(candidate_value, key=lambda value: value.encode("utf-8"))
            != sorted(values, key=lambda value: value.encode("utf-8"))
        ):
            return TopicsListCandidateResult(
                "invalid",
                findings=(
                    Finding(
                        "TOPICS_LIST_SEMANTIC_CHANGE",
                        TOPICS_PATH,
                        line,
                        topic_id,
                        field_name,
                    ),
                ),
            )

    preimage_revision = (
        "sha256:" + hashlib.sha256(topics_text.encode("utf-8")).hexdigest()
    )
    output_revision = (
        "sha256:" + hashlib.sha256(candidate_text.encode("utf-8")).hexdigest()
    )
    return TopicsListCandidateResult(
        "candidate",
        preimage_revision=preimage_revision,
        output_revision=output_revision,
        preimage_text=topics_text,
        text=candidate_text,
        changes=tuple(changes),
    )


def _documents_text(documents: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in HEADERS:
        value = documents.get(name)
        if isinstance(value, str):
            result[name] = value
            continue
        if isinstance(value, Mapping):
            text = value.get("text")
            if isinstance(text, str):
                result[name] = text
                continue
        raise ValueError(f"documents.{name} must be text or an object with text")
    allowed = set(HEADERS) | {"vocab"}
    extra = sorted(set(documents) - allowed)
    if extra:
        raise ValueError(f"unknown document keys: {extra}")
    if "vocab" in documents:
        value = documents["vocab"]
        if isinstance(value, str):
            result["vocab"] = value
        elif isinstance(value, Mapping):
            text = value.get("text")
            if not isinstance(text, str):
                raise ValueError("documents.vocab must be text or an object with text")
            result["vocab"] = text
        else:
            raise ValueError("documents.vocab must be text or an object with text")
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


def _append_rows(table: ParsedTable, rows: Sequence[Sequence[str]]) -> str:
    if table.data_end is None:
        raise ValueError(f"cannot append to invalid {table.name} table")
    if not rows:
        return table.text
    prefix = "".join(table.lines[: table.data_end])
    suffix = "".join(table.lines[table.data_end :])
    if prefix and not prefix.endswith(("\n", "\r")):
        prefix += table.newline
    rendered = "".join(_render_row(row, table.newline) for row in rows)
    text = prefix + rendered + suffix
    if not table.final_newline and text.endswith(table.newline):
        text = text[: -len(table.newline)]
    return text


def _classification_finding(path: str, detail: str) -> Finding:
    return Finding("SOURCE_CLASSIFICATION_INVALID", path, detail=detail)


def _normalize_classification_entry(
    value: Any,
    *,
    path: str,
    subdomain: bool,
) -> tuple[dict[str, Any] | None, list[Finding]]:
    expected = {"id", "label", "aliases"} | ({"parent"} if subdomain else set())
    if not isinstance(value, Mapping) or set(value) != expected:
        return None, [_classification_finding(path, "entry fields are invalid")]
    findings: list[Finding] = []
    row_id = value.get("id")
    label = value.get("label")
    aliases = value.get("aliases")
    if not isinstance(row_id, str) or not VOCAB_ID_RE.fullmatch(row_id):
        findings.append(_classification_finding(f"{path}.id", "expected kebab-case ID"))
    if not isinstance(label, str) or not label.strip():
        findings.append(
            _classification_finding(f"{path}.label", "expected nonblank text")
        )
    if not isinstance(aliases, list):
        findings.append(_classification_finding(f"{path}.aliases", "expected array"))
        normalized_aliases: list[str] = []
    else:
        normalized_aliases = []
        for index, alias in enumerate(aliases):
            if not isinstance(alias, str) or not alias.strip():
                findings.append(
                    _classification_finding(
                        f"{path}.aliases[{index}]", "expected nonblank text"
                    )
                )
                continue
            normalized_aliases.append(alias.strip())
        if len(set(normalized_aliases)) != len(normalized_aliases):
            findings.append(
                _classification_finding(f"{path}.aliases", "aliases must be unique")
            )
    parent: str | None = None
    if subdomain:
        parent_value = value.get("parent")
        if not isinstance(parent_value, str) or not parent_value.strip():
            findings.append(
                _classification_finding(f"{path}.parent", "expected nonblank text")
            )
        else:
            parent = parent_value.strip()
    if findings:
        return None, findings
    assert isinstance(row_id, str) and isinstance(label, str)
    normalized: dict[str, Any] = {
        "id": row_id,
        "label": label.strip(),
        "aliases": normalized_aliases,
    }
    if subdomain:
        assert parent is not None
        normalized["parent"] = parent
    return normalized, []


def normalize_source_classification(
    value: Any,
) -> tuple[dict[str, Any] | None, list[Finding]]:
    """Validate and trim one optional source-intrinsic classification."""
    if value is None:
        return None, []
    if not isinstance(value, Mapping) or set(value) != {
        "domain",
        "subdomain",
        "tags",
        "candidate_terms",
    }:
        return None, [
            _classification_finding(
                "worker.classification", "classification fields are invalid"
            )
        ]

    findings: list[Finding] = []
    domain: dict[str, Any] | None = None
    if value["domain"] is not None:
        domain, entry_findings = _normalize_classification_entry(
            value["domain"], path="worker.classification.domain", subdomain=False
        )
        findings.extend(entry_findings)
    subdomain: dict[str, Any] | None = None
    if value["subdomain"] is not None:
        subdomain, entry_findings = _normalize_classification_entry(
            value["subdomain"],
            path="worker.classification.subdomain",
            subdomain=True,
        )
        findings.extend(entry_findings)

    tags_value = value["tags"]
    tags: list[dict[str, Any]] = []
    if not isinstance(tags_value, list):
        findings.append(
            _classification_finding("worker.classification.tags", "expected array")
        )
    elif len(tags_value) > 3:
        findings.append(
            _classification_finding(
                "worker.classification.tags", "at most three tags are allowed"
            )
        )
    else:
        for index, tag_value in enumerate(tags_value):
            tag, entry_findings = _normalize_classification_entry(
                tag_value,
                path=f"worker.classification.tags[{index}]",
                subdomain=False,
            )
            findings.extend(entry_findings)
            if tag is not None:
                tags.append(tag)
        tag_keys = [
            (
                tag["id"],
                tag["label"],
                tuple(tag["aliases"]),
            )
            for tag in tags
        ]
        if len(set(tag_keys)) != len(tag_keys):
            findings.append(
                _classification_finding(
                    "worker.classification.tags", "tags must be unique"
                )
            )

    candidate_value = value["candidate_terms"]
    candidate_terms: list[str] = []
    if not isinstance(candidate_value, list):
        findings.append(
            _classification_finding(
                "worker.classification.candidate_terms", "expected array"
            )
        )
    else:
        for index, term in enumerate(candidate_value):
            if not isinstance(term, str) or not term.strip():
                findings.append(
                    _classification_finding(
                        f"worker.classification.candidate_terms[{index}]",
                        "expected nonblank text",
                    )
                )
                continue
            candidate_terms.append(term.strip())
        if len(set(candidate_terms)) != len(candidate_terms):
            findings.append(
                _classification_finding(
                    "worker.classification.candidate_terms",
                    "candidate terms must be unique",
                )
            )
    if findings:
        return None, _normalize_findings(findings)
    return {
        "domain": domain,
        "subdomain": subdomain,
        "tags": tags,
        "candidate_terms": candidate_terms,
    }, []


_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _classification_token(value: str) -> str:
    return value.strip().translate(_ASCII_LOWER)


def _record_tokens(record: Mapping[str, Any]) -> set[str]:
    return {
        _classification_token(value)
        for value in [
            str(record["id"]),
            str(record["label"]),
            *(str(alias) for alias in record["aliases"]),
        ]
        if value.strip()
    }


def _proposal_tokens(proposal: Mapping[str, Any]) -> set[str]:
    return {
        _classification_token(value)
        for value in [
            str(proposal["id"]),
            str(proposal["label"]),
            *(str(alias) for alias in proposal["aliases"]),
        ]
        if value.strip()
    }


def _new_vocab_row(
    proposal: Mapping[str, Any],
    *,
    row_type: str,
    parent: str,
) -> list[str]:
    return [
        str(proposal["id"]),
        row_type,
        _encode_vocab_scalar(str(proposal["label"])),
        parent,
        _encode_registry_list([str(alias) for alias in proposal["aliases"]]),
        "active",
        "",
    ]


def _resolve_vocab_entry(
    records: list[dict[str, Any]],
    proposal: Mapping[str, Any],
    *,
    row_type: str,
    parent: str,
    appended: list[list[str]],
) -> str | None:
    tokens = _proposal_tokens(proposal)
    matches = [record for record in records if tokens & _record_tokens(record)]
    if not matches:
        row = _new_vocab_row(proposal, row_type=row_type, parent=parent)
        appended.append(row)
        record = {
            "id": proposal["id"],
            "type": row_type,
            "label": proposal["label"],
            "parent": parent,
            "aliases": list(proposal["aliases"]),
            "status": "active",
            "raw": _row_dict(VOCAB_HEADER, row),
        }
        records.append(record)
        return str(proposal["id"])
    if len(matches) != 1:
        return None
    match = matches[0]
    if match["type"] == "source-kind" or match["type"] != row_type:
        return None
    if row_type == "subdomain" and match["parent"] != parent:
        return None
    return str(match["id"])


def resolve_source_classification(
    vocab_text: str,
    classification: Any,
) -> tuple[str, dict[str, Any] | None, list[Finding]]:
    """Resolve one classification against VOCAB and append only unseen legal rows."""
    normalized, findings = normalize_source_classification(classification)
    if findings:
        return vocab_text, None, findings
    if normalized is None:
        return vocab_text, None, []
    table, records, vocab_findings = _validated_vocab(vocab_text)
    if vocab_findings:
        return vocab_text, None, vocab_findings

    candidate_terms: list[str] = []
    candidate_keys: set[str] = set()

    def add_candidate(value: str) -> None:
        term = value.strip()
        key = _classification_token(term)
        if term and key not in candidate_keys:
            candidate_keys.add(key)
            candidate_terms.append(term)

    for term in normalized["candidate_terms"]:
        add_candidate(str(term))

    appended: list[list[str]] = []
    domain_proposal = normalized["domain"]
    domain_id: str | None = None
    if domain_proposal is not None:
        domain_id = _resolve_vocab_entry(
            records,
            domain_proposal,
            row_type="domain",
            parent="",
            appended=appended,
        )
        if domain_id is None:
            add_candidate(str(domain_proposal["label"]))

    subdomain_id: str | None = None
    subdomain_proposal = normalized["subdomain"]
    if subdomain_proposal is not None:
        parent_matches = (
            domain_proposal is not None
            and domain_id is not None
            and _classification_token(str(subdomain_proposal["parent"]))
            in {
                _classification_token(str(domain_proposal["id"])),
                _classification_token(domain_id),
            }
        )
        if parent_matches and domain_id is not None:
            subdomain_id = _resolve_vocab_entry(
                records,
                subdomain_proposal,
                row_type="subdomain",
                parent=domain_id,
                appended=appended,
            )
        if subdomain_id is None:
            add_candidate(str(subdomain_proposal["label"]))

    tag_ids: list[str] = []
    for tag in normalized["tags"]:
        tag_id = _resolve_vocab_entry(
            records, tag, row_type="tag", parent="", appended=appended
        )
        if tag_id is None:
            add_candidate(str(tag["label"]))
        elif tag_id not in tag_ids:
            tag_ids.append(tag_id)

    candidate_vocab = _append_rows(table, appended)
    post_findings = validate_vocab(candidate_vocab)
    if post_findings:
        return vocab_text, None, post_findings
    return (
        candidate_vocab,
        {
            "primary_domain": domain_id or "",
            "subdomains": [subdomain_id] if subdomain_id is not None else [],
            "canonical_tags": tag_ids,
            "candidate_terms": candidate_terms,
        },
        [],
    )


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
    try:
        if DATE_RE.fullmatch(first_seen) is None:
            raise ValueError
        date.fromisoformat(first_seen)
    except (TypeError, ValueError):
        return _event_error("EVENT_ARTIFACT_PATH_DATE_MISMATCH", value)
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
        rf"^{re.escape(first_seen)}--{re.escape(source_id)}--"
        r"[a-z0-9_](?:[a-z0-9._-]*[a-z0-9_])?\.md$"
    )
    if expected.fullmatch(filename) is None:
        return _event_error("EVENT_ARTIFACT_PATH_INVALID", value)
    return []


def source_artifact_path_is_canonical(
    value: Any,
    source_id: str,
    first_seen: str,
) -> bool:
    """Return whether a persisted source path has the canonical new-artifact shape."""
    return not _validate_source_artifact_path(
        value,
        source_id,
        first_seen,
        is_new=True,
    )


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


class TopicInspectionError(ValueError):
    """One topic cannot be inspected without returning partial context."""

    def __init__(self, code: str, path: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.path = path
        self.detail = detail


@dataclass(frozen=True)
class TopicSelection:
    state: str
    topic: dict[str, Any] | None
    relations: tuple[dict[str, Any], ...]
    artifact_paths: tuple[str, ...]
    pending_edges: tuple[dict[str, Any], ...]
    findings: tuple[Finding, ...]

    def paths_for(self, purpose: str) -> tuple[str, ...]:
        """Return the stable bounded artifact set for one inspection purpose."""
        if purpose not in INSPECTION_PURPOSES:
            raise TopicInspectionError(
                "TOPIC_INSPECTION_INPUT_INVALID",
                "args.purpose",
                "purpose must be answer, research, or refresh",
            )
        if self.topic is None:
            return ()
        paths = [self.topic["topic_path"]]
        if purpose == "research":
            paths.append(_subdomain_path(self.topic))
            statuses = {"applied"}
        elif purpose == "refresh":
            statuses = {"pending"}
        else:
            statuses = set()
        paths.extend(
            relation["source_artifact"]
            for relation in self.relations
            if relation["status"] in statuses
        )
        return tuple(dict.fromkeys(paths))

    def require_locked_match(self, locked: TopicSelection) -> None:
        """Reject any candidate-to-lock topic selection drift."""
        if self != locked:
            raise TopicInspectionError(
                "TOPIC_INSPECTION_UNAVAILABLE",
                TOPICS_PATH,
                "locked topic selection differs from candidate selection",
            )


def select_topic_state(documents: Mapping[str, Any], topic_id: str) -> TopicSelection:
    """Classify one topic from canonical registries without partial context."""
    if not isinstance(topic_id, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]*", topic_id
    ):
        return TopicSelection(
            "invalid",
            None,
            (),
            (),
            (),
            (
                Finding(
                    "TOPIC_SELECTION_INPUT_INVALID",
                    "args.topic_id",
                    detail="topic_id must be a normalized Atlas ID",
                ),
            ),
        )
    try:
        texts = _documents_text(documents)
        parsed = _parse_documents({name: texts[name] for name in HEADERS})
    except (TypeError, ValueError, UnicodeError) as exc:
        return TopicSelection(
            "invalid",
            None,
            (),
            (),
            (),
            (Finding("TOPIC_SELECTION_INVALID", "documents", detail=str(exc)),),
        )
    findings = tuple(
        validate_documents(
            texts["manifest"],
            texts["topics"],
            texts["relations"],
            vocab_text=texts.get("vocab"),
        )
    )
    if findings:
        return TopicSelection("invalid", None, (), (), (), findings)

    topic_rows = _mutable_rows(parsed["topics"], TOPICS_HEADER)
    matches = [row for row in topic_rows if row["Topic ID"] == topic_id]
    if not matches or matches[0]["Freshness state"] == "archived":
        return TopicSelection("absent", None, (), (), (), ())

    relation_rows = sorted(
        (
            row
            for row in _mutable_rows(parsed["relations"], RELATIONS_HEADER)
            if row["Topic ID"] == topic_id
        ),
        key=lambda row: (int(row["Source seq"]), row["Edge ID"]),
    )
    topic = _typed_topic(matches[0])
    relations = tuple(_typed_relation(row) for row in relation_rows)
    artifact_paths = tuple(
        dict.fromkeys(relation["source_artifact"] for relation in relations)
    )
    pending_edges = tuple(
        relation for relation in relations if relation["status"] == "pending"
    )
    return TopicSelection(
        topic["freshness_state"],
        topic,
        relations,
        artifact_paths,
        pending_edges,
        (),
    )


class SourceCandidateError(ValueError):
    """A topic-scoped source candidate snapshot is invalid or incomplete."""

    def __init__(self, code: str, path: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.path = path
        self.detail = detail


@dataclass(frozen=True)
class SourceCandidateScope:
    state: str
    topic: dict[str, Any] | None
    sources: tuple[dict[str, Any], ...]
    gaps: tuple[dict[str, Any], ...]
    suppressed: tuple[dict[str, Any], ...]
    requested_source_id: str | None
    findings: tuple[Finding, ...]

    @property
    def artifact_paths(self) -> tuple[str, ...]:
        return tuple(source["artifact"] for source in self.sources)

    def require_locked_match(self, locked: SourceCandidateScope) -> None:
        if self != locked:
            raise SourceCandidateError(
                "SOURCE_CANDIDATE_SNAPSHOT_DRIFT",
                "snapshot",
                "locked candidate scope differs from preliminary selection",
            )


def _pending_route_base(
    relations: Sequence[Mapping[str, str]],
    source_id: str,
    content_hash: str,
) -> list[dict[str, str]]:
    pending = sorted(
        (
            row
            for row in relations
            if row["Source ID"] == source_id
            and row["Source content hash"] == content_hash
            and row["Status"] == "pending"
        ),
        key=lambda row: row["Topic ID"],
    )
    return [
        {
            "topic_id": row["Topic ID"],
            "relation": row["Relation"],
            "impact": row["Impact"],
            "confidence": row["Confidence"],
            "reason": _registry_decode_scalar(row["Notes"]),
        }
        for row in pending
    ]


def select_source_candidate_scope(
    documents: Mapping[str, Any],
    topic_id: str,
    named_urls: Sequence[str],
    *,
    source_id: str | None = None,
) -> SourceCandidateScope:
    """Select the bounded active-source path set for one topic snapshot."""
    if (
        not isinstance(topic_id, str)
        or VOCAB_ID_RE.fullmatch(topic_id) is None
        or isinstance(named_urls, (str, bytes))
        or not isinstance(named_urls, Sequence)
        or any(not isinstance(value, str) for value in named_urls)
        or (
            source_id is not None
            and (
                not isinstance(source_id, str)
                or SOURCE_ID_RE.fullmatch(source_id) is None
            )
        )
    ):
        return SourceCandidateScope(
            "invalid",
            None,
            (),
            (),
            (),
            source_id,
            (
                Finding(
                    "SOURCE_CANDIDATE_INPUT_INVALID",
                    "args",
                    detail="topic, named URL, or source identity is invalid",
                ),
            ),
        )
    try:
        texts = _documents_text(documents)
    except (TypeError, ValueError, UnicodeError) as exc:
        return SourceCandidateScope(
            "invalid",
            None,
            (),
            (),
            (),
            source_id,
            (Finding("SOURCE_CANDIDATE_STATE_INVALID", "documents", detail=str(exc)),),
        )
    if "vocab" not in texts:
        return SourceCandidateScope(
            "invalid",
            None,
            (),
            (),
            (),
            source_id,
            (
                Finding(
                    "VOCAB_DOCUMENT_REQUIRED",
                    VOCAB_PATH,
                    detail="candidate discovery requires VOCAB",
                ),
            ),
        )
    findings = validate_documents(
        texts["manifest"],
        texts["topics"],
        texts["relations"],
        vocab_text=texts["vocab"],
    )
    if findings:
        return SourceCandidateScope(
            "invalid", None, (), (), (), source_id, tuple(findings)
        )
    parsed = _parse_documents({name: texts[name] for name in HEADERS})
    topic_rows = _mutable_rows(parsed["topics"], TOPICS_HEADER)
    topic_row = next(
        (
            row
            for row in topic_rows
            if row["Topic ID"] == topic_id and row["Freshness state"] != "archived"
        ),
        None,
    )
    if topic_row is None:
        return SourceCandidateScope("absent", None, (), (), (), source_id, ())

    manifest_rows = _mutable_rows(parsed["manifest"], MANIFEST_HEADER)
    relation_rows = _mutable_rows(parsed["relations"], RELATIONS_HEADER)
    by_url = {row["Canonical URL"]: row for row in manifest_rows}
    named_set = set(named_urls)
    gaps: list[dict[str, Any]] = []
    for canonical_url in named_urls:
        row = by_url.get(canonical_url)
        if row is None:
            gaps.append(
                {
                    "canonical_url": canonical_url,
                    "source_id": None,
                    "reason": "missing",
                }
            )
        elif row["Status"] != "active":
            gaps.append(
                {
                    "canonical_url": canonical_url,
                    "source_id": row["Source ID"],
                    "reason": "inactive",
                }
            )

    sources: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    for row in sorted(manifest_rows, key=lambda item: int(item["Source seq"])):
        if row["Status"] != "active":
            continue
        if source_id is not None and row["Source ID"] != source_id:
            continue
        already_related = any(
            relation["Source ID"] == row["Source ID"]
            and relation["Source content hash"] == row["Content hash"]
            and relation["Topic ID"] == topic_id
            for relation in relation_rows
        )
        if already_related:
            suppressed.append(
                {
                    "source_id": row["Source ID"],
                    "reason": "already-related-current-hash",
                }
            )
            continue
        sources.append(
            {
                "source_seq": int(row["Source seq"]),
                "source_id": row["Source ID"],
                "canonical_url": row["Canonical URL"],
                "artifact": row["Artifact"],
                "content_hash": row["Content hash"],
                "named": row["Canonical URL"] in named_set,
                "pending_edges": _pending_route_base(
                    relation_rows, row["Source ID"], row["Content hash"]
                ),
            }
        )
    return SourceCandidateScope(
        "ready",
        _typed_topic(topic_row),
        tuple(sources),
        tuple(gaps),
        tuple(suppressed),
        source_id,
        (),
    )


def _phrase_tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return tuple(
        part
        for part in "".join(
            char if char.isalnum() else " " for char in normalized
        ).split()
        if part
    )


def _contains_phrase(haystack: str, needle: str) -> bool:
    haystack_tokens = _phrase_tokens(haystack)
    needle_tokens = _phrase_tokens(needle)
    if not needle_tokens or len(needle_tokens) > len(haystack_tokens):
        return False
    width = len(needle_tokens)
    return any(
        haystack_tokens[index : index + width] == needle_tokens
        for index in range(len(haystack_tokens) - width + 1)
    )


def _candidate_match_facts(
    topic: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> tuple[list[str], list[str]]:
    positive: list[str] = []
    source_domains = {
        projection["primary_domain"],
        *projection["secondary_domains"],
    }
    if topic["domain"] in source_domains:
        positive.append(f"domain:{topic['domain']}")
    if topic["subdomain"] in projection["subdomains"]:
        positive.append(f"subdomain:{topic['subdomain']}")
    source_tags = set(projection["canonical_tags"])
    for tag in topic["canonical_tags"]:
        if tag in source_tags:
            positive.append(f"canonical-tag:{tag}")
    text_fields = (
        projection["title"],
        projection["tldr"],
        projection["key_points"],
    )
    for kind, phrases in (
        ("alias", topic["aliases"]),
        ("include", topic["include_terms"]),
    ):
        for phrase in phrases:
            if any(_contains_phrase(text, phrase) for text in text_fields):
                positive.append(f"{kind}:{phrase}")
    excluded = [
        f"exclude:{phrase}"
        for phrase in topic["exclude_terms"]
        if any(_contains_phrase(text, phrase) for text in text_fields)
    ]
    return positive, excluded


def validate_source_taxonomy(
    vocab_text: str,
    *,
    primary_domain: str,
    secondary_domains: Sequence[str],
    subdomains: Sequence[str],
    canonical_tags: Sequence[str],
    path: str,
) -> list[Finding]:
    """Validate one source artifact's canonical vocabulary bindings."""
    _, records, findings = _validated_vocab(vocab_text)
    if findings:
        return findings
    by_id = {str(record["id"]): record for record in records}
    bindings: list[tuple[str, str]] = []
    if primary_domain:
        bindings.append((primary_domain, "domain"))
    bindings.extend((value, "domain") for value in secondary_domains)
    bindings.extend((value, "subdomain") for value in subdomains)
    bindings.extend((value, "tag") for value in canonical_tags)
    result: list[Finding] = []
    for row_id, expected_type in bindings:
        record = by_id.get(row_id)
        if record is None or record["type"] != expected_type:
            result.append(
                Finding(
                    "SOURCE_TAXONOMY_INVALID",
                    path,
                    row=row_id,
                    detail=f"expected {expected_type} vocabulary ID",
                )
            )
    return _normalize_findings(result)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def build_source_candidates(
    scope: SourceCandidateScope,
    projections: Mapping[str, Mapping[str, Any]],
    *,
    vocab_text: str,
    registry_revisions: Mapping[str, str],
) -> dict[str, Any]:
    """Match one locked source scope and return only bounded candidate packets."""
    if scope.state != "ready" or scope.topic is None:
        raise SourceCandidateError(
            "SOURCE_CANDIDATE_SCOPE_INVALID",
            "scope",
            "candidate scope is not ready",
        )
    if set(registry_revisions) != {"manifest", "topics", "relations", "vocab"} or any(
        not isinstance(value, str) or REVISION_RE.fullmatch(value) is None
        for value in registry_revisions.values()
    ):
        raise SourceCandidateError(
            "SOURCE_CANDIDATE_SNAPSHOT_INVALID",
            "registry_revisions",
            "registry revisions are invalid",
        )
    expected_projection_keys = {
        "revision",
        "source_id",
        "canonical_url",
        "content_hash",
        "title",
        "tldr",
        "key_points",
        "primary_domain",
        "secondary_domains",
        "subdomains",
        "canonical_tags",
    }
    topic_scope = {
        key: scope.topic[key]
        for key in (
            "topic_id",
            "domain",
            "subdomain",
            "canonical_title",
            "aliases",
            "canonical_tags",
            "include_terms",
            "exclude_terms",
        )
    }
    topic_scope_sha256 = _canonical_sha256(topic_scope)
    candidates: list[dict[str, Any]] = []
    pair_disposition = (
        "already-related"
        if scope.requested_source_id is not None
        and any(
            item["source_id"] == scope.requested_source_id for item in scope.suppressed
        )
        else "unavailable"
    )
    for source in scope.sources:
        path = source["artifact"]
        projection = projections.get(path)
        if (
            not isinstance(projection, Mapping)
            or set(projection) != expected_projection_keys
        ):
            raise SourceCandidateError(
                "SOURCE_CANDIDATE_ARTIFACT_INVALID",
                path,
                "candidate artifact projection is missing or malformed",
            )
        if (
            projection["source_id"] != source["source_id"]
            or projection["canonical_url"] != source["canonical_url"]
            or projection["content_hash"] != source["content_hash"]
            or not isinstance(projection["revision"], str)
            or REVISION_RE.fullmatch(projection["revision"]) is None
        ):
            raise SourceCandidateError(
                "SOURCE_CANDIDATE_ARTIFACT_DRIFT",
                path,
                "manifest and artifact identity or revision disagree",
            )
        string_fields = ("title", "tldr", "key_points", "primary_domain")
        list_fields = (
            "secondary_domains",
            "subdomains",
            "canonical_tags",
        )
        if any(not isinstance(projection[name], str) for name in string_fields) or any(
            not isinstance(projection[name], list)
            or any(not isinstance(value, str) for value in projection[name])
            for name in list_fields
        ):
            raise SourceCandidateError(
                "SOURCE_CANDIDATE_ARTIFACT_INVALID",
                path,
                "candidate artifact fields are invalid",
            )
        taxonomy_findings = validate_source_taxonomy(
            vocab_text,
            primary_domain=projection["primary_domain"],
            secondary_domains=projection["secondary_domains"],
            subdomains=projection["subdomains"],
            canonical_tags=projection["canonical_tags"],
            path=path,
        )
        if taxonomy_findings:
            first = taxonomy_findings[0]
            raise SourceCandidateError(
                first.code, first.path, first.detail or first.row or ""
            )
        positive_hits, exclude_hits = _candidate_match_facts(scope.topic, projection)
        eligible = source["named"] or (bool(positive_hits) and not exclude_hits)
        if not eligible:
            if scope.requested_source_id == source["source_id"]:
                pair_disposition = "not-candidate"
            continue
        expected_revisions = {
            "artifact": projection["revision"],
            "topics": registry_revisions["topics"],
            "relations": registry_revisions["relations"],
            "vocab": registry_revisions["vocab"],
        }
        source_projection = {
            "source_seq": source["source_seq"],
            "source_id": source["source_id"],
            "canonical_url": source["canonical_url"],
            "content_hash": source["content_hash"],
            "artifact": source["artifact"],
            "artifact_revision": projection["revision"],
            "pending_edges": source["pending_edges"],
        }
        match_facts = {
            "positive_hits": positive_hits,
            "exclude_hits": exclude_hits,
        }
        candidate_sha256 = _canonical_sha256(
            {
                "version": 1,
                "source_projection": source_projection,
                "topic_scope_sha256": topic_scope_sha256,
                "named": source["named"],
                "match_facts": match_facts,
            }
        )
        candidates.append(
            {
                **source_projection,
                "topic_id": scope.topic["topic_id"],
                "topic_scope_sha256": topic_scope_sha256,
                **match_facts,
                "named": source["named"],
                "glance": {
                    "title": projection["title"],
                    "summary": {
                        "tldr": projection["tldr"],
                        "key_points": projection["key_points"],
                    },
                    "classification": {
                        "primary_domain": projection["primary_domain"],
                        "secondary_domains": projection["secondary_domains"],
                        "subdomains": projection["subdomains"],
                        "canonical_tags": projection["canonical_tags"],
                    },
                },
                "expected_revisions": expected_revisions,
                "candidate_sha256": candidate_sha256,
            }
        )
        if scope.requested_source_id == source["source_id"]:
            pair_disposition = "candidate"
    return {
        "topic_id": scope.topic["topic_id"],
        "topic_scope_sha256": topic_scope_sha256,
        "registry_revisions": dict(registry_revisions),
        "candidates": candidates,
        "gaps": [dict(item) for item in scope.gaps],
        "suppressed": [dict(item) for item in scope.suppressed],
        "pair_disposition": (
            pair_disposition if scope.requested_source_id is not None else None
        ),
    }


def _inspection_source_relations(
    relations: Sequence[Mapping[str, Any]], purpose: str
) -> list[dict[str, Any]]:
    if purpose == "research":
        statuses = {"applied"}
    elif purpose == "refresh":
        statuses = {"pending"}
    else:
        statuses = set()
    return [dict(row) for row in relations if row["status"] in statuses]


def _subdomain_path(topic: Mapping[str, Any]) -> str:
    return f"summaries/research/{topic['domain']}/{topic['subdomain']}/INDEX.md"


def _inspection_artifact(artifacts: Mapping[str, Any], path: str) -> tuple[str, str]:
    value = artifacts.get(path)
    if not isinstance(value, Mapping) or set(value) != {"revision", "text"}:
        raise TopicInspectionError(
            "TOPIC_INSPECTION_UNAVAILABLE",
            path,
            "required artifact snapshot is unavailable",
        )
    revision = value.get("revision")
    text = value.get("text")
    if (
        not isinstance(revision, str)
        or REVISION_RE.fullmatch(revision) is None
        or not isinstance(text, str)
    ):
        raise TopicInspectionError(
            "TOPIC_INSPECTION_UNAVAILABLE",
            path,
            "required artifact snapshot is unavailable",
        )
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise TopicInspectionError(
            "TOPIC_INSPECTION_INVALID", path, "artifact is not valid UTF-8"
        ) from exc
    return revision, text


def _managed_sections(text: str, names: Sequence[str], path: str) -> dict[str, str]:
    lines = text.splitlines(keepends=True)
    expected = set(names)
    starts: dict[str, list[int]] = {name: [] for name in names}
    ends: dict[str, list[int]] = {name: [] for name in names}
    marker = re.compile(r"^<!-- atlas:managed:(start|end) ([a-z0-9-]+) -->$")
    for index, line in enumerate(lines):
        body = _body(line).strip()
        if not body.startswith("<!-- atlas:managed:"):
            continue
        match = marker.fullmatch(body)
        if match is None or match.group(2) not in expected:
            raise TopicInspectionError(
                "TOPIC_INSPECTION_INVALID",
                path,
                f"invalid managed marker on line {index + 1}",
            )
        target = starts if match.group(1) == "start" else ends
        target[match.group(2)].append(index)
    result: dict[str, str] = {}
    previous_end = -1
    for name in names:
        if len(starts[name]) != 1 or len(ends[name]) != 1:
            raise TopicInspectionError(
                "TOPIC_INSPECTION_INVALID",
                path,
                f"managed marker pair {name!r} must occur exactly once",
            )
        start, end = starts[name][0], ends[name][0]
        if end <= start or start <= previous_end:
            raise TopicInspectionError(
                "TOPIC_INSPECTION_INVALID",
                path,
                f"managed marker pair {name!r} is unordered",
            )
        result[name] = "".join(lines[start + 1 : end])
        previous_end = end
    return result


def _topic_frontmatter_scalar(text: str, key: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    prefix = f"{key}:"
    values = [
        line[len(prefix) :].strip() for line in lines[1:end] if line.startswith(prefix)
    ]
    if len(values) != 1:
        return None
    raw = values[0]
    if raw.startswith('"'):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, str) else None
    return raw


def validate_answer_authoring(
    current_index_text: str,
    candidate_index_text: str,
    relations: Sequence[Mapping[str, Any]],
    *,
    selected_edge_ids: Sequence[str] = (),
    path: str = "args.index_text",
) -> list[Finding]:
    """Validate evidence rank for answer-bearing topic output."""
    try:
        current = _managed_sections(current_index_text, TOPIC_MANAGED_SECTIONS, path)
        candidate = _managed_sections(
            candidate_index_text, TOPIC_MANAGED_SECTIONS, path
        )
    except TopicInspectionError as exc:
        return [Finding("ANSWER_AUTHORING_INDEX_INVALID", exc.path, detail=exc.detail)]

    selected = set(selected_edge_ids)
    eligible: set[str] = set()
    for relation in relations:
        artifact = relation.get("source_artifact")
        if not isinstance(artifact, str) or not artifact:
            continue
        status = relation.get("status")
        is_selected = status == "pending" and relation.get("edge_id") in selected
        if (
            relation.get("relation") == "direct"
            and relation.get("impact") in {"high", "medium"}
            and (status == "applied" or is_selected)
        ):
            eligible.add(artifact)

    findings: list[Finding] = []
    for section in ANSWER_AUTHORING_SECTIONS:
        content = candidate[section]
        references = {
            match.removeprefix("vault://atlas/")
            for match in SOURCE_ARTIFACT_REFERENCE_RE.findall(content)
        }
        ineligible = sorted(references - eligible)
        if ineligible:
            findings.append(
                Finding(
                    "ANSWER_EVIDENCE_INELIGIBLE",
                    path,
                    row=section,
                    detail=f"answer-bearing section cites ineligible artifact {ineligible[0]!r}",
                )
            )
        substantive = bool(content.strip()) and (
            section != "current-answer" or content.strip() != INITIAL_CURRENT_ANSWER
        )
        changed = content != current[section]
        if changed and not eligible:
            findings.append(
                Finding(
                    "ANSWER_EVIDENCE_REQUIRED",
                    path,
                    row=section,
                    detail="without direct high/medium evidence, answer-bearing sections must remain unchanged",
                )
            )
        elif changed and substantive and not (references & eligible):
            findings.append(
                Finding(
                    "ANSWER_EVIDENCE_REQUIRED",
                    path,
                    row=section,
                    detail="changed answer-bearing section requires direct high/medium evidence",
                )
            )

    coverage = _topic_frontmatter_scalar(candidate_index_text, "coverage_state")
    if coverage is None:
        findings.append(
            Finding(
                "ANSWER_AUTHORING_INDEX_INVALID",
                path,
                detail="topic coverage_state is missing or invalid",
            )
        )
    elif not eligible and coverage not in {"insufficient", "partial"}:
        findings.append(
            Finding(
                "ANSWER_COVERAGE_INELIGIBLE",
                path,
                detail=(
                    "without direct high/medium evidence, coverage_state "
                    "must be insufficient or partial"
                ),
            )
        )
    return _normalize_findings(findings)


def _typed_topic(row: Mapping[str, str]) -> dict[str, Any]:
    aliases, _ = _registry_list(row["Aliases"])
    tags, _ = _registry_list(row["Canonical tags"])
    include_terms, _ = _registry_list(row["Include terms"])
    exclude_terms, _ = _registry_list(row["Exclude terms"])
    return {
        "topic_id": row["Topic ID"],
        "topic_path": row["Topic path"],
        "domain": row["Domain"],
        "subdomain": row["Subdomain"],
        "canonical_title": _registry_decode_scalar(row["Canonical title"]),
        "aliases": aliases or [],
        "canonical_tags": tags or [],
        "include_terms": include_terms or [],
        "exclude_terms": exclude_terms or [],
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
        "last_synthesized": row["Last synthesized"] or None,
        "source_watermark": int(row["Source watermark"]),
        "refresh_model": row["Refresh model"],
    }


def _typed_relation(row: Mapping[str, str]) -> dict[str, Any]:
    return {
        "edge_id": row["Edge ID"],
        "source_seq": int(row["Source seq"]),
        "source_id": row["Source ID"],
        "source_artifact": row["Source artifact"],
        "source_content_hash": row["Source content hash"],
        "topic_id": row["Topic ID"],
        "relation": row["Relation"],
        "impact": row["Impact"],
        "confidence": row["Confidence"],
        "status": row["Status"],
        "created": row["Created"],
        "applied_in_pass": row["Applied in pass"] or None,
        "notes": _registry_decode_scalar(row["Notes"]),
    }


def _source_record(
    relation: Mapping[str, Any],
    manifest_by_id: Mapping[str, Mapping[str, str]],
    artifacts: Mapping[str, Any],
) -> dict[str, Any]:
    manifest = manifest_by_id[relation["source_id"]]
    revision, text = _inspection_artifact(artifacts, relation["source_artifact"])
    return {
        "source_id": relation["source_id"],
        "source_seq": relation["source_seq"],
        "canonical_url": manifest["Canonical URL"],
        "artifact_path": relation["source_artifact"],
        "artifact_revision": revision,
        "content_hash": relation["source_content_hash"],
        "relation": relation["relation"],
        "impact": relation["impact"],
        "confidence": relation["confidence"],
        "answer_authoring_eligible": (
            relation["relation"] == "direct"
            and relation["impact"] in {"high", "medium"}
            and relation["status"] in {"applied", "pending"}
        ),
        "text": text,
    }


def _inspection_revisions(
    registry_revisions: Mapping[str, Any],
    artifact_revisions: Mapping[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    if set(registry_revisions) != set(HEADERS):
        raise TopicInspectionError(
            "TOPIC_INSPECTION_UNAVAILABLE",
            "registry_revisions",
            "complete registry revision bindings are required",
        )
    registries: dict[str, str] = {}
    for name, path in PATHS.items():
        revision = registry_revisions[name]
        if not isinstance(revision, str) or REVISION_RE.fullmatch(revision) is None:
            raise TopicInspectionError(
                "TOPIC_INSPECTION_UNAVAILABLE",
                path,
                "registry revision binding is invalid",
            )
        registries[f"vault://atlas/{path}"] = revision
    used_artifacts = {
        f"vault://atlas/{path}": revision
        for path, revision in artifact_revisions.items()
    }
    return (
        dict(sorted(registries.items())),
        dict(sorted(used_artifacts.items())),
    )


def inspect_topic(
    documents: Mapping[str, Any],
    artifacts: Mapping[str, Any],
    topic_id: str,
    purpose: str,
    revisions: Mapping[str, Any],
) -> dict[str, Any]:
    """Return one bounded, revision-bound topic context without partial state."""
    if purpose not in INSPECTION_PURPOSES:
        raise TopicInspectionError(
            "TOPIC_INSPECTION_INPUT_INVALID",
            "args.purpose",
            "purpose must be answer, research, or refresh",
        )
    selection = select_topic_state(documents, topic_id)
    if selection.state == "absent":
        raise TopicInspectionError(
            "TOPIC_INSPECTION_ABSENT",
            TOPICS_PATH,
            "topic is not present or is archived",
        )
    if selection.state == "invalid":
        finding = selection.findings[0]
        code = (
            "TOPIC_INSPECTION_INPUT_INVALID"
            if finding.code == "TOPIC_SELECTION_INPUT_INVALID"
            else "TOPIC_INSPECTION_INVALID"
        )
        raise TopicInspectionError(
            code,
            finding.path,
            f"{finding.code}: {finding.detail or 'registry state is invalid'}",
        )
    assert selection.topic is not None
    topic = selection.topic
    required_paths = selection.paths_for(purpose)
    if set(artifacts) != set(required_paths):
        raise TopicInspectionError(
            "TOPIC_INSPECTION_UNAVAILABLE",
            "artifacts",
            "locked artifact set differs from the selected topic snapshot",
        )
    artifact_revisions: dict[str, str] = {}
    artifact_texts: dict[str, str] = {}
    for path in required_paths:
        revision, text = _inspection_artifact(artifacts, path)
        artifact_revisions[path] = revision
        artifact_texts[path] = text

    topic_sections = _managed_sections(
        artifact_texts[topic["topic_path"]],
        TOPIC_MANAGED_SECTIONS,
        topic["topic_path"],
    )
    freshness = {
        key: topic[key]
        for key in (
            "freshness_state",
            "dirty_count",
            "pending_edge_ids",
            "newest_pending_source_seq",
            "last_synthesized",
            "source_watermark",
            "refresh_model",
        )
    }
    manifest_rows, manifest_findings = validated_manifest_rows(
        _documents_text(documents)["manifest"]
    )
    if manifest_findings:
        finding = manifest_findings[0]
        raise TopicInspectionError(
            "TOPIC_INSPECTION_INVALID",
            finding.path,
            f"{finding.code}: {finding.detail or 'registry state is invalid'}",
        )
    manifest_by_id = {row["Source ID"]: row for row in manifest_rows}
    source_relations = _inspection_source_relations(selection.relations, purpose)
    source_records = [
        _source_record(relation, manifest_by_id, artifacts)
        for relation in source_relations
    ]
    if purpose == "answer":
        payload: dict[str, Any] = {
            "managed_sections": topic_sections,
            "freshness": freshness,
        }
    elif purpose == "research":
        subdomain_path = _subdomain_path(topic)
        _managed_sections(
            artifact_texts[subdomain_path],
            SUBDOMAIN_MANAGED_SECTIONS,
            subdomain_path,
        )
        payload = {
            "managed_sections": topic_sections,
            "subdomain_index": {
                "path": subdomain_path,
                "text": artifact_texts[subdomain_path],
            },
            "source_summaries": source_records,
        }
    else:
        source_by_path = {record["artifact_path"]: record for record in source_records}
        payload = {
            "managed_sections": topic_sections,
            "pending_edges": [
                {
                    "relation": relation,
                    "source_summary": source_by_path[relation["source_artifact"]],
                }
                for relation in source_relations
            ],
            "current_pass": {
                "last_synthesized": topic["last_synthesized"],
                "applied_in_passes": sorted(
                    {
                        relation["applied_in_pass"]
                        for relation in selection.relations
                        if relation["applied_in_pass"]
                    }
                ),
            },
        }

    registry_bindings, artifact_bindings = _inspection_revisions(
        revisions, artifact_revisions
    )
    pending_edge_ids = list(topic["pending_edge_ids"])
    preimage = {
        "topic_id": topic_id,
        "purpose": purpose,
        "registry_revisions": registry_bindings,
        "artifact_revisions": artifact_bindings,
        "pending_edge_ids": pending_edge_ids,
    }
    canonical = (
        json.dumps(
            preimage,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return {
        "version": VERSION,
        "topic_id": topic_id,
        "purpose": purpose,
        "freshness": freshness,
        "topic": topic,
        "relations": list(selection.relations),
        "registry_revisions": registry_bindings,
        "artifact_revisions": artifact_bindings,
        "pending_edge_ids": pending_edge_ids,
        "payload": payload,
        "inspection_sha256": hashlib.sha256(canonical).hexdigest(),
    }


@dataclass(frozen=True)
class TopicsListCandidateResult:
    state: str
    preimage_revision: str | None = None
    output_revision: str | None = None
    preimage_text: str | None = None
    text: str | None = None
    changes: tuple[dict[str, Any], ...] = ()
    findings: tuple[Finding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"state": self.state}
        if self.state == "candidate":
            result.update(
                {
                    "preimage_revision": self.preimage_revision,
                    "output_revision": self.output_revision,
                    "preimage_text": self.preimage_text,
                    "text": self.text,
                    "changes": [dict(change) for change in self.changes],
                }
            )
        if self.findings:
            result["findings"] = [finding.to_dict() for finding in self.findings]
        return result


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

    parsed = _parse_documents({name: texts[name] for name in HEADERS})
    input_findings = validate_documents(
        texts["manifest"],
        texts["topics"],
        texts["relations"],
        vocab_text=texts.get("vocab"),
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
            candidate["manifest"],
            candidate["topics"],
            candidate["relations"],
            vocab_text=candidate.get("vocab"),
        )
        if candidate_findings:
            return _failed(texts, candidate_findings)
        candidate_parsed = _parse_documents({name: candidate[name] for name in HEADERS})
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
    vocab_replacement: str | None = None

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
                    "classification",
                },
            )
        )
        source_id = event.get("source_id")
        canonical_url = event.get("canonical_url")
        artifact = event.get("artifact")
        content_hash = event.get("content_hash")
        classification = event.get("classification")
        if classification is not None:
            _, classification_findings = normalize_source_classification(classification)
            event_findings.extend(classification_findings)
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
        classification_derived: dict[str, Any] | None = None
        if content_changed and event.get("classification") is not None:
            vocab_text = texts.get("vocab")
            if vocab_text is None:
                return _failed(
                    texts,
                    _event_error(
                        "VOCAB_DOCUMENT_REQUIRED",
                        "source classification requires the vocabulary document",
                    ),
                )
            resolved_vocab, classification_derived, classification_findings = (
                resolve_source_classification(vocab_text, event["classification"])
            )
            if classification_findings:
                return _failed(texts, classification_findings)
            if resolved_vocab != vocab_text:
                vocab_replacement = resolved_vocab
                changed.add("vocab")
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
        if classification_derived is not None:
            source_derived["classification"] = classification_derived

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
            event_findings.extend(_event_error("EVENT_SOURCE_ARCHIVED", str(source_id)))
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
            and isinstance(source_id, str)
            and isinstance(content_hash, str)
            and isinstance(checked_on, str)
        )
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

    elif event_type == "research-complete":
        event_findings.extend(
            _require_event(
                event,
                {
                    "type",
                    "topic_id",
                    "inspection_sha256",
                    "pass_path",
                    "pass_sha256",
                    "topic_index_sha256",
                    "subdomain_index_sha256",
                    "completed_on",
                },
            )
        )
        topic_id = event.get("topic_id")
        topic = (
            _topic_row(topic_rows, str(topic_id)) if isinstance(topic_id, str) else None
        )
        if topic is None:
            event_findings.extend(_event_error("EVENT_TOPIC_UNKNOWN", str(topic_id)))
        elif topic["Freshness state"] != "current":
            event_findings.extend(
                _event_error("RESEARCH_TOPIC_NOT_CURRENT", topic["Freshness state"])
            )
        pending = _pending_for_topic(relation_rows, str(topic_id))
        if pending:
            event_findings.extend(
                _event_error(
                    "RESEARCH_PENDING_EDGES",
                    repr([row["Edge ID"] for row in pending]),
                )
            )
        for field_name in (
            "inspection_sha256",
            "pass_sha256",
            "topic_index_sha256",
            "subdomain_index_sha256",
        ):
            value = event.get(field_name)
            if not isinstance(value, str) or CONTENT_HASH_RE.fullmatch(value) is None:
                event_findings.extend(
                    _event_error("EVENT_HASH_INVALID", f"{field_name}={value!r}")
                )
        completed_on = event.get("completed_on")
        parsed_completed, date_findings = _parse_event_date(
            completed_on, "completed_on"
        )
        event_findings.extend(date_findings)
        pass_path = event.get("pass_path")
        if topic is not None and isinstance(pass_path, str):
            topic_directory = topic["Topic path"].removesuffix("/INDEX.md")
            pass_match = re.fullmatch(
                re.escape(topic_directory)
                + r"/passes/(\d{4}-\d{2}-\d{2})--[a-z0-9][a-z0-9-]*\.md",
                pass_path,
            )
            if (
                pass_match is None
                or parsed_completed is None
                or pass_match.group(1) != str(completed_on)
            ):
                event_findings.extend(
                    _event_error("EVENT_PASS_PATH_INVALID", str(pass_path))
                )
        else:
            event_findings.extend(
                _event_error("EVENT_PASS_PATH_INVALID", str(pass_path))
            )
        if event_findings:
            return _failed(texts, event_findings)
        assert topic is not None
        if topic["Last synthesized"] != completed_on:
            topic["Last synthesized"] = str(completed_on)
            changed.add("topics")

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
            reason = repair.get("reason")
            event_findings.extend(
                _validate_reason(
                    reason,
                    target["Relation"],
                    target["Impact"],
                    str(edge_id),
                )
            )
            if isinstance(reason, str):
                normalized.append((target, reason))
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
    if "vocab" in changed:
        assert vocab_replacement is not None
        replacements["vocab"] = vocab_replacement
    candidate = dict(texts)
    candidate.update(replacements)
    candidate_findings = validate_documents(
        candidate["manifest"],
        candidate["topics"],
        candidate["relations"],
        vocab_text=candidate.get("vocab"),
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
    for name, relative in TABLE_PATHS.items():
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
    return validate_documents(
        texts["manifest"],
        texts["topics"],
        texts["relations"],
        vocab_text=texts["vocab"],
    )
