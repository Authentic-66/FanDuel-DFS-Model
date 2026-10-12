"""Per-player usage and efficiency from weekly stats, prior-season blend, and injury redistribution.

The aggregate frame (indexed by name key) carries two views of the same player:
  usage:      u_g, u_att, u_car, u_tgt     -> per-game volume = u_x / u_g
  efficiency: att, cmp, py, ptd, ints, car, ry, rtd, tgt, rec, rey, retd  -> per-opportunity rates, shrunk to league priors
Without a prior-season blend the two views hold the same raw totals.
"""
import pandas as pd

STAT_COLS = dict(att='attempts', cmp='completions', py='passing_yards', ptd='passing_tds', ints='passing_interceptions',
                 car='carries', ry='rushing_yards', rtd='rushing_tds', tgt='targets', rec='receptions',
                 rey='receiving_yards', retd='receiving_tds')
VOLUME = ['att', 'car', 'tgt']


def aggregate(st):
    """Season totals per player, indexed by name key. When two nflverse players share a key (e.g. DJ Turner WR/CB),
    the one with the most attempts + carries + targets wins."""
    st = st.sort_values('week')
    agg = st.groupby(['k', 'player_id']).agg(g=('week', 'nunique'), team=('team', 'last'),
                                             **{c: (s, 'sum') for c, s in STAT_COLS.items()})
    agg = agg.assign(volume=agg[VOLUME].sum(axis=1)).sort_values('volume', kind='stable')
    agg = agg.reset_index().groupby('k').tail(1).set_index('k').drop(columns=['player_id', 'volume'])
    agg['u_g'] = agg.g.astype(float)
    for c in VOLUME:
        agg['u_' + c] = agg[c].astype(float)
    return agg


def blend_prior(agg, prior, pb):
    """Shrink current-season usage/efficiency toward the prior season (config [model.prior_blend]).

    usage:      u_x = cur_x + Ku * prior_x / prior_g,   u_g = cur_g + Ku    (Ku pseudo-games of prior per-game volume)
    efficiency: x   = cur_x + Ke * prior_x / prior_g                        (Ke games' worth of prior opportunities)
    Only players with >= min_prior_games prior games; both weights scale by team_change_weight if the team changed.
    """
    ku, ke = pb['usage_games'], pb['efficiency_games']
    agg = agg.copy()
    if ku == 0 and ke == 0:
        return agg
    pr = prior[prior.g >= pb['min_prior_games']].reindex(agg.index)
    has = pr.g.notna()
    w = pd.Series(1.0, index=agg.index).where(pr.team == agg.team, pb['team_change_weight'])[has]
    per_game = pr.loc[has, list(STAT_COLS)].div(pr.g[has], axis=0)
    for c in VOLUME:
        agg.loc[has, 'u_' + c] += ku * w * per_game[c]
    agg.loc[has, 'u_g'] += ku * w
    for c in STAT_COLS:
        agg[c] = agg[c].astype(float)
        agg.loc[has, c] += ke * w * per_game[c]
    return agg


def per_game(agg, key, col):
    return agg.at[key, 'u_' + col] / agg.at[key, 'u_g']


def already_absent(st, key, team):
    """True if the player has no stat row in his team's most recent game in `st`: he was already missing, so his
    teammates' recent usage reflects it."""
    last = st[st.team == team].week.max()
    return not ((st.k == key) & (st.week == last)).any()


def present_share(agg, st, out_key, mate_key, team):
    """Share of a teammate's usage sample in which the OUT player's role was still his: that part of the teammate's
    per-game volume does not yet reflect the absence. Current season: the teammate's games for `team` in which the OUT
    player also has a stat row. The teammate's prior-season pseudo-games (u_g - g) all count: they describe his role
    on a full depth chart, not his role with this player missing."""
    weeks = lambda k: set(st.week[(st.k == k) & (st.team == team)])
    shared = len(weeks(out_key) & weeks(mate_key))
    return min(1.0, (shared + agg.at[mate_key, 'u_g'] - agg.at[mate_key, 'g']) / agg.at[mate_key, 'u_g'])


def redistribute_out(agg, out_players, active_fd, share, st=None, mode='skip'):
    """Give `share` of each OUT player's per-game targets/carries to active same-team RB/WR/TE, pro rata to their own
    per-game volume. Returns ({key: extra targets/g}, {key: extra carries/g}). `st` = the stats frame; without it
    every OUT player is handed out in full. [model.injury] absent_mode:
      "present_share": each teammate's gain is scaled by present_share (above). A player ruled out for the first time
          is handed out in full; one who has already missed games is handed out for the part of the sample he played
          in, so the gain fades as the games without him accumulate.
      "skip": OUT players who missed their team's most recent game are skipped entirely (Oct 10 2026 behaviour; it
          assumed teammates' usage already reflected the absence, but usage is a season average plus the prior blend:
          week 5, Braelon Allen got nothing for Breece Hall and Jaylen Warren nothing for Rico Dowdle)."""
    if mode not in ('present_share', 'skip'):
        raise ValueError(f'[model.injury] absent_mode must be "present_share" or "skip", not {mode!r}')
    extra = {'tgt': {}, 'car': {}}
    for o in out_players.itertuples():
        if o.Key not in agg.index or (st is not None and mode == 'skip' and already_absent(st, o.Key, o.Team)):
            continue
        mates = active_fd[(active_fd.Team == o.Team) & active_fd.Position.isin(['RB', 'WR', 'TE'])]
        mates = mates[mates.Key.isin(agg.index)].Key
        frac = {k: present_share(agg, st, o.Key, k, o.Team) if st is not None and mode == 'present_share' else 1.0
                for k in mates}
        for col, gained in extra.items():
            wts = mates.map(lambda k: per_game(agg, k, col))
            if wts.sum() > 0:
                for k, w in zip(mates, wts):
                    gained[k] = gained.get(k, 0) + share * per_game(agg, o.Key, col) * w / wts.sum() * frac[k]
    return extra['tgt'], extra['car']


def starting_qbs(st):
    """Keys of each team's QB with the most attempts in that team's most recent game."""
    qb = st[st.position == 'QB']
    qb = qb[qb.week == qb.groupby('team').week.transform('max')]
    return set(qb.sort_values('attempts').groupby('team').tail(1).k)
