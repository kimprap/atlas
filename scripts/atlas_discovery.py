#!/usr/bin/env python3
"""Pure, bounded Atlas discovery-candidate normalization."""

from __future__ import annotations

from typing import Final

import atlas_url


VERSION: Final = 1
_SCOPE_KEYS: Final = frozenset({"kind", "identifier", "limit"})
_CANDIDATE_KEYS: Final = frozenset({"url", "discovered_from", "label"})
_MANIFEST_KEYS: Final = frozenset({"source_id", "canonical_url", "status"})
_MANIFEST_STATUSES: Final = frozenset({"active", "archived"})


def _exact_object(value: object, keys: frozenset[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must contain exactly {sorted(keys)!r}")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value


def _rows(value: object, label: str) -> list[object] | tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be an array")
    return value


def _normalize_scope(scope: object) -> dict[str, object]:
    raw_scope = _exact_object(scope, _SCOPE_KEYS, "scope")
    kind = _string(raw_scope["kind"], "scope.kind")
    identifier = _string(raw_scope["identifier"], "scope.identifier")
    if not kind or not identifier:
        raise ValueError("scope kind and identifier must be nonempty")
    limit = raw_scope["limit"]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("scope.limit must be a positive integer")
    return {"kind": kind, "identifier": identifier, "limit": limit}


def _manifest_statuses(manifest_rows: object) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for index, value in enumerate(_rows(manifest_rows, "manifest_rows")):
        row = _exact_object(value, _MANIFEST_KEYS, f"manifest_rows[{index}]")
        source_id = _string(row["source_id"], f"manifest_rows[{index}].source_id")
        canonical_url = _string(
            row["canonical_url"], f"manifest_rows[{index}].canonical_url"
        )
        status = _string(row["status"], f"manifest_rows[{index}].status")
        try:
            normalized_url = atlas_url.normalize_canonical_url(canonical_url)
        except ValueError as exc:
            raise ValueError(
                f"manifest_rows[{index}].canonical_url is invalid"
            ) from exc
        if (
            normalized_url != canonical_url
            or atlas_url.source_id_for(canonical_url) != source_id
        ):
            raise ValueError(f"manifest_rows[{index}] identity is inconsistent")
        if status not in _MANIFEST_STATUSES:
            raise ValueError(f"manifest_rows[{index}].status is unsupported")
        if canonical_url in statuses and statuses[canonical_url] != status:
            raise ValueError(f"manifest_rows[{index}] conflicts with an earlier row")
        statuses[canonical_url] = status
    return statuses


def normalize_candidates(
    scope: object,
    candidates: object,
    manifest_rows: object = (),
) -> dict[str, object]:
    """Normalize and classify one bounded discovery result without external work.

    Inputs are JSON-shaped values. Valid candidates are deduplicated by their
    canonical Atlas URL, stably ordered by source identity, and split at the
    requested limit. Invalid URLs are retained as ordered rejection records.
    """

    normalized_scope = _normalize_scope(scope)
    manifest_statuses = _manifest_statuses(manifest_rows)
    selected_by_url: dict[str, dict[str, object]] = {}
    rejected: list[dict[str, str]] = []

    for index, value in enumerate(_rows(candidates, "candidates")):
        candidate = _exact_object(value, _CANDIDATE_KEYS, f"candidates[{index}]")
        url = _string(candidate["url"], f"candidates[{index}].url")
        discovered_from = _string(
            candidate["discovered_from"], f"candidates[{index}].discovered_from"
        )
        label = _string(candidate["label"], f"candidates[{index}].label")
        try:
            canonical_url = atlas_url.normalize_canonical_url(url)
        except ValueError as exc:
            rejected.append(
                {
                    "url": url,
                    "discovered_from": discovered_from,
                    "label": label,
                    "classification": "rejected",
                    "code": "URL_INVALID",
                    "detail": str(exc),
                }
            )
            continue
        if canonical_url in selected_by_url:
            continue

        manifest_status = manifest_statuses.get(canonical_url)
        classification = (
            "new" if manifest_status is None else f"existing-{manifest_status}"
        )
        selected_by_url[canonical_url] = {
            "source_id": atlas_url.source_id_for(canonical_url),
            "canonical_url": canonical_url,
            "classification": classification,
            "manifest_status": manifest_status,
            "discovered_from": discovered_from,
            "label": label,
        }

    accepted = sorted(
        selected_by_url.values(),
        key=lambda row: (str(row["source_id"]), str(row["canonical_url"])),
    )
    limit = normalized_scope["limit"]
    assert isinstance(limit, int)
    return {
        "version": VERSION,
        "scope": normalized_scope,
        "selected": accepted[:limit],
        "overflow": accepted[limit:],
        "rejected": rejected,
    }
