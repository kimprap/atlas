"""Call records, the cap and the window guard (spec 4.11) on the core module.

No paid command exists before ``add`` lands, so these drive ``spend.Guard`` the
way a batch does, before its first paid call and before each later item, on a
profile resolved from a temporary ``HOME``, the real SQLite store and the fake
host.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from tests.fakes.fake_host import FakeHost

from atlas import ports  # noqa: E402  (fake_host puts the package on sys.path)
from atlas.core import config, spend  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRICES = ROOT / "skills" / "atlas-init" / "prices.default.toml"
NOW = datetime(2026, 11, 15, 12, 0).astimezone()
LAST_MONTH = datetime(2026, 10, 31, 12, 0).astimezone()
SONNET = "anthropic/claude-sonnet-5-5"
QUESTION = ports.Question("support", "noul", "Does the passage support the claim?")


def summary(model: str, tokens_in: int = 1_000, tokens_out: int = 500) -> ports.Reply:
    return ports.Reply(model, "high", "", {}, "tool", ports.Usage(tokens_in, tokens_out, 0, 0), ports.Cost(None, "unknown"))


class LimitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(mock.patch.dict(os.environ, {"HOME": str(self.home)}))
        self.store_path = self.home / "data" / "smoke.db"
        self.configure()

    def configure(self, extra: str = "", tail: str = "") -> None:
        settings = config.config_path()
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(
            f'default_profile = "smoke"\n[profiles.smoke]\nstore = "{self.store_path}"\njudge = "jev"\n{extra}\n{tail}'
        )
        self.profile = config.resolve(None, None)

    def open(self, fake: FakeHost):
        store = fake.open_store(self.store_path)
        self.addCleanup(store.close)
        return store

    def judge_call(self, fake: FakeHost, store, now: datetime = NOW) -> None:
        """One paid judge call, recorded as a command records it."""
        spend.record_judgments(store, "add", fake.judge("claim and passages", [QUESTION]), now=now)

    def test_calls_are_billed_estimated_or_unknown(self) -> None:
        self.configure(tail=DEFAULT_PRICES.read_text())
        fake = FakeHost(judgments={"support": ports.Answer(p=0.9)}, judge_cost=ports.Cost(0.0125, "billed"))
        store = self.open(fake)
        self.judge_call(fake, store)
        priced = spend.record_call(store, self.profile, "add", "atlas_summarize", summary(SONNET, 30_000, 8_000), now=NOW)
        unpriced = spend.record_call(store, self.profile, "add", "atlas_summarize", summary("other/model"), now=NOW)
        # Sonnet 5.5 list price: $2 per million input and $10 per million output tokens.
        self.assertEqual((priced.cost_kind, round(priced.cost_usd, 6)), ("estimated", 0.14))
        self.assertEqual((unpriced.cost_kind, unpriced.cost_usd), ("unknown", None))
        month = spend.month(store, NOW)
        self.assertEqual(month["calls"], 3)
        self.assertEqual(month["total"], {"billed": 0.0125, "estimated": 0.14, "unknown_calls": 1})
        self.assertEqual(month["by_role"]["judge"], {"calls": 1, "billed": 0.0125, "estimated": 0.0, "unknown_calls": 0})
        self.assertEqual(store.models_not_billed(spend.JUDGE_ROLE), [SONNET, "other/model"])

    def test_the_cap_counts_billed_cost_of_this_local_month_only(self) -> None:
        self.configure("cap_usd = 10.0")
        fake = FakeHost(judgments={"support": ports.Answer(p=0.9)}, judge_cost=ports.Cost(9.0, "billed"))
        store = self.open(fake)
        self.judge_call(fake, store, now=LAST_MONTH)
        spend.record_call(store, self.profile, "add", "atlas_summarize", summary(SONNET, 10**9, 0), now=NOW)
        guard = spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], clock=lambda: NOW)
        self.assertIsNone(guard.check())
        self.judge_call(fake, store)
        self.assertEqual(guard.check().kind, "cap")

    def test_the_cap_yields_before_the_next_item_with_done_and_not_started_counts(self) -> None:
        self.configure("cap_usd = 10.0")
        fake = FakeHost(judgments={"support": ports.Answer(p=0.9)}, judge_cost=ports.Cost(3.0, "billed"))
        store = self.open(fake)
        guard = spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], batch=True, clock=lambda: NOW)
        items, done, stop = 5, 0, None
        for index in range(items):
            stop = guard.check(done, items - done) if index else guard.check()
            if stop is not None:
                break
            self.judge_call(fake, store)
            done += 1
        # $6 billed is under 80% of $10; the third item's $9 is at 90%, so the fourth item yields.
        self.assertEqual(done, 3)
        self.assertEqual(stop.text(), "stopped: this month's billed spend is $9.00, 90% of the $10.00 monthly cap: 3 of 5 done, 2 not started")
        self.judge_call(fake, store)
        self.assertEqual(guard.check().what, "this month's billed spend $12.00 is at or past the $10.00 monthly cap")
        guard.continue_past({"cap"})
        self.assertIsNone(guard.check(4, 1))

        unpaid = spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], paid=False, clock=lambda: NOW)
        self.assertIsNone(unpaid.check())
        self.configure()
        uncapped = spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], clock=lambda: NOW)
        self.assertIsNone(uncapped.check())

    def test_the_window_guard_runs_for_batches_only_on_the_roles_providers(self) -> None:
        resets = datetime(2026, 11, 15, 14, 30).astimezone().isoformat()
        windows = [
            ports.Window("fake", "5h", 18_000, 0.91, resets),
            ports.Window("fake", "7d", 604_800, 0.40, resets),
            ports.Window("elsewhere", "5h", 18_000, 0.99, resets),
        ]
        fake = FakeHost(windows=windows)
        store = self.open(fake)
        batch = spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], batch=True, clock=lambda: NOW)
        stop = batch.check(12, 28)
        self.assertEqual(stop.kind, "window")
        self.assertEqual(stop.text(), "stopped: fake 5-hour window at 91%: 12 of 40 done, 28 not started; resets 14:30")
        self.assertEqual(fake.calls[-1], ("windows", ("fake",)))
        self.assertEqual(batch.window_use(), "fake 5-hour window at 91%, resets 14:30; fake weekly window at 40%, resets 14:30")
        batch.continue_past({"window"})
        self.assertIsNone(batch.check(13, 27))

        fake.calls.clear()
        single = spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], clock=lambda: NOW)
        self.assertIsNone(single.check())
        self.assertNotIn("windows", [call[0] for call in fake.calls])

        self.configure("window_stop = 0.95")
        relaxed = spend.Guard(store, self.profile, fake.host(), ["atlas_summarize"], batch=True, clock=lambda: NOW)
        self.assertIsNone(relaxed.check())

    def test_without_a_quota_port_the_guard_is_off_and_window_use_unknown(self) -> None:
        full = [ports.Window("fake", "5h", 18_000, 0.99, NOW.isoformat())]
        for label, fake in {"no quota port": FakeHost(windows=full, quota=False), "no host facts": FakeHost(windows=full, facts=False)}.items():
            with self.subTest(label):
                guard = spend.Guard(self.open(fake), self.profile, fake.host(), ["atlas_summarize"], batch=True, clock=lambda: NOW)
                self.assertIsNone(guard.check())
                self.assertEqual(guard.window_use(), "window use unknown")

    def test_the_batch_estimate_uses_medians_else_30k_in_and_8k_out(self) -> None:
        self.configure(tail=DEFAULT_PRICES.read_text())
        store = self.open(FakeHost())
        # No calls yet: 30K in and 8K out at $2 and $10 per million.
        self.assertEqual(spend.estimate_text(spend.estimate_item(store, self.profile, f"{SONNET}:high"), SONNET), "about $0.14 at list price")
        self.assertAlmostEqual(spend.estimate_item(store, self.profile, SONNET, page_tokens=100_000), 0.28)
        for tokens_in, tokens_out in ((10_000, 1_000), (20_000, 2_000), (90_000, 9_000)):
            spend.record_call(store, self.profile, "add", "atlas_summarize", summary(SONNET, tokens_in, tokens_out), now=NOW)
        self.assertAlmostEqual(spend.estimate_item(store, self.profile, SONNET), 0.06)
        self.assertIsNone(spend.estimate_item(store, self.profile, "other/model"))
        self.assertEqual(spend.estimate_text(None, "other/model:high"), "cost unknown: no price row for other/model")

    def test_stage_3_settings_default_and_bad_values_are_not_set_up(self) -> None:
        self.assertEqual(
            self.profile.limits(),
            {
                "max_page_tokens": 150_000,
                "judge_concurrency": 8,
                "rethink": True,
                "near_copy": 0.90,
                "reread_days": 30,
                "reread_new_text": 0.05,
                "cap_usd": None,
                "cap_warn": 0.80,
                "window_stop": 0.90,
            },
        )
        self.assertEqual(set(self.profile.confirm.values()), {"always"})
        for line in ("cap_warn = 1.5", "judge_concurrency = 0", "rethink = 1", "cap_usd = -5"):
            with self.subTest(line), self.assertRaises(config.NotSetUp) as caught:
                self.configure(line)
            self.assertIn(line.split(" ")[0], caught.exception.what)
        with self.assertRaises(config.NotSetUp):
            self.configure(tail='[prices."x"]\ninput = 1.0\n')


if __name__ == "__main__":
    unittest.main()
