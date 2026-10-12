"""Fit the depth-rank split inside a position ([model.injury.position_share] *_rank) and test it on past seasons.
Shares: how the same-position gain was divided between the largest, second, and third-and-lower remaining teammates
in the first game each starter missed (history.within_position), leave-one-season-out, recent seasons weighted more.
Test: for every such game, each remaining RB/WR/TE who played is projected four ways (no redistribution; the rule through week 5, 80% to every RB/WR/TE
pro rata; routed by position and pro rata inside it; routed by position and split by depth rank, with shares fit on the other seasons),
with Vegas totals and the calibration in config, against his actual FanDuel points.
Changes nothing in config. Writes weeks/history/depth_shares.csv, depth_rows.csv and depth_test.csv.
Needs `fetch_stats.py --seasons <first-1>-<last> --history` first."""
import os
import zlib

import numpy as np
import pandas as pd

from dfs import config, data, history as h, project, sim, usage
from dfs.scoring import stats_points

week, cfg, a = config.cli(__doc__, [
    (['--seasons'], dict(default='2021-2025')),
    (['--decay'], dict(type=float, default=0.75)),
    (['--n-sims'], dict(type=int, default=2000)),
])
lo, hi = map(int, a.seasons.split('-'))
seasons = list(range(lo, hi + 1))
W = h.season_weights(seasons, a.decay)
m, sc = cfg['model'], cfg['scoring']
base_routing = {pos: {k: v for k, v in rule.items() if not k.endswith('_rank')} for pos, rule in m['injury']['position_share'].items()}
stats = {s: data.load_stats(week.stats(s), cfg) for s in [lo - 1] + seasons}
events = {s: h.absences(stats[s]) for s in seasons}
within = pd.concat([h.within_position(stats[s], events[s]) for s in seasons], ignore_index=True)
within['w'] = within.season.map(W)


def rank_shares(d):
    """{position: {col_rank: [largest, second, third and lower]}} from within-position rows."""
    out = {}
    for (pos, col), e in d.groupby(['pos', 'col']):
        g = (e.w * e.gain).groupby(e['rank']).sum().reindex([1, 2, 3]).fillna(0).clip(lower=0)
        out.setdefault(pos, {})[col + '_rank'] = [round(float(x), 3) for x in g / g.sum()]
    return out


def with_ranks(shares):
    return {pos: {**rule, **shares.get(pos, {})} for pos, rule in base_routing.items()}


fits = [dict(held_out='none (all seasons)', **{f'{p} {c}': v for p, r in rank_shares(within).items() for c, v in r.items()})]
fits += [dict(held_out=s, **{f'{p} {c}': v for p, r in rank_shares(within[within.season != s]).items() for c, v in r.items()}) for s in seasons]
fits = pd.DataFrame(fits)
pd.set_option('display.width', 250)
print(fits.to_string(index=False))

