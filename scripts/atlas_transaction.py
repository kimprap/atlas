#!/usr/bin/env python3
"""Provider-neutral transaction provenance and recovery mechanics."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol


VERSION = 1
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class TransactionError(ValueError):
    """A transaction record, target, or recovery invariant is invalid."""


class TransactionRecordError(TransactionError):
    """A connector could not safely read an immutable transaction record."""

    def __init__(
        self, path: str, detail: str = "immutable transaction record is unreadable"
    ):
        self.path = path
        self.detail = detail
        super().__init__(detail)


class TransactionTargetConflict(TransactionError):
    """A live target changed while a transaction operation was being applied."""

    def __init__(self, path: str, detail: str = "transaction target revision conflict"):
        self.path = path
        self.detail = detail
        super().__init__(detail)


def canonical_json(value: Any) -> bytes:
    """Encode one canonical compact JSON record with exactly one LF."""
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


@dataclass(frozen=True)
class TransactionTarget:
    path: str
    input_bytes: bytes | None
    output_bytes: bytes

    def intent_value(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "input_sha256": (
                None if self.input_bytes is None else sha256(self.input_bytes)
            ),
            "output_sha256": sha256(self.output_bytes),
        }


@dataclass(frozen=True)
class TransactionIdentity:
    """Owner-bound identity fields for the transaction ID and immutable intent."""

    base: Mapping[str, Any]
    intent: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TransactionPlan:
    base_transaction_id: str
    transaction_id: str
    attempt: int
    predecessor_sha256: str | None
    intent: dict[str, Any]
    targets: tuple[TransactionTarget, ...]
    transaction_root: str = ".atlas/transactions"


@dataclass(frozen=True)
class TransactionPolicy:
    """One owner-parametric journal policy for the shared machine."""

    owner_id: str
    target_allowlist: TargetAllowlist
    target_rank: TargetRank
    identity_binding: IdentityBinding
    event_validator: Callable[
        [Mapping[str, Any], str, Sequence[TransactionTarget]], Mapping[str, Any]
    ]
    base_formula: Callable[
        [Mapping[str, Any], str, Sequence[TransactionTarget]], Mapping[str, Any]
    ] | None = None
    transaction_root: str = ".atlas/transactions"
    terminal_statuses: tuple[str, ...] = (
        "applied",
        "no-op",
        "aborted",
        "rolled-back",
        "manual-conflict",
    )
    terminal_validator: Callable[
        [str, Mapping[str, Any], bytes, TransactionPlan], None
    ] | None = None


@dataclass(frozen=True)
class Journal:
    record: Mapping[str, Any]
    plan: TransactionPlan
    status: str | None
    terminal: bytes | None
    prepared: Mapping[str, Any] | None
    record_names: tuple[str, ...]


class ConnectorPort(Protocol):
    def read(self, path: str) -> bytes | None: ...
    def read_record(self, path: str) -> bytes | None: ...
    def create(self, path: str, data: bytes) -> None: ...
    def write(self, path: str, data: bytes, expected_revision: str) -> None: ...
    def delete(self, path: str, expected_revision: str) -> None: ...


class TransactionPort(Protocol):
    def list(self, path: str) -> list[str]: ...


TargetAllowlist = Collection[str] | Callable[[str], bool]
TargetRank = Callable[[str], tuple[int, str]]
IdentityBinding = (
    TransactionIdentity
    | Mapping[str, Any]
    | Callable[[Mapping[str, Any], str], TransactionIdentity | Mapping[str, Any]]
)
PostValidator = Callable[[ConnectorPort, TransactionPlan], Any]


def _read_record(connector: ConnectorPort, path: str) -> bytes | None:
    try:
        return connector.read_record(path)
    except TransactionRecordError:
        raise
    except ValueError as exc:
        if getattr(exc, "_atlas_connector_kind", None) in {
            "binding",
            "mutation_unavailable",
            "conflict",
            "io",
            "durability",
        }:
            raise
        raise TransactionRecordError(path) from exc


def _revision_for_bytes(value: bytes | None) -> str:
    return "missing" if value is None else f"sha256:{sha256(value)}"


def event_record_value(
    event_record: Mapping[str, Any], plan: TransactionPlan
) -> dict[str, Any]:
    return {
        "version": VERSION,
        "event_record": dict(event_record),
        "attempt": plan.attempt,
        "predecessor_sha256": plan.predecessor_sha256,
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


def store_event(
    connector: ConnectorPort,
    transaction_root: str,
    event_record: Mapping[str, Any],
    plan: TransactionPlan,
) -> None:
    path = f"{transaction_root.rstrip('/')}/{plan.transaction_id}/event.json"
    body = canonical_json(event_record_value(event_record, plan))
    current = _read_record(connector, path)
    if current is None:
        connector.create(path, body)
    elif current != body:
        raise TransactionError("transaction event collision")


def _allowlisted(target_allowlist: TargetAllowlist, path: str) -> bool:
    try:
        allowed = (
            target_allowlist(path)
            if callable(target_allowlist)
            else path in target_allowlist
        )
    except Exception as exc:
        raise TransactionError("transaction target allowlist failed") from exc
    if not isinstance(allowed, bool):
        raise TransactionError("transaction target allowlist must return bool")
    return allowed


def _target_key(
    path: str,
    *,
    target_allowlist: TargetAllowlist,
    target_rank: TargetRank,
) -> tuple[int, str]:
    if (
        not isinstance(path, str)
        or not path
        or not _allowlisted(target_allowlist, path)
    ):
        raise TransactionError(
            f"transaction target is outside the owner write set: {path}"
        )
    try:
        rank = target_rank(path)
    except TransactionError:
        raise
    except Exception as exc:
        raise TransactionError("transaction target rank failed") from exc
    if (
        not isinstance(rank, tuple)
        or len(rank) != 2
        or type(rank[0]) is not int
        or not isinstance(rank[1], str)
    ):
        raise TransactionError("transaction target rank is invalid")
    return rank


def _resolve_identity(
    identity_binding: IdentityBinding,
    event_record: Mapping[str, Any],
    event_hash: str,
) -> TransactionIdentity:
    value: Any
    if isinstance(identity_binding, TransactionIdentity):
        value = identity_binding
    elif callable(identity_binding):
        try:
            value = identity_binding(event_record, event_hash)
        except TransactionError:
            raise
        except Exception as exc:
            raise TransactionError("transaction identity binding failed") from exc
    else:
        value = identity_binding
    if isinstance(value, TransactionIdentity):
        identity = value
    elif isinstance(value, Mapping):
        identity = TransactionIdentity(value, value)
    else:
        raise TransactionError("transaction identity binding must be an object")
    if not isinstance(identity.base, Mapping) or not isinstance(
        identity.intent, Mapping
    ):
        raise TransactionError("transaction identity fields must be objects")
    base = dict(identity.base)
    intent = dict(identity.intent)
    if "targets" in base or "targets" in intent:
        raise TransactionError("transaction identity cannot bind targets")
    if "event_record_sha256" in base and base["event_record_sha256"] != event_hash:
        raise TransactionError("transaction identity event hash does not match")
    if "event_record_sha256" in intent and intent["event_record_sha256"] != event_hash:
        raise TransactionError("transaction identity event hash does not match")
    return TransactionIdentity(base, intent)


def _validate_plan_policy(
    targets: Sequence[TransactionTarget],
    *,
    target_allowlist: TargetAllowlist | None,
    target_rank: TargetRank | None,
) -> None:
    if (target_allowlist is None) != (target_rank is None):
        raise TransactionError("transaction target policy is incomplete")
    if target_allowlist is None or target_rank is None:
        return
    for target in targets:
        _target_key(
            target.path,
            target_allowlist=target_allowlist,
            target_rank=target_rank,
        )


def build_transaction_plan(
    *,
    event_path: str,
    event_record: Mapping[str, Any],
    targets: Sequence[TransactionTarget],
    target_allowlist: TargetAllowlist,
    target_rank: TargetRank,
    identity_binding: IdentityBinding,
    attempt: int = 0,
    predecessor_sha256: str | None = None,
    base_formula: Callable[
        [Mapping[str, Any], str, Sequence[TransactionTarget]], Mapping[str, Any]
    ]
    | None = None,
    transaction_root: str = ".atlas/transactions",
) -> TransactionPlan:
    event_raw = canonical_json(event_record)
    event_hash = sha256(event_raw)
    if attempt < 0 or (attempt == 0) != (predecessor_sha256 is None):
        raise TransactionError("transaction attempt/predecessor mismatch")
    if (
        predecessor_sha256 is not None
        and _HASH_RE.fullmatch(predecessor_sha256) is None
    ):
        raise TransactionError("transaction predecessor hash is invalid")
    for target in targets:
        _target_key(
            target.path,
            target_allowlist=target_allowlist,
            target_rank=target_rank,
        )
    ordered = tuple(
        sorted(
            targets,
            key=lambda target: _target_key(
                target.path,
                target_allowlist=target_allowlist,
                target_rank=target_rank,
            ),
        )
    )
    if tuple(targets) != ordered:
        raise TransactionError("transaction targets are not in canonical order")
    target_values = [target.intent_value() for target in targets]
    identity = _resolve_identity(identity_binding, event_record, event_hash)
    if base_formula is None:
        base_value = dict(identity.base)
        base_value["event_record_sha256"] = event_hash
        base_value["targets"] = target_values
    else:
        try:
            base_value = dict(base_formula(event_record, event_hash, tuple(targets)))
        except TransactionError:
            raise
        except Exception as exc:
            raise TransactionError("transaction base identity failed") from exc
        if not base_value:
            raise TransactionError("transaction base identity is empty")
    base = sha256(canonical_json(base_value))[:16]
    transaction_id = f"{base}-a{attempt:06d}"
    intent = dict(identity.intent)
    reserved = {
        "version",
        "base_transaction_id",
        "transaction_id",
        "attempt",
        "predecessor_sha256",
        "event_path",
        "event_record_sha256",
        "targets",
    }
    if reserved.intersection(intent):
        raise TransactionError("transaction identity uses reserved intent fields")
    intent.update(
        {
            "version": VERSION,
            "base_transaction_id": base,
            "transaction_id": transaction_id,
            "attempt": attempt,
            "predecessor_sha256": predecessor_sha256,
            "event_path": event_path,
            "event_record_sha256": event_hash,
            "targets": target_values,
        }
    )
    return TransactionPlan(
        base,
        transaction_id,
        attempt,
        predecessor_sha256,
        intent,
        tuple(targets),
        transaction_root,
    )
def _create_verified(connector: ConnectorPort, path: str, data: bytes) -> None:
    try:
        connector.create(path, data)
    except ValueError as exc:
        if getattr(exc, "_atlas_connector_kind", None) != "conflict":
            raise
        current = _read_record(connector, path)
        if current == data:
            return
        raise TransactionError(f"immutable record collision: {path}") from exc
    if _read_record(connector, path) != data:
        raise TransactionError(f"connector acknowledgement mismatch: {path}")


def _write_verified(
    connector: ConnectorPort,
    path: str,
    data: bytes,
    expected_revision: str,
) -> None:
    try:
        connector.write(path, data, expected_revision)
        acknowledged = connector.read(path)
    except TransactionError:
        raise
    except ValueError as exc:
        if getattr(exc, "_atlas_connector_kind", None) in {
            "binding",
            "mutation_unavailable",
            "io",
            "durability",
        }:
            raise
        raise TransactionTargetConflict(path) from exc
    if acknowledged != data:
        raise TransactionError(f"connector acknowledgement mismatch: {path}")


def _delete_verified(
    connector: ConnectorPort,
    path: str,
    expected_revision: str,
) -> None:
    try:
        connector.delete(path, expected_revision)
        acknowledged = connector.read(path)
    except TransactionError:
        raise
    except ValueError as exc:
        if getattr(exc, "_atlas_connector_kind", None) in {
            "binding",
            "mutation_unavailable",
            "io",
            "durability",
        }:
            raise
        raise TransactionTargetConflict(path) from exc
    if acknowledged is not None:
        raise TransactionError(f"connector delete acknowledgement mismatch: {path}")


def _current_hashes(
    connector: ConnectorPort, targets: Sequence[TransactionTarget]
) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for target in targets:
        try:
            current = connector.read(target.path)
        except TransactionError:
            raise
        except ValueError as exc:
            if getattr(exc, "_atlas_connector_kind", None) in {
                "binding",
                "mutation_unavailable",
                "io",
                "durability",
            }:
                raise
            raise TransactionTargetConflict(target.path) from exc
        values[target.path] = None if current is None else sha256(current)
    return values


def _terminal_record(
    status: str, intent_sha256: str, proof: Mapping[str, Any] | None = None
) -> bytes:
    value: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "intent_sha256": intent_sha256,
    }
    if proof is not None:
        value["owner_proof"] = dict(proof)
    return canonical_json(value)


def build_successor_plan(
    plan: TransactionPlan,
    *,
    event_path: str,
    event_record: Mapping[str, Any],
    terminal_record: bytes,
    target_allowlist: TargetAllowlist,
    target_rank: TargetRank,
    identity_binding: IdentityBinding,
    base_formula: Callable[
        [Mapping[str, Any], str, Sequence[TransactionTarget]], Mapping[str, Any]
    ]
    | None = None,
    terminal_validator: Callable[[str, bytes, TransactionPlan], None] | None = None,
) -> TransactionPlan:
    if plan.attempt != 0:
        raise TransactionError(
            "only the initial transaction attempt may have a successor"
        )
    intent_hash = sha256(canonical_json(plan.intent))
    verified = False
    for status in ("aborted", "rolled-back"):
        if terminal_record == _terminal_record(status, intent_hash):
            verified = True
            break
    if not verified and terminal_validator is not None:
        try:
            terminal_validator("aborted", terminal_record, plan)
            verified = True
        except Exception:
            try:
                terminal_validator("rolled-back", terminal_record, plan)
                verified = True
            except Exception as exc:
                raise TransactionError(
                    "successor requires a verified aborted or rolled-back terminal record"
                ) from exc
    if not verified:
        raise TransactionError(
            "successor requires the verified aborted or rolled-back terminal record"
        )
    successor = build_transaction_plan(
        event_path=event_path,
        event_record=event_record,
        targets=plan.targets,
        target_allowlist=target_allowlist,
        target_rank=target_rank,
        identity_binding=identity_binding,
        attempt=plan.attempt + 1,
        predecessor_sha256=sha256(terminal_record),
        base_formula=base_formula,
        transaction_root=plan.transaction_root,
    )
    if successor.base_transaction_id != plan.base_transaction_id:
        raise TransactionError("successor event or outputs differ from the predecessor")
    return successor
def _ensure_terminal(
    connector: ConnectorPort,
    path: str,
    status: str,
    intent_sha256: str,
    proof: Mapping[str, Any] | None = None,
) -> None:
    expected = _terminal_record(status, intent_sha256, proof)
    current = _read_record(connector, path)
    if current is None:
        _create_verified(connector, path, expected)
    elif current != expected:
        raise TransactionError(f"terminal record collision: {path}")

def abort_event_only(
    connector: ConnectorPort,
    transaction_root: str,
    plan: TransactionPlan,
    event_record: Mapping[str, Any],
    *,
    terminal_factory: Callable[
        [str, Mapping[str, Any], TransactionPlan], bytes
    ]
    | None = None,
    terminal_validator: Callable[
        [str, Mapping[str, Any], bytes, TransactionPlan], None
    ]
    | None = None,
) -> str:
    """Close an event-only journal without fabricating intent or backups."""
    base = f"{transaction_root.rstrip('/')}/{plan.transaction_id}"
    names = _record_names(connector, base)
    allowed = {"event.json", "aborted.json"}
    unknown = sorted(set(names) - allowed)
    if unknown:
        raise TransactionRecordError(
            f"{base}/{unknown[0]}",
            "event-only transaction has nonterminal records",
        )
    event_path = f"{base}/event.json"
    if _read_record(connector, event_path) is None:
        raise TransactionRecordError(event_path, "transaction event is missing")
    if _read_record(connector, f"{base}/intent.json") is not None:
        raise TransactionError("event-only transaction already has an intent")
    if _read_record(connector, f"{base}/prepared.json") is not None:
        raise TransactionRecordError(
            f"{base}/prepared.json",
            "event-only transaction has a prepared record",
        )
    factory = terminal_factory or (
        lambda status, event, candidate: _terminal_record(
            status,
            sha256(canonical_json(candidate.intent)),
        )
    )
    try:
        terminal = factory("aborted", event_record, plan)
        _decode_record(terminal, f"{base}/aborted.json")
    except TransactionRecordError:
        raise
    except (TypeError, ValueError, UnicodeError) as exc:
        raise TransactionRecordError(
            f"{base}/aborted.json",
            "event-only terminal record is malformed",
        ) from exc
    if terminal_validator is not None:
        try:
            terminal_validator("aborted", event_record, terminal, plan)
        except TransactionRecordError:
            raise
        except Exception as exc:
            raise TransactionRecordError(
                f"{base}/aborted.json",
                "event-only terminal proof is malformed",
            ) from exc
    current = _read_record(connector, f"{base}/aborted.json")
    if current is None:
        _create_verified(connector, f"{base}/aborted.json", terminal)
    elif current != terminal:
        raise TransactionError(f"terminal record collision: {base}/aborted.json")
    return "aborted"


@dataclass(frozen=True)
class _RecoveryPlan:
    action: str
    classifications: dict[str, str]
    restore_paths: list[str] = field(default_factory=list)
    output_revisions: dict[str, str] = field(default_factory=dict)


def _plan_recovery(
    intent: Mapping[str, Any],
    prepared: Mapping[str, Any] | None,
    current_hashes: Mapping[str, str | None],
    *,
    abort: bool = False,
) -> _RecoveryPlan:
    if not isinstance(intent, Mapping):
        raise TransactionError("intent must be an object")
    targets = intent.get("targets")
    if not isinstance(targets, list):
        raise TransactionError("intent.targets must be an array")
    if prepared is not None and not isinstance(prepared, Mapping):
        raise TransactionError("prepared must be an object or null")
    normalized: list[tuple[str, str | None, str]] = []
    seen: set[str] = set()
    for index, target in enumerate(targets):
        if not isinstance(target, Mapping) or set(target) != {
            "path",
            "input_sha256",
            "output_sha256",
        }:
            raise TransactionError(f"intent.targets[{index}] has invalid fields")
        path = target.get("path")
        input_hash = target.get("input_sha256")
        output_hash = target.get("output_sha256")
        if not isinstance(path, str) or not path or path in seen:
            raise TransactionError(f"intent.targets[{index}].path is invalid")
        if input_hash is not None and (
            not isinstance(input_hash, str) or _HASH_RE.fullmatch(input_hash) is None
        ):
            raise TransactionError(f"intent.targets[{index}].input_sha256 is invalid")
        if not isinstance(output_hash, str) or _HASH_RE.fullmatch(output_hash) is None:
            raise TransactionError(f"intent.targets[{index}].output_sha256 is invalid")
        if input_hash == output_hash:
            raise TransactionError(f"intent.targets[{index}] is not a changed target")
        seen.add(path)
        normalized.append((path, input_hash, output_hash))
    if set(current_hashes) != seen:
        raise TransactionError("current_hashes must contain exactly the target paths")
    if not normalized:
        return _RecoveryPlan("no-op", {})

    classifications: dict[str, str] = {}
    output_revisions: dict[str, str] = {}
    for path, input_hash, output_hash in normalized:
        current = current_hashes[path]
        if current == output_hash:
            classifications[path] = "output"
            output_revisions[path] = f"sha256:{output_hash}"
        elif current == input_hash:
            classifications[path] = "input"
        else:
            classifications[path] = "other"

    if prepared is None:
        if any(value != "input" for value in classifications.values()):
            return _RecoveryPlan("manual-conflict", classifications)
        return _RecoveryPlan("aborted" if abort else "prepare", classifications)
    if "other" in classifications.values():
        return _RecoveryPlan("manual-conflict", classifications)
    if all(value == "output" for value in classifications.values()):
        return _RecoveryPlan("applied", classifications)
    if all(value == "input" for value in classifications.values()):
        return _RecoveryPlan("rolled-back", classifications)
    restore = [
        path for path, _, _ in reversed(normalized) if classifications[path] == "output"
    ]
    return _RecoveryPlan("rollback", classifications, restore, output_revisions)


def _force_rollback(
    plan: TransactionPlan,
    current_hashes: Mapping[str, str | None],
) -> _RecoveryPlan:
    output_paths = [
        target.path
        for target in reversed(plan.targets)
        if current_hashes[target.path] == sha256(target.output_bytes)
    ]
    if not output_paths:
        return _RecoveryPlan(
            "rolled-back",
            {path: "input" for path in current_hashes},
        )
    classifications = {
        target.path: (
            "output"
            if current_hashes[target.path] == sha256(target.output_bytes)
            else "input"
        )
        for target in plan.targets
    }
    output_revisions = {
        target.path: f"sha256:{sha256(target.output_bytes)}"
        for target in plan.targets
        if classifications[target.path] == "output"
    }
    return _RecoveryPlan(
        "rollback",
        classifications,
        output_paths,
        output_revisions,
    )


def _run_post_validator(
    post_validator: PostValidator,
    connector: ConnectorPort,
    plan: TransactionPlan,
) -> Any:
    try:
        return post_validator(connector, plan)
    except TransactionError:
        raise
    except OSError:
        # Connector I/O and durability failures do not qualify a rollback;
        # recovery must preserve the open immutable identity.
        raise
    except Exception as exc:
        if getattr(exc, "_atlas_connector_kind", None) in {
            "binding",
            "mutation_unavailable",
            "conflict",
            "io",
            "durability",
        }:
            raise
        raise TransactionError("owner post-validation failed") from exc
def recover_transaction(
    connector: ConnectorPort,
    transaction_root: str,
    plan: TransactionPlan,
    *,
    abort_unprepared: bool = False,
    post_validation_failed: bool = False,
    target_allowlist: TargetAllowlist | None = None,
    target_rank: TargetRank | None = None,
    post_validator: PostValidator | None = None,
    terminal_validator: Callable[[str, bytes, TransactionPlan], None] | None = None,
) -> str:
    """Recover one existing transaction attempt from connector-reread truth."""
    _validate_plan_policy(
        plan.targets,
        target_allowlist=target_allowlist,
        target_rank=target_rank,
    )
    base = f"{transaction_root.rstrip('/')}/{plan.transaction_id}"
    record_names = _record_names(connector, base)
    if record_names:
        allowed_names = {
            "event.json",
            "intent.json",
            "prepared.json",
            *(f"backups/{index:06d}.json" for index in range(len(plan.targets))),
            *(f"progress/{index:06d}.json" for index in range(len(plan.targets))),
            "applied.json",
            "no-op.json",
            "aborted.json",
            "rolled-back.json",
            "manual-conflict.json",
        }
        unknown_names = sorted(set(record_names) - allowed_names)
        if unknown_names:
            raise TransactionError(
                f"transaction record path is not canonical: {unknown_names[0]}"
            )
    intent_path = f"{base}/intent.json"
    expected_intent = canonical_json(plan.intent)
    if _read_record(connector, intent_path) != expected_intent:
        raise TransactionError("transaction intent is missing or does not match")
    intent_hash = sha256(expected_intent)
    prepared_path = f"{base}/prepared.json"
    prepared_raw = _read_record(connector, prepared_path)
    backup_hashes: list[str] = []
    first_missing_backup: int | None = None
    for index, target in enumerate(plan.targets):
        backup = canonical_json(
            {
                "version": VERSION,
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
        raw_backup = _read_record(connector, backup_path)
        if raw_backup is None:
            if first_missing_backup is None:
                first_missing_backup = index
        elif first_missing_backup is not None:
            raise TransactionError("transaction backup records are not a cumulative prefix")
        elif raw_backup != backup:
            raise TransactionError("transaction backup is missing or malformed")
        backup_hashes.append(sha256(backup))

    prepared: Mapping[str, Any] | None = None
    if prepared_raw is not None:
        if first_missing_backup is not None:
            raise TransactionError("transaction prepared record is malformed")
        expected_prepared = canonical_json(
            {
                "version": VERSION,
                "intent_sha256": intent_hash,
                "backup_sha256s": backup_hashes,
            }
        )
        if prepared_raw != expected_prepared:
            raise TransactionError("transaction prepared record is malformed")
        try:
            prepared = json.loads(prepared_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TransactionError("transaction prepared record is malformed") from exc
    if not plan.targets and prepared_raw is not None:
        raise TransactionError("no-op transaction cannot have a prepared record")

    expected_progresses = [
        canonical_json(
            {
                "version": VERSION,
                "index": index,
                "path": target.path,
                "output_sha256": sha256(target.output_bytes),
            }
        )
        for index, target in enumerate(plan.targets)
    ]
    current_progresses = [
        _read_record(connector, f"{base}/progress/{index:06d}.json")
        for index in range(len(expected_progresses))
    ]
    first_missing_progress: int | None = None
    for index, (current_progress, expected_progress) in enumerate(
        zip(current_progresses, expected_progresses, strict=True)
    ):
        if current_progress is None:
            if first_missing_progress is None:
                first_missing_progress = index
            continue
        if prepared_raw is None:
            raise TransactionError("transaction progress requires prepared")
        if first_missing_progress is not None:
            raise TransactionError(
                "transaction progress records are not a cumulative prefix"
            )
        if current_progress != expected_progress:
            raise TransactionError("transaction progress record collision")

    existing_terminals = [
        status
        for status in ("applied", "no-op", "aborted", "rolled-back", "manual-conflict")
        if _read_record(connector, f"{base}/{status}.json") is not None
    ]
    if existing_terminals:
        if len(existing_terminals) != 1:
            raise TransactionError("transaction has multiple terminal records")
        status = existing_terminals[0]
        if status == "no-op" and (plan.targets or prepared_raw is not None):
            raise TransactionError(
                "no-op terminal requires an empty target set and no prepared record"
            )
        if status == "aborted" and prepared_raw is not None:
            raise TransactionError("aborted terminal requires no prepared record")
        if status in {"applied", "rolled-back", "manual-conflict"} and (
            prepared_raw is None
        ):
            raise TransactionError("terminal requires prepared record")
        if status == "applied" and first_missing_progress is not None:
            raise TransactionError("applied terminal requires every progress record")
        terminal_path = f"{base}/{status}.json"
        terminal_raw = _read_record(connector, terminal_path)
        if terminal_raw != _terminal_record(status, intent_hash):
            if terminal_validator is None:
                raise TransactionError("transaction terminal record is malformed")
            try:
                terminal_validator(status, terminal_raw, plan)
            except TransactionError:
                raise
            except Exception as exc:
                raise TransactionError("transaction terminal proof is malformed") from exc
        return status
    current_hashes = _current_hashes(connector, plan.targets)
    recovery = _plan_recovery(
        plan.intent,
        prepared,
        current_hashes,
        abort=abort_unprepared,
    )
    owner_proof: Mapping[str, Any] | None = None
    if recovery.action == "applied" and post_validator is not None:
        try:
            value = _run_post_validator(post_validator, connector, plan)
            if value is not None:
                if not isinstance(value, Mapping):
                    raise TransactionError("owner post-validation proof is invalid")
                owner_proof = dict(value)
        except TransactionError:
            recovery = _force_rollback(plan, current_hashes)
    elif post_validation_failed and recovery.action == "applied":
        recovery = _force_rollback(plan, current_hashes)

    if recovery.action == "prepare":
        # A missing prepared record is an unprepared crash prefix. The
        # immutable journal is never completed by fabricating backup records;
        # close the attempt as aborted and leave its observed prefix intact.
        recovery = _RecoveryPlan("aborted", recovery.classifications)
    if recovery.action == "applied" and first_missing_progress is not None:
        for index in range(first_missing_progress, len(expected_progresses)):
            _create_verified(
                connector,
                f"{base}/progress/{index:06d}.json",
                expected_progresses[index],
            )

    if recovery.action in {
        "aborted",
        "rolled-back",
        "applied",
        "no-op",
        "manual-conflict",
    }:
        terminal_path = f"{base}/{recovery.action}.json"
        _ensure_terminal(
            connector,
            terminal_path,
            recovery.action,
            intent_hash,
            owner_proof if recovery.action == "applied" else None,
        )
        return recovery.action
    if recovery.action != "rollback":
        raise TransactionError(f"unknown recovery action: {recovery.action}")
    target_by_path = {target.path: target for target in plan.targets}
    for path in recovery.restore_paths:
        target = target_by_path[path]
        expected_revision = recovery.output_revisions.get(path)
        if expected_revision is None:
            raise TransactionError(f"rollback output revision is missing: {path}")
        if target.input_bytes is None:
            _delete_verified(connector, path, expected_revision)
        else:
            _write_verified(
                connector,
                path,
                target.input_bytes,
                expected_revision,
            )
    reread = _current_hashes(connector, plan.targets)
    expected = {
        target.path: None if target.input_bytes is None else sha256(target.input_bytes)
        for target in plan.targets
    }
    if reread != expected:
        raise TransactionError("rollback did not restore every input hash")
    terminal_path = f"{base}/rolled-back.json"
    _ensure_terminal(connector, terminal_path, "rolled-back", intent_hash)
    return "rolled-back"


def execute_transaction(
    connector: ConnectorPort,
    transaction_root: str,
    plan: TransactionPlan,
    *,
    target_allowlist: TargetAllowlist | None = None,
    target_rank: TargetRank | None = None,
    post_validator: PostValidator | None = None,
    terminal_validator: Callable[[str, bytes, TransactionPlan], None] | None = None,
    surface_post_intent_failure: bool = False,
) -> str:
    """Execute one transaction attempt and recover one-shot connector failures.

    An owner may opt into surfacing the original post-intent interruption when
    reread recovery reaches an applied terminal; the default preserves the
    existing one-shot status return.
    """
    _validate_plan_policy(
        plan.targets,
        target_allowlist=target_allowlist,
        target_rank=target_rank,
    )
    base = f"{transaction_root.rstrip('/')}/{plan.transaction_id}"
    intent_raw = canonical_json(plan.intent)
    intent_hash = sha256(intent_raw)
    intent_path = f"{base}/intent.json"
    post_validation_failed = False
    owner_proof: Mapping[str, Any] | None = None
    try:
        current_inputs: dict[str, bytes | None] = {}
        for target in plan.targets:
            try:
                current_inputs[target.path] = connector.read(target.path)
            except ValueError as exc:
                if getattr(exc, "_atlas_connector_kind", None) in {
                    "binding",
                    "mutation_unavailable",
                    "conflict",
                    "io",
                    "durability",
                }:
                    raise
                raise TransactionTargetConflict(target.path) from exc
        current = {
            path: None if value is None else sha256(value)
            for path, value in current_inputs.items()
        }
        expected_inputs = {
            target.path: (
                None if target.input_bytes is None else sha256(target.input_bytes)
            )
            for target in plan.targets
        }
        if current != expected_inputs:
            raise TransactionError("transaction optimistic input hash mismatch")
        _create_verified(connector, intent_path, intent_raw)
        backup_hashes: list[str] = []
        for index, target in enumerate(plan.targets):
            backup = canonical_json(
                {
                    "version": VERSION,
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
            _create_verified(connector, backup_path, backup)
            backup_hashes.append(sha256(backup))
        if not plan.targets:
            _create_verified(
                connector, f"{base}/no-op.json", _terminal_record("no-op", intent_hash)
            )
            return "no-op"
        prepared = canonical_json(
            {
                "version": VERSION,
                "intent_sha256": intent_hash,
                "backup_sha256s": backup_hashes,
            }
        )
        _create_verified(connector, f"{base}/prepared.json", prepared)
        for index, target in enumerate(plan.targets):
            current_bytes = current_inputs[target.path]
            if current_bytes != target.input_bytes:
                raise TransactionError(f"target changed before write: {target.path}")
            _write_verified(
                connector,
                target.path,
                target.output_bytes,
                _revision_for_bytes(current_bytes),
            )
            progress = canonical_json(
                {
                    "version": VERSION,
                    "index": index,
                    "path": target.path,
                    "output_sha256": sha256(target.output_bytes),
                }
            )
            _create_verified(
                connector,
                f"{base}/progress/{index:06d}.json",
                progress,
            )
        if post_validator is not None:
            try:
                value = _run_post_validator(post_validator, connector, plan)
                if value is not None:
                    if not isinstance(value, Mapping):
                        raise TransactionError("owner post-validation proof is invalid")
                    owner_proof = dict(value)
            except TransactionError:
                post_validation_failed = True
                raise
        _create_verified(
            connector,
            f"{base}/applied.json",
            _terminal_record("applied", intent_hash, owner_proof),
        )
        return "applied"
    except (OSError, TransactionError) as exc:
        if _read_record(connector, intent_path) is None:
            raise
        status = recover_transaction(
            connector,
            transaction_root,
            plan,
            abort_unprepared=True,
            post_validation_failed=post_validation_failed,
            target_allowlist=target_allowlist,
            target_rank=target_rank,
            post_validator=post_validator if not post_validation_failed else None,
            terminal_validator=terminal_validator,
        )
        if surface_post_intent_failure and status == "applied":
            raise TransactionError(
                f"transaction interrupted after intent; recovery reached {status}"
            ) from exc
        return status
def _unique_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _decode_record(raw: bytes, path: str) -> Any:
    if not isinstance(raw, bytes):
        raise TransactionRecordError(path, "immutable record is not bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object_pairs,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise TransactionRecordError(path, "immutable record is invalid JSON") from exc
    try:
        canonical = canonical_json(value)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise TransactionRecordError(path, "immutable record is not canonical JSON") from exc
    if canonical != raw:
        raise TransactionRecordError(path, "immutable record is not canonical JSON")
    return value


def _record_names(connector: ConnectorPort, root: str) -> tuple[str, ...]:
    listing = getattr(connector, "list", None)
    if not callable(listing):
        return ()
    try:
        values = listing(root)
    except FileNotFoundError:
        return ()
    except TransactionError:
        raise
    except OSError:
        raise
    except ValueError as exc:
        if getattr(exc, "_atlas_connector_kind", None) in {
            "binding",
            "mutation_unavailable",
            "conflict",
            "io",
            "durability",
        }:
            raise
        raise TransactionRecordError(root, "transaction namespace is unreadable") from exc
    except (TypeError, AttributeError) as exc:
        raise TransactionRecordError(root, "transaction namespace is unreadable") from exc
    if type(values) is not list:
        raise TransactionRecordError(root, "transaction namespace listing is invalid")
    prefix = root.rstrip("/") + "/"
    names: list[str] = []
    for value in values:
        if not isinstance(value, str):
            raise TransactionRecordError(root, "transaction namespace listing is invalid")
        name = value[len(prefix) :] if value.startswith(prefix) else value
        if (
            not name
            or name.startswith("/")
            or any(part in {"", ".", ".."} for part in name.split("/"))
        ):
            raise TransactionRecordError(root, "transaction record path is invalid")
        names.append(name)
    if len(set(names)) != len(names):
        raise TransactionRecordError(root, "transaction namespace listing has duplicates")
    try:
        return tuple(sorted(names, key=lambda value: value.encode("utf-8")))
    except UnicodeError as exc:
        raise TransactionRecordError(
            root, "transaction namespace listing is not valid UTF-8"
        ) from exc


def _target_records(
    outer: Mapping[str, Any],
    path: str,
    policy: TransactionPolicy,
) -> tuple[TransactionTarget, ...]:
    rows = outer.get("targets")
    if type(rows) is not list:
        raise TransactionRecordError(path, "transaction targets are invalid")
    targets: list[TransactionTarget] = []
    seen_paths: set[str] = set()
    for index, row in enumerate(rows):
        if type(row) is not dict or set(row) != {
            "path",
            "input_base64",
            "output_base64",
        }:
            raise TransactionRecordError(
                path, f"transaction target {index} is invalid"
            )
        target_path = row["path"]
        input_encoded = row["input_base64"]
        output_encoded = row["output_base64"]
        if (
            not isinstance(target_path, str)
            or not target_path
            or target_path in seen_paths
            or (input_encoded is not None and not isinstance(input_encoded, str))
            or not isinstance(output_encoded, str)
        ):
            raise TransactionRecordError(
                path, f"transaction target {index} fields are invalid"
            )
        try:
            input_bytes = (
                None
                if input_encoded is None
                else base64.b64decode(input_encoded, validate=True)
            )
            output_bytes = base64.b64decode(output_encoded, validate=True)
        except (TypeError, ValueError) as exc:
            raise TransactionRecordError(
                path, f"transaction target {index} bytes are invalid"
            ) from exc
        if (
            input_encoded is not None
            and base64.b64encode(input_bytes).decode("ascii") != input_encoded
        ) or base64.b64encode(output_bytes).decode("ascii") != output_encoded:
            raise TransactionRecordError(
                path, f"transaction target {index} bytes are not canonical"
            )
        if input_bytes is not None and input_bytes == output_bytes:
            raise TransactionRecordError(
                path, f"transaction target {index} is not a changed target"
            )
        seen_paths.add(target_path)
        targets.append(TransactionTarget(target_path, input_bytes, output_bytes))
    try:
        _validate_plan_policy(
            targets,
            target_allowlist=policy.target_allowlist,
            target_rank=policy.target_rank,
        )
    except TransactionError as exc:
        raise TransactionRecordError(path, str(exc)) from exc
    ordered = tuple(
        sorted(
            targets,
            key=lambda target: _target_key(
                target.path,
                target_allowlist=policy.target_allowlist,
                target_rank=policy.target_rank,
            ),
        )
    )
    if tuple(targets) != ordered:
        raise TransactionRecordError(path, "transaction targets are not canonical ordered")
    return tuple(targets)


def load_transaction(
    connector: ConnectorPort,
    transaction_id: str,
    policy: TransactionPolicy,
) -> Journal:
    """Load one immutable journal and prove its complete crash-prefix grammar."""
    if not isinstance(transaction_id, str) or re.fullmatch(
        r"[0-9a-f]{16}-a[0-9]{6}", transaction_id
    ) is None:
        raise TransactionRecordError(transaction_id, "transaction ID is invalid")
    root = f"{policy.transaction_root.rstrip('/')}/{transaction_id}"
    event_path = f"{root}/event.json"
    names = _record_names(connector, root)
    raw_event = _read_record(connector, event_path)
    if raw_event is None:
        raise TransactionRecordError(event_path, "transaction event is missing")
    if names and "event.json" not in names:
        raise TransactionRecordError(event_path, "transaction event is not listed")
    outer = _decode_record(raw_event, event_path)
    if (
        type(outer) is not dict
        or set(outer)
        != {"version", "event_record", "attempt", "predecessor_sha256", "targets"}
        or outer["version"] != VERSION
        or type(outer["attempt"]) is not int
        or outer["attempt"] not in {0, 1}
    ):
        raise TransactionRecordError(event_path, "transaction event envelope is invalid")
    attempt = outer["attempt"]
    predecessor_sha256 = outer["predecessor_sha256"]
    if attempt == 0:
        if predecessor_sha256 is not None:
            raise TransactionRecordError(
                event_path, "attempt-zero predecessor is invalid"
            )
    elif (
        not isinstance(predecessor_sha256, str)
        or _HASH_RE.fullmatch(predecessor_sha256) is None
    ):
        raise TransactionRecordError(event_path, "successor predecessor is invalid")
    if type(outer["event_record"]) is not dict:
        raise TransactionRecordError(event_path, "owner event is invalid")
    targets = _target_records(outer, event_path, policy)
    try:
        record = policy.event_validator(outer["event_record"], event_path, targets)
    except TransactionRecordError:
        raise
    except Exception as exc:
        raise TransactionRecordError(event_path, "owner event is invalid") from exc
    if not isinstance(record, Mapping) or dict(record) != outer["event_record"]:
        raise TransactionRecordError(event_path, "owner event validator changed bytes")
    try:
        plan = build_transaction_plan(
            event_path=event_path,
            event_record=record,
            targets=targets,
            target_allowlist=policy.target_allowlist,
            target_rank=policy.target_rank,
            identity_binding=policy.identity_binding,
            attempt=attempt,
            predecessor_sha256=predecessor_sha256,
            base_formula=policy.base_formula,
            transaction_root=policy.transaction_root,
        )
    except TransactionError as exc:
        raise TransactionRecordError(event_path, "transaction plan is invalid") from exc
    if plan.transaction_id != transaction_id:
        raise TransactionRecordError(event_path, "transaction ID is not bound")
    try:
        expected_event = canonical_json(event_record_value(record, plan))
    except (TypeError, ValueError, UnicodeError) as exc:
        raise TransactionRecordError(event_path, "event record is not canonical") from exc
    if expected_event != raw_event:
        raise TransactionRecordError(event_path, "event bytes do not match transaction plan")

    allowed = {
        "event.json",
        "intent.json",
        "prepared.json",
        *(f"backups/{index:06d}.json" for index in range(len(targets))),
        *(f"progress/{index:06d}.json" for index in range(len(targets))),
        *(f"{status}.json" for status in policy.terminal_statuses),
    }
    if names:
        unknown = sorted(set(names) - allowed)
        if unknown:
            raise TransactionRecordError(
                f"{root}/{unknown[0]}", "transaction record path is not canonical"
            )

    intent_path = f"{root}/intent.json"
    raw_intent = _read_record(connector, intent_path)
    prepared_path = f"{root}/prepared.json"
    prepared_raw = _read_record(connector, prepared_path)
    backup_names = [
        name.removeprefix("backups/")
        for name in names
        if name.startswith("backups/")
    ]
    expected_backup_names = {
        f"{index:06d}.json" for index in range(len(targets))
    }
    unknown_backups = sorted(set(backup_names) - expected_backup_names)
    if unknown_backups:
        raise TransactionRecordError(
            f"{root}/backups/{unknown_backups[0]}",
            "backup index is invalid",
        )

    backup_hashes: list[str] = []
    backup_present: list[bool] = []
    first_missing: int | None = None
    for index, target in enumerate(targets):
        backup_path = f"{root}/backups/{index:06d}.json"
        expected_backup = canonical_json(
            {
                "version": VERSION,
                "path": target.path,
                "input_sha256": (
                    None if target.input_bytes is None else sha256(target.input_bytes)
                ),
                "input_base64": (
                    None
                    if target.input_bytes is None
                    else base64.b64encode(target.input_bytes).decode("ascii")
                ),
            }
        )
        raw_backup = _read_record(connector, backup_path)
        backup_present.append(raw_backup is not None)
        if raw_backup is None:
            if first_missing is None:
                first_missing = index
        elif first_missing is not None:
            raise TransactionRecordError(
                backup_path, "backup records are not a cumulative prefix"
            )
        elif raw_backup != expected_backup:
            raise TransactionRecordError(backup_path, "backup record is malformed")
        backup_hashes.append(sha256(expected_backup))

    intent_hash: str | None = None
    if raw_intent is None:
        later = [name for name in names if name != "event.json"]
        if later and set(later) != {"aborted.json"}:
            raise TransactionRecordError(
                f"{root}/{sorted(later)[0]}", "records exist without intent"
            )
        if prepared_raw is not None or any(backup_present):
            raise TransactionRecordError(
                root, "prepared or backup records require intent"
            )
        progress_present = [
            _read_record(connector, f"{root}/progress/{index:06d}.json") is not None
            for index in range(len(targets))
        ]
        if any(progress_present):
            raise TransactionRecordError(root, "progress records require intent")
    else:
        expected_intent = canonical_json(plan.intent)
        if raw_intent != expected_intent:
            raise TransactionRecordError(intent_path, "intent record is malformed")
        intent_hash = sha256(expected_intent)
        if prepared_raw is not None:
            expected_prepared = canonical_json(
                {
                    "version": VERSION,
                    "intent_sha256": intent_hash,
                    "backup_sha256s": backup_hashes,
                }
            )
            if first_missing is not None or prepared_raw != expected_prepared:
                raise TransactionRecordError(
                    prepared_path, "prepared record is malformed"
                )

        progress_names = [
            name.removeprefix("progress/")
            for name in names
            if name.startswith("progress/")
        ]
        expected_progress_names = {
            f"{index:06d}.json" for index in range(len(targets))
        }
        unknown_progress = sorted(set(progress_names) - expected_progress_names)
        if unknown_progress:
            raise TransactionRecordError(
                f"{root}/progress/{unknown_progress[0]}",
                "progress index is invalid",
            )
        progress_missing: int | None = None
        for index, target in enumerate(targets):
            progress_path = f"{root}/progress/{index:06d}.json"
            progress = _read_record(connector, progress_path)
            if progress is None:
                if progress_missing is None:
                    progress_missing = index
                continue
            if prepared_raw is None:
                raise TransactionRecordError(progress_path, "progress requires prepared")
            if progress_missing is not None:
                raise TransactionRecordError(
                    progress_path, "progress records are not a cumulative prefix"
                )
            expected_progress = canonical_json(
                {
                    "version": VERSION,
                    "index": index,
                    "path": target.path,
                    "output_sha256": sha256(target.output_bytes),
                }
            )
            if progress != expected_progress:
                raise TransactionRecordError(
                    progress_path, "progress record is malformed"
                )

    terminals: list[tuple[str, bytes]] = []
    for status_name in policy.terminal_statuses:
        raw_terminal = _read_record(connector, f"{root}/{status_name}.json")
        if raw_terminal is not None:
            terminals.append((status_name, raw_terminal))
    if len(terminals) > 1:
        raise TransactionRecordError(root, "transaction has multiple terminal records")

    status: str | None = None
    terminal: bytes | None = None
    if terminals:
        status, terminal = terminals[0]
        terminal_path = f"{root}/{status}.json"
        if raw_intent is None:
            if status != "aborted":
                raise TransactionRecordError(
                    terminal_path, "no-intent terminal is invalid"
                )
            if policy.terminal_validator is None:
                raise TransactionRecordError(
                    terminal_path, "no-intent terminal proof is unavailable"
                )
        else:
            assert intent_hash is not None
            if status == "no-op" and (targets or prepared_raw is not None):
                raise TransactionRecordError(
                    terminal_path,
                    "no-op terminal requires an empty target set and no prepared record",
                )
            if status == "aborted" and prepared_raw is not None:
                raise TransactionRecordError(
                    terminal_path,
                    "aborted terminal requires no prepared record",
                )
            if status in {"applied", "rolled-back", "manual-conflict"} and (
                prepared_raw is None
            ):
                raise TransactionRecordError(
                    terminal_path, "terminal requires prepared record"
                )
            if status == "applied":
                for index in range(len(targets)):
                    progress_path = f"{root}/progress/{index:06d}.json"
                    if _read_record(connector, progress_path) is None:
                        raise TransactionRecordError(
                            progress_path,
                            "applied terminal requires every progress record",
                        )
            expected_terminal = _terminal_record(status, intent_hash)
            if terminal != expected_terminal and policy.terminal_validator is None:
                raise TransactionRecordError(
                    terminal_path, "terminal record is malformed"
                )
        if policy.terminal_validator is not None:
            try:
                policy.terminal_validator(status, record, terminal, plan)
            except TransactionRecordError:
                raise
            except Exception as exc:
                raise TransactionRecordError(
                    terminal_path, "terminal owner proof is invalid"
                ) from exc

    if plan.attempt == 1:
        predecessor_id = f"{plan.base_transaction_id}-a000000"
        try:
            predecessor = load_transaction(connector, predecessor_id, policy)
        except TransactionRecordError as exc:
            raise TransactionRecordError(
                event_path, "successor predecessor is invalid"
            ) from exc
        if (
            predecessor.plan.attempt != 0
            or predecessor.plan.base_transaction_id != plan.base_transaction_id
            or predecessor.record != record
            or predecessor.plan.targets != plan.targets
            or predecessor.status not in {"aborted", "rolled-back"}
            or predecessor.terminal is None
            or sha256(predecessor.terminal) != plan.predecessor_sha256
        ):
            raise TransactionRecordError(
                event_path, "successor predecessor is invalid"
            )

    return Journal(
        record=record,
        plan=plan,
        status=status,
        terminal=terminal,
        prepared=(
            None
            if prepared_raw is None
            else _decode_record(prepared_raw, prepared_path)
        ),
        record_names=names,
    )
