"""nflverse snap counts (data/cache/snap_counts_<season>.csv, from fetch_stats.py) -> recent-role features for the role
guard switches ([model.role_guard] promotion / snap_projection / role_drop; docs/role_guard_tests.md).

A snap-count row means the player was active and took at least one snap (offence, defence or special teams) in that
game; no row = inactive or not with the team. offense_pct is his share of the team's offensive snaps."""
import os

import numpy as np
import pandas as pd

from .data import norm_name

FEATURES = ['LastSnap', 'ActiveLast', 'AvgSnap', 'Recent2Snap', 'RecentVol', 'PriorSnap']


def path(cache, season):
    return os.path.join(cache, f'snap_counts_{season}.csv')


def load(file, cfg, before_week=None):
    """Regular-season snap rows: k (join key, FanDuel aliases applied), team (FanDuel codes), position, week, snap
    (offensive snap share 0-1). before_week keeps earlier weeks only (archived re-runs, backtests)."""
    sn = pd.read_csv(file, low_memory=False)
    sn = sn[sn.game_type == 'REG'] if 'game_type' in sn else sn
    if before_week is not None:
        sn = sn[sn.week < before_week]
    alias = cfg.get('names', {}).get('aliases', {})
    return pd.DataFrame(dict(k=sn.player.map(lambda n: norm_name(alias.get(n, n))).values,
                             team=sn.team.replace(cfg['teams']['nflverse_to_fd']).values,
                             position=sn.position.values, week=sn.week.values,
                             snap=sn.offense_pct.fillna(0).astype(float).values))


def features(sn, st, prior_sn=None, games=2):
    """Per join key, as of the frames given (they must hold only games before the slate):
      LastSnap    offensive snap share in his team's most recent game (0 if he has no row: inactive)
      ActiveLast  he has a row in that game (active)
      AvgSnap     mean snap share over his earlier games for the team this season (before the most recent one)
      Recent2Snap mean snap share over the team's last `games` games (missing games count 0)
      RecentVol   targets + carries per team game over the team's last `games` games (stats frame st; 0 if no row)
      PriorSnap   mean snap share in the prior season (prior_sn), NaN if none
    Team = the team of his latest snap row. Keys without snap rows are absent from the result."""
    if sn.empty:
        return pd.DataFrame(columns=FEATURES)
    sn = sn.sort_values('week').drop_duplicates(['k', 'team', 'week'], keep='last')
    team_weeks = sn.groupby('team').week.apply(lambda w: sorted(set(w))).to_dict()
    vol = st.assign(v=st.targets.fillna(0) + st.carries.fillna(0)).groupby(['k', 'team', 'week']).v.sum()
    rows = {}
    for (k, team), g in sn.groupby(['k', 'team']):
        wk = team_weeks[team]
        last, recent = wk[-1], wk[-games:]
        by_week = dict(zip(g.week, g.snap))
        earlier = [s for w, s in by_week.items() if w < last]
        rv = sum(vol.get((k, team, w), 0.0) for w in recent) / len(recent)
        row = dict(LastSnap=by_week.get(last, 0.0), ActiveLast=last in by_week,
                   AvgSnap=float(np.mean(earlier)) if earlier else np.nan,
                   Recent2Snap=sum(by_week.get(w, 0.0) for w in recent) / len(recent), RecentVol=rv,
                   last_week=g.week.max(), team=team)
        if k not in rows or row['last_week'] >= rows[k]['last_week']:
            rows[k] = row
    out = pd.DataFrame.from_dict(rows, orient='index')
    prior = (prior_sn.groupby('k').snap.mean() if prior_sn is not None and not prior_sn.empty
             else pd.Series(dtype=float))
    out['PriorSnap'] = out.index.map(prior)
    return out[FEATURES + ['team']]
