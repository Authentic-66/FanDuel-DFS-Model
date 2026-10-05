"""Sequential MILP lineup builder (PuLP/CBC): one lineup per sim draw, stacked, under Doug's exposure rules.

Rules come from config: [roster], [optimizer] (caps, objective, overlap), [prefs] (red/yellow/green review lists),
[stacks] (QB team weights and per-team stack rules, e.g. BUF = QB + 1 receiver + James Cook III).
"""
import csv
import random

import numpy as np
import pandas as pd


def starters(proj, prefs, opt):
    """Projections (with `row` = sims row) cut to each team's starters if prefs.starters_only: the week's starting QB,
    top-N RB/WR/TE by projection per [optimizer.starters], all DSTs, plus green players."""
    green = set(prefs['green'])
    pr = proj.assign(row=range(len(proj)))
    if prefs['starters_only']:
        act = pr[(pr.Inj != 'O') & pr.Proj.notna()].copy()
        act['rk'] = act.groupby(['Team', 'Pos']).Proj.rank(ascending=False, method='first')
        depth = act.Pos.map(opt['starters']).fillna(0)
        ok = (((act.Pos == 'QB') & act.StartingQB) | (act.Pos == 'D')
              | (act.Pos.isin(list(opt['starters'])) & (act.rk <= depth)) | act.Name.isin(green))
        pr = pr[pr.Id.isin(act.Id[ok])]
    return pr


def eligible_pool(proj, prefs, opt):
    """Players the optimizer may use: starters (see above), not red, projected >= min_proj (DST and green exempt),
    QB must be the week's starter."""
    green, red = set(prefs['green']), set(prefs['red'])
    pr = starters(proj, prefs, opt)
    keep = (~pr.Name.isin(red) & ~pr.Team.isin(prefs['red_teams'])
            & ((pr.Pos == 'D') | (pr.Proj >= opt['min_proj']) | pr.Name.isin(green))
            & ((pr.Pos != 'QB') | pr.StartingQB))
    return pr[keep].reset_index(drop=True)


def exposure_limits(df, prefs, opt):
    """Per-player (cap, need) in lineups. Yellow = cap at yellow_factor * listed; Q = questionable_cap_pct of N;
    green = need max(green_multiplier * listed, green_floor), never above the cap; player_cap overrides."""
    n, cap_all = opt['n_lineups'], opt['exposure_cap']
    yellow, green, pcap = prefs['yellow'], prefs['green'], prefs['player_cap']
    cap, need = {}, {}
    for i, name in df.Name.items():
        if name in yellow:
            cap[i] = round(yellow[name] * opt['yellow_factor'])
        elif df.Inj[i] == 'Q':
            cap[i] = opt['questionable_cap_pct'] * n
        else:
            cap[i] = cap_all
        if name in green:
            need[i] = min(cap_all, max(opt['green_multiplier'] * green[name], opt['green_floor']))
        if name in pcap:
            cap[i] = pcap[name]
            if i in need:
                need[i] = min(need[i], pcap[name] - 5)
    return cap, need


def assign_forced(df, need, n, rnd):
    """Spread each green player's required lineups over random lineup slots; green QBs get disjoint slots."""
    force = {k: set() for k in range(n)}
    qslots = list(range(n))
    rnd.shuffle(qslots)
    for i, k in sorted(need.items(), key=lambda t: df.Pos[t[0]] != 'QB'):
        slots = [qslots.pop() for _ in range(k)] if df.Pos[i] == 'QB' else rnd.sample(range(n), k)
        for s in slots:
            force[s].add(i)
    return force


def stack_rule(team, stacks, opt):
    rule = {'receivers': opt['stack']['receivers'], 'bring_back': opt['stack']['bring_back'], 'require': []}
    rule.update(stacks['rules'].get(team, {}))
    return rule


def solve_lineup(df, obj, team, rule, cap, use, forced, prior_lineups, roster, opt):
    import pulp
    idx = df.index
    pos = lambda p: [i for i in idx if df.Pos[i] == p]
    opp = df[df.Team == team].Opp.iloc[0]
    P = pulp.LpProblem('lineup', pulp.LpMaximize)
    x = {i: pulp.LpVariable(f'x{i}', cat='Binary') for i in idx}
    P += pulp.lpSum(obj[i] * x[i] for i in idx)
    P += pulp.lpSum(df.Salary[i] * x[i] for i in idx) <= roster['salary_cap']
    slots = pd.Series(roster['slots']).replace({'DEF': 'D'})
    counts = slots[slots != 'FLEX'].value_counts()
    for p, c in counts.items():
        P += pulp.lpSum(x[i] for i in pos(p)) == c if p in ('QB', 'D') else pulp.lpSum(x[i] for i in pos(p)) >= c
    P += pulp.lpSum(x[i] for p in roster['flex'] for i in pos(p)) == counts[roster['flex']].sum() + (slots == 'FLEX').sum()
    for t in df.Team.unique():
        P += pulp.lpSum(x[i] for i in idx if df.Team[i] == t and df.Pos[i] != 'D') <= roster['max_per_team']
    # stack: this team's QB + receivers (+ required players) + bring-back from the opponent
    P += pulp.lpSum(x[i] for i in pos('QB') if df.Team[i] == team) == 1
    P += pulp.lpSum(x[i] for i in idx if df.Team[i] == team and df.Pos[i] in ('WR', 'TE')) >= rule['receivers']
    for name in rule['require']:
        P += pulp.lpSum(x[i] for i in idx if df.Name[i] == name) == 1
    P += pulp.lpSum(x[i] for i in idx if df.Team[i] == opp and df.Pos[i] != 'D') >= rule['bring_back']
    for d in pos('D'):   # no DST facing our own offensive players
        for i in idx:
            if df.Pos[i] != 'D' and df.Team[i] == df.Opp[d]:
                P += x[d] + x[i] <= 1
    for i in idx:
        if use[i] >= cap[i]:
            P += x[i] == 0
    for i in forced:
        P += x[i] == 1
    for lp in prior_lineups:
        P += pulp.lpSum(x[i] for i in lp) <= opt['max_overlap']
    if P.solve(pulp.PULP_CBC_CMD(msg=0)) != 1:
        return None
    return [i for i in idx if x[i].value() > 0.5]


