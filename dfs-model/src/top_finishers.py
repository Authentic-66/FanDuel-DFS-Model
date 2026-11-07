"""Who finishes at the top? NFL only (Doug, Nov 6 2026; analysis only, no model change).

Reads the full All Entries exports of NFL weeks 5-8 (data/<week>/raw/). FanDuel's EntryName is "user (k/N)": N = that user's entries in the contest. Prints aggregated tables only;
usernames never leave memory (repeat winners get anonymous ids user_001..., assigned by this run, mapping not
saved). Doug (gst1999) is shown as "Doug". NFL only: never pooled with the other sport (Doug, Nov 6).
Cash = rank within the paid places of the week-9 $35K Pooch Punt table (data/2026-w09/prizes_pooch-punt.csv),
which reproduces Doug's winnings for weeks 5, 7 and 8 to the cent and week 6 within $0.01. The week-5 Hail
Mary has no prize table: in sections 1-3, not 4.

    python src/top_finishers.py > scratch.md   (report: docs/top_finishers.md)
"""
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPORT = 'NFL'
DOUG = 'gst1999'
FEE = 0.05
PRIZES = os.path.join(ROOT, 'data', '2026-w09', 'prizes_pooch-punt.csv')
CONTESTS = [  # label, sport, raw export, prize table (None = unknown)
    ('wk5 Pooch Punt', 'NFL', os.path.join(ROOT, 'data', '2026-w05', 'raw', '10.11.2026_35k_Pooch_Punt_All_Entries.csv'),
     PRIZES),
    ('wk5 Hail Mary', 'NFL', os.path.join(ROOT, 'data', '2026-w05', 'raw', '10.11.2026_45k_Hail_Mary_All_Entries.csv'),
     None),
    ('wk6 Pooch Punt', 'NFL', os.path.join(ROOT, 'data', '2026-w06', 'raw', '135326-281053769.csv'), PRIZES),
    ('wk7 Pooch Punt', 'NFL', os.path.join(ROOT, 'data', '2026-w07', 'raw', '135562-281154846.csv'), PRIZES),
    ('wk8 Pooch Punt', 'NFL', os.path.join(ROOT, 'data', '2026-w08', 'raw', '135859-281259493.csv'), PRIZES),
]
BUCKETS = ['1', '2-20', '21-149', '150 (max)']


def bucket(n, nmax):
    if n >= nmax:
        return '150 (max)'
    return '1' if n == 1 else '2-20' if n <= 20 else '21-149'


def load(path, prizes):
    d = pd.read_csv(path, usecols=['Rank', 'EntryId', 'EntryName', 'Points', 'Lineup'], encoding='utf-8-sig',
                    low_memory=False).dropna(subset=['EntryId'])
    p = d.EntryName.astype(str).str.extract(r'^(.*) \((\d+)/(\d+)\)$')
    d['user'], d['n'] = p[0], p[2].astype(float)
    d = d.dropna(subset=['user'])
    d['n'] = d.n.astype(int)
    d['Rank'] = pd.to_numeric(d.Rank, errors='coerce')
    d['scored'] = pd.to_numeric(d.Points, errors='coerce').notna()
    nmax = d.n.max()
    d['bucket'] = [bucket(n, nmax) for n in d.n]
    if prizes:
        t = pd.read_csv(prizes)
        edges = t.rank_to.values
        idx = np.searchsorted(edges, d.Rank.fillna(10 ** 9).values)
        d['won'] = np.where(idx < len(t), t.prize.values[np.minimum(idx, len(t) - 1)], 0.0)
        d.loc[~d.scored, 'won'] = 0.0
    return d, nmax


def md(df):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    out += ['| ' + ' | '.join(str(v) for v in r) + ' |' for r in df.itertuples(index=False)]
    return '\n'.join(out)


