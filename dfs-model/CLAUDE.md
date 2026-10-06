# CLAUDE.md — dfs-model

## What this is
Doug's FanDuel NFL DFS model for the **Sunday main-slate "Pooch Punt"** GPP ($0.05 entry, up to 150 entries, ~600k-entry field,
guaranteed overlay). Goal: maximize chance of top finishes, not average score. Built in a claude.ai chat Sept 30–Oct 4 2026
(Phase 1); this repo is where Phase 2 happens. Doug also runs a Benter-style horse racing model (separate repo, Authentic-66)
and thinks in those terms: fundamentals model + market/public overlay, calibration, backtesting.

## Contest scoring (FanDuel, verified from contest rules screenshot)
- Pass yd 0.04, pass TD 4, INT -1; rush/rec yd 0.1; rush/rec/return TD 6; reception 0.5 (half PPR); fumble lost -2; 2-pt 2.
- **Bonuses: +3 for 100+ rush yds, +3 for 100+ rec yds, +3 for 300+ pass yds.**
- DST: sack 1, INT 2, fumble rec 2, return TD 6, safety 2, blocked kick 2; points-allowed tiers (0:+10, 1-6:+7, 7-13:+4,
  14-20:+1, 21-27:0, 28-34:-1, 35+:-4). Points allowed counts only offensive TDs/2-pt/XP/FG allowed by the defense.
- Roster: QB, RB, RB, WR, WR, WR, TE, FLEX (RB/WR/TE), DEF. Cap $60,000. Max 4 players from one NFL team.
- **Upload CSV header must be exactly `QB,RB,RB,WR,WR,WR,TE,FLEX,DEF`** with FanDuel player Ids. pandas mangles duplicate
  headers (RB.1, WR.1) when re-reading a CSV — write with the csv module or fix the header (this broke an upload in week 4).

## Config (all rules and tunables live here, not in code)
- `config/defaults.toml` — rules that hold week to week: `[scoring]`, `[roster]`, `[teams]`, `[model.*]` (sim count/seed,
  league priors, noise, correlation, DST, injury handling, `[model.prior_blend]`), `[optimizer]` (Doug's standing rules:
  exposure cap, objective weight, overlap, starters depth, yellow/green formulas, default stack shape).
- `[ownership]` (model settings) and `[optimizer.leverage]` (off by default: `own_weight` points per 1% owned,
  `max_lineup_own`, `stack_exponent`) also live in defaults.toml; turn leverage on per week in week.toml.
- `config/<week>/week.toml` — deep-merged over defaults (any default can be overridden for one week): `[status]` OUT/Q,
  `[overrides]` Doug's reads, `[prefs]` red/red_teams/yellow/green/player_cap/starters_only, `[stacks.weights]` QB-team
  draw weights, `[stacks.rules.<TEAM>]` per-team stack shape (e.g. BUF: `receivers = 1`, `require = ["James Cook III"]`).
  `[contest]` field_size (for grading); `[contest.guru]` = FanDuel Guru (paid) suggestions pre-lock: per slot (QB, RB1,
  RB2, WR1-3, TE, FLEX, DEF) the 3 players Guru offered + Doug's pick, plus fill_order and adapts. All ~27 suggestions
  are the signal (Guru shows them to every paying user), not just the picks. Doug may send screenshots: transcribe them.
  Parsed/validated by `ownership.guru_table`.
  New week: copy last week's `week.toml` and edit.

## Pipeline (`src/` scripts are thin CLIs over the `src/dfs/` package; all take `--week`, default `$DFS_WEEK`)
- `dfs/config.py` — `Week` paths (data/, weeks/, config/, stats cache by season) and config loading.
- `dfs/scoring.py` — contest scoring from config; `stats_points` turns nflverse rows into FanDuel points (matches FanDuel
  FPPG exactly; tested) so any historical week can be graded.
- `dfs/data.py` — slate (status applied, or FanDuel Q/D tags until [status] is filled; missing FPPG -> 0), Vegas lines -> implied totals, nflverse stats (FanDuel team
  codes, all positions kept: Travis Hunter is listed as CB). `before_week` stops future weeks leaking into re-runs.
- `dfs/usage.py` — per-player totals keyed by name (name collisions like DJ Turner WR/CB resolved by player_id, offensive
  volume wins), prior-season blend, 80% redistribution of newly-OUT players' targets/carries, starting QB = most attempts
  in each team's latest game.
