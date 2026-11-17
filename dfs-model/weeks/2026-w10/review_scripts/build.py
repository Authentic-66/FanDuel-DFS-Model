"""In-process rebuilds on the scratch repo copy (nothing in the real weeks/ is touched).
usage: python build.py <week> <mode> <label> [json mutate]
mode: model | nodraw | median70 | v1 | v2 | v3 | cap45 | flex
mutate json: {"red_add": [...], "red_remove": [...], "player_cap": {...}, "cap_remove": [...],
              "proj_override": "path.csv" (Name,Proj: player sims rescaled to Proj, like override.py)}
writes out/builds/<week>__<label>.csv : 9 Ids + Proj (the build's own objective mean/median)."""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'repo', 'src'))
os.chdir(os.path.join(HERE, 'repo'))
import numpy as np, pandas as pd
from dfs import config, optimize as opt, ownership, project, overrides

wk, mode, label = sys.argv[1:4]
mut = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
week = config.current_week(wk)
cfg = config.load_config(week)
o = cfg['optimizer']
red = set(cfg['prefs'].get('red', []))
red |= set(mut.get('red_add', []))
red -= set(mut.get('red_remove', []))
cfg['prefs']['red'] = sorted(red)
pc = dict(cfg['prefs'].get('player_cap', {}))
for n in mut.get('cap_remove', []):
    pc.pop(n, None)
pc.update(mut.get('player_cap', {}))
cfg['prefs']['player_cap'] = pc
if mode == 'nodraw':
    o.update(mean_weight=1.0)
if mode in ('median70', 'v1', 'v2', 'v3'):
    o.update(mean_weight=1.0, exposure_cap=105, max_overlap=7)
if mode in ('v1', 'flex'):
    o.update(rb_stack_pieces=True, flex_te_top_salary=5)
if mode == 'v2':
    o['stack'] = dict(o['stack'], receivers=1, bring_back=0)
if mode == 'cap45':
    o['exposure_cap'] = 45
proj, sims = project.load(week)
if mut.get('proj_override'):
    t = pd.read_csv(mut['proj_override'])
    ov = {r.Name: float(r.Proj) for r in t.itertuples() if r.Name in set(proj.Name)}
    i_ok = {n: v for n, v in ov.items() if sims[proj.index[proj.Name == n][0]].mean() > 0 and v > 0}
    proj, sims = overrides.apply(proj, sims, i_ok)
    zero = [n for n, v in ov.items() if v <= 0]
    for n in zero:   # an outside projection of 0 = not playing for that source: zero the sims
        i = proj.index[proj.Name == n][0]
        sims[i] *= 0
        proj.loc[i, 'Proj'] = 0.0
    print(f'override: {len(i_ok)} rescaled, {len(zero)} zeroed')
proj = ownership.attach(week, cfg, proj, quiet=True)
df = opt.eligible_pool(proj, cfg['prefs'], o)
if mode in ('median70', 'v1', 'v2', 'v3'):
    df = df.assign(Proj=np.median(sims, axis=1)[df.row.values])
lineups, use = opt.build_lineups(df, sims, cfg)
if mode == 'v3':
    n = o['n_lineups']
    keep, rep = round(n * 0.7), n - round(n * 0.7)
    order = sorted(range(len(lineups)), key=lambda k: -df.Proj[lineups[k]].sum())
    top = [lineups[k] for k in order[:keep]]
    lineups = top + top[:rep]
    use = {}
    for lp in lineups:
        for i in lp:
            use[i] = use.get(i, 0) + 1
upload, readable, exposure = opt.outputs(df, sims, lineups, use, cfg)
os.makedirs(os.path.join(HERE, 'out', 'builds'), exist_ok=True)
res = pd.DataFrame(upload, columns=['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE', 'FLEX', 'DEF'])
res['Proj'] = readable.Proj.values
res.to_csv(os.path.join(HERE, 'out', 'builds', f'{wk}__{label}.csv'), index=False)
print(wk, mode, label, len(res), 'lineups, mean proj', round(res.Proj.mean(), 1))
