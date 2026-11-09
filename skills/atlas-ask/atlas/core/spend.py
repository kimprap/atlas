"""Paid-call records, this month's spend, the cap, the window guard and batch estimates.

Every paid call writes one ``calls`` row. A judge call's cost is billed (the
judge's reply carries it); a model role's cost is the price table's list price
for the reply's model (``estimated``), or ``unknown`` when the table has no row.

The cap counts billed cost only, in the profile's current calendar month (local
time). From ``cap_warn`` × ``cap_usd``, and past the cap, every paid command
yields before its first paid call and a batch before its next item. The window
guard runs for batches only: before each item it reads the quota windows of the
providers of the roles the batch uses, and yields when any window's used share
is at or past ``window_stop``. Without a quota port, host facts or readable
windows the guard is off and window use is unknown. A command that continues
past a limit (``Guard.continue_past``) is not stopped by it again.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from atlas import ports
from atlas.core.config import Price, Profile
from atlas.store import CallRecord, Store

# The role label of judge calls in ``calls`` rows and the spend view.
JUDGE_ROLE = "judge"
SUMMARIZE_ROLE = "atlas_summarize"

# Per-item batch estimate: the last calls it takes medians over, and the token
# counts it uses before any call is recorded.
ESTIMATE_SAMPLE = 50
DEFAULT_INPUT_TOKENS = 30_000
DEFAULT_OUTPUT_TOKENS = 8_000

WINDOW_USE_UNKNOWN = "window use unknown"
CAP = "cap"
WINDOW = "window"

Clock = Callable[[], datetime]


def local_now() -> datetime:
    """The current local time, timezone-aware."""
    return datetime.now().astimezone()


def stamp(now: datetime) -> str:
    """``now`` as the UTC ISO-8601 text the store keeps."""
    return now.astimezone(timezone.utc).isoformat(timespec="seconds")


def month_start(now: datetime) -> str:
    """The start of ``now``'s local calendar month, as store text."""
    local = now.astimezone()
    return stamp(datetime(local.year, local.month, 1).astimezone())


def price_for(prices: Mapping[str, Price], model: str) -> Price | None:
    """The price row of ``model``, also when it carries a ``:<thinking>`` suffix."""
    return prices.get(model) or prices.get(model.partition(":")[0])


def list_price(price: Price, tokens_in: int, tokens_out: int, cache_read: int = 0, cache_write: int = 0) -> float:
    """USD at list price for the given token counts."""
    total = (
        price.input * tokens_in
        + price.output * tokens_out
        + price.cache_read * cache_read
        + price.cache_write * cache_write
    )
    return total / 1_000_000


def record_call(
    store: Store, profile: Profile, command: str, role: str, answer: ports.Reply, now: datetime | None = None
) -> CallRecord:
    """Keep one model-role call; ``command`` is the command as called, e.g. ``add --reread``."""
    usage = answer.usage
    if answer.cost.kind == "billed" and answer.cost.usd is not None:
        cost, kind = answer.cost.usd, "billed"
    else:
        price = price_for(profile.prices, answer.model)
        if price is None:
            cost, kind = None, "unknown"
        else:
            cost = list_price(price, usage.input, usage.output, usage.cache_read, usage.cache_write)
            kind = "estimated"
    record = CallRecord(
        at=stamp(now or local_now()),
        command=command,
        role=role,
        model=answer.model,
        thinking=answer.thinking,
        tokens_in=usage.input,
        tokens_out=usage.output,
        cache_read=usage.cache_read,
        cache_write=usage.cache_write,
        cost_usd=cost,
        cost_kind=kind,
    )
    store.add_call(record)
    return record


def record_judgments(
    store: Store, command: str, judgments: ports.Judgments, now: datetime | None = None
) -> CallRecord:
    """Keep one judge call, billed from the judge's reply, else of unknown cost."""
    billed = judgments.cost.kind == "billed" and judgments.cost.usd is not None
    record = CallRecord(
        at=stamp(now or local_now()),
        command=command,
        role=JUDGE_ROLE,
        model=judgments.model,
        thinking=None,
        tokens_in=0,
        tokens_out=0,
        cache_read=0,
        cache_write=0,
        cost_usd=judgments.cost.usd if billed else None,
        cost_kind="billed" if billed else "unknown",
    )
    store.add_call(record)
    return record


