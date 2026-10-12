"""Fit [model.opponent] on past seasons and report it out of sample. Rows: weeks 4-18 of each season, projected with
Vegas totals and the calibration in config. For each position the multiplier is 1 + beta * (tilt - 1), where tilt is
the defence's points allowed to that position relative to the league, divided by its overall level (dfs.opponent).
beta, shrink_games and prior_games are fit leave-one-season-out, recent seasons weighted more.
Also prints the double-counting check: what the defence's overall level adds to a projection that already has the
Vegas total. Changes nothing in config. Writes weeks/history/opponent.csv and opponent_fits.csv.
Needs `fetch_stats.py --seasons <first-1>-<last> --history` first."""
import itertools
import os

import numpy as np
import pandas as pd

from dfs import config, data, history as h, opponent, project

week, cfg, a = config.cli(__doc__, [
    (['--seasons'], dict(default='2021-2025')),
    (['--decay'], dict(type=float, default=0.75)),
    (['--rows-cache'], dict(default='')),
])
lo, hi = map(int, a.seasons.split('-'))
seasons = list(range(lo, hi + 1))
W = h.season_weights(seasons, a.decay)
m, sc = cfg['model'], cfg['scoring']
cap = m['opponent']['cap']
rows, _ = h.season_rows(week, cfg, seasons, vegas=True, cache_dir=a.rows_cache)
rows['Cal'] = project.calibrated(rows.Proj.values, rows.Pos.values, m['calibration'])
w = rows.season.map(W).values
allowed = {s: opponent.allowed(data.load_stats(week.stats(s), cfg), sc) for s in [lo - 1] + seasons}
GRID = list(itertools.product([2, 4, 8, 16], [0, 2, 4, 8]))     # (shrink_games, prior_games)


def lookup(k, kp):
    """tilt and overall ratio for every row under one (shrink_games, prior_games)."""
    t, r = np.ones(len(rows)), np.ones(len(rows))
    for (s, wk), idx in rows.groupby(['season', 'week']).groups.items():
        cur = allowed[s]
        tl = opponent.tilt(cur[cur.index.get_level_values('week') < wk], allowed[s - 1], dict(shrink_games=k, prior_games=kp))
        sub = rows.loc[idx]
        ok = sub.opp.isin(tl.index).values
        ix = np.asarray(idx)[ok]
        t[ix] = [tl.at[d, p] for d, p in zip(sub.opp[ok], sub.Pos[ok])]
        r[ix] = tl.ALL.reindex(sub.opp[ok]).values
    return t, r


tables = {g: lookup(*g) for g in GRID}
y = (rows.FPTS - rows.Cal).values
slope = lambda x, t: float((w[t] * x[t] * y[t]).sum() / (w[t] * x[t] ** 2).sum())
rmse = lambda e, t: float(np.sqrt(np.average(e[t] ** 2, weights=w[t])))


