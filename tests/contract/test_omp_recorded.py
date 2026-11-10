"""The OMP adapter against recorded ``omp`` output, offline.

``tests/fixtures/omp/omp`` stands in for ``omp`` and answers from the output
captured on 2026-11-09 with omp 18.18.2 (``tests/fixtures/omp/*/index.json``
names each file's source; the cut-off and refused replies are derived from the
captured one). GitHub's tree API and an image link are served from
``tests/fixtures/github`` and ``tests/fixtures/images`` on a loopback server.
No network, no real ``omp`` process and no key are used.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.contract import suite
from tests.contract.replay import FIXTURES, Replay

from atlas import ports  # noqa: E402
from atlas.adapters.omp import OmpHost  # noqa: E402

OMP = FIXTURES / "omp" / "omp"
TREE = (FIXTURES / "github" / "anthropics_skills_tree.json").read_bytes()
PIXEL = (FIXTURES / "images" / "pixel.png").read_bytes()
PAGES = json.loads((FIXTURES / "omp" / "read" / "index.json").read_text(encoding="utf-8"))
REDIRECT = "https://python.org/"
REPO = "https://github.com/anthropics/skills"
GONE = "https://example.com/atlas-no-such-page-404"
X_POST = "https://x.com/jack/status/20"
# The same repo read when GitHub's API refused omp, so omp reports Method native.
REPO_NATIVE = "https://github.com/anthropics/skills/"
VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


def _tree(method: str, path: str, body: bytes) -> tuple[int, bytes]:
    if path == "/repos/anthropics/skills/git/trees/HEAD?recursive=1":
        return 200, TREE
    if path == "/images/pixel.png":
        return 200, PIXEL
    if path == "/images/not-an-image.png":
        return 200, b'{"message": "this is not an image"}'
    return 404, b'{"message": "Not Found"}'


class Recorded:
    """Each test runs with the recorded ``omp`` first on ``PATH`` and a loopback GitHub."""

    def setUp(self) -> None:
        super().setUp()
        self.github = self.enterContext(Replay(_tree))
        self.log = Path(self.enterContext(tempfile.TemporaryDirectory())) / "omp.log"
        path = f"{OMP.parent}{os.pathsep}{os.environ.get('PATH', '')}"
        self.enterContext(mock.patch.dict(os.environ, {"ATLAS_FAKE_OMP_LOG": str(self.log), "PATH": path}))
        self.omp = OmpHost(github_api=self.github.url)

    def runs(self) -> list[dict]:
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]


class RecordedRead(Recorded, suite.ReadContract, unittest.TestCase):
    REDIRECT_LINK = REDIRECT
    REDIRECTED_TO = "https://www.python.org/"
    REPO_LINK = REPO
    GONE_LINK = GONE
    GONE_REASON = "gone"
    PAGE_LINKS = (REDIRECT, REPO, X_POST)
    VIDEO_LINK = VIDEO
    TRANSCRIPT_PHRASE = "really really long trunks"
    NO_TRANSCRIPT_LINK = REDIRECT

    def setUp(self) -> None:
        super().setUp()
        self.IMAGE_LINK = f"{self.github.url}/images/pixel.png"

    def make_read(self) -> ports.ReadPort:
        return self.omp

    def test_an_image_link_gives_the_served_bytes_and_a_non_image_is_unreadable(self) -> None:
        self.assertEqual(self.omp.image(self.IMAGE_LINK), PIXEL)
        for name, reason in (("not-an-image.png", "error"), ("missing.png", "gone")):
            with self.subTest(name=name):
                got = self.omp.image(f"{self.github.url}/images/{name}")
                self.assertIsInstance(got, ports.Unreadable)
                self.assertEqual(got.reason, reason)

    def test_the_recorded_pages_carry_header_and_counter_lines(self) -> None:
        # The absence checks above can see these lines: the raw output has them.
        for link in self.PAGE_LINKS:
            raw = (FIXTURES / "omp" / "read" / PAGES[link]["file"]).read_text(encoding="utf-8")
            self.assertRegex(raw, suite.HEADER_LINE)
        for link in (REPO, X_POST):
            raw = (FIXTURES / "omp" / "read" / PAGES[link]["file"]).read_text(encoding="utf-8")
            self.assertRegex(raw, suite.COUNTER_LINE)

    def test_repo_items_come_from_the_tree_listing(self) -> None:
        page = self.omp.read(REPO)
        self.assertEqual(
            [(item.path, item.kind, item.link) for item in page.items],
            [
                ("skills/docx", "skill", f"{REPO}/tree/HEAD/skills/docx"),
                ("skills/pdf", "skill", f"{REPO}/tree/HEAD/skills/pdf"),
                ("template", "skill", f"{REPO}/tree/HEAD/template"),
            ],
        )
        self.assertEqual((page.title, page.author, page.publisher), ("anthropics/skills", "anthropics", "GitHub"))

    def test_a_repo_read_as_native_is_still_a_repo_with_its_items(self) -> None:
        raw = (FIXTURES / "omp" / "read" / PAGES[REPO_NATIVE]["file"]).read_text(encoding="utf-8")
        self.assertIn("\nMethod: native\n", raw)
        page = self.omp.read(REPO_NATIVE)
        self.assertEqual((page.kind_hint, page.title, page.author, page.publisher), ("repo", "anthropics/skills", "anthropics", "GitHub"))
        self.assertEqual(len(page.items), 3)

    def test_a_transcript_read_keeps_the_title_and_transcript_but_not_the_description(self) -> None:
        raw = (FIXTURES / "omp" / "read" / PAGES[VIDEO]["file"]).read_text(encoding="utf-8")
        self.assertIn("Microplastics", raw)
        page = self.omp.read(VIDEO, "transcript")
        self.assertTrue(page.text.startswith("# Me at the zoo\n\nAll right, so here we are"), page.text[:80])
        self.assertNotIn("Microplastics", page.text)
        self.assertIn("Microplastics", self.omp.read(VIDEO).text, "a whole-page read keeps the description")

    def test_an_x_post_keeps_the_post_and_its_author_replies_only(self) -> None:
        page = self.omp.read(X_POST)
        self.assertEqual((page.kind_hint, page.author, page.publisher), ("x_post", "@jack", "X"))
        self.assertIn("just setting up my twttr", page.text)
        raw = (FIXTURES / "omp" / "read" / PAGES[X_POST]["file"]).read_text(encoding="utf-8")
        self.assertIn("@lexfridman", raw)
        self.assertNotIn("@lexfridman", page.text)

    def test_the_article_front_matter_gives_the_title(self) -> None:
        page = self.omp.read(REDIRECT)
        self.assertEqual((page.title, page.kind_hint), ("Welcome to Python.org", "article"))
        self.assertNotIn("meta_omitted", page.text)
        self.assertIn("https://www.python.org/about/gettingstarted/", page.links)

    def test_a_repo_whose_file_list_cannot_be_read_is_unreadable(self) -> None:
        limited = self.enterContext(Replay(lambda m, p, b: (403, b'{"message": "API rate limit exceeded"}')))
        got = OmpHost(github_api=limited.url).read(REPO)
        self.assertIsInstance(got, ports.Unreadable)
        self.assertEqual(got.reason, "error")
        self.assertIn("HTTP 403", got.detail)


class RecordedCall(Recorded, suite.CallContract, suite.CallStopContract, unittest.TestCase):
    TOOL_ROLE = "tiny"
    CUT_OFF_ROLE = "tiny"
    REFUSED_ROLE = "tiny"

    def make_call(self) -> ports.CallPort:
        return self.omp

    def test_the_gateway_request_names_the_role_and_forces_the_tool(self) -> None:
        reply = self.omp.call(
            "tiny", [{"role": "user", "content": suite.FORCED_TOOL_MESSAGE}], [suite.RECORD_TOOL], "record", 200
        )
        gateway = [run for run in self.runs() if run["argv"] == ["auth-gateway", "stdio"]]
        self.assertEqual(len(gateway), 1)
        request = json.loads(gateway[0]["stdin"])
        self.assertEqual(request["path"], "/v1/messages")
        body = request["body"]
        self.assertEqual((body["model"], body["max_tokens"]), ("@tiny", 200))
        self.assertEqual(body["tool_choice"], {"type": "tool", "name": "record"})
        self.assertEqual(body["tools"], [suite.RECORD_TOOL])
        self.assertEqual(
            (reply.model, reply.thinking, reply.usage),
            ("anthropic/claude-haiku-5-5", "high", ports.Usage(18, 64, 0, 540)),
        )

    def test_a_missing_role_starts_no_gateway(self) -> None:
        with self.assertRaises(ports.RoleMissing):
            self.omp.call(suite.MISSING_ROLE, [{"role": "user", "content": "hi"}], [], None, 10)
        self.assertNotIn(["auth-gateway", "stdio"], [run["argv"] for run in self.runs()])


class RecordedQuota(Recorded, suite.QuotaContract, unittest.TestCase):
    PROVIDER = "anthropic"

    def make_quota(self) -> ports.QuotaPort:
        return self.omp

    def test_a_window_keeps_the_gateway_values(self) -> None:
        rows = self.omp.windows(["anthropic"])
        self.assertEqual(
            rows[0], ports.Window("anthropic", "anthropic:5h", 18000, 0.08, "2026-11-09T19:20:00+00:00")
        )
        self.assertEqual(len(rows), 3)


class RecordedFacts(Recorded, suite.FactsContract, unittest.TestCase):
    KNOWN_ROLE = "smol"

    def make_facts(self) -> ports.HostFacts:
        return self.omp

    def test_role_fix_gives_the_config_lines_and_the_config_file(self) -> None:
        fix = self.omp.role_fix({"atlas_escalate": "anthropic/claude-opus-5-5:medium"})
        self.assertEqual(fix.lines, ("modelRoles:", "  atlas_escalate: anthropic/claude-opus-5-5:medium"))
        self.assertEqual(fix.where, "/home/kim/.omp/agent/config.yml")

    def test_version_context_and_roles_match_the_recording(self) -> None:
        self.assertEqual(self.omp.version(), "18.18.2")
        self.assertEqual(self.omp.role_context("smol"), 1000000)
        self.assertEqual(self.omp.roles()["judge"], "openrouter/~typesafe/jev-latest")


if __name__ == "__main__":
    unittest.main()
