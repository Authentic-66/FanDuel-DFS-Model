import os, re, csv
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
R = r'D:\FanDuel-DFS\dfs-model-starter\FanDuel-DFS Model\dfs-model'
f = pd.read_csv(os.path.join(HERE, 'out', '2026-w10_field.csv'))
mine = f[f.mine].copy()
mine['ids'] = mine.Lineup.str.findall(r'\((\d+-\d+)\)').apply(frozenset)
rows = list(csv.reader(open(os.path.join(R, 'weeks', '2026-w10', 'edit_entries_149.csv'))))
ed = [r for r in rows[1:] if r and r[0].isdigit()]
edm = {int(r[0]): frozenset(r[4:13]) for r in ed}
print('edit file rows', len(ed))
ent149 = [frozenset(r) for r in list(csv.reader(open(os.path.join(R, 'weeks/2026-w10/entered_upload_149.csv'))))[1:]]
first = [frozenset(r) for r in list(csv.reader(open(os.path.join(R, 'weeks/2026-w10/entered_as_uploaded/entered_upload_149.csv'))))[1:]]
print('entered_upload_149', len(ent149), 'first upload', len(first), 'shared', len(set(ent149) & set(first)))
mine['in_edit'] = [edm.get(e) == s for e, s in zip(mine.EntryId, mine.ids)]
mine['in149'] = mine.ids.isin(set(ent149))
free = 3767370153
print('export entries', len(mine), '| match edit file by entry id', int(mine.in_edit.sum()),
      '| in entered_upload_149', int(mine.in149.sum()))
odd = mine[~mine.in_edit]
print(odd[['EntryId', 'Points', 'Won']].to_string())
print('149 file lineups missing from export:', sum(x not in set(mine.ids) for x in ent149))
fr = mine[mine.EntryId == free]
m149 = mine[mine.EntryId != free]
print('free entry', fr[['Rank', 'Points', 'Won']].to_string(index=False), fr.Lineup.iloc[0])
print('149: won', round(m149.Won.sum(), 2), 'cashed', int((m149.Won > 0).sum()), 'avg', round(m149.Points.mean(), 1),
      'total won', round(mine.Won.sum(), 2))
