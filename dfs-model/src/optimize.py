"""Build stacked GPP lineups -> weeks/<week>/upload.csv, readable.csv, projections.csv, exposure.csv
(+ stacks.csv: our stack shares vs the field's projected QB ownership, when Own_proj is available)."""
from dfs import config, optimize as opt, ownership, project

week, cfg, _ = config.cli(__doc__)
proj, sims = project.load(week)
proj = ownership.attach(week, cfg, proj, quiet=True)   # refresh: proj.csv may predate the latest results
o = cfg['optimizer']
opt.starters(proj, cfg['prefs'], o).drop(columns='row').to_csv(week.output('projections.csv'), index=False)
df = opt.eligible_pool(proj, cfg['prefs'], o)
lineups, use = opt.build_lineups(df, sims, cfg)
upload, readable, exposure = opt.outputs(df, sims, lineups, use, cfg)
opt.write_upload(week.output('upload.csv'), upload, cfg['roster']['slots'])
readable.to_csv(week.output('readable.csv'), index=False)
exposure.to_csv(week.output('exposure.csv'), index=False)
print(exposure[exposure.Review != ''][['Player', 'Lineups', 'Review']].to_string(index=False))
print(readable.Stack.value_counts().to_string())
print(exposure.head(8)[['Player', 'Lineups']].to_string(index=False))
if 'Own_proj' in proj:
    stacks = ownership.stack_table(df, cfg['stacks']['weights'], cfg['ownership']['chalk_qb_own'])
    stacks.to_csv(week.output('stacks.csv'), index=False)
    print('\nStacks vs field (CHALK = QB projected >= %.0f%% owned; Leverage < 1 = we are chalkier than the field):'
          % cfg['ownership']['chalk_qb_own'])
    print(stacks.to_string(index=False))
    print('\nMean lineup projected ownership: %.0f%%' % readable.Own_proj_sum.mean())
