"""Entered set made from two builds (Doug, Nov 3, week 9): 100 lineups from the median-70 shadow build + 49 from the
current model build (cap 25; Doug, Nov 6: was 75 + 74), no duplicates, = the 149 files (free entry as usual). Both
full builds of 150 stay in their folders and are graded on their own.

    python src/combine_entry.py --week 2026-w09                      # median70/ x 100 + main folder x 49
    python src/combine_entry.py --week 2026-w09 --a median70:100 --b :49

Picking: lineups are taken evenly spaced through each build (1, 3, 5, ... for 75 of 150), so each half keeps its
build's stack-team mix (the builds run team by team). From the second build, lineups identical to one already taken
are skipped first. Writes weeks/<week>/entered_upload_149.csv, entered_readable_149.csv (projections are the model's,
also for median-70 lineups), entered_exposure.csv and entered_source.csv (which build and lineup each came from).
Checks every lineup (slots, salary cap, player list, Out / IR / reds, duplicates) and stops on any problem.

Exposure rule (Doug, Nov 6): ELITE players have no exposure cap. Elite = top 5 at his position (QB, RB, WR, TE, DST)
by FanDuel's 2026 points per game (FPPG; ranked among players with 4+ games played), with no FanDuel injury tag and
his normal role (not lifted 1+ point by teammates out [RoutingBump], no role-drop flag, not promoted by the role
guard, QB = his team's starter). A top-5 player who fails a test is not elite; nobody below moves up. Anyone else over
70% of the entered lineups: the second build (the model, main folder) is rebuilt WITHOUT him into weeks/<week>/
model_excl/ (optimize.py --exclude; the graded main folder is untouched) and the entry recombined, repeated until
every non-elite player is at or under 70%. --no-rebuild only reports. Prints the elite list, any rebuild, combined
exposure (top 15) and every player over 70%."""
import math
import os
import subprocess
import sys

import numpy as np
import pandas as pd

from dfs import config, optimize as opt, ownership, project

POS_OK = {'QB': {'QB'}, 'RB': {'RB'}, 'WR': {'WR'}, 'TE': {'TE'}, 'FLEX': {'RB', 'WR', 'TE'}, 'DEF': {'D', 'DEF', 'DST'}}
ELITE_TOP, ELITE_MIN_GAMES, ELITE_MAX_BUMP = 5, 4, 1.0
REBUILD_DIR = 'model_excl'


def spaced(k, n):
    """k evenly spaced positions out of n (0, 2, 4, ... for 75 of 150)."""
    if k > n:
        raise SystemExit(f'asked for {k} lineups from a build of {n}')
    return sorted({int(x) for x in np.floor(np.arange(k) * n / k)})


def pick(week, spec):
    folder, k = spec.rsplit(':', 1)
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


def elite_table(fd, proj):
    """Top ELITE_TOP per position by FanDuel FPPG (ELITE_MIN_GAMES+ played) with the tests; column Elite = passes all."""
    cols = [c for c in ['Id', 'RoutingBump', 'RoleDrop', 'GuardRescue', 'StartingQB'] if c in proj]
    x = fd.merge(proj[cols], on='Id', how='left')
    out = []
    for pos in ['QB', 'RB', 'WR', 'TE', 'D']:
        s = x[(x.Position == pos) & (x.Played >= ELITE_MIN_GAMES)].sort_values('FPPG', ascending=False).head(ELITE_TOP)
        for _, r in s.iterrows():
            why = []
            tag = r.get('Injury Indicator')
            if isinstance(tag, str) and tag.strip():
                why.append(f'FanDuel tag {tag.strip()}')
            bump = r.get('RoutingBump')
            if pd.notna(bump) and bump >= ELITE_MAX_BUMP:
                why.append(f'lifted +{bump:.1f} by teammates out')
            if isinstance(r.get('RoleDrop'), str) and r.get('RoleDrop').strip():
                why.append('role-drop flag')
            if isinstance(r.get('GuardRescue'), str) and r.get('GuardRescue').strip():
                why.append('promoted by the role guard')
            if pos == 'QB' and r.get('StartingQB') is not True and str(r.get('StartingQB')) != 'True':
                why.append('not the starting QB')
            out.append(dict(Id=r.Id, Player=r.Nickname, Pos=pos, Team=r.Team, Played=int(r.Played),
                            FPPG=round(float(r.FPPG), 2), Elite=not why, Why_not='; '.join(why)))
    return pd.DataFrame(out)


