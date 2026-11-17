"""Running paper table (Doug, Nov 16): every set built each week, graded as if entered on its own, full set and its
20 highest-projected lineups, weeks 5 onward. Money is exact (each lineup ranked against every entry in the All
Entries export, ties split) with data/<week>/prizes_pooch-punt.csv (weeks without one use the latest earlier table:
weeks 5-8 use week 9's, as in docs/week9_review.md s7).

    python src/paper_results.py                 # every week with an export in data/<week>/raw/
    python src/paper_results.py --rebuild 2026-w11   # re-read that week's export (after replacing it)

Sets: weeks/<week>/<folder>/upload.csv + readable.csv (Proj ranks the top 20; median builds rank by median), plus
weeks/<week>/paper/<set>.csv (sets rebuilt on paper later: 9 Ids + Proj). The entered set is graded as it was
entered (149 to week 10, entry_20 from week 11).
Writes docs/paper_results.csv (one row per week x set x full/top20) and docs/paper_results.md (summary tables).
The export is read once per week and cached in data/<week>/raw/ (field_points.npy, player_points.csv)."""
import argparse
import csv
import glob
import os
import re

import numpy as np
import pandas as pd

from dfs import config

ROOT = config.ROOT
SETS = [('model', ''), ('model_cap45', 'model_cap45'), ('flex_shadow', 'flex_shadow'), ('nodraw', 'nodraw'),
        ('median70_injcap', 'median70'), ('median70_plain', 'median70_plain'), ('median70_v1', 'median70_v1'),
        ('median70_v2', 'median70_v2'), ('median70_v3', 'median70_v3'), ('pool', 'pool')]
TOP = 20
FEE = 0.05


def md_table(df):
    """Markdown table without the tabulate package."""
    fmt = lambda v: f'{v:.2f}' if isinstance(v, float) else ('' if v is None else str(v))
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    for r in df.itertuples(index=False):
        out.append('| ' + ' | '.join('' if (isinstance(v, float) and np.isnan(v)) else fmt(v) for v in r) + ' |')
    return '\n'.join(out)


def weeks():
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, 'data', '2026-w*'))):
        w = os.path.basename(d)
        if int(w[-2:]) >= 5 and export(w):
            out.append(w)
    return out


def export(w):
    files = [f for f in glob.glob(os.path.join(ROOT, 'data', w, 'raw', '*.csv'))
             if 'hail_mary' not in os.path.basename(f).lower() and os.path.basename(f) != 'player_points.csv']
    return max(files, key=os.path.getsize) if files else None


def field(w, rebuild=False):
    raw = os.path.join(ROOT, 'data', w, 'raw')
    fp, pp = os.path.join(raw, 'field_points.npy'), os.path.join(raw, 'player_points.csv')
    if rebuild or not (os.path.exists(fp) and os.path.exists(pp)):
        e = pd.read_csv(export(w), encoding='utf-8-sig', usecols=['EntryId', 'Points', 'Player', 'FPTS'], low_memory=False)
        pts = np.sort(e.dropna(subset=['EntryId']).Points.fillna(0).values)[::-1]
        np.save(fp, pts)
        pl = e.dropna(subset=['Player'])
        pd.DataFrame({'Id': pl.Player.str.extract(r'\((\d+-\d+)\)$')[0], 'FPTS': pl.FPTS.astype(float)}).to_csv(pp, index=False)
    pl = pd.read_csv(pp)
    return np.load(fp), dict(zip(pl.Id, pl.FPTS))


def prizes(w):
    tables = sorted(glob.glob(os.path.join(ROOT, 'data', '2026-w*', 'prizes_pooch-punt.csv')))
    own = os.path.join(ROOT, 'data', w, 'prizes_pooch-punt.csv')
    earlier = [t for t in tables if os.path.basename(os.path.dirname(t)) <= w]
    path = own if os.path.exists(own) else (max(earlier) if earlier else min(tables))   # weeks 5-8: week 9's
    t = pd.read_csv(path).sort_values('rank_from')
    out = np.zeros(int(t.rank_to.max()))
    for r in t.itertuples():
        out[int(r.rank_from) - 1:int(r.rank_to)] = r.prize
    return out, os.path.basename(os.path.dirname(path))


def grade(lineups, fld, act, pr):
    pts = np.array([sum(act.get(i, 0.0) for i in lp) for lp in lineups])
    neg, n = -fld, len(fld)
    won, rk = 0.0, []
    for s in pts:
        above = int(np.searchsorted(neg, -s - 1e-6, side='left'))
        tied = int(np.searchsorted(neg, -s + 1e-6, side='right')) - above + 1
        places = np.arange(above, above + tied)
        paid = places[places < len(pr)]
        won += float(pr[paid].sum() / tied) if len(paid) else 0.0
        rk.append(above + 1)
    rk = np.array(rk)
    return dict(lineups=len(pts), avg=round(pts.mean(), 1), cashed=int((rk <= len(pr)).sum()),
                cash_rate=round((rk <= len(pr)).mean() * 100, 1), won=round(won, 2),
                net=round(won - FEE * len(pts), 2), top10=int((rk <= 0.1 * n).sum()), top1=int((rk <= 0.01 * n).sum()),
                best=round(pts.max(), 1), best_rank=int(rk.min()))


