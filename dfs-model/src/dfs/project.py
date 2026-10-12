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
    inj = m['injury']
    absent_mode = inj.get('absent_mode', 'skip')
    xt, xc = usage.redistribute_out(agg, data.newly_out(fd_all, cfg['status']), fd, inj['redistribute_share'],
                                    st if absent_mode == 'present_share' or inj.get('skip_already_absent', True) else None,
                                    absent_mode)
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
    for team, name in cfg['status'].get('starting_qb', {}).items():   # Doug's call beats last game's attempts
        qbs = (proj.Pos == 'QB') & (proj.Team == team)
        if not (qbs & (proj.Name == name)).any():
            raise ValueError(f'[status.starting_qb] {team}: {name!r} is not an active {team} QB on the slate')
        proj.loc[qbs, 'StartingQB'] = proj.Name[qbs] == name
    sims = adjust(proj, np.array(sims), lines, m)
    stats = pd.DataFrame([summarize(pts, sal) for pts, sal in zip(sims, proj.Salary)])
    proj[stats.columns] = stats
    order = proj.Proj.sort_values(ascending=False, kind='stable').index
    return proj.loc[order].drop(columns='Key').reset_index(drop=True), sims[order]


def calibrated(mean, pos, cal):
    """[model.calibration]: projected mean with the over-confident ranges pulled down. Every skill player loses
    top_slope of each point above top_knee; RBs also lose rb_slope of each point above rb_knee."""
    out = mean - cal['top_slope'] * np.maximum(mean - cal['top_knee'], 0)
    return out - np.where(pos == 'RB', cal['rb_slope'] * np.maximum(mean - cal['rb_knee'], 0), 0)


def dst_target(proj, lines, m):
    """[model.dst.flatten]: DST mean from opponent implied total and salary only, around the slate's simulated DST
    average. Drops the FanDuel-FPPG quality term, which has not predicted DST scoring (docs/week6_prep.md)."""
    fl = m['dst']['flatten']
    d = proj[proj.Pos == 'D']
    opp = d.Opp.map(lines.implied)
    return (d.Proj.mean() + fl['opp_implied'] * (opp - opp.mean())
            + fl['salary_per_1k'] * (d.Salary - d.Salary.mean()) / 1000)


def adjust(proj, sims, lines, m):
    """Post-simulation corrections, in order: non-starting QBs to zero ([model.qb] zero_backups), calibration shrink
    of skill players ([model.calibration], sims rescaled so their shape is kept), DST flattening ([model.dst.flatten],
    sims shifted). Returns the adjusted sims; proj.Proj must hold the unadjusted means."""
    sims = sims.copy()
    mean = sims.mean(axis=1)
    skill = (proj.Pos != 'D').values
    if m['qb'].get('zero_backups'):
        sims[((proj.Pos == 'QB') & ~proj.StartingQB).values] = 0
        no_qb = sorted(set(proj.Team) - set(proj.Team[proj.StartingQB]))
        if no_qb:
            print(f'WARNING: no starting QB flagged for {", ".join(no_qb)}: set [status.starting_qb] in week.toml')
    cal = m.get('calibration', {})
    if cal.get('enabled'):
        new = calibrated(mean, proj.Pos.values, cal)
        scale = np.where(skill & (mean > 0), new / np.where(mean > 0, mean, 1), 1.0)
        sims *= scale[:, None]
    if m['dst'].get('flatten', {}).get('enabled'):
        target = dst_target(proj, lines, m)
        sims[target.index] += (target.values - mean[target.index])[:, None]
    return sims


def summarize(pts, salary):
    return dict(Proj=round(pts.mean(), 1), Median=round(np.median(pts), 1), Ceiling_p90=round(np.percentile(pts, 90), 1),
                P_20plus=round((pts >= 20).mean(), 3), Value_per_1k=round(pts.mean() / salary * 1000, 2))


def save(week, proj, sims):
    proj.to_csv(week.output('proj.csv'), index=False)
    np.save(week.output('sims.npy'), sims)


def load(week):
    return pd.read_csv(week.proj), np.load(week.sims)
