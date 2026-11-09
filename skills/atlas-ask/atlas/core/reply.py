"""Strict JSON body input and the one-line CLI reply.

A body is one JSON object in UTF-8. Duplicate keys, NaN and Infinity, numbers
too large to hold, invalid UTF-8, unpaired surrogate escapes and any non-object
value are bad input.

A reply has exactly the keys ``ok``, ``op``, ``result``, ``problems``, ``next``
and ``decisions``, and goes to stdout as one ``json.dumps`` line. ``ok`` is true
only for exit 0.
"""

from __future__ import annotations

import json
import math
import sys
from collections.abc import Mapping, Sequence
from typing import Any, NoReturn, TextIO

DONE = 0
FAILED = 1
BAD_INPUT = 2
NOT_SET_UP = 3
NEEDS_DECISION = 4

EXIT_CODES = frozenset({DONE, FAILED, BAD_INPUT, NOT_SET_UP, NEEDS_DECISION})
MAX_NEXT = 3


class BadInput(ValueError):
    """The body breaks the strict input rules; ``problem`` says how in plain text."""

    def __init__(self, problem: str) -> None:
        super().__init__(problem)
        self.problem = problem


def _reject_constant(value: str) -> NoReturn:
    raise BadInput(f"{value} is not a number JSON allows")


def _int(text: str) -> int:
    try:
        return int(text)
    except ValueError:
        raise BadInput(f"body holds an integer of {len(text)} digits; too many") from None


def _float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise BadInput(f"body holds a number too large to hold: {text[:20]}")
    return value


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BadInput(f"duplicate key {json.dumps(key, ensure_ascii=False)}")
        result[key] = value
    return result


def _check_text(value: Any, path: str) -> None:
    if isinstance(value, str):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise BadInput(f"{path} holds an unpaired surrogate escape") from None
    elif isinstance(value, dict):
        for key, item in value.items():
            _check_text(key, f"a key in {path}")
            _check_text(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_text(item, f"{path}[{index}]")


def decode_body(raw: bytes) -> dict[str, Any]:
    """Return the body object, or raise ``BadInput`` naming the first problem."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise BadInput("body is not valid UTF-8") from None
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object,
            parse_constant=_reject_constant,
            parse_int=_int,
            parse_float=_float,
        )
        if not isinstance(value, dict):
            raise BadInput("body must be one JSON object")
        _check_text(value, "body")
    except json.JSONDecodeError as exc:
        raise BadInput(
            f"body is not valid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from None
    except RecursionError:
        raise BadInput("body is nested too deeply") from None
    return value


def problem(field: str, text: str, link: str | None = None) -> dict[str, Any]:
    """One ``problems[]`` item."""
    return {"link": link, "field": field, "problem": text}


def next_step(label: str, then: Mapping[str, Any]) -> dict[str, Any]:
    """One ``next[]`` item: a plain-text label and the typed action it runs."""
    return {"label": label, "then": dict(then)}


def build(
    op: str,
    code: int,
    result: Mapping[str, Any] | None = None,
    problems: Sequence[Mapping[str, Any]] = (),
    next: Sequence[Mapping[str, Any]] = (),
    decisions: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Return the six-key reply for ``op`` ending with exit ``code``."""
    if code not in EXIT_CODES:
        raise ValueError(f"exit code {code} is not one of 0-4")
    if len(next) > MAX_NEXT:
        raise ValueError(f"next has {len(next)} items; at most {MAX_NEXT}")
    if code == NEEDS_DECISION and not decisions:
        raise ValueError("exit 4 needs at least one decision")
    for item in problems:
        if set(item) != {"link", "field", "problem"}:
            raise ValueError("a problems item has exactly link, field and problem")
    for item in next:
        if set(item) != {"label", "then"}:
            raise ValueError("a next item has exactly label and then")
    return {
        "ok": code == DONE,
        "op": op,
        "result": dict(result or {}),
        "problems": [dict(item) for item in problems],
        "next": [dict(item) for item in next],
        "decisions": [dict(item) for item in decisions],
    }


def write(reply: Mapping[str, Any], code: int, stream: TextIO | None = None) -> int:
    """Write ``reply`` as one JSON line and return ``code`` for the process exit."""
    out = sys.stdout if stream is None else stream
    out.write(json.dumps(reply, allow_nan=False) + "\n")
    out.flush()
    return code
