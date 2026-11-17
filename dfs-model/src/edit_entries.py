"""Late news after the entry is uploaded: write FanDuel's edit-entries file that swaps the uploaded lineups for the
rebuilt ones (Nov 16; adapted from weeks/2026-w10/edit_entries_build.py).

    python src/edit_entries.py --week 2026-w11 --template data/2026-w11/<FanDuel edit-entries file>.csv

--template: the file from the contest's edit-entries page (header starts entry_id,contest_id,...).
--uploaded: the folder holding what was uploaded (default: the newest weeks/<week>/entry_20_<HHMM>/, which
weekly.py --stage sunday saves before it rebuilds). New lineups: weeks/<week>/entry_20/upload.csv.
Entries whose lineup is not one of the uploaded ones (e.g. a free entry) are left untouched.
Writes weeks/<week>/entry_20/edit_entries.csv (upload it on the edit-entries page) and checks it."""
import argparse
import csv
import glob
import os

from dfs import config, data, optimize as opt

SLOTS = ['QB', 'RB', 'RB', 'WR', 'WR', 'WR', 'TE', 'FLEX', 'DEF']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--week', required=True)
    ap.add_argument('--template', required=True)
    ap.add_argument('--uploaded', default='')
    a = ap.parse_args()
    week = config.current_week(a.week)
    cfg = config.load_config(week)
    up_dir = a.uploaded or max(glob.glob(os.path.join(week.out, 'entry_20_*')), key=os.path.getmtime, default='')
    if not up_dir:
        raise SystemExit('no entry_20_<HHMM>/ folder: give --uploaded <folder with the uploaded upload.csv>')
    _, old = opt.read_upload(os.path.join(up_dir, 'upload.csv'))
    _, new = opt.read_upload(os.path.join(week.out, 'entry_20', 'upload.csv'))
    rows = list(csv.reader(open(a.template, newline='', encoding='utf-8-sig')))
    head = rows[0]
    if head[:1] != ['entry_id'] or head[4:13] != SLOTS:
        raise SystemExit(f'{a.template} is not an edit-entries file (header {head[:13]})')
    oldsets = {}
    for k, o in enumerate(old):
        oldsets.setdefault(frozenset(o), []).append(k)
    plan, other = [], []
    for i in range(1, len(rows)):
        if not rows[i] or not rows[i][0].isdigit():
            continue
        ks = oldsets.get(frozenset(rows[i][4:13]))
        (plan if ks else other).append(i)
        if ks:
            ks.pop(0)
            if not ks:
                del oldsets[frozenset(rows[i][4:13])]
    print(f'uploaded set: {up_dir}; entries matched {len(plan)}, left untouched {len(other)} '
          f'({", ".join(rows[i][0] for i in other) or "none"})')
    if len(plan) != len(new):
        raise SystemExit(f'matched {len(plan)} entries but have {len(new)} new lineups: check --uploaded')
    changed = 0
    for i, lp in zip(plan, new):
        changed += frozenset(rows[i][4:13]) != frozenset(lp)
        rows[i][4:13] = lp
    out = os.path.join(week.out, 'entry_20', 'edit_entries.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f, quoting=csv.QUOTE_ALL).writerows(rows)
    # check: player list, slots, salary, held-out / red players
    fd = data.load_slate(week.fd_players, cfg['status']).set_index('Id')
    bad_names = set(cfg['status']['out']) | set(cfg['status']['questionable']) | set(cfg['prefs'].get('red', []))
    err = []
    for i in plan:
        ids = rows[i][4:13]
        if any(x not in fd.index for x in ids):
            err.append(f'{rows[i][0]}: player not on the list')
            continue
        p = fd.loc[ids]
        if p.Salary.sum() > 60000:
            err.append(f'{rows[i][0]}: salary {p.Salary.sum()}')
        bad = [n for n in p.Nickname if n in bad_names] + list(p.Nickname[p.Inj.isin(['O', 'IR', 'Q'])])
        if bad:
            err.append(f'{rows[i][0]}: held-out player {bad}')
    if err:
        raise SystemExit('INVALID, do not upload:\n' + '\n'.join(err))
    print(f'{changed} of {len(plan)} entries change. Upload {out} on the contest\'s edit-entries page.')


if __name__ == '__main__':
    main()
