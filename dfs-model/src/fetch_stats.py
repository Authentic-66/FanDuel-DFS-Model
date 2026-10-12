"""Download nflverse data into data/cache. Default: weekly player stats for the week's season and the prior season.
--seasons 2020-2025 (or 2021,2023) fetches those seasons instead; --history also fetches, per season, the weekly
team stats (stats_team_week_<season>.csv, for DST scoring) and the schedule with Vegas lines
(schedule_<season>.csv: scores, spread_line, total_line), which the history refits in src/fit_history.py use."""
import io
import os
import urllib.request

import pandas as pd

from dfs import config

RELEASE = 'https://github.com/nflverse/nflverse-data/releases/download'
GAMES = 'https://github.com/nflverse/nfldata/raw/master/data/games.csv'


def seasons(text):
    out = []
    for part in text.split(','):
        lo, _, hi = part.partition('-')
        out += range(int(lo), int(hi or lo) + 1)
    return out


week, cfg, a = config.cli(__doc__, [
    (['--seasons'], dict(default='', help='e.g. 2020-2025 or 2021,2023 (default: the week\'s season and the one before)')),
    (['--history'], dict(action='store_true', help='also fetch team stats and schedules with Vegas lines')),
])
os.makedirs(week.cache, exist_ok=True)
years = seasons(a.seasons) if a.seasons else [week.season, week.season - 1]
for yr in years:
    urllib.request.urlretrieve(f'{RELEASE}/stats_player/stats_player_week_{yr}.csv', week.stats(yr))
    print('saved', week.stats(yr))
if a.history:
    for yr in years:
        path = os.path.join(week.cache, f'stats_team_week_{yr}.csv')
        urllib.request.urlretrieve(f'{RELEASE}/stats_team/stats_team_week_{yr}.csv', path)
        print('saved', path)
    games = pd.read_csv(io.BytesIO(urllib.request.urlopen(GAMES).read()), low_memory=False)
    for yr in years:
        path = os.path.join(week.cache, f'schedule_{yr}.csv')
        games[games.season == yr].to_csv(path, index=False)
        print('saved', path, len(games[games.season == yr]), 'games')
