#!/usr/bin/env python3
"""The Atlas quality tool (repo-only; never shipped, never reached through ``atlas-ask``).

  quality.py build-library [--yes] [--vault <v1 instance folder>]
  quality.py promote --from <profile> --query <id>
  quality.py promote-page --from <profile> --link <link> --old-ref <date> --old-text <file>
  quality.py run <summary|search|answers> --base <ref> [--set k=v ...] --cand <ref> [--set k=v ...] [--runs 3] [--yes]
  quality.py spot <comparison|keypoints> [--answer <item> <label>]
  quality.py report <comparison>
  quality.py marks-report --profile <name>

It compares two versions of Atlas (a git ref plus setting overrides) on the ``eval`` profile through
the summary, search and answers lanes, with the user's spot checks and paired bootstrap intervals
(spec 4.15). Without ``--yes``, ``build-library`` and ``run`` print the estimated cost and make no
read, model or judge call and write nothing. It reads a real profile only in ``promote``, ``promote-page`` and
``marks-report`` (which opens the profile's store file read-only and never migrates it) and writes only the ``eval``
profile's store, and the cache folder ``~/.cache/atlas-quality/`` for the worktrees and scratch stores of a run.

Overrides (``--set``): a profile setting (``rethink``, ``judge``, ``near_copy``, ...), ``role.<role>=<model selector>``
or ``phrasings=own`` (the search lane without the fixed phrasings). The rubric version is a property of the ref.
Exit codes: 0 done, 1 stopped or failed, 2 bad input, 3 not set up.
"""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.quality import _path, evaldb, lanes, library, marks, promote, report, spot, versions, worker  # noqa: E402

from atlas import ports  # noqa: E402
from atlas.core import config, spend  # noqa: E402

ROOT = _path.ROOT
EVAL = "eval"
RUNS = 3
COMMANDS = ("build-library", "promote", "promote-page", "run", "spot", "report", "marks-report")


class Usage(Exception):
    pass


def _flags(argv: Sequence[str], spec: dict[str, bool]) -> dict[str, Any]:
    """Parse ``--name value`` (``True`` in ``spec``: the flag takes a value) and bare ``--name`` flags; anything else is a usage error."""
    found: dict[str, Any] = {}
    items = list(argv)
    while items:
        flag = items.pop(0)
        name = flag[2:]
        if not flag.startswith("--") or name not in spec:
            raise Usage(f'unexpected "{flag}"')
        if spec[name]:
            if not items:
                raise Usage(f"{flag} needs a value")
            found[name] = items.pop(0)
        else:
            found[name] = True
    return found


def parse_run(argv: Sequence[str]) -> tuple[str, versions.Version, versions.Version, int, bool]:
    """``run <lane> --base <ref> [--set k=v ...] --cand <ref> [--set k=v ...] [--runs n] [--yes]``; a ``--set`` belongs to the version named before it."""
    if not argv or argv[0] not in evaldb.LANES:
        raise Usage(f"run takes a lane: {', '.join(evaldb.LANES)}")
    lane, items = argv[0], list(argv[1:])
    refs: dict[str, str] = {}
    overrides: dict[str, dict[str, str]] = {"base": {}, "cand": {}}
    side: str | None = None
    runs, yes = RUNS, False
    while items:
        flag = items.pop(0)
        if flag in ("--base", "--cand", "--set", "--runs"):
            if not items:
                raise Usage(f"{flag} needs a value")
            value = items.pop(0)
        if flag in ("--base", "--cand"):
            side = flag[2:]
            refs[side] = value
        elif flag == "--set":
            if side is None:
                raise Usage("--set belongs to the version named before it: put it after --base or --cand")
            try:
                key, text = worker.parse_override(value)
            except ValueError as err:
                raise Usage(str(err)) from None
            overrides[side][key] = text
        elif flag == "--runs":
            if not value.isdigit() or int(value) < 1:
                raise Usage("--runs is a whole number of 1 or more")
            runs = int(value)
        elif flag == "--yes":
            yes = True
        else:
            raise Usage(f'unexpected "{flag}"')
    if set(refs) != {"base", "cand"}:
        raise Usage("run needs --base <ref> and --cand <ref>")
    return lane, versions.Version("base", refs["base"], overrides["base"]), versions.Version("cand", refs["cand"], overrides["cand"]), runs, yes


