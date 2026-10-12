"""Sequential MILP lineup builder (PuLP/CBC): one lineup per sim draw, stacked, under Doug's exposure rules.

Rules come from config: [roster], [optimizer] (caps, objective, overlap), [prefs] (red/yellow/green review lists),
[stacks] (QB team weights and per-team stack rules, e.g. BUF = QB + 1 receiver + James Cook III),
[prefs] green_mode ("floor" = forced minimum lineups; "boost" = objective and stack-weight multiplier, nothing forced),
[optimizer.leverage] (off by default: ownership penalty, lineup ownership cap, chalk-stack down-weighting; needs Own_proj).
"""
import csv
import random

import numpy as np
import pandas as pd


def starters(proj, prefs, opt):
    """Projections (with `row` = sims row) cut to each team's starters if prefs.starters_only: the week's starting QB,
    top-N RB/WR/TE by projection per [optimizer.starters], all DSTs, plus green players. Depth is ranked among players
    eligible this run: OUT, and Q when opt.exclude_questionable (green exempt), don't hold depth slots."""
    green = set(prefs['green'])
    pr = proj.assign(row=range(len(proj)))
    if prefs['starters_only']:
        held = (pr.Inj == 'O') | (opt['exclude_questionable'] & (pr.Inj == 'Q') & ~pr.Name.isin(green))
        act = pr[~held & pr.Proj.notna()].copy()
        act['rk'] = act.groupby(['Team', 'Pos']).Proj.rank(ascending=False, method='first')
        depth = act.Pos.map(opt['starters']).fillna(0)
        floor = act.Pos.map(opt.get('starters_min_proj', {})).fillna(0)   # applies below the top player only
        ok = (((act.Pos == 'QB') & act.StartingQB) | (act.Pos == 'D')
              | (act.Pos.isin(list(opt['starters'])) & (act.rk <= depth) & ((act.rk == 1) | (act.Proj >= floor)))
              | act.Name.isin(green))
        pr = pr[pr.Id.isin(act.Id[ok])]
    return pr


def eligible_pool(proj, prefs, opt):
    """Players the optimizer may use: starters (see above), not red, projected >= min_proj (DST and green exempt),
    QB must be the week's starter, no questionable players if opt.exclude_questionable (green players exempt).
    Excluded Q players don't hold starter depth (see starters), so their backups move up."""
    green, red = set(prefs['green']), set(prefs['red'])
    pr = starters(proj, prefs, opt)
    keep = (~pr.Name.isin(red) & ~pr.Team.isin(prefs['red_teams'])
            & ~(opt['exclude_questionable'] & (pr.Inj == 'Q') & ~pr.Name.isin(green))
            & ((pr.Pos == 'D') | (pr.Proj >= opt['min_proj']) | pr.Name.isin(green))
            & ((pr.Pos != 'QB') | pr.StartingQB))
    return pr[keep].reset_index(drop=True)


def green_boost(prefs):
    """Multiplier for green players under [prefs] green_mode = "boost" (1 + green_boost); 1.0 in "floor" mode."""
    mode = prefs.get('green_mode', 'floor')
    if mode not in ('floor', 'boost'):
        raise ValueError(f'[prefs] green_mode must be "floor" or "boost", not {mode!r}')
    return 1 + prefs.get('green_boost', 0.15) if mode == 'boost' else 1.0


def exposure_limits(df, prefs, opt):
    """Per-player (cap, need) in lineups. Yellow = cap at yellow_factor * listed; Q = questionable_cap_pct of N;
    green = need max(green_multiplier * listed, green_floor), never above the cap (prefs.green_floor = per-player floor);
    player_cap overrides. With green_mode = "boost" nothing is forced (need is empty): see build_lineups."""
    forced = green_boost(prefs) == 1.0
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
        if name in green and forced:
            floor = prefs.get('green_floor', {}).get(name, opt['green_floor'])
            need[i] = min(cap_all, max(opt['green_multiplier'] * green[name], floor))
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
    lev = opt['leverage']
    if lev['enabled'] and lev['max_lineup_own']:
        P += pulp.lpSum(df.Own_proj[i] * x[i] for i in idx) <= lev['max_lineup_own']
    if P.solve(pulp.PULP_CBC_CMD(msg=0)) != 1:
        return None
    return [i for i in idx if x[i].value() > 0.5]


def leverage_weights(df, weights, lev):
    """Stack draw weights scaled by (mean field QB own / team's field QB own) ** stack_exponent."""
    qb = df[(df.Pos == 'QB') & df.StartingQB].groupby('Team').Own_proj.max()
    own = pd.Series({t: qb.get(t, np.nan) for t in weights}).clip(lower=0.5)
    own = own.fillna(own.mean())
    return {t: w * (own.mean() / own[t]) ** lev['stack_exponent'] for t, w in weights.items()}


def reserved_caps(df, cap, force, slot, team, stacks, opt, queue=None):
    """Caps for a lineup stacked on `team`, holding back room on players that a stack still to come requires by rule:
    one lineup per later forced (green) QB slot, and per stack still queued under stack_allocation = "proportional".
    Without it other stacks use the required player up to his cap and that team's stacks fall short (week 4: Allen 21
    of 25 behind Cook). [optimizer] reserve_required."""
    out = dict(cap)
    later = [df.Team[q] for s in range(slot + 1, len(force)) for q in force[s] if df.Pos[q] == 'QB']
    for t in later + list(queue or []):
        if t != team:
            for name in stack_rule(t, stacks, opt)['require']:
                for i in df.index[df.Name == name]:
                    out[i] -= 1
    return out


