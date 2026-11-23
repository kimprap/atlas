"""``build-library``: the ``eval`` test library, built once from ticket 08's graded pool (spec 4.15, ticket 13 section 2).

Reads the pool's 516 distinct v1 source ids (``grades.json``), the 47 queries and
their phrasings (``queries.json``, ``rewrites.json``) from git history, and maps
each id to its link through the ``canonical_url`` front-matter line of the frozen v1
vault (read only). The cleaned links go to the bulk runner (``tools/bulk/runner.py``) as run
``library`` on ``eval``: it adds them through ``atlas.core.app.run("add", ...)`` with the real host
as the front door, ``--yes`` being the user's confirm for each batch, and owns the lanes, the fixed
scope answers, the retries, the parked and dropped links, the stops and the ledger. A pool id with no
``canonical_url``, a link that does not read and a link whose summary fails are counted and listed
with their reason; a cap or window decision stops the run, and a rerun continues, because a stored
link reports as already stored and makes no paid call. Queries and grades are imported as ``cases``
rows with origin ``ticket08``, idempotently.

When the slice leaves nothing to send in this run the last line is
``library: <a> added, <u> unreadable, 47 queries, 1535 grades``: ``a`` counts the pool's ids whose link
the library holds after the run (added now or stored before; joined copies and ids sharing one cleaned
link included) and ``u`` every other id (no link, retry, parked or dropped), so each id is counted
exactly once. A slice that ends on time with links left prints ``slice ended: ... run again to continue``
last instead. Without ``--yes`` it prints the count of links not yet stored and their estimated cost
and makes no call.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from tools.bulk import runner
from tools.quality import _path, evaldb  # noqa: F401  (_path puts the atlas package on sys.path)

from atlas import ports  # noqa: E402
from atlas.core import config, identity  # noqa: E402

HISTORY_REF = "570617c^"
HISTORY_DIR = ".scratch/atlas-v2/prototypes/08-retrieval"
DEFAULT_VAULT = "~/dev/atlas-v1-vault/instances/atlas"
PROFILE = "eval"
APPROVAL_WORDS = "quality.py build-library --yes"
RUN = "library"


class Stop(Exception):
    """The run cannot go on without the user: ``text`` is the decision's or the failure's own words."""


@dataclass(frozen=True)
class History:
    grades: Mapping[str, Mapping[str, int]]  # query id -> source id -> grade
    queries: Sequence[Mapping[str, Any]]
    rewrites: Mapping[str, Sequence[str]]

    def source_ids(self) -> list[str]:
        return sorted({source for graded in self.grades.values() for source in graded})


def git_show(repo: Path, ref: str, name: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{name}"], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise Stop(f"git show {ref}:{name} failed: {proc.stderr.strip() or proc.returncode}")
    return proc.stdout


def read_history(repo: Path, ref: str) -> History:
    def load(name: str) -> Any:
        return json.loads(git_show(repo, ref, f"{HISTORY_DIR}/{name}.json"))

    return History(load("grades"), load("queries"), load("rewrites"))


def front_matter(text: str) -> dict[str, str]:
    """The ``key: value`` lines of one artifact's front matter, values as written."""
    if not text.startswith("---\n"):
        return {}
    fields: dict[str, str] = {}
    for line in text[4:].split("\n---", 1)[0].splitlines():
        key, colon, value = line.partition(":")
        if colon and key and not key.startswith(" "):
            fields[key] = value.strip()
    return fields


def read_vault(vault: Path) -> dict[str, str]:
    """Each v1 source artifact's ``source_id`` with its ``canonical_url`` (read only; run logs left out)."""
    sources = vault / "summaries" / "sources"
    if not sources.is_dir():
        raise Stop(f"no summaries/sources folder under {vault}")
    found: dict[str, str] = {}
    for path in sorted(sources.rglob("*.md")):
        if "runs" in path.relative_to(sources).parts:
            continue
        fields = front_matter(path.read_text(encoding="utf-8"))
        source_id, link = fields.get("source_id", "").strip('"'), fields.get("canonical_url", "").strip('"')
        if source_id and link:
            found.setdefault(source_id, link)
    return found


