"""History test for the role-guard recent-role switches (docs/role_guard_tests.md; Doug, Nov 3 2026).

    python src/fit_role_guard.py [--seasons 2023-2025] [--sims 1000]

For each season, weeks 4-18: every RB / WR / TE with a snap-count row in the game (= active) is projected the way
model.py does it with the week-9 settings (usage from earlier weeks + prior-season blend, Vegas implied totals,
injury routing of players with 3+ targets + carries a game who are absent that week, FanDuel-FPPG fallback = prior
season points per game, calibration and the WR implied-total correction), then the role guard is applied four ways
on the same draws: as live, + promotion (switch 1), + snap_projection (switch 2), role_drop_action = "scale"
(switch 3). Rows -> weeks/2026-w09/role_guard_history.csv; per switch: players changed per week, and bias / MAE /
RMSE (projection minus actual FanDuel points) of the changed players, as live vs with the switch."""
import contextlib
import copy
import io
import os
import types

import numpy as np
import pandas as pd

from dfs import config, data, history, project, sim, snaps, usage
from dfs.scoring import stats_points

SKILL = {'RB': 'RB', 'FB': 'RB', 'WR': 'WR', 'TE': 'TE'}
VARIANTS = {'live': {}, 'promotion': {'promotion': True}, 'snap_projection': {'snap_projection': True},
            'role_drop_scale': {'role_drop_action': 'scale'}}


def seasons(text):
    lo, _, hi = text.partition('-')
    return range(int(lo), int(hi or lo) + 1)


def routing_of(inj):
    routing = inj.get('position_share') if inj.get('routing') == 'position' else None
    if routing:
        ranked = inj.get('depth_rank_positions', list(routing)) if inj.get('within_position') == 'depth_rank' else []
        routing = {p: {k: v for k, v in r.items() if p in ranked or not k.endswith('_rank')} for p, r in routing.items()}
    return routing


def season_rows(week, cfg, season, n_sims, seed=11):
    m, sc, inj = cfg['model'], cfg['scoring'], cfg['model']['injury']
    rg = m['role_guard']
    st = data.load_stats(week.stats(season), cfg)
    st = st.assign(fd=stats_points(sc, st))
    pst = data.load_stats(week.stats(season - 1), cfg)
    pst = pst.assign(fd=stats_points(sc, pst))
    prior = usage.aggregate(pst)
    prior_fppg = pst.groupby('k').fd.sum() / prior.g
    sn = snaps.load(snaps.path(week.cache, season), cfg)
    psn = snaps.load(snaps.path(week.cache, season - 1), cfg)
    ln = history.load_lines(week.cache, season, cfg)
    implied = dict(zip(zip(ln.week, ln.team), ln.implied))
    opp_of = dict(zip(zip(ln.week, ln.team), ln.opp))
    routing = routing_of(inj)
    team_sd = np.hypot(m['correlation']['team_sd'], m['correlation']['game_sd'])
    no_lines = types.SimpleNamespace(implied=pd.Series(dtype=float))
    m_adj = copy.deepcopy(m)
    m_adj['dst']['flatten']['enabled'] = False      # skill players only: no DSTs to flatten
    out = []
    for w in range(4, 19):
        before = st[st.week < w]
        cur = usage.aggregate(before)
        agg = usage.blend_prior(cur, prior, m['prior_blend'])
        role = project.role_volume(before)
        feats = snaps.features(sn[sn.week < w], before, psn, rg.get('promotion_games', 2))
        now = sn[(sn.week == w) & sn.position.isin(list(SKILL))].drop_duplicates('k')
        if now.empty:
            continue
        pop = pd.DataFrame(dict(Key=now.k.values, Team=now.team.values, Position=now.position.map(SKILL).values))
        act = st[st.week == w].groupby('k').fd.sum()
        # absent this week: players with 3+ targets + carries a game this season whose team played and who have no
        # snap row (the live run lists such players OUT: injury tags + IR with volume)
        last_pos = before.sort_values('week').groupby('k').position.last()
        teams_now = set(pop.Team)
        outs = [(k, cur.at[k, 'team'], SKILL.get(last_pos.get(k), None)) for k in cur.index
                if role.get(k, 0) >= 3 and cur.at[k, 'team'] in teams_now and k not in set(pop.Key)
                and SKILL.get(last_pos.get(k)) is not None]
        outs = pd.DataFrame(outs, columns=['Key', 'Team', 'Position'])
        xt, xc = usage.redistribute_out(agg, outs, pop, inj['redistribute_share'], before,
                                        inj.get('absent_mode', 'skip'), routing, inj.get('bump_scale'))
        rng = np.random.default_rng(seed + 100 * season + w)
        raw, rows = [], []
        for r in pop.itertuples():
            scale = implied.get((w, r.Team), m['league_team_total']) / m['league_team_total']
            f = np.exp(rng.normal(0, team_sd, n_sims) + m['correlation']['shift'])
            if r.Key in agg.index:
                pts = sim.sim_skill(rng, agg.loc[r.Key], r.Position, scale, f, xt.get(r.Key, 0), xc.get(r.Key, 0),
                                    m, sc, n_sims)
            else:
                pts = sim.sim_fallback(rng, float(prior_fppg.get(r.Key, 0.0)), scale, f, m, n_sims)
            raw.append(pts)
            rows.append(dict(Name=r.Key, Key=r.Key, Pos=r.Position, Team=r.Team, Opp=opp_of.get((w, r.Team), ''),
                             Inj='', NoData=r.Key not in agg.index, RoleVol=role.get(r.Key, 0.0),
                             GainedVol=xt.get(r.Key, 0) + xc.get(r.Key, 0), StartingQB=False, Salary=1,
                             ImpliedTeamTotal=implied.get((w, r.Team), m['league_team_total'])))
        proj = pd.DataFrame(rows)
        for c in snaps.FEATURES:
            proj[c] = proj.Key.map(feats[c]).where(proj.Team.values == proj.Key.map(feats.team).values)
        raw = np.array(raw)
        res = dict(season=season, week=w, k=proj.Key, pos=proj.Pos, team=proj.Team, actual=proj.Key.map(act).fillna(0.0),
                   nodata=proj.NoData, role_vol=proj.RoleVol, gained=proj.GainedVol, last_snap=proj.LastSnap,
                   avg_snap=proj.AvgSnap, recent_vol=proj.RecentVol)
        for name, extra in VARIANTS.items():
            c = copy.deepcopy(rg)
            c.update(extra)
            s = raw.copy()
            with contextlib.redirect_stdout(io.StringIO()):
                drop = project.role_drop(proj, c, s)
                why = project.role_guard(proj, s, c, {})
                s = project.adjust(proj, s, no_lines, m_adj)
            res[name] = s.mean(axis=1)
            if name == 'live':
                res['guard'], res['flag'] = why, drop
            if name in ('promotion', 'snap_projection'):
                res[name + '_label'] = project.guard_rescue(proj, c)[0]
        out.append(pd.DataFrame(res))
        print(f'{season} week {w}: {len(proj)} players, {len(outs)} absent with volume', flush=True)
    return pd.concat(out, ignore_index=True)


