"""Post-slate grading: projection calibration, my entries vs field, stack performance, ownership vs exposure."""
import re

import numpy as np
import pandas as pd

TIERS = [(0, 8), (8, 14), (14, 20), (20, 99)]
ID_RE = r'\((\d+-\d+)\)'


def load_actuals(path):
    """results_players.csv -> Id, FPTS, own_pct."""
    r = pd.read_csv(path)
    return pd.DataFrame({'Id': r.Player.str.extract(ID_RE)[0], 'FPTS': r.FPTS, 'own_pct': r['%Drafted'] * 100})


def joined(proj, actuals):
    return actuals.merge(proj, on='Id').dropna(subset=['Proj'])


def calibration_table(sk, tiers=TIERS):
    rows = []
    for lo, hi in tiers:
        s = sk[(sk.Proj >= lo) & (sk.Proj < hi)]
        rows.append(dict(tier=f'{lo}-{hi}', n=len(s), proj=s.Proj.mean(), actual=s.FPTS.mean(), gap=s.Proj.mean() - s.FPTS.mean()))
    return pd.DataFrame(rows)


def entries(path, proj):
    """My entries with lineup Ids and stack team (team of the QB)."""
    me = pd.read_csv(path)
    pid = proj.set_index('Id')
    me['ids'] = me.Lineup.map(lambda s: re.findall(ID_RE, s))
    me['stack'] = me.ids.map(lambda l: next((pid.Team[i] for i in l if i in pid.index and pid.Pos[i] == 'QB'), '?'))
    return me


def stack_performance(me):
    return me.groupby('stack').Points.agg(['count', 'mean', 'max']).round(1).sort_values('mean', ascending=False)


def ownership_vs_exposure(sk, me, top=15):
    ex = pd.Series([i for l in me.ids for i in l]).value_counts() / len(me) * 100
    sk = sk.assign(my_pct=sk.Id.map(ex).fillna(0))
    return sk.sort_values('FPTS', ascending=False).head(top)[['Name', 'Team', 'Proj', 'FPTS', 'own_pct', 'my_pct']].round(1)


def report(week, proj):
    c = joined(proj, load_actuals(week.results_players))
    sk, d = c[c.Pos != 'D'], c[c.Pos == 'D']
    print('Projection vs actual (skill players), corr = %.3f' % np.corrcoef(sk.Proj, sk.FPTS)[0, 1])
    for t in calibration_table(sk).itertuples():
        print(f'  proj {t.tier:<5}: n={t.n:3d}  mean proj {t.proj:5.1f}  actual {t.actual:5.1f}')
    print('DST corr = %.2f' % np.corrcoef(d.Proj, d.FPTS)[0, 1])
    me = entries(week.results_entries, proj)
    print('\nMy entries: mean %.1f  best %.1f (rank %d)' % (me.Points.mean(), me.Points.max(), me.Rank.min()))
    print(stack_performance(me).to_string())
    print('\nTop scorers with field ownership vs my exposure:')
    print(ownership_vs_exposure(sk, me).to_string(index=False))


# --- Doug's reads: red / yellow / green, applied ([prefs]) and shadow ([shadow]) --------------------------------------

COLOURS = {'red': ('red', 'red_teams'), 'yellow': ('yellow',), 'green': ('green', 'green_floor')}


def read_groups(cfg):
    """Doug's reads as rows of (colour, source, keys): source 'applied' = [prefs] (used in the run), 'shadow' =
    [shadow] (recorded only). keys = that colour's config entries; colours with nothing listed are left out."""
    out = []
    for source, section in [('applied', cfg['prefs']), ('shadow', cfg.get('shadow', {}))]:
        for colour, keys in COLOURS.items():
            got = {k: section[k] for k in keys if section.get(k)}
            if got.get(keys[0]) or got.get('red_teams'):
                out.append((colour, source, got))
    return out


def read_variants(cfg):
    """One counterfactual [prefs] per read group, each differing from the run as entered in that group only:
    applied reads are taken out, shadow reads are put in. Returns rows of (colour, source, label, prefs)."""
    out = []
    for colour, source, got in read_groups(cfg):
        prefs = dict(cfg['prefs'])
        for k in COLOURS[colour]:
            empty = [] if k in ('red', 'red_teams') else {}
            mine, theirs = prefs.get(k, empty), got.get(k, empty)
            if source == 'applied':
                prefs[k] = empty
            elif isinstance(empty, dict):
                prefs[k] = {**mine, **theirs}
            else:
                prefs[k] = list(mine) + [x for x in theirs if x not in mine]
        out.append((colour, source, f'{colour} ({source}) ' + ('removed' if source == 'applied' else 'added'), prefs))
    return out


