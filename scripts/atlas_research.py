from __future__ import annotations

import base64
import hashlib
import re
from datetime import date, datetime
from typing import Any, Mapping, Sequence

import atlas_index
import atlas_state
import atlas_transaction

VERSION = 1
OWNER_ID = "atlas-research-v1"
ROOT_URI = "vault://atlas/"
MANIFEST_URI = ROOT_URI + atlas_state.MANIFEST_PATH
TOPICS_URI = ROOT_URI + atlas_state.TOPICS_PATH
RELATIONS_URI = ROOT_URI + atlas_state.RELATIONS_PATH
TRANSACTION_ROOT = ".atlas/transactions/research"
REQUEST_FIELDS = {
    "version",
    "topic_id",
    "inspection_sha256",
    "pass_uri",
    "pass_text",
    "index_text",
    "completed_on",
}
PREPARED_FIELDS = {
    "version",
    "owner",
    "request",
    "request_sha256",
    "transaction_id",
    "attempt",
    "predecessor_sha256",
    "event_record",
    "targets",
}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
TOPIC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PASS_RELATIVE_RE = re.compile(
    r"^summaries/research/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*/"
    r"topics/[a-z0-9][a-z0-9-]*/passes/(\d{4}-\d{2}-\d{2})--"
    r"[a-z0-9][a-z0-9-]*\.md$"
)
TOPIC_INDEX_RE = re.compile(
    r"^summaries/research/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*/"
    r"topics/[a-z0-9][a-z0-9-]*/INDEX\.md$"
)
SUBDOMAIN_INDEX_RE = re.compile(
    r"^summaries/research/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*/INDEX\.md$"
)


class ResearchError(ValueError):
    def __init__(self, code: str, path: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.path = path
        self.detail = detail


def _canonical_json(value: Any) -> bytes:
    return atlas_transaction.canonical_json(value)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _utf8(value: Any, path: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value):
        raise ResearchError("RESEARCH_INPUT_INVALID", path, "value must be text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID", path, "value is not valid UTF-8"
        ) from exc
    return value


def _request(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != REQUEST_FIELDS:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args",
            "research request fields are invalid",
        )
    result = dict(value)
    if type(result["version"]) is not int or result["version"] != VERSION:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID", "args.version", "version must be 1"
        )
    topic_id = _utf8(result["topic_id"], "args.topic_id")
    if TOPIC_ID_RE.fullmatch(topic_id) is None:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args.topic_id",
            "topic_id must be a normalized Atlas ID",
        )
    inspection_sha256 = _utf8(result["inspection_sha256"], "args.inspection_sha256")
    if HASH_RE.fullmatch(inspection_sha256) is None:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args.inspection_sha256",
            "inspection_sha256 must be lowercase SHA-256",
        )
    pass_uri = _utf8(result["pass_uri"], "args.pass_uri")
    _utf8(result["pass_text"], "args.pass_text")
    _utf8(result["index_text"], "args.index_text")
    completed_on = _utf8(result["completed_on"], "args.completed_on")
    try:
        parsed_date = date.fromisoformat(completed_on)
    except ValueError as exc:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args.completed_on",
            "completed_on must be a real YYYY-MM-DD date",
        ) from exc
    if str(parsed_date) != completed_on:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args.completed_on",
            "completed_on must be canonical YYYY-MM-DD",
        )
    if not pass_uri.startswith(ROOT_URI):
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args.pass_uri",
            "pass_uri must be under vault://atlas/",
        )
    relative = pass_uri.removeprefix(ROOT_URI)
    match = PASS_RELATIVE_RE.fullmatch(relative)
    if match is None or match.group(1) != completed_on:
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args.pass_uri",
            "pass_uri must be a dated pass matching completed_on",
        )
    return result


def _registry_documents(connector: Any) -> dict[str, str]:
    return {
        "manifest": connector.read_text(MANIFEST_URI),
        "topics": connector.read_text(TOPICS_URI),
        "relations": connector.read_text(RELATIONS_URI),
    }


