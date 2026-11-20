"""Doug's Friday update and Sunday final in one command (Nov 16; weeks 11-12 routine, docs/commands.md).

    python src/weekly.py --week 2026-w11 --stage friday     # data/2026-w11/fd_players_friday.csv
    python src/weekly.py --week 2026-w11 --stage sunday     # data/2026-w11/fd_players_sunday.csv

Steps (stops on any problem):
 1. FanDuel list: data/<week>/fd_players_<stage>.csv is diffed against the current fd_players.csv (players added /
    removed, tag and salary changes), then copied over it.
 2. nflverse stats + snaps refreshed (fetch_stats.py); --no-fetch skips it.
 3. Statuses from FanDuel's tags -> config/<week>/auto.toml [status] (week.toml adds to / overrides it):
    O, D and NA (Sunday's official inactives) -> out; IR with 3+ targets + carries a game this season -> out (their
    volume is routed to teammates); Q -> questionable (held out of lineups). Players FanDuel clears drop off.
 4. Lines: nflverse games.csv spread / total for the slate's games -> data/<week>/lines.csv, and stack weights
    round(2 x (implied - 16)), min 1 -> auto.toml [stacks.weights]. --keep-lines keeps the existing lines.csv.
 5. model.py, then every set (frozen through week 12): model (main folder), model_cap45, flex_shadow, nodraw,
    median70 (30% injury cap), median70_plain, median70_v1 / v2 / v3, and pool if [pool] lists exist.
 6. Rule check of every set (slots, salary, out / Q / red players, duplicates; repeats only in v3).
 7. ENTRY = the flex shadow's 20 highest-projected lineups -> weeks/<week>/entry_20/upload.csv (+ readable.csv,
    exposure.csv). Friday's is a preview. On Sunday an earlier Sunday entry is copied to entry_20_<HHMM>/ first.
Late news after uploading: edit week.toml (see docs/commands.md), rerun --stage sunday --keep-list, then
src/edit_entries.py writes FanDuel's edit-entries file."""
import argparse
import datetime as dt
import io
import os
import shutil
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from dfs import config, data, optimize as opt

HERE = os.path.dirname(os.path.abspath(__file__))
GAMES = 'https://github.com/nflverse/nfldata/raw/master/data/games.csv'
IR_MIN_VOL = 3.0
ENTRY_N, ENTRY_FROM, ENTRY_DIR = 20, 'flex_shadow', 'entry_20'
RB_PIECE_SETS = {'flex_shadow', 'median70_v1'}   # rb_stack_pieces builds: [optimizer] no_qb_own_rb = "rb_pieces" applies
SETS = [   # (folder, optimize.py args) -- frozen through week 12 (Doug, Nov 16)
    ('model_cap45', ['--subdir', 'model_cap45', '--cap', '45']),
    ('flex_shadow', ['--flex-shadow']),
    ('nodraw', ['--no-draw']),
    ('median70', ['--median70', '--injury-cap', '45']),
    ('median70_plain', ['--median70', '--subdir', 'median70_plain']),
    ('median70_v1', ['--median70', '--variant', 'flex']),
    ('median70_v2', ['--median70', '--variant', 'stack']),
    ('median70_v3', ['--median70', '--variant', 'repeats']),
]


def run(args, log=None):
    cmd = [sys.executable, os.path.join(HERE, args[0])] + args[1:]
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    if log:
        with open(log, 'w', encoding='utf-8') as f:
            f.write(r.stdout + r.stderr)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit(f'FAILED: {" ".join(args)}')
    return r.stdout


def toml_list(name, items, notes):
    body = ''.join(f'  "{n}",{"  # " + notes[n] if notes.get(n) else ""}\n' for n in items)
    return f'{name} = [\n{body}]\n'


def ir_volume(week, cfg):
    """Targets + carries a game this season (nflverse), by FanDuel join key."""
    st = data.load_stats(week.stats(), cfg, before_week=week.number)
    st['vol'] = st.targets.fillna(0) + st.carries.fillna(0)
    return st.groupby('k').vol.mean()


def statuses(week, cfg, fd_path):
    raw = pd.read_csv(fd_path, dtype=str, keep_default_na=False)
    tag = raw['Injury Indicator']
    vol = ir_volume(week, cfg)
    raw['vol'] = raw.Nickname.map(data.norm_name).map(vol).fillna(0)
    notes, out, q = {}, [], []
    for r in raw.itertuples():
        t = tag[r.Index]
        if t in ('O', 'D', 'NA'):
            out.append(r.Nickname)
            notes[r.Nickname] = {'O': 'FanDuel O', 'D': 'FanDuel D', 'NA': 'FanDuel NA = inactive'}[t]
        elif t == 'IR' and r.vol >= IR_MIN_VOL:
            out.append(r.Nickname)
            notes[r.Nickname] = f'FanDuel IR, {r.vol:.1f} targets + carries a game'
        elif t == 'Q':
            q.append(r.Nickname)
    return out, q, notes


