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
from typing import Any, Iterable, Literal, Mapping, Sequence

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
    "Source routing SHA-256",
    "Refresh after",
    "Route status",
    "Status",
)
SOURCE_TAXONOMY_REMEDIATION_MANIFEST_HEADER = (
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
    "Routing scope SHA-256",
    "Freshness state",
    "Dirty count",
    "Pending edge IDs",
    "Newest pending source seq",
    "Last synthesized",
    "Source watermark",
    "Refresh model",
)
SOURCE_TOPIC_ROUTING_LEGACY_TOPICS_HEADER = (
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
    "Generation",
    "Source seq",
    "Source ID",
    "Source artifact",
    "Source content hash",
    "Source routing SHA-256",
    "Topic ID",
    "Topic scope SHA-256",
    "Work kind",
    "Prior edge ID",
    "Relation",
    "Impact",
    "Confidence",
    "Status",
    "Created",
    "Applied in pass",
    "Refresh disposition",
    "Notes",
)
SOURCE_TOPIC_ROUTING_LEGACY_RELATIONS_HEADER = (
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
TABLE_HEADERS = {
    **HEADERS,
    "vocab": VOCAB_HEADER,
    "source-taxonomy-remediation-manifest": (
        SOURCE_TAXONOMY_REMEDIATION_MANIFEST_HEADER
    ),
    "source-topic-routing-legacy-topics": (SOURCE_TOPIC_ROUTING_LEGACY_TOPICS_HEADER),
    "source-topic-routing-legacy-relations": (
        SOURCE_TOPIC_ROUTING_LEGACY_RELATIONS_HEADER
    ),
}
PATHS = {
    "manifest": MANIFEST_PATH,
    "topics": TOPICS_PATH,
    "relations": RELATIONS_PATH,
}
TABLE_PATHS = {
    **PATHS,
    "vocab": VOCAB_PATH,
    "source-taxonomy-remediation-manifest": MANIFEST_PATH,
    "source-topic-routing-legacy-topics": TOPICS_PATH,
    "source-topic-routing-legacy-relations": RELATIONS_PATH,
}

SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")
CONTENT_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SEMANTIC_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EDGE_ID_RE = re.compile(
    r"^edge--[0-9a-f]{12}--[a-z0-9][a-z0-9-]*--g[0-9]{8,}"
    r"--[0-9a-f]{8}--(?:[0-9a-f]{8}|legacy)--[0-9a-f]{8}$"
)
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
ROUTING_TERM_TYPES = {"domain", "subdomain", "tag", "topic"}
ROUTING_TERM_CONFIDENCES = {"high", "medium", "low"}
RELATION_STATUSES = {"pending", "applied", "rejected", "superseded"}
RELATION_WORK_KINDS = {
    "evidence",
    "source-change",
    "scope-change",
    "verifier-invalidation",
}
REFRESH_DISPOSITIONS = {"incorporated", "reviewed-no-change", "legacy"}
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


@dataclass(frozen=True)
class SourceTaxonomyRemediationTargetResult:
    source_id: str
    path: str
    changes: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "path": self.path,
            "changes": [dict(change) for change in self.changes],
        }


@dataclass(frozen=True)
class SourceTaxonomyRemediationCandidateResult:
    state: str
    targets: tuple[SourceTaxonomyRemediationTargetResult, ...] = ()
    findings: tuple[Finding, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"state": self.state}
        if self.state == "candidate":
            result["targets"] = [target.to_dict() for target in self.targets]
        if self.findings:
            result["findings"] = [finding.to_dict() for finding in self.findings]
        return result


@dataclass(frozen=True)
class _SourceTaxonomyRemediationSpec:
    source_id: str
    path: str
    primary_domain_change: tuple[str, str] | None
    subdomain_observations: tuple[tuple[int, str], ...]


