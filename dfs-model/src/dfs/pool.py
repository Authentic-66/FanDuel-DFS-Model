"""Doug's pool mode (docs/pool_mode.md): 150 lineups built only from Doug's player pool ([pool] in week.toml), with at
most [pool] max_filler players per lineup from outside it. Same projections, sims, objective and standing rules as the
model; written to weeks/<week>/pool/ by `optimize.py --pool`, graded by analyze_results.py.

[pool] in week.toml: QB / RB / WR / TE / DST = lists of names (DST: FanDuel name, e.g. "Buffalo Bills", or team
code). ranked = true: each list is in Doug's rank order, and the objective gets a small boost by rank (rank_boost).
"""
import numpy as np
import pandas as pd

from . import optimize

POSITIONS = {'QB': 'QB', 'RB': 'RB', 'WR': 'WR', 'TE': 'TE', 'DST': 'D'}
SLOTS = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 1, 'D': 1}   # fixed slots per lineup; FLEX = one more RB / WR / TE


def listed(pool):
    """{pos: [names]} from the [pool] section (pos in QB/RB/WR/TE/D). Empty dict = pool mode not set up."""
    return {p: list(pool.get(key, [])) for key, p in POSITIONS.items() if pool.get(key)}


def is_on(cfg):
    return bool(listed(cfg.get('pool', {})))


def members(proj, pool, slate_names=None):
    """Pool rows as a DataFrame (Name, Pos, Rank, row index into proj or -1, Note). Errors on a name that is not on
    the FanDuel slate at all (typo); a name on the slate but missing from proj (ruled out) is kept with a note.
    DST may be given as the FanDuel name or the team code."""
    rows, bad = [], []
    for pos, names in listed(pool).items():
        seen = set()
        for rank, name in enumerate(names, 1):
            hit = proj.index[(proj.Pos == pos) & ((proj.Name == name) | ((pos == 'D') & (proj.Team == name)))]
            if name in seen:
                raise ValueError(f'[pool] {name!r} is listed twice under {pos}')
            seen.add(name)
            if len(hit):
                rows.append(dict(Name=proj.Name[hit[0]], Pos=pos, Rank=rank, Listed=len(names), proj_row=int(hit[0]), Note=''))
            elif slate_names is not None and name in slate_names:
                rows.append(dict(Name=name, Pos=pos, Rank=rank, Listed=len(names), proj_row=-1, Note='not in projections (out)'))
            else:
                bad.append(f'{name} ({pos})')
    if bad:
        raise ValueError(f'[pool] names not on the slate at that position: {", ".join(bad)}')
    return pd.DataFrame(rows, columns=['Name', 'Pos', 'Rank', 'Listed', 'proj_row', 'Note'])


def rank_mult(rank, listed_n, ranked, boost):
    """Objective multiplier for a pool player: 1 + boost for rank 1 falling linearly to 1.0 for the last listed.
    1.0 for everyone when the pool is not ranked."""
    if not ranked or listed_n <= 1:
        return 1.0 + (boost if ranked else 0.0)
    return 1.0 + boost * (listed_n - rank) / (listed_n - 1)


def passes_role_guard(proj, rg):
    """Filler check: the [model.role_guard] test, applied whether or not the guard is on for the model run (needs the
    RoleVol / NoData columns that model.py writes). True = has 2026 data and, at a role-floor position, enough volume."""
    if 'RoleVol' not in proj or 'NoData' not in proj:
        raise ValueError('pool mode: proj.csv has no RoleVol / NoData columns (written by model.py since week 7): re-run model.py')
    low = proj.Pos.isin(rg.get('positions', ['WR', 'TE'])) & (proj.RoleVol.fillna(0) < rg.get('min_volume', 3.0))
    guarded = proj['RoleGuard'].fillna('').astype(str).ne('') if 'RoleGuard' in proj else False
    return (proj.Pos == 'D') | (~proj.NoData.astype(bool) & ~low & ~guarded)


