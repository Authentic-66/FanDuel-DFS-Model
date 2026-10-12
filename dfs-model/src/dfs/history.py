"""Refits on several past seasons (docs/phase2_history.md): Vegas lines and DST scoring from the nflverse schedule and
team stats, the injury-redistribution share from games a starter missed, and season-weighted leave-one-season-out
helpers. Inputs are the data/cache files written by `fetch_stats.py --seasons ... --history`. Nothing here is used
by the weekly pipeline."""
import os

import numpy as np
import pandas as pd

from . import data
from .scoring import dst_points

SKILL = ['RB', 'WR', 'TE']


def season_weights(seasons, decay=0.75):
    """Weight per season: the latest counts 1, each season back counts `decay` times the one after it."""
    last = max(seasons)
    return {s: decay ** (last - s) for s in seasons}


def load_lines(cache, season, cfg):
    """One row per team per regular-season game from schedule_<season>.csv: season, week, team, opp, implied,
    opp_implied, margin (the team's expected margin: + = favoured), scored, allowed. FanDuel team codes."""
    g = pd.read_csv(os.path.join(cache, f'schedule_{season}.csv'), low_memory=False)
    g = g[(g.game_type == 'REG') & g.home_score.notna()]
    fd = cfg['teams']['nflverse_to_fd']
    half = lambda team, opp, sign, scored, allowed: pd.DataFrame(dict(
        season=season, week=g.week, team=g[team].replace(fd), opp=g[opp].replace(fd),
        implied=g.total_line / 2 + sign * g.spread_line / 2, opp_implied=g.total_line / 2 - sign * g.spread_line / 2,
        margin=sign * g.spread_line, scored=g[scored], allowed=g[allowed]))
    return pd.concat([half('home_team', 'away_team', 1, 'home_score', 'away_score'),      # spread_line: + = home favoured
                      half('away_team', 'home_team', -1, 'away_score', 'home_score')], ignore_index=True)


def dst_games(cache, season, cfg):
    """load_lines rows plus each team's actual FanDuel DST points (FPTS) and its average over its earlier games that
    season (prior_avg, NaN in its first game). Points allowed = opponent's score less the points its own defence and
    special teams scored (7 per return TD, 2 per safety): FanDuel charges a DST only for points its defence gave up."""
    t = pd.read_csv(os.path.join(cache, f'stats_team_week_{season}.csv'), low_memory=False)
    t = t[t.season_type == 'REG'].assign(team=lambda d: d.team.replace(cfg['teams']['nflverse_to_fd'])).fillna(0)
    t = t.assign(ret_td=t.def_tds + t.special_teams_tds)
    t = t.set_index(['week', 'team'])
    g = load_lines(cache, season, cfg)
    own = t.reindex(pd.MultiIndex.from_frame(g[['week', 'team']])).reset_index(drop=True)
    opp = t.reindex(pd.MultiIndex.from_frame(g[['week', 'opp']])).reset_index(drop=True)
    allowed = np.maximum(g.allowed - 7 * opp.ret_td - 2 * opp.def_safeties, 0)
    g['FPTS'] = dst_points(cfg['scoring']['dst'], allowed, sacks=own.def_sacks, ints=own.def_interceptions,
                           fumble_recoveries=own.fumble_recovery_opp, return_td=own.ret_td, safeties=own.def_safeties,
                           blocked_kicks=own.def_punt_blocks + own.def_fg_blocks + own.def_pat_blocks).astype(float)
    g = g.sort_values(['team', 'week']).reset_index(drop=True)
    g['prior_avg'] = g.groupby('team').FPTS.transform(lambda s: s.shift().expanding().mean())
    return g


def wls(x, y, w):
    """Weighted least squares with an intercept. x: (n, k). Returns (intercept, coefficients)."""
    a = np.c_[np.ones(len(y)), x] * np.sqrt(w)[:, None]
    beta = np.linalg.lstsq(a, y * np.sqrt(w), rcond=None)[0]
    return beta[0], beta[1:]


def loso(df, cols, weights, y='FPTS'):
    """Leave-one-season-out weighted regression of y on cols. Returns (out-of-season predictions aligned to df,
    per-held-out-season coefficient rows, coefficients fit on every season)."""
    pred, fits = pd.Series(np.nan, index=df.index), []
    w = df.season.map(weights).values
    for s in sorted(df.season.unique()):
        tr = (df.season != s).values
        b0, b = wls(df.loc[tr, cols].values, df.loc[tr, y].values, w[tr])
        pred[~tr] = b0 + df.loc[~tr, cols].values @ b
        fits.append(dict(held_out=s, intercept=b0, **dict(zip(cols, b))))
    b0, b = wls(df[cols].values, df[y].values, w)
    return pred, pd.DataFrame(fits), dict(intercept=b0, **dict(zip(cols, b)))


