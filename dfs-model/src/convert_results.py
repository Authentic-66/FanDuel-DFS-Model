"""Convert a FanDuel "All Entries" contest export into the small result files the grading code reads.
Writes data/<week>/results[_<tag>]_players.csv, _my_entries.csv, _top2000.csv and _field_quantiles.csv.
The export itself (~200 MB) stays untracked in data/<week>/raw/."""
import os

import pandas as pd

from dfs import config

QUANTILES = [0.5, 0.75, 0.9, 0.95, 0.99, 0.999]
ENTRY_COLS = ['Rank', 'EntryId', 'EntryName', 'Points', 'Lineup']
PLAYER_COLS = ['Player', 'Roster Position', '%Drafted', 'FPTS', 'Salary']

week, cfg, a = config.cli(__doc__, [
    (('export',), dict(help='path to the FanDuel All Entries csv')),
    (('--user',), dict(required=True, help='FanDuel username, e.g. gst1999')),
    (('--tag',), dict(default='', help='file-name tag for a second contest, e.g. 025 -> results_025_players.csv')),
])
raw = pd.read_csv(a.export, encoding='utf-8-sig', low_memory=False)
prefix = os.path.join(week.data, 'results_' + (a.tag + '_' if a.tag else ''))

players = raw[PLAYER_COLS].dropna(subset=['Player']).copy()
players['%Drafted'] = (players['%Drafted'].str.rstrip('%').astype(float) / 100).round(4)
players['Salary'] = players.Salary.astype(int)
players.to_csv(prefix + 'players.csv', index=False)

ent = raw[ENTRY_COLS].dropna(subset=['EntryId']).copy()
ent[['Rank', 'EntryId']] = ent[['Rank', 'EntryId']].astype('int64')
mine = ent[ent.EntryName.str.split(' ').str[0] == a.user]
mine.to_csv(prefix + 'my_entries.csv', index=False)
ent.head(2000).to_csv(prefix + 'top2000.csv', index=False)
q = ent.Points.quantile(QUANTILES).round(2)
pd.DataFrame({'quantile': QUANTILES, 'points': q.values}).to_csv(prefix + 'field_quantiles.csv', index=False)

print(f'{len(ent):,} entries, winner {ent.Points.max():.2f}, mean {ent.Points.mean():.2f}; '
      f'{len(players)} players; {len(mine)} entries for {a.user}')
print(pd.DataFrame({'quantile': QUANTILES, 'points': q.values}).to_string(index=False))
