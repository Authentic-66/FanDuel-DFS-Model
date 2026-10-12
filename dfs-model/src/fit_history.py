"""Refit the DST coefficients, the injury-redistribution share, the calibration and the simulation spread on several
past seasons, leave-one-season-out with recent seasons weighted more, and print each next to the current default.
Changes nothing in config: the tables go to weeks/history/ and docs/phase2_history.md for Doug to decide.
Needs `fetch_stats.py --seasons <first-1>-<last> --history` first (the season before the first is the prior blend)."""
import os

import numpy as np
import pandas as pd

from dfs import backtest as bt, config, data, history as h, project

week, cfg, a = config.cli(__doc__, [
    (['--seasons'], dict(default='2021-2025')),
    (['--decay'], dict(type=float, default=0.75, help='weight of each season relative to the one after it')),
    (['--rows-cache'], dict(default='', help='folder to keep the simulated season rows between runs')),
    (['--skip-sims'], dict(action='store_true', help='DST and injury share only')),
])
lo, hi = map(int, a.seasons.split('-'))
seasons = list(range(lo, hi + 1))
W = h.season_weights(seasons, a.decay)
m = cfg['model']
out_dir = os.path.join(week.root, 'weeks', 'history')
os.makedirs(out_dir, exist_ok=True)
save = lambda df, name: df.to_csv(os.path.join(out_dir, name), index=False)
pd.set_option('display.width', 250)
rmse = lambda e, w=None: float(np.sqrt(np.average(np.asarray(e) ** 2, weights=w)))
print('season weights:', {s: round(w, 2) for s, w in W.items()})

# --- coverage ---------------------------------------------------------------------------------------------------------
cov = []
for s in [lo - 1] + seasons:
    p = pd.read_csv(week.stats(s), low_memory=False)
    p = p[p.season_type == 'REG']
    g = pd.read_csv(os.path.join(week.cache, f'schedule_{s}.csv'), low_memory=False)
    g = g[g.game_type == 'REG']
    t = pd.read_csv(os.path.join(week.cache, f'stats_team_week_{s}.csv'), low_memory=False)
    cov.append(dict(season=s, weeks=p.week.nunique(), teams=p.team.nunique(), player_rows=len(p),
                    skill_rows=int(p.position.isin(['QB', 'RB', 'WR', 'TE']).sum()), games=len(g),
                    team_rows=int((t.season_type == 'REG').sum()), missing_spread=int(g.spread_line.isna().sum()),
                    missing_total=int(g.total_line.isna().sum()), missing_score=int(g.home_score.isna().sum())))
cov = pd.DataFrame(cov)
print('\nCOVERAGE (regular season)\n' + cov.to_string(index=False))
save(cov, 'coverage.csv')

# --- DST --------------------------------------------------------------------------------------------------------------
d = pd.concat([h.dst_games(week.cache, s, cfg) for s in seasons], ignore_index=True)
d = d[d.week >= 4].reset_index(drop=True)            # prior_avg needs a few games; the model is graded from week 4 too
cols = ['FPTS', 'opp_implied', 'margin', 'prior_avg']
d[cols] = d[cols] - d.groupby(['season', 'week'])[cols].transform('mean')    # around the week's average, as the model does
w = d.season.map(W).values
cur = m['dst']['flatten']['opp_implied']
rows = [dict(model='flat (every DST the same)', rmse=rmse(d.FPTS, w), r=np.nan),
        dict(model=f'current: {cur} x opponent implied total', rmse=rmse(d.FPTS - cur * d.opp_implied, w),
             r=np.corrcoef(cur * d.opp_implied, d.FPTS)[0, 1], opp_implied=cur)]
dst_fits = []
for label, xs in [('opponent implied total', ['opp_implied']), ('+ own expected margin', ['opp_implied', 'margin']),
                  ('+ own DST average so far', ['opp_implied', 'prior_avg']),
                  ('all three', ['opp_implied', 'margin', 'prior_avg'])]:
    pred, fits, full = h.loso(d, xs, W)
    rows.append(dict(model='refit: ' + label, rmse=rmse(d.FPTS - pred, w), r=np.corrcoef(pred, d.FPTS)[0, 1],
                     **{x: full[x] for x in xs}, **{x + '_range': '%.2f to %.2f' % (fits[x].min(), fits[x].max()) for x in xs}))
    dst_fits.append(fits.assign(model=label))
