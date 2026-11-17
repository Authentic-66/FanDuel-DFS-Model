"""FDR (Friday) projections vs ours vs FanDuel FPPG: accuracy by position, weeks 9-10; writes override files for builds."""
import os, re
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
R = r'D:\FanDuel-DFS\dfs-model-starter\FanDuel-DFS Model\dfs-model'
ALIAS = {'zonovan knight': 'bam knight'}


def norm(s):
    s = re.sub(r'[^a-z ]', '', str(s).lower().replace('-', ' '))
    s = ' '.join(t for t in s.split() if t not in ('jr', 'sr', 'ii', 'iii', 'iv', 'v'))
    return ALIAS.get(s, s)


def spearman(a, b):
    return pd.Series(a).rank().corr(pd.Series(b).rank())


rows = []
for w, fri in [('09', 'friday'), ('10', 'prelim')]:
    wk = '2026-w' + w
    f = pd.read_csv(os.path.join(R, 'data', wk, 'fdr_projections_fri.csv'))
    p = pd.read_csv(os.path.join(R, 'weeks', wk, 'proj.csv'))
    pf = pd.read_csv(os.path.join(R, 'weeks', wk, fri, 'projections.csv'))[['Name', 'Proj']].rename(columns={'Proj': 'OursFri'})
    pts = pd.read_csv(os.path.join(HERE, 'out', wk + '_pts.csv'))
    act = dict(zip(pts.Id, pts.FPTS))
    f['k'] = np.where(f.player.str.contains('D/ST'), f.team.map(norm), f.player.map(norm))
    p['k'] = p.Name.map(norm)
    m = p.merge(f[['k', 'fantasy']].drop_duplicates('k'), on='k', how='left').merge(pf, on='Name', how='left')
    m['FDR'] = m.fantasy
    m['Actual'] = m.Id.map(act)
    print(wk, 'proj rows', len(p), 'FDR matched', int(m.FDR.notna().sum()), 'with actual', int(m.Actual.notna().sum()))
    # override files for the lineup builds: FDR only where matched; players we project 0 (out) stay 0
    live = m[(m.Proj > 0) & m.FDR.notna()]
    live[['Name']].assign(Proj=live.FDR.round(2)).to_csv(os.path.join(HERE, 'out', f'{wk}_ov_fdr.csv'), index=False)
    live[['Name']].assign(Proj=(0.5 * live.FDR + 0.5 * live.Proj).round(2)).to_csv(os.path.join(HERE, 'out', f'{wk}_ov_blend.csv'), index=False)
    m['week'] = w
    rows.append(m)
a = pd.concat(rows)
# population: played-relevant players: we project them active (Proj > 0), FDR has them, a result exists,
# and either source projects 4+
s = a[(a.Proj > 0) & a.FDR.notna() & a.Actual.notna() & ((a.Proj >= 4) | (a.FDR >= 4))].copy()
s['Pos'] = s.Pos.replace({'D': 'DST'})
s['Blend'] = 0.5 * s.Proj + 0.5 * s.FDR
out = []
for (lab, g) in [('ALL', s)] + list(s.groupby('Pos')) + [(f'wk{w}', g) for w, g in s.groupby('week')]:
    r = dict(group=lab, n=len(g))
    for c in ['Proj', 'OursFri', 'FDR', 'Blend', 'FD_FPPG']:
        x = g[[c, 'Actual']].dropna()
        r[c + '_MAE'] = round((x[c] - x.Actual).abs().mean(), 2)
        r[c + '_bias'] = round((x[c] - x.Actual).mean(), 2)
        r[c + '_rho'] = round(spearman(x[c].values, x.Actual.values), 3)
    out.append(r)
o = pd.DataFrame(out)
o.to_csv(os.path.join(HERE, 'out', 'q4_accuracy.csv'), index=False)
pd.set_option('display.width', 250)
print('Proj = ours Sunday final; OursFri = ours Friday preview; FDR = FanDuel Research Friday; FD_FPPG = season avg')
print(o[['group', 'n'] + [c for c in o.columns if c.endswith('_MAE')]].to_string(index=False))
print(o[['group', 'n'] + [c for c in o.columns if c.endswith('_rho')]].to_string(index=False))
print(o[['group', 'n'] + [c for c in o.columns if c.endswith('_bias')]].to_string(index=False))
# head-to-head: who was closer, and residual regression of Actual - ours on (FDR - ours)
s['d'] = s.FDR - s.Proj
s['res'] = s.Actual - s.Proj
b = np.polyfit(s.d, s.res, 1)
print('\nresidual (actual - ours) on (FDR - ours): slope %.2f (0 = FDR adds nothing, 1 = FDR right)' % b[0])
for pos, g in s.groupby('Pos'):
    print(pos, 'slope %.2f' % np.polyfit(g.d, g.res, 1)[0], 'n', len(g))
print('\nBiggest disagreements (|FDR - ours| >= 4):')
print(s[s.d.abs() >= 4][['week', 'Name', 'Pos', 'Team', 'Proj', 'OursFri', 'FDR', 'Actual']].sort_values('week').to_string(index=False))