def fit(train):
    """Best (shrink_games, prior_games, beta) on the training rows: least weighted squared error, beta >= 0."""
    best = None
    for g in GRID:
        x = rows.Cal.values * (tables[g][0] - 1)
        b = max(slope(x, train), 0.0)
        sse = float((w[train] * (y[train] - b * x[train]) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, g, b)
    return best[1], best[2]


out, fits = [], []
for pos in opponent.POS:
    p = (rows.Pos == pos).values
    adj = np.zeros(len(rows))
    for s in seasons:
        tr, te = p & (rows.season != s).values, p & (rows.season == s).values
        g, b = fit(tr)
        f = np.clip(1 + b * (tables[g][0] - 1), 1 - cap, 1 + cap)
        adj[te] = rows.Cal.values[te] * (f[te] - 1)
        fits.append(dict(Pos=pos, held_out=s, shrink_games=g[0], prior_games=g[1], beta=b))
    g, b = fit(p)
    fits.append(dict(Pos=pos, held_out='none (all seasons)', shrink_games=g[0], prior_games=g[1], beta=b))
    t, r = tables[g]
    betas = [f['beta'] for f in fits if f['Pos'] == pos and f['held_out'] != 'none (all seasons)']
    by_season = [np.sqrt(np.mean((y[p & (rows.season == s).values] - adj[p & (rows.season == s).values]) ** 2))
                 - np.sqrt(np.mean(y[p & (rows.season == s).values] ** 2)) for s in seasons]
    out.append(dict(Pos=pos, n=int(p.sum()), rmse_without=rmse(y, p), rmse_with=rmse(y - adj, p), beta=b,
                    beta_range='%.2f to %.2f' % (min(betas), max(betas)), shrink_games=g[0], prior_games=g[1],
                    tilt_sd=float(np.std(t[p])), adj_typical=float(np.mean(np.abs(adj[p]))), adj_p95=float(np.percentile(np.abs(adj[p]), 95)),
                    adj_max=float(np.abs(adj[p]).max()), seasons_better=int(sum(d < 0 for d in by_season)),
                    # double-counting check: the defence's overall level, and the raw (undivided) ratio, on the same rows
                    beta_overall=slope(rows.Cal.values * (r - 1), p), beta_raw_ratio=slope(rows.Cal.values * (t * r - 1), p),
                    corr_tilt_overall=float(np.corrcoef(t[p], r[p])[0, 1])))
    rows.loc[p, 'adj'] = adj[p]
out, fits = pd.DataFrame(out), pd.DataFrame(fits)
pd.set_option('display.width', 250)
print(out.round(3).to_string(index=False))
print(fits.round(3).to_string(index=False))
allp = np.ones(len(rows), bool)
print('all positions: rmse without %.4f, with %.4f' % (rmse(y, allp), rmse(y - rows.adj.values, allp)))


# config holds one shrink_games / prior_games for every position: fit that version too, the same way
def fit_shared(train):
    best = None
    for g in GRID:
        x = rows.Cal.values * (tables[g][0] - 1)
        betas = {pos: max(slope(x, train & (rows.Pos == pos).values), 0.0) for pos in opponent.POS}
        pred = x * rows.Pos.map(betas).values
        sse = float((w[train] * (y[train] - pred[train]) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, g, betas)
    return best[1], best[2]


shared = np.zeros(len(rows))
for s in seasons:
    tr, te = (rows.season != s).values, (rows.season == s).values
    g, betas = fit_shared(tr)
    f = np.clip(1 + rows.Pos.map(betas).values * (tables[g][0] - 1), 1 - cap, 1 + cap)
    shared[te] = rows.Cal.values[te] * (f[te] - 1)
    fits = pd.concat([fits, pd.DataFrame([dict(Pos='shared', held_out=s, shrink_games=g[0], prior_games=g[1], **betas)])])
g, betas = fit_shared(allp)
print(f'one setting for all positions: shrink_games = {g[0]}, prior_games = {g[1]}, beta =', {k: round(v, 2) for k, v in betas.items()})
sh = pd.DataFrame([dict(Pos=pos, rmse_without=rmse(y, (rows.Pos == pos).values), rmse_with=rmse(y - shared, (rows.Pos == pos).values),
                        adj_typical=np.mean(np.abs(shared[(rows.Pos == pos).values])), adj_p95=np.percentile(np.abs(shared[(rows.Pos == pos).values]), 95),
                        adj_max=np.abs(shared[(rows.Pos == pos).values]).max(), beta=betas[pos]) for pos in opponent.POS]
                  + [dict(Pos='all', rmse_without=rmse(y, allp), rmse_with=rmse(y - shared, allp), adj_typical=np.mean(np.abs(shared)),
                          adj_p95=np.percentile(np.abs(shared), 95), adj_max=np.abs(shared).max())])
print(sh.round(3).to_string(index=False))
print(fits[fits.Pos == 'shared'].round(2).to_string(index=False))
sh.to_csv(os.path.join(week.root, 'weeks', 'history', 'opponent_shared.csv'), index=False)
out_dir = os.path.join(week.root, 'weeks', 'history')
out.to_csv(os.path.join(out_dir, 'opponent.csv'), index=False)
fits.to_csv(os.path.join(out_dir, 'opponent_fits.csv'), index=False)
