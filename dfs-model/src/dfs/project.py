"""Build the week's projections and correlated sims: slate + lines + stats -> proj DataFrame, sims array (rows aligned)."""
import numpy as np
import pandas as pd

from . import data, sim, usage


def load_usage(week, cfg):
    """Current-season aggregate (stats before this week only, so archived weeks can be re-run without leakage),
    blended toward the prior season per [model.prior_blend], plus the current stats frame."""
    st = data.load_stats(week.stats(), cfg, before_week=week.number)
    agg = usage.aggregate(st)
    pb = cfg['model']['prior_blend']
    if pb['usage_games'] or pb['efficiency_games']:
        prior = usage.aggregate(data.load_stats(week.stats(week.season - 1), cfg))
        agg = usage.blend_prior(agg, prior, pb)
    return agg, st


def build(week, cfg, agg=None, st=None):
    """Returns (proj, sims). Pass agg/st to reuse loaded stats (backtest sweeps)."""
    m, sc = cfg['model'], cfg['scoring']
    n = m['n_sims']
    rng = np.random.default_rng(m['seed'])
    fd_all = data.load_slate(week.fd_players, cfg['status'])
    fd = data.active(fd_all)
    lines = data.load_lines(week.lines)
    if agg is None:
        agg, st = load_usage(week, cfg)
    xt, xc = usage.redistribute_out(agg, data.newly_out(fd_all, cfg['status']), fd, m['injury']['redistribute_share'])
    tf = sim.team_factors(rng, lines, m['correlation'], n)
    league_dst = fd[fd.Position == 'D'].FPPG.mean()

    rows, sims = [], []
    for r in fd.itertuples():
        t, k, pos = r.Team, r.Key, r.Position
        opp, implied = lines.opp[t], lines.implied[t]
        scale, f = implied / m['league_team_total'], tf[t]
        if pos == 'D':
            pts = sim.sim_dst(rng, r.FPPG, league_dst, lines.implied[opp], tf[opp], m, sc['dst'], n)
        elif k in agg.index:
            pts = sim.sim_skill(rng, agg.loc[k], pos, scale, f, xt.get(k, 0), xc.get(k, 0), m, sc, n)
        else:
            pts = sim.sim_fallback(rng, r.FPPG, scale, f, m, n)
        if r.Inj == 'Q':
            pts = pts * (rng.random(n) > m['injury']['questionable_inactive_prob'])
        sims.append(pts)
        rows.append(dict(Id=r.Id, Name=r.Nickname, Pos=pos, Team=t, Opp=opp, Salary=r.Salary, Inj=r.Inj,
                         ImpliedTeamTotal=round(implied, 1), GameTotal=round(implied + lines.implied[opp], 1),
                         FD_FPPG=round(r.FPPG, 1), GainedVol=round(xt.get(k, 0) + xc.get(k, 0), 2), Key=k,
                         **summarize(pts, r.Salary)))
    proj = pd.DataFrame(rows)
    proj['StartingQB'] = (proj.Pos == 'QB') & proj.Key.isin(usage.starting_qbs(st))
    order = proj.Proj.sort_values(ascending=False, kind='stable').index
    return proj.loc[order].drop(columns='Key').reset_index(drop=True), np.array(sims)[order]


def summarize(pts, salary):
    return dict(Proj=round(pts.mean(), 1), Median=round(np.median(pts), 1), Ceiling_p90=round(np.percentile(pts, 90), 1),
                P_20plus=round((pts >= 20).mean(), 3), Value_per_1k=round(pts.mean() / salary * 1000, 2))


def save(week, proj, sims):
    proj.to_csv(week.output('proj.csv'), index=False)
    np.save(week.output('sims.npy'), sims)


def load(week):
    return pd.read_csv(week.proj), np.load(week.sims)