def stats(d, col):
    e = d[col] - d.actual
    return dict(bias=e.mean(), mae=e.abs().mean(), rmse=np.sqrt((e ** 2).mean()))


def report(rows):
    lines = []
    for name in ('promotion', 'snap_projection', 'role_drop_scale'):
        changed = rows[(rows[name] - rows.live).abs() > 0.01]
        weeks = rows.groupby(['season', 'week']).ngroups
        lines.append(f'\n=== {name}: {len(changed)} player-weeks changed ({len(changed) / weeks:.1f} a week)')
        parts = [('all', changed)] + [(str(s), g) for s, g in changed.groupby('season')] + \
            [('switch proj 4+', changed[changed[name] >= 4])]
        if name == 'promotion':     # which test kept him (a player can pass more than one)
            lab = changed.promotion_label.astype(str)
            parts += [('inherits', changed[lab.str.contains('inherits')]),
                      ('last games', changed[lab.str.contains('games')]),
                      ('snaps', changed[lab.str.contains('snaps')]),
                      ('snaps only', changed[lab.str.contains('snaps') & ~lab.str.contains('inherits|games')])]
            parts += [(p, g) for p, g in changed.groupby('pos')]
        for label, d in parts:
            if len(d) == 0:
                continue
            a, b = stats(d, 'live'), stats(d, name)
            lines.append(f'  {label:>14}: n {len(d):4d}  actual {d.actual.mean():5.2f} | live proj {d.live.mean():5.2f} '
                         f'bias {a["bias"]:+5.2f} MAE {a["mae"]:5.2f} RMSE {a["rmse"]:5.2f} | switch proj '
                         f'{d[name].mean():5.2f} bias {b["bias"]:+5.2f} MAE {b["mae"]:5.2f} RMSE {b["rmse"]:5.2f}')
    fl = rows[rows.flag.astype(str) != '']
    a = stats(fl, 'live') if len(fl) else None
    lines.append(f'\n=== role-drop flag (as live): {len(fl)} player-weeks '
                 + (f'({len(fl) / rows.groupby(["season", "week"]).ngroups:.1f} a week), actual {fl.actual.mean():.2f}, '
                    f'live proj {fl.live.mean():.2f}, bias {a["bias"]:+.2f}' if a else ''))
    return '\n'.join(lines)


if __name__ == '__main__':
    week, cfg, a = config.cli(__doc__, [(['--seasons'], dict(default='2023-2025')),
                                        (['--sims'], dict(type=int, default=1000))])
    rows = pd.concat([season_rows(week, cfg, s, a.sims) for s in seasons(a.seasons)], ignore_index=True)
    path = week.output('role_guard_history.csv')
    rows.to_csv(path, index=False)
    print(report(rows))
    print('\nwritten', path)
