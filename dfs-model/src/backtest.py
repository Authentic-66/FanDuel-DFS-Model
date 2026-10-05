"""Phase 2 #1: tune [model.prior_blend] by backtest. Grades every (usage_games, efficiency_games) pair on
  (a) the archived slate for --week (full pipeline vs data/<week>/results_players.csv), and
  (b) weeks 4-18 of --season (projections from earlier weeks + prior-season blend vs actual FanDuel points).
Writes weeks/<week>/backtest_prior_blend_slate.csv and _season.csv / _season_weekly.csv."""
import pandas as pd

from dfs import backtest as bt, config

week, cfg, a = config.cli(__doc__, [
    (['--usage'], dict(default='0,1,2,3,4,6,8,12,16', help='usage_games grid')),
    (['--efficiency'], dict(default='0,2,4,8,12,16,24,32', help='efficiency_games grid')),
    (['--season'], dict(type=int, default=2025, help='season for the multi-week check (needs it and the prior in cache)')),
    (['--exclude'], dict(default='', help='comma-separated names to drop from slate grading (e.g. in-game injuries)')),
])
nums = lambda s: [float(x) for x in s.split(',')]
settings = bt.grid(nums(a.usage), nums(a.efficiency))
pd.set_option('display.width', 250)
cols = ['usage_games', 'efficiency_games', 'n', 'r', 'rmse', 'bias', 'slope', 'gap_14+', 'gap_20+', 'over_p90']

slate, _ = bt.slate_backtest(week, cfg, settings, exclude=[n for n in a.exclude.split(',') if n])
slate.to_csv(week.output('backtest_prior_blend_slate.csv'), index=False)
print(f'== {week.name} slate (graded n={slate.n[0]}), best 10 by RMSE')
print(slate.sort_values('rmse')[cols].head(10).round(3).to_string(index=False))

season, weekly = bt.season_backtest(week.stats(a.season), week.stats(a.season - 1), cfg, settings, weeks=range(4, 19))
season.to_csv(week.output('backtest_prior_blend_season.csv'), index=False)
weekly.to_csv(week.output('backtest_prior_blend_season_weekly.csv'), index=False)
print(f'\n== {a.season} weeks 4-18 pooled (n={season.n[0]}), best 10 by RMSE')
print(season.sort_values('rmse')[cols].head(10).round(3).to_string(index=False))
