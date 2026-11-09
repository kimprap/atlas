from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "atlas-ask"))
from atlas.core import links  # noqa: E402


class LinkCleanupTests(unittest.TestCase):
    def normalize(self, value: str) -> str:
        return links.normalize_canonical_url(value)

    def test_input_trimming_scheme_host_case_and_scheme_preservation(self) -> None:
        self.assertEqual(
            self.normalize("  HTTPS://Example.COM/Path  "), "https://example.com/Path"
        )
        self.assertEqual(self.normalize("http://EXAMPLE.com"), "http://example.com")
        self.assertEqual(self.normalize("https://EXAMPLE.com"), "https://example.com")

    def test_credentials_and_invalid_authorities_are_rejected(self) -> None:
        for value in (
            "https://user@example.com",
            "https://user:pass@example.com",
            "https://",
            "https:///path",
            "https://example com/path",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.normalize(value)

    def test_default_nondefault_and_invalid_ports(self) -> None:
        self.assertEqual(self.normalize("http://example.com:80"), "http://example.com")
        self.assertEqual(
            self.normalize("https://example.com:443"), "https://example.com"
        )
        self.assertEqual(
            self.normalize("http://example.com:443"), "http://example.com:443"
        )
        self.assertEqual(
            self.normalize("https://example.com:80"), "https://example.com:80"
        )
        self.assertEqual(
            self.normalize("https://example.com:8443"), "https://example.com:8443"
        )
        for value in (
            "https://example.com:",
            "https://example.com:nope",
            "https://example.com:65536",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.normalize(value)

    def test_ip_idna_and_terminal_dns_dot_normalization(self) -> None:
        self.assertEqual(self.normalize("http://192.0.2.1:80/a"), "http://192.0.2.1/a")
        self.assertEqual(
            self.normalize("https://[2001:0DB8:0:0:0:0:0:1]:443"),
            "https://[2001:db8::1]",
        )
        self.assertEqual(
            self.normalize("https://BÜCHER.example./"), "https://xn--bcher-kva.example/"
        )
        with self.assertRaises(ValueError):
            self.normalize("https://[fe80::1%25en0]/")

    def test_x_aliases_are_canonicalized(self) -> None:
        for host in ("twitter.com", "www.twitter.com", "www.x.com", "x.com"):
            with self.subTest(host=host):
                self.assertEqual(
                    self.normalize(f"https://{host}/user/status/1"),
                    "https://x.com/user/status/1",
                )
        self.assertEqual(
            self.normalize("https://mobile.twitter.com/user/status/1"),
            "https://mobile.twitter.com/user/status/1",
        )

    def test_empty_root_and_nonroot_paths_remain_distinct(self) -> None:
        self.assertEqual(self.normalize("https://example.com"), "https://example.com")
        self.assertEqual(self.normalize("https://example.com/"), "https://example.com/")
        self.assertEqual(
            self.normalize("https://example.com/a///"), "https://example.com/a"
        )
        self.assertEqual(
            self.normalize("https://example.com/%2fA/"), "https://example.com/%2fA"
        )
        self.assertEqual(
            self.normalize("https://example.com/a/../b/"), "https://example.com/a/../b"
        )

    def test_fragments_empty_queries_and_utm_components_are_removed(self) -> None:
        self.assertEqual(
            self.normalize("https://example.com/a?#fragment"), "https://example.com/a"
        )
        self.assertEqual(
            self.normalize("https://example.com/a?foo=1&UTM_Source=x&bar=2#fragment"),
            "https://example.com/a?foo=1&bar=2",
        )
        self.assertEqual(
            self.normalize("https://example.com/?%75tm_source=x"),
            "https://example.com/",
        )

    def test_x_numeric_s_is_removed_in_every_position(self) -> None:
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?s=20&foo=a"),
            "https://x.com/u/status/1?foo=a",
        )
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?foo=a&s=20&bar=b"),
            "https://x.com/u/status/1?foo=a&bar=b",
        )
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?foo=a&s=20"),
            "https://x.com/u/status/1?foo=a",
        )
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?s=20&s=21"),
            "https://x.com/u/status/1",
        )
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?s=%32%30"),
            "https://x.com/u/status/1",
        )

    def test_nonnumeric_empty_unicode_and_case_variant_s_survive(self) -> None:
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?s=abc"),
            "https://x.com/u/status/1?s=abc",
        )
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?s="), "https://x.com/u/status/1?s="
        )
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?s=٢٠"),
            "https://x.com/u/status/1?s=٢٠",
        )
        self.assertEqual(
            self.normalize("https://x.com/u/status/1?S=20"),
            "https://x.com/u/status/1?S=20",
        )
        self.assertEqual(
            self.normalize("https://example.com/?s=20"), "https://example.com/?s=20"
        )

    def test_surviving_query_bytes_order_and_empty_components_are_preserved(
        self,
    ) -> None:
        value = "https://example.com/?a=one+two&&semi=x;y&dup=1&dup=2&esc=%2f%2F&"
        self.assertEqual(self.normalize(value), value)
        self.assertEqual(
            self.normalize("https://x.com/u?foo=a+b;s=20&s=20&bar=%2f"),
            "https://x.com/u?foo=a+b;s=20&bar=%2f",
        )

    def test_malformed_escapes_and_query_utf8_are_rejected(self) -> None:
        for value in (
            "https://example.com/%",
            "https://example.com/?x=%2",
            "https://example.com/?x=%GG",
            "https://example.com/?x=%FF",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.normalize(value)

    def test_invalid_schemes_and_unbracketed_ipv6_are_rejected(self) -> None:
        for value in (
            "example.com",
            "ftp://example.com",
            "mailto:a@example.com",
            "https://2001:db8::1/",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.normalize(value)

    def test_normalization_is_idempotent(self) -> None:
        inputs = (
            " HTTPS://www.X.com/u/status/1?foo=%2f&s=20&utm_medium=x#frag ",
            "https://BÜCHER.example./a///?x=1&&y=2",
            "http://[2001:0db8::1]:80/",
        )
        for value in inputs:
            with self.subTest(value=value):
                once = self.normalize(value)
                self.assertEqual(self.normalize(once), once)

    def test_exact_known_source_id_prefixes(self) -> None:
        self.assertEqual(
            links.source_id_for("https://x.com/example/status/1?foo=a&bar=b"),
            "abca97778de4",
        )
        self.assertEqual(
            links.source_id_for("https://arxiv.org/abs/2606.24937"), "a2cb64316448"
        )

    def test_reference_resolution_normalizes_after_joining(self) -> None:
        canonical_url, source_id = links.resolve_reference(
            "https://example.com/guides/current",
            "source?utm_source=test#section",
        )
        self.assertEqual(canonical_url, "https://example.com/guides/source")
        self.assertEqual(source_id, links.source_id_for(canonical_url))

        for base_url, reference in (
            ("HTTPS://EXAMPLE.COM/guides/current", "child"),
            ("https://example.com/guides/current", " child"),
            ("https://example.com/guides/current", "mailto:owner@example.com"),
        ):
            with self.subTest(base_url=base_url, reference=reference):
                with self.assertRaises(ValueError):
                    links.resolve_reference(base_url, reference)


if __name__ == "__main__":
    unittest.main()