def read_set(w, folder):
    d = os.path.join(ROOT, 'weeks', w, folder)
    up, rd = os.path.join(d, 'upload.csv'), os.path.join(d, 'readable.csv')
    if not (os.path.exists(up) and os.path.exists(rd)):
        return None
    rows = [r[:9] for r in list(csv.reader(open(up)))[1:] if r]
    return rows, pd.read_csv(rd).Proj.values


def sets_for(w):
    out = {}
    for name, folder in SETS:
        if w == '2026-w09' and name == 'median70_injcap':
            continue   # week 9's median70/ had no injury cap: it is the plain build
        if w == '2026-w09' and name == 'median70_plain':
            folder = 'median70'
        x = read_set(w, folder)
        if x:
            out[name] = x
    for p in sorted(glob.glob(os.path.join(ROOT, 'weeks', w, 'paper', '*.csv'))):
        name = os.path.splitext(os.path.basename(p))[0]
        if name not in out:
            d = pd.read_csv(p, dtype=str)
            out[name] = (d.iloc[:, :9].values.tolist(), d.Proj.astype(float).values)
    return out


def entered(w):
    for f in ['entry_20/upload.csv', 'entered_upload_149.csv']:
        p = os.path.join(ROOT, 'weeks', w, f)
        if os.path.exists(p):
            return [r[:9] for r in list(csv.reader(open(p)))[1:] if r], f
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--rebuild', default='', help='re-read this week\'s export')
    a = ap.parse_args()
    rows = []
    for w in weeks():
        fld, act = field(w, rebuild=(w == a.rebuild))
        pr, table = prizes(w)
        ent, ent_file = entered(w)
        if ent:
            rows.append(dict(week=w, set='ENTERED', scope=ent_file, **grade(ent, fld, act, pr)))
        for name, (lps, proj) in sets_for(w).items():
            order = np.argsort(-np.asarray(proj, dtype=float), kind='stable')[:TOP]
            rows.append(dict(week=w, set=name, scope='full', **grade(lps, fld, act, pr)))
            rows.append(dict(week=w, set=name, scope='top20', **grade([lps[k] for k in order], fld, act, pr)))
        print(f'{w}: field {len(fld):,}, prize table {table}, {len(sets_for(w))} sets'
              + (f', entered = {ent_file}' if ent else ''))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(ROOT, 'docs', 'paper_results.csv'), index=False)
    md = ['# Paper results (running table, weeks 5 onward)', '',
          'Written by `python src/paper_results.py`; one row per week x set in `docs/paper_results.csv`. Every set '
          'graded as if entered on its own (exact money). top20 = each build\'s 20 highest-projected lineups ($1.00 a '
          'week). Model frozen through week 12 (Doug, Nov 16).', '']
    for scope, title in [('top20', 'Top 20 per build: net $ by week'), ('full', 'Full 150 per build: net $ by week')]:
        x = d[d.scope == scope]
        piv = x.pivot(index='set', columns='week', values='net')
        piv.columns = [c[-2:] for c in piv.columns]
        tot = x.groupby('set').agg(weeks=('net', 'size'), net=('net', 'sum'), cashed=('cashed', 'sum'),
                                   lineups=('lineups', 'sum'), avg=('avg', 'mean'), top10=('top10', 'sum'),
                                   top1=('top1', 'sum'), profit_weeks=('net', lambda s: int((s > 0).sum())))
        tot['cash_%'] = (tot.cashed / tot.lineups * 100).round(1)
        t = piv.join(tot[['weeks', 'net', 'cash_%', 'avg', 'top10', 'top1', 'profit_weeks']].round(2)) \
            .sort_values('net', ascending=False)
        md += [f'## {title}', '', md_table(t.reset_index()), '']
    e = d[d.set == 'ENTERED'][['week', 'scope', 'lineups', 'avg', 'cash_rate', 'won', 'net', 'top10', 'top1', 'best']]
    md += ['## Entered (as entered)', '', md_table(e), '',
           f'Entered total: won ${e.won.sum():.2f}, net ${e.net.sum():.2f} (weeks 5 on; the running total since week 4 '
           'is in CLAUDE.md).', '']
    with open(os.path.join(ROOT, 'docs', 'paper_results.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print('written docs/paper_results.csv and docs/paper_results.md')


if __name__ == '__main__':
    main()