def import_cases(db: Any, history: History, links: Mapping[str, str]) -> tuple[int, int]:
    """Keep the queries and grades as ``cases`` rows (existing rows stay) and return how many of each the store holds."""
    with evaldb.transaction(db):
        for query in history.queries:
            payload = {
                "qid": query["qid"],
                "origin": query["origin"],
                "text": query["text"],
                "rewrites": list(history.rewrites.get(query["qid"], ())),
                **{key: query[key] for key in ("gold_user", "gold_v1", "seed", "seed_title") if key in query},
            }
            seed = query.get("seed")
            if seed is not None:
                payload["seed_link"] = links.get(seed)
            evaldb.add_case(db, f"q:{query['qid']}", "search", "query", payload, None, "ticket08")
        for qid, graded in history.grades.items():
            for source_id, grade in graded.items():
                payload = {"qid": qid, "source": source_id, "grade": grade}
                evaldb.add_case(db, f"g:{qid}:{source_id}", "search", "grade", payload, links.get(source_id), "ticket08")
    queries = db.execute("SELECT count(*) FROM cases WHERE kind = 'query' AND origin = 'ticket08'").fetchone()[0]
    grades = db.execute("SELECT count(*) FROM cases WHERE kind = 'grade' AND origin = 'ticket08'").fetchone()[0]
    return queries, grades


def _why(entry: Mapping[str, Any] | None) -> str:
    """Why a pool link is not stored, as the runner's ledger says."""
    if entry is None:
        return "not stored after the add"
    if entry["state"] == runner.PARKED:
        return f"parked: {entry['question']}"
    return f"{entry['reason']} (will be tried again)" if entry["state"] == runner.RETRY else str(entry["reason"])


def build(
    host: ports.Host,
    repo: Path,
    history_ref: str,
    vault: Path,
    yes: bool,
    slice_minutes: float,
    check_token: bool,
    now: Callable[[], float],
    out: TextIO,
    err: TextIO,
) -> int:
    """Run ``build-library``; returns the exit code. ``now`` is the slice clock in seconds."""
    try:
        history = read_history(repo, history_ref)
        in_vault = read_vault(vault)
    except Stop as stop:
        print(str(stop), file=err)
        return 2
    try:
        profile = config.resolve(PROFILE, None)
    except config.NotSetUp as not_set_up:
        item = not_set_up.item()
        print(f"{item['what']}; {item['fix'][0]}", file=err)
        return 3
    ids = history.source_ids()
    link_of: dict[str, str] = {}
    reasons: dict[str, str] = {}
    for source_id in ids:
        raw = in_vault.get(source_id)
        cleaned = identity.clean(raw) if raw else None
        if cleaned is None:
            reasons[source_id] = "no canonical_url in the v1 vault" if not raw else f"{raw} is not a full http(s) link"
        else:
            link_of[source_id] = cleaned
    store = host.open_store(profile.store) if (yes or profile.store.exists()) else None
    try:
        distinct = list(dict.fromkeys(link_of.values()))
        held = [link for link in distinct if store is not None and store.source_for_link(link) is not None]
        if not yes:
            print(f"{len(distinct) - len(held)} of {len(distinct)} pool links are not stored yet ({len(held)} stored; {len(reasons)} pool ids have no usable link)", file=out)
            result = runner.run(host, PROFILE, RUN, distinct, yes=False, slice_minutes=slice_minutes, check_token=check_token, words=APPROVAL_WORDS, now=now, out=out, err=err)
            if result.end == "dry":
                print("no read, model or judge call was made; run again with --yes to build", file=out)
            return result.code
        assert store is not None
        db = evaldb.connect(profile.store)
        try:
            queries, grades = import_cases(db, history, in_vault)
        finally:
            db.close()
        result = runner.run(host, PROFILE, RUN, distinct, yes=True, slice_minutes=slice_minutes, check_token=check_token, words=APPROVAL_WORDS, now=now, out=out, err=err)
        if result.end == "stopped":
            print(f"stopped: {result.text}", file=out)
        if result.end in ("stopped", "refused"):
            return result.code
        stored = sum(1 for link in distinct if store.source_for_link(link) is not None)
        if result.end == "sliced":
            print(f"slice ended: {stored} of {len(distinct)} pool links stored; run again to continue", file=out)
            return 0
        added = 0
        for source_id in ids:
            link = link_of.get(source_id)
            if link is not None and store.source_for_link(link) is not None:
                added += 1
                continue
            reasons[source_id] = reasons.get(source_id) or _why(result.left.get(link or ""))
        for source_id, why in sorted(reasons.items()):
            print(f"  dropped {source_id} {in_vault.get(source_id, '(no link)')}: {why}", file=err)
        print(f"library: {added} added, {len(reasons)} unreadable, {queries} queries, {grades} grades", file=out)
        return 0
    finally:
        if store is not None:
            store.close()


if __name__ == "__main__":
    print("run tools/quality/quality.py", file=sys.stderr)
    raise SystemExit(2)
