import os, json
import numpy as np, pandas as pd
import gradelib as g
wk = '2026-w10'
W = os.path.join(g.R, 'weeks', wk)
sets = {}
sets['Entered 149 (edited)'] = g.read_upload(os.path.join(W, 'entered_upload_149.csv'))
sets['First upload 149'] = g.read_upload(os.path.join(W, 'entered_as_uploaded', 'entered_upload_149.csv'))
sets['Model 150'] = g.read_upload(os.path.join(W, 'upload.csv'))
for lab, sub in [('No-draw', 'nodraw'), ('Median-70 (30% injury cap)', 'median70'), ('Median-70 plain', 'median70_plain'),
                 ('Median-70 v1 flex', 'median70_v1'), ('Median-70 v2 stack', 'median70_v2'),
                 ('Median-70 v3 repeats', 'median70_v3'), ('Cap-45', 'model_cap45'), ('Pool', 'pool'),
                 ('Flex shadow', 'flex_shadow')]:
    sets[lab] = g.read_upload(os.path.join(W, sub, 'upload.csv'))
for lab, key in [('FDR projections 150', 'fdr'), ('50/50 blend 150', 'blend')]:
    b = g.rebuilt(wk, key)
    if b:
        sets[lab] = b[0]
# Sunday calls, each 149 (lowest projected dropped, as entered)
ent = set(map(frozenset, sets['Entered 149 (edited)']))
first = set(map(frozenset, sets['First upload 149']))
for lab, key in [('Neither call (rebuild)', 'sun_neither'), ('Etienne cap 8 only', 'sun_etienne_only'),
                 ('E. Johnson un-red only', 'sun_ej_only')]:
    b = g.rebuilt(wk, key)
    if b:
        x = g.drop_lowest(*b)
        sets[lab] = x
        print(lab, 'shared with entered', len(set(map(frozenset, x)) & ent), 'with first upload', len(set(map(frozenset, x)) & first))
rows = []
for lab, lps in sets.items():
    r = dict(set=lab)
    r.update(g.grade(wk, lps))
    rows.append(r)
d = pd.DataFrame(rows)
d.to_csv(os.path.join(g.HERE, 'out', 'q2_week10_sets.csv'), index=False)
pd.set_option('display.width', 250)
print(d.to_string(index=False))
# exposure of key chalk in entered vs first upload
pts = pd.read_csv(os.path.join(g.HERE, 'out', wk + '_pts.csv'))
nm = dict(zip(pts.Id, pts.Name))
for lab in ['Entered 149 (edited)', 'First upload 149', 'Model 150', 'Median-70 plain', 'Cap-45']:
    c = pd.Series([nm.get(i, i) for lp in sets[lab] for i in lp]).value_counts()
    print(lab, {k: int(c.get(k, 0)) for k in ['Emmett Johnson', 'Travis Etienne Jr.', 'Christian McCaffrey', 'Brock Purdy',
                                               'George Pickens', 'Parker Washington', 'George Kittle', 'Chuba Hubbard',
                                               'Jaxon Smith-Njigba', 'Brock Bowers']})
print(pts.sort_values('%Drafted', ascending=False).head(15).to_string(index=False))
