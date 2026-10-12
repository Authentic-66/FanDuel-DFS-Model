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


# --- calibration shrink ([model.calibration]) ----------------------------------------------------------------------

def season_rows(path, prior_path, cfg, weeks, min_fppg=5.0, n_sims=2000, seed=7, keep_sims=False, implied=None):
    """Uncalibrated per-player projections for each week of a season, as in season_backtest (neutral team totals,
    usage from earlier weeks + prior blend). Columns: fold, Pos, Proj, FPTS, Ceiling_p90 (uncalibrated), week, team, opp.
    keep_sims: return (rows, sims) with one row of draws per row of the frame (for fit_spread).
    implied: {(week, team): Vegas implied total} to scale each player by his team's total as the weekly model does
    (history.load_lines); teams missing from it, and every team when it is None, get the league-average total."""
    m, sc = cfg['model'], cfg['scoring']
    season = data.load_stats(path, cfg)
    season = season.assign(fd=stats_points(sc, season))
    year = int(season.season.iloc[0])
    prior = usage.aggregate(data.load_stats(prior_path, cfg))
    team_sd = np.hypot(m['correlation']['team_sd'], m['correlation']['game_sd'])
    out, sims = [], []
    for w in weeks:
        before = season[season.week < w]
        cur = usage.aggregate(before)
        fppg = before.groupby('k').fd.sum() / cur.g
        now = season[(season.week == w) & season.position.isin(['QB', 'RB', 'WR', 'TE'])]
        now = now[now.k.isin(fppg.index[fppg >= min_fppg])].drop_duplicates('k')
        agg = usage.blend_prior(cur, prior, m['prior_blend'])
        rng = np.random.default_rng(seed)
        for r in now.itertuples():
            f = np.exp(rng.normal(0, team_sd, n_sims) + m['correlation']['shift'])
            scale = implied.get((w, r.team), m['league_team_total']) / m['league_team_total'] if implied else 1.0
            pts = sim.sim_skill(rng, agg.loc[r.k], r.position, scale, f, 0, 0, m, sc, n_sims)
            out.append((f'{year}-w{w:02d}', r.position, pts.mean(), r.fd, np.percentile(pts, 90), w, r.team,
                        getattr(r, 'opp', '')))
            if keep_sims:
                sims.append(pts.astype(np.float32))
    rows = pd.DataFrame(out, columns=['fold', 'Pos', 'Proj', 'FPTS', 'Ceiling_p90', 'week', 'team', 'opp'])
    return (rows, np.array(sims)) if keep_sims else rows


def slate_rows(week, cfg, min_fppg=5.0):
    """Uncalibrated, unwidened projections from the real pipeline on an archived slate vs FanDuel results: skill players with
    FanDuel FPPG >= min_fppg, starting QBs only. Columns: fold, Pos, Proj, FPTS (+ Name)."""
    off = {'calibration': {'enabled': False}, 'spread': dict.fromkeys(cfg['model'].get('spread', {}), 1.0)}
    c = deep_merge(cfg, {'model': off})
    proj, _ = project.build(week, c)
    fd = data.load_slate(week.fd_players, c['status'])
    j = analyze.joined(proj, analyze.load_actuals(week.results_players))
    j = j[j.Id.isin(set(fd.Id[(fd.Position != 'D') & (fd.FPPG >= min_fppg)])) & ((j.Pos != 'QB') | j.StartingQB)]
    return j.assign(fold=week.name)[['fold', 'Pos', 'Proj', 'FPTS', 'Ceiling_p90', 'Name']]


MAX_SLOPE = 0.6   # a slope near 1 would flatten (and above 1 invert) the ranking of the top projections


def fit_calibration(rows, top_knee, rb_knee, weights=None):
    """Least-squares (top_slope, rb_slope) for project.calibrated on rows (Pos, Proj, FPTS): regress the
    over-projection Proj - FPTS on the two hinge terms, no intercept. Slopes are kept in [0, MAX_SLOPE].
    weights: optional per-row weights (e.g. recent seasons count more)."""
    h = np.c_[np.maximum(rows.Proj - top_knee, 0), (rows.Pos == 'RB') * np.maximum(rows.Proj - rb_knee, 0)]
    y = (rows.Proj - rows.FPTS).values
    if weights is not None:
        root = np.sqrt(np.asarray(weights, dtype=float))
        h, y = h * root[:, None], y * root
    top, rb = np.linalg.lstsq(h, y, rcond=None)[0]
    if not 0 <= top <= MAX_SLOPE:     # pin it at the bound and refit the RB slope on what is left
        top = float(np.clip(top, 0, MAX_SLOPE))
        rb = (h[:, 1] @ (y - top * h[:, 0])) / (h[:, 1] @ h[:, 1])
    if not 0 <= rb <= MAX_SLOPE:
        rb = float(np.clip(rb, 0, MAX_SLOPE))
        top = float(np.clip((h[:, 0] @ (y - rb * h[:, 1])) / (h[:, 0] @ h[:, 0]), 0, MAX_SLOPE))
    return dict(top_knee=top_knee, top_slope=float(top), rb_knee=rb_knee, rb_slope=float(rb))


def calibration_cv(rows, top_knee, rb_knee):
    """Leave-one-week-out: each fold's rows are calibrated with slopes fit on every other fold. Returns rows with
    Cal (out-of-fold calibrated projection) and the per-fold slopes."""
    out, fits = [], []
    for fold in sorted(rows.fold.unique()):
        cal = fit_calibration(rows[rows.fold != fold], top_knee, rb_knee)
        test = rows[rows.fold == fold]
        out.append(test.assign(Cal=project.calibrated(test.Proj.values, test.Pos.values, cal)))
        fits.append(dict(fold=fold, **cal))
    return pd.concat(out), pd.DataFrame(fits)


# --- simulation spread ([model.spread]) ---------------------------------------------------------------------------------

def p90_coverage(sims, actual, k=1.0, weights=None):
    """Share of rows (weighted if `weights`) whose actual score beat the 90th percentile of their draws widened by k
    (target 0.10)."""
    return float(np.average(actual > np.percentile(project.widen(sims, k), 90, axis=1), weights=weights))


def fit_spread(sims, actual, target=0.10, hi=3.0, steps=20, weights=None):
    """Smallest spread factor k in [1, hi] (project.widen) at which no more than `target` of the rows beat their
    90th percentile: bisection, coverage falls as k grows. 1.0 if the draws are already wide enough."""
    if p90_coverage(sims, actual, weights=weights) <= target:
        return 1.0
    lo = 1.0
    for _ in range(steps):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if p90_coverage(sims, actual, mid, weights) <= target else (mid, hi)
    return round(hi, 3)


def spread_cv(rows, sims, pos):
    """Leave-one-week-out spread factor for one position. rows: fold, Pos, FPTS; sims: calibrated draws, one row
    per row of `rows`. Returns (rows of that position with P90 before / P90_wide out-of-fold, per-fold factors)."""
    keep = (rows.Pos == pos).values
    d, s = rows[keep].reset_index(drop=True), sims[keep]
    d['P90'], d['P90_wide'], fits = np.percentile(s, 90, axis=1), np.nan, []
    for fold in sorted(d.fold.unique()):
        test = (d.fold == fold).values
        k = fit_spread(s[~test], d.FPTS.values[~test])
        d.loc[test, 'P90_wide'] = np.percentile(project.widen(s[test], k), 90, axis=1)
        fits.append(dict(fold=fold, k=k))
    return d, pd.DataFrame(fits)


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
