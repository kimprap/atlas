"""The bulk runner (spec section 6; ``ARCHITECTURE.md`` "Bulk runner"): a repo-only tool that works through a large
list of links for one profile in lanes and time-boxed slices.

It adds links through ``atlas.core.app.run("add", ...)`` with the host it is given, acting as the front door: a
``confirm`` decision is answered with the caller's approval words, a ``pick_scope`` decision with the page, the
transcript, the images or the first part (never an expanding scope) and anything it has no answer for is parked
in the run's ledger while the run goes on. A ``cap`` or ``window`` decision, ``judge_setup`` or any unexpected
exit ends the run. The ledger holds only what the store cannot: each link not yet done, with its lane, state,
reason and attempts and, for a parked link, the question, options and the user's answer.

``bulk.py`` is the command line; ``tools/quality/library.py`` calls ``run`` for ``build-library``. Every entry point
prints its own errors and returns an exit code: 0 done, 1 stopped, 2 bad input, 3 not set up.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import urlsplit

from tools.quality import _path  # noqa: F401  (puts the repo root and the atlas package on sys.path)

from atlas import ports  # noqa: E402
from atlas.core import app, config, failure_log, identity, sites, spend  # noqa: E402

BATCH = 8
DEFAULT_SLICE = 55
# Later runs an unreadable link is sent in again before it is dropped.
RETRIES = 2
# Rounds of answers one batch may take before the run gives up on it.
MAX_ROUNDS = 6
SUMMARIZE = "atlas_summarize"
TOKEN_VARIABLES = ("GITHUB_TOKEN", "GH_TOKEN")

QUEUED, RETRY, PARKED, DROPPED = "queued", "retry", "parked", "dropped"
DONE = "done"
STATES = (DONE, QUEUED, RETRY, PARKED, DROPPED)

# Lanes in the order they run, which is the cheapest and most likely to succeed first.
PAGE, X_POST, GITHUB_PAGE, REPO_ROOT, VIDEO, IMAGE = "page", "x_post", "github_page", "repo_root", "video", "image"
LANES = (PAGE, X_POST, GITHUB_PAGE, REPO_ROOT, VIDEO, IMAGE)
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp")
VIDEO_HOSTS = frozenset({"vimeo.com", "www.vimeo.com"})
# The scope answers a pick-scope decision gets, in order of preference.
FIXED_SCOPES = ("page", "transcript", "images", "first_part")
_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class BadInput(Exception):
    """The call or the ledger is wrong: the text says how (exit 2)."""


class Halt(Exception):
    """The run cannot go on: ``text`` is the decision's or the failure's own words, ``code`` the exit code."""

    def __init__(self, code: int, text: str) -> None:
        super().__init__(text)
        self.code = code
        self.text = text


@dataclass
class Result:
    """How a ``run`` ended. ``end`` is ``dry`` (estimate only), ``refused`` (bad input or not set up), ``stopped``
    (``text`` says why), ``sliced`` (the slice ran out with links left to send this run) or ``finished`` (every link
    due this run was sent). ``left`` is the ledger's links not yet done."""

    code: int
    end: str
    left: dict[str, dict[str, Any]] = field(default_factory=dict)
    text: str = ""

    @property
    def more(self) -> bool:
        """Whether a later run has links to send: a queued or retry link, or a parked link whose answer is not sent."""
        return any(e["state"] in (QUEUED, RETRY) or (e["state"] == PARKED and e.get("answer")) for e in self.left.values())


def lane_of(link: str) -> str:
    """The lane of one cleaned link, from the link alone."""
    split = urlsplit(link)
    host = (split.hostname or "").lower()
    if split.path.lower().endswith(IMAGE_SUFFIXES):
        return IMAGE
    site = sites.site_for(host)
    if host in VIDEO_HOSTS or (site is not None and site.name == "youtube"):
        return VIDEO
    if site is not None and site.name == "github":
        return REPO_ROOT if len([part for part in split.path.split("/") if part]) == 2 else GITHUB_PAGE
    if site is not None and site.name == "x":
        return X_POST
    return PAGE


