from __future__ import annotations

import contextlib
import dataclasses
import fcntl
import hashlib
import json
import os
import re
import secrets
import stat
import tempfile
import threading
from pathlib import Path
from typing import Iterator
from urllib.parse import unquote_to_bytes, urlsplit


ROOT_URI = "vault://atlas/"
_REVISION = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_BAD_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_SCALAR = re.compile(r"[A-Za-z0-9._/@+-][A-Za-z0-9._/@+\-/]*\Z")


@dataclasses.dataclass(frozen=True)
class LocalProfile:
    profile: str
    instance: str
    connector: str
    root: Path


@dataclasses.dataclass
class _Lock:
    gate: threading.RLock
    depth: int = 0
    fd: int | None = None


_LOCKS: dict[str, _Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _scalar(value: str, line: int) -> str:
    if (
        not value
        or value != value.strip()
        or value[0] in "[{-&*!|>"
        or value.startswith("<<")
    ):
        raise ValueError(f"profile line {line} has an ambiguous scalar")
    if value[0] in "'\"":
        if len(value) < 2 or value[-1] != value[0]:
            raise ValueError(f"profile line {line} has an unterminated scalar")
        if value[0] == "'":
            value = value[1:-1].replace("''", "'")
        else:
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"profile line {line} has an invalid scalar") from exc
        if not isinstance(value, str) or not value:
            raise ValueError(f"profile line {line} must be a string")
        return value
    if (
        not _SCALAR.fullmatch(value)
        or value.lower() in {"true", "false", "null", "~"}
        or re.fullmatch(r"[-+]?(?:\d+|\d+\.\d+)", value)
    ):
        raise ValueError(f"profile line {line} has an invalid scalar")
    return value


def _parse_profile(text: str) -> dict[str, object]:
    values: dict[str, object] = {}
    local: dict[str, str] = {}
    under_local = False
    for line, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw or raw.rstrip() != raw:
            raise ValueError(f"profile line {line} has invalid indentation")
        indent = len(raw) - len(raw.lstrip(" "))
        body = raw[indent:]
        if ":" not in body:
            raise ValueError(f"profile line {line} is not a mapping entry")
        key, value = body.split(":", 1)
        if not re.fullmatch(r"[a-z_]+", key):
            raise ValueError(f"profile line {line} has an invalid key")
        if indent == 0:
            under_local = key == "local_fs"
            if key in values:
                raise ValueError(f"profile line {line} duplicates {key}")
            if key == "local_fs":
                if value:
                    raise ValueError("profile local_fs must be a mapping")
                values[key] = local
            elif key in {"profile", "instance", "connector"}:
                if not value.startswith(" ") or value.startswith("  "):
                    raise ValueError(
                        f"profile line {line} must use one scalar separator"
                    )
                values[key] = _scalar(value[1:], line)
            else:
                raise ValueError(f"profile line {line} has unknown key {key}")
        elif indent == 2 and under_local and key == "root":
            if key in local:
                raise ValueError(f"profile line {line} duplicates local_fs.root")
            if not value.startswith(" ") or value.startswith("  "):
                raise ValueError(f"profile line {line} must use one scalar separator")
            local[key] = _scalar(value[1:], line)
        else:
            raise ValueError(f"profile line {line} has an invalid nested mapping")
    if set(values) != {"profile", "instance", "connector", "local_fs"} or set(
        local
    ) != {"root"}:
        raise ValueError(
            "profile must contain exactly profile, instance, connector, and local_fs.root"
        )
    return values


