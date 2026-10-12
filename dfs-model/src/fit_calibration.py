"""Fit [model.calibration] (shrink of the top projections and of RBs above 8) and report it out of sample.
Rows: every week 4-18 of --season (projections from earlier weeks + prior blend, neutral team totals) plus each archived
slate in --slates (the real pipeline vs data/<week>/results_players.csv). Slopes are fit leave-one-week-out, so no
week is graded with slopes that saw it. Writes weeks/<week>/calibration_cv.csv and calibration_fit.csv."""
import numpy as np
import pandas as pd

from dfs import backtest as bt, config

week, cfg, a = config.cli(__doc__, [
    (['--season'], dict(type=int, default=2025)),
    (['--slates'], dict(default='2026-w04,2026-w05', help='archived slates with results, comma-separated')),
])
cal = cfg['model']['calibration']
rows = pd.concat([bt.season_rows(week.stats(a.season), week.stats(a.season - 1), cfg, range(4, 19))]
                 + [bt.slate_rows(config.current_week(w), config.load_config(config.current_week(w)))
                    for w in a.slates.split(',') if w])
cv, fits = bt.calibration_cv(rows, cal['top_knee'], cal['rb_knee'])
rmse = lambda d, c: np.sqrt(np.mean((d[c] - d.FPTS) ** 2))
tiers = {'all': cv.Proj > -1, 'proj 20+': cv.Proj >= 20, 'RB 8+': (cv.Pos == 'RB') & (cv.Proj >= 8)}
out = []
for src, s in [(f'{a.season} wk 4-18', cv.fold.str.startswith(str(a.season)))] + [(w, cv.fold == w) for w in a.slates.split(',') if w]:
    for tier, t in tiers.items():
        d = cv[s & t]
        out.append(dict(rows=src, tier=tier, n=len(d), proj=d.Proj.mean(), cal=d.Cal.mean(), actual=d.FPTS.mean(),
                        rmse_before=rmse(d, 'Proj'), rmse_after=rmse(d, 'Cal')))
out = pd.DataFrame(out)
pd.set_option('display.width', 250)
print(out.round(3).to_string(index=False))
final = bt.fit_calibration(rows, cal['top_knee'], cal['rb_knee'])
print('\nleave-one-week-out slopes: top %.3f-%.3f, rb %.3f-%.3f' % (fits.top_slope.min(), fits.top_slope.max(),
                                                                  fits.rb_slope.min(), fits.rb_slope.max()))
print('fit on all rows ([model.calibration]): top_slope = %.3f, rb_slope = %.3f' % (final['top_slope'], final['rb_slope']))
out.to_csv(week.output('calibration_cv.csv'), index=False)
fits.to_csv(week.output('calibration_fit.csv'), index=False)
