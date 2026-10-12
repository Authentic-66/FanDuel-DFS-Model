"""Load the week's inputs: FanDuel player list (with status applied), Vegas lines, nflverse weekly stats."""
import re

import pandas as pd

INACTIVE = ['O', 'D', 'IR']


def norm_name(s):
    """Join key between FanDuel and nflverse names: lowercase letters only, suffixes dropped."""
    return re.sub(r'[^a-z]', '', re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', str(s).lower()))


def load_slate(path, status):
    """All FanDuel players with Inj (status), Full name and join Key. Returns the full list; filter with active(...).
    FanDuel's O/IR tags are always kept. Until [status] is filled in (both lists empty: before Friday's report),
    FanDuel's Q and D tags count as Q; once it is, they are cleared and config status decides (they go stale)."""
    fd = pd.read_csv(path)
    fd['FPPG'] = fd.FPPG.fillna(0)    # never-played backups have no FPPG
    tags = fd['Injury Indicator']
    fd['Inj'] = tags.where(tags.isin(['O', 'IR']), '')
    if not status['out'] and not status['questionable']:
        fd.loc[tags.isin(['Q', 'D']), 'Inj'] = 'Q'
    fd['Full'] = fd['First Name'] + ' ' + fd['Last Name']
    fd['Key'] = fd.Nickname.map(norm_name)
    named = lambda names: fd.Full.isin(names) | fd.Nickname.isin(names)
    fd.loc[named(status['out']), 'Inj'] = 'O'
    fd.loc[named(status['questionable']), 'Inj'] = 'Q'
    for t in trades(fd, status).itertuples():   # a traded player plays for (and stacks with) his new team
        fd.loc[fd.Key == t.Key, 'Team'] = t.To
    return fd


def trades(fd, status):
    """[[status.trade]] entries as rows (Key, Name, Pos, From, To, share, factor), validated against the slate.
    player / from / to are required. new_target_share (his share of the new team's targets) has no default: if he is
    on the slate the model stops rather than guess a traded player's role. first_week_factor (default 1.0) scales it."""
    rows = []
    for t in status.get('trade', []):
        missing = [k for k in ('player', 'from', 'to') if not t.get(k)]
        if missing:
            raise ValueError(f'[[status.trade]] entry {t} is missing {", ".join(missing)}')
        who = fd[(fd.Full == t['player']) | (fd.Nickname == t['player'])]
        if len(who) > 1:
            raise ValueError(f'[[status.trade]] {t["player"]!r}: {len(who)} players with that name on the slate')
        if who.empty:   # not on the slate (new team not playing it): his old teammates still get his volume
            rows.append(dict(Key=norm_name(t['player']), Name=t['player'], Pos=t.get('position', ''), From=t['from'],
                             To=t['to'], share=0.0, factor=1.0))   # position (optional): routes his old volume by position
            continue
        team = who.Team.iloc[0]
        if team not in (t['from'], t['to']):
            raise ValueError(f'[[status.trade]] {t["player"]}: FanDuel lists him on {team}, not {t["from"]} or {t["to"]}')
        share = t.get('new_target_share')
        if share in (None, ''):
            raise ValueError(f'[[status.trade]] {t["player"]} ({t["from"]} -> {t["to"]}): set new_target_share, his '
                             f'share of the {t["to"]} targets (e.g. 0.15). The model will not guess the role of a traded player.')
        if not 0 <= share < 1:
            raise ValueError(f'[[status.trade]] {t["player"]}: new_target_share must be between 0 and 1, not {share}')
        rows.append(dict(Key=who.Key.iloc[0], Name=who.Nickname.iloc[0], Pos=who.Position.iloc[0], From=t['from'],
                         To=t['to'], share=float(share),
                         factor=float(t.get('first_week_factor', 1.0))))
    return pd.DataFrame(rows, columns=['Key', 'Name', 'Pos', 'From', 'To', 'share', 'factor'])


def active(fd):
    return fd[~fd.Inj.isin(INACTIVE)].reset_index(drop=True)


def newly_out(fd, status):
    """Skill players ruled OUT this week by config status (their usage gets redistributed). Traded players are left
    to usage.trade_volume: their new teammates' usage never included them."""
    out = fd.Full.isin(status['out']) | fd.Nickname.isin(status['out'])
    return fd[out & fd.Position.isin(['RB', 'WR', 'TE']) & ~fd.Key.isin(trades(fd, status).Key)]


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
    fd = cfg['teams']['nflverse_to_fd']
    st = st.assign(team=st.team.replace(fd), k=st.player_display_name.map(norm_name))
    if 'opponent_team' in st:
        st = st.assign(opp=st.opponent_team.replace(fd))     # the defence faced, FanDuel codes (dfs.opponent)
    return st[~((st.position == 'QB') & (st.attempts < cfg['model']['qb']['min_attempts']))].reset_index(drop=True)
