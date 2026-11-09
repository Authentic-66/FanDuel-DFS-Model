"""Max-entrants vs our NFL builds (Doug, Nov 6 2026; analysis only, NFL only, nothing written to weeks/).

Per week (5-8, Pooch Punt), compare the lineups of users who entered the max (150) with ours: ownership, salary by
position, stack shape, chalk (players over 20% owned), FLEX, and portfolio shape (lineup repeats, top player
exposure, players used, overlap with the nearest other lineup). Groups: field, max-entrants (all their entries),
max-entrants' top-1% entries, Doug as entered, and each of our builds re-scored on that week's actual ownership:
model (weeks/<week>/upload.csv), no-draw, median-70 and cap 45 (rebuilt from the archived inputs into a scratch
folder: --builds DIR/w05_nodraw/upload.csv etc.; the week 7-8 cap-45 controls in weeks/ are used when present).
Definitions follow learn_from_winners.py (same features). Similarity = mean |gap| over the decision metrics, each gap
in units of the field's per-lineup SD (portfolio metrics: SD across max-entrant users).

    python src/max_entrants.py --builds <scratch dir> > report.md
"""
import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dfs import config  # noqa: E402
from learn_from_winners import ID_RE, features, players_table, read_set, to_index  # noqa: E402

DOUG = 'gst1999'
EXPORTS = {'2026-w05': '10.11.2026_35k_Pooch_Punt_All_Entries.csv', '2026-w06': '135326-281053769.csv',
           '2026-w07': '135562-281154846.csv', '2026-w08': '135859-281259493.csv',
           '2026-w09': '136184-281370292.csv'}
BUILDS = ['model', 'nodraw', 'median70', 'cap45']
LINEUP_METRICS = [  # (label, function of the features frame -> per-lineup series)
    ('salary QB', lambda f: f.sal_QB), ('salary RB', lambda f: f.sal_RB), ('salary WR', lambda f: f.sal_WR),
    ('salary TE', lambda f: f.sal_TE), ('salary DST', lambda f: f.sal_D), ('salary total', lambda f: f.sal_total),
    ('avg player own %', lambda f: f.own_avg), ('total own %', lambda f: f.own_sum),
    ('chalk (>20% owned)', lambda f: f.n_over20), ('RBs', lambda f: f.n_RB),
    ('FLEX RB %', lambda f: 100 * (f.flex == 'RB')), ('FLEX WR %', lambda f: 100 * (f.flex == 'WR')),
    ('FLEX TE %', lambda f: 100 * (f.flex == 'TE')),
    ('QB stack pieces', lambda f: f.stack_n), ('QB + 2 or more %', lambda f: 100 * (f.stack_n >= 2)),
    ('bring-back %', lambda f: 100 * f.bringback), ('naked QB %', lambda f: 100 * (f.stack_n == 0)),
]
PORTFOLIO = ['distinct lineups per 150', 'top player exposure %', 'players used', 'overlap with nearest lineup']


def portfolio(f):
    """Shape of one 150-lineup set (f = features of its lineups, duplicates included)."""
    keys = [tuple(sorted(x)) for x in f.ids]
    uniq = sorted(set(keys))
    s = pd.Series([i for lu in f.ids for i in lu]).value_counts()
    m = np.zeros((len(uniq), len({i for k in uniq for i in k})), dtype=np.int8)
    col = {i: j for j, i in enumerate({i for k in uniq for i in k})}
    for r, k in enumerate(uniq):
        m[r, [col[i] for i in k]] = 1
    shared = m.astype(np.int16) @ m.T.astype(np.int16)
    np.fill_diagonal(shared, -1)
    near = shared.max(axis=1).mean() if len(uniq) > 1 else 9.0
    return {'distinct lineups per 150': 150 * len(uniq) / len(keys), 'top player exposure %': 100 * s.iloc[0] / len(keys),
            'players used': s.size, 'overlap with nearest lineup': near}