def reads_players(cfg, proj, actuals, me):
    """Every player Doug marked, by colour and source: projection, actual, field ownership, lineups we entered.
    Players on a red team are listed if projected >= [optimizer] min_proj (or a DST)."""
    held = pd.Series([i for l in me.ids for i in l]).value_counts()
    p = proj.merge(actuals, on='Id', how='left')
    rows = []
    for colour, source, got in read_groups(cfg):
        names = set(got.get(COLOURS[colour][0], []))
        on_team = p.Team.isin(got.get('red_teams', [])) & ((p.Pos == 'D') | (p.Proj >= cfg['optimizer']['min_proj']))
        for r in p[p.Name.isin(names) | on_team].itertuples():
            rows.append(dict(colour=colour, source=source, Name=r.Name, Pos=r.Pos, Team=r.Team, Proj=r.Proj, FPTS=r.FPTS,
                             diff=r.FPTS - r.Proj, own_pct=r.own_pct, my_lineups=int(held.get(r.Id, 0))))
        for n in sorted(names - set(p.Name)):
            rows.append(dict(colour=colour, source=source, Name=n, Pos='?', my_lineups=0))   # not on the slate
    return pd.DataFrame(rows, columns=['colour', 'source', 'Name', 'Pos', 'Team', 'Proj', 'FPTS', 'diff', 'own_pct', 'my_lineups'])


def reads_summary(players):
    """Per colour and source: players, mean projection and actual, how many scored below projection, lineup slots."""
    g = players.dropna(subset=['FPTS']).groupby(['colour', 'source'], sort=False)
    return g.agg(players=('Name', 'size'), proj=('Proj', 'mean'), actual=('FPTS', 'mean'),
                 below_proj=('diff', lambda d: int((d < 0).sum())), own_pct=('own_pct', 'mean'),
                 my_lineup_slots=('my_lineups', 'sum')).reset_index()


def reads_lineups(week, cfg, proj, sims):
    """Each colour as lineups: re-run the optimizer as entered, then once per read group with only that group
    changed (read_variants), and score every run on actual points. read_effect = points per lineup the reads were
    worth: entered minus without them (applied), or with them minus entered (shadow). Nothing in weeks/ is rewritten."""
    import os
    from . import backtest, optimize
    act = load_actuals(week.results_players).set_index('Id').FPTS
    n_field = cfg['contest'].get('field_size', 0)
    top_path = os.path.join(week.data, 'results_top2000.csv')
    ranked = bool(n_field) and os.path.exists(top_path)
    if ranked:
        top, qs = pd.read_csv(top_path), pd.read_csv(os.path.join(week.data, 'results_field_quantiles.csv'))
    rows = []
    for colour, source, label, prefs in [('', '', 'as entered', cfg['prefs'])] + read_variants(cfg):
        c = dict(cfg, prefs=prefs)
        df = optimize.eligible_pool(proj, prefs, c['optimizer'])
        lineups, _ = optimize.build_lineups(df, sims, c)
        pts = np.array([act.reindex(df.Id[lp]).fillna(0).sum() for lp in lineups])
        r = dict(run=label, colour=colour, source=source, lineups=len(lineups), avg=pts.mean(), best=pts.max())
        if ranked:
            rk = np.array([backtest.est_rank(x, top, qs, n_field) for x in pts])
            r.update(best_rank=int(rk.min()), top_1pct=int((rk <= 0.01 * n_field).sum()), top_10pct=int((rk <= 0.10 * n_field).sum()))
        r['read_effect'] = np.nan if not colour else (rows[0]['avg'] - r['avg'] if source == 'applied' else r['avg'] - rows[0]['avg'])
        rows.append(r)
    return pd.DataFrame(rows)


# --- Doug's pool lineups (dfs/pool.py), graded whether or not they were entered ----------------------------------------

def pool_report(week, cfg, folder='pool'):
    """Pool lineups (weeks/<week>/pool/upload.csv) vs the model's lineups (weeks/<week>/upload.csv) vs what was
    entered (results_my_entries.csv), all scored on actual points: lineups, avg, top-10% / top-1% counts, best and
    best rank (when [contest] field_size and the field files exist), and how many of each set were entered.
    folder: weeks/<week>/<folder>/ (e.g. 'pool/test' for optimize.py --pool --subdir test).
    [grading] extra_sets in week.toml: more folders under weeks/<week>/ graded alongside (shadow control sets).
    Returns None when the week has no pool lineups."""
    import os
    from . import optimize, pool
    path = os.path.join(week.out, folder, 'upload.csv')
    if not os.path.exists(path):
        return None
    act = load_actuals(week.results_players)
    ent = [re.findall(ID_RE, s) for s in pd.read_csv(week.results_entries).Lineup]
    sets = {'pool': optimize.read_upload(path)[1]}
    if os.path.exists(os.path.join(week.out, 'upload.csv')):
        sets['model'] = optimize.read_upload(os.path.join(week.out, 'upload.csv'))[1]
    for name in cfg.get('grading', {}).get('extra_sets', []):   # e.g. week 7's shadow control set model_cap45
        extra = os.path.join(week.out, name, 'upload.csv')
        if os.path.exists(extra):
            sets[name] = optimize.read_upload(extra)[1]
        else:
            print(f'grading: [grading] extra_sets lists {name} but weeks/{week.name}/{name}/upload.csv is missing')
    sets['entered'] = ent
    n_field = cfg['contest'].get('field_size', 0)
    top_path, q_path = os.path.join(week.data, 'results_top2000.csv'), os.path.join(week.data, 'results_field_quantiles.csv')
    if n_field and os.path.exists(top_path) and os.path.exists(q_path):
        return pool.grade(sets, act, ent, pd.read_csv(top_path), pd.read_csv(q_path), n_field)
    return pool.grade(sets, act, ent)
