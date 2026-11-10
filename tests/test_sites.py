"""The site table (spec 4.9): one row each for X, GitHub and YouTube, through link cleanup.

Each row joins its tracking and spelling variants into one link, keeps different
pages apart, touches no other host, and says which sources cannot change.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "atlas-ask"))
from atlas.core import links, sites  # noqa: E402


def normalize(value: str) -> str:
    return links.normalize_canonical_url(value)


class XRowTests(unittest.TestCase):
    def test_aliases_handle_case_and_media_suffixes_join_one_post(self) -> None:
        for value in (
            "https://twitter.com/user/status/1",
            "https://www.twitter.com/User/status/1",
            "https://www.x.com/USER/status/1/photo/2",
            "https://x.com/user/status/1/video/1?s=20",
        ):
            with self.subTest(value=value):
                self.assertEqual(normalize(value), "https://x.com/user/status/1")
        self.assertEqual(
            normalize("https://mobile.twitter.com/user/status/1"), "https://mobile.twitter.com/user/status/1"
        )
        self.assertNotEqual(normalize("https://x.com/user/status/1"), normalize("https://x.com/user/status/2"))

    def test_numeric_s_is_removed_in_every_position(self) -> None:
        self.assertEqual(normalize("https://x.com/u/status/1?s=20&foo=a"), "https://x.com/u/status/1?foo=a")
        self.assertEqual(normalize("https://x.com/u/status/1?foo=a&s=20&bar=b"), "https://x.com/u/status/1?foo=a&bar=b")
        self.assertEqual(normalize("https://x.com/u/status/1?foo=a&s=20"), "https://x.com/u/status/1?foo=a")
        self.assertEqual(normalize("https://x.com/u/status/1?s=20&s=21"), "https://x.com/u/status/1")
        self.assertEqual(normalize("https://x.com/u/status/1?s=%32%30"), "https://x.com/u/status/1")
        self.assertEqual(normalize("https://x.com/u?foo=a+b;s=20&s=20&bar=%2f"), "https://x.com/u?foo=a+b;s=20&bar=%2f")

    def test_nonnumeric_empty_unicode_and_case_variant_s_survive(self) -> None:
        self.assertEqual(normalize("https://x.com/u/status/1?s=abc"), "https://x.com/u/status/1?s=abc")
        self.assertEqual(normalize("https://x.com/u/status/1?s="), "https://x.com/u/status/1?s=")
        self.assertEqual(normalize("https://x.com/u/status/1?s=٢٠"), "https://x.com/u/status/1?s=٢٠")
        self.assertEqual(normalize("https://x.com/u/status/1?S=20"), "https://x.com/u/status/1?S=20")
        self.assertEqual(normalize("https://example.com/?s=20"), "https://example.com/?s=20")

    def test_a_post_cannot_change_and_a_profile_can(self) -> None:
        self.assertTrue(sites.unchangeable(normalize("https://twitter.com/User/status/1/photo/1")))
        self.assertFalse(sites.unchangeable(normalize("https://x.com/user")))


class GitHubRowTests(unittest.TestCase):
    def test_owner_and_repo_case_and_ref_join_one_repo(self) -> None:
        for value in (
            "https://github.com/EveryInc/compound-engineering-plugin",
            "https://github.com/everyinc/Compound-Engineering-Plugin?ref=producthunt",
        ):
            with self.subTest(value=value):
                self.assertEqual(normalize(value), "https://github.com/everyinc/compound-engineering-plugin")

    def test_paths_inside_a_repo_and_other_hosts_keep_their_case(self) -> None:
        self.assertEqual(
            normalize("https://github.com/Owner/Repo/blob/main/Docs/README.md?plain=1"),
            "https://github.com/owner/repo/blob/main/Docs/README.md?plain=1",
        )
        self.assertNotEqual(
            normalize("https://github.com/zilliztech/memsearch"),
            normalize("https://github.com/zilliztech/memsearch/blob/main/README.md"),
        )
        self.assertEqual(normalize("https://gitlab.com/Owner/Repo?ref=x"), "https://gitlab.com/Owner/Repo?ref=x")

    def test_a_file_pinned_to_a_commit_cannot_change_and_a_branch_file_can(self) -> None:
        commit = "66898f60e8c744e269f8ce06c2b2b99ce7660d5f"
        self.assertTrue(sites.unchangeable(normalize(f"https://github.com/o/r/blob/{commit}/SKILL.md")))
        self.assertTrue(sites.unchangeable(normalize(f"https://github.com/o/r/tree/{commit}/skills")))
        self.assertFalse(sites.unchangeable(normalize("https://github.com/o/r/blob/main/SKILL.md")))
        self.assertFalse(sites.unchangeable(normalize("https://github.com/o/r")))


class YouTubeRowTests(unittest.TestCase):
    def test_share_trackers_and_the_short_link_join_one_video(self) -> None:
        for value in (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&si=abc&feature=shared",
            "https://youtu.be/dQw4w9WgXcQ?si=abc",
        ):
            with self.subTest(value=value):
                self.assertEqual(normalize(value), "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(normalize("https://youtu.be/dQw4w9WgXcQ?t=30"), "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30")
        self.assertNotEqual(normalize("https://www.youtube.com/watch?v=A1"), normalize("https://www.youtube.com/watch?v=B2"))
        self.assertFalse(sites.unchangeable(normalize("https://youtu.be/dQw4w9WgXcQ")))


class NoFoldingTests(unittest.TestCase):
    def test_www_and_http_are_not_folded(self) -> None:
        self.assertEqual(normalize("http://www.example.com/a"), "http://www.example.com/a")
        self.assertEqual(normalize("http://github.com/o/r"), "http://github.com/o/r")
        self.assertNotEqual(normalize("https://www.example.com/a"), normalize("https://example.com/a"))
        self.assertFalse(sites.unchangeable(normalize("https://example.com/a")))


if __name__ == "__main__":
    unittest.main()
