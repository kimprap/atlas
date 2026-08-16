#!/usr/bin/env python3
"""Inspect, create, sync, and check Atlas framework instances.

Product-owned files are authored only in the app package and copied into
instances. Seed-once files are empty-state templates and are never overwritten
by sync-framework. This separate administration CLI does not bind the Atlas
façade or deploy the app.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path, PureWindowsPath
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import atlas_cli  # noqa: E402
from atlas_state import audit_instance  # noqa: E402


APP_ROOT = SCRIPT_DIR.parent
SCAFFOLD_DIR = APP_ROOT / "scaffold"
MANIFEST_PATH = SCAFFOLD_DIR / "MANIFEST.json"
DEFAULT_INSTANCES_ROOT = APP_ROOT.parent / "vault" / "instances"
MANIFEST_LOGICAL_PATH = "scaffold/MANIFEST.json"
COMMAND_OPERATIONS = {
    "inspect-framework": "instance.inspect-framework",
    "create": "instance.create",
    "sync-framework": "instance.sync-framework",
    "check": "instance.check",
}


class InstanceCliError(Exception):
    """Expected machine-safe instance administration failure."""

    def __init__(
        self,
        code: str,
        path: str,
        detail: str,
        *,
        disposition: str = "rejected",
    ) -> None:
        super().__init__(detail)
        self.code = code
        self.path = path
        self.detail = detail
        self.disposition = disposition

    def finding(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "detail": self.detail}


class CliArgumentError(ValueError):
    """Argparse rejected machine command arguments."""


class MachineArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliArgumentError(message)


def finding(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def manifest_relative_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_INVALID",
            MANIFEST_LOGICAL_PATH,
            f"{label} must be a non-empty relative path",
        )
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if (
        path == Path(".")
        or path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.root)
        or bool(windows_path.drive)
        or "\\" in value
        or ".." in path.parts
    ):
        raise InstanceCliError(
            "FRAMEWORK_SOURCE_OUTSIDE_ROOT"
            if label.endswith(".source") or label.startswith("seed_once[")
            else "FRAMEWORK_DESTINATION_OUTSIDE_ROOT",
            MANIFEST_LOGICAL_PATH,
            f"{label} must stay within its owning root",
        )
    return path


def _destination_parts(path: Path) -> tuple[str, ...]:
    return tuple(part.casefold() for part in path.parts)


def _validate_destination_collisions(
    destinations: list[tuple[str, Path]],
) -> None:
    prior: list[tuple[str, Path, tuple[str, ...]]] = []
    for label, path in destinations:
        parts = _destination_parts(path)
        for other_label, other_path, other_parts in prior:
            if parts == other_parts:
                code = (
                    "FRAMEWORK_DESTINATION_DUPLICATE"
                    if path.parts == other_path.parts
                    else "FRAMEWORK_DESTINATION_COLLISION"
                )
                raise InstanceCliError(
                    code,
                    path.as_posix(),
                    f"{label} collides with {other_label}",
                )
            if (
                len(parts) < len(other_parts) and other_parts[: len(parts)] == parts
            ) or (
                len(other_parts) < len(parts)
                and parts[: len(other_parts)] == other_parts
            ):
                raise InstanceCliError(
                    "FRAMEWORK_DESTINATION_COLLISION",
                    path.as_posix(),
                    f"{label} collides with {other_label}",
                )
        prior.append((label, path, parts))


def _validated_manifest(data: object) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_INVALID",
            MANIFEST_LOGICAL_PATH,
            "manifest root must be an object",
        )
    if data.get("schema_version") != 1:
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_INVALID",
            MANIFEST_LOGICAL_PATH,
            "schema_version must be 1",
        )

    product_owned = data.get("product_owned")
    seed_once = data.get("seed_once")
    if not isinstance(product_owned, list) or not isinstance(seed_once, list):
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_INVALID",
            MANIFEST_LOGICAL_PATH,
            "manifest must define product_owned and seed_once lists",
        )
    never_touch = data.get("never_touch")
    if never_touch is not None and (
        not isinstance(never_touch, list)
        or any(not isinstance(item, str) or not item for item in never_touch)
    ):
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_INVALID",
            MANIFEST_LOGICAL_PATH,
            "never_touch must be a list of non-empty paths when present",
        )

    normalized_owned: list[dict[str, str]] = []
    normalized_seeds: list[str] = []
    destinations: list[tuple[str, Path]] = []

    for index, entry in enumerate(product_owned):
        label = f"product_owned[{index}]"
        if not isinstance(entry, dict):
            raise InstanceCliError(
                "FRAMEWORK_MANIFEST_INVALID",
                MANIFEST_LOGICAL_PATH,
                f"{label} must be an object",
            )
        source_rel = manifest_relative_path(entry.get("source"), f"{label}.source")
        dest_rel = manifest_relative_path(entry.get("dest"), f"{label}.dest")
        source = APP_ROOT / source_rel
        if not source.is_file():
            raise InstanceCliError(
                "FRAMEWORK_SOURCE_MISSING",
                source_rel.as_posix(),
                f"declared {label}.source is not a file",
                disposition="unavailable",
            )
        normalized_owned.append(
            {"source": source_rel.as_posix(), "dest": dest_rel.as_posix()}
        )
        destinations.append((f"{label}.dest", dest_rel))

    for index, value in enumerate(seed_once):
        label = f"seed_once[{index}]"
        source_rel = manifest_relative_path(value, label)
        source = SCAFFOLD_DIR / source_rel
        if not source.is_file():
            raise InstanceCliError(
                "FRAMEWORK_SOURCE_MISSING",
                f"scaffold/{source_rel.as_posix()}",
                f"declared {label} template is not a file",
                disposition="unavailable",
            )
        normalized_seeds.append(source_rel.as_posix())
        destinations.append((label, source_rel))

    _validate_destination_collisions(destinations)
    return {
        "schema_version": 1,
        "product_owned": normalized_owned,
        "seed_once": normalized_seeds,
    }


def inspect_framework() -> dict[str, Any]:
    """Load and validate the one framework manifest used by every operation."""
    try:
        raw = MANIFEST_PATH.read_bytes()
    except FileNotFoundError as exc:
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_MISSING",
            MANIFEST_LOGICAL_PATH,
            "framework manifest is not available",
            disposition="unavailable",
        ) from exc
    except OSError as exc:
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_UNAVAILABLE",
            MANIFEST_LOGICAL_PATH,
            "framework manifest could not be read",
            disposition="unavailable",
        ) from exc
    try:
        data = atlas_cli.decode(raw)
    except atlas_cli.JsonInputError as exc:
        raise InstanceCliError(
            "FRAMEWORK_MANIFEST_INVALID",
            MANIFEST_LOGICAL_PATH,
            "framework manifest is not strict UTF-8 JSON",
        ) from exc
    return _validated_manifest(data)


def framework_result(manifest: Mapping[str, Any]) -> dict[str, Any]:
    product_owned = [dict(entry) for entry in manifest["product_owned"]]
    seed_once = list(manifest["seed_once"])
    return {
        "manifest": MANIFEST_LOGICAL_PATH,
        "schema_version": manifest["schema_version"],
        "files": {
            "product_owned": product_owned,
            "seed_once": seed_once,
        },
        "counts": {
            "product_owned": len(product_owned),
            "seed_once": len(seed_once),
            "total": len(product_owned) + len(seed_once),
        },
    }


def resolve_instances_root(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_INSTANCES_ROOT.resolve()


def instance_dir(instances_root: Path, name: str) -> Path:
    if not name or name in {".", ".."} or "/" in name or "\\" in name or "\x00" in name:
        raise InstanceCliError(
            "INSTANCE_NAME_INVALID",
            "name",
            "instance name must be one non-empty directory name",
        )
    return instances_root / name


def list_instance_names(instances_root: Path) -> list[str]:
    if not instances_root.is_dir():
        return []
    return sorted(
        path.name
        for path in instances_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def write_product_owned(manifest: Mapping[str, Any], dest_root: Path) -> list[str]:
    written: list[str] = []
    for entry in manifest["product_owned"]:
        source = APP_ROOT / entry["source"]
        dest = dest_root / entry["dest"]
        copy_file(source, dest)
        written.append(entry["dest"])
    return written


def write_seed_once(manifest: Mapping[str, Any], dest_root: Path) -> list[str]:
    written: list[str] = []
    for relative in manifest["seed_once"]:
        source = SCAFFOLD_DIR / relative
        dest = dest_root / relative
        copy_file(source, dest)
        written.append(relative)
    return written


def file_matches(a: Path, b: Path) -> bool:
    if not a.is_file() or not b.is_file():
        return False
    return a.read_bytes() == b.read_bytes()


def _product_comparison(
    manifest: Mapping[str, Any], dest_root: Path
) -> dict[str, list[str]]:
    changed: list[str] = []
    unchanged: list[str] = []
    for entry in manifest["product_owned"]:
        bucket = (
            unchanged
            if file_matches(APP_ROOT / entry["source"], dest_root / entry["dest"])
            else changed
        )
        bucket.append(entry["dest"])
    return {"changed": changed, "unchanged": unchanged}


def _select_instance_names(
    args: argparse.Namespace,
    *,
    default_all: bool,
) -> list[str]:
    name = getattr(args, "name", None)
    all_instances = bool(getattr(args, "all", False))
    if name and all_instances:
        raise InstanceCliError(
            "INSTANCE_SELECTOR_CONFLICT",
            "selector",
            "--name and --all are mutually exclusive",
        )
    instances_root = resolve_instances_root(args.instances_root)
    if name:
        instance_dir(instances_root, name)
        return [name]
    if all_instances or default_all:
        return list_instance_names(instances_root)
    raise InstanceCliError(
        "INSTANCE_SELECTOR_REQUIRED",
        "selector",
        "pass exactly one of --name or --all",
    )


def cmd_inspect_framework(args: argparse.Namespace) -> dict[str, Any]:
    del args
    manifest = inspect_framework()
    return atlas_cli.response(
        "instance.inspect-framework",
        "no-write",
        result=framework_result(manifest),
    )


def cmd_create(args: argparse.Namespace) -> dict[str, Any]:
    manifest = inspect_framework()
    instances_root = resolve_instances_root(args.instances_root)
    dest = instance_dir(instances_root, args.name)
    if dest.exists():
        raise InstanceCliError(
            "INSTANCE_ALREADY_EXISTS",
            f"instance/{args.name}",
            "instance already exists",
        )

    inventory = framework_result(manifest)
    result = {
        "instance": args.name,
        "dry_run": bool(args.dry_run),
        "framework": inventory,
        "product_owned": {
            "changed": [entry["dest"] for entry in manifest["product_owned"]],
            "unchanged": [],
        },
    }
    if args.dry_run:
        return atlas_cli.response("instance.create", "no-write", result=result)

    try:
        dest.mkdir(parents=True, exist_ok=False)
        try:
            write_seed_once(manifest, dest)
            write_product_owned(manifest, dest)
        except BaseException:
            shutil.rmtree(dest, ignore_errors=True)
            raise
    except OSError as exc:
        raise InstanceCliError(
            "INSTANCE_CREATE_IO_FAILURE",
            f"instance/{args.name}",
            "instance creation failed and the new directory was removed",
            disposition="unavailable",
        ) from exc
    return atlas_cli.response("instance.create", "completed", result=result)


def cmd_sync_framework(args: argparse.Namespace) -> dict[str, Any]:
    manifest = inspect_framework()
    names = _select_instance_names(args, default_all=False)
    if not names:
        raise InstanceCliError(
            "INSTANCE_NOT_FOUND",
            "instances",
            "no instances match the selector",
        )
    instances_root = resolve_instances_root(args.instances_root)
    targets = [(name, instance_dir(instances_root, name)) for name in names]
    for name, dest in targets:
        if not dest.is_dir():
            raise InstanceCliError(
                "INSTANCE_NOT_FOUND",
                f"instance/{name}",
                "instance directory is missing",
            )

    comparisons = [
        {"instance": name, **_product_comparison(manifest, dest)}
        for name, dest in targets
    ]
    result = {
        "dry_run": bool(args.dry_run),
        "framework": framework_result(manifest),
        "instances": comparisons,
        "counts": {
            "instances": len(comparisons),
            "product_owned_per_instance": len(manifest["product_owned"]),
            "changed": sum(len(item["changed"]) for item in comparisons),
            "unchanged": sum(len(item["unchanged"]) for item in comparisons),
        },
    }
    if args.dry_run:
        return atlas_cli.response(
            "instance.sync-framework",
            "no-write",
            result=result,
        )

    try:
        for _, dest in targets:
            write_product_owned(manifest, dest)
    except OSError as exc:
        raise InstanceCliError(
            "INSTANCE_SYNC_IO_FAILURE",
            "instances",
            "framework sync stopped after an I/O failure; inspect and check the selected instances",
            disposition="manual-intervention",
        ) from exc
    return atlas_cli.response(
        "instance.sync-framework",
        "completed",
        result=result,
    )


def _check_result(manifest: Mapping[str, Any], names: list[str]) -> dict[str, Any]:
    return {
        "framework": framework_result(manifest),
        "instances": names,
        "counts": {
            "instances": len(names),
            "product_owned_per_instance": len(manifest["product_owned"]),
            "seed_once_per_instance": len(manifest["seed_once"]),
        },
    }


def cmd_check(args: argparse.Namespace) -> dict[str, Any]:
    manifest = inspect_framework()
    names = _select_instance_names(args, default_all=True)
    instances_root = resolve_instances_root(args.instances_root)
    findings: list[dict[str, str]] = []

    for entry in manifest["product_owned"]:
        leaked = SCAFFOLD_DIR / entry["dest"]
        if leaked.is_file():
            findings.append(
                finding(
                    "FRAMEWORK_PRODUCT_BODY_IN_SCAFFOLD",
                    f"scaffold/{entry['dest']}",
                    f"author product_owned content at {entry['source']}",
                )
            )

    for name in names:
        dest = instance_dir(instances_root, name)
        if not dest.is_dir():
            findings.append(
                finding(
                    "INSTANCE_NOT_FOUND",
                    f"instance/{name}",
                    "instance directory is missing",
                )
            )
            continue
        for entry in manifest["product_owned"]:
            source = APP_ROOT / entry["source"]
            instance_path = dest / entry["dest"]
            logical_path = f"instance/{name}/{entry['dest']}"
            if not instance_path.is_file():
                findings.append(
                    finding(
                        "INSTANCE_PRODUCT_OWNED_MISSING",
                        logical_path,
                        "product_owned file is missing",
                    )
                )
            elif not file_matches(source, instance_path):
                findings.append(
                    finding(
                        "INSTANCE_PRODUCT_OWNED_DRIFT",
                        logical_path,
                        f"run sync-framework --name {name}",
                    )
                )
        for relative in manifest["seed_once"]:
            if not (dest / relative).is_file():
                findings.append(
                    finding(
                        "INSTANCE_SEED_PATH_MISSING",
                        f"instance/{name}/{relative}",
                        "seed_once structure path is missing",
                    )
                )
        for item in audit_instance(dest):
            detail_parts = []
            if item.line is not None:
                detail_parts.append(f"line {item.line}")
            if item.row:
                detail_parts.append(f"row {item.row}")
            if item.detail:
                detail_parts.append(item.detail)
            findings.append(
                finding(
                    item.code,
                    f"instance/{name}/{item.path}",
                    "; ".join(detail_parts) or "living registry validation failed",
                )
            )

    result = _check_result(manifest, names)
    if findings:
        return atlas_cli.response(
            "instance.check",
            "rejected",
            result=result,
            findings=findings,
        )
    return atlas_cli.response("instance.check", "no-write", result=result)


def build_parser() -> argparse.ArgumentParser:
    parser = MachineArgumentParser(
        prog="atlas-instance",
        description="Inspect, provision, sync, and check Atlas framework instances.",
    )
    parser.add_argument(
        "--instances-root",
        default=None,
        help=f"Instance parent directory (default: {DEFAULT_INSTANCES_ROOT})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_parser = sub.add_parser(
        "inspect-framework",
        help="Validate and inventory the product framework manifest",
    )
    inspect_parser.set_defaults(func=cmd_inspect_framework)

    create_parser = sub.add_parser(
        "create",
        help="Create a new empty instance from the scaffold",
    )
    create_parser.add_argument("--name", required=True, help="Instance id")
    create_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report the create without writing",
    )
    create_parser.set_defaults(func=cmd_create)

    sync_parser = sub.add_parser(
        "sync-framework",
        help="Overwrite product_owned files from app sources",
    )
    sync_group = sync_parser.add_mutually_exclusive_group(required=True)
    sync_group.add_argument("--name", help="Single instance id")
    sync_group.add_argument(
        "--all",
        action="store_true",
        help="All instances under instances-root",
    )
    sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and compare without writing",
    )
    sync_parser.set_defaults(func=cmd_sync_framework)

    check_parser = sub.add_parser(
        "check",
        help="Check framework alignment, scaffold integrity, and living registries",
    )
    check_group = check_parser.add_mutually_exclusive_group()
    check_group.add_argument("--name", help="Single instance id")
    check_group.add_argument(
        "--all",
        action="store_true",
        help="All instances (the default when --name is omitted)",
    )
    check_parser.set_defaults(func=cmd_check)
    return parser


def _operation_from_argv(argv: list[str]) -> str | None:
    index = 0
    while index < len(argv):
        token = argv[index]
        if token == "--instances-root":
            index += 2
            continue
        if token.startswith("--instances-root="):
            index += 1
            continue
        if token in COMMAND_OPERATIONS:
            return COMMAND_OPERATIONS[token]
        if not token.startswith("-"):
            return None
        index += 1
    return None


def _argument_finding(message: str) -> dict[str, str]:
    if "--name" in message and "--all" in message:
        return finding(
            "INSTANCE_SELECTOR_CONFLICT",
            "selector",
            "--name and --all are mutually exclusive",
        )
    return finding(
        "INSTANCE_ARGUMENT_INVALID",
        "arguments",
        "instance command arguments are invalid",
    )


def run(argv: list[str] | None = None) -> dict[str, Any]:
    values = list(sys.argv[1:] if argv is None else argv)
    op = _operation_from_argv(values)
    try:
        args = build_parser().parse_args(values)
    except CliArgumentError as exc:
        return atlas_cli.response(
            op,
            "rejected",
            findings=[_argument_finding(str(exc))],
        )

    op = COMMAND_OPERATIONS[args.command]
    try:
        return args.func(args)
    except InstanceCliError as exc:
        return atlas_cli.response(
            op,
            exc.disposition,
            findings=[exc.finding()],
        )
    except OSError:
        return atlas_cli.response(
            op,
            "unavailable",
            findings=[
                finding(
                    "INSTANCE_IO_UNAVAILABLE",
                    "instance",
                    "instance administration I/O is unavailable",
                )
            ],
        )
    except BaseException:
        return atlas_cli.response(
            op,
            "internal-error",
            findings=[
                finding(
                    "INSTANCE_INTERNAL_ERROR",
                    "instance",
                    "instance administration failed unexpectedly",
                )
            ],
        )


def main(argv: list[str] | None = None) -> int:
    return atlas_cli.emit(run(argv))


if __name__ == "__main__":
    sys.exit(main())
