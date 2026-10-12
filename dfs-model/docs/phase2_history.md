# Phase 2: refits on 2021-2025 (Oct 12, 2026)

Four settings refit on five seasons instead of one. **No default was changed.** This is the evidence for Doug and
Claude to decide what to adopt before week 7.

## Summary

| Setting | Current | 2021-2025 refit | Range, leaving one season out | Reading |
|---|---|---|---|---|
| DST: points per point of opponent implied total | -0.35 (plus +0.35 per $1,000 of salary) | -0.46 alone; -0.36 with the team's own expected margin at +0.07 | -0.48 to -0.42 alone | Current value holds. No historical salaries, so the salary term cannot be refit. |
| DST: the team's own scoring average | not used | +0.02 per point | 0.00 to +0.05 | Confirms dropping it. |
| Injury share, WR out (targets) | 80% to every RB/WR/TE pro rata | 93% reaches teammates: 77% to other WRs, 16% to RBs and TEs | 75% to 100% | The amount is about right. The routing is not: the model sends half of it to other positions. |
| Injury share, RB out (carries) | 80%, pro rata | 95%, almost all to other RBs | 92% to 96% | Low by about 15 points. |
| Injury share, RB out (targets) | 80%, pro rata | 70%, all of it to other RBs | 54% to 92% | The model sends about 8% to RBs and 72% to WRs and TEs. |
| Injury share, TE out (targets) | 80%, pro rata | 49%, nearly all to other TEs | 45% to 58% | High by about 30 points, and misrouted. Noisy (59 games). |
| Spread, RB | 1.376 | 1.36 | 1.34 to 1.41 | Holds. |
| Spread, TE | 1.0 | 1.22 | 1.20 to 1.22 | Too narrow now. |
| Spread, WR | 1.0 | 1.17 | 1.12 to 1.23 | Too narrow now. |
| Spread, QB | 1.0 | 1.15 | 1.11 to 1.19 | Too narrow now. |
| Calibration, slope above 16 | 0.28 | 0.36 | 0.32 to 0.41 | A little low when Vegas totals are in the projection. |
| Calibration, RB slope above 8 | 0.12 | 0.12 | 0.11 to 0.13 | Holds. |
| Calibration, knees | 16 and 8 | 10 and 0 fit best | same in every fold | No measurable gain in accuracy from moving them. |

The spread and calibration rows are from projections that use each game's Vegas total, which is how the weekly
model runs. Section 5 also gives them with league-average totals, which is how the current values were fit.

## 1. Data

Pulled from nflverse into `data/cache` with `python src/fetch_stats.py --seasons 2020-2025 --history`:

- `stats_player_week_<season>.csv`: the same file and 150 columns as the 2024 and 2025 files already in use.
  Re-downloading 2024 and 2025 gave byte-identical files.
- `stats_team_week_<season>.csv`: team totals by week, used to score DSTs.
- `schedule_<season>.csv`: one row per game with scores, `spread_line` and `total_line` (from nflverse `games.csv`).

I also pulled 2020, which was not asked for. It is used only as the prior season for the 2021 projections, so that
2021 is projected the same way as the other four seasons.

Regular-season coverage:

| Season | Weeks | Teams | Games | Player rows | QB/RB/WR/TE rows | Games missing spread, total or score |
|---|---|---|---|---|---|---|
| 2020 | 17 | 32 | 256 | 16,774 | 5,543 | 0 |
| 2021 | 18 | 32 | 272 | 18,128 | 5,866 | 0 |
| 2022 | 18 | 32 | 271 | 17,981 | 5,808 | 0 |
| 2023 | 18 | 32 | 272 | 17,806 | 5,801 | 0 |
| 2024 | 18 | 32 | 272 | 18,130 | 5,864 | 0 |
| 2025 | 18 | 32 | 272 | 18,540 | 6,037 | 0 |

2022 has 271 games because Buffalo at Cincinnati was cancelled. Every game has a team-stats row for both teams.

`data/cache` is not tracked in git, so the files live on this machine only; the command above rebuilds them.

## 2. Method

- **Seasons:** 2021 to 2025, weeks 4 to 18, the same weeks the current values were fit on.
- **Leave one season out:** every number in an "out of season" column grades a season with values fit on the other
  four. The range column is the spread of the five fits.
- **Recent seasons count more:** each season counts 0.75 times the one after it, so 2025 = 1.00, 2024 = 0.75,
  2023 = 0.56, 2022 = 0.42, 2021 = 0.32. Weighting matters little for the spread factors (unweighted within 0.03)
  and the calibration (0.39 unweighted against 0.36 above 16). It matters more for the injury shares, where 2025
  was a high year: a WR's share is 84% unweighted against 93%.
- **No historical FanDuel salaries or injury reports.** DSTs are scored from team stats, and an absence is a game
  with no stat row.

Everything is reproduced by `python src/fit_history.py --week 2026-w05` (about three minutes). Tables are written
to `weeks/history/`.

