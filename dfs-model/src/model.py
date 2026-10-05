"""Projections + correlated sims -> weeks/<week>/proj.csv, sims.npy (see CLAUDE.md, config/defaults.toml [model])."""
from dfs import config, project

week, cfg, _ = config.cli(__doc__)
proj, sims = project.build(week, cfg)
project.save(week, proj, sims)
print(proj.head(25).to_string(index=False))
