"""Puts the repo root and the Atlas package on ``sys.path``: import this module first.

The root makes ``tools.quality`` importable when a tool runs as a script. The Atlas
package goes last, so a caller that put another checkout's ``skills/atlas-ask`` first
(the version worker, which runs a git worktree's Atlas) keeps it.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ATLAS = str(ROOT / "skills" / "atlas-ask")
if ATLAS not in sys.path:
    sys.path.append(ATLAS)