def frame(proj, cfg, slate_names=None):
    """(df for the optimizer with a `row` column and an InPool flag, pool table with per-player status).
    Pool players skip starters_only and min_proj (like green) but not OUT, the questionable rule, red, or the
    starting-QB rule. Fillers come from the model's normal eligible pool, minus QBs and role-guard failures."""
    prefs, o, pl = cfg['prefs'], cfg['optimizer'], cfg['pool']
    tab = members(proj, pl, slate_names)
    pr = proj.assign(row=range(len(proj)))
    red, red_teams = set(prefs['red']), set(prefs['red_teams'])
    notes = []
    for t in tab.itertuples():
        if t.proj_row < 0:
            notes.append(t.Note)
            continue
        r = pr.loc[t.proj_row]
        notes.append('red' if r.Name in red or r.Team in red_teams else
                     'questionable' if o['exclude_questionable'] and r.Inj == 'Q' else
                     'not the starting QB' if r.Pos == 'QB' and not r.StartingQB else
                     'projects 0' if not r.Proj > 0 else '')
    tab['Note'] = notes
    tab['Usable'] = tab.Note == ''
    use_rows = tab.proj_row[tab.Usable].tolist()
    nogreen = dict(prefs, green={}, green_floor={})
    fill = optimize.eligible_pool(proj, nogreen, o)
    fill = fill[(fill.Pos != 'QB') & ~fill.row.isin(tab.proj_row) & fill.row.map(passes_role_guard(proj, cfg['model'].get('role_guard', {})))]
    df = pd.concat([pr.loc[use_rows].assign(InPool=True), fill.assign(InPool=False)], ignore_index=True)
    return df, tab


def capacity(tab, cap, n, max_filler):
    """Lower bound check before building: can the usable pool fill n lineups at this exposure cap with at most
    max_filler fillers each? (Ignores salary, team limits, stacks and overlap, so passing is necessary, not
    sufficient.) Returns (ok, fillers needed, detail by position). Fillers can't be the QB (the stack QB is a pool QB)."""
    k = tab[tab.Usable].Pos.value_counts()
    short = {p: max(0, SLOTS[p] * n - int(k.get(p, 0)) * cap) for p in SLOTS}
    flex = max(0, 7 * n - sum(int(k.get(p, 0)) for p in ('RB', 'WR', 'TE')) * cap)
    needed = short['D'] + max(short['RB'] + short['WR'] + short['TE'], flex)
    ok = short['QB'] == 0 and needed <= max_filler * n
    return ok, needed, dict(short, FLEX=flex)


def stack_weights(df, cfg, max_filler):
    """[stacks.weights] cut to teams with a usable pool QB whose stack can be met with at most max_filler fillers
    (receivers from his team, bring-back from the opponent, players a stack rule requires). A pool QB's team with no
    weight gets the smallest listed weight. Prints what it drops or adds."""
    o, stacks = cfg['optimizer'], cfg['stacks']
    base = stacks['weights']
    lo = min(base.values()) if base else 1
    pool = df[df.InPool]
    out = {}
    for team in pool.Team[pool.Pos == 'QB']:
        rule = optimize.stack_rule(team, stacks, o)
        opp = pool.Opp[(pool.Team == team) & (pool.Pos == 'QB')].iloc[0]
        rec = int(((pool.Team == team) & optimize.receivers(pool, stacks)).sum())
        back = int(((pool.Team == opp) & ~pool.Pos.isin(['D', 'QB'])).sum())   # one QB per lineup: his QB can't be it
        req_out = [n for n in rule['require'] if n not in set(pool.Name)]
        missing = [n for n in rule['require'] if n not in set(df.Name)]
        need = max(0, rule['receivers'] - rec) + max(0, rule['bring_back'] - back) + len(req_out)
        if missing or need > max_filler:
            why = f'requires {", ".join(missing)} (not eligible)' if missing else \
                f'{rec} pool receiver(s), {back} pool bring-back option(s): needs {need} fillers'
            print(f'pool: {team} cannot be stacked ({why}); dropped from the stack draw')
            continue
        if team not in base:
            print(f'pool: {team} has a pool QB but no [stacks.weights] entry; using weight {lo}')
        out[team] = base.get(team, lo)
    if not out:
        raise ValueError('pool mode: no pool QB can be stacked (pool QB + receivers + bring-back)')
    return out