_SOURCE_TAXONOMY_REMEDIATION_TARGETS = (
    _SourceTaxonomyRemediationSpec(
        "4991aefd6e2d",
        "summaries/sources/artifacts/2026/2026-07/2026-07-15--4991aefd6e2d--elia-mrkr-app-cloudflare-edge-analytics-architectu.md",
        ("Unknown", "web"),
        (),
    ),
    _SourceTaxonomyRemediationSpec(
        "a635aacf9534",
        "summaries/sources/artifacts/2026/2026-07/2026-07-15--a635aacf9534--tradingview-mcp.md",
        ("Unknown", "agent-systems"),
        (),
    ),
    _SourceTaxonomyRemediationSpec(
        "199d442d5281",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--199d442d5281--Bedrock-AgentCore-infrastructure.md",
        None,
        ((0, "agentic-harness-architecture"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "1f5bcd011229",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--1f5bcd011229--agent-harness-graph-engineering.md",
        None,
        ((0, "agentic-harness-architecture"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "6d302abbb73d",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--6d302abbb73d--OpenShip.md",
        ("agent-systems/harness", "agent-systems"),
        ((0, "agentic-harness-architecture"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "74ce3826133b",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--74ce3826133b--Next.js-page-speed.md",
        None,
        ((0, "ai-coding-workflow"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "9336444a8725",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--9336444a8725--state-of-agent-wikis.md",
        None,
        ((0, "agentic-harness-architecture"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "ab9804dff1da",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--ab9804dff1da--continual-learning-for-agents.md",
        ("agent-systems/harness", "agent-systems"),
        ((0, "lean-self-improving-agent-harness"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "c69cd3b0e6e6",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--c69cd3b0e6e6--agentic-autonomy-levels.md",
        None,
        (
            (0, "agentic-harness-architecture"),
            (1, "lean-self-improving-agent-harness"),
        ),
    ),
    _SourceTaxonomyRemediationSpec(
        "cfade8e4b07f",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--cfade8e4b07f--Durable-Objects-agents.md",
        None,
        ((0, "agentic-harness-architecture"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "db96a95a18e2",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--db96a95a18e2--self-improving-code-review-agent.md",
        ("agent-systems/harness", "agent-systems"),
        (
            (0, "agentic-harness-architecture"),
            (1, "ai-coding-workflow"),
        ),
    ),
    _SourceTaxonomyRemediationSpec(
        "e5b92aed7772",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--e5b92aed7772--context-engineering-rules-change.md",
        None,
        ((0, "agentic-harness-architecture"),),
    ),
    _SourceTaxonomyRemediationSpec(
        "ef463732cff6",
        "summaries/sources/artifacts/2026/2026-07/2026-07-30--ef463732cff6--software-factories.md",
        None,
        (
            (0, "agentic-harness-architecture"),
            (1, "lean-self-improving-agent-harness"),
        ),
    ),
)
_SOURCE_TAXONOMY_REMEDIATION_BY_PATH = {
    target.path: target for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS
}
_SOURCE_TAXONOMY_REMEDIATION_LEGACY_PRIMARY = {
    "Unknown",
    "agent-systems/harness",
}
_SOURCE_TAXONOMY_REMEDIATION_LEGACY_SUBDOMAINS = {
    "agentic-harness-architecture",
    "ai-coding-workflow",
    "lean-self-improving-agent-harness",
}
_SOURCE_PROJECTION_KEYS = {
    "revision",
    "source_id",
    "canonical_url",
    "content_hash",
    "title",
    "tldr",
    "key_points",
    "source_kind",
    "primary_domain",
    "secondary_domains",
    "subdomains",
    "canonical_tags",
}


def source_taxonomy_remediation_target_paths() -> tuple[str, ...]:
    """Return the reducer-owned exact migration target allowlist."""

    return tuple(target.path for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS)


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


def _edge_id(
    source_id: str,
    topic_id: str,
    generation: int,
    content_hash: str,
    source_routing_sha256: str,
    topic_scope_sha256: str,
) -> str:
    topic_key = re.sub(r"[/ .]+", "-", topic_id)
    routing_token = (
        "legacy"
        if source_routing_sha256 == "legacy-unavailable"
        else source_routing_sha256.removeprefix("sha256:")[:8]
    )
    return (
        f"edge--{source_id}--{topic_key}--g{generation:08d}"
        f"--{content_hash[:8]}--{routing_token}"
        f"--{topic_scope_sha256.removeprefix('sha256:')[:8]}"
    )


def _select_relation_frontier(
    relations: Sequence[Mapping[str, str]],
    *,
    source_id: str,
    topic_id: str,
    current_source_hash: str,
    current_routing_sha256: str,
    current_scope_sha256: str,
) -> tuple[Mapping[str, str] | None, int, list[Finding]]:
    """Return one validated predecessor-chain tip for a source-topic pair."""
    pair = [
        row
        for row in relations
        if row.get("Source ID") == source_id and row.get("Topic ID") == topic_id
    ]
    if not pair:
        return None, 0, []
    findings: list[Finding] = []
    by_id: dict[str, Mapping[str, str]] = {}
    generations: dict[int, str] = {}
    children: dict[str, list[Mapping[str, str]]] = {}
    active = [row for row in pair if row.get("Status") != "rejected"]
    for row in pair:
        edge_id = row.get("Edge ID", "")
        if edge_id in by_id:
            findings.append(
                Finding("RELATION_FRONTIER_COLLISION", RELATIONS_PATH, row=edge_id)
            )
        by_id[edge_id] = row
        try:
            generation = int(row.get("Generation", ""))
        except ValueError:
            findings.append(
                Finding("RELATION_GENERATION_INVALID", RELATIONS_PATH, row=edge_id)
            )
            continue
        if generation in generations:
            findings.append(
                Finding(
                    "RELATION_FRONTIER_GENERATION_REPEATED",
                    RELATIONS_PATH,
                    row=edge_id,
                )
            )
        generations[generation] = edge_id
        prior_id = row.get("Prior edge ID", "")
        if generation == 0:
            if prior_id:
                findings.append(
                    Finding(
                        "RELATION_FRONTIER_ROOT_INVALID",
                        RELATIONS_PATH,
                        row=edge_id,
                    )
                )
        else:
            prior = by_id.get(prior_id) or next(
                (item for item in pair if item.get("Edge ID") == prior_id), None
            )
            prior_generation = -1
            if prior is not None:
                try:
                    prior_generation = int(prior.get("Generation", ""))
                except ValueError:
                    prior_generation = generation
            if (
                prior is None
                or prior.get("Status") == "rejected"
                or prior_generation >= generation
            ):
                findings.append(
                    Finding(
                        "RELATION_FRONTIER_PREDECESSOR_INVALID",
                        RELATIONS_PATH,
                        row=edge_id,
                    )
                )
            else:
                children.setdefault(prior_id, []).append(row)
    for prior_id, successors in children.items():
        if len(successors) > 1:
            findings.append(
                Finding(
                    "RELATION_FRONTIER_FORK",
                    RELATIONS_PATH,
                    row=prior_id,
                )
            )
    tips = [row for row in active if row.get("Edge ID") not in children]
    if len(tips) != 1:
        findings.append(
            Finding(
                "RELATION_FRONTIER_AMBIGUOUS",
                RELATIONS_PATH,
                detail=f"expected one tip, found {len(tips)}",
            )
        )
        return None, max(generations, default=-1) + 1, _normalize_findings(findings)
    tip = tips[0]
    if (
        tip.get("Source content hash") != current_source_hash
        or tip.get("Source routing SHA-256") != current_routing_sha256
        or tip.get("Topic scope SHA-256") != current_scope_sha256
    ):
        findings.append(
            Finding(
                "RELATION_FRONTIER_STALE",
                RELATIONS_PATH,
                row=tip.get("Edge ID", ""),
            )
        )
    return (
        tip,
        max(generations, default=-1) + 1,
        _normalize_findings(findings),
    )


def _validate_manifest(
    table: ParsedTable,
    *,
    historical_source_taxonomy_remediation: bool = False,
) -> tuple[list[Finding], dict[str, dict[str, str]]]:
    findings: list[Finding] = []
    by_id: dict[str, dict[str, str]] = {}
    header = (
        SOURCE_TAXONOMY_REMEDIATION_MANIFEST_HEADER
        if historical_source_taxonomy_remediation
        else MANIFEST_HEADER
    )
    records = [_row_dict(header, row) for row in table.rows]
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
        if not historical_source_taxonomy_remediation:
            routing_digest = row["Source routing SHA-256"]
            if row["Status"] == "active":
                if SEMANTIC_SHA256_RE.fullmatch(routing_digest) is None:
                    findings.append(
                        Finding(
                            "MANIFEST_SOURCE_ROUTING_SHA256_INVALID",
                            table.path,
                            line,
                            source_id,
                        )
                    )
            elif routing_digest:
                findings.append(
                    Finding(
                        "MANIFEST_ARCHIVED_ROUTING_SHA256_FORBIDDEN",
                        table.path,
                        line,
                        source_id,
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


def validated_source_taxonomy_remediation_manifest_rows(
    manifest_text: str,
) -> tuple[list[dict[str, str]], list[Finding]]:
    """Decode the immutable schema-1 manifest used by the named remediation."""
    table = _parse_table("source-taxonomy-remediation-manifest", manifest_text)
    findings = _normalize_findings(table.findings)
    if findings:
        return [], findings
    manifest_findings, by_id = _validate_manifest(
        table,
        historical_source_taxonomy_remediation=True,
    )
    findings = _normalize_findings(manifest_findings)
    if findings:
        return [], findings
    return list(by_id.values()), []


def validated_taxonomy_backfill_manifest_rows(
    manifest_text: str,
) -> tuple[list[dict[str, str]], list[Finding]]:
    """Decode either supported manifest generation for taxonomy backfill."""
    rows, findings = validated_manifest_rows(manifest_text)
    if not findings:
        return rows, []
    historical_rows, historical_findings = (
        validated_source_taxonomy_remediation_manifest_rows(manifest_text)
    )
    if not historical_findings:
        return historical_rows, []
    return [], findings


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
        decoded_lists = {
            field: (_registry_list(row[field])[0] or [])
            for field in ("Aliases", "Canonical tags", "Include terms", "Exclude terms")
        }
        observed_scope_sha256 = row["Routing scope SHA-256"]
        try:
            expected_scope_sha256 = topic_routing_scope_sha256(
                {
                    "topic_id": topic_id,
                    "domain": domain,
                    "subdomain": subdomain,
                    "canonical_title": title,
                    "aliases": decoded_lists["Aliases"],
                    "canonical_tags": decoded_lists["Canonical tags"],
                    "include_terms": decoded_lists["Include terms"],
                    "exclude_terms": decoded_lists["Exclude terms"],
                }
            )
        except (TypeError, ValueError):
            expected_scope_sha256 = ""
        if (
            SEMANTIC_SHA256_RE.fullmatch(observed_scope_sha256) is None
            or observed_scope_sha256 != expected_scope_sha256
        ):
            findings.append(
                Finding(
                    "TOPIC_ROUTING_SCOPE_SHA256_INVALID",
                    table.path,
                    line,
                    topic_id,
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
        topic_row = topics.get(row["Topic ID"])
        generation_text = row["Generation"]
        generation = (
            int(generation_text) if re.fullmatch(r"0|[1-9]\d*", generation_text) else -1
        )
        if generation < 0:
            findings.append(
                Finding("RELATION_GENERATION_INVALID", table.path, line, edge_id)
            )
        if not EDGE_ID_RE.fullmatch(edge_id):
            findings.append(
                Finding("RELATION_EDGE_ID_INVALID", table.path, line, edge_id)
            )
        content_hash = row["Source content hash"]
        routing_sha256 = row["Source routing SHA-256"]
        scope_sha256 = row["Topic scope SHA-256"]
        if CONTENT_HASH_RE.fullmatch(content_hash) is None:
            findings.append(
                Finding("RELATION_CONTENT_HASH_INVALID", table.path, line, edge_id)
            )
        if (
            routing_sha256 != "legacy-unavailable"
            and SEMANTIC_SHA256_RE.fullmatch(routing_sha256) is None
        ):
            findings.append(
                Finding("RELATION_ROUTING_SHA256_INVALID", table.path, line, edge_id)
            )
        if SEMANTIC_SHA256_RE.fullmatch(scope_sha256) is None:
            findings.append(
                Finding("RELATION_SCOPE_SHA256_INVALID", table.path, line, edge_id)
            )
        if (
            generation >= 0
            and CONTENT_HASH_RE.fullmatch(content_hash)
            and (
                routing_sha256 == "legacy-unavailable"
                or SEMANTIC_SHA256_RE.fullmatch(routing_sha256)
            )
            and SEMANTIC_SHA256_RE.fullmatch(scope_sha256)
            and edge_id
            != _edge_id(
                source_id,
                row["Topic ID"],
                generation,
                content_hash,
                routing_sha256,
                scope_sha256,
            )
        ):
            findings.append(
                Finding("RELATION_EDGE_ID_MISMATCH", table.path, line, edge_id)
            )
        work_kind = row["Work kind"]
        if work_kind not in RELATION_WORK_KINDS:
            findings.append(
                Finding("RELATION_WORK_KIND_INVALID", table.path, line, edge_id)
            )
        evidence_fields = (row["Relation"], row["Impact"], row["Confidence"])
        if work_kind == "evidence":
            if (
                row["Relation"] not in RELATIONS
                or row["Impact"] not in LEVELS
                or row["Confidence"] not in LEVELS
            ):
                findings.append(
                    Finding("RELATION_EVIDENCE_INVALID", table.path, line, edge_id)
                )
        elif any(evidence_fields):
            findings.append(
                Finding(
                    "RELATION_INVALIDATION_EVIDENCE_FORBIDDEN",
                    table.path,
                    line,
                    edge_id,
                )
            )
        status = row["Status"]
        if status not in RELATION_STATUSES:
            findings.append(
                Finding("RELATION_STATUS_INVALID", table.path, line, edge_id)
            )
        if DATE_RE.fullmatch(row["Created"]) is None:
            findings.append(Finding("RELATION_DATE_INVALID", table.path, line, edge_id))
        applied_in = row["Applied in pass"]
        disposition = row["Refresh disposition"]
        if status == "applied":
            if not applied_in or disposition not in REFRESH_DISPOSITIONS:
                findings.append(
                    Finding(
                        "RELATION_APPLIED_FIELDS_INVALID", table.path, line, edge_id
                    )
                )
            if disposition == "legacy" and routing_sha256 != "legacy-unavailable":
                findings.append(
                    Finding(
                        "RELATION_LEGACY_DISPOSITION_INVALID",
                        table.path,
                        line,
                        edge_id,
                    )
                )
        elif applied_in or disposition:
            findings.append(
                Finding(
                    "RELATION_UNAPPLIED_FIELDS_FORBIDDEN",
                    table.path,
                    line,
                    edge_id,
                )
            )
        if (generation == 0) != (row["Prior edge ID"] == ""):
            findings.append(
                Finding("RELATION_PRIOR_EDGE_INVALID", table.path, line, edge_id)
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
        if topic_row is None:
            findings.append(
                Finding("RELATION_TOPIC_UNKNOWN", table.path, line, edge_id)
            )
    for source_id, topic_id in sorted(
        {(row["Source ID"], row["Topic ID"]) for row in records}
    ):
        manifest_row = manifest.get(source_id)
        topic_row = topics.get(topic_id)
        if manifest_row is None or topic_row is None:
            continue
        _, _, pair_findings = _select_relation_frontier(
            records,
            source_id=source_id,
            topic_id=topic_id,
            current_source_hash=manifest_row["Content hash"],
            current_routing_sha256=manifest_row["Source routing SHA-256"],
            current_scope_sha256=topic_row["Routing scope SHA-256"],
        )
        findings.extend(pair_findings)
    return _normalize_findings(findings), records


def _pending_for_topic(
    relations: Sequence[dict[str, str]], topic_id: str
) -> list[dict[str, str]]:
    rows = [
        row
        for row in relations
        if row["Topic ID"] == topic_id and row["Status"] == "pending"
    ]
    return sorted(rows, key=lambda row: (int(row["Source seq"]), row["Edge ID"]))


_REFRESH_DISPOSITION_FIELDS = {
    "edge_id",
    "generation",
    "source_seq",
    "source_id",
    "source_content_hash",
    "source_routing_sha256",
    "topic_scope_sha256",
    "work_kind",
    "disposition",
}


def _refresh_disposition_projection(
    row: Mapping[str, str], disposition: str
) -> dict[str, Any]:
    return {
        "edge_id": row["Edge ID"],
        "generation": int(row["Generation"]),
        "source_seq": int(row["Source seq"]),
        "source_id": row["Source ID"],
        "source_content_hash": row["Source content hash"],
        "source_routing_sha256": row["Source routing SHA-256"],
        "topic_scope_sha256": row["Topic scope SHA-256"],
        "work_kind": row["Work kind"],
        "disposition": disposition,
    }


def _validate_refresh_event(
    texts: Mapping[str, str],
    relations: Sequence[dict[str, str]],
    event: Mapping[str, Any],
    topic_id: str,
    *,
    allow_applied: bool,
    pass_path: str | None = None,
) -> tuple[list[dict[str, Any]], bool, list[Finding]]:
    findings: list[Finding] = []
    inspection_sha256 = event.get("inspection_sha256")
    if "inspection_sha256" in event and (
        not isinstance(inspection_sha256, str)
        or CONTENT_HASH_RE.fullmatch(inspection_sha256) is None
    ):
        findings.extend(
            _event_error("REFRESH_INSPECTION_SHA256_INVALID", str(inspection_sha256))
        )
    expected_revisions = event.get("expected_revisions")
    if "expected_revisions" in event:
        if (
            not isinstance(expected_revisions, Mapping)
            or set(expected_revisions) != set(HEADERS)
            or any(
                not isinstance(value, str) or REVISION_RE.fullmatch(value) is None
                for value in expected_revisions.values()
            )
        ):
            findings.extend(
                _event_error(
                    "REFRESH_REVISIONS_INVALID",
                    "expected_revisions must bind each registry",
                )
            )
        else:
            actual_revisions = {
                name: "sha256:"
                + hashlib.sha256(texts[name].encode("utf-8")).hexdigest()
                for name in HEADERS
            }
            if dict(expected_revisions) != actual_revisions:
                findings.extend(
                    _event_error(
                        "REFRESH_REVISION_MISMATCH",
                        f"expected {actual_revisions!r}",
                    )
                )
    raw_dispositions = event.get("dispositions")
    if "dispositions" not in event:
        return [], False, findings
    if not isinstance(raw_dispositions, list) or not raw_dispositions:
        findings.extend(
            _event_error(
                "REFRESH_PENDING_SET_MISMATCH",
                "dispositions must cover nonempty pending work",
            )
        )
        return [], False, findings
    dispositions: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_dispositions):
        if (
            not isinstance(raw, Mapping)
            or set(raw) != _REFRESH_DISPOSITION_FIELDS
            or raw.get("disposition") not in {"incorporated", "reviewed-no-change"}
        ):
            findings.extend(
                _event_error(
                    "REFRESH_DISPOSITION_INVALID",
                    "disposition fields are invalid",
                    str(index),
                )
            )
            continue
        dispositions.append(dict(raw))
    if findings:
        return dispositions, False, findings
    edge_ids = [str(item["edge_id"]) for item in dispositions]
    if len(set(edge_ids)) != len(edge_ids):
        findings.extend(
            _event_error("REFRESH_DISPOSITION_DUPLICATE", "edge IDs must be unique")
        )
        return dispositions, False, findings
    pending = _pending_for_topic(relations, topic_id)
    expected_ids = [row["Edge ID"] for row in pending]
    idempotent = False
    selected: list[dict[str, str]]
    if edge_ids == expected_ids:
        selected = pending
    elif allow_applied and not pending and pass_path is not None:
        by_id = {row["Edge ID"]: row for row in relations}
        selected = [by_id[edge_id] for edge_id in edge_ids if edge_id in by_id]
        idempotent = len(selected) == len(edge_ids) and all(
            row["Status"] == "applied"
            and row["Applied in pass"] == pass_path
            and row["Refresh disposition"] == item["disposition"]
            for row, item in zip(selected, dispositions, strict=True)
        )
        if not idempotent:
            selected = []
    else:
        selected = []
    if not selected:
        findings.extend(
            _event_error("REFRESH_PENDING_SET_MISMATCH", f"expected {expected_ids!r}")
        )
        return dispositions, False, findings
    for index, (row, item) in enumerate(zip(selected, dispositions, strict=True)):
        if item != _refresh_disposition_projection(row, str(item["disposition"])):
            findings.extend(
                _event_error(
                    "REFRESH_FRONTIER_MISMATCH",
                    "generation or semantic identity changed",
                    str(index),
                )
            )
    return dispositions, idempotent, findings


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


def validate_source_taxonomy_remediation_documents(
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    *,
    vocab_text: str | None = None,
) -> list[Finding]:
    """Validate the immutable schema-1 registry surface used by the remediation."""
    parsed = {
        "manifest": _parse_table("source-taxonomy-remediation-manifest", manifest_text),
        "topics": _parse_table("topics", topics_text),
        "relations": _parse_table("relations", relations_text),
    }
    vocab_findings = validate_vocab(vocab_text) if vocab_text is not None else []
    structural = _normalize_findings(
        [
            *(finding for table in parsed.values() for finding in table.findings),
            *vocab_findings,
        ]
    )
    if structural:
        return structural

    manifest_findings, manifest = _validate_manifest(
        parsed["manifest"],
        historical_source_taxonomy_remediation=True,
    )
    topic_findings, topics = _validate_topics_shape(parsed["topics"])
    relation_findings, relations = _validate_relations(
        parsed["relations"], manifest, topics
    )
    semantic = manifest_findings + topic_findings + relation_findings
    if not semantic:
        semantic.extend(_validate_topic_caches(parsed["topics"], topics, relations))
    return _normalize_findings(semantic)


def validate_taxonomy_backfill_documents(
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    *,
    vocab_text: str | None = None,
) -> list[Finding]:
    """Validate either supported registry generation for taxonomy backfill."""
    findings = validate_documents(
        manifest_text,
        topics_text,
        relations_text,
        vocab_text=vocab_text,
    )
    if not findings:
        return []
    _, historical_manifest_findings = (
        validated_source_taxonomy_remediation_manifest_rows(manifest_text)
    )
    if historical_manifest_findings:
        return findings
    return validate_source_taxonomy_remediation_documents(
        manifest_text,
        topics_text,
        relations_text,
        vocab_text=vocab_text,
    )


def _atlas_uri(path: str) -> str:
    return (
        path
        if path.startswith("vault://atlas/")
        else "vault://atlas/" + path.lstrip("/")
    )


def _taxonomy_observation(
    *,
    path: str,
    field: str,
    row_id: str,
    expected_type: str,
    expected_parent_ids: Iterable[str] = (),
) -> dict[str, Any]:
    return {
        "path": _atlas_uri(path),
        "field": field,
        "row_id": row_id,
        "expected_type": expected_type,
        "expected_parent_ids": tuple(
            sorted(
                {value for value in expected_parent_ids if value},
                key=lambda value: value.encode("utf-8"),
            )
        ),
    }


def _taxonomy_detail(
    observation: Mapping[str, Any],
    *,
    observed_state: str,
    observed_type: str | None,
    observed_parent: str | None,
) -> str:
    return json.dumps(
        {
            "expected_parent_ids": list(observation["expected_parent_ids"]),
            "expected_type": observation["expected_type"],
            "field": observation["field"],
            "observed_parent": observed_parent,
            "observed_state": observed_state,
            "observed_type": observed_type,
            "row_id": observation["row_id"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _taxonomy_finding(
    code: str,
    observation: Mapping[str, Any],
    *,
    observed_state: str,
    observed_type: str | None = None,
    observed_parent: str | None = None,
) -> Finding:
    return Finding(
        code,
        str(observation["path"]),
        detail=_taxonomy_detail(
            observation,
            observed_state=observed_state,
            observed_type=observed_type,
            observed_parent=observed_parent,
        ),
    )


def _source_taxonomy_observations(
    *,
    path: str,
    source_kind: str,
    primary_domain: str,
    secondary_domains: Sequence[str],
    subdomains: Sequence[str],
    canonical_tags: Sequence[str],
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    if source_kind:
        observations.append(
            _taxonomy_observation(
                path=path,
                field="source_kind",
                row_id=source_kind,
                expected_type="source-kind",
            )
        )
    if primary_domain:
        observations.append(
            _taxonomy_observation(
                path=path,
                field="primary_domain",
                row_id=primary_domain,
                expected_type="domain",
            )
        )
    for index, value in enumerate(secondary_domains):
        if value:
            observations.append(
                _taxonomy_observation(
                    path=path,
                    field=f"secondary_domains[{index}]",
                    row_id=value,
                    expected_type="domain",
                )
            )
    allowed_parents = {primary_domain, *secondary_domains} - {""}
    for index, value in enumerate(subdomains):
        if value:
            observations.append(
                _taxonomy_observation(
                    path=path,
                    field=f"subdomains[{index}]",
                    row_id=value,
                    expected_type="subdomain",
                    expected_parent_ids=allowed_parents,
                )
            )
    for index, value in enumerate(canonical_tags):
        if value:
            observations.append(
                _taxonomy_observation(
                    path=path,
                    field=f"canonical_tags[{index}]",
                    row_id=value,
                    expected_type="tag",
                )
            )
    return observations


def _source_taxonomy_remediation_observation_detail(
    *,
    field: str,
    index: int | None,
    expected: Any,
    observed: Any,
) -> str:
    return json.dumps(
        {
            "expected": expected,
            "field": field,
            "index": index,
            "observed": observed,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _source_taxonomy_remediation_target_detail(
    *,
    expected_source_id: str | None,
    expected_path: str | None,
    observed_path: str | None,
    observed_status: str | None,
) -> str:
    return json.dumps(
        {
            "expected_path": expected_path,
            "expected_source_id": expected_source_id,
            "observed_path": observed_path,
            "observed_status": observed_status,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _source_taxonomy_remediation_projection_findings(
    active_rows: Sequence[Mapping[str, str]],
    source_projections: Mapping[str, Mapping[str, Any]],
) -> list[Finding]:
    findings: list[Finding] = []
    expected_paths = {row["Artifact"] for row in active_rows}
    for missing in sorted(expected_paths - set(source_projections)):
        row = next(row for row in active_rows if row["Artifact"] == missing)
        findings.append(
            Finding(
                "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                _atlas_uri(missing),
                detail="active source projection is missing",
            )
        )
    for extra in sorted(set(source_projections) - expected_paths):
        findings.append(
            Finding(
                "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                _atlas_uri(extra),
                detail="source projection is not in the locked active set",
            )
        )
    for row in active_rows:
        path = row["Artifact"]
        projection = source_projections.get(path)
        if not isinstance(projection, Mapping):
            continue
        if set(projection) != _SOURCE_PROJECTION_KEYS:
            findings.append(
                Finding(
                    "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                    _atlas_uri(path),
                    detail="source projection keys are invalid",
                )
            )
            continue
        if (
            projection["source_id"] != row["Source ID"]
            or projection["canonical_url"] != row["Canonical URL"]
            or projection["content_hash"] != row["Content hash"]
            or not isinstance(projection["revision"], str)
            or REVISION_RE.fullmatch(projection["revision"]) is None
        ):
            findings.append(
                Finding(
                    "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                    _atlas_uri(path),
                    detail="manifest and source projection identity or revision disagree",
                )
            )
            continue
        if any(
            not isinstance(projection[name], str)
            for name in (
                "title",
                "tldr",
                "key_points",
                "source_kind",
                "primary_domain",
            )
        ) or any(
            not isinstance(projection[name], list)
            or any(not isinstance(value, str) for value in projection[name])
            for name in ("secondary_domains", "subdomains", "canonical_tags")
        ):
            findings.append(
                Finding(
                    "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                    _atlas_uri(path),
                    detail="source projection taxonomy fields are invalid",
                )
            )
    return _normalize_findings(findings)


def _source_taxonomy_remediation_target_findings(
    manifest_rows: Sequence[Mapping[str, str]],
) -> list[Finding]:
    by_id = {row["Source ID"]: row for row in manifest_rows}
    by_path = {row["Artifact"]: row for row in manifest_rows}
    findings: list[Finding] = []
    for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS:
        by_identity = by_id.get(target.source_id)
        by_location = by_path.get(target.path)
        if (
            by_identity is not None
            and by_identity["Artifact"] == target.path
            and by_identity["Status"] == "active"
            and by_location is by_identity
        ):
            continue
        observed = by_identity if by_identity is not None else by_location
        findings.append(
            Finding(
                "SOURCE_TAXONOMY_REMEDIATION_TARGET_MISMATCH",
                _atlas_uri(MANIFEST_PATH),
                detail=_source_taxonomy_remediation_target_detail(
                    expected_source_id=target.source_id,
                    expected_path=target.path,
                    observed_path=None if observed is None else observed["Artifact"],
                    observed_status=None if observed is None else observed["Status"],
                ),
            )
        )
    return _normalize_findings(findings)


def _source_taxonomy_remediation_topic_observations(
    topics_text: str,
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    parsed_topics = _parse_table("topics", topics_text)
    for row in _mutable_rows(parsed_topics, TOPICS_HEADER):
        path = _atlas_uri(row["Topic path"])
        observations.append(
            _taxonomy_observation(
                path=path,
                field="Domain",
                row_id=row["Domain"],
                expected_type="domain",
            )
        )
        observations.append(
            _taxonomy_observation(
                path=path,
                field="Subdomain",
                row_id=row["Subdomain"],
                expected_type="subdomain",
                expected_parent_ids=(row["Domain"],),
            )
        )
        tags, _ = _registry_list(row["Canonical tags"])
        assert tags is not None
        observations.extend(
            _taxonomy_observation(
                path=path,
                field=f"Canonical tags[{index}]",
                row_id=tag,
                expected_type="tag",
            )
            for index, tag in enumerate(tags)
        )
    return observations


def _source_taxonomy_remediation_closure_findings(
    topics_text: str,
    vocab_text: str,
    active_rows: Sequence[Mapping[str, str]],
    source_projections: Mapping[str, Mapping[str, Any]],
    *,
    permit_baseline: bool,
) -> list[Finding]:
    _, records, vocab_findings = _validated_vocab(vocab_text)
    if vocab_findings:
        return vocab_findings
    by_id = {str(record["id"]): record for record in records}
    observations = _source_taxonomy_remediation_topic_observations(topics_text)
    for row in active_rows:
        projection = source_projections[row["Artifact"]]
        observations.extend(
            _source_taxonomy_observations(
                path=row["Artifact"],
                source_kind=str(projection["source_kind"]),
                primary_domain=str(projection["primary_domain"]),
                secondary_domains=projection["secondary_domains"],
                subdomains=projection["subdomains"],
                canonical_tags=projection["canonical_tags"],
            )
        )
    permitted: set[tuple[str, str, str]] = set()
    if permit_baseline:
        for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS:
            path = _atlas_uri(target.path)
            if target.primary_domain_change is not None:
                permitted.add((path, "primary_domain", target.primary_domain_change[0]))
            permitted.update(
                (path, f"subdomains[{index}]", value)
                for index, value in target.subdomain_observations
            )
    findings: list[Finding] = []
    for observation in observations:
        row_id = str(observation["row_id"])
        if (
            str(observation["path"]),
            str(observation["field"]),
            row_id,
        ) in permitted:
            continue
        record = by_id.get(row_id)
        if VOCAB_ID_RE.fullmatch(row_id) is None:
            findings.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="invalid-id",
                )
            )
            continue
        if record is None:
            findings.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="missing",
                )
            )
            continue
        if record["type"] != observation["expected_type"]:
            findings.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="wrong-type",
                    observed_type=str(record["type"]),
                    observed_parent=str(record["parent"]) or None,
                )
            )
            continue
        if (
            observation["expected_type"] == "subdomain"
            and record["parent"] not in observation["expected_parent_ids"]
        ):
            findings.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="parent-conflict",
                    observed_type="subdomain",
                    observed_parent=str(record["parent"]) or None,
                )
            )
    return _normalize_findings(findings)


def _source_taxonomy_remediation_required_vocab_findings(
    vocab_text: str,
) -> list[Finding]:
    _, records, vocab_findings = _validated_vocab(vocab_text)
    if vocab_findings:
        return vocab_findings
    by_id = {str(record["id"]): record for record in records}
    required = (
        ("web", "domain", ""),
        ("agent-systems", "domain", ""),
        ("harness", "subdomain", "agent-systems"),
    )
    findings: list[Finding] = []
    for row_id, row_type, parent in required:
        record = by_id.get(row_id)
        if (
            record is not None
            and record["type"] == row_type
            and record["parent"] == parent
            and record["status"] in VOCAB_STATUSES
        ):
            continue
        observation = _taxonomy_observation(
            path=VOCAB_PATH,
            field=f"required.{row_id}",
            row_id=row_id,
            expected_type=row_type,
            expected_parent_ids=(parent,) if parent else (),
        )
        if record is None:
            observed_state = "missing"
        elif record["type"] != row_type:
            observed_state = "wrong-type"
        else:
            observed_state = "parent-conflict"
        findings.append(
            _taxonomy_finding(
                "SOURCE_TAXONOMY_INVALID",
                observation,
                observed_state=observed_state,
                observed_type=None if record is None else str(record["type"]),
                observed_parent=None
                if record is None
                else str(record["parent"]) or None,
            )
        )
    return _normalize_findings(findings)


def _source_taxonomy_remediation_baseline_findings(
    active_rows: Sequence[Mapping[str, str]],
    source_projections: Mapping[str, Mapping[str, Any]],
) -> list[Finding]:
    findings: list[Finding] = []
    expected_legacy_slots = {
        (
            target.path,
            "primary_domain",
            None,
            target.primary_domain_change[0],
        )
        for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS
        if target.primary_domain_change is not None
    }
    expected_legacy_slots.update(
        (target.path, "subdomains", index, value)
        for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS
        for index, value in target.subdomain_observations
    )
    for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS:
        projection = source_projections[target.path]
        if target.primary_domain_change is not None:
            observed = projection["primary_domain"]
            expected = target.primary_domain_change[0]
            if observed != expected:
                findings.append(
                    Finding(
                        "SOURCE_TAXONOMY_REMEDIATION_OBSERVATION_MISMATCH",
                        _atlas_uri(target.path),
                        detail=_source_taxonomy_remediation_observation_detail(
                            field="primary_domain",
                            index=None,
                            expected=expected,
                            observed=observed,
                        ),
                    )
                )
        subdomains = projection["subdomains"]
        for index, expected in target.subdomain_observations:
            observed = subdomains[index] if index < len(subdomains) else None
            if observed != expected:
                findings.append(
                    Finding(
                        "SOURCE_TAXONOMY_REMEDIATION_OBSERVATION_MISMATCH",
                        _atlas_uri(target.path),
                        detail=_source_taxonomy_remediation_observation_detail(
                            field="subdomains",
                            index=index,
                            expected=expected,
                            observed=observed,
                        ),
                    )
                )
    for row in active_rows:
        path = row["Artifact"]
        projection = source_projections[path]
        primary = projection["primary_domain"]
        if (
            primary in _SOURCE_TAXONOMY_REMEDIATION_LEGACY_PRIMARY
            and (path, "primary_domain", None, primary) not in expected_legacy_slots
        ):
            target = _SOURCE_TAXONOMY_REMEDIATION_BY_PATH.get(path)
            if target is None:
                findings.append(
                    Finding(
                        "SOURCE_TAXONOMY_REMEDIATION_TARGET_MISMATCH",
                        _atlas_uri(path),
                        detail=_source_taxonomy_remediation_target_detail(
                            expected_source_id=None,
                            expected_path=None,
                            observed_path=path,
                            observed_status=row["Status"],
                        ),
                    )
                )
            else:
                findings.append(
                    Finding(
                        "SOURCE_TAXONOMY_REMEDIATION_OBSERVATION_MISMATCH",
                        _atlas_uri(path),
                        detail=_source_taxonomy_remediation_observation_detail(
                            field="primary_domain",
                            index=None,
                            expected=None,
                            observed=primary,
                        ),
                    )
                )
        for index, value in enumerate(projection["subdomains"]):
            if (
                value in _SOURCE_TAXONOMY_REMEDIATION_LEGACY_SUBDOMAINS
                and (path, "subdomains", index, value) not in expected_legacy_slots
            ):
                target = _SOURCE_TAXONOMY_REMEDIATION_BY_PATH.get(path)
                if target is None:
                    findings.append(
                        Finding(
                            "SOURCE_TAXONOMY_REMEDIATION_TARGET_MISMATCH",
                            _atlas_uri(path),
                            detail=_source_taxonomy_remediation_target_detail(
                                expected_source_id=None,
                                expected_path=None,
                                observed_path=path,
                                observed_status=row["Status"],
                            ),
                        )
                    )
                else:
                    findings.append(
                        Finding(
                            "SOURCE_TAXONOMY_REMEDIATION_OBSERVATION_MISMATCH",
                            _atlas_uri(path),
                            detail=_source_taxonomy_remediation_observation_detail(
                                field="subdomains",
                                index=index,
                                expected=None,
                                observed=value,
                            ),
                        )
                    )
    return _normalize_findings(findings)


def _source_taxonomy_remediation_subdomains(values: Sequence[str]) -> list[str]:
    output: list[str] = []
    harness_seen = False
    for value in values:
        mapped = (
            "harness"
            if value in _SOURCE_TAXONOMY_REMEDIATION_LEGACY_SUBDOMAINS
            else value
        )
        if mapped == "harness":
            if harness_seen:
                continue
            harness_seen = True
        output.append(mapped)
    return output


def _source_taxonomy_remediation_is_no_op(
    active_rows: Sequence[Mapping[str, str]],
    source_projections: Mapping[str, Mapping[str, Any]],
) -> bool:
    for row in active_rows:
        projection = source_projections[row["Artifact"]]
        if projection["primary_domain"] in _SOURCE_TAXONOMY_REMEDIATION_LEGACY_PRIMARY:
            return False
        if any(
            value in _SOURCE_TAXONOMY_REMEDIATION_LEGACY_SUBDOMAINS
            for value in projection["subdomains"]
        ):
            return False
    for target in _SOURCE_TAXONOMY_REMEDIATION_TARGETS:
        projection = source_projections[target.path]
        if (
            target.primary_domain_change is not None
            and projection["primary_domain"] != target.primary_domain_change[1]
        ):
            return False
        if target.subdomain_observations and "harness" not in projection["subdomains"]:
            return False
    return True


def prepare_source_taxonomy_remediation_candidate(
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    vocab_text: str,
    source_projections: Mapping[str, Mapping[str, Any]],
) -> SourceTaxonomyRemediationCandidateResult:
    """Prepare the fixed all-or-nothing source-taxonomy remediation candidate."""

    if not isinstance(source_projections, Mapping):
        raise TypeError("source_projections must be a mapping")
    registry_findings = validate_source_taxonomy_remediation_documents(
        manifest_text,
        topics_text,
        relations_text,
        vocab_text=vocab_text,
    )
    if registry_findings:
        return SourceTaxonomyRemediationCandidateResult(
            "invalid", findings=tuple(registry_findings)
        )
    manifest_rows, manifest_findings = (
        validated_source_taxonomy_remediation_manifest_rows(manifest_text)
    )
    if manifest_findings:
        return SourceTaxonomyRemediationCandidateResult(
            "invalid", findings=tuple(manifest_findings)
        )
    active_rows = sorted(
        (row for row in manifest_rows if row["Status"] == "active"),
        key=lambda row: int(row["Source seq"]),
    )
    findings = [
        *_source_taxonomy_remediation_target_findings(manifest_rows),
        *_source_taxonomy_remediation_projection_findings(
            active_rows, source_projections
        ),
        *_source_taxonomy_remediation_required_vocab_findings(vocab_text),
    ]
    if findings:
        return SourceTaxonomyRemediationCandidateResult(
            "invalid", findings=tuple(_normalize_findings(findings))
        )
    no_op = _source_taxonomy_remediation_is_no_op(active_rows, source_projections)
    closure_findings = _source_taxonomy_remediation_closure_findings(
        topics_text,
        vocab_text,
        active_rows,
        source_projections,
        permit_baseline=not no_op,
    )
    if no_op:
        if closure_findings:
            return SourceTaxonomyRemediationCandidateResult(
                "invalid", findings=tuple(closure_findings)
            )
        return SourceTaxonomyRemediationCandidateResult("no-op")
    baseline_findings = _source_taxonomy_remediation_baseline_findings(
        active_rows, source_projections
    )
    if baseline_findings or closure_findings:
        return SourceTaxonomyRemediationCandidateResult(
            "invalid",
            findings=tuple(
                _normalize_findings([*baseline_findings, *closure_findings])
            ),
        )

    outputs = {
        path: dict(projection) for path, projection in source_projections.items()
    }
    targets: list[SourceTaxonomyRemediationTargetResult] = []
    for row in active_rows:
        target = _SOURCE_TAXONOMY_REMEDIATION_BY_PATH.get(row["Artifact"])
        if target is None:
            continue
        projection = source_projections[target.path]
        changes: list[dict[str, Any]] = []
        if target.primary_domain_change is not None:
            before, after = target.primary_domain_change
            changes.append(
                {"field": "primary_domain", "before": before, "after": after}
            )
            outputs[target.path]["primary_domain"] = after
        if target.subdomain_observations:
            before_values = list(projection["subdomains"])
            after_values = _source_taxonomy_remediation_subdomains(before_values)
            changes.append(
                {
                    "field": "subdomains",
                    "before": before_values,
                    "after": after_values,
                }
            )
            outputs[target.path]["subdomains"] = after_values
        targets.append(
            SourceTaxonomyRemediationTargetResult(
                target.source_id,
                target.path,
                tuple(changes),
            )
        )
    output_findings = _source_taxonomy_remediation_closure_findings(
        topics_text,
        vocab_text,
        active_rows,
        outputs,
        permit_baseline=False,
    )
    if output_findings:
        detail = json.dumps(
            {"findings": [finding.to_dict() for finding in output_findings]},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return SourceTaxonomyRemediationCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "SOURCE_TAXONOMY_REMEDIATION_OUTPUT_INVALID",
                    _atlas_uri(MANIFEST_PATH),
                    detail=detail,
                ),
                *tuple(output_findings),
            ),
        )
    if len(targets) != len(_SOURCE_TAXONOMY_REMEDIATION_TARGETS):
        return SourceTaxonomyRemediationCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "SOURCE_TAXONOMY_REMEDIATION_OUTPUT_INVALID",
                    _atlas_uri(MANIFEST_PATH),
                    detail="candidate target set is incomplete",
                ),
            ),
        )
    return SourceTaxonomyRemediationCandidateResult("candidate", targets=tuple(targets))


def prepare_taxonomy_backfill_candidate(
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    vocab_text: str,
    source_projections: Mapping[str, Mapping[str, Any]],
) -> TaxonomyBackfillCandidateResult:
    """Prepare one deterministic insert-only VOCAB closure candidate."""
    if not isinstance(source_projections, Mapping):
        raise TypeError("source_projections must be a mapping")
    baseline = _normalize_findings(
        validate_taxonomy_backfill_documents(
            manifest_text,
            topics_text,
            relations_text,
            vocab_text=vocab_text,
        )
    )
    if baseline:
        return TaxonomyBackfillCandidateResult("invalid", findings=tuple(baseline))

    manifest_rows, manifest_findings = validated_taxonomy_backfill_manifest_rows(
        manifest_text
    )
    if manifest_findings:
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=tuple(manifest_findings)
        )
    active_rows = sorted(
        (row for row in manifest_rows if row["Status"] == "active"),
        key=lambda row: int(row["Source seq"]),
    )
    expected_artifacts = {row["Artifact"] for row in active_rows}
    if set(source_projections) != expected_artifacts:
        detail = json.dumps(
            {
                "expected": sorted(expected_artifacts),
                "observed": sorted(source_projections),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "TAXONOMY_BACKFILL_SOURCE_SET_INVALID",
                    _atlas_uri(MANIFEST_PATH),
                    detail=detail,
                ),
            ),
        )

    observations: list[dict[str, Any]] = []
    parsed_topics = _parse_table("topics", topics_text)
    for row in _mutable_rows(parsed_topics, TOPICS_HEADER):
        topic_path = _atlas_uri(row["Topic path"])
        observations.append(
            _taxonomy_observation(
                path=topic_path,
                field="Domain",
                row_id=row["Domain"],
                expected_type="domain",
            )
        )
        observations.append(
            _taxonomy_observation(
                path=topic_path,
                field="Subdomain",
                row_id=row["Subdomain"],
                expected_type="subdomain",
                expected_parent_ids=(row["Domain"],),
            )
        )
        tags, _ = _registry_list(row["Canonical tags"])
        assert tags is not None
        for index, tag in enumerate(tags):
            observations.append(
                _taxonomy_observation(
                    path=topic_path,
                    field=f"Canonical tags[{index}]",
                    row_id=tag,
                    expected_type="tag",
                )
            )

    projection_findings: list[Finding] = []
    for row in active_rows:
        artifact = row["Artifact"]
        projection = source_projections.get(artifact)
        path = _atlas_uri(artifact)
        if (
            not isinstance(projection, Mapping)
            or set(projection) != _SOURCE_PROJECTION_KEYS
        ):
            projection_findings.append(
                Finding(
                    "TAXONOMY_BACKFILL_SOURCE_INVALID",
                    path,
                    detail="source projection is missing or malformed",
                )
            )
            continue
        if (
            projection["source_id"] != row["Source ID"]
            or projection["canonical_url"] != row["Canonical URL"]
            or projection["content_hash"] != row["Content hash"]
            or not isinstance(projection["revision"], str)
            or REVISION_RE.fullmatch(projection["revision"]) is None
        ):
            projection_findings.append(
                Finding(
                    "TAXONOMY_BACKFILL_SOURCE_INVALID",
                    path,
                    detail="manifest and source projection identity or revision disagree",
                )
            )
            continue
        string_fields = (
            "title",
            "tldr",
            "key_points",
            "source_kind",
            "primary_domain",
        )
        list_fields = ("secondary_domains", "subdomains", "canonical_tags")
        if any(not isinstance(projection[name], str) for name in string_fields) or any(
            not isinstance(projection[name], list)
            or any(not isinstance(value, str) for value in projection[name])
            for name in list_fields
        ):
            projection_findings.append(
                Finding(
                    "TAXONOMY_BACKFILL_SOURCE_INVALID",
                    path,
                    detail="source projection taxonomy fields are invalid",
                )
            )
            continue
        observations.extend(
            _source_taxonomy_observations(
                path=path,
                source_kind=str(projection["source_kind"]),
                primary_domain=str(projection["primary_domain"]),
                secondary_domains=projection["secondary_domains"],
                subdomains=projection["subdomains"],
                canonical_tags=projection["canonical_tags"],
            )
        )
    if projection_findings:
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=tuple(_normalize_findings(projection_findings))
        )

    table, records, vocab_findings = _validated_vocab(vocab_text)
    if vocab_findings:
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=tuple(vocab_findings)
        )
    by_id = {str(record["id"]): record for record in records}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        grouped.setdefault(str(observation["row_id"]), []).append(observation)

    blockers: list[Finding] = []
    planned: dict[tuple[str, str], dict[str, Any]] = {}
    missing: dict[str, list[dict[str, Any]]] = {}
    for row_id in sorted(grouped, key=lambda value: value.encode("utf-8")):
        current = grouped[row_id]
        if VOCAB_ID_RE.fullmatch(row_id) is None:
            blockers.extend(
                _taxonomy_finding(
                    "TAXONOMY_BACKFILL_ID_INVALID",
                    observation,
                    observed_state="invalid-id",
                )
                for observation in current
            )
            continue
        expected_types = {str(item["expected_type"]) for item in current}
        if len(expected_types) != 1:
            observed_type = "|".join(sorted(expected_types))
            blockers.extend(
                _taxonomy_finding(
                    "TAXONOMY_BACKFILL_TYPE_CONFLICT",
                    observation,
                    observed_state="wrong-type",
                    observed_type=observed_type,
                )
                for observation in current
            )
            continue
        expected_type = next(iter(expected_types))
        record = by_id.get(row_id)
        if record is None:
            missing[row_id] = current
            continue
        if record["type"] != expected_type:
            blockers.extend(
                _taxonomy_finding(
                    "TAXONOMY_BACKFILL_TYPE_CONFLICT",
                    observation,
                    observed_state="wrong-type",
                    observed_type=str(record["type"]),
                    observed_parent=str(record["parent"]) or None,
                )
                for observation in current
            )
            continue
        if expected_type == "subdomain":
            for observation in current:
                if record["parent"] not in observation["expected_parent_ids"]:
                    blockers.append(
                        _taxonomy_finding(
                            "TAXONOMY_BACKFILL_PARENT_CONFLICT",
                            observation,
                            observed_state="parent-conflict",
                            observed_type="subdomain",
                            observed_parent=str(record["parent"]) or None,
                        )
                    )

    for row_type in ("domain", "tag"):
        for row_id in sorted(missing, key=lambda value: value.encode("utf-8")):
            current = missing[row_id]
            if current[0]["expected_type"] != row_type:
                continue
            collisions = [
                record
                for record in records
                if _classification_token(row_id) in _record_tokens(record)
            ]
            if collisions:
                collision = collisions[0]
                blockers.extend(
                    _taxonomy_finding(
                        "TAXONOMY_BACKFILL_TOKEN_CONFLICT",
                        observation,
                        observed_state="missing",
                        observed_type=str(collision["type"]),
                        observed_parent=str(collision["parent"]) or None,
                    )
                    for observation in current
                )
                continue
            planned[(row_type, row_id)] = {
                "id": row_id,
                "type": row_type,
                "label": row_id,
                "parent": "",
                "allowed_aliases": [],
                "status": "active",
                "notes": "",
            }

    for row_id in sorted(missing, key=lambda value: value.encode("utf-8")):
        current = missing[row_id]
        row_type = str(current[0]["expected_type"])
        if row_type == "source-kind":
            blockers.extend(
                _taxonomy_finding(
                    "TAXONOMY_BACKFILL_INSERT_UNSUPPORTED",
                    observation,
                    observed_state="missing",
                )
                for observation in current
            )
            continue
        if row_type != "subdomain":
            continue
        collisions = [
            record
            for record in records
            if _classification_token(row_id) in _record_tokens(record)
        ]
        if collisions:
            collision = collisions[0]
            blockers.extend(
                _taxonomy_finding(
                    "TAXONOMY_BACKFILL_TOKEN_CONFLICT",
                    observation,
                    observed_state="missing",
                    observed_type=str(collision["type"]),
                    observed_parent=str(collision["parent"]) or None,
                )
                for observation in current
            )
            continue
        parent_sets = [set(item["expected_parent_ids"]) for item in current]
        parent_intersection = set(parent_sets[0]) if parent_sets else set()
        for parent_set in parent_sets[1:]:
            parent_intersection.intersection_update(parent_set)
        if len(parent_intersection) != 1:
            blockers.extend(
                _taxonomy_finding(
                    "TAXONOMY_BACKFILL_PARENT_AMBIGUOUS",
                    observation,
                    observed_state="missing",
                )
                for observation in current
            )
            continue
        parent = next(iter(parent_intersection))
        parent_record = by_id.get(parent)
        parent_available = (
            parent_record is not None and parent_record["type"] == "domain"
        ) or ("domain", parent) in planned
        if not parent_available:
            blockers.extend(
                _taxonomy_finding(
                    "TAXONOMY_BACKFILL_PARENT_AMBIGUOUS",
                    observation,
                    observed_state="missing",
                )
                for observation in current
            )
            continue
        planned[(row_type, row_id)] = {
            "id": row_id,
            "type": row_type,
            "label": row_id,
            "parent": parent,
            "allowed_aliases": [],
            "status": "active",
            "notes": "",
        }

    if blockers:
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=tuple(_normalize_findings(blockers))
        )
    changes = [
        planned[key]
        for key in sorted(
            planned,
            key=lambda item: (
                {"domain": 0, "subdomain": 1, "tag": 2}[item[0]],
                item[1].encode("utf-8"),
            ),
        )
    ]
    if not changes:
        return TaxonomyBackfillCandidateResult("no-op")
    rows = [
        _new_vocab_row(
            {
                "id": change["id"],
                "label": change["label"],
                "aliases": change["allowed_aliases"],
            },
            row_type=str(change["type"]),
            parent=str(change["parent"]),
        )
        for change in changes
    ]
    candidate_text = _append_rows(table, rows)
    replay = prepare_taxonomy_backfill_candidate(
        manifest_text,
        topics_text,
        relations_text,
        candidate_text,
        source_projections,
    )
    if replay.state != "no-op":
        findings = replay.findings or (
            Finding(
                "TAXONOMY_BACKFILL_POST_INVALID",
                _atlas_uri(VOCAB_PATH),
                detail="candidate replay did not close taxonomy",
            ),
        )
        return TaxonomyBackfillCandidateResult("invalid", findings=tuple(findings))
    return TaxonomyBackfillCandidateResult(
        "candidate",
        preimage_revision="sha256:"
        + hashlib.sha256(vocab_text.encode("utf-8")).hexdigest(),
        output_revision="sha256:"
        + hashlib.sha256(candidate_text.encode("utf-8")).hexdigest(),
        preimage_text=vocab_text,
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
    """Validate one closed normalized classifier result."""
    if not isinstance(value, Mapping) or set(value) != {
        "version",
        "primary_domain",
        "secondary_domains",
        "subdomains",
        "tags",
        "routing_terms",
    }:
        return None, [
            _classification_finding(
                "classification.result", "classifier result fields are invalid"
            )
        ]
    if value.get("version") != 1:
        return None, [
            _classification_finding(
                "classification.result.version", "expected version 1"
            )
        ]
    findings: list[Finding] = []

    def entry(
        item: Any, path: str, *, subdomain: bool = False
    ) -> dict[str, Any] | None:
        normalized, entry_findings = _normalize_classification_entry(
            item, path=path, subdomain=subdomain
        )
        findings.extend(entry_findings)
        return normalized

    primary_value = value.get("primary_domain")
    primary = (
        None
        if primary_value is None
        else entry(primary_value, "classification.result.primary_domain")
    )
    collections: dict[str, list[dict[str, Any]]] = {}
    for name, limit, subdomain in (
        ("secondary_domains", 3, False),
        ("subdomains", 6, True),
        ("tags", 12, False),
    ):
        raw = value.get(name)
        items: list[dict[str, Any]] = []
        if not isinstance(raw, list) or len(raw) > limit:
            findings.append(
                _classification_finding(
                    f"classification.result.{name}",
                    f"expected array capped at {limit}",
                )
            )
        else:
            for index, raw_item in enumerate(raw):
                normalized = entry(
                    raw_item,
                    f"classification.result.{name}[{index}]",
                    subdomain=subdomain,
                )
                if normalized is not None:
                    items.append(normalized)
            if len({str(item["id"]).casefold() for item in items}) != len(items):
                findings.append(
                    _classification_finding(
                        f"classification.result.{name}", "IDs must be unique"
                    )
                )
        collections[name] = items
    domain_ids = {
        str(item["id"]).casefold()
        for item in (
            ([primary] if primary is not None else [])
            + collections["secondary_domains"]
        )
    }
    for item in collections["subdomains"]:
        if str(item["parent"]).casefold() not in domain_ids:
            findings.append(
                _classification_finding(
                    "classification.result.subdomains",
                    "subdomain parent must name a proposed domain",
                )
            )
    raw_terms = value.get("routing_terms")
    routing_terms: list[dict[str, str]] = []
    identities: set[tuple[str, str]] = set()
    if not isinstance(raw_terms, list) or len(raw_terms) > 24:
        findings.append(
            _classification_finding(
                "classification.result.routing_terms",
                "expected array capped at 24",
            )
        )
    else:
        for index, raw_term in enumerate(raw_terms):
            if not isinstance(raw_term, Mapping) or set(raw_term) != {
                "type",
                "value",
                "confidence",
            }:
                findings.append(
                    _classification_finding(
                        f"classification.result.routing_terms[{index}]",
                        "routing term fields are invalid",
                    )
                )
                continue
            term_type = raw_term.get("type")
            term_value = raw_term.get("value")
            confidence = raw_term.get("confidence")
            if (
                term_type not in ROUTING_TERM_TYPES
                or confidence not in ROUTING_TERM_CONFIDENCES
                or not isinstance(term_value, str)
                or not term_value.strip()
                or unicodedata.normalize("NFKC", term_value).strip() != term_value
            ):
                findings.append(
                    _classification_finding(
                        f"classification.result.routing_terms[{index}]",
                        "routing term value is invalid",
                    )
                )
                continue
            identity = (str(term_type), term_value.casefold())
            if identity in identities:
                findings.append(
                    _classification_finding(
                        "classification.result.routing_terms",
                        "routing terms must be unique",
                    )
                )
            identities.add(identity)
            routing_terms.append(
                {
                    "type": str(term_type),
                    "value": term_value,
                    "confidence": str(confidence),
                }
            )
    if primary is None:
        findings.append(
            _classification_finding(
                "classification.result.primary_domain",
                "classified result requires a primary domain",
            )
        )
    if findings:
        return None, _normalize_findings(findings)
    return {
        "primary_domain": primary,
        "secondary_domains": collections["secondary_domains"],
        "subdomains": collections["subdomains"],
        "tags": collections["tags"],
        "routing_terms": routing_terms,
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


def resolve_vocabulary_proposals(
    vocab_text: str,
    classification: Any,
    *,
    conflict_policy: Literal["candidate-term", "block"],
) -> tuple[str, dict[str, Any] | None, list[Finding]]:
    """Resolve canonical classifier proposals under one explicit conflict policy."""
    if conflict_policy not in {"candidate-term", "block"}:
        raise ValueError("conflict_policy must be candidate-term or block")
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
    conflicts: list[Finding] = []

    def add_candidate(value: str) -> None:
        term = value.strip()
        key = _classification_token(term)
        if term and key not in candidate_keys:
            candidate_keys.add(key)
            candidate_terms.append(term)

    def handle_conflict(field: str, label: str) -> None:
        if conflict_policy == "candidate-term":
            add_candidate(label)
        else:
            conflicts.append(
                Finding(
                    "TOPIC_VOCABULARY_CONFLICT",
                    _atlas_uri(VOCAB_PATH),
                    detail=f"{field} proposal is ambiguous or incompatible",
                )
            )

    appended: list[list[str]] = []
    domain_id_by_proposal: dict[str, str] = {}
    domain_ids: list[str] = []
    domain_proposals = [
        normalized["primary_domain"],
        *normalized["secondary_domains"],
    ]
    for index, domain in enumerate(domain_proposals):
        resolved = _resolve_vocab_entry(
            records,
            domain,
            row_type="domain",
            parent="",
            appended=appended,
        )
        if resolved is None:
            handle_conflict(f"domains[{index}]", str(domain["label"]))
            continue
        domain_id_by_proposal[str(domain["id"]).casefold()] = resolved
        if resolved not in domain_ids:
            domain_ids.append(resolved)

    subdomain_ids: list[str] = []
    for index, subdomain in enumerate(normalized["subdomains"]):
        parent_id = domain_id_by_proposal.get(str(subdomain["parent"]).casefold())
        resolved = (
            None
            if parent_id is None
            else _resolve_vocab_entry(
                records,
                subdomain,
                row_type="subdomain",
                parent=parent_id,
                appended=appended,
            )
        )
        if resolved is None:
            handle_conflict(f"subdomains[{index}]", str(subdomain["label"]))
        elif resolved not in subdomain_ids:
            subdomain_ids.append(resolved)

    tag_ids: list[str] = []
    for index, tag in enumerate(normalized["tags"]):
        resolved = _resolve_vocab_entry(
            records, tag, row_type="tag", parent="", appended=appended
        )
        if resolved is None:
            handle_conflict(f"tags[{index}]", str(tag["label"]))
        elif resolved not in tag_ids:
            tag_ids.append(resolved)

    if conflicts:
        return vocab_text, None, _normalize_findings(conflicts)
    candidate_vocab = _append_rows(table, appended)
    post_findings = validate_vocab(candidate_vocab)
    if post_findings:
        return vocab_text, None, post_findings
    return (
        candidate_vocab,
        {
            "classification_status": "classified",
            "primary_domain": domain_ids[0] if domain_ids else "",
            "secondary_domains": domain_ids[1:],
            "subdomains": subdomain_ids,
            "canonical_tags": tag_ids,
            "routing_terms": normalized["routing_terms"],
            "candidate_terms": candidate_terms,
        },
        [],
    )


def resolve_source_classification(
    vocab_text: str,
    classification: Any,
) -> tuple[str, dict[str, Any] | None, list[Finding]]:
    """Resolve one source classification with candidate-term degradation."""
    return resolve_vocabulary_proposals(
        vocab_text,
        classification,
        conflict_policy="candidate-term",
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

    def __init__(
        self,
        code: str,
        path: str,
        detail: str,
        *,
        findings: Sequence[Finding] = (),
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.path = path
        self.detail = detail
        self.findings = tuple(_normalize_findings(findings))


@dataclass(frozen=True)
class SourceCandidateScope:
    state: str
    topic: dict[str, Any] | None
    sources: tuple[dict[str, Any], ...]
    gaps: tuple[dict[str, Any], ...]
    suppressed: tuple[dict[str, Any], ...]
    requested_source_id: str | None
    findings: tuple[Finding, ...]
    route_action: str = "candidate-route"

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
) -> list[dict[str, Any]]:
    pending = sorted(
        (
            row
            for row in relations
            if row["Source ID"] == source_id and row["Status"] == "pending"
        ),
        key=lambda row: (row["Topic ID"], int(row["Generation"])),
    )
    return [
        {
            "edge_id": row["Edge ID"],
            "generation": int(row["Generation"]),
            "topic_id": row["Topic ID"],
            "topic_scope_sha256": row["Topic scope SHA-256"],
            "source_routing_sha256": row["Source routing SHA-256"],
            "work_kind": row["Work kind"],
            "prior_edge_id": row["Prior edge ID"] or None,
            "relation": row["Relation"] or None,
            "impact": row["Impact"] or None,
            "confidence": row["Confidence"] or None,
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
    route_action: str = "candidate-route",
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
        or route_action not in {"candidate-route", "explicit-revalidation"}
        or (route_action == "explicit-revalidation" and source_id is None)
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
        topic_scope_sha256 = topic_row["Routing scope SHA-256"]
        tip, _, frontier_findings = _select_relation_frontier(
            relation_rows,
            source_id=row["Source ID"],
            topic_id=topic_id,
            current_source_hash=row["Content hash"],
            current_routing_sha256=row["Source routing SHA-256"],
            current_scope_sha256=topic_scope_sha256,
        )
        already_related = (
            route_action == "candidate-route"
            and tip is not None
            and not frontier_findings
            and tip["Work kind"] == "evidence"
            and tip["Status"] in {"pending", "applied"}
        )
        if already_related:
            suppressed.append(
                {
                    "source_id": row["Source ID"],
                    "reason": "already-related-current-evidence",
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
                "source_routing_sha256": row["Source routing SHA-256"],
                "named": row["Canonical URL"] in named_set,
                "pending_edges": _pending_route_base(relation_rows, row["Source ID"]),
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
        route_action,
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
    vocab_records: Sequence[Mapping[str, Any]],
) -> tuple[list[str], list[str], int]:
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

    by_id = {str(record["id"]): record for record in vocab_records}

    def vocab_values(identifier: str) -> tuple[str, ...]:
        record = by_id.get(identifier)
        if record is None:
            return (identifier,)
        return (
            str(record["id"]),
            str(record["label"]),
            *(str(alias) for alias in record["aliases"]),
        )

    targets = {
        "domain": vocab_values(str(topic["domain"])),
        "subdomain": vocab_values(str(topic["subdomain"])),
        "tag": tuple(
            value
            for identifier in topic["canonical_tags"]
            for value in vocab_values(str(identifier))
        ),
        "topic": (
            str(topic["topic_id"]),
            str(topic["canonical_title"]),
            *(str(value) for value in topic["aliases"]),
            *(str(value) for value in topic["include_terms"]),
        ),
    }
    ranks = {"high": 3, "medium": 2, "low": 1}
    routing_rank = 0
    for term in projection["routing_terms"]:
        term_type = str(term["type"])
        term_value = str(term["value"])
        confidence = str(term["confidence"])
        if any(
            _contains_phrase(target, term_value)
            and _contains_phrase(term_value, target)
            for target in targets[term_type]
        ):
            positive.append(f"routing-term:{term_type}:{confidence}:{term_value}")
            routing_rank = max(routing_rank, ranks[confidence])
    return positive, excluded, routing_rank


def validate_source_taxonomy(
    vocab_text: str,
    *,
    source_kind: str,
    primary_domain: str,
    secondary_domains: Sequence[str],
    subdomains: Sequence[str],
    canonical_tags: Sequence[str],
    path: str,
) -> list[Finding]:
    """Validate one source artifact's exact canonical vocabulary bindings."""
    _, records, findings = _validated_vocab(vocab_text)
    if findings:
        return findings
    by_id = {str(record["id"]): record for record in records}
    result: list[Finding] = []
    observations = _source_taxonomy_observations(
        path=path,
        source_kind=source_kind,
        primary_domain=primary_domain,
        secondary_domains=secondary_domains,
        subdomains=subdomains,
        canonical_tags=canonical_tags,
    )
    for observation in observations:
        row_id = str(observation["row_id"])
        if VOCAB_ID_RE.fullmatch(row_id) is None:
            result.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="invalid-id",
                )
            )
            continue
        record = by_id.get(row_id)
        if record is None:
            result.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="missing",
                )
            )
            continue
        expected_type = str(observation["expected_type"])
        if record["type"] != expected_type:
            result.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="wrong-type",
                    observed_type=str(record["type"]),
                    observed_parent=str(record["parent"]) or None,
                )
            )
            continue
        if (
            expected_type == "subdomain"
            and record["parent"] not in observation["expected_parent_ids"]
        ):
            result.append(
                _taxonomy_finding(
                    "SOURCE_TAXONOMY_INVALID",
                    observation,
                    observed_state="parent-conflict",
                    observed_type="subdomain",
                    observed_parent=str(record["parent"]) or None,
                )
            )
    return _normalize_findings(result)


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


SOURCE_ROUTING_FIELDS = (
    "classification_status",
    "primary_domain",
    "secondary_domains",
    "subdomains",
    "canonical_tags",
    "routing_terms",
    "title",
    "tldr",
    "key_points",
)
TOPIC_ROUTING_SCOPE_FIELDS = (
    "topic_id",
    "domain",
    "subdomain",
    "canonical_title",
    "aliases",
    "canonical_tags",
    "include_terms",
    "exclude_terms",
)


def source_routing_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return the only source-routing semantic hash projection."""
    if any(field not in value for field in SOURCE_ROUTING_FIELDS):
        raise ValueError("source routing projection is incomplete")
    projection = {field: value[field] for field in SOURCE_ROUTING_FIELDS}
    if projection["classification_status"] not in {"classified", "unclassified"}:
        raise ValueError("source routing classification status is invalid")
    for field in ("primary_domain", "title", "tldr", "key_points"):
        if not isinstance(projection[field], str):
            raise ValueError(f"source routing {field} is invalid")
    for field in ("secondary_domains", "subdomains", "canonical_tags"):
        if not isinstance(projection[field], list) or any(
            not isinstance(item, str) for item in projection[field]
        ):
            raise ValueError(f"source routing {field} is invalid")
    routing_terms = projection["routing_terms"]
    if not isinstance(routing_terms, list):
        raise ValueError("source routing terms are invalid")
    return projection


def source_routing_sha256(value: Mapping[str, Any]) -> str:
    return _canonical_sha256(source_routing_projection(value))


def topic_routing_scope(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return the only topic-routing scope hash projection."""
    if any(field not in value for field in TOPIC_ROUTING_SCOPE_FIELDS):
        raise ValueError("topic routing scope is incomplete")
    projection = {field: value[field] for field in TOPIC_ROUTING_SCOPE_FIELDS}
    for field in ("topic_id", "domain", "subdomain", "canonical_title"):
        if not isinstance(projection[field], str):
            raise ValueError(f"topic routing {field} is invalid")
    for field in ("aliases", "canonical_tags", "include_terms", "exclude_terms"):
        if not isinstance(projection[field], list) or any(
            not isinstance(item, str) for item in projection[field]
        ):
            raise ValueError(f"topic routing {field} is invalid")
    return projection


def topic_routing_scope_sha256(value: Mapping[str, Any]) -> str:
    return _canonical_sha256(topic_routing_scope(value))


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
        "source_routing_sha256",
        "classification_status",
        "routing_terms",
        "title",
        "tldr",
        "key_points",
        "source_kind",
        "primary_domain",
        "secondary_domains",
        "subdomains",
        "canonical_tags",
    }
    _, vocab_records, vocab_findings = _validated_vocab(vocab_text)
    if vocab_findings:
        first = vocab_findings[0]
        raise SourceCandidateError(
            first.code, first.path, first.detail, findings=vocab_findings
        )
    locked: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    taxonomy_findings: list[Finding] = []
    skipped: list[dict[str, Any]] = []
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
            or projection["source_routing_sha256"] != source["source_routing_sha256"]
            or projection["source_routing_sha256"] != source_routing_sha256(projection)
            or not isinstance(projection["revision"], str)
            or REVISION_RE.fullmatch(projection["revision"]) is None
        ):
            raise SourceCandidateError(
                "SOURCE_CANDIDATE_ARTIFACT_DRIFT",
                path,
                "manifest and artifact identity, semantic digest, or revision disagree",
            )
        string_fields = (
            "classification_status",
            "title",
            "tldr",
            "key_points",
            "source_kind",
            "primary_domain",
            "source_routing_sha256",
        )
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
        if projection["classification_status"] == "unclassified":
            if (
                projection["primary_domain"]
                or projection["secondary_domains"]
                or projection["subdomains"]
                or projection["canonical_tags"]
                or projection["routing_terms"]
            ):
                raise SourceCandidateError(
                    "SOURCE_CANDIDATE_ARTIFACT_INVALID",
                    path,
                    "unclassified source contains routing classification",
                )
            skipped.append(
                {
                    "source_seq": source["source_seq"],
                    "source_id": source["source_id"],
                    "artifact": source["artifact"],
                    "findings": [
                        {
                            "code": "SOURCE_CLASSIFICATION_UNAVAILABLE",
                            "path": path,
                            "detail": "source classification is unavailable",
                        }
                    ],
                }
            )
            continue
        source_taxonomy_findings = validate_source_taxonomy(
            vocab_text,
            source_kind=projection["source_kind"],
            primary_domain=projection["primary_domain"],
            secondary_domains=projection["secondary_domains"],
            subdomains=projection["subdomains"],
            canonical_tags=projection["canonical_tags"],
            path=path,
        )
        if source_taxonomy_findings:
            positive_hits, exclude_hits, _ = _candidate_match_facts(
                scope.topic, projection, vocab_records
            )
            if source["named"] or positive_hits or exclude_hits:
                taxonomy_findings.extend(source_taxonomy_findings)
            else:
                skipped.append(
                    {
                        "source_seq": source["source_seq"],
                        "source_id": source["source_id"],
                        "artifact": source["artifact"],
                        "findings": [
                            finding.to_dict()
                            for finding in _normalize_findings(source_taxonomy_findings)
                        ],
                    }
                )
            continue
        locked.append((source, projection))
    taxonomy_findings = _normalize_findings(taxonomy_findings)
    if taxonomy_findings:
        first = taxonomy_findings[0]
        raise SourceCandidateError(
            first.code,
            first.path,
            first.detail,
            findings=taxonomy_findings,
        )

    topic_scope = topic_routing_scope(scope.topic)
    topic_scope_sha256 = topic_routing_scope_sha256(topic_scope)
    if topic_scope_sha256 != scope.topic["routing_scope_sha256"]:
        raise SourceCandidateError(
            "SOURCE_CANDIDATE_TOPIC_SCOPE_DRIFT",
            TOPICS_PATH,
            "stored topic routing scope digest is stale",
        )
    skipped.sort(key=lambda item: (item["source_seq"], item["source_id"]))
    candidates: list[dict[str, Any]] = []
    pair_disposition = (
        "already-related"
        if scope.requested_source_id is not None
        and any(
            item["source_id"] == scope.requested_source_id for item in scope.suppressed
        )
        else "unavailable"
    )
    for source, projection in locked:
        positive_hits, exclude_hits, routing_rank = _candidate_match_facts(
            scope.topic, projection, vocab_records
        )
        eligible = (source["named"] or bool(positive_hits)) and not exclude_hits
        if not eligible:
            if scope.requested_source_id == source["source_id"]:
                pair_disposition = "not-candidate"
            continue
        expected_revisions = {
            "artifact": projection["revision"],
            "manifest": registry_revisions["manifest"],
            "topics": registry_revisions["topics"],
            "relations": registry_revisions["relations"],
            "vocab": registry_revisions["vocab"],
        }
        source_projection = {
            "source_seq": source["source_seq"],
            "source_id": source["source_id"],
            "canonical_url": source["canonical_url"],
            "content_hash": source["content_hash"],
            "source_routing_sha256": source["source_routing_sha256"],
            "artifact": source["artifact"],
            "artifact_revision": projection["revision"],
            "pending_edges": source["pending_edges"],
        }
        routing_hits = sorted(set(positive_hits), key=lambda item: item.encode("utf-8"))
        candidate_sha256 = _canonical_sha256(
            {
                "version": 2,
                "source_projection": source_projection,
                "route_action": scope.route_action,
                "topic_scope_sha256": topic_scope_sha256,
                "named": source["named"],
                "routing_hits": routing_hits,
                "routing_rank": routing_rank,
                "expected_revisions": expected_revisions,
            }
        )
        candidates.append(
            {
                **source_projection,
                "topic_id": scope.topic["topic_id"],
                "topic_scope_sha256": topic_scope_sha256,
                "route_action": scope.route_action,
                "routing_hits": routing_hits,
                "routing_rank": routing_rank,
                "named": source["named"],
                "glance": {
                    "title": projection["title"],
                    "summary": {
                        "tldr": projection["tldr"],
                        "key_points": projection["key_points"],
                    },
                    "classification": {
                        "classification_status": projection["classification_status"],
                        "primary_domain": projection["primary_domain"],
                        "secondary_domains": projection["secondary_domains"],
                        "subdomains": projection["subdomains"],
                        "canonical_tags": projection["canonical_tags"],
                        "routing_terms": projection["routing_terms"],
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
        "skipped_sources": skipped,
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
        "routing_scope_sha256": row["Routing scope SHA-256"],
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
        "generation": int(row["Generation"]),
        "source_seq": int(row["Source seq"]),
        "source_id": row["Source ID"],
        "source_artifact": row["Source artifact"],
        "source_content_hash": row["Source content hash"],
        "source_routing_sha256": row["Source routing SHA-256"],
        "topic_id": row["Topic ID"],
        "topic_scope_sha256": row["Topic scope SHA-256"],
        "work_kind": row["Work kind"],
        "prior_edge_id": row["Prior edge ID"] or None,
        "relation": row["Relation"] or None,
        "impact": row["Impact"] or None,
        "confidence": row["Confidence"] or None,
        "status": row["Status"],
        "created": row["Created"],
        "applied_in_pass": row["Applied in pass"] or None,
        "refresh_disposition": row["Refresh disposition"] or None,
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
    relation_by_id = {relation["edge_id"]: relation for relation in selection.relations}
    pending_frontier = [
        {
            key: relation_by_id[edge_id][key]
            for key in (
                "edge_id",
                "generation",
                "source_seq",
                "source_id",
                "source_content_hash",
                "source_routing_sha256",
                "topic_scope_sha256",
                "work_kind",
            )
        }
        for edge_id in pending_edge_ids
    ]
    preimage = {
        "topic_id": topic_id,
        "purpose": purpose,
        "registry_revisions": registry_bindings,
        "artifact_revisions": artifact_bindings,
        "pending_edge_ids": pending_edge_ids,
        "pending_frontier": pending_frontier,
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
class TaxonomyBackfillCandidateResult:
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


def prepare_vocabulary_domain_insertion_candidate(
    vocab_text: str,
    domain_id: str,
) -> TaxonomyBackfillCandidateResult:
    """Prepare one canonical top-level domain insertion in VOCAB."""
    if not isinstance(domain_id, str) or not VOCAB_ID_RE.fullmatch(domain_id):
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "VOCABULARY_DOMAIN_INSERTION_ID_INVALID",
                    "args.domain_id",
                    row=str(domain_id),
                    detail=("expected exact lowercase kebab-case [a-z0-9][a-z0-9-]*"),
                ),
            ),
        )

    table, records, findings = _validated_vocab(vocab_text)
    if findings:
        return TaxonomyBackfillCandidateResult("invalid", findings=tuple(findings))

    def conflict(
        record: Mapping[str, Any],
        line: int,
        contact_fields: Sequence[str],
    ) -> Finding:
        detail = json.dumps(
            {
                "contact_fields": sorted(set(contact_fields)),
                "observed_id": str(record["id"]),
                "observed_parent": str(record["parent"]),
                "observed_status": str(record["status"]),
                "observed_type": str(record["type"]),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return Finding(
            "VOCABULARY_DOMAIN_INSERTION_CONFLICT",
            _atlas_uri(VOCAB_PATH),
            line=line,
            row=domain_id,
            detail=detail,
        )

    for record, line in zip(records, table.row_lines, strict=True):
        if record["id"] != domain_id:
            continue
        if record["type"] == "domain" and not record["parent"]:
            return TaxonomyBackfillCandidateResult("no-op")
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=(conflict(record, line, ("id",)),)
        )

    request_token = _classification_token(domain_id)
    conflicts: list[Finding] = []
    for record, line in zip(records, table.row_lines, strict=True):
        if request_token not in _record_tokens(record):
            continue
        contact_fields: list[str] = []
        if _classification_token(str(record["id"])) == request_token:
            contact_fields.append("id")
        if _classification_token(str(record["label"])) == request_token:
            contact_fields.append("label")
        if any(
            _classification_token(str(alias)) == request_token
            for alias in record["aliases"]
        ):
            contact_fields.append("allowed_aliases")
        if contact_fields:
            conflicts.append(conflict(record, line, contact_fields))
    if conflicts:
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=tuple(_normalize_findings(conflicts))
        )

    change = {
        "id": domain_id,
        "type": "domain",
        "label": domain_id,
        "parent": "",
        "allowed_aliases": [],
        "status": "active",
        "notes": "",
    }
    candidate_text = _append_rows(
        table,
        (
            _new_vocab_row(
                {"id": domain_id, "label": domain_id, "aliases": []},
                row_type="domain",
                parent="",
            ),
        ),
    )
    if validate_vocab(candidate_text):
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "VOCABULARY_DOMAIN_INSERTION_POST_INVALID",
                    _atlas_uri(VOCAB_PATH),
                ),
            ),
        )
    replay = prepare_vocabulary_domain_insertion_candidate(candidate_text, domain_id)
    if replay.state != "no-op":
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "VOCABULARY_DOMAIN_INSERTION_POST_INVALID",
                    _atlas_uri(VOCAB_PATH),
                ),
            ),
        )
    return TaxonomyBackfillCandidateResult(
        "candidate",
        preimage_revision="sha256:"
        + hashlib.sha256(vocab_text.encode("utf-8")).hexdigest(),
        output_revision="sha256:"
        + hashlib.sha256(candidate_text.encode("utf-8")).hexdigest(),
        preimage_text=vocab_text,
        text=candidate_text,
        changes=(change,),
    )


def prepare_vocabulary_subdomain_insertion_candidate(
    vocab_text: str,
    subdomain_id: str,
    parent_domain_id: str,
) -> TaxonomyBackfillCandidateResult:
    """Prepare one canonical subdomain insertion beneath an active domain."""
    argument_findings: list[Finding] = []
    for field, value in (
        ("subdomain_id", subdomain_id),
        ("parent_domain_id", parent_domain_id),
    ):
        if isinstance(value, str) and VOCAB_ID_RE.fullmatch(value):
            continue
        argument_findings.append(
            Finding(
                "VOCABULARY_SUBDOMAIN_INSERTION_ID_INVALID",
                f"args.{field}",
                row=str(value),
                detail=("expected exact lowercase kebab-case [a-z0-9][a-z0-9-]*"),
            )
        )
    if argument_findings:
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=tuple(_normalize_findings(argument_findings)),
        )

    table, records, findings = _validated_vocab(vocab_text)
    if findings:
        return TaxonomyBackfillCandidateResult("invalid", findings=tuple(findings))

    vocab_path = _atlas_uri(VOCAB_PATH)
    parent_record: Mapping[str, Any] | None = None
    parent_line: int | None = None
    for record, line in zip(records, table.row_lines, strict=True):
        if record["id"] == parent_domain_id:
            parent_record = record
            parent_line = line
            break
    if (
        parent_record is None
        or parent_record["type"] != "domain"
        or parent_record["parent"]
        or parent_record["status"] != "active"
    ):
        parent_detail = json.dumps(
            {
                "expected_parent": "",
                "expected_status": "active",
                "expected_type": "domain",
                "observed_parent": (
                    None if parent_record is None else str(parent_record["parent"])
                ),
                "observed_state": (
                    "missing" if parent_record is None else "incompatible"
                ),
                "observed_status": (
                    None if parent_record is None else str(parent_record["status"])
                ),
                "observed_type": (
                    None if parent_record is None else str(parent_record["type"])
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "VOCABULARY_SUBDOMAIN_INSERTION_PARENT_CONFLICT",
                    vocab_path,
                    line=parent_line,
                    row=parent_domain_id,
                    detail=parent_detail,
                ),
            ),
        )

    def conflict(
        record: Mapping[str, Any],
        line: int,
        contact_fields: Sequence[str],
    ) -> Finding:
        detail = json.dumps(
            {
                "contact_fields": sorted(set(contact_fields)),
                "expected_parent": parent_domain_id,
                "observed_id": str(record["id"]),
                "observed_parent": str(record["parent"]),
                "observed_status": str(record["status"]),
                "observed_type": str(record["type"]),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return Finding(
            "VOCABULARY_SUBDOMAIN_INSERTION_CONFLICT",
            vocab_path,
            line=line,
            row=subdomain_id,
            detail=detail,
        )

    for record, line in zip(records, table.row_lines, strict=True):
        if record["id"] != subdomain_id:
            continue
        if record["type"] == "subdomain" and record["parent"] == parent_domain_id:
            return TaxonomyBackfillCandidateResult("no-op")
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=(conflict(record, line, ("id",)),)
        )

    request_token = _classification_token(subdomain_id)
    conflicts: list[Finding] = []
    for record, line in zip(records, table.row_lines, strict=True):
        if request_token not in _record_tokens(record):
            continue
        contact_fields: list[str] = []
        if _classification_token(str(record["id"])) == request_token:
            contact_fields.append("id")
        if _classification_token(str(record["label"])) == request_token:
            contact_fields.append("label")
        if any(
            _classification_token(str(alias)) == request_token
            for alias in record["aliases"]
        ):
            contact_fields.append("allowed_aliases")
        if contact_fields:
            conflicts.append(conflict(record, line, contact_fields))
    if conflicts:
        return TaxonomyBackfillCandidateResult(
            "invalid", findings=tuple(_normalize_findings(conflicts))
        )

    change = {
        "id": subdomain_id,
        "type": "subdomain",
        "label": subdomain_id,
        "parent": parent_domain_id,
        "allowed_aliases": [],
        "status": "active",
        "notes": "",
    }
    candidate_text = _append_rows(
        table,
        (
            _new_vocab_row(
                {"id": subdomain_id, "label": subdomain_id, "aliases": []},
                row_type="subdomain",
                parent=parent_domain_id,
            ),
        ),
    )
    if validate_vocab(candidate_text):
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "VOCABULARY_SUBDOMAIN_INSERTION_POST_INVALID",
                    vocab_path,
                ),
            ),
        )
    replay = prepare_vocabulary_subdomain_insertion_candidate(
        candidate_text,
        subdomain_id,
        parent_domain_id,
    )
    if replay.state != "no-op" or replay.findings:
        return TaxonomyBackfillCandidateResult(
            "invalid",
            findings=(
                Finding(
                    "VOCABULARY_SUBDOMAIN_INSERTION_POST_INVALID",
                    vocab_path,
                ),
            ),
        )
    return TaxonomyBackfillCandidateResult(
        "candidate",
        preimage_revision="sha256:"
        + hashlib.sha256(vocab_text.encode("utf-8")).hexdigest(),
        output_revision="sha256:"
        + hashlib.sha256(candidate_text.encode("utf-8")).hexdigest(),
        preimage_text=vocab_text,
        text=candidate_text,
        changes=(change,),
    )


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
        common = {
            "version",
            "type",
            "mode",
            "source_id",
            "canonical_url",
            "artifact",
            "first_seen",
            "checked_on",
            "summarized_on",
            "content_hash",
            "refresh_after",
            "source_routing_sha256",
            "classification_action",
        }
        action = event.get("classification_action")
        required = common | (
            {"classification_input"}
            if action in {"replace", "mark-unclassified"}
            else set()
        )
        event_findings.extend(_require_event(event, required))
        if event.get("version") != 2:
            event_findings.extend(_event_error("EVENT_VERSION_INVALID", "expected 2"))
        mode = event.get("mode")
        if mode not in {"routine", "resummarize", "reroute", "promote"}:
            event_findings.extend(_event_error("EVENT_MODE_INVALID", str(mode)))
        if action not in {"preserve", "replace", "mark-unclassified"}:
            event_findings.extend(
                _event_error("EVENT_CLASSIFICATION_ACTION_INVALID", str(action))
            )
        if action == "preserve" and mode != "promote":
            event_findings.extend(
                _event_error(
                    "EVENT_CLASSIFICATION_ACTION_INVALID",
                    "preserve is legal only for promotion",
                )
            )
        source_id = event.get("source_id")
        canonical_url = event.get("canonical_url")
        artifact = event.get("artifact")
        content_hash = event.get("content_hash")
        routing_sha256 = event.get("source_routing_sha256")
        if not isinstance(source_id, str) or SOURCE_ID_RE.fullmatch(source_id) is None:
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
        if (
            not isinstance(content_hash, str)
            or CONTENT_HASH_RE.fullmatch(content_hash) is None
        ):
            event_findings.extend(
                _event_error("EVENT_CONTENT_HASH_INVALID", str(content_hash))
            )
        if (
            not isinstance(routing_sha256, str)
            or SEMANTIC_SHA256_RE.fullmatch(routing_sha256) is None
        ):
            event_findings.extend(
                _event_error("EVENT_SOURCE_ROUTING_SHA256_INVALID", str(routing_sha256))
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
        if len(parsed_dates) == 4 and not (
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
        routine_unchanged = (
            action == "replace"
            and mode == "routine"
            and existing_by_id is not None
            and event.get("artifact") == existing_by_id["Artifact"]
            and event.get("first_seen") == existing_by_id["First seen"]
            and event.get("summarized_on") == existing_by_id["Last summarized"]
            and event.get("content_hash") == existing_by_id["Content hash"]
            and event.get("source_routing_sha256")
            == existing_by_id["Source routing SHA-256"]
            and event.get("refresh_after") == existing_by_id["Refresh after"]
        )
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
        classification_derived: dict[str, Any] | None = None
        if action in {"replace", "mark-unclassified"}:
            classification_input = event.get("classification_input")
            if not isinstance(classification_input, Mapping):
                if "classification_input" in event:
                    event_findings.extend(
                        _event_error(
                            "EVENT_CLASSIFICATION_INPUT_INVALID",
                            "classification_input must be an object",
                        )
                    )
            elif action == "replace":
                result = classification_input.get("result")
                if (
                    classification_input.get("version") != 1
                    or classification_input.get("status") != "classified"
                    or not isinstance(result, Mapping)
                ):
                    event_findings.extend(
                        _event_error(
                            "EVENT_CLASSIFICATION_INPUT_INVALID",
                            "replace requires classified input",
                        )
                    )
                else:
                    normalized, normalized_findings = normalize_source_classification(
                        result
                    )
                    event_findings.extend(normalized_findings)
                    if not normalized_findings and not routine_unchanged:
                        vocab_text = texts.get("vocab")
                        if vocab_text is None:
                            event_findings.extend(
                                _event_error(
                                    "VOCAB_DOCUMENT_REQUIRED",
                                    "source classification requires vocabulary",
                                )
                            )
                        else:
                            (
                                resolved_vocab,
                                classification_derived,
                                classification_findings,
                            ) = resolve_source_classification(vocab_text, result)
                            event_findings.extend(classification_findings)
                            if (
                                not classification_findings
                                and classification_derived is not None
                                and not classification_derived["primary_domain"]
                            ):
                                event_findings.extend(
                                    _event_error(
                                        "SOURCE_CLASSIFICATION_VOCAB_CONFLICT",
                                        "primary domain proposal is ambiguous or incompatible",
                                    )
                                )
                            elif (
                                not classification_findings
                                and resolved_vocab != vocab_text
                            ):
                                vocab_replacement = resolved_vocab
                                changed.add("vocab")
            else:
                if (
                    classification_input.get("version") != 1
                    or classification_input.get("status") != "semantic-unavailable"
                    or classification_input.get("disposition")
                    != "SOURCE_CLASSIFICATION_UNAVAILABLE"
                    or classification_input.get("reason")
                    not in {
                        "schema-invalid",
                        "required-fields-incomplete",
                        "semantic-incomplete",
                    }
                ):
                    event_findings.extend(
                        _event_error(
                            "EVENT_CLASSIFICATION_INPUT_INVALID",
                            "mark-unclassified requires settled semantic unavailable input",
                        )
                    )
                else:
                    classification_derived = {
                        "classification_status": "unclassified",
                        "primary_domain": "",
                        "secondary_domains": [],
                        "subdomains": [],
                        "canonical_tags": [],
                        "routing_terms": [],
                        "candidate_terms": [],
                    }
        if event_findings:
            return _failed(texts, event_findings)
        assert (
            isinstance(source_id, str)
            and isinstance(canonical_url, str)
            and isinstance(artifact, str)
            and isinstance(content_hash, str)
            and isinstance(routing_sha256, str)
        )
        old_hash = existing_by_id["Content hash"] if existing_by_id is not None else ""
        old_routing = (
            existing_by_id["Source routing SHA-256"]
            if existing_by_id is not None
            else ""
        )
        if event_findings:
            return _failed(texts, event_findings)
        content_changed = is_new or old_hash != content_hash
        routing_changed = is_new or old_routing != routing_sha256
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
                "Source routing SHA-256": routing_sha256,
                "Refresh after": str(event["refresh_after"]),
                "Route status": (
                    "routing-blocked" if action == "mark-unclassified" else "unrouted"
                ),
                "Status": "active",
            }
            manifest_rows.append(source)
        else:
            assert existing_by_id is not None
            source = existing_by_id
            source["Last checked"] = str(event["checked_on"])
            source["Last summarized"] = str(event["summarized_on"])
            source["Content hash"] = content_hash
            source["Source routing SHA-256"] = routing_sha256
            source["Refresh after"] = str(event["refresh_after"])
            if content_changed or routing_changed:
                source["Route status"] = (
                    "routing-blocked" if action == "mark-unclassified" else "unrouted"
                )
                for topic in topic_rows:
                    pair = [
                        row
                        for row in relation_rows
                        if row["Source ID"] == source_id
                        and row["Topic ID"] == topic["Topic ID"]
                    ]
                    if not pair:
                        continue
                    tip, generation, frontier_findings = _select_relation_frontier(
                        relation_rows,
                        source_id=source_id,
                        topic_id=topic["Topic ID"],
                        current_source_hash=old_hash,
                        current_routing_sha256=old_routing,
                        current_scope_sha256=topic["Routing scope SHA-256"],
                    )
                    if frontier_findings or tip is None:
                        return _failed(texts, frontier_findings)
                    if tip["Status"] == "pending":
                        tip["Status"] = "superseded"
                    note_change = (
                        "content and routing semantic"
                        if content_changed and routing_changed
                        else "content"
                        if content_changed
                        else "routing semantic"
                    )
                    edge_id = _edge_id(
                        source_id,
                        topic["Topic ID"],
                        generation,
                        content_hash,
                        routing_sha256,
                        topic["Routing scope SHA-256"],
                    )
                    relation_rows.append(
                        {
                            "Edge ID": edge_id,
                            "Generation": str(generation),
                            "Source seq": source["Source seq"],
                            "Source ID": source_id,
                            "Source artifact": source["Artifact"],
                            "Source content hash": content_hash,
                            "Source routing SHA-256": routing_sha256,
                            "Topic ID": topic["Topic ID"],
                            "Topic scope SHA-256": topic["Routing scope SHA-256"],
                            "Work kind": "source-change",
                            "Prior edge ID": tip["Edge ID"],
                            "Relation": "",
                            "Impact": "",
                            "Confidence": "",
                            "Status": "pending",
                            "Created": str(event["checked_on"]),
                            "Applied in pass": "",
                            "Refresh disposition": "",
                            "Notes": (
                                f"Invalidates frontier {tip['Edge ID']} after source "
                                f"{note_change} change."
                            ),
                        }
                    )
                    changed.update({"relations", "topics"})
        manifest_rows.sort(key=lambda row: int(row["Source seq"]))
        if "relations" in changed:
            relation_rows.sort(
                key=lambda row: (
                    int(row["Source seq"]),
                    row["Topic ID"],
                    int(row["Generation"]),
                )
            )
            _recompute_topics(topic_rows, relation_rows)
        changed.add("manifest")
        source_derived = {
            "source": {
                "created": is_new,
                "content_changed": content_changed,
                "routing_changed": routing_changed,
                "source_seq": int(source["Source seq"]),
                "source_id": source_id,
                "canonical_url": canonical_url,
                "artifact": source["Artifact"],
                "first_seen": source["First seen"],
                "content_hash": source["Content hash"],
                "source_routing_sha256": source["Source routing SHA-256"],
                "route_status": source["Route status"],
                "status": source["Status"],
            }
        }
        if classification_derived is not None:
            source_derived["classification"] = classification_derived

    elif event_type == "topic-scope-upsert":
        event_findings.extend(
            _require_event(
                event,
                {
                    "version",
                    "type",
                    "topic_id",
                    "topic_path",
                    "aliases",
                    "canonical_tags",
                    "include_terms",
                    "exclude_terms",
                    "old_scope_sha256",
                    "new_scope_sha256",
                    "revised_on",
                },
            )
        )
        if event.get("version") != 1:
            event_findings.extend(_event_error("EVENT_VERSION_INVALID", "expected 1"))
        topic_id = event.get("topic_id")
        topic_path = event.get("topic_path")
        revised_on = event.get("revised_on")
        old_scope_sha256 = event.get("old_scope_sha256")
        new_scope_sha256 = event.get("new_scope_sha256")
        if not isinstance(topic_id, str) or not topic_id:
            event_findings.extend(_event_error("EVENT_TOPIC_INVALID", str(topic_id)))
        if not isinstance(topic_path, str) or not topic_path:
            event_findings.extend(
                _event_error("EVENT_TOPIC_PATH_INVALID", str(topic_path))
            )
        if not isinstance(revised_on, str) or DATE_RE.fullmatch(revised_on) is None:
            event_findings.extend(_event_error("EVENT_DATE_INVALID", str(revised_on)))
        else:
            try:
                date.fromisoformat(revised_on)
            except ValueError:
                event_findings.extend(
                    _event_error("EVENT_DATE_INVALID", str(revised_on))
                )
        for field_name, digest in (
            ("old_scope_sha256", old_scope_sha256),
            ("new_scope_sha256", new_scope_sha256),
        ):
            if (
                not isinstance(digest, str)
                or SEMANTIC_SHA256_RE.fullmatch(digest) is None
            ):
                event_findings.extend(
                    _event_error("EVENT_SCOPE_SHA256_INVALID", field_name)
                )
        scope_lists: dict[str, list[str]] = {}
        for field_name in (
            "aliases",
            "canonical_tags",
            "include_terms",
            "exclude_terms",
        ):
            value = event.get(field_name)
            if (
                type(value) is not list
                or any(
                    not isinstance(item, str) or not item or item != item.strip()
                    for item in value
                )
                or len(set(value)) != len(value)
                or value != sorted(value, key=lambda item: item.encode("utf-8"))
            ):
                event_findings.extend(
                    _event_error("EVENT_SCOPE_FIELD_INVALID", field_name)
                )
            else:
                scope_lists[field_name] = list(value)
        if event_findings:
            return _failed(texts, event_findings)
        assert isinstance(topic_id, str)
        topic = _topic_row(topic_rows, topic_id)
        if topic is None or topic["Freshness state"] == "archived":
            return _failed(
                texts,
                _event_error("EVENT_TOPIC_INVALID", topic_id),
            )
        if (
            topic["Topic path"] != topic_path
            or topic["Routing scope SHA-256"] != old_scope_sha256
        ):
            return _failed(
                texts,
                _event_error("EVENT_CURRENT_EVIDENCE", topic_id),
            )
        expected_new_scope = topic_routing_scope_sha256(
            {
                "topic_id": topic_id,
                "domain": topic["Domain"],
                "subdomain": topic["Subdomain"],
                "canonical_title": topic["Canonical title"],
                "aliases": scope_lists["aliases"],
                "canonical_tags": scope_lists["canonical_tags"],
                "include_terms": scope_lists["include_terms"],
                "exclude_terms": scope_lists["exclude_terms"],
            }
        )
        if expected_new_scope != new_scope_sha256:
            return _failed(
                texts,
                _event_error("EVENT_SCOPE_SHA256_INVALID", "new_scope_sha256"),
            )
        previous_scope = str(old_scope_sha256)
        topic["Aliases"] = _encode_registry_list(scope_lists["aliases"])
        topic["Canonical tags"] = _encode_registry_list(scope_lists["canonical_tags"])
        topic["Include terms"] = _encode_registry_list(scope_lists["include_terms"])
        topic["Exclude terms"] = _encode_registry_list(scope_lists["exclude_terms"])
        topic["Routing scope SHA-256"] = str(new_scope_sha256)
        changed.add("topics")
        if old_scope_sha256 != new_scope_sha256:
            manifest_by_id = {
                row["Source ID"]: row
                for row in manifest_rows
                if row["Status"] == "active"
            }
            source_ids = sorted(
                {
                    row["Source ID"]
                    for row in relation_rows
                    if row["Topic ID"] == topic_id
                }
            )
            for source_id in source_ids:
                source = manifest_by_id.get(source_id)
                if source is None:
                    return _failed(
                        texts,
                        _event_error("EVENT_CURRENT_EVIDENCE", source_id),
                    )
                tip, generation, frontier_findings = _select_relation_frontier(
                    relation_rows,
                    source_id=source_id,
                    topic_id=topic_id,
                    current_source_hash=source["Content hash"],
                    current_routing_sha256=source["Source routing SHA-256"],
                    current_scope_sha256=previous_scope,
                )
                if frontier_findings or tip is None:
                    return _failed(texts, frontier_findings)
                if tip["Status"] == "pending":
                    tip["Status"] = "superseded"
                edge_id = _edge_id(
                    source_id,
                    topic_id,
                    generation,
                    source["Content hash"],
                    source["Source routing SHA-256"],
                    str(new_scope_sha256),
                )
                relation_rows.append(
                    {
                        "Edge ID": edge_id,
                        "Generation": str(generation),
                        "Source seq": source["Source seq"],
                        "Source ID": source_id,
                        "Source artifact": source["Artifact"],
                        "Source content hash": source["Content hash"],
                        "Source routing SHA-256": source["Source routing SHA-256"],
                        "Topic ID": topic_id,
                        "Topic scope SHA-256": str(new_scope_sha256),
                        "Work kind": "scope-change",
                        "Prior edge ID": tip["Edge ID"],
                        "Relation": "",
                        "Impact": "",
                        "Confidence": "",
                        "Status": "pending",
                        "Created": str(revised_on),
                        "Applied in pass": "",
                        "Refresh disposition": "",
                        "Notes": (
                            f"Invalidates frontier {tip['Edge ID']} after topic "
                            "scope revision."
                        ),
                    }
                )
            relation_rows.sort(
                key=lambda row: (
                    int(row["Source seq"]),
                    row["Topic ID"],
                    int(row["Generation"]),
                )
            )
            _recompute_topics(topic_rows, relation_rows)
            changed.add("relations")

    elif event_type == "route-upsert":
        event_findings.extend(
            _require_event(
                event,
                {
                    "version",
                    "type",
                    "route_action",
                    "source_id",
                    "content_hash",
                    "source_routing_sha256",
                    "checked_on",
                    "outcome",
                    "edges",
                    "excluded_topic_ids",
                },
            )
        )
        if event.get("version") != 2:
            event_findings.extend(_event_error("EVENT_VERSION_INVALID", "expected 2"))
        route_action = event.get("route_action")
        if route_action not in {"candidate-route", "explicit-revalidation"}:
            event_findings.extend(
                _event_error("EVENT_ROUTE_ACTION_INVALID", str(route_action))
            )
        source_id = event.get("source_id")
        content_hash = event.get("content_hash")
        routing_sha256 = event.get("source_routing_sha256")
        checked_on = event.get("checked_on")
        outcome = event.get("outcome")
        edges = event.get("edges")
        excluded_topic_ids = event.get("excluded_topic_ids")
        if not isinstance(source_id, str) or SOURCE_ID_RE.fullmatch(source_id) is None:
            event_findings.extend(
                _event_error("EVENT_SOURCE_ID_INVALID", str(source_id))
            )
        if (
            not isinstance(content_hash, str)
            or CONTENT_HASH_RE.fullmatch(content_hash) is None
        ):
            event_findings.extend(
                _event_error("EVENT_CONTENT_HASH_INVALID", str(content_hash))
            )
        if (
            not isinstance(routing_sha256, str)
            or SEMANTIC_SHA256_RE.fullmatch(routing_sha256) is None
        ):
            event_findings.extend(
                _event_error("EVENT_SOURCE_ROUTING_SHA256_INVALID", str(routing_sha256))
            )
        if not isinstance(checked_on, str) or DATE_RE.fullmatch(checked_on) is None:
            event_findings.extend(_event_error("EVENT_DATE_INVALID", str(checked_on)))
        if outcome not in {"routed", "no-topic-match", "routing-blocked"}:
            event_findings.extend(_event_error("EVENT_OUTCOME_INVALID", str(outcome)))
        if not isinstance(edges, list):
            event_findings.extend(
                _event_error("EVENT_EDGES_INVALID", "edges must be an array")
            )
            edges = []
        if (
            not isinstance(excluded_topic_ids, list)
            or any(not isinstance(item, str) for item in excluded_topic_ids)
            or excluded_topic_ids != sorted(set(excluded_topic_ids))
        ):
            event_findings.extend(
                _event_error(
                    "EVENT_EXCLUDED_TOPICS_INVALID",
                    "excluded_topic_ids must be sorted unique text",
                )
            )
            excluded_topic_ids = []
        if route_action != "explicit-revalidation" and excluded_topic_ids:
            event_findings.extend(
                _event_error(
                    "EVENT_EXCLUSION_AUTHORITY_INVALID",
                    "only explicit revalidation may exclude",
                )
            )
        source = next(
            (row for row in manifest_rows if row["Source ID"] == source_id), None
        )
        if source is None:
            event_findings.extend(_event_error("EVENT_SOURCE_UNKNOWN", str(source_id)))
        elif source["Status"] == "archived":
            event_findings.extend(_event_error("EVENT_SOURCE_ARCHIVED", str(source_id)))
        elif (
            content_hash != source["Content hash"]
            or routing_sha256 != source["Source routing SHA-256"]
        ):
            event_findings.extend(
                _event_error("EVENT_SOURCE_IDENTITY_MISMATCH", str(source_id))
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
            if set(edge) != expected:
                event_findings.extend(
                    _event_error("EVENT_EDGE_INVALID", "edge keys are invalid", row_id)
                )
                continue
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
            if not any(item.row == row_id for item in event_findings):
                normalized_edges.append({name: str(edge[name]) for name in expected})
        if included_topics.intersection(excluded_topic_ids):
            event_findings.extend(
                _event_error(
                    "EVENT_TOPIC_DECISION_CONFLICT",
                    "included and excluded topics must be disjoint",
                )
            )
        for topic_id in excluded_topic_ids:
            if _topic_row(topic_rows, topic_id) is None:
                event_findings.extend(_event_error("EVENT_TOPIC_UNKNOWN", topic_id))
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
            and isinstance(routing_sha256, str)
            and isinstance(checked_on, str)
        )
        relation_changed = False
        for edge in normalized_edges:
            topic = _topic_row(topic_rows, edge["topic_id"])
            assert topic is not None
            tip, generation, frontier_findings = _select_relation_frontier(
                relation_rows,
                source_id=source_id,
                topic_id=edge["topic_id"],
                current_source_hash=content_hash,
                current_routing_sha256=routing_sha256,
                current_scope_sha256=topic["Routing scope SHA-256"],
            )
            if frontier_findings:
                return _failed(texts, frontier_findings)
            verifier_equal = (
                tip is not None
                and tip["Work kind"] == "evidence"
                and tip["Relation"] == edge["relation"]
                and tip["Impact"] == edge["impact"]
                and tip["Confidence"] == edge["confidence"]
                and _registry_decode_scalar(tip["Notes"]) == edge["reason"]
            )
            if tip is not None and tip["Work kind"] == "evidence":
                if route_action == "candidate-route":
                    return _failed(
                        texts,
                        _event_error(
                            "EVENT_CURRENT_EVIDENCE",
                            f"current evidence already exists for {edge['topic_id']}",
                        ),
                    )
                if verifier_equal:
                    continue
            if (
                tip is not None
                and tip["Status"] == "pending"
                and tip["Work kind"] != "evidence"
            ):
                tip.update(
                    {
                        "Work kind": "evidence",
                        "Relation": edge["relation"],
                        "Impact": edge["impact"],
                        "Confidence": edge["confidence"],
                        "Notes": edge["reason"],
                    }
                )
                relation_changed = True
                continue
            if tip is not None and tip["Status"] == "pending":
                tip["Status"] = "superseded"
            generation_value = 0 if tip is None else generation
            edge_id = _edge_id(
                source_id,
                edge["topic_id"],
                generation_value,
                content_hash,
                routing_sha256,
                topic["Routing scope SHA-256"],
            )
            relation_rows.append(
                {
                    "Edge ID": edge_id,
                    "Generation": str(generation_value),
                    "Source seq": source["Source seq"],
                    "Source ID": source_id,
                    "Source artifact": source["Artifact"],
                    "Source content hash": content_hash,
                    "Source routing SHA-256": routing_sha256,
                    "Topic ID": edge["topic_id"],
                    "Topic scope SHA-256": topic["Routing scope SHA-256"],
                    "Work kind": "evidence",
                    "Prior edge ID": "" if tip is None else tip["Edge ID"],
                    "Relation": edge["relation"],
                    "Impact": edge["impact"],
                    "Confidence": edge["confidence"],
                    "Status": "pending",
                    "Created": checked_on,
                    "Applied in pass": "",
                    "Refresh disposition": "",
                    "Notes": edge["reason"],
                }
            )
            relation_changed = True
        for topic_id in excluded_topic_ids:
            topic = _topic_row(topic_rows, topic_id)
            assert topic is not None
            tip, generation, frontier_findings = _select_relation_frontier(
                relation_rows,
                source_id=source_id,
                topic_id=topic_id,
                current_source_hash=content_hash,
                current_routing_sha256=routing_sha256,
                current_scope_sha256=topic["Routing scope SHA-256"],
            )
            if frontier_findings:
                return _failed(texts, frontier_findings)
            if tip is None or tip["Work kind"] != "evidence":
                continue
            if tip["Status"] == "pending":
                tip["Status"] = "superseded"
            edge_id = _edge_id(
                source_id,
                topic_id,
                generation,
                content_hash,
                routing_sha256,
                topic["Routing scope SHA-256"],
            )
            relation_rows.append(
                {
                    "Edge ID": edge_id,
                    "Generation": str(generation),
                    "Source seq": source["Source seq"],
                    "Source ID": source_id,
                    "Source artifact": source["Artifact"],
                    "Source content hash": content_hash,
                    "Source routing SHA-256": routing_sha256,
                    "Topic ID": topic_id,
                    "Topic scope SHA-256": topic["Routing scope SHA-256"],
                    "Work kind": "verifier-invalidation",
                    "Prior edge ID": tip["Edge ID"],
                    "Relation": "",
                    "Impact": "",
                    "Confidence": "",
                    "Status": "pending",
                    "Created": checked_on,
                    "Applied in pass": "",
                    "Refresh disposition": "",
                    "Notes": (
                        f"Invalidates frontier {tip['Edge ID']} after explicit "
                        "verifier exclusion."
                    ),
                }
            )
            relation_changed = True
        has_exact_evidence = False
        pair_topic_ids = sorted(
            {row["Topic ID"] for row in relation_rows if row["Source ID"] == source_id}
        )
        for topic_id in pair_topic_ids:
            topic = _topic_row(topic_rows, topic_id)
            assert topic is not None
            tip, _, frontier_findings = _select_relation_frontier(
                relation_rows,
                source_id=source_id,
                topic_id=topic_id,
                current_source_hash=content_hash,
                current_routing_sha256=routing_sha256,
                current_scope_sha256=topic["Routing scope SHA-256"],
            )
            if frontier_findings:
                return _failed(texts, frontier_findings)
            if (
                tip is not None
                and tip["Work kind"] == "evidence"
                and tip["Status"] in {"pending", "applied"}
            ):
                has_exact_evidence = True
                break
        next_route_status = "routed" if has_exact_evidence else str(outcome)
        if source["Route status"] != next_route_status:
            source["Route status"] = next_route_status
            changed.add("manifest")
        if relation_changed:
            relation_rows.sort(
                key=lambda row: (
                    int(row["Source seq"]),
                    row["Topic ID"],
                    int(row["Generation"]),
                )
            )
            _recompute_topics(topic_rows, relation_rows)
            changed.update({"topics", "relations"})

    elif event_type == "refresh-start":
        event_findings.extend(
            _require_event(
                event,
                {
                    "version",
                    "type",
                    "topic_id",
                    "inspection_sha256",
                    "expected_revisions",
                    "dispositions",
                    "started_at",
                },
            )
        )
        if event.get("version") != 2:
            event_findings.extend(_event_error("EVENT_VERSION_INVALID", "expected 2"))
        topic_id = event.get("topic_id")
        started_at = event.get("started_at")
        topic = (
            _topic_row(topic_rows, str(topic_id)) if isinstance(topic_id, str) else None
        )
        if topic is None:
            event_findings.extend(_event_error("EVENT_TOPIC_UNKNOWN", str(topic_id)))
        if not isinstance(started_at, str) or not started_at:
            event_findings.extend(
                _event_error("EVENT_STARTED_AT_INVALID", str(started_at))
            )
        _, _, refresh_findings = _validate_refresh_event(
            texts,
            relation_rows,
            event,
            str(topic_id),
            allow_applied=False,
        )
        event_findings.extend(refresh_findings)
        if event_findings:
            return _failed(texts, event_findings)
        assert topic is not None
        if topic["Freshness state"] != "refreshing":
            topic["Freshness state"] = "refreshing"
            changed.add("topics")

    elif event_type == "refresh-complete":
        event_findings.extend(
            _require_event(
                event,
                {
                    "version",
                    "type",
                    "topic_id",
                    "inspection_sha256",
                    "expected_revisions",
                    "dispositions",
                    "pass_path",
                    "completed_on",
                },
            )
        )
        if event.get("version") != 2:
            event_findings.extend(_event_error("EVENT_VERSION_INVALID", "expected 2"))
        topic_id = event.get("topic_id")
        pass_path = event.get("pass_path")
        completed_on = event.get("completed_on")
        topic = (
            _topic_row(topic_rows, str(topic_id)) if isinstance(topic_id, str) else None
        )
        if topic is None:
            event_findings.extend(_event_error("EVENT_TOPIC_UNKNOWN", str(topic_id)))
        if not isinstance(pass_path, str) or not pass_path:
            event_findings.extend(
                _event_error("EVENT_PASS_PATH_INVALID", str(pass_path))
            )
        if not isinstance(completed_on, str) or not DATE_RE.fullmatch(completed_on):
            event_findings.extend(_event_error("EVENT_DATE_INVALID", str(completed_on)))
        dispositions, idempotent, refresh_findings = _validate_refresh_event(
            texts,
            relation_rows,
            event,
            str(topic_id),
            allow_applied=True,
            pass_path=pass_path if isinstance(pass_path, str) else None,
        )
        event_findings.extend(refresh_findings)
        if event_findings:
            return _failed(texts, event_findings)
        if not idempotent:
            by_id = {
                str(item["edge_id"]): str(item["disposition"]) for item in dispositions
            }
            for row in relation_rows:
                disposition = by_id.get(row["Edge ID"])
                if disposition is not None:
                    row["Status"] = "applied"
                    row["Applied in pass"] = str(pass_path)
                    row["Refresh disposition"] = disposition
            _recompute_topics(
                topic_rows,
                relation_rows,
                states={str(topic_id): "current"},
                synthesized={str(topic_id): str(completed_on)},
            )
            changed.update({"relations", "topics"})
            applied_edge_ids = list(by_id)

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
    for name, relative in {**PATHS, "vocab": VOCAB_PATH}.items():
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
