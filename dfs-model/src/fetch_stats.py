"""Download nflverse weekly player stats (the week's season and the prior season) into data/cache."""
import os
import urllib.request

from dfs import config

week, cfg, _ = config.cli(__doc__)
os.makedirs(week.cache, exist_ok=True)
for yr in (week.season, week.season - 1):
    url = f'https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{yr}.csv'
    urllib.request.urlretrieve(url, week.stats(yr))
    print('saved', week.stats(yr))
