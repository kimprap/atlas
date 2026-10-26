# Atlas v1 notes (summary)

Six notes the user collected while maintaining Atlas v1, triaged against `~/dev/atlas/app` on 2026-10-19.

| Note | Still applies? | Where it went |
|---|---|---|
| 1. Eval loop | Idea yes; v1 plan no | Map fog: how summaries and search results are judged |
| 2. Legacy `TOPICS.md` repair | No | Dropped (old vault out of scope) |
| 3. Taxonomy closure | Fix no; lessons yes | Ticket 06 lessons |
| 4. SEO frontend stack topic | Yes, as an example | Ticket 02 |
| 5. TradingView topic | Yes, as an example | Ticket 02 |
| 6. Link cleanup, daily sourcing, `last30days` | Yes | Tickets 02 and 06; map fog (source identity) |

## Notes

1. **Eval loop.** Asked for a manual Atlas evaluation loop: existing calibration assets, read-only evaluation, disposable-instance mutation cases, baseline-versus-candidate comparison; no scheduling or automatic changes. The v1 plan (`.agents/plans/archive/2026-07-29-2056_atlas-evaluation-loop.md`) is PENDING, never run, and tied to v1 fixtures; the idea survives as the map's open quality item.
2. **Legacy `TOPICS.md` repair.** Asked to migrate seven old semicolon-list cells in `TOPICS.md` and validate the registry. Obsolete: the old vault is frozen and repairing it is out of scope.
3. **Taxonomy closure.** Diagnosed legacy sources whose labels were missing from `VOCAB.md`, which blocked research on every new topic and produced errors that hid the offending label. Already fixed in v1; v2 drops fixed labels. Lessons kept in ticket 06: one bad source never blocks every search, and every error names the source and field at fault.
   - Pointer: `~/dev/atlas/app/.agents/plans/archive/2026-08-23-1557_atlas-taxonomy-closure.md` (DONE 2026-08-24; commit `890f17c`).
4. **SEO frontend stack topic.** Asked to create topic `seo-lean-frontend-stack` and publish a first research draft. Kept as an example workload in ticket 02: a topic built from a multi-criteria brief and refined later.
5. **TradingView topic.** Asked for a technical-trading research topic, created only after agreeing its name and domain. Kept as an example workload in ticket 02: agree on a topic's name and scope before creating it.
6. **Link cleanup, daily sourcing, `last30days`.** Asked that tracking suffixes such as X's `s=<int>` be stripped while keeping links valid, and that an unchanged re-added link not be summarized again; a list of topics for daily sourcing; and how to use `last30days`. v1 already strips X `s=<digits>` and dedups by canonical URL plus content hash. Duplicates, scheduled discovery, and `last30days` as a discovery source went to ticket 02; how `last30days` plugs in went to ticket 06; identity rules stay in the map fog.

## Criteria from note 4: lean SEO frontend stack

Recommend the most robust, lean, mature frontend stack for SEO. Optimize for:

- page-load speed;
- SEO customization;
- modularity (not locked to one dependency or one UI kit);
- multiple mature UI component systems;
- modern CSS (radius, padding, hierarchy);
- information design that matches human scanning (e.g. a details card is not a flat list);
- easy micro-transitions/motion.

One combined topic; do not create a separate UI/UX/motion topic first. Motion and hierarchy are selection criteria for the stack. Iterate later.

## Criteria from note 5: TradingView technical-analysis setup

Use a TradingView account for backtesting, its data, or Pine Script. Requirements:

- only these technical-analysis tools: candlestick price patterns across timeframes, MACD, RSI, stochastic RSI;
- medium- to long-term analysis, not high-frequency;
- larger timeframes take precedence: M > W > 2D > D > 2hr > 30m;
- multiple decision engines, one per tool or per combination of tools;
- engines are modular and can be backtested independently;
- engine decisions are aggregated with varying weights;
- a backtest framework that supports an autoresearch loop to find the best tool configuration/pattern meeting a specified success threshold, each loop adjusting the tools above.

Create the topic only after the name and domain are agreed.