def build(proj, sims, cfg, slate_names=None):
    """Pool lineups. Returns (df, lineups, use, tab, info): same lineups/use as optimize.build_lineups, the pool table
    and a dict with the cap used and the capacity check."""
    pl = cfg['pool']
    o = cfg['optimizer']
    n, max_filler = o['n_lineups'], pl.get('max_filler', 1)
    df, tab = frame(proj, cfg, slate_names)
    for t in tab[~tab.Usable].itertuples():
        print(f'pool: {t.Name} ({t.Pos}) held out: {t.Note}')
    cap = o['exposure_cap']
    ok, needed, short = capacity(tab, cap, n, max_filler)
    raised = False
    if not ok and pl.get('raise_cap_to', 0) > cap:
        print(f'pool: at cap {cap} the pool cannot fill {n} lineups (needs {needed} fillers, {max_filler * n} allowed; '
              f'short by position {short}). Standing rule "raise to {pl["raise_cap_to"]} if infeasible": pool players '
              f'capped at {pl["raise_cap_to"]}, fillers stay at {cap}')
        cap, raised = pl['raise_cap_to'], True
        ok, needed, short = capacity(tab, cap, n, max_filler)
    if not ok:
        raise ValueError(f'pool mode: pool too small for {n} lineups at cap {cap} with {max_filler} filler(s) each '
                         f'(short by position {short}); add players or raise [pool] raise_cap_to')
    ranked, boost = pl.get('ranked', False), pl.get('rank_boost', 0.05)
    by_row = {r.proj_row: rank_mult(r.Rank, r.Listed, ranked, boost) for r in tab[tab.Usable].itertuples()}
    mult = np.array([by_row.get(r, 1.0) if p else 1.0 for r, p in zip(df.row, df.InPool)])
    c = dict(cfg, prefs=dict(cfg['prefs'], green={}, green_floor={}),
             stacks=dict(cfg['stacks'], weights=stack_weights(df, cfg, max_filler)))
    members_idx = set(df.index[df.InPool])
    try:
        lineups, use = optimize.build_lineups(df, sims, c, pool_mode=dict(members=members_idx, max_filler=max_filler,
                                                                          cap=cap, mult=mult))
    except RuntimeError as e:   # the capacity check passed but the stacks ran dry (docs/pool_mode.md section 4)
        raise RuntimeError(f'pool mode: {e}. The pool is too thin for {n} lineups at cap {cap}: add receivers (most '
                           f'often WRs) for the pool QBs, or raise [pool] raise_cap_to / max_filler in week.toml '
                           f'(weeks 4-6 test: see docs/pool_mode.md)') from None
    used = pd.Series(use)
    tab['Proj'] = tab.proj_row.map(lambda r: proj.Proj[r] if r >= 0 else np.nan)
    tab['Mult'] = tab.proj_row.map(lambda r: round(by_row.get(r, np.nan), 3))
    tab['Lineups'] = tab.proj_row.map(lambda r: int(used[df.index[df.row == r]].sum()) if r >= 0 else 0)
    info = dict(cap=cap, raised=raised, fillers_needed=needed, stack_weights=c['stacks']['weights'])
    return df, lineups, use, tab.drop(columns='proj_row'), info


def outputs(df, sims, lineups, use, cfg, tab):
    """optimize.outputs plus pool columns: readable Filler (the lineup's non-pool player, '' if none), exposure Pool
    (pool rank, or 'filler')."""
    upload, readable, ex = optimize.outputs(df, sims, lineups, use, cfg)
    readable.insert(readable.columns.get_loc('Stack'), 'Filler',
                    [', '.join(df.Name[i] for i in lp if not df.InPool[i]) for lp in lineups])
    rank = {(r.Name, r.Pos): r.Rank for r in tab.itertuples()}
    ex.insert(ex.columns.get_loc('Lineups'), 'Pool',
              [str(rank.get((nm, p), 'filler')) for nm, p in zip(ex.Player, ex.Pos)])
    return upload, readable, ex


# --- grading (analyze_results.py) -------------------------------------------------------------------------------------

def grade(lineup_sets, actuals, entered_ids, top=None, qs=None, field_size=0):
    """Score lineup sets on actual points. lineup_sets: {label: list of Id lists}. Returns one row per set: lineups,
    avg, top_10pct, top_1pct, best, best_rank (ranks when field data is given) and entered = how many of the set's
    lineups match an entered lineup (same 9 Ids)."""
    from .backtest import est_rank
    act = actuals.set_index('Id').FPTS
    ent = {frozenset(ids) for ids in entered_ids}
    rows = []
    for label, sets in lineup_sets.items():
        pts = np.array([act.reindex(ids).fillna(0).sum() for ids in sets])
        r = dict(set=label, lineups=len(sets), avg=round(pts.mean(), 1), best=round(pts.max(), 1),
                 entered=sum(frozenset(ids) in ent for ids in sets))
        if top is not None and field_size:
            rk = np.array([est_rank(x, top, qs, field_size) for x in pts])
            r.update(top_10pct=int((rk <= 0.10 * field_size).sum()), top_1pct=int((rk <= 0.01 * field_size).sum()),
                     best_rank=int(rk.min()))
        rows.append(r)
    return pd.DataFrame(rows)
