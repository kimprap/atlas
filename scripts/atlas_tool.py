from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any

import atlas_discovery
import atlas_quality
import atlas_source
import atlas_state
import atlas_url
from atlas_connector import LocalFilesystemConnector, resolve_profile

VERSION = 1
ROOT = "vault://atlas/"
MANIFEST = ROOT + "summaries/sources/MANIFEST.md"
TOPICS = ROOT + "summaries/registry/TOPICS.md"
RELATIONS = ROOT + "summaries/registry/RELATIONS.md"
TRANSACTION_ROOT = ".atlas/transactions"
OPERATIONS = tuple(
    sorted(
        {
            "vault.read",
            "vault.read_json",
            "vault.list",
            "vault.hash",
            "vault.write_json",
            "vault.conditional_replace",
            "vault.digest_tree",
            "vault.delete_tree",
            "url.normalize",
            "url.resolve_reference",
            "discovery.normalize",
            "quality.validate_proposal",
            "quality.validate_summary",
            "quality.prepare_calibration",
            "quality.validate_calibration",
            "quality.validate_fresh_assessment",
            "state.validate",
            "state.reduce",
            "source.render_summary",
            "source.merge_artifact",
            "source.render_route_artifact",
            "source.lookup",
            "source.inventory",
            "source.prepare",
            "source.snapshot_active",
            "effect.execute",
            "effect.recover",
            "transaction.execute",
            "transaction.recover",
            "transaction.successor",
            "refresh.execute",
            "refresh.recover",
        }
    )
)
_READ_ONLY_OPERATIONS = tuple(
    sorted(
        {
            "vault.read",
            "vault.read_json",
            "vault.list",
            "vault.hash",
            "vault.digest_tree",
            "url.normalize",
            "url.resolve_reference",
            "discovery.normalize",
            "quality.validate_proposal",
            "quality.validate_summary",
            "quality.prepare_calibration",
            "quality.validate_calibration",
            "quality.validate_fresh_assessment",
            "state.validate",
            "state.reduce",
            "source.render_summary",
            "source.merge_artifact",
            "source.render_route_artifact",
            "source.lookup",
            "source.inventory",
            "source.prepare",
        }
    )
)
_REVISION = re.compile(r"(?:missing|sha256:[0-9a-f]{64})\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_TX_ID = re.compile(r"[0-9a-f]{16}-a[0-9]{6}\Z")
_EFFECT_ID = re.compile(r"effect-[0-9]{4,}\Z")
_MEMBER_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")


class Failure(ValueError):
    def __init__(
        self,
        code: str,
        path: str,
        detail: str,
        findings: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(detail)
        self.code, self.path, self.detail = code, path, detail
        self.findings = findings


def _json(value: Any) -> bytes:
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


def _hash(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _finding(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _findings(items: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {"code": code, "path": path, "detail": detail}
        for code, path, detail in sorted(
            {(x["code"], x["path"], x.get("detail", "")) for x in items}
        )
    ]


def _response(
    op: str | None,
    result: Mapping[str, Any] | None = None,
    findings: Sequence[dict[str, str]] = (),
) -> dict[str, Any]:
    found = _findings(findings)
    return {
        "version": VERSION,
        "ok": not found,
        "op": op,
        "result": dict(result) if not found else None,
        "findings": found,
    }


def _error(op: str | None, code: str, path: str, detail: str) -> dict[str, Any]:
    return _response(op, findings=[_finding(code, path, detail)])


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
    return result


def _mutations(connector: Any) -> None:
    if _capabilities(connector).get("conditional_replace") != "available":
        raise Failure(
            "MUTATION_UNAVAILABLE", "connector", "the active profile is read-only"
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
        else:
            code, path, detail = (
                getattr(value, "code", None),
                getattr(value, "path", None),
                getattr(value, "detail", ""),
            )
        if (
            not isinstance(code, str)
            or not isinstance(path, str)
            or not isinstance(detail, str)
        ):
            raise Failure(
                "OWNER_OUTPUT_INVALID", "findings", "owner returned an invalid finding"
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
            docs["manifest"], docs["topics"], docs["relations"]
        )
    )


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
    value = _args(args, {"intent", "inputs"}, "source.inventory")
    intent = _text(value["intent"], "args.intent")
    if intent not in {"presence", "routine", "resummarize"}:
        raise Failure("REQUEST_INVALID", "args.intent", "intent is invalid")
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
    checked_on = date.today().isoformat() if intent != "presence" else None
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
        "manifest_revision": "sha256:" + _hash(manifest_bytes),
        "entries": normalized,
    }
    if checked_on is not None:
        result["checked_on"] = checked_on
    return result


def _source_prepare(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"identity", "mode", "worker"}, "source.prepare")
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

    docs = _documents(connector)
    _validate(docs)
    source_id = atlas_url.source_id_for(canonical_url)
    existing = next(
        (
            row
            for row, _ in _rows(docs["manifest"], atlas_state.MANIFEST_HEADER, MANIFEST)
            if row["Source ID"] == source_id
        ),
        None,
    )
    living_artifact_text: str | None = None
    if existing is not None and existing["Status"] == "active":
        artifact_uri = _logical(existing["Artifact"])
        try:
            living_artifact_text = connector.read_text(artifact_uri)
        except (FileNotFoundError, ValueError) as exc:
            return {
                "state": "rejected",
                "findings": [
                    {
                        "code": "SOURCE_ARTIFACT_INVALID",
                        "path": artifact_uri,
                        "detail": str(exc),
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
    artifact_text = prepared["artifact_text"]
    if artifact_text is not None and (
        living_artifact_text is None or artifact_text != living_artifact_text
    ):
        targets.append(
            {
                "path": _logical(prepared["artifact_path"]),
                "expected_revision": (
                    "missing"
                    if living_artifact_text is None
                    else "sha256:" + _hash(living_artifact_text.encode("utf-8"))
                ),
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
                    "expected_revision": "sha256:" + _hash(docs[name].encode("utf-8")),
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
            raise atlas_source.SourceError("transaction path is invalid")
        return _logical(path)

    def read(self, path: str) -> bytes | None:
        try:
            return self.connector.read_bytes(self._uri(path))
        except FileNotFoundError:
            return None

    def create(self, path: str, data: bytes) -> None:
        self.connector.conditional_replace(self._uri(path), "missing", data)

    def write(self, path: str, data: bytes) -> None:
        uri = self._uri(path)
        revision = self.connector.revision(uri)
        self.connector.conditional_replace(uri, revision, data)

    def delete(self, path: str) -> None:
        self.connector.delete(path)


def _event(value: Any) -> dict[str, Any]:
    record = _object(value, "event_record")
    fields = {
        "version",
        "event_type",
        "source_id",
        "promotion_map_sha256",
        "promotion_row_sha256",
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
    expected = {
        "source": "source-upsert",
        "source-upsert": "source-upsert",
        "route": "route-upsert",
        "route-upsert": "route-upsert",
    }
    if (
        not isinstance(record["event_type"], str)
        or expected.get(record["event_type"]) != event.get("type")
        or event.get("source_id") != source_id
    ):
        raise Failure(
            "EVENT_RECORD_INVALID", "event_record", "event identity is inconsistent"
        )
    for name in ("promotion_map_sha256", "promotion_row_sha256"):
        digest = record[name]
        if digest is not None and (
            not isinstance(digest, str) or _SHA256.fullmatch(digest) is None
        ):
            raise Failure(
                "EVENT_RECORD_INVALID", f"event_record.{name}", "hash is invalid"
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
            "source event cannot carry route decision",
        )
    return record


def _rank(path: str) -> tuple[int, str]:
    if path.startswith(atlas_source.ARTIFACT_PREFIX) and path.endswith(".md"):
        return 0, path
    order = {
        atlas_state.RELATIONS_PATH: 1,
        atlas_state.TOPICS_PATH: 2,
        atlas_state.MANIFEST_PATH: 3,
    }
    if path not in order:
        raise Failure(
            "TARGET_NOT_ALLOWED",
            "targets",
            "target is outside the source/route write set",
        )
    return order[path], path


def _targets(
    value: Any,
) -> tuple[tuple[atlas_source.TransactionTarget, ...], dict[str, str]]:
    if type(value) is not list or not value:
        raise Failure("TARGETS_INVALID", "targets", "targets must be a nonempty array")
    targets: list[atlas_source.TransactionTarget] = []
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
        targets.append(atlas_source.TransactionTarget(path, None, output))
        revisions[path] = expected
    ordered = tuple(sorted(targets, key=lambda item: _rank(item.path)))
    if tuple(targets) != ordered or len(revisions) != len(targets):
        raise Failure(
            "TARGETS_INVALID", "targets", "targets are not uniquely canonical ordered"
        )
    return ordered, revisions


def _bind(
    connector: Any,
    targets: Sequence[atlas_source.TransactionTarget],
    expected: Mapping[str, str],
) -> tuple[atlas_source.TransactionTarget, ...]:
    result: list[atlas_source.TransactionTarget] = []
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
            atlas_source.TransactionTarget(
                target.path, input_bytes, target.output_bytes
            )
        )
    return tuple(result)


def _route_guard(connector: Any, record: Mapping[str, Any]) -> None:
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
        values = atlas_source.parse_artifact(connector.read_text(artifact_uri)).values
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
    current = [
        item
        for item, _ in _rows(docs["relations"], atlas_state.RELATIONS_HEADER, RELATIONS)
        if item["Source ID"] == record["source_id"]
        and item["Source content hash"] == row["Content hash"]
        and item["Status"] in {"pending", "applied"}
    ]
    if event.get("outcome") == "no-topic-match" and current:
        raise Failure(
            "ROUTE_PREFLIGHT_HASH_MISMATCH",
            "event_record.event.outcome",
            "outcome conflicts with current relations",
        )


def _plan(
    record: Mapping[str, Any],
    targets: Sequence[atlas_source.TransactionTarget],
    attempt: int = 0,
    predecessor: str | None = None,
) -> atlas_source.TransactionPlan:
    provisional = atlas_source.build_transaction_plan(
        event_path="pending/event.json",
        event_record=record,
        targets=targets,
        attempt=attempt,
        predecessor_sha256=predecessor,
    )
    return atlas_source.build_transaction_plan(
        event_path=f"{TRANSACTION_ROOT}/{provisional.transaction_id}/event.json",
        event_record=record,
        targets=targets,
        attempt=attempt,
        predecessor_sha256=predecessor,
    )


def _base(plan: atlas_source.TransactionPlan) -> str:
    return f"{TRANSACTION_ROOT}/{plan.transaction_id}"


def _event_value(
    record: Mapping[str, Any], plan: atlas_source.TransactionPlan
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "event_record": dict(record),
        "attempt": plan.attempt,
        "predecessor_sha256": plan.predecessor_sha256,
        "targets": [
            {
                "path": target.path,
                "input_base64": None
                if target.input_bytes is None
                else base64.b64encode(target.input_bytes).decode("ascii"),
                "output_base64": base64.b64encode(target.output_bytes).decode("ascii"),
            }
            for target in plan.targets
        ],
    }


def _store_event(
    port: _Port, record: Mapping[str, Any], plan: atlas_source.TransactionPlan
) -> None:
    path = f"{_base(plan)}/event.json"
    body = _json(_event_value(record, plan))
    current = port.read(path)
    if current is None:
        port.create(path, body)
    elif current != body:
        raise Failure(
            "TRANSACTION_EVENT_COLLISION", _logical(path), "immutable event differs"
        )


def _receipt(
    connector: Any, port: _Port, plan: atlas_source.TransactionPlan, status: str
) -> dict[str, Any]:
    terminal = port.read(f"{_base(plan)}/{status}.json")
    if terminal is None:
        raise Failure(
            "TRANSACTION_RECORD_INVALID",
            _logical(_base(plan)),
            "terminal record is missing",
        )
    return {
        "transaction_id": plan.transaction_id,
        "base_transaction_id": plan.base_transaction_id,
        "attempt": plan.attempt,
        "predecessor_sha256": plan.predecessor_sha256,
        "status": status,
        "targets": [target.intent_value() for target in plan.targets],
        "sha256": _hash(terminal),
        "target_revisions": {
            _logical(target.path): connector.revision(_logical(target.path))
            for target in plan.targets
        },
    }


def _tx_result(
    connector: Any, port: _Port, plan: atlas_source.TransactionPlan, status: str
) -> dict[str, Any]:
    base = _base(plan)
    names = [
        "prepared.json",
        *(f"backups/{index:06d}.json" for index, _ in enumerate(plan.targets)),
        *(f"progress/{index:06d}.json" for index, _ in enumerate(plan.targets)),
        f"{status}.json",
    ]
    return {
        "event_uri": _logical(f"{base}/event.json"),
        "intent_uri": _logical(f"{base}/intent.json"),
        "phase_uris": [
            _logical(f"{base}/{name}")
            for name in names
            if port.read(f"{base}/{name}") is not None
        ],
        "receipt": _receipt(connector, port, plan, status),
    }


def _load_plan(
    port: _Port, transaction_id: str
) -> tuple[dict[str, Any], atlas_source.TransactionPlan]:
    path = f"{TRANSACTION_ROOT}/{transaction_id}/event.json"
    raw = port.read(path)
    if raw is None:
        raise Failure(
            "TRANSACTION_UNKNOWN", "transaction_id", "transaction event is missing"
        )
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Failure(
            "TRANSACTION_RECORD_INVALID", _logical(path), "event record is invalid"
        ) from exc
    if (
        type(value) is not dict
        or set(value)
        != {"version", "event_record", "attempt", "predecessor_sha256", "targets"}
        or _json(value) != raw
    ):
        raise Failure(
            "TRANSACTION_RECORD_INVALID", _logical(path), "event record is noncanonical"
        )
    if (
        value["version"] != VERSION
        or type(value["attempt"]) is not int
        or value["attempt"] < 0
    ):
        raise Failure(
            "TRANSACTION_RECORD_INVALID", _logical(path), "attempt is invalid"
        )
    predecessor = value["predecessor_sha256"]
    if predecessor is not None and (
        not isinstance(predecessor, str) or _SHA256.fullmatch(predecessor) is None
    ):
        raise Failure(
            "TRANSACTION_RECORD_INVALID", _logical(path), "predecessor is invalid"
        )
    record = _event(value["event_record"])
    if type(value["targets"]) is not list or not value["targets"]:
        raise Failure(
            "TRANSACTION_RECORD_INVALID", _logical(path), "targets are invalid"
        )
    targets: list[atlas_source.TransactionTarget] = []
    for row in value["targets"]:
        item = _object(row, "transaction.targets")
        if set(item) != {"path", "input_base64", "output_base64"} or not isinstance(
            item["path"], str
        ):
            raise Failure(
                "TRANSACTION_RECORD_INVALID",
                _logical(path),
                "target fields are invalid",
            )
        try:
            input_bytes = (
                None
                if item["input_base64"] is None
                else base64.b64decode(item["input_base64"], validate=True)
            )
            output_bytes = base64.b64decode(item["output_base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise Failure(
                "TRANSACTION_RECORD_INVALID", _logical(path), "target bytes are invalid"
            ) from exc
        _rank(item["path"])
        targets.append(
            atlas_source.TransactionTarget(item["path"], input_bytes, output_bytes)
        )
    plan = _plan(record, tuple(targets), value["attempt"], predecessor)
    if plan.transaction_id != transaction_id:
        raise Failure(
            "TRANSACTION_RECORD_INVALID", _logical(path), "transaction ID is not bound"
        )
    return record, plan


def _tx_execute(connector: Any, args: Any) -> dict[str, Any]:
    value = _args(args, {"event_record", "targets"}, "transaction.execute")
    record = _event(value["event_record"])
    pending, expected = _targets(value["targets"])
    _mutations(connector)
    with connector.mutation_session():
        targets = _bind(connector, pending, expected)
        _route_guard(connector, record)
        try:
            plan = _plan(record, targets)
        except atlas_source.SourceError as exc:
            raise Failure("TRANSACTION_INVALID", "targets", str(exc)) from exc
        port = _Port(connector)
        _store_event(port, record, plan)
        try:
            status = atlas_source.execute_transaction(port, TRANSACTION_ROOT, plan)
        except atlas_source.SourceError as exc:
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
    value = _args(args, {"transaction_id"}, "transaction.recover")
    transaction_id = _text(value["transaction_id"], "transaction_id")
    if _TX_ID.fullmatch(transaction_id) is None:
        raise Failure(
            "TRANSACTION_UNKNOWN", "transaction_id", "transaction ID is invalid"
        )
    _mutations(connector)
    with connector.mutation_session():
        port = _Port(connector)
        _, plan = _load_plan(port, transaction_id)
        try:
            status = atlas_source.recover_transaction(port, TRANSACTION_ROOT, plan)
        except atlas_source.SourceError as exc:
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
        terminal = [
            (status, port.read(f"{_base(predecessor)}/{status}.json"))
            for status in (
                "applied",
                "no-op",
                "aborted",
                "rolled-back",
                "manual-conflict",
            )
        ]
        terminal = [(status, raw) for status, raw in terminal if raw is not None]
        if len(terminal) != 1 or terminal[0][0] not in {"aborted", "rolled-back"}:
            raise Failure(
                "SUCCESSOR_TERMINAL_INELIGIBLE",
                "transaction_id",
                "only attempt-zero aborted or rolled-back transactions are eligible",
            )
        successor_id = (
            f"{predecessor.base_transaction_id}-a{predecessor.attempt + 1:06d}"
        )
        try:
            plan = atlas_source.build_successor_plan(
                predecessor,
                event_path=f"{TRANSACTION_ROOT}/{successor_id}/event.json",
                event_record=record,
                terminal_record=terminal[0][1],
            )
        except atlas_source.SourceError as exc:
            raise Failure(
                "SUCCESSOR_TERMINAL_INELIGIBLE", "transaction_id", str(exc)
            ) from exc
        _store_event(port, record, plan)
        status = atlas_source.execute_transaction(port, TRANSACTION_ROOT, plan)
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
        for name in ("manifest", "topics", "relations")
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
    documents = _documents(connector)
    _validate(documents)
    _effect_identity_preflight(connector, parsed, effect, documents)
    pre_state = _effect_state_hashes(documents)
    virtual_documents = dict(documents)
    virtual_bytes: dict[str, bytes | None] = {}
    claimed_transactions: list[dict[str, Any]] = []
    target_uris: set[str] = set()
    artifact_targets: set[str] = set()
    for transaction in parsed["transactions"]:
        bound: list[atlas_source.TransactionTarget] = []
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
                atlas_source.TransactionTarget(
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
            }
        }
        reducer_outputs = {
            _relative(_doc_uri(name)): text.encode("utf-8")
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
        try:
            plan = _plan(transaction["event_record"], tuple(bound))
        except atlas_source.SourceError as exc:
            raise Failure(
                "EFFECT_TRANSACTIONS_INVALID", "transactions", str(exc)
            ) from exc
        claimed_transactions.append(
            {
                "stage": transaction["stage"],
                "transaction_id": plan.transaction_id,
                "transaction": _event_value(transaction["event_record"], plan),
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
) -> tuple[dict[str, Any], atlas_source.TransactionPlan]:
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
    targets: list[atlas_source.TransactionTarget] = []
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
        targets.append(atlas_source.TransactionTarget(path, input_bytes, output_bytes))
    plan = _plan(record, tuple(targets))
    if plan.transaction_id != value.get("transaction_id"):
        raise Failure(
            "EFFECT_CLAIM_INVALID",
            "claim.transactions.transaction_id",
            "claimed transaction ID is invalid",
        )
    return record, plan


def _effect_current_bytes(
    connector: Any, target: atlas_source.TransactionTarget
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
    plan: atlas_source.TransactionPlan,
) -> tuple[str, dict[str, Any]]:
    event_path = f"{_base(plan)}/event.json"
    existing = port.read(event_path)
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
            _route_guard(connector, record)
            _store_event(port, record, plan)
            status = atlas_source.execute_transaction(port, TRANSACTION_ROOT, plan)
        else:
            loaded_record, loaded_plan = _load_plan(port, plan.transaction_id)
            if (
                _event_value(loaded_record, loaded_plan) != _event_value(record, plan)
                or loaded_plan.transaction_id != plan.transaction_id
            ):
                raise Failure(
                    "EFFECT_TRANSACTION_COLLISION",
                    _logical(event_path),
                    "stored transaction differs from claim",
                )
            status = atlas_source.recover_transaction(port, TRANSACTION_ROOT, plan)
    except atlas_source.SourceError as exc:
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
    terminal = port.read(f"{_base(plan)}/{status}.json")
    assert terminal is not None
    successor_id = f"{plan.base_transaction_id}-a{plan.attempt + 1:06d}"
    try:
        successor = atlas_source.build_successor_plan(
            plan,
            event_path=f"{TRANSACTION_ROOT}/{successor_id}/event.json",
            event_record=record,
            terminal_record=terminal,
        )
    except atlas_source.SourceError as exc:
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
        documents = _documents(connector)
        _validate(documents)
    post_documents = _documents(connector)
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
        or values.get("logical_root", values.get("root")) != ROOT
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
                value["artifact_text"], value["evidence_bundle"], value["checklist"]
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
    if op == "quality.validate_fresh_assessment":
        value = _args(args, {"assessment", "packet"}, op)
        _reject(
            atlas_quality.validate_fresh_source_assessment(
                value["assessment"], value["packet"]
            )
        )
        return {}
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
        try:
            if "documents" in value:
                documents = value["documents"]
                if not isinstance(documents, Mapping):
                    raise ValueError("documents must be an object")
                _reject(
                    atlas_state.validate_documents(
                        documents["manifest"],
                        documents["topics"],
                        documents["relations"],
                    )
                )
            else:
                _validate(_documents(_connector(connector)))
        except KeyError as exc:
            raise Failure(
                "STATE_INPUT_INVALID", "args.documents", "document is missing"
            ) from exc
        except ValueError as exc:
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


def _dispatch(op: str, args: Any, connector: Any | None) -> dict[str, Any]:
    if op.startswith("vault."):
        return _vault(_connector(connector), op, args)
    if op == "source.lookup":
        return _source_lookup(_connector(connector), args)
    if op == "source.inventory":
        return _source_inventory(_connector(connector), args)
    if op == "source.prepare":
        return _source_prepare(_connector(connector), args)
    if op == "source.snapshot_active":
        return _snapshot(_connector(connector), args)
    if op == "transaction.execute":
        return _tx_execute(_connector(connector), args)
    if op == "transaction.recover":
        return _tx_recover(_connector(connector), args)
    if op == "transaction.successor":
        return _tx_successor(_connector(connector), args)
    if op == "effect.execute":
        return _effect_execute(_connector(connector), args, recover=False)
    if op == "effect.recover":
        return _effect_execute(_connector(connector), args, recover=True)
    if op == "refresh.execute":
        return _refresh_execute(_connector(connector), args)
    if op == "refresh.recover":
        return _refresh_recover(_connector(connector), args)
    return _pure(op, args, connector)


def _exception(op: str | None, exc: BaseException) -> dict[str, Any]:
    if isinstance(exc, Failure):
        return (
            _response(op, findings=exc.findings)
            if exc.findings is not None
            else _error(op, exc.code, exc.path, exc.detail)
        )
    if isinstance(exc, OSError):
        return _error(op, "IO_FAILURE", op or "request", str(exc))
    if isinstance(
        exc, (ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError)
    ):
        message = str(exc)
        if "mutation_unavailable" in message:
            return _error(op, "MUTATION_UNAVAILABLE", "connector", message)
        if "revision conflict" in message:
            return _error(op, "REVISION_STALE", op or "request", message)
        if "delete approval" in message:
            return _error(op, "DELETE_APPROVAL_INVALID", "args.approval", message)
        if "tree digest mismatch" in message:
            return _error(op, "DELETE_DIGEST_STALE", "args.expected_digest", message)
        return _error(op, "REQUEST_INVALID", op or "request", message)
    raise exc


def capabilities(connector: Any | None = None) -> dict[str, Any]:
    try:
        active = _connector(connector)
        values = _capabilities(active)
        if (
            values.get("adapter") != "atlas-local-fs-cas-v1"
            or values.get("logical_root", values.get("root")) != ROOT
        ):
            raise Failure(
                "BINDING_INVALID", "connector", "unsupported connector capability"
            )
        return _response(
            "capabilities",
            {
                "adapter": "atlas-local-fs-cas-v1",
                "logical_root": ROOT,
                "operations": list(
                    OPERATIONS
                    if values.get("conditional_replace") == "available"
                    else _READ_ONLY_OPERATIONS
                ),
            },
        )
    except (Failure, OSError, ValueError, TypeError, AttributeError) as exc:
        return _exception("capabilities", exc)


def execute(request: Any, connector: Any | None = None) -> dict[str, Any]:
    op = (
        request.get("op")
        if isinstance(request, Mapping) and isinstance(request.get("op"), str)
        else None
    )
    if type(request) is not dict:
        return _error(op, "REQUEST_INVALID", "request", "expected an object")
    if type(request.get("version")) is not int or request.get("version") != VERSION:
        return _error(op, "VERSION_UNSUPPORTED", "version", "expected version 1")
    if (
        set(request) != {"version", "op", "args"}
        or not isinstance(request["op"], str)
        or type(request["args"]) is not dict
    ):
        return _error(
            op, "REQUEST_INVALID", "request", "expected exactly version, op, args"
        )
    op = request["op"]
    if op not in OPERATIONS:
        return _error(
            op, "OP_UNKNOWN", op, "operation is not an Atlas facade capability"
        )
    try:
        return _response(op, _dispatch(op, request["args"], connector))
    except (
        Failure,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        UnicodeError,
        json.JSONDecodeError,
    ) as exc:
        return _exception(op, exc)


def _exit(response: Mapping[str, Any]) -> int:
    if response["ok"]:
        return 0
    codes = {
        "BINDING_INVALID",
        "IO_FAILURE",
        "MUTATION_UNAVAILABLE",
        "REVISION_STALE",
        "QUARANTINED_NOT_ERASED",
        "MANUAL_CONFLICT",
        "DELETE_DIGEST_STALE",
        "PASS_COLLISION",
        "REFRESH_CONCURRENT_MUTATION",
        "TRANSACTION_RECOVERABLE",
    }
    return 3 if response["findings"][0]["code"] in codes else 2


def main(argv: Sequence[str] | None = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    try:
        if values == ["capabilities"]:
            response = capabilities()
        elif len(values) == 3 and values[:2] == ["call", "--input"] and values[2]:
            raw = (
                sys.stdin.buffer.read()
                if values[2] == "-"
                else Path(values[2]).read_bytes()
            )
            response = execute(json.loads(raw.decode("utf-8")))
        else:
            raise Failure(
                "REQUEST_INVALID",
                "argv",
                "expected capabilities or call --input <path|->",
            )
    except Failure as exc:
        response = _error(None, exc.code, exc.path, exc.detail)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        response = _error(None, "REQUEST_INVALID", "input", str(exc))
    sys.stdout.buffer.write(_json(response))
    return _exit(response)


if __name__ == "__main__":
    raise SystemExit(main())
