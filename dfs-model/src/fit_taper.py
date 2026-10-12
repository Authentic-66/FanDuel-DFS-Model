"""Fit [model.spread] as tapered factors {low, top} per position on past seasons (Vegas totals, the calibration in
config applied mean-only), leave-one-season-out with recent seasons weighted more, and report the share of players
beating their simulated 90th percentile by position and tier: unwidened, with the spread in config, with one flat
factor per position, and tapered. Changes nothing in config. Writes weeks/history/taper.csv and taper_fits.csv.
Needs `fetch_stats.py --seasons <first-1>-<last> --history` first."""
import json
import os

import numpy as np
import pandas as pd

from dfs import backtest as bt, config, history as h, project

week, cfg, a = config.cli(__doc__, [
    (['--seasons'], dict(default='2021-2025')),
    (['--decay'], dict(type=float, default=0.75)),
    (['--top-slope'], dict(type=float, default=None, help='calibration slope above the knee (default: config)')),
    (['--from'], dict(type=float, default=12.0, dest='lo', help='projection up to which `low` applies')),
    (['--to'], dict(type=float, default=20.0, dest='hi', help='projection from which `top` applies')),
    (['--rows-cache'], dict(default='')),
    (['--json'], dict(default='', help='also write the fitted spec to this file')),
])
lo, hi = map(int, a.seasons.split('-'))
seasons = list(range(lo, hi + 1))
W = h.season_weights(seasons, a.decay)
m = cfg['model']
cal = dict(m['calibration'], **({'top_slope': a.top_slope} if a.top_slope is not None else {}))
taper = {'from': a.lo, 'to': a.hi}
rows, sims = h.season_rows(week, cfg, seasons, vegas=True, cache_dir=a.rows_cache)
rows['Cal'] = project.calibrated(rows.Proj.values, rows.Pos.values, cal)
sims = sims + (rows.Cal - rows.Proj).values[:, None].astype(np.float32)      # mean-only calibration
w = rows.season.map(W).values
TIERS = [('all', 0, 99), ('under 8', 0, 8), ('8-16', 8, 16), ('16+', 16, 99), ('20+', 20, 99)]
out, fits, spec_all = [], [], {}
for pos in ['QB', 'RB', 'WR', 'TE']:
    keep = (rows.Pos == pos).values
    x, r, wp = sims[keep], rows[keep].reset_index(drop=True), w[keep]
    mean, act = r.Cal.values, r.FPTS.values
    p90 = {'unwidened': np.percentile(x, 90, axis=1),
           'config': h.taper_p90(x, mean, m.get('spread', {}).get(pos, 1.0), m.get('spread_taper')),
           'flat': np.zeros(len(r)), 'tapered': np.zeros(len(r))}
    for s in seasons:
        tr, te = (r.season != s).values, (r.season == s).values
        k = bt.fit_spread(x[tr], act[tr], weights=wp[tr])
        spec = h.fit_taper(x[tr], mean[tr], act[tr], wp[tr], taper)
        p90['flat'][te] = h.taper_p90(x[te], mean[te], k, taper)
        p90['tapered'][te] = h.taper_p90(x[te], mean[te], spec, taper)
        fits.append(dict(Pos=pos, held_out=s, flat=k, **spec))
    spec_all[pos] = h.fit_taper(x, mean, act, wp, taper)
    fits.append(dict(Pos=pos, held_out='none (all seasons)', flat=bt.fit_spread(x, act, weights=wp), **spec_all[pos]))
    for tier, a0, a1 in TIERS:
        t = (mean >= a0) & (mean < a1)
        if t.sum() >= 50:
            out.append(dict(Pos=pos, tier=tier, n=int(t.sum()), **{c: np.average(act[t] > q[t], weights=wp[t]) * 100 for c, q in p90.items()},
                            p90_unwidened=np.average(p90['unwidened'][t], weights=wp[t]), p90_tapered=np.average(p90['tapered'][t], weights=wp[t])))
out, fits = pd.DataFrame(out), pd.DataFrame(fits)
pd.set_option('display.width', 250)
print(f"calibration {cal}; taper from {a.lo} to {a.hi}; share beating the simulated 90th percentile, % (target 10)")
print(out.round(1).to_string(index=False))
print(fits.round(3).to_string(index=False))
print('[model.spread]', json.dumps(spec_all), '[model.spread_taper]', json.dumps(taper))
out_dir = os.path.join(week.root, 'weeks', 'history')
os.makedirs(out_dir, exist_ok=True)
out.to_csv(os.path.join(out_dir, 'taper.csv'), index=False)
fits.to_csv(os.path.join(out_dir, 'taper_fits.csv'), index=False)
if a.json:
    json.dump({'spread': spec_all, 'spread_taper': taper}, open(a.json, 'w'))
