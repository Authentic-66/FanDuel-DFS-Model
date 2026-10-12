"""Per-player usage and efficiency from weekly stats, prior-season blend, and injury redistribution.

The aggregate frame (indexed by name key) carries two views of the same player:
  usage:      u_g, u_att, u_car, u_tgt     -> per-game volume = u_x / u_g
  efficiency: att, cmp, py, ptd, ints, car, ry, rtd, tgt, rec, rey, retd  -> per-opportunity rates, shrunk to league priors
Without a prior-season blend the two views hold the same raw totals.
"""
import numpy as np
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


def routes(routing, pos, col, share, same):
    """How one OUT player's volume in `col` ('tgt' / 'car') is split: [(share of his volume, mask of the teammates
    who divide it, depth-rank shares or None)]. routing = [model.injury.position_share], keyed by the OUT player's
    position, e.g. WR = {tgt_same = 0.77, tgt_other = 0.16}: 77% of his targets to teammates at his position (`same`),
    16% to the rest. tgt_rank = [0.2, 0.2, 0.6] (optional) splits the same-position part by depth rank instead of
    pro rata (see rank_weights). Without a rule for this position and column, `share` goes to every teammate (the
    pro-rata rule)."""
    rule = (routing or {}).get(pos, {})
    if col + '_same' not in rule:
        return [(share, same | ~same, None)]
    return [(rule[col + '_same'], same, rule.get(col + '_rank')), (rule.get(col + '_other', 0.0), ~same, None)]


def rank_weights(volume, ranks):
    """Shares of a group's gain by depth rank. volume: each teammate's own per-game volume; ranks = [largest, second,
    third and lower]: the teammate with the most volume gets ranks[0], the next ranks[1], and everyone below shares
    ranks[2] equally. With fewer than three teammates the unused share goes to those present in proportion
    (the weights are rescaled to sum to 1)."""
    order = np.argsort(-np.asarray(volume, dtype=float), kind='stable')
    w = np.zeros(len(order))
    for place, i in enumerate(order):
        w[i] = ranks[place] if place < 2 else ranks[2] / (len(order) - 2)
    return w / w.sum() if w.sum() > 0 else w


def redistribute_out(agg, out_players, active_fd, share, st=None, mode='skip', routing=None):
    """Give each OUT player's per-game targets/carries to active same-team RB/WR/TE. Returns ({key: extra targets/g},
    {key: extra carries/g}). Without `routing`, `share` of it goes to all of them pro rata to their own per-game
    volume. With `routing` ([model.injury.position_share]; out_players needs a Position column) it is split by
    position first (see routes) and pro rata inside each group; a part whose group has no volume is not handed out.
    `st` = the stats frame; without it every OUT player is handed out in full. [model.injury] absent_mode:
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
        mates = mates[mates.Key.isin(agg.index) & (mates.Key != o.Key)]
        same = (mates.Position == getattr(o, 'Position', None)).values
        mates = mates.Key
        frac = {k: present_share(agg, st, o.Key, k, o.Team) if st is not None and mode == 'present_share' else 1.0
                for k in mates}
        for col, gained in extra.items():
            wts = mates.map(lambda k: per_game(agg, k, col)).values
            for part, group, ranks in routes(routing, getattr(o, 'Position', None), col, share, same):
                if ranks is not None and group.any():        # by depth rank: also reaches teammates with no volume yet
                    split = rank_weights(wts[group], ranks)
                elif wts[group].sum() > 0:
                    split = wts[group] / wts[group].sum()
                else:
                    continue
                for k, w in zip(mates[group], split):
                    if part * w:
                        gained[k] = gained.get(k, 0) + part * per_game(agg, o.Key, col) * w * frac[k]
    return extra['tgt'], extra['car']


def trade_volume(agg, trades, active_fd, share, routing=None):
    """Volume changes for [[status.trade]] players (rows from data.trades; active_fd already lists them on the new
    team). Returns ({key: extra targets/g}, {key: extra carries/g}) to add to redistribute_out's.
    Old team: handled like a player ruled out for the first time: his per-game targets and carries go to his old
    teammates (`share` pro rata, or by position with `routing`, as in redistribute_out), in full, however many games
    he has already missed.
    New team (only if he is active): he gets share * factor of the team's targets per game, taken from his new
    teammates in proportion to their own targets, so the team total is unchanged. His carries stay his own."""
    xt, xc = {}, {}
    for t in trades.itertuples():
        if t.Key not in agg.index:
            raise ValueError(f'[[status.trade]] {t.Name}: no stats this season or last, nothing to move')
        old_t, old_c = redistribute_out(agg, pd.DataFrame([dict(Key=t.Key, Team=t.From, Position=t.Pos)]), active_fd,
                                        share, routing=routing)
        for extra, gained in ((xt, old_t), (xc, old_c)):
            for k, v in gained.items():
                extra[k] = extra.get(k, 0) + v
        if t.Key not in set(active_fd.Key):
            continue
        mates = active_fd[(active_fd.Team == t.To) & active_fd.Position.isin(['RB', 'WR', 'TE'])]
        mates = mates[mates.Key.isin(agg.index) & (mates.Key != t.Key)].Key
        tgt = mates.map(lambda k: per_game(agg, k, 'tgt'))
        if tgt.sum() <= 0:
            raise ValueError(f'[[status.trade]] {t.Name}: no {t.To} targets to take a share of')
        take = t.share * t.factor
        for k, v in zip(mates, tgt):
            xt[k] = xt.get(k, 0) - take * v
        xt[t.Key] = xt.get(t.Key, 0) + take * tgt.sum() - per_game(agg, t.Key, 'tgt')
    return xt, xc


def team_mismatches(agg, active_fd, trades, min_volume=3.0):
    """Active skill players FanDuel lists on a different team from their latest stats, not covered by a
    [[status.trade]] entry, with at least min_volume attempts + carries + targets a game: [(name, FanDuel, stats)].
    As-is they keep their old-team volume on the new team and nobody's volume is adjusted."""
    out = []
    for r in active_fd[active_fd.Position.isin(['QB', 'RB', 'WR', 'TE']) & active_fd.Key.isin(agg.index)].itertuples():
        vol = sum(per_game(agg, r.Key, c) for c in VOLUME)
        if agg.at[r.Key, 'team'] != r.Team and vol >= min_volume and r.Key not in set(trades.Key):
            out.append((r.Nickname, r.Team, agg.at[r.Key, 'team']))
    return out


def starting_qbs(st):
    """Keys of each team's QB with the most attempts in that team's most recent game."""
    qb = st[st.position == 'QB']
    qb = qb[qb.week == qb.groupby('team').week.transform('max')]
    return set(qb.sort_values('attempts').groupby('team').tail(1).k)
