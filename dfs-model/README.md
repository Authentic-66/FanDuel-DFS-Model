# dfs-model

FanDuel NFL GPP lineup model (Pooch Punt, 150-entry max). Simulation-based projections, correlated stacks, MILP optimizer.
Sibling project to the Benter racing model; same philosophy: fundamentals model + market overlay, validated by backtests.

## Weekly run
```bash
pip install -r requirements.txt
export DFS_WEEK=2026-w05                # folder name used everywhere (or pass --week 2026-w05 to any script)
python src/fetch_stats.py               # refresh nflverse stats (this season + last) into data/cache
# inputs in data/$DFS_WEEK/: fd_players.csv (FanDuel players list), lines.csv (spreads/totals)
# settings: copy config/<last week>/week.toml to config/$DFS_WEEK/week.toml and edit status, overrides, prefs, stacks
python src/model.py                     # projections + 10k sims  -> weeks/$DFS_WEEK/proj.csv, sims.npy
                                        #   (+ Own_proj: field ownership fit on earlier weeks' results)
python src/override.py                  # apply Doug's projection reads
python src/optimize.py                  # 150 lineups -> upload.csv, readable.csv, exposure.csv (+ Own_proj_%), stacks.csv
# after the slate: save results files in data/$DFS_WEEK/ and run
python src/analyze_results.py
python src/fit_ownership.py             # ownership model fit report incl. this week's results
```
Rules and tunables: `config/defaults.toml` (week to week) and `config/<week>/week.toml` (this week; overrides defaults).

## Tests and backtests
```bash
python -m unittest discover -s tests             # scoring, usage/blend, week-4 regression checks
python src/backtest.py --week 2026-w04           # prior-blend grid on the slate + 2025 weeks 4-18 (needs 2024 stats cached)
python src/backtest_leverage.py --week 2026-w04  # leverage settings on an archived slate (~20 min; one slate = a sketch)
```
See CLAUDE.md for rules, scoring, and the Phase 2 roadmap; docs/ for weekly reviews and Phase 2 write-ups.
