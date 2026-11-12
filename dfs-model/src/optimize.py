"""Build stacked GPP lineups -> weeks/<week>/upload.csv, readable.csv, projections.csv, exposure.csv
(+ stacks.csv: our stack shares vs the field's projected QB ownership, when Own_proj is available).
--subdir writes them to weeks/<week>/<subdir>/ instead, leaving the main files alone (e.g. to compare settings).
--cap N overrides [optimizer] exposure_cap for this run only (e.g. week 7's shadow control set:
--subdir model_cap45 --cap 45).
--flex-shadow: the weeks 9-10 shadow build (Doug, Nov 2): [optimizer] rb_stack_pieces = true and flex_te_top_salary = 5
for this run only, written to weeks/<week>/flex_shadow/ unless --subdir is given (docs/week9_tests.md section 6).
--no-draw / --median70: the weeks 9-10 cash-style shadow sets (Doug, Nov 3; docs/late_news_and_cash_builds.md in the
NBA repo): --no-draw = objective is the projection only (mean_weight 1), same caps -> nodraw/; --median70 = objective
is each player's median sim score, mean_weight 1, exposure cap 105 (70% of 150), max overlap 7 -> median70/.
Built at the final run, not entered, graded beside the entered set ([grading] extra_sets).
With --median70 (week 10 on, Doug Nov 12; docs/week9_review.md section 7): --variant flex = v1, the flex-shadow rule
(-> median70_v1/); --variant stack = v2, QB + 1 receiver, bring-back optional (-> median70_v2/); --variant repeats =
v3, the plain build's 150 ranked by projected (median) score, top 105 kept and the top 45 entered twice (->
median70_v3/). --injury-cap N: players lifted by injured teammates (RoutingBump 1+ or GuardRescue set: the elite
rule's "not normal role" test) are capped at N lineups (Doug, Nov 12: 30% = 45).
--pool builds Doug's pool lineups from [pool] in week.toml instead (docs/pool_mode.md) and writes them to
weeks/<week>/pool/ (or pool/<subdir>/), plus pool.csv: every listed player, his rank, status and lineups."""
import os

import numpy as np
import pandas as pd

from dfs import config, optimize as opt, ownership, pool, project

week, cfg, args = config.cli(__doc__, [(('--subdir',), dict(default='', help='write outputs to weeks/<week>/<subdir>/')),
                                       (('--pool',), dict(action='store_true', help="Doug's pool lineups -> weeks/<week>/pool/")),
                                       (('--cap',), dict(type=int, default=0, help='exposure cap for this run (default: config)')),
                                       (('--flex-shadow',), dict(action='store_true',
                                                                 help='RB stack pieces + TE flex top-5 by salary -> flex_shadow/')),
                                       (('--no-draw',), dict(action='store_true',
                                                             help='shadow: projection-only objective -> nodraw/')),
                                       (('--median70',), dict(action='store_true',
                                                              help='shadow: median objective, cap 105, overlap 7 -> median70/')),
                                       (('--variant',), dict(default='', choices=['', 'flex', 'stack', 'repeats'],
                                                             help='with --median70: v1 flex / v2 stack / v3 repeats')),
                                       (('--injury-cap',), dict(type=int, default=0,
                                                                help='with --median70: cap (lineups) for RoutingBump 1+ / '
                                                                     'GuardRescue players')),
                                       (('--exclude',), dict(default='',
                                                             help='"Name, Name": left out of this run only, like a red '
                                                                  '(combine_entry exposure rule, Doug Nov 6); needs --subdir'))])
if args.exclude:
    if not args.subdir:
        raise SystemExit('--exclude: give a --subdir so the graded model folder is not overwritten')
    names = [n.strip() for n in args.exclude.split(',') if n.strip()]
    known = set(project.load(week)[0].Name)
    unknown = [n for n in names if n not in known]
    if unknown:
        raise SystemExit(f'--exclude: not in proj.csv: {unknown}')
    cfg['prefs']['red'] = sorted(set(cfg['prefs']['red']) | set(names))
    print('excluded for this run only:', ', '.join(names))
if (args.no_draw or args.median70) and (args.pool or args.flex_shadow or (args.no_draw and args.median70)):
    raise SystemExit('--no-draw / --median70: one at a time, model build only')
if args.no_draw:
    cfg['optimizer'].update(mean_weight=1.0)
    args.subdir = args.subdir or 'nodraw'
    print('no-draw shadow: objective = projection only (mean_weight 1); ->', args.subdir)
if args.median70:
    cfg['optimizer'].update(mean_weight=1.0, exposure_cap=105, max_overlap=7)
    args.subdir = args.subdir or 'median70'
    print('median-70 shadow: objective = median sim score, cap 105, overlap 7; ->', args.subdir)
if (args.variant or args.injury_cap) and not args.median70:
    raise SystemExit('--variant / --injury-cap: only with --median70')
