"""Learn from winners (weekly review step, Doug Nov 2): compare the field's top 1%, top 10%, the whole field and our
entered lineups on lineup build - salary by position, RB count and FLEX, ownership, stack type, QB/DST salary tier,
points by position - plus exposure to the field's 10 most-owned players (ours, our model set and each [grading]
extra_sets set, e.g. the cap-45 control) and how far our lineups finished below the field median.

  python src/learn_from_winners.py --week 2026-w09 [--export data/2026-w09/raw/<file>.csv] [--set name=upload.csv]
      reads the full FanDuel All Entries export (untracked, data/<week>/raw/) and writes weeks/<week>/winners.csv
      (metric x group) and weeks/<week>/winners_top_owned.csv
  python src/learn_from_winners.py --compare 2026-w05,2026-w06,2026-w07,2026-w08
      reads those weeks' winners.csv and lists the us-vs-top-10% differences that show up every week, in three of
      but one, or in fewer

Ownership = FanDuel's %Drafted for this contest. A stack piece is a QB teammate (any non-DST); bring-back = at least
one non-DST from the QB's opponent; game stack = teammate + bring-back, one-team = teammate(s) only, naked = none."""
import glob
import os
import re

import numpy as np
import pandas as pd

from dfs import config

ID_RE = re.compile(r'\((\d+-\d+)\)')
POS = ['QB', 'RB', 'WR', 'TE', 'D']
GROUPS = ['top1', 'top10', 'field', 'ours']
QB_TIERS = [(0, 7500, 'QB <7.5k'), (7500, 8500, 'QB 7.5-8.4k'), (8500, 9300, 'QB 8.5-9.2k'), (9300, 99999, 'QB 9.3k+')]
D_TIERS = [(0, 3800, 'DST <3.8k'), (3800, 4300, 'DST 3.8-4.2k'), (4300, 4800, 'DST 4.3-4.7k'), (4800, 99999, 'DST 4.8k+')]
# |ours - top 10%| at or above this counts as a difference in the --compare report
THRESH = dict(salary=150, share=4.0, own=0.5, count=0.10, points=1.0)


def players_table(raw, week):
    """Export player rows + team/opponent from the week's FanDuel player file(s)."""
    p = raw[['Player', 'Roster Position', '%Drafted', 'FPTS', 'Salary']].dropna(subset=['Player']).copy()
    p['Id'] = p.Player.str.extract(ID_RE)[0]
    p['Name'] = p.Player.str.replace(ID_RE, '', regex=True).str.strip()
    p['Pos'] = p['Roster Position']
    p['own'] = p['%Drafted'].astype(str).str.rstrip('%').astype(float)            # percent
    p['Salary'] = p.Salary.astype(int)
    teams = pd.concat([pd.read_csv(f)[['Id', 'Team', 'Opponent']] for f in sorted(glob.glob(os.path.join(week.data, 'fd_players*.csv')))])
    teams = teams.drop_duplicates('Id').set_index('Id')
    p['Team'], p['Opp'] = p.Id.map(teams.Team), p.Id.map(teams.Opponent)
    return p.drop_duplicates('Id').reset_index(drop=True)


def to_index(lineups, P):
    """List of 9-id lineups (slot order QB RB RB WR WR WR TE FLEX D) -> int array of player-table rows (-1 unknown)."""
    pos = {i: k for k, i in enumerate(P.Id)}
    return np.array([[pos.get(i, -1) for i in lu] for lu in lineups], dtype=int)


