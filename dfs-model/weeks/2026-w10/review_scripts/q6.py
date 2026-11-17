"""Top 20 by each build's own projection, weeks 5-10, graded as if entered (20 x $0.05 = $1.00 a week)."""
import os
import numpy as np, pandas as pd
import gradelib as g
WEEKS = ['2026-w%02d' % w for w in range(5, 11)]
ARCH = {'model': {w: '' for w in WEEKS},
        'cap45': {'2026-w07': 'model_cap45', '2026-w08': 'model_cap45', '2026-w09': 'model_cap45', '2026-w10': 'model_cap45'},
        'pool': {'2026-w07': 'pool', '2026-w08': 'pool', '2026-w09': 'pool', '2026-w10': 'pool'},
        'flex': {'2026-w09': 'flex_shadow', '2026-w10': 'flex_shadow'},
        'nodraw': {'2026-w09': 'nodraw', '2026-w10': 'nodraw'},
        'median70': {'2026-w09': 'median70', '2026-w10': 'median70_plain'},
        'v1': {'2026-w10': 'median70_v1'}, 'v2': {'2026-w10': 'median70_v2'}}
BUILDS = ['model', 'nodraw', 'cap45', 'flex', 'pool', 'median70', 'v1', 'v2', 'fdr', 'blend']
rows = []
for b in BUILDS:
    for w in WEEKS:
        x = None
        if w in ARCH.get(b, {}):
            x = g.archived(w, ARCH[b][w])
        else:
            x = g.rebuilt(w, b)
        if x is None:
            continue
        lps, pj = x
        order = np.argsort(-np.asarray(pj), kind='stable')
        top = [lps[k] for k in order[:20]]
        full = g.grade(w, lps)
        t = g.grade(w, top)
        dist = len(set(map(frozenset, top)))
        rows.append(dict(build=b, week=w[-2:], t20_avg=t['avg'], t20_cashed=t['cashed'], t20_won=t['won'], t20_net=t['net'],
                         t20_top10=t['top10'], t20_top1=t['top1'], t20_best=t['best'], t20_distinct=dist,
                         full_avg=full['avg'], full_cash=full['cash_rate'], full_net=full['net'],
                         full_net_per20=round(full['net'] / full['lineups'] * 20, 2)))
d = pd.DataFrame(rows)
d.to_csv(os.path.join(g.HERE, 'out', 'q6_top20.csv'), index=False)
pd.set_option('display.width', 250)
print(d.to_string(index=False))
s = d.groupby('build').agg(weeks=('week', 'count'), t20_avg=('t20_avg', 'mean'), t20_cashed=('t20_cashed', 'sum'),
                           t20_won=('t20_won', 'sum'), t20_net=('t20_net', 'sum'), t20_top10=('t20_top10', 'sum'),
                           t20_top1=('t20_top1', 'sum'), weeks_profit=('t20_net', lambda x: int((x > 0).sum())),
                           full_net_per20=('full_net_per20', 'sum'))
s['t20_cash_rate'] = (s.t20_cashed / (20 * s.weeks) * 100).round(1)
print(s.round(2).sort_values('t20_net', ascending=False).to_string())
six = d[d.build.isin(s[s.weeks == 6].index)]
print('\nweeks 5-10 complete builds only: net by week')
print(six.pivot(index='build', columns='week', values='t20_net').to_string())
