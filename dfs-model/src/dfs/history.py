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


# --- simulated season rows and the tapered spread ----------------------------------------------------------------------

def season_rows(week, cfg, seasons, vegas=True, cache_dir=''):
    """backtest.season_rows for weeks 4-18 of each season (prior blend from the season before), one frame with a
    `season` column plus the matching draws. vegas: scale each team by its implied total from the schedule (how the
    weekly model runs) instead of the league average. cache_dir: keep the result there between runs."""
    from . import backtest
    path = os.path.join(cache_dir, f"rows_{'vegas' if vegas else 'neutral'}_{min(seasons)}_{max(seasons)}") if cache_dir else ''
    if path and os.path.exists(path + '.pkl'):
        return pd.read_pickle(path + '.pkl'), np.load(path + '.npy')
    rows, sims = [], []
    for s in seasons:
        ln = load_lines(week.cache, s, cfg)
        implied = dict(zip(zip(ln.week, ln.team), ln.implied)) if vegas else None
        r, x = backtest.season_rows(week.stats(s), week.stats(s - 1), cfg, range(4, 19), keep_sims=True, implied=implied)
        rows.append(r.assign(season=s))
        sims.append(x)
    rows, sims = pd.concat(rows, ignore_index=True), np.concatenate(sims)
    if path:
        rows.to_pickle(path + '.pkl')
        np.save(path + '.npy', sims)
    return rows, sims


def taper_p90(sims, mean, spec, taper):
    """90th percentile of each row's draws after [model.spread] widening (spec = number or {low, top})."""
    from . import project
    return np.percentile(project.widen(sims, project.spread_factor(mean, spec, taper)), 90, axis=1)


def fit_taper(sims, mean, actual, weights, taper, split=16.0, target=0.10, hi=2.5, steps=12, rounds=2, min_top=100):
    """{low, top} spread factors for one position (project.spread_factor): `low` so that `target` of the players
    projected under `split` beat their 90th percentile, `top` (never below 1) so that the same holds from `split`
    up; the two are solved in turn because the taper between them touches both tiers. With fewer than min_top rows
    at `split` or above there is nothing to fit a taper on, and one flat factor is fit to everyone (low = top)."""
    upper = mean >= split
    flat = upper.sum() < min_top
    spec = {'low': 1.0, 'top': 1.0}

    def solve(keys, rows):
        beat = lambda v: np.average(actual[rows] > taper_p90(sims[rows], mean[rows], {**spec, **dict.fromkeys(keys, v)}, taper),
                                    weights=weights[rows])
        if beat(1.0) <= target:
            return 1.0
        a, b = 1.0, hi
        for _ in range(steps):
            mid = (a + b) / 2
            a, b = (a, mid) if beat(mid) <= target else (mid, b)
        return round(b, 3)

    if flat:
        k = solve(['low', 'top'], np.ones(len(mean), bool))
        return {'low': k, 'top': k}
    for _ in range(rounds):
        spec['low'] = solve(['low'], ~upper)
        spec['top'] = solve(['top'], upper)
    return spec


def within_position(st, ev):
    """How a missing starter's volume was split among the teammates at HIS position. st: one season's stats frame;
    ev: that season's rows of absences(). For each event, the same-position teammates who played the missed game are
    ranked by their per-game volume over the games the missing player played (rank 1 = the largest; 3 = third and
    lower). One row per teammate: base, actual in the missed game, gain = actual - base, and prorata = the event's
    total same-position gain split in proportion to base, which is what the model's rule hands him."""
    col = {'tgt': 'targets', 'car': 'carries'}
    rows = []
    for e in ev.itertuples():
        tm = st[(st.team == e.team) & (st.position == e.pos)]
        his = set(tm.week[(tm.k == e.k) & (tm.week < e.week)])
        now = tm[(tm.week == e.week) & (tm.k != e.k)].groupby('k')[col[e.col]].sum()
        base = tm[tm.week.isin(his)].groupby('k')[col[e.col]].sum().reindex(now.index).fillna(0) / len(his)
        if not len(now) or base.sum() <= 0:
            continue
        order = base.sort_values(ascending=False, kind='stable').index
        gain = (now - base).reindex(order)
        for i, k in enumerate(order):
            rows.append(dict(season=e.season, week=e.week, team=e.team, out=e.k, pos=e.pos, col=e.col, mate=k,
                             rank=min(i + 1, 3), base=base[k], actual=now[k], gain=gain[k],
                             prorata=gain.sum() * base[k] / base.sum()))
    return pd.DataFrame(rows)