def pct(x):
    return f'{100 * x:.1f}%'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    s1, s2, s4, alltop, users = [], [], [], [], []
    pool2 = {b: [0, 0, 0, 0] for b in BUCKETS}          # field entries, field users, top-1% entries, top-1% users
    pool4 = {}                                          # (sport, bucket) -> entries, cashed, won
    dup = {b: [0, 0] for b in BUCKETS}                  # entries, distinct lineups within each user
    for label, sport, path, prizes in CONTESTS:
        d, nmax = load(path, prizes)
        e = len(d)
        cut1 = math.ceil(0.01 * e)
        row = dict(Contest=label, Entries=f'{e:,}', Users=f'{d.user.nunique():,}', Max_entries=nmax)
        for name, k in [('Top 20', 20), ('Top 100', 100), ('Top 1%', cut1)]:
            t = d[d.Rank <= k]
            vc = t.user.value_counts()
            row[f'{name}: users'] = f'{vc.size} of {len(t)}'
            top_user = vc.index[0]
            row[f'{name}: most by 1 user'] = (f'{vc.iloc[0]} ({d.loc[d.user == top_user, "n"].max()} entered, '
                                              f'{t.loc[t.user == top_user, "Lineup"].nunique()} distinct)')
        s1.append(row)
        u = d.groupby('user').agg(n=('n', 'max'), bucket=('bucket', 'first'))
        top = d[d.Rank <= cut1]
        alltop.append(top.assign(contest=label))
        users.append(u.assign(contest=label, top1=top.groupby('user').size().reindex(u.index).fillna(0).astype(int),
                              sport=sport))
        r2 = dict(Contest=label)
        tb = top.groupby('user').bucket.first()
        for b in BUCKETS:
            x = d[d.bucket == b]
            dup[b] = [dup[b][0] + len(x), dup[b][1] + x.groupby('user').Lineup.nunique().sum()]
            fe, fu = (d.bucket == b).sum(), (u.bucket == b).sum()
            te, tu = (top.bucket == b).sum(), (tb == b).sum()
            pool2[b] = [x + y for x, y in zip(pool2[b], [fe, fu, te, tu])]
            r2[b] = f'{pct(te / len(top))} vs {pct(fe / e)}'
        s2.append(r2)
        if prizes:
            r4 = dict(Contest=label, Field_cash=pct((d.won > 0).mean()), Field_return=f'{d.won.sum() / (FEE * e):.2f}')
            dg = d[d.user == DOUG]
            for b, x in [(b, d[d.bucket == b]) for b in BUCKETS] + [('Doug', dg)]:
                for k in ('All',):
                    v = pool4.setdefault((k, b), [0, 0, 0.0])
                    pool4[(k, b)] = [v[0] + len(x), v[1] + (x.won > 0).sum(), v[2] + x.won.sum()]
                if b != 'Doug':
                    r4[b] = f'{pct((x.won > 0).mean())} / {x.won.sum() / (FEE * len(x)):.2f}' if len(x) else '-'
            r4['Doug'] = f'{pct((dg.won > 0).mean())} / {dg.won.sum() / (FEE * len(dg)):.2f}' if len(dg) else '-'
            s4.append(r4)

    print('## 1. Concentration at the top (users among the top entries; most entries one user had there, with '
          'that user\'s total entries in the contest)\n')
    print(md(pd.DataFrame(s1)))
    print('\n## 2. Share of top-1% entries vs share of field entries, by the user\'s entries in the contest\n')
    print(md(pd.DataFrame(s2)))
    tot_f = sum(v[0] for v in pool2.values()); tot_t = sum(v[2] for v in pool2.values())
    tot_fu = sum(v[1] for v in pool2.values()); tot_tu = sum(v[3] for v in pool2.values())
    print(f'\nAll {SPORT} contests:\n')
    print(md(pd.DataFrame([dict(Entries_per_user=b, Field_entries=pct(v[0] / tot_f), Top1_entries=pct(v[2] / tot_t),
                                Lift=f'{(v[2] / tot_t) / (v[0] / tot_f):.2f}', Top1_rate_per_entry=pct(v[2] / v[0]),
                                Field_users=pct(v[1] / tot_fu), Users_with_a_top1=pct(v[3] / tot_tu))
                           for b, v in pool2.items()])))

    print('\nDuplicate lineups: distinct lineups per entry within a user (1.00 = no repeats), pooled:\n')
    print(md(pd.DataFrame([dict(Entries_per_user=b, Distinct_per_entry=f'{v[1] / v[0]:.2f}') for b, v in dup.items()])))

    U = pd.concat(users).reset_index()
    per = U.groupby('user').agg(contests=('contest', 'size'), top1_contests=('top1', lambda s: (s > 0).sum()),
                                top1_entries=('top1', 'sum'), entries=('n', 'sum'), median_n=('n', 'median'),
                                sports=('sport', lambda s: '+'.join(sorted(set(s)))))
    per['rate'] = per.top1_entries / per.entries
    rep = per[per.top1_contests >= 3].sort_values(['top1_contests', 'top1_entries'], ascending=False)
    print(f'\n## 3. Repeat winners: users in the top 1% of 3+ of the {len(CONTESTS)} contests\n')
    print(f'{len(rep)} users (of {len(per):,} distinct users; {(per.contests >= 3).sum():,} entered 3+ contests).\n')
    print(md(rep.groupby('top1_contests').size().rename('Users').reset_index().rename(columns={'top1_contests': 'Top-1% contests'})))
    print('\nTop 25 (and Doug):\n')
    out = rep.reset_index()
    out['user'] = ['Doug' if x == DOUG else f'user_{i + 1:03d}' for i, x in enumerate(out.user)]
    out['rate'] = out.rate.map(pct)
    out['median_n'] = out.median_n.astype(int)
    out = out[(out.index < 25) | (out.user == 'Doug')]
    print(md(out.rename(columns={'user': 'User', 'contests': 'Contests entered', 'top1_contests': 'Top-1% contests',
                                 'top1_entries': 'Top-1% entries', 'entries': 'Total entries',
                                 'median_n': 'Median entries per contest', 'sports': 'Sports',
                                 'rate': 'Top-1% rate per entry'})))
    big = per[per.contests >= 3]
    print('\nEntered 3+ contests, by median entries per contest (top-1% rate per entry; field 1%):\n')
    big = big.assign(b=pd.cut(big.median_n, [0, 1, 20, 149, 150], labels=BUCKETS))
    print(md(big.groupby('b', observed=True).apply(lambda g: pd.Series(dict(
        Users=len(g), With_3plus_top1=(g.top1_contests >= 3).sum(),
        Rate=pct(g.top1_entries.sum() / g.entries.sum())))).reset_index().rename(columns={'b': 'Entries_per_contest'})))
    if DOUG in per.index:
        dg = per.loc[DOUG]
        print(f'\nDoug: {dg.contests} contests, {dg.top1_contests} with a top-1% entry, {dg.top1_entries} top-1% '
              f'entries of {dg.entries} ({pct(dg.rate)}).')

    print('\n## 4. Cash rate / return (won / fees) by entries per user (contests with a prize table)\n')
    print(md(pd.DataFrame(s4)))
    for k in ('All',):
        rows = {b: pool4[(k, b)] for b in BUCKETS}
        te = sum(v[0] for v in rows.values()); tc = sum(v[1] for v in rows.values()); tw = sum(v[2] for v in rows.values())
        g = pool4[(k, 'Doug')]
        print(f'\nAll {SPORT} contests: field cash {pct(tc / te)}, return {tw / (FEE * te):.2f}; Doug {g[0]} entries, cash '
              f'{pct(g[1] / g[0])}, return {g[2] / (FEE * g[0]):.2f}\n')
        print(md(pd.DataFrame([dict(Entries_per_user=b, Entries=f'{v[0]:,}', Share_of_entries=pct(v[0] / te),
                                    Cash_rate=pct(v[1] / v[0]), Share_of_cashes=pct(v[1] / tc),
                                    Return=f'{v[2] / (FEE * v[0]):.2f}', Share_of_prize_money=pct(v[2] / tw))
                               for b, v in rows.items()])))


if __name__ == '__main__':
    main()
