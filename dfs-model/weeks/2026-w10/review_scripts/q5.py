import os, json
import numpy as np, pandas as pd
import gradelib as g
wk = '2026-w10'
W = os.path.join(g.R, 'weeks', wk)
groups = json.load(open(os.path.join(g.HERE, 'groups.json')))
proj = pd.read_csv(os.path.join(W, 'proj.csv'))
_, act, _ = g.week_data(wk)
proj['Actual'] = proj.Id.map(act)
ent = g.read_upload(os.path.join(W, 'entered_upload_149.csv'))
base = g.grade(wk, ent)
print('As entered:', base)
rows = []
for k in ['matchup', 'role', 'nointerest', 'nonote', 'all']:
    p = proj[proj.Name.isin(groups[k])]
    live = p[p.Proj > 0]
    b = g.rebuilt(wk, 'red_' + k)
    x = g.drop_lowest(*b)
    gr = g.grade(wk, x)
    names = {i: n for i, n in zip(proj.Id, proj.Name)}
    used = pd.Series([names[i] for lp in x for i in lp if names[i] in groups[k]]).value_counts()
    rows.append(dict(group=k, players=len(p), active_proj=len(live), proj=round(live.Proj.mean(), 1),
                     actual=round(live.Actual.mean(), 1), avg=gr['avg'], d_avg=round(gr['avg'] - base['avg'], 1),
                     won=gr['won'], d_won=round(gr['won'] - base['won'], 2), top10=gr['top10'], top1=gr['top1'],
                     used=', '.join(f'{n} {c} ({proj.loc[proj.Name == n, "Proj"].iloc[0]} / {act.get(proj.loc[proj.Name == n, "Id"].iloc[0], 0)})'
                                    for n, c in used.head(8).items())))
d = pd.DataFrame(rows)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 200)
print(d.to_string(index=False))
d.to_csv(os.path.join(g.HERE, 'out', 'q5_reds.csv'), index=False)
for k in ['matchup', 'role', 'nointerest']:
    print(k, proj[proj.Name.isin(groups[k])][['Name', 'Team', 'Proj', 'Actual']].to_string(index=False))
# promotion kill rule
pr = proj[proj.GuardRescue.notna() & (proj.GuardRescue.astype(str) != '') & (proj.Proj >= 4)]
print('\nPromoted (GuardRescue) Proj 4+ week 10:')
cnt = pd.Series([i for lp in ent for i in lp]).value_counts()
pr = pr.assign(lineups=pr.Id.map(cnt).fillna(0).astype(int))
print(pr[['Name', 'Pos', 'Team', 'GuardRescue', 'Proj', 'Actual', 'lineups']].to_string(index=False))
print('week 10: n %d proj %.2f actual %.2f diff %.2f' % (len(pr), pr.Proj.mean(), pr.Actual.mean(), (pr.Actual - pr.Proj).mean()))
w9 = [5.9 - 6.7, 5.0 - 0.0, 4.1 - 1.6]   # week9_review s4: proj - actual
allp = list(pr.Proj - pr.Actual) + w9
print('weeks 9-10 combined: n %d, under-score by %.2f a player (kill rule fires at 1.5+)' % (len(allp), np.mean(allp)))
allg = proj[proj.GuardRescue.notna() & (proj.GuardRescue.astype(str) != '')]
print('all promoted wk10: n %d proj %.2f actual %.2f' % (len(allg), allg.Proj.mean(), allg.Actual.fillna(0).mean()))
