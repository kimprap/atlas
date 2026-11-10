"""The OMP adapter: the read, call and quota ports and the host facts capability.

Everything runs through the ``omp`` command: ``omp read <link>`` reads a page,
``omp auth-gateway stdio`` answers model calls and the ``/v1/models`` and
``/v1/usage`` reads, and ``omp config`` and ``omp --version`` supply the facts.
A repo page's sub-items come from GitHub's unauthenticated tree API; a repo
page whose file list cannot be read is unreadable, not a page without items.
A GitHub repo link is a repo by its link, whatever ``Method`` omp reports (it
falls back to ``native`` when GitHub's API refuses it). Read scope
``transcript`` keeps the page's ``## Transcript`` section under its title; a
page without one is unreadable with reason ``no_transcript``.
Image bytes are fetched directly with a plain HTTP GET, because ``omp read``
prints text, not image bytes; an image page lists its own link as its image.
One ``OmpHost`` serves one command; role and model lists are read once per command.
"""

from __future__ import annotations

import base64
import http.client
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

from atlas import ports

READ_TIMEOUT_S = 90
CALL_TIMEOUT_S = 600
GATEWAY_TIMEOUT_S = 60
FACT_TIMEOUT_S = 30
GITHUB_API = "https://api.github.com"
GITHUB_TIMEOUT_S = 30
IMAGE_TIMEOUT_S = 30
# The largest image a model call takes inline.
IMAGE_MAX_BYTES = 5 * 1024 * 1024

THINKING_LEVELS = frozenset({"off", "minimal", "low", "medium", "high", "xhigh", "max", "auto"})
# omp's placeholder tool input when the model's tool JSON does not parse: ``{__parseError, __rawJson}``.
TOOL_PARSE_ERROR = "__parseError"

# ``omp read`` header keys; the header ends at the first blank line, then ``---``.
HEADER = re.compile(r"^(URL|Content-Type|Method|Notes): ?(.*)$")
# A GitHub or X counter line: two or more ``Name: number`` items joined by `` · ``.
COUNTER = re.compile(r"^[A-Z][A-Za-z]*: [\d.,]+[KMB]?(?: · [A-Z][A-Za-z]*: [\d.,]+[KMB]?)+$")
# An X post or reply heading: ``### @handle (name) · date · link``.
X_HEADING = re.compile(r"^### @(\w+) \((.*?)\) · (.*?) · (\S+)$")
HTTP_STATUS = re.compile(r"HTTP (\d{3})")
MD_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)")
BARE_URL = re.compile(r"(?<![(\[])\bhttps?://[^\s)\]>\"']+")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")

# ``Method`` values that settle the kind on their own.
METHOD_KINDS = {"github-repo": "repo", "image": "image", "feed": "link_list"}
# ``Method`` values whose page is prose; anything else not settled is ``unknown``.
ARTICLE_METHODS = frozenset(
    {"native", "alternate-markdown", "content-negotiation", "raw-html", "llms.txt", "markit", "text"}
)
VIDEO_HOSTS = ("youtube.com", "youtu.be", "vimeo.com")
PAPER_HOSTS = ("arxiv.org",)
GITHUB_HOSTS = frozenset({"github.com", "www.github.com"})
# First path parts of github.com pages that are not an owner's repo.
GITHUB_NOT_OWNERS = frozenset(
    {
        "about", "apps", "collections", "contact", "customer-stories", "enterprise", "events", "explore",
        "features", "login", "marketplace", "new", "notifications", "orgs", "organizations", "pricing",
        "pulls", "issues", "search", "security", "settings", "site", "sponsors", "topics", "trending", "users",
    }
)
TRANSCRIPT = "transcript"
TRANSCRIPT_HEADING = re.compile(r"^## Transcript\b.*$", re.M)
SECTION_HEADING = re.compile(r"^## ", re.M)
TITLE_LINE = re.compile(r"^# .+$", re.M)
# The files that mark a repo folder as a skill, plugin or package.
ITEM_MARKERS = {
    "SKILL.md": "skill",
    ".claude-plugin/plugin.json": "plugin",
    "package.json": "package",
    "pyproject.toml": "package",
    "Cargo.toml": "package",
    "go.mod": "package",
}

