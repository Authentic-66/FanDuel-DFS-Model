"""Phase 2 #2: projected field ownership from pre-lock information, and stack chalk flags.

Model (config [ownership]): ridge regression of logit(%Drafted) on the configured features, fit on every earlier week
with FanDuel results, then shifted per position (in logit space) so each position's ownership sums to what the field
must roster (QB 100%, DST 100%, RB/WR/TE at their training-week shares; 9 slots = 900% in all).

Training rows come from re-running this week's pipeline as it would have looked before lock: projections from the
current model plus that week's [overrides] (Doug's reads carry news the field also sees; they fit ownership slightly
better than raw model projections). Rows are cached in weeks/<week>/ownership_train.csv; delete it (or pass
refresh=True) after a material projection-model change.
"""
import glob
import os

import numpy as np
import pandas as pd

from . import analyze, overrides, project
from .config import Week, load_config

POSITIONS = ['QB', 'RB', 'WR', 'TE', 'D']
FEATURES = {
    'log_salary': lambda d: np.log(d.Salary / 1000),
    'proj': lambda d: d.Proj,
    'value': lambda d: d.Value_per_1k,
    'fppg': lambda d: d.FD_FPPG,
    'implied': lambda d: d.ImpliedTeamTotal,
    'game_total': lambda d: d.GameTotal,
    'gained_vol': lambda d: np.log1p(d.GainedVol),   # targets + carries/g inherited from OUT teammates
}
TRAIN_COLS = ['Id', 'Name', 'Pos', 'Team', 'Opp', 'Salary', 'Proj', 'Value_per_1k', 'FD_FPPG', 'ImpliedTeamTotal',
              'GameTotal', 'GainedVol', 'StartingQB', 'own']


def design(df, oc):
    """Feature matrix: configured features + position intercepts (QB is the base)."""
    X = pd.DataFrame({f: FEATURES[f](df) for f in oc['features']}, index=df.index)
    for p in POSITIONS[1:]:
        X['is_' + p] = (df.Pos == p).astype(float)
    return X


def logit_target(own, floor):
    o = np.clip(own, floor, 1 - floor)
    return np.log(o / (1 - o))


# --- training data ----------------------------------------------------------------------------------------------

def training_frame(week, cfg=None, refresh=False):
    """Pre-lock features for one archived week joined with actual ownership (fraction; undrafted/unlisted = 0)."""
    path = os.path.join(week.out, 'ownership_train.csv')
    if os.path.exists(path) and not refresh:
        return pd.read_csv(path)
    cfg = cfg or load_config(week)
    proj, sims = project.build(week, cfg)
    proj, _ = overrides.apply(proj, sims, cfg['overrides'])
    act = analyze.load_actuals(week.results_players).set_index('Id').own_pct / 100
    df = proj.assign(own=proj.Id.map(act).fillna(0.0))[TRAIN_COLS]
    df.to_csv(week.output('ownership_train.csv'), index=False)
    return df


def results_weeks(week, include_self=False):
    """Earlier weeks (same root) that have FanDuel results files, oldest first (plus `week` if include_self)."""
    found = []
    for path in glob.glob(os.path.join(week.root, 'data', '*', 'results_players.csv')):
        w = Week(os.path.basename(os.path.dirname(path)), week.root)
        try:
            key = (w.season, w.number)
        except AttributeError:   # folder name not a week (e.g. data/cache)
            continue
        if key < (week.season, week.number) or (include_self and key == (week.season, week.number)):
            found.append((key, w))
    return [w for _, w in sorted(found)]


def training_set(week, oc, refresh=False, include_self=False):
    weeks = results_weeks(week, include_self)
    if oc['max_weeks']:
        weeks = weeks[-oc['max_weeks']:]
    frames = [training_frame(w, refresh=refresh).assign(week=w.name) for w in weeks]
    return (pd.concat(frames, ignore_index=True) if frames else None), [w.name for w in weeks]


# --- fit / predict ----------------------------------------------------------------------------------------------

def fit(train, oc):
    """Ridge on standardized features (intercept unpenalized), rows with Proj >= min_proj.
    Returns a JSON-able model dict including per-position ownership totals."""
    t = train[train.Proj >= oc['min_proj']]
    X = design(t, oc)
    mu, sd = X.mean(), X.std().replace(0, 1).fillna(1)
    Z = np.c_[np.ones(len(X)), ((X - mu) / sd).values]
    R = oc['ridge'] * np.eye(Z.shape[1])
    R[0, 0] = 0
    b = np.linalg.solve(Z.T @ Z + R, Z.T @ logit_target(t.own.values, oc['floor']))
    n_weeks = train.week.nunique() if 'week' in train else 1
    totals = (train.groupby('Pos').own.sum() / n_weeks).reindex(POSITIONS).to_dict()
    totals.update(QB=1.0, D=1.0)   # exactly one QB and one DST per lineup
    return dict(cols=list(X.columns), mu=mu.tolist(), sd=sd.tolist(), intercept=b[0], coef=b[1:].tolist(),
                totals=totals)


def raw_logit(df, model, oc):
    X = design(df, oc)[model['cols']]
    return model['intercept'] + ((X - model['mu']) / model['sd']).values @ np.array(model['coef'])


