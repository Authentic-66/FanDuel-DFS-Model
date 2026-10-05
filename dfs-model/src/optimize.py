"""Build stacked GPP lineups -> weeks/<week>/upload.csv, readable.csv, projections.csv, exposure.csv."""
from dfs import config, optimize as opt, project

week, cfg, _ = config.cli(__doc__)
proj, sims = project.load(week)
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