def _money(value: float) -> float:
    return round(value, 6)


def month(store: Store, now: datetime | None = None) -> dict[str, Any]:
    """This local calendar month's calls: the count, and cost per role and in total, billed and estimated apart."""
    when = (now or local_now()).astimezone()
    rows = store.calls_since(month_start(when))
    by_role: dict[str, dict[str, Any]] = {}
    total = {"billed": 0.0, "estimated": 0.0, "unknown_calls": 0}
    for row in rows:
        entry = by_role.setdefault(row.role, {"calls": 0, "billed": 0.0, "estimated": 0.0, "unknown_calls": 0})
        entry["calls"] += 1
        for bucket in (entry, total):
            if row.cost_kind == "unknown":
                bucket["unknown_calls"] += 1
            else:
                bucket[row.cost_kind] += row.cost_usd
    for bucket in (*by_role.values(), total):
        bucket["billed"] = _money(bucket["billed"])
        bucket["estimated"] = _money(bucket["estimated"])
    return {"month": when.strftime("%Y-%m"), "calls": len(rows), "by_role": by_role, "total": total}


def billed_this_month(store: Store, now: datetime | None = None) -> float:
    """The sum of billed cost in ``now``'s local calendar month."""
    rows = store.calls_since(month_start(now or local_now()))
    return _money(sum(row.cost_usd for row in rows if row.cost_kind == "billed"))


def _percent(share: float) -> str:
    return f"{round(share * 100)}%"


def duration_label(seconds: int) -> str:
    """``18000`` → ``5-hour``, ``604800`` → ``weekly``."""
    if seconds == 7 * 86_400:
        return "weekly"
    if seconds % 86_400 == 0:
        return f"{seconds // 86_400}-day"
    if seconds % 3_600 == 0:
        return f"{seconds // 3_600}-hour"
    return f"{max(seconds // 60, 1)}-minute"


def reset_label(resets_at: str, now: datetime) -> str:
    """A window's reset time in local time: ``14:30`` today, else ``2026-11-17 09:00``."""
    try:
        when = datetime.fromisoformat(resets_at).astimezone(now.astimezone().tzinfo)
    except ValueError:
        return resets_at
    return when.strftime("%H:%M" if when.date() == now.astimezone().date() else "%Y-%m-%d %H:%M")


def window_label(window: ports.Window) -> str:
    """``anthropic 5-hour window``."""
    return f"{window.provider} {duration_label(window.duration_s)} window"


@dataclass(frozen=True)
class Limit:
    """A cap or window yield. ``done`` and ``not_started`` count a batch's items when it stops partway."""

    kind: str  # CAP or WINDOW
    what: str  # "this month's billed spend is $16.40, 82% of the $20.00 monthly cap"
    resets: str | None = None  # WINDOW: when the stopping windows reset, in local time
    done: int | None = None
    not_started: int | None = None

    def text(self) -> str:
        """The plain-text statement a decision question opens with."""
        head = self.what
        if self.done is not None and self.not_started is not None:
            total = self.done + self.not_started
            head = f"stopped: {head}: {self.done} of {total} done, {self.not_started} not started"
        return f"{head}; resets {self.resets}" if self.resets else head


def cap_limit(profile: Profile, billed: float) -> Limit | None:
    """The cap yield for this month's ``billed`` cost, else ``None`` (also when no cap is set)."""
    cap = profile.cap_usd
    if cap is None or billed < profile.cap_warn * cap:
        return None
    if billed >= cap:
        what = f"this month's billed spend ${billed:.2f} is at or past the ${cap:.2f} monthly cap"
    else:
        what = f"this month's billed spend is ${billed:.2f}, {_percent(billed / cap)} of the ${cap:.2f} monthly cap"
    return Limit(CAP, what)


def providers(host: ports.Host, roles: Sequence[str]) -> list[str] | None:
    """The providers of ``roles``, in role order without repeats; ``None`` when the host cannot say."""
    if host.facts is None:
        return None
    found: list[str] = []
    try:
        for role in roles:
            provider = host.facts.role_provider(role)
            if provider is not None and provider not in found:
                found.append(provider)
    except ports.CallFailed:
        return None
    return found