def minutes(text: str) -> float:
    """``--slice``'s value; ``ValueError`` when it is not a number above 0."""
    value = float(text)
    if not value > 0 or value == float("inf"):
        raise ValueError(text)
    return value


# Ledger -----------------------------------------------------------------------------------------------------------
def ledger_path(profile: str, name: str) -> Path:
    """The run's ledger. A profile is any name the settings hold that is a folder name (as the failed-summary log needs); a run name is stricter."""
    if not profile or profile in (".", "..") or "/" in profile or os.sep in profile:
        raise BadInput(f"the profile name {profile!r} is not a folder name")
    if _NAME.fullmatch(name) is None:
        raise BadInput(f"the run name {name!r} is not letters, digits, '.', '_' and '-' starting with a letter or digit")
    return failure_log.state_home() / "atlas" / profile / "bulk" / f"{name}.json"


def _entry(lane: str | None, state: str = QUEUED, reason: str | None = None, attempts: int = 0, last_run: int = 0, **extra: Any) -> dict[str, Any]:
    return {"lane": lane, "state": state, "reason": reason, "attempts": attempts, "last_run": last_run, **extra}


def _check_entry(entry: Any) -> None:
    """``ValueError`` (or ``KeyError``/``TypeError``) when ``entry`` is not what this runner writes: a hand-edited ledger must not crash a run later."""
    if entry["state"] not in (QUEUED, RETRY, PARKED, DROPPED):
        raise ValueError(f"a link has the state {entry['state']!r}")
    if entry["lane"] not in LANES and not (entry["lane"] is None and entry["state"] == DROPPED):
        raise ValueError(f"a link has the lane {entry['lane']!r}")
    if not (isinstance(entry["attempts"], int) and isinstance(entry["last_run"], int)):
        raise ValueError("a link's attempts and last_run are whole numbers")
    if entry["state"] == PARKED:
        ids = [option["id"] for option in entry["options"] if isinstance(option["then"], dict)]
        if not isinstance(entry["question"], str) or len(ids) != len(entry["options"]) or entry["answer"] not in (None, *ids):
            raise ValueError("a parked link holds its question, options and answer")


