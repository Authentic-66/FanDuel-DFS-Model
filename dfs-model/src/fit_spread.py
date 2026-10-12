"""Fit [model.spread] (how much wider a position's simulated draws should be) and report it out of sample.
Rows: every week 4-18 of --season (projections from earlier weeks + prior blend, neutral team totals), with the
calibration applied as in the model (mean only, slopes leave-one-week-out). The factor is the smallest one at which
10% of the position's players beat their simulated 90th percentile, fit leave-one-week-out.
Writes weeks/<week>/spread_cv.csv and spread_fit.csv."""
import numpy as np
import pandas as pd

from dfs import backtest as bt, config

week, cfg, a = config.cli(__doc__, [
    (['--season'], dict(type=int, default=2025)),
    (['--slates'], dict(default='2026-w04,2026-w05', help='archived slates used for the calibration slopes only')),
    (['--positions'], dict(default='RB', help='positions to widen, comma-separated; the rest are reported as they are')),
])
cal = cfg['model']['calibration']
rows, sims = bt.season_rows(week.stats(a.season), week.stats(a.season - 1), cfg, range(4, 19), keep_sims=True)
slates = [bt.slate_rows(config.current_week(w), config.load_config(config.current_week(w))) for w in a.slates.split(',') if w]
cv, _ = bt.calibration_cv(pd.concat([rows] + slates, ignore_index=True), cal['top_knee'], cal['rb_knee'])
rows['Cal'] = cv.Cal.loc[rows.index]
sims = sims + (rows.Cal - rows.Proj).values[:, None]     # mean-only calibration: every draw moves with the mean

widened = a.positions.split(',')
tiers = [('all', 0, 99), ('under 8', 0, 8), ('8-16', 8, 16), ('16+', 16, 99)]
out, fits = [], []
for pos in ['QB', 'RB', 'WR', 'TE']:
    d, f = bt.spread_cv(rows, sims, pos)
    k_all = bt.fit_spread(sims[(rows.Pos == pos).values], d.FPTS.values)
    fits.append(f.assign(Pos=pos, k_all_weeks=k_all, applied=pos in widened))
    for tier, lo, hi in tiers:
        t = d[(d.Proj >= lo) & (d.Proj < hi)]
        if len(t) >= 20:
            out.append(dict(Pos=pos, tier=tier, n=len(t), before=np.mean(t.FPTS > t.P90) * 100,
                            after=np.mean(t.FPTS > (t.P90_wide if pos in widened else t.P90)) * 100,
                            if_fit=np.mean(t.FPTS > t.P90_wide) * 100, p90_before=t.P90.mean(), p90_wide=t.P90_wide.mean()))
out, fits = pd.DataFrame(out), pd.concat(fits)
pd.set_option('display.width', 250)
print(out.round(1).to_string(index=False))
print(fits.groupby('Pos').agg(k_min=('k', 'min'), k_max=('k', 'max'), k_all_weeks=('k_all_weeks', 'first')).round(3))
out.to_csv(week.output('spread_cv.csv'), index=False)
fits.to_csv(week.output('spread_fit.csv'), index=False)
