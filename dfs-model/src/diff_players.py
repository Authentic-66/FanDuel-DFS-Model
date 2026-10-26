"""Compare two FanDuel player lists for the same slate (e.g. Tuesday's fd_players.csv against Friday's download) and
report players added, players removed, injury-tag changes and salary changes. Reads only.

Week 7 lesson (docs/week7_review.md): the Oct 19 list was never refreshed, so Josh Jacobs (back from the exempt list)
was missing all week. Checklist: re-download the list Friday and Sunday morning and run this against the previous one.

    python src/diff_players.py data/2026-w08/fd_players_tue.csv data/2026-w08/fd_players.csv
"""
import argparse
import sys

import pandas as pd

TAG = 'Injury Indicator'


def load(path):
    fd = pd.read_csv(path)
    fd[TAG] = fd[TAG].fillna('')
    fd['Player'] = fd.Nickname + ' (' + fd.Team + ' ' + fd.Position + ')'
    return fd.set_index('Id')


def diff(old, new):
    """{added, removed, tags, salary} DataFrames. Players are matched on FanDuel Id (stable within a slate); a player
    whose Id changed shows up as removed and added."""
    both = old.index.intersection(new.index)
    cols = ['Player', 'Salary', 'FPPG', TAG]
    added = new.loc[new.index.difference(old.index), cols].sort_values('Salary', ascending=False)
    removed = old.loc[old.index.difference(new.index), cols].sort_values('Salary', ascending=False)
    o, n = old.loc[both], new.loc[both]
    tags = pd.DataFrame({'Player': n.Player, 'Salary': n.Salary, 'was': o[TAG], 'now': n[TAG]})[o[TAG] != n[TAG]]
    sal = pd.DataFrame({'Player': n.Player, 'was': o.Salary, 'now': n.Salary})[o.Salary != n.Salary]
    return dict(added=added, removed=removed, tags=tags.sort_values('Salary', ascending=False), salary=sal)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('old', help='earlier fd_players.csv')
    ap.add_argument('new', help='later fd_players.csv')
    ap.add_argument('--min-salary', type=int, default=0, help='list only players at or above this salary')
    a = ap.parse_args(argv)
    d = diff(load(a.old), load(a.new))
    pd.set_option('display.width', 200)
    pd.set_option('display.max_rows', 500)
    titles = dict(added='Added (in the new list only: e.g. back from IR / exempt list, signed, traded in)',
                  removed='Removed (in the old list only)', tags='Injury tag changes', salary='Salary changes')
    for k, title in titles.items():
        t = d[k]
        if a.min_salary and 'Salary' in t:
            t = t[t.Salary >= a.min_salary]
        print(f'\n{title}: {len(t)}')
        if len(t):
            print(t.to_string(index=False))
    return d


if __name__ == '__main__':
    main(sys.argv[1:])