## 3. DST

2,238 team-games. Each DST is scored with FanDuel's rules from the team stats. Points allowed are the opponent's
score less what the opponent's own defence and special teams scored. League average comes out at 6.1 to 7.1 points
a game by season. Everything is measured against the week's average, as the model does against the slate average.

| Model | Coefficients | RMSE | r |
|---|---|---|---|
| Every DST the same | | 5.39 | |
| Current: -0.35 x opponent implied total | | 5.12 | 0.31 |
| Refit: opponent implied total | -0.46 | 5.11 | 0.31 |
| Refit: + own expected margin | -0.36 and +0.07 per point of margin | 5.11 | 0.31 |
| Refit: + own DST average so far that season | -0.45 and +0.02 | 5.11 | 0.31 |
| Refit: all three | -0.36, +0.07, 0.00 | 5.11 | 0.31 |

RMSE and r for the refits are out of season. By season, the slope on opponent implied total alone was -0.39,
-0.30, -0.47, -0.60 and -0.44 (2021 to 2025).

- **The opponent's implied total is the whole signal,** and it is a small one: it takes the error from 5.39 to
  5.11. Nothing added to it moves the error.
- **A DST's own scoring average predicts nothing** (+0.02 per point). That confirms the week-6 decision to drop
  the FanDuel-average term.
- **The salary term cannot be refit** because there are no historical salaries. On the 46 DSTs of weeks 4 and 5,
  salary is mostly a restatement of the lines: about 56% of its variation is the team's expected margin, and it
  falls about $130 per point of opponent implied total. So the current formula acts like about -0.40 per point
  of opponent total, between the two historical fits (-0.46 alone, -0.36 with the margin).
- **Current -0.35 costs nothing against the refit** (5.12 against 5.11).

## 4. Injury redistribution

What was measured. A starter is an RB, WR or TE who played each of his team's previous three games and averaged
at least 6 targets (WR), 4.5 targets (TE), or 10 carries or 3 targets (RB). The event is the first game he missed
that season, week 4 or later. The share is how much more the rest of the team's RBs, WRs and TEs got in that game
than they averaged in the games he played, divided by his own average. It is measured on team totals, so it
includes whoever replaced him.

| Player out | Volume | Games | His average | Share reaching teammates | To his own position | To other positions | Range | Model now: own / other |
|---|---|---|---|---|---|---|---|---|
| WR | Targets | 124 | 7.9 | 93% (±10) | 77% (±7) | 16% | 75% to 100% | 40% / 40% |
| RB | Carries | 105 | 14.2 | 95% (±5) | 94% (±4) | 1% | 92% to 96% | 70% / 10% |
| RB | Targets | 88 | 4.1 | 70% (±20) | 70% (±7) | 0% | 54% to 92% | 8% / 72% |
| TE | Targets | 59 | 6.0 | 49% (±20) | 46% (±9) | 4% | 45% to 58% | 6% / 74% |

± is one standard error. The last column is what the current rule does with its 80%: it splits it across every
RB, WR and TE in proportion to each player's own volume, so most of a TE's or an RB's targets go to the wide
receivers.

- **The total is not the problem.** For a WR or an RB's carries, 80% is if anything low.
- **The routing is the problem.** In the games themselves, a missing player's volume goes to his own position:
  77 of 93 points for a WR, all of it for an RB. The model sends half or more to other positions.
- **TEs are different.** Only about half of a missing TE's targets show up anywhere among the RBs, WRs and TEs.
  The total has a wide error (±20), but the 46% to other TEs is measured better (±9).
- Dropping week 18, when healthy starters are rested, changes little: 95%, 97%, 72% and 61%.

Limits. An absence is a missing stat row, not an injury report, so a healthy scratch or a suspension counts.
Only first absences are measured, which is the case the model hands out in full. Team totals cannot say which
teammate gained: much of the "own position" share goes to the direct backup, who often has almost no volume of
his own, and a pro-rata rule gives such a player very little whatever the share is.

What adopting this would take: a share by position of the player who is out, and a rule that sends most of it to
his own position. That is a code change in `usage.redistribute_out`, not a config value. Suggested starting
numbers, to be tested on weeks 4 to 6 first: WR out, 75% to WRs and 15% to RBs and TEs; RB out, 95% of carries
and 70% of targets to RBs; TE out, 45% to TEs and 5% to the rest.

## 5. Simulation spread

Share of players who beat their simulated 90th percentile (target 10%), with the current calibration applied.
"Refit" grades each season with a factor fit on the other four.

Projections using each game's Vegas total (how the model runs):

| Position | n | Current factor | Beat now | Refit factor | Range | Beat after refit |
|---|---|---|---|---|---|---|
| QB | 2,067 | 1.0 | 13.5% | 1.15 | 1.11 to 1.19 | 10.0% |
| RB | 3,365 | 1.376 | 9.9% (14.8% unwidened) | 1.36 | 1.34 to 1.41 | 9.8% |
| WR | 5,063 | 1.0 | 12.3% | 1.17 | 1.12 to 1.23 | 10.0% |
| TE | 1,698 | 1.0 | 13.2% | 1.22 | 1.20 to 1.22 | 9.9% |

