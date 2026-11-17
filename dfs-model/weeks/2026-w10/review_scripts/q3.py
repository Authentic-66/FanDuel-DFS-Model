"""Low scores: entered lineups under 100, players under 3 points, why. Plus sub-3 rates weeks 5-10."""
import os, re, csv
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
R = r'D:\FanDuel-DFS\dfs-model-starter\FanDuel-DFS Model\dfs-model'
W = os.path.join(R, 'weeks', '2026-w10')
TEAM = {'LAR': 'LA', 'JAC': 'JAX'}


def norm(s):
    s = re.sub(r'[^a-z ]', '', str(s).lower().replace('-', ' '))
    return ' '.join(t for t in s.split() if t not in ('jr', 'sr', 'ii', 'iii', 'iv', 'v'))


pts = pd.read_csv(os.path.join(HERE, 'out', '2026-w10_pts.csv'))
fp = dict(zip(pts.Id, pts.FPTS))
proj = pd.read_csv(os.path.join(W, 'proj.csv'))
P = proj.set_index('Id')
snaps = pd.read_csv(os.path.join(HERE, 'nfl', 'snap_counts_2026.csv'))
st = pd.read_csv(os.path.join(HERE, 'nfl', 'stats_player_week_2026.csv'), low_memory=False)
snaps['k'] = snaps.player.map(norm) + '|' + snaps.team
st['k'] = st.player_display_name.map(norm) + '|' + st.team
s10 = snaps[snaps.week == 10].set_index('k')
prev = snaps[(snaps.week < 10) & (snaps.offense_snaps > 0)].groupby('k').offense_pct.mean()
t10 = st[st.week == 10].set_index('k')
st['opp'] = st.targets.fillna(0) + st.carries.fillna(0)
prev_opp = st[st.week < 10].groupby('k').opp.mean()
sched = pd.read_csv(os.path.join(R, 'data', 'cache', 'schedule_2026.csv'))
g10 = sched[sched.week == 10]
kick = {}
for r in g10.itertuples():
    kick[r.away_team] = kick[r.home_team] = r.gametime
teams_played = set(snaps[snaps.week == 10].team)

ent = [r for r in list(csv.reader(open(os.path.join(W, 'entered_upload_149.csv'))))[1:]]
rows, lus = [], []
for k, lp in enumerate(ent):
    tot = sum(fp.get(i, 0) for i in lp)
    lus.append(tot)
    if tot >= 100:
        continue
    for i in lp:
        v = fp.get(i, 0)
        if v >= 3:
            continue
        p = P.loc[i]
        key = norm(p.Name) + '|' + TEAM.get(p.Team, p.Team)
        if p.Pos == 'D':
            why, sn, avg, opp = 'DST', np.nan, np.nan, np.nan
        else:
            sn = s10.offense_pct.get(key, np.nan) if key in s10.index else np.nan
            avg = prev.get(key, np.nan)
            o = t10.loc[key] if key in t10.index else None
            opp = (float(np.nansum([o.targets, o.carries])) if o is not None and not isinstance(o, pd.DataFrame) else np.nan)
            if np.isnan(sn) or sn == 0:
                why = 'did not play (inactive / DNP)'
            elif not np.isnan(avg) and sn < 0.5 * avg:
                why = 'left early / limited snaps (in-game injury or benching)'
            elif not np.isnan(avg) and sn < 0.8 * avg:
                why = 'reduced role'
            else:
                why = 'bad game (normal snaps)'
        rows.append(dict(lineup=k + 1, lineup_pts=round(tot, 1), Name=p.Name, Pos=p.Pos, Team=p.Team, Proj=p.Proj,
                         FPTS=v, snap_pct=sn, avg_snap=round(avg, 2) if not np.isnan(avg) else np.nan,
                         tgt_car=opp, prev_tgt_car=round(prev_opp.get(key, np.nan), 1), kick=kick.get(TEAM.get(p.Team, p.Team)),
                         why=why))
d = pd.DataFrame(rows)
d.to_csv(os.path.join(HERE, 'out', 'q3_low_lineups.csv'), index=False)
lus = np.array(lus)
print('entered 149 under 100:', (lus < 100).sum(), ' under 60:', (lus < 60).sum(), ' min', lus.min().round(1))
print('\nplayer rows', len(d), '| lineups with a sub-3 player among the under-100s:', d.lineup.nunique())
agg = d.groupby(['Name', 'Pos', 'Team', 'Proj', 'FPTS', 'snap_pct', 'avg_snap', 'tgt_car', 'prev_tgt_car', 'kick', 'why'],
                dropna=False).lineup.count().rename('lineups').reset_index().sort_values('lineups', ascending=False)
pd.set_option('display.width', 250)
print(agg.to_string(index=False))
print(d.groupby('why').lineup.agg(['count', 'nunique']))
# entered players who did not play at all: were any out on the Sunday list?
fd = pd.read_csv(os.path.join(R, 'data', '2026-w10', 'fd_players_sunday.csv'))
allp = sorted({i for lp in ent for i in lp})
dnp = []
for i in allp:
    p = P.loc[i]
    if p.Pos == 'D':
        continue
    key = norm(p.Name) + '|' + TEAM.get(p.Team, p.Team)
    sn = s10.offense_pct.get(key, np.nan) if key in s10.index else np.nan
    if (np.isnan(sn) or sn == 0) and TEAM.get(p.Team, p.Team) in teams_played:
        tag = fd.loc[fd.Id == i, 'Injury Indicator'].tolist()
        dnp.append((p.Name, p.Team, fp.get(i), tag, sum(i in lp for lp in ent)))
print('\nentered players with no week-10 offensive snap (team played):', dnp)
# sub-3 rate weeks 5-10
out = []
for w in ['05', '06', '07', '08', '09', '10']:
    f = pd.read_csv(os.path.join(HERE, 'out', f'2026-w{w}_field.csv'), usecols=['Rank', 'Points', 'mine', 'n_sub3', 'dst_sub3'])
    n = len(f)
    top = f[f.Rank <= 0.1 * n]
    top1 = f[f.Rank <= 0.01 * n]
    mine = f[f.mine]
    r = dict(week=w)
    for lab, x in [('field', f), ('top10', top), ('top1', top1), ('ours', mine)]:
        r[lab + '_any'] = round((x.n_sub3 > 0).mean() * 100, 1)
        r[lab + '_avgn'] = round(x.n_sub3.mean(), 2)
    out.append(r)
o = pd.DataFrame(out)
o.to_csv(os.path.join(HERE, 'out', 'q3_sub3_rates.csv'), index=False)
print('\nShare of lineups with 1+ non-DST player under 3 points (%), and avg count:')
print(o.to_string(index=False))
