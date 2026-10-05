"""Correlated Monte Carlo simulation of FanDuel points (config [model] sections).

Correlation: each team gets a scoring multiplier f = exp(team noise + game noise + shift); teammates share f, and the
two teams in a game share the game noise. Volume and TD rates scale with f, so stacks move together.
"""
import numpy as np

from .scoring import dst_points, skill_points


def shrink(num, den, prior):
    """Per-opportunity rate shrunk toward a league prior {'mean', 'k' pseudo-opportunities}."""
    return (num + prior['mean'] * prior['k']) / (den + prior['k'])


def game_order(games):
    return sorted(games)


def team_factors(rng, lines, corr, n):
    game_noise = {g: rng.normal(0, corr['game_sd'], n) for g in game_order(set(lines.game))}
    return {t: np.exp(rng.normal(0, corr['team_sd'], n) + game_noise[lines.game[t]] + corr['shift']) for t in lines.index}


def sim_skill(rng, a, pos, scale, f, extra_tgt, extra_car, m, sc, n):
    """One QB/RB/WR/TE (FanDuel pos) from aggregated usage `a` (see usage.py). scale = implied / league total."""
    pr = m['priors']
    vol = 1 + m['volume_elasticity'] * (scale - 1)
    c = {}
    if pos == 'QB' and a.u_att > 0:
        q = m['qb']
        att = (a.u_att + q['prior_attempts']) / (a.u_g + 1) * vol * np.exp(rng.normal(0, q['att_sd'], n))
        c['pass_yds'] = att * shrink(a.py, a.att, pr['ypa']) * f ** q['yds_team_exp'] * np.exp(rng.normal(0, q['yds_sd'], n))
        c['pass_td'] = rng.poisson(att * shrink(a.ptd, a.att, pr['pass_td']) * f)
        c['ints'] = rng.poisson(att * shrink(a.ints, a.att, pr['int']), n)
    car = (a.u_car / a.u_g + extra_car) * vol
    if car > 0:
        r = m['rush']
        ca = car * np.exp(rng.normal(0, r['att_sd'], n)) * f ** r['att_team_exp']
        c['rush_yds'] = ca * shrink(a.ry, a.car, pr['ypc']) * np.exp(rng.normal(0, r['yds_sd'], n))
        c['rush_td'] = rng.poisson(ca * shrink(a.rtd, a.car, pr['rush_td']) * f)
    tgt = (a.u_tgt / a.u_g + extra_tgt) * vol
    if tgt > 0:
        r = m['rec']
        tt = tgt * np.exp(rng.normal(0, r['tgt_sd'], n)) * f ** r['tgt_team_exp']
        cr = shrink(a.rec, a.tgt, pr['catch_rate'])
        c['rec'] = rng.binomial(np.maximum(tt.round().astype(int), 0), min(cr, r['catch_rate_max']))
        ypc = shrink(a.rey, a.tgt, pr['ypt']) / max(cr, r['catch_rate_floor'])
        c['rec_yds'] = c['rec'] * ypc * np.exp(rng.normal(0, r['yds_sd'], n))
        c['rec_td'] = rng.poisson(tt * shrink(a.retd, a.tgt, pr['rec_td']) * f)
    return np.asarray(skill_points(sc, **c), dtype=float) * np.ones(n)


def sim_dst(rng, fppg, league_fppg, opp_implied, f_opp, m, dst, n):
    d = m['dst']
    q = (1 - d['quality_shrink']) + d['quality_shrink'] * fppg / league_fppg
    sacks = rng.poisson(d['sacks'] * q, n)
    turnovers = rng.poisson(d['turnovers'] * q * (m['league_team_total'] / opp_implied) ** d['turnover_total_exp'], n)
    td = rng.binomial(1, d['return_td_prob'], n)
    # INTs and fumble recoveries both score dst.interception (= dst.fumble_recovery) points
    return dst_points(dst, opp_implied * f_opp, sacks=sacks, ints=turnovers, return_td=td).astype(float)


def sim_fallback(rng, fppg, scale, f, m, n):
    fb = m['fallback']
    return np.maximum(fppg * scale ** fb['total_exp'] * f ** fb['team_exp'] * np.exp(rng.normal(0, fb['sd'], n)), 0)
