"""``build-library``: the ``eval`` test library, built once from ticket 08's graded pool (spec 4.15, ticket 13 section 2).

Reads the pool's 516 distinct v1 source ids (``grades.json``), the 47 queries and
their phrasings (``queries.json``, ``rewrites.json``) from git history, and maps
each id to its link through the ``canonical_url`` front-matter line of the frozen v1
vault (read only). Each link is added to ``eval`` through ``atlas.core.app.run("add", ...)``
with the real host, the tool acting as the front door: ``--yes`` is the user's
confirm for each batch, and a ``pick_scope`` decision is answered with the page
itself for a repo or link list, the transcript for a video, the images for an image
page and the first part for a page over the token limit, never an expanding scope.
A pool id with no ``canonical_url``, a link that does not read and a link whose
summary fails are dropped, counted and listed with their reason. A cap or window
decision, and any decision the tool has no fixed answer for, stops the run with its
text; a rerun continues, because a stored link reports as already stored and makes
no paid call. Queries and grades are imported as ``cases`` rows with origin
``ticket08``, idempotently.

The last line is ``library: <a> added, <u> unreadable, 47 queries, 1535 grades``:
``a`` counts the pool's ids whose link the library holds after the run (added now or
stored before; joined copies and ids sharing one cleaned link included) and ``u``
the ids dropped, so each id is counted exactly once. Without ``--yes`` it prints the
count of links not yet stored and their estimated cost and makes no call.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from tools.quality import _path, evaldb  # noqa: F401  (_path puts the atlas package on sys.path)

from atlas import ports  # noqa: E402
from atlas.core import app, config, identity, spend  # noqa: E402

HISTORY_REF = "570617c^"
HISTORY_DIR = ".scratch/atlas-v2/prototypes/08-retrieval"
DEFAULT_VAULT = "~/dev/atlas-v1-vault/instances/atlas"
PROFILE = "eval"
BATCH = 8
APPROVAL_WORDS = "quality.py build-library --yes"
# Rounds of answers one item or batch may take before the run gives up on it.
MAX_ROUNDS = 6
SUMMARIZE = "atlas_summarize"


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


def _first_text(answer: Mapping[str, Any]) -> str:
    for decision in answer.get("decisions", ()):
        return str(decision["question"])
    for problem in answer.get("problems", ()):
        return str(problem["problem"])
    for item in answer.get("result", {}).get("needs_action", ()):
        return str(item["what"])
    return json.dumps(answer.get("result", {}))[:200]


class Driver:
    """Adds links through ``app.run("add", ...)`` as the front door: answers each decision it has a fixed answer for."""

    def __init__(self, host: ports.Host, log: Callable[[str], None]) -> None:
        self.host = host
        self.log = log
        # Why each cleaned link did not end up stored, as the run learned it.
        self.dropped: dict[str, str] = {}

    def _note(self, answer: Mapping[str, Any]) -> None:
        for item in answer.get("result", {}).get("items", ()):
            result = str(item.get("result", ""))
            link = identity.clean(item.get("link"))
            if link is not None and (result.startswith("unreadable") or result.startswith("summary failed")):
                self.dropped[link] = result

    @staticmethod
    def _scope_option(decision: Mapping[str, Any]) -> Mapping[str, Any] | None:
        """The option with the fixed answer: the page, the transcript, the images or the first part; never an expanding scope."""
        options = {option["id"]: option for option in decision["options"]}
        for wanted in ("page", "transcript", "images", "first_part"):
            if wanted in options:
                return options[wanted]
        return None

    def add(self, body: dict[str, Any]) -> None:
        """Run ``body`` and every resend the decisions call for; raises ``Stop`` on a decision it cannot answer."""
        for _ in range(MAX_ROUNDS):
            answer, code = app.run("add", None, {"profile": PROFILE, **body}, self.host)
            self._note(answer)
            if code == 0:
                return
            if code != 4:
                raise Stop(_first_text(answer))
            decisions = answer["decisions"]
            confirm = next((d for d in decisions if d["kind"] == "confirm"), None)
            if confirm is not None:
                approval = {"by": "confirm", "decision": confirm["id"], "choice": "go", "words": APPROVAL_WORDS}
                body = {**{k: v for k, v in body.items() if k != "approval"}, "approval": approval}
                continue
            for decision in decisions:
                if decision["kind"] == "summary_failed":
                    for option in decision["options"]:
                        for item in option["then"].get("resend", {}).get("items", ()):
                            link = identity.clean(item.get("link"))
                            if link is not None:
                                self.dropped[link] = "summary failed, also after one escalation"
                    continue
                option = self._scope_option(decision) if decision["kind"] == "pick_scope" else None
                if option is None:
                    raise Stop(decision["question"])
                resend = dict(option["then"]["resend"])
                self.add({k: v for k, v in resend.items() if k != "mode"})
            return
        raise Stop(f"no end to the decisions of an add of {len(body.get('items', ()))} link(s)")


def estimate_per_link(store: Any, profile: config.Profile, selector: str | None) -> float | None:
    if selector is None:
        return None
    if store is not None:
        return spend.estimate_item(store, profile, selector)
    price = spend.price_for(profile.prices, selector)
    return None if price is None else spend.list_price(price, spend.DEFAULT_INPUT_TOKENS, spend.DEFAULT_OUTPUT_TOKENS)


def build(
    host: ports.Host,
    repo: Path,
    history_ref: str,
    vault: Path,
    yes: bool,
    out: TextIO,
    err: TextIO,
) -> int:
    """Run ``build-library``; returns the exit code."""
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
        todo = [link for link in distinct if store is None or store.source_for_link(link) is None]
        if not yes:
            return _estimate(host, profile, store, todo, len(distinct), len(reasons), out)
        assert store is not None
        db = evaldb.connect(profile.store)
        try:
            queries, grades = import_cases(db, history, in_vault)
        finally:
            db.close()
        driver = Driver(host, lambda text: print(text, file=err, flush=True))
        try:
            for start in range(0, len(todo), BATCH):
                batch = todo[start : start + BATCH]
                driver.add({"items": [{"link": link} for link in batch]})
                stored = sum(1 for link in todo[: start + len(batch)] if store.source_for_link(link) is not None)
                print(f"batch {start // BATCH + 1} of {-(-len(todo) // BATCH)}: {stored} of {start + len(batch)} stored", file=err, flush=True)
        except Stop as stop:
            stored = sum(1 for link in todo if store.source_for_link(link) is not None)
            print(f"stopped: {stored} of {len(todo)} links stored this run so far; {stop}", file=err)
            print(f"stopped: {stop}", file=out)
            return 1
        added = 0
        for source_id in ids:
            link = link_of.get(source_id)
            if link is not None and store.source_for_link(link) is not None:
                added += 1
                continue
            reasons[source_id] = reasons.get(source_id) or (driver.dropped.get(link or "") or "not stored after the add")
        for source_id, why in sorted(reasons.items()):
            print(f"  dropped {source_id} {in_vault.get(source_id, '(no link)')}: {why}", file=err)
        print(f"library: {added} added, {len(reasons)} unreadable, {queries} queries, {grades} grades", file=out)
        return 0
    finally:
        if store is not None:
            store.close()


def _estimate(host: ports.Host, profile: config.Profile, store: Any, todo: Sequence[str], distinct: int, no_link: int, out: TextIO) -> int:
    selector = None
    if host.facts is not None:
        try:
            selector = host.facts.roles().get(SUMMARIZE)
        except ports.CallFailed:
            selector = None
    each = estimate_per_link(store, profile, selector)
    held = distinct - len(todo)
    print(f"{len(todo)} of {distinct} pool links are not stored yet ({held} stored; {no_link} pool ids have no usable link)", file=out)
    if selector is None:
        print("estimate: cost unknown: the summary model is not known", file=out)
    elif each is None:
        print(f"estimate: {spend.estimate_text(None, selector)}", file=out)
    else:
        print(f"estimate: {spend.estimate_text(each * len(todo), selector)} ({spend.estimate_text(each, selector)} per link), plus Jev calls billed on the OpenRouter key", file=out)
    print("no read, model or judge call was made; run again with --yes to build", file=out)
    return 0


if __name__ == "__main__":
    print("run tools/quality/quality.py", file=sys.stderr)
    raise SystemExit(2)
