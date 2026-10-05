"""Apply Doug's projection reads ([overrides] in config/<week>/week.toml) to proj.csv / sims.npy in place."""
from dfs import config, overrides, project

week, cfg, _ = config.cli(__doc__)
proj, sims = overrides.apply(*project.load(week), cfg['overrides'])
project.save(week, proj, sims)
print(proj[proj.Name.isin(cfg['overrides'])][['Name', 'Proj', 'Ceiling_p90']].to_string(index=False))