class Tool:
    """The seams the commands run on; tests pass their own host, runner, repository and clock."""

    def __init__(
        self,
        host_factory: Callable[[str], ports.Host],
        runner: Callable[[Path, Any], dict[str, Any]],
        repo: Path,
        history_ref: str,
        now: Callable[[], datetime],
        out: TextIO,
        err: TextIO,
    ) -> None:
        self.host_factory = host_factory
        self.runner = runner
        self.repo = repo
        self.history_ref = history_ref
        self.now = now
        self.out = out
        self.err = err

    def context(self, db: Any, profile: config.Profile, host: ports.Host, dry: bool) -> lanes.Ctx:
        return lanes.Ctx(
            host=host, profile=profile, db=db, store_path=profile.store, repo=self.repo, runner=self.runner, now=self.now,
            out=self.out, err=self.err, cache=versions.cache_root(), checkout=versions.checkout, dry=dry,
        )

    def profile(self) -> config.Profile | None:
        try:
            profile = config.resolve(EVAL, None)
        except config.NotSetUp as not_set_up:
            item = not_set_up.item()
            print(f"{item['what']}; {item['fix'][0]}", file=self.err)
            return None
        if not profile.store.exists():
            print(f"the eval store {profile.store} does not exist: run build-library --yes first", file=self.err)
            return None
        return profile

    # build-library ------------------------------------------------------------------------------
    def build_library(self, argv: Sequence[str]) -> int:
        flags = _flags(argv, {"yes": False, "vault": True})
        vault = Path(flags.get("vault", library.DEFAULT_VAULT)).expanduser()
        return library.build(self.host_factory(EVAL), self.repo, self.history_ref, vault, bool(flags.get("yes")), self.out, self.err)

    # promote ------------------------------------------------------------------------------------
    def promote(self, argv: Sequence[str]) -> int:
        flags = _flags(argv, {"from": True, "query": True})
        if "from" not in flags or not str(flags.get("query", "")).isdigit():
            raise Usage("promote needs --from <profile> and --query <id>")
        profile = self.profile()
        if profile is None:
            return 3
        with evaldb.session(profile.store, dry=False) as db:
            print(f"promoted {promote.promote(db, flags['from'], int(flags['query']))}", file=self.out)
        return 0

    def promote_page(self, argv: Sequence[str]) -> int:
        flags = _flags(argv, {"from": True, "link": True, "old-ref": True, "old-text": True})
        if not {"from", "link", "old-ref", "old-text"} <= set(flags):
            raise Usage("promote-page needs --from <profile>, --link <link>, --old-ref <date> and --old-text <file>")
        profile = self.profile()
        if profile is None:
            return 3
        with evaldb.session(profile.store, dry=False) as db:
            case = promote.promote_page(db, flags["from"], flags["link"], flags["old-ref"], Path(flags["old-text"]))
            print(f"promoted {case}", file=self.out)
        return 0

    # run ----------------------------------------------------------------------------------------
    def run(self, argv: Sequence[str]) -> int:
        lane, base, cand, runs, yes = parse_run(argv)
        profile = self.profile()
        if profile is None:
            return 3
        host = self.host_factory(EVAL)
        with evaldb.session(profile.store, dry=not yes) as db:
            ctx = self.context(db, profile, host, dry=not yes)
            return self._run(ctx, lane, base, cand, runs, yes)

    def _run(self, ctx: lanes.Ctx, lane: str, base: versions.Version, cand: versions.Version, runs: int, yes: bool) -> int:
        out = self.out
        try:
            work = lanes.plan(ctx, lane)
            if not work.cases:
                raise lanes.Stop(f"the {lane} lane has no cases: build the library first")
            store = ctx.host.open_store(ctx.profile.store)
            try:
                for line in lanes.estimate_lines(ctx, lane, work.cases, runs, store):
                    print(line, file=out)
            finally:
                store.close()
            drafted: list[str] = []
            if lane == "summary":
                drafted, unreviewed = lanes.pages_needing_key_points(ctx, work.cases)
                if drafted:
                    print(f"key points: {len(drafted)} of the {lanes.PAGES} pages have none; Opus drafts them first ({lanes.KEY_POINTS_ROLE})", file=out)
                if unreviewed:
                    print(f"key points: {len(unreviewed)} pages have key points you have not reviewed; review them with `quality.py spot keypoints`", file=out)
            if not yes:
                print("no read, model or judge call was made and nothing was written; run again with --yes to run it", file=out)
                return 0
            if drafted:
                by_id = {case["id"]: case for case in work.cases}
                for case_id in drafted:
                    lanes.draft_key_points(ctx, by_id[case_id])
                print(f"drafted key points for {len(drafted)} pages; review them with `quality.py spot keypoints`, then run again", file=out)
                return 1
            if lane == "summary" and unreviewed:
                raise lanes.Stop(f"{len(unreviewed)} pages have key points you have not reviewed: `quality.py spot keypoints`")
            jev = lanes.Jev(ctx)
            return self._compare(ctx, jev, lane, base, cand, runs, work)
        except (lanes.Stop, versions.VersionError) as stop:
            print(f"stopped: {stop}", file=self.err)
            return 1

    def _compare(self, ctx: lanes.Ctx, jev: lanes.Jev, lane: str, base: versions.Version, cand: versions.Version, runs: int, work: lanes.Plan) -> int:
        comparison = f"{lane}-{self.now():%Y%m%dT%H%M%S}"
        resolved = {v.label: versions.resolve(self.repo, v.ref) for v in (base, cand)}
        ids: dict[str, list[int]] = {"base": [], "cand": []}
        try:
            self._versions(ctx, jev, lane, base, cand, runs, work, comparison, resolved, ids)
        finally:
            shutil.rmtree(ctx.cache / comparison, ignore_errors=True)
        return self._finish(ctx, lane, comparison, ids)

    def _versions(self, ctx, jev, lane, base, cand, runs, work, comparison, resolved, ids) -> None:  # type: ignore[no-untyped-def]
        with ctx.checkout(self.repo, resolved["base"], f"{comparison}-base") as base_tree, ctx.checkout(self.repo, resolved["cand"], f"{comparison}-cand") as cand_tree:
            trees = {"base": base_tree, "cand": cand_tree}
            for rep in range(1, runs + 1):
                for version in (base, cand):
                    pinned = versions.Version(version.label, resolved[version.label], version.overrides)
                    ids[version.label].append(lanes.run_version(ctx, jev, lane, pinned, trees[version.label], comparison, rep, work))
                    print(f"{version.label} run {rep} of {runs} finished", file=self.err, flush=True)

    def _finish(self, ctx: lanes.Ctx, lane: str, comparison: str, ids: dict[str, list[int]]) -> int:
        ctx.db.execute(
            "INSERT INTO comparisons (id, lane, base_runs, cand_runs, report, spot_status) VALUES (?, ?, ?, ?, NULL, 'not started')",
            (comparison, lane, json.dumps(ids["base"]), json.dumps(ids["cand"])),
        )
        sample = spot.materialize(ctx.db, comparison, lane, ids["base"], ids["cand"])
        text = report.build(ctx.db, comparison)
        ctx.db.execute("UPDATE comparisons SET report = ? WHERE id = ?", (text, comparison))
        print(text, file=self.out)
        print(f"spot check: {sample} items to label with `quality.py spot {comparison}`", file=self.out)
        return 0

    # spot and report ----------------------------------------------------------------------------
    def spot(self, argv: Sequence[str]) -> int:
        if not argv:
            raise Usage("spot needs a comparison id (or keypoints)")
        name, rest = argv[0], list(argv[1:])
        profile = self.profile()
        if profile is None:
            return 3
        with evaldb.session(profile.store, dry=False) as db:
            at = spend.stamp(self.now())
            try:
                if rest:
                    if len(rest) != 3 or rest[0] != "--answer":
                        raise Usage("spot takes --answer <item> <label>")
                    if name == spot.KEY_POINTS:
                        spot.answer_key_points(db, rest[1], rest[2], at)
                        print(json.dumps({"comparison": name, "recorded": rest[1]}), file=self.out)
                    else:
                        status = spot.answer(db, name, rest[1], rest[2], at)
                        print(json.dumps({"comparison": name, "recorded": rest[1], "status": status}), file=self.out)
                    return 0
                if name == spot.KEY_POINTS:
                    print(json.dumps(spot.next_key_points(db), ensure_ascii=False), file=self.out)
                elif db.execute("SELECT 1 FROM comparisons WHERE id = ?", (name,)).fetchone() is None:
                    raise Usage(f"no comparison {name}")
                else:
                    print(json.dumps(spot.next_item(db, name), ensure_ascii=False), file=self.out)
            except ValueError as err:
                raise Usage(str(err)) from None
        return 0

    def report(self, argv: Sequence[str]) -> int:
        if len(argv) != 1:
            raise Usage("report needs a comparison id")
        profile = self.profile()
        if profile is None:
            return 3
        with evaldb.session(profile.store, dry=False) as db:
            try:
                text = report.build(db, argv[0])
            except ValueError as err:
                raise Usage(str(err)) from None
            db.execute("UPDATE comparisons SET report = ? WHERE id = ?", (text, argv[0]))
            print(text, file=self.out)
        return 0

    def marks_report(self, argv: Sequence[str]) -> int:
        flags = _flags(argv, {"profile": True})
        if "profile" not in flags:
            raise Usage("marks-report needs --profile <name>")
        try:
            profile = config.resolve(flags["profile"], None)
        except config.NotSetUp as not_set_up:
            item = not_set_up.item()
            print(f"{item['what']}; {item['fix'][0]}", file=self.err)
            return 3
        if not profile.store.exists():
            print(f"the store {profile.store} does not exist", file=self.err)
            return 1
        try:
            found = marks.rows(profile.store)
        except marks.MarksError as stop:
            print(f"stopped: {stop}", file=self.err)
            return 1
        print(marks.HEADER, file=self.out)
        for row in found:
            print(row, file=self.out)
        return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    host_factory: Callable[[str], ports.Host] | None = None,
    runner: Callable[[Path, Any], dict[str, Any]] | None = None,
    repo: Path = ROOT,
    history_ref: str = library.HISTORY_REF,
    now: Callable[[], datetime] = datetime.now,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    out, err = out or sys.stdout, err or sys.stderr
    if host_factory is None:
        from atlas import host as atlas_host

        host_factory = atlas_host.build
    tool = Tool(host_factory, runner or versions.subprocess_runner, repo, history_ref, now, out, err)
    if not args or args[0] not in COMMANDS:
        print(f"usage: quality.py <{'|'.join(COMMANDS)}> ...", file=err)
        return 2
    command = {
        "build-library": tool.build_library,
        "promote": tool.promote,
        "promote-page": tool.promote_page,
        "run": tool.run,
        "spot": tool.spot,
        "report": tool.report,
        "marks-report": tool.marks_report,
    }[args[0]]
    try:
        return command(args[1:])
    except Usage as err_usage:
        print(f"{args[0]}: {err_usage}", file=err)
        return 2
    except (promote.PromoteError, library.Stop) as stop:
        print(f"stopped: {stop}", file=err)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
