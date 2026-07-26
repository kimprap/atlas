#!/usr/bin/env python3
"""Deterministic Atlas source artifact assembly and transaction coordination."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

import atlas_quality
from atlas_state import (
    MANIFEST_PATH,
    RELATIONS_PATH,
    TOPICS_PATH,
    plan_transaction_recovery,
)
from atlas_url import normalize_canonical_url, source_id_for


VERSION = 1
ARTIFACT_PREFIX = "summaries/sources/artifacts/"
FRONTMATTER_KEYS = (
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
LIST_FRONTMATTER_KEYS = {
    "subdomains",
    "secondary_domains",
    "canonical_tags",
    "candidate_terms",
}


def _validate_frontmatter_shapes(values: Mapping[str, str]) -> None:
    if values.get("schema_version") != "1":
        raise SourceError("frontmatter schema_version must be the unquoted integer 1")
    source_seq = values.get("source_seq", "")
    if re.fullmatch(r"0|[1-9]\d*", source_seq) is None:
        raise SourceError(
            "frontmatter source_seq must be an unquoted non-negative integer"
        )
    for key in LIST_FRONTMATTER_KEYS:
        raw = values.get(key, "")
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SourceError(
                f"frontmatter {key} must be a JSON array of strings"
            ) from exc
        if not isinstance(items, list) or any(
            not isinstance(item, str) for item in items
        ):
            raise SourceError(f"frontmatter {key} must be a JSON array of strings")


ROUTE_STATUSES = {"unrouted", "routed", "no-topic-match", "routing-blocked"}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^[0-9a-f]{12}$")
TARGET_ORDER = {
    RELATIONS_PATH: 1,
    TOPICS_PATH: 2,
    MANIFEST_PATH: 3,
}


class SourceError(ValueError):
    """A source artifact or transaction violates the canonical contract."""


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class ParsedArtifact:
    values: dict[str, str]
    body: str


def parse_artifact(text: str) -> ParsedArtifact:
    if not isinstance(text, str):
        raise SourceError("artifact text must be a string")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        raise SourceError("artifact frontmatter is missing")
    boundary = normalized.find("\n---\n", 4)
    if boundary < 0:
        raise SourceError("artifact frontmatter is unterminated")
    values: dict[str, str] = {}
    list_items: dict[str, list[str]] = {}
    last_key: str | None = None
    for line in normalized[4:boundary].splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        if line.startswith(("  - ", "\t- ")):
            if last_key not in LIST_FRONTMATTER_KEYS or values.get(last_key) != "":
                raise SourceError(f"invalid frontmatter line: {line}")
            raw_item = line.split("-", 1)[1].strip()
            if not raw_item:
                raise SourceError(f"invalid frontmatter line: {line}")
            if raw_item.startswith('"'):
                try:
                    item = json.loads(raw_item)
                except json.JSONDecodeError as exc:
                    raise SourceError(f"invalid frontmatter line: {line}") from exc
                if not isinstance(item, str):
                    raise SourceError(f"invalid frontmatter line: {line}")
            elif len(raw_item) >= 2 and raw_item[0] == raw_item[-1] == "'":
                item = raw_item[1:-1].replace("''", "'")
            else:
                item = raw_item
            list_items.setdefault(last_key, []).append(item)
            continue
        if line[:1].isspace():
            raise SourceError(f"invalid frontmatter line: {line}")
        key, separator, raw = line.partition(":")
        if not separator or not key or key in values:
            raise SourceError(f"invalid frontmatter line: {line}")
        values[key] = raw.strip()
        last_key = key
    for key in LIST_FRONTMATTER_KEYS:
        if values.get(key) == "":
            items = list_items.get(key)
            if not items:
                raise SourceError(f"frontmatter {key} block sequence is empty")
            values[key] = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    missing = set(FRONTMATTER_KEYS) - set(values)
    unknown = set(values) - set(FRONTMATTER_KEYS)
    if missing or unknown:
        raise SourceError(
            f"artifact frontmatter keys invalid: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    _validate_frontmatter_shapes(values)
    body = normalized[boundary + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    return ParsedArtifact(values, body)


def scalar(values: Mapping[str, str], key: str) -> str:
    raw = values[key]
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SourceError(
                f"frontmatter {key} is not a valid quoted scalar"
            ) from exc
        if not isinstance(value, str):
            raise SourceError(f"frontmatter {key} must be text")
        return value
    return raw


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_artifact(values: Mapping[str, str], body: str) -> str:
    missing = set(FRONTMATTER_KEYS) - set(values)
    unknown = set(values) - set(FRONTMATTER_KEYS)
    if missing or unknown:
        raise SourceError(
            f"render frontmatter keys invalid: missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    _validate_frontmatter_shapes(values)
    normalized_body = body.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
    frontmatter = "\n".join(f"{key}: {values[key]}" for key in FRONTMATTER_KEYS)
    return f"---\n{frontmatter}\n---\n\n{normalized_body}\n"


def _replace_header(body: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^\*\*{re.escape(label)}\*\*:.*$", re.MULTILINE)
    replacement = f"**{label}**: {value}"
    updated, count = pattern.subn(lambda _: replacement, body)
    if count != 1:
        raise SourceError(f"artifact body must contain one rendered {label} field")
    return updated


def resolve_effective_content_hash(bundle: Mapping[str, Any]) -> str:
    """Return the effective content hash for one evidence bundle.

    Delegates to `atlas_quality.resolve_effective_content_hash` so source assembly
    and quality validation share one text-hash and projection owner. Raises
    SourceError when the envelope is invalid, incomplete, or not text-backed.
    """
    effective, findings = atlas_quality.resolve_effective_content_hash(bundle)
    if findings or effective is None:
        detail = findings[0].code if findings else "EVIDENCE_PAYLOAD_TEXT_INVALID"
        if findings and findings[0].detail:
            detail = f"{detail}: {findings[0].detail}"
        raise SourceError(f"evidence identity invalid: {detail}")
    return effective


def classify_hash_transition(
    previous_content_hash: str | None,
    evidence_bundle: Mapping[str, Any],
) -> str:
    """Return `same-hash` or `changed-hash` from proven text evidence only.

    Inaccessible, empty, media-backed, unbacked projection, or otherwise unproven
    evidence raises SourceError and is a no-write result—never a guessed transition.
    `hash_baseline_migration` is a reporting reason only and is not returned here.
    """
    effective = resolve_effective_content_hash(evidence_bundle)
    if previous_content_hash is None:
        return "changed-hash"
    if (
        not isinstance(previous_content_hash, str)
        or HASH_RE.fullmatch(previous_content_hash) is None
    ):
        raise SourceError("previous content_hash is invalid")
    return "same-hash" if previous_content_hash == effective else "changed-hash"


def _evidence_identity(bundle: Mapping[str, Any]) -> dict[str, str]:
    canonical_url = bundle.get("canonical_url")
    payload = bundle.get("payload_text")
    first_seen = bundle.get("first_seen", bundle.get("fetched_at"))
    if (
        not isinstance(canonical_url, str)
        or not isinstance(payload, str)
        or not isinstance(first_seen, str)
    ):
        raise SourceError(
            "evidence bundle lacks canonical_url, payload_text, or first_seen/fetched_at"
        )
    if payload == "":
        raise SourceError("evidence payload_text is empty")
    normalized = normalize_canonical_url(canonical_url)
    if normalized != canonical_url:
        raise SourceError("evidence canonical_url is not normalized")
    content_hash = resolve_effective_content_hash(bundle)
    return {
        "canonical_url": canonical_url,
        "source_id": source_id_for(canonical_url),
        "content_hash": content_hash,
        "first_seen": first_seen,
    }


def _require_state(
    source_state: Mapping[str, Any], name: str, expected_type: type
) -> Any:
    value = source_state.get(name)
    if not isinstance(value, expected_type):
        raise SourceError(f"source_state.{name} has invalid type")
    return value


def merge_artifact(
    staged_artifact_text: str,
    evidence_bundle: Mapping[str, Any],
    event: Mapping[str, Any],
    source_state: Mapping[str, Any],
    *,
    living_artifact_text: str | None = None,
    fresh_capture: bool = False,
) -> str:
    """Assemble one canonical source artifact from a selected staged artifact."""
    if event.get("type") != "source-upsert":
        raise SourceError("merge-artifact requires a source-upsert event")
    staged = parse_artifact(staged_artifact_text)
    evidence = _evidence_identity(evidence_bundle)
    created = _require_state(source_state, "created", bool)
    source_seq = _require_state(source_state, "source_seq", int)
    state_source_id = _require_state(source_state, "source_id", str)
    state_url = _require_state(source_state, "canonical_url", str)
    state_hash = _require_state(source_state, "content_hash", str)
    state_first_seen = _require_state(source_state, "first_seen", str)
    route_status = _require_state(source_state, "route_status", str)
    if route_status not in ROUTE_STATUSES:
        raise SourceError("source_state.route_status is invalid")
    event_source_id = event.get("source_id")
    event_url = event.get("canonical_url")
    event_hash = event.get("content_hash")
    if not isinstance(event_source_id, str) or not SOURCE_ID_RE.fullmatch(
        event_source_id
    ):
        raise SourceError("event source_id is invalid")
    if (
        not isinstance(event_url, str)
        or normalize_canonical_url(event_url) != event_url
    ):
        raise SourceError("event canonical_url is invalid")
    if not isinstance(event_hash, str) or not HASH_RE.fullmatch(event_hash):
        raise SourceError("event content_hash is invalid")
    identities = {
        scalar(staged.values, "source_id"),
        evidence["source_id"],
        event_source_id,
        state_source_id,
    }
    urls = {
        scalar(staged.values, "canonical_url"),
        evidence["canonical_url"],
        event_url,
        state_url,
    }
    hashes = {
        scalar(staged.values, "content_hash"),
        evidence["content_hash"],
        event_hash,
        state_hash,
    }
    if len(identities) != 1 or len(urls) != 1 or len(hashes) != 1:
        raise SourceError(
            "staged artifact, evidence, event, and reducer identity disagree"
        )
    if created and {
        scalar(staged.values, "first_seen"),
        evidence["first_seen"],
        str(event.get("first_seen")),
        state_first_seen,
    } != {state_first_seen}:
        raise SourceError("new-source first_seen values disagree")

    living = (
        parse_artifact(living_artifact_text)
        if living_artifact_text is not None
        else None
    )
    if created and living is not None:
        raise SourceError("new-source merge cannot receive a living artifact")
    if not created and living is None:
        raise SourceError("existing-source merge requires a living artifact")
    living_hash = scalar(living.values, "content_hash") if living is not None else None
    content_changed = living_hash is not None and living_hash != event_hash
    if content_changed and not fresh_capture:
        raise SourceError(
            "changed-hash merge requires fresh capture evidence and artifact"
        )

    values = dict(staged.values)
    values["source_id"] = quoted(state_source_id)
    values["source_seq"] = str(source_seq)
    values["canonical_url"] = quoted(state_url)
    values["first_seen"] = quoted(state_first_seen)
    values["last_checked"] = quoted(str(event.get("checked_on")))
    values["last_summarized"] = quoted(str(event.get("summarized_on")))
    values["refresh_after"] = quoted(str(event.get("refresh_after")))
    values["content_hash"] = quoted(state_hash)
    if created:
        values["routing_status"] = quoted("unrouted")
        values["routed_at"] = quoted("")
    else:
        assert living is not None
        values["acquired_by"] = living.values["acquired_by"]
        values["acquisition_run"] = living.values["acquisition_run"]
        if content_changed:
            values["routing_status"] = quoted("unrouted")
            values["routed_at"] = quoted("")
        else:
            values["routing_status"] = quoted(route_status)
            values["routed_at"] = living.values["routed_at"]

    body = staged.body
    body = _replace_header(body, "Source ID", f"`{state_source_id}`")
    body = _replace_header(body, "Source seq", f"`{source_seq}`")
    body = _replace_header(body, "First seen", state_first_seen)
    body = _replace_header(body, "Last checked", str(event.get("checked_on")))
    body = _replace_header(body, "Last summarized", str(event.get("summarized_on")))
    body = _replace_header(body, "Refresh after", str(event.get("refresh_after")))
    body = _replace_header(
        body, "Route status", f"`{scalar(values, 'routing_status')}`"
    )
    return render_artifact(values, body)


def render_route_artifact(
    artifact_text: str,
    route_event: Mapping[str, Any],
    route_status: str,
) -> str:
    """Render the source artifact side of one validated terminal route-upsert."""
    if route_event.get("type") != "route-upsert":
        raise SourceError("route renderer requires a route-upsert event")
    checked_on = route_event.get("checked_on")
    if not isinstance(checked_on, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", checked_on
    ):
        raise SourceError("route event checked_on is invalid")
    if route_status not in ROUTE_STATUSES - {"unrouted"}:
        raise SourceError("route status must be terminal")
    parsed = parse_artifact(artifact_text)
    values = dict(parsed.values)
    values["routing_status"] = quoted(route_status)
    values["routed_at"] = quoted(checked_on)
    body = _replace_header(parsed.body, "Route status", f"`{route_status}`")
    return render_artifact(values, body)


def build_event_record(
    *,
    event_type: str,
    source_id: str,
    event: Mapping[str, Any],
    route_decision: Mapping[str, Any] | None,
    promotion_map_sha256: str | None = None,
    promotion_row_sha256: str | None = None,
    require_promotion: bool = False,
) -> dict[str, Any]:
    if event.get("type") != event_type or event.get("source_id") != source_id:
        raise SourceError("event record identity mismatch")
    for name, value in (
        ("promotion_map_sha256", promotion_map_sha256),
        ("promotion_row_sha256", promotion_row_sha256),
    ):
        if value is not None and (
            not isinstance(value, str) or HASH_RE.fullmatch(value) is None
        ):
            raise SourceError(f"{name} is invalid")
        if require_promotion and value is None:
            raise SourceError(f"{name} is required")
    return {
        "version": 1,
        "event_type": event_type,
        "source_id": source_id,
        "promotion_map_sha256": promotion_map_sha256,
        "promotion_row_sha256": promotion_row_sha256,
        "event": dict(event),
        "route_decision": None if route_decision is None else dict(route_decision),
    }


@dataclass(frozen=True)
class TransactionTarget:
    path: str
    input_bytes: bytes | None
    output_bytes: bytes

    def intent_value(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "input_sha256": None
            if self.input_bytes is None
            else sha256(self.input_bytes),
            "output_sha256": sha256(self.output_bytes),
        }


@dataclass(frozen=True)
class TransactionPlan:
    base_transaction_id: str
    transaction_id: str
    attempt: int
    predecessor_sha256: str | None
    intent: dict[str, Any]
    targets: tuple[TransactionTarget, ...]


class ConnectorPort(Protocol):
    def read(self, path: str) -> bytes | None: ...
    def create(self, path: str, data: bytes) -> None: ...
    def write(self, path: str, data: bytes) -> None: ...
    def delete(self, path: str) -> None: ...


def _target_rank(path: str) -> tuple[int, str]:
    if path.startswith(ARTIFACT_PREFIX):
        return (0, path)
    if path in TARGET_ORDER:
        return (TARGET_ORDER[path], path)
    raise SourceError(
        f"transaction target is outside the source/route write set: {path}"
    )


def build_transaction_plan(
    *,
    event_path: str,
    event_record: Mapping[str, Any],
    targets: Sequence[TransactionTarget],
    attempt: int = 0,
    predecessor_sha256: str | None = None,
) -> TransactionPlan:
    event_raw = canonical_json(event_record)
    event_hash = sha256(event_raw)
    if attempt < 0 or (attempt == 0) != (predecessor_sha256 is None):
        raise SourceError("transaction attempt/predecessor mismatch")
    if predecessor_sha256 is not None and HASH_RE.fullmatch(predecessor_sha256) is None:
        raise SourceError("transaction predecessor hash is invalid")
    ordered = tuple(sorted(targets, key=lambda target: _target_rank(target.path)))
    if tuple(targets) != ordered:
        raise SourceError("transaction targets are not in canonical order")
    if len({target.path for target in targets}) != len(targets):
        raise SourceError("transaction target paths must be unique")
    target_values = [target.intent_value() for target in targets]
    if any(item["input_sha256"] == item["output_sha256"] for item in target_values):
        raise SourceError("transaction targets must contain changed bytes only")
    source_id = event_record.get("source_id")
    map_hash = event_record.get("promotion_map_sha256")
    row_hash = event_record.get("promotion_row_sha256")
    base_value = {
        "event_record_sha256": event_hash,
        "promotion_map_sha256": map_hash,
        "promotion_row_sha256": row_hash,
        "source_id": source_id,
        "targets": target_values,
    }
    base = sha256(canonical_json(base_value))[:16]
    transaction_id = f"{base}-a{attempt:06d}"
    intent = {
        "version": 1,
        "base_transaction_id": base,
        "transaction_id": transaction_id,
        "attempt": attempt,
        "predecessor_sha256": predecessor_sha256,
        "event_path": event_path,
        "event_record_sha256": event_hash,
        "event_type": event_record.get("event_type"),
        "promotion_map_sha256": map_hash,
        "promotion_row_sha256": row_hash,
        "source_id": source_id,
        "targets": target_values,
    }
    return TransactionPlan(
        base, transaction_id, attempt, predecessor_sha256, intent, tuple(targets)
    )


def _record_path(root: str, transaction_id: str, name: str) -> str:
    return f"{root.rstrip('/')}/{transaction_id}/{name}"


def _create_verified(connector: ConnectorPort, path: str, data: bytes) -> None:
    connector.create(path, data)
    if connector.read(path) != data:
        raise SourceError(f"connector acknowledgement mismatch: {path}")


def _write_verified(connector: ConnectorPort, path: str, data: bytes) -> None:
    connector.write(path, data)
    if connector.read(path) != data:
        raise SourceError(f"connector acknowledgement mismatch: {path}")


def _current_hashes(
    connector: ConnectorPort, targets: Sequence[TransactionTarget]
) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for target in targets:
        current = connector.read(target.path)
        values[target.path] = None if current is None else sha256(current)
    return values


def _terminal_record(status: str, intent_sha256: str) -> bytes:
    return canonical_json(
        {"version": 1, "status": status, "intent_sha256": intent_sha256}
    )


def build_successor_plan(
    plan: TransactionPlan,
    *,
    event_path: str,
    event_record: Mapping[str, Any],
    terminal_record: bytes,
) -> TransactionPlan:
    intent_hash = sha256(canonical_json(plan.intent))
    if not any(
        terminal_record == _terminal_record(status, intent_hash)
        for status in ("aborted", "rolled-back")
    ):
        raise SourceError(
            "successor requires the verified aborted or rolled-back terminal record"
        )
    successor = build_transaction_plan(
        event_path=event_path,
        event_record=event_record,
        targets=plan.targets,
        attempt=plan.attempt + 1,
        predecessor_sha256=sha256(terminal_record),
    )
    if successor.base_transaction_id != plan.base_transaction_id:
        raise SourceError("successor event or outputs differ from the predecessor")
    return successor


def _ensure_terminal(
    connector: ConnectorPort,
    path: str,
    status: str,
    intent_sha256: str,
) -> None:
    expected = _terminal_record(status, intent_sha256)
    current = connector.read(path)
    if current is None:
        _create_verified(connector, path, expected)
    elif current != expected:
        raise SourceError(f"terminal record collision: {path}")


def recover_transaction(
    connector: ConnectorPort,
    transaction_root: str,
    plan: TransactionPlan,
    *,
    abort_unprepared: bool = False,
) -> str:
    """Recover one existing transaction attempt from connector-reread truth."""
    base = f"{transaction_root.rstrip('/')}/{plan.transaction_id}"
    intent_path = f"{base}/intent.json"
    expected_intent = canonical_json(plan.intent)
    if connector.read(intent_path) != expected_intent:
        raise SourceError("transaction intent is missing or does not match")
    intent_hash = sha256(expected_intent)
    existing_terminals = [
        status
        for status in ("applied", "no-op", "aborted", "rolled-back", "manual-conflict")
        if connector.read(f"{base}/{status}.json") is not None
    ]
    if existing_terminals:
        if len(existing_terminals) != 1:
            raise SourceError("transaction has multiple terminal records")
        status = existing_terminals[0]
        if connector.read(f"{base}/{status}.json") != _terminal_record(
            status, intent_hash
        ):
            raise SourceError("transaction terminal record is malformed")
        return status
    prepared_path = f"{base}/prepared.json"
    prepared_raw = connector.read(prepared_path)
    prepared: Mapping[str, Any] | None = None
    if prepared_raw is not None:
        backup_hashes: list[str] = []
        for index, target in enumerate(plan.targets):
            backup = canonical_json(
                {
                    "version": 1,
                    "path": target.path,
                    "input_sha256": (
                        None
                        if target.input_bytes is None
                        else sha256(target.input_bytes)
                    ),
                    "input_base64": (
                        None
                        if target.input_bytes is None
                        else base64.b64encode(target.input_bytes).decode("ascii")
                    ),
                }
            )
            if connector.read(f"{base}/backups/{index:06d}.json") != backup:
                raise SourceError("transaction backup is missing or malformed")
            backup_hashes.append(sha256(backup))
        expected_prepared = canonical_json(
            {
                "version": 1,
                "intent_sha256": intent_hash,
                "backup_sha256s": backup_hashes,
            }
        )
        if prepared_raw != expected_prepared:
            raise SourceError("transaction prepared record is malformed")
        prepared = json.loads(prepared_raw.decode("utf-8"))
    recovery = plan_transaction_recovery(
        plan.intent,
        prepared,
        _current_hashes(connector, plan.targets),
        abort=abort_unprepared,
    )
    if recovery.action == "prepare":
        backup_hashes: list[str] = []
        for index, target in enumerate(plan.targets):
            backup = canonical_json(
                {
                    "version": 1,
                    "path": target.path,
                    "input_sha256": (
                        None
                        if target.input_bytes is None
                        else sha256(target.input_bytes)
                    ),
                    "input_base64": (
                        None
                        if target.input_bytes is None
                        else base64.b64encode(target.input_bytes).decode("ascii")
                    ),
                }
            )
            backup_path = f"{base}/backups/{index:06d}.json"
            current_backup = connector.read(backup_path)
            if current_backup is None:
                _create_verified(connector, backup_path, backup)
            elif current_backup != backup:
                raise SourceError("transaction backup collision")
            backup_hashes.append(sha256(backup))
        prepared_bytes = canonical_json(
            {
                "version": 1,
                "intent_sha256": intent_hash,
                "backup_sha256s": backup_hashes,
            }
        )
        current_prepared = connector.read(prepared_path)
        if current_prepared is None:
            _create_verified(connector, prepared_path, prepared_bytes)
        elif current_prepared != prepared_bytes:
            raise SourceError("transaction prepared record collision")
        recovery = plan_transaction_recovery(
            plan.intent,
            json.loads(prepared_bytes.decode("utf-8")),
            _current_hashes(connector, plan.targets),
        )
    if recovery.action in {
        "aborted",
        "rolled-back",
        "applied",
        "no-op",
        "manual-conflict",
    }:
        terminal_path = f"{base}/{recovery.action}.json"
        _ensure_terminal(connector, terminal_path, recovery.action, intent_hash)
        return recovery.action
    if recovery.action != "rollback":
        raise SourceError(f"unknown recovery action: {recovery.action}")
    target_by_path = {target.path: target for target in plan.targets}
    for path in recovery.restore_paths:
        target = target_by_path[path]
        if target.input_bytes is None:
            connector.delete(path)
            if connector.read(path) is not None:
                raise SourceError(f"connector delete acknowledgement mismatch: {path}")
        else:
            _write_verified(connector, path, target.input_bytes)
    reread = _current_hashes(connector, plan.targets)
    expected = {
        target.path: None if target.input_bytes is None else sha256(target.input_bytes)
        for target in plan.targets
    }
    if reread != expected:
        raise SourceError("rollback did not restore every input hash")
    terminal_path = f"{base}/rolled-back.json"
    _ensure_terminal(connector, terminal_path, "rolled-back", intent_hash)
    return "rolled-back"


def execute_transaction(
    connector: ConnectorPort,
    transaction_root: str,
    plan: TransactionPlan,
) -> str:
    """Execute one transaction attempt and recover any one-shot connector failure."""
    base = f"{transaction_root.rstrip('/')}/{plan.transaction_id}"
    intent_raw = canonical_json(plan.intent)
    intent_hash = sha256(intent_raw)
    intent_path = f"{base}/intent.json"
    try:
        current = _current_hashes(connector, plan.targets)
        expected_inputs = {
            target.path: None
            if target.input_bytes is None
            else sha256(target.input_bytes)
            for target in plan.targets
        }
        if current != expected_inputs:
            raise SourceError("transaction optimistic input hash mismatch")
        _create_verified(connector, intent_path, intent_raw)
        backup_hashes: list[str] = []
        for index, target in enumerate(plan.targets):
            backup = canonical_json(
                {
                    "version": 1,
                    "path": target.path,
                    "input_sha256": None
                    if target.input_bytes is None
                    else sha256(target.input_bytes),
                    "input_base64": None
                    if target.input_bytes is None
                    else base64.b64encode(target.input_bytes).decode("ascii"),
                }
            )
            backup_path = f"{base}/backups/{index:06d}.json"
            _create_verified(connector, backup_path, backup)
            backup_hashes.append(sha256(backup))
        prepared = canonical_json(
            {
                "version": 1,
                "intent_sha256": intent_hash,
                "backup_sha256s": backup_hashes,
            }
        )
        _create_verified(connector, f"{base}/prepared.json", prepared)
        if not plan.targets:
            _create_verified(
                connector, f"{base}/no-op.json", _terminal_record("no-op", intent_hash)
            )
            return "no-op"
        for index, target in enumerate(plan.targets):
            current_bytes = connector.read(target.path)
            expected = target.input_bytes
            if current_bytes != expected:
                raise SourceError(f"target changed before write: {target.path}")
            _write_verified(connector, target.path, target.output_bytes)
            progress = canonical_json(
                {
                    "version": 1,
                    "index": index,
                    "path": target.path,
                    "output_sha256": sha256(target.output_bytes),
                }
            )
            _create_verified(connector, f"{base}/progress/{index:06d}.json", progress)
        _create_verified(
            connector, f"{base}/applied.json", _terminal_record("applied", intent_hash)
        )
        return "applied"
    except (OSError, SourceError):
        if connector.read(intent_path) is None:
            raise
        return recover_transaction(
            connector,
            transaction_root,
            plan,
            abort_unprepared=True,
        )


def _load_input(path: str) -> Mapping[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    value = json.loads(raw)
    if not isinstance(value, Mapping) or value.get("version") != VERSION:
        raise SourceError("input.version must be 1")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render deterministic Atlas source artifacts."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    merge = subparsers.add_parser("merge-artifact")
    merge.add_argument("--input", required=True)
    route = subparsers.add_parser("render-route-artifact")
    route.add_argument("--input", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = _load_input(args.input)
        if args.command == "merge-artifact":
            allowed = {
                "version",
                "staged_artifact_text",
                "evidence_bundle",
                "event",
                "source_state",
                "living_artifact_text",
                "fresh_capture",
            }
            if set(payload) != allowed:
                raise SourceError("merge-artifact input fields are invalid")
            artifact_text = merge_artifact(
                payload["staged_artifact_text"],
                payload["evidence_bundle"],
                payload["event"],
                payload["source_state"],
                living_artifact_text=payload["living_artifact_text"],
                fresh_capture=payload["fresh_capture"],
            )
        else:
            allowed = {"version", "artifact_text", "route_event", "route_status"}
            if set(payload) != allowed:
                raise SourceError("render-route-artifact input fields are invalid")
            artifact_text = render_route_artifact(
                payload["artifact_text"],
                payload["route_event"],
                payload["route_status"],
            )
        result = {
            "ok": True,
            "artifact_text": artifact_text,
            "artifact_sha256": sha256(artifact_text.encode("utf-8")),
        }
        sys.stdout.write(
            json.dumps(
                result, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            + "\n"
        )
        return 0
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        TypeError,
        SourceError,
        ValueError,
    ) as exc:
        print(f"atlas-source: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
