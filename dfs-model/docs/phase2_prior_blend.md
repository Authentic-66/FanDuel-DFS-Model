# Phase 2 #1 — Prior-season blend (Oct 5, 2026)

**Adopted: `usage_games = 2`, `efficiency_games = 4`** (`config/defaults.toml` `[model.prior_blend]`; set both to 0 to turn off).

## What it does
Before simulating, each player's 2026 numbers get 2025 mixed in (players with >= 4 games in 2025; rookies unchanged):
- **Usage** (targets, carries, pass attempts per game): add 2 pseudo-games at the player's 2025 per-game rate.
  After 3 games that is 60% 2026 / 40% 2025; after 10 games, 83% / 17%. The prior fades on its own as the season grows.
- **Efficiency** (yds/TDs/catches per opportunity): add 4 games' worth of 2025 opportunities and outcomes, then the
  existing shrink to league priors applies on top.
- `team_change_weight` (discount for players who changed teams) was tested at 0 / 0.5 / 1; no gain, so it stays 1.0.

## Backtests (`python src/backtest.py --week 2026-w04`; CSVs in `weeks/2026-w04/backtest_prior_blend_*.csv`)
Graded set: skill players averaging >= 5 FanDuel pts/g before the week (model-independent). `slope` = OLS slope of actual
on projected (1 = calibrated, < 1 = projections too spread out, i.e. overconfident). `gap 20+` = mean projected minus mean
actual for players projected 20+.

| Test | Setting | RMSE | r | slope | bias | gap 20+ |
|---|---|---|---|---|---|---|
| **2026 wk 4 slate** (n=127, full pipeline vs FanDuel results) | none | 8.30 | .424 | 0.60 | +2.0 | +7.1 |
| | **2 / 4** | **8.08** | .434 | 0.66 | +1.7 | +4.2 |
| wk 4 excl. 6 in-game injuries (n=122) | none | 8.26 | .421 | 0.59 | +1.9 | +7.4 |
| | **2 / 4** | **7.94** | .443 | 0.66 | +1.5 | +4.2 |
| **2025 wks 4–18** (n=2,378; earlier weeks + 2024 prior vs actual FD pts) | none | 7.36 | .524 | 0.91 | +0.7 | +2.2 |
| | **2 / 4** | **7.32** | .530 | 0.95 | +0.7 | +2.2 |
| 2025 wks 4–6 only (early season, like now) | none | 7.08 | | 0.92 | | +2.3 |
| | **2 / 4** | **7.02** | | 0.98 | | +1.8 |

The analyze_results-style table on week 4 (all graded skill players, model projections before Doug's overrides):

| Proj tier | none: proj / actual | 2/4 blend: proj / actual |
|---|---|---|
| 8–14 | 10.6 / 8.8 | 10.1 / 8.7 |
| 14–20 | 17.0 / 14.9 | 16.9 / 14.1 |
| 20+ | 23.8 / 16.7 | 22.6 / 19.2 |

Why 2/4 and not the week-4 optimum (3/4, RMSE 8.067 vs 8.077): the surface is flat across usage 2–6 / efficiency 4–16 on
week 4, and 2/4 is also within 0.002 of the best on the 15-week 2025 test, so it is the robust choice. One slate is ~130
correlated outcomes; picking its exact optimum would be fitting noise.

## What it does and doesn't fix
- It agrees with Doug's reads without being told: Nacua 15.2 -> 20.3 (Doug's override 20.5, "2025 level"),
  McCaffrey 18.4 -> 20.9 (Doug 21.0). Biggest cuts are 3-week hot starts: K. Walker 27.8 -> 21.0, Bowers 22.5 -> 16.1,
  Golden 14.8 -> 10.6, Tuten 13.8 -> 10.4.
- **Week 4 was unusually bad.** Its slope (0.60) is lower than every one of the 15 weeks of 2025 (min 0.62, median 0.92)
  and its 20+ gap (+7.1) was matched by one 2025 week. Expect future weeks to look more like the 2025 numbers.
- **Remaining bias, not fixed by the blend:** about +0.7 pts overall and +2 pts in the 20+ tier persist across 2025 with or
  without it, so it is structural (sim mechanics or TD rates), not hot starts. Worth a look before or alongside the
  ownership model: try heavier TD-rate shrinkage (`[model.priors]` k values) by the same backtest.
- The 2025 test uses league-average team totals (no archived lines), so it checks the usage/efficiency estimate, not the
  Vegas layer.