def _load(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as err:
        raise BadInput(f"the ledger {path} cannot be read: {err}") from None
    try:
        ledger = json.loads(text)
        if not (isinstance(ledger, dict) and isinstance(ledger["run"], int) and isinstance(ledger["links"], dict)):
            raise ValueError("it holds no run counter and links")
        for entry in ledger["links"].values():
            _check_entry(entry)
    except (ValueError, KeyError, TypeError) as err:
        raise BadInput(f"the ledger {path} is not a run ledger: {err!r}") from None
    return ledger


def _save(path: Path, ledger: Mapping[str, Any]) -> None:
    """Write the ledger to a temporary file in its folder and rename it over the ledger, so a kill leaves one whole file."""
    folder = path.parent
    try:
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(folder, 0o700)
        handle, temporary = tempfile.mkstemp(dir=folder, prefix=f"{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as file:
                json.dump(ledger, file, ensure_ascii=False, indent=1)
                file.flush()
                os.fsync(file.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise
    except OSError as err:
        raise Halt(1, f"the ledger {path} cannot be written: {err}") from None


def _require(profile: str, name: str) -> tuple[Path, dict[str, Any]]:
    path = ledger_path(profile, name)
    ledger = _load(path)
    if ledger is None:
        raise BadInput(f"no run {name} for profile {profile}: it has no ledger")
    return path, ledger


def _tally(entries: Mapping[str, Mapping[str, Any]]) -> dict[tuple[str | None, str], int]:
    found: dict[tuple[str | None, str], int] = {}
    for entry in entries.values():
        key = (entry["lane"], entry["state"])
        found[key] = found.get(key, 0) + 1
    return found


def _counts(found: Mapping[tuple[str | None, str], int], empty: str) -> str:
    order = [(lane, state) for lane in (*LANES, None) for state in STATES]
    parts = [f"{lane or 'no lane'} {state} {found[(lane, state)]}" for lane, state in order if (lane, state) in found]
    return ", ".join(parts) or empty


# status, answer, retry ---------------------------------------------------------------------------------------------
def status(profile: str, name: str, out: TextIO, err: TextIO) -> int:
    try:
        _, ledger = _require(profile, name)
    except BadInput as bad:
        print(str(bad), file=err)
        return 2
    entries = ledger["links"]
    print(f"run {name} on {profile}: run {ledger['run']}, {len(entries)} link(s) not yet done", file=out)
    for lane in (*LANES, None):
        found = {state: n for (each, state), n in _tally(entries).items() if each == lane}
        if found:
            print(f"{lane or 'no lane'}: {', '.join(f'{state} {found[state]}' for state in STATES if state in found)}", file=out)
    for link, entry in entries.items():
        if entry["state"] == PARKED:
            answered = f"; answered: {entry['answer']}" if entry.get("answer") else ""
            print(f"parked {link}: {entry['question']} [options: {', '.join(option['id'] for option in entry['options'])}{answered}]", file=out)
        elif entry["state"] == DROPPED:
            log = f" [log {entry['log']}]" if entry.get("log") else ""
            print(f"dropped {link}: {entry['reason']}{log}", file=out)
    return 0


def answer(profile: str, name: str, link: str, option: str, out: TextIO, err: TextIO) -> int:
    try:
        path, ledger = _require(profile, name)
        entries = ledger["links"]
        key = identity.clean(link) or link
        entry = entries.get(key)
        if entry is None or entry["state"] != PARKED:
            raise BadInput(f"{link} is not a parked link of run {name}")
        chosen = next((each for each in entry["options"] if each["id"] == option), None)
        if chosen is None:
            raise BadInput(f"{option!r} is not an option of {link}: the options are {', '.join(each['id'] for each in entry['options'])}")
        if "resend" in chosen["then"]:
            entry["answer"] = option
            print(f"recorded {option} for {key}; the next run sends it", file=out)
        else:
            entries[key] = _entry(entry["lane"], DROPPED, f"skipped ({option})", entry["attempts"], entry["last_run"])
            print(f"recorded {option} for {key}; nothing to send, so it is dropped", file=out)
        _save(path, ledger)
    except BadInput as bad:
        print(str(bad), file=err)
        return 2
    except Halt as halt:
        print(f"stopped: {halt.text}", file=err)
        return halt.code
    return 0


def retry(profile: str, name: str, link: str | None, out: TextIO, err: TextIO) -> int:
    """Put ``link``, or with ``None`` every dropped link, back in the queue."""
    try:
        path, ledger = _require(profile, name)
        entries = ledger["links"]
        if link is None:
            wanted = [key for key, entry in entries.items() if entry["state"] == DROPPED and entry["lane"] is not None]
        else:
            key = identity.clean(link) or link
            entry = entries.get(key)
            if entry is None or entry["state"] != DROPPED or entry["lane"] is None:
                raise BadInput(f"{link} is not a dropped link of run {name}")
            wanted = [key]
        for key in wanted:
            entries[key] = _entry(entries[key]["lane"])
        _save(path, ledger)
    except BadInput as bad:
        print(str(bad), file=err)
        return 2
    except Halt as halt:
        print(f"stopped: {halt.text}", file=err)
        return halt.code
    print(f"{len(wanted)} link(s) back in the queue", file=out)
    return 0


# run ----------------------------------------------------------------------------------------------------------------
Unit = tuple[str, list[str], dict[str, Any]]


def _resend_body(resend: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in resend.items() if key != "mode"}


def _units(entries: Mapping[str, Mapping[str, Any]]) -> list[Unit]:
    """What a run sends, in order: each answered parked link as its own add, then each lane's batches."""
    units: list[Unit] = []
    for link, entry in entries.items():
        if entry["state"] == PARKED and entry.get("answer"):
            option = next(each for each in entry["options"] if each["id"] == entry["answer"])
            units.append((entry["lane"], [link], _resend_body(option["then"]["resend"])))
    for lane in LANES:
        due = [link for link, entry in entries.items() if entry["lane"] == lane and entry["state"] in (QUEUED, RETRY)]
        for start in range(0, len(due), BATCH):
            batch = due[start : start + BATCH]
            units.append((lane, batch, {"items": [{"link": link} for link in batch]}))
    return units


def _text(answer: Mapping[str, Any]) -> str:
    for decision in answer.get("decisions", ()):
        return str(decision["question"])
    for problem in answer.get("problems", ()):
        return str(problem["problem"])
    for item in answer.get("result", {}).get("needs_action", ()):
        return f"{item['what']}; {item['fix'][0]}" if item.get("fix") else str(item["what"])
    return json.dumps(answer.get("result", {}))[:200]


def _decision_link(decision: Mapping[str, Any]) -> str | None:
    """The cleaned link a decision is about, from the items its options resend."""
    for option in decision["options"]:
        for item in option["then"].get("resend", {}).get("items", ()):
            link = identity.clean(item.get("link"))
            if link is not None:
                return link
    return None


def _scope_option(decision: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """The option with the fixed answer; never an expanding scope."""
    options = {option["id"]: option for option in decision["options"] if "resend" in option["then"]}
    for wanted in FIXED_SCOPES:
        if wanted in options:
            return options[wanted]
    return None


def estimate_per_link(store: Any, profile: config.Profile, selector: str | None) -> float | None:
    if selector is None:
        return None
    if store is not None:
        return spend.estimate_item(store, profile, selector)
    price = spend.price_for(profile.prices, selector)
    return None if price is None else spend.list_price(price, spend.DEFAULT_INPUT_TOKENS, spend.DEFAULT_OUTPUT_TOKENS)


def _estimate(host: ports.Host, profile: config.Profile, store: Any, count: int, out: TextIO) -> None:
    selector = None
    if host.facts is not None:
        try:
            selector = host.facts.roles().get(SUMMARIZE)
        except ports.CallFailed:
            selector = None
    each = estimate_per_link(store, profile, selector)
    if selector is None:
        print("estimate: cost unknown: the summary model is not known", file=out)
    elif each is None:
        print(f"estimate: {spend.estimate_text(None, selector)}", file=out)
    else:
        print(f"estimate: {spend.estimate_text(each * count, selector)} ({spend.estimate_text(each, selector)} per link), plus Jev calls billed on the OpenRouter key", file=out)


def token_problem() -> str | None:
    """Why a run with GitHub links may not start, or ``None``. The value is only tested for being non-blank."""
    if any(os.environ.get(variable, "").strip() for variable in TOKEN_VARIABLES):
        return None
    return f"the queue holds GitHub links and neither {' nor '.join(TOKEN_VARIABLES)} holds a value: set one, or pass --no-token to run without"


class _Slice:
    """One ``run --yes``: the batches in order, until the plan is done, the slice runs out or the run stops."""

    def __init__(
        self,
        host: ports.Host,
        store: Any,
        profile: str,
        name: str,
        path: Path,
        ledger: dict[str, Any],
        words: str,
        now: Callable[[], float],
        out: TextIO,
        err: TextIO,
    ) -> None:
        self.host, self.store, self.profile, self.name = host, store, profile, name
        self.path, self.ledger, self.words, self.now, self.out, self.err = path, ledger, words, now, out, err
        self.entries: dict[str, dict[str, Any]] = ledger["links"]
        self.run: int = ledger["run"]
        self.this: dict[tuple[str | None, str], int] = {}
        self.batches = 0

    def go(self, units: Sequence[Unit], seconds: float) -> Result:
        started = self.now()
        end, halt = "finished", None
        try:
            for unit in units:
                if self.now() - started >= seconds:
                    end = "sliced"
                    break
                self._send(unit)
                _save(self.path, self.ledger)
        except Halt as stop:
            end, halt = "stopped", stop
        try:
            _save(self.path, self.ledger)
        except Halt as failed:
            halt = halt or failed
            end = "stopped"
        sent = sum(self.this.values())
        print(f"run {self.name} on {self.profile}: slice {self.run}, {sent} link(s) sent", file=self.out)
        print(f"this slice: {_counts(self.this, 'nothing sent')}", file=self.out)
        print(f"in the ledger: {_counts(_tally(self.entries), 'nothing left')}", file=self.out)
        if halt is not None:
            return Result(halt.code, "stopped", dict(self.entries), halt.text)
        return Result(0, end, dict(self.entries))

    def _held(self, link: str) -> bool:
        return self.store.source_for_link(link) is not None

    def _send(self, unit: Unit) -> None:
        lane, links, body = unit
        outcomes: dict[str, dict[str, Any]] = {}
        halt = None
        try:
            self._chain(body, outcomes)
        except Halt as stop:
            halt = stop
        stored = self._settle(lane, links, outcomes, halt is not None)
        self.batches += 1
        print(f"batch {self.batches} ({lane}): {stored} of {len(links)} stored", file=self.err, flush=True)
        if halt is not None:
            raise halt

    def _chain(self, body: dict[str, Any], outcomes: dict[str, dict[str, Any]]) -> None:
        """Run ``body`` and every resend its decisions call for; ``Halt`` on a stop."""
        for _ in range(MAX_ROUNDS):
            reply, code = app.run("add", None, {"profile": self.profile, **body}, self.host)
            for item in reply.get("result", {}).get("items", ()):
                link = identity.clean(item.get("link"))
                if link is not None:
                    outcomes[link] = {"result": str(item.get("result", ""))}
            if code == 0:
                return
            if code != 4:
                raise Halt(3 if code == 3 else 1, _text(reply))
            decisions = reply["decisions"]
            for decision in decisions:
                if decision["kind"] in (spend.CAP, spend.WINDOW):
                    raise Halt(1, str(decision["question"]))
                if decision["kind"] == "judge_setup":
                    raise Halt(3, str(decision["question"]))
            confirm = next((d for d in decisions if d["kind"] == "confirm"), None)
            if confirm is not None:
                approval = {"by": "confirm", "decision": confirm["id"], "choice": "go", "words": self.words}
                body = {**{key: value for key, value in body.items() if key != "approval"}, "approval": approval}
                continue
            self._decide(reply, decisions, outcomes)
            return
        raise Halt(1, f"no end to the decisions of an add of {len(body.get('items', ()))} link(s)")

    def _decide(self, reply: Mapping[str, Any], decisions: Sequence[Mapping[str, Any]], outcomes: dict[str, dict[str, Any]]) -> None:
        failed = iter([item for item in reply.get("result", {}).get("items", ()) if item.get("result") == "summary failed"])
        for decision in decisions:
            link = _decision_link(decision)
            if decision["kind"] == "summary_failed" and link is not None:
                outcomes[link] = {"failed": next(failed, {}).get("replies_log")}
            elif decision["kind"] == "pick_scope" and link is not None:
                option = _scope_option(decision)
                if option is None:
                    options = [{"id": each["id"], "label": each["label"], "then": each["then"]} for each in decision["options"]]
                    outcomes[link] = {"parked": {"question": str(decision["question"]), "options": options, "answer": None}}
                else:
                    self._chain(_resend_body(option["then"]["resend"]), outcomes)
            else:
                raise Halt(1, str(decision["question"]))

    def _settle(self, lane: str, links: Sequence[str], outcomes: Mapping[str, Mapping[str, Any]], halted: bool) -> int:
        """Record each link's outcome in the ledger; a link a stop left without one stays as it was. Returns how many are stored."""
        stored = 0
        for link in links:
            entry = self.entries[link]
            got = outcomes.get(link)
            if self._held(link):
                del self.entries[link]
                self._count(lane, DONE)
                stored += 1
                continue
            result = str(got.get("result", "")) if got is not None else ""
            if got is not None and "parked" in got:
                self._mark(lane, link, entry, PARKED, "needs your answer", **got["parked"])
            elif got is not None and "failed" in got:
                self._mark(lane, link, entry, DROPPED, "summary failed", log=got["failed"])
            elif result.startswith("unreadable"):
                dropped = entry["attempts"] + 1 > RETRIES
                self._mark(lane, link, entry, DROPPED if dropped else RETRY, result)
            elif not halted:
                self._mark(lane, link, entry, DROPPED, f"not stored after the add: {result or 'no result'}")
        return stored

    def _mark(self, lane: str, link: str, entry: Mapping[str, Any], state: str, reason: str, **extra: Any) -> None:
        self.entries[link] = _entry(entry["lane"], state, reason, entry["attempts"] + 1, self.run, **extra)
        self._count(lane, state)

    def _count(self, lane: str, state: str) -> None:
        self.this[(lane, state)] = self.this.get((lane, state), 0) + 1


def run(
    host: ports.Host,
    profile: str,
    name: str,
    links: Sequence[str] | None,
    *,
    yes: bool,
    slice_minutes: float,
    check_token: bool,
    words: str,
    now: Callable[[], float],
    out: TextIO,
    err: TextIO,
) -> Result:
    """One run of the named ledger on ``profile``; ``links`` are the raw links to add to its queue, ``None`` to continue.

    Without ``yes`` it prints each lane's count and the estimate and touches nothing. ``now`` is the slice clock in seconds.
    """
    try:
        path = ledger_path(profile, name)
        ledger = _load(path)
        if ledger is None and not links:
            raise BadInput(f"no run {name} for profile {profile}: give --links <file>")
        try:
            resolved = config.resolve(profile, None)
        except config.NotSetUp as not_set_up:
            item = not_set_up.item()
            print(f"{item['what']}; {item['fix'][0]}", file=err)
            return Result(3, "refused")
        ledger = ledger or {"run": 0, "links": {}}
        store = host.open_store(resolved.store) if (yes or resolved.store.exists()) else None
        try:
            return _run(host, resolved, store, name, path, ledger, links or (), yes, slice_minutes, check_token, words, now, out, err)
        finally:
            if store is not None:
                store.close()
    except BadInput as bad:
        print(str(bad), file=err)
        return Result(2, "refused")
    except Halt as halt:
        print(f"stopped: {halt.text}", file=err)
        return Result(halt.code, "stopped", text=halt.text)


def _run(
    host: ports.Host,
    profile: config.Profile,
    store: Any,
    name: str,
    path: Path,
    ledger: dict[str, Any],
    links: Sequence[str],
    yes: bool,
    slice_minutes: float,
    check_token: bool,
    words: str,
    now: Callable[[], float],
    out: TextIO,
    err: TextIO,
) -> Result:
    entries: dict[str, dict[str, Any]] = ledger["links"]

    def held(link: str) -> bool:
        return store is not None and store.source_for_link(link) is not None

    for link in [link for link in entries if held(link)]:
        del entries[link]
    for raw in links:
        cleaned = identity.clean(raw)
        if cleaned is None:
            entries.setdefault(raw, _entry(None, DROPPED, "not a full http(s) link"))
        elif cleaned not in entries and not held(cleaned):
            entries[cleaned] = _entry(lane_of(cleaned))
    units = _units(entries)
    if not yes:
        for lane in LANES:
            held_in_lane = sum(1 for e in entries.values() if e["lane"] == lane)
            if held_in_lane:
                due = sum(len(batch) for each, batch, _ in units if each == lane)
                print(f"{lane}: {held_in_lane} not yet done, {due} to send", file=out)
        _estimate(host, profile, store, sum(len(batch) for _, batch, _ in units), out)
        return Result(0, "dry", dict(entries))
    if check_token and any(lane in (REPO_ROOT, GITHUB_PAGE) for lane, _, _ in units):
        problem = token_problem()
        if problem is not None:
            raise BadInput(problem)
    ledger["run"] += 1
    _save(path, ledger)
    return _Slice(host, store, profile.name, name, path, ledger, words, now, out, err).go(units, slice_minutes * 60)
