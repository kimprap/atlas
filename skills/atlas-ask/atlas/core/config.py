"""Settings and profiles from ``~/.config/atlas/config.toml``.

``atlas-init`` is the only writer of the file; Atlas only reads it. The keys read
so far are ``default_profile`` and, per profile, ``store`` and ``judge``; other
keys are left for the stages that read them. The profile is the body's
``profile``, else ``ATLAS_PROFILE``, else ``default_profile``.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SETUP_SKILL = "atlas-init"
JUDGES = ("jev", "opus")


@dataclass(frozen=True)
class Profile:
    name: str
    store: Path
    judge: str | None  # None when no judge choice is saved


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
    return Profile(name=name, store=Path(store).expanduser(), judge=judge)