def build_lineups(df, sims, cfg):
    """Returns (lineups as lists of df index, exposure counts)."""
    opt, prefs, stacks = cfg['optimizer'], cfg['prefs'], cfg['stacks']
    n = opt['n_lineups']
    rnd = random.Random(opt['seed'])
    cap, need = exposure_limits(df, prefs, opt)
    force = assign_forced(df, need, n, rnd)
    pool = [t for t, w in stacks['weights'].items() for _ in range(w)]
    if not pool:
        raise ValueError('no stack weights: set [stacks.weights] in week.toml')
    use = {i: 0 for i in df.index}
    lineups, draw, tries = [], 0, 0
    w = opt['mean_weight']
    while len(lineups) < n:
        draw += 1
        tries += 1
        slot = len(lineups)
        F = sorted([i for i in force[slot] if use[i] < cap[i]], key=lambda i: (df.Pos[i] != 'QB', -df.Salary[i]))
        if tries > opt['relax_force_after']:   # infeasible: drop forced players, cheapest non-QB first
            F = F[:max(0, len(F) - (tries - opt['relax_force_after']))]
        if tries > opt['drop_force_after']:
            force[slot], F = set(), []
        fq = [i for i in F if df.Pos[i] == 'QB']
        team = df.Team[fq[0]] if fq else rnd.choice(pool)
        obj = w * df.Proj.values + (1 - w) * sims[df.row.values, draw % sims.shape[1]]
        lp = solve_lineup(df, obj, team, stack_rule(team, stacks, opt), cap, use, F, lineups, cfg['roster'], opt)
        if lp is None:
            continue
        lineups.append(lp)
        tries = 0
        for i in lp:
            use[i] += 1
    return lineups, use


def slot_order(df, lp, roster):
    """Lineup indices in upload slot order; FLEX = first extra RB, then WR, then TE."""
    by = {p: [i for i in lp if df.Pos[i] == p] for p in ['QB', 'RB', 'WR', 'TE', 'D']}
    need = pd.Series(roster['slots']).replace({'DEF': 'D'})
    need = need[need != 'FLEX'].value_counts()
    flex = [i for p in roster['flex'] for i in by[p][need[p]:]]
    out, taken = [], {p: 0 for p in by}
    for s in roster['slots']:
        if s == 'FLEX':
            out.append(flex.pop(0))
            continue
        p = 'D' if s == 'DEF' else s
        out.append(by[p][taken[p]])
        taken[p] += 1
    return out


def write_upload(path, rows, header):
    """FanDuel upload CSV. Written with csv (not pandas) so the duplicate RB/WR header stays exact."""
    with open(path, 'w', newline='') as f:
        wr = csv.writer(f, lineterminator='\n')
        wr.writerow(header)
        wr.writerows(rows)


def read_upload(path):
    with open(path, newline='') as f:
        r = csv.reader(f)
        return next(r), list(r)


def outputs(df, sims, lineups, use, cfg):
    """(upload rows, readable DataFrame, exposure DataFrame)."""
    roster, prefs, n = cfg['roster'], cfg['prefs'], cfg['optimizer']['n_lineups']
    labels = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE', 'FLEX', 'DEF']
    upload, readable = [], []
    for k, lp in enumerate(lineups):
        order = slot_order(df, lp, roster)
        upload.append([df.Id[i] for i in order])
        sim = sims[df.row.values[lp]].sum(0)
        d = {'Lineup': k + 1}
        for s, i in zip(labels, order):
            d[s] = f'{df.Name[i]} ({df.Team[i]}, ${df.Salary[i]:,}, {df.Proj[i]})'
        d.update(Stack=df.Team[order[0]], Salary=int(df.Salary[lp].sum()), Proj=round(df.Proj[lp].sum(), 1),
                 Ceiling_p90=round(np.percentile(sim, 90), 1), P_200plus=round((sim >= 200).mean(), 4))
        readable.append(d)
    c = pd.Series(use)
    c = c[c > 0]
    ex = pd.DataFrame({'Player': df.Name[c.index], 'Pos': df.Pos[c.index], 'Team': df.Team[c.index],
                       'Salary': df.Salary[c.index], 'Proj': df.Proj[c.index], 'Status': df.Inj[c.index].fillna(''),
                       'Lineups': c.values, 'Exposure_%': (c.values / n * 100).round(1)}).sort_values('Lineups', ascending=False)
    ex['Review'] = ex.Player.map(lambda p: 'Green (more)' if p in prefs['green'] else ('Yellow (less)' if p in prefs['yellow'] else ''))
    return upload, pd.DataFrame(readable), ex
