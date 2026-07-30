from __future__ import annotations

import json
import socket
import sys
import unittest
import urllib.request
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_discovery  # noqa: E402
import atlas_url  # noqa: E402


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        + b"\n"
    )


def invalid_url_detail(value: str) -> str:
    try:
        atlas_url.normalize_canonical_url(value)
    except ValueError as exc:
        return str(exc)
    raise AssertionError(f"fixture must be rejected by atlas_url: {value!r}")


def manifest_row(canonical_url: str, status: str) -> dict[str, str]:
    return {
        "source_id": atlas_url.source_id_for(canonical_url),
        "canonical_url": canonical_url,
        "status": status,
    }


class AtlasDiscoveryTests(unittest.TestCase):
    @contextmanager
    def forbid_external_work(self):
        forbidden = mock.Mock(
            side_effect=AssertionError("discovery normalization must be pure")
        )
        with ExitStack() as stack:
            for name in (
                "fetch",
                "crawl",
                "score",
                "decide_officialness",
                "is_official",
            ):
                stack.enter_context(
                    mock.patch.object(
                        atlas_discovery, name, side_effect=forbidden, create=True
                    )
                )
            stack.enter_context(
                mock.patch.object(urllib.request, "urlopen", side_effect=forbidden)
            )
            stack.enter_context(
                mock.patch.object(socket, "create_connection", side_effect=forbidden)
            )
            yield forbidden

    def normalize(
        self,
        scope: object,
        candidates: object,
        manifest_rows: object = (),
    ) -> dict[str, object]:
        with self.forbid_external_work() as forbidden:
            result = atlas_discovery.normalize_candidates(
                scope, candidates, manifest_rows
            )
        forbidden.assert_not_called()
        return result

    def test_normalizes_deduplicates_classifies_limits_and_rerenders_canonically(
        self,
    ) -> None:
        active_url = atlas_url.normalize_canonical_url(
            " HTTPS://Example.COM/Path?utm_source=discard#section "
        )
        archived_url = atlas_url.normalize_canonical_url(
            "HTTPS://Example.COM/Archived#old"
        )
        new_url = atlas_url.normalize_canonical_url(
            "https://example.com/New?utm_medium=discard"
        )
        invalid_one = "not a URL"
        invalid_two = "ftp://example.com/outside"
        scope = {"kind": "search", "identifier": "synthetic-batch", "limit": 2}
        candidates = [
            {
                "url": " HTTPS://Example.COM/Path?utm_source=discard#section ",
                "discovered_from": "synthetic-first",
                "label": "First provenance",
            },
            {
                "url": invalid_one,
                "discovered_from": "synthetic-invalid-one",
                "label": "Rejected one",
            },
            {
                "url": "https://example.com/Path?utm_campaign=discard",
                "discovered_from": "synthetic-duplicate",
                "label": "Must not replace provenance",
            },
            {
                "url": "HTTPS://Example.COM/Archived#old",
                "discovered_from": "synthetic-archived",
                "label": "Archived source",
            },
            {
                "url": "https://example.com/New?utm_medium=discard",
                "discovered_from": "synthetic-new",
                "label": "Café source",
            },
            {
                "url": invalid_two,
                "discovered_from": "synthetic-invalid-two",
                "label": "Rejected two",
            },
        ]
        manifest_rows = [
            manifest_row(active_url, "active"),
            manifest_row(archived_url, "archived"),
        ]

        accepted = [
            {
                "source_id": atlas_url.source_id_for(active_url),
                "canonical_url": active_url,
                "classification": "existing-active",
                "manifest_status": "active",
                "discovered_from": "synthetic-first",
                "label": "First provenance",
            },
            {
                "source_id": atlas_url.source_id_for(archived_url),
                "canonical_url": archived_url,
                "classification": "existing-archived",
                "manifest_status": "archived",
                "discovered_from": "synthetic-archived",
                "label": "Archived source",
            },
            {
                "source_id": atlas_url.source_id_for(new_url),
                "canonical_url": new_url,
                "classification": "new",
                "manifest_status": None,
                "discovered_from": "synthetic-new",
                "label": "Café source",
            },
        ]
        accepted.sort(key=lambda row: (row["source_id"], row["canonical_url"]))
        expected = {
            "version": 1,
            "scope": scope,
            "selected": accepted[:2],
            "overflow": accepted[2:],
            "rejected": [
                {
                    "url": invalid_one,
                    "discovered_from": "synthetic-invalid-one",
                    "label": "Rejected one",
                    "classification": "rejected",
                    "code": "URL_INVALID",
                    "detail": invalid_url_detail(invalid_one),
                },
                {
                    "url": invalid_two,
                    "discovered_from": "synthetic-invalid-two",
                    "label": "Rejected two",
                    "classification": "rejected",
                    "code": "URL_INVALID",
                    "detail": invalid_url_detail(invalid_two),
                },
            ],
        }

        actual = self.normalize(scope, candidates, manifest_rows)
        rerendered = self.normalize(dict(scope), list(candidates), tuple(manifest_rows))

        self.assertEqual(actual, expected)
        self.assertEqual(rerendered, expected)
        self.assertEqual(canonical_bytes(actual), canonical_bytes(expected))
        self.assertEqual(canonical_bytes(actual), canonical_bytes(rerendered))
        self.assertTrue(canonical_bytes(actual).endswith(b"\n"))
        self.assertIn("Café".encode("utf-8"), canonical_bytes(actual))
        self.assertEqual(
            [
                (row["source_id"], row["canonical_url"])
                for row in actual["selected"] + actual["overflow"]
            ],
            sorted(
                (row["source_id"], row["canonical_url"])
                for row in actual["selected"] + actual["overflow"]
            ),
        )
        self.assertEqual(len(actual["selected"]), scope["limit"])
        self.assertEqual(len(actual["selected"]) + len(actual["overflow"]), 3)
        self.assertEqual(
            [row["classification"] for row in actual["rejected"]],
            ["rejected", "rejected"],
        )

    def test_rejects_invalid_exact_shapes_and_limits_without_external_work(
        self,
    ) -> None:
        url = atlas_url.normalize_canonical_url("https://example.com/valid")
        valid_scope = {"kind": "search", "identifier": "synthetic-batch", "limit": 1}
        valid_candidate = {
            "url": url,
            "discovered_from": "synthetic",
            "label": "Valid source",
        }
        valid_manifest = manifest_row(url, "active")
        invalid_calls = (
            (
                "scope has an unknown key",
                {**valid_scope, "extra": "no"},
                [valid_candidate],
                (),
            ),
            (
                "scope omits a required key",
                {"kind": "search", "identifier": "synthetic-batch"},
                [valid_candidate],
                (),
            ),
            (
                "scope kind has the wrong type",
                {**valid_scope, "kind": ["search"]},
                [valid_candidate],
                (),
            ),
            (
                "scope root has the wrong type",
                ["search", "synthetic-batch", 1],
                [valid_candidate],
                (),
            ),
            (
                "scope identifier has the wrong type",
                {**valid_scope, "identifier": 1},
                [valid_candidate],
                (),
            ),
            (
                "limit is boolean",
                {**valid_scope, "limit": True},
                [valid_candidate],
                (),
            ),
            (
                "limit is zero",
                {**valid_scope, "limit": 0},
                [valid_candidate],
                (),
            ),
            (
                "limit is negative",
                {**valid_scope, "limit": -1},
                [valid_candidate],
                (),
            ),
            (
                "limit has the wrong type",
                {**valid_scope, "limit": "1"},
                [valid_candidate],
                (),
            ),
            (
                "candidate has an unknown key",
                valid_scope,
                [{**valid_candidate, "extra": "no"}],
                (),
            ),
            (
                "candidate omits a required key",
                valid_scope,
                [{"url": url, "discovered_from": "synthetic"}],
                (),
            ),
            (
                "candidate field has the wrong type",
                valid_scope,
                [{**valid_candidate, "label": 1}],
                (),
            ),
            (
                "candidate URL has the wrong type",
                valid_scope,
                [{**valid_candidate, "url": 1}],
                (),
            ),
            (
                "candidate provenance has the wrong type",
                valid_scope,
                [{**valid_candidate, "discovered_from": 1}],
                (),
            ),
            (
                "candidate collection has the wrong type",
                valid_scope,
                valid_candidate,
                (),
            ),
            (
                "manifest row has an unknown key",
                valid_scope,
                [valid_candidate],
                [{**valid_manifest, "extra": "no"}],
            ),
            (
                "manifest row omits a required key",
                valid_scope,
                [valid_candidate],
                [{"source_id": valid_manifest["source_id"], "status": "active"}],
            ),
            (
                "manifest status is unsupported",
                valid_scope,
                [valid_candidate],
                [{**valid_manifest, "status": "paused"}],
            ),
            (
                "manifest field has the wrong type",
                valid_scope,
                [valid_candidate],
                [{**valid_manifest, "source_id": 1}],
            ),
            (
                "manifest canonical URL has the wrong type",
                valid_scope,
                [valid_candidate],
                [{**valid_manifest, "canonical_url": 1}],
            ),
            (
                "manifest status has the wrong type",
                valid_scope,
                [valid_candidate],
                [{**valid_manifest, "status": 1}],
            ),
            (
                "manifest collection has the wrong type",
                valid_scope,
                [valid_candidate],
                valid_manifest,
            ),
        )

        for label, scope, candidates, manifest_rows in invalid_calls:
            with self.subTest(label=label), self.forbid_external_work() as forbidden:
                with self.assertRaises(ValueError):
                    atlas_discovery.normalize_candidates(
                        scope, candidates, manifest_rows
                    )
                forbidden.assert_not_called()


if __name__ == "__main__":
    unittest.main()
