"""Settings and profiles from ``~/.config/atlas/config.toml``.

``atlas-init`` is the only writer of the file; Atlas only reads it. The keys read
so far are ``default_profile``; per profile ``store`` and ``judge`` (stage 2), the
limits ``max_page_tokens``, ``judge_concurrency``, ``rethink``, ``near_copy``,
``reread_days``, ``reread_new_text``, ``cap_usd``, ``cap_warn``, ``window_stop``
and the ``confirm`` table (stage 3); and the top-level ``prices`` table (stage 3).
A missing key takes its default; ``cap_usd`` has none, so no cap is set. Other
keys are left for the stages that read them. The profile is the body's
``profile``, else ``ATLAS_PROFILE``, else ``default_profile``.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

SETUP_SKILL = "atlas-init"
JUDGES = ("jev", "opus")

# The changes that have a confirm setting, and the two settings each may take.
CHANGE_KINDS = (
    "add",
    "add_redo",
    "add_reread",
    "inbox_add",
    "note",
    "archive",
    "restore",
    "follow",
    "unfollow",
    "plan_start",
)
ALWAYS = "always"
NEVER = "never"

# The four token prices of a price row, in USD per million tokens.
PRICE_KEYS = ("input", "output", "cache_read", "cache_write")


@dataclass(frozen=True)
class Price:
    """One model's list price in USD per million tokens."""

    input: float
    output: float
    cache_read: float
    cache_write: float


@dataclass(frozen=True)
class Profile:
    name: str
    store: Path
    judge: str | None  # None when no judge choice is saved
    max_page_tokens: int
    judge_concurrency: int
    rethink: bool
    near_copy: float
    reread_days: int
    reread_new_text: float
    cap_usd: float | None  # None when no monthly cap is set
    cap_warn: float
    window_stop: float
    confirm: Mapping[str, str]  # every change kind with its setting; one the file leaves out is "always"
    prices: Mapping[str, Price]  # the top-level price table by model, shared by every profile

    def limits(self) -> dict[str, Any]:
        """The limit settings by key, as ``status --detail`` shows them."""
        return {
            "max_page_tokens": self.max_page_tokens,
            "judge_concurrency": self.judge_concurrency,
            "rethink": self.rethink,
            "near_copy": self.near_copy,
            "reread_days": self.reread_days,
            "reread_new_text": self.reread_new_text,
            "cap_usd": self.cap_usd,
            "cap_warn": self.cap_warn,
            "window_stop": self.window_stop,
        }


class NotSetUp(Exception):
    """Atlas cannot run a command: ``what`` says why; ``atlas-init`` is the fix."""

    def __init__(self, what: str) -> None:
        super().__init__(what)
        self.what = what

    def item(self) -> dict[str, Any]:
        """The ``needs_action`` item for this problem."""
        return {
            "what": f"Atlas is not set up: {self.what}",
            "fix": [f"Run `{SETUP_SKILL}` to set up Atlas."],
            "where": str(config_path()),
        }


def config_path() -> Path:
    """The settings file ``atlas-init`` writes, under the caller's ``HOME``."""
    return Path.home() / ".config" / "atlas" / "config.toml"


def _read() -> dict[str, Any]:
    path = config_path()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise NotSetUp("there is no settings file") from None
    except (OSError, UnicodeDecodeError) as err:
        raise NotSetUp(f"the settings file cannot be read ({err})") from None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as err:
        raise NotSetUp(f"the settings file is not valid TOML ({err})") from None


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _setting(entry: Mapping[str, Any], name: str, key: str, default: Any, valid: Any, rule: str) -> Any:
    """``entry[key]`` when ``valid`` holds for it, ``default`` when absent, else ``NotSetUp`` naming ``rule``."""
    if key not in entry:
        return default
    value = entry[key]
    if not valid(value):
        raise NotSetUp(f'{key} of profile "{name}" is {value!r}; it must be {rule}')
    return value


