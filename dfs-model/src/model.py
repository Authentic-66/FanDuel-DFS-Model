"""Projections + correlated sims -> weeks/<week>/proj.csv, sims.npy (see CLAUDE.md, config/defaults.toml [model]).
Adds Own_proj (projected field ownership, [ownership]) when earlier weeks have FanDuel results."""
from dfs import config, ownership, project

week, cfg, _ = config.cli(__doc__)
proj, sims = project.build(week, cfg)
proj = ownership.attach(week, cfg, proj)
project.save(week, proj, sims)
print(proj.head(25).to_string(index=False))
