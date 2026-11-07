"""Entered set made from two builds (Doug, Nov 3, week 9): 100 lineups from the median-70 shadow build + 49 from the
current model build (cap 25; Doug, Nov 6: was 75 + 74), no duplicates, = the 149 files (free entry as usual). Both full builds of 150 stay in
their folders and are graded on their own.

    python src/combine_entry.py --week 2026-w09                      # median70/ x 100 + main folder x 49
    python src/combine_entry.py --week 2026-w09 --a median70:100 --b :49

Picking: lineups are taken evenly spaced through each build (1, 3, 5, ... for 75 of 150), so each half keeps its
build's stack-team mix (the builds run team by team). From the second build, lineups identical to one already taken
are skipped first. Writes weeks/<week>/entered_upload_149.csv, entered_readable_149.csv (projections are the model's,
also for median-70 lineups), entered_exposure.csv and entered_source.csv (which build and lineup each came from).
Checks every lineup (slots, salary cap, player list, Out / IR / reds, duplicates) and stops on any problem.
Prints combined exposure (top 15) and flags any player over 70% (Doug, Nov 6: over 50% is acceptable at 100 / 49;
max-entrants run their top player at ~66%)."""
import os

import numpy as np
import pandas as pd

from dfs import config, optimize as opt, ownership, project

POS_OK = {'QB': {'QB'}, 'RB': {'RB'}, 'WR': {'WR'}, 'TE': {'TE'}, 'FLEX': {'RB', 'WR', 'TE'}, 'DEF': {'D', 'DEF', 'DST'}}


def spaced(k, n):
    """k evenly spaced positions out of n (0, 2, 4, ... for 75 of 150)."""
    if k > n:
        raise SystemExit(f'asked for {k} lineups from a build of {n}')
    return sorted({int(x) for x in np.floor(np.arange(k) * n / k)})


def pick(week, spec):
    folder, k = spec.split(':')
    path = os.path.join(week.out, folder, 'upload.csv')
    if not os.path.exists(path):
        raise SystemExit(f'missing {path}: build it first')
    header, rows = opt.read_upload(path)
    return folder or 'model', int(k), header, rows


def check(rows, header, fd, cfg):
    """Problems with the combined upload (empty list = fine)."""
    bad = []
    info = fd.set_index('Id')
    reds = set(cfg['prefs'].get('red', []))
    st = cfg.get('status', {})
    held_out = set(st.get('out', [])) | set(st.get('questionable', []))
    cap = cfg['roster'].get('salary_cap', 60000)
    seen = set()
    for k, r in enumerate(rows, 1):
        if len(r) != len(header) or len(set(r)) != len(r):
            bad.append(f'lineup {k}: {len(set(r))} distinct players in {len(header)} slots')
            continue
        missing = [i for i in r if i not in info.index]
        if missing:
            bad.append(f'lineup {k}: not on the player list: {missing}')
            continue
        for slot, i in zip(header, r):
            if info.Position[i] not in POS_OK.get(slot, {slot}):
                bad.append(f'lineup {k}: {info.Nickname[i]} ({info.Position[i]}) in the {slot} slot')
        sal = int(info.Salary[list(r)].sum())
        if sal > cap:
            bad.append(f'lineup {k}: salary ${sal:,} over ${cap:,}')
        tags = info['Injury Indicator'].reindex(list(r)).fillna('') if 'Injury Indicator' in info else None
        if tags is not None and tags.isin(['O', 'IR', 'NA']).any():
            bad.append(f'lineup {k}: Out / IR player {list(info.Nickname[tags[tags.isin(["O", "IR", "NA"])].index])}')
        held = [info.Nickname[i] for i in r if info.Nickname[i] in held_out]
        if held:
            bad.append(f'lineup {k}: [status] out / questionable player {held}')
        red = [info.Nickname[i] for i in r if info.Nickname[i] in reds]
        if red:
            bad.append(f'lineup {k}: red player {red}')
        if frozenset(r) in seen:
            bad.append(f'lineup {k}: duplicate lineup')
        seen.add(frozenset(r))
    return bad


def main():
    week, cfg, args = config.cli(__doc__, [
        (('--a',), dict(default='median70:100', help='first build folder:count (default median70:100)')),
        (('--b',), dict(default=':49', help='second build folder:count (default :49 = main folder)')),
        (('--flag',), dict(type=float, default=70.0, help='flag players above this exposure %% (default 70)'))])
    na, ka, header, ra = pick(week, args.a)
    nb, kb, hb, rb = pick(week, args.b)
    if header != hb:
        raise SystemExit('the two uploads have different headers')
    take_a = [(na, j) for j in spaced(ka, len(ra))]
    have = {frozenset(ra[j]) for _, j in take_a}
    free_b = [j for j in range(len(rb)) if frozenset(rb[j]) not in have]
    dups = len(rb) - len(free_b)
    take_b = [(nb, free_b[j]) for j in spaced(kb, len(free_b))]
    src = {na: ra, nb: rb}
    rows = [list(src[n][j]) for n, j in take_a + take_b]

    fd = pd.read_csv(week.fd_players)
    problems = check(rows, header, fd, cfg)
    if problems:
        print('\n'.join(problems))
        raise SystemExit(f'{len(problems)} problem(s): nothing written')

    proj, sims = project.load(week)
    proj = ownership.attach(week, cfg, proj, quiet=True)
    df = opt.eligible_pool(proj, cfg['prefs'], cfg['optimizer'])
    by_id = {v: i for i, v in df.Id.items()}
    out_of_pool = sorted({i for r in rows for i in r if i not in by_id})
    if out_of_pool:
        raise SystemExit(f'players not in the model pool: {out_of_pool}')
    lineups = [[by_id[i] for i in r] for r in rows]
    use = pd.Series([i for lp in lineups for i in lp]).value_counts().to_dict()
    c = dict(cfg, optimizer=dict(cfg['optimizer'], n_lineups=len(rows)))
    upload, readable, exposure = opt.outputs(df, sims, lineups, use, c)

    opt.write_upload(week.output('entered_upload_149.csv'), upload, header)
    readable.insert(1, 'Build', [n for n, _ in take_a + take_b])
    readable.insert(2, 'Build_lineup', [j + 1 for _, j in take_a + take_b])
    readable.to_csv(week.output('entered_readable_149.csv'), index=False)
    exposure.to_csv(week.output('entered_exposure.csv'), index=False)
    readable[['Lineup', 'Build', 'Build_lineup']].to_csv(week.output('entered_source.csv'), index=False)

    print(f'{len(rows)} lineups: {len(take_a)} from {na} + {len(take_b)} from {nb} '
          f'({dups} of {nb} matched a {na} lineup and were skipped); all checks passed')
    for n in (na, nb):
        r = readable[readable.Build == n]
        print(f'  {n}: projection {r.Proj.mean():.1f} avg (model projections), salary ${r.Salary.min():,}-'
              f'${r.Salary.max():,}, stacks {r.Stack.value_counts().to_dict()}')
    used = exposure[exposure.Lineups > 0]
    print(f'\nCombined exposure, top 15 of {len(used)} players used:')
    print(used.head(15)[['Player', 'Pos', 'Team', 'Salary', 'Proj', 'Lineups', 'Exposure_%']].to_string(index=False))
    over = used[used['Exposure_%'] > args.flag]
    print(f'\nOver {args.flag:.0f}%: ' + (', '.join(f'{p} {e}%' for p, e in zip(over.Player, over['Exposure_%']))
                                       if len(over) else 'none'))
    print('->', week.output('entered_upload_149.csv'))


if __name__ == '__main__':
    main()
