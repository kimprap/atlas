#!/usr/bin/env python3
"""Canonical Atlas source URL and source-ID ownership."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
from urllib.parse import unquote, urljoin, urlsplit


_MALFORMED_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_ASCII_DIGITS_RE = re.compile(r"^[0-9]+$", re.ASCII)
_X_ALIASES = {"twitter.com", "www.twitter.com", "www.x.com"}


def _ascii_utm_prefix(value: str) -> bool:
    return (
        len(value) >= 4
        and value[0] in "uU"
        and value[1] in "tT"
        and value[2] in "mM"
        and value[3] == "_"
    )


def _decode_query_component(value: str) -> str:
    try:
        return unquote(value, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("query contains invalid UTF-8 percent escapes") from exc


def _normalized_host(hostname: str) -> tuple[str, bool]:
    if not hostname:
        raise ValueError("URL authority must contain a host")
    if "%" in hostname:
        raise ValueError("zone-scoped IPv6 is not canonical")
    if any(character.isspace() or ord(character) < 0x20 for character in hostname):
        raise ValueError("URL host contains whitespace or control characters")

    lowered = hostname.lower()
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        if lowered.endswith("."):
            lowered = lowered[:-1]
        if not lowered:
            raise ValueError("URL authority must contain a host")
        try:
            encoded = lowered.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("URL host is not valid IDNA") from exc
        if not encoded or any(not label for label in encoded.split(".")):
            raise ValueError("URL host is not valid IDNA")
        if encoded in _X_ALIASES:
            encoded = "x.com"
        return encoded, False

    if isinstance(address, ipaddress.IPv6Address):
        return address.compressed.lower(), True
    return str(address), False


def normalize_canonical_url(url: str) -> str:
    """Return the canonical Atlas identity URL for one explicit HTTP(S) input."""
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    value = url.strip()
    if not value:
        raise ValueError("url must not be empty")
    if _MALFORMED_ESCAPE_RE.search(value):
        raise ValueError("URL contains a malformed percent escape")

    try:
        parts = urlsplit(value)
    except ValueError as exc:
        raise ValueError(f"invalid URL: {exc}") from exc
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("URL scheme must be explicit HTTP or HTTPS")
    if not parts.netloc:
        raise ValueError("URL authority must contain a host")
    try:
        username = parts.username
        password = parts.password
        hostname = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise ValueError(f"invalid URL authority: {exc}") from exc
    if username is not None or password is not None:
        raise ValueError("URL userinfo is not allowed")
    authority_without_userinfo = parts.netloc.rsplit("@", 1)[-1]
    if authority_without_userinfo.endswith(":"):
        raise ValueError("URL port must be numeric and nonempty")
    if hostname is None:
        raise ValueError("URL authority must contain a host")

    host, ipv6 = _normalized_host(hostname)
    default_port = (scheme == "http" and port == 80) or (
        scheme == "https" and port == 443
    )
    rendered_host = f"[{host}]" if ipv6 else host
    authority = (
        rendered_host if port is None or default_port else f"{rendered_host}:{port}"
    )

    path = parts.path
    if len(path) > 1:
        path = path.rstrip("/") or "/"

    query = parts.query
    if query:
        survivors: list[str] = []
        for component in query.split("&"):
            raw_name, separator, raw_value = component.partition("=")
            decoded_name = _decode_query_component(raw_name)
            decoded_value = _decode_query_component(raw_value if separator else "")
            drop = _ascii_utm_prefix(decoded_name)
            if (
                host == "x.com"
                and decoded_name == "s"
                and _ASCII_DIGITS_RE.fullmatch(decoded_value)
            ):
                drop = True
            if not drop:
                survivors.append(component)
        query = "&".join(survivors)

    canonical = f"{scheme}://{authority}{path}"
    if query:
        canonical += "?" + query
    return canonical


def resolve_reference(base_url: str, reference: str) -> tuple[str, str]:
    """Resolve one URI reference against a normalized Atlas source URL."""
    if not isinstance(base_url, str):
        raise ValueError("base URL must be a string")
    normalized_base = normalize_canonical_url(base_url)
    if base_url != normalized_base:
        raise ValueError("base URL must be normalized")
    if (
        not isinstance(reference, str)
        or not reference
        or reference.strip() != reference
    ):
        raise ValueError("reference must be a nonempty URI reference")
    canonical_url = normalize_canonical_url(urljoin(normalized_base, reference))
    return canonical_url, source_id_for(canonical_url)


def source_id_for(canonical_url: str) -> str:
    """Normalize one URL and return its 12-hex Atlas source identifier."""
    normalized = normalize_canonical_url(canonical_url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize one Atlas source URL.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    normalize = subparsers.add_parser("normalize")
    normalize.add_argument("--url", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        canonical_url = normalize_canonical_url(args.url)
        payload = {
            "canonical_url": canonical_url,
            "source_id": source_id_for(canonical_url),
        }
        sys.stdout.write(
            json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            + "\n"
        )
        return 0
    except (TypeError, ValueError) as exc:
        print(f"atlas-url: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