def combine(week, a_spec, b_spec):
    na, ka, header, ra = pick(week, a_spec)
    nb, kb, hb, rb = pick(week, b_spec)
    if header != hb:
        raise SystemExit('the two uploads have different headers')
    take_a = [(na, j) for j in spaced(ka, len(ra))]
    have = {frozenset(ra[j]) for _, j in take_a}
    free_b = [j for j in range(len(rb)) if frozenset(rb[j]) not in have]
    take_b = [(nb, free_b[j]) for j in spaced(kb, len(free_b))]
    src = {na: ra, nb: rb}
    rows = [list(src[n][j]) for n, j in take_a + take_b]
    return dict(header=header, rows=rows, take=take_a + take_b, na=na, nb=nb, n_a=len(take_a), n_b=len(take_b),
                dups=len(rb) - len(free_b))


def main():
    week, cfg, args = config.cli(__doc__, [
        (('--a',), dict(default='median70:100', help='first build folder:count (default median70:100)')),
        (('--b',), dict(default=':49', help='second build folder:count (default :49 = main folder, the model)')),
        (('--flag',), dict(type=float, default=70.0, help='exposure %% limit for non-elite players (default 70)')),
        (('--no-rebuild',), dict(action='store_true', help='report players over the limit, do not rebuild'))])
    fd = pd.read_csv(week.fd_players)
    proj, sims = project.load(week)
    E = elite_table(fd, proj)
    elite_ids = set(E.Id[E.Elite])
    print(f'Elite (no exposure cap): top {ELITE_TOP} per position by FanDuel FPPG, {ELITE_MIN_GAMES}+ games played')
    print(E.drop(columns='Id').to_string(index=False))

    b_folder, kb = args.b.rsplit(':', 1)
    excluded, log = [], []
    for attempt in range(6):
        C = combine(week, args.a, args.b if not excluded else f'{REBUILD_DIR}:{kb}')
        n = len(C['rows'])
        limit = math.floor(args.flag / 100 * n + 1e-9)
        counts = pd.Series([i for r in C['rows'] for i in r]).value_counts()
        over = [i for i, c in counts.items() if c > limit and i not in elite_ids]
        if not over or args.no_rebuild:
            break
        if b_folder:
            print(f'note: the rebuild is the plain model build (optimize.py, no shadow flags) without them; --b was '
                  f'{b_folder}')
        names = list(fd.set_index('Id').Nickname.reindex(over))
        excluded += [x for x in names if x not in excluded]
        log.append(f'over {args.flag:.0f}% ({limit} of {n}): ' + ', '.join(
            f'{fd.set_index("Id").Nickname[i]} {counts[i]}' for i in over) + f' -> model rebuilt without {", ".join(excluded)}')
        print('\n' + log[-1])
        cmd = [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'optimize.py'),
               '--week', week.name, '--subdir', REBUILD_DIR, '--exclude', ', '.join(excluded)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-2000:], r.stderr[-2000:])
            raise SystemExit('the rebuild without ' + ', '.join(excluded) + ' failed: nothing written')
    else:
        raise SystemExit('still over the limit after 6 rebuilds: nothing written')

    rows, header, take = C['rows'], C['header'], C['take']
    problems = check(rows, header, fd, cfg)
    if problems:
        print('\n'.join(problems))
        raise SystemExit(f'{len(problems)} problem(s): nothing written')

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
    readable.insert(1, 'Build', [nm for nm, _ in take])
    readable.insert(2, 'Build_lineup', [j + 1 for _, j in take])
    readable.to_csv(week.output('entered_readable_149.csv'), index=False)
    exposure.to_csv(week.output('entered_exposure.csv'), index=False)
    readable[['Lineup', 'Build', 'Build_lineup']].to_csv(week.output('entered_source.csv'), index=False)

    print(f'\n{len(rows)} lineups: {C["n_a"]} from {C["na"]} + {C["n_b"]} from {C["nb"]} '
          f'({C["dups"]} of {C["nb"]} matched a {C["na"]} lineup and were skipped); all checks passed')
    print('Rebuilds: ' + ('none' if not log else f'{len(log)} (model without {", ".join(excluded)} -> {REBUILD_DIR}/)'))
    for nm in (C['na'], C['nb']):
        r = readable[readable.Build == nm]
        print(f'  {nm}: projection {r.Proj.mean():.1f} avg (model projections), salary ${r.Salary.min():,}-'
              f'${r.Salary.max():,}, stacks {r.Stack.value_counts().to_dict()}')
    used = exposure[exposure.Lineups > 0]
    print(f'\nCombined exposure, top 15 of {len(used)} players used:')
    print(used.head(15)[['Player', 'Pos', 'Team', 'Salary', 'Proj', 'Lineups', 'Exposure_%']].to_string(index=False))
    over = used[used['Exposure_%'] > args.flag]
    elite_names = set(E.Player[E.Elite])
    print(f'\nOver {args.flag:.0f}%: ' + (', '.join(f'{p} {e}% ({"elite" if p in elite_names else "NOT elite"})'
                                                 for p, e in zip(over.Player, over['Exposure_%'])) if len(over) else 'none'))
    print('->', week.output('entered_upload_149.csv'))


if __name__ == '__main__':
    main()