def features(ix, P):
    """One row per lineup."""
    ok = (ix >= 0).all(axis=1)
    ix = ix[ok]
    sal, own, pts = (P[c].to_numpy(dtype=float)[ix] for c in ['Salary', 'own', 'FPTS'])
    obj = lambda c: P[c].to_numpy(dtype=object)[ix]
    pos, team, opp = obj('Pos'), obj('Team'), obj('Opp')
    f = pd.DataFrame(index=range(len(ix)))
    for q in POS:
        m = pos == q
        f['sal_' + q] = (sal * m).sum(axis=1)
        f['pts_' + q] = (pts * m).sum(axis=1)
    f['sal_total'], f['pts_total'] = sal.sum(axis=1), pts.sum(axis=1)
    f['n_RB'] = (pos == 'RB').sum(axis=1)
    f['flex'] = pos[:, 7]
    f['own_avg'], f['own_sum'] = own.mean(axis=1), own.sum(axis=1)
    f['n_over20'] = (own > 20).sum(axis=1)
    qb_team, qb_opp = team[:, [0]], opp[:, [0]]
    nd = pos != 'D'
    mate = nd & (team == qb_team)
    mate[:, 0] = False
    f['stack_n'] = mate.sum(axis=1)
    f['stack_recv'] = (mate & np.isin(pos, ['WR', 'TE'])).sum(axis=1)
    f['bringback'] = (nd & (team == qb_opp)).any(axis=1)
    f['stack_type'] = np.where(f.stack_n == 0, 'naked', np.where(f.bringback, 'game', 'one-team'))
    f['qb_tier'] = pd.cut(sal[:, 0], [t[0] for t in QB_TIERS] + [99999], right=False, labels=[t[2] for t in QB_TIERS]).astype(str)
    f['dst_tier'] = pd.cut(sal[:, 8], [t[0] for t in D_TIERS] + [99999], right=False, labels=[t[2] for t in D_TIERS]).astype(str)
    f['ids'] = list(P.Id.to_numpy(dtype=object)[ix])
    return f


def summarize(f):
    """[(metric, kind, unit, value)] for one group. kind: decision (set before lock) or outcome."""
    out = []
    add = lambda m, k, u, v: out.append((m, k, u, float(v)))
    for q in POS + ['total']:
        add('salary ' + q, 'decision', 'salary', f['sal_' + q].mean())
    add('RBs per lineup', 'decision', 'count', f.n_RB.mean())
    for q in ['RB', 'WR', 'TE']:
        add('FLEX ' + q + ' %', 'decision', 'share', 100 * (f.flex == q).mean())
    add('avg player ownership %', 'decision', 'own', f.own_avg.mean())
    add('total lineup ownership %', 'decision', 'own', f.own_sum.mean())
    add('players over 20% owned', 'decision', 'count', f.n_over20.mean())
    add('QB stack pieces (teammates)', 'decision', 'count', f.stack_n.mean())
    for n, lab in [(0, '0'), (1, '1'), (2, '2'), (3, '3+')]:
        m = f.stack_n >= 3 if n == 3 else f.stack_n == n
        add(f'QB + {lab} %', 'decision', 'share', 100 * m.mean())
    add('bring-back %', 'decision', 'share', 100 * f.bringback.mean())
    for t in ['game', 'one-team', 'naked']:
        add(f'{t} stack %', 'decision', 'share', 100 * (f.stack_type == t).mean())
    for _, _, lab in QB_TIERS:
        add(lab + ' %', 'decision', 'share', 100 * (f.qb_tier == lab).mean())
    for _, _, lab in D_TIERS:
        add(lab + ' %', 'decision', 'share', 100 * (f.dst_tier == lab).mean())
    for q in POS + ['total']:
        add('points ' + q, 'outcome', 'points', f['pts_' + q].mean())
    return out


def exposure(f, ids):
    s = pd.Series([i for lu in f.ids for i in lu]).value_counts()
    return 100 * s.reindex(ids).fillna(0) / len(f)


def read_set(path):
    with open(path) as fh:
        rows = [r.strip().split(',') for r in fh.read().splitlines()[1:] if r.strip()]
    return rows