def _snapshot(
    connector: Any, request: Mapping[str, Any]
) -> tuple[
    dict[str, Any],
    dict[str, str],
    dict[str, dict[str, Any]],
]:
    candidate_documents = _registry_documents(connector)
    try:
        candidate_selection = atlas_state.select_topic_state(
            candidate_documents, request["topic_id"]
        )
        candidate_paths = candidate_selection.paths_for("research")
    except atlas_state.TopicInspectionError as exc:
        raise ResearchError(exc.code, exc.path, exc.detail) from exc
    registry_uris = {
        "manifest": MANIFEST_URI,
        "topics": TOPICS_URI,
        "relations": RELATIONS_URI,
    }
    artifact_uris = {path: ROOT_URI + path for path in candidate_paths}
    uris = [
        *registry_uris.values(),
        *artifact_uris.values(),
    ]
    if candidate_selection.topic is not None:
        uris.append(request["pass_uri"])
    snapshot = connector.consistent_read(uris)
    decoded: dict[str, dict[str, Any]] = {}

    def decode(uri: str) -> None:
        entry = snapshot[uri]
        data, revision = entry.get("bytes"), entry.get("revision")
        if revision == "missing" and data is None:
            decoded[uri] = {"revision": "missing", "text": None}
            return
        if not isinstance(data, bytes) or not isinstance(revision, str):
            raise ResearchError(
                "RESEARCH_INSPECTION_UNAVAILABLE",
                uri,
                "consistent-read result is invalid",
            )
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ResearchError(
                "RESEARCH_INSPECTION_UNAVAILABLE",
                uri,
                "snapshot text is not valid UTF-8",
            ) from exc
        decoded[uri] = {"revision": revision, "text": text}

    for uri in registry_uris.values():
        decode(uri)
    documents: dict[str, str] = {}
    registry_revisions: dict[str, str] = {}
    for name, uri in registry_uris.items():
        entry = decoded[uri]
        if not isinstance(entry.get("text"), str):
            raise ResearchError(
                "RESEARCH_INSPECTION_UNAVAILABLE",
                uri,
                "registry snapshot is unavailable",
            )
        documents[name] = entry["text"]
        registry_revisions[name] = entry["revision"]
    try:
        locked_selection = atlas_state.select_topic_state(
            documents, request["topic_id"]
        )
        candidate_selection.require_locked_match(locked_selection)
    except atlas_state.TopicInspectionError as exc:
        raise ResearchError(exc.code, exc.path, exc.detail) from exc

    for uri in artifact_uris.values():
        decode(uri)
    if candidate_selection.topic is not None:
        decode(request["pass_uri"])
    artifacts = {path: decoded[uri] for path, uri in artifact_uris.items()}
    try:
        inspection = atlas_state.inspect_topic(
            documents,
            artifacts,
            request["topic_id"],
            "research",
            registry_revisions,
        )
    except atlas_state.TopicInspectionError as exc:
        raise ResearchError(exc.code, exc.path, exc.detail) from exc
    topic_path = inspection["topic"]["topic_path"]
    expected_pass_prefix = ROOT_URI + topic_path.removesuffix("INDEX.md") + "passes/"
    if not request["pass_uri"].startswith(expected_pass_prefix):
        raise ResearchError(
            "RESEARCH_INPUT_INVALID",
            "args.pass_uri",
            "pass_uri does not belong to the requested topic",
        )
    if snapshot[request["pass_uri"]]["revision"] != "missing":
        raise ResearchError(
            "RESEARCH_PASS_COLLISION",
            request["pass_uri"],
            "research pass target already exists",
        )
    if inspection["inspection_sha256"] != request["inspection_sha256"]:
        raise ResearchError(
            "RESEARCH_INSPECTION_STALE",
            "args.inspection_sha256",
            "inspection binding does not match current state",
        )
    if (
        inspection["freshness"]["freshness_state"] != "current"
        or inspection["pending_edge_ids"]
    ):
        raise ResearchError(
            "RESEARCH_NOT_ELIGIBLE",
            atlas_state.TOPICS_PATH,
            "research requires a current topic with zero pending edges",
        )
    return inspection, documents, artifacts


def _pass_document(
    text: str, request: Mapping[str, Any], topic: Mapping[str, Any]
) -> None:
    parsed = atlas_index._frontmatter(text)
    if parsed is None:
        raise ResearchError(
            "RESEARCH_PASS_INVALID", "args.pass_text", "pass frontmatter is invalid"
        )
    values, _, lines, _, close, _ = parsed
    expected_keys = {
        "schema_version",
        "note_type",
        "managed_by",
        "topic",
        "domain",
        "subdomain",
        "requested",
        "completed",
        "mode",
        "coverage_state",
        "confidence",
        "tags",
    }
    if set(values) != expected_keys:
        raise ResearchError(
            "RESEARCH_PASS_INVALID",
            "args.pass_text",
            "pass frontmatter keys are invalid",
        )
    expected = {
        "schema_version": "1",
        "note_type": "research-pass",
        "managed_by": "atlas",
        "topic": topic["topic_id"],
        "domain": topic["domain"],
        "subdomain": topic["subdomain"],
    }
    if any(
        values.get(key) != expected_value for key, expected_value in expected.items()
    ):
        raise ResearchError(
            "RESEARCH_PASS_INVALID",
            "args.pass_text",
            "pass identity does not match the inspected topic",
        )
    if values.get("mode") not in {"vault-only", "acquisition-first"}:
        raise ResearchError(
            "RESEARCH_PASS_INVALID", "args.pass_text", "pass mode is invalid"
        )
    if values.get("coverage_state") not in {
        "sufficient",
        "partial",
        "insufficient",
        "stale",
    } or values.get("confidence") not in {"high", "medium", "low"}:
        raise ResearchError(
            "RESEARCH_PASS_INVALID",
            "args.pass_text",
            "pass coverage or confidence is invalid",
        )
    if atlas_index._parse_json_array(values.get("tags", "")) is None:
        raise ResearchError(
            "RESEARCH_PASS_INVALID", "args.pass_text", "pass tags are invalid"
        )
    for key in ("requested", "completed"):
        raw = values.get(key, "")
        if not raw.endswith("Z"):
            raise ResearchError(
                "RESEARCH_PASS_INVALID",
                "args.pass_text",
                f"pass {key} must be an ISO-8601 UTC timestamp",
            )
        try:
            timestamp = datetime.fromisoformat(raw[:-1] + "+00:00")
        except ValueError as exc:
            raise ResearchError(
                "RESEARCH_PASS_INVALID",
                "args.pass_text",
                f"pass {key} must be an ISO-8601 UTC timestamp",
            ) from exc
        if (
            key == "completed"
            and timestamp.date().isoformat() != request["completed_on"]
        ):
            raise ResearchError(
                "RESEARCH_PASS_INVALID",
                "args.pass_text",
                "pass completed timestamp disagrees with completed_on",
            )
    bodies = [atlas_index._line_body(line).strip() for line in lines[close + 1 :]]
    required_headings = {
        "## Request",
        "## Mode",
        "## Coverage gate",
        "## Existing artifacts consulted",
        "## New source artifacts created",
        "## Findings",
        "## Changes applied to topic INDEX.md",
        "## Gaps left open",
        "## Next acquisition needs",
    }
    if not any(
        body.startswith("# ") for body in bodies
    ) or not required_headings.issubset(set(bodies)):
        raise ResearchError(
            "RESEARCH_PASS_INVALID",
            "args.pass_text",
            "pass headings are incomplete",
        )


