"""Build the week's projections and correlated sims: slate + lines + stats -> proj DataFrame, sims array (rows aligned)."""
import numpy as np
import pandas as pd

from . import data, opponent, sim, usage


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
    if inj.get('routing', 'pro_rata') not in ('pro_rata', 'position'):
        raise ValueError(f'[model.injury] routing must be "pro_rata" or "position", not {inj["routing"]!r}')
    routing = inj.get('position_share') if inj.get('routing') == 'position' else None
    within = inj.get('within_position', 'pro_rata')
    if within not in ('pro_rata', 'depth_rank'):
        raise ValueError(f'[model.injury] within_position must be "pro_rata" or "depth_rank", not {within!r}')
    if routing:     # keep the *_rank shares only where the depth split is on; elsewhere pro rata inside the position
        ranked = inj.get('depth_rank_positions', list(routing)) if within == 'depth_rank' else []
        routing = {pos: {k: v for k, v in rule.items() if pos in ranked or not k.endswith('_rank')}
                   for pos, rule in routing.items()}
    xt, xc = usage.redistribute_out(agg, data.newly_out(fd_all, cfg['status']), fd, inj['redistribute_share'],
                                    st if absent_mode == 'present_share' or inj.get('skip_already_absent', True) else None,
                                    absent_mode, routing)
    moved = data.trades(fd_all, cfg['status'])
    for extra, gained in zip((xt, xc), usage.trade_volume(agg, moved, fd, inj['redistribute_share'], routing)):
        for k, v in gained.items():
            extra[k] = extra.get(k, 0) + v
    for name, fd_team, stat_team in usage.team_mismatches(agg, fd, moved):
        print(f'WARNING: FanDuel lists {name} on {fd_team}, his stats are with {stat_team}: if he was traded, add a '
              f'[[status.trade]] entry (as-is he keeps his {stat_team} volume and no teammate is adjusted)')
    tf = sim.team_factors(rng, lines, m['correlation'], n)
    league_dst = fd[fd.Position == 'D'].FPPG.mean()

    rows, sims, unrouted = [], [], {}
    for r in fd.itertuples():
        t, k, pos = r.Team, r.Key, r.Position
        opp, implied = lines.opp[t], lines.implied[t]
        scale, f = implied / m['league_team_total'], tf[t]
        if pos == 'D':
            pts = sim.sim_dst(rng, r.FPPG, league_dst, lines.implied[opp], tf[opp], m, sc['dst'], n)
        elif k in agg.index:
            before = rng.bit_generator.state
            pts = sim.sim_skill(rng, agg.loc[k], pos, scale, f, xt.get(k, 0), xc.get(k, 0), m, sc, n)
            if xt.get(k, 0) or xc.get(k, 0):    # report only (RoutingBump): the same player without the redistributed
                twin = np.random.default_rng()  # volume, on a copy of the generator so the main draws are untouched
                twin.bit_generator.state = before
                unrouted[len(sims)] = (pts.mean(), sim.sim_skill(twin, agg.loc[k], pos, scale, f, 0, 0, m, sc, n).mean())
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
    proj['RoutingBump'] = routing_bump(proj, unrouted, m)
    sims = adjust(proj, np.array(sims), lines, m)
    opp = m.get('opponent', {})
    if opp.get('enabled'):      # last: a multiplier on the finished draws, so the calibration and spread fits still hold
        prior = data.load_stats(week.stats(week.season - 1), cfg)
        tilts = opponent.tilt(opponent.allowed(st, sc), opponent.allowed(prior, sc), opp)
        f = opponent.factors(proj.Pos.values, proj.Opp.values, tilts, opp)
        proj['OppAdj'] = np.round(sims.mean(axis=1) * (f - 1), 2)      # points added or removed by the matchup
        sims = sims * f[:, None]
    stats = pd.DataFrame([summarize(pts, sal) for pts, sal in zip(sims, proj.Salary)])
    proj[stats.columns] = stats
    order = proj.Proj.sort_values(ascending=False, kind='stable').index
    return proj.loc[order].drop(columns='Key').reset_index(drop=True), sims[order]