dst = pd.DataFrame(rows)
print(f'\nDST ({len(d)} team-games, weeks 4-18; rmse and r are out of season for the refits)\n' + dst.round(3).to_string(index=False))
by_season = d.assign(e_cur=(d.FPTS - cur * d.opp_implied) ** 2, e_flat=d.FPTS ** 2,
                     r_x=d.opp_implied).groupby('season').apply(
    lambda x: pd.Series(dict(n=len(x), slope=np.polyfit(x.opp_implied, x.FPTS, 1)[0], r=np.corrcoef(x.opp_implied, x.FPTS)[0, 1],
                             rmse_flat=np.sqrt(x.e_flat.mean()), rmse_current=np.sqrt(x.e_cur.mean()))))
print(by_season.round(3).to_string())
save(dst, 'dst.csv'); save(pd.concat(dst_fits), 'dst_fits.csv'); save(by_season.reset_index(), 'dst_by_season.csv')

# --- injury redistribution share ---------------------------------------------------------------------------------------
ev = pd.concat([h.absences(data.load_stats(week.stats(s), cfg)) for s in seasons], ignore_index=True)
save(ev, 'absences.csv')
inj = []
for label, e_all in [('all weeks', ev), ('without week 18', ev[ev.week < 18])]:
    for (pos, col), e in e_all.groupby(['pos', 'col']):
        tot, se = h.share(e, W)
        same, se_same = h.share(e, W, 'gain_same')
        other, _ = h.share(e, W, 'gain_other')
        left_out = [h.share(e[e.season != s], W)[0] for s in seasons]
        inj.append(dict(rows=label, out=pos, volume={'tgt': 'targets', 'car': 'carries'}[col], n=len(e), per_game=e.base.mean(),
                        share=tot, se=se, same_pos=same, se_same=se_same, other_pos=other,
                        loso_range='%.2f to %.2f' % (min(left_out), max(left_out)), unweighted=e.gain.sum() / e.base.sum(),
                        model_same_pos=m['injury']['redistribute_share'] * e.same_base.sum() / e.others_base.sum(),
                        model_other_pos=m['injury']['redistribute_share'] * (1 - e.same_base.sum() / e.others_base.sum())))
inj = pd.DataFrame(inj)
print(f"\nINJURY SHARE (current: {m['injury']['redistribute_share']} to all RB/WR/TE pro rata)\n" + inj.round(2).to_string(index=False))
save(inj, 'injury_share.csv')
if a.skip_sims:
    raise SystemExit

# --- simulated rows: neutral totals (how the current values were fit) and Vegas totals (how the model runs) -------------
def season_rows(variant):
    path = os.path.join(a.rows_cache, f'rows_{variant}_{lo}_{hi}') if a.rows_cache else ''
    if path and os.path.exists(path + '.pkl'):
        return pd.read_pickle(path + '.pkl'), np.load(path + '.npy')
    rows, sims = [], []
    for s in seasons:
        ln = h.load_lines(week.cache, s, cfg)
        implied = dict(zip(zip(ln.week, ln.team), ln.implied)) if variant == 'vegas' else None
        r, x = bt.season_rows(week.stats(s), week.stats(s - 1), cfg, range(4, 19), keep_sims=True, implied=implied)
        rows.append(r.assign(season=s)); sims.append(x)
        print(variant, s, len(r), 'rows', flush=True)
    rows, sims = pd.concat(rows, ignore_index=True), np.concatenate(sims)
    if path:
        rows.to_pickle(path + '.pkl'); np.save(path + '.npy', sims)
    return rows, sims


TOP_KNEES, RB_KNEES = [8, 10, 12, 14, 16, 18, 20], [0, 2, 4, 6, 8, 10, 12]
cur_cal = {k: m['calibration'][k] for k in ('top_knee', 'top_slope', 'rb_knee', 'rb_slope')}
TIERS = [('all', lambda r: r.Proj > -1), ('projected 16+', lambda r: r.Proj >= 16), ('projected 20+', lambda r: r.Proj >= 20),
         ('RB 8+', lambda r: (r.Pos == 'RB') & (r.Proj >= 8))]
