"""Build stacked GPP lineups -> weeks/<week>/upload.csv, readable.csv, projections.csv, exposure.csv
(+ stacks.csv: our stack shares vs the field's projected QB ownership, when Own_proj is available).
--subdir writes them to weeks/<week>/<subdir>/ instead, leaving the main files alone (e.g. to compare settings).
--pool builds Doug's pool lineups from [pool] in week.toml instead (docs/pool_mode.md) and writes them to
weeks/<week>/pool/ (or pool/<subdir>/), plus pool.csv: every listed player, his rank, status and lineups."""
import os

import pandas as pd

from dfs import config, optimize as opt, ownership, pool, project

week, cfg, args = config.cli(__doc__, [(('--subdir',), dict(default='', help='write outputs to weeks/<week>/<subdir>/')),
                                       (('--pool',), dict(action='store_true', help="Doug's pool lineups -> weeks/<week>/pool/"))])
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
    lineups, use = opt.build_lineups(df, sims, cfg)
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
