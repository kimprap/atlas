"""The Jev adapter: the judge port on OpenRouter Decisions.

One ``POST https://openrouter.ai/api/alpha/decisions`` per ``judge`` call, model
``~typesafe/jev-latest``. The key is ``OPENROUTER_API_KEY`` from
``~/.config/atlas/openrouter.env``, read only when the file (after any link)
has mode 600, at most once per command. The file may hold other ``KEY=value``
lines; only the one key is taken and the rest is never kept. The key goes into
the request header only: never into argv, a log, a reply, a problem or an
exception text. 429 and 529 are retried after 1, 2, 4 and 8 s, then the call
fails with ``JudgeFailed``.
"""

from __future__ import annotations

import http.client
import json
import os
import stat
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from atlas import ports

ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
MODEL = "~typesafe/jev-latest"
KEY_NAME = "OPENROUTER_API_KEY"
RETRY_STATUSES = frozenset({429, 529})
BACKOFF_S = (1, 2, 4, 8)
TIMEOUT_S = 60


def key_file() -> Path:
    """The key file the user places, under the caller's ``HOME``."""
    return Path.home() / ".config" / "atlas" / "openrouter.env"


def _parse_key(text: str) -> str | None:
    """The value of the ``OPENROUTER_API_KEY=`` line; every other line is skipped unread."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        name, sep, value = line.partition("=")
        if not sep or name.strip() != KEY_NAME:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value or None
    return None


class JevJudge:
    """The judge port on OpenRouter Decisions with the user's own key."""

    def __init__(
        self,
        endpoint: str = ENDPOINT,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.endpoint = endpoint
        self._sleep = sleep
        self._loaded = False
        self._key: str | None = None
        self._problem: ports.SetupProblem | None = None

    def _load(self) -> None:
        """Check the key file and read the key from it, once."""
        if self._loaded:
            return
        self._loaded = True
        path = key_file()
        where = str(path)
        place = f"Put the line {KEY_NAME}=<your OpenRouter key> in {where}."
        chmod = f"Run: chmod 600 {where}"
        try:
            mode = stat.S_IMODE(os.stat(path).st_mode)
        except FileNotFoundError:
            self._problem = ports.SetupProblem("The Jev key file is missing", (place, chmod), where)
            return
        except OSError as err:
            self._problem = ports.SetupProblem(f"The Jev key file cannot be checked ({err.strerror})", (place, chmod), where)
            return
        if mode != 0o600:
            self._problem = ports.SetupProblem(f"The Jev key file has mode {mode:o}, not 600", (chmod,), where)
            return
        try:
            key = _parse_key(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as err:
            reason = err.strerror if isinstance(err, OSError) else "it is not UTF-8 text"
            self._problem = ports.SetupProblem(f"The Jev key file cannot be read ({reason})", (place,), where)
            return
        if key is None:
            self._problem = ports.SetupProblem(f"The Jev key file has no {KEY_NAME} line", (place,), where)
            return
        self._key = key

    def setup_problem(self) -> ports.SetupProblem | None:
        self._load()
        return self._problem

    def _scrub(self, text: str) -> str:
        return text.replace(self._key, "[key]") if self._key else text

    def _post(self, payload: bytes) -> tuple[int, Any]:
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
                status, raw = response.status, response.read()
        except urllib.error.HTTPError as err:
            status, raw = err.code, err.read()
        except (OSError, http.client.HTTPException) as err:
            reason = getattr(err, "reason", err)
            raise ports.JudgeFailed(None, self._scrub(f"Jev could not be reached: {reason}")) from None
        try:
            return status, json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return status, raw.decode("utf-8", "replace")

    def judge(self, state: str, questions: Sequence[ports.Question]) -> ports.Judgments:
        if not isinstance(state, str) or not questions:
            raise ValueError("a judge request holds one state and at least one question")
        if any(not isinstance(question, ports.Question) for question in questions):
            raise ValueError("judge questions are ports.Question values")
        if len({question.id for question in questions}) != len(questions):
            raise ValueError("judge question ids repeat")
        self._load()
        if self._problem is not None:
            raise ports.JudgeNotSetUp(self._problem.what)
        wire: dict[str, Any] = {}
        for question in questions:
            entry: dict[str, Any] = {"type": question.type, "instructions": question.text}
            if question.type == "choice":
                entry["criteria"] = {option: option for option in question.options}
            wire[question.id] = entry
        payload = json.dumps({"model": MODEL, "state": state, "questions": wire}).encode("utf-8")
        for delay in (*BACKOFF_S, None):
            status, body = self._post(payload)
            if status not in RETRY_STATUSES:
                break
            if delay is None:
                raise ports.JudgeFailed(status, self._scrub(f"Jev is busy: {_error_text(body)}"))
            self._sleep(delay)
        if status != 200:
            raise ports.JudgeFailed(status, self._scrub(_error_text(body)))
        return self._judgments(body, questions)

    def _judgments(self, body: Any, questions: Sequence[ports.Question]) -> ports.Judgments:
        if not isinstance(body, Mapping) or not isinstance(body.get("answers"), Mapping):
            raise ports.JudgeFailed(200, "the Jev reply has no answers")
        model = body.get("model")
        if not isinstance(model, str) or not model:
            raise ports.JudgeFailed(200, "the Jev reply names no model")
        answers: dict[str, ports.Answer] = {}
        for question in questions:
            got = body["answers"].get(question.id)
            if not isinstance(got, Mapping) or got.get("type") != question.type:
                raise ports.JudgeFailed(200, f"the Jev reply has no {question.type} answer for {question.id}")
            try:
                if question.type == "noul":
                    answers[question.id] = ports.Answer(p=float(got["noul"]))
                else:
                    probabilities = {str(k): float(v) for k, v in got["probabilities"].items()}
                    answers[question.id] = ports.Answer(
                        probabilities=probabilities, confidence=float(got["confidence"])
                    )
            except (KeyError, TypeError, ValueError, AttributeError):
                raise ports.JudgeFailed(200, f"the Jev answer for {question.id} is malformed") from None
        usage = body.get("usage")
        cost = usage.get("cost") if isinstance(usage, Mapping) else None
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            billed = ports.Cost(float(cost), "billed")
        else:
            billed = ports.Cost(None, "unknown")
        return ports.Judgments(model=model, answers=answers, cost=billed)


def _error_text(body: Any) -> str:
    if isinstance(body, Mapping) and isinstance(body.get("error"), Mapping):
        return str(body["error"].get("message", ""))[:300] or "no error message"
    return str(body)[:300] or "no error message"