def lines(week, cfg, teams):
    games = pd.read_csv(io.BytesIO(urllib.request.urlopen(GAMES).read()), low_memory=False)
    fdmap = cfg['teams']['nflverse_to_fd']
    g = games[(games.season == week.season) & (games.week == week.number)].copy()
    g['away'] = g.away_team.replace(fdmap)
    g['home'] = g.home_team.replace(fdmap)
    g = g[g.away.isin(teams) & g.home.isin(teams)]
    missing = set(teams) - set(g.away) - set(g.home)
    if missing:
        raise SystemExit(f'lines: no nflverse game for {sorted(missing)}')
    if g.spread_line.isna().any() or g.total_line.isna().any():
        raise SystemExit('lines: nflverse has no spread / total yet for ' + ', '.join(g[g.total_line.isna()].away))
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    rows = []
    for r in g.itertuples():   # nflverse spread_line > 0 = home favoured
        fav = r.home if r.spread_line >= 0 else r.away
        rows.append(dict(away=r.away, home=r.home, fav=fav, spread=abs(float(r.spread_line)), total=float(r.total_line),
                         note=f'nflverse games.csv spread_line/total_line, downloaded {stamp} (weekly.py)'))
    return pd.DataFrame(rows), g


def weights(ln):
    w = {}
    for r in ln.itertuples():
        for team, implied in [(r.fav, r.total / 2 + r.spread / 2),
                              (r.home if r.fav == r.away else r.away, r.total / 2 - r.spread / 2)]:
            w[team] = max(1, int(2 * (implied - 16) + 0.5))   # round half up (week 7: HOU 20.5 -> 21)
    return dict(sorted(w.items(), key=lambda kv: -kv[1]))


def check_sets(week, cfg, folders):
    sys.path.insert(0, HERE)
    from combine_entry import check
    fd = data.load_slate(week.fd_players, cfg['status'])
    probs = {}
    for f in folders:
        header, rows = opt.read_upload(os.path.join(week.out, f, 'upload.csv'))
        bad = check(rows, header, fd, cfg)
        if f == 'median70_v3':
            bad = [b for b in bad if 'duplicate lineup' not in b]
        info = fd.set_index('Id')
        floor = cfg['optimizer'].get('min_salary', 0)
        low = sum(info.Salary[list(r)].sum() < floor for r in rows)
        # QB + own RB ban (Doug, Nov 20): the builds with every RB as a stack piece
        mode = cfg['optimizer'].get('no_qb_own_rb', 'off')
        if mode == 'all' or (mode == 'rb_pieces' and f in RB_PIECE_SETS):
            for k, r in enumerate(rows, 1):
                q = [i for i in r if info.Position[i] == 'QB'][0]
                own = [info.Nickname[i] for i in r if info.Position[i] == 'RB' and info.Team[i] == info.Team[q]]
                if own:
                    bad.append(f'lineup {k}: QB {info.Nickname[q]} with his own RB {own}')
        print(f'  {f or "model"}: {len(rows)} lineups, {len(bad)} problems' + (f', {low} under ${floor:,}' if low else ''))
        if bad:
            probs[f] = bad[:5]
    return probs


