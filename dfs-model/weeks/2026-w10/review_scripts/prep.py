"""Compact per-week field files from the raw All Entries exports (weeks 5-10).
out/<wk>_field.csv : Rank, EntryId, Points, mine, n_sub3 (non-DST players < 3 pts), dst_sub3, top10, Won
out/<wk>_pts.csv   : Id, Player, Pos, FPTS, Drafted
"""
import os, re, sys, glob
import numpy as np, pandas as pd

R = r'D:\FanDuel-DFS\dfs-model-starter\FanDuel-DFS Model\dfs-model'
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)
RAW = {'2026-w05': 'data/2026-w05/raw/10.11.2026_35k_Pooch_Punt_All_Entries.csv'}
for w in ['2026-w06', '2026-w07', '2026-w08', '2026-w09', '2026-w10']:
    RAW[w] = glob.glob(os.path.join(R, 'data', w, 'raw', '*.csv'))[0]
TOK = re.compile(r'(QB|RB|WR|TE|D) [^,]*?\((\d+-\d+)\)')

for wk in (sys.argv[1:] or RAW):
    p = RAW[wk] if os.path.isabs(RAW[wk]) else os.path.join(R, RAW[wk])
    cols = pd.read_csv(p, nrows=0, encoding='utf-8-sig').columns
    use = [c for c in ['Rank', 'EntryId', 'EntryName', 'Points', 'Lineup', 'Won', 'Player', 'Roster Position',
                       '%Drafted', 'FPTS'] if c in cols]
    raw = pd.read_csv(p, encoding='utf-8-sig', usecols=use, low_memory=False)
    pl = raw[['Player', 'Roster Position', '%Drafted', 'FPTS']].dropna(subset=['Player']).copy()
    pl['Id'] = pl.Player.str.extract(r'\((\d+-\d+)\)$')[0]
    pl['Name'] = pl.Player.str.replace(r' \(\d+-\d+\)$', '', regex=True)
    pts = dict(zip(pl.Id, pl.FPTS.astype(float)))
    pl[['Id', 'Name', 'Roster Position', '%Drafted', 'FPTS']].to_csv(os.path.join(OUT, wk + '_pts.csv'), index=False)
    e = raw.dropna(subset=['EntryId']).copy()
    e["Lineup"] = e.Lineup.fillna("")
    toks = e.Lineup.str.findall(TOK)
    nsub, dsub, nmiss = [], [], 0
    for t in toks:
        k = d = 0
        for pos, i in t:
            v = pts.get(i)
            if v is None:
                nmiss += 1; v = 0.0
            if pos == 'D':
                d = int(v < 3)
            elif v < 3:
                k += 1
        nsub.append(k); dsub.append(d)
    f = pd.DataFrame({'Rank': e.Rank.astype('int64'), 'EntryId': e.EntryId.astype('int64'), 'Points': e.Points.astype(float),
                      'mine': e.EntryName.str.split(' ').str[0].eq('gst1999'), 'n_sub3': nsub, 'dst_sub3': dsub})
    if 'Won' in e:
        f['Won'] = e.Won.astype(str).str.replace(r'[$,]', '', regex=True).replace('nan', '0').astype(float)
    f['Lineup'] = e.Lineup.values
    f.to_csv(os.path.join(OUT, wk + '_field.csv'), index=False)
    print(wk, len(f), 'entries; ids not in player list:', nmiss, '; mine', int(f.mine.sum()))