# --- injury redistribution -------------------------------------------------------------------------------------------

def absences(st, min_week=4, run=3, starters=None):
    """First game each starter missed in a season, with where his volume went. st: data.load_stats frame of one season.
    A starter = RB/WR/TE who played each of his team's previous `run` games and averaged at least starters[pos][col]
    per game over his games for that team (defaults: WR 6 targets, TE 4.5 targets, RB 10 carries or 3 targets).
    The missed game = his team played in week >= min_week and he has no stat row for any team. Only his first miss
    of the season counts (the model hands a first-time OUT player out in full).
    One row per (player, col in tgt/car) that clears the threshold:
      base        his per-game volume before the game
      others_base what the rest of the team's RB/WR/TE averaged in the games he played
      others      what they got in the game he missed (+ _same / _other: split by his position / the other positions)
    The share that reached his teammates is (others - others_base) / base."""
    starters = starters or {'WR': {'tgt': 6.0}, 'TE': {'tgt': 4.5}, 'RB': {'car': 10.0, 'tgt': 3.0}}
    col = {'tgt': 'targets', 'car': 'carries'}
    sk = st[st.position.isin(SKILL)]
    moved = set(zip(sk.k, sk.week))      # he played that week for another team (traded or released): not an absence
    rows = []
    for team, tm in sk.groupby('team'):
        weeks = sorted(tm.week.unique())
        vol = {c: tm.pivot_table(index='week', columns='position', values=col[c], aggfunc='sum').reindex(weeks).fillna(0)
               for c in col}
        for k, pl in tm.groupby('k'):
            pos = pl.position.iloc[0]
            played = set(pl.week)
            missed = [i for i, w in enumerate(weeks) if w not in played and w > min(played)]
            if not missed:
                continue
            i, w = missed[0], weeks[missed[0]]                     # his first missed game: one event a season at most
            if w < min_week or i < run or not all(x in played for x in weeks[i - run:i]) or (k, w) in moved:
                continue
            before = pl[pl.week < w].groupby('week')[list(col.values())].sum()
            for c, need in starters[pos].items():
                mine = before[col[c]]
                if mine.mean() < need:
                    continue
                team_before = vol[c].loc[mine.index]
                rows.append(dict(
                    season=int(st.season.iloc[0]), week=w, team=team, k=k, pos=pos, col=c, base=mine.mean(),
                    others_base=(team_before.sum(axis=1) - mine).mean(), others=vol[c].loc[w].sum(),
                    same_base=(team_before[pos] - mine).mean(), same=vol[c].loc[w].get(pos, 0.0)))
    out = pd.DataFrame(rows, columns=['season', 'week', 'team', 'k', 'pos', 'col', 'base', 'others_base', 'others',
                                      'same_base', 'same'])
    out['gain'] = out.others - out.others_base
    out['gain_same'] = out.same - out.same_base
    out['gain_other'] = out.gain - out.gain_same
    return out


def share(ev, weights, gain='gain'):
    """Weighted ratio-of-sums share of the missing starters' volume that reached `gain`, with a standard error."""
    w = ev.season.map(weights).values
    s = (w * ev[gain]).sum() / (w * ev.base).sum()
    se = np.sqrt((w ** 2 * (ev[gain] - s * ev.base) ** 2).sum()) / (w * ev.base).sum()
    return s, se


# --- calibration knees -------------------------------------------------------------------------------------------------

def fit_knees(rows, weights, top_knees, rb_knees):
    """[model.calibration] with the knees searched too: the (top_knee, rb_knee) pair on the grid whose least-squares
    slopes (backtest.fit_calibration) leave the smallest weighted squared error. Returns the calibration dict."""
    from . import backtest, project
    best, best_sse = None, np.inf
    for tk in top_knees:
        for rk in rb_knees:
            cal = backtest.fit_calibration(rows, tk, rk, weights)
            sse = float((weights * (project.calibrated(rows.Proj.values, rows.Pos.values, cal) - rows.FPTS.values) ** 2).sum())
            if sse < best_sse:
                best, best_sse = cal, sse
    return best
