"""Strict JSON body input and the one-line CLI reply.

A body is one JSON object in UTF-8. Duplicate keys, NaN and Infinity, numbers
too large to hold, invalid UTF-8, unpaired surrogate escapes and any non-object
value are bad input.

A reply has exactly the keys ``ok``, ``op``, ``result``, ``problems``, ``next``
and ``decisions``, and goes to stdout as one ``json.dumps`` line. ``ok`` is true
only for exit 0; ``decisions`` is non-empty exactly on exit 4.

A decision stops one change for the user. Its id binds it to that change: the
first 16 hex of SHA-256 over the command, the mode flag, the canonical body
without ``approval``, and the kind. A resend whose ``approval.decision`` is not
that id is bad input: the approval is for a different change.
"""

from __future__ import annotations

import hashlib
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

DECISION_KINDS = frozenset(
    {
        "confirm",
        "cap",
        "window",
        "pick_scope",
        "summary_failed",
        "judge_setup",
        "version_save",
        "already_current",
    }
)
OTHER_CHANGE = "this approval is for a different change"


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


def _check_then(then: Mapping[str, Any]) -> None:
    """A ``then`` is exactly one of ``resend`` (an object), ``skill`` (a name) or ``stop`` (true)."""
    if len(then) != 1:
        raise ValueError("a then has exactly one of resend, skill or stop")
    [(action, value)] = then.items()
    if action == "resend" and isinstance(value, Mapping):
        return
    if action == "skill" and isinstance(value, str) and value:
        return
    if action == "stop" and value is True:
        return
    raise ValueError(f"then {{{action!r}: {value!r}}} is not a resend object, skill name or stop true")


def next_step(label: str, then: Mapping[str, Any]) -> dict[str, Any]:
    """One ``next[]`` item: a plain-text label and the typed action it runs."""
    _check_then(then)
    return {"label": label, "then": dict(then)}


def decision_id(command: str, mode: str | None, body: Mapping[str, Any], kind: str) -> str:
    """The id that binds a decision to the change it stops."""
    change = {key: value for key, value in body.items() if key != "approval"}
    canonical = json.dumps(
        [command, mode, change, kind], sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def option(id: str, label: str, then: Mapping[str, Any]) -> dict[str, Any]:
    """One option of a decision: its id, a plain-text label and the typed action it runs."""
    _check_then(then)
    return {"id": id, "label": label, "then": dict(then)}


def decision(
    command: str,
    mode: str | None,
    body: Mapping[str, Any],
    kind: str,
    question: str,
    options: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """One ``decisions[]`` item for the change ``command``/``mode``/``body`` would make."""
    if kind not in DECISION_KINDS:
        raise ValueError(f"decision kind {kind!r} is not one of {sorted(DECISION_KINDS)}")
    if not options:
        raise ValueError("a decision has at least one option")
    return {
        "id": decision_id(command, mode, body, kind),
        "kind": kind,
        "question": question,
        "options": [dict(item) for item in options],
    }


def approval_problem(
    command: str, mode: str | None, body: Mapping[str, Any], kind: str
) -> dict[str, Any] | None:
    """The bad-input problem for an ``approval.decision`` that names another change, else ``None``."""
    approval = body.get("approval")
    if not isinstance(approval, Mapping) or "decision" not in approval:
        return None
    if approval["decision"] == decision_id(command, mode, body, kind):
        return None
    return problem("approval", OTHER_CHANGE)


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
    if (code == NEEDS_DECISION) != bool(decisions):
        raise ValueError("decisions are given exactly on exit 4")
    for item in problems:
        if set(item) != {"link", "field", "problem"}:
            raise ValueError("a problems item has exactly link, field and problem")
    for item in next:
        if set(item) != {"label", "then"}:
            raise ValueError("a next item has exactly label and then")
        _check_then(item["then"])
    for item in decisions:
        if set(item) != {"id", "kind", "question", "options"} or item["kind"] not in DECISION_KINDS:
            raise ValueError("a decisions item has exactly id, kind, question and options, with a known kind")
        for choice in item["options"]:
            if set(choice) != {"id", "label", "then"}:
                raise ValueError("a decision option has exactly id, label and then")
            _check_then(choice["then"])
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