def _confirm(entry: Mapping[str, Any], name: str) -> Mapping[str, str]:
    table = entry.get("confirm", {})
    if not isinstance(table, dict):
        raise NotSetUp(f'confirm of profile "{name}" is not a table')
    settings = dict.fromkeys(CHANGE_KINDS, ALWAYS)
    for kind, value in table.items():
        if kind not in settings:
            raise NotSetUp(f'confirm.{kind} of profile "{name}" names no change; the changes are {", ".join(CHANGE_KINDS)}')
        if value not in (ALWAYS, NEVER):
            raise NotSetUp(f'confirm.{kind} of profile "{name}" is {value!r}; it must be "{ALWAYS}" or "{NEVER}"')
        settings[kind] = value
    return MappingProxyType(settings)


def _prices(settings: Mapping[str, Any]) -> Mapping[str, Price]:
    table = settings.get("prices", {})
    if not isinstance(table, dict):
        raise NotSetUp("prices in the settings file is not a table")
    rows: dict[str, Price] = {}
    for model, row in table.items():
        if not isinstance(row, dict) or set(row) != set(PRICE_KEYS):
            raise NotSetUp(f'the price row of "{model}" must hold exactly {", ".join(PRICE_KEYS)}')
        if not all(_number(row[key]) and row[key] >= 0 for key in PRICE_KEYS):
            raise NotSetUp(f'the price row of "{model}" must hold numbers of 0 or more')
        rows[model] = Price(*(float(row[key]) for key in PRICE_KEYS))
    return MappingProxyType(rows)


def resolve(chosen: str | None, from_env: str | None) -> Profile:
    """The profile named by ``chosen`` (the body), else ``from_env``, else ``default_profile``."""
    settings = _read()
    name = chosen or from_env or settings.get("default_profile")
    if name is None:
        raise NotSetUp("no profile is chosen and the settings file has no default_profile")
    if not isinstance(name, str) or not name:
        raise NotSetUp("default_profile in the settings file is not a profile name")
    profiles = settings.get("profiles", {})
    if not isinstance(profiles, dict) or not isinstance(profiles.get(name, {}), dict):
        raise NotSetUp("profiles in the settings file are not tables")
    if name not in profiles:
        raise NotSetUp(f'profile "{name}" is not in the settings file')
    entry = profiles[name]
    store = entry.get("store")
    if store is None:
        raise NotSetUp(f'profile "{name}" has no store path')
    if not isinstance(store, str) or not Path(store).expanduser().is_absolute():
        raise NotSetUp(f'the store path of profile "{name}" is not an absolute path or one starting with ~')
    judge = entry.get("judge")
    if judge is not None and judge not in JUDGES:
        raise NotSetUp(f'the judge of profile "{name}" is {judge!r}; it must be "jev" or "opus"')

    def count(key: str, default: int) -> int:
        valid = lambda v: isinstance(v, int) and not isinstance(v, bool) and v > 0  # noqa: E731
        return _setting(entry, name, key, default, valid, "a whole number above 0")

    def share(key: str, default: float) -> float:
        valid = lambda v: _number(v) and 0 < v <= 1  # noqa: E731
        return float(_setting(entry, name, key, default, valid, "a share above 0 and at most 1"))

    cap = _setting(entry, name, "cap_usd", None, lambda v: _number(v) and v > 0, "a number of dollars above 0")
    return Profile(
        name=name,
        store=Path(store).expanduser(),
        judge=judge,
        max_page_tokens=count("max_page_tokens", 150_000),
        judge_concurrency=count("judge_concurrency", 8),
        rethink=_setting(entry, name, "rethink", True, lambda v: isinstance(v, bool), "true or false"),
        near_copy=share("near_copy", 0.90),
        reread_days=count("reread_days", 30),
        reread_new_text=share("reread_new_text", 0.05),
        cap_usd=None if cap is None else float(cap),
        cap_warn=share("cap_warn", 0.80),
        window_stop=share("window_stop", 0.90),
        confirm=_confirm(entry, name),
        prices=_prices(settings),
    )