def _topic_identity_request(
    topic: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "topic_id": topic["topic_id"],
        "domain": topic["domain"],
        "subdomain": topic["subdomain"],
        "canonical_title": topic["canonical_title"],
        "aliases": topic["aliases"],
        "canonical_tags": topic["canonical_tags"],
        "include_terms": topic["include_terms"],
        "exclude_terms": topic["exclude_terms"],
        "related_topic_ids": list(current["scope_values"]["Related topics"]),
        "status": current["values"]["status"],
    }


def _protected_topic(parsed: Mapping[str, Any]) -> tuple[str, ...]:
    lines = list(parsed["lines"])
    for index in range(1, len(lines)):
        body = atlas_index._line_body(lines[index])
        if ":" not in body:
            continue
        key = body.split(":", 1)[0].strip()
        if key in {"coverage_state", "confidence", "last_researched", "tags"}:
            ending = atlas_index._line_ending(lines[index], parsed["newline"])
            lines[index] = f"{key}: <research-managed>{ending}"
    result: list[str] = []
    cursor = 0
    for name in atlas_state.TOPIC_MANAGED_SECTIONS:
        start, end = parsed["pairs"][name]
        result.extend(lines[cursor : start + 1])
        result.append(f"<research-managed:{name}>\n")
        cursor = end
    result.extend(lines[cursor:])
    return tuple(result)


def _topic_candidate(
    current_text: str,
    candidate_text: str,
    request: Mapping[str, Any],
    topic: Mapping[str, Any],
) -> Mapping[str, Any]:
    current, current_error = atlas_index._parse_topic_document(current_text)
    candidate, candidate_error = atlas_index._parse_topic_document(candidate_text)
    if current_error or current is None:
        raise ResearchError(
            "RESEARCH_TOPIC_INVALID",
            topic["topic_path"],
            current_error or "invalid topic",
        )
    if candidate_error or candidate is None:
        raise ResearchError(
            "RESEARCH_TOPIC_INVALID",
            "args.index_text",
            candidate_error or "invalid topic",
        )
    identity_request = _topic_identity_request(topic, current)
    findings = atlas_index._topic_identity_findings(
        candidate, identity_request, conflict_code="RESEARCH_TOPIC_INVALID"
    )
    if findings:
        raise ResearchError(
            "RESEARCH_TOPIC_INVALID",
            findings[0].path,
            findings[0].detail,
        )
    if candidate["scope_values"] != current["scope_values"]:
        raise ResearchError(
            "RESEARCH_TOPIC_INVALID",
            "args.index_text",
            "scope-and-routing projection changed during research",
        )
    if candidate["read_next"] != current["read_next"]:
        raise ResearchError(
            "RESEARCH_TOPIC_INVALID",
            "args.index_text",
            "read-next projection changed during research",
        )
    for name in ("agent-answer-contract", "scope-and-routing", "read-next"):
        current_start, current_end = current["pairs"][name]
        candidate_start, candidate_end = candidate["pairs"][name]
        if (
            current["lines"][current_start + 1 : current_end]
            != candidate["lines"][candidate_start + 1 : candidate_end]
        ):
            raise ResearchError(
                "RESEARCH_TOPIC_INVALID",
                "args.index_text",
                f"managed contract section {name} changed during research",
            )
    if _protected_topic(current) != _protected_topic(candidate):
        raise ResearchError(
            "RESEARCH_TOPIC_INVALID",
            "args.index_text",
            "topic unmanaged content or structure changed",
        )
    if candidate["values"]["last_researched"] != request["completed_on"]:
        raise ResearchError(
            "RESEARCH_TOPIC_INVALID",
            "args.index_text",
            "topic last_researched disagrees with completed_on",
        )
    if candidate_text.encode("utf-8") == current_text.encode("utf-8"):
        raise ResearchError(
            "RESEARCH_TOPIC_UNCHANGED",
            "args.index_text",
            "research topic output is unchanged",
        )
    return candidate


