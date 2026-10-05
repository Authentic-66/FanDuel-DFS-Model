"""Backtests for projection settings (Phase 2 #1: prior-season blend).

slate_backtest: the full weekly pipeline on an archived slate (Vegas, status, redistribution) vs FanDuel results.
season_backtest: per-week projections from earlier weeks of a season (+ prior-season blend) vs actual FanDuel points
    computed from nflverse stats. No Vegas lines or slate, so every team gets the league-average total; tests the
    usage/efficiency estimate itself over many weeks.
Both grade the same model-independent player set: players averaging >= min_fppg FanDuel points before the week.
"""
import itertools
import os

import numpy as np
import pandas as pd

from . import analyze, data, project, sim, usage
from .config import deep_merge
from .scoring import stats_points


def metrics(df):
    """df: Proj, FPTS (and optionally Ceiling_p90). slope = OLS slope of actual on projection (1 = calibrated,
    < 1 = overconfident spread); gap_X = mean projected - mean actual within that projection tier."""
    p, a = df.Proj.values, df.FPTS.values
    out = dict(n=len(df), r=np.corrcoef(p, a)[0, 1], rmse=np.sqrt(np.mean((p - a) ** 2)), mae=np.mean(np.abs(p - a)),
               bias=np.mean(p - a), slope=np.cov(p, a)[0, 1] / np.var(p, ddof=1))
    for lo, hi in [(14, 20), (20, 99)]:
        s = df[(df.Proj >= lo) & (df.Proj < hi)]
        out[f'n_{lo}+'] = len(s)
        out[f'gap_{lo}+'] = s.Proj.mean() - s.FPTS.mean() if len(s) else np.nan
    if 'Ceiling_p90' in df:
        out['over_p90'] = np.mean(a > df.Ceiling_p90.values)   # target 0.10
    return out


def blend_cfg(cfg, **pb):
    return deep_merge(cfg, {'model': {'prior_blend': pb}})


def grid(usage_games, efficiency_games, **fixed):
    return [dict(usage_games=u, efficiency_games=e, **fixed) for u, e in itertools.product(usage_games, efficiency_games)]


# --- archived slate ---------------------------------------------------------------------------------------------

def slate_backtest(week, cfg, settings, min_fppg=5.0, exclude=()):
    """Run the real projection pipeline for each prior_blend setting; grade skill players with FanDuel FPPG >= min_fppg
    (pre-slate, from fd_players.csv) against results_players.csv. `exclude`: names to drop (e.g. in-game injuries)."""
    st = data.load_stats(week.stats(), cfg, before_week=week.number)
    cur = usage.aggregate(st)
    prior = usage.aggregate(data.load_stats(week.stats(week.season - 1), cfg))
    actuals = analyze.load_actuals(week.results_players)
    fd = data.load_slate(week.fd_players, cfg['status'])
    graded = set(fd.Id[(fd.Position != 'D') & (fd.FPPG >= min_fppg)])
    rows, projs = [], {}
    for pb in settings:
        c = blend_cfg(cfg, **pb)
        proj, _ = project.build(week, c, agg=usage.blend_prior(cur, prior, c['model']['prior_blend']), st=st)
        j = analyze.joined(proj, actuals)
        j = j[j.Id.isin(graded) & ~j.Name.isin(exclude)]
        rows.append({**pb, **metrics(j)})
        projs[tuple(pb.values())] = proj
    return pd.DataFrame(rows), projs


# --- season of weekly stats -------------------------------------------------------------------------------------