def week_tables(wk, builds_dir):
    week = config.Week(wk)
    raw = pd.read_csv(os.path.join(week.data, 'raw', EXPORTS[wk]), encoding='utf-8-sig', low_memory=False)
    P = players_table(raw, week)
    ent = raw[['Rank', 'EntryName', 'Points', 'Lineup']].dropna(subset=['Lineup']).copy()
    lus = ent.Lineup.str.findall(ID_RE)
    full = (lus.str.len() == 9).values
    ent, lus = ent[full], lus[full]
    nm = ent.EntryName.str.extract(r'^(.*) \((\d+)/(\d+)\)$')
    F = features(to_index(lus.tolist(), P), P)
    F['Rank'] = pd.to_numeric(ent.Rank, errors='coerce').values
    F['user'], F['n'] = nm[0].values, nm[2].astype(int).values
    cut = np.ceil(0.01 * len(F))
    groups = {'field': F, 'max-entrants': F[F.n == 150], 'max top-1%': F[(F.n == 150) & (F.Rank <= cut)],
              'field top-1%': F[F.Rank <= cut], 'Doug entered': F[F.user == DOUG]}
    sets = {}
    for b in BUILDS:
        cands = [os.path.join(week.out, 'upload.csv')] if b == 'model' else []
        if b == 'cap45':
            cands.append(os.path.join(week.out, 'model_cap45', 'upload.csv'))
        cands.append(os.path.join(builds_dir, f'{wk[-3:].replace("-", "")}_{b}', 'upload.csv'))
        path = next((c for c in cands if os.path.exists(c)), None)
        if path:
            fs = features(to_index(read_set(path), P), P)
            if len(fs):
                groups[b] = fs
                sets[b] = fs
    rows = {g: {lab: fn(f).mean() for lab, fn in LINEUP_METRICS} for g, f in groups.items()}
    sd = {lab: fn(F).std() for lab, fn in LINEUP_METRICS}
    # portfolio shape: each max-entrant user's 150 (averaged; SD across users) vs our sets
    users = groups['max-entrants'].groupby('user')
    up = pd.DataFrame([portfolio(f) for _, f in users if len(f) == 150])
    for k in PORTFOLIO:
        rows['max-entrants'][k] = up[k].mean()
        sd[k] = up[k].std()
    for g in ['Doug entered'] + list(sets):
        if len(groups[g]) >= 100:
            for k, v in portfolio(groups[g]).items():
                rows[g][k] = v
    return pd.DataFrame(rows), sd, {g: len(f) for g, f in groups.items()}, len(up)


def gap(T, sd, ref, cols, metrics):
    return {c: np.nanmean([abs(T.at[m, c] - T.at[m, ref]) / sd[m] for m in metrics
                           if m in T.index and pd.notna(T.at[m, c]) and sd[m] > 0]) for c in cols}


def md(df, fmt='{:.1f}'):
    out = ['| ' + ' | '.join([''] + list(map(str, df.columns))) + ' |', '|' + '---|' * (len(df.columns) + 1)]
    for i, r in df.iterrows():
        out.append('| ' + ' | '.join([str(i)] + ['' if pd.isna(v) else fmt.format(v) if isinstance(v, (float, int, np.floating, np.integer)) else str(v) for v in r]) + ' |')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--builds', required=True, help='scratch folder holding w05_nodraw/upload.csv etc.')
    ap.add_argument('--weeks', default=','.join(EXPORTS), help='comma list, default weeks 5-9')
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    allT, gaps = [], []
    for wk in a.weeks.split(','):
        T, sd, n, nu = week_tables(wk, a.builds)
        ours = [c for c in ['Doug entered'] + BUILDS if c in T.columns]
        lm = [m for m, _ in LINEUP_METRICS]
        g1 = gap(T, sd, 'max-entrants', ours, lm)
        g2 = gap(T, sd, 'max top-1%', ours, lm)
        g3 = gap(T, sd, 'max-entrants', ours, PORTFOLIO)
        gaps.append(pd.DataFrame({'vs max-entrants (lineups)': g1, 'vs max top-1% (lineups)': g2,
                                  'vs max-entrants (portfolio)': g3}).assign(week=wk))
        print(f'## {wk}\n')
        print('Lineups: ' + ', '.join(f'{g} {v:,}' for g, v in n.items()) + f'; max-entrant users with 150: {nu:,}\n')
        print(md(T.rename(columns={'Doug entered': 'Doug'})))
        print()
        allT.append(T.assign(week=wk))
    G = pd.concat(gaps)
    print('## Similarity: mean gap in SD units (lower = more like max-entrants), per week\n')
    for wk, g in G.groupby('week'):
        print(f'**{wk}**\n')
        print(md(g.drop(columns='week'), '{:.2f}'))
        print()
    print('**Weeks 5-8 average**\n')
    print(md(G.drop(columns='week').groupby(level=0).mean().reindex([c for c in ['Doug entered'] + BUILDS if c in G.index]),
             '{:.2f}'))
    A = pd.concat(allT)
    print('\n## Weeks 5-8 average of every metric\n')
    print(md(A.drop(columns='week').groupby(level=0, sort=False).mean().rename(columns={'Doug entered': 'Doug'})))


if __name__ == '__main__':
    main()