if args.variant:
    v = {'flex': 'v1', 'stack': 'v2', 'repeats': 'v3'}[args.variant]
    if args.subdir == 'median70':
        args.subdir = 'median70_' + v
    if args.variant == 'flex':
        cfg['optimizer'].update(rb_stack_pieces=True, flex_te_top_salary=5)
    elif args.variant == 'stack':
        cfg['optimizer']['stack'] = dict(cfg['optimizer']['stack'], receivers=1, bring_back=0)
    print(f'median-70 {v} ({args.variant}); ->', args.subdir)
if args.flex_shadow:
    if args.pool:
        raise SystemExit('--flex-shadow is for the model build, not --pool')
    cfg['optimizer'].update(rb_stack_pieces=True, flex_te_top_salary=5)
    args.subdir = args.subdir or 'flex_shadow'
    print('flex shadow: every RB a stack piece, TE in the FLEX only if top-5 by salary; ->', args.subdir)
if args.cap:
    print(f"exposure cap {args.cap} for this run (config: {cfg['optimizer']['exposure_cap']})")
    cfg['optimizer']['exposure_cap'] = args.cap
if args.pool:
    if not pool.is_on(cfg):
        raise SystemExit('--pool: no [pool] lists in config/%s/week.toml' % week.name)
    args.subdir = os.path.join('pool', args.subdir) if args.subdir else 'pool'
os.makedirs(os.path.join(week.out, args.subdir), exist_ok=True)
out = lambda name: week.output(os.path.join(args.subdir, name))
proj, sims = project.load(week)
proj = ownership.attach(week, cfg, proj, quiet=True)   # refresh: proj.csv may predate the latest results
o = cfg['optimizer']
opt.starters(proj, cfg['prefs'], o).drop(columns='row').to_csv(out('projections.csv'), index=False)
if args.pool:
    slate = set(pd.read_csv(week.fd_players).Nickname)
    df, lineups, use, tab, info = pool.build(proj, sims, cfg, slate)
    upload, readable, exposure = pool.outputs(df, sims, lineups, use, cfg, tab)
    tab.to_csv(out('pool.csv'), index=False)
    print(f"pool: cap {info['cap']} for pool players; stack teams {info['stack_weights']}")
    print(f"pool: {(readable.Filler != '').sum()} of {len(readable)} lineups use a filler")
    print(tab.to_string(index=False))
else:
    df = opt.eligible_pool(proj, cfg['prefs'], o)
    if args.injury_cap:
        rescue = df.GuardRescue.fillna('').astype(str).str.len() > 0 if 'GuardRescue' in df else False
        lifted = df[(df.RoutingBump >= 1) | rescue]
        for name in lifted.Name:
            cfg['prefs']['player_cap'][name] = min(args.injury_cap, cfg['prefs']['player_cap'].get(name, args.injury_cap))
        print(f'injury cap {args.injury_cap}: ' + ', '.join(f'{r.Name} ({r.Proj})' for r in
                                                           lifted.sort_values('Proj', ascending=False).itertuples()))
    if args.median70:
        df = df.assign(Proj=np.median(sims, axis=1)[df.row.values])   # pool chosen on projections, built on medians
    lineups, use = opt.build_lineups(df, sims, cfg)
    if args.variant == 'repeats':   # v3: top 105 by projected (median) score kept, the top 45 entered twice
        n = cfg['optimizer']['n_lineups']
        keep, rep = round(n * 0.7), n - round(n * 0.7)
        order = sorted(range(len(lineups)), key=lambda k: -df.Proj[lineups[k]].sum())
        top = [lineups[k] for k in order[:keep]]
        lineups = top + top[:rep]
        use = {}
        for lp in lineups:
            for i in lp:
                use[i] = use.get(i, 0) + 1
        print(f'v3 repeats: {keep} distinct, top {rep} twice')
    upload, readable, exposure = opt.outputs(df, sims, lineups, use, cfg)
opt.write_upload(out('upload.csv'), upload, cfg['roster']['slots'])
readable.to_csv(out('readable.csv'), index=False)
exposure.to_csv(out('exposure.csv'), index=False)
print(exposure[exposure.Review != ''][['Player', 'Lineups', 'Review']].to_string(index=False))
print(readable.Stack.value_counts().to_string())
print(exposure.head(8)[['Player', 'Lineups']].to_string(index=False))
if 'Own_proj' in proj:
    weights = info['stack_weights'] if args.pool else cfg['stacks']['weights']
    stacks = ownership.stack_table(df, weights, cfg['ownership']['chalk_qb_own'],
                                   extra_receivers=cfg['stacks'].get('extra_receivers', []))
    stacks.to_csv(out('stacks.csv'), index=False)
    print('\nStacks vs field (CHALK = QB projected >= %.0f%% owned; Leverage < 1 = we are chalkier than the field):'
          % cfg['ownership']['chalk_qb_own'])
    print(stacks.to_string(index=False))
    print('\nMean lineup projected ownership: %.0f%%' % readable.Own_proj_sum.mean())