def run_week(week, cfg, a):
    raws = sorted(glob.glob(os.path.join(week.data, 'raw', '*.csv')))
    export = a.export or (raws[0] if len(raws) == 1 else None)
    if not export:
        raise SystemExit(f'pick the contest export with --export (found {raws})')
    raw = pd.read_csv(export, encoding='utf-8-sig', low_memory=False)
    P = players_table(raw, week)
    ent = raw[['Rank', 'EntryName', 'Points', 'Lineup']].dropna(subset=['Lineup']).copy()
    ent['Rank'] = ent.Rank.astype(int)
    lus = ent.Lineup.str.findall(ID_RE)
    full = lus.str.len() == 9
    ent, lus = ent[full.values], lus[full]
    N = int(cfg.get('contest', {}).get('field_size') or len(ent))
    ix = to_index(lus.tolist(), P)
    F = features(ix, P)
    F['Rank'], F['Points'], F['user'] = ent.Rank.values, ent.Points.values, ent.EntryName.str.split(' ').str[0].values
    groups = {'top1': F[F.Rank <= 0.01 * N], 'top10': F[F.Rank <= 0.10 * N], 'field': F, 'ours': F[F.user == a.user]}
    if len(groups['ours']) == 0:
        raise SystemExit(f'no entries for {a.user} in {export}')

    rows = []
    for g, f in groups.items():
        for m, k, u, v in summarize(f):
            rows.append(dict(week=week.name, metric=m, kind=k, unit=u, group=g, value=v))
    S = pd.DataFrame(rows)
    T = S.pivot_table(index=['metric', 'kind', 'unit'], columns='group', values='value', sort=False)[GROUPS].reset_index()
    T['ours_minus_top10'] = T.ours - T.top10
    T['field_minus_top10'] = T.field - T.top10

    # the field's 10 most-owned players: exposure of every group and set
    top_ids = list(P.sort_values('own', ascending=False).Id.head(10))
    X = P.set_index('Id').loc[top_ids, ['Name', 'Pos', 'Team', 'Salary', 'own', 'FPTS']].rename(columns={'own': 'field_own'})
    X['value_x'] = X.FPTS / (X.Salary / 1000)
    for g in ['top1', 'top10', 'ours']:
        X[g] = exposure(groups[g], top_ids)
    sets = {'model': os.path.join(week.out, 'upload.csv')}
    for s in cfg.get('grading', {}).get('extra_sets', []):
        sets[s] = os.path.join(week.out, s, 'upload.csv')
    for kv in a.set or []:
        k, v = kv.split('=', 1)
        sets[k] = v
    caps = {}
    for s, path in sets.items():
        if os.path.exists(path):
            fs = features(to_index(read_set(path), P), P)
            X['set_' + s] = exposure(fs, top_ids)
            caps[s] = len(fs)
    X['hit'] = X.top10 >= 1.2 * X.field_own          # the top 10% held him at 1.2x the field's rate or more
    X = X.reset_index()

    # below the field median
    med = float(F.Points.median())
    ours = groups['ours']
    below = dict(week=week.name, field_median=med, ours_avg=ours.Points.mean(), ours_median=ours.Points.median(),
                 share_below_median=100 * (ours.Points < med).mean(), avg_minus_median=ours.Points.mean() - med,
                 n_ours=len(ours), n_field=len(F), top1_n=len(groups['top1']), top10_n=len(groups['top10']))
    for k, v in below.items():
        if k != 'week':
            T = pd.concat([T, pd.DataFrame([dict(metric='median: ' + k, kind='summary', unit='', ours=v)])], ignore_index=True)

    T.insert(0, 'week', week.name)
    T.to_csv(os.path.join(week.out, 'winners.csv'), index=False)
    X.insert(0, 'week', week.name)
    X.to_csv(os.path.join(week.out, 'winners_top_owned.csv'), index=False)

    pd.set_option('display.width', 250, 'display.max_rows', 200)
    print(f'{week.name}: {len(F):,} full lineups (field size {N:,}); top 1% {len(groups["top1"]):,}, top 10% '
          f'{len(groups["top10"]):,}; ours {len(ours)} ({a.user})')
    print(T[T.kind != 'summary'].drop(columns=['week', 'kind', 'unit']).round(2).to_string(index=False))
    print(f'\nBelow the field median ({med:.2f}): {below["share_below_median"]:.0f}% of our lineups; our average '
          f'{below["ours_avg"]:.2f} ({below["avg_minus_median"]:+.2f}), our median {below["ours_median"]:.2f}')
    print('\nField 10 most-owned players: exposure % (hit = top 10% held him at 1.2x the field rate or more)')
    print(X.drop(columns=['week']).round(1).to_string(index=False))
    sc = [c for c in X if c.startswith('set_')]
    for lab, m in [('hits', X.hit), ('rest', ~X.hit)]:
        print(f'  mean exposure, {lab} ({int(m.sum())}): ' + ', '.join(f'{c} {X.loc[m, c].mean():.1f}'
              for c in ['field_own', 'top10', 'ours'] + sc))


