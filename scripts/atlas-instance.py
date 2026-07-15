#!/usr/bin/env python3
"""Atlas instance provision: create, sync-framework, check.

Materializes vault instance trees from the app product. Product-owned files
(e.g. .agents/ARCHITECTURE.md → instance ARCHITECTURE.md) are authored only
in the product package and copied into instances. Seed-once files are
empty-state templates under scaffold/ and are never overwritten by sync-framework.

This is not an app deploy/release pipeline.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path, PureWindowsPath


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from atlas_state import audit_instance


APP_ROOT = SCRIPT_DIR.parent
SCAFFOLD_DIR = APP_ROOT / "scaffold"
MANIFEST_PATH = SCAFFOLD_DIR / "MANIFEST.json"
DEFAULT_INSTANCES_ROOT = APP_ROOT.parent / "vault" / "instances"


def manifest_relative_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise SystemExit(f"manifest {label} must be a non-empty relative path")
    path = Path(value)
    windows_path = PureWindowsPath(value)
    if (
        path == Path(".")
        or path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.root
        or "\\" in value
        or ".." in path.parts
    ):
        raise SystemExit(f"manifest {label} must stay within its owning root: {value!r}")
    return path


def validate_manifest(data: object) -> None:
    if not isinstance(data, dict):
        raise SystemExit("manifest root must be an object")

    product_owned = data.get("product_owned")
    seed_once = data.get("seed_once")
    if not isinstance(product_owned, list) or not isinstance(seed_once, list):
        raise SystemExit("manifest must define product_owned and seed_once lists")

    for index, entry in enumerate(product_owned):
        label = f"product_owned[{index}]"
        if not isinstance(entry, dict):
            raise SystemExit(f"manifest {label} must be an object")
        source = APP_ROOT / manifest_relative_path(entry.get("source"), f"{label}.source")
        manifest_relative_path(entry.get("dest"), f"{label}.dest")
        if not source.is_file():
            raise SystemExit(f"product_owned source missing: {source}")

    for index, value in enumerate(seed_once):
        source = SCAFFOLD_DIR / manifest_relative_path(value, f"seed_once[{index}]")
        if not source.is_file():
            raise SystemExit(f"seed_once template missing: {source}")


def load_manifest() -> dict:
    if not MANIFEST_PATH.is_file():
        raise SystemExit(f"missing manifest: {MANIFEST_PATH}")
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid manifest {MANIFEST_PATH}: {exc}") from exc
    validate_manifest(data)
    return data


def resolve_instances_root(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    return DEFAULT_INSTANCES_ROOT.resolve()


def instance_dir(instances_root: Path, name: str) -> Path:
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise SystemExit(f"invalid instance name: {name!r}")
    return instances_root / name


def list_instance_names(instances_root: Path) -> list[str]:
    if not instances_root.is_dir():
        return []
    return sorted(
        p.name
        for p in instances_root.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def write_product_owned(manifest: dict, dest_root: Path) -> list[str]:
    written: list[str] = []
    for entry in manifest["product_owned"]:
        source = APP_ROOT / entry["source"]
        dest = dest_root / entry["dest"]
        if not source.is_file():
            raise SystemExit(f"product_owned source missing: {source}")
        copy_file(source, dest)
        written.append(entry["dest"])
    return written


def write_seed_once(manifest: dict, dest_root: Path) -> list[str]:
    written: list[str] = []
    for rel in manifest["seed_once"]:
        source = SCAFFOLD_DIR / rel
        dest = dest_root / rel
        if not source.is_file():
            raise SystemExit(f"seed_once template missing: {source}")
        copy_file(source, dest)
        written.append(rel)
    return written


def cmd_create(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    instances_root = resolve_instances_root(args.instances_root)
    dest = instance_dir(instances_root, args.name)

    if dest.exists():
        print(f"error: instance already exists: {dest}", file=sys.stderr)
        return 1

    dest.mkdir(parents=True, exist_ok=False)
    try:
        seeds = write_seed_once(manifest, dest)
        owned = write_product_owned(manifest, dest)
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    print(f"created instance: {dest}")
    print(f"  seed_once: {len(seeds)} file(s)")
    print(f"  product_owned: {len(owned)} file(s)")
    print("  note: point a vault profile/connector at this instance root before use")
    return 0


def iter_targets(args: argparse.Namespace) -> list[Path]:
    instances_root = resolve_instances_root(args.instances_root)
    if args.all:
        names = list_instance_names(instances_root)
        if not names:
            print(f"error: no instances under {instances_root}", file=sys.stderr)
            return []
        return [instance_dir(instances_root, n) for n in names]
    if not args.name:
        print("error: pass --name <id> or --all", file=sys.stderr)
        return []
    return [instance_dir(instances_root, args.name)]


def cmd_sync_framework(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    targets = iter_targets(args)
    if not targets:
        return 1

    errors = 0
    for dest in targets:
        if not dest.is_dir():
            print(f"error: instance missing: {dest}", file=sys.stderr)
            errors += 1
            continue
        owned = write_product_owned(manifest, dest)
        print(f"synced product_owned → {dest} ({len(owned)} file(s))")
    return 1 if errors else 0


def file_matches(a: Path, b: Path) -> bool:
    if not a.is_file() or not b.is_file():
        return False
    return a.read_bytes() == b.read_bytes()


def cmd_check(args: argparse.Namespace) -> int:
    manifest = load_manifest()
    failures: list[str] = []
    instances_root = resolve_instances_root(args.instances_root)

    # Scaffold must not hand-host product_owned bodies (author in product package).
    for entry in manifest["product_owned"]:
        leaked = SCAFFOLD_DIR / entry["dest"]
        if leaked.is_file():
            failures.append(
                f"scaffold must not contain product_owned body: {leaked} "
                f"(author at {entry['source']}; provision injects on create/sync)"
            )

    for rel in manifest["seed_once"]:
        path = SCAFFOLD_DIR / rel
        if not path.is_file():
            failures.append(f"seed_once template missing: {path}")

    for entry in manifest["product_owned"]:
        source = APP_ROOT / entry["source"]
        if not source.is_file():
            failures.append(f"product_owned source missing: {source}")

    # Default: all existing instances. Explicit --name / --all still supported.
    if args.name:
        targets = [instance_dir(instances_root, args.name)]
    else:
        names = list_instance_names(instances_root)
        targets = [instance_dir(instances_root, n) for n in names]

    for dest in targets:
        if not dest.is_dir():
            failures.append(f"instance missing: {dest}")
            continue
        for entry in manifest["product_owned"]:
            source = APP_ROOT / entry["source"]
            inst = dest / entry["dest"]
            if not inst.is_file():
                failures.append(f"instance missing product_owned: {inst}")
            elif not file_matches(source, inst):
                failures.append(
                    f"product_owned drift: {inst} != {source} "
                    f"(run: python3 scripts/atlas-instance.py sync-framework --name {dest.name})"
                )
        for rel in manifest["seed_once"]:
            # seed_once may diverge after real use; only require path existence at create time.
            # Still require that at least the seed structure paths exist for empty shells.
            # For living instances, registries exist but content may differ — do not fail.
            inst = dest / rel
            if not inst.is_file():
                failures.append(f"instance missing seed path (structure): {inst}")
        for finding in audit_instance(dest):
            anchor = f":{finding.line}" if finding.line is not None else ""
            row = f" [{finding.row}]" if finding.row else ""
            detail = f" — {finding.detail}" if finding.detail else ""
            failures.append(
                f"living registry {finding.code}: {dest / finding.path}{anchor}{row}{detail}"
            )

    if failures:
        print("check FAILED:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("check OK")
    if targets:
        print(f"  instances: {', '.join(t.name for t in targets)}")
    print(f"  product_owned entries: {len(manifest['product_owned'])}")
    print(f"  seed_once templates: {len(manifest['seed_once'])}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atlas-instance",
        description="Provision and sync Atlas vault instances from app scaffold templates.",
    )
    parser.add_argument(
        "--instances-root",
        default=None,
        help=f"Instance parent directory (default: {DEFAULT_INSTANCES_ROOT})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new empty instance from scaffold")
    p_create.add_argument("--name", required=True, help="Instance id (directory name)")
    p_create.set_defaults(func=cmd_create)

    p_sync = sub.add_parser(
        "sync-framework",
        help="Overwrite product_owned files in an instance from app sources",
    )
    g = p_sync.add_mutually_exclusive_group(required=True)
    g.add_argument("--name", help="Single instance id")
    g.add_argument("--all", action="store_true", help="All instances under instances-root")
    p_sync.set_defaults(func=cmd_sync_framework)

    p_check = sub.add_parser(
        "check",
        help="Verify product-owned alignment, scaffold integrity, and living registries",
    )
    p_check.add_argument("--name", help="Single instance id (default: all existing)")
    p_check.add_argument(
        "--all",
        action="store_true",
        help="Explicitly check all instances (same as default when --name omitted)",
    )
    p_check.set_defaults(func=cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
