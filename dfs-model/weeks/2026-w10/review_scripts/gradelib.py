import os, csv
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
R = r'D:\FanDuel-DFS\dfs-model-starter\FanDuel-DFS Model\dfs-model'
_cache = {}


def prizes(wk):
    p = os.path.join(R, 'data', wk, 'prizes_pooch-punt.csv')
    if not os.path.exists(p):
        p = os.path.join(R, 'data', '2026-w09', 'prizes_pooch-punt.csv')   # weeks 5-8: week-9 table (as in week9_review s7)
    t = pd.read_csv(p).sort_values('rank_from')
    out = np.zeros(int(t.rank_to.max()))
    for r in t.itertuples():
        out[int(r.rank_from) - 1:int(r.rank_to)] = r.prize
    return out


def week_data(wk):
    if wk not in _cache:
        f = pd.read_csv(os.path.join(HERE, 'out', wk + '_field.csv'), usecols=['Points'])
        pts = pd.read_csv(os.path.join(HERE, 'out', wk + '_pts.csv'))
        _cache[wk] = (np.sort(f.Points.fillna(0).values)[::-1], dict(zip(pts.Id, pts.FPTS)), prizes(wk))
    return _cache[wk]


def score(wk, lineups):
    _, act, _ = week_data(wk)
    return np.array([sum(act.get(i, 0.0) for i in lp) for lp in lineups])


def grade(wk, lineups, fee=0.05):
    field, act, pr = week_data(wk)
    pts = score(wk, lineups)
    neg = -field
    n = len(field)
    won, ranks = [], []
    for s in pts:
        above = int(np.searchsorted(neg, -s - 1e-6, side='left'))
        tied = int(np.searchsorted(neg, -s + 1e-6, side='right')) - above + 1
        places = np.arange(above, above + tied)
        paid = places[places < len(pr)]
        won.append(float(pr[paid].sum() / tied) if len(paid) else 0.0)
        ranks.append(above + 1)
    ranks = np.array(ranks)
    w = float(np.sum(won))
    return dict(lineups=len(pts), avg=round(pts.mean(), 1), cash_rate=round((ranks <= len(pr)).mean() * 100, 1),
                cashed=int((ranks <= len(pr)).sum()), won=round(w, 2), net=round(w - fee * len(pts), 2),
                top10=int((ranks <= 0.10 * n).sum()), top1=int((ranks <= 0.01 * n).sum()),
                best=round(pts.max(), 1), best_rank=int(ranks.min()))


def read_upload(path):
    rows = list(csv.reader(open(path)))
    return [r[:9] for r in rows[1:] if r]


def archived(wk, sub=''):
    """(lineups, Proj) of an archived set: weeks/<wk>/<sub>/upload.csv + readable.csv."""
    d = os.path.join(R, 'weeks', wk, sub)
    up = read_upload(os.path.join(d, 'upload.csv'))
    rd = pd.read_csv(os.path.join(d, 'readable.csv'))
    return up, rd.Proj.values


def rebuilt(wk, label):
    p = os.path.join(HERE, 'out', 'builds', f'{wk}__{label}.csv')
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, dtype=str)
    return d.iloc[:, :9].values.tolist(), d.Proj.astype(float).values


def drop_lowest(lineups, proj):
    k = int(np.argmin(proj))
    return [lp for j, lp in enumerate(lineups) if j != k]
