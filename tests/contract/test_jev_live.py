"""The Jev adapter against OpenRouter Decisions, run only with ``ATLAS_LIVE=1``.

The ``ok`` judge uses the user's own key file ``~/.config/atlas/openrouter.env``
and sends one request (its answer is reused); the missing and loose key-file
cases point ``HOME`` at a temporary folder and send nothing.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from functools import cache
from pathlib import Path
from unittest import mock

from tests.contract import suite

from atlas import ports  # noqa: E402
from atlas.adapters.jev import JevJudge  # noqa: E402

LIVE = os.environ.get("ATLAS_LIVE") == "1"


@cache
def _judged() -> ports.Judgments:
    return JevJudge().judge(suite.JUDGE_STATE, [suite.CAUSE, suite.KIND])


@unittest.skipUnless(LIVE, "live: set ATLAS_LIVE=1 to call OpenRouter Decisions")
class LiveJudge(suite.JudgeContract, unittest.TestCase):
    JUDGE_MODEL = r"^typesafe/jev-"

    def judged(self) -> ports.Judgments:
        return _judged()

    def make_judge(self, key: str) -> ports.JudgePort:
        if key == "ok":
            return JevJudge()
        home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(home)}))
        if key == "loose":
            path = home / ".config" / "atlas" / "openrouter.env"
            path.parent.mkdir(parents=True)
            path.write_text("OPENROUTER_API_KEY=sk-or-v1-not-a-key\n", encoding="utf-8")
            os.chmod(path, 0o644)
        return JevJudge()


if __name__ == "__main__":
    unittest.main()