def compare(weeks):
    D = pd.concat([pd.read_csv(os.path.join(config.current_week(w).out, 'winners.csv')) for w in weeks])
    D = D[D.kind != 'summary']
    diff = D.pivot_table(index=['metric', 'kind', 'unit'], columns='week', values='ours_minus_top10', sort=False)
    fld = D.pivot_table(index=['metric', 'kind', 'unit'], columns='week', values='field_minus_top10', sort=False)
    rows = []
    for key, d in diff.iterrows():
        t = THRESH[key[2]]
        pos, neg = int(((d >= t)).sum()), int(((d <= -t)).sum())
        n = max(pos, neg)
        rows.append(dict(metric=key[0], kind=key[1], **{w[-3:]: round(v, 1) for w, v in d.items()},
                         mean=round(d.mean(), 1), field_mean=round(fld.loc[key].mean(), 1),
                         weeks=n if pos == 0 or neg == 0 else f'{pos}+/{neg}-', sign='+' if pos >= neg else '-'))
    R = pd.DataFrame(rows)
    pd.set_option('display.width', 250, 'display.max_rows', 200)
    print('ours minus field top 10%, by week (field_mean = field minus top 10%, averaged)')
    print('thresholds:', THRESH)
    n = len(weeks)
    for lab, m in [('IN ALL WEEKS (same direction)', R.weeks == n), ('in all but one week', R.weeks == n - 1),
                   ('in fewer weeks, or mixed direction', ~R.weeks.isin([n, n - 1]) & (R.weeks != 0))]:
        print(f'\n{lab}'); print(R[m].to_string(index=False) if m.any() else '  none')
    below = pd.concat([pd.read_csv(os.path.join(config.current_week(w).out, 'winners.csv')) for w in weeks])
    below = below[below.kind == 'summary'].pivot_table(index='week', columns='metric', values='ours')
    print('\nBelow the field median'); print(below.round(2).to_string())
    X = pd.concat([pd.read_csv(os.path.join(config.current_week(w).out, 'winners_top_owned.csv')) for w in weeks])
    cols = ['field_own', 'top1', 'top10', 'ours'] + [c for c in X if c.startswith('set_')]
    print('\nField 10 most-owned players, mean exposure % by week: the hits, then the rest')
    for lab, m in [('hits', X.hit), ('rest', ~X.hit)]:
        E = X[m].groupby('week')[cols].mean()
        E.insert(0, 'n', X[m].groupby('week').size())
        print(f'-- {lab}'); print(E.round(1).to_string())
    return R


if __name__ == '__main__':
    week, cfg, a = config.cli(__doc__, [
        (('--export',), dict(help='FanDuel All Entries csv (default: the only csv in data/<week>/raw/)')),
        (('--user',), dict(default='gst1999', help='FanDuel username')),
        (('--set',), dict(action='append', help='extra set for the exposure table: name=path/to/upload.csv')),
        (('--compare',), dict(help='comma-separated weeks: report differences from their winners.csv instead')),
    ])
    if a.compare:
        compare(a.compare.split(','))
    else:
        run_week(week, cfg, a)