def allocate_stacks(weights, n):
    """Split n lineups over stack teams in proportion to their weights, largest-remainder rounding (ties go to the
    team listed first). Returns {team: lineups}; the counts sum to n."""
    total = sum(weights.values())
    if total <= 0:
        raise ValueError('stack weights sum to zero')
    quota = {t: n * w / total for t, w in weights.items()}
    counts = {t: int(q) for t, q in quota.items()}
    left = n - sum(counts.values())
    for t in sorted(quota, key=lambda t: counts[t] - quota[t])[:left]:
        counts[t] += 1
    return counts


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
    lev = opt['leverage']
    penalty = 0.0
    lw = None
    if lev['enabled']:
        if 'Own_proj' not in df:
            raise ValueError('[optimizer.leverage] enabled but proj has no Own_proj (no earlier result weeks?)')
        penalty = lev['own_weight'] * df.Own_proj.values
        if lev['stack_exponent']:
            lw = leverage_weights(df, stacks['weights'], lev)
    # green_mode = "boost": green players' objective value x (1 + green_boost); green QBs' stack weights x the same,
    # or x [prefs] green_qb_weight if set
    boost = green_boost(prefs)
    mult = np.where(df.Name.isin(set(prefs['green'])), boost, 1.0)
    green_qb_teams = set(df.Team[(df.Pos == 'QB') & (mult > 1)])
    if green_qb_teams:
        qb_mult = prefs.get('green_qb_weight') or boost
        lw = {t: w * (qb_mult if t in green_qb_teams else 1) for t, w in (lw or stacks['weights']).items()}
    if lw is not None:
        teams, tw = list(lw), list(lw.values())
        pool = None
    # [optimizer] stack_allocation = "proportional": fixed stack counts from the weights instead of one draw per lineup
    alloc = opt.get('stack_allocation', 'random')
    if alloc not in ('random', 'proportional'):
        raise ValueError(f'[optimizer] stack_allocation must be "random" or "proportional", not {alloc!r}')
    queue = None
    if alloc == 'proportional':
        live = dict(lw or stacks['weights'])
        counts = allocate_stacks(live, n)
        # Tightest teams first (receiver lineups needed / receiver lineups available under the caps): built late, other
        # stacks have used their receivers up to the cap and the team can no longer be stacked.
        rec = df[df.Pos.isin(['WR', 'TE'])]
        room = {t: sum(cap[i] for i in rec.index[rec.Team == t]) for t in counts}
        tight = {t: counts[t] * stack_rule(t, stacks, opt)['receivers'] / max(room[t], 1) for t in counts}
        queue = [t for t in sorted(counts, key=lambda t: -tight[t]) for _ in range(counts[t])]
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
        if fq:
            team = df.Team[fq[0]]
        elif queue is not None:
            team = queue[0]
        else:
            team = rnd.choice(pool) if pool else rnd.choices(teams, tw)[0]
        obj = (w * df.Proj.values + (1 - w) * sims[df.row.values, draw % sims.shape[1]]) * mult - penalty
        caps = reserved_caps(df, cap, force, slot, team, stacks, opt, queue) if opt.get('reserve_required') else cap
        lp = solve_lineup(df, obj, team, stack_rule(team, stacks, opt), caps, use, F, lineups, cfg['roster'], opt)
        if lp is None:
            if tries > 20 * opt['drop_force_after']:   # e.g. a [optimizer.leverage] max_lineup_own nothing can meet
                raise RuntimeError(f'no feasible lineup for slot {slot + 1} after {tries} tries')
            if queue is not None and not F:   # nothing forced, so this team can't be stacked any more (caps/overlap):
                short = queue.count(team)     # hand its remaining lineups to the other teams, again by weight
                live.pop(team)
                queue = [t for t in queue if t != team] + [t for t, k in allocate_stacks(live, short).items()
                                                           for _ in range(k)]
                print(f'stack allocation: {team} cannot be stacked again; {short} lineup(s) reallocated')
            continue
        if queue is not None and team in queue:
            queue.remove(team)
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
        if 'Own_proj' in df:
            d['Own_proj_sum'] = round(df.Own_proj[lp].sum(), 1)
        readable.append(d)
    c = pd.Series(use)
    c = c[c > 0]
    ex = pd.DataFrame({'Player': df.Name[c.index], 'Pos': df.Pos[c.index], 'Team': df.Team[c.index],
                       'Salary': df.Salary[c.index], 'Proj': df.Proj[c.index], 'Status': df.Inj[c.index].fillna(''),
                       'Lineups': c.values, 'Exposure_%': (c.values / n * 100).round(1)}).sort_values('Lineups', ascending=False)
    if 'Own_proj' in df:   # field's projected ownership; Exp_minus_Own > 0 = we are overweight vs the field
        fades = df[~df.index.isin(c.index) & (df.Own_proj >= cfg['ownership']['show_unused_own'])]
        ex = pd.concat([ex, pd.DataFrame({'Player': fades.Name, 'Pos': fades.Pos, 'Team': fades.Team,
                                          'Salary': fades.Salary, 'Proj': fades.Proj, 'Status': fades.Inj.fillna(''),
                                          'Lineups': 0, 'Exposure_%': 0.0})])
        ex['Own_proj_%'] = df.Own_proj[ex.index].values
        ex['Exp_minus_Own'] = (ex['Exposure_%'] - ex['Own_proj_%']).round(1)
    if 'RoutingBump' in df:   # points gained from injury / trade redistribution: spot depth players lifted into lineups
        ex.insert(ex.columns.get_loc('Proj') + 1, 'Routing_bump', df.RoutingBump[ex.index].values)
    ex['Review'] = ex.Player.map(lambda p: 'Green (more)' if p in prefs['green'] else ('Yellow (less)' if p in prefs['yellow'] else ''))
    return upload, pd.DataFrame(readable), ex
