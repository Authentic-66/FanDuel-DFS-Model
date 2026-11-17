"""Doug's review sheet, news calls only (Nov 16; weeks 11-12).

    python src/review_sheet.py --week 2026-w11 build    # after the Friday run -> data/<week>/review_sheet.xlsx
    python src/review_sheet.py --week 2026-w11 apply    # reads data/<week>/review_sheet_reviewed.xlsx

Build: one row per player projected 3+ or in any model lineup: Name, Pos, Team, Salary, Proj, Inj (FanDuel tag),
Lineups (model), RoutingBump (points from teammates out), Promoted (role guard), RoleDrop, then Doug's columns:
  Color = red  -> left out of every set ([prefs] red)
  Cap   = N    -> at most N lineups per set ([prefs.player_cap])
  Note  = why (news only from week 11: backup becomes the starter, back from IR, a real role change; Doug, Nov 16).
Apply: rewrites the SHEET blocks in config/<week>/week.toml (between the '# >>> SHEET' and '# <<< SHEET' lines of
[prefs] red and [prefs.player_cap]) and prints them back for checking; names must be on the sheet exactly.
Then rerun python src/weekly.py --week <week> --stage friday --keep-list (or wait for Sunday)."""
import argparse
import os
import re

import pandas as pd

from dfs import config


def build(week):
    proj = pd.read_csv(week.proj)
    ex = pd.read_csv(os.path.join(week.out, 'exposure.csv'))
    n = ex.set_index('Player').Lineups
    proj['Lineups'] = proj.Name.map(n).fillna(0).astype(int)
    df = proj[(proj.Proj >= 3) | (proj.Lineups > 0)].copy()
    df['Promoted'] = df.GuardRescue.fillna('') if 'GuardRescue' in df else ''
    df['RoleDrop'] = df.RoleDrop.fillna('') if 'RoleDrop' in df else ''
    cols = ['Name', 'Pos', 'Team', 'Opp', 'Salary', 'Proj', 'Inj', 'Lineups', 'RoutingBump', 'Promoted', 'RoleDrop']
    df = df[cols].sort_values(['Pos', 'Proj'], ascending=[True, False])
    df['Color'] = ''
    df['Cap'] = ''
    df['Note'] = ''
    path = os.path.join(week.data, 'review_sheet.xlsx')
    df.to_excel(path, index=False)
    print(f'{path}: {len(df)} players. Mark news calls only (Color = red, Cap = N, Note = why), save as '
          f'review_sheet_reviewed.xlsx, then run apply.')


def block(text, header, lines):
    """Replace the SHEET block inside the table that starts with `header`."""
    start = re.search(r'(?m)^' + re.escape(header) + r'.*$', text)
    if not start:
        raise SystemExit(f'week.toml has no {header} line')
    a = text.index('# >>> SHEET', start.end())
    b = text.index('# <<< SHEET', a)
    a = text.index('\n', a) + 1
    return text[:a] + ''.join(lines) + text[b:]


def apply(week):
    path = os.path.join(week.data, 'review_sheet_reviewed.xlsx')
    s = pd.read_excel(path, dtype=str).fillna('')
    s = s.apply(lambda c: c.str.strip())
    known = set(pd.read_csv(week.proj).Name)
    red = s[s.Color.str.lower() == 'red']
    cap = s[s.Cap != '']
    unknown = sorted((set(red.Name) | set(cap.Name)) - known)
    other = sorted(set(s.Color.str.lower()) - {'', 'red'})
    if unknown or other:
        raise SystemExit(f'fix the sheet: names not in proj.csv {unknown}; Color values other than red {other}')
    bad_cap = [r.Name for r in cap.itertuples() if not r.Cap.split('.')[0].isdigit()]
    if bad_cap:
        raise SystemExit(f'fix the sheet: Cap must be a number of lineups: {bad_cap}')
    note = lambda r: f'  # {r.Note}' if r.Note else ''
    red_lines = [f'  "{r.Name}",{note(r)}\n' for r in red.itertuples()]
    cap_lines = [f'"{r.Name}" = {int(float(r.Cap))}{note(r)}\n' for r in cap.itertuples()]
    toml = os.path.join(week.config_dir, 'week.toml')
    text = open(toml, encoding='utf-8').read()
    text = block(text, 'red = [', red_lines)
    text = block(text, '[prefs.player_cap]', cap_lines)
    with open(toml, 'w', encoding='utf-8') as f:
        f.write(text)
    cfg = config.load_config(week)   # read back through the real loader
    print(f'red ({len(cfg["prefs"]["red"])}):', ', '.join(cfg['prefs']['red']) or 'none')
    print('caps:', ', '.join(f'{k} {v}' for k, v in cfg['prefs']['player_cap'].items()) or 'none')
    print('notes:', *[f'{r.Name}: {r.Note}' for r in s[s.Note != ''].itertuples()], sep='\n  ')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--week', required=True)
    ap.add_argument('action', choices=['build', 'apply'])
    a = ap.parse_args()
    week = config.current_week(a.week)
    (build if a.action == 'build' else apply)(week)


if __name__ == '__main__':
    main()