def windows(host: ports.Host, roles: Sequence[str]) -> list[ports.Window] | None:
    """The quota windows of the providers of ``roles``; ``None`` when window use is unknown."""
    names = providers(host, roles)
    if host.quota is None or names is None:
        return None
    if not names:
        return []
    try:
        return list(host.quota.windows(names))
    except ports.CallFailed:
        return None


def windows_at_stop(profile: Profile, rows: Sequence[ports.Window]) -> list[ports.Window]:
    """The windows whose used share is at or past ``window_stop``."""
    return [row for row in rows if row.used_fraction >= profile.window_stop]


def window_limit(profile: Profile, rows: Sequence[ports.Window], now: datetime) -> Limit | None:
    """The window yield for ``rows``, else ``None``; it resets when the last stopping window does."""
    full = windows_at_stop(profile, rows)
    if not full:
        return None
    what = "; ".join(f"{window_label(row)} at {_percent(row.used_fraction)}" for row in full)
    last = max(full, key=lambda row: row.resets_at)
    return Limit(WINDOW, what, resets=reset_label(last.resets_at, now))


def window_use(rows: Sequence[ports.Window] | None, now: datetime) -> str:
    """Each window's current percent and reset time, for a batch confirm; Atlas predicts no percent."""
    if rows is None:
        return WINDOW_USE_UNKNOWN
    if not rows:
        return "no usage windows reported"
    return "; ".join(
        f"{window_label(row)} at {_percent(row.used_fraction)}, resets {reset_label(row.resets_at, now)}" for row in rows
    )


class Guard:
    """The cap and window checks of one command.

    ``paid`` commands check the cap; ``batch`` commands (an ``add`` reading 2 or
    more links, a redo, a re-read of 2 or more, a catch-up with 2 or more answer
    calls) also check the windows of the providers of ``roles``. Call ``check``
    before the first paid call and before each later item.
    """

    def __init__(
        self,
        store: Store,
        profile: Profile,
        host: ports.Host,
        roles: Sequence[str],
        *,
        paid: bool = True,
        batch: bool = False,
        clock: Clock = local_now,
    ) -> None:
        self.store = store
        self.profile = profile
        self.host = host
        self.roles = tuple(roles)
        self.paid = paid
        self.batch = batch
        self.clock = clock
        self.continued: set[str] = set()

    def continue_past(self, kinds: Iterable[str]) -> None:
        """The user chose to go on past these limit kinds for this command."""
        self.continued |= set(kinds)

    def check(self, done: int | None = None, not_started: int | None = None) -> Limit | None:
        """The first limit that stops the next paid call or item, else ``None``.

        ``done`` and ``not_started`` count a batch's items when it is partway.
        """
        now = self.clock()
        limit = None
        if self.paid and CAP not in self.continued:
            limit = cap_limit(self.profile, billed_this_month(self.store, now))
        if limit is None and self.batch and WINDOW not in self.continued:
            rows = windows(self.host, self.roles)
            limit = window_limit(self.profile, rows, now) if rows is not None else None
        if limit is None:
            return None
        return Limit(limit.kind, limit.what, limit.resets, done, not_started)

    def window_use(self) -> str:
        """Each window's current percent and reset time, or that window use is unknown."""
        return window_use(windows(self.host, self.roles), self.clock())


def estimate_item(store: Store, profile: Profile, model: str, page_tokens: int | None = None) -> float | None:
    """One batch item's list-price cost on ``model``, or ``None`` without its price row.

    Input tokens are ``page_tokens`` (a stored page, for redo and re-read), else
    the median input of the last 50 ``atlas_summarize`` calls (30K before any);
    output is the median output of those calls (8K before any).
    """
    price = price_for(profile.prices, model)
    if price is None:
        return None
    recent = store.recent_calls(SUMMARIZE_ROLE, ESTIMATE_SAMPLE)
    if page_tokens is None:
        page_tokens = (
            int(statistics.median(row.tokens_in + row.cache_read + row.cache_write for row in recent))
            if recent
            else DEFAULT_INPUT_TOKENS
        )
    output = int(statistics.median(row.tokens_out for row in recent)) if recent else DEFAULT_OUTPUT_TOKENS
    return list_price(price, page_tokens, output)


def estimate_text(cost: float | None, model: str) -> str:
    """``about $1.20 at list price``, or why there is no estimate."""
    if cost is None:
        return f"cost unknown: no price row for {model.partition(':')[0]}"
    return f"about ${cost:.2f} at list price"