- `dfs/sim.py` + `dfs/project.py` (`model.py`) — implied totals -> usage x volume elasticity -> 10k correlated sims (team
  factor + shared game factor), Q players zeroed in 25% of sims, DST from opponent total + own FanDuel avg. Deterministic
  for a given seed (game order sorted; the old code depended on Python's hash seed).
- `dfs/overrides.py` (`override.py`) — rescale a player's sims to Doug's mean; errors on unknown names; idempotent.
- `dfs/optimize.py` (`optimize.py`) — sequential MILP (PuLP/CBC), one lineup per sim draw; objective 0.4*mean + 0.6*draw.
  Upload written with the csv module (exact duplicate header).
- `dfs/ownership.py` — projected field ownership (`Own_proj`, % of lineups): ridge on logit(%Drafted), refit every run
  from all earlier weeks' results (training rows cached in `weeks/<w>/ownership_train.csv`), shifted per position so
  QB/DST sum to 100%. Added in model.py, override.py (post-override) and optimize.py; also exposure.csv
  (`Own_proj_%`, `Exp_minus_Own`, plus 0-lineup players projected >= 5%) and stacks.csv. `fit_ownership.py` = CV report.
- `dfs/analyze.py` (`analyze_results.py`) — post-slate grading. `dfs/backtest.py` (`backtest.py`) — Phase 2 tuning;
  `backtest_leverage.py` — leverage settings on an archived slate.
- `fetch_stats.py` — nflverse stats for the week's season and the prior one.
- Tests: `python -m unittest discover -s tests` (stdlib unittest; scoring, usage/blend, ownership, week-4 regression checks).

## Doug's standing rules (current; confirm each week)
- **Starters only**: QB1 (week's starter), RB1, top-3 WR, TE1 per team by projection. Green-listed players always eligible.
- **Exposure cap 25 lineups** for every player and DST (Doug's choice to limit bust risk; raise to 40 only if infeasible).
- Stack per lineup: QB + >=2 of his WR/TE + >=1 bring-back from opponent. No DST facing your own offensive players.
- Pull questionable players rather than rely on late swap (he enters via CSV and won't hand-edit 150 lineups):
  `[optimizer] exclude_questionable = true` (default; week 4 sets false, it predates the rule). Before Friday's report
  (`[status]` lists both empty) FanDuel's own tags apply: O/IR out, Q/D = Q (excluded). Once `[status]` has entries,
  FanDuel's Q/D tags are ignored. Excluded Q/OUT players don't hold starter depth: RB1/top-3 WR/TE1 are ranked among
  eligible players, so backups move up (green exempt).
- If he has a free entry, upload 149 (drop lowest projected) and use the free entry separately.
- Weekly review loop: he color-codes `exposure.csv` in Excel — **red = exclude, yellow = less (cap at ~half current),
  green = more (min = max(2x current, 12))**. Two shades of green both mean "more". Lists live in `config/<week>/week.toml`
  `[prefs]`.
- When he wants more of a player the model projects low, prefer a projection override (ask his read) over forced exposure;
  forcing low-projected players cost ~5 points of average lineup projection in week 4.

## Week 4 (2026-w04) result — see docs/week4_review.md
149 model lineups + 1 FanDuel "Guru" lineup. Model avg 111.3 vs field 107.3; best 178.7 (rank 1,054 / 596,809, top 0.18%);
4 lineups in top 1%; winner 217.0. Guru lineup 93.0 (rank ~427k). Net +$2.35.
Calibration: rank-order fine (r = 0.68) but **overconfident at the top** (proj 20+: 23.4 projected vs 17.1 actual) — 3-week
hot starts inflate. DST projections ~uninformative (r = 0.24). Jaguars "contrarian" stack was actually chalk
(P. Washington 30% owned) and was our worst stack — we had no ownership model.

## Phase 2 roadmap (in priority order)
1. **Prior-season blend** — DONE Oct 5 (docs/phase2_prior_blend.md): usage 2 pseudo-games, efficiency 4 games of 2025.
   Week-4 RMSE 8.30 -> 8.08, 20+ tier gap +7.1 -> +4.2; also better on 2025 wks 4-18 (with 2024 prior). Residual
   structural bias (~+0.7 overall, ~+2 at 20+) remains — candidate: heavier TD-rate shrinkage, tuned with the same backtest.
2. **Ownership model** — DONE Oct 5 (docs/phase2_ownership.md). Week-4 CV MAE 3.2 pts (null 4.2), log-r 0.73. Misses
   mid-priced chalk (P. Washington 4.6% vs 30%, A. Jones 6% vs 40%) and QB ownership; would NOT have flagged the JAC
   stack. The FanDuel Guru lineup held 6 players owned 17-40% — candidate feature once 3+ weeks are recorded.
   Leverage OFF by default; week-4 backtest is noise-dominated (0.2 harmless, 1.0 costs ~10 pts of projection).
3. **Vegas-weighted stacks**: stack-team weights from implied totals instead of hand-set `[stacks.weights]` in week.toml.
4. Pass/rush defensive split adjustment (opponent yds allowed vs league avg, heavily shrunk). Doug supplied week-4 tables.
5. Better DST model; better starter detection (depth charts) instead of projection rank.
6. Backtest harness: re-run each archived week and score lineups vs actuals.

## Tech debt (honest)
Refactored Oct 5 into `src/dfs/` with config-driven rules. Verified: with the same hash seed the new projection code
reproduces the old model.py sims exactly (all 537 players x 10k draws), and the optimizer's pool, caps, green forcing and
stack-team draws match the old optimize.py exactly. Full optimizer run on 2026-w04 (Oct 5, blend off for comparability):
150 lineups, zero rule violations, 102 of 104 players shared with the archived run, exposure corr 0.97, stack counts
within a few lineups (exact match isn't possible: sims.npy wasn't archived). Known interaction (also in the old code): the
BUF rule requires Cook, so Cook's 25 cap is shared with non-BUF lineups and Josh Allen's green target of 25 lands at 21. Known gaps: starter detection misses teams whose last starter is
inactive (TB in week 4 had no starting QB flagged); the "raise exposure cap to 40 if infeasible" rule is manual
(`[optimizer] exposure_cap` in week.toml). Team codes: FanDuel JAC/LAR vs nflverse JAX/LA (`[teams]` in defaults.toml).
Vegas lines are entered by hand; three week-4 lines were estimates.