With league-average totals (how the current RB factor was fit) the factors are QB 1.13, RB 1.33, WR 1.15, TE 1.24.

- **The RB factor adopted this morning holds on five seasons:** 1.36 against 1.376, and 9.9% coverage as it is.
- **Every other position is too narrow** by a smaller amount: about 12 to 13.5% beat the ceiling instead of 10%.
- **One factor per position over-widens the top players.** For players projected 16+, the share beating the
  ceiling is already near 10% unwidened (QB 10.3%, RB 12.3%, WR 7.8%) and falls to about 7% once the factor is
  applied (QB 7.1%, RB 6.9% with the current 1.376, WR 6.4%). The shortfall is among players projected under 16.
  This morning's 2025-only figure of 18% for RBs at 16+ does not hold up over five seasons.
- 2024 was the widest season: 16% of QBs and 14% of WRs beat their ceiling before any widening.

If spread factors are adopted for QB, WR and TE, the week-4 and week-5 lineup test from section 8 of
`docs/week6_prep.md` should be repeated first: widening TEs is likely to raise the TE-flex share again. A factor
that shrinks as the projection rises would fit better than a flat one and is not built.

## 6. Calibration

12,193 player-games. "Projected" and "actual" are weighted averages; RMSE is out of season for the refits.

Projections using each game's Vegas total:

| Calibration | All: projected / actual | 16+: projected / actual | 20+: projected / actual | RB 8+: projected / actual | RMSE, all |
|---|---|---|---|---|---|
| None | 11.76 / 11.02 | 19.85 / 17.89 | 22.90 / 20.36 | 13.73 / 12.57 | 7.32 |
| Current (16: 0.28, RB 8: 0.12) | 11.39 / 11.02 | 18.41 / 17.89 | 20.59 / 20.36 | 12.79 / 12.57 | 7.25 |
| Refit slopes, same knees (0.36, 0.12) | 11.32 / 11.02 | 18.10 / 17.89 | 20.03 / 20.36 | 12.71 / 12.57 | 7.25 |
| Refit knees and slopes (10: 0.19, RB 0: 0.03) | 11.08 / 11.02 | 17.79 / 17.89 | 20.27 / 20.36 | 12.55 / 12.57 | 7.25 |

Slopes leaving one season out: above 16, 0.32 to 0.41; RBs above 8, 0.11 to 0.13.

With league-average totals the refit slopes are 0.24 (0.22 to 0.29) and 0.14, and the current values leave the 16+
tier exactly unbiased (17.86 projected, 17.86 actual).

- **The calibration earns its place on five seasons.** Without it the 16+ tier is projected 2.0 points too high
  and the 20+ tier 2.5.
- **The current slope above 16 is a little low for the way the model runs.** Vegas totals push the top
  projections higher, and 0.28 leaves the 16+ tier half a point high (18.4 against 17.9). 0.36 leaves 0.2.
- **The RB slope holds** at 0.12.
- **Moving the knees does not improve accuracy.** The best-fitting knees are 10 for everyone and 0 for RBs, a
  gentler shrink that starts earlier, and every fold picks the same ones. It removes the remaining overall bias
  (11.08 against 11.02, where the current values leave 11.39). But RMSE is 7.25 in all three calibrated rows, so
  this is a choice about bias, not about error.
- No version changes RMSE by more than 0.07. Calibration fixes the level of the top projections; it does not make
  the ranking better.

## 7. To decide before week 7

1. **Injury routing** (section 4): the largest gap between the model and the data. It needs a code change and a
   test on weeks 4 to 6. Braelon Allen and Jaylen Warren in week 5 were this case.
2. **Spread for QB, WR and TE** (section 5): 1.15, 1.17, 1.22 as config values, after the lineup test. Or a
   factor that tapers at the top, which is more work.
3. **Calibration slope above 16** (section 6): 0.28 to about 0.36. A one-line config change; projections above 16
   come down by a further 8% of each point above 16.
4. **DST** (section 3): nothing to change.
5. **Calibration knees** (section 6): leave them unless the overall bias matters more than keeping projections
   under 16 untouched.

## Files

- `src/fetch_stats.py`: `--seasons` and `--history` options.
- `src/dfs/history.py`: lines and DST scoring from the schedule and team stats, starter absences, season weights.
- `src/fit_history.py`: runs all four refits. `src/dfs/backtest.py`: optional weights and Vegas totals in the
  season rows.
- `tests/test_history.py` (5 tests; 56 pass in total).
- `weeks/history/`: `coverage.csv`, `dst.csv`, `dst_by_season.csv`, `dst_fits.csv`, `absences.csv` (every event),
  `injury_share.csv`, `spread.csv`, `spread_fits.csv`, `calibration.csv`, `calibration_fits.csv`.
