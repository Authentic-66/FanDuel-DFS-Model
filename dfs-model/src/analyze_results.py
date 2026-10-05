"""Grade a week: calibration vs actual FanDuel points, my entries vs field, stack performance, ownership leverage.
Inputs: weeks/<week>/proj.csv, data/<week>/results_players.csv, results_my_entries.csv."""
from dfs import analyze, config, project

week, cfg, _ = config.cli(__doc__)
analyze.report(week, project.load(week)[0])