cal_out, cal_fits, spread_out, spread_fits = [], [], [], []
for variant in ['neutral', 'vegas']:
    rows, sims = season_rows(variant)
    w = rows.season.map(W).values
    cal = lambda c, r=rows: project.calibrated(r.Proj.values, r.Pos.values, c)
    preds = {'no calibration': rows.Proj.values, 'current': cal(cur_cal),
             'refit slopes, current knees': np.zeros(len(rows)), 'refit knees and slopes': np.zeros(len(rows))}
    for s in seasons:
        tr, te = (rows.season != s).values, (rows.season == s).values
        f1 = bt.fit_calibration(rows[tr], cur_cal['top_knee'], cur_cal['rb_knee'], w[tr])
        f2 = h.fit_knees(rows[tr], w[tr], TOP_KNEES, RB_KNEES)
        preds['refit slopes, current knees'][te] = cal(f1, rows[te])
        preds['refit knees and slopes'][te] = cal(f2, rows[te])
        cal_fits += [dict(totals=variant, held_out=s, fit='slopes', **f1), dict(totals=variant, held_out=s, fit='knees and slopes', **f2)]
    cal_fits += [dict(totals=variant, held_out='none (all seasons)', fit='slopes',
                      **bt.fit_calibration(rows, cur_cal['top_knee'], cur_cal['rb_knee'], w)),
                 dict(totals=variant, held_out='none (all seasons)', fit='knees and slopes',
                      **h.fit_knees(rows, w, TOP_KNEES, RB_KNEES)),
                 dict(totals=variant, held_out='none (all seasons, unweighted)', fit='slopes',
                      **bt.fit_calibration(rows, cur_cal['top_knee'], cur_cal['rb_knee']))]
    for label, p in preds.items():
        for tier, pick in TIERS:
            t = pick(rows).values
            cal_out.append(dict(totals=variant, calibration=label, tier=tier, n=int(t.sum()), projected=np.average(p[t], weights=w[t]),
                                actual=np.average(rows.FPTS[t], weights=w[t]), rmse=rmse(p[t] - rows.FPTS[t], w[t])))
    for s in seasons:
        t = (rows.season == s).values
        cal_out += [dict(totals=variant, calibration=label, tier=f'season {s}', n=int(t.sum()), projected=p[t].mean(),
                         actual=rows.FPTS[t].mean(), rmse=rmse(p[t] - rows.FPTS[t])) for label, p in preds.items()]

    # spread: draws carry the current calibration (mean only), then each position's factor is fit out of season
    shifted = sims + (preds['current'] - rows.Proj.values)[:, None].astype(np.float32)
    cur_spread = m.get('spread', {})
    for pos in ['QB', 'RB', 'WR', 'TE']:
        keep = (rows.Pos == pos).values
        x, r, wp = shifted[keep], rows[keep].reset_index(drop=True), w[keep]
        p90 = {'before': np.percentile(x, 90, axis=1), 'current': np.percentile(project.widen(x, cur_spread.get(pos, 1.0)), 90, axis=1),
               'refit': np.zeros(len(r))}
        for s in seasons:
            tr, te = (r.season != s).values, (r.season == s).values
            k = bt.fit_spread(x[tr], r.FPTS.values[tr], weights=wp[tr])
            p90['refit'][te] = np.percentile(project.widen(x[te], k), 90, axis=1)
            spread_fits.append(dict(totals=variant, Pos=pos, held_out=s, k=k))
        k_all = bt.fit_spread(x, r.FPTS.values, weights=wp)
        ks = [f['k'] for f in spread_fits if f['totals'] == variant and f['Pos'] == pos]
        beat = lambda q, t: np.average(r.FPTS.values[t] > q[t], weights=wp[t]) * 100
        for tier, t in [('all', np.ones(len(r), bool)), ('16+', (r.Proj >= 16).values)]:
            if t.sum() >= 50:
                spread_out.append(dict(totals=variant, Pos=pos, tier=tier, n=int(t.sum()), current_k=cur_spread.get(pos, 1.0),
                                       refit_k=k_all, k_range='%.2f to %.2f' % (min(ks), max(ks)),
                                       k_unweighted=bt.fit_spread(x, r.FPTS.values) if tier == 'all' else np.nan,
                                       beat_before=beat(p90['before'], t), beat_current=beat(p90['current'], t), beat_refit=beat(p90['refit'], t)))
        for s in seasons:
            t = (r.season == s).values
            spread_out.append(dict(totals=variant, Pos=pos, tier=f'season {s}', n=int(t.sum()), current_k=cur_spread.get(pos, 1.0),
                                   beat_before=np.mean(r.FPTS.values[t] > p90['before'][t]) * 100,
                                   beat_current=np.mean(r.FPTS.values[t] > p90['current'][t]) * 100,
                                   beat_refit=np.mean(r.FPTS.values[t] > p90['refit'][t]) * 100))
cal_out, cal_fits, spread_out, spread_fits = map(pd.DataFrame, (cal_out, cal_fits, spread_out, spread_fits))
print(f'\nCALIBRATION (current: {cur_cal})\n' + cal_out[~cal_out.tier.str.startswith('season')].round(2).to_string(index=False))
print(cal_out[cal_out.tier.str.startswith('season')].round(2).to_string(index=False))
print(cal_fits.round(3).to_string(index=False))
print('\nSPREAD (share beating the simulated 90th percentile, %; target 10)\n' + spread_out.round(2).to_string(index=False))
save(cal_out, 'calibration.csv'); save(cal_fits, 'calibration_fits.csv'); save(spread_out, 'spread.csv'); save(spread_fits, 'spread_fits.csv')