STOP_REASONS = {
    "end_turn": "end",
    "stop_sequence": "end",
    "tool_use": "tool",
    "max_tokens": "cut_off",
    "refusal": "refused",
}


def _host(link: str) -> str:
    return (urllib.parse.urlsplit(link).hostname or "").removeprefix("www.")


def _unique(items: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def _split_header(output: str) -> tuple[dict[str, str], str]:
    """``omp read`` output as (header fields, body); the ``---`` after the header is dropped."""
    lines = output.split("\n")
    header: dict[str, str] = {}
    at = 0
    while at < len(lines) and lines[at].strip():
        match = HEADER.match(lines[at])
        if match is None:
            break
        header[match.group(1)] = match.group(2).strip()
        at += 1
    while at < len(lines) and not lines[at].strip():
        at += 1
    if at < len(lines) and lines[at].strip() == "---":
        at += 1
    return header, "\n".join(lines[at:])


def _front_matter(body: str) -> tuple[dict[str, str], str]:
    """A leading ``---`` front matter block as fields, and the body without it."""
    stripped = body.lstrip("\n")
    if not stripped.startswith("---\n"):
        return {}, body
    end = stripped.find("\n---", 4)
    if end < 0:
        return {}, body
    fields: dict[str, str] = {}
    for line in stripped[4:end].split("\n"):
        key, sep, value = line.partition(":")
        if sep and key and not key.startswith(" "):
            fields[key.strip()] = value.strip().strip('"')
    return fields, stripped[end + 4 :].lstrip("\n")


def _unreadable(header: Mapping[str, str]) -> ports.Unreadable | None:
    method = header.get("Method", "")
    notes = header.get("Notes", "")
    if method == "x-unavailable":
        return ports.Unreadable("no_reader", notes or "X pages of this kind cannot be read")
    if method == "blocked":
        return ports.Unreadable("error", notes or "the page is behind bot protection")
    if method != "failed":
        return None
    status = HTTP_STATUS.search(notes)
    code = int(status.group(1)) if status else None
    if code in (404, 410):
        return ports.Unreadable("gone", notes)
    if code in (401, 403):
        return ports.Unreadable("login", notes)
    if code == 402:
        return ports.Unreadable("paywall", notes)
    return ports.Unreadable("error", notes or "the page could not be fetched")


def github_repo(link: str) -> tuple[str, str] | None:
    """The (owner, repo) a github.com repo link names, or ``None`` for any other link."""
    parts = urllib.parse.urlsplit(link)
    if (parts.hostname or "").lower() not in GITHUB_HOSTS:
        return None
    path = [part for part in parts.path.split("/") if part]
    if len(path) != 2 or path[0].lower() in GITHUB_NOT_OWNERS:
        return None
    return path[0], path[1].removesuffix(".git")


def _transcript(text: str) -> str | None:
    """The page's title line and its ``## Transcript`` section, or ``None`` when it has none."""
    heading = TRANSCRIPT_HEADING.search(text)
    if heading is None:
        return None
    rest = text[heading.end():]
    end = SECTION_HEADING.search(rest)
    body = (rest[: end.start()] if end else rest).strip().strip("-").strip()
    if not body:
        return None
    title = TITLE_LINE.search(text[: heading.start()])
    return f"{title.group(0)}\n\n{body}" if title else body


def _kind_hint(method: str, content_type: str, link: str) -> str:
    host = _host(link)
    if method == "x-search":
        return "x_post" if "/status/" in link else "unknown"
    if github_repo(link) is not None:
        return "repo"
    if method in METHOD_KINDS:
        return METHOD_KINDS[method]
    if host.endswith(VIDEO_HOSTS):
        return "video"
    if host.endswith(PAPER_HOSTS) or content_type.startswith("application/pdf"):
        return "paper"
    if method in ARTICLE_METHODS:
        path = urllib.parse.urlsplit(link).path
        if host.startswith("docs.") or path.startswith("/docs/") or "/docs/" in path:
            return "docs"
        return "article"
    return "unknown"


def _x_thread(body: str) -> tuple[str, str | None, str | None]:
    """Keep the post and its author's own replies, numbered in page order.

    Returns (text, author handle, published) for the post.
    """
    author = published = None
    kept: list[str] = []
    section = ""
    keep_block = True
    replies = 0
    for line in body.split("\n"):
        if line.startswith("## "):
            section = line[3:].strip()
            keep_block = True
            if section == "Replies":
                kept.append("## Author replies")
                continue
        heading = X_HEADING.match(line)
        if heading is not None:
            handle = heading.group(1)
            if section == "Post" and author is None:
                author, published = handle, heading.group(3)
            if section == "Replies":
                keep_block = handle.lower() == (author or "").lower()
                if keep_block:
                    replies += 1
                    line = f"### Reply {replies}: {line[4:]}"
        if keep_block:
            kept.append(line)
    if replies == 0 and "## Author replies" in kept:
        at = kept.index("## Author replies")
        kept = kept[:at]
    return "\n".join(kept).strip("\n"), author, published


def _references(text: str, base: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(images, links) named in ``text``, made absolute against ``base``."""
    images = [urllib.parse.urljoin(base, ref) for ref in MD_IMAGE.findall(text)]
    links: list[str] = []
    for ref in MD_LINK.findall(text):
        links.append(urllib.parse.urljoin(base, ref))
    for ref in BARE_URL.findall(text):
        ref = ref.rstrip(".,;:")
        path = urllib.parse.urlsplit(ref).path.lower()
        if path.endswith(IMAGE_SUFFIXES) or "pbs.twimg.com/media/" in ref:
            images.append(ref)
        else:
            links.append(ref)
    return _unique(images), _unique([link for link in links if link not in images])


def repo_items(tree: Sequence[Mapping[str, Any]], owner: str, repo: str) -> tuple[ports.RepoItem, ...]:
    """Skill, plugin and package folders found in a GitHub tree listing, in path order."""
    found: dict[str, str] = {}
    for entry in tree:
        if entry.get("type") != "blob" or not isinstance(entry.get("path"), str):
            continue
        path = PurePosixPath(entry["path"])
        for marker, kind in ITEM_MARKERS.items():
            depth = len(PurePosixPath(marker).parts)
            if tuple(path.parts[-depth:]) != PurePosixPath(marker).parts:
                continue
            if len(path.parts) <= depth:
                continue  # the repo itself is the page, not one of its items
            found.setdefault(str(PurePosixPath(*path.parts[:-depth])), kind)
    return tuple(
        ports.RepoItem(path=name, link=f"https://github.com/{owner}/{repo}/tree/HEAD/{name}", kind=kind)
        for name, kind in sorted(found.items())
    )


def _status_detail(body: Any) -> str:
    if isinstance(body, Mapping) and isinstance(body.get("error"), Mapping):
        return str(body["error"].get("message", ""))[:300]
    return str(body)[:300]


def media_type(data: bytes) -> str:
    """The image type of ``data`` from its first bytes; ``ValueError`` when it is not PNG, JPEG, GIF or WebP."""
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError("an image is not PNG, JPEG, GIF or WebP")


def _image_block(data: bytes) -> dict[str, Any]:
    encoded = base64.b64encode(data).decode("ascii")
    return {"type": "image", "source": {"type": "base64", "media_type": media_type(data), "data": encoded}}


def _http_unreadable(code: int, detail: str) -> ports.Unreadable:
    if code in (404, 410):
        return ports.Unreadable("gone", detail)
    if code in (401, 403):
        return ports.Unreadable("login", detail)
    if code == 402:
        return ports.Unreadable("paywall", detail)
    return ports.Unreadable("error", detail)


class OmpHost:
    """The read, call and quota ports and the host facts, all through ``omp``."""

    name = "omp"

    def __init__(self, github_api: str = GITHUB_API) -> None:
        self.github_api = github_api.rstrip("/")
        self._roles: dict[str, str] | None = None
        self._models: list[Mapping[str, Any]] | None = None

    # process plumbing
    def _run(self, args: Sequence[str], timeout: int, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["omp", *args],
            input=stdin,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    def _gateway(self, path: str, body: Mapping[str, Any] | None, timeout: int) -> tuple[int, Any]:
        """One request through ``omp auth-gateway stdio``: (status, response body)."""
        request: dict[str, Any] = {"id": 1, "path": path}
        if body is not None:
            request["body"] = body
        try:
            proc = self._run(["auth-gateway", "stdio"], timeout, json.dumps(request) + "\n")
        except OSError as err:
            raise ports.CallFailed(None, f"omp cannot be started: {err.strerror}") from None
        except subprocess.TimeoutExpired:
            raise ports.CallFailed(None, f"the omp gateway gave no answer within {timeout} s") from None
        for line in proc.stdout.splitlines():
            try:
                answer = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(answer, dict) and answer.get("id") == 1:
                return int(answer.get("status", 0)), answer.get("body")
        tail = proc.stderr.strip().splitlines()[-1:] or [f"exit {proc.returncode}"]
        raise ports.CallFailed(None, f"the omp gateway gave no answer: {tail[0][:300]}")

    def _models_list(self) -> list[Mapping[str, Any]]:
        if self._models is None:
            status, body = self._gateway("/v1/models", None, GATEWAY_TIMEOUT_S)
            if status != 200 or not isinstance(body, Mapping) or not isinstance(body.get("data"), list):
                raise ports.CallFailed(status, f"the model list could not be read: {_status_detail(body)}")
            self._models = [row for row in body["data"] if isinstance(row, Mapping)]
        return self._models

    # read port
    def read(self, link: str, scope: ports.Scope = None) -> ports.Page | ports.Unreadable:
        if scope not in (None, TRANSCRIPT):
            raise ValueError("this Atlas build reads whole pages or transcripts only")
        try:
            proc = self._run(["read", link], READ_TIMEOUT_S)
        except OSError as err:
            return ports.Unreadable("no_reader", f"omp cannot be started: {err.strerror}")
        except subprocess.TimeoutExpired:
            return ports.Unreadable("error", f"omp read gave no page within {READ_TIMEOUT_S} s")
        if proc.returncode != 0:
            tail = proc.stderr.strip().splitlines()[-1:] or [f"exit {proc.returncode}"]
            return ports.Unreadable("error", tail[0][:300])
        header, body = _split_header(proc.stdout)
        if "Method" not in header:
            return ports.Unreadable("error", "omp read gave no page header")
        trouble = _unreadable(header)
        if trouble is not None:
            return trouble
        final_link = header.get("URL") or link
        method = header["Method"]
        fields, body = _front_matter(body)
        title = fields.get("title") or None
        author = fields.get("author") or None
        published = fields.get("article:published_time") or fields.get("published") or None
        publisher = None
        items: tuple[ports.RepoItem, ...] = ()
        if method.startswith("github") or method.startswith("x-"):
            body = "\n".join(line for line in body.split("\n") if not COUNTER.match(line.strip()))
        repo = github_repo(final_link)
        if repo is None and method == "github-repo":
            parts = urllib.parse.urlsplit(final_link).path.strip("/").split("/")
            repo = (parts[0], parts[1]) if len(parts) >= 2 else None
        if repo is not None:
            owner, name = repo
            publisher = "GitHub"
            author, title = owner, f"{owner}/{name}"
            listed = self._repo_items(owner, name)
            if isinstance(listed, ports.Unreadable):
                return listed
            items = listed
        elif method == "x-search":
            publisher = "X"
            body, handle, published = _x_thread(body)
            author = f"@{handle}" if handle else None
        text = body.strip("\n")
        if not text.strip():
            return ports.Unreadable("error", header.get("Notes") or "the page has no text")
        if scope == TRANSCRIPT:
            transcript = _transcript(text)
            if transcript is None:
                return ports.Unreadable("no_transcript", f"{final_link} has no transcript")
            text = transcript
        images, links = _references(text, final_link)
        if method == "image" and not images:
            images = (final_link,)
        counts = ports.Counts(words=len(text.split()), links=len(links), images=len(images))
        return ports.Page(
            final_link=final_link,
            title=title,
            author=author,
            publisher=publisher,
            published=published,
            kind_hint=_kind_hint(method, header.get("Content-Type", ""), final_link),
            text=text,
            images=images,
            links=links,
            counts=counts,
            items=items,
        )

    def _repo_items(self, owner: str, repo: str) -> tuple[ports.RepoItem, ...] | ports.Unreadable:
        """The repo's sub-items from GitHub's tree API, or why the file list could not be read."""
        url = f"{self.github_api}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        request = urllib.request.Request(
            url, headers={"Accept": "application/vnd.github+json", "User-Agent": "atlas"}
        )
        why = f"GitHub's file list for {owner}/{repo} could not be read"
        try:
            with urllib.request.urlopen(request, timeout=GITHUB_TIMEOUT_S) as response:
                listing = json.load(response)
        except urllib.error.HTTPError as err:
            return ports.Unreadable("error", f"{why}: HTTP {err.code}")
        except (OSError, http.client.HTTPException, json.JSONDecodeError) as err:
            return ports.Unreadable("error", f"{why}: {getattr(err, 'reason', err)}")
        tree = listing.get("tree") if isinstance(listing, Mapping) else None
        if not isinstance(tree, list):
            return ports.Unreadable("error", f"{why}: the reply has no tree")
        return repo_items(tree, owner, repo)

    def image(self, link: str) -> bytes | ports.Unreadable:
        request = urllib.request.Request(link, headers={"User-Agent": "atlas"})
        try:
            with urllib.request.urlopen(request, timeout=IMAGE_TIMEOUT_S) as response:
                data = response.read(IMAGE_MAX_BYTES + 1)
        except urllib.error.HTTPError as err:
            return _http_unreadable(err.code, f"the image could not be fetched (HTTP {err.code})")
        except (OSError, ValueError, http.client.HTTPException) as err:
            return ports.Unreadable("error", f"the image could not be fetched: {getattr(err, 'reason', err)}")
        if len(data) > IMAGE_MAX_BYTES:
            return ports.Unreadable("error", f"the image is larger than {IMAGE_MAX_BYTES // (1024 * 1024)} MB")
        try:
            media_type(data)
        except ValueError as err:
            return ports.Unreadable("error", str(err))
        return data

    # call port
    def call(
        self,
        role: str,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
        tool_choice: str | None,
        max_output: int,
        images: Sequence[bytes] = (),
    ) -> ports.Reply:
        selector = self.roles().get(role)
        if selector is None:
            raise ports.RoleMissing(role)
        system = [m["content"] for m in messages if m.get("role") == "system"]
        turns = [dict(m) for m in messages if m.get("role") != "system"]
        if images:
            if not turns or turns[-1].get("role") != "user":
                raise ValueError("images go with a closing user message")
            content = turns[-1]["content"]
            blocks = [{"type": "text", "text": content}] if isinstance(content, str) else list(content)
            turns[-1]["content"] = [*(_image_block(data) for data in images), *blocks]
        body: dict[str, Any] = {"model": f"@{role}", "max_tokens": max_output, "messages": turns}
        if system:
            body["system"] = "\n\n".join(system)
        if tools:
            body["tools"] = [dict(tool) for tool in tools]
        if tool_choice is not None:
            body["tool_choice"] = {"type": "tool", "name": tool_choice}
        status, answer = self._gateway("/v1/messages", body, CALL_TIMEOUT_S)
        if status != 200 or not isinstance(answer, Mapping):
            raise ports.CallFailed(status, _status_detail(answer))
        stop = STOP_REASONS.get(str(answer.get("stop_reason")))
        if stop is None:
            raise ports.CallFailed(status, f"the reply has an unknown stop reason {answer.get('stop_reason')!r}")
        blocks = answer.get("content") if isinstance(answer.get("content"), list) else []
        text = "".join(b.get("text", "") for b in blocks if isinstance(b, Mapping) and b.get("type") == "text")
        tool_input = next(
            (b.get("input") for b in blocks if isinstance(b, Mapping) and b.get("type") == "tool_use"), None
        )
        usage = answer.get("usage") if isinstance(answer.get("usage"), Mapping) else {}
        level = selector.rpartition(":")[2] if ":" in selector else ""
        return ports.Reply(
            model=str(answer.get("model") or selector),
            thinking=level if level in THINKING_LEVELS else None,
            content=text,
            tool_input=tool_input if isinstance(tool_input, Mapping) and TOOL_PARSE_ERROR not in tool_input else None,
            stop=stop,
            usage=ports.Usage(
                input=int(usage.get("input_tokens") or 0),
                output=int(usage.get("output_tokens") or 0),
                cache_read=int(usage.get("cache_read_input_tokens") or 0),
                cache_write=int(usage.get("cache_creation_input_tokens") or 0),
            ),
            cost=ports.Cost(None, "unknown"),
        )

    # quota port
    def windows(self, providers: Sequence[str]) -> list[ports.Window]:
        status, body = self._gateway("/v1/usage", None, GATEWAY_TIMEOUT_S)
        if status != 200 or not isinstance(body, Mapping) or not isinstance(body.get("reports"), list):
            raise ports.CallFailed(status, f"usage windows could not be read: {_status_detail(body)}")
        rows: list[ports.Window] = []
        for report in body["reports"]:
            if not isinstance(report, Mapping) or report.get("provider") not in providers:
                continue
            for limit in report.get("limits") or []:
                window = limit.get("window") if isinstance(limit, Mapping) else None
                amount = limit.get("amount") if isinstance(limit, Mapping) else None
                if not isinstance(window, Mapping) or not isinstance(amount, Mapping):
                    continue
                fraction = amount.get("usedFraction")
                duration = window.get("durationMs")
                resets = window.get("resetsAt")
                if not all(isinstance(v, (int, float)) for v in (fraction, duration, resets)):
                    continue
                rows.append(
                    ports.Window(
                        provider=str(report["provider"]),
                        window_id=str(limit.get("id") or window.get("id")),
                        duration_s=int(duration // 1000),
                        used_fraction=float(fraction),
                        resets_at=datetime.fromtimestamp(resets / 1000, tz=timezone.utc).isoformat(timespec="seconds"),
                    )
                )
        return rows

    # host facts capability
    def version(self) -> str | None:
        try:
            proc = self._run(["--version"], FACT_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired):
            return None
        match = re.search(r"(\d+(?:\.\d+)+)", proc.stdout) if proc.returncode == 0 else None
        return match.group(1) if match else None

    def roles(self) -> dict[str, str]:
        if self._roles is None:
            try:
                proc = self._run(["config", "get", "modelRoles", "--json"], FACT_TIMEOUT_S)
            except (OSError, subprocess.TimeoutExpired) as err:
                raise ports.CallFailed(None, f"omp config could not be read: {err}") from None
            if proc.returncode != 0:
                tail = proc.stderr.strip().splitlines()[-1:] or [f"exit {proc.returncode}"]
                raise ports.CallFailed(None, f"omp config could not be read: {tail[0][:300]}")
            try:
                value = json.loads(proc.stdout).get("value") or {}
            except (json.JSONDecodeError, AttributeError):
                value = None
            if not isinstance(value, dict):
                raise ports.CallFailed(None, "omp config gave model roles that are not a table")
            self._roles = {str(k): str(v) for k, v in value.items()}
        return dict(self._roles)

    def role_fix(self, missing: Mapping[str, str]) -> ports.RoleFix:
        lines = ("modelRoles:", *(f"  {role}: {selector}" for role, selector in missing.items()))
        try:
            proc = self._run(["config", "path"], FACT_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired):
            return ports.RoleFix(lines, None)
        folder = proc.stdout.strip() if proc.returncode == 0 else ""
        return ports.RoleFix(lines, f"{folder}/config.yml" if folder else None)

    def role_provider(self, role: str) -> str | None:
        selector = self.roles().get(role)
        return selector.partition("/")[0] if selector and "/" in selector else None

    def role_context(self, role: str) -> int | None:
        selector = self.roles().get(role)
        if selector is None:
            return None
        base, _, level = selector.rpartition(":")
        model = base if level in THINKING_LEVELS and base else selector
        for row in self._models_list():
            if row.get("id") == model and isinstance(row.get("context_length"), int):
                return row["context_length"]
        return None