def _coverage_without(value: str, title: str) -> str:
    parts = [
        (raw, decoded)
        for raw, decoded in atlas_index._projection_parts(value)
        if decoded != title
    ]
    return atlas_index._projection_source(parts).strip()


def _render_subdomain_research(
    current_text: str,
    topics_text: str,
    topic: Mapping[str, Any],
    candidate_topic: Mapping[str, Any],
    completed_on: str,
) -> str:
    request = {
        **_topic_identity_request(topic, candidate_topic),
        "created_on": completed_on,
        "_topics_text": topics_text,
    }
    parsed, findings = atlas_index._validate_subdomain(current_text, request)
    if findings or parsed is None:
        first = findings[0] if findings else None
        raise ResearchError(
            "RESEARCH_SUBDOMAIN_INVALID",
            topic["topic_path"],
            first.detail if first is not None else "subdomain index is invalid",
        )
    requested = parsed["topic_rows_by_id"].get(topic["topic_id"])
    if requested is None:
        raise ResearchError(
            "RESEARCH_SUBDOMAIN_INVALID",
            parsed["uri"],
            "topic projection is missing",
        )
    lines = list(parsed["lines"])
    newline = parsed["newline"]
    coverage = atlas_index._coverage_label(candidate_topic["values"]["coverage_state"])
    initial_answer = candidate_topic["current_answer"] == (
        atlas_state.INITIAL_CURRENT_ANSWER,
    )
    row_values = (
        topic["canonical_title"],
        "Research required" if initial_answer else "See topic answer",
        coverage,
        "Current",
        completed_on,
        topic["topic_path"],
    )
    lines[requested["line_index"]] = atlas_index._render_row(row_values, newline)

    for index in range(1, parsed["close"]):
        body = atlas_index._line_body(lines[index])
        if ":" not in body or body.split(":", 1)[0].strip() != "last_updated":
            continue
        raw_value = body.split(":", 1)[1]
        raw = raw_value.strip()
        quote = raw[0] if raw and raw[0] in "\"'" else ""
        replacement = quote + completed_on + quote if quote else completed_on
        leading = raw_value[: len(raw_value) - len(raw_value.lstrip())]
        trailing = raw_value[len(raw_value.rstrip()) :]
        lines[index] = (
            body[: body.index(":") + 1]
            + leading
            + replacement
            + trailing
            + atlas_index._line_ending(lines[index], newline)
        )
        break

    pairs, marker_error = atlas_index._marker_pairs(
        lines, atlas_state.SUBDOMAIN_MANAGED_SECTIONS
    )
    if marker_error:
        raise ResearchError("RESEARCH_SUBDOMAIN_INVALID", parsed["uri"], marker_error)
    coverage_start, coverage_end = pairs["coverage-map"]
    coverage_content = lines[coverage_start + 1 : coverage_end]
    for offset, line in enumerate(coverage_content):
        body = atlas_index._line_body(line)
        match = re.fullmatch(
            r"(- (Sufficient|Partial|Insufficient):)([ \t]*)(.*)", body
        )
        if match is None:
            continue
        label = match.group(2)
        value = _coverage_without(match.group(4), topic["canonical_title"])
        placeholder = atlas_index.COVERAGE_PLACEHOLDERS[label]
        if not value:
            value = placeholder
        if label == coverage:
            value = atlas_index._insert_sorted_value(
                value,
                topic["canonical_title"],
                topic["topic_id"],
                parsed["topic_rows"],
                placeholder=placeholder,
                bucket=label,
            )
        coverage_content[offset] = (
            match.group(1)
            + match.group(3)
            + value
            + atlas_index._line_ending(line, newline)
        )
    lines[coverage_start + 1 : coverage_end] = coverage_content

    pairs, marker_error = atlas_index._marker_pairs(
        lines, atlas_state.SUBDOMAIN_MANAGED_SECTIONS
    )
    if marker_error:
        raise ResearchError("RESEARCH_SUBDOMAIN_INVALID", parsed["uri"], marker_error)
    stale_start, stale_end = pairs["stale-or-weak-areas"]
    if coverage == "Sufficient":
        lines[stale_start + 1 : stale_end] = [
            line
            for line in lines[stale_start + 1 : stale_end]
            if not atlas_index._stale_entry_matches(
                atlas_index._line_body(line), topic["canonical_title"]
            )
        ]
    output = atlas_index._replace_lines_preserve_final(lines, parsed["final_newline"])
    output_parsed, output_findings = atlas_index._validate_subdomain(output, request)
    if output_findings or output_parsed is None:
        first = output_findings[0] if output_findings else None
        raise ResearchError(
            "RESEARCH_SUBDOMAIN_INVALID",
            parsed["uri"],
            first.detail if first is not None else "subdomain output is invalid",
        )
    projection = atlas_index._projection_findings(
        output_parsed,
        request,
        candidate_topic,
        {
            "Freshness state": "current",
        },
        conflict_code="RESEARCH_SUBDOMAIN_INVALID",
    )
    if projection:
        raise ResearchError(
            "RESEARCH_SUBDOMAIN_INVALID",
            projection[0].path,
            projection[0].detail,
        )
    if output == current_text:
        raise ResearchError(
            "RESEARCH_SUBDOMAIN_UNCHANGED",
            parsed["uri"],
            "subdomain projection output is unchanged",
        )
    return output


