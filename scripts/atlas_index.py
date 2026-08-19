#!/usr/bin/env python3
"""Pure deterministic planning for Atlas topic create-or-confirm.

This module deliberately owns no connector or transaction mechanics.  It accepts
complete registry/index snapshots as text and returns either stable findings, a
compatible-existing confirmation, or a byte-only three-target plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import base64
import hashlib
import json
import re
import unicodedata
from typing import Any, Mapping, Sequence

import atlas_state


VERSION = 1
ROOT_URI = "vault://atlas/"
MANIFEST_URI = ROOT_URI + atlas_state.MANIFEST_PATH
TOPICS_URI = ROOT_URI + atlas_state.TOPICS_PATH
RELATIONS_URI = ROOT_URI + atlas_state.RELATIONS_PATH

TOPIC_CREATE_EVENT_TYPE = "topic-create"
TOPIC_FRESHNESS = "current"
FRESHNESS_WINDOW = "P90D"
TOPIC_REFRESH_MODEL = "same-as-topic-creation"
TOPIC_STATUS = "active"
TOPIC_COVERAGE = "insufficient"
TOPIC_CONFIDENCE = "low"
TOPIC_OWNER_ID = "atlas-index-topic-create-v1"

REQUEST_FIELDS = frozenset(
    {
        "version",
        "topic_id",
        "topic_path",
        "domain",
        "subdomain",
        "canonical_title",
        "aliases",
        "include_terms",
        "exclude_terms",
        "related_topic_ids",
        "status",
        "coverage_state",
        "confidence",
        "refresh_model",
        "created_on",
    }
)

TOPIC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URI_RE = re.compile(
    r"^vault://atlas/summaries/research/([^/]+)/([^/]+)/topics/([^/]+)/INDEX\.md$"
)
TOPIC_REL_RE = re.compile(
    r"^summaries/research/([^/]+)/([^/]+)/topics/([^/]+)/INDEX\.md$"
)
TOPIC_LINK_RE = re.compile(
    r"(?:vault://atlas/)?summaries/research/([^/]+)/([^/]+)/topics/([^/]+)/INDEX\.md$"
)
COVERAGE_PLACEHOLDERS = {
    "Sufficient": "<topics with usable current answers>",
    "Partial": "<topics with known gaps>",
    "Insufficient": "<topics needing acquisition>",
}


SUBDOMAIN_MARKERS = atlas_state.SUBDOMAIN_MANAGED_SECTIONS
TOPIC_MARKERS = atlas_state.TOPIC_MANAGED_SECTIONS
SUBDOMAIN_TOPIC_MAP_HEADER = (
    "Topic",
    "Default answer",
    "Coverage",
    "Freshness",
    "Last updated",
    "Link",
)

# ``None`` is the public missing-topic representation.  The sentinel is useful
# to callers that want to distinguish an omitted argument from an explicit None
# while preserving the same pure owner semantics.
MISSING = object()


class _FrozenList(list[Any]):
    """A JSON-compatible list that cannot be mutated after construction."""

    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("immutable Atlas owner value")

    __delitem__ = __setitem__ = append = clear = extend = insert = pop = remove = (
        reverse
    ) = sort = _immutable

    def __iadd__(self, value: Any) -> _FrozenList:
        self._immutable(value)
        return self

    def __imul__(self, value: Any) -> _FrozenList:
        self._immutable(value)
        return self


class _FrozenDict(dict[str, Any]):
    """A JSON-compatible mapping that cannot be mutated after construction."""

    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("immutable Atlas owner value")

    __delitem__ = __setitem__ = clear = pop = popitem = setdefault = update = _immutable

    def __ior__(self, value: Any) -> _FrozenDict:
        self._immutable(value)
        return self


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _FrozenDict({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return _FrozenList(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _frozen_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    return _freeze(value)


@dataclass(frozen=True)
class TopicTarget:
    """One owner-produced target; connector revisions are intentionally absent."""

    path: str
    input_bytes: bytes | None
    output_bytes: bytes

    @property
    def output_sha256(self) -> str:
        return hashlib.sha256(self.output_bytes).hexdigest()

    @property
    def input_sha256(self) -> str | None:
        return (
            None
            if self.input_bytes is None
            else hashlib.sha256(self.input_bytes).hexdigest()
        )

    @property
    def output_revision(self) -> str:
        return "sha256:" + self.output_sha256


@dataclass(frozen=True)
class TopicValidation:
    ok: bool
    findings: tuple[atlas_state.Finding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "findings": [item.to_dict() for item in self.findings]}


@dataclass(frozen=True)
class TopicPostValidation:
    """Inputs retained for the façade's pre-terminal owner validation seam."""

    request: Mapping[str, Any]
    request_sha256: str
    expected_topic_bytes: bytes
    expected_subdomain_bytes: bytes
    expected_topics_bytes: bytes
    baseline_findings: tuple[atlas_state.Finding, ...]

    def __call__(
        self,
        manifest_text: str,
        topics_text: str,
        relations_text: str,
        subdomain_text: str,
        topic_text: str,
    ) -> tuple[atlas_state.Finding, ...]:
        return self.validate(
            manifest_text,
            topics_text,
            relations_text,
            subdomain_text,
            topic_text,
        )

    def validate(
        self,
        manifest_text: str,
        topics_text: str,
        relations_text: str,
        subdomain_text: str,
        topic_text: str,
    ) -> tuple[atlas_state.Finding, ...]:
        return validate_topic_post_state(
            self.request,
            manifest_text,
            topics_text,
            relations_text,
            subdomain_text,
            topic_text,
            expected_topic_bytes=self.expected_topic_bytes,
            expected_subdomain_bytes=self.expected_subdomain_bytes,
            expected_topics_bytes=self.expected_topics_bytes,
            baseline_findings=self.baseline_findings,
            request_sha256=self.request_sha256,
        )


@dataclass(frozen=True)
class TopicTransactionBinding:
    """Immutable owner binding reconstructed from a transaction event/intent."""

    request: Mapping[str, Any]
    request_sha256: str
    targets: tuple[TopicTarget, ...]
    owner_policy_version: str
    attempt: int
    predecessor_sha256: str | None
    post_validation: TopicPostValidation
    base_transaction_id: str = ""
    transaction_id: str = ""
    event_record_sha256: str = ""

    @property
    def target_paths(self) -> tuple[str, ...]:
        return tuple(target.path for target in self.targets)

    @property
    def input_sha256s(self) -> tuple[str | None, ...]:
        return tuple(target.input_sha256 for target in self.targets)

    @property
    def output_sha256s(self) -> tuple[str, ...]:
        return tuple(target.output_sha256 for target in self.targets)

    @property
    def post_validator(self) -> TopicPostValidation:
        return self.post_validation


@dataclass(frozen=True)
class TopicPlan:
    """Immutable pure-owner output for an absent topic."""

    request: Mapping[str, Any]
    request_sha256: str
    event_record: Mapping[str, Any]
    targets: tuple[TopicTarget, ...]
    post_validation: TopicPostValidation
    baseline_findings: tuple[atlas_state.Finding, ...]
    paths: Mapping[str, str]
    output_revisions: Mapping[str, str]

    state: str = "created"
    transaction: None = None
    receipt: None = None
    topic_namespace: str = ""
    base_transaction_id: str = ""

    @property
    def event(self) -> Mapping[str, Any]:
        return self.event_record

    @property
    def candidate_topic_bytes(self) -> bytes:
        return self.targets[0].output_bytes

    @property
    def candidate_subdomain_bytes(self) -> bytes:
        return self.targets[1].output_bytes

    @property
    def candidate_topics_bytes(self) -> bytes:
        return self.targets[2].output_bytes

    @property
    def post_validator(self) -> TopicPostValidation:
        return self.post_validation

    @property
    def output_hashes(self) -> Mapping[str, str]:
        return _frozen_mapping(
            {
                name: value.removeprefix("sha256:")
                for name, value in self.output_revisions.items()
            }
        )

    @property
    def output_bytes(self) -> tuple[bytes, ...]:
        return tuple(target.output_bytes for target in self.targets)

    @property
    def target_paths(self) -> tuple[str, ...]:
        return tuple(target.path for target in self.targets)

    @property
    def validation(self) -> TopicValidation:
        return TopicValidation(True, ())

    def validate_post_state(
        self,
        manifest_text: str,
        topics_text: str,
        relations_text: str,
        subdomain_text: str,
        topic_text: str,
    ) -> tuple[atlas_state.Finding, ...]:
        return self.post_validation.validate(
            manifest_text,
            topics_text,
            relations_text,
            subdomain_text,
            topic_text,
        )


@dataclass(frozen=True)
class TopicConfirmation:
    """Immutable compatible-existing no-op result."""

    request: Mapping[str, Any]
    request_sha256: str
    paths: Mapping[str, str]
    revisions: Mapping[str, str]
    validation: TopicValidation
    state: str = "confirmed"
    transaction: None = None
    receipt: None = None

    @property
    def targets(self) -> tuple[TopicTarget, ...]:
        return ()

    @property
    def current_revisions(self) -> Mapping[str, str]:
        return self.revisions

    @property
    def output_bytes(self) -> tuple[bytes, ...]:
        return ()


Findings = tuple[atlas_state.Finding, ...]
TopicResult = TopicConfirmation | TopicPlan | Findings


