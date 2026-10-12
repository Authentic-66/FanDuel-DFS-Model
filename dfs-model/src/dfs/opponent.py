"""Opponent adjustment ([model.opponent]): how much more or less than average a defence gives up to one position,
beyond how good the defence is overall.

The team's Vegas implied total already prices the defence as a whole, so the overall level is divided out and only
the tilt is used: a defence that allows 10% more than the league to every position has tilt 1.0 everywhere, and one
that allows 10% more to tight ends and league average in total has a TE tilt of 1.10.

Built from games before the week only: FanDuel points allowed per game by position, as a ratio to the league average,
blended with the prior season (prior_games pseudo-games) and shrunk toward 1.0 (shrink_games pseudo-games).
"""
import numpy as np
import pandas as pd

from .scoring import stats_points

POS = ['QB', 'RB', 'WR', 'TE']


def allowed(st, sc):
    """FanDuel points each defence allowed, one row per (week, defence): columns QB, RB, WR, TE and ALL (their sum).
    st: data.load_stats frame (needs the `opp` column) of one season."""
    sk = st[st.position.isin(POS)]
    a = sk.assign(fd=stats_points(sc, sk)).pivot_table(index=['week', 'opp'], columns='position', values='fd', aggfunc='sum')
    a = a.reindex(columns=POS).fillna(0)
    return a.assign(ALL=a.sum(axis=1))


def ratios(a):
    """Per defence: games and points allowed per game relative to the league average of the same frame."""
    per_game = a.groupby(level='opp').mean()
    return (per_game / a.mean()).assign(g=a.groupby(level='opp').size())


def tilt(cur, prior, o):
    """Defence x position tilt (see module docstring). cur: allowed() of the season so far (may be empty);
    prior: allowed() of the prior season or None; o: [model.opponent] (shrink_games, prior_games).
    Returns a frame indexed by defence with columns QB, RB, WR, TE (tilt) and ALL (the overall ratio divided out)."""
    k, kp = o['shrink_games'], o['prior_games'] if prior is not None else 0
    rc = ratios(cur) if len(cur) else pd.DataFrame(columns=POS + ['ALL', 'g'], dtype=float)
    teams = sorted(set(rc.index) | (set(prior.index.get_level_values('opp')) if prior is not None else set()))
    rc = rc.reindex(teams)
    g = rc.g.fillna(0).values[:, None]
    cols = POS + ['ALL']
    rp = ratios(prior).reindex(teams)[cols].fillna(1.0).values if prior is not None else 1.0
    shrunk = (g * rc[cols].fillna(1.0).values + kp * rp + k) / (g + kp + k)
    out = pd.DataFrame(shrunk, index=teams, columns=cols)
    out[POS] = out[POS].div(out.ALL, axis=0)
    return out


def factors(pos, opp, tilts, o):
    """Multiplier on each player's projection: 1 + beta[position] * (tilt - 1), kept within 1 +/- cap. pos / opp:
    arrays, one entry per player. Players at other positions, or facing a defence with no games on record, get 1."""
    beta = o.get('beta', {})
    t = np.array([tilts.at[d, p] if p in POS and d in tilts.index else 1.0 for p, d in zip(pos, opp)])
    b = np.array([beta.get(p, 0.0) for p in pos])
    return np.clip(1 + b * (t - 1), 1 - o['cap'], 1 + o['cap'])