def _relative(uri: str) -> str:
    if not uri.startswith(ROOT_URI):
        raise ResearchError("RESEARCH_INPUT_INVALID", "uri", "URI is outside Atlas")
    return uri.removeprefix(ROOT_URI)


def _rank(path: str) -> tuple[int, str]:
    if PASS_RELATIVE_RE.fullmatch(path):
        return (0, path)
    if TOPIC_INDEX_RE.fullmatch(path):
        return (1, path)
    if SUBDOMAIN_INDEX_RE.fullmatch(path):
        return (2, path)
    if path == atlas_state.TOPICS_PATH:
        return (3, path)
    return (99, path)


def _allow(path: str) -> bool:
    return _rank(path)[0] < 99


def _identity(
    record: Mapping[str, Any], _: str
) -> atlas_transaction.TransactionIdentity:
    base = {
        "owner": OWNER_ID,
        "request_sha256": record["request_sha256"],
        "inspection_sha256": record["inspection_sha256"],
    }
    return atlas_transaction.TransactionIdentity(base, base)


def _event_validator(
    record: Mapping[str, Any],
    path: str,
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> Mapping[str, Any]:
    required = {
        "version",
        "owner",
        "request",
        "request_sha256",
        "inspection_sha256",
        "registry_input_sha256",
        "reducer_event",
        "target_paths",
        "output_sha256",
    }
    if (
        set(record) != required
        or type(record.get("version")) is not int
        or record.get("version") != VERSION
        or record.get("owner") != OWNER_ID
    ):
        raise atlas_transaction.TransactionRecordError(
            path, "research event fields are invalid"
        )
    request = _request(record.get("request"))
    request_sha256 = _sha256(_canonical_json(request))
    if request_sha256 != record.get("request_sha256") or request[
        "inspection_sha256"
    ] != record.get("inspection_sha256"):
        raise atlas_transaction.TransactionRecordError(
            path, "research event request binding is invalid"
        )
    target_paths = [target.path for target in targets]
    if target_paths != record.get("target_paths"):
        raise atlas_transaction.TransactionRecordError(
            path, "research target set is invalid"
        )
    output_sha256 = {target.path: _sha256(target.output_bytes) for target in targets}
    if output_sha256 != record.get("output_sha256"):
        raise atlas_transaction.TransactionRecordError(
            path, "research output binding is invalid"
        )
    if target_paths != sorted(target_paths, key=_rank) or len(target_paths) != 4:
        raise atlas_transaction.TransactionRecordError(
            path, "research target order is invalid"
        )
    return record


def _policy() -> atlas_transaction.TransactionPolicy:
    return atlas_transaction.TransactionPolicy(
        owner_id=OWNER_ID,
        target_allowlist=_allow,
        target_rank=_rank,
        identity_binding=_identity,
        event_validator=_event_validator,
        transaction_root=TRANSACTION_ROOT,
    )


def _plan(
    event_record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
    *,
    attempt: int = 0,
    predecessor_sha256: str | None = None,
) -> atlas_transaction.TransactionPlan:
    provisional = atlas_transaction.build_transaction_plan(
        event_path="pending/event.json",
        event_record=event_record,
        targets=targets,
        target_allowlist=_allow,
        target_rank=_rank,
        identity_binding=_identity,
        attempt=attempt,
        predecessor_sha256=predecessor_sha256,
        transaction_root=TRANSACTION_ROOT,
    )
    return atlas_transaction.build_transaction_plan(
        event_path=(f"{TRANSACTION_ROOT}/{provisional.transaction_id}/event.json"),
        event_record=event_record,
        targets=targets,
        target_allowlist=_allow,
        target_rank=_rank,
        identity_binding=_identity,
        attempt=attempt,
        predecessor_sha256=predecessor_sha256,
        transaction_root=TRANSACTION_ROOT,
    )


def _prepared_value(
    request: Mapping[str, Any],
    event_record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "owner": OWNER_ID,
        "request": dict(request),
        "request_sha256": event_record["request_sha256"],
        "transaction_id": plan.transaction_id,
        "attempt": plan.attempt,
        "predecessor_sha256": plan.predecessor_sha256,
        "event_record": dict(event_record),
        "targets": [
            {
                "path": target.path,
                "input_base64": (
                    None
                    if target.input_bytes is None
                    else base64.b64encode(target.input_bytes).decode("ascii")
                ),
                "output_base64": base64.b64encode(target.output_bytes).decode("ascii"),
            }
            for target in plan.targets
        ],
    }


def _decode_prepared(
    value: Any,
) -> tuple[dict[str, Any], Mapping[str, Any], atlas_transaction.TransactionPlan]:
    if not isinstance(value, Mapping) or set(value) != PREPARED_FIELDS:
        raise ResearchError(
            "RESEARCH_PREPARED_INVALID", "args.prepared", "prepared fields are invalid"
        )
    if value.get("version") != VERSION or value.get("owner") != OWNER_ID:
        raise ResearchError(
            "RESEARCH_PREPARED_INVALID", "args.prepared", "prepared identity is invalid"
        )
    request = _request(value.get("request"))
    request_sha256 = _sha256(_canonical_json(request))
    if value.get("request_sha256") != request_sha256:
        raise ResearchError(
            "RESEARCH_PREPARED_INVALID",
            "args.prepared",
            "prepared request hash is invalid",
        )
    event_record = value.get("event_record")
    rows = value.get("targets")
    if not isinstance(event_record, Mapping) or type(rows) is not list:
        raise ResearchError(
            "RESEARCH_PREPARED_INVALID",
            "args.prepared",
            "prepared transaction is invalid",
        )
    targets: list[atlas_transaction.TransactionTarget] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {
            "path",
            "input_base64",
            "output_base64",
        }:
            raise ResearchError(
                "RESEARCH_PREPARED_INVALID",
                f"args.prepared.targets[{index}]",
                "prepared target is invalid",
            )
        path = row["path"]
        input_base64 = row["input_base64"]
        output_base64 = row["output_base64"]
        if (
            not isinstance(path, str)
            or (input_base64 is not None and not isinstance(input_base64, str))
            or not isinstance(output_base64, str)
        ):
            raise ResearchError(
                "RESEARCH_PREPARED_INVALID",
                f"args.prepared.targets[{index}]",
                "prepared target values are invalid",
            )
        try:
            input_bytes = (
                None
                if input_base64 is None
                else base64.b64decode(input_base64, validate=True)
            )
            output_bytes = base64.b64decode(output_base64, validate=True)
        except (TypeError, ValueError) as exc:
            raise ResearchError(
                "RESEARCH_PREPARED_INVALID",
                f"args.prepared.targets[{index}]",
                "prepared target bytes are invalid",
            ) from exc
        targets.append(
            atlas_transaction.TransactionTarget(path, input_bytes, output_bytes)
        )
    attempt = value.get("attempt")
    predecessor_value = value.get("predecessor_sha256")
    if type(attempt) is not int or attempt not in {0, 1}:
        raise ResearchError(
            "RESEARCH_PREPARED_INVALID",
            "args.prepared.attempt",
            "prepared attempt is invalid",
        )
    predecessor_sha256: str | None
    if attempt == 0:
        if predecessor_value is not None:
            raise ResearchError(
                "RESEARCH_PREPARED_INVALID",
                "args.prepared.predecessor_sha256",
                "prepared predecessor binding is invalid",
            )
        predecessor_sha256 = None
    else:
        if (
            not isinstance(predecessor_value, str)
            or HASH_RE.fullmatch(predecessor_value) is None
        ):
            raise ResearchError(
                "RESEARCH_PREPARED_INVALID",
                "args.prepared.predecessor_sha256",
                "prepared predecessor binding is invalid",
            )
        predecessor_sha256 = predecessor_value
    try:
        plan = _plan(
            event_record,
            targets,
            attempt=attempt,
            predecessor_sha256=predecessor_sha256,
        )
        _event_validator(event_record, "args.prepared.event_record", plan.targets)
    except (atlas_transaction.TransactionError, ResearchError) as exc:
        raise ResearchError(
            "RESEARCH_PREPARED_INVALID", "args.prepared", str(exc)
        ) from exc
    if value.get("transaction_id") != plan.transaction_id:
        raise ResearchError(
            "RESEARCH_PREPARED_INVALID",
            "args.prepared.transaction_id",
            "prepared transaction ID is invalid",
        )
    return request, event_record, plan


def _derive_projection(
    connector: Any, request: Mapping[str, Any]
) -> tuple[dict[str, Any], tuple[atlas_transaction.TransactionTarget, ...]]:
    inspection, documents, artifacts = _snapshot(connector, request)
    topic = inspection["topic"]
    topic_path = topic["topic_path"]
    subdomain_path = (
        f"summaries/research/{topic['domain']}/{topic['subdomain']}/INDEX.md"
    )
    current_topic = artifacts[topic_path]["text"]
    current_subdomain = artifacts[subdomain_path]["text"]
    assert isinstance(current_topic, str) and isinstance(current_subdomain, str)
    _pass_document(request["pass_text"], request, topic)
    candidate_topic = _topic_candidate(
        current_topic, request["index_text"], request, topic
    )
    rank_findings = atlas_state.validate_answer_authoring(
        current_topic,
        request["index_text"],
        inspection["relations"],
        path="args.index_text",
    )
    if rank_findings:
        first = rank_findings[0]
        raise ResearchError(first.code, first.path, first.detail)
    candidate_subdomain = _render_subdomain_research(
        current_subdomain,
        documents["topics"],
        topic,
        candidate_topic,
        request["completed_on"],
    )
    pass_path = _relative(request["pass_uri"])
    pass_bytes = request["pass_text"].encode("utf-8")
    topic_bytes = request["index_text"].encode("utf-8")
    subdomain_bytes = candidate_subdomain.encode("utf-8")
    reducer_event = {
        "type": "research-complete",
        "topic_id": request["topic_id"],
        "inspection_sha256": request["inspection_sha256"],
        "pass_path": pass_path,
        "pass_sha256": _sha256(pass_bytes),
        "topic_index_sha256": _sha256(topic_bytes),
        "subdomain_index_sha256": _sha256(subdomain_bytes),
        "completed_on": request["completed_on"],
    }
    reduced = atlas_state.reduce_event(documents, reducer_event)
    if not reduced.ok:
        first = reduced.findings[0]
        raise ResearchError(first.code, first.path, first.detail)
    if set(reduced.documents) != {"topics"}:
        raise ResearchError(
            "RESEARCH_TOPICS_UNCHANGED",
            atlas_state.TOPICS_PATH,
            "research completion must change only TOPICS.md",
        )
    topics_bytes = reduced.documents["topics"].encode("utf-8")
    targets = (
        atlas_transaction.TransactionTarget(pass_path, None, pass_bytes),
        atlas_transaction.TransactionTarget(
            topic_path, current_topic.encode("utf-8"), topic_bytes
        ),
        atlas_transaction.TransactionTarget(
            subdomain_path, current_subdomain.encode("utf-8"), subdomain_bytes
        ),
        atlas_transaction.TransactionTarget(
            atlas_state.TOPICS_PATH,
            documents["topics"].encode("utf-8"),
            topics_bytes,
        ),
    )
    request_sha256 = _sha256(_canonical_json(request))
    event_record = {
        "version": VERSION,
        "owner": OWNER_ID,
        "request": dict(request),
        "request_sha256": request_sha256,
        "inspection_sha256": request["inspection_sha256"],
        "registry_input_sha256": {
            "manifest": _sha256(documents["manifest"].encode("utf-8")),
            "relations": _sha256(documents["relations"].encode("utf-8")),
        },
        "reducer_event": reducer_event,
        "target_paths": [target.path for target in targets],
        "output_sha256": {
            target.path: _sha256(target.output_bytes) for target in targets
        },
    }
    return event_record, targets


def prepare(connector: Any, value: Any) -> dict[str, Any]:
    """Prepare one exact four-target research publication without writing."""
    request = _request(value)
    event_record, targets = _derive_projection(connector, request)
    plan = _plan(event_record, targets)
    return _prepared_value(request, event_record, plan)


def _post_validate(
    port: atlas_transaction.ConnectorPort,
    plan: atlas_transaction.TransactionPlan,
    record: Mapping[str, Any],
) -> None:
    target_by_path = {target.path: target for target in plan.targets}
    for target in plan.targets:
        if port.read(target.path) != target.output_bytes:
            raise atlas_transaction.TransactionError(
                f"research target acknowledgement mismatch: {target.path}"
            )
    manifest = port.read(atlas_state.MANIFEST_PATH)
    relations = port.read(atlas_state.RELATIONS_PATH)
    if manifest is None or relations is None:
        raise atlas_transaction.TransactionError("research registry input disappeared")
    if {
        "manifest": _sha256(manifest),
        "relations": _sha256(relations),
    } != record["registry_input_sha256"]:
        raise atlas_transaction.TransactionError(
            "research changed a non-target registry"
        )
    topics_target = target_by_path[atlas_state.TOPICS_PATH]
    assert topics_target.input_bytes is not None
    baseline_documents = {
        "manifest": manifest.decode("utf-8"),
        "topics": topics_target.input_bytes.decode("utf-8"),
        "relations": relations.decode("utf-8"),
    }
    reduced = atlas_state.reduce_event(baseline_documents, record["reducer_event"])
    if (
        not reduced.ok
        or reduced.documents.get("topics", "").encode("utf-8")
        != topics_target.output_bytes
    ):
        raise atlas_transaction.TransactionError(
            "research TOPICS.md output is not reducer-derived"
        )
    request = record["request"]
    inspection, _, _, _ = _snapshot_from_targets(record, plan)
    topic = inspection["topic"]
    topic_target = plan.targets[1]
    subdomain_target = plan.targets[2]
    assert (
        topic_target.input_bytes is not None
        and subdomain_target.input_bytes is not None
    )
    candidate = _topic_candidate(
        topic_target.input_bytes.decode("utf-8"),
        topic_target.output_bytes.decode("utf-8"),
        request,
        topic,
    )
    expected_subdomain = _render_subdomain_research(
        subdomain_target.input_bytes.decode("utf-8"),
        baseline_documents["topics"],
        topic,
        candidate,
        request["completed_on"],
    ).encode("utf-8")
    if expected_subdomain != subdomain_target.output_bytes:
        raise atlas_transaction.TransactionError(
            "research subdomain projection is not deterministic"
        )
    _pass_document(plan.targets[0].output_bytes.decode("utf-8"), request, topic)


def _snapshot_from_targets(
    record: Mapping[str, Any], plan: atlas_transaction.TransactionPlan
) -> tuple[dict[str, Any], None, None, None]:
    request = record["request"]
    topic_path = plan.targets[1].path
    parts = topic_path.split("/")
    topic = {
        "topic_id": request["topic_id"],
        "topic_path": topic_path,
        "domain": parts[2],
        "subdomain": parts[3],
        "canonical_title": "",
        "aliases": [],
        "canonical_tags": [],
        "include_terms": [],
        "exclude_terms": [],
    }
    topic_input = plan.targets[1].input_bytes
    if topic_input is None:
        raise atlas_transaction.TransactionError("research topic input is missing")
    parsed, error = atlas_index._parse_topic_document(topic_input.decode("utf-8"))
    if error or parsed is None:
        raise atlas_transaction.TransactionError("research topic input is invalid")
    topic["canonical_title"] = parsed["heading"]
    topic["aliases"] = parsed["aliases"]
    topic["canonical_tags"] = parsed["tags"]
    topic["include_terms"] = parsed["scope_values"]["Include"]
    topic["exclude_terms"] = parsed["scope_values"]["Exclude"]
    return {"topic": topic}, None, None, None


def _result(
    connector: Any,
    port: atlas_transaction.LogicalConnectorPort,
    record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
    status: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "transaction_id": plan.transaction_id,
        "request_sha256": record["request_sha256"],
    }
    if status == "applied":
        result["revisions"] = {
            target.path: connector.revision(ROOT_URI + target.path)
            for target in plan.targets
        }
        return result
    if status not in {"aborted", "rolled-back"} or plan.attempt != 0:
        return result
    journal = atlas_transaction.load_transaction(port, plan.transaction_id, _policy())
    if journal.terminal is None:
        raise atlas_transaction.TransactionError(
            "research successor requires a terminal record"
        )
    successor = atlas_transaction.build_successor_plan(
        plan,
        event_path=(
            f"{TRANSACTION_ROOT}/{plan.base_transaction_id}-a000001/event.json"
        ),
        event_record=record,
        terminal_record=journal.terminal,
        target_allowlist=_allow,
        target_rank=_rank,
        identity_binding=_identity,
    )
    atlas_transaction.store_event(port, TRANSACTION_ROOT, record, successor)
    prepared = _prepared_value(record["request"], record, successor)
    result["next"] = {
        "operation": "research.execute",
        "args": {"prepared": prepared},
    }
    return result


def execute(connector: Any, value: Any) -> dict[str, Any]:
    """Execute one prepared research publication under the shared journal."""
    request, record, plan = _decode_prepared(value)
    with connector.mutation_session():
        derived_record, derived_targets = _derive_projection(connector, request)
        if (
            _canonical_json(record) != _canonical_json(derived_record)
            or tuple(plan.targets) != derived_targets
        ):
            raise ResearchError(
                "RESEARCH_PREPARED_INVALID",
                "args.prepared",
                (
                    "prepared projection does not match the validated request "
                    "and current snapshot"
                ),
            )
        port = atlas_transaction.LogicalConnectorPort(connector)
        atlas_transaction.store_event(port, TRANSACTION_ROOT, record, plan)
        status = atlas_transaction.execute_transaction(
            port,
            TRANSACTION_ROOT,
            plan,
            target_allowlist=_allow,
            target_rank=_rank,
            post_validator=lambda current_port, current_plan: _post_validate(
                current_port, current_plan, record
            ),
        )
        return _result(connector, port, record, plan, status)


def recover(connector: Any, transaction_id: Any, request_value: Any) -> dict[str, Any]:
    """Recover one exact research request without rebasing its semantics."""
    request = _request(request_value)
    if not isinstance(transaction_id, str):
        raise ResearchError(
            "RESEARCH_RECOVERY_INVALID",
            "args.transaction_id",
            "transaction_id must be text",
        )
    with connector.mutation_session():
        port = atlas_transaction.LogicalConnectorPort(connector)
        journal = atlas_transaction.load_transaction(port, transaction_id, _policy())
        if journal.record.get("request") != request:
            raise ResearchError(
                "RESEARCH_RECOVERY_INVALID",
                "args.request",
                "recovery request is not byte-identical to the journal request",
            )
        status = atlas_transaction.recover_transaction(
            port,
            TRANSACTION_ROOT,
            journal.plan,
            abort_unprepared=True,
            target_allowlist=_allow,
            target_rank=_rank,
            post_validator=lambda current_port, current_plan: _post_validate(
                current_port, current_plan, journal.record
            ),
        )
        return _result(connector, port, journal.record, journal.plan, status)