def entry(week, stage):
    src = os.path.join(week.out, ENTRY_FROM)
    header, rows = opt.read_upload(os.path.join(src, 'upload.csv'))
    rd = pd.read_csv(os.path.join(src, 'readable.csv'))
    top = rd.Proj.sort_values(ascending=False, kind='stable').index[:ENTRY_N]
    dest = os.path.join(week.out, ENTRY_DIR)
    mark = os.path.join(dest, 'stage.txt')
    if stage == 'sunday' and os.path.exists(mark) and open(mark).read().startswith('sunday'):
        keep = dest + '_' + dt.datetime.fromtimestamp(os.path.getmtime(mark)).strftime('%H%M')
        shutil.copytree(dest, keep, dirs_exist_ok=True)
        print(f'earlier Sunday entry kept in {keep} (in case it was already uploaded)')
    os.makedirs(dest, exist_ok=True)
    opt.write_upload(os.path.join(dest, 'upload.csv'), [rows[i] for i in top], header)
    sel = rd.loc[top].reset_index(drop=True)
    sel.insert(0, 'FromLineup', top + 1)
    sel.to_csv(os.path.join(dest, 'readable.csv'), index=False)
    cols = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'WR3', 'TE', 'FLEX', 'DEF']
    names = pd.Series([c.split(' (')[0] for c in sel[cols].values.ravel()]).value_counts()
    names.rename_axis('Player').rename('Lineups').to_csv(os.path.join(dest, 'exposure.csv'))
    with open(mark, 'w') as f:
        f.write(f'{stage} {dt.datetime.now():%Y-%m-%d %H:%M}\n')
    return sel, names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--week', required=True)
    ap.add_argument('--stage', required=True, choices=['friday', 'sunday'])
    ap.add_argument('--keep-list', action='store_true', help='rerun on the current fd_players.csv (late news rerun)')
    ap.add_argument('--keep-lines', action='store_true', help='keep data/<week>/lines.csv as it is')
    ap.add_argument('--no-fetch', action='store_true', help='skip the nflverse stats refresh')
    a = ap.parse_args()
    week = config.current_week(a.week)
    if not os.path.exists(os.path.join(week.config_dir, 'week.toml')):
        raise SystemExit(f'no config/{week.name}/week.toml: the week has not been set up')
    print(f'=== {week.name} {a.stage.upper()} ({dt.datetime.now():%a %b %d %H:%M}) ===')

    # 1. player list
    new = os.path.join(week.data, f'fd_players_{a.stage}.csv')
    if not a.keep_list:
        if not os.path.exists(new):
            raise SystemExit(f'save FanDuel\'s player list as {new} first')
        if os.path.exists(week.fd_players):
            print('\n--- player list changes vs the previous fd_players.csv ---')
            print(run(['diff_players.py', week.fd_players, new]))
        shutil.copyfile(new, week.fd_players)
        print(f'fd_players.csv <- {os.path.basename(new)}')
    # 2. stats
    if not a.no_fetch:
        run(['fetch_stats.py', '--week', week.name])
        print('nflverse stats + snaps refreshed')
    cfg = config.load_config(week)
    # 3. statuses + 4. lines -> auto.toml
    out, q, notes = statuses(week, cfg, week.fd_players)
    teams = sorted(pd.read_csv(week.fd_players).Team.unique())
    if a.keep_lines:
        ln = pd.read_csv(week.lines)
        print('lines: kept the existing lines.csv')
    else:
        ln, _ = lines(week, cfg, teams)
        ln.to_csv(week.lines, index=False)
        print(f'lines: {len(ln)} games written to {week.lines}')
    w = weights(ln)
    text = (f'# WRITTEN BY src/weekly.py --stage {a.stage} ({dt.datetime.now():%Y-%m-%d %H:%M}); do not edit: it is\n'
            f'# rewritten every run. Your own calls go in week.toml (they add to / override this file).\n'
            f'[status]\n' + toml_list('out', out, notes) + toml_list('questionable', q, {}) +
            '\n[stacks.weights]\n' + ''.join(f'{t} = {v}\n' for t, v in w.items()))
    with open(os.path.join(week.config_dir, 'auto.toml'), 'w', encoding='utf-8') as f:
        f.write(text)
    cfg = config.load_config(week)
    print(f'statuses: {len(out)} out (O / D / NA / IR 3+), {len(q)} questionable (held out): {", ".join(q) or "none"}')
    print('stack weights: ' + ', '.join(f'{t} {v}' for t, v in w.items()))
    # 5. model + sets
    print('\n--- model.py ---')
    mlog = os.path.join(week.out, 'model_log.txt')
    os.makedirs(week.out, exist_ok=True)
    txt = run(['model.py', '--week', week.name], mlog)
    warn = [l for l in txt.splitlines() if any(k in l.lower() for k in ('warn', 'no starting qb', 'starter', 'mismatch'))]
    print('\n'.join(warn[:25]) or 'no warnings', f'\n(full log: {mlog})')
    jobs = [('', [])] + SETS + ([('pool', ['--pool'])] if any(cfg.get('pool', {}).get(p) for p in
                                                             ('QB', 'RB', 'WR', 'TE', 'DST')) else [])
    print(f'\n--- building {len(jobs)} sets (a few minutes) ---')

    def one(job):
        folder, args = job
        log = os.path.join(week.out, f'build_log_{folder or "model"}.txt')
        run(['optimize.py', '--week', week.name] + args, log)
        return folder
    with ThreadPoolExecutor(3) as ex:
        for folder in ex.map(one, jobs):
            print(f'  built {folder or "model (main folder)"}')
    # 6. checks
    print('\n--- rule check ---')
    probs = check_sets(week, cfg, [j[0] for j in jobs])
    if probs:
        for f, b in probs.items():
            print(f'PROBLEM in {f or "model"}:', *b, sep='\n  ')
        raise SystemExit('INVALID: do not upload; fix and rerun')
    # 7. entry
    sel, names = entry(week, a.stage)
    print(f'\n=== ENTRY ({"PREVIEW, do not upload" if a.stage == "friday" else "upload this"}): '
          f'{os.path.join(week.out, ENTRY_DIR, "upload.csv")} ===')
    print(f'{len(sel)} lineups from {ENTRY_FROM}, projection {sel.Proj.min()}-{sel.Proj.max()} (avg {sel.Proj.mean():.1f})')
    print('stacks:', sel.Stack.value_counts().to_dict())
    print('most used:', ', '.join(f'{n} {c}' for n, c in names.head(12).items()))


if __name__ == '__main__':
    main()
