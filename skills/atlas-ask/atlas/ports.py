"""The host seams core calls: read, call, judge and quota ports and the host facts capability.

Value types are frozen dataclasses; ports are Protocols. Adapters implement them
and ``atlas.host`` picks which; core sees only these shapes. A port or
capability the host lacks is ``None`` on the ``Host`` value, and core takes the
fixed fallback the architecture names for it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from atlas.store import Store

# The annotated-tag trailer holding the host version a release was tagged with.
# It lives here, not in core, because its name spells the host's name.
HOST_VERSION_TRAILER = "Omp-Version"

KIND_HINTS = frozenset(
    {"article", "repo", "docs", "x_post", "paper", "video", "image", "link_list", "unknown"}
)
UNREADABLE_REASONS = frozenset({"paywall", "login", "error", "gone", "no_transcript", "no_reader"})
STOPS = frozenset({"end", "tool", "cut_off", "refused"})
COST_KINDS = frozenset({"billed", "estimated", "unknown"})
QUESTION_TYPES = frozenset({"noul", "choice"})

# ``read`` scope: None, "transcript", "images" or {"sections": [...]}.
Scope = None | str | Mapping[str, Sequence[str]]


@dataclass(frozen=True)
class RepoItem:
    """One repo sub-item (a skill, plugin or package) from the full file list."""

    path: str
    link: str
    kind: str


@dataclass(frozen=True)
class Counts:
    words: int
    links: int
    images: int


@dataclass(frozen=True)
class Page:
    """One page as read: header lines and counters already removed from ``text``.

    ``images`` are the page's image links in page order (an image page lists
    itself); ``ReadPort.image`` gives each one's bytes.
    """

    final_link: str
    title: str | None
    author: str | None
    publisher: str | None
    published: str | None
    kind_hint: str
    text: str
    images: tuple[str, ...] = ()
    links: tuple[str, ...] = ()
    counts: Counts = Counts(0, 0, 0)
    items: tuple[RepoItem, ...] = ()

    def __post_init__(self) -> None:
        if self.kind_hint not in KIND_HINTS:
            raise ValueError(f"kind_hint {self.kind_hint!r} is not one of {sorted(KIND_HINTS)}")


@dataclass(frozen=True)
class Unreadable:
    reason: str
    detail: str

    def __post_init__(self) -> None:
        if self.reason not in UNREADABLE_REASONS:
            raise ValueError(f"reason {self.reason!r} is not one of {sorted(UNREADABLE_REASONS)}")


@dataclass(frozen=True)
class Usage:
    input: int
    output: int
    cache_read: int
    cache_write: int


@dataclass(frozen=True)
class Cost:
    usd: float | None
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in COST_KINDS:
            raise ValueError(f"cost kind {self.kind!r} is not one of {sorted(COST_KINDS)}")


@dataclass(frozen=True)
class Reply:
    """One model reply; ``tool_input`` holds the forced tool's arguments when ``stop`` is ``tool``.

    ``tool_input`` is ``None`` when the reply holds no usable tool call; ``tool_raw`` is then
    the host's raw tool text when it gave one (tool arguments that do not parse), else ``None``.
    """

    model: str
    thinking: str | None
    content: str
    tool_input: Mapping[str, Any] | None
    stop: str
    usage: Usage
    cost: Cost
    tool_raw: str | None = None

    def __post_init__(self) -> None:
        if self.stop not in STOPS:
            raise ValueError(f"stop {self.stop!r} is not one of {sorted(STOPS)}")


@dataclass(frozen=True)
class Question:
    """One judge question; a ``choice`` question has ``options``, a ``noul`` one none."""

    id: str
    type: str
    text: str
    options: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.type not in QUESTION_TYPES:
            raise ValueError(f"question type {self.type!r} is not one of {sorted(QUESTION_TYPES)}")
        if (self.type == "choice") != bool(self.options):
            raise ValueError("a choice question has options and a noul question has none")


@dataclass(frozen=True)
class Answer:
    """A ``noul`` answer sets ``p``; a ``choice`` answer sets ``probabilities`` and ``confidence``."""

    p: float | None = None
    probabilities: Mapping[str, float] | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class Judgments:
    model: str
    answers: Mapping[str, Answer]
    cost: Cost


@dataclass(frozen=True)
class Window:
    provider: str
    window_id: str
    duration_s: int
    used_fraction: float
    resets_at: str


@dataclass(frozen=True)
class SetupProblem:
    """What a port lacks to work, the lines that fix it and the file they concern."""

    what: str
    fix: tuple[str, ...]
    where: str | None


@dataclass(frozen=True)
class RoleFix:
    """The host's own lines that add missing roles, and the file they go into."""

    lines: tuple[str, ...]
    where: str | None


class RoleMissing(Exception):
    def __init__(self, role: str) -> None:
        super().__init__(f"role {role} is not set on this host")
        self.role = role


class CallFailed(Exception):
    def __init__(self, status: int | None, detail: str) -> None:
        super().__init__(f"call failed ({status}): {detail}")
        self.status = status
        self.detail = detail


class JudgeNotSetUp(Exception):
    """The judge cannot run; ``JudgePort.setup_problem()`` says why."""


class JudgeFailed(Exception):
    def __init__(self, status: int | None, detail: str) -> None:
        super().__init__(f"judge failed ({status}): {detail}")
        self.status = status
        self.detail = detail


class ReadPort(Protocol):
    def read(self, link: str, scope: Scope = None) -> Page | Unreadable: ...

    def image(self, link: str) -> bytes | Unreadable:
        """The bytes of the image at ``link`` (PNG, JPEG, GIF or WebP), or why they cannot be had."""
        ...


class CallPort(Protocol):
    def call(
        self,
        role: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
        tool_choice: str | None,
        max_output: int,
        images: Sequence[bytes] = (),
    ) -> Reply: ...


class JudgePort(Protocol):
    def judge(self, state: str, questions: Sequence[Question]) -> Judgments: ...

    def setup_problem(self) -> SetupProblem | None: ...


class QuotaPort(Protocol):
    def windows(self, providers: Sequence[str]) -> list[Window]: ...


class HostFacts(Protocol):
    name: str

    def version(self) -> str | None: ...

    def roles(self) -> dict[str, str]: ...

    def role_fix(self, missing: Mapping[str, str]) -> RoleFix: ...

    def role_provider(self, role: str) -> str | None: ...

    def role_context(self, role: str) -> int | None: ...


@dataclass(frozen=True)
class Host:
    """Everything core may reach outside itself for one command."""

    read: ReadPort
    call: CallPort
    open_store: Callable[[Path], Store]
    judge: JudgePort | None = None
    quota: QuotaPort | None = None
    facts: HostFacts | None = None
