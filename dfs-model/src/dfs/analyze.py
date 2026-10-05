"""Post-slate grading: projection calibration, my entries vs field, stack performance, ownership vs exposure."""
import re

import numpy as np
import pandas as pd

TIERS = [(0, 8), (8, 14), (14, 20), (20, 99)]
ID_RE = r'\((\d+-\d+)\)'


def load_actuals(path):
    """results_players.csv -> Id, FPTS, own_pct."""
    r = pd.read_csv(path)
    return pd.DataFrame({'Id': r.Player.str.extract(ID_RE)[0], 'FPTS': r.FPTS, 'own_pct': r['%Drafted'] * 100})


def joined(proj, actuals):
    return actuals.merge(proj, on='Id').dropna(subset=['Proj'])


def calibration_table(sk, tiers=TIERS):
    rows = []
    for lo, hi in tiers:
        s = sk[(sk.Proj >= lo) & (sk.Proj < hi)]
        rows.append(dict(tier=f'{lo}-{hi}', n=len(s), proj=s.Proj.mean(), actual=s.FPTS.mean(), gap=s.Proj.mean() - s.FPTS.mean()))
    return pd.DataFrame(rows)


def entries(path, proj):
    """My entries with lineup Ids and stack team (team of the QB)."""
    me = pd.read_csv(path)
    pid = proj.set_index('Id')
    me['ids'] = me.Lineup.map(lambda s: re.findall(ID_RE, s))
    me['stack'] = me.ids.map(lambda l: next((pid.Team[i] for i in l if i in pid.index and pid.Pos[i] == 'QB'), '?'))
    return me


def stack_performance(me):
    return me.groupby('stack').Points.agg(['count', 'mean', 'max']).round(1).sort_values('mean', ascending=False)


def ownership_vs_exposure(sk, me, top=15):
    ex = pd.Series([i for l in me.ids for i in l]).value_counts() / len(me) * 100
    sk = sk.assign(my_pct=sk.Id.map(ex).fillna(0))
    return sk.sort_values('FPTS', ascending=False).head(top)[['Name', 'Team', 'Proj', 'FPTS', 'own_pct', 'my_pct']].round(1)


def report(week, proj):
    c = joined(proj, load_actuals(week.results_players))
    sk, d = c[c.Pos != 'D'], c[c.Pos == 'D']
    print('Projection vs actual (skill players), corr = %.3f' % np.corrcoef(sk.Proj, sk.FPTS)[0, 1])
    for t in calibration_table(sk).itertuples():
        print(f'  proj {t.tier:<5}: n={t.n:3d}  mean proj {t.proj:5.1f}  actual {t.actual:5.1f}')
    print('DST corr = %.2f' % np.corrcoef(d.Proj, d.FPTS)[0, 1])
    me = entries(week.results_entries, proj)
    print('\nMy entries: mean %.1f  best %.1f (rank %d)' % (me.Points.mean(), me.Points.max(), me.Rank.min()))
    print(stack_performance(me).to_string())
    print('\nTop scorers with field ownership vs my exposure:')
    print(ownership_vs_exposure(sk, me).to_string(index=False))