def routing_bump(proj, unrouted, m):
    """Points each player's projection gained (or lost) from injury / trade redistribution: his calibrated mean with
    the redistributed volume minus the same without it. unrouted: {row: (raw mean with, raw mean without)}.
    For the exposure sheet, so depth players lifted into lineups can be spotted; it changes no projection."""
    bump = np.zeros(len(proj))
    cal = m.get('calibration', {})
    for i, (with_, without) in unrouted.items():
        pair, pos = np.array([with_, without]), np.repeat(proj.Pos[i], 2)
        if cal.get('enabled') and not (proj.Pos[i] == 'QB' and m['qb'].get('zero_backups') and not proj.StartingQB[i]):
            pair = calibrated(pair, pos, cal)
        bump[i] = pair[0] - pair[1]
    return np.round(bump, 1)


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


def spread_factor(mean, spec, taper=None):
    """[model.spread] factor for players projected `mean`. spec = one number (the same for everyone) or
    {low, top}: `low` up to [model.spread_taper] from, falling in a straight line to `top` at `to` and above."""
    if not isinstance(spec, dict):
        return np.full(len(mean), float(spec))
    return np.interp(mean, [taper['from'], taper['to']], [spec['low'], spec['top']])


def widen(sims, k):
    """[model.spread]: every draw moved to k times its distance from the player's mean (rows = players; k = one
    number or one per row). Draws pushed below zero are set to zero and the row is rescaled, so the mean is unchanged."""
    mu = sims.mean(axis=1, keepdims=True)
    k = np.reshape(k, (-1, 1)) if np.ndim(k) else k
    out = np.maximum(mu + k * (sims - mu), 0)
    return out * mu / np.where(out.mean(axis=1, keepdims=True) > 0, out.mean(axis=1, keepdims=True), 1)


def adjust(proj, sims, lines, m):
    """Post-simulation corrections, in order: non-starting QBs to zero ([model.qb] zero_backups), calibration shrink
    of skill players ([model.calibration]: sims shifted, or rescaled with mode = "scale"), wider spread by position
    ([model.spread], mean kept), DST flattening ([model.dst.flatten], sims shifted). Returns the adjusted sims;
    proj.Proj must hold the unadjusted means."""
    sims = sims.copy()
    skill = (proj.Pos != 'D').values
    if m['qb'].get('zero_backups'):
        sims[((proj.Pos == 'QB') & ~proj.StartingQB).values] = 0
        no_qb = sorted(set(proj.Team) - set(proj.Team[proj.StartingQB]))
        if no_qb:
            print(f'WARNING: no starting QB flagged for {", ".join(no_qb)}: set [status.starting_qb] in week.toml')
    mean = sims.mean(axis=1)
    cal = m.get('calibration', {})
    if cal.get('enabled'):
        new = calibrated(mean, proj.Pos.values, cal)
        mode = cal.get('mode', 'shift')
        if mode not in ('shift', 'scale'):
            raise ValueError(f'[model.calibration] mode must be "shift" or "scale", not {mode!r}')
        hit = skill & (mean > 0)
        if mode == 'shift':     # lower the mean, keep the simulated spread
            sims += np.where(hit, new - mean, 0.0)[:, None]
        else:                   # shrink every draw in proportion (ceilings come down with the mean)
            sims *= np.where(hit, new / np.where(mean > 0, mean, 1), 1.0)[:, None]
    for pos, spec in m.get('spread', {}).items():
        rows = (proj.Pos == pos).values & (sims.mean(axis=1) > 0)
        if spec != 1 and rows.any():
            sims[rows] = widen(sims[rows], spread_factor(sims[rows].mean(axis=1), spec, m.get('spread_taper')))
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
