"""Grade a week: calibration vs actual FanDuel points, my entries vs field, stack performance, ownership leverage,
and Doug's reads: red, yellow and green graded separately, both applied ([prefs]) and shadow ([shadow]), per player
and as lineups (the optimizer is re-run once as entered and once per colour and source; --no-read-lineups skips that).
Inputs: weeks/<week>/proj.csv, sims.npy, data/<week>/results_players.csv, results_my_entries.csv.
Writes weeks/<week>/reads_players.csv and reads_lineups.csv."""
import pandas as pd

from dfs import analyze, config, ownership, project

week, cfg, a = config.cli(__doc__, [(('--no-read-lineups',), dict(action='store_true', help='skip the optimizer re-runs'))])
proj, sims = project.load(week)
analyze.report(week, proj)

pd.set_option('display.width', 250)
players = analyze.reads_players(cfg, proj, analyze.load_actuals(week.results_players), analyze.entries(week.results_entries, proj))
if players.empty:
    print("\nDoug's reads: none listed under [prefs] or [shadow]")
else:
    players.to_csv(week.output('reads_players.csv'), index=False)
    print("\nDoug's reads by colour (applied = used in the run, shadow = recorded only):")
    print(analyze.reads_summary(players).round(1).to_string(index=False))
    if not a.no_read_lineups:
        lineups = analyze.reads_lineups(week, cfg, ownership.attach(week, cfg, proj, quiet=True), sims)
        lineups.to_csv(week.output('reads_lineups.csv'), index=False)
        print('\nAs lineups (read_effect = points per lineup the reads were worth; "as entered" should match my entries):')
        print(lineups.round(1).to_string(index=False))
