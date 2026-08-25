from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any
import atlas_cli
import atlas_discovery
import atlas_index
import atlas_quality
import atlas_research
import atlas_source
import atlas_transaction
import atlas_state
import atlas_url
from atlas_connector import (
    ConnectorBindingError,
    ConnectorConflictError,
    ConnectorDurabilityError,
    ConnectorIOError,
    ConnectorMutationUnavailableError,
    LocalFilesystemConnector,
    resolve_profile,
)

VERSION = 1
ROOT = "vault://atlas/"
MANIFEST = ROOT + "summaries/sources/MANIFEST.md"
TOPICS = ROOT + "summaries/registry/TOPICS.md"
RELATIONS = ROOT + "summaries/registry/RELATIONS.md"
VOCAB = ROOT + "summaries/registry/VOCAB.md"
TRANSACTION_ROOT = ".atlas/transactions"
PRODUCT_ROOT = Path(__file__).resolve().parents[1]
WORKER_SCHEMA_PATH = (
    PRODUCT_ROOT
    / ".agents"
    / "skills"
    / "atlas-core"
    / "assets"
    / "source-worker-result.schema.json"
)
PROPOSAL_SCHEMA_PATH = WORKER_SCHEMA_PATH.with_name(
    "source-summary-proposal.schema.json"
)


@dataclass(frozen=True)
class OperationSpec:
    literal: str
    handler: Callable[[Any | None, Any], dict[str, Any]]
    command: tuple[str, str]
    audience: str
    access: str
    required: frozenset[str]
    optional: frozenset[str]
    connector_methods: frozenset[str]
    lifecycle_class: str
    preview_operation: str | None
    recovery_operation: str | None
    contract_anchor: str
    summary: str


_REVISION = re.compile(r"(?:missing|sha256:[0-9a-f]{64})\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_TX_ID = re.compile(r"[0-9a-f]{16}-a[0-9]{6}\Z")
_EFFECT_ID = re.compile(r"effect-[0-9]{4,}\Z")
_MEMBER_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
_INDEX_TOPIC_RELATIVE = re.compile(
    r"^summaries/research/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*/topics/[a-z0-9][a-z0-9-]*/INDEX\.md\Z"
)
_INDEX_SUBDOMAIN_RELATIVE = re.compile(
    r"^summaries/research/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*/INDEX\.md\Z"
)
_INDEX_TERMINALS = ("applied", "no-op", "aborted", "rolled-back", "manual-conflict")


class Failure(ValueError):
    def __init__(
        self,
        code: str,
        path: str,
        detail: str,
        findings: list[dict[str, str]] | None = None,
        *,
        result: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.code, self.path, self.detail = code, path, detail
        self.findings = findings
        self.result = result


class _UnicodeScalarError(ValueError):
    def __init__(self, path: str) -> None:
        super().__init__("value contains an invalid Unicode scalar")
        self.path = path


class _DuplicateJsonKeyError(ValueError):
    """The public request JSON contains a duplicate object key."""


def _unique_public_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError
        result[key] = value
    return result


class _IndexPostValidationError(atlas_transaction.TransactionError):
    """Owner post-state semantics failed, rather than connector recovery."""


class _IndexJournalProbeError(OSError):
    def __init__(
        self,
        transaction_id: str | None,
        failed_path: str,
    ) -> None:
        super().__init__("transaction journal probe failed")
        self.transaction_id = transaction_id
        self.failed_path = failed_path
        matches = re.findall(r"[0-9a-f]{16}-a[0-9]{6}", failed_path)
        self.failed_transaction_id = matches[-1] if matches else transaction_id


def _assert_unicode_scalars(value: Any, path: str = "request") -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise _UnicodeScalarError(path)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("object keys must be text")
            if any(0xD800 <= ord(char) <= 0xDFFF for char in key):
                raise _UnicodeScalarError(path)
            child_path = (
                key
                if path == "request" and key in {"version", "op", "args"}
                else f"{path}.{key}"
            )
            _assert_unicode_scalars(item, child_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_unicode_scalars(item, f"{path}[{index}]")


def _json(value: Any) -> bytes:
    return atlas_cli.encode(value)


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _finding(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _findings(items: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    return atlas_cli.normalize_findings(items)


def _finding_disposition(items: Sequence[dict[str, str]]) -> str:
    codes = {item["code"] for item in items}
    if codes & {"MANUAL_CONFLICT", "QUARANTINED_NOT_ERASED"}:
        return "manual-intervention"
    if codes & {"TRANSACTION_RECOVERABLE", "REFRESH_RECOVERABLE"}:
        return "recovery-required"
    if "FRAMEWORK_INTERNAL_ERROR" in codes:
        return "internal-error"
    if codes & {
        "BINDING_INVALID",
        "CAPABILITY_UNAVAILABLE",
        "IO_FAILURE",
        "MUTATION_UNAVAILABLE",
    }:
        return "unavailable"
    return "rejected"


def _response(
    op: str | None,
    result: Mapping[str, Any] | None = None,
    findings: Sequence[dict[str, str]] = (),
    *,
    disposition: str | None = None,
    recovery: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    found = _findings(findings)
    selected = disposition or (_finding_disposition(found) if found else "completed")
    if selected == "recovery-required" and recovery is None:
        selected = "manual-intervention"
    return atlas_cli.response(
        op,
        selected,
        result=result,
        findings=found,
        recovery=recovery,
    )


def _error(
    op: str | None,
    code: str,
    path: str,
    detail: str,
    *,
    result: Mapping[str, Any] | None = None,
    recovery: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _response(
        op,
        result=result,
        findings=[_finding(code, path, detail)],
        recovery=recovery,
    )


def _object(value: Any, path: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise Failure("REQUEST_INVALID", path, "expected an object")
    return value


def _args(value: Any, fields: set[str], op: str) -> dict[str, Any]:
    data = _object(value, "args")
    if set(data) != fields:
        raise Failure(
            "ARGUMENTS_INVALID", "args", f"{op} requires exactly {sorted(fields)!r}"
        )
    return data


def _source_worker_schema() -> dict[str, Any]:
    """Load fixed product schemas and return their native transport projection."""
    try:
        worker_schema = json.loads(WORKER_SCHEMA_PATH.read_text(encoding="utf-8"))
        proposal_schema = json.loads(PROPOSAL_SCHEMA_PATH.read_text(encoding="utf-8"))
        schema = atlas_source.project_worker_transport_schema(
            worker_schema,
            proposal_schema,
        )
        return {"schema": schema}
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        atlas_source.SourceError,
    ) as exc:
        raise Failure(
            "WORKER_SCHEMA_INVALID",
            "assets",
            "worker transport schema assets are invalid",
        ) from exc


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise Failure("REQUEST_INVALID", path, "expected text")
    return value


def _uri(value: Any, path: str, *, root: bool = False) -> str:
    uri = _text(value, path)
    if not uri.startswith(ROOT):
        raise Failure("PATH_INVALID", path, "expected a vault://atlas/ URI")
    relative = uri.removeprefix(ROOT)
    if not relative:
        if root:
            return uri
        raise Failure("PATH_INVALID", path, "a file URI is required")
    if relative.startswith("/") or relative.endswith("/") or "?" in uri or "#" in uri:
        raise Failure("PATH_INVALID", path, "logical URI is invalid")
    return uri


def _relative(uri: str) -> str:
    return uri.removeprefix(ROOT)


def _logical(relative: str) -> str:
    return ROOT + relative


def _record_path(path: str) -> str:
    return path if path.startswith(ROOT) else _logical(path)


def _record_failure(exc: atlas_transaction.TransactionRecordError) -> Failure:
    return Failure(
        "TRANSACTION_RECORD_INVALID",
        _record_path(exc.path),
        exc.detail,
    )


def _connector(value: Any | None) -> Any:
    if value is not None:
        return value
    try:
        return LocalFilesystemConnector(resolve_profile())
    except (OSError, ValueError) as exc:
        raise Failure("BINDING_INVALID", "profile", str(exc)) from exc


def _capabilities(connector: Any) -> Mapping[str, Any]:
    try:
        result = connector.capabilities()
    except OSError as exc:
        raise Failure("IO_FAILURE", "connector", str(exc)) from exc
    except (AttributeError, TypeError, ValueError) as exc:
        raise Failure("BINDING_INVALID", "connector", str(exc)) from exc
    if not isinstance(result, Mapping):
        raise Failure("BINDING_INVALID", "connector", "capabilities are invalid")
    operations = result.get("operations")
    if (
        result.get("logical_root") != ROOT
        or type(operations) is not list
        or any(not isinstance(item, str) or not item for item in operations)
        or len(set(operations)) != len(operations)
    ):
        raise Failure("BINDING_INVALID", "connector", "capabilities are invalid")
    return result


def _require_connector_methods(
    connector: Any,
    methods: Sequence[str],
    *,
    write: bool,
) -> None:
    capabilities = _capabilities(connector)
    declared = set(capabilities["operations"])
    missing = sorted(set(methods) - declared)
    if missing:
        raise Failure(
            "MUTATION_UNAVAILABLE" if write else "CAPABILITY_UNAVAILABLE",
            "connector",
            f"connector does not provide {missing[0]}",
        )
    for name in methods:
        try:
            method = getattr(connector, name, None)
        except Exception as exc:
            raise Failure(
                "BINDING_INVALID",
                "connector",
                f"declared connector method {name} could not be resolved",
            ) from exc
        if not callable(method):
            raise Failure(
                "BINDING_INVALID",
                "connector",
                f"declared connector method {name} is not callable",
            )


def _connector_methods_available(
    connector: Any,
    methods: Collection[str],
) -> bool:
    for name in methods:
        try:
            if not callable(getattr(connector, name, None)):
                return False
        except Exception:
            return False
    return True


def _mutations(connector: Any) -> None:
    _require_connector_methods(
        connector,
        ("mutation_session", "conditional_replace"),
        write=True,
    )


def _owner_findings(values: Sequence[Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for value in values:
        if isinstance(value, Mapping):
            code, path, detail = (
                value.get("code"),
                value.get("path"),
                value.get("detail", ""),
            )
            line, row = value.get("line"), value.get("row")
        else:
            code, path, detail = (
                getattr(value, "code", None),
                getattr(value, "path", None),
                getattr(value, "detail", ""),
            )
            line, row = getattr(value, "line", None), getattr(value, "row", None)
        if (
            not isinstance(code, str)
            or not isinstance(path, str)
            or not isinstance(detail, str)
            or (line is not None and (type(line) is not int or line < 1))
            or (row is not None and not isinstance(row, str))
        ):
            raise Failure(
                "OWNER_OUTPUT_INVALID", "findings", "owner returned an invalid finding"
            )
        if line is not None or row is not None:
            contextual_detail: dict[str, Any] = {"detail": detail}
            if line is not None:
                contextual_detail["line"] = line
            if row is not None:
                contextual_detail["row"] = row
            detail = json.dumps(
                contextual_detail,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        result.append(_finding(code, path, detail))
    return _findings(result)


def _reject(values: Sequence[Any]) -> None:
    findings = _owner_findings(values)
    if findings:
        first = findings[0]
        raise Failure(first["code"], first["path"], first["detail"], findings)


def _documents(connector: Any) -> dict[str, str]:
    return {
        "manifest": connector.read_text(MANIFEST),
        "topics": connector.read_text(TOPICS),
        "relations": connector.read_text(RELATIONS),
    }


def _doc_uri(name: str) -> str:
    return {"manifest": MANIFEST, "topics": TOPICS, "relations": RELATIONS}[name]


def _validate(docs: Mapping[str, str]) -> None:
    _reject(
        atlas_state.validate_documents(
            docs["manifest"],
            docs["topics"],
            docs["relations"],
            vocab_text=docs.get("vocab"),
        )
    )


def _snapshot_text(entry: object, path: str) -> dict[str, Any]:
    if not isinstance(entry, Mapping):
        raise Failure(
            "BINDING_INVALID", "connector", "consistent-read result is invalid"
        )
    data = entry.get("bytes")
    revision = entry.get("revision")
    if revision == "missing" and data is None:
        return {"revision": "missing", "text": None}
    if not isinstance(data, bytes) or not isinstance(revision, str):
        raise Failure(
            "BINDING_INVALID", "connector", "consistent-read result is invalid"
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Failure(
            "TOPIC_INSPECTION_UNAVAILABLE",
            path,
            "snapshot text is not valid UTF-8",
        ) from exc
    return {"revision": revision, "text": text}


def _topic_inspect(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"topic_id", "purpose"}, "topic.inspect")
    topic_id = _text(value["topic_id"], "args.topic_id")
    purpose = _text(value["purpose"], "args.purpose")
    try:
        candidate_documents = _documents(connector)
        candidate_selection = atlas_state.select_topic_state(
            candidate_documents, topic_id
        )
        candidate_paths = candidate_selection.paths_for(purpose)
        registry_uris = {
            "manifest": MANIFEST,
            "topics": TOPICS,
            "relations": RELATIONS,
        }
        snapshot = connector.consistent_read(
            [*registry_uris.values(), *(_logical(path) for path in candidate_paths)]
        )
        decoded = {uri: _snapshot_text(entry, uri) for uri, entry in snapshot.items()}
        documents = {name: decoded[uri]["text"] for name, uri in registry_uris.items()}
        registry_revisions = {
            name: decoded[uri]["revision"] for name, uri in registry_uris.items()
        }
        locked_selection = atlas_state.select_topic_state(documents, topic_id)
        candidate_selection.require_locked_match(locked_selection)
        artifacts = {path: decoded[_logical(path)] for path in candidate_paths}
        return atlas_state.inspect_topic(
            documents,
            artifacts,
            topic_id,
            purpose,
            registry_revisions,
        )
    except atlas_state.TopicInspectionError as exc:
        raise Failure(exc.code, exc.path, exc.detail) from exc
    except FileNotFoundError as exc:
        raise Failure(
            "TOPIC_INSPECTION_UNAVAILABLE",
            "artifacts",
            "required artifact snapshot is unavailable",
        ) from exc


def _reduce(
    docs: Mapping[str, str], event: Mapping[str, Any], *, refresh: bool = False
) -> atlas_state.ReductionResult:
    result = atlas_state.reduce_event(docs, event)
    if result.ok:
        return result
    findings = _owner_findings(result.findings)
    if refresh and any(
        item["code"] == "REFRESH_PENDING_SET_MISMATCH" for item in findings
    ):
        raise Failure(
            "REFRESH_EDGE_SET_MISMATCH",
            "projection.edge_ids",
            "the ordered edge set is not the complete pending set",
        )
    first = findings[0]
    raise Failure(first["code"], first["path"], first["detail"], findings)


def _rows(
    text: str, header: Sequence[str], path: str
) -> list[tuple[dict[str, str], str]]:
    lines = text.splitlines(keepends=True)
    try:
        start = (
            next(
                index
                for index, line in enumerate(lines)
                if tuple(atlas_state.split_markdown_row(line) or ()) == tuple(header)
            )
            + 2
        )
    except StopIteration as exc:
        raise Failure(
            "STATE_INVALID", path, "canonical table header is missing"
        ) from exc
    result: list[tuple[dict[str, str], str]] = []
    for raw in lines[start:]:
        cells = atlas_state.split_markdown_row(raw)
        if cells is None or len(cells) != len(header):
            break
        result.append((dict(zip(header, cells, strict=True)), raw))
    return result


def _source_manifest_row(row: Mapping[str, str]) -> dict[str, Any]:
    return {
        "source_seq": int(row["Source seq"]),
        "source_id": row["Source ID"],
        "canonical_url": row["Canonical URL"],
        "artifact_uri": _logical(row["Artifact"]),
        "first_seen": row["First seen"],
        "last_checked": row["Last checked"],
        "last_summarized": row["Last summarized"],
        "content_hash": row["Content hash"],
        "refresh_after": row["Refresh after"],
        "route_status": row["Route status"],
        "status": row["Status"],
    }


def _source_lookup(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"url"}, "source.lookup")
    try:
        canonical_url = atlas_url.normalize_canonical_url(
            _text(value["url"], "args.url")
        )
    except ValueError as exc:
        raise Failure("URL_INVALID", "args.url", str(exc)) from exc

    try:
        manifest_bytes = connector.read_bytes(MANIFEST)
    except OSError as exc:
        raise Failure("IO_FAILURE", MANIFEST, str(exc)) from exc
    try:
        manifest_text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Failure(
            "MANIFEST_UTF8_INVALID", MANIFEST, "manifest is not valid UTF-8"
        ) from exc

    row, findings = atlas_state.lookup_manifest_row(manifest_text, canonical_url)
    _reject(findings)
    result_row = None if row is None else _source_manifest_row(row)
    return {
        "canonical_url": canonical_url,
        "manifest_revision": "sha256:" + _hash(manifest_bytes),
        "row": result_row,
    }


def _source_inventory(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"intent", "checked_on", "inputs"}, "source.inventory")
    intent = _text(value["intent"], "args.intent")
    if intent not in {"presence", "routine", "resummarize"}:
        raise Failure("REQUEST_INVALID", "args.intent", "intent is invalid")
    checked_on = _text(value["checked_on"], "args.checked_on")
    try:
        if date.fromisoformat(checked_on).isoformat() != checked_on:
            raise ValueError
    except ValueError as exc:
        raise Failure(
            "REQUEST_INVALID", "args.checked_on", "expected YYYY-MM-DD"
        ) from exc
    if type(value["inputs"]) is not list or not value["inputs"]:
        raise Failure(
            "REQUEST_INVALID", "args.inputs", "inputs must be a nonempty array"
        )

    inputs: list[dict[str, Any]] = []
    for index, item in enumerate(value["inputs"]):
        row = _object(item, f"args.inputs[{index}]")
        if set(row) != {"label", "url", "depth"}:
            raise Failure(
                "REQUEST_INVALID",
                f"args.inputs[{index}]",
                "input fields are invalid",
            )
        label = _text(row["label"], f"args.inputs[{index}].label")
        if not label:
            raise Failure(
                "REQUEST_INVALID",
                f"args.inputs[{index}].label",
                "label must be nonempty",
            )
        url = _text(row["url"], f"args.inputs[{index}].url")
        if type(row["depth"]) is not int or row["depth"] not in {0, 1}:
            raise Failure(
                "REQUEST_INVALID",
                f"args.inputs[{index}].depth",
                "depth must be 0 or 1",
            )
        inputs.append({"label": label, "url": url, "depth": row["depth"]})

    try:
        manifest_bytes = connector.read_bytes(MANIFEST)
    except OSError as exc:
        raise Failure("IO_FAILURE", MANIFEST, str(exc)) from exc
    try:
        manifest_text = manifest_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Failure(
            "MANIFEST_UTF8_INVALID", MANIFEST, "manifest is not valid UTF-8"
        ) from exc
    manifest_rows, findings = atlas_state.validated_manifest_rows(manifest_text)
    _reject(findings)
    manifest_by_url = {row["Canonical URL"]: row for row in manifest_rows}

    normalized: list[dict[str, Any]] = []
    source_urls: dict[str, set[str]] = {}
    for index, item in enumerate(inputs):
        entry: dict[str, Any] = {
            "input_index": index,
            "label": item["label"],
            "depth": item["depth"],
        }
        try:
            canonical_url = atlas_url.normalize_canonical_url(item["url"])
        except ValueError as exc:
            entry.update(
                {
                    "disposition": "rejected",
                    "findings": [
                        {
                            "code": "URL_INVALID",
                            "path": f"args.inputs[{index}].url",
                            "detail": str(exc),
                        }
                    ],
                }
            )
        else:
            source_id = atlas_url.source_id_for(canonical_url)
            entry.update({"canonical_url": canonical_url, "source_id": source_id})
            source_urls.setdefault(source_id, set()).add(canonical_url)
        normalized.append(entry)

    collisions = {source_id for source_id, urls in source_urls.items() if len(urls) > 1}
    winners: dict[str, int] = {}
    for entry in normalized:
        if entry.get("disposition") == "rejected":
            continue
        canonical_url = entry["canonical_url"]
        source_id = entry["source_id"]
        if source_id in collisions:
            entry.update(
                {
                    "disposition": "rejected",
                    "findings": [
                        {
                            "code": "SOURCE_ID_COLLISION",
                            "path": f"args.inputs[{entry['input_index']}].url",
                            "detail": "distinct canonical URLs have the same source ID",
                        }
                    ],
                }
            )
            continue
        winner = winners.get(canonical_url)
        if winner is not None:
            entry.update(
                {
                    "disposition": "duplicate",
                    "winner_input_index": winner,
                    "manifest_row": (
                        None
                        if canonical_url not in manifest_by_url
                        else _source_manifest_row(manifest_by_url[canonical_url])
                    ),
                    "findings": [],
                }
            )
            continue
        winners[canonical_url] = entry["input_index"]
        row = manifest_by_url.get(canonical_url)
        if row is None:
            disposition = "new"
        elif row["Status"] == "archived":
            disposition = "archived"
        elif intent == "routine":
            refresh_after = row["Refresh after"]
            disposition = (
                "active-due"
                if not refresh_after or refresh_after <= checked_on
                else "active-not-due"
            )
        else:
            disposition = "active"
        entry.update(
            {
                "disposition": disposition,
                "winner_input_index": entry["input_index"],
                "manifest_row": (None if row is None else _source_manifest_row(row)),
                "findings": [],
            }
        )
    result: dict[str, Any] = {
        "intent": intent,
        "checked_on": checked_on,
        "manifest_revision": "sha256:" + _hash(manifest_bytes),
        "entries": normalized,
    }
    return result


def _source_candidates_for_topic(connector: Any, args: Any) -> dict[str, Any]:
    raw = _object(args, "args")
    required = {"topic_id", "named_urls"}
    if set(raw) != required and set(raw) != required | {"source_id"}:
        raise Failure(
            "ARGUMENTS_INVALID",
            "args",
            "source.candidates_for_topic requires topic_id, named_urls, and optional source_id",
        )
    topic_id = _text(raw["topic_id"], "args.topic_id")
    if atlas_state.VOCAB_ID_RE.fullmatch(topic_id) is None:
        raise Failure("REQUEST_INVALID", "args.topic_id", "topic ID must be canonical")
    raw_named_urls = raw["named_urls"]
    if type(raw_named_urls) is not list:
        raise Failure(
            "REQUEST_INVALID", "args.named_urls", "named_urls must be an array"
        )
    named_urls: list[str] = []
    seen_urls: set[str] = set()
    for index, value in enumerate(raw_named_urls):
        if not isinstance(value, str):
            raise Failure(
                "REQUEST_INVALID",
                f"args.named_urls[{index}]",
                "named URL must be text",
            )
        try:
            canonical_url = atlas_url.normalize_canonical_url(value)
        except ValueError as exc:
            raise Failure(
                "REQUEST_INVALID", f"args.named_urls[{index}]", str(exc)
            ) from exc
        if canonical_url not in seen_urls:
            seen_urls.add(canonical_url)
            named_urls.append(canonical_url)
    source_id: str | None = None
    if "source_id" in raw:
        source_id = _text(raw["source_id"], "args.source_id")
        if atlas_state.SOURCE_ID_RE.fullmatch(source_id) is None:
            raise Failure("REQUEST_INVALID", "args.source_id", "source ID is invalid")

    registry_uris = {
        "manifest": MANIFEST,
        "topics": TOPICS,
        "relations": RELATIONS,
        "vocab": VOCAB,
    }
    preliminary_documents = {
        name: connector.read_text(uri) for name, uri in registry_uris.items()
    }
    preliminary = atlas_state.select_source_candidate_scope(
        preliminary_documents,
        topic_id,
        named_urls,
        source_id=source_id,
    )
    preliminary_rows, _ = atlas_state.validated_manifest_rows(
        preliminary_documents["manifest"]
    )
    artifact_superset = tuple(
        dict.fromkeys(
            row["Artifact"] for row in preliminary_rows if row["Status"] == "active"
        )
    )
    paths = [
        *registry_uris.values(),
        *(_logical(path) for path in artifact_superset),
    ]
    snapshot = connector.consistent_read(paths)
    if not isinstance(snapshot, Mapping) or set(snapshot) != set(paths):
        raise Failure(
            "SOURCE_CANDIDATE_SNAPSHOT_INVALID",
            "snapshot",
            "consistent-read path set is invalid",
        )
    decoded = {uri: _snapshot_text(snapshot[uri], uri) for uri in paths}
    if any(decoded[uri]["text"] is None for uri in registry_uris.values()):
        raise Failure(
            "SOURCE_CANDIDATE_STATE_INVALID",
            "snapshot",
            "canonical registry is missing",
        )
    locked_documents = {
        name: decoded[uri]["text"] for name, uri in registry_uris.items()
    }
    locked = atlas_state.select_source_candidate_scope(
        locked_documents,
        topic_id,
        named_urls,
        source_id=source_id,
    )
    if locked.findings:
        return {
            "state": "rejected",
            "findings": _owner_findings(locked.findings),
        }
    try:
        preliminary.require_locked_match(locked)
        if locked.state == "absent":
            return {
                "state": "terminal",
                "outcome": "topic-absent",
                "topic_id": topic_id,
                "candidates": [],
                "gaps": [],
            }
        projections: dict[str, Mapping[str, Any]] = {}
        for source in locked.sources:
            artifact_path = source["artifact"]
            artifact_uri = _logical(artifact_path)
            artifact_snapshot = decoded[artifact_uri]
            artifact_text = artifact_snapshot["text"]
            if artifact_text is None:
                raise atlas_state.SourceCandidateError(
                    "SOURCE_CANDIDATE_ARTIFACT_INVALID",
                    artifact_uri,
                    "active source artifact is missing",
                )
            projections[artifact_path] = atlas_source.candidate_artifact_projection(
                artifact_text,
                artifact_snapshot["revision"],
            )
        result = atlas_state.build_source_candidates(
            locked,
            projections,
            vocab_text=locked_documents["vocab"],
            registry_revisions={
                name: decoded[uri]["revision"] for name, uri in registry_uris.items()
            },
        )
    except atlas_state.SourceCandidateError as exc:
        findings = _owner_findings(exc.findings) if exc.findings else None
        raise Failure(exc.code, exc.path, exc.detail, findings) from exc
    except ValueError as exc:
        raise Failure(
            "SOURCE_CANDIDATE_ARTIFACT_INVALID", "artifacts", str(exc)
        ) from exc
    return {"state": "ready", **result}


def _source_prepare(connector: Any, args: Any) -> dict[str, Any]:
    raw_args = _object(args, "args")
    if set(raw_args) == {"mode", "artifact_uri", "evidence_uri"}:
        if raw_args["mode"] != "promote":
            raise Failure(
                "SOURCE_PREPARE_INPUT_INVALID",
                "args.mode",
                "promotion input requires mode promote",
            )
        return _source_prepare_promotion(
            connector,
            {
                "artifact_uri": raw_args["artifact_uri"],
                "evidence_uri": raw_args["evidence_uri"],
            },
        )
    value = _args(raw_args, {"identity", "mode", "worker"}, "source.prepare")
    identity = _object(value["identity"], "args.identity")
    if set(identity) != {"canonical_url", "checked_on"}:
        raise Failure("REQUEST_INVALID", "args.identity", "identity fields are invalid")
    canonical_url = _text(identity["canonical_url"], "args.identity.canonical_url")
    checked_on = _text(identity["checked_on"], "args.identity.checked_on")
    try:
        if atlas_url.normalize_canonical_url(canonical_url) != canonical_url:
            raise ValueError("canonical URL must be normalized")
        if atlas_state.DATE_RE.fullmatch(checked_on) is None:
            raise ValueError("checked_on must be YYYY-MM-DD")
        date.fromisoformat(checked_on)
    except ValueError as exc:
        raise Failure(
            "SOURCE_PREPARE_INPUT_INVALID", "args.identity", str(exc)
        ) from exc
    mode = _text(value["mode"], "args.mode")
    if mode not in {"routine", "resummarize"}:
        raise Failure("SOURCE_PREPARE_INPUT_INVALID", "args.mode", "mode is invalid")
    worker_findings = atlas_source.validate_worker_result(value["worker"])
    if worker_findings:
        return {"state": "rejected", "findings": worker_findings}
    worker = value["worker"]
    assert isinstance(worker, Mapping)
    if worker.get("kind") in {"needs-input", "expanded"}:
        return {
            "state": "rejected",
            "findings": [
                {
                    "code": "WORKER_PACKET_NOT_FINAL",
                    "path": "worker.kind",
                    "detail": "source preparation accepts ready or no-write packets",
                }
            ],
        }

    source_id = atlas_url.source_id_for(canonical_url)
    preliminary_manifest = connector.read_text(MANIFEST)
    preliminary_existing = next(
        (
            row
            for row, _ in _rows(
                preliminary_manifest, atlas_state.MANIFEST_HEADER, MANIFEST
            )
            if row["Source ID"] == source_id
        ),
        None,
    )
    preliminary_binding = (
        None
        if preliminary_existing is None
        else (preliminary_existing["Status"], preliminary_existing["Artifact"])
    )
    artifact_uri = (
        _logical(preliminary_existing["Artifact"])
        if preliminary_existing is not None
        and preliminary_existing["Status"] == "active"
        else None
    )
    registry_uris = {
        "manifest": MANIFEST,
        "topics": TOPICS,
        "relations": RELATIONS,
        "vocab": VOCAB,
    }
    paths = [*registry_uris.values(), *([artifact_uri] if artifact_uri else [])]
    snapshot = connector.consistent_read(paths)
    if not isinstance(snapshot, Mapping) or set(snapshot) != set(paths):
        raise Failure(
            "SOURCE_PREPARE_STALE",
            "snapshot",
            "consistent-read path set is invalid",
        )
    decoded = {uri: _snapshot_text(snapshot[uri], uri) for uri in paths}
    if any(decoded[uri]["text"] is None for uri in registry_uris.values()):
        raise Failure(
            "STATE_INVALID", "snapshot", "canonical source registry is missing"
        )
    docs = {name: decoded[uri]["text"] for name, uri in registry_uris.items()}
    _validate(docs)
    existing = next(
        (
            row
            for row, _ in _rows(docs["manifest"], atlas_state.MANIFEST_HEADER, MANIFEST)
            if row["Source ID"] == source_id
        ),
        None,
    )
    locked_binding = (
        None if existing is None else (existing["Status"], existing["Artifact"])
    )
    if locked_binding != preliminary_binding:
        return {
            "state": "rejected",
            "findings": [
                {
                    "code": "SOURCE_PREPARE_STALE",
                    "path": MANIFEST,
                    "detail": "source binding changed during preparation",
                }
            ],
        }
    living_artifact_text: str | None = None
    living_artifact_revision = "missing"
    if existing is not None and existing["Status"] == "active":
        assert artifact_uri is not None
        living_artifact_text = decoded[artifact_uri]["text"]
        living_artifact_revision = decoded[artifact_uri]["revision"]
        if living_artifact_text is None:
            return {
                "state": "rejected",
                "findings": [
                    {
                        "code": "SOURCE_ARTIFACT_INVALID",
                        "path": artifact_uri,
                        "detail": "active source artifact is missing",
                    }
                ],
            }
    prepared = atlas_source.prepare_source(
        docs,
        canonical_url=canonical_url,
        checked_on=checked_on,
        mode=mode,
        worker=value["worker"],
        living_artifact_text=living_artifact_text,
    )
    if prepared["state"] != "prepared":
        return prepared

    targets: list[dict[str, str]] = []
    vocab_replacement = prepared["documents"].get("vocab")
    if vocab_replacement is not None and vocab_replacement != docs["vocab"]:
        targets.append(
            {
                "path": VOCAB,
                "expected_revision": decoded[VOCAB]["revision"],
                "text": vocab_replacement,
            }
        )
    artifact_text = prepared["artifact_text"]
    if artifact_text is not None and (
        living_artifact_text is None or artifact_text != living_artifact_text
    ):
        targets.append(
            {
                "path": _logical(prepared["artifact_path"]),
                "expected_revision": living_artifact_revision,
                "text": artifact_text,
            }
        )
    for name, uri in (
        ("relations", RELATIONS),
        ("topics", TOPICS),
        ("manifest", MANIFEST),
    ):
        replacement = prepared["documents"].get(name)
        if replacement is not None and replacement != docs[name]:
            targets.append(
                {
                    "path": uri,
                    "expected_revision": decoded[uri]["revision"],
                    "text": replacement,
                }
            )
    if not targets:
        return {
            "state": "terminal",
            "outcome": "unchanged",
            "reason": "source preparation has no changed targets",
        }
    try:
        event_record = atlas_source.build_event_record(
            event_type="source-upsert",
            source_id=source_id,
            event=prepared["event"],
            route_decision=None,
        )
    except ValueError as exc:
        return {
            "state": "rejected",
            "findings": [
                {
                    "code": "SOURCE_PREPARE_INVALID",
                    "path": "worker",
                    "detail": str(exc),
                }
            ],
        }
    return {
        "state": "prepared",
        "outcome": prepared["outcome"],
        "route_required": prepared["route_required"],
        "transaction": {"event_record": event_record, "targets": targets},
    }


def _route_prepare_revision(value: Any, path: str) -> str:
    revision = _text(value, path)
    if re.fullmatch(r"sha256:[0-9a-f]{64}", revision) is None:
        raise Failure("REQUEST_INVALID", path, "expected a SHA-256 revision")
    return revision


def _route_prepare_date(value: Any, path: str) -> str:
    checked = _text(value, path)
    try:
        if date.fromisoformat(checked).isoformat() != checked:
            raise ValueError
    except ValueError as exc:
        raise Failure("REQUEST_INVALID", path, "expected YYYY-MM-DD") from exc
    return checked


def _route_prepare_binding(value: Any) -> dict[str, Any]:
    binding = _object(value, "args.binding")
    if set(binding) != {"canonical_url", "manifest_revision", "row"}:
        raise Failure(
            "REQUEST_INVALID", "args.binding", "lookup binding fields are invalid"
        )
    canonical_url = _text(binding["canonical_url"], "args.binding.canonical_url")
    try:
        if atlas_url.normalize_canonical_url(canonical_url) != canonical_url:
            raise ValueError("canonical URL must be normalized")
    except ValueError as exc:
        raise Failure(
            "REQUEST_INVALID", "args.binding.canonical_url", str(exc)
        ) from exc
    manifest_revision = _route_prepare_revision(
        binding["manifest_revision"], "args.binding.manifest_revision"
    )
    row = _object(binding["row"], "args.binding.row")
    expected_fields = {
        "source_seq",
        "source_id",
        "canonical_url",
        "artifact_uri",
        "first_seen",
        "last_checked",
        "last_summarized",
        "content_hash",
        "refresh_after",
        "route_status",
        "status",
    }
    if set(row) != expected_fields:
        raise Failure(
            "REQUEST_INVALID", "args.binding.row", "lookup row fields are invalid"
        )
    if type(row["source_seq"]) is not int or row["source_seq"] < 1:
        raise Failure(
            "REQUEST_INVALID",
            "args.binding.row.source_seq",
            "source sequence must be a positive integer",
        )
    source_id = _text(row["source_id"], "args.binding.row.source_id")
    if atlas_state.SOURCE_ID_RE.fullmatch(source_id) is None:
        raise Failure(
            "REQUEST_INVALID", "args.binding.row.source_id", "source ID is invalid"
        )
    row_url = _text(row["canonical_url"], "args.binding.row.canonical_url")
    if row_url != canonical_url or atlas_url.source_id_for(canonical_url) != source_id:
        raise Failure(
            "REQUEST_INVALID",
            "args.binding.row",
            "lookup URL and source ID disagree",
        )
    artifact_uri = _uri(row["artifact_uri"], "args.binding.row.artifact_uri")
    first_seen = _route_prepare_date(row["first_seen"], "args.binding.row.first_seen")
    if not atlas_state.source_artifact_path_is_canonical(
        _relative(artifact_uri), source_id, first_seen
    ):
        raise Failure(
            "REQUEST_INVALID",
            "args.binding.row.artifact_uri",
            "source artifact path is invalid",
        )
    for name in ("last_checked", "last_summarized"):
        _route_prepare_date(row[name], f"args.binding.row.{name}")
    content_hash = _text(row["content_hash"], "args.binding.row.content_hash")
    if atlas_state.CONTENT_HASH_RE.fullmatch(content_hash) is None:
        raise Failure(
            "REQUEST_INVALID",
            "args.binding.row.content_hash",
            "content hash is invalid",
        )
    refresh_after = _text(row["refresh_after"], "args.binding.row.refresh_after")
    if refresh_after:
        _route_prepare_date(refresh_after, "args.binding.row.refresh_after")
    if row["route_status"] not in atlas_state.ROUTE_STATUSES:
        raise Failure(
            "REQUEST_INVALID",
            "args.binding.row.route_status",
            "route status is invalid",
        )
    if row["status"] not in atlas_state.SOURCE_STATUSES:
        raise Failure(
            "REQUEST_INVALID", "args.binding.row.status", "source status is invalid"
        )
    return {
        "canonical_url": canonical_url,
        "manifest_revision": manifest_revision,
        "row": dict(row),
    }


def _route_prepare_decision(value: Any) -> dict[str, Any]:
    decision = _object(value, "args.decision")
    if set(decision) != {"outcome", "edges"}:
        raise Failure(
            "REQUEST_INVALID", "args.decision", "route decision fields are invalid"
        )
    outcome = _text(decision["outcome"], "args.decision.outcome")
    if outcome not in {"routed", "no-topic-match", "routing-blocked"}:
        raise Failure(
            "REQUEST_INVALID", "args.decision.outcome", "route outcome is invalid"
        )
    raw_edges = decision["edges"]
    if type(raw_edges) is not list:
        raise Failure(
            "REQUEST_INVALID", "args.decision.edges", "edges must be an array"
        )
    edges: list[dict[str, str]] = []
    topics: set[str] = set()
    expected_fields = {"topic_id", "relation", "impact", "confidence", "reason"}
    for index, item in enumerate(raw_edges):
        edge = _object(item, f"args.decision.edges[{index}]")
        if set(edge) != expected_fields:
            raise Failure(
                "REQUEST_INVALID",
                f"args.decision.edges[{index}]",
                "route edge fields are invalid",
            )
        topic_id = _text(edge["topic_id"], f"args.decision.edges[{index}].topic_id")
        if atlas_index.TOPIC_ID_RE.fullmatch(topic_id) is None or topic_id in topics:
            raise Failure(
                "REQUEST_INVALID",
                f"args.decision.edges[{index}].topic_id",
                "topic ID must be canonical and unique",
            )
        topics.add(topic_id)
        relation = _text(edge["relation"], f"args.decision.edges[{index}].relation")
        impact = _text(edge["impact"], f"args.decision.edges[{index}].impact")
        confidence = _text(
            edge["confidence"], f"args.decision.edges[{index}].confidence"
        )
        if relation not in atlas_state.RELATIONS:
            raise Failure(
                "REQUEST_INVALID",
                f"args.decision.edges[{index}].relation",
                "relation is invalid",
            )
        if impact not in atlas_state.LEVELS:
            raise Failure(
                "REQUEST_INVALID",
                f"args.decision.edges[{index}].impact",
                "impact is invalid",
            )
        if confidence not in atlas_state.LEVELS:
            raise Failure(
                "REQUEST_INVALID",
                f"args.decision.edges[{index}].confidence",
                "confidence is invalid",
            )
        reason = _text(edge["reason"], f"args.decision.edges[{index}].reason")
        match = atlas_state.REASON_RE.fullmatch(reason)
        if (
            match is None
            or match.group("relation") != relation
            or match.group("impact") != impact
        ):
            raise Failure(
                "REQUEST_INVALID",
                f"args.decision.edges[{index}].reason",
                "reason does not match its relation and impact",
            )
        edges.append({name: edge[name] for name in expected_fields})
    if (outcome == "routed") != bool(edges):
        raise Failure(
            "REQUEST_INVALID",
            "args.decision",
            "routed requires edges and other outcomes require none",
        )
    return {"outcome": outcome, "edges": edges}


def _route_snapshot_bytes(
    snapshot: Mapping[str, Any], path: str, expected_revision: str
) -> bytes:
    entry = snapshot.get(path)
    if not isinstance(entry, Mapping) or set(entry) != {"revision", "bytes"}:
        raise Failure(
            "BINDING_INVALID", path, "consistent-read entry fields are invalid"
        )
    revision = entry["revision"]
    raw = entry["bytes"]
    if revision != expected_revision:
        raise Failure("REVISION_STALE", path, "snapshot revision changed")
    if not isinstance(raw, bytes):
        raise Failure("REVISION_STALE", path, "snapshot target is missing")
    return raw


def _source_prepare_route(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(
        args,
        {"binding", "checked_on", "expected_revisions", "decision"},
        "source.prepare_route",
    )
    binding = _route_prepare_binding(value["binding"])
    checked_on = _route_prepare_date(value["checked_on"], "args.checked_on")
    raw_revisions = _object(value["expected_revisions"], "args.expected_revisions")
    if set(raw_revisions) != {"artifact", "topics", "relations", "vocab"}:
        raise Failure(
            "REQUEST_INVALID",
            "args.expected_revisions",
            "expected revision fields are invalid",
        )
    expected_revisions = {
        name: _route_prepare_revision(
            raw_revisions[name], f"args.expected_revisions.{name}"
        )
        for name in ("artifact", "topics", "relations", "vocab")
    }
    decision = _route_prepare_decision(value["decision"])
    artifact_uri = binding["row"]["artifact_uri"]
    paths = [MANIFEST, TOPICS, RELATIONS, VOCAB, artifact_uri]
    snapshot = connector.consistent_read(paths)
    if not isinstance(snapshot, Mapping) or set(snapshot) != set(paths):
        raise Failure(
            "BINDING_INVALID", "connector", "consistent-read path set is invalid"
        )
    expected_by_uri = {
        MANIFEST: binding["manifest_revision"],
        TOPICS: expected_revisions["topics"],
        RELATIONS: expected_revisions["relations"],
        VOCAB: expected_revisions["vocab"],
        artifact_uri: expected_revisions["artifact"],
    }
    raw_by_uri = {
        path: _route_snapshot_bytes(snapshot, path, expected_by_uri[path])
        for path in paths
    }
    decoded: dict[str, str] = {}
    for path, raw in raw_by_uri.items():
        try:
            decoded[path] = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            code = (
                "ROUTE_PREFLIGHT_ARTIFACT_INVALID"
                if path == artifact_uri
                else "STATE_INVALID"
            )
            raise Failure(code, path, "snapshot text is not valid UTF-8") from exc
    documents = {
        "manifest": decoded[MANIFEST],
        "topics": decoded[TOPICS],
        "relations": decoded[RELATIONS],
        "vocab": decoded[VOCAB],
    }
    state_findings = atlas_state.validate_documents(
        documents["manifest"],
        documents["topics"],
        documents["relations"],
        vocab_text=documents["vocab"],
    )
    if state_findings:
        return {"state": "rejected", "findings": _owner_findings(state_findings)}
    rows, _ = atlas_state.validated_manifest_rows(documents["manifest"])
    current = next(
        (row for row in rows if row["Source ID"] == binding["row"]["source_id"]),
        None,
    )
    if current is None:
        raise Failure(
            "ROUTE_PREFLIGHT_SOURCE_MISSING",
            "args.binding.row.source_id",
            "bound source is absent",
        )
    if _source_manifest_row(current) != binding["row"]:
        raise Failure(
            "REVISION_STALE",
            MANIFEST,
            "bound source row differs from the current manifest",
        )
    try:
        artifact_values = atlas_source.parse_artifact(decoded[artifact_uri]).values
        artifact_identity = {
            "source_id": atlas_source.scalar(artifact_values, "source_id"),
            "canonical_url": atlas_source.scalar(artifact_values, "canonical_url"),
            "content_hash": atlas_source.scalar(artifact_values, "content_hash"),
            "route_status": atlas_source.scalar(artifact_values, "routing_status"),
        }
        artifact_taxonomy: dict[str, Any] = {
            "source_kind": atlas_source.scalar(artifact_values, "source_kind"),
            "primary_domain": atlas_source.scalar(artifact_values, "primary_domain"),
            "secondary_domains": json.loads(artifact_values["secondary_domains"]),
            "subdomains": json.loads(artifact_values["subdomains"]),
            "canonical_tags": json.loads(artifact_values["canonical_tags"]),
        }
        for name in ("secondary_domains", "subdomains", "canonical_tags"):
            if not isinstance(artifact_taxonomy[name], list) or any(
                not isinstance(item, str) for item in artifact_taxonomy[name]
            ):
                raise ValueError(f"artifact {name} is invalid")
    except (KeyError, TypeError, ValueError) as exc:
        raise Failure(
            "ROUTE_PREFLIGHT_ARTIFACT_INVALID", artifact_uri, str(exc)
        ) from exc
    expected_identity = {
        name: binding["row"][name]
        for name in ("source_id", "canonical_url", "content_hash", "route_status")
    }
    if artifact_identity != expected_identity:
        raise Failure(
            "ROUTE_PREFLIGHT_HASH_MISMATCH",
            artifact_uri,
            "manifest and artifact identity disagree",
        )
    taxonomy_findings = atlas_state.validate_source_taxonomy(
        documents["vocab"],
        **artifact_taxonomy,
        path=_relative(artifact_uri),
    )
    if taxonomy_findings:
        return {"state": "rejected", "findings": _owner_findings(taxonomy_findings)}
    event = {
        "type": "route-upsert",
        "source_id": binding["row"]["source_id"],
        "content_hash": binding["row"]["content_hash"],
        "checked_on": checked_on,
        "outcome": decision["outcome"],
        "edges": decision["edges"],
    }
    reduction = atlas_state.reduce_event(documents, event)
    if not reduction.ok:
        return {
            "state": "rejected",
            "findings": _owner_findings(reduction.findings),
        }
    try:
        event_record = atlas_source.build_event_record(
            event_type="route-upsert",
            source_id=binding["row"]["source_id"],
            event=event,
            route_decision=decision,
        )
    except ValueError as exc:
        return {
            "state": "rejected",
            "findings": [
                {
                    "code": "SOURCE_PREPARE_INVALID",
                    "path": "args.decision",
                    "detail": str(exc),
                }
            ],
        }
    projection = _route_projection(
        event_record,
        documents,
        reduction,
        _relative(artifact_uri),
        raw_by_uri[artifact_uri],
    )
    if not projection:
        return {
            "state": "terminal",
            "outcome": "unchanged",
            "reason": "route preparation has no changed targets",
        }
    revision_by_path = {
        _relative(MANIFEST): binding["manifest_revision"],
        _relative(TOPICS): expected_revisions["topics"],
        _relative(RELATIONS): expected_revisions["relations"],
        _relative(artifact_uri): expected_revisions["artifact"],
    }
    targets = [
        {
            "path": _logical(path),
            "expected_revision": revision_by_path[path],
            "text": output.decode("utf-8"),
        }
        for path, output in sorted(projection.items(), key=lambda item: _rank(item[0]))
    ]
    return {
        "state": "prepared",
        "transaction": {"event_record": event_record, "targets": targets},
    }


def _promotion_identity(
    manifest_text: str,
    staged_text: str,
    worker: Any,
) -> tuple[str, str, str]:
    staged = atlas_source.parse_artifact(staged_text)
    canonical_url = atlas_source.scalar(staged.values, "canonical_url")
    source_id = atlas_url.source_id_for(canonical_url)
    rows, findings = atlas_state.validated_manifest_rows(manifest_text)
    if findings:
        raise ValueError("source manifest is invalid")
    existing = next(
        (row for row in rows if row["Source ID"] == source_id),
        None,
    )
    if existing is not None:
        return canonical_url, source_id, _logical(existing["Artifact"])
    if not isinstance(worker, Mapping):
        raise ValueError("evidence packet must be an object")
    evidence_bundle = worker.get("evidence_bundle")
    if not isinstance(evidence_bundle, Mapping):
        raise ValueError("evidence bundle must be an object")
    effective_evidence: Mapping[str, Any] = evidence_bundle
    if "first_seen" not in evidence_bundle and "fetched_at" not in evidence_bundle:
        effective_evidence = {
            **evidence_bundle,
            "first_seen": atlas_source.scalar(staged.values, "first_seen"),
        }
    identity = atlas_source.evidence_identity(effective_evidence)
    artifact_path = atlas_source.source_artifact_path(
        identity["first_seen"],
        source_id,
        atlas_source.scalar(staged.values, "title"),
    )
    return canonical_url, source_id, _logical(artifact_path)


def _source_prepare_promotion(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"artifact_uri", "evidence_uri"}, "source.prepare")
    artifact_uri = _uri(value["artifact_uri"], "args.artifact_uri")
    evidence_uri = _uri(value["evidence_uri"], "args.evidence_uri")
    if artifact_uri == evidence_uri:
        raise Failure(
            "SOURCE_PROMOTION_INPUT_INVALID",
            "args",
            "artifact and evidence URIs must differ",
        )

    preliminary = connector.consistent_read([artifact_uri, evidence_uri, MANIFEST])
    try:
        preliminary_revisions: dict[str, str] = {}
        preliminary_bytes: dict[str, bytes] = {}
        for path in (artifact_uri, evidence_uri, MANIFEST):
            entry = preliminary[path]
            if not isinstance(entry, Mapping) or set(entry) != {"revision", "bytes"}:
                raise ValueError("consistent-read entry fields are invalid")
            revision = entry["revision"]
            raw = entry["bytes"]
            if (
                not isinstance(revision, str)
                or _REVISION.fullmatch(revision) is None
                or not isinstance(raw, bytes)
            ):
                raise ValueError("promotion input is missing or invalid")
            preliminary_revisions[path] = revision
            preliminary_bytes[path] = raw
        staged_text = preliminary_bytes[artifact_uri].decode("utf-8")
        worker = atlas_cli.decode(preliminary_bytes[evidence_uri])
        canonical_url, source_id, target_uri = _promotion_identity(
            preliminary_bytes[MANIFEST].decode("utf-8"),
            staged_text,
            worker,
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        atlas_cli.JsonInputError,
    ) as exc:
        return {
            "state": "rejected",
            "findings": [
                {
                    "code": "SOURCE_PROMOTION_INPUT_INVALID",
                    "path": "args",
                    "detail": str(exc),
                }
            ],
        }
    if target_uri in {artifact_uri, evidence_uri}:
        raise Failure(
            "SOURCE_PROMOTION_INPUT_INVALID",
            "args",
            "promotion inputs must be distinct from the living target",
        )

    paths = [artifact_uri, evidence_uri, MANIFEST, TOPICS, RELATIONS, target_uri]
    snapshot = connector.consistent_read(paths)
    try:
        for path in paths:
            entry = _object(snapshot[path], f"snapshot.{path}")
            if set(entry) != {"revision", "bytes"}:
                raise ValueError("consistent-read entry fields are invalid")
            revision = entry["revision"]
            raw = entry["bytes"]
            if not isinstance(revision, str) or _REVISION.fullmatch(revision) is None:
                raise ValueError("consistent-read revision is invalid")
            if raw is not None and not isinstance(raw, bytes):
                raise ValueError("consistent-read bytes are invalid")
        staged_raw = snapshot[artifact_uri]["bytes"]
        evidence_raw = snapshot[evidence_uri]["bytes"]
        if staged_raw is None or evidence_raw is None:
            raise ValueError("promotion input is missing")
        if any(snapshot[uri]["bytes"] is None for uri in (MANIFEST, TOPICS, RELATIONS)):
            raise ValueError("canonical source registry is missing")
        staged_text = staged_raw.decode("utf-8")
        worker = atlas_cli.decode(evidence_raw)
        docs = {
            "manifest": snapshot[MANIFEST]["bytes"].decode("utf-8"),
            "topics": snapshot[TOPICS]["bytes"].decode("utf-8"),
            "relations": snapshot[RELATIONS]["bytes"].decode("utf-8"),
        }
        _validate(docs)
        canonical_url, source_id, current_target = _promotion_identity(
            docs["manifest"],
            staged_text,
            worker,
        )
        if any(
            snapshot[uri]["revision"] != revision
            for uri, revision in preliminary_revisions.items()
        ):
            raise ValueError("promotion input changed during preparation")
        if current_target != target_uri:
            raise ValueError("promotion target changed during preparation")
        rows, _ = atlas_state.validated_manifest_rows(docs["manifest"])
        current = next(
            (row for row in rows if row["Source ID"] == source_id),
            None,
        )
        target_raw = snapshot[target_uri]["bytes"]
        if current is None and target_raw is not None:
            raise ValueError("new source target already exists")
        living_artifact_text = (
            None if target_raw is None else target_raw.decode("utf-8")
        )
    except (
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        atlas_cli.JsonInputError,
    ) as exc:
        return {
            "state": "rejected",
            "findings": [
                {
                    "code": "SOURCE_PROMOTION_STALE",
                    "path": "snapshot",
                    "detail": str(exc),
                }
            ],
        }

    prepared = atlas_source.prepare_promotion(
        docs,
        staged_artifact_text=staged_text,
        worker=worker,
        living_artifact_text=living_artifact_text,
    )
    if prepared["state"] != "prepared":
        return prepared
    targets: list[dict[str, str]] = []
    artifact_text = prepared["artifact_text"]
    if living_artifact_text is None or artifact_text != living_artifact_text:
        targets.append(
            {
                "path": target_uri,
                "expected_revision": snapshot[target_uri]["revision"],
                "text": artifact_text,
            }
        )
    for name, uri in (
        ("relations", RELATIONS),
        ("topics", TOPICS),
        ("manifest", MANIFEST),
    ):
        replacement = prepared["documents"].get(name)
        if replacement is not None and replacement != docs[name]:
            targets.append(
                {
                    "path": uri,
                    "expected_revision": snapshot[uri]["revision"],
                    "text": replacement,
                }
            )
    if not targets:
        return {
            "state": "terminal",
            "outcome": "unchanged",
            "reason": "promotion has no changed targets",
        }
    promotion = {
        "artifact_uri": artifact_uri,
        "artifact_revision": snapshot[artifact_uri]["revision"],
        "evidence_uri": evidence_uri,
        "evidence_revision": snapshot[evidence_uri]["revision"],
    }
    event_record = atlas_source.build_event_record(
        event_type="source-upsert",
        source_id=source_id,
        event=prepared["event"],
        route_decision=None,
        promotion=promotion,
    )
    return {
        "state": "prepared",
        "outcome": prepared["outcome"],
        "route_required": prepared["route_required"],
        "identity": {
            "canonical_url": canonical_url,
            "source_id": source_id,
        },
        "promotion": promotion,
        "transaction": {"event_record": event_record, "targets": targets},
    }


def _snapshot(connector: Any, args: Any) -> dict[str, Any]:
    _args(args, set(), "source.snapshot_active")
    _mutations(connector)
    with connector.mutation_session():
        docs = _documents(connector)
        _validate(docs)
        selected: list[dict[str, Any]] = []
        for row, raw in _rows(docs["manifest"], atlas_state.MANIFEST_HEADER, MANIFEST):
            if row["Status"] != "active":
                continue
            artifact_uri = _logical(row["Artifact"])
            try:
                artifact = atlas_source.parse_artifact(
                    connector.read_text(artifact_uri)
                ).values
                actual = {
                    "Source ID": atlas_source.scalar(artifact, "source_id"),
                    "Source seq": atlas_source.scalar(artifact, "source_seq"),
                    "Canonical URL": atlas_source.scalar(artifact, "canonical_url"),
                    "Content hash": atlas_source.scalar(artifact, "content_hash"),
                    "Route status": atlas_source.scalar(artifact, "routing_status"),
                }
            except (FileNotFoundError, ValueError) as exc:
                raise Failure(
                    "SNAPSHOT_ARTIFACT_INVALID", artifact_uri, str(exc)
                ) from exc
            if actual != {key: row[key] for key in actual}:
                raise Failure(
                    "SNAPSHOT_ARTIFACT_IDENTITY_MISMATCH",
                    artifact_uri,
                    "manifest and artifact identity disagree",
                )
            selected.append(
                {
                    "source_seq": int(row["Source seq"]),
                    "source_id": row["Source ID"],
                    "canonical_url": row["Canonical URL"],
                    "artifact_uri": artifact_uri,
                    "content_hash": row["Content hash"],
                    "route_status": row["Route status"],
                    "manifest_row_sha256": _hash(raw.encode("utf-8")),
                    "artifact_revision": connector.revision(artifact_uri),
                }
            )
        selected.sort(key=lambda item: (item["source_seq"], item["source_id"]))
        ids = sorted(item["source_id"] for item in selected)
        return {
            "manifest_revision": connector.revision(MANIFEST),
            "active_count": len(selected),
            "source_id_set_sha256": _hash(("\n".join(ids) + "\n").encode("utf-8")),
            "rows": selected,
        }


def _binding_identity(connector: Any) -> dict[str, str]:
    try:
        value = connector.binding_identity()
    except (ConnectorIOError, ConnectorDurabilityError):
        raise
    except (AttributeError, TypeError, ValueError, OSError) as exc:
        raise Failure(
            "BINDING_INVALID",
            "connector",
            "binding identity is invalid",
        ) from exc
    if not isinstance(value, Mapping) or set(value) != {
        "instance_id",
        "binding_revision",
    }:
        raise Failure("BINDING_INVALID", "connector", "binding identity is invalid")
    instance_id = value["instance_id"]
    binding_revision = value["binding_revision"]
    if (
        not isinstance(instance_id, str)
        or not instance_id
        or not isinstance(binding_revision, str)
        or _REVISION.fullmatch(binding_revision) is None
        or binding_revision == "missing"
    ):
        raise Failure("BINDING_INVALID", "connector", "binding identity is invalid")
    return {
        "instance_id": instance_id,
        "binding_revision": binding_revision,
    }


def _canonical_no_lf(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _migration_snapshot_entry(entry: Any, uri: str) -> tuple[str, str]:
    if not isinstance(entry, Mapping) or set(entry) != {"bytes", "revision"}:
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            uri,
            "consistent-read entry is invalid",
        )
    raw = entry["bytes"]
    revision = entry["revision"]
    if (
        not isinstance(raw, bytes)
        or not isinstance(revision, str)
        or _REVISION.fullmatch(revision) is None
        or revision == "missing"
        or revision != "sha256:" + _hash(raw)
    ):
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            uri,
            "consistent-read entry is missing or revision-invalid",
        )
    try:
        return revision, raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            uri,
            "snapshot text is not valid UTF-8",
        ) from exc


def _migration_snapshot(
    connector: Any,
) -> tuple[
    dict[str, str],
    dict[str, Any],
    atlas_state.TaxonomyBackfillCandidateResult,
]:
    try:
        preliminary_manifest = connector.read_text(MANIFEST)
    except (OSError, ValueError, UnicodeError) as exc:
        raise Failure("MIGRATION_SNAPSHOT_INVALID", MANIFEST, str(exc)) from exc
    preliminary_rows, preliminary_findings = atlas_state.validated_manifest_rows(
        preliminary_manifest
    )
    _reject(preliminary_findings)
    preliminary_artifacts = tuple(
        row["Artifact"]
        for row in sorted(
            (row for row in preliminary_rows if row["Status"] == "active"),
            key=lambda row: int(row["Source seq"]),
        )
    )
    registry_uris = {
        "manifest": MANIFEST,
        "topics": TOPICS,
        "relations": RELATIONS,
        "vocab": VOCAB,
    }
    artifact_uris = tuple(_logical(path) for path in preliminary_artifacts)
    paths = [*registry_uris.values(), *artifact_uris]
    try:
        snapshot = connector.consistent_read(paths)
    except (OSError, ValueError, TypeError) as exc:
        raise Failure("MIGRATION_SNAPSHOT_INVALID", "snapshot", str(exc)) from exc
    if not isinstance(snapshot, Mapping) or set(snapshot) != set(paths):
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            "snapshot",
            "consistent-read path set is invalid",
        )
    decoded = {uri: _migration_snapshot_entry(snapshot[uri], uri) for uri in paths}
    documents = {name: decoded[uri][1] for name, uri in registry_uris.items()}
    locked_rows, locked_findings = atlas_state.validated_manifest_rows(
        documents["manifest"]
    )
    _reject(locked_findings)
    active_rows = sorted(
        (row for row in locked_rows if row["Status"] == "active"),
        key=lambda row: int(row["Source seq"]),
    )
    locked_artifacts = tuple(row["Artifact"] for row in active_rows)
    if locked_artifacts != preliminary_artifacts:
        raise Failure(
            "REVISION_STALE",
            MANIFEST,
            "active source set changed during migration snapshot",
        )
    projections: dict[str, Mapping[str, Any]] = {}
    artifact_revisions: list[dict[str, str]] = []
    for row in active_rows:
        relative = row["Artifact"]
        uri = _logical(relative)
        revision, text = decoded[uri]
        try:
            projections[relative] = atlas_source.candidate_artifact_projection(
                text,
                revision,
            )
        except ValueError as exc:
            raise Failure(
                "TAXONOMY_BACKFILL_SOURCE_INVALID",
                uri,
                str(exc),
            ) from exc
        artifact_revisions.append({"path": uri, "revision": revision})
    inventory: dict[str, Any] = {
        "manifest_revision": decoded[MANIFEST][0],
        "topics_revision": decoded[TOPICS][0],
        "relations_revision": decoded[RELATIONS][0],
        "vocab_revision": decoded[VOCAB][0],
        "artifact_revisions": artifact_revisions,
    }
    result = atlas_state.prepare_taxonomy_backfill_candidate(
        documents["manifest"],
        documents["topics"],
        documents["relations"],
        documents["vocab"],
        projections,
    )
    return documents, inventory, result


def _migration_candidate_hash(
    binding: Mapping[str, str],
    inventory: Mapping[str, Any],
    output_revision: str,
    changes: Sequence[Mapping[str, Any]],
) -> str:
    material = {
        "version": 1,
        "binding": dict(binding),
        "inventory": dict(inventory),
        "path": VOCAB,
        "output_revision": output_revision,
        "changes": [dict(change) for change in changes],
    }
    return "sha256:" + _hash(_canonical_no_lf(material))


def _migration_prepare_taxonomy_backfill(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    _args(args, set(), "migration.prepare_taxonomy_backfill")
    binding = _binding_identity(connector)
    _, inventory, result = _migration_snapshot(connector)
    if result.findings:
        _reject(result.findings)
    if _binding_identity(connector) != binding:
        raise Failure(
            "REVISION_STALE",
            "connector",
            "connector binding changed during migration prepare",
        )
    if result.state == "no-op":
        return {
            "state": "no-op",
            "binding": binding,
            "inventory": inventory,
            "candidate": None,
        }
    if (
        result.state != "candidate"
        or result.text is None
        or result.preimage_text is None
        or result.preimage_revision is None
        or result.output_revision is None
    ):
        raise Failure(
            "TAXONOMY_BACKFILL_INVALID",
            VOCAB,
            "candidate result is incomplete",
        )
    changes = [dict(change) for change in result.changes]
    candidate_sha256 = _migration_candidate_hash(
        binding,
        inventory,
        result.output_revision,
        changes,
    )
    return {
        "state": "candidate",
        "binding": binding,
        "inventory": inventory,
        "candidate": {
            "candidate_sha256": candidate_sha256,
            "path": VOCAB,
            "preimage_text": result.preimage_text,
            "text": result.text,
            "preimage_revision": result.preimage_revision,
            "output_revision": result.output_revision,
            "changes": changes,
            "approval_literal": (
                f"APPLY ATLAS TAXONOMY BACKFILL "
                f"{binding['instance_id']} {candidate_sha256}"
            ),
        },
    }


def _migration_current_vocab(
    connector: Any,
) -> tuple[str, bytes | None]:
    try:
        value = connector.read_bytes(VOCAB)
    except FileNotFoundError:
        return "missing", None
    except (OSError, ValueError):
        return "unknown", None
    return "sha256:" + _hash(value), value


def _migration_result(
    *,
    state: str,
    binding: Mapping[str, str],
    candidate_sha256: str,
    inventory: Mapping[str, Any],
    forward: Mapping[str, Any],
    post_validation: Mapping[str, Any],
    rollback: Mapping[str, Any] | None,
    findings: Sequence[dict[str, str]],
) -> dict[str, Any]:
    return {
        "version": 1,
        "state": state,
        "binding": dict(binding),
        "candidate_sha256": candidate_sha256,
        "inventory": dict(inventory),
        "forward": dict(forward),
        "post_validation": dict(post_validation),
        "rollback": None if rollback is None else dict(rollback),
        "findings": _findings(findings),
    }


def _taxonomy_backfill_post_validation(
    connector: Any,
    inventory: Mapping[str, Any],
    candidate: atlas_state.TaxonomyBackfillCandidateResult,
) -> tuple[Mapping[str, Any], Sequence[dict[str, str]]]:
    post_documents, post_inventory, replay = _migration_snapshot(connector)
    post_findings: list[dict[str, str]] = []
    for key, path in (
        ("manifest_revision", MANIFEST),
        ("topics_revision", TOPICS),
        ("relations_revision", RELATIONS),
    ):
        if post_inventory[key] != inventory[key]:
            post_findings.append(
                _finding(
                    "MIGRATION_SIBLING_DRIFT",
                    path,
                    f"{path} changed during migration",
                )
            )
    if post_inventory["artifact_revisions"] != inventory["artifact_revisions"]:
        post_findings.append(
            _finding(
                "MIGRATION_SIBLING_DRIFT",
                "artifacts",
                "active source artifact inventory changed during migration",
            )
        )
    if (
        post_inventory["vocab_revision"] != candidate.output_revision
        or post_documents["vocab"] != candidate.text
    ):
        post_findings.append(
            _finding(
                "MIGRATION_OUTPUT_MISMATCH",
                VOCAB,
                "VOCAB.md does not match the candidate output",
            )
        )
    if replay.findings:
        post_findings.extend(_owner_findings(replay.findings))
    if replay.state != "no-op":
        post_findings.append(
            _finding(
                "MIGRATION_POST_VALIDATION_FAILED",
                VOCAB,
                "taxonomy reducer replay did not return no-op",
            )
        )
    return post_inventory, post_findings


def _one_file_migration_apply(
    connector: Any,
    *,
    binding: Mapping[str, str],
    candidate_sha256: str,
    inventory: Mapping[str, Any],
    candidate: atlas_state.TaxonomyBackfillCandidateResult,
    post_validator: Callable[
        [], tuple[Mapping[str, Any], Sequence[dict[str, str]]]
    ],
    single_session: bool,
    pre_effect_validator: Callable[[], None] | None = None,
) -> dict[str, Any]:
    if (
        candidate.text is None
        or candidate.preimage_text is None
        or candidate.preimage_revision is None
        or candidate.output_revision is None
    ):
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "args.candidate_sha256",
            "candidate is incomplete",
        )
    output_bytes = candidate.text.encode("utf-8")
    preimage_bytes = candidate.preimage_text.encode("utf-8")

    def run(*, session_open: bool) -> dict[str, Any]:
        forward: dict[str, Any] = {
            "attempted": True,
            "status": "error",
            "revision": "missing",
            "acknowledged_revision": "missing",
            "classification": "unknown",
        }
        findings: list[dict[str, str]] = []
        forward_acknowledged = False
        if session_open and pre_effect_validator is not None:
            pre_effect_validator()
        try:
            if session_open:
                raw_forward = connector.conditional_replace(
                    VOCAB,
                    candidate.preimage_revision,
                    output_bytes,
                )
            else:
                with connector.mutation_session():
                    if pre_effect_validator is not None:
                        pre_effect_validator()
                    raw_forward = connector.conditional_replace(
                        VOCAB,
                        candidate.preimage_revision,
                        output_bytes,
                    )
            if not isinstance(raw_forward, Mapping):
                raise ValueError("forward acknowledgement is invalid")
            required = {"status", "revision", "acknowledged_revision"}
            for key in required:
                if isinstance(raw_forward.get(key), str):
                    forward[key] = raw_forward[key]
            forward_acknowledged = (
                set(raw_forward) == required
                and raw_forward["status"] == "replaced"
                and raw_forward["revision"] == candidate.output_revision
                and raw_forward["acknowledged_revision"] == candidate.output_revision
            )
            if not forward_acknowledged:
                findings.append(
                    _finding(
                        "MIGRATION_FORWARD_ACK_INVALID",
                        VOCAB,
                        "forward acknowledgement does not prove the candidate output",
                    )
                )
        except Failure:
            raise
        except ConnectorConflictError as exc:
            findings.append(
                _finding(
                    "MIGRATION_FORWARD_CONFLICT",
                    VOCAB,
                    str(exc),
                )
            )
        except (OSError, ValueError, TypeError, KeyError) as exc:
            findings.append(_finding("MIGRATION_FORWARD_FAILED", VOCAB, str(exc)))

        post_validation: dict[str, Any] = {
            "attempted": True,
            "inventory": None,
            "ok": False,
            "findings": [],
        }
        post_io_error: ConnectorIOError | ConnectorDurabilityError | None = None
        try:
            post_inventory, post_findings = post_validator()
            post_validation["inventory"] = dict(post_inventory)
            post_validation["findings"] = _findings(post_findings)
            post_validation["ok"] = not post_validation["findings"]
            findings.extend(post_validation["findings"])
        except (ConnectorIOError, ConnectorDurabilityError) as exc:
            if single_session:
                post_io_error = exc
                detail = "connector I/O failed during post-validation"
            else:
                detail = str(exc)
            normalized = [
                _finding("MIGRATION_POST_VALIDATION_FAILED", VOCAB, detail)
            ]
            post_validation["findings"] = normalized
            findings.extend(normalized)
        except Failure as exc:
            normalized = exc.findings or [
                _finding("MIGRATION_POST_VALIDATION_FAILED", exc.path, exc.detail)
            ]
            post_validation["findings"] = _findings(normalized)
            findings.extend(post_validation["findings"])
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            normalized = [
                _finding("MIGRATION_POST_VALIDATION_FAILED", VOCAB, str(exc))
            ]
            post_validation["findings"] = normalized
            findings.extend(normalized)

        current_revision, current_bytes = _migration_current_vocab(connector)
        if (
            current_revision == candidate.output_revision
            and current_bytes == output_bytes
        ):
            classification = "output"
        elif (
            current_revision == candidate.preimage_revision
            and current_bytes == preimage_bytes
        ):
            classification = "input"
        else:
            classification = "other"
        forward["classification"] = classification

        if (
            forward_acknowledged
            and classification == "output"
            and post_validation["ok"]
        ):
            return _migration_result(
                state="applied",
                binding=binding,
                candidate_sha256=candidate_sha256,
                inventory=inventory,
                forward=forward,
                post_validation=post_validation,
                rollback=None,
                findings=findings,
            )

        rollback: dict[str, Any] | None = None
        if classification == "output":
            rollback = {
                "attempted": True,
                "status": "error",
                "revision": "missing",
                "acknowledged_revision": "missing",
                "preimage_confirmed": False,
            }
            try:
                if session_open:
                    raw_rollback = connector.conditional_replace(
                        VOCAB,
                        candidate.output_revision,
                        preimage_bytes,
                    )
                else:
                    with connector.mutation_session():
                        raw_rollback = connector.conditional_replace(
                            VOCAB,
                            candidate.output_revision,
                            preimage_bytes,
                        )
                if not isinstance(raw_rollback, Mapping):
                    raise ValueError("rollback acknowledgement is invalid")
                required = {"status", "revision", "acknowledged_revision"}
                for key in required:
                    if isinstance(raw_rollback.get(key), str):
                        rollback[key] = raw_rollback[key]
                rollback["preimage_confirmed"] = (
                    set(raw_rollback) == required
                    and raw_rollback["status"] == "replaced"
                    and raw_rollback["revision"] == candidate.preimage_revision
                    and raw_rollback["acknowledged_revision"]
                    == candidate.preimage_revision
                    and connector.read_bytes(VOCAB) == preimage_bytes
                )
            except (
                ConnectorConflictError,
                OSError,
                ValueError,
                TypeError,
                KeyError,
            ) as exc:
                if post_io_error is not None:
                    detail = "rollback failed after post-validation I/O failure"
                else:
                    detail = str(exc)
                findings.append(
                    _finding("MIGRATION_ROLLBACK_FAILED", VOCAB, detail)
                )
            if rollback["preimage_confirmed"]:
                state = "rolled-back"
            else:
                if not any(
                    item["code"] == "MIGRATION_ROLLBACK_FAILED"
                    for item in findings
                ):
                    findings.append(
                        _finding(
                            "MIGRATION_ROLLBACK_ACK_INVALID",
                            VOCAB,
                            (
                                "rollback acknowledgement and reread do not "
                                "prove the preimage"
                            ),
                        )
                    )
                state = "manual-conflict"
        elif classification == "input":
            state = "rolled-back"
        else:
            state = "manual-conflict"
            findings.append(
                _finding(
                    "MIGRATION_EFFECT_UNKNOWN",
                    VOCAB,
                    "current VOCAB bytes are neither preimage nor candidate",
                )
            )
        if post_io_error is not None and state == "rolled-back":
            raise post_io_error
        return _migration_result(
            state=state,
            binding=binding,
            candidate_sha256=candidate_sha256,
            inventory=inventory,
            forward=forward,
            post_validation=post_validation,
            rollback=rollback,
            findings=findings,
        )

    if single_session:
        with connector.mutation_session():
            return run(session_open=True)
    return run(session_open=False)


def _migration_apply_taxonomy_backfill(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    value = _args(
        args,
        {"instance_id", "candidate_sha256", "approval"},
        "migration.apply_taxonomy_backfill",
    )
    instance_id = _text(value["instance_id"], "args.instance_id")
    candidate_sha256 = _text(value["candidate_sha256"], "args.candidate_sha256")
    approval = _text(value["approval"], "args.approval")
    if (
        not instance_id
        or _REVISION.fullmatch(candidate_sha256) is None
        or candidate_sha256 == "missing"
    ):
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args",
            "instance and candidate identity are invalid",
        )
    expected_approval = (
        f"APPLY ATLAS TAXONOMY BACKFILL {instance_id} {candidate_sha256}"
    )
    if approval != expected_approval:
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args.approval",
            "approval literal does not bind instance and candidate",
        )

    binding = _binding_identity(connector)
    _, inventory, result = _migration_snapshot(connector)
    if result.findings:
        _reject(result.findings)
    if (
        instance_id != binding["instance_id"]
        or result.state != "candidate"
        or result.text is None
        or result.preimage_text is None
        or result.preimage_revision is None
        or result.output_revision is None
    ):
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "args.candidate_sha256",
            "candidate no longer exists for this binding",
        )
    changes = [dict(change) for change in result.changes]
    current_hash = _migration_candidate_hash(
        binding,
        inventory,
        result.output_revision,
        changes,
    )
    if current_hash != candidate_sha256:
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "args.candidate_sha256",
            "candidate does not match current inventory",
        )
    if _binding_identity(connector) != binding:
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "connector",
            "connector binding changed before effect",
        )
    _mutations(connector)
    return _one_file_migration_apply(
        connector,
        binding=binding,
        candidate_sha256=candidate_sha256,
        inventory=inventory,
        candidate=result,
        post_validator=lambda: _taxonomy_backfill_post_validation(
            connector, inventory, result
        ),
        single_session=False,
    )


def _vocabulary_domain_snapshot(
    connector: Any,
    domain_id: str,
) -> tuple[dict[str, Any], atlas_state.TaxonomyBackfillCandidateResult]:
    try:
        snapshot = connector.consistent_read([VOCAB])
    except (ConnectorIOError, ConnectorDurabilityError):
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            VOCAB,
            "consistent read failed",
        ) from exc
    if not isinstance(snapshot, Mapping) or set(snapshot) != {VOCAB}:
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            VOCAB,
            "consistent-read path set is invalid",
        )
    vocab_revision, vocab_text = _migration_snapshot_entry(snapshot[VOCAB], VOCAB)
    return (
        {"vocab_revision": vocab_revision},
        atlas_state.prepare_vocabulary_domain_insertion_candidate(
            vocab_text, domain_id
        ),
    )


def _vocabulary_domain_candidate_hash(
    binding: Mapping[str, str],
    inventory: Mapping[str, Any],
    domain_id: str,
    output_revision: str,
    changes: Sequence[Mapping[str, Any]],
) -> str:
    material = {
        "version": 1,
        "operation": "migration.apply_vocabulary_domain_insertion",
        "migration_id": "vocabulary-domain-insertion-v1",
        "request": {"domain_id": domain_id},
        "binding": dict(binding),
        "inventory": dict(inventory),
        "path": VOCAB,
        "output_revision": output_revision,
        "changes": [dict(change) for change in changes],
    }
    return "sha256:" + _hash(_canonical_no_lf(material))


def _migration_prepare_vocabulary_domain_insertion(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    value = _args(
        args,
        {"domain_id"},
        "migration.prepare_vocabulary_domain_insertion",
    )
    domain_id = _text(value["domain_id"], "args.domain_id")
    binding = _binding_identity(connector)
    inventory, result = _vocabulary_domain_snapshot(connector, domain_id)
    if result.findings:
        _reject(result.findings)
    if _binding_identity(connector) != binding:
        raise Failure(
            "REVISION_STALE",
            "connector",
            "connector binding changed during migration prepare",
        )
    if result.state == "no-op":
        return {
            "state": "no-op",
            "binding": binding,
            "inventory": inventory,
            "candidate": None,
        }
    if (
        result.state != "candidate"
        or result.text is None
        or result.preimage_text is None
        or result.preimage_revision is None
        or result.output_revision is None
    ):
        raise Failure(
            "VOCABULARY_DOMAIN_INSERTION_POST_INVALID",
            VOCAB,
            "candidate result is incomplete",
        )
    changes = [dict(change) for change in result.changes]
    candidate_sha256 = _vocabulary_domain_candidate_hash(
        binding,
        inventory,
        domain_id,
        result.output_revision,
        changes,
    )
    return {
        "state": "candidate",
        "binding": binding,
        "inventory": inventory,
        "candidate": {
            "candidate_sha256": candidate_sha256,
            "path": VOCAB,
            "preimage_text": result.preimage_text,
            "text": result.text,
            "preimage_revision": result.preimage_revision,
            "output_revision": result.output_revision,
            "changes": changes,
            "approval_literal": (
                "APPLY ATLAS VOCABULARY DOMAIN INSERTION V1 "
                f"{binding['instance_id']} {domain_id} {candidate_sha256}"
            ),
        },
    }


def _vocabulary_domain_post_validation(
    connector: Any,
    binding: Mapping[str, str],
    candidate: atlas_state.TaxonomyBackfillCandidateResult,
    domain_id: str,
) -> tuple[Mapping[str, Any], Sequence[dict[str, str]]]:
    raw = connector.read_bytes(VOCAB)
    revision = "sha256:" + _hash(raw)
    text = raw.decode("utf-8")
    post_inventory = {"vocab_revision": revision}
    post_findings: list[dict[str, str]] = []
    if _binding_identity(connector) != binding:
        post_findings.append(
            _finding(
                "MIGRATION_BINDING_DRIFT",
                "connector",
                "connector binding changed during migration",
            )
        )
    if revision != candidate.output_revision or text != candidate.text:
        post_findings.append(
            _finding(
                "MIGRATION_OUTPUT_MISMATCH",
                VOCAB,
                "VOCAB.md does not match the candidate output",
            )
        )
    post_findings.extend(
        _owner_findings(atlas_state.validate_vocab(text))
    )
    replay = atlas_state.prepare_vocabulary_domain_insertion_candidate(
        text, domain_id
    )
    if replay.findings:
        post_findings.extend(_owner_findings(replay.findings))
    if replay.state != "no-op":
        post_findings.append(
            _finding(
                "MIGRATION_POST_VALIDATION_FAILED",
                VOCAB,
                "vocabulary-domain insertion replay did not return no-op",
            )
        )
    return post_inventory, post_findings


def _migration_apply_vocabulary_domain_insertion(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    value = _args(
        args,
        {"domain_id", "instance_id", "candidate_sha256", "approval"},
        "migration.apply_vocabulary_domain_insertion",
    )
    domain_id = _text(value["domain_id"], "args.domain_id")
    instance_id = _text(value["instance_id"], "args.instance_id")
    candidate_sha256 = _text(value["candidate_sha256"], "args.candidate_sha256")
    approval = _text(value["approval"], "args.approval")
    if (
        atlas_state.VOCAB_ID_RE.fullmatch(domain_id) is None
        or not instance_id
        or _REVISION.fullmatch(candidate_sha256) is None
        or candidate_sha256 == "missing"
    ):
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args",
            "domain, instance, and candidate identity are invalid",
        )
    expected_approval = (
        "APPLY ATLAS VOCABULARY DOMAIN INSERTION V1 "
        f"{instance_id} {domain_id} {candidate_sha256}"
    )
    if approval != expected_approval:
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args.approval",
            "approval literal does not bind domain, instance, and candidate",
        )

    binding = _binding_identity(connector)
    try:
        inventory, result = _vocabulary_domain_snapshot(connector, domain_id)
    except Failure as exc:
        if exc.code == "MIGRATION_SNAPSHOT_INVALID":
            raise Failure(
                "MIGRATION_CANDIDATE_STALE",
                "args.candidate_sha256",
                "vocabulary snapshot no longer matches the candidate",
            ) from exc
        raise
    if (
        result.findings
        or instance_id != binding["instance_id"]
        or result.state != "candidate"
        or result.text is None
        or result.preimage_text is None
        or result.preimage_revision is None
        or result.output_revision is None
    ):
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "args.candidate_sha256",
            "candidate no longer exists for this domain and binding",
        )
    changes = [dict(change) for change in result.changes]
    current_hash = _vocabulary_domain_candidate_hash(
        binding,
        inventory,
        domain_id,
        result.output_revision,
        changes,
    )
    if current_hash != candidate_sha256:
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "args.candidate_sha256",
            "candidate does not match current vocabulary inventory",
        )
    def require_current_binding() -> None:
        if _binding_identity(connector) != binding:
            raise Failure(
                "MIGRATION_CANDIDATE_STALE",
                "args.candidate_sha256",
                "connector binding changed before effect",
            )

    require_current_binding()
    _mutations(connector)
    return _one_file_migration_apply(
        connector,
        binding=binding,
        candidate_sha256=candidate_sha256,
        inventory=inventory,
        candidate=result,
        post_validator=lambda: _vocabulary_domain_post_validation(
            connector, binding, result, domain_id
        ),
        single_session=True,
        pre_effect_validator=require_current_binding,
    )


def _vocabulary_subdomain_snapshot(
    connector: Any,
    subdomain_id: str,
    parent_domain_id: str,
) -> tuple[dict[str, Any], atlas_state.TaxonomyBackfillCandidateResult]:
    try:
        snapshot = connector.consistent_read([VOCAB])
    except (ConnectorIOError, ConnectorDurabilityError):
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            VOCAB,
            "consistent read failed",
        ) from exc
    if not isinstance(snapshot, Mapping) or set(snapshot) != {VOCAB}:
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            VOCAB,
            "consistent-read path set is invalid",
        )
    vocab_revision, vocab_text = _migration_snapshot_entry(snapshot[VOCAB], VOCAB)
    return (
        {"vocab_revision": vocab_revision},
        atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
            vocab_text,
            subdomain_id,
            parent_domain_id,
        ),
    )


def _vocabulary_subdomain_candidate_hash(
    binding: Mapping[str, str],
    inventory: Mapping[str, Any],
    subdomain_id: str,
    parent_domain_id: str,
    output_revision: str,
    changes: Sequence[Mapping[str, Any]],
) -> str:
    material = {
        "version": 1,
        "operation": "migration.apply_vocabulary_subdomain_insertion",
        "migration_id": "vocabulary-subdomain-insertion-v1",
        "request": {
            "subdomain_id": subdomain_id,
            "parent_domain_id": parent_domain_id,
        },
        "binding": dict(binding),
        "inventory": dict(inventory),
        "path": VOCAB,
        "output_revision": output_revision,
        "changes": [dict(change) for change in changes],
    }
    return "sha256:" + _hash(_canonical_no_lf(material))


def _migration_prepare_vocabulary_subdomain_insertion(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    value = _args(
        args,
        {"subdomain_id", "parent_domain_id"},
        "migration.prepare_vocabulary_subdomain_insertion",
    )
    subdomain_id = _text(value["subdomain_id"], "args.subdomain_id")
    parent_domain_id = _text(
        value["parent_domain_id"], "args.parent_domain_id"
    )
    binding = _binding_identity(connector)
    inventory, result = _vocabulary_subdomain_snapshot(
        connector,
        subdomain_id,
        parent_domain_id,
    )
    if result.findings:
        _reject(result.findings)
    if _binding_identity(connector) != binding:
        raise Failure(
            "REVISION_STALE",
            "connector",
            "connector binding changed during migration prepare",
        )
    if result.state == "no-op":
        return {
            "state": "no-op",
            "binding": binding,
            "inventory": inventory,
            "candidate": None,
        }
    if (
        result.state != "candidate"
        or result.text is None
        or result.preimage_text is None
        or result.preimage_revision is None
        or result.output_revision is None
        or len(result.changes) != 1
    ):
        raise Failure(
            "VOCABULARY_SUBDOMAIN_INSERTION_POST_INVALID",
            VOCAB,
            "candidate result is incomplete",
        )
    changes = [dict(change) for change in result.changes]
    candidate_sha256 = _vocabulary_subdomain_candidate_hash(
        binding,
        inventory,
        subdomain_id,
        parent_domain_id,
        result.output_revision,
        changes,
    )
    return {
        "state": "candidate",
        "binding": binding,
        "inventory": inventory,
        "candidate": {
            "candidate_sha256": candidate_sha256,
            "path": VOCAB,
            "preimage_text": result.preimage_text,
            "text": result.text,
            "preimage_revision": result.preimage_revision,
            "output_revision": result.output_revision,
            "changes": changes,
            "approval_literal": (
                "APPLY ATLAS VOCABULARY SUBDOMAIN INSERTION V1 "
                f"{binding['instance_id']} {subdomain_id} "
                f"{parent_domain_id} {candidate_sha256}"
            ),
        },
    }


def _vocabulary_subdomain_post_validation(
    connector: Any,
    binding: Mapping[str, str],
    candidate: atlas_state.TaxonomyBackfillCandidateResult,
    subdomain_id: str,
    parent_domain_id: str,
) -> tuple[Mapping[str, Any], Sequence[dict[str, str]]]:
    raw = connector.read_bytes(VOCAB)
    revision = "sha256:" + _hash(raw)
    text = raw.decode("utf-8")
    post_inventory = {"vocab_revision": revision}
    post_findings: list[dict[str, str]] = []
    if _binding_identity(connector) != binding:
        post_findings.append(
            _finding(
                "MIGRATION_BINDING_DRIFT",
                "connector",
                "connector binding changed during migration",
            )
        )
    if revision != candidate.output_revision or text != candidate.text:
        post_findings.append(
            _finding(
                "MIGRATION_OUTPUT_MISMATCH",
                VOCAB,
                "VOCAB.md does not match the candidate output",
            )
        )
    post_findings.extend(
        _owner_findings(atlas_state.validate_vocab(text))
    )
    replay = atlas_state.prepare_vocabulary_subdomain_insertion_candidate(
        text,
        subdomain_id,
        parent_domain_id,
    )
    if replay.findings:
        post_findings.extend(_owner_findings(replay.findings))
    if replay.state != "no-op":
        post_findings.append(
            _finding(
                "MIGRATION_POST_VALIDATION_FAILED",
                VOCAB,
                "vocabulary-subdomain insertion replay did not return no-op",
            )
        )
    return post_inventory, post_findings


def _migration_apply_vocabulary_subdomain_insertion(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    value = _args(
        args,
        {
            "subdomain_id",
            "parent_domain_id",
            "instance_id",
            "candidate_sha256",
            "approval",
        },
        "migration.apply_vocabulary_subdomain_insertion",
    )
    subdomain_id = _text(value["subdomain_id"], "args.subdomain_id")
    parent_domain_id = _text(
        value["parent_domain_id"], "args.parent_domain_id"
    )
    instance_id = _text(value["instance_id"], "args.instance_id")
    candidate_sha256 = _text(
        value["candidate_sha256"], "args.candidate_sha256"
    )
    approval = _text(value["approval"], "args.approval")
    if (
        atlas_state.VOCAB_ID_RE.fullmatch(subdomain_id) is None
        or atlas_state.VOCAB_ID_RE.fullmatch(parent_domain_id) is None
        or not instance_id
        or _REVISION.fullmatch(candidate_sha256) is None
        or candidate_sha256 == "missing"
    ):
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args",
            "subdomain, parent, instance, and candidate identity are invalid",
        )
    expected_approval = (
        "APPLY ATLAS VOCABULARY SUBDOMAIN INSERTION V1 "
        f"{instance_id} {subdomain_id} {parent_domain_id} {candidate_sha256}"
    )
    if approval != expected_approval:
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args.approval",
            "approval literal does not bind subdomain, parent, instance, and candidate",
        )

    binding = _binding_identity(connector)
    try:
        inventory, result = _vocabulary_subdomain_snapshot(
            connector,
            subdomain_id,
            parent_domain_id,
        )
    except Failure as exc:
        if exc.code == "MIGRATION_SNAPSHOT_INVALID":
            raise Failure(
                "MIGRATION_CANDIDATE_STALE",
                "args.candidate_sha256",
                "vocabulary snapshot no longer matches the candidate",
            ) from exc
        raise
    if (
        result.findings
        or instance_id != binding["instance_id"]
        or result.state != "candidate"
        or result.text is None
        or result.preimage_text is None
        or result.preimage_revision is None
        or result.output_revision is None
        or len(result.changes) != 1
    ):
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "args.candidate_sha256",
            "candidate no longer exists for this subdomain, parent, and binding",
        )
    changes = [dict(change) for change in result.changes]
    current_hash = _vocabulary_subdomain_candidate_hash(
        binding,
        inventory,
        subdomain_id,
        parent_domain_id,
        result.output_revision,
        changes,
    )
    if current_hash != candidate_sha256:
        raise Failure(
            "MIGRATION_CANDIDATE_STALE",
            "args.candidate_sha256",
            "candidate does not match current vocabulary inventory",
        )

    def require_current_binding() -> None:
        if _binding_identity(connector) != binding:
            raise Failure(
                "MIGRATION_CANDIDATE_STALE",
                "args.candidate_sha256",
                "connector binding changed before effect",
            )

    require_current_binding()
    _mutations(connector)
    return _one_file_migration_apply(
        connector,
        binding=binding,
        candidate_sha256=candidate_sha256,
        inventory=inventory,
        candidate=result,
        post_validator=lambda: _vocabulary_subdomain_post_validation(
            connector,
            binding,
            result,
            subdomain_id,
            parent_domain_id,
        ),
        single_session=True,
        pre_effect_validator=require_current_binding,
    )


_SOURCE_TAXONOMY_MIGRATION_ID = "source-taxonomy-remediation-v1"
_SOURCE_TAXONOMY_OWNER_ID = "atlas-source-taxonomy-remediation-v1"
_SOURCE_TAXONOMY_TRANSACTION_ROOT = (
    ".atlas/transactions/migrations/source-taxonomy-remediation-v1"
)
_SOURCE_TAXONOMY_TARGET_PATHS = (
    atlas_state.source_taxonomy_remediation_target_paths()
)
_SOURCE_TAXONOMY_TARGET_RANK = {
    path: index for index, path in enumerate(_SOURCE_TAXONOMY_TARGET_PATHS)
}
_SOURCE_TAXONOMY_LEGACY_VALUES = {
    "Unknown",
    "agent-systems/harness",
    "agentic-harness-architecture",
    "ai-coding-workflow",
    "lean-self-improving-agent-harness",
}


def _source_taxonomy_target_allowed(path: str) -> bool:
    return path in _SOURCE_TAXONOMY_TARGET_RANK


def _source_taxonomy_target_rank(path: str) -> tuple[int, str]:
    rank = _SOURCE_TAXONOMY_TARGET_RANK.get(path)
    if rank is None:
        raise atlas_transaction.TransactionError(
            "transaction target is outside the source-taxonomy remediation write set"
        )
    return rank, path


def _source_taxonomy_inventory_artifacts(
    inventory: Any,
) -> tuple[dict[str, Any], ...]:
    if not isinstance(inventory, Mapping) or set(inventory) != {
        "manifest_revision",
        "topics_revision",
        "relations_revision",
        "vocab_revision",
        "active_artifacts",
    }:
        raise ValueError("source-taxonomy remediation inventory fields are invalid")
    for key in (
        "manifest_revision",
        "topics_revision",
        "relations_revision",
        "vocab_revision",
    ):
        value = inventory[key]
        if (
            not isinstance(value, str)
            or _REVISION.fullmatch(value) is None
            or value == "missing"
        ):
            raise ValueError(
                "source-taxonomy remediation inventory revision is invalid"
            )
    active = inventory["active_artifacts"]
    if type(active) is not list:
        raise ValueError(
            "source-taxonomy remediation active inventory is invalid"
        )
    rows: list[dict[str, Any]] = []
    identities: set[str] = set()
    paths: set[str] = set()
    for item in active:
        if not isinstance(item, Mapping) or set(item) != {
            "source_seq",
            "source_id",
            "path",
            "revision",
        }:
            raise ValueError(
                "source-taxonomy remediation artifact inventory is invalid"
            )
        source_seq = item["source_seq"]
        source_id = item["source_id"]
        path = item["path"]
        revision = item["revision"]
        if (
            type(source_seq) is not int
            or source_seq < 0
            or not isinstance(source_id, str)
            or atlas_state.SOURCE_ID_RE.fullmatch(source_id) is None
            or not isinstance(path, str)
            or not path.startswith(ROOT)
            or not isinstance(revision, str)
            or _REVISION.fullmatch(revision) is None
            or revision == "missing"
        ):
            raise ValueError(
                "source-taxonomy remediation artifact inventory value is invalid"
            )
        relative = _relative(path)
        if (
            not relative.startswith(atlas_source.ARTIFACT_PREFIX)
            or not relative.endswith(".md")
            or source_id in identities
            or relative in paths
        ):
            raise ValueError(
                "source-taxonomy remediation artifact inventory identity is invalid"
            )
        identities.add(source_id)
        paths.add(relative)
        rows.append(dict(item))
    if rows != sorted(rows, key=lambda item: (item["source_seq"], item["source_id"])):
        raise ValueError(
            "source-taxonomy remediation artifact inventory is not ordered"
        )
    return tuple(rows)


def _source_taxonomy_snapshot(connector: Any) -> dict[str, Any]:
    try:
        preliminary_manifest = connector.read_text(MANIFEST)
    except (OSError, ValueError, UnicodeError) as exc:
        raise Failure("MIGRATION_SNAPSHOT_INVALID", MANIFEST, str(exc)) from exc
    preliminary_rows, preliminary_findings = atlas_state.validated_manifest_rows(
        preliminary_manifest
    )
    _reject(preliminary_findings)
    preliminary_active = sorted(
        (row for row in preliminary_rows if row["Status"] == "active"),
        key=lambda row: (int(row["Source seq"]), row["Source ID"]),
    )
    preliminary_paths = tuple(row["Artifact"] for row in preliminary_active)
    registry_uris = {
        "manifest": MANIFEST,
        "topics": TOPICS,
        "relations": RELATIONS,
        "vocab": VOCAB,
    }
    artifact_uris = tuple(_logical(path) for path in preliminary_paths)
    paths = [*registry_uris.values(), *artifact_uris]
    try:
        snapshot = connector.consistent_read(paths)
    except (OSError, ValueError, TypeError) as exc:
        raise Failure("MIGRATION_SNAPSHOT_INVALID", "snapshot", str(exc)) from exc
    if not isinstance(snapshot, Mapping) or set(snapshot) != set(paths):
        raise Failure(
            "MIGRATION_SNAPSHOT_INVALID",
            "snapshot",
            "consistent-read path set is invalid",
        )
    decoded = {uri: _migration_snapshot_entry(snapshot[uri], uri) for uri in paths}
    documents = {name: decoded[uri][1] for name, uri in registry_uris.items()}
    locked_rows, locked_findings = atlas_state.validated_manifest_rows(
        documents["manifest"]
    )
    _reject(locked_findings)
    active_rows = sorted(
        (row for row in locked_rows if row["Status"] == "active"),
        key=lambda row: (int(row["Source seq"]), row["Source ID"]),
    )
    locked_paths = tuple(row["Artifact"] for row in active_rows)
    if locked_paths != preliminary_paths:
        raise Failure(
            "REVISION_STALE",
            MANIFEST,
            "active source set changed during remediation snapshot",
        )
    projections: dict[str, Mapping[str, Any]] = {}
    input_bytes: dict[str, bytes] = {}
    active_inventory: list[dict[str, Any]] = []
    for row in active_rows:
        relative = row["Artifact"]
        uri = _logical(relative)
        revision, text = decoded[uri]
        raw = snapshot[uri]["bytes"]
        assert isinstance(raw, bytes)
        try:
            projections[relative] = atlas_source.candidate_artifact_projection(
                text,
                revision,
            )
        except ValueError as exc:
            raise Failure(
                "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                uri,
                str(exc),
            ) from exc
        input_bytes[relative] = raw
        active_inventory.append(
            {
                "source_seq": int(row["Source seq"]),
                "source_id": row["Source ID"],
                "path": uri,
                "revision": revision,
            }
        )
    inventory: dict[str, Any] = {
        "manifest_revision": decoded[MANIFEST][0],
        "topics_revision": decoded[TOPICS][0],
        "relations_revision": decoded[RELATIONS][0],
        "vocab_revision": decoded[VOCAB][0],
        "active_artifacts": active_inventory,
    }
    result = atlas_state.prepare_source_taxonomy_remediation_candidate(
        documents["manifest"],
        documents["topics"],
        documents["relations"],
        documents["vocab"],
        projections,
    )
    if result.findings:
        _reject(result.findings)
    if result.state == "no-op":
        return {
            "documents": documents,
            "inventory": inventory,
            "result": result,
            "input_bytes": input_bytes,
            "output_bytes": {},
            "targets": [],
        }
    if result.state != "candidate":
        raise Failure(
            "SOURCE_TAXONOMY_REMEDIATION_OUTPUT_INVALID",
            MANIFEST,
            "source-taxonomy remediation reducer result is incomplete",
        )
    output_projections = dict(projections)
    output_bytes: dict[str, bytes] = {}
    targets: list[dict[str, Any]] = []
    for target in result.targets:
        changes = [dict(change) for change in target.changes]
        by_field = {change["field"]: change for change in changes}
        try:
            output_text = atlas_source.render_source_taxonomy_remediation(
                decoded[_logical(target.path)][1],
                expected_source_id=target.source_id,
                primary_domain_change=(
                    None
                    if "primary_domain" not in by_field
                    else {
                        "before": by_field["primary_domain"]["before"],
                        "after": by_field["primary_domain"]["after"],
                    }
                ),
                subdomains_change=(
                    None
                    if "subdomains" not in by_field
                    else {
                        "before": by_field["subdomains"]["before"],
                        "after": by_field["subdomains"]["after"],
                    }
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise Failure(
                "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                _logical(target.path),
                str(exc),
            ) from exc
        raw = output_text.encode("utf-8")
        output_revision = "sha256:" + _hash(raw)
        try:
            output_projections[target.path] = (
                atlas_source.candidate_artifact_projection(
                    output_text,
                    output_revision,
                )
            )
        except ValueError as exc:
            raise Failure(
                "SOURCE_TAXONOMY_REMEDIATION_ARTIFACT_INVALID",
                _logical(target.path),
                str(exc),
            ) from exc
        output_bytes[target.path] = raw
        targets.append(
            {
                "source_id": target.source_id,
                "path": _logical(target.path),
                "preimage_revision": projections[target.path]["revision"],
                "output_revision": output_revision,
                "changes": changes,
            }
        )
    replay = atlas_state.prepare_source_taxonomy_remediation_candidate(
        documents["manifest"],
        documents["topics"],
        documents["relations"],
        documents["vocab"],
        output_projections,
    )
    if replay.findings or replay.state != "no-op":
        findings = _owner_findings(replay.findings)
        findings.append(
            _finding(
                "SOURCE_TAXONOMY_REMEDIATION_OUTPUT_INVALID",
                MANIFEST,
                "rendered output did not replay to no-op",
            )
        )
        normalized = _findings(findings)
        first = normalized[0]
        raise Failure(
            first["code"],
            first["path"],
            first["detail"],
            normalized,
        )
    if tuple(_relative(target["path"]) for target in targets) != (
        _SOURCE_TAXONOMY_TARGET_PATHS
    ):
        raise Failure(
            "SOURCE_TAXONOMY_REMEDIATION_OUTPUT_INVALID",
            MANIFEST,
            "candidate target order differs from the approved numeric order",
        )
    return {
        "documents": documents,
        "inventory": inventory,
        "result": result,
        "input_bytes": input_bytes,
        "output_bytes": output_bytes,
        "targets": targets,
    }


def _source_taxonomy_candidate(
    binding: Mapping[str, str],
    snapshot: Mapping[str, Any],
) -> dict[str, Any] | None:
    result = snapshot["result"]
    if result.state == "no-op":
        return None
    targets = [dict(target) for target in snapshot["targets"]]
    material = {
        "version": VERSION,
        "operation": "migration.apply_source_taxonomy_remediation",
        "migration_id": _SOURCE_TAXONOMY_MIGRATION_ID,
        "binding": dict(binding),
        "inventory": dict(snapshot["inventory"]),
        "targets": targets,
    }
    candidate_sha256 = "sha256:" + _hash(_canonical_no_lf(material))
    return {
        "migration_id": _SOURCE_TAXONOMY_MIGRATION_ID,
        "candidate_sha256": candidate_sha256,
        "targets": targets,
        "approval_literal": (
            "APPLY ATLAS SOURCE TAXONOMY REMEDIATION V1 "
            f"{binding['instance_id']} {candidate_sha256}"
        ),
    }


def _migration_prepare_source_taxonomy_remediation(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    _args(args, set(), "migration.prepare_source_taxonomy_remediation")
    binding = _binding_identity(connector)
    snapshot = _source_taxonomy_snapshot(connector)
    candidate = _source_taxonomy_candidate(binding, snapshot)
    if _binding_identity(connector) != binding:
        raise Failure(
            "REVISION_STALE",
            "connector",
            "connector binding changed during remediation prepare",
        )
    return {
        "state": "no-op" if candidate is None else "candidate",
        "binding": binding,
        "inventory": snapshot["inventory"],
        "candidate": candidate,
    }


def _source_taxonomy_event_validator(
    value: Mapping[str, Any],
    event_path: str,
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> Mapping[str, Any]:
    try:
        if set(value) != {
            "version",
            "migration_id",
            "binding",
            "candidate_sha256",
            "inventory",
            "inventory_sha256",
            "request",
            "request_sha256",
        }:
            raise ValueError("source-taxonomy remediation event fields are invalid")
        if value["version"] != VERSION or value["migration_id"] != (
            _SOURCE_TAXONOMY_MIGRATION_ID
        ):
            raise ValueError("source-taxonomy remediation event identity is invalid")
        binding = value["binding"]
        if not isinstance(binding, Mapping) or set(binding) != {
            "instance_id",
            "binding_revision",
        }:
            raise ValueError("source-taxonomy remediation event binding is invalid")
        if (
            not isinstance(binding["instance_id"], str)
            or not binding["instance_id"]
            or not isinstance(binding["binding_revision"], str)
            or _REVISION.fullmatch(binding["binding_revision"]) is None
            or binding["binding_revision"] == "missing"
        ):
            raise ValueError("source-taxonomy remediation event binding is invalid")
        candidate_sha256 = value["candidate_sha256"]
        if (
            not isinstance(candidate_sha256, str)
            or _REVISION.fullmatch(candidate_sha256) is None
            or candidate_sha256 == "missing"
        ):
            raise ValueError("source-taxonomy remediation candidate hash is invalid")
        inventory = value["inventory"]
        _source_taxonomy_inventory_artifacts(inventory)
        inventory_sha256 = value["inventory_sha256"]
        if inventory_sha256 != "sha256:" + _hash(
            _canonical_no_lf(dict(inventory))
        ):
            raise ValueError("source-taxonomy remediation inventory hash is invalid")
        request = value["request"]
        if not isinstance(request, Mapping) or set(request) != {
            "instance_id",
            "candidate_sha256",
            "approval",
        }:
            raise ValueError("source-taxonomy remediation request is invalid")
        expected_approval = (
            "APPLY ATLAS SOURCE TAXONOMY REMEDIATION V1 "
            f"{binding['instance_id']} {candidate_sha256}"
        )
        if (
            request["instance_id"] != binding["instance_id"]
            or request["candidate_sha256"] != candidate_sha256
            or request["approval"] != expected_approval
            or value["request_sha256"]
            != "sha256:" + _hash(_canonical_no_lf(dict(request)))
        ):
            raise ValueError(
                "source-taxonomy remediation request binding is invalid"
            )
        if tuple(target.path for target in targets) != (
            _SOURCE_TAXONOMY_TARGET_PATHS
        ):
            raise ValueError(
                "source-taxonomy remediation event target set is invalid"
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise atlas_transaction.TransactionRecordError(
            event_path,
            str(exc),
        ) from exc
    return dict(value)


def _source_taxonomy_identity_binding(
    record: Mapping[str, Any],
    _event_hash: str,
) -> atlas_transaction.TransactionIdentity:
    base = {
        "migration_id": record.get("migration_id"),
        "candidate_sha256": record.get("candidate_sha256"),
        "inventory_sha256": record.get("inventory_sha256"),
        "request_sha256": record.get("request_sha256"),
    }
    return atlas_transaction.TransactionIdentity(
        base=base,
        intent={
            **base,
            "binding": dict(record.get("binding", {})),
        },
    )


def _source_taxonomy_owner_proof(
    record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
) -> dict[str, Any]:
    return {
        "inventory_sha256": record["inventory_sha256"],
        "target_output_revisions": [
            {
                "path": _logical(target.path),
                "revision": "sha256:" + atlas_transaction.sha256(
                    target.output_bytes
                ),
            }
            for target in plan.targets
        ],
        "taxonomy_closure": True,
    }


def _source_taxonomy_terminal_validator(
    status: str,
    record: Mapping[str, Any],
    raw: bytes,
    plan: atlas_transaction.TransactionPlan,
) -> None:
    intent_sha256 = atlas_transaction.sha256(
        atlas_transaction.canonical_json(plan.intent)
    )
    expected: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "intent_sha256": intent_sha256,
    }
    if status == "applied":
        expected["owner_proof"] = _source_taxonomy_owner_proof(record, plan)
    if raw != atlas_transaction.canonical_json(expected):
        raise atlas_transaction.TransactionRecordError(
            f"{plan.transaction_root}/{plan.transaction_id}/{status}.json",
            "source-taxonomy remediation terminal proof is invalid",
        )


def _source_taxonomy_transaction_policy(
) -> atlas_transaction.TransactionPolicy:
    return atlas_transaction.TransactionPolicy(
        owner_id=_SOURCE_TAXONOMY_OWNER_ID,
        target_allowlist=_source_taxonomy_target_allowed,
        target_rank=_source_taxonomy_target_rank,
        identity_binding=_source_taxonomy_identity_binding,
        event_validator=_source_taxonomy_event_validator,
        transaction_root=_SOURCE_TAXONOMY_TRANSACTION_ROOT,
        terminal_statuses=(
            "applied",
            "aborted",
            "rolled-back",
            "manual-conflict",
        ),
        terminal_validator=_source_taxonomy_terminal_validator,
    )


def _source_taxonomy_plan(
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> atlas_transaction.TransactionPlan:
    provisional = atlas_transaction.build_transaction_plan(
        event_path="pending/event.json",
        event_record=record,
        targets=targets,
        target_allowlist=_source_taxonomy_target_allowed,
        target_rank=_source_taxonomy_target_rank,
        identity_binding=_source_taxonomy_identity_binding,
        transaction_root=_SOURCE_TAXONOMY_TRANSACTION_ROOT,
    )
    return atlas_transaction.build_transaction_plan(
        event_path=(
            f"{_SOURCE_TAXONOMY_TRANSACTION_ROOT}/"
            f"{provisional.transaction_id}/event.json"
        ),
        event_record=record,
        targets=targets,
        target_allowlist=_source_taxonomy_target_allowed,
        target_rank=_source_taxonomy_target_rank,
        identity_binding=_source_taxonomy_identity_binding,
        transaction_root=_SOURCE_TAXONOMY_TRANSACTION_ROOT,
    )


def _source_taxonomy_post_proof(
    connector: Any,
    record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
) -> dict[str, Any]:
    try:
        binding = dict(record["binding"])
        if _binding_identity(connector) != binding:
            raise ValueError("connector binding changed during post-validation")
        inventory = dict(record["inventory"])
        active_inventory = _source_taxonomy_inventory_artifacts(inventory)
        registry_uris = {
            "manifest": MANIFEST,
            "topics": TOPICS,
            "relations": RELATIONS,
            "vocab": VOCAB,
        }
        artifact_uris = [str(item["path"]) for item in active_inventory]
        paths = [*registry_uris.values(), *artifact_uris]
        snapshot = connector.consistent_read(paths)
        if not isinstance(snapshot, Mapping) or set(snapshot) != set(paths):
            raise ValueError("post-validation consistent-read set is invalid")
        decoded = {
            uri: _migration_snapshot_entry(snapshot[uri], uri) for uri in paths
        }
        expected_registry = {
            MANIFEST: inventory["manifest_revision"],
            TOPICS: inventory["topics_revision"],
            RELATIONS: inventory["relations_revision"],
            VOCAB: inventory["vocab_revision"],
        }
        for uri, revision in expected_registry.items():
            if decoded[uri][0] != revision:
                raise ValueError(f"{uri} changed during remediation")
        targets_by_path = {target.path: target for target in plan.targets}
        inventory_by_path = {
            _relative(str(item["path"])): item for item in active_inventory
        }
        for relative, item in inventory_by_path.items():
            actual_revision = decoded[_logical(relative)][0]
            expected_revision = (
                "sha256:"
                + atlas_transaction.sha256(targets_by_path[relative].output_bytes)
                if relative in targets_by_path
                else item["revision"]
            )
            if actual_revision != expected_revision:
                raise ValueError(
                    f"{_logical(relative)} revision changed during remediation"
                )
        documents = {
            name: decoded[uri][1] for name, uri in registry_uris.items()
        }
        document_findings = atlas_state.validate_documents(
            documents["manifest"],
            documents["topics"],
            documents["relations"],
            vocab_text=documents["vocab"],
        )
        if document_findings:
            first = document_findings[0]
            raise ValueError(
                f"{first.code}: {first.path}: {first.detail or first.row or ''}"
            )
        manifest_rows, manifest_findings = atlas_state.validated_manifest_rows(
            documents["manifest"]
        )
        if manifest_findings:
            raise ValueError("manifest failed remediation post-validation")
        active_rows = sorted(
            (row for row in manifest_rows if row["Status"] == "active"),
            key=lambda row: (int(row["Source seq"]), row["Source ID"]),
        )
        observed_inventory = [
            {
                "source_seq": int(row["Source seq"]),
                "source_id": row["Source ID"],
                "path": _logical(row["Artifact"]),
                "revision": decoded[_logical(row["Artifact"])][0],
            }
            for row in active_rows
        ]
        expected_identity = [
            {
                "source_seq": item["source_seq"],
                "source_id": item["source_id"],
                "path": item["path"],
            }
            for item in active_inventory
        ]
        observed_identity = [
            {
                "source_seq": item["source_seq"],
                "source_id": item["source_id"],
                "path": item["path"],
            }
            for item in observed_inventory
        ]
        if observed_identity != expected_identity:
            raise ValueError(
                "active source identity changed during remediation"
            )
        projections: dict[str, Mapping[str, Any]] = {}
        row_by_path = {row["Artifact"]: row for row in active_rows}
        for relative, item in inventory_by_path.items():
            uri = _logical(relative)
            revision, text = decoded[uri]
            raw = snapshot[uri]["bytes"]
            if relative in targets_by_path and raw != (
                targets_by_path[relative].output_bytes
            ):
                raise ValueError(f"{uri} does not equal the approved output")
            projection = atlas_source.candidate_artifact_projection(text, revision)
            projections[relative] = projection
            parsed = atlas_source.parse_artifact(text).values
            row = row_by_path[relative]
            identity = {
                "source_id": atlas_source.scalar(parsed, "source_id"),
                "source_seq": atlas_source.scalar(parsed, "source_seq"),
                "canonical_url": atlas_source.scalar(parsed, "canonical_url"),
                "content_hash": atlas_source.scalar(parsed, "content_hash"),
                "source_kind": atlas_source.scalar(parsed, "source_kind"),
                "route_status": atlas_source.scalar(parsed, "routing_status"),
            }
            if identity != {
                "source_id": row["Source ID"],
                "source_seq": row["Source seq"],
                "canonical_url": row["Canonical URL"],
                "content_hash": row["Content hash"],
                "source_kind": projection["source_kind"],
                "route_status": row["Route status"],
            }:
                raise ValueError(f"{uri} identity differs from MANIFEST")
            taxonomy_values = [
                projection["source_kind"],
                projection["primary_domain"],
                *projection["secondary_domains"],
                *projection["subdomains"],
                *projection["canonical_tags"],
            ]
            if any(
                value in _SOURCE_TAXONOMY_LEGACY_VALUES
                for value in taxonomy_values
            ):
                raise ValueError(f"{uri} retains a legacy taxonomy value")
            taxonomy_findings = atlas_state.validate_source_taxonomy(
                documents["vocab"],
                source_kind=projection["source_kind"],
                primary_domain=projection["primary_domain"],
                secondary_domains=projection["secondary_domains"],
                subdomains=projection["subdomains"],
                canonical_tags=projection["canonical_tags"],
                path=relative,
            )
            if taxonomy_findings:
                first = taxonomy_findings[0]
                raise ValueError(
                    f"{first.code}: {first.path}: {first.detail or first.row or ''}"
                )
        replay = atlas_state.prepare_source_taxonomy_remediation_candidate(
            documents["manifest"],
            documents["topics"],
            documents["relations"],
            documents["vocab"],
            projections,
        )
        if replay.findings or replay.state != "no-op":
            raise ValueError(
                "source-taxonomy remediation replay did not return no-op"
            )
        if _binding_identity(connector) != binding:
            raise ValueError("connector binding changed during post-validation")
        proof = _source_taxonomy_owner_proof(record, plan)
        if proof["inventory_sha256"] != (
            "sha256:" + _hash(_canonical_no_lf(inventory))
        ):
            raise ValueError("source-taxonomy remediation inventory proof is invalid")
        return proof
    except OSError:
        raise
    except atlas_transaction.TransactionError:
        raise
    except Exception as exc:
        raise atlas_transaction.TransactionError(str(exc)) from exc


def _source_taxonomy_post_validator(
    connector: Any,
    record: Mapping[str, Any],
    trace: dict[str, Any],
) -> atlas_transaction.PostValidator:
    def validate(
        _port: atlas_transaction.ConnectorPort,
        plan: atlas_transaction.TransactionPlan,
    ) -> dict[str, Any]:
        trace["attempted"] = True
        try:
            proof = _source_taxonomy_post_proof(connector, record, plan)
        except atlas_transaction.TransactionError as exc:
            trace["findings"] = [
                _finding(
                    "MIGRATION_POST_VALIDATION_FAILED",
                    MANIFEST,
                    str(exc),
                )
            ]
            raise
        trace["ok"] = True
        trace["taxonomy_closure"] = True
        return proof

    return validate


def _source_taxonomy_target_revisions(
    connector: Any,
    plan: atlas_transaction.TransactionPlan,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for target in plan.targets:
        preimage_revision = (
            "missing"
            if target.input_bytes is None
            else "sha256:" + atlas_transaction.sha256(target.input_bytes)
        )
        output_revision = "sha256:" + atlas_transaction.sha256(
            target.output_bytes
        )
        try:
            raw = connector.read_bytes(_logical(target.path))
        except FileNotFoundError:
            raw = None
            current_revision = "missing"
        except (OSError, ValueError):
            raw = None
            current_revision = "unknown"
        else:
            current_revision = "sha256:" + _hash(raw)
        if current_revision == preimage_revision:
            classification = "input"
        elif current_revision == output_revision:
            classification = "output"
        elif current_revision == "unknown":
            classification = "unknown"
        else:
            classification = "other"
        rows.append(
            {
                "path": _logical(target.path),
                "preimage_revision": preimage_revision,
                "output_revision": output_revision,
                "current_revision": current_revision,
                "classification": classification,
            }
        )
    return rows


def _source_taxonomy_terminal_result(
    connector: Any,
    journal: atlas_transaction.Journal,
    trace: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    status = journal.status
    if status not in {"applied", "aborted", "rolled-back", "manual-conflict"}:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(
                f"{journal.plan.transaction_root}/"
                f"{journal.plan.transaction_id}"
            ),
            "source-taxonomy remediation transaction is not terminal",
        )
    record = journal.record
    target_revisions = _source_taxonomy_target_revisions(
        connector,
        journal.plan,
    )
    findings = list((trace or {}).get("findings", []))
    if status == "manual-conflict" and not findings:
        findings.append(
            _finding(
                "MIGRATION_EFFECT_UNKNOWN",
                _logical(
                    f"{journal.plan.transaction_root}/"
                    f"{journal.plan.transaction_id}/intent.json"
                ),
                "source-taxonomy remediation requires manual reconciliation",
            )
        )
    attempted = bool((trace or {}).get("attempted", False))
    if status == "applied":
        attempted = True
    elif all(
        f"progress/{index:06d}.json" in journal.record_names
        for index in range(len(journal.plan.targets))
    ):
        attempted = True
    post_validation = {
        "attempted": attempted,
        "ok": status == "applied",
        "inventory_sha256": record["inventory_sha256"],
        "taxonomy_closure": status == "applied",
        "findings": _findings(findings),
    }
    return {
        "version": VERSION,
        "state": status,
        "binding": dict(record["binding"]),
        "candidate_sha256": record["candidate_sha256"],
        "transaction_id": journal.plan.transaction_id,
        "inventory": dict(record["inventory"]),
        "target_revisions": target_revisions,
        "post_validation": post_validation,
        "findings": _findings(findings),
    }


def _source_taxonomy_recoverable_failure(
    connector: Any,
    plan: atlas_transaction.TransactionPlan,
    request: Mapping[str, Any],
    detail: str,
) -> Failure:
    target_revisions = _source_taxonomy_target_revisions(connector, plan)
    classifications = {item["classification"] for item in target_revisions}
    effect = (
        "partial"
        if classifications <= {"input", "output"} and "output" in classifications
        else "unknown"
    )
    path = _logical(
        f"{plan.transaction_root}/{plan.transaction_id}/intent.json"
    )
    findings = [_finding("TRANSACTION_RECOVERABLE", path, detail)]
    return Failure(
        "TRANSACTION_RECOVERABLE",
        path,
        detail,
        findings,
        result={
            "version": VERSION,
            "transaction_id": plan.transaction_id,
            "target_revisions": target_revisions,
            "effect_classification": effect,
        },
    )


def _source_taxonomy_load_journal(
    port: Any,
    transaction_id: str,
) -> atlas_transaction.Journal:
    try:
        journal = atlas_transaction.load_transaction(
            port,
            transaction_id,
            _source_taxonomy_transaction_policy(),
        )
    except atlas_transaction.TransactionRecordError as exc:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _record_path(exc.path),
            exc.detail,
        ) from exc
    if journal.plan.attempt != 0:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            "args.transaction_id",
            "source-taxonomy remediation does not permit successors",
        )
    return journal


def _migration_apply_source_taxonomy_remediation(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    value = _args(
        args,
        {"instance_id", "candidate_sha256", "approval"},
        "migration.apply_source_taxonomy_remediation",
    )
    instance_id = _text(value["instance_id"], "args.instance_id")
    candidate_sha256 = _text(
        value["candidate_sha256"],
        "args.candidate_sha256",
    )
    approval = _text(value["approval"], "args.approval")
    if (
        not instance_id
        or _REVISION.fullmatch(candidate_sha256) is None
        or candidate_sha256 == "missing"
    ):
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args",
            "instance and candidate identity are invalid",
        )
    expected_approval = (
        "APPLY ATLAS SOURCE TAXONOMY REMEDIATION V1 "
        f"{instance_id} {candidate_sha256}"
    )
    if approval != expected_approval:
        raise Failure(
            "MIGRATION_APPROVAL_INVALID",
            "args.approval",
            "approval literal does not bind instance and candidate",
        )
    _mutations(connector)
    request = dict(value)
    with connector.mutation_session():
        binding = _binding_identity(connector)
        snapshot = _source_taxonomy_snapshot(connector)
        candidate = _source_taxonomy_candidate(binding, snapshot)
        if (
            candidate is None
            or instance_id != binding["instance_id"]
            or candidate["candidate_sha256"] != candidate_sha256
            or candidate["approval_literal"] != approval
        ):
            raise Failure(
                "MIGRATION_CANDIDATE_STALE",
                "args.candidate_sha256",
                "candidate no longer matches the complete current inventory",
            )
        inventory = snapshot["inventory"]
        revision_expectations = {
            MANIFEST: inventory["manifest_revision"],
            TOPICS: inventory["topics_revision"],
            RELATIONS: inventory["relations_revision"],
            VOCAB: inventory["vocab_revision"],
            **{
                item["path"]: item["revision"]
                for item in inventory["active_artifacts"]
            },
        }
        if _binding_identity(connector) != binding or any(
            connector.revision(path) != revision
            for path, revision in revision_expectations.items()
        ):
            raise Failure(
                "MIGRATION_CANDIDATE_STALE",
                "snapshot",
                "binding or inventory changed before transaction intent",
            )
        record = {
            "version": VERSION,
            "migration_id": _SOURCE_TAXONOMY_MIGRATION_ID,
            "binding": binding,
            "candidate_sha256": candidate_sha256,
            "inventory": inventory,
            "inventory_sha256": (
                "sha256:" + _hash(_canonical_no_lf(inventory))
            ),
            "request": request,
            "request_sha256": (
                "sha256:" + _hash(_canonical_no_lf(request))
            ),
        }
        targets = tuple(
            atlas_transaction.TransactionTarget(
                path,
                snapshot["input_bytes"][path],
                snapshot["output_bytes"][path],
            )
            for path in _SOURCE_TAXONOMY_TARGET_PATHS
        )
        try:
            plan = _source_taxonomy_plan(record, targets)
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "TRANSACTION_INVALID",
                "targets",
                str(exc),
            ) from exc
        port = _Port(connector)
        try:
            atlas_transaction.store_event(
                port,
                _SOURCE_TAXONOMY_TRANSACTION_ROOT,
                record,
                plan,
            )
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "TRANSACTION_EVENT_COLLISION",
                _logical(
                    f"{plan.transaction_root}/{plan.transaction_id}/event.json"
                ),
                str(exc),
            ) from exc
        trace: dict[str, Any] = {
            "attempted": False,
            "ok": False,
            "taxonomy_closure": False,
            "findings": [],
        }
        terminal_validator = lambda status, raw, current_plan: (
            _source_taxonomy_terminal_validator(
                status,
                record,
                raw,
                current_plan,
            )
        )
        try:
            atlas_transaction.execute_transaction(
                port,
                _SOURCE_TAXONOMY_TRANSACTION_ROOT,
                plan,
                target_allowlist=_source_taxonomy_target_allowed,
                target_rank=_source_taxonomy_target_rank,
                post_validator=_source_taxonomy_post_validator(
                    connector,
                    record,
                    trace,
                ),
                terminal_validator=terminal_validator,
                surface_post_intent_failure=True,
            )
        except Exception as exc:
            try:
                intent = port.read_record(
                    f"{plan.transaction_root}/{plan.transaction_id}/intent.json"
                )
            except Exception:
                raise exc
            if intent is None:
                raise exc
            raise _source_taxonomy_recoverable_failure(
                connector,
                plan,
                request,
                str(exc),
            ) from exc
        try:
            journal = _source_taxonomy_load_journal(port, plan.transaction_id)
        except (ConnectorIOError, ConnectorDurabilityError) as exc:
            raise _source_taxonomy_recoverable_failure(
                connector,
                plan,
                request,
                str(exc),
            ) from exc
        return _source_taxonomy_terminal_result(
            connector,
            journal,
            trace,
        )


def _migration_recover_source_taxonomy_remediation(
    connector: Any,
    args: Any,
) -> dict[str, Any]:
    value = _args(
        args,
        {"version", "transaction_id", "request"},
        "migration.recover_source_taxonomy_remediation",
    )
    if type(value["version"]) is not int or value["version"] != VERSION:
        raise Failure(
            "MIGRATION_RECOVERY_INVALID",
            "args.version",
            "version must be 1",
        )
    transaction_id = _text(value["transaction_id"], "args.transaction_id")
    if _TX_ID.fullmatch(transaction_id) is None:
        raise Failure(
            "TRANSACTION_UNKNOWN",
            "args.transaction_id",
            "transaction ID is invalid",
        )
    request = _object(value["request"], "args.request")
    if set(request) != {"instance_id", "candidate_sha256", "approval"}:
        raise Failure(
            "MIGRATION_RECOVERY_INVALID",
            "args.request",
            "recovery request fields are invalid",
        )
    _mutations(connector)
    with connector.mutation_session():
        port = _Port(connector)
        journal = _source_taxonomy_load_journal(port, transaction_id)
        record = journal.record
        if (
            request != record["request"]
            or "sha256:" + _hash(_canonical_no_lf(dict(request)))
            != record["request_sha256"]
            or _binding_identity(connector) != record["binding"]
        ):
            raise Failure(
                "MIGRATION_RECOVERY_INVALID",
                "args.request",
                "recovery request does not bind the immutable transaction",
            )
        if journal.status is not None:
            return _source_taxonomy_terminal_result(connector, journal)
        trace: dict[str, Any] = {
            "attempted": False,
            "ok": False,
            "taxonomy_closure": False,
            "findings": [],
        }
        terminal_validator = lambda status, raw, current_plan: (
            _source_taxonomy_terminal_validator(
                status,
                record,
                raw,
                current_plan,
            )
        )
        try:
            atlas_transaction.recover_transaction(
                port,
                _SOURCE_TAXONOMY_TRANSACTION_ROOT,
                journal.plan,
                abort_unprepared=True,
                target_allowlist=_source_taxonomy_target_allowed,
                target_rank=_source_taxonomy_target_rank,
                post_validator=_source_taxonomy_post_validator(
                    connector,
                    record,
                    trace,
                ),
                terminal_validator=terminal_validator,
            )
        except Exception as exc:
            try:
                intent = port.read_record(
                    f"{journal.plan.transaction_root}/"
                    f"{journal.plan.transaction_id}/intent.json"
                )
            except Exception:
                raise exc
            if intent is None:
                raise exc
            raise _source_taxonomy_recoverable_failure(
                connector,
                journal.plan,
                request,
                str(exc),
            ) from exc
        try:
            terminal = _source_taxonomy_load_journal(port, transaction_id)
        except (ConnectorIOError, ConnectorDurabilityError) as exc:
            raise _source_taxonomy_recoverable_failure(
                connector,
                journal.plan,
                request,
                str(exc),
            ) from exc
        return _source_taxonomy_terminal_result(
            connector,
            terminal,
            trace,
        )


class _Port:
    def __init__(self, connector: Any) -> None:
        self.connector = connector

    def _uri(self, path: str) -> str:
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or ".." in path.split("/")
        ):
            raise atlas_transaction.TransactionError("transaction path is invalid")
        return _logical(path)

    def read(self, path: str) -> bytes | None:
        try:
            return self.connector.read_bytes(self._uri(path))
        except FileNotFoundError:
            return None
        except ConnectorConflictError as exc:
            raise atlas_transaction.TransactionTargetConflict(
                path,
                str(exc),
            ) from exc
        except ConnectorBindingError:
            raise
        except (ConnectorIOError, ConnectorDurabilityError):
            raise
        except ValueError as exc:
            raise ConnectorBindingError(str(exc)) from exc

    def read_record(self, path: str) -> bytes | None:
        uri = self._uri(path)
        try:
            return self.connector.read_bytes(uri)
        except FileNotFoundError:
            return None
        except (
            ConnectorBindingError,
            ConnectorConflictError,
            ConnectorIOError,
            ConnectorDurabilityError,
        ):
            raise
        except atlas_transaction.TransactionError:
            raise
        except ValueError as exc:
            raise atlas_transaction.TransactionRecordError(uri, str(exc)) from exc

    def create(self, path: str, data: bytes) -> None:
        uri = self._uri(path)
        try:
            self.connector.conditional_replace(uri, "missing", data)
        except (
            ConnectorBindingError,
            ConnectorIOError,
            ConnectorDurabilityError,
        ):
            raise
        except ConnectorConflictError:
            raise
        except atlas_transaction.TransactionError:
            raise
        except ValueError as exc:
            raise atlas_transaction.TransactionRecordError(uri, str(exc)) from exc

    def write(self, path: str, data: bytes, expected_revision: str) -> None:
        try:
            self.connector.conditional_replace(self._uri(path), expected_revision, data)
        except ConnectorBindingError:
            raise
        except ConnectorConflictError as exc:
            raise atlas_transaction.TransactionTargetConflict(path, str(exc)) from exc

    def delete(self, path: str, expected_revision: str) -> None:
        try:
            self.connector.delete(self._uri(path), expected_revision)
        except ConnectorBindingError:
            raise
        except ConnectorConflictError as exc:
            raise atlas_transaction.TransactionTargetConflict(path, str(exc)) from exc

    def list(self, path: str) -> list[str]:
        root_uri = self._uri(path)
        try:
            values = self.connector.list(root_uri)
        except FileNotFoundError:
            return []
        except (
            ConnectorBindingError,
            ConnectorConflictError,
            ConnectorIOError,
            ConnectorDurabilityError,
        ):
            raise
        except atlas_transaction.TransactionError:
            raise
        except ValueError as exc:
            raise atlas_transaction.TransactionRecordError(root_uri, str(exc)) from exc
        prefix = root_uri.rstrip("/") + "/"
        result: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value.startswith(prefix):
                raise atlas_transaction.TransactionRecordError(
                    root_uri, "transaction namespace listing is invalid"
                )
            result.append(value[len(prefix) :])
        return result


def _event(value: Any) -> dict[str, Any]:
    record = _object(value, "event_record")
    fields = {
        "version",
        "event_type",
        "source_id",
        "promotion",
        "event",
        "route_decision",
    }
    if (
        set(record) != fields
        or type(record["version"]) is not int
        or record["version"] != VERSION
    ):
        raise Failure(
            "EVENT_RECORD_INVALID", "event_record", "event record fields are invalid"
        )
    event = _object(record["event"], "event_record.event")
    source_id = _text(record["source_id"], "event_record.source_id")
    event_type = record["event_type"]
    event_kind = event.get("type")
    expected = {
        "source": "source-upsert",
        "source-upsert": "source-upsert",
        "route": "route-upsert",
        "route-upsert": "route-upsert",
    }
    repair_event = event_kind in {
        "repair-table-placement",
        "repair-relation-notes",
    }
    if (
        not isinstance(event_type, str)
        or (repair_event and (event_type != "repair" or source_id != "repair"))
        or (
            not repair_event
            and (
                expected.get(event_type) != event_kind
                or event.get("source_id") != source_id
            )
        )
    ):
        raise Failure(
            "EVENT_RECORD_INVALID", "event_record", "event identity is inconsistent"
        )
    promotion = record["promotion"]
    if promotion is not None:
        if not isinstance(promotion, Mapping) or set(promotion) != {
            "artifact_uri",
            "artifact_revision",
            "evidence_uri",
            "evidence_revision",
        }:
            raise Failure(
                "EVENT_RECORD_INVALID",
                "event_record.promotion",
                "promotion provenance fields are invalid",
            )
        for name in ("artifact_uri", "evidence_uri"):
            try:
                _uri(promotion[name], f"event_record.promotion.{name}")
            except Failure as exc:
                raise Failure(
                    "EVENT_RECORD_INVALID",
                    f"event_record.promotion.{name}",
                    exc.detail,
                ) from exc
        for name in ("artifact_revision", "evidence_revision"):
            revision = promotion[name]
            if (
                not isinstance(revision, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", revision) is None
            ):
                raise Failure(
                    "EVENT_RECORD_INVALID",
                    f"event_record.promotion.{name}",
                    "revision is invalid",
                )
    if promotion is not None and event_kind != "source-upsert":
        raise Failure(
            "EVENT_RECORD_INVALID",
            "event_record.promotion",
            "only a source-upsert event may carry promotion provenance",
        )
    if event["type"] == "route-upsert":
        if record["route_decision"] != {
            "outcome": event.get("outcome"),
            "edges": event.get("edges"),
        }:
            raise Failure(
                "EVENT_RECORD_INVALID",
                "event_record.route_decision",
                "route decision does not bind event",
            )
    elif record["route_decision"] is not None:
        raise Failure(
            "EVENT_RECORD_INVALID",
            "event_record.route_decision",
            "non-route event cannot carry route decision",
        )
    return record


def _rank(path: str) -> tuple[int, str]:
    if path == atlas_state.VOCAB_PATH:
        return 0, path
    if path.startswith(atlas_source.ARTIFACT_PREFIX) and path.endswith(".md"):
        return 1, path
    order = {
        atlas_state.RELATIONS_PATH: 2,
        atlas_state.TOPICS_PATH: 3,
        atlas_state.MANIFEST_PATH: 4,
    }
    if path not in order:
        raise Failure(
            "TARGET_NOT_ALLOWED",
            "targets",
            "target is outside the source/route write set",
        )
    return order[path], path


def _target_allowed(path: str) -> bool:
    return (path.startswith(atlas_source.ARTIFACT_PREFIX) and path.endswith(".md")) or (
        path
        in {
            atlas_state.RELATIONS_PATH,
            atlas_state.VOCAB_PATH,
            atlas_state.TOPICS_PATH,
            atlas_state.MANIFEST_PATH,
        }
    )


def _identity_binding(
    record: Mapping[str, Any], event_hash: str
) -> atlas_transaction.TransactionIdentity:
    return atlas_transaction.TransactionIdentity(
        base={
            "event_record_sha256": event_hash,
            "source_id": record.get("source_id"),
        },
        intent={
            "event_type": record.get("event_type"),
            "source_id": record.get("source_id"),
        },
    )


def _targets(
    value: Any,
) -> tuple[tuple[atlas_transaction.TransactionTarget, ...], dict[str, str]]:
    if type(value) is not list or not value:
        raise Failure("TARGETS_INVALID", "targets", "targets must be a nonempty array")
    targets: list[atlas_transaction.TransactionTarget] = []
    revisions: dict[str, str] = {}
    for index, item in enumerate(value):
        row = _object(item, f"targets[{index}]")
        if set(row) != {"path", "expected_revision", "text"}:
            raise Failure(
                "TARGETS_INVALID", f"targets[{index}]", "target fields are invalid"
            )
        uri = _uri(row["path"], f"targets[{index}].path")
        expected = _text(
            row["expected_revision"], f"targets[{index}].expected_revision"
        )
        if _REVISION.fullmatch(expected) is None:
            raise Failure(
                "TARGETS_INVALID",
                f"targets[{index}].expected_revision",
                "revision is invalid",
            )
        path = _relative(uri)
        _rank(path)
        try:
            output = _text(row["text"], f"targets[{index}].text").encode("utf-8")
        except UnicodeEncodeError as exc:
            raise Failure(
                "TARGETS_INVALID", f"targets[{index}].text", "text is not UTF-8"
            ) from exc
        targets.append(atlas_transaction.TransactionTarget(path, None, output))
        revisions[path] = expected
    ordered = tuple(sorted(targets, key=lambda item: _rank(item.path)))
    if tuple(targets) != ordered or len(revisions) != len(targets):
        raise Failure(
            "TARGETS_INVALID", "targets", "targets are not uniquely canonical ordered"
        )
    return ordered, revisions


def _bind(
    connector: Any,
    targets: Sequence[atlas_transaction.TransactionTarget],
    expected: Mapping[str, str],
) -> tuple[atlas_transaction.TransactionTarget, ...]:
    result: list[atlas_transaction.TransactionTarget] = []
    for target in targets:
        uri = _logical(target.path)
        revision = connector.revision(uri)
        if revision != expected[target.path]:
            raise Failure(
                "REVISION_STALE", uri, "target revision changed before authorization"
            )
        try:
            input_bytes = None if revision == "missing" else connector.read_bytes(uri)
        except FileNotFoundError as exc:
            raise Failure(
                "REVISION_STALE", uri, "target disappeared during authorization"
            ) from exc
        result.append(
            atlas_transaction.TransactionTarget(
                target.path, input_bytes, target.output_bytes
            )
        )
    return tuple(result)


def _source_artifact_guard(
    documents: Mapping[str, str],
    reduction: atlas_state.ReductionResult,
    event: Mapping[str, Any],
    target: atlas_transaction.TransactionTarget,
    living_artifact_text: str | None,
) -> None:
    try:
        text = target.output_bytes.decode("utf-8")
        parsed = atlas_source.parse_artifact(text)
        if atlas_source.render_artifact(parsed.values, parsed.body) != text:
            raise ValueError("artifact bytes are not in canonical rendered form")
        source = reduction.derived["source"]
        if not isinstance(source, Mapping):
            raise ValueError("source reducer output is invalid")
        expected_scalars = {
            "schema_version": "1",
            "note_type": "source-summary",
            "managed_by": "atlas",
            "source_id": source["source_id"],
            "source_seq": str(source["source_seq"]),
            "canonical_url": source["canonical_url"],
            "first_seen": source["first_seen"],
            "last_checked": event["checked_on"],
            "last_summarized": event["summarized_on"],
            "content_hash": source["content_hash"],
            "refresh_after": event["refresh_after"],
            "routing_status": source["route_status"],
        }
        actual_scalars = {
            name: atlas_source.scalar(parsed.values, name) for name in expected_scalars
        }
        if actual_scalars != expected_scalars:
            raise ValueError(
                "artifact identity, dates, or route status differ from reducer output"
            )
        arrays = {
            name: json.loads(parsed.values[name])
            for name in (
                "subdomains",
                "secondary_domains",
                "canonical_tags",
                "candidate_terms",
            )
        }
        if any(
            not isinstance(value, list)
            or any(not isinstance(item, str) for item in value)
            for value in arrays.values()
        ):
            raise ValueError("artifact taxonomy fields are invalid")
        actual_taxonomy = {
            "primary_domain": atlas_source.scalar(parsed.values, "primary_domain"),
            **arrays,
        }
        living = (
            None
            if living_artifact_text is None
            else atlas_source.parse_artifact(living_artifact_text)
        )
        content_changed = source.get("content_changed")
        created = source.get("created")
        if not isinstance(content_changed, bool) or not isinstance(created, bool):
            raise ValueError("source reducer transition is invalid")
        preserved_scalars = ("acquired_by", "acquisition_run")
        if content_changed:
            classification = reduction.derived.get("classification")
            if not isinstance(classification, Mapping):
                raise ValueError("new or changed source classification is missing")
            expected_taxonomy = {
                "primary_domain": classification["primary_domain"],
                "subdomains": classification["subdomains"],
                "secondary_domains": (
                    []
                    if living is None
                    else json.loads(living.values["secondary_domains"])
                ),
                "canonical_tags": classification["canonical_tags"],
                "candidate_terms": classification["candidate_terms"],
            }
            if actual_taxonomy != expected_taxonomy:
                raise ValueError("artifact classification differs from reducer output")
            if atlas_source.scalar(parsed.values, "routed_at"):
                raise ValueError("new or changed source must clear routed_at")
            if living is not None and any(
                parsed.values[name] != living.values[name] for name in preserved_scalars
            ):
                raise ValueError(
                    "changed source acquisition provenance is not preserved"
                )
        else:
            if living is None:
                raise ValueError("same-hash source has no living artifact")
            if any(
                parsed.values[name] != living.values[name]
                for name in (
                    "primary_domain",
                    "subdomains",
                    "secondary_domains",
                    "canonical_tags",
                    "candidate_terms",
                    "routed_at",
                    *preserved_scalars,
                )
            ):
                raise ValueError("same-hash source bindings are not preserved")
        vocab_text = reduction.documents.get("vocab", documents["vocab"])
        taxonomy_findings = atlas_state.validate_source_taxonomy(
            vocab_text,
            source_kind=atlas_source.scalar(parsed.values, "source_kind"),
            primary_domain=actual_taxonomy["primary_domain"],
            secondary_domains=actual_taxonomy["secondary_domains"],
            subdomains=actual_taxonomy["subdomains"],
            canonical_tags=actual_taxonomy["canonical_tags"],
            path=target.path,
        )
        if taxonomy_findings:
            raise ValueError("artifact taxonomy is not valid against reducer output")
        atlas_source.candidate_artifact_projection(
            text, "sha256:" + _hash(target.output_bytes)
        )
    except (
        KeyError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        raise Failure(
            "SOURCE_PREFLIGHT_ARTIFACT_INVALID",
            _logical(target.path),
            str(exc),
        ) from exc


def _source_guard(
    connector: Any,
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> None:
    event = record["event"]
    if event.get("type") != "source-upsert" or record.get("promotion") is not None:
        return
    documents = {**_documents(connector), "vocab": connector.read_text(VOCAB)}
    _validate(documents)
    manifest_rows, manifest_findings = atlas_state.validated_manifest_rows(
        documents["manifest"]
    )
    _reject(manifest_findings)
    existing = next(
        (row for row in manifest_rows if row["Source ID"] == record["source_id"]),
        None,
    )
    living_artifact_text: str | None = None
    if existing is not None:
        try:
            living_artifact_text = connector.read_text(_logical(existing["Artifact"]))
        except FileNotFoundError as exc:
            raise Failure(
                "SOURCE_PREFLIGHT_ARTIFACT_INVALID",
                _logical(existing["Artifact"]),
                "living source artifact is absent",
            ) from exc
    reduction = _reduce(documents, event)
    source = reduction.derived.get("source")
    if not isinstance(source, Mapping):
        raise Failure(
            "SOURCE_PREFLIGHT_INVALID",
            "event_record.event",
            "source reducer output is invalid",
        )
    expected_projection = {
        (
            atlas_state.VOCAB_PATH if name == "vocab" else _relative(_doc_uri(name))
        ): text.encode("utf-8")
        for name, text in reduction.documents.items()
    }
    artifact_targets = [
        target
        for target in targets
        if target.path.startswith(atlas_source.ARTIFACT_PREFIX)
    ]
    artifact_path = source.get("artifact")
    if not isinstance(artifact_path, str):
        raise Failure(
            "SOURCE_PREFLIGHT_INVALID",
            "event_record.event.artifact",
            "source reducer artifact path is invalid",
        )
    artifact_required = bool(source.get("content_changed")) or (
        existing is not None
        and event.get("summarized_on") != existing["Last summarized"]
    )
    if len(artifact_targets) > 1 or (
        artifact_targets and artifact_targets[0].path != artifact_path
    ):
        raise Failure(
            "SOURCE_PREFLIGHT_PROJECTION_MISMATCH",
            "targets",
            "source artifact target differs from reducer output",
        )
    if artifact_targets:
        artifact_target = artifact_targets[0]
        _source_artifact_guard(
            documents,
            reduction,
            event,
            artifact_target,
            living_artifact_text,
        )
        expected_projection[artifact_path] = artifact_target.output_bytes
    elif artifact_required:
        raise Failure(
            "SOURCE_PREFLIGHT_PROJECTION_MISMATCH",
            "targets",
            "source artifact target is missing",
        )
    actual_projection = {target.path: target.output_bytes for target in targets}
    if actual_projection != expected_projection:
        raise Failure(
            "SOURCE_PREFLIGHT_PROJECTION_MISMATCH",
            "targets",
            "source targets do not equal the reducer and artifact projection",
        )


def _route_projection(
    record: Mapping[str, Any],
    documents: Mapping[str, str],
    reduction: atlas_state.ReductionResult,
    artifact_path: str,
    artifact_bytes: bytes | None,
) -> dict[str, bytes]:
    candidate_documents = dict(documents)
    candidate_documents.update(reduction.documents)
    row = next(
        (
            item
            for item, _ in _rows(
                candidate_documents["manifest"],
                atlas_state.MANIFEST_HEADER,
                MANIFEST,
            )
            if item["Source ID"] == record["source_id"]
        ),
        None,
    )
    if row is None:
        raise Failure(
            "ROUTE_PREFLIGHT_SOURCE_MISSING",
            "event_record.source_id",
            "source is absent from reducer output",
        )
    if artifact_bytes is None:
        raise Failure(
            "ROUTE_PREFLIGHT_ARTIFACT_INVALID",
            _logical(artifact_path),
            "source artifact is absent",
        )
    try:
        artifact_text = artifact_bytes.decode("utf-8")
        rendered_artifact = atlas_source.render_route_artifact(
            artifact_text,
            record["event"],
            row["Route status"],
        ).encode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise Failure(
            "ROUTE_PREFLIGHT_ARTIFACT_INVALID",
            _logical(artifact_path),
            str(exc),
        ) from exc
    projection = {
        _relative(_doc_uri(name)): text.encode("utf-8")
        for name, text in reduction.documents.items()
    }
    if rendered_artifact != artifact_bytes:
        projection[artifact_path] = rendered_artifact
    return projection


def _route_guard(
    connector: Any,
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> None:
    event = record["event"]
    if event.get("type") != "route-upsert":
        return
    docs = _documents(connector)
    _validate(docs)
    row = next(
        (
            item
            for item, _ in _rows(
                docs["manifest"], atlas_state.MANIFEST_HEADER, MANIFEST
            )
            if item["Source ID"] == record["source_id"]
        ),
        None,
    )
    if row is None:
        raise Failure(
            "ROUTE_PREFLIGHT_SOURCE_MISSING",
            "event_record.source_id",
            "source is absent",
        )
    if row["Status"] != "active":
        raise Failure(
            "ROUTE_PREFLIGHT_ARCHIVED", "event_record.source_id", "source is archived"
        )
    if event.get("content_hash") != row["Content hash"]:
        raise Failure(
            "ROUTE_PREFLIGHT_HASH_MISMATCH",
            "event_record.event.content_hash",
            "event and manifest hash disagree",
        )
    artifact_uri = _logical(row["Artifact"])
    try:
        artifact_text = connector.read_text(artifact_uri)
        values = atlas_source.parse_artifact(artifact_text).values
        actual = {
            "Source ID": atlas_source.scalar(values, "source_id"),
            "Canonical URL": atlas_source.scalar(values, "canonical_url"),
            "Content hash": atlas_source.scalar(values, "content_hash"),
            "Route status": atlas_source.scalar(values, "routing_status"),
        }
    except (FileNotFoundError, ValueError) as exc:
        raise Failure(
            "ROUTE_PREFLIGHT_ARTIFACT_INVALID", artifact_uri, str(exc)
        ) from exc
    if actual != {key: row[key] for key in actual}:
        raise Failure(
            "ROUTE_PREFLIGHT_HASH_MISMATCH",
            artifact_uri,
            "manifest and artifact identity disagree",
        )
    reduction = _reduce(docs, event)
    expected_projection = _route_projection(
        record,
        docs,
        reduction,
        _relative(artifact_uri),
        artifact_text.encode("utf-8"),
    )
    actual_projection = {target.path: target.output_bytes for target in targets}
    if actual_projection != expected_projection:
        raise Failure(
            "ROUTE_PREFLIGHT_PROJECTION_MISMATCH",
            "targets",
            "route targets do not equal the reducer and renderer projection",
        )


def _repair_guard(
    connector: Any,
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> None:
    event = record["event"]
    if event.get("type") not in {
        "repair-table-placement",
        "repair-relation-notes",
    }:
        return
    docs = _documents(connector)
    reduction = atlas_state.reduce_event(docs, event)
    if not reduction.ok:
        raise Failure(
            "REPAIR_PREFLIGHT_INVALID",
            "event_record.event",
            "repair event is not valid for current state",
            findings=_owner_findings(reduction.findings),
        )
    expected_projection = {
        _relative(_doc_uri(name)): text.encode("utf-8")
        for name, text in reduction.documents.items()
        if text != docs[name]
    }
    actual_projection = {target.path: target.output_bytes for target in targets}
    if actual_projection != expected_projection:
        raise Failure(
            "REPAIR_PREFLIGHT_PROJECTION_MISMATCH",
            "targets",
            "repair targets do not equal the reducer projection",
        )


def _promotion_guard(
    connector: Any,
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> None:
    promotion = record["promotion"]
    if promotion is None:
        return
    if not isinstance(promotion, Mapping):
        raise Failure(
            "SOURCE_PROMOTION_PREFLIGHT_INVALID",
            "event_record.promotion",
            "promotion provenance is invalid",
        )
    artifact_uri = str(promotion["artifact_uri"])
    evidence_uri = str(promotion["evidence_uri"])
    if artifact_uri == evidence_uri:
        raise Failure(
            "SOURCE_PROMOTION_PREFLIGHT_INVALID",
            "event_record.promotion",
            "promotion inputs must be distinct",
        )
    for name, uri in (
        ("artifact", artifact_uri),
        ("evidence", evidence_uri),
    ):
        expected_revision = promotion[f"{name}_revision"]
        if connector.revision(uri) != expected_revision:
            raise Failure(
                "SOURCE_PROMOTION_STALE",
                uri,
                "frozen promotion input revision changed",
            )
    try:
        staged_text = connector.read_bytes(artifact_uri).decode("utf-8")
        worker = atlas_cli.decode(connector.read_bytes(evidence_uri))
        docs = _documents(connector)
        _validate(docs)
        canonical_url, source_id, target_uri = _promotion_identity(
            docs["manifest"],
            staged_text,
            worker,
        )
        if source_id != record["source_id"]:
            raise ValueError("promotion source identity differs from event")
        if target_uri in {artifact_uri, evidence_uri}:
            raise ValueError("promotion inputs overlap the living target")
        target_path = _relative(target_uri)
        bound_inputs = {target.path: target.input_bytes for target in targets}
        if target_path in bound_inputs:
            target_raw = bound_inputs[target_path]
        else:
            target_revision = connector.revision(target_uri)
            target_raw = (
                None
                if target_revision == "missing"
                else connector.read_bytes(target_uri)
            )
        living_artifact_text = (
            None if target_raw is None else target_raw.decode("utf-8")
        )
        prepared = atlas_source.prepare_promotion(
            docs,
            staged_artifact_text=staged_text,
            worker=worker,
            living_artifact_text=living_artifact_text,
        )
    except (
        FileNotFoundError,
        KeyError,
        TypeError,
        ValueError,
        UnicodeDecodeError,
        atlas_cli.JsonInputError,
    ) as exc:
        raise Failure(
            "SOURCE_PROMOTION_PREFLIGHT_INVALID",
            "event_record.promotion",
            str(exc),
        ) from exc
    if prepared["state"] != "prepared":
        raise Failure(
            "SOURCE_PROMOTION_PREFLIGHT_INVALID",
            "event_record.promotion",
            "frozen promotion pair is not valid for current state",
        )
    expected_projection: dict[str, bytes] = {}
    artifact_text = prepared["artifact_text"]
    if living_artifact_text is None or artifact_text != living_artifact_text:
        expected_projection[target_path] = artifact_text.encode("utf-8")
    for name, uri in (
        ("relations", RELATIONS),
        ("topics", TOPICS),
        ("manifest", MANIFEST),
    ):
        replacement = prepared["documents"].get(name)
        if replacement is not None and replacement != docs[name]:
            expected_projection[_relative(uri)] = replacement.encode("utf-8")
    actual_projection = {target.path: target.output_bytes for target in targets}
    if actual_projection != expected_projection:
        raise Failure(
            "SOURCE_PROMOTION_PROJECTION_MISMATCH",
            "targets",
            "promotion targets do not equal the frozen staged projection",
        )


def _plan(
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
    attempt: int = 0,
    predecessor: str | None = None,
) -> atlas_transaction.TransactionPlan:
    provisional = atlas_transaction.build_transaction_plan(
        event_path="pending/event.json",
        event_record=record,
        targets=targets,
        target_allowlist=_target_allowed,
        target_rank=_rank,
        identity_binding=_identity_binding,
        attempt=attempt,
        predecessor_sha256=predecessor,
    )
    return atlas_transaction.build_transaction_plan(
        event_path=f"{TRANSACTION_ROOT}/{provisional.transaction_id}/event.json",
        event_record=record,
        targets=targets,
        target_allowlist=_target_allowed,
        target_rank=_rank,
        identity_binding=_identity_binding,
        attempt=attempt,
        predecessor_sha256=predecessor,
    )


def _base(plan: atlas_transaction.TransactionPlan) -> str:
    return f"{plan.transaction_root.rstrip('/')}/{plan.transaction_id}"


def _receipt(
    connector: Any,
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
    status: str,
    *,
    historical: bool = False,
) -> dict[str, Any]:
    terminal = port.read_record(f"{_base(plan)}/{status}.json")
    if terminal is None:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(_base(plan)),
            "terminal record is missing",
        )
    target_revisions: dict[str, str] = {}
    for target in plan.targets:
        uri = _logical(target.path)
        if status == "applied":
            target_revisions[uri] = "sha256:" + atlas_transaction.sha256(
                target.output_bytes
            )
        elif historical:
            target_revisions[uri] = (
                "missing"
                if target.input_bytes is None
                else "sha256:" + atlas_transaction.sha256(target.input_bytes)
            )
        else:
            target_revisions[uri] = connector.revision(uri)
    return {
        "transaction_id": plan.transaction_id,
        "base_transaction_id": plan.base_transaction_id,
        "attempt": plan.attempt,
        "predecessor_sha256": plan.predecessor_sha256,
        "status": status,
        "targets": [target.intent_value() for target in plan.targets],
        "sha256": atlas_transaction.sha256(terminal),
        "target_revisions": target_revisions,
    }


def _tx_result(
    connector: Any,
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
    status: str,
    *,
    historical: bool = False,
    record_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    base = _base(plan)
    names = [
        "prepared.json",
        *(f"backups/{index:06d}.json" for index, _ in enumerate(plan.targets)),
        *(f"progress/{index:06d}.json" for index, _ in enumerate(plan.targets)),
        f"{status}.json",
    ]
    present = set(record_names or ())
    return {
        "event_uri": _logical(f"{base}/event.json"),
        "intent_uri": _logical(f"{base}/intent.json"),
        "phase_uris": [
            _logical(f"{base}/{name}")
            for name in names
            if name in present
            or (not historical and port.read_record(f"{base}/{name}") is not None)
        ],
        "receipt": _receipt(
            connector,
            port,
            plan,
            status,
            historical=historical,
        ),
    }


def _source_post_validator(
    connector: Any,
    record: Mapping[str, Any],
) -> atlas_transaction.PostValidator | None:
    event = record.get("event")
    if not isinstance(event, Mapping) or event.get("type") not in {
        "source-upsert",
        "route-upsert",
    }:
        return None

    def validate(
        _port: atlas_transaction.ConnectorPort,
        _plan: atlas_transaction.TransactionPlan,
    ) -> None:
        documents = {
            "manifest": connector.read_text(MANIFEST),
            "topics": connector.read_text(TOPICS),
            "relations": connector.read_text(RELATIONS),
            "vocab": connector.read_text(VOCAB),
        }
        findings = atlas_state.validate_documents(
            documents["manifest"],
            documents["topics"],
            documents["relations"],
            vocab_text=documents["vocab"],
        )
        if findings:
            first = findings[0]
            raise atlas_transaction.TransactionError(
                f"{first.code}: {first.path}: {first.detail or first.row or ''}"
            )
        rows, row_findings = atlas_state.validated_manifest_rows(documents["manifest"])
        if row_findings:
            raise atlas_transaction.TransactionError(
                "source manifest failed post-validation"
            )
        source_id = event.get("source_id")
        row = next(
            (item for item in rows if item["Source ID"] == source_id),
            None,
        )
        if row is None or row["Status"] != "active":
            raise atlas_transaction.TransactionError(
                "source row is absent or inactive after transaction"
            )
        artifact_uri = _logical(row["Artifact"])
        try:
            artifact = atlas_source.parse_artifact(
                connector.read_text(artifact_uri)
            ).values
            identity = {
                "source_id": atlas_source.scalar(artifact, "source_id"),
                "canonical_url": atlas_source.scalar(artifact, "canonical_url"),
                "content_hash": atlas_source.scalar(artifact, "content_hash"),
                "route_status": atlas_source.scalar(artifact, "routing_status"),
            }
            taxonomy = {
                "source_kind": atlas_source.scalar(artifact, "source_kind"),
                "primary_domain": atlas_source.scalar(artifact, "primary_domain"),
                "secondary_domains": json.loads(artifact["secondary_domains"]),
                "subdomains": json.loads(artifact["subdomains"]),
                "canonical_tags": json.loads(artifact["canonical_tags"]),
            }
        except (FileNotFoundError, KeyError, TypeError, ValueError) as exc:
            raise atlas_transaction.TransactionError(
                "source artifact failed post-validation"
            ) from exc
        expected_identity = {
            "source_id": row["Source ID"],
            "canonical_url": row["Canonical URL"],
            "content_hash": row["Content hash"],
            "route_status": row["Route status"],
        }
        if identity != expected_identity:
            raise atlas_transaction.TransactionError(
                "source manifest and artifact differ after transaction"
            )
        taxonomy_findings = atlas_state.validate_source_taxonomy(
            documents["vocab"],
            **taxonomy,
            path=row["Artifact"],
        )
        if taxonomy_findings:
            raise atlas_transaction.TransactionError(
                "source taxonomy failed post-validation"
            )

    return validate


def _source_transaction_event_validator(
    value: Mapping[str, Any],
    event_path: str,
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> Mapping[str, Any]:
    try:
        return _event(value)
    except Failure as exc:
        raise atlas_transaction.TransactionRecordError(event_path, exc.detail) from exc


def _source_transaction_policy() -> atlas_transaction.TransactionPolicy:
    return atlas_transaction.TransactionPolicy(
        owner_id="atlas-source-route-v1",
        target_allowlist=_target_allowed,
        target_rank=_rank,
        identity_binding=_identity_binding,
        event_validator=_source_transaction_event_validator,
        terminal_statuses=(
            "applied",
            "no-op",
            "aborted",
            "rolled-back",
            "manual-conflict",
        ),
    )


def _load_plan(
    port: _Port, transaction_id: str
) -> tuple[dict[str, Any], atlas_transaction.TransactionPlan]:
    try:
        journal = atlas_transaction.load_transaction(
            port,
            transaction_id,
            _source_transaction_policy(),
        )
    except atlas_transaction.TransactionRecordError as exc:
        raise _record_failure(exc) from exc
    except FileNotFoundError as exc:
        raise Failure(
            "TRANSACTION_UNKNOWN", "transaction_id", "transaction event is missing"
        ) from exc
    except atlas_transaction.TransactionError as exc:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(f"{TRANSACTION_ROOT}/{transaction_id}/event.json"),
            str(exc),
        ) from exc
    return dict(journal.record), journal.plan


def _tx_execute(connector: Any, args: Any) -> dict[str, Any]:
    raw_args = _object(args, "args")
    if set(raw_args) == {"version", "event"}:
        return _repair_execute(connector, raw_args)
    value = _args(raw_args, {"event_record", "targets"}, "transaction.execute")
    record = _event(value["event_record"])
    pending, expected = _targets(value["targets"])
    _mutations(connector)
    with connector.mutation_session():
        targets = _bind(connector, pending, expected)
        _source_guard(connector, record, targets)
        _promotion_guard(connector, record, targets)
        _route_guard(connector, record, targets)
        _repair_guard(connector, record, targets)
        try:
            plan = _plan(record, targets)
        except atlas_transaction.TransactionError as exc:
            raise Failure("TRANSACTION_INVALID", "targets", str(exc)) from exc
        port = _Port(connector)
        try:
            atlas_transaction.store_event(
                port,
                TRANSACTION_ROOT,
                record,
                plan,
            )
        except atlas_transaction.TransactionRecordError as exc:
            raise _record_failure(exc) from exc
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "TRANSACTION_EVENT_COLLISION",
                _logical(f"{_base(plan)}/event.json"),
                "immutable event differs",
            ) from exc
        try:
            status = atlas_transaction.execute_transaction(
                port,
                TRANSACTION_ROOT,
                plan,
                target_allowlist=_target_allowed,
                target_rank=_rank,
                post_validator=_source_post_validator(connector, record),
            )
        except atlas_transaction.TransactionTargetConflict as exc:
            raise Failure(
                "MANUAL_CONFLICT",
                _record_path(exc.path),
                exc.detail,
            ) from exc
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "TRANSACTION_INVALID", _logical(_base(plan)), str(exc)
            ) from exc
        result = _tx_result(connector, port, plan, status)
        if status == "manual-conflict":
            raise Failure(
                "MANUAL_CONFLICT", result["intent_uri"], "transaction inputs drifted"
            )
        if status not in {"applied", "no-op"}:
            raise Failure(
                "TRANSACTION_RECOVERABLE",
                result["intent_uri"],
                f"transaction reached {status}",
            )
        return result


def _tx_recover(connector: Any, args: Any) -> dict[str, Any]:
    raw_args = _object(args, "args")
    if set(raw_args) == {"version", "transaction_id", "request"}:
        return _repair_recover(connector, raw_args)
    value = _args(raw_args, {"transaction_id"}, "transaction.recover")
    transaction_id = _text(value["transaction_id"], "transaction_id")
    if _TX_ID.fullmatch(transaction_id) is None:
        raise Failure(
            "TRANSACTION_UNKNOWN", "transaction_id", "transaction ID is invalid"
        )
    _mutations(connector)
    with connector.mutation_session():
        port = _Port(connector)
        record, plan = _load_plan(port, transaction_id)
        journal = atlas_transaction.load_transaction(
            port,
            transaction_id,
            _source_transaction_policy(),
        )
        if journal.status == "manual-conflict":
            raise Failure(
                "MANUAL_CONFLICT",
                _logical(f"{_base(plan)}/intent.json"),
                "transaction requires manual reconciliation",
            )
        if journal.status is not None:
            result = _tx_result(
                connector,
                port,
                plan,
                journal.status,
                historical=True,
                record_names=journal.record_names,
            )
            return {"receipt": result["receipt"]}
        try:
            status = atlas_transaction.recover_transaction(
                port,
                plan.transaction_root,
                plan,
                target_allowlist=_target_allowed,
                target_rank=_rank,
                post_validator=_source_post_validator(connector, record),
            )
        except atlas_transaction.TransactionTargetConflict as exc:
            raise Failure(
                "MANUAL_CONFLICT",
                _record_path(exc.path),
                exc.detail,
            ) from exc
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "TRANSACTION_RECORD_INVALID", _logical(_base(plan)), str(exc)
            ) from exc
        result = _tx_result(connector, port, plan, status)
        if status == "manual-conflict":
            raise Failure(
                "MANUAL_CONFLICT",
                result["intent_uri"],
                "transaction requires manual reconciliation",
            )
        return {"receipt": result["receipt"]}


def _tx_successor(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"transaction_id"}, "transaction.successor")
    transaction_id = _text(value["transaction_id"], "transaction_id")
    if _TX_ID.fullmatch(transaction_id) is None:
        raise Failure(
            "TRANSACTION_UNKNOWN", "transaction_id", "transaction ID is invalid"
        )
    _mutations(connector)
    with connector.mutation_session():
        port = _Port(connector)
        record, predecessor = _load_plan(port, transaction_id)
        if record["event"].get("type") in {
            "repair-table-placement",
            "repair-relation-notes",
        }:
            raise Failure(
                "SUCCESSOR_TERMINAL_INELIGIBLE",
                "transaction_id",
                "repair transactions do not permit forward successors",
            )
        journal = atlas_transaction.load_transaction(
            port,
            transaction_id,
            _source_transaction_policy(),
        )
        if journal.status not in {"aborted", "rolled-back"}:
            raise Failure(
                "SUCCESSOR_TERMINAL_INELIGIBLE",
                "transaction_id",
                "only attempt-zero aborted or rolled-back transactions are eligible",
            )
        _source_guard(connector, record, predecessor.targets)
        _promotion_guard(connector, record, predecessor.targets)
        _route_guard(connector, record, predecessor.targets)
        successor_id = (
            f"{predecessor.base_transaction_id}-a{predecessor.attempt + 1:06d}"
        )
        try:
            plan = atlas_transaction.build_successor_plan(
                predecessor,
                event_path=f"{predecessor.transaction_root}/{successor_id}/event.json",
                event_record=record,
                terminal_record=journal.terminal or b"",
                target_allowlist=_target_allowed,
                target_rank=_rank,
                identity_binding=_identity_binding,
            )
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "SUCCESSOR_TERMINAL_INELIGIBLE", "transaction_id", str(exc)
            ) from exc
        try:
            atlas_transaction.store_event(
                port,
                predecessor.transaction_root,
                record,
                plan,
            )
        except atlas_transaction.TransactionRecordError as exc:
            raise _record_failure(exc) from exc
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "TRANSACTION_EVENT_COLLISION",
                _logical(f"{_base(plan)}/event.json"),
                "immutable event differs",
            ) from exc
        status = atlas_transaction.execute_transaction(
            port,
            plan.transaction_root,
            plan,
            target_allowlist=_target_allowed,
            target_rank=_rank,
            post_validator=_source_post_validator(connector, record),
        )
        result = _tx_result(connector, port, plan, status)
        if status == "manual-conflict":
            raise Failure(
                "MANUAL_CONFLICT", result["intent_uri"], "successor inputs drifted"
            )
        if status not in {"applied", "no-op"}:
            raise Failure(
                "TRANSACTION_RECOVERABLE",
                result["intent_uri"],
                f"successor reached {status}",
            )
        return result


def _index_paths(request: Mapping[str, Any]) -> dict[str, str] | None:
    domain = request.get("domain")
    subdomain = request.get("subdomain")
    topic_id = request.get("topic_id")
    if not all(
        isinstance(value, str) and atlas_index.TOPIC_ID_RE.fullmatch(value) is not None
        for value in (domain, subdomain, topic_id)
    ):
        return None
    topic = f"{ROOT}summaries/research/{domain}/{subdomain}/topics/{topic_id}/INDEX.md"
    if request.get("topic_path") != topic:
        return None
    return {
        "vocab": VOCAB,
        "topic": topic,
        "subdomain": (f"{ROOT}summaries/research/{domain}/{subdomain}/INDEX.md"),
        "registry": TOPICS,
    }


def _index_safe_namespace(request: Any) -> str | None:
    """Derive a journal namespace only from a safe topic identity tuple."""
    if type(request) is not dict:
        return None
    domain = request.get("domain")
    subdomain = request.get("subdomain")
    topic_id = request.get("topic_id")
    if not all(
        isinstance(value, str) and atlas_index.TOPIC_ID_RE.fullmatch(value) is not None
        for value in (domain, subdomain, topic_id)
    ):
        return None
    topic_path = (
        f"{ROOT}summaries/research/{domain}/{subdomain}/topics/{topic_id}/INDEX.md"
    )
    try:
        return atlas_index.topic_namespace_sha256(
            {"topic_id": topic_id, "topic_path": topic_path}
        )
    except (TypeError, ValueError, UnicodeError):
        return None


def _index_read_snapshot(
    connector: Any,
    uri: str,
    *,
    code: str,
    missing: bool = False,
) -> tuple[bytes | None, str | None]:
    try:
        raw = connector.read_bytes(uri)
    except FileNotFoundError:
        if missing:
            return None, None
        raise Failure(code, uri, "logical snapshot is missing")
    except (
        ConnectorBindingError,
        ConnectorConflictError,
        ConnectorIOError,
        ConnectorDurabilityError,
    ):
        raise
    except ValueError as exc:
        raise Failure(code, uri, str(exc)) from exc
    try:
        return raw, raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Failure(code, uri, "logical snapshot is not valid UTF-8") from exc


def _index_prepare(
    connector: Any,
    request: Mapping[str, Any],
) -> tuple[dict[str, str], atlas_index.TopicConfirmation | atlas_index.TopicPlan]:
    paths = _index_paths(request)
    if paths is None:
        result = atlas_index.prepare_topic(
            request,
            "",
            "",
            "",
            "",
            "",
            atlas_index.MISSING,
        )
        if isinstance(result, (atlas_index.TopicConfirmation, atlas_index.TopicPlan)):
            raise Failure(
                "OWNER_OUTPUT_INVALID",
                "index.create_topic",
                "invalid request did not produce findings",
            )
        _reject(result)
        raise AssertionError("unreachable")
    manifest_raw, manifest_text = _index_read_snapshot(
        connector, MANIFEST, code="REGISTRY_INVALID"
    )
    topics_raw, topics_text = _index_read_snapshot(
        connector, TOPICS, code="REGISTRY_INVALID"
    )
    relations_raw, relations_text = _index_read_snapshot(
        connector, RELATIONS, code="REGISTRY_INVALID"
    )
    vocab_raw, vocab_text = _index_read_snapshot(
        connector, VOCAB, code="REGISTRY_INVALID"
    )
    subdomain_raw, subdomain_text = _index_read_snapshot(
        connector, paths["subdomain"], code="SUBDOMAIN_INVALID", missing=True
    )
    topic_raw, topic_text = _index_read_snapshot(
        connector, paths["topic"], code="TOPIC_COMPATIBILITY_CONFLICT", missing=True
    )
    assert (
        manifest_raw is not None
        and topics_raw is not None
        and relations_raw is not None
        and vocab_raw is not None
        and manifest_text is not None
        and topics_text is not None
        and relations_text is not None
        and vocab_text is not None
    )
    result = atlas_index.prepare_topic(
        request,
        manifest_text,
        topics_text,
        relations_text,
        vocab_text,
        subdomain_text if subdomain_raw is not None else atlas_index.MISSING,
        topic_text,
    )
    if isinstance(result, (atlas_index.TopicConfirmation, atlas_index.TopicPlan)):
        return paths, result
    _reject(result)
    raise AssertionError("unreachable")


def _index_rank(path: str) -> tuple[int, str]:
    if path == atlas_state.VOCAB_PATH:
        return 0, path
    if _INDEX_TOPIC_RELATIVE.fullmatch(path):
        return 1, path
    if _INDEX_SUBDOMAIN_RELATIVE.fullmatch(path):
        return 2, path
    if path == atlas_state.TOPICS_PATH:
        return 3, path
    raise atlas_transaction.TransactionError(
        "topic target is outside the approved write set"
    )


def _index_target_allowed(path: str) -> bool:
    try:
        _index_rank(path)
    except atlas_transaction.TransactionError:
        return False
    return True


def _index_identity(
    record: Mapping[str, Any],
    event_hash: str,
) -> atlas_transaction.TransactionIdentity:
    request = record["request"]
    return atlas_transaction.TransactionIdentity(
        base={
            "owner": atlas_index.TOPIC_OWNER_ID,
            "topic_namespace_sha256": record["topic_namespace_sha256"],
            "request_sha256": record["request_sha256"],
            "topic_id": request["topic_id"],
            "topic_path": request["topic_path"],
        },
        intent={
            "owner": atlas_index.TOPIC_OWNER_ID,
            "event_type": record["event_type"],
            "topic_namespace_sha256": record["topic_namespace_sha256"],
            "request_sha256": record["request_sha256"],
            "request": request,
        },
    )


def _index_base_formula(
    event: Mapping[str, Any],
    event_hash: str,
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> Mapping[str, Any]:
    logical_targets = tuple(
        atlas_index.TopicTarget(
            _logical(target.path),
            target.input_bytes,
            target.output_bytes,
        )
        for target in targets
    )
    return atlas_index.topic_base_identity(event, event_hash, logical_targets)


def _index_plan(
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
    attempt: int = 0,
    predecessor: str | None = None,
) -> atlas_transaction.TransactionPlan:
    try:
        namespace = record.get("topic_namespace_sha256")
        if not isinstance(namespace, str):
            raise atlas_transaction.TransactionError("topic namespace is missing")
        transaction_root = f"{TRANSACTION_ROOT}/topics/{namespace}"
        provisional = atlas_transaction.build_transaction_plan(
            event_path="pending/event.json",
            event_record=record,
            targets=targets,
            target_allowlist=_index_target_allowed,
            target_rank=_index_rank,
            identity_binding=_index_identity,
            base_formula=_index_base_formula,
            transaction_root=transaction_root,
            attempt=attempt,
            predecessor_sha256=predecessor,
        )
        return atlas_transaction.build_transaction_plan(
            event_path=f"{transaction_root}/{provisional.transaction_id}/event.json",
            event_record=record,
            targets=targets,
            target_allowlist=_index_target_allowed,
            target_rank=_index_rank,
            identity_binding=_index_identity,
            base_formula=_index_base_formula,
            transaction_root=transaction_root,
            attempt=attempt,
            predecessor_sha256=predecessor,
        )
    except atlas_transaction.TransactionError as exc:
        raise Failure("TRANSACTION_INVALID", "targets", str(exc)) from exc


def _target_input_revision(
    target: atlas_transaction.TransactionTarget,
) -> str:
    if target.input_bytes is None:
        return "missing"
    return "sha256:" + atlas_transaction.sha256(target.input_bytes)


def _index_bind(
    connector: Any,
    targets: Sequence[atlas_index.TopicTarget],
) -> tuple[tuple[atlas_transaction.TransactionTarget, ...], dict[str, str]]:
    bound: list[atlas_transaction.TransactionTarget] = []
    revisions: dict[str, str] = {}
    for target in targets:
        uri = target.path
        revision = connector.revision(uri)
        input_bytes = target.input_bytes
        expected = (
            "missing"
            if input_bytes is None
            else "sha256:" + atlas_transaction.sha256(input_bytes)
        )
        if revision != expected:
            raise Failure(
                "REVISION_STALE",
                uri,
                "target revision changed before authorization",
            )
        if target.input_bytes is None:
            input_bytes = None
        else:
            try:
                input_bytes = connector.read_bytes(uri)
            except FileNotFoundError as exc:
                raise Failure(
                    "REVISION_STALE",
                    uri,
                    "target disappeared during authorization",
                ) from exc
            if input_bytes != target.input_bytes:
                raise Failure(
                    "REVISION_STALE",
                    uri,
                    "target bytes changed before authorization",
                )
        path = _relative(uri)
        bound.append(
            atlas_transaction.TransactionTarget(
                path,
                input_bytes,
                target.output_bytes,
            )
        )
        revisions[uri] = revision
    return tuple(bound), revisions


def _index_post_validator(
    connector: Any,
    owner_post: atlas_index.TopicPostValidation,
) -> atlas_transaction.PostValidator:
    del connector

    def validate(
        port: atlas_transaction.ConnectorPort,
        plan: atlas_transaction.TransactionPlan,
    ) -> Mapping[str, Any]:
        def read_text(path: str) -> str:
            try:
                raw = port.read(path)
            except atlas_transaction.TransactionError:
                raise
            except (ConnectorBindingError, ConnectorIOError, ConnectorDurabilityError):
                raise
            except (TypeError, ValueError, UnicodeError) as exc:
                raise atlas_transaction.TransactionError(
                    f"post-validation target cannot be read: {path}"
                ) from exc
            if raw is None:
                raise _IndexPostValidationError(
                    f"post-validation target is missing: {path}"
                )
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise _IndexPostValidationError(
                    f"post-validation target is not UTF-8: {path}"
                ) from exc

        try:
            roles = atlas_index.topic_target_roles(
                owner_post.request,
                [_logical(target.path) for target in plan.targets],
            )
            manifest_text = read_text(atlas_state.MANIFEST_PATH)
            topics_text = read_text(atlas_state.TOPICS_PATH)
            relations_text = read_text(atlas_state.RELATIONS_PATH)
            if owner_post.request["version"] == atlas_index.VERSION:
                vocab_text = None
                registry_findings = atlas_state.validate_documents(
                    manifest_text,
                    topics_text,
                    relations_text,
                )
            else:
                vocab_text = read_text(atlas_state.VOCAB_PATH)
                registry_findings = atlas_state.validate_documents(
                    manifest_text,
                    topics_text,
                    relations_text,
                    vocab_text=vocab_text,
                )
            subdomain_text = read_text(_relative(roles["subdomain"]))
            topic_text = read_text(_relative(roles["topic"]))
            if registry_findings:
                raise _IndexPostValidationError("complete registry validation failed")
            findings = owner_post.validate(
                manifest_text,
                topics_text,
                relations_text,
                vocab_text,
                subdomain_text,
                topic_text,
            )
            if findings:
                raise _IndexPostValidationError("owner post-validation failed")
            return {
                "owner": atlas_index.TOPIC_OWNER_ID,
                "policy": "topic-post-v1",
                "request_sha256": plan.intent["request_sha256"],
                "target_output_sha256s": [
                    atlas_transaction.sha256(target.output_bytes)
                    for target in plan.targets
                ],
            }
        except atlas_transaction.TransactionError:
            raise
        except (ConnectorBindingError, ConnectorIOError, ConnectorDurabilityError):
            raise
        except (TypeError, ValueError, UnicodeError) as exc:
            raise _IndexPostValidationError("owner post-validation failed") from exc

    return validate


def _index_terminal_record(
    status: str,
    event_record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
) -> bytes:
    if status == "aborted":
        return atlas_transaction.canonical_json(
            {
                "version": atlas_transaction.VERSION,
                "status": "aborted",
                "event_sha256": atlas_transaction.sha256(
                    atlas_transaction.canonical_json(event_record)
                ),
                "owner": atlas_index.TOPIC_OWNER_ID,
            }
        )
    return atlas_transaction._terminal_record(
        status,
        atlas_transaction.sha256(atlas_transaction.canonical_json(plan.intent)),
    )


def _index_terminal_validator(
    status: str,
    record: Mapping[str, Any],
    terminal: bytes,
    plan: atlas_transaction.TransactionPlan,
) -> None:
    try:
        value = atlas_transaction._decode_record(
            terminal, f"{_base(plan)}/{status}.json"
        )
        canonical_value = atlas_transaction.canonical_json(value)
    except atlas_transaction.TransactionRecordError:
        raise
    except (TypeError, ValueError, UnicodeError) as exc:
        raise atlas_transaction.TransactionRecordError(
            f"{_base(plan)}/{status}.json", "terminal record is malformed"
        ) from exc
    if (
        status == "aborted"
        and type(value) is dict
        and set(value) == {"version", "status", "event_sha256", "owner"}
        and value.get("version") == atlas_transaction.VERSION
        and value.get("status") == "aborted"
        and value.get("owner") == atlas_index.TOPIC_OWNER_ID
        and value.get("event_sha256")
        == atlas_transaction.sha256(atlas_transaction.canonical_json(record))
        and canonical_value == terminal
    ):
        return
    if status != "applied":
        expected = atlas_transaction._terminal_record(
            status,
            atlas_transaction.sha256(atlas_transaction.canonical_json(plan.intent)),
        )
        if terminal == expected:
            return
        raise atlas_transaction.TransactionRecordError(
            f"{_base(plan)}/{status}.json", "terminal record is malformed"
        )
    expected_proof = {
        "owner": atlas_index.TOPIC_OWNER_ID,
        "policy": "topic-post-v1",
        "request_sha256": plan.intent["request_sha256"],
        "target_output_sha256s": [
            atlas_transaction.sha256(target.output_bytes) for target in plan.targets
        ],
    }
    if (
        type(value) is not dict
        or set(value) != {"version", "status", "intent_sha256", "owner_proof"}
        or value.get("version") != atlas_transaction.VERSION
        or value.get("status") != "applied"
        or value.get("intent_sha256")
        != atlas_transaction.sha256(atlas_transaction.canonical_json(plan.intent))
        or value.get("owner_proof") != expected_proof
        or canonical_value != terminal
    ):
        raise atlas_transaction.TransactionRecordError(
            f"{_base(plan)}/applied.json", "topic owner proof is malformed"
        )


def _index_journal(
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
) -> atlas_transaction.Journal:
    namespace = plan.intent.get("topic_namespace_sha256")
    if not isinstance(namespace, str):
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(f"{_base(plan)}/event.json"),
            "topic namespace is missing",
        )
    try:
        return atlas_transaction.load_transaction(
            port,
            plan.transaction_id,
            _index_transaction_policy(namespace),
        )
    except atlas_transaction.TransactionRecordError as exc:
        raise _record_failure(exc) from exc


def _index_verify_records(
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
) -> tuple[str | None, bytes | None, bool]:
    journal = _index_journal(port, plan)
    return journal.status, journal.terminal, journal.prepared is not None


def _index_classifications(
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for target in plan.targets:
        try:
            current = port.read(target.path)
        except ConnectorBindingError:
            raise
        except ConnectorConflictError as exc:
            raise Failure(
                "MANUAL_CONFLICT",
                _logical(target.path),
                "target cannot be safely classified",
            ) from exc
        except (ConnectorIOError, ConnectorDurabilityError):
            raise
        except ValueError as exc:
            raise Failure(
                "BINDING_INVALID",
                "connector",
                "connector target classification failed",
            ) from exc
        if current == target.output_bytes:
            result[target.path] = "output"
        elif current == target.input_bytes:
            result[target.path] = "input"
        else:
            result[target.path] = "other"
    return result


def _index_successor_id(plan: atlas_transaction.TransactionPlan) -> str:
    if plan.attempt != 0:
        raise Failure(
            "SUCCESSOR_TERMINAL_INELIGIBLE",
            "transaction_id",
            "only attempt zero may have a successor",
        )
    return f"{plan.base_transaction_id}-a000001"


def _index_successor_exists(
    port: _Port,
    record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
) -> bool:
    if plan.attempt != 0:
        return False
    namespace = plan.intent["topic_namespace_sha256"]
    successor_id = _index_successor_id(plan)
    successor_path = f"{plan.transaction_root}/{successor_id}/event.json"
    if port.read_record(successor_path) is None:
        return False
    successor_record, successor_plan = _index_load_plan(port, successor_id, namespace)
    if successor_record != record or successor_plan.targets != plan.targets:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(successor_path),
            "successor event does not match immutable predecessor",
        )
    return True


def _index_successor_is_executable(
    journal: atlas_transaction.Journal,
    journals: Sequence[atlas_transaction.Journal],
    candidate: atlas_transaction.TransactionPlan,
) -> bool:
    if journal.plan.attempt != 0 or journal.status not in {"aborted", "rolled-back"}:
        return False
    successor_id = _index_successor_id(journal.plan)
    if any(item.plan.transaction_id == successor_id for item in journals):
        return False
    return tuple(
        (target.path, target.input_bytes) for target in journal.plan.targets
    ) == tuple((target.path, target.input_bytes) for target in candidate.targets)


def _index_namespace_journals(
    port: _Port,
    namespace: str,
) -> tuple[atlas_transaction.Journal, ...]:
    root = f"{TRANSACTION_ROOT}/topics/{namespace}"
    try:
        names = port.list(root)
    except atlas_transaction.TransactionRecordError as exc:
        raise _record_failure(exc) from exc
    except OSError as exc:
        raise _IndexJournalProbeError(None, root) from exc
    ids: set[str] = set()
    for name in names:
        parts = name.split("/")
        transaction_id = parts[0] if parts else ""
        if (
            len(parts) < 2
            or _TX_ID.fullmatch(transaction_id) is None
            or not transaction_id.endswith(("-a000000", "-a000001"))
        ):
            raise Failure(
                "TRANSACTION_RECORD_INVALID",
                _logical(f"{root}/{name}"),
                "topic transaction namespace path is invalid",
            )
        ids.add(transaction_id)
    policy = _index_transaction_policy(namespace)
    journals: list[atlas_transaction.Journal] = []
    for transaction_id in sorted(ids):
        try:
            journals.append(
                atlas_transaction.load_transaction(port, transaction_id, policy)
            )
        except atlas_transaction.TransactionRecordError as exc:
            raise _record_failure(exc) from exc
        except OSError as exc:
            raise _IndexJournalProbeError(transaction_id, str(exc)) from exc
    return tuple(journals)


def _index_binding_event(
    record: Mapping[str, Any],
    targets: Sequence[atlas_transaction.TransactionTarget],
    *,
    attempt: int = 0,
    predecessor_sha256: str | None = None,
) -> dict[str, Any]:
    """Adapt transaction-owned bytes for the pure index binding owner."""

    return {
        "event_record": dict(record),
        "attempt": attempt,
        "predecessor_sha256": predecessor_sha256,
        "targets": [
            {
                "path": target.path,
                "input_bytes": target.input_bytes,
                "output_bytes": target.output_bytes,
            }
            for target in targets
        ],
    }


def _index_transaction_event_validator(
    value: Mapping[str, Any],
    event_path: str,
    targets: Sequence[atlas_transaction.TransactionTarget],
) -> Mapping[str, Any]:
    binding = atlas_index.load_topic_binding(
        _index_binding_event(value, targets),
        atlas_index.MISSING,
    )
    if not isinstance(binding, atlas_index.TopicTransactionBinding):
        raise atlas_transaction.TransactionRecordError(
            event_path,
            "topic owner binding is invalid",
        )
    return dict(value)


def _index_transaction_policy(
    namespace: str | None = None,
) -> atlas_transaction.TransactionPolicy:
    root = (
        TRANSACTION_ROOT
        if namespace is None
        else f"{TRANSACTION_ROOT}/topics/{namespace}"
    )
    return atlas_transaction.TransactionPolicy(
        owner_id=atlas_index.TOPIC_OWNER_ID,
        target_allowlist=_index_target_allowed,
        target_rank=_index_rank,
        identity_binding=_index_identity,
        base_formula=_index_base_formula,
        event_validator=_index_transaction_event_validator,
        transaction_root=root,
        terminal_statuses=tuple(_INDEX_TERMINALS),
        terminal_validator=_index_terminal_validator,
    )


def _index_load_current_plan(
    port: _Port,
    transaction_id: str,
    namespace: str | None = None,
) -> tuple[dict[str, Any], atlas_transaction.TransactionPlan]:
    try:
        journal = atlas_transaction.load_transaction(
            port,
            transaction_id,
            _index_transaction_policy(namespace),
        )
    except atlas_transaction.TransactionRecordError as exc:
        raise _record_failure(exc) from exc
    except atlas_transaction.TransactionError as exc:
        raise Failure(
            "IO_FAILURE",
            _logical(
                f"{TRANSACTION_ROOT}/topics/{namespace}/{transaction_id}/event.json"
                if namespace is not None
                else f"{TRANSACTION_ROOT}/{transaction_id}/event.json"
            ),
            str(exc),
        ) from exc
    return dict(journal.record), journal.plan


def _index_load_plan(
    port: _Port,
    transaction_id: str,
    namespace: str | None = None,
) -> tuple[dict[str, Any], atlas_transaction.TransactionPlan]:
    return _index_load_current_plan(port, transaction_id, namespace)


def _index_verify_current_intent(
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
) -> None:
    intent_path = f"{_base(plan)}/intent.json"
    try:
        intent_raw = port.read_record(intent_path)
    except atlas_transaction.TransactionRecordError as exc:
        raise _record_failure(exc) from exc
    except atlas_transaction.TransactionError as exc:
        raise Failure("IO_FAILURE", "index.recover_topic", str(exc)) from exc
    if intent_raw != atlas_transaction.canonical_json(plan.intent):
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(intent_path),
            "transaction intent is missing or does not match",
        )


def _index_receipt(
    connector: Any,
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
    status: str,
    input_revisions: Mapping[str, str] | None = None,
    *,
    historical: bool = False,
) -> dict[str, Any]:
    base = _base(plan)
    terminal_path = f"{base}/{status}.json"
    terminal = port.read_record(terminal_path)
    if terminal is None:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(terminal_path),
            "terminal record is missing",
        )
    request = plan.intent["request"]
    entries: list[dict[str, Any]] = []
    target_revisions: dict[str, str] = {}
    for target in plan.targets:
        uri = _logical(target.path)
        revision = (
            input_revisions.get(uri)
            if input_revisions is not None
            else (
                "missing"
                if target.input_bytes is None
                else "sha256:" + atlas_transaction.sha256(target.input_bytes)
            )
        )
        assert revision is not None
        output_revision = "sha256:" + atlas_transaction.sha256(target.output_bytes)
        if historical:
            target_revision = output_revision if status == "applied" else revision
        else:
            target_revision = connector.revision(uri)
            if status == "applied" and target_revision != output_revision:
                raise Failure(
                    "MANUAL_CONFLICT",
                    uri,
                    "applied transaction target revision is not its recorded output",
                )
        target_revisions[uri] = target_revision
        entries.append(
            {
                "path": uri,
                "input_revision": revision,
                "input_sha256": (
                    None
                    if target.input_bytes is None
                    else atlas_transaction.sha256(target.input_bytes)
                ),
                "output_sha256": atlas_transaction.sha256(target.output_bytes),
                "output_revision": output_revision,
            }
        )
    return {
        "request_sha256": plan.intent["request_sha256"],
        "created_on": request["created_on"],
        "transaction_id": plan.transaction_id,
        "base_transaction_id": plan.base_transaction_id,
        "attempt": plan.attempt,
        "predecessor_sha256": plan.predecessor_sha256,
        "status": status,
        "targets": entries,
        "sha256": atlas_transaction.sha256(terminal),
        "target_revisions": target_revisions,
    }


def _index_transaction_result(
    connector: Any,
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
    status: str,
    input_revisions: Mapping[str, str] | None = None,
    *,
    historical: bool = False,
    record_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    base = _base(plan)
    phase_names = [
        "prepared.json",
        *(f"backups/{index:06d}.json" for index, _ in enumerate(plan.targets)),
        *(f"progress/{index:06d}.json" for index, _ in enumerate(plan.targets)),
        f"{status}.json",
    ]
    present = set(record_names or ())
    phase_uris = [
        _logical(f"{base}/{name}")
        for name in phase_names
        if name in present
        or (not historical and port.read_record(f"{base}/{name}") is not None)
    ]
    transaction = {
        "event_uri": _logical(f"{base}/event.json"),
        "intent_uri": _logical(f"{base}/intent.json"),
        "phase_uris": phase_uris,
        "terminal_uri": _logical(f"{base}/{status}.json"),
    }
    receipt = _index_receipt(
        connector,
        port,
        plan,
        status,
        input_revisions,
        historical=historical,
    )
    paths = atlas_index.topic_target_roles(
        plan.intent["request"],
        [_logical(target.path) for target in plan.targets],
    )
    targets_by_uri = {_logical(target.path): target for target in plan.targets}
    revisions: dict[str, str] = {}
    for role, path in paths.items():
        target = targets_by_uri[path]
        if status == "applied":
            revision = "sha256:" + atlas_transaction.sha256(target.output_bytes)
        elif historical:
            revision = _target_input_revision(target)
        else:
            revision = connector.revision(path)
        revisions[role] = revision
    return {
        "paths": paths,
        "revisions": revisions,
        "transaction": transaction,
        "receipt": receipt,
    }


def _index_transaction_error(
    port: _Port,
    plan: atlas_transaction.TransactionPlan,
    exc: atlas_transaction.TransactionError | OSError,
    *,
    intent_verified: bool = False,
    probe_targets: bool = True,
) -> None:
    intent_uri = _logical(f"{_base(plan)}/intent.json")
    if isinstance(exc, atlas_transaction.TransactionRecordError):
        raise _record_failure(exc) from exc
    if isinstance(exc, atlas_transaction.TransactionTargetConflict):
        raise Failure(
            "MANUAL_CONFLICT",
            _record_path(exc.path),
            exc.detail,
        ) from exc
    if intent_verified:
        try:
            status, _, _ = _index_verify_records(port, plan)
        except atlas_transaction.TransactionRecordError as record_exc:
            raise _record_failure(record_exc) from exc
        except (OSError, atlas_transaction.TransactionError):
            status = None
        if status == "manual-conflict":
            raise Failure(
                "MANUAL_CONFLICT",
                intent_uri,
                "transaction requires manual reconciliation",
            ) from exc
        classifications: Mapping[str, str] | None = None
        if probe_targets:
            try:
                classifications = _index_classifications(port, plan)
            except OSError:
                classifications = None
        conflict_path = (
            next(
                (path for path, value in classifications.items() if value == "other"),
                None,
            )
            if classifications is not None
            else None
        )
        if conflict_path is not None:
            raise Failure(
                "MANUAL_CONFLICT",
                _logical(conflict_path),
                "transaction target changed during recovery",
            ) from exc
        raise Failure(
            "TRANSACTION_RECOVERABLE",
            intent_uri,
            f"transaction {plan.transaction_id} requires exact-request recovery",
        ) from exc
    try:
        intent_raw = port.read_record(f"{_base(plan)}/intent.json")
    except atlas_transaction.TransactionRecordError as record_exc:
        raise _record_failure(record_exc) from exc
    except OSError:
        # A failed identity probe cannot establish a post-intent boundary.
        # Preserve the connector failure rather than manufacturing identity.
        raise
    if intent_raw is None:
        if isinstance(exc, OSError):
            # Event-only and other pre-intent acknowledgement loss keeps the
            # façade's existing IO_FAILURE envelope.
            raise exc
        raise Failure(
            "TRANSACTION_INVALID",
            _logical(_base(plan)),
            str(exc),
        ) from exc
    expected_intent = atlas_transaction.canonical_json(plan.intent)
    if intent_raw != expected_intent:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            intent_uri,
            "transaction intent is missing or does not match",
        ) from exc
    try:
        status, _, _ = _index_verify_records(port, plan)
    except atlas_transaction.TransactionRecordError as record_exc:
        raise _record_failure(record_exc) from exc
    except (OSError, atlas_transaction.TransactionError):
        status = None
    if status == "manual-conflict":
        raise Failure(
            "MANUAL_CONFLICT",
            intent_uri,
            "transaction requires manual reconciliation",
        ) from exc
    classifications = None
    if probe_targets:
        try:
            classifications = _index_classifications(port, plan)
        except OSError:
            classifications = None
    conflict_path = (
        next(
            (path for path, value in classifications.items() if value == "other"),
            None,
        )
        if classifications is not None
        else None
    )
    if conflict_path is not None:
        raise Failure(
            "MANUAL_CONFLICT",
            _logical(conflict_path),
            "transaction target changed during recovery",
        ) from exc
    raise Failure(
        "TRANSACTION_RECOVERABLE",
        intent_uri,
        f"transaction {plan.transaction_id} requires exact-request recovery",
    ) from exc


def _index_execute_plan(
    connector: Any,
    request: Mapping[str, Any],
    owner_plan: atlas_index.TopicPlan,
) -> dict[str, Any]:
    record = dict(owner_plan.event_record)
    namespace = record["topic_namespace_sha256"]
    port = _Port(connector)
    journals = _index_namespace_journals(port, namespace)
    bound, input_revisions = _index_bind(connector, owner_plan.targets)
    candidate = _index_plan(record, bound)
    same_request = [
        journal
        for journal in journals
        if journal.record.get("request") == record["request"]
    ]
    for journal in same_request:
        if journal.plan.targets != candidate.targets and journal.status is None:
            raise Failure(
                "TRANSACTION_RECOVERABLE",
                _logical(
                    f"{journal.plan.transaction_root}/{journal.plan.transaction_id}/intent.json"
                ),
                "event-only topic transaction no longer matches current inputs",
            )
    by_base = {
        journal.plan.base_transaction_id: journal
        for journal in journals
        if journal.plan.base_transaction_id == candidate.base_transaction_id
    }
    selected = by_base.get(candidate.base_transaction_id)
    other_journals = [
        journal
        for journal in journals
        if journal.plan.base_transaction_id != candidate.base_transaction_id
    ]
    if any(journal.status == "manual-conflict" for journal in other_journals):
        raise Failure(
            "MANUAL_CONFLICT",
            _logical(f"{TRANSACTION_ROOT}/topics/{namespace}"),
            "topic transaction namespace requires manual reconciliation",
        )
    if any(
        journal.status is None
        or journal.status == "applied"
        or _index_successor_is_executable(journal, journals, candidate)
        for journal in other_journals
    ):
        raise Failure(
            "TRANSACTION_RECOVERABLE",
            _logical(f"{TRANSACTION_ROOT}/topics/{namespace}"),
            "topic transaction namespace is not closed",
        )
    if selected is None:
        plan = candidate
    else:
        if selected.plan.targets != candidate.targets or selected.record != record:
            raise Failure(
                "TRANSACTION_RECORD_INVALID",
                _logical(
                    f"{selected.plan.transaction_root}/{selected.plan.transaction_id}/event.json"
                ),
                "immutable topic event differs from current binding",
            )
        if selected.status is None:
            if selected.record_names != ("event.json",):
                raise Failure(
                    "TRANSACTION_RECOVERABLE",
                    _logical(
                        f"{selected.plan.transaction_root}/"
                        f"{selected.plan.transaction_id}/intent.json"
                    ),
                    "topic transaction requires named recovery",
                )
            plan = selected.plan
        elif selected.status == "manual-conflict":
            raise Failure(
                "MANUAL_CONFLICT",
                _logical(
                    f"{selected.plan.transaction_root}/"
                    f"{selected.plan.transaction_id}/intent.json"
                ),
                "transaction requires manual reconciliation",
            )
        elif selected.status in {"aborted", "rolled-back"}:
            successor_id = _index_successor_id(selected.plan)
            existing_successor = next(
                (
                    journal
                    for journal in journals
                    if journal.plan.transaction_id == successor_id
                ),
                None,
            )
            if existing_successor is not None:
                if existing_successor.status is not None:
                    raise Failure(
                        "SUCCESSOR_TERMINAL_INELIGIBLE",
                        "transaction_id",
                        "only one identical successor is permitted",
                    )
                if existing_successor.record_names != ("event.json",):
                    raise Failure(
                        "TRANSACTION_RECOVERABLE",
                        _logical(
                            f"{existing_successor.plan.transaction_root}/{successor_id}/intent.json"
                        ),
                        "successor requires named recovery",
                    )
                plan = existing_successor.plan
            else:
                try:
                    plan = atlas_transaction.build_successor_plan(
                        selected.plan,
                        event_path=f"{selected.plan.transaction_root}/{successor_id}/event.json",
                        event_record=record,
                        terminal_record=selected.terminal or b"",
                        target_allowlist=_index_target_allowed,
                        target_rank=_index_rank,
                        identity_binding=_index_identity,
                        base_formula=_index_base_formula,
                        terminal_validator=lambda terminal_status, terminal, terminal_plan: (
                            _index_terminal_validator(
                                terminal_status,
                                record,
                                terminal,
                                terminal_plan,
                            )
                        ),
                    )
                except atlas_transaction.TransactionError as exc:
                    raise Failure(
                        "SUCCESSOR_TERMINAL_INELIGIBLE", "transaction_id", str(exc)
                    ) from exc
                input_revisions = {
                    _logical(target.path): _target_input_revision(target)
                    for target in plan.targets
                }
        else:
            raise Failure(
                "TRANSACTION_RECORD_INVALID",
                _logical(
                    f"{selected.plan.transaction_root}/{selected.plan.transaction_id}"
                ),
                "transaction already has a terminal state",
            )
    try:
        atlas_transaction.store_event(
            port,
            plan.transaction_root,
            record,
            plan,
        )
        status = atlas_transaction.execute_transaction(
            port,
            plan.transaction_root,
            plan,
            target_allowlist=_index_target_allowed,
            target_rank=_index_rank,
            post_validator=_index_post_validator(
                connector,
                owner_plan.post_validation,
            ),
            terminal_validator=lambda terminal_status, terminal, terminal_plan: (
                _index_terminal_validator(
                    terminal_status,
                    record,
                    terminal,
                    terminal_plan,
                )
            ),
            surface_post_intent_failure=True,
        )
        result = _index_transaction_result(
            connector,
            port,
            plan,
            status,
            input_revisions,
        )
    except (atlas_transaction.TransactionError, OSError) as exc:
        _index_transaction_error(port, plan, exc)
        raise AssertionError("unreachable")
    if status == "manual-conflict":
        raise Failure(
            "MANUAL_CONFLICT",
            result["transaction"]["intent_uri"],
            "transaction requires manual reconciliation",
        )
    if status != "applied":
        raise Failure(
            "TRANSACTION_RECOVERABLE",
            result["transaction"]["intent_uri"],
            f"transaction reached {status}; recover with the exact request",
        )
    result.update(
        {
            "state": "created",
            "validation": {"ok": True, "findings": []},
        }
    )
    return result


def _index_recovery_binding(
    record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
) -> atlas_index.TopicTransactionBinding:
    event_uri = _logical(f"{_base(plan)}/event.json")
    binding = atlas_index.load_topic_binding(
        _index_binding_event(
            record,
            plan.targets,
            attempt=plan.attempt,
            predecessor_sha256=plan.predecessor_sha256,
        ),
        plan.intent,
    )
    if not isinstance(binding, atlas_index.TopicTransactionBinding):
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            event_uri,
            "topic owner binding is invalid",
        )
    return binding


def _index_create(connector: Any, args: Any) -> dict[str, Any]:
    request = _object(args, "args")
    fields = set(atlas_index.REQUEST_FIELDS)
    if set(request) != fields:
        owner_result = atlas_index.prepare_topic(
            request,
            "",
            "",
            "",
            "",
            "",
            None,
        )
        if isinstance(
            owner_result, (atlas_index.TopicConfirmation, atlas_index.TopicPlan)
        ):
            raise Failure(
                "OWNER_OUTPUT_INVALID",
                "findings",
                "owner returned a plan for an invalid request shape",
            )
        _reject(owner_result)
        raise AssertionError("owner did not reject invalid request shape")
    normalized_request, request_findings = atlas_index._validate_request(request)
    if request_findings or normalized_request is None:
        _reject(request_findings)
        raise AssertionError("owner did not reject invalid request")
    _mutations(connector)
    with connector.mutation_session():
        try:
            namespace = atlas_index.topic_namespace_sha256(request)
        except (TypeError, ValueError, UnicodeError):
            namespace = None
        namespace_journals = (
            ()
            if namespace is None
            else _index_namespace_journals(_Port(connector), namespace)
        )
        paths, owner_result = _index_prepare(connector, request)
        if isinstance(owner_result, atlas_index.TopicConfirmation):
            for journal in namespace_journals:
                if journal.status == "manual-conflict":
                    raise Failure(
                        "MANUAL_CONFLICT",
                        _logical(
                            f"{journal.plan.transaction_root}/"
                            f"{journal.plan.transaction_id}/intent.json"
                        ),
                        "topic transaction requires manual reconciliation",
                    )
                if journal.status is None:
                    raise Failure(
                        "TRANSACTION_RECOVERABLE",
                        _logical(
                            f"{journal.plan.transaction_root}/"
                            f"{journal.plan.transaction_id}/intent.json"
                        ),
                        "topic transaction namespace is not closed",
                    )
            return {
                "state": owner_result.state,
                "paths": dict(owner_result.paths),
                "revisions": dict(owner_result.revisions),
                "transaction": None,
                "receipt": None,
                "validation": owner_result.validation.to_dict(),
            }
        return _index_execute_plan(connector, request, owner_result)


def _index_current_intent_exists(
    port: _Port,
    namespace: str,
    transaction_id: str,
) -> bool:
    return (
        port.read_record(
            f"{TRANSACTION_ROOT}/topics/{namespace}/{transaction_id}/intent.json"
        )
        is not None
    )


def _index_recover(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(
        args,
        {"version", "transaction_id", "request"},
        "index.recover_topic",
    )
    if type(value["version"]) is not int or value["version"] != VERSION:
        raise Failure(
            "INDEX_REQUEST_INVALID",
            "args.version",
            "version must be 1",
        )
    transaction_id = _text(value["transaction_id"], "args.transaction_id")
    if _TX_ID.fullmatch(transaction_id) is None:
        raise Failure(
            "TRANSACTION_UNKNOWN",
            "args.transaction_id",
            "transaction ID is invalid",
        )
    if type(value["request"]) is not dict:
        raise Failure(
            "INDEX_REQUEST_INVALID",
            "args.request",
            "request must be an object",
        )
    namespace = _index_safe_namespace(value["request"])
    if namespace is None:
        normalized_request, request_findings = atlas_index._decode_journal_request(
            value["request"]
        )
        if request_findings or normalized_request is None:
            _reject(request_findings)
            raise AssertionError("owner did not reject invalid recovery request")
        raise Failure(
            "INDEX_REQUEST_INVALID",
            "args.request",
            "request topic identity is invalid",
        )
    _mutations(connector)
    with connector.mutation_session():
        port = _Port(connector)
        recovery_phase = "namespace"
        try:
            # Validate every journal in the immutable topic namespace before
            # resolving the named transaction or touching live product targets.
            _index_namespace_journals(port, namespace)
            recovery_phase = "named-journal"
            record, plan = _index_load_current_plan(port, transaction_id, namespace)
        except OSError as exc:
            intent_uri = _logical(
                f"{TRANSACTION_ROOT}/topics/{namespace}/{transaction_id}/intent.json"
            )
            if isinstance(exc, _IndexJournalProbeError):
                failed_transaction_id = exc.failed_transaction_id
                if (
                    failed_transaction_id is not None
                    and failed_transaction_id != transaction_id
                ):
                    raise Failure(
                        "TRANSACTION_RECOVERABLE",
                        intent_uri,
                        f"transaction {transaction_id} requires exact-request recovery",
                    ) from exc
                if exc.failed_path.rstrip().endswith("/intent.json"):
                    raise Failure(
                        "IO_FAILURE",
                        "index.recover_topic",
                        "transaction identity could not be verified",
                    ) from exc
            try:
                current_intent = _index_current_intent_exists(
                    port,
                    namespace,
                    transaction_id,
                )
            except OSError as identity_exc:
                # A failed intent probe still has a durable boundary when
                # the named event is readable.  Preserve the supplied
                # transaction identity instead of downgrading to a generic
                # I/O response.
                try:
                    event_raw = port.read_record(
                        f"{TRANSACTION_ROOT}/topics/{namespace}/"
                        f"{transaction_id}/event.json"
                    )
                except OSError as event_exc:
                    raise Failure(
                        "IO_FAILURE",
                        "index.recover_topic",
                        "transaction identity could not be verified",
                    ) from event_exc
                if event_raw is not None:
                    raise Failure(
                        "TRANSACTION_RECOVERABLE",
                        intent_uri,
                        f"transaction {transaction_id} requires exact-request recovery",
                    ) from exc
                raise Failure(
                    "IO_FAILURE",
                    "index.recover_topic",
                    "transaction identity could not be verified",
                ) from identity_exc
            if current_intent:
                raise Failure(
                    "TRANSACTION_RECOVERABLE",
                    intent_uri,
                    f"transaction {transaction_id} requires exact-request recovery",
                ) from exc
            raise Failure(
                "IO_FAILURE",
                "index.recover_topic",
                "transaction provenance could not be read",
            ) from exc
        normalized_request, request_findings = atlas_index._decode_journal_request(
            value["request"]
        )
        if request_findings or normalized_request is None:
            _reject(request_findings)
            raise AssertionError("owner did not reject invalid recovery request")
        if normalized_request != value["request"]:
            raise Failure(
                "INDEX_REQUEST_INVALID",
                "args.request",
                "recovery request is not canonical",
            )
        try:
            supplied = atlas_index.canonical_json(value["request"])
            immutable = atlas_index.canonical_json(record["request"])
        except (TypeError, ValueError, UnicodeError) as exc:
            raise Failure(
                "INDEX_REQUEST_INVALID",
                "args.request",
                "recovery request is not canonical JSON",
            ) from exc
        if supplied != immutable:
            raise Failure(
                "MANUAL_CONFLICT",
                "args.request",
                "recovery request differs from immutable intent",
            )
        journal = _index_journal(port, plan)
        if journal.status is not None:
            if journal.status == "manual-conflict":
                raise Failure(
                    "MANUAL_CONFLICT",
                    _logical(f"{_base(plan)}/intent.json"),
                    "transaction requires manual reconciliation",
                )
            successor_exists = False
            if plan.attempt == 0 and journal.status in {"aborted", "rolled-back"}:
                try:
                    successor_exists = _index_successor_exists(port, record, plan)
                except OSError as exc:
                    raise Failure(
                        "TRANSACTION_RECOVERABLE",
                        _logical(f"{_base(plan)}/intent.json"),
                        f"transaction {plan.transaction_id} requires exact-request recovery",
                    ) from exc
            result = _index_transaction_result(
                connector,
                port,
                plan,
                journal.status,
                historical=True,
                record_names=journal.record_names,
            )
            result.update(
                {
                    "state": journal.status,
                    "status": journal.status,
                    "successor_eligible": (
                        plan.attempt == 0
                        and journal.status in {"aborted", "rolled-back"}
                        and not successor_exists
                    ),
                    "validation": {"ok": journal.status == "applied", "findings": []},
                }
            )
            return result
        if "intent.json" not in journal.record_names:
            try:
                status = atlas_transaction.abort_event_only(
                    port,
                    plan.transaction_root,
                    plan,
                    record,
                    terminal_factory=_index_terminal_record,
                    terminal_validator=_index_terminal_validator,
                )
                journal = _index_journal(port, plan)
            except (atlas_transaction.TransactionError, OSError) as exc:
                _index_transaction_error(port, plan, exc)
                raise AssertionError("unreachable")
            result = _index_transaction_result(
                connector,
                port,
                plan,
                status,
                historical=True,
                record_names=journal.record_names,
            )
            result.update(
                {
                    "state": status,
                    "status": status,
                    "successor_eligible": plan.attempt == 0,
                    "validation": {"ok": False, "findings": []},
                }
            )
            return result
        classifications: dict[str, str] | None = None
        recovery_phase = "verification"
        try:
            status_before = journal.status
            prepared = journal.prepared is not None
            recovery_phase = "successor"
            if _index_successor_exists(port, record, plan):
                raise Failure(
                    "SUCCESSOR_TERMINAL_INELIGIBLE",
                    "transaction_id",
                    "only one identical successor is permitted",
                )
            recovery_phase = "classification"
            classifications = _index_classifications(port, plan)
            all_output = all(value == "output" for value in classifications.values())
            if status_before == "applied" and not all_output:
                raise Failure(
                    "MANUAL_CONFLICT",
                    _logical(_base(plan)),
                    "applied transaction targets are not all output bytes",
                )
            if status_before in {"aborted", "rolled-back"} and not all(
                value == "input" for value in classifications.values()
            ):
                raise Failure(
                    "MANUAL_CONFLICT",
                    _logical(_base(plan)),
                    "rolled-back transaction targets are not all input bytes",
                )
            if (
                status_before is None
                and not prepared
                and not all(value == "input" for value in classifications.values())
            ):
                raise Failure(
                    "MANUAL_CONFLICT",
                    _logical(_base(plan)),
                    "unprepared transaction targets are not all input bytes",
                )
            if status_before == "applied":
                try:
                    _index_post_validator(
                        connector,
                        _index_recovery_binding(record, plan).post_validation,
                    )(port, plan)
                except Failure:
                    raise
                except _IndexPostValidationError as exc:
                    raise Failure(
                        "TRANSACTION_RECORD_INVALID",
                        _logical(f"{_base(plan)}/event.json"),
                        "stored applied outputs fail owner post-validation",
                    ) from exc
                except atlas_transaction.TransactionError:
                    raise
            post_validator = None
            if status_before is None and all_output:
                post_validator = _index_post_validator(
                    connector,
                    _index_recovery_binding(record, plan).post_validation,
                )
            recovery_phase = "effects"
            status = atlas_transaction.recover_transaction(
                port,
                plan.transaction_root,
                plan,
                abort_unprepared=True,
                target_allowlist=_index_target_allowed,
                target_rank=_index_rank,
                post_validator=post_validator,
                terminal_validator=lambda terminal_status, terminal, terminal_plan: (
                    _index_terminal_validator(
                        terminal_status,
                        record,
                        terminal,
                        terminal_plan,
                    )
                ),
            )
            recovery_phase = "receipt"
            result = _index_transaction_result(connector, port, plan, status)
        except (atlas_transaction.TransactionError, OSError) as exc:
            _index_transaction_error(
                port,
                plan,
                exc,
                intent_verified=True,
                probe_targets=(
                    classifications is not None
                    and recovery_phase in {"effects", "receipt"}
                ),
            )
            raise AssertionError("unreachable")
        if status == "manual-conflict":
            raise Failure(
                "MANUAL_CONFLICT",
                result["transaction"]["intent_uri"],
                "transaction requires manual reconciliation",
            )
        result.update(
            {
                "state": status,
                "status": status,
                "successor_eligible": (
                    plan.attempt == 0 and status in {"aborted", "rolled-back"}
                ),
                "validation": {"ok": status == "applied", "findings": []},
            }
        )
        return result


def _effect_parse(args: Any) -> dict[str, Any]:
    value = _args(
        args,
        {
            "authority",
            "checks",
            "allowed_target_paths",
            "members",
            "context",
            "transactions",
            "no_write_code",
            "receipt_root",
        },
        "effect.execute",
    )
    authority = _object(value["authority"], "authority")
    authority_fields = {
        "projection_uri",
        "projection_revision",
        "approval_uri",
        "approval_revision",
        "effect_id",
        "effect_sha256",
    }
    if set(authority) != authority_fields:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID", "authority", "authority fields are invalid"
        )
    for name in ("projection_uri", "approval_uri"):
        _uri(authority[name], f"authority.{name}")
    for name in ("projection_revision", "approval_revision"):
        revision = _text(authority[name], f"authority.{name}")
        if _REVISION.fullmatch(revision) is None or revision == "missing":
            raise Failure(
                "EFFECT_AUTHORITY_INVALID",
                f"authority.{name}",
                "authority revision is invalid",
            )
    effect_id = _text(authority["effect_id"], "authority.effect_id")
    effect_sha256 = _text(authority["effect_sha256"], "authority.effect_sha256")
    if (
        _EFFECT_ID.fullmatch(effect_id) is None
        or _SHA256.fullmatch(effect_sha256) is None
    ):
        raise Failure(
            "EFFECT_AUTHORITY_INVALID", "authority", "effect identity is invalid"
        )

    if type(value["checks"]) is not list or not value["checks"]:
        raise Failure(
            "EFFECT_CHECKS_INVALID", "checks", "checks must be a nonempty array"
        )
    checks: list[dict[str, str]] = []
    for index, item in enumerate(value["checks"]):
        row = _object(item, f"checks[{index}]")
        if set(row) != {"path", "expected_revision"}:
            raise Failure(
                "EFFECT_CHECKS_INVALID",
                f"checks[{index}]",
                "check fields are invalid",
            )
        path = _uri(row["path"], f"checks[{index}].path")
        revision = _text(row["expected_revision"], f"checks[{index}].expected_revision")
        if _REVISION.fullmatch(revision) is None:
            raise Failure(
                "EFFECT_CHECKS_INVALID",
                f"checks[{index}].expected_revision",
                "revision is invalid",
            )
        checks.append({"path": path, "expected_revision": revision})
    if checks != sorted(checks, key=lambda item: item["path"].encode("utf-8")) or len(
        {item["path"] for item in checks}
    ) != len(checks):
        raise Failure(
            "EFFECT_CHECKS_INVALID", "checks", "checks are not uniquely byte-sorted"
        )

    if type(value["allowed_target_paths"]) is not list:
        raise Failure(
            "EFFECT_TARGETS_INVALID",
            "allowed_target_paths",
            "allowed paths must be an array",
        )
    allowed = [
        _uri(item, f"allowed_target_paths[{index}]")
        for index, item in enumerate(value["allowed_target_paths"])
    ]
    if allowed != sorted(allowed, key=lambda item: item.encode("utf-8")) or len(
        set(allowed)
    ) != len(allowed):
        raise Failure(
            "EFFECT_TARGETS_INVALID",
            "allowed_target_paths",
            "allowed paths are not uniquely byte-sorted",
        )

    if type(value["members"]) is not list or not value["members"]:
        raise Failure(
            "EFFECT_MEMBERS_INVALID", "members", "members must be a nonempty array"
        )
    members: list[dict[str, Any]] = []
    for index, item in enumerate(value["members"]):
        row = _object(item, f"members[{index}]")
        if set(row) != {"member_id", "role", "origin_sha256", "context"}:
            raise Failure(
                "EFFECT_MEMBERS_INVALID",
                f"members[{index}]",
                "member fields are invalid",
            )
        member_id = _text(row["member_id"], f"members[{index}].member_id")
        role = _text(row["role"], f"members[{index}].role")
        origin = _text(row["origin_sha256"], f"members[{index}].origin_sha256")
        context = _object(row["context"], f"members[{index}].context")
        if (
            _MEMBER_ID.fullmatch(member_id) is None
            or not role
            or _SHA256.fullmatch(origin) is None
        ):
            raise Failure(
                "EFFECT_MEMBERS_INVALID",
                f"members[{index}]",
                "member identity is invalid",
            )
        _json(context)
        members.append(
            {
                "member_id": member_id,
                "role": role,
                "origin_sha256": origin,
                "context": context,
            }
        )
    if members != sorted(members, key=lambda item: item["member_id"]) or len(
        {item["member_id"] for item in members}
    ) != len(members):
        raise Failure(
            "EFFECT_MEMBERS_INVALID", "members", "members are not uniquely sorted"
        )

    context = _object(value["context"], "context")
    _json(context)
    if type(value["transactions"]) is not list or len(value["transactions"]) > 2:
        raise Failure(
            "EFFECT_TRANSACTIONS_INVALID",
            "transactions",
            "transactions must contain at most source and route",
        )
    transactions: list[dict[str, Any]] = []
    for index, item in enumerate(value["transactions"]):
        row = _object(item, f"transactions[{index}]")
        if set(row) != {"stage", "event_record", "targets"}:
            raise Failure(
                "EFFECT_TRANSACTIONS_INVALID",
                f"transactions[{index}]",
                "transaction fields are invalid",
            )
        stage = _text(row["stage"], f"transactions[{index}].stage")
        if stage not in {"source", "route"}:
            raise Failure(
                "EFFECT_TRANSACTIONS_INVALID",
                f"transactions[{index}].stage",
                "stage is invalid",
            )
        record = _event(row["event_record"])
        expected_type = "source-upsert" if stage == "source" else "route-upsert"
        if record["event"]["type"] != expected_type:
            raise Failure(
                "EFFECT_TRANSACTIONS_INVALID",
                f"transactions[{index}].event_record",
                "stage and event type disagree",
            )
        pending, expected = _targets(row["targets"])
        transactions.append(
            {
                "stage": stage,
                "event_record": record,
                "targets": pending,
                "expected": expected,
            }
        )
    stages = [item["stage"] for item in transactions]
    if stages not in ([], ["source"], ["route"], ["source", "route"]):
        raise Failure(
            "EFFECT_TRANSACTIONS_INVALID",
            "transactions",
            "stages are duplicated or out of order",
        )

    no_write = value["no_write_code"]
    if no_write is not None:
        no_write = _text(no_write, "no_write_code")
        if not no_write:
            raise Failure(
                "EFFECT_NO_WRITE_INVALID",
                "no_write_code",
                "no-write code is empty",
            )
    if bool(transactions) == (no_write is not None):
        raise Failure(
            "EFFECT_NO_WRITE_INVALID",
            "no_write_code",
            "exactly one of transactions or a no-write code is required",
        )

    receipt_root = _uri(value["receipt_root"], "receipt_root")
    if not receipt_root.startswith(ROOT + "tmp/") or not receipt_root.endswith(
        "/" + effect_id
    ):
        raise Failure(
            "EFFECT_RECEIPT_ROOT_INVALID",
            "receipt_root",
            "receipt root must be under vault://atlas/tmp/ and end in the effect ID",
        )
    return {
        "value": value,
        "authority": dict(authority),
        "checks": checks,
        "allowed_target_paths": allowed,
        "members": members,
        "context": context,
        "transactions": transactions,
        "no_write_code": no_write,
        "receipt_root": receipt_root,
        "request_sha256": _hash(_json(value)),
    }


def _effect_read_json(
    connector: Any, uri: str, expected_revision: str, path: str
) -> tuple[dict[str, Any], bytes]:
    if connector.revision(uri) != expected_revision:
        raise Failure("EFFECT_AUTHORITY_STALE", path, "authority revision changed")
    try:
        raw = connector.read_bytes(uri)
        value = json.loads(raw.decode("utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID", path, "authority JSON is invalid"
        ) from exc
    document = _object(value, path)
    if _json(document) != raw:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID", path, "authority JSON is noncanonical"
        )
    return document, raw


def _effect_authorize(connector: Any, parsed: Mapping[str, Any]) -> dict[str, Any]:
    authority = parsed["authority"]
    projection, _ = _effect_read_json(
        connector,
        authority["projection_uri"],
        authority["projection_revision"],
        "authority.projection_uri",
    )
    approval, _ = _effect_read_json(
        connector,
        authority["approval_uri"],
        authority["approval_revision"],
        "authority.approval_uri",
    )
    if (
        approval.get("projection_uri") != authority["projection_uri"]
        or approval.get("projection_revision") != authority["projection_revision"]
        or approval.get("projection_whole_byte_sha256")
        != authority["projection_revision"].removeprefix("sha256:")
    ):
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "authority.approval_uri",
            "approval does not bind the projection",
        )
    effects = projection.get("effects")
    if type(effects) is not list:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "authority.projection_uri",
            "effects are invalid",
        )
    selected = [
        item
        for item in effects
        if isinstance(item, Mapping) and item.get("effect_id") == authority["effect_id"]
    ]
    if len(selected) != 1:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "authority.effect_id",
            "projection effect is not unique",
        )
    effect = dict(selected[0])
    core = {key: value for key, value in effect.items() if key != "effect_sha256"}
    if (
        effect.get("effect_sha256") != authority["effect_sha256"]
        or _hash(_json(core)) != authority["effect_sha256"]
        or authority["effect_sha256"] not in projection.get("effect_hashes", [])
    ):
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "authority.effect_sha256",
            "projection effect hash is invalid",
        )
    uses = approval.get("effect_uses")
    if type(uses) is not list:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "authority.approval_uri",
            "approval uses are invalid",
        )
    selected_uses = [
        item
        for item in uses
        if isinstance(item, Mapping) and item.get("effect_id") == authority["effect_id"]
    ]
    if (
        len(selected_uses) != 1
        or selected_uses[0].get("effect_sha256") != authority["effect_sha256"]
        or selected_uses[0].get("use_limit") != 1
        or selected_uses[0].get("consumed") is not False
        or authority["effect_sha256"] not in approval.get("effect_hashes", [])
    ):
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "authority.effect_id",
            "approval does not grant one unconsumed use",
        )
    origins = effect.get("origins")
    if type(origins) is not list or not origins:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "authority.effect_id",
            "projection origins are invalid",
        )
    origin_hashes = sorted(_hash(_json(item)) for item in origins)
    member_hashes = sorted(item["origin_sha256"] for item in parsed["members"])
    if origin_hashes != member_hashes:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "members",
            "members do not account for every projected origin",
        )
    return effect


def _effect_state_hashes(documents: Mapping[str, str]) -> dict[str, str]:
    return {
        name: "sha256:" + _hash(documents[name].encode("utf-8"))
        for name in ("manifest", "topics", "relations", "vocab")
    }


def _effect_revision(value: bytes | None) -> str:
    return "missing" if value is None else "sha256:" + _hash(value)


def _effect_identity_preflight(
    connector: Any,
    parsed: Mapping[str, Any],
    effect: Mapping[str, Any],
    documents: Mapping[str, str],
) -> None:
    identity = _object(effect.get("identity"), "projection.effect.identity")
    source_id = _text(identity.get("source_id"), "projection.effect.identity.source_id")
    canonical_url = _text(
        identity.get("canonical_url"), "projection.effect.identity.canonical_url"
    )
    matches = [
        (row, raw)
        for row, raw in _rows(
            documents["manifest"], atlas_state.MANIFEST_HEADER, MANIFEST
        )
        if row["Source ID"] == source_id or row["Canonical URL"] == canonical_url
    ]
    if any(
        row["Source ID"] != source_id or row["Canonical URL"] != canonical_url
        for row, _ in matches
    ):
        raise Failure(
            "EFFECT_SHARED_INTEGRITY",
            MANIFEST,
            "effect identity collides with a different manifest row",
        )
    row_and_raw = matches[0] if matches else None
    kind = effect.get("effect_kind")
    no_write = parsed["no_write_code"]
    transactions = parsed["transactions"]
    if any(item["event_record"]["source_id"] != source_id for item in transactions):
        raise Failure(
            "EFFECT_IDENTITY_INVALID",
            "transactions",
            "transaction source identity differs from the projected effect",
        )
    if kind == "parent-page-only":
        if row_and_raw is None or row_and_raw[0]["Status"] != "active":
            raise Failure(
                "EFFECT_MEMBER_DRIFT",
                MANIFEST,
                "approved parent row is absent or not active",
            )
        row, raw = row_and_raw
        fixed = effect.get("fixed_artifact_uri")
        if fixed != _logical(row["Artifact"]):
            raise Failure(
                "EFFECT_MEMBER_DRIFT",
                MANIFEST,
                "approved parent artifact path changed",
            )
        for origin in effect["origins"]:
            if origin.get("parent_manifest_row_sha256") != _hash(
                raw.encode("utf-8")
            ) or origin.get("parent_artifact_revision") != connector.revision(
                str(fixed)
            ):
                raise Failure(
                    "EFFECT_MEMBER_DRIFT",
                    str(fixed),
                    "approved parent row or artifact revision changed",
                )
        if not transactions and no_write != "current-valid-no-op":
            raise Failure(
                "EFFECT_NO_WRITE_INVALID",
                "no_write_code",
                "parent direct no-write must be current-valid-no-op",
            )
    elif kind == "independent-candidate":
        status = effect.get("candidate_status")
        if status == "existing-active":
            if (
                row_and_raw is None
                or row_and_raw[0]["Status"] != "active"
                or transactions
                or no_write != "existing-active-no-op"
            ):
                raise Failure(
                    "EFFECT_DEDUPE_CHANGED",
                    MANIFEST,
                    "existing-active effect no longer matches current state",
                )
        elif status == "new" and row_and_raw is not None:
            expected = (
                "existing-active-no-op"
                if row_and_raw[0]["Status"] == "active"
                else "existing-archived-no-op"
            )
            if transactions or no_write != expected:
                raise Failure(
                    "EFFECT_DEDUPE_CHANGED",
                    MANIFEST,
                    f"candidate now requires {expected}",
                )
        elif status == "new" and transactions and transactions[0]["stage"] != "source":
            raise Failure(
                "EFFECT_TRANSACTIONS_INVALID",
                "transactions",
                "a new candidate must start with a source transaction",
            )
    else:
        raise Failure(
            "EFFECT_AUTHORITY_INVALID",
            "projection.effect.effect_kind",
            "effect kind is unsupported",
        )


def _effect_plan_summary(result: atlas_state.ReductionResult) -> dict[str, Any]:
    value = result.to_dict()
    return {
        "result_sha256": _hash(_json(value)),
        "preconditions": dict(sorted(result.preconditions.items())),
        "document_revisions": {
            name: "sha256:" + _hash(text.encode("utf-8"))
            for name, text in sorted(result.documents.items())
        },
        "derived": result.derived,
        "applied_edge_ids": result.applied_edge_ids,
    }


def _effect_prepare_claim(
    connector: Any, parsed: Mapping[str, Any], effect: Mapping[str, Any]
) -> dict[str, Any]:
    for check in parsed["checks"]:
        if connector.revision(check["path"]) != check["expected_revision"]:
            raise Failure(
                "EFFECT_PREPARED_STALE",
                check["path"],
                "prepared input revision changed before claim",
            )
    documents = {**_documents(connector), "vocab": connector.read_text(VOCAB)}
    _validate(documents)
    _effect_identity_preflight(connector, parsed, effect, documents)
    pre_state = _effect_state_hashes(documents)
    virtual_documents = dict(documents)
    virtual_bytes: dict[str, bytes | None] = {}
    claimed_transactions: list[dict[str, Any]] = []
    target_uris: set[str] = set()
    artifact_targets: set[str] = set()
    for transaction in parsed["transactions"]:
        bound: list[atlas_transaction.TransactionTarget] = []
        for target in transaction["targets"]:
            uri = _logical(target.path)
            if target.path not in virtual_bytes:
                revision = connector.revision(uri)
                try:
                    virtual_bytes[target.path] = (
                        None if revision == "missing" else connector.read_bytes(uri)
                    )
                except FileNotFoundError as exc:
                    raise Failure(
                        "EFFECT_STATE_DRIFT", uri, "target disappeared during preflight"
                    ) from exc
            current = virtual_bytes[target.path]
            if _effect_revision(current) != transaction["expected"][target.path]:
                raise Failure(
                    "EFFECT_STATE_DRIFT",
                    uri,
                    "target revision differs from the virtual predecessor state",
                )
            if current == target.output_bytes:
                raise Failure(
                    "EFFECT_TARGET_UNCHANGED",
                    uri,
                    "effect transaction contains an unchanged target",
                )
            bound.append(
                atlas_transaction.TransactionTarget(
                    target.path, current, target.output_bytes
                )
            )
        reduction = _reduce(virtual_documents, transaction["event_record"]["event"])
        candidate_documents = dict(virtual_documents)
        candidate_documents.update(reduction.documents)
        _validate(candidate_documents)
        registry_targets = {
            target.path: target.output_bytes
            for target in bound
            if target.path
            in {
                atlas_state.MANIFEST_PATH,
                atlas_state.TOPICS_PATH,
                atlas_state.RELATIONS_PATH,
                atlas_state.VOCAB_PATH,
            }
        }
        reducer_outputs = {
            (
                atlas_state.VOCAB_PATH if name == "vocab" else _relative(_doc_uri(name))
            ): text.encode("utf-8")
            for name, text in reduction.documents.items()
        }
        if registry_targets != reducer_outputs:
            raise Failure(
                "EFFECT_REDUCER_OUTPUT_MISMATCH",
                "transactions",
                "registry targets do not equal reducer output",
            )
        stage_artifacts = [
            target
            for target in bound
            if target.path.startswith(atlas_source.ARTIFACT_PREFIX)
        ]
        if len(stage_artifacts) != 1:
            raise Failure(
                "EFFECT_TARGETS_INVALID",
                "transactions",
                "each source or route transaction must target one artifact",
            )
        artifact_target = stage_artifacts[0]
        try:
            artifact = atlas_source.parse_artifact(
                artifact_target.output_bytes.decode("utf-8")
            ).values
        except (UnicodeDecodeError, ValueError) as exc:
            raise Failure(
                "EFFECT_ARTIFACT_INVALID",
                _logical(artifact_target.path),
                str(exc),
            ) from exc
        source_id = transaction["event_record"]["source_id"]
        manifest_row = next(
            (
                row
                for row, _ in _rows(
                    candidate_documents["manifest"],
                    atlas_state.MANIFEST_HEADER,
                    MANIFEST,
                )
                if row["Source ID"] == source_id
            ),
            None,
        )
        actual = {
            "Source ID": atlas_source.scalar(artifact, "source_id"),
            "Source seq": atlas_source.scalar(artifact, "source_seq"),
            "Canonical URL": atlas_source.scalar(artifact, "canonical_url"),
            "Content hash": atlas_source.scalar(artifact, "content_hash"),
            "Route status": atlas_source.scalar(artifact, "routing_status"),
            "Artifact": artifact_target.path,
        }
        if (
            manifest_row is None
            or manifest_row["Source ID"] != effect["identity"]["source_id"]
            or manifest_row["Canonical URL"] != effect["identity"]["canonical_url"]
            or actual != {key: manifest_row[key] for key in actual}
        ):
            raise Failure(
                "EFFECT_ARTIFACT_INVALID",
                _logical(artifact_target.path),
                "artifact does not equal reducer-emitted manifest identity",
            )
        if transaction["event_record"]["event"]["type"] == "source-upsert":
            try:
                living_artifact_text = (
                    None
                    if artifact_target.input_bytes is None
                    else artifact_target.input_bytes.decode("utf-8")
                )
            except UnicodeDecodeError as exc:
                raise Failure(
                    "EFFECT_ARTIFACT_INVALID",
                    _logical(artifact_target.path),
                    "source artifact preimage is not UTF-8",
                ) from exc
            _source_artifact_guard(
                virtual_documents,
                reduction,
                transaction["event_record"]["event"],
                artifact_target,
                living_artifact_text,
            )
            expected_source_projection = {
                **reducer_outputs,
                artifact_target.path: artifact_target.output_bytes,
            }
            actual_source_projection = {
                target.path: target.output_bytes for target in bound
            }
            if actual_source_projection != expected_source_projection:
                raise Failure(
                    "SOURCE_PREFLIGHT_PROJECTION_MISMATCH",
                    "transactions",
                    "source targets do not equal the reducer and artifact projection",
                )
        if transaction["event_record"]["event"]["type"] == "route-upsert":
            expected_route_projection = _route_projection(
                transaction["event_record"],
                virtual_documents,
                reduction,
                artifact_target.path,
                artifact_target.input_bytes,
            )
            actual_route_projection = {
                target.path: target.output_bytes for target in bound
            }
            if actual_route_projection != expected_route_projection:
                raise Failure(
                    "ROUTE_PREFLIGHT_PROJECTION_MISMATCH",
                    "transactions",
                    "route targets do not equal the reducer and renderer projection",
                )
        try:
            plan = _plan(transaction["event_record"], tuple(bound))
        except atlas_transaction.TransactionError as exc:
            raise Failure(
                "EFFECT_TRANSACTIONS_INVALID", "transactions", str(exc)
            ) from exc
        claimed_transactions.append(
            {
                "stage": transaction["stage"],
                "transaction_id": plan.transaction_id,
                "transaction": atlas_transaction.event_record_value(
                    transaction["event_record"], plan
                ),
                "reducer": _effect_plan_summary(reduction),
            }
        )
        for target in bound:
            virtual_bytes[target.path] = target.output_bytes
            target_uris.add(_logical(target.path))
            if target.path.startswith(atlas_source.ARTIFACT_PREFIX):
                artifact_targets.add(_logical(target.path))
        virtual_documents = candidate_documents
    expected_allowed = sorted(target_uris, key=lambda item: item.encode("utf-8"))
    if expected_allowed != parsed["allowed_target_paths"]:
        raise Failure(
            "EFFECT_TARGETS_INVALID",
            "allowed_target_paths",
            "allowed paths do not equal the transaction target union",
        )
    if effect["effect_kind"] == "parent-page-only" and artifact_targets not in (
        set(),
        {effect["fixed_artifact_uri"]},
    ):
        raise Failure(
            "EFFECT_TARGETS_INVALID",
            "allowed_target_paths",
            "page-only effect targets another artifact",
        )
    return {
        "version": VERSION,
        "kind": "effect-claim-v1",
        "request_sha256": parsed["request_sha256"],
        "authority": parsed["authority"],
        "effect": dict(effect),
        "checks": parsed["checks"],
        "allowed_target_paths": parsed["allowed_target_paths"],
        "members": parsed["members"],
        "context": parsed["context"],
        "no_write_code": parsed["no_write_code"],
        "receipt_root": parsed["receipt_root"],
        "pre_state": pre_state,
        "expected_post_state": _effect_state_hashes(virtual_documents),
        "transactions": claimed_transactions,
    }


def _effect_paths(parsed: Mapping[str, Any]) -> dict[str, Any]:
    root = parsed["receipt_root"]
    return {
        "claim": root + "/claim.json",
        "members": [
            (item["member_id"], root + f"/member-{item['member_id']}.json")
            for item in parsed["members"]
        ],
        "effect": root + "/effect.json",
        "closure": root + "/closure.json",
    }


def _effect_descriptor(connector: Any, uri: str) -> dict[str, str]:
    revision = connector.revision(uri)
    if revision == "missing":
        raise Failure("EFFECT_RECORD_INVALID", uri, "effect record is missing")
    return {"uri": uri, "revision": revision}


def _effect_load_record(connector: Any, uri: str, code: str) -> dict[str, Any] | None:
    revision = connector.revision(uri)
    if revision == "missing":
        return None
    try:
        raw = connector.read_bytes(uri)
        value = json.loads(raw.decode("utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Failure(code, uri, "immutable record is invalid") from exc
    record = _object(value, uri)
    if _json(record) != raw:
        raise Failure(code, uri, "immutable record is noncanonical")
    return record


def _effect_claim_plan(
    value: Mapping[str, Any],
) -> tuple[dict[str, Any], atlas_transaction.TransactionPlan]:
    transaction = _object(value.get("transaction"), "claim.transactions.transaction")
    if set(transaction) != {
        "version",
        "event_record",
        "attempt",
        "predecessor_sha256",
        "targets",
    }:
        raise Failure(
            "EFFECT_CLAIM_INVALID",
            "claim.transactions.transaction",
            "claimed transaction fields are invalid",
        )
    if (
        transaction["version"] != VERSION
        or transaction["attempt"] != 0
        or transaction["predecessor_sha256"] is not None
        or type(transaction["targets"]) is not list
        or not transaction["targets"]
    ):
        raise Failure(
            "EFFECT_CLAIM_INVALID",
            "claim.transactions.transaction",
            "claimed attempt is invalid",
        )
    record = _event(transaction["event_record"])
    targets: list[atlas_transaction.TransactionTarget] = []
    for item in transaction["targets"]:
        row = _object(item, "claim.transactions.targets")
        if set(row) != {"path", "input_base64", "output_base64"}:
            raise Failure(
                "EFFECT_CLAIM_INVALID",
                "claim.transactions.targets",
                "claimed target fields are invalid",
            )
        try:
            input_bytes = (
                None
                if row["input_base64"] is None
                else base64.b64decode(row["input_base64"], validate=True)
            )
            output_bytes = base64.b64decode(row["output_base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise Failure(
                "EFFECT_CLAIM_INVALID",
                "claim.transactions.targets",
                "claimed target bytes are invalid",
            ) from exc
        path = _text(row["path"], "claim.transactions.targets.path")
        _rank(path)
        targets.append(
            atlas_transaction.TransactionTarget(path, input_bytes, output_bytes)
        )
    plan = _plan(record, tuple(targets))
    if plan.transaction_id != value.get("transaction_id"):
        raise Failure(
            "EFFECT_CLAIM_INVALID",
            "claim.transactions.transaction_id",
            "claimed transaction ID is invalid",
        )
    return record, plan


def _effect_current_bytes(
    connector: Any, target: atlas_transaction.TransactionTarget
) -> bytes | None:
    uri = _logical(target.path)
    revision = connector.revision(uri)
    try:
        return None if revision == "missing" else connector.read_bytes(uri)
    except FileNotFoundError as exc:
        raise Failure("EFFECT_STATE_DRIFT", uri, "target disappeared") from exc


def _effect_run_attempt(
    connector: Any,
    port: _Port,
    record: Mapping[str, Any],
    plan: atlas_transaction.TransactionPlan,
) -> tuple[str, dict[str, Any]]:
    event_path = f"{_base(plan)}/event.json"
    existing = port.read_record(event_path)
    try:
        if existing is None:
            if any(
                _effect_current_bytes(connector, target) != target.input_bytes
                for target in plan.targets
            ):
                raise Failure(
                    "EFFECT_STATE_DRIFT",
                    _logical(event_path),
                    "claimed transaction inputs drifted",
                )
            _source_guard(connector, record, plan.targets)
            _route_guard(connector, record, plan.targets)
            try:
                atlas_transaction.store_event(
                    port,
                    TRANSACTION_ROOT,
                    record,
                    plan,
                )
            except atlas_transaction.TransactionRecordError as exc:
                raise _record_failure(exc) from exc
            except atlas_transaction.TransactionError as exc:
                raise Failure(
                    "TRANSACTION_EVENT_COLLISION",
                    _logical(event_path),
                    "immutable event differs",
                ) from exc
            status = atlas_transaction.execute_transaction(
                port,
                TRANSACTION_ROOT,
                plan,
                target_allowlist=_target_allowed,
                target_rank=_rank,
                post_validator=_source_post_validator(connector, record),
            )
        else:
            loaded_record, loaded_plan = _load_plan(port, plan.transaction_id)
            if (
                atlas_transaction.event_record_value(loaded_record, loaded_plan)
                != atlas_transaction.event_record_value(record, plan)
                or loaded_plan.transaction_id != plan.transaction_id
            ):
                raise Failure(
                    "EFFECT_TRANSACTION_COLLISION",
                    _logical(event_path),
                    "stored transaction differs from claim",
                )
            post_validator = _source_post_validator(connector, record)
            intent = port.read_record(f"{_base(plan)}/intent.json")
            aborted = port.read_record(f"{_base(plan)}/aborted.json")
            operation = (
                atlas_transaction.execute_transaction
                if intent is None and aborted is None
                else atlas_transaction.recover_transaction
            )
            status = operation(
                port,
                TRANSACTION_ROOT,
                plan,
                target_allowlist=_target_allowed,
                target_rank=_rank,
                post_validator=post_validator,
            )
    except atlas_transaction.TransactionRecordError as exc:
        raise _record_failure(exc) from exc
    except atlas_transaction.TransactionTargetConflict as exc:
        raise Failure(
            "MANUAL_CONFLICT",
            _record_path(exc.path),
            exc.detail,
        ) from exc
    except atlas_transaction.TransactionError as exc:
        raise Failure(
            "EFFECT_TRANSACTION_INVALID", _logical(event_path), str(exc)
        ) from exc
    return status, _tx_result(connector, port, plan, status)


def _effect_resume_transaction(
    connector: Any,
    claimed: Mapping[str, Any],
) -> dict[str, Any]:
    record, plan = _effect_claim_plan(claimed)
    port = _Port(connector)
    status, result = _effect_run_attempt(connector, port, record, plan)
    if status in {"applied", "no-op"}:
        return result["receipt"]
    if status == "manual-conflict":
        raise Failure(
            "MANUAL_CONFLICT", result["intent_uri"], "effect transaction conflicts"
        )
    if status not in {"aborted", "rolled-back"}:
        raise Failure(
            "EFFECT_OPERATIONAL_BLOCKED",
            result["intent_uri"],
            f"transaction reached {status}",
        )
    terminal = port.read_record(f"{_base(plan)}/{status}.json")
    assert terminal is not None
    successor_id = f"{plan.base_transaction_id}-a{plan.attempt + 1:06d}"
    try:
        successor = atlas_transaction.build_successor_plan(
            plan,
            event_path=f"{TRANSACTION_ROOT}/{successor_id}/event.json",
            event_record=record,
            terminal_record=terminal,
            target_allowlist=_target_allowed,
            target_rank=_rank,
            identity_binding=_identity_binding,
        )
    except atlas_transaction.TransactionError as exc:
        raise Failure(
            "EFFECT_OPERATIONAL_BLOCKED", result["intent_uri"], str(exc)
        ) from exc
    successor_status, successor_result = _effect_run_attempt(
        connector, port, record, successor
    )
    if successor_status == "manual-conflict":
        raise Failure(
            "MANUAL_CONFLICT",
            successor_result["intent_uri"],
            "effect successor conflicts",
        )
    if successor_status not in {"applied", "no-op"}:
        raise Failure(
            "EFFECT_OPERATIONAL_BLOCKED",
            successor_result["intent_uri"],
            f"effect successor reached {successor_status}",
        )
    return successor_result["receipt"]


def _effect_result_from_closure(
    connector: Any, paths: Mapping[str, Any], closure: Mapping[str, Any]
) -> dict[str, Any]:
    required = {
        "version",
        "kind",
        "request_sha256",
        "claim",
        "members",
        "effect",
        "transactions",
        "outcome",
        "pre_state",
        "post_state",
        "validation",
    }
    if (
        set(closure) != required
        or closure.get("version") != VERSION
        or closure.get("kind") != "effect-closure-v1"
    ):
        raise Failure(
            "EFFECT_RECORD_INVALID", paths["closure"], "closure fields are invalid"
        )
    return {
        "claim": closure["claim"],
        "members": closure["members"],
        "effect": closure["effect"],
        "closure": _effect_descriptor(connector, paths["closure"]),
        "transactions": closure["transactions"],
        "outcome": closure["outcome"],
    }


def _effect_resume(
    connector: Any,
    parsed: Mapping[str, Any],
    claim: Mapping[str, Any],
    paths: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        claim.get("version") != VERSION
        or claim.get("kind") != "effect-claim-v1"
        or claim.get("request_sha256") != parsed["request_sha256"]
        or claim.get("authority") != parsed["authority"]
        or claim.get("receipt_root") != parsed["receipt_root"]
    ):
        raise Failure(
            "EFFECT_CLAIM_COLLISION",
            paths["claim"],
            "existing claim differs from the exact request",
        )
    closure = _effect_load_record(connector, paths["closure"], "EFFECT_RECORD_INVALID")
    if closure is not None:
        if closure.get("request_sha256") != parsed["request_sha256"]:
            raise Failure(
                "EFFECT_RECORD_INVALID",
                paths["closure"],
                "closure request binding differs",
            )
        return _effect_result_from_closure(connector, paths, closure)
    target_paths = {
        _logical(target.path)
        for claimed in claim.get("transactions", [])
        for target in _effect_claim_plan(claimed)[1].targets
    }
    for check in claim.get("checks", []):
        if (
            check["path"] not in target_paths
            and connector.revision(check["path"]) != check["expected_revision"]
        ):
            raise Failure(
                "EFFECT_PREPARED_STALE",
                check["path"],
                "prepared input changed during recovery",
            )
    transaction_results: list[dict[str, Any]] = []
    for index, claimed in enumerate(claim.get("transactions", [])):
        receipt = _effect_resume_transaction(connector, claimed)
        transaction_results.append({"stage": claimed["stage"], "receipt": receipt})
        if (
            claimed["stage"] == "source"
            and index + 1 < len(claim["transactions"])
            and receipt["status"] != "applied"
        ):
            raise Failure(
                "EFFECT_OPERATIONAL_BLOCKED",
                "transactions",
                "route cannot advance after a source no-op",
            )
        documents = {**_documents(connector), "vocab": connector.read_text(VOCAB)}
        _validate(documents)
    post_documents = {
        **_documents(connector),
        "vocab": connector.read_text(VOCAB),
    }
    _validate(post_documents)
    post_state = _effect_state_hashes(post_documents)
    if post_state != claim.get("expected_post_state"):
        raise Failure(
            "EFFECT_STATE_DRIFT",
            MANIFEST,
            "complete post-state differs from the claimed reducer chain",
        )
    outcome = (
        claim["no_write_code"]
        if claim["no_write_code"] is not None
        else (
            "applied"
            if any(
                item["receipt"]["status"] == "applied" for item in transaction_results
            )
            else "no-op"
        )
    )
    claim_descriptor = _effect_descriptor(connector, paths["claim"])
    member_descriptors: list[dict[str, str]] = []
    for member, (member_id, uri) in zip(
        claim["members"], paths["members"], strict=True
    ):
        assert member["member_id"] == member_id
        value = {
            "version": VERSION,
            "kind": "effect-member-receipt-v1",
            "request_sha256": claim["request_sha256"],
            "effect_id": claim["authority"]["effect_id"],
            "effect_sha256": claim["authority"]["effect_sha256"],
            "member_id": member_id,
            "role": member["role"],
            "origin_sha256": member["origin_sha256"],
            "context": member["context"],
            "claim": claim_descriptor,
            "transactions": transaction_results,
            "reducers": [
                {
                    "stage": item["stage"],
                    "result": item["reducer"],
                }
                for item in claim["transactions"]
            ],
            "pre_state": claim["pre_state"],
            "post_state": post_state,
            "validation": {"findings": []},
            "outcome": outcome,
        }
        _immutable(connector, uri, value, "EFFECT_RECEIPT_COLLISION")
        member_descriptors.append(
            {"member_id": member_id, **_effect_descriptor(connector, uri)}
        )
    effect_value = {
        "version": VERSION,
        "kind": "effect-receipt-v1",
        "request_sha256": claim["request_sha256"],
        "authority": claim["authority"],
        "context": claim["context"],
        "claim": claim_descriptor,
        "members": member_descriptors,
        "transactions": transaction_results,
        "reducers": [
            {"stage": item["stage"], "result": item["reducer"]}
            for item in claim["transactions"]
        ],
        "pre_state": claim["pre_state"],
        "post_state": post_state,
        "validation": {"findings": []},
        "outcome": outcome,
    }
    _immutable(connector, paths["effect"], effect_value, "EFFECT_RECEIPT_COLLISION")
    effect_descriptor = _effect_descriptor(connector, paths["effect"])
    closure_value = {
        "version": VERSION,
        "kind": "effect-closure-v1",
        "request_sha256": claim["request_sha256"],
        "claim": claim_descriptor,
        "members": member_descriptors,
        "effect": effect_descriptor,
        "transactions": transaction_results,
        "outcome": outcome,
        "pre_state": claim["pre_state"],
        "post_state": post_state,
        "validation": {"findings": []},
    }
    _immutable(connector, paths["closure"], closure_value, "EFFECT_CLOSURE_COLLISION")
    return _effect_result_from_closure(connector, paths, closure_value)


def _effect_execute(connector: Any, args: Any, *, recover: bool) -> dict[str, Any]:
    parsed = _effect_parse(args)
    _mutations(connector)
    values = _capabilities(connector)
    if (
        values.get("adapter") != "atlas-local-fs-cas-v1"
        or values.get("logical_root") != ROOT
    ):
        raise Failure(
            "BINDING_INVALID", "connector", "unsupported connector capability"
        )
    paths = _effect_paths(parsed)
    with connector.mutation_session():
        effect = _effect_authorize(connector, parsed)
        existing = _effect_load_record(
            connector, paths["claim"], "EFFECT_CLAIM_INVALID"
        )
        if existing is None:
            if recover:
                raise Failure(
                    "EFFECT_CLAIM_UNKNOWN", paths["claim"], "effect claim is missing"
                )
            for _, uri in paths["members"]:
                if connector.revision(uri) != "missing":
                    raise Failure(
                        "EFFECT_RECORD_COLLISION",
                        uri,
                        "receipt exists without a claim",
                    )
            for name in ("effect", "closure"):
                if connector.revision(paths[name]) != "missing":
                    raise Failure(
                        "EFFECT_RECORD_COLLISION",
                        paths[name],
                        "record exists without a claim",
                    )
            claim = _effect_prepare_claim(connector, parsed, effect)
            _immutable(connector, paths["claim"], claim, "EFFECT_CLAIM_COLLISION")
        else:
            claim = existing
        return _effect_resume(connector, parsed, claim, paths)


def _day(value: Any, path: str) -> str:
    result = _text(value, path)
    try:
        if date.fromisoformat(result).isoformat() != result:
            raise ValueError
    except ValueError as exc:
        raise Failure(
            "REFRESH_PROJECTION_INVALID", path, "expected YYYY-MM-DD"
        ) from exc
    return result


def _projection(
    value: Any, pass_text: Any, index_text: Any
) -> tuple[dict[str, Any], str, str]:
    data = _object(value, "projection")
    fields = {
        "version",
        "topic_id",
        "edge_ids",
        "manifest_revision",
        "topics_revision",
        "relations_revision",
        "index_uri",
        "index_revision",
        "pass_uri",
        "pass_expected_revision",
        "pass_sha256",
        "index_sha256",
        "started_at",
        "completed_on",
        "transaction_root",
    }
    if (
        set(data) != fields
        or type(data["version"]) is not int
        or data["version"] != VERSION
    ):
        raise Failure(
            "REFRESH_PROJECTION_INVALID", "projection", "projection fields are invalid"
        )
    result = dict(data)
    result["topic_id"] = _text(result["topic_id"], "projection.topic_id")
    if (
        type(result["edge_ids"]) is not list
        or not all(isinstance(item, str) and item for item in result["edge_ids"])
        or len(set(result["edge_ids"])) != len(result["edge_ids"])
    ):
        raise Failure(
            "REFRESH_PROJECTION_INVALID",
            "projection.edge_ids",
            "edge IDs must be unique nonempty text",
        )
    for key in (
        "manifest_revision",
        "topics_revision",
        "relations_revision",
        "index_revision",
        "pass_expected_revision",
    ):
        if _REVISION.fullmatch(_text(result[key], f"projection.{key}")) is None:
            raise Failure(
                "REFRESH_PROJECTION_INVALID", f"projection.{key}", "revision is invalid"
            )
    if result["pass_expected_revision"] != "missing":
        raise Failure(
            "REFRESH_PROJECTION_INVALID",
            "projection.pass_expected_revision",
            "pass must be expected missing",
        )
    for key in ("pass_sha256", "index_sha256"):
        if _SHA256.fullmatch(_text(result[key], f"projection.{key}")) is None:
            raise Failure(
                "REFRESH_PROJECTION_INVALID", f"projection.{key}", "hash is invalid"
            )
    result["index_uri"] = _uri(result["index_uri"], "projection.index_uri")
    result["pass_uri"] = _uri(result["pass_uri"], "projection.pass_uri")
    result["transaction_root"] = _uri(
        result["transaction_root"], "projection.transaction_root"
    )
    result["started_at"] = _day(result["started_at"], "projection.started_at")
    result["completed_on"] = _day(result["completed_on"], "projection.completed_on")
    passed, indexed = _text(pass_text, "pass_text"), _text(index_text, "index_text")
    if _hash(passed.encode("utf-8")) != result["pass_sha256"]:
        raise Failure(
            "REFRESH_OUTPUT_HASH_MISMATCH",
            "pass_text",
            "pass bytes do not match projection",
        )
    if _hash(indexed.encode("utf-8")) != result["index_sha256"]:
        raise Failure(
            "REFRESH_OUTPUT_HASH_MISMATCH",
            "index_text",
            "index bytes do not match projection",
        )
    return result, passed, indexed


def _refresh_paths(projection: Mapping[str, Any]) -> tuple[str, str, str]:
    root = _relative(str(projection["transaction_root"]))
    return root, f"{root}/intent.json", f"{root}/receipt.json"


def _immutable(connector: Any, uri: str, value: Mapping[str, Any], code: str) -> None:
    data = _json(value)
    revision = connector.revision(uri)
    if revision == "missing":
        connector.conditional_replace(uri, "missing", data)
    elif connector.read_bytes(uri) != data:
        raise Failure(code, uri, "immutable record differs")


def _intent(
    projection: Mapping[str, Any], pass_text: str, index_text: str
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "projection": dict(projection),
        "pass_text": pass_text,
        "index_text": index_text,
    }


def _refresh_receipt(
    projection: Mapping[str, Any],
    intent: Mapping[str, Any],
    status: str,
    reason: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "topic_id": projection["topic_id"],
        "edge_ids": list(projection["edge_ids"]),
        "pass_uri": projection["pass_uri"],
        "pass_sha256": projection["pass_sha256"],
        "index_sha256": projection["index_sha256"],
        "input_revisions": {
            key.removesuffix("_revision"): projection[key]
            for key in (
                "manifest_revision",
                "topics_revision",
                "relations_revision",
                "index_revision",
            )
        },
        "intent_sha256": _hash(_json(intent)),
    }
    if reason is not None:
        result["reason"] = reason
    return result


def _apply(
    connector: Any, result: atlas_state.ReductionResult, revisions: Mapping[str, str]
) -> None:
    for name in ("relations", "topics", "manifest"):
        if name in result.documents:
            connector.conditional_replace(
                _doc_uri(name), revisions[name], result.documents[name].encode("utf-8")
            )


def _phase_uris(connector: Any, root: str) -> list[str]:
    try:
        entries = connector.list(_logical(root))
    except FileNotFoundError:
        return []
    return [
        entry
        for entry in entries
        if entry.endswith(".json")
        and not entry.endswith("/intent.json")
        and not entry.endswith("/receipt.json")
    ]


def _refresh_result(
    connector: Any, projection: Mapping[str, Any], receipt: Mapping[str, Any]
) -> dict[str, Any]:
    root, intent_path, _ = _refresh_paths(projection)
    return {
        "intent_uri": _logical(intent_path),
        "phase_uris": _phase_uris(connector, root),
        "receipt": dict(receipt),
    }


def _block(
    connector: Any,
    projection: Mapping[str, Any],
    intent: Mapping[str, Any],
    root: str,
    reason: str,
) -> dict[str, Any]:
    docs = _documents(connector)
    result = _reduce(
        docs,
        {"type": "refresh-fail", "topic_id": projection["topic_id"], "reason": reason},
        refresh=True,
    )
    _apply(
        connector, result, {name: connector.revision(_doc_uri(name)) for name in docs}
    )
    _immutable(
        connector,
        _logical(f"{root}/phases/blocked.json"),
        {
            "version": VERSION,
            "reason": reason,
            "topics_revision": connector.revision(TOPICS),
        },
        "REFRESH_PHASE_CONFLICT",
    )
    receipt = _refresh_receipt(projection, intent, "blocked", reason)
    _, _, receipt_path = _refresh_paths(projection)
    _immutable(connector, _logical(receipt_path), receipt, "REFRESH_RECEIPT_CONFLICT")
    return receipt


def _complete(
    connector: Any, projection: Mapping[str, Any], intent: Mapping[str, Any], root: str
) -> dict[str, Any]:
    docs = _documents(connector)
    result = _reduce(
        docs,
        {
            "type": "refresh-complete",
            "topic_id": projection["topic_id"],
            "edge_ids": list(projection["edge_ids"]),
            "pass_path": _relative(str(projection["pass_uri"])),
            "completed_on": projection["completed_on"],
        },
        refresh=True,
    )
    _apply(
        connector, result, {name: connector.revision(_doc_uri(name)) for name in docs}
    )
    _validate(_documents(connector))
    _immutable(
        connector,
        _logical(f"{root}/phases/complete.json"),
        {
            "version": VERSION,
            "relations_revision": connector.revision(RELATIONS),
            "topics_revision": connector.revision(TOPICS),
            "applied_edge_ids": list(projection["edge_ids"]),
        },
        "REFRESH_PHASE_CONFLICT",
    )
    receipt = _refresh_receipt(projection, intent, "current")
    _, _, receipt_path = _refresh_paths(projection)
    _immutable(connector, _logical(receipt_path), receipt, "REFRESH_RECEIPT_CONFLICT")
    return receipt


def _stored_receipt(connector: Any, receipt_path: str) -> dict[str, Any] | None:
    try:
        raw = connector.read_bytes(_logical(receipt_path))
    except FileNotFoundError:
        return None
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Failure(
            "REFRESH_RECEIPT_INVALID", _logical(receipt_path), "receipt is invalid"
        ) from exc
    if type(receipt) is not dict or _json(receipt) != raw:
        raise Failure(
            "REFRESH_RECEIPT_INVALID", _logical(receipt_path), "receipt is noncanonical"
        )
    return receipt


def _recover_refresh(
    connector: Any, projection: Mapping[str, Any], pass_text: str, index_text: str
) -> dict[str, Any]:
    intent = _intent(projection, pass_text, index_text)
    root, intent_path, receipt_path = _refresh_paths(projection)
    try:
        raw = connector.read_bytes(_logical(intent_path))
    except FileNotFoundError as exc:
        raise Failure(
            "REFRESH_INTENT_MISSING", _logical(intent_path), "refresh intent is missing"
        ) from exc
    if raw != _json(intent):
        raise Failure(
            "REFRESH_RECOVERY_MISMATCH",
            _logical(intent_path),
            "request differs from immutable intent",
        )
    receipt = _stored_receipt(connector, receipt_path)
    if receipt is not None:
        return _refresh_result(connector, projection, receipt)
    pass_revision = connector.revision(str(projection["pass_uri"]))
    index_revision = connector.revision(str(projection["index_uri"]))
    want_pass, want_index = (
        "sha256:" + str(projection["pass_sha256"]),
        "sha256:" + str(projection["index_sha256"]),
    )
    if pass_revision not in {"missing", want_pass} or index_revision not in {
        str(projection["index_revision"]),
        want_index,
    }:
        raise Failure(
            "MANUAL_CONFLICT",
            _logical(root),
            "refresh output differs from immutable projection",
        )
    docs = _documents(connector)
    topic = next(
        (
            row
            for row, _ in _rows(docs["topics"], atlas_state.TOPICS_HEADER, TOPICS)
            if row["Topic ID"] == projection["topic_id"]
        ),
        None,
    )
    if topic is None:
        raise Failure("MANUAL_CONFLICT", TOPICS, "refresh topic is missing")
    if pass_revision == want_pass and index_revision == want_index:
        return _refresh_result(
            connector, projection, _complete(connector, projection, intent, root)
        )
    if topic["Freshness state"] == "refreshing":
        return _refresh_result(
            connector,
            projection,
            _block(connector, projection, intent, root, "incomplete refresh recovery"),
        )
    if topic["Freshness state"] == "blocked":
        receipt = _refresh_receipt(
            projection, intent, "blocked", "incomplete refresh recovery"
        )
        _immutable(
            connector, _logical(receipt_path), receipt, "REFRESH_RECEIPT_CONFLICT"
        )
        return _refresh_result(connector, projection, receipt)
    raise Failure("MANUAL_CONFLICT", TOPICS, "refresh phase cannot be recovered")


def _refresh_execute(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"projection", "pass_text", "index_text"}, "refresh.execute")
    projection, pass_text, index_text = _projection(
        value["projection"], value["pass_text"], value["index_text"]
    )
    _mutations(connector)
    with connector.mutation_session():
        root, intent_path, _ = _refresh_paths(projection)
        try:
            actual = {
                "manifest": connector.revision(MANIFEST),
                "topics": connector.revision(TOPICS),
                "relations": connector.revision(RELATIONS),
                "index": connector.revision(str(projection["index_uri"])),
            }
            expected = {
                "manifest": projection["manifest_revision"],
                "topics": projection["topics_revision"],
                "relations": projection["relations_revision"],
                "index": projection["index_revision"],
            }
            if actual != expected:
                raise Failure(
                    "REVISION_STALE", "projection", "refresh input revisions changed"
                )
            if connector.revision(_logical(intent_path)) != "missing":
                return _recover_refresh(connector, projection, pass_text, index_text)
            docs = _documents(connector)
            start = _reduce(
                docs,
                {
                    "type": "refresh-start",
                    "topic_id": projection["topic_id"],
                    "edge_ids": list(projection["edge_ids"]),
                    "started_at": projection["started_at"],
                },
                refresh=True,
            )
            selection = atlas_state.select_topic_state(
                docs, str(projection["topic_id"])
            )
            if selection.topic is None or selection.findings:
                raise Failure(
                    "REFRESH_TOPIC_INVALID",
                    TOPICS,
                    "refresh topic selection is invalid",
                )
            rank_findings = atlas_state.validate_answer_authoring(
                connector.read_text(str(projection["index_uri"])),
                index_text,
                selection.relations,
                selected_edge_ids=projection["edge_ids"],
                path="index_text",
            )
            _reject(rank_findings)
            intent = _intent(projection, pass_text, index_text)
            _immutable(
                connector, _logical(intent_path), intent, "REFRESH_INTENT_CONFLICT"
            )
            _immutable(
                connector,
                _logical(f"{root}/phases/start.json"),
                {
                    "version": VERSION,
                    "topics_revision": projection["topics_revision"],
                    "edge_ids": list(projection["edge_ids"]),
                },
                "REFRESH_PHASE_CONFLICT",
            )
            _apply(
                connector,
                start,
                {
                    "manifest": actual["manifest"],
                    "topics": actual["topics"],
                    "relations": actual["relations"],
                },
            )
            pass_uri = str(projection["pass_uri"])
            if connector.revision(pass_uri) != "missing":
                _block(connector, projection, intent, root, "pass collision")
                raise Failure("PASS_COLLISION", pass_uri, "pass target is not missing")
            connector.conditional_replace(
                pass_uri, "missing", pass_text.encode("utf-8")
            )
            _immutable(
                connector,
                _logical(f"{root}/phases/pass.json"),
                {
                    "version": VERSION,
                    "pass_revision": connector.revision(pass_uri),
                    "pass_sha256": projection["pass_sha256"],
                },
                "REFRESH_PHASE_CONFLICT",
            )
            index_uri = str(projection["index_uri"])
            if connector.revision(index_uri) != projection["index_revision"]:
                _block(connector, projection, intent, root, "index revision stale")
                raise Failure(
                    "REFRESH_CONCURRENT_MUTATION", index_uri, "index revision changed"
                )
            connector.conditional_replace(
                index_uri, str(projection["index_revision"]), index_text.encode("utf-8")
            )
            _immutable(
                connector,
                _logical(f"{root}/phases/index.json"),
                {
                    "version": VERSION,
                    "index_revision": connector.revision(index_uri),
                    "index_sha256": projection["index_sha256"],
                },
                "REFRESH_PHASE_CONFLICT",
            )
            return _refresh_result(
                connector, projection, _complete(connector, projection, intent, root)
            )
        except OSError as exc:
            raise Failure("IO_FAILURE", _logical(intent_path), str(exc)) from exc


def _refresh_recover(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"projection", "pass_text", "index_text"}, "refresh.recover")
    projection, pass_text, index_text = _projection(
        value["projection"], value["pass_text"], value["index_text"]
    )
    _mutations(connector)
    with connector.mutation_session():
        return _recover_refresh(connector, projection, pass_text, index_text)


def _vault(connector: Any, op: str, args: Any) -> dict[str, Any]:
    if op == "vault.read":
        value = _args(args, {"path"}, op)
        uri = _uri(value["path"], "args.path")
        return {
            "path": uri,
            "text": connector.read_text(uri),
            "revision": connector.revision(uri),
        }
    if op == "vault.read_json":
        value = _args(args, {"path"}, op)
        uri = _uri(value["path"], "args.path")
        return {
            "path": uri,
            "value": connector.read_json(uri),
            "revision": connector.revision(uri),
        }
    if op == "vault.list":
        value = _args(args, {"path"}, op)
        uri = _uri(value["path"], "args.path", root=True)
        return {"path": uri, "entries": connector.list(uri)}
    if op == "vault.hash":
        value = _args(args, {"path"}, op)
        uri = _uri(value["path"], "args.path")
        return {"path": uri, "revision": connector.revision(uri)}
    if op == "vault.digest_tree":
        value = _args(args, {"path"}, op)
        uri = _uri(value["path"], "args.path", root=True)
        return {"path": uri, **connector.digest_tree(uri)}
    if op == "vault.write_json":
        value = _args(args, {"path", "value"}, op)
        uri = _uri(value["path"], "args.path")
        _mutations(connector)
        with connector.mutation_session():
            return {"path": uri, **connector.write_json(uri, value["value"])}
    if op == "vault.conditional_replace":
        value = _args(args, {"path", "expected_revision", "text"}, op)
        uri = _uri(value["path"], "args.path")
        revision = _text(value["expected_revision"], "args.expected_revision")
        if _REVISION.fullmatch(revision) is None:
            raise Failure(
                "REQUEST_INVALID", "args.expected_revision", "revision is invalid"
            )
        text = _text(value["text"], "args.text")
        _mutations(connector)
        with connector.mutation_session():
            return {
                "path": uri,
                **connector.conditional_replace(uri, revision, text.encode("utf-8")),
            }
    if op == "vault.delete_tree":
        value = _args(
            args,
            {
                "path",
                "expected_digest",
                "projection_sha256",
                "approval",
                "report_revision",
            },
            op,
        )
        uri = _uri(value["path"], "args.path")
        digest, projection, approval, report = (
            _text(value[key], f"args.{key}")
            for key in (
                "expected_digest",
                "projection_sha256",
                "approval",
                "report_revision",
            )
        )
        if approval != f"DELETE_TREE {uri} {digest} {projection}":
            raise Failure(
                "DELETE_APPROVAL_INVALID",
                "args.approval",
                "approval does not bind request",
            )
        _mutations(connector)
        with connector.mutation_session():
            result = connector.delete_tree(
                uri,
                expected_digest=digest,
                projection_sha256=projection,
                approval=approval,
                report_revision=report,
            )
        if result.get("status") == "quarantined-not-erased":
            raise Failure(
                "QUARANTINED_NOT_ERASED",
                str(result.get("quarantine_uri", uri)),
                "tree was quarantined but not durably erased",
            )
        return {"path": uri, **result}
    raise AssertionError(op)


def _pure(op: str, args: Any, connector: Any | None) -> dict[str, Any]:
    if op == "source.normalize_capture":
        value = _args(args, {"capture"}, op)
        try:
            return atlas_source.normalize_capture(value["capture"])
        except (TypeError, ValueError, KeyError) as exc:
            raise Failure("CAPTURE_INVALID", "args.capture", str(exc)) from exc
    if op == "source.worker_schema":
        _args(args, set(), op)
        return _source_worker_schema()
    if op == "url.normalize":
        value = _args(args, {"url"}, op)
        try:
            canonical = atlas_url.normalize_canonical_url(
                _text(value["url"], "args.url")
            )
        except ValueError as exc:
            raise Failure("URL_INVALID", "args.url", str(exc)) from exc
        return {
            "canonical_url": canonical,
            "source_id": atlas_url.source_id_for(canonical),
        }
    if op == "url.resolve_reference":
        value = _args(args, {"base_url", "reference"}, op)
        base_url = _text(value["base_url"], "args.base_url")
        reference = _text(value["reference"], "args.reference")
        try:
            canonical_url, source_id = atlas_url.resolve_reference(base_url, reference)
        except ValueError as exc:
            path = (
                "args.base_url" if str(exc).startswith("base URL") else "args.reference"
            )
            raise Failure("URL_INVALID", path, str(exc)) from exc
        return {"canonical_url": canonical_url, "source_id": source_id}
    if op == "discovery.normalize":
        value = _args(args, {"scope", "candidates", "manifest_rows"}, op)
        try:
            return atlas_discovery.normalize_candidates(
                value["scope"], value["candidates"], value["manifest_rows"]
            )
        except ValueError as exc:
            raise Failure("DISCOVERY_INPUT_INVALID", "args", str(exc)) from exc
    if op == "quality.validate_proposal":
        value = _args(args, {"proposal", "evidence_ledger"}, op)
        _reject(
            atlas_quality.validate_proposal(value["proposal"], value["evidence_ledger"])
        )
        return {}
    if op == "quality.validate_summary":
        value = _args(args, {"artifact_text", "evidence_bundle", "checklist"}, op)
        _reject(
            atlas_quality.validate_summary(
                value["artifact_text"],
                value["evidence_bundle"],
                value["checklist"],
            )
        )
        return {}
    if op == "quality.prepare_calibration":
        value = _args(args, {"fixture_text", "case_ids"}, op)
        try:
            return atlas_quality.prepare_calibration(
                value["fixture_text"], value["case_ids"]
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise Failure("CALIBRATION_INPUT_INVALID", "args", str(exc)) from exc
    if op == "quality.validate_calibration":
        value = _args(args, {"fixture_text", "response_text"}, op)
        _reject(
            atlas_quality.validate_calibration(
                value["fixture_text"], value["response_text"]
            )
        )
        return {}
    if op == "topic.inspect":
        return _topic_inspect(_connector(connector), args)
    if op == "state.reduce":
        value = _args(args, {"documents", "event"}, op)
        try:
            result = atlas_state.reduce_event(value["documents"], value["event"])
        except (TypeError, ValueError) as exc:
            raise Failure("STATE_INPUT_INVALID", "args", str(exc)) from exc
        if not result.ok:
            findings = _owner_findings(result.findings)
            first = findings[0]
            raise Failure(first["code"], first["path"], first["detail"], findings)
        return result.to_dict()
    if op == "state.validate":
        value = _object(args, "args")
        if set(value) not in (set(), {"documents"}):
            raise Failure(
                "ARGUMENTS_INVALID", "args", "state.validate accepts optional documents"
            )
        if "documents" in value:
            documents = value["documents"]
            if type(documents) is not dict:
                raise Failure(
                    "STATE_INPUT_INVALID",
                    "args.documents",
                    "documents must be an object",
                )
            required = {"manifest", "topics", "relations"}
            missing = sorted(required - set(documents))
            if missing:
                raise Failure(
                    "STATE_INPUT_INVALID",
                    f"args.documents.{missing[0]}",
                    "document is missing",
                )
            unknown = sorted(set(documents) - (required | {"vocab"}))
            if unknown:
                raise Failure(
                    "STATE_INPUT_INVALID",
                    f"args.documents.{unknown[0]}",
                    "document key is unknown",
                )
            for name in ("manifest", "topics", "relations", "vocab"):
                if name not in documents:
                    continue
                if not isinstance(documents[name], str):
                    raise Failure(
                        "STATE_INPUT_INVALID",
                        f"args.documents.{name}",
                        "document must be text",
                    )
            try:
                findings = atlas_state.validate_documents(
                    documents["manifest"],
                    documents["topics"],
                    documents["relations"],
                    vocab_text=documents.get("vocab"),
                )
            except (TypeError, ValueError) as exc:
                raise Failure("STATE_INPUT_INVALID", "args", str(exc)) from exc
            _reject(findings)
        else:
            try:
                docs = _documents(_connector(connector))
                docs["vocab"] = _connector(connector).read_text(VOCAB)
                _validate(docs)
            except Failure:
                raise
            except (TypeError, ValueError) as exc:
                raise Failure("STATE_INPUT_INVALID", "args", str(exc)) from exc
        return {}
    if op == "source.render_summary":
        value = _args(args, {"proposal", "caller_context", "source_state"}, op)
        try:
            return {
                "artifact_text": atlas_source.render_summary_proposal(
                    value["proposal"],
                    caller_context=value["caller_context"],
                    source_state=value["source_state"],
                )
            }
        except (TypeError, ValueError) as exc:
            raise Failure("SOURCE_INPUT_INVALID", "args", str(exc)) from exc
    if op == "source.merge_artifact":
        value = _object(args, "args")
        required = {"staged_artifact_text", "evidence_bundle", "event", "source_state"}
        optional = {"living_artifact_text", "fresh_capture"}
        if not required <= set(value) or not set(value) <= required | optional:
            raise Failure(
                "ARGUMENTS_INVALID", "args", "merge-artifact arguments are invalid"
            )
        try:
            return {"artifact_text": atlas_source.merge_artifact(**value)}
        except (TypeError, ValueError) as exc:
            raise Failure("SOURCE_INPUT_INVALID", "args", str(exc)) from exc
    if op == "source.render_route_artifact":
        value = _args(args, {"artifact_text", "route_event", "route_status"}, op)
        try:
            return {
                "artifact_text": atlas_source.render_route_artifact(
                    value["artifact_text"], value["route_event"], value["route_status"]
                )
            }
        except (TypeError, ValueError) as exc:
            raise Failure("SOURCE_INPUT_INVALID", "args", str(exc)) from exc
    raise AssertionError(op)


def _research_prepare(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(
        args,
        set(atlas_research.REQUEST_FIELDS),
        "research.prepare",
    )
    try:
        return {"prepared": atlas_research.prepare(connector, value)}
    except atlas_research.ResearchError as exc:
        raise Failure(exc.code, exc.path, exc.detail) from exc


def _research_execute(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"prepared"}, "research.execute")
    _mutations(connector)
    try:
        return atlas_research.execute(connector, value["prepared"])
    except atlas_research.ResearchError as exc:
        raise Failure(exc.code, exc.path, exc.detail) from exc


def _research_recover(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(
        args,
        {"version", "transaction_id", "request"},
        "research.recover",
    )
    if type(value["version"]) is not int or value["version"] != VERSION:
        raise Failure(
            "RESEARCH_RECOVERY_INVALID",
            "args.version",
            "version must be 1",
        )
    _mutations(connector)
    try:
        return atlas_research.recover(
            connector,
            value["transaction_id"],
            value["request"],
        )
    except atlas_research.ResearchError as exc:
        raise Failure(exc.code, exc.path, exc.detail) from exc


def _operation(
    literal: str,
    handler: Callable[[Any | None, Any], dict[str, Any]],
    *,
    audience: str,
    access: str,
    required: Sequence[str] = (),
    optional: Sequence[str] = (),
    methods: Sequence[str] = (),
    lifecycle_class: str,
    preview: str | None = None,
    recovery: str | None = None,
    contract: str,
    summary: str,
) -> OperationSpec:
    family, verb = literal.split(".", 1)
    return OperationSpec(
        literal=literal,
        handler=handler,
        command=(family, verb.replace("_", "-")),
        audience=audience,
        access=access,
        required=frozenset(required),
        optional=frozenset(optional),
        connector_methods=frozenset(methods),
        lifecycle_class=lifecycle_class,
        preview_operation=preview,
        recovery_operation=recovery,
        contract_anchor=contract,
        summary=summary,
    )


def _repair_request(value: Any, path: str) -> dict[str, Any]:
    request_value = _object(value, path)
    if (
        set(request_value) != {"version", "event"}
        or request_value.get("version") != VERSION
    ):
        raise Failure("REQUEST_INVALID", path, "repair request fields are invalid")
    event = _object(request_value["event"], f"{path}.event")
    if event.get("type") not in {
        "repair-table-placement",
        "repair-relation-notes",
    }:
        raise Failure(
            "REQUEST_INVALID", f"{path}.event.type", "repair event type is invalid"
        )
    return {"version": VERSION, "event": dict(event)}


def _repair_event_record(request_value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "event_type": "repair",
        "source_id": "repair",
        "promotion": None,
        "event": dict(request_value["event"]),
        "route_decision": None,
    }


def _repair_snapshot(
    connector: Any,
    path: str,
    *,
    code: str = "REPAIR_INPUT_INVALID",
) -> tuple[dict[str, str], dict[str, str]]:
    docs: dict[str, str] = {}
    revisions: dict[str, str] = {}
    try:
        for name, uri in (
            ("manifest", MANIFEST),
            ("topics", TOPICS),
            ("relations", RELATIONS),
        ):
            raw = connector.read_bytes(uri)
            revision = connector.revision(uri)
            if not isinstance(raw, bytes) or revision != "sha256:" + _hash(raw):
                raise ValueError("registry bytes and revision disagree")
            docs[name] = raw.decode("utf-8")
            revisions[uri] = revision
    except (FileNotFoundError, TypeError, ValueError, UnicodeDecodeError) as exc:
        raise Failure(code, path, str(exc)) from exc
    return docs, revisions


def _validate_repair_result(connector: Any, path: str) -> None:
    docs, _ = _repair_snapshot(
        connector,
        path,
        code="FRAMEWORK_INTERNAL_ERROR",
    )
    findings = atlas_state.validate_documents(
        docs["manifest"], docs["topics"], docs["relations"]
    )
    if findings:
        raise Failure(
            "FRAMEWORK_INTERNAL_ERROR",
            path,
            "committed repair failed post-validation",
            findings=[
                _finding(
                    "FRAMEWORK_INTERNAL_ERROR",
                    path,
                    "committed repair failed post-validation",
                ),
                *_owner_findings(findings),
            ],
        )


def _repair_execute(connector: Any, args: Any) -> dict[str, Any]:
    request_value = _repair_request(args, "args")
    _mutations(connector)
    with connector.mutation_session():
        docs, revisions = _repair_snapshot(connector, "snapshot")
        reduction = atlas_state.reduce_event(docs, request_value["event"])
        if not reduction.ok:
            _reject(reduction.findings)
        targets = [
            {
                "path": _doc_uri(name),
                "expected_revision": revisions[_doc_uri(name)],
                "text": replacement,
            }
            for name, replacement in reduction.documents.items()
            if replacement != docs[name]
        ]
        if not targets:
            return {
                "state": "terminal",
                "outcome": "unchanged",
                "reason": "repair has no changed targets",
            }
        result = _tx_execute(
            connector,
            {
                "event_record": _repair_event_record(request_value),
                "targets": targets,
            },
        )
        result["status"] = result["receipt"]["status"]
        if result["status"] in {"applied", "no-op"}:
            _validate_repair_result(connector, "transaction.execute")
        return result


def _repair_recover(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"version", "transaction_id", "request"}, "transaction.recover")
    if value["version"] != VERSION:
        raise Failure("REQUEST_INVALID", "args.version", "version must be 1")
    transaction_id = _text(value["transaction_id"], "args.transaction_id")
    if _TX_ID.fullmatch(transaction_id) is None:
        raise Failure(
            "TRANSACTION_UNKNOWN", "args.transaction_id", "transaction ID is invalid"
        )
    request_value = _repair_request(value["request"], "args.request")
    _mutations(connector)
    with connector.mutation_session():
        port = _Port(connector)
        record, _ = _load_plan(port, transaction_id)
        if record != _repair_event_record(request_value):
            raise Failure(
                "TRANSACTION_REQUEST_MISMATCH",
                "args.request",
                "repair request differs from the immutable transaction",
            )
        result = _tx_recover(connector, {"transaction_id": transaction_id})
        status = result["receipt"]["status"]
        if status in {"applied", "no-op"}:
            _validate_repair_result(connector, "transaction.recover")
        result["status"] = status
        return result


_CATALOG = tuple(
    sorted(
        (
            _operation(
                "vault.read",
                lambda connector, args: _vault(connector, "vault.read", args),
                audience="lifecycle",
                access="read",
                required=("path",),
                methods=("read_text", "revision"),
                lifecycle_class="query",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="Read one UTF-8 vault artifact and revision.",
            ),
            _operation(
                "vault.read_json",
                lambda connector, args: _vault(connector, "vault.read_json", args),
                audience="lifecycle",
                access="read",
                required=("path",),
                methods=("read_json", "revision"),
                lifecycle_class="query",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="Read one JSON vault artifact and revision.",
            ),
            _operation(
                "vault.list",
                lambda connector, args: _vault(connector, "vault.list", args),
                audience="lifecycle",
                access="read",
                required=("path",),
                methods=("list",),
                lifecycle_class="query",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="List one bounded logical vault tree.",
            ),
            _operation(
                "vault.hash",
                lambda connector, args: _vault(connector, "vault.hash", args),
                audience="lifecycle",
                access="read",
                required=("path",),
                methods=("revision",),
                lifecycle_class="query",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="Read one full-byte vault revision.",
            ),
            _operation(
                "vault.digest_tree",
                lambda connector, args: _vault(connector, "vault.digest_tree", args),
                audience="lifecycle",
                access="read",
                required=("path",),
                methods=("digest_tree",),
                lifecycle_class="preview",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="Digest one bounded logical vault tree.",
            ),
            _operation(
                "vault.write_json",
                lambda connector, args: _vault(connector, "vault.write_json", args),
                audience="internal",
                access="write",
                required=("path", "value"),
                methods=("mutation_session", "conditional_replace", "write_json"),
                lifecycle_class="execute",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="Create one canonical JSON vault artifact.",
            ),
            _operation(
                "vault.conditional_replace",
                lambda connector, args: _vault(
                    connector, "vault.conditional_replace", args
                ),
                audience="internal",
                access="write",
                required=("path", "expected_revision", "text"),
                methods=("mutation_session", "conditional_replace"),
                lifecycle_class="execute",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="Conditionally replace one UTF-8 vault artifact.",
            ),
            _operation(
                "vault.delete_tree",
                lambda connector, args: _vault(connector, "vault.delete_tree", args),
                audience="internal",
                access="write",
                required=(
                    "path",
                    "expected_digest",
                    "projection_sha256",
                    "approval",
                    "report_revision",
                ),
                methods=(
                    "mutation_session",
                    "conditional_replace",
                    "delete_tree",
                ),
                lifecycle_class="execute",
                preview="vault.digest_tree",
                contract="markdown-registry-contracts.md#atlas-tool-facade-interface",
                summary="Delete one approval-bound logical tree.",
            ),
            _operation(
                "url.normalize",
                lambda connector, args: _pure("url.normalize", args, connector),
                audience="lifecycle",
                access="pure",
                required=("url",),
                lifecycle_class="transform",
                contract="markdown-registry-contracts.md#canonical-url-normalization",
                summary="Normalize one canonical source URL.",
            ),
            _operation(
                "url.resolve_reference",
                lambda connector, args: _pure("url.resolve_reference", args, connector),
                audience="lifecycle",
                access="pure",
                required=("base_url", "reference"),
                lifecycle_class="transform",
                contract="markdown-registry-contracts.md#reference-resolution",
                summary="Resolve one source reference against a base URL.",
            ),
            _operation(
                "discovery.normalize",
                lambda connector, args: _pure("discovery.normalize", args, connector),
                audience="internal",
                access="pure",
                required=("scope", "candidates", "manifest_rows"),
                lifecycle_class="transform",
                contract="markdown-registry-contracts.md#source-inventory-and-preparation",
                summary="Normalize a bounded discovery candidate set.",
            ),
            _operation(
                "quality.validate_proposal",
                lambda connector, args: _pure(
                    "quality.validate_proposal", args, connector
                ),
                audience="lifecycle",
                access="pure",
                required=("proposal", "evidence_ledger"),
                lifecycle_class="validate",
                contract="source-summary-quality-guide.md",
                summary="Validate one evidence-bound source proposal.",
            ),
            _operation(
                "quality.validate_summary",
                lambda connector, args: _pure(
                    "quality.validate_summary", args, connector
                ),
                audience="lifecycle",
                access="pure",
                required=("artifact_text", "evidence_bundle", "checklist"),
                lifecycle_class="validate",
                contract="source-summary-quality-guide.md",
                summary="Validate one rendered source summary.",
            ),
            _operation(
                "quality.prepare_calibration",
                lambda connector, args: _pure(
                    "quality.prepare_calibration", args, connector
                ),
                audience="internal",
                access="pure",
                required=("fixture_text", "case_ids"),
                lifecycle_class="maintenance",
                contract="source-summary-quality-guide.md",
                summary="Prepare bounded quality calibration cases.",
            ),
            _operation(
                "quality.validate_calibration",
                lambda connector, args: _pure(
                    "quality.validate_calibration", args, connector
                ),
                audience="internal",
                access="pure",
                required=("fixture_text", "response_text"),
                lifecycle_class="maintenance",
                contract="source-summary-quality-guide.md",
                summary="Validate one quality calibration response.",
            ),
            _operation(
                "state.validate",
                lambda connector, args: _pure("state.validate", args, connector),
                audience="lifecycle",
                access="read",
                optional=("documents",),
                methods=("read_text",),
                lifecycle_class="validate",
                contract="markdown-registry-contracts.md#canonical-registry-tables",
                summary="Validate supplied or bound canonical registries.",
            ),
            _operation(
                "state.reduce",
                lambda connector, args: _pure("state.reduce", args, connector),
                audience="internal",
                access="pure",
                required=("documents", "event"),
                lifecycle_class="transform",
                contract="markdown-registry-contracts.md#reference-reducer-interface",
                summary="Reduce one canonical registry event.",
            ),
            _operation(
                "topic.inspect",
                lambda connector, args: _topic_inspect(connector, args),
                audience="lifecycle",
                access="consistent-read",
                required=("topic_id", "purpose"),
                methods=("read_text", "consistent_read"),
                lifecycle_class="inspect",
                contract="markdown-registry-contracts.md#purpose-specific-topic-inspection",
                summary="Inspect one topic for answer, research, or refresh.",
            ),
            _operation(
                "source.normalize_capture",
                lambda connector, args: _pure(
                    "source.normalize_capture", args, connector
                ),
                audience="lifecycle",
                access="pure",
                required=("capture",),
                lifecycle_class="transform",
                contract="source-capture-mapping.md",
                summary="Normalize one complete transport-neutral capture.",
            ),
            _operation(
                "source.worker_schema",
                lambda connector, args: _pure("source.worker_schema", args, connector),
                audience="lifecycle",
                access="pure",
                lifecycle_class="query",
                contract="markdown-registry-contracts.md#source-proposals",
                summary="Return the strict source worker schema.",
            ),
            _operation(
                "source.lookup",
                lambda connector, args: _source_lookup(connector, args),
                audience="lifecycle",
                access="read",
                required=("url",),
                methods=("read_bytes",),
                lifecycle_class="query",
                contract="markdown-registry-contracts.md#source-presence-lookup",
                summary="Look up one canonical source identity.",
            ),
            _operation(
                "source.inventory",
                lambda connector, args: _source_inventory(connector, args),
                audience="lifecycle",
                access="read",
                required=("intent", "checked_on", "inputs"),
                methods=("read_bytes",),
                lifecycle_class="inspect",
                contract="markdown-registry-contracts.md#source-inventory-and-preparation",
                summary="Classify one explicit source input set.",
            ),
            _operation(
                "source.candidates_for_topic",
                lambda connector, args: _source_candidates_for_topic(connector, args),
                audience="lifecycle",
                access="consistent-read",
                required=("topic_id", "named_urls"),
                optional=("source_id",),
                methods=("read_text", "consistent_read"),
                lifecycle_class="inspect",
                contract="markdown-registry-contracts.md#topic-scoped-source-candidates",
                summary="Discover bounded active-source candidates for one topic.",
            ),
            _operation(
                "source.prepare",
                lambda connector, args: _source_prepare(connector, args),
                audience="lifecycle",
                access="consistent-read",
                required=("mode",),
                optional=("identity", "worker", "artifact_uri", "evidence_uri"),
                methods=("read_text", "consistent_read"),
                lifecycle_class="prepare",
                contract="markdown-registry-contracts.md#source-inventory-and-preparation",
                summary="Prepare one source transaction without writing.",
            ),
            _operation(
                "source.prepare_route",
                lambda connector, args: _source_prepare_route(connector, args),
                audience="lifecycle",
                access="consistent-read",
                required=(
                    "binding",
                    "checked_on",
                    "expected_revisions",
                    "decision",
                ),
                methods=("consistent_read",),
                lifecycle_class="prepare",
                contract="markdown-registry-contracts.md#prepared-route-transaction",
                summary="Prepare one route transaction without writing.",
            ),
            _operation(
                "source.snapshot_active",
                lambda connector, args: _snapshot(connector, args),
                audience="lifecycle",
                access="write",
                methods=(
                    "read_text",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                ),
                lifecycle_class="execute",
                contract="markdown-registry-contracts.md#active-source-snapshot",
                summary="Persist one active-source snapshot receipt.",
            ),
            _operation(
                "source.render_summary",
                lambda connector, args: _pure("source.render_summary", args, connector),
                audience="internal",
                access="pure",
                required=("proposal", "caller_context", "source_state"),
                lifecycle_class="transform",
                contract="markdown-registry-contracts.md#source-proposals",
                summary="Render one canonical source summary.",
            ),
            _operation(
                "source.merge_artifact",
                lambda connector, args: _pure("source.merge_artifact", args, connector),
                audience="internal",
                access="pure",
                required=(
                    "staged_artifact_text",
                    "evidence_bundle",
                    "event",
                    "source_state",
                ),
                optional=("living_artifact_text", "fresh_capture"),
                lifecycle_class="transform",
                contract="markdown-registry-contracts.md#source-proposals",
                summary="Merge one source artifact with living content.",
            ),
            _operation(
                "source.render_route_artifact",
                lambda connector, args: _pure(
                    "source.render_route_artifact", args, connector
                ),
                audience="internal",
                access="pure",
                required=("artifact_text", "route_event", "route_status"),
                lifecycle_class="transform",
                contract="markdown-registry-contracts.md#source-proposals",
                summary="Render one route projection into a source artifact.",
            ),
            _operation(
                "migration.prepare_source_taxonomy_remediation",
                lambda connector, args: (
                    _migration_prepare_source_taxonomy_remediation(
                        connector,
                        args,
                    )
                ),
                audience="lifecycle",
                access="consistent-read",
                methods=("binding_identity", "read_text", "consistent_read"),
                lifecycle_class="prepare",
                contract="markdown-registry-contracts.md#source-taxonomy-remediation-candidate-and-migration",
                summary="Preview the fixed source-taxonomy remediation.",
            ),
            _operation(
                "migration.apply_source_taxonomy_remediation",
                lambda connector, args: (
                    _migration_apply_source_taxonomy_remediation(
                        connector,
                        args,
                    )
                ),
                audience="lifecycle",
                access="write",
                required=("instance_id", "candidate_sha256", "approval"),
                methods=(
                    "binding_identity",
                    "read_text",
                    "read_bytes",
                    "consistent_read",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="execute",
                preview="migration.prepare_source_taxonomy_remediation",
                recovery="migration.recover_source_taxonomy_remediation",
                contract="markdown-registry-contracts.md#source-taxonomy-remediation-candidate-and-migration",
                summary="Apply the fixed source-taxonomy remediation.",
            ),
            _operation(
                "migration.recover_source_taxonomy_remediation",
                lambda connector, args: (
                    _migration_recover_source_taxonomy_remediation(
                        connector,
                        args,
                    )
                ),
                audience="lifecycle",
                access="write",
                required=("version", "transaction_id", "request"),
                methods=(
                    "binding_identity",
                    "read_bytes",
                    "consistent_read",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="recover",
                contract="markdown-registry-contracts.md#source-taxonomy-remediation-candidate-and-migration",
                summary="Recover one source-taxonomy remediation transaction.",
            ),
            _operation(
                "migration.prepare_taxonomy_backfill",
                lambda connector, args: _migration_prepare_taxonomy_backfill(
                    connector, args
                ),
                audience="lifecycle",
                access="consistent-read",
                methods=("binding_identity", "read_text", "consistent_read"),
                lifecycle_class="prepare",
                contract="markdown-registry-contracts.md#taxonomy-closure-candidate-and-migration",
                summary="Preview one candidate-locked taxonomy backfill.",
            ),
            _operation(
                "migration.apply_taxonomy_backfill",
                lambda connector, args: _migration_apply_taxonomy_backfill(
                    connector, args
                ),
                audience="lifecycle",
                access="write",
                required=("instance_id", "candidate_sha256", "approval"),
                methods=(
                    "binding_identity",
                    "read_text",
                    "read_bytes",
                    "consistent_read",
                    "mutation_session",
                    "conditional_replace",
                ),
                lifecycle_class="execute",
                preview="migration.prepare_taxonomy_backfill",
                contract="markdown-registry-contracts.md#taxonomy-closure-candidate-and-migration",
                summary="Apply one approved VOCAB taxonomy backfill.",
            ),
            _operation(
                "migration.prepare_vocabulary_domain_insertion",
                lambda connector, args: (
                    _migration_prepare_vocabulary_domain_insertion(
                        connector,
                        args,
                    )
                ),
                audience="lifecycle",
                access="consistent-read",
                required=("domain_id",),
                methods=("binding_identity", "consistent_read"),
                lifecycle_class="prepare",
                contract="markdown-registry-contracts.md#vocabulary-domain-insertion-candidate-and-migration",
                summary="Preview one canonical top-level vocabulary domain insertion.",
            ),
            _operation(
                "migration.apply_vocabulary_domain_insertion",
                lambda connector, args: (
                    _migration_apply_vocabulary_domain_insertion(
                        connector,
                        args,
                    )
                ),
                audience="lifecycle",
                access="write",
                required=(
                    "domain_id",
                    "instance_id",
                    "candidate_sha256",
                    "approval",
                ),
                methods=(
                    "binding_identity",
                    "consistent_read",
                    "read_bytes",
                    "mutation_session",
                    "conditional_replace",
                ),
                lifecycle_class="execute",
                preview="migration.prepare_vocabulary_domain_insertion",
                contract="markdown-registry-contracts.md#vocabulary-domain-insertion-candidate-and-migration",
                summary="Apply one approved top-level vocabulary domain insertion.",
            ),
            _operation(
                "migration.prepare_vocabulary_subdomain_insertion",
                lambda connector, args: (
                    _migration_prepare_vocabulary_subdomain_insertion(
                        connector,
                        args,
                    )
                ),
                audience="lifecycle",
                access="consistent-read",
                required=("parent_domain_id", "subdomain_id"),
                methods=("binding_identity", "consistent_read"),
                lifecycle_class="prepare",
                contract="markdown-registry-contracts.md#vocabulary-subdomain-insertion-candidate-and-migration",
                summary="Preview one canonical parent-bound vocabulary subdomain insertion.",
            ),
            _operation(
                "migration.apply_vocabulary_subdomain_insertion",
                lambda connector, args: (
                    _migration_apply_vocabulary_subdomain_insertion(
                        connector,
                        args,
                    )
                ),
                audience="lifecycle",
                access="write",
                required=(
                    "approval",
                    "candidate_sha256",
                    "instance_id",
                    "parent_domain_id",
                    "subdomain_id",
                ),
                methods=(
                    "binding_identity",
                    "consistent_read",
                    "read_bytes",
                    "mutation_session",
                    "conditional_replace",
                ),
                lifecycle_class="execute",
                preview="migration.prepare_vocabulary_subdomain_insertion",
                contract="markdown-registry-contracts.md#vocabulary-subdomain-insertion-candidate-and-migration",
                summary="Apply one approved parent-bound vocabulary subdomain insertion.",
            ),
            _operation(
                "transaction.execute",
                lambda connector, args: _tx_execute(connector, args),
                audience="internal",
                access="write",
                optional=("event_record", "targets", "version", "event"),
                methods=(
                    "read_bytes",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="execute",
                recovery="transaction.recover",
                contract="markdown-registry-contracts.md#generic-transactions-topic-creation-and-refresh",
                summary="Execute one generic owner-bound transaction.",
            ),
            _operation(
                "transaction.recover",
                lambda connector, args: _tx_recover(connector, args),
                audience="internal",
                access="write",
                required=("transaction_id",),
                optional=("version", "request"),
                methods=(
                    "read_bytes",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="recover",
                contract="markdown-registry-contracts.md#generic-transactions-topic-creation-and-refresh",
                summary="Recover one generic transaction.",
            ),
            _operation(
                "transaction.successor",
                lambda connector, args: _tx_successor(connector, args),
                audience="internal",
                access="write",
                required=("transaction_id",),
                methods=(
                    "read_bytes",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="recover",
                contract="markdown-registry-contracts.md#generic-transactions-topic-creation-and-refresh",
                summary="Create the sole eligible generic successor.",
            ),
            _operation(
                "index.create_topic",
                lambda connector, args: _index_create(connector, args),
                audience="lifecycle",
                access="write",
                required=tuple(atlas_index.REQUEST_FIELDS),
                methods=(
                    "read_bytes",
                    "read_text",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="execute",
                recovery="index.recover_topic",
                contract="markdown-registry-contracts.md#generic-transactions-topic-creation-and-refresh",
                summary="Create or confirm one canonical research topic.",
            ),
            _operation(
                "index.recover_topic",
                lambda connector, args: _index_recover(connector, args),
                audience="lifecycle",
                access="write",
                required=("version", "transaction_id", "request"),
                methods=(
                    "read_bytes",
                    "read_text",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="recover",
                contract="markdown-registry-contracts.md#generic-transactions-topic-creation-and-refresh",
                summary="Recover one exact topic creation request.",
            ),
            _operation(
                "research.prepare",
                lambda connector, args: _research_prepare(connector, args),
                audience="lifecycle",
                access="consistent-read",
                required=tuple(atlas_research.REQUEST_FIELDS),
                methods=("read_text", "consistent_read"),
                lifecycle_class="prepare",
                contract="markdown-registry-contracts.md#research-publication",
                summary="Prepare one exact four-target research publication.",
            ),
            _operation(
                "research.execute",
                lambda connector, args: _research_execute(connector, args),
                audience="lifecycle",
                access="write",
                required=("prepared",),
                methods=(
                    "read_text",
                    "consistent_read",
                    "read_bytes",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="execute",
                preview="research.prepare",
                recovery="research.recover",
                contract="markdown-registry-contracts.md#research-publication",
                summary="Execute one prepared research publication.",
            ),
            _operation(
                "research.recover",
                lambda connector, args: _research_recover(connector, args),
                audience="lifecycle",
                access="write",
                required=("version", "transaction_id", "request"),
                methods=(
                    "read_bytes",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="recover",
                contract="markdown-registry-contracts.md#research-publication",
                summary="Recover one exact research publication request.",
            ),
            _operation(
                "refresh.execute",
                lambda connector, args: _refresh_execute(connector, args),
                audience="lifecycle",
                access="write",
                required=("projection", "pass_text", "index_text"),
                methods=(
                    "read_bytes",
                    "read_text",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="execute",
                recovery="refresh.recover",
                contract="markdown-registry-contracts.md#quick-answer-freshness",
                summary="Execute one exact topic refresh.",
            ),
            _operation(
                "refresh.recover",
                lambda connector, args: _refresh_recover(connector, args),
                audience="lifecycle",
                access="write",
                required=("projection", "pass_text", "index_text"),
                methods=(
                    "read_bytes",
                    "read_text",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="recover",
                contract="markdown-registry-contracts.md#quick-answer-freshness",
                summary="Recover one exact topic refresh.",
            ),
            _operation(
                "effect.execute",
                lambda connector, args: _effect_execute(connector, args, recover=False),
                audience="lifecycle",
                access="write",
                required=(
                    "authority",
                    "checks",
                    "allowed_target_paths",
                    "members",
                    "context",
                    "transactions",
                    "no_write_code",
                    "receipt_root",
                ),
                methods=(
                    "read_bytes",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="execute",
                recovery="effect.recover",
                contract="operating-cadence-and-guardrails.md",
                summary="Execute one approved aggregate effect.",
            ),
            _operation(
                "effect.recover",
                lambda connector, args: _effect_execute(connector, args, recover=True),
                audience="lifecycle",
                access="write",
                required=(
                    "authority",
                    "checks",
                    "allowed_target_paths",
                    "members",
                    "context",
                    "transactions",
                    "no_write_code",
                    "receipt_root",
                ),
                methods=(
                    "read_bytes",
                    "revision",
                    "list",
                    "mutation_session",
                    "conditional_replace",
                    "delete",
                ),
                lifecycle_class="recover",
                contract="operating-cadence-and-guardrails.md",
                summary="Recover one approved aggregate effect.",
            ),
        ),
        key=lambda spec: spec.literal,
    )
)
_OPERATION_BY_LITERAL = MappingProxyType({spec.literal: spec for spec in _CATALOG})
if len(_OPERATION_BY_LITERAL) != len(_CATALOG):
    raise RuntimeError("operation catalog contains duplicate literals")


def operation_specs() -> tuple[OperationSpec, ...]:
    return _CATALOG


def _dispatch(op: str, args: Any, connector: Any | None) -> dict[str, Any]:
    spec = _OPERATION_BY_LITERAL[op]
    active = connector
    if spec.access != "pure":
        active = _connector(active)
        _require_connector_methods(
            active,
            tuple(spec.connector_methods),
            write=spec.access == "write",
        )
    return spec.handler(active, args)


def _transaction_id_from_path(path: str) -> str | None:
    match = re.search(r"(?:^|/)([0-9a-f]{16}-a[0-9]{6})(?:/|$)", path)
    return None if match is None else match.group(1)


def _failure_recovery(
    op: str | None,
    exc: Failure,
    args: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    codes = {exc.code}
    if exc.findings is not None:
        codes.update(item.get("code", "") for item in exc.findings)
    if (op == "source.candidates_for_topic" and "SOURCE_TAXONOMY_INVALID" in codes) or (
        op == "index.create_topic" and "TOPIC_VOCABULARY_MIGRATION_REQUIRED" in codes
    ):
        return {
            "migration_preview": {
                "operation": "migration.prepare_taxonomy_backfill",
                "args": {},
            }
        }, None
    if "TRANSACTION_RECOVERABLE" not in codes:
        return None, None
    transaction_id = _transaction_id_from_path(exc.path)
    if (
        op
        in {
            "migration.apply_source_taxonomy_remediation",
            "migration.recover_source_taxonomy_remediation",
        }
        and transaction_id
        and isinstance(args, Mapping)
    ):
        request = (
            args.get("request")
            if op == "migration.recover_source_taxonomy_remediation"
            else args
        )
        if isinstance(request, Mapping):
            return exc.result or {"transaction_id": transaction_id}, {
                "operation": "migration.recover_source_taxonomy_remediation",
                "args": {
                    "version": VERSION,
                    "transaction_id": transaction_id,
                    "request": dict(request),
                },
            }
    if op in {"transaction.execute", "transaction.successor"} and transaction_id:
        recovery_args: dict[str, Any] = {"transaction_id": transaction_id}
        if (
            op == "transaction.execute"
            and isinstance(args, Mapping)
            and set(args) == {"version", "event"}
        ):
            recovery_args = {
                "version": VERSION,
                "transaction_id": transaction_id,
                "request": dict(args),
            }
        recovery = {
            "operation": "transaction.recover",
            "args": recovery_args,
        }
        return {"transaction_id": transaction_id}, recovery
    if op == "index.create_topic" and transaction_id and isinstance(args, Mapping):
        recovery = {
            "operation": "index.recover_topic",
            "args": {
                "version": VERSION,
                "transaction_id": transaction_id,
                "request": dict(args),
            },
        }
        return {"transaction_id": transaction_id}, recovery
    if op == "refresh.execute" and isinstance(args, Mapping):
        return None, {"operation": "refresh.recover", "args": dict(args)}
    if op == "effect.execute" and isinstance(args, Mapping):
        return None, {"operation": "effect.recover", "args": dict(args)}
    return None, None


def _exception(
    op: str | None,
    exc: BaseException,
    args: Any = None,
) -> dict[str, Any]:
    if isinstance(exc, Failure):
        result, recovery = _failure_recovery(op, exc, args)
        findings = (
            exc.findings
            if exc.findings is not None
            else [_finding(exc.code, exc.path, exc.detail)]
        )
        return _response(
            op,
            result=result,
            findings=findings,
            recovery=recovery,
        )
    if isinstance(exc, ConnectorMutationUnavailableError):
        return _error(
            op, "MUTATION_UNAVAILABLE", "connector", "mutations are unavailable"
        )
    if isinstance(exc, ConnectorBindingError):
        return _error(
            op, "BINDING_INVALID", "connector", "connector binding is invalid"
        )
    if isinstance(exc, ConnectorConflictError):
        return _error(
            op,
            "REVISION_STALE",
            op or "request",
            "connector compare-and-swap conflicted",
        )
    if isinstance(exc, (ConnectorIOError, ConnectorDurabilityError)):
        return _error(op, "IO_FAILURE", op or "request", "connector I/O failed")
    if isinstance(exc, atlas_transaction.TransactionRecordError):
        return _error(
            op,
            "TRANSACTION_RECORD_INVALID",
            _record_path(exc.path),
            exc.detail,
        )
    if isinstance(exc, atlas_transaction.TransactionTargetConflict):
        return _error(
            op,
            "MANUAL_CONFLICT",
            _record_path(exc.path),
            exc.detail,
        )
    if isinstance(exc, OSError):
        return _error(op, "IO_FAILURE", op or "request", "connector I/O failed")
    if isinstance(
        exc,
        (
            atlas_cli.JsonInputError,
            ValueError,
            TypeError,
            KeyError,
            UnicodeError,
            json.JSONDecodeError,
        ),
    ):
        message = str(exc)
        if "mutation_unavailable" in message:
            return _error(
                op, "MUTATION_UNAVAILABLE", "connector", "mutations are unavailable"
            )
        if "revision conflict" in message:
            return _error(op, "REVISION_STALE", op or "request", message)
        if "delete approval" in message:
            return _error(op, "DELETE_APPROVAL_INVALID", "args.approval", message)
        if "tree digest mismatch" in message:
            return _error(op, "DELETE_DIGEST_STALE", "args.expected_digest", message)
        return _error(op, "REQUEST_INVALID", op or "request", message)
    return _error(
        op,
        "FRAMEWORK_INTERNAL_ERROR",
        op or "request",
        "unexpected Atlas framework failure",
    )


def _operation_capability(spec: OperationSpec) -> dict[str, Any]:
    return {
        "operation": spec.literal,
        "command": " ".join(spec.command),
        "audience": spec.audience,
        "access": spec.access,
        "required": sorted(spec.required),
        "optional": sorted(spec.optional),
        "connector_methods": sorted(spec.connector_methods),
        "lifecycle_class": spec.lifecycle_class,
        "preview_operation": spec.preview_operation,
        "recovery_operation": spec.recovery_operation,
        "contract_anchor": spec.contract_anchor,
        "summary": spec.summary,
    }


def capabilities(
    connector: Any | None = None,
    *,
    include_internal: bool = False,
) -> dict[str, Any]:
    try:
        selected = [
            spec
            for spec in _CATALOG
            if include_internal or spec.audience == "lifecycle"
        ]
        binding: dict[str, Any] | None = None
        if connector is not None:
            values = _capabilities(connector)
            _require_connector_methods(connector, ("binding_identity",), write=False)
            identity = connector.binding_identity()
            adapter = values.get("adapter")
            if (
                not isinstance(identity, Mapping)
                or set(identity) != {"instance_id", "binding_revision"}
                or not isinstance(identity.get("instance_id"), str)
                or not isinstance(identity.get("binding_revision"), str)
                or not isinstance(adapter, str)
                or not adapter
            ):
                raise Failure(
                    "BINDING_INVALID",
                    "connector",
                    "binding identity is invalid",
                )
            declared = set(values["operations"])
            selected = [
                spec
                for spec in selected
                if set(spec.connector_methods) <= declared
                and _connector_methods_available(connector, spec.connector_methods)
            ]
            binding = {
                "instance_id": identity["instance_id"],
                "binding_revision": identity["binding_revision"],
                "adapter": adapter,
                "logical_root": ROOT,
                "mutation_state": (
                    "available"
                    if {"mutation_session", "conditional_replace"} <= declared
                    else "unavailable"
                ),
            }
        return _response(
            "capabilities",
            {
                "binding": binding,
                "operations": [_operation_capability(spec) for spec in selected],
            },
        )
    except Exception as exc:
        return _exception("capabilities", exc)


def _migration_result_response(
    op: str,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    value = dict(result)
    state = value.get("state")
    if state == "applied":
        return _response(op, value, disposition="completed")
    if state in {"aborted", "rolled-back"}:
        return _response(op, value, disposition="no-write")
    if state == "manual-conflict":
        findings = value.get("findings")
        if not isinstance(findings, list) or not findings:
            findings = [
                _finding(
                    "MIGRATION_EFFECT_UNKNOWN",
                    VOCAB,
                    "migration effect requires manual reconciliation",
                )
            ]
        return _response(
            op,
            value,
            findings=findings,
            disposition="manual-intervention",
            recovery=None,
        )
    return _error(
        op,
        "OWNER_OUTPUT_INVALID",
        op,
        "migration returned an invalid terminal state",
        result=value,
    )


def _result_response(op: str, result: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(result)
    if op in {
        "migration.prepare_source_taxonomy_remediation",
        "migration.prepare_vocabulary_domain_insertion",
        "migration.prepare_vocabulary_subdomain_insertion",
    }:
        return _response(op, value, disposition="completed")
    if op in {
        "migration.apply_source_taxonomy_remediation",
        "migration.recover_source_taxonomy_remediation",
        "migration.apply_taxonomy_backfill",
        "migration.apply_vocabulary_domain_insertion",
        "migration.apply_vocabulary_subdomain_insertion",
    }:
        return _migration_result_response(op, value)
    status = value.get("status")
    if status == "manual-conflict":
        return _error(
            op,
            "MANUAL_CONFLICT",
            op,
            "operation requires manual reconciliation",
            result=value,
        )
    if (
        status in {"aborted", "rolled-back"}
        or value.get("state") in {"rejected", "needs-revision", "terminal", "no-op"}
        or value.get("outcome")
        in {"no-write", "unchanged", "active-not-due", "archived"}
    ):
        return _response(op, value, disposition="no-write")
    return _response(op, value)


def execute(request: Any, connector: Any | None = None) -> dict[str, Any]:
    if type(request) is not dict:
        return _error(None, "REQUEST_INVALID", "request", "expected an object")
    op_value = request.get("op")
    safe_op = op_value if isinstance(op_value, str) else None
    try:
        atlas_cli.encode(request)
    except atlas_cli.JsonInputError:
        return _error(
            safe_op,
            "REQUEST_INVALID",
            "request",
            "request contains invalid machine JSON data",
        )
    if set(request) != {"version", "op", "args"}:
        return _error(
            safe_op,
            "REQUEST_INVALID",
            "request",
            "expected exactly version, op, args",
        )
    if type(request.get("version")) is not int or (
        request.get("version") != atlas_cli.VERSION
    ):
        return _error(
            safe_op,
            "VERSION_UNSUPPORTED",
            "version",
            f"expected version {atlas_cli.VERSION}",
        )
    if not isinstance(request.get("op"), str):
        return _error(
            None,
            "REQUEST_INVALID",
            "op",
            "operation must be text",
        )
    if type(request.get("args")) is not dict:
        return _error(
            safe_op,
            "REQUEST_INVALID",
            "args",
            "expected an object",
        )
    op = request["op"]
    if op not in _OPERATION_BY_LITERAL:
        return _error(
            op, "OP_UNKNOWN", op, "operation is not an Atlas facade capability"
        )
    spec = _OPERATION_BY_LITERAL[op]
    fields = set(request["args"])
    missing = sorted(spec.required - fields)
    unknown = sorted(fields - spec.required - spec.optional)
    if missing:
        return _error(
            op,
            "ARGUMENTS_INVALID",
            f"args.{missing[0]}",
            "required argument is missing",
        )
    if unknown:
        return _error(
            op,
            "ARGUMENTS_INVALID",
            f"args.{unknown[0]}",
            "argument is not supported",
        )
    try:
        result = _dispatch(op, request["args"], connector)
        return _result_response(op, result)
    except Exception as exc:
        return _exception(op, exc, request["args"])


def _exit(response: Mapping[str, Any]) -> int:
    return atlas_cli.exit_code(response)


def _root_help() -> str:
    families = sorted(
        {spec.command[0] for spec in _CATALOG if spec.audience == "lifecycle"}
    )
    return "\n".join(
        (
            "Atlas provider-neutral façade",
            "",
            "Usage:",
            "  atlas_tool.py [--profile PATH] [--read-only] capabilities [--all]",
            "  atlas_tool.py [--profile PATH] [--read-only] call --input PATH|-",
            "  atlas_tool.py [--profile PATH] [--read-only] FAMILY VERB --input PATH|-",
            "",
            "Lifecycle families: " + ", ".join(families),
        )
    )


def _family_help(family: str) -> str:
    specs = [
        spec
        for spec in _CATALOG
        if spec.audience == "lifecycle" and spec.command[0] == family
    ]
    lines = [f"Atlas {family} lifecycle commands", "", "Commands:"]
    if not specs:
        lines.append("  (none)")
    for spec in specs:
        lines.append(
            f"  {spec.command[0]} {spec.command[1]} --input PATH|-  {spec.summary}"
        )
    return "\n".join(lines)


def _command_help(spec: OperationSpec) -> str:
    required = ", ".join(sorted(spec.required)) or "(none)"
    optional = ", ".join(sorted(spec.optional)) or "(none)"
    return "\n".join(
        (
            spec.summary,
            "",
            f"Usage: atlas_tool.py {spec.command[0]} {spec.command[1]} --input PATH|-",
            f"Required keys: {required}",
            f"Optional keys: {optional}",
        )
    )


def _read_machine_input(path: str) -> Any:
    try:
        raw = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    except OSError as exc:
        raise Failure("REQUEST_INVALID", "input", "input could not be read") from exc
    try:
        return atlas_cli.decode(raw)
    except atlas_cli.JsonInputError as exc:
        raise Failure("REQUEST_INVALID", "input", str(exc)) from exc


def _cli_connector(
    profile: str | None,
    *,
    read_only: bool,
    allow_unbound: bool,
) -> Any | None:
    try:
        return LocalFilesystemConnector(
            resolve_profile(profile),
            read_only=read_only,
        )
    except (OSError, ValueError) as exc:
        if (
            allow_unbound
            and profile is None
            and not os.environ.get("ATLAS_VAULT_PROFILE")
        ):
            return None
        raise Failure("BINDING_INVALID", "profile", "profile is unavailable") from exc


def _parse_global(values: list[str]) -> tuple[str | None, bool, list[str]]:
    profile: str | None = None
    read_only = False
    cursor = 0
    while cursor < len(values):
        value = values[cursor]
        if value == "--profile":
            if profile is not None or cursor + 1 >= len(values):
                raise Failure("REQUEST_INVALID", "argv", "--profile requires one path")
            profile = values[cursor + 1]
            cursor += 2
            continue
        if value == "--read-only":
            if read_only:
                raise Failure("REQUEST_INVALID", "argv", "--read-only may appear once")
            read_only = True
            cursor += 1
            continue
        break
    return profile, read_only, values[cursor:]


def main(argv: Sequence[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    response: dict[str, Any]
    try:
        profile, read_only, command = _parse_global(values)
        if command in (["--help"], ["-h"]):
            print(_root_help())
            return 0
        if command in (["capabilities", "--help"], ["capabilities", "-h"]):
            print(
                "Usage: atlas_tool.py [--profile PATH] [--read-only] "
                "capabilities [--all]"
            )
            return 0
        if command in (["capabilities"], ["capabilities", "--all"]):
            connector = (
                _cli_connector(
                    profile,
                    read_only=read_only,
                    allow_unbound=False,
                )
                if profile is not None or os.environ.get("ATLAS_VAULT_PROFILE")
                else None
            )
            response = capabilities(
                connector,
                include_internal=command == ["capabilities", "--all"],
            )
            return atlas_cli.emit(response)
        if len(command) == 2 and command[1] in {"--help", "-h"}:
            print(_family_help(command[0]))
            return 0
        if (
            len(command) == 3
            and command[2] in {"--help", "-h"}
            and (command[0], command[1]) in {spec.command for spec in _CATALOG}
        ):
            spec = next(spec for spec in _CATALOG if spec.command == tuple(command[:2]))
            print(_command_help(spec))
            return 0
        if len(command) == 3 and command[0] == "call" and command[1] == "--input":
            request = _read_machine_input(command[2])
            if type(request) is not dict:
                raise Failure(
                    "REQUEST_INVALID", "input", "call input must be an object"
                )
        elif (
            len(command) == 4
            and command[2] == "--input"
            and (command[0], command[1]) in {spec.command for spec in _CATALOG}
        ):
            spec = next(spec for spec in _CATALOG if spec.command == tuple(command[:2]))
            args = _read_machine_input(command[3])
            if type(args) is not dict:
                raise Failure(
                    "REQUEST_INVALID",
                    "input",
                    "family command input must be an object",
                )
            request = {
                "version": atlas_cli.VERSION,
                "op": spec.literal,
                "args": args,
            }
        else:
            raise Failure(
                "REQUEST_INVALID",
                "argv",
                "unknown command; use --help",
            )
        op = request.get("op")
        spec = _OPERATION_BY_LITERAL.get(op) if isinstance(op, str) else None
        connector = None
        if spec is not None and spec.access != "pure":
            connector = _cli_connector(
                profile,
                read_only=read_only,
                allow_unbound=False,
            )
        response = execute(request, connector)
    except Exception as exc:
        response = _exception(None, exc)
    return atlas_cli.emit(response)


if __name__ == "__main__":
    raise SystemExit(main())
