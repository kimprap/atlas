"""The quality tool's replay read adapter passes the read-port contract, offline.

``tests/fixtures/quality/records.json`` holds page records built from the
recorded ``omp read`` output, the recorded GitHub tree and the recorded pixel
(its ``source`` field says how); the adapter answers from them and reads
nothing else.
"""

from __future__ import annotations

import socket
import unittest
from unittest import mock

from tests.contract import suite
from tests.contract.replay import FIXTURES

from atlas import ports  # noqa: E402
from tools.quality import replay_read  # noqa: E402

RECORDS = FIXTURES / "quality" / "records.json"


class ReplayRead(suite.ReadContract, unittest.TestCase):
    REDIRECT_LINK = "https://python.org/"
    REDIRECTED_TO = "https://www.python.org/"
    REPO_LINK = "https://github.com/anthropics/skills"
    GONE_LINK = "https://example.com/atlas-no-such-page-404"
    GONE_REASON = "gone"
    PAGE_LINKS = ("https://python.org/", "https://github.com/anthropics/skills", "https://x.com/jack/status/20")
    IMAGE_LINK = "https://images.example/pixel.png"
    VIDEO_LINK = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    TRANSCRIPT_PHRASE = "really really long trunks"
    NO_TRANSCRIPT_LINK = "https://python.org/"

    def make_read(self) -> ports.ReadPort:
        return replay_read.ReplayRead(replay_read.load_records(RECORDS))

    def test_it_never_opens_a_socket(self) -> None:
        # The contract cases above read through the adapter; here every socket is refused.
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("the replay adapter opened a socket")):
            read = self.make_read()
            for link in (*self.PAGE_LINKS, self.GONE_LINK):
                read.read(link)
            read.image(self.IMAGE_LINK)
            self.assertIsInstance(read.read(self.VIDEO_LINK, "transcript"), ports.Page)


if __name__ == "__main__":
    unittest.main()