def canonical_json(value: Any) -> bytes:
    """Return the canonical JSON bytes used for owner request/event hashes."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def topic_namespace_sha256(request: Mapping[str, Any]) -> str:
    """Return the stable topic-identity namespace digest."""
    topic_id = request.get("topic_id")
    topic_path = request.get("topic_path")
    if not isinstance(topic_id, str) or not isinstance(topic_path, str):
        raise ValueError("topic namespace requires canonical topic identity")
    return sha256(
        canonical_json(
            {
                "owner": TOPIC_OWNER_ID,
                "topic_id": topic_id,
                "topic_path": topic_path,
            }
        )
    )


def topic_base_transaction_id(
    request: Mapping[str, Any], targets: Sequence[TopicTarget]
) -> str:
    """Return the input/output-bound topic base identity."""
    if len(targets) != 3:
        raise ValueError("topic transaction requires exactly three targets")
    input_identities = [target.input_sha256 for target in targets]
    output_hashes = [target.output_sha256 for target in targets]
    target_paths = [target.path for target in targets]
    return sha256(
        canonical_json(
            {
                "owner": TOPIC_OWNER_ID,
                "request_sha256": sha256(canonical_json(dict(request))),
                "target_paths": target_paths,
                "input_identities": input_identities,
                "output_sha256s": output_hashes,
            }
        )
    )[:16]


def topic_base_identity(
    event: Mapping[str, Any],
    _event_hash: str,
    targets: Sequence[Any],
) -> Mapping[str, Any]:
    """Return the exact input/output-bound base identity for the owner."""
    request = event.get("request")
    if not isinstance(request, Mapping):
        raise ValueError("topic event request is invalid")
    input_identities = [
        (None if target.input_bytes is None else sha256(target.input_bytes))
        for target in targets
    ]
    output_hashes = [sha256(target.output_bytes) for target in targets]
    return {
        "owner": TOPIC_OWNER_ID,
        "request_sha256": sha256(canonical_json(dict(request))),
        "target_paths": [target.path for target in targets],
        "input_identities": input_identities,
        "output_sha256s": output_hashes,
    }


def _sort_findings(items: Sequence[atlas_state.Finding]) -> Findings:
    unique = set(items)
    return tuple(
        sorted(
            unique,
            key=lambda item: (
                item.path,
                item.line if item.line is not None else -1,
                item.code,
                item.row or "",
                item.detail,
            ),
        )
    )


def _finding(
    code: str,
    path: str,
    detail: str = "",
    *,
    line: int | None = None,
    row: str | None = None,
) -> atlas_state.Finding:
    return atlas_state.Finding(code, path, line, row, detail)


def _uri(path: str) -> str:
    if path.startswith(ROOT_URI):
        return path
    return ROOT_URI + path.lstrip("/")


def _registry_invalid(findings: Sequence[atlas_state.Finding]) -> Findings:
    converted = []
    for item in findings:
        converted.append(
            _finding(
                "REGISTRY_INVALID",
                _uri(item.path),
                ": ".join(part for part in (item.code, item.detail) if part),
                line=item.line,
                row=item.row,
            )
        )
    return _sort_findings(converted)


_MARKDOWN_ESCAPABLE = frozenset("\\|;[]()")
_MARKDOWN_LINE_BOUNDARIES = frozenset("\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029")
_MARKDOWN_CONTROL_CATEGORIES = frozenset({"Cc", "Cf", "Zl", "Zp"})
_LIST_EMPTY_SENTINEL = "none"


def _is_markdown_control_boundary(value: str) -> bool:
    return (
        value in _MARKDOWN_LINE_BOUNDARIES
        or unicodedata.category(value) in _MARKDOWN_CONTROL_CATEGORIES
    )


def _unicode_escape(value: str) -> str:
    return f"\\u{{{ord(value):04x}}}"


def _encode_markdown_scalar(
    value: str,
    *,
    reserved: Sequence[str] = (),
    protect_literals: Sequence[str] = (),
) -> str:
    """Encode one scalar for a Markdown projection without lossy escapes.

    Backslash escapes are intentionally canonical: every literal backslash is
    doubled, while control/line-boundary characters use an explicit code-point
    token.  A decoder can therefore distinguish an input such as ``\\;`` from
    a semicolon escaped by this codec.  ``reserved`` is contextual syntax
    (table pipes, list semicolons, or link-label brackets).
    """

    reserved_chars = frozenset(reserved)
    protect = value in protect_literals
    encoded: list[str] = []
    for index, char in enumerate(value):
        if protect and index == 0:
            encoded.append(_unicode_escape(char))
        elif char == "\\":
            encoded.append("\\\\")
        elif _is_markdown_control_boundary(char):
            encoded.append(_unicode_escape(char))
        elif char in reserved_chars:
            encoded.append("\\" + char)
        else:
            encoded.append(char)
    return "".join(encoded)


def _decode_markdown_scalar(value: str) -> str:
    """Decode the scalar codec, retaining unknown legacy-looking escapes."""

    decoded: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            decoded.append(char)
            index += 1
            continue
        if index + 1 >= len(value):
            decoded.append("\\")
            index += 1
            continue
        next_char = value[index + 1]
        if next_char == "\\":
            decoded.append("\\")
            index += 2
            continue
        if next_char == "u" and value.startswith("\\u{", index):
            close = value.find("}", index + 3)
            if close != -1:
                digits = value[index + 3 : close]
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
        if next_char in _MARKDOWN_ESCAPABLE or not next_char.isalnum():
            decoded.append(next_char)
            index += 2
            continue
        # Unknown ``\\q``-style text is literal text, not an escape.
        decoded.append("\\")
        index += 1
    return "".join(decoded)


def _canonical_markdown_form(
    value: str,
    *,
    reserved: Sequence[str] = (),
    protect_literals: Sequence[str] = (),
) -> str:
    return _encode_markdown_scalar(
        value,
        reserved=reserved,
        protect_literals=protect_literals,
    )


def _raw_scalar_matches(
    raw: str,
    expected: str,
    *,
    reserved: Sequence[str] = (),
    protect_literals: Sequence[str] = (),
) -> bool:
    """Match only the canonical writer spelling for a managed identity."""

    source = raw.strip()
    canonical = _canonical_markdown_form(
        expected,
        reserved=reserved,
        protect_literals=protect_literals,
    )
    return source == canonical


def _raw_list_matches(
    raw: str,
    expected: Sequence[str],
    *,
    empty_legacy: str = "",
    reserved: Sequence[str] = (";",),
    protect_literals: Sequence[str] = (),
) -> bool:
    """Compare list syntax without accepting decoder-equivalent spellings."""

    source = raw.strip()
    if not expected:
        return source == empty_legacy
    parts = _projection_parts(source)
    if len(parts) != len(expected):
        return False
    if len(expected) == 1 and source == empty_legacy:
        return False
    return all(
        _raw_scalar_matches(
            part_raw,
            expected_value,
            reserved=reserved,
            protect_literals=protect_literals,
        )
        for (part_raw, _), expected_value in zip(parts, expected, strict=True)
    )


def _raw_table_list_matches(raw: str, expected: Sequence[str]) -> bool:
    """Compare a list after accounting for its enclosing Markdown table layer."""

    source = raw.strip()
    if not expected:
        return source == ""
    return _raw_list_matches(
        _decode_markdown_cell(source),
        expected,
        empty_legacy=_LIST_EMPTY_SENTINEL,
        reserved=(";",),
        protect_literals=(_LIST_EMPTY_SENTINEL,),
    )


def _raw_projection_parts(value: str) -> tuple[list[str], list[str]]:
    parts = _projection_parts(value)
    return [raw for raw, _ in parts], [decoded for _, decoded in parts]


def _list_projection_value(values: Sequence[str], *, empty: str) -> str:
    if not values:
        return empty
    return "; ".join(
        _encode_markdown_scalar(
            item,
            reserved=(";",),
            protect_literals=(_LIST_EMPTY_SENTINEL,),
        )
        for item in values
    )


def _utf8_string(
    value: Any, path: str, *, nonempty: bool = True
) -> list[atlas_state.Finding]:
    if not isinstance(value, str):
        return [_finding("INDEX_REQUEST_INVALID", path, "value must be a string")]
    if nonempty and not value:
        return [_finding("INDEX_REQUEST_INVALID", path, "value must be nonempty")]
    if value != value.strip():
        return [_finding("INDEX_REQUEST_INVALID", path, "value must be trimmed")]
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return [_finding("INDEX_REQUEST_INVALID", path, "value is not valid UTF-8")]
    return []


def _array_values(value: Any, path: str) -> tuple[list[str], list[atlas_state.Finding]]:
    if type(value) is not list:
        return [], [_finding("INDEX_REQUEST_INVALID", path, "value must be an array")]
    findings: list[atlas_state.Finding] = []
    values: list[str] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        item_findings = _utf8_string(item, item_path)
        findings.extend(item_findings)
        if not item_findings:
            values.append(item)
    if len(set(values)) != len(values):
        findings.append(
            _finding("INDEX_REQUEST_INVALID", path, "values must be unique")
        )
    if values != sorted(values, key=lambda item: item.encode("utf-8")):
        findings.append(
            _finding("INDEX_REQUEST_INVALID", path, "values must be UTF-8 byte ordered")
        )
    return values, findings


def _valid_date(value: Any, path: str) -> list[atlas_state.Finding]:
    findings = _utf8_string(value, path)
    if findings:
        return findings
    if DATE_RE.fullmatch(value) is None:
        return [_finding("INDEX_REQUEST_INVALID", path, "value must be YYYY-MM-DD")]
    try:
        date.fromisoformat(value)
    except ValueError:
        return [
            _finding("INDEX_REQUEST_INVALID", path, "value must be a real UTC date")
        ]
    return []


def _validate_request(request: Any) -> tuple[dict[str, Any] | None, Findings]:
    if not isinstance(request, Mapping):
        return None, (
            _finding("INDEX_REQUEST_INVALID", "args", "value must be an object"),
        )
    safe_fields: set[str] = set()
    invalid_key_shape = False
    for field in request:
        if not isinstance(field, str):
            invalid_key_shape = True
            continue
        try:
            encoded_field = str.encode(field, "utf-8")
        except UnicodeEncodeError:
            invalid_key_shape = True
            continue
        safe_fields.add(encoded_field.decode("utf-8"))

    findings: list[atlas_state.Finding] = []
    if invalid_key_shape:
        findings.append(
            _finding(
                "INDEX_REQUEST_INVALID",
                "args",
                "field names must be strings with valid UTF-8 encoding",
            )
        )
    for field in sorted(REQUEST_FIELDS - safe_fields):
        findings.append(
            _finding("INDEX_REQUEST_INVALID", f"args.{field}", "field is missing")
        )
    for field in sorted(safe_fields - REQUEST_FIELDS):
        findings.append(
            _finding("INDEX_REQUEST_INVALID", f"args.{field}", "field is unknown")
        )
    if findings:
        return None, _sort_findings(findings)

    value = dict(request)
    if type(value["version"]) is not int or value["version"] != VERSION:
        findings.append(
            _finding("INDEX_REQUEST_INVALID", "args.version", "version must be 1")
        )

    for field in ("topic_id", "domain", "subdomain"):
        findings.extend(_utf8_string(value[field], f"args.{field}"))
        if isinstance(value[field], str) and not TOPIC_ID_RE.fullmatch(value[field]):
            findings.append(
                _finding(
                    "INDEX_REQUEST_INVALID",
                    f"args.{field}",
                    "value is not a normalized Atlas ID",
                )
            )
    findings.extend(_utf8_string(value["canonical_title"], "args.canonical_title"))

    for field in ("aliases", "include_terms", "exclude_terms", "related_topic_ids"):
        values, array_findings = _array_values(value[field], f"args.{field}")
        value[field] = values
        findings.extend(array_findings)
        if field == "related_topic_ids":
            for index, item in enumerate(values):
                if not TOPIC_ID_RE.fullmatch(item):
                    findings.append(
                        _finding(
                            "INDEX_REQUEST_INVALID",
                            f"args.{field}[{index}]",
                            "value is not a normalized Atlas ID",
                        )
                    )

    for field, expected in (
        ("status", TOPIC_STATUS),
        ("coverage_state", TOPIC_COVERAGE),
        ("confidence", TOPIC_CONFIDENCE),
        ("refresh_model", TOPIC_REFRESH_MODEL),
    ):
        findings.extend(_utf8_string(value[field], f"args.{field}"))
        if isinstance(value[field], str) and value[field] != expected:
            findings.append(
                _finding(
                    "INDEX_REQUEST_INVALID",
                    f"args.{field}",
                    f"value must be {expected!r}",
                )
            )
    findings.extend(_valid_date(value["created_on"], "args.created_on"))

    if (
        isinstance(value["topic_id"], str)
        and isinstance(value["domain"], str)
        and isinstance(value["subdomain"], str)
    ):
        expected_topic_path = _topic_uri(
            value["domain"], value["subdomain"], value["topic_id"]
        )
        topic_path = value["topic_path"]
        findings.extend(_utf8_string(topic_path, "args.topic_path"))
        if isinstance(topic_path, str):
            match = URI_RE.fullmatch(topic_path)
            if match is None:
                findings.append(
                    _finding(
                        "INDEX_REQUEST_INVALID",
                        "args.topic_path",
                        "path is not a canonical Atlas topic URI",
                    )
                )
            elif topic_path != expected_topic_path:
                findings.append(
                    _finding(
                        "INDEX_REQUEST_INVALID",
                        "args.topic_path",
                        "path does not match topic identity",
                    )
                )
            if any(
                token in topic_path
                for token in ("?", "#", "\\", "%2f", "%2F", "%2e", "%2E")
            ):
                findings.append(
                    _finding(
                        "INDEX_REQUEST_INVALID",
                        "args.topic_path",
                        "path contains a forbidden query, fragment, or traversal",
                    )
                )
    else:
        findings.extend(_utf8_string(value["topic_path"], "args.topic_path"))

    if findings:
        return None, _sort_findings(findings)
    return value, ()


def _topic_uri(domain: str, subdomain: str, topic_id: str) -> str:
    return (
        f"{ROOT_URI}summaries/research/{domain}/{subdomain}/topics/{topic_id}/INDEX.md"
    )


def _subdomain_uri(domain: str, subdomain: str) -> str:
    return f"{ROOT_URI}summaries/research/{domain}/{subdomain}/INDEX.md"


def _topic_relative(domain: str, subdomain: str, topic_id: str) -> str:
    return _topic_uri(domain, subdomain, topic_id)[len(ROOT_URI) :]


def _detect_newline(text: str) -> str:
    return atlas_state._detect_newline(text)


def _line_body(line: str) -> str:
    return atlas_state._body(line)


def _line_ending(line: str, default: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return default


def _split_markdown_row(line: str) -> list[str] | None:
    """Parse one row while retaining canonical scalar escape sequences."""

    return atlas_state.split_markdown_row(line)


def _escape_markdown_cell(value: str) -> str:
    return _encode_markdown_scalar(value, reserved=("|",))


def _render_row(cells: Sequence[str], newline: str) -> str:
    return (
        "| "
        + " | ".join(_escape_markdown_cell(cell) for cell in cells)
        + " |"
        + newline
    )


def _decode_markdown_cell(value: str) -> str:
    return _decode_markdown_scalar(value)


def _topic_table_rows(table: atlas_state.ParsedTable) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cells in table.rows:
        raw = dict(zip(atlas_state.TOPICS_HEADER, cells, strict=True))
        decoded = dict(
            zip(
                atlas_state.TOPICS_HEADER,
                (_decode_markdown_cell(cell) for cell in cells),
                strict=True,
            )
        )
        decoded["_raw"] = raw
        rows.append(decoded)
    return rows


def _replace_lines_preserve_final(lines: list[str], final_newline: bool) -> str:
    text = "".join(lines)
    if not final_newline and text.endswith(("\r\n", "\n", "\r")):
        if text.endswith("\r\n"):
            text = text[:-2]
        else:
            text = text[:-1]
    return text


def _frontmatter(
    text: str,
) -> (
    tuple[
        dict[str, str],
        dict[str, str],
        list[str],
        int,
        int,
        str,
    ]
    | None
):
    lines = text.splitlines(keepends=True)
    if not lines or _line_body(lines[0]) != "---":
        return None
    close = None
    for index in range(1, len(lines)):
        if _line_body(lines[index]) == "---":
            close = index
            break
    if close is None:
        return None
    values: dict[str, str] = {}
    raw_values: dict[str, str] = {}
    for line in lines[1:close]:
        body = _line_body(line)
        if not body.strip() or body.lstrip().startswith("#") or ":" not in body:
            return None
        key, raw = body.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if not key or key in values:
            return None
        raw_values[key] = raw
        values[key] = _yaml_scalar(raw)
    return values, raw_values, lines, 0, close, _detect_newline(text)


def _yaml_scalar(raw: str) -> str:
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        if raw[0] == '"':
            try:
                value = json.loads(raw)
                return value if isinstance(value, str) else raw
            except json.JSONDecodeError:
                return raw
        return raw[1:-1]
    return raw


def _parse_json_array(raw: str) -> list[str] | None:
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None
    if type(value) is not list or any(not isinstance(item, str) for item in value):
        return None
    return value


def _marker_pairs(
    lines: Sequence[str], names: Sequence[str]
) -> tuple[dict[str, tuple[int, int]], str | None]:
    starts: dict[str, list[int]] = {name: [] for name in names}
    ends: dict[str, list[int]] = {name: [] for name in names}
    expected = set(names)
    marker_re = re.compile(r"^<!-- atlas:managed:(start|end) ([a-z0-9-]+) -->$")
    marker_prefix_re = re.compile(r"^<!--\s*atlas:managed:")
    for index, line in enumerate(lines):
        body = _line_body(line).strip()
        if marker_prefix_re.match(body) is None:
            continue
        match = marker_re.fullmatch(body)
        if match is None or match.group(2) not in expected:
            return {}, f"invalid managed marker on line {index + 1}"
        (starts if match.group(1) == "start" else ends)[match.group(2)].append(index)
    pairs: dict[str, tuple[int, int]] = {}
    previous_end = -1
    for name in names:
        if len(starts[name]) != 1 or len(ends[name]) != 1:
            return {}, f"managed marker pair {name!r} must occur exactly once"
        start, end = starts[name][0], ends[name][0]
        if end <= start:
            return {}, f"managed marker pair {name!r} is not ordered"
        if start <= previous_end:
            return {}, f"managed marker pair {name!r} overlaps or is out of sequence"
        pairs[name] = (start, end)
        previous_end = end
    return pairs, None


def _topic_map_link_classification(
    row: Mapping[str, Any],
    canonical_rows: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any],
    uri: str,
) -> tuple[str | None, Mapping[str, Any] | None, bool, atlas_state.Finding | None]:
    """Classify one topic-map Link before any owner plan is produced.

    The decoded Link is the row's identity oracle.  Raw spelling is a
    separate compatibility dimension: only an unrelated, semantically
    resolved row may carry a decoder-equivalent spelling as baseline drift.
    """

    link = row["cells"][5]
    match = TOPIC_LINK_RE.fullmatch(link)
    topic_id = match.group(3) if match else None
    if topic_id is None or TOPIC_ID_RE.fullmatch(topic_id) is None:
        return (
            None,
            None,
            False,
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID",
                uri,
                "topic-map link is not canonical",
                row=str(row["raw_cells"][5]),
            ),
        )
    canonical = canonical_rows.get(topic_id)
    if canonical is None:
        return (
            topic_id,
            None,
            False,
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID",
                uri,
                "topic-map link has no canonical TOPICS.md row",
                row=topic_id,
            ),
        )
    expected_link = _canonical_related_topic_path(canonical)
    if expected_link is None:
        return (
            topic_id,
            canonical,
            False,
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID",
                uri,
                "topic-map link has no canonical topic path",
                row=topic_id,
            ),
        )
    decoded_link = link.removeprefix(ROOT_URI)
    if decoded_link != expected_link:
        return (
            topic_id,
            canonical,
            False,
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID",
                uri,
                "topic-map link disagrees with canonical topic identity",
                row=topic_id,
            ),
        )
    raw_canonical = _raw_scalar_matches(
        row["raw_cells"][5], expected_link, reserved=("|",)
    )
    requested_id = request.get("topic_id")
    related_ids = request.get("related_topic_ids", ())
    role = (
        "requested"
        if topic_id == requested_id
        else "related"
        if topic_id in related_ids
        else "other"
    )
    if role in {"requested", "related"} and not raw_canonical:
        return (
            topic_id,
            canonical,
            raw_canonical,
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                uri,
                "topic-map Link is not canonically encoded",
                row=topic_id,
            ),
        )
    return topic_id, canonical, raw_canonical, None


def _topic_map_identity_role(
    topic_id: str,
    request: Mapping[str, Any],
) -> str:
    if topic_id == request.get("topic_id"):
        return "requested"
    if topic_id in request.get("related_topic_ids", ()):
        return "related"
    return "other"


def _validate_subdomain(
    text: Any,
    request: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, Findings]:
    uri = _subdomain_uri(request["domain"], request["subdomain"])
    if not isinstance(text, str) or not text:
        return None, (
            _finding("SUBDOMAIN_INVALID", uri, "subdomain INDEX.md is missing"),
        )
    parsed = _frontmatter(text)
    if parsed is None:
        return None, (_finding("SUBDOMAIN_INVALID", uri, "frontmatter is invalid"),)
    values, _, lines, _, close, newline = parsed
    expected_keys = {
        "schema_version",
        "note_type",
        "managed_by",
        "domain",
        "subdomain",
        "last_updated",
        "tags",
    }
    if set(values) != expected_keys:
        return None, (
            _finding(
                "SUBDOMAIN_INVALID",
                uri,
                "frontmatter keys are not the canonical subdomain shape",
            ),
        )
    if (
        values.get("schema_version") != "1"
        or values.get("note_type") != "subdomain-index"
        or values.get("managed_by") != "atlas"
    ):
        return None, (
            _finding("SUBDOMAIN_INVALID", uri, "frontmatter identity is invalid"),
        )
    if (
        values.get("domain") != request["domain"]
        or values.get("subdomain") != request["subdomain"]
    ):
        return None, (
            _finding(
                "SUBDOMAIN_INVALID",
                uri,
                "frontmatter domain/subdomain does not match request",
            ),
        )
    if close < 1 or _line_body(lines[1]) != "schema_version: 1":
        return None, (
            _finding(
                "SUBDOMAIN_INVALID",
                uri,
                "schema_version must be the unquoted integer 1",
            ),
        )
    if DATE_RE.fullmatch(values.get("last_updated", "")) is None:
        return None, (
            _finding("SUBDOMAIN_INVALID", uri, "last_updated is not YYYY-MM-DD"),
        )
    try:
        date.fromisoformat(values["last_updated"])
    except ValueError:
        return None, (
            _finding("SUBDOMAIN_INVALID", uri, "last_updated is not a real date"),
        )
    if _parse_json_array(values.get("tags", "")) is None:
        return None, (
            _finding("SUBDOMAIN_INVALID", uri, "tags must be a JSON string array"),
        )
    heading = next(
        (
            _line_body(line).strip()
            for line in lines[close + 1 :]
            if _line_body(line).strip().startswith("# ")
        ),
        "",
    )
    if not heading:
        return None, (
            _finding("SUBDOMAIN_INVALID", uri, "subdomain heading is missing"),
        )
    pairs, marker_error = _marker_pairs(lines, SUBDOMAIN_MARKERS)
    if marker_error:
        return None, (_finding("SUBDOMAIN_INVALID", uri, marker_error),)
    topic_start, topic_end = pairs["topic-map"]

    topic_content = lines[topic_start + 1 : topic_end]
    nonblank = [
        (index, line)
        for index, line in enumerate(topic_content)
        if _line_body(line).strip()
    ]
    if len(nonblank) < 2:
        return None, (
            _finding("SUBDOMAIN_PROJECTION_INVALID", uri, "topic-map table is missing"),
        )
    header = _split_markdown_row(nonblank[0][1])
    separator = _split_markdown_row(nonblank[1][1])
    if (
        tuple(header or ()) != SUBDOMAIN_TOPIC_MAP_HEADER
        or separator is None
        or not atlas_state._is_separator(separator, len(SUBDOMAIN_TOPIC_MAP_HEADER))
    ):
        return None, (
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID", uri, "topic-map table header is invalid"
            ),
        )
    topic_rows: list[dict[str, Any]] = []
    for relative_index, line in nonblank[2:]:
        raw_cells = _split_markdown_row(line)
        if raw_cells is None or len(raw_cells) != len(SUBDOMAIN_TOPIC_MAP_HEADER):
            return None, (
                _finding(
                    "SUBDOMAIN_PROJECTION_INVALID", uri, "topic-map row is invalid"
                ),
            )
        cells = tuple(_decode_markdown_cell(cell) for cell in raw_cells)
        link = cells[5]
        match = TOPIC_LINK_RE.fullmatch(link)
        topic_id = match.group(3) if match else None
        if topic_id is None or not TOPIC_ID_RE.fullmatch(topic_id):
            return None, (
                _finding(
                    "SUBDOMAIN_PROJECTION_INVALID",
                    uri,
                    "topic-map link is not canonical",
                    row=raw_cells[5],
                ),
            )
        topic_rows.append(
            {
                "id": topic_id,
                "cells": tuple(cells),
                "raw_cells": tuple(raw_cells),
                "line_index": topic_start + 1 + relative_index,
                "raw": line,
            }
        )
    if len({row["id"] for row in topic_rows}) != len(topic_rows):
        return None, (
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID",
                uri,
                "topic-map contains duplicate topic IDs",
            ),
        )

    sections: dict[str, list[str]] = {
        name: [_line_body(item) for item in lines[start + 1 : end]]
        for name, (start, end) in pairs.items()
    }
    coverage_lines = sections["coverage-map"]
    coverage_values: dict[str, tuple[int, str]] = {}
    for index, body in enumerate(coverage_lines):
        if not body.strip():
            continue
        match = re.fullmatch(r"- (Sufficient|Partial|Insufficient):(?: (.*))?", body)
        if match is None or match.group(1) in coverage_values:
            return None, (
                _finding(
                    "SUBDOMAIN_PROJECTION_INVALID", uri, "coverage-map is invalid"
                ),
            )
        coverage_values[match.group(1)] = (index, match.group(2) or "")
    if set(coverage_values) != {"Sufficient", "Partial", "Insufficient"}:
        return None, (
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID",
                uri,
                "coverage-map buckets are incomplete",
            ),
        )

    stale_lines = sections["stale-or-weak-areas"]
    for body in stale_lines:
        if body.strip() and not body.startswith("- "):
            return None, (
                _finding(
                    "SUBDOMAIN_PROJECTION_INVALID",
                    uri,
                    "stale-or-weak-areas is invalid",
                ),
            )

    # Every row is first resolved through its decoded Link.  Raw identity
    # spelling is strict for requested/authorized related rows and is
    # baseline drift only for a truly unrelated resolved row.
    topic_rows_by_id = {row["id"]: row for row in topic_rows}
    registry_table = atlas_state._parse_table("topics", request["_topics_text"])
    canonical_rows = {row["Topic ID"]: row for row in _topic_table_rows(registry_table)}
    baseline: list[atlas_state.Finding] = []
    for row in topic_rows:
        topic_id, canonical, raw_link_canonical, identity_error = (
            _topic_map_link_classification(row, canonical_rows, request, uri)
        )
        if identity_error is not None:
            return None, (identity_error,)
        assert topic_id is not None and canonical is not None
        role = _topic_map_identity_role(topic_id, request)
        raw_cells = row["raw_cells"]
        expected = {
            "Topic": (
                request["canonical_title"]
                if role == "requested"
                else _topic_row_semantic_title(canonical)
            ),
            "Freshness": _title_case(canonical["Freshness state"]),
            "Link": _canonical_related_topic_path(canonical),
        }
        assert expected["Link"] is not None
        identity_fields = (("Topic", 0), ("Link", 5))
        if role in {"requested", "related"}:
            for field, index in identity_fields:
                if not _raw_scalar_matches(
                    raw_cells[index], expected[field], reserved=("|",)
                ):
                    return None, (
                        _finding(
                            "TOPIC_COMPATIBILITY_CONFLICT",
                            uri,
                            f"{field} disagrees with canonical topic identity",
                            row=topic_id,
                        ),
                    )
            continue
        # Coverage and last-updated values require the topic INDEX.md, which
        # is intentionally supplied only for the requested topic. Their
        # unrelated values are therefore preserved as baseline bytes.
        drift = not raw_link_canonical
        for field, index in (("Topic", 0), ("Freshness", 3)):
            if not _raw_scalar_matches(
                raw_cells[index], expected[field], reserved=("|",)
            ):
                drift = True
                break
        if drift:
            baseline.append(
                _finding(
                    "SUBDOMAIN_TOPIC_MAP_DRIFT",
                    uri,
                    "topic-map row differs from canonical TOPICS.md",
                    row=topic_id,
                )
            )

    return {
        "values": values,
        "lines": lines,
        "close": close,
        "newline": newline,
        "final_newline": text.endswith(("\n", "\r")),
        "pairs": pairs,
        "topic_rows": topic_rows,
        "coverage_values": coverage_values,
        "sections": sections,
        "baseline": _sort_findings(baseline),
        "uri": uri,
        "topic_rows_by_id": topic_rows_by_id,
    }, ()


def _title_case(value: str) -> str:
    return value[:1].upper() + value[1:] if value else value


def _coverage_label(state: str, *_: str) -> str:
    return {
        "sufficient": "Sufficient",
        "partial": "Partial",
        "insufficient": "Insufficient",
        "stale": "Insufficient",
    }.get(state, state)


def _canonical_related_topic_path(row: Mapping[str, str]) -> str | None:
    topic_id = row.get("Topic ID")
    domain = row.get("Domain")
    subdomain = row.get("Subdomain")
    if not all(isinstance(value, str) for value in (topic_id, domain, subdomain)):
        return None
    if any(
        TOPIC_ID_RE.fullmatch(value) is None for value in (topic_id, domain, subdomain)
    ):
        return None
    return _topic_relative(domain, subdomain, topic_id)


def _validate_event_request(
    request: Any,
    topics_text: Any,
    *,
    require_absent: bool = False,
) -> tuple[dict[str, Any] | None, Findings]:
    """Validate an immutable event request without connector access."""

    normalized, request_findings = _validate_request(request)
    if request_findings:
        return None, request_findings
    assert normalized is not None
    if not isinstance(topics_text, str):
        return None, (
            _finding(
                "REGISTRY_INVALID",
                TOPICS_URI,
                "TOPICS.md snapshot must be text",
            ),
        )
    table = atlas_state._parse_table("topics", topics_text)
    if table.findings:
        return None, _registry_invalid(table.findings)
    topic_shape_findings, _ = atlas_state._validate_topics_shape(table)
    if topic_shape_findings:
        return None, _registry_invalid(topic_shape_findings)
    rows = _topic_table_rows(table)
    topic_by_id = {row["Topic ID"]: row for row in rows}
    if require_absent:
        _, identity_findings = _topic_row_for_request(table, normalized)
        requested_rows = [
            row
            for row in rows
            if row["Topic ID"] == normalized["topic_id"]
            or row["Topic path"]
            in {
                _topic_relative(
                    normalized["domain"],
                    normalized["subdomain"],
                    normalized["topic_id"],
                ),
                normalized["topic_path"],
            }
        ]
        if identity_findings:
            findings = list(identity_findings)
        elif requested_rows:
            findings = [
                _finding(
                    "TOPIC_ORPHAN",
                    TOPICS_URI,
                    "embedded event input does not prove the requested topic is absent",
                    row=normalized["topic_id"],
                )
            ]
        else:
            findings = []
        if findings:
            return None, _sort_findings(findings)
    findings: list[atlas_state.Finding] = []
    topic_id = normalized["topic_id"]
    for index, item in enumerate(normalized["related_topic_ids"]):
        path = f"args.related_topic_ids[{index}]"
        if item == topic_id:
            findings.append(
                _finding(
                    "RELATED_TOPIC_SELF",
                    path,
                    "related topics must not include topic_id",
                    row=topic_id,
                )
            )
            continue
        related_row = topic_by_id.get(item)
        if related_row is None:
            findings.append(
                _finding(
                    "RELATED_TOPIC_UNKNOWN",
                    path,
                    "related topic ID is not present in TOPICS.md",
                    row=item,
                )
            )
            continue
        expected_path = _canonical_related_topic_path(related_row)
        canonical = (
            expected_path is not None
            and _raw_scalar_matches(
                _topic_row_raw(related_row, "Topic ID"),
                related_row["Topic ID"],
                reserved=("|",),
            )
            and _raw_scalar_matches(
                _topic_row_raw(related_row, "Domain"),
                related_row["Domain"],
                reserved=("|",),
            )
            and _raw_scalar_matches(
                _topic_row_raw(related_row, "Subdomain"),
                related_row["Subdomain"],
                reserved=("|",),
            )
            and _raw_scalar_matches(
                _topic_row_raw(related_row, "Topic path"),
                expected_path,
                reserved=("|",),
            )
        )
        if not canonical:
            findings.append(
                _finding(
                    "TOPIC_COMPATIBILITY_CONFLICT",
                    TOPICS_URI,
                    "related topic path disagrees with its canonical identity",
                    row=item,
                )
            )
    if findings:
        return None, _sort_findings(findings)
    return normalized, ()


def _topic_binding_invalid(detail: str) -> Findings:
    return (_finding("TRANSACTION_RECORD_INVALID", "event_record", detail),)


def load_topic_binding(
    event_record: Any,
    intent_record_or_missing: Any,
) -> TopicTransactionBinding | Findings:
    """Reconstruct and validate an immutable topic transaction owner binding."""

    if not isinstance(event_record, Mapping):
        return _topic_binding_invalid("topic event record is invalid")
    outer = event_record
    owner_record = outer.get("event_record") if "event_record" in outer else outer
    if not isinstance(owner_record, Mapping):
        return _topic_binding_invalid("topic event owner record is invalid")
    required = {
        "version",
        "event_type",
        "owner",
        "topic_namespace_sha256",
        "base_transaction_id",
        "request_sha256",
        "request",
    }
    if set(owner_record) != required:
        return _topic_binding_invalid("topic event owner fields are invalid")
    request = owner_record.get("request")
    if (
        type(owner_record.get("version")) is not int
        or owner_record["version"] != VERSION
        or owner_record["event_type"] != TOPIC_CREATE_EVENT_TYPE
        or owner_record["owner"] != TOPIC_OWNER_ID
        or not isinstance(request, Mapping)
    ):
        return _topic_binding_invalid("topic event owner identity is invalid")
    try:
        request_value = json.loads(canonical_json(request).decode("utf-8"))
    except (TypeError, ValueError, UnicodeError):
        return _topic_binding_invalid("embedded topic request is not canonical")
    normalized, request_findings = _validate_request(request_value)
    if (
        request_findings
        or normalized is None
        or normalized != request_value
        or request_value != request
    ):
        return _topic_binding_invalid("embedded topic request is invalid")
    request = normalized
    try:
        request_sha256 = sha256(canonical_json(request))
        namespace = topic_namespace_sha256(request)
    except (TypeError, ValueError, UnicodeError):
        return _topic_binding_invalid("embedded topic request is not canonical")
    if (
        owner_record.get("request_sha256") != request_sha256
        or owner_record.get("topic_namespace_sha256") != namespace
        or not isinstance(owner_record.get("base_transaction_id"), str)
        or re.fullmatch(r"[0-9a-f]{16}", owner_record["base_transaction_id"]) is None
    ):
        return _topic_binding_invalid("topic event identity does not match request")

    target_rows = outer.get("targets")
    if not isinstance(target_rows, list) or len(target_rows) != 3:
        return _topic_binding_invalid("topic event target set is invalid")
    expected_paths = (
        _topic_relative(request["domain"], request["subdomain"], request["topic_id"]),
        _subdomain_uri(request["domain"], request["subdomain"]).removeprefix(ROOT_URI),
        atlas_state.TOPICS_PATH,
    )
    targets: list[TopicTarget] = []
    for index, (row, expected_path) in enumerate(
        zip(target_rows, expected_paths, strict=True)
    ):
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str):
            return _topic_binding_invalid(f"topic event target {index} is invalid")
        if row["path"] != expected_path:
            return _topic_binding_invalid("topic event target order is invalid")
        if set(row) == {"path", "input_bytes", "output_bytes"}:
            input_bytes = row["input_bytes"]
            output_bytes = row["output_bytes"]
            if input_bytes is not None and type(input_bytes) is not bytes:
                return _topic_binding_invalid(
                    f"topic event target {index} input is invalid"
                )
            if type(output_bytes) is not bytes:
                return _topic_binding_invalid(
                    f"topic event target {index} output is invalid"
                )
        elif set(row) == {"path", "input_base64", "output_base64"}:
            input_encoded = row["input_base64"]
            output_encoded = row["output_base64"]
            if input_encoded is not None and not isinstance(input_encoded, str):
                return _topic_binding_invalid(
                    f"topic event target {index} input is invalid"
                )
            if not isinstance(output_encoded, str):
                return _topic_binding_invalid(
                    f"topic event target {index} output is invalid"
                )
            try:
                input_bytes = (
                    None
                    if input_encoded is None
                    else base64.b64decode(input_encoded, validate=True)
                )
                output_bytes = base64.b64decode(output_encoded, validate=True)
            except (TypeError, ValueError):
                return _topic_binding_invalid(
                    f"topic event target {index} bytes are invalid"
                )
        else:
            return _topic_binding_invalid(
                f"topic event target {index} fields are invalid"
            )
        assert isinstance(output_bytes, bytes)
        if input_bytes is not None and input_bytes == output_bytes:
            return _topic_binding_invalid(f"topic event target {index} is unchanged")
        targets.append(TopicTarget(_uri(row["path"]), input_bytes, output_bytes))
    if (
        targets[0].input_bytes is not None
        or targets[1].input_bytes is None
        or targets[2].input_bytes is None
    ):
        return _topic_binding_invalid("topic event target inputs are invalid")
    try:
        expected_base = topic_base_transaction_id(request, targets)
    except (TypeError, ValueError, UnicodeError):
        return _topic_binding_invalid("topic event base identity is invalid")
    if owner_record["base_transaction_id"] != expected_base:
        return _topic_binding_invalid(
            "topic event base identity does not match targets"
        )

    attempt = outer.get("attempt", 0)
    predecessor = outer.get("predecessor_sha256")
    if type(attempt) is not int or attempt not in {0, 1}:
        return _topic_binding_invalid("topic event attempt is invalid")
    if attempt == 0:
        if predecessor is not None:
            return _topic_binding_invalid("attempt-zero predecessor is invalid")
    elif (
        not isinstance(predecessor, str)
        or re.fullmatch(r"[0-9a-f]{64}", predecessor) is None
    ):
        return _topic_binding_invalid("successor predecessor is invalid")

    try:
        topics_text = targets[2].input_bytes.decode("utf-8")
        subdomain_text = targets[1].input_bytes.decode("utf-8")
    except (AttributeError, UnicodeDecodeError):
        return _topic_binding_invalid("topic event inputs are not UTF-8")
    normalized_event, event_findings = _validate_event_request(
        request,
        topics_text,
        require_absent=True,
    )
    if event_findings or normalized_event is None or normalized_event != request:
        return _topic_binding_invalid("topic event inputs do not prove an absent topic")
    parsed_subdomain, subdomain_findings = _validate_subdomain(
        subdomain_text,
        {**request, "_topics_text": topics_text},
    )
    if (
        parsed_subdomain is None
        or subdomain_findings
        or any(
            row["id"] == request["topic_id"]
            or row["cells"][5]
            in {
                _topic_relative(
                    request["domain"],
                    request["subdomain"],
                    request["topic_id"],
                ),
                request["topic_path"],
            }
            for row in parsed_subdomain["topic_rows"]
        )
    ):
        return _topic_binding_invalid("topic event inputs do not prove an absent topic")

    intent = intent_record_or_missing
    transaction_id = ""
    event_hash = sha256(canonical_json(owner_record))
    if intent is not None and intent is not MISSING:
        if not isinstance(intent, Mapping):
            return _topic_binding_invalid("topic transaction intent is invalid")
        intent_targets = intent.get("targets")
        expected_intent_targets = [
            {
                "path": target.path.removeprefix(ROOT_URI),
                "input_sha256": target.input_sha256,
                "output_sha256": target.output_sha256,
            }
            for target in targets
        ]
        if (
            intent.get("request") != request
            or intent.get("request_sha256") != request_sha256
            or intent_targets != expected_intent_targets
            or intent.get("attempt") != attempt
            or intent.get("predecessor_sha256") != predecessor
            or intent.get("event_record_sha256") != event_hash
            or intent.get("base_transaction_id") != owner_record["base_transaction_id"]
        ):
            return _topic_binding_invalid(
                "topic transaction intent does not match event"
            )
        transaction_id = intent.get("transaction_id", "")
        if (
            not isinstance(transaction_id, str)
            or re.fullmatch(r"[0-9a-f]{16}-a[0-9]{6}", transaction_id) is None
        ):
            return _topic_binding_invalid("topic transaction ID is invalid")
        for key in ("owner_policy", "owner_policy_version", "policy"):
            if key in intent and intent[key] != "topic-post-v1":
                return _topic_binding_invalid("topic owner policy is invalid")

    post_validation = TopicPostValidation(
        _frozen_mapping(request),
        request_sha256,
        targets[0].output_bytes,
        targets[1].output_bytes,
        targets[2].output_bytes,
        tuple(parsed_subdomain["baseline"]),
    )
    return TopicTransactionBinding(
        _frozen_mapping(request),
        request_sha256,
        tuple(targets),
        "topic-post-v1",
        attempt,
        predecessor,
        post_validation,
        owner_record["base_transaction_id"],
        transaction_id,
        event_hash,
    )


def _markdown_link_label(value: str) -> str:
    return _encode_markdown_scalar(value, reserved=("[", "]"))


def _topic_map_expected_new(request: Mapping[str, Any]) -> tuple[str, ...]:
    topic_path = _topic_relative(
        request["domain"], request["subdomain"], request["topic_id"]
    )
    return (
        request["canonical_title"],
        "Research required",
        "Insufficient",
        "Current",
        request["created_on"],
        topic_path,
    )


def _list_value(values: Sequence[str]) -> str:
    return _list_projection_value(values, empty=_LIST_EMPTY_SENTINEL)


def _topic_frontmatter(request: Mapping[str, Any]) -> list[str]:
    aliases = json.dumps(request["aliases"], ensure_ascii=True, separators=(",", ":"))
    return [
        "---",
        "schema_version: 1",
        "note_type: research-topic",
        "managed_by: atlas",
        f'topic: "{request["topic_id"]}"',
        f'domain: "{request["domain"]}"',
        f'subdomain: "{request["subdomain"]}"',
        f"aliases: {aliases}",
        f'status: "{TOPIC_STATUS}"',
        f'coverage_state: "{TOPIC_COVERAGE}"',
        f'confidence: "{TOPIC_CONFIDENCE}"',
        f'last_researched: "{request["created_on"]}"',
        f'freshness_window: "{FRESHNESS_WINDOW}"',
        "tags: []",
        "---",
    ]


def _render_topic(
    request: Mapping[str, Any],
    related_topic_links: Mapping[str, tuple[str, str]],
    newline: str = "\n",
) -> str:
    related = request["related_topic_ids"]
    lines = _topic_frontmatter(request) + [
        "",
        f"# {_encode_markdown_scalar(request['canonical_title'])}",
        "",
        "## Agent answer contract",
        "<!-- atlas:managed:start agent-answer-contract -->",
        "- Answer only when `TOPICS.md` says this topic is `current`.",
        "- If dirty, refreshing, or blocked, halt with freshness state, dirty count, and pending edge IDs.",
        "- Cite source artifacts from `## Evidence map`; raw URLs are not evidence unless also materialized as source artifacts.",
        "<!-- atlas:managed:end agent-answer-contract -->",
        "",
        "## Scope and routing",
        "<!-- atlas:managed:start scope-and-routing -->",
        f"- Topic ID: `{request['topic_id']}`",
        f"- Include: {_list_value(request['include_terms'])}",
        f"- Exclude: {_list_value(request['exclude_terms'])}",
        f"- Related topics: {_list_value(related)}",
        "<!-- atlas:managed:end scope-and-routing -->",
        "",
        "## Current answer",
        "<!-- atlas:managed:start current-answer -->",
        "- No evidence-backed answer exists; acquisition and research are required.",
        "<!-- atlas:managed:end current-answer -->",
        "",
        "## Decision tree",
        "<!-- atlas:managed:start decision-tree -->",
        "<!-- atlas:managed:end decision-tree -->",
        "",
        "## Recommendation matrix",
        "<!-- atlas:managed:start recommendation-matrix -->",
        "| Situation | Recommendation | Evidence | Confidence |",
        "|---|---|---|---|",
        "<!-- atlas:managed:end recommendation-matrix -->",
        "",
        "## Edge cases",
        "<!-- atlas:managed:start edge-cases -->",
        "<!-- atlas:managed:end edge-cases -->",
        "",
        "## Caveats / failure modes",
        "<!-- atlas:managed:start caveats-failure-modes -->",
        "<!-- atlas:managed:end caveats-failure-modes -->",
        "",
        "## Evidence map",
        "<!-- atlas:managed:start evidence-map -->",
        "| Claim / use | Source artifact | Evidence strength | Notes |",
        "|---|---|---|---|",
        "<!-- atlas:managed:end evidence-map -->",
        "",
        "### Not-yet-digested external leads",
        "",
        "## Gaps and acquisition needs",
        "<!-- atlas:managed:start gaps-and-acquisition-needs -->",
        "- Evidence-backed answer unavailable — acquire and research relevant sources.",
        "<!-- atlas:managed:end gaps-and-acquisition-needs -->",
        "",
        "## Recent changes",
        "<!-- atlas:managed:start recent-changes -->",
        "<!-- atlas:managed:end recent-changes -->",
        "",
        "## Read next",
        "<!-- atlas:managed:start read-next -->",
    ]
    lines.extend(
        f"- [{related_topic_links[item][0]}]({related_topic_links[item][1]})"
        for item in related
    )
    lines.extend(
        [
            "<!-- atlas:managed:end read-next -->",
        ]
    )
    return newline.join(lines) + newline


def _parse_topic_document(text: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(text, str) or not text:
        return None, "topic INDEX.md is missing"
    parsed = _frontmatter(text)
    if parsed is None:
        return None, "topic frontmatter is invalid"
    values, raw_values, lines, _, close, newline = parsed
    expected_keys = {
        "schema_version",
        "note_type",
        "managed_by",
        "topic",
        "domain",
        "subdomain",
        "aliases",
        "status",
        "coverage_state",
        "confidence",
        "last_researched",
        "freshness_window",
        "tags",
    }
    if set(values) != expected_keys:
        return None, "topic frontmatter keys are invalid"
    if close < 1 or _line_body(lines[1]) != "schema_version: 1":
        return None, "topic schema_version must be the unquoted integer 1"
    if (
        values.get("schema_version") != "1"
        or values.get("note_type") != "research-topic"
        or values.get("managed_by") != "atlas"
    ):
        return None, "topic frontmatter identity is invalid"
    aliases = _parse_json_array(values.get("aliases", ""))
    tags = _parse_json_array(values.get("tags", ""))
    if aliases is None or tags is None:
        return None, "topic aliases/tags must be JSON string arrays"
    if (
        values.get("status") not in {"active", "archived", "draft"}
        or values.get("coverage_state")
        not in {"sufficient", "partial", "insufficient", "stale"}
        or values.get("confidence") not in {"high", "medium", "low"}
        or values.get("freshness_window") != FRESHNESS_WINDOW
    ):
        return None, "topic frontmatter enum or freshness window is invalid"
    if DATE_RE.fullmatch(values.get("last_researched", "")) is None:
        return None, "topic last_researched is invalid"
    try:
        date.fromisoformat(values["last_researched"])
    except ValueError:
        return None, "topic last_researched is not a real date"
    heading = next(
        (
            _line_body(line).strip()
            for line in lines[close + 1 :]
            if _line_body(line).strip().startswith("# ")
        ),
        None,
    )
    if heading is None:
        return None, "topic heading is missing"
    heading_raw = heading[2:]
    pairs, marker_error = _marker_pairs(lines, TOPIC_MARKERS)
    if marker_error:
        return None, marker_error
    current_start, current_end = pairs["current-answer"]
    current_answer = tuple(
        _line_body(line).strip()
        for line in lines[current_start + 1 : current_end]
        if _line_body(line).strip()
    )
    scope_start, scope_end = pairs["scope-and-routing"]
    scope: dict[str, str] = {}
    scope_values: dict[str, Any] = {}
    scope_raw_values: dict[str, str] = {}
    scope_labels = {"Topic ID", "Include", "Exclude", "Related topics"}
    for line in lines[scope_start + 1 : scope_end]:
        body = _line_body(line).strip()
        if not body:
            continue
        match = re.fullmatch(
            r"- (Topic ID|Include|Exclude|Related topics): ?(.*)", body
        )
        if match is None or match.group(1) in scope:
            return None, "topic scope-and-routing projection is invalid"
        label, raw_value = match.groups()
        scope[label] = raw_value
        scope_raw_values[label] = raw_value
        if label == "Topic ID":
            if len(raw_value) < 2 or raw_value[0] != "`" or raw_value[-1] != "`":
                return None, "topic scope-and-routing projection is invalid"
            scope_values[label] = _decode_markdown_scalar(raw_value[1:-1])
        else:
            parsed_values = _parse_semicolon(raw_value)
            if parsed_values is None:
                return None, "topic scope-and-routing projection is invalid"
            scope_values[label] = parsed_values
    if set(scope) != scope_labels:
        return None, "topic scope-and-routing projection is invalid"
    read_start, read_end = pairs["read-next"]
    read_next: list[dict[str, str]] = []
    for line in lines[read_start + 1 : read_end]:
        body = _line_body(line).strip()
        if not body:
            continue
        link_match = re.fullmatch(r"- \[(.*)\]\(([^()]*)\)", body)
        if link_match is None:
            return None, "topic read-next projection is invalid"
        raw_label, raw_path = link_match.groups()
        read_next.append(
            {
                "raw_label": raw_label,
                "label": _decode_markdown_scalar(raw_label),
                "raw_path": raw_path,
            }
        )
    return {
        "values": values,
        "raw_values": raw_values,
        "aliases": aliases,
        "tags": tags,
        "heading": _decode_markdown_scalar(heading_raw),
        "heading_raw": heading_raw,
        "scope": scope,
        "scope_values": scope_values,
        "scope_raw_values": scope_raw_values,
        "lines": lines,
        "newline": newline,
        "final_newline": text.endswith(("\n", "\r")),
        "pairs": pairs,
        "current_answer": current_answer,
        "read_next": read_next,
    }, None


def _parse_semicolon(value: str) -> list[str] | None:
    if value == _LIST_EMPTY_SENTINEL:
        return []
    if not value:
        return None
    parts = [decoded.strip() for _, decoded in _projection_parts(value)]
    if any(not item for item in parts):
        return None
    return parts


def _topic_identity_findings(
    parsed: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    conflict_code: str = "TOPIC_COMPATIBILITY_CONFLICT",
) -> list[atlas_state.Finding]:
    values = parsed["values"]
    tags = parsed["tags"]
    scope_raw_values = parsed.get("scope_raw_values", parsed["scope"])
    findings: list[atlas_state.Finding] = []
    expected_scalars = {
        "topic": request["topic_id"],
        "domain": request["domain"],
        "subdomain": request["subdomain"],
        "status": request["status"],
    }
    raw_values = parsed.get("raw_values", {})
    expected_raw_values = {
        "schema_version": "1",
        "note_type": "research-topic",
        "managed_by": "atlas",
        "topic": json.dumps(
            request["topic_id"], ensure_ascii=True, separators=(",", ":")
        ),
        "domain": json.dumps(
            request["domain"], ensure_ascii=True, separators=(",", ":")
        ),
        "subdomain": json.dumps(
            request["subdomain"], ensure_ascii=True, separators=(",", ":")
        ),
        "aliases": json.dumps(
            request["aliases"], ensure_ascii=True, separators=(",", ":")
        ),
        "status": json.dumps(
            request["status"], ensure_ascii=True, separators=(",", ":")
        ),
        "coverage_state": json.dumps(
            values["coverage_state"], ensure_ascii=True, separators=(",", ":")
        ),
        "confidence": json.dumps(
            values["confidence"], ensure_ascii=True, separators=(",", ":")
        ),
        "last_researched": json.dumps(
            values["last_researched"], ensure_ascii=True, separators=(",", ":")
        ),
        "freshness_window": json.dumps(
            values["freshness_window"], ensure_ascii=True, separators=(",", ":")
        ),
        "tags": json.dumps(tags, ensure_ascii=True, separators=(",", ":")),
    }
    topic_uri = _topic_uri(request["domain"], request["subdomain"], request["topic_id"])
    for field, expected_raw in expected_raw_values.items():
        if raw_values.get(field) != expected_raw:
            findings.append(
                _finding(
                    conflict_code,
                    topic_uri,
                    f"frontmatter {field} is not canonically encoded",
                )
            )
    for field, expected in expected_scalars.items():
        if values.get(field) != expected:
            findings.append(
                _finding(
                    conflict_code,
                    _topic_uri(
                        request["domain"], request["subdomain"], request["topic_id"]
                    ),
                    f"frontmatter {field} disagrees with request",
                )
            )
    if not _raw_scalar_matches(
        parsed.get("heading_raw", parsed["heading"]),
        request["canonical_title"],
    ):
        findings.append(
            _finding(
                conflict_code,
                _topic_uri(
                    request["domain"], request["subdomain"], request["topic_id"]
                ),
                "canonical title disagrees with request",
            )
        )
    if parsed["aliases"] != request["aliases"]:
        findings.append(
            _finding(
                conflict_code,
                _topic_uri(
                    request["domain"], request["subdomain"], request["topic_id"]
                ),
                "aliases disagree with request",
            )
        )
    expected_scope = {
        "Topic ID": request["topic_id"],
        "Include": request["include_terms"],
        "Exclude": request["exclude_terms"],
        "Related topics": request["related_topic_ids"],
    }
    for field, expected in expected_scope.items():
        raw_value = scope_raw_values.get(field, "")
        if field == "Topic ID":
            actual = raw_value[1:-1] if len(raw_value) >= 2 else ""
            matches = _raw_scalar_matches(actual, expected)
        else:
            matches = _raw_list_matches(
                raw_value,
                expected,
                empty_legacy=_LIST_EMPTY_SENTINEL,
                reserved=(";",),
                protect_literals=(_LIST_EMPTY_SENTINEL,),
            )
        if not matches:
            findings.append(
                _finding(
                    conflict_code,
                    _topic_uri(
                        request["domain"], request["subdomain"], request["topic_id"]
                    ),
                    f"scope {field} disagrees with request",
                )
            )
    return findings


def _row_lists(
    row: Mapping[str, str],
) -> tuple[list[str] | None, list[str] | None, list[str] | None]:
    def parse(value: str) -> list[str] | None:
        if value == "":
            return []
        return _parse_semicolon(value)

    return (
        parse(row["Aliases"]),
        parse(row["Include terms"]),
        parse(row["Exclude terms"]),
    )


def _topic_row_raw(row: Mapping[str, Any], field: str) -> str:
    raw = row.get("_raw")
    if isinstance(raw, Mapping):
        return str(raw.get(field, row[field]))
    return str(row[field])


def _topic_row_semantic_title(row: Mapping[str, Any]) -> str:
    raw = _topic_row_raw(row, "Canonical title").strip()
    decoded = str(row["Canonical title"])
    canonical = _encode_markdown_scalar(decoded, reserved=("|",))
    return decoded if raw in {decoded, canonical} else raw


def _topic_link_findings(
    parsed: Mapping[str, Any],
    request: Mapping[str, Any],
    topic_rows_by_id: Mapping[str, Mapping[str, Any]],
    *,
    conflict_code: str = "TOPIC_COMPATIBILITY_CONFLICT",
) -> list[atlas_state.Finding]:
    actual = parsed.get("read_next", ())
    expected_ids = request["related_topic_ids"]
    findings: list[atlas_state.Finding] = []
    if len(actual) != len(expected_ids):
        findings.append(
            _finding(
                conflict_code,
                _topic_uri(
                    request["domain"], request["subdomain"], request["topic_id"]
                ),
                "read-next related topic links disagree with request",
            )
        )
        return findings
    for item, link in zip(expected_ids, actual, strict=True):
        row = topic_rows_by_id.get(item)
        if row is None:
            continue
        label_ok = _raw_scalar_matches(
            link["raw_label"],
            _topic_row_semantic_title(row),
            reserved=("[", "]"),
        )
        path_ok = _raw_scalar_matches(link["raw_path"], row["Topic path"])
        if not label_ok or not path_ok:
            findings.append(
                _finding(
                    conflict_code,
                    _topic_uri(
                        request["domain"], request["subdomain"], request["topic_id"]
                    ),
                    "read-next related topic link disagrees with canonical state",
                    row=item,
                )
            )
    return findings


def _projection_findings(
    parsed_subdomain: Mapping[str, Any],
    request: Mapping[str, Any],
    topic_parsed: Mapping[str, Any],
    topic_row: Mapping[str, Any],
    *,
    conflict_code: str = "TOPIC_COMPATIBILITY_CONFLICT",
) -> list[atlas_state.Finding]:
    uri = parsed_subdomain["uri"]
    requested = parsed_subdomain["topic_rows_by_id"].get(request["topic_id"])
    findings: list[atlas_state.Finding] = []
    if requested is None:
        findings.append(
            _finding(
                conflict_code,
                _topic_uri(
                    request["domain"], request["subdomain"], request["topic_id"]
                ),
                "requested subdomain topic projection is missing",
                row=request["topic_id"],
            )
        )
        return findings

    raw_cells = requested["raw_cells"]
    values = topic_parsed["values"]
    coverage = _coverage_label(values["coverage_state"])
    expected = {
        0: request["canonical_title"],
        2: coverage,
        3: _title_case(topic_row["Freshness state"]),
        4: values["last_researched"],
        5: _topic_relative(
            request["domain"], request["subdomain"], request["topic_id"]
        ),
    }
    for index, value in expected.items():
        if not _raw_scalar_matches(raw_cells[index], value, reserved=("|",)):
            findings.append(
                _finding(
                    conflict_code,
                    uri,
                    f"requested topic-map field {index} disagrees with canonical state",
                    row=request["topic_id"],
                )
            )

    initial_answer = topic_parsed["current_answer"] == (
        "- No evidence-backed answer exists; acquisition and research are required.",
    )
    if initial_answer and not _raw_scalar_matches(
        raw_cells[1], "Research required", reserved=("|",)
    ):
        findings.append(
            _finding(
                conflict_code,
                uri,
                "initial no-evidence topic-map answer is not Research required",
                row=request["topic_id"],
            )
        )
    elif not initial_answer and _raw_scalar_matches(
        raw_cells[1], "Research required", reserved=("|",)
    ):
        findings.append(
            _finding(
                conflict_code,
                uri,
                "evolved topic-map answer still uses the initial Research required value",
                row=request["topic_id"],
            )
        )

    title = request["canonical_title"]
    topic_rows = parsed_subdomain["topic_rows"]
    coverage_values = parsed_subdomain["coverage_values"]
    bucket = coverage_values.get(coverage)
    if bucket is None:
        findings.append(
            _finding(
                conflict_code,
                uri,
                f"requested topic coverage bucket {coverage} is missing",
                row=request["topic_id"],
            )
        )
    else:
        for label, (_, value) in coverage_values.items():
            _, entries = _split_projection_values(
                value,
                COVERAGE_PLACEHOLDERS.get(label),
                topic_rows=topic_rows,
                bucket=label,
            )
            raw_entries = [raw for raw, _ in _projection_parts(value)]
            if len(raw_entries) != len(entries):
                raw_entries = []
            same_title_members = [
                row
                for row in topic_rows
                if _topic_map_bucket(row) == label
                and _topic_map_title_matches(row, title)
            ]
            matches = _projection_membership_indices(
                entries,
                same_title_members,
                raw_values=raw_entries or None,
            )
            actual_count = (
                sum(
                    _raw_scalar_matches(raw, title, reserved=(";",))
                    for raw in raw_entries
                )
                if raw_entries
                else entries.count(title)
            )
            expected_count = len(same_title_members)
            requested_present = request["topic_id"] in matches
            if label == coverage:
                valid = (
                    requested_present
                    and actual_count == expected_count
                    and len(matches) >= expected_count
                )
            else:
                valid = not requested_present and actual_count == expected_count
            if not valid:
                findings.append(
                    _finding(
                        conflict_code,
                        uri,
                        f"requested topic is not listed exactly once under {coverage}"
                        if label == coverage
                        else f"requested topic is listed under {label} instead of {coverage}",
                        row=request["topic_id"],
                    )
                )

    stale_values = parsed_subdomain["sections"].get("stale-or-weak-areas", ())
    same_title_rows = [
        row for row in topic_rows if _topic_map_title_matches(row, title)
    ]
    stale_members = [row for row in same_title_rows if _topic_map_requires_stale(row)]
    requires_stale = (
        values["coverage_state"] != "sufficient"
        or topic_row["Freshness state"] != "current"
        or initial_answer
    )
    if requires_stale:
        stale_matches, stale_projection_count = _stale_membership_assignments(
            stale_values, stale_members, known_topic_rows=topic_rows
        )
        requested_index = stale_matches.get(request["topic_id"])
        requested_body = (
            stale_values[requested_index].strip()
            if requested_index is not None and requested_index < len(stale_values)
            else None
        )
        if (
            requested_index is None
            or len(stale_matches) != len(stale_members)
            or stale_projection_count != len(stale_members)
            or (initial_answer and not _stale_entry_matches(requested_body, title))
        ):
            findings.append(
                _finding(
                    conflict_code,
                    uri,
                    "requested topic stale-or-weak projection is missing or duplicated",
                    row=request["topic_id"],
                )
            )
    elif stale_members:
        # A same-title stale entry may belong to an older topic membership.
        # Only a direct match to the requested ID is a requested projection
        # conflict; duplicate display titles remain unrelated memberships.
        stale_matches = _stale_membership_indices(
            stale_values, stale_members, known_topic_rows=topic_rows
        )
        if request["topic_id"] in stale_matches:
            findings.append(
                _finding(
                    conflict_code,
                    uri,
                    "sufficient current topic must not remain in stale-or-weak projection",
                    row=request["topic_id"],
                )
            )
    else:
        stale_matches = _stale_membership_indices(
            stale_values, same_title_rows, known_topic_rows=topic_rows
        )
        if request["topic_id"] in stale_matches:
            findings.append(
                _finding(
                    conflict_code,
                    uri,
                    "sufficient current topic must not remain in stale-or-weak projection",
                    row=request["topic_id"],
                )
            )
    return findings


def _topic_row_for_request(
    topics_table: atlas_state.ParsedTable,
    request: Mapping[str, Any],
) -> tuple[dict[str, str] | None, Findings]:
    rows = _topic_table_rows(topics_table)
    requested = next(
        (row for row in rows if row["Topic ID"] == request["topic_id"]), None
    )
    topic_rel = _topic_relative(
        request["domain"], request["subdomain"], request["topic_id"]
    )
    topic_uri = _topic_uri(request["domain"], request["subdomain"], request["topic_id"])
    path_rows = [row for row in rows if row["Topic path"] in {topic_rel, topic_uri}]
    findings: list[atlas_state.Finding] = []
    if requested is not None and requested["Topic path"] != topic_rel:
        findings.append(
            _finding(
                "TOPIC_ID_EXISTS",
                _uri(requested["Topic path"]),
                "topic ID already exists at another path",
                row=request["topic_id"],
            )
        )
    if path_rows and any(row["Topic ID"] != request["topic_id"] for row in path_rows):
        findings.append(
            _finding(
                "TOPIC_PATH_EXISTS",
                topic_uri,
                "canonical topic path belongs to another topic ID",
                row=path_rows[0]["Topic ID"],
            )
        )
    if findings:
        return requested, _sort_findings(findings)
    return requested, ()


def _render_topics_registry(
    text: str,
    table: atlas_state.ParsedTable,
    request: Mapping[str, Any],
) -> str:
    newline = table.newline
    lines = list(table.lines)
    rows = _topic_table_rows(table)
    new_cells = (
        request["topic_id"],
        _topic_relative(request["domain"], request["subdomain"], request["topic_id"]),
        request["domain"],
        request["subdomain"],
        request["canonical_title"],
        _list_projection_value(request["aliases"], empty=""),
        "",
        _list_projection_value(request["include_terms"], empty=""),
        _list_projection_value(request["exclude_terms"], empty=""),
        TOPIC_FRESHNESS,
        "0",
        "",
        "",
        "",
        "0",
        TOPIC_REFRESH_MODEL,
    )
    insert_at = table.data_end if table.data_end is not None else len(lines)
    for row, line_number in zip(rows, table.row_lines, strict=True):
        if request["topic_id"].encode("utf-8") < row["Topic ID"].encode("utf-8"):
            insert_at = line_number - 1
            break
    if insert_at > 0 and not lines[insert_at - 1].endswith(("\n", "\r")):
        lines[insert_at - 1] += newline
    lines.insert(insert_at, _render_row(new_cells, newline))
    return _replace_lines_preserve_final(lines, table.final_newline)


def _topic_map_id(row: Mapping[str, Any]) -> str:
    return str(row["id"])


def _topic_map_title(row: Mapping[str, Any]) -> str:
    return str(row["cells"][0])


def _topic_map_semantic_title(row: Mapping[str, Any]) -> str:
    raw = _topic_map_raw_cell(row, 0).strip()
    decoded = _topic_map_title(row)
    canonical = _encode_markdown_scalar(decoded, reserved=("|",))
    return decoded if raw in {decoded, canonical} else raw


def _topic_map_raw_cell(row: Mapping[str, Any], index: int) -> str:
    raw_cells = row.get("raw_cells")
    if isinstance(raw_cells, Sequence) and index < len(raw_cells):
        return str(raw_cells[index])
    return str(row["cells"][index])


def _topic_map_cell_matches(
    row: Mapping[str, Any],
    index: int,
    expected: str,
    *,
    reserved: Sequence[str] = ("|",),
) -> bool:
    return _raw_scalar_matches(
        _topic_map_raw_cell(row, index),
        expected,
        reserved=reserved,
    )


def _topic_map_title_matches(
    row: Mapping[str, Any], expected: str, *, reserved: Sequence[str] = ("|",)
) -> bool:
    return _topic_map_cell_matches(row, 0, expected, reserved=reserved)


def _topic_map_bucket(row: Mapping[str, Any]) -> str:
    return str(row["cells"][2])


def _topic_map_requires_stale(row: Mapping[str, Any]) -> bool:
    cells = row["cells"]
    raw_cells = row.get("raw_cells")
    if isinstance(raw_cells, Sequence):
        return (
            _raw_scalar_matches(raw_cells[1], "Research required", reserved=("|",))
            or not _raw_scalar_matches(raw_cells[2], "Sufficient", reserved=("|",))
            or not _raw_scalar_matches(raw_cells[3], "Current", reserved=("|",))
        )
    return (
        cells[1] == "Research required"
        or cells[2] != "Sufficient"
        or cells[3] != "Current"
    )


def _projection_membership_indices(
    values: Sequence[str],
    topic_rows: Sequence[Mapping[str, Any]],
    *,
    title: str | None = None,
    raw_values: Sequence[str] | None = None,
) -> dict[str, int]:
    """Match display values to canonical topic IDs in byte-order sequence.

    Markdown projections intentionally display titles rather than IDs.  Matching
    the sorted topic-map members, instead of using a title-to-ID dictionary,
    preserves multiplicity when two IDs share one canonical title.
    """

    members = sorted(
        (
            row
            for row in topic_rows
            if title is None or _topic_map_title_matches(row, title)
        ),
        key=lambda row: _topic_map_id(row).encode("utf-8"),
    )
    matches: dict[str, int] = {}
    cursor = 0
    for row in members:
        row_title = _topic_map_semantic_title(row)
        for index in range(cursor, len(values)):
            item_matches = (
                _raw_scalar_matches(
                    raw_values[index],
                    row_title,
                    reserved=(";",),
                )
                if raw_values is not None and index < len(raw_values)
                else values[index] == row_title
            )
            if item_matches:
                matches[_topic_map_id(row)] = index
                cursor = index + 1
                break
    return matches


def _encode_projection_value(value: str) -> str:
    return _encode_markdown_scalar(value, reserved=(";",))


def _projection_parts(value: str) -> list[tuple[str, str]]:
    """Return exact source segments and decoded values split on raw semicolons."""

    if not value:
        return []
    parts: list[tuple[str, str]] = []
    start = 0
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\":
            if index + 1 >= len(value):
                index += 1
                continue
            next_char = value[index + 1]
            if next_char in {"\\", ";"}:
                index += 2
                continue
            if next_char == "u" and value.startswith("\\u{", index):
                close = value.find("}", index + 3)
                if close != -1:
                    digits = value[index + 3 : close]
                    try:
                        codepoint = int(digits, 16)
                    except ValueError:
                        codepoint = -1
                    if (
                        1 <= len(digits) <= 6
                        and 0 <= codepoint <= 0x10FFFF
                        and not 0xD800 <= codepoint <= 0xDFFF
                    ):
                        index = close + 1
                        continue
            index += 1
            continue
        if char == ";":
            raw = value[start:index]
            parts.append((raw, _decode_markdown_scalar(raw).strip()))
            start = index + 1
        index += 1
    raw = value[start:]
    parts.append((raw, _decode_markdown_scalar(raw).strip()))
    return parts


def _split_projection_values(
    value: str,
    placeholder: str | None = None,
    *,
    topic_rows: Sequence[Mapping[str, Any]] = (),
    bucket: str | None = None,
) -> tuple[str, list[str]]:
    delimiter = "; "
    if placeholder is not None and value == placeholder:
        owns_title = any(
            _topic_map_title_matches(row, placeholder)
            and (bucket is None or _topic_map_bucket(row) == bucket)
            for row in topic_rows
        )
        if not owns_title:
            return delimiter, []
    return delimiter, [decoded for _, decoded in _projection_parts(value)]


def _projection_source(parts: Sequence[tuple[str, str]]) -> str:
    return "".join(
        raw + (";" if index + 1 < len(parts) else "")
        for index, (raw, _) in enumerate(parts)
    )


def _insert_sorted_value(
    value: str,
    new_value: str,
    requested_id: str,
    topic_rows: Sequence[Mapping[str, Any]],
    *,
    placeholder: str | None = None,
    bucket: str | None = None,
) -> str:
    _, values = _split_projection_values(
        value,
        placeholder,
        topic_rows=topic_rows,
        bucket=bucket,
    )
    parts = _projection_parts(value)
    raw_values = [raw for raw, _ in parts]
    if len(raw_values) != len(values):
        raw_values = [_encode_projection_value(item) for item in values]
        parts = [(raw, item) for raw, item in zip(raw_values, values, strict=True)]
    relevant_rows = [
        row for row in topic_rows if bucket is None or _topic_map_bucket(row) == bucket
    ]
    matches = _projection_membership_indices(
        values,
        relevant_rows,
        raw_values=raw_values,
    )
    if requested_id in matches:
        return value
    new_encoded = _encode_projection_value(new_value)
    if not values:
        return new_encoded

    index = len(values)
    for row in sorted(
        relevant_rows, key=lambda item: _topic_map_id(item).encode("utf-8")
    ):
        row_id = _topic_map_id(row)
        position = matches.get(row_id)
        if position is None:
            continue
        if requested_id.encode("utf-8") < row_id.encode("utf-8"):
            index = position
            break
        index = max(index, position + 1)
    index = max(0, min(index, len(parts)))
    if index == 0:
        suffix = _projection_source(parts)
        return new_encoded + "; " + suffix
    if index == len(parts):
        prefix = _projection_source(parts)
        return prefix + "; " + new_encoded
    prefix = _projection_source(parts[:index])
    suffix = _projection_source(parts[index:])
    return prefix + ";" + new_encoded + "; " + suffix


def _stale_projection_label(value: str) -> str:
    return _encode_markdown_scalar(value, reserved=(";",))


def _stale_entry(value: str) -> str:
    return (
        "- "
        + _stale_projection_label(value)
        + " — No evidence-backed answer exists; acquisition/research is required."
    )


def _stale_entry_matches(value: str | None, title: str) -> bool:
    if not isinstance(value, str):
        return False
    suffix = " — No evidence-backed answer exists; acquisition/research is required."
    source = value.strip()
    if not source.startswith("- ") or not source.endswith(suffix):
        return False
    label = source[2 : -len(suffix)]
    return bool(label) and _raw_scalar_matches(
        label,
        title,
        reserved=(";",),
    )


def _stale_membership_assignments(
    stale_values: Sequence[str],
    topic_rows: Sequence[Mapping[str, Any]],
    *,
    title: str | None = None,
    known_topic_rows: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[dict[str, int], int]:
    """Assign complete stale labels and count every relevant projection."""

    owns_scaffold_title = any(
        _topic_map_title_matches(row, "<topic or gap>")
        and _topic_map_requires_stale(row)
        for row in topic_rows
    )
    known_rows = tuple(topic_rows if known_topic_rows is None else known_topic_rows)
    labels: list[tuple[int, tuple[str, ...]]] = []
    for index, raw in enumerate(stale_values):
        body = raw.strip()
        if body == "- <topic or gap> — <reason>" and not owns_scaffold_title:
            continue
        if not body.startswith("- "):
            continue
        candidates: list[tuple[int, str, str]] = []
        for row in known_rows:
            row_id = _topic_map_id(row)
            title_value = _topic_map_semantic_title(row)
            for label in (title_value, _stale_projection_label(title_value)):
                if (
                    label
                    and body.startswith(f"- {label} — ")
                    and _raw_scalar_matches(
                        label,
                        title_value,
                        reserved=(";",),
                    )
                ):
                    candidates.append((len(label), row_id, "title"))
            for label in (row_id, f"`{row_id}`"):
                if label and body.startswith(f"- {label} — "):
                    candidates.append((len(label), row_id, "id"))
        if candidates:
            longest = max(length for length, _, _ in candidates)
            longest_candidates = [
                (row_id, form)
                for length, row_id, form in candidates
                if length == longest
            ]
            title_ids = {
                row_id for row_id, form in longest_candidates if form == "title"
            }
            id_ids = {row_id for row_id, form in longest_candidates if form == "id"}
            if any(title_id != id_id for title_id in title_ids for id_id in id_ids):
                continue
            labels.append(
                (
                    index,
                    tuple(
                        sorted(
                            {row_id for row_id, _ in longest_candidates},
                            key=lambda value: value.encode("utf-8"),
                        )
                    ),
                )
            )

    members = sorted(
        (
            row
            for row in topic_rows
            if title is None or _topic_map_title_matches(row, title)
        ),
        key=lambda row: _topic_map_id(row).encode("utf-8"),
    )
    member_ids = {_topic_map_id(row) for row in members}
    relevant_label_count = sum(
        any(row_id in member_ids for row_id in candidate_ids)
        for _, candidate_ids in labels
    )
    matches: dict[str, int] = {}
    cursor = 0
    for row in members:
        row_id = _topic_map_id(row)
        for position in range(cursor, len(labels)):
            if row_id in labels[position][1]:
                matches[row_id] = labels[position][0]
                cursor = position + 1
                break
    return matches, relevant_label_count


def _stale_membership_indices(
    stale_values: Sequence[str],
    topic_rows: Sequence[Mapping[str, Any]],
    *,
    title: str | None = None,
    known_topic_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, int]:
    matches, _ = _stale_membership_assignments(
        stale_values,
        topic_rows,
        title=title,
        known_topic_rows=known_topic_rows,
    )
    return matches


def _render_new_subdomain(
    request: Mapping[str, Any],
    newline: str = "\n",
) -> str:
    """Render the canonical empty subdomain index for a missing parent."""

    domain = request["domain"]
    subdomain = request["subdomain"]
    heading = _title_case(subdomain.replace("-", " "))
    lines = [
        "---",
        "schema_version: 1",
        "note_type: subdomain-index",
        "managed_by: atlas",
        f'domain: "{domain}"',
        f'subdomain: "{subdomain}"',
        f'last_updated: "{request["created_on"]}"',
        "tags: []",
        "---",
        "",
        f"# {heading}",
        "",
        "## Routing scope",
        "<!-- atlas:managed:start routing-scope -->",
        f"- Domain: `{domain}`",
        f"- Subdomain: `{subdomain}`",
        f"- Include: {_list_value(request['include_terms'])}",
        f"- Exclude: {_list_value(request['exclude_terms'])}",
        "<!-- atlas:managed:end routing-scope -->",
        "",
        "## Topic map",
        "<!-- atlas:managed:start topic-map -->",
        "| Topic | Default answer | Coverage | Freshness | Last updated | Link |",
        "|---|---|---|---|---|---|",
        "<!-- atlas:managed:end topic-map -->",
        "",
        "## Default lookup order",
        "<!-- atlas:managed:start default-lookup-order -->",
        "1. Check `vault://atlas/summaries/registry/TOPICS.md` for topic path and freshness.",
        "2. Read the topic `INDEX.md` when `Freshness state=current`.",
        "3. Read optional split files only when the topic `INDEX.md` points to them.",
        "<!-- atlas:managed:end default-lookup-order -->",
        "",
        "## Coverage map",
        "<!-- atlas:managed:start coverage-map -->",
        "- Sufficient: <topics with usable current answers>",
        "- Partial: <topics with known gaps>",
        "- Insufficient: <topics needing acquisition>",
        "<!-- atlas:managed:end coverage-map -->",
        "",
        "## Stale or weak areas",
        "<!-- atlas:managed:start stale-or-weak-areas -->",
        "- <topic or gap> — <reason>",
        "<!-- atlas:managed:end stale-or-weak-areas -->",
        "",
        "## Acquisition watchlist",
        "<!-- atlas:managed:start acquisition-watchlist -->",
        "- <source class, feed, repo, author, query, or evidence gap>",
        "<!-- atlas:managed:end acquisition-watchlist -->",
    ]
    return newline.join(lines) + newline


def _render_subdomain(
    parsed: Mapping[str, Any],
    request: Mapping[str, Any],
) -> str:
    lines = list(parsed["lines"])
    newline = parsed["newline"]
    pairs = parsed["pairs"]
    topic_start, topic_end = pairs["topic-map"]
    topic_rows = list(parsed["topic_rows"])
    new_row = _render_row(_topic_map_expected_new(request), newline)
    if request["topic_id"] not in parsed["topic_rows_by_id"]:
        insertion = topic_end
        for row in topic_rows:
            if request["topic_id"].encode("utf-8") < row["id"].encode("utf-8"):
                insertion = row["line_index"]
                break
        if insertion > 0 and not lines[insertion - 1].endswith(("\n", "\r")):
            lines[insertion - 1] += newline
        lines.insert(insertion, new_row)
        # All positions after topic-map insertion moved by one.  Re-discover
        # marker indexes before replacing the other managed sections.
        pairs, marker_error = _marker_pairs(lines, SUBDOMAIN_MARKERS)
        if marker_error:
            raise ValueError(marker_error)

    # Replace only the requested frontmatter field, preserving its accepted
    # key spacing, value spacing, quote style, and original line ending.
    for index in range(1, parsed["close"]):
        line = lines[index]
        body = _line_body(line)
        if ":" not in body:
            continue
        key, raw_value = body.split(":", 1)
        if key.strip() != "last_updated":
            continue
        raw = raw_value.strip()
        quote = raw[0] if raw and raw[0] in "\"'" else ""
        replacement = (
            quote + request["created_on"] + quote if quote else request["created_on"]
        )
        leading = raw_value[: len(raw_value) - len(raw_value.lstrip())]
        trailing = raw_value[len(raw_value.rstrip()) :]
        lines[index] = (
            body[: body.index(":") + 1]
            + leading
            + replacement
            + trailing
            + _line_ending(line, newline)
        )
        break

    # Locate the requested bucket after any topic-map insertion.
    pairs, marker_error = _marker_pairs(lines, SUBDOMAIN_MARKERS)
    if marker_error:
        raise ValueError(marker_error)
    coverage_start, coverage_end = pairs["coverage-map"]
    coverage_content = lines[coverage_start + 1 : coverage_end]
    for offset, line in enumerate(coverage_content):
        body = _line_body(line)
        match = re.fullmatch(r"(- Insufficient:)([ \t]*)(.*)", body)
        if match:
            existing = match.group(3)
            new_value = _insert_sorted_value(
                existing,
                request["canonical_title"],
                request["topic_id"],
                parsed["topic_rows"],
                placeholder=COVERAGE_PLACEHOLDERS["Insufficient"],
                bucket="Insufficient",
            )
            ending = _line_ending(line, newline)
            coverage_content[offset] = (
                match.group(1) + match.group(2) + new_value + ending
            )
            break
    lines[coverage_start + 1 : coverage_end] = coverage_content

    pairs, marker_error = _marker_pairs(lines, SUBDOMAIN_MARKERS)
    if marker_error:
        raise ValueError(marker_error)
    stale_start, stale_end = pairs["stale-or-weak-areas"]
    stale_content = lines[stale_start + 1 : stale_end]
    stale_entry = _stale_entry(request["canonical_title"])
    existing_matches = _stale_membership_indices(
        [_line_body(line) for line in stale_content],
        parsed["topic_rows"],
        title=request["canonical_title"],
    )
    if request["topic_id"] not in existing_matches:
        empty_placeholder = [
            index
            for index, line in enumerate(stale_content)
            if _line_body(line).strip() == "- <topic or gap> — <reason>"
            and not any(
                _topic_map_title(row) == "<topic or gap>"
                and _topic_map_requires_stale(row)
                for row in parsed["topic_rows"]
            )
        ]
        placeholder_line: str | None = None
        if empty_placeholder:
            placeholder_line = stale_content.pop(empty_placeholder[0])
        stale_members = [
            row for row in parsed["topic_rows"] if _topic_map_requires_stale(row)
        ]
        stale_matches = _stale_membership_indices(
            [_line_body(line) for line in stale_content],
            stale_members,
            known_topic_rows=parsed["topic_rows"],
        )
        insert = len(stale_content)
        for row in sorted(
            stale_members,
            key=lambda item: _topic_map_id(item).encode("utf-8"),
        ):
            row_id = _topic_map_id(row)
            position = stale_matches.get(row_id)
            if position is None:
                continue
            if request["topic_id"].encode("utf-8") < row_id.encode("utf-8"):
                insert = position
                break
            insert = max(insert, position + 1)
        ending = (
            _line_ending(placeholder_line, newline)
            if placeholder_line is not None
            else newline
        )
        stale_content.insert(insert, stale_entry + ending)
    lines[stale_start + 1 : stale_end] = stale_content
    return _replace_lines_preserve_final(lines, parsed["final_newline"])


def _topic_bytes(value: str) -> bytes:
    return value.encode("utf-8")


def _validate_requested_projection(
    request: Mapping[str, Any],
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    subdomain_text: str,
    topic_text: str,
) -> Findings:
    registry_findings = atlas_state.validate_documents(
        manifest_text, topics_text, relations_text
    )
    if registry_findings:
        return _registry_invalid(registry_findings)
    topics_table = atlas_state._parse_table("topics", topics_text)
    parsed_subdomain, subdomain_findings = _validate_subdomain(
        subdomain_text, {**request, "_topics_text": topics_text}
    )
    if subdomain_findings or parsed_subdomain is None:
        return subdomain_findings
    parsed_topic, topic_error = _parse_topic_document(topic_text)
    if topic_error or parsed_topic is None:
        return (
            _finding(
                "TOPIC_RENDER_INVALID",
                _topic_uri(
                    request["domain"], request["subdomain"], request["topic_id"]
                ),
                topic_error or "topic document is invalid",
            ),
        )
    row, row_findings = _topic_row_for_request(topics_table, request)
    if row_findings or row is None:
        return row_findings or (
            _finding(
                "TOPIC_ORPHAN",
                _topic_uri(
                    request["domain"], request["subdomain"], request["topic_id"]
                ),
                "requested topic row is missing",
            ),
        )
    findings = _topic_identity_findings(
        parsed_topic, request, conflict_code="TOPIC_RENDER_INVALID"
    )
    findings.extend(
        _topic_link_findings(
            parsed_topic,
            request,
            {item["Topic ID"]: item for item in _topic_table_rows(topics_table)},
            conflict_code="TOPIC_RENDER_INVALID",
        )
    )
    if findings:
        return _sort_findings(findings)
    findings.extend(
        _projection_findings(
            parsed_subdomain,
            request,
            parsed_topic,
            row,
            conflict_code="TOPIC_RENDER_INVALID",
        )
    )
    return _sort_findings(findings)


def validate_topic_post_state(
    request: Mapping[str, Any],
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    subdomain_text: str,
    topic_text: str,
    *,
    expected_topic_bytes: bytes | None = None,
    expected_subdomain_bytes: bytes | None = None,
    expected_topics_bytes: bytes | None = None,
    baseline_findings: Sequence[atlas_state.Finding] = (),
    request_sha256: str | None = None,
) -> Findings:
    """Validate the requested post-state before a transaction may be applied."""

    findings: list[atlas_state.Finding] = []
    if request_sha256 is not None:
        try:
            canonical = canonical_json(request)
        except (TypeError, ValueError):
            findings.append(
                _finding(
                    "INDEX_REQUEST_INVALID", "args", "request is not canonical JSON"
                )
            )
        else:
            if sha256(canonical) != request_sha256:
                findings.append(
                    _finding("INDEX_REQUEST_INVALID", "args", "request hash changed")
                )
    if (
        expected_topic_bytes is not None
        and _topic_bytes(topic_text) != expected_topic_bytes
    ):
        findings.append(
            _finding(
                "TOPIC_RENDER_INVALID",
                _topic_uri(
                    request["domain"], request["subdomain"], request["topic_id"]
                ),
                "topic candidate bytes changed",
            )
        )
    if (
        expected_subdomain_bytes is not None
        and _topic_bytes(subdomain_text) != expected_subdomain_bytes
    ):
        findings.append(
            _finding(
                "SUBDOMAIN_PROJECTION_INVALID",
                _subdomain_uri(request["domain"], request["subdomain"]),
                "subdomain candidate bytes changed",
            )
        )
    if (
        expected_topics_bytes is not None
        and _topic_bytes(topics_text) != expected_topics_bytes
    ):
        findings.append(
            _finding(
                "REGISTRY_INVALID", TOPICS_URI, "TOPICS.md candidate bytes changed"
            )
        )
    findings.extend(
        _validate_requested_projection(
            request,
            manifest_text,
            topics_text,
            relations_text,
            subdomain_text,
            topic_text,
        )
    )
    current_subdomain, subdomain_findings = _validate_subdomain(
        subdomain_text, {**request, "_topics_text": topics_text}
    )
    if current_subdomain is not None and not subdomain_findings:
        current_baseline = current_subdomain["baseline"]
        if tuple(current_baseline) != tuple(baseline_findings):
            findings.append(
                _finding(
                    "SUBDOMAIN_PROJECTION_INVALID",
                    _subdomain_uri(request["domain"], request["subdomain"]),
                    "baseline subdomain drift changed",
                )
            )
    return _sort_findings(findings)


def prepare_topic(
    request: Any,
    manifest_text: str,
    topics_text: str,
    relations_text: str,
    subdomain_text: str | None | object,
    topic_text_or_missing: str | None | object,
) -> TopicResult:
    """Prepare a deterministic topic confirmation or exact three-target plan."""

    normalized, request_findings = _validate_request(request)
    if request_findings:
        return request_findings
    assert normalized is not None
    request = normalized
    request_hash = sha256(canonical_json(request))
    domain = request["domain"]
    subdomain = request["subdomain"]
    topic_id = request["topic_id"]
    topic_uri = _topic_uri(domain, subdomain, topic_id)
    subdomain_uri = _subdomain_uri(domain, subdomain)

    if not all(
        isinstance(value, str) for value in (manifest_text, topics_text, relations_text)
    ):
        invalid = [
            _finding(
                "REGISTRY_INVALID",
                path,
                "registry snapshot must be text",
            )
            for value, path in (
                (manifest_text, MANIFEST_URI),
                (topics_text, TOPICS_URI),
                (relations_text, RELATIONS_URI),
            )
            if not isinstance(value, str)
        ]
        return _sort_findings(invalid)
    registry_findings = atlas_state.validate_documents(
        manifest_text, topics_text, relations_text
    )
    if registry_findings:
        return _registry_invalid(registry_findings)
    topics_table = atlas_state._parse_table("topics", topics_text)
    normalized_event, related_findings = _validate_event_request(request, topics_text)
    if related_findings:
        return related_findings
    assert normalized_event is not None
    request = normalized_event
    topic_rows = _topic_table_rows(topics_table)
    topic_by_id = {row["Topic ID"]: row for row in topic_rows}

    row, row_findings = _topic_row_for_request(topics_table, request)
    if row_findings:
        return row_findings
    subdomain_missing = subdomain_text is None or subdomain_text is MISSING
    parsed_subdomain = None
    if not subdomain_missing:
        if not isinstance(subdomain_text, str):
            return (
                _finding(
                    "SUBDOMAIN_INVALID",
                    subdomain_uri,
                    "subdomain INDEX.md snapshot is not text",
                ),
            )
        parsed_subdomain, subdomain_findings = _validate_subdomain(
            subdomain_text, {**request, "_topics_text": topics_text}
        )
        if subdomain_findings or parsed_subdomain is None:
            return subdomain_findings
    projection_row = (
        None
        if parsed_subdomain is None
        else parsed_subdomain["topic_rows_by_id"].get(topic_id)
    )
    topic_missing = topic_text_or_missing is None or topic_text_or_missing is MISSING
    if topic_missing:
        if row is not None or projection_row is not None:
            path = topic_uri if row is not None else subdomain_uri
            return (
                _finding(
                    "TOPIC_ORPHAN",
                    path,
                    "topic registry/projection exists without a topic INDEX.md",
                    row=topic_id,
                ),
            )
        if subdomain_missing:
            newline = "\n"
            rendered_parent = _render_new_subdomain(request, newline)
            parsed_subdomain, subdomain_findings = _validate_subdomain(
                rendered_parent, {**request, "_topics_text": topics_text}
            )
            if subdomain_findings or parsed_subdomain is None:
                return subdomain_findings
            subdomain_input = None
        else:
            newline = _detect_newline(subdomain_text)
            subdomain_input = _topic_bytes(subdomain_text)
        related_topic_links = {
            item: (
                _markdown_link_label(_topic_row_semantic_title(topic_by_id[item])),
                topic_by_id[item]["Topic path"],
            )
            for item in request["related_topic_ids"]
        }
        topic_text = _render_topic(request, related_topic_links, newline)
        topics_candidate = _render_topics_registry(topics_text, topics_table, request)
        subdomain_candidate = _render_subdomain(parsed_subdomain, request)
        topic_output = _topic_bytes(topic_text)
        subdomain_output = _topic_bytes(subdomain_candidate)
        topics_output = _topic_bytes(topics_candidate)
        candidate_findings = _validate_requested_projection(
            request,
            manifest_text,
            topics_candidate,
            relations_text,
            subdomain_candidate,
            topic_text,
        )
        if candidate_findings:
            return candidate_findings
        baseline = parsed_subdomain["baseline"]
        paths = {
            "topic": topic_uri,
            "subdomain": subdomain_uri,
            "registry": TOPICS_URI,
        }
        targets = (
            TopicTarget(topic_uri, None, topic_output),
            TopicTarget(subdomain_uri, subdomain_input, subdomain_output),
            TopicTarget(TOPICS_URI, _topic_bytes(topics_text), topics_output),
        )
        namespace = topic_namespace_sha256(request)
        base_id = topic_base_transaction_id(request, targets)
        event_record = {
            "version": VERSION,
            "event_type": TOPIC_CREATE_EVENT_TYPE,
            "owner": TOPIC_OWNER_ID,
            "topic_namespace_sha256": namespace,
            "base_transaction_id": base_id,
            "request_sha256": request_hash,
            "request": request,
        }
        post = TopicPostValidation(
            _frozen_mapping(request),
            request_hash,
            topic_output,
            subdomain_output,
            topics_output,
            baseline,
        )
        output_revisions = _frozen_mapping(
            {
                "topic": targets[0].output_revision,
                "subdomain": targets[1].output_revision,
                "registry": targets[2].output_revision,
            }
        )
        return TopicPlan(
            _frozen_mapping(request),
            request_hash,
            _frozen_mapping(event_record),
            targets,
            post,
            baseline,
            _frozen_mapping(paths),
            output_revisions,
            topic_namespace=namespace,
            base_transaction_id=base_id,
        )

    if subdomain_missing:
        return (
            _finding(
                "SUBDOMAIN_INVALID",
                subdomain_uri,
                "subdomain INDEX.md is missing",
            ),
        )
    if not isinstance(topic_text_or_missing, str):
        return (
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                topic_uri,
                "topic INDEX.md snapshot is not text",
            ),
        )
    if row is None or projection_row is None:
        return (
            _finding(
                "TOPIC_ORPHAN",
                topic_uri,
                "topic INDEX.md and canonical projections are not a complete pair",
                row=topic_id,
            ),
        )
    parsed_topic, topic_error = _parse_topic_document(topic_text_or_missing)
    if topic_error or parsed_topic is None:
        return (
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                topic_uri,
                topic_error or "topic document is invalid",
                row=topic_id,
            ),
        )
    if parsed_topic["values"].get("topic") != topic_id:
        return (
            _finding(
                "TOPIC_PATH_EXISTS",
                topic_uri,
                "topic INDEX.md path belongs to another topic ID",
                row=parsed_topic["values"].get("topic"),
            ),
        )
    identity_findings = _topic_identity_findings(parsed_topic, request)
    identity_findings.extend(_topic_link_findings(parsed_topic, request, topic_by_id))
    if not _raw_scalar_matches(
        _topic_row_raw(row, "Topic ID"),
        topic_id,
        reserved=("|",),
    ):
        identity_findings.append(
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                TOPICS_URI,
                "canonical Topic ID disagrees with request",
                row=topic_id,
            )
        )
    expected_topic_rel = _topic_relative(domain, subdomain, topic_id)
    if not _raw_scalar_matches(
        _topic_row_raw(row, "Topic path"),
        expected_topic_rel,
        reserved=("|",),
    ):
        identity_findings.append(
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                topic_uri,
                "canonical TOPICS.md path disagrees with request",
                row=topic_id,
            )
        )
    if not _raw_scalar_matches(
        _topic_row_raw(row, "Canonical title"),
        request["canonical_title"],
        reserved=("|",),
    ):
        identity_findings.append(
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                TOPICS_URI,
                "canonical title disagrees with request",
                row=topic_id,
            )
        )
    aliases, include_terms, exclude_terms = _row_lists(row)
    if aliases is None or include_terms is None or exclude_terms is None:
        identity_findings.append(
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                TOPICS_URI,
                "topic registry list field is invalid",
                row=topic_id,
            )
        )
    else:
        list_fields = (
            (
                "Aliases",
                aliases,
                request["aliases"],
                "canonical aliases disagree with request",
            ),
            (
                "Include terms",
                include_terms,
                request["include_terms"],
                "canonical include terms disagree with request",
            ),
            (
                "Exclude terms",
                exclude_terms,
                request["exclude_terms"],
                "canonical exclude terms disagree with request",
            ),
        )
        for field, _actual, expected, detail in list_fields:
            if not _raw_table_list_matches(
                _topic_row_raw(row, field),
                expected,
            ):
                identity_findings.append(
                    _finding(
                        "TOPIC_COMPATIBILITY_CONFLICT",
                        TOPICS_URI,
                        detail,
                        row=topic_id,
                    )
                )
    if not all(
        _raw_scalar_matches(
            _topic_row_raw(row, field),
            expected,
            reserved=("|",),
        )
        for field, expected in (
            ("Domain", domain),
            ("Subdomain", subdomain),
            ("Refresh model", request["refresh_model"]),
        )
    ):
        identity_findings.append(
            _finding(
                "TOPIC_COMPATIBILITY_CONFLICT",
                TOPICS_URI,
                "canonical topic scope or refresh model disagrees with request",
                row=topic_id,
            )
        )
    identity_findings.extend(
        _projection_findings(parsed_subdomain, request, parsed_topic, row)
    )
    if identity_findings:
        return _sort_findings(identity_findings)

    revisions = _frozen_mapping(
        {
            "topic": "sha256:" + sha256(_topic_bytes(topic_text_or_missing)),
            "subdomain": "sha256:" + sha256(_topic_bytes(subdomain_text)),
            "registry": "sha256:" + sha256(_topic_bytes(topics_text)),
        }
    )
    return TopicConfirmation(
        _frozen_mapping(request),
        request_hash,
        _frozen_mapping(
            {"topic": topic_uri, "subdomain": subdomain_uri, "registry": TOPICS_URI}
        ),
        revisions,
        TopicValidation(True, ()),
    )


__all__ = [
    "Findings",
    "TopicResult",
    "TopicConfirmation",
    "TopicPlan",
    "TopicPostValidation",
    "TopicTransactionBinding",
    "TOPIC_OWNER_ID",
    "TOPIC_CREATE_EVENT_TYPE",
    "_validate_event_request",
    "TopicTarget",
    "TopicValidation",
    "canonical_json",
    "prepare_topic",
    "sha256",
    "topic_namespace_sha256",
    "topic_base_transaction_id",
    "topic_base_identity",
    "validate_topic_post_state",
    "load_topic_binding",
]