def season_backtest(path, prior_path, cfg, settings, weeks, min_fppg=5.0, n_sims=2000, seed=7):
    """For each week w: usage from weeks < w of the season, blended per setting; neutral team totals; independent team
    factor per player (only means and p90 are graded, so cross-player correlation is irrelevant).
    Returns (per-setting metrics pooled over weeks, per-week per-setting metrics)."""
    m, sc = cfg['model'], cfg['scoring']
    season = data.load_stats(path, cfg)
    season = season.assign(fd=stats_points(sc, season))
    prior = usage.aggregate(data.load_stats(prior_path, cfg))
    corr = m['correlation']
    team_sd = np.hypot(corr['team_sd'], corr['game_sd'])
    pooled, weekly = {i: [] for i in range(len(settings))}, []
    for w in weeks:
        before = season[season.week < w]
        cur = usage.aggregate(before)
        fppg = before.groupby('k').fd.sum() / cur.g
        now = season[(season.week == w) & season.position.isin(['QB', 'RB', 'WR', 'TE'])]
        now = now[now.k.isin(fppg.index[fppg >= min_fppg])].drop_duplicates('k')
        for i, pb in enumerate(settings):
            c = blend_cfg(cfg, **pb)
            agg = usage.blend_prior(cur, prior, c['model']['prior_blend'])
            rng = np.random.default_rng(seed)
            res = []
            for r in now.itertuples():
                f = np.exp(rng.normal(0, team_sd, n_sims) + corr['shift'])
                pts = sim.sim_skill(rng, agg.loc[r.k], r.position, 1.0, f, 0, 0, c['model'], sc, n_sims)
                res.append((pts.mean(), np.percentile(pts, 90), r.fd))
            df = pd.DataFrame(res, columns=['Proj', 'Ceiling_p90', 'FPTS'])
            pooled[i].append(df)
            weekly.append({'week': w, **pb, **metrics(df)})
    summary = pd.DataFrame([{**pb, **metrics(pd.concat(pooled[i]))} for i, pb in enumerate(settings)])
    return summary, pd.DataFrame(weekly)


# --- Phase 2 #2: leverage on an archived slate --------------------------------------------------------------------

def est_rank(points, top, quantiles, field_size):
    """Contest rank for a score: exact from the top-N results, else interpolated from field quantiles."""
    if points >= top.Points.min():
        return int((top.Points > points).sum() + 1)
    q = np.interp(points, np.r_[0, quantiles.points], np.r_[0, quantiles['quantile']])   # below median: rough
    return int(round((1 - q) * field_size)) + 1


def leverage_backtest(week, cfg, settings, field_size, sources=('cv',)):
    """Rebuild the week (current model + that week's overrides), attach ownership, and run the optimizer once per
    leverage setting; grade every lineup against actual FanDuel points.
    sources: 'cv' = out-of-fold predicted ownership for this week (what a pre-lock model could know, roughly);
    'actual' = the field's real %Drafted (oracle: the most leverage could do with perfect ownership)."""
    from . import optimize, ownership, overrides
    proj, sims = project.build(week, cfg)
    proj, sims = overrides.apply(proj, sims, cfg['overrides'])
    oc = cfg['ownership']
    train = ownership.training_frame(week, cfg)
    own = {'cv': pd.Series(ownership.cross_validate(train, oc) * 100, index=train.Id),
           'actual': pd.Series(train.own.values * 100, index=train.Id)}
    act = analyze.load_actuals(week.results_players).set_index('Id')
    top = pd.read_csv(os.path.join(week.data, 'results_top2000.csv'))
    qs = pd.read_csv(os.path.join(week.data, 'results_field_quantiles.csv'))
    rows = []
    for src in sources:
        p = proj.assign(Own_proj=proj.Id.map(own[src]).fillna(0).round(2))
        for s in settings:
            if src == 'actual' and not s.get('enabled'):
                continue   # leverage off ignores ownership: same as the 'cv' baseline
            c = deep_merge(cfg, {'optimizer': {'leverage': s}})
            df = optimize.eligible_pool(p, c['prefs'], c['optimizer'])
            lineups, _ = optimize.build_lineups(df, sims, c)
            pts = np.array([act.FPTS.reindex(df.Id[lp]).fillna(0).sum() for lp in lineups])
            ranks = np.array([est_rank(x, top, qs, field_size) for x in pts])
            rows.append(dict(own_source=src, **s, mean=pts.mean(), sd=pts.std(), best=pts.max(), best_rank=ranks.min(),
                             top_1pct=int((ranks <= 0.01 * field_size).sum()),
                             top_10pct=int((ranks <= 0.10 * field_size).sum()),
                             proj=np.mean([df.Proj[lp].sum() for lp in lineups]),
                             own_proj=np.mean([df.Own_proj[lp].sum() for lp in lineups]),
                             own_actual=np.mean([act.own_pct.reindex(df.Id[lp]).fillna(0).sum() for lp in lineups]),
                             stacks=pd.Series([df.Team[[i for i in lp if df.Pos[i] == 'QB'][0]] for lp in lineups])
                             .value_counts().to_dict()))
            print(rows[-1])
    return pd.DataFrame(rows)
