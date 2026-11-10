"""Link cleanup: the canonical form of one HTTP(S) link and its short id.

The generic rules never change the page a link opens: scheme and host case,
IDNA, the default port, the fragment, trailing ``/``, ``utm_*`` and the known
tracking parameters. Unknown parameters are kept. ``sites`` then applies its
row for the link's host.
"""

from __future__ import annotations

import hashlib
import ipaddress
import re
from urllib.parse import unquote, urljoin, urlsplit

from atlas.core import sites

_MALFORMED_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_TRACKING = frozenset({"fbclid", "gclid", "igshid", "mc_cid", "mc_eid"})


def _tracking(name: str) -> bool:
    """A ``utm_*`` or known tracking parameter name, ASCII case-insensitive."""
    prefix = name[:4]
    if prefix.isascii() and prefix.lower() == "utm_":
        return True
    return name.isascii() and name.lower() in _TRACKING


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
    rendered_port = "" if port is None or default_port else f":{port}"

    path = parts.path
    if len(path) > 1:
        path = path.rstrip("/") or "/"

    survivors: list[sites.Query] = []
    if parts.query:
        for component in parts.query.split("&"):
            raw_name, separator, raw_value = component.partition("=")
            name = _decode_query_component(raw_name)
            value = _decode_query_component(raw_value if separator else "")
            if not _tracking(name):
                survivors.append(sites.Query(component, name, value))

    cleaned = sites.clean(sites.Parts(scheme, rendered_host, rendered_port, path, tuple(survivors)))
    return cleaned.render()


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
