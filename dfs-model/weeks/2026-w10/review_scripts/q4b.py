import pandas as pd
import gradelib as g
rows = []
for w in ['2026-w09', '2026-w10']:
    for lab, x in [('model (ours)', g.archived(w)), ('FDR projections', g.rebuilt(w, 'fdr')), ('50/50 blend', g.rebuilt(w, 'blend'))]:
        if x is None:
            continue
        r = dict(week=w[-2:], build=lab)
        r.update(g.grade(w, x[0]))
        rows.append(r)
d = pd.DataFrame(rows)
pd.set_option('display.width', 250)
print(d.to_string(index=False))
t = d.groupby('build')[['avg', 'cashed', 'won', 'net', 'top10', 'top1']].agg({'avg': 'mean', 'cashed': 'sum', 'won': 'sum',
                                                                            'net': 'sum', 'top10': 'sum', 'top1': 'sum'})
print(t.round(2).to_string())
d.to_csv(g.HERE + '/out/q4_builds.csv', index=False)