def resolve_profile(profile_path: Path | str | None = None) -> LocalProfile:
    selected = os.environ.get("ATLAS_VAULT_PROFILE") if profile_path is None else None
    source = (
        Path(selected)
        if selected
        else Path(profile_path)
        if profile_path is not None
        else Path.cwd().parent / "vault/config/profiles/local.yml"
    )
    source = source.expanduser().absolute()
    try:
        info = os.lstat(source)
    except OSError as exc:
        raise ValueError("profile is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ValueError("profile must be a regular file")
    try:
        values = _parse_profile(source.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("profile must be UTF-8") from exc
    profiles = source.parent
    if profiles.name != "profiles" or profiles.parent.name != "config":
        raise ValueError("profile must be under config/profiles")
    local_values = values["local_fs"]
    if not isinstance(local_values, dict) or not isinstance(
        local_values.get("root"), str
    ):
        raise ValueError("profile local_fs.root must be a string")
    root = Path(local_values["root"])
    if not root.is_absolute():
        root = profiles.parent.parent / root
    root = root.absolute()
    try:
        info = os.lstat(root)
    except OSError as exc:
        raise ValueError("profile local_fs.root is unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ValueError("profile local_fs.root must be a directory")
    return LocalProfile(
        str(values["profile"]),
        str(values["instance"]),
        str(values["connector"]),
        root.resolve(),
    )


class LocalFilesystemConnector:
    def __init__(self, profile: LocalProfile) -> None:
        if not isinstance(profile, LocalProfile):
            raise TypeError("LocalFilesystemConnector requires a LocalProfile")
        self._profile, self._root = profile, profile.root
        self._lock_key = hashlib.sha256(str(self._root).encode()).hexdigest()
        self._mutable = (
            profile.connector == "local-fs"
            and hasattr(os, "O_NOFOLLOW")
            and hasattr(os, "O_DIRECTORY")
        )
        if self._mutable:
            try:
                fd = self._root_fd()
            except OSError:
                self._mutable = False
            else:
                os.close(fd)

    def capabilities(self) -> dict[str, object]:
        operations = [
            "digest_tree",
            "list",
            "read_bytes",
            "read_json",
            "read_text",
            "revision",
        ]
        if self._mutable:
            operations += ["conditional_replace", "delete_tree", "write_json"]
        return {
            "adapter": "atlas-local-fs-cas-v1",
            "root": ROOT_URI,
            "logical_root": ROOT_URI,
            "conditional_replace": "available" if self._mutable else "unavailable",
            "operations": sorted(operations),
        }

    def _parts(self, uri: str) -> tuple[str, ...]:
        if not isinstance(uri, str) or _BAD_ESCAPE.search(uri):
            raise ValueError("logical URI is invalid")
        try:
            parsed = urlsplit(uri)
        except ValueError as exc:
            raise ValueError("logical URI is invalid") from exc
        if parsed.scheme != "vault" or parsed.netloc != "atlas":
            if "@" in parsed.netloc:
                raise ValueError("logical URI credentials are not allowed")
            raise ValueError("logical URI authority is not atlas")
        if parsed.query:
            raise ValueError("logical URI query is not allowed")
        if parsed.fragment:
            raise ValueError("logical URI fragment is not allowed")
        try:
            path = unquote_to_bytes(parsed.path).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("logical URI path must be UTF-8") from exc
        if not path.startswith("/") or "\\" in path or "\0" in path:
            raise ValueError("logical URI path is invalid")
        parts = tuple(part for part in path.split("/") if part)
        if any(part in {".", ".."} for part in parts):
            raise ValueError("logical URI path traversal is not allowed")
        return parts

    def _internal_parts(self, path: str) -> tuple[str, ...]:
        if path.startswith("vault://"):
            return self._parts(path)
        if (
            not path
            or path.startswith("/")
            or "?" in path
            or "#" in path
            or "\\" in path
        ):
            raise ValueError("relative path is invalid")
        parts = tuple(part for part in path.split("/") if part)
        if not parts or any(part in {".", ".."} for part in parts):
            raise ValueError("relative path traversal is not allowed")
        return parts

    @staticmethod
    def _uri(parts: tuple[str, ...]) -> str:
        return ROOT_URI if not parts else ROOT_URI + "/".join(parts)

    def _root_fd(self) -> int:
        return os.open(self._root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    @staticmethod
    def _directory(info: os.stat_result, name: str) -> None:
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"symlink is not allowed: {name}")
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError(f"special file is not allowed: {name}")

    @staticmethod
    def _regular(info: os.stat_result, name: str) -> None:
        if stat.S_ISLNK(info.st_mode):
            raise ValueError(f"symlink is not allowed: {name}")
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"special file is not allowed: {name}")

    @staticmethod
    def _stat(fd: int, name: str) -> os.stat_result:
        return os.stat(name, dir_fd=fd, follow_symlinks=False)

    @contextlib.contextmanager
    def _dir(self, parts: tuple[str, ...], create: bool = False) -> Iterator[int]:
        fd = self._root_fd()
        try:
            for part in parts:
                try:
                    info = self._stat(fd, part)
                except FileNotFoundError:
                    if not create:
                        raise
                    os.mkdir(part, 0o700, dir_fd=fd)
                    os.fsync(fd)
                    info = self._stat(fd, part)
                self._directory(info, part)
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
                os.close(fd)
                fd = child
            yield fd
        finally:
            os.close(fd)

    def _read_at(self, parent: int, name: str) -> bytes:
        self._regular(self._stat(parent, name), name)
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            with os.fdopen(fd, "rb", closefd=False) as file:
                return file.read()
        finally:
            os.close(fd)

    def _read(self, parts: tuple[str, ...]) -> bytes:
        if not parts:
            raise ValueError("logical URI must identify a file")
        with self._dir(parts[:-1]) as parent:
            return self._read_at(parent, parts[-1])

    def read_bytes(self, uri: str) -> bytes:
        return self._read(self._parts(uri))

    def read_text(self, uri: str) -> str:
        try:
            return self.read_bytes(uri).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("text is not valid UTF-8") from exc

    def read_json(self, uri: str) -> object:
        try:
            return json.loads(self.read_text(uri))
        except json.JSONDecodeError as exc:
            raise ValueError("JSON is invalid") from exc

    def revision(self, uri: str) -> str:
        try:
            data = self._read(self._parts(uri))
        except FileNotFoundError:
            return "missing"
        return "sha256:" + hashlib.sha256(data).hexdigest()

    def list(self, uri: str) -> list[str]:
        prefix, entries = self._parts(uri), []

        def walk(fd: int, parts: tuple[str, ...]) -> None:
            for name in sorted(os.listdir(fd), key=lambda item: item.encode("utf-8")):
                info, child_parts = self._stat(fd, name), parts + (name,)
                if stat.S_ISLNK(info.st_mode):
                    raise ValueError(f"symlink is not allowed: {name}")
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(
                        name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                    )
                    try:
                        walk(child, child_parts)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode):
                    entries.append(child_parts)
                else:
                    raise ValueError(f"special file is not allowed: {name}")

        with self._dir(prefix) as fd:
            walk(fd, prefix)
        return [
            self._uri(parts)
            for parts in sorted(
                entries, key=lambda parts: "/".join(parts).encode("utf-8")
            )
        ]

    def _require_mutation(self) -> None:
        if not self._mutable:
            raise ValueError("mutation_unavailable")

    @contextlib.contextmanager
    def mutation_session(self) -> Iterator[None]:
        self._require_mutation()
        with _LOCKS_GUARD:
            lock = _LOCKS.setdefault(self._lock_key, _Lock(threading.RLock()))
        lock.gate.acquire()
        entered = False
        try:
            if not lock.depth:
                location = (
                    Path(tempfile.gettempdir())
                    / "atlas-local-fs-cas-v1-locks"
                    / f"{self._lock_key}.lock"
                )
                location.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                fd = os.open(location, os.O_CREAT | os.O_RDWR, 0o600)
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX)
                except BaseException:
                    os.close(fd)
                    raise
                lock.fd = fd
            lock.depth += 1
            entered = True
            yield
        finally:
            if entered:
                lock.depth -= 1
                if not lock.depth:
                    assert lock.fd is not None
                    fcntl.flock(lock.fd, fcntl.LOCK_UN)
                    os.close(lock.fd)
                    lock.fd = None
            lock.gate.release()

    @staticmethod
    def _write(fd: int, value: bytes) -> None:
        offset = 0
        while offset < len(value):
            written = os.write(fd, value[offset:])
            if written <= 0:
                raise OSError("short write")
            offset += written

    def _atomic(self, parent: int, name: str, value: bytes) -> None:
        temporary, fd = f".{name}.atlas-{secrets.token_hex(16)}.tmp", None
        try:
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            self._write(fd, value)
            os.fsync(fd)
            os.close(fd)
            fd = None
            os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        except BaseException:
            if fd is not None:
                os.close(fd)
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
            raise

    def _replace(self, parts: tuple[str, ...], value: bytes) -> None:
        if not parts:
            raise ValueError("logical URI must identify a file")
        with self._dir(parts[:-1], create=True) as parent:
            try:
                self._regular(self._stat(parent, parts[-1]), parts[-1])
            except FileNotFoundError:
                pass
            self._atomic(parent, parts[-1], value)

    def conditional_replace(
        self, uri: str, expected_revision: str, value: bytes
    ) -> dict[str, str]:
        if (
            not isinstance(value, bytes)
            or expected_revision != "missing"
            and not _REVISION.fullmatch(expected_revision)
        ):
            raise ValueError("conditional replacement request is invalid")
        parts = self._parts(uri)
        with self.mutation_session():
            try:
                current = self._read(parts)
            except FileNotFoundError:
                current = None
            revision = (
                "missing"
                if current is None
                else "sha256:" + hashlib.sha256(current).hexdigest()
            )
            if revision != expected_revision:
                raise ValueError("revision conflict")
            if current is not None and current == value:
                acknowledged = self.revision(uri)
                if acknowledged != revision:
                    raise OSError("durable reread acknowledgement failed")
                return {
                    "status": "no_change",
                    "revision": revision,
                    "acknowledged_revision": acknowledged,
                }
            self._replace(parts, value)
            revision = "sha256:" + hashlib.sha256(value).hexdigest()
            if self.revision(uri) != revision:
                raise OSError("durable reread acknowledgement failed")
            return {
                "status": "replaced",
                "revision": revision,
                "acknowledged_revision": revision,
            }

    def write_json(self, uri: str, value: object) -> dict[str, str]:
        try:
            body = (
                json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8")
                + b"\n"
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("JSON value is not canonicalizable") from exc
        return self.conditional_replace(uri, self.revision(uri), body)

    def delete(self, path: str) -> None:
        """Internal transaction rollback primitive; not a façade capability."""
        parts = self._internal_parts(path)
        with self.mutation_session(), self._dir(parts[:-1]) as parent:
            self._regular(self._stat(parent, parts[-1]), parts[-1])
            os.unlink(parts[-1], dir_fd=parent)
            os.fsync(parent)
            if self.revision(self._uri(parts)) != "missing":
                raise OSError("durable delete acknowledgement failed")

    def _digest(self, fd: int) -> dict[str, object]:
        entries: list[tuple[bytes, bytes]] = []
        directories, files, size = 0, 0, 0

        def walk(directory: int, prefix: tuple[str, ...]) -> None:
            nonlocal directories, files, size
            for name in sorted(
                os.listdir(directory), key=lambda item: item.encode("utf-8")
            ):
                info = self._stat(directory, name)
                relative = "/".join(prefix + (name,))
                relative_bytes = relative.encode("utf-8")
                if stat.S_ISLNK(info.st_mode):
                    raise ValueError(f"symlink is not allowed: {relative}")
                if stat.S_ISDIR(info.st_mode):
                    entries.append((relative_bytes, b"D\t" + relative_bytes + b"/\n"))
                    directories += 1
                    child = os.open(
                        name,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=directory,
                    )
                    try:
                        walk(child, prefix + (name,))
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode):
                    value = self._read_at(directory, name)
                    line = (
                        f"F\t{hashlib.sha256(value).hexdigest()}\t{len(value)}\t"
                        f"{relative}\n"
                    ).encode("utf-8")
                    entries.append((relative_bytes, line))
                    files, size = files + 1, size + len(value)
                else:
                    raise ValueError(f"special file is not allowed: {relative}")

        walk(fd, ())
        entries.sort(key=lambda item: item[0])
        digest = hashlib.sha256()
        for _, line in entries:
            digest.update(line)
        return {
            "digest": "sha256:" + digest.hexdigest(),
            "directories": directories,
            "files": files,
            "bytes": size,
        }

    def digest_tree(self, uri: str) -> dict[str, object]:
        with self._dir(self._parts(uri)) as fd:
            return self._digest(fd)

    def _tombstone(self, parent: int, name: str) -> dict[str, object] | None:
        try:
            value = self._read_at(parent, name)
        except FileNotFoundError:
            return None
        try:
            data = json.loads(value.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("delete tombstone is invalid") from exc
        if not isinstance(data, dict):
            raise ValueError("delete tombstone is invalid")
        return data

    def _erase(self, parent: int, name: str) -> None:
        self._directory(self._stat(parent, name), name)
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        try:
            for child in sorted(os.listdir(fd), key=lambda item: item.encode("utf-8")):
                info = self._stat(fd, child)
                if stat.S_ISLNK(info.st_mode):
                    raise ValueError(f"symlink is not allowed: {child}")
                if stat.S_ISDIR(info.st_mode):
                    self._erase(fd, child)
                elif stat.S_ISREG(info.st_mode):
                    os.unlink(child, dir_fd=fd)
                else:
                    raise ValueError(f"special file is not allowed: {child}")
            os.fsync(fd)
        finally:
            os.close(fd)
        os.rmdir(name, dir_fd=parent)

    @staticmethod
    def _delete_result(status: str, quarantine_uri: str) -> dict[str, str]:
        return {"status": status, "quarantine_uri": quarantine_uri}

    def delete_tree(
        self,
        uri: str,
        *,
        expected_digest: str,
        projection_sha256: str,
        approval: str,
        report_revision: str,
    ) -> dict[str, str]:
        parts = self._parts(uri)
        if (
            not parts
            or not _REVISION.fullmatch(expected_digest)
            or not _SHA256.fullmatch(projection_sha256)
            or not _REVISION.fullmatch(report_revision)
        ):
            raise ValueError("delete request is invalid")
        if approval != f"DELETE_TREE {uri} {expected_digest} {projection_sha256}":
            raise ValueError("delete approval does not match request")
        request = {
            "path": uri,
            "expected_digest": expected_digest,
            "projection_sha256": projection_sha256,
            "approval": approval,
            "report_revision": report_revision,
        }
        key = hashlib.sha256(uri.encode()).hexdigest()
        tombstone, quarantine = f".atlas-delete-{key}.json", f".atlas-quarantine-{key}"
        parent_parts, target = parts[:-1], parts[-1]
        quarantine_uri = self._uri(parent_parts + (quarantine,))
        with self.mutation_session(), self._dir(parent_parts) as parent:
            prior = self._tombstone(parent, tombstone)
            if prior is not None:
                if (
                    prior.get("request") != request
                    or prior.get("quarantine") != quarantine
                ):
                    raise ValueError("resume request does not match tombstone")
                try:
                    self._directory(self._stat(parent, quarantine), quarantine)
                except FileNotFoundError:
                    try:
                        self._stat(parent, target)
                    except FileNotFoundError:
                        os.unlink(tombstone, dir_fd=parent)
                        os.fsync(parent)
                        return self._delete_result("deleted", quarantine_uri)
                else:
                    try:
                        self._erase(parent, quarantine)
                        os.fsync(parent)
                    except OSError:
                        return self._delete_result(
                            "quarantined-not-erased", quarantine_uri
                        )
                    os.unlink(tombstone, dir_fd=parent)
                    os.fsync(parent)
                    return self._delete_result("deleted", quarantine_uri)
            try:
                self._directory(self._stat(parent, target), target)
            except FileNotFoundError as exc:
                raise ValueError("tree is missing") from exc
            if self.digest_tree(uri)["digest"] != expected_digest:
                raise ValueError("tree digest mismatch")
            body = (
                json.dumps(
                    {"quarantine": quarantine, "request": request},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
                + b"\n"
            )
            self._atomic(parent, tombstone, body)
            os.rename(target, quarantine, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
            try:
                self._erase(parent, quarantine)
                os.fsync(parent)
            except OSError:
                return self._delete_result("quarantined-not-erased", quarantine_uri)
            os.unlink(tombstone, dir_fd=parent)
            os.fsync(parent)
            return self._delete_result("deleted", quarantine_uri)