rows = []
for s in seasons:
    st = stats[s].assign(fd=lambda d: stats_points(sc, d))
    prior = usage.aggregate(stats[s - 1])
    ln = h.load_lines(week.cache, s, cfg)
    implied = dict(zip(zip(ln.week, ln.team), ln.implied))
    routing = {'old rule': None, 'pro rata': base_routing, 'depth': with_ranks(rank_shares(within[within.season != s]))}
    ev = events[s]
    for wk, ev_w in ev.groupby('week'):
        agg = usage.blend_prior(usage.aggregate(st[st.week < wk]), prior, m['prior_blend'])
        now = st[(st.week == wk) & st.position.isin(h.SKILL)].drop_duplicates('k')
        for team, e in ev_w.groupby('team'):
            out = e.drop_duplicates('k').rename(columns={'k': 'Key', 'team': 'Team', 'pos': 'Position'})[['Key', 'Team', 'Position']]
            out = out[out.Key.isin(agg.index)]
            mates = now[(now.team == team) & now.k.isin(agg.index) & ~now.k.isin(out.Key)]
            active = pd.DataFrame(dict(Key=mates.k.values, Team=team, Position=mates.position.values))
            extra = {'none': ({}, {})}
            extra.update({name: usage.redistribute_out(agg, out, active, m['injury']['redistribute_share'], routing=r)
                          for name, r in routing.items()})
            scale = implied.get((wk, team), m['league_team_total']) / m['league_team_total']
            for r in mates.itertuples():
                rec = dict(season=s, week=wk, team=team, k=r.k, Pos=r.position, FPTS=r.fd, out=','.join(out.Key),
                           out_pos=','.join(sorted(set(out.Position))))
                for name, (xt, xc) in extra.items():
                    rng = np.random.default_rng(zlib.crc32(f'{s}-{wk}-{r.k}'.encode()))     # same draws for each variant
                    f = np.exp(rng.normal(0, np.hypot(m['correlation']['team_sd'], m['correlation']['game_sd']), a.n_sims)
                               + m['correlation']['shift'])
                    pts = sim.sim_skill(rng, agg.loc[r.k], r.position, scale, f, xt.get(r.k, 0), xc.get(r.k, 0), m, sc, a.n_sims)
                    rec[name] = float(project.calibrated(np.array([pts.mean()]), np.array([r.position]), m['calibration'])[0])
                    rec['gain ' + name] = xt.get(r.k, 0) + xc.get(r.k, 0)
                rows.append(rec)
    print(s, len(rows), flush=True)
rows = pd.DataFrame(rows)
rows['w'] = rows.season.map(W)
rmse = lambda d, c: float(np.sqrt(np.average((d[c] - d.FPTS) ** 2, weights=d.w))) if len(d) else np.nan
bias = lambda d, c: float(np.average(d[c] - d.FPTS, weights=d.w)) if len(d) else np.nan
moved = (rows.depth - rows['pro rata']).abs() >= 1
routed = (rows['pro rata'] - rows.none).abs() >= 1
SETS = [('all teammates', rows.k.notna()), ('routing moved him 1+ (pro rata vs none)', routed),
        ('depth split moved him 1+ (vs pro rata)', moved), ('  of those: raised by the depth split', moved & (rows.depth > rows['pro rata'])),
        ('  of those: lowered by the depth split', moved & (rows.depth < rows['pro rata']))]
SETS += [(f'depth split moved him 1+, {p}', moved & (rows.Pos == p)) for p in h.SKILL]
SETS += [(f'{p} out: routing moved him 1+', routed & (rows.out_pos == p)) for p in h.SKILL]
SETS += [(f'{p} out: all teammates', rows.out_pos == p) for p in h.SKILL]
VARIANTS = ['none', 'old rule', 'pro rata', 'depth']
test = pd.DataFrame([dict(players=label, n=int(t.sum()), actual=float(np.average(rows.FPTS[t], weights=rows.w[t])) if t.any() else np.nan,
                          **{f'proj {c}': float(np.average(rows[c][t], weights=rows.w[t])) if t.any() else np.nan for c in VARIANTS},
                          **{f'rmse {c}': rmse(rows[t], c) for c in VARIANTS}) for label, t in SETS])
print(test.round(2).to_string(index=False))
by_season = pd.DataFrame([dict(season=s, n=int((moved & (rows.season == s)).sum()), rmse_pro_rata=rmse(rows[moved & (rows.season == s)], 'pro rata'),
                               rmse_depth=rmse(rows[moved & (rows.season == s)], 'depth')) for s in seasons])
print(by_season.round(2).to_string(index=False))
print('[model.injury.position_share] rank shares:', rank_shares(within))
out_dir = os.path.join(week.root, 'weeks', 'history')
fits.to_csv(os.path.join(out_dir, 'depth_shares.csv'), index=False)
rows.to_csv(os.path.join(out_dir, 'depth_rows.csv'), index=False)
test.to_csv(os.path.join(out_dir, 'depth_test.csv'), index=False)
by_season.to_csv(os.path.join(out_dir, 'depth_test_by_season.csv'), index=False)
