"""Apply Doug's projection reads ([overrides] in config/<week>/week.toml) to proj.csv / sims.npy in place,
then recompute Own_proj from the overridden projections."""
from dfs import config, ownership, overrides, project

week, cfg, _ = config.cli(__doc__)
proj, sims = overrides.apply(*project.load(week), cfg['overrides'])
proj = ownership.attach(week, cfg, proj, quiet=True)
project.save(week, proj, sims)
cols = ['Name', 'Proj', 'Ceiling_p90'] + (['Own_proj'] if 'Own_proj' in proj else [])
print(proj[proj.Name.isin(cfg['overrides'])][cols].to_string(index=False))