def normalize(df, z, totals):
    """Shift each position's logits by a constant so its ownership sums to totals[pos] (bisection)."""
    out = np.zeros(len(df))
    for p, target in totals.items():
        m = (df.Pos == p).values
        if not m.any():
            continue
        lo, hi = -30.0, 30.0
        for _ in range(80):
            c = (lo + hi) / 2
            lo, hi = (c, hi) if (1 / (1 + np.exp(-(z[m] + c)))).sum() < target else (lo, c)
        out[m] = 1 / (1 + np.exp(-(z[m] + c)))
    return out


def predict(df, model, oc):
    """Projected ownership as a fraction, normalized over the rows of df (pass the whole active slate)."""
    return normalize(df, raw_logit(df, model, oc), model['totals'])


def cross_validate(train, oc, folds=None, seed=0):
    """Out-of-fold predictions (fraction). Folds are random players; with several weeks, use whole weeks instead
    (leave-one-week-out), which is the honest test of next-week prediction."""
    folds = folds or oc['folds']
    oof = np.zeros(len(train))
    weeks = train.week.unique() if 'week' in train else []
    if len(weeks) > 1:
        groups = train.week.values
        keys = weeks
    else:
        groups = np.random.default_rng(seed).permutation(len(train)) % folds
        keys = range(folds)
    for k in keys:
        te = groups == k
        oof[te] = raw_logit(train[te], fit(train[~te], oc), oc)
    out = np.zeros(len(train))
    by_week = train.week.values if 'week' in train else np.zeros(len(train))
    totals = fit(train, oc)['totals']
    for w in np.unique(by_week):
        m = by_week == w
        out[m] = normalize(train[m], oof[m], totals)
    return out


def fit_report(train, pred_own):
    """Fit by position on a model-independent set (actual >= 1% or Proj >= 5): n, Pearson r on %, r on log %,
    MAE in percentage points, and MAE of the naive position-average guess."""
    ev = (train.own >= 0.01) | (train.Proj >= 5)
    a, b = train.own.values * 100, pred_own * 100
    null = train.groupby('Pos').own.transform('mean').values * 100
    rows = []
    for p in POSITIONS + ['ALL']:
        m = ev.values & ((train.Pos == p).values if p != 'ALL' else True)
        la, lb = np.log(np.clip(a[m], 0.5, None)), np.log(np.clip(b[m], 0.5, None))
        rows.append(dict(pos=p, n=int(m.sum()), r=np.corrcoef(a[m], b[m])[0, 1], r_log=np.corrcoef(la, lb)[0, 1],
                         mae=np.mean(np.abs(a[m] - b[m])), mae_null=np.mean(np.abs(a[m] - null[m]))))
    return pd.DataFrame(rows).round(3)


# --- pipeline hooks ---------------------------------------------------------------------------------------------

def attach(week, cfg, proj, quiet=False):
    """proj with Own_proj (% of field lineups) from a model fit on all earlier result weeks. Returns proj unchanged
    (no column) when ownership is disabled or no earlier week has results."""
    oc = cfg['ownership']
    proj = proj.drop(columns=['Own_proj'], errors='ignore')
    if not oc['enabled']:
        return proj
    train, weeks = training_set(week, oc)
    if train is None:
        if not quiet:
            print(f'ownership: no earlier weeks with results_players.csv before {week.name}; Own_proj not added')
        return proj
    model = fit(train, oc)
    out = proj.copy()
    out['Own_proj'] = (predict(out, model, oc) * 100).round(2)
    if not quiet:
        print(f'ownership: fit on {", ".join(weeks)} ({len(train)} rows)')
    return out


def stack_table(df, weights, chalk_qb_own, receivers=2):
    """Per stack team: our share of stack draws, the field's projected QB ownership (≈ share of field lineups built
    on that QB), its top receivers' ownership, a CHALK flag when the field is likely to overweight it
    (QB own >= chalk_qb_own %), and Leverage = our share / field share (< 1: we are chalkier than the field).
    df needs Own_proj."""
    tot = sum(weights.values()) or 1
    rows = []
    for t, w in weights.items():
        qb = df[(df.Team == t) & (df.Pos == 'QB') & df.StartingQB]
        rec = df[(df.Team == t) & df.Pos.isin(['WR', 'TE'])].nlargest(receivers, 'Own_proj')
        q = qb.Own_proj.max() if len(qb) else np.nan
        rows.append(dict(Team=t, Our_share_pct=round(100 * w / tot, 1), Field_QB_own=q,
                         Top_receivers=', '.join(f'{n} {o:.0f}%' for n, o in zip(rec.Name, rec.Own_proj)),
                         Receiver_own=round(rec.Own_proj.sum(), 1)))
    st = pd.DataFrame(rows)
    st['Chalk'] = np.where(st.Field_QB_own >= chalk_qb_own, 'CHALK', '')
    st['Leverage'] = (st.Our_share_pct / st.Field_QB_own.clip(lower=0.5)).round(2)
    return st.sort_values('Field_QB_own', ascending=False).reset_index(drop=True)
