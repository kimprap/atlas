from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any, NoReturn

VERSION = 2
DISPOSITIONS = frozenset(
    {
        "completed",
        "no-write",
        "rejected",
        "unavailable",
        "recovery-required",
        "manual-intervention",
        "internal-error",
    }
)
_SUCCESS = frozenset({"completed", "no-write"})
_EXIT_CODES = {
    "completed": 0,
    "no-write": 0,
    "rejected": 2,
    "unavailable": 3,
    "recovery-required": 4,
    "manual-intervention": 4,
    "internal-error": 70,
}


class JsonInputError(ValueError):
    """Machine JSON input violates the strict shared CLI contract."""


class _DuplicateKeyError(JsonInputError):
    pass


def _reject_constant(value: str) -> NoReturn:
    raise JsonInputError(f"nonfinite number {value!r} is not allowed")


def _pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise _DuplicateKeyError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _assert_scalars(value: Any, path: str = "input") -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise JsonInputError(f"{path} contains an invalid Unicode scalar") from exc
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _assert_scalars(key, f"{path}.key")
            _assert_scalars(item, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(
        value, (bytes, bytearray, memoryview)
    ):
        for index, item in enumerate(value):
            _assert_scalars(item, f"{path}[{index}]")


def decode(raw: bytes) -> Any:
    """Decode one complete duplicate-safe, finite, UTF-8 JSON value."""
    if not isinstance(raw, bytes):
        raise JsonInputError("input must be bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise JsonInputError("input is not valid UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except _DuplicateKeyError:
        raise
    except JsonInputError:
        raise
    except json.JSONDecodeError as exc:
        raise JsonInputError("input is not one complete JSON value") from exc
    _assert_scalars(value)
    return value


def encode(value: Any) -> bytes:
    """Encode canonical UTF-8 JSON with exactly one trailing LF."""
    _assert_scalars(value, "response")
    try:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise JsonInputError("response is not canonical JSON data") from exc
    return payload + b"\n"


def normalize_findings(values: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    normalized: set[tuple[str, str, str]] = set()
    for value in values:
        if not isinstance(value, Mapping) or set(value) != {"code", "path", "detail"}:
            raise ValueError("finding fields are invalid")
        code, path, detail = value["code"], value["path"], value["detail"]
        if not all(isinstance(item, str) for item in (code, path, detail)):
            raise ValueError("finding values must be text")
        _assert_scalars(code, "finding.code")
        _assert_scalars(path, "finding.path")
        _assert_scalars(detail, "finding.detail")
        normalized.add((code, path, detail))
    return [
        {"code": code, "path": path, "detail": detail}
        for code, path, detail in sorted(normalized)
    ]


def response(
    op: str | None,
    disposition: str,
    *,
    result: Mapping[str, Any] | None = None,
    findings: Sequence[Mapping[str, Any]] = (),
    recovery: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct the exact version-2 machine response envelope."""
    if op is not None and not isinstance(op, str):
        raise ValueError("response operation must be text or null")
    if disposition not in DISPOSITIONS:
        raise ValueError("response disposition is invalid")
    found = normalize_findings(findings)
    ok = disposition in _SUCCESS
    if ok and found:
        raise ValueError("successful response cannot contain findings")
    if not ok and not found:
        raise ValueError("failed response requires a finding")
    if result is not None and not isinstance(result, Mapping):
        raise ValueError("response result must be an object or null")
    if recovery is not None:
        if not isinstance(recovery, Mapping) or set(recovery) != {"operation", "args"}:
            raise ValueError("response recovery fields are invalid")
        if not isinstance(recovery.get("operation"), str) or not isinstance(
            recovery.get("args"), Mapping
        ):
            raise ValueError("response recovery binding is invalid")
    if disposition in {"recovery-required", "manual-intervention"}:
        if disposition == "recovery-required" and recovery is None:
            raise ValueError("recovery-required response needs exact recovery")
    elif recovery is not None:
        raise ValueError("recovery is allowed only for recovery dispositions")
    return {
        "version": VERSION,
        "ok": ok,
        "op": op,
        "disposition": disposition,
        "result": None if result is None else dict(result),
        "findings": found,
        "recovery": None if recovery is None else dict(recovery),
    }


def exit_code(value: Mapping[str, Any]) -> int:
    disposition = value.get("disposition")
    if disposition not in _EXIT_CODES:
        return 70
    return _EXIT_CODES[disposition]


def emit(value: Mapping[str, Any]) -> int:
    sys.stdout.buffer.write(encode(value))
    return exit_code(value)
