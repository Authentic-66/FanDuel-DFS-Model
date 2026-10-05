"""Load the week's inputs: FanDuel player list (with status applied), Vegas lines, nflverse weekly stats."""
import re

import pandas as pd

INACTIVE = ['O', 'D', 'IR']


def norm_name(s):
    """Join key between FanDuel and nflverse names: lowercase letters only, suffixes dropped."""
    return re.sub(r'[^a-z]', '', re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', str(s).lower()))


def load_slate(path, status):
    """All FanDuel players with Injury Indicator rebuilt from config status (stale Q/D tags cleared; O/IR kept).
    Adds Inj (status), Full name and join Key. Returns the full list; filter with active(...)."""
    fd = pd.read_csv(path)
    fd['FPPG'] = fd.FPPG.fillna(0)    # never-played backups have no FPPG
    fd['Inj'] = fd['Injury Indicator'].where(fd['Injury Indicator'].isin(['O', 'IR']), '')
    fd['Full'] = fd['First Name'] + ' ' + fd['Last Name']
    fd['Key'] = fd.Nickname.map(norm_name)
    named = lambda names: fd.Full.isin(names) | fd.Nickname.isin(names)
    fd.loc[named(status['out']), 'Inj'] = 'O'
    fd.loc[named(status['questionable']), 'Inj'] = 'Q'
    return fd


def active(fd):
    return fd[~fd.Inj.isin(INACTIVE)].reset_index(drop=True)


def newly_out(fd, status):
    """Skill players ruled OUT this week by config status (their usage gets redistributed)."""
    out = fd.Full.isin(status['out']) | fd.Nickname.isin(status['out'])
    return fd[out & fd.Position.isin(['RB', 'WR', 'TE'])]


def load_lines(path):
    """Per-team implied total, opponent and game id from lines.csv (away,home,fav,spread,total)."""
    rows = []
    for g in pd.read_csv(path).itertuples():
        dog = g.home if g.fav == g.away else g.away
        game = f'{g.away}@{g.home}'
        rows.append(dict(team=g.fav, opp=dog, game=game, implied=g.total / 2 + g.spread / 2))
        rows.append(dict(team=dog, opp=g.fav, game=game, implied=g.total / 2 - g.spread / 2))
    return pd.DataFrame(rows).set_index('team')


def load_stats(path, cfg, before_week=None):
    """nflverse weekly player stats with FanDuel team codes, join key, configured season types. All positions are
    kept (two-way players like Travis Hunter are listed as CB); usage.aggregate resolves name collisions.
    QB game rows under model.qb.min_attempts are dropped (cameos). before_week limits to earlier weeks (backtests)."""
    st = pd.read_csv(path, low_memory=False)
    st = st[st.season_type.isin(cfg['model']['season_types'])]
    if before_week is not None:
        st = st[st.week < before_week]
    st = st.assign(team=st.team.replace(cfg['teams']['nflverse_to_fd']), k=st.player_display_name.map(norm_name))
    return st[~((st.position == 'QB') & (st.attempts < cfg['model']['qb']['min_attempts']))].reset_index(drop=True)
